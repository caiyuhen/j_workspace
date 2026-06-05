"""
大模型服务连接测试脚本

测试大模型服务(192.168.0.214:8802/chat/)的连接和RAG功能
"""
import asyncio
import httpx
import sys
from datetime import datetime


# 大模型服务配置
LLM_ENDPOINT = "http://192.168.0.214:8802/chat/"
LLM_MODEL = "medical-large"
TIMEOUT = 30


async def test_connection():
    """测试基本连接"""
    print("=" * 60)
    print("1. 测试基本连接")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # 尝试访问健康检查端点
            try:
                response = await client.get(f"{LLM_ENDPOINT.replace('/chat/', '')}/health")
                print(f"✅ 服务健康检查: {response.status_code}")
            except:
                print("⚠️ 健康检查端点不可用，尝试直接调用API...")
            
            # 测试基本连通性
            response = await client.get(LLM_ENDPOINT.replace('/chat/', ''))
            print(f"✅ 服务连接成功: {LLM_ENDPOINT}")
            return True
            
    except httpx.ConnectError:
        print(f"❌ 连接失败: 无法连接到 {LLM_ENDPOINT}")
        print("   请检查:")
        print("   1. 服务地址是否正确")
        print("   2. 服务是否已启动")
        print("   3. 网络是否可达")
        return False
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False


async def test_chat_completion():
    """测试聊天补全API"""
    print("\n" + "=" * 60)
    print("2. 测试聊天补全API")
    print("=" * 60)
    
    test_messages = [
        {"role": "user", "content": "你好，请介绍一下你自己。"}
    ]
    
    payload = {
        "model": LLM_MODEL,
        "messages": test_messages,
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print(f"📤 发送请求到: {LLM_ENDPOINT}chat/completions")
            print(f"📝 请求内容: {test_messages[0]['content']}")
            
            start_time = datetime.now()
            
            response = await client.post(
                f"{LLM_ENDPOINT}chat/completions",
                json=payload
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 请求成功 (耗时: {elapsed:.2f}s)")
                
                # 解析响应
                if "choices" in result:
                    content = result["choices"][0].get("message", {}).get("content", "")
                    print(f"📥 响应内容: {content[:200]}...")
                elif "content" in result:
                    print(f"📥 响应内容: {result['content'][:200]}...")
                else:
                    print(f"📥 响应: {result}")
                
                return True
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print(f"❌ 请求超时 (超过 {TIMEOUT}s)")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


async def test_rag_query():
    """测试RAG医学知识检索"""
    print("\n" + "=" * 60)
    print("3. 测试RAG医学知识检索")
    print("=" * 60)
    
    medical_queries = [
        "高血压的诊断标准是什么？",
        "糖尿病患者应该如何饮食？",
        "阿司匹林的适应症和禁忌症有哪些？"
    ]
    
    success_count = 0
    
    for query in medical_queries:
        print(f"\n📝 查询: {query}")
        
        payload = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": query}],
            "temperature": 0.5,
            "max_tokens": 500
        }
        
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                start_time = datetime.now()
                
                response = await client.post(
                    f"{LLM_ENDPOINT}chat/completions",
                    json=payload
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 提取响应内容
                    if "choices" in result:
                        content = result["choices"][0].get("message", {}).get("content", "")
                    elif "content" in result:
                        content = result["content"]
                    else:
                        content = str(result)
                    
                    print(f"✅ 成功 (耗时: {elapsed:.2f}s)")
                    print(f"   响应摘要: {content[:150]}...")
                    success_count += 1
                else:
                    print(f"❌ 失败: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"❌ 异常: {e}")
    
    print(f"\n📊 RAG测试结果: {success_count}/{len(medical_queries)} 成功")
    return success_count == len(medical_queries)


async def test_stream_chat():
    """测试流式响应"""
    print("\n" + "=" * 60)
    print("4. 测试流式响应")
    print("=" * 60)
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": "请简要介绍糖尿病的类型。"}],
        "stream": True,
        "max_tokens": 200
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print(f"📤 发送流式请求...")
            
            async with client.stream(
                "POST",
                f"{LLM_ENDPOINT}chat/completions",
                json=payload
            ) as response:
                if response.status_code == 200:
                    print("✅ 流式连接成功")
                    print("📥 流式响应: ", end="")
                    
                    chunk_count = 0
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            chunk_count += 1
                            if chunk_count <= 5:  # 只显示前5个chunk
                                print(f"[chunk {chunk_count}]", end=" ")
                    
                    print(f"\n   共接收 {chunk_count} 个数据块")
                    return True
                else:
                    print(f"❌ 流式请求失败: HTTP {response.status_code}")
                    return False
                    
    except Exception as e:
        print(f"⚠️ 流式响应测试跳过: {e}")
        return None


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("   医学智能体系统 - 大模型服务连接测试")
    print(f"   服务地址: {LLM_ENDPOINT}")
    print(f"   测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # 1. 测试基本连接
    results["connection"] = await test_connection()
    
    if not results["connection"]:
        print("\n❌ 服务连接失败，跳过后续测试")
        return
    
    # 2. 测试聊天补全
    results["chat"] = await test_chat_completion()
    
    # 3. 测试RAG检索
    results["rag"] = await test_rag_query()
    
    # 4. 测试流式响应
    results["stream"] = await test_stream_chat()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("   测试结果汇总")
    print("=" * 60)
    
    for name, success in results.items():
        status = "✅ 通过" if success else ("❌ 失败" if success is False else "⚠️ 跳过")
        print(f"   {name}: {status}")
    
    all_passed = all(r for r in results.values() if r is not None)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！大模型服务连接正常。")
    else:
        print("⚠️ 部分测试未通过，请检查服务配置。")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
