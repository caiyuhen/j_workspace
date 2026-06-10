import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_workflow_endpoint_rejects_missing_pdf_for_pdf_only():
    module = load_module("services/report-gateway/src/main.py", "report_gateway_main_contract")
    client = TestClient(module.app)

    response = client.post(
        "/workflow/analyze",
        data={
            "workflow_type": "pdf_only",
            "duration": "24",
            "compliance": "0.9",
            "treatment_type": "Brace",
        },
    )

    assert response.status_code == 400
