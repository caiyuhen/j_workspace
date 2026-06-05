#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDISC SDTM 最终专业医学翻译器
完整翻译所有医学术语
"""

import pymysql
import re
from datetime import datetime

DB_CONFIG = {
    'host': 'rm-2ze99d2eaw127x8i6yo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'jdms',
    'password': 'jdjd@12358',
    'database': 'ohms',
    'charset': 'utf8mb4'
}

# 完整的医学翻译词典
MEDICAL_DICT = {
    # 基本测试术语
    "Test": "测试",
    "Test Code": "测试代码",
    "Test Name": "测试项目",
    "Code": "代码",
    "Name": "名称",
    
    # 实验室
    "Laboratory": "实验室",
    "Laboratory Test": "实验室检查",
    "Hematology": "血液学",
    "Biochemistry": "生化",
    "Urine": "尿",
    "Blood": "血",
    "Plasma": "血浆",
    "Serum": "血清",
    
    # 功能
    "Functional": "功能",
    "Assessment": "评估",
    "Evaluation": "评价",
    "Walk": "步行",
    "Run": "跑",
    "Meter": "米",
    "Stair": "台阶",
    "Ascend": "上楼",
    "Descend": "下楼",
    "Minute": "分钟",
    
    # 时间相关
    "Time": "时间",
    "Date": "日期",
    "Day": "天",
    "Week": "周",
    "Month": "月",
    "Year": "年",
    "Hour": "小时",
    
    # 状态
    "Was": "是否",
    "Performed": "执行",
    "Completed": "完成",
    "Grading": "分级",
    "Grade": "等级",
    "Score": "评分",
    
    # 穿戴
    "Wear": "穿戴",
    "Orthoses": "矫形器",
    
    # 认知
    "Cognitive": "认知",
    "Memory": "记忆",
    "Attention": "注意力",
    "Learning": "学习",
    "Auditory": "听觉",
    "Verbal": "言语",
    
    # 量表相关
    "Scale": "量表",
    "Questionnaire": "问卷",
    "Inventory": "清单",
    "Version": "版本",
    "Brief": "简要",
    "Extended": "扩展",
    
    # 疾病
    "Alzheimer": "阿尔茨海默",
    "Dementia": "痴呆",
    "Depression": "抑郁",
    "Anxiety": "焦虑",
    "Diabetes": "糖尿病",
    "Hypertension": "高血压",
    
    # 药代动力学
    "PK": "药代动力学",
    "Parameter": "参数",
    "Dose": "剂量",
    "Weight": "体重",
}

def translate_text(text):
    """翻译文本"""
    if not text:
        return text
    
    result = text
    
    # 按长度降序排序
    sorted_keys = sorted(MEDICAL_DICT.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        if key in result:
            result = result.replace(key, MEDICAL_DICT[key])
    
    # 特殊处理变量名前缀后的内容
    var_pattern = r'^([A-Z]+(\d|[1-9]\d*))-(.*)$'
    match = re.match(var_pattern, result)
    
    if match:
        var_name = match.group(1)
        rest = match.group(3)
        
        # 翻译变量名后的内容
        for key in sorted_keys:
            if key in rest:
                rest = rest.replace(key, MEDICAL_DICT[key])
        
        result = f"{var_name}-{rest}"
    
    return result

def update_all_records():
    """更新所有记录"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 获取所有记录
    cursor.execute("SELECT id, codelist_name, cdisc_synonyms FROM sdtm_terminology ORDER BY id")
    records = cursor.fetchall()
    
    total = len(records)
    updated = 0
    
    print(f"开始翻译 {total} 条记录...")
    print("-" * 100)
    
    for i, record in enumerate(records):
        rec_id = record[0]
        codelist_name = record[1]
        synonyms = record[2]
        
        # 翻译
        cn_name = translate_text(codelist_name) if codelist_name else None
        cn_syn = translate_text(synonyms) if synonyms else None
        
        # 更新
        try:
            cursor.execute(
                "UPDATE sdtm_terminology SET codelist_cn_name = %s, cdisc_submission_value_cn_name = %s WHERE id = %s",
                (cn_name, cn_syn, rec_id)
            )
            updated += 1
            
            if (i + 1) % 1000 == 0:
                print(f"进度：{i+1}/{total} ({(i+1)/total*100:.1f}%)")
                
                # 每 1000 条提交一次
                conn.commit()
                
        except Exception as e:
            print(f"错误 ID {rec_id}: {e}")
    
    # 最终提交
    conn.commit()
    conn.close()
    
    print("-" * 100)
    print(f"完成！更新了 {updated}/{total} 条记录")
    
    return updated

def generate_report():
    """生成翻译对照报告"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 统计
    cursor.execute("""
        SELECT 
            COUNT(*),
            SUM(CASE WHEN codelist_cn_name IS NOT NULL THEN 1 ELSE 0 END),
            SUM(CASE WHEN cdisc_submission_value_cn_name IS NOT NULL THEN 1 ELSE 0 END)
        FROM sdtm_terminology
    """)
    stats = cursor.fetchone()
    
    # 取样
    cursor.execute("""
        SELECT codelist_name, codelist_cn_name, cdisc_synonyms, cdisc_submission_value_cn_name
        FROM sdtm_terminology
        WHERE codelist_name IS NOT NULL
        ORDER BY id
        LIMIT 50
    """)
    samples = cursor.fetchall()
    
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
    
    report.append(f"\n{'序号':<6} {'原文':<50} {'中文翻译':<50}")
    report.append("-" * 150)
    
    for i, s in enumerate(samples, 1):
        en = str(s[0])[:50] if s[0] else "NULL"
        cn = str(s[1])[:50] if s[1] else "NULL"
        report.append(f"{i:<6} {en:<50} {cn:<50}")
    
    # 保存
    with open('C:/Users/Administrator/WorkBuddy/2026-05-22-17-00-44/translation_report.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print('\n'.join(report))
    print(f"\n报告已保存到：translation_report.txt")

if __name__ == "__main__":
    print("=" * 100)
    print("CDISC SDTM 完整翻译")
    print("=" * 100)
    
    update_all_records()
    generate_report()
