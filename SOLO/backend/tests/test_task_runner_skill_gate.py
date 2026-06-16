import pytest

from app.models import Task, TaskStatus
from app.services.task_execution_service import TaskRunner
from tests.test_task_execution_service import FakeArtifactService, FakeDB, FakeLLMService, MissingSkillResolver


@pytest.mark.asyncio
async def test_runner_waits_for_confirmation_when_required_skill_is_missing():
    db = FakeDB()
    llm = FakeLLMService()
    artifacts = FakeArtifactService()
    runner = TaskRunner(llm_service=llm, artifact_service=artifacts, skill_resolver=MissingSkillResolver())
    task = Task(
        id="task-1",
        user_id="user-1",
        conversation_id="conv-1",
        title="检索 PubMed 文献并生成综述",
        description="检索 PubMed 文献并生成综述",
        task_type="chat_task",
        status=TaskStatus.RUNNING,
        config={"model": "cherryin-qwen3.6-plus", "deliverable_format": "docx"},
    )

    result = await runner.execute(
        db=db,
        task=task,
        user_id="user-1",
        conversation_id="conv-1",
        prompt="检索 PubMed 文献并生成综述",
        model="cherryin-qwen3.6-plus",
        deliverable_format="docx",
    )

    assert task.status == TaskStatus.WAITING_FOR_SKILL
    assert result["waiting_for_skill"] is True
    assert result["skill_resolution"]["missing_skills"][0]["candidates"][0]["id"] == "candidate_pubmed_search"
    assert llm.calls == []
    assert artifacts.calls == []
