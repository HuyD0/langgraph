"""Runs a submitted solution against a problem's test cases.

**This is a guard rail, not a security boundary.** It runs *your* code on *your*
machine in a subprocess with a timeout, which protects you from the infinite loop
you will eventually write, and stops a crash from taking the tutor down with it.
It does not defend against deliberately hostile code, and is not trying to - if
you paste something untrusted in here, it runs with your privileges. It also gets
none of the server's environment variables, so a pasted snippet cannot read your keys.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from drill._harness import SENTINEL
from drill.problems import Problem
from drill.state import CaseResult, SubmissionResult

_HARNESS = Path(__file__).with_name("_harness.py")
MAX_OUTPUT_BYTES = 8 * 1024 * 1024  # how much a submission may print before its writes start failing
CHILD_ENV = ("PATH", "SYSTEMROOT", "TEMP", "TMP")  # the only variables the submission's process is given


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
        "max_output_bytes": MAX_OUTPUT_BYTES,
    }

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="drill-") as tmp:
        payload_path = Path(tmp) / "payload.json"
        payload_path.write_text(json.dumps(payload), encoding="utf-8")

        out_path, err_path = Path(tmp) / "stdout.txt", Path(tmp) / "stderr.txt"
        # Output goes to files, not into this process's memory: a print in an endless loop
        # would otherwise pile up hundreds of megabytes here. Its own session (process
        # group) lets us stop anything the submission started, not just the submission.
        # A minimal environment: the server's keys and database settings stay out of
        # reach (SYSTEMROOT/TEMP keep Python starting on Windows; -I already ignores PYTHON*).
        with out_path.open("wb") as out, err_path.open("wb") as err:
            proc = subprocess.Popen(
                # -X utf8: print() writes UTF-8 on Windows too, so an emoji or accent never crashes it
                [sys.executable, "-I", "-X", "utf8", str(_HARNESS), str(payload_path)],
                stdout=out, stderr=err, cwd=tmp, start_new_session=True,
                env={k: os.environ[k] for k in CHILD_ENV if k in os.environ},
            )
            try:
                _wait(proc, out_path, timeout)
            except subprocess.TimeoutExpired:
                _stop_all(proc)
                return _empty_result(
                    f"Your solution ran for more than {timeout}s and was stopped.\n"
                    "That usually means an infinite loop, or a complexity blow-up on "
                    "the larger hidden test cases.",
                    time.perf_counter() - started,
                    timed_out=True,
                )
            _stop_all(proc)  # anything it left running in the background
        stdout = out_path.read_text(encoding="utf-8", errors="replace")
        stderr = _tail(err_path)
        printed_too_much = out_path.stat().st_size >= MAX_OUTPUT_BYTES

    duration = time.perf_counter() - started

    if SENTINEL not in stdout:
        # The child died before reporting: a segfault, a sys.exit, an OOM kill, or too much output.
        if printed_too_much:
            return _empty_result(
                f"Your solution printed more than {MAX_OUTPUT_BYTES // (1024 * 1024)} MB and was stopped.\n"
                "That usually means a print inside a loop that never ends.",
                duration,
            )
        detail = (stderr or stdout[-2000:]).strip()[-2000:]
        return _empty_result(
            "The solution process exited without reporting results "
            f"(exit code {proc.returncode}).\n{detail}",
            duration,
        )

    raw = stdout.split(SENTINEL, 1)[1].strip()
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


def _wait(proc: subprocess.Popen, out_path: Path, timeout: int) -> None:
    """Wait for the submission to finish, raising ``TimeoutExpired`` after ``timeout`` seconds.

    Elsewhere the harness caps the output file's size itself. Windows has no such cap, so
    there we watch the file and return as soon as it holds ``MAX_OUTPUT_BYTES`` (the caller
    then stops the process).
    """
    if sys.platform != "win32":
        proc.wait(timeout=timeout)
        return
    end = time.monotonic() + timeout
    while proc.poll() is None:
        if out_path.stat().st_size >= MAX_OUTPUT_BYTES:
            return
        if time.monotonic() > end:
            raise subprocess.TimeoutExpired(proc.args, timeout)
        time.sleep(0.05)


def _stop_all(proc: subprocess.Popen) -> None:
    """Kill the submission and every process it started, then reap it."""
    if hasattr(os, "killpg"):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass  # already gone
    else:
        proc.kill()
    proc.wait()


def _tail(path: Path, size: int = 4000) -> str:
    """The last ``size`` bytes of a file, as text."""
    with path.open("rb") as f:
        f.seek(max(0, path.stat().st_size - size))
        return f.read().decode("utf-8", errors="replace")


def first_failure(result: SubmissionResult) -> CaseResult | None:
    """The first failing case - what the tutor points at when giving a hint."""
    for case in result["cases"]:
        if not case["passed"]:
            return case
    return None
