import numpy as np


def ks_2samp_statistic(expected, actual):
    expected = np.sort(np.asarray(expected).reshape(-1))
    actual = np.sort(np.asarray(actual).reshape(-1))
    if len(expected) == 0 or len(actual) == 0:
        return {"ks_stat": 0.0, "p_value": 1.0}
    values = np.unique(np.concatenate([expected, actual]))
    cdf_expected = np.searchsorted(expected, values, side="right") / len(expected)
    cdf_actual = np.searchsorted(actual, values, side="right") / len(actual)
    ks_stat = float(np.max(np.abs(cdf_expected - cdf_actual)))
    n1 = len(expected)
    n2 = len(actual)
    en = np.sqrt((n1 * n2) / (n1 + n2))
    if en == 0:
        return {"ks_stat": ks_stat, "p_value": 1.0}
    lam = (en + 0.12 + 0.11 / en) * ks_stat
    series = [(-1) ** (k - 1) * np.exp(-2 * (k**2) * (lam**2)) for k in range(1, 6)]
    p_value = float(np.clip(2 * np.sum(series), 0.0, 1.0))
    return {"ks_stat": ks_stat, "p_value": p_value}


def psi(expected, actual, buckets=10):
    expected = np.asarray(expected).reshape(-1)
    actual = np.asarray(actual).reshape(-1)
    quantiles = np.linspace(0, 1, buckets + 1)
    breakpoints = np.quantile(expected, quantiles)
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf
    expected_counts = np.histogram(expected, bins=breakpoints)[0]
    actual_counts = np.histogram(actual, bins=breakpoints)[0]
    expected_perc = expected_counts / max(len(expected), 1)
    actual_perc = actual_counts / max(len(actual), 1)
    psi_values = (actual_perc - expected_perc) * np.log(
        (actual_perc + 1e-6) / (expected_perc + 1e-6)
    )
    return float(np.sum(psi_values))


def detect_drift(expected, actual, threshold=0.1):
    score = psi(expected, actual)
    ks_result = ks_2samp_statistic(expected, actual)
    alert = bool(score > threshold or ks_result["ks_stat"] > threshold)
    return {"psi": score, "ks_stat": ks_result["ks_stat"], "ks_p_value": ks_result["p_value"], "alert": alert}


def compare_feature_distributions(expected_df, actual_df, feature_cols, threshold=0.1):
    result = {}
    for col in feature_cols:
        expected = np.asarray(expected_df[col]).reshape(-1)
        actual = np.asarray(actual_df[col]).reshape(-1)
        psi_score = psi(expected, actual)
        ks_result = ks_2samp_statistic(expected, actual)
        expected_mean = float(np.mean(expected)) if len(expected) else 0.0
        actual_mean = float(np.mean(actual)) if len(actual) else 0.0
        expected_std = float(np.std(expected)) if len(expected) else 0.0
        actual_std = float(np.std(actual)) if len(actual) else 0.0
        mean_shift = abs(actual_mean - expected_mean) / (abs(expected_mean) + 1e-6)
        std_shift = abs(actual_std - expected_std) / (abs(expected_std) + 1e-6)
        alert = bool(psi_score > threshold or ks_result["ks_stat"] > threshold or mean_shift > threshold)
        result[col] = {
            "psi": float(psi_score),
            "ks_stat": float(ks_result["ks_stat"]),
            "ks_p_value": float(ks_result["p_value"]),
            "mean_shift_ratio": float(mean_shift),
            "std_shift_ratio": float(std_shift),
            "alert": alert,
        }
    return result


def should_rollback(current_auroc, baseline_auroc, drop=0.03):
    return bool(baseline_auroc - current_auroc >= drop)
