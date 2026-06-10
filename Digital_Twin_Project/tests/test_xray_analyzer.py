import importlib.util
from pathlib import Path

from PIL import Image


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_analyze_png_returns_patient_state(tmp_path: Path):
    module = load_module("services/xray-analysis-service/src/analyzer.py", "xray_analyzer")
    image_path = tmp_path / "spine.png"
    Image.new("L", (120, 240), color=128).save(image_path)

    result = module.XRayAnalyzer().analyze(image_path, patient_name="测试患者")

    assert result["status"] == "success"
    assert result["patient_state"]["name"] == "测试患者"
    assert result["patient_state"]["data_source"] == "xray"
    assert "cobb_angle" in result["patient_state"]["metrics"]
    assert "vertebral_rotation" in result["patient_state"]["curve_data"]
