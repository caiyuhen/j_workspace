import os
import json
from typing import Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.calibration import CalibratedClassifierCV


def _select_feature_columns(df: pd.DataFrame, id_col: str, date_col: str, target_cols: List[str]) -> List[str]:
    drop_cols = set([id_col, date_col] + list(target_cols))
    return [c for c in df.columns if c not in drop_cols and np.issubdtype(df[c].dtype, np.number)]


def _train_binary_model(X: np.ndarray, y: np.ndarray, seed: int, class_weight: str = None) -> Pipeline:
    cw = "balanced" if class_weight == "class_weight" else None
    base = Pipeline(
        steps=[
            ("scaler", StandardScaler(with_mean=True, with_std=True)),
            ("clf", LogisticRegression(max_iter=300, random_state=seed, class_weight=cw, C=0.2, solver="liblinear")),
        ]
    )
    calib = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    calib.fit(X, y)
    return calib


def train_xgb_multi_pipeline(
    df: pd.DataFrame,
    schema,
    horizon_days: int,
    seed: int,
    target_cols: List[str],
    imbalance_strategy: str = "class_weight",
):
    feature_cols = _select_feature_columns(df, schema.id_col, schema.date_col, target_cols)
    feature_means = df[feature_cols].mean(numeric_only=True).to_dict()
    X = df[feature_cols].fillna(feature_means).fillna(0.0).values
    models: Dict[str, Pipeline] = {}
    metrics = {}
    positive_rate_stats = {}
    for i, target in enumerate(target_cols):
        y = df[target].values.astype(int)
        if y.max() == y.min():
            auc = 0.5
            model = _train_binary_model(X, y, seed + i, class_weight=imbalance_strategy)
        else:
            model = _train_binary_model(X, y, seed + i, class_weight=imbalance_strategy)
            try:
                proba = model.predict_proba(X)[:, 1]
                auc = float(roc_auc_score(y, proba))
            except Exception:
                auc = 0.5
        models[target] = model
        metrics[target] = {"train_auroc": auc, "samples": int(len(y)), "positive_rate": float(y.mean())}
        positive_rate_stats[target] = {"rows": int(len(y)), "positives": int(y.sum()), "positive_rate": float(y.mean())}
    artifacts = {
        "models": models,
        "feature_names": feature_cols,
        "metrics": metrics,
        "positive_rate_stats": positive_rate_stats,
        "horizon_days": horizon_days,
        "feature_means": feature_means,
        "type": "xgb_multi_mock",
    }
    return artifacts


def train_xgb_pipeline(df: pd.DataFrame, schema, horizon_days: int, seed: int, imbalance_strategy: str = "class_weight"):
    return {
        "model": None,
        "metrics": {"status": "skipped_mock"},
        "horizon_days": horizon_days,
        "type": "xgb_mock",
    }


def train_lstm_pipeline(df: pd.DataFrame, schema, horizon_days: int, seed: int):
    return {
        "model": None,
        "metrics": {"status": "skipped_mock"},
        "horizon_days": horizon_days,
        "type": "lstm_mock",
    }


def train_transformer_pipeline(df: pd.DataFrame, schema, horizon_days: int, seed: int, target_cols: List[str]):
    return {
        "model": None,
        "metrics": {"status": "skipped_mock"},
        "horizon_days": horizon_days,
        "type": "transformer_mock",
    }


def persist_artifacts(output_dir: str, artifacts: dict, horizon_days: int, suffix: str, risk_thresholds: dict):
    os.makedirs(output_dir, exist_ok=True)
    bundle = {"artifacts": {"type": artifacts.get("type", "xgb_mock")}, "thresholds": risk_thresholds}
    path = os.path.join(output_dir, f"xgb_{horizon_days}d_{suffix}.joblib")
    joblib.dump(bundle, path)


def persist_lstm_artifacts(output_dir: str, artifacts: dict, horizon_days: int, suffix: str):
    os.makedirs(output_dir, exist_ok=True)
    bundle = {"artifacts": {"type": artifacts.get("type", "lstm_mock")}}
    path = os.path.join(output_dir, f"lstm_{horizon_days}d_{suffix}.joblib")
    joblib.dump(bundle, path)


def persist_multi_artifacts(output_dir: str, artifacts: dict, horizon_days: int, suffix: str, risk_thresholds: dict):
    os.makedirs(output_dir, exist_ok=True)
    # Convert sklearn pipelines to bytes via joblib
    serializable = {
        "type": artifacts.get("type", "xgb_multi_mock"),
        "feature_names": artifacts.get("feature_names", []),
        "feature_means": artifacts.get("feature_means", {}),
        "horizon_days": artifacts.get("horizon_days", horizon_days),
        "models": artifacts.get("models", {}),
        "thresholds": risk_thresholds,
    }
    path = os.path.join(output_dir, f"xgb_multi_{horizon_days}d_{suffix}.joblib")
    joblib.dump(serializable, path)


def persist_transformer_artifacts(output_dir: str, artifacts: dict, horizon_days: int, suffix: str, risk_thresholds: dict):
    os.makedirs(output_dir, exist_ok=True)
    bundle = {"artifacts": {"type": artifacts.get("type", "transformer_mock")}, "thresholds": risk_thresholds}
    path = os.path.join(output_dir, f"transformer_{horizon_days}d_{suffix}.pt")
    joblib.dump(bundle, path)
