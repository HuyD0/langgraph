"""`drill cloud check` must catch every missing permission, as in a locked-down work workspace."""

from __future__ import annotations

import json

import pytest

from drill import cloud, cloud_check

SP = "sp-1111"
MODEL = "ai.models.haiku"
TRACE_TAGS = [
    {"key": "mlflow.experiment.databricksTraceDestinationPath", "value": "main.traces.drill"},
    {"key": "mlflow.experiment.databricksTraceSpanStorageTable", "value": "main.traces.drill_otel_spans"},
    {"key": "mlflow.experiment.databricksTraceLogStorageTable", "value": "main.traces.drill_otel_logs"},
    {"key": "mlflow.experiment.databricksTraceAnnotationStorageTable", "value": "main.traces.drill_otel_annotations"},
]


class FakeWorkspace:
    """Answers the CLI calls the check makes, from a table of who holds what."""

    def __init__(self, grants: dict, app_acl: list[str], experiment_acl: dict, roles: bool = True, warehouse_acl: dict | None = None):
        self.grants, self.app_acl, self.experiment_acl, self.roles = grants, app_acl, experiment_acl, roles
        self.warehouse_acl = warehouse_acl if warehouse_acl is not None else {SP: "CAN_USE", "me@example.com": "CAN_MANAGE"}
        self.patched: list[tuple] = []

    def __call__(self, *args, profile=None, check=True, target=None):
        a = list(args)
        if a[:2] == ["current-user", "me"]:
            return {"userName": "me@example.com"}
        if a[:2] == ["api", "get"] and "/model-services/" in a[2]:
            return {"name": f"model-services/{MODEL}"}
        if a[:2] == ["api", "get"] and "/effective-permissions/" in a[2]:
            path, principal = a[2].split("/effective-permissions/")[1].split("?principal=")
            privs = self.grants.get((path, principal), [])
            return {"privilege_assignments": [{"principal": principal, "privileges": [{"privilege": p} for p in privs]}]}
        if a[:2] == ["api", "patch"]:
            self.patched.append((a[2], json.loads(a[4])))
            return {}
        if a[:2] == ["postgres", "get-project"]:
            return {"name": a[2]}
        if a[:2] == ["postgres", "list-databases"]:
            return [{"name": "projects/drill/branches/production/databases/db"}]
        if a[:2] == ["postgres", "list-roles"]:
            return [{"status": {"postgres_role": SP}}] if self.roles else []
        if a[:2] == ["experiments", "get-experiment"]:
            return {"experiment": {"name": "/Shared/daily-drill", "tags": TRACE_TAGS}}
        if a[:2] == ["experiments", "get-permissions"]:
            return {"access_control_list": [{"service_principal_name": p, "user_name": p,
                                             "all_permissions": [{"permission_level": lvl}]}
                                            for p, lvl in self.experiment_acl.items()]}
        if a[:2] == ["warehouses", "get-permissions"]:
            return {"access_control_list": [{"service_principal_name": p, "user_name": p, "all_permissions": [{"permission_level": lvl}]}
                                            for p, lvl in self.warehouse_acl.items()]}
        if a[:2] == ["apps", "get-permissions"]:
            return {"access_control_list": [{"service_principal_name": SP, "all_permissions": [{"permission_level": lvl}]}
                                            for lvl in self.app_acl]}
        raise AssertionError(f"unexpected call {a}")


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.setattr(cloud, "PROJECT_ROOT", tmp_path)
    cloud.write_overrides("work", {"lakebase_branch": "projects/drill/branches/production",
                                   "lakebase_database": "projects/drill/branches/production/databases/db",
                                   "experiment_id": "42", "model": MODEL, "warehouse_id": "wh1",
                                   "prompt_schema": "main.daily_drill"})
    monkeypatch.setattr(cloud_check, "model_name", lambda target: MODEL)


def deployed(monkeypatch):
    monkeypatch.setattr(cloud, "status", lambda t, p: {"name": "daily-drill", "state": "ACTIVE", "url": "", "service_principal": SP})


def run(fake):
    found = cloud_check.check("work", "work", cli=fake, live=False)
    return {f.need: f for f in found}


def test_a_fully_granted_app_passes(work, monkeypatch):
    deployed(monkeypatch)
    everything = {(k, SP): v for k, v in {
        "catalog/ai": ["USE_CATALOG"], "schema/ai.models": ["USE_SCHEMA"], f"model_service/{MODEL}": ["EXECUTE"],
        "catalog/main": ["USE_CATALOG"], "schema/main.traces": ["USE_SCHEMA"],
        "table/main.traces.drill_otel_spans": ["SELECT", "MODIFY"], "table/main.traces.drill_otel_logs": ["ALL_PRIVILEGES"],
        "table/main.traces.drill_otel_annotations": ["SELECT", "MODIFY"], "schema/main.daily_drill": ["USE_SCHEMA", "EXECUTE"],
    }.items()}
    everything[("schema/main.daily_drill", "me@example.com")] = ["ALL_PRIVILEGES"]
    found = run(FakeWorkspace(everything, ["CAN_MANAGE"], {SP: "CAN_EDIT"}))
    assert all(f.ok for f in found.values()), [n for n, f in found.items() if not f.ok]


def test_a_locked_down_workspace_shows_each_gap_with_its_fix(work, monkeypatch):
    deployed(monkeypatch)
    some = {("catalog/ai", SP): ["USE_CATALOG"], ("schema/ai.models", SP): ["USE_SCHEMA"],
            ("catalog/main", SP): ["USE_CATALOG"], ("schema/main.traces", SP): ["USE_SCHEMA"],
            ("table/main.traces.drill_otel_spans", SP): ["SELECT"],
            ("schema/main.daily_drill", "me@example.com"): ["USE_SCHEMA", "EXECUTE"]}
    fake = FakeWorkspace(some, [], {}, roles=False, warehouse_acl={})
    found = run(fake)
    bad = {n for n, f in found.items() if f.ok is False}
    assert bad == {
        f"the app: EXECUTE on {MODEL}",
        "the app: a Postgres role on the branch",
        "the app: CAN_EDIT on the experiment",
        "the app: SELECT, MODIFY on main.traces.drill_otel_spans",
        "the app: SELECT, MODIFY on main.traces.drill_otel_logs",
        "the app: SELECT, MODIFY on main.traces.drill_otel_annotations",
        "the app: CAN_USE on warehouse wh1",
        "the app: USE_SCHEMA, EXECUTE on main.daily_drill",
        "the app: CAN_MANAGE on itself (to stop when idle)",
        "you: USE_SCHEMA, CREATE_FUNCTION, CREATE_TABLE, EXECUTE on main.daily_drill (to register prompts and the eval set)",
    }
    assert found["the app: SELECT, MODIFY on main.traces.drill_otel_spans"].detail == "missing MODIFY"
    assert "permissions/model_service/" + MODEL in found[f"the app: EXECUTE on {MODEL}"].fix


def test_fix_grants_only_what_is_missing(work, monkeypatch):
    deployed(monkeypatch)
    fake = FakeWorkspace({("table/main.traces.drill_otel_spans", SP): ["SELECT"]}, ["CAN_MANAGE"], {SP: "CAN_EDIT"})
    found = cloud_check.check("work", "work", cli=fake, live=False)
    cloud_check.fix([f for f in found if f.grant and f.grant[0] == "table"], "work", cli=fake)
    spans = [body for url, body in fake.patched if url.endswith("drill_otel_spans")]
    assert spans == [{"changes": [{"principal": SP, "add": ["MODIFY"]}]}]


def test_before_the_first_deploy_it_checks_what_you_can_hand_on(work, monkeypatch):
    monkeypatch.setattr(cloud, "status", lambda t, p: {"name": "daily-drill", "state": "NOT DEPLOYED", "url": ""})
    me = "me@example.com"
    # Account users may use the model; you manage the trace schema but not the tables; you own the experiment.
    grants = {("catalog/ai", "account users"): ["USE_CATALOG"], ("schema/ai.models", "account users"): ["USE_SCHEMA"],
              (f"model_service/{MODEL}", "account users"): ["EXECUTE"],
              ("catalog/main", me): ["MANAGE"], ("schema/main.traces", me): ["MANAGE"]}
    found = run(FakeWorkspace(grants, [], {me: "CAN_MANAGE"}))
    assert found["deployed"].ok is None
    assert found[f"the deploy can grant: EXECUTE on {MODEL}"].ok
    assert found["you: CAN_MANAGE on the experiment"].ok
    assert found["you: MANAGE on main.traces.drill_otel_spans"].ok is False


def test_the_users_group_counts_for_workspace_permissions():
    acl = {"access_control_list": [{"group_name": "users", "all_permissions": [{"permission_level": "CAN_USE"}]},
                                   {"group_name": "admins", "all_permissions": [{"permission_level": "CAN_MANAGE"}]}]}
    assert cloud_check.acl_levels(acl, SP) == {"CAN_USE"}  # every service principal is in "users", not in "admins"
