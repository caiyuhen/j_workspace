"""
临床决策支持模块
Clinical Decision Support System (CDSS)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from ..config import Config
from ..knowledge import MedicalKnowledgeBase


class DiagnosticReasoner:
    """诊断推理引擎"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.kb = MedicalKnowledgeBase(self.config)
        
        # 症状-疾病关联知识库（简化版）
        self.symptom_disease_map = self._build_symptom_disease_map()
    
    def _build_symptom_disease_map(self) -> Dict[str, List[Dict[str, Any]]]:
        """构建症状-疾病关联映射"""
        # 简化版的诊断知识库
        disease_db = [
            {
                'disease': '2型糖尿病',
                'icd10': 'E11',
                'category': '内分泌',
                'symptoms': ['多饮', '多食', '多尿', '体重下降', '乏力', '口干'],
                'key_findings': ['空腹血糖≥7.0 mmol/L', 'HbA1c≥6.5%'],
                'confidence': 0.85
            },
            {
                'disease': '1型糖尿病',
                'icd10': 'E10',
                'category': '内分泌',
                'symptoms': ['多饮', '多食', '多尿', '体重明显下降', '酮症', '青少年起病'],
                'key_findings': ['胰岛素绝对缺乏', 'GAD抗体阳性'],
                'confidence': 0.80
            },
            {
                'disease': '原发性高血压',
                'icd10': 'I10',
                'category': '心血管',
                'symptoms': ['头痛', '头晕', '血压升高', '头胀', '耳鸣'],
                'key_findings': ['收缩压≥140 mmHg', '舒张压≥90 mmHg'],
                'confidence': 0.85
            },
            {
                'disease': '冠心病',
                'icd10': 'I25',
                'category': '心血管',
                'symptoms': ['胸痛', '胸闷', '压榨感', '放射痛', '劳力后加重', '休息缓解'],
                'key_findings': ['ST段改变', '肌钙蛋白升高', '冠脉狭窄'],
                'confidence': 0.80
            },
            {
                'disease': '急性心肌梗死',
                'icd10': 'I21',
                'category': '心血管',
                'symptoms': ['剧烈胸痛', '压榨感', '大汗', '濒死感', '放射至左肩'],
                'key_findings': ['肌钙蛋白显著升高', 'ST段弓背向上抬高', '病理性Q波'],
                'confidence': 0.90
            },
            {
                'disease': '社区获得性肺炎',
                'icd10': 'J18',
                'category': '呼吸科',
                'symptoms': ['发热', '咳嗽', '咳痰', '胸痛', '呼吸困难', '寒战'],
                'key_findings': ['肺部啰音', '胸片浸润影', 'WBC升高'],
                'confidence': 0.80
            },
            {
                'disease': '慢性阻塞性肺疾病',
                'icd10': 'J44',
                'category': '呼吸科',
                'symptoms': ['慢性咳嗽', '咳痰', '气短', '呼吸困难', '喘息', '吸烟史'],
                'key_findings': ['FEV1/FVC<70%', '肺气肿征象'],
                'confidence': 0.85
            },
            {
                'disease': '脑梗死',
                'icd10': 'I63',
                'category': '神经科',
                'symptoms': ['偏瘫', '失语', '偏身感觉障碍', '意识障碍', '吞咽困难'],
                'key_findings': ['CT低密度灶', 'DWI高信号', '局灶性神经功能缺损'],
                'confidence': 0.85
            },
            {
                'disease': '脑出血',
                'icd10': 'I61',
                'category': '神经科',
                'symptoms': ['突发头痛', '呕吐', '意识障碍', '偏瘫', '血压显著升高'],
                'key_findings': ['CT高密度影', '颅内压升高'],
                'confidence': 0.85
            },
            {
                'disease': '胃溃疡',
                'icd10': 'K25',
                'category': '消化科',
                'symptoms': ['餐后腹痛', '上腹痛', '反酸', '嗳气', '黑便'],
                'key_findings': ['胃镜溃疡', 'HP阳性'],
                'confidence': 0.75
            },
            {
                'disease': '十二指肠溃疡',
                'icd10': 'K26',
                'category': '消化科',
                'symptoms': ['空腹痛', '夜间痛', '进食缓解', '反酸', '黑便'],
                'key_findings': ['胃镜溃疡', 'HP阳性'],
                'confidence': 0.75
            },
            {
                'disease': '急性阑尾炎',
                'icd10': 'K35',
                'category': '外科',
                'symptoms': ['转移性右下腹痛', '麦氏点压痛', '反跳痛', '发热', '恶心呕吐'],
                'key_findings': ['WBC升高', '右下腹超声异常'],
                'confidence': 0.85
            }
        ]
        
        # 构建症状到疾病的映射
        symptom_map = {}
        for disease in disease_db:
            for symptom in disease['symptoms']:
                if symptom not in symptom_map:
                    symptom_map[symptom] = []
                symptom_map[symptom].append(disease)
        
        return symptom_map
    
    def reason(self, symptoms: List[str], lab_results: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """基于症状和实验室结果进行诊断推理
        
        Args:
            symptoms: 症状列表
            lab_results: 实验室检查结果字典
        
        Returns:
            可能的诊断列表，按置信度排序
        """
        lab_results = lab_results or {}
        
        # 匹配症状
        matched_diseases = {}
        
        for symptom in symptoms:
            # 精确匹配
            if symptom in self.symptom_disease_map:
                for disease in self.symptom_disease_map[symptom]:
                    disease_name = disease['disease']
                    if disease_name not in matched_diseases:
                        matched_diseases[disease_name] = {
                            **disease,
                            'matched_symptoms': set(),
                            'matched_findings': set(),
                            'score': 0
                        }
                    matched_diseases[disease_name]['matched_symptoms'].add(symptom)
        
        # 匹配关键发现
        for disease_name, disease_info in matched_diseases.items():
            for finding in disease_info['key_findings']:
                # 检查实验室结果中是否有关键词
                for lab_key, lab_value in lab_results.items():
                    if finding.lower() in f"{lab_key} {lab_value}".lower():
                        disease_info['matched_findings'].add(finding)
        
        # 计算得分
        results = []
        for disease_name, disease_info in matched_diseases.items():
            total_symptoms = len(disease_info['symptoms'])
            matched_symptom_count = len(disease_info['matched_symptoms'])
            matched_finding_count = len(disease_info['matched_findings'])
            
            # 基础得分 = 症状匹配率 * 基础置信度
            symptom_score = (matched_symptom_count / max(total_symptoms, 1)) * disease_info['confidence']
            
            # 关键发现加分
            finding_score = matched_finding_count * 0.1
            
            # 最终得分
            final_score = min(symptom_score + finding_score, 1.0)
            
            results.append({
                'disease': disease_name,
                'icd10': disease_info['icd10'],
                'category': disease_info['category'],
                'confidence': round(final_score, 2),
                'matched_symptoms': list(disease_info['matched_symptoms']),
                'matched_findings': list(disease_info['matched_findings']),
                'all_symptoms': disease_info['symptoms'],
                'key_findings': disease_info['key_findings']
            })
        
        # 按置信度排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return results
    
    def generate_differential_diagnosis(
        self,
        symptoms: List[str],
        lab_results: Dict[str, str] = None,
        max_diagnoses: int = 5
    ) -> Dict[str, Any]:
        """生成鉴别诊断
        
        Args:
            symptoms: 症状列表
            lab_results: 实验室检查结果
            max_diagnoses: 最大诊断数量
        
        Returns:
            鉴别诊断结果
        """
        diagnoses = self.reason(symptoms, lab_results)
        
        # 限制诊断数量
        top_diagnoses = diagnoses[:max_diagnoses]
        
        # 生成建议的进一步检查
        recommended_tests = self._generate_recommended_tests(top_diagnoses)
        
        return {
            'primary_diagnosis': top_diagnoses[0] if top_diagnoses else None,
            'differential_diagnoses': top_diagnoses,
            'recommended_tests': recommended_tests,
            'input_symptoms': symptoms,
            'input_lab_results': lab_results
        }
    
    def _generate_recommended_tests(self, diagnoses: List[Dict[str, Any]]) -> List[str]:
        """根据诊断建议进一步检查"""
        # 根据可能的诊断建议检查
        recommended = set()
        
        for diag in diagnoses:
            category = diag.get('category', '')
            
            if category == '内分泌':
                recommended.update(['空腹血糖', '餐后2小时血糖', '糖化血红蛋白(HbA1c)', '胰岛素释放试验'])
            elif category == '心血管':
                recommended.update(['心电图', '心肌酶谱', '肌钙蛋白', '心脏超声', '冠脉CTA'])
            elif category == '呼吸科':
                recommended.update(['胸片', '胸部CT', '肺功能', '动脉血气分析', '痰培养'])
            elif category == '神经科':
                recommended.update(['头颅CT', '头颅MRI', '脑血管造影', '脑脊液检查'])
            elif category == '消化科':
                recommended.update(['胃镜', '幽门螺杆菌检测', '大便潜血', '肝功能'])
            elif category == '外科':
                recommended.update(['血常规', 'C反应蛋白', '腹部超声', '腹部CT'])
        
        return list(recommended)


class MedicationSafetyChecker:
    """用药安全检查器"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        # 药物相互作用数据库（简化版）
        self.drug_interactions = self._build_drug_interaction_db()
        
        # 常见药物剂量范围
        self.drug_dosages = self._build_drug_dosage_db()
    
    def _build_drug_interaction_db(self) -> Dict[str, List[Dict[str, Any]]]:
        """构建药物相互作用数据库"""
        return {
            '华法林': [
                {
                    'drug': '阿司匹林',
                    'severity': 'high',
                    'description': '增加出血风险',
                    'recommendation': '密切监测INR，考虑调整华法林剂量'
                },
                {
                    'drug': '布洛芬',
                    'severity': 'high',
                    'description': 'NSAIDs影响血小板功能并可能导致胃肠道出血',
                    'recommendation': '避免联用或使用胃肠道保护剂'
                }
            ],
            '辛伐他汀': [
                {
                    'drug': '红霉素',
                    'severity': 'high',
                    'description': '增加横纹肌溶解风险',
                    'recommendation': '避免联用'
                },
                {
                    'drug': '克拉霉素',
                    'severity': 'high',
                    'description': '增加横纹肌溶解风险',
                    'recommendation': '避免联用'
                }
            ],
            '二甲双胍': [
                {
                    'drug': '碘造影剂',
                    'severity': 'medium',
                    'description': '可能增加乳酸酸中毒风险',
                    'recommendation': '使用造影剂前后48小时停用二甲双胍'
                }
            ],
            '西地那非': [
                {
                    'drug': '硝酸甘油',
                    'severity': 'high',
                    'description': '严重低血压风险',
                    'recommendation': '绝对禁忌，严禁联用'
                }
            ]
        }
    
    def _build_drug_dosage_db(self) -> Dict[str, Dict[str, Any]]:
        """构建药物剂量数据库"""
        return {
            '阿司匹林': {
                'usual_dose': '100 mg qd',
                'max_daily': 300,
                'unit': 'mg',
                'indication': {
                    '心梗二级预防': '75-100 mg qd',
                    '急性心梗': '首剂300 mg嚼服，随后75-100 mg qd'
                }
            },
            '二甲双胍': {
                'usual_dose': '500 mg tid',
                'max_daily': 2000,
                'unit': 'mg',
                'indication': {
                    '2型糖尿病': '起始500 mg bid/tid，根据血糖调整'
                }
            },
            '阿托伐他汀': {
                'usual_dose': '20 mg qn',
                'max_daily': 80,
                'unit': 'mg',
                'indication': {
                    '高血脂': '10-20 mg qn',
                    '冠心病': '20-80 mg qn'
                }
            },
            '氨氯地平': {
                'usual_dose': '5 mg qd',
                'max_daily': 10,
                'unit': 'mg',
                'indication': {
                    '高血压': '5-10 mg qd',
                    '心绞痛': '5-10 mg qd'
                }
            }
        }
    
    def check_drug_interactions(self, medications: List[str]) -> List[Dict[str, Any]]:
        """检查药物相互作用
        
        Args:
            medications: 药物列表
        
        Returns:
            相互作用警告列表
        """
        warnings = []
        
        for i, med1 in enumerate(medications):
            if med1 in self.drug_interactions:
                for interaction in self.drug_interactions[med1]:
                    if interaction['drug'] in medications:
                        warnings.append({
                            'type': 'drug_interaction',
                            'severity': interaction['severity'],
                            'drug1': med1,
                            'drug2': interaction['drug'],
                            'description': interaction['description'],
                            'recommendation': interaction['recommendation']
                        })
        
        return warnings
    
    def check_dosage(self, medication: str, dose: float, unit: str = 'mg') -> Dict[str, Any]:
        """检查药物剂量是否合适
        
        Args:
            medication: 药物名称
            dose: 日剂量
            unit: 剂量单位
        
        Returns:
            剂量检查结果
        """
        if medication not in self.drug_dosages:
            return {
                'safe': None,
                'message': f'暂无{medication}的剂量数据，建议查阅药品说明书'
            }
        
        drug_info = self.drug_dosages[medication]
        
        if dose > drug_info['max_daily']:
            return {
                'safe': False,
                'severity': 'high',
                'message': f'{medication}日剂量{dose}{unit}超过最大推荐剂量{drug_info["max_daily"]}{unit}',
                'recommendation': '建议降低剂量或确认适应症'
            }
        elif dose > drug_info['max_daily'] * 0.8:
            return {
                'safe': True,
                'severity': 'low',
                'message': f'{medication}日剂量{dose}{unit}接近最大剂量',
                'recommendation': '建议密切监测药物不良反应'
            }
        else:
            return {
                'safe': True,
                'severity': 'none',
                'message': f'{medication}日剂量{dose}{unit}在推荐范围内',
                'usual_dose': drug_info['usual_dose']
            }
    
    def check_allergies(self, medications: List[str], allergies: List[str]) -> List[Dict[str, Any]]:
        """检查过敏史
        
        Args:
            medications: 药物列表
            allergies: 过敏药物列表
        
        Returns:
            过敏警告列表
        """
        warnings = []
        
        for med in medications:
            for allergy in allergies:
                # 简单的字符串匹配（实际应用应该更复杂）
                if allergy.lower() in med.lower() or med.lower() in allergy.lower():
                    warnings.append({
                        'type': 'allergy',
                        'severity': 'high',
                        'medication': med,
                        'allergy': allergy,
                        'description': f'患者对{allergy}过敏，处方包含{med}',
                        'recommendation': '建议更换其他药物'
                    })
        
        return warnings
    
    def comprehensive_check(
        self,
        medications: List[str],
        allergies: List[str] = None,
        doses: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """全面的用药安全检查
        
        Args:
            medications: 药物列表
            allergies: 过敏药物列表
            doses: 各药物的日剂量
        
        Returns:
            检查结果
        """
        allergies = allergies or []
        doses = doses or {}
        
        # 检查相互作用
        interaction_warnings = self.check_drug_interactions(medications)
        
        # 检查过敏
        allergy_warnings = self.check_allergies(medications, allergies)
        
        # 检查剂量
        dosage_warnings = []
        for med in medications:
            if med in doses:
                result = self.check_dosage(med, doses[med])
                if not result.get('safe', True) or result.get('severity') != 'none':
                    dosage_warnings.append({
                        'medication': med,
                        **result
                    })
        
        all_warnings = interaction_warnings + allergy_warnings + dosage_warnings
        
        # 按严重程度排序
        severity_order = {'high': 0, 'medium': 1, 'low': 2, 'none': 3}
        all_warnings.sort(key=lambda x: severity_order.get(x.get('severity', 'none'), 3))
        
        return {
            'total_warnings': len(all_warnings),
            'warnings': all_warnings,
            'medications_checked': medications,
            'is_safe': not any(w.get('severity') == 'high' for w in all_warnings),
            'recommendations': [w.get('recommendation', '') for w in all_warnings if w.get('recommendation')]
        }


class ClinicalDecisionSupport:
    """临床决策支持主类"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.diagnostic_reasoner = DiagnosticReasoner(config)
        self.medication_checker = MedicationSafetyChecker(config)
        self.kb = MedicalKnowledgeBase(config)
    
    def diagnose(
        self,
        symptoms: List[str],
        lab_results: Dict[str, str] = None,
        max_diagnoses: int = 5
    ) -> Dict[str, Any]:
        """诊断支持
        
        Args:
            symptoms: 症状列表
            lab_results: 实验室检查结果
            max_diagnoses: 最大诊断数量
        
        Returns:
            诊断结果
        """
        result = self.diagnostic_reasoner.generate_differential_diagnosis(
            symptoms, lab_results, max_diagnoses
        )
        
        # 添加指南参考
        if result['primary_diagnosis']:
            guideline_info = self.kb.search(result['primary_diagnosis']['disease'], limit=2)
            result['guideline_references'] = guideline_info
        
        return result
    
    def check_medication_safety(
        self,
        medications: List[str],
        allergies: List[str] = None,
        doses: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """用药安全检查
        
        Args:
            medications: 药物列表
            allergies: 过敏药物列表
            doses: 各药物的日剂量
        
        Returns:
            检查结果
        """
        return self.medication_checker.comprehensive_check(medications, allergies, doses)
    
    def check_guideline_compliance(
        self,
        diagnosis: str,
        treatment: str
    ) -> Dict[str, Any]:
        """检查治疗方案是否符合指南
        
        Args:
            diagnosis: 诊断
            treatment: 治疗方案
        
        Returns:
            合规性检查结果
        """
        # 搜索相关指南
        guidelines = self.kb.search(f"{diagnosis} 治疗指南", limit=3)
        
        # 简单的关键词匹配（实际应该使用更复杂的NLP）
        treatment_keywords = treatment.lower().split()
        
        compliance_issues = []
        compliant_points = []
        
        for guideline in guidelines:
            guideline_text = guideline['content'].lower()
            
            # 检查治疗方案中的关键词是否在指南中
            for keyword in treatment_keywords:
                if len(keyword) > 2 and keyword in guideline_text:
                    compliant_points.append(f"方案中'{keyword}'符合指南建议")
        
        return {
            'diagnosis': diagnosis,
            'treatment': treatment,
            'guidelines': guidelines,
            'compliant_points': compliant_points,
            'issues': compliance_issues,
            'overall_compliance': '部分符合' if compliant_points else '未找到明确依据'
        }
