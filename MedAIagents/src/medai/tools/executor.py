"""
工具执行器模块
Tool Executor Module
"""

import asyncio
import inspect
from typing import Dict, Any, List, Union, Tuple

from .registry import ToolRegistry


def _validate_type(value: Any, schema_type: str) -> bool:
    """基本类型验证"""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }
    expected = type_map.get(schema_type)
    if expected is None:
        return True
    if isinstance(expected, tuple):
        return isinstance(value, expected)
    return isinstance(value, expected)


def _validate_value(value: Any, schema: Dict[str, Any], path: str = "") -> Tuple[bool, str]:
    """递归验证单个值是否符合 schema"""
    if not isinstance(schema, dict):
        return True, ""

    # 验证类型
    schema_type = schema.get("type")
    if schema_type and not _validate_type(value, schema_type):
        return False, f"{path}: expected {schema_type}, got {type(value).__name__}"

    # 验证 enum
    enum_values = schema.get("enum")
    if enum_values is not None and value not in enum_values:
        return False, f"{path}: must be one of {enum_values}"

    # 验证 array items
    if schema_type == "array" and isinstance(value, list):
        items_schema = schema.get("items", {})
        for i, item in enumerate(value):
            valid, msg = _validate_value(item, items_schema, f"{path}[{i}]")
            if not valid:
                return False, msg

    # 验证 object properties
    if schema_type == "object" and isinstance(value, dict):
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in value:
                valid, msg = _validate_value(value[prop_name], prop_schema, f"{path}.{prop_name}")
                if not valid:
                    return False, msg

    return True, ""


class ToolExecutor:
    """工具执行器
    
    负责验证工具参数并执行工具调用。
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    def validate_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, str]:
        """验证工具参数
        
        Args:
            tool_name: 工具名称
            arguments: 参数字典
        
        Returns:
            (是否有效, 错误信息)
        """
        try:
            tool = self.registry.get(tool_name)
        except KeyError as e:
            return False, str(e)
        
        schema = tool.parameters
        if not isinstance(schema, dict):
            return True, ""
        
        # 检查 required
        required = schema.get("required", [])
        for field in required:
            if field not in arguments:
                return False, f"Missing required argument: '{field}'"
        
        # 验证每个参数的类型
        properties = schema.get("properties", {})
        for arg_name, arg_value in arguments.items():
            if arg_name in properties:
                valid, msg = _validate_value(arg_value, properties[arg_name], arg_name)
                if not valid:
                    return False, msg
        
        return True, ""
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            arguments: 参数字典
        
        Returns:
            工具执行结果
        
        Raises:
            KeyError: 工具不存在
            ValueError: 参数验证失败
            RuntimeError: 工具执行失败
        """
        # 获取工具定义
        tool = self.registry.get(tool_name)
        
        if tool.func is None:
            raise RuntimeError(f"Tool '{tool_name}' has no executable function")
        
        # 验证参数
        valid, error = self.validate_arguments(tool_name, arguments)
        if not valid:
            raise ValueError(f"Argument validation failed: {error}")
        
        # 执行工具
        try:
            if asyncio.iscoroutinefunction(tool.func):
                result = await tool.func(**arguments)
            else:
                # 同步函数在事件循环中运行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: tool.func(**arguments))
            return result
        except Exception as e:
            raise RuntimeError(f"Tool '{tool_name}' execution failed: {e}") from e
    
    async def execute_batch(
        self,
        calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量执行工具
        
        Args:
            calls: 调用列表，每项包含 tool_name 和 arguments
        
        Returns:
            结果列表，每项包含 success, result, error
        """
        results = []
        for call in calls:
            tool_name = call.get("tool_name")
            arguments = call.get("arguments", {})
            try:
                result = await self.execute(tool_name, arguments)
                results.append({
                    "tool_name": tool_name,
                    "success": True,
                    "result": result,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "tool_name": tool_name,
                    "success": False,
                    "result": None,
                    "error": str(e)
                })
        return results
