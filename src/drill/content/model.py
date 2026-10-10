"""How a lesson is written down. Every file in :mod:`drill.content.modules` uses these.

A **module** is one chapter of the learning path. A **lesson** is one entry in it:
something to read (``learn``), a quick question (``check``), an exercise to code
(``exercise``) and how to talk about it in an interview (``angle``). The lesson's id is
the exercise's id, and the exercise's ``fn`` is the function the learner writes.

The helpers below only build plain dicts and lists. They exist so a lesson reads as a
form to fill in, and so a typo in a field name fails loudly at import time rather than
quietly producing an empty box on the page.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Module:
    """One chapter: an id used in URLs and progress, a title, a one-line blurb, lessons in order."""

    id: str
    title: str
    blurb: str
    lessons: list[dict] = field(default_factory=list)

    @property
    def lesson_ids(self) -> list[str]:
        return [lesson["id"] for lesson in self.lessons]


def module(id: str, title: str, blurb: str) -> Module:
    return Module(id=id, title=title, blurb=blurb)


def case(*args: Any, expected: Any, sample: bool = False) -> dict:
    """One test: the arguments the function is called with, and the answer it must return.

    ``sample=True`` marks the one case shown to the learner as the worked example; the
    rest are held back, like a real interview.
    """
    return {"args": list(args), "expected": expected, "sample": sample}


def exercise(
    *,
    title: str,
    topic: str,
    difficulty: str,
    fn: str,
    prompt: str,
    pattern: str,
    target: str,
    starter: str,
    solution: str,
    cases: list[dict],
    guided: str,
    concepts: list,
    byhand: str,
    why: str,
    realworld: str | None = None,
    gotchas: list | None = None,
    fills: list[str] | None = None,
    unordered: bool = False,
) -> dict:
    """The Build step of a lesson.

    ``guided`` is the fill-in-the-blanks scaffold, with ``___`` for each blank, and
    ``fills`` are the intended answers in order; :func:`drill.content.build.check_exercises`
    fills them in and runs the result, so a scaffold can never drift from its solution.
    ``concepts``, ``byhand``, ``why`` and ``gotchas`` are the Learn panel next to the editor.
    """
    assert all(c["sample"] for c in cases[:1]) or any(c["sample"] for c in cases) or not cases, (
        f"{fn}: mark one case as the sample"
    )
    return {
        "title": title, "topic": topic, "difficulty": difficulty, "fn": fn,
        "prompt": prompt, "pattern": pattern, "target": target, "realworld": realworld,
        "starter": starter, "solution": solution, "cases": cases, "unordered": unordered,
        "guided": guided, "fills": fills,
        "concepts": concepts, "byhand": byhand, "why": why, "gotchas": gotchas,
    }


def example(caption: str, code: str) -> dict:
    """The worked example under the Learn text."""
    return {"caption": caption, "code": code}


def question(text: str, options: list[str], *, answer: int, why: str) -> dict:
    """The Check step: a multiple-choice question. ``answer`` is the index of the right option."""
    assert 0 <= answer < len(options), f"answer {answer} is not one of {len(options)} options"
    return {"question": text, "options": options, "answer": answer, "why": why}


def angle(*, pattern: str, text: str, say: str, classic: str | None = None) -> dict:
    """The Interview step: the pattern, why it matters, a sentence to say out loud, and the
    classic interview problem (from :mod:`drill.problems`) that uses the same idea."""
    return {"pattern": pattern, "text": text, "say": say, "classic": classic}


def stack(title: str, code: str) -> dict:
    """The "In your stack" box: the same idea in Databricks, LangGraph, LangChain or MLflow."""
    return {"title": title, "code": code}


def lesson(
    owner: Module,
    id: str,
    *,
    title: str,
    learn: list[str],
    example: dict,
    check: dict,
    angle: dict,
    exercise: dict,
    stack: dict | None = None,
) -> dict:
    """Add one lesson to a module. Lessons appear on the page in the order they are added."""
    assert id not in owner.lesson_ids, f"{id} is already in {owner.id}"
    entry = {
        "id": id, "title": title, "learn": learn, "example": example, "check": check,
        "angle": angle, "stack": stack, "exercise": exercise,
    }
    owner.lessons.append(entry)
    return entry
