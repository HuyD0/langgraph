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

import re

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Module:
    """One chapter: an id used in URLs and progress, a title, a one-line blurb, lessons in order."""

    id: str
    title: str
    blurb: str
    lessons: list[dict] = field(default_factory=list)
    planned: list[dict] = field(default_factory=list)  # "coming soon" lessons: a title and one line, no exercise yet
    setting: str = ""  # the world every tutor example and question is set in, like the platform team's repos

    @property
    def lesson_ids(self) -> list[str]:
        return [lesson["id"] for lesson in self.lessons]


def module(id: str, title: str, blurb: str, *, setting: str = "") -> Module:
    """A chapter. ``setting`` describes the world its examples live in; the AI tutor gets it with
    every question, so a "harder one like this" stays in that world instead of inventing another."""
    return Module(id=id, title=title, blurb=blurb, setting=setting)


def planned(owner: Module, id: str, title: str, blurb: str) -> dict:
    """A lesson that is coming but not written yet: shown faded as "Coming soon", never counted.

    When it is written, replace this call with a ``lesson(...)`` of the same id, so nothing
    that links to it has to change.
    """
    assert id not in owner.lesson_ids and id not in [p["id"] for p in owner.planned], f"{id} is already in {owner.id}"
    entry = {"id": id, "title": title, "blurb": blurb}
    owner.planned.append(entry)
    return entry


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
    machine: dict | None = None,
    practice: dict | None = None,
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
        "guided": guided, "fills": fills, "machine": machine, "practice": practice,
        "concepts": concepts, "byhand": byhand, "why": why, "gotchas": gotchas,
    }


def machine(*, bins: list[str], who: list[str], label_field: str | None = None,
            label_arg: int | None = None, leak_arg: int | None = None) -> dict:
    """The Build step's machine: the example's rows travel through the function into bins.

    Only for exercises that sort rows into groups: the first argument is a list of rows (dicts)
    and the sample case returns one list per bin, together holding exactly those rows.
    ``bins`` are the returned lists' names in order, ``who`` says in a few words who belongs in
    each. Each row's pill shows ``row[label_field]``, or ``row[args[label_arg]]`` when the field
    name is itself an argument (``key`` in split_by_key). ``leak_arg`` turns on the leak check:
    a value of that field found in more than one bin is flagged.
    """
    assert len(bins) == len(who) and 2 <= len(bins) <= 4, "a machine has 2 to 4 bins, each with a who; 4 make a 2 by 2 map"
    assert (label_field is None) != (label_arg is None), "label pills by a field or by an argument, not both"
    return {"bins": bins, "who": who, "label_field": label_field, "label_arg": label_arg, "leak_arg": leak_arg}


EVIDENCE_KINDS = ("code", "chain", "plan", "claim", "prompt")


def evidence(kind: str, **data: Any) -> dict:
    """What a practice question is about, drawn above it: ``code`` (YAML, HCL or a log, with
    ``text`` and optional ``title``), ``chain`` (a field's stops from YAML to provider, each
    ``{"label", "sub", "state"}`` with state ok, now or later, plus an optional ``snippet``),
    ``plan`` (``summary`` counts and ``changes`` rows ``{"sym", "address", "note"}``), ``claim``
    (a quote: something an AI assistant said, or an idea someone brought; ``who`` names it) or ``prompt`` (a prompt to an AI assistant, ``___`` for the gap)."""
    assert kind in EVIDENCE_KINDS, f"unknown evidence kind {kind!r}"
    return {"kind": kind, **data}


def ask(question: str, options: list[str], *, answer: int, clue: str, why: str,
        evidence: dict | None = None, wrong: list[str | None] | None = None, pick: bool = False) -> dict:
    """One practice question: one screen, one plain question about the evidence above it.

    A wrong pick shows its line from ``wrong`` (or a plain "not quite"); help is ``clue`` first,
    then the answer. ``why`` is shown once it's right. With ``pick``, the plan's own rows are the
    options (tap the change you'd stop on), and ``answer`` is a row's position.
    """
    n = len(evidence["changes"]) if pick else len(options)
    assert 2 <= n <= 6 and 0 <= answer < n, f"{question[:40]}: answer {answer} out of {n} options"
    assert not pick or (evidence and evidence["kind"] == "plan"), "pick needs plan evidence"
    right = evidence["changes"][answer]["address"] if pick else options[answer]
    assert right.lower() not in clue.lower(), f"{question[:40]}: the clue gives the answer away"
    assert wrong is None or len(wrong) == n, f"{question[:40]}: one wrong line per option"
    return {"question": question, "options": options, "answer": answer, "clue": clue, "why": why,
            "evidence": evidence, "wrong": wrong, "pick": pick}


def fix(question: str, *, start: str, answer: str, rules: dict, goal: list[dict] | None = None,
        clue: str, why: str, file: str = "") -> dict:
    """A practice question where the learner edits a YAML file until the check passes, like a
    product team's pull request. ``rules`` is the contract and ``goal`` what the fix must do (see
    :mod:`drill.content.yaml_rules`); ``answer`` is one fixed version, shown after the clue."""
    assert start.strip() and answer.strip() and rules.get("path"), f"{question[:40]}: a fix needs start, answer and rules"
    return {"kind": "fix", "question": question, "start": start, "answer": answer, "rules": rules,
            "goal": goal or [], "clue": clue, "why": why, "file": file}


def practice(*, intro: str, asks: list[dict], explain: str | None = None) -> dict:
    """The Build step as a few questions about real evidence, for platform lessons where the job
    is reading YAML, plans and logs rather than writing Python. Three to five asks, easy to
    tricky; the Python exercise stays one tap away. ``explain`` is the Explain step's big idea
    for someone who practised this way rather than coding."""
    assert 2 <= len(asks) <= 6, "a practice set has two to six questions"
    return {"intro": intro, "asks": asks, "explain": explain}


def example(caption: str, code: str) -> dict:
    """The worked example under the Learn text."""
    return {"caption": caption, "code": code}


def question(text: str, options: list[str], *, answer: int, why: str) -> dict:
    """The Check step: a multiple-choice question. ``answer`` is the index of the right option."""
    assert 0 <= answer < len(options), f"answer {answer} is not one of {len(options)} options"
    return {"question": text, "options": options, "answer": answer, "why": why}


_GAP = re.compile(r"\[\[(.+?)\]\]")


def cloze(say: str) -> tuple[str, list]:
    """Split a sentence with gaps into the plain sentence and the pieces the page shows.

    A gap is ``[[answer|wrong|wrong::clue]]``: the right word first, two tempting wrong ones,
    then a clue that points at the answer without giving it. The pieces alternate text and
    gaps: ``["When a stack changes I find everything ", {"answer": ..., "wrong": [...],
    "clue": ...}, " of it, ..."]``. A sentence with no gaps gives an empty list.
    """
    pieces: list = []
    at = 0
    for m in _GAP.finditer(say):
        body, _, clue = m.group(1).partition("::")
        answer, *wrong = [w.strip() for w in body.split("|")]
        assert len(wrong) == 2, f"gap {answer!r} needs two wrong choices, has {len(wrong)}"
        assert clue.strip(), f"gap {answer!r} needs a clue: help is a clue first, then the answer"
        assert answer not in wrong, f"gap {answer!r} lists its answer as a wrong choice"
        pieces += [say[at:m.start()], {"answer": answer, "wrong": wrong, "clue": clue.strip()}]
        at = m.end()
    if not pieces:
        return say, []
    pieces.append(say[at:])
    assert 2 <= len(pieces) // 2 <= 3, f"a sentence takes two or three gaps, not {len(pieces) // 2}"
    plain = "".join(p if isinstance(p, str) else p["answer"] for p in pieces)
    return plain, pieces


def angle(*, pattern: str, text: str, say: str, classic: str | None = None) -> dict:
    """The Explain step: the pattern, why it matters, a sentence to say out loud, and the
    classic interview problem (from :mod:`drill.problems`) that uses the same idea.

    ``say`` may mark two or three gaps (see :func:`cloze`); then the learner rebuilds the
    sentence by picking words, and ``say`` itself is stored plain for everything else."""
    plain, pieces = cloze(say)
    return {"pattern": pattern, "text": text, "say": plain, "cloze": pieces, "classic": classic}


def stack(title: str, code: str) -> dict:
    """The "In your stack" box: the same idea in Databricks, LangGraph, LangChain or MLflow."""
    return {"title": title, "code": code}


# The seven traits of trustworthy AI in the NIST AI Risk Management Framework (AI RMF 1.0),
# keyed by the short name the page shows. Order is NIST's.
TRAITS = {
    "valid": "Valid and reliable",
    "safe": "Safe",
    "secure": "Secure and resilient",
    "accountable": "Accountable and transparent",
    "explainable": "Explainable",
    "private": "Privacy-enhanced",
    "fair": "Fair",
}


def trust(trait: str, *, phrase: str, view: str, tip: str, rmf: str, tevv: bool = False) -> dict:
    """A trust mark (see :mod:`drill.content.trust`): the ember on the page, placed right after
    ``phrase`` in the lesson's Learn text.
    ``view`` says why this moment matters for responsible AI, privacy or governance; ``tip`` is
    one thing to do about it; ``rmf`` is the NIST AI RMF reference, like "Measure 2.10". ``tevv``
    marks a moment that produces test evidence (NIST's test, evaluation, verification and validation)."""
    assert trait in TRAITS, f"unknown trait {trait!r}; use one of {', '.join(TRAITS)}"
    return {"trait": trait, "phrase": phrase, "view": view, "tip": tip, "rmf": rmf, "tevv": tevv}


def source(title: str, url: str) -> list[str]:
    """A page a lesson's facts were checked against: what it is, and where."""
    assert url.startswith("https://"), f"{title}: a source needs an https link"
    return [title, url]


SCREEN_KINDS = ("flow", "header", "changes", "log", "diff", "history")


def screen(kind: str, *, caption: str, steps: list[str], tips: list[str] | None = None, **data: Any) -> dict:
    """One view of a tool, redrawn on the page with numbered callouts: a Spacelift run's header,
    its Changes list, its planning log, a plan diff, its history, or a flow of steps.

    The page draws it from ``data`` in the app's own look, so it fits a phone and follows the
    theme. Parts of the view carry a number (``"n": 2``); ``steps`` explain them in order, so
    step 1 is about the part marked 1. The content can match a real screenshot exactly.
    ``tips`` are good habits for this view, shown under the steps.
    """
    assert kind in SCREEN_KINDS, f"unknown screen kind {kind!r}"
    used = sorted({n for n in _numbers(data)})
    assert used == list(range(1, len(steps) + 1)), f"{caption}: callouts {used} need one step each, in order"
    return {"kind": kind, "caption": caption, "steps": steps, "tips": tips or [], "data": data}


def _numbers(value: Any):
    if isinstance(value, dict):
        if isinstance(value.get("n"), int):
            yield value["n"]
        for v in value.values():
            yield from _numbers(v)
    elif isinstance(value, list):
        for v in value:
            yield from _numbers(v)


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
    checked: str | None = None,
    sources: list[list[str]] | None = None,
    walkthrough: list[dict] | None = None,
) -> dict:
    """Add one lesson to a module. Lessons appear on the page in the order they are added.

    ``checked`` is the day (YYYY-MM-DD) the lesson's facts were last checked against its
    ``sources``. Lessons about products that change often must have both; the page shows the
    date, and ``drill content stale`` lists lessons due for another look.
    """
    assert id not in owner.lesson_ids, f"{id} is already in {owner.id}"
    if checked is not None:
        import datetime
        datetime.date.fromisoformat(checked)  # fails loudly on a typo
        assert sources, f"{id}: a checked date needs the sources it was checked against"
    entry = {
        "id": id, "title": title, "learn": learn, "example": example, "check": check,
        "angle": angle, "stack": stack, "exercise": exercise, "checked": checked, "sources": sources,
        "walkthrough": walkthrough,
    }
    owner.lessons.append(entry)
    return entry
