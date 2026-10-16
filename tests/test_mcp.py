"""The MCP door keeps the answers back: a lesson card asks the Check questions but never carries
the right option or the model Explain sentence, so an agent helping a learner has to mark a pick
with ``check_answer`` and only gets the sentence from ``mark_done``. Offline, like test_server.py.
"""

from __future__ import annotations

import pytest

from drill.server import mcp as mcp_door
from drill.server.bank import Bank
from drill.server.router import ModelRouter
from drill.server.store import DocStore

LEAKS = ("answer_index", "why", "say_it_like_this")  # the fields the card used to carry


@pytest.fixture
def store(tmp_path) -> DocStore:
    return DocStore(f"sqlite:///{tmp_path / 'drill.db'}")


@pytest.fixture(scope="module")
def bank() -> Bank:
    return Bank.load()


def _keys(value, path: str = "") -> set[str]:
    """Every key in a nested dict, with its path, so a leak anywhere in a card is named."""
    found = set()
    if isinstance(value, dict):
        for k, v in value.items():
            found.add(f"{path}.{k}")
            found |= _keys(v, f"{path}.{k}")
    elif isinstance(value, list):
        for v in value:
            found |= _keys(v, path + "[]")
    return found


def test_no_card_carries_a_check_answer_or_the_explain_sentence(bank):
    for lesson_id in bank.order():
        card = bank.card(lesson_id)
        leaked = sorted(k for k in _keys(card) if k.rsplit(".", 1)[-1] in LEAKS)
        assert not leaked, f"{lesson_id}: {leaked}"
        assert card["check"]["question"] and len(card["check"]["options"]) >= 2
        for extra in card["more_checks"]:
            assert set(extra) == {"question", "options", "clue"} and extra["clue"]  # a clue is help, not the answer
        assert set(card["interview"]) == {"pattern", "angle", "classic"}


def test_check_answer_marks_a_pick_and_says_why(bank):
    lesson_id = bank.order()[0]
    checks = bank.checks(lesson_id)
    assert len(checks) == 1 + len(bank.lessons[lesson_id]["more"])
    for number, (question, options, right, why) in enumerate(checks, start=1):
        good = bank.check_answer(lesson_id, number, right)
        assert good == {"lesson_id": lesson_id, "question": number, "of": len(checks), "asked": question,
                        "picked": options[right], "right": True, "why": why}
        wrong = bank.check_answer(lesson_id, number, (right + 1) % len(options))
        assert wrong["right"] is False and wrong["why"] == why and wrong["picked"] == options[(right + 1) % len(options)]
    with pytest.raises(ValueError, match="Check question"):
        bank.check_answer(lesson_id, len(checks) + 1, 0)
    with pytest.raises(ValueError, match="options"):
        bank.check_answer(lesson_id, 1, 99)
    with pytest.raises(KeyError):
        bank.check_answer("no_such_lesson", 1, 0)


def test_the_tools_ask_mark_and_only_then_hand_over_the_sentence(store, bank):
    mcp_door.configure(store=store, router=ModelRouter(None, None, store), bank=bank)
    first = bank.order()[0]
    card = mcp_door.next_drill()
    assert card["id"] == first and mcp_door.get_drill(first) == card
    assert not any(k.rsplit(".", 1)[-1] in LEAKS for k in _keys(card))

    right = bank.lessons[first]["check"][2]
    assert mcp_door.check_answer(first, 1, right)["right"] is True
    assert mcp_door.check_answer(first, 1, (right + 1) % 3)["right"] is False
    assert mcp_door.check_answer(first)["question"] == 1  # the defaults: the first question, the first option

    done = mcp_door.mark_done(first)
    assert done["done"] and done["next"] == bank.order()[1]
    assert done["explain"] == {"say_it_like_this": bank.lessons[first]["angle"][2]}
    assert mcp_door.next_drill()["id"] == bank.order()[1]
    lessons = mcp_door.list_lessons()
    assert lessons[0]["lessons"][0] == {"id": first, "title": bank.lessons[first]["title"], "done": True}
    with pytest.raises(KeyError):
        mcp_door.check_answer("no_such_lesson", 1, 0)


def test_the_tool_list_names_check_answer():
    """The agent finds the marking tool where it finds the others."""
    import asyncio

    tools = {t.name for t in asyncio.run(mcp_door.server.list_tools())}
    assert {"next_drill", "get_drill", "list_lessons", "check_answer", "mark_done", "hint", "run_tests"} <= tools
