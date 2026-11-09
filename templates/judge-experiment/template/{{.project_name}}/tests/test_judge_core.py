"""The experiment's logic, without Spark or a model: `uv run --with pytest --with pandas pytest tests`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import judge_core as core  # noqa: E402


def row(i, answer="It costs 30 euros.", expected=None):
    return {"id": f"r{i}", "group": "g", "context": "c", "question": "q", "answer": answer, "expected_pass": expected}


def test_each_plant_breaks_one_rule_and_is_known_bad():
    rows = [row(i, f"Answer {i} costs {i + 2} euros.") for i in range(10)]
    planted = core.plants(rows, per_kind=5)
    assert {p["planted"] for p in planted} == set(core.PLANT_KINDS) and len(planted) == 20
    assert all(p["expected_pass"] is False and p["id"].startswith("plant:") for p in planted)
    assert [p["id"] for p in planted] == [p["id"] for p in core.plants(rows, per_kind=5)]  # the same every run
    wrong = next(p for p in planted if p["planted"] == "wrong_number")
    assert wrong["answer"] != next(r for r in rows if wrong["id"].endswith(r["id"]))["answer"]


def test_no_number_means_no_wrong_number_plant():
    assert core.change_number("No digits here.") is None
    assert core.change_number("Wait 15 minutes.") == "Wait 150 minutes."


def test_the_gate_counts_known_bad_answers():
    rows = [row(1, expected=False), row(2, expected=True), {**row(3), "planted": "made_up_fact", "expected_pass": False}]
    gate = core.measurable(rows, need=2)
    assert gate["ok"] and gate["known_bad"] == 2 and gate["by_kind"] == {"labelled": 1, "made_up_fact": 1}
    assert not core.measurable(rows, need=3)["ok"]


def test_code_checks_catch_rules_a_judge_should_not_need_to():
    assert core.code_checks("Short and fine.", 10)["pass"]
    assert not core.code_checks("As I said in my last message, yes.", 50)["pass"]
    assert not core.code_checks("word " * 30, 10)["pass"]


def test_consensus_majority_split_and_tie():
    assert core.consensus([True, True, False]) == (True, True)
    assert core.consensus([True, False]) == (False, True)
    assert core.consensus([None, True]) == (True, False)


def test_scores_and_comparison():
    truth = [False, False, True, True]
    s = core.scores([False, True, True, True], truth)
    assert s["catch"]["rate"] == 0.5 and s["keep"]["rate"] == 1.0 and s["balanced"] == 0.75
    c = core.compare([False, False, True, True], [False, True, True, True], truth)
    assert c == {"only_first_right": 1, "only_second_right": 0, "p_value": 1.0}
    assert core.kappa([True, True], [True, True]) is None


def test_blank_and_missing_labels_mean_nobody_checked():
    import pandas as pd

    import tables

    df = pd.DataFrame({"id": ["a", "b", "c", "d"], "expected_pass": [None, float("nan"), "false", True]})
    assert [r["expected_pass"] for r in tables.rows(df)] == [None, None, False, True]


def test_balanced_accuracy_is_empty_without_good_labels():
    s = core.scores([False, False], [False, False])
    assert s["catch"]["rate"] == 1.0 and s["keep"]["n"] == 0 and s["balanced"] is None


def test_a_persons_verdicts_become_labels_on_real_rows_only():
    rows = [row(1), row(2, expected=True), {**row(3), "planted": "made_up_fact", "expected_pass": False}]
    out, changed = core.apply_verdicts(rows, {"r1": False, "r2": True, "r3": True})
    assert [r["expected_pass"] for r in out] == [False, True, False] and changed == 1


def test_reviewers_answers_read_as_pass_or_fail():
    import review

    assert [review.as_pass(v) for v in (True, "Pass", "fail", "no", "maybe")] == [True, True, False, False, None]


def test_a_trace_that_is_gone_has_no_verdict(monkeypatch):
    import mlflow

    import review

    monkeypatch.setattr(review, "question_id", lambda experiment_id: "q1")
    monkeypatch.setattr(mlflow, "get_trace", lambda trace_id: None)
    assert review.verdicts("exp", ["tr-gone"]) == {}
