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
    assert sorted(lifecycle_modules) == sorted(modules.ORDER), "every module belongs to one lifecycle stage"
    assert lifecycle_modules == modules.ORDER, "the path teaches the stages in order, so ORDER follows LIFECYCLE"


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
