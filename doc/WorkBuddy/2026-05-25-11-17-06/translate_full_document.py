#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDISC SDTM Implementation Guide v3.4 全文档翻译脚本
分批提取并标记所有章节用于翻译
"""

import json
import fitz  # PyMuPDF
import os
import re

def extract_chapters_by_toc(toc):
    """根据目录提取各章节的页码范围 - 基于标题格式"""
    chapters = []
    
    # 查找所有一级章节 (格式：数字 + 空格+标题，如 "1 Introduction", "2 Fundamentals...")
    chapter_pattern = re.compile(r'^(\d+)\s+([A-Za-z].*)')
    
    chapter_pages = []
    
    for item in toc:
        try:
            page_num = item[0]
            title = item[1]
            
            # 匹配一级章节
            match = chapter_pattern.match(title)
            if match:
                chapter_num = int(match.group(1))
                chapter_title = match.group(2)
                chapter_pages.append({
                    'chapter_num': chapter_num,
                    'title': chapter_title,
                    'page': page_num
                })
        except Exception as e:
            continue
    
    # 构建章节范围
    for i, chapter in enumerate(chapter_pages):
        start_page = chapter['page']
        
        # 结束页是下一个章节的开始页 -1
        if i + 1 < len(chapter_pages):
            end_page = chapter_pages[i + 1]['page'] - 1
        else:
            end_page = 461  # 最后一页
        
        chapters.append({
            'chapter_num': chapter['chapter_num'],
            'title': chapter['title'],
            'start_page': start_page,
            'end_page': end_page,
            'page_count': end_page - start_page + 1
        })
    
    return chapters

def extract_text_by_range(pdf_path, start_page, end_page):
    """提取指定页码范围的文本"""
    doc = fitz.open(pdf_path)
    texts = []
    
    print(f"  提取第 {start_page} - {end_page} 页...")
    
    for page_num in range(start_page - 1, min(end_page, len(doc))):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            texts.append({
                'page': page_num + 1,
                'content': text
            })
    
    doc.close()
    return texts

def main():
    pdf_path = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\SDTMIG_v3.4-FINAL_2022-07-21.pdf'
    structure_path = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\SDTMIG_structure.json'
    output_dir = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\chapters'
    
    # 创建章节目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取目录结构
    with open(structure_path, 'r', encoding='utf-8') as f:
        structure = json.load(f)
    
    toc = structure['toc']
    total_pages = structure['total_pages']
    
    print(f"=" * 60)
    print(f"CDISC SDTM Implementation Guide v3.4 章节提取")
    print(f"=" * 60)
    print(f"总页数：{total_pages}")
    print(f"目录项数：{len(toc)}")
    print()
    
    # 提取主要章节
    chapters = extract_chapters_by_toc(toc)
    
    print(f"发现 {len(chapters)} 个主要章节")
    print()
    
    # 为每个章节创建提取任务
    tasks = []
    for chapter in chapters:
        task = {
            'chapter_number': chapter['chapter_num'],
            'title': chapter['title'],
            'start_page': chapter['start_page'],
            'end_page': chapter['end_page'],
            'page_count': chapter['page_count']
        }
        tasks.append(task)
        
        # 提取文本
        try:
            texts = extract_text_by_range(pdf_path, chapter['start_page'], chapter['end_page'])
            
            # 保存为文件
            safe_title = chapter['title'][:50].replace('/', '_').replace('\\', '_').replace(':', '_').replace(' ', '_')
            filename = f"Chapter{chapter['chapter_num']:02d}_{safe_title}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for text_info in texts:
                    f.write(f"\n--- 第{text_info['page']}页 ---\n")
                    f.write(text_info['content'])
            
            task['file'] = filepath
            task['status'] = 'extracted'
            
        except Exception as e:
            print(f"  ❌ 提取失败：{e}")
            task['status'] = 'failed'
            task['error'] = str(e)
    
    # 保存任务列表
    tasks_path = os.path.join(output_dir, 'translation_tasks.json')
    with open(tasks_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    # 输出统计
    print("\n" + "=" * 60)
    print("章节提取完成")
    print("=" * 60)
    
    success_count = sum(1 for t in tasks if t['status'] == 'extracted')
    failed_count = sum(1 for t in tasks if t['status'] == 'failed')
    
    print(f"成功提取：{success_count}/{len(tasks)} 个章节")
    print(f"失败：{failed_count} 个章节")
    print()
    
    print("提取的章节列表:")
    print("-" * 60)
    for task in tasks:
        status_icon = "✅" if task['status'] == 'extracted' else "❌"
        title_short = task['title'][:50] + "..." if len(task['title']) > 50 else task['title']
        print(f"{status_icon} 第{task['chapter_number']}章：{title_short}")
        print(f"    页数：{task['page_count']}页 (第{task['start_page']}-{task['end_page']}页)")
        if task['status'] == 'extracted':
            file_size = os.path.getsize(task['file']) / 1024
            print(f"    文件：{file_size:.1f} KB")
    
    return tasks

if __name__ == '__main__':
    tasks = main()
    print("\n" + "=" * 60)
    print(f"章节提取完成！共 {len(tasks)} 个章节准备翻译")
    print("=" * 60)
