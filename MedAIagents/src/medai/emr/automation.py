"""
电子病历自动化模块
Electronic Medical Record (EMR) Automation
"""

import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from ..config import Config


class MedicalNoteTemplate:
    """病历模板类"""
    
    def __init__(self, template_type: str, name: str, content: str):
        self.template_type = template_type
        self.name = name
        self.content = content
        self.created_at = datetime.now()
    
    def render(self, **kwargs) -> str:
        """渲染模板"""
        result = self.content
        for key, value in kwargs.items():
            placeholder = f'{{{{{key}}}}}'
            result = result.replace(placeholder, str(value) if value else '')
        return result


class EMRInformationExtractor:
    """EMR信息提取器"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        # 正则表达式模式
        self.patterns = {
            'patient_name': re.compile(r'(?:姓名|患者姓名)[：:]\s*([^\n，。；]+)'),
            'age': re.compile(r'(?:年龄)[：:]\s*(\d+)\s*岁'),
            'gender': re.compile(r'(?:性别)[：:]\s*(男|女)'),
            'diagnosis': re.compile(r'(?:诊断|入院诊断|出院诊断)[：:]\s*([^\n。；]+)'),
            'blood_pressure': re.compile(r'(?:血压|BP)[：:]\s*(\d+)\s*/\s*(\d+)\s*mmHg'),
            'heart_rate': re.compile(r'(?:心率|HR|P)[：:]\s*(\d+)\s*次/分'),
            'temperature': re.compile(r'(?:体温|T)[：:]\s*(\d+\.?\d*)\s*[℃°C]'),
            'blood_glucose': re.compile(r'(?:血糖|GLU)[：:]\s*(\d+\.?\d*)\s*mmol/L'),
            'icd10': re.compile(r'[A-Z]\d{2}(?:\.\d{1,2})?'),
        }
    
    def extract_patient_info(self, text: str) -> Dict[str, Any]:
        """提取患者基本信息"""
        info = {}
        
        for field, pattern in self.patterns.items():
            match = pattern.search(text)
            if match:
                if field == 'blood_pressure':
                    info['systolic_bp'] = int(match.group(1))
                    info['diastolic_bp'] = int(match.group(2))
                else:
                    info[field] = match.group(1).strip()
        
        return info
    
    def extract_symptoms(self, text: str) -> List[str]:
        """提取症状描述"""
        # 常见症状关键词
        symptom_keywords = [
            '发热', '头痛', '咳嗽', '咳痰', '胸痛', '腹痛', '腹泻', '恶心', '呕吐',
            '头晕', '乏力', '呼吸困难', '胸闷', '心悸', '水肿', '皮疹', '瘙痒',
            '关节痛', '腰痛', '尿频', '尿急', '尿痛', '视力模糊', '耳鸣', '眩晕'
        ]
        
        found_symptoms = []
        for symptom in symptom_keywords:
            if symptom in text:
                found_symptoms.append(symptom)
        
        return found_symptoms
    
    def extract_lab_results(self, text: str) -> Dict[str, str]:
        """提取实验室检查结果"""
        lab_results = {}
        
        # 常见检查项目模式
        lab_patterns = {
            'WBC': re.compile(r'白细胞.*?(\d+\.?\d*)\s*\*?\s*10\^?\d?\d?/L'),
            'RBC': re.compile(r'红细胞.*?(\d+\.?\d*)\s*\*?\s*10\^?\d?\d?/L'),
            'Hb': re.compile(r'血红蛋白.*?(\d+)\s*g/L'),
            'PLT': re.compile(r'血小板.*?(\d+)\s*\*?\s*10\^?\d?\d?/L'),
            'ALT': re.compile(r'谷丙转氨酶.*?(\d+)\s*U/L'),
            'AST': re.compile(r'谷草转氨酶.*?(\d+)\s*U/L'),
            'Cr': re.compile(r'肌酐.*?(\d+)\s*μmol/L'),
            'BUN': re.compile(r'尿素氮.*?(\d+\.?\d*)\s*mmol/L'),
        }
        
        for test_name, pattern in lab_patterns.items():
            match = pattern.search(text)
            if match:
                lab_results[test_name] = match.group(1)
        
        return lab_results
    
    def extract_medications(self, text: str) -> List[Dict[str, str]]:
        """提取用药信息"""
        # 简化的药物提取
        medications = []
        
        # 常见药物名称
        common_drugs = [
            '阿司匹林', '二甲双胍', '阿托伐他汀', '氨氯地平', '美托洛尔',
            '奥美拉唑', '头孢', '青霉素', '左氧氟沙星', '华法林',
            '胰岛素', '泼尼松', '呋塞米', '螺内酯', '氯吡格雷'
        ]
        
        for drug in common_drugs:
            if drug in text:
                # 尝试提取剂量
                dose_match = re.search(rf'{drug}\s*(\d+\.?\d*\s*mg?)', text)
                dose = dose_match.group(1) if dose_match else '未知'
                
                # 尝试提取用法
                freq_match = re.search(rf'{drug}.*?(qd|bid|tid|qn|po|iv)', text, re.IGNORECASE)
                frequency = freq_match.group(1) if freq_match else '未知'
                
                medications.append({
                    'name': drug,
                    'dose': dose,
                    'frequency': frequency
                })
        
        return medications
    
    def comprehensive_extract(self, text: str) -> Dict[str, Any]:
        """综合提取所有信息"""
        return {
            'patient_info': self.extract_patient_info(text),
            'symptoms': self.extract_symptoms(text),
            'lab_results': self.extract_lab_results(text),
            'medications': self.extract_medications(text),
            'extraction_time': datetime.now().isoformat()
        }


class EMRNoteGenerator:
    """EMR病历生成器"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.templates = self._load_templates()
        self.extractor = EMRInformationExtractor(config)
    
    def _load_templates(self) -> Dict[str, MedicalNoteTemplate]:
        """加载预定义的病历模板"""
        templates = {}
        
        # 入院记录模板
        admission_note = """
【入院记录】

姓名：{{patient_name}}    性别：{{gender}}    年龄：{{age}}岁  
民族：{{ethnicity}}    婚否：{{marital_status}}    职业：{{occupation}}  
籍贯/现住址：{{address}}  
入院日期：{{admission_date}}    记录日期：{{record_date}}  
病史陈述者：{{historian}}    可靠程度：{{reliability}}

---

【主诉】
{{chief_complaint}}

【现病史】
{{history_of_present_illness}}

【既往史】
{{past_medical_history}}

【个人史及家族史】
个人史：{{personal_history}}
家族史：{{family_history}}

【体格检查】
一般情况：体温 {{temperature}}℃  脉搏 {{pulse}}次/分  呼吸 {{respiration}}次/分  血压 {{blood_pressure}}mmHg
皮肤黏膜：{{skin_mucosa}}
淋巴结：{{lymph_nodes}}
头部及其器官：{{head_organs}}
颈部：{{neck}}
胸部：
    肺脏：{{lungs}}
    心脏：{{heart}}
腹部：{{abdomen}}
肛门直肠及外生殖器：{{genitalia}}
脊柱四肢：{{spine_extremities}}
神经系统：{{neurological}}

【辅助检查】
{{auxiliary_examinations}}

【初步诊断】
{{diagnosis}}

【诊断依据】
{{diagnostic_basis}}

【鉴别诊断】
{{differential_diagnosis}}

【诊疗计划】
{{treatment_plan}}

医师签名：{{doctor_name}}
        """
        
        templates['admission_note'] = MedicalNoteTemplate(
            'admission', '入院记录模板', admission_note
        )
        
        # 病程记录模板
        progress_note = """
【病程记录】

日期：{{date}}    时间：{{time}}

{{subjective}}

【体格检查】
生命体征：体温 {{temperature}}℃  脉搏 {{pulse}}次/分  呼吸 {{respiration}}次/分  血压 {{blood_pressure}}mmHg
一般情况：{{general_condition}}

【辅助检查结果】
{{lab_results}}

【病情分析】
{{analysis}}

【诊疗措施】
{{actions}}

【下一步计划】
{{next_steps}}

医师签名：{{doctor_name}}
        """
        
        templates['progress_note'] = MedicalNoteTemplate(
            'progress', '病程记录模板', progress_note
        )
        
        # 出院记录模板
        discharge_note = """
【出院记录】

姓名：{{patient_name}}    性别：{{gender}}    年龄：{{age}}岁  
住院号：{{hospital_number}}
入院日期：{{admission_date}}    出院日期：{{discharge_date}}
住院天数：{{length_of_stay}}天

---

【入院情况】
{{admission_condition}}

【入院诊断】
{{admission_diagnosis}}

【诊疗经过】
{{hospital_course}}

【出院诊断】
{{discharge_diagnosis}}

【出院情况】
{{discharge_condition}}

【出院医嘱】
{{discharge_orders}}

【随访建议】
{{follow_up}}

医师签名：{{doctor_name}}
        """
        
        templates['discharge_note'] = MedicalNoteTemplate(
            'discharge', '出院记录模板', discharge_note
        )
        
        # 手术记录模板
        surgery_note = """
【手术记录】

手术日期：{{surgery_date}}
术前诊断：{{preop_diagnosis}}
术后诊断：{{postop_diagnosis}}
手术名称：{{procedure_name}}
手术者：{{surgeon}}    助手：{{assistant}}
麻醉方式：{{anesthesia_type}}
麻醉医师：{{anesthesiologist}}

---

【手术经过】
{{procedure_description}}

【术中出血】
{{blood_loss}}

【术中用药】
{{medications_given}}

【标本处理】
{{specimens}}

【特殊情况】
{{complications}}

【术后处理】
{{postop_management}}

手术者签名：{{surgeon_signature}}
        """
        
        templates['surgery_note'] = MedicalNoteTemplate(
            'surgery', '手术记录模板', surgery_note
        )
        
        return templates
    
    def generate_admission_note(
        self,
        patient_name: str,
        gender: str,
        age: int,
        chief_complaint: str,
        diagnosis: str,
        **kwargs
    ) -> str:
        """生成入院记录"""
        template = self.templates['admission_note']
        
        # 填充默认值
        defaults = {
            'patient_name': patient_name,
            'gender': gender,
            'age': age,
            'ethnicity': '汉族',
            'marital_status': '已婚',
            'occupation': '无',
            'address': '不详',
            'admission_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'record_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'historian': '患者本人',
            'reliability': '可靠',
            'chief_complaint': chief_complaint,
            'history_of_present_illness': '详见现病史',
            'past_medical_history': '否认高血压、糖尿病、冠心病等慢性病史。否认肝炎、结核等传染病史。否认手术、外伤史。否认食物、药物过敏史。',
            'personal_history': '生于原籍，久居本地，无疫区旅居史。无烟、酒嗜好。',
            'family_history': '否认家族性遗传病史。',
            'temperature': '36.5',
            'pulse': '72',
            'respiration': '18',
            'blood_pressure': '120/80',
            'skin_mucosa': '全身皮肤黏膜无黄染、皮疹、出血点。',
            'lymph_nodes': '全身浅表淋巴结未触及肿大。',
            'head_organs': '头颅无畸形，眼睑无水肿，结膜无充血，巩膜无黄染，瞳孔等大等圆，对光反射灵敏。耳鼻咽喉未见异常。',
            'neck': '颈软，无抵抗，颈静脉无怒张，气管居中，甲状腺未触及肿大。',
            'lungs': '双肺呼吸音清，未闻及干湿性啰音。',
            'heart': '心前区无隆起，心尖搏动位于第五肋间左锁骨中线内0.5cm，搏动有力，未触及震颤。心界不大。心率72次/分，律齐，各瓣膜听诊区未闻及病理性杂音。',
            'abdomen': '腹平坦，未见胃肠型及蠕动波，未见腹壁静脉曲张。腹软，全腹无压痛、反跳痛，未触及包块，肝脾肋下未触及。移动性浊音阴性。肠鸣音正常。',
            'genitalia': '未查。',
            'spine_extremities': '脊柱生理弯曲存在，无畸形，活动自如。四肢无畸形，关节无红肿，活动自如。双下肢无水肿。',
            'neurological': '生理反射存在，病理反射未引出。',
            'auxiliary_examinations': '暂缺。',
            'diagnosis': diagnosis,
            'diagnostic_basis': '根据病史、体格检查及辅助检查结果。',
            'differential_diagnosis': '根据目前资料，暂不考虑其他诊断。',
            'treatment_plan': '1. 完善相关检查；2. 对症支持治疗；3. 请相关科室会诊。',
            'doctor_name': '医师'
        }
        
        # 合并用户提供的参数
        params = {**defaults, **kwargs}
        
        return template.render(**params).strip()
    
    def generate_progress_note(
        self,
        subjective: str,
        temperature: float = 36.5,
        pulse: int = 72,
        respiration: int = 18,
        blood_pressure: str = '120/80',
        **kwargs
    ) -> str:
        """生成病程记录"""
        template = self.templates['progress_note']
        
        defaults = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M'),
            'subjective': subjective,
            'temperature': str(temperature),
            'pulse': str(pulse),
            'respiration': str(respiration),
            'blood_pressure': blood_pressure,
            'general_condition': '患者一般情况可，精神食欲睡眠可。',
            'lab_results': '暂无新的检查结果。',
            'analysis': '患者目前病情稳定。',
            'actions': '继续当前治疗方案。',
            'next_steps': '观察病情变化。',
            'doctor_name': '医师'
        }
        
        params = {**defaults, **kwargs}
        return template.render(**params).strip()
    
    def generate_discharge_note(
        self,
        patient_name: str,
        gender: str,
        age: int,
        admission_diagnosis: str,
        discharge_diagnosis: str,
        discharge_orders: str,
        **kwargs
    ) -> str:
        """生成出院记录"""
        template = self.templates['discharge_note']
        
        defaults = {
            'patient_name': patient_name,
            'gender': gender,
            'age': age,
            'hospital_number': 'XXXXXX',
            'admission_date': kwargs.get('admission_date', datetime.now().strftime('%Y-%m-%d')),
            'discharge_date': datetime.now().strftime('%Y-%m-%d'),
            'length_of_stay': '7',
            'admission_condition': '患者因"{}"入院。'.format(admission_diagnosis),
            'admission_diagnosis': admission_diagnosis,
            'hospital_course': '入院后完善相关检查，给予对症支持治疗，患者病情好转。',
            'discharge_diagnosis': discharge_diagnosis,
            'discharge_condition': '患者一般情况可，生命体征平稳，症状缓解。',
            'discharge_orders': discharge_orders,
            'follow_up': '出院后1周门诊复查，不适随诊。',
            'doctor_name': '医师'
        }
        
        params = {**defaults, **kwargs}
        return template.render(**params).strip()
    
    def generate_from_text(self, text: str, template_type: str = 'progress_note') -> str:
        """从自由文本生成结构化病历"""
        # 先从文本中提取信息
        extracted = self.extractor.comprehensive_extract(text)
        
        # 根据提取的信息生成病历
        patient_info = extracted['patient_info']
        symptoms = extracted['symptoms']
        lab_results = extracted['lab_results']
        
        # 构建主诉
        chief_complaint = '、'.join(symptoms[:3]) if symptoms else '未描述'
        
        if template_type == 'admission_note':
            return self.generate_admission_note(
                patient_name=patient_info.get('patient_name', '不详'),
                gender=patient_info.get('gender', '男'),
                age=int(patient_info.get('age', 0)),
                chief_complaint=chief_complaint,
                diagnosis=patient_info.get('diagnosis', '待查'),
                temperature=patient_info.get('temperature', '36.5'),
                blood_pressure=patient_info.get('systolic_bp', '120') + '/' + patient_info.get('diastolic_bp', '80'),
                auxiliary_examinations=json.dumps(lab_results, ensure_ascii=False, indent=2)
            )
        elif template_type == 'progress_note':
            lab_text = '\n'.join([f'{k}: {v}' for k, v in lab_results.items()]) if lab_results else '无'
            return self.generate_progress_note(
                subjective='患者诉' + '、'.join(symptoms) if symptoms else '无特殊不适',
                lab_results=lab_text
            )
        else:
            return "不支持的模板类型"
    
    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return list(self.templates.keys())


class ICD10Coder:
    """ICD-10编码助手"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        # 简化的ICD-10编码映射
        self.icd10_map = {
            '2型糖尿病': 'E11.9',
            '2型糖尿病伴酮症': 'E11.1',
            '2型糖尿病伴肾病': 'E11.2',
            '2型糖尿病伴神经病变': 'E11.4',
            '原发性高血压': 'I10',
            '高血压性心脏病': 'I11.9',
            '高血压性肾脏病': 'I12.9',
            '冠心病': 'I25.9',
            '心绞痛': 'I20.9',
            '急性心肌梗死': 'I21.9',
            '陈旧性心肌梗死': 'I25.2',
            '脑梗死': 'I63.9',
            '脑出血': 'I61.9',
            '社区获得性肺炎': 'J18.9',
            '慢性阻塞性肺疾病': 'J44.9',
            '支气管哮喘': 'J45.9',
            '胃溃疡': 'K25.9',
            '十二指肠溃疡': 'K26.9',
            '急性阑尾炎': 'K35.9',
            '急性上呼吸道感染': 'J06.9',
            '流行性感冒': 'J11.1',
            '慢性胃炎': 'K29.5',
            '胆囊结石': 'K80.2',
            '尿路感染': 'N39.0',
            '血脂异常': 'E78.5',
            '甲状腺功能亢进': 'E05.9',
            '甲状腺功能减退': 'E03.9'
        }
    
    def get_icd10_code(self, diagnosis: str) -> Optional[str]:
        """获取ICD-10编码"""
        # 精确匹配
        if diagnosis in self.icd10_map:
            return self.icd10_map[diagnosis]
        
        # 模糊匹配
        for key, code in self.icd10_map.items():
            if key in diagnosis or diagnosis in key:
                return code
        
        return None
    
    def search_icd10(self, keyword: str) -> List[Dict[str, str]]:
        """搜索ICD-10编码"""
        results = []
        keyword_lower = keyword.lower()
        
        for diagnosis, code in self.icd10_map.items():
            if keyword_lower in diagnosis.lower() or keyword_lower in code.lower():
                results.append({
                    'diagnosis': diagnosis,
                    'icd10_code': code
                })
        
        return results
    
    def validate_icd10(self, code: str) -> bool:
        """验证ICD-10编码格式是否正确"""
        # 简单的格式验证：字母 + 2位数字 + 可选的小数点和1-2位数字
        pattern = re.compile(r'^[A-Z]\d{2}(\.\d{1,2})?$')
        return bool(pattern.match(code))
