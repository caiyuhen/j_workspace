<<<<<<< HEAD
import copy
import logging

class SimulationEngine:
    def __init__(self):
        self.logger = logging.getLogger("SimulationEngine")

    def run_simulation(self, patient_name, initial_state, treatment_plan):
        """
        根据初始状态和治疗方案执行脊柱演变模拟。
        
        参数:
            patient_name (str): 患者姓名
            initial_state (dict): 包含 'metrics' 和 'curve_data'
            treatment_plan (dict): 包含 'type', 'duration' (月), 'compliance' (依从性)
            
        返回:
            dict: 完整的时间序列数据结构
        """
        
        duration_months = treatment_plan.get('duration', 24) # 默认 2 年
        duration_weeks = duration_months * 4 # 转换为周
        compliance = treatment_plan.get('compliance', 0.8)
        treatment_type = treatment_plan.get('type', 'Brace')

        self.logger.info(f"正在模拟 {patient_name} 的时间序列: {treatment_type} vs 自然病程, {duration_weeks} 周 ({duration_months} 月)")

        # 初始化序列
        timeseries_data = {
            "patient_name": patient_name,
            "treatment_plan": treatment_plan,
            "timeline": []
        }

        # 基础月度变化率 (度/毫米 每月) -> 转换为每周
        # 自然病程: 恶化
        natural_worsening_rate_deg_month = 0.5 
        natural_worsening_rate_deg_week = natural_worsening_rate_deg_month / 4.0
        
        # --- 干预组 (Intervention) ---
        intervention_effect_deg_month = 0
        if treatment_type == 'Brace':
            intervention_effect_deg_month = -0.8 * compliance # 较强矫正
        elif treatment_type == 'PT':
            intervention_effect_deg_month = -0.3 * compliance # 较弱矫正
        elif treatment_type == 'Intensive':
            intervention_effect_deg_month = -1.5 * compliance # 强化康复
        
        intervention_effect_deg_week = intervention_effect_deg_month / 4.0

        # --- 强化组 (Intensive) ---
        # 假设强化组是高依从性 (0.95) 的同类型治疗，或者是更激进的方案
        intensive_compliance = 0.95
        intensive_effect_deg_month = 0
        if treatment_type == 'Brace':
             # 强化支具：可能每天佩戴时间更长，或者结合了 PT
            intensive_effect_deg_month = -1.2 * intensive_compliance 
        elif treatment_type == 'PT':
            intensive_effect_deg_month = -0.6 * intensive_compliance
        else:
             # 默认强化
            intensive_effect_deg_month = -1.8 * intensive_compliance

        intensive_effect_deg_week = intensive_effect_deg_month / 4.0

        # 初始状态
        current_metrics = initial_state['metrics']
        current_curve = initial_state['curve_data']

        # 模拟循环 (按周)
        for week in range(duration_weeks + 1):
            week_data = {
                "week": week,
                "control": {},
                "intervention": {},
                "intensive": {}
            }

            # --- 对照组 (自然病程) ---
            # 随时间恶化
            total_worsening = natural_worsening_rate_deg_week * week
            
            c_metrics = copy.deepcopy(current_metrics)
            c_curve = copy.deepcopy(current_curve)

            # 更新后凸/前凸
            c_metrics['kyphosis_max'] = max(10, c_metrics['kyphosis_max'] + total_worsening * 0.5)
            c_metrics['lordosis_max'] = max(10, c_metrics['lordosis_max'] + total_worsening * 0.5)
            
            # 更新 Cobb 角 (假设 Cobb 角也随恶化增加)
            c_metrics['cobb_angle'] = max(10, c_metrics['cobb_angle'] + total_worsening)

            # 更新旋转和偏移 (恶化因子 > 1.0)
            worsening_factor = 1.0 + (total_worsening / 50.0) # 加快恶化速度以便观察
            c_curve['vertebral_rotation'] = [r * worsening_factor for r in c_curve['vertebral_rotation']]
            if c_curve.get('coronal_offsets'):
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

            # 更新 Cobb 角
            i_metrics['cobb_angle'] = max(5, i_metrics['cobb_angle'] + total_improvement)

            # 更新旋转和偏移 (改善因子 < 1.0)
            improvement_factor = max(0.2, 1.0 + (total_improvement / 50.0)) 
            i_curve['vertebral_rotation'] = [r * improvement_factor for r in i_curve['vertebral_rotation']]
            if i_curve.get('coronal_offsets'):
                i_curve['coronal_offsets'] = [o * improvement_factor for o in i_curve['coronal_offsets']]
            
            week_data['intervention'] = {'metrics': i_metrics, 'curve_data': i_curve}

            # --- 强化组 (Intensive) ---
            total_intensive_imp = intensive_effect_deg_week * week
            
            int_metrics = copy.deepcopy(current_metrics)
            int_curve = copy.deepcopy(current_curve)
            
            int_metrics['kyphosis_max'] = max(10, int_metrics['kyphosis_max'] + total_intensive_imp * 0.5)
            int_metrics['lordosis_max'] = max(10, int_metrics['lordosis_max'] + total_intensive_imp * 0.5)
            int_metrics['cobb_angle'] = max(5, int_metrics['cobb_angle'] + total_intensive_imp)
            
            intensive_factor = max(0.1, 1.0 + (total_intensive_imp / 50.0))
            int_curve['vertebral_rotation'] = [r * intensive_factor for r in int_curve['vertebral_rotation']]
            if int_curve.get('coronal_offsets'):
                int_curve['coronal_offsets'] = [o * intensive_factor for o in int_curve['coronal_offsets']]
            
            week_data['intensive'] = {'metrics': int_metrics, 'curve_data': int_curve}

            timeseries_data['timeline'].append(week_data)
            
        return timeseries_data
=======
import copy
import logging

class SimulationEngine:
    def __init__(self):
        self.logger = logging.getLogger("SimulationEngine")

    def run_simulation(self, patient_name, initial_state, treatment_plan):
        """
        根据初始状态和治疗方案执行脊柱演变模拟。
        
        参数:
            patient_name (str): 患者姓名
            initial_state (dict): 包含 'metrics' 和 'curve_data'
            treatment_plan (dict): 包含 'type', 'duration' (月), 'compliance' (依从性)
            
        返回:
            dict: 完整的时间序列数据结构
        """
        
        duration_months = treatment_plan.get('duration', 24) # 默认 2 年
        duration_weeks = duration_months * 4 # 转换为周
        compliance = treatment_plan.get('compliance', 0.8)
        treatment_type = treatment_plan.get('type', 'Brace')

        self.logger.info(f"正在模拟 {patient_name} 的时间序列: {treatment_type} vs 自然病程, {duration_weeks} 周 ({duration_months} 月)")

        # 初始化序列
        timeseries_data = {
            "patient_name": patient_name,
            "treatment_plan": treatment_plan,
            "timeline": []
        }

        # 基础月度变化率 (度/毫米 每月) -> 转换为每周
        # 自然病程: 恶化
        natural_worsening_rate_deg_month = 0.5 
        natural_worsening_rate_deg_week = natural_worsening_rate_deg_month / 4.0
        
        # --- 干预组 (Intervention) ---
        intervention_effect_deg_month = 0
        if treatment_type == 'Brace':
            intervention_effect_deg_month = -0.8 * compliance # 较强矫正
        elif treatment_type == 'PT':
            intervention_effect_deg_month = -0.3 * compliance # 较弱矫正
        elif treatment_type == 'Intensive':
            intervention_effect_deg_month = -1.5 * compliance # 强化康复
        
        intervention_effect_deg_week = intervention_effect_deg_month / 4.0

        # --- 强化组 (Intensive) ---
        # 假设强化组是高依从性 (0.95) 的同类型治疗，或者是更激进的方案
        intensive_compliance = 0.95
        intensive_effect_deg_month = 0
        if treatment_type == 'Brace':
             # 强化支具：可能每天佩戴时间更长，或者结合了 PT
            intensive_effect_deg_month = -1.2 * intensive_compliance 
        elif treatment_type == 'PT':
            intensive_effect_deg_month = -0.6 * intensive_compliance
        else:
             # 默认强化
            intensive_effect_deg_month = -1.8 * intensive_compliance

        intensive_effect_deg_week = intensive_effect_deg_month / 4.0

        # 初始状态
        current_metrics = initial_state['metrics']
        current_curve = initial_state['curve_data']

        # 模拟循环 (按周)
        for week in range(duration_weeks + 1):
            week_data = {
                "week": week,
                "control": {},
                "intervention": {},
                "intensive": {}
            }

            # --- 对照组 (自然病程) ---
            # 随时间恶化
            total_worsening = natural_worsening_rate_deg_week * week
            
            c_metrics = copy.deepcopy(current_metrics)
            c_curve = copy.deepcopy(current_curve)

            # 更新后凸/前凸
            c_metrics['kyphosis_max'] = max(10, c_metrics['kyphosis_max'] + total_worsening * 0.5)
            c_metrics['lordosis_max'] = max(10, c_metrics['lordosis_max'] + total_worsening * 0.5)
            
            # 更新 Cobb 角 (假设 Cobb 角也随恶化增加)
            c_metrics['cobb_angle'] = max(10, c_metrics['cobb_angle'] + total_worsening)

            # 更新旋转和偏移 (恶化因子 > 1.0)
            worsening_factor = 1.0 + (total_worsening / 50.0) # 加快恶化速度以便观察
            c_curve['vertebral_rotation'] = [r * worsening_factor for r in c_curve['vertebral_rotation']]
            if c_curve.get('coronal_offsets'):
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

            # 更新 Cobb 角
            i_metrics['cobb_angle'] = max(5, i_metrics['cobb_angle'] + total_improvement)

            # 更新旋转和偏移 (改善因子 < 1.0)
            improvement_factor = max(0.2, 1.0 + (total_improvement / 50.0)) 
            i_curve['vertebral_rotation'] = [r * improvement_factor for r in i_curve['vertebral_rotation']]
            if i_curve.get('coronal_offsets'):
                i_curve['coronal_offsets'] = [o * improvement_factor for o in i_curve['coronal_offsets']]
            
            week_data['intervention'] = {'metrics': i_metrics, 'curve_data': i_curve}

            # --- 强化组 (Intensive) ---
            total_intensive_imp = intensive_effect_deg_week * week
            
            int_metrics = copy.deepcopy(current_metrics)
            int_curve = copy.deepcopy(current_curve)
            
            int_metrics['kyphosis_max'] = max(10, int_metrics['kyphosis_max'] + total_intensive_imp * 0.5)
            int_metrics['lordosis_max'] = max(10, int_metrics['lordosis_max'] + total_intensive_imp * 0.5)
            int_metrics['cobb_angle'] = max(5, int_metrics['cobb_angle'] + total_intensive_imp)
            
            intensive_factor = max(0.1, 1.0 + (total_intensive_imp / 50.0))
            int_curve['vertebral_rotation'] = [r * intensive_factor for r in int_curve['vertebral_rotation']]
            if int_curve.get('coronal_offsets'):
                int_curve['coronal_offsets'] = [o * intensive_factor for o in int_curve['coronal_offsets']]
            
            week_data['intensive'] = {'metrics': int_metrics, 'curve_data': int_curve}

            timeseries_data['timeline'].append(week_data)
            
        return timeseries_data
>>>>>>> origin/main
