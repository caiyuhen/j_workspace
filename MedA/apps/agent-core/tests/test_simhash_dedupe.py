import pytest
from app.services.simhash import (
    normalize_text_for_hash,
    simhash64,
    hamming_distance,
    cjk_char_jaccard,
    cjk_titles_near_duplicate,
    CJK_JACCARD_THRESHOLD,
)


class TestHammingDistance:
    def test_hamming_zero(self):
        assert hamming_distance(0x0000000000000000, 0x0000000000000000) == 0

    def test_hamming_one(self):
        assert hamming_distance(0x0000000000000000, 0x0000000000000001) == 1

    def test_hamming_three(self):
        assert hamming_distance(0x0000000000000000, 0x0000000000000007) == 3

    def test_hamming_four(self):
        assert hamming_distance(0x0000000000000000, 0x000000000000000F) == 4

    def test_hamming_sixtyfour(self):
        assert hamming_distance(
            0x0000000000000000, 0xFFFFFFFFFFFFFFFF
        ) == 64


class TestNormalizeText:
    def test_normalize_punctuation(self):
        assert normalize_text_for_hash("Hello, World!") == "hello world"

    def test_normalize_case(self):
        assert normalize_text_for_hash("HELLO WORLD") == "hello world"

    def test_normalize_nfkc(self):
        assert normalize_text_for_hash("Ｈｅｌｌｏ　Ｗｏｒｌｄ") == "hello world"


class TestSimhash64:
    def test_simhash_identical(self):
        a = simhash64("A Systematic Review of Machine Learning in Medicine")
        b = simhash64("A Systematic Review of Machine Learning in Medicine")
        assert a == b

    def test_simhash_punctuation_diff(self):
        a = simhash64("Randomized controlled trial: 5-year outcomes.")
        b = simhash64("Randomized controlled trial 5-year outcomes")
        assert a == b

    def test_simhash_case_diff(self):
        a = simhash64("Meta-Analysis of Diabetes Treatments")
        b = simhash64("meta-analysis of diabetes treatments")
        assert a == b

    def test_simhash_cjk_near(self):
        """Wave82B 中文短文本近似重复判定：**不依赖 SimHash Hamming**（SimHash 对 16 字中文短标题
        bit 分布不敏感，hamming 通常 8-12），改用新增 **CJK 字符级 Jaccard（去 9 个纯虚字后）≥ 0.92** 命中。
        —— 本 test 同时验证：两条仅差 1 个「的」字的临床标题，Jaccard 应该 1.0（「的」属于停用集合）。
        """
        title_a = "针刺治疗脑卒中后肩痛的随机对照研究"
        title_b = "针刺治疗脑卒中后肩痛随机对照研究"
        # 层 4 中文专用判定（Jaccard 优先走）
        j = cjk_char_jaccard(title_a, title_b)
        assert j >= CJK_JACCARD_THRESHOLD
        assert cjk_titles_near_duplicate(title_a, title_b) is True

    def test_cjk_jaccard_not_related(self):
        """中文不相关标题 Jaccard 必须 < 0.8（离 0.92 阈值足够远，零假阳性）。"""
        a = "针刺治疗脑卒中后肩痛的随机对照研究"
        b = "二甲双胍联合胰岛素治疗 2 型糖尿病疗效观察"
        assert cjk_char_jaccard(a, b) < 0.8
        assert cjk_titles_near_duplicate(a, b) is False

    def test_cjk_jaccard_below_min_chars_skip(self):
        """CJK 实字 < 4 直接返回 0.0（跳过 Jaccard）。"""
        assert cjk_char_jaccard("卒中", "脑卒中") == 0.0
        assert cjk_titles_near_duplicate("卒中", "脑卒中") is False

    def test_simhash_completely_different(self):
        a = simhash64("Cardiovascular disease prevention in elderly patients")
        b = simhash64("Surgical management of pediatric scoliosis")
        assert hamming_distance(a, b) >= 10

    def test_simhash_empty(self):
        assert simhash64("") == 0

    def test_simhash_short_title_zero(self):
        assert simhash64("Hi") == 0

    def test_simhash_same_year_near(self):
        a = simhash64("Phase 3 trial of drug X in breast cancer (2021)")
        b = simhash64("Phase 3 trial of drug X in breast cancer 2021")
        assert a == b

    def test_simhash_boundary_len10(self):
        s = "1234567890"
        assert simhash64(s) != 0
