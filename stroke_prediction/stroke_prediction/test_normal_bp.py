import requests
import json

# 测试正常血压值的预测
test_data = {
    "age": 40,
    "gender": "男",
    "height": 170,
    "weight": 70,
    "systolic_bp": 120,  # 正常收缩压
    "diastolic_bp": 80,  # 正常舒张压
    "cholesterol": 200,
    "glucose": 100,
    "smoking": "否",
    "alcohol": "否",
    "physical_activity": "是",
    "season": "春季"
}

try:
    response = requests.post('http://127.0.0.1:5008/predict', json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        print("预测结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 查找高血压预测结果
        hypertension_result = result['predictions'].get('hypertension')
        
        if hypertension_result:
            print(f"\n高血压预测详情:")
            print(f"概率: {hypertension_result['probability']:.4f}")
            print(f"风险等级: {hypertension_result['risk_level']}")
            print(f"预测结果: {'阳性' if hypertension_result['prediction'] else '阴性'}")
            
            # 分析结果合理性
            prob = hypertension_result['probability']
            if prob > 0.8:
                print(f"\n⚠️ 异常: 正常血压(120/80)预测概率过高: {prob:.1%}")
            elif prob < 0.3:
                print(f"\n✅ 正常: 正常血压预测概率合理: {prob:.1%}")
            else:
                print(f"\n⚠️ 可疑: 正常血压预测概率偏高: {prob:.1%}")
        else:
            print("未找到高血压预测结果")
    else:
        print(f"请求失败: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"请求失败: {e}")