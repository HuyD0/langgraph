"""Practice history, and the selection logic that decides what you drill next."""

from __future__ import annotations

import json
import random

from drill.problems import get_problem
from drill.progress import AttemptRecord, new_attempt


def record(store, problem_id: str, solved: bool, attempts: int = 1) -> None:
    store.record(
        new_attempt(
            get_problem(problem_id), solved=solved, attempts=attempts,
            hints_used=0, duration_s=1.0,
        )
    )


def test_empty_history_reads_as_empty(store):
    assert store.load() == []
    assert store.stats_by_topic() == {}
    assert store.weakest_topic() is None


def test_records_round_trip(store):
    record(store, "two_sum", solved=True)
    history = store.load()
    assert len(history) == 1
    assert isinstance(history[0], AttemptRecord)
    assert history[0].problem_id == "two_sum" and history[0].topic == "hash-map"


def test_stats_count_attempts_and_solves(store):
    record(store, "two_sum", solved=True)
    record(store, "group_anagrams", solved=False)
    assert store.stats_by_topic()["hash-map"] == {"attempted": 2, "solved": 1}


def test_weakest_topic_is_the_worst_solve_rate(store):
    record(store, "two_sum", solved=True)          # hash-map: 1/1
    record(store, "valid_parentheses", solved=False)  # stack:    0/1
    assert store.weakest_topic() == "stack"


def test_weakest_topic_breaks_ties_toward_least_practised(store):
    record(store, "two_sum", solved=False)
    record(store, "group_anagrams", solved=False)   # hash-map: 0/2
    record(store, "valid_parentheses", solved=False)  # stack:   0/1
    assert store.weakest_topic() == "stack"


def test_corrupt_history_does_not_block_practice(store, progress_path):
    """A broken file should cost you your history, not your session."""
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("{not json", encoding="utf-8")
    assert store.load() == []


def test_rows_from_an_older_schema_are_skipped(store, progress_path):
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        json.dumps({"attempts": [{"problem_id": "two_sum", "unknown_field": 1}]}),
        encoding="utf-8",
    )
    assert store.load() == []


def test_explicit_problem_id_wins(store):
    assert store.choose_problem(problem_id="merge_intervals").id == "merge_intervals"


def test_selection_prefers_the_weakest_topic(store):
    record(store, "two_sum", solved=True)             # hash-map looks fine
    record(store, "valid_parentheses", solved=False)  # stack does not
    chosen = store.choose_problem(rng=random.Random(0))
    assert chosen.topic == "stack"


def test_selection_skips_what_you_already_solved(store):
    solved = {"two_sum", "binary_search", "climbing_stairs"}
    for pid in solved:
        record(store, pid, solved=True)
    for _ in range(20):
        assert store.choose_problem(rng=random.Random()).id not in solved


def test_topic_filter_is_respected(store):
    assert store.choose_problem(topic="graph", rng=random.Random(1)).topic == "graph"


def test_unknown_topic_raises(store):
    import pytest

    with pytest.raises(KeyError):
        store.choose_problem(topic="not-a-topic")


def test_everything_solved_falls_back_to_revision(store):
    from drill.problems import ALL_PROBLEMS

    for problem in ALL_PROBLEMS:
        record(store, problem.id, solved=True)
    assert store.choose_problem(rng=random.Random(2)) is not None
