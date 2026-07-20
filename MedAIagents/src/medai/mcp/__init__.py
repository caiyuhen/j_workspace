"""
MCP (Model Context Protocol) 模块
支持 MCP Client（消费外部工具）和 MCP Server（暴露医学工具）双向通信。
"""

from .types import (
    MCPCallToolRequest,
    MCPCallToolResult,
    MCPInitializeRequest,
    MCPInitializeResult,
    MCPPrompt,
    MCPResource,
    MCPTool,
)
from .client import MCPClient
from .server_manager import MCPServerManager
from .server import MedicalMCPServer

__all__ = [
    "MCPClient",
    "MCPServerManager",
    "MedicalMCPServer",
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    "MCPCallToolRequest",
    "MCPCallToolResult",
    "MCPInitializeRequest",
    "MCPInitializeResult",
]
