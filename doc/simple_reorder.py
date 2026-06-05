import re

filepath = r'D:\doc\数据培训 PPT_增强版.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 简单方法：查找所有 <div class="slide" id="sX">
slide_starts = list(re.finditer(r'<div class="slide" id="s(\d+)"', content))
print(f'找到 {len(slide_starts)} 张幻灯片')

# 提取每张幻灯片的位置、ID 和大致内容
slides_info = []
for i, match in enumerate(slide_starts):
    slide_id = match.group(1)
    start_pos = match.start()
    
    # 找到下一张幻灯片的开始位置
    if i + 1 < len(slide_starts):
        end_pos = slide_starts[i + 1].start()
    else:
        # 找到 nav-bar
        nav_match = re.search(r'<div class="nav-bar">', content[start_pos:])
        end_pos = start_pos + nav_match.start() if nav_match else len(content)
    
    slide_content = content[start_pos:end_pos]
    
    # 提取标题
    title_match = re.search(r'slide-title"[^>]*>([^<]+)', slide_content)
    section_match = re.search(r'section-name"[^>]*>([^<]+)', slide_content)
    kicker_match = re.search(r'kicker"[^>]*>([^<]+)', slide_content)
    
    if title_match:
        title = title_match.group(1).strip()[:50]
    elif section_match:
        title = f'[分节] {section_match.group(1).strip()}'
    elif kicker_match:
        title = f'[封面] {kicker_match.group(1).strip()}'
    else:
        title = '[无标题]'
    
    slides_info.append({
        'position': i + 1,
        'id': slide_id,
        'title': title,
        'start': start_pos,
        'end': end_pos,
        'content': slide_content
    })
    
    print(f'{i+1:2d}. S{slide_id}: {title}')

print(f'\n总幻灯片数：{len(slides_info)}')

# 检查用户要求
print('\n=== 用户要求的重新排序 ===')
print('用户说要将第 23,24,21,22,25,20 页重新排序')
print(f'但我们只有 {len(slides_info)} 页...')

# 可能用户说的是 ID?
ids_with_20_plus = [s for s in slides_info if int(s['id']) >= 20]
if ids_with_20_plus:
    print('\nID >= 20 的幻灯片:')
    for s in ids_with_20_plus:
        print(f'  位置{s["position"]}: S{s["id"]} - {s["title"][:50]}')
