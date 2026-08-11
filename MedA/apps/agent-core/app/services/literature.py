from sqlmodel import Session, select

from app.models import LiteratureImportBatch, LiteratureRecord, ResearchProject
from app.schemas import (
    CreateLiteratureRecordRequest,
    ImportLiteratureRequest,
    ImportResultSummary,
    LiteratureBatchSummary,
    LiteratureLibraryResponse,
    LiteratureRecordSummary,
    LiteratureSourceCount,
    LiteratureStats,
    SourceCatalogItemResponse,
    WorkspaceProjectSummary,
)
from app.services.literature_parser import parse_literature_text
from app.services.source_catalog import SOURCE_CATALOG, SOURCE_KEYS

UNIQUE_STATUSES = {"unique", "confirmed_unique"}


class LiteratureError(Exception):
    """请求中携带了非法的来源 key、无法解析的文本，或非法的条目状态。"""


def _source_label(source_key: str) -> str:
    for item in SOURCE_CATALOG:
        if item.key == source_key:
            return item.label

    return source_key


def _require_known_source(source_key: str) -> None:
    if source_key not in SOURCE_KEYS:
        raise LiteratureError(f"unknown source key: {source_key}")


def _detect_duplicate(
    session: Session,
    project_id: int,
    candidate: LiteratureRecord,
) -> int | None:
    """Task 3 会实现三级去重判定，本任务先不判重。"""
    return None


def _to_record_summary(record: LiteratureRecord) -> LiteratureRecordSummary:
    return LiteratureRecordSummary(
        id=record.id or 0,
        title=record.title,
        authors=record.authors,
        journal=record.journal,
        year=record.year,
        doi=record.doi,
        pmid=record.pmid,
        source_key=record.source_key,
        source_label=_source_label(record.source_key),
        dedupe_status=record.dedupe_status,
        duplicate_of_id=record.duplicate_of_id,
    )


def _build_stats(records: list[LiteratureRecord]) -> LiteratureStats:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.source_key] = counts.get(record.source_key, 0) + 1

    return LiteratureStats(
        total_count=len(records),
        unique_count=sum(
            1 for record in records if record.dedupe_status in UNIQUE_STATUSES
        ),
        duplicate_count=sum(
            1 for record in records if record.dedupe_status == "duplicate"
        ),
        by_source=[
            LiteratureSourceCount(
                source_key=item.key,
                source_label=item.label,
                count=counts[item.key],
            )
            for item in SOURCE_CATALOG
            if item.key in counts
        ],
    )


def build_library_response(
    session: Session,
    project: ResearchProject,
    last_import_result: ImportResultSummary | None = None,
) -> LiteratureLibraryResponse:
    project_id = project.id or 0
    records = list(
        session.exec(
            select(LiteratureRecord)
            .where(LiteratureRecord.project_id == project_id)
            .order_by(LiteratureRecord.id)
        )
    )
    batches = list(
        session.exec(
            select(LiteratureImportBatch)
            .where(LiteratureImportBatch.project_id == project_id)
            .order_by(LiteratureImportBatch.id)
        )
    )

    return LiteratureLibraryResponse(
        project=WorkspaceProjectSummary(
            id=project_id,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="检索",
            updated_at_label="刚刚更新",
        ),
        stage_key="search",
        records=[_to_record_summary(record) for record in records],
        stats=_build_stats(records),
        recent_batches=[
            LiteratureBatchSummary(
                id=batch.id or 0,
                source_key=batch.source_key,
                source_label=_source_label(batch.source_key),
                parsed_count=batch.parsed_count,
                duplicate_count=batch.duplicate_count,
                skipped_count=batch.skipped_count,
                created_at_label=batch.created_at_label,
            )
            for batch in batches
        ],
        available_sources=[
            SourceCatalogItemResponse(
                key=item.key,
                label=item.label,
                description=item.description,
                supports_full_text=item.supports_full_text,
            )
            for item in SOURCE_CATALOG
        ],
        last_import_result=last_import_result,
    )


def import_literature(
    session: Session,
    project: ResearchProject,
    payload: ImportLiteratureRequest,
) -> LiteratureLibraryResponse:
    _require_known_source(payload.source_key)

    parsed = parse_literature_text(payload.raw_text)
    if not parsed.entries:
        raise LiteratureError("无法从粘贴内容中解析出任何条目")

    project_id = project.id or 0
    batch = LiteratureImportBatch(
        project_id=project_id,
        source_key=payload.source_key,
        parsed_count=len(parsed.entries),
        skipped_count=parsed.skipped_count,
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)

    duplicate_count = 0
    for entry in parsed.entries:
        record = LiteratureRecord(
            project_id=project_id,
            title=entry.title,
            authors=entry.authors,
            journal=entry.journal,
            year=entry.year,
            doi=entry.doi,
            pmid=entry.pmid,
            abstract=entry.abstract,
            source_key=payload.source_key,
            import_batch_id=batch.id,
        )
        original_id = _detect_duplicate(session, project_id, record)
        if original_id is not None:
            record.dedupe_status = "duplicate"
            record.duplicate_of_id = original_id
            duplicate_count += 1

        session.add(record)
        session.commit()

    batch.duplicate_count = duplicate_count
    session.add(batch)
    session.commit()

    return build_library_response(
        session,
        project,
        ImportResultSummary(
            imported_count=len(parsed.entries),
            duplicate_count=duplicate_count,
            skipped_count=parsed.skipped_count,
        ),
    )


def create_literature_record(
    session: Session,
    project: ResearchProject,
    payload: CreateLiteratureRecordRequest,
) -> LiteratureLibraryResponse:
    _require_known_source(payload.source_key)

    title = payload.title.strip()
    if title == "":
        raise LiteratureError("title 不能为空")

    project_id = project.id or 0
    record = LiteratureRecord(
        project_id=project_id,
        title=title,
        authors=payload.authors,
        journal=payload.journal,
        year=payload.year,
        doi=payload.doi,
        pmid=payload.pmid,
        abstract=payload.abstract,
        source_key=payload.source_key,
    )
    original_id = _detect_duplicate(session, project_id, record)
    if original_id is not None:
        record.dedupe_status = "duplicate"
        record.duplicate_of_id = original_id

    session.add(record)
    session.commit()

    return build_library_response(session, project)
