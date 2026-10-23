"""Assemble the Daily Drill page from its parts.

    uv run drill build-page              # writes dist/daily-drill.html and dist/data.json
    uv run python -m drill.content.build # the same

The parts, and where each one lives:

- the learning path: one file per module in :mod:`drill.content.modules`
- the classic interview problems: :mod:`drill.problems`, the same bank the CLI drills,
  plus their page-only Learn text in :mod:`drill.content.classics`
- the glossary, habits and gotchas: :mod:`drill.content.extras`
- the trust marks (responsible AI, privacy and NIST notes): :mod:`drill.content.trust`
- the sticker callbacks and Look again questions: :mod:`drill.content.callbacks`
- the Learn step's diagrams: :mod:`drill.content.diagrams`
- the page itself: ``page.html`` next to this file, with ``/*DATA*/`` where the content goes

:func:`build_data` returns the content as one dict, which is what the page embeds and what
the local server and its MCP tools read, so they can never disagree about what a lesson is.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from drill.content import callbacks, classics, diagrams, extras, modules, real, review, trust
from drill.content.checks import more_checks
from drill.content.model import TRAITS, Module

HERE = Path(__file__).resolve().parent
PAGE_TEMPLATE = HERE / "page.html"
PAGE_PARTS = HERE / "page"  # parts of page.html kept in their own files, pulled in by /*INCLUDE page/<file>*/
TOKENS = HERE / "tokens.css"  # the design tokens, inlined into the page at /*TOKENS*/

_INCLUDE = re.compile(r"^/\*INCLUDE (page/[A-Za-z0-9_.-]+)\*/$", re.M)


def page_source() -> str:
    """page.html with its parts filled in: the whole page as one text, before tokens and content.

    Parts of the page live in ``page/`` (one file per section, like ``page/study-list.js``) and
    sit in page.html as a line of their own, ``/*INCLUDE page/study-list.js*/``, at the exact spot
    they belong: CSS order matters. The same comment form works inside <style> and <script>.
    Everything that reads the page (the build, the tests) reads it through here.
    """
    template = PAGE_TEMPLATE.read_text(encoding="utf-8")

    def part(m: re.Match) -> str:
        path = HERE / m.group(1)
        assert path.is_file(), f"page.html includes {m.group(1)}, which doesn't exist"
        text = path.read_text(encoding="utf-8")
        assert not _INCLUDE.search(text), f"{m.group(1)} includes another part; keep parts one level deep"
        return text[:-1] if text.endswith("\n") else text

    return _INCLUDE.sub(part, template)

_EXERCISE_FIELDS = ("title", "topic", "difficulty", "fn", "prompt", "pattern", "target",
                    "realworld", "starter", "solution", "cases", "unordered", "machine", "practice")
_LEARN_FIELDS = ("concepts", "byhand", "why", "gotchas", "guided")
_SCAFFOLD_HEADER = "# Replace every ___ with real code, then run the tests."


def _without_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def _page_lesson(entry: dict, note: dict | None = None) -> dict:
    """The shape page.html reads: tuples as lists, in a fixed order."""
    ex, q, a = entry["example"], entry["check"], entry["angle"]
    out = {
        "title": entry["title"],
        "learn": list(entry["learn"]),
        "example": [ex["caption"], ex["code"]],
        "check": [q["question"], list(q["options"]), q["answer"], q["why"]] + ([q["clue"]] if q.get("clue") else []),
        "angle": [a["pattern"], a["text"], a["say"], a["classic"], a.get("cloze") or []],
    }
    more = more_checks().get(entry["id"])
    if more:  # the Check step's questions 2 and 3, each with a clue (content/checks/)
        out["more"] = [[m["question"], list(m["options"]), m["answer"], m["why"], m["clue"]] for m in more]
    if entry["stack"]:
        out["stack"] = [entry["stack"]["title"], entry["stack"]["code"]]
    if entry.get("walkthrough"):
        out["walk"] = entry["walkthrough"]  # tool views redrawn with numbered callouts (model.screen)
    if entry.get("cards"):
        out["cards"] = entry["cards"]  # Learn as picture cards (model.card), drawn by page/cards.js
    if note:
        out["trust"] = [note["trait"], note["phrase"], note["view"], note["tip"], note["rmf"], note["tevv"]]
    if entry["id"] in diagrams.DIAGRAMS:  # one picture in Learn, drawn by page/diagrams.js
        # picture cards carry their own pictures, one per card, and the page draws only those
        assert not entry.get("cards"), f"{entry['id']}: a lesson with picture cards takes no diagram; draw it as a card"
        out["diagram"] = diagrams.DIAGRAMS[entry["id"]]
    links = callbacks.CALLBACKS.get(entry["id"])
    if links:  # [to, phrase, idea, here] per sticker callback, and the one Look again question if any
        out["callbacks"] = [[c["to"], c["phrase"], c["idea"], c["here"]] for c in links]
        again = next(([c["to"], c["again"]] for c in links if c["again"]), None)
        if again:
            to, q = again
            out["again"] = [to, q["question"], list(q["options"]), q["answer"], q["why"], q["clue"]]
    # [day, sources]: a lesson checked against sources, or the content date with none.
    from drill.content.freshness import CONTENT_DATE
    out["checked"] = [entry.get("checked") or CONTENT_DATE, [list(s) for s in entry.get("sources") or []]]
    return out


def _classic_problem(problem) -> dict:
    return {
        "id": problem.id, "title": problem.title, "topic": problem.topic,
        "difficulty": problem.difficulty, "fn": problem.function_name,
        "prompt": problem.prompt, "pattern": problem.pattern, "target": problem.target_complexity,
        "starter": problem.starter_code, "solution": problem.reference_solution,
        "cases": [{"args": list(tc.args), "expected": tc.expected, "sample": tc.is_sample}
                  for tc in problem.test_cases],
        "unordered": problem.unordered,
    }


def _track_setting(loaded: list[Module], track_modules: list[str]) -> str:
    """The world a track's modules are set in, so a pack joining the track tells the tutor the same."""
    return next((m.setting for m in loaded if m.id in track_modules and m.setting), "")


def build_data(loaded: list[Module] | None = None, packs: list | None = None, assets: str = "url") -> dict:
    """Everything the page, the server and the MCP tools show, as plain data.

    ``packs`` (from :func:`drill.content.packs.load_packs`) add their journeys as modules in the
    phase each pack names. Nothing here reads the environment: only callers that mean to show a
    pack pass one, so the public build never contains one. ``assets`` is ``"url"`` (the server
    serves pack files at ``pack-assets/<pack>/<path>``) or ``"inline"`` (a static page carries them).
    """
    from drill.problems import ALL_PROBLEMS

    loaded = loaded if loaded is not None else modules.load()
    packs = packs or []
    lifecycle = [[n, t, list(ms)] for n, t, ms in modules.LIFECYCLE]
    tracks = [[i, n, t, list(ms)] for i, n, t, ms in modules.TRACKS]
    loaded = list(loaded)
    for pack in packs:
        # A pack's journeys go after the last module of the phase or track it joins.
        joins = next((p[2] for p in lifecycle if p[0] == pack.phase), None)
        if joins is None:
            track = next(tr for tr in tracks if tr[0] == pack.phase)
            joins = track[3]
            for m in pack.modules:
                m.setting = m.setting or _track_setting(loaded, joins)
        after = max((i for i, m in enumerate(loaded) if m.id in joins), default=len(loaded) - 1)
        loaded[after + 1:after + 1] = pack.modules
        joins += [m.id for m in pack.modules]
    bank: dict[str, dict] = {}
    learn: dict[str, dict] = {}

    for problem in ALL_PROBLEMS:
        bank[problem.id] = _classic_problem(problem)
        learn[problem.id] = dict(classics.LEARN[problem.id])

    lessons: dict[str, dict] = {}
    for mod in loaded:
        for entry in mod.lessons:
            if entry.get("pack"):  # a pack lesson: a practice exercise instead of Python
                extra = entry["pack"]
                bank[entry["id"]] = {"id": entry["id"], "title": entry["title"], "topic": mod.title,
                                     "difficulty": extra["difficulty"], "fn": "", "prompt": extra["practice"]["prompt"],
                                     "pattern": entry["angle"]["pattern"], "target": extra["objective"],
                                     "cases": [], "practice": True}
                learn[entry["id"]] = {}
                lessons[entry["id"]] = {**_page_lesson(entry), "pack": _pack_assets(extra, assets)}
                continue
            ex = entry["exercise"]
            bank[entry["id"]] = _without_none({"id": entry["id"], **{k: ex[k] for k in _EXERCISE_FIELDS}})
            learn[entry["id"]] = _without_none({k: ex[k] for k in _LEARN_FIELDS})
            lessons[entry["id"]] = _page_lesson(entry, trust.NOTES.get(entry["id"]))

    for lesson_id, entry in lessons.items():
        classic = entry["angle"][3]
        assert classic is None or classic in bank, f"{lesson_id}: unknown classic {classic!r}"

    data = json.loads(json.dumps({
        "modules": [{"id": m.id, "title": m.title, "blurb": m.blurb, "lessons": m.lesson_ids, "planned": m.planned, "setting": m.setting} for m in loaded],
        "lifecycle": [{"name": n, "text": t, "modules": ms} for n, t, ms in lifecycle],
        "aliases": modules.ALIASES,  # old core lesson ids -> current, so saved progress carries over
        "tracks": [{"id": i, "name": n, "text": t, "modules": ms} for i, n, t, ms in tracks],
        "lessons": lessons,
        "bank": list(bank.values()),
        "learn": learn,
        "traits": TRAITS,
        "glossary": extras.GLOSSARY,
        "rules": extras.RULES,
        "aiGotchas": extras.AI_GOTCHAS,
        "iacGotchas": extras.IAC_GOTCHAS,
        "classics": [p.id for p in ALL_PROBLEMS],
        "review": review.data(),
        "real": real.data(),
        "skill": skill_files(),
    }, ensure_ascii=False))
    from drill import tutor_prepared

    # The tutor's answers to its standard questions, written ahead and checked, so Ask works with no model.
    data["prepared"] = tutor_prepared.served(data, packs=packs)  # a pack's own answers come from inside the pack
    return data


def _pack_assets(extra: dict, mode: str) -> dict:
    """Point a pack lesson's screenshots and diagram at where the page can load them."""
    if mode != "url":
        return extra
    from drill.content.packs import asset_slots

    extra = json.loads(json.dumps(extra))
    for holder, key in asset_slots(extra):
        holder[key] = f"pack-assets/{extra['pack']}/{holder[key]}"
    return extra


SKILL_DIR = Path(__file__).resolve().parents[3] / ".claude" / "skills" / "vet-ai-use-case"


def skill_files() -> dict:
    """The repo's vet-ai-use-case skill, file by file, for the lesson "Turn your vetting into a skill"."""
    if not SKILL_DIR.is_dir():  # installed without the repo around it: the lesson shows no files
        return {"name": "vet-ai-use-case", "path": ".claude/skills/vet-ai-use-case", "files": {}}
    files = {p.relative_to(SKILL_DIR).as_posix(): p.read_text(encoding="utf-8") for p in sorted(SKILL_DIR.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    return {"name": "vet-ai-use-case", "path": ".claude/skills/vet-ai-use-case", "files": files}


def render_page(data: dict) -> str:
    """page.html with the design tokens and the content embedded: still one HTML file."""
    template = page_source()
    assert "/*DATA*/" in template, "page.html has lost its /*DATA*/ marker"
    assert "/*TOKENS*/" in template, "page.html has lost its /*TOKENS*/ marker"
    tokens = TOKENS.read_text(encoding="utf-8")
    return (template
            .replace("/*TOKENS*/", tokens, 1)
            # "<" is escaped so no lesson text can end the <script> block: </script> and <!-- are the two sequences a browser acts on.
            .replace("/*DATA*/", json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")))


def build_page(data: dict | None = None) -> str:
    return render_page(data or build_data())


# -- checks ---------------------------------------------------------------------

_BIG_O = re.compile(r"\bO\((n|1|log|k|V|rows|capacity|total)")


def big_o_leftovers(data: dict) -> list[tuple[str, str]]:
    """Big-O notation in anything the learner reads. Code fields and the glossary are allowed."""
    found: list[tuple[str, str]] = []

    def walk(x: Any, path: str) -> None:
        if isinstance(x, str):
            if _BIG_O.search(x) and not any(s in path for s in ("solution", "starter", "guided")):
                if not path.startswith(".glossary"):
                    found.append((path, x[:90]))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}")

    walk(data, "")
    return found


def _run(code: str, fn: str, cases: list[dict], label: tuple) -> None:
    namespace: dict = {}
    exec(code, namespace)  # noqa: S102 - our own reference solutions
    function = namespace[fn]
    for c in cases:
        got = function(*copy.deepcopy(c["args"]))
        assert got == c["expected"], (*label, c["args"], c["expected"], got)


def check_exercises(loaded: list[Module] | None = None) -> int:
    """Run every lesson's solution, and its scaffold with the blanks filled in, against its cases.

    Returns how many exercises were checked. Raises on the first one that fails.
    """
    loaded = loaded if loaded is not None else modules.load()
    checked = 0
    for mod in loaded:
        for entry in mod.lessons:
            ex = entry["exercise"]
            if ex is None:  # a pack lesson: practice, not Python
                continue
            _run(ex["solution"], ex["fn"], ex["cases"], (mod.id, entry["id"], "solution"))
            if ex["fills"] is not None:
                code = ex["guided"].replace(_SCAFFOLD_HEADER, "#")
                for fill in ex["fills"]:
                    assert "___" in code, (entry["id"], "more fills than blanks")
                    code = code.replace("___", fill, 1)
                assert "___" not in code, (entry["id"], "a blank was left unfilled")
                _run(code, ex["fn"], ex["cases"], (mod.id, entry["id"], "guided"))
            checked += 1
    return checked


# -- writing the files ----------------------------------------------------------

def write(out_dir: Path, data: dict | None = None) -> tuple[Path, Path]:
    """Write ``daily-drill.html`` (to publish) and ``data.json`` (the same content as data)."""
    data = data or build_data()
    out_dir.mkdir(parents=True, exist_ok=True)
    page, as_json = out_dir / "daily-drill.html", out_dir / "data.json"
    page.write_text(render_page(data), encoding="utf-8")
    as_json.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return page, as_json


def main(argv: list[str] | None = None) -> int:
    import argparse

    from drill.config import PROJECT_ROOT

    parser = argparse.ArgumentParser(description="Build the Daily Drill page.")
    parser.add_argument("--out", type=Path, default=None, help="where to write (default: dist/, or dist/private/ with --pack)")
    parser.add_argument("--pack", type=Path, action="append", default=[],
                        help="include a content pack (repeatable). The page then holds the pack: never publish it publicly.")
    args = parser.parse_args(argv)

    from drill.content import packs as content_packs

    loaded = modules.load()
    checked = check_exercises(loaded)
    taken = {lesson["id"] for m in loaded for lesson in m.lessons}
    try:
        packs = content_packs.load_packs(args.pack, taken=taken) if args.pack else []
    except content_packs.PackError as exc:
        print("The content pack has problems:\n" + str(exc), file=sys.stderr)
        return 1
    data = build_data(loaded, packs, assets="inline")
    if packs:
        content_packs.inline_assets(data, packs)
    out = args.out or PROJECT_ROOT / "dist" / ("private" if packs else "")
    leftovers = big_o_leftovers(data)
    for path, text in leftovers:
        print("BIG-O:", path, text, file=sys.stderr)
    page, _ = write(out, data)
    print(f"checked {checked} exercises; {len(data['lessons'])} lessons, {len(data['bank'])} problems -> {page}")
    if packs:
        print(f"Includes {', '.join(p.id for p in packs)}: this page holds private content. Don't publish it to a public place.")
    if leftovers:
        print("Big-O notation found in learner-facing text; see the BIG-O lines above.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
