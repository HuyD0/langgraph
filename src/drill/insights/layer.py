"""The semantic layer: the ordered SQL that creates ``<insights_catalog>.drill_insights``.

Each view, function and the metric view is one file in ``sql/`` so it can be reviewed on its own and
run by hand. The files use exactly two placeholders, ``{lakebase_catalog}`` and ``{insights_catalog}``;
``statements()`` fills them in and returns everything in dependency order, grants last.
"""

from __future__ import annotations

from collections.abc import Iterable
from importlib import resources

SCHEMA = "drill_insights"
PLACEHOLDERS = ("lakebase_catalog", "insights_catalog")

# Tables the app creates only once a version that has them starts (the leaderboard's `board` came after
# the first deploys). A view cannot be created while a table it reads is missing, so the layer builds
# without the table and says so; the next run of the layer step puts the real read back.
# table -> (what the view reads, what stands in for it while the table is missing)
OPTIONAL_TABLES: dict[str, tuple[str, str]] = {
    "board": ("FROM `{lakebase_catalog}`.drill.board bo\n  WHERE lower(bo.owner) LIKE '%@%'",
              "FROM (SELECT CAST(NULL AS STRING) AS owner) bo\n  WHERE FALSE  -- no board table yet, so nobody is on the leaderboard"),
}

# In dependency order: a view only reads views listed before it.
VIEW_ORDER = ("lessons", "progress_docs", "activity", "learner_lessons", "study_items", "learners", "lesson_summary", "weekly_notes")
FUNCTION_ORDER = ("retention_by_start_week", "who_is_stuck", "lessons_needing_work", "team_week")
METRIC_VIEW_NAME = "engagement_metrics"

# What Genie is given: the metric view plus these four views and the four functions. The rest are
# helpers (progress_docs), dashboard-only (study_items, weekly_notes) or carried by lesson_summary (lessons).
GENIE_VIEWS = ("learners", "learner_lessons", "lesson_summary", "activity")

SCHEMA_COMMENT = ("Daily Drill insights: commented views over the app data for the programme owner, managers, the dashboard "
                  "and the Genie agent. Shows every learner, so it is shared with the managers group only.")


def _read(filename: str) -> str:
    return resources.files("drill.insights.sql").joinpath(filename).read_text(encoding="utf-8").strip()


VIEWS: list[tuple[str, str]] = [(name, _read(f"{name}.sql")) for name in VIEW_ORDER]
FUNCTIONS: list[tuple[str, str]] = [(name, _read(f"{name}.sql")) for name in FUNCTION_ORDER]
METRIC_VIEW: tuple[str, str] = (METRIC_VIEW_NAME, _read(f"{METRIC_VIEW_NAME}.yaml"))


def fill(sql: str, lakebase_catalog: str, insights_catalog: str, missing_tables: Iterable[str] = ()) -> str:
    """Put the real catalog names into a statement (plain replacement, so braces elsewhere are safe),
    with a stand-in for each of ``missing_tables`` (see ``OPTIONAL_TABLES``)."""
    for table in missing_tables:
        if table not in OPTIONAL_TABLES:
            raise ValueError(f"The layer cannot build without {table}; it can only do without {', '.join(OPTIONAL_TABLES)}.")
        reads, stand_in = OPTIONAL_TABLES[table]
        sql = sql.replace(reads, stand_in)
    return sql.replace("{lakebase_catalog}", lakebase_catalog).replace("{insights_catalog}", insights_catalog)


def optional_tables_missing(existing: Iterable[str]) -> list[str]:
    """Which of the tables the layer can do without are not among ``existing`` (the Lakebase catalog's tables)."""
    have = set(existing)
    return [table for table in OPTIONAL_TABLES if table not in have]


def fqn(insights_catalog: str, name: str) -> str:
    """The full, backticked name of an object in the insights schema, for SQL."""
    return f"`{insights_catalog}`.{SCHEMA}.{name}"


def identifier(insights_catalog: str, name: str) -> str:
    """The full name without backticks, the way Genie identifiers are written."""
    return f"{insights_catalog}.{SCHEMA}.{name}"


def schema_statement(insights_catalog: str) -> str:
    return f"CREATE SCHEMA IF NOT EXISTS `{insights_catalog}`.{SCHEMA}\nCOMMENT '{SCHEMA_COMMENT}'"


def metric_view_statement(insights_catalog: str) -> str:
    """``CREATE OR REPLACE VIEW ... WITH METRICS LANGUAGE YAML AS $$...$$``, as the metric view docs show."""
    name, yaml_text = METRIC_VIEW
    return (f"CREATE OR REPLACE VIEW {fqn(insights_catalog, name)}\nWITH METRICS\nLANGUAGE YAML\nAS $$\n"
            f"{fill(yaml_text, '', insights_catalog)}\n$$")


def grant_statements(insights_catalog: str, managers_group: str | None) -> list[str]:
    """What the managers group gets: the insights schema only. Raw-catalog grants are never touched here
    (whether to revoke them is the owner's decision, see docs/INSIGHTS.md)."""
    if not managers_group:
        return []
    return [
        f"GRANT USE CATALOG ON CATALOG `{insights_catalog}` TO `{managers_group}`",
        f"GRANT USE SCHEMA, SELECT, EXECUTE ON SCHEMA `{insights_catalog}`.{SCHEMA} TO `{managers_group}`",
    ]


def statements(lakebase_catalog: str, insights_catalog: str, managers_group: str | None = None,
               missing_tables: Iterable[str] = ()) -> list[str]:
    """Every statement that builds the layer, in the order to run them: schema, views, functions,
    metric view, grants. ``drill cloud insights --dry-run`` prints them; ``missing_tables`` names the
    Lakebase tables that are not there yet (``OPTIONAL_TABLES``), which the views then do without."""
    missing = list(missing_tables)
    out = [schema_statement(insights_catalog)]
    out += [fill(sql, lakebase_catalog, insights_catalog, missing) for _, sql in VIEWS]
    out += [fill(sql, lakebase_catalog, insights_catalog, missing) for _, sql in FUNCTIONS]
    out.append(metric_view_statement(insights_catalog))
    out += grant_statements(insights_catalog, managers_group)
    return out


def object_names() -> list[str]:
    """Every object the layer creates, in creation order (schema first)."""
    return [SCHEMA, *VIEW_ORDER, *FUNCTION_ORDER, METRIC_VIEW_NAME]
