from scripts.generate_synth_data import generate_synthetic_data
from src.schema import FeatureSchema
from src.training import train_transformer_pipeline, persist_transformer_artifacts
from src.inference import load_transformer_bundle, predict_transformer_risk


def test_transformer_pipeline(tmp_path):
    schema = FeatureSchema()
    df = generate_synthetic_data(patients=6, days=10, seed=17)
    artifacts = train_transformer_pipeline(df, schema, horizon_days=7, seed=17, target_cols=list(schema.target_cols))
    persist_transformer_artifacts(str(tmp_path), artifacts, horizon_days=7, suffix="A")
    bundle = load_transformer_bundle(str(tmp_path / "transformer_7d_A.pt"))
    patient_id = df[schema.id_col].iloc[0]
    latest = df[df[schema.id_col] == patient_id].sort_values(schema.date_col).tail(7)
    preds, _ = predict_transformer_risk(latest, schema, bundle, 7)
    assert preds.shape[0] >= 1
