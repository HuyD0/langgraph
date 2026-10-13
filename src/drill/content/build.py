"""Assemble the Daily Drill page from its parts.

    uv run drill build-page              # writes dist/daily-drill.html and dist/data.json
    uv run python -m drill.content.build # the same

The parts, and where each one lives:

- the learning path: one file per module in :mod:`drill.content.modules`
- the classic interview problems: :mod:`drill.problems`, the same bank the CLI drills,
  plus their page-only Learn text in :mod:`drill.content.classics`
- the glossary, habits and gotchas: :mod:`drill.content.extras`
- the trust marks (responsible AI, privacy and NIST notes): :mod:`drill.content.trust`
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

from drill.content import classics, extras, modules, real, review, trust
from drill.content.model import TRAITS, Module

HERE = Path(__file__).resolve().parent
PAGE_TEMPLATE = HERE / "page.html"
TOKENS = HERE / "tokens.css"  # the design tokens, inlined into the page at /*TOKENS*/

_EXERCISE_FIELDS = ("title", "topic", "difficulty", "fn", "prompt", "pattern", "target",
                    "realworld", "starter", "solution", "cases", "unordered", "machine", "sort")
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
        "check": [q["question"], list(q["options"]), q["answer"], q["why"]],
        "angle": [a["pattern"], a["text"], a["say"], a["classic"]],
    }
    if entry["stack"]:
        out["stack"] = [entry["stack"]["title"], entry["stack"]["code"]]
    if note:
        out["trust"] = [note["trait"], note["phrase"], note["view"], note["tip"], note["rmf"], note["tevv"]]
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


def build_data(loaded: list[Module] | None = None) -> dict:
    """Everything the page, the server and the MCP tools show, as plain data."""
    from drill.problems import ALL_PROBLEMS

    loaded = loaded if loaded is not None else modules.load()
    bank: dict[str, dict] = {}
    learn: dict[str, dict] = {}

    for problem in ALL_PROBLEMS:
        bank[problem.id] = _classic_problem(problem)
        learn[problem.id] = dict(classics.LEARN[problem.id])

    lessons: dict[str, dict] = {}
    for mod in loaded:
        for entry in mod.lessons:
            ex = entry["exercise"]
            bank[entry["id"]] = _without_none({"id": entry["id"], **{k: ex[k] for k in _EXERCISE_FIELDS}})
            learn[entry["id"]] = _without_none({k: ex[k] for k in _LEARN_FIELDS})
            lessons[entry["id"]] = _page_lesson(entry, trust.NOTES.get(entry["id"]))

    for lesson_id, entry in lessons.items():
        classic = entry["angle"][3]
        assert classic is None or classic in bank, f"{lesson_id}: unknown classic {classic!r}"

    return json.loads(json.dumps({
        "modules": [{"id": m.id, "title": m.title, "blurb": m.blurb, "lessons": m.lesson_ids} for m in loaded],
        "lifecycle": [{"name": n, "text": t, "modules": ms} for n, t, ms in modules.LIFECYCLE],
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


SKILL_DIR = Path(__file__).resolve().parents[3] / ".claude" / "skills" / "vet-ai-use-case"


def skill_files() -> dict:
    """The repo's vet-ai-use-case skill, file by file, for the lesson "Turn your vetting into a skill"."""
    if not SKILL_DIR.is_dir():  # installed without the repo around it: the lesson shows no files
        return {"name": "vet-ai-use-case", "path": ".claude/skills/vet-ai-use-case", "files": {}}
    files = {str(p.relative_to(SKILL_DIR)): p.read_text(encoding="utf-8") for p in sorted(SKILL_DIR.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    return {"name": "vet-ai-use-case", "path": ".claude/skills/vet-ai-use-case", "files": files}


def render_page(data: dict) -> str:
    """page.html with the design tokens and the content embedded: still one HTML file."""
    template = PAGE_TEMPLATE.read_text(encoding="utf-8")
    assert "/*DATA*/" in template, "page.html has lost its /*DATA*/ marker"
    assert "/*TOKENS*/" in template, "page.html has lost its /*TOKENS*/ marker"
    tokens = TOKENS.read_text(encoding="utf-8")
    return (template
            .replace("/*TOKENS*/", tokens, 1)
            .replace("/*DATA*/", json.dumps(data, ensure_ascii=False)))


def build_page(data: dict | None = None) -> str:
    return render_page(data or build_data())


# -- checks ---------------------------------------------------------------------

_BIG_O = re.compile(r"\bO\((n|1|log|k|V|rows|capacity|total)")


def big_o_leftovers(data: dict) -> list[tuple[str, str]]:
    """Big-O notation in anything the learner reads. Code fields and the glossary are allowed."""
    found: list[tuple[str, str]] = []

    def walk(x, path: str) -> None:
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
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "dist", help="where to write (default: dist/)")
    args = parser.parse_args(argv)

    loaded = modules.load()
    checked = check_exercises(loaded)
    data = build_data(loaded)
    leftovers = big_o_leftovers(data)
    for path, text in leftovers:
        print("BIG-O:", path, text, file=sys.stderr)
    page, _ = write(args.out, data)
    print(f"checked {checked} exercises; {len(data['lessons'])} lessons, {len(data['bank'])} problems -> {page}")
    if leftovers:
        print("Big-O notation found in learner-facing text; see the BIG-O lines above.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
