import logging
import os
import torch
import re

# Use HF-Mirror to accelerate model downloading in China
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from transformers import pipeline

logger = logging.getLogger(__name__)

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
            model_name = "ckiplab/bert-base-chinese-ner"
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

    def _extract_measurements_regex(self, text: str) -> list:
        """
        Use Regex to accurately extract medical measurements with values and optional units.
        E.g. "空腹血糖 6.5", "收缩压 120mmHg"
        """
        measurements = []
        if not text or not isinstance(text, str):
            return measurements
            
        # Pattern matches: [Chinese Name] [spaces/colon/comma] [number/decimal] [optional unit]
        # Example 1: 空腹血糖 6.5, 餐后血糖: 8.0 mmol/L
        # Example 2: 3天前 症状：发热，value：38.5 单位：度
        pattern = r'([\u4e00-\u9fa5A-Za-z]+(?:血糖|血压|心率|指标|血脂|胆固醇|蛋白|压|酸|酶|素|计数|比值|体积|浓度|饱和度|时间|宽度|百分比|发热|体温|症状))[\s:：,，]*(?:value[：:]|值[：:]|为[：:]?|：)?\s*([\d\.]+)\s*(?:单位[：:])?\s*([a-zA-Z/%/度℃]*)(?![0-9\.\-])'
        
        matches = re.finditer(pattern, text)
        
        # Second pattern specifically for the user's custom format: 症状：发热，value：38.5 单位：度
        pattern_custom = r'症状：([\u4e00-\u9fa5A-Za-z]+)[\s,，]*value[：:]\s*([\d\.]+)\s*(?:单位[：:])?\s*([a-zA-Z/%/度℃]*)'
        matches_custom = re.finditer(pattern_custom, text)
        
        all_matches = []
        for match in matches:
            all_matches.append({"type": "measurement", "match": match})
            
        for match in matches_custom:
            all_matches.append({"type": "symptom", "match": match})
            
        for item in all_matches:
            match = item["match"]
            name = match.group(1).strip()
            value = match.group(2).strip()
            unit = match.group(3).strip()
            
            # Avoid extracting pure dates like 2023.05
            if "." in value and len(value.split(".")[0]) == 4:
                continue
                
            measurements.append({
                "type": item["type"],
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
        empty_result = lambda t: {"conditions": [], "medications": [], "procedures": [], "measurements": [], "symptoms_with_values": [], "times": [], "observations": [t] if t else []}
        
        if not self.ner_pipeline or not texts:
            return [empty_result(t) for t in texts]

        # Filter out empty texts for the pipeline to avoid crashes, replace with a dummy string
        # Keep track of original texts to map them back
        # For our custom regex extraction we use the original text, but for the pipeline we might want to clean up things it struggles with.
        safe_texts = [t if isinstance(t, str) and t.strip() else "无" for t in texts]
        
        final_results = []
        try:
            # The pipeline supports batching list of strings
            batch_outputs = self.ner_pipeline(safe_texts, batch_size=batch_size)
            
            # If a single string was passed (due to len(texts)==1), pipeline returns List[dict] instead of List[List[dict]]
            if len(safe_texts) == 1 and (not isinstance(batch_outputs, list) or (len(batch_outputs) > 0 and isinstance(batch_outputs[0], dict))):
                batch_outputs = [batch_outputs]

            for idx, entities in enumerate(batch_outputs):
                original_text = texts[idx]
                result = {
                    "conditions": [],
                    "medications": [],
                    "procedures": [],
                    "measurements": [],
                    "symptoms_with_values": [],
                    "times": [],
                    "observations": []
                }
                
                # If it was an invalid text originally, just return the empty structure
                if not isinstance(original_text, str) or not original_text.strip():
                    final_results.append(empty_result(original_text))
                    continue

                # 1. First, extract regex measurements and symptoms
                regex_measurements = self._extract_measurements_regex(original_text)
                for rm in regex_measurements:
                    unit_str = f" {rm['unit']}" if rm['unit'] else ""
                    if rm['type'] == 'symptom':
                        result["symptoms_with_values"].append(f"症状：{rm['name']}    值：{rm['value']}{unit_str}")
                    else:
                        result["measurements"].append(f"检查：{rm['name']}    值：{rm['value']}{unit_str}")
                        
                # 2. Extract times
                times = self._extract_time_regex(original_text)
                for t in times:
                    result["times"].append(t)
                    
                # We want to remove the extracted measurement texts from NER processing mentally, 
                # but for simplicity we'll just ignore NER fragments that overlap with numbers
                
                for ent in entities:
                    entity_group = ent.get("entity_group", "")
                    word = ent.get("word", "").strip()
                    
                    if not word or re.match(r'^[\d\.\s]+$', word) or word in ["天", "前", "后", "月", "年", "小时"]:
                        # Skip pure numbers or time fragments handled by regex
                        continue
                        
                    if entity_group in ["DIS", "SYM", "DISEASE", "SYMPTOM"]:
                        result["conditions"].append(word)
                    elif entity_group in ["MED", "MEDICINE", "DRUG"]:
                        result["medications"].append(word)
                    elif entity_group in ["PRO", "PROCEDURE"]:
                        result["procedures"].append(word)
                    elif entity_group in ["BOD", "BODY", "LOC"]:
                        result["observations"].append(f"部位: {word}")
                    else:
                        result["observations"].append(word)
                        
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
            "observations": []
        }
        
        if not self.ner_pipeline or not text or not isinstance(text, str):
            if text:
                result["observations"].append(text)
            return result

        try:
            # 1. Regex measurements & symptoms
            regex_measurements = self._extract_measurements_regex(text)
            for rm in regex_measurements:
                unit_str = f" {rm['unit']}" if rm['unit'] else ""
                if rm['type'] == 'symptom':
                    result["symptoms_with_values"].append(f"症状：{rm['name']}    值：{rm['value']}{unit_str}")
                else:
                    result["measurements"].append(f"检查：{rm['name']}    值：{rm['value']}{unit_str}")
                    
            # 2. Extract times
            times = self._extract_time_regex(text)
            for t in times:
                result["times"].append(t)
                
            entities = self.ner_pipeline(text)
            
            # Map generic NER tags to OMOP domains
            for ent in entities:
                entity_group = ent.get("entity_group", "")
                word = ent.get("word", "").strip()
                
                if not word or re.match(r'^[\d\.\s]+$', word) or word in ["天", "前", "后", "月", "年", "小时"]:
                    continue
                    
                if entity_group in ["DIS", "SYM", "DISEASE", "SYMPTOM"]:
                    result["conditions"].append(word)
                elif entity_group in ["MED", "MEDICINE", "DRUG"]:
                    result["medications"].append(word)
                elif entity_group in ["PRO", "PROCEDURE"]:
                    result["procedures"].append(word)
                elif entity_group in ["BOD", "BODY", "LOC"]:
                    # Body parts might be observations
                    result["observations"].append(f"部位: {word}")
                else:
                    # Unclassified entities go to observations
                    result["observations"].append(word)
                    
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
