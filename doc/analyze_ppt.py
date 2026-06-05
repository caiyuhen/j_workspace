import re

# 读取文件
filepath = r'D:\doc\数据培训 PPT_增强版.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

print('=== 当前 PPT 结构分析 ===')

# 提取所有幻灯片，带顺序
slide_pattern = r'(<div class="slide" id="s\d+".*?</div>\s*<!-- ═.*?==>)'
slides_with_comments = re.findall(slide_pattern, content, re.DOTALL)

# 更简单的方法：按顺序提取
simple_pattern = r'<div class="slide" id="s(\d+)".*?>([^<]*<div[^>]*class="slide-inner"[^>]*>(.*?)</div>.*?</div>)'
slides = list(re.finditer(simple_pattern, content, re.DOTALL))

print(f'找到 {len(slides)} 张幻灯片')

# 打印每张幻灯片的标题
for i, match in enumerate(slides):
    slide_id = match.group(1)
    inner_content = match.group(3)[:500]
    
    # 尝试提取标题
    title_match = re.search(r'slide-title"[^>]*>([^<]+)', inner_content)
    section_match = re.search(r'section-name"[^>]*>([^<]+)', inner_content)
    
    if title_match:
        title = title_match.group(1).strip()[:60]
        print(f'{i+1}. S{slide_id}: {title}')
    elif section_match:
        section = section_match.group(1).strip()
        print(f'{i+1}. S{slide_id}: [分节页] {section}')
    else:
        print(f'{i+1}. S{slide_id}: [无标题]')

print('\n=== 用户要求的重新排序 ===')
print('将 Slide 23 移到位置 12')
print('将 Slide 24 移到位置 16')  
print('将 Slide 21 移到位置 14')
print('将 Slide 22 移到位置 15')
print('将 Slide 25 移到位置 20')
print('将 Slide 20 移到位置 25')
print('其它顺延')

print('\n但当前只有 25 张幻灯片 (S0-S22,含重复),没有 S23-S25')
print('需要确认用户的真实意图...')
