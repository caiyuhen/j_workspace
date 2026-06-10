import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_analyze_png_returns_quality_and_analysis_meta(tmp_path: Path):
    module = load_module("services/xray-analysis-service/src/analyzer.py", "xray_analyzer_enhanced")
    image_path = tmp_path / "coronal_spine.png"

    canvas = np.zeros((240, 120), dtype=np.uint8)
    for y in range(20, 220):
        x = int(60 + 15 * np.sin((y - 20) / 30.0))
        canvas[y, max(0, x - 2) : min(120, x + 3)] = 220
    Image.fromarray(canvas).save(image_path)

    result = module.XRayAnalyzer().analyze(image_path, patient_name="增强患者")

    assert result["status"] == "success"
    state = result["patient_state"]
    assert state["image_quality_score"] > 0
    assert state["analysis_meta"]["foreground_detected"] is True
    assert state["analysis_meta"]["centerline_points"] >= 10
    assert state["analysis_meta"]["view_hint"] == "coronal"
