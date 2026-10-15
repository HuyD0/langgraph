"""Material for a chat tutor (a Claude Project) that teaches from the same curriculum.

Two outputs:

- **The curriculum map** (``docs/tutor/CURRICULUM_MAP.md``): every module and lesson (its
  Learn text, check question and answer, exercise, interview pattern and "what to say",
  gotcha card), the practice sets, notebooks and glossary. It is generated from the content
  itself, so it can never drift: ``uv run drill tutor map`` (a test fails when it is stale).
- **A snapshot** of where the learner is: lessons done and in progress, check questions and
  gotchas missed, exercises that needed hints, study items due. It is personal, so it is
  written outside the repository by default (``~/Documents/daily-drill/tutor-snapshot.md``)
  where Finder shows it and git can't pick it up.

    uv run drill tutor map
    uv run drill tutor snapshot                     # this Mac's progress only
    uv run drill tutor snapshot --copy              # and put the text on the clipboard
    uv run drill tutor snapshot --progress .drill/export/data/users/me/progress.json --study .drill/export/study
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from drill.config import PROJECT_ROOT

MAP_PATH = PROJECT_ROOT / "docs" / "tutor" / "CURRICULUM_MAP.md"
SNAPSHOT_PATH = Path.home() / "Documents" / "daily-drill" / "tutor-snapshot.md"
EXPORT_DIR = PROJECT_ROOT / ".drill" / "export"  # where exports from the claude.ai page go (git ignores .drill/)
LOCAL_PROGRESS = "data/users/local/progress"
STEPS = ["Learn", "Check", "Build", "Explain"]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _plain(text: str) -> str:
    """Markdown emphasis off, whitespace squeezed, for one-line list items.

    Pipes stay as they are: lessons quote shell commands like `cat a.txt | sh`.
    """
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", str(text))
    return " ".join(text.split())


def _short(text: str, limit: int) -> str:
    """Cut at a word boundary, with an ellipsis, never mid-word."""
    text = _plain(text)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def gotcha_cards(data: dict) -> dict[str, dict]:
    """Each lesson's "Spot the gotcha" card, with the index of the right answer.

    Mirrors page.html: the cards are numbered within each list (AI, IaC, habits), habits
    included, and the right option sits at position ``index % 3``. Habits have no card.
    """
    cards: dict[str, dict] = {}
    for cards_list in (data["aiGotchas"], data["iacGotchas"], data["rules"]):
        for index, (title, why, before, after, where) in enumerate(cards_list):
            if where.startswith("build:"):
                continue
            cards[where] = {"title": title, "why": why, "before": before, "after": after, "answer": index % 3}
    return cards


def _notebooks() -> list[tuple[str, str]]:
    out = []
    # By milestone number, so m10 comes after m9d rather than after m1.
    def milestone(path: Path) -> tuple[int, str]:
        number = re.match(r"m(\d+)", path.stem)
        return (int(number.group(1)) if number else 0, path.stem)

    for path in sorted((PROJECT_ROOT / "notebooks").glob("m*.ipynb"), key=milestone):
        cells = json.loads(path.read_text()).get("cells", [])
        heading = next((c for c in cells if c.get("cell_type") == "markdown"), None)
        title = "".join(heading["source"]).split("\n")[0].lstrip("# ").strip() if heading else path.stem
        out.append((path.name, title))
    return out


# ---------------------------------------------------------------------------
# The curriculum map
# ---------------------------------------------------------------------------


def curriculum_map(data: dict | None = None) -> str:
    """The whole curriculum as one Markdown file, for a tutor's knowledge."""
    if data is None:
        from drill.content import build_data

        data = build_data()
    bank = {p["id"]: p for p in data["bank"]}
    cards = gotcha_cards(data)
    stage_of = {mid: st["name"] for st in data["lifecycle"] for mid in st["modules"]}
    stage_of.update({mid: tr["name"] for tr in data.get("tracks", []) for mid in tr["modules"]})
    total = sum(len(m["lessons"]) for m in data["modules"])

    lines = [
        "# Daily Drill curriculum map",
        "",
        "Generated from `src/drill/content` by `uv run drill tutor map`; do not edit by hand. "
        "These are the lessons that exist; anything not listed here has not been built yet.",
        "",
        f"The learning path has {total} lessons in {len(data['modules'])} modules, in the order below. "
        "Each lesson has four steps: Learn (a short reading), Check (one multiple-choice question), "
        "Build (a small Python exercise that runs in the browser, with a starting scaffold that has "
        f"blanks to fill) and Explain (the pattern used and what to say). {len(cards)} of the "
        f"{total} lessons also have a \"Spot the gotcha\" card in the Explain step: risky code, pick "
        "the rule it breaks, then see the fix. The learner saves things to a study list that brings "
        "them back for review after 3, 10, 30 and 90 days.",
        "",
        "Each module is tagged with the stage of an AI project it belongs to. The tags are labels, "
        "not the order:",
        "",
        *[f"- **{st['name']}**: {st['text']}" for st in data["lifecycle"]],
        *[f"- **{tr['name']}** (a separate track beside the path, numbered P1.1 and so on): {tr['text']}"
          for tr in data.get("tracks", [])],
        "",
    ]
    number = 0
    for module in data["modules"]:
        stage = stage_of.get(module["id"], "")
        lines += [f"## {module['title']}" + (f" (stage: {stage})" if stage else ""), "", module["blurb"], ""]
        if module.get("planned"):
            lines += ["Coming soon, not built yet (say so if asked; don't teach them as if they exist): "
                      + "; ".join(_plain(p["title"]) for p in module["planned"]) + ".", ""]
        for lesson_id in module["lessons"]:
            number += 1
            lesson = data["lessons"][lesson_id]
            problem = bank[lesson_id]
            question, options, right, why = lesson["check"][:4]
            pattern, pattern_text, say, _classic = lesson["angle"][:4]
            lines += [
                f"### {number}. {_plain(lesson['title'])} (`{lesson_id}`)",
                "",
                *[f"{_plain(p)}" for p in lesson["learn"]],
                "",
                f"- **Check:** {_plain(question)} Right answer: {_plain(options[right])}. Why: {_plain(why)}",
                *[f"- **Check, question {k}:** {_plain(q)} Right answer: {_plain(opts[r])}. Why: {_plain(w)}"
                  for k, (q, opts, r, w, _clue) in enumerate(lesson.get("more") or [], 2)],
                f"- **Exercise:** {_plain(problem['title'])}, writing `{problem['fn']}`. Approach: {_plain(problem['pattern'])}",
                f"- **Explain:** the pattern is {_plain(pattern)}. Why this pattern: {_plain(pattern_text)} "
                f"What to say: {_plain(say)}",
            ]
            if lesson_id in cards:
                card = cards[lesson_id]
                lines += [
                    f"- **Spot the gotcha:** \"{_plain(card['title'])}\". {_plain(card['why'])} "
                    "The learner sees this risky code and picks the rule it breaks:",
                    "",
                    "  ```",
                    *[f"  {line}" for line in card["before"].splitlines()],
                    "  ```",
                    "",
                    "  The fix:",
                    "",
                    "  ```",
                    *[f"  {line}" for line in card["after"].splitlines()],
                    "  ```",
                ]
            lines.append("")

    lines += ["## Practice sets", "", "Optional practice outside the path.", ""]
    for name, ids in (("Classic interview problems", data["classics"]),):
        lines.append(f"- **{name}**: " + "; ".join(f"{_plain(bank[i]['title'])} (`{bank[i]['fn']}`)" for i in ids))
    lines += [
        "",
        "## Notebooks",
        "",
        "Longer, hands-on milestones in `notebooks/`, each with an answer key in `notebooks/solutions/`. "
        "Notebooks 1 to 6 build this repository's terminal coding tutor, step by step.",
        "",
    ]
    lines += [f"- `{name}`: {title}" for name, title in _notebooks()]
    lines += ["", "## Glossary", "", "The definitions the page uses; use the same ones.", ""]
    for group, terms in data["glossary"]:
        lines += [f"### {group}", ""]
        lines += [f"- **{term}**: {_plain(meaning)}" for term, meaning in terms]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_map(path: Path = MAP_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(curriculum_map())
    return path


# ---------------------------------------------------------------------------
# The snapshot
# ---------------------------------------------------------------------------


def merge_progress(a: dict, b: dict) -> dict:
    """Two copies of the page's progress, combined the way the page combines them (``b`` wins)."""
    lessons = dict(a.get("lessons") or {})
    for lesson_id, theirs in (b.get("lessons") or {}).items():
        theirs = theirs or {}
        mine = lessons.get(lesson_id)
        if not mine:
            lessons[lesson_id] = theirs
            continue
        lessons[lesson_id] = {
            "step": max(mine.get("step") or 0, theirs.get("step") or 0),
            "checked": theirs.get("checked") if theirs.get("checked") is not None else mine.get("checked"),
            "done": bool(mine.get("done") or theirs.get("done")),
        }
        said = theirs.get("said") or mine.get("said")  # the Explain step's sentence, when there is one
        if said:
            lessons[lesson_id]["said"] = said
        first = mine.get("first") or theirs.get("first")  # the shared result: the first time through stays
        if first:
            lessons[lesson_id]["first"] = first
    return {
        "solved": {**(a.get("solved") or {}), **(b.get("solved") or {})},
        "days": sorted(set(a.get("days") or []) | set(b.get("days") or [])),
        "lessons": lessons,
        "gotchas": {**(a.get("gotchas") or {}), **(b.get("gotchas") or {})},
        "current": b.get("current") or a.get("current"),
        # the learner's own use case, bars and numbers: the newer copy wins, b on a tie
        "mine": b.get("mine") if ((b.get("mine") or {}).get("updatedAt") or 0) >= ((a.get("mine") or {}).get("updatedAt") or 0) else a.get("mine"),
    }


def snapshot(progress: dict, study_items: list[dict], data: dict | None = None, today: str | None = None) -> str:
    """Where the learner is, as one page a tutor can read. Every date is worked out from ``today``."""
    from drill.server.study import is_due

    if data is None:
        from drill.content import build_data

        data = build_data()
    day = dt.date.fromisoformat(today) if today else dt.date.today()
    now_ms = dt.datetime.combine(day, dt.time(23, 59)).timestamp() * 1000
    lessons = progress.get("lessons") or {}
    solved = progress.get("solved") or {}
    picked = progress.get("gotchas") or {}
    cards = gotcha_cards(data)
    order = [lid for m in data["modules"] for lid in m["lessons"]]
    title = {lid: _plain(data["lessons"][lid]["title"]) for lid in order}
    module_of = {lid: m["title"] for m in data["modules"] for lid in m["lessons"]}
    entry = {lid: (lessons.get(lid) or {}) for lid in order}

    done = [lid for lid in order if entry[lid].get("done")]

    def started(lid: str) -> bool:  # page.html's started(): an empty entry is not a start
        e = entry[lid]
        return (e.get("step") or 0) > 0 or e.get("checked") is not None or bool(e.get("done"))

    def state_of(lid: str) -> str:
        if not started(lid):
            return "not started"
        return f"in progress, at the {STEPS[min(entry[lid].get('step') or 0, 3)]} step"

    in_progress = [lid for lid in order if started(lid) and lid not in done]
    current = progress.get("current")  # the page resumes this lesson if it is unfinished
    next_up = current if current in title and lessons.get(current) and not entry[current].get("done") else None
    next_up = next_up or next((lid for lid in order if lid not in done), None)
    days = progress.get("days") or []
    since = lambda n: [d for d in days if (day - dt.timedelta(days=n)).isoformat() < d <= day.isoformat()]  # noqa: E731

    wrong_checks = [
        lid for lid in order
        if entry[lid].get("checked") is not None and entry[lid]["checked"] != data["lessons"][lid]["check"][2]
    ]
    missed = [lid for lid in order if lid in picked and lid in cards and picked[lid] != cards[lid]["answer"]]
    spotted = [lid for lid in order if lid in picked and lid in cards and picked[lid] == cards[lid]["answer"]]
    hinted = [lid for lid in order if ((solved.get(lid) or {}).get("hints") or 0) >= 2]
    due = [it for it in study_items if is_due(it, now_ms)]
    learning = [it for it in study_items if it.get("status") != "got"]
    text_of = lambda it: str(it.get("text") or "")  # noqa: E731

    lines = [
        f"# Daily Drill snapshot, {day.isoformat()}",
        "",
        "Personal: where the learner is on the Daily Drill path. Do not commit or share.",
        "",
        "## Progress",
        "",
        f"- Lessons finished: {len(done)} of {len(order)}.",
    ]
    if next_up:
        lines.append(f"- Next lesson: {title[next_up]} ({module_of[next_up]}), {state_of(next_up)}.")
    else:
        lines.append("- The path is finished.")
    lines += [
        f"- Days practised: {len(since(7))} in the last 7 days, {len(since(30))} in the last 30.",
        f"- Spot the gotcha: {len(spotted)} spotted, {len(missed)} missed, of {len(cards)} cards.",
        "",
        "| Module | Finished |",
        "|---|---|",
    ]
    for module in data["modules"]:
        n = len([lid for lid in module["lessons"] if lid in done])
        lines.append(f"| {module['title']} | {n} of {len(module['lessons'])} |")

    def section(heading: str, rows: list[str], empty: str) -> None:
        lines.extend(["", f"## {heading}", ""])
        lines.extend(rows or [f"- {empty}"])

    def wrong_row(lid: str) -> str:
        question, options, right, why = data["lessons"][lid]["check"][:4]
        picked_option = options[entry[lid]["checked"]] if 0 <= entry[lid]["checked"] < len(options) else "?"
        return (
            f"- {title[lid]}: \"{_plain(question)}\" They chose \"{_plain(picked_option)}\". "
            f"The right answer is \"{_plain(options[right])}\": {_plain(why)}"
        )

    section("Started, not finished", [f"- {title[lid]} ({module_of[lid]}), {state_of(lid)}" for lid in in_progress], "None.")
    section("Finished", ["- " + "; ".join(title[lid] for lid in done)] if done else [], "None yet.")
    section("Check questions answered wrong", [wrong_row(lid) for lid in wrong_checks], "None.")
    section("Spot the gotcha cards missed", [f"- {cards[lid]['title']}, in {title[lid]}" for lid in missed], "None.")
    section("Exercises that needed two or more hints", [f"- {title[lid]} ({solved[lid]['hints']} hints)" for lid in hinted], "None.")
    section("Study list: due for review now", [f"- {_short(text_of(it), 160)}" for it in due], "Nothing due.")
    section(
        "Study list: still learning",
        [f"- {_short(text_of(it), 160)}" + (f" (their note: {_short(it['note'], 120)})" if it.get("note") else "") for it in learning],
        "Nothing on the list.",
    )
    own = progress.get("mine") or {}
    card = own.get("card") or {}
    own_rows = []
    idea = own.get("idea") or {}
    if any(str(idea.get(k) or "").strip() for k in ("problem", "who", "what", "measure")):
        gates = [label for key, label in (("rule", "a rule could do it"), ("nodata", "no examples to test on"), ("harm", "unchecked harm")) if idea.get(key)]
        own_rows.append(
            f"- Their idea: problem \"{_short(idea.get('problem') or 'not written', 120)}\"; use case \"Help {idea.get('who') or '?'} {idea.get('what') or '?'} so {idea.get('measure') or '?'}\""
            + (f"; failed gates: {', '.join(gates)}" if gates else "")
            + (f"; {idea['mode']}" if idea.get("mode") else "")
            + (f"; rated {idea.get('value') or '?'} value, {idea.get('doable') or '?'} doable" if idea.get("value") or idea.get("doable") else "") + "."
        )
    if any((v or "").strip() for v in card.values()):
        own_rows.append("- Their use case card: " + "; ".join(f"{k.replace('_', ' ')}: {_short(v.strip(), 120)}" for k, v in card.items() if (v or "").strip()) + ".")
    reqs = [r.strip() for r in (own.get("reqs") or "").splitlines() if r.strip()]
    if reqs:
        own_rows.append("- Their requirements: " + "; ".join(_short(r, 100) for r in reqs[:12]) + ".")
    bars = own.get("bars") or {}
    if any(str(bars.get(k) or "").strip() for k in ("quality", "seconds", "cost")):
        own_rows.append(f"- Their fit-for-purpose bars: {bars.get('quality') or '?'} in 100 right, under {bars.get('seconds') or '?'} seconds, under ${bars.get('cost') or '?'} a task"
                        + (f", must never: {_short(bars['mustpass'], 100)}" if (bars.get("mustpass") or "").strip() else "") + ".")
    summary = (own.get("costs") or {}).get("summary") or {}
    if summary.get("total"):
        top = "; ".join(f"{name} ${value:,}" for name, value in (summary.get("items") or [])[:5])
        own_rows.append(f"- Their total cost of ownership: ${summary['total']:,} over {summary.get('years', '?')} years, ${summary.get('perMonth', 0):,} a month to run. Biggest items: {top}.")
    outcome = own.get("outcome") or {}
    if outcome.get("call"):
        own_rows.append(f"- Their pilot's call, by their own bars: {outcome['call']}.")
    feedback = own.get("feedback") or []
    if feedback:
        useful = [f for f in feedback if f.get("name") == "useful"]
        reasons = [f["name"].replace("_", " ") for f in feedback if f.get("value") is True and f.get("name") not in ("useful", "pilot_outcome")]
        own_rows.append(f"- Their ratings of AI drafts: {sum(1 for f in useful if f.get('value'))} useful, {sum(1 for f in useful if not f.get('value'))} not"
                        + (f"; reasons given: {', '.join(sorted(set(reasons)))}" if reasons else "") + ".")
    section("Their own use case (from the Use case and fit lessons)", own_rows, "Not written yet.")
    focus = (
        [f"review \"{_short(text_of(it), 60)}\"" for it in due[:3]]
        + [f"the gotcha \"{cards[lid]['title']}\"" for lid in missed[:2]]
        + [f"the idea behind {title[lid]}" for lid in list(dict.fromkeys(wrong_checks + hinted))[:2]]
    )
    if not focus:  # nothing due or missed yet: talk through open questions, then the next lesson
        focus = [f"talk through \"{_short(text_of(it), 60)}\"" for it in learning[:2]]
        if next_up:
            focus.append(f"prepare for the next lesson, {title[next_up]}")
    lines.extend(["", "## Suggested focus for the next session", ""])
    fallback = "- Carry on with the next lesson." if next_up else "- Revisit earlier lessons, try the practice sets, or do a mock interview."
    lines.append("- " + "; ".join(focus) + "." if focus else fallback)
    return "\n".join(lines) + "\n"


def write_snapshot(
    path: Path = SNAPSHOT_PATH,
    progress_file: Path | None = None,
    study_source: Path | None = None,
) -> Path:
    """This Mac's progress and study list, merged with exported copies from claude.ai if given."""
    from drill.server import study
    from drill.server.store import DocStore

    store = DocStore()
    progress = store.get(LOCAL_PROGRESS) or {}
    if progress_file:
        exported = json.loads(progress_file.read_text())
        progress = merge_progress(progress, exported.get("data", exported))
    items = study.load(store)
    if study_source:
        writes, _ = study.merge(items, study.read_items(study_source))
        by_id = {it["id"]: it for it in items}
        by_id.update({it["id"]: it for it in writes})
        items = list(by_id.values())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot(progress, items))
    return path
