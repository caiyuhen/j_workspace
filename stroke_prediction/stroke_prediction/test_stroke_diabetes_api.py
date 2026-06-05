#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_stroke_diabetes_prediction():
    """测试脑卒中和糖尿病预测API"""
    
    # API端点
    url = "http://127.0.0.1:5008/predict"
    
    # 测试数据 - 高风险样本
    test_data = {
        "age": 65,
        "gender": "Male",
        "hypertension": 1,
        "heart_disease": 1,
        "ever_married": "Yes",
        "work_type": "Private",
        "residence_type": "Urban",
        "avg_glucose_level": 180.5,
        "bmi": 28.5,
        "smoking_status": "formerly smoked",
        "systolic_bp": 160,
        "diastolic_bp": 95,
        "cholesterol": 250,
        "exercise_frequency": 1,
        "alcohol_consumption": 2,
        "stress_level": 8,
        "sleep_hours": 5,
        "family_history_stroke": 1,
        "medication_adherence": 0,
        "previous_stroke": 0
    }
    
    print("=== 测试脑卒中和糖尿病预测API ===")
    print(f"测试数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送POST请求
        response = requests.post(url, json=test_data, timeout=30)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查脑卒中预测结果
            if 'predictions' in result and 'stroke' in result['predictions']:
                stroke_result = result['predictions']['stroke']
                print(f"\n=== 脑卒中预测结果 ===")
                print(f"风险概率: {stroke_result.get('probability', 'N/A')}")
                print(f"预测结果: {stroke_result.get('prediction', 'N/A')}")
                print(f"风险等级: {stroke_result.get('risk_level', 'N/A')}")
                print(f"使用模型: {stroke_result.get('model_name', '未知')}")
                print(f"特征数量: {stroke_result.get('features_used', 'N/A')}")
            else:
                print("❌ 未找到脑卒中预测结果")
            
            # 检查糖尿病预测结果
            if 'predictions' in result and 'diabetes' in result['predictions']:
                diabetes_result = result['predictions']['diabetes']
                print(f"\n=== 糖尿病预测结果 ===")
                print(f"风险概率: {diabetes_result.get('probability', 'N/A')}")
                print(f"预测结果: {diabetes_result.get('prediction', 'N/A')}")
                print(f"风险等级: {diabetes_result.get('risk_level', 'N/A')}")
                print(f"使用模型: {diabetes_result.get('model_name', '未知')}")
                print(f"特征数量: {diabetes_result.get('features_used', 'N/A')}")
            else:
                print("❌ 未找到糖尿病预测结果")
                
        else:
            print(f"❌ API请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    test_stroke_diabetes_prediction()