"""
工具调用解析器
支持多提供商格式的工具调用解析与标准化
"""

from typing import List, Dict, Any


class ToolCallParser:
    """工具调用解析器，支持多提供商格式"""

    @staticmethod
    def parse_openai_tool_calls(response) -> List[Dict]:
        """解析 OpenAI 格式的 tool_calls

        OpenAI 格式: response.choices[0].message.tool_calls
        """
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

    @staticmethod
    def parse_anthropic_tool_calls(response) -> List[Dict]:
        """解析 Anthropic 格式的 tool_calls（预留）"""
        # Anthropic tool use 格式预留实现
        return []

    @staticmethod
    def normalize_tool_call(tool_call) -> Dict:
        """将 tool_call 统一为标准字典格式

        Args:
            tool_call: 可以是字典或 SDK 返回的对象

        Returns:
            标准格式的字典:
            {
                'id': str,
                'type': str,
                'function': {
                    'name': str,
                    'arguments': str
                }
            }
        """
        if isinstance(tool_call, dict):
            func = tool_call.get('function', {}) or {}
            if not isinstance(func, dict):
                func = {}
            return {
                'id': tool_call.get('id'),
                'type': tool_call.get('type', 'function'),
                'function': {
                    'name': func.get('name'),
                    'arguments': func.get('arguments'),
                }
            }

        # 处理对象类型（如 OpenAI SDK 返回的对象）
        normalized = {
            'id': getattr(tool_call, 'id', None),
            'type': getattr(tool_call, 'type', 'function'),
            'function': {
                'name': None,
                'arguments': None,
            }
        }
        func = getattr(tool_call, 'function', None)
        if func:
            normalized['function']['name'] = getattr(func, 'name', None)
            normalized['function']['arguments'] = getattr(func, 'arguments', None)

        return normalized
