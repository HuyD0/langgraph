"""Milestone 3: the branching policy. -> src/drill_rebuild/m3_routing.py"""

from __future__ import annotations

import pytest

from drill_rebuild.m3_routing import route_after_tests


def state(passed: bool, attempts: int, max_attempts: int = 3) -> dict:
    return {"result": {"passed": passed}, "attempts": attempts, "max_attempts": max_attempts}


def test_passing_routes_to_review():
    assert route_after_tests(state(True, 1)) == "review"


def test_passing_on_the_last_attempt_still_reviews():
    assert route_after_tests(state(True, 3)) == "review"


@pytest.mark.parametrize("attempts", [1, 2])
def test_failing_with_attempts_left_routes_to_hint(attempts):
    assert route_after_tests(state(False, attempts)) == "hint"


@pytest.mark.parametrize("attempts", [3, 4])
def test_failing_out_of_attempts_routes_to_explain(attempts):
    assert route_after_tests(state(False, attempts)) == "explain"


def test_a_missing_result_is_a_failure_not_a_pass():
    assert route_after_tests({"attempts": 1, "max_attempts": 3}) == "hint"


def test_max_attempts_is_read_from_the_state():
    assert route_after_tests(state(False, 3, max_attempts=5)) == "hint"
    assert route_after_tests(state(False, 5, max_attempts=5)) == "explain"


def test_max_attempts_defaults_to_three():
    assert route_after_tests({"result": {"passed": False}, "attempts": 3}) == "explain"


def test_only_the_three_known_values_are_returned():
    assert route_after_tests(state(True, 1)) in {"review", "hint", "explain"}
