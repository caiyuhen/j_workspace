import numpy as np
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression


def fit_platt(model, X_train, y_train, cv: int = 3):
    y_train = np.asarray(y_train)
    classes, counts = np.unique(y_train, return_counts=True)
    min_count = int(counts.min()) if len(counts) > 0 else 0
    if min_count < 2:
        return model
    cv = min(cv, min_count)
    calibrator = CalibratedClassifierCV(model, method="sigmoid", cv=cv)
    calibrator.fit(X_train, y_train)
    return calibrator


def fit_isotonic(probs, y_val):
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(probs, y_val)
    return calibrator


def apply_isotonic(calibrator, probs):
    probs = np.asarray(probs).reshape(-1)
    return calibrator.predict(probs)
