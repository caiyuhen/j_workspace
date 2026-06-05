import json
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from simulate_treatment import simulate_treatment_timeseries
    from visualize_spine_evolution import visualize_evolution
except ImportError as e:
    print(f"导入模块时出错: {e}")
    sys.exit(1)

def run_intensive_demo():
    patient_name = "倪欣然"
    input_data_file = r"d:\workspace\Digital_Twin_Project\parsed_spine_data.json"
    timeseries_dir = r"d:\workspace\Digital_Twin_Project\timeseries_output"
    output_dir = r"d:\workspace\Digital_Twin_Project\output"

    # 定义强化治疗计划
    intensive_plan = {
        'type': 'Intensive',   # 新的强化模式
        'duration': 24,        # 2 年
        'compliance': 0.95     # 非常高的依从性
    }

    print(f"正在为 {patient_name} 生成强化治疗演示...")

    # 1. 模拟
    # 注意: 我们在文件名后添加 '_intensive' 以区别于标准支具模型
    timeseries_file = os.path.join(timeseries_dir, f"{patient_name}_intensive_timeseries.json")
    simulate_treatment_timeseries(patient_name, intensive_plan, input_data_file, timeseries_file)

    # 2. 可视化
    # 可视化器根据输入文件名生成文件。
    # 它将被命名为 "{patient_name}_intensive_evolution_viz.html"
    visualize_evolution(timeseries_file, output_dir)

    print(f"\n演示生成成功。")
    print(f"可视化: {os.path.join(output_dir, f'{patient_name}_intensive_evolution_viz.html')}")

if __name__ == "__main__":
    run_intensive_demo()
