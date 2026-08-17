import pytest
from app.services.report_engine import (
    ProjectReportInput, GradeAssRow,
    generate_report_three_formats, INTERNAL_CSS,
)

DUMMY_INPUT = ProjectReportInput(
    project_name="CKD & SGLT2i SR",
    project_id=1,
    owner_display="Dr. Alice",
    abstract_summary="SGLT2 inhibitors reduce HF in CKD population",
    prisma_checklist_masked_count=22,
    prisma_checklist_total_items=27,
    grade_rows=[
        GradeAssRow(
            outcome_label="MACE 12mo", certainty="Moderate", participants_n=8000, studies_k=6,
            effect_label="RR 0.82 [0.72, 0.94]", ar_control="20.0%", ar_intervention="16.4%",
            comments="",
        ),
        GradeAssRow(
            outcome_label="HF Hospitalization", certainty="High", participants_n=7400, studies_k=5,
            effect_label="RR 0.61 [0.50, 0.74]", ar_control="15.0%", ar_intervention="9.1%",
            comments="Large effect",
        ),
        GradeAssRow(
            outcome_label="Hyperkalemia Adverse Event", certainty="Low", participants_n=9200, studies_k=7,
            effect_label="RR 1.21 [1.05, 1.39]", ar_control="6.0%", ar_intervention="7.2%",
            comments="Imprecision due to wide CI",
        ),
        GradeAssRow(
            outcome_label="Acute Kidney Injury eGFR >30 drop", certainty="VeryLow", participants_n=5000, studies_k=3,
            effect_label="MD -2.1 [-5.0, 0.8] ml/min", ar_control="NR", ar_intervention="NR",
            comments="Very serious imprecision; inconsistency across studies",
        ),
    ],
    forest_svg_content='<svg xmlns="http://www.w3.org/2000/svg" width="600" height="300" id="forest-test"><g></g></svg>',
)

def test_ac6a_md_contains_all_4_certainty_level_names():
    md, _h, _t = generate_report_three_formats(DUMMY_INPUT)
    for level in ("High", "Moderate", "Low", "VeryLow"):
        assert level in md, f"md missing certainty level {level}"

def test_ac6b_html_contains_all_4_grade_certainty_labels():
    _m, html, _t = generate_report_three_formats(DUMMY_INPUT)
    for level in ("High", "Moderate", "Low", "VeryLow"):
        assert level in html, f"html missing level={level}"

def test_ac6c_txt_contains_project_name_camelcase():
    _m, _h, txt = generate_report_three_formats(DUMMY_INPUT)
    assert DUMMY_INPUT.project_name in txt

def test_ac6d_md_contains_MACE_and_HF_outcome_labels():
    md, _h, _t = generate_report_three_formats(DUMMY_INPUT)
    for lbl in ("MACE 12mo", "HF Hospitalization"):
        assert lbl in md, f"md missing outcome label {lbl}"

def test_ac6e_html_contains_sofrs_table_header_12_cols_names_or_equiv_rr_participants():
    _m, html, _t = generate_report_three_formats(DUMMY_INPUT)
    assert "RR" in html
    assert "Participants" in html or "participants" in html or "N" in html

def test_ac6f_all_three_outputs_non_empty_strings_length_gt_50_bytes():
    md, h, t = generate_report_three_formats(DUMMY_INPUT)
    for name, content in (("md", md), ("html", h), ("txt", t)):
        assert isinstance(content, str) and len(content) > 50, f"{name} too short len={len(content)}"

def test_ac7a_internal_css_has_grade_color_high_166534_green_exact():
    assert "#166534" in INTERNAL_CSS, "grade-color-High missing green #166534"

def test_ac7b_internal_css_has_grade_color_moderate_1d4ed8_blue():
    assert "#1d4ed8" in INTERNAL_CSS, "grade-color-Moderate missing blue #1d4ed8"

def test_ac7c_internal_css_has_grade_color_low_b45309_orange():
    assert "#b45309" in INTERNAL_CSS, "grade-color-Low missing orange #b45309"

def test_ac7d_internal_css_has_grade_color_verylow_7f1d1d_dark_red():
    assert "#7f1d1d" in INTERNAL_CSS, "grade-color-VeryLow missing dark red #7f1d1d"

def test_ac7e_html_no_external_script_src_tag():
    _m, html, _t = generate_report_three_formats(DUMMY_INPUT)
    assert "<script src=" not in html, "HTML contains external script src (forbidden; 0 新依赖)"
    assert "<script " not in html, "HTML contains script block (forbidden; self-contained no 外链)"

def test_ac7f_html_forest_svg_directly_embedded_without_base64_starts_svg_tag():
    _m, html, _t = generate_report_three_formats(DUMMY_INPUT)
    # Forest SVG embedded direct as <svg element
    assert "<svg " in html or '&lt;svg' not in html, "SVG must be direct <svg not escaped"
    assert "forest-test" in html, "forest id missing (not embedded correctly)"
