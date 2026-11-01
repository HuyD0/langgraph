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
import tempfile
import time
from pathlib import Path
from typing import Any

from drill.config import PROJECT_ROOT

APP_RESOURCE = "daily_drill"  # the app's key under resources.apps in databricks.yml
DEFAULT_APP_NAME = "daily-drill"
DEFAULT_PROJECT = "daily-drill"
CRASHED = {"CRASHED", "UNAVAILABLE"}  # app_status states where the app's own code isn't running


class CloudError(RuntimeError):
    """A step failed; the message says what to do."""


def overrides_path(target: str) -> Path:
    return PROJECT_ROOT / ".databricks" / "bundle" / target / "variable-overrides.json"


def read_overrides(target: str) -> dict:
    path = overrides_path(target)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def write_overrides(target: str, values: dict) -> Path:
    path = overrides_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**read_overrides(target), **values}, indent=2) + "\n", encoding="utf-8")
    return path


def profile_for(target: str, given: str | None = None) -> str | None:
    """The CLI profile for a target: ``given``, else the one databricks.yml names for it."""
    if given:
        return given
    import yaml

    bundle = yaml.safe_load((PROJECT_ROOT / "databricks.yml").read_text(encoding="utf-8"))
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
    # Uploading and starting the app installs packages and can take many minutes; anything
    # else that hasn't answered in a few minutes is stuck, not slow.
    limit = 30 * 60 if args[:1] == ("bundle",) else 5 * 60
    try:
        done = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=limit)
    except FileNotFoundError:
        raise CloudError("The Databricks CLI isn't installed: see https://docs.databricks.com/dev-tools/cli/install (Mac: `brew install databricks/tap/databricks`, Windows: `winget install Databricks.DatabricksCLI`), then try again.") from None
    except subprocess.TimeoutExpired:
        raise CloudError(f"`{' '.join(cmd)}` didn't finish in {limit // 60} minutes, so it was stopped.") from None
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


DEFAULT_EXPERIMENT = "/Shared/daily-drill"  # the deployed app's traces: shared, and apart from your own experiments


def experiment_id(path: str, profile: str | None, trace_schema: str | None = None) -> str:
    """The id of the MLflow experiment at ``path``, creating it if it is not there.

    With ``trace_schema`` (``catalog.schema``) a new experiment keeps its traces in Unity Catalog
    tables named after it, which a workspace storage firewall doesn't block. The link can only
    be made when the experiment is created.
    """
    found = cli("experiments", "get-by-name", path, "-o", "json", profile=profile, check=False)
    if isinstance(found, dict) and found.get("experiment"):
        return found["experiment"]["experiment_id"]
    if not trace_schema:
        return cli("experiments", "create-experiment", path, "-o", "json", profile=profile)["experiment_id"]
    import mlflow
    from mlflow.entities.trace_location import UnityCatalog

    catalog, _, schema = trace_schema.partition(".")
    prefix = "".join(ch if ch.isalnum() else "_" for ch in path.rsplit("/", 1)[-1])  # daily-drill -> daily_drill
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    return mlflow.set_experiment(path, trace_location=UnityCatalog(catalog, schema, table_prefix=prefix)).experiment_id


def me(profile: str | None) -> str:
    return cli("current-user", "me", "-o", "json", profile=profile)["userName"]


def default_warehouse(profile: str | None) -> str:
    """A serverless SQL warehouse to attach feedback with: the smallest, which stops itself when idle."""
    warehouses = cli("warehouses", "list", "-o", "json", profile=profile) or []
    serverless = [w for w in warehouses if w.get("enable_serverless_compute")]
    if not serverless:
        raise CloudError("No serverless SQL warehouse found. Create a 2X-Small one with a short auto-stop, then pass --warehouse.")
    sizes = ["2X-Small", "X-Small", "Small", "Medium", "Large", "X-Large", "2X-Large", "3X-Large", "4X-Large"]
    return min(serverless, key=lambda w: sizes.index(w.get("cluster_size")) if w.get("cluster_size") in sizes else 99)["id"]


def setup(target: str, profile: str | None, project: str, create_lakebase: bool, experiment: str | None,
          model: str | None, name: str | None, trace_schema: str | None = None, warehouse: str | None = None,
          prompt_schema: str | None = None) -> dict:
    """Find or create what the app needs in the workspace, and save the values for ``deploy``."""
    branch, database = ensure_lakebase(project, profile, create_lakebase)
    saved = read_overrides(target)
    path = experiment or saved.get("experiment_path") or DEFAULT_EXPERIMENT
    schema = trace_schema or saved.get("trace_schema")
    values = {"lakebase_branch": branch, "lakebase_database": database,
              "experiment_id": experiment_id(path, profile, schema), "experiment_path": path}
    if schema:
        values["trace_schema"] = schema
    values["warehouse_id"] = warehouse or saved.get("warehouse_id") or default_warehouse(profile)
    if prompt_schema:
        values["prompt_schema"] = prompt_schema
    if model:
        values["model"] = model
    if name:
        values["app_name"] = name
    write_overrides(target, values)
    return {**values, "experiment": path, "file": str(overrides_path(target).relative_to(PROJECT_ROOT))}


# -- deploy and run -------------------------------------------------------------

def requirements() -> Path:
    """Write requirements.txt from uv.lock: the exact versions the tests ran, plus this repo itself."""
    try:
        out = subprocess.run(
            ["uv", "export", "--no-dev", "--extra", "lakebase", "--no-hashes", "--no-emit-project",
             "--format", "requirements-txt", "--quiet"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
            check=True, timeout=5 * 60,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        detail = getattr(exc, "stderr", None) or exc
        raise CloudError(f"Couldn't write requirements.txt with `uv export`: {detail}") from None
    pins = [line for line in out.splitlines() if line and not line.startswith(("#", " "))]
    head = (
        "# What a Databricks App installs (it reads only this file). Generated from uv.lock, so the\n"
        "# app runs the exact versions the tests ran; regenerate with `uv run drill cloud requirements`.\n"
        "# The last line installs this repo itself, editable, so its lessons and skill folder are found.\n"
    )
    path = PROJECT_ROOT / "requirements.txt"
    path.write_text(head + "\n".join(pins) + "\n-e .\n", encoding="utf-8")
    return path


def stamp_version() -> str:
    """Write the commit to .drill-version, so the app's traces say which code they came from."""
    from drill.server.observe import app_version

    stamp = PROJECT_ROOT / ".drill-version"
    stamp.unlink(missing_ok=True)  # ask git, not last time's stamp
    version = app_version()
    stamp.write_text(version + "\n", encoding="utf-8")
    return version


def deploy(target: str, profile: str | None) -> dict:
    """Upload the code, attach the resources, and start the app (or restart it on the new code)."""
    missing = [k for k in ("lakebase_branch", "lakebase_database", "experiment_id") if k not in read_overrides(target)]
    if missing:
        raise CloudError(f"Run `uv run drill cloud setup --target {target}` first (missing {', '.join(missing)}).")
    version = stamp_version()
    try:
        registered = register_version(target, profile, version)
    except Exception as exc:  # noqa: BLE001 - a missing record must not stop a deploy
        registered = {"error": str(exc).splitlines()[0][:200]}
    cli("bundle", "deploy", profile=profile, target=target)
    still_billing = (f"The app may still be running, and billing. Check with `uv run drill cloud status --target {target}`; "
                     f"stop it with `uv run drill cloud stop --target {target}`.")
    try:
        cli("bundle", "run", APP_RESOURCE, profile=profile, target=target)
    except CloudError as exc:
        raise CloudError(f"{exc}\n\n{still_billing}") from None
    info = status(target, profile)
    if info["state"] == "NOT DEPLOYED":
        raise CloudError(f"The app started but couldn't be looked up afterwards. {still_billing}")
    # The idle stop runs inside the app's own code: if that code crashed, nothing will ever
    # stop the app, so stop it now rather than let it bill until someone notices.
    if info.get("app_state") in CRASHED:
        stop(target, profile)
        raise CloudError(
            f"The app's code didn't start ({info['app_state']}), so it was stopped to save money. "
            f"See why with `databricks apps logs {info['name']}`."
        )
    if not info.get("service_principal"):
        raise CloudError(f"The app is running but couldn't be allowed to stop itself when idle. {still_billing}")
    allow_self_stop(info["name"], info["service_principal"], profile)
    return {**info, "version": version, "registered": registered}


def upstream_commit() -> str | None:
    """The public commit a work copy was built on: the first line of the ``UPSTREAM`` file at the
    project root (docs/PORTING.md, "Keeping the work copy current"), or ``None`` in the public repo."""
    path = PROJECT_ROOT / "UPSTREAM"
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return lines[0].strip()[:80] if lines else None


def register_version(target: str, profile: str | None, version: str) -> dict:
    """Record this version of the app in its experiment before it starts, so its traces link to it.

    One MLflow logged model per commit, ``daily-drill-<commit>``, with a description, the settings
    that shape its answers as parameters, and links to the prompt versions it uses. The app's
    ``set_active_model(name=...)`` finds it by name. The scorers are registered on the experiment too.
    """
    import mlflow
    from mlflow import MlflowClient

    from drill import mlflow_names, trace_scoring
    from drill.content import review
    from drill.review_eval import JUDGE_VERSION

    saved = read_overrides(target)
    experiment = saved["experiment_id"]
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    # Name the experiment outright: some MLflow calls fall back on MLFLOW_EXPERIMENT_NAME/_ID from the
    # environment, which other tools set (Claude Code's own tracing does), and would aim elsewhere.
    mlflow.set_experiment(experiment_id=experiment)
    name = f"daily-drill-{version}"
    prompts = {}
    if saved.get("prompt_schema"):
        for key in ("review", "challenge"):
            pv = mlflow.genai.load_prompt(f"prompts:/{saved['prompt_schema']}.{mlflow_names.PROMPTS[key]}@production",
                                          link_to_model=False)
            prompts[key] = pv
    params = {
        "model": saved.get("model", "system.ai.claude-haiku-4-5"), "target": target,
        "review_version": review.REVIEW_VERSION, "challenge_version": review.CHALLENGE_VERSION,
        "judge_version": JUDGE_VERSION, "lakebase_branch": saved.get("lakebase_branch", ""),
        **{f"prompt_{k}": f"{pv.name}/{pv.version}" for k, pv in prompts.items()},
    }
    tags = {**mlflow_names.context_tags(version), "environment": "app", "target": target,
            "mlflow.note.content": f"Daily Drill {version}: the page, the tutor and its reviews, deployed to "
                                   f"the {target} workspace. Answers come from {params['model']}."}
    upstream = upstream_commit()
    if upstream:  # a work copy: say which public commit this version is built on
        params["upstream"] = tags["upstream"] = upstream
    found = mlflow.search_logged_models(experiment_ids=[experiment], filter_string=f"name = '{name}'", output_format="list")
    model = found[0] if found else mlflow.create_external_model(
        name=name, experiment_id=experiment, model_type="agent", params=params, tags=tags)
    client = MlflowClient()
    for pv in prompts.values():
        client.link_prompt_version_to_model(pv.name, str(pv.version), model.model_id)
    try:
        scorers = trace_scoring.register(experiment)
    except ImportError:  # registering on Databricks needs databricks-agents (a dev dependency, not the app's)
        scorers = ["(not registered: run `uv sync` for databricks-agents)"]
    return {"model_id": model.model_id, "name": name, "new": not found, "prompts": [f"{pv.name}/{pv.version}" for pv in prompts.values()],
            "scorers": scorers}


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
        "app_state": app.get("app_status", {}).get("state", ""),  # whether the code itself is running
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


# -- the insights layer, the Genie Agent and the rebuilt dashboard ----------------------

INSIGHTS_STEPS = ("layer", "genie", "dashboard", "all")


def _statement_state(result: Any) -> str | None:
    """The state the CLI's query tool reports for a statement, wherever it puts it."""
    if isinstance(result, dict):
        status = result.get("status")
        if isinstance(status, dict) and status.get("state"):
            return str(status["state"])
        if result.get("state"):
            return str(result["state"])
    return None


SQL_STATEMENTS_API = "/api/2.0/sql/statements"


def run_sql(sql: str, warehouse: str, profile: str | None, poll_seconds: float = 5.0) -> Any:
    """One statement on the warehouse through the SQL statement API; fails loudly unless it succeeded.

    Not the CLI's query tool: on the command line it reads a leading ``-- comment`` as a flag, and from a
    file it did not carry the metric view's YAML through whole. The API takes the text as it is and answers
    with ``status.state``. The body goes in a file (``--json @file``) because the long views would not fit a
    Windows command line. A statement still running after the API's longest wait (the first one may be
    waking the warehouse) is polled until it finishes, for up to five minutes."""
    body = {"warehouse_id": warehouse, "statement": sql, "wait_timeout": "50s", "on_wait_timeout": "CONTINUE"}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "statement.json"
        path.write_text(json.dumps(body), encoding="utf-8")
        result = cli("api", "post", SQL_STATEMENTS_API, "--json", f"@{path}", profile=profile)
    for _ in range(60):
        if _statement_state(result) not in ("PENDING", "RUNNING") or not isinstance(result, dict) or not result.get("statement_id"):
            break
        time.sleep(poll_seconds)
        result = cli("api", "get", f"{SQL_STATEMENTS_API}/{result['statement_id']}", profile=profile)
    state = _statement_state(result)
    if state != "SUCCEEDED":
        head = next((line for line in sql.splitlines() if line.strip() and not line.strip().startswith("--")), sql)[:120]
        error = ((result.get("status") or {}).get("error") or {}).get("message", "") if isinstance(result, dict) else ""
        raise CloudError(f"This statement did not succeed ({state}): {head}\n{error or json.dumps(result)[:800]}")
    return result


def _missing_optional_tables(lakebase_catalog: str, profile: str | None) -> list[str]:
    """Which tables the layer can do without are not in the Lakebase catalog yet: the app makes them the
    first time a version that has them starts, and a view cannot be created over a table that is not there."""
    from drill.insights import layer

    listed = cli("tables", "list", lakebase_catalog, "drill", "-o", "json", profile=profile)
    if not isinstance(listed, list):
        raise CloudError(f"Couldn't list the tables of {lakebase_catalog}.drill: {str(listed)[:300]}")
    return layer.optional_tables_missing(t.get("name", "") for t in listed if isinstance(t, dict))


def _ensure_genie(insights_catalog: str, warehouse: str, profile: str | None, space_id: str | None) -> tuple[str, list[str]]:
    """Create the Genie Agent, or update it in place (its benchmarks travel inside serialized_space).

    The API rejects the whole payload on a key it does not know ("Unknown field"), and one key in the payload,
    ``sql_functions``, is a best guess (docs/INSIGHTS.md, step 1 says how to learn the real one). So on that
    error the key it names is dropped from the space and the call is made once more; the names dropped come
    back with the space id so the command can say what the agent was saved without."""
    from drill.insights import genie

    space = genie.serialized_space(insights_catalog)
    existing = cli("genie", "get-space", space_id, "-o", "json", profile=profile, check=False) if space_id else None
    update = isinstance(existing, dict) and bool(existing.get("space_id"))
    parent = None if update else f"/Workspace/Users/{me(profile)}"
    dropped: list[str] = []
    for attempt in (1, 2):
        try:
            if update:
                cli("genie", "update-space", space_id, "--json", json.dumps({"serialized_space": json.dumps(space)}), "-o", "json", profile=profile)
                return space_id, dropped
            body = genie.space_body(insights_catalog, warehouse, parent, space)
            return cli("genie", "create-space", "--json", json.dumps(body), "-o", "json", profile=profile)["space_id"], dropped
        except CloudError as exc:
            field = genie.unknown_field(str(exc)) if attempt == 1 else None
            if not field:
                note = f" (after dropping {', '.join(dropped)} and trying once more)" if dropped else ""
                raise CloudError(f"{exc}{note}") from None
            dropped.append(field)
            space = genie.without_field(space, field)
    raise AssertionError("unreachable")


def _publish_insights_dashboard(target: str, profile: str | None, warehouse: str, insights_catalog: str, space_id: str | None) -> dict:
    """Rebuild the managers' dashboard in place (same id, same link) on the insights layer and republish it.
    With no ``space_id`` the board goes out with Ask Genie off."""
    from drill.insights import dashboard as board

    values = read_overrides(target)
    body = {"display_name": board.DASHBOARD_NAME, "warehouse_id": warehouse,
            "serialized_dashboard": json.dumps(board.dashboard(insights_catalog, space_id))}
    dashboard_id = values.get("manager_dashboard_id")
    existing = cli("lakeview", "get", dashboard_id, "-o", "json", profile=profile, check=False) if dashboard_id else None
    if isinstance(existing, dict) and existing.get("lifecycle_state") != "TRASHED":
        cli("lakeview", "update", dashboard_id, "--json", json.dumps(body), "-o", "json", profile=profile)
    else:
        body["parent_path"] = f"/Users/{me(profile)}"
        dashboard_id = cli("lakeview", "create", "--json", json.dumps(body), "-o", "json", profile=profile)["dashboard_id"]
    cli("lakeview", "publish", dashboard_id, "--embed-credentials", "--warehouse-id", warehouse, "-o", "json", profile=profile)
    host = cli("auth", "describe", "-o", "json", profile=profile, check=False)
    host = (host or {}).get("details", {}).get("host", "") if isinstance(host, dict) else ""
    return {"dashboard_id": dashboard_id, "genie_space_id": space_id,
            "url": f"{host.rstrip('/')}/dashboardsv3/{dashboard_id}/published" if host else dashboard_id}


def insights(target: str, profile: str | None, warehouse: str | None = None, lakebase_catalog: str | None = None,
             insights_catalog: str | None = None, managers: str | None = None, dry_run: bool = False, step: str = "all") -> dict:
    """Build the insights layer (``layer``), the Genie Agent (``genie``) and the rebuilt dashboard (``dashboard``),
    or ``all`` of them in that order. ``dry_run`` returns every SQL statement and both JSON documents and runs
    nothing. Catalog, warehouse, group and ids come from the overrides file and go back there.

    With ``all``, a Genie step that fails does not stop the dashboard: republishing it is what closes the open
    Ask Genie on today's board, so it goes out with Genie off and the result carries ``genie.error`` (the command
    then exits with an error) instead of raising straight away."""
    from drill.insights import dashboard as board, genie, layer

    if step not in INSIGHTS_STEPS:
        raise CloudError(f"--step must be one of {', '.join(INSIGHTS_STEPS)}.")
    values = read_overrides(target)
    lakebase_catalog = lakebase_catalog or values.get("lakebase_catalog") or DEFAULT_CATALOG
    insights_catalog = insights_catalog or values.get("insights_catalog")
    managers = managers or values.get("managers_group")
    warehouse = warehouse or values.get("warehouse_id")
    space_id = values.get("insights_genie_id")
    if dry_run:
        catalog = insights_catalog or "INSIGHTS_CATALOG"
        return {"dry_run": True, "lakebase_catalog": lakebase_catalog, "insights_catalog": catalog, "managers_group": managers,
                "genie_space_id": space_id, "statements": layer.statements(lakebase_catalog, catalog, managers),
                "genie": genie.serialized_space(catalog), "dashboard": board.dashboard(catalog, space_id)}
    if not insights_catalog:
        raise CloudError("Pass --insights-catalog <catalog>: a standard Unity Catalog catalog you own for the drill_insights "
                         "schema, not the Lakebase one (it is read-only). docs/INSIGHTS.md says how to choose it.")
    if not warehouse:
        raise CloudError("Pass --warehouse <id>: a small serverless SQL warehouse (Lakebase catalogs need serverless).")
    done: dict[str, Any] = {"insights_catalog": insights_catalog, "lakebase_catalog": lakebase_catalog, "step": step}
    if step in ("layer", "all"):
        ensure_catalog(target, profile, lakebase_catalog)
        missing = _missing_optional_tables(lakebase_catalog, profile)
        statements = layer.statements(lakebase_catalog, insights_catalog, managers, missing)
        for sql in statements:
            run_sql(sql, warehouse, profile)
        done["layer"] = {"objects": layer.object_names(), "statements": len(statements), "granted_to": managers,
                         "without_tables": missing}
    if step in ("genie", "all"):
        try:
            space_id, dropped = _ensure_genie(insights_catalog, warehouse, profile, space_id)
            done["genie"] = {"space_id": space_id, "benchmarks": len(genie.BENCHMARKS), "dropped_fields": dropped}
        except CloudError as exc:
            if step != "all":
                raise
            done["genie"] = {"error": str(exc)}
            space_id = None  # the dashboard still goes out, with Ask Genie off
    if step in ("dashboard", "all"):
        done["dashboard"] = _publish_insights_dashboard(target, profile, warehouse, insights_catalog, space_id)
    saved = {"lakebase_catalog": lakebase_catalog, "insights_catalog": insights_catalog, "warehouse_id": warehouse}
    if managers:
        saved["managers_group"] = managers
    if space_id:
        saved["insights_genie_id"] = space_id
    if done.get("dashboard"):
        saved["manager_dashboard_id"] = done["dashboard"]["dashboard_id"]
    write_overrides(target, saved)
    return done
