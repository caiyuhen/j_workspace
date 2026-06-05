#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDISC SDTM 术语批量翻译和数据库更新脚本
"""

import json
import pymysql
from cdisc_translator import translate_codelist_name, translate_synonym

# 数据库配置
DB_CONFIG = {
    'host': 'rm-2ze99d2eaw127x8i6yo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'jdms',
    'password': 'jdjd@12358',
    'database': 'ohms',
    'charset': 'utf8mb4'
}

def load_data(filepath: str) -> list:
    """加载导出的 JSON 数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def translate_batch(data: list, batch_size: int = 1000) -> int:
    """批量翻译并更新数据库"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    total_updated = 0
    total_records = len(data)
    
    print(f"开始翻译并更新 {total_records} 条记录...")
    print("-" * 80)
    
    for start_idx in range(0, total_records, batch_size):
        end_idx = min(start_idx + batch_size, total_records)
        batch = data[start_idx:end_idx]
        
        updates = []
        for item in batch:
            record_id = item['id']
            codelist_name = item.get('codelist_name')
            cdisc_synonyms = item.get('cdisc_synonyms')
            
            # 翻译
            codelist_cn = translate_codelist_name(codelist_name) if codelist_name else None
            synonym_cn = translate_synonym(cdisc_synonyms) if cdisc_synonyms else None
            
            # 构建更新语句
            if codelist_cn or synonym_cn:
                values = []
                conditions = []
                
                if codelist_cn is not None:
                    conditions.append("codelist_cn_name = %s")
                    values.append(codelist_cn)
                
                if synonym_cn is not None:
                    conditions.append("cdisc_submission_value_cn_name = %s")
                    values.append(synonym_cn)
                
                if conditions:
                    values.append(record_id)
                    update_sql = f"UPDATE sdtm_terminology SET {', '.join(conditions)} WHERE id = %s"
                    updates.append((update_sql, values))
        
        # 执行批量更新
        for update_sql, values in updates:
            try:
                cursor.execute(update_sql, values)
                total_updated += cursor.rowcount
            except Exception as e:
                print(f"更新记录失败：{e}")
        
        # 提交批次
        conn.commit()
        
        progress = (end_idx / total_records) * 100
        print(f"进度：{end_idx}/{total_records} ({progress:.1f}%) - 已更新：{total_updated}")
    
    cursor.close()
    conn.close()
    
    print("-" * 80)
    print(f"完成！共更新 {total_updated} 条记录")
    return total_updated

def verify_translation(filepath: str) -> dict:
    """验证翻译结果"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 统计翻译完成情况
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN codelist_cn_name IS NOT NULL AND codelist_cn_name != '' THEN 1 ELSE 0 END) as codelist_translated,
            SUM(CASE WHEN cdisc_submission_value_cn_name IS NOT NULL AND cdisc_submission_value_cn_name != '' THEN 1 ELSE 0 END) as synonym_translated
        FROM sdtm_terminology
    """)
    
    result = cursor.fetchone()
    stats = {
        'total': result[0],
        'codelist_translated': result[1],
        'synonym_translated': result[2]
    }
    
    # 抽样查看翻译结果
    cursor.execute("""
        SELECT 
            codelist_name,
            codelist_cn_name,
            cdisc_synonyms,
            cdisc_submission_value_cn_name
        FROM sdtm_terminology
        WHERE codelist_cn_name IS NOT NULL
        LIMIT 10
    """)
    
    samples = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return stats, samples

if __name__ == "__main__":
    print("=" * 80)
    print("CDISC SDTM 术语翻译和数据库更新工具")
    print("=" * 80)
    print()
    
    # 加载数据
    print("正在加载数据...")
    data = load_data('C:/Users/Administrator/WorkBuddy/2026-05-22-17-00-44/sdtm_terminology_export.json')
    print(f"已加载 {len(data)} 条记录")
    print()
    
    # 执行翻译和更新
    updated_count = translate_batch(data)
    print()
    
    # 验证结果
    print("正在验证翻译结果...")
    stats, samples = verify_translation('C:/Users/Administrator/WorkBuddy/2026-05-22-17-00-44/sdtm_terminology_export.json')
    
    print(f"\n翻译统计:")
    print(f"  总记录数：{stats['total']}")
    print(f"  已翻译 codelist_name: {stats['codelist_translated']} ({stats['codelist_translated']/stats['total']*100:.1f}%)")
    print(f"  已翻译 cdisc_synonyms: {stats['synonym_translated']} ({stats['synonym_translated']/stats['total']*100:.1f}%)")
    
    print(f"\n翻译样例:")
    print("-" * 80)
    for sample in samples[:5]:
        print(f"原文 (codelist_name): {sample[0]}")
        print(f"翻译 (codelist_cn_name): {sample[1]}")
        if sample[2]:
            print(f"原文 (cdisc_synonyms): {sample[2]}")
            print(f"翻译 (cdisc_submission_value_cn_name): {sample[3]}")
        print("-" * 80)
