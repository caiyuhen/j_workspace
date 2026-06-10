import importlib.util
from io import BytesIO

from fastapi.testclient import TestClient


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_heic_returns_clear_conversion_hint():
    module = load_module("services/xray-analysis-service/src/main.py", "xray_service_format")
    client = TestClient(module.app)

    response = client.post(
        "/xray/analyze",
        files={"file": ("sample.HEIC", BytesIO(b"not-a-real-heic"), "image/heic")},
    )

    assert response.status_code == 422
    assert "HEIC" in response.json()["detail"]
    assert "PNG" in response.json()["detail"] or "JPG" in response.json()["detail"]
