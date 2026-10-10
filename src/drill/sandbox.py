"""Runs a submitted solution against a problem's test cases.

**This is a guard rail, not a security boundary.** It runs *your* code on *your*
machine in a subprocess with a timeout, which protects you from the infinite loop
you will eventually write, and stops a crash from taking the tutor down with it.
It does not defend against deliberately hostile code, and is not trying to - if
you paste something untrusted in here, it runs with your privileges.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from drill._harness import SENTINEL
from drill.problems import Problem
from drill.state import CaseResult, SubmissionResult

_HARNESS = Path(__file__).with_name("_harness.py")


def _empty_result(fatal: str, duration: float, timed_out: bool = False) -> SubmissionResult:
    return SubmissionResult(
        passed=False, total=0, passed_count=0, cases=[],
        fatal_error=fatal, timed_out=timed_out, duration_s=duration,
    )


def run_submission(
    problem: Problem, source: str, timeout: int = 10, include_samples: bool = True
) -> SubmissionResult:
    """Execute ``source`` against ``problem``'s cases and report what happened.

    Never raises on a bad submission: a syntax error, a missing function, a crash
    or a timeout all come back as a :class:`SubmissionResult` with ``passed=False``,
    because "your code is broken" is a normal outcome here, not an exception.
    """
    cases = problem.test_cases if include_samples else problem.hidden
    return run_cases(
        source,
        problem.function_name,
        [{"args": list(tc.args), "expected": tc.expected} for tc in cases],
        unordered=problem.unordered,
        timeout=timeout,
    )


def run_cases(
    source: str,
    function_name: str,
    cases: list[dict],
    *,
    unordered: bool = False,
    timeout: int = 10,
) -> SubmissionResult:
    """Like :func:`run_submission`, for cases given as plain ``{"args", "expected"}`` dicts.

    This is the shape the Daily Drill page stores its exercises in, so the local
    server can check an attempt without first turning it into a :class:`Problem`.
    """
    payload = {
        "source": source,
        "function_name": function_name,
        "unordered": unordered,
        "cases": [{"args": list(c["args"]), "expected": c["expected"]} for c in cases],
    }

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="drill-") as tmp:
        payload_path = Path(tmp) / "payload.json"
        payload_path.write_text(json.dumps(payload), encoding="utf-8")

        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(_HARNESS), str(payload_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return _empty_result(
                f"Your solution ran for more than {timeout}s and was stopped.\n"
                "That usually means an infinite loop, or a complexity blow-up on "
                "the larger hidden test cases.",
                time.perf_counter() - started,
                timed_out=True,
            )

    duration = time.perf_counter() - started

    if SENTINEL not in proc.stdout:
        # The child died before reporting: a segfault, a sys.exit, an OOM kill.
        detail = (proc.stderr or proc.stdout or "").strip()[-2000:]
        return _empty_result(
            "The solution process exited without reporting results "
            f"(exit code {proc.returncode}).\n{detail}",
            duration,
        )

    raw = proc.stdout.split(SENTINEL, 1)[1].strip()
    try:
        report = json.loads(raw)
    except json.JSONDecodeError:
        return _empty_result(f"Could not parse the run report:\n{raw[:2000]}", duration)

    if report.get("fatal_error"):
        return _empty_result(report["fatal_error"], duration)

    cases_out: list[CaseResult] = [
        CaseResult(
            args=c["args"], expected=c["expected"], actual=c["actual"],
            passed=c["passed"], error=c["error"],
        )
        for c in report["cases"]
    ]
    passed_count = sum(1 for c in cases_out if c["passed"])

    return SubmissionResult(
        passed=passed_count == len(cases_out) and bool(cases_out),
        total=len(cases_out),
        passed_count=passed_count,
        cases=cases_out,
        fatal_error=None,
        timed_out=False,
        duration_s=duration,
    )


def first_failure(result: SubmissionResult) -> CaseResult | None:
    """The first failing case - what the tutor points at when giving a hint."""
    for case in result["cases"]:
        if not case["passed"]:
            return case
    return None
