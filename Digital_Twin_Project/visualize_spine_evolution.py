import json
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def calculate_spine_coordinates(metrics, curve_data):
    """
    根据指标计算脊柱椎骨的 3D 坐标。
    重用了 generate_spine_model.py 中的逻辑
    """
    # 1. 生成 Z 轴 (垂直)
    num_vertebrae = 17 # T1-T12, L1-L5
    z_coords = np.linspace(0, 600, num_vertebrae) # 600mm 高度近似值

    # 2. 生成矢状面轮廓 (Y 轴) - 后凸与前凸
    # 建模为两个正弦波
    # 胸椎 (后凸): y = A * sin(k * z)
    # 腰椎 (前凸): y = -B * sin(k * z)
    
    kyphosis_angle = metrics.get('kyphosis_max', 30)
    lordosis_angle = metrics.get('lordosis_max', 40)
    
    # 将角度转换为简化的深度幅度 (启发式)
    # 40 度约 30-40mm 深度？我们使用 1.0 因子进行可视化
    kyphosis_depth = kyphosis_angle * 1.0
    lordosis_depth = lordosis_angle * 1.0

    y_coords = []
    for z in z_coords:
        if z > 300: # 胸椎 (上部)
            # 归一化胸椎 z (300-600) -> 0-Pi
            norm_z = (z - 300) / 300 * np.pi
            y = kyphosis_depth * np.sin(norm_z)
        else: # 腰椎 (下部)
            # 归一化腰椎 z (0-300) -> 0-Pi
            norm_z = z / 300 * np.pi
            y = -lordosis_depth * np.sin(norm_z)
        y_coords.append(y)

    # 3. 生成冠状面轮廓 (X 轴) - 脊柱侧弯/旋转
    # 如果缺少冠状面偏移或偏移较小，则使用旋转来驱动 X 轴偏移
    rotations = curve_data.get('vertebral_rotation', [0]*num_vertebrae)
    
    # 如果旋转列表较短/较长，则进行插值
    if len(rotations) != num_vertebrae:
        rotations = np.interp(
            np.linspace(0, 1, num_vertebrae),
            np.linspace(0, 1, len(rotations)),
            rotations
        )

    # 启发式：旋转引起侧向偏离
    # 10 度旋转 -> ~5mm 偏移？
    x_coords = []
    
    # 检查是否存在显式的冠状面偏移
    explicit_offsets = curve_data.get('coronal_offsets', [])
    if explicit_offsets and len(explicit_offsets) > 0:
         if len(explicit_offsets) != num_vertebrae:
            explicit_offsets = np.interp(
                np.linspace(0, 1, num_vertebrae),
                np.linspace(0, 1, len(explicit_offsets)),
                explicit_offsets
            )
         x_coords = explicit_offsets
    else:
        # 源自旋转
        x_coords = [-r * 0.5 for r in rotations] 

    return z_coords, y_coords, x_coords, rotations

def get_node_colors(rotations, x_coords):
    colors = []
    for rot, off in zip(rotations, x_coords):
        if abs(rot) > 5 or abs(off) > 10:
            colors.append('red')
        else:
            colors.append('green')
    return colors

def create_spine_traces(z, y, x, colors, name_prefix):
    x_center = x.tolist() if hasattr(x, 'tolist') else list(x)
    y_center = y.tolist() if hasattr(y, 'tolist') else list(y)
    z_center = z.tolist() if hasattr(z, 'tolist') else list(z)

    vertebra_x = []
    vertebra_y = []
    vertebra_z = []
    rib_x = []
    rib_y = []
    rib_z = []
    center_index = (len(z_center) - 1) / 2 if z_center else 0

    for i, (cx, cy, cz) in enumerate(zip(x_center, y_center, z_center)):
        dist = abs(i - center_index) / center_index if center_index else 0
        width = 14 - 5 * dist
        depth = 5 - 1.5 * dist
        vertebra_x.extend([cx - width, cx + width, cx + width, cx - width, cx - width, None])
        vertebra_y.extend([cy - depth, cy - depth, cy + depth, cy + depth, cy - depth, None])
        vertebra_z.extend([cz, cz, cz, cz, cz, None])
        rib_span = 22 - 8 * dist
        rib_depth = 12 - 4 * dist
        left_rib_x = [cx - width, cx - width - rib_span * 0.55, cx - width - rib_span]
        left_rib_y = [cy, cy + rib_depth, cy + rib_depth * 0.35]
        right_rib_x = [cx + width, cx + width + rib_span * 0.55, cx + width + rib_span]
        right_rib_y = [cy, cy + rib_depth, cy + rib_depth * 0.35]
        rib_x.extend(left_rib_x + [None] + right_rib_x + [None])
        rib_y.extend(left_rib_y + [None] + right_rib_y + [None])
        rib_z.extend([cz, cz, cz, None, cz, cz, cz, None])

    x_lines = x_center + [None] + vertebra_x + rib_x
    y_lines = y_center + [None] + vertebra_y + rib_y
    z_lines = z_center + [None] + vertebra_z + rib_z

    color_value_map = {'green': 0, 'red': 1}
    center_color_values = [color_value_map.get(c, 0) for c in colors]
    vertebra_color_values = []
    rib_color_values = []
    for c in colors:
        v = color_value_map.get(c, 0)
        vertebra_color_values.extend([v, v, v, v, v, 0])
        rib_color_values.extend([v, v, v, 0, v, v, v, 0])
    line_color_values = center_color_values + [0] + vertebra_color_values + rib_color_values

    return go.Scatter3d(
        x=x_lines,
        y=y_lines,
        z=z_lines,
        mode='lines',
        line=dict(
            color=line_color_values,
            cmin=0,
            cmax=1,
            colorscale=[[0.0, '#22c55e'], [0.4999, '#22c55e'], [0.5, '#ef4444'], [1.0, '#ef4444']],
            width=8
        ),
        name=f'{name_prefix} 脊柱骨格'
    )

def visualize_evolution(timeseries_file, output_dir):
    with open(timeseries_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    patient_name = data['patient_name']
    timeline = data['timeline']
    
    # 检查这是否是强化治疗演示
    is_intensive = "intensive" in os.path.basename(timeseries_file)
    output_filename = f"{patient_name}_intensive_evolution_viz.html" if is_intensive else f"{patient_name}_evolution_viz.html"

    # 翻译治疗类型
    treatment_type = data['treatment_plan']['type']
    treatment_map = {
        'Brace': '支具治疗',
        'PT': '物理治疗',
        'Intensive': '强化干预',
        'Surgery': '手术治疗'
    }
    treatment_cn = treatment_map.get(treatment_type, treatment_type)

    # 创建子图
    fig = make_subplots(
        rows=2, cols=2,
        specs=[
            [{'type': 'scene'}, {'type': 'scene'}],
            [{'colspan': 2, 'type': 'xy'}, None]
        ],
        subplot_titles=(
            '自然发展', 
            '强化干预' if is_intensive else f"干预治疗 ({treatment_cn})",
            '指标对比'
        ),
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3]
    )

    # --- 图表的静态数据 ---
    # 尝试先获取 'week'，如果是旧数据则回退到 'month'
    weeks = []
    if 'week' in timeline[0]:
        weeks = [t['week'] for t in timeline]
        time_unit = "周"
        time_label = "Week"
    else:
        weeks = [t['month'] for t in timeline]
        time_unit = "月"
        time_label = "Month"
    
    # 指标提取
    c_kyphosis = [t['control']['metrics']['kyphosis_max'] for t in timeline]
    i_kyphosis = [t['intervention']['metrics']['kyphosis_max'] for t in timeline]
    
    c_max_rot = [max([abs(r) for r in t['control']['curve_data']['vertebral_rotation']]) for t in timeline]
    i_max_rot = [max([abs(r) for r in t['intervention']['curve_data']['vertebral_rotation']]) for t in timeline]

    # 添加指标轨迹 (静态背景线)
    fig.add_trace(go.Scatter(x=weeks, y=c_kyphosis, mode='lines', name='自然发展 (后凸角)', line=dict(color='red', dash='dot')), row=2, col=1)
    fig.add_trace(go.Scatter(x=weeks, y=i_kyphosis, mode='lines', name='强化干预 (后凸角)' if is_intensive else '干预治疗 (后凸角)', line=dict(color='green', dash='dot')), row=2, col=1)
    fig.add_trace(go.Scatter(x=weeks, y=c_max_rot, mode='lines', name='自然发展 (旋转角)', line=dict(color='orange', dash='dash')), row=2, col=1)
    fig.add_trace(go.Scatter(x=weeks, y=i_max_rot, mode='lines', name='强化干预 (旋转角)' if is_intensive else '干预治疗 (旋转角)', line=dict(color='blue', dash='dash')), row=2, col=1)

    # 当前时间的移动垂直线
    # 时间 0 的初始位置
    max_y = max(max(c_kyphosis), max(i_kyphosis), max(c_max_rot), max(i_max_rot)) * 1.1
    fig.add_trace(go.Scatter(x=[0, 0], y=[0, max_y], mode='lines', name='当前时间', line=dict(color='black', width=2)), row=2, col=1)

    # --- 初始 3D 状态 (时间 0) ---
    t0 = timeline[0]
    
    # 对照组
    z0, y0, x0, r0 = calculate_spine_coordinates(t0['control']['metrics'], t0['control']['curve_data'])
    colors0_c = get_node_colors(r0, x0)
    trace_control = create_spine_traces(z0, y0, x0, colors0_c, "自然发展")
    fig.add_trace(trace_control, row=1, col=1)

    # 干预组
    # (通常在第 0 个月与对照组相同，但我们计算一下)
    z0i, y0i, x0i, r0i = calculate_spine_coordinates(t0['intervention']['metrics'], t0['intervention']['curve_data'])
    colors0_i = get_node_colors(r0i, x0i)
    trace_intervention = create_spine_traces(z0i, y0i, x0i, colors0_i, "强化干预" if is_intensive else "干预治疗")
    fig.add_trace(trace_intervention, row=1, col=2)


    # --- 动画帧 ---
    frames = []
    for i, t in enumerate(timeline):
        time_val = weeks[i]
        
        # 对照组数据
        zc, yc, xc, rc = calculate_spine_coordinates(t['control']['metrics'], t['control']['curve_data'])
        cc = get_node_colors(rc, xc)
        
        # 干预组数据
        zi, yi, xi, ri = calculate_spine_coordinates(t['intervention']['metrics'], t['intervention']['curve_data'])
        ci = get_node_colors(ri, xi)

        # 帧
        frames.append(go.Frame(
            data=[
                # 更新指标线 (当前时间) - 索引 4
                go.Scatter(x=[time_val, time_val], y=[0, max_y]), 
                
                # 更新对照组 3D - 索引 5
                create_spine_traces(zc, yc, xc, cc, "自然发展"),
                
                # 更新干预组 3D - 索引 6
                create_spine_traces(zi, yi, xi, ci, "干预治疗")
            ],
            name=str(time_val),
            traces=[4, 5, 6] # 仅更新这些轨迹
        ))

    fig.frames = frames

    # --- 滑块与按钮 ---
    fig.update_layout(
        title=f"脊柱治疗预测: {patient_name} (周期: {len(timeline)-1} {time_unit})",
        scene=dict(
            xaxis=dict(range=[-100, 100], title='冠状面 (X)'),
            yaxis=dict(range=[-100, 100], title='矢状面 (Y)'),
            zaxis=dict(range=[0, 600], title='轴向 (Z)'),
            aspectmode='manual', aspectratio=dict(x=1, y=1, z=3)
        ),
        scene2=dict(
            xaxis=dict(range=[-100, 100], title='冠状面 (X)'),
            yaxis=dict(range=[-100, 100], title='矢状面 (Y)'),
            zaxis=dict(range=[0, 600], title='轴向 (Z)'),
            aspectmode='manual', aspectratio=dict(x=1, y=1, z=3)
        ),
        sliders=[{
            'steps': [
                {
                    'method': 'animate',
                    'args': [[str(k)], {'mode': 'immediate', 'frame': {'duration': 100, 'redraw': True}, 'transition': {'duration': 0}}],
                    'label': str(k)
                } for k in weeks
            ],
            'transition': {'duration': 0},
            'x': 0.1, 'len': 0.9,
            'currentvalue': {'prefix': f'{time_unit}: '}
        }],
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'x': 0.05,
            'buttons': [
                {
                    'label': '播放',
                    'method': 'animate',
                    'args': [None, {'frame': {'duration': 100, 'redraw': True}, 'fromcurrent': True, 'transition': {'duration': 0}}]
                },
                {
                    'label': '暂停',
                    'method': 'animate',
                    'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate', 'transition': {'duration': 0}}]
                }
            ]
        }]
    )

    output_path = os.path.join(output_dir, output_filename)
    fig.write_html(output_path)
    print(f"Visualization generated: {output_path}")

if __name__ == "__main__":
    input_file = r"d:\workspace\Digital_Twin_Project\spine_prediction_timeseries.json"
    output_dir = r"d:\workspace\Digital_Twin_Project\output"
    
    visualize_evolution(input_file, output_dir)
