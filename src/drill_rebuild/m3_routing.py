"""Milestone 3 - the tutor's branching policy.

Run: uv run pytest tests/rebuild/test_m3_routing.py

WHY THIS MATTERS
This one function decides everything about how the tutor feels: how long it lets
you struggle, and when it gives up and explains. It is also the clearest example
in the project of a decision worth isolating - no model call, no I/O, so it is
trivially testable and you can reason about it completely.
"""

from __future__ import annotations


def route_after_tests(state: dict) -> str:
    """Decide what happens after a submission has been graded.

    Return exactly one of these strings:

        "review"   the tests passed - critique the working solution
        "hint"     the tests failed and attempts remain - nudge them
        "explain"  the tests failed and attempts are used up - walk them through it

    Read the state from these keys:
        state["result"]["passed"]   bool  (may be missing entirely)
        state["attempts"]           int   (may be missing)
        state["max_attempts"]       int   (may be missing; default to 3)

    Three details the tests check, each of which is a real bug if you miss it:

    1. Passing on the FINAL attempt still routes to "review". Solving it on the
       last try is solving it.
    2. A missing `result` means the grader never ran, which is a failure - it must
       not be read as a pass.
    3. `max_attempts` comes from the state, not a hard-coded 3, so it stays
       configurable.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 3: implement route_after_tests")
