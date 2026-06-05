"""
大模型服务客户端

大模型服务地址: 192.168.0.214:8802/chat/
该服务已内置RAG（检索增强生成）能力，包含医学知识向量库。

调用时会自动：
1. 解析用户查询意图
2. 向量检索相关医学知识
3. 知识增强生成响应
4. 返回结果及知识来源引用
"""
import httpx
from typing import List, Dict, AsyncGenerator, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    大模型服务客户端（内置RAG）
    
    大模型服务已内置RAG能力，无需单独管理知识库。
    """
    
    def __init__(
        self,
        endpoint: str = None,
        model: str = None,
        timeout: int = None
    ):
        self.endpoint = endpoint or settings.LLM_ENDPOINT
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
    
    async def chat(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        **kwargs
    ) -> Dict:
        """
        发送聊天请求（自动触发RAG检索增强）
        
        适配 LLM API 格式：
        - Endpoint: POST /chat
        - 请求: {"prompt": "...", "use_rag": true, "history": [...], ...}
        - 响应: {"response": "...", "retrieved_knowledge": [...], ...}
        
        Args:
            messages: 消息列表，格式: [{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            stream: 是否流式返回
            **kwargs: 其他参数
            
        Returns:
            Dict: 大模型响应，包含content、tokens、sources等字段
        """
        # 提取最后一条用户消息作为 prompt
        prompt = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                prompt = msg["content"]
                break
        
        # 构建历史消息（排除最后一条用户消息和系统消息）
        history = []
        user_msg_count = 0
        for msg in messages:
            if msg["role"] == "user":
                user_msg_count += 1
        # 如果有多条用户消息，前面的作为 history
        if user_msg_count > 1:
            for msg in messages[:-1]:
                if msg["role"] != "system":
                    history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # 构建符合 LLM 服务 API 的请求格式
        # 启用 RAG 检索增强（超时已增加到 300 秒）
        payload = {
            "prompt": prompt,
            "use_rag": True,
            "use_adapter": True,
            "history": history,
            "temperature": temperature,
            "max_new_tokens": max_tokens
        }
        
        logger.info(f"LLM 请求: prompt长度={len(prompt)}, use_rag=True")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout / 1000) as client:
                response = await client.post(
                    f"{self.endpoint}/chat",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # 转换响应格式为统一格式
                return {
                    "content": result.get("response", ""),
                    "tokens": len(result.get("response", "")) // 4,
                    "model": self.model,
                    "sources": result.get("retrieved_knowledge", []),
                    "analysis": result.get("analysis", {}),
                    "raw_response": result
                }
                
        except httpx.TimeoutException:
            logger.error(f"LLM服务请求超时: {self.endpoint}")
            return self._fallback_response(messages)
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM服务HTTP错误: {e}")
            return self._fallback_response(messages)
        except Exception as e:
            logger.error(f"LLM服务请求失败: {e}")
            return self._fallback_response(messages)
    
    def _fallback_response(self, messages: List[Dict]) -> Dict:
        """
        备用响应：当 LLM 服务不可用时返回模拟响应
        """
        # 获取最后一条用户消息
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        # 生成模拟响应
        response_text = f"""我理解您的问题是：{user_message[:100]}...

由于大模型服务暂时不可用，我无法提供完整的医学分析。以下是基本建议：

1. **问题分析**：您提出的问题涉及医学领域，建议咨询专业医生获取准确诊断。

2. **建议措施**：
   - 如有不适症状，请及时就医
   - 保持健康的生活方式
   - 定期进行体检

3. **注意事项**：
   - 本系统仅供参考，不能替代专业医疗诊断
   - 如有紧急情况，请立即拨打急救电话

---
*提示：大模型服务连接失败，请检查服务配置或稍后重试。*"""

        return {
            "content": response_text,
            "tokens": len(response_text) // 4,
            "model": "fallback",
            "sources": []
        }
    
    async def stream_chat(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天（自动RAG增强）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            str: 流式响应内容块
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout / 1000) as client:
                async with client.stream(
                    "POST",
                    f"{self.endpoint}/chat/completions",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            yield data
                            
        except Exception as e:
            logger.error(f"流式请求失败: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        检查大模型服务健康状态
        
        Returns:
            bool: 服务是否健康
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.endpoint}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本Token数量（估算）
        
        简化实现：
        - 中文约1.5字符/token
        - 英文约4字符/token
        
        Args:
            text: 输入文本
            
        Returns:
            int: Token数量估算
        """
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """
        计算消息列表Token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: Token数量
        """
        total = 0
        for msg in messages:
            # 消息格式开销
            total += 4
            total += self.count_tokens(msg.get("role", ""))
            total += self.count_tokens(msg.get("content", ""))
        # 对话开始标记
        total += 2
        return total


# 全局单例实例
llm_service = LLMService()
