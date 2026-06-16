"""
代理基类定义

提供所有代理的基础抽象类和通用数据结构
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field


class AgentStatus(Enum):
    """代理状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    user_id: str
    conversation_id: str
    input: Any
    metadata: Dict = field(default_factory=dict)


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    success: bool
    output: Any
    error: Optional[str] = None
    metrics: Dict = field(default_factory=dict)


class BaseAgent(ABC):
    """
    代理基类
    
    所有专业代理都需要继承此类并实现execute方法。
    代理通过调用LLM服务 `/chat` 接口获取RAG增强的响应。
    """
    
    # 代理基本信息（子类需要覆盖）
    name: str = "base_agent"
    description: str = "基础代理"
    capabilities: List[str] = []
    
    def __init__(self):
        self.status = AgentStatus.IDLE
        self._llm_client = None
    
    @property
    def llm(self):
        """获取LLM客户端（延迟加载）"""
        if self._llm_client is None:
            from app.services.llm_service import llm_service
            self._llm_client = llm_service
        return self._llm_client
    
    @abstractmethod
    async def execute(self, context: TaskContext) -> TaskResult:
        """
        执行任务
        
        Args:
            context: 任务上下文，包含输入和元数据
            
        Returns:
            TaskResult: 任务执行结果
        """
        pass
    
    def can_handle(self, task_type: str) -> bool:
        """
        判断是否能处理某类型任务
        
        Args:
            task_type: 任务类型
            
        Returns:
            bool: 是否能处理
        """
        return task_type in self.capabilities
    
    async def call_llm(
        self, 
        messages: List[Dict], 
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict:
        """
        调用大模型（自动RAG增强）
        
        大模型服务会通过 `/chat` 接口自动：
        1. 解析用户查询意图
        2. 向量检索相关医学知识
        3. 知识增强生成响应
        4. 返回结果及知识来源引用
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            Dict: 大模型响应
        """
        self.status = AgentStatus.BUSY
        try:
            if "model" not in kwargs:
                context = kwargs.get("context")
                if context and getattr(context, "metadata", None):
                    kwargs["model"] = context.metadata.get("model")

            result = await self.llm.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return result
        except Exception as e:
            self.status = AgentStatus.ERROR
            raise e
        finally:
            self.status = AgentStatus.IDLE
    
    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} status={self.status.value}>"
