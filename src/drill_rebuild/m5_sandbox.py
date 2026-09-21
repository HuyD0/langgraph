"""Milestone 5 - running someone else's code without it taking you down.

Run: uv run pytest tests/rebuild/test_m5_sandbox.py

WHY THIS MATTERS
This is the hardest milestone and the most transferable. Any system that executes
work it did not write - a CI runner, a plugin host, a notebook kernel - faces
exactly this: run it elsewhere, bound how long it gets, and turn every possible
failure into data instead of an exception.

You do not have to write the child process. `drill._harness` already does that
job and you may import it. Your task is the PARENT side: launch it, feed it,
enforce the timeout, and parse what comes back.
"""

from __future__ import annotations

from typing import Any

# The child prints this line, then one line of JSON. Anything printed before it is
# the submission's own output and must be ignored.
from drill._harness import SENTINEL  # noqa: F401  (you will need this)


def build_payload(problem: Any, source: str) -> dict:
    """Build the JSON payload the harness expects.

    It needs exactly these keys::

        {
          "source":        the submitted code, as a string,
          "function_name": which function to call,
          "unordered":     bool - compare ignoring order,
          "cases":         [{"args": [...], "expected": ...}, ...],
        }

    Note `args` must be a LIST, not a tuple: `json.dumps` cannot tell you apart
    from a tuple, it just writes an array, and the child reads it back as a list.
    Getting this wrong is the kind of serialisation mismatch that produces a
    baffling error three layers away.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 5: implement build_payload")


def parse_report(stdout: str) -> dict | None:
    """Pull the JSON report out of the child's stdout.

    The submission is allowed to print - you WILL print things while debugging -
    so the report is whatever follows the last SENTINEL line. Return the decoded
    dict, or None if there is no sentinel or the JSON will not parse.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 5: implement parse_report")


def run_submission(problem: Any, source: str, timeout: int = 10) -> dict:
    """Run `source` against `problem`'s test cases and report what happened.

    Return a dict with these keys::

        passed        bool   - every case passed (and there was at least one)
        total         int
        passed_count  int
        cases         list of per-case dicts from the harness
        fatal_error   str | None
        timed_out     bool

    This function must NEVER raise because of a bad submission. A syntax error, a
    missing function, a crash, an infinite loop - each is a normal outcome that
    comes back as a result with passed=False. If any of them escaped as an
    exception, one bad submission would end the practice session.

    How to run the child::

        subprocess.run(
            [sys.executable, "-I", <path to drill/_harness.py>, <payload path>],
            capture_output=True, text=True, timeout=timeout,
        )

    `-I` is isolated mode: the child ignores PYTHONPATH and the user site
    directory, so the submission cannot import your project and shadow something.
    Catch `subprocess.TimeoutExpired` and return timed_out=True.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 5: implement run_submission")
