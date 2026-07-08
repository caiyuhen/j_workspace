import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, brier_score_loss
from sklearn.linear_model import LinearRegression


def calibration_slope(y_true, y_prob):
    y_true = np.asarray(y_true).reshape(-1)
    y_prob = np.asarray(y_prob).reshape(-1)
    eps = 1e-6
    logit = np.log((y_prob + eps) / (1 - y_prob + eps)).reshape(-1, 1)
    model = LinearRegression()
    model.fit(logit, y_true)
    return float(model.coef_[0])


def evaluate_binary(y_true, y_prob, threshold=0.5):
    y_true = np.asarray(y_true).reshape(-1)
    y_prob = np.asarray(y_prob).reshape(-1)
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "auroc": float(roc_auc_score(y_true, y_prob)),
        "auprc": float(average_precision_score(y_true, y_prob)),
        "f1": float(f1_score(y_true, y_pred)),
        "brier": float(brier_score_loss(y_true, y_prob)),
        "calibration_slope": float(calibration_slope(y_true, y_prob)),
    }
