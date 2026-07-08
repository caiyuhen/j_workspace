import pandas as pd
from datetime import datetime, timedelta
from src.schema import FeatureSchema
from src.labeling import generate_future_label


def test_generate_future_label():
    schema = FeatureSchema()
    base_date = datetime(2024, 1, 1)
    records = []
    for day in range(5):
        records.append(
            {
                schema.id_col: "P1",
                schema.date_col: base_date + timedelta(days=day),
                schema.target_col: 1 if day == 4 else 0,
            }
        )
    df = pd.DataFrame(records)
    labels = generate_future_label(df, schema, horizon_days=3)
    label_day0 = labels.iloc[0][f"label_3d"]
    label_day1 = labels.iloc[1][f"label_3d"]
    label_last = labels.iloc[-1][f"label_3d"]
    assert label_day0 == 0
    assert label_day1 == 1
    assert label_last == 1
