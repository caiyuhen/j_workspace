from __future__ import annotations

import json
import re
from typing import Iterable, Sequence

from rank_bm25 import BM25Okapi
from sqlmodel import Session, select

from app.models import LiteratureRecord, SearchRun

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize_for_bm25(text: str) -> list[str]:
    if not text:
        return []
    cjk = CJK_RE.findall(text)
    words = [w.lower() for w in TOKEN_RE.findall(text)]
    return cjk + words


def _doc_tokens(r: LiteratureRecord) -> list[str]:
    return tokenize_for_bm25(f"{r.title} {r.abstract}")


def compute_bm25_scores_for(
    records: Sequence[LiteratureRecord], query_tokens: Iterable[str]
) -> list[float]:
    corpus = [_doc_tokens(r) for r in records]
    if not corpus:
        return []
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(list(query_tokens))
    return [float(x) for x in scores]


def recompute_bm25_for_search_run(session: Session, search_run_id: int) -> None:
    run = session.get(SearchRun, search_run_id)
    if run is None:
        return
    records = list(session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.search_run_id == run.id,
            LiteratureRecord.dedupe_status != "duplicate",
        )
    ).all())
    if not records:
        return
    try:
        snap = json.loads(run.query_snapshot or "{}")
    except Exception:
        snap = {}
    parts: list[str] = []
    for key in ("p", "i", "c", "o"):
        if snap.get(key):
            parts.append(str(snap[key]))
    if snap.get("boolean_text"):
        parts.append(str(snap["boolean_text"]))
    raw = " ".join(parts)
    q_tokens = tokenize_for_bm25(raw)
    if not q_tokens:
        for r in records:
            r.relevance_score = None
        session.add_all(records)
        session.commit()
        return
    scores = compute_bm25_scores_for(records, q_tokens)
    max_s = max(scores) if scores and max(scores) > 0 else None
    for r, s in zip(records, scores):
        r.relevance_score = float(s) / float(max_s) if max_s is not None else None
    session.add_all(records)
    session.commit()
