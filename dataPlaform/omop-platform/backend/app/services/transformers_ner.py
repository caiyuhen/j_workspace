import logging
import os
import torch
import re

# Use HF-Mirror to accelerate model downloading in China
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from transformers import pipeline
from app.core.logger import data_logger

logger = data_logger

class TransformersNERMapper:
    """
    A lightweight wrapper around a Hugging Face Transformers NER model.
    By default, it uses a multilingual or Chinese-specific NER model
    capable of identifying diseases, symptoms, medications, etc.
    """
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TransformersNERMapper, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # 使用专门针对中文医疗 NER 微调的模型，替换通用模型
            # 该模型基于 CMeEE (中文医学命名实体识别) 数据集训练，能识别：疾病、临床表现、医疗设备、医疗程序、药物等
            # model_name = "shibing624/bert4ner-base-chinese"
            model_name = "shibing624/bert4ner-base-chinese"
            # 兼容性较好的通用 NER
            # model_name = "Babelscape/wikineural-multilingual-ner"
            # GPU check
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU (cuda:0)" if device == 0 else "CPU"
            
            logger.info(f"Loading Transformers NER model: {model_name} on {device_name}...")
            try:
                # aggregation_strategy="simple" groups B-LOC, I-LOC into a single LOC entity
                self.ner_pipeline = pipeline("ner", model=model_name, aggregation_strategy="simple", device=device)
                logger.info(f"Transformers NER model loaded successfully on {device_name}.")
            except Exception as e:
                logger.error(f"Failed to load NER model: {e}")
                self.ner_pipeline = None
            self._initialized = True

    def _extract_time_regex(self, text: str) -> list:
        times = []
        if not text or not isinstance(text, str): return times
        
        # 匹配相对时间: "3天前", "1个月后", "2周内"
        pattern_rel = r'(\d+[\s]*(?:年|个月|月|周|天|日|小时|分钟|分)[\s]*(?:前|后|内|以来))'
        matches_rel = re.finditer(pattern_rel, text)
        for m in matches_rel:
            times.append(m.group(1).strip())
            
        # 匹配绝对日期: "2023年5月12日", "2023-05-12"
        pattern_abs = r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2})'
        matches_abs = re.finditer(pattern_abs, text)
        for m in matches_abs:
            times.append(m.group(1).strip())
            
        return list(set(times))

    def _extract_negations(self, text: str) -> dict:
        """
        前置正则：专门拦截包含否定词的医学短语，防止大模型将其错误识别为既有疾病。
        例如将“否认高血压史”、“未见明显骨折”拦截为阴性观察。
        """
        negations = []
        cleaned_text = text
        
        # 匹配模式：(否认|无|未见|排除) + (可选修饰词) + (疾病/症状/部位) + (可选后缀如"史")
        pattern = r'(否认|无|未发现|未见)(?:明显)?([\u4e00-\u9fa5]{2,10}?)(?:病?史|异常|表现|体征)?(?=[，。；,\.;\n\r]|$)'
        
        for match in re.finditer(pattern, text):
            full_match = match.group(0)
            negation_word = match.group(1)
            entity = match.group(2)
            
            # 组装为排除性诊断格式
            negations.append(f"诊断：{entity}，否定词：{negation_word}")
            
            # 将该部分从原文中替换为空格，防止后续大模型再次错误提取
            cleaned_text = cleaned_text.replace(full_match, ' ' * len(full_match))
            
        return {"negations": negations, "remaining_text": cleaned_text}

    def _extract_drugs_regex(self, text: str) -> dict:
        """
        Extract medication name, dosage form, and route of administration using regex.
        Returns a dictionary with 'drugs' list and 'remaining_text'.
        """
        drugs = []
        cleaned_text = text
        if not text or not isinstance(text, str):
            return {"drugs": drugs, "remaining_text": cleaned_text}
            
        forms = r'(?:肠溶片|分散片|糖衣片|薄膜衣片|咀嚼片|口腔崩解片|片|胶囊|软胶囊|微丸|丸|颗粒|冲剂|注射液|注射用|粉针剂|口服液|糖浆|滴眼液|滴鼻液|滴耳液|软膏|乳膏|霜|凝胶|贴膏|贴剂|栓|散|气雾剂|喷雾剂|粉吸入剂|滴注液|溶液|混悬液|乳剂|剂)'
        routes = r'(?:静脉滴注|静滴|静脉注射|静注|肌肉注射|肌注|皮下注射|皮注|皮内注射|口服|吞服|含服|舌下含服|外用|涂抹|贴敷|雾化吸入|雾化|滴眼|滴鼻|滴耳|直肠给药|阴道给药|注射)'
        
        # P2: Drug + Form + Route? (e.g., 阿司匹林肠溶片静脉滴注)
        p2 = rf'([\u4e00-\u9fa5A-Za-z0-9]{{2,12}}?)({forms})(?:({routes})|(?=[，。；、\s]|$))'
        # P1: Form + Drug + Route? (e.g., 注射用头孢曲松钠)
        p1 = rf'({forms})([\u4e00-\u9fa5A-Za-z0-9]{{2,8}}?)(?:({routes})|(?=[，。；、\s]|$))'
        
        # Strip irrelevant prefix words
        prefix_pattern = r'^(?:住院|期间|给予|带药[：:]?|出院|用药[：:]?|使用|加用|服用|对症|支持|治疗|的|了|：|、|，|,|\s|。)+'
        
        # First match P2 (Drug + Form)
        for match in re.finditer(p2, cleaned_text):
            raw_drug = match.group(1)
            form = match.group(2)
            route = match.group(3) if match.group(3) else ""
            
            drug_name = re.sub(prefix_pattern, '', raw_drug)
            if len(drug_name) >= 2:
                # If no route is found but form implies it
                if not route:
                    if "注射" in form: route = "注射"
                    elif "片" in form or "胶囊" in form or "丸" in form: route = "口服"
                    
                drugs.append(f"药名：{drug_name} 剂型：{form} 给药方式：{route}")
                cleaned_text = cleaned_text.replace(match.group(0), ' ' * len(match.group(0)))
                
        # Then match P1 (Form + Drug)
        for match in re.finditer(p1, cleaned_text):
            form = match.group(1)
            raw_drug = match.group(2)
            route = match.group(3) if match.group(3) else ""
            
            drug_name = re.sub(prefix_pattern, '', raw_drug)
            if len(drug_name) >= 2:
                if not route:
                    if "注射" in form: route = "注射"
                    elif "片" in form or "胶囊" in form or "丸" in form: route = "口服"
                    
                drugs.append(f"药名：{drug_name} 剂型：{form} 给药方式：{route}")
                cleaned_text = cleaned_text.replace(match.group(0), ' ' * len(match.group(0)))
                
        return {"drugs": drugs, "remaining_text": cleaned_text}

    def _extract_measurements_regex(self, text: str) -> list:
        """
        Use Regex to accurately extract medical measurements with values and optional units.
        E.g. "检查项：空腹血糖 值:6.5", "WBC 6.5", "检查项：餐后血糖  值: 8.0 单位:mmol/L"
        """
        measurements = []
        if not text or not isinstance(text, str):
            return measurements
            
        # Pattern 1: With "检查项：" or "指标：" prefix (explicit)
        pattern1 = r'(?:检查项|指标)[：:\s]*([A-Za-z\u4e00-\u9fa50-9\-]+)[\s:：,，]*(?:value[：:]|值[：:]|为[：:]?|：)?\s*([\d\.\/]+)\s*(?:单位[：:])?\s*([^，。；,\s\n]+)?'
        
        # Pattern 2: Without prefix, but has typical measurement names or English acronyms
        pattern2 = r'(?<!检查项：)(?<!检查项:)(?<!检查项 )([A-Za-z\u4e00-\u9fa50-9\-]+(?:血糖|血压|心率|指标|血脂|胆固醇|蛋白|压|酸|酶|素|计数|比值|体积|浓度|饱和度|时间|宽度|百分比|发热|体温|症状)|(?!(?:value|单位|检查项|症状))[A-Za-z]{2,15}[A-Za-z0-9\-]{0,10})[\s:：,，]*(?:value[：:]|值[：:]|为[：:]?|：)?\s*([\d\.\/]+)\s*(?:单位[：:])?\s*([^，。；,\s\n]+)?(?![0-9\.\-\/])'
        
        # Pattern 3: With "症状：" prefix
        pattern3 = r'症状[：:\s]*([A-Za-z\u4e00-\u9fa50-9\-]+)[\s:：,，]*(?:value[：:]|值[：:]|为[：:]?|：)?\s*([\d\.\/]+)\s*(?:单位[：:])?\s*([^，。；,\s\n]+)?'
        
        # Pattern 4: Symptom + Duration (e.g. "关节疼痛1周")
        pattern4_after = r'([\u4e00-\u9fa5]{2,6}(?:痛|晕|热|咳|闷|悸|力|心|吐|泻|肿|麻|痒|血|斑|疹|疮|瘤|癌|炎|病|不适|异常))(\d+(?:年|个月|月|周|天|日|小时|分钟|分)(?:余|以来)?)'
        
        # Pattern 5: Duration + Symptom (e.g. "1天前起床时突发头晕")
        pattern5_before = r'(\d+(?:年|个月|月|周|天|日|小时|分钟|分)(?:前|以来)?)[^，。；？！\n]{0,10}?(?:突发|出现|伴有)?([\u4e00-\u9fa5]{2,6}(?:痛|晕|热|咳|闷|悸|力|心|吐|泻|肿|麻|痒|血|斑|疹|疮|瘤|癌|炎|病|不适|异常))'
        
        all_matches = []
        
        # Find time+symptom
        for match in re.finditer(pattern5_before, text):
            all_matches.append({"type": "time_symptom", "match": match})
            text = text.replace(match.group(0), ' ' * len(match.group(0)))
            
        # Find symptom+time
        for match in re.finditer(pattern4_after, text):
            all_matches.append({"type": "symptom_time", "match": match})
            text = text.replace(match.group(0), ' ' * len(match.group(0)))
            
        # Find explicit symptoms
        for match in re.finditer(pattern3, text):
            all_matches.append({"type": "symptom", "match": match})
            text = text.replace(match.group(0), ' ' * len(match.group(0))) # Replace to prevent double matching
            
        # Find explicit measurements
        for match in re.finditer(pattern1, text):
            all_matches.append({"type": "measurement", "match": match})
            text = text.replace(match.group(0), ' ' * len(match.group(0)))
            
        # Find fallback items
        for match in re.finditer(pattern2, text):
            all_matches.append({"type": "measurement", "match": match})
            
        for item in all_matches:
            match = item["match"]
            m_type = item["type"]
            
            if m_type == "symptom_time":
                symptom_name = match.group(1).strip()
                duration = match.group(2).strip()
                measurements.append({
                    "type": "symptom",
                    "name": f"症状：{symptom_name}",
                    "value": duration,
                    "unit": "持续时间"
                })
            elif m_type == "time_symptom":
                duration = match.group(1).strip()
                symptom_name = match.group(2).strip()
                measurements.append({
                    "type": "symptom",
                    "name": f"症状：{symptom_name}",
                    "value": duration,
                    "unit": "持续时间"
                })
            else:
                name = match.group(1).strip()
                value = match.group(2).strip()
                unit = match.group(3).strip() if match.lastindex >= 3 and match.group(3) else ""
                
                # Clean up unit that caught trailing descriptive text
                if unit and re.search(r'(趋势|平稳|好转|异常|正常|偏高|偏低|阳性|阴性|表现|注意|目前|建议|复查|由于|符合)', unit):
                    # We just discard the invalid unit
                    unit = ""
                    
                # Auto-infer units if missing
                if not unit:
                    if "血糖" in name:
                        unit = "mmol/L"
                    elif "心率" in name:
                        unit = "次/分"
                    elif "压" in name and ("血" in name or "收缩" in name or "舒张" in name):
                        unit = "mmHg"
                    elif "体温" in name or "发热" in name:
                        unit = "度"
                    elif "饱和度" in name:
                        unit = "%"
                
                # Filter out pure numbers as names or empty names
                if not name or name.isdigit():
                    continue
                    
                # Avoid extracting pure dates like 2023.05
                if "." in value and len(value.split(".")[0]) == 4:
                    continue
                    
                measurements.append({
                    "type": m_type,
                    "name": name,
                    "value": value,
                    "unit": unit
                })
                
        return measurements

    def extract_entities_batch(self, texts: list, batch_size: int = 16) -> list:
        """
        Extracts entities from a batch of texts.
        This utilizes GPU (if available) efficiently via Transformers batching.
        """
        empty_result = lambda t: {"conditions": [], "medications": [], "procedures": [], "measurements": [], "symptoms_with_values": [], "times": [], "observations": [t] if t else [], "negations": []}
        
        if not texts:
            return []

        # --- 第一阶段：在进入大模型前进行正则清洗和拦截 ---
        cleaned_texts = []
        pre_extracted_data = [] # 保存每条文本被正则提前抓走的数据
        
        for text in texts:
            # 初始化该条文本的空字典
            base_dict = {"conditions": [], "medications": [], "procedures": [], "measurements": [], "symptoms_with_values": [], "times": [], "observations": [], "negations": []}
            
            if not isinstance(text, str) or not text.strip():
                cleaned_texts.append("无")
                pre_extracted_data.append(base_dict)
                continue
                
            # 1. 否定词拦截
            neg_res = self._extract_negations(text)
            base_dict["negations"].extend(neg_res["negations"])
            clean_t = neg_res["remaining_text"]
            
            # 2. 药品、剂型、给药方式提取
            drug_res = self._extract_drugs_regex(clean_t)
            base_dict["medications"].extend(drug_res["drugs"])
            clean_t = drug_res["remaining_text"]
            
            # 3. 指标和症状提取
            regex_measurements = self._extract_measurements_regex(clean_t)
            for rm in regex_measurements:
                unit_str = f" 单位:{rm['unit']}" if rm['unit'] else ""
                if rm['type'] == 'symptom':
                    base_dict["symptoms_with_values"].append(f"症状：{rm['name']} 值:{rm['value']}{unit_str}")
                else:
                    base_dict["measurements"].append(f"检查项：{rm['name']} 值:{rm['value']}{unit_str}")
                    
            # 3. 时间提取
            times = self._extract_time_regex(clean_t)
            for t in times:
                base_dict["times"].append(t)
                
            cleaned_texts.append(clean_t if clean_t.strip() else "无")
            pre_extracted_data.append(base_dict)

        final_results = []
        
        # If NER model failed to load, just return the regex extracted data
        if not self.ner_pipeline:
            for idx, result in enumerate(pre_extracted_data):
                original_text = texts[idx]
                if not any([result["conditions"], result["medications"], result["procedures"], result["measurements"], result["symptoms_with_values"], result["times"], result["negations"]]):
                    result["observations"].append(original_text)
                final_results.append(result)
            return final_results
            
        try:
            # The pipeline supports batching list of strings
            batch_outputs = self.ner_pipeline(cleaned_texts, batch_size=batch_size)
            
            # If a single string was passed (due to len(texts)==1), pipeline returns List[dict] instead of List[List[dict]]
            if len(cleaned_texts) == 1 and (not isinstance(batch_outputs, list) or (len(batch_outputs) > 0 and isinstance(batch_outputs[0], dict))):
                batch_outputs = [batch_outputs]

            for idx, entities in enumerate(batch_outputs):
                original_text = texts[idx]
                result = pre_extracted_data[idx]
                
                # If it was an invalid text originally, just return the empty structure
                if not isinstance(original_text, str) or not original_text.strip():
                    final_results.append(empty_result(original_text))
                    continue
                    
                # We want to remove the extracted measurement texts from NER processing mentally, 
                # but for simplicity we'll just ignore NER fragments that overlap with numbers
                
                for ent in entities:
                    entity_group = ent.get("entity_group", "")
                    word = ent.get("word", "").strip()
                    # Clean up token artifacts (like ##) from subword tokenization
                    word = word.replace('##', '')
                    
                    if not word or re.match(r'^[\d\.\s]+$', word) or word in ["天", "前", "后", "月", "年", "小时"]:
                        # Skip pure numbers or time fragments handled by regex
                        continue
                        
                    if 'DIS' in entity_group or 'SYM' in entity_group or entity_group in ["DISEASE", "SYMPTOM", "disease", "symptom"]:
                        word = re.sub(r'^(?:入院|出院|初步|确诊|补充)?(?:诊断|印象|考虑为|：|:)+', '', word)
                        word = re.sub(r'^符合(.*?)(?:表现|改变|特征|影像)?$', r'\1', word)
                        word = re.sub(r'表现$', '', word)
                        if word and len(word) > 1:
                            result["conditions"].append(word)
                    elif 'DRU' in entity_group or entity_group in ["MED", "MEDICINE", "DRUG"]:
                        result["medications"].append(word)
                    elif 'PRO' in entity_group or 'EQU' in entity_group or entity_group in ["PROCEDURE"]:
                        result["procedures"].append(word)
                    elif 'BOD' in entity_group or entity_group in ["BODY", "LOC"]:
                        result["observations"].append(f"部位: {word}")
                    else:
                        # Some generic models output LOC/ORG/PER
                        if entity_group not in ["O", ""]:
                            result["observations"].append(f"{entity_group}: {word}")
                        
                # Deduplicate entities
                result["conditions"] = list(dict.fromkeys(result["conditions"]))
                result["medications"] = list(dict.fromkeys(result["medications"]))
                result["procedures"] = list(dict.fromkeys(result["procedures"]))
                result["measurements"] = list(dict.fromkeys(result["measurements"]))
                result["symptoms_with_values"] = list(dict.fromkeys(result["symptoms_with_values"]))
                result["times"] = list(dict.fromkeys(result["times"]))
                result["observations"] = list(dict.fromkeys(result["observations"]))
                result["negations"] = list(dict.fromkeys(result["negations"]))
                
                # If the model didn't find anything specific, keep the whole text as an observation
                if not any([result["conditions"], result["medications"], result["procedures"], result["measurements"], result["symptoms_with_values"], result["times"]]):
                    result["observations"].append(original_text)
                elif result["observations"]:
                    # Clean up random fragments like "3 天" if time was successfully extracted
                    if len(result["times"]) > 0:
                        result["observations"] = [o for o in result["observations"] if not re.match(r'^[\d\s天前后月年小时]+$', o)]
                    
                final_results.append(result)
                
            return final_results
            
        except Exception as e:
            logger.warning(f"Batch NER extraction failed: {e}")
            return [empty_result(t) for t in texts]

    def extract_entities(self, text: str) -> dict:
        """
        Extracts entities from the given text using the NER pipeline.
        Returns a dictionary categorizing entities by type.
        """
        result = {
            "conditions": [],
            "medications": [],
            "procedures": [],
            "measurements": [],
            "symptoms_with_values": [],
            "times": [],
            "observations": [],
            "negations": []
        }
        
        if not text or not isinstance(text, str):
            return result

        try:
            # 0. 前置过滤：否定词拦截 (防止大模型幻觉)
            negation_result = self._extract_negations(text)
            result["negations"].extend(negation_result["negations"])
            text_for_ner = negation_result["remaining_text"]

            # 1. Regex measurements & symptoms
            regex_measurements = self._extract_measurements_regex(text_for_ner)
            for rm in regex_measurements:
                unit_str = f" 单位:{rm['unit']}" if rm['unit'] else ""
                if rm['type'] == 'symptom':
                    result["symptoms_with_values"].append(f"症状：{rm['name']} 值:{rm['value']}{unit_str}")
                else:
                    result["measurements"].append(f"检查项：{rm['name']} 值:{rm['value']}{unit_str}")
                    
            # 2. Extract times
            times = self._extract_time_regex(text_for_ner)
            for t in times:
                result["times"].append(t)
                
            if not self.ner_pipeline:
                if not any([result["conditions"], result["medications"], result["procedures"], result["measurements"], result["symptoms_with_values"], result["times"], result["negations"]]):
                    result["observations"].append(text)
                return result
                
            entities = self.ner_pipeline(text_for_ner)
            
            # Map generic NER tags to OMOP domains
            for ent in entities:
                entity_group = ent.get("entity_group", "")
                word = ent.get("word", "").strip()
                # Clean up token artifacts (like ##) from subword tokenization
                word = word.replace('##', '')
                
                if not word or re.match(r'^[\d\.\s]+$', word) or word in ["天", "前", "后", "月", "年", "小时"]:
                    continue
                    
                if 'DIS' in entity_group or 'SYM' in entity_group or entity_group in ["DISEASE", "SYMPTOM", "disease", "symptom", "ORG", "PER", "LOC"]:
                    # If a generic model is used, we roughly map LOC/ORG to observations, but some models don't have medical tags.
                    # Since we use medical model, we just keep this logic robust.
                    pass
                    
                if 'DIS' in entity_group or 'SYM' in entity_group or entity_group in ["DISEASE", "SYMPTOM", "disease", "symptom"]:
                    result["conditions"].append(word)
                elif 'DRU' in entity_group or entity_group in ["MED", "MEDICINE", "DRUG"]:
                    result["medications"].append(word)
                elif 'PRO' in entity_group or 'EQU' in entity_group or entity_group in ["PROCEDURE"]:
                    result["procedures"].append(word)
                elif 'BOD' in entity_group or entity_group in ["BODY", "LOC"]:
                    # Body parts might be observations
                    result["observations"].append(f"部位: {word}")
                else:
                    # Unclassified entities go to observations
                    if entity_group not in ["O", ""]:
                        result["observations"].append(f"{entity_group}: {word}")
                    
            # If the model didn't find anything specific, keep the whole text as an observation
            if not any([result["conditions"], result["medications"], result["procedures"], result["measurements"], result["symptoms_with_values"], result["times"]]):
                result["observations"].append(text)
            elif result["observations"]:
                if len(result["times"]) > 0:
                    result["observations"] = [o for o in result["observations"] if not re.match(r'^[\d\s天前后月年小时]+$', o)]
                
        except Exception as e:
            logger.warning(f"NER extraction failed for text '{text}': {e}")
            result["observations"].append(text)
            
        return result
