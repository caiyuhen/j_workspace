import pytest

from app.models import Task, TaskStatus
from app.services.task_execution_service import TaskPlanner, TaskRunner


class FakeDB:
    def __init__(self):
        self.added = []
        self.flush_count = 0
        self.commit_count = 0

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flush_count += 1

    async def commit(self):
        self.commit_count += 1


class FakeLLMService:
    def __init__(self):
        self.calls = []

    async def chat(self, messages, session_id=None, model=None, **kwargs):
        self.calls.append({"messages": messages, "session_id": session_id, "model": model})
        if "生成完整正文" in messages[-1]["content"]:
            return {"content": "# 最终交付内容\n\n## 结果\n\n- 要点一\n- 要点二"}
        return {"content": "# 任务大纲\n\n## 一、背景\n\n## 二、方案"}


class FakeArtifactService:
    def __init__(self):
        self.calls = []

    def create_artifact(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "artifact_id": "artifact-1",
            "task_id": kwargs["task_id"],
            "filename": "交付物.docx",
            "format": kwargs["artifact_format"],
            "download_url": "/api/v1/artifacts/artifact-1/download",
            "created_at": kwargs.get("created_at") or __import__("datetime").datetime.now(),
        }


class ReadySkillResolver:
    def resolve(self, prompt):
        return {"ready": True, "required_skills": [], "installed_skills": [], "missing_skills": []}


class MissingSkillResolver:
    def resolve(self, prompt):
        return {
            "ready": False,
            "required_skills": [{"required_skill_id": "skill_pubmed_search"}],
            "installed_skills": [],
            "missing_skills": [
                {
                    "required_skill_id": "skill_pubmed_search",
                    "query": "PubMed 文献检索",
                    "category": "research",
                    "candidates": [
                        {
                            "id": "candidate_pubmed_search",
                            "target_skill_id": "skill_pubmed_search",
                            "display_name": "PubMed 文献检索",
                            "description": "检索 PubMed 文献",
                            "category": "research",
                            "protocol": "skillhub",
                            "install_requires_confirmation": True,
                        }
                    ],
                    "message": "需要安装或启用 Skill 后继续执行",
                }
            ],
        }


def test_planner_creates_claw_style_steps():
    planner = TaskPlanner()

    plan = planner.create_plan("生成糖尿病研究方案", deliverable_format="pptx")

    assert plan["goal"] == "生成糖尿病研究方案"
    assert plan["deliverable_format"] == "pptx"
    assert [step["type"] for step in plan["steps"]] == ["planning", "llm", "llm", "artifact"]
    assert [step["name"] for step in plan["steps"]] == ["理解任务", "生成大纲", "生成完整正文", "生成交付物"]


@pytest.mark.asyncio
async def test_runner_creates_subtasks_executes_with_selected_model_and_builds_artifact():
    db = FakeDB()
    llm = FakeLLMService()
    artifacts = FakeArtifactService()
    runner = TaskRunner(llm_service=llm, artifact_service=artifacts, skill_resolver=ReadySkillResolver())
    task = Task(
        id="task-1",
        user_id="user-1",
        conversation_id="conv-1",
        title="生成糖尿病研究方案",
        description="生成糖尿病研究方案",
        task_type="chat_task",
        status=TaskStatus.RUNNING,
        config={"model": "cherryin-qwen3.6-plus", "deliverable_format": "docx"},
    )

    result = await runner.execute(
        db=db,
        task=task,
        user_id="user-1",
        conversation_id="conv-1",
        prompt="生成糖尿病研究方案",
        model="cherryin-qwen3.6-plus",
        deliverable_format="docx",
    )

    subtasks = [obj for obj in db.added if obj.__class__.__name__ == "SubTask"]
    assert len(subtasks) == 4
    assert all(subtask.status == TaskStatus.COMPLETED for subtask in subtasks)
    assert [call["model"] for call in llm.calls] == ["cherryin-qwen3.6-plus", "cherryin-qwen3.6-plus"]
    assert artifacts.calls[0]["artifact_format"] == "docx"
    assert artifacts.calls[0]["content"] == "# 最终交付内容\n\n## 结果\n\n- 要点一\n- 要点二"
    assert task.status == TaskStatus.COMPLETED
    assert db.commit_count >= 4
    assert result["content"] == "# 最终交付内容\n\n## 结果\n\n- 要点一\n- 要点二"
    assert result["artifacts"][0]["artifact_id"] == "artifact-1"
    assert len(result["subtasks"]) == 4
