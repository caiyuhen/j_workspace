import importlib.util


def load_module(module_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_fused_state_keeps_analysis_meta_from_xray():
    module = load_module("services/report-gateway/src/main.py", "report_gateway_meta")
    pdf_state = {
        "name": "测试患者",
        "data_source": "pdf",
        "metrics": {"cobb_angle": 12.0, "kyphosis_max": 40.0, "lordosis_max": 30.0},
        "curve_data": {
            "vertebral_rotation": [1.0] * 17,
            "coronal_offsets": [0.0] * 17,
            "sagittal_profile": [10.0] * 17,
        },
    }
    xray_state = {
        "name": "测试患者",
        "data_source": "xray",
        "metrics": {"cobb_angle": 20.0, "kyphosis_max": 36.0, "lordosis_max": 28.0},
        "curve_data": {
            "vertebral_rotation": [1.5] * 17,
            "coronal_offsets": [2.0] * 17,
            "sagittal_profile": [9.0] * 17,
        },
        "confidence": {"cobb_angle": 0.7},
        "image_quality_score": 0.81,
        "analysis_meta": {"view_hint": "coronal", "centerline_points": 17, "foreground_detected": True},
    }

    fused = module.fuse_patient_states(pdf_state, xray_state, explicit_name=None)

    assert fused["image_quality_score"] == 0.81
    assert fused["analysis_meta"]["view_hint"] == "coronal"
