from __future__ import annotations

from app.services.sources._cn_dict import (
    TERM_DICT,
    _clean_pubmed_tags,
    translate_boolean_for_cn_source,
)


def test_sglti2_and_rct_with_pt_tag_cleaned():
    raw = "SGLT2i[Title/Abstract] AND RCT[pt]"
    cleaned = _clean_pubmed_tags(raw)
    assert "[" not in cleaned
    assert "]" not in cleaned
    assert "Title/Abstract" not in cleaned
    translated = translate_boolean_for_cn_source(raw, source="cnki")
    assert "钠葡萄糖协同转运蛋白2抑制剂" in translated
    assert "随机对照试验" in translated
    assert "AND" in translated


def test_hfredef_and_dka_structure_preserved():
    raw = "(HFrefEF OR DKA) AND NOT placebo"
    translated = translate_boolean_for_cn_source(raw, source="wanfang")
    assert translated.startswith("(")
    assert "OR" in translated
    assert "AND NOT" in translated
    assert "安慰剂" in translated
    assert "糖尿病酮症酸中毒" in translated


def test_clean_pubmed_tags_removes_all_variants():
    variants = [
        "Metformin[Mesh]",
        "Empagliflozin[Title/Abstract]",
        "(CKD[Title] OR DKD[Abstract])",
        "T2DM[pt] AND CVD[mh]",
    ]
    for v in variants:
        out = _clean_pubmed_tags(v)
        assert "[" not in out, f"bracket left in: {out}"
        assert "]" not in out, f"bracket left in: {out}"


def test_unmapped_term_preserved_and_mapped_term_ok():
    raw = "xyzunmappedabc AND SGLT2i OR semaglutide, unknown123"
    translated = translate_boolean_for_cn_source(raw)
    assert "xyzunmappedabc" in translated
    assert "unknown123" in translated
    assert "钠葡萄糖协同转运蛋白2抑制剂" in translated
    assert "司美格鲁肽" in translated


def test_longest_boolean_sglt2i_ckd_full_pass():
    raw = (
        "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] "
        "OR Empagliflozin[Mesh] OR Dapagliflozin[Mesh]) "
        "AND (chronic kidney disease[Title] OR CKD[Abstract] "
        "OR diabetic nephropathies[mh]) "
        "AND (randomised controlled trial[pt] OR RCT[pt] "
        "OR retrospective cohort[Title]) "
        "AND NOT placebo[Title/Abstract]"
    )
    translated = translate_boolean_for_cn_source(raw, source="cnki")
    assert "钠葡萄糖协同转运蛋白2抑制剂" in translated
    assert "恩格列净" in translated
    assert "达格列净" in translated
    assert "慢性肾脏病" in translated
    assert "糖尿病肾病" in translated
    assert "随机对照试验" in translated
    assert "回顾性队列" in translated
    assert "安慰剂" in translated
    assert "AND" in translated
    assert "OR" in translated
    assert "NOT" in translated
    assert "(" in translated and ")" in translated
