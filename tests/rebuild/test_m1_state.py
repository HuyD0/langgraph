"""Milestone 1: typed state and partial updates. -> src/drill_rebuild/m1_state.py"""

from __future__ import annotations

from drill_rebuild.m1_state import DrillState, SubmissionResult, bump_attempts, merge_update


def test_state_declares_the_expected_keys():
    keys = set(DrillState.__annotations__)
    assert {"problem_id", "attempts", "max_attempts", "hints", "submission",
            "result", "feedback"} <= keys
    assert "_placeholder" not in keys, "replace the placeholder with the real keys"


def test_result_declares_the_expected_keys():
    keys = set(SubmissionResult.__annotations__)
    assert {"passed", "total", "passed_count", "fatal_error"} <= keys
    assert "_placeholder" not in keys


def test_state_keys_are_optional():
    """total=False is what lets a node return one key instead of the whole dict."""
    assert DrillState.__total__ is False


def test_update_overwrites_matching_keys():
    assert merge_update({"attempts": 1}, {"attempts": 2})["attempts"] == 2


def test_untouched_keys_survive():
    merged = merge_update({"problem_id": "two_sum", "attempts": 1}, {"attempts": 2})
    assert merged["problem_id"] == "two_sum"


def test_new_keys_are_added():
    assert merge_update({"attempts": 1}, {"feedback": "nice"})["feedback"] == "nice"


def test_empty_update_changes_nothing():
    state = {"attempts": 1, "hints": []}
    assert merge_update(state, {}) == state


def test_the_original_state_is_not_mutated():
    """LangGraph keeps old states for checkpointing. Mutating one corrupts history."""
    state = {"attempts": 1}
    merge_update(state, {"attempts": 99})
    assert state["attempts"] == 1


def test_merge_returns_a_new_object():
    state = {"attempts": 1}
    assert merge_update(state, {}) is not state


def test_bump_returns_only_the_changed_key():
    assert bump_attempts({"attempts": 1, "problem_id": "two_sum"}) == {"attempts": 2}


def test_bump_treats_a_missing_count_as_zero():
    assert bump_attempts({}) == {"attempts": 1}
