"""Milestone 1 answer key - typed state and partial updates."""

from __future__ import annotations

from typing import Any, TypedDict


class SubmissionResult(TypedDict, total=False):
    passed: bool
    total: int
    passed_count: int
    fatal_error: str | None


class DrillState(TypedDict, total=False):
    problem_id: str
    attempts: int
    max_attempts: int
    hints: list[str]
    submission: str
    result: SubmissionResult
    feedback: str


def merge_update(state: dict, update: dict) -> dict:
    """Merge a partial update into the state, returning a new dict.

    ``{**a, **b}`` builds a new dict with b's keys winning - which is both the
    shortest way to say it and the reason the original is never mutated.
    """
    return {**state, **update}


def bump_attempts(state: dict) -> dict:
    """Return only the changed key, which is the convention every node follows."""
    return {"attempts": state.get("attempts", 0) + 1}
