import pandas as pd
from src.schema import FeatureSchema
from src.preprocessing import apply_range_clipping, build_preprocess_pipeline


def test_apply_range_clipping():
    schema = FeatureSchema()
    df = pd.DataFrame(
        {
            "systolic_bp": [50, 250],
            "diastolic_bp": [30, 140],
            "age": [-5, 150],
        }
    )
    clipped = apply_range_clipping(df, schema)
    assert clipped["systolic_bp"].min() >= 80
    assert clipped["systolic_bp"].max() <= 220
    assert clipped["diastolic_bp"].min() >= 40
    assert clipped["diastolic_bp"].max() <= 130
    assert clipped["age"].min() >= 0
    assert clipped["age"].max() <= 120


def test_preprocess_pipeline_fit():
    schema = FeatureSchema()
    df = pd.DataFrame(
        {
            "age": [40, 50],
            "gender": [0, 1],
            "ethnicity": ["Asian", "White"],
            "systolic_bp": [120, 130],
            "diastolic_bp": [80, 85],
            "air_quality": [50, 60],
            "season": [0, 1],
        }
    )
    pipeline = build_preprocess_pipeline(schema, feature_columns=df.columns.tolist())
    transformed = pipeline.fit_transform(df)
    assert transformed.shape[0] == 2
