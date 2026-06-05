#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDISC SDTM 术语翻译工具
将 codelist_name 翻译成中文存入 codelist_cn_name
将 cdisc_synonyms 翻译成中文存入 cdisc_submission_value_cn_name
"""

import json
import re
from typing import Dict, Tuple

# CDISC 标准术语翻译映射
CDISC_TRANSLATION_MAP = {
    # 功能测试
    "10-Meter Walk/Run Functional Test": "10 米步行/跑功能测试",
    "4-Stair Ascend Functional Test": "4 级台阶上楼功能测试",
    "4-Stair Descend Functional Test": "4 级台阶下楼功能测试",
    "6 Minute Walk Functional Test": "6 分钟步行功能测试",
    "ADNI Auditory Verbal Learning Functional Test": "ADNI 听觉言语学习功能测试",
    
    # 测试相关
    "Test Code": "测试代码",
    "Test Name": "测试名称",
    "Test Grade": "测试等级",
    "Time to Walk/Run 10 Meters": "步行/跑 10 米时间",
    "Time to Do 4-Stair Ascend": "4 级台阶上楼时间",
    "Was Walk/Run Performed": "是否执行步行/跑",
    "Was 4-Stair Ascend Performed": "是否执行 4 级台阶上楼",
    "Wear Orthoses": "穿戴矫形器",
    
    # 临床分类
    "Clinical Classification": "临床分类",
    "ORRES": "观察结果响应",
    "STRESC": "严重程度评分",
    "TN/TC": "测试名称/测试代码",
    
    # 疾病评估
    "AJCC TNM Staging System 7th Edition": "AJCC TNM 分期系统第 7 版",
    "AJCC Tumor Grade Response": "AJCC 肿瘤分级应答",
    "ASSIGN Cardiovascular Disease 10-Year Risk Score": "ASSIGN 心血管疾病 10 年风险评分",
    "ATLAS": "ATLAS",
    "Abnormal Involuntary Movement Scale": "异常不自主运动量表",
    "Acute Coronary Syndrome Presentation Category": "急性冠脉综合征呈现类别",
    "Acute Physiology and Chronic Health Evaluation II": "急性生理与慢性健康评估 II",
    
    # 通用术语
    "Study": "研究",
    "Subject": "受试者",
    "Visit": "访视",
    "Event": "事件",
    "Adverse Event": "不良事件",
    "Concomitant Medication": "合并用药",
    "Medical History": "病史",
    "Family History": "家族史",
    "Physical Examination": "体格检查",
    "Vital Signs": "生命体征",
    "Laboratory Test": "实验室检查",
    "Electrocardiogram": "心电图",
    "Demographics": "人口统计学",
    "Informed Consent": "知情同意",
    "Screening": "筛选",
    "Randomization": "随机化",
    "Discontinuation": "中断",
    "Withdrawal": "退出",
    "Completion": "完成",
    "Outcome": "结果",
    "Assessment": "评估",
    "Questionnaire": "问卷",
    "Scale": "量表",
    "Score": "评分",
    "Response": "应答",
    "Outcome Measure": "结局指标",
    "Exposure": "暴露",
    "Intervention": "干预",
    "Treatment": "治疗",
    "Drug": "药物",
    "Device": "器械",
    "Biologic": "生物制品",
    
    # 常见前缀后缀
    "Code": "代码",
    "Name": "名称",
    "Date": "日期",
    "Time": "时间",
    "Type": "类型",
    "Category": "类别",
    "Category Code": "类别代码",
    "Category Name": "类别名称",
    "Term": "术语",
    "Term Code": "术语代码",
    "Term Name": "术语名称",
    "Lowest Level": "最低级别",
    "Next Level": "下一级",
    "Parent": "父级",
    "Child": "子级",
    "Synonym": "同义词",
    "Definition": "定义",
    "Preferred Term": "首选术语",
    "Source": "来源",
    "Version": "版本",
    
    # 常见缩写
    "RCT": "随机对照试验",
    "RWE": "真实世界证据",
    "GCP": "药物临床试验质量管理规范",
    "SDTM": "研究数据标准塔",
    "CDISC": "临床数据交换标准协会",
    "AE": "不良事件",
    "SAE": "严重不良事件",
    "TEAE": "治疗期 Emergent 不良事件",
    "AESI": "感兴趣的安全不良事件",
    "PM": "合并用药",
    "MH": "既往病史",
    "FH": "家族史",
    "LB": "实验室检查",
    "VS": "生命体征",
    "ECG": "心电图",
    "PE": "体格检查",
    "DEMO": "人口统计学",
    "DS": "研究处置",
    "EX": "暴露",
    "CM": "合并用药",
    "MH": "既往病史",
    "RS": "研究者总结",
    "SS": "受试者总结",
}

def translate_codelist_name(name: str) -> str:
    """翻译 codelist_name 字段"""
    if not name:
        return ""
    
    translation = name
    
    # 先尝试完整匹配
    if name in CDISC_TRANSLATION_MAP:
        return CDISC_TRANSLATION_MAP[name]
    
    # 使用规则替换
    # 处理 "Test Code" 和 "Test Name" 后缀
    if name.endswith(" Test Code"):
        base_name = name[:-10]
        base_cn = translate_codelist_name(base_name)
        return f"{base_cn} 测试代码"
    
    if name.endswith(" Test Name"):
        base_name = name[:-10]
        base_cn = translate_codelist_name(base_name)
        return f"{base_cn} 测试名称"
    
    # 处理 "Clinical Classification"
    if " Clinical Classification " in name:
        parts = name.split(" Clinical Classification ")
        if len(parts) == 2:
            prefix_cn = translate_codelist_name(parts[0])
            suffix = parts[1]
            if suffix.startswith("ORRES for "):
                detail = suffix[10:]
                detail_cn = translate_codelist_name(detail)
                return f"{prefix_cn} 临床分类 ORRES {detail_cn}"
            elif suffix.startswith("STRESC for "):
                detail = suffix[11:]
                detail_cn = translate_codelist_name(detail)
                return f"{prefix_cn} 临床分类 STRESC {detail_cn}"
    
    # 逐个单词翻译
    words = name.split()
    translated_words = []
    for word in words:
        # 清理标点
        clean_word = re.sub(r'[^a-zA-Z0-9]', '', word)
        if clean_word in CDISC_TRANSLATION_MAP:
            translated_words.append(CDISC_TRANSLATION_MAP[clean_word])
        else:
            translated_words.append(word)
    
    # 重新组合，保留原有空格和标点
    result = name
    for key, value in CDISC_TRANSLATION_MAP.items():
        if key in result:
            result = result.replace(key, value)
    
    return result

def translate_synonym(synonym: str) -> str:
    """翻译 cdisc_synonyms 字段"""
    if not synonym:
        return ""
    
    result = synonym
    
    # 应用翻译映射
    for key, value in CDISC_TRANSLATION_MAP.items():
        if key in result:
            result = result.replace(key, value)
    
    # 处理变量名格式 (如 TENMW1-Was Walk/Run Performed)
    if '-' in result and result.split('-')[0].upper() == result.split('-')[0]:
        # 这是变量名前缀格式
        parts = result.split('-', 1)
        if len(parts) == 2:
            var_name = parts[0]
            description = parts[1]
            description_cn = translate_synonym(description) if description != result else description
            return f"{var_name}-{description_cn}"
    
    return result

def batch_translate(data: list) -> Tuple[Dict[str, str], Dict[str, str]]:
    """批量翻译并返回映射"""
    codelist_map = {}
    synonym_map = {}
    
    for item in data:
        codelist_name = item.get('codelist_name')
        cdisc_synonyms = item.get('cdisc_synonyms')
        
        if codelist_name:
            codelist_map[codelist_name] = translate_codelist_name(codelist_name)
        
        if cdisc_synonyms:
            synonym_map[cdisc_synonyms] = translate_synonym(cdisc_synonyms)
    
    return codelist_map, synonym_map

if __name__ == "__main__":
    # 测试翻译
    test_cases = [
        "10-Meter Walk/Run Functional Test Test Code",
        "TENMW1-Was Walk/Run Performed",
        "AJCC TNM Staging System 7th Edition Clinical Classification Test Name",
        "Abnormal Involuntary Movement Scale Clinical Classification ORRES for AIMS0101 Through AIMS0107 TN/TC",
    ]
    
    print("=== 翻译测试 ===")
    for test in test_cases:
        print(f"原文：{test}")
        print(f"翻译：{translate_codelist_name(test)}")
        print()
