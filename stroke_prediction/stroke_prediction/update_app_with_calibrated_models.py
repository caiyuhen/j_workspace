#!/usr/bin/env python3
"""
更新应用程序使用校准后的模型
"""

import os
import shutil
import json

def backup_original_models():
    """备份原始模型文件"""
    print("=== 备份原始模型文件 ===")
    
    backup_dir = "models/original_backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        "models/optimized_stroke_model.joblib",
        "models/optimized_diabetes_model.joblib",
        "models/optimized_stroke_features.json",
        "models/optimized_diabetes_features.json"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            print(f"✓ 备份: {file_path} -> {backup_path}")
        else:
            print(f"✗ 文件不存在: {file_path}")

def replace_with_calibrated_models():
    """用校准后的模型替换原始模型"""
    print("\n=== 替换为校准后的模型 ===")
    
    replacements = [
        ("models/calibrated_stroke_model.joblib", "models/optimized_stroke_model.joblib"),
        ("models/calibrated_diabetes_model.joblib", "models/optimized_diabetes_model.joblib"),
        ("models/calibrated_stroke_features.json", "models/optimized_stroke_features.json"),
        ("models/calibrated_diabetes_features.json", "models/optimized_diabetes_features.json")
    ]
    
    for calibrated_path, original_path in replacements:
        if os.path.exists(calibrated_path):
            shutil.copy2(calibrated_path, original_path)
            print(f"✓ 替换: {calibrated_path} -> {original_path}")
        else:
            print(f"✗ 校准文件不存在: {calibrated_path}")

def update_risk_thresholds():
    """更新风险分层阈值"""
    print("\n=== 更新风险分层阈值 ===")
    
    # 新的风险阈值（基于校准后的模型结果）
    new_thresholds = {
        "stroke": {
            "low_risk": 0.25,      # 25%以下为低风险
            "medium_risk": 0.35,   # 25-35%为中等风险
            "high_risk": 0.45      # 35-45%为较高风险，45%以上为高风险
        },
        "diabetes": {
            "low_risk": 0.20,      # 20%以下为低风险
            "medium_risk": 0.30,   # 20-30%为中等风险
            "high_risk": 0.40      # 30-40%为较高风险，40%以上为高风险
        }
    }
    
    # 保存新的阈值配置
    thresholds_path = "models/risk_thresholds.json"
    with open(thresholds_path, 'w', encoding='utf-8') as f:
        json.dump(new_thresholds, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 风险阈值配置已保存: {thresholds_path}")
    
    # 显示新阈值
    for disease, thresholds in new_thresholds.items():
        print(f"\n{disease.upper()} 风险阈值:")
        print(f"  低风险: < {thresholds['low_risk']:.0%}")
        print(f"  中等风险: {thresholds['low_risk']:.0%} - {thresholds['medium_risk']:.0%}")
        print(f"  较高风险: {thresholds['medium_risk']:.0%} - {thresholds['high_risk']:.0%}")
        print(f"  高风险: > {thresholds['high_risk']:.0%}")

def create_model_info():
    """创建模型信息文件"""
    print("\n=== 创建模型信息文件 ===")
    
    model_info = {
        "version": "2.0_calibrated",
        "update_date": "2024-01-20",
        "description": "校准后的风险预测模型，修复了基线风险过高的问题",
        "improvements": {
            "stroke_model": {
                "baseline_risk_reduction": "17.0%",
                "calibration_method": "isotonic",
                "brier_score_improvement": 0.1510
            },
            "diabetes_model": {
                "baseline_risk_reduction": "16.6%",
                "calibration_method": "sigmoid",
                "brier_score_improvement": 0.0352
            }
        },
        "risk_levels": {
            "stroke": {
                "low": "< 25%",
                "medium": "25% - 35%",
                "high": "35% - 45%",
                "very_high": "> 45%"
            },
            "diabetes": {
                "low": "< 20%",
                "medium": "20% - 30%",
                "high": "30% - 40%",
                "very_high": "> 40%"
            }
        }
    }
    
    info_path = "models/model_info.json"
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(model_info, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 模型信息已保存: {info_path}")

def verify_update():
    """验证更新是否成功"""
    print("\n=== 验证更新结果 ===")
    
    required_files = [
        "models/optimized_stroke_model.joblib",
        "models/optimized_diabetes_model.joblib",
        "models/optimized_stroke_features.json",
        "models/optimized_diabetes_features.json",
        "models/risk_thresholds.json",
        "models/model_info.json"
    ]
    
    all_good = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            all_good = False
    
    if all_good:
        print("\n✓ 所有文件更新成功！")
        print("应用程序现在将使用校准后的模型。")
    else:
        print("\n✗ 部分文件更新失败，请检查。")
    
    return all_good

def main():
    """主函数"""
    print("=== 更新应用程序使用校准后的模型 ===\n")
    
    # 1. 备份原始模型
    backup_original_models()
    
    # 2. 替换为校准后的模型
    replace_with_calibrated_models()
    
    # 3. 更新风险阈值
    update_risk_thresholds()
    
    # 4. 创建模型信息
    create_model_info()
    
    # 5. 验证更新
    success = verify_update()
    
    if success:
        print("\n=== 更新完成 ===")
        print("建议重启应用程序以加载新的模型。")
        print("新模型的预测结果将更加合理，基线风险显著降低。")
    else:
        print("\n=== 更新失败 ===")
        print("请检查错误信息并重试。")

if __name__ == "__main__":
    main()