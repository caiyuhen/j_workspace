from scripts.generate_synth_data import generate_synthetic_data
from src.schema import FeatureSchema
from src.dataset import build_sequence_dataset_multi


def test_build_sequence_dataset_multi_empty():
    schema = FeatureSchema()
    df = generate_synthetic_data(patients=2, days=3, seed=19)
    sequences, labels, meta = build_sequence_dataset_multi(
        df, schema, sequence_days=7, horizon_days=7, target_cols=["stroke", "diabetes"]
    )
    assert sequences.shape[0] == 0
    assert labels.shape[0] == 0
    assert meta.shape[0] == 0
