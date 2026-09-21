"""Milestone 4: aggregating history. -> src/drill_rebuild/m4_progress.py"""

from __future__ import annotations

from drill_rebuild.m4_progress import AttemptRecord, stats_by_topic, unsolved_ids, weakest_topic


def rec(problem_id: str, topic: str, solved: bool) -> AttemptRecord:
    return AttemptRecord(problem_id=problem_id, topic=topic, solved=solved, attempts=1)


def test_empty_history_gives_empty_stats():
    assert stats_by_topic([]) == {}


def test_counts_attempts_and_solves():
    history = [rec("a", "hash-map", True), rec("b", "hash-map", False)]
    assert stats_by_topic(history) == {"hash-map": {"attempted": 2, "solved": 1}}


def test_topics_are_counted_separately():
    stats = stats_by_topic([rec("a", "hash-map", True), rec("b", "stack", False)])
    assert stats["hash-map"]["solved"] == 1
    assert stats["stack"]["solved"] == 0


def test_weakest_topic_of_an_empty_history_is_none():
    assert weakest_topic([]) is None


def test_weakest_topic_is_the_lowest_solve_rate():
    history = [rec("a", "hash-map", True), rec("b", "stack", False)]
    assert weakest_topic(history) == "stack"


def test_weakest_topic_compares_rates_not_totals():
    """stack is 1/2; hash-map is 2/3. Counting raw solves would pick the wrong one."""
    history = [
        rec("a", "hash-map", True), rec("b", "hash-map", True), rec("c", "hash-map", False),
        rec("d", "stack", True), rec("e", "stack", False),
    ]
    assert weakest_topic(history) == "stack"


def test_tie_breaks_toward_the_least_practised():
    """Both are 0%. The one you have barely touched is the one to work on."""
    history = [rec("a", "hash-map", False), rec("b", "hash-map", False),
               rec("c", "stack", False)]
    assert weakest_topic(history) == "stack"


def test_unsolved_excludes_anything_ever_solved():
    history = [rec("a", "hash-map", False), rec("a", "hash-map", True)]
    assert unsolved_ids(history, ["a", "b"]) == ["b"]


def test_unsolved_preserves_input_order():
    assert unsolved_ids([], ["c", "a", "b"]) == ["c", "a", "b"]


def test_unsolved_of_everything_solved_is_empty():
    assert unsolved_ids([rec("a", "t", True)], ["a"]) == []
