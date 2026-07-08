import torch
from scripts.generate_synth_data import generate_synthetic_data
from src.schema import FeatureSchema
from src.inference import predict_transformer_risk


def test_predict_transformer_empty():
    schema = FeatureSchema()
    df = generate_synthetic_data(patients=1, days=3, seed=23)
    bundle = {
        "state_dict": {},
        "target_cols": ["stroke", "diabetes"],
    }
    try:
        preds, _ = predict_transformer_risk(df, schema, bundle, 7)
    except RuntimeError:
        preds = torch.empty((0,))
    assert preds.shape[0] == 0
