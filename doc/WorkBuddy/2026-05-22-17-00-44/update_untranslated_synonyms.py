#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量翻译并更新未翻译的 cdisc_synonyms
"""
import pymysql
from extended_medical_translator import ExtendedMedicalTranslator

# 数据库配置
db_config = {
    'host': 'rm-2ze99d2eaw127x8i6yo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'jdms',
    'password': 'jdjd@12358',
    'database': 'ohms',
    'charset': 'utf8mb4'
}

def update_untranslated_batch(translator, batch_size=1000):
    """分批更新未翻译的记录"""
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # 查询未翻译的记录总数
        cursor.execute("""
            SELECT COUNT(*) FROM sdtm_terminology
            WHERE cdisc_submission_value_cn_name IS NULL OR cdisc_submission_value_cn_name = ''
        """)
        total_count = cursor.fetchone()[0]
        print(f"需要翻译的记录总数：{total_count:,}")
        
        translated_count = 0
        unchanged_count = 0
        
        # 分批处理 - 使用 codelist_name 和 cdisc_submission_value 作为唯一标识
        offset = 0
        while offset < total_count:
            # 查询一批未翻译的记录
            cursor.execute("""
                SELECT 
                    codelist_name,
                    cdisc_submission_value,
                    cdisc_synonyms
                FROM sdtm_terminology
                WHERE cdisc_submission_value_cn_name IS NULL OR cdisc_submission_value_cn_name = ''
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            rows = cursor.fetchall()
            print(f"\n处理第 {offset//batch_size + 1} 批，共 {len(rows)} 条记录")
            
            for row in rows:
                codelist_name, cdisc_value, cdisc_synonyms = row
                
                # 使用 cdisc_submission_value 进行翻译
                term_to_translate = cdisc_value or cdisc_synonyms
                
                if term_to_translate:
                    # 翻译
                    translated = translator.translate(term_to_translate, codelist_name)
                    
                    # 构建 WHERE 条件
                    if cdisc_value:
                        # 使用 codelist_name 和 cdisc_submission_value 作为唯一条件
                        cursor.execute("""
                            UPDATE sdtm_terminology
                            SET cdisc_submission_value_cn_name = %s
                            WHERE codelist_name = %s 
                            AND cdisc_submission_value = %s
                            AND (cdisc_submission_value_cn_name IS NULL OR cdisc_submission_value_cn_name = '')
                        """, (translated, codelist_name, cdisc_value))
                    else:
                        # 只有 cdisc_synonyms 的情况
                        cursor.execute("""
                            UPDATE sdtm_terminology
                            SET cdisc_submission_value_cn_name = %s
                            WHERE codelist_name = %s 
                            AND cdisc_synonyms = %s
                            AND (cdisc_submission_value_cn_name IS NULL OR cdisc_submission_value_cn_name = '')
                        """, (translated, codelist_name, cdisc_synonyms))
                    
                    if translated and translated != term_to_translate:
                        translated_count += 1
                    else:
                        unchanged_count += 1
            
            # 提交批次
            conn.commit()
            offset += batch_size
            print(f"✓ 批次提交完成，累计翻译：{translated_count:,} 条，保留原术语：{unchanged_count:,} 条")
        
        print(f"\n{'='*60}")
        print(f"批量更新完成！")
        print(f"  新翻译：{translated_count:,} 条")
        print(f"  保留原术语：{unchanged_count:,} 条")
        print(f"  总计处理：{translated_count + unchanged_count:,} 条")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"错误：{e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def verify_translation():
    """验证翻译结果"""
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 统计翻译情况
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN cdisc_submission_value_cn_name IS NOT NULL AND cdisc_submission_value_cn_name != '' THEN 1 ELSE 0 END) as translated
            FROM sdtm_terminology
        """)
        stats = cursor.fetchone()
        
        total = stats['total']
        translated = stats['translated']
        rate = translated/total*100 if total > 0 else 0
        
        print(f"\n【翻译统计】")
        print(f"  总记录数：{total:,}")
        print(f"  已翻译：{translated:,} ({rate:.1f}%)")
        print(f"  未翻译：{total-translated:,} ({100-rate:.1f}%)")
        
        # 按类别统计
        print(f"\n【按类别统计】")
        cursor.execute("""
            SELECT 
                codelist_name,
                COUNT(*) as total,
                SUM(CASE WHEN cdisc_submission_value_cn_name IS NOT NULL AND cdisc_submission_value_cn_name != '' THEN 1 ELSE 0 END) as translated,
                SUM(CASE WHEN cdisc_submission_value_cn_name IS NULL OR cdisc_submission_value_cn_name = '' THEN 1 ELSE 0 END) as not_translated
            FROM sdtm_terminology
            GROUP BY codelist_name
            ORDER BY not_translated DESC
            LIMIT 20
        """)
        
        print(f"{'类别名称':<50} {'总数':>10} {'已翻译':>10} {'未翻译':>10}")
        print("-" * 80)
        
        for row in cursor.fetchall():
            name = row['codelist_name'][:48] if len(row['codelist_name']) > 48 else row['codelist_name']
            total_cnt = row['total']
            translated_cnt = row['translated']
            not_translated_cnt = row['not_translated']
            print(f"{name:<50} {total_cnt:>10,} {translated_cnt:>10,} {not_translated_cnt:>10,}")
        
        # 显示翻译样例
        print(f"\n【翻译样例 - 新增翻译】")
        cursor.execute("""
            SELECT 
                codelist_name,
                cdisc_submission_value,
                cdisc_submission_value_cn_name
            FROM sdtm_terminology
            WHERE cdisc_submission_value_cn_name IS NOT NULL 
            AND cdisc_submission_value IS NOT NULL
            AND (codelist_name LIKE '%Microorganism%' 
                 OR codelist_name LIKE '%Anatomical%' 
                 OR codelist_name LIKE '%PK Unit%')
            LIMIT 20
        """)
        
        for row in cursor.fetchall():
            category = row['codelist_name'][:30]
            en = row['cdisc_submission_value'][:25] if row['cdisc_submission_value'] else ''
            cn = row['cdisc_submission_value_cn_name'][:25] if row['cdisc_submission_value_cn_name'] else ''
            print(f"  [{category:<30}] {en:<25} -> {cn}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("开始批量翻译未翻译的 cdisc_synonyms")
    print("="*60)
    
    translator = ExtendedMedicalTranslator()
    
    # 执行批量翻译
    update_untranslated_batch(translator, batch_size=1000)
    
    # 验证结果
    verify_translation()
    
    print("\n✅ 任务完成！")
