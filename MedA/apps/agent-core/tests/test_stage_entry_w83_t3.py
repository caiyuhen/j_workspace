import json
from fastapi.testclient import TestClient
from sqlmodel import Session, select, func

from app.db import engine
from app.main import app
from app.models import (
    ExtractionTemplate,
    ExtractionCell,
    LiteratureRecord,
    OutcomeDefinition,
    AnalysisRun,
)


def _login_and_create_project(client: TestClient) -> tuple[str, int]:
    login = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "demo-hospital",
            "organization_name": "Demo Hospital",
            "user_id": "u-t3-001",
            "display_name": "Dr. T3",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    token = login.json()["token"]

    project = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-t3-001",
            "name": "T3 WAVE8.3 阶段入口卡片锁测试",
            "description": "Wave83 T3 extraction+analysis stage cards dynamic lock",
        },
    )

    return token, project.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _insert_literature_ft_included(project_id: int, n: int) -> None:
    with Session(engine) as session:
        for i in range(n):
            rec = LiteratureRecord(
                project_id=project_id,
                title=f"FT-Included-{i+1}",
                source_key="pubmed",
                source_label="PubMed",
                dedupe_status="unique",
                screening_stage="fulltext",
                screening_decision="include",
            )
            session.add(rec)
        session.commit()


def _insert_extraction_template(
    project_id: int,
    locked: bool,
    fields_count: int,
) -> None:
    fields = []
    for i in range(fields_count):
        fields.append({
            "key": f"f{i+1}",
            "label": f"字段{i+1}",
            "type": "text",
        })
    with Session(engine) as session:
        tpl = ExtractionTemplate(
            project_id=project_id,
            name="测试模板",
            locked=locked,
            fields_json=fields,
        )
        session.add(tpl)
        session.commit()


def _insert_extraction_cells(
    project_id: int,
    total_cells: int,
    fields_count: int,
) -> None:
    with Session(engine) as session:
        recs = session.exec(
            select(LiteratureRecord).where(
                LiteratureRecord.project_id == project_id,
                LiteratureRecord.screening_stage == "fulltext",
                LiteratureRecord.screening_decision == "include",
            )
        ).all()
        inserted = 0
        for rec in recs:
            for f_idx in range(fields_count):
                if inserted >= total_cells:
                    break
                cell = ExtractionCell(
                    record_id=rec.id or 0,
                    field_key=f"f{f_idx+1}",
                    reviewer_id="u-t3-001",
                    project_id=project_id,
                    value_json=json.dumps({"text": f"val-{inserted}"}, ensure_ascii=False),
                    confidence=0.95,
                )
                session.add(cell)
                inserted += 1
            if inserted >= total_cells:
                break
        session.commit()


def _insert_outcome_definitions(project_id: int, count: int) -> None:
    with Session(engine) as session:
        for i in range(count):
            od = OutcomeDefinition(
                project_id=project_id,
                outcome_key=f"outcome_{i+1}",
                label=f"结局{i+1}",
                measure_type="continuous",
            )
            session.add(od)
        session.commit()


def _insert_analysis_runs(project_id: int, count: int) -> None:
    with Session(engine) as session:
        outcomes = session.exec(
            select(OutcomeDefinition).where(OutcomeDefinition.project_id == project_id)
        ).all()
        outcome_id = outcomes[0].id if outcomes else None
        for i in range(count):
            ar = AnalysisRun(
                project_id=project_id,
                outcome_id=outcome_id,
                method="meta_analysis",
                config_json={"alpha": 0.05},
                result_json={"smd": 0.32, "p_value": 0.012},
                status="done",
                created_by="u-t3-001",
            )
            session.add(ar)
        session.commit()


class TestT3ExtractionStageCards:
    def test_t3_a01_no_tpl_fields_lt3_template_locked(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/extraction",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert "extraction_stage_cards" in body
        assert body["extraction_stage_cards"] is not None
        cards = {c["key"]: c for c in body["extraction_stage_cards"]}
        assert "template" in cards
        assert cards["template"]["status"] == "locked"

    def test_t3_a02_tpl_locked_true_fields_ge3_template_ready(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        _insert_extraction_template(project_id, locked=True, fields_count=5)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/extraction",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        cards = {c["key"]: c for c in body["extraction_stage_cards"]}
        assert cards["template"]["status"] == "ready"

    def test_t3_a03_tpl_fields_ge3_cells_lt_n4_evidence_table_locked(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        _insert_extraction_template(project_id, locked=True, fields_count=4)
        _insert_literature_ft_included(project_id, n=4)
        _insert_extraction_cells(project_id, total_cells=3, fields_count=4)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/extraction",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        cards = {c["key"]: c for c in body["extraction_stage_cards"]}
        assert cards["evidence-table"]["status"] == "locked"

    def test_t3_a04_dual_review_always_locked(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        _insert_extraction_template(project_id, locked=True, fields_count=6)
        _insert_literature_ft_included(project_id, n=3)
        _insert_extraction_cells(project_id, total_cells=30, fields_count=6)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/extraction",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        cards = {c["key"]: c for c in body["extraction_stage_cards"]}
        assert cards["dual-review"]["status"] == "locked"


class TestT3AnalysisStageCards:
    def test_t3_b01_outcome_lt1_variables_locked(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/analysis",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert "analysis_stage_cards" in body
        assert body["analysis_stage_cards"] is not None
        cards = {c["key"]: c for c in body["analysis_stage_cards"]}
        assert "variables" in cards
        assert cards["variables"]["status"] == "locked"

    def test_t3_b02_outcome_ge1_runs_eq0_vars_ready_results_charts_locked(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        _insert_outcome_definitions(project_id, count=3)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/analysis",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        cards = {c["key"]: c for c in body["analysis_stage_cards"]}
        assert cards["variables"]["status"] == "ready"
        assert cards["results"]["status"] == "locked"
        assert cards["charts"]["status"] == "locked"

    def test_t3_b03_runs_ge1_results_charts_ready(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        _insert_outcome_definitions(project_id, count=2)
        _insert_analysis_runs(project_id, count=2)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/analysis",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        cards = {c["key"]: c for c in body["analysis_stage_cards"]}
        assert cards["results"]["status"] == "ready"
        assert cards["charts"]["status"] == "ready"


class TestT3MigrationIdempotent:
    def test_t3_c01_double_reset_build_stage_entry_ok(self) -> None:
        from app.db import reset_db, init_db
        from app.models import ResearchProject, Organization, User
        from app.services.stage_entry import build_stage_entry

        reset_db()
        init_db()

        with Session(engine) as session:
            u = User(user_id="u-idem-001", display_name="IdemUser")
            session.add(u)
            o = Organization(slug="demo-hospital", name="Demo Hospital")
            session.add(o)
            session.flush()
            p = ResearchProject(
                organization_slug="demo-hospital",
                owner_user_id="u-idem-001",
                name="Idempotent 1",
                description="idem1",
                workspace_key="ws-idem-1",
            )
            session.add(p)
            session.flush()
            pid = p.id or 0
            r1 = build_stage_entry(session, p, "extraction")
            assert r1 is not None
            r2 = build_stage_entry(session, p, "analysis")
            assert r2 is not None

        reset_db()
        init_db()

        with Session(engine) as session:
            u = User(user_id="u-idem-002", display_name="IdemUser2")
            session.add(u)
            o = Organization(slug="demo-hospital", name="Demo Hospital")
            session.add(o)
            session.flush()
            p = ResearchProject(
                organization_slug="demo-hospital",
                owner_user_id="u-idem-002",
                name="Idempotent 2",
                description="idem2",
                workspace_key="ws-idem-2",
            )
            session.add(p)
            session.flush()
            r3 = build_stage_entry(session, p, "extraction")
            assert r3 is not None
            r4 = build_stage_entry(session, p, "analysis")
            assert r4 is not None
