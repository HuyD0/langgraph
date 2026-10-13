"""The Databricks App deploy files must agree with each other and name no real workspace."""

from __future__ import annotations

import re

import pytest
import yaml

from drill import cloud
from drill.config import PROJECT_ROOT


def test_app_yaml_takes_every_workspace_value_from_a_resource_the_bundle_attaches():
    app = yaml.safe_load((PROJECT_ROOT / "app.yaml").read_text())
    bundle = yaml.safe_load((PROJECT_ROOT / "databricks.yml").read_text())
    attached = {r["name"] for r in bundle["resources"]["apps"][cloud.APP_RESOURCE]["resources"]}
    wanted = {e["valueFrom"] for e in app["env"] if "valueFrom" in e}
    assert wanted == attached
    assert set(bundle["targets"]) == {"personal", "work"}


def test_the_deploy_files_name_no_real_workspace():
    for name in ("app.yaml", "databricks.yml"):
        text = (PROJECT_ROOT / name).read_text()
        assert not re.search(r"adb-\d+|azuredatabricks\.net|@[a-z0-9-]+\.[a-z]+|\b\d{12,}\b", text), name


def test_requirements_match_the_lock_file():
    """Change a dependency, then run `uv run drill cloud requirements`; this fails until you do."""
    text = (PROJECT_ROOT / "requirements.txt").read_text()
    pins = dict(re.findall(r"^([A-Za-z0-9_.\-\[\]]+)==([^\s;]+)", text, flags=re.M))
    lock = (PROJECT_ROOT / "uv.lock").read_text()
    for package, version in pins.items():
        name = re.sub(r"\[.*\]", "", package).lower().replace("_", "-")
        assert f'name = "{name}"\nversion = "{version}"' in lock.replace("_", "-"), f"{package}=={version}"
    assert text.rstrip().endswith("-e .")
    assert "fastapi==" in text and "psycopg==" in text


def test_setup_values_are_kept_out_of_git(tmp_path, monkeypatch):
    monkeypatch.setattr(cloud, "PROJECT_ROOT", tmp_path)
    cloud.write_overrides("work", {"experiment_id": "1"})
    cloud.write_overrides("work", {"app_name": "drill-test"})
    assert cloud.read_overrides("work") == {"experiment_id": "1", "app_name": "drill-test"}
    assert cloud.app_name("work") == "drill-test"
    gitignore = (PROJECT_ROOT / ".gitignore").read_text().splitlines()
    assert ".databricks/" in gitignore and ".drill-version" in gitignore


# -- deploy never leaves a broken app billing ---------------------------------------


class FakeCLI:
    """Stands in for the Databricks CLI: records each call and answers ``apps get`` with ``app``."""

    def __init__(self, app=None, fail_on=None):
        self.app, self.fail_on, self.calls = app, fail_on, []

    def __call__(self, *args, profile=None, target=None, check=True):
        self.calls.append(args[:2])
        if self.fail_on and args[:2] == self.fail_on:
            raise cloud.CloudError("boom")
        if args[:2] == ("apps", "get"):
            return self.app
        return None


def deploy_with(monkeypatch, tmp_path, fake):
    monkeypatch.setattr(cloud, "PROJECT_ROOT", tmp_path)
    cloud.write_overrides("personal", {"lakebase_branch": "b", "lakebase_database": "d", "experiment_id": "1"})
    monkeypatch.setattr(cloud, "stamp_version", lambda: "abc123")
    monkeypatch.setattr(cloud, "cli", fake)
    return cloud.deploy("personal", None)


def running_app(app_state="RUNNING", sp="sp-1"):
    return {"name": "daily-drill", "url": "https://x", "service_principal_client_id": sp,
            "compute_status": {"state": "ACTIVE"}, "app_status": {"state": app_state}}


def test_a_healthy_deploy_lets_the_app_stop_itself(monkeypatch, tmp_path):
    fake = FakeCLI(running_app())
    info = deploy_with(monkeypatch, tmp_path, fake)
    assert info["version"] == "abc123" and ("apps", "update-permissions") in fake.calls
    assert ("apps", "stop") not in fake.calls


def test_an_app_whose_code_crashed_is_stopped_so_it_does_not_bill(monkeypatch, tmp_path):
    fake = FakeCLI(running_app("CRASHED"))
    with pytest.raises(cloud.CloudError, match="stopped to save money"):
        deploy_with(monkeypatch, tmp_path, fake)
    assert ("apps", "stop") in fake.calls


def test_a_failed_start_says_the_app_may_still_be_billing(monkeypatch, tmp_path):
    with pytest.raises(cloud.CloudError, match="drill cloud stop"):
        deploy_with(monkeypatch, tmp_path, FakeCLI(running_app(), fail_on=("bundle", "run")))


def test_an_app_with_no_service_principal_is_a_clear_error_not_a_traceback(monkeypatch, tmp_path):
    with pytest.raises(cloud.CloudError, match="stop itself"):
        deploy_with(monkeypatch, tmp_path, FakeCLI(running_app(sp="")))


def test_a_missing_databricks_cli_is_a_clear_error(monkeypatch):
    def missing(*a, **k):
        raise FileNotFoundError("databricks")

    monkeypatch.setattr(cloud.subprocess, "run", missing)
    with pytest.raises(cloud.CloudError, match="brew install databricks"):
        cloud.cli("apps", "list")
