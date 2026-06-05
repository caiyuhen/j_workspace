#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试模型加载问题
"""

import joblib
import os

def debug_models():
    """调试模型加载问题"""
    print("=== 调试模型加载问题 ===")
    
    # 检查fast_recall_optimized_models目录
    model_dirs = [d for d in os.listdir('.') if d.startswith('fast_recall_optimized_models_')]
    print(f"找到的模型目录: {model_dirs}")
    
    if model_dirs:
        model_dir = model_dirs[0]
        print(f"\n检查目录: {model_dir}")
        
        # 列出目录中的文件
        files = os.listdir(model_dir)
        print(f"目录中的文件: {files}")
        
        # 检查阈值文件
        threshold_path = os.path.join(model_dir, 'best_thresholds.joblib')
        print(f"\n阈值文件存在: {os.path.exists(threshold_path)}")
        
        if os.path.exists(threshold_path):
            try:
                thresholds = joblib.load(threshold_path)
                print(f"阈值类型: {type(thresholds)}")
                print(f"阈值内容: {thresholds}")
            except Exception as e:
                print(f"加载阈值文件失败: {e}")
        
        # 检查几个模型文件
        diseases = ['stroke', 'diabetes', 'hypertension']
        for disease in diseases:
            model_path = os.path.join(model_dir, f'{disease}_model.joblib')
            if os.path.exists(model_path):
                try:
                    model = joblib.load(model_path)
                    print(f"\n{disease} 模型:")
                    print(f"  类型: {type(model)}")
                    print(f"  类名: {model.__class__.__name__}")
                    print(f"  有predict_proba: {hasattr(model, 'predict_proba')}")
                    
                    # 如果是字典，打印内容
                    if isinstance(model, dict):
                        print(f"  字典键: {list(model.keys())}")
                        for key, value in model.items():
                            print(f"    {key}: {type(value)}")
                            if hasattr(value, 'predict_proba'):
                                print(f"      {key} 有predict_proba方法")
                    
                except Exception as e:
                    print(f"  加载失败: {e}")
            else:
                print(f"\n{disease} 模型文件不存在: {model_path}")
    
    # 检查fine_tuned_models目录
    fine_tuned_dirs = [d for d in os.listdir('.') if d.startswith('fine_tuned_models_')]
    print(f"\n找到的fine_tuned目录: {fine_tuned_dirs}")
    
    if fine_tuned_dirs:
        model_dir = fine_tuned_dirs[0]
        print(f"\n检查fine_tuned目录: {model_dir}")
        
        # 检查几个模型文件
        for disease in diseases:
            model_path = os.path.join(model_dir, f'{disease}_model.joblib')
            if os.path.exists(model_path):
                try:
                    model = joblib.load(model_path)
                    print(f"\n{disease} fine_tuned模型:")
                    print(f"  类型: {type(model)}")
                    print(f"  类名: {model.__class__.__name__}")
                    print(f"  有predict_proba: {hasattr(model, 'predict_proba')}")
                    
                    # 如果是字典，打印内容
                    if isinstance(model, dict):
                        print(f"  字典键: {list(model.keys())}")
                        for key, value in model.items():
                            print(f"    {key}: {type(value)}")
                            if hasattr(value, 'predict_proba'):
                                print(f"      {key} 有predict_proba方法")
                    
                except Exception as e:
                    print(f"  加载失败: {e}")

if __name__ == "__main__":
    debug_models()