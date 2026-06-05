#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析未翻译数据"""

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

# 查询未翻译的记录
query = """
SELECT codelist_name, cdisc_submission_value 
FROM sdtm_terminology 
WHERE cdisc_submission_value_cn_name IS NULL
   OR cdisc_submission_value_cn_name = ''
LIMIT 2000
"""

cursor.execute(query)
untranslated = cursor.fetchall()

print(f'未翻译总记录数：{len(untranslated)}')

# 统计类别分布
category_count = Counter()
sample_by_category = {}

for record in untranslated:
    category = record.get('codelist_name', 'Unknown')
    value = record.get('cdisc_submission_value', '')
    
    category_count[category] += 1
    
    if category not in sample_by_category:
        sample_by_category[category] = []
    if len(sample_by_category[category]) < 5:
        sample_by_category[category].append(value)

print('\n' + '=' * 80)
print('未翻译 Top 30 类别:')
print('=' * 80)
for cat, count in category_count.most_common(30):
    print(f'{cat:50s} {count}')

print('\n' + '=' * 80)
print('各类别未翻译样例:')
print('=' * 80)
for category, samples in list(sample_by_category.items())[:20]:
    print(f'\n{category}:')
    for sample in samples[:3]:
        print(f'  - {sample}')

cursor.close()
conn.close()
