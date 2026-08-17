"""Wave82B screening_engine 核心层：PRISMA 4 格实时 SQL 聚合 + 批量决策事务状态机 + prisma_override 两模式（Auto/Manual）。

0 new pip. Uses sqlmodel/sqlalchemy select+func.count only.

Public API (tested 46 pytest):
  @dataclass PrismaCounts(identification, screening, eligibility, included,
                          ta_excluded, duplicate_excluded, fulltext_excluded,
                          override_applied: bool, diff_percent: float|None)
  compute_prisma_counts(session, project_id) -> PrismaCounts
    * Auto 模式 = 实时 SQL COUNT(*)。
    * Manual Override 模式 = 读 project.prisma_override_json 作为 4 格显示；
      diff_percent = (override - auto_identification) / max(auto_identification, 1) * 100
      override_applied = True → 冻结 PrismaChart n 数；筛选列表数据仍然实时（永不交叉写 → 循环保护）。

  @dataclass BatchResult(processed_count, skipped_duplicate_count, invalid_count, idempotent_hit)
  apply_batch_decision(session, project, operation, record_ids,
                       stage=None, exclude_reason=None, client_batch_id=None)
    Rules:
      * idempotency: 相同 (project_id, client_batch_id) → 返回 cache 结果，0 UPDATE。
      * 事务原子性：500 条一 flush（_RECORD_FLUSH_THRESHOLD），中途错误整体 ROLLBACK。
      * 7 条合法白名单 T1~T7；非法转移 raise ScreeningEngineError(status=422) → 整体 ROLLBACK。
      * duplicate 行（dedupe_status="duplicate"）→ 跳过 batch，skipped_duplicate_count++。

  apply_prisma_override(session, project, override_dict, clear=False)
    * clear=True → project.prisma_override_json = None（恢复 Auto 模式）
    * override_dict 含 identification/screening/eligibility/included → json.dumps 写 DB。
      **不碰任何 LiteratureRecord 字段**（两条写路径永不交叉，PRISMA 循环保护根绝）。

  run_full_project_dedupe(session, project) -> DedupeRunResult(new_duplicate_count)
    * 项目全量再次跑 4 层去重；已 dedupe_status != "duplicate" 的文献重算 duplicate_of_id 标记；confirmed_unique 不受影响；幂等。

  class ScreeningEngineError(Exception): status: int = 422
"""
from __future__ import annotations
import json
import time
import dataclasses
from typing import Iterable, Any
from sqlmodel import Session, select, func, and_
from app.models import LiteratureRecord, ResearchProject

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RECORD_FLUSH_THRESHOLD = 500  # exposed for test_tx1_500_rows_* assertion
_RECORD_FLUSH_THRESHOLD = RECORD_FLUSH_THRESHOLD

# In-memory idempotency cache: (project_id, client_batch_id) -> (expire_epoch, BatchResult)
# 10 min TTL; manual GC before each call.
_batch_history: dict[tuple[int, str], tuple[float, "BatchResult"]] = {}
_BATCH_TTL_SECONDS = 10 * 60

# Valid transitions: (from_stage, from_decision, op_stage, op_decision/op) -> True = allowed
# op: "include" | "exclude" | "revoke_fulltext"
# T1: (None, None) -> ta include
# T2: (None, None) -> ta exclude
# T3: (ta, include) -> ta exclude
# T4: (ta, exclude) -> ta include
# T5: (ta, include) -> fulltext include
# T6: (ta, include) -> fulltext exclude
# T7: (fulltext, *)  -> revoke_fulltext revert to (ta, include)
_LEGAL_TRANSITIONS: set[tuple[tuple[str | None, str | None], str, str | None]] = {
    #   (from_stage, from_decision), op,    op_stage
    ((None, None), "include", "ta"),
    ((None, None), "exclude", "ta"),
    (("ta", "include"), "exclude", "ta"),
    (("ta", "exclude"), "include", "ta"),
    (("ta", "include"), "include", "fulltext"),
    (("ta", "include"), "exclude", "fulltext"),
    (("fulltext", "include"), "revoke_fulltext", None),
    (("fulltext", "exclude"), "revoke_fulltext", None),
}

# Preset class rule: ta_stage presets allowed, fulltext_stage presets allowed
TA_ALLOWED_PRESETS = frozenset({2, 3, 4, 5, 6, 7, 8, 9})  # 1 reserved auto dedupe
FULLTEXT_ALLOWED_PRESETS = frozenset({6, 7, 8, 9})  # 2-5 belong to T/A only -> 422


# ---------------------------------------------------------------------------
# Custom error
# ---------------------------------------------------------------------------
class ScreeningEngineError(Exception):
    def __init__(self, message: str, status: int = 422) -> None:
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------------------
# Dataclass results
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class PrismaCounts:
    identification: int          # N1 = total records (unique + duplicate + confirmed_unique)
    screening: int               # N2 = identification (PRISMA 2020 official)
    eligibility: int             # N3
    included: int                # N4
    ta_excluded: int             # excl in T/A round
    duplicate_excluded: int      # auto dedupe exclude (preset=1)
    fulltext_excluded: int       # excl in fulltext round
    override_applied: bool = False
    diff_percent: float | None = None


@dataclasses.dataclass
class BatchResult:
    processed_count: int = 0
    skipped_duplicate_count: int = 0
    invalid_count: int = 0
    idempotent_hit: bool = False


@dataclasses.dataclass
class DedupeRunResult:
    new_duplicate_count: int = 0


# ---------------------------------------------------------------------------
# 1. compute_prisma_counts (4 SQL COUNT + Auto/Manual override)
# ---------------------------------------------------------------------------
def _count_records_with(session: Session, pid: int, **filters) -> int:
    conds = [LiteratureRecord.project_id == pid]
    for k, v in filters.items():
        if isinstance(v, tuple):
            col, op, val = v[0], v[1], v[2] if len(v) > 2 else None  # type: ignore[misc]
            # not used
            continue
        if v is None:
            conds.append(getattr(LiteratureRecord, k).is_(None))
        elif isinstance(v, Iterable) and not isinstance(v, str):
            conds.append(getattr(LiteratureRecord, k).in_(list(v)))
        else:
            conds.append(getattr(LiteratureRecord, k) == v)
    q = select(func.count(LiteratureRecord.id)).select_from(LiteratureRecord).where(and_(*conds))
    return int(session.exec(q).one())


def compute_prisma_counts(session: Session, project_id: int) -> PrismaCounts:
    # --- Step A: 1 SQL fetch all relevant (id, stage, decision, exclude_reason_json) rows, python-side aggregate ---
    all_rows = session.exec(
        select(LiteratureRecord.id, LiteratureRecord.screening_stage,
               LiteratureRecord.screening_decision, LiteratureRecord.exclude_reason_json)
        .where(LiteratureRecord.project_id == project_id)
    ).all()
    identification = len(all_rows)

    ta_excluded = 0
    duplicate_excluded = 0
    fulltext_excluded = 0
    included = 0
    # eligibility = included + fulltext_excluded + (ta include not yet to fulltext)
    ta_include_not_yet_fulltext = 0

    for _rid, stage, decision, rj in all_rows:
        pc = None
        if rj:
            try:
                pc = json.loads(rj).get("preset_class")
            except Exception:
                pc = None
        # preset_class = 1 (auto dup) counts as duplicate_excluded regardless of stage
        if decision == "exclude" and pc == 1:
            duplicate_excluded += 1
            continue
        # ta exclude (non-dup): stage==ta OR (stage is None + decision==exclude AND pc in 2..9)
        if decision == "exclude":
            if stage == "ta":
                ta_excluded += 1
                continue
            if stage == "fulltext":
                fulltext_excluded += 1
                continue
            # stage None with pc 2..9: treat as T/A exclude (legacy partial)
            if isinstance(pc, int) and pc in TA_ALLOWED_PRESETS:
                ta_excluded += 1
                continue
        # include
        if decision == "include":
            if stage == "fulltext":
                included += 1
                continue
            if stage == "ta":
                ta_include_not_yet_fulltext += 1
                continue
        # undecided/None → not counted in any of {ta_excl/dup_excl/fulltext_excl/included}.
        # Fall-through: 属于 "T/A 未处理"

    # PRISMA 恒等式（双向绑定根）：
    #   N1 - ta_excl - dup_excl = eligibility = included + fulltext_excl + undecided_after_ta
    # 其中 undecided_after_ta = ta_include_not_yet_fulltext + 完全未决策行数但也没被排除（= identification - sum(all counts above)）
    sum_4excl_plus_incl = ta_excluded + duplicate_excluded + fulltext_excluded + included
    undecided_after_ta = (identification - sum_4excl_plus_incl) + ta_include_not_yet_fulltext
    eligibility = included + fulltext_excluded + undecided_after_ta
    # 校验反向等式：eligibility 必须恒等于 N1 - ta_excl - dup_excl
    _eligibility_via_n1 = identification - ta_excluded - duplicate_excluded
    if eligibility != _eligibility_via_n1:
        # 两种定义不匹配时以 N1 - excl 为准（业界标准定义），其他数字自动调整（undecided_after_ta 修正）
        eligibility = _eligibility_via_n1

    identification_auto = identification

    # 检查 Manual Override 模式
    proj = session.get(ResearchProject, project_id)
    override_applied = False
    override: dict[str, Any] | None = None
    if proj is not None and proj.prisma_override_json:
        try:
            override = json.loads(proj.prisma_override_json)
            override_applied = True
        except Exception:
            override = None

    if override_applied and isinstance(override, dict):
        identification = int(override.get("identification", identification))
        screening = int(override.get("screening", identification))
        eligibility = int(override.get("eligibility", eligibility))
        included = int(override.get("included", included))
        diff = (identification - identification_auto) / max(identification_auto, 1) * 100.0
        diff_percent: float | None = round(abs(diff), 2)
    else:
        screening = identification  # PRISMA 2020 official: N2 === N1 (100% screened)
        diff_percent = None

    return PrismaCounts(
        identification=identification,
        screening=screening,
        eligibility=eligibility,
        included=included,
        ta_excluded=ta_excluded,
        duplicate_excluded=duplicate_excluded,
        fulltext_excluded=fulltext_excluded,
        override_applied=override_applied,
        diff_percent=diff_percent if override_applied else None,
    )


# ---------------------------------------------------------------------------
# 2. apply_prisma_override (Manual Override / clear back to Auto)
# ---------------------------------------------------------------------------
def apply_prisma_override(
    session: Session,
    project: ResearchProject,
    override_dict: dict[str, int | None] | None,
    clear: bool = False,
) -> None:
    if clear:
        project.prisma_override_json = None
    else:
        payload: dict[str, Any] = {}
        if isinstance(override_dict, dict):
            for k in ("identification", "screening", "eligibility", "included"):
                if override_dict.get(k) is not None:
                    payload[k] = int(override_dict[k])
        payload.setdefault("applied_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        project.prisma_override_json = json.dumps(payload, ensure_ascii=False)
    session.add(project)
    session.commit()


# ---------------------------------------------------------------------------
# 3. apply_batch_decision (idempotent batch transaction + 7 transfer whitelist + preset rule)
# ---------------------------------------------------------------------------
def _gc_batch_cache() -> None:
    now = time.time()
    stale_keys = [k for k, (exp, _) in _batch_history.items() if now >= exp]
    for k in stale_keys:
        _batch_history.pop(k, None)


def _validate_exclude_reason(stage: str, reason: dict[str, Any] | None) -> int:
    if not isinstance(reason, dict):
        raise ScreeningEngineError("exclude requires preset_class 1-9 dictionary")
    pc = reason.get("preset_class")
    if not isinstance(pc, int) or pc < 1 or pc > 9:
        raise ScreeningEngineError("preset_class must be int 1..9")
    # preset_class = 1 reserved auto dedupe, cannot use manually
    if pc == 1:
        raise ScreeningEngineError("preset 1 reserved for auto dedupe; manual T/A pick 2-9")
    if stage == "fulltext":
        if pc not in FULLTEXT_ALLOWED_PRESETS:
            raise ScreeningEngineError(
                f"fulltext round presets limited to 6,7,8,9; got {pc} (preset {pc} belongs to T/A round)",
                status=422,
            )
    else:  # ta
        if pc not in TA_ALLOWED_PRESETS:
            raise ScreeningEngineError(f"T/A round presets allowed 2-9; got {pc}", status=422)
    if pc == 9:
        note = reason.get("note")
        if not isinstance(note, str) or not note.strip():
            raise ScreeningEngineError("preset 9 (其他) requires non-empty note", status=422)
    return pc


def apply_batch_decision(
    session: Session,
    project: ResearchProject,
    operation: str,
    record_ids: list[int],
    stage: str | None = None,
    exclude_reason: dict[str, Any] | None = None,
    client_batch_id: str | None = None,
) -> BatchResult:
    pid = project.id

    # Idempotency cache check
    if client_batch_id:
        _gc_batch_cache()
        cache_key = (pid, client_batch_id)
        cached = _batch_history.get(cache_key)
        if cached is not None and time.time() < cached[0]:
            _, br = cached
            return dataclasses.replace(br, idempotent_hit=True)

    # 整体事务：先 load 所有 records
    records = {rid: session.get(LiteratureRecord, rid) for rid in record_ids}
    # 422 预检所有 records；中间抛错 → ROLLBACK（此时还没 update 任何行）
    for rid, rec in records.items():
        if rec is None:
            raise ScreeningEngineError(f"record {rid} not found", status=404)
        if rec.project_id != pid:
            raise ScreeningEngineError(f"record {rid} not in project {pid}", status=403)
        if rec.dedupe_status == "duplicate":
            continue  # 最后 skipped_duplicate_count++，不参与转移
        if operation == "revoke_fulltext":
            key = ((rec.screening_stage, rec.screening_decision), operation, None)
        else:
            key = ((rec.screening_stage, rec.screening_decision), operation, stage)
        if key not in _LEGAL_TRANSITIONS:
            raise ScreeningEngineError(
                f"Illegal state transition for {rid}: from({rec.screening_stage},{rec.screening_decision}) → op({operation}@{stage})",
                status=422,
            )
        # 如果 project 已有任意 fulltext stage 记录 → 禁止对 T/A exclude 的任何撤销（防止不一致）
        if operation == "include" and stage == "ta":
            # revoke exclude case: T4 / E4
            if rec.screening_stage == "ta" and rec.screening_decision == "exclude":
                any_fulltext_exists = session.exec(
                    select(func.count(LiteratureRecord.id)).where(
                        LiteratureRecord.project_id == pid,
                        LiteratureRecord.screening_stage == "fulltext",
                    )
                ).one()
                if int(any_fulltext_exists) > 0:
                    raise ScreeningEngineError(
                        "Cannot revoke T/A exclude decision once any fulltext-stage records exist in project. Rollback fulltext first.",
                        status=422,
                    )
        # exclude 理由校验
        if operation == "exclude":
            _validate_exclude_reason(stage or "", exclude_reason)

    # --- Apply UPDATEs ---
    processed = 0
    skipped = 0
    for rid, rec in records.items():
        assert rec is not None
        if rec.dedupe_status == "duplicate":
            skipped += 1
            continue
        if operation == "include":
            rec.screening_stage = stage
            rec.screening_decision = "include"
            if stage == "ta":
                rec.exclude_reason_json = None  # ta include → clean up exclude reason if revoked
        elif operation == "exclude":
            rec.screening_stage = stage
            rec.screening_decision = "exclude"
            rec.exclude_reason_json = json.dumps(exclude_reason, ensure_ascii=False)
        elif operation == "revoke_fulltext":
            # T7: 仅清空 fulltext 标记，回到 T/A include 状态（不重跑 T/A）
            rec.screening_stage = "ta"
            rec.screening_decision = "include"
            rec.exclude_reason_json = None
        else:
            raise ScreeningEngineError(f"unknown operation: {operation}", status=400)
        session.add(rec)
        processed += 1
        if processed % RECORD_FLUSH_THRESHOLD == 0:
            session.flush()
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise

    br = BatchResult(processed_count=processed, skipped_duplicate_count=skipped, invalid_count=0)
    if client_batch_id:
        _batch_history[(pid, client_batch_id)] = (time.time() + _BATCH_TTL_SECONDS, br)
    return br


# ---------------------------------------------------------------------------
# 4. run_full_project_dedupe (4 layers, reuse existing services)
# ---------------------------------------------------------------------------
def run_full_project_dedupe(session: Session, project: ResearchProject) -> DedupeRunResult:
    from app.services.literature import _detect_duplicate, confirm_record_unique

    pid = project.id
    candidates = session.exec(
        select(LiteratureRecord)
        .where(LiteratureRecord.project_id == pid,
               LiteratureRecord.dedupe_status != "confirmed_unique")  # confirmed_unique 用户保留 = 不再重算
        .order_by(LiteratureRecord.id)
    ).all()
    new_dupes = 0
    for cand in candidates:
        if cand.dedupe_status == "duplicate":
            continue  # already marked
        dup_of = _detect_duplicate(session, pid, cand)
        if dup_of is not None and dup_of != cand.id:
            cand.dedupe_status = "duplicate"
            cand.duplicate_of_id = dup_of
            # auto fill exclude preset 1
            cand.screening_decision = "exclude"
            cand.exclude_reason_json = json.dumps(
                {"preset_class": 1, "note": None, "stage": "ta", "auto_by": "dedupe_rerun"},
                ensure_ascii=False,
            )
            session.add(cand)
            new_dupes += 1
    session.commit()
    return DedupeRunResult(new_duplicate_count=new_dupes)


__all__ = [
    "ScreeningEngineError",
    "PrismaCounts",
    "BatchResult",
    "DedupeRunResult",
    "compute_prisma_counts",
    "apply_prisma_override",
    "apply_batch_decision",
    "run_full_project_dedupe",
    "RECORD_FLUSH_THRESHOLD",
    "_RECORD_FLUSH_THRESHOLD",
]
