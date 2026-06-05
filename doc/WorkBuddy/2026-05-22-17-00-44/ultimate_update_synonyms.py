#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
终极批量翻译更新脚本
覆盖剩余 1,000 条未翻译术语
"""

import pymysql
import json
from datetime import datetime
import sys

# 导入终极翻译器
sys.path.insert(0, 'C:/Users/Administrator/WorkBuddy/2026-05-22-17-00-44')
from ultimate_medical_translator import UltimateMedicalTranslator

# 数据库连接配置
db_config = {
    'host': 'rm-2ze99d2eaw127x8i6yo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'jdms',
    'password': 'jdjd@12358',
    'database': 'ohms',
    'charset': 'utf8mb4'
}

def main():
    print('=' * 80)
    print('CDISC SDTM 终极翻译更新')
    print('=' * 80)
    print(f'开始时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 初始化翻译器
    translator = UltimateMedicalTranslator()
    
    # 连接数据库
    print('\n正在连接数据库...')
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # 查询未翻译的记录
        print('查询未翻译记录...')
        query = """
        SELECT codelist_name, cdisc_submission_value 
        FROM sdtm_terminology 
        WHERE cdisc_submission_value_cn_name IS NULL
           OR cdisc_submission_value_cn_name = ''
        """
        
        cursor.execute(query)
        untranslated = cursor.fetchall()
        
        total_count = len(untranslated)
        print(f'未翻译记录总数：{total_count}')
        
        if total_count == 0:
            print('所有记录已翻译完成！')
            return
        
        # 批量翻译和更新
        translated_count = 0
        skipped_count = 0
        failed_count = 0
        
        # 统计按类别翻译情况
        category_stats = {}
        translation_samples = {}
        
        batch_size = 500
        # 使用 codelist_name 和 cdisc_submission_value 组合作为唯一标识
        update_sql = "UPDATE sdtm_terminology SET cdisc_submission_value_cn_name = %s WHERE codelist_name = %s AND cdisc_submission_value = %s"
        
        print(f'\n开始翻译 {total_count} 条记录...')
        print('-' * 80)
        
        for i, row in enumerate(untranslated):
            codelist_name, cdisc_value = row
            
            # 翻译术语
            translated = translator.translate(cdisc_value, codelist_name)
            
            # 判断是否翻译成功
            if translated != cdisc_value:
                translated_count += 1
                try:
                    cursor.execute(update_sql, (translated, codelist_name, cdisc_value))
                    
                    # 统计按类别翻译
                    if codelist_name not in category_stats:
                        category_stats[codelist_name] = {'translated': 0, 'skipped': 0}
                    category_stats[codelist_name]['translated'] += 1
                    
                    # 保存翻译样例
                    if codelist_name not in translation_samples or len(translation_samples[codelist_name]) < 5:
                        if codelist_name not in translation_samples:
                            translation_samples[codelist_name] = []
                        translation_samples[codelist_name].append({
                            'original': cdisc_value,
                            'translated': translated
                        })
                        
                except Exception as e:
                    failed_count += 1
                    if failed_count <= 5:
                        print(f'更新失败 {term_id}: {str(e)}')
            else:
                skipped_count += 1
                if codelist_name not in category_stats:
                    category_stats[codelist_name] = {'translated': 0, 'skipped': 0}
                category_stats[codelist_name]['skipped'] += 1
            
            # 每批提交一次
            if (i + 1) % batch_size == 0:
                conn.commit()
                print(f'进度：{i + 1}/{total_count} - 已翻译：{translated_count} - 跳过：{skipped_count}')
        
        # 提交最后一批
        conn.commit()
        
        # 打印最终统计
        print('\n' + '=' * 80)
        print('翻译完成统计')
        print('=' * 80)
        print(f'总记录数：{total_count}')
        print(f'新增翻译：{translated_count} ({translated_count/total_count*100:.2f}%)')
        print(f'跳过（无法翻译）: {skipped_count} ({skipped_count/total_count*100:.2f}%)')
        print(f'更新失败：{failed_count}')
        
        # 按类别统计
        print('\n' + '=' * 80)
        print('按类别翻译统计')
        print('=' * 80)
        for category, stats in sorted(category_stats.items(), key=lambda x: x[1]['translated'], reverse=True):
            total = stats['translated'] + stats['skipped']
            rate = stats['translated'] / total * 100 if total > 0 else 0
            print(f'{category:50s} 翻译：{stats["translated"]:4d}  跳过：{stats["skipped"]:4d}  成功率：{rate:6.2f}%')
        
        # 翻译样例
        print('\n' + '=' * 80)
        print('翻译样例（Top 15 类别）')
        print('=' * 80)
        for category, samples in list(translation_samples.items())[:15]:
            print(f'\n{category}:')
            for sample in samples[:3]:
                print(f'  "{sample["original"]}" -> "{sample["translated"]}"')
        
        # 生成详细报告
        report_content = generate_report(
            total_count, translated_count, skipped_count, failed_count,
            category_stats, translation_samples
        )
        
        report_path = 'C:/Users/Administrator/WorkBuddy/2026-05-22-17-00-44/cdisc_translation_ultimate_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f'\n详细报告已保存到：{report_path}')
        
    except Exception as e:
        conn.rollback()
        print(f'\n发生错误：{str(e)}')
        import traceback
        traceback.print_exc()
        
    finally:
        cursor.close()
        conn.close()
        print(f'\n结束时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

def generate_report(total, translated, skipped, failed, category_stats, samples):
    """生成详细报告"""
    
    report = []
    report.append('=' * 80)
    report.append('CDISC SDTM 终极翻译详细报告')
    report.append('=' * 80)
    report.append(f'报告生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 整体统计
    report.append('\n' + '=' * 80)
    report.append('整体统计')
    report.append('=' * 80)
    report.append(f'未翻译记录总数：{total}')
    report.append(f'新增翻译：{translated} ({translated/total*100:.2f}%)')
    report.append(f'跳过（无法翻译）: {skipped} ({skipped/total*100:.2f}%)')
    report.append(f'更新失败：{failed}')
    
    # 按类别统计
    report.append('\n' + '=' * 80)
    report.append('按类别翻译统计（按翻译数量降序）')
    report.append('=' * 80)
    
    for category, stats in sorted(category_stats.items(), key=lambda x: x[1]['translated'], reverse=True):
        total_cat = stats['translated'] + stats['skipped']
        rate = stats['translated'] / total_cat * 100 if total_cat > 0 else 0
        report.append(f'{category:50s}')
        report.append(f'  翻译：{stats["translated"]:4d}  跳过：{stats["skipped"]:4d}  成功率：{rate:6.2f}%')
    
    # 翻译样例
    report.append('\n' + '=' * 80)
    report.append('翻译样例')
    report.append('=' * 80)
    
    for category, category_samples in list(samples.items())[:20]:
        report.append(f'\n{category}:')
        for sample in category_samples[:5]:
            report.append(f'  "{sample["original"]}" -> "{sample["translated"]}"')
    
    # 建议
    report.append('\n' + '=' * 80)
    report.append('后续建议')
    report.append('=' * 80)
    
    skipped_categories = [(cat, stats) for cat, stats in category_stats.items() if stats['skipped'] > 0]
    if skipped_categories:
        report.append('以下类别仍有部分未翻译，需要人工审核或补充翻译词典:')
        for cat, stats in sorted(skipped_categories, key=lambda x: x[1]['skipped'], reverse=True)[:10]:
            report.append(f'  - {cat}: {stats["skipped"]} 条未翻译')
    
    return '\n'.join(report)

if __name__ == '__main__':
    main()
