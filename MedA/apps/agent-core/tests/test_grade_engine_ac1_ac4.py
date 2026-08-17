import pytest
from app.services.grade_engine import (
    Grade5Domains, Grade3Upgrades, compute_certainty_final,
    DOWNGRADE_TABLE_STR, UPGRADE_TABLE_STR,
)

DOM5_NONE = Grade5Domains(
    risk_of_bias="no_concerns", indirectness="no_concerns",
    inconsistency="no_concerns", imprecision="no_concerns",
    publication_bias="no_concerns",
)
UP3_NONE = Grade3Upgrades(large_effect=False, dose_response=False, confounders_reduce=False)
UP3_LE1 = Grade3Upgrades(large_effect=True, dose_response=False, confounders_reduce=False)
UP3_ALL  = Grade3Upgrades(large_effect=True, dose_response=True,  confounders_reduce=True)

def downgrade_only(*, r, ind, inc, imp, pub):
    return Grade5Domains(
        risk_of_bias=r, indirectness=ind, inconsistency=inc,
        imprecision=imp, publication_bias=pub,
    )

SOME = "some_concerns"
MAJR = "major_concerns"
NO   = "no_concerns"

def test_ac1_all_no_upgrade_none_gives_HIGH():
    assert compute_certainty_final(DOM5_NONE, UP3_NONE, start="High") == "High"

def test_ac2_some_roB_0_upgrade_gives_MODERATE():
    d = downgrade_only(r=SOME, ind=NO, inc=NO, imp=NO, pub=NO)
    assert compute_certainty_final(d, UP3_NONE, start="High") == "Moderate"

def test_ac3_two_some_0_upgrade_gives_LOW():
    d = downgrade_only(r=SOME, ind=SOME, inc=NO, imp=NO, pub=NO)
    assert compute_certainty_final(d, UP3_NONE, start="High") == "Low"
def test_ac3_two_some_plus_large_effect_gives_MODERATE():
    d = downgrade_only(r=SOME, ind=SOME, inc=NO, imp=NO, pub=NO)
    assert compute_certainty_final(d, UP3_LE1, start="High") == "Moderate"

def test_ac4_major_x2_some_x2_score6_gives_VERYLOW():
    d = downgrade_only(r=MAJR, ind=SOME, inc=SOME, imp=MAJR, pub=NO)
    assert compute_certainty_final(d, UP3_NONE, start="High") == "VeryLow"
def test_ac4_verylow_plus_three_upgrade_gives_HIGH_cap():
    d = downgrade_only(r=MAJR, ind=SOME, inc=SOME, imp=MAJR, pub=NO)
    assert compute_certainty_final(d, UP3_ALL, start="High") == "High"

def test_cover_start_high_td_01():
    assert compute_certainty_final(downgrade_only(r=NO,ind=NO,inc=NO,imp=NO,pub=SOME), UP3_NONE, "High") == "Moderate"
def test_cover_start_high_td_02():
    assert compute_certainty_final(downgrade_only(r=SOME,ind=NO,inc=SOME,imp=NO,pub=NO), UP3_NONE, "High") == "Low"
def test_cover_start_high_td_03():
    assert compute_certainty_final(downgrade_only(r=SOME,ind=SOME,inc=SOME,imp=NO,pub=NO), UP3_NONE, "High") == "VeryLow"
def test_cover_start_high_td_04():
    assert compute_certainty_final(downgrade_only(r=MAJR,ind=SOME,inc=SOME,imp=SOME,pub=SOME), UP3_NONE, "High") == "VeryLow"
def test_cover_start_high_td_05():
    assert compute_certainty_final(downgrade_only(r=NO,ind=MAJR,inc=NO,imp=NO,pub=MAJR), UP3_NONE, "High") == "VeryLow"
def test_cover_start_moderate_td_06():
    assert compute_certainty_final(downgrade_only(r=SOME,ind=NO,inc=NO,imp=NO,pub=NO), UP3_NONE, "Moderate") == "Low"
def test_cover_start_moderate_td_07():
    assert compute_certainty_final(downgrade_only(r=SOME,ind=SOME,inc=NO,imp=NO,pub=NO), UP3_NONE, "Moderate") == "VeryLow"
def test_cover_start_low_td_08():
    assert compute_certainty_final(downgrade_only(r=SOME,ind=NO,inc=NO,imp=NO,pub=NO), UP3_NONE, "Low") == "VeryLow"
def test_cover_start_verylow_td_09():
    assert compute_certainty_final(downgrade_only(r=MAJR,ind=MAJR,inc=MAJR,imp=MAJR,pub=MAJR), UP3_NONE, "VeryLow") == "VeryLow"

def test_cov_up_vl_1():
    d = downgrade_only(r=MAJR,ind=SOME,inc=SOME,imp=MAJR,pub=NO)
    up = Grade3Upgrades(True,False,False)
    assert compute_certainty_final(d, up, "High") == "Low"
def test_cov_up_vl_2():
    d = downgrade_only(r=MAJR,ind=SOME,inc=SOME,imp=MAJR,pub=NO)
    up = Grade3Upgrades(True,True,False)
    assert compute_certainty_final(d, up, "High") == "Moderate"
def test_cov_up_vl_3():
    d = downgrade_only(r=MAJR,ind=SOME,inc=SOME,imp=MAJR,pub=NO)
    assert compute_certainty_final(d, UP3_ALL, "High") == "High"
def test_cov_up_low_1():
    d = downgrade_only(r=SOME,ind=SOME,inc=NO,imp=NO,pub=NO)
    up = Grade3Upgrades(True,False,False)
    assert compute_certainty_final(d, up, "High") == "Moderate"
def test_cov_up_low_2():
    d = downgrade_only(r=SOME,ind=SOME,inc=NO,imp=NO,pub=NO)
    up = Grade3Upgrades(True,True,False)
    assert compute_certainty_final(d, up, "High") == "High"
def test_cov_up_low_3():
    d = downgrade_only(r=SOME,ind=SOME,inc=NO,imp=NO,pub=NO)
    assert compute_certainty_final(d, UP3_ALL, "High") == "High"
def test_cov_up_moderate_1():
    d = downgrade_only(r=SOME,ind=NO,inc=NO,imp=NO,pub=NO)
    up = Grade3Upgrades(True,False,False)
    assert compute_certainty_final(d, up, "High") == "High"
def test_cov_up_high_no_upgrade_possible():
    up = UP3_ALL
    assert compute_certainty_final(DOM5_NONE, up, "High") == "High"
def test_cov_start_low_double_some_clamp_verylow():
    d = downgrade_only(r=SOME,ind=SOME,inc=NO,imp=NO,pub=NO)
    assert compute_certainty_final(d, UP3_NONE, "Low") == "VeryLow"
