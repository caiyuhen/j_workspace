import numpy as np
from sklearn.linear_model import LogisticRegression
from src.models.calibration import fit_platt, fit_isotonic, apply_isotonic


def test_calibration_helpers():
    X = np.array([[0], [1], [2], [3]])
    y = np.array([0, 0, 1, 1])
    model = LogisticRegression().fit(X, y)
    calibrator = fit_platt(model, X, y)
    probs = calibrator.predict_proba(X)[:, 1]
    iso = fit_isotonic(probs, y)
    calibrated = apply_isotonic(iso, probs)
    assert calibrated.min() >= 0
    assert calibrated.max() <= 1
