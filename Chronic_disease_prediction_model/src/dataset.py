import numpy as np
import pandas as pd
from .schema import FeatureSchema


def build_sequence_dataset(
    df: pd.DataFrame,
    schema: FeatureSchema,
    sequence_days: int,
    horizon_days: int,
) -> tuple:
    df = df.copy()
    for col in schema.categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype("category").cat.codes.replace(-1, np.nan)
    df_sorted = df.sort_values([schema.id_col, schema.date_col])
    sequences = []
    labels = []
    dates = []
    ids = []
    for patient_id, group in df_sorted.groupby(schema.id_col):
        group = group.set_index(schema.date_col).sort_index()
        for current_date in group.index:
            window_start = current_date - pd.Timedelta(days=sequence_days - 1)
            history = group.loc[window_start:current_date]
            if len(history) < sequence_days:
                continue
            static_vals = (
                group.loc[current_date]
                .reindex(schema.static_cols)
                .apply(pd.to_numeric, errors="coerce")
                .values
            )
            dynamic_vals = (
                history.reindex(columns=schema.dynamic_cols)
                .apply(pd.to_numeric, errors="coerce")
                .values
            )
            static_repeated = np.repeat(static_vals.reshape(1, -1), sequence_days, axis=0)
            sequence = np.concatenate([static_repeated, dynamic_vals], axis=1)
            window_end = current_date + pd.Timedelta(days=horizon_days)
            future_window = group.loc[current_date:window_end]
            if schema.target_col in future_window.columns:
                label = int(future_window[schema.target_col].fillna(0).max() > 0)
            else:
                label = 0
            sequences.append(sequence)
            labels.append(label)
            dates.append(current_date)
            ids.append(patient_id)
    if len(sequences) == 0:
        return np.empty((0, sequence_days, len(schema.static_cols) + len(schema.dynamic_cols))), np.array([]), pd.DataFrame(
            {schema.id_col: [], schema.date_col: []}
        )
    return np.stack(sequences), np.array(labels), pd.DataFrame(
        {schema.id_col: ids, schema.date_col: dates}
    )


def build_sequence_dataset_multi(
    df: pd.DataFrame,
    schema: FeatureSchema,
    sequence_days: int,
    horizon_days: int,
    target_cols: list | None = None,
) -> tuple:
    if target_cols is None:
        target_cols = list(schema.target_cols)
    df = df.copy()
    for col in schema.categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype("category").cat.codes.replace(-1, np.nan)
    df_sorted = df.sort_values([schema.id_col, schema.date_col])
    sequences = []
    labels = []
    dates = []
    ids = []
    for patient_id, group in df_sorted.groupby(schema.id_col):
        group = group.set_index(schema.date_col).sort_index()
        for current_date in group.index:
            window_start = current_date - pd.Timedelta(days=sequence_days - 1)
            history = group.loc[window_start:current_date]
            if len(history) < sequence_days:
                continue
            static_vals = (
                group.loc[current_date]
                .reindex(schema.static_cols)
                .apply(pd.to_numeric, errors="coerce")
                .values
            )
            dynamic_vals = (
                history.reindex(columns=schema.dynamic_cols)
                .apply(pd.to_numeric, errors="coerce")
                .values
            )
            static_repeated = np.repeat(static_vals.reshape(1, -1), sequence_days, axis=0)
            sequence = np.concatenate([static_repeated, dynamic_vals], axis=1)
            window_end = current_date + pd.Timedelta(days=horizon_days)
            future_window = group.loc[current_date:window_end]
            label_vector = []
            for target in target_cols:
                if target in future_window.columns:
                    label = int(future_window[target].fillna(0).max() > 0)
                else:
                    label = 0
                label_vector.append(label)
            sequences.append(sequence)
            labels.append(label_vector)
            dates.append(current_date)
            ids.append(patient_id)
    if len(sequences) == 0:
        return (
            np.empty((0, sequence_days, len(schema.static_cols) + len(schema.dynamic_cols))),
            np.empty((0, len(target_cols))),
            pd.DataFrame({schema.id_col: [], schema.date_col: []}),
        )
    return np.stack(sequences), np.array(labels), pd.DataFrame(
        {schema.id_col: ids, schema.date_col: dates}
    )
