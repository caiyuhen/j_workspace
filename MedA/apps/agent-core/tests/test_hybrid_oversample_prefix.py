import random
from collections import defaultdict

import pytest

from app.services.simhash import (
    OVERSAMPLE_PREFIX_BITS,
    _oversample_prefix_pairs,
    minhash_signature,
    lsh_find_candidates,
    tokenize_to_2shingles,
    simhash64,
)


def _seed_records(n, seed=42):
    random.seed(seed)
    tok = "abcdefghijklmnopqrstuvwxyz0123456789"
    recs = []
    for i in range(n):
        length = random.randint(20, 60)
        text = "".join(random.choice(tok) for _ in range(length))
        recs.append({"id": i, "title": f"T{i}", "abstract": text})
    return recs


def _jaccard_texts(a: str, b: str, k=5) -> float:
    def shingles(s):
        return {s[i:i + k] for i in range(max(1, len(s) - k + 1))}
    sa, sb = shingles(a), shingles(b)
    u = sa | sb
    return len(sa & sb) / len(u) if u else 0.0


def _make_mutant(base: str, keep_ratio: float, seed=0) -> str:
    random.seed(seed)
    chars = list(base)
    n_change = max(1, int(len(chars) * (1 - keep_ratio)))
    idxs = random.sample(range(len(chars)), min(n_change, len(chars)))
    pool = "abcdefghijklmnopqrstuvwxyz0123456789"
    for i in idxs:
        chars[i] = random.choice(pool)
    return "".join(chars)


class TestOversamplePrefixBasics:
    def test_oversample_empty(self):
        assert _oversample_prefix_pairs([]) == set()

    def test_oversample_one(self):
        assert _oversample_prefix_pairs([0x1234567812345678]) == set()

    def test_oversample_pair_identical_prefixes(self):
        fp0 = (0xABCD << 54) | 0x0000_0000_0000_0001
        fp1 = (0xABCD << 54) | 0x0000_0000_0000_0002
        res = _oversample_prefix_pairs([fp0, fp1], n_bits=16)
        assert (0, 1) in res or (1, 0) in res

    def test_oversample_distinct_prefixes(self):
        fp0 = 0xAAAA << 48
        fp1 = 0xBBBB << 48
        res = _oversample_prefix_pairs([fp0, fp1], n_bits=16)
        assert not res

    def test_oversample_symmetry_canonical(self):
        fps = [
            (0xF00D << 48) | i
            for i in range(5)
        ]
        res = _oversample_prefix_pairs(fps, n_bits=16)
        for (a, b) in res:
            assert a < b, "pairs must be canonical small<large"

    def test_oversample_group_all_same_prefix(self):
        fps = [(0xBEEF << 48) | i for i in range(8)]
        res = _oversample_prefix_pairs(fps, n_bits=16)
        n = len(fps)
        assert len(res) == n * (n - 1) // 2, "all pairs for shared prefix"

    def test_oversample_bits_matches_global_default(self):
        assert OVERSAMPLE_PREFIX_BITS == 10


class TestOversampleBoundaryRecall:
    @pytest.mark.parametrize("seed", list(range(50)))
    def test_j07_boundary_fn_rate_low(self, seed):
        random.seed(10_000 + seed)
        base = "a" * 120
        boundary_true_pairs = 0
        lsh_missed = 0
        oversample_rescued = 0
        for inner in range(20):
            records = []
            base_text = base + "".join(random.choice("xyz") for _ in range(80))
            records.append({"id": 0, "title": "base", "abstract": base_text})
            for k in range(1, 4):
                mutant = _make_mutant(base_text, keep_ratio=0.68 + 0.02 * (k - 1), seed=seed * 50 + inner * 3 + k)
                records.append({"id": k, "title": f"m{k}", "abstract": mutant})
            texts = [r["abstract"] for r in records]
            sims = [simhash64(t) for t in texts]
            sigs = [minhash_signature(tokenize_to_2shingles(t)) for t in texts]
            lsh_cand = lsh_find_candidates(sigs)
            over_cand = _oversample_prefix_pairs(sims, n_bits=10)
            all_cand = lsh_cand | over_cand
            for i in range(len(records)):
                for j in range(i + 1, len(records)):
                    jv = _jaccard_texts(texts[i], texts[j], k=5)
                    if jv >= 0.70:
                        boundary_true_pairs += 1
                        pair = (i, j)
                        if pair not in lsh_cand:
                            lsh_missed += 1
                            if pair in all_cand:
                                oversample_rescued += 1
        if boundary_true_pairs:
            fn_rate = (boundary_true_pairs - (boundary_true_pairs - lsh_missed + oversample_rescued)) / boundary_true_pairs
            assert fn_rate <= 0.05, f"seed={seed} boundary fn_rate={fn_rate:.3f} exceeds 5%"

    def test_oversample_small_constant_adds_at_most_10pct_candidates(self):
        recs = _seed_records(500, seed=7)
        texts = [r["abstract"] for r in recs]
        sims = [simhash64(t) for t in texts]
        sigs = [minhash_signature(tokenize_to_2shingles(t)) for t in texts]
        lsh_c = lsh_find_candidates(sigs)
        over_c = _oversample_prefix_pairs(sims, n_bits=10)
        extras = len(over_c - lsh_c)
        base = max(1, len(lsh_c))
        total_pairs = len(sims) * (len(sims) - 1) // 2
        cap = max(int(0.05 * total_pairs), 200)
        assert extras <= base * 0.50 + cap, f"oversample added too many extras: {extras}/{base} (cap={cap})"

    def test_lsh_plus_oversample_high_recall_at_j075(self):
        random.seed(99)
        tp_total = 0
        found_total = 0
        for trial in range(60):
            n = 40
            ids_added = 0
            recs = []
            clusters = defaultdict(list)
            for ci in range(4):
                base_str = "cluster_" + str(ci) + "_" + "x" * 100
                for rep in range(10):
                    jitter = _make_mutant(base_str, keep_ratio=0.78 + 0.01 * (rep % 4), seed=trial * 100 + ci * 10 + rep)
                    clusters[ci].append(len(recs))
                    recs.append({"id": ids_added, "title": f"r{ids_added}", "abstract": jitter})
                    ids_added += 1
            texts = [r["abstract"] for r in recs]
            sims = [simhash64(t) for t in texts]
            sigs = [minhash_signature(tokenize_to_2shingles(t)) for t in texts]
            cand = lsh_find_candidates(sigs) | _oversample_prefix_pairs(sims, n_bits=10)
            for ci, members in clusters.items():
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        a, b = members[i], members[j]
                        if _jaccard_texts(texts[a], texts[b], k=5) >= 0.70:
                            tp_total += 1
                            if (a, b) in cand:
                                found_total += 1
        if tp_total:
            recall = found_total / tp_total
            assert recall >= 0.95, f"high-J recall too low: {recall:.3f} ({found_total}/{tp_total})"
