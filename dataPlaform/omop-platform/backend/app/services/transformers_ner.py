import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
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
    LLM_BATCH_MAX_WORKERS = 4
    NOTE_SECTION_HEADER_PATTERN = re.compile(
        r"(主诉|现病史|既往史|个人史|过敏史|家族史|查体|体格检查|辅助检查|检验|影像学检查|诊断|出院诊断|治疗计划|处理意见|出院医嘱)\s*[:：]"
    )

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

        self._llm_client = httpx.Client(
            timeout=self.LLM_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

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
            "devices": [],
            "specimens": [],
            "death": [],
            "providers": [],
            "care_sites": [],
            "note_nlp_items": [],
        }

    def _dedupe_list(self, items: List[Any]) -> List[Any]:
        clean_items: List[Any] = []
        seen = set()
        for item in items:
            if isinstance(item, dict):
                normalized = json.dumps(item, ensure_ascii=False, sort_keys=True)
                if normalized in seen:
                    continue
                seen.add(normalized)
                clean_items.append(item)
                continue
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
            "devices",
            "specimens",
            "death",
            "providers",
            "care_sites",
            "note_nlp_items",
        ]:
            result[key] = self._dedupe_list(result.get(key, []))
        return result

    @staticmethod
    def _format_timing_log(prefix: str, metrics: Dict[str, float], extra: Optional[Dict[str, Any]] = None) -> str:
        metric_parts = [f"{key}={value:.2f}" for key, value in metrics.items()]
        extra_parts = [f"{key}={value}" for key, value in (extra or {}).items()]
        joined = " ".join(metric_parts + extra_parts)
        return f"{prefix} {joined}".strip()

    def _merge_results(self, *results: Dict[str, List[str]]) -> Dict[str, List[str]]:
        merged = self._empty_result()
        merged["observations"] = []
        for result in results:
            if not result:
                continue
            for key in merged.keys():
                merged[key].extend(result.get(key, []))
        return self._dedupe_result(merged)

    def _append_note_nlp_item(
        self,
        result: Dict[str, List[Any]],
        domain: str,
        text: str,
        normalized_value: Optional[str] = None,
        confidence: Optional[float] = None,
        source_layer: str = "unknown",
        negated: bool = False,
        offset_start: Optional[int] = None,
        offset_end: Optional[int] = None,
    ) -> None:
        if not text:
            return

        item: Dict[str, Any] = {
            "domain": domain,
            "text": text,
            "normalized_value": normalized_value if normalized_value is not None else text,
            "source_layer": source_layer,
            "negated": negated,
        }
        if confidence is not None:
            item["confidence"] = round(float(confidence), 4)
        if offset_start is not None:
            item["offset_start"] = int(offset_start)
        if offset_end is not None:
            item["offset_end"] = int(offset_end)
        result["note_nlp_items"].append(item)

    def _bucket_to_note_domain(self, bucket: str) -> str:
        return {
            "conditions": "condition",
            "medications": "medication",
            "procedures": "procedure",
            "measurements": "measurement",
            "symptoms_with_values": "symptom",
            "times": "time",
            "observations": "observation",
            "negations": "negation",
            "devices": "device",
            "specimens": "specimen",
            "death": "death",
            "providers": "provider",
            "care_sites": "care_site",
        }.get(bucket, bucket)

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

    @staticmethod
    def _find_text_span(text: str, needle: str, used_spans: Optional[List[Tuple[int, int]]] = None) -> Tuple[Optional[int], Optional[int]]:
        if not text or not needle:
            return None, None

        start = 0
        while True:
            idx = text.find(needle, start)
            if idx == -1:
                return None, None
            end = idx + len(needle)
            overlapped = any(not (end <= used_start or idx >= used_end) for used_start, used_end in (used_spans or []))
            if not overlapped:
                return idx, end
            start = idx + 1

    def _find_text_span_by_candidates(
        self,
        text: str,
        candidates: List[str],
        used_spans: Optional[List[Tuple[int, int]]] = None,
    ) -> Tuple[Optional[int], Optional[int]]:
        for candidate in candidates:
            start, end = self._find_text_span(text, candidate, used_spans=used_spans)
            if start is not None and end is not None:
                return start, end
        return None, None

    @classmethod
    @lru_cache(maxsize=4096)
    def _extract_text_sections_cached(cls, text: str) -> Tuple[Tuple[str, int, int], ...]:
        if not text:
            return ()

        matches = list(cls.NOTE_SECTION_HEADER_PATTERN.finditer(text))
        if not matches:
            return ()

        sections: List[Tuple[str, int, int]] = []
        for idx, match in enumerate(matches):
            label = match.group(1).strip()
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            sections.append((label, start, end))
        return tuple(sections)

    @classmethod
    def _extract_text_sections(cls, text: str) -> List[Dict[str, Any]]:
        return [
            {
                "label": label,
                "start": start,
                "end": end,
            }
            for label, start, end in cls._extract_text_sections_cached(text)
        ]

    @staticmethod
    def _assign_sections_to_items(result: Dict[str, List[Any]], text: str) -> None:
        sections = TransformersNERMapper._extract_text_sections(text)
        if not sections:
            return

        for item in result.get("note_nlp_items", []):
            if not isinstance(item, dict) or item.get("section"):
                continue
            offset_start = item.get("offset_start")
            if offset_start is None:
                continue
            for section in sections:
                if section["start"] <= offset_start < section["end"]:
                    item["section"] = section["label"]
                    break

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

    def _extract_time_regex(self, text: str) -> Tuple[List[Dict[str, Any]], str]:
        if not text or not isinstance(text, str):
            return [], text

        times: List[Dict[str, Any]] = []
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
                times.append(
                    {
                        "text": value,
                        "start": match.start(1),
                        "end": match.end(1),
                    }
                )
                cleaned = self._remove_span(cleaned, match.start(1), match.end(1))
        return times, cleaned

    def _extract_negations(self, text: str) -> Dict[str, Any]:
        negations: List[Dict[str, Any]] = []
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
            negations.append(
                {
                    "text": f"诊断：{entity} ，否定词：{negation_word}",
                    "start": match.start(),
                    "end": match.end(),
                }
            )
            cleaned_text = cleaned_text.replace(full_match, " " * len(full_match), 1)

        return {"negations": negations, "remaining_text": cleaned_text}

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

    def _extract_measurements_regex(self, text: str) -> Tuple[List[Dict[str, Any]], str]:
        measurements: List[Dict[str, str]] = []
        cleaned = text
        if not text or not isinstance(text, str):
            return measurements, cleaned

        symptom_pattern = r"(?:[\u4e00-\u9fa5]{0,10}(?:疼痛|头晕|发热|咳嗽|胸闷|恶心|呕吐|乏力|腹痛|麻木|出血|水肿|不适))"

        specs = [
            (
                "symptom_after",
                rf"({symptom_pattern})\s*(\d+(?:年|个月|月|周|天|日|小时|分钟|分))",
            ),
            (
                "symptom_before",
                rf"(\d+(?:年|个月|月|周|天|日|小时|分钟|分))(?:前|来)?[^，。；,\n]{{0,12}}?(?:出现|伴有|突发|起床时)?({symptom_pattern})",
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
                            "start": match.start(),
                            "end": match.end(),
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
                            "start": match.start(),
                            "end": match.end(),
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
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )
                cleaned = self._remove_span(cleaned, match.start(), match.end())

        return measurements, cleaned

    def _extract_domain_regex(self, text: str) -> Tuple[Dict[str, List[Dict[str, Any]]], str]:
        result = {
            "devices": [],
            "specimens": [],
            "death": [],
            "providers": [],
            "care_sites": [],
        }
        cleaned = text
        if not text or not isinstance(text, str):
            return result, cleaned

        patterns = {
            "devices": [
                r"(冠脉支架|支架|起搏器|导管|引流管|呼吸机)",
            ],
            "specimens": [
                r"(静脉血|动脉血|血清|血浆|尿液|尿标本|粪便|痰液|组织标本|血标本)",
            ],
            "death": [
                r"(抢救无效死亡|临床死亡|死亡)",
            ],
            "providers": [
                r"([王李张刘陈杨黄赵周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段雷钱汤尹黎易常武乔贺赖龚文]+(?:主任|医生|医师))",
            ],
            "care_sites": [
                r"(心内科|心外科|急诊科|ICU|重症医学科|检验科|影像科|放射科|呼吸科|神经内科|消化内科|肾内科|病理科|门诊|病区)",
            ],
        }

        for bucket, bucket_patterns in patterns.items():
            for pattern in bucket_patterns:
                for match in list(re.finditer(pattern, cleaned)):
                    value = match.group(1).strip() if match.lastindex else match.group(0).strip()
                    if not value:
                        continue
                    result[bucket].append(
                        {
                            "text": value,
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )
                    cleaned = self._remove_span(cleaned, match.start(), match.end())
        return result, cleaned

    def _build_regex_result(self, text: str) -> Tuple[Dict[str, List[str]], str]:
        result = self._empty_result()
        result["observations"] = []
        residual = text

        neg_res = self._extract_negations(residual)
        result["negations"].extend([item["text"] for item in neg_res["negations"]])
        for negation in neg_res["negations"]:
            self._append_note_nlp_item(
                result,
                "negation",
                negation["text"],
                normalized_value=negation["text"],
                source_layer="regex",
                negated=True,
                offset_start=negation["start"],
                offset_end=negation["end"],
            )
        residual = neg_res["remaining_text"]

        drug_res = self._extract_drugs_regex(residual)
        result["medications"].extend(drug_res["drugs"])
        residual = drug_res["remaining_text"]

        regex_measurements, residual = self._extract_measurements_regex(residual)
        for item in regex_measurements:
            unit_str = f" 单位:{item['unit']}" if item.get("unit") else ""
            if item["type"] == "symptom":
                symptom_text = f"{item['name']} 持续时间：{item['value']}"
                result["symptoms_with_values"].append(symptom_text)
                self._append_note_nlp_item(
                    result,
                    "symptom",
                    symptom_text,
                    normalized_value=item["name"],
                    source_layer="regex",
                    offset_start=item.get("start"),
                    offset_end=item.get("end"),
                )
            else:
                measurement_text = f"检查项：{item['name']} 值:{item['value']}{unit_str}"
                result["measurements"].append(measurement_text)
                self._append_note_nlp_item(
                    result,
                    "measurement",
                    measurement_text,
                    normalized_value=item["name"],
                    source_layer="regex",
                    offset_start=item.get("start"),
                    offset_end=item.get("end"),
                )

        times, residual = self._extract_time_regex(residual)
        result["times"].extend([item["text"] for item in times])
        for time_item in times:
            self._append_note_nlp_item(
                result,
                "time",
                time_item["text"],
                normalized_value=time_item["text"],
                source_layer="regex",
                offset_start=time_item["start"],
                offset_end=time_item["end"],
            )

        domain_result, residual = self._extract_domain_regex(residual)
        for key, values in domain_result.items():
            result[key].extend([item["text"] for item in values])
            domain = self._bucket_to_note_domain(key)
            for value in values:
                self._append_note_nlp_item(
                    result,
                    domain,
                    value["text"],
                    normalized_value=value["text"],
                    source_layer="regex",
                    offset_start=value["start"],
                    offset_end=value["end"],
                )

        self._assign_sections_to_items(result, text)
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

    def _collect_ner_result(self, text: str, entities: List[Dict[str, Any]]) -> Tuple[Dict[str, List[str]], str, float]:
        result = self._empty_result()
        result["observations"] = []
        residual = text
        scores: List[float] = []
        used_spans: List[Tuple[int, int]] = []

        for ent in entities or []:
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
            offset_start, offset_end = self._find_text_span(text, word, used_spans=used_spans)
            if offset_start is not None and offset_end is not None:
                used_spans.append((offset_start, offset_end))
            self._append_note_nlp_item(
                result,
                self._bucket_to_note_domain(bucket),
                mapped_word,
                normalized_value=mapped_word,
                confidence=score,
                source_layer="ner",
                offset_start=offset_start,
                offset_end=offset_end,
            )
            scores.append(score)
            residual = re.sub(re.escape(word), " ", residual, count=1)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        self._assign_sections_to_items(result, text)
        return self._dedupe_result(result), residual, avg_score

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

        return self._collect_ner_result(text, entities)

    def _extract_with_ner_batch(
        self, texts: List[str], batch_size: int
    ) -> List[Tuple[Dict[str, List[str]], str, float]]:
        empty_outputs = [
            (self._empty_result(), text if isinstance(text, str) else "", 0.0)
            for text in texts
        ]
        if not texts or not self.ner_pipeline:
            return empty_outputs

        indexed_texts = [
            (idx, text)
            for idx, text in enumerate(texts)
            if isinstance(text, str) and text.strip()
        ]
        if not indexed_texts:
            return empty_outputs

        batched_texts = [text for _, text in indexed_texts]
        try:
            entity_batches = self.ner_pipeline(batched_texts, batch_size=batch_size)
        except TypeError:
            entity_batches = self.ner_pipeline(batched_texts)
        except Exception as exc:
            logger.warning(f"NER batch extraction failed: {exc}")
            return empty_outputs

        if entity_batches and isinstance(entity_batches[0], dict):
            entity_batches = [entity_batches]

        outputs = list(empty_outputs)
        for (idx, text), entities in zip(indexed_texts, entity_batches):
            outputs[idx] = self._collect_ner_result(text, entities)
        return outputs

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
            'The required schema is {"conditions":[],"medications":[],"procedures":[],"observations":[],"devices":[],"specimens":[],"death":[],"providers":[],"care_sites":[]}. '
            "conditions means diseases, diagnoses, and symptom phrases. "
            "medications means medication names only. "
            "procedures means surgeries, procedures, and examinations. "
            "observations means body parts, signs, and other medical observations. "
            "devices means implants and medical devices. "
            "specimens means sample types such as blood or urine. "
            "death means death events or death descriptions. "
            "providers means clinician names or roles. "
            "care_sites means departments, wards, or service locations. "
            "Never return keys such as response, result, summary, data, or reasoning."
        )
        user_prompt = (
            "Extract medical entities from the following text. Return JSON only.\n"
            "Example output:\n"
            '{"conditions":["急性胆囊炎"],"medications":[],"procedures":["支架植入术"],"observations":["右上腹压痛"],"devices":["冠脉支架"],"specimens":["静脉血"],"death":[],"providers":["李主任"],"care_sites":["心内科"]}\n'
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
                if any(
                    key in wrapped
                    for key in [
                        "conditions",
                        "medications",
                        "procedures",
                        "observations",
                        "devices",
                        "specimens",
                        "death",
                        "providers",
                        "care_sites",
                    ]
                ):
                    return wrapped
            if isinstance(wrapped, str) and "{" in wrapped:
                try:
                    nested = json.loads(self._extract_json_fragment(wrapped))
                    if isinstance(nested, dict):
                        return nested
                except Exception:
                    pass
        return parsed

    def _parse_llm_content(self, content: str, original_text: str = "") -> Dict[str, List[str]]:
        parsed = json.loads(self._extract_json_fragment(content))
        parsed = self._coerce_llm_json_shape(parsed)
        result = self._empty_result()
        result["observations"] = []
        used_spans: List[Tuple[int, int]] = []
        for key in [
            "conditions",
            "medications",
            "procedures",
            "observations",
            "devices",
            "specimens",
            "death",
            "providers",
            "care_sites",
        ]:
            values = parsed.get(key, [])
            if isinstance(values, str):
                values = [values]
            if isinstance(values, list):
                domain = self._bucket_to_note_domain(key)
                for item in values:
                    if isinstance(item, dict):
                        text_value = str(item.get("text", "")).strip()
                        normalized_value = str(item.get("normalized_value", text_value)).strip() or text_value
                    else:
                        text_value = str(item).strip()
                        normalized_value = text_value

                    if not text_value:
                        continue

                    result[key].append(text_value)
                    offset_start, offset_end = self._find_text_span_by_candidates(
                        original_text,
                        [text_value, normalized_value],
                        used_spans=used_spans,
                    )
                    if offset_start is not None and offset_end is not None:
                        used_spans.append((offset_start, offset_end))
                    self._append_note_nlp_item(
                        result,
                        domain,
                        text_value,
                        normalized_value=normalized_value,
                        source_layer="llm",
                        offset_start=offset_start,
                        offset_end=offset_end,
                    )
        self._assign_sections_to_items(result, original_text)
        return self._dedupe_result(result)

    def _extract_with_llm(
        self,
        text: str,
        client: Optional[httpx.Client] = None,
        original_text: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        result = self._empty_result()
        result["observations"] = []
        if not self._looks_like_meaningful_residual(text):
            return result

        owns_client = False
        llm_client = client or getattr(self, "_llm_client", None)
        try:
            if llm_client is None:
                llm_client = httpx.Client(timeout=self.LLM_TIMEOUT)
                owns_client = True

            response = llm_client.post(
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
            parsed = self._parse_llm_content(content.strip(), original_text=original_text or text)
            logger.info("LLM residual extraction succeeded.")
            return parsed
        except Exception as exc:
            logger.warning(f"LLM extraction failed: {exc}")
            return result
        finally:
            if owns_client and llm_client is not None:
                llm_client.close()

    def _extract_with_llm_batch(
        self, jobs: List[Tuple[int, str, str]], max_workers: Optional[int] = None
    ) -> List[Dict[str, List[str]]]:
        if not jobs:
            return []

        worker_count = max(1, min(max_workers or self.LLM_BATCH_MAX_WORKERS, len(jobs)))
        results: List[Optional[Dict[str, List[str]]]] = [None] * len(jobs)

        def run_job(job_position: int, text: str, original_text: str) -> Tuple[int, Dict[str, List[str]]]:
            return job_position, self._extract_with_llm(text, original_text=original_text)

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(run_job, job_position, text, original_text): job_position
                for job_position, (_, text, original_text) in enumerate(jobs)
            }
            for future in as_completed(future_map):
                job_position, result = future.result()
                results[job_position] = result

        return [result or self._empty_result() for result in results]

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

    def _should_use_llm(self, residual_text: str, ner_result: Dict[str, List[str]], avg_ner_score: float) -> bool:
        if not self._looks_like_meaningful_residual(residual_text):
            return False
        if not any(ner_result[key] for key in ["conditions", "medications", "procedures"]):
            return True
        return bool(avg_ner_score and avg_ner_score < self.LLM_NER_CONFIDENCE_THRESHOLD + 0.08)

    def _extract_entities_single(self, text: str) -> Dict[str, List[str]]:
        if not text or not isinstance(text, str):
            return self._empty_result()

        total_started_at = time.perf_counter()

        regex_started_at = time.perf_counter()
        regex_result, residual_after_regex = self._build_regex_result(text)
        residual_after_regex = self._cleanup_leftover_text(residual_after_regex)
        regex_ms = (time.perf_counter() - regex_started_at) * 1000

        ner_started_at = time.perf_counter()
        ner_result, residual_after_ner, avg_ner_score = self._extract_with_ner(residual_after_regex)
        residual_after_ner = self._cleanup_leftover_text(residual_after_ner)
        ner_ms = (time.perf_counter() - ner_started_at) * 1000

        llm_result = self._empty_result()
        llm_result["observations"] = []
        llm_ms = 0.0
        if self._should_use_llm(residual_after_ner, ner_result, avg_ner_score):
            llm_started_at = time.perf_counter()
            llm_result = self._extract_with_llm(residual_after_ner, original_text=text)
            llm_ms = (time.perf_counter() - llm_started_at) * 1000

        merged = self._merge_results(regex_result, ner_result, llm_result)
        finalized = self._finalize_result(text, merged)

        logger.info(
            self._format_timing_log(
                "[NLP_SINGLE]",
                {
                    "regex_ms": regex_ms,
                    "ner_ms": ner_ms,
                    "llm_ms": llm_ms,
                    "total_ms": (time.perf_counter() - total_started_at) * 1000,
                },
                extra={"text_len": len(text)},
            )
        )
        return finalized

    def extract_entities_batch(self, texts: List[str], batch_size: int = 16) -> List[Dict[str, List[str]]]:
        if not texts:
            return []

        total_started_at = time.perf_counter()
        regex_results: List[Dict[str, List[str]]] = []
        residuals_after_regex: List[str] = []

        regex_started_at = time.perf_counter()
        for text in texts:
            if not text or not isinstance(text, str):
                regex_results.append(self._empty_result())
                residuals_after_regex.append("")
                continue

            regex_result, residual_after_regex = self._build_regex_result(text)
            regex_results.append(regex_result)
            residuals_after_regex.append(self._cleanup_leftover_text(residual_after_regex))
        regex_ms = (time.perf_counter() - regex_started_at) * 1000

        ner_started_at = time.perf_counter()
        ner_outputs = self._extract_with_ner_batch(residuals_after_regex, batch_size=batch_size)
        ner_ms = (time.perf_counter() - ner_started_at) * 1000
        llm_jobs: List[Tuple[int, str, str]] = []

        for idx, text in enumerate(texts):
            if not text or not isinstance(text, str):
                continue
            ner_result, residual_after_ner, avg_ner_score = ner_outputs[idx]
            residual_after_ner = self._cleanup_leftover_text(residual_after_ner)
            if self._should_use_llm(residual_after_ner, ner_result, avg_ner_score):
                llm_jobs.append((idx, residual_after_ner, text))

        llm_results_by_index: Dict[int, Dict[str, List[str]]] = {}
        llm_ms_total = 0.0
        if llm_jobs:
            llm_started_at = time.perf_counter()
            batch_llm_results = self._extract_with_llm_batch(llm_jobs, max_workers=self.LLM_BATCH_MAX_WORKERS)
            llm_ms_total = (time.perf_counter() - llm_started_at) * 1000
            for (job_index, _, _), llm_result in zip(llm_jobs, batch_llm_results):
                llm_results_by_index[job_index] = llm_result

        final_results: List[Dict[str, List[str]]] = []
        for idx, text in enumerate(texts):
            if not text or not isinstance(text, str):
                final_results.append(self._empty_result())
                continue

            ner_result, residual_after_ner, avg_ner_score = ner_outputs[idx]
            residual_after_ner = self._cleanup_leftover_text(residual_after_ner)

            llm_result = self._empty_result()
            llm_result["observations"] = []
            if idx in llm_results_by_index:
                llm_result = llm_results_by_index[idx]

            merged = self._merge_results(regex_results[idx], ner_result, llm_result)
            final_results.append(self._finalize_result(text, merged))

        logger.info(
            self._format_timing_log(
                "[NLP_BATCH]",
                {
                    "regex_ms": regex_ms,
                    "ner_ms": ner_ms,
                    "llm_ms": llm_ms_total,
                    "total_ms": (time.perf_counter() - total_started_at) * 1000,
                },
                extra={"texts": len(texts), "batch_size": batch_size},
            )
        )
        return final_results

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        return self._extract_entities_single(text)
