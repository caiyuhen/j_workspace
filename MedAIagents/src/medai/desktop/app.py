"""
MedAIagents 桌面应用启动器
Desktop Application Launcher
"""

import sys
import os
import threading
import time
import webbrowser

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from medai.config import Config

# 全局变量
server_running = False
server_url = "http://127.0.0.1:8228"


def start_server():
    """启动 FastAPI 服务"""
    global server_running
    
    try:
        import uvicorn
        from medai.desktop.server import app
        
        print("🚀 正在启动 MedAIagents 服务...")
        
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8228,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        server_running = True
        server.run()
        
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        server_running = False


def wait_for_server(timeout: int = 30):
    """等待服务启动"""
    import requests
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{server_url}/api/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False


def run_desktop_app():
    """运行桌面应用"""
    print("=" * 60)
    print("🏥 MedAIagents - 医学 AI 助手 桌面版")
    print("=" * 60)
    
    # 1. 启动后端服务
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 2. 等待服务启动
    print("\n⏳ 正在启动服务，请稍候...")
    
    if not wait_for_server():
        print("❌ 服务启动超时，请检查端口是否被占用")
        input("\n按回车键退出...")
        sys.exit(1)
    
    print("✅ 服务已启动")
    
    # 3. 尝试使用 pywebview 打开窗口
    try:
        import webview
        
        print("🖥️  正在打开桌面应用窗口...\n")
        
        # 创建窗口
        window = webview.create_window(
            title="MedAIagents - 医学 AI 助手",
            url=server_url,
            width=1280,
            height=800,
            resizable=True,
            min_size=(1000, 600),
            background_color="#f0f2f5",
            text_select=True
        )
        
        # 启动应用
        webview.start(debug=False)
        
    except ImportError:
        # 如果没有安装 pywebview，使用浏览器打开
        print("⚠️  检测到未安装 pywebview，将使用浏览器打开")
        print(f"🌐 在浏览器中打开: {server_url}")
        webbrowser.open(server_url)
        
        print("\n📝 提示: 要使用桌面应用窗口，请安装 pywebview:")
        print("   pip install pywebview\n")
        
        # 保持程序运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 正在关闭服务...")
            
    except Exception as e:
        print(f"❌ 启动桌面应用失败: {e}")
        print(f"🌐 您可以手动在浏览器中访问: {server_url}")
        
        input("\n按回车键退出...")
        sys.exit(1)


def run_headless():
    """仅启动后端服务（无头模式）"""
    print("=" * 60)
    print("🏥 MedAIagents - 后端服务模式")
    print("=" * 60)
    
    print(f"\n🌐 服务地址: {server_url}")
    print(f"📖 API 文档: {server_url}/docs")
    print(f"\n按 Ctrl+C 停止服务\n")
    
    start_server()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MedAIagents 桌面应用")
    parser.add_argument('--headless', action='store_true', help='仅启动后端服务（无头模式）')
    parser.add_argument('--port', type=int, default=8228, help='服务端口（默认：8228）')
    
    args = parser.parse_args()
    
    # 更新端口
    server_url = f"http://127.0.0.1:{args.port}"
    
    if args.headless:
        run_headless()
    else:
        run_desktop_app()
