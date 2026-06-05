#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接使用 PyMuPDF 的 get_toc() 功能提取章节
"""

import fitz  # PyMuPDF
import os
import json

def main():
    pdf_path = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\SDTMIG_v3.4-FINAL_2022-07-21.pdf'
    output_dir = r'C:\Users\Administrator\WorkBuddy\2026-05-25-11-17-06\chapters_v2'
    
    os.makedirs(output_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    
    print(f"=" * 60)
    print(f"CDISC SDTM Implementation Guide v3.4 章节提取 v2")
    print(f"=" * 60)
    print(f"PDF 总页数：{len(doc)}")
    print()
    
    # 使用 PyMuPDF 的 get_toc() 方法
    toc = doc.get_toc()
    
    print(f"目录项数：{len(toc)}")
    print()
    print("目录结构示例 (前 15 项):")
    for i, item in enumerate(toc[:15]):
        print(f"  {i}: 页码={item[0]}, 级别={item[1]}, 标题='{item[2]}'")
    print()
    
    # 提取一级章节 (级别=1)
    chapters = []
    for item in toc:
        page_num, level, title = item[0], item[1], item[2]
        
        # 只处理级别 1 的章节，并跳过封面和目录
        if level == 1 and not any(x in title for x in ['Contents', 'SDTM Implementation Guide']):
            # 匹配 "数字 + 空格 + 标题" 格式
            if title[0].isdigit():
                chapters.append({
                    'page': page_num,
                    'title': title
                })
    
    print(f"找到 {len(chapters)} 个一级章节")
    print()
    
    # 为每个章节提取文本
    tasks = []
    for i, chapter in enumerate(chapters):
        start_page = chapter['page']
        
        # 确定结束页
        if i + 1 < len(chapters):
            end_page = chapters[i + 1]['page'] - 1
        else:
            end_page = len(doc)  # 最后一页
        
        page_count = end_page - start_page + 1
        
        print(f"处理第{chapter['page']}章：{chapter['title'][:50]}...")
        print(f"  范围：{start_page} - {end_page} 页 ({page_count}页)")
        
        # 提取文本
        try:
            texts = []
            for page_num in range(start_page - 1, end_page):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    texts.append({
                        'page': page_num + 1,
                        'content': text
                    })
            
            # 保存文件
            safe_title = chapter['title'][:50].replace('/', '_').replace('\\', '_').replace(':', '_').replace(' ', '_')
            filename = f"Chapter{start_page:02d}_{safe_title}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for text_info in texts:
                    f.write(f"\n--- 第{text_info['page']}页 ---\n")
                    f.write(text_info['content'])
            
            file_size = os.path.getsize(filepath) / 1024
            print(f"  ✅ 已保存：{file_size:.1f} KB")
            
            tasks.append({
                'chapter': start_page,
                'title': chapter['title'],
                'pages': f"{start_page}-{end_page}",
                'page_count': page_count,
                'file': filepath,
                'size_kb': file_size,
                'status': 'extracted'
            })
            
        except Exception as e:
            print(f"  ❌ 错误：{e}")
            tasks.append({
                'chapter': start_page,
                'title': chapter['title'],
                'status': 'failed',
                'error': str(e)
            })
    
    doc.close()
    
    # 保存任务列表
    tasks_path = os.path.join(output_dir, 'translation_tasks.json')
    with open(tasks_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    # 输出摘要
    print()
    print("=" * 60)
    print("章节提取摘要")
    print("=" * 60)
    
    total_pages = sum(t['page_count'] for t in tasks if 'page_count' in t)
    total_size = sum(t.get('size_kb', 0) for t in tasks)
    
    print(f"章节数：{len(tasks)}")
    print(f"总页数：{total_pages}")
    print(f"总文件大小：{total_size:.1f} KB ({total_size/1024:.1f} MB)")
    print()
    
    print("详细列表:")
    print("-" * 60)
    for task in tasks:
        status_icon = "✅" if task['status'] == 'extracted' else "❌"
        title_short = task['title'][:40] + "..." if len(task['title']) > 40 else task['title']
        print(f"{status_icon} 第{task['chapter']}章：{title_short}")
        if task['status'] == 'extracted':
            print(f"    {task['pages']}页 ({task['page_count']}页), {task['size_kb']:.1f} KB")

if __name__ == '__main__':
    main()
    print("\n" + "=" * 60)
    print("提取完成!")
    print("=" * 60)
