"""Reading and writing the experiment's tables: Unity Catalog on Databricks, CSV files in .local/ on a laptop.

On a laptop (no Spark), every table is .local/<name>.csv, so the whole job can be tried with a cheap judge before
anything runs in the workspace: see README.md, "Try it on your laptop".
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

LOCAL = Path(__file__).resolve().parents[1] / ".local"


def _dbutils():
    """Databricks' dbutils, when this runs as a notebook in a workspace; None on a laptop. (The SDK offers a stand-in
    dbutils on a laptop too, so the runtime's own variable decides.)"""
    import os

    if "DATABRICKS_RUNTIME_VERSION" not in os.environ:
        return None
    try:
        from databricks.sdk.runtime import dbutils

        dbutils.widgets  # noqa: B018 - fails outside a notebook
        return dbutils
    except Exception:  # noqa: BLE001
        return None


def args(*extra: tuple[str, dict]) -> argparse.Namespace:
    """The step's settings: the job's notebook parameters in a workspace, command-line options on a laptop."""
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", default="")
    p.add_argument("--schema", default="")
    p.add_argument("--root", default="", help="The project folder (the job passes the bundle's files path)")
    p.add_argument("--experiment", default="", help="The MLflow experiment (a /Users/... or /Shared/... path on Databricks)")
    p.add_argument("--warehouse-id", default="", help="SQL warehouse for Unity Catalog trace storage (Databricks only)")
    p.add_argument("--project", default=Path(__file__).resolve().parents[1].name, help="The project's name, for tags")
    for name, kw in extra:
        p.add_argument(name, **kw)
    dbu = _dbutils()
    if dbu is None:
        return p.parse_args()
    argv = []
    for action in p._actions:
        for opt in action.option_strings:
            if opt.startswith("--"):
                try:
                    argv += [opt, dbu.widgets.get(opt[2:])]
                except Exception:  # noqa: BLE001 - a parameter the job didn't pass keeps its default
                    pass
    return p.parse_args(argv)


def say(markdown: str) -> None:
    """Show Markdown: rendered in a notebook, as plain text on a laptop."""
    if _dbutils() is None:
        print(markdown)
        return
    try:
        import markdown as md

        html = md.markdown(markdown, extensions=["tables"])
    except Exception:  # noqa: BLE001 - without the package, show it as written
        from html import escape

        html = f"<pre>{escape(markdown)}</pre>"
    from databricks.sdk.runtime import displayHTML

    displayHTML(f'<div style="font-family: system-ui, sans-serif; line-height: 1.5">{html}</div>')


def show(df: pd.DataFrame) -> None:
    """Show a table: an interactive table in a notebook, plain text on a laptop."""
    if _dbutils() is None:
        print(df.to_string(index=False))
        return
    from databricks.sdk.runtime import display

    display(df)


def link(path: str) -> str:
    """A link to an MLflow page (a path such as /ml/experiments/123): in this workspace, or in the local MLflow."""
    if _dbutils() is None:
        import mlflow

        uri = mlflow.get_tracking_uri()
        return uri.rstrip("/") + "/#" + path.replace("/ml/", "/", 1) if uri.startswith("http") else path
    try:
        from databricks.sdk import WorkspaceClient

        return WorkspaceClient().config.host.rstrip("/") + path
    except Exception:  # noqa: BLE001
        return path


def where(a: argparse.Namespace, table: str) -> str:
    """Where a table lives, for a reader: catalog.schema.table, or the CSV file on a laptop."""
    return name(a, table) if _spark() is not None and a.catalog else f".local/{table}.csv"


def root(a: argparse.Namespace) -> Path:
    """The project folder. A job passes it, because serverless runs a task's script without __file__ set; on a laptop
    it is found from this module's own place."""
    return Path(a.root) if a.root else Path(__file__).resolve().parents[1]


def experiment(a: argparse.Namespace):
    """Open the experiment, creating it the first time. On Databricks its traces go to Unity Catalog, as Delta tables in
    <catalog>.<schema>, which MLflow recommends over the experiment's own storage. That is set only when an experiment is
    created, so an existing experiment that stores traces elsewhere stops the run instead of silently using it."""
    import os

    import mlflow

    if not (a.catalog and _spark() is not None):  # a laptop: a local MLflow keeps its own storage
        return mlflow.set_experiment(a.experiment)
    from mlflow.entities.trace_location import UnityCatalog

    if a.warehouse_id:
        os.environ.setdefault("MLFLOW_TRACING_SQL_WAREHOUSE_ID", a.warehouse_id)
    found = mlflow.get_experiment_by_name(a.experiment)
    if found is None:
        eid = mlflow.create_experiment(name=a.experiment, trace_location=UnityCatalog(catalog_name=a.catalog, schema_name=a.schema))
        return mlflow.set_experiment(experiment_id=eid)
    where = getattr(found, "trace_location", None)
    if not isinstance(where, UnityCatalog) or (where.catalog_name, where.schema_name) != (a.catalog, a.schema):
        trash = " It is in the trash, which still holds the name until the trash is emptied." if found.lifecycle_stage == "deleted" else ""
        raise SystemExit(f"Experiment {a.experiment} stores its traces in {where or 'the experiment itself'}, not in "
                         f"{a.catalog}.{a.schema}.{trash} Trace storage can't be changed after creation: set the bundle "
                         "variable experiment_name to a new path.")
    return mlflow.set_experiment(experiment_id=found.experiment_id)


def _spark():
    try:
        from pyspark.sql import SparkSession

        return SparkSession.builder.getOrCreate()
    except Exception:  # noqa: BLE001 - no Spark: run locally
        return None


def name(a: argparse.Namespace, table: str) -> str:
    return f"{a.catalog}.{a.schema}.{table}"


def exists(a: argparse.Namespace, table: str) -> bool:
    spark = _spark()
    if spark is None:
        return (LOCAL / f"{table}.csv").exists()
    return spark.catalog.tableExists(name(a, table))


def read(a: argparse.Namespace, table: str) -> pd.DataFrame:
    spark = _spark()
    df = pd.read_csv(LOCAL / f"{table}.csv") if spark is None else spark.table(name(a, table)).toPandas()
    return df.astype(object).where(pd.notna(df), None)  # empty cells become None, not NaN, in every column


def write(a: argparse.Namespace, table: str, df: pd.DataFrame) -> None:
    spark = _spark()
    if spark is None:
        LOCAL.mkdir(exist_ok=True)
        df.to_csv(LOCAL / f"{table}.csv", index=False)
        return
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {a.catalog}.{a.schema}")
    clean = df.copy()
    for col in clean.columns:  # dicts and lists become JSON text, so Delta gets plain columns
        if clean[col].map(lambda v: isinstance(v, (dict, list))).any():
            clean[col] = clean[col].map(lambda v: json.dumps(v) if isinstance(v, (dict, list)) else v)
    spark.createDataFrame(clean).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(name(a, table))


def rows(df: pd.DataFrame) -> list[dict]:
    """Table rows as dicts, with expected_pass as True, False or None."""
    out = []
    for r in df.to_dict("records"):
        v = r.get("expected_pass")
        empty = v is None or (isinstance(v, float) and math.isnan(v)) or str(v).strip() == ""  # NaN or blank: nobody checked it
        r["expected_pass"] = None if empty else str(v).strip().lower() in ("true", "1", "1.0", "yes")
        out.append(r)
    return out
