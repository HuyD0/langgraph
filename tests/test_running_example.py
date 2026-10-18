"""The HR assistant runs through the lessons with one set of numbers (src/drill/content/running_example.py).
These tests catch a lesson that drifts from it, and a fact sheet that stops adding up."""

from __future__ import annotations

import pytest

from drill.content import build_data, modules
from drill.content.running_example import HR, quotes


def strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in strings(v)]
    return []


@pytest.fixture(scope="module")
def lesson_text() -> dict[str, str]:
    data = build_data(modules.load())  # a lesson's text is split over its lesson, its exercise and its study notes
    bank = {problem["id"]: problem for problem in data["bank"]}
    return {lid: "\n".join(strings([lesson, bank.get(lid), data["learn"].get(lid)])) for lid, lesson in data["lessons"].items()}


def test_every_lesson_quotes_the_fact_sheet(lesson_text):
    missing = []
    for lid, needles in quotes().items():
        assert lid in lesson_text, f"{lid} is not a lesson any more: update quotes()"
        for needle in needles:
            if needle not in lesson_text[lid]:
                missing.append(f"{lid}: {needle!r}")
    assert not missing, "a lesson no longer says what running_example.py says:\n" + "\n".join(missing)


def test_the_fact_sheet_adds_up():
    h = HR
    assert h["by_hand_minutes"] / 60 * h["hourly_rate"] == h["by_hand_cost"]
    assert round(h["model_per_ticket"] + h["check_per_ticket"] + h["redo_per_ticket"], 3) == h["cost_per_ticket"]
    assert h["cost_per_ticket_about"] == f"{h['cost_per_ticket'] + 0.0001:.2f}"  # 1.865 rounds up in print, not in Python
    assert h["cost_per_ticket"] < h["cost_criterion"]
    assert round(h["by_hand_cost"] - h["cost_per_ticket"] - h["uncaught_per_ticket"], 3) == h["saving_per_ticket"]
    assert h["monthly"]["model"] == h["tickets_per_month"] * h["model_per_ticket"]
    assert h["monthly"]["people"] == round(h["tickets_per_month"] * (h["check_per_ticket"] + h["redo_per_ticket"]))
    assert h["fixed_monthly"] == h["monthly"]["hosting"] + h["monthly"]["evals"]
    net = h["saving_per_ticket"] * h["tickets_per_month"] - h["fixed_monthly"]
    assert round(h["build"] / net, 1) == h["payback_months"]
    assert h["break_even_tickets"] == -(-h["fixed_monthly"] // h["saving_per_ticket"])
    assert 22 * h["tickets_per_day"] < h["tickets_per_month"] <= 23 * h["tickets_per_day"]  # working days in a month
    assert h["golden_set"] < h["eval_examples"]
