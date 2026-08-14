from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.services.bm25_scoring import compute_bm25_scores_for, tokenize_for_bm25
from app.services.literature import _normalize_identifiers
from app.services.pico import (
    _extract_comparison,
    _extract_intervention,
    _extract_outcome,
    _extract_population,
    _detect_study_type,
    _rule_baseline_extract as _sa_pico_extract,  # keep import for external API parity
)
from app.services.sources.protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    UnifiedLiteratureEntry,
)
from app.services.sources.pubmed_adapter import PubMedAdapter

DEMO_PRESETS_PY: dict[str, dict] = {
    "sglt2i_ckd": {
        "boolean_text": "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR canagliflozin[Title/Abstract]) AND (chronic kidney disease[Title/Abstract] OR CKD[Title/Abstract] OR diabetic nephropathies[MeSH Major Topic]) AND randomised controlled trial[pt]",
        "pico": {"p": "adult with type 2 diabetes mellitus and CKD stage 2-4 or macroalbuminuria", "i": "SGLT2 inhibitor add-on to RAAS blockade", "c": "placebo or standard of care without SGLT2i", "o": "composite renal endpoint (eGFR decline ≥50% / ESRD / renal death) ; change in eGFR slope ; 3P-MACE ; AE of genital mycotic infection / DKA / hypovolemia"},
        "filters": {"study_type": ["rct"]},
    },
    "sglt2i_hfredef": {
        "boolean_text": "(DAPA-HF[Title/Abstract] OR DAPA-CKD[Title/Abstract] OR (dapagliflozin[Title/Abstract] AND (heart failure with reduced ejection fraction[Title/Abstract] OR HFrEF[Title/Abstract] OR chronic kidney disease[Title/Abstract]))) AND randomised controlled trial[pt]",
        "pico": {"p": "HFrEF LVEF ≤40% with/without T2DM; CKD eGFR 25-75 + uACR >200", "i": "dapagliflozin 10 mg once daily", "c": "matching placebo", "o": "CV death or worsening HF composite; renal composite; change in NT-proBNP / KCCQ"},
        "filters": {"study_type": ["rct"]},
    },
    "met_cv_presto": {
        "boolean_text": "(PRESTO[Title/Abstract] OR (metformin[Title/Abstract] AND cardiovascular[Title/Abstract] AND (prediabetes[Title/Abstract] OR insulin resistance[Title/Abstract]))) AND randomized controlled trial[pt]",
        "pico": {"p": "prediabetes / insulin resistance with CV risk factors but no established ASCVD", "i": "metformin extended-release +/- lifestyle intervention", "c": "placebo or lifestyle-only", "o": "MACE (CV death / MI / stroke) ; change in LDL-C / SBP / Hba1c"},
        "filters": {"study_type": ["rct"]},
    },
    "glp1_mace_rws": {
        "boolean_text": "(glucagon-like peptide-1 receptor agonist[Title/Abstract] OR GLP-1 RA[Title/Abstract] OR liraglutide[Title/Abstract] OR semaglutide[Title/Abstract] OR dulaglutide[Title/Abstract] OR tirzepatide[Title/Abstract]) AND (major adverse cardiovascular events[Title/Abstract] OR MACE[Title/Abstract] OR cardiovascular outcomes[Title/Abstract]) AND ((randomized controlled trial[pt]) OR (real-world[Title/Abstract] OR retrospective[Title/Abstract] OR cohort[Title/Abstract]))",
        "pico": {"p": "T2DM with established ASCVD or high CV risk", "i": "GLP-1 RA (injectable or oral) as add-on", "c": "DPP-4 inhibitor / sulfonylurea / basal insulin / placebo", "o": "3P-MACE (CV death, non-fatal MI, non-fatal stroke) ; all-cause mortality ; severe hypoglycaemia"},
        "filters": {"study_type": ["rct_and_sr"]},
    },
    "sglt2i_dka_safety": {
        "boolean_text": "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR ertugliflozin[Title/Abstract]) AND (diabetic ketoacidosis[Title/Abstract] OR DKA[Title/Abstract] OR euglycemic ketoacidosis[Title/Abstract] OR ketosis[Title/Abstract])",
        "pico": {"p": "T2DM or T1DM on SGLT2i around peri-operative / fasting / severe illness periods", "i": "SGLT2i continued or paused peri-event window", "c": "same population without SGLT2i exposure", "o": "event rate of DKA / euglycemic DKA ; median bicarbonate / gap / anion gap at diagnosis"},
    },
    "met_lifestyle_predm": {
        "boolean_text": "(diabetes prevention program[Title/Abstract] OR DPP[Title/Abstract] OR prediabetes[Title/Abstract]) AND (metformin[Title/Abstract] AND (lifestyle[Title/Abstract] OR diet AND exercise[Title/Abstract])) AND (progression to type 2 diabetes[Title/Abstract] OR incidence of type 2 diabetes[Title/Abstract])",
        "pico": {"p": "adult with prediabetes (IFG / IGT / elevated HbA1c 5.7-6.4%) without prior CV event", "i": "metformin 850 mg BID + intensive lifestyle (≥7% weight loss, 150 min/wk exercise)", "c": "placebo + standard lifestyle brochure", "o": "time to T2DM diagnosis (primary) ; regression to normoglycaemia ; change in weight / Hba1c at 3y"},
        "filters": {"pubmed_mindate": "1996/01/01"},
    },
}


@dataclass
class _MiniPico:
    population: str | None
    intervention: str | None
    comparison: str | None
    outcome: str | None
    study_type: str | None
    extraction_method: str
    confidence: float | None
    record_id: int | None
    p_text: str
    i_text: str
    c_text: str
    o_text: str


def _mini_extract_pico(title: str, abstract: str):
    text = f"{title}\n{abstract}"
    pop, _ = _extract_population(text)
    intr, _ = _extract_intervention(text)
    cmp, _ = _extract_comparison(text)
    out, _ = _extract_outcome(text)
    study, _ = _detect_study_type(text)
    return _MiniPico(
        population=pop, intervention=intr, comparison=cmp, outcome=out,
        study_type=study, extraction_method="rule_baseline_demo", confidence=None,
        record_id=None,
        p_text=(pop or ""), i_text=(intr or ""), c_text=(cmp or ""), o_text=(out or ""),
    )


@dataclass
class DemoResult:
    preset_key: str
    search_run_id: int
    raw_hits: int
    after_dedupe_hits: int
    bm25_top3: list[dict]
    pico_top5: list[dict]
    csv_export_path: str | None
    warnings: list[str]
    fallback_mode: bool


def _resolve_mode_or_exit(preset_key: str) -> None:
    if preset_key not in DEMO_PRESETS_PY:
        print(f"[demo] ERROR: unknown preset '{preset_key}'.", file=sys.stderr)
        print(
            "[demo] Available keys:",
            ", ".join(sorted(DEMO_PRESETS_PY.keys())),
            file=sys.stderr,
        )
        sys.exit(2)


async def run_pubmed_demo(
    preset_key: str,
    *,
    export_csv: bool = True,
    export_dir: Path | None = None,
) -> DemoResult:
    _resolve_mode_or_exit(preset_key)
    preset = DEMO_PRESETS_PY[preset_key]

    ctx = SearchRunContext(
        project_id=0,
        search_run_id=0,
        pubmed_api_key=os.environ.get("PUBMED_API_KEY"),
        adapter_modes={"pubmed": "prefer_real"},
        rate_limit_rps={"pubmed": 3.0},
    )

    adapter = PubMedAdapter()
    norm_q = NormalizedSearchQuery(
        boolean_text=preset["boolean_text"],
        filters=preset.get("filters", {}) if isinstance(preset.get("filters"), dict) else {},
        source_key="pubmed",
    )
    adapter_result: AdapterResult = await adapter.run_search(norm_q, ctx)

    normalized_records = [
        UnifiedLiteratureEntry(
            doi=_normalize_identifiers(r.doi, "", "")[0],
            pmid=_normalize_identifiers("", r.pmid, "")[1],
            title=(r.title or "").strip(),
            authors=r.authors,
            journal=r.journal,
            year=r.year,
            abstract=r.abstract,
            source_key=r.source_key,
            source_record_id=r.source_record_id,
        )
        for r in adapter_result.records
    ]

    seen_doi: set[str] = set()
    seen_pmid: set[str] = set()
    seen_title_year: set[tuple[str, int | None]] = set()
    deduped: list[UnifiedLiteratureEntry] = []
    for r in normalized_records:
        doi, pmid, title = r.doi or "", r.pmid or "", (r.title or "").strip()
        if title == "":
            continue
        key_ty = (title, r.year)
        if doi and doi in seen_doi:
            continue
        if pmid and pmid in seen_pmid:
            continue
        if key_ty in seen_title_year:
            continue
        if doi:
            seen_doi.add(doi)
        if pmid:
            seen_pmid.add(pmid)
        seen_title_year.add(key_ty)
        deduped.append(r)
    raw_hits = len(normalized_records)
    after_dedupe_hits = len(deduped)

    fallback_mode = bool(adapter_result.warnings) and any(
        "fallback" in w or "注入" in w for w in adapter_result.warnings
    )

    @dataclass
    class _MiniRec:
        title: str
        abstract: str
        year: int | None
        journal: str
        doi: str
        pmid: str
        source_record_id: str
        bm25_score: float | None = None

    mini_records: list[_MiniRec] = [
        _MiniRec(
            title=(e.title or "").strip(),
            abstract=e.abstract or "",
            year=e.year,
            journal=e.journal or "",
            doi=e.doi or "",
            pmid=e.pmid or "",
            source_record_id=e.source_record_id or "",
        )
        for e in deduped
    ]

    pico = preset.get("pico") or {}
    q_raw = " ".join(
        [preset["boolean_text"]] + [str(pico[k]) for k in ("p", "i", "c", "o") if pico.get(k)]
    )
    q_tokens = tokenize_for_bm25(q_raw)
    if mini_records and q_tokens:
        scores = compute_bm25_scores_for(mini_records, q_tokens)
        max_s = max(scores) if scores and max(scores) > 0 else None
        for m, s in zip(mini_records, scores):
            m.bm25_score = (float(s) / float(max_s)) if max_s is not None else None

    sorted_by_score = sorted(
        mini_records,
        key=lambda e: (e.bm25_score is not None, e.bm25_score or 0.0),
        reverse=True,
    )[:3]
    bm25_top3 = [
        {
            "title": m.title[:140],
            "score": round(m.bm25_score or 0.0, 4),
            "year": m.year,
            "doi": m.doi or None,
        }
        for m in sorted_by_score
    ]

    pico_domain_words: dict[str, dict[str, int]] = {"p": {}, "i": {}, "c": {}, "o": {}}
    for m in mini_records:
        pico_obj = _mini_extract_pico(m.title or "", m.abstract or "")
        for dom in ("p", "i", "c", "o"):
            val = getattr(pico_obj, f"{dom}_text") or ""
            toks = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]", val.lower())
            for t in toks:
                if len(t) < 2 and not ("\u4e00" <= t <= "\u9fff"):
                    continue
                pico_domain_words[dom][t] = pico_domain_words[dom].get(t, 0) + 1
    flat: list[tuple[str, str, int]] = []
    for dom, counter in pico_domain_words.items():
        for tok, freq in counter.items():
            flat.append((dom, tok, freq))
    flat.sort(key=lambda x: x[2], reverse=True)
    pico_top5 = [
        {"domain": dom, "value": tok, "freq": freq} for (dom, tok, freq) in flat[:5]
    ]

    csv_export_path: str | None = None
    if export_csv and mini_records:
        export_dir_ = export_dir or (
            Path(__file__).resolve().parent.parent.parent / "artifacts" / "demo_csv"
        )
        export_dir_.mkdir(parents=True, exist_ok=True)
        csv_path = export_dir_ / (
            f"pubmed_demo_{preset_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "rank",
                    "title",
                    "year",
                    "journal",
                    "doi",
                    "pmid",
                    "source_record_id",
                    "bm25_score",
                ]
            )
            ranked = sorted(
                mini_records,
                key=lambda x: (x.bm25_score is not None, x.bm25_score or 0.0),
                reverse=True,
            )
            for i, m in enumerate(ranked, 1):
                w.writerow(
                    [
                        i,
                        m.title,
                        m.year or "",
                        m.journal,
                        m.doi,
                        m.pmid,
                        m.source_record_id,
                        round(m.bm25_score or 0.0, 4),
                    ]
                )
        csv_export_path = str(csv_path)

    return DemoResult(
        preset_key=preset_key,
        search_run_id=0,
        raw_hits=raw_hits,
        after_dedupe_hits=after_dedupe_hits,
        bm25_top3=bm25_top3,
        pico_top5=pico_top5,
        csv_export_path=csv_export_path,
        warnings=list(adapter_result.warnings or []),
        fallback_mode=fallback_mode,
    )


def _print_report(r: DemoResult) -> None:
    print("=" * 56)
    print(f"  MedA · PubMed real-data demo   preset = {r.preset_key}")
    tag = "(no-network fallback injected dataset)" if r.fallback_mode else "(used live NCBI E-utilities)"
    print(f"  {tag}")
    print("=" * 56)
    print(
        f"  [① Hits] raw PubMed = {r.raw_hits} | after dedupe = {r.after_dedupe_hits}"
    )
    if r.warnings:
        print("  [Warnings]")
        for w in r.warnings:
            print(f"    · {w}")
    print()
    print("  [② BM25 top-3]")
    for i, row in enumerate(r.bm25_top3, 1):
        print(
            f"    {i}. [score={row['score']:.3f}] {row['title']}  ({row['year']}) doi={row['doi'] or 'N/A'}"
        )
    print()
    print("  [③ PICO frequent tokens (rule_baseline)]")
    for row in r.pico_top5:
        print(f"    · [{row['domain']}] {row['value']!r} × {row['freq']}")
    if r.csv_export_path:
        print()
        print(f"  [④ CSV exported] → {r.csv_export_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MedA · PubMed real-data end-to-end CLI demo."
    )
    parser.add_argument(
        "preset_key",
        help="One of: " + ", ".join(sorted(DEMO_PRESETS_PY.keys())),
    )
    parser.add_argument(
        "--no-csv", action="store_true", help="Skip CSV export."
    )
    parser.add_argument(
        "--export-dir", type=Path, default=None, help="Override CSV export directory."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Dump DemoResult as JSON on success after human-readable sections.",
    )
    args = parser.parse_args()

    result = asyncio.run(
        run_pubmed_demo(
            args.preset_key,
            export_csv=not args.no_csv,
            export_dir=args.export_dir,
        )
    )
    _print_report(result)

    if args.json:
        print()
        print("--- JSON ---")
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                default=lambda o: getattr(o, "__dict__", str(o)),
                indent=2,
            )
        )

    if result.after_dedupe_hits == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
