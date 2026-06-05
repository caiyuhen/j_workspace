import re

# 读取文件
filepath = r'D:\doc\数据培训 PPT_增强版.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取所有幻灯片，按出现的顺序
slide_pattern = r'(<div class="slide" id="s\d+".*?<div class="nav-bar">)'
all_matches = list(re.finditer(slide_pattern, content, re.DOTALL))

# 单独提取每张幻灯片
individual_pattern = r'<div class="slide" id="s\d+".*?(?=<div class="slide"|$)'
slides = list(re.finditer(individual_pattern, content, re.DOTALL | re.IGNORECASE))

# 移除最后的 nav-bar 部分
for i, slide in enumerate(slides):
    slide_content = slide.group(0)
    # 移除 nav-bar 如果存在
    nav_match = re.search(r'<div class="nav-bar">.*', slide_content, re.DOTALL)
    if nav_match:
        slides[i] = re.sub(r'<div class="slide" id="s\d+".*?<div class="nav-bar">.*', 
                          r'<div class="slide" id="s\1">' + nav_match.group(0)[:nav_match.start()], 
                          slide_content, flags=re.DOTALL)

print(f'找到 {len(slides)} 张幻灯片')

# 按顺序编号并提取标题
numbered_slides = []
for idx, slide in enumerate(slides):
    slide_id_match = re.search(r'id="s(\d+)"', slide.group(0))
    slide_id = slide_id_match.group(1) if slide_id_match else 'unknown'
    
    # 提取标题
    title_match = re.search(r'slide-title"[^>]*>([^<]+)', slide.group(0))
    section_match = re.search(r'section-name"[^>]*>([^<]+)', slide.group(0))
    kicker_match = re.search(r'kicker"[^>]*>([^<]+)', slide.group(0))
    
    if title_match:
        title = title_match.group(1).strip()[:60]
    elif section_match:
        title = f'[分节] {section_match.group(1).strip()}'
    elif kicker_match:
        title = f'[封面] {kicker_match.group(1).strip()}'
    else:
        title = '[无标题]'
    
    numbered_slides.append({
        'position': idx + 1,  # 当前位置 (1-based)
        'id': slide_id,
        'title': title,
        'content': slide.group(0)
    })
    
    print(f'{idx+1}. S{slide_id}: {title}')

print(f'\n总幻灯片数：{len(numbered_slides)}')

# 用户要求的重新排序:
# 将第 23 页移到第 12 页位置
# 将第 24 页移到第 16 页位置
# 将第 21 页移到第 14 页位置
# 将第 22 页移到第 15 页位置
# 将第 25 页移到第 20 页位置
# 将第 20 页移到第 25 页位置
# 其它顺延

print('\n=== 用户要求的重新排序 ===')
print('注意：当前只有 25 页，但用户提到了第 23-25 页')

# 检查是否有 25 页
if len(numbered_slides) < 25:
    print(f'\n⚠️  警告：只有 {len(numbered_slides)} 页，没有第 23-25 页')
    print('可能用户指的是 ID 而不是位置？')
    print('或者需要重新检查文件结构...')
else:
    print(f'\n✓ 有 {len(numbered_slides)} 页，可以执行重新排序')
    
    # 创建重新排序映射
    # 用户说的"将 SLIDE 23 修改为 SLIDE 12"意思是：原来在第 23 页的内容现在放到第 12 页
    reorder_spec = {
        23: 12,  # 原第 23 页 → 新第 12 页
        24: 16,  # 原第 24 页 → 新第 16 页
        21: 14,  # 原第 21 页 → 新第 14 页
        22: 15,  # 原第 22 页 → 新第 15 页
        25: 20,  # 原第 25 页 → 新第 20 页
        20: 25,  # 原第 20 页 → 新第 25 页
    }
    
    print('\n重新排序规则:')
    for old_pos, new_pos in sorted(reorder_spec.items()):
        slide = numbered_slides[old_pos - 1]
        print(f'  原第{old_pos}页 (S{slide["id"]}) [{slide["title"][:40]}] → 新第{new_pos}页')
