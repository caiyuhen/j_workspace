import asyncio, random, time
from app.services.simhash import simhash64, THR, find_duplicates_bktree, find_duplicates_hybrid

BOILER = ("randomized double-blind placebo controlled multicenter trial evaluating "
          "efficacy and safety primary endpoint change from baseline").split()

def gen(n, seed=42, dup_rate=0.15):
    rng = random.Random(seed)
    recs = []
    for i in range(n):
        if recs and rng.random() < dup_rate:
            src = recs[rng.randrange(len(recs))]
            recs.append({"id": i + 1, "title": src["title"], "abstract": src["abstract"]})
            continue
        t_tok = [f"kw{rng.randrange(200000)}" for _ in range(8)]
        a_tok = [f"tm{rng.randrange(200000)}" for _ in range(22)]
        recs.append({
            "id": i + 1,
            "title": "trial " + " ".join(t_tok),
            "abstract": " ".join(BOILER[:6]) + " " + " ".join(a_tok),
        })
    return recs

for n in (10000, 50000):
    recs = gen(n)
    uniq_src = len({(r["title"], r["abstract"]) for r in recs})
    t = time.perf_counter(); fps = [simhash64(f"{r['title']} {r['abstract']}") for r in recs]
    print("n", n, "uniq_texts", uniq_src, "distinct_fps", len(set(fps)), "simhash_s", round(time.perf_counter()-t, 2))
    t = time.perf_counter()
    kb, _ = asyncio.run(find_duplicates_bktree(recs, THR, n_jobs=8, enable_parity_check=False))
    print("   BK   kept", len(kb), "ratio", round(len(kb)/n, 4), "s", round(time.perf_counter()-t, 2))
    t = time.perf_counter()
    kh, d = find_duplicates_hybrid(recs, THR, n_jobs=8, enable_parity_check=False)
    print("   HYB  kept", len(kh), "ratio", round(len(kh)/n, 4), "s", round(time.perf_counter()-t, 2),
          "fb", d["perf_json"]["fallback_used"], "parity_eq", set(kb) == set(kh))
    print("   avg_rec_bytes", (sum(len(r["title"]) + len(r["abstract"]) for r in recs) // n) + 90)
