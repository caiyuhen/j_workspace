from __future__ import annotations

import pytest

from app.services.sources.protocol import NormalizedSearchQuery


def _clamp_max_pages_cn(value: int | None) -> int:
    if value is None:
        return 1
    return max(1, min(3, value))


class TestMaxPagesCnLiteralAccepts123Only:
    def test_valid_values_1_2_3_are_accepted(self) -> None:
        for valid in (1, 2, 3):
            q = NormalizedSearchQuery(
                boolean_text="test",
                filters={},
                source_key="cnki",
                max_pages_cn=valid,
            )
            assert q.max_pages_cn == valid

    def test_invalid_values_raise_error(self) -> None:
        for invalid in (0, 4, 5, 10, -1):
            with pytest.raises((ValueError, TypeError)):
                NormalizedSearchQuery(
                    boolean_text="test",
                    filters={},
                    source_key="cnki",
                    max_pages_cn=invalid,
                )


class TestDefaultMaxPagesCnIsNoneAndClampBehavesLike1:
    def test_default_max_pages_cn_is_none(self) -> None:
        q = NormalizedSearchQuery(
            boolean_text="test",
            filters={},
            source_key="cnki",
        )
        assert q.max_pages_cn is None

    def test_none_clamps_to_1_and_valid_values_clamp_in_range(self) -> None:
        assert _clamp_max_pages_cn(None) == 1
        assert _clamp_max_pages_cn(1) == 1
        assert _clamp_max_pages_cn(2) == 2
        assert _clamp_max_pages_cn(3) == 3

    def test_existing_calls_without_max_pages_cn_still_work(self) -> None:
        q = NormalizedSearchQuery(
            boolean_text="Metformin[Mesh]",
            filters={"language": ["english"]},
            source_key="pubmed",
        )
        assert q.source_key == "pubmed"
        assert q.boolean_text == "Metformin[Mesh]"
        assert q.max_pages_cn is None
