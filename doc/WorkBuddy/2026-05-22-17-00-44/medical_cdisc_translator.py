#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDISC SDTM 专业医学翻译工具
基于 CDISC 标准和医学专业术语进行翻译
"""

import re
from typing import Optional

class MedicalTranslator:
    """专业医学翻译器"""
    
    def __init__(self):
        # CDISC 标准术语专业翻译映射
        self.terms = {
            # 实验室检查
            "Laboratory Test Name": "实验室检查名称",
            "Laboratory Test Code": "实验室检查代码",
            "Laboratory Anatomical Location": "实验室检查解剖位置",
            "Method": "检测方法",
            "Unit": "单位",
            "Microscopic Findings": "显微镜检查发现",
            "Microbiology Test Name": "微生物学检测名称",
            "Microbiology Test Code": "微生物学检测代码",
            "Microorganism": "微生物",
            
            # 药代动力学
            "PK Parameters": "药代动力学参数",
            "PK Parameters Code": "药代动力学参数代码",
            "PK Units of Measure": "药代动力学计量单位",
            "Binding Agent for Immunogenicity Tests": "免疫原性测试结合剂",
            "Cell Phenotyping Test Name": "细胞表型分析测试名称",
            "Cell Phenotyping Test Code": "细胞表型分析测试代码",
            
            # 功能评估量表
            "Functional Assessment of Chronic Illness Therapy-Fatigue": "慢性病治疗功能评估 - 疲劳量表",
            "Functional Assessment of Chronic Illness Therapy-Social": "慢性病治疗功能评估 - 社会功能",
            "ADNI Auditory Verbal Learning Functional Test": "阿尔茨海默病神经影像学计划听觉言语学习功能测试",
            "Alzheimer's Disease Cooperative Study-Activities of Daily Living": "阿尔茨海默病合作研究 - 日常生活活动量表",
            "World Health Organization Disability Assessment Schedule": "世界卫生组织残疾评估量表",
            "Pediatric Quality of Life Neuromuscular Module": "儿童生活质量神经肌肉模块",
            "National Youth Tobacco Survey": "全国青年烟草调查",
            "Deployment Risk and Resilience Inventory-2": "部署风险与韧性清单 -2",
            "Patient-Reported Outcomes Version of the Common Terminology Criteria": "患者报告结局通用术语标准版",
            "National Comprehensive Cancer Network/Functional Assessment of Cancer Therapy": "美国国家综合癌症网络/癌症治疗功能评估",
            
            # 解剖位置
            "Anatomical Location": "解剖位置",
            
            # 问卷和评估
            "Category of Questionnaire": "问卷类别",
            "Questionnaire": "问卷",
            "Questionnaire Name": "问卷名称",
            "Questionnaire Code": "问卷代码",
            
            # 测试相关
            "Test Name": "测试名称",
            "Test Code": "测试代码",
            "Functional Test": "功能测试",
            
            # 研究相关
            "Study": "研究",
            "Subject": "受试者",
            "Visit": "访视",
            "Event": "事件",
            "Outcome": "结局",
            "Assessment": "评估",
            
            # 临床相关
            "Clinical Classification": "临床分类",
            "Adverse Event": "不良事件",
            "Medical History": "医学史",
            "Concomitant Medication": "合并用药",
            "Physical Examination": "体格检查",
            "Vital Signs": "生命体征",
            "Electrocardiogram": "心电图",
            "Demographics": "人口统计学资料",
            
            # 通用后缀
            "Test Name": "测试名称",
            "Test Code": "测试代码",
            "Name": "名称",
            "Code": "代码",
            "Date": "日期",
            "Time": "时间",
            "Type": "类型",
            "Category": "类别",
            "Term": "术语",
            "Value": "值",
            "Category Code": "类别代码",
            "Category Name": "类别名称",
        }
        
        # 医学专业词汇翻译
        self.medical_terms = {
            # 疾病和症状
            "Adverse Event": "不良事件",
            "Serious Adverse Event": "严重不良事件",
            "Infection": "感染",
            "Inflammation": "炎症",
            "Tumor": "肿瘤",
            "Cancer": "癌症",
            "Diabetes": "糖尿病",
            "Hypertension": "高血压",
            "Cardiovascular": "心血管",
            "Respiratory": "呼吸",
            "Neurological": "神经",
            "Psychiatric": "精神",
            "Gastrointestinal": "胃肠道",
            "Hepatic": "肝脏",
            "Renal": "肾脏",
            "Hematological": "血液学",
            "Immunological": "免疫学",
            
            # 检验类型
            "Hematology": "血液学",
            "Biochemistry": "生化",
            "Urinalysis": "尿液分析",
            "Immunology": "免疫学",
            "Molecular": "分子生物学",
            "Genetic": "遗传学",
            "Pathology": "病理学",
            "Microscopy": "显微镜检查",
            
            # 解剖部位
            "Blood": "血液",
            "Plasma": "血浆",
            "Serum": "血清",
            "Urine": "尿液",
            "Feces": "粪便",
            "Tissue": "组织",
            "Cell": "细胞",
            "Liver": "肝脏",
            "Kidney": "肾脏",
            "Heart": "心脏",
            "Lung": "肺",
            "Brain": "脑",
            "Skin": "皮肤",
            
            # 药物和治疗
            "Drug": "药物",
            "Medication": "用药",
            "Treatment": "治疗",
            "Intervention": "干预",
            "Therapy": "疗法",
            "Dosage": "剂量",
            "Dose": "剂量",
            "Administration": "给药",
            "Route": "途径",
            
            # 统计和分析
            "Mean": "均值",
            "Median": "中位数",
            "Standard Deviation": "标准差",
            "Percentage": "百分比",
            "Ratio": "比率",
            "Rate": "率",
            "Frequency": "频率",
            "Incidence": "发生率",
            "Prevalence": "流行率",
        }
        
        # 单位翻译
        self.units = {
            "mg": "毫克",
            "g": "克",
            "kg": "千克",
            "ml": "毫升",
            "l": "升",
            "mmol/l": "毫摩尔/升",
            "umol/l": "微摩尔/升",
            "ng/ml": "纳克/毫升",
            "pg/ml": "皮克/毫升",
            "%": "百分比",
            "beats/min": "次/分",
            "mmhg": "毫米汞柱",
            "celsius": "摄氏度",
            "hours": "小时",
            "days": "天",
            "weeks": "周",
            "months": "月",
            "years": "年",
        }
    
    def translate_codelist_name(self, name: Optional[str]) -> Optional[str]:
        """翻译 codelist_name 字段"""
        if not name:
            return None
        
        original = name
        translation = name
        
        # 1. 首先检查完全匹配
        if name in self.terms:
            return self.terms[name]
        
        # 2. 处理包含关系的术语 (从长到短)
        sorted_terms = sorted(self.terms.keys(), key=len, reverse=True)
        for term in sorted_terms:
            if term in translation:
                translation = translation.replace(term, self.terms[term])
        
        # 3. 处理医学专业术语
        for term, cn in self.medical_terms.items():
            if term in translation:
                translation = translation.replace(term, cn)
        
        # 4. 处理特殊模式
        # 模式 1: "Test Name" / "Test Code" 后缀
        if translation != original:
            # 如果已经有翻译，检查是否还有未翻译的 Test Name/Code
            if " Test Name" in translation:
                translation = translation.replace(" Test Name", " 测试名称")
            if " Test Code" in translation:
                translation = translation.replace(" Test Code", " 测试代码")
        
        # 5. 处理量表名称 (包含版本号的)
        # 例如："Pediatric Quality of Life Neuromuscular Module Version 3.0"
        version_pattern = r'(Version \d+\.\d+)'
        version_match = re.search(version_pattern, translation)
        if version_match:
            translation = translation.replace(version_match.group(1), f" 第{version_match.group(1).replace('Version ', '')}版")
        
        # 6. 处理组织名称
        org_patterns = {
            r'World Health Organization': '世界卫生组织',
            r'National Comprehensive Cancer Network': '美国国家综合癌症网络',
            r'Alzheimer\'s Disease Cooperative Study': '阿尔茨海默病合作研究',
            r'Functional Assessment of Chronic Illness Therapy': '慢性病治疗功能评估',
        }
        
        for pattern, cn in org_patterns.items():
            if re.search(pattern, translation):
                translation = re.sub(pattern, cn, translation)
        
        # 如果没有做任何翻译，返回原文
        if translation == original:
            return original
            
        return translation
    
    def translate_synonym(self, synonym: Optional[str]) -> Optional[str]:
        """翻译 cdisc_synonyms 字段"""
        if not synonym:
            return None
        
        original = synonym
        translation = synonym
        
        # 1. 处理变量名前缀 (如 LAB1, AE1 等)
        var_prefix_pattern = r'^([A-Z]+(\d|[1-9]\d*))-(.*)$'
        match = re.match(var_prefix_pattern, translation)
        if match:
            var_name = match.group(1)
            var_number = match.group(2)
            description = match.group(3)
            
            # 翻译描述部分
            desc_translation = description
            
            # 应用医学术语翻译
            for term, cn in self.medical_terms.items():
                if term in desc_translation:
                    desc_translation = desc_translation.replace(term, cn)
            
            # 应用通用术语翻译
            sorted_terms = sorted(self.terms.keys(), key=len, reverse=True)
            for term in sorted_terms:
                if term in desc_translation:
                    desc_translation = desc_translation.replace(term, self.terms[term])
            
            # 如果有变化，重组
            if desc_translation != description:
                translation = f"{var_name}-{desc_translation}"
        
        # 2. 如果没有变量名前缀，直接翻译
        else:
            sorted_terms = sorted(self.terms.keys(), key=len, reverse=True)
            for term in sorted_terms:
                if term in translation:
                    translation = translation.replace(term, self.terms[term])
            
            for term, cn in self.medical_terms.items():
                if term in translation:
                    translation = translation.replace(term, cn)
        
        # 如果没有做任何翻译，返回原文
        if translation == original:
            return original
            
        return translation

# 测试
if __name__ == "__main__":
    translator = MedicalTranslator()
    
    test_cases = [
        "Laboratory Test Name",
        "Functional Assessment of Chronic Illness Therapy-Social",
        "World Health Organization Disability Assessment Schedule 2.0",
        "LAB1-Hemoglobin",
        "AE1-Infection",
    ]
    
    print("=== codelist_name 翻译测试 ===")
    for test in test_cases:
        print(f"原文：{test}")
        print(f"翻译：{translator.translate_codelist_name(test)}")
        print()
    
    print("\n=== cdisc_synonyms 翻译测试 ===")
    synonym_tests = [
        "LAB1-Hemoglobin",
        "AE1-Serious Infection",
        "TENMW1-Was Walk/Run Performed",
    ]
    for test in synonym_tests:
        print(f"原文：{test}")
        print(f"翻译：{translator.translate_synonym(test)}")
        print()
