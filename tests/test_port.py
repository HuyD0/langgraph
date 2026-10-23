"""`drill cloud port`: the plan it makes from what a workspace has, and what share grants. All offline."""

from __future__ import annotations

import json

import pytest

from drill import cloud, port

MODEL = "ai.models.haiku"


def fake_cli(have: set[str], calls: list):
    """A Databricks CLI that knows only the objects in ``have``."""
    def cli(*args, profile=None, target=None, check=True):
        calls.append(args)
        key = " ".join(a for a in args if a not in ("-o", "json"))
        if args[0] == "current-user":
            return {"userName": "me@corp.com"} if "signin" in have else "Error: not signed in"
        if args[:2] in (("apps", "list"), ("postgres", "list-projects")):
            return [] if "features" in have else "Error: not enabled"
        if args[0] == "api" and "model-services" in args[2]:
            return {"name": MODEL} if "model" in have else "Error: 404"
        if args[:2] == ("warehouses", "list"):
            return []
        for thing in have:
            if key.endswith(thing):
                return {"name": thing, "experiment": {"experiment_id": "1"}}
        return "Error: does not exist"
    return cli


@pytest.fixture(autouse=True)
def no_saved(monkeypatch):
    monkeypatch.setattr(cloud, "read_overrides", lambda target: {})
    monkeypatch.setattr(port, "cli_version", lambda: (1, 20))


def states(p):
    return {s.name.split(" (")[0]: s.state for s in p.steps}


def test_a_fresh_workspace_plans_to_create_what_is_missing():
    have = {"signin", "features", "model", "team"}  # the catalog exists, nothing else does
    p = port.plan("work", "work", catalog="team", model=MODEL, project="dd", experiment="/Shared/dd/x",
                  warehouse=None, cli=fake_cli(have, []))
    got = states(p)
    assert not p.blocked
    assert got["schema team.drill_traces"] == got["schema team.daily_drill"] == port.CREATE
    assert got["SQL warehouse 'daily-drill'"] == got["Lakebase project dd"] == got["experiment /Shared/dd/x"] == port.CREATE
    assert p.values["trace_schema"] == "team.drill_traces" and p.values["model"] == MODEL


def test_what_blocks_a_port_says_what_to_do():
    p = port.plan("work", "work", catalog=None, model=None, project="dd", experiment=None, warehouse=None,
                  cli=fake_cli({"signin"}, []))
    blocked = {s.name: s.todo for s in p.blocked}
    assert "Databricks Apps enabled" in blocked and "Lakebase available" in blocked
    assert "--model" in blocked["model service"] and "--catalog" in blocked["trace and prompt schemas"]
    with pytest.raises(cloud.CloudError):
        port.apply(p, learners=[], managers=None, say=lambda _: None)


def test_not_signed_in_stops_at_the_sign_in():
    p = port.plan("work", "work", catalog="t", model=MODEL, project="dd", experiment=None, warehouse=None,
                  cli=fake_cli(set(), []))
    assert [s.state for s in p.steps][-1] == port.BLOCKED and "auth login" in p.steps[-1].todo


def test_share_lets_learners_use_the_app_and_managers_read_the_dashboard(monkeypatch):
    monkeypatch.setattr(cloud, "read_overrides", lambda t: {"manager_dashboard_id": "d1", "lakebase_catalog": "lb"})
    calls: list = []
    out = port.share("work", "work", ["ana@corp.com"], "drill-managers", cli=lambda *a, **k: calls.append(a))
    acl = json.loads(calls[0][calls[0].index("--json") + 1])["access_control_list"]
    assert {"user_name": "ana@corp.com", "permission_level": "CAN_USE"} in acl
    assert {"group_name": "drill-managers", "permission_level": "CAN_USE"} in acl
    assert any("/permissions/dashboards/d1" in " ".join(c) for c in calls)
    assert any("unity-catalog/permissions/catalog/lb" in " ".join(c) for c in calls)
    assert len(out) == 4


def test_ask_mode_asks_what_is_missing_and_changes_nothing_on_no(monkeypatch):
    import subprocess
    from types import SimpleNamespace

    from typer.testing import CliRunner

    import drill.cli as cli

    for name in ("DRILL_TARGET", "DRILL_PROFILE", "DRILL_CATALOG", "DRILL_MODEL", "DRILL_MANAGERS", "DRILL_LEARNERS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("shutil.which", lambda tool: f"/bin/{tool}")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))  # already signed in
    asked = {}
    monkeypatch.setattr(port, "plan", lambda target, profile, **kw: asked.update(target=target, profile=profile, **kw)
                        or port.Plan(target, profile))
    monkeypatch.setattr(port, "apply", lambda *a, **k: pytest.fail("applied without a yes"))
    # Enter keeps "work" for the target and the profile; then catalog, model, no managers, two learners, and "n"
    answers = "\n\nteam\n" + MODEL + "\n\na@corp.com b@corp.com\nn\n"
    result = CliRunner().invoke(cli.app, ["cloud", "port", "--ask"], input=answers)
    assert result.exit_code == 0, result.output
    assert asked["target"] == asked["profile"] == "work" and asked["catalog"] == "team" and asked["model"] == MODEL
    assert "Nothing changed" in result.output


def test_ask_mode_names_the_install_command_for_a_missing_tool(monkeypatch):
    import sys

    from typer.testing import CliRunner

    import drill.cli as cli

    monkeypatch.setattr("shutil.which", lambda tool: None if tool == "databricks" else f"/bin/{tool}")
    monkeypatch.setattr(sys, "platform", "win32")
    result = CliRunner().invoke(cli.app, ["cloud", "port", "--ask"])
    assert result.exit_code == 1 and "winget install --exact --id Databricks.DatabricksCLI" in result.output
