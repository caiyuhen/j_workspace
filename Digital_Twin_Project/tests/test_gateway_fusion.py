import importlib.util


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_fuse_patient_states_marks_conflict_when_angles_diverge():
    module = load_module("services/report-gateway/src/main.py", "report_gateway_main_fusion")
    pdf_state = {
        "name": "张三",
        "data_source": "pdf",
        "metrics": {"cobb_angle": 10.0, "kyphosis_max": 40.0, "lordosis_max": 30.0},
        "curve_data": {"vertebral_rotation": [1.0] * 17, "coronal_offsets": [0.0] * 17, "sagittal_profile": [10.0] * 17},
    }
    xray_state = {
        "name": "张三",
        "data_source": "xray",
        "metrics": {"cobb_angle": 24.0, "kyphosis_max": 35.0, "lordosis_max": 28.0},
        "curve_data": {"vertebral_rotation": [2.0] * 17, "coronal_offsets": [5.0] * 17, "sagittal_profile": [12.0] * 17},
        "confidence": {"cobb_angle": 0.65},
    }

    result = module.fuse_patient_states(pdf_state, xray_state, explicit_name=None)

    assert result["data_source"] == "fused"
    assert result["review_required"] is True
    assert result["confidence"]["cobb_angle"] == 0.65
