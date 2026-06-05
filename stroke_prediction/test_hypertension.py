#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_hypertension_prediction():
    """测试高血压风险预测"""
    
    # 测试数据 - 高风险患者
    test_data = {
        'age': 65,
        'gender': 1,  # 男性
        'hypertension': 0,  # 当前没有高血压
        'heart_disease': 0,
        'ever_married': 1,
        'work_type': 2,
        'Residence_type': 1,
        'avg_glucose_level': 150,
        'bmi': 30,
        'smoking_status': 2,
        'systolic_bp': 160,  # 高收缩压
        'diastolic_bp': 95,  # 高舒张压
        'cholesterol': 250,
        'exercise_frequency': 1,
        'alcohol_consumption': 2,
        'stress_level': 4,
        'sleep_hours': 5,
        'family_history_stroke': 1,
        'family_history_hypertension': 1,  # 家族高血压史
        'medication_adherence': 2,
        'previous_stroke': 0,
        'physical_activity': 1,
        'diet_quality': 2,
        'social_support': 3,
        'depression_score': 3,
        'anxiety_score': 3,
        'cognitive_status': 1,
        'mobility_status': 1,
        'vision_problems': 0,
        'hearing_problems': 0,
        'chronic_kidney_disease': 0
    }

    try:
        print("正在测试高血压风险预测...")
        response = requests.post('http://127.0.0.1:5008/predict', json=test_data)
        
        if response.status_code != 200:
            print(f"HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
            
        result = response.json()
        print('预测结果:')
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 重点检查高血压预测
        if 'predictions' in result:
            hypertension_pred = result['predictions'].get('hypertension')
            
            if hypertension_pred:
                print(f'\n高血压预测详情:')
                print(f'疾病: {hypertension_pred["disease_name"]}')
                print(f'风险概率: {hypertension_pred["probability"]:.4f}')
                print(f'预测结果: {hypertension_pred["prediction"]}')
                print(f'风险等级: {hypertension_pred["risk_level"]}')
                
                # 分析预测是否合理
                prob = hypertension_pred["probability"]
                prediction = hypertension_pred["prediction"]
                
                print(f'\n预测分析:')
                print(f'患者特征: 65岁男性，收缩压160，舒张压95，BMI30，家族高血压史')
                print(f'预测概率: {prob:.4f} ({prob*100:.2f}%)')
                print(f'预测结果: {"高风险" if prediction == 1 else "低风险"}')
                
                # 判断预测是否合理
                if prob > 0.5 and prediction == 1:
                    print('✓ 预测结果合理 - 高风险特征应该预测为高风险')
                elif prob <= 0.5 and prediction == 0:
                    print('✓ 预测结果合理 - 低风险特征预测为低风险')
                else:
                    print('⚠ 预测结果可能有问题 - 概率与预测结果不一致')
                    
            else:
                print('\n❌ 未找到高血压预测结果')
        else:
            print('\n❌ 响应中没有predictions字段')
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败 - 请确保Flask应用正在运行")
    except Exception as e:
        print(f'❌ 请求失败: {e}')

if __name__ == "__main__":
    test_hypertension_prediction()