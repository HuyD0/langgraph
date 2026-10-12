"""Every name the app gives MLflow, read from settings, so moving workspaces is a change of settings.

| Setting | Default | What it names |
|---|---|---|
| ``DRILL_MLFLOW_EXPERIMENT`` | ``daily-drill`` | your experiments and evals (on Databricks, ``/Users/<you>/daily-drill``) |
| ``DRILL_MLFLOW_EXPERIMENT_ID`` | *(unset)* | the deployed app's experiment, by id (the app's resource sets it) |
| ``DRILL_CLI_MLFLOW_EXPERIMENT`` | ``daily-drill-cli`` | the terminal tutor's practice runs (``drill start``) |
| ``DRILL_PROMPT_SCHEMA`` | *(unset)* | where prompts and evaluation datasets live, ``catalog.schema``; required on Databricks, where both are in Unity Catalog |
| ``DRILL_ENVIRONMENT`` | ``app`` in a Databricks App, else ``local`` | the ``environment`` tag on every trace and run |

Every trace and run is also tagged with ``app_version`` (the commit) and, in an app, the
``app_name`` and ``workspace_id`` the platform gives it, so traces from your personal
workspace and from work can never be mistaken for each other. Users and sessions use
MLflow's own fields (``mlflow.trace.user``, ``mlflow.trace.session``), and the page's id
for each request is the trace's ``client_request_id``.
"""

from __future__ import annotations

import os
import re

PROMPTS = {"review": "use_case_review", "challenge": "use_case_challenge",
           "hint": "drill_hint", "tutor_review": "drill_review", "explain": "drill_explain"}
_SCHEMA = re.compile(r"^[A-Za-z0-9_]+\.[A-Za-z0-9_]+$")


def environment() -> str:
    """``local`` on a laptop, ``app`` in a Databricks App, or whatever ``DRILL_ENVIRONMENT`` says."""
    return os.getenv("DRILL_ENVIRONMENT", "").strip() or ("app" if os.getenv("DATABRICKS_APP_NAME", "").strip() else "local")


def experiment() -> str:
    return os.getenv("DRILL_MLFLOW_EXPERIMENT", "").strip() or "daily-drill"


def cli_experiment() -> str:
    return os.getenv("DRILL_CLI_MLFLOW_EXPERIMENT", "").strip() or "daily-drill-cli"


def prompt_schema() -> str:
    schema = os.getenv("DRILL_PROMPT_SCHEMA", "").strip()
    if schema and not _SCHEMA.match(schema):
        raise ValueError(f"DRILL_PROMPT_SCHEMA must be catalog.schema, not {schema!r}")
    return schema


def prompt_name(key: str) -> str:
    """A prompt's registry name: ``catalog.schema.use_case_review`` on Databricks, ``use_case_review`` locally."""
    schema = prompt_schema()
    return f"{schema}.{PROMPTS[key]}" if schema else PROMPTS[key]


def dataset_name(short: str) -> str:
    """An evaluation dataset's name: a Unity Catalog table beside the prompts on Databricks, the short name locally."""
    schema = prompt_schema()
    return f"{schema}.{short}" if schema else short


def needs_prompt_schema(tracking_uri: str) -> bool:
    return tracking_uri.startswith("databricks") and not prompt_schema()


def context_tags(version: str) -> dict:
    """Tags for every trace and run: where it ran and which code ran it."""
    tags = {"environment": environment(), "app_version": version}
    for tag, env in (("app_name", "DATABRICKS_APP_NAME"), ("workspace_id", "DATABRICKS_WORKSPACE_ID")):
        if os.getenv(env, "").strip():
            tags[tag] = os.environ[env].strip()
    return tags


def context_metadata(version: str) -> dict:
    """MLflow's own source fields, so the trace UI links the commit (without the ``-dirty`` mark)."""
    commit = version.removesuffix("-dirty")
    return {"mlflow.source.git.commit": commit} if re.fullmatch(r"[0-9a-f]{7,40}", commit) else {}


def run_name(*parts: str) -> str:
    """Run names without spaces, so they filter cleanly: ``review-eval-review-v2``."""
    return "-".join(re.sub(r"[^A-Za-z0-9.]+", "-", p).strip("-").lower() for p in parts if p)
