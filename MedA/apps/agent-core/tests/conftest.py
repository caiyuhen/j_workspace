from collections.abc import Generator
from dataclasses import dataclass

import pytest
from sqlmodel import Session

import app.models  # noqa: F401 – ensure all SQLModel classes register into metadata
from app.db import engine, init_db, reset_db
from app.models import Organization, ResearchProject, User


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
