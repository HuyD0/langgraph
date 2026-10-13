"""The manager's dashboard: how each learner is progressing, where they are stuck, what they ask.

    uv run drill cloud manager-view            # personal workspace
    uv run drill cloud manager-view --target work

It reads the app's Lakebase tables through a read-only Unity Catalog catalog, so a SQL
warehouse can query them, and publishes one AI/BI dashboard with four pages: the team,
where each person is stuck, the questions they asked, and the weekly notes the app writes
(drill.server.team). Both are found or created, so running it again only updates them.

Only managers should get it: the catalog has no per-person filter. Share the dashboard and
grant ``USE CATALOG``/``SELECT`` on the catalog to a managers group, never to learners.
"""

from __future__ import annotations

import json
from typing import Any

DASHBOARD_NAME = "Daily Drill: learners"
LEARNER = "owner LIKE '%@%'"  # a person, not the app's own service principal (cache and usage rows)


def datasets(catalog: str) -> dict[str, str]:
    """Each dataset's SQL, reading ``<catalog>.drill.*``."""
    t = lambda name: f"`{catalog}`.drill.{name}"  # noqa: E731
    progress_type = "struct<current:string,lessons:map<string,struct<done:boolean,step:int>>>"
    return {
        "ds_learners": f"""
WITH p AS (
  SELECT owner, from_json(body, '{progress_type}') AS doc
  FROM {t('docs')} WHERE path LIKE 'data/users/%/progress' AND {LEARNER}
), e AS (
  SELECT owner, timestamp_seconds(at) AS at, kind, lesson_id, detail FROM {t('events')} WHERE {LEARNER}
), act AS (
  SELECT owner, MAX(at) AS last_active,
    COUNT(DISTINCT CASE WHEN at >= current_timestamp() - INTERVAL 7 DAYS THEN to_date(at) END) AS days_active_7d,
    COUNT_IF(kind = 'solved') AS exercises_solved,
    ROUND(AVG(CASE WHEN kind = 'solved' THEN CAST(get_json_object(detail, '$.hints') AS INT) END), 1) AS avg_hints,
    COUNT_IF(kind = 'asked' AND get_json_object(detail, '$.question') IS NOT NULL
             AND at >= current_timestamp() - INTERVAL 7 DAYS) AS questions_7d
  FROM e GROUP BY owner
), checks AS (
  SELECT e.owner, AVG(CASE WHEN CAST(get_json_object(e.detail, '$.answer') AS INT) = l.check_answer THEN 1.0 ELSE 0.0 END) AS right_rate
  FROM e JOIN {t('lessons')} l ON l.id = e.lesson_id WHERE e.kind = 'checked' GROUP BY e.owner
), study AS (
  SELECT owner, COUNT_IF(coalesce(get_json_object(body, '$.status'), 'open') <> 'got') AS study_open
  FROM {t('docs')} WHERE path LIKE 'study/%' AND {LEARNER} GROUP BY owner
), focus AS (
  SELECT owner, max_by(get_json_object(detail, '$.focus'), at) AS practising FROM e WHERE kind = 'focus_set' GROUP BY owner
), path AS (SELECT COUNT(*) AS n FROM {t('lessons')})
SELECT p.owner AS learner,
  size(map_filter(p.doc.lessons, (k, v) -> v.done)) AS lessons_done, path.n AS lessons_in_path,
  cur.no || ' ' || cur.title AS current_lesson, act.last_active, coalesce(act.days_active_7d, 0) AS days_active_7d,
  ROUND(100 * checks.right_rate) AS check_right_pct, coalesce(act.exercises_solved, 0) AS exercises_solved, act.avg_hints,
  coalesce(act.questions_7d, 0) AS questions_7d, coalesce(study.study_open, 0) AS study_open,
  coalesce(focus.practising, 'ai') AS practising
FROM p CROSS JOIN path
LEFT JOIN {t('lessons')} cur ON cur.id = p.doc.current
LEFT JOIN act ON act.owner = p.owner
LEFT JOIN checks ON checks.owner = p.owner
LEFT JOIN study ON study.owner = p.owner
LEFT JOIN focus ON focus.owner = p.owner""",
        "ds_weekly": f"""
SELECT e.owner AS learner, date_trunc('WEEK', timestamp_seconds(e.at)) AS week,
  COUNT_IF(e.kind = 'lesson_done') AS lessons_done, COUNT_IF(e.kind = 'solved') AS exercises_solved,
  COUNT_IF(e.kind = 'asked') AS asked, COUNT(DISTINCT to_date(timestamp_seconds(e.at))) AS days_active
FROM {t('events')} e WHERE e.{LEARNER}
GROUP BY 1, 2""",
        "ds_wrong_checks": f"""
SELECT e.owner AS learner, timestamp_seconds(e.at) AS at, l.no || ' ' || l.title AS lesson, l.phase,
  substr('ABC', CAST(get_json_object(e.detail, '$.answer') AS INT) + 1, 1) AS picked, substr('ABC', l.check_answer + 1, 1) AS right_answer
FROM {t('events')} e JOIN {t('lessons')} l ON l.id = e.lesson_id
WHERE e.kind = 'checked' AND e.{LEARNER} AND CAST(get_json_object(e.detail, '$.answer') AS INT) <> l.check_answer""",
        "ds_hints": f"""
SELECT e.owner AS learner, timestamp_seconds(e.at) AS at, coalesce(l.no || ' ' || l.title, e.lesson_id) AS exercise,
  CAST(get_json_object(e.detail, '$.hints') AS INT) AS hints
FROM {t('events')} e LEFT JOIN {t('lessons')} l ON l.id = e.lesson_id
WHERE e.kind = 'solved' AND e.{LEARNER} AND CAST(get_json_object(e.detail, '$.hints') AS INT) >= 2""",
        # platform practice: each question not right first time, what they picked, and the help they needed
        "ds_practice_missed": f"""
WITH m AS (
  SELECT owner, at, lesson_id, explode(from_json(get_json_object(detail, '$.missed'),
    'array<struct<q:string,wrong:array<string>,clue:boolean,answer:boolean,checks:int,problems:array<string>>>')) AS x
  FROM {t('events')} WHERE kind = 'practised' AND {LEARNER}
)
SELECT m.owner AS learner, timestamp_seconds(m.at) AS at, coalesce(l.no || ' ' || l.title, m.lesson_id) AS lesson,
  m.x.q AS question, array_join(m.x.wrong, ', ') AS picked,
  CASE WHEN m.x.answer THEN 'the answer' WHEN m.x.clue THEN 'a clue' ELSE '' END AS needed,
  array_join(m.x.problems, '; ') AS yaml_problems
FROM m LEFT JOIN {t('lessons')} l ON l.id = m.lesson_id""",
        "ds_study": f"""
SELECT owner AS learner, get_json_object(body, '$.text') AS item, get_json_object(body, '$.source') AS source,
  coalesce(get_json_object(body, '$.status'), 'open') AS status, timestamp_seconds(updated_at) AS updated
FROM {t('docs')} WHERE path LIKE 'study/%' AND {LEARNER}""",
        "ds_questions": f"""
SELECT e.owner AS learner, timestamp_seconds(e.at) AS at, coalesce(l.no || ' ' || l.title, e.lesson_id) AS lesson,
  get_json_object(e.detail, '$.step') AS step, get_json_object(e.detail, '$.question') AS question
FROM {t('events')} e LEFT JOIN {t('lessons')} l ON l.id = e.lesson_id
WHERE e.kind = 'asked' AND e.{LEARNER} AND get_json_object(e.detail, '$.question') IS NOT NULL""",
        "ds_notes": f"""
SELECT owner AS learner, week, summary AS note, timestamp_seconds(made_at) AS written
FROM {t('summaries')} WHERE {LEARNER}""",
    }


# -- layout ----------------------------------------------------------------------

def _text(name: str, lines: list[str], x: int, y: int, w: int = 6, h: int = 2) -> dict:
    return {"widget": {"name": name, "multilineTextboxSpec": {"lines": lines}}, "position": {"x": x, "y": y, "width": w, "height": h}}


def _table(name: str, dataset: str, columns: list[tuple[str, str, str]], title: str, description: str,
           x: int, y: int, w: int = 6, h: int = 6) -> dict:
    """``columns``: (field, kind, heading), kind being string, integer, float or datetime."""
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {
                "datasetName": dataset, "disaggregated": True,
                "fields": [{"name": f, "expression": f"`{f}`"} for f, _, _ in columns]}}],
            "spec": {"version": 1, "widgetType": "table", "encodings": {"columns": [
                {"fieldName": f, "type": kind, "displayAs": "datetime" if kind == "datetime" else ("number" if kind in ("integer", "float") else "string"),
                 "visible": True, "order": i, "title": head, "displayName": head}
                for i, (f, kind, head) in enumerate(columns)]},
                "frame": {"showTitle": True, "title": title, "showDescription": True, "description": description}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _bar(name: str, dataset: str, x_field: str, y_field: str, title: str, description: str, x: int, y: int, w: int = 6, h: int = 5) -> dict:
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {
                "datasetName": dataset, "disaggregated": False,
                "fields": [{"name": x_field, "expression": f"`{x_field}`"}, {"name": y_field, "expression": f"SUM(`{y_field}`)"},
                           {"name": "learner", "expression": "`learner`"}]}}],
            "spec": {"version": 3, "widgetType": "bar", "encodings": {
                "x": {"fieldName": x_field, "scale": {"type": "temporal"}, "displayName": "week"},
                "y": {"fieldName": y_field, "scale": {"type": "quantitative"}, "displayName": y_field.replace("_", " ")},
                "color": {"fieldName": "learner", "scale": {"type": "categorical"}, "displayName": "learner"}},
                "frame": {"showTitle": True, "title": title, "showDescription": True, "description": description}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _learner_filter(name: str, sets: list[str], x: int = 0, y: int = 0) -> dict:
    """One "Learner" picker that filters every dataset on the page."""
    return {
        "widget": {
            "name": name,
            "queries": [{"name": f"f_{ds}", "query": {"datasetName": ds, "disaggregated": False, "fields": [
                {"name": "learner", "expression": "`learner`"},
                {"name": "learner_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"}]}} for ds in sets],
            "spec": {"version": 2, "widgetType": "filter-multi-select", "encodings": {"fields": [
                {"fieldName": "learner", "displayName": "learner", "queryName": f"f_{ds}"} for ds in sets]},
                "frame": {"showTitle": True, "title": "Learner"}},
        },
        "position": {"x": x, "y": y, "width": 2, "height": 2},
    }


def dashboard(catalog: str) -> dict:
    """The whole dashboard, ready for the Lakeview API's ``serialized_dashboard``."""
    sql = datasets(catalog)
    ds = [{"name": name, "displayName": name.removeprefix("ds_").replace("_", " "), "queryLines": [query.strip()]}
          for name, query in sql.items()]
    team = {"name": "team", "displayName": "Team", "pageType": "PAGE_TYPE_CANVAS", "layout": [
        _text("t_team", ["### How everyone is getting on\n",
                         "One row per learner. Lessons come from their progress; days, Checks, hints and questions from what they did. "
                         "Check right % counts first answers to each lesson's multiple-choice question."], 0, 0, 4),
        _learner_filter("f_team", ["ds_learners", "ds_weekly"], 4, 0),
        _table("tb_learners", "ds_learners", [
            ("learner", "string", "learner"), ("lessons_done", "integer", "lessons done"), ("lessons_in_path", "integer", "of"),
            ("current_lesson", "string", "on lesson"), ("last_active", "datetime", "last active"),
            ("days_active_7d", "integer", "days active (7d)"), ("check_right_pct", "integer", "Check right %"),
            ("exercises_solved", "integer", "exercises solved"), ("avg_hints", "float", "hints per exercise"),
            ("questions_7d", "integer", "questions (7d)"), ("study_open", "integer", "study list open"),
            ("practising", "string", "practising")],
            "Learners", "Where each person is on the path", 0, 2, 6, 5),
        _bar("b_weekly", "ds_weekly", "week", "lessons_done", "Lessons finished per week", "A steady few a week beats a burst", 0, 7, 3),
        _bar("b_days", "ds_weekly", "week", "days_active", "Days active per week", "Daily practice is the habit to build", 3, 7, 3),
    ]}
    stuck = {"name": "stuck", "displayName": "Where they're stuck", "pageType": "PAGE_TYPE_CANVAS", "layout": [
        _text("t_stuck", ["### Where they may be stuck\n",
                          "Wrong first answers, exercises that took two or more hints, and what they saved to come back to."], 0, 0, 4),
        _learner_filter("f_stuck", ["ds_wrong_checks", "ds_hints", "ds_study", "ds_practice_missed"], 4, 0),
        _table("tb_wrong", "ds_wrong_checks", [("learner", "string", "learner"), ("at", "datetime", "when"), ("lesson", "string", "lesson"),
                                               ("phase", "string", "phase"), ("picked", "string", "picked"), ("right_answer", "string", "right answer")],
               "Check answers they got wrong", "A topic that keeps showing up here is worth a conversation", 0, 2, 6, 5),
        _table("tb_hints", "ds_hints", [("learner", "string", "learner"), ("at", "datetime", "when"), ("exercise", "string", "exercise"),
                                        ("hints", "integer", "hints")], "Exercises that needed 2 or more hints", "", 0, 7, 3, 5),
        _table("tb_study", "ds_study", [("learner", "string", "learner"), ("item", "string", "saved"), ("source", "string", "from"),
                                        ("status", "string", "status"), ("updated", "datetime", "updated")],
               "Study list", "Things they saved to understand better; 'got' means they marked it learned", 3, 7, 3, 5),
        _table("tb_practice", "ds_practice_missed", [("learner", "string", "learner"), ("at", "datetime", "when"), ("lesson", "string", "lesson"),
                                                     ("question", "string", "question"), ("picked", "string", "picked"), ("needed", "string", "needed"),
                                                     ("yaml_problems", "string", "YAML problems")],
               "Platform practice questions they missed", "The wrong answer they picked usually shows the misunderstanding", 0, 12, 6, 6),
    ]}
    questions = {"name": "questions", "displayName": "Questions", "pageType": "PAGE_TYPE_CANVAS", "layout": [
        _text("t_q", ["### What they asked the tutor\n", "Every question typed or tapped in \"Ask about this lesson\", newest first."], 0, 0, 4),
        _learner_filter("f_q", ["ds_questions"], 4, 0),
        _table("tb_q", "ds_questions", [("learner", "string", "learner"), ("at", "datetime", "when"), ("lesson", "string", "lesson"),
                                        ("step", "string", "step"), ("question", "string", "question")], "Questions", "", 0, 2, 6, 8),
    ]}
    notes = {"name": "notes", "displayName": "Weekly notes", "pageType": "PAGE_TYPE_CANVAS", "layout": [
        _text("t_n", ["### Weekly notes\n", "A few plain sentences per learner, written by the app's model from the week's numbers. "
                      "Refreshed about once a day while people study."], 0, 0, 4),
        _learner_filter("f_n", ["ds_notes"], 4, 0),
        _table("tb_n", "ds_notes", [("learner", "string", "learner"), ("week", "string", "week"), ("note", "string", "note"),
                                    ("written", "datetime", "written")], "Notes", "", 0, 2, 6, 8),
    ]}
    return {"datasets": ds, "pages": [team, stuck, questions, notes]}


def serialized(catalog: str) -> str:
    return json.dumps(dashboard(catalog))


def summary(info: dict[str, Any]) -> str:
    return f"Dashboard: {info.get('url')}\nCatalog: {info.get('catalog')}"
