"""The session driver, exercised with a scripted learner instead of a terminal.

`run_session` takes the "how do I get code from the human" part as an argument,
so a test can hand it a function that returns canned submissions. No stdin, no
editor, no prompts - which is the payoff for keeping the CLI out of it.
"""

from __future__ import annotations

from drill.graph import build_drill_graph
from drill.session import run_session

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


def scripted(*submissions):
    """A learner who submits these answers in order."""
    queue = list(submissions)

    def _get(problem, request):
        return queue.pop(0) if queue else WRONG

    return _get


def test_solving_first_time(deps):
    outcome = run_session(build_drill_graph(), deps, scripted(CORRECT), problem_id="two_sum")
    assert outcome.solved
    assert outcome.attempts == 1
    assert outcome.hints == []
    assert outcome.problem.id == "two_sum"


def test_failing_then_solving(deps):
    outcome = run_session(build_drill_graph(), deps, scripted(WRONG, CORRECT), problem_id="two_sum")
    assert outcome.solved
    assert outcome.attempts == 2
    assert len(outcome.hints) == 1


def test_never_solving_ends_with_a_walkthrough(deps):
    outcome = run_session(build_drill_graph(), deps, scripted(WRONG, WRONG, WRONG),
                          problem_id="two_sum")
    assert not outcome.solved
    assert outcome.attempts == 3
    assert outcome.final_state["verdict"] == "explain"
    assert outcome.feedback


def test_events_are_emitted_in_order(deps):
    seen = []
    run_session(build_drill_graph(), deps, scripted(WRONG, CORRECT),
                problem_id="two_sum", on_event=lambda kind, _: seen.append(kind))
    assert seen == ["problem", "awaiting_submission", "hint", "awaiting_submission", "finished"]


def test_session_is_recorded_to_progress(deps):
    run_session(build_drill_graph(), deps, scripted(CORRECT), problem_id="two_sum")
    history = deps.progress.load()
    assert len(history) == 1
    assert history[0].problem_id == "two_sum" and history[0].solved


def test_topic_selection_is_honoured(deps):
    outcome = run_session(build_drill_graph(), deps, scripted(WRONG, WRONG, WRONG), topic="stack")
    assert outcome.problem.topic == "stack"


def test_selection_targets_the_weakest_topic(deps):
    """Fail at stack, and the next unguided session should come back to stack."""
    run_session(build_drill_graph(), deps, scripted(CORRECT), problem_id="two_sum")
    run_session(build_drill_graph(), deps, scripted(WRONG, WRONG, WRONG),
                problem_id="valid_parentheses")
    outcome = run_session(build_drill_graph(), deps, scripted(WRONG, WRONG, WRONG))
    assert outcome.problem.topic == "stack"


def test_each_session_gets_its_own_thread(deps):
    a = run_session(build_drill_graph(), deps, scripted(CORRECT), problem_id="two_sum")
    b = run_session(build_drill_graph(), deps, scripted(WRONG, WRONG, WRONG),
                    problem_id="binary_search")
    assert a.problem.id != b.problem.id
    assert len(deps.progress.load()) == 2
