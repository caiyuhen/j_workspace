import re

# 读取文件
filepath = r'D:\doc\数据培训 PPT_增强版.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'原始文件大小：{len(content)} 字节')

# 提取所有幻灯片，按 id 排序
slide_pattern = r'(<div class="slide" id="s\d+".*?</div>)'
slides = re.findall(slide_pattern, content, re.DOTALL)

print(f'找到 {len(slides)} 张幻灯片')

# 创建幻灯片 ID 到内容的映射
slide_map = {}
for slide in slides:
    match = re.search(r'id="s(\d+)"', slide)
    if match:
        slide_num = int(match.group(1))
        slide_map[slide_num] = slide

print(f'幻灯片 ID 范围：{min(slide_map.keys())} - {max(slide_map.keys())}')

# 用户要求的映射关系:
# SLIDE 23 → SLIDE 12
# SLIDE 24 → SLIDE 16
# SLIDE 21 → SLIDE 14
# SLIDE 22 → SLIDE 15
# SLIDE 25 → SLIDE 20
# SLIDE 20 → SLIDE 25
# 其它的顺延

# 创建新的映射表
reorder_map = {
    23: 12,
    24: 16,
    21: 14,
    22: 15,
    25: 20,
    20: 25,
}

# 获取所有原始幻灯片 ID
original_ids = sorted(slide_map.keys())
print(f'原始幻灯片 ID: {original_ids}')

# 确定哪些 ID 需要顺延 (不在 reorder_map 中的)
# 我们需要为每个目标位置分配正确的内容

# 首先，将明确指定的幻灯片放到目标位置
assigned_targets = set(reorder_map.values())
print(f'已分配的目标位置：{sorted(assigned_targets)}')

# 找出未被重新排序的原始幻灯片
unreordered_sources = [s for s in original_ids if s not in reorder_map]
print(f'未重新排序的源幻灯片：{unreordered_sources}')

# 找出可用的目标位置 (0-24, 排除已分配的)
all_targets = set(range(25))  # 假设共 25 页
available_targets = sorted(all_targets - assigned_targets)
print(f'可用目标位置：{available_targets}')

# 按顺序分配未重新排序的幻灯片
for src, tgt in zip(unreordered_sources, available_targets):
    reorder_map[src] = tgt

print(f'\n完整映射关系:')
for src in sorted(reorder_map.keys()):
    print(f'  S{src} → S{reorder_map[src]}')

# 按目标位置排序，生成新的幻灯片顺序
sorted_by_target = sorted(reorder_map.items(), key=lambda x: x[1])

# 重建内容
# 首先找到 slide 容器
slide_container_pattern = r'(<div class="deck" id="deck">)(.*?)(</div><!-- /deck -->)'
match = re.search(slide_container_pattern, content, re.DOTALL)

if match:
    deck_start = match.group(1)
    deck_end = match.group(3)
    
    # 按新顺序拼接幻灯片
    new_slides_content = ''
    for src_id, tgt_id in sorted_by_target:
        slide_content = slide_map[src_id]
        # 更新 slide 的 id
        new_slide = re.sub(r'id="s\d+"', f'id="s{tgt_id}"', slide_content)
        new_slides_content += new_slide + '\n\n'
    
    # 替换内容
    new_content = deck_start + '\n' + new_slides_content + deck_end
    content = re.sub(slide_container_pattern, new_content, content)
    
    print(f'\n✓ 已重新排序幻灯片')
    print(f'新文件大小：{len(content)} 字节')
    
    # 保存
    output_path = r'D:\doc\数据培训 PPT_增强版_v2.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'\n✅ 文件已保存：{output_path}')
else:
    print('✗ 未找到 deck 容器')
