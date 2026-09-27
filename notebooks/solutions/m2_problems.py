"""Milestone 2 answer key - dataclasses and lookup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TestCase:
    # Tells pytest this is a data class, not a test class to collect.
    __test__ = False

    args: tuple[Any, ...]
    expected: Any
    is_sample: bool = False


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    topic: str
    difficulty: str
    function_name: str
    test_cases: tuple[TestCase, ...]

    @property
    def samples(self) -> tuple[TestCase, ...]:
        return tuple(c for c in self.test_cases if c.is_sample)

    @property
    def hidden(self) -> tuple[TestCase, ...]:
        return tuple(c for c in self.test_cases if not c.is_sample)


def build_index(problems: tuple) -> dict:
    """Map id -> Problem, refusing duplicates.

    The duplicate check is the point. A dict comprehension would silently keep the
    last of two problems sharing an id, and you would lose an afternoon to it.
    """
    index: dict = {}
    for problem in problems:
        if problem.id in index:
            raise ValueError(f"Duplicate problem id: {problem.id!r}")
        index[problem.id] = problem
    return index


def get_problem(index: dict, problem_id: str):
    """Look up one problem, listing the valid ids on a miss.

    ``from None`` suppresses the chained "During handling of the above exception"
    noise, so the reader sees the useful message and not the plumbing.
    """
    try:
        return index[problem_id]
    except KeyError:
        raise KeyError(
            f"No problem with id {problem_id!r}. Available: {', '.join(index)}"
        ) from None


def filter_problems(problems: tuple, topic: str | None = None, difficulty: str | None = None) -> tuple:
    """Filter by topic and/or difficulty, combining with AND."""
    out = tuple(problems)
    if topic:
        out = tuple(p for p in out if p.topic == topic)
    if difficulty:
        out = tuple(p for p in out if p.difficulty == difficulty)
    return out
