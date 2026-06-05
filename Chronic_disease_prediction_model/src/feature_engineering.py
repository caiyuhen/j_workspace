import numpy as np
import pandas as pd
from .schema import FeatureSchema


def build_rolling_features(
    df: pd.DataFrame,
    schema: FeatureSchema,
    window_days: int,
) -> pd.DataFrame:
    df_sorted = df.sort_values([schema.id_col, schema.date_col])
    feature_rows = []
    for patient_id, group in df_sorted.groupby(schema.id_col):
        group = group.set_index(schema.date_col).sort_index()
        for current_date in group.index:
            window_start = current_date - pd.Timedelta(days=window_days - 1)
            window = group.loc[window_start:current_date]
            static_vals = group.loc[current_date].reindex(schema.static_cols)
            stats = {}
            for col in schema.dynamic_cols:
                if col in window.columns:
                    series = window[col].astype(float)
                    stats[f"{col}_mean_{window_days}d"] = series.mean()
                    stats[f"{col}_std_{window_days}d"] = series.std(ddof=0)
                    stats[f"{col}_min_{window_days}d"] = series.min()
                    stats[f"{col}_max_{window_days}d"] = series.max()
                    if len(series) > 1:
                        x = np.arange(len(series))
                        coef = np.polyfit(x, series.values, 1)[0]
                    else:
                        coef = 0.0
                    stats[f"{col}_trend_{window_days}d"] = coef
            row = {
                schema.id_col: patient_id,
                schema.date_col: current_date,
                **static_vals.to_dict(),
                **stats,
            }
            feature_rows.append(row)
    return pd.DataFrame(feature_rows)


def align_features(
    features: pd.DataFrame,
    schema: FeatureSchema,
    window_days: int,
) -> pd.DataFrame:
    required = [schema.id_col, schema.date_col] + list(schema.static_cols)
    dynamic = []
    for col in schema.dynamic_cols:
        dynamic.extend(
            [
                f"{col}_mean_{window_days}d",
                f"{col}_std_{window_days}d",
                f"{col}_min_{window_days}d",
                f"{col}_max_{window_days}d",
                f"{col}_trend_{window_days}d",
            ]
        )
    needed = required + dynamic
    for col in needed:
        if col not in features.columns:
            features[col] = np.nan
    return features[needed]
