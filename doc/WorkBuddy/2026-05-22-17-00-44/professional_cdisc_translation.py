#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDISC SDTM 专业医学术语翻译和数据库更新脚本
"""

import pymysql
import json
import re
from typing import Optional, Tuple, Dict
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'host': 'rm-2ze99d2eaw127x8i6yo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'jdms',
    'password': 'jdjd@12358',
    'database': 'ohms',
    'charset': 'utf8mb4'
}

class ProfessionalMedicalTranslator:
    """专业医学翻译器"""
    
    def __init__(self):
        # 构建全面的医学术语翻译表
        self._build_medical_dictionary()
    
    def _build_medical_dictionary(self):
        """构建医学词典"""
        # CDISC SDTM 标准术语
        self.cdisc_terms = {
            # 实验室检查
            "Laboratory Test Name": "实验室检查项目",
            "Laboratory Test Code": "实验室检查代码",
            "Laboratory Analytical Method": "实验室分析方法",
            "Laboratory Analytical Method Calculation Formula": "实验室分析方法计算公式",
            "Anatomical Location": "解剖部位",
            "Unit": "计量单位",
            "Method": "方法",
            "Microscopic Findings": "镜下所见",
            "Microbiology Test Name": "微生物学检验项目",
            "Microbiology Test Code": "微生物学检验代码",
            "Microorganism": "微生物名称",
            
            # 药代动力学
            "PK Parameters": "药代动力学参数",
            "PK Parameters Code": "药代动力学参数代码",
            "PK Units of Measure": "药代动力学计量单位",
            "PK Analytical Method": "药代动力学分析方法",
            
            # 细胞和免疫
            "Cell Phenotyping Test Name": "细胞表型分析测试项目",
            "Cell Phenotyping Test Code": "细胞表型分析测试代码",
            "Binding Agent for Immunogenicity Tests": "免疫原性检验结合剂",
            
            # 量表评估
            "Questionnaire": "调查问卷",
            "Category of Questionnaire": "问卷类别",
            "Questionnaire Test Name": "问卷测试项目",
            "Questionnaire Test Code": "问卷测试代码",
            
            # 功能测试
            "Functional Test": "功能测试",
            "Test Name": "测试项目",
            "Test Code": "测试代码",
            "Category of Functional Test": "功能测试类别",
            
            # 通用
            "Name": "名称",
            "Code": "代码",
            "Date": "日期",
            "Time": "时间",
            "Type": "类型",
            "Category": "类别",
            "Term": "术语",
            "Value": "值",
        }
        
        # 专业量表翻译
        self.scale_terms = {
            # 阿尔茨海默病相关
            "Alzheimer's Disease Assessment Scale": "阿尔茨海默病评估量表",
            "ADAS-Cog": "阿尔茨海默病评估量表 - 认知分量表",
            "Alzheimer's Disease Cooperative Study-Activities of Daily Living": "阿尔茨海默病合作研究 - 日常生活活动量表",
            "ADCS-ADL": "阿尔茨海默病合作研究 - 日常生活活动量表",
            "MCI Version": "轻度认知障碍版",
            "Severe Dementia Version": "重度痴呆版",
            
            # 功能评估
            "Functional Assessment of Chronic Illness Therapy": "慢性病治疗功能评估量表",
            "FACIT": "慢性病治疗功能评估量表",
            "FACIT-Fatigue": "慢性病治疗功能评估 - 疲乏分量表",
            "FACIT-Social": "慢性病治疗功能评估 - 社会功能分量表",
            "FACIT-Dyspnea": "慢性病治疗功能评估 - 呼吸困难分量表",
            
            # 认知功能
            "Alzheimer's Disease Cooperative Study-Cognitive Assessment Interview": "阿尔茨海默病合作研究 - 认知功能评估访谈",
            "Brief Assessment of Cognition in Schizophrenia": "精神分裂症认知功能简要评估",
            "BACS": "精神分裂症认知功能简要评估",
            "Controlled Oral Word Association Test": "控制性口语联想测试",
            "COWAT": "控制性口语联想测试",
            "Emotion Recognition": "情绪识别测试",
            
            # 生活质量
            "World Health Organization Disability Assessment Schedule": "世界卫生组织残疾评估量表",
            "WHODAS": "世界卫生组织残疾评估量表",
            "Patient-Reported Outcomes": "患者报告结局",
            "PRO": "患者报告结局",
            "Pediatric Quality of Life": "儿童生活质量",
            "PedsQL": "儿童生活质量量表",
            "Neuromuscular Module": "神经肌肉模块",
            
            # 成瘾相关
            "Alcohol Use Disorders Identification Test": "酒精使用障碍识别测试",
            "AUDIT": "酒精使用障碍识别测试",
            "AUDIT-Consumption": "酒精使用障碍识别测试 - 饮酒分量表",
            "AUDIT-C": "酒精使用障碍识别测试 - 简版",
            "Self-Report Version": "自报版",
            "Concise Interview Version": "简短访谈版",
            
            # 呼吸相关
            "Airway Questionnaire 20": "气道问卷 20",
            "AQLQ": "哮喘生活质量问卷",
            
            # 其他评估
            "Deployment Risk and Resilience Inventory": "部署风险与韧性清单",
            "DRRI": "部署风险与韧性清单",
            "National Youth Tobacco Survey": "全国青年烟草调查",
            "NYTS": "全国青年烟草调查",
            "ADNI Auditory Verbal Learning Test": "阿尔茨海默病神经影像计划听觉言语学习测试",
        }
        
        # 运动功能测试
        self.motor_terms = {
            "10-Meter Walk/Run Functional Test": "10 米步行/跑功能测试",
            "4-Stair Ascend Functional Test": "四级台阶上楼功能测试",
            "4-Stair Descend Functional Test": "四级台阶下楼功能测试",
            "6 Minute Walk Functional Test": "6 分钟步行功能测试",
            "6MWT": "6 分钟步行测试",
        }
        
        # 组织名称
        self.org_names = {
            "World Health Organization": "世界卫生组织",
            "WHO": "世界卫生组织",
            "National Comprehensive Cancer Network": "美国国家综合癌症网络",
            "NCCN": "美国国家综合癌症网络",
            "Alzheimer's Disease Cooperative Study": "阿尔茨海默病合作研究",
            "ADCS": "阿尔茨海默病合作研究",
            "ADNI": "阿尔茨海默病神经影像计划",
            "CDISC": "临床数据交换标准协会",
        }
        
        # 医学专业词汇
        self.medical_vocab = {
            "Cognitive": "认知",
            "Functional": "功能",
            "Assessment": "评估",
            "Evaluation": "评价",
            "Analysis": "分析",
            "Inventory": "清单",
            "Questionnaire": "问卷",
            "Scale": "量表",
            "Test": "测试",
            "Survey": "调查",
            "Disability": "残疾",
            "Dyspnea": "呼吸困难",
            "Fatigue": "疲乏",
            "Schizophrenia": "精神分裂症",
            "Dementia": "痴呆",
            "Depression": "抑郁",
            "Anxiety": "焦虑",
            "Neuromuscular": "神经肌肉",
            "Immunogenicity": "免疫原性",
            "Phenotyping": "表型分析",
            "Microbiological": "微生物学",
            "Pharmacokinetic": "药代动力学",
            "Analytical": "分析",
            "Microscopic": "镜下",
            "Anatomical": "解剖",
        }
    
    def translate_codelist_name(self, name: Optional[str]) -> Optional[str]:
        """翻译 codelist_name"""
        if not name:
            return None
        
        result = name
        
        # 1. 组织名称翻译
        for en, cn in self.org_names.items():
            if en in result:
                result = result.replace(en, cn)
        
        # 2. 专业量表翻译 (按长度降序)
        sorted_scales = sorted(self.scale_terms.items(), key=lambda x: len(x[0]), reverse=True)
        for en, cn in sorted_scales:
            if en in result:
                result = result.replace(en, cn)
        
        # 3. 运动功能测试翻译
        for en, cn in self.motor_terms.items():
            if en in result:
                result = result.replace(en, cn)
        
        # 4. CDISC 标准术语翻译 (按长度降序)
        sorted_terms = sorted(self.cdisc_terms.items(), key=lambda x: len(x[0]), reverse=True)
        for en, cn in sorted_terms:
            if en in result:
                result = result.replace(en, cn)
        
        # 5. 处理版本号 (如 Version 3.0, 2.0 等)
        version_patterns = [
            (r'(\d+\.\d+)$', r' 第\1 版'),  # 结尾版本号
            (r' Version (\d+\.\d+)', r' 第\1 版'),  # "Version X.X"
            (r'V(\d+\.\d+)', r'第\1 版'),  # "VX.X"
        ]
        for pattern, replacement in version_patterns:
            result = re.sub(pattern, replacement, result)
        
        # 6. 处理日期格式
        result = re.sub(r'(\d{2}[A-Z]{3}\d{4})', r'\1 版', result)
        
        # 7. 翻译版本相关
        if " Version" in result and "Version " not in result:
            result = result.replace(" Version", " 版本")
        if "Version Questionnaire" in result:
            result = result.replace("Version Questionnaire", "版本问卷")
        
        return result
    
    def translate_synonym(self, synonym: Optional[str]) -> Optional[str]:
        """翻译 cdisc_synonyms"""
        if not synonym:
            return None
        
        result = synonym
        original = synonym
        
        # 1. 处理变量名前缀 (如 LABST, AETERM 等)
        var_pattern = r'^([A-Z]+(\d|[1-9]\d*))-(.*)$'
        match = re.match(var_pattern, result)
        
        if match:
            var_name = match.group(1)
            description = match.group(3)
            
            # 翻译描述部分
            trans_desc = description
            
            # 应用医学术语翻译
            sorted_terms = sorted(self.cdisc_terms.items(), key=lambda x: len(x[0]), reverse=True)
            for en, cn in sorted_terms:
                if en in trans_desc:
                    trans_desc = trans_desc.replace(en, cn)
            
            # 应用医学词汇翻译
            for en, cn in self.medical_vocab.items():
                if en in trans_desc:
                    trans_desc = trans_desc.replace(en, cn)
            
            if trans_desc != description:
                result = f"{var_name}-{trans_desc}"
        else:
            # 无变量名前缀，直接翻译
            sorted_terms = sorted(self.cdisc_terms.items(), key=lambda x: len(x[0]), reverse=True)
            for en, cn in sorted_terms:
                if en in result:
                    result = result.replace(en, cn)
            
            for en, cn in self.medical_vocab.items():
                if en in result:
                    result = result.replace(en, cn)
        
        return result if result != original else original

def export_terminology_data() -> Tuple[list, dict, dict]:
    """导出术语数据"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, codelist_name, cdisc_synonyms 
        FROM sdtm_terminology 
        WHERE codelist_name IS NOT NULL OR cdisc_synonyms IS NOT NULL
        ORDER BY id
    """)
    
    data = []
    for row in cursor.fetchall():
        data.append({
            'id': row[0],
            'codelist_name': row[1],
            'cdisc_synonyms': row[2]
        })
    
    # 构建唯一术语映射
    codelist_map = {}
    synonym_map = {}
    
    for item in data:
        if item['codelist_name'] and item['codelist_name'] not in codelist_map:
            codelist_map[item['codelist_name']] = []
        if item['cdisc_synonyms'] and item['cdisc_synonyms'] not in synonym_map:
            synonym_map[item['cdisc_synonyms']] = []
        
        if item['codelist_name']:
            codelist_map[item['codelist_name']].append(item['id'])
        if item['cdisc_synonyms']:
            synonym_map[item['cdisc_synonyms']].append(item['id'])
    
    cursor.close()
    conn.close()
    
    return data, codelist_map, synonym_map

def update_database_with_translations(translator: ProfessionalMedicalTranslator) -> dict:
    """使用翻译结果更新数据库"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    stats = {
        'total': 0,
        'codelist_updated': 0,
        'synonym_updated': 0,
        'errors': []
    }
    
    # 获取所有记录
    cursor.execute("""
        SELECT id, codelist_name, cdisc_synonyms
        FROM sdtm_terminology
        ORDER BY id
    """)
    
    all_records = cursor.fetchall()
    stats['total'] = len(all_records)
    
    print(f"开始翻译并更新 {stats['total']} 条记录...")
    print("-" * 100)
    
    batch_size = 1000
    for start_idx in range(0, len(all_records), batch_size):
        end_idx = min(start_idx + batch_size, len(all_records))
        batch = all_records[start_idx:end_idx]
        
        for record in batch:
            record_id = record[0]
            codelist_name = record[1]
            cdisc_synonyms = record[2]
            
            try:
                # 翻译
                codelist_cn = translator.translate_codelist_name(codelist_name)
                synonym_cn = translator.translate_synonym(cdisc_synonyms)
                
                # 构建更新语句
                updates = []
                values = []
                
                if codelist_cn:
                    updates.append("codelist_cn_name = %s")
                    values.append(codelist_cn)
                    stats['codelist_updated'] += 1
                
                if synonym_cn:
                    updates.append("cdisc_submission_value_cn_name = %s")
                    values.append(synonym_cn)
                    stats['synonym_updated'] += 1
                
                if updates:
                    values.append(record_id)
                    sql = f"UPDATE sdtm_terminology SET {', '.join(updates)} WHERE id = %s"
                    cursor.execute(sql, values)
                    
            except Exception as e:
                stats['errors'].append(f"ID {record_id}: {str(e)}")
        
        # 提交批次
        conn.commit()
        
        progress = (end_idx / len(all_records)) * 100
        print(f"进度：{end_idx}/{len(all_records)} ({progress:.1f}%)")
    
    cursor.close()
    conn.close()
    
    print("-" * 100)
    return stats

def generate_translation_report() -> None:
    """生成翻译对照报告"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 获取翻译样例
    cursor.execute("""
        SELECT 
            codelist_name,
            codelist_cn_name,
            cdisc_synonyms,
            cdisc_submission_value_cn_name
        FROM sdtm_terminology
        WHERE codelist_name IS NOT NULL AND codelist_cn_name IS NOT NULL
        ORDER BY id
        LIMIT 100
    """)
    
    samples = cursor.fetchall()
    
    # 统计信息
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN codelist_cn_name IS NOT NULL THEN 1 ELSE 0 END) as codelist_translated,
            SUM(CASE WHEN cdisc_submission_value_cn_name IS NOT NULL THEN 1 ELSE 0 END) as synonym_translated
        FROM sdtm_terminology
    """)
    
    stats = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    # 生成报告
    report = []
    report.append("=" * 150)
    report.append("CDISC SDTM 术语翻译对照报告")
    report.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 150)
    
    report.append(f"\n统计信息:")
    report.append(f"  总记录数：{stats[0]:,}")
    report.append(f"  已翻译 codelist_name: {stats[1]:,} ({stats[1]/stats[0]*100:.1f}%)")
    report.append(f"  已翻译 cdisc_synonyms: {stats[2]:,} ({stats[2]/stats[0]*100:.1f}%)")
    
    report.append(f"\n{'序号':<6} {'原文 (codelist_name)':<55} {'中文翻译 (codelist_cn_name)':<55}")
    report.append("-" * 150)
    
    for i, sample in enumerate(samples[:30], 1):
        en_name = str(sample[0])[:55] if sample[0] else "NULL"
        cn_name = str(sample[1])[:55] if sample[1] else "NULL"
        report.append(f"{i:<6} {en_name:<55} {cn_name:<55}")
    
    report.append(f"\n... (共{len(samples)}条，显示前 30 条)")
    
    # 保存报告
    report_path = 'C:/Users/Administrator/WorkBuddy/2026-05-22-17-00-44/cdisc_translation_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n翻译对照报告已保存到：{report_path}")
    
    # 打印报告
    print('\n'.join(report))

def main():
    """主函数"""
    print("=" * 100)
    print("CDISC SDTM 专业医学术语翻译工具")
    print("=" * 100)
    print()
    
    # 1. 初始化翻译器
    print("正在初始化医学翻译器...")
    translator = ProfessionalMedicalTranslator()
    print("翻译器初始化完成")
    print()
    
    # 2. 更新数据库
    print("正在翻译并更新数据库...")
    stats = update_database_with_translations(translator)
    
    print(f"\n翻译完成!")
    print(f"  总记录数：{stats['total']:,}")
    print(f"  已翻译 codelist_name: {stats['codelist_updated']:,}")
    print(f"  已翻译 cdisc_synonyms: {stats['synonym_updated']:,}")
    if stats['errors']:
        print(f"  错误数：{len(stats['errors'])}")
    print()
    
    # 3. 生成报告
    print("正在生成翻译对照报告...")
    generate_translation_report()

if __name__ == "__main__":
    main()
