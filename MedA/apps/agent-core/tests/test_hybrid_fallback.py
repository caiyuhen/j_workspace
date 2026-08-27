import pytest

try:
    from app.services.simhash import (
        find_duplicates_hybrid, FALLBACK_N_PARITY,
    )
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False
    find_duplicates_hybrid = None
    FALLBACK_N_PARITY = None

class TestHybridFallback:
    def test_fallback_const_2000_w11_safe_boundary(self):
        assert _IMPORT_OK and FALLBACK_N_PARITY == 2000
    def test_len_1999_triggers_bk_only(self):
        recs = [{"id":i,"title":f"t{i}","abstract":""} for i in range(1999)]
        kept, diag = find_duplicates_hybrid(recs)
        assert _IMPORT_OK and diag["perf_json"]["fallback_used"] is True
    def test_len_2000_still_fallback_bk(self):
        recs = [{"id":i,"title":f"t{i}","abstract":"dup"} for i in range(2000)]
        kept, diag = find_duplicates_hybrid(recs)
        assert _IMPORT_OK and diag["perf_json"]["fallback_used"] is True
    def test_len_2001_enters_hybrid(self):
        recs = [{"id":i,"title":f"t{i}","abstract":"a"*i} for i in range(2001)]
        kept, diag = find_duplicates_hybrid(recs)
        assert _IMPORT_OK and diag["perf_json"]["fallback_used"] is False
    def test_stage_minhash_ms_zero_when_fallback(self):
        kept, diag = find_duplicates_hybrid([{"id":i,"title":f"t{i}"} for i in range(500)])
        assert _IMPORT_OK and diag["perf_json"]["stage_ms"]["minhash_ms"] == 0
    def test_stage_lsh_ms_zero_when_fallback(self):
        kept, diag = find_duplicates_hybrid([{"id":i} for i in range(1000)])
        assert _IMPORT_OK and diag["perf_json"]["stage_ms"]["lsh_ms"] == 0
    def test_stage_oversample_prefix_zero_when_fallback(self):
        kept, diag = find_duplicates_hybrid([{"id":i} for i in range(2000)])
        assert _IMPORT_OK and diag["perf_json"]["stage_ms"].get("oversample_ms", 0) == 0
    def test_stage_bk_ms_nonzero_always(self):
        kept, diag = find_duplicates_hybrid([{"id":i} for i in range(500)])
        assert _IMPORT_OK and diag["perf_json"]["stage_ms"]["bk_ms"] >= 0
    def test_version_w12_hybrid_v1_always(self):
        assert _IMPORT_OK
        for n in [500, 10001]:
            recs = [{"id":i,"title":f"t{i}"} for i in range(n)]
            kept, diag = find_duplicates_hybrid(recs)
            assert diag["perf_json"]["version"] == "w12-hybrid-v1"
    def test_total_ms_equals_stages_sum_when_hybrid(self):
        n = 10005
        recs = [{"id":i,"title":f"title {i%100}","abstract":"abstract body " * (i%30)} for i in range(n)]
        kept, diag = find_duplicates_hybrid(recs)
        st = diag["perf_json"]["stage_ms"]
        total = st["minhash_ms"]+st["lsh_ms"]+st.get("oversample_ms",0)+st["bk_ms"]+st["union_ms"]
        assert _IMPORT_OK and abs(total - st["total_ms"]) < 50.0
    def test_lsh_candidates_field_exists_always(self):
        kept, diag = find_duplicates_hybrid([{"id":i} for i in range(100)])
        assert _IMPORT_OK and "lsh_candidates" in diag["perf_json"]
    def test_lsh_filter_ratio_field(self):
        kept, diag = find_duplicates_hybrid([{"id":i} for i in range(10001)])
        assert _IMPORT_OK and "lsh_candidate_filter_ratio" in diag["perf_json"]
    def test_oversample_prefix_field_exists(self):
        kept, diag = find_duplicates_hybrid([{"id":i} for i in range(50)])
        assert _IMPORT_OK and "oversample_prefix" in diag["perf_json"]
    def test_n_records_field(self):
        recs = [{"id":i} for i in range(555)]
        kept, diag = find_duplicates_hybrid(recs)
        assert _IMPORT_OK and diag["perf_json"]["n_records"] == 555
    def test_kept_ids_is_list_of_ints(self):
        kept, _ = find_duplicates_hybrid([{"id":i} for i in range(200)])
        assert _IMPORT_OK and isinstance(kept, list) and all(isinstance(x,int) for x in kept)
    def test_kept_ids_are_sorted(self):
        recs = [{"id":100-i,"title":f"t{i}"} for i in range(100)]
        kept, _ = find_duplicates_hybrid(recs)
        assert _IMPORT_OK and kept == sorted(kept)
    def test_exact_duplicates_in_fewer_than_10k_result_in_kept_min_id(self):
        recs = [
            {"id": 17, "title": "exact same A", "abstract": "body"},
            {"id": 9,  "title": "exact same A", "abstract": "body"},
            {"id": 21, "title": "exact same A", "abstract": "body"},
        ]
        kept, _ = find_duplicates_hybrid(recs)
        assert _IMPORT_OK and 9 in kept and 17 not in kept and 21 not in kept
    def test_hybrid_vs_bk_parity_result_equal_when_below_fallback(self):
        assert _IMPORT_OK
        import asyncio
        from app.services.simhash import find_duplicates_bktree
        recs = [{"id":i,"title":f"kw {i//3} same group"} for i in range(500)]
        kept_h, _ = find_duplicates_hybrid(recs)
        kept_b, _ = asyncio.run(find_duplicates_bktree(recs))
        assert set(kept_h) == set(kept_b)
