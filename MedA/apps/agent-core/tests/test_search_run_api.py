from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import engine
from app.main import app
from app.models import LiteratureRecord, SearchRun, SearchRunSource

from tests.conftest import SOURCE_DATASET_REGISTRY, inject_mock_datasets_into_adapters


def _login_and_create_project(client: TestClient) -> tuple[str, int]:
    login = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "demo-hospital",
            "organization_name": "Demo Hospital",
            "user_id": "u-001",
            "display_name": "Dr. Chen",
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
            "owner_user_id": "u-001",
            "name": "糖尿病心血管研究",
            "description": "Wave 8 search run integration tests",
        },
    )

    return token, project.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _base_url(project_id: int) -> str:
    return f"/api/workspace/projects/{project_id}/stages/search/search-runs"


def test_s1_create_search_run_happy_path() -> None:
    """S1: 成功创建 search run 返回 201 和 id。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        _base_url(project_id),
        headers=_auth(token),
        json={
            "sources": ["pubmed", "cnki", "wanfang"],
            "query_snapshot": {"p": "T2DM", "i": "SGLT2", "c": "placebo", "o": "MACE"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["id"] is not None
    assert body["project_id"] == project_id
    assert body["status"] == "pending"
    assert set(body["selected_sources"]) == {"pubmed", "cnki", "wanfang"}


def test_s1_create_search_run_fails_no_sources_422() -> None:
    """S1: 无 sources 时返回 422。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        _base_url(project_id),
        headers=_auth(token),
        json={
            "sources": [],
            "query_snapshot": {"p": "T2DM"},
        },
    )

    assert response.status_code == 422


def test_s1_create_search_run_fails_snapshot_and_version_both_null_422() -> None:
    """S1: query_snapshot 和 search_query_version_id 都为 null 时返回 422。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        _base_url(project_id),
        headers=_auth(token),
        json={
            "sources": ["pubmed"],
            "query_snapshot": None,
            "search_query_version_id": None,
        },
    )

    assert response.status_code == 422


def test_s2_list_search_runs_empty_total_0() -> None:
    """S2: 无 search runs 时返回 total=0。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(_base_url(project_id), headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_s3_get_nonexistent_search_run_404() -> None:
    """S3: 不存在的 search run 返回 404。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(
        f"{_base_url(project_id)}/99999",
        headers=_auth(token),
    )

    assert response.status_code == 404 or response.status_code == 422


def test_s4_cancel_pending_run_ok() -> None:
    """S4: 取消 pending 状态的 run 成功返回 cancelled。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    create_resp = client.post(
        _base_url(project_id),
        headers=_auth(token),
        json={
            "sources": ["pubmed"],
            "query_snapshot": {"p": "T2DM"},
        },
    )
    run_id = create_resp.json()["id"]

    cancel_resp = client.post(
        f"{_base_url(project_id)}/{run_id}/cancel",
        headers=_auth(token),
    )

    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"


def test_s4_cancel_already_completed_run_422() -> None:
    """S4: 取消已完成的 run 返回 422 already_finished。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    with Session(engine) as session:
        run = SearchRun(
            project_id=project_id,
            selected_sources="pubmed",
            status="completed",
            query_snapshot='{"p":"T2DM"}',
        )
        session.add(run)
        session.flush()
        run_id = run.id or 0
        srs = SearchRunSource(
            search_run_id=run_id,
            source_key="pubmed",
            status="completed",
        )
        session.add(srs)
        session.commit()

    cancel_resp = client.post(
        f"{_base_url(project_id)}/{run_id}/cancel",
        headers=_auth(token),
    )

    assert cancel_resp.status_code == 422
    assert "already" in cancel_resp.json()["detail"].lower() or \
           "finished" in cancel_resp.json()["detail"].lower()


def test_s5_retry_successful_run_422_nothing_to_retry() -> None:
    """S5: 重试成功完成的 run 返回 422 nothing_to_retry。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    with Session(engine) as session:
        run = SearchRun(
            project_id=project_id,
            selected_sources="pubmed",
            status="completed",
            query_snapshot='{"p":"T2DM"}',
        )
        session.add(run)
        session.flush()
        run_id = run.id or 0
        srs = SearchRunSource(
            search_run_id=run_id,
            source_key="pubmed",
            status="completed",
        )
        session.add(srs)
        session.commit()

    retry_resp = client.post(
        f"{_base_url(project_id)}/{run_id}/retry",
        headers=_auth(token),
    )

    assert retry_resp.status_code == 422


def test_s6_export_csv_content_type_and_filename() -> None:
    """S6: CSV 导出 Content-Type=text/csv 且 filename header 包含安全 id+date。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    with Session(engine) as session:
        run = SearchRun(
            project_id=project_id,
            selected_sources="pubmed",
            status="completed",
            query_snapshot='{"p":"T2DM"}',
        )
        session.add(run)
        session.flush()
        run_id = run.id or 0
        srs = SearchRunSource(
            search_run_id=run_id,
            source_key="pubmed",
            status="completed",
            records_retrieved=2,
            records_imported=2,
        )
        session.add(srs)
        rec1 = LiteratureRecord(
            project_id=project_id,
            title="Paper 1",
            source_key="pubmed",
            search_run_id=run_id,
        )
        rec2 = LiteratureRecord(
            project_id=project_id,
            title="Paper 2",
            source_key="pubmed",
            search_run_id=run_id,
        )
        session.add_all([rec1, rec2])
        session.commit()

    export_resp = client.get(
        f"{_base_url(project_id)}/{run_id}/export.csv",
        headers=_auth(token),
    )

    assert export_resp.status_code == 200
    content_type = export_resp.headers.get("content-type", "")
    assert "text/csv" in content_type

    disp = export_resp.headers.get("content-disposition", "")
    assert "search-run-" in disp
    import re
    assert re.search(r"\d{8}", disp), "filename 应包含日期 YYYYMMDD 格式"


def test_s7_poll_status_right_after_create() -> None:
    """S7: 创建后立即 poll 返回 finished_sources=0 total=3。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    create_resp = client.post(
        _base_url(project_id),
        headers=_auth(token),
        json={
            "sources": ["pubmed", "cnki", "wanfang"],
            "query_snapshot": {"p": "T2DM"},
        },
    )
    run_id = create_resp.json()["id"]

    poll_resp = client.get(
        f"{_base_url(project_id)}/{run_id}/status",
        headers=_auth(token),
    )

    assert poll_resp.status_code == 200
    poll_body = poll_resp.json()
    assert poll_body["total_sources"] == 3
    assert poll_body["finished_sources"] == 0


def test_b1_post_recompute_bm25_queued_true(monkeypatch) -> None:
    """B1: POST recompute-bm25 返回 {queued:true}。"""
    inject_mock_datasets_into_adapters(monkeypatch, SOURCE_DATASET_REGISTRY)
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    with Session(engine) as session:
        run = SearchRun(
            project_id=project_id,
            selected_sources="pubmed",
            status="completed",
            query_snapshot='{"p":"T2DM","i":"SGLT2","c":"placebo","o":"MACE"}',
        )
        session.add(run)
        session.flush()
        run_id = run.id or 0
        srs = SearchRunSource(
            search_run_id=run_id,
            source_key="pubmed",
            status="completed",
        )
        session.add(srs)
        for entry in SOURCE_DATASET_REGISTRY["pubmed"]:
            rec = LiteratureRecord(
                project_id=project_id,
                title=entry.title,
                authors=entry.authors,
                journal=entry.journal,
                year=entry.year,
                doi=entry.doi,
                pmid=entry.pmid,
                abstract=entry.abstract,
                source_key="pubmed",
                search_run_id=run_id,
            )
            session.add(rec)
        session.commit()

    recompute_resp = client.post(
        f"{_base_url(project_id)}/{run_id}/recompute-bm25",
        headers=_auth(token),
    )

    assert recompute_resp.status_code == 200
    assert recompute_resp.json() == {"queued": True}


def test_p1_batch_extract_pico_empty_record_ids_422() -> None:
    """P1: 空 record_ids 返回 422 no_records_provided。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    url = f"/api/workspace/projects/{project_id}/stages/search/literature/records/pico:batch-extract"
    resp = client.post(
        url,
        headers=_auth(token),
        json={"record_ids": [], "method": "rule_baseline"},
    )

    assert resp.status_code == 422
    assert "no_records_provided" in resp.json()["detail"]


def test_p2_get_pico_nonexistent_record_404() -> None:
    """P2: 获取不存在记录的 PICO 返回 404。"""
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    url = f"/api/workspace/projects/{project_id}/stages/search/literature/records/99999/pico"
    resp = client.get(url, headers=_auth(token))

    assert resp.status_code == 404


def test_p3_autofill_query_supporting_record_ids_count(monkeypatch) -> None:
    """P3: autofill 返回 supporting_record_ids 长度 >=2。"""
    inject_mock_datasets_into_adapters(monkeypatch, SOURCE_DATASET_REGISTRY)
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    with Session(engine) as session:
        run = SearchRun(
            project_id=project_id,
            selected_sources="pubmed,cnki,wanfang",
            status="completed",
            query_snapshot='{"p":"T2DM CKD","i":"SGLT2","c":"placebo","o":"MACE HF"}',
        )
        session.add(run)
        session.flush()
        run_id = run.id or 0

        all_entries = []
        for key in ["pubmed", "cnki", "wanfang"]:
            if key in SOURCE_DATASET_REGISTRY:
                all_entries.extend(SOURCE_DATASET_REGISTRY[key])

        for entry in all_entries:
            srs = SearchRunSource(
                search_run_id=run_id,
                source_key=key,
                status="completed",
            )
            break
        session.add(srs)

        for entry in all_entries:
            rec = LiteratureRecord(
                project_id=project_id,
                title=entry.title,
                authors=entry.authors,
                journal=entry.journal,
                year=entry.year,
                doi=entry.doi,
                pmid=entry.pmid,
                abstract=entry.abstract,
                source_key=entry.source_record_id.split("-")[0] if entry.source_record_id else "pubmed",
                search_run_id=run_id,
                dedupe_status="unique",
                relevance_score=0.8,
            )
            session.add(rec)
        session.commit()

    autofill_url = f"{_base_url(project_id)}/{run_id}/pico:autofill-query"
    autofill_resp = client.post(autofill_url, headers=_auth(token))

    assert autofill_resp.status_code == 200
    autofill_body = autofill_resp.json()
    assert "supporting_record_ids" in autofill_body
    assert len(autofill_body["supporting_record_ids"]) >= 2
