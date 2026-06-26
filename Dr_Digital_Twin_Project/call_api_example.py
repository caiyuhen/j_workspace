import requests
import json
import base64
import os

# 配置 API 地址 (根据您的服务实际运行端口进行修改，默认 8123)
API_URL = "http://127.0.0.1:8123/api/v1/generate_video"

def call_generate_video(text, gender="female"):
    print(f"正在调用接口生成视频...\n文本内容: {text}\n选择性别: {gender}")
    
    payload = {
        "text": text,
        "doctor_gender": gender
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=120) # 视频生成比较耗时，设置较长超时时间
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "success":
            trace_id = data.get("trace_id")
            print(f"✅ 接口调用成功! Trace ID: {trace_id}")
            
            # 如果返回了视频 Base64，我们可以将其保存为本地文件查看
            video_b64 = data.get("video_base64")
            if video_b64:
                output_filename = f"test_output_{trace_id}.mp4"
                with open(output_filename, "wb") as f:
                    f.write(base64.b64decode(video_b64))
                print(f"🎬 视频已成功保存到本地: {output_filename}")
            else:
                audio_b64 = data.get("audio_base64")
                if audio_b64:
                    output_filename = f"test_output_{trace_id}.wav"
                    with open(output_filename, "wb") as f:
                        f.write(base64.b64decode(audio_b64))
                    print(f"⚠️ 视频生成失败，已回退保存纯音频到本地: {output_filename}")
        else:
            print("❌ 接口返回错误:", data)
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    # 测试调用
    test_text = "您好！您的空腹血糖目前是8.5mmol/L，收缩压145mmHg，建议立即启动降压治疗，推荐使用ACEI类药物（如贝那普利10mg qd）。"
    call_generate_video(test_text, gender="female")
