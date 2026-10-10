"""What the tutor says, and how an exercise is checked.

The prompts behind hints, reviews and explanations live here so the web door and the
MCP door teach the same way, in the same plain language as the page. ``run_exercise``
runs a learner's code against an exercise's test cases, the way the page does in the
browser, but in a subprocess on this machine.
"""

from __future__ import annotations

from drill.sandbox import first_failure, run_cases

LEARNER = (
    "The learner is new to coding and is learning AI engineering: Databricks for agents, "
    "LangGraph, LangChain and MLflow, plus Terraform for Azure Databricks. Explain any jargon "
    "in plain words. Never use Big-O notation; say things like \"it walks through the list once\" "
    "instead. Short sentences. Encouraging but not gushing. Wrap identifiers in backticks."
)

HINT_LEVELS = {
    1: "Point at what to look at, in one or two sentences. Do not say what to write.",
    2: "Name the step to take next and the Python feature it needs, with a tiny example about something else.",
    3: "Walk through the approach step by step in words. You may show one line of the kind of code needed, but not the solution.",
}


def exercise_context(card: dict) -> str:
    """The exercise, as the model should see it."""
    ex = card["exercise"]
    lines = [f"Exercise: {ex['title']}", ex["prompt"]]
    if ex.get("pattern"):
        lines.append(f"The intended approach: {ex['pattern']}")
    if ex.get("sample_case"):
        lines.append(f"Example: {ex['function']}(*{ex['sample_case']['args']!r}) should return {ex['sample_case']['expected']!r}")
    return "\n".join(lines)


def hint_prompt(card: dict, code: str = "", level: int = 1, failure: dict | None = None) -> str:
    level = max(1, min(3, int(level or 1)))
    parts = [
        f"You are a patient coding tutor. {LEARNER}",
        f"Give a level-{level} hint. {HINT_LEVELS[level]} Under 80 words. Never give the full solution. Reply with the hint only.",
        exercise_context(card),
    ]
    if code.strip():
        parts.append("Their code so far:\n```python\n" + code.strip() + "\n```")
    if failure:
        parts.append(
            f"A failing test: called with {failure.get('args')!r}, expected {failure.get('expected')!r}, "
            f"got {failure.get('actual')!r}." + (f" Error: {failure['error']}" if failure.get("error") else "")
        )
    return "\n\n".join(parts)


def review_prompt(card: dict, code: str) -> str:
    return "\n\n".join(
        [
            f"You are a friendly reviewer. {LEARNER} Their solution passes all tests. Review it briefly.",
            "Cover, in under 140 words of prose:\n"
            "1. How fast it is, in plain words (for example \"it walks through the list once\").\n"
            "2. One edge case or follow-up question an interviewer might raise.\n"
            "3. One thing to say out loud when explaining it, and one habit (naming, edge cases, not changing the input) if it applies.\n"
            "4. One production practice that would matter if this ran for real on their stack, in one sentence.\n"
            "No rewritten code.",
            exercise_context(card),
            "Their solution:\n```python\n" + code.strip() + "\n```",
        ]
    )


def explain_prompt(text: str, note: str = "") -> str:
    return "\n\n".join(
        [
            f"{LEARNER}\nThey saved this to understand better:\n\"\"\"\n{text.strip()}\n\"\"\"",
            f"Their note about what confuses them: {note.strip()}" if note.strip() else "",
            "Explain it to them. Say what it is in one plain sentence first. Then show a tiny Python example "
            "in a ```python block with a comment on each line, about something other than their exercise. "
            "Then one or two sentences on why it matters at work. Under 180 words.",
        ]
    ).replace("\n\n\n\n", "\n\n")


def run_exercise(problem: dict, code: str, timeout: int = 10) -> dict:
    """Run ``code`` against the exercise's cases and summarise the result as a plain dict."""
    cases = [{"args": c["args"], "expected": c["expected"]} for c in problem.get("cases", [])]
    result = run_cases(code, problem["fn"], cases, unordered=problem.get("unordered", False), timeout=timeout)
    failure = first_failure(result)
    return {
        "passed": result["passed"],
        "passed_count": result["passed_count"],
        "total": result["total"],
        "fatal_error": result["fatal_error"],
        "timed_out": result["timed_out"],
        "first_failure": (
            {"args": failure["args"], "expected": failure["expected"], "actual": failure["actual"], "error": failure["error"]}
            if failure
            else None
        ),
    }
