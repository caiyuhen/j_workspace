"""
任务规划器引擎
Task Planner Engine
"""

import asyncio
import json
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from .models import SubTask, TaskPlan, TaskStatus


class TaskPlanner:
    """任务规划器

    基于 LLM 将用户请求分解为可执行子任务，并支持依赖感知的并行执行。
    """

    def __init__(self, llm_router: Any):
        """初始化任务规划器

        Args:
            llm_router: LLM 路由实例，需实现 `chat(messages, **kwargs)` 接口
        """
        self.llm_router = llm_router

    async def plan(self, user_request: str, available_tools: List[Dict]) -> TaskPlan:
        """根据用户请求生成任务计划

        Args:
            user_request: 用户原始请求
            available_tools: 可用工具列表，每项包含 name、description

        Returns:
            生成的任务计划
        """
        prompt = self._build_planning_prompt(user_request, available_tools)
        messages = [
            {"role": "system", "content": "你是一个任务分解专家，将用户请求分解为可并行执行的子任务。"},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.llm_router.chat(messages)
        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            # 降级：生成单任务计划
            return TaskPlan(
                goal=user_request,
                subtasks=[
                    SubTask(
                        id="task_1",
                        description=user_request,
                    )
                ],
            )

        return self._parse_plan(response)

    async def execute(
        self,
        plan: TaskPlan,
        executor: Any,
        max_parallel: int = 3,
    ) -> TaskPlan:
        """执行任务计划

        按依赖关系拓扑排序，并行执行无依赖的任务。
        失败任务自动重试 1 次。

        Args:
            plan: 任务计划
            executor: 执行器，需实现 `execute(tool_name, arguments)` 接口
            max_parallel: 最大并行数

        Returns:
            执行后的任务计划（含结果）
        """
        sorted_subtasks = self._topological_sort(plan.subtasks)
        if sorted_subtasks is None:
            raise ValueError("任务依赖存在循环，无法执行")

        subtask_map = {st.id: st for st in plan.subtasks}
        completed_ids: set = set()
        failed_ids: set = set()
        semaphore = asyncio.Semaphore(max_parallel)

        async def _run_single(subtask: SubTask) -> None:
            """执行单个子任务（含1次重试）"""
            async with semaphore:
                for attempt in range(2):  # 原始执行 + 1次重试
                    subtask.status = TaskStatus.RUNNING
                    logger.info(
                        f"Executing subtask {subtask.id} (attempt {attempt + 1}): "
                        f"{subtask.description}"
                    )

                    try:
                        if subtask.tool:
                            result = await executor.execute(
                                subtask.tool, subtask.arguments or {}
                            )
                        else:
                            # 无工具时，直接返回描述作为结果
                            result = {"description": subtask.description}

                        subtask.status = TaskStatus.COMPLETED
                        subtask.result = result
                        subtask.error = None
                        completed_ids.add(subtask.id)
                        logger.info(f"Subtask {subtask.id} completed")
                        return
                    except Exception as e:
                        error_msg = str(e)
                        if attempt == 0:
                            logger.warning(
                                f"Subtask {subtask.id} failed: {error_msg}, retrying..."
                            )
                            continue
                        else:
                            subtask.status = TaskStatus.FAILED
                            subtask.error = error_msg
                            failed_ids.add(subtask.id)
                            logger.error(
                                f"Subtask {subtask.id} failed after retry: {error_msg}"
                            )
                            return

        # 按拓扑层级分批执行
        pending = deque(sorted_subtasks)
        running_tasks: List[asyncio.Task] = []

        while pending or running_tasks:
            # 启动所有依赖已满足的任务
            launched = []
            for st in list(pending):
                deps_satisfied = all(
                    dep_id in completed_ids or dep_id not in subtask_map
                    for dep_id in st.dependencies
                )
                # 如果依赖的任务已失败，则本任务标记为失败（跳过）
                deps_failed = any(
                    dep_id in failed_ids for dep_id in st.dependencies
                )

                if deps_failed:
                    st.status = TaskStatus.FAILED
                    st.error = f"依赖任务失败: {st.dependencies}"
                    failed_ids.add(st.id)
                    launched.append(st)
                    continue

                if deps_satisfied and st.status == TaskStatus.PENDING:
                    task = asyncio.create_task(_run_single(st))
                    running_tasks.append(task)
                    launched.append(st)

            for st in launched:
                pending.remove(st)

            if running_tasks:
                # 等待至少一个任务完成
                done, running_tasks = await asyncio.wait(
                    running_tasks, return_when=asyncio.FIRST_COMPLETED
                )
                running_tasks = list(running_tasks)
            else:
                # 没有可运行的任务且还有未完成的，说明有循环或不可达
                if pending:
                    for st in pending:
                        st.status = TaskStatus.FAILED
                        st.error = "依赖不可达或存在循环依赖"
                    break

        plan.completed_at = datetime.now()
        return plan

    def _build_planning_prompt(self, request: str, tools: List[Dict]) -> str:
        """构建任务分解提示词"""
        tools_desc = "\n".join(
            f"- {tool.get('name', 'unknown')}: {tool.get('description', '无描述')}"
            for tool in tools
        )

        prompt = f"""请将以下用户请求分解为一系列可执行的子任务。

## 用户请求
{request}

## 可用工具
{tools_desc}

## 输出要求
请严格按照以下 JSON 格式输出任务计划，不要包含其他内容：

```json
{{
  "goal": "任务目标描述",
  "subtasks": [
    {{
      "id": "task_1",
      "description": "子任务描述",
      "tool": "可选的工具名称",
      "arguments": {{}},
      "dependencies": []
    }},
    {{
      "id": "task_2",
      "description": "子任务描述",
      "tool": "可选的工具名称",
      "arguments": {{}},
      "dependencies": ["task_1"]
    }}
  ]
}}
```

注意事项：
1. `id` 必须唯一
2. `dependencies` 填写依赖的其他子任务 id 列表
3. `tool` 和 `arguments` 仅在需要调用工具时填写
4. 尽可能并行化无依赖的子任务
5. 只输出 JSON，不要添加任何解释性文字
"""
        return prompt

    def _parse_plan(self, response: str) -> TaskPlan:
        """解析 LLM 返回的 JSON 响应"""
        # 尝试从 Markdown 代码块中提取 JSON
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            # 尝试更宽松的提取
            start = json_str.find("{")
            end = json_str.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(json_str[start : end + 1])
            else:
                raise ValueError(f"无法解析 LLM 返回的计划: {response}") from e

        subtasks = []
        for st_data in data.get("subtasks", []):
            subtasks.append(SubTask(**st_data))

        return TaskPlan(
            goal=data.get("goal", "未知目标"),
            subtasks=subtasks,
        )

    def _topological_sort(self, subtasks: List[SubTask]) -> Optional[List[SubTask]]:
        """按依赖关系对子任务进行拓扑排序

        Args:
            subtasks: 子任务列表

        Returns:
            排序后的子任务列表，如果存在循环依赖则返回 None
        """
        subtask_map = {st.id: st for st in subtasks}
        in_degree = {st.id: 0 for st in subtasks}

        # 计算入度
        for st in subtasks:
            for dep in st.dependencies:
                if dep in subtask_map:
                    in_degree[st.id] += 1

        # Kahn 算法
        queue = deque([st_id for st_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            current_id = queue.popleft()
            result.append(subtask_map[current_id])

            # 找到所有依赖 current_id 的任务，入度减 1
            for st in subtasks:
                if current_id in st.dependencies:
                    in_degree[st.id] -= 1
                    if in_degree[st.id] == 0:
                        queue.append(st.id)

        if len(result) != len(subtasks):
            return None  # 存在循环依赖

        return result
