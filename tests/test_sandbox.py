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


def test_a_submission_cannot_read_the_servers_environment(monkeypatch):
    """The server holds keys and database settings; a pasted snippet must not see them."""
    monkeypatch.setenv("DRILL_HOSTED_API_KEY", "not-for-the-learner")
    source = (
        "import os\n"
        "def two_sum(nums, target):\n"
        "    return sorted(k for k in os.environ if k.startswith(('DRILL_', 'AZURE_', 'PG', 'LAKEBASE_')))\n"
    )
    result = run_submission(TWO_SUM, source)
    assert result["total"] > 0 and result["fatal_error"] is None
    assert all(case["actual"] == [] for case in result["cases"])


def test_a_crash_shows_the_submissions_frames_not_the_harness():
    """The traceback starts in the learner's code, so the server's path to the harness stays private."""
    result = run_submission(TWO_SUM, "def two_sum(nums, target):\n    return [nums[99], 0]\n")
    error = first_failure(result)["error"] or ""
    assert "IndexError" in error and "<submission>" in error
    assert "_harness.py" not in error


def test_sys_exit_in_a_submission_is_reported_not_swallowed():
    result = run_submission(TWO_SUM, "import sys\nsys.exit(3)\n")
    assert not result["passed"]
    assert "SystemExit" in (result["fatal_error"] or "") and "_harness.py" not in result["fatal_error"]


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


def test_printing_forever_is_capped_not_held_in_memory(monkeypatch):
    from drill import sandbox

    monkeypatch.setattr(sandbox, "MAX_OUTPUT_BYTES", 256 * 1024)
    source = "def two_sum(nums, target):\n    while True:\n        print('x' * 1000)\n"
    result = run_submission(get_problem("two_sum"), source, timeout=10)
    assert not result["passed"] and not result["timed_out"]  # stopped by the cap, well before the time limit
    assert "printed more than" in result["fatal_error"]


def test_processes_the_submission_starts_are_stopped_too(tmp_path):
    marker = tmp_path / "still-running"
    source = (
        "import subprocess, sys\n"
        "def two_sum(nums, target):\n"
        f"    subprocess.Popen([sys.executable, '-c', 'import time, pathlib; time.sleep(1.5); pathlib.Path({str(marker)!r}).touch()'])\n"
        "    return [0, 1]\n"
    )
    run_submission(get_problem("two_sum"), source)
    import time

    time.sleep(2.5)
    assert not marker.exists()  # the background process was killed with the submission
