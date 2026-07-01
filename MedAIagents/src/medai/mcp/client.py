"""
MCPClient 实现

支持 stdio 和 SSE 两种传输方式的 MCP 客户端，基于 JSON-RPC 2.0 协议通信。
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import aiohttp

from .types import (
    MCPCallToolRequest,
    MCPCallToolResult,
    MCPClientInfo,
    MCPCapabilities,
    MCPInitializeRequest,
    MCPInitializeResult,
    MCPPrompt,
    MCPResource,
    MCPTool,
)


class MCPClient:
    """MCP 协议客户端

    支持通过 stdio（子进程）或 SSE（HTTP）与 MCP Server 通信。

    Attributes:
        name: 客户端名称，用于标识。
        transport: 传输方式，"stdio" 或 "sse"。
    """

    def __init__(self, name: str, transport: str = "stdio"):
        """初始化 MCPClient。

        Args:
            name: 客户端名称。
            transport: 传输方式，可选 "stdio" 或 "sse"。
        """
        self.name = name
        self.transport = transport.lower()
        self._request_id = 0
        self._process: Optional[asyncio.subprocess.Process] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._sse_response: Optional[aiohttp.ClientResponse] = None
        self._sse_reader: Optional[asyncio.StreamReader] = None
        self._url: Optional[str] = None
        self._pending: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
        self._initialized = False

    async def connect(
        self,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        url: Optional[str] = None,
    ) -> None:
        """连接到 MCP Server。

        根据初始化时指定的 transport 类型建立连接。

        Args:
            command: stdio 模式下要执行的命令（如 "python"）。
            args: stdio 模式下命令的参数列表。
            url: sse 模式下服务器 URL。

        Raises:
            ValueError: transport 类型不支持或缺少必要参数。
            RuntimeError: 连接失败时抛出。
        """
        if self.transport == "stdio":
            if not command:
                raise ValueError("stdio transport requires 'command' parameter")
            await self._connect_stdio(command, args or [])
        elif self.transport == "sse":
            if not url:
                raise ValueError("sse transport requires 'url' parameter")
            await self._connect_sse(url)
        else:
            raise ValueError(f"Unsupported transport: {self.transport}")

    async def _connect_stdio(
        self, command: str, args: List[str]
    ) -> None:
        """通过子进程 stdio 方式连接 MCP Server。

        启动指定命令作为子进程，通过 stdin 发送 JSON-RPC 请求，
        通过 stdout 接收响应。

        Args:
            command: 要执行的命令。
            args: 命令参数列表。

        Raises:
            RuntimeError: 子进程启动失败。
        """
        try:
            self._process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to start subprocess {command}: {exc}") from exc

        # 启动读取 stdout 的后台任务
        self._read_task = asyncio.create_task(self._read_stdio_loop())

    async def _read_stdio_loop(self) -> None:
        """持续从子进程 stdout 读取 JSON-RPC 响应的后台循环。"""
        if self._process is None or self._process.stdout is None:
            return

        try:
            while True:
                line = await self._process.stdout.readline()
                if not line:
                    break
                try:
                    message = json.loads(line.decode("utf-8").strip())
                    self._handle_message(message)
                except json.JSONDecodeError:
                    continue
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def _connect_sse(self, url: str) -> None:
        """通过 HTTP SSE 方式连接 MCP Server。

        建立 SSE 连接接收服务器推送消息，通过 HTTP POST 发送请求。

        Args:
            url: MCP Server 的 SSE 端点 URL。

        Raises:
            RuntimeError: SSE 连接建立失败。
        """
        self._url = url.rstrip("/")
        self._session = aiohttp.ClientSession()

        try:
            self._sse_response = await self._session.get(
                f"{self._url}/sse",
                headers={"Accept": "text/event-stream"},
            )
            self._sse_response.raise_for_status()
        except Exception as exc:
            await self._session.close()
            self._session = None
            raise RuntimeError(f"Failed to connect to SSE endpoint {url}: {exc}") from exc

        # 启动读取 SSE 事件的后台任务
        self._read_task = asyncio.create_task(self._read_sse_loop())

    async def _read_sse_loop(self) -> None:
        """持续从 SSE 连接读取事件的后台循环。"""
        if self._sse_response is None:
            return

        try:
            async for line in self._sse_response.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    try:
                        message = json.loads(data)
                        self._handle_message(message)
                    except json.JSONDecodeError:
                        continue
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def _handle_message(self, message: Dict[str, Any]) -> None:
        """处理接收到的 JSON-RPC 消息。

        将响应匹配到对应的 pending future。

        Args:
            message: 解析后的 JSON 消息字典。
        """
        msg_id = message.get("id")
        if msg_id is None:
            return

        future = self._pending.pop(msg_id, None)
        if future is None:
            return

        if not future.done():
            if "error" in message:
                error = message["error"]
                future.set_exception(
                    RuntimeError(f"JSON-RPC error {error.get('code')}: {error.get('message')}")
                )
            else:
                future.set_result(message.get("result"))

    async def _send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """发送 JSON-RPC 请求并等待响应。

        Args:
            method: JSON-RPC 方法名。
            params: 请求参数。

        Returns:
            服务器返回的 result 字段内容。

        Raises:
            RuntimeError: 通信失败或响应错误。
        """
        self._request_id += 1
        request_id = self._request_id

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future

        if self.transport == "stdio":
            await self._send_stdio(payload)
        else:
            await self._send_sse(payload)

        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            self._pending.pop(request_id, None)
            raise RuntimeError(f"Request {method} timed out")

    async def _send_stdio(self, payload: Dict[str, Any]) -> None:
        """通过子进程 stdin 发送消息。

        Args:
            payload: 要发送的 JSON 消息字典。

        Raises:
            RuntimeError: 子进程未连接或已终止。
        """
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("stdio transport not connected")

        data = json.dumps(payload, ensure_ascii=False) + "\n"
        self._process.stdin.write(data.encode("utf-8"))
        await self._process.stdin.drain()

    async def _send_sse(self, payload: Dict[str, Any]) -> None:
        """通过 HTTP POST 发送消息到 SSE 服务端。

        Args:
            payload: 要发送的 JSON 消息字典。

        Raises:
            RuntimeError: SSE 连接未建立或 POST 失败。
        """
        if self._session is None or self._url is None:
            raise RuntimeError("sse transport not connected")

        async with self._session.post(
            f"{self._url}/message",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as resp:
            resp.raise_for_status()

    async def initialize(self) -> MCPInitializeResult:
        """发送 initialize 请求完成协议握手。

        Returns:
            服务器返回的初始化结果。

        Raises:
            RuntimeError: 初始化失败。
        """
        request = MCPInitializeRequest(
            protocol_version="2024-11-05",
            capabilities=MCPCapabilities(tools={}, resources={}, prompts={}),
            client_info=MCPClientInfo(name=self.name, version="1.0.0"),
        )
        result = await self._send_request(
            "initialize",
            request.model_dump(by_alias=True, exclude_none=True),
        )
        init_result = MCPInitializeResult.model_validate(result)
        self._initialized = True
        return init_result

    async def list_tools(self) -> List[MCPTool]:
        """获取服务器提供的工具列表。

        Returns:
            MCPTool 列表。

        Raises:
            RuntimeError: 请求失败。
        """
        result = await self._send_request("tools/list", {})
        tools = result.get("tools", [])
        return [MCPTool.model_validate(t) for t in tools]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """调用指定工具。

        Args:
            name: 工具名称。
            arguments: 工具参数。

        Returns:
            工具调用结果。

        Raises:
            RuntimeError: 调用失败。
        """
        request = MCPCallToolRequest(name=name, arguments=arguments)
        result = await self._send_request(
            "tools/call",
            request.model_dump(),
        )
        return MCPCallToolResult.model_validate(result)

    async def list_resources(self) -> List[MCPResource]:
        """获取服务器提供的资源列表。

        Returns:
            MCPResource 列表。

        Raises:
            RuntimeError: 请求失败。
        """
        result = await self._send_request("resources/list", {})
        resources = result.get("resources", [])
        return [MCPResource.model_validate(r) for r in resources]

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取指定资源内容。

        Args:
            uri: 资源 URI。

        Returns:
            资源内容字典。

        Raises:
            RuntimeError: 读取失败。
        """
        return await self._send_request("resources/read", {"uri": uri})

    async def list_prompts(self) -> List[MCPPrompt]:
        """获取服务器提供的提示词列表。

        Returns:
            MCPPrompt 列表。

        Raises:
            RuntimeError: 请求失败。
        """
        result = await self._send_request("prompts/list", {})
        prompts = result.get("prompts", [])
        return [MCPPrompt.model_validate(p) for p in prompts]

    async def disconnect(self) -> None:
        """断开与 MCP Server 的连接并清理资源。"""
        # 取消读取任务
        if self._read_task is not None and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        # 取消所有 pending 请求
        for future in self._pending.values():
            if not future.done():
                future.cancel()
        self._pending.clear()

        # 关闭 stdio 子进程
        if self._process is not None:
            if self._process.stdin is not None:
                self._process.stdin.close()
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
            self._process = None

        # 关闭 SSE 连接
        if self._sse_response is not None:
            self._sse_response.close()
            self._sse_response = None

        if self._session is not None:
            await self._session.close()
            self._session = None

        self._initialized = False
