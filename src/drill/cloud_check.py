"""Check that the Databricks App has every permission it needs, and say how to fix what is missing.

    uv run drill cloud check                 # personal workspace
    uv run drill cloud check --target work   # before and after the first deploy at work
    uv run drill cloud check --fix           # also grant what is missing, where you are allowed to

Before the first deploy it checks **you**: that you can sign in, that the model service,
Lakebase project and experiment exist, and that you hold the rights a deploy needs to hand
on to the app. After it, it checks **the app's service principal**, the identity the app
runs as, against each thing it touches:

| What | The service principal needs | Given by |
|---|---|---|
| The model (a Unity Gateway model service) | ``USE CATALOG``, ``USE SCHEMA``, ``EXECUTE`` | the app's ``model`` resource |
| Lakebase | a Postgres role on the branch | the app's ``postgres`` resource |
| The MLflow experiment | ``CAN_EDIT`` | the app's ``experiment`` resource |
| The trace tables in Unity Catalog | ``USE CATALOG``, ``USE SCHEMA``, ``SELECT`` and ``MODIFY`` on the span, log and annotation tables | nobody: grant it, or ``--fix`` |
| The SQL warehouse (to attach feedback to those traces) | ``CAN_USE`` | the app's ``sql-warehouse`` resource |
| The prompts schema (to link traces to prompt versions) | ``USE CATALOG``, ``USE SCHEMA``, ``EXECUTE`` | nobody: grant it, or ``--fix`` |
| Its own app (to stop itself when idle) | ``CAN_MANAGE`` | ``drill cloud deploy`` |

Rights are read as *effective* rights, so a grant to a group the principal is in (such as
"account users") counts. When the app is running, it also asks the app itself whether the
model, Lakebase and tracing all work.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from drill import cloud

Cli = Callable[..., Any]
ALL = "ALL_PRIVILEGES"


@dataclass
class Finding:
    area: str
    need: str
    ok: bool | None  # None: could not be checked yet (for example, the app is stopped)
    detail: str = ""
    fix: str = ""
    grant: tuple | None = None  # (securable type, full name, principal, privileges) that --fix can apply

    @property
    def mark(self) -> str:
        return {True: "✓", False: "✗", None: "–"}[self.ok]


def effective(cli: Cli, securable: str, name: str, principal: str, profile: str | None) -> set[str]:
    """The privileges ``principal`` holds on a Unity Catalog object, however they were granted."""
    got = cli("api", "get", f"/api/2.1/unity-catalog/effective-permissions/{securable}/{name}?principal={principal}",
              profile=profile, check=False)
    if not isinstance(got, dict):
        return set()
    return {p["privilege"] for a in got.get("privilege_assignments", []) for p in a.get("privileges", [])}


def has(privileges: set[str], *wanted: str) -> list[str]:
    """Which of ``wanted`` are missing; ALL_PRIVILEGES covers everything."""
    return [] if ALL in privileges else [w for w in wanted if w not in privileges]


def acl_levels(acl: Any, principal: str) -> set[str]:
    """Permission levels ``principal`` holds in a workspace ACL, directly or through the ``users`` group,
    which every user and service principal in a workspace belongs to."""
    levels: set[str] = set()
    for entry in (acl or {}).get("access_control_list", []) if isinstance(acl, dict) else []:
        if principal in (entry.get("service_principal_name"), entry.get("user_name"), entry.get("group_name")) \
                or entry.get("group_name") == "users":
            levels |= {p["permission_level"] for p in entry.get("all_permissions", [])}
    return levels


def grant_cmd(securable: str, name: str, principal: str, privileges: list[str]) -> str:
    changes = json.dumps({"changes": [{"principal": principal, "add": privileges}]})
    return f"databricks api patch /api/2.1/unity-catalog/permissions/{securable}/{name} --json '{changes}'"


def model_name(target: str) -> str:
    import yaml

    from drill.config import PROJECT_ROOT

    default = yaml.safe_load((PROJECT_ROOT / "databricks.yml").read_text())["variables"]["model"]["default"]
    return cloud.read_overrides(target).get("model", default)


def check(target: str, profile: str | None, cli: Cli = cloud.cli, live: bool = True) -> list[Finding]:
    found: list[Finding] = []
    add = found.append

    # -- you -------------------------------------------------------------------
    try:
        me = cli("current-user", "me", "-o", "json", profile=profile)["userName"]
        add(Finding("You", f"sign in ({profile or 'default profile'})", True, me))
    except Exception as exc:  # noqa: BLE001
        add(Finding("You", f"sign in ({profile or 'default profile'})", False, str(exc).splitlines()[-1],
                    f"databricks auth login --host https://adb-<id>.azuredatabricks.net --profile {profile}"))
        return found
    settings = cloud.read_overrides(target)
    missing = [k for k in ("lakebase_branch", "lakebase_database", "experiment_id") if k not in settings]
    add(Finding("You", "deploy settings saved", not missing, ", ".join(missing) and f"missing {', '.join(missing)}",
                f"uv run drill cloud setup --target {target}"))

    app = cloud.status(target, profile)
    deployed = app["state"] != "NOT DEPLOYED" and bool(app.get("service_principal"))
    sp = app.get("service_principal", "")
    who = sp if deployed else me
    whom = "the app" if deployed else "you"
    add(Finding("App", "deployed", True if deployed else None, f"{app['name']}: {app['state']}",
                "" if deployed else f"uv run drill cloud deploy --target {target}"))

    # -- the model service -------------------------------------------------------
    model = model_name(target)
    catalog, schema, _ = (model.split(".") + ["", "", ""])[:3]
    exists = isinstance(cli("api", "get", f"/api/2.1/unity-catalog/model-services/{model}", profile=profile, check=False), dict)
    add(Finding("Model", f"model service {model} exists", exists, "" if exists else "not found, or you cannot see it",
                "Ask your platform team for the three-part name, then: drill cloud setup --model <catalog.schema.name>"))
    if exists:
        need = [("catalog", catalog, ["USE_CATALOG"]), ("schema", f"{catalog}.{schema}", ["USE_SCHEMA"]),
                ("model_service", model, ["EXECUTE"])]
        for securable, name, privileges in need:
            privs = effective(cli, securable, name, who, profile)
            if deployed:
                gap = has(privs, *privileges)
            elif not has(privs, "MANAGE") or not has(effective(cli, securable, name, "account users", profile), *privileges):
                gap = []  # the deploy can grant it: you hold MANAGE, or every account user has it already
            else:
                gap = privileges
            add(Finding("Model", f"{whom if deployed else 'the deploy can grant'}: {', '.join(privileges)} on {name}", not gap,
                        f"missing {', '.join(gap)}" if gap else "",
                        grant_cmd(securable, name, who, gap) if deployed else "Ask for these on the model service, or MANAGE so the deploy can grant them to the app",
                        (securable, name, who, gap) if deployed and gap else None))

    # -- Lakebase ----------------------------------------------------------------
    branch = settings.get("lakebase_branch", "")
    if branch:
        project = "/".join(branch.split("/")[:2])
        ok = isinstance(cli("postgres", "get-project", project, "-o", "json", profile=profile, check=False), dict)
        add(Finding("Lakebase", f"project {project.split('/')[-1]} exists", ok, "",
                    f"uv run drill cloud setup --target {target} --create-lakebase"))
        databases = cli("postgres", "list-databases", branch, "-o", "json", profile=profile, check=False) if ok else []
        names = {d.get("name") for d in databases or [] if isinstance(d, dict)}
        add(Finding("Lakebase", "database exists", settings.get("lakebase_database") in names,
                    settings.get("lakebase_database", ""), f"uv run drill cloud setup --target {target}"))
        if deployed and ok:
            roles = cli("postgres", "list-roles", branch, "-o", "json", profile=profile, check=False) or []
            has_role = any(sp in json.dumps(r) for r in roles if isinstance(r, dict))
            add(Finding("Lakebase", "the app: a Postgres role on the branch", has_role, "",
                        f"uv run drill cloud deploy --target {target}  (the postgres resource creates it)"))

    # -- the experiment and its trace tables ---------------------------------------
    experiment_id = settings.get("experiment_id", "")
    if experiment_id:
        exp = cli("experiments", "get-experiment", experiment_id, "-o", "json", profile=profile, check=False)
        exp = exp.get("experiment") if isinstance(exp, dict) else None
        add(Finding("Traces", f"experiment {experiment_id} exists", bool(exp), (exp or {}).get("name", ""),
                    f"uv run drill cloud setup --target {target} --experiment <path>"))
        acl = cli("experiments", "get-permissions", experiment_id, "-o", "json", profile=profile, check=False)
        levels = acl_levels(acl, who)
        need_level = {"CAN_EDIT", "CAN_MANAGE"} if deployed else {"CAN_MANAGE"}
        add(Finding("Traces", f"{whom}: {'CAN_EDIT' if deployed else 'CAN_MANAGE'} on the experiment", bool(levels & need_level),
                    ", ".join(sorted(levels)) or "none", f"uv run drill cloud deploy --target {target}" if deployed
                    else "Ask the experiment's owner for CAN_MANAGE, or use an experiment you own"))
        tags = {t["key"]: t["value"] for t in (exp or {}).get("tags", [])}
        destination = tags.get("mlflow.experiment.databricksTraceDestinationPath", "")
        if destination:
            tcat, tschema = destination.split(".")[:2]
            tables = [tags[k] for k in ("mlflow.experiment.databricksTraceSpanStorageTable",
                                        "mlflow.experiment.databricksTraceLogStorageTable",
                                        "mlflow.experiment.databricksTraceAnnotationStorageTable") if k in tags]
            need = [("catalog", tcat, ["USE_CATALOG"]), ("schema", f"{tcat}.{tschema}", ["USE_SCHEMA"])]
            need += [("table", t, ["SELECT", "MODIFY"]) for t in tables]
            for securable, name, privileges in need:
                privs = effective(cli, securable, name, who, profile)
                gap = has(privs, *privileges) if deployed else has(privs, "MANAGE")
                label = f"{whom}: {', '.join(privileges) if deployed else 'MANAGE'} on {name}"
                add(Finding("Traces", label, not gap, f"missing {', '.join(gap)}" if gap else "",
                            grant_cmd(securable, name, who, gap) if deployed
                            else "Ask for MANAGE here (so you can grant the app), or have it granted to the app after deploy",
                            (securable, name, who, gap) if deployed and gap else None))

    # -- the SQL warehouse (feedback on traces kept in Unity Catalog) -----------------
    warehouse = settings.get("warehouse_id", "")
    if not warehouse:
        add(Finding("Traces", "a SQL warehouse for feedback", False, "none saved",
                    f"uv run drill cloud setup --target {target}  (or --warehouse <id>)"))
    else:
        levels = acl_levels(cli("warehouses", "get-permissions", warehouse, "-o", "json", profile=profile, check=False), who)
        ok = bool(levels & ({"CAN_USE", "CAN_MANAGE", "IS_OWNER"} if deployed else {"CAN_MANAGE", "IS_OWNER"}))
        add(Finding("Traces", f"{whom}: {'CAN_USE' if deployed else 'CAN_MANAGE'} on warehouse {warehouse}", ok,
                    ", ".join(sorted(levels)) or "none",
                    f"uv run drill cloud deploy --target {target}  (the sql-warehouse resource grants it)" if deployed
                    else "Ask the warehouse owner for CAN_MANAGE, or pick one you manage with --warehouse"))

    # -- the prompts the app links its traces to ----------------------------------------
    prompts = settings.get("prompt_schema", "")
    if prompts:
        # You register the prompts and the review cases (an evaluation dataset, a table) here.
        need = ["USE_SCHEMA", "CREATE_FUNCTION", "CREATE_TABLE", "EXECUTE"]
        gap = has(effective(cli, "schema", prompts, me, profile), *need)
        add(Finding("Prompts", f"you: {', '.join(need)} on {prompts} (to register prompts and the eval set)", not gap,
                    f"missing {', '.join(gap)}" if gap else "",
                    f"Ask for these on {prompts}, or use a schema you own: drill cloud setup --prompt-schema <catalog.schema>"))
    if prompts and deployed:
        pcat = prompts.split(".")[0]
        for securable, name, privileges in (("catalog", pcat, ["USE_CATALOG"]), ("schema", prompts, ["USE_SCHEMA", "EXECUTE"])):
            gap = has(effective(cli, securable, name, sp, profile), *privileges)
            add(Finding("Prompts", f"the app: {', '.join(privileges)} on {name}", not gap,
                        f"missing {', '.join(gap)}" if gap else "", grant_cmd(securable, name, sp, gap),
                        (securable, name, sp, gap) if gap else None))

    # -- stopping itself ------------------------------------------------------------
    if deployed:
        levels = acl_levels(cli("apps", "get-permissions", app["name"], "-o", "json", profile=profile, check=False), sp)
        add(Finding("App", "the app: CAN_MANAGE on itself (to stop when idle)", "CAN_MANAGE" in levels,
                    ", ".join(sorted(levels)) or "none", f"uv run drill cloud deploy --target {target}",
                    ("app", app["name"], sp, ["CAN_MANAGE"]) if "CAN_MANAGE" not in levels else None))

    # -- the running app, end to end -----------------------------------------------
    if live and deployed:
        found += live_checks(app, model, profile, cli)
    return found


def live_checks(app: dict, model: str, profile: str | None, cli: Cli) -> list[Finding]:
    """Ask the running app whether its model, Lakebase and tracing work, signed in as you."""
    if app["state"] != "ACTIVE":
        return [Finding("Live", "the app answers", None, f"{app['state']}: start it to check end to end",
                        "uv run drill cloud start")]
    import httpx

    token = cli("auth", "token", "-o", "json", profile=profile)["access_token"]
    try:
        health = httpx.get(app["url"].rstrip("/") + "/api/health", headers={"Authorization": f"Bearer {token}"},
                           timeout=30, follow_redirects=False).json()
    except Exception as exc:  # noqa: BLE001
        return [Finding("Live", "the app answers", False, str(exc), "databricks apps logs " + app["name"])]
    models = health.get("models", {})
    return [
        Finding("Live", "the app answers", True, app["url"]),
        Finding("Live", f"model is {model}", models.get("hosted") == model, str(models.get("hosted")),
                "Check DRILL_HOSTED_MODEL in app.yaml and the model resource"),
        Finding("Live", "progress saves to Lakebase", health.get("store") == "lakebase" and not health.get("store_fallback"),
                f"store={health.get('store')} fallback={health.get('store_fallback')}",
                "databricks apps logs " + app["name"] + "  (look for 'Lakebase is out of reach')"),
        Finding("Live", "tracing is on", bool(models.get("tracing")), "",
                "databricks apps logs " + app["name"] + "  (look for 'MLflow tracing is off')"),
    ]


def fix(findings: list[Finding], profile: str | None, cli: Cli = cloud.cli) -> list[str]:
    """Apply the grants the check found missing. Needs MANAGE (or CAN_MANAGE) on each object."""
    done: list[str] = []
    for f in findings:
        if not f.grant:
            continue
        securable, name, principal, privileges = f.grant
        if securable == "app":
            cloud.allow_self_stop(name, principal, profile)
        else:
            body = json.dumps({"changes": [{"principal": principal, "add": privileges}]})
            cli("api", "patch", f"/api/2.1/unity-catalog/permissions/{securable}/{name}", "--json", body, profile=profile)
        done.append(f"{', '.join(privileges)} on {name}")
    return done
