import difflib
from typing import List, Dict

class NLPMapper:
    """
    NLP Semantic Mapper
    Automatically maps uploaded CSV headers to standard OMOP domain fields
    using semantic synonyms and fuzzy string matching.
    """
    
    # NLP Semantic Synonym Dictionary
    TARGET_SCHEMA = {
        "person_source_value": ["id", "patient", "patient_id", "患者编号", "病人编号", "就诊号", "门诊号", "id_card", "身份证", "患者id", "编号", "人员编号"],
        "gender_source_value": ["gender", "sex", "性别", "患者性别", "男女", "病人性别"],
        "birth_datetime": ["age", "birth", "dob", "birth_date", "birth_datetime", "出生日期", "年龄", "患者年龄", "出生", "岁数"],
        "observation_source_value": ["department", "diagnosis", "科室", "诊断", "就诊科室", "主诉", "icd", "icd_diagnosis", "疾病", "症状", "chief_complaint"],
        "visit_source_value": ["visit", "admission", "visit_id", "就诊记录", "入院记录", "门诊号", "住院号", "admission_record"],
        "visit_start_datetime": ["visit_date", "admission_date", "就诊时间", "入院时间", "挂号时间"],
        "visit_end_datetime": ["discharge_date", "出院时间"]
    }

    @classmethod
    def generate_mapping(cls, csv_headers: List[str]) -> Dict[str, str]:
        """
        Generates a mapping configuration dynamically based on semantic similarity.
        """
        mapping = {}
        used_headers = set()

        for target_field, synonyms in cls.TARGET_SCHEMA.items():
            best_match = None
            highest_score = 0.0

            for header in csv_headers:
                if header in used_headers:
                    continue
                
                # 1. Exact Match (Case Insensitive)
                if header.lower() == target_field.lower() or header.lower() in [s.lower() for s in synonyms]:
                    best_match = header
                    highest_score = 1.0
                    break
                
                # 2. NLP Fuzzy Semantic Match (Levenshtein Distance)
                for synonym in synonyms:
                    # Calculate semantic similarity ratio
                    score = difflib.SequenceMatcher(None, header.lower(), synonym.lower()).ratio()
                    # Threshold: at least 60% similarity
                    if score > highest_score and score > 0.6: 
                        highest_score = score
                        best_match = header

            if best_match:
                mapping[target_field] = best_match
                used_headers.add(best_match)

        return mapping
