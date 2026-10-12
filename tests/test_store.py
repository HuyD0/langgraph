"""The progress store: owners, the activity log, the Lakebase login, and moving work between stores.

All offline. Lakebase is stood in for by a second SQLite file, and its login by a fake
Databricks client, so these run with no workspace and no credentials.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from drill.server import activity, store as store_mod
from drill.server.api import create_app
from drill.server.bank import Bank
from drill.server.router import ModelRouter, Route
from drill.server.store import DocStore, LakebaseLogin, open_store


def sqlite_url(tmp_path, name="drill.db") -> str:
    return f"sqlite:///{tmp_path / name}"


class FakeDatabricks:
    """Just enough of a WorkspaceClient: who you are, and a new password each time one is asked for."""

    def __init__(self, user="sam@example.com"):
        self.issued = 0
        self.current_user = SimpleNamespace(me=lambda: SimpleNamespace(user_name=user))
        self.postgres = SimpleNamespace(generate_database_credential=self._credential)

    def _credential(self, endpoint):
        self.issued += 1
        return SimpleNamespace(token=f"token-{self.issued}", endpoint=endpoint)


# -- owners -------------------------------------------------------------------


def test_two_people_in_one_database_never_see_each_others_documents(tmp_path):
    url = sqlite_url(tmp_path)
    sam, alex = DocStore(url, owner="sam@example.com"), DocStore(url, owner="alex@example.com")
    sam.set("data/users/local/progress", {"days": ["2026-10-12"]})
    sam.set("study/s1", {"text": "MERGE"})
    assert alex.get("data/users/local/progress") is None and alex.list("study") == []
    alex.set("study/s1", {"text": "same id, different person"})
    assert sam.get("study/s1") == {"text": "MERGE"}
    alex.delete("study/s1")
    assert sam.get("study/s1") == {"text": "MERGE"}


def test_on_your_own_mac_the_owner_is_local(tmp_path, monkeypatch):
    monkeypatch.delenv("DRILL_OWNER", raising=False)
    assert DocStore(sqlite_url(tmp_path)).owner == "local"


def test_a_file_from_before_owners_is_upgraded_and_keeps_its_documents(tmp_path):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE docs (path VARCHAR(512) PRIMARY KEY, body TEXT NOT NULL, updated_at FLOAT NOT NULL)")
        conn.execute("INSERT INTO docs VALUES ('study/a', '{\"text\": \"alias\"}', 5)")
    store = DocStore(f"sqlite:///{path}")
    assert store.get("study/a") == {"text": "alias"} and store.owner == "local"
    assert DocStore(f"sqlite:///{path}").get("study/a") == {"text": "alias"}  # opening it again changes nothing


def test_drill_home_moves_the_files_out_of_the_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("DRILL_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("DRILL_DATABASE_URL", raising=False)
    assert store_mod.database_url() == f"sqlite:///{tmp_path / 'home' / 'drill.db'}"


# -- the activity log -----------------------------------------------------------


def test_progress_changes_become_events():
    before = {"lessons": {"a": {"step": 1, "checked": None, "done": False}}, "solved": {"p": {"count": 1, "hints": 0}}}
    after = {
        "lessons": {"a": {"step": 3, "checked": 2, "done": True}, "b": {"step": 0, "checked": None, "done": False}},
        "solved": {"p": {"count": 2, "hints": 1}, "q": {"count": 1, "hints": 3}},
    }
    assert list(activity.progress_events(before, after)) == [
        ("step", "a", {"step": 3}),
        ("checked", "a", {"answer": 2}),
        ("lesson_done", "a", {}),
        ("solved", "p", {"hints": 1, "count": 2}),
        ("solved", "q", {"hints": 3, "count": 1}),
    ]
    assert list(activity.progress_events(after, after)) == []  # saving the same thing again records nothing


def test_the_page_saving_progress_and_asking_are_logged(tmp_path):
    store = DocStore(sqlite_url(tmp_path))
    model = GenericFakeChatModel(messages=iter([AIMessage(content="Look at the gate.")]))
    router = ModelRouter(Route("local", "fake", model), None, store)
    client = TestClient(create_app(store=store, router=router, bank=Bank.load(), with_mcp=False))
    client.put("/api/docs/data/users/local/progress", json={"lessons": {"claim_gate": {"step": 1, "checked": None, "done": False}}})
    client.patch("/api/docs/data/users/local/progress", json={"lessons": {"claim_gate": {"step": 3, "checked": 0, "done": True}}})
    client.put("/api/docs/study/x1", json={"text": "not progress, so no event"})
    client.post("/api/ask", json={"prompt": "why?", "trace": {"feature": "hint", "lesson_id": "claim_gate", "hint_level": 2}})
    kinds = [(e["kind"], e["lesson_id"]) for e in store.events()]
    assert kinds == [("step", "claim_gate"), ("step", "claim_gate"), ("checked", "claim_gate"),
                     ("lesson_done", "claim_gate"), ("asked", "claim_gate")]
    assert store.events()[-1]["detail"] == {"feature": "hint", "hint_level": 2}
    assert client.get("/api/health").json()["owner"] == "local"


# -- saving ---------------------------------------------------------------------


def test_saving_the_same_document_twice_replaces_it(tmp_path):
    store = DocStore(sqlite_url(tmp_path))
    store.set("study/a", {"n": 1})
    store.set("study/a", {"n": 2})
    assert store.get("study/a") == {"n": 2} and len(store.list("study")) == 1


def test_counters_added_from_many_threads_at_once_are_all_counted(tmp_path):
    store = DocStore(sqlite_url(tmp_path))
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: store.add("usage/today", "hosted", {"calls": 1, "tokens": 10}), range(40)))
    assert store.get("usage/today") == {"hosted": {"calls": 40, "tokens": 400}}


# -- Lakebase -------------------------------------------------------------------


def test_the_lakebase_password_is_fetched_once_and_renewed_when_it_runs_out():
    databricks = FakeDatabricks()
    login = LakebaseLogin("projects/p/branches/b/endpoints/e", client=databricks)
    assert login.user == "sam@example.com"
    assert login.password() == login.password() == "token-1"
    login._until = 0  # the hour is up
    assert login.password() == "token-2"


def test_lakebase_out_of_reach_falls_back_to_this_machine(tmp_path, monkeypatch):
    databricks = FakeDatabricks()
    monkeypatch.setenv("DRILL_HOME", str(tmp_path))
    monkeypatch.setenv("DRILL_LAKEBASE_ENDPOINT", "projects/p/branches/b/endpoints/e")
    # Nothing listens on port 1, so the connection is refused straight away.
    monkeypatch.setenv("DRILL_DATABASE_URL", "postgresql+psycopg://127.0.0.1:1/databricks_postgres?connect_timeout=2")
    store = open_store(make_login=lambda endpoint: LakebaseLogin(endpoint, client=databricks))
    assert databricks.issued == 1  # it did sign in with a fresh password before the connection failed
    assert store.fallback and store.kind == "sqlite" and store.owner == "sam@example.com"
    assert store.url == f"sqlite:///{tmp_path / 'drill.db'}"


def test_in_a_databricks_app_lakebase_out_of_reach_stops_the_app_instead_of_losing_work(tmp_path, monkeypatch):
    databricks = FakeDatabricks()
    monkeypatch.setenv("DRILL_HOME", str(tmp_path))
    monkeypatch.setenv("DATABRICKS_APP_NAME", "daily-drill")
    monkeypatch.setenv("DRILL_LAKEBASE_ENDPOINT", "projects/p/branches/b/endpoints/e")
    monkeypatch.setenv("DRILL_DATABASE_URL", "postgresql+psycopg://127.0.0.1:1/databricks_postgres?connect_timeout=2")
    monkeypatch.setattr(store_mod.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="will not start"):
        open_store(make_login=lambda endpoint: LakebaseLogin(endpoint, client=databricks), wait=5)
    assert databricks.issued >= 2  # it tried again before giving up
    assert not (tmp_path / "drill.db").exists()  # and never started saving to the app's wiped disk


def test_no_lakebase_settings_means_the_local_file(tmp_path, monkeypatch):
    monkeypatch.setenv("DRILL_HOME", str(tmp_path))
    monkeypatch.delenv("DRILL_LAKEBASE_ENDPOINT", raising=False)
    monkeypatch.delenv("DRILL_DATABASE_URL", raising=False)
    store = open_store()
    assert store.kind == "sqlite" and not store.fallback


def test_push_sends_documents_and_events_up_once(tmp_path):
    here = DocStore(sqlite_url(tmp_path, "here.db"), owner="local")
    work = DocStore(sqlite_url(tmp_path, "work.db"), owner="sam@example.com")
    here.set("study/s1", {"text": "MERGE"}, updated_at=10)
    here.set("study/s2", {"text": "older here"}, updated_at=10)
    work.set("study/s2", {"text": "newer at work"}, updated_at=20)
    here.log("lesson_done", "claim_gate")
    assert here.push_to(work) == {"docs": 1, "skipped": 1, "events": 1}
    assert work.get("study/s1") == {"text": "MERGE"} and work.get("study/s2") == {"text": "newer at work"}
    assert [e["owner"] for e in work.events()] == ["sam@example.com"]
    assert here.push_to(work) == {"docs": 0, "skipped": 2, "events": 0}  # running it twice is harmless

