from scripts.generate_synth_data import generate_synthetic_data
from src.schema import FeatureSchema
from src.training import train_lstm_pipeline, persist_lstm_artifacts


def test_train_lstm_pipeline(tmp_path):
    schema = FeatureSchema()
    df = generate_synthetic_data(patients=4, days=10, seed=9)
    artifacts = train_lstm_pipeline(df, schema, horizon_days=7, seed=9)
    persist_lstm_artifacts(str(tmp_path), artifacts, horizon_days=7, suffix="A")
    assert (tmp_path / "lstm_7d_A.pt").exists()
    assert (tmp_path / "lstm_7d_A_calibrator.joblib").exists()
