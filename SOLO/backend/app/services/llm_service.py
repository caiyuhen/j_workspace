"""
大模型服务客户端

默认兼容原有医疗大模型 `/chat` 接口；当请求指定的模型命中
`model_configs.json` 中的 OpenAI-compatible 配置时，改走 `/chat/completions`。
"""
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    大模型服务客户端。

    - 默认模式：调用原有 `{LLM_ENDPOINT}/chat`，保留内置 RAG 能力。
    - OpenAI 兼容模式：按模型配置调用 `{endpoint}/chat/completions`。
    """

    def __init__(
        self,
        endpoint: str = None,
        model: str = None,
        timeout: int = None,
        config_path: Optional[Path] = None,
    ):
        self.endpoint = self._normalize_endpoint(endpoint or settings.LLM_ENDPOINT)
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
        self.config_path = Path(config_path) if config_path else Path(__file__).resolve().parents[2] / "model_configs.json"
        self._model_configs = self._load_model_configs()

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        """
        规范化服务地址。

        兼容旧配置中以 `/chat/` 或 OpenAI `/chat/completions` 结尾的写法，统一转换为基础地址。
        """
        normalized = (endpoint or "").strip().rstrip("/")
        if normalized.endswith("/chat/completions"):
            normalized = normalized[: -len("/chat/completions")]
        if normalized.endswith("/chat"):
            normalized = normalized[:-5]
        return normalized

    def _load_model_configs(self) -> List[Dict]:
        """读取模型配置；读取失败时保持原有单模型行为。"""
        if not self.config_path.exists():
            return []
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                configs = json.load(f)
            if isinstance(configs, list):
                return configs
            logger.warning("模型配置文件格式不是列表: %s", self.config_path)
        except Exception as e:
            logger.warning("读取模型配置失败: %s, path=%s", e, self.config_path)
        return []

    def reload_model_configs(self) -> None:
        """重新加载模型配置，便于运行中更新配置后生效。"""
        self._model_configs = self._load_model_configs()

    def get_model_configs(self) -> List[Dict]:
        """返回可展示给前端的模型列表，不暴露 api_key。"""
        return [
            {
                "name": cfg.get("name"),
                "display_name": cfg.get("display_name") or cfg.get("name"),
                "type": cfg.get("type", "openai"),
                "default": bool(cfg.get("default", False)),
            }
            for cfg in self._model_configs
            if cfg.get("name")
        ]

    def _resolve_model_config(self, model_name: Optional[str]) -> Optional[Dict]:
        """根据请求模型名找到配置；未传模型时使用 default 配置。"""
        if not self._model_configs:
            return None

        if model_name:
            for cfg in self._model_configs:
                if cfg.get("name") == model_name:
                    return cfg
            logger.warning("未找到请求的模型配置: %s，将回退到默认 LLM 配置", model_name)
            return None

        for cfg in self._model_configs:
            if cfg.get("default"):
                return cfg
        return None

    @staticmethod
    def _build_payload(
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict:
        """将消息列表转换为医疗大模型 `/chat` 接口所需格式。"""
        prompt = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                prompt = msg["content"]
                break

        history = []
        user_msg_count = 0
        for msg in messages:
            if msg["role"] == "user":
                user_msg_count += 1

        if user_msg_count > 1:
            for msg in messages[:-1]:
                if msg["role"] != "system":
                    history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

        payload = {
            "prompt": prompt,
            "use_rag": kwargs.get("use_rag", True),
            "return_rag_info": kwargs.get("return_rag_info", True),
            "use_adapter": kwargs.get("use_adapter", True),
            "history": kwargs.get("history", history),
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "repetition_penalty": kwargs.get("repetition_penalty", 1.1)
        }

        session_id = kwargs.get("session_id")
        if session_id:
            payload["session_id"] = session_id

        return payload

    @staticmethod
    def _openai_payload(messages: List[Dict], model: str, temperature: float, max_tokens: int) -> Dict:
        """构造 OpenAI-compatible chat/completions 请求体。"""
        return {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    async def chat(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        发送聊天请求。

        Args:
            messages: 消息列表，格式: [{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成 token 数
            stream: 是否流式返回
            model: 前端选择的模型名称，对应 `model_configs.json` 的 name
            **kwargs: 其他参数
        """
        model_config = self._resolve_model_config(model)
        if model_config and model_config.get("type") == "openai":
            return await self._chat_openai_compatible(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model_config=model_config,
            )
        if model_config and model_config.get("type") in {"medical_rag", "medical-rag", "rag", "chat"}:
            return await self._chat_medical_rag(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model_config=model_config,
                **kwargs,
            )
        return await self._chat_medical_rag(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def _chat_openai_compatible(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        model_config: Dict,
    ) -> Dict:
        """调用 OpenAI-compatible `/chat/completions` 接口。"""
        endpoint = self._normalize_endpoint(model_config.get("endpoint", ""))
        raw_model = model_config.get("model") or model_config.get("name")
        selected_name = model_config.get("name") or raw_model
        payload = self._openai_payload(messages, raw_model, temperature, max_tokens)
        headers = {"Content-Type": "application/json"}
        api_key = model_config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        logger.info("OpenAI兼容LLM请求: endpoint=%s, model=%s", endpoint, selected_name)

        try:
            import urllib.request
            req = urllib.request.Request(
                f"{endpoint}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout / 1000) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            content = ""
            choices = result.get("choices") or []
            if choices:
                message = choices[0].get("message") or {}
                content = message.get("content") or choices[0].get("text") or ""

            usage = result.get("usage") or {}
            return {
                "content": content,
                "tokens": usage.get("total_tokens") or len(content) // 4,
                "model": selected_name,
                "raw_model": raw_model,
                "sources": [],
                "analysis": {},
                "raw_response": result,
            }
        except Exception as e:
            logger.error("OpenAI兼容LLM请求失败: %s, endpoint=%s, model=%s", e, endpoint, selected_name)
            return self._fallback_response(messages, model=selected_name)

    async def _chat_medical_rag(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        model_config: Optional[Dict] = None,
        **kwargs,
    ) -> Dict:
        """调用医疗大模型 `/chat` 接口。"""
        payload = self._build_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        prompt = payload.get("prompt", "")
        endpoint = self._normalize_endpoint(model_config.get("endpoint")) if model_config else self.endpoint
        selected_name = model_config.get("name") if model_config else self.model
        raw_model = model_config.get("model") if model_config else self.model

        logger.info("医疗RAG LLM请求: endpoint=%s, model=%s, prompt长度=%s", endpoint, selected_name, len(prompt))

        try:
            import urllib.request
            req = urllib.request.Request(
                f"{endpoint}/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout / 1000) as resp:
                result = json.loads(resp.read().decode("utf-8"))

                return {
                    "content": result.get("response", ""),
                    "tokens": len(result.get("response", "")) // 4,
                    "model": selected_name,
                    "raw_model": raw_model,
                    "sources": result.get("retrieved_knowledge", []),
                    "analysis": result.get("analysis", {}),
                    "raw_response": result
                }

        except Exception as e:
            logger.error("医疗RAG LLM请求失败: %s, endpoint=%s, model=%s", e, endpoint, selected_name)
            return self._fallback_response(messages, model=selected_name)

    def _fallback_response(self, messages: List[Dict], model: str = "fallback") -> Dict:
        """备用响应：当 LLM 服务不可用时返回模拟响应。"""
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break

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
            "model": model,
            "sources": []
        }

    async def stream_chat(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天：当前通过非流式调用后分块返回，保持现有前端兼容。"""
        try:
            result = await self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )
            content = result.get("content", "")
            chunk_size = 20
            for i in range(0, len(content), chunk_size):
                yield content[i:i + chunk_size]
        except Exception as e:
            logger.error("流式请求失败: %s", e)
            raise

    async def health_check(self) -> bool:
        """检查原有医疗大模型服务健康状态。"""
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.endpoint}/health", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def count_tokens(self, text: str) -> int:
        """计算文本 Token 数量（估算）。"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)

    def count_messages_tokens(self, messages: List[Dict]) -> int:
        """计算消息列表 Token 数量。"""
        total = 0
        for msg in messages:
            total += 4
            total += self.count_tokens(msg.get("role", ""))
            total += self.count_tokens(msg.get("content", ""))
        total += 2
        return total


llm_service = LLMService()
