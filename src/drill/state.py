"""The graph's state: the single dict every node reads from and writes to.

If you only learn one LangGraph idea, make it this one. A graph is a set of
functions that each take the state and return a *partial* update to it. LangGraph
merges each update into the state and passes it to the next node. Nodes never call
each other directly, which is what makes the flow easy to test and to draw.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

# What the tutor decided to do after grading a submission. Kept as a closed set of
# strings so the conditional edge in graph.py cannot route somewhere that has no node.
Verdict = Literal["solved", "hint", "explain"]


class CaseResult(TypedDict):
    """Outcome of running one test case against a submitted solution."""

    args: list[Any]
    expected: Any
    actual: Any
    passed: bool
    error: str | None


class SubmissionResult(TypedDict):
    """Outcome of running the whole test suite against one submission."""

    passed: bool
    total: int
    passed_count: int
    cases: list[CaseResult]
    # Set when the code never ran at all: syntax error, missing function, timeout.
    fatal_error: str | None
    timed_out: bool
    duration_s: float


class DrillState(TypedDict, total=False):
    """State for one practice session on one problem.

    ``total=False`` means every key is optional, so nodes can return small partial
    updates (``{"attempts": 2}``) instead of rebuilding the whole dict each time.
    """

    # --- set when the session starts -------------------------------------------
    problem_id: str
    topic: str | None

    # --- the learner's work ------------------------------------------------------
    submission: str
    attempts: int
    max_attempts: int

    # --- grading -----------------------------------------------------------------
    result: SubmissionResult
    verdict: Verdict

    # --- what the tutor says back --------------------------------------------------
    hints: list[str]
    feedback: str

    # --- bookkeeping ----------------------------------------------------------------
    started_at: float
    finished_at: float
