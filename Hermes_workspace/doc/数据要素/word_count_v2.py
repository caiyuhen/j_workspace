import re, os

def count_cn(text):
    cn = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text)
    return len(cn)

os.chdir(r'D:\workspace\Hermes_workspace\doc\数据要素')

files = [
    ('申报书填充内容_part1.md', [
        ('项目背景(500)', '### （一）项目背景'),
        ('应用场景(500)', '### （二）应用场景'),
        ('核心优势(1000)', '### （三）核心优势'),
    ]),
    ('申报书填充内容_part2a.md', [
        ('数据要素基础(3000)', '### （一）数据要素基础'),
    ]),
    ('申报书填充内容_part2b.md', [
        ('技术路线(4000)', '### （二）技术路线'),
    ]),
    ('申报书填充内容_part2cd.md', [
        ('数据治理(3000)', '### （三）数据治理'),
        ('机制创新(3000)', '### （四）机制创新'),
    ]),
    ('申报书填充内容_part4_security.md', [
        ('安全保障(1000)', '### （五）安全保障'),
    ]),
    ('申报书填充内容_part3.md', [
        ('应用成效(5000)', '## 三、应用成效'),
        ('商业模式(5000)', '## 四、商业模式'),
    ]),
]

for fname, sections in files:
    if not os.path.exists(fname):
        print(f'{fname}: NOT FOUND')
        continue
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f'\n=== {fname} === 总中文字: {count_cn(content)}')
    
    for sec_name, sec_key in sections:
        # Find the section and count its chars
        idx = content.find(sec_key)
        if idx == -1:
            print(f'  [WARN] Section "{sec_key}" not found in {fname}')
            continue
        
        # Find the next section at same or higher level
        rest = content[idx + len(sec_key):]
        # Look for next ### or ## heading
        next_idx = len(content)
        for pattern in ['### ', '## ']:
            pos = rest.find(f'\n{pattern}')
            if pos != -1 and idx + len(sec_key) + pos < next_idx:
                next_idx = idx + len(sec_key) + pos
        
        section_text = content[idx:next_idx]
        print(f'  [{sec_name}] {count_cn(section_text)}字')
