import time, random, json
from app.services.simhash import (
    simhash64, THR, find_duplicates_hybrid, tokenize_to_2shingles,
    minhash_signature, lsh_find_candidates, _oversample_prefix_pairs,
)

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

recs = gen(10000)
texts = [f"{r['title']} {r['abstract']}" for r in recs]
t = time.perf_counter(); fps = [simhash64(x) for x in texts]; print("simhash_s", round(time.perf_counter()-t, 2))
t = time.perf_counter(); toks = [tokenize_to_2shingles(x) for x in texts]; print("shingle_s", round(time.perf_counter()-t, 2))
print("avg_shingles", sum(len(x) for x in toks)//len(toks))
t = time.perf_counter(); sigs = [minhash_signature(x) for x in toks]; print("minhash_s", round(time.perf_counter()-t, 2))
t = time.perf_counter(); c = lsh_find_candidates(sigs); print("lsh_s", round(time.perf_counter()-t, 2), "cands", len(c))
t = time.perf_counter(); o = _oversample_prefix_pairs(fps); print("over_s", round(time.perf_counter()-t, 2), "pairs", len(o))
t = time.perf_counter()
kept, diag = find_duplicates_hybrid(recs, THR, n_jobs=8, enable_parity_check=False)
print("hybrid_s", round(time.perf_counter()-t, 2))
print(json.dumps(diag["perf_json"], indent=1))
