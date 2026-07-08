import pandas as pd
from src.monitoring import psi, ks_2samp_statistic, detect_drift, compare_feature_distributions, should_rollback


def test_psi_and_drift():
    expected = [0.1, 0.2, 0.3, 0.4]
    actual = [0.9, 0.8, 0.7, 0.6]
    score = psi(expected, actual)
    ks = ks_2samp_statistic(expected, actual)
    drift = detect_drift(expected, actual, threshold=0.1)
    assert score >= 0
    assert ks["ks_stat"] >= 0
    assert drift["alert"] is True


def test_feature_distribution_compare():
    baseline = pd.DataFrame({"f1": [1, 2, 3, 4], "f2": [10, 20, 30, 40]})
    current = pd.DataFrame({"f1": [1, 2, 3, 4], "f2": [40, 50, 60, 70]})
    result = compare_feature_distributions(baseline, current, ["f1", "f2"], threshold=0.1)
    assert "f1" in result
    assert "f2" in result
    assert result["f2"]["alert"] is True


def test_rollback():
    assert should_rollback(0.7, 0.8, drop=0.05) is True
