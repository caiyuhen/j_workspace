"""任务进度聚合服务。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List


def _enum_value(value: Any) -> str:
    return getattr(value, "value", str(value))


def _iso(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def build_subtask_progress(subtask) -> Dict[str, Any]:
    """转换子任务为前端进度结构。"""
    return {
        "id": subtask.id,
        "name": subtask.name,
        "description": subtask.description,
        "status": _enum_value(subtask.status),
        "input_data": subtask.input_data or {},
        "output_data": subtask.output_data or {},
        "error_message": subtask.error_message,
        "started_at": _iso(subtask.started_at),
        "completed_at": _iso(subtask.completed_at),
        "created_at": _iso(subtask.created_at),
        "updated_at": _iso(subtask.updated_at),
    }


def build_task_progress(task, subtasks: Iterable) -> Dict[str, Any]:
    """聚合 Task + SubTask 为可视化进度详情。"""
    subtask_items: List[Dict[str, Any]] = [build_subtask_progress(subtask) for subtask in subtasks]
    total = len(subtask_items)
    completed = sum(1 for item in subtask_items if item["status"] == "completed")
    running = sum(1 for item in subtask_items if item["status"] == "running")
    failed = sum(1 for item in subtask_items if item["status"] == "failed")
    pending = sum(1 for item in subtask_items if item["status"] == "pending")
    skipped = sum(1 for item in subtask_items if item["status"] == "skipped")
    progress_percent = int((completed / total) * 100) if total else (100 if _enum_value(task.status) == "completed" else 0)

    result = task.result or {}
    return {
        "task_id": task.id,
        "conversation_id": task.conversation_id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "status": _enum_value(task.status),
        "progress_percent": progress_percent,
        "summary": {
            "total": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "pending": pending,
            "skipped": skipped,
        },
        "subtasks": subtask_items,
        "artifacts": result.get("artifacts") or [],
        "result": result,
        "waiting_for_skill": bool(result.get("waiting_for_skill") or _enum_value(task.status) == "waiting_for_skill"),
        "skill_resolution": result.get("skill_resolution") or (task.config or {}).get("skill_resolution"),
        "error_message": task.error_message,
        "duration_seconds": task.duration_seconds,
        "started_at": _iso(task.started_at),
        "completed_at": _iso(task.completed_at),
        "created_at": _iso(task.created_at),
        "updated_at": _iso(task.updated_at),
    }
