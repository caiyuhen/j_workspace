from src.inference import risk_level


def test_risk_level():
    assert risk_level(0.1) == "低风险"
    assert risk_level(0.3) == "中风险"
    assert risk_level(0.45) == "高风险"
    assert risk_level(0.6) == "极高风险"
    assert risk_level(0.2, (0.2, 0.4, 0.7)) == "中风险"
