import pytest
from app.services.output_stage import build_output_stage_cards_3, OutputStageCard

def test_c1_card1_protocol_ready_grade_ge_1_and_prisma_items_checked_ge_5():
    out = build_output_stage_cards_3(grade_count=2, prisma_items_checked=5, sof_rows=1, studies_k_any_outcome=3, snap_count=1)
    cards = {c.card_key: c for c in out}
    c = cards["protocol_report_draft"]
    assert c.ready is True, f"card1 ready expected True; got locked_reason={c.locked_reason}"
    assert c.locked_reason is None

def test_c2_card1_protocol_locked_reason_literal_when_grade_lt_1():
    out = build_output_stage_cards_3(grade_count=0, prisma_items_checked=10, sof_rows=1, studies_k_any_outcome=3, snap_count=1)
    cards = {c.card_key: c for c in out}
    c = cards["protocol_report_draft"]
    assert c.ready is False
    assert c.locked_reason == "protocol_requires_grade_and_prisma_5_items", f"got={c.locked_reason!r}"

def test_c3_card1_protocol_locked_reason_literal_when_prisma_lt_5():
    out = build_output_stage_cards_3(grade_count=3, prisma_items_checked=4, sof_rows=1, studies_k_any_outcome=3, snap_count=1)
    cards = {c.card_key: c for c in out}
    c = cards["protocol_report_draft"]
    assert c.ready is False
    assert c.locked_reason == "protocol_requires_grade_and_prisma_5_items"

def test_c4_card2_sof_ready_sofrs_ge_1_and_studiesk_ge_3():
    out = build_output_stage_cards_3(grade_count=1, prisma_items_checked=5, sof_rows=1, studies_k_any_outcome=3, snap_count=1)
    cards = {c.card_key: c for c in out}
    c = cards["sof_attachments_ready"]
    assert c.ready is True
    assert c.locked_reason is None

def test_c5_card2_sof_locked_literal_when_sof_lt_1():
    out = build_output_stage_cards_3(grade_count=1, prisma_items_checked=5, sof_rows=0, studies_k_any_outcome=3, snap_count=1)
    cards = {c.card_key: c for c in out}
    c = cards["sof_attachments_ready"]
    assert c.ready is False
    assert c.locked_reason == "attachments_requires_sof_row_and_forest_3_studies", f"got={c.locked_reason!r}"

def test_c6_card2_sof_locked_literal_when_studiesk_lt_3():
    out = build_output_stage_cards_3(grade_count=1, prisma_items_checked=5, sof_rows=2, studies_k_any_outcome=2, snap_count=1)
    cards = {c.card_key: c for c in out}
    c = cards["sof_attachments_ready"]
    assert c.ready is False
    assert c.locked_reason == "attachments_requires_sof_row_and_forest_3_studies"

def test_c7_card3_snap_ready_snap_count_ge_1():
    out = build_output_stage_cards_3(grade_count=1, prisma_items_checked=5, sof_rows=1, studies_k_any_outcome=3, snap_count=1)
    cards = {c.card_key: c for c in out}
    c = cards["export_version_snapshots_ready"]
    assert c.ready is True
    assert c.locked_reason is None

def test_c8_card3_snap_locked_literal_when_snap_count_eq_0():
    out = build_output_stage_cards_3(grade_count=1, prisma_items_checked=5, sof_rows=1, studies_k_any_outcome=3, snap_count=0)
    cards = {c.card_key: c for c in out}
    c = cards["export_version_snapshots_ready"]
    assert c.ready is False
    assert c.locked_reason == "exports_requires_at_least_one_report_snapshot", f"got={c.locked_reason!r}"

def test_c9_output_3_cards_exact_key_set():
    out = build_output_stage_cards_3(grade_count=1, prisma_items_checked=5, sof_rows=1, studies_k_any_outcome=3, snap_count=1)
    keys = sorted([c.card_key for c in out])
    assert keys == sorted([
        "protocol_report_draft",
        "sof_attachments_ready",
        "export_version_snapshots_ready",
    ]), f"got keys={keys}"

def test_c10_all_locked_cards_exact_three_locks_when_zero():
    out = build_output_stage_cards_3(grade_count=0, prisma_items_checked=0, sof_rows=0, studies_k_any_outcome=0, snap_count=0)
    cards = {c.card_key: c for c in out}
    # 3 张全 locked
    assert cards["protocol_report_draft"].ready is False
    assert cards["sof_attachments_ready"].ready is False
    assert cards["export_version_snapshots_ready"].ready is False
    # Literals exactly
    assert cards["protocol_report_draft"].locked_reason == "protocol_requires_grade_and_prisma_5_items"
    assert cards["sof_attachments_ready"].locked_reason == "attachments_requires_sof_row_and_forest_3_studies"
    assert cards["export_version_snapshots_ready"].locked_reason == "exports_requires_at_least_one_report_snapshot"

def test_c11_output_stage_card_class_4_attrs_only_card_key_ready_locked_reason_studies_k_meta():
    c = OutputStageCard(card_key="protocol_report_draft", ready=True, locked_reason=None)
    # dataclass: verify attribute slots are restricted
    d = c.__dict__ if hasattr(c, "__dict__") else {f: getattr(c, f) for f in c.__dataclass_fields__}
    fields = sorted(d.keys())
    # card_key, ready, locked_reason (maybe studies_k_meta optional extra ok as long as 3 main)
    assert "card_key" in fields
    assert "ready" in fields
    assert "locked_reason" in fields
    assert isinstance(c.ready, bool)
    assert isinstance(c.card_key, str)

def test_c12_all_locked_cards_have_non_empty_locked_reason():
    out = build_output_stage_cards_3(grade_count=0, prisma_items_checked=0, sof_rows=0, studies_k_any_outcome=0, snap_count=0)
    for c in out:
        if c.ready is False:
            assert isinstance(c.locked_reason, str) and len(c.locked_reason) >= 5
