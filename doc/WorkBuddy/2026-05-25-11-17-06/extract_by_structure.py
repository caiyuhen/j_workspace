#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于手动定义的章节页码进行提取
从之前解析的结构文件中读取正确页码
"""

import fitz
import os
import json

def main():
    pdf_path = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\SDTMIG_v3.4-FINAL_2022-07-21.pdf'
    structure_path = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\SDTMIG_structure.json'
    output_dir = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\chapters_corrected'
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取结构文件获取正确页码
    with open(structure_path, 'r', encoding='utf-8') as f:
        structure = json.load(f)
    
    toc = structure['toc']
    
    # 提取一级章节 (根据标题格式)
    import re
    chapters = []
    
    for item in toc:
        page_num = item[0]
        title = item[1]  # 第二项是标题
        
        # 匹配 "数字 + 空格 + 英文" 格式
        match = re.match(r'^(\d+)\s+([A-Za-z].*)', title)
        if match:
            chapter_num = int(match.group(1))
            chapter_title = match.group(2)
            
            # 只收集有实际页码 (>=7) 的章节
            if page_num >= 7:
                chapters.append({
                    'num': chapter_num,
                    'title': chapter_title,
                    'page': page_num
                })
    
    print(f"找到 {len(chapters)} 个主要章节:")
    for ch in chapters:
        print(f"  第{ch['num']}章：{ch['title'][:50]} (第{ch['page']}页)")
    print()
    
    # 打开 PDF
    doc = fitz.open(pdf_path)
    print(f"PDF 总页数：{len(doc)}")
    print()
    
    # 提取每个章节
    tasks = []
    
    for i, chapter in enumerate(chapters):
        start_page = chapter['page']
        
        # 确定结束页
        if i + 1 < len(chapters):
            end_page = chapters[i + 1]['page'] - 1
        else:
            end_page = len(doc)
        
        page_count = end_page - start_page + 1
        
        print(f"提取 第{chapter['num']}章：{chapter['title'][:40]}...", end=" ")
        print(f"(第{start_page}-{end_page}页，{page_count}页)")
        
        try:
            all_text = []
            char_count = 0
            
            for page_num in range(start_page - 1, min(end_page, len(doc))):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    all_text.append(f"\n{'='*60}\n第{page_num + 1}页\n{'='*60}\n{text}")
                    char_count += len(text)
            
            # 保存
            safe_title = re.sub(r'[^\w]', '_', chapter['title'][:40])
            filename = f"Chapter{chapter['num']:02d}_{safe_title}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("\n".join(all_text))
            
            file_size = os.path.getsize(filepath)
            
            print(f"  ✅ {file_size/1024:.1f} KB, {char_count/1000:.1f}K 字符")
            
            tasks.append({
                'chapter': chapter['num'],
                'title': chapter['title'],
                'pages': f"{start_page}-{end_page}",
                'page_count': page_count,
                'size_kb': round(file_size/1024, 1),
                'chars': char_count
            })
            
        except Exception as e:
            print(f"  ❌ {e}")
    
    doc.close()
    
    # 保存任务列表
    with open(os.path.join(output_dir, 'tasks.json'), 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    # 汇总
    print()
    print("=" * 70)
    total_pages = sum(t['page_count'] for t in tasks)
    total_size = sum(t['size_kb'] for t in tasks)
    total_chars = sum(t['chars'] for t in tasks)
    
    print(f"✓ 成功提取 {len(tasks)} 个章节")
    print(f"✓ 总页数：{total_pages}")
    print(f"✓ 总大小：{total_size:.1f} KB ({total_size/1024:.1f} MB)")
    print(f"✓ 总字符：{total_chars/10000:.1f} 万字符")
    print("=" * 70)

if __name__ == '__main__':
    main()
