<<<<<<< HEAD
import json
import numpy as np
import plotly.graph_objects as go
import os

def generate_spine_model(data_file, output_dir):
    with open(data_file, 'r', encoding='utf-8') as f:
        patients = json.load(f)

    for patient in patients:
        name = patient['name']
        metrics = patient['metrics']
        curve_data = patient['curve_data']
        
        # --- 生成脊柱几何结构 ---
        # 定义层级 (近似: L5 到 T1)
        # 5 个腰椎 + 12 个胸椎 = 17 个层级
        levels = ['L5', 'L4', 'L3', 'L2', 'L1', 
                  'T12', 'T11', 'T10', 'T9', 'T8', 'T7', 'T6', 'T5', 'T4', 'T3', 'T2', 'T1']
        
        n_levels = len(levels)
        z_coords = np.linspace(0, n_levels * 25, n_levels) # 每层约 25mm
        
        # 矢状面轮廓 (Y 轴)
        # 模拟前凸 (L5-T12) 和后凸 (T12-T1)
        # 使用由最大角度调制的简单正弦波
        # 归一化 Z 从 0 到 1
        z_norm = z_coords / z_coords.max()
        
        # 基于角度的振幅 (启发式: 1 度 ~ 1mm 深度用于可视化)
        # 前凸通常在底部 (腰椎), 后凸在顶部 (胸椎)
        # 简单的 S 曲线: -sin(2*pi*z)
        # 我们希望底部是前凸 (向前凸出 -> +Y)?
        # 实际上前凸是向前凸出。后凸是向后凸出。
        # 假设 +Y 是前侧。
        # 腰椎: y > 0. 胸椎: y < 0.
        
        lordosis_amp = metrics.get('lordosis_max', 30)
        kyphosis_amp = metrics.get('kyphosis_max', 40)
        
        # 创建平滑的 S 曲线
        # 下部 (腰椎, z_norm 0 到 0.4): 正向凸起
        # 上部 (胸椎, z_norm 0.4 到 1.0): 负向凸起
        
        y_coords = []
        for z in z_norm:
            if z < 0.35: # 腰椎区域
                # 前凸的抛物线或正弦片段
                # 峰值约在 z=0.15
                val = lordosis_amp * np.sin(z / 0.35 * np.pi) 
            else: # 胸椎区域
                # 后凸的正弦片段
                # 峰值约在 z=0.7
                val = -kyphosis_amp * np.sin((z - 0.35) / 0.65 * np.pi)
            y_coords.append(val)
            
        y_coords = np.array(y_coords)

        # 轴向旋转和冠状面偏移 (X 轴)
        rotations = curve_data.get('vertebral_rotation', [])
        
        # 如果计数不同，插值旋转以匹配 n_levels
        if not rotations:
            rotations = [0] * n_levels
        else:
            # 简单插值
            orig_indices = np.linspace(0, n_levels-1, len(rotations))
            target_indices = np.arange(n_levels)
            rotations = np.interp(target_indices, orig_indices, rotations)
            
        # X 坐标: 源自冠状面偏移或旋转耦合
        # 如果 coronal_offsets 为空，使用旋转模拟脊柱侧弯
        coronal_offsets = curve_data.get('coronal_offsets', [])
        if not coronal_offsets:
             # 启发式: 旋转通常伴随侧向偏离
             # 1 度旋转 ~ 0.5mm 偏离?
             x_coords = -np.array(rotations) * 0.5 
        else:
            # 如果需要则插值
            if len(coronal_offsets) != n_levels:
                orig_indices = np.linspace(0, n_levels-1, len(coronal_offsets))
                x_coords = np.interp(target_indices, orig_indices, coronal_offsets)
            else:
                x_coords = np.array(coronal_offsets)

        # --- 基于健康的颜色逻辑 ---
        # "不健康"的阈值:
        # 旋转 > 5 度
        # 冠状面偏移 > 10mm (任意视觉阈值)
        
        node_colors = []
        node_status = []
        
        for rot, off in zip(rotations, x_coords):
            is_unhealthy = False
            status_text = "正常"
            
            if abs(rot) > 5:
                is_unhealthy = True
                status_text = f"旋转: {rot:.1f}°"
            
            if abs(off) > 10:
                is_unhealthy = True
                status_text += f" | 偏移: {off:.1f}mm"
                
            if is_unhealthy:
                node_colors.append('red')
                node_status.append(f"异常 ({status_text})")
            else:
                node_colors.append('green')
                node_status.append("正常")

        # --- 验证检查 ---
        print(f"\n--- {name} 的验证 ---")
        print(f"源数据 (提取): 后凸={metrics.get('kyphosis_max')}, 前凸={metrics.get('lordosis_max')}")
        rot_max = max(rotations, key=abs) if len(rotations)>0 else 0
        print(f"源数据 (提取): 最大旋转={rot_max}")
        print(f"模型数据 (生成): Y 范围=[{y_coords.min():.2f}, {y_coords.max():.2f}] (与后凸/前凸一致)")
        print(f"模型数据 (生成): X 范围=[{x_coords.min():.2f}, {x_coords.max():.2f}] (源自旋转/偏移)")
        
        abnormal_count = node_colors.count('red')
        print(f"健康状态: 检测到 {abnormal_count} 个异常椎骨。")

        # --- 绘图 ---
        fig = go.Figure()

        # 1. 脊柱曲线
        fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='markers+lines',
            marker=dict(
                size=10,
                color=z_coords,
                colorscale='Viridis',
                symbol='diamond',
                opacity=0.9
            ),
            line=dict(
                color='darkblue',
                width=5
            ),
            name='脊柱骨格'
        ))

        # 2. 椎骨标记 (球体)
        # 我们需要为每种颜色添加轨迹或使用标记颜色数组
        fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='markers+text',
            marker=dict(size=10, color=node_colors), # 使用动态颜色
            text=[f"{l}<br>{s}" for l, s in zip(levels, node_status)], # 将状态添加到标签
            textposition="middle right",
            name='椎体中心'
        ))

        # 3. 代表旋转的方向向量 (圆锥)
        # 默认向量 (0 度) 指向前侧 (+Y)
        # 旋转向量: x = sin(theta), y = cos(theta)
        # theta 以度为单位。+旋转通常意味着向左还是向右?
        # 假设 +旋转 = 逆时针 (左) -> X < 0
        
        rads = np.radians(rotations)
        u = -np.sin(rads) # X 分量
        v = np.cos(rads)  # Y 分量
        w = np.zeros_like(rads) # Z 分量 (平坦)

        fig.add_trace(go.Cone(
            x=x_coords, y=y_coords, z=z_coords,
            u=u, v=v, w=w,
            sizemode="absolute",
            sizeref=20,
            anchor="tail",
            colorscale='Viridis',
            showscale=False,
            name='旋转方向'
        ))

        # 布局
        fig.update_layout(
            title=f"数字孪生: 脊柱模型 - {name}",
            scene=dict(
                xaxis=dict(range=[-200, 200], title='冠状面 (X) [mm]'),
                yaxis=dict(range=[-200, 200], title='矢状面 (Y) [mm]'),
                zaxis=dict(range=[0, 600], title='轴向 (Z) [mm]'),
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=1.5)
            ),
            margin=dict(l=0, r=0, b=0, t=40)
        )

        output_path = os.path.join(output_dir, f"{name}_spine_model.html")
        fig.write_html(output_path)
        print(f"为 {name} 生成模型: {output_path}")

if __name__ == "__main__":
    data_file = r"d:\workspace\Digital_Twin_Project\parsed_spine_data.json"
    output_dir = r"d:\workspace\Digital_Twin_Project\output"
    
    # 检查预测数据
    predicted_file = r"d:\workspace\Digital_Twin_Project\predicted_spine_data.json"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    generate_spine_model(data_file, output_dir)
    
    if os.path.exists(predicted_file):
        print("\n--- 正在生成预测模型 ---")
        generate_spine_model(predicted_file, output_dir)
=======
import json
import numpy as np
import plotly.graph_objects as go
import os

def generate_spine_model(data_file, output_dir):
    with open(data_file, 'r', encoding='utf-8') as f:
        patients = json.load(f)

    for patient in patients:
        name = patient['name']
        metrics = patient['metrics']
        curve_data = patient['curve_data']
        
        # --- 生成脊柱几何结构 ---
        # 定义层级 (近似: L5 到 T1)
        # 5 个腰椎 + 12 个胸椎 = 17 个层级
        levels = ['L5', 'L4', 'L3', 'L2', 'L1', 
                  'T12', 'T11', 'T10', 'T9', 'T8', 'T7', 'T6', 'T5', 'T4', 'T3', 'T2', 'T1']
        
        n_levels = len(levels)
        z_coords = np.linspace(0, n_levels * 25, n_levels) # 每层约 25mm
        
        # 矢状面轮廓 (Y 轴)
        # 模拟前凸 (L5-T12) 和后凸 (T12-T1)
        # 使用由最大角度调制的简单正弦波
        # 归一化 Z 从 0 到 1
        z_norm = z_coords / z_coords.max()
        
        # 基于角度的振幅 (启发式: 1 度 ~ 1mm 深度用于可视化)
        # 前凸通常在底部 (腰椎), 后凸在顶部 (胸椎)
        # 简单的 S 曲线: -sin(2*pi*z)
        # 我们希望底部是前凸 (向前凸出 -> +Y)?
        # 实际上前凸是向前凸出。后凸是向后凸出。
        # 假设 +Y 是前侧。
        # 腰椎: y > 0. 胸椎: y < 0.
        
        lordosis_amp = metrics.get('lordosis_max', 30)
        kyphosis_amp = metrics.get('kyphosis_max', 40)
        
        # 创建平滑的 S 曲线
        # 下部 (腰椎, z_norm 0 到 0.4): 正向凸起
        # 上部 (胸椎, z_norm 0.4 到 1.0): 负向凸起
        
        y_coords = []
        for z in z_norm:
            if z < 0.35: # 腰椎区域
                # 前凸的抛物线或正弦片段
                # 峰值约在 z=0.15
                val = lordosis_amp * np.sin(z / 0.35 * np.pi) 
            else: # 胸椎区域
                # 后凸的正弦片段
                # 峰值约在 z=0.7
                val = -kyphosis_amp * np.sin((z - 0.35) / 0.65 * np.pi)
            y_coords.append(val)
            
        y_coords = np.array(y_coords)

        # 轴向旋转和冠状面偏移 (X 轴)
        rotations = curve_data.get('vertebral_rotation', [])
        
        # 如果计数不同，插值旋转以匹配 n_levels
        if not rotations:
            rotations = [0] * n_levels
        else:
            # 简单插值
            orig_indices = np.linspace(0, n_levels-1, len(rotations))
            target_indices = np.arange(n_levels)
            rotations = np.interp(target_indices, orig_indices, rotations)
            
        # X 坐标: 源自冠状面偏移或旋转耦合
        # 如果 coronal_offsets 为空，使用旋转模拟脊柱侧弯
        coronal_offsets = curve_data.get('coronal_offsets', [])
        if not coronal_offsets:
             # 启发式: 旋转通常伴随侧向偏离
             # 1 度旋转 ~ 0.5mm 偏离?
             x_coords = -np.array(rotations) * 0.5 
        else:
            # 如果需要则插值
            if len(coronal_offsets) != n_levels:
                orig_indices = np.linspace(0, n_levels-1, len(coronal_offsets))
                x_coords = np.interp(target_indices, orig_indices, coronal_offsets)
            else:
                x_coords = np.array(coronal_offsets)

        # --- 基于健康的颜色逻辑 ---
        # "不健康"的阈值:
        # 旋转 > 5 度
        # 冠状面偏移 > 10mm (任意视觉阈值)
        
        node_colors = []
        node_status = []
        
        for rot, off in zip(rotations, x_coords):
            is_unhealthy = False
            status_text = "正常"
            
            if abs(rot) > 5:
                is_unhealthy = True
                status_text = f"旋转: {rot:.1f}°"
            
            if abs(off) > 10:
                is_unhealthy = True
                status_text += f" | 偏移: {off:.1f}mm"
                
            if is_unhealthy:
                node_colors.append('red')
                node_status.append(f"异常 ({status_text})")
            else:
                node_colors.append('green')
                node_status.append("正常")

        # --- 验证检查 ---
        print(f"\n--- {name} 的验证 ---")
        print(f"源数据 (提取): 后凸={metrics.get('kyphosis_max')}, 前凸={metrics.get('lordosis_max')}")
        rot_max = max(rotations, key=abs) if len(rotations)>0 else 0
        print(f"源数据 (提取): 最大旋转={rot_max}")
        print(f"模型数据 (生成): Y 范围=[{y_coords.min():.2f}, {y_coords.max():.2f}] (与后凸/前凸一致)")
        print(f"模型数据 (生成): X 范围=[{x_coords.min():.2f}, {x_coords.max():.2f}] (源自旋转/偏移)")
        
        abnormal_count = node_colors.count('red')
        print(f"健康状态: 检测到 {abnormal_count} 个异常椎骨。")

        # --- 绘图 ---
        fig = go.Figure()

        # 1. 脊柱曲线
        fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='markers+lines',
            marker=dict(
                size=10,
                color=z_coords,
                colorscale='Viridis',
                symbol='diamond',
                opacity=0.9
            ),
            line=dict(
                color='darkblue',
                width=5
            ),
            name='脊柱骨格'
        ))

        # 2. 椎骨标记 (球体)
        # 我们需要为每种颜色添加轨迹或使用标记颜色数组
        fig.add_trace(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='markers+text',
            marker=dict(size=10, color=node_colors), # 使用动态颜色
            text=[f"{l}<br>{s}" for l, s in zip(levels, node_status)], # 将状态添加到标签
            textposition="middle right",
            name='椎体中心'
        ))

        # 3. 代表旋转的方向向量 (圆锥)
        # 默认向量 (0 度) 指向前侧 (+Y)
        # 旋转向量: x = sin(theta), y = cos(theta)
        # theta 以度为单位。+旋转通常意味着向左还是向右?
        # 假设 +旋转 = 逆时针 (左) -> X < 0
        
        rads = np.radians(rotations)
        u = -np.sin(rads) # X 分量
        v = np.cos(rads)  # Y 分量
        w = np.zeros_like(rads) # Z 分量 (平坦)

        fig.add_trace(go.Cone(
            x=x_coords, y=y_coords, z=z_coords,
            u=u, v=v, w=w,
            sizemode="absolute",
            sizeref=20,
            anchor="tail",
            colorscale='Viridis',
            showscale=False,
            name='旋转方向'
        ))

        # 布局
        fig.update_layout(
            title=f"数字孪生: 脊柱模型 - {name}",
            scene=dict(
                xaxis=dict(range=[-200, 200], title='冠状面 (X) [mm]'),
                yaxis=dict(range=[-200, 200], title='矢状面 (Y) [mm]'),
                zaxis=dict(range=[0, 600], title='轴向 (Z) [mm]'),
                aspectmode='manual',
                aspectratio=dict(x=1, y=1, z=1.5)
            ),
            margin=dict(l=0, r=0, b=0, t=40)
        )

        output_path = os.path.join(output_dir, f"{name}_spine_model.html")
        fig.write_html(output_path)
        print(f"为 {name} 生成模型: {output_path}")

if __name__ == "__main__":
    data_file = r"d:\workspace\Digital_Twin_Project\parsed_spine_data.json"
    output_dir = r"d:\workspace\Digital_Twin_Project\output"
    
    # 检查预测数据
    predicted_file = r"d:\workspace\Digital_Twin_Project\predicted_spine_data.json"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    generate_spine_model(data_file, output_dir)
    
    if os.path.exists(predicted_file):
        print("\n--- 正在生成预测模型 ---")
        generate_spine_model(predicted_file, output_dir)
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
