"""Milestone 5: running untrusted code. -> src/drill_rebuild/m5_sandbox.py

These use the real problem bank, so your implementation has to work against the
same data the finished tutor uses.
"""

from __future__ import annotations

import json

from drill._harness import SENTINEL
from drill.problems import get_problem
from drill_rebuild.m5_sandbox import build_payload, parse_report, run_submission

TWO_SUM = get_problem("two_sum")
CORRECT = (
    "def two_sum(nums, target):\n"
    "    seen = {}\n"
    "    for i, n in enumerate(nums):\n"
    "        if target - n in seen:\n"
    "            return [seen[target - n], i]\n"
    "        seen[n] = i\n"
    "    return []\n"
)


def test_payload_has_the_required_keys():
    payload = build_payload(TWO_SUM, CORRECT)
    assert set(payload) >= {"source", "function_name", "unordered", "cases"}
    assert payload["function_name"] == "two_sum"


def test_payload_args_are_lists_not_tuples():
    """JSON has no tuples. Send lists, or the child sees something you did not mean."""
    payload = build_payload(TWO_SUM, CORRECT)
    assert all(isinstance(case["args"], list) for case in payload["cases"])


def test_payload_is_json_serialisable():
    json.dumps(build_payload(TWO_SUM, CORRECT))


def test_parse_report_reads_json_after_the_sentinel():
    assert parse_report(f'{SENTINEL}\n{{"cases": [], "fatal_error": null}}')["cases"] == []


def test_parse_report_ignores_anything_printed_first():
    stdout = f'debugging output\nmore noise\n{SENTINEL}\n{{"cases": [], "fatal_error": null}}'
    assert parse_report(stdout) is not None


def test_parse_report_returns_none_without_a_sentinel():
    assert parse_report("just some output") is None


def test_parse_report_returns_none_on_bad_json():
    assert parse_report(f"{SENTINEL}\nnot json at all") is None


def test_correct_solution_passes():
    result = run_submission(TWO_SUM, CORRECT)
    assert result["passed"]
    assert result["passed_count"] == result["total"] == len(TWO_SUM.test_cases)
    assert result["fatal_error"] is None


def test_wrong_answer_fails_without_raising():
    result = run_submission(TWO_SUM, "def two_sum(nums, target):\n    return [0, 1]\n")
    assert not result["passed"]
    assert 0 < result["passed_count"] < result["total"]


def test_syntax_error_comes_back_as_a_result():
    result = run_submission(TWO_SUM, "def two_sum(nums, target)\n    return []\n")
    assert not result["passed"]
    assert result["fatal_error"]


def test_missing_function_comes_back_as_a_result():
    result = run_submission(TWO_SUM, "def nope():\n    return []\n")
    assert not result["passed"]
    assert result["fatal_error"]


def test_infinite_loop_times_out_instead_of_hanging():
    result = run_submission(
        TWO_SUM, "def two_sum(nums, target):\n    while True:\n        pass\n", timeout=2
    )
    assert result["timed_out"]
    assert not result["passed"]


def test_a_printing_submission_still_grades():
    assert run_submission(TWO_SUM, 'print("hello")\n' + CORRECT)["passed"]
