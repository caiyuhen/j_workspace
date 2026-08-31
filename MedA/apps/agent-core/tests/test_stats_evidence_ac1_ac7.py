import math
from app.services.stats_evidence import (
    normal_cdf,
    chi2_cdf,
    cohen_kappa,
    binary_rr_95ci,
    binary_or_95ci,
    binary_rd_95ci,
    continuous_md_95ci,
    fixed_iv_pooled,
    fixed_mh_pooled_rr,
    dl_random_pooled,
    compute_heterogeneity,
)


def test_ac1_cohen_kappa_4x4_07143():
    table = [
        [38, 0, 0, 2],
        [0, 28, 0, 2],
        [0, 0, 14, 6],
        [2, 2, 6, 0],
    ]
    k = cohen_kappa(table)
    assert abs(k - 0.7143) <= 0.001


def test_ac2_binary_rr_95ci_no_cc():
    res = binary_rr_95ci(a=20, n1=100, c=10, n2=100, cc=False)
    assert abs(res["rr"] - 2.0) <= 1e-9
    # Katz: var(logRR) = 1/20 - 1/100 + 1/10 - 1/100 = 0.13, se = 0.360555
    assert abs(res["ci_low"] - 0.9866) <= 0.0001
    assert abs(res["ci_high"] - 4.0545) <= 0.0001


def test_ac3_5studies_fixed_iv_vs_mh_rr_diff_le_002():
    studies = [
        (20, 20000, 22, 20000),
        (40, 40000, 44, 40000),
        (30, 30000, 33, 30000),
        (50, 50000, 55, 50000),
        (60, 60000, 66, 60000),
    ]
    rrs = []
    ses = []
    for a, n1, c, n2 in studies:
        r = binary_rr_95ci(a=a, n1=n1, c=c, n2=n2, cc=False)
        log_rr = math.log(r["rr"])
        se_rr = (math.log(r["ci_high"]) - math.log(r["ci_low"])) / (2 * 1.959963984540054)
        rrs.append(log_rr)
        ses.append(se_rr)
    iv_res = fixed_iv_pooled(rrs, ses)
    iv_rr = math.exp(iv_res["pooled"])
    mh_res = fixed_mh_pooled_rr(studies)
    assert abs(iv_rr - mh_res["rr"]) <= 0.002


def test_ac4_dl_random_pooled_tau2_0234():
    ests = [-0.348, -0.190, -0.100, -0.010, 0.148]
    ses = [0.107, 0.107, 0.107, 0.107, 0.107]
    res = dl_random_pooled(ests, ses)
    assert abs(res["tau2"] - 0.0234) <= 0.001


def test_ac5_compute_heterogeneity_i2_672_pq_0015():
    ests = [-0.348, -0.190, -0.100, -0.010, 0.148]
    ses = [0.107, 0.107, 0.107, 0.107, 0.107]
    res = compute_heterogeneity(ests, ses)
    assert abs(res["I2"] - 67.2) <= 2.0
    assert abs(res["p_Q"] - 0.015) <= 0.005


def test_ac6_continuous_md_95ci_04_ci():
    res = continuous_md_95ci(m1=5.2, s1=1.1, n1=50, m2=4.8, s2=0.9, n2=50)
    assert abs(res["md"] - 0.4) <= 1e-9
    # se = sqrt(1.1²/50 + 0.9²/50) = 0.200998
    assert abs(res["ci_low"] - 0.0061) <= 0.0001
    assert abs(res["ci_high"] - 0.7939) <= 0.0001


def test_normal_cdf_minus_196():
    assert abs(normal_cdf(-1.96) - 0.0250) <= 0.001


def test_normal_cdf_196():
    assert abs(normal_cdf(1.96) - 0.9750) <= 0.001


def test_normal_cdf_0():
    assert abs(normal_cdf(0.0) - 0.5) <= 1e-9


def test_normal_cdf_3():
    assert abs(normal_cdf(3.0) - 0.99865) <= 0.0001


def test_chi2_cdf_df4_x9488_is_095():
    assert abs(chi2_cdf(df=4, x=9.488) - 0.95) <= 0.005


def test_chi2_cdf_df1_x3841_is_095():
    assert abs(chi2_cdf(df=1, x=3.841) - 0.95) <= 0.005


def test_binary_rd_95ci_simple():
    res = binary_rd_95ci(a=20, n1=100, c=10, n2=100, cc=False)
    assert abs(res["rd"] - 0.10) <= 1e-9
    assert res["ci_low"] < 0.10 < res["ci_high"]


def test_binary_or_95ci_simple():
    res = binary_or_95ci(a=20, n1=80, c=10, n2=90, cc=False)
    or_exp = (20 * 80) / (60 * 10)
    assert abs(res["or"] - or_exp) <= 0.001
    assert res["ci_low"] < res["or"] < res["ci_high"]


def test_binary_rr_95ci_cc_05_on_zero():
    res = binary_rr_95ci(a=0, n1=50, c=5, n2=50, cc=True)
    assert res["rr"] > 0
    assert res["ci_low"] > 0
    assert math.isfinite(res["ci_high"])


def test_binary_or_95ci_cc_05_on_zero():
    res = binary_or_95ci(a=0, n1=50, c=5, n2=50, cc=True)
    assert res["or"] > 0
    assert res["ci_low"] > 0
    assert math.isfinite(res["ci_high"])


def test_fixed_iv_pooled_se_two_studies():
    ests = [0.5, 0.6]
    ses = [0.1, 0.15]
    res = fixed_iv_pooled(ests, ses)
    w1 = 1.0 / (0.1 ** 2)
    w2 = 1.0 / (0.15 ** 2)
    expected_pooled = (w1 * 0.5 + w2 * 0.6) / (w1 + w2)
    expected_se = math.sqrt(1.0 / (w1 + w2))
    assert abs(res["pooled"] - expected_pooled) <= 1e-9
    assert abs(res["se"] - expected_se) <= 1e-9


def test_fixed_iv_pooled_three_studies_balanced():
    ests = [0.3, 0.3, 0.3]
    ses = [0.1, 0.1, 0.1]
    res = fixed_iv_pooled(ests, ses)
    assert abs(res["pooled"] - 0.3) <= 1e-9
    expected_se = math.sqrt(1.0 / (3.0 / 0.01))
    assert abs(res["se"] - expected_se) <= 1e-9


def test_fixed_mh_pooled_rr_two_studies_simple():
    studies = [(10, 100, 8, 100), (15, 200, 10, 200)]
    res = fixed_mh_pooled_rr(studies)
    assert res["rr"] > 0
    assert res["ci_low"] < res["rr"] < res["ci_high"]


def test_dl_random_pooled_homogeneous_tau2_near_zero():
    ests = [0.5, 0.51, 0.49, 0.505, 0.495]
    ses = [0.05, 0.05, 0.05, 0.05, 0.05]
    res = dl_random_pooled(ests, ses)
    assert res["tau2"] >= 0.0
    assert res["tau2"] <= 0.001


def test_dl_random_pooled_single_study():
    ests = [0.7]
    ses = [0.2]
    res = dl_random_pooled(ests, ses)
    assert abs(res["tau2"]) <= 1e-9
    assert abs(res["pooled"] - 0.7) <= 1e-9
    assert abs(res["se"] - 0.2) <= 1e-9


def test_cohen_kappa_2x2_perfect_diagonal():
    table = [[20, 0], [0, 30]]
    k = cohen_kappa(table)
    assert abs(k - 1.0) <= 1e-9


def test_cohen_kappa_2x2_chance_only():
    table = [[6, 9], [4, 6]]
    k = cohen_kappa(table)
    assert abs(k - 0.0) <= 1e-9


def test_binary_rd_95ci_cc_boundary():
    res = binary_rd_95ci(a=1, n1=10, c=0, n2=10, cc=True)
    assert math.isfinite(res["rd"])
    assert math.isfinite(res["ci_low"])
    assert math.isfinite(res["ci_high"])


def test_compute_heterogeneity_homogeneous_i2_near_zero():
    ests = [0.1, 0.101, 0.099, 0.102, 0.098]
    ses = [0.02, 0.02, 0.02, 0.02, 0.02]
    res = compute_heterogeneity(ests, ses)
    assert res["I2"] >= 0.0
    assert res["I2"] <= 30.0
    assert res["p_Q"] > 0.05
