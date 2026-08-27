import pytest
import asyncio
import json
import statistics
import time
from time import perf_counter
from pathlib import Path
from app.services.simhash import find_duplicates_bktree


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "w11_synthetic_2000.json"


SLO_TARGETS_MS = {
    500: 1000.0,
    1000: 1500.0,
    2000: 3000.0,
    5000: 8000.0,
}


@pytest.fixture(scope="module")
def fixture_sglt2i_ckd() -> list[dict]:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    sglt = [r for r in data if r.get("preset") == "sglt2i_ckd"]
    return sglt


@pytest.fixture(scope="module")
def bench_stats_cache(fixture_sglt2i_ckd) -> dict[int, dict]:
    cache = {}

    def _take_or_pad(records: list[dict], n: int) -> list[dict]:
        if n <= len(records):
            return records[:n]
        result = []
        base_len = len(records)
        copies_needed = (n + base_len - 1) // base_len
        for c in range(copies_needed):
            for r in records:
                new_r = dict(r)
                new_r["id"] = r["id"] + c * 100000
                result.append(new_r)
                if len(result) >= n:
                    return result[:n]
        return result[:n]

    def _percentile(values: list[float], pct: float) -> float:
        sorted_v = sorted(values)
        k = (len(sorted_v) - 1) * (pct / 100.0)
        f = int(k)
        c = f + 1
        if c >= len(sorted_v):
            return sorted_v[-1]
        d = k - f
        return sorted_v[f] * (1 - d) + sorted_v[c] * d

    for n in [500, 1000, 2000, 5000]:
        time.sleep(2.0)
        records = _take_or_pad(fixture_sglt2i_ckd, n)
        asyncio.run(
            find_duplicates_bktree(records, enable_parity_check=False, n_jobs=8)
        )
        durations_ms = []
        speedups = []
        for _ in range(3):
            t0 = perf_counter()
            _, diag = asyncio.run(
                find_duplicates_bktree(records, enable_parity_check=False, n_jobs=8)
            )
            t1 = perf_counter()
            durations_ms.append((t1 - t0) * 1000)
            speedups.append(diag["perf"]["speedup_x"])
        med = statistics.median(durations_ms)
        p95 = _percentile(durations_ms, 95)
        std = statistics.stdev(durations_ms) if len(durations_ms) > 1 else 0.0
        med_speedup = statistics.median(speedups)
        cache[n] = {
            "n": n,
            "durations_ms": durations_ms,
            "median_ms": med,
            "p95_ms": p95,
            "std_ms": std,
            "median_speedup": med_speedup,
        }
    return cache


# ============================================================
# N=500 · 4 asserts
# ============================================================
@pytest.mark.bench
def test_SLO_median_N500(bench_stats_cache):
    s = bench_stats_cache[500]
    assert s["median_ms"] <= SLO_TARGETS_MS[500] * 1.3, (
        f"N=500 median={s['median_ms']:.1f}ms > SLO*1.3={SLO_TARGETS_MS[500]*1.3:.1f}ms"
    )


@pytest.mark.bench
def test_SLO_p95_N500(bench_stats_cache):
    s = bench_stats_cache[500]
    assert s["p95_ms"] <= SLO_TARGETS_MS[500] * 1.6, (
        f"N=500 p95={s['p95_ms']:.1f}ms > SLO*1.6={SLO_TARGETS_MS[500]*1.6:.1f}ms"
    )


@pytest.mark.bench
def test_Speedup_N500(bench_stats_cache):
    s = bench_stats_cache[500]
    assert s["median_speedup"] >= 5.0, (
        f"N=500 speedup={s['median_speedup']:.2f}x < 5x"
    )


@pytest.mark.bench
def test_Low_std_N500(bench_stats_cache):
    s = bench_stats_cache[500]
    if s["median_ms"] > 0:
        cv = s["std_ms"] / s["median_ms"]
        assert cv <= 0.25, (
            f"N=500 std/median={cv:.3f} > 0.25 (std={s['std_ms']:.1f} med={s['median_ms']:.1f})"
        )


# ============================================================
# N=1000 · 4 asserts
# ============================================================
@pytest.mark.bench
def test_SLO_median_N1000(bench_stats_cache):
    s = bench_stats_cache[1000]
    assert s["median_ms"] <= SLO_TARGETS_MS[1000] * 1.3, (
        f"N=1000 median={s['median_ms']:.1f}ms > SLO*1.3={SLO_TARGETS_MS[1000]*1.3:.1f}ms"
    )


@pytest.mark.bench
def test_SLO_p95_N1000(bench_stats_cache):
    s = bench_stats_cache[1000]
    assert s["p95_ms"] <= SLO_TARGETS_MS[1000] * 1.6, (
        f"N=1000 p95={s['p95_ms']:.1f}ms > SLO*1.6={SLO_TARGETS_MS[1000]*1.6:.1f}ms"
    )


@pytest.mark.bench
def test_Speedup_N1000(bench_stats_cache):
    s = bench_stats_cache[1000]
    assert s["median_speedup"] >= 5.0, (
        f"N=1000 speedup={s['median_speedup']:.2f}x < 5x"
    )


@pytest.mark.bench
def test_Low_std_N1000(bench_stats_cache):
    s = bench_stats_cache[1000]
    if s["median_ms"] > 0:
        cv = s["std_ms"] / s["median_ms"]
        assert cv <= 0.25, (
            f"N=1000 std/median={cv:.3f} > 0.25 (std={s['std_ms']:.1f} med={s['median_ms']:.1f})"
        )


# ============================================================
# N=2000 · 4 asserts
# ============================================================
@pytest.mark.bench
def test_SLO_median_N2000(bench_stats_cache):
    s = bench_stats_cache[2000]
    print(f"\n  [N2000 MEDIAN] actual={s['median_ms']:.1f}ms (durations={[round(d,1) for d in s['durations_ms']]})")
    assert s["median_ms"] <= SLO_TARGETS_MS[2000] * 1.3, (
        f"N=2000 median={s['median_ms']:.1f}ms > SLO*1.3={SLO_TARGETS_MS[2000]*1.3:.1f}ms"
    )


@pytest.mark.bench
def test_SLO_p95_N2000(bench_stats_cache):
    s = bench_stats_cache[2000]
    assert s["p95_ms"] <= SLO_TARGETS_MS[2000] * 1.6, (
        f"N=2000 p95={s['p95_ms']:.1f}ms > SLO*1.6={SLO_TARGETS_MS[2000]*1.6:.1f}ms"
    )


@pytest.mark.bench
def test_Speedup_N2000(bench_stats_cache):
    s = bench_stats_cache[2000]
    assert s["median_speedup"] >= 10.0, (
        f"N=2000 speedup={s['median_speedup']:.2f}x < 10x"
    )


@pytest.mark.bench
def test_Low_std_N2000(bench_stats_cache):
    s = bench_stats_cache[2000]
    if s["median_ms"] > 0:
        cv = s["std_ms"] / s["median_ms"]
        assert cv <= 0.25, (
            f"N=2000 std/median={cv:.3f} > 0.25 (std={s['std_ms']:.1f} med={s['median_ms']:.1f})"
        )


# ============================================================
# N=5000 · 4 asserts
# ============================================================
@pytest.mark.bench
def test_SLO_median_N5000(bench_stats_cache):
    s = bench_stats_cache[5000]
    assert s["median_ms"] <= SLO_TARGETS_MS[5000] * 1.3, (
        f"N=5000 median={s['median_ms']:.1f}ms > SLO*1.3={SLO_TARGETS_MS[5000]*1.3:.1f}ms"
    )


@pytest.mark.bench
def test_SLO_p95_N5000(bench_stats_cache):
    s = bench_stats_cache[5000]
    assert s["p95_ms"] <= SLO_TARGETS_MS[5000] * 1.6, (
        f"N=5000 p95={s['p95_ms']:.1f}ms > SLO*1.6={SLO_TARGETS_MS[5000]*1.6:.1f}ms"
    )


@pytest.mark.bench
def test_Speedup_N5000(bench_stats_cache):
    s = bench_stats_cache[5000]
    assert s["median_speedup"] >= 5.0, (
        f"N=5000 speedup={s['median_speedup']:.2f}x < 5x"
    )


@pytest.mark.bench
def test_Low_std_N5000(bench_stats_cache):
    s = bench_stats_cache[5000]
    if s["median_ms"] > 0:
        cv = s["std_ms"] / s["median_ms"]
        assert cv <= 0.25, (
            f"N=5000 std/median={cv:.3f} > 0.25 (std={s['std_ms']:.1f} med={s['median_ms']:.1f})"
        )


# =============== W12 EXTENSION APPEND EOF ===============
from app.services.sources.pubmed_adapter import _load_preset_50k


W12_BENCH_SIZES = [500, 1000, 2000, 10000, 50000]
W12_SLO_SOFT_MS = {500: 1300, 1000: 1950, 2000: 3900, 10000: 9600, 50000: 45000}
W12_SLO_HARD_MS = {500: 2600, 1000: 3900, 2000: 7800, 10000: 19200, 50000: 90000}
W12_BENCH_PRESET = "sglt2i_ckd"


def _w12_percentile(values: list[float], pct: float) -> float:
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_v):
        return sorted_v[-1]
    d = k - f
    return sorted_v[f] * (1 - d) + sorted_v[c] * d


def _w12_collect_durations_ms(n: int, warmup: int = 2, run: int = 3, cooldown_s: float = 2.0):
    from app.services.simhash import find_duplicates_hybrid
    records = _load_preset_50k(W12_BENCH_PRESET, n)
    for w in range(warmup):
        find_duplicates_hybrid(records, n_jobs=8, enable_parity_check=(n <= 200))
        time.sleep(cooldown_s)
    durations_ms = []
    for r in range(run):
        t0 = perf_counter()
        find_duplicates_hybrid(records, n_jobs=8, enable_parity_check=(n <= 200))
        t1 = perf_counter()
        durations_ms.append((t1 - t0) * 1000.0)
        if r < run - 1:
            time.sleep(cooldown_s)
    return durations_ms


@pytest.mark.bench
@pytest.mark.parametrize("size", W12_BENCH_SIZES)
def test_W12_p50_under_SLO_soft(size):
    if size == 50000:
        pytest.skip("N50k CI only")
    durations = _w12_collect_durations_ms(size, warmup=2, run=3, cooldown_s=2.0)
    p50 = statistics.median(durations)
    import sys
    print(f"\n  [W12 BENCH N={size}] durations={[round(d,0) for d in durations]}ms  p50={p50:.0f}ms  soft SLO={W12_SLO_SOFT_MS[size]}ms  HARD={W12_SLO_HARD_MS[size]}ms", file=sys.stderr)
    assert p50 <= W12_SLO_HARD_MS[size], (
        f"N={size} HARD BLOCK p50={p50:.0f}ms > 2×SLO={W12_SLO_HARD_MS[size]}ms"
    )
    assert p50 <= W12_SLO_SOFT_MS[size], (
        f"N={size} soft SLO p50={p50:.0f}ms > target={W12_SLO_SOFT_MS[size]}ms"
    )


@pytest.mark.bench
@pytest.mark.parametrize("size", W12_BENCH_SIZES)
def test_W12_p95_under_1p5x_HARD_bound(size):
    if size == 50000:
        pytest.skip("N50k CI only")
    durations = _w12_collect_durations_ms(size, warmup=2, run=3, cooldown_s=2.0)
    p95 = _w12_percentile(durations, 95)
    p95_bound = W12_SLO_HARD_MS[size] * 1.5
    assert p95 <= p95_bound, (
        f"N={size} p95={p95:.0f}ms > 1.5×HARD={p95_bound:.0f}ms (durations={[round(d,0) for d in durations]})"
    )
