<<<<<<< HEAD
from unittest.mock import patch

from fastapi.testclient import TestClient

from audit_logging_service.app import app as audit_app
from data_validation_service.app import app as validation_app
from monitoring_service.app import app as monitoring_app
from patient_mgmt_service.app import app as patient_app
from project_config_service.app import app as project_app
from randomization_service.app import app as random_app
from security_service.app import app as security_app

audit_client = TestClient(audit_app)
validation_client = TestClient(validation_app)
monitoring_client = TestClient(monitoring_app)
patient_client = TestClient(patient_app)
project_client = TestClient(project_app)
random_client = TestClient(random_app)
security_client = TestClient(security_app)


def _dispatch(service_name: str, method: str, path: str, payload: dict | None = None):
    clients = {
        "audit_logging_service": audit_client,
        "data_validation_service": validation_client,
        "project_config_service": project_client,
        "randomization_service": random_client,
    }
    response = clients[service_name].request(method, path, json=payload)
    if response.status_code >= 400:
        body = response.json()
        raise RuntimeError(body.get("detail", str(body)))
    return response.json()


def setup_function() -> None:
    from ctms_common.db import get_connection

    with TestClient(audit_app), TestClient(project_app), TestClient(patient_app), TestClient(monitoring_app), TestClient(security_app):
        pass
    get_connection("audit_logging_service").execute("DELETE FROM audit_logs").connection.commit()
    get_connection("project_config_service").execute("DELETE FROM projects").connection.commit()
    get_connection("project_config_service").execute("DELETE FROM sites").connection.commit()
    get_connection("patient_mgmt_service").execute("DELETE FROM patients").connection.commit()
    get_connection("monitoring_service").execute("DELETE FROM risk_metrics").connection.commit()
    get_connection("security_service").execute("DELETE FROM user_roles").connection.commit()
    get_connection("security_service").execute("DELETE FROM security_audit").connection.commit()


def test_switch_off_assign_device_test() -> None:
    with patch("project_config_service.app.call_service", side_effect=_dispatch), patch(
        "randomization_service.app.call_service", side_effect=_dispatch
    ), patch("patient_mgmt_service.app.call_service", side_effect=_dispatch):
        project_id = project_client.post(
            "/projects", json={"name": "P1", "randomization_enabled": False, "protocol_reason": "Device Test"}
        ).json()["project_id"]
        data = patient_client.post(
            "/patients",
            json={
                "project_id": project_id,
                "name": "A",
                "age": 35,
                "severity": "medium",
                "operator_id": "INV-01",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-INV01",
                "mfa_verified": True,
            },
        ).json()
        assert data["assigned_group"] == "Device Test"


def test_switch_on_randomization_works() -> None:
    with patch("project_config_service.app.call_service", side_effect=_dispatch), patch(
        "randomization_service.app.call_service", side_effect=_dispatch
    ), patch("patient_mgmt_service.app.call_service", side_effect=_dispatch):
        project_id = project_client.post(
            "/projects", json={"name": "P2", "randomization_enabled": True, "protocol_reason": "Intervention"}
        ).json()["project_id"]
        data = patient_client.post(
            "/patients",
            json={
                "project_id": project_id,
                "name": "B",
                "age": 67,
                "severity": "high",
                "operator_id": "INV-02",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-INV02",
                "mfa_verified": True,
            },
        ).json()
        assert data["assigned_group"] in {"Treatment", "Control"}


def test_dynamic_switch_before_and_after_enrollment() -> None:
    with patch("project_config_service.app.call_service", side_effect=_dispatch), patch(
        "randomization_service.app.call_service", side_effect=_dispatch
    ), patch("patient_mgmt_service.app.call_service", side_effect=_dispatch):
        project_id = project_client.post(
            "/projects", json={"name": "P3", "randomization_enabled": True, "protocol_reason": "Intervention"}
        ).json()["project_id"]
        ok = project_client.put(
            f"/projects/{project_id}/randomization-switch",
            json={
                "enabled": False,
                "operator_id": "PM-01",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-PM01",
                "mfa_verified": True,
            },
        )
        assert ok.status_code == 200
        patient_client.post(
            "/patients",
            json={
                "project_id": project_id,
                "name": "C",
                "age": 29,
                "severity": "low",
                "operator_id": "INV-03",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-INV03",
                "mfa_verified": True,
            },
        )
        blocked = project_client.put(
            f"/projects/{project_id}/randomization-switch",
            json={
                "enabled": True,
                "operator_id": "PM-01",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-PM01",
                "mfa_verified": True,
            },
        )
        assert blocked.status_code == 400


def test_audit_fields() -> None:
    with patch("project_config_service.app.call_service", side_effect=_dispatch), patch(
        "randomization_service.app.call_service", side_effect=_dispatch
    ), patch("patient_mgmt_service.app.call_service", side_effect=_dispatch):
        project_id = project_client.post(
            "/projects", json={"name": "P4", "randomization_enabled": False, "protocol_reason": "Device Test"}
        ).json()["project_id"]
        patient_client.post(
            "/patients",
            json={
                "project_id": project_id,
                "name": "D",
                "age": 40,
                "severity": "medium",
                "operator_id": "INV-04",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-INV04",
                "mfa_verified": True,
            },
        )
        logs = audit_client.get("/audit").json()
        assert logs[0]["operator_ip"] == "127.0.0.1"
        assert logs[0]["timestamp"]


def test_other_modules() -> None:
    project_id = project_client.post(
        "/projects", json={"name": "P5", "randomization_enabled": True, "protocol_reason": "Intervention"}
    ).json()["project_id"]
    assert project_client.post("/sites", json={"project_id": project_id, "site_name": "S1", "planned_budget": 1000}).status_code == 200
    assert validation_client.post("/clean", json={"points": [{"id": 1, "value": None}, {"id": 2, "value": 20}]}).json()["anomaly_count"] == 1
    assert monitoring_client.post(
        "/risk/metrics", json={"project_id": project_id, "metric_name": "delay", "metric_value": 12, "threshold": 8}
    ).json()["breached"] is True
    assert security_client.post("/rbac/assign", json={"username": "u1", "role": "CRA", "permission_group": "monitor"}).json()["assigned"] is True
=======
from unittest.mock import patch

from fastapi.testclient import TestClient

from audit_logging_service.app import app as audit_app
from data_validation_service.app import app as validation_app
from monitoring_service.app import app as monitoring_app
from patient_mgmt_service.app import app as patient_app
from project_config_service.app import app as project_app
from randomization_service.app import app as random_app
from security_service.app import app as security_app

audit_client = TestClient(audit_app)
validation_client = TestClient(validation_app)
monitoring_client = TestClient(monitoring_app)
patient_client = TestClient(patient_app)
project_client = TestClient(project_app)
random_client = TestClient(random_app)
security_client = TestClient(security_app)


def _dispatch(service_name: str, method: str, path: str, payload: dict | None = None):
    clients = {
        "audit_logging_service": audit_client,
        "data_validation_service": validation_client,
        "project_config_service": project_client,
        "randomization_service": random_client,
    }
    response = clients[service_name].request(method, path, json=payload)
    if response.status_code >= 400:
        body = response.json()
        raise RuntimeError(body.get("detail", str(body)))
    return response.json()


def setup_function() -> None:
    from ctms_common.db import get_connection

    with TestClient(audit_app), TestClient(project_app), TestClient(patient_app), TestClient(monitoring_app), TestClient(security_app):
        pass
    get_connection("audit_logging_service").execute("DELETE FROM audit_logs").connection.commit()
    get_connection("project_config_service").execute("DELETE FROM projects").connection.commit()
    get_connection("project_config_service").execute("DELETE FROM sites").connection.commit()
    get_connection("patient_mgmt_service").execute("DELETE FROM patients").connection.commit()
    get_connection("monitoring_service").execute("DELETE FROM risk_metrics").connection.commit()
    get_connection("security_service").execute("DELETE FROM user_roles").connection.commit()
    get_connection("security_service").execute("DELETE FROM security_audit").connection.commit()


def test_switch_off_assign_device_test() -> None:
    with patch("project_config_service.app.call_service", side_effect=_dispatch), patch(
        "randomization_service.app.call_service", side_effect=_dispatch
    ), patch("patient_mgmt_service.app.call_service", side_effect=_dispatch):
        project_id = project_client.post(
            "/projects", json={"name": "P1", "randomization_enabled": False, "protocol_reason": "Device Test"}
        ).json()["project_id"]
        data = patient_client.post(
            "/patients",
            json={
                "project_id": project_id,
                "name": "A",
                "age": 35,
                "severity": "medium",
                "operator_id": "INV-01",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-INV01",
                "mfa_verified": True,
            },
        ).json()
        assert data["assigned_group"] == "Device Test"


def test_switch_on_randomization_works() -> None:
    with patch("project_config_service.app.call_service", side_effect=_dispatch), patch(
        "randomization_service.app.call_service", side_effect=_dispatch
    ), patch("patient_mgmt_service.app.call_service", side_effect=_dispatch):
        project_id = project_client.post(
            "/projects", json={"name": "P2", "randomization_enabled": True, "protocol_reason": "Intervention"}
        ).json()["project_id"]
        data = patient_client.post(
            "/patients",
            json={
                "project_id": project_id,
                "name": "B",
                "age": 67,
                "severity": "high",
                "operator_id": "INV-02",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-INV02",
                "mfa_verified": True,
            },
        ).json()
        assert data["assigned_group"] in {"Treatment", "Control"}


def test_dynamic_switch_before_and_after_enrollment() -> None:
    with patch("project_config_service.app.call_service", side_effect=_dispatch), patch(
        "randomization_service.app.call_service", side_effect=_dispatch
    ), patch("patient_mgmt_service.app.call_service", side_effect=_dispatch):
        project_id = project_client.post(
            "/projects", json={"name": "P3", "randomization_enabled": True, "protocol_reason": "Intervention"}
        ).json()["project_id"]
        ok = project_client.put(
            f"/projects/{project_id}/randomization-switch",
            json={
                "enabled": False,
                "operator_id": "PM-01",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-PM01",
                "mfa_verified": True,
            },
        )
        assert ok.status_code == 200
        patient_client.post(
            "/patients",
            json={
                "project_id": project_id,
                "name": "C",
                "age": 29,
                "severity": "low",
                "operator_id": "INV-03",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-INV03",
                "mfa_verified": True,
            },
        )
        blocked = project_client.put(
            f"/projects/{project_id}/randomization-switch",
            json={
                "enabled": True,
                "operator_id": "PM-01",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-PM01",
                "mfa_verified": True,
            },
        )
        assert blocked.status_code == 400


def test_audit_fields() -> None:
    with patch("project_config_service.app.call_service", side_effect=_dispatch), patch(
        "randomization_service.app.call_service", side_effect=_dispatch
    ), patch("patient_mgmt_service.app.call_service", side_effect=_dispatch):
        project_id = project_client.post(
            "/projects", json={"name": "P4", "randomization_enabled": False, "protocol_reason": "Device Test"}
        ).json()["project_id"]
        patient_client.post(
            "/patients",
            json={
                "project_id": project_id,
                "name": "D",
                "age": 40,
                "severity": "medium",
                "operator_id": "INV-04",
                "operator_ip": "127.0.0.1",
                "signature": "SIG-INV04",
                "mfa_verified": True,
            },
        )
        logs = audit_client.get("/audit").json()
        assert logs[0]["operator_ip"] == "127.0.0.1"
        assert logs[0]["timestamp"]


def test_other_modules() -> None:
    project_id = project_client.post(
        "/projects", json={"name": "P5", "randomization_enabled": True, "protocol_reason": "Intervention"}
    ).json()["project_id"]
    assert project_client.post("/sites", json={"project_id": project_id, "site_name": "S1", "planned_budget": 1000}).status_code == 200
    assert validation_client.post("/clean", json={"points": [{"id": 1, "value": None}, {"id": 2, "value": 20}]}).json()["anomaly_count"] == 1
    assert monitoring_client.post(
        "/risk/metrics", json={"project_id": project_id, "metric_name": "delay", "metric_value": 12, "threshold": 8}
    ).json()["breached"] is True
    assert security_client.post("/rbac/assign", json={"username": "u1", "role": "CRA", "permission_group": "monitor"}).json()["assigned"] is True
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
