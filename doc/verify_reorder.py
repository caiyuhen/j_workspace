import re
filepath = r'D:\doc\数据培训 PPT_增强版_重排.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

slide_starts = list(re.finditer(r'<div class="slide" id="s(\d+)"', content))
print(f'重排后幻灯片数：{len(slide_starts)}')
print()

for i, match in enumerate(slide_starts):
    start_pos = match.start()
    if i + 1 < len(slide_starts):
        end_pos = slide_starts[i + 1].start()
    else:
        nav_match = re.search(r'<div class="nav-bar">', content[start_pos:])
        end_pos = start_pos + nav_match.start() if nav_match else len(content)
    
    slide_content = content[start_pos:end_pos]
    title_match = re.search(r'slide-title"[^>]*>([^<]+)', slide_content)
    section_match = re.search(r'section-name"[^>]*>([^<]+)', slide_content)
    
    if title_match:
        title = title_match.group(1).strip()[:50]
    elif section_match:
        title = '[分节] ' + section_match.group(1).strip()
    else:
        title = '[无标题]'
    
    print(f'{i+1:2d}. S{match.group(1)}: {title}')
