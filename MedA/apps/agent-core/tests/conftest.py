from collections.abc import Generator
from dataclasses import dataclass

import pytest
from sqlmodel import Session

import app.models  # noqa: F401 – ensure all SQLModel classes register into metadata
from app.db import engine, init_db, reset_db
from app.models import Organization, ResearchProject, User


def pytest_addoption(parser):
    parser.addoption("--runneedsnetwork", action="store_true", default=False, help="Run tests marked needs_network (real-HTTP)")
    parser.addoption("--runeedsbrowser", action="store_true", default=False, help="Run tests marked needs_browser (real-browser)")
def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runneedsnetwork"):
        skip_mark = pytest.mark.skip(reason="skip needs_network (pass --runneedsnetwork to run)")
        for item in items:
            if "needs_network" in getattr(item, "keywords", {}): item.add_marker(skip_mark)
    if not config.getoption("--runeedsbrowser"):
        skip_browser = pytest.mark.skip(reason="skip needs_browser (pass --runeedsbrowser to run)")
        for item in items:
            if "needs_browser" in getattr(item, "keywords", {}): item.add_marker(skip_browser)


@dataclass
class UnifiedMockEntry:
    doi: str
    pmid: str
    title: str
    authors: str
    journal: str
    year: int | None
    abstract: str
    source_record_id: str | None = None


MOCK_PUBMED_DATASET: list[UnifiedMockEntry] = [
    UnifiedMockEntry(
        doi="10.1056/nejmoa2212939".lower(),
        pmid="37123457",
        title="Dapagliflozin in Patients with Chronic Kidney Disease",
        authors="Neuen BL, et al.",
        journal="New England Journal of Medicine",
        year=2023,
        abstract="BACKGROUND: The SGLT2 inhibitor... in chronic kidney disease (CKD). METHODS: We conducted a double-blind...",
        source_record_id="pm37123457",
    ),
    UnifiedMockEntry(
        doi="10.1016/s2213-8587(23)00042-5",
        pmid="37000001",
        title="Effect of Empagliflozin on Cardiovascular Outcomes in T2DM with Established CVD",
        authors="Zinman B, et al.",
        journal="Lancet Diabetes Endocrinol",
        year=2023,
        abstract="We studied empagliflozin versus placebo in T2DM with CVD...",
        source_record_id="pm37000001",
    ),
    UnifiedMockEntry(
        doi="10.1001/jama.2023.12345".lower(),
        pmid="37333333",
        title="Metformin plus Lifestyle versus Lifestyle Alone in Prediabetes",
        authors="Chen L, Zhang Y, Wang H",
        journal="JAMA",
        year=2024,
        abstract="This is a RCT of Metformin plus lifestyle against lifestyle...",
        source_record_id="pm37333333",
    ),
]

MOCK_CNKI_DATASET: list[UnifiedMockEntry] = [
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="二甲双胍联合 SGLT2 抑制剂治疗 2 型糖尿病合并慢性肾病疗效观察",
        authors="李明;王建国;赵丽",
        journal="中华内分泌代谢杂志",
        year=2024,
        abstract="目的 观察二甲双胍联合 SGLT2i 治疗 T2DM 合并 CKD 的疗效...",
        source_record_id="cnki-2024-0001",
    ),
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="GLP-1 RA 对心血管结局影响的真实世界研究（单中心）",
        authors="张伟;刘芳",
        journal="中国糖尿病杂志",
        year=2023,
        abstract="回顾性纳入 210 例 T2DM 患者...",
        source_record_id="cnki-2023-2345",
    ),
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="HFrEF 合并 2 型糖尿病患者启用 SGLT2 抑制剂的预后队列研究",
        authors="陈海波;吴丹;张琳;马骁",
        journal="中华心血管病杂志",
        year=2024,
        abstract="回顾性队列 368 例 HFrEF + T2DM，分析 SGLT2i 启用 12 月 HF 住院复合终点...",
        source_record_id="cnki-2024-hfref-99",
    ),
]

MOCK_WANFANG_DATASET: list[UnifiedMockEntry] = [
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="达格列净在 CKD 非糖尿病人群中的安全性 Meta 分析",
        authors="孙志远;陈曦",
        journal="中华肾脏病杂志",
        year=2024,
        abstract="系统评价达格列净用于非 DM CKD 的安全性 ...",
        source_record_id="wf-2024-1122",
    ),
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="基于 PRISMA 的糖尿病肾病随机对照试验文献质量评价（2019-2023）",
        authors="林婉如;赵一鸣;黄思琪",
        journal="中国循证医学杂志",
        year=2024,
        abstract="按 PRISMA 与 AMSTAR-2 标准系统评价 DKD 相关 RCT 报告质量共 68 篇...",
        source_record_id="wf-2024-prisma-08",
    ),
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="ARNI 联合 SGLT2i 在 HFrEF 合并 CKD 中的真实世界疗效",
        authors="郑凯;何梦婷;冯磊",
        journal="中华高血压杂志",
        year=2023,
        abstract="纳入 196 例 HFrEF + CKD(eGFR 30-60)，ARNI+SGLT2i vs 标准治疗，随访 6 月...",
        source_record_id="wf-2023-arni-7714",
    ),
]


SOURCE_DATASET_REGISTRY: dict[str, list[UnifiedMockEntry]] = {
    "pubmed": MOCK_PUBMED_DATASET,
    "cnki": MOCK_CNKI_DATASET,
    "wanfang": MOCK_WANFANG_DATASET,
}


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    reset_db()
    init_db()
    yield


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def create_test_user(session: Session) -> User:
    user = User(user_id="u-test-001", display_name="Test Doctor")
    session.add(user)
    session.flush()
    org = Organization(slug="demo-hospital", name="Demo Hospital")
    session.add(org)
    session.flush()
    return user


def create_test_project(session: Session, user: User) -> ResearchProject:
    project = ResearchProject(
        organization_slug="demo-hospital",
        owner_user_id=user.user_id,
        name="测试项目",
        description="Wave 8 模型测试",
        workspace_key="ws-test",
    )
    session.add(project)
    session.flush()
    return project


def inject_mock_datasets_into_adapters(
    monkeypatch,
    registry: dict[str, list[UnifiedMockEntry]],
) -> None:
    """Helper that pushes test mock entries into each StubAdapter's INJECTED_DATASET."""
    from app.services.sources import cnki_adapter, pubmed_adapter, wanfang_adapter
    from app.services.sources.protocol import UnifiedLiteratureEntry

    def _coerce(entries: list[UnifiedMockEntry]) -> list[UnifiedLiteratureEntry]:
        return [
            UnifiedLiteratureEntry(
                doi=e.doi, pmid=e.pmid, title=e.title, authors=e.authors,
                journal=e.journal, year=e.year, abstract=e.abstract,
                source_key="__unset__", source_record_id=e.source_record_id,
            ) for e in entries
        ]

    if "pubmed" in registry:
        mock_entries = _coerce(registry["pubmed"])
        async def _esearch(q, ctx):
            ids = [e.source_record_id or f"m{i}" for i, e in enumerate(mock_entries, 1)]
            return ids, len(mock_entries)
        async def _efetch(ids):
            return mock_entries
        monkeypatch.setattr(
            "app.services.sources.pubmed_adapter._esearch_pubmed_ids", _esearch
        )
        monkeypatch.setattr(
            "app.services.sources.pubmed_adapter._efetch_parse_entries", _efetch
        )
    if "cnki" in registry:
        monkeypatch.setattr(
            cnki_adapter, "INJECTED_DATASET", _coerce(registry["cnki"])
        )
    if "wanfang" in registry:
        monkeypatch.setattr(
            wanfang_adapter, "INJECTED_DATASET", _coerce(registry["wanfang"])
        )


import os as _os
import pytest as _pytest

_VALID_PRESETS_W12 = [
    "sglt2i_ckd",
    "empagliflozin_hf",
    "glp1_weightloss",
    "liraglutide_nafld",
    "pkd_tolvaptan",
    "ckd_blood_pressure_control",
]

_PRESET_TITLE_ABSTRACT_TEMPLATES_W12 = [
    ("{drug} in type 2 diabetes: vs type 2 diabe trial n{i}",
     "Phase 2 trial of {drug} in albuminuria. Patients n=100 were randomized. Primary endpoint egfr decline. HbA1c reduction observed. Body weight change measured. Safety profile consistent with class. Trial registry NCT{i:08d}."),
    ("{drug} for heart failure with preserved ejection fraction trial n{i}",
     "Phase 3 randomized double-blind {drug} vs placebo in chronic HF with EF>40%. NT-proBNP change primary endpoint. Cardiovascular death or HF hospital composite secondary. Follow-up 12 months. Baseline characteristics balanced."),
    ("{drug} once-weekly injection obesity trial n{i}",
     "Phase 3 trial {drug} for weight management in BMI>=30. Co-primary: %BW loss and >=5% BW responder. Adherence daily injections tracked. Gastrointestinal side effects most common AE. Study duration 68 weeks."),
    ("{drug} for NASH-related fibrosis liver trial n{i}",
     "Phase 2b {drug} liver histology NAS fibrosis improvement. Liver biopsy paired baseline end-of-treatment ALT/AST reduction monitored. Hepatic fat fraction MRI-PDFF. Weight loss secondary outcome."),
    ("{drug} for ADPKD cystic progression trial n{i}",
     "Phase 3 {drug} TKV percent change total kidney volume 36 months. eGFR slope secondary endpoint. Hyponatremia safety monitoring. Water intake protocol adherence. PK trough levels assessed monthly."),
    ("{drug} combination for resistant hypertension trial n{i}",
     "Phase 4 open-label {drug} + thiazide + ACEi triple therapy clinic BP reduction 24h ambulatory. Primary BP change from baseline to week 12. Secondary: CV event rate 1 year. Renal function eGFR/UACR safety."),
]


def _ensure_w12_synthetic_fixture_exists() -> _os.PathLike:
    """Generate w12_synthetic_50k.json deterministically (seed=42) if it's missing.

    Avoids committing 137.56 MB to git (GitHub 100MB limit).
    File shape: list[{id:int, nct_id:str, title:str, abstract:str, preset:str}]
    6 VALID_PRESETS x 63,500 records each = 381,000 total records; continuous id 1..381000.
    """
    import json
    import pathlib
    import random
    here = pathlib.Path(__file__).resolve().parent
    fixture_path = here / "fixtures" / "w12_synthetic_50k.json"
    if fixture_path.exists() and fixture_path.stat().st_size > 1_000_000:
        return fixture_path
    n_per_preset = 63500
    rng = random.Random(42)
    records = []
    _id = 0
    for p_idx, preset in enumerate(_VALID_PRESETS_W12):
        tpl_title, tpl_abs = _PRESET_TITLE_ABSTRACT_TEMPLATES_W12[p_idx]
        drug = preset.split("_")[0]
        for i in range(n_per_preset):
            _id += 1
            records.append({
                "id": _id,
                "nct_id": f"NCT{10000000 + rng.randrange(90000000)}",
                "title": tpl_title.format(drug=drug, i=i),
                "abstract": tpl_abs.format(drug=drug, i=i),
                "preset": preset,
            })
    fixture_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return fixture_path


@_pytest.fixture(scope="session", autouse=True)
def _w12_fixture_materializer_50k_big_asset():
    _ensure_w12_synthetic_fixture_exists()


@_pytest.fixture(autouse=True)
def _force_all_sources_force_mock_for_pytest(monkeypatch):
    """pytest 默认零外网：三 source 全 force_mock。
    needs_network 标记的测试会显式 pop 这些 env。
    """
    monkeypatch.setenv("MEDA_PUBMED_MODE", "force_mock")
    monkeypatch.setenv("MEDA_CNKI_MODE",   "force_mock")
    monkeypatch.setenv("MEDA_WANFANG_MODE","force_mock")
