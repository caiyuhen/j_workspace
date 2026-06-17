from datetime import datetime

from app.models import SubTask, Task, TaskStatus
from app.services.task_progress_service import build_task_progress


def test_build_task_progress_calculates_progress_and_summary():
    task = Task(
        id="task-1",
        user_id="user-1",
        conversation_id="conv-1",
        title="生成研究方案",
        description="生成研究方案",
        task_type="chat_task",
        status=TaskStatus.RUNNING,
        result={"artifacts": [{"artifact_id": "artifact-1", "filename": "方案.docx"}]},
        created_at=datetime(2026, 1, 1, 10, 0, 0),
    )
    subtasks = [
        SubTask(
            id="sub-1",
            task_id="task-1",
            name="理解任务",
            description="解析目标",
            status=TaskStatus.COMPLETED,
            output_data={"goal": "生成研究方案"},
        ),
        SubTask(
            id="sub-2",
            task_id="task-1",
            name="生成大纲",
            description="生成结构化大纲",
            status=TaskStatus.RUNNING,
            input_data={"order": 2},
        ),
        SubTask(
            id="sub-3",
            task_id="task-1",
            name="生成交付物",
            description="生成 Word 文件",
            status=TaskStatus.PENDING,
        ),
    ]

    progress = build_task_progress(task, subtasks)

    assert progress["task_id"] == "task-1"
    assert progress["status"] == "running"
    assert progress["progress_percent"] == 33
    assert progress["summary"]["total"] == 3
    assert progress["summary"]["completed"] == 1
    assert progress["summary"]["running"] == 1
    assert progress["summary"]["failed"] == 0
    assert progress["subtasks"][0]["status"] == "completed"
    assert "agent_type" not in progress["subtasks"][1], "agent_type 字段已彻底删除"
    assert progress["artifacts"][0]["artifact_id"] == "artifact-1"


def test_build_task_progress_reports_failed_status_and_error():
    task = Task(
        id="task-2",
        user_id="user-1",
        title="失败任务",
        task_type="chat_task",
        status=TaskStatus.FAILED,
        error_message="LLM 调用失败",
    )
    subtasks = [
        SubTask(
            id="sub-1",
            task_id="task-2",
            name="生成正文",
            status=TaskStatus.FAILED,
            error_message="模型超时",
        )
    ]

    progress = build_task_progress(task, subtasks)

    assert progress["status"] == "failed"
    assert progress["progress_percent"] == 0
    assert progress["error_message"] == "LLM 调用失败"
    assert progress["subtasks"][0]["error_message"] == "模型超时"
