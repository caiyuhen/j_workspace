import json

# 加载原始数据
with open('C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/SDTMIG_v3.4_raw.json', 'r', encoding='utf-8') as f:
    all_pages = json.load(f)

# 根据目录结构，第 1 章 Introduction 从第 7 页开始，到第 16 页左右
# 提取第 1-16 页 (索引 0-15)
chapter1_pages = all_pages[0:16]

# 合并文本
full_text = ""
for page_data in chapter1_pages:
    full_text += f"\n\n[Page {page_data['page']}]\n{page_data['text']}"

# 保存到文件
with open('C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/Chapter1_Introduction.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)

print(f"第 1 章 Introduction 提取完成")
print(f"页数：{len(chapter1_pages)}")
print(f"总字符数：{len(full_text)}")
print(f"已保存到：Chapter1_Introduction.txt")
