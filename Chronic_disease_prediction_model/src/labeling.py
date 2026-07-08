import pandas as pd
from .schema import FeatureSchema


def generate_future_label(
    df: pd.DataFrame,
    schema: FeatureSchema,
    horizon_days: int,
) -> pd.DataFrame:
    df_sorted = df.sort_values([schema.id_col, schema.date_col])
    labels = []
    for patient_id, group in df_sorted.groupby(schema.id_col):
        group = group.set_index(schema.date_col).sort_index()
        for current_date in group.index:
            window_end = current_date + pd.Timedelta(days=horizon_days)
            future_window = group.loc[current_date:window_end]
            if schema.target_col in future_window.columns:
                label = int(future_window[schema.target_col].fillna(0).max() > 0)
            else:
                label = 0
            labels.append(
                {
                    schema.id_col: patient_id,
                    schema.date_col: current_date,
                    f"label_{horizon_days}d": label,
                }
            )
    return pd.DataFrame(labels)


def generate_future_labels(
    df: pd.DataFrame,
    schema: FeatureSchema,
    horizon_days: int,
    target_cols: list | None = None,
) -> pd.DataFrame:
    if target_cols is None:
        target_cols = list(schema.target_cols)
    df_sorted = df.sort_values([schema.id_col, schema.date_col])
    label_rows = []
    for patient_id, group in df_sorted.groupby(schema.id_col):
        group = group.set_index(schema.date_col).sort_index()
        for current_date in group.index:
            window_end = current_date + pd.Timedelta(days=horizon_days)
            future_window = group.loc[current_date:window_end]
            row = {schema.id_col: patient_id, schema.date_col: current_date}
            for target in target_cols:
                if target in future_window.columns:
                    label = int(future_window[target].fillna(0).max() > 0)
                else:
                    label = 0
                row[f"label_{target}_{horizon_days}d"] = label
            label_rows.append(row)
    return pd.DataFrame(label_rows)
