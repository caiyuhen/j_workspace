"""
LLM模型路由模块
LLM Model Routing Module
"""

import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from loguru import logger

from ..config import Config


class BaseLLMProvider(ABC):
    """LLM提供商基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.default_model = config.get('default_model')
        self.temperature = config.get('temperature', 0.3)
        self.max_tokens = config.get('max_tokens', 4096)
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        """聊天补全"""
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天补全"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Any] = None,
        **kwargs
    ) -> Any:
        model = model or self.default_model
        temperature = kwargs.get('temperature', temperature)
        max_tokens = kwargs.get('max_tokens', max_tokens)
        
        try:
            request_params = {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
            }
            if tools is not None:
                request_params['tools'] = tools
            if tool_choice is not None:
                request_params['tool_choice'] = tool_choice
            
            response = await self.client.chat.completions.create(**request_params)
            
            if tools is not None:
                return response
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            raise
    
    def parse_tool_calls(self, response) -> List[Dict]:
        """从响应中解析 tool_calls"""
        if not response or not hasattr(response, 'choices') or not response.choices:
            return []
        
        message = response.choices[0].message
        if not message or not hasattr(message, 'tool_calls') or message.tool_calls is None:
            return []
        
        result = []
        for tc in message.tool_calls:
            result.append({
                'id': getattr(tc, 'id', None),
                'type': getattr(tc, 'type', 'function'),
                'function': {
                    'name': getattr(tc.function, 'name', None),
                    'arguments': getattr(tc.function, 'arguments', None),
                }
            })
        return result
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(BaseLLMProvider):
    """Anthropic提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = AsyncAnthropic(api_key=self.api_key)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        model = model or self.default_model
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        # 转换消息格式
        system_message = ""
        converted_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                converted_messages.append(msg)
        
        try:
            response = await self.client.messages.create(
                model=model,
                messages=converted_messages,
                system=system_message if system_message else None,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API Error: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        system_message = ""
        converted_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                converted_messages.append(msg)
        
        stream = await self.client.messages.create(
            model=model,
            messages=converted_messages,
            system=system_message if system_message else None,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for event in stream:
            if event.type == 'content_block_delta':
                yield event.delta.text


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        model = model or self.default_model
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek API Error: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        model = model or self.default_model
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LLMRouter:
    """LLM路由管理器"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """初始化所有配置的提供商"""
        providers_config = self.config.get('llm.providers', {})
        
        provider_classes = {
            'openai': OpenAIProvider,
            'anthropic': AnthropicProvider,
            'deepseek': DeepSeekProvider,
        }
        
        for provider_name, provider_config in providers_config.items():
            if provider_name in provider_classes:
                try:
                    self._providers[provider_name] = provider_classes[provider_name](provider_config)
                    logger.info(f"Initialized LLM provider: {provider_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM provider {provider_name}: {e}")
    
    def get_provider(self, provider: str = None) -> BaseLLMProvider:
        """获取LLM提供商
        
        Args:
            provider: 提供商名称，如不指定则使用默认提供商
        
        Returns:
            LLM提供商实例
        """
        if provider is None:
            provider = self.config.get('llm.default_provider', 'openai')
        
        if provider not in self._providers:
            raise ValueError(f"LLM provider '{provider}' not configured or initialized")
        
        return self._providers[provider]
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: str = None,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Any] = None,
        **kwargs
    ):
        """聊天接口
        
        Args:
            messages: 消息列表
            provider: LLM提供商
            model: 模型名称
            stream: 是否流式输出
            tools: 工具定义列表
            tool_choice: 工具选择策略
            **kwargs: 其他参数
        
        Returns:
            完整响应或流式生成器
        """
        llm_provider = self.get_provider(provider)
        
        if stream:
            return llm_provider.chat_completion_stream(messages, model, **kwargs)
        else:
            return await llm_provider.chat_completion(
                messages, model=model, tools=tools, tool_choice=tool_choice, **kwargs
            )
    
    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        model: str = None,
        provider: str = None,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ):
        """使用工具调用聊天，并解析 tool_calls
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            model: 模型名称
            provider: LLM提供商
            temperature: 温度参数
            max_tokens: 最大token数
        
        Returns:
            (content, tool_calls) 元组
        """
        response = await self.chat(
            messages=messages,
            provider=provider,
            model=model,
            stream=False,
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        llm_provider = self.get_provider(provider)
        content = ""
        tool_calls = []
        
        if hasattr(response, 'choices'):
            message = response.choices[0].message if response.choices else None
            content = getattr(message, 'content', None) or ""
            if hasattr(llm_provider, 'parse_tool_calls'):
                tool_calls = llm_provider.parse_tool_calls(response)
            else:
                from .tool_parser import ToolCallParser
                tool_calls = ToolCallParser.parse_openai_tool_calls(response)
        else:
            content = response or ""
        
        return content, tool_calls
    
    def switch_provider(self, provider: str):
        """切换默认提供商"""
        if provider not in self._providers:
            raise ValueError(f"LLM provider '{provider}' not available")
        
        self.config.set('llm.default_provider', provider)
        logger.info(f"Switched default LLM provider to: {provider}")
    
    @property
    def available_providers(self) -> List[str]:
        """获取所有可用提供商"""
        return list(self._providers.keys())
