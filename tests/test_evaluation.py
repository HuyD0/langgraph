"""Scoring the tutor.

The leak detector is the tutor's guard rail, so it gets the most adversarial
tests in the project: prose that *looks* like code must stay clean, and code
hidden inside prose must still be caught.
"""

from __future__ import annotations

import pytest

from drill.evaluation import build_scorers, detect_code_leak, hint_word_count

# Real hints. None of these may be flagged.
GOOD_HINTS = [
    "What does your loop do when the list is empty? Walk through it on that case.",
    "You are scanning the whole list for each element. Is there a structure that "
    "answers 'have I seen this before?' in one step?",
    "Think about what you need to remember as you move from left to right.",
    "Your answer returns the values, but the problem asks for their positions.",
    "Consider sorting the intervals first. What becomes true about neighbours then?",
    "A dictionary would give you that lookup in constant time. What should the key be?",
    # Prose whose wording overlaps Python keywords - the false positives a
    # keyword-matching detector would produce.
    "Consider what has to be true for each element in the list:",
    "Ask yourself what this loop is really for:",
    "There is a simpler approach if the input is already sorted:",
    "Think about what you would return if the list were empty.",
    "Your function returns early. Is that right while there are items left?",
    "The while condition is the part to re-read.",
]

# Leaked answers. All of these must be caught.
LEAKED_HINTS = [
    "Try this:\n```python\nseen = {}\n```",
    "You need:\n    return [seen[target - n], i]",
    "Use a dict:\n  seen = {}\n  for i, n in enumerate(nums):",
    "Just do seen.setdefault(key, []).append(word) for each word.",
    "Start with:\nimport collections",
    "Write   for i in range(len(nums)):\nand check each pair.",
    "def two_sum(nums, target):",
    "Set best = 0 first.",
    "The fix is grid[r][c] = '0' after you visit it.",
]


@pytest.mark.parametrize("hint", GOOD_HINTS)
def test_legitimate_hints_are_not_flagged(hint):
    verdict = detect_code_leak(hint)
    assert not verdict.leaked, f"false positive ({verdict.evidence}) on: {hint!r}"


@pytest.mark.parametrize("hint", LEAKED_HINTS)
def test_leaked_code_is_caught(hint):
    verdict = detect_code_leak(hint)
    assert verdict.leaked, f"missed a leak in: {hint!r}"
    assert verdict.evidence


def test_verdict_is_truthy():
    assert bool(detect_code_leak("return x")) is True
    assert bool(detect_code_leak("Think it through.")) is False


def test_empty_and_none_are_safe():
    assert not detect_code_leak("")
    assert not detect_code_leak(None)  # type: ignore[arg-type]


def test_evidence_is_deduplicated():
    verdict = detect_code_leak("x = 0\ny = 0\nz = 0")
    assert len(verdict.evidence) == len(set(verdict.evidence))


def test_detector_is_bounded_on_a_pathological_input():
    """A huge input must not stall an eval run."""
    import time

    start = time.perf_counter()
    detect_code_leak("word " * 20000)
    assert time.perf_counter() - start < 5.0


def test_word_count():
    assert hint_word_count("one two three") == 3
    assert hint_word_count("") == 0


def test_scorers_build_without_a_judge():
    scorers = build_scorers(include_judge=False)
    names = {s.name for s in scorers}
    assert names == {"no_code_leak", "hint_is_brief", "hint_cites_failure"}


def test_no_code_leak_scorer_agrees_with_the_detector():
    scorer = next(s for s in build_scorers() if s.name == "no_code_leak")
    assert scorer(outputs="What happens on an empty list?") is True
    assert scorer(outputs="return [seen[x], i]") is False


def test_brevity_scorer():
    scorer = next(s for s in build_scorers() if s.name == "hint_is_brief")
    assert scorer(outputs="short hint") is True
    assert scorer(outputs="word " * 200) is False


def test_cites_failure_scorer():
    scorer = next(s for s in build_scorers() if s.name == "hint_cites_failure")
    assert scorer(inputs={"failing_input": "empty list"},
                  outputs="What happens on an empty list?") is True
    assert scorer(inputs={"failing_input": "zzzz"}, outputs="Generic advice.") is False
    # Nothing to cite: do not punish.
    assert scorer(inputs={}, outputs="Generic advice.") is True
