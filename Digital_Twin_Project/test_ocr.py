import requests
import os

# 配置
# 确保端口与 docker-compose.yml 或 start_debug.ps1 匹配
# 默认 OCR 服务端口为 8004
OCR_SERVICE_URL = "http://localhost:8004"
FILE_PATH = r"D:\workspace\Digital_Twin_Project\source_data\10\倪欣然.pdf"

def test_ocr_extraction():
    """
    测试 OCR 服务提取 PDF 的功能。
    这是一个简单的 Python 脚本，以避免 PowerShell curl 语法问题。
    """
    if not os.path.exists(FILE_PATH):
        print(f"错误: 未找到文件 {FILE_PATH}")
        return

    print(f"正在发送 {FILE_PATH} 到 {OCR_SERVICE_URL}...")
    
    try:
        with open(FILE_PATH, "rb") as f:
            files = {"file": (os.path.basename(FILE_PATH), f, "application/pdf")}
            # 修正端点路径，匹配 main.py 中的 definition
            response = requests.post(f"{OCR_SERVICE_URL}/ocr/extract", files=files)
        
        if response.status_code == 200:
            print("✅ 成功!")
            print("响应数据:")
            print(response.json())
        else:
            print(f"❌ 失败: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接被拒绝。OCR 服务是否正在运行？")
        print("尝试运行: python services/ocr-service/src/main.py")

if __name__ == "__main__":
    test_ocr_extraction()
