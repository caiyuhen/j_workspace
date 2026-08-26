import random, time, asyncio, sys
sys.path.insert(0, "apps/agent-core")
from app.services import simhash as S

random.seed(1)
# 1) equivalence
words = ["alpha","beta","gamma","delta","肾病","糖尿","trial","phase","nct12345678","x"]
bad = 0
for t in range(3000):
    k = random.randint(0, 40)
    txt = " ".join(random.choice(words) for _ in range(k))
    if S.simhash64(txt) != S._simhash64_fast(txt):
        bad += 1
print("equiv_mismatch", bad)
print("short", S.simhash64("abc"), S._simhash64_fast("abc"))

# 2) parity on synthetic
sys.path.insert(0, "apps/agent-core/tests")
from test_simhash_bktree_parity import _records_for_preset_size, PRESETS  # noqa

for preset in PRESETS[:2]:
    for n in (5000,):
        recs = _records_for_preset_size(preset, n)
        t0 = time.perf_counter()
        kb, _ = asyncio.run(S.find_duplicates_bktree(recs, S.THR, n_jobs=8, enable_parity_check=False))
        t1 = time.perf_counter()
        kh, d = S.find_duplicates_hybrid(recs, S.THR, n_jobs=8, enable_parity_check=False)
        t2 = time.perf_counter()
        sb, sh = set(kb), set(kh)
        print(preset, n, "bk", len(sb), f"{t1-t0:.2f}s", "hy", len(sh), f"{t2-t1:.2f}s",
              "missing", len(sb-sh), "extra", len(sh-sb), "fallback", d["perf_json"]["fallback_used"])
