"""Milestone 1 - the state a graph passes between its nodes.

Run: uv run pytest tests/rebuild/test_m1_state.py

WHY THIS COMES FIRST
Every node in a LangGraph app is a function that takes the state and returns a
*partial* update - just the keys it changed. LangGraph merges that update into the
state for you. Once that clicks, the rest of the framework is bookkeeping.

WHAT TO DO
Fill in the two TypedDicts below, then implement `merge_update`, which is a
simplified version of what LangGraph does internally on every node return.
"""

from __future__ import annotations

from typing import Any, TypedDict


class SubmissionResult(TypedDict, total=False):
    """The outcome of running one submission against a problem's test cases.

    TODO: give this the following keys, with these types:
        passed        bool   - did every case pass?
        total         int    - how many cases ran
        passed_count  int    - how many passed
        fatal_error   str | None - set when the code did not run at all
    """

    # TODO: replace this with the real keys.
    _placeholder: Any


class DrillState(TypedDict, total=False):
    """State for one practice session.

    TODO: give this the following keys:
        problem_id   str
        attempts     int
        max_attempts int
        hints        list[str]
        submission   str
        result       SubmissionResult
        feedback     str

    `total=False` means every key is optional. That is what lets a node return
    `{"attempts": 2}` instead of rebuilding the whole dict - so keep it.
    """

    # TODO: replace this with the real keys.
    _placeholder: Any


def merge_update(state: dict, update: dict) -> dict:
    """Merge a node's partial update into the state and return the new state.

    This is the heart of how a graph accumulates work. Requirements:

    - Return a NEW dict. Never mutate `state` - a caller may still be holding it,
      and LangGraph relies on old states staying intact for checkpointing.
    - Keys in `update` overwrite keys in `state`.
    - Keys absent from `update` are carried through unchanged.
    - An empty update returns an equal copy of the state.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 1: implement merge_update")


def bump_attempts(state: dict) -> dict:
    """Return the partial update that records one more attempt.

    Should return exactly `{"attempts": <one more than the current count>}`, and
    treat a missing `attempts` key as 0.

    Note it returns *only* the changed key - not the whole state. That is the
    convention every node in this project follows.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 1: implement bump_attempts")
