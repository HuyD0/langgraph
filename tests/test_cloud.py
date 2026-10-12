"""The Databricks App deploy files must agree with each other and name no real workspace."""

from __future__ import annotations

import re

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
