"""
MCP (Model Context Protocol) Server 实现

将 MedAIagents 的医学工具暴露为 MCP Server，支持 SSE 和 stdio 两种传输方式。
基于 JSON-RPC 2.0 协议。
"""

import asyncio
import json
import sys
import traceback
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from loguru import logger

from .types import MCPTool, MCPCallToolResult


class MedicalMCPServer:
    """MCP Server 实现
    
    将 ToolRegistry 中的医学工具暴露为标准 MCP tools。
    支持通过 SSE（HTTP）或 stdio（子进程）两种传输方式通信。
    
    Attributes:
        name: Server 名称
        version: Server 版本
        tool_registry: 工具注册表实例
        tool_executor: 工具执行器实例
    """
    
    def __init__(
        self,
        name: str = "MedAIagents",
        version: str = "1.0.0",
        tool_registry=None,
        tool_executor=None,
    ):
        self.name = name
        self.version = version
        self.tool_registry = tool_registry
        self.tool_executor = tool_executor
        self._initialized = False
        self._client_info: Optional[Dict[str, Any]] = None
        self._request_id = 0
    
    # ========== 工具注册表转换 ==========
    
    def _get_mcp_tools(self) -> List[MCPTool]:
        """将 ToolRegistry 中的工具转换为 MCP Tool 格式"""
        if self.tool_registry is None:
            return []
        
        mcp_tools = []
        for tool_def in self.tool_registry._tools.values():
            mcp_tools.append(MCPTool(
                name=tool_def.name,
                description=tool_def.description,
                input_schema=tool_def.parameters
            ))
        return mcp_tools
    
    def _call_tool(self, name: str, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """调用指定工具"""
        if self.tool_registry is None or not self.tool_registry.has_tool(name):
            return MCPCallToolResult(
                content=[{"type": "text", "text": f"Tool '{name}' not found"}],
                is_error=True
            )
        
        try:
            tool_def = self.tool_registry.get(name)
            
            if tool_def.func is not None:
                # 直接调用工具函数
                result = tool_def.func(**arguments)
            elif self.tool_executor is not None:
                # 通过执行器调用
                result = self.tool_executor.execute(name, arguments)
            else:
                return MCPCallToolResult(
                    content=[{"type": "text", "text": f"Tool '{name}' has no executable function"}],
                    is_error=True
                )
            
            # 序列化结果
            if isinstance(result, (dict, list)):
                text = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                text = str(result)
            
            return MCPCallToolResult(
                content=[{"type": "text", "text": text}],
                is_error=False
            )
        except Exception as e:
            logger.error(f"Tool '{name}' execution failed: {e}")
            return MCPCallToolResult(
                content=[{"type": "text", "text": f"Execution error: {str(e)}\n{traceback.format_exc()}"}],
                is_error=True
            )
    
    # ========== JSON-RPC 处理 ==========
    
    def _make_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    
    def _make_error(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    
    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单个 JSON-RPC 请求
        
        Args:
            request: JSON-RPC 请求字典
        
        Returns:
            JSON-RPC 响应字典，或 None（通知类型请求）
        """
        if request.get("jsonrpc") != "2.0":
            return self._make_error(request.get("id"), -32600, "Invalid Request: jsonrpc must be 2.0")
        
        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")
        
        # 通知类型（无 id）不返回响应
        is_notification = req_id is None
        
        try:
            if method == "initialize":
                return await self._handle_initialize(req_id, params)
            
            elif method == "initialized":
                # 客户端初始化完成通知，无需响应
                self._initialized = True
                logger.info(f"MCP Client initialized: {self._client_info}")
                return None
            
            elif method == "ping":
                return self._make_response(req_id, {})
            
            # 以下方法需要初始化完成
            if not self._initialized and method != "initialize":
                if is_notification:
                    return None
                return self._make_error(req_id, -32001, "Server not initialized")
            
            if method == "tools/list":
                return await self._handle_tools_list(req_id)
            
            elif method == "tools/call":
                return await self._handle_tools_call(req_id, params)
            
            elif method == "resources/list":
                return self._make_response(req_id, {"resources": []})
            
            elif method == "prompts/list":
                return self._make_response(req_id, {"prompts": []})
            
            else:
                if is_notification:
                    return None
                return self._make_error(req_id, -32601, f"Method not found: {method}")
        
        except Exception as e:
            logger.error(f"MCP request handling error: {e}")
            if is_notification:
                return None
            return self._make_error(req_id, -32603, f"Internal error: {str(e)}")
    
    async def _handle_initialize(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 initialize 请求"""
        self._client_info = params.get("clientInfo", {})
        self._initialized = True
        protocol_version = params.get("protocolVersion", "2024-11-05")
        
        result = {
            "protocolVersion": protocol_version,
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
            },
        }
        
        logger.info(f"MCP Server initialized by client: {self._client_info}")
        return self._make_response(req_id, result)
    
    async def _handle_tools_list(self, req_id: Any) -> Dict[str, Any]:
        """处理 tools/list 请求"""
        tools = self._get_mcp_tools()
        tools_data = []
        for tool in tools:
            tools_data.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            })
        return self._make_response(req_id, {"tools": tools_data})
    
    async def _handle_tools_call(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 tools/call 请求"""
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        result = self._call_tool(name, arguments)
        
        response = {
            "content": result.content,
        }
        if result.is_error:
            response["isError"] = True
        
        return self._make_response(req_id, response)
    
    # ========== stdio 传输 ==========
    
    async def run_stdio(self):
        """以 stdio 模式运行 MCP Server"""
        logger.info("MCP Server starting in stdio mode...")
        
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    response = self._make_error(None, -32700, "Parse error")
                    self._write_stdio(response)
                    continue
                
                response = await self.handle_request(request)
                if response is not None:
                    self._write_stdio(response)
            
            except Exception as e:
                logger.error(f"stdio handling error: {e}")
                break
        
        logger.info("MCP Server stdio mode stopped")
    
    def _write_stdio(self, response: Dict[str, Any]):
        """写入 stdout（JSON-RPC 响应）"""
        json_str = json.dumps(response, ensure_ascii=False)
        sys.stdout.write(json_str + "\n")
        sys.stdout.flush()
    
    # ========== SSE 传输（FastAPI 集成） ==========
    
    async def handle_sse_message(self, message: str) -> Optional[str]:
        """处理 SSE 消息，返回 SSE 响应字符串
        
        Args:
            message: JSON-RPC 请求 JSON 字符串
        
        Returns:
            JSON-RPC 响应 JSON 字符串，或 None
        """
        try:
            request = json.loads(message)
        except json.JSONDecodeError:
            response = self._make_error(None, -32700, "Parse error")
            return json.dumps(response, ensure_ascii=False)
        
        response = await self.handle_request(request)
        if response is not None:
            return json.dumps(response, ensure_ascii=False)
        return None
