"""
MCPServerManager 实现

管理多个 MCP Server 连接，提供统一的工具发现、调用和资源访问接口。
支持工具名称扁平化（server_name.tool_name 格式）以避免命名冲突。
"""

from typing import Any, Dict, List, Optional

from .client import MCPClient
from .types import MCPCallToolResult, MCPTool


class MCPServerManager:
    """MCP Server 管理器

    管理多个 MCPClient 实例，提供聚合的工具视图和调用接口。

    Attributes:
        _servers: 存储已连接的 MCPClient 实例，键为 server_name。
        _configs: 存储每个服务器的配置信息。
    """

    def __init__(self):
        """初始化 MCPServerManager。"""
        self._servers: Dict[str, MCPClient] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}

    async def add_server(self, name: str, config: Dict[str, Any]) -> None:
        """添加并连接一个 MCP Server。

        Args:
            name: 服务器名称，用于后续标识。
            config: 服务器配置，包含以下字段：
                - transport: "stdio" 或 "sse"
                - command: stdio 模式下要执行的命令
                - args: stdio 模式下命令参数列表（可选）
                - url: sse 模式下服务器 URL

        Raises:
            ValueError: 该名称的服务器已存在。
            RuntimeError: 连接或初始化失败。
        """
        if name in self._servers:
            raise ValueError(f"Server '{name}' already exists")

        transport = config.get("transport", "stdio")
        client = MCPClient(name=name, transport=transport)

        try:
            await client.connect(
                command=config.get("command"),
                args=config.get("args"),
                url=config.get("url"),
            )
            await client.initialize()
        except Exception as exc:
            await client.disconnect()
            raise RuntimeError(f"Failed to add server '{name}': {exc}") from exc

        self._servers[name] = client
        self._configs[name] = config.copy()

    async def remove_server(self, name: str) -> None:
        """移除并断开指定 MCP Server。

        Args:
            name: 服务器名称。

        Raises:
            ValueError: 服务器不存在。
        """
        if name not in self._servers:
            raise ValueError(f"Server '{name}' does not exist")

        client = self._servers.pop(name)
        self._configs.pop(name, None)
        await client.disconnect()

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """获取所有服务器的工具列表（扁平化）。

        工具名称格式为 ``server_name.tool_name``，便于唯一标识和调用。

        Returns:
            扁平化后的工具字典列表，每个字典包含：
            - server_name: 所属服务器名称
            - tool_name: 原始工具名称
            - name: 扁平化后的全称 ``server_name.tool_name``
            - description: 工具描述
            - input_schema: 输入参数 JSON Schema
        """
        all_tools: List[Dict[str, Any]] = []
        for server_name, client in self._servers.items():
            tools = await client.list_tools()
            for tool in tools:
                flat_tool = {
                    "server_name": server_name,
                    "tool_name": tool.name,
                    "name": f"{server_name}.{tool.name}",
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                all_tools.append(flat_tool)
        self._cached_all_tools = all_tools
        return all_tools

    def get_all_tools_sync(self) -> List[Dict[str, Any]]:
        """获取所有已缓存的工具列表（扁平化，同步版本）。

        注意：此返回基于最近一次 `get_all_tools` 的缓存，
        若服务器工具动态变化，请先调用 `get_all_tools` 刷新。
        """
        return getattr(self, "_cached_all_tools", [])

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> MCPCallToolResult:
        """在指定服务器上调用工具。

        Args:
            server_name: 服务器名称。
            tool_name: 工具名称（原始名称，不含 server 前缀）。
            arguments: 工具调用参数。

        Returns:
            工具调用结果。

        Raises:
            ValueError: 服务器不存在。
            RuntimeError: 调用失败。
        """
        if server_name not in self._servers:
            raise ValueError(f"Server '{server_name}' does not exist")

        client = self._servers[server_name]
        return await client.call_tool(tool_name, arguments)

    def get_server_tools(self, server_name: str) -> List[MCPTool]:
        """获取指定服务器的工具列表。

        Args:
            server_name: 服务器名称。

        Returns:
            MCPTool 列表。

        Raises:
            ValueError: 服务器不存在。
        """
        if server_name not in self._servers:
            raise ValueError(f"Server '{server_name}' does not exist")

        # 返回 client 最近一次 list_tools 的结果（若已缓存）
        # 由于 list_tools 是异步的，这里提供一个同步接口来获取缓存
        return getattr(self._servers[server_name], "_cached_tools", [])

    async def fetch_server_tools(self, server_name: str) -> List[MCPTool]:
        """异步获取指定服务器的最新工具列表。

        Args:
            server_name: 服务器名称。

        Returns:
            MCPTool 列表。
        """
        if server_name not in self._servers:
            raise ValueError(f"Server '{server_name}' does not exist")

        tools = await self._servers[server_name].list_tools()
        self._servers[server_name]._cached_tools = tools
        return tools

    async def disconnect_all(self) -> None:
        """断开所有服务器的连接。"""
        for client in self._servers.values():
            await client.disconnect()
        self._servers.clear()
        self._configs.clear()

    def __len__(self) -> int:
        """返回当前连接的服务器数量。"""
        return len(self._servers)

    def __contains__(self, name: str) -> bool:
        """判断是否包含指定名称的服务器。"""
        return name in self._servers
