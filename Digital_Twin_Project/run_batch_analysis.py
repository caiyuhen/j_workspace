import json
import os
import sys

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from simulate_treatment import simulate_treatment_timeseries
    from visualize_spine_evolution import visualize_evolution
except ImportError as e:
    print(f"导入模块时出错: {e}")
    print("请确保 simulate_treatment.py 和 visualize_spine_evolution.py 在同一目录下。")
    sys.exit(1)

def run_batch_analysis():
    # 配置
    input_data_file = r"d:\workspace\Digital_Twin_Project\parsed_spine_data.json"
    timeseries_dir = r"d:\workspace\Digital_Twin_Project\timeseries_output"
    output_dir = r"d:\workspace\Digital_Twin_Project\output"

    # 确保目录存在
    if not os.path.exists(timeseries_dir):
        os.makedirs(timeseries_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 加载患者数据
    if not os.path.exists(input_data_file):
        print(f"错误: 未找到输入文件 {input_data_file}。")
        return

    with open(input_data_file, 'r', encoding='utf-8') as f:
        all_patients = json.load(f)

    print(f"找到 {len(all_patients)} 名患者。开始批量分析...")

    # 批量分析的默认治疗计划
    default_plan = {
        'type': 'Brace',       # 默认为支具干预
        'duration': 24,        # 2 年
        'compliance': 0.9      # 90% 依从性
    }

    success_count = 0
    error_count = 0

    for patient in all_patients:
        name = patient.get('name', 'Unknown')
        print(f"\n--- 正在处理患者: {name} ---")

        try:
            # 1. 模拟治疗 (生成时间序列)
            timeseries_file = os.path.join(timeseries_dir, f"{name}_timeseries.json")
            simulate_treatment_timeseries(name, default_plan, input_data_file, timeseries_file)

            # 2. 可视化演变 (生成 HTML)
            visualize_evolution(timeseries_file, output_dir)
            
            success_count += 1
            
        except Exception as e:
            print(f"处理 {name} 时出错: {str(e)}")
            error_count += 1

    print("\n" + "="*30)
    print(f"批量分析完成。")
    print(f"成功处理: {success_count}")
    print(f"错误: {error_count}")
    print(f"输出目录: {output_dir}")
    print("="*30)

if __name__ == "__main__":
    run_batch_analysis()
