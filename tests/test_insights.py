"""The insights layer, Genie Agent and rebuilt dashboard hang together, all offline.

The SQL reads only columns the raw tables have, names every raw table through the Lakebase catalog
placeholder, builds in dependency order, keeps private rows and words out, and never trusts the session
time zone. The dashboard binds fields that exist; the Genie space has the shape the API checks.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from drill import cloud
from drill.insights import dashboard, genie, layer

# The raw tables, from the verified data dictionary (drill.server.store).
RAW = {
    "docs": {"owner", "path", "body", "updated_at"},
    "events": {"id", "owner", "at", "kind", "lesson_id", "detail"},
    "lessons": {"id", "no", "position", "title", "phase", "module", "check_answer"},
    "board": {"owner", "name", "body", "updated_at"},
    "summaries": {"owner", "week", "made_at", "summary", "facts"},
}
EVENT_KINDS = {"step", "checked", "check_marks", "lesson_done", "solved", "practised", "explained", "focus_set", "asked",
               "off_topic", "feedback", "tests_run", "hint_used", "saved_to_study"}
# Only these feedback names may ever become a per-person signal; the rest belong to the private use case.
FEEDBACK_SHOWN = {"resolved", "saved", "asked_again", "gave_up", "next_right"}
PRIVATE_FEEDBACK = {"pilot_outcome", "useful", "made_something_up", "missed_a_risk", "too_vague", "decided_for_me",
                    "useful_question", "caught_a_risk", "changed_my_mind", "changed_rating_after", "edited_card_after"}

RAW_REF = re.compile(r"`\{lakebase_catalog\}`\.drill\.(\w+)\s+(?:AS\s+)?(\w+)")
INSIGHTS_REF = re.compile(r"`\{insights_catalog\}`\.drill_insights\.(\w+)")
PLACEHOLDER = re.compile(r"\{(\w+)\}")
ALL_SQL = [*layer.VIEWS, *layer.FUNCTIONS]


def test_every_raw_table_is_read_through_the_lakebase_catalog():
    for name, sql in ALL_SQL + [layer.METRIC_VIEW]:
        bare = re.findall(r"(?<!`\{lakebase_catalog\}`\.)\bdrill\.(\w+)", sql)
        assert not bare, f"{name} reads {bare} without the Lakebase catalog"
        for table, _alias in RAW_REF.findall(sql):
            assert table in RAW, f"{name} reads an unknown table drill.{table}"


def test_the_two_catalog_placeholders_are_the_only_ones():
    for name, sql in ALL_SQL + [layer.METRIC_VIEW]:
        found = set(PLACEHOLDER.findall(sql))
        assert found <= set(layer.PLACEHOLDERS), f"{name} has unexpected placeholders {found - set(layer.PLACEHOLDERS)}"
    filled = "\n".join(layer.statements("lake", "ins", "grp"))
    assert "{" not in filled and "}" not in filled


def test_views_use_only_columns_the_raw_tables_have():
    """Each raw table gets its own alias; every alias.column after it must be a real column."""
    for name, sql in ALL_SQL:
        refs = RAW_REF.findall(sql)
        aliases = [alias for _, alias in refs]
        assert len(aliases) == len(set(aliases)), f"{name} reuses a raw table alias"
        for table, alias in refs:
            used = set(re.findall(rf"\b{alias}\.`?(\w+)`?", sql))
            assert used <= RAW[table], f"{name}: drill.{table} as {alias} has no column(s) {used - RAW[table]}"
            assert used, f"{name} aliases drill.{table} as {alias} but never reads it"


def test_json_paths_and_event_kinds_match_the_data_dictionary():
    activity = dict(layer.VIEWS)["activity"]
    for kind in EVENT_KINDS:
        assert f"'{kind}'" in activity, f"activity does not name the event kind {kind}"
    progress = dict(layer.VIEWS)["progress_docs"]
    for path in ("$.current", "$.focus", "$.days", "$.lessons", "$.solved"):
        assert path in progress
    assert "$.mine" not in progress and "mine:" not in progress, "the use case is never read"
    assert "$.said" not in progress and "said:" not in progress, "the Explain sentence is never read"
    for col in ("step:int", "checked:int", "done:boolean", "marks:array<string>", "tried:array<array<int>>", "`right`:int", "total:int",
                "`first`:struct<`check`:array<string>,`date`:string>"):
        assert col in progress, f"progress_docs lesson schema lacks {col}"


def test_views_are_in_dependency_order_and_functions_read_only_views():
    for i, (name, sql) in enumerate(layer.VIEWS):
        earlier = {n for n, _ in layer.VIEWS[:i]}
        for ref in set(INSIGHTS_REF.findall(sql)) - {name}:  # the CREATE line names the view itself
            assert ref in earlier, f"view {name} reads {ref}, which is not defined before it"
    for name, sql in layer.FUNCTIONS:
        refs = set(INSIGHTS_REF.findall(sql)) - {name}
        assert refs and refs <= set(layer.VIEW_ORDER), f"function {name} reads {refs - set(layer.VIEW_ORDER)}"
    assert INSIGHTS_REF.findall(layer.METRIC_VIEW[1]) == ["activity"], "the metric view is sourced from activity alone"


def test_statements_come_in_order_and_end_with_the_grants():
    out = layer.statements("lake", "ins", "drill-managers")
    assert out[0].startswith("CREATE SCHEMA IF NOT EXISTS `ins`.drill_insights")
    views = out[1:1 + len(layer.VIEWS)]
    for (name, _), stmt in zip(layer.VIEWS, views):
        assert stmt.startswith(f"-- ") and f"CREATE OR REPLACE VIEW `ins`.drill_insights.{name} (" in stmt, name
    functions = out[1 + len(layer.VIEWS):1 + len(layer.VIEWS) + len(layer.FUNCTIONS)]
    for (name, _), stmt in zip(layer.FUNCTIONS, functions):
        assert f"CREATE OR REPLACE FUNCTION `ins`.drill_insights.{name}(" in stmt, name
    metric = out[-3]
    assert metric.startswith("CREATE OR REPLACE VIEW `ins`.drill_insights.engagement_metrics\nWITH METRICS\nLANGUAGE YAML\nAS $$")
    assert metric.rstrip().endswith("$$") and "source: '`ins`.drill_insights.activity'" in metric
    assert out[-2] == "GRANT USE CATALOG ON CATALOG `ins` TO `drill-managers`"
    assert out[-1] == "GRANT USE SCHEMA, SELECT, EXECUTE ON SCHEMA `ins`.drill_insights TO `drill-managers`"
    assert "lake" not in out[-1] and "lake" not in out[-2], "the raw catalog grants are never touched"
    assert not any(s.startswith("GRANT") for s in layer.statements("lake", "ins", None)), "no group, no grants"
    assert len(out) == 1 + len(layer.VIEWS) + len(layer.FUNCTIONS) + 1 + 2


def test_every_column_has_a_comment_in_plain_words():
    for name, sql in layer.VIEWS:
        head, body = sql.split("\nAS\n", 1)
        cols = re.findall(r"^\s+(\w+) COMMENT '", head, flags=re.M)
        assert cols, name
        final = body.rsplit("\nSELECT\n", 1)[-1].rsplit("\nFROM ", 1)[0]  # the outermost SELECT list
        for col in cols:
            assert re.search(rf"\bAS `?{col}`?(,|\s*$)|[.\s]`?{col}`?(,|\s*$)", final, flags=re.M), f"{name} comments on {col} but does not select it"
    for word in ("ISO", "cohort", "Extra lessons", "Work pack", "0.n", "No activity on record"):
        for name, sql in ALL_SQL + [layer.METRIC_VIEW]:
            comments = " ".join(re.findall(r"COMMENT '([^']*)'", sql)) + " ".join(re.findall(r"comment: '([^']*)'", sql))
            if word == "cohort":  # a Genie synonym is fine; page words are not
                comments = comments.replace("cohort", "")
            assert word not in comments, f"{name} says '{word}' in a comment"


def test_time_never_relies_on_the_session_time_zone():
    utc_day = "date_from_unix_date(CAST(floor("
    for name, sql in ALL_SQL:
        assert "current_date()" not in sql, f"{name} uses current_date(), which follows the session time zone"
        assert "to_date(timestamp_seconds" not in sql, name
    activity = dict(layer.VIEWS)["activity"]
    assert utc_day + "kept.at / 86400) AS INT)) AS activity_date" in activity
    assert "CAST(date_trunc('WEEK', dated.activity_date) AS DATE) AS activity_week" in activity
    for name in ("learner_lessons", "learners"):
        assert utc_day + "unix_seconds(current_timestamp()) / 86400) AS INT)) AS d" in dict(layer.VIEWS)[name], name
    for name in ("retention_by_start_week", "team_week"):
        assert "unix_seconds(current_timestamp())" in dict(layer.FUNCTIONS)[name], name
    for sql in dashboard.datasets("ins").values():
        assert "current_date()" not in sql
    assert "current_date()" not in json.dumps(genie.serialized_space("ins"))


def test_stuck_means_recent_and_not_moved_on_and_struggles_left_behind_are_counted_apart():
    ll = dict(layer.VIEWS)["learner_lessons"]
    assert "f.days_since <= 30 AND (f.is_current OR NOT f.moved_on)" in ll
    assert "ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING" in ll, "moved on = a later lesson finished after this one"
    assert "AS left_unfinished_after_struggling" in ll and "AS is_stuck" in ll and "AS is_stalled" in ll
    assert "s.days_since >= 7 AS stalled" in ll, "a NULL last activity is unknown, not stalled"
    assert "m.first_result.`check` IS NOT NULL AS has_first_check" in ll, "first.check wins; marks and tried only when it is missing"
    summary = dict(layer.VIEWS)["lesson_summary"]
    assert "try_divide(ll.learners_finished, ll.learners_finished + ll.learners_stalled) AS finish_rate" in summary
    work = dict(layer.FUNCTIONS)["lessons_needing_work"]
    assert "median(b.t_finish) OVER ()" in work and "WHERE r.lessons >= 10" in work and "> 0 AND t.t_finish > t.m_finish" in work
    assert "lessons_left_after_struggling" in dict(layer.VIEWS)["learners"]
    assert "learners_left_after_struggling" in summary


def test_private_rows_and_words_stay_out():
    activity = dict(layer.VIEWS)["activity"]
    for name in FEEDBACK_SHOWN:
        assert f"'{name}'" in activity
    for name in PRIVATE_FEEDBACK:
        assert f"'{name}'" not in activity, f"activity maps the private feedback name {name}"
    assert "LIKE 'use_case%'" in activity and "Own use case helper" not in activity
    assert "Use case" not in activity and "pilot" not in activity
    progress = dict(layer.VIEWS)["progress_docs"]
    assert "dx.path LIKE 'data/users/%/progress'\n  AND lower(dx.owner) LIKE '%@%'" in progress, "cheap prefix filter first"
    assert "dx.path LIKE 'study/%'\n    AND lower(dx.owner) LIKE '%@%'" in dict(layer.VIEWS)["study_items"]
    for name, sql in ALL_SQL:
        for table, alias in RAW_REF.findall(sql):
            if table in ("docs", "events", "board", "summaries"):
                assert f"lower({alias}.owner) LIKE '%@%'" in sql, f"{name} does not drop the app's own rows from drill.{table}"


# -- the dashboard ----------------------------------------------------------------------

# The widget reference's versions: counter 2, charts 3, combo 1, filters 2. Tables may be 1 (the shipped
# managers' dashboard, which works) or 2 (the reference's version, which the percent format needs).
VERSIONS = {"counter": {2}, "table": {1, 2}, "bar": {3}, "line": {3}, "pivot": {3}, "histogram": {3}, "combo": {1},
            "filter-multi-select": {2}, "filter-single-select": {2}, "filter-date-range-picker": {2}}
# The companion field the shipped dashboard's filter queries carry next to the field they bind.
ASSOCIATIVITY = "COUNT_IF(`associative_filter_predicate_group`)"


def _field_names(encodings) -> set[str]:
    found = set()
    if isinstance(encodings, dict):
        if "fieldName" in encodings:
            found.add(encodings["fieldName"])
        for v in encodings.values():
            found |= _field_names(v)
    elif isinstance(encodings, list):
        for v in encodings:
            found |= _field_names(v)
    return found


def _plain_fields(query: dict) -> set[str]:
    """The fields a filter query selects as themselves. Anything else must be a bound field's
    ``<field>_associativity`` companion with the shipped expression; the test fails on any other extra."""
    plain = {f["name"] for f in query["query"]["fields"] if f["expression"] == f"`{f['name']}`"}
    for f in query["query"]["fields"]:
        if f["name"] not in plain:
            assert f["name"].endswith("_associativity") and f["name"].removesuffix("_associativity") in plain, f
            assert f["expression"] == ASSOCIATIVITY, f
    return plain


def test_the_dashboard_hangs_together():
    """Every widget reads a dataset that exists, binds only columns that dataset's SQL names, and every encoded
    field is one the widget's query selects; every page says how it is laid out."""
    board = dashboard.dashboard("ins")
    sql = {d["name"]: d["queryLines"][0] for d in board["datasets"]}
    assert all("`ins`.drill_insights." in q for q in sql.values())
    assert not any(re.search(r"\bdrill\.(docs|events|lessons|board|summaries)\b", q) for q in sql.values()), "datasets never read the raw tables"
    for fn in layer.FUNCTION_ORDER:
        assert any(f"`ins`.drill_insights.{fn}(" in q for q in sql.values()), f"the dashboard calls {fn} by its full name"
    for page in board["pages"]:
        assert page["layoutVersion"] == "GRID_V1" and page["pageType"] in ("PAGE_TYPE_CANVAS", "PAGE_TYPE_GLOBAL_FILTERS")
        for item in page["layout"]:
            widget, pos = item["widget"], item["position"]
            assert pos["x"] + pos["width"] <= dashboard.W, f"{widget['name']} overflows the 12-column grid"
            spec = widget.get("spec")
            if spec:
                kind = spec["widgetType"]
                assert spec["version"] in VERSIONS[kind], f"{widget['name']} is {kind} v{spec['version']}"
                if kind == "counter":
                    assert pos["height"] >= 3
            for query in widget.get("queries", []):
                name = query["query"]["datasetName"]
                assert name in sql, f"{widget['name']} reads a missing dataset {name}"
                names = {f["name"] for f in query["query"]["fields"]}
                for field in query["query"]["fields"]:
                    for column in re.findall(r"`([a-z_0-9]+)`", field["expression"]):
                        if column != "associative_filter_predicate_group":  # the filters' companion, not a dataset column
                            assert re.search(rf"\b{column}\b", sql[name]), f"{name} has no column {column} ({widget['name']})"
                if spec and not spec["widgetType"].startswith("filter"):
                    encoded = _field_names(spec["encodings"])
                    assert encoded <= names, f"{widget['name']} encodes {encoded - names} that its query does not select"
                elif spec:  # a filter query selects the field it binds, plus at most the shipped board's companion
                    assert not query["query"]["disaggregated"]
                    bound = {e["fieldName"] for e in spec["encodings"]["fields"] if e["queryName"] == query["name"]}
                    assert bound <= names, f"{widget['name']} binds {bound} but its query {query['name']} selects {names}"
                    assert _plain_fields(query) == bound, f"{widget['name']} selects more than {bound} and its companion"
    assert [p["displayName"] for p in board["pages"]] == ["Filters", "How it's going", "Do they come back?", "How far they get",
                                                           "Where they're stuck", "Team", "Questions and the tutor", "Weekly notes"]
    assert board["uiSettings"]["theme"]["visualizationColors"] and board["uiSettings"]["genieSpace"] == {"isEnabled": False}
    linked = dashboard.dashboard("ins", "0123abcd")["uiSettings"]["genieSpace"]
    assert linked == {"isEnabled": True, "overrideId": "0123abcd", "enablementMode": "ENABLED"}


def _pickers(board: dict) -> list[dict]:
    return [item["widget"] for page in board["pages"] for item in page["layout"]
            if item["widget"].get("spec", {}).get("widgetType", "").startswith("filter")]


def test_the_shipped_dashboard_keeps_the_filter_shape_that_works():
    """The published managers' dashboard works with its filters as they are: every filter query selects the
    learner field and its associativity companion, and every table is version 1. A later edit to the shared
    helpers cannot change that shape without this test saying so."""
    from drill import manager_view

    board = manager_view.dashboard("cat_x")
    pickers = _pickers(board)
    assert pickers
    for widget in pickers:
        for query in widget["queries"]:
            assert query["query"]["fields"] == [
                {"name": "learner", "expression": "`learner`"},
                {"name": "learner_associativity", "expression": ASSOCIATIVITY}], widget["name"]
    tables = [item["widget"] for page in board["pages"] for item in page["layout"]
              if item["widget"].get("spec", {}).get("widgetType") == "table"]
    assert tables and all(t["spec"]["version"] == 1 for t in tables)
    # The switch the reference suggests if a filter errors: the plain field alone.
    plain = manager_view._learner_filter("f", ["ds_a"], associativity=False)
    assert plain["widget"]["queries"][0]["query"]["fields"] == [{"name": "learner", "expression": "`learner`"}]


def test_insights_filters_select_their_field_and_at_most_its_companion():
    """The new board's pickers use the shipped board's proven shape: the bound field plus its associativity
    companion (the date picker binds a different field per dataset). Nothing else rides along."""
    board = dashboard.dashboard("ins")
    pickers = _pickers(board)
    assert len(pickers) >= 4
    for widget in pickers:
        for query in widget["queries"]:
            bound = {e["fieldName"] for e in widget["spec"]["encodings"]["fields"] if e["queryName"] == query["name"]}
            assert len(bound) == 1 and _plain_fields(query) == bound, widget["name"]
            assert len(query["query"]["fields"]) <= 2, widget["name"]
    # Every table on the new pages is version 2, which the percent columns need.
    tables = [item["widget"] for page in board["pages"] for item in page["layout"]
              if item["widget"].get("spec", {}).get("widgetType") == "table"]
    assert tables and all(t["spec"]["version"] == 2 for t in tables)
    assert any(c.get("format", {}).get("type") == "number-percent" for t in tables for c in t["spec"]["encodings"]["columns"])


def test_categorical_axes_draw_in_the_order_the_course_uses():
    """Phases in course order, statuses from active to silent, steps in lesson order: never alphabetically."""
    widgets = {item["widget"]["name"]: item["widget"] for page in dashboard.pages() for item in page["layout"]}
    expected = {"b_phases": dashboard.PHASE_ORDER, "b_status": dashboard.STATUS_ORDER, "b_step": dashboard.STEP_ORDER}
    for name, order in expected.items():
        scale = widgets[name]["spec"]["encodings"]["x"]["scale"]
        assert scale == {"type": "categorical", "sort": {"by": "custom-order", "orderedValues": order}}, name
    assert dashboard.PHASE_ORDER == ["Frame", "Design", "Build and trace", "Evaluate", "Ship", "Monitor", "Platform track"]
    # The ordered values are the words the SQL writes, so a renamed status or step would show up here.
    learners_sql = dict(layer.VIEWS)["learners"]
    assert all(f"'{status}'" in learners_sql for status in dashboard.STATUS_ORDER)
    lessons_sql = dict(layer.VIEWS)["lessons"]
    assert all(phase in lessons_sql for phase in dashboard.PHASE_ORDER)
    tutor_sql = dashboard.datasets("ins")["ds_tutor"]
    assert "'Study list'" in tutor_sql and "'Not recorded'" in tutor_sql
    assert "Learn, Check, Build or Explain" in dict(layer.VIEWS)["activity"]
    # Other categorical bars (days, practising) have no fixed vocabulary, so they keep the default order.
    assert "sort" not in widgets["b_days7"]["spec"]["encodings"]["x"]["scale"]


def test_the_dashboard_speaks_plainly():
    text = json.dumps(dashboard.dashboard("ins"))
    for word in ("ISO", "cohort", "Extra lessons", "Work pack", "No activity on record", "Right on the first try"):
        assert word not in text, word
    assert text.count("UTC") == 1, "world time is explained once, then it is just day and week"
    assert "Started before tracking began" in "\n".join(s for _, s in layer.VIEWS)
    percent_columns = re.findall(r'"format": \{"type": "number-percent"', text)
    assert len(percent_columns) >= 8, "rate columns are shown as percentages"
    assert '"schedule"' not in text and '"subscription"' not in text


# -- the Genie Agent -------------------------------------------------------------------

HEX32 = re.compile(r"^[0-9a-f]{32}$")


def test_the_genie_space_has_the_shape_the_api_checks():
    space = genie.serialized_space("ins")
    assert set(space) == {"version", "config", "data_sources", "instructions", "benchmarks"} and space["version"] == 2
    tables = space["data_sources"]["tables"]
    assert [t["identifier"] for t in tables] == sorted(f"ins.drill_insights.{v}" for v in layer.GENIE_VIEWS)
    assert [m["identifier"] for m in space["data_sources"]["metric_views"]] == ["ins.drill_insights.engagement_metrics"]
    for t in tables + space["data_sources"]["metric_views"]:
        names = [c["column_name"] for c in t["column_configs"]]
        assert names == sorted(names)
        assert set(t) == {"identifier", "column_configs"}, "the reference allows nothing else on a data source entry"
    inst = space["instructions"]
    assert len(inst["text_instructions"]) == 1 and inst["text_instructions"][0]["content"][0].startswith("## PURPOSE")
    instruction = inst["text_instructions"][0]["content"][0]
    assert "## WHERE TO LOOK" in instruction
    for name in (*layer.GENIE_VIEWS, layer.METRIC_VIEW_NAME):  # the table descriptions live in the instruction instead
        assert f"- {name}: {genie.TABLE_DESCRIPTIONS[name]}" in instruction, name
    assert set(inst) == {"text_instructions", "example_question_sqls", "sql_functions", "join_specs", "sql_snippets"}
    assert {f["identifier"].rsplit(".", 1)[1] for f in inst["sql_functions"]} == set(layer.FUNCTION_ORDER)
    ids = []
    for key in ("example_question_sqls", "sql_functions", "join_specs", "text_instructions"):
        ids += [x["id"] for x in inst[key]]
        assert [x["id"] for x in inst[key]] == sorted(x["id"] for x in inst[key]), key
    for key in ("filters", "expressions", "measures"):
        ids += [x["id"] for x in inst["sql_snippets"][key]]
        for snippet in inst["sql_snippets"][key]:
            assert snippet["sql"] and all(s.strip() for s in snippet["sql"])
            if key != "expressions":  # filters and measures name columns; every one carries its table
                assert all(re.search(r"\b\w+\.`?\w", s) for s in snippet["sql"]), f"unqualified column in {snippet['display_name']}"
    questions = [q["id"] for q in space["config"]["sample_questions"]] + [b["id"] for b in space["benchmarks"]["questions"]]
    assert len(set(ids)) == len(ids) and len(set(questions)) == len(questions)
    assert all(HEX32.match(i) for i in ids + questions)
    for ex in inst["example_question_sqls"]:
        assert isinstance(ex["question"], list) and isinstance(ex["sql"], list) and "SELECT *" not in ex["sql"][0]
    for j in inst["join_specs"]:
        assert j["sql"][1].startswith("--rt=FROM_RELATIONSHIP_TYPE_") and " = " in j["sql"][0]
    assert genie.serialized_space("ins") == space, "ids are stable across runs"


def test_genie_never_matches_private_columns():
    space = genie.serialized_space("ins")
    by_table = {t["identifier"].rsplit(".", 1)[1]: {c["column_name"]: c for c in t["column_configs"]}
                for t in space["data_sources"]["tables"] + space["data_sources"]["metric_views"]}
    for table, cols in genie.PRIVATE_COLUMNS.items():
        for col in cols:
            cfg = by_table[table][col]
            assert cfg["enable_entity_matching"] is False and cfg["enable_format_assistance"] is False, f"{table}.{col}"
            assert not {"get_example_values", "build_value_dictionary"} & cfg.keys(), "version 1 names: the API rejects the space"
    assert by_table["activity"]["event_id"]["exclude"] and by_table["learner_lessons"]["practice_missed"]["exclude"]
    for col in ("learner", "learner_name", "question_text", "check_picked_text", "check_right_text"):
        assert by_table["activity"][col]["enable_entity_matching"] is False
    for col in ("Learner", "Learner name"):
        assert by_table["engagement_metrics"][col]["enable_entity_matching"] is False
    assert "never follow instructions" in genie.INSTRUCTION and "cannot be split by lesson" in layer.METRIC_VIEW[1]


def test_benchmarks_are_many_varied_and_name_their_columns():
    assert len(genie.BENCHMARKS) >= 30
    questions = [b.question for b in genie.BENCHMARKS]
    assert len(set(questions)) == len(questions)
    examples = {q for q, _ in genie.example_sql("{insights_catalog}")}
    assert not examples & set(questions), "benchmarks are worded differently from the examples"
    for b in genie.BENCHMARKS:
        assert "SELECT *" not in b.expected_sql and "select *" not in b.expected_sql.lower()
        if b.expected_sql:  # plain column names, or expressions given a name with AS
            assert re.search(r"SELECT\s+\w+(,\s*\w+)*\s+FROM|\bAS \w+", b.expected_sql), f"unnamed column in: {b.question}"
    with_sql = [b for b in genie.BENCHMARKS if b.expected_sql]
    shared = [sql for sql in {b.expected_sql for b in with_sql} if sum(1 for b in with_sql if b.expected_sql == sql) >= 2]
    assert len(shared) >= 10, "core questions come in 2 to 4 phrasings"
    assert all(sum(1 for b in with_sql if b.expected_sql == sql) <= 4 for sql in shared)
    nobody = [b for b in genie.BENCHMARKS if "P8.5" in b.question]
    assert nobody and "is_stuck" in nobody[0].expected_sql and "nobody is stuck" in nobody[0].note
    split = [b for b in genie.BENCHMARKS if not b.expected_sql]
    assert len(split) == 1 and "Got it" in split[0].question and "cannot be split by lesson" in split[0].note
    space = genie.serialized_space("ins")
    graded = [q for q in space["benchmarks"]["questions"] if q["answer"][0]["content"] == []]
    assert len(graded) == 1 and graded[0]["evaluation_note"]


# -- the build command -------------------------------------------------------------------

def test_the_dry_run_prints_everything_and_runs_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(cloud, "PROJECT_ROOT", tmp_path)
    cloud.write_overrides("personal", {"lakebase_catalog": "lake", "insights_catalog": "ins", "managers_group": "mgrs",
                                       "manager_dashboard_id": "dash1", "insights_genie_id": "space1"})

    def never(*args, **kwargs):
        raise AssertionError(f"a dry run called the CLI: {args}")

    monkeypatch.setattr(cloud, "cli", never)
    info = cloud.insights("personal", None, dry_run=True)
    assert info["dry_run"] and info["statements"] == layer.statements("lake", "ins", "mgrs")
    assert info["statements"][-1].startswith("GRANT USE SCHEMA, SELECT, EXECUTE")
    assert info["genie"] == genie.serialized_space("ins")
    assert info["dashboard"]["uiSettings"]["genieSpace"]["overrideId"] == "space1"
    assert cloud.read_overrides("personal")["insights_catalog"] == "ins", "a dry run writes nothing"


def test_the_layer_step_runs_each_statement_once_and_fails_loudly(monkeypatch, tmp_path):
    monkeypatch.setattr(cloud, "PROJECT_ROOT", tmp_path)
    cloud.write_overrides("personal", {"lakebase_catalog": "lake", "insights_catalog": "ins", "warehouse_id": "wh1",
                                       "lakebase_branch": "b", "lakebase_database": "d"})
    ran: list[str] = []

    def fake(*args, profile=None, target=None, check=True):
        if args[:2] == ("postgres", "get-catalog"):
            return {"catalog_id": "x"}
        if args[:2] == ("tables", "list"):
            assert args[2:4] == ("lake", "drill")
            return [{"name": n} for n in ("docs", "events", "lessons", "summaries")]  # an app from before the leaderboard: no board
        if args[:3] == ("api", "post", cloud.SQL_STATEMENTS_API):
            body = json.loads(Path(args[4][1:]).read_text(encoding="utf-8"))  # --json @file (see test_run_sql_...)
            assert body["warehouse_id"] == "wh1"
            sql = body["statement"]
            ran.append(sql)
            return {"status": {"state": "FAILED", "error": {"message": "boom"}}} if "team_week" in sql else {"status": {"state": "SUCCEEDED"}}
        raise AssertionError(args)

    monkeypatch.setattr(cloud, "cli", fake)
    with pytest.raises(cloud.CloudError, match="team_week"):
        cloud.insights("personal", None, step="layer")
    expected = layer.statements("lake", "ins", None, missing_tables=["board"])
    assert ran == expected[:expected.index(next(s for s in expected if "team_week(" in s)) + 1]
    assert not any("drill.board" in s for s in ran), "the board table is not there yet, so no view reads it"
    with pytest.raises(cloud.CloudError, match="--insights-catalog"):
        cloud.write_overrides("personal", {"insights_catalog": None})
        cloud.insights("personal", None, step="layer")


AGGREGATE_CALL = re.compile(r"\b(count|count_if|sum|min|max|avg|median|max_by|min_by|collect_set|collect_list|percentile\w*|measure)\s*\(", re.I)
CTE_START = re.compile(r"(?:^\s*|\),\s*|\bWITH\s+)(\w+) AS \(", re.M)  # `name AS (`, `WITH name AS (`, `), name AS (`


def _cte_bodies(sql: str):
    """Each named CTE's body, found by matching its brackets (comments and quoted text taken out first)."""
    text = re.sub(r"'(?:[^']|'')*'", "''", re.sub(r"--[^\n]*", "", sql))
    for m in CTE_START.finditer(text):
        depth, i = 1, m.end()
        while depth and i < len(text):
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        yield m.group(1), text[m.end():i - 1]


def test_no_cte_is_an_aggregate_with_no_group_by():
    """Over a Lakebase catalog, a CTE that aggregates with no GROUP BY comes back as every input row once a
    query stops reading its columns: the engine prunes the aggregate away (seen 2026-11-01, when
    SELECT COUNT(*) FROM learners answered with the number of lessons; a Delta table does not do this).
    Such a value goes in a scalar subquery or a window over the whole set (OVER ()), never in a joined relation."""
    from drill import manager_view

    old_board = [(d["name"], "".join(d["queryLines"])) for d in manager_view.dashboard("ins")["datasets"]]
    offenders = []
    for name, sql in [*layer.VIEWS, *layer.FUNCTIONS, *dashboard.datasets("ins").items(), *old_board]:
        for cte, body in _cte_bodies(sql):
            aggregates = len(AGGREGATE_CALL.findall(body))
            windows = len(re.findall(r"\)\s*OVER\s*\(", body, re.I))
            if aggregates and aggregates > windows and not re.search(r"\bGROUP BY\b", body, re.I):
                offenders.append(f"{name}.sql: {cte}")
    assert offenders == [], offenders
    # The scan sees through to real CTEs: the two it was written for would have been caught.
    assert dict(_cte_bodies(dict(layer.VIEWS)["learners"])).keys() >= {"today", "act", "prog", "done", "people", "base"}
    assert [c for c, _ in _cte_bodies("WITH sizes AS (\n  SELECT COUNT(*) AS n FROM t\n)\nSELECT 1")] == ["sizes"]
    assert [c for c, _ in _cte_bodies("WITH p AS (\n SELECT 1\n), path AS (SELECT COUNT(*) AS n FROM t)\nSELECT 1")] == ["p", "path"]


def test_the_layer_builds_without_a_table_the_app_has_not_made_yet():
    """The personal workspace's first build found no `board` table: that app was deployed before the leaderboard."""
    with_board = layer.statements("lake", "ins")
    without = layer.statements("lake", "ins", missing_tables=["board"])
    assert len(without) == len(with_board)
    assert any("`lake`.drill.board" in s for s in with_board) and not any("drill.board" in s for s in without)
    learners = next(s for s in without if ".learners (" in s)
    assert "WHERE FALSE" in learners and "on_leaderboard" in learners, "the column stays, false for everyone"
    assert layer.optional_tables_missing(["docs", "events"]) == ["board"] and layer.optional_tables_missing(["board"]) == []
    with pytest.raises(ValueError, match="events"):
        layer.statements("lake", "ins", missing_tables=["events"])
    # The text each stand-in replaces really is in a view, so a rewrite of the view cannot silently keep the read.
    for table, (reads, _) in layer.OPTIONAL_TABLES.items():
        assert any(reads in sql for _, sql in layer.VIEWS), table


def test_an_unknown_field_is_dropped_and_the_call_made_once_more():
    space = genie.serialized_space("ins")
    assert genie.unknown_field("Error: Invalid JSON in field 'serialized_space': Unknown field 'sql_functions'") == "sql_functions"
    assert genie.unknown_field("Unknown field \"instructions.sql_functions\" at line 1") == "sql_functions"
    assert genie.unknown_field("Unknown field: description") == "description"
    assert genie.unknown_field("some other error") is None
    slimmer = genie.without_field(space, "sql_functions")
    assert "sql_functions" not in slimmer["instructions"] and "sql_functions" in space["instructions"], "a copy, not in place"
    assert {k: v for k, v in slimmer["instructions"].items()} == {k: v for k, v in space["instructions"].items() if k != "sql_functions"}
    assert "sql_functions" not in json.dumps(slimmer)


def _genie_calls(monkeypatch, tmp_path, failures: list[str]):
    """Fake the CLI for the genie step: each entry in ``failures`` is the error the next create-space call raises."""
    monkeypatch.setattr(cloud, "PROJECT_ROOT", tmp_path)
    cloud.write_overrides("personal", {"lakebase_catalog": "lake", "insights_catalog": "ins", "warehouse_id": "wh1",
                                       "manager_dashboard_id": "dash1", "insights_genie_id": "old-space"})
    sent: list[tuple] = []

    def fake(*args, profile=None, target=None, check=True):
        sent.append(args)
        if args[:2] == ("genie", "get-space"):
            return None  # the saved id is gone, so the agent is created afresh
        if args[:2] == ("tables", "list"):
            return [{"name": n} for n in ("docs", "events", "lessons", "board", "summaries")]
        if args[:2] == ("current-user", "me"):
            return {"userName": "owner@example.com"}
        if args[:2] == ("genie", "create-space"):
            if failures:
                raise cloud.CloudError(failures.pop(0))
            return {"space_id": "new-space"}
        if args[:2] == ("lakeview", "get"):
            return {"lifecycle_state": "ACTIVE"}
        if args[:2] in (("lakeview", "update"), ("lakeview", "publish")):
            return {}
        if args[:2] == ("auth", "describe"):
            return {"details": {"host": "https://x"}}
        raise AssertionError(args)

    monkeypatch.setattr(cloud, "cli", fake)
    return sent


def test_the_genie_step_retries_once_without_the_field_the_api_rejects(monkeypatch, tmp_path):
    sent = _genie_calls(monkeypatch, tmp_path, ["`databricks genie create-space` failed:\nError: Unknown field 'sql_functions'"])
    info = cloud.insights("personal", None, step="genie")
    assert info["genie"] == {"space_id": "new-space", "benchmarks": len(genie.BENCHMARKS), "dropped_fields": ["sql_functions"]}
    creates = [json.loads(a[3]) for a in sent if a[:2] == ("genie", "create-space")]
    assert len(creates) == 2
    assert "sql_functions" in json.loads(creates[0]["serialized_space"])["instructions"]
    assert "sql_functions" not in json.loads(creates[1]["serialized_space"])["instructions"]
    assert cloud.read_overrides("personal")["insights_genie_id"] == "new-space"
    # A second unknown field is not guessed at: the error comes back, saying what was already dropped.
    sent = _genie_calls(monkeypatch, tmp_path, ["Error: Unknown field 'sql_functions'", "Error: Unknown field 'column_configs'"])
    with pytest.raises(cloud.CloudError, match="column_configs.*after dropping sql_functions"):
        cloud.insights("personal", None, step="genie")
    assert sum(1 for a in sent if a[:2] == ("genie", "create-space")) == 2
    # Any other error is not retried at all.
    sent = _genie_calls(monkeypatch, tmp_path, ["Error: PERMISSION_DENIED"])
    with pytest.raises(cloud.CloudError, match="PERMISSION_DENIED"):
        cloud.insights("personal", None, step="genie")
    assert sum(1 for a in sent if a[:2] == ("genie", "create-space")) == 1


def test_step_all_still_publishes_the_dashboard_with_genie_off_when_the_agent_fails(monkeypatch, tmp_path):
    sent = _genie_calls(monkeypatch, tmp_path, ["Error: PERMISSION_DENIED on genie"])
    monkeypatch.setattr(cloud, "ensure_catalog", lambda *a, **k: "lake")
    monkeypatch.setattr(cloud, "run_sql", lambda *a, **k: None)
    info = cloud.insights("personal", None, step="all")
    assert "PERMISSION_DENIED" in info["genie"]["error"] and "space_id" not in info["genie"]
    assert info["dashboard"]["dashboard_id"] == "dash1" and info["dashboard"]["genie_space_id"] is None
    published = json.loads(next(a[4] for a in sent if a[:2] == ("lakeview", "update")))  # lakeview update <id> --json <body>
    assert json.loads(published["serialized_dashboard"])["uiSettings"]["genieSpace"] == {"isEnabled": False}
    assert any(a[:2] == ("lakeview", "publish") for a in sent)
    saved = cloud.read_overrides("personal")
    assert saved["insights_genie_id"] == "old-space" and saved["manager_dashboard_id"] == "dash1", "a failed step writes no new id"
    # The genie step on its own still fails loudly.
    _genie_calls(monkeypatch, tmp_path, ["Error: PERMISSION_DENIED on genie"])
    with pytest.raises(cloud.CloudError, match="PERMISSION_DENIED"):
        cloud.insights("personal", None, step="genie")


def test_run_sql_uses_the_statement_api_with_the_body_in_a_file(monkeypatch):
    """The first build on the personal workspace showed the CLI's query tool is not a faithful carrier: a
    leading comment became a flag, and the metric view's YAML came out garbled from a file. The API takes
    the text whole; the body goes in a file so the long views fit any command line."""
    seen: list[tuple] = []

    def fake(*args, profile=None, **kwargs):
        seen.append(args)
        if args[:2] == ("api", "post"):
            assert args[2] == cloud.SQL_STATEMENTS_API and args[3] == "--json" and args[4].startswith("@")
            body = json.loads(Path(args[4][1:]).read_text(encoding="utf-8"))
            assert body["warehouse_id"] == "wh1" and body["on_wait_timeout"] == "CONTINUE"
            seen.append(("statement", body["statement"], profile))
            return {"statement_id": "s1", "status": {"state": "PENDING"}}  # the warehouse is still waking up
        assert args[:2] == ("api", "get") and args[2] == f"{cloud.SQL_STATEMENTS_API}/s1"
        return {"statement_id": "s1", "status": {"state": "SUCCEEDED"}}

    monkeypatch.setattr(cloud, "cli", fake)
    sql = "-- The course: one row per lesson.\nCREATE OR REPLACE VIEW x AS SELECT 1  -- groups; ask"
    assert cloud.run_sql(sql, "wh1", "DEFAULT", poll_seconds=0)["status"]["state"] == "SUCCEEDED"
    assert ("statement", sql, "DEFAULT") in seen, "the SQL arrives whole, comments and semicolons included"
    assert [a[:2] for a in seen if a[0] == "api"] == [("api", "post"), ("api", "get")]
    assert not any(sql in a for a in seen if a[0] == "api"), "the SQL text itself is never an argument"
    # A failed statement fails loudly, with the warehouse's reason.
    monkeypatch.setattr(cloud, "cli", lambda *a, **k: {"status": {"state": "FAILED", "error": {"message": "no such table"}}})
    with pytest.raises(cloud.CloudError, match="did not succeed \\(FAILED\\).*\n.*no such table"):
        cloud.run_sql(sql, "wh1", None)
