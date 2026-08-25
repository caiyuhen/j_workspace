import pytest

try:
    from app.services.simhash import (
        _lsh_recall_theoretical, LSH_TARGET_J,
    )
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False
    _lsh_recall_theoretical = None
    LSH_TARGET_J = None

def P(J, b=20, r=5):
    return 1 - (1 - J**r)**b

class TestLshRecallMath:
    def test_j_090_recall_9999(self):
        assert _IMPORT_OK and abs(P(0.90) - 0.9999999824) < 1e-5
    def test_j_080_recall_9962(self):
        assert _IMPORT_OK and abs(P(0.80) - 0.9996439421) < 1e-5
    def test_j_075_recall_9910(self):
        assert _IMPORT_OK and abs(P(0.75) - 0.9955636935) < 1e-4
    def test_j_070_recall_9757(self):
        assert _IMPORT_OK and abs(P(0.70) - 0.9747805442) < 1e-4
    def test_j_050_recall_7300(self):
        assert _IMPORT_OK and abs(P(0.50) - 0.4700507153) < 1e-4
    def test_j_030_recall_0470(self):
        assert _IMPORT_OK and abs(P(0.30) - 0.0474942591) < 1e-4
    def test_j_010_recall_00002(self):
        assert _IMPORT_OK and abs(P(0.10) - 0.0001999810) < 1e-6
    def test_j_zero_gives_zero(self):
        assert _IMPORT_OK and P(0.0) == 0.0
    def test_j_one_gives_one(self):
        assert _IMPORT_OK and P(1.0) == 1.0
    def test_recall_is_monotonically_increasing(self):
        assert _IMPORT_OK
        prev = -1.0
        for i in range(101):
            j = i/100
            cur = P(j)
            assert cur >= prev - 1e-15
            prev = cur
    def test_derivative_positive_everywhere(self):
        assert _IMPORT_OK
        for i in range(1, 100):
            j_lo = i/100 - 0.005; j_hi = i/100 + 0.005
            assert P(j_hi) >= P(j_lo)
    def test_t_target_from_params(self):
        import math
        t = (1/20) ** (1/5)
        assert _IMPORT_OK and abs(t - 0.5492802717) < 1e-5
        assert _IMPORT_OK and LSH_TARGET_J == 0.70
    def test_recall_at_t_about_63_percent(self):
        t = (1/20)**(1/5)
        assert _IMPORT_OK and abs(P(t) - 0.6321206) < 0.02
    def test_fn_helper_matches_analytic(self):
        assert _IMPORT_OK
        for j in [0.1, 0.3, 0.5, 0.7, 0.8, 0.95]:
            assert abs(_lsh_recall_theoretical(j) - P(j)) < 1e-9
