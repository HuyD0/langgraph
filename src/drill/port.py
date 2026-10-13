"""Move Daily Drill into a workspace in one go: ``uv run drill cloud port``.

    uv run drill cloud port --target work --catalog <team catalog> --model <catalog.schema.service>
    uv run drill cloud port --target work ... --apply --learner ana@corp.com --managers drill-managers

Without ``--apply`` nothing changes: it checks your tools, your sign-in, that the workspace has
Apps, serverless and Lakebase, and that every object the app needs exists, and prints a plan with
each step marked ready, to be created, or blocked (and why). With ``--apply`` it creates what is
missing (the trace and prompt schemas, a small serverless SQL warehouse, the Lakebase project, the
experiment), saves the settings, grants what the app needs, deploys, builds the managers'
dashboard and shares the app and the dashboard. Every step finds before it creates, so running it
again only fills gaps. It stops at the first blocked step, saying what to do.

What the workspace holds:

    <catalog>.drill_traces    the experiment's traces (Unity Catalog tables, firewall-friendly)
    <catalog>.daily_drill     prompts, scorers and the review cases
    Lakebase project          everyone's progress, study lists and activity
    a 2X-Small serverless SQL warehouse, stopping after 5 idle minutes
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from drill import cloud

READY, CREATE, BLOCKED, LATER = "ready", "create", "blocked", "later"
MIN_CLI = (1, 20)
TRACE_SCHEMA, PROMPT_SCHEMA = "drill_traces", "daily_drill"
WAREHOUSE = {"name": "daily-drill", "cluster_size": "2X-Small", "min_num_clusters": 1, "max_num_clusters": 1,
             "auto_stop_mins": 5, "enable_serverless_compute": True, "warehouse_type": "PRO"}


@dataclass
class Step:
    name: str
    state: str  # ready, create, blocked or later (happens during apply)
    detail: str = ""
    todo: str = ""  # what to do when blocked
    run: Callable[[], Any] | None = field(default=None, repr=False)

    @property
    def mark(self) -> str:
        return {READY: "✓", CREATE: "＋", BLOCKED: "✗", LATER: "→"}[self.state]


@dataclass
class Plan:
    target: str
    profile: str | None
    steps: list[Step] = field(default_factory=list)
    values: dict = field(default_factory=dict)  # what setup will save

    @property
    def blocked(self) -> list[Step]:
        return [s for s in self.steps if s.state == BLOCKED]


def _ok(result: Any) -> bool:
    return isinstance(result, (dict, list)) and bool(result) or result == []


def cli_version() -> tuple[int, ...]:
    try:
        out = subprocess.run(["databricks", "--version"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return ()
    found = re.search(r"v?(\d+)\.(\d+)", out)
    return tuple(int(x) for x in found.groups()) if found else ()


def plan(target: str, profile: str | None, *, catalog: str | None, model: str | None, project: str,
         experiment: str | None, warehouse: str | None, cli: Callable[..., Any] = cloud.cli) -> Plan:
    """Look at the workspace and work out every step; changes nothing."""
    p = Plan(target, profile)
    add = p.steps.append
    saved = cloud.read_overrides(target)

    version = cli_version()
    add(Step("Databricks CLI v1.20 or newer", READY if version >= MIN_CLI else BLOCKED,
             ".".join(map(str, version)) or "not found", "brew upgrade databricks (or see docs.databricks.com/dev-tools/cli)"))
    me = cli("current-user", "me", "-o", "json", profile=profile, check=False)
    if not isinstance(me, dict):
        add(Step(f"signed in with profile '{profile}'", BLOCKED, str(me or "")[-120:],
                 f"databricks auth login --host https://adb-<workspace-id>.azuredatabricks.net --profile {profile}"))
        return p
    add(Step(f"signed in with profile '{profile}'", READY, me.get("userName", "")))

    # -- the workspace has what the app runs on -------------------------------------
    apps = cli("apps", "list", "-o", "json", profile=profile, check=False)
    add(Step("Databricks Apps enabled", READY if _ok(apps) else BLOCKED, "" if _ok(apps) else str(apps)[-120:],
             "Turn on Databricks Apps for the workspace (account console → workspace → Previews/Features)."))
    projects = cli("postgres", "list-projects", "-o", "json", profile=profile, check=False)
    add(Step("Lakebase available", READY if _ok(projects) else BLOCKED, "" if _ok(projects) else str(projects)[-120:],
             "Lakebase Autoscaling must be available in the workspace's region and enabled."))

    # -- the model -------------------------------------------------------------------
    model = model or saved.get("model")
    if not model:
        add(Step("model service", BLOCKED, "none given", "Pass --model <catalog.schema.service>, a governed Unity Gateway model service."))
    else:
        found = cli("api", "get", f"/api/2.1/unity-catalog/model-services/{model}", profile=profile, check=False)
        add(Step(f"model service {model}", READY if isinstance(found, dict) else BLOCKED, "",
                 "Create the model service in Unity Gateway first, or pass the name of one that exists."))
        p.values["model"] = model

    # -- Unity Catalog: where traces and prompts live ---------------------------------
    trace_schema = saved.get("trace_schema") or (f"{catalog}.{TRACE_SCHEMA}" if catalog else None)
    prompt_schema = saved.get("prompt_schema") or (f"{catalog}.{PROMPT_SCHEMA}" if catalog else None)
    if not (trace_schema and prompt_schema):
        add(Step("trace and prompt schemas", BLOCKED, "no catalog given", "Pass --catalog <a catalog your team owns>."))
    else:
        for name in sorted({trace_schema.split(".")[0], prompt_schema.split(".")[0]}):
            found = cli("catalogs", "get", name, "-o", "json", profile=profile, check=False)
            add(Step(f"catalog {name}", READY if isinstance(found, dict) else BLOCKED, "",
                     f"Create catalog {name} (or pass --catalog with one that exists)."))
        for full in (trace_schema, prompt_schema):
            found = cli("schemas", "get", full, "-o", "json", profile=profile, check=False)
            cat, _, sch = full.partition(".")
            add(Step(f"schema {full}", READY if isinstance(found, dict) else CREATE, "",
                     run=lambda cat=cat, sch=sch: cli("schemas", "create", sch, cat, "-o", "json", profile=profile)))
        p.values.update(trace_schema=trace_schema, prompt_schema=prompt_schema)

    # -- a small serverless SQL warehouse ---------------------------------------------
    warehouse = warehouse or saved.get("warehouse_id")
    if warehouse:
        found = cli("warehouses", "get", warehouse, "-o", "json", profile=profile, check=False)
        good = isinstance(found, dict) and found.get("enable_serverless_compute")
        add(Step(f"SQL warehouse {warehouse} (serverless)", READY if good else BLOCKED, "",
                 "Pass a serverless warehouse with --warehouse, or leave it out to create one."))
        p.values["warehouse_id"] = warehouse
    else:
        listed = cli("warehouses", "list", "-o", "json", profile=profile, check=False) or []
        mine = next((w for w in listed if isinstance(w, dict) and w.get("name") == WAREHOUSE["name"]), None)
        if mine:
            add(Step(f"SQL warehouse '{WAREHOUSE['name']}'", READY, mine["id"]))
            p.values["warehouse_id"] = mine["id"]
        else:
            def make_warehouse():
                made = cli("warehouses", "create", "--json", json.dumps(WAREHOUSE), "-o", "json", profile=profile)
                p.values["warehouse_id"] = made["id"]
            add(Step(f"SQL warehouse '{WAREHOUSE['name']}' (2X-Small, serverless, stops after 5 idle minutes)", CREATE,
                     run=make_warehouse))

    # -- Lakebase project and the experiment --------------------------------------------
    found = cli("postgres", "get-project", f"projects/{project}", "-o", "json", profile=profile, check=False)
    add(Step(f"Lakebase project {project}", READY if isinstance(found, dict) else CREATE,
             "" if isinstance(found, dict) else "scales to zero after 5 idle minutes"))
    path = experiment or saved.get("experiment_path") or cloud.DEFAULT_EXPERIMENT
    folder = path.rsplit("/", 1)[0]
    found = cli("workspace", "get-status", folder, "-o", "json", profile=profile, check=False)
    add(Step(f"folder {folder}", READY if isinstance(found, dict) else CREATE, "",
             run=lambda: cli("workspace", "mkdirs", folder, profile=profile)))
    found = cli("experiments", "get-by-name", path, "-o", "json", profile=profile, check=False)
    add(Step(f"experiment {path}", READY if isinstance(found, dict) and found.get("experiment") else CREATE,
             "traces kept in Unity Catalog" if trace_schema else ""))
    p.values.update(project=project, experiment=path)

    # -- what happens on apply ----------------------------------------------------------
    for name in ("save settings (git-ignored)", "grant the app what it needs (drill cloud check --fix)",
                 "deploy the app", "managers' dashboard", "share the app and the dashboard"):
        add(Step(name, LATER))
    return p


def apply(p: Plan, *, learners: list[str], managers: str | None, deploy: bool = True,
          say: Callable[[str], None] = print, cli: Callable[..., Any] = cloud.cli) -> dict:
    """Carry the plan out. Stops at a blocked step; returns what was done."""
    if p.blocked:
        raise cloud.CloudError("Blocked: " + "; ".join(f"{s.name}: {s.todo}" for s in p.blocked))
    for step in p.steps:
        if step.state == CREATE and step.run:
            say(f"＋ {step.name}")
            step.run()
    v = p.values
    say("→ save settings")
    for attempt in range(18):  # a new Lakebase project needs a minute or two before its database exists
        try:
            cloud.setup(p.target, p.profile, v["project"], True, v["experiment"], v.get("model"), None,
                        v.get("trace_schema"), v.get("warehouse_id"), v.get("prompt_schema"))
            break
        except cloud.CloudError as exc:
            if "no database yet" not in str(exc) or attempt == 17:
                raise
            say("  waiting for the new Lakebase database...")
            time.sleep(10)
    from drill import cloud_check

    say("→ grant what you can before deploying")
    granted = cloud_check.fix(cloud_check.check(p.target, p.profile, live=False), p.profile)
    done: dict[str, Any] = {"granted": granted}
    if not deploy:
        return done
    say("→ deploy (installing packages takes a few minutes)")
    done["app"] = cloud.deploy(p.target, p.profile)
    findings = cloud_check.check(p.target, p.profile)
    done["granted"] += cloud_check.fix(findings, p.profile)
    done["missing"] = [f"{f.area}: {f.need}" for f in cloud_check.check(p.target, p.profile) if f.ok is False]
    say("→ managers' dashboard")
    done["dashboard"] = cloud.manager_view(p.target, p.profile)
    say("→ share")
    done["shared"] = share(p.target, p.profile, learners, managers, cli=cli)
    return done


def share(target: str, profile: str | None, learners: list[str], managers: str | None,
          cli: Callable[..., Any] = cloud.cli) -> list[str]:
    """Learners may use the app; a managers group may use it, read the dashboard and the catalog behind it."""
    name, saved, out = cloud.app_name(target), cloud.read_overrides(target), []
    acl = [{"user_name": e, "permission_level": "CAN_USE"} for e in learners]
    if managers:
        acl.append({"group_name": managers, "permission_level": "CAN_USE"})
    if acl:
        cli("apps", "update-permissions", name, "--json", json.dumps({"access_control_list": acl}), "-o", "json", profile=profile)
        out += [f"{a.get('user_name') or a.get('group_name')} can use {name}" for a in acl]
    if managers and saved.get("manager_dashboard_id"):
        body = {"access_control_list": [{"group_name": managers, "permission_level": "CAN_READ"}]}
        cli("api", "patch", f"/api/2.0/permissions/dashboards/{saved['manager_dashboard_id']}", "--json", json.dumps(body), profile=profile)
        out.append(f"{managers} can read the dashboard")
    if managers and saved.get("lakebase_catalog"):
        body = {"changes": [{"principal": managers, "add": ["USE_CATALOG", "USE_SCHEMA", "SELECT"]}]}
        cli("api", "patch", f"/api/2.1/unity-catalog/permissions/catalog/{saved['lakebase_catalog']}", "--json", json.dumps(body), profile=profile)
        out.append(f"{managers} can read catalog {saved['lakebase_catalog']}")
    return out
