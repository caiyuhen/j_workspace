#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试目录解析"""

import json

with open(r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\SDTMIG_structure.json', 'r', encoding='utf-8') as f:
    structure = json.load(f)

toc = structure['toc']

print(f"总页数：{structure['total_pages']}")
print(f"目录项数：{len(toc)}")
print()
print("前 10 项目录:")
for i, item in enumerate(toc[:10]):
    print(f"{i}: 页码={item[0]}, 标题='{item[1]}', 级别={item[2]}")
