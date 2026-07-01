"""
工具注册表模块
Tool Registry Module
"""

from typing import Dict, Any, List, Callable, Optional
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """工具定义模型"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema 格式
    func: Optional[Callable] = None

    class Config:
        arbitrary_types_allowed = True


class ToolRegistry:
    """工具注册表
    
    管理所有可用工具的注册、查询和注销。
    支持 OpenAI function calling 格式的工具列表输出。
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        func: Callable = None
    ) -> ToolDefinition:
        """注册一个工具
        
        Args:
            name: 工具名称（唯一标识）
            description: 工具描述
            parameters: 参数 JSON Schema
            func: 工具执行函数（可选）
        
        Returns:
            注册的工具定义
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")
        
        tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            func=func
        )
        self._tools[name] = tool
        return tool
    
    def get(self, name: str) -> ToolDefinition:
        """获取工具定义
        
        Args:
            name: 工具名称
        
        Returns:
            工具定义
        
        Raises:
            KeyError: 工具不存在
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        return self._tools[name]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具（OpenAI function format）
        
        Returns:
            工具列表，格式兼容 OpenAI function calling
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self._tools.values()
        ]
    
    def unregister(self, name: str) -> bool:
        """注销工具
        
        Args:
            name: 工具名称
        
        Returns:
            是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def has_tool(self, name: str) -> bool:
        """检查工具是否存在
        
        Args:
            name: 工具名称
        
        Returns:
            是否存在
        """
        return name in self._tools
    
    @property
    def tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
