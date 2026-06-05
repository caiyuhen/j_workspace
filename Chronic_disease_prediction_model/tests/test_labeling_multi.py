from datetime import datetime, timedelta
import pandas as pd
from src.schema import FeatureSchema
from src.labeling import generate_future_labels


def test_generate_future_labels():
    schema = FeatureSchema()
    base_date = datetime(2024, 1, 1)
    records = []
    for day in range(4):
        records.append(
            {
                schema.id_col: "P1",
                schema.date_col: base_date + timedelta(days=day),
                "stroke": 1 if day == 3 else 0,
                "diabetes": 1 if day >= 2 else 0,
            }
        )
    df = pd.DataFrame(records)
    labels = generate_future_labels(df, schema, horizon_days=2, target_cols=["stroke", "diabetes"])
    assert f"label_stroke_2d" in labels.columns
    assert f"label_diabetes_2d" in labels.columns
