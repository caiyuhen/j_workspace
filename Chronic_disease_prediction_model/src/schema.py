class FeatureSchema:
    def __init__(self):
        self.date_col = "exam_date"
        self.id_col = "patient_id"
        self.target_cols = [
            "stroke", "diabetes", "arrhythmia", "hypertension", "kidney_disease",
            "depression", "anxiety", "alzheimer", "coronary_heart_disease", "gout",
            "parkinson", "heart_failure", "asthma", "bronchiectasis"
        ]
        
        # Mapping diseases to their Chinese names
        self.disease_names = {
            "stroke": "脑卒中",
            "diabetes": "糖尿病",
            "arrhythmia": "心律不齐",
            "hypertension": "高血压",
            "kidney_disease": "肾脏疾病",
            "depression": "抑郁症",
            "anxiety": "焦虑症",
            "alzheimer": "阿尔茨海默病",
            "coronary_heart_disease": "冠心病",
            "gout": "痛风",
            "parkinson": "帕金森病",
            "heart_failure": "慢性心力衰竭",
            "asthma": "支气管哮喘",
            "bronchiectasis": "支气管扩张"
        }
        
        # Adding dummy risk recommendations for the API to not crash
        self.risk_thresholds = {
            "stroke": (0.6, 0.8, 0.95),
            "diabetes": (0.8, 0.9, 0.98),
            "arrhythmia": (0.6, 0.8, 0.95),
            "hypertension": (0.8, 0.9, 0.98),
            "kidney_disease": (0.6, 0.8, 0.95),
            "depression": (0.6, 0.8, 0.95),
            "anxiety": (0.8, 0.9, 0.98),
            "alzheimer": (0.6, 0.8, 0.95),
            "coronary_heart_disease": (0.6, 0.8, 0.95),
            "gout": (0.6, 0.8, 0.95),
            "parkinson": (0.8, 0.9, 0.98),
            "heart_failure": (0.8, 0.9, 0.98),
            "asthma": (0.6, 0.8, 0.95),
            "bronchiectasis": (0.6, 0.8, 0.95),
        }
        
        self.risk_recommendations = {
            disease: {
                "低风险": ["保持当前健康生活方式。"],
                "中风险": ["建议定期体检，注意饮食。"],
                "高风险": ["建议尽快就医进行详细检查。"],
                "极高风险": ["请立即就医，遵循医生指导。"]
            }
            for disease in self.target_cols
        }
