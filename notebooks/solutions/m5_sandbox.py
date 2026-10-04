"""Milestone 5 answer key - running untrusted code.

Written against the names the notebook's setup cell already defines: ``json``,
``subprocess``, ``sys``, ``tempfile``, ``Path``, ``SENTINEL`` and ``HARNESS``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from drill import _harness
from drill._harness import SENTINEL

# The notebook's setup cell binds this the same way.
HARNESS = Path(_harness.__file__)


def build_payload(problem: Any, source: str) -> dict:
    """Build the JSON payload the harness expects.

    ``list(c.args)`` matters: json has no tuple, so a tuple would be written as an
    array and read back as a list anyway. Converting here makes that explicit
    rather than leaving a type that silently changes across the process boundary.
    """
    return {
        "source": source,
        "function_name": problem.function_name,
        "unordered": problem.unordered,
        "cases": [{"args": list(c.args), "expected": c.expected} for c in problem.test_cases],
    }


def parse_report(stdout: str) -> dict | None:
    """Pull the JSON report out of the child's stdout.

    ``rsplit`` with maxsplit=1 takes the *last* sentinel, so a submission that
    prints the sentinel string itself cannot spoof the report.
    """
    if SENTINEL not in stdout:
        return None
    try:
        return json.loads(stdout.rsplit(SENTINEL, 1)[1].strip())
    except json.JSONDecodeError:
        return None


def run_submission(problem: Any, source: str, timeout: int = 10) -> dict:
    """Run a submission and report what happened, never raising on bad code."""
    empty = {
        "passed": False, "total": 0, "passed_count": 0, "cases": [],
        "fatal_error": None, "timed_out": False,
    }

    with tempfile.TemporaryDirectory() as tmp:
        payload_path = Path(tmp) / "payload.json"
        payload_path.write_text(json.dumps(build_payload(problem, source)), encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(HARNESS), str(payload_path)],
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {**empty, "timed_out": True,
                    "fatal_error": f"Your solution ran for more than {timeout}s and was stopped."}

    report = parse_report(proc.stdout)
    if report is None:
        return {**empty,
                "fatal_error": f"No report (exit {proc.returncode}): {(proc.stderr or '')[-500:]}"}
    if report.get("fatal_error"):
        return {**empty, "fatal_error": report["fatal_error"]}

    cases = report["cases"]
    passed_count = sum(1 for c in cases if c["passed"])
    return {
        "passed": bool(cases) and passed_count == len(cases),
        "total": len(cases),
        "passed_count": passed_count,
        "cases": cases,
        "fatal_error": None,
        "timed_out": False,
    }
