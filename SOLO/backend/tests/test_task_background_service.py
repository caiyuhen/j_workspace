import pytest

from app.models import TaskStatus
from app.services.task_background_service import build_task_started_result, should_poll_task


def test_build_task_started_result_returns_non_blocking_payload():
    result = build_task_started_result(task_id="task-1")

    assert result["content"] == "任务已创建，正在后台执行。"
    assert result["task_status"] == TaskStatus.RUNNING.value
    assert result["async_execution"] is True
    assert result["subtasks"] == []
    assert result["artifacts"] == []


@pytest.mark.parametrize("status, expected", [
    ("pending", True),
    ("running", True),
    ("waiting_for_skill", False),
    ("completed", False),
    ("failed", False),
    ("cancelled", False),
])
def test_should_poll_task_only_for_active_execution_states(status, expected):
    assert should_poll_task(status) is expected
