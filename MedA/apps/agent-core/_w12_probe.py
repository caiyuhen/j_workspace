import json, os, time, random
from collections import Counter
from app.services.simhash import simhash64, THR

FX = os.path.join("tests", "fixtures", "w12_synthetic_50k.json")
print("fixture size bytes", os.path.getsize(FX))
t0 = time.perf_counter()
with open(FX, "r", encoding="utf-8") as f:
    data = json.load(f)
print("load_s", round(time.perf_counter() - t0, 2), "type", type(data).__name__, "len", len(data))
if isinstance(data, list):
    print("presets", Counter(r.get("preset") for r in data).most_common())
    print("sample0", json.dumps(data[0], ensure_ascii=False)[:300])
else:
    print("keys", list(data.keys())[:10])

# ---- diverse generator candidate ----
WORDS = ("randomized placebo controlled trial efficacy safety renal cardiac hepatic "
         "glycemic albuminuria proteinuria fibrosis hospitalization mortality cohort "
         "multicenter openlabel crossover titration adherence biomarker endpoint "
         "creatinine potassium sodium hemoglobin insulin metformin diuretic statin").split()

def gen(n, dup_rate=0.15, seed=7):
    rng = random.Random(seed)
    recs = []
    for i in range(n):
        if recs and rng.random() < dup_rate:
            src = recs[rng.randrange(len(recs))]
            recs.append({"id": i + 1, "title": src["title"], "abstract": src["abstract"]})
            continue
        title = " ".join(rng.choice(WORDS) for _ in range(12)) + f" study {i}"
        abstract = " ".join(rng.choice(WORDS) for _ in range(60))
        recs.append({"id": i + 1, "title": title, "abstract": abstract})
    return recs

from app.services.simhash import find_duplicates_hybrid
for n in (2000, 10000):
    recs = gen(n)
    fps = [simhash64(f"{r['title']} {r['abstract']}") for r in recs]
    print("gen n", n, "distinct_fps", len(set(fps)))
    t0 = time.perf_counter()
    kept, diag = find_duplicates_hybrid(recs, THR, n_jobs=8, enable_parity_check=False)
    print("   hybrid kept", len(kept), "ratio", round(len(kept) / n, 4),
          "elapsed_s", round(time.perf_counter() - t0, 2),
          "fallback", diag["perf_json"]["fallback_used"])
