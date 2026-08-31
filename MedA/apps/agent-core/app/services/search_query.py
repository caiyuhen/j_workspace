import json

from sqlmodel import Session, select

from app.models import (
    ResearchProject,
    SearchQuery,
    SearchQueryDraft,
    SearchQueryVersion,
    SearchRun,
)
from app.schemas import (
    DeriveSearchQueryDraftRequest,
    SaveSearchQueryDraftRequest,
    SearchExpressionBlock,
    SearchPreviewSummary,
    SearchQueryEditorResponse,
    SearchTermGroupSummary,
    SearchTermSummary,
    SearchValidationMessage,
    WorkspaceProjectSummary,
)
from app.services.search_source import enabled_source_keys_for_project
from app.services.source_catalog import source_labels_for_keys
from app.services.workspace import latest_project_update_label


class SearchQueryNotFoundError(Exception):
    """Raised when a query, draft, or version cannot be resolved for a project."""


def _load_query_for_project(
    session: Session,
    project: ResearchProject,
    query_id: int,
) -> SearchQuery:
    query = session.get(SearchQuery, query_id)
    if query is None or query.project_id != (project.id or 0):
        raise SearchQueryNotFoundError("query not found")

    return query


def _load_draft(session: Session, query_id: int) -> SearchQueryDraft:
    draft = session.exec(
        select(SearchQueryDraft).where(SearchQueryDraft.query_id == query_id)
    ).first()
    if draft is None:
        raise SearchQueryNotFoundError("draft not found")

    return draft


def _load_version(
    session: Session,
    query_id: int,
    version_label: str,
) -> SearchQueryVersion:
    version = session.exec(
        select(SearchQueryVersion).where(
            SearchQueryVersion.query_id == query_id,
            SearchQueryVersion.version_label == version_label,
        )
    ).first()
    if version is None:
        raise SearchQueryNotFoundError("version not found")

    return version


def _build_validation_messages(
    grouped_terms: list[SearchTermGroupSummary],
    expression_blocks: list[SearchExpressionBlock],
) -> list[SearchValidationMessage]:
    if not expression_blocks:
        return [
            SearchValidationMessage(
                level="error",
                code="EMPTY_EXPRESSION",
                message="当前检索式为空，暂不可执行。",
            )
        ]

    if len(grouped_terms) < 2:
        return [
            SearchValidationMessage(
                level="warning",
                code="MISSING_CORE_GROUP",
                message="建议至少补充两个核心主题组。",
            )
        ]

    return [
        SearchValidationMessage(
            level="info",
            code="READY_TO_SAVE",
            message="当前检索式结构完整，可继续保存或生成版本。",
        )
    ]


CORE_TERM_GROUP_KEYS = ("population", "intervention", "comparison", "outcome", "study_design")


def _build_preview_summary(
    session: Session,
    project_id: int,
    grouped_terms: list[SearchTermGroupSummary],
    selected_source_labels: list[str],
    source: str,
) -> SearchPreviewSummary:
    """预览摘要只汇报能算出来的事实：真实主题组覆盖数，以及该项目历史检索的真实命中量。"""
    covered_groups = len(
        {
            group.group_key
            for group in grouped_terms
            if group.group_key in CORE_TERM_GROUP_KEYS
            and any(term.selected for term in group.terms)
        }
    )

    if selected_source_labels:
        # 命中量不做估算，只回放这个项目已完成检索的真实区间；没跑过就说明还没有依据。
        hit_counts = [
            int(value)
            for value in session.exec(
                select(SearchRun.total_after_dedupe)
                .where(SearchRun.project_id == project_id)
                .where(SearchRun.status == "completed")
            ).all()
            if value is not None
        ]
        if not hit_counts:
            estimated_hit_band = "尚无历史检索数据"
        elif min(hit_counts) == max(hit_counts):
            estimated_hit_band = f"{min(hit_counts)}"
        else:
            estimated_hit_band = f"{min(hit_counts)}-{max(hit_counts)}"
    else:
        estimated_hit_band = "不可用"

    return SearchPreviewSummary(
        status="available" if selected_source_labels else "unavailable",
        coverage_hint=f"主题组覆盖 {covered_groups} / {len(CORE_TERM_GROUP_KEYS)}",
        database_scope_summary=(
            ", ".join(selected_source_labels) if selected_source_labels else "未选择数据库"
        ),
        estimated_hit_band=estimated_hit_band,
        last_generated_from=source,
    )


def get_or_create_search_query_editor(
    session: Session,
    project: ResearchProject,
    query_id: int | None = None,
) -> SearchQueryEditorResponse:
    project_id = project.id or 0

    if query_id is not None:
        query = _load_query_for_project(session, project, query_id)
    else:
        query = session.exec(
            select(SearchQuery).where(SearchQuery.project_id == project_id)
        ).first()

    if query is None:
        # 新建检索式不预填示例检索词，主题组与检索式都从空开始，由研究者自己录入。
        grouped_terms: list[SearchTermGroupSummary] = []
        expression_blocks: list[SearchExpressionBlock] = []
        query = SearchQuery(project_id=project_id, name="检索式 1")
        session.add(query)
        session.commit()
        session.refresh(query)

        draft = SearchQueryDraft(
            query_id=query.id or 0,
            grouped_terms_json=json.dumps([], ensure_ascii=False),
            expression_blocks_json=json.dumps([], ensure_ascii=False),
            selected_sources_json=json.dumps(
                source_labels_for_keys(enabled_source_keys_for_project(session, project)),
                ensure_ascii=False,
            ),
        )
        session.add(draft)
        session.commit()
        session.refresh(draft)
    else:
        draft = _load_draft(session, query.id or 0)
        grouped_terms = [
            SearchTermGroupSummary(**item) for item in json.loads(draft.grouped_terms_json)
        ]
        expression_blocks = [
            SearchExpressionBlock(**item)
            for item in json.loads(draft.expression_blocks_json)
        ]

    # Wave 6: 来源不再从 draft 读，改为项目级配置驱动
    enabled_keys = enabled_source_keys_for_project(session, project)
    selected_sources = source_labels_for_keys(enabled_keys)
    validation_messages = _build_validation_messages(grouped_terms, expression_blocks)
    if not enabled_keys:
        validation_messages.append(
            SearchValidationMessage(
                level="error",
                code="MISSING_SOURCE_CONFIG",
                message="请先在数据库来源页启用至少一个来源。",
            )
        )

    # Return the real version anchor so UI can show what version this draft is based on
    query_version = draft.based_on_version if draft.based_on_version != "v0" else "draft"

    return SearchQueryEditorResponse(
        project=WorkspaceProjectSummary(
            id=project_id,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="检索",
            updated_at_label=latest_project_update_label(session, project_id),
        ),
        stage_key="search",
        query_id=query.id or 0,
        query_name=query.name,
        query_version=query_version,
        query_dirty=draft.query_dirty,
        query_mode="draft",
        selected_sources=selected_sources,
        grouped_terms=grouped_terms,
        expression_blocks=expression_blocks,
        validation_messages=validation_messages,
        preview_summary=_build_preview_summary(
            session, project_id, grouped_terms, selected_sources, "draft"
        ),
    )


def save_search_query_draft(
    session: Session,
    project: ResearchProject,
    payload: SaveSearchQueryDraftRequest,
) -> SearchQueryEditorResponse:
    query = _load_query_for_project(session, project, payload.query_id)
    draft = _load_draft(session, payload.query_id)

    query.name = payload.query_name
    draft.grouped_terms_json = json.dumps(
        [item.model_dump() for item in payload.grouped_terms],
        ensure_ascii=False,
    )
    draft.expression_blocks_json = json.dumps(
        [item.model_dump() for item in payload.expression_blocks],
        ensure_ascii=False,
    )
    draft.selected_sources_json = json.dumps(payload.selected_sources, ensure_ascii=False)
    draft.query_dirty = False
    session.add(query)
    session.add(draft)
    session.commit()

    return get_or_create_search_query_editor(session, project, query.id or 0)


def save_search_query_version(
    session: Session,
    project: ResearchProject,
    payload: SaveSearchQueryDraftRequest,
) -> SearchQueryEditorResponse:
    save_search_query_draft(session, project, payload)
    query = _load_query_for_project(session, project, payload.query_id)
    draft = _load_draft(session, payload.query_id)

    current_index = int(query.latest_version.removeprefix("v"))
    next_version = f"v{current_index + 1}"
    version = SearchQueryVersion(
        query_id=payload.query_id,
        version_label=next_version,
        grouped_terms_json=draft.grouped_terms_json,
        expression_blocks_json=draft.expression_blocks_json,
        selected_sources_json=draft.selected_sources_json,
    )
    query.latest_version = next_version
    draft.based_on_version = next_version
    session.add(version)
    session.add(query)
    session.add(draft)
    session.commit()

    return get_or_create_search_query_editor(session, project, query.id or 0)


def get_search_query_snapshot(
    session: Session,
    project: ResearchProject,
    query_id: int,
    version_label: str,
) -> SearchQueryEditorResponse:
    query = _load_query_for_project(session, project, query_id)
    version = _load_version(session, query_id, version_label)

    grouped_terms = [
        SearchTermGroupSummary(**item) for item in json.loads(version.grouped_terms_json)
    ]
    expression_blocks = [
        SearchExpressionBlock(**item)
        for item in json.loads(version.expression_blocks_json)
    ]
    selected_sources = json.loads(version.selected_sources_json)

    return SearchQueryEditorResponse(
        project=WorkspaceProjectSummary(
            id=project.id or 0,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="检索",
            updated_at_label=latest_project_update_label(session, project.id or 0),
        ),
        stage_key="search",
        query_id=query_id,
        query_name=query.name,
        query_version=version_label,
        query_dirty=False,
        query_mode="snapshot",
        selected_sources=selected_sources,
        grouped_terms=grouped_terms,
        expression_blocks=expression_blocks,
        validation_messages=_build_validation_messages(grouped_terms, expression_blocks),
        preview_summary=_build_preview_summary(
            session, project.id or 0, grouped_terms, selected_sources, "snapshot"
        ),
    )


def derive_search_query_draft(
    session: Session,
    project: ResearchProject,
    payload: DeriveSearchQueryDraftRequest,
) -> SearchQueryEditorResponse:
    query = _load_query_for_project(session, project, payload.query_id)
    draft = _load_draft(session, payload.query_id)
    version = _load_version(session, payload.query_id, payload.version_label)

    draft.grouped_terms_json = version.grouped_terms_json
    draft.expression_blocks_json = version.expression_blocks_json
    draft.selected_sources_json = version.selected_sources_json
    draft.based_on_version = payload.version_label
    draft.query_dirty = False
    session.add(draft)
    session.commit()

    return get_or_create_search_query_editor(session, project, query.id or 0)
