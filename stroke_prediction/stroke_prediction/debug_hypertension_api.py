#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试Flask API中高血压模型的特征处理
"""

import requests
import json
import numpy as np

def debug_hypertension_api():
    """调试高血压API预测"""
    print("=== 调试高血压API预测 ===")
    
    # 正常血压样本 - 应该被识别为低风险
    normal_bp_data = {
        'age': '30',
        'gender': '0',
        'bmi': '22.0',
        'systolic_bp': '110',  # 正常血压
        'diastolic_bp': '70',  # 正常血压
        'avg_glucose_level': '90',
        'smoking_status': '0',
        'work_type': '1',
        'residence_type': '1',
        'ever_married': '1',
        'heart_rate': '70',
        'exercise_frequency': '4',  # 经常运动
        'sleep_hours': '8',
        'stress_level': '1',  # 低压力
        'alcohol_consumption': '0',  # 不喝酒
        'diet_quality': '4',  # 好的饮食
        'heart_disease': '0',
        'family_history': '0',  # 无家族史
        'medication_count': '0',
        'memory_score': '9',
        'cognitive_score': '95',
        'education_level': '4',
        'creatinine': '0.8',
        'bun': '12',
        'cholesterol': '180',
        'triglycerides': '120',
        'uric_acid': '4.5',
        'seafood_consumption': '2',
        'beer_consumption': '0',
        'air_quality': '1',  # 优秀空气质量
        'season': 'spring'
    }
    
    print("发送正常血压样本...")
    print(f"输入数据: {json.dumps(normal_bp_data, indent=2, ensure_ascii=False)}")
    
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post('http://127.0.0.1:5008/api/predict', 
                               json=normal_bp_data, 
                               headers=headers, 
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'predictions' in result and 'hypertension' in result['predictions']:
                hypertension_result = result['predictions']['hypertension']
                print(f"\n高血压预测结果:")
                print(f"  概率: {hypertension_result.get('probability', '未知'):.4f}")
                print(f"  预测: {hypertension_result.get('prediction', '未知')}")
                print(f"  风险等级: {hypertension_result.get('risk_level', '未知')}")
                print(f"  使用的模型: {hypertension_result.get('model_used', '未知')}")
                print(f"  使用的特征数: {hypertension_result.get('features_used', '未知')}")
                
                # 分析问题
                prob = hypertension_result.get('probability', 1.0)
                if prob > 0.5:
                    print(f"\n❌ 问题: 正常血压样本被错误识别为高风险 (概率: {prob:.4f})")
                    print("可能原因:")
                    print("1. 模型使用了错误的特征映射")
                    print("2. 特征标准化有问题")
                    print("3. 模型本身有问题")
                else:
                    print(f"\n✅ 正确: 正常血压样本被识别为低风险 (概率: {prob:.4f})")
                
                return hypertension_result
            else:
                print("响应中没有高血压预测结果")
                print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return None
        else:
            print(f"API请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"API调试失败: {e}")
        return None

def test_direct_model():
    """直接测试模型文件"""
    print("\n=== 直接测试模型文件 ===")
    
    import joblib
    
    try:
        # 加载模型和标准化器
        model = joblib.load('models/optimized_hypertension_target_model.joblib')
        scaler = joblib.load('models/optimized_hypertension_target_scaler.joblib')
        
        # 加载特征配置
        with open('models/optimized_hypertension_target_features.json', 'r', encoding='utf-8') as f:
            features_config = json.load(f)
        
        selected_features = features_config['selected_features']
        print(f"模型期望的特征: {selected_features}")
        print(f"特征数量: {len(selected_features)}")
        
        # 构建正常血压样本的特征向量
        # 根据特征配置映射输入数据
        feature_mapping = {
            'age': 30,
            'systolic_bp': 110,  # 正常血压
            'cholesterol_level': 180,  # 正常胆固醇
            'alcohol_consumption': 0,  # 不喝酒
            'diabetes_duration': 0,  # 无糖尿病
            'liver_function': 1,  # 正常肝功能
            'stress_level': 1,  # 低压力
            'diastolic_bp': 70,  # 正常血压
            'avg_glucose_level': 90,  # 正常血糖
            'medication_adherence': 1,  # 良好用药依从性
            'hba1c_level': 5.5,  # 正常糖化血红蛋白
            'sleep_hours': 8,  # 充足睡眠
            'bmi': 22.0,  # 正常BMI
            'kidney_function': 1,  # 正常肾功能
            'ever_married': 1  # 已婚
        }
        
        # 构建特征向量
        feature_values = []
        for feature in selected_features:
            value = feature_mapping.get(feature, 0)
            feature_values.append(value)
        
        features = np.array(feature_values).reshape(1, -1)
        print(f"构建的特征向量: {features}")
        print(f"特征向量形状: {features.shape}")
        
        # 标准化
        features_scaled = scaler.transform(features)
        print(f"标准化后的特征: {features_scaled}")
        
        # 预测
        prob = model.predict_proba(features_scaled)[0, 1]
        pred = model.predict(features_scaled)[0]
        
        print(f"直接模型预测:")
        print(f"  概率: {prob:.4f}")
        print(f"  预测: {pred}")
        
        if prob < 0.4:
            print("✅ 直接模型正确识别为低风险")
        else:
            print("❌ 直接模型错误识别为高风险")
            
        return prob, pred
        
    except Exception as e:
        print(f"直接模型测试失败: {e}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        return None, None

if __name__ == "__main__":
    print("开始调试高血压API...")
    
    # 测试API
    api_result = debug_hypertension_api()
    
    # 直接测试模型
    direct_prob, direct_pred = test_direct_model()
    
    # 比较结果
    if api_result and direct_prob is not None:
        api_prob = api_result.get('probability', 0)
        print(f"\n=== 结果比较 ===")
        print(f"API预测概率: {api_prob:.4f}")
        print(f"直接模型概率: {direct_prob:.4f}")
        print(f"概率差异: {abs(api_prob - direct_prob):.4f}")
        
        if abs(api_prob - direct_prob) > 0.01:
            print("❌ API和直接模型结果不一致，存在特征处理问题")
        else:
            print("✅ API和直接模型结果一致")