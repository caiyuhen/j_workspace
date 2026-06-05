from src.evaluation import evaluate_binary


def test_evaluate_binary():
    y_true = [0, 1, 0, 1]
    y_prob = [0.1, 0.9, 0.2, 0.8]
    metrics = evaluate_binary(y_true, y_prob)
    assert metrics["auroc"] >= 0.9
    assert metrics["auprc"] >= 0.9
    assert metrics["f1"] >= 0.9
