"""What a practice problem is made of."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TestCase:
    """One input/output pair the submitted function must satisfy."""

    # Tells pytest this is a data class, not a test class to collect.
    # Without it, the name "TestCase" trips pytest's test-discovery heuristic.
    __test__ = False

    args: tuple[Any, ...]
    expected: Any
    # Shown to you up front as a worked example. The rest are held back, so you
    # cannot pass by special-casing the samples - the same deal as a real interview.
    is_sample: bool = False


@dataclass(frozen=True)
class Problem:
    """A single interview problem, plus everything the tutor needs to teach it."""

    id: str
    title: str
    topic: str
    difficulty: str  # "easy" | "medium" | "hard"
    prompt: str
    function_name: str
    starter_code: str
    test_cases: tuple[TestCase, ...]
    # Used by the `explain` node once you are out of attempts, and by the test
    # suite to prove every problem in the bank is actually solvable.
    reference_solution: str
    target_complexity: str
    # The transferable idea. This is what you are really drilling - the pattern
    # generalises to dozens of problems, the specific puzzle does not.
    pattern: str
    # True when the answer's ordering is not significant (e.g. grouped anagrams),
    # so the runner sorts both sides before comparing.
    unordered: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def samples(self) -> tuple[TestCase, ...]:
        return tuple(tc for tc in self.test_cases if tc.is_sample)

    @property
    def hidden(self) -> tuple[TestCase, ...]:
        return tuple(tc for tc in self.test_cases if not tc.is_sample)
