from src.models.xgb_model import build_xgb_model


def test_xgb_model_build():
    model = build_xgb_model(seed=42)
    assert hasattr(model, "fit")
    assert hasattr(model, "predict_proba")
