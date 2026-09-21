"""The tutor's core policy is one pure function. Test it like one.

No graph, no model, no I/O - which is exactly why the routing logic was worth
pulling out of the nodes in the first place.
"""

from __future__ import annotations

import pytest

from drill.nodes import route_after_tests


def state(passed: bool, attempts: int, max_attempts: int = 3) -> dict:
    return {"result": {"passed": passed}, "attempts": attempts, "max_attempts": max_attempts}


def test_passing_goes_to_review():
    assert route_after_tests(state(True, 1)) == "review"


def test_passing_on_the_last_attempt_still_reviews():
    """Solving it on the final try is solving it, not running out of tries."""
    assert route_after_tests(state(True, 3)) == "review"


@pytest.mark.parametrize("attempts", [1, 2])
def test_failing_with_attempts_left_goes_to_hint(attempts):
    assert route_after_tests(state(False, attempts)) == "hint"


@pytest.mark.parametrize("attempts", [3, 4])
def test_failing_out_of_attempts_goes_to_explain(attempts):
    assert route_after_tests(state(False, attempts)) == "explain"


def test_missing_result_is_treated_as_a_failure():
    """A node that never ran must not be mistaken for a pass."""
    assert route_after_tests({"attempts": 1, "max_attempts": 3}) == "hint"


def test_max_attempts_is_configurable():
    assert route_after_tests(state(False, 3, max_attempts=5)) == "hint"
    assert route_after_tests(state(False, 5, max_attempts=5)) == "explain"
