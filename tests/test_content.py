"""The Daily Drill page's content must be solvable, complete, plain, and the same everywhere.

Every lesson's exercise is checked twice: its reference solution, and its fill-in-the-blanks
scaffold with the intended answers filled in, both against the exercise's own cases. The
page is then built in memory, which also fails if Big-O notation appears in anything the
learner reads, or if a lesson points at a classic problem that does not exist.
"""

from __future__ import annotations

import json

import pytest

from drill.content import big_o_leftovers, build_data, build_page, check_exercises
from drill.content import modules
from drill.content.model import Module
from drill.problems import ALL_PROBLEMS


@pytest.fixture(scope="module")
def loaded() -> list[Module]:
    return modules.load()


@pytest.fixture(scope="module")
def data(loaded) -> dict:
    return build_data(loaded)


@pytest.mark.parametrize("module_id", modules.ORDER)
def test_every_exercise_and_scaffold_passes_its_own_cases(module_id):
    assert check_exercises(modules.load([module_id])) > 0


def test_modules_are_in_order_and_lessons_are_unique(loaded):
    assert [m.id for m in loaded] == modules.ORDER
    ids = [lesson_id for m in loaded for lesson_id in m.lesson_ids]
    assert len(ids) == len(set(ids)), "a lesson id appears twice"
    lifecycle_modules = [mid for _, _, ms in modules.LIFECYCLE for mid in ms]
    track_modules = [mid for _, _, _, ms in modules.TRACKS for mid in ms]
    assert lifecycle_modules == modules.PATH, "the path teaches the stages in order, so PATH follows LIFECYCLE"
    assert modules.ORDER == modules.PATH + track_modules, "every module is in one lifecycle stage or one track, path first"
    assert len(set(modules.ORDER)) == len(modules.ORDER), "a module is in only one place"


def test_the_path_has_six_phases_one_sticker_shape_each():
    # The page gives each phase its own sticker shape and rail icon, six of each (phShape, PH_ICON).
    assert len(modules.LIFECYCLE) == 6, "a seventh phase needs a seventh sticker shape and icon in page.html"


def test_every_module_has_an_icon_for_its_stickers():
    # Each sticker shows its module's icon inside its phase's shape.
    import re
    from pathlib import Path
    page = (Path(__file__).resolve().parents[1] / "src/drill/content/page.html").read_text()
    icons = page.split("const MOD_ICON = {", 1)[1].split("};", 1)[0]
    named = set(re.findall(r'"?([a-z-]+)"?\s*:', icons))
    missing = [mid for mid in modules.ORDER if mid not in named]
    assert not missing, f"MOD_ICON has no icon for {missing}"


def test_every_lesson_picture_belongs_to_a_real_lesson():
    # A lesson's own sticker picture is a sprite symbol "s-<lesson id>"; a typo would silently fall back.
    import re
    from pathlib import Path
    page = (Path(__file__).resolve().parents[1] / "src/drill/content/page.html").read_text()
    pictures = re.findall(r'<symbol id="s-([a-z0-9_]+)"', page)
    lessons = {lid for m in modules.load(modules.ORDER) for lid in m.lesson_ids}
    assert pictures, "no lesson pictures found"
    assert len(pictures) == len(set(pictures)), "a lesson has two pictures"
    assert not set(pictures) - lessons, f"pictures for lessons that don't exist: {set(pictures) - lessons}"
    missing = sorted(lessons - set(pictures))
    assert not missing, f"lessons without a sticker picture (add a s-<id> symbol to page.html): {missing}"


def test_every_lesson_has_an_exercise_and_every_classic_is_real(data):
    bank = {p["id"] for p in data["bank"]}
    assert set(data["lessons"]) <= bank
    for lesson_id, lesson in data["lessons"].items():
        assert lesson_id in data["learn"], f"{lesson_id} has no Learn panel"
        classic = lesson["angle"][3]
        assert classic is None or classic in data["classics"], f"{lesson_id} points at {classic!r}"


def test_classic_problems_on_the_page_are_the_cli_bank(data):
    """One text for each classic: the page shows exactly what `drill start` drills."""
    page = {p["id"]: p for p in data["bank"]}
    assert data["classics"] == [p.id for p in ALL_PROBLEMS]
    for problem in ALL_PROBLEMS:
        shown = page[problem.id]
        assert shown["prompt"] == problem.prompt and shown["solution"] == problem.reference_solution
        assert [c["expected"] for c in shown["cases"]] == [tc.expected for tc in problem.test_cases]


def test_no_big_o_in_learner_facing_text(data):
    assert big_o_leftovers(data) == []


def test_page_embeds_the_content(data):
    html = build_page(data)
    assert "/*DATA*/" not in html
    assert json.dumps(data["modules"][0]["title"]) in html


def test_page_embeds_the_design_tokens(data):
    """tokens.css is the one place colors and fonts live; the page must use only names it defines."""
    import re
    from pathlib import Path

    here = Path(__file__).parent.parent / "src" / "drill" / "content"
    tokens, page = (here / "tokens.css").read_text(), (here / "page.html").read_text()
    defined = set(re.findall(r"(--[a-z][a-z0-9-]*)\s*:", tokens))
    used = set(re.findall(r"var\((--[a-z][a-z0-9-]*)", page))
    page_local = set(re.findall(r"(?<!var\()(--[a-z][a-z0-9-]*)", page))  # e.g. --toph, set by the script
    assert used <= defined | page_local, f"used but never defined: {sorted(used - defined - page_local)}"
    html = build_page(data)
    assert "/*TOKENS*/" not in html and "--accent: #2346d1" in html


def test_every_gotcha_has_a_lesson_and_code_to_spot(data):
    """Each card is a "Spot the gotcha" challenge in one lesson, or a Build-step habit."""
    lessons = set(data["lessons"])
    shown_in: dict[str, str] = {}
    habits = []
    for card in data["aiGotchas"] + data["iacGotchas"] + data["rules"]:
        title, why, before, after, where = card
        assert title and why, card
        if where.startswith("build:"):
            habits.append(where)
            continue
        assert where in lessons, f"{title!r} points at {where!r}, which is not a lesson"
        assert where not in shown_in, f"{where} has two gotchas: {shown_in[where]!r} and {title!r}"
        assert before and after and before != after, f"{title!r} needs code before and after"
        shown_in[where] = title
    assert sorted(habits) == ["build:error", "build:fail", "build:pass"]


def test_the_page_only_looks_up_elements_that_exist():
    """A removed element that the script still looks up breaks the page silently (the Notebook did)."""
    import re
    from pathlib import Path

    page = (Path(__file__).parent.parent / "src" / "drill" / "content" / "page.html").read_text()
    static = set(re.findall(r'id="([A-Za-z0-9_-]+)"', page))
    looked_up = set(re.findall(r'\$\("([A-Za-z0-9_-]+)"\)', page))
    assert looked_up <= static, f"looked up but not on the page: {sorted(looked_up - static)}"
    tabs = re.findall(r'data-nb="([a-z]+)"', page)
    assert tabs and all(f'id="nb-{t}"' in page for t in tabs), "every Notebook tab needs its nb-<tab> pane"


def test_every_machine_fits_its_example(data):
    """The machine animates the sample case, so it must sort exactly the input rows into its bins."""
    import json

    key = lambda r: json.dumps(r, sort_keys=True)
    machines = [p for p in data["bank"] if p.get("machine")]
    assert {p["id"] for p in machines} >= {"split_by_key", "validate_rows"}
    for p in machines:
        m, case = p["machine"], next(c for c in p["cases"] if c.get("sample"))
        rows, out = case["args"][0], case["expected"]
        assert isinstance(rows, list) and rows and all(isinstance(r, dict) for r in rows), p["id"]
        assert isinstance(out, list) and len(out) == len(m["bins"]), f"{p['id']}: one returned list per bin"
        assert sorted(key(r) for g in out for r in g) == sorted(key(r) for r in rows), f"{p['id']}: the bins hold exactly the input rows"
        field = m["label_field"] or case["args"][m["label_arg"]]
        assert all(field in r for r in rows), f"{p['id']}: every row has the pill's field {field!r}"
        if m["leak_arg"] is not None:
            assert isinstance(case["args"][m["leak_arg"]], str), f"{p['id']}: leak_arg names a field"



def test_every_build_it_for_real_card_points_at_a_real_notebook_section():
    import json
    from pathlib import Path

    from drill.content import real

    lessons = {lid for m in modules.load(modules.ORDER) for lid in m.lesson_ids}
    root = Path(__file__).resolve().parents[1] / "notebooks"
    for lesson_id, (notebook, section, uses) in real.REAL.items():
        assert lesson_id in lessons, f"no lesson {lesson_id}"
        assert notebook in real.NOTEBOOKS and uses, lesson_id
        cells = json.loads((root / f"{notebook}.ipynb").read_text())["cells"]
        headings = {line[3:].strip() for c in cells if c["cell_type"] == "markdown" for line in "".join(c["source"]).splitlines() if line.startswith("## ")}
        assert section in headings, f"{lesson_id}: {notebook} has no section {section!r}"


def test_the_use_case_sort_agrees_with_the_python_answer(loaded):
    """Lesson 1.1's sorting board and its Python exercise must place every idea the same way."""
    ex = next(e["exercise"] for m in loaded for e in m.lessons if e["id"] == "use_case_score")
    namespace: dict = {}
    exec(ex["solution"], namespace)  # noqa: S102 - our own reference solution
    rows = [{"id": i["name"], "name": i["name"], "value": i["value"], "doable": i["doable"], "gate": i["gate"]}
            for i in ex["sort"]["items"]]
    lists = namespace[ex["fn"]](rows)
    code_bin = {r["id"]: name for name, got in zip(ex["machine"]["bins"], lists) for r in got}
    for item in ex["sort"]["items"]:
        assert code_bin[item["name"]] == ("shelve" if item["bin"] == "gate" else item["bin"]), item["name"]
        assert (item["bin"] == "gate") == bool(item["gate"]), item["name"]
    assert {i["bin"] for i in ex["sort"]["items"]} == {b["id"] for b in ex["sort"]["bins"]}, "every bin gets at least one idea"


def test_motion_effects_keep_their_promises():
    """Every effect the script plays has its look, and the looks stay cheap: they never loop or blur,
    each root ends with fx-end (when the script removes it), and the engine checks motion first."""
    import re
    from pathlib import Path

    page = (Path(__file__).parent.parent / "src" / "drill" / "content" / "page.html").read_text()
    fx = page.split("/* fx: start */")[1].split("/* fx: end */")[0]
    assert "infinite" not in fx and "blur(" not in fx, "effects must end on their own and stay cheap to draw"
    played = set(re.findall(r'fxScreen\("([a-z]+)"', page)) | set(re.findall(r'fxOn\(.*?, "([a-z]+)", FX\.', page))
    assert played >= {"space", "merge", "spark", "turn", "curtain", "heal", "smoke", "seal", "unveil", "room"}
    for name in played:
        assert f".fx-{name} " in fx, f"fx {name!r} is played but has no .fx-{name} rules"
        assert re.search(rf"\b{name}: ", page.split("const FX = {")[1].split("};")[0]), f"FX.{name} has no markup"
    defined = set(re.findall(r"@keyframes ([a-z-]+)", page))
    used = {n for decl in re.findall(r"animation:([^;}]+)", fx) for n in re.findall(r"\b(fx-[a-z-]+)", decl)}
    assert used <= defined, f"animations with no keyframes: {sorted(used - defined)}"
    engine = page.split("// ---------- motion: short effects")[1].split("const FX = {")[0]
    for fn in ("fxScreen", "fxOn", "fxMove"):
        body = engine.split(f"function {fn}(")[1].split("\n}")[0]
        assert "motionOn()" in body and "try {" in body, f"{fn} must check motion and never throw"
    assert 'e.animationName !== "fx-end"' in engine and "FX_LIMIT" in engine


def test_every_look_has_the_motion_tokens():
    """Effects read their colours from tokens, so each theme must define them (light, dark twice, dusk)."""
    from pathlib import Path

    tokens = (Path(__file__).parent.parent / "src" / "drill" / "content" / "tokens.css").read_text()
    for name in ("--fx-core", "--fx-glow", "--fx-veil", "--fx-red", "--fx-mix"):
        assert tokens.count(name + ":") == 4, name
    for name in ("--path", "--path-bg", "--path-line", "--path-ink"):
        assert tokens.count(name + ":") == 4, name
    for name in ("--dur-tap", "--dur-step", "--dur-moment", "--dur-big", "--dur-slide", "--ease-out", "--ease-in", "--ease-pop"):
        assert tokens.count(name + ":") == 1, name


def test_phase_tabs_are_one_piece_with_their_room():
    """Home's phases are a real tab list joined to the room below, and only the room's title shape glows."""
    from pathlib import Path

    page = (Path(__file__).parent.parent / "src" / "drill" / "content" / "page.html").read_text()
    rail = page.split("function railHtml(")[1].split("\n}")[0]
    assert 'role="tablist"' in rail and 'role="tab"' in rail and "aria-selected" in rail and 'aria-controls="phasePanel"' in rail
    assert 'badgeSvg(i, 11, st === "done" ? "done" : "")' in rail, "the tabs never get the glowing 'now' badge"
    assert 'id="phasePanel" role="tabpanel"' in page and "aria-labelledby=\"phtab${nidx}\"" in page
    assert '.rail.phtabs [role=tab]' in page and '"ArrowLeft"' not in rail, "arrow keys are handled once, outside railHtml"
    assert "ArrowRight" in page.split("the phase tabs: arrows")[1].split("});")[0]
    for rule in (".phasebox {", ".phasebox.here {", ".rail.phtabs {", ".rail.phtabs .sleeve {", ".book.room {"):
        assert rule in page, rule
    assert 'class="phasebox' in page and "data-showing=" in page, "the box must not carry data-phase, or any tap inside it would switch phase"


def test_a_sorting_lesson_explains_itself_to_someone_who_sorted(loaded):
    """Explain must not tell a learner who sorted cards about the Python lists they never wrote."""
    for mod in loaded:
        for entry in mod.lessons:
            sort = entry["exercise"]["sort"]
            if not sort:
                continue
            assert sort["explain"], f"{entry['id']}: a sort_task needs explain text"
            assert "Python" not in sort["explain"] and "elif" not in sort["explain"], entry["id"]
            assert sort["explain"] in entry["angle"]["text"], f"{entry['id']}: explain should be the lesson's own words"
            labels = {b["id"]: f'{b["label"]} {b["who"]}'.lower() for b in sort["bins"]}
            if "gate" in labels and "shelve" in labels:  # the lesson says a failed gate is shelved; the board must agree
                assert "gate" in labels["shelve"] and "shelved" in labels["gate"], entry["id"]


def test_every_look_is_readable():
    """Text, results, the primary button and code colours meet contrast minimums in light, dark and dusk."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parent.parent / "scripts" / "contrast.py"
    spec = importlib.util.spec_from_file_location("contrast", path)
    contrast = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contrast)
    rows = contrast.check()
    assert len(rows) == 3 * len(contrast.PAIRS), "every pair checked in every look"
    bad = [f"{look}: {fg} on {bg} is {r:.2f}:1, needs {m}" for look, fg, bg, r, m, _ in rows if r < m]
    assert not bad, bad


def test_placeholders_are_coming_soon_not_lessons(loaded, data):
    """A planned lesson has a title and a line, never an exercise, and never shares an id with a real lesson."""
    lesson_ids = {lid for m in loaded for lid in m.lesson_ids}
    for m in loaded:
        for p in m.planned:
            assert set(p) == {"id", "title", "blurb"} and p["title"] and p["blurb"], (m.id, p)
            assert p["id"] not in lesson_ids, f"{p['id']} is both a lesson and a placeholder"
    shown = {p["id"] for m in data["modules"] for p in m["planned"]}
    assert shown and not (shown & set(data["lessons"])), "placeholders reach the page, and never as lessons"


def test_the_platform_track_has_a_real_lesson_in_every_module(loaded):
    """Each track module opens with a lesson you can do, so a placeholder is never all there is."""
    by_id = {m.id: m for m in loaded}
    for _, _, _, mids in modules.TRACKS:
        for mid in mids:
            assert by_id[mid].lessons, f"{mid} has only placeholders"


def test_a_sentence_with_gaps_is_stored_plain_and_in_pieces():
    from drill.content.model import cloze

    plain, pieces = cloze("I find everything [[downstream|upstream|beside it::Which way?]] of it, then wait for [[inputs|outputs|logs::What it needs.]].")
    assert plain == "I find everything downstream of it, then wait for inputs."
    assert pieces[1] == {"answer": "downstream", "wrong": ["upstream", "beside it"], "clue": "Which way?"}
    assert cloze("No gaps here.") == ("No gaps here.", [])
    with pytest.raises(AssertionError):  # help is a clue first, so every gap needs one
        cloze("One [[gap|a|b]] and [[two|c|d::ok]].")


def test_every_explain_gap_is_answerable_and_the_plain_sentence_reads_right():
    from drill.content.build import build_data

    with_gaps = 0
    for lid, lesson in build_data()["lessons"].items():
        pattern, text, say, classic, pieces = lesson["angle"]
        if not pieces:
            continue
        with_gaps += 1
        assert "[[" not in say and "]]" not in say, lid
        assert "".join(p if isinstance(p, str) else p["answer"] for p in pieces) == say, lid
        for g in (p for p in pieces if not isinstance(p, str)):
            assert len({g["answer"], *g["wrong"]}) == 3, (lid, g)
            assert g["answer"].lower() not in g["clue"].lower(), f"{lid}: the clue gives away {g['answer']!r}"
    assert with_gaps == len(build_data()["lessons"]), "every lesson's Explain sentence has gaps"


def test_every_platform_module_tells_the_tutor_its_setting():
    """Without a setting, "give me a harder one" drifts to generic web-app examples."""
    from drill.content.build import PAGE_TEMPLATE

    data = build_data()
    track = next(t for t in data["tracks"] if t["id"] == "platform")
    by_id = {m["id"]: m for m in data["modules"]}
    for mid in track["modules"]:
        assert "Azure Databricks" in by_id[mid]["setting"], mid
    assert "modOf[cur.id].setting" in PAGE_TEMPLATE.read_text(), "the tutor's lesson context must include the setting"


def test_the_frontend_guide_and_screen_gallery_match_the_code():
    """docs/FRONTEND.md's map names page.html's section markers, and docs/screens/README.md shows
    every shot scripts/screenshots.mjs takes: renaming one without the other fails here."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    page = (root / "src/drill/content/page.html").read_text()
    guide = (root / "docs/FRONTEND.md").read_text()
    table = guide.split("## Map of the script", 1)[1].split("\n## ", 1)[0]
    markers = [m for cell in re.findall(r"^\| `([^`]+)`(?: / `([^`]+)`)? \|", table, re.M) for m in cell if m]
    assert len(markers) >= 20
    for marker in markers:
        assert f"// ---------- {marker}" in page, f"docs/FRONTEND.md names a section page.html doesn't have: {marker}"

    shots = re.findall(r'^\s*\["([a-z0-9-]+)",', (root / "scripts/screenshots.mjs").read_text(), re.M)
    gallery = (root / "docs/screens/README.md").read_text()
    assert len(shots) >= 10
    for name in shots:
        assert f"({name}.webp)" in gallery, f"docs/screens/README.md doesn't show {name}"
        assert (root / "docs/screens" / f"{name}.webp").exists(), f"run scripts/screenshots.mjs: {name}.webp is missing"


def test_fast_changing_lessons_say_when_they_were_checked():
    # Databricks products are renamed and moved often, so these lessons carry the day their
    # facts were checked and the pages they were checked against; the page shows both.
    import datetime
    from pathlib import Path

    from drill.content.freshness import STALE_DAYS, freshness
    dated = {"workspace", "access", "databricks-ai"}
    for mod in modules.load():
        for lesson in mod.lessons:
            if mod.id in dated:
                assert lesson["checked"] and lesson["sources"], f"{lesson['id']} needs checked= and sources="
    page = (Path(__file__).resolve().parents[1] / "src/drill/content/page.html").read_text()
    assert f"const STALE_DAYS = {STALE_DAYS};" in page, "the page and drill content stale agree on when to warn"
    later = freshness(modules.load(), datetime.date(2030, 1, 1))
    total = sum(len(m.lesson_ids) for m in modules.load())
    assert not later["fresh"] and len(later["due"]) == total, "every lesson comes due as time passes"
    data = build_data(modules.load())
    assert data["lessons"]["masked_columns"]["checked"][1][0][1].startswith("https://")
    assert all(lesson["checked"][0] for lesson in data["lessons"].values()), "every lesson has a date on the page"


def test_the_page_script_parses(data, tmp_path):
    # A clash of names or a stray bracket stops the whole page, and no other test runs its script.
    import re
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    html = build_page(data)
    script = max(re.findall(r"<script>(.*?)</script>", html, re.S), key=len)
    (tmp_path / "page.js").write_text(script)
    result = subprocess.run([node, "--check", str(tmp_path / "page.js")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-800:]


def test_every_walkthrough_screen_can_be_drawn_and_explained():
    """A lesson's walkthrough screens (model.screen) each need a renderer in page.html, and every
    numbered callout needs its step: screen() checks the numbers, this checks the page."""
    import re
    from drill.content.build import PAGE_TEMPLATE
    from drill.content.model import SCREEN_KINDS

    page = PAGE_TEMPLATE.read_text()
    views = re.search(r"const SL_VIEW = \{(.*?)\n\};", page, re.S).group(1)
    for kind in SCREEN_KINDS:
        assert re.search(rf"^\s*{kind}: d =>", views, re.M), f"page.html can't draw a {kind!r} screen"
    walks = [(lid, w) for lid, lesson in build_data()["lessons"].items() for w in lesson.get("walk", [])]
    assert walks, "the Spacelift run lesson has a walkthrough"
    for lid, w in walks:
        assert w["steps"] and w["caption"], lid
