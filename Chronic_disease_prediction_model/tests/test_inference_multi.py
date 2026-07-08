from scripts.generate_synth_data import generate_synthetic_data
from src.schema import FeatureSchema
from src.training import train_xgb_multi_pipeline
from src.inference import predict_multi_risk


def test_inference_multi_pipeline():
    schema = FeatureSchema()
    df = generate_synthetic_data(patients=8, days=10, seed=13)
    artifacts = train_xgb_multi_pipeline(
        df,
        schema,
        horizon_days=7,
        seed=13,
        target_cols=list(schema.target_cols),
        imbalance_strategy="class_weight",
    )
    model_bundle = {
        "models": artifacts["models"],
        "calibrators": artifacts["calibrators"],
        "preprocess": artifacts["preprocess"],
        "feature_names": artifacts["feature_names"],
    }
    latest = df.sort_values(schema.date_col).tail(7)
    preds, top_factors = predict_multi_risk(latest, schema, model_bundle, 7, top_k=3)
    assert preds.shape[0] >= 1
    assert "stroke" in top_factors
    assert "positive_rate_stats" in artifacts
    assert "stroke" in artifacts["positive_rate_stats"]
