import fitz
import json
import re

def extract_all_text(pdf_path, output_md):
    """提取 PDF 全部文本并保存为 Markdown"""
    doc = fitz.open(pdf_path)
    all_text = []
    
    print(f"开始提取 {len(doc)} 页内容...")
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        if text.strip():
            all_text.append({
                'page': i + 1,
                'text': text
            })
            if (i + 1) % 50 == 0:
                print(f"  已提取 {i + 1}/{len(doc)} 页")
    
    doc.close()
    
    # 保存到 JSON
    json_output = 'C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/SDTMIG_v3.4_raw.json'
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(all_text, f, ensure_ascii=False, indent=2)
    print(f"JSON 数据已保存到：{json_output}")
    
    print(f"提取完成！共 {len(all_text)} 页有内容的页面")
    print(f"原始数据已保存到：{output_md.replace('.md', '_raw.json')}")
    
    # 同时保存为纯文本用于预览
    with open(output_md.replace('.md', '_preview.txt'), 'w', encoding='utf-8') as f:
        for item in all_text[:10]:  # 前 10 页预览
            f.write(f"\n{'='*80}\n")
            f.write(f"第 {item['page']} 页\n")
            f.write(f"{'='*80}\n")
            f.write(item['text'][:3000] + "\n")  # 每页最多 3000 字符
    
    return len(all_text)

# 提取全部文本
pdf_path = 'C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/SDTMIG_v3.4-FINAL_2022-07-21.pdf'
output_path = 'C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/SDTMIG_v3.4_ENGLISH.txt'

total_pages = extract_all_text(pdf_path, output_path)
print(f"\n总页数：{total_pages}")
