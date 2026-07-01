"""
Prompt 优化器
基于反馈历史自动优化 system prompt 和工具描述
"""

from typing import List, Dict


class PromptOptimizer:
    def __init__(self, llm_router):
        self.llm_router = llm_router

    async def optimize_system_prompt(self, current_prompt: str, role: str,
                                     feedback_history: List[Dict]) -> str:
        """基于反馈历史优化 system prompt

        Args:
            current_prompt: 当前 system prompt
            role: 角色描述，如 'medical_diagnosis'
            feedback_history: 反馈历史列表

        Returns:
            优化后的 system prompt
        """
        feedback_summary = "\n".join([
            f"- Rating {item.get('rating', 'N/A')}: {item.get('feedback', '')}"
            for item in feedback_history[:20]
        ])

        optimize_prompt = f"""You are a prompt optimization expert. Based on the feedback history, improve the following system prompt for a {role} assistant.

Current system prompt:
{current_prompt}

Feedback history:
{feedback_summary}

Please provide an improved system prompt that addresses the issues mentioned in the feedback. Return ONLY the improved prompt, without any explanation."""

        messages = [
            {'role': 'system', 'content': 'You optimize system prompts for AI assistants.'},
            {'role': 'user', 'content': optimize_prompt}
        ]

        optimized = await self.llm_router.chat(messages, temperature=0.3, max_tokens=2048)
        return optimized.strip() if isinstance(optimized, str) else str(optimized)

    async def suggest_tool_improvements(self, tool_name: str,
                                        feedback_history: List[Dict]) -> List[str]:
        """基于反馈建议工具改进

        Args:
            tool_name: 工具名称
            feedback_history: 反馈历史列表

        Returns:
            改进建议列表
        """
        relevant_feedback = [
            item for item in feedback_history
            if tool_name.lower() in (item.get('feedback', '') or '').lower()
        ]

        if not relevant_feedback:
            return ["No specific feedback found for this tool. Consider adding more detailed usage instructions."]

        feedback_summary = "\n".join([
            f"- {item.get('feedback', '')}" for item in relevant_feedback[:15]
        ])

        suggest_prompt = f"""You are a tool design expert. Based on user feedback for the tool '{tool_name}', suggest improvements to the tool's description or parameters.

Feedback:
{feedback_summary}

Please provide 3-5 concrete improvement suggestions as a numbered list."""

        messages = [
            {'role': 'system', 'content': 'You improve tool designs based on user feedback.'},
            {'role': 'user', 'content': suggest_prompt}
        ]

        response = await self.llm_router.chat(messages, temperature=0.5, max_tokens=1024)
        suggestions = []
        if isinstance(response, str):
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    suggestions.append(line.lstrip('0123456789.- ').strip())
        return suggestions if suggestions else [response.strip()]
