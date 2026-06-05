#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据已知章节页码提取 - 基于目录解析
"""

import fitz
import os
import json
import re

def parse_toc(toc):
    """解析 PyMuPDF 的目录 - 格式为 [页码，标题字符串，未知字段]"""
    chapters = []
    
    for item in toc:
        try:
            page_num = item[0]
            title = item[1]
            
            # 匹配 "数字 + 空格 + 英文标题" 格式
            match = re.match(r'^(\d+)\s+([A-Za-z].*)', title)
            if match:
                chapter_num = int(match.group(1))
                chapter_title = match.group(2)
                chapters.append({
                    'num': chapter_num,
                    'title': chapter_title,
                    'page': page_num
                })
        except:
            continue
    
    return chapters

def main():
    pdf_path = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\SDTMIG_v3.4-FINAL_2022-07-21.pdf'
    output_dir = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\chapters_final'
    
    os.makedirs(output_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    
    print(f"=" * 70)
    print(f"CDISC SDTM Implementation Guide v3.4 全文档提取")
    print(f"=" * 70)
    print(f"PDF 总页数：{len(doc)}")
    print()
    
    # 获取目录
    toc = doc.get_toc()
    chapters = parse_toc(toc)
    
    print(f"找到 {len(chapters)} 个主要章节:")
    print("-" * 70)
    for ch in chapters:
        print(f"  第{ch['num']}章：{ch['title'][:50]} (第{ch['page']}页开始)")
    print()
    
    # 提取每个章节
    tasks = []
    total_chars = 0
    
    for i, chapter in enumerate(chapters):
        start_page = chapter['page']
        
        # 确定结束页
        if i + 1 < len(chapters):
            end_page = chapters[i + 1]['page'] - 1
        else:
            end_page = len(doc)
        
        page_count = end_page - start_page + 1
        
        print(f"提取 第{chapter['num']}章：{chapter['title'][:40]}...")
        print(f"  范围：第{start_page}-{end_page}页 ({page_count}页)", end=" ")
        
        try:
            # 提取文本
            all_text = []
            char_count = 0
            
            for page_num in range(start_page - 1, min(end_page, len(doc))):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    all_text.append(f"\n{'='*60}\n第{page_num + 1}页\n{'='*60}\n{text}")
                    char_count += len(text)
            
            # 保存文件
            safe_title = re.sub(r'[^\w]', '_', chapter['title'][:40])
            filename = f"Chapter{chapter['num']:02d}_{safe_title}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(all_text))
            
            file_size = os.path.getsize(filepath)
            total_chars += char_count
            
            print(f"✅ {file_size/1024:.1f} KB, {char_count/1000:.1f}K 字符")
            
            tasks.append({
                'chapter': chapter['num'],
                'title': chapter['title'],
                'pages': f"{start_page}-{end_page}",
                'page_count': page_count,
                'file': filepath,
                'size_kb': round(file_size/1024, 1),
                'char_count': char_count,
                'status': 'success'
            })
            
        except Exception as e:
            print(f"❌ 错误：{e}")
            tasks.append({
                'chapter': chapter['num'],
                'title': chapter['title'],
                'status': 'failed',
                'error': str(e)
            })
    
    doc.close()
    
    # 保存任务列表
    tasks_json = os.path.join(output_dir, 'translation_tasks.json')
    with open(tasks_json, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    # 输出汇总
    print()
    print("=" * 70)
    print("提取完成!")
    print("=" * 70)
    
    success_tasks = [t for t in tasks if t['status'] == 'success']
    total_pages = sum(t['page_count'] for t in success_tasks)
    total_size = sum(t.get('size_kb', 0) for t in success_tasks)
    total_chars_display = sum(t.get('char_count', 0) for t in success_tasks)
    
    print(f"✓ 成功：{len(success_tasks)}/{len(tasks)} 个章节")
    print(f"✓ 总页数：{total_pages} 页")
    print(f"✓ 总大小：{total_size:.1f} KB ({total_size/1024:.1f} MB)")
    print(f"✓ 总字符：{total_chars_display/1000:.1f}K 字符 ({total_chars_display/10000:.1f} 万字符)")
    print()
    print(f"输出目录：{output_dir}")
    print("=" * 70)

if __name__ == '__main__':
    main()
