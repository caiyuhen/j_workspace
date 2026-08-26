import asyncio, time, random
from app.services.simhash import simhash64, THR, find_duplicates_bktree

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

for n in (2000, 10000):
    recs = gen(n)
    t0 = time.perf_counter()
    kept, diag = asyncio.run(find_duplicates_bktree(recs, THR, n_jobs=8, enable_parity_check=False))
    print("BK-pure n", n, "kept", len(kept), "ratio", round(len(kept)/n, 4),
          "elapsed_s", round(time.perf_counter() - t0, 2))
