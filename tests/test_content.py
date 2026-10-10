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
