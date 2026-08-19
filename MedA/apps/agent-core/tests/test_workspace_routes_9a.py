"""Wave9a T5 Routes 2 tests (append-only).

- test_funnel_stats_success (POST /api/workspace/screening/funnel-stats → stats contain N4/E1/E6 counts)
- test_evidence_decide_TA_exclude_6_reject_422 (stage=screening_ta + exclude_reason_ids=[6] → HTTP 422)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _dev_login_and_create_project(client: TestClient) -> tuple[str, int]:
    login_resp = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "meda-wave9a",
            "organization_name": "MedA W9a Unit",
            "user_id": "u-w9a-001",
            "display_name": "W9a Reviewer",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    if login_resp.status_code not in (200, 201):
        login_resp = client.post(
            "/api/auth/dev-login",
            json={
                "organization_slug": "demo-hospital",
                "organization_name": "Demo Hospital",
                "user_id": "u-w9a-002",
                "display_name": "W9a Reviewer 2",
                "role": "org_admin",
                "client_type": "web",
            },
        )
    assert login_resp.status_code in (200, 201), f"login failed: {login_resp.status_code} {login_resp.text}"
    token = login_resp.json()["token"]

    proj_resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": login_resp.json().get("organization_slug") or "meda-wave9a",
            "owner_user_id": "u-w9a-001",
            "name": "Wave9a Funnel Routes Project",
            "description": "pytest routes 9a verify",
        },
    )
    if proj_resp.status_code in (200, 201):
        project_id = proj_resp.json()["id"]
    else:
        list_resp = client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200, f"list projects failed: {list_resp.status_code}"
        items = list_resp.json() or []
        assert items, "no projects found for user"
        project_id = items[0]["id"]

    return token, int(project_id)


class TestW9aWorkspaceRoutes:
    def test_funnel_stats_success(self):
        """S1: POST /screening/funnel-stats returns stats array with N4/E1/E6 keys and count > 0."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/screening/funnel-stats",
            headers={"Authorization": f"Bearer {token}"},
            json={"pi_id": pid, "n3_override": 1000, "n4_dupes_removed_override": 140},
        )

        assert resp.status_code == 200, f"funnel-stats non-200: {resp.status_code} {resp.text}"
        body = resp.json()

        assert "stats" in body, f"body missing 'stats' key: {list(body.keys())}"
        stats = body["stats"]
        assert isinstance(stats, list), "stats should be a list"
        assert len(stats) >= 6, f"stats len expected >=6: {len(stats)}"

        by_key = {s["key"]: s for s in stats if isinstance(s, dict) and "key" in s}
        for required_key in ("N4", "E1", "E6"):
            assert required_key in by_key, f"stats missing key {required_key}: {list(by_key.keys())}"
            cnt = by_key[required_key]["count"]
            assert isinstance(cnt, int), f"{required_key}.count not int: {type(cnt)}"
            assert cnt >= 0, f"{required_key}.count negative: {cnt}"

        if by_key["N1"]["count"] > 0:
            assert by_key["N4"]["count"] <= by_key["N3"]["count"], "N4 must be <= N3"
            assert by_key["E1"]["count"] == by_key["N4"]["count"], "E1 must equal N4 per funnel spec"

    def test_evidence_decide_TA_exclude_6_reject_422(self):
        """S2: stage=screening_ta + exclude_reason_ids=[6] → HTTP 422 (ta_allowed=False for id=6)."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/evidence-artifact/decide",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pi_id": pid,
                "record_ids": [6],
                "stage": "screening_ta",
                "decision": "exclude",
                "exclude_reason_ids": [6],
            },
        )

        assert resp.status_code == 422, (
            f"expected HTTP 422 (ta_allowed=False for id=6 in TA stage); "
            f"got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert isinstance(detail, str), f"detail not a string: {type(detail)} {detail}"
        assert (
            "ta_allowed=False" in detail
            or "exclude_reason_id=6" in detail
            or "screening_ta" in detail
        ), f"422 detail missing expected keywords: {detail!r}"
