from scripts.generate_synth_data import generate_synthetic_data
from src.schema import FeatureSchema
from src.dataset import build_sequence_dataset


def test_build_sequence_dataset():
    schema = FeatureSchema()
    df = generate_synthetic_data(patients=3, days=8, seed=5)
    sequences, labels, meta = build_sequence_dataset(df, schema, sequence_days=7, horizon_days=7)
    assert sequences.shape[1] == 7
    assert sequences.shape[2] == len(schema.static_cols) + len(schema.dynamic_cols)
    assert len(labels) == len(meta)
