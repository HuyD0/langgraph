"""Content packs: optional lessons loaded from YAML, never part of the public build.

All offline, with the fictional pack in tests/fixtures/content-packs/example and the slot pack
in content-packs/iac-applied. No cloud credentials, no private repositories.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from drill.content import build, modules, packs
from drill.content.build import page_source

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "tests" / "fixtures" / "content-packs" / "example"
SLOTS = ROOT / "content-packs" / "iac-applied"


@pytest.fixture(scope="module")
def core():
    return modules.load()


@pytest.fixture
def copy(tmp_path):
    """A writable copy of the example pack, to break on purpose."""
    dest = tmp_path / "example"
    shutil.copytree(EXAMPLE, dest)
    return dest


def ids(pack):
    return [lesson["id"] for m in pack.modules for lesson in m.lessons]


def test_the_public_build_has_no_pack(core, monkeypatch):
    monkeypatch.setenv("DRILL_CONTENT_PACKS", str(EXAMPLE))  # even when one is configured
    data = build.build_data(core)
    assert not any(lid.startswith("ex_") for lid in data["lessons"])
    assert [m["id"] for m in data["modules"]] == modules.ORDER, "the curriculum is unchanged"
    html = build.render_page(data)
    assert "ex_config_links" not in html and "orbit" not in html


def test_build_page_writes_packs_only_where_git_ignores_them(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    assert build.main(["--out", str(tmp_path / "public")]) == 0
    assert "ex_config_links" not in (tmp_path / "public" / "daily-drill.html").read_text(encoding="utf-8")
    assert build.main(["--out", str(tmp_path / "private"), "--pack", str(EXAMPLE)]) == 0
    page = (tmp_path / "private" / "daily-drill.html").read_text(encoding="utf-8")
    assert "ex_config_links" in page and "data:image/svg+xml;base64," in page, "assets travel inside a static page"
    import subprocess

    ignored = subprocess.run(["git", "check-ignore", "-q", "dist/private/daily-drill.html"], cwd=ROOT)
    assert ignored.returncode == 0, "the default --pack output (dist/private/) must be ignored by git"


def test_an_enabled_pack_joins_its_phase(core):
    pack = packs.load_pack(EXAMPLE, drafts=False)
    assert ids(pack) == ["ex_config_links", "ex_trace_field", "ex_order_steps", "ex_repair_config",
                         "ex_read_run", "ex_failed_run", "ex_plan_review", "ex_self_check"]
    assert sorted(pack.hidden) == ["ex_draft_only", "ex_slot_only"], "slots always, drafts unless previewing"
    data = build.build_data(core, [pack])
    ship = next(p for p in data["lifecycle"] if p["name"] == pack.phase)
    assert ship["modules"][-2:] == ["example-configure", "example-review"]
    order = [m["id"] for m in data["modules"]]
    assert order.index("example-review") < order.index("tracing"), "inside its phase, not at the end of the path"
    lesson = data["lessons"]["ex_failed_run"]
    assert lesson["check"][2] == 1 and lesson["pack"]["practice"]["kind"] == "troubleshooting"
    stub = next(p for p in data["bank"] if p["id"] == "ex_failed_run")
    assert stub["practice"] and stub["fn"] == "" and stub["cases"] == []
    assert all(lid in data["lessons"] for lid in modules.ORDER and [x for m in core for x in m.lesson_ids])


def test_drafts_show_when_previewing():
    assert "ex_draft_only" in ids(packs.load_pack(EXAMPLE, drafts=True))


def test_slots_and_empty_journeys_leave_no_gaps(copy):
    for f in (copy / "lessons").glob("*.yaml"):
        text = f.read_text(encoding="utf-8").replace("status: ready", "status: slot")
        f.write_text(text, encoding="utf-8")
    pack = packs.load_pack(copy, drafts=False)
    assert pack.modules == [], "a journey with nothing to show is left out of the path"


def test_every_practice_kind_has_a_renderer_and_a_contract():
    page = page_source()
    shapes = page.split("const PX_SHAPE = {")[1].split("};")[0]
    for kind, shape in packs.PRACTICE_KINDS.items():
        assert f'{kind}: "{shape}"' in shapes, f"page.html has no renderer for {kind}"
        assert f'shape === "{shape}"' in page
    template = (ROOT / "content-packs" / "templates" / "exercise.example.yaml").read_text(encoding="utf-8")
    for kind in packs.PRACTICE_KINDS:
        assert f"kind: {kind}" in template, f"the exercise template has no {kind} example"
    for view in packs.VIEW_KINDS:
        assert f'v.kind === "{view}"' in page, f"page.html cannot draw a {view} view"


@pytest.mark.parametrize("kind", sorted(packs.PRACTICE_KINDS))
def test_each_kind_reports_what_it_is_missing(kind):
    problems = packs.check_practice({"kind": kind}, "x")
    assert any("missing 'prompt'" in p for p in problems)
    assert len(problems) >= 2, f"{kind} should also name its own required fields"


def test_mistakes_are_named_by_file_and_field(copy, core):
    taken = {lesson["id"] for m in core for lesson in m.lessons}
    f = copy / "lessons" / "order-steps.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace("answer: 1", "answer: 7").replace("kind: ordering", "kind: dance"), encoding="utf-8")
    g = copy / "lessons" / "config-links.yaml"
    g.write_text(g.read_text(encoding="utf-8").replace("sources: [ev_team_doc]", "sources: [ev_missing]")
                 .replace("assets/request-flow.svg", "assets/nope.svg"), encoding="utf-8")
    with pytest.raises(packs.PackError) as err:
        packs.load_pack(copy, taken=taken)
    text = str(err.value)
    assert "order-steps.yaml: check.answer must be the index" in text
    assert "order-steps.yaml: practice: kind 'dance'" in text
    assert "config-links.yaml: learn.sources names 'ev_missing'" in text
    assert "config-links.yaml: learn refers to 'assets/nope.svg'" in text


def test_an_asset_outside_the_pack_folder_is_refused(copy, tmp_path):
    """The server serves and the static build inlines whatever a lesson names: it must stay in the pack."""
    secret = tmp_path / "secret.txt"
    secret.write_text("not for the page", encoding="utf-8")
    (copy / "assets" / "link.svg").symlink_to(secret)
    f = copy / "lessons" / "config-links.yaml"
    original = f.read_text(encoding="utf-8")
    for ref in ("../secret.txt", str(secret), "assets/../../secret.txt", "assets/link.svg"):
        f.write_text(original.replace("assets/request-flow.svg", ref), encoding="utf-8")
        with pytest.raises(packs.PackError) as err:
            packs.load_pack(copy)
        assert f"'{ref}' points outside the pack folder" in str(err.value), ref
    f.write_text(original, encoding="utf-8")
    assert packs.load_pack(copy).assets["assets/request-flow.svg"].endswith("request-flow.svg"), "a file inside still works"


def test_pack_dirs_skip_a_folder_that_is_not_there(tmp_path, caplog):
    """app.yaml can name a pack by default; a checkout without that folder still starts, with one log line."""
    here = tmp_path / "here"
    here.mkdir()
    env = os.pathsep.join([str(here), str(tmp_path / "gone"), "content-packs/iac-applied"])
    with caplog.at_level(logging.INFO, logger="drill.content.packs"):
        assert packs.pack_dirs(env) == [here, SLOTS], "a relative path counts from the project root"
    assert "gone" in caplog.text and "skipping" in caplog.text
    assert packs.pack_dirs("") == []


def test_duplicate_and_clashing_ids_are_rejected(copy, core):
    f = copy / "lessons" / "trace-field.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace("id: ex_trace_field", "id: ex_config_links"), encoding="utf-8")
    with pytest.raises(packs.PackError, match="already used"):
        packs.load_pack(copy)
    f.write_text(f.read_text(encoding="utf-8").replace("id: ex_config_links", "id: split_by_key"), encoding="utf-8")
    with pytest.raises(packs.PackError, match="already a lesson in the curriculum"):
        packs.load_pack(copy, taken={lesson["id"] for m in core for lesson in m.lessons})


def test_a_ready_lesson_cannot_keep_placeholders(copy):
    f = copy / "lessons" / "draft-only.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace("status: draft", "status: ready"), encoding="utf-8")
    with pytest.raises(packs.PackError, match="_TODO placeholder"):
        packs.load_pack(copy)


def test_aliases_carry_progress_over(copy):
    f = copy / "lessons" / "config-links.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace("id: ex_config_links", "id: ex_config_links_v2\naliases: [ex_config_links]")
                 .replace("prerequisites: [ex_config_links]", ""), encoding="utf-8")
    t = copy / "lessons" / "trace-field.yaml"
    t.write_text(t.read_text(encoding="utf-8").replace("prerequisites: [ex_config_links]", "prerequisites: [ex_config_links_v2]"), encoding="utf-8")
    pack = packs.load_pack(copy)
    lesson = next(lesson for m in pack.modules for lesson in m.lessons if lesson["id"] == "ex_config_links_v2")
    assert lesson["pack"]["aliases"] == ["ex_config_links"]
    page = page_source()
    assert "function migrateAliases()" in page and page.count("migrateAliases();") >= 2


def test_the_slot_pack_defines_both_journeys_and_the_capstone():
    pack = packs.load_pack(SLOTS, drafts=True)
    assert pack.modules == [], "slots show nothing"
    assert len(pack.hidden) == 13
    assert {h[:6] for h in pack.hidden} == {"iac_a1", "iac_a2", "iac_a3", "iac_a4", "iac_a5", "iac_a6", "iac_b1",
                                             "iac_b2", "iac_b3", "iac_b4", "iac_b5", "iac_b6", "iac_c1"}


def test_the_public_repository_holds_no_real_content():
    """While content-packs/PUBLIC exists, packs here are slots only, with no files in assets."""
    if not (ROOT / "content-packs" / "PUBLIC").exists():
        pytest.skip("the private copy: real lessons belong here")
    import yaml

    # Only the shared packs: internal/ (the work copy's real lessons) and private/ (a laptop's own) may be filled.
    shared = [p for p in (ROOT / "content-packs").iterdir() if p.is_dir() and p.name not in ("internal", "private", "templates")]
    assert shared, "no shared pack found under content-packs/"
    for pack in shared:
        for f in pack.glob("lessons/*.yaml"):
            assert yaml.safe_load(f.read_text(encoding="utf-8"))["status"] == "slot", f"{f} is filled in; keep real lessons private"
        for f in pack.glob("assets/*"):
            assert f.name == "README.md", f"{f}: keep screenshots and diagrams in the private copy"


def test_the_server_serves_a_pack_and_only_its_named_files(tmp_path, monkeypatch):
    from drill.server.api import create_app
    from drill.server.bank import Bank
    from drill.server.router import ModelRouter
    from drill.server.store import DocStore

    monkeypatch.setenv("DRILL_CONTENT_PACKS", str(EXAMPLE))
    bank = Bank.load()
    assert "ex_failed_run" in bank.lessons and bank.card("ex_failed_run")["practice"]["kind"] == "troubleshooting"
    store = DocStore(f"sqlite:///{tmp_path / 'd.db'}")
    client = TestClient(create_app(store=store, router=ModelRouter(None, None, store), bank=bank, with_mcp=False))
    assert "ex_config_links" in client.get("/").text
    assert client.get("/pack-assets/example/assets/request-flow.svg").status_code == 200
    assert client.get("/pack-assets/example/pack.yaml").status_code == 404, "only files a lesson names"
    assert client.get("/pack-assets/example/../../../README.md").status_code == 404
    assert bank.pack_asset("example", "assets/request-flow.svg")
    assert bank.pack_asset("example", "assets/../assets/request-flow.svg") is None, "never a step up"


def test_without_a_pack_the_server_is_unchanged(monkeypatch):
    from drill.server.bank import Bank

    monkeypatch.delenv("DRILL_CONTENT_PACKS", raising=False)
    bank = Bank.load()
    assert bank.packs == [] and not any(lid.startswith("ex_") for lid in bank.lessons)
    assert json.dumps(bank.data["modules"]) == json.dumps(build.build_data()["modules"])


def test_a_guided_tour_needs_its_image_and_boxes_inside_it(copy):
    f = copy / "lessons" / "read-run.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace("w: 28.3", "w: 128.3").replace("image: assets/run-page.svg\n      ratio", "image: assets/missing.svg\n      ratio"), encoding="utf-8")
    with pytest.raises(packs.PackError) as err:
        packs.load_pack(copy)
    assert "w must be a number from 0 to 100" in str(err.value)
    assert "learn refers to 'assets/missing.svg'" in str(err.value)


def test_a_pack_can_join_a_track_and_takes_its_setting(copy, core):
    # The IaC pack joins the Platform track, not a phase of the path; its tutor stays in that world.
    f = copy / "pack.yaml"
    f.write_text(f.read_text(encoding="utf-8").replace("phase: Ship", "track: platform"), encoding="utf-8")
    pack = packs.load_pack(copy, drafts=False)
    data = build.build_data(core, [pack])
    track = next(t for t in data["tracks"] if t["id"] == "platform")
    assert track["modules"][-2:] == ["example-configure", "example-review"]
    assert all("example" not in m for p in data["lifecycle"] for m in p["modules"]), "not in a phase as well"
    by_id = {m["id"]: m for m in data["modules"]}
    assert "Azure Databricks" in by_id["example-configure"]["setting"]
    f.write_text(f.read_text(encoding="utf-8") + "phase: Ship\n", encoding="utf-8")
    with pytest.raises(packs.PackError, match="either 'phase'"):
        packs.load_pack(copy)
    assert "track: platform" in (SLOTS / "pack.yaml").read_text(encoding="utf-8"), "the IaC slots join the Platform track"


def test_the_build_page_command_takes_a_pack(tmp_path, monkeypatch):
    # docs/CONTENT_PACKS.md says `uv run drill build-page --pack <folder>`; the command must pass it on.
    from typer.testing import CliRunner

    from drill.cli import app

    monkeypatch.chdir(ROOT)
    result = CliRunner().invoke(app, ["build-page", "--out", str(tmp_path), "--pack", str(EXAMPLE)])
    assert result.exit_code == 0, result.output
    assert "ex_config_links" in (tmp_path / "daily-drill.html").read_text(encoding="utf-8")
