import json

from sqlmodel import Session, select

from app.models import ResearchProject, SearchSourceConfig
from app.schemas import (
    AvailableSourceResponse,
    CatalogOptionResponse,
    SaveSearchSourceConfigRequest,
    SearchSourceCatalogResponse,
    SearchSourceConfigResponse,
    SearchValidationMessage,
    SourceCatalogItemResponse,
    SourceImpactSummary,
    WorkspaceProjectSummary,
)
from app.services.source_catalog import (
    LANGUAGE_KEYS,
    LANGUAGE_OPTIONS,
    SEARCH_FIELD_KEYS,
    SEARCH_FIELD_OPTIONS,
    SOURCE_CATALOG,
    SOURCE_KEYS,
    source_labels_for_keys,
)

DEFAULT_ENABLED_SOURCES = ["pubmed", "embase"]
DEFAULT_SEARCH_FIELDS = ["title", "abstract"]
DEFAULT_LANGUAGES = ["en"]
NARROW_YEAR_SPAN = 3


class SearchSourceConfigError(Exception):
    """请求中携带了非法的来源 key、字段 key 或年份区间。"""


def build_source_catalog() -> SearchSourceCatalogResponse:
    return SearchSourceCatalogResponse(
        available_sources=[
            SourceCatalogItemResponse(
                key=item.key,
                label=item.label,
                description=item.description,
                supports_full_text=item.supports_full_text,
            )
            for item in SOURCE_CATALOG
        ],
        search_field_options=[
            CatalogOptionResponse(key=item.key, label=item.label)
            for item in SEARCH_FIELD_OPTIONS
        ],
        language_options=[
            CatalogOptionResponse(key=item.key, label=item.label)
            for item in LANGUAGE_OPTIONS
        ],
    )


def _validate_payload(payload: SaveSearchSourceConfigRequest) -> None:
    unknown_sources = [key for key in payload.enabled_source_keys if key not in SOURCE_KEYS]
    if unknown_sources:
        raise SearchSourceConfigError(
            f"unknown source keys: {', '.join(unknown_sources)}"
        )

    unknown_fields = [key for key in payload.search_fields if key not in SEARCH_FIELD_KEYS]
    if unknown_fields:
        raise SearchSourceConfigError(
            f"unknown search fields: {', '.join(unknown_fields)}"
        )

    unknown_languages = [key for key in payload.languages if key not in LANGUAGE_KEYS]
    if unknown_languages:
        raise SearchSourceConfigError(
            f"unknown languages: {', '.join(unknown_languages)}"
        )

    if (
        payload.year_from is not None
        and payload.year_to is not None
        and payload.year_from > payload.year_to
    ):
        raise SearchSourceConfigError(
            f"year_from {payload.year_from} must not exceed year_to {payload.year_to}"
        )


def build_source_validation_messages(
    enabled_source_keys: list[str],
    search_fields: list[str],
    year_from: int | None,
    year_to: int | None,
) -> list[SearchValidationMessage]:
    messages: list[SearchValidationMessage] = []

    if not enabled_source_keys:
        messages.append(
            SearchValidationMessage(
                level="error",
                code="MISSING_SOURCE_CONFIG",
                message="请先在数据库来源页启用至少一个来源。",
            )
        )

    if not search_fields:
        messages.append(
            SearchValidationMessage(
                level="warning",
                code="EMPTY_SEARCH_FIELDS",
                message="未选择任何检索字段，检索范围可能过窄。",
            )
        )

    if (
        year_from is not None
        and year_to is not None
        and year_to - year_from < NARROW_YEAR_SPAN
    ):
        messages.append(
            SearchValidationMessage(
                level="info",
                code="NARROW_YEAR_RANGE",
                message="当前时间窗较窄，可能遗漏早期关键研究。",
            )
        )

    return messages


def get_or_create_source_config(
    session: Session,
    project: ResearchProject,
) -> SearchSourceConfig:
    project_id = project.id or 0
    config = session.exec(
        select(SearchSourceConfig).where(SearchSourceConfig.project_id == project_id)
    ).first()

    if config is None:
        config = SearchSourceConfig(
            project_id=project_id,
            enabled_sources_json=json.dumps(DEFAULT_ENABLED_SOURCES, ensure_ascii=False),
            search_fields_json=json.dumps(DEFAULT_SEARCH_FIELDS, ensure_ascii=False),
            languages_json=json.dumps(DEFAULT_LANGUAGES, ensure_ascii=False),
        )
        session.add(config)
        session.commit()
        session.refresh(config)

    return config


def enabled_source_keys_for_project(
    session: Session,
    project: ResearchProject,
) -> list[str]:
    """供 search_query 服务读取项目当前启用的来源 key。"""
    config = get_or_create_source_config(session, project)
    return json.loads(config.enabled_sources_json)


def _build_response(
    project: ResearchProject,
    config: SearchSourceConfig,
) -> SearchSourceConfigResponse:
    enabled_keys = json.loads(config.enabled_sources_json)
    search_fields = json.loads(config.search_fields_json)
    languages = json.loads(config.languages_json)
    labels = source_labels_for_keys(enabled_keys)

    coverage_hint = (
        f"已启用 {len(enabled_keys)} 个数据库：{', '.join(labels)}"
        if labels
        else "尚未启用任何数据库"
    )
    query_impact_hint = (
        f"当前检索式的预览将基于这 {len(enabled_keys)} 个库重新计算"
        if labels
        else "检索式预览当前不可用，请先启用来源"
    )

    return SearchSourceConfigResponse(
        project=WorkspaceProjectSummary(
            id=project.id or 0,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="检索",
            updated_at_label="刚刚更新",
        ),
        stage_key="search",
        available_sources=[
            AvailableSourceResponse(
                key=item.key,
                label=item.label,
                description=item.description,
                supports_full_text=item.supports_full_text,
                enabled=item.key in set(enabled_keys),
            )
            for item in SOURCE_CATALOG
        ],
        enabled_source_keys=enabled_keys,
        search_fields=search_fields,
        year_from=config.year_from,
        year_to=config.year_to,
        languages=languages,
        config_dirty=config.config_dirty,
        impact_summary=SourceImpactSummary(
            enabled_count=len(enabled_keys),
            coverage_hint=coverage_hint,
            query_impact_hint=query_impact_hint,
        ),
        validation_messages=build_source_validation_messages(
            enabled_keys, search_fields, config.year_from, config.year_to
        ),
    )


def get_source_config(
    session: Session,
    project: ResearchProject,
) -> SearchSourceConfigResponse:
    config = get_or_create_source_config(session, project)
    return _build_response(project, config)


def save_source_config(
    session: Session,
    project: ResearchProject,
    payload: SaveSearchSourceConfigRequest,
) -> SearchSourceConfigResponse:
    _validate_payload(payload)

    config = get_or_create_source_config(session, project)
    config.enabled_sources_json = json.dumps(
        payload.enabled_source_keys, ensure_ascii=False
    )
    config.search_fields_json = json.dumps(payload.search_fields, ensure_ascii=False)
    config.languages_json = json.dumps(payload.languages, ensure_ascii=False)
    config.year_from = payload.year_from
    config.year_to = payload.year_to
    config.config_dirty = False
    session.add(config)
    session.commit()
    session.refresh(config)

    return _build_response(project, config)
