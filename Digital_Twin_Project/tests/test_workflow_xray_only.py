import importlib.util
from io import BytesIO

from fastapi.testclient import TestClient


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_xray_only_workflow_returns_unified_response(monkeypatch):
    module = load_module("services/report-gateway/src/main.py", "report_gateway_main_xray_only")
    client = TestClient(module.app)

    async def fake_call_xray_service(client_obj, upload, patient_name):
        return {
            "status": "success",
            "patient_state": {
                "name": patient_name or "X患者",
                "data_source": "xray",
                "metrics": {"cobb_angle": 22.0, "kyphosis_max": 35.0, "lordosis_max": 30.0},
                "curve_data": {"vertebral_rotation": [1.0] * 17, "coronal_offsets": [2.0] * 17, "sagittal_profile": [9.0] * 17},
                "confidence": {"cobb_angle": 0.65},
                "review_required": False,
            },
        }

    async def fake_run_pipeline(client_obj, workflow_type, patient_state, treatment_plan):
        return {
            "workflow_type": workflow_type,
            "patient_state": patient_state,
            "simulation_id": "sim-1",
            "evolution_chart_json": {"data": [], "layout": {}},
            "comparison_data": {},
            "summary": "已完成 xray_only 工作流分析",
            "review_required": False,
        }

    monkeypatch.setattr(module, "call_xray_service", fake_call_xray_service)
    monkeypatch.setattr(module, "run_pipeline_from_patient_state", fake_run_pipeline)

    response = client.post(
        "/workflow/analyze",
        data={"workflow_type": "xray_only", "treatment_type": "Brace", "duration": "24", "compliance": "0.9"},
        files={"xray_file": ("xray.png", BytesIO(b"fake"), "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["workflow_type"] == "xray_only"
