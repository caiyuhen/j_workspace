import json
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class SpineVisualizer:
    def __init__(self):
        pass

    def _calculate_spine_coordinates(self, metrics, curve_data):
        """
        根据指标计算脊柱椎骨的 3D 坐标。
        """
        # 1. 生成 Z 轴 (垂直)
        num_vertebrae = 17 # T1-T12, L1-L5
        z_coords = np.linspace(0, 600, num_vertebrae) # 600mm 高度近似值

        # 2. 生成矢状面轮廓 (Y 轴) - 后凸与前凸
        kyphosis_angle = metrics.get('kyphosis_max', 30)
        lordosis_angle = metrics.get('lordosis_max', 40)
        
        kyphosis_depth = kyphosis_angle * 1.0
        lordosis_depth = lordosis_angle * 1.0

        y_coords = []
        for z in z_coords:
            if z > 300: # 胸椎 (上部)
                norm_z = (z - 300) / 300 * np.pi
                y = kyphosis_depth * np.sin(norm_z)
            else: # 腰椎 (下部)
                norm_z = z / 300 * np.pi
                y = -lordosis_depth * np.sin(norm_z)
            y_coords.append(y)

        # 3. 生成冠状面轮廓 (X 轴) - 侧弯/旋转
        rotations = curve_data.get('vertebral_rotation', [0]*num_vertebrae)
        
        if len(rotations) != num_vertebrae:
            rotations = np.interp(
                np.linspace(0, 1, num_vertebrae),
                np.linspace(0, 1, len(rotations)),
                rotations
            )

        x_coords = []
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
            x_coords = [-r * 0.5 for r in rotations] 

        return z_coords, y_coords, x_coords, rotations

    def _get_node_colors(self, rotations, x_coords):
        colors = []
        for rot, off in zip(rotations, x_coords):
            if abs(rot) > 5 or abs(off) > 10:
                colors.append('red')
            else:
                colors.append('green')
        return colors

    def _create_spine_traces(self, z, y, x, colors, name_prefix):
        if hasattr(x, 'tolist'): x = x.tolist()
        if hasattr(y, 'tolist'): y = y.tolist()
        if hasattr(z, 'tolist'): z = z.tolist()

        x_center = list(x)
        y_center = list(y)
        z_center = list(z)

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
            name=f'{name_prefix} 脊柱骨格',
            showlegend=True,
            visible=True
        )

    def create_evolution_chart(self, simulation_data):
        """
        生成脊柱演变的 Plotly 图表，包含自然病程、常规干预和强化干预的对比。
        """
        patient_name = simulation_data['patient_name']
        timeline = simulation_data['timeline']
        
        # 翻译治疗类型
        treatment_type = simulation_data['treatment_plan']['type']
        treatment_map = {
            'Brace': '支具治疗',
            'PT': '物理治疗',
            'Intensive': '强化干预',
            'Surgery': '手术治疗'
        }
        treatment_cn = treatment_map.get(treatment_type, treatment_type)

        # 创建子图: 1行3列用于3D展示，第2行用于曲线对比
        fig = make_subplots(
            rows=2, cols=3,
            specs=[
                [{'type': 'scene'}, {'type': 'scene'}, {'type': 'scene'}],
                [{'colspan': 3, 'type': 'xy'}, None, None]
            ],
            subplot_titles=(
                '自然发展 (无干预)', 
                f'常规干预 ({treatment_cn})',
                '强化干预 (高依从性/强化)',
                '关键指标对比演变'
            ),
            vertical_spacing=0.1,
            row_heights=[0.6, 0.4]
        )

        # --- 图表的静态数据 ---
        weeks = []
        time_unit = "月"
        if 'week' in timeline[0]:
            weeks = [t['week'] for t in timeline]
            time_unit = "周"
        else:
            weeks = [t['month'] for t in timeline]
        
        # 指标提取
        c_kyphosis = [t['control']['metrics']['kyphosis_max'] for t in timeline]
        i_kyphosis = [t['intervention']['metrics']['kyphosis_max'] for t in timeline]
        int_kyphosis = [t.get('intensive', {}).get('metrics', {}).get('kyphosis_max', 0) for t in timeline]
        
        c_cobb = [t['control']['metrics'].get('cobb_angle', 0) for t in timeline]
        i_cobb = [t['intervention']['metrics'].get('cobb_angle', 0) for t in timeline]
        int_cobb = [t.get('intensive', {}).get('metrics', {}).get('cobb_angle', 0) for t in timeline]

        # 添加指标轨迹 (Row 2)
        # Cobb 角
        fig.add_trace(go.Scatter(x=weeks, y=c_cobb, mode='lines', name='自然发展 (Cobb角)', line=dict(color='red', width=3)), row=2, col=1)
        fig.add_trace(go.Scatter(x=weeks, y=i_cobb, mode='lines', name='常规干预 (Cobb角)', line=dict(color='orange', width=3)), row=2, col=1)
        fig.add_trace(go.Scatter(x=weeks, y=int_cobb, mode='lines', name='强化干预 (Cobb角)', line=dict(color='green', width=3)), row=2, col=1)
        
        # 后凸角 (虚线作为参考)
        fig.add_trace(go.Scatter(x=weeks, y=c_kyphosis, mode='lines', name='自然发展 (后凸角)', line=dict(color='red', dash='dot', width=1), showlegend=True), row=2, col=1)
        fig.add_trace(go.Scatter(x=weeks, y=i_kyphosis, mode='lines', name='常规干预 (后凸角)', line=dict(color='orange', dash='dot', width=1), showlegend=True), row=2, col=1)
        fig.add_trace(go.Scatter(x=weeks, y=int_kyphosis, mode='lines', name='强化干预 (后凸角)', line=dict(color='green', dash='dot', width=1), showlegend=True), row=2, col=1)

        # 移动垂直线 (时间指示器)
        max_y = max(max(c_cobb), max(i_cobb), max(int_cobb)) * 1.2
        # 注意: 这里的 trace index 很重要，用于动画更新
        # 目前 traces: 0,1,2,3,4,5 (6条线) -> 垂直线是第 7 条 (index 6)
        fig.add_trace(go.Scatter(x=[0, 0], y=[0, max_y], mode='lines', name='当前时间', line=dict(color='black', width=2, dash='dash')), row=2, col=1)

        # --- 初始 3D 状态 (时间 0) ---
        t0 = timeline[0]
        
        # 1. 自然组 (Row 1, Col 1)
        z0, y0, x0, r0 = self._calculate_spine_coordinates(t0['control']['metrics'], t0['control']['curve_data'])
        colors0_c = self._get_node_colors(r0, x0)
        trace_control = self._create_spine_traces(z0, y0, x0, colors0_c, "自然")
        fig.add_trace(trace_control, row=1, col=1)

        # 2. 常规干预组 (Row 1, Col 2)
        z0i, y0i, x0i, r0i = self._calculate_spine_coordinates(t0['intervention']['metrics'], t0['intervention']['curve_data'])
        colors0_i = self._get_node_colors(r0i, x0i)
        trace_intervention = self._create_spine_traces(z0i, y0i, x0i, colors0_i, "常规")
        fig.add_trace(trace_intervention, row=1, col=2)

        # 3. 强化干预组 (Row 1, Col 3)
        intensive_metrics = t0.get('intensive', {}).get('metrics')
        if not intensive_metrics:
            intensive_metrics = t0['control']['metrics']
            
        intensive_curve = t0.get('intensive', {}).get('curve_data')
        if not intensive_curve:
            intensive_curve = t0['control']['curve_data']

        z0int, y0int, x0int, r0int = self._calculate_spine_coordinates(intensive_metrics, intensive_curve)
        colors0_int = self._get_node_colors(r0int, x0int)
        trace_intensive = self._create_spine_traces(z0int, y0int, x0int, colors0_int, "强化")
        fig.add_trace(trace_intensive, row=1, col=3)

        # --- 动画帧 ---
        frames = []
        # 静态 traces 数量: 6 (lines) + 1 (vertical) + 3 (3D initial) = 10 traces
        # 动画需要更新: 垂直线 (index 6), 3D Control (index 7), 3D Intervention (index 8), 3D Intensive (index 9)
        # 注意: Plotly 的 trace 索引是全局的。
        # Traces order added:
        # 0: Control Cobb (2D)
        # 1: Intervention Cobb (2D)
        # 2: Intensive Cobb (2D)
        # 3: Control Kyphosis (2D)
        # 4: Intervention Kyphosis (2D)
        # 5: Intensive Kyphosis (2D)
        # 6: Vertical Line (2D)
        # 7: Control 3D (3D)
        # 8: Intervention 3D (3D)
        # 9: Intensive 3D (3D)
        
        for i, t in enumerate(timeline):
            time_val = weeks[i]
            
            # Control 3D
            zc, yc, xc, rc = self._calculate_spine_coordinates(t['control']['metrics'], t['control']['curve_data'])
            cc = self._get_node_colors(rc, xc)
            trace_c = self._create_spine_traces(zc, yc, xc, cc, "自然")
            
            # Intervention 3D
            zi, yi, xi, ri = self._calculate_spine_coordinates(t['intervention']['metrics'], t['intervention']['curve_data'])
            ci = self._get_node_colors(ri, xi)
            trace_i = self._create_spine_traces(zi, yi, xi, ci, "常规")
            
            # Intensive 3D
            intensive_metrics = t.get('intensive', {}).get('metrics')
            if not intensive_metrics:
                intensive_metrics = t['control']['metrics']
            
            intensive_curve = t.get('intensive', {}).get('curve_data')
            if not intensive_curve:
                intensive_curve = t['control']['curve_data']

            zint, yint, xint, rint = self._calculate_spine_coordinates(intensive_metrics, intensive_curve)
            cint = self._get_node_colors(rint, xint)
            trace_int = self._create_spine_traces(zint, yint, xint, cint, "强化")

            frames.append(go.Frame(
                data=[
                    # 更新垂直线 (index 6)
                    go.Scatter(x=[time_val, time_val], y=[0, max_y]), 
                    # 更新 3D Control (index 7)
                    trace_c,
                    # 更新 3D Intervention (index 8)
                    trace_i,
                    # 更新 3D Intensive (index 9)
                    trace_int
                ],
                name=str(time_val),
                traces=[6, 7, 8, 9] 
            ))

        fig.frames = frames

        # --- 滑块与按钮 ---
        scene_camera = dict(eye=dict(x=1.8, y=1.8, z=1.8))
        common_scene_config = dict(
            xaxis=dict(range=[-100, 100], title='X'), 
            yaxis=dict(range=[-100, 100], title='Y'), 
            zaxis=dict(range=[0, 600], title='Z'), 
            aspectmode='manual', 
            aspectratio=dict(x=1, y=1, z=3), 
            camera=scene_camera
        )

        fig.update_scenes(patch=common_scene_config)

        fig.update_layout(
            title=f"脊柱治疗多维对比: {patient_name} (周期: {len(timeline)-1} {time_unit})",
            sliders=[{
                'steps': [{'method': 'animate', 'args': [[str(k)], {'mode': 'immediate', 'frame': {'duration': 100, 'redraw': True}, 'transition': {'duration': 0}}], 'label': str(k)} for k in weeks],
                'transition': {'duration': 0},
                'x': 0.1, 'len': 0.9,
                'currentvalue': {'prefix': f'{time_unit}: '}
            }],
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'x': 0.05,
                'buttons': [
                    {'label': '播放', 'method': 'animate', 'args': [None, {'frame': {'duration': 100, 'redraw': True}, 'fromcurrent': True, 'transition': {'duration': 0}}]},
                    {'label': '暂停', 'method': 'animate', 'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate', 'transition': {'duration': 0}}]}
                ]
            }]
        )
        return fig
