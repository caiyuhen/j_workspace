"""LLM 网关：统一封装"任务执行用的对话模型"调用。

支持两种网关，由环境变量切换：

- ``SOLO_LLM_GATEWAY=cherryin``：走 OpenAI 兼容协议
  - ``SOLO_CHERRYIN_API_BASE``（默认 ``https://open.cherryin.cc/v1``）
  - ``SOLO_CHERRYIN_API_KEY``
  - ``SOLO_CHERRYIN_MODEL``（如 ``qwen/qwen3.5-35b-a3b``）

- ``SOLO_LLM_GATEWAY=inner``：走内网医疗 LLM 网关
  - ``SOLO_INNER_LLM_BASE``（默认 ``http://192.168.0.214:8802``）
  - 不需要鉴权
  - 请求体：``{"prompt": ..., "history": [...], "use_rag": true, "use_adapter": true,
                "temperature": 0.7, "max_new_tokens": 512}``
  - 响应字段：``response.json()["response"]``

设计原则：
- API key 等敏感信息只通过环境变量读取，不在代码里 hardcode；
- HTTP 调用通过依赖注入暴露 ``http_post``，方便单元测试不发真实请求；
- 任意配置缺失或调用异常时，``chat`` 都会显式抛出 ``LLMGatewayError``，由调用方自己决定回退；
- 模块本身不发任何"假动作"调用：未配置时根本就不会构建 gateway。
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMGatewayError(RuntimeError):
    """LLM 网关调用失败，由调用方决定是否回退到 fallback。"""


@dataclass
class GatewayConfig:
    name: str
    api_base: str
    api_key: Optional[str] = None
    model: Optional[str] = None


class LLMGateway:
    """LLM 网关抽象基类，子类只需实现 ``chat``。"""

    name = "base"

    def chat(self, messages: List[Dict[str, str]], *, timeout: int = 60) -> str:
        raise NotImplementedError


class CherryInOpenAIGateway(LLMGateway):
    """走 OpenAI 协议的 cherryin 网关。"""

    name = "cherryin"

    def __init__(self, config: GatewayConfig, http_post: Callable[..., Any]):
        if not config.api_base:
            raise LLMGatewayError("CherryIn 网关未配置 api_base")
        if not config.api_key:
            raise LLMGatewayError("CherryIn 网关未配置 api_key")
        if not config.model:
            raise LLMGatewayError("CherryIn 网关未配置 model")
        self.config = config
        self._http_post = http_post

    def chat(self, messages: List[Dict[str, str]], *, timeout: int = 60) -> str:
        url = self.config.api_base.rstrip("/") + "/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = self._http_post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise LLMGatewayError(f"CherryIn 网关调用失败: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMGatewayError(f"CherryIn 响应结构异常: {data!r}") from exc


class InnerChatGateway(LLMGateway):
    """走内网 ``/chat`` 协议的 LLM 网关，无鉴权。"""

    name = "inner"

    def __init__(self, config: GatewayConfig, http_post: Callable[..., Any]):
        if not config.api_base:
            raise LLMGatewayError("内网 LLM 网关未配置 api_base")
        self.config = config
        self._http_post = http_post

    def chat(self, messages: List[Dict[str, str]], *, timeout: int = 60) -> str:
        url = self.config.api_base.rstrip("/") + "/chat"
        # 把 messages 拆成 prompt + history（最后一条 user 当 prompt，前面的塞 history）
        history = []
        prompt = ""
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content") or ""
            if role == "user":
                if prompt:
                    history.append({"role": "user", "content": prompt})
                prompt = content
            elif role in ("assistant", "system"):
                if prompt:
                    history.append({"role": "user", "content": prompt})
                    prompt = ""
                history.append({"role": role, "content": content})
        if not prompt:
            # 没有 user 消息：把全部内容拼成 prompt
            prompt = "\n".join(m.get("content") or "" for m in messages)
            history = []

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "history": history,
            "use_rag": True,
            "use_adapter": True,
            "temperature": 0.7,
            "max_new_tokens": 512,
        }
        headers = {"Content-Type": "application/json"}
        try:
            resp = self._http_post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise LLMGatewayError(f"内网 LLM 网关调用失败: {exc}") from exc

        text = data.get("response") if isinstance(data, dict) else None
        if not text:
            raise LLMGatewayError(f"内网 LLM 响应缺少 response 字段: {data!r}")
        return text


def _httpx_post_factory():
    import httpx

    def _post(url, json=None, headers=None, timeout=None):
        with httpx.Client(timeout=timeout or 60) as client:
            return client.post(url, json=json, headers=headers)

    return _post


def build_llm_gateway(http_post: Optional[Callable[..., Any]] = None) -> Optional[LLMGateway]:
    """读取环境变量，按 ``SOLO_LLM_GATEWAY`` 切换：

    返回 None 表示"未启用"，调用方应继续使用原有的本地 LLM。
    """
    name = (os.getenv("SOLO_LLM_GATEWAY") or "").strip().lower()
    if not name:
        return None
    if http_post is None:
        http_post = _httpx_post_factory()

    if name == "cherryin":
        config = GatewayConfig(
            name="cherryin",
            api_base=os.getenv("SOLO_CHERRYIN_API_BASE", "https://open.cherryin.cc/v1"),
            api_key=os.getenv("SOLO_CHERRYIN_API_KEY"),
            model=os.getenv("SOLO_CHERRYIN_MODEL"),
        )
        return CherryInOpenAIGateway(config=config, http_post=http_post)

    if name == "inner":
        config = GatewayConfig(
            name="inner",
            api_base=os.getenv("SOLO_INNER_LLM_BASE", "http://192.168.0.214:8802"),
        )
        return InnerChatGateway(config=config, http_post=http_post)

    raise LLMGatewayError(f"未知 SOLO_LLM_GATEWAY 取值: {name}")
