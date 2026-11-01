"""The managers' dashboard rebuilt on the insights layer: "Daily Drill: how it is going".

Seven pages, each answering one question, plus a filter page. Every dataset reads the insights layer by its
full name and calls the trusted functions by their full name, so the dashboard, Genie and the owner's own
queries all share one definition of every number. The board keeps the id and link of the old dashboard
(``manager_dashboard_id`` in the overrides file) and reuses manager_view's widget helpers.
"""

from __future__ import annotations

from drill.insights import layer
from drill.insights.genie import THIS_MONDAY, UTC_TODAY
from drill.manager_view import _bar, _filter_fields, _learner_filter, _table, _text

DASHBOARD_NAME = "Daily Drill: how it is going"
W = 12  # the grid is 12 columns wide

THEME = {
    "canvasBackgroundColor": {"light": "#FCFCFC", "dark": "#1F272D"},
    "widgetBackgroundColor": {"light": "#FFFFFF", "dark": "#11171C"},
    "fontColor": {"light": "#11171C", "dark": "#E8ECF0"},
    "selectionColor": {"light": "#2272B4", "dark": "#8ACAFF"},
    # Violet first (the AI path), then blue, teal (the platform track), and distinct hues after them.
    "visualizationColors": ["#6929C4", "#1192E8", "#005D5D", "#9F1853", "#FA4D56", "#FFA600", "#99DDB4"],
    "widgetHeaderAlignment": "LEFT",
}

PERCENT = {"type": "number-percent", "decimalPlaces": {"type": "max", "places": 0}}
ONE_DECIMAL = {"type": "number", "decimalPlaces": {"type": "max", "places": 1}}


def datasets(insights_catalog: str) -> dict[str, str]:
    """Each dataset's SQL, reading ``<insights_catalog>.drill_insights.*`` by full name."""
    t = lambda name: layer.fqn(insights_catalog, name)  # noqa: E731
    kpi_measures = """MEASURE(`Active learners`) AS active_learners,
    MEASURE(`New learners`) AS new_learners,
    MEASURE(`Days active per learner`) AS days_per_learner,
    MEASURE(`Lessons finished`) AS lessons_finished,
    MEASURE(`Typed questions`) AS typed_questions,
    MEASURE(`Learners using the tutor`) AS tutor_users,
    MEASURE(`Got it rate`) AS got_it_rate"""
    return {
        # The counters: the last 7 days against the 7 days before, on UTC days.
        "ds_kpis": f"""
WITH cur AS (
  SELECT {kpi_measures}
  FROM {t('engagement_metrics')}
  WHERE `Day` >= date_sub({UTC_TODAY}, 6)
),
prev AS (
  SELECT {kpi_measures}
  FROM {t('engagement_metrics')}
  WHERE `Day` BETWEEN date_sub({UTC_TODAY}, 13) AND date_sub({UTC_TODAY}, 7)
)
SELECT
  cur.active_learners AS active_learners_7d, prev.active_learners AS active_learners_prev_7d,
  cur.new_learners AS new_learners_7d, prev.new_learners AS new_learners_prev_7d,
  cur.days_per_learner AS days_per_learner_7d, prev.days_per_learner AS days_per_learner_prev_7d,
  cur.lessons_finished AS lessons_finished_7d, prev.lessons_finished AS lessons_finished_prev_7d,
  cur.typed_questions AS typed_questions_7d, prev.typed_questions AS typed_questions_prev_7d,
  cur.tutor_users AS tutor_users_7d, prev.tutor_users AS tutor_users_prev_7d,
  cur.got_it_rate AS got_it_rate_7d, prev.got_it_rate AS got_it_rate_prev_7d
FROM cur CROSS JOIN prev""",
        # One row per week for the last 26 weeks; each number is that week's own count.
        "ds_weekly": f"""
SELECT
  `Week` AS week,
  MEASURE(`Active learners`) AS active_learners,
  MEASURE(`New learners`) AS new_learners,
  MEASURE(`Days active per learner`) AS days_per_active_learner,
  MEASURE(`Lessons finished`) AS lessons_finished,
  MEASURE(`Typed questions`) AS typed_questions,
  MEASURE(`Got it ratings`) AS got_it,
  MEASURE(`Still stuck ratings`) AS still_stuck,
  MEASURE(`Got it rate`) AS got_it_rate
FROM {t('engagement_metrics')}
WHERE `Week` >= date_sub({THIS_MONDAY}, 7 * 25)
GROUP BY ALL""",
        "ds_retention": f"""
SELECT start_week, week_number, learners_started, learners_active, share_active
FROM {t('retention_by_start_week')}(12)
WHERE week_number <= 8""",
        "ds_learners": f"""
SELECT
  learner, learner_name, CASE WHEN has_started THEN 'Yes' ELSE 'No' END AS started, status, attention_reason,
  last_active_date, days_since_last_active, days_active_last_7, days_active_last_28, longest_streak_days,
  lessons_finished, lessons_finished_last_28, main_path_lessons_finished, main_path_percent_done,
  platform_track_lessons_finished, exercises_passed, current_lesson, coalesce(current_phase, 'None yet') AS current_phase,
  practising, first_check_answers, first_check_answers_right, stuck_lessons, lessons_left_after_struggling,
  typed_questions_last_7, study_items_open, study_reviews_due,
  CASE WHEN on_leaderboard THEN 'Yes' ELSE 'No' END AS on_leaderboard, start_week
FROM {t('learners')}""",
        "ds_attention": f"""
SELECT
  learner, learner_name, status, attention_reason, last_active_date, days_since_last_active,
  current_lesson, stuck_lessons, lessons_finished,
  CASE status WHEN 'Drifting' THEN 1 WHEN 'Gone quiet' THEN 2 WHEN 'Active' THEN 3 ELSE 4 END AS sort_order
FROM {t('learners')}
WHERE attention_reason IS NOT NULL
ORDER BY sort_order, stuck_lessons DESC, learner_name""",
        "ds_phase_progress": f"""
WITH per_phase AS (
  SELECT ll.learner, ll.phase, ll.phase_order, ll.course_part,
    COUNT_IF(ll.furthest_step_number >= 1) AS started, COUNT_IF(ll.is_finished) AS finished
  FROM {t('learner_lessons')} ll
  WHERE ll.phase_order IS NOT NULL
  GROUP BY ll.learner, ll.phase, ll.phase_order, ll.course_part
),
sized AS (
  SELECT p.*, l.lessons_in_phase
  FROM per_phase p
  JOIN (SELECT DISTINCT phase, lessons_in_phase FROM {t('lessons')}) l ON l.phase = p.phase
)
SELECT phase, phase_order, course_part, '1. Started a lesson' AS stage, COUNT_IF(started > 0) AS learners
FROM sized GROUP BY phase, phase_order, course_part
UNION ALL
SELECT phase, phase_order, course_part, '2. Finished a lesson' AS stage, COUNT_IF(finished > 0) AS learners
FROM sized GROUP BY phase, phase_order, course_part
UNION ALL
SELECT phase, phase_order, course_part, '3. Finished the whole phase' AS stage, COUNT_IF(finished >= lessons_in_phase) AS learners
FROM sized GROUP BY phase, phase_order, course_part""",
        "ds_lessons": f"""
SELECT
  lesson, lesson_number, position, phase, phase_order, module, course_part,
  learners_opened, learners_past_learn, learners_reached_build, learners_reached_explain, learners_finished,
  learners_in_progress, learners_stalled, learners_stuck, learners_left_after_struggling, finish_rate,
  first_check_answers, first_check_wrong, first_check_wrong_rate, check_answers_shown, check_on_own_rate,
  tutor_requests, typed_questions, still_stuck_presses
FROM {t('lesson_summary')}
ORDER BY position""",
        "ds_needs_work": f"""
SELECT
  lesson, phase, course_part, position, learners_past_learn, learners_stalled, learners_stuck,
  finish_rate, check_on_own_rate, practice_right_rate, code_two_plus_hints_rate,
  explain_wrong_picks_per_learner, still_stuck_per_learner, warning_signs, main_problem
FROM {t('lessons_needing_work')}(5)
ORDER BY warning_signs DESC, learners_stuck DESC, position""",
        "ds_check_questions": f"""
WITH q AS (
  SELECT ll.lesson, ll.position, ll.phase, ll.phase_order, ll.course_part,
    stack(3, 1, ll.check_q1_result, 2, ll.check_q2_result, 3, ll.check_q3_result) AS (question_number, result)
  FROM {t('learner_lessons')} ll
  WHERE ll.phase_order IS NOT NULL
)
SELECT
  q.lesson, q.position, q.phase, q.phase_order, q.course_part, q.question_number,
  COUNT(*) AS learners_tried,
  COUNT_IF(q.result = 'On their own') AS on_their_own,
  COUNT_IF(q.result = 'With a clue or another try') AS with_help,
  COUNT_IF(q.result = 'Answer shown') AS answer_shown,
  COUNT_IF(q.result = 'Tried, not right yet') AS not_right_yet,
  try_divide(COUNT_IF(q.result = 'On their own'), COUNT(*)) AS on_own_rate
FROM q
WHERE q.result IS NOT NULL
GROUP BY q.lesson, q.position, q.phase, q.phase_order, q.course_part, q.question_number
ORDER BY on_own_rate, learners_tried DESC, q.position, q.question_number""",
        "ds_q1_wrong_picks": f"""
WITH answered AS (
  SELECT lesson_id, COUNT(*) AS first_answers
  FROM {t('learner_lessons')}
  WHERE first_check_answer_right IS NOT NULL
  GROUP BY lesson_id
)
SELECT
  ll.lesson, ll.position, ll.phase, ll.course_part,
  ll.first_check_picked AS picked, ll.first_check_right_answer AS right_answer,
  COUNT(*) AS learners_picked_it, a.first_answers,
  try_divide(COUNT(*), a.first_answers) AS share_of_first_answers
FROM {t('learner_lessons')} ll
JOIN answered a ON a.lesson_id = ll.lesson_id
WHERE ll.first_check_answer_right = false AND ll.first_check_picked IS NOT NULL
GROUP BY ll.lesson, ll.position, ll.phase, ll.course_part, ll.first_check_picked, ll.first_check_right_answer, a.first_answers
ORDER BY learners_picked_it DESC, ll.position""",
        "ds_practice_missed": f"""
WITH did AS (
  SELECT lesson_id, COUNT(*) AS learners_did_practice
  FROM {t('learner_lessons')}
  WHERE practice_questions IS NOT NULL
  GROUP BY lesson_id
),
m AS (
  SELECT ll.lesson_id, ll.lesson, ll.position, ll.phase, ll.course_part,
    mx.x.q AS question, try_element_at(mx.x.wrong, 1) AS first_wrong_pick,
    CASE WHEN mx.x.answer THEN 'Answer shown' WHEN mx.x.clue THEN 'Clue' ELSE 'Another try' END AS help_used
  FROM {t('learner_lessons')} ll
  LATERAL VIEW explode(ll.practice_missed) mx AS x
),
top_pick AS (
  SELECT t.lesson_id, t.question, max_by(t.first_wrong_pick, t.n) AS most_common_wrong_pick
  FROM (SELECT lesson_id, question, first_wrong_pick, COUNT(*) AS n FROM m WHERE first_wrong_pick IS NOT NULL
        GROUP BY lesson_id, question, first_wrong_pick) t
  GROUP BY t.lesson_id, t.question
)
SELECT
  m.lesson, m.position, m.phase, m.course_part, m.question,
  COUNT(*) AS learners_missed, d.learners_did_practice,
  try_divide(COUNT(*), d.learners_did_practice) AS miss_rate,
  COUNT_IF(m.help_used = 'Clue') AS needed_a_clue,
  COUNT_IF(m.help_used = 'Answer shown') AS needed_the_answer,
  tp.most_common_wrong_pick
FROM m
LEFT JOIN did d ON d.lesson_id = m.lesson_id
LEFT JOIN top_pick tp ON tp.lesson_id = m.lesson_id AND tp.question = m.question
GROUP BY m.lesson_id, m.lesson, m.position, m.phase, m.course_part, m.question, d.learners_did_practice, tp.most_common_wrong_pick
ORDER BY learners_missed DESC, m.position""",
        "ds_stuck": f"""
SELECT
  learner, learner_name, status, lesson, phase, furthest_step, help_signals,
  first_check_picked, first_check_right_answer, practice_missed_questions,
  tutor_requests, last_activity_at, days_since_last_activity
FROM {t('who_is_stuck')}('')
ORDER BY days_since_last_activity DESC, learner_name""",
        "ds_team_week": f"""
SELECT learner, learner_name, status, week_start, days_active, days_active_week_before, lessons_finished,
  lessons_finished_week_before, exercises_passed, typed_questions, first_check_answers, first_check_answers_right, stuck_lessons
FROM {t('team_week')}(CAST(NULL AS DATE))
ORDER BY lessons_finished DESC, days_active DESC, learner_name""",
        "ds_study": f"""
SELECT learner, learner_name, saved_at, saved_text, learner_note, saved_from, lesson, status,
  CASE WHEN review_due THEN 'Yes' ELSE 'No' END AS review_due, follow_up_questions
FROM {t('study_items')}
ORDER BY CASE WHEN status = 'Open' THEN 0 ELSE 1 END, saved_at DESC""",
        "ds_tutor": f"""
SELECT
  learner, learner_name, activity_date, activity_week, tutor_feature, how_asked,
  coalesce(tutor_step, CASE WHEN tutor_feature LIKE 'Study list%' THEN 'Study list' ELSE 'Not recorded' END) AS lesson_step,
  lesson, phase, course_part
FROM {t('activity')}
WHERE activity_code = 'asked'""",
        "ds_questions": f"""
SELECT happened_at, learner, learner_name, lesson, tutor_step, how_asked, question_text
FROM {t('activity')}
WHERE question_text IS NOT NULL
ORDER BY happened_at DESC""",
        "ds_notes": f"""
SELECT learner, learner_name, week, note, written_at
FROM {t('weekly_notes')}
ORDER BY week DESC, learner_name""",
    }


# -- widget helpers beyond manager_view's ---------------------------------------------

def _frame(title: str, description: str) -> dict:
    return {"showTitle": True, "title": title, "showDescription": bool(description), "description": description}


def _counter(name: str, dataset: str, value: str, target: str, title: str, description: str, x: int, y: int,
             w: int = 3, h: int = 3, fmt: dict | None = None, value_label: str = "Last 7 days", target_label: str = "7 days before") -> dict:
    """A KPI from a one-row dataset, with the previous period as the comparison (counter version 2, height 3)."""
    value_enc = {"fieldName": value, "displayName": value_label}
    if fmt:
        value_enc["format"] = fmt
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "disaggregated": True, "fields": [
                {"name": value, "expression": f"`{value}`"}, {"name": target, "expression": f"`{target}`"}]}}],
            "spec": {"version": 2, "widgetType": "counter",
                     "encodings": {"value": value_enc, "target": {"fieldName": target, "displayName": target_label}},
                     "frame": _frame(title, description)},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _line(name: str, dataset: str, x_field: str, y_fields: list[tuple[str, str]], title: str, description: str,
          x: int, y: int, w: int = 6, h: int = 5, fmt: dict | None = None) -> dict:
    """A line chart over a dataset that already has one row per period (``y_fields``: (field, label))."""
    y_enc = {"scale": {"type": "quantitative"}, "fields": [{"fieldName": f, "displayName": lab} for f, lab in y_fields]}
    if fmt:
        y_enc["format"] = fmt
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "disaggregated": True, "fields": [
                {"name": x_field, "expression": f"`{x_field}`"}, *[{"name": f, "expression": f"`{f}`"} for f, _ in y_fields]]}}],
            "spec": {"version": 3, "widgetType": "line",
                     "encodings": {"x": {"fieldName": x_field, "scale": {"type": "temporal"}, "displayName": "Week"}, "y": y_enc},
                     "frame": _frame(title, description)},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _pivot(name: str, dataset: str, row: str, col: str, cell: str, title: str, description: str, x: int, y: int,
           w: int = W, h: int = 6, extra: list[str] | None = None) -> dict:
    """A cross-tab (pivot version 3): rows by ``row``, columns by ``col``, the cell a colour-scaled SUM of ``cell``."""
    fields = [{"name": row, "expression": f"`{row}`"}, {"name": col, "expression": f"`{col}`"},
              {"name": f"sum({cell})", "expression": f"SUM(`{cell}`)"}]
    fields += [{"name": f"sum({e})", "expression": f"SUM(`{e}`)"} for e in (extra or [])]
    cells = [{"fieldName": f"sum({cell})", "cellType": "color-scale", "format": PERCENT}]
    cells += [{"fieldName": f"sum({e})", "cellType": "text"} for e in (extra or [])]
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "disaggregated": False, "fields": fields}}],
            "spec": {"version": 3, "widgetType": "pivot",
                     "encodings": {"rows": [{"fieldName": row, "displayName": "Start week"}],
                                   "columns": [{"fieldName": col, "displayName": "Weeks later"}],
                                   "cell": {"type": "multi-cell", "fields": cells}},
                     "frame": _frame(title, description)},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _histogram(name: str, dataset: str, field: str, bin_width: int, title: str, description: str, x: int, y: int,
               w: int = 4, h: int = 6) -> dict:
    """A frequency distribution (histogram version 3); the bin width lives in the field expression."""
    bin_name = f"bin({field}, binWidth={bin_width})"
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "disaggregated": False, "fields": [
                {"name": bin_name, "expression": f"BIN_FLOOR(`{field}`, {bin_width})"},
                {"name": "count(*)", "expression": "COUNT(`*`)"}]}}],
            "spec": {"version": 3, "widgetType": "histogram",
                     "encodings": {"x": {"fieldName": bin_name, "scale": {"type": "quantitative"}, "displayName": field.replace("_", " ")},
                                   "y": {"fieldName": "count(*)", "scale": {"type": "quantitative"}, "displayName": "Learners"}},
                     "frame": _frame(title, description)},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _combo(name: str, dataset: str, x_field: str, bars: list[tuple[str, str]], lines: list[tuple[str, str]],
           title: str, description: str, x: int, y: int, w: int = 6, h: int = 5, line_fmt: dict | None = None) -> dict:
    """Bars on the first axis and a line on the second (combo version 1), over one row per period."""
    fields = [{"name": x_field, "expression": f"`{x_field}`"}]
    fields += [{"name": f, "expression": f"`{f}`"} for f, _ in bars + lines]
    secondary = {"fields": [{"fieldName": f, "displayName": lab} for f, lab in lines]}
    if line_fmt:
        secondary["format"] = line_fmt
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "disaggregated": True, "fields": fields}}],
            "spec": {"version": 1, "widgetType": "combo",
                     "encodings": {"x": {"fieldName": x_field, "scale": {"type": "temporal"}, "displayName": "Week"},
                                   "y": {"scale": {"type": "quantitative"},
                                         "primary": {"fields": [{"fieldName": f, "displayName": lab} for f, lab in bars]},
                                         "secondary": secondary},
                                   "label": {"show": False}},
                     "frame": _frame(title, description)},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _multi_select(name: str, field: str, title: str, sets: list[str], x: int, y: int, w: int = 2, h: int = 2,
                  default: str | None = None, single: bool = False, associativity: bool = True) -> dict:
    """A picker on ``field`` that filters every dataset in ``sets``, the same shape as manager_view's Learner picker:
    the field plus its ``associative_filter_predicate_group`` companion, which the shipped dashboard proves works.
    ``associativity=False`` gives the plain field alone (the dashboard reference's advice) if a filter errors."""
    spec = {"version": 2, "widgetType": "filter-single-select" if single else "filter-multi-select",
            "encodings": {"fields": [{"fieldName": field, "displayName": title, "queryName": f"f_{ds}"} for ds in sets]},
            "frame": {"showTitle": True, "title": title}}
    if default is not None:
        spec["selection"] = {"defaultSelection": {"values": {"dataType": "STRING", "values": [{"value": default}]}}}
    return {
        "widget": {
            "name": name,
            "queries": [{"name": f"f_{ds}", "query": {"datasetName": ds, "disaggregated": False,
                                                     "fields": _filter_fields(field, associativity)}} for ds in sets],
            "spec": spec,
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _date_range(name: str, bindings: list[tuple[str, str]], title: str, x: int, y: int, w: int = 4, h: int = 2) -> dict:
    """A date range picker bound to one date column per dataset (``bindings``: (dataset, field))."""
    return {
        "widget": {
            "name": name,
            "queries": [{"name": f"f_{ds}", "query": {"datasetName": ds, "disaggregated": False,
                                                     "fields": [{"name": field, "expression": f"`{field}`"}]}} for ds, field in bindings],
            "spec": {"version": 2, "widgetType": "filter-date-range-picker",
                     "encodings": {"fields": [{"fieldName": field, "displayName": title, "queryName": f"f_{ds}"} for ds, field in bindings]},
                     "frame": {"showTitle": True, "title": title}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def _page(name: str, title: str, layout: list[dict], page_type: str = "PAGE_TYPE_CANVAS") -> dict:
    return {"name": name, "displayName": title, "pageType": page_type, "layoutVersion": "GRID_V1", "layout": layout}


# -- the pages -------------------------------------------------------------------------

TIME_NOTE = ("Days and weeks are world time (UTC) days, so an evening of study in the Americas can land on the next day. "
             "Weeks run Monday to Sunday; the current week is still in progress.")

# Categorical axes draw alphabetically unless told the order; these follow the course, the quiet-days scale and the lesson.
PHASE_ORDER = ["Frame", "Design", "Build and trace", "Evaluate", "Ship", "Monitor", "Platform track"]
STATUS_ORDER = ["Active", "Drifting", "Gone quiet", "Not started", "Started before tracking began"]
STEP_ORDER = ["Learn", "Check", "Build", "Explain", "Study list", "Not recorded"]


def pages() -> list[dict]:
    per_person = ["ds_learners", "ds_attention", "ds_stuck", "ds_team_week", "ds_study", "ds_tutor", "ds_questions", "ds_notes"]
    by_part = ["ds_phase_progress", "ds_lessons", "ds_needs_work", "ds_check_questions", "ds_q1_wrong_picks", "ds_practice_missed"]
    filters = _page("filters", "Filters", [
        _date_range("f_dates", [("ds_weekly", "week"), ("ds_tutor", "activity_date"), ("ds_questions", "happened_at")],
                    "Dates (weekly charts, tutor requests and questions)", 0, 0, 6),
        _learner_filter("f_learner", per_person, 6, 0, 6),
    ], "PAGE_TYPE_GLOBAL_FILTERS")

    going = _page("going", "How it's going", [
        _text("t_going", ["### How Daily Drill is being used\n", "\n",
                          "The four numbers compare the last 7 days with the 7 days before. The charts use calendar weeks. "
                          "Active means a learning action: moving to a step, answering a Check question, finishing a lesson, passing an exercise, "
                          "finishing practice or asking the tutor. Just opening the app or choosing what to practise does not count. " + TIME_NOTE],
              0, 0, W, 2),
        _counter("c_active", "ds_kpis", "active_learners_7d", "active_learners_prev_7d", "Active learners",
                 "Different people with a learning action", 0, 2),
        _counter("c_new", "ds_kpis", "new_learners_7d", "new_learners_prev_7d", "New learners",
                 "People whose first learning action was in the period", 3, 2),
        _counter("c_days", "ds_kpis", "days_per_learner_7d", "days_per_learner_prev_7d", "Days studied per active learner",
                 "Out of 7; the habit the course is built around", 6, 2, fmt=ONE_DECIMAL),
        _counter("c_finished", "ds_kpis", "lessons_finished_7d", "lessons_finished_prev_7d", "Lessons finished",
                 "First finishes only", 9, 2),
        _line("l_weekly", "ds_weekly", "week", [("active_learners", "Active learners"), ("new_learners", "New learners")],
              "Active and new learners per week", "Growing, flat or fading, and whether new people keep arriving", 0, 5, 6),
        _bar("b_finished", "ds_weekly", "week", "lessons_finished", "Lessons finished per week",
             "A steady few each week beats one burst. A launch week can spike when old progress is recorded all at once", 6, 5, 6,
             color=None, x_label="Week", y_label="Lessons finished"),
        _line("l_days", "ds_weekly", "week", [("days_per_active_learner", "Days studied per active learner")],
              "Days studied per active learner, by week", "Whether the study habit gets stronger as the programme settles in", 0, 10, W, 5,
              fmt=ONE_DECIMAL),
    ])

    back = _page("back", "Do they come back?", [
        _text("t_back", ["### After their first week, do people keep coming back?\n", "\n",
                         "In the table, each row is a group of people who started in the same week. Each column is a number of weeks later. "
                         "Each cell is the share of that group who did something to learn in that week. "
                         "The chart and the list below show the state today, over all time."], 0, 0, W, 2),
        _pivot("p_retention", "ds_retention", "start_week", "week_number", "share_active", "Still learning, by start week",
               "Each starting group is kept apart, so a big launch week cannot hide a later drop-off", 0, 2, W, 6,
               extra=["learners_started", "learners_active"]),
        _bar("b_status", "ds_learners", "status", "learner", "Where everyone is now",
             "Active: a learning action in the last 7 days. Drifting: 7 to 20 quiet days. Gone quiet: 21 or more", 0, 8, 6,
             color=None, x_scale="categorical", x_label="Status", y_label="Learners", agg="COUNT", x_sort=STATUS_ORDER),
        _bar("b_days7", "ds_learners", "days_active_last_7", "learner", "Days studied in the last 7 days",
             "A few people every day against many once a week", 6, 8, 6,
             color=None, x_scale="categorical", x_label="Days with a learning action", y_label="Learners", agg="COUNT"),
        _table("tb_attention", "ds_attention", [
            ("learner_name", "string", "Learner"), ("status", "string", "Status"), ("attention_reason", "string", "Why check in"),
            ("last_active_date", "date", "Last learning day"), ("current_lesson", "string", "On lesson"),
            ("stuck_lessons", "integer", "Stuck on"), ("lessons_finished", "integer", "Lessons finished")],
            "Who needs a check-in", "Drifting first: a nudge after one missed week is the cheapest help there is", 0, 13, W, 7, version=2),
    ])

    far = _page("far", "How far they get", [
        _text("t_far", ["### How far through the course do learners get?\n", "\n",
                        "Main path and Platform track are separate parts: someone practising the track is not behind on the path. "
                        "Everything on this page shows the state today, over all time."], 0, 0, 8, 2),
        _multi_select("f_part_far", "course_part", "Course part", by_part, 8, 0),
        _multi_select("f_started", "started", "Has started", ["ds_learners"], 10, 0, default="Yes", single=True),
        _bar("b_phases", "ds_phase_progress", "phase", "learners", "Learners reaching each phase",
             "The drop between the bars shows where people stall", 0, 2, 8, 6,
             color="stage", x_scale="categorical", x_label="Phase", y_label="Learners", layout="group", x_sort=PHASE_ORDER),
        _histogram("h_finished", "ds_learners", "lessons_finished", 10, "Lessons finished per learner",
                   "Do most people stop after a handful of lessons, or keep going?", 8, 2, 4, 6),
        _bar("b_practising", "ds_learners", "practising", "learner", "What learners chose to practise",
             "The AI engineering path, the Platform track, both, or not chosen yet", 0, 8, W, 4,
             color=None, x_scale="categorical", x_label="Practising", y_label="Learners", agg="COUNT"),
        _table("tb_lessons", "ds_lessons", [
            ("lesson", "string", "Lesson"), ("phase", "string", "Phase"), ("learners_opened", "integer", "Opened"),
            ("learners_past_learn", "integer", "Past Learn"), ("learners_reached_build", "integer", "Reached Build"),
            ("learners_reached_explain", "integer", "Reached Explain"), ("learners_finished", "integer", "Finished"),
            ("learners_in_progress", "integer", "Working on it"), ("learners_stalled", "integer", "Stalled 7+ days"),
            ("finish_rate", "percent", "Finish rate (settled learners)")],
            "Where each lesson loses people", "In course order; click a heading to re-sort. Lessons only peeked at count as opened, never as stalled",
            0, 12, W, 8, version=2),
    ])

    stuck = _page("stuck", "Where they're stuck", [
        _text("t_stuck", ["### Which lessons and questions trip people up, and who is stuck right now?\n", "\n",
                          "Stuck means: past Learn, needed help, not finished, last touched 7 to 30 days ago, and not moved on to later lessons. "
                          "Someone working on a lesson today is not stuck yet. Rates are shown with the number of people behind them."], 0, 0, 10, 2),
        _multi_select("f_part_stuck", "course_part", "Course part", by_part, 10, 0),
        _table("tb_needs_work", "ds_needs_work", [
            ("lesson", "string", "Lesson"), ("phase", "string", "Phase"), ("learners_past_learn", "integer", "Past Learn"),
            ("learners_stuck", "integer", "Stuck now"), ("warning_signs", "integer", "Warning signs (0 to 6)"), ("main_problem", "string", "Main problem"),
            ("finish_rate", "percent", "Finish rate"), ("check_on_own_rate", "percent", "Check on own"), ("practice_right_rate", "percent", "Practice right first time"),
            ("code_two_plus_hints_rate", "percent", "Code needing hint 2+"), ("explain_wrong_picks_per_learner", "float", "Explain wrong picks per learner"),
            ("still_stuck_per_learner", "float", "Still stuck per learner")],
            "Lessons to look at first", "Lessons with 5 or more learners past Learn; a sign counts when the lesson is clearly worse than the typical lesson. "
            "Empty until 10 lessons qualify. The same trusted function Genie uses", 0, 2, W, 7, version=2),
        _table("tb_check_q", "ds_check_questions", [
            ("lesson", "string", "Lesson"), ("question_number", "integer", "Check question"), ("learners_tried", "integer", "Tried"),
            ("on_their_own", "integer", "On their own"), ("with_help", "integer", "With a clue or another try"),
            ("answer_shown", "integer", "Answer shown"), ("not_right_yet", "integer", "Not right yet"), ("on_own_rate", "percent", "On their own (share)")],
            "Check questions people miss", "Lowest share on their own first; read it with the number tried", 0, 9, 6, 7, version=2),
        _table("tb_q1_wrong", "ds_q1_wrong_picks", [
            ("lesson", "string", "Lesson"), ("picked", "string", "Picked first"), ("right_answer", "string", "Right answer"),
            ("learners_picked_it", "integer", "Learners"), ("first_answers", "integer", "Of first answers"), ("share_of_first_answers", "percent", "Share")],
            "Wrong first picks on Check question 1", "The wrong option people choose shows the misunderstanding, in their words", 6, 9, 6, 7, version=2),
        _table("tb_practice", "ds_practice_missed", [
            ("lesson", "string", "Lesson"), ("question", "string", "Practice question"), ("learners_missed", "integer", "Missed it"),
            ("learners_did_practice", "integer", "Did the practice"), ("miss_rate", "percent", "Miss rate"),
            ("needed_a_clue", "integer", "Needed a clue"), ("needed_the_answer", "integer", "Needed the answer"),
            ("most_common_wrong_pick", "string", "Most common wrong pick")],
            "Practice questions missed most", "Latest run per learner. The most common wrong pick shows exactly what to explain better", 0, 16, W, 7, version=2),
        _table("tb_stuck", "ds_stuck", [
            ("learner_name", "string", "Learner"), ("status", "string", "Status"), ("lesson", "string", "Lesson"),
            ("furthest_step", "string", "Got as far as"), ("help_signals", "string", "What tripped them up"),
            ("first_check_picked", "string", "Check 1: picked"), ("first_check_right_answer", "string", "Check 1: right answer"),
            ("practice_missed_questions", "string", "Practice questions missed"), ("tutor_requests", "integer", "Tutor requests"),
            ("days_since_last_activity", "integer", "Quiet days")],
            "Who is stuck now", "The short list worth a friendly nudge, with what tripped each person up", 0, 23, W, 7, version=2),
    ])

    team = _page("team", "Team", [
        _text("t_team", ["### Where is each person, and what did they save to come back to?\n", "\n",
                         "One row per person. Progress comes from their saved lessons; days, Check answers and questions from what they did. "
                         "Check question 1 right first time counts the very first pick on each lesson."], 0, 0, W, 2),
        _table("tb_everyone", "ds_learners", [
            ("learner_name", "string", "Learner"), ("status", "string", "Status"), ("lessons_finished", "integer", "Lessons finished"),
            ("main_path_percent_done", "integer", "Main path done (%)"), ("platform_track_lessons_finished", "integer", "Track lessons finished"),
            ("current_lesson", "string", "On lesson"), ("practising", "string", "Practising"), ("last_active_date", "date", "Last learning day"),
            ("days_active_last_7", "integer", "Days (7d)"), ("days_active_last_28", "integer", "Days (28d)"),
            ("lessons_finished_last_28", "integer", "Finished (28d)"), ("first_check_answers_right", "integer", "Check 1 right first time"),
            ("first_check_answers", "integer", "Check 1 answered"), ("stuck_lessons", "integer", "Stuck on"),
            ("lessons_left_after_struggling", "integer", "Left after struggling"), ("typed_questions_last_7", "integer", "Questions (7d)"),
            ("study_items_open", "integer", "Study list open"), ("study_reviews_due", "integer", "Reviews due"), ("on_leaderboard", "string", "Leaderboard")],
            "Everyone", "Sort by any heading. One row per person, both saved copies merged", 0, 2, W, 9, version=2),
        _table("tb_team_week", "ds_team_week", [
            ("learner_name", "string", "Learner"), ("status", "string", "Status"), ("days_active", "integer", "Days this week"),
            ("days_active_week_before", "integer", "Days last week"), ("lessons_finished", "integer", "Finished this week"),
            ("lessons_finished_week_before", "integer", "Finished last week"), ("exercises_passed", "integer", "Exercises passed"),
            ("typed_questions", "integer", "Questions typed"), ("first_check_answers_right", "integer", "Check 1 right first time"),
            ("first_check_answers", "integer", "Check 1 answered"), ("stuck_lessons", "integer", "Stuck on")],
            "This week, per person", "Monday to now, next to the week before. The same trusted function Genie uses for how did everyone do", 0, 11, W, 7, version=2),
        _table("tb_study", "ds_study", [
            ("learner_name", "string", "Learner"), ("saved_text", "string", "Saved"), ("learner_note", "string", "Their note"),
            ("saved_from", "string", "From"), ("lesson", "string", "Lesson"), ("status", "string", "Status"),
            ("review_due", "string", "Review due"), ("follow_up_questions", "integer", "Follow-up questions"), ("saved_at", "datetime", "Saved")],
            "Study lists", "What people chose to come back to, in their own words. Open items first", 0, 18, W, 8, version=2),
    ])

    tutor = _page("tutor", "Questions and the tutor", [
        _text("t_tutor", ["### How much do people use the AI tutor, what for, and do its answers help?\n", "\n",
                          "The three numbers compare the last 7 days with the 7 days before. Got it and Still stuck are the ratings learners give an answer; "
                          "the app does not record which lesson a rating belongs to, so they are shown by week only. "
                          "Help with the use case a learner writes for themselves is private and not counted anywhere."], 0, 0, W, 2),
        _counter("c_typed", "ds_kpis", "typed_questions_7d", "typed_questions_prev_7d", "Typed questions",
                 "Questions people wrote themselves", 0, 2, 4),
        _counter("c_tutor_users", "ds_kpis", "tutor_users_7d", "tutor_users_prev_7d", "Learners using the tutor",
                 "Spread across people, or a few heavy users?", 4, 2, 4),
        _counter("c_got_it", "ds_kpis", "got_it_rate_7d", "got_it_rate_prev_7d", "Got it rate",
                 "Of rated answers, the share marked Got it", 8, 2, 4, fmt=PERCENT),
        _bar("b_tutor_week", "ds_tutor", "activity_week", "learner", "Tutor requests per week, by what for",
             "Lesson questions, code hints, reviews or the study list", 0, 5, 6,
             color="tutor_feature", x_label="Week", y_label="Requests", agg="COUNT"),
        _combo("cb_got_it", "ds_weekly", "week", [("got_it", "Got it"), ("still_stuck", "Still stuck")], [("got_it_rate", "Got it rate")],
               "Got it and Still stuck per week", "The rate next to how many ratings it rests on", 6, 5, 6, line_fmt=PERCENT),
        _bar("b_step", "ds_tutor", "lesson_step", "learner", "Where in a lesson people ask",
             "Asking mostly at Check or Build points to where the explanations fall short", 0, 10, 4,
             color=None, x_scale="categorical", x_label="Step", y_label="Requests", agg="COUNT", x_sort=STEP_ORDER),
        _table("tb_lesson_q", "ds_lessons", [
            ("lesson", "string", "Lesson"), ("phase", "string", "Phase"), ("typed_questions", "integer", "Typed questions"),
            ("still_stuck_presses", "integer", "Still stuck presses"), ("tutor_requests", "integer", "All requests"),
            ("learners_past_learn", "integer", "Learners past Learn")],
            "Lessons with the most questions", "Candidates for a clearer Learn card or a prepared answer; sort by Typed questions", 4, 10, 8, 5, version=2),
        _table("tb_questions", "ds_questions", [
            ("happened_at", "datetime", "When"), ("learner_name", "string", "Learner"), ("lesson", "string", "Lesson"),
            ("tutor_step", "string", "Step"), ("how_asked", "string", "How asked"), ("question_text", "string", "Question")],
            "Questions, newest first", "Their words: the most useful thing for a coaching chat", 0, 15, W, 8, version=2),
    ])

    notes = _page("notes", "Weekly notes", [
        _text("t_notes", ["### What does the weekly note say about each person?\n", "\n",
                          "A few plain sentences per learner per week, written by the app's model from that week's numbers. "
                          "An opinion to start a conversation, not a measurement; they are kept out of Genie."], 0, 0, W, 2),
        _table("tb_notes", "ds_notes", [
            ("learner_name", "string", "Learner"), ("week", "string", "Week"), ("note", "string", "Note"), ("written_at", "datetime", "Written")],
            "Weekly notes", "Newest week first", 0, 2, W, 8, version=2),
    ])
    return [filters, going, back, far, stuck, team, tutor, notes]


def dashboard(insights_catalog: str, genie_space_id: str | None = None) -> dict:
    """The whole dashboard, ready for the Lakeview API's ``serialized_dashboard``. With a Genie Agent id the
    Ask Genie button opens that curated agent (each viewer with their own rights); without one Genie is off,
    so no auto-made Genie answers with the publisher's rights."""
    sql = datasets(insights_catalog)
    ds = [{"name": name, "displayName": name.removeprefix("ds_").replace("_", " "), "queryLines": [query.strip()]}
          for name, query in sql.items()]
    genie = ({"isEnabled": True, "overrideId": genie_space_id, "enablementMode": "ENABLED"} if genie_space_id
             else {"isEnabled": False})
    return {"datasets": ds, "pages": pages(), "uiSettings": {"theme": THEME, "genieSpace": genie}}
