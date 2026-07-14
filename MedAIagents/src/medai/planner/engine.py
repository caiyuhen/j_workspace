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
        enable_replan: bool = True,
        max_replan: int = 2,
    ) -> TaskPlan:
        """执行任务计划（支持动态重规划 Loop）

        按依赖关系拓扑排序，并行执行无依赖的任务。
        失败任务自动重试 1 次。
        当失败比例过高或关键任务失败时，自动触发重规划。

        Args:
            plan: 任务计划
            executor: 执行器，需实现 `execute(tool_name, arguments)` 接口
            max_parallel: 最大并行数
            enable_replan: 是否启用动态重规划
            max_replan: 最大重规划次数

        Returns:
            执行后的任务计划（含结果）
        """
        original_goal = plan.goal
        replan_count = 0

        while True:
            # 执行当前 plan
            await self._execute_once(plan, executor, max_parallel)

            # 检查是否需要重规划
            if not enable_replan or replan_count >= max_replan:
                break

            should_replan, reason = self._should_replan(plan)
            if not should_replan:
                break

            logger.info(f"触发重规划 (第 {replan_count + 1} 次): {reason}")
            new_plan = await self._replan(plan, original_goal)
            plan = self._merge_replan_results(plan, new_plan)
            replan_count += 1
            logger.info(f"重规划完成，新任务数: {len(plan.subtasks)}，继续执行...")

        plan.replan_count = replan_count
        plan.completed_at = datetime.now()
        return plan

    async def _execute_once(
        self,
        plan: TaskPlan,
        executor: Any,
        max_parallel: int = 3,
    ) -> None:
        """单次执行任务计划（内部方法）

        按依赖关系拓扑排序，并行执行无依赖的任务。
        失败任务自动重试 1 次。
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
                        if subtask.tool and subtask.tool not in ('unknown', '', None):
                            try:
                                result = await executor.execute(
                                    subtask.tool, subtask.arguments or {}
                                )
                            except (KeyError, RuntimeError, ValueError) as tool_err:
                                # 工具不存在或执行失败，降级为 LLM 回答
                                logger.warning(f"Tool '{subtask.tool}' failed: {tool_err}, falling back to LLM")
                                result = {"description": subtask.description, "note": f"工具调用失败，由LLM直接生成: {str(tool_err)[:200]}"}
                        else:
                            # 无工具或工具为unknown，直接返回描述作为结果
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

    def _should_replan(self, plan: TaskPlan) -> tuple:
        """判断是否需要重规划

        Returns:
            (should_replan: bool, reason: str)
        """
        total = len(plan.subtasks)
        if total == 0:
            return False, "无子任务"

        completed = [st for st in plan.subtasks if st.status == TaskStatus.COMPLETED]
        failed = [st for st in plan.subtasks if st.status == TaskStatus.FAILED]
        failed_count = len(failed)
        completed_count = len(completed)

        # 条件1：失败比例 > 30%
        failure_rate = failed_count / total
        if failure_rate > 0.3:
            return True, f"失败比例过高 ({failure_rate:.0%}，{failed_count}/{total}个任务失败)"

        # 条件2：全部失败
        if failed_count == total:
            return True, f"所有任务均失败 ({failed_count}/{total})"

        # 条件3：关键任务失败（没有任何任务成功完成）
        if completed_count == 0 and failed_count > 0:
            return True, f"关键任务失败，无任何成功结果"

        # 条件4：失败任务包含明显的规划错误信号
        for st in failed:
            error_lower = (st.error or "").lower()
            if any(kw in error_lower for kw in ["工具", "tool", "不存在", "not found", "unknown"]):
                return True, f"任务'{st.description[:30]}'因工具/资源缺失失败，需要重新规划"

        return False, ""

    async def _replan(self, plan: TaskPlan, original_goal: str) -> TaskPlan:
        """基于执行结果重新规划任务

        将已完成的子任务结果和失败原因反馈给 LLM，生成修订后的任务计划。
        """
        # 收集已完成任务的摘要
        completed_tasks = []
        for st in plan.subtasks:
            if st.status == TaskStatus.COMPLETED:
                result_summary = ""
                if st.result:
                    if isinstance(st.result, dict):
                        result_summary = json.dumps(st.result, ensure_ascii=False, indent=2)[:500]
                    else:
                        result_summary = str(st.result)[:500]
                completed_tasks.append({
                    "id": st.id,
                    "description": st.description,
                    "result_summary": result_summary,
                })

        # 收集失败任务的原因
        failed_tasks = []
        for st in plan.subtasks:
            if st.status == TaskStatus.FAILED:
                failed_tasks.append({
                    "id": st.id,
                    "description": st.description,
                    "error": st.error or "未知错误",
                })

        prompt = self._build_replanning_prompt(
            original_goal, completed_tasks, failed_tasks
        )
        messages = [
            {"role": "system", "content": "你是一个任务规划专家。根据前序任务的执行结果，重新规划剩余任务。"},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.llm_router.chat(messages)
            new_plan = self._parse_plan(response)
            return new_plan
        except Exception as e:
            logger.error(f"Re-planning failed: {e}")
            # 重规划失败，返回空计划（表示无可补充任务）
            return TaskPlan(goal=original_goal, subtasks=[])

    def _merge_replan_results(self, old_plan: TaskPlan, new_plan: TaskPlan) -> TaskPlan:
        """合并重规划结果：保留已完成的旧任务，添加新任务

        新任务会获得新的 id，避免与旧任务冲突。
        """
        # 保留已完成的旧任务
        merged_subtasks = [
            st for st in old_plan.subtasks if st.status == TaskStatus.COMPLETED
        ]

        # 为新增任务生成新的 id
        existing_ids = {st.id for st in merged_subtasks}
        for i, st in enumerate(new_plan.subtasks):
            new_id = f"replanned_task_{i + 1}"
            while new_id in existing_ids:
                new_id = f"replanned_task_{i + 1}_{len(existing_ids)}"
                existing_ids.add(new_id)
            st.id = new_id
            # 重置状态为待执行
            st.status = TaskStatus.PENDING
            st.result = None
            st.error = None
            # 更新依赖关系（指向已完成的旧任务或新任务）
            st.dependencies = [
                dep for dep in st.dependencies if dep in existing_ids
            ]
            merged_subtasks.append(st)
            existing_ids.add(new_id)

        return TaskPlan(
            goal=old_plan.goal,
            subtasks=merged_subtasks,
        )

    def _build_replanning_prompt(
        self,
        goal: str,
        completed_tasks: List[Dict],
        failed_tasks: List[Dict],
    ) -> str:
        """构建重规划提示词"""
        completed_str = ""
        for ct in completed_tasks:
            completed_str += f"\n- [{ct['id']}] {ct['description']}\n  结果摘要: {ct['result_summary'][:200]}\n"

        failed_str = ""
        for ft in failed_tasks:
            failed_str += f"\n- [{ft['id']}] {ft['description']}\n  失败原因: {ft['error']}\n"

        prompt = f"""原任务目标：{goal}

部分任务已经执行，但后续任务因失败或规划不当需要重新规划。

## 已完成的任务（结果可直接使用）
{completed_str or "（无）"}

## 失败的任务（需要替代方案）
{failed_str or "（无）"}

## 要求
请重新规划剩余任务，以达成最终目标。注意：
1. 已完成的任务结果可以作为后续任务的输入
2. 失败的任务需要设计替代方案（更换工具、调整策略或绕过）
3. 新任务不要重复已完成的工作
4. 新任务的 dependencies 只引用已完成的任务 id

## 输出格式
请严格按照以下 JSON 格式输出，不要包含其他内容：

```json
{{
  "goal": "{goal}",
  "subtasks": [
    {{
      "id": "task_1",
      "description": "新任务描述",
      "tool": "",
      "arguments": {{}},
      "dependencies": []
    }}
  ]
}}
```

如果已完成的任务已足够达成目标，可以输出空的 subtasks 列表。"""
        return prompt

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
3. `tool` 仅在需要调用已有工具时填写工具名称，如果没有合适的工具则留空字符串 ""
4. `arguments` 仅在填写了 `tool` 时才需要
5. 尽可能并行化无依赖的子任务
6. 只输出 JSON，不要添加任何解释性文字
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
