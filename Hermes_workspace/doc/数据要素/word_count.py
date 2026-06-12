import os

files = {
    '项目概述(项目背景500+应用场景500+核心优势1000)': 'D:/workspace/Hermes_workspace/doc/数据要素/申报书填充内容_part1.md',
    '解决方案(数据要素基础3000+技术路线4000)': 'D:/workspace/Hermes_workspace/doc/数据要素/申报书填充内容_part2a.md',
    '解决方案(技术路线续+数据治理3000+机制创新3000)': 'D:/workspace/Hermes_workspace/doc/数据要素/申报书填充内容_part2b.md',
    '解决方案(数据治理续+机制创新续+安全保障1000)': 'D:/workspace/Hermes_workspace/doc/数据要素/申报书填充内容_part2cd.md',
    '安全保障(1000)': 'D:/workspace/Hermes_workspace/doc/数据要素/申报书填充内容_part4_security.md',
    '应用成效(5000)+商业模式(5000)': 'D:/workspace/Hermes_workspace/doc/数据要素/申报书填充内容_part3.md',
}

import re

def count_chinese_chars(text):
    """Count Chinese characters only"""
    chinese = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', text)
    return len(chinese)

def count_all_chars(text):
    """Count all characters including punctuation, spaces, etc"""
    return len(text)

for label, path in files.items():
    if not os.path.exists(path):
        print(f"{label}: FILE NOT FOUND at {path}")
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    chinese_count = count_chinese_chars(content)
    total_count = count_all_chars(content)
    print(f"\n{label}")
    print(f"  位置: {path}")
    print(f"  中文字数: {chinese_count}")
    print(f"  总字符数: {total_count}")
    
    # Try to count by sections
    lines = content.split('\n')
    section_chars = {}
    current_section = "header"
    for line in lines:
        if line.startswith('### ') or line.startswith('## '):
            current_section = line.strip()
        if current_section not in section_chars:
            section_chars[current_section] = 0
        section_chars[current_section] += count_chinese_chars(line)
    
    for sec, cnt in section_chars.items():
        if cnt > 0:
            print(f"    [{sec}] ~{cnt}中文字")
