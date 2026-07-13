import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
import torch
from transformers import pipeline

from app.core.logger import data_logger

# Use HF-Mirror to accelerate model downloading in China
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

logger = data_logger


class TransformersNERMapper:
    """
    三级漏斗式 NLP 抽取器：
    1. 正则优先处理结构化内容
    2. 轻量 NER 处理剩余医学短语
    3. 本地 LLM 处理复杂自然语言残余片段
    """

    _instance = None

    LLM_URL = "http://192.168.0.214:8802/v1/chat/completions"
    LLM_AUTHORIZATION = "Bearer 467e395934ab0b80da2b4f9cc9df28a51fbda2fc184e3e0d"
    LLM_MODEL = "local-medical-llm"
    LLM_TIMEOUT = 40.0
    LLM_TRIGGER_MIN_LEN = 8
    LLM_NER_CONFIDENCE_THRESHOLD = 0.78

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TransformersNERMapper, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        model_name = "shibing624/bert4ner-base-chinese"
        device = 0 if torch.cuda.is_available() else -1
        device_name = "GPU (cuda:0)" if device == 0 else "CPU"

        logger.info(f"Loading Transformers NER model: {model_name} on {device_name}...")
        try:
            self.ner_pipeline = pipeline(
                "ner",
                model=model_name,
                aggregation_strategy="simple",
                device=device,
            )
            logger.info(f"Transformers NER model loaded successfully on {device_name}.")
        except Exception as exc:
            logger.error(f"Failed to load NER model: {exc}")
            self.ner_pipeline = None

        self._initialized = True

    def _empty_result(self, fallback_text: str = "") -> Dict[str, List[str]]:
        return {
            "conditions": [],
            "medications": [],
            "procedures": [],
            "measurements": [],
            "symptoms_with_values": [],
            "times": [],
            "observations": [fallback_text] if fallback_text else [],
            "negations": [],
        }

    def _dedupe_list(self, items: List[str]) -> List[str]:
        clean_items: List[str] = []
        seen = set()
        for item in items:
            if not isinstance(item, str):
                continue
            normalized = re.sub(r"\s+", " ", item).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            clean_items.append(normalized)
        return clean_items

    def _dedupe_result(self, result: Dict[str, List[str]]) -> Dict[str, List[str]]:
        for key in [
            "conditions",
            "medications",
            "procedures",
            "measurements",
            "symptoms_with_values",
            "times",
            "observations",
            "negations",
        ]:
            result[key] = self._dedupe_list(result.get(key, []))
        return result

    def _merge_results(self, *results: Dict[str, List[str]]) -> Dict[str, List[str]]:
        merged = self._empty_result()
        merged["observations"] = []
        for result in results:
            if not result:
                continue
            for key in merged.keys():
                merged[key].extend(result.get(key, []))
        return self._dedupe_result(merged)

    def _cleanup_leftover_text(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text
        cleaned = re.sub(r"[\[\]【】()（）]", " ", cleaned)
        cleaned = re.sub(r"[,:：;；，。/\\|+\-]+", " ", cleaned)
        cleaned = re.sub(
            r"\b(?:value|unit|measurement|route|form|frequency|dose)\b",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _looks_like_meaningful_residual(self, text: str) -> bool:
        if not text:
            return False
        cleaned = self._cleanup_leftover_text(text)
        if len(cleaned) < self.LLM_TRIGGER_MIN_LEN:
            return False
        if re.fullmatch(r"[\d\s\.,:：;；，。/\-年月日前后小时天周分]+", cleaned):
            return False
        if re.fullmatch(r"[A-Za-z0-9\s./\-]+", cleaned):
            return False
        return len(re.findall(r"[\u4e00-\u9fa5]", cleaned)) >= 3

    def _remove_span(self, text: str, start: int, end: int) -> str:
        if start < 0 or end <= start:
            return text
        chars = list(text)
        for idx in range(start, min(end, len(chars))):
            chars[idx] = " "
        return "".join(chars)

    def _extract_time_regex(self, text: str) -> Tuple[List[str], str]:
        if not text or not isinstance(text, str):
            return [], text

        times: List[str] = []
        cleaned = text
        patterns = [
            r"(\d+\s*(?:年|个月|月|周|天|日|小时|分钟|分)\s*(?:前|后|内|以来)?)",
            r"(\d{4}年\d{1,2}月\d{1,2}日)",
            r"(\d{4}-\d{1,2}-\d{1,2})",
            r"(\d{4}/\d{1,2}/\d{1,2})",
        ]
        for pattern in patterns:
            for match in list(re.finditer(pattern, cleaned)):
                value = match.group(1).strip()
                times.append(value)
                cleaned = self._remove_span(cleaned, match.start(1), match.end(1))
        return self._dedupe_list(times), cleaned

    def _extract_negations(self, text: str) -> Dict[str, Any]:
        negations: List[str] = []
        cleaned_text = text
        if not text or not isinstance(text, str):
            return {"negations": negations, "remaining_text": cleaned_text}

        pattern = r"(否认|无|未见|未发现)(?:明显)?([\u4e00-\u9fa5A-Za-z0-9]{2,16}?)(?:史|症|异常|表现|体征)?(?=[，。；,.;\n\r]|$)"
        for match in list(re.finditer(pattern, cleaned_text)):
            full_match = match.group(0)
            negation_word = match.group(1).strip()
            entity = match.group(2).strip()
            if len(entity) < 2:
                continue
            negations.append(f"诊断：{entity} ，否定词：{negation_word}")
            cleaned_text = cleaned_text.replace(full_match, " " * len(full_match), 1)

        return {"negations": self._dedupe_list(negations), "remaining_text": cleaned_text}

    def _extract_drugs_regex(self, text: str) -> Dict[str, Any]:
        drugs: List[str] = []
        cleaned_text = text
        if not text or not isinstance(text, str):
            return {"drugs": drugs, "remaining_text": cleaned_text}

        forms = (
            r"(?:肠溶片|分散片|糖衣片|薄膜衣片|咀嚼片|口腔崩解片|片|胶囊|软胶囊|微丸|丸|颗粒|冲剂|"
            r"注射液|注射用粉针剂|口服液|糖浆|滴眼液|滴鼻液|滴耳液|软膏|乳膏|凝胶|贴膏|贴剂|"
            r"栓|气雾剂|喷雾剂|粉吸入剂|滴注液|溶液|混悬液|乳剂)"
        )
        routes = (
            r"(?:静脉滴注|静滴|静脉注射|静注|肌肉注射|肌注|皮下注射|皮注|皮内注射|口服|吞服|含服|"
            r"舌下含服|外用|涂抹|贴敷|雾化吸入|雾化|滴眼|滴鼻|滴耳|直肠给药|阴道给药|注射)"
        )
        prefix_pattern = (
            r"^(?:住院期间给予|住院期间|期间给予|给予|出院带药|出院|用药|使用|加用|服用|"
            r"对症支持治疗|对症支持|支持治疗|治疗|予以|予|应用)+"
        )

        patterns = [
            ("drug_form", rf"([\u4e00-\u9fa5A-Za-z0-9]{{2,20}}?)\s*({forms})(?:\s*({routes}))?"),
            ("form_drug", rf"({forms})([\u4e00-\u9fa5A-Za-z0-9]{{2,20}}?)(?:\s*({routes}))?"),
        ]

        for pattern_type, pattern in patterns:
            for match in list(re.finditer(pattern, cleaned_text)):
                if pattern_type == "drug_form":
                    raw_drug, form, route = match.group(1), match.group(2), match.group(3) or ""
                else:
                    form, raw_drug, route = match.group(1), match.group(2), match.group(3) or ""

                drug_name = re.sub(prefix_pattern, "", raw_drug).strip()
                if len(drug_name) < 2:
                    continue

                if not route:
                    if "注射" in form:
                        route = "注射"
                    elif any(token in form for token in ["片", "胶囊", "丸", "颗粒", "口服液", "糖浆"]):
                        route = "口服"

                drugs.append(f"药名：{drug_name} 剂型：{form} 给药方式：{route}")
                cleaned_text = self._remove_span(cleaned_text, match.start(), match.end())

        return {"drugs": self._dedupe_list(drugs), "remaining_text": cleaned_text}

    def _infer_measurement_unit(self, name: str, unit: str) -> str:
        if unit:
            return unit
        if "血糖" in name:
            return "mmol/L"
        if "心率" in name:
            return "次/分"
        if "血压" in name or "收缩压" in name or "舒张压" in name:
            return "mmHg"
        if "体温" in name or "发热" in name:
            return "℃"
        if "饱和度" in name:
            return "%"
        return unit

    def _extract_measurements_regex(self, text: str) -> Tuple[List[Dict[str, str]], str]:
        measurements: List[Dict[str, str]] = []
        cleaned = text
        if not text or not isinstance(text, str):
            return measurements, cleaned

        specs = [
            (
                "symptom_after",
                r"([\u4e00-\u9fa5]{2,10}(?:疼痛|头晕|发热|咳嗽|胸闷|恶心|呕吐|乏力|腹痛|麻木|出血|水肿|不适))\s*(\d+(?:年|个月|月|周|天|日|小时|分钟|分))",
            ),
            (
                "symptom_before",
                r"(\d+(?:年|个月|月|周|天|日|小时|分钟|分))(?:前|来)?[^，。；,\n]{0,12}?(?:出现|伴有|突发|起床时)?([\u4e00-\u9fa5]{2,10}(?:疼痛|头晕|发热|咳嗽|胸闷|恶心|呕吐|乏力|腹痛|麻木|出血|水肿|不适))",
            ),
            (
                "measurement",
                r"(?:检查项|指标)\s*[:：]?\s*([A-Za-z\u4e00-\u9fa50-9\-]+)\s*(?:value|值)?\s*[:：]?\s*([\d./]+)\s*(?:单位)?\s*[:：]?\s*([^\s，。；,\n]+)?",
            ),
            (
                "measurement",
                r"([A-Za-z\u4e00-\u9fa50-9\-]{2,20}(?:血糖|血压|心率|体温|血氧饱和度|WBC|Hb|PLT|CRP|ALT|AST|肌酐|尿酸|胆固醇|甘油三酯|蛋白|计数|浓度|比值|体积))\s*[:：]?\s*([\d./]+)\s*(?:单位)?\s*[:：]?\s*([^\s，。；,\n]+)?",
            ),
        ]

        for item_type, pattern in specs:
            for match in list(re.finditer(pattern, cleaned, flags=re.IGNORECASE)):
                if item_type == "symptom_after":
                    symptom_name = match.group(1).strip()
                    duration = match.group(2).strip()
                    measurements.append(
                        {
                            "type": "symptom",
                            "name": f"症状：{symptom_name}",
                            "value": duration,
                            "unit": "持续时间",
                        }
                    )
                elif item_type == "symptom_before":
                    duration = match.group(1).strip()
                    symptom_name = match.group(2).strip()
                    measurements.append(
                        {
                            "type": "symptom",
                            "name": f"症状：{symptom_name}",
                            "value": duration,
                            "unit": "持续时间",
                        }
                    )
                else:
                    name = match.group(1).strip()
                    value = match.group(2).strip()
                    unit = match.group(3).strip() if match.lastindex and match.lastindex >= 3 and match.group(3) else ""
                    if re.search(r"(趋势|平稳|好转|异常|正常|偏高|偏低|注意|目前|建议|复查|由于|符合)", unit):
                        unit = ""
                    unit = self._infer_measurement_unit(name, unit)
                    if not name or name.isdigit():
                        continue
                    if "." in value and len(value.split(".")[0]) == 4:
                        continue
                    measurements.append(
                        {
                            "type": "measurement",
                            "name": name,
                            "value": value,
                            "unit": unit,
                        }
                    )
                cleaned = self._remove_span(cleaned, match.start(), match.end())

        return measurements, cleaned

    def _build_regex_result(self, text: str) -> Tuple[Dict[str, List[str]], str]:
        result = self._empty_result()
        result["observations"] = []
        residual = text

        neg_res = self._extract_negations(residual)
        result["negations"].extend(neg_res["negations"])
        residual = neg_res["remaining_text"]

        drug_res = self._extract_drugs_regex(residual)
        result["medications"].extend(drug_res["drugs"])
        residual = drug_res["remaining_text"]

        regex_measurements, residual = self._extract_measurements_regex(residual)
        for item in regex_measurements:
            unit_str = f" 单位:{item['unit']}" if item.get("unit") else ""
            if item["type"] == "symptom":
                result["symptoms_with_values"].append(f"{item['name']} 持续时间：{item['value']}")
            else:
                result["measurements"].append(f"检查项：{item['name']} 值:{item['value']}{unit_str}")

        times, residual = self._extract_time_regex(residual)
        result["times"].extend(times)

        return self._dedupe_result(result), residual

    def _map_ner_entity(self, entity_group: str, word: str, score: float) -> Tuple[Optional[str], Optional[str]]:
        if not word or len(word) < 2:
            return None, None

        group = (entity_group or "").upper()
        if group in {"O", ""}:
            return None, None

        if "DIS" in group or group in {"DISEASE", "SYMPTOM", "SYM"}:
            return "conditions", word
        if "DRU" in group or group in {"MED", "MEDICINE", "DRUG"}:
            return "medications", word
        if "PRO" in group or "EQU" in group or group in {"PROCEDURE"}:
            return "procedures", word
        if "BOD" in group or group in {"BODY", "LOC"}:
            return "observations", f"部位: {word}"
        if score >= 0.92 and re.search(r"[\u4e00-\u9fa5]{2,}", word):
            return "observations", f"{group}: {word}"
        return None, None

    def _extract_with_ner(self, text: str) -> Tuple[Dict[str, List[str]], str, float]:
        result = self._empty_result()
        result["observations"] = []
        if not text or not self.ner_pipeline:
            return result, text, 0.0

        residual = text
        scores: List[float] = []
        try:
            entities = self.ner_pipeline(text)
        except Exception as exc:
            logger.warning(f"NER extraction failed for text '{text}': {exc}")
            return result, text, 0.0

        for ent in entities:
            entity_group = ent.get("entity_group", "")
            word = str(ent.get("word", "")).replace("##", "").strip()
            score = float(ent.get("score", 0.0) or 0.0)
            if not word or re.match(r"^[\d.\s]+$", word):
                continue

            bucket, mapped_word = self._map_ner_entity(entity_group, word, score)
            if not bucket or not mapped_word:
                continue

            if score < self.LLM_NER_CONFIDENCE_THRESHOLD and bucket != "observations":
                continue

            result[bucket].append(mapped_word)
            scores.append(score)
            residual = re.sub(re.escape(word), " ", residual, count=1)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        return self._dedupe_result(result), residual, avg_score

    def _llm_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.LLM_AUTHORIZATION,
            "Content-Type": "application/json",
        }

    def _llm_payload(self, text: str) -> Dict[str, Any]:
        system_prompt = (
            "You are a medical entity extraction engine. "
            "Return exactly one valid JSON object and nothing else. "
            "Do not provide explanation, advice, markdown, code fences, or extra keys. "
            'The required schema is {"conditions":[],"medications":[],"procedures":[],"observations":[]}. '
            "conditions means diseases, diagnoses, and symptom phrases. "
            "medications means medication names only. "
            "procedures means surgeries, procedures, and examinations. "
            "observations means body parts, signs, and other medical observations. "
            "Never return keys such as response, result, summary, data, or reasoning."
        )
        user_prompt = (
            "Extract medical entities from the following text. Return JSON only.\n"
            "Example output:\n"
            '{"conditions":["急性胆囊炎"],"medications":[],"procedures":["支架植入术"],"observations":["右上腹压痛"]}\n'
            f"Medical text:\n{text}"
        )
        return {
            "model": self.LLM_MODEL,
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }

    def _extract_json_fragment(self, content: str) -> str:
        text = content.strip()
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fence_match:
            return fence_match.group(1).strip()

        first = text.find("{")
        if first == -1:
            return text

        depth = 0
        in_string = False
        escape = False
        for idx in range(first, len(text)):
            ch = text[idx]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[first : idx + 1]
        return text

    def _coerce_llm_json_shape(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        if all(key in parsed for key in ["conditions", "medications", "procedures", "observations"]):
            return parsed

        for wrapper_key in ["response", "result", "data", "output"]:
            wrapped = parsed.get(wrapper_key)
            if isinstance(wrapped, dict):
                if any(key in wrapped for key in ["conditions", "medications", "procedures", "observations"]):
                    return wrapped
            if isinstance(wrapped, str) and "{" in wrapped:
                try:
                    nested = json.loads(self._extract_json_fragment(wrapped))
                    if isinstance(nested, dict):
                        return nested
                except Exception:
                    pass
        return parsed

    def _parse_llm_content(self, content: str) -> Dict[str, List[str]]:
        parsed = json.loads(self._extract_json_fragment(content))
        parsed = self._coerce_llm_json_shape(parsed)
        result = self._empty_result()
        result["observations"] = []
        for key in ["conditions", "medications", "procedures", "observations"]:
            values = parsed.get(key, [])
            if isinstance(values, str):
                values = [values]
            if isinstance(values, list):
                result[key].extend([str(item).strip() for item in values if str(item).strip()])
        return self._dedupe_result(result)

    def _extract_with_llm(self, text: str) -> Dict[str, List[str]]:
        result = self._empty_result()
        result["observations"] = []
        if not self._looks_like_meaningful_residual(text):
            return result

        try:
            with httpx.Client(timeout=self.LLM_TIMEOUT) as client:
                response = client.post(
                    self.LLM_URL,
                    headers=self._llm_headers(),
                    json=self._llm_payload(text),
                )
                response.raise_for_status()
                body = response.json()

            choices = body.get("choices", [])
            if not choices:
                logger.warning("LLM returned empty choices.")
                return result

            message = choices[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, list):
                content = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
            if not isinstance(content, str) or not content.strip():
                logger.warning("LLM returned empty content.")
                return result

            logger.info(f"LLM raw content: {content[:500]}")
            parsed = self._parse_llm_content(content.strip())
            logger.info("LLM residual extraction succeeded.")
            return parsed
        except Exception as exc:
            logger.warning(f"LLM extraction failed: {exc}")
            return result

    def _finalize_result(self, original_text: str, result: Dict[str, List[str]]) -> Dict[str, List[str]]:
        finalized = self._dedupe_result(result)
        meaningful = any(
            finalized[key]
            for key in [
                "conditions",
                "medications",
                "procedures",
                "measurements",
                "symptoms_with_values",
                "times",
                "negations",
            ]
        )
        if not meaningful and original_text:
            finalized["observations"] = self._dedupe_list(finalized.get("observations", []) + [original_text])
        elif finalized["times"]:
            finalized["observations"] = [
                item
                for item in finalized.get("observations", [])
                if not re.fullmatch(r"[\d\s年前后月日小时周分]+", item)
            ]
        return finalized

    def _extract_entities_single(self, text: str) -> Dict[str, List[str]]:
        if not text or not isinstance(text, str):
            return self._empty_result()

        regex_result, residual_after_regex = self._build_regex_result(text)
        residual_after_regex = self._cleanup_leftover_text(residual_after_regex)

        ner_result, residual_after_ner, avg_ner_score = self._extract_with_ner(residual_after_regex)
        residual_after_ner = self._cleanup_leftover_text(residual_after_ner)

        llm_result = self._empty_result()
        llm_result["observations"] = []
        if self._looks_like_meaningful_residual(residual_after_ner):
            if (not any(ner_result[key] for key in ["conditions", "medications", "procedures"])) or (
                avg_ner_score and avg_ner_score < self.LLM_NER_CONFIDENCE_THRESHOLD + 0.08
            ):
                llm_result = self._extract_with_llm(residual_after_ner)

        merged = self._merge_results(regex_result, ner_result, llm_result)
        return self._finalize_result(text, merged)

    def extract_entities_batch(self, texts: List[str], batch_size: int = 16) -> List[Dict[str, List[str]]]:
        _ = batch_size
        return [self._extract_entities_single(text) for text in texts]

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        return self._extract_entities_single(text)
