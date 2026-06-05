from scripts.generate_synth_data import generate_synthetic_data
from src.schema import FeatureSchema
from src.training import train_xgb_pipeline, persist_artifacts
from src.inference import load_model_bundle


def test_training_persist(tmp_path):
    schema = FeatureSchema()
    df = generate_synthetic_data(patients=6, days=9, seed=11)
    df.loc[df.index[:5], schema.target_col] = 1
    artifacts = train_xgb_pipeline(df, schema, horizon_days=7, seed=11)
    persist_artifacts(str(tmp_path), artifacts, horizon_days=7, suffix="A", risk_thresholds=schema.risk_thresholds)
    bundle = load_model_bundle(str(tmp_path / "xgb_7d_A.joblib"))
    assert "model" in bundle
    assert "calibrator" in bundle
    assert "thresholds" in bundle
    assert "label_stats" in artifacts
    assert artifacts["imbalance_strategy"] == "class_weight"
