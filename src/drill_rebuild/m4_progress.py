"""Milestone 4 - reading your own practice history.

Run: uv run pytest tests/rebuild/test_m4_progress.py

WHY THIS MATTERS
This is the aggregate-and-rank shape that turns up constantly in interviews:
group records by a key, compute a rate per group, pick the extreme. The twist is
the tie-break, which is where most first drafts are subtly wrong.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AttemptRecord:
    """One finished session."""

    problem_id: str
    topic: str
    solved: bool
    attempts: int


def stats_by_topic(history: list[AttemptRecord]) -> dict[str, dict[str, int]]:
    """Aggregate a history into per-topic counts.

    Return a dict shaped like::

        {"hash-map": {"attempted": 3, "solved": 2}, "stack": {"attempted": 1, "solved": 0}}

    An empty history returns an empty dict - not a dict of zeros.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 4: implement stats_by_topic")


def weakest_topic(history: list[AttemptRecord]) -> str | None:
    """Return the topic you are worst at, or None if the history is empty.

    "Worst" means the lowest solved/attempted ratio.

    The tie-break is the interesting part: when two topics have the same ratio,
    prefer the one you have practised LESS. Without that rule, a topic you tried
    once and failed ranks equal with one you failed ten times, and selection can
    get stuck on the well-explored one. Sorting by a tuple gets you both rules at
    once - think about what that tuple contains.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 4: implement weakest_topic")


def unsolved_ids(history: list[AttemptRecord], all_ids: list[str]) -> list[str]:
    """Return the ids from `all_ids` that have never been solved.

    A problem counts as solved if ANY record for it has solved=True - failing it
    twice and then solving it means you solved it. Preserve the order of `all_ids`.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 4: implement unsolved_ids")
