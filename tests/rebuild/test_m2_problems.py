"""Milestone 2: dataclasses and lookup. -> src/drill_rebuild/m2_problems.py"""

from __future__ import annotations

import dataclasses

import pytest

from drill_rebuild.m2_problems import (
    Problem, TestCase, build_index, filter_problems, get_problem,
)


def make(pid: str, topic: str = "hash-map", difficulty: str = "easy") -> Problem:
    return Problem(
        id=pid, title=pid.title(), topic=topic, difficulty=difficulty,
        function_name=pid,
        test_cases=(
            TestCase(args=(1,), expected=1, is_sample=True),
            TestCase(args=(2,), expected=2),
        ),
    )


def test_testcase_defaults_to_hidden():
    assert TestCase(args=(1,), expected=1).is_sample is False


def test_dataclasses_are_frozen():
    case = TestCase(args=(1,), expected=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        case.expected = 2  # type: ignore[misc]


def test_samples_and_hidden_partition_the_cases():
    problem = make("two_sum")
    assert len(problem.samples) == 1 and problem.samples[0].is_sample
    assert len(problem.hidden) == 1 and not problem.hidden[0].is_sample
    assert len(problem.samples) + len(problem.hidden) == len(problem.test_cases)


def test_index_maps_id_to_problem():
    problems = (make("a"), make("b"))
    index = build_index(problems)
    assert index["a"] is problems[0] and index["b"] is problems[1]


def test_duplicate_ids_are_rejected():
    with pytest.raises(ValueError):
        build_index((make("a"), make("a")))


def test_lookup_finds_a_problem():
    index = build_index((make("two_sum"),))
    assert get_problem(index, "two_sum").id == "two_sum"


def test_lookup_miss_raises_keyerror():
    with pytest.raises(KeyError):
        get_problem(build_index((make("two_sum"),)), "nope")


def test_lookup_miss_lists_the_valid_ids():
    """The whole point of milestone 2: a message that saves the next person a trip."""
    index = build_index((make("two_sum"), make("binary_search")))
    with pytest.raises(KeyError) as exc:
        get_problem(index, "two-sum")
    message = str(exc.value)
    assert "two_sum" in message and "binary_search" in message


def test_filter_by_topic():
    problems = (make("a", topic="stack"), make("b", topic="graph"))
    assert filter_problems(problems, topic="stack") == (problems[0],)


def test_filter_by_difficulty():
    problems = (make("a", difficulty="easy"), make("b", difficulty="medium"))
    assert filter_problems(problems, difficulty="medium") == (problems[1],)


def test_filters_combine_with_and():
    problems = (make("a", topic="stack", difficulty="easy"),
                make("b", topic="stack", difficulty="medium"))
    assert filter_problems(problems, topic="stack", difficulty="medium") == (problems[1],)


def test_no_filter_returns_everything_as_a_tuple():
    problems = (make("a"), make("b"))
    assert filter_problems(problems) == problems


def test_no_match_returns_an_empty_tuple():
    assert filter_problems((make("a"),), topic="nope") == ()
