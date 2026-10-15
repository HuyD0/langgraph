"""Runs one submission against one problem's test cases, in a throwaway process.

This file is executed as a *script*, never imported by the rest of the package:

    python -I drill/_harness.py payload.json

``-I`` is isolated mode, so the child ignores ``PYTHONPATH`` and the user site
directory. That keeps the submission from accidentally importing ``drill`` itself
and shadowing something. Everything the child needs arrives in the JSON payload.

Results come back on stdout after a sentinel line, so anything the submission
prints - and you *should* print things while debugging - cannot corrupt the
report the parent parses.

The parent sends stdout to a file, not into its own memory, and the payload's
``max_output_bytes`` caps how big any file this process writes can get. A ``print`` in an
endless loop then fails with "File too large" instead of filling the disk or the server.
"""

import copy
import json
import sys
import traceback

SENTINEL = "---DRILL-RESULT---"


def normalize(value):
    """Sort nested sequences so order-insensitive answers compare equal.

    ``key=repr`` rather than natural ordering, because a submission may return
    mixed types and we would rather compare them than crash on a TypeError.
    """
    if isinstance(value, (list, tuple)):
        items = [normalize(v) for v in value]
        try:
            return sorted(items, key=repr)
        except TypeError:
            return items
    return value


def safe(value):
    """Make a value JSON-encodable, falling back to its repr."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


def main() -> None:
    payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
    limit_output(payload.get("max_output_bytes"))
    source = payload["source"]
    function_name = payload["function_name"]
    unordered = payload.get("unordered", False)

    report = {"cases": [], "fatal_error": None}

    # Step 1: does the submitted code even run? A syntax error or a NameError at
    # module level lands here, and is reported as fatal rather than as a failed case.
    namespace = {"__name__": "__submission__"}
    try:
        exec(compile(source, "<submission>", "exec"), namespace)
    except (Exception, SystemExit) as exc:  # SystemExit: a learner's sys.exit() is a wrong answer, not a crash
        report["fatal_error"] = format_error(exc, limit=6)
        emit(report)
        return

    func = namespace.get(function_name)
    if not callable(func):
        defined = sorted(k for k, v in namespace.items() if callable(v) and not k.startswith("__"))
        report["fatal_error"] = (
            f"No function named {function_name!r} was defined.\n"
            f"Functions found: {', '.join(defined) if defined else '(none)'}"
        )
        emit(report)
        return

    # Step 2: run each case in isolation. Arguments are deep-copied so a solution
    # that mutates its input (flood fill does, for instance) cannot corrupt a
    # later case or the expected values.
    for case in payload["cases"]:
        args = copy.deepcopy(case["args"])
        expected = case["expected"]
        entry = {"args": safe(args), "expected": safe(expected), "actual": None,
                 "passed": False, "error": None}
        try:
            actual = func(*args)
            entry["actual"] = safe(actual)

            left, right = (normalize(actual), normalize(expected)) if unordered else (actual, expected)
            passed = left == right
            # In Python `True == 1`, which would let a solution returning 1 pass a
            # boolean problem. Interviewers notice that; so does this.
            if passed and isinstance(expected, bool) and not isinstance(actual, bool):
                passed = False
                entry["error"] = f"expected a bool, got {type(actual).__name__}"
            entry["passed"] = passed
        except (Exception, SystemExit) as exc:
            entry["error"] = format_error(exc, limit=4)
        report["cases"].append(entry)

    emit(report)


def format_error(exc: BaseException, limit: int) -> str:
    """The traceback from the submission's own frames on.

    The outermost frame is this harness, so dropping it (``tb_next``) keeps the server's
    path to this file out of what the learner reads.
    """
    tb = exc.__traceback__
    return "".join(traceback.format_exception(type(exc), exc, tb.tb_next if tb else None, limit=limit))


def limit_output(max_bytes) -> None:
    """Cap the size of any file this process writes, stdout's file included (POSIX only)."""
    if not max_bytes:
        return
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_FSIZE, (max_bytes, max_bytes))
    except (ImportError, ValueError, OSError):
        pass  # Windows, or a limit we may not set: run without the cap


def emit(report) -> None:
    sys.stdout.flush()
    print(SENTINEL)
    print(json.dumps(report))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
