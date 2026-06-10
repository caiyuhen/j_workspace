import importlib.util
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_xray_analyze_endpoint_accepts_png(tmp_path: Path):
    module = load_module("services/xray-analysis-service/src/main.py", "xray_service_main_endpoint")
    client = TestClient(module.app)

    image_path = tmp_path / "spine.png"
    Image.new("L", (100, 200), color=128).save(image_path)

    response = client.post(
        "/xray/analyze",
        files={"file": ("spine.png", image_path.read_bytes(), "image/png")},
        data={"patient_name": "接口患者"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["patient_state"]["name"] == "接口患者"
