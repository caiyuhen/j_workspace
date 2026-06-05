import json
import re
import os

def extract_numbers(text_list):
    numbers = []
    for text in text_list:
        # 从字符串如 "28°", "5.3mm" 中提取数字，如 28, 28.5, -5 等
        # matches = re.findall(r'([-+]?\d*\.\d+|\d+)', text)
        # 更好的正则以专门捕获 "28°" 或 "mm"
        
        # 清理特定的 OCR 伪影
        clean_text = text.replace(" ", "").replace("O", "0").replace("o", "0")
        
        # 查找度数值
        if "°" in text:
            vals = re.findall(r'([-+]?\d*\.\d+|\d+)', text)
            for v in vals:
                numbers.append({'type': 'angle', 'value': float(v), 'raw': text})
        
        # 查找 mm 值
        elif "mm" in text.lower():
            vals = re.findall(r'([-+]?\d*\.\d+|\d+)', text)
            for v in vals:
                numbers.append({'type': 'distance', 'value': float(v), 'raw': text})
                
    return numbers

def parse_spine_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    parsed_data = []

    for entry in raw_data:
        filename = entry['filename']
        patient_name = filename.replace('.pdf', '')
        
        patient_record = {
            'name': patient_name,
            'metrics': {
                'kyphosis_max': 0, # 胸椎曲线 (约 20-50 度)
                'lordosis_max': 0, # 腰椎曲线 (约 20-60 度)
                'coronal_offset_max': 0,
                'sagittal_offset_max': 0
            },
            'curve_data': {
                'coronal_offsets': [], # X 轴
                'sagittal_angles': [], # 用于 Y 轴重建
                'vertebral_rotation': []
            }
        }

        # --- 处理第 6 页 (全局指标) ---
        page_6 = entry.get('extracted_pages', {}).get('page_6', {}).get('text_content', [])
        
        # 简单启发式: 查找关键词并抓取后续行中找到的最近数字
        # 或者直接抓取所有数字并根据范围/上下文进行猜测。
        
        # 让我们尝试找到明确的键值对 (如果可能)，或者只是收集 "候选项"
        # 后凸通常在 20-50 左右
        # 前凸通常在 20-60 左右
        
        p6_str = "\n".join(page_6)
        
        # 尝试在整个页面文本块上使用正则查找特定值
        # 示例: "最大后凸角度... 28°"
        # 由于行被分割，我们在整个列表中搜索数字。
        
        angles = []
        distances = []
        for line in page_6:
            # 清理 OCR 错误
            line = line.replace(" ", "")
            
            # 查找度数
            deg_matches = re.findall(r'(\d+\.?\d*)°', line)
            for d in deg_matches:
                angles.append(float(d))
            
            # 查找 mm
            mm_matches = re.findall(r'(\d+\.?\d*)mm', line, re.IGNORECASE)
            for m in mm_matches:
                distances.append(float(m))
        
        # 全局指标的启发式方法
        if angles:
            # 通常前几个大角度是后凸/前凸
            # 后凸通常列在第一位或者是胸椎中较大的那个
            # 让我们取前两个大于 10 的有效角度作为后凸和前凸候选项
            valid_angles = [a for a in angles if 10 < a < 90]
            if len(valid_angles) >= 1:
                patient_record['metrics']['kyphosis_max'] = valid_angles[0]
            if len(valid_angles) >= 2:
                patient_record['metrics']['lordosis_max'] = valid_angles[1]
                
        if distances:
            # 最大距离可能是躯干偏移或类似
            patient_record['metrics']['coronal_offset_max'] = max(distances) if distances else 0

        # --- 处理第 7/8 页 (详细序列) ---
        # 我们需要 3D 模型的一系列点。
        # 如果我们找不到完美的序列，我们将根据全局指标生成一个。
        
        # 从第 7 和 8 页收集所有角度和 mm
        page_7 = entry.get('extracted_pages', {}).get('page_7', {}).get('text_content', [])
        page_8 = entry.get('extracted_pages', {}).get('page_8', {}).get('text_content', [])
        
        all_series_lines = page_7 + page_8
        series_angles = []
        series_mm = []
        
        for line in all_series_lines:
             # 查找度数 (通常是每层的旋转或柯布角)
            line = line.replace(" ", "").replace("O", "0")
            deg_matches = re.findall(r'([-+]?\d+\.?\d*)°', line)
            for d in deg_matches:
                series_angles.append(float(d))
            
            # 查找 mm (偏移)
            mm_matches = re.findall(r'([-+]?\d+\.?\d*)mm', line, re.IGNORECASE)
            for m in mm_matches:
                series_mm.append(float(m))
        
        # 如果我们找到大量数据点 (例如 > 10)，则存储它们
        if len(series_mm) > 5:
            patient_record['curve_data']['coronal_offsets'] = series_mm[:17] # 限制为约 17 个椎骨 (T1-L5)
        
        if len(series_angles) > 5:
            patient_record['curve_data']['vertebral_rotation'] = series_angles[:17]

        parsed_data.append(patient_record)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
    
    print(f"已保存 {len(parsed_data)} 名患者的解析数据至 {output_file}")

if __name__ == "__main__":
    input_json = r"d:\workspace\Digital_Twin_Project\extracted_data.json"
    output_json = r"d:\workspace\Digital_Twin_Project\parsed_spine_data.json"
    parse_spine_data(input_json, output_json)
