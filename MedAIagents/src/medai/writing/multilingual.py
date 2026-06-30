"""
多语言支持模块 (v0.4.0)
Multilingual Support Module

功能:
- 中英双语界面文本管理
- 论文中英互译辅助框架
- 医学术语标准化对照 (ICD-10, MeSH, SNOMED-CT)
- 中文核心期刊数据库扩展
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import os


class Language(Enum):
    """支持的语言"""
    ZH_CN = "zh_CN"
    EN_US = "en_US"


@dataclass
class MedicalTerm:
    """医学术语条目"""
    english: str
    chinese: str
    abbreviation: str = ""
    category: str = ""  # 解剖/疾病/药物/检查等
    icd10_code: str = ""  # ICD-10编码
    mesh_term: str = ""  # MeSH主题词
    snomed_id: str = ""  # SNOMED-CT ID
    definition: str = ""  # 定义
    synonyms: List[str] = None

    def __post_init__(self):
        if self.synonyms is None:
            self.synonyms = []


class I18nManager:
    """国际化文本管理器"""

    def __init__(self):
        self._translations = self._load_translations()
        self._current_lang = Language.ZH_CN

    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """加载界面翻译文本"""
        return {
            "zh_CN": {
                "app_title": "MedAIagents 医学AI代理框架",
                "menu_diagnosis": "诊断辅助",
                "menu_medication": "用药安全",
                "menu_emr": "病历文书",
                "menu_icd10": "ICD-10编码",
                "menu_knowledge": "知识库检索",
                "menu_research": "临床科研",
                "menu_writing": "医学写作",
                "menu_paper_eval": "论文评分",
                "menu_journal_rec": "期刊推荐",
                "menu_meta": "Meta分析",
                "menu_grant": "基金申请",
                "menu_peer_review": "同行评审",
                "menu_settings": "系统设置",
                "button_submit": "提交",
                "button_cancel": "取消",
                "button_save": "保存",
                "button_export": "导出",
                "button_analyze": "分析",
                "button_generate": "生成",
                "label_input": "输入",
                "label_output": "输出",
                "label_result": "结果",
                "status_processing": "处理中...",
                "status_completed": "已完成",
                "status_error": "发生错误",
                "title_welcome": "欢迎使用 MedAIagents",
                "desc_diagnosis": "基于症状和检查结果的智能诊断辅助",
                "desc_medication": "药物相互作用检测和用药安全审查",
                "desc_research": "RCT方案设计、Meta分析、基金申请辅助",
                "desc_writing": "论文结构生成、质量评分、期刊推荐",
                "hint_search": "请输入关键词或问题...",
                "msg_success": "操作成功",
                "msg_fail": "操作失败",
            },
            "en_US": {
                "app_title": "MedAIagents Medical AI Agent Framework",
                "menu_diagnosis": "Diagnosis Assistant",
                "menu_medication": "Medication Safety",
                "menu_emr": "Medical Records",
                "menu_icd10": "ICD-10 Coding",
                "menu_knowledge": "Knowledge Base",
                "menu_research": "Clinical Research",
                "menu_writing": "Medical Writing",
                "menu_paper_eval": "Paper Evaluation",
                "menu_journal_rec": "Journal Recommendation",
                "menu_meta": "Meta-Analysis",
                "menu_grant": "Grant Proposal",
                "menu_peer_review": "Peer Review",
                "menu_settings": "Settings",
                "button_submit": "Submit",
                "button_cancel": "Cancel",
                "button_save": "Save",
                "button_export": "Export",
                "button_analyze": "Analyze",
                "button_generate": "Generate",
                "label_input": "Input",
                "label_output": "Output",
                "label_result": "Result",
                "status_processing": "Processing...",
                "status_completed": "Completed",
                "status_error": "Error occurred",
                "title_welcome": "Welcome to MedAIagents",
                "desc_diagnosis": "Intelligent diagnosis based on symptoms and test results",
                "desc_medication": "Drug interaction detection and safety review",
                "desc_research": "RCT design, meta-analysis, grant proposal assistant",
                "desc_writing": "Paper structure, quality scoring, journal recommendation",
                "hint_search": "Enter keywords or questions...",
                "msg_success": "Operation successful",
                "msg_fail": "Operation failed",
            }
        }

    def set_language(self, lang: Language):
        """设置当前语言"""
        self._current_lang = lang

    def get_language(self) -> Language:
        """获取当前语言"""
        return self._current_lang

    def translate_ui(self, key: str) -> str:
        """翻译界面文本"""
        lang_code = self._current_lang.value
        return self._translations.get(lang_code, {}).get(key, key)

    def get_all_ui_keys(self) -> List[str]:
        """获取所有UI文本键"""
        return list(self._translations["zh_CN"].keys())


class MedicalTerminology:
    """医学术语标准化对照"""

    def __init__(self):
        self._terms = self._build_terminology_database()
        self._en_to_zh = {}
        self._zh_to_en = {}
        self._build_indices()

    def _build_terminology_database(self) -> Dict[str, MedicalTerm]:
        """构建医学术语数据库"""
        terms = {
            # 疾病
            "diabetes_mellitus": MedicalTerm(
                english="Diabetes Mellitus",
                chinese="糖尿病",
                abbreviation="DM",
                category="疾病",
                icd10_code="E10-E14",
                mesh_term="Diabetes Mellitus",
                snomed_id="73211009",
                definition="一组以高血糖为特征的代谢性疾病",
                synonyms=["Sugar diabetes", "高血糖症"]
            ),
            "hypertension": MedicalTerm(
                english="Hypertension",
                chinese="高血压",
                abbreviation="HTN",
                category="疾病",
                icd10_code="I10-I15",
                mesh_term="Hypertension",
                snomed_id="38341003",
                definition="动脉血压持续升高的慢性疾病",
                synonyms=["High blood pressure", "血压高"]
            ),
            "myocardial_infarction": MedicalTerm(
                english="Myocardial Infarction",
                chinese="心肌梗死",
                abbreviation="MI",
                category="疾病",
                icd10_code="I21-I22",
                mesh_term="Myocardial Infarction",
                snomed_id="22298006",
                definition="心肌因缺血导致坏死",
                synonyms=["Heart attack", "心梗", "心脏病发作"]
            ),
            "stroke": MedicalTerm(
                english="Stroke",
                chinese="脑卒中",
                abbreviation="CVA",
                category="疾病",
                icd10_code="I60-I64",
                mesh_term="Stroke",
                snomed_id="230690007",
                definition="脑部血液供应障碍导致的脑组织损伤",
                synonyms=["Cerebrovascular accident", "中风"]
            ),
            "pneumonia": MedicalTerm(
                english="Pneumonia",
                chinese="肺炎",
                abbreviation="",
                category="疾病",
                icd10_code="J12-J18",
                mesh_term="Pneumonia",
                snomed_id="233604007",
                definition="肺实质的炎症性感染",
                synonyms=["肺部感染"]
            ),
            "covid19": MedicalTerm(
                english="COVID-19",
                chinese="新型冠状病毒肺炎",
                abbreviation="COVID-19",
                category="疾病",
                icd10_code="U07.1",
                mesh_term="COVID-19",
                snomed_id="840539006",
                definition="由SARS-CoV-2引起的急性呼吸道传染病",
                synonyms=["新型冠状病毒感染", "新冠肺炎"]
            ),
            "cancer": MedicalTerm(
                english="Cancer",
                chinese="癌症/恶性肿瘤",
                abbreviation="CA",
                category="疾病",
                icd10_code="C00-C97",
                mesh_term="Neoplasms",
                snomed_id="363346000",
                definition="细胞异常增殖形成的恶性肿瘤",
                synonyms=["Malignancy", "Tumor", "癌", "肿瘤"]
            ),
            "chronic_kidney_disease": MedicalTerm(
                english="Chronic Kidney Disease",
                chinese="慢性肾脏病",
                abbreviation="CKD",
                category="疾病",
                icd10_code="N18",
                mesh_term="Renal Insufficiency, Chronic",
                snomed_id="709044004",
                definition="肾脏结构或功能异常持续超过3个月",
                synonyms=["慢性肾病", "慢性肾衰竭"]
            ),
            # 解剖
            "heart": MedicalTerm(
                english="Heart",
                chinese="心脏",
                abbreviation="",
                category="解剖",
                icd10_code="",
                mesh_term="Heart",
                snomed_id="80891009",
                definition="循环系统的中心泵血器官",
                synonyms=["Cardiac", "心"]
            ),
            "liver": MedicalTerm(
                english="Liver",
                chinese="肝脏",
                abbreviation="",
                category="解剖",
                icd10_code="",
                mesh_term="Liver",
                snomed_id="10200004",
                definition="人体最大的内脏器官，具有代谢、解毒等功能",
                synonyms=["Hepatic", "肝"]
            ),
            "lung": MedicalTerm(
                english="Lung",
                chinese="肺",
                abbreviation="",
                category="解剖",
                icd10_code="",
                mesh_term="Lung",
                snomed_id="39607008",
                definition="呼吸系统的主要器官",
                synonyms=["Pulmonary", "肺脏"]
            ),
            "kidney": MedicalTerm(
                english="Kidney",
                chinese="肾脏",
                abbreviation="",
                category="解剖",
                icd10_code="",
                mesh_term="Kidney",
                snomed_id="64033007",
                definition="泌尿系统的核心器官",
                synonyms=["Renal", "肾"]
            ),
            # 药物
            "metformin": MedicalTerm(
                english="Metformin",
                chinese="二甲双胍",
                abbreviation="",
                category="药物",
                icd10_code="",
                mesh_term="Metformin",
                snomed_id="691881",
                definition="双胍类口服降糖药，2型糖尿病一线用药",
                synonyms=["Glucophage", "格华止"]
            ),
            "aspirin": MedicalTerm(
                english="Aspirin",
                chinese="阿司匹林",
                abbreviation="ASA",
                category="药物",
                icd10_code="",
                mesh_term="Aspirin",
                snomed_id="387458008",
                definition="非甾体抗炎药，具有解热镇痛抗血小板作用",
                synonyms=["Acetylsalicylic acid", "乙酰水杨酸"]
            ),
            "insulin": MedicalTerm(
                english="Insulin",
                chinese="胰岛素",
                abbreviation="",
                category="药物",
                icd10_code="",
                mesh_term="Insulin",
                snomed_id="67866001",
                definition="胰腺分泌的调节血糖的蛋白质激素",
                synonyms=["胰岛素制剂"]
            ),
            "atorvastatin": MedicalTerm(
                english="Atorvastatin",
                chinese="阿托伐他汀",
                abbreviation="",
                category="药物",
                icd10_code="",
                mesh_term="Atorvastatin",
                snomed_id="407316006",
                definition="HMG-CoA还原酶抑制剂，用于降脂治疗",
                synonyms=["Lipitor", "立普妥"]
            ),
            # 检查
            "ct_scan": MedicalTerm(
                english="Computed Tomography",
                chinese="计算机断层扫描",
                abbreviation="CT",
                category="检查",
                icd10_code="",
                mesh_term="Tomography, X-Ray Computed",
                snomed_id="77477000",
                definition="利用X射线和计算机重建断层图像的影像学检查",
                synonyms=["CT scan", "CT检查"]
            ),
            "mri": MedicalTerm(
                english="Magnetic Resonance Imaging",
                chinese="磁共振成像",
                abbreviation="MRI",
                category="检查",
                icd10_code="",
                mesh_term="Magnetic Resonance Imaging",
                snomed_id="113091000",
                definition="利用磁场和射频脉冲获取人体组织图像",
                synonyms=["核磁共振", "MR"]
            ),
            "ultrasound": MedicalTerm(
                english="Ultrasonography",
                chinese="超声检查",
                abbreviation="US",
                category="检查",
                icd10_code="",
                mesh_term="Ultrasonography",
                snomed_id="16310003",
                definition="利用超声波获取人体内部结构图像",
                synonyms=["B超", "彩超", "超声"]
            ),
            "electrocardiogram": MedicalTerm(
                english="Electrocardiogram",
                chinese="心电图",
                abbreviation="ECG/EKG",
                category="检查",
                icd10_code="",
                mesh_term="Electrocardiography",
                snomed_id="115950006",
                definition="记录心脏电活动的检查方法",
                synonyms=["ECG", "EKG", "心电图检查"]
            ),
            "biopsy": MedicalTerm(
                english="Biopsy",
                chinese="活检/组织病理检查",
                abbreviation="",
                category="检查",
                icd10_code="",
                mesh_term="Biopsy",
                snomed_id="86273004",
                definition="从活体获取组织标本进行病理学检查",
                synonyms=["活组织检查", "病理活检"]
            ),
            # 生理指标
            "blood_pressure": MedicalTerm(
                english="Blood Pressure",
                chinese="血压",
                abbreviation="BP",
                category="生理指标",
                icd10_code="",
                mesh_term="Blood Pressure",
                snomed_id="75367002",
                definition="血液对血管壁的侧压力",
                synonyms=["动脉血压"]
            ),
            "blood_glucose": MedicalTerm(
                english="Blood Glucose",
                chinese="血糖",
                abbreviation="BG",
                category="生理指标",
                icd10_code="",
                mesh_term="Blood Glucose",
                snomed_id="33747003",
                definition="血液中葡萄糖的浓度",
                synonyms=["血糖值", "Glu"]
            ),
            "hemoglobin_a1c": MedicalTerm(
                english="Glycated Hemoglobin",
                chinese="糖化血红蛋白",
                abbreviation="HbA1c",
                category="生理指标",
                icd10_code="",
                mesh_term="Glycated Hemoglobin A",
                snomed_id="33747003",
                definition="反映过去2-3个月平均血糖水平的指标",
                synonyms=["HbA1c", "糖化血红蛋白A1c"]
            ),
        }
        return terms

    def _build_indices(self):
        """构建中英文索引"""
        for term_id, term in self._terms.items():
            self._en_to_zh[term.english.lower()] = term
            self._zh_to_en[term.chinese] = term
            for syn in term.synonyms:
                if syn.lower() not in self._en_to_zh:
                    self._en_to_zh[syn.lower()] = term
                if syn not in self._zh_to_en:
                    self._zh_to_en[syn] = term

    def lookup(self, query: str) -> Optional[MedicalTerm]:
        """
        查询术语
        """
        query_lower = query.lower().strip()
        # 英文查找
        if query_lower in self._en_to_zh:
            return self._en_to_zh[query_lower]
        # 中文查找
        if query in self._zh_to_en:
            return self._zh_to_en[query]
        # 模糊匹配
        for en_term, term_obj in self._en_to_zh.items():
            if query_lower in en_term or en_term in query_lower:
                return term_obj
        for zh_term, term_obj in self._zh_to_en.items():
            if query in zh_term or zh_term in query:
                return term_obj
        return None

    def translate_term(self, text: str, target_lang: Language) -> str:
        """
        翻译医学术语（简单替换）
        """
        term = self.lookup(text)
        if term:
            return term.chinese if target_lang == Language.ZH_CN else term.english
        return text

    def translate_text(self, text: str, target_lang: Language) -> str:
        """
        文本级术语翻译（替换文中所有已知术语）
        """
        result = text
        if target_lang == Language.ZH_CN:
            # 英译中：按英文术语长度降序替换，避免短词覆盖长词
            sorted_terms = sorted(self._en_to_zh.items(), key=lambda x: len(x[0]), reverse=True)
            for en_term, term_obj in sorted_terms:
                if en_term in result.lower():
                    result = result.replace(en_term, term_obj.chinese)
                    # 保留首字母大写的变体
                    result = result.replace(en_term.capitalize(), term_obj.chinese)
                    result = result.replace(en_term.upper(), term_obj.chinese)
        else:
            # 中译英
            sorted_terms = sorted(self._zh_to_en.items(), key=lambda x: len(x[0]), reverse=True)
            for zh_term, term_obj in sorted_terms:
                if zh_term in result:
                    result = result.replace(zh_term, term_obj.english)
        return result

    def get_terms_by_category(self, category: str) -> List[MedicalTerm]:
        """按分类获取术语"""
        return [t for t in self._terms.values() if t.category == category]

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return sorted(list(set(t.category for t in self._terms.values())))

    def search(self, keyword: str) -> List[MedicalTerm]:
        """模糊搜索术语"""
        results = []
        keyword_lower = keyword.lower()
        for term in self._terms.values():
            if (keyword_lower in term.english.lower() or
                keyword_lower in term.chinese or
                keyword_lower in term.definition.lower() or
                any(keyword_lower in syn.lower() for syn in term.synonyms)):
                results.append(term)
        return results

    def get_term_table(self) -> List[Dict[str, str]]:
        """获取所有术语对照表"""
        return [
            {
                "英文": t.english,
                "中文": t.chinese,
                "缩写": t.abbreviation,
                "ICD-10": t.icd10_code,
                "MeSH": t.mesh_term,
                "分类": t.category,
            }
            for t in self._terms.values()
        ]


class ChineseJournalDatabase:
    """中文核心期刊数据库"""

    def __init__(self):
        self.journals = self._build_database()

    def _build_database(self) -> List[Dict[str, Any]]:
        """构建中文核心期刊数据库"""
        return [
            {
                "name": "中华医学杂志",
                "english_name": "Chinese Medical Journal",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["综合医学"],
                "impact_factor_2023": 1.8,
                "publication_cycle": "周刊",
                "acceptance_rate": "约15%",
                "issn": "0376-2491",
                "cn": "11-2137/R",
            },
            {
                "name": "中华内科杂志",
                "english_name": "Chinese Journal of Internal Medicine",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["内科学"],
                "impact_factor_2023": 1.5,
                "publication_cycle": "月刊",
                "acceptance_rate": "约12%",
                "issn": "0578-1426",
                "cn": "11-2198/R",
            },
            {
                "name": "中华心血管病杂志",
                "english_name": "Chinese Journal of Cardiology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["心血管"],
                "impact_factor_2023": 1.6,
                "publication_cycle": "月刊",
                "acceptance_rate": "约10%",
                "issn": "0253-3758",
                "cn": "11-2148/R",
            },
            {
                "name": "中华内分泌代谢杂志",
                "english_name": "Chinese Journal of Endocrinology and Metabolism",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["内分泌"],
                "impact_factor_2023": 1.4,
                "publication_cycle": "月刊",
                "acceptance_rate": "约12%",
                "issn": "1000-6696",
                "cn": "12-1087/R",
            },
            {
                "name": "中华肿瘤杂志",
                "english_name": "Chinese Journal of Oncology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["肿瘤"],
                "impact_factor_2023": 1.7,
                "publication_cycle": "月刊",
                "acceptance_rate": "约10%",
                "issn": "0253-3766",
                "cn": "11-2152/R",
            },
            {
                "name": "中华消化杂志",
                "english_name": "Chinese Journal of Digestion",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["消化"],
                "impact_factor_2023": 1.3,
                "publication_cycle": "月刊",
                "acceptance_rate": "约14%",
                "issn": "0254-1432",
                "cn": "31-1367/R",
            },
            {
                "name": "中华神经科杂志",
                "english_name": "Chinese Journal of Neurology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["神经"],
                "impact_factor_2023": 1.5,
                "publication_cycle": "月刊",
                "acceptance_rate": "约11%",
                "issn": "1006-7876",
                "cn": "11-3694/R",
            },
            {
                "name": "中华结核和呼吸杂志",
                "english_name": "Chinese Journal of Tuberculosis and Respiratory Diseases",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["呼吸"],
                "impact_factor_2023": 1.4,
                "publication_cycle": "月刊",
                "acceptance_rate": "约12%",
                "issn": "1001-0939",
                "cn": "11-2147/R",
            },
            {
                "name": "中华肾脏病杂志",
                "english_name": "Chinese Journal of Nephrology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["肾脏"],
                "impact_factor_2023": 1.3,
                "publication_cycle": "月刊",
                "acceptance_rate": "约13%",
                "issn": "1001-7097",
                "cn": "44-1217/R",
            },
            {
                "name": "中华血液学杂志",
                "english_name": "Chinese Journal of Hematology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["血液"],
                "impact_factor_2023": 1.2,
                "publication_cycle": "月刊",
                "acceptance_rate": "约14%",
                "issn": "0253-2727",
                "cn": "12-1090/R",
            },
            {
                "name": "中国药理学通报",
                "english_name": "Chinese Pharmacological Bulletin",
                "publisher": "中国药理学会",
                "core_level": "北大核心/CSCD",
                "field": ["药学", "药理"],
                "impact_factor_2023": 1.8,
                "publication_cycle": "月刊",
                "acceptance_rate": "约18%",
                "issn": "1001-1978",
                "cn": "34-1086/R",
            },
            {
                "name": "中国中西医结合杂志",
                "english_name": "Chinese Journal of Integrated Traditional and Western Medicine",
                "publisher": "中国中西医结合学会",
                "core_level": "北大核心/CSCD",
                "field": ["中西医结合"],
                "impact_factor_2023": 1.6,
                "publication_cycle": "月刊",
                "acceptance_rate": "约15%",
                "issn": "1003-5370",
                "cn": "11-2787/R",
            },
            {
                "name": "中国医学影像技术",
                "english_name": "Chinese Journal of Medical Imaging Technology",
                "publisher": "中国科学院",
                "core_level": "北大核心/CSCD",
                "field": ["影像"],
                "impact_factor_2023": 1.1,
                "publication_cycle": "月刊",
                "acceptance_rate": "约20%",
                "issn": "1003-3289",
                "cn": "11-1881/R",
            },
            {
                "name": "中华护理杂志",
                "english_name": "Chinese Journal of Nursing",
                "publisher": "中华护理学会",
                "core_level": "北大核心/CSCD",
                "field": ["护理"],
                "impact_factor_2023": 2.5,
                "publication_cycle": "月刊",
                "acceptance_rate": "约10%",
                "issn": "0254-1769",
                "cn": "11-2234/R",
            },
            {
                "name": "中华流行病学杂志",
                "english_name": "Chinese Journal of Epidemiology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["流行病学", "公共卫生"],
                "impact_factor_2023": 1.9,
                "publication_cycle": "月刊",
                "acceptance_rate": "约12%",
                "issn": "0254-6450",
                "cn": "11-2338/R",
            },
            {
                "name": "中国公共卫生",
                "english_name": "Chinese Journal of Public Health",
                "publisher": "中华预防医学会",
                "core_level": "北大核心/CSCD",
                "field": ["公共卫生"],
                "impact_factor_2023": 1.7,
                "publication_cycle": "月刊",
                "acceptance_rate": "约15%",
                "issn": "1001-0580",
                "cn": "21-1234/R",
            },
            {
                "name": "中华儿科杂志",
                "english_name": "Chinese Journal of Pediatrics",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["儿科"],
                "impact_factor_2023": 1.4,
                "publication_cycle": "月刊",
                "acceptance_rate": "约13%",
                "issn": "0578-1310",
                "cn": "11-2140/R",
            },
            {
                "name": "中华妇产科杂志",
                "english_name": "Chinese Journal of Obstetrics and Gynecology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["妇产科"],
                "impact_factor_2023": 1.5,
                "publication_cycle": "月刊",
                "acceptance_rate": "约12%",
                "issn": "0529-567X",
                "cn": "11-2141/R",
            },
            {
                "name": "中华骨科杂志",
                "english_name": "Chinese Journal of Orthopaedics",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["骨科"],
                "impact_factor_2023": 1.6,
                "publication_cycle": "半月刊",
                "acceptance_rate": "约11%",
                "issn": "0253-2352",
                "cn": "12-1113/R",
            },
            {
                "name": "中华外科杂志",
                "english_name": "Chinese Journal of Surgery",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["外科"],
                "impact_factor_2023": 1.5,
                "publication_cycle": "半月刊",
                "acceptance_rate": "约10%",
                "issn": "0529-5815",
                "cn": "11-2139/R",
            },
            {
                "name": "中华检验医学杂志",
                "english_name": "Chinese Journal of Laboratory Medicine",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["检验"],
                "impact_factor_2023": 1.3,
                "publication_cycle": "月刊",
                "acceptance_rate": "约14%",
                "issn": "1009-9158",
                "cn": "11-4452/R",
            },
            {
                "name": "中华精神科杂志",
                "english_name": "Chinese Journal of Psychiatry",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["精神"],
                "impact_factor_2023": 1.2,
                "publication_cycle": "双月刊",
                "acceptance_rate": "约15%",
                "issn": "1006-7884",
                "cn": "11-3661/R",
            },
            {
                "name": "中华眼科杂志",
                "english_name": "Chinese Journal of Ophthalmology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["眼科"],
                "impact_factor_2023": 1.3,
                "publication_cycle": "月刊",
                "acceptance_rate": "约14%",
                "issn": "0412-4081",
                "cn": "11-2142/R",
            },
            {
                "name": "中华皮肤科杂志",
                "english_name": "Chinese Journal of Dermatology",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["皮肤"],
                "impact_factor_2023": 1.1,
                "publication_cycle": "月刊",
                "acceptance_rate": "约16%",
                "issn": "0412-4030",
                "cn": "32-1138/R",
            },
            {
                "name": "中华耳鼻咽喉头颈外科杂志",
                "english_name": "Chinese Journal of Otorhinolaryngology Head and Neck Surgery",
                "publisher": "中华医学会",
                "core_level": "北大核心/CSCD",
                "field": ["耳鼻咽喉"],
                "impact_factor_2023": 1.0,
                "publication_cycle": "月刊",
                "acceptance_rate": "约17%",
                "issn": "1673-0860",
                "cn": "11-5330/R",
            },
        ]

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索期刊"""
        results = []
        keyword_lower = keyword.lower()
        for journal in self.journals:
            searchable = (
                journal["name"] + journal["english_name"] +
                " ".join(journal["field"]) + journal["publisher"]
            ).lower()
            if keyword_lower in searchable:
                results.append(journal)
        return results

    def get_by_field(self, field: str) -> List[Dict[str, Any]]:
        """按领域获取期刊"""
        return [j for j in self.journals if field in j["field"]]

    def get_all_fields(self) -> List[str]:
        """获取所有领域"""
        fields = set()
        for j in self.journals:
            fields.update(j["field"])
        return sorted(list(fields))

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计"""
        return {
            "total_journals": len(self.journals),
            "fields_covered": len(self.get_all_fields()),
            "avg_if": round(sum(j.get("impact_factor_2023", 0) for j in self.journals) / len(self.journals), 2),
            "publication_cycles": {cycle: sum(1 for j in self.journals if j["publication_cycle"] == cycle)
                                  for cycle in set(j["publication_cycle"] for j in self.journals)}
        }


class MultilingualAssistant:
    """多语言助手主类"""

    def __init__(self):
        self.i18n = I18nManager()
        self.terminology = MedicalTerminology()
        self.chinese_journals = ChineseJournalDatabase()

    def translate_paper_abstract(self, abstract: str, target_lang: Language) -> Dict[str, str]:
        """
        论文摘要翻译辅助（术语级翻译）
        """
        translated = self.terminology.translate_text(abstract, target_lang)
        # 提取文中涉及的医学术语
        found_terms = []
        for term_id, term in self.terminology._terms.items():
            if term.english.lower() in abstract.lower():
                found_terms.append({
                    "原文": term.english,
                    "译文": term.chinese,
                    "缩写": term.abbreviation,
                    "定义": term.definition,
                })

        return {
            "translated_text": translated,
            "found_terms": found_terms,
            "term_count": len(found_terms),
        }

    def get_chinese_journal_recommendation(self, field: str) -> List[Dict[str, Any]]:
        """获取中文核心期刊推荐"""
        return self.chinese_journals.get_by_field(field)

    def generate_bilingual_report(self, content: Dict[str, Any]) -> str:
        """生成双语对照报告"""
        report = f"""
{'='*60}
双语医学报告
{'='*60}

【中文】
{content.get('zh', '无中文内容')}

---

【English】
{content.get('en', 'No English content')}

---

【术语对照表】
{'术语':<20s} {'Term':<30s} {'缩写':<10s}
{'-'*60}
"""
        for term in content.get('terms', []):
            report += f"{term['chinese']:<20s} {term['english']:<30s} {term.get('abbreviation', ''):<10s}\n"

        report += "\n" + "="*60 + "\n"
        return report
