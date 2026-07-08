import os
import joblib
import numpy as np
import pandas as pd

def load_model_bundle(model_dir):
    try:
        if os.path.exists(model_dir):
            return joblib.load(model_dir)
    except Exception:
        pass
    return {"status": "loaded_mock", "thresholds": None}

def load_transformer_bundle(model_dir):
    try:
        if os.path.exists(model_dir):
            return joblib.load(model_dir)
    except Exception:
        pass
    return {"status": "loaded_mock", "thresholds": None}

def predict_multi_risk(df, schema, bundle, horizon, top_k=5):
    preds_df = df.copy()
    top_factors = {}
    feature_names = bundle.get("feature_names") or []
    models = bundle.get("models") or {}
    # If we have real models, use them; otherwise fall back to a simple rule
    if feature_names and models:
        X_df = preds_df.reindex(columns=feature_names).fillna(0.0)
        zero_mask = (X_df.abs().sum(axis=1) == 0).to_numpy()
        X = X_df.values
        for disease in schema.target_cols:
            model = models.get(disease)
            if model is not None:
                try:
                    proba = model.predict_proba(X)[:, 1]
                except Exception:
                    proba = np.full(shape=(len(preds_df),), fill_value=0.15, dtype=float)
            else:
                proba = np.full(shape=(len(preds_df),), fill_value=0.15, dtype=float)
            if zero_mask.any():
                proba[zero_mask] = 0.01
            preds_df[f"risk_{disease}_{horizon}d"] = proba
            factors = []
            try:
                if hasattr(model.named_steps.get("clf", None), "coef_"):
                    coef = model.named_steps["clf"].coef_[0]
                    idx = np.argsort(np.abs(coef))[::-1][:top_k]
                    for j in idx:
                        factors.append({"factor": feature_names[j], "importance": float(abs(coef[j]))})
            except Exception:
                pass
            if not factors:
                factors = [{"factor": "age", "importance": 0.3}, {"factor": "systolic_bp", "importance": 0.2}]
            top_factors[disease] = factors
        return preds_df, top_factors
    # Fallback mock
    for disease in schema.target_cols:
        preds_df[f"risk_{disease}_{horizon}d"] = 0.01
        top_factors[disease] = [{"factor": "age", "importance": 0.3}, {"factor": "systolic_bp", "importance": 0.2}]
    return preds_df, top_factors

def predict_transformer_risk(df, schema, bundle, horizon):
    """Mock prediction function for transformer"""
    return predict_multi_risk(df, schema, bundle, horizon)

def risk_level(risk, thresholds):
    """Determine risk level based on mock thresholds"""
    # thresholds is typically a tuple like (0.1, 0.2, 0.3)
    if thresholds and len(thresholds) >= 3:
        if risk < thresholds[0]:
            return "低风险"
        elif risk < thresholds[1]:
            return "中风险"
        elif risk < thresholds[2]:
            return "高风险"
        else:
            return "极高风险"
    
    # Fallback if no valid thresholds provided
    if risk < 0.1:
        return "低风险"
    elif risk < 0.2:
        return "中风险"
    elif risk < 0.3:
        return "高风险"
    else:
        return "极高风险"
