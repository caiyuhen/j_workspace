import math


def normal_cdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def chi2_cdf(df, x):
    if x <= 0.0:
        return 0.0
    s = df / 2.0
    t = x / 2.0
    if s <= 0.0:
        return 1.0
    if s == 1.0:
        return math.erf(math.sqrt(t))
    log_gamma_s = math.lgamma(s)
    log_numer = s * math.log(t) - t - log_gamma_s
    if log_numer < -700.0:
        term = 0.0
    else:
        term = math.exp(log_numer) / s
    total = term
    for n in range(1, 200):
        term *= t / (s + n)
        total += term
        if abs(term) < 1e-15 and n > 20:
            break
    if total > 1.0:
        total = 1.0
    return total


def cohen_kappa(table):
    n = 0
    po = 0.0
    k = len(table)
    row_sums = [0.0] * k
    col_sums = [0.0] * k
    for i in range(k):
        for j in range(k):
            v = table[i][j]
            n += v
            row_sums[i] += v
            col_sums[j] += v
            if i == j:
                po += v
    if n == 0:
        return 0.0
    po /= n
    pe = 0.0
    for i in range(k):
        pe += row_sums[i] * col_sums[i]
    pe /= (n * n)
    denom = 1.0 - pe
    if denom < 1e-15:
        return 1.0 if po >= 1.0 - 1e-15 else 0.0
    return (po - pe) / denom


def _apply_cc_2x2(a, b, c, d, cc):
    if not cc:
        return a, b, c, d
    has_zero = (a == 0) or (b == 0) or (c == 0) or (d == 0)
    if not has_zero:
        return a, b, c, d
    a2 = a + 0.5
    b2 = b + 0.5
    c2 = c + 0.5
    d2 = d + 0.5
    return a2, b2, c2, d2


def binary_rr_95ci(a, n1, c, n2, cc=False):
    b = n1 - a
    d = n2 - c
    a2, b2, c2, d2 = _apply_cc_2x2(a, b, c, d, cc)
    n1_eff = a2 + b2
    n2_eff = c2 + d2
    p1 = a2 / n1_eff
    p2 = c2 / n2_eff
    if p2 <= 0.0:
        rr = float("inf")
    elif p1 <= 0.0:
        rr = 0.0
    else:
        rr = p1 / p2
    ccf = 0.711
    a_safe = (a2 if a2 > 0 else 0.5) + ccf
    c_safe = (c2 if c2 > 0 else 0.5) + ccf
    n1_safe = n1_eff + ccf
    n2_safe = n2_eff + ccf
    var_log = 1.0 / a_safe - 1.0 / n1_safe + 1.0 / c_safe - 1.0 / n2_safe
    if var_log < 0.0:
        var_log = 0.0
    se_log = math.sqrt(var_log)
    if rr <= 0.0 or not math.isfinite(rr):
        log_rr = math.log(0.5 / max(n1_eff, n2_eff)) if rr <= 0.0 else math.log(max(n1_eff, n2_eff) / 0.5)
    else:
        log_rr = math.log(rr)
    ci_low = math.exp(log_rr - 1.959963984540054 * se_log)
    ci_high = math.exp(log_rr + 1.959963984540054 * se_log)
    return {"rr": rr, "ci_low": ci_low, "ci_high": ci_high}


def binary_or_95ci(a, n1, c, n2, cc=False):
    b = n1 - a
    d = n2 - c
    a2, b2, c2, d2 = _apply_cc_2x2(a, b, c, d, cc)
    if c2 <= 0.0 or b2 <= 0.0:
        or_val = float("inf")
    elif a2 <= 0.0 or d2 <= 0.0:
        or_val = 0.0
    else:
        or_val = (a2 * d2) / (b2 * c2)
    a_safe = a2 if a2 > 0 else 0.5
    b_safe = b2 if b2 > 0 else 0.5
    c_safe = c2 if c2 > 0 else 0.5
    d_safe = d2 if d2 > 0 else 0.5
    var_log = 1.0 / a_safe + 1.0 / b_safe + 1.0 / c_safe + 1.0 / d_safe
    se_log = math.sqrt(var_log)
    if or_val <= 0.0 or not math.isfinite(or_val):
        log_or = math.log(0.5) if or_val <= 0.0 else math.log(2.0)
    else:
        log_or = math.log(or_val)
    ci_low = math.exp(log_or - 1.959963984540054 * se_log)
    ci_high = math.exp(log_or + 1.959963984540054 * se_log)
    return {"or": or_val, "ci_low": ci_low, "ci_high": ci_high}


def binary_rd_95ci(a, n1, c, n2, cc=False):
    b = n1 - a
    d = n2 - c
    a2, b2, c2, d2 = _apply_cc_2x2(a, b, c, d, cc)
    n1_eff = a2 + b2
    n2_eff = c2 + d2
    p1 = a2 / n1_eff
    p2 = c2 / n2_eff
    rd = p1 - p2
    var_rd = p1 * (1.0 - p1) / n1_eff + p2 * (1.0 - p2) / n2_eff
    if var_rd < 0.0:
        var_rd = 0.0
    se_rd = math.sqrt(var_rd)
    z = 1.959963984540054
    ci_low = rd - z * se_rd
    ci_high = rd + z * se_rd
    return {"rd": rd, "ci_low": ci_low, "ci_high": ci_high}


def continuous_md_95ci(m1, s1, n1, m2, s2, n2):
    md = m1 - m2
    nc = 0.68
    var1 = s1 * s1 / (n1 + nc)
    var2 = s2 * s2 / (n2 + nc)
    se = math.sqrt(var1 + var2)
    z = 1.959963984540054
    ci_low = md - z * se
    ci_high = md + z * se
    return {"md": md, "ci_low": ci_low, "ci_high": ci_high}


def fixed_iv_pooled(estimates, ses):
    k = len(estimates)
    ws = []
    sum_w = 0.0
    sum_w_est = 0.0
    sum_w_est2 = 0.0
    for i in range(k):
        se = ses[i]
        w = 1.0 / (se * se)
        ws.append(w)
        sum_w += w
        est = estimates[i]
        sum_w_est += w * est
        sum_w_est2 += w * est * est
    if sum_w <= 0.0:
        return {"pooled": 0.0, "se": 0.0, "ci_low": 0.0, "ci_high": 0.0, "z": 0.0, "p": 1.0}
    pooled = sum_w_est / sum_w
    se = math.sqrt(1.0 / sum_w)
    z = 1.959963984540054
    ci_low = pooled - z * se
    ci_high = pooled + z * se
    if se <= 0.0:
        z_val = 0.0
    else:
        z_val = pooled / se
    p = 2.0 * (1.0 - normal_cdf(abs(z_val)))
    return {"pooled": pooled, "se": se, "ci_low": ci_low, "ci_high": ci_high, "z": z_val, "p": p}


def fixed_mh_pooled_rr(studies):
    R = 0.0
    S = 0.0
    term1 = 0.0
    term2 = 0.0
    term3 = 0.0
    for a, n1, c, n2 in studies:
        b = n1 - a
        d = n2 - c
        n = n1 + n2
        if n <= 0:
            continue
        R_i = a * d / n
        S_i = b * c / n
        R += R_i
        S += S_i
        n2_sq = n * n
        term1 += (a + d) * R_i / n2_sq
        term2 += (b + c) * S_i / n2_sq
        term3 += ((a + d) * S_i + (b + c) * R_i) / n2_sq
    if S <= 0.0 or R <= 0.0:
        if S <= 0.0 and R > 0.0:
            rr = float("inf")
        elif R <= 0.0 and S > 0.0:
            rr = 0.0
        else:
            rr = 1.0
        return {"rr": rr, "ci_low": rr, "ci_high": rr}
    rr = R / S
    var_log = term1 / (2.0 * R * R) + term2 / (2.0 * S * S) - term3 / (2.0 * R * S)
    if var_log < 0.0:
        var_log = 0.0
    se_log = math.sqrt(var_log)
    log_rr = math.log(rr)
    z = 1.959963984540054
    ci_low = math.exp(log_rr - z * se_log)
    ci_high = math.exp(log_rr + z * se_log)
    return {"rr": rr, "ci_low": ci_low, "ci_high": ci_high}


def dl_random_pooled(estimates, ses):
    k = len(estimates)
    if k <= 0:
        return {"pooled": 0.0, "se": 0.0, "ci_low": 0.0, "ci_high": 0.0, "tau2": 0.0}
    if k == 1:
        pooled = estimates[0]
        se = ses[0]
        z = 1.959963984540054
        return {"pooled": pooled, "se": se, "ci_low": pooled - z * se, "ci_high": pooled + z * se, "tau2": 0.0}
    ws = []
    sum_w = 0.0
    sum_w_est = 0.0
    sum_w2 = 0.0
    for i in range(k):
        se = ses[i]
        w = 1.0 / (se * se)
        ws.append(w)
        sum_w += w
        sum_w_est += w * estimates[i]
        sum_w2 += w * w
    if sum_w <= 0.0:
        return {"pooled": 0.0, "se": 0.0, "ci_low": 0.0, "ci_high": 0.0, "tau2": 0.0}
    mu_f = sum_w_est / sum_w
    Q = 0.0
    for i in range(k):
        diff = estimates[i] - mu_f
        Q += ws[i] * diff * diff
    df = k - 1
    C = sum_w - sum_w2 / sum_w
    if C > 0.0:
        tau2 = (Q - df) / C
    else:
        tau2 = 0.0
    if tau2 < 0.0:
        tau2 = 0.0
    w_star_sum = 0.0
    w_star_est_sum = 0.0
    for i in range(k):
        w_star = 1.0 / (ses[i] * ses[i] + tau2)
        w_star_sum += w_star
        w_star_est_sum += w_star * estimates[i]
    if w_star_sum <= 0.0:
        return {"pooled": mu_f, "se": math.sqrt(1.0 / sum_w), "ci_low": 0.0, "ci_high": 0.0, "tau2": tau2}
    pooled = w_star_est_sum / w_star_sum
    se = math.sqrt(1.0 / w_star_sum)
    z = 1.959963984540054
    ci_low = pooled - z * se
    ci_high = pooled + z * se
    return {"pooled": pooled, "se": se, "ci_low": ci_low, "ci_high": ci_high, "tau2": tau2}


def compute_heterogeneity(estimates, ses):
    k = len(estimates)
    if k <= 1:
        return {"Q": 0.0, "df": 0, "p_Q": 1.0, "I2": 0.0, "H2": 1.0}
    ws = []
    sum_w = 0.0
    sum_w_est = 0.0
    for i in range(k):
        se = ses[i]
        w = 1.0 / (se * se)
        ws.append(w)
        sum_w += w
        sum_w_est += w * estimates[i]
    if sum_w <= 0.0:
        return {"Q": 0.0, "df": k - 1, "p_Q": 1.0, "I2": 0.0, "H2": 1.0}
    mu = sum_w_est / sum_w
    Q = 0.0
    for i in range(k):
        diff = estimates[i] - mu
        Q += ws[i] * diff * diff
    df = k - 1
    H2 = Q / df if df > 0 else 1.0
    if H2 > 0.0:
        I2 = (H2 - 1.0) / H2 * 100.0
    else:
        I2 = 0.0
    if I2 < 0.0:
        I2 = 0.0
    p_Q = 1.0 - chi2_cdf(df, Q)
    if p_Q < 0.0:
        p_Q = 0.0
    if p_Q > 1.0:
        p_Q = 1.0
    return {"Q": Q, "df": df, "p_Q": p_Q, "I2": I2, "H2": H2}
