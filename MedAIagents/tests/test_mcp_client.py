"""
MCP (Model Context Protocol) 客户端模块单元测试

测试范围：
- Pydantic 类型定义验证
- MCPClient 初始化和基础行为
- MCPServerManager 多服务器管理、工具扁平化、工具调用
"""

import asyncio
import json
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, "src")

from medai.mcp import (
    MCPCallToolRequest,
    MCPCallToolResult,
    MCPClient,
    MCPInitializeRequest,
    MCPInitializeResult,
    MCPPrompt,
    MCPResource,
    MCPServerManager,
    MCPTool,
)
from medai.mcp.types import MCPClientInfo, MCPCapabilities, MCPServerInfo


# ============================================================
# 1. 类型定义测试
# ============================================================


class TestMCPTypes:
    """测试 MCP Pydantic 类型定义"""

    def test_mcp_tool_creation(self):
        """测试 MCPTool 创建和字段验证"""
        tool = MCPTool(
            name="search_patient",
            description="根据患者 ID 搜索患者信息",
            input_schema={
                "type": "object",
                "properties": {"patient_id": {"type": "string"}},
                "required": ["patient_id"],
            },
        )
        assert tool.name == "search_patient"
        assert tool.description == "根据患者 ID 搜索患者信息"
        assert tool.input_schema["type"] == "object"

    def test_mcp_resource_creation(self):
        """测试 MCPResource 创建"""
        resource = MCPResource(
            uri="file:///data/patients/12345.json",
            name="患者12345病历",
            mime_type="application/json",
        )
        assert resource.uri == "file:///data/patients/12345.json"
        assert resource.name == "患者12345病历"
        assert resource.mime_type == "application/json"

    def test_mcp_prompt_creation(self):
        """测试 MCPPrompt 创建"""
        prompt = MCPPrompt(
            name="summarize",
            description="总结文本",
            arguments=[
                {"name": "text", "description": "输入文本", "required": True}
            ],
        )
        assert prompt.name == "summarize"
        assert prompt.arguments[0].name == "text"
        assert prompt.arguments[0].required is True

    def test_mcp_call_tool_request(self):
        """测试 MCPCallToolRequest 创建"""
        req = MCPCallToolRequest(name="calc", arguments={"a": 1, "b": 2})
        assert req.name == "calc"
        assert req.arguments == {"a": 1, "b": 2}

    def test_mcp_call_tool_result(self):
        """测试 MCPCallToolResult 创建"""
        result = MCPCallToolResult(
            content=[{"type": "text", "text": "hello"}], is_error=False
        )
        assert result.content[0]["text"] == "hello"
        assert result.is_error is False

    def test_mcp_initialize_request(self):
        """测试 MCPInitializeRequest 创建和别名序列化"""
        req = MCPInitializeRequest(
            protocol_version="2024-11-05",
            capabilities=MCPCapabilities(tools={}),
            client_info=MCPClientInfo(name="test-client", version="1.0.0"),
        )
        data = req.model_dump(by_alias=True)
        assert data["protocolVersion"] == "2024-11-05"
        assert data["clientInfo"]["name"] == "test-client"

    def test_mcp_initialize_result(self):
        """测试 MCPInitializeResult 创建"""
        result = MCPInitializeResult(
            protocol_version="2024-11-05",
            capabilities=MCPCapabilities(tools={}),
            server_info=MCPServerInfo(name="test-server", version="0.1.0"),
        )
        assert result.server_info.name == "test-server"


# ============================================================
# 2. MCPClient 初始化测试
# ============================================================


class TestMCPClientInit:
    """测试 MCPClient 初始化和基础属性"""

    def test_client_default_transport(self):
        """测试默认 transport 为 stdio"""
        client = MCPClient(name="test")
        assert client.name == "test"
        assert client.transport == "stdio"
        assert client._request_id == 0
        assert client._initialized is False

    def test_client_sse_transport(self):
        """测试 SSE transport 设置"""
        client = MCPClient(name="test-sse", transport="SSE")
        assert client.transport == "sse"

    def test_client_invalid_transport(self):
        """测试不支持的 transport 在 connect 时抛出异常"""
        client = MCPClient(name="test", transport="invalid")
        with pytest.raises(ValueError, match="Unsupported transport"):
            asyncio.run(client.connect(command="echo"))

    def test_client_stdio_missing_command(self):
        """测试 stdio 模式缺少 command 时抛出异常"""
        client = MCPClient(name="test", transport="stdio")
        with pytest.raises(ValueError, match="requires 'command' parameter"):
            asyncio.run(client.connect())

    def test_client_sse_missing_url(self):
        """测试 SSE 模式缺少 url 时抛出异常"""
        client = MCPClient(name="test", transport="sse")
        with pytest.raises(ValueError, match="requires 'url' parameter"):
            asyncio.run(client.connect())


# ============================================================
# 3. MCPServerManager 管理测试
# ============================================================


@pytest.mark.asyncio
class TestMCPServerManager:
    """测试 MCPServerManager 服务器管理功能"""

    async def test_add_and_remove_server(self):
        """测试添加和移除服务器"""
        manager = MCPServerManager()

        # Mock MCPClient 以避免真实子进程/网络连接
        with patch("medai.mcp.server_manager.MCPClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.initialize = AsyncMock()
            mock_client.disconnect = AsyncMock()
            mock_client.list_tools = AsyncMock(return_value=[])
            MockClient.return_value = mock_client

            config = {
                "transport": "stdio",
                "command": "python",
                "args": ["-m", "mcp_server"],
            }
            await manager.add_server("medical_server", config)
            assert "medical_server" in manager
            assert len(manager) == 1

            await manager.remove_server("medical_server")
            assert "medical_server" not in manager
            assert len(manager) == 0
            mock_client.disconnect.assert_awaited_once()

    async def test_add_duplicate_server(self):
        """测试添加同名服务器应抛出 ValueError"""
        manager = MCPServerManager()

        with patch("medai.mcp.server_manager.MCPClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.initialize = AsyncMock()
            mock_client.disconnect = AsyncMock()
            MockClient.return_value = mock_client

            config = {"transport": "stdio", "command": "python"}
            await manager.add_server("server1", config)

            with pytest.raises(ValueError, match="already exists"):
                await manager.add_server("server1", config)

            # 清理
            await manager.remove_server("server1")

    async def test_remove_nonexistent_server(self):
        """测试移除不存在的服务器应抛出 ValueError"""
        manager = MCPServerManager()
        with pytest.raises(ValueError, match="does not exist"):
            await manager.remove_server("nonexistent")

    async def test_call_tool_on_server(self):
        """测试在指定服务器上调用工具"""
        manager = MCPServerManager()

        with patch("medai.mcp.server_manager.MCPClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.initialize = AsyncMock()
            mock_client.disconnect = AsyncMock()
            mock_client.call_tool = AsyncMock(
                return_value=MCPCallToolResult(
                    content=[{"type": "text", "text": "result"}]
                )
            )
            MockClient.return_value = mock_client

            config = {"transport": "stdio", "command": "python"}
            await manager.add_server("server_a", config)

            result = await manager.call_tool("server_a", "tool1", {"x": 1})
            assert result.content[0]["text"] == "result"
            mock_client.call_tool.assert_awaited_once_with("tool1", {"x": 1})

            await manager.remove_server("server_a")

    async def test_call_tool_server_not_found(self):
        """测试在不存在的服务器上调用工具应抛出 ValueError"""
        manager = MCPServerManager()
        with pytest.raises(ValueError, match="does not exist"):
            await manager.call_tool("missing", "tool", {})

    async def test_disconnect_all(self):
        """测试断开所有服务器连接"""
        manager = MCPServerManager()

        with patch("medai.mcp.server_manager.MCPClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.initialize = AsyncMock()
            mock_client.disconnect = AsyncMock()
            MockClient.return_value = mock_client

            await manager.add_server("s1", {"transport": "stdio", "command": "python"})
            await manager.add_server("s2", {"transport": "stdio", "command": "python"})
            assert len(manager) == 2

            await manager.disconnect_all()
            assert len(manager) == 0
            assert mock_client.disconnect.await_count == 2

    async def test_get_server_tools(self):
        """测试获取指定服务器的工具列表（缓存）"""
        manager = MCPServerManager()

        with patch("medai.mcp.server_manager.MCPClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.initialize = AsyncMock()
            mock_client.disconnect = AsyncMock()
            mock_client._cached_tools = [
                MCPTool(name="t1", description="d1", input_schema={}),
            ]
            MockClient.return_value = mock_client

            await manager.add_server("s1", {"transport": "stdio", "command": "python"})
            tools = manager.get_server_tools("s1")
            assert len(tools) == 1
            assert tools[0].name == "t1"

            await manager.disconnect_all()

    async def test_get_server_tools_not_found(self):
        """测试获取不存在服务器的工具列表应抛出 ValueError"""
        manager = MCPServerManager()
        with pytest.raises(ValueError, match="does not exist"):
            manager.get_server_tools("missing")


# ============================================================
# 4. 工具扁平化测试
# ============================================================


@pytest.mark.asyncio
class TestToolFlattening:
    """测试工具名称扁平化（server.toolname 格式）"""

    async def test_get_all_tools_flattening(self):
        """测试 get_all_tools 返回扁平化工具列表"""
        manager = MCPServerManager()

        with patch("medai.mcp.server_manager.MCPClient") as MockClient:
            mock_client_a = AsyncMock()
            mock_client_a.initialize = AsyncMock()
            mock_client_a.disconnect = AsyncMock()
            mock_client_a.list_tools = AsyncMock(
                return_value=[
                    MCPTool(name="search", description="搜索", input_schema={}),
                    MCPTool(name="calc", description="计算", input_schema={}),
                ]
            )

            mock_client_b = AsyncMock()
            mock_client_b.initialize = AsyncMock()
            mock_client_b.disconnect = AsyncMock()
            mock_client_b.list_tools = AsyncMock(
                return_value=[
                    MCPTool(name="translate", description="翻译", input_schema={}),
                ]
            )

            MockClient.side_effect = [mock_client_a, mock_client_b]

            await manager.add_server("medical", {"transport": "stdio", "command": "python"})
            await manager.add_server("nlp", {"transport": "stdio", "command": "python"})

            all_tools = await manager.get_all_tools()
            assert len(all_tools) == 3

            names = {t["name"] for t in all_tools}
            assert names == {"medical.search", "medical.calc", "nlp.translate"}

            # 检查每个工具字典的字段
            for tool in all_tools:
                assert "server_name" in tool
                assert "tool_name" in tool
                assert "name" in tool
                assert "description" in tool
                assert "input_schema" in tool
                assert tool["name"] == f"{tool['server_name']}.{tool['tool_name']}"

            await manager.disconnect_all()

    async def test_get_all_tools_empty(self):
        """测试无服务器时 get_all_tools 返回空列表"""
        manager = MCPServerManager()
        all_tools = await manager.get_all_tools()
        assert all_tools == []



class TestToolFlatteningSync:
    """同步工具扁平化测试"""

    def test_get_all_tools_sync_cached(self):
        """测试同步获取缓存的工具列表"""
        manager = MCPServerManager()
        manager._cached_all_tools = [
            {
                "server_name": "s1",
                "tool_name": "t1",
                "name": "s1.t1",
                "description": "desc",
                "input_schema": {},
            }
        ]
        tools = manager.get_all_tools_sync()
        assert len(tools) == 1
        assert tools[0]["name"] == "s1.t1"


# ============================================================
# 5. MCPClient JSON-RPC 通信 mock 测试
# ============================================================


@pytest.mark.asyncio
class TestMCPClientJSONRPC:
    """测试 MCPClient JSON-RPC 通信（使用 mock）"""

    async def test_initialize(self):
        """测试 initialize 请求发送和结果解析"""
        client = MCPClient(name="test-client", transport="stdio")

        mock_result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mock-server", "version": "0.1.0"},
        }

        with patch.object(
            client, "_send_request", new=AsyncMock(return_value=mock_result)
        ) as mock_send:
            result = await client.initialize()
            mock_send.assert_awaited_once()
            assert isinstance(result, MCPInitializeResult)
            assert result.server_info.name == "mock-server"
            assert client._initialized is True

    async def test_list_tools(self):
        """测试 list_tools 请求"""
        client = MCPClient(name="test", transport="stdio")
        mock_result = {
            "tools": [
                {"name": "tool1", "description": "desc1", "inputSchema": {}},
                {"name": "tool2", "description": "desc2", "inputSchema": {}},
            ]
        }

        with patch.object(
            client, "_send_request", new=AsyncMock(return_value=mock_result)
        ) as mock_send:
            tools = await client.list_tools()
            mock_send.assert_awaited_once_with("tools/list", {})
            assert len(tools) == 2
            assert tools[0].name == "tool1"
            assert tools[1].name == "tool2"

    async def test_call_tool(self):
        """测试 call_tool 请求"""
        client = MCPClient(name="test", transport="stdio")
        mock_result = {
            "content": [{"type": "text", "text": "success"}],
            "isError": False,
        }

        with patch.object(
            client, "_send_request", new=AsyncMock(return_value=mock_result)
        ) as mock_send:
            result = await client.call_tool("my_tool", {"arg": 1})
            mock_send.assert_awaited_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "tools/call"
            assert call_args[1]["name"] == "my_tool"
            assert call_args[1]["arguments"] == {"arg": 1}

            assert isinstance(result, MCPCallToolResult)
            assert result.content[0]["text"] == "success"
            assert result.is_error is False

    async def test_list_resources(self):
        """测试 list_resources 请求"""
        client = MCPClient(name="test", transport="stdio")
        mock_result = {
            "resources": [
                {"uri": "file:///a.txt", "name": "a", "mimeType": "text/plain"}
            ]
        }

        with patch.object(
            client, "_send_request", new=AsyncMock(return_value=mock_result)
        ):
            resources = await client.list_resources()
            assert len(resources) == 1
            assert resources[0].uri == "file:///a.txt"

    async def test_read_resource(self):
        """测试 read_resource 请求"""
        client = MCPClient(name="test", transport="stdio")
        mock_result = {"contents": "data"}

        with patch.object(
            client, "_send_request", new=AsyncMock(return_value=mock_result)
        ) as mock_send:
            result = await client.read_resource("file:///a.txt")
            mock_send.assert_awaited_once_with(
                "resources/read", {"uri": "file:///a.txt"}
            )
            assert result == {"contents": "data"}

    async def test_disconnect(self):
        """测试 disconnect 清理资源"""
        client = MCPClient(name="test", transport="stdio")
        # 模拟一个 pending future
        future = asyncio.get_event_loop().create_future()
        client._pending[1] = future

        # 使用真实 asyncio.Task 作为 _read_task，以便可以被 await
        async def dummy_task():
            await asyncio.sleep(0)

        task = asyncio.create_task(dummy_task())
        client._read_task = task
        await client.disconnect()
        assert client._initialized is False
        assert len(client._pending) == 0
        assert task.cancelled()

    async def test_request_id_increment(self):
        """测试内部 _request_id 自增"""
        client = MCPClient(name="test", transport="stdio")
        assert client._request_id == 0

        # 模拟底层 _send_stdio，让 _send_request 完整执行（包含 id 自增）
        with patch.object(
            client, "_send_stdio", new=AsyncMock()
        ):
            # list_tools 内部调用 _send_request，后者会自增 id
            with pytest.raises(RuntimeError, match="timed out"):
                await client.list_tools()
            assert client._request_id == 1

            with pytest.raises(RuntimeError, match="timed out"):
                await client.list_resources()
            assert client._request_id == 2


# ============================================================
# 6. JSON-RPC 消息处理测试
# ============================================================


class TestJSONRPCHandling:
    """测试内部 JSON-RPC 消息路由"""

    def test_handle_message_result(self):
        """测试正常 result 消息匹配到 pending future"""
        client = MCPClient(name="test")
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        client._pending[5] = future

        client._handle_message({"jsonrpc": "2.0", "id": 5, "result": {"tools": []}})
        assert future.done()
        assert future.result() == {"tools": []}
        assert 5 not in client._pending
        loop.close()

    def test_handle_message_error(self):
        """测试 error 消息匹配到 pending future"""
        client = MCPClient(name="test")
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        client._pending[3] = future

        client._handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "error": {"code": -32600, "message": "Invalid Request"},
            }
        )
        assert future.done()
        with pytest.raises(RuntimeError, match="Invalid Request"):
            future.result()
        assert 3 not in client._pending
        loop.close()

    def test_handle_message_no_id(self):
        """测试无 id 的消息被忽略"""
        client = MCPClient(name="test")
        client._handle_message({"jsonrpc": "2.0", "method": "notification"})
        # 不应抛出异常

    def test_handle_message_unknown_id(self):
        """测试未知 id 的消息被忽略"""
        client = MCPClient(name="test")
        client._handle_message({"jsonrpc": "2.0", "id": 999, "result": {}})
        # 不应抛出异常


# ============================================================
# 7. MCPServerManager 工具调用 mock 测试
# ============================================================


@pytest.mark.asyncio
class TestMCPServerManagerCallToolMock:
    """测试 MCPServerManager 工具调用（mock）"""

    async def test_manager_call_tool_mock(self):
        """测试 Manager 的 call_tool 方法正确路由到对应 client"""
        manager = MCPServerManager()

        with patch("medai.mcp.server_manager.MCPClient") as MockClient:
            mock_client_a = AsyncMock()
            mock_client_a.initialize = AsyncMock()
            mock_client_a.disconnect = AsyncMock()
            mock_client_a.call_tool = AsyncMock(
                return_value=MCPCallToolResult(
                    content=[{"type": "text", "text": "from A"}]
                )
            )

            mock_client_b = AsyncMock()
            mock_client_b.initialize = AsyncMock()
            mock_client_b.disconnect = AsyncMock()
            mock_client_b.call_tool = AsyncMock(
                return_value=MCPCallToolResult(
                    content=[{"type": "text", "text": "from B"}]
                )
            )

            MockClient.side_effect = [mock_client_a, mock_client_b]

            await manager.add_server("server_a", {"transport": "stdio", "command": "python"})
            await manager.add_server("server_b", {"transport": "stdio", "command": "python"})

            result_a = await manager.call_tool("server_a", "tool1", {"x": 1})
            assert result_a.content[0]["text"] == "from A"
            mock_client_a.call_tool.assert_awaited_once_with("tool1", {"x": 1})

            result_b = await manager.call_tool("server_b", "tool2", {"y": 2})
            assert result_b.content[0]["text"] == "from B"
            mock_client_b.call_tool.assert_awaited_once_with("tool2", {"y": 2})

            await manager.disconnect_all()

    async def test_manager_flattened_tools_unique(self):
        """测试来自不同服务器的同名工具在扁平化后唯一"""
        manager = MCPServerManager()

        with patch("medai.mcp.server_manager.MCPClient") as MockClient:
            mock_client_a = AsyncMock()
            mock_client_a.initialize = AsyncMock()
            mock_client_a.disconnect = AsyncMock()
            mock_client_a.list_tools = AsyncMock(
                return_value=[
                    MCPTool(name="search", description="医疗搜索", input_schema={}),
                ]
            )

            mock_client_b = AsyncMock()
            mock_client_b.initialize = AsyncMock()
            mock_client_b.disconnect = AsyncMock()
            mock_client_b.list_tools = AsyncMock(
                return_value=[
                    MCPTool(name="search", description="通用搜索", input_schema={}),
                ]
            )

            MockClient.side_effect = [mock_client_a, mock_client_b]

            await manager.add_server("medical", {"transport": "stdio", "command": "python"})
            await manager.add_server("general", {"transport": "stdio", "command": "python"})

            tools = await manager.get_all_tools()
            names = [t["name"] for t in tools]
            assert "medical.search" in names
            assert "general.search" in names
            assert len(names) == 2

            await manager.disconnect_all()
