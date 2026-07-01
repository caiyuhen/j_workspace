"""
Agent 基类
Base Agent Class
"""

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from ..tools.registry import ToolRegistry


class BaseAgent:
    """Agent 基类

    提供基础的消息构建、LLM 调用和记忆管理功能，
    支持纯对话模式和工具调用模式。
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        llm_router: Any,
    ):
        """初始化 Agent

        Args:
            name: Agent 名称
            role: Agent 角色标识（如 clinical、imaging 等）
            system_prompt: 系统提示词
            llm_router: LLM 路由实例
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm_router = llm_router
        self.memory: List[Dict] = []
        self.tools: ToolRegistry = ToolRegistry()

    async def run(self, task: str, context: Dict = None) -> str:
        """运行 Agent（纯对话模式）

        Args:
            task: 用户任务描述
            context: 额外上下文信息

        Returns:
            LLM 响应文本
        """
        messages = self._build_messages(task, context)

        try:
            response = await self.llm_router.chat(messages)
        except Exception as e:
            logger.error(f"Agent '{self.name}' run failed: {e}")
            response = f"抱歉，处理请求时出现错误：{str(e)}"

        self._record_memory("user", task)
        self._record_memory("assistant", response)
        return response

    async def run_with_tools(
        self,
        task: str,
        context: Dict = None,
        tool_executor: Any = None,
    ) -> str:
        """运行 Agent（工具调用模式）

        1. 调用 LLM 获取响应（带 tools）
        2. 如果响应包含 tool_calls，执行工具
        3. 将工具结果返回给 LLM 获取最终响应

        Args:
            task: 用户任务描述
            context: 额外上下文信息
            tool_executor: 工具执行器实例

        Returns:
            最终响应文本
        """
        messages = self._build_messages(task, context)
        tools = self.tools.list_tools()

        try:
            # 第一次调用：获取可能的 tool_calls
            if tools:
                response = await self.llm_router.chat(
                    messages, tools=tools, tool_choice="auto"
                )
            else:
                response = await self.llm_router.chat(messages)
        except Exception as e:
            logger.error(f"Agent '{self.name}' run_with_tools failed: {e}")
            response = f"抱歉，处理请求时出现错误：{str(e)}"

        # 检查是否需要调用工具（OpenAI 格式）
        tool_calls = self._extract_tool_calls(response)

        if tool_calls and tool_executor:
            # 将 assistant 消息加入上下文
            assistant_msg = {"role": "assistant", "content": ""}
            if isinstance(response, str):
                assistant_msg["content"] = response
            else:
                assistant_msg = response if isinstance(response, dict) else {"role": "assistant", "content": str(response)}
            messages.append(assistant_msg)

            # 执行工具调用
            for tool_call in tool_calls:
                tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
                arguments = tool_call.get("arguments") or tool_call.get("function", {}).get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                logger.info(f"Agent '{self.name}' calling tool: {tool_name}")
                try:
                    tool_result = await tool_executor.execute(tool_name, arguments)
                except Exception as e:
                    tool_result = {"error": str(e)}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", "unknown"),
                    "name": tool_name,
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })

            # 第二次调用：获取最终响应
            try:
                final_response = await self.llm_router.chat(messages)
            except Exception as e:
                logger.error(f"Agent '{self.name}' final call failed: {e}")
                final_response = f"工具调用后处理出现错误：{str(e)}"
        else:
            final_response = response if isinstance(response, str) else str(response)

        self._record_memory("user", task)
        self._record_memory("assistant", final_response)
        return final_response

    def _build_messages(self, task: str, context: Dict = None) -> List[Dict]:
        """构建消息列表"""
        messages = [{"role": "system", "content": self.system_prompt}]

        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2, default=str)
            messages.append({
                "role": "system",
                "content": f"【上下文信息】\n{context_str}",
            })

        messages.append({"role": "user", "content": task})
        return messages

    def _record_memory(self, role: str, content: str) -> None:
        """记录到记忆"""
        self.memory.append({"role": role, "content": content})
        # 限制记忆长度，防止无限增长
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

    def _extract_tool_calls(self, response: Any) -> List[Dict]:
        """从响应中提取工具调用列表

        支持 OpenAI 格式的 tool_calls 和普通 dict 列表。
        """
        if isinstance(response, dict):
            tool_calls = response.get("tool_calls", [])
            if tool_calls:
                return tool_calls
            # 尝试从 message 中提取
            message = response.get("message", {})
            if message:
                return message.get("tool_calls", [])
        # 字符串响应，尝试解析 JSON
        elif isinstance(response, str):
            try:
                data = json.loads(response)
                if isinstance(data, list):
                    return data
                return data.get("tool_calls", [])
            except (json.JSONDecodeError, AttributeError):
                pass
        return []

    def clear_memory(self) -> None:
        """清空记忆"""
        self.memory.clear()

    def get_memory(self, limit: int = 10) -> List[Dict]:
        """获取最近记忆"""
        return self.memory[-limit:]
