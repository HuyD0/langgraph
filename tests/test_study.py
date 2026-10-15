"""The study list: merging two copies of it, and which items are due for a review."""

from __future__ import annotations

import json

from drill.server import mcp as mcp_door
from drill.server import study
from drill.server.store import DocStore


def item(item_id: str, text: str = "x", **fields) -> dict:
    return {"id": item_id, "text": text, "status": "open", "createdAt": 1, **fields}


def test_merge_adds_missing_items_and_keeps_the_newer_copy():
    mine = [item("a", "old", updatedAt=5), item("b")]
    theirs = [item("a", "new", updatedAt=9), item("b", "an older copy", updatedAt=0), item("c")]
    writes, counts = study.merge(mine, theirs)
    assert [w["id"] for w in writes] == ["a", "c"] and writes[0]["text"] == "new"
    assert counts == {"added": 1, "updated": 1, "unchanged": 1}


def test_merging_the_same_list_twice_changes_nothing(tmp_path):
    store = DocStore(f"sqlite:///{tmp_path / 'drill.db'}")
    theirs = [item("a"), item("b", status="got", reviewAt=0)]
    assert study.import_items(store, theirs) == {"added": 2, "updated": 0, "unchanged": 0}
    assert study.import_items(store, theirs) == {"added": 0, "updated": 0, "unchanged": 2}
    assert sorted(i["id"] for i in study.load(store)) == ["a", "b"]


def test_items_come_from_a_file_or_a_folder_of_item_files(tmp_path):
    (tmp_path / "list.json").write_text(json.dumps([item("a"), item("b")]))
    folder = tmp_path / "export" / "study"  # how an artifact database export is laid out
    folder.mkdir(parents=True)
    (folder / "c.json").write_text(json.dumps(item("c")))
    assert [i["id"] for i in study.read_items(tmp_path / "list.json")] == ["a", "b"]
    assert [i["id"] for i in study.read_items(tmp_path / "export")] == ["c"]


def test_due_means_understood_and_past_its_review_time():
    assert study.is_due(item("a", status="got", reviewAt=100), now_ms=200)
    assert not study.is_due(item("a", status="got", reviewAt=300), now_ms=200)
    assert not study.is_due(item("a", reviewAt=0), now_ms=200)  # still being learned
    assert study.is_due(item("a", status="got"), now_ms=200)  # understood but never scheduled: due now
    assert study.REVIEW_DAYS == (3, 10, 30, 90)


def test_drill_study_exports_and_imports(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    import drill.cli as cli

    monkeypatch.setattr(cli, "_load_dotenv", lambda: None)  # never read the developer's .env here
    monkeypatch.setenv("DRILL_DATABASE_URL", f"sqlite:///{tmp_path / 'drill.db'}")
    source = tmp_path / "in.json"
    source.write_text(json.dumps([item("a", "MERGE INTO")]))
    runner = CliRunner()
    imported = runner.invoke(cli.app, ["study", "import", str(source)])
    assert imported.exit_code == 0 and "Added 1" in imported.output
    out = tmp_path / "out.json"
    assert runner.invoke(cli.app, ["study", "export", str(out)]).exit_code == 0
    assert [i["text"] for i in json.loads(out.read_text())] == ["MERGE INTO"]


def test_claude_can_ask_for_the_items_due_for_review(tmp_path):
    store = DocStore(f"sqlite:///{tmp_path / 'drill.db'}")
    store.set("study/a", item("a", "MERGE INTO"))
    store.set("study/b", item("b", "pass^k", status="got", reviewAt=0))
    store.set("study/c", item("c", "nDCG", status="got", reviewAt=9e15))  # not due for a long time
    mcp_door.configure(store=store)
    assert [i["text"] for i in mcp_door.study_list("due")] == ["pass^k"]
    assert sorted(i["text"] for i in mcp_door.study_list("got")) == ["nDCG", "pass^k"]
    saved = mcp_door.save_to_study("MLflow assessments")
    assert store.get(f"study/{saved['id']}")["updatedAt"] > 0  # so merging can tell which copy is newer


def test_the_page_never_drops_study_list_changes_made_while_it_connects():
    """Runs the page's own study-list code in node against a slow, partly failing fake account."""
    import shutil
    import subprocess
    from pathlib import Path

    import pytest

    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    root = Path(__file__).resolve().parent
    script = root.parent / "src" / "drill" / "content" / "page" / "study-list.js"
    result = subprocess.run([node, str(root / "fixtures" / "study_sync.js"), str(script)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr[-800:]
