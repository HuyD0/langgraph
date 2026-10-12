"""The manager's view: the lessons table, one learner's week as numbers, and the weekly note.

All offline: a SQLite store and LangChain's fake chat model standing in for the tutor.
"""

from __future__ import annotations

import asyncio
import json
import time

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from sqlalchemy import insert, select

from drill.server import team
from drill.server.api import create_app
from drill.server.bank import Bank
from drill.server.router import ModelRouter, Route
from drill.server.store import DocStore, events, lessons, summaries

ANA = "ana@example.com"


@pytest.fixture
def store(tmp_path) -> DocStore:
    return DocStore(f"sqlite:///{tmp_path / 'drill.db'}")


@pytest.fixture(scope="module")
def bank() -> Bank:
    return Bank.load()


def router(store, *replies) -> ModelRouter:
    model = GenericFakeChatModel(messages=iter([AIMessage(content=r) for r in replies]))
    return ModelRouter(Route("local", "fake", model), None, store)


def event(store, owner, kind, lesson_id="", at=None, **detail):
    with store.engine.begin() as conn:
        conn.execute(insert(events).values(id=f"{kind}-{lesson_id}-{at}-{len(detail)}", owner=owner, at=at or time.time(),
                                           kind=kind, lesson_id=lesson_id, detail=json.dumps(detail)))


def test_lessons_are_numbered_like_the_page(store, bank):
    rows = team.lesson_rows(bank)
    assert len(rows) == len(bank.lessons) == len({r["id"] for r in rows})
    assert rows[0]["no"] == "1.1" and rows[0]["position"] == 1 and rows[0]["phase"] == "Frame"
    phases = [r["phase"] for r in rows]
    assert phases == sorted(phases, key=phases.index), "a phase's lessons sit together"
    assert all(0 <= r["check_answer"] <= 2 for r in rows)
    assert team.write_lessons(store, bank) == len(rows)
    team.write_lessons(store, bank)  # again on the next start: replaced, not doubled
    with store.engine.begin() as conn:
        assert len(conn.execute(select(lessons)).all()) == len(rows)


def test_a_learners_week_as_numbers(store, bank):
    first, second = bank.order()[:2]
    right = bank.lessons[first]["check"][2]
    now = time.time()
    me = store.for_owner(ANA)
    me.set("data/users/abc/progress", {"lessons": {first: {"done": True}, second: {"step": 1}}, "current": second})
    me.set("study/s1", {"text": "What is leakage?", "status": "open"})
    me.set("study/s2", {"text": "MERGE", "status": "got"})
    event(store, ANA, "checked", first, now - 3600, answer=right)
    event(store, ANA, "checked", second, now - 3000, answer=(bank.lessons[second]["check"][2] + 1) % 3)
    event(store, ANA, "lesson_done", first, now - 2000)
    event(store, ANA, "solved", first, now - 1900, hints=2, count=1)
    event(store, ANA, "asked", second, now - 1000, feature="ask_lesson", question="Does this hold for RAG?")
    event(store, ANA, "asked", second, now - 900, feature="hint")
    event(store, ANA, "asked", first, now - 30 * 86400, feature="ask_lesson", question="an old question")
    event(store, "bo@example.com", "asked", first, now, feature="ask_lesson", question="someone else's")

    facts = team.learner_facts(store, ANA, bank, now)
    assert facts["lessons_done_total"] == 1 and facts["current_lesson"] == bank.lessons[second]["title"]
    assert [c["right"] for c in facts["check_answers"]] == [True, False]
    assert facts["exercises_solved"] == [{"exercise": bank.lessons[first]["title"], "hints": 2}]
    assert facts["questions"] == ["Does this hold for RAG?"], "only this week's, only theirs"
    assert facts["hints_asked"] == 1
    assert facts["study_list_open"] == ["What is leakage?"] and facts["study_list_got"] == 1
    assert len(facts["days_active"]) >= 1


def test_weekly_note_is_written_once_and_refreshed_only_after_news(store, bank):
    now = time.time()
    event(store, ANA, "lesson_done", bank.order()[0], now - 600)
    tutor = router(store, "Finished one lesson. Going well. Stuck on nothing yet. Ask what she found hard.", "second note")
    assert team.due(store, now) == [ANA]
    assert asyncio.run(team.write_due(store, tutor, bank)) == 1
    with store.engine.begin() as conn:
        row = conn.execute(select(summaries)).mappings().one()
    assert row["owner"] == ANA and row["week"] == team.iso_week(now) and row["summary"].startswith("Finished one lesson")
    assert json.loads(row["facts"])["lessons_done_this_week"]
    assert team.due(store, now) == [], "already written this week, no news since"
    later = now + team.REFRESH + 60
    assert team.due(store, later) == [], "a day later but nothing new: no rewrite"
    event(store, ANA, "asked", "", later - 30, feature="ask_lesson", question="new")
    assert team.due(store, later) == [ANA]


def test_no_note_without_activity_or_a_model(store, bank):
    assert asyncio.run(team.write_summary(store, router(store, "unused"), bank, ANA)) is None
    event(store, ANA, "lesson_done", bank.order()[0])
    broken = ModelRouter(None, None, store)
    assert asyncio.run(team.write_due(store, broken, bank)) == 0


def test_summaries_are_for_shared_databases_only(store, monkeypatch):
    monkeypatch.delenv("DRILL_TEAM_SUMMARIES", raising=False)
    assert not team.enabled(store), "one person's SQLite file has no team"
    monkeypatch.setenv("DRILL_TEAM_SUMMARIES", "1")
    assert team.enabled(store)
    assert team.grant_managers(store) is False, "no Postgres roles in SQLite"


def test_asked_events_keep_the_question(store, bank):
    client = TestClient(create_app(store=store, router=router(store, "An answer."), bank=bank, with_mcp=False))
    client.post("/api/ask", json={"prompt": "hello", "trace": {"feature": "ask_lesson", "lesson_id": "split_by_key",
                                                              "question": "Why split by user?" + "x" * 600}})
    asked = [e for e in store.events() if e["kind"] == "asked"]
    assert asked and asked[0]["detail"]["question"].startswith("Why split by user?")
    assert len(asked[0]["detail"]["question"]) == 500


def test_the_managers_dashboard_hangs_together():
    """Every widget reads a dataset that exists, and only columns that dataset's query names."""
    import re

    from drill import manager_view

    board = manager_view.dashboard("cat_x")
    sql = {d["name"]: d["queryLines"][0] for d in board["datasets"]}
    assert all("`cat_x`.drill." in q for q in sql.values())
    assert all(manager_view.LEARNER.split()[0] in q for q in sql.values()), "the app's own rows stay out"
    for page in board["pages"]:
        for item in page["layout"]:
            for query in item["widget"].get("queries", []):
                name = query["query"]["datasetName"]
                assert name in sql, f"{item['widget']['name']} reads a missing dataset {name}"
                for field in query["query"]["fields"]:
                    for column in re.findall(r"`([a-z_0-9]+)`", field["expression"]):
                        if column != "associative_filter_predicate_group":
                            assert re.search(rf"\b{column}\b", sql[name]), f"{name} has no column {column}"
    assert [p["displayName"] for p in board["pages"]] == ["Team", "Where they're stuck", "Questions", "Weekly notes"]
