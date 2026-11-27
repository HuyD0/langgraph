"""A renamed lesson on the server: saved progress under its old id is read under the new id (Bank.migrate,
the page's own rule), so the MCP tools see it done, the manager's numbers count it once, and the page
moving the record over isn't logged as the lesson done again. Ids the app doesn't have aren't counted."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from drill.server import team
from drill.server.api import create_app
from drill.server.bank import Bank
from drill.server.store import DocStore

ANA = "ana@example.com"


@pytest.fixture(scope="module")
def bank() -> Bank:
    real = Bank.load()
    return Bank(dict(real.data, aliases={"old_first": real.order()[0]}))


def test_progress_under_an_old_id_moves_to_the_new_one(bank):
    first, second = bank.order()[:2]
    saved = {"lessons": {"old_first": {"step": 3, "done": True}, second: {"step": 1}}, "current": "old_first",
             "solved": {"old_first": {"count": 1}}, "gotchas": {"old_first": 0}}
    got = bank.migrate(saved)
    assert got["lessons"] == {first: {"step": 3, "done": True}, second: {"step": 1}}
    assert got["solved"] == {first: {"count": 1}} and got["gotchas"] == {first: 0} and got["current"] == first
    assert "old_first" in saved["lessons"], "the saved copy itself is left alone"
    joined = bank.migrate({"lessons": {"old_first": {"step": 3, "done": True}, first: {"step": 1, "checked": 1}}})
    assert joined["lessons"] == {first: {"step": 3, "done": True, "checked": 1}}
    assert bank.next_lesson(saved) == bank.order()[1], "the MCP's next lesson skips the renamed one already done"


def test_the_managers_numbers_count_each_lesson_once_and_only_known_ones(tmp_path, bank):
    first, second = bank.order()[:2]
    store = DocStore(f"sqlite:///{tmp_path / 'drill.db'}")
    me = store.for_owner(ANA)
    me.set("data/users/abc/progress", {"lessons": {"old_first": {"done": True}, first: {"done": True},
                                                    "from_another_branch": {"done": True}, second: {"step": 1}},
                                       "current": "from_another_branch"})
    facts = team.learner_facts(store, ANA, bank, time.time())
    assert facts["lessons_done_total"] == 1 and facts["current_lesson"] is None
    me.set("data/users/abc/progress", {"lessons": {"old_first": {"done": True}}, "current": "old_first"})
    assert team.learner_facts(store, ANA, bank, time.time())["current_lesson"] is None, "a done lesson isn't current"


def test_the_page_moving_a_record_is_not_logged_as_news(tmp_path, bank):
    first = bank.order()[0]
    store = DocStore(f"sqlite:///{tmp_path / 'drill.db'}")
    client = TestClient(create_app(store=store, bank=bank, with_mcp=False))
    client.put("/api/docs/data/users/local/progress", json={"lessons": {"old_first": {"step": 3, "checked": None, "done": True}}})
    client.put("/api/docs/data/users/local/progress", json={"lessons": {first: {"step": 3, "checked": None, "done": True}}})
    kinds = [(e["kind"], e["lesson_id"]) for e in store.events()]
    assert kinds == [("step", first), ("lesson_done", first)], "logged once, under the lesson's current id"
