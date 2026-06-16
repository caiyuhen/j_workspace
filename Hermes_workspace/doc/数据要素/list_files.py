#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

DIR = r'D:\workspace\Hermes_workspace\doc\数据要素'
print(f'Working dir: {DIR}')
print()

if not os.path.isdir(DIR):
    print('DIR NOT FOUND!')
    # Try alternative
    alt = r'D:\workspace\Hermes_workspace\doc\数据要素'.replace('数据要素','数据要素')
    if os.path.isdir(alt):
        print(f'Alt found: {alt}')
        DIR = alt

print('All files:')
for f in sorted(os.listdir(DIR)):
    sz = os.path.getsize(os.path.join(DIR, f))
    print(f'  {f} ({sz/1024:.1f} KB)')

print()
# Find any docx
for f in os.listdir(DIR):
    if f.endswith('.docx'):
        print(f'FOUND DOCX: {f}')
