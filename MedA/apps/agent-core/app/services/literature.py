from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import LiteratureImportBatch, LiteratureRecord, ResearchProject


_SOURCE_LABELS = {"pubmed": "PubMed", "cnki": "CNKI", "wanfang": "万方"}


@dataclass
class _ImportResult:
    count: int
    skipped_count: int
    duplicate_count: int


def import_unified_entries(
    session,
    project_id,
    source_key,
    entries,
    search_run_id=None,
    search_run_source_id=None,
) -> _ImportResult:
    _project = session.get(ResearchProject, project_id)
    if _project is None:
        raise HTTPException(status_code=404, detail="project not found")

    source_label = _SOURCE_LABELS.get(source_key, source_key)

    batch = LiteratureImportBatch(
        project_id=project_id,
        source_key=source_key,
        parsed_count=len(entries),
        duplicate_count=0,
        skipped_count=0,
        search_run_source_id=search_run_source_id,
    )
    session.add(batch)
    session.flush()

    imported = 0
    failed = 0
    duplicates = 0

    for e in entries:
        try:
            doi, pmid, title = _normalize_identifiers(e.doi or "", e.pmid or "", e.title or "")
            if title == "":
                failed += 1
                continue
            candidate = LiteratureRecord(
                project_id=project_id,
                doi=doi,
                pmid=pmid,
                title=title,
                authors=e.authors or "",
                journal=e.journal or "",
                year=e.year,
                abstract=e.abstract or "",
                source_key=source_key,
            )
            dup_id = _detect_duplicate(session, project_id, candidate)
            status = "unique" if dup_id is None else "duplicate"
            if dup_id is not None:
                duplicates += 1
            # Wave82B auto screening exclude (preset_class=1 重复文献, ta stage, auto_by=dedupe_layer4)
            # WAVE82B_INSERT_DEDUPE_AUTO_EXCLUDE 开始
            auto_screening_decision = None
            auto_exclude_reason_json = None
            if status == "duplicate":
                auto_screening_decision = "exclude"
                auto_exclude_reason_json = __import__("json").dumps(
                    {"preset_class": 1, "note": None, "stage": "ta", "auto_by": "dedupe_layer4"},
                    ensure_ascii=False,
                )
            # WAVE82B_INSERT_DEDUPE_AUTO_EXCLUDE 结束
            rec = LiteratureRecord(
                project_id=project_id,
                doi=doi,
                pmid=pmid,
                title=title,
                authors=e.authors or "",
                journal=e.journal or "",
                year=e.year,
                abstract=e.abstract or "",
                source_key=source_key,
                source_label=source_label,
                dedupe_status=status,
                duplicate_of_id=dup_id,
                import_batch_id=batch.id,
                search_run_id=search_run_id,
                pico_status="not_extracted",
                # Wave82B 追加：dedupe 命中时自动填 screening 字段（值=上面 auto_* 变量，unique 时=None 写空）
                screening_decision=auto_screening_decision,
                exclude_reason_json=auto_exclude_reason_json,
            )
            session.add(rec)
            session.flush()
            imported += 1
        except Exception:
            failed += 1
            session.rollback()

    session.commit()
    session.refresh(batch)
    batch.duplicate_count = duplicates
    batch.skipped_count = failed
    session.add(batch)
    session.commit()
    return _ImportResult(count=imported, skipped_count=failed, duplicate_count=duplicates)
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
from app.services.literature_parser import normalize_title, parse_literature_text
from app.services.source_catalog import SOURCE_CATALOG, SOURCE_KEYS

UNIQUE_STATUSES = {"unique", "confirmed_unique"}


class LiteratureError(Exception):
    """请求中携带了非法的来源 key、无法解析的文本，或非法的条目状态。"""


class LiteratureNotFoundError(Exception):
    """指定的文献条目不存在，或不属于当前项目。"""


def _source_label(source_key: str) -> str:
    for item in SOURCE_CATALOG:
        if item.key == source_key:
            return item.label

    return source_key


def _require_known_source(source_key: str) -> None:
    if source_key not in SOURCE_KEYS:
        raise LiteratureError(f"unknown source key: {source_key}")


def _format_created_at_label(created_at: datetime) -> str:
    delta = datetime.utcnow() - created_at
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "刚刚导入"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分钟前导入"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小时前导入"
    days = hours // 24
    if days < 30:
        return f"{days} 天前导入"
    return created_at.strftime("%Y-%m-%d 导入")


def _detect_duplicate(
    session: Session,
    project_id: int,
    candidate: LiteratureRecord,
) -> int | None:
    """三级判定，命中即停。只在同项目内比较，且不以 duplicate 记录作为原件。
    DOI/PMID 用数据库 LIMIT 1 查询，标题级仅加载必要字段。"""
    base_query = (
        select(LiteratureRecord)
        .where(
            LiteratureRecord.project_id == project_id,
            LiteratureRecord.dedupe_status != "duplicate",
        )
        .order_by(LiteratureRecord.id)
    )

    if candidate.doi != "":
        match = session.exec(
            base_query.where(LiteratureRecord.doi == candidate.doi).limit(1)
        ).first()
        if match is not None:
            return match.id

    if candidate.pmid != "":
        match = session.exec(
            base_query.where(LiteratureRecord.pmid == candidate.pmid).limit(1)
        ).first()
        if match is not None:
            return match.id

    candidate_title = normalize_title(candidate.title)
    existing = session.exec(
        select(LiteratureRecord.id, LiteratureRecord.title, LiteratureRecord.year)
        .where(
            LiteratureRecord.project_id == project_id,
            LiteratureRecord.dedupe_status != "duplicate",
        )
        .order_by(LiteratureRecord.id)
    ).all()
    for row in existing:
        record_id, record_title, record_year = row
        if (
            normalize_title(record_title) == candidate_title
            and record_year == candidate.year
        ):
            return record_id

    # WAVE82B_INSERT_SIMHASH_LEVEL4 开始（四级判定：同年份分桶 + 中文 Jaccard ≥ 0.92 OR SimHash Hamming ≤ 5）
    #  前 3 级 exact 都没命中，才走末层 fuzzy（英文走 SimHash，中文短标题走字符 Jaccard，两者任一命中即停）
    from app.services.simhash import (
        simhash64, hamming_distance, SIMHASH_HAMMING_THRESHOLD,
        cjk_char_jaccard, CJK_JACCARD_THRESHOLD,
    )
    candidate_fp = simhash64(candidate.title or "")
    if candidate.year is not None:
        # 同年份分桶：dedup_status 不是 duplicate（以 confirmed_unique / unique 作为原件）
        same_year_rows = session.exec(
            select(LiteratureRecord.id, LiteratureRecord.title, LiteratureRecord.year)
            .where(
                LiteratureRecord.project_id == project_id,
                LiteratureRecord.dedupe_status != "duplicate",
                LiteratureRecord.year == candidate.year,
            )
            .order_by(LiteratureRecord.id)
        ).all()
        for row in same_year_rows:
            record_id, record_title, _ = row
            # 中文短标题：Jaccard ≥ 0.92 优先判定（SimHash 对 ≤20 字中文不敏感）
            j = cjk_char_jaccard(candidate.title or "", record_title or "")
            if j >= CJK_JACCARD_THRESHOLD:
                return record_id
            # 英文 / 长中文：SimHash Hamming ≤ 阈值（短标题候选 simhash=0 直接跳过）
            if candidate_fp != 0:
                rec_fp = simhash64(record_title or "")
                if rec_fp != 0 and hamming_distance(candidate_fp, rec_fp) <= SIMHASH_HAMMING_THRESHOLD:
                    return record_id
    # WAVE82B_INSERT_SIMHASH_LEVEL4 结束

    return None


def _normalize_identifiers(
    doi: str, pmid: str, title: str
) -> tuple[str, str, str]:
    """统一规范化标识符和标题：DOI 全小写+去空格、PMID 去空格、title strip。"""
    return (
        doi.strip().lower(),
        pmid.strip(),
        title.strip(),
    )


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
    *,
    search_run_id: int | None = None,
    sort: Literal["default", "relevance", "year_desc", "journal"] = "default",
    min_score: float | None = None,
) -> LiteratureLibraryResponse:
    project_id = project.id or 0
    q = select(LiteratureRecord).where(LiteratureRecord.project_id == project_id)
    if search_run_id is not None:
        q = q.where(LiteratureRecord.search_run_id == search_run_id)
    all_records = list(session.exec(q).all())
    if min_score is not None:
        all_records = [
            r for r in all_records
            if r.relevance_score is not None and r.relevance_score >= min_score
        ]

    if sort == "relevance":
        all_records.sort(key=lambda r: (-(r.relevance_score or -1.0), -(r.year or 0), -(r.id or 0)))
    elif sort == "year_desc":
        all_records.sort(key=lambda r: (-(r.year or 0), -(r.relevance_score or 0), -(r.id or 0)))
    elif sort == "journal":
        all_records.sort(key=lambda r: ((r.journal or "").lower(), -(r.year or 0), -(r.id or 0)))
    else:
        all_records.sort(key=lambda r: -(r.id or 0))

    records = all_records
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
                created_at_label=_format_created_at_label(batch.created_at),
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
    session.flush()

    duplicate_count = 0
    failed_count = 0
    for entry in parsed.entries:
        norm_doi, norm_pmid, norm_title = _normalize_identifiers(
            entry.doi, entry.pmid, entry.title
        )
        if norm_title == "":
            failed_count += 1
            continue

        record = LiteratureRecord(
            project_id=project_id,
            title=norm_title,
            authors=entry.authors,
            journal=entry.journal,
            year=entry.year,
            doi=norm_doi,
            pmid=norm_pmid,
            abstract=entry.abstract,
            source_key=payload.source_key,
            import_batch_id=batch.id,
        )
        try:
            original_id = _detect_duplicate(session, project_id, record)
            if original_id is not None:
                record.dedupe_status = "duplicate"
                record.duplicate_of_id = original_id
                duplicate_count += 1

            session.add(record)
            session.commit()
        except Exception:
            session.rollback()
            failed_count += 1
            continue

    batch.duplicate_count = duplicate_count
    batch.skipped_count = parsed.skipped_count + failed_count
    session.add(batch)
    session.commit()

    return build_library_response(
        session,
        project,
        ImportResultSummary(
            imported_count=len(parsed.entries) - failed_count,
            duplicate_count=duplicate_count,
            skipped_count=parsed.skipped_count + failed_count,
        ),
    )


def create_literature_record(
    session: Session,
    project: ResearchProject,
    payload: CreateLiteratureRecordRequest,
) -> LiteratureLibraryResponse:
    _require_known_source(payload.source_key)

    norm_doi, norm_pmid, norm_title = _normalize_identifiers(
        payload.doi, payload.pmid, payload.title
    )
    if norm_title == "":
        raise LiteratureError("title 不能为空")

    project_id = project.id or 0
    record = LiteratureRecord(
        project_id=project_id,
        title=norm_title,
        authors=payload.authors,
        journal=payload.journal,
        year=payload.year,
        doi=norm_doi,
        pmid=norm_pmid,
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


def confirm_record_unique(
    session: Session,
    project: ResearchProject,
    record_id: int,
) -> LiteratureLibraryResponse:
    record = session.get(LiteratureRecord, record_id)
    if record is None or record.project_id != (project.id or 0):
        raise LiteratureNotFoundError("record not found")

    if record.dedupe_status != "duplicate":
        raise LiteratureError(
            f"record {record_id} is not marked as duplicate"
        )

    record.dedupe_status = "confirmed_unique"
    record.duplicate_of_id = None
    # WAVE82B_INSERT_CONFIRM_UNIQUE_CLEAR_SCREENING 开始
    # 用户点击「不是重复 → 保留为独立」时，必须清空之前系统自动填的 screening=exclude（否则会一直卡在「重复文献排除」）
    record.screening_decision = None
    record.exclude_reason_json = None
    record.screening_stage = None
    # WAVE82B_INSERT_CONFIRM_UNIQUE_CLEAR_SCREENING 结束
    session.add(record)
    session.commit()

    return build_library_response(session, project)
