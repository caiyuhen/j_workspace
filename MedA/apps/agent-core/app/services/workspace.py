from sqlmodel import Session, select

from app.models import ArtifactRecord, ResearchProject, ResearchTaskRecord
from app.schemas import (
    WorkspaceAssistantSummary,
    WorkspaceHeroAction,
    WorkspaceHomeResponse,
    WorkspaceItemSummary,
    WorkspaceProjectSummary,
    WorkspaceStageSummary,
)

STAGE_DEFINITIONS: list[tuple[str, str, str]] = [
    ("topic", "选题", "done"),
    ("search", "检索", "done"),
    ("screening", "筛选", "in_progress"),
    ("extraction", "抽取", "pending"),
    ("analysis", "分析", "pending"),
    ("output", "产出", "pending"),
]

ARTIFACT_STAGE_MAP = {
    "protocol": "topic",
    "search_strategy": "search",
    "screening_log": "screening",
    "extraction_sheet": "extraction",
    "analysis_output": "analysis",
    "report": "output",
}


def _take_with_fallback[T](items: list[T], fallback_items: list[T], count: int) -> list[T]:
    return (items + fallback_items)[:count]


def _build_default_tasks(project_id: int) -> list[ResearchTaskRecord]:
    return [
        ResearchTaskRecord(
            project_id=project_id,
            title="完善纳排标准草案",
            stage_key="screening",
            status="in_progress",
        ),
        ResearchTaskRecord(
            project_id=project_id,
            title="补充文献检索式",
            stage_key="search",
            status="todo",
        ),
    ]


def _build_default_artifacts(project_id: int) -> list[ArtifactRecord]:
    return [
        ArtifactRecord(
            project_id=project_id,
            artifact_type="protocol",
            title="方案初稿 v0.3",
        ),
        ArtifactRecord(
            project_id=project_id,
            artifact_type="search_strategy",
            title="文献检索式 v0.2",
        ),
    ]


def build_workspace_home(session: Session, project: ResearchProject) -> WorkspaceHomeResponse:
    project_id = project.id or 0
    tasks = session.exec(
        select(ResearchTaskRecord).where(ResearchTaskRecord.project_id == project_id)
    ).all()
    artifacts = session.exec(
        select(ArtifactRecord).where(ArtifactRecord.project_id == project_id)
    ).all()

    if not tasks:
        tasks = _build_default_tasks(project_id)

    if not artifacts:
        artifacts = _build_default_artifacts(project_id)

    recent_tasks = _take_with_fallback(tasks, _build_default_tasks(project_id), 2)
    recent_artifacts = _take_with_fallback(
        artifacts, _build_default_artifacts(project_id), 2
    )

    stages = [
        WorkspaceStageSummary(
            key=key,
            label=label,
            status=status,
            task_count=sum(1 for task in tasks if task.stage_key == key),
            artifact_count=sum(
                1
                for artifact in artifacts
                if ARTIFACT_STAGE_MAP.get(artifact.artifact_type) == key
            ),
            target=f"/workspace/stages/{key}",
        )
        for key, label, status in STAGE_DEFINITIONS
    ]

    return WorkspaceHomeResponse(
        project=WorkspaceProjectSummary(
            id=project_id,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="方案设计",
            updated_at_label="刚刚更新",
        ),
        hero_cta=WorkspaceHeroAction(
            label="继续上次研究",
            target="/workspace/tasks/recent",
        ),
        stages=stages,
        recent_tasks=[
            WorkspaceItemSummary(
                title=recent_tasks[0].title,
                subtitle="继续完善当前任务",
                target="/workspace/tasks/recent",
            ),
            WorkspaceItemSummary(
                title=recent_tasks[1].title,
                subtitle="检索策略待补充",
                target="/workspace/tasks/recent",
            ),
        ],
        recent_artifacts=[
            WorkspaceItemSummary(
                title=recent_artifacts[0].title,
                subtitle="最近修改于 5 分钟前",
                target="/workspace/artifacts/recent",
            ),
            WorkspaceItemSummary(
                title=recent_artifacts[1].title,
                subtitle="最近修改于 20 分钟前",
                target="/workspace/artifacts/recent",
            ),
        ],
        activity=[
            WorkspaceItemSummary(
                title="文献筛选阶段已进入进行中",
                subtitle="系统同步了最新阶段状态",
                target="/workspace/activity",
            ),
            WorkspaceItemSummary(
                title="新增方案初稿版本",
                subtitle="产物链路已更新",
                target="/workspace/artifacts/recent",
            ),
        ],
        assistant=WorkspaceAssistantSummary(
            headline="MedA 助手建议",
            primary_action_label="生成下一步建议",
            primary_action_target="/workspace/assistant",
        ),
        todos=[
            WorkspaceItemSummary(
                title="确认研究终点定义",
                subtitle="今日到期",
                target="/workspace/tasks/recent",
            ),
            WorkspaceItemSummary(
                title="审核入排标准变更",
                subtitle="等待 PI 确认",
                target="/workspace/tasks/recent",
            ),
        ],
    )
