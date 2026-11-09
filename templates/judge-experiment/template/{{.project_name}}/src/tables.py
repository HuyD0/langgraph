"""Reading and writing the experiment's tables: Unity Catalog on Databricks, CSV files in .local/ on a laptop.

On a laptop (no Spark), every table is .local/<name>.csv, so the whole job can be tried with a cheap judge before
anything runs in the workspace: see README.md, "Try it on your laptop".
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

LOCAL = Path(__file__).resolve().parents[1] / ".local"


def args(*extra: tuple[str, dict]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", default="")
    p.add_argument("--schema", default="")
    for name, kw in extra:
        p.add_argument(name, **kw)
    return p.parse_args()


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
        empty = v is None or (isinstance(v, float) and v != v) or str(v).strip() == ""  # NaN or blank: nobody checked it
        r["expected_pass"] = None if empty else str(v).strip().lower() in ("true", "1", "1.0", "yes")
        out.append(r)
    return out
