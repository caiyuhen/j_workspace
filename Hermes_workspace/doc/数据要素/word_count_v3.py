import re, os

def count_cn(text):
    cn = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text)
    return len(cn)

os.chdir(r'D:\workspace\Hermes_workspace\doc\数据要素')

# Read part3 and count sections manually
with open('申报书填充内容_part3.md', 'r', encoding='utf-8') as f:
    p3 = f.read()

# Find app section
app_start = p3.find('## 三、应用成效')
bus_start = p3.find('## 四、商业模式')

app_text = p3[app_start:bus_start] if bus_start > app_start else p3[app_start:]
bus_text = p3[bus_start:]

print('=== 申报书填充内容_part3.md ===')
print(f'  总中文字: {count_cn(p3)}')
print(f'  [应用成效(5000)] {count_cn(app_text)}字')
print(f'  [商业模式(5000)] {count_cn(bus_text)}字')

# Also do all other files
files = [
    '申报书填充内容_part1.md',
    '申报书填充内容_part2a.md',
    '申报书填充内容_part2b.md',
    '申报书填充内容_part2cd.md',
    '申报书填充内容_part4_security.md',
]

for fname in files:
    if not os.path.exists(fname):
        print(f'{fname}: NOT FOUND')
        continue
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'\n=== {fname} === 总中文字: {count_cn(content)}')
    
    lines = content.split('\n')
    section_cn = {}
    current = ''
    for line in lines:
        if line.startswith('### '):
            current = line.strip()
        if current not in section_cn:
            section_cn[current] = 0
        section_cn[current] += count_cn(line)
    
    for sec, cnt in section_cn.items():
        if cnt > 100:
            print(f'  [{sec}] {cnt}字')
