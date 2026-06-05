#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最终翻译进度检查"""

import pymysql
from collections import Counter

# 数据库连接配置
db_config = {
    'host': 'rm-2ze99d2eaw127x8i6yo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'jdms',
    'password': 'jdjd@12358',
    'database': 'ohms',
    'charset': 'utf8mb4'
}

# 连接数据库
conn = pymysql.connect(**db_config)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# 查询总体统计
query = """
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN codelist_cn_name IS NOT NULL AND codelist_cn_name != '' THEN 1 ELSE 0 END) as codelist_translated,
    SUM(CASE WHEN cdisc_submission_value_cn_name IS NOT NULL AND cdisc_submission_value_cn_name != '' THEN 1 ELSE 0 END) as cdisc_translated
FROM sdtm_terminology
"""

cursor.execute(query)
result = cursor.fetchone()

print('=' * 80)
print('CDISC SDTM 翻译最终统计')
print('=' * 80)
print(f'总记录数：{result["total"]:,}')
print(f'codelist_name 翻译：{result["codelist_translated"]:,} ({result["codelist_translated"]/result["total"]*100:.2f}%)')
print(f'cdisc_synonyms 翻译：{result["cdisc_translated"]:,} ({result["cdisc_translated"]/result["total"]*100:.2f}%)')
print(f'cdisc_synonyms 未翻译：{result["total"] - result["cdisc_translated"]:,} ({(result["total"] - result["cdisc_translated"])/result["total"]*100:.2f}%)')

# 查询未翻译的类别分布
print('\n' + '=' * 80)
print('剩余未翻译类别分布 (Top 20)')
print('=' * 80)

query2 = """
SELECT codelist_name, COUNT(*) as count
FROM sdtm_terminology
WHERE cdisc_submission_value_cn_name IS NULL OR cdisc_submission_value_cn_name = ''
GROUP BY codelist_name
ORDER BY count DESC
LIMIT 20
"""

cursor.execute(query2)
untranslated_categories = cursor.fetchall()

print('类别' + '未翻译数'.rjust(10))
print('-' * 80)
for row in untranslated_categories:
    print(row["codelist_name"].ljust(60) + str(row["count"]).rjust(10))

# 翻译样例
print('\n' + '=' * 80)
print('最新翻译样例')
print('=' * 80)

query3 = """
SELECT codelist_name, codelist_cn_name, cdisc_submission_value, cdisc_submission_value_cn_name
FROM sdtm_terminology
WHERE cdisc_submission_value_cn_name IS NOT NULL 
  AND cdisc_submission_value_cn_name != ''
  AND cdisc_submission_value != cdisc_submission_value_cn_name
LIMIT 30
"""

cursor.execute(query3)
samples = cursor.fetchall()

for i, row in enumerate(samples, 1):
    category = row['codelist_name'][:40]
    original = row['cdisc_submission_value'][:30]
    translated = row['cdisc_submission_value_cn_name'][:20]
    print(f'{i:2d}. {category:<40s} "{original:<30s}" -> "{translated}"')

cursor.close()
conn.close()
