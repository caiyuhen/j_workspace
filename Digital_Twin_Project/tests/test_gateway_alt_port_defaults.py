import importlib.util


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_gateway_defaults_to_alt_ports_when_env_missing(monkeypatch):
    for key in (
        "PATIENT_SERVICE_URL",
        "SIMULATION_SERVICE_URL",
        "VISUALIZATION_SERVICE_URL",
        "OCR_SERVICE_URL",
        "XRAY_SERVICE_URL",
    ):
        monkeypatch.delenv(key, raising=False)

    module = load_module("services/report-gateway/src/main.py", "report_gateway_alt_defaults")

    assert module.PATIENT_SERVICE_URL == "http://127.0.0.1:9003"
    assert module.SIMULATION_SERVICE_URL == "http://127.0.0.1:9001"
    assert module.VISUALIZATION_SERVICE_URL == "http://127.0.0.1:9002"
    assert module.OCR_SERVICE_URL == "http://127.0.0.1:9004"
    assert module.XRAY_SERVICE_URL == "http://127.0.0.1:9005"
