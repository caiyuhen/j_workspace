import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from .schema import FeatureSchema


def apply_range_clipping(df: pd.DataFrame, schema: FeatureSchema) -> pd.DataFrame:
    clipped = df.copy()
    for col, bounds in schema.ranges.items():
        if col in clipped.columns:
            low, high = bounds
            clipped[col] = clipped[col].clip(lower=low, upper=high)
    return clipped


def build_preprocess_pipeline(
    schema: FeatureSchema, feature_columns: list | None = None
) -> ColumnTransformer:
    if feature_columns is None:
        feature_columns = list(schema.static_cols + schema.dynamic_cols)
    categorical_cols = [col for col in schema.categorical_cols if col in feature_columns]
    numeric_cols = [col for col in feature_columns if col not in categorical_cols]
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ],
        remainder="drop",
    )


def ensure_datetime(df: pd.DataFrame, schema: FeatureSchema) -> pd.DataFrame:
    converted = df.copy()
    converted[schema.date_col] = pd.to_datetime(converted[schema.date_col])
    return converted
