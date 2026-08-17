from __future__ import annotations

class OutputStageError(Exception):
    pass

def _simulate_rule_O1(*, locked: bool, touch: str) -> None:
    if locked and touch in {"domains_5", "upgrades_3", "certainty_final"}:
        raise OutputStageError("grade_locked_cannot_change_assessment")

def _simulate_rule_O2(*, has_meta: bool) -> None:
    if not has_meta:
        raise OutputStageError("grade_requires_completed_meta_analysis")

def _simulate_rule_O5(*, grade_count: int) -> None:
    if grade_count <= 0:
        raise OutputStageError("report_requires_at_least_one_grade_assessment")

def _simulate_rule_O6_incomplete(*, md: str, html: str, txt: str) -> None:
    if not (md and html and txt):
        raise OutputStageError("report_snapshot_incomplete_missing_content_sections")

def _simulate_rule_O7(*, locked: bool) -> None:
    if locked:
        raise OutputStageError("prisma_checklist_locked_cannot_change_items")

def _simulate_rule_O8(*, keys_count: int) -> None:
    if keys_count != 5:
        raise OutputStageError("grade_invalid_domain_count_require_exact_5_keys")

from dataclasses import dataclass as _dcdataclass

OUTPUT_3_CARD_KEYS = (
    "protocol_report_draft",
    "sof_attachments_ready",
    "export_version_snapshots_ready",
)

@_dcdataclass(frozen=True, slots=True)
class OutputStageCard:
    card_key: str
    ready: bool
    locked_reason: str | None = None

def build_output_stage_cards_3(
    *,
    grade_count: int,
    prisma_items_checked: int,
    sof_rows: int,
    studies_k_any_outcome: int,
    snap_count: int,
) -> list[OutputStageCard]:
    cards: list[OutputStageCard] = []
    # Card 1 — protocol_report_draft
    ready_1 = (grade_count >= 1 and prisma_items_checked >= 5)
    cards.append(OutputStageCard(
        card_key="protocol_report_draft",
        ready=ready_1,
        locked_reason=None if ready_1 else "protocol_requires_grade_and_prisma_5_items",
    ))
    # Card 2 — sof_attachments_ready
    ready_2 = (sof_rows >= 1 and studies_k_any_outcome >= 3)
    cards.append(OutputStageCard(
        card_key="sof_attachments_ready",
        ready=ready_2,
        locked_reason=None if ready_2 else "attachments_requires_sof_row_and_forest_3_studies",
    ))
    # Card 3 — export_version_snapshots_ready
    ready_3 = (snap_count >= 1)
    cards.append(OutputStageCard(
        card_key="export_version_snapshots_ready",
        ready=ready_3,
        locked_reason=None if ready_3 else "exports_requires_at_least_one_report_snapshot",
    ))
    return cards
