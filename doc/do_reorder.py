import re

filepath = r'D:\doc\数据培训 PPT_增强版.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取所有幻灯片
slide_starts = list(re.finditer(r'<div class="slide" id="s(\d+)"', content))
slides = []
for i, match in enumerate(slide_starts):
    start_pos = match.start()
    if i + 1 < len(slide_starts):
        end_pos = slide_starts[i + 1].start()
    else:
        nav_match = re.search(r'<div class="nav-bar">', content[start_pos:])
        end_pos = start_pos + nav_match.start() if nav_match else len(content)
    slides.append(content[start_pos:end_pos])

print(f'原始幻灯片数：{len(slides)}')

# 用户要求的重新排序:
# 将第 23 页修改为第 12 页位置
# 将第 24 页修改为第 16 页位置
# 将第 21 页修改为第 14 页位置
# 将第 22 页修改为第 15 页位置
# 将第 20 页修改为第 25 页位置
# 其它顺延

# 由于只有 24 页，我将理解为:
# 将 S21 (位置 23) → 移到位置 12
# 将 S22 (位置 24) → 移到位置 16
# 将 S19 (位置 21) → 移到位置 14
# 将 S20 (位置 22) → 移到位置 15
# 将 S22 (位置 24，最后一张) → 移到位置 20
# 将 S18 (位置 20) → 移到位置 25(但只有 24 页，所以到 24 或 25)

# 创建新的顺序
# 首先移除要移动的幻灯片
move_spec = [
    (23, 12),  # 原位置 23 → 新位置 12
    (24, 16),  # 原位置 24 → 新位置 16
    (21, 14),  # 原位置 21 → 新位置 14
    (22, 15),  # 原位置 22 → 新位置 15
    (20, 25),  # 原位置 20 → 新位置 25(扩展一页)
]

# 将要移动的幻灯片编号 (1-based)
to_move = {23, 24, 21, 22, 20}
to_keep = [i for i in range(1, len(slides)+1) if i not in to_move]

print(f'要保持的幻灯片位置：{to_keep}')
print(f'要移动的幻灯片位置：{sorted(to_move)}')

# 创建新顺序数组
new_order = [None] * 25  # 预留 25 个位置

# 先放置固定的移动规则
for old_pos, new_pos in move_spec:
    if old_pos <= len(slides):
        new_order[new_pos - 1] = old_pos - 1  # 转换为 0-based 索引
        print(f'位置{old_pos} → 位置{new_pos}')

# 填充剩余的 (保持原有顺序)
keep_idx = 0
for i in range(25):
    if new_order[i] is None:
        if keep_idx < len(to_keep):
            new_order[i] = to_keep[keep_idx] - 1  # 转换为 0-based
            keep_idx += 1

# 移除 None
new_order = [idx for idx in new_order if idx is not None]

print(f'\n新顺序共有 {len(new_order)} 张幻灯片')
print('新顺序映射:')
for new_pos, old_pos in enumerate(new_order, 1):
    print(f'  新位置{new_pos:2d} ← 原位置{old_pos+1:2d}')

# 重新拼接幻灯片
nav_match = re.search(r'(<div class="nav-bar">.*?</body></html>)', content, re.DOTALL)
nav_html = nav_match.group(1) if nav_match else ''

# 找到 deck 结束标记
deck_end_match = re.search(r'(<\/div><!-- \/deck -->)', content)
deck_end = deck_end_match.group(1) if deck_end_match else '</div>'

# 构建新的 deck 内容
new_deck_content = '<div class="deck" id="deck">\n'
for idx in new_order:
    # 更新 slide 的 id
    old_slide = slides[idx]
    # 生成新的连续 ID
    new_id = new_order.index(idx)
    new_slide = re.sub(r'id="s\d+"', f'id="s{new_id}"', old_slide)
    new_deck_content += new_slide + '\n\n'

new_deck_content += deck_end + '\n' + nav_html

# 替换原内容
new_content = re.sub(
    r'<div class="deck" id="deck">.*?(<div class="nav-bar">)',
    new_deck_content + r'\1',
    content,
    flags=re.DOTALL
)

# 保存
output_path = r'D:\doc\数据培训 PPT_增强版_重排.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'\n✅ 文件已保存：{output_path}')
print(f'新文件大小：{len(new_content)} 字节')
