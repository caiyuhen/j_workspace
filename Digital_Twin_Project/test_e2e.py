# 脊柱数字孪生微服务 - 端到端测试脚本
# 此脚本验证整个微服务管道：
# OCR -> 患者服务 -> 模拟服务 -> 可视化服务

import requests
import json
import time
import os

# 配置
GATEWAY_URL = "http://127.0.0.1:8000"
# 用于验证的直接服务 URL
PATIENT_SERVICE_URL = "http://127.0.0.1:8003"
SIMULATION_SERVICE_URL = "http://127.0.0.1:8001"
VISUALIZATION_SERVICE_URL = "http://127.0.0.1:8002"
OCR_SERVICE_URL = "http://127.0.0.1:8004"

# 测试数据
TEST_PDF_PATH = "sample_medical_record.pdf" # 确保此文件存在或使用虚拟文件创建它
PATIENT_NAME = "倪欣然" # 示例 PDF 中的预期名称

def create_dummy_pdf():
    """如果在本地不可用，则创建一个虚拟 PDF 用于测试。"""
    if not os.path.exists(TEST_PDF_PATH):
        print(f"创建虚拟 PDF: {TEST_PDF_PATH}")
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(TEST_PDF_PATH)
        c.drawString(100, 750, f"Patient Name: {PATIENT_NAME}")
        c.drawString(100, 730, "Diagnosis: Scoliosis")
        c.drawString(100, 710, "Cobb Angle: 25 degrees")
        c.save()

def test_ocr_upload():
    print(f"\n[步骤 1] 上传 PDF 到网关 (OCR 提取)...")
    if not os.path.exists(TEST_PDF_PATH):
        create_dummy_pdf()
        
    try:
        with open(TEST_PDF_PATH, "rb") as f:
            files = {"file": (TEST_PDF_PATH, f, "application/pdf")}
            # 注意：网关端点是 /upload/ocr
            resp = requests.post(f"{GATEWAY_URL}/upload/ocr", files=files)
            
        if resp.status_code == 200:
            print("✅ OCR 上传成功。")
            print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ OCR 上传失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ OCR 上传期间发生异常: {e}")
        return False

def test_patient_verification():
    print(f"\n[步骤 2] 在患者服务中验证患者数据...")
    # 稍等片刻以确保文件系统同步
    time.sleep(2)
    try:
        resp = requests.get(f"{PATIENT_SERVICE_URL}/patients/{PATIENT_NAME}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ 找到 {data.get('name')} 的患者数据。")
            print(f"   Diagnosis: {data.get('diagnosis')}")
            print(f"   Cobb Angle: {data.get('cobb_angle')}")
            return True
        else:
            print(f"❌ 患者验证失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 患者验证期间发生异常: {e}")
        return False

def test_report_generation():
    print(f"\n[步骤 3] 正在为 '{PATIENT_NAME}' 生成报告...")
    payload = {
        "patient_name": PATIENT_NAME,
        "treatment_plan": {
            "type": "Brace",
            "duration": 24, # 月
            "compliance": 0.9
        }
    }
    
    try:
        resp = requests.post(f"{GATEWAY_URL}/report/generate", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            print("✅ 报告生成成功。")
            
            # 验证滑块数据
            chart_json = data.get("evolution_chart_json", {})
            layout = chart_json.get("layout", {})
            sliders = layout.get("sliders", [])
            
            if sliders:
                steps = sliders[0].get("steps", [])
                print(f"✅ 找到包含 {len(steps)} 个步骤（周）的滑块。")
                if len(steps) > 50:
                     print("   确认基于“周”的演变（2 年约 104 周）。")
                else:
                     print(f"⚠️ 警告：预期约 104 个步骤，实际得到 {len(steps)}。")
            else:
                print("❌ 图表 JSON 中未找到滑块配置。")
            
            return True
        else:
            print(f"❌ 报告生成失败: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 报告生成期间发生异常: {e}")
        return False

if __name__ == "__main__":
    print("=== 开始脊柱数字孪生微服务端到端测试 ===")
    
    # 确保服务已启动（基本检查）
    try:
        requests.get(f"{GATEWAY_URL}/health", timeout=5)
    except Exception as e:
        print(f"❌ 网关无法访问。请先使用 ./start_debug.ps1 或 ./start_services.sh 启动服务. Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    if test_ocr_upload():
        if test_patient_verification():
            test_report_generation()
            
    print("\n=== 测试序列完成 ===")
