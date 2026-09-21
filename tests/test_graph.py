"""End-to-end runs through the graph, with a fake model standing in for Azure.

These are the tests that would have been impossible against the old agent: it
built its model and its search client at import time, so there was no seam to
put a fake into. Passing dependencies through the config is what buys this.
"""

from __future__ import annotations

from langgraph.types import Command

CORRECT_TWO_SUM = (
    "def two_sum(nums, target):\n"
    "    seen = {}\n"
    "    for i, n in enumerate(nums):\n"
    "        if target - n in seen:\n"
    "            return [seen[target - n], i]\n"
    "        seen[n] = i\n"
    "    return []\n"
)
WRONG_TWO_SUM = "def two_sum(nums, target):\n    return [0, 0]\n"


def start(graph, deps, thread, problem_id="two_sum"):
    config = deps.as_config(thread)
    out = graph.invoke({"problem_id": problem_id, "topic": ""}, config=config)
    return config, out


def test_graph_pauses_asking_for_a_submission(graph, deps):
    _, out = start(graph, deps, "t-pause")
    request = out["__interrupt__"][0].value
    assert request["kind"] == "submission_request"
    assert request["problem_id"] == "two_sum"
    assert request["attempt"] == 1


def test_correct_first_submission_is_reviewed_and_recorded(graph, deps, fake_model):
    config, _ = start(graph, deps, "t-solve")
    out = graph.invoke(Command(resume={"submission": CORRECT_TWO_SUM}), config=config)

    assert "__interrupt__" not in out, "graph should have finished"
    assert out["verdict"] == "solved"
    assert out["attempts"] == 1
    assert out["hints"] == []
    assert len(fake_model.calls) == 1, "exactly one model call: the review"

    history = deps.progress.load()
    assert len(history) == 1 and history[0].solved


def test_wrong_submission_produces_a_hint_and_pauses_again(graph, deps, fake_model):
    config, _ = start(graph, deps, "t-hint")
    out = graph.invoke(Command(resume={"submission": WRONG_TWO_SUM}), config=config)

    values = graph.get_state(config).values
    assert len(values["hints"]) == 1
    assert out["__interrupt__"][0].value["attempt"] == 2, "it must ask again"
    assert "two_sum(" in fake_model.last_prompt, "the hint prompt should cite the failing call"


def test_retry_loop_then_solve(graph, deps):
    """Fail, take a hint, then solve: the cycle the graph exists for."""
    config, _ = start(graph, deps, "t-loop")
    graph.invoke(Command(resume={"submission": WRONG_TWO_SUM}), config=config)
    out = graph.invoke(Command(resume={"submission": CORRECT_TWO_SUM}), config=config)

    assert "__interrupt__" not in out
    assert out["verdict"] == "solved"
    assert out["attempts"] == 2
    assert len(out["hints"]) == 1


def test_running_out_of_attempts_explains_instead_of_hinting(graph, deps, fake_model):
    config, _ = start(graph, deps, "t-explain")
    for _ in range(3):
        out = graph.invoke(Command(resume={"submission": WRONG_TWO_SUM}), config=config)

    assert "__interrupt__" not in out
    assert out["verdict"] == "explain"
    assert out["attempts"] == 3
    assert len(out["hints"]) == 2, "two hints, then the walkthrough"
    assert "seen[n] = i" in fake_model.last_prompt, "the walkthrough sees the reference solution"

    history = deps.progress.load()
    assert len(history) == 1 and not history[0].solved


def test_max_attempts_comes_from_settings(graph, deps):
    object.__setattr__(deps.settings, "max_attempts", 1)
    config, _ = start(graph, deps, "t-one-shot")
    out = graph.invoke(Command(resume={"submission": WRONG_TWO_SUM}), config=config)
    assert "__interrupt__" not in out
    assert out["verdict"] == "explain", "one attempt, so a failure goes straight to the walkthrough"


def test_threads_are_independent(graph, deps):
    """Two sessions in flight at once must not see each other's state."""
    c1, _ = start(graph, deps, "t-a", problem_id="two_sum")
    c2, _ = start(graph, deps, "t-b", problem_id="binary_search")
    graph.invoke(Command(resume={"submission": WRONG_TWO_SUM}), config=c1)

    assert graph.get_state(c1).values["problem_id"] == "two_sum"
    assert graph.get_state(c2).values["problem_id"] == "binary_search"
    assert graph.get_state(c2).values["attempts"] == 0


def test_nodes_refuse_to_run_without_deps(graph):
    """A missing dependency should say so, not fail obscurely later."""
    import pytest

    with pytest.raises(Exception, match="Deps"):
        graph.invoke({"problem_id": "two_sum"}, config={"configurable": {"thread_id": "x"}})
