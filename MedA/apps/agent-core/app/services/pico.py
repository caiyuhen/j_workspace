from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from sqlmodel import Session, select

from app.models import LiteraturePico, LiteratureRecord, SearchRun


_LLM_PROVIDER: Literal["claude", "openai"] | None = (
    os.environ.get("MEDA_PICO_LLM_PROVIDER") or None
)


POP_TERMS = [
    "T2DM", "2型糖尿病", "2 型糖尿病", "T1DM", "CKD", "慢性肾病", "CKD 3b", "HFrEF", "心衰",
    "高血压", "STEMI", "NSTEMI", "ACS", "急性冠脉综合征", "肥胖", "NAFLD",
]
INT_TERMS = [
    "SGLT2", "SGLT2i", "达格列净", "Dapagliflozin", "恩格列净", "Empagliflozin",
    "GLP-1", "GLP1", "司美格鲁肽", "Semaglutide", "利拉鲁肽", "Liraglutide",
    "二甲双胍", "Metformin", "胰岛素", "Insulin", "ACEI", "ARB", "他汀", "Statin",
]
CMP_TERMS = [
    "安慰剂", "placebo", "常规治疗", "usual care", "对照", "control",
    "生活方式", "lifestyle", "磺脲类", "sulfonylurea",
]
OUT_TERMS = [
    "MACE", "主要心血管不良事件", "3P-MACE", "4P-MACE", "HF 住院", "心衰住院", "住院率",
    "全因死亡", "all-cause mortality", "心血管死亡", "CV death", "eGFR 下降", "肌酐翻倍",
    "复合肾脏终点", "HbA1c", "体重变化",
]
STUDY_TYPE_RULES = [
    ("rct", re.compile(r"\bRCT\b|randomiz|随机|随机对照|randomized controlled", re.IGNORECASE)),
    ("observational", re.compile(r"cohort|队列|retrospective|回顾性|observational", re.IGNORECASE)),
    ("review", re.compile(r"meta.?analysis|systematic review|Meta分析|系统综述", re.IGNORECASE)),
]


class PicoExtractionError(Exception):
    def __init__(
        self,
        message: str,
        code: Literal[
            "no_records_provided", "llm_not_configured", "llm_not_implemented", "pico_failed"
        ],
    ):
        super().__init__(message)
        self.code = code


@dataclass
class BatchResult:
    processed: int
    already_had: int
    failed: int


def _extract_population(text: str) -> tuple[str | None, float]:
    found = [t for t in POP_TERMS if t.lower() in text.lower()]
    if not found:
        return None, 0.0
    return "；".join(sorted(set(found))), min(1.0, 0.25 + 0.15 * len(found))


def _extract_intervention(text: str) -> tuple[str | None, float]:
    found = [t for t in INT_TERMS if t.lower() in text.lower()]
    if not found:
        return None, 0.0
    return "；".join(sorted(set(found))), min(1.0, 0.25 + 0.15 * len(found))


def _extract_comparison(text: str) -> tuple[str | None, float]:
    found = [t for t in CMP_TERMS if t.lower() in text.lower()]
    if not found:
        return None, 0.0
    return "；".join(sorted(set(found))), min(1.0, 0.25 + 0.15 * len(found))


def _extract_outcome(text: str) -> tuple[str | None, float]:
    found = [t for t in OUT_TERMS if t.lower() in text.lower()]
    if not found:
        return None, 0.0
    return "；".join(sorted(set(found))), min(1.0, 0.25 + 0.15 * len(found))


def _detect_study_type(text: str) -> tuple[str | None, float]:
    for label, rx in STUDY_TYPE_RULES:
        if rx.search(text):
            return label, 0.9
    return None, 0.0


def _rule_baseline_extract(rec: LiteratureRecord) -> LiteraturePico:
    text = f"{rec.title}\n{rec.abstract}"
    pop, p_w = _extract_population(text)
    intr, i_w = _extract_intervention(text)
    cmp, c_w = _extract_comparison(text)
    out, o_w = _extract_outcome(text)
    study, s_w = _detect_study_type(text)
    conf = round(sum([p_w, i_w, c_w, o_w, s_w]) / 5.0, 3)
    return LiteraturePico(
        record_id=rec.id,
        population=pop,
        intervention=intr,
        comparison=cmp,
        outcome=out,
        study_type=study,
        extraction_method="rule_baseline",
        confidence=conf,
    )


async def _llm_extract(rec: LiteratureRecord, provider: str) -> LiteraturePico:
    raise PicoExtractionError(
        f"LLM provider {provider!r} is not wired yet; no LLM SDK is installed.",
        "llm_not_implemented",
    )


def extract_pico_for_record(
    session: Session,
    record_id: int,
    *,
    method: Literal["rule_baseline", "llm"] = "rule_baseline",
) -> LiteraturePico:
    rec = session.get(LiteratureRecord, record_id)
    if rec is None:
        raise PicoExtractionError("record not found", "pico_failed")

    if method == "llm":
        if _LLM_PROVIDER is None:
            raise PicoExtractionError(
                "PICO LLM engine not configured. Set MEDA_PICO_LLM_PROVIDER env.",
                "llm_not_configured",
            )
        import asyncio
        pico = asyncio.run(_llm_extract(rec, _LLM_PROVIDER))
    else:
        pico = _rule_baseline_extract(rec)

    exist = session.exec(
        select(LiteraturePico).where(LiteraturePico.record_id == record_id)
    ).first()
    if exist is not None:
        session.delete(exist)
        session.flush()
    session.add(pico)
    rec.pico_status = "extracted" if pico.population or pico.intervention else "failed"
    session.add(rec)
    session.commit()
    session.refresh(pico)
    return pico


def batch_extract_pico(
    session: Session,
    record_ids: list[int],
    *,
    method: Literal["rule_baseline", "llm"] = "rule_baseline",
) -> BatchResult:
    if not record_ids:
        raise PicoExtractionError("no_records_provided", "no_records_provided")
    processed = 0
    already = 0
    failed = 0
    for rid in record_ids:
        rec = session.get(LiteratureRecord, rid)
        if rec is None:
            failed += 1
            continue
        if rec.pico_status == "extracted":
            already += 1
            continue
        try:
            extract_pico_for_record(session, rid, method=method)
            processed += 1
        except PicoExtractionError as exc:
            if exc.code in {"llm_not_configured", "llm_not_implemented"}:
                raise
            failed += 1
            rec.pico_status = "failed"
            session.add(rec)
            session.commit()
    return BatchResult(processed=processed, already_had=already, failed=failed)


def suggest_pico_autofill(
    session: Session,
    run_id: int,
    top_n_records: int = 5,
):
    run = session.get(SearchRun, run_id)
    if run is None:
        from fastapi import HTTPException
        raise HTTPException(404, "search_run not found")

    records = list(session.exec(
        select(LiteratureRecord)
        .where(LiteratureRecord.search_run_id == run.id)
        .where(LiteratureRecord.dedupe_status != "duplicate")
        .order_by((LiteratureRecord.relevance_score or 0).desc())
        .limit(max(20, top_n_records))
    ).all())
    if not records:
        from app.schemas import PicoAutofillDraft as _D
        return _D(p="", i="", c="", o="", supporting_record_ids=[])

    picos = list(session.exec(
        select(LiteraturePico).where(
            LiteraturePico.record_id.in_([r.id for r in records])
        )
    ).all())
    pico_by_rec = {p.record_id: p for p in picos}
    pop_counter: Counter[str] = Counter()
    int_counter: Counter[str] = Counter()
    cmp_counter: Counter[str] = Counter()
    out_counter: Counter[str] = Counter()
    supporting = []
    for r in records:
        p = pico_by_rec.get(r.id) or _rule_baseline_extract(r)
        scored = 0
        if p.population:
            for part in p.population.split("；"):
                if part:
                    pop_counter[part] += 1
                    scored += 1
        if p.intervention:
            for part in p.intervention.split("；"):
                if part:
                    int_counter[part] += 1
                    scored += 1
        if p.comparison:
            for part in p.comparison.split("；"):
                if part:
                    cmp_counter[part] += 1
                    scored += 1
        if p.outcome:
            for part in p.outcome.split("；"):
                if part:
                    out_counter[part] += 1
                    scored += 1
        if scored >= 2 and len(supporting) < top_n_records:
            supporting.append(r.id)

    def _top(counter: Counter[str]) -> str:
        items = [t for t, _ in counter.most_common(5)]
        return "；".join(items)

    from app.schemas import PicoAutofillDraft as _D
    return _D(
        p=_top(pop_counter),
        i=_top(int_counter),
        c=_top(cmp_counter),
        o=_top(out_counter),
        supporting_record_ids=supporting,
    )
