"""
Agent 编排器
Agent Orchestrator
"""

import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger

from .base import BaseAgent
from ..planner.engine import TaskPlanner
from ..planner.models import TaskStatus


class AgentOrchestrator:
    """Agent 编排器

    负责多 Agent 的注册、查找、并行分派、顺序协作和自动编排。
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """注册 Agent

        Args:
            agent: Agent 实例
        """
        if agent.name in self._agents:
            logger.warning(f"Agent '{agent.name}' already registered, overwriting")
        self._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name} (role={agent.role})")

    def get_agent(self, name: str) -> BaseAgent:
        """根据名称获取 Agent

        Args:
            name: Agent 名称

        Returns:
            Agent 实例

        Raises:
            KeyError: Agent 不存在
        """
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' 未找到")
        return self._agents[name]

    async def delegate(self, task: str, required_roles: List[str]) -> Dict[str, str]:
        """并行分派任务给多个 Agent

        Args:
            task: 任务描述
            required_roles: 需要的角色列表

        Returns:
            各 Agent 的响应字典，键为 Agent 名称
        """
        agents = []
        for role in required_roles:
            agent = self._find_agent_by_role(role)
            if agent:
                agents.append(agent)
            else:
                logger.warning(f"No agent found for role: {role}")

        if not agents:
            return {"error": f"未找到任何匹配的角色: {required_roles}"}

        async def _run_agent(agent: BaseAgent) -> tuple:
            try:
                result = await agent.run(task)
                return agent.name, result
            except Exception as e:
                logger.error(f"Agent '{agent.name}' delegate failed: {e}")
                return agent.name, f"执行失败: {str(e)}"

        # 并行执行
        results = await asyncio.gather(*[_run_agent(agent) for agent in agents])
        return dict(results)

    async def collaborate(self, task: str, agent_sequence: List[str]) -> str:
        """按顺序协作，每个 Agent 的上下文包含前面 Agent 的结果

        Args:
            task: 初始任务描述
            agent_sequence: Agent 名称序列

        Returns:
            最后一个 Agent 的响应
        """
        if not agent_sequence:
            return "未指定协作 Agent 序列"

        context = {}
        current_task = task
        last_result = ""

        for agent_name in agent_sequence:
            try:
                agent = self.get_agent(agent_name)
            except KeyError:
                logger.error(f"Agent '{agent_name}' not found in collaboration")
                last_result = f"Agent '{agent_name}' 未找到"
                context[agent_name] = last_result
                continue

            # 构建包含前面结果的上下文
            if context:
                collaborate_context = {
                    "original_task": task,
                    "previous_results": context,
                }
            else:
                collaborate_context = None

            try:
                last_result = await agent.run(current_task, context=collaborate_context)
            except Exception as e:
                logger.error(f"Agent '{agent_name}' collaboration failed: {e}")
                last_result = f"Agent '{agent_name}' 执行失败: {str(e)}"

            context[agent_name] = last_result

        return last_result

    async def auto_orchestrate(
        self,
        task: str,
        planner: TaskPlanner,
        available_tools: List[Dict] = None,
    ) -> str:
        """自动编排：先分解任务，再自动选择 Agent 执行

        Args:
            task: 用户任务
            planner: 任务规划器实例
            available_tools: 可用工具列表（如未提供则使用各 Agent 的工具）

        Returns:
            汇总后的结果
        """
        # 收集所有可用工具
        if available_tools is None:
            available_tools = []
            for agent in self._agents.values():
                for tool_def in agent.tools.list_tools():
                    available_tools.append({
                        "name": tool_def["function"]["name"],
                        "description": tool_def["function"]["description"],
                    })
            # 去重
            seen = set()
            unique_tools = []
            for tool in available_tools:
                if tool["name"] not in seen:
                    seen.add(tool["name"])
                    unique_tools.append(tool)
            available_tools = unique_tools

        # 生成任务计划
        plan = await planner.plan(task, available_tools)

        if not plan.subtasks:
            return "任务分解结果为空，无法执行。"

        # 为每个子任务选择合适的 Agent
        results_map: Dict[str, str] = {}
        completed_ids: set = set()
        pending = list(plan.subtasks)

        while pending:
            # 找出依赖已满足的子任务
            ready = []
            for st in list(pending):
                deps_ok = all(
                    dep in completed_ids or plan.get_subtask(dep) is None
                    for dep in st.dependencies
                )
                if deps_ok and st.status.value == "pending":
                    ready.append(st)

            if not ready:
                # 如果没有就绪任务但还有未完成的，可能是循环依赖
                for st in pending:
                    st.status = TaskStatus.FAILED  # type: ignore[assignment]
                    st.error = "依赖不可达"  # type: ignore[assignment]
                break

            # 并行执行就绪任务
            async def _execute_subtask(st) -> tuple:
                agent = self._select_agent_for_subtask(st)
                try:
                    # 构建上下文：包含依赖任务的结果
                    ctx = {}
                    if st.dependencies:
                        for dep_id in st.dependencies:
                            dep = plan.get_subtask(dep_id)
                            if dep and dep.result is not None:
                                ctx[f"dependency_{dep_id}"] = dep.result

                    if st.tool and agent.tools.has_tool(st.tool):
                        # 如果子任务指定了工具，使用 tool_executor 方式
                        from ..tools.executor import ToolExecutor
                        executor = ToolExecutor(agent.tools)
                        result = await agent.run_with_tools(
                            st.description,
                            context=ctx if ctx else None,
                            tool_executor=executor,
                        )
                    else:
                        result = await agent.run(
                            st.description,
                            context=ctx if ctx else None,
                        )

                    st.status = TaskStatus.COMPLETED  # type: ignore[assignment]
                    st.result = result  # type: ignore[assignment]
                    completed_ids.add(st.id)
                    return st.id, result
                except Exception as e:
                    st.status = TaskStatus.FAILED  # type: ignore[assignment]
                    st.error = str(e)  # type: ignore[assignment]
                    completed_ids.add(st.id)
                    return st.id, f"执行失败: {str(e)}"

            batch_results = await asyncio.gather(*[_execute_subtask(st) for st in ready])
            for st_id, result in batch_results:
                results_map[st_id] = result

            for st in ready:
                pending.remove(st)

        # 汇总结果
        return self._synthesize_results(results_map)

    def _find_agent_by_role(self, role: str) -> Optional[BaseAgent]:
        """根据角色查找 Agent"""
        for agent in self._agents.values():
            if agent.role == role:
                return agent
        return None

    def _select_agent_for_subtask(self, subtask) -> BaseAgent:
        """为子任务选择合适的 Agent

        根据子任务的 tool 字段或 description 中的关键词匹配。
        """
        desc = subtask.description.lower()
        tool = (subtask.tool or "").lower()

        # 工具名到角色的映射
        tool_role_map = {
            "diagnose": "clinical",
            "check_medication": "clinical",
            "generate_medical_note": "clinical",
            "analyze_imaging": "imaging",
            "search_literature": "research",
            "calculate_sample_size": "research",
            "export_document": "writing",
        }

        # 先按 tool 匹配
        for t, r in tool_role_map.items():
            if t in tool:
                agent = self._find_agent_by_role(r)
                if agent:
                    return agent

        # 再按关键词匹配
        keyword_role_map = {
            "clinical": ["诊断", "用药", "病历", "临床", "症状", "处方", "患者"],
            "imaging": ["影像", "ct", "mri", "x光", "超声", "放射", "影像", "结节"],
            "research": ["文献", "样本量", "统计", "科研", "研究", "pubmed", "rct"],
            "writing": ["论文", "写作", "撰写", "基金", "方案", "protocol", "回复信"],
            "bioinformatics": ["基因", "生信", "组学", "生存分析", "差异表达", "通路"],
        }

        for role, keywords in keyword_role_map.items():
            if any(kw in desc for kw in keywords):
                agent = self._find_agent_by_role(role)
                if agent:
                    return agent

        # 默认返回第一个注册的 Agent，或创建临时 BaseAgent
        if self._agents:
            return next(iter(self._agents.values()))

        # 没有任何 Agent 时抛出异常
        raise RuntimeError("没有可用的 Agent 来执行子任务")

    def _synthesize_results(self, results: Dict[str, str]) -> str:
        """汇总多个子任务的结果"""
        if not results:
            return "无执行结果"

        lines = ["## 任务执行结果汇总", ""]
        for idx, (task_id, result) in enumerate(results.items(), 1):
            lines.append(f"### 子任务 {idx} ({task_id})")
            lines.append(str(result))
            lines.append("")

        return "\n".join(lines)

    @property
    def agent_names(self) -> List[str]:
        """获取所有已注册 Agent 名称"""
        return list(self._agents.keys())

    @property
    def agent_roles(self) -> List[str]:
        """获取所有已注册 Agent 角色"""
        return [agent.role for agent in self._agents.values()]

    def list_agents(self) -> List[Dict[str, str]]:
        """列出所有 Agent 信息"""
        return [
            {"name": agent.name, "role": agent.role}
            for agent in self._agents.values()
        ]
