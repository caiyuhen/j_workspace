import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_health_endpoint():
    module_path = Path("services/xray-analysis-service/src/main.py")
    module = load_module(str(module_path), "xray_service_main")
    client = TestClient(module.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "xray-analysis-service"
