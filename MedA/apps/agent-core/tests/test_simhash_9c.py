import pytest
from app.services.simhash import (
    _h64,
    tokenize_to_2shingles,
    simhash,
    hamming_distance,
    jaccard,
    THRESHOLDS,
)


class TestSimhash9c:
    def test_A1_identical_doc_hamming_zero(self):
        doc = "A Systematic Review of Machine Learning Applications in Clinical Medicine"
        a = simhash(doc)
        b = simhash(doc)
        assert hamming_distance(a, b) == 0

    def test_A2_completely_different_hamming_ge_20(self):
        doc_a = "Cardiovascular disease prevention strategies in elderly patients with hypertension"
        doc_b = "Surgical management of pediatric scoliosis with minimally invasive techniques"
        a = simhash(doc_a)
        b = simhash(doc_b)
        assert hamming_distance(a, b) >= 20

    def test_A3_tiny_change_hamming_le_3(self):
        doc_a = "Randomized controlled trial of metformin in type 2 diabetes"
        doc_b = "Randomized controlled trial of metformin in type 2 diabetes."
        a = simhash(doc_a)
        b = simhash(doc_b)
        assert hamming_distance(a, b) <= 3

    def test_A4_jaccard_identical_set_one(self):
        s = {"apple", "banana", "cherry", "date"}
        assert jaccard(s, s) == 1.0

    def test_A5_threshold_within_duplicate(self):
        assert 7 <= THRESHOLDS["hamming_bits_max"]
        assert 0.93 >= THRESHOLDS["jaccard_min"]
        is_dup = (7 <= THRESHOLDS["hamming_bits_max"]) and (0.93 >= THRESHOLDS["jaccard_min"])
        assert is_dup is True

    def test_A6_threshold_hamming8_not_duplicate(self):
        assert 8 > THRESHOLDS["hamming_bits_max"]
        is_dup = 8 <= THRESHOLDS["hamming_bits_max"]
        assert is_dup is False
