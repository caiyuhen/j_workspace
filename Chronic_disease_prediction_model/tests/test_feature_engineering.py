import pandas as pd
from datetime import datetime, timedelta
from src.schema import FeatureSchema
from src.feature_engineering import build_rolling_features, align_features


def test_build_rolling_features():
    schema = FeatureSchema()
    base_date = datetime(2024, 1, 1)
    records = []
    for day in range(3):
        records.append(
            {
                schema.id_col: "P1",
                schema.date_col: base_date + timedelta(days=day),
                "age": 50,
                "gender": 1,
                "ethnicity": "Asian",
                "systolic_bp": 120 + day,
                "diastolic_bp": 80,
                "air_quality": 60,
                "season": 0,
            }
        )
    df = pd.DataFrame(records)
    features = build_rolling_features(df, schema, window_days=2)
    aligned = align_features(features, schema, window_days=2)
    assert aligned.shape[0] == 3
    assert any(col.endswith("mean_2d") for col in aligned.columns)
