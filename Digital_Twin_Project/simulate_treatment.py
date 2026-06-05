import json
import numpy as np
import os
import copy

def simulate_treatment_timeseries(patient_name, treatment_plan, current_data_file, output_file):
    with open(current_data_file, 'r', encoding='utf-8') as f:
        all_patients = json.load(f)

    patient_data = next((p for p in all_patients if p['name'] == patient_name), None)
    if not patient_data:
        print(f"Patient {patient_name} not found.")
        return

    duration_months = treatment_plan.get('duration', 24) # 默认 2 年
    duration_weeks = duration_months * 4 # 转换为周
    compliance = treatment_plan.get('compliance', 0.8)
    treatment_type = treatment_plan.get('type', 'Brace')

    print(f"为 {patient_name} 模拟时间序列: {treatment_type} vs 自然发展, {duration_weeks} 周 ({duration_months} 月)")

    # 初始化序列
    timeseries_data = {
        "patient_name": patient_name,
        "treatment_plan": treatment_plan,
        "timeline": []
    }

    # 基础月增长率 (度/毫米 每月) -> 转换为周
    # 自然发展: 恶化
    natural_worsening_rate_deg_month = 0.5 
    natural_worsening_rate_deg_week = natural_worsening_rate_deg_month / 4.0
    
    # 干预: 改善 (净效应)
    if treatment_type == 'Brace':
        intervention_effect_deg_month = -0.8 * compliance # 强力矫正
    elif treatment_type == 'PT':
        intervention_effect_deg_month = -0.3 * compliance # 弱矫正
    elif treatment_type == 'Intensive':
        intervention_effect_deg_month = -1.5 * compliance # 强化康复: 非常强力的矫正
    else:
        intervention_effect_deg_month = 0
    
    intervention_effect_deg_week = intervention_effect_deg_month / 4.0

    # 初始状态
    current_metrics = patient_data['metrics']
    current_curve = patient_data['curve_data']

    # 模拟循环 (周)
    for week in range(duration_weeks + 1):
        week_data = {
            "week": week,
            "control": {},
            "intervention": {}
        }

        # --- 对照组 (自然发展) ---
        # 随时间恶化
        total_worsening = natural_worsening_rate_deg_week * week
        
        c_metrics = copy.deepcopy(current_metrics)
        c_curve = copy.deepcopy(current_curve)

        # 更新后凸/前凸
        c_metrics['kyphosis_max'] = max(10, c_metrics['kyphosis_max'] + total_worsening * 0.5)
        c_metrics['lordosis_max'] = max(10, c_metrics['lordosis_max'] + total_worsening * 0.5)

        # 更新旋转和偏移 (恶化因子 > 1.0)
        worsening_factor = 1.0 + (total_worsening / 100.0)
        c_curve['vertebral_rotation'] = [r * worsening_factor for r in c_curve['vertebral_rotation']]
        if c_curve['coronal_offsets']:
            c_curve['coronal_offsets'] = [o * worsening_factor for o in c_curve['coronal_offsets']]
        
        week_data['control'] = {'metrics': c_metrics, 'curve_data': c_curve}

        # --- 干预组 ---
        # 随时间改善
        total_improvement = intervention_effect_deg_week * week
        
        i_metrics = copy.deepcopy(current_metrics)
        i_curve = copy.deepcopy(current_curve)

        # 更新后凸/前凸
        i_metrics['kyphosis_max'] = max(10, i_metrics['kyphosis_max'] + total_improvement * 0.5)
        i_metrics['lordosis_max'] = max(10, i_metrics['lordosis_max'] + total_improvement * 0.5)

        # 更新旋转和偏移 (改善因子 < 1.0)
        # 注意: total_improvement 为负值，所以 (1 + neg) < 1
        # 对于强化康复，我们允许更积极的矫正
        improvement_factor = max(0.2, 1.0 + (total_improvement / 50.0)) # 改善上限为 80%
        i_curve['vertebral_rotation'] = [r * improvement_factor for r in i_curve['vertebral_rotation']]
        if i_curve['coronal_offsets']:
            i_curve['coronal_offsets'] = [o * improvement_factor for o in i_curve['coronal_offsets']]

        week_data['intervention'] = {'metrics': i_metrics, 'curve_data': i_curve}
        
        timeseries_data['timeline'].append(week_data)

    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(timeseries_data, f, ensure_ascii=False, indent=2)

    print(f"时间序列预测已保存至 {output_file}")

if __name__ == "__main__":
    input_file = r"d:\workspace\Digital_Twin_Project\parsed_spine_data.json"
    output_file = r"d:\workspace\Digital_Twin_Project\spine_prediction_timeseries.json"
    
    plan = {
        'type': 'Brace',
        'duration': 24, # 2 years
        'compliance': 0.9
    }
    
    simulate_treatment_timeseries("倪欣然", plan, input_file, output_file)
