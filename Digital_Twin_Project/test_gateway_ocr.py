import requests
import os
import json
import time

# 配置
GATEWAY_URL = "http://localhost:8000"
PATIENT_SERVICE_URL = "http://localhost:8003"
FILE_PATH = r"d:\workspace\Digital_Twin_Project\source_data\10\倪欣然.pdf"
PATIENT_NAME = "倪欣然"

def test_gateway_ocr_flow():
    if not os.path.exists(FILE_PATH):
        print(f"错误: 未找到测试文件 {FILE_PATH}")
        return

    print(f"--- 步骤 1: 上传 PDF 到网关 ({GATEWAY_URL}/upload/ocr) ---")
    try:
        files = {
            'file': (os.path.basename(FILE_PATH), open(FILE_PATH, 'rb'), 'application/pdf')
        }
        
        response = requests.post(f"{GATEWAY_URL}/upload/ocr", files=files)
        
        if response.status_code == 200:
            print("✅ 上传成功!")
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        else:
            print(f"❌ 上传失败: {response.status_code}")
            print(response.text)
            return
            
    except Exception as e:
        print(f"❌ 上传错误: {str(e)}")
        return

    print(f"\n--- 步骤 2: 在患者服务中验证患者数据 ({PATIENT_SERVICE_URL}/patients/{PATIENT_NAME}) ---")
    # 稍作暂停等待重新加载完成（尽管在网关中已等待）
    time.sleep(1)
    
    try:
        response = requests.get(f"{PATIENT_SERVICE_URL}/patients/{PATIENT_NAME}")
        
        if response.status_code == 200:
            print("✅ 找到患者数据!")
            # 打印数据摘要
            data = response.json()
            print(f"ID: {data.get('id')}")
            print(f"Name: {data.get('name')}")
            print(f"Metrics: {json.dumps(data.get('metrics'), ensure_ascii=False)}")
        else:
            print(f"❌ 未找到患者数据: {response.status_code}")
            print("数据可能未正确重新加载。")
            return

    except Exception as e:
        print(f"❌ 验证错误: {str(e)}")
        return

    print(f"\n--- 步骤 3: 通过网关生成报告 ({GATEWAY_URL}/report/generate) ---")
    try:
        payload = {
            "patient_name": PATIENT_NAME,
            "treatment_plan": {
                "type": "Brace",
                "duration": 24,
                "compliance": 0.9
            }
        }
        
        response = requests.post(f"{GATEWAY_URL}/report/generate", json=payload)
        
        if response.status_code == 200:
            print("✅ 报告生成成功!")
            result = response.json()
            print(f"Report ID: {result.get('simulation_id')}")
            print(f"Summary: {result.get('summary')}")
        else:
            print(f"❌ 报告生成失败: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ 报告错误: {str(e)}")

if __name__ == "__main__":
    test_gateway_ocr_flow()
