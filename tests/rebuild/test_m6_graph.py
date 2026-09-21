"""Milestone 6: wiring the graph. -> src/drill_rebuild/m6_graph.py

The first tests check the shape; the last ones actually run it, using the same
fake-model fixtures as the main suite.
"""

from __future__ import annotations

import pytest
from langgraph.types import Command

from drill_rebuild.m6_graph import build_drill_graph

CORRECT = (
    "def two_sum(nums, target):\n"
    "    seen = {}\n"
    "    for i, n in enumerate(nums):\n"
    "        if target - n in seen:\n"
    "            return [seen[target - n], i]\n"
    "        seen[n] = i\n"
    "    return []\n"
)
WRONG = "def two_sum(nums, target):\n    return [0, 0]\n"


@pytest.fixture
def built():
    return build_drill_graph()


def edges(graph) -> set[tuple[str, str]]:
    return {(e.source, e.target) for e in graph.get_graph().edges}


def test_all_seven_nodes_exist(built):
    names = set(built.get_graph().nodes)
    assert {"select_problem", "await_submission", "run_tests",
            "hint", "review", "explain", "record"} <= names


def test_the_happy_path_is_connected(built):
    assert {("__start__", "select_problem"),
            ("select_problem", "await_submission"),
            ("await_submission", "run_tests")} <= edges(built)


def test_run_tests_branches_three_ways(built):
    assert {("run_tests", "review"), ("run_tests", "hint"),
            ("run_tests", "explain")} <= edges(built)


def test_hint_loops_back_for_another_attempt(built):
    """The cycle. Without it this is a pipeline that gives up after one try."""
    assert ("hint", "await_submission") in edges(built)


def test_both_endings_are_recorded(built):
    assert {("review", "record"), ("explain", "record")} <= edges(built)


def test_record_ends_the_graph(built):
    assert ("record", "__end__") in edges(built)


def test_the_graph_pauses_for_a_submission(built, deps):
    out = built.invoke({"problem_id": "two_sum"}, config=deps.as_config("m6-a"))
    assert "__interrupt__" in out, "no checkpointer, or no interrupt in await_submission"
    assert out["__interrupt__"][0].value["problem_id"] == "two_sum"


def test_a_correct_submission_finishes(built, deps):
    config = deps.as_config("m6-b")
    built.invoke({"problem_id": "two_sum"}, config=config)
    out = built.invoke(Command(resume={"submission": CORRECT}), config=config)
    assert "__interrupt__" not in out
    assert out["verdict"] == "solved"


def test_a_wrong_submission_hints_and_asks_again(built, deps):
    config = deps.as_config("m6-c")
    built.invoke({"problem_id": "two_sum"}, config=config)
    out = built.invoke(Command(resume={"submission": WRONG}), config=config)
    assert "__interrupt__" in out
    assert out["__interrupt__"][0].value["attempt"] == 2


def test_running_out_of_attempts_explains(built, deps):
    config = deps.as_config("m6-d")
    built.invoke({"problem_id": "two_sum"}, config=config)
    for _ in range(3):
        out = built.invoke(Command(resume={"submission": WRONG}), config=config)
    assert "__interrupt__" not in out
    assert out["verdict"] == "explain"
