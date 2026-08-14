import pytest


@pytest.mark.needs_network
def test_foo_marked_runs_when_flag_passed():
    assert 1 + 1 == 2


def test_bar_unmarked_always_runs():
    assert True


@pytest.mark.needs_network
def test_baz_marked_also_skips_without_flag():
    assert 2 + 2 == 4
