"""
工具调用框架模块
Tool Calling Framework Module

提供工具注册、参数验证和执行功能，
支持 OpenAI function calling 格式。
"""

from .registry import ToolRegistry, ToolDefinition
from .executor import ToolExecutor
from .medical_tools import register_medical_tools

__all__ = [
    "ToolRegistry",
    "ToolDefinition",
    "ToolExecutor",
    "register_medical_tools",
]
