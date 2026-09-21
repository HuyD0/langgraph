"""The grader has to survive every way a submission can be wrong.

A submission that crashes, loops forever, or defines the wrong name is a *normal*
outcome here, not an exception. If any of these raised instead of returning a
result, a bad submission would take the whole session down with it.
"""

from __future__ import annotations

from drill.problems import get_problem
from drill.sandbox import first_failure, run_submission

TWO_SUM = get_problem("two_sum")
VALID_PARENS = get_problem("valid_parentheses")

CORRECT = (
    "def two_sum(nums, target):\n"
    "    seen = {}\n"
    "    for i, n in enumerate(nums):\n"
    "        if target - n in seen:\n"
    "            return [seen[target - n], i]\n"
    "        seen[n] = i\n"
    "    return []\n"
)


def test_correct_solution_passes():
    result = run_submission(TWO_SUM, CORRECT)
    assert result["passed"]
    assert result["passed_count"] == result["total"] == len(TWO_SUM.test_cases)
    assert result["fatal_error"] is None
    assert first_failure(result) is None


def test_wrong_answer_reports_the_failing_case():
    result = run_submission(TWO_SUM, "def two_sum(nums, target):\n    return [0, 1]\n")
    assert not result["passed"]
    case = first_failure(result)
    assert case is not None
    assert case["expected"] != case["actual"]


def test_syntax_error_is_fatal_not_an_exception():
    result = run_submission(TWO_SUM, "def two_sum(nums, target)\n    return []\n")
    assert not result["passed"]
    assert "SyntaxError" in result["fatal_error"]


def test_missing_function_names_what_was_found():
    result = run_submission(TWO_SUM, "def twosum(nums, target):\n    return []\n")
    assert "two_sum" in result["fatal_error"]
    assert "twosum" in result["fatal_error"]


def test_infinite_loop_times_out():
    result = run_submission(TWO_SUM, "def two_sum(nums, target):\n    while True:\n        pass\n", timeout=2)
    assert result["timed_out"]
    assert not result["passed"]


def test_exception_in_one_case_is_recorded_per_case():
    result = run_submission(TWO_SUM, "def two_sum(nums, target):\n    return [nums[99], 0]\n")
    assert not result["passed"]
    assert "IndexError" in (first_failure(result)["error"] or "")
    # The other cases still ran; one crash does not abort the batch.
    assert result["total"] == len(TWO_SUM.test_cases)


def test_printing_does_not_corrupt_the_report():
    """You will print things while debugging. That must not break grading."""
    noisy = 'print("debugging")\nimport sys\nsys.stderr.write("noise\\n")\n' + CORRECT
    assert run_submission(TWO_SUM, noisy)["passed"]


def test_truthy_int_does_not_pass_a_boolean_problem():
    """`1 == True` in Python. An interviewer would notice; so should the grader."""
    result = run_submission(VALID_PARENS, "def is_valid(s):\n    return 1\n")
    assert not result["passed"]
    assert "bool" in (first_failure(result)["error"] or "")


def test_mutating_the_input_cannot_corrupt_later_cases():
    """Flood fill mutates its grid. Each case must get its own deep copy."""
    islands = get_problem("num_islands")
    assert run_submission(islands, islands.reference_solution)["passed"]


def test_unordered_problem_accepts_any_ordering():
    reversed_groups = (
        "def group_anagrams(strs):\n"
        "    groups = {}\n"
        "    for word in strs:\n"
        "        groups.setdefault(''.join(sorted(word)), []).append(word)\n"
        "    return list(reversed(list(groups.values())))\n"
    )
    assert run_submission(get_problem("group_anagrams"), reversed_groups)["passed"]


def test_hidden_cases_only_excludes_samples():
    result = run_submission(TWO_SUM, CORRECT, include_samples=False)
    assert result["total"] == len(TWO_SUM.hidden)
