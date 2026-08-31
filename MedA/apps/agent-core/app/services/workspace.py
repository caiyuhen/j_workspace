from datetime import datetime

from sqlmodel import Session, func, select

from app.models import (
    AnalysisRun,
    ArtifactRecord,
    ExtractionCell,
    ExtractionTemplate,
    GradeAssessment,
    LiteratureImportBatch,
    LiteratureRecord,
    OutcomeDefinition,
    ReportSnapshot,
    ResearchProject,
    ResearchTaskRecord,
    SearchRun,
)
from app.schemas import (
    WorkspaceAssistantSummary,
    WorkspaceHeroAction,
    WorkspaceHomeResponse,
    WorkspaceItemSummary,
    WorkspaceProjectSummary,
    WorkspaceStageSummary,
)

STAGE_DEFINITIONS: list[tuple[str, str]] = [
    ("topic", "选题"),
    ("search", "检索"),
    ("screening", "筛选"),
    ("extraction", "抽取"),
    ("analysis", "分析"),
    ("output", "产出"),
]

STAGE_LABELS = dict(STAGE_DEFINITIONS)

TASK_STATUS_LABELS = {
    "todo": "待开始",
    "in_progress": "进行中",
    "blocked": "阻塞中",
    "done": "已完成",
}

ARTIFACT_STAGE_MAP = {
    "protocol": "topic",
    "search_strategy": "search",
    "screening_log": "screening",
    "extraction_sheet": "extraction",
    "analysis_output": "analysis",
    "report": "output",
}


def _count(session: Session, statement) -> int:
    return int(session.exec(statement).one())


def _stage_status(started: bool, finished: bool) -> str:
    if finished:
        return "done"
    return "in_progress" if started else "pending"


def compute_stage_statuses(session: Session, project_id: int) -> dict[str, str]:
    """每个阶段的状态由该阶段真实落库记录推导，没有记录就是 pending。

    只看该阶段自己的产物：检索看 SearchRun/文献条目，筛选看筛选决策，抽取看模板与
    单元格，分析看结局定义与分析任务，产出看 GRADE 评估与报告快照。
    """
    protocol_artifacts = _count(
        session,
        select(func.count(ArtifactRecord.id)).where(
            ArtifactRecord.project_id == project_id,
            ArtifactRecord.artifact_type == "protocol",
        ),
    )
    topic_tasks = _count(
        session,
        select(func.count(ResearchTaskRecord.id)).where(
            ResearchTaskRecord.project_id == project_id,
            ResearchTaskRecord.stage_key == "topic",
        ),
    )

    search_runs = _count(
        session,
        select(func.count(SearchRun.id)).where(SearchRun.project_id == project_id),
    )
    imported_records = _count(
        session,
        select(func.count(LiteratureRecord.id)).where(
            LiteratureRecord.project_id == project_id
        ),
    )

    screened_records = _count(
        session,
        select(func.count(LiteratureRecord.id)).where(
            LiteratureRecord.project_id == project_id,
            LiteratureRecord.screening_stage.is_not(None),
        ),
    )
    fulltext_included = _count(
        session,
        select(func.count(LiteratureRecord.id)).where(
            LiteratureRecord.project_id == project_id,
            LiteratureRecord.screening_stage == "fulltext",
            LiteratureRecord.screening_decision == "include",
        ),
    )

    templates = _count(
        session,
        select(func.count(ExtractionTemplate.id)).where(
            ExtractionTemplate.project_id == project_id
        ),
    )
    cells = _count(
        session,
        select(func.count())
        .select_from(ExtractionCell)
        .where(ExtractionCell.project_id == project_id),
    )

    outcomes = _count(
        session,
        select(func.count(OutcomeDefinition.id)).where(
            OutcomeDefinition.project_id == project_id
        ),
    )
    analysis_runs = _count(
        session,
        select(func.count(AnalysisRun.id)).where(AnalysisRun.project_id == project_id),
    )
    analysis_completed = _count(
        session,
        select(func.count(AnalysisRun.id)).where(
            AnalysisRun.project_id == project_id,
            AnalysisRun.status == "completed",
        ),
    )

    grade_assessments = _count(
        session,
        select(func.count(GradeAssessment.id)).where(
            GradeAssessment.project_id == project_id
        ),
    )
    report_snapshots = _count(
        session,
        select(func.count(ReportSnapshot.id)).where(
            ReportSnapshot.project_id == project_id
        ),
    )

    return {
        "topic": _stage_status(
            topic_tasks > 0 or protocol_artifacts > 0, protocol_artifacts > 0
        ),
        "search": _stage_status(search_runs > 0, imported_records > 0),
        "screening": _stage_status(screened_records > 0, fulltext_included > 0),
        "extraction": _stage_status(
            templates > 0 or cells > 0,
            fulltext_included > 0 and cells >= fulltext_included,
        ),
        "analysis": _stage_status(outcomes > 0 or analysis_runs > 0, analysis_completed > 0),
        "output": _stage_status(grade_assessments > 0, report_snapshots > 0),
    }


def current_stage_label(stage_statuses: dict[str, str]) -> str:
    """当前阶段 = 第一个还没 done 的阶段；全部 done 时停在最后一个阶段。"""
    for key, label in STAGE_DEFINITIONS:
        if stage_statuses.get(key) != "done":
            return label
    return STAGE_DEFINITIONS[-1][1]


def _format_relative_label(moment: datetime) -> str:
    seconds = int((datetime.utcnow() - moment).total_seconds())
    if seconds < 60:
        return "刚刚更新"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分钟前更新"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小时前更新"
    days = hours // 24
    if days < 30:
        return f"{days} 天前更新"
    return moment.strftime("%Y-%m-%d 更新")


def _as_datetime(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


TIMESTAMPED_PROJECT_MODELS = (
    LiteratureImportBatch,
    SearchRun,
    ExtractionTemplate,
    AnalysisRun,
    GradeAssessment,
    ReportSnapshot,
)


def latest_project_update_label(session: Session, project_id: int) -> str:
    """项目最近一次真实落库时间的相对文案；没有任何带时间戳的记录时返回空串。"""
    moments: list[datetime] = []
    for model in TIMESTAMPED_PROJECT_MODELS:
        raw = session.exec(
            select(func.max(model.created_at)).where(model.project_id == project_id)
        ).one()
        moment = _as_datetime(raw)
        if moment is not None:
            moments.append(moment)
    if not moments:
        return ""
    return _format_relative_label(max(moments))


def _build_activity(session: Session, project_id: int) -> list[WorkspaceItemSummary]:
    """活动流只由真实落库记录构成，没有记录就是空态。"""
    events: list[tuple[datetime, WorkspaceItemSummary]] = []

    batches = session.exec(
        select(LiteratureImportBatch).where(
            LiteratureImportBatch.project_id == project_id
        )
    ).all()
    for batch in batches:
        moment = _as_datetime(batch.created_at)
        if moment is None:
            continue
        events.append(
            (
                moment,
                WorkspaceItemSummary(
                    title=f"导入 {batch.source_key} 文献 {batch.parsed_count} 条",
                    subtitle=f"去重 {batch.duplicate_count} 条 / 跳过 {batch.skipped_count} 条",
                    target="/workspace/activity",
                ),
            )
        )

    runs = session.exec(select(SearchRun).where(SearchRun.project_id == project_id)).all()
    for run in runs:
        moment = _as_datetime(run.created_at)
        if moment is None:
            continue
        events.append(
            (
                moment,
                WorkspaceItemSummary(
                    title=f"检索任务 #{run.id} 状态 {run.status}",
                    subtitle=f"原始命中 {run.total_hits_raw} 条 / 去重后 {run.total_after_dedupe} 条",
                    target="/workspace/activity",
                ),
            )
        )

    analysis_runs = session.exec(
        select(AnalysisRun).where(AnalysisRun.project_id == project_id)
    ).all()
    for run in analysis_runs:
        moment = _as_datetime(run.created_at)
        if moment is None:
            continue
        events.append(
            (
                moment,
                WorkspaceItemSummary(
                    title=f"分析任务 {run.method} 状态 {run.status}",
                    subtitle="分析链路已更新",
                    target="/workspace/activity",
                ),
            )
        )

    snapshots = session.exec(
        select(ReportSnapshot).where(ReportSnapshot.project_id == project_id)
    ).all()
    for snapshot in snapshots:
        moment = _as_datetime(snapshot.created_at)
        if moment is None:
            continue
        events.append(
            (
                moment,
                WorkspaceItemSummary(
                    title=f"生成报告快照 {snapshot.version_label}",
                    subtitle="产出链路已更新",
                    target="/workspace/artifacts/recent",
                ),
            )
        )

    events.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in events[:2]]


def build_workspace_home(session: Session, project: ResearchProject) -> WorkspaceHomeResponse:
    project_id = project.id or 0
    tasks = session.exec(
        select(ResearchTaskRecord).where(ResearchTaskRecord.project_id == project_id)
    ).all()
    artifacts = session.exec(
        select(ArtifactRecord).where(ArtifactRecord.project_id == project_id)
    ).all()

    stage_statuses = compute_stage_statuses(session, project_id)

    stages = [
        WorkspaceStageSummary(
            key=key,
            label=label,
            status=stage_statuses[key],
            task_count=sum(1 for task in tasks if task.stage_key == key),
            artifact_count=sum(
                1
                for artifact in artifacts
                if ARTIFACT_STAGE_MAP.get(artifact.artifact_type) == key
            ),
            target=f"/workspace/stages/{key}",
        )
        for key, label in STAGE_DEFINITIONS
    ]

    return WorkspaceHomeResponse(
        project=WorkspaceProjectSummary(
            id=project_id,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage=current_stage_label(stage_statuses),
            updated_at_label=latest_project_update_label(session, project_id),
        ),
        hero_cta=WorkspaceHeroAction(
            label="继续上次研究",
            target="/workspace/tasks/recent",
        ),
        stages=stages,
        recent_tasks=[
            WorkspaceItemSummary(
                title=task.title,
                subtitle=(
                    f"{STAGE_LABELS.get(task.stage_key, task.stage_key)}阶段 · "
                    f"{TASK_STATUS_LABELS.get(task.status, task.status)}"
                ),
                target="/workspace/tasks/recent",
            )
            for task in tasks[:2]
        ],
        recent_artifacts=[
            WorkspaceItemSummary(
                title=artifact.title,
                subtitle=(
                    f"{STAGE_LABELS.get(ARTIFACT_STAGE_MAP.get(artifact.artifact_type, ''), '未归类')}"
                    "阶段产物"
                ),
                target="/workspace/artifacts/recent",
            )
            for artifact in artifacts[:2]
        ],
        activity=_build_activity(session, project_id),
        assistant=WorkspaceAssistantSummary(
            headline="MedA 助手建议",
            primary_action_label="生成下一步建议",
            primary_action_target="/workspace/assistant",
        ),
        todos=[
            WorkspaceItemSummary(
                title=task.title,
                subtitle=TASK_STATUS_LABELS.get(task.status, task.status),
                target="/workspace/tasks/recent",
            )
            for task in tasks
            if task.status != "done"
        ][:2],
    )
