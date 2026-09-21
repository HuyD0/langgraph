"""The problem bank must be internally consistent.

The load-bearing test here is `test_reference_solution_passes`: it runs every
reference solution against its own test cases. Add a problem with a typo in the
expected output and this catches it immediately, rather than you discovering it
mid-session when the tutor insists your correct answer is wrong.
"""

from __future__ import annotations

import pytest

from drill.problems import ALL_PROBLEMS, TOPICS, get_problem, list_problems, problem_ids
from drill.sandbox import run_submission

ALL_IDS = [p.id for p in ALL_PROBLEMS]


@pytest.mark.parametrize("problem", ALL_PROBLEMS, ids=ALL_IDS)
def test_reference_solution_passes(problem):
    result = run_submission(problem, problem.reference_solution, timeout=30)
    assert result["fatal_error"] is None, result["fatal_error"]
    assert result["passed"], (
        f"{problem.id}: only {result['passed_count']}/{result['total']} cases passed. "
        f"First failure: {[c for c in result['cases'] if not c['passed']][:1]}"
    )


@pytest.mark.parametrize("problem", ALL_PROBLEMS, ids=ALL_IDS)
def test_starter_code_does_not_pass(problem):
    """The stub must not accidentally solve the problem, or there is nothing to do."""
    result = run_submission(problem, problem.starter_code, timeout=30)
    assert not result["passed"]


@pytest.mark.parametrize("problem", ALL_PROBLEMS, ids=ALL_IDS)
def test_problem_is_well_formed(problem):
    assert problem.id and problem.title and problem.prompt
    assert problem.difficulty in {"easy", "medium", "hard"}
    assert problem.samples, f"{problem.id} has no sample case to show the learner"
    assert problem.hidden, f"{problem.id} has no hidden cases, so samples can be special-cased"
    assert problem.function_name in problem.starter_code
    assert problem.function_name in problem.reference_solution


def test_ids_are_unique():
    assert len(ALL_IDS) == len(set(ALL_IDS))


def test_get_problem_roundtrips():
    for pid in problem_ids():
        assert get_problem(pid).id == pid


def test_get_problem_lists_options_on_typo():
    with pytest.raises(KeyError, match="two_sum"):
        get_problem("two-sum")


def test_list_problems_filters():
    assert all(p.topic == "hash-map" for p in list_problems(topic="hash-map"))
    assert all(p.difficulty == "easy" for p in list_problems(difficulty="easy"))
    assert list_problems(topic="nonexistent") == ()


def test_topics_are_covered():
    """Several distinct patterns, so weakest-topic selection has somewhere to go."""
    assert len(TOPICS) >= 5
