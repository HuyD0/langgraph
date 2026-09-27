"""Milestone 3 answer key - the branching policy."""

from __future__ import annotations


def route_after_tests(state: dict) -> str:
    """Decide what happens after a submission has been graded.

    Order matters. Checking ``passed`` first is what makes solving it on the final
    attempt still count as solved; testing the attempt budget first would route a
    last-second pass to ``explain``.

    ``state.get("result") or {}`` rather than ``state.get("result", {})``: the key
    may be present and None, and only the former handles that.
    """
    result = state.get("result") or {}
    if result.get("passed"):
        return "review"
    if state.get("attempts", 0) >= state.get("max_attempts", 3):
        return "explain"
    return "hint"
