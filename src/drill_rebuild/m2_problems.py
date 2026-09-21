"""Milestone 2 - modelling a problem, and looking one up.

Run: uv run pytest tests/rebuild/test_m2_problems.py

WHY THIS MATTERS
Interviewers watch how you model data before you write logic. A good dataclass
makes the rest of the code obvious; a dict-of-dicts makes every later function
defensive. This milestone is small on purpose - the lesson is in the details,
especially the error message.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TestCase:
    """One input/output pair.

    TODO: give this three fields:
        args      tuple[Any, ...]  - positional arguments to call the function with
        expected  Any              - what it must return
        is_sample bool             - shown to the learner up front; default False

    `frozen=True` makes instances immutable and hashable. Keep it: a test case
    that can be edited after construction is a bug waiting to happen.
    """

    # Tells pytest this is a data class, not a test class to collect.
    # Without it, the name "TestCase" trips pytest's test-discovery heuristic.
    __test__ = False


@dataclass(frozen=True)
class Problem:
    """One interview problem.

    TODO: give this at least these fields:
        id             str
        title          str
        topic          str
        difficulty     str
        function_name  str
        test_cases     tuple[TestCase, ...]

    Then add two properties:
        samples -> tuple[TestCase, ...]   only the cases with is_sample True
        hidden  -> tuple[TestCase, ...]   only the cases with is_sample False

    Why both: samples teach the format, hidden cases stop you passing by
    special-casing the examples. An interviewer holds some tests back too.
    """


def build_index(problems: tuple[Problem, ...]) -> dict[str, Problem]:
    """Build an id -> Problem lookup table.

    TODO: implement. Raise ValueError if two problems share an id - a duplicate
    would silently shadow one of them, and you would lose an afternoon to it.
    """
    raise NotImplementedError("Milestone 2: implement build_index")


def get_problem(index: dict[str, Problem], problem_id: str) -> Problem:
    """Look up one problem by id.

    On a miss, raise KeyError whose message lists the available ids. Compare:

        KeyError: 'two-sum'
        KeyError: "No problem with id 'two-sum'. Available: two_sum, binary_search, ..."

    The second one costs you two extra lines and saves every future user - you
    included - a trip into the source. Error messages are a design surface.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 2: implement get_problem")


def filter_problems(
    problems: tuple[Problem, ...],
    topic: str | None = None,
    difficulty: str | None = None,
) -> tuple[Problem, ...]:
    """Filter by topic and/or difficulty.

    Both arguments are optional and combine with AND. Passing neither returns
    everything. Return a tuple, not a list.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 2: implement filter_problems")
