import json

# 加载原始数据
with open('C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/SDTMIG_v3.4_raw.json', 'r', encoding='utf-8') as f:
    all_pages = json.load(f)

# 根据目录结构，第 2 章从第 17 页开始，到第 40 页左右
# 提取第 17-40 页 (索引 16-39)
chapter2_pages = all_pages[16:40]

# 合并文本
full_text = ""
for page_data in chapter2_pages:
    full_text += f"\n\n[Page {page_data['page']}]\n{page_data['text']}"

# 保存到文件
with open('C:/Users/Administrator/WorkBuddy/2026-05-25-11-17-06/Chapter2_Fundamentals.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)

print(f"第 2 章 Fundamentals of the SDTM 提取完成")
print(f"页数：{len(chapter2_pages)}")
print(f"总字符数：{len(full_text)}")
print(f"已保存到：Chapter2_Fundamentals.txt")
