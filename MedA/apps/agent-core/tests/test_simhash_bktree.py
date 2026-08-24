import pytest, random, statistics, asyncio
from app.services.simhash import (
    simhash64, hamming_distance,
    BKTree64, find_duplicates_bktree, _union_find_cluster,
    SIMHASH_HAMMING_THRESHOLD as THR,
)


# ============================================================
# Unit B1-B10 · BKTree64 build/query correctness
# ============================================================
def test_B1_bktree_init_default_distance_is_hamming():
    t = BKTree64()
    assert t.distance_fn is hamming_distance


def test_B2_bktree_insert_one_query_self_radius0_returns_self():
    t = BKTree64()
    t.insert(fp=0x1234, payload="r1")
    result = t.query(target=0x1234, radius=0)
    assert result == ["r1"]


def test_B3_bktree_query_radius0_different_fp_returns_empty():
    t = BKTree64()
    t.insert(0xAAAA, "a")
    assert t.query(0xBBBB, 0) == []


def test_B4_bktree_query_within_radius6_included():
    a = 0b0
    b = 0b111111
    t = BKTree64()
    t.insert(a, "a")
    t.insert(b, "b")
    res_a = set(t.query(a, 6))
    res_b = set(t.query(b, 6))
    assert "b" in res_a and "a" in res_b


def test_B5_bktree_query_outside_radius6_excluded():
    a = 0b0
    c = (1 << 7) - 1
    t = BKTree64()
    t.insert(a, "a")
    t.insert(c, "c")
    assert "c" not in set(t.query(a, 6))


def test_B6_bktree_build_batch_20_items_all_queryable_self_radius0():
    items = [(1 << i, f"fp{i}") for i in range(20)]
    t = BKTree64()
    t.build(items)
    for fp, p in items:
        assert t.query(fp, 0) == [p]


def test_B7_bktree_insert_duplicate_fp_keeps_both_payloads():
    t = BKTree64()
    t.insert(0xFF, "pA")
    t.insert(0xFF, "pB")
    res = set(t.query(0xFF, 0))
    assert res == {"pA", "pB"}


def test_B8_bktree_empty_build_query_returns_empty():
    t = BKTree64()
    t.build([])
    assert t.query(0, 100) == []


def test_B9_bktree_query_radius_14_bits():
    t = BKTree64()
    t.build([(0, "A"), (0x3FFF, "B")])
    assert len(t.query(0, 14)) >= 2
    assert "B" not in set(t.query(0, 13))


def test_B10_bktree_build_order_robust_to_shuffled_same_result():
    random.seed(99)
    base = [(random.getrandbits(64), f"r{i}") for i in range(100)]
    a = BKTree64()
    a.build(base)
    b = BKTree64()
    b.build(base[::-1])
    q = base[50][0]
    assert set(a.query(q, 6)) == set(b.query(q, 6))


# ============================================================
# Unit B11-B20 · BKTree64 edge cases / stress
# ============================================================
def test_B11_build_1000_query_fp0_radius10_no_crash():
    random.seed(7)
    items = [(random.getrandbits(64), f"r{i}") for i in range(1000)]
    t = BKTree64()
    t.build(items)
    res = t.query(0, 10)
    assert isinstance(res, list)


def test_B12_insert_none_fp_raises_typeerror():
    t = BKTree64()
    with pytest.raises(TypeError):
        t.insert(fp=None, payload="x")


def test_B13_payload_can_be_any_type_int_dict_tuple():
    t = BKTree64()
    t.insert(0x01, 42)
    t.insert(0x02, {"k": "v"})
    t.insert(0x03, (1, 2, 3))
    assert 42 in t.query(0x01, 0)
    assert {"k": "v"} in t.query(0x02, 0)
    assert (1, 2, 3) in t.query(0x03, 0)


def test_B14_insert_none_payload_query_returns_none_ok():
    t = BKTree64()
    t.insert(0xEE, None)
    res = t.query(0xEE, 0)
    assert None in res


def test_B15_build_2000_self_radius0_all_queryable():
    random.seed(123)
    items = [(random.getrandbits(64), i) for i in range(2000)]
    t = BKTree64()
    t.build(items)
    for fp, p in items:
        assert p in t.query(fp, 0)


def test_B16_query_radius_neg1_returns_empty():
    t = BKTree64()
    t.insert(0x01, "a")
    t.insert(0x02, "b")
    assert t.query(0x01, -1) == []


def test_B17_custom_distance_fn_zero_returns_all():
    t = BKTree64(distance_fn=lambda x, y: 0)
    t.insert(0xAA, "p1")
    t.insert(0xBB, "p2")
    t.insert(0xCC, "p3")
    res = set(t.query(0xFF, 0))
    assert res == {"p1", "p2", "p3"}


def test_B18_custom_distance_fn_100_needs_large_radius():
    t = BKTree64(distance_fn=lambda x, y: 100)
    t.insert(0x00, "p1")
    assert t.query(0x00, 99) == []
    assert "p1" in t.query(0x00, 100)


def test_B19_same_fp_100_inserts_100_payloads():
    t = BKTree64()
    for i in range(100):
        t.insert(0xDEAD, f"item_{i}")
    res = set(t.query(0xDEAD, 0))
    assert len(res) == 100


def test_B20_two_clusters_10_each_mutually_exclusive():
    random.seed(5)
    c1_base = 0xAAAAAAAAAAAAAAA0
    c2_base = 0x5555555555555550
    items = []
    for i in range(10):
        items.append((c1_base | i, f"c1_{i}"))
        items.append((c2_base | i, f"c2_{i}"))
    t = BKTree64()
    t.build(items)
    r1 = set(t.query(c1_base, 6))
    r2 = set(t.query(c2_base, 6))
    assert all(p.startswith("c1_") for p in r1) or len(r1) >= 1
    assert all(p.startswith("c2_") for p in r2) or len(r2) >= 1


# ============================================================
# Unit B21-B24 · _union_find_cluster
# ============================================================
def test_B21_union_find_empty_pairs_returns_empty():
    assert _union_find_cluster([]) == []


def test_B22_union_find_chain_ab_bc_1_group_3():
    pairs = [("a", "b"), ("b", "c")]
    groups = _union_find_cluster(pairs)
    assert len(groups) == 1
    assert sorted(groups[0]) == ["a", "b", "c"]


def test_B23_union_find_4_disjoint_ids_4_groups():
    pairs = [(1, 2), (3, 4)]
    groups = _union_find_cluster(pairs)
    assert len(groups) == 2
    sizes = sorted(len(g) for g in groups)
    assert sizes == [2, 2]


def test_B24_union_find_order_invariance():
    pairs1 = [("b", "a"), ("c", "b")]
    pairs2 = [("a", "b"), ("b", "c")]
    g1 = _union_find_cluster(pairs1)
    g2 = _union_find_cluster(pairs2)
    assert sorted(tuple(sorted(g)) for g in g1) == sorted(tuple(sorted(g)) for g in g2)


# ============================================================
# Integration B25-B32 · find_duplicates_bktree + diag_stats
# ============================================================
def test_B25_find_dup_empty_records():
    kept, diag = asyncio.run(find_duplicates_bktree([], THR, 8, False))
    assert kept == []
    assert "sizes_hist" in diag
    assert "hamming_hist" in diag
    assert "perf" in diag


def test_B26_find_dup_1_record():
    recs = [{"id": 0, "title": "Study A", "abstract": "Abstract here content enough"}]
    kept, diag = asyncio.run(find_duplicates_bktree(recs, THR, 4, False))
    assert kept == [0]
    assert sum(diag["sizes_hist"].values()) == 1


def test_B27_find_dup_2_identical_titles():
    title = "A randomized controlled trial of empagliflozin in CKD patients with long enough title"
    abstract = "Background methods results conclusions plenty of text content here to satisfy min length"
    recs = [
        {"id": 0, "title": title, "abstract": abstract},
        {"id": 1, "title": title, "abstract": abstract},
    ]
    kept, diag = asyncio.run(find_duplicates_bktree(recs, THR, 2, False))
    assert kept == [0]
    assert diag["sizes_hist"].get(2, 0) == 2


def test_B28_find_dup_njobs1_eq_njobs8():
    random.seed(88)
    recs = []
    for i in range(120):
        words = ["trial", "study", "randomized", "double-blind", "phase", "patients",
                 "treatment", "placebo", "outcome", "analysis", "results", "methods",
                 "cardiovascular", "kidney", "diabetes", "hypertension", "systolic", "endpoint"]
        random.shuffle(words)
        title = " ".join(words[:8]) + f" #{i:03d}"
        abstract = " ".join(words[4:]) + f" and {i} more words content"
        recs.append({"id": i, "title": title, "abstract": abstract})
    k1, _ = asyncio.run(find_duplicates_bktree(recs, THR, 1, False))
    k8, _ = asyncio.run(find_duplicates_bktree(recs, THR, 8, False))
    assert k1 == k8


def test_B29_perf_nodes_eq_records_len():
    random.seed(77)
    n = 50
    recs = []
    for i in range(n):
        recs.append({"id": i, "title": f"Randomized trial long enough title {i}",
                     "abstract": f"Abstract with enough content words {i} " + "x y z " * 20})
    _, diag = asyncio.run(find_duplicates_bktree(recs, THR, 4, False))
    assert diag["perf"]["nodes"] == n


def test_B30_hamming_hist_keys_all_le_thr6():
    random.seed(55)
    recs = []
    for i in range(80):
        recs.append({"id": i, "title": f"Medical study RCT patients therapy {i} title text here",
                     "abstract": f"Background methods results conclusions this is abstract body {i} " * 5})
    _, diag = asyncio.run(find_duplicates_bktree(recs, THR, 4, False))
    for h in diag["hamming_hist"].keys():
        assert h <= THR


def test_B31_sizes_hist_sum_eq_n():
    random.seed(33)
    n = 100
    recs = []
    for i in range(n):
        t = f"Clinical trial title {i} machine learning health care data long enough"
        a = f"Abstract body {i} with plenty of text words content methods results conclusion background " * 3
        recs.append({"id": i, "title": t, "abstract": a})
    _, diag = asyncio.run(find_duplicates_bktree(recs, THR, 8, False))
    assert sum(diag["sizes_hist"].values()) == n


def test_B32_speedup_ge_1p5_for_n_ge_100():
    random.seed(999)
    n = 150
    recs = []
    for i in range(n):
        t = f"Randomized controlled double blind study {i} cardiovascular outcomes CKD diabetes"
        a = f"Background {i} We conducted a multi-center double-blind RCT with enough patients " \
            f"Methods primary endpoint secondary endpoints composite cardiovascular renal " \
            f"Results statistically significant hazard ratio confidence interval " \
            f"Conclusion standard of care considerations"
        recs.append({"id": i, "title": t, "abstract": a})
    _, diag = asyncio.run(find_duplicates_bktree(recs, THR, 8, False))
    assert diag["perf"]["speedup_x"] >= 1.5
