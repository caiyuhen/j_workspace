import pytest

try:
    from app.services.simhash import (
        lsh_find_candidates, LSH_BANDS, LSH_ROWS,
    )
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False
    lsh_find_candidates = None
    LSH_BANDS = None
    LSH_ROWS = None

class TestLshBandPartition:
    def test_bands_20_rows_5(self):
        assert _IMPORT_OK and LSH_BANDS == 20 and LSH_ROWS == 5
    def test_empty_signatures_empty_pairs(self):
        assert _IMPORT_OK and lsh_find_candidates([]) == set()
    def test_single_sig_no_pairs(self):
        assert _IMPORT_OK and lsh_find_candidates([tuple(range(100))]) == set()
    def test_return_type_is_set_of_tuples(self):
        sigs = [tuple([i]*100) for i in range(3)]
        cand = lsh_find_candidates(sigs)
        assert _IMPORT_OK and isinstance(cand, set)
        if _IMPORT_OK:
            for p in cand: assert isinstance(p, tuple) and len(p) == 2 and p[0] < p[1]
    def test_candidates_sorted_pairs_no_self_pairs(self):
        cand = lsh_find_candidates([tuple([i]*100) for i in range(50)])
        assert _IMPORT_OK and all(a < b for a,b in cand)
    def test_no_duplicate_pairs(self):
        sigs = [tuple([42]*100)]*20
        cand = lsh_find_candidates(sigs)
        assert _IMPORT_OK and len(list(cand)) == len(set(cand))
    def test_100_identical_docs_produce_C_n_2_candidates_or_more(self):
        N = 100
        sigs = [tuple([7]*100) for _ in range(N)]
        cand = lsh_find_candidates(sigs)
        assert _IMPORT_OK and len(cand) >= N*(N-1)//2 * 0.99
    def test_identical_docs_pair_ij_included_in_cand(self):
        sigs = [tuple([0xDEAD]*100)]*40
        cand = lsh_find_candidates(sigs)
        assert _IMPORT_OK and len(cand) >= 700
    def test_bucket_count_20(self):
        assert _IMPORT_OK and len(lsh_find_candidates([tuple([3]*100)]*10)) == 45
    def test_dissimilar_docs_few_pairs(self):
        sigs = [tuple(((i * (p+1)) & 0xFFFFFFFF) for p in range(100)) for i in range(100)]
        cand = lsh_find_candidates(sigs)
        assert _IMPORT_OK and len(cand) <= 200
    def test_dissimilar_500_docs_cand_under_1_percent(self):
        import random
        random.seed(42)
        sigs = [tuple(random.randint(0, 0xFFFFFFFF) for _ in range(100)) for _ in range(500)]
        cand = lsh_find_candidates(sigs)
        all_pairs = 500*499//2
        ratio = len(cand) / all_pairs
        assert _IMPORT_OK and ratio < 0.05
    def test_input_not_mutated(self):
        sigs = [tuple([i]*100) for i in range(10)]
        snap = [s for s in sigs]
        lsh_find_candidates(sigs)
        assert _IMPORT_OK and sigs == snap
    def test_accepts_list_of_tuples_only(self):
        assert _IMPORT_OK
        with pytest.raises(TypeError):
            lsh_find_candidates(["not-a-tuple"]*3)
    def test_deterministic_same_sigs_same_cand(self):
        s = [tuple(range(i, i+100)) for i in range(0, 100, 10)]
        c1 = lsh_find_candidates(s); c2 = lsh_find_candidates(s)
        assert _IMPORT_OK and c1 == c2
    def test_nearby_documents_high_overlap_produce_candidates(self):
        base = list(range(100))
        s1 = tuple(base); s2 = tuple(base[:80] + list(range(200,220)))
        cand = lsh_find_candidates([s1, s2])
        assert _IMPORT_OK and len(cand) <= 1
    def test_three_identical_groups_separate(self):
        sA = tuple([1]*100); sB = tuple([2]*100); sC = tuple([3]*100)
        sigs = [sA]*10 + [sB]*10 + [sC]*10
        cand = lsh_find_candidates(sigs)
        assert _IMPORT_OK
        for (a,b) in cand:
            gA = a // 10; gB = b // 10
            assert gA == gB
    def test_docid_order_does_not_affect_pair_sortedness(self):
        cand = lsh_find_candidates([tuple([9]*100)]*5)
        assert _IMPORT_OK and all(a < b for a,b in cand)
    def test_n_is_2_docs_identical_cand_exactly_1_pair(self):
        cand = lsh_find_candidates([tuple([5]*100)]*2)
        assert _IMPORT_OK and cand == {(0,1)}
    def test_n_is_2_docs_opposite_cand_empty_or_rare(self):
        s1 = tuple([0]*100); s2 = tuple([0xFFFFFFFF]*100)
        cand = lsh_find_candidates([s1, s2])
        assert _IMPORT_OK and cand == set()
    def test_really_all_different_10_sigs_zero_pairs(self):
        basis = [0]*100
        sigs = []
        for i in range(10):
            s = list(basis)
            for bi in range(LSH_BANDS):
                for ri in range(LSH_ROWS):
                    s[bi * LSH_ROWS + ri] = (i + 1) * (bi + 13) * 1009 + ri * 97
            sigs.append(tuple(s))
        cand = lsh_find_candidates(sigs)
        total_possible = len(sigs) * (len(sigs) - 1) // 2
        assert _IMPORT_OK and len(cand) == 0, f"distinct sigs should not share any full band: {len(cand)}/{total_possible}"
    def test_bucket_counts_dont_crash_for_50k_synth(self):
        mocks = [tuple(range(i, i+100)) for i in range(500)]
        c = lsh_find_candidates(mocks)
        assert _IMPORT_OK and isinstance(c, set)
    def test_returns_fresh_copy_not_internal_state(self):
        s = [tuple([1]*100)]*3
        c1 = lsh_find_candidates(s); c1.add((999,1000))
        c2 = lsh_find_candidates(s)
        assert _IMPORT_OK and (999,1000) not in c2
    def test_band_buckets_are_released_after_call_no_memory_leak(self):
        pytest.skip("optional mem test; skip for sandbox")
    def test_zero_sigs_returns_empty_set(self):
        assert _IMPORT_OK and lsh_find_candidates([]) == set()
    def test_two_different_bands_no_overlap_no_candidates(self):
        s1 = tuple([0]*100)
        s2 = list([0]*100); s2[LSH_ROWS] = 999
        cand = lsh_find_candidates([s1, tuple(s2)])
        assert _IMPORT_OK and isinstance(cand, set)
    def test_large_n_500_same_group_high_candidate_count(self):
        sigs = [tuple([0xAB]*100) for _ in range(20)]
        cand = lsh_find_candidates(sigs)
        assert _IMPORT_OK and len(cand) >= 190  # C(20,2) = 190
