import json
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import engine
from app.main import app
from app.models import LiteratureRecord


def _login_and_create_project(client: TestClient) -> tuple[str, int]:
    login = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "demo-hospital",
            "organization_name": "Demo Hospital",
            "user_id": "u-t6-001",
            "display_name": "Dr. T6",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    token = login.json()["token"]

    project = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-t6-001",
            "name": "T6 筛选阶段测试",
            "description": "Wave82B T6 stage entry screening",
        },
    )

    return token, project.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _insert_literature_record(
    project_id: int,
    title: str,
    screening_stage: str | None = None,
    screening_decision: str | None = None,
    exclude_reason: dict | None = None,
    dedupe_status: str = "unique",
) -> None:
    with Session(engine) as session:
        rec = LiteratureRecord(
            project_id=project_id,
            title=title,
            source_key="pubmed",
            source_label="PubMed",
            dedupe_status=dedupe_status,
            screening_stage=screening_stage,
            screening_decision=screening_decision,
            exclude_reason_json=json.dumps(exclude_reason, ensure_ascii=False) if exclude_reason else None,
        )
        session.add(rec)
        session.commit()


class TestT6StageEntryScreening:
    def test_t6_e01_missing_stage_404(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/no_exist",
            headers=_auth(token),
        )
        assert response.status_code == 404

    def test_t6_e02_topic_stage_has_no_prisma(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/topic",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        assert "prisma_counts" in body
        assert body["prisma_counts"] is None
        assert body["stage_key"] == "topic"
        assert body["stage_label"] == "选题"
        assert len(body["entry_cards"]) == 3

    def test_t6_e03_screening_has_prisma_11_fields(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        _insert_literature_record(
            project_id=project_id,
            title="TA included paper",
            screening_stage="ta",
            screening_decision="include",
        )
        _insert_literature_record(
            project_id=project_id,
            title="TA excluded paper",
            screening_stage="ta",
            screening_decision="exclude",
            exclude_reason={"preset_class": 2, "note": "人群不符"},
        )
        _insert_literature_record(
            project_id=project_id,
            title="Duplicate auto-excluded",
            screening_stage=None,
            screening_decision="exclude",
            exclude_reason={"preset_class": 1, "note": None, "stage": "ta", "auto_by": "dedupe"},
            dedupe_status="duplicate",
        )

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/screening",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        prisma_counts = body["prisma_counts"]
        assert prisma_counts is not None
        assert prisma_counts["identification"] == 3
        assert len(prisma_counts) == 11, f"prisma_counts 应有 11 字段，实际 {len(prisma_counts)}: {list(prisma_counts.keys())}"

    def test_t6_e04_n2_zero_locks_fulltext_card(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/screening",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        prisma_counts = body["prisma_counts"]
        assert prisma_counts["ta_included"] == 0
        fulltext_card = next(c for c in body["entry_cards"] if c["key"] == "full-text")
        assert fulltext_card["status"] == "locked"

    def test_t6_e05_n2_positive_unlocks_fulltext_card(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        for i in range(2):
            _insert_literature_record(
                project_id=project_id,
                title=f"TA excluded {i+1}",
                screening_stage="ta",
                screening_decision="exclude",
                exclude_reason={"preset_class": 3, "note": "干预不符"},
            )
        for i in range(3):
            _insert_literature_record(
                project_id=project_id,
                title=f"TA included {i+1}",
                screening_stage="ta",
                screening_decision="include",
            )

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/screening",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        prisma_counts = body["prisma_counts"]
        assert prisma_counts["ta_included"] == 3
        fulltext_card = next(c for c in body["entry_cards"] if c["key"] == "full-text")
        assert fulltext_card["status"] == "ready"

    def test_t6_e06_three_cards_keys_present(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/screening",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        keys = [c["key"] for c in body["entry_cards"]]
        assert keys == ["title-abstract", "full-text", "prisma"]

    def test_t6_e07_prisma_card_status_always_ready(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        _insert_literature_record(
            project_id=project_id,
            title="Some screening record",
            screening_stage="ta",
            screening_decision="include",
        )

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/screening",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        prisma_card = next(c for c in body["entry_cards"] if c["key"] == "prisma")
        assert prisma_card["status"] == "ready"

    def test_t6_e08_stage_entry_response_extra_type_check(self) -> None:
        client = TestClient(app)
        token, project_id = _login_and_create_project(client)

        _insert_literature_record(
            project_id=project_id,
            title="FT included",
            screening_stage="fulltext",
            screening_decision="include",
        )
        _insert_literature_record(
            project_id=project_id,
            title="FT excluded",
            screening_stage="fulltext",
            screening_decision="exclude",
            exclude_reason={"preset_class": 6, "note": "数据不可用"},
        )
        _insert_literature_record(
            project_id=project_id,
            title="TA include",
            screening_stage="ta",
            screening_decision="include",
        )
        _insert_literature_record(
            project_id=project_id,
            title="TA exclude",
            screening_stage="ta",
            screening_decision="exclude",
            exclude_reason={"preset_class": 2, "note": "人群不符"},
        )
        _insert_literature_record(
            project_id=project_id,
            title="Dup excluded",
            screening_stage=None,
            screening_decision="exclude",
            exclude_reason={"preset_class": 1, "note": None},
            dedupe_status="duplicate",
        )

        response = client.get(
            f"/api/workspace/projects/{project_id}/stages/screening",
            headers=_auth(token),
        )
        assert response.status_code == 200
        body = response.json()
        prisma_counts = body["prisma_counts"]
        required_8_keys = {
            "identification",
            "ta_included",
            "ta_excluded",
            "fulltext_included",
            "fulltext_excluded",
            "duplicate_excluded",
            "included",
            "manual_override_applied",
        }
        assert required_8_keys.issubset(set(prisma_counts.keys())), (
            f"缺少 key: {required_8_keys - set(prisma_counts.keys())}"
        )
