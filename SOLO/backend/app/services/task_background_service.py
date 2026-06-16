"""后台任务执行辅助服务 - 纯同步版本，完全不用 asyncio。"""
from __future__ import annotations

import logging
import threading
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from app.config import settings
from app.models import Task, TaskStatus, SubTask, AgentType

logger = logging.getLogger(__name__)


def _sync_db_url(database_url: str) -> str:
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return database_url


def build_task_started_result(task_id: str) -> Dict[str, Any]:
    """构造任务已启动的非阻塞响应。"""
    return {
        "content": "任务已创建，正在后台执行。",
        "task_id": task_id,
        "task_status": TaskStatus.RUNNING.value,
        "async_execution": True,
        "waiting_for_skill": False,
        "skill_resolution": None,
        "subtasks": [],
        "artifacts": [],
    }


def should_poll_task(status: Optional[str]) -> bool:
    """判断前端是否应继续轮询任务状态。"""
    return (status or "").lower() in {TaskStatus.PENDING.value, TaskStatus.RUNNING.value}


def _call_llm_sync(messages: list, model: Optional[str], conversation_id: str, timeout: int = 60) -> str:
    """同步调用 LLM 服务，返回响应内容。"""
    endpoint = settings.LLM_ENDPOINT.rstrip("/")
    if endpoint.endswith("/chat/completions"):
        endpoint = endpoint[:-len("/chat/completions")]
    if endpoint.endswith("/chat"):
        endpoint = endpoint[:-5]

    url = f"{endpoint}/chat/completions"
    payload = {
        "model": model or settings.LLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 8000,
    }

    # 重试机制：最多重试 2 次
    last_error = None
    for attempt in range(3):
        logger.info("🤖 调用 LLM (尝试 %d/3): model=%s", attempt + 1, model or settings.LLM_MODEL)
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            # 如果 content 为空，尝试从 reasoning_content 中提取
            if not content:
                reasoning_content = message.get("reasoning_content", "")
                content = reasoning_content
            logger.info("🤖 LLM 响应长度：%d 字符", len(content))
            return content
        except requests.exceptions.Timeout:
            last_error = f"LLM 调用超时 ({timeout}s)"
            logger.warning("🤖 %s (尝试 %d/3)", last_error, attempt + 1)
            time.sleep(2 ** attempt)
        except Exception as exc:
            last_error = f"LLM 调用失败：{exc}"
            logger.warning("🤖 %s (尝试 %d/3)", last_error, attempt + 1)
            time.sleep(2 ** attempt)

    logger.error("🤖 LLM 调用最终失败：%s", last_error)
    return ""  # 返回空字符串而不是错误信息，让后续步骤继续


def _run_task_in_thread(
    task_id: str,
    user_id: str,
    conversation_id: str,
    prompt: str,
    model: Optional[str],
    deliverable_format: str,
) -> None:
    """在独立线程中纯同步执行任务。"""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    sync_url = _sync_db_url(settings.DATABASE_URL)
    logger.info("🚀 后台线程启动: task_id=%s", task_id)

    engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)

    with Session() as db:
        try:
            task = db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
            if not task:
                logger.error("❌ 后台任务不存在: %s", task_id)
                return

            logger.info("✅ 找到任务: %s", task.title[:60])

            # Plan
            plan_steps = [
                {"name": "理解任务", "type": "planning", "agent_type": AgentType.ORCHESTRATOR.value, "description": "分析任务目标和需求"},
                {"name": "生成大纲", "type": "llm", "agent_type": AgentType.RESEARCH.value, "description": "生成结构化大纲"},
                {"name": "生成完整正文", "type": "llm", "agent_type": AgentType.RESEARCH.value, "description": "基于大纲生成完整正文"},
                {"name": "生成交付物", "type": "artifact", "agent_type": AgentType.TOOL.value, "description": "生成最终交付文件"},
            ]

            task.config = {**(task.config or {}), "model": model, "deliverable_format": deliverable_format}
            task.started_at = task.started_at or datetime.now()
            task.status = TaskStatus.RUNNING
            db.flush()
            db.commit()
            logger.info("📝 任务配置已保存: %d 步", len(plan_steps))

            # Create subtasks
            subtask_records = []
            for index, step in enumerate(plan_steps, 1):
                subtask = SubTask(
                    id=f"{task_id}-sub-{index}",
                    task_id=task_id,
                    name=step["name"],
                    description=step.get("description"),
                    agent_type=AgentType(step["agent_type"]),
                    status=TaskStatus.PENDING,
                    input_data={"step_type": step["type"], "order": index, "prompt": prompt},
                    depends_on=[],
                )
                db.add(subtask)
                subtask_records.append(subtask)
            db.flush()
            db.commit()
            logger.info("📋 子任务已创建: %d 个", len(subtask_records))

            outline_content = ""
            final_content = ""

            for subtask, step in zip(subtask_records, plan_steps):
                logger.info("▶️ 开始: %s", step["name"])
                subtask.status = TaskStatus.RUNNING
                subtask.started_at = datetime.now()
                db.flush()
                db.commit()

                try:
                    if step["type"] == "planning":
                        subtask.output_data = {"goal": prompt, "plan": plan_steps}
                        time.sleep(0.1)

                    elif step["type"] == "llm" and step["name"] == "生成大纲":
                        outline_prompt = f"""请为下面任务生成结构化大纲，输出 Markdown。

任务：{prompt}
交付物格式：{deliverable_format}"""
                        response = _call_llm_sync(
                            [{"role": "user", "content": outline_prompt}],
                            model=model,
                            conversation_id=conversation_id,
                        )
                        outline_content = response
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
                        response = _call_llm_sync(
                            [{"role": "user", "content": body_prompt}],
                            model=model,
                            conversation_id=conversation_id,
                        )
                        final_content = response
                        subtask.output_data = {"content": final_content}

                    elif step["type"] == "artifact":
                        content = final_content or outline_content or prompt
                        subtask.output_data = {"content": content, "format": deliverable_format}

                    subtask.status = TaskStatus.COMPLETED
                    subtask.completed_at = datetime.now()
                    db.flush()
                    db.commit()
                    logger.info("✅ 完成: %s", step["name"])

                except Exception as exc:
                    subtask.status = TaskStatus.FAILED
                    subtask.error_message = str(exc)
                    subtask.completed_at = datetime.now()
                    db.flush()
                    db.commit()
                    raise

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            if task.started_at:
                task.duration_seconds = int((task.completed_at - task.started_at).total_seconds())
            task.result = {
                "content": final_content,
                "plan": plan_steps,
                "subtasks": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "status": _enum_value(s.status),
                    }
                    for s in subtask_records
                ],
                "artifacts": [],
            }
            db.commit()
            logger.info("🎉 任务完成: %s，耗时 %d 秒", task_id, task.duration_seconds or 0)

        except Exception as exc:
            db.rollback()
            logger.error("❌ 后台任务异常: %s\n%s", task_id, traceback.format_exc())
            try:
                with Session() as fail_db:
                    task = fail_db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
                    if task:
                        task.status = TaskStatus.FAILED
                        task.error_message = str(exc)
                        task.completed_at = datetime.now()
                        fail_db.commit()
                        logger.info("💀 已标记任务失败: %s", task_id)
            except Exception as fail_exc:
                logger.error("标记任务失败也出错: %s", fail_exc)


def _enum_value(v) -> str:
    return v.value if hasattr(v, "value") else str(v)


def launch_task_in_background(
    task_id: str,
    user_id: str,
    conversation_id: str,
    prompt: str,
    model: Optional[str],
    deliverable_format: str,
) -> None:
    """启动 daemon 线程执行任务。"""
    logger.info("🧵 启动任务线程: task_id=%s", task_id)
    thread = threading.Thread(
        target=_run_task_in_thread,
        args=(task_id, user_id, conversation_id, prompt, model, deliverable_format),
        daemon=True,
    )
    thread.start()
    logger.info("✅ 线程已启动: %s", thread.name)
