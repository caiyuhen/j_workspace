"""Claw/Hermes 风格任务计划与执行服务。"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models import AgentType, SubTask, Task, TaskStatus
from app.services.artifact_service import artifact_service as default_artifact_service
from app.services.llm_service import llm_service as default_llm_service
from app.services.skill_resolver import skill_resolver as default_skill_resolver


def _enum_value(value: Any) -> str:
    return getattr(value, "value", str(value))


class TaskPlanner:
    """把用户提示语转为可执行任务计划。"""

    def create_plan(self, prompt: str, deliverable_format: str = "md") -> Dict[str, Any]:
        goal = (prompt or "任务").strip()
        artifact_label = {
            "md": "生成 Markdown 交付物",
            "docx": "生成 Word 交付物",
            "xlsx": "生成 Excel 交付物",
            "pptx": "生成 PPT 交付物",
        }.get((deliverable_format or "md").lower(), "生成交付物")
        return {
            "goal": goal,
            "deliverable_format": (deliverable_format or "md").lower(),
            "steps": [
                {
                    "name": "理解任务",
                    "type": "planning",
                    "agent_type": AgentType.ORCHESTRATOR.value,
                    "description": "解析用户目标、交付物格式和执行边界。",
                },
                {
                    "name": "生成大纲",
                    "type": "llm",
                    "agent_type": AgentType.RESEARCH.value,
                    "description": "根据任务目标生成结构化大纲。",
                },
                {
                    "name": "生成完整正文",
                    "type": "llm",
                    "agent_type": AgentType.RESEARCH.value,
                    "description": "基于大纲生成完整交付内容。",
                },
                {
                    "name": "生成交付物",
                    "type": "artifact",
                    "agent_type": AgentType.TOOL.value,
                    "description": artifact_label,
                },
            ],
        }


class TaskRunner:
    """执行任务计划、更新子任务状态并生成交付物。"""

    def __init__(self, llm_service=None, artifact_service=None, planner: Optional[TaskPlanner] = None, skill_resolver=None):
        self.llm_service = llm_service or default_llm_service
        self.artifact_service = artifact_service or default_artifact_service
        self.planner = planner or TaskPlanner()
        self.skill_resolver = skill_resolver or default_skill_resolver

    @staticmethod
    async def _persist(db) -> None:
        """刷新并尽快提交进度，确保前端轮询能看到真实状态。"""
        flush_result = db.flush()
        if hasattr(flush_result, "__await__"):
            await flush_result
        commit = getattr(db, "commit", None)
        if commit:
            commit_result = commit()
            if hasattr(commit_result, "__await__"):
                await commit_result

    @staticmethod
    def _subtask_payload(subtask: SubTask) -> Dict[str, Any]:
        return {
            "id": subtask.id,
            "name": subtask.name,
            "description": subtask.description,
            "agent_type": _enum_value(subtask.agent_type),
            "status": _enum_value(subtask.status),
            "input_data": subtask.input_data or {},
            "output_data": subtask.output_data or {},
            "error_message": subtask.error_message,
        }

    async def execute(
        self,
        db,
        task: Task,
        user_id: str,
        conversation_id: str,
        prompt: str,
        model: Optional[str],
        deliverable_format: str = "md",
    ) -> Dict[str, Any]:
        plan = self.planner.create_plan(prompt, deliverable_format=deliverable_format)
        skill_resolution = self.skill_resolver.resolve(prompt)
        task.config = {
            **(task.config or {}),
            "plan": plan,
            "model": model,
            "deliverable_format": deliverable_format,
            "skill_resolution": skill_resolution,
        }
        task.started_at = task.started_at or datetime.now()
        if not skill_resolution.get("ready", True):
            task.status = TaskStatus.WAITING_FOR_SKILL
            task.result = {
                "content": "任务需要安装或启用 Skill 后继续执行。",
                "waiting_for_skill": True,
                "skill_resolution": skill_resolution,
                "plan": plan,
                "subtasks": [],
                "artifacts": [],
            }
            await self._persist(db)
            return task.result

        task.status = TaskStatus.RUNNING

        subtasks: List[SubTask] = []
        for index, step in enumerate(plan["steps"], 1):
            subtask = SubTask(
                id=str(uuid.uuid4()),
                task_id=task.id,
                name=step["name"],
                description=step.get("description"),
                agent_type=AgentType(step.get("agent_type") or AgentType.TOOL.value),
                status=TaskStatus.PENDING,
                input_data={"step_type": step["type"], "order": index, "prompt": prompt},
                depends_on=[subtasks[-1].id] if subtasks else [],
            )
            db.add(subtask)
            subtasks.append(subtask)
        await self._persist(db)

        outline_content = ""
        final_content = ""
        artifacts: List[Dict[str, Any]] = []

        try:
            for subtask, step in zip(subtasks, plan["steps"]):
                subtask.status = TaskStatus.RUNNING
                subtask.started_at = datetime.now()
                await self._persist(db)

                if step["type"] == "planning":
                    subtask.output_data = {"goal": plan["goal"], "plan": plan}
                elif step["type"] == "llm" and step["name"] == "生成大纲":
                    outline_prompt = f"""请为下面任务生成结构化大纲，输出 Markdown。

任务：{prompt}
交付物格式：{deliverable_format}"""
                    response = await self.llm_service.chat(
                        [{"role": "user", "content": outline_prompt}],
                        session_id=conversation_id,
                        model=model,
                    )
                    outline_content = response.get("content", "") if isinstance(response, dict) else str(response)
                    subtask.output_data = {"content": outline_content}
                elif step["type"] == "llm" and step["name"] == "生成完整正文":
                    body_prompt = f"""请基于任务和大纲生成完整正文，输出可直接转换为 {deliverable_format} 文件的 Markdown 内容。

任务：{prompt}

大纲：
{outline_content}

要求：
1. 内容完整，不要只给建议。
2. 包含标题、目标、主体内容、结论/下一步。
3. 如适合表格，请使用 Markdown 表格。"""
                    response = await self.llm_service.chat(
                        [{"role": "user", "content": body_prompt}],
                        session_id=conversation_id,
                        model=model,
                    )
                    final_content = response.get("content", "") if isinstance(response, dict) else str(response)
                    subtask.output_data = {"content": final_content}
                elif step["type"] == "artifact":
                    artifact = self.artifact_service.create_artifact(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        task_id=task.id,
                        title=prompt,
                        content=final_content or outline_content or prompt,
                        artifact_format=deliverable_format,
                    )
                    artifacts = [artifact]
                    subtask.output_data = {"artifacts": artifacts}

                subtask.status = TaskStatus.COMPLETED
                subtask.completed_at = datetime.now()
                await self._persist(db)

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            if task.started_at:
                task.duration_seconds = int((task.completed_at - task.started_at).total_seconds())
            task.result = {
                "content": final_content,
                "plan": plan,
                "subtasks": [self._subtask_payload(subtask) for subtask in subtasks],
                "artifacts": artifacts,
                "skill_resolution": skill_resolution,
                "waiting_for_skill": False,
            }
            await self._persist(db)
            return task.result
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            task.completed_at = datetime.now()
            for subtask in subtasks:
                if subtask.status == TaskStatus.RUNNING:
                    subtask.status = TaskStatus.FAILED
                    subtask.error_message = str(exc)
                    subtask.completed_at = datetime.now()
            await self._persist(db)
            raise


task_planner = TaskPlanner()
task_runner = TaskRunner(planner=task_planner)
