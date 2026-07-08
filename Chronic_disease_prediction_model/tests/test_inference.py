import pandas as pd
from scripts.generate_synth_data import generate_synthetic_data
from src.schema import FeatureSchema
from src.training import train_xgb_pipeline
from src.inference import predict_risk


def test_inference_pipeline(tmp_path):
    schema = FeatureSchema()
    df = generate_synthetic_data(patients=10, days=10, seed=7)
    artifacts = train_xgb_pipeline(df, schema, horizon_days=7, seed=7)
    model_bundle = {
        "model": artifacts["model"],
        "calibrator": artifacts["calibrator"],
        "preprocess": artifacts["preprocess"],
        "feature_names": artifacts["feature_names"],
    }
    latest = df.sort_values(schema.date_col).tail(7)
    preds, top_factors = predict_risk(latest, schema, model_bundle, 7, top_k=3)
    assert preds.shape[0] >= 1
    assert len(top_factors) <= 3
