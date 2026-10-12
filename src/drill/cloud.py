"""Run the Daily Drill server as a Databricks App: set up, deploy, start, stop.

    uv run drill cloud setup      # once per workspace: Lakebase project, settings file
    uv run drill cloud deploy     # upload the code and (re)start the app
    uv run drill cloud stop       # stop paying for it; progress stays in Lakebase
    uv run drill cloud start
    uv run drill cloud status     # running or not, and its address

Everything goes through the Databricks CLI and the bundle in ``databricks.yml``. A target
(``personal`` by default, or ``work``) picks the workspace; the values that name real things
in it live in ``.databricks/bundle/<target>/variable-overrides.json``, which git ignores,
so the public repo never holds them. Porting to another workspace is ``setup`` and
``deploy`` with ``--target work``. See docs/DATABRICKS_APP.md.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from drill.config import PROJECT_ROOT

APP_RESOURCE = "daily_drill"  # the app's key under resources.apps in databricks.yml
DEFAULT_APP_NAME = "daily-drill"
DEFAULT_PROJECT = "daily-drill"


class CloudError(RuntimeError):
    """A step failed; the message says what to do."""


def overrides_path(target: str) -> Path:
    return PROJECT_ROOT / ".databricks" / "bundle" / target / "variable-overrides.json"


def read_overrides(target: str) -> dict:
    path = overrides_path(target)
    return json.loads(path.read_text()) if path.is_file() else {}


def write_overrides(target: str, values: dict) -> Path:
    path = overrides_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**read_overrides(target), **values}, indent=2) + "\n")
    return path


def profile_for(target: str, given: str | None = None) -> str | None:
    """The CLI profile for a target: ``given``, else the one databricks.yml names for it."""
    if given:
        return given
    import yaml

    bundle = yaml.safe_load((PROJECT_ROOT / "databricks.yml").read_text())
    targets = bundle.get("targets") or {}
    if target not in targets:
        raise CloudError(f"No target '{target}' in databricks.yml; it has {', '.join(targets)}.")
    return ((targets[target] or {}).get("workspace") or {}).get("profile")


def app_name(target: str) -> str:
    return read_overrides(target).get("app_name", DEFAULT_APP_NAME)


def cli(*args: str, profile: str | None = None, target: str | None = None, check: bool = True) -> Any:
    """Run ``databricks <args>``; JSON output comes back parsed, anything else as text."""
    cmd = ["databricks", *args]
    if profile:
        cmd += ["--profile", profile]
    if target:
        cmd += ["--target", target]
    done = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if check and done.returncode != 0:
        raise CloudError(f"`{' '.join(cmd)}` failed:\n{(done.stderr or done.stdout).strip()}")
    out = done.stdout.strip()
    try:
        return json.loads(out) if out else None
    except json.JSONDecodeError:
        return out


# -- setup ----------------------------------------------------------------------

def ensure_lakebase(project: str, profile: str | None, create: bool) -> tuple[str, str]:
    """The project's ``production`` branch and its database, creating the project if asked to.

    A new project sleeps after five idle minutes and wakes on the next request, so a
    personal learning app costs little while nobody is studying.
    """
    found = cli("postgres", "get-project", f"projects/{project}", "-o", "json", profile=profile, check=False)
    if not isinstance(found, dict):
        if not create:
            raise CloudError(f"No Lakebase project '{project}'. Ask your platform team for one, or pass --create-lakebase.")
        spec = {"spec": {
            "display_name": "Daily Drill",
            "default_endpoint_settings": {
                "autoscaling_limit_min_cu": 0.5, "autoscaling_limit_max_cu": 1, "suspend_timeout_duration": "300s",
            },
        }}
        cli("postgres", "create-project", project, "--json", json.dumps(spec), "-o", "json", profile=profile)
    branch = f"projects/{project}/branches/production"
    databases = cli("postgres", "list-databases", branch, "-o", "json", profile=profile) or []
    if not databases:
        raise CloudError(f"{branch} has no database yet. Wait a minute and run setup again.")
    return branch, databases[0]["name"]


def experiment_id(path: str, profile: str | None) -> str:
    """The id of the MLflow experiment at ``path``, creating it if it is not there."""
    found = cli("experiments", "get-by-name", path, "-o", "json", profile=profile, check=False)
    if isinstance(found, dict) and found.get("experiment"):
        return found["experiment"]["experiment_id"]
    made = cli("experiments", "create-experiment", path, "-o", "json", profile=profile)
    return made["experiment_id"]


def me(profile: str | None) -> str:
    return cli("current-user", "me", "-o", "json", profile=profile)["userName"]


def setup(target: str, profile: str | None, project: str, create_lakebase: bool, experiment: str | None,
          model: str | None, name: str | None) -> dict:
    """Find or create what the app needs in the workspace, and save the values for ``deploy``."""
    branch, database = ensure_lakebase(project, profile, create_lakebase)
    path = experiment or f"/Users/{me(profile)}/daily-drill"
    values = {"lakebase_branch": branch, "lakebase_database": database, "experiment_id": experiment_id(path, profile)}
    if model:
        values["model"] = model
    if name:
        values["app_name"] = name
    write_overrides(target, values)
    return {**values, "experiment": path, "file": str(overrides_path(target).relative_to(PROJECT_ROOT))}


# -- deploy and run -------------------------------------------------------------

def requirements() -> Path:
    """Write requirements.txt from uv.lock: the exact versions the tests ran, plus this repo itself."""
    out = subprocess.run(
        ["uv", "export", "--no-dev", "--extra", "lakebase", "--no-hashes", "--no-emit-project",
         "--format", "requirements-txt", "--quiet"],
        cwd=PROJECT_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    pins = [line for line in out.splitlines() if line and not line.startswith(("#", " "))]
    head = (
        "# What a Databricks App installs (it reads only this file). Generated from uv.lock, so the\n"
        "# app runs the exact versions the tests ran; regenerate with `uv run drill cloud requirements`.\n"
        "# The last line installs this repo itself, editable, so its lessons and skill folder are found.\n"
    )
    path = PROJECT_ROOT / "requirements.txt"
    path.write_text(head + "\n".join(pins) + "\n-e .\n")
    return path


def stamp_version() -> str:
    """Write the commit to .drill-version, so the app's traces say which code they came from."""
    from drill.server.observe import app_version

    stamp = PROJECT_ROOT / ".drill-version"
    stamp.unlink(missing_ok=True)  # ask git, not last time's stamp
    version = app_version()
    stamp.write_text(version + "\n")
    return version


def deploy(target: str, profile: str | None) -> dict:
    """Upload the code, attach the resources, and start the app (or restart it on the new code)."""
    missing = [k for k in ("lakebase_branch", "lakebase_database", "experiment_id") if k not in read_overrides(target)]
    if missing:
        raise CloudError(f"Run `uv run drill cloud setup --target {target}` first (missing {', '.join(missing)}).")
    version = stamp_version()
    cli("bundle", "deploy", profile=profile, target=target)
    cli("bundle", "run", APP_RESOURCE, profile=profile, target=target)
    info = status(target, profile)
    allow_self_stop(info["name"], info["service_principal"], profile)
    return {**info, "version": version}


def allow_self_stop(name: str, service_principal: str, profile: str | None) -> None:
    """Let the app's service principal stop its own app, so it can switch off when idle."""
    if not service_principal:
        return
    acl = {"access_control_list": [{"service_principal_name": service_principal, "permission_level": "CAN_MANAGE"}]}
    cli("apps", "update-permissions", name, "--json", json.dumps(acl), "-o", "json", profile=profile)


def status(target: str, profile: str | None) -> dict:
    app = cli("apps", "get", app_name(target), "-o", "json", profile=profile, check=False)
    if not isinstance(app, dict):
        return {"name": app_name(target), "state": "NOT DEPLOYED", "url": ""}
    return {
        "name": app["name"],
        "state": app.get("compute_status", {}).get("state", "UNKNOWN"),
        "url": app.get("url", ""),
        "service_principal": app.get("service_principal_client_id", ""),
    }


def start(target: str, profile: str | None) -> dict:
    cli("apps", "start", app_name(target), "-o", "json", profile=profile)
    return status(target, profile)


def stop(target: str, profile: str | None) -> dict:
    cli("apps", "stop", app_name(target), "-o", "json", profile=profile)
    return status(target, profile)


# -- the manager's view ------------------------------------------------------------

DEFAULT_CATALOG = "daily_drill_lakebase"


def ensure_catalog(target: str, profile: str | None, catalog: str) -> str:
    """A read-only Unity Catalog catalog over the app's Lakebase database, so a SQL warehouse
    (and the dashboard) can read it. Found if it is there, else registered."""
    found = cli("postgres", "get-catalog", f"catalogs/{catalog}", "-o", "json", profile=profile, check=False)
    if isinstance(found, dict) and found.get("catalog_id"):
        return catalog
    values = read_overrides(target)
    if "lakebase_database" not in values:
        raise CloudError(f"Run `uv run drill cloud setup --target {target}` first.")
    database = cli("postgres", "get-database", values["lakebase_database"], "-o", "json", profile=profile)
    spec = {"spec": {"branch": values["lakebase_branch"], "postgres_database": database["status"]["postgres_database"]}}
    cli("postgres", "create-catalog", catalog, "--json", json.dumps(spec), "-o", "json", profile=profile)
    return catalog


def manager_view(target: str, profile: str | None, warehouse: str | None = None, catalog: str | None = None) -> dict:
    """Find or create the catalog and the learners dashboard, then publish it with your
    credentials (so it reads every learner's rows). Running it again updates both."""
    from drill import manager_view as view

    values = read_overrides(target)
    warehouse = warehouse or values.get("warehouse_id")
    if not warehouse:
        raise CloudError("Pass --warehouse <id>: a small serverless SQL warehouse (Lakebase catalogs need serverless).")
    catalog = ensure_catalog(target, profile, catalog or values.get("lakebase_catalog") or DEFAULT_CATALOG)
    body = {"display_name": view.DASHBOARD_NAME, "warehouse_id": warehouse, "serialized_dashboard": view.serialized(catalog)}
    dashboard_id = values.get("manager_dashboard_id")
    existing = cli("lakeview", "get", dashboard_id, "-o", "json", profile=profile, check=False) if dashboard_id else None
    if isinstance(existing, dict) and existing.get("lifecycle_state") != "TRASHED":
        cli("lakeview", "update", dashboard_id, "--json", json.dumps(body), "-o", "json", profile=profile)
    else:
        body["parent_path"] = f"/Users/{me(profile)}"
        dashboard_id = cli("lakeview", "create", "--json", json.dumps(body), "-o", "json", profile=profile)["dashboard_id"]
    cli("lakeview", "publish", dashboard_id, "--embed-credentials", "--warehouse-id", warehouse, "-o", "json", profile=profile)
    write_overrides(target, {"lakebase_catalog": catalog, "warehouse_id": warehouse, "manager_dashboard_id": dashboard_id})
    host = cli("auth", "describe", "-o", "json", profile=profile, check=False)
    host = (host or {}).get("details", {}).get("host", "") if isinstance(host, dict) else ""
    return {"catalog": catalog, "dashboard_id": dashboard_id,
            "url": f"{host.rstrip('/')}/dashboardsv3/{dashboard_id}/published" if host else dashboard_id}
