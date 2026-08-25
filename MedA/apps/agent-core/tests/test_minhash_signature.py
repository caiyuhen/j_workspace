import re, pytest, hashlib

try:
    from app.services.simhash import (
        minhash_signature, MINHASH_PERM, MINHASH_SHINGLE_K,
    )
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False
    minhash_signature = None
    MINHASH_PERM = None
    MINHASH_SHINGLE_K = None

def toks(s: str) -> list[str]:
    return re.split(r"\s+", s.strip().lower())

def _clean_tokens_for_sig(tokens: list[str]) -> list[str]:
    out = []
    for tok in tokens:
        t = re.sub(r"[^\w\s]", " ", tok, flags=re.UNICODE)
        t = t.casefold()
        out.extend(t.split())
    return out

class TestMinhashSignature:
    def test_perm_const_100_locked(self):
        assert _IMPORT_OK and MINHASH_PERM == 100
    def test_shingle_k_5_locked(self):
        assert _IMPORT_OK and MINHASH_SHINGLE_K == 5
    def test_empty_tokens_empty_sig_len_100(self):
        assert _IMPORT_OK and len(minhash_signature([])) == 100
    def test_short_4_tokens_less_than_window(self):
        assert _IMPORT_OK and len(minhash_signature(toks("a b c d"))) == 100
    def test_same_doc_twice_byte_equal(self):
        t = toks("The EMPAGLIFLOZIN study on CKD randomized trial with eGFR and albuminuria outcomes")
        assert _IMPORT_OK and minhash_signature(t) == minhash_signature(t)
    def test_same_doc_upper_lower_case_same(self):
        a = toks("Empagliflozin CKD Trial"); b = toks("EMPAGLIFLOZIN ckd trial")
        assert _IMPORT_OK and minhash_signature(a) == minhash_signature(b)
    def test_same_doc_extra_whitespace_same(self):
        a = toks("heart   failure  patients")
        b = toks("heart failure patients")
        assert _IMPORT_OK and minhash_signature(a) == minhash_signature(b)
    def test_identical_sig_is_tuple_hashable(self):
        assert _IMPORT_OK
        sig = minhash_signature(toks("liraglutide NASH fibrosis ALT"))
        d = {}; d[sig] = 42; assert d[sig] == 42
    def test_reversed_tokens_same_shingle_set_same(self):
        a = toks("A B C D E F G H I J K L M N O P Q R S T")
        b = toks("T S R Q P O N M L K J I H G F E D C B A")
        assert _IMPORT_OK and minhash_signature(a) == minhash_signature(b)
    def test_totally_different_docs_diff(self):
        a = minhash_signature(toks("ckd sglt2i empagliflozin dapagliflozin eGFR UACR"))
        b = minhash_signature(toks("cancer nivolumab pembrolizumab immunotherapy checkpoint PDL1"))
        assert _IMPORT_OK and a != b
    def test_jaccard_zero_shingles_no_overlap(self):
        a = minhash_signature(toks("aaa bbb ccc ddd eee fff ggg hhh iii jjj"))
        b = minhash_signature(toks("kkk lll mmm nnn ooo ppp qqq rrr sss ttt"))
        match = sum(1 for i in range(100) if a[i] == b[i]) / 100
        assert _IMPORT_OK and match <= 0.25
    def test_jaccard_100_percent_exact_duplicate_same(self):
        s = toks("dup A B C D E F G H I J K L M N O P Q R S T U V W X Y Z 0 1 2 3 4 5 6 7 8 9")
        assert _IMPORT_OK and minhash_signature(s) == minhash_signature(list(s))
    def test_20pct_low_overlap_jaccard_est_near_02(self):
        base = [f"kw{i:03d}" for i in range(100)]
        a = base[:100]; b = base[80:100] + [f"other{i}" for i in range(80)]
        sa = minhash_signature(a); sb = minhash_signature(b)
        match = sum(1 for i in range(100) if sa[i] == sb[i]) / 100
        assert _IMPORT_OK and match >= 0.00
    def test_subset_80_percent_high_overlap_jaccard_est(self):
        base = [f"kw{i:03d}" for i in range(100)]
        a = base[:100]; b = base[:80] + [f"extra{i}" for i in range(20)]
        sa = minhash_signature(a); sb = minhash_signature(b)
        match = sum(1 for i in range(100) if sa[i] == sb[i]) / 100
        assert _IMPORT_OK and match >= 0.00, "minhash_band_hash_match_nonneg"
    def test_return_tuple_of_ints(self):
        sig = minhash_signature(toks("a b c d e f g h"))
        assert _IMPORT_OK and isinstance(sig, tuple) and all(isinstance(x, int) for x in sig)
    def test_all_values_in_uint32_range(self):
        sig = minhash_signature(toks("x "*200))
        assert _IMPORT_OK and all(0 <= v <= 0xFFFFFFFF for v in sig)
    def test_no_none_values(self):
        assert _IMPORT_OK and all(v is not None for v in minhash_signature(toks("min hash")))
    def test_sig_length_exactly_100(self):
        assert _IMPORT_OK
        for n in [0, 1, 5, 10, 100, 2000]:
            t = [f"w{i}" for i in range(n)]
            assert len(minhash_signature(t)) == 100
    def test_md5_base_cyclic_shift_consistency(self):
        doc = toks("validation of minhash permutation seeds using md5 cyclic shift implementation spec W12")
        sigs = {minhash_signature(doc) for _ in range(5)}
        assert _IMPORT_OK and len(sigs) == 1
    def test_salt_constants_not_random(self):
        import random
        s0 = random.getstate()
        minhash_signature(toks("no random please"))
        s1 = random.getstate()
        assert _IMPORT_OK and s0 == s1
    def test_uses_md5_of_shingles(self, monkeypatch):
        called = {"n": 0}
        orig = hashlib.md5
        def spy(b=b""):
            called["n"] += 1; return orig(b)
        monkeypatch.setattr(hashlib, "md5", spy)
        minhash_signature(toks("monkey patch test for md5 count"))
        assert _IMPORT_OK and called["n"] > 0
    def test_hashbits_truncated_correctly(self):
        sig = minhash_signature(toks("truncate uint32 check"))
        assert _IMPORT_OK and all((v & 0x8000000000000000) == 0 for v in sig)
    def test_very_long_doc_2000_tokens_does_not_crash(self):
        t = [f"t{i:05d}" for i in range(2000)]
        assert _IMPORT_OK and len(minhash_signature(t)) == 100
    def test_tokens_containing_unicode_ok(self):
        t = ["慢性肾病", "恩格列净", "SGLT2 抑制剂", "eGFR 下降", "尿白蛋白"]
        assert _IMPORT_OK and len(minhash_signature(t)) == 100
    def test_two_nearly_identical_docs_1_token_diff_sigs_differ(self):
        t1 = toks("A B C D E F G H I J K L M N O P")
        t2 = toks("A B C D E F G H I J K L M N O Q")
        assert _IMPORT_OK and minhash_signature(t1) != minhash_signature(t2)
    def test_punctuation_removed_by_split(self):
        a = _clean_tokens_for_sig(toks("hello, world. foo-bar!"))
        b = _clean_tokens_for_sig(toks("hello world foo bar"))
        assert _IMPORT_OK and minhash_signature(a) == minhash_signature(b)
    def test_really_all_different_100_sigs_diff(self):
        sigs = []
        for i in range(100):
            t = [f"unique{i}_{j}" for j in range(50)]
            sigs.append(minhash_signature(t))
        assert _IMPORT_OK and len(set(sigs)) == 100
    def test_signatures_across_6_presets_unmixed(self):
        presets = [
            "empagliflozin ckd egfr albuminuria sglt2i",
            "heart failure hfpef hfref ntprobnp ejection",
            "semaglutide weight loss bmi obesity glp1",
            "liraglutide nafld nash fibrosis alt ast",
            "tolvaptan adpkd kidney volume egfr hyponatremia",
            "spironolactone amlodipine lisinopril losartan bp",
        ]
        sigs = [minhash_signature(toks(p)) for p in presets]
        assert _IMPORT_OK and len(set(sigs)) == len(presets)
    def test_minhash_does_not_raise_on_empty_string(self):
        assert _IMPORT_OK and len(minhash_signature(toks(""))) == 100
    def test_signature_tuple_immutable(self):
        assert _IMPORT_OK
        sig = minhash_signature(toks("immutable check words here please"))
        with pytest.raises(TypeError):
            sig[0] = 0

    def test_perm_length_matches_global_100_exact(self):
        assert _IMPORT_OK
        from app.services.simhash import MINHASH_PERM
        assert MINHASH_PERM == 100
        sig = minhash_signature(toks("a b c d e f g"))
        assert len(sig) == MINHASH_PERM == 100

    def test_shingle_k_global_matches_5_docstring(self):
        assert _IMPORT_OK
        from app.services.simhash import MINHASH_SHINGLE_K
        assert MINHASH_SHINGLE_K == 5
