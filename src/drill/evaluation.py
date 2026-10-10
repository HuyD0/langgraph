"""Scoring the tutor itself.

A tutor that quietly starts handing out answers still *feels* helpful - you solve
more problems, faster - while teaching you nothing. You would not notice until an
interview, which is the worst possible time to find out.

So the rule the hint prompt cares most about ("never write code") is checked
mechanically here, by a scorer that runs over recorded sessions. Edit a prompt,
re-run the eval, and a regression shows up as a number rather than as a habit.

The leak detector is deliberately **deterministic** - no LLM judge. It is cheap,
it runs in CI with no credentials, and it never disagrees with itself between runs.
The optional LLM judge below catches the subtler case the regexes cannot: prose
that describes the algorithm so completely that writing it out is mechanical.
"""

from __future__ import annotations

import ast
import re
import textwrap
from dataclasses import dataclass

# Two-layer detection.
#
# Layer 1 - regexes, for shapes that are unambiguous wherever they appear.
_CODE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"```", "fenced code block"),
    (r"\w+\.(append|pop|add|setdefault|sort|extend|update)\s*\(", "collection method call"),
    (r"\w+\[[^\]]+\]\s*=", "item assignment"),
    (r"^\s{4,}\S+.*[=:]\s*\S", "indented code line"),
)
_COMPILED = tuple((re.compile(p, re.MULTILINE), label) for p, label in _CODE_PATTERNS)

# Layer 2 - actually parse it.
#
# Regexes cannot tell "for i in range(n):" from the English phrase "...for each
# element in the list:". Both match any pattern loose enough to catch the first.
# Python's own parser can tell them apart, so we ask it: a fragment is code if it
# parses as one of these statement types. Prose overwhelmingly does not parse at all.
_CODE_NODES = (
    ast.For, ast.While, ast.If, ast.FunctionDef, ast.Return,
    ast.Import, ast.ImportFrom, ast.Assign, ast.AugAssign,
)

_NODE_LABELS = {
    "For": "for loop", "While": "while loop", "If": "if statement",
    "FunctionDef": "function definition", "Return": "return statement",
    "Import": "import statement", "ImportFrom": "import statement",
    "Assign": "assignment", "AugAssign": "assignment",
}

# Parsing every word offset of every line is O(words) parses per hint. Hints are
# capped at ~90 words, so this is microseconds, but the bound keeps a pathological
# input from stalling an eval run.
_MAX_PARSE_ATTEMPTS = 300

# How many times to trim a fragment back before giving up on it.
_MAX_TRUNCATIONS = 3
_INDENT_WIDTH = 4

_WORD_START = re.compile(r"\b\w")


def _parse_kind(fragment: str) -> str | None:
    """Label ``fragment`` if it parses as a code statement, else None.

    Wrapped in a dummy function so a bare ``return`` is legal, and retried with a
    ``pass`` body so a block header like ``for i in range(n):`` parses too.
    """
    for body in (fragment, fragment + "\n    pass"):
        try:
            tree = ast.parse("def _wrapper():\n" + textwrap.indent(body, "    "))
        except (SyntaxError, ValueError, MemoryError, RecursionError):
            continue
        for node in tree.body[0].body:  # type: ignore[attr-defined]
            # A valueless `return` is nearly always truncated prose ("...would
            # return if the list were empty"), not a leaked line of code.
            if isinstance(node, ast.Return) and node.value is None:
                continue
            if isinstance(node, _CODE_NODES):
                return _NODE_LABELS.get(type(node).__name__, "code statement")
    return None


def _syntax_cut(fragment: str) -> str | None:
    """Trim ``fragment`` back to where the parser first objected.

    Code embedded in a sentence - "Set best = 0 first." - does not parse whole,
    but its prefix does. Rather than guessing where the code ends with a regex,
    ask the parser: ``SyntaxError.offset`` points at the first token it could not
    use, so everything before that is the candidate.
    """
    try:
        ast.parse("def _wrapper():\n" + textwrap.indent(fragment, "    "))
    except SyntaxError as exc:
        if exc.lineno == 2 and exc.offset:
            cut = max(exc.offset - 1 - _INDENT_WIDTH, 0)
            trimmed = fragment[:cut].rstrip()
            return trimmed if trimmed and trimmed != fragment else None
    except (ValueError, MemoryError, RecursionError):
        return None
    return None


def _statement_kind(fragment: str) -> str | None:
    """Does ``fragment``, or a prefix of it, parse as a Python statement?"""
    current = fragment.strip()
    if not current:
        return None
    for _ in range(_MAX_TRUNCATIONS):
        kind = _parse_kind(current)
        if kind:
            return kind
        shorter = _syntax_cut(current)
        if shorter is None:
            return None
        current = shorter
    return None


def _parsed_evidence(hint: str) -> list[str]:
    """Scan each line for a substring that parses as a Python statement."""
    found: list[str] = []
    attempts = 0
    for line in (hint or "").splitlines():
        for match in _WORD_START.finditer(line):
            if attempts >= _MAX_PARSE_ATTEMPTS:
                return found
            attempts += 1
            kind = _statement_kind(line[match.start():])
            if kind:
                found.append(kind)
                break  # one finding per line is enough
    return found


@dataclass(frozen=True)
class LeakVerdict:
    """Whether a hint leaked code, and what gave it away."""

    leaked: bool
    evidence: tuple[str, ...]

    def __bool__(self) -> bool:
        return self.leaked


def detect_code_leak(hint: str) -> LeakVerdict:
    """Flag a hint that contains Python rather than describing it in prose."""
    evidence = [label for pattern, label in _COMPILED if pattern.search(hint or "")]
    evidence.extend(_parsed_evidence(hint))
    # dict.fromkeys de-duplicates while preserving order, so the evidence reads
    # in the order it was found rather than in an arbitrary set order.
    return LeakVerdict(leaked=bool(evidence), evidence=tuple(dict.fromkeys(evidence)))


def hint_word_count(hint: str) -> int:
    return len((hint or "").split())


# ---------------------------------------------------------------------------
# MLflow scorers
# ---------------------------------------------------------------------------


def build_scorers(include_judge: bool = False) -> list:
    """Assemble the scorer list for :func:`evaluate_hints`.

    Imports MLflow lazily so this module stays importable in a bare environment.

    Args:
        include_judge: add an LLM-as-judge scorer for the "describes the algorithm
            too completely" case. Needs a judge model configured, so it is off by
            default and the deterministic scorers run everywhere.
    """
    from mlflow.genai.scorers import scorer

    @scorer(name="no_code_leak", description="Hint must not contain Python code.")
    def no_code_leak(outputs) -> bool:
        return not detect_code_leak(_as_text(outputs)).leaked

    @scorer(name="hint_is_brief", description="Hint stays under 90 words.")
    def hint_is_brief(outputs) -> bool:
        return hint_word_count(_as_text(outputs)) <= 90

    @scorer(
        name="hint_cites_failure",
        description="Hint refers to the specific failing case, not generic advice.",
    )
    def hint_cites_failure(inputs, outputs) -> bool:
        text = _as_text(outputs).lower()
        failing = str((inputs or {}).get("failing_input", "")).lower()
        if not failing:
            return True  # nothing to cite; do not punish
        tokens = [t for t in re.findall(r"[\w']+", failing) if len(t) > 1]
        return any(t in text for t in tokens)

    scorers = [no_code_leak, hint_is_brief, hint_cites_failure]

    if include_judge:
        from mlflow.genai.scorers import Guidelines

        scorers.append(
            Guidelines(
                name="withholds_the_answer",
                guidelines=(
                    "The response must guide the learner toward the solution without "
                    "stating the complete algorithm step by step. Asking a leading "
                    "question or naming a data structure passes. Describing the full "
                    "sequence of operations such that writing the code is mechanical fails."
                ),
            )
        )
    return scorers


def _as_text(outputs) -> str:
    """Normalise a scorer's `outputs` into plain text."""
    if isinstance(outputs, str):
        return outputs
    if isinstance(outputs, dict):
        for key in ("hint", "feedback", "output", "response", "content"):
            if key in outputs:
                return str(outputs[key])
    return str(outputs)


def evaluate_hints(dataset: list[dict], include_judge: bool = False):
    """Run the hint scorers over a dataset of recorded hints.

    Each row is ``{"inputs": {...}, "outputs": "<the hint text>"}``. Build one from
    your own history with :func:`dataset_from_traces`, or hand-write rows to pin
    down a regression you have just seen.
    """
    import mlflow

    return mlflow.genai.evaluate(data=dataset, scorers=build_scorers(include_judge))


def dataset_from_traces(experiment_name: str = "daily-drill", limit: int = 100) -> list[dict]:
    """Pull hints out of recorded MLflow traces into an evaluation dataset.

    This is the payoff for tracing every session: your eval set is your own
    practice history, so the tutor is scored on the hints it actually gave you.
    """
    import mlflow

    mlflow.flush_trace_async_logging()
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        return []

    rows: list[dict] = []
    traces = mlflow.search_traces(locations=[experiment.experiment_id], max_results=limit)
    for _, trace_row in traces.iterrows():
        trace = mlflow.get_trace(trace_row.trace_id)
        if trace is None:
            continue
        for span in trace.data.spans:
            if span.name != "hint" or not span.outputs:
                continue
            text = _as_text(span.outputs)
            if text:
                rows.append(
                    {
                        "inputs": {"problem_id": (span.inputs or {}).get("problem_id", "")},
                        "outputs": text,
                    }
                )
    return rows
