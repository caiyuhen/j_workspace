import fitz
import json
import re

def extract_pdf_structure(pdf_path):
    """提取 PDF 的目录和章节结构"""
    doc = fitz.open(pdf_path)
    result = {
        'total_pages': len(doc),
        'toc': [],
        'sample_pages': []
    }
    
    # 提取目录
    try:
        toc = doc.get_toc()
        result['toc'] = toc
    except:
        result['toc'] = []
    
    # 提取前 5 页的文本用于预览
    for i in range(min(5, len(doc))):
        page = doc[i]
        text = page.get_text()
        if text.strip():
            result['sample_pages'].append({
                'page': i + 1,
                'text': text[:2000]  # 每页最多 2000 字符
            })
    
    doc.close()
    return result

# 提取结构
pdf_path = 'C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/SDTMIG_v3.4-FINAL_2022-07-21.pdf'
structure = extract_pdf_structure(pdf_path)

# 保存结果
with open('C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/SDTMIG_structure.json', 'w', encoding='utf-8') as f:
    json.dump(structure, f, ensure_ascii=False, indent=2)

print(f"总页数：{structure['total_pages']}")
print(f"目录项数：{len(structure['toc'])}")
print("\n目录结构:")
for item in structure['toc'][:20]:  # 显示前 20 项
    try:
        level = int(item[1]) if item[1] else 1
        print(f"  {'  ' * (level-1)}{item[2]} (页 {item[0]})")
    except:
        print(f"  {item}")
