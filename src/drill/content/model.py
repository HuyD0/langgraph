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


def practice(*, intro: str, asks: list[dict], explain: str | None = None, pattern: str | None = None,
             realworld: str | None = None, gotchas: list | None = None) -> dict:
    """The Build step as a few questions about real evidence, for lessons whose skill is a decision
    or reading a plan, run, policy or trace rather than writing Python; the tab says Practice. Three to five asks, easy to
    tricky; the Python exercise stays one tap away.

    The Explain step then describes what the learner did, not the Python they didn't write:
    ``pattern`` names the way of thinking they used (the heading, like "Cross it out: job or bar?"),
    ``explain`` is the big idea, and ``realworld`` is "Where you'll use this" in their job. ``gotchas``,
    when given, replace the exercise's gotchas in practice mode (for ones that only make sense in code)."""
    assert 2 <= len(asks) <= 6, "a practice set has two to six questions"
    return {"intro": intro, "asks": asks, "explain": explain, "pattern": pattern, "realworld": realworld, "gotchas": gotchas}


def example(caption: str, code: str) -> dict:
    """The worked example under the Learn text."""
    return {"caption": caption, "code": code}


def question(text: str, options: list[str], *, answer: int, why: str, clue: str | None = None) -> dict:
    """The Check step's first question: multiple choice. ``answer`` is the index of the right
    option. With a ``clue``, help shows it before the answer. More questions: ``content/checks/``."""
    assert 0 <= answer < len(options), f"answer {answer} is not one of {len(options)} options"
    assert not clue or options[answer].lower() not in clue.lower(), f"{text[:40]}: the clue gives the answer away"
    return {"question": text, "options": options, "answer": answer, "why": why, **({"clue": clue} if clue else {})}


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


def callback(to: str, *, phrase: str, idea: str, here: str, again: dict | None = None) -> dict:
    """A sticker callback (see :mod:`drill.content.callbacks`): the sticker of an earlier lesson ``to``,
    placed right after ``phrase`` in this lesson's Learn text, where the lesson uses that lesson's idea.
    ``idea`` names the idea in a few words (the card's heading); ``here`` says in one or two plain
    sentences what it means in this lesson. ``again`` is an optional Look again question (made with
    :func:`ask`, so it has a clue) shown after Learn: one question that uses the earlier idea."""
    assert to and phrase and idea and here, "a callback needs to, phrase, idea and here"
    return {"to": to, "phrase": phrase, "idea": idea, "here": here, "again": again}


DIAGRAM_KINDS = ("flow", "tree", "graph", "table", "chart", "pair")


def diagram(kind: str, *, caption: str, callouts: list[str], after: int = 0, **data) -> dict:
    """One picture for a lesson's Learn step (see :mod:`drill.content.diagrams`), drawn by the page from
    this data. ``kind`` is flow, tree, graph, table or chart; ``caption`` says in plain words what the
    picture shows; ``callouts`` are the numbered notes, in the order of the numbers on the picture;
    ``after`` is the Learn paragraph the picture follows. The rest is the kind's own data.

    Three ways a picture can do more than sit still. ``steps``: a list of ``{"now": ..., "say": ...}``
    the learner taps through (``now`` is a node index for flow, a node id for graph, a row index for
    tree), each step's ``say`` replacing the caption. ``play=True`` on a tree whose bars are time: they
    grow in once, in time order, with a Replay. ``live=True``: in Build, the same kind of picture is
    drawn from what the learner's function returned on the example (page/diagrams.js, ``LIVE``).
    A ``pair`` is two small pictures, ``before`` and ``fixed``, each a dict with its own ``kind``,
    ``label`` and data, for a spot-the-difference lesson."""
    assert kind in DIAGRAM_KINDS, f"unknown diagram kind {kind!r}; use one of {', '.join(DIAGRAM_KINDS)}"
    assert 20 < len(caption) < 400 and 1 <= len(callouts) <= 6, "a caption of a sentence or three, and 1 to 6 callouts"
    need = {"flow": ("nodes",), "tree": ("rows", "max", "unit"), "graph": ("nodes", "edges"), "table": ("columns", "rows"), "chart": ("x", "y"), "pair": ("before", "fixed")}[kind]
    for key in need:
        assert key in data, f"a {kind} diagram needs {key}"
    if kind == "pair":
        for half in (data["before"], data["fixed"]):
            assert half["kind"] in ("table", "tree", "flow") and half.get("label"), "each half has a kind and a short label"
    if data.get("steps"):
        assert kind in ("flow", "graph", "tree") and all(s.get("say") and "now" in s for s in data["steps"]), "steps need now and say, on a flow, graph or tree"
    if data.get("play"):
        assert kind == "tree", "only a tree's bars play"
    if kind == "table":
        assert all(len(r) == len(data["columns"]) for r in data["rows"]), "every row has one cell per column"
    if kind == "graph":
        ids = {n["id"] for n in data["nodes"]}
        assert all(e["from"] in ids and e["to"] in ids for e in data["edges"]), "edges join known nodes"
    return {"kind": kind, "caption": caption, "callouts": callouts, "after": after, **data}


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


# ---------- picture cards: a lesson's Learn step as short cards, one idea and one picture each ----------
# The page draws each picture from this data (page/cards.js) in the app's own look; ``picture_text``
# says the same thing in words, for the tutor map, the MCP tools, search and screen readers.
# Two looks tell two kinds of thing apart by shape, never by a new colour: "solid" (a filled tile)
# and "dashed" (a ruler-edged tile). Icons are names from page.html's sprite (a test checks).
PICTURE_KINDS = ("piles", "crossout", "split", "rewrite", "pillars", "seesaw", "steps")
LOOKS = ("solid", "dashed")


def tile(text: str, *, icon: str | None = None, look: str = "solid") -> dict:
    """One tile in a pile or a split: a short phrase, an optional icon, drawn solid or dashed."""
    assert look in LOOKS, f"{text}: look is one of {LOOKS}"
    return {"text": text, "icon": icon, "look": look}


def pile(title: str, items: list, *, sub: str = "", look: str = "solid") -> dict:
    """A column of tiles under a heading. ``items`` are phrases, or ``(icon, phrase)`` pairs."""
    tiles = [tile(i[1], icon=i[0], look=look) if isinstance(i, tuple) else tile(i, look=look) for i in items]
    return {"title": title, "sub": sub, "look": look, "items": tiles}


def piles(*columns: dict, key: list[tuple[str, str]] | None = None) -> dict:
    """Two piles side by side, like jobs and bars. ``key`` labels the looks: ``[("solid", "job: functional"), ...]``."""
    assert len(columns) == 2, "piles are drawn as two columns"
    return {"kind": "piles", "piles": list(columns), "key": [list(k) for k in key or []]}


def struck(text: str, then: str, verdict: str, *, look: str = "solid", icon: str = "x") -> dict:
    """One row of a cross-out test: the line crossed out, what happens then, and what that makes it."""
    assert look in LOOKS
    return {"text": text, "then": then, "verdict": verdict, "look": look, "icon": icon}


def crossout(*rows: dict) -> dict:
    """The cross-out test: cross a line off, see what's lost."""
    assert rows, "a cross-out needs a row"
    return {"kind": "crossout", "rows": list(rows)}


def split(parts: list[str], into: list[dict]) -> dict:
    """A sentence cut into parts (``parts``), then the separate lines it becomes (``into``, made with :func:`tile`)."""
    assert len(parts) >= 2 and into, "a split cuts a sentence into at least two parts"
    return {"kind": "split", "parts": parts, "into": into}


def rewrite(*pairs: tuple[str, str]) -> dict:
    """Vague words, each crossed out and rewritten as something you can check: ``("fast", "under 5 seconds")``."""
    assert pairs, "a rewrite needs a pair"
    return {"kind": "rewrite", "pairs": [list(p) for p in pairs]}


def pillar(name: str, icon: str, question: str, *, short: str | None = None, chips: list[str] | None = None,
           open: bool = False) -> dict:
    """One pillar: its name, icon and question. The picture writes ``short`` (or the name) up the pillar,
    so keep it to one word; the list under the picture gives the full name. ``chips`` are short labels
    resting on it (a requirement like "R4 EU"); ``open`` marks a pillar nothing answers yet, in hint colours."""
    label = short or name
    assert " " not in label and len(label) <= 12, f"{name}: give a one-word short name of 12 letters at most"
    assert all(len(c) <= 8 for c in chips or []), f"{name}: chips are 8 characters at most, to fit a phone"
    return {"name": name, "short": label, "icon": icon, "question": question, "chips": chips or [], "open": open}


def pillars(roof: str, *columns: dict, list_questions: bool = True) -> dict:
    """A roof (``roof``, the thing being held up) on three to six pillars, each a question. With
    ``list_questions`` the questions are listed under the picture; otherwise only open pillars are."""
    assert 3 <= len(columns) <= 6, "three to six pillars fit a phone"
    return {"kind": "pillars", "roof": roof, "pillars": list(columns), "list": list_questions}


def seesaw(up: tuple[str, str], down: tuple[str, str], *, caption: str) -> dict:
    """A trade-off: the side that goes ``up`` (title, short line) and the side that pays, ``down``."""
    return {"kind": "seesaw", "up": list(up), "down": list(down), "caption": caption}


def steps(*items: tuple[str, str, str], decide: bool = False) -> dict:
    """Steps in order, each ``(icon, title, text)``. With ``decide``, the last step is drawn solid:
    the moment a person makes the call."""
    assert len(items) >= 2, "steps need at least two"
    return {"kind": "steps", "items": [list(i) for i in items], "decide": decide}


def card(heading: str, text: str, *, picture: dict | None = None, after: str | None = None,
         note: tuple[str, str] | None = None) -> dict:
    """One Learn card: a short heading, the text (with **bold** and `code`), an optional picture, an
    optional line after the picture, and an optional folded note ``(summary, text)``."""
    assert heading and text, "a card needs a heading and text"
    assert picture is None or picture.get("kind") in PICTURE_KINDS, f"{heading}: unknown picture"
    return {"heading": heading, "text": text, "picture": picture, "after": after,
            "note": list(note) if note else None}


def picture_text(p: dict | None) -> str:
    """A picture in words: what the tutor map, the MCP tools and screen readers get."""
    if not p:
        return ""
    k = p["kind"]
    if k == "piles":
        return " ".join(f"{c['title']}{' (' + c['sub'] + ')' if c['sub'] else ''}: "
                        + "; ".join(t["text"] for t in c["items"]) + "." for c in p["piles"])
    if k == "crossout":
        return " ".join(f'Cross out "{r["text"]}": {r["then"]} ({r["verdict"]}).' for r in p["rows"])
    if k == "split":
        return f'"{" ".join(p["parts"])}" splits into: ' + "; ".join(t["text"] for t in p["into"]) + "."
    if k == "rewrite":
        return " ".join(f'"{a}" becomes "{b}".' for a, b in p["pairs"])
    if k == "pillars":
        cols = []
        for c in p["pillars"]:
            rest = f" holds {', '.join(c['chips'])}" if c["chips"] else (" has nothing on it yet" if c["open"] else "")
            cols.append(f"{c['name']} ({c['question']}){rest}")
        return f"{p['roof']} rests on {len(cols)} pillars: " + "; ".join(cols) + "."
    if k == "seesaw":
        return f"{p['up'][0]} goes up ({p['up'][1]}) and {p['down'][0]} pays ({p['down'][1]}). {p['caption']}"
    if k == "steps":
        return " ".join(f"{n}. {t}: {x}" for n, (_, t, x) in enumerate(p["items"], 1))
    raise AssertionError(k)


def cards_learn(cards: list[dict]) -> list[str]:
    """The cards as Learn paragraphs, for everything that reads text (the tutor map, MCP tools, search)."""
    out = []
    for c in cards:
        parts = [f"{c['heading']}: {c['text']}", picture_text(c["picture"]), c["after"] or ""]
        if c["note"]:
            parts.append(f"{c['note'][0]}: {c['note'][1]}")
        out.append(" ".join(p for p in parts if p))
    return out


def _icons(cards: list[dict]):
    """Every icon name the cards use, for the test that checks page.html has each one."""
    for c in cards:
        p = c["picture"] or {}
        for col in p.get("piles", []):
            yield from (t["icon"] for t in col["items"] if t["icon"])
        yield from (r["icon"] for r in p.get("rows", []))
        yield from (t["icon"] for t in p.get("into", []) if t["icon"])
        yield from (c2["icon"] for c2 in p.get("pillars", []))
        yield from (i[0] for i in p.get("items", []))


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
    learn: list[str] | None = None,
    example: dict,
    check: dict,
    angle: dict,
    exercise: dict,
    stack: dict | None = None,
    checked: str | None = None,
    sources: list[list[str]] | None = None,
    walkthrough: list[dict] | None = None,
    cards: list[dict] | None = None,
) -> dict:
    """Add one lesson to a module. Lessons appear on the page in the order they are added.

    ``cards`` (made with :func:`card`) draw the Learn step as short cards with pictures, in place of
    ``learn`` paragraphs and the example; ``learn`` is then written from the cards, for everything that
    reads text. The ``example`` stays in the data for the tutor and the MCP tools.

    ``checked`` is the day (YYYY-MM-DD) the lesson's facts were last checked against its
    ``sources``. Lessons about products that change often must have both; the page shows the
    date, and ``drill content stale`` lists lessons due for another look.
    """
    assert id not in owner.lesson_ids, f"{id} is already in {owner.id}"
    assert (learn is None) != (cards is None), f"{id}: give learn paragraphs or cards, not both"
    if cards is not None:
        assert 2 <= len(cards) <= 7, f"{id}: two to seven cards"
        learn = cards_learn(cards)
    if checked is not None:
        import datetime
        datetime.date.fromisoformat(checked)  # fails loudly on a typo
        assert sources, f"{id}: a checked date needs the sources it was checked against"
    entry = {
        "id": id, "title": title, "learn": learn, "example": example, "check": check,
        "angle": angle, "stack": stack, "exercise": exercise, "checked": checked, "sources": sources,
        "walkthrough": walkthrough, "cards": cards,
    }
    owner.lessons.append(entry)
    return entry
