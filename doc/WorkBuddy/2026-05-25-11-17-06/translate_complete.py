#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDISC SDTM Implementation Guide v3.4 全文翻译
分块读取、分块翻译、整合输出
"""

import os
import re
import json

def read_full_text():
    """读取完整文本"""
    filepath = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\chapters\Chapter10_Appendices.txt'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def split_by_pages(text):
    """按页码分割文本"""
    pattern = r'--- 第 (\d+) 页 ---'
    pages = re.split(pattern, text)
    
    result = {}
    i = 1
    while i < len(pages):
        if i + 1 < len(pages):
            page_num = pages[i]
            content = pages[i + 1].strip()
            result[int(page_num)] = content
            i += 2
        else:
            break
    
    return result

def main():
    print("=" * 70)
    print("CDISC SDTM Implementation Guide v3.4 全文翻译准备")
    print("=" * 70)
    
    # 读取全文
    print("读取原文...")
    full_text = read_full_text()
    print(f"✓ 原文总大小：{len(full_text) / 1000:.1f} KB ({len(full_text) / 10000:.1f}万字符)")
    
    # 分割页面
    print("分割页面...")
    pages = split_by_pages(full_text)
    print(f"✓ 共 {len(pages)} 页")
    
    # 统计页数分布
    total_chars = sum(len(p) for p in pages.values())
    avg_chars = total_chars / len(pages) if pages else 0
    
    print(f"✓ 总字符：{total_chars / 10000:.1f} 万字符")
    print(f"✓ 平均每页：{avg_chars / 1000:.1f}K 字符")
    
    # 保存统计信息
    stats = {
        'total_pages': len(pages),
        'total_chars': total_chars,
        'avg_chars_per_page': avg_chars,
        'page_range': f"1-{max(pages.keys()) if pages else 0}"
    }
    
    stats_file = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\translation_stats.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 70)
    print("翻译策略:")
    print("=" * 70)
    print("由于文档较大，将采用分批翻译:")
    print("  - 批次 1: 第 1-50 页 (引言、基础概念)")
    print("  - 批次 2: 第 51-150 页 (标准格式、域模型假设)")
    print("  - 批次 3: 第 151-250 页 (专用域、通用观察类)")
    print("  - 批次 4: 第 251-350 页 (各域详细规格)")
    print("  - 批次 5: 第 351-461 页 (试验设计、关系表示、附录)")
    print()
    print(f"输出目录：C:\\Users\\Administrator\\WorkBuddy\\2026-05-25-11-17-06\\")
    print("=" * 70)

if __name__ == '__main__':
    main()
