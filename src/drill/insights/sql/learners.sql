-- One row per person who has opened Daily Drill: started or not, status in words, how far they got,
-- whether they are stuck, how they use the tutor. Days are UTC days except the streak, which follows
-- the calendar on the learner device.
CREATE OR REPLACE VIEW `{insights_catalog}`.drill_insights.learners (
  learner COMMENT 'Work email of the learner, in lower case. The only identity there is: no teams, managers or start dates.',
  learner_name COMMENT 'Name taken from the email, such as Sam Kim. Use it to show people.',
  has_started COMMENT 'True once the person has done a learning action, moved past the Learn step of a lesson, or passed an exercise. Count learners with this.',
  status COMMENT 'Active (last learning action 0 to 6 days ago), Drifting (7 to 20 days: missed one weekly cycle), Gone quiet (21 days or more: missed three), Not started (opened the app only), or Started before tracking began (progress exists but no action was ever recorded).',
  attention_reason COMMENT 'Why a manager may want to check in, in words. Empty when all is well.',
  first_active_date COMMENT 'The first day they did a learning action (a UTC day).',
  start_week COMMENT 'Monday of their first learning week. Groups learners into starting groups.',
  last_active_date COMMENT 'The last day they did a learning action (a UTC day).',
  days_since_last_active COMMENT 'Days from their last learning day to today. 0 means today. Empty if none is recorded.',
  last_visit_at COMMENT 'The last time they opened the app, even if they did nothing. Not the same as last active.',
  days_active_total COMMENT 'Different days with a learning action.',
  days_active_last_7 COMMENT 'Different days with a learning action in the last 7 days including today, 0 to 7.',
  days_active_last_28 COMMENT 'Different days with a learning action in the last 28 days including today.',
  longest_streak_days COMMENT 'Their longest run of days in a row with real study, by the calendar on their own device.',
  lessons_opened COMMENT 'Lessons they have opened.',
  lessons_finished COMMENT 'Lessons finished, all parts of the course together.',
  lessons_finished_last_28 COMMENT 'Lessons finished for the first time in the last 28 days. Lessons finished before actions were recorded have no date.',
  main_path_lessons_finished COMMENT 'Lessons finished on the main six-phase path.',
  platform_track_lessons_finished COMMENT 'Lessons finished on the Platform track.',
  main_path_percent_done COMMENT 'Share of the main path finished, as a whole number from 0 to 100. Someone practising only the Platform track is not behind.',
  exercises_passed COMMENT 'Different exercises passed at least once, including classic interview problems that are not lessons.',
  current_lesson COMMENT 'The lesson they last opened (number and title). It can be a finished or a Platform track lesson.',
  current_phase COMMENT 'Phase of the current lesson.',
  practising COMMENT 'What they chose to practise: AI engineering path, Platform track, Both, or Not chosen yet (the app then shows the AI path).',
  first_check_answers COMMENT 'Lessons where they have answered Check question 1.',
  first_check_answers_right COMMENT 'Of those, how many first picks were right.',
  stuck_lessons COMMENT 'Lessons they are stuck on right now: past Learn, needed help, not finished, last touched 7 to 30 days ago, and not moved on.',
  lessons_left_after_struggling COMMENT 'Lessons they struggled on and left unfinished, but moved on from or left more than 30 days ago. Not stuck, but worth knowing.',
  tutor_requests COMMENT 'All requests to the AI tutor: questions, hints, code reviews and study list help.',
  typed_questions COMMENT 'Questions they wrote to the tutor themselves, ever.',
  typed_questions_last_7 COMMENT 'Questions they wrote to the tutor in the last 7 days.',
  study_items_open COMMENT 'Items on their study list not yet marked Got it.',
  study_reviews_due COMMENT 'Study list items due for a spaced review now.',
  on_leaderboard COMMENT 'True when they have joined the weekly leaderboard (it is opt-in).'
)
COMMENT 'One row per person who has opened Daily Drill: whether they started, how active they are, how far they got, whether they are stuck and how they use the tutor. Count learners with has_started = true. Days are UTC days, except the streak, which follows the calendar on the learner device.'
AS
WITH today AS (
  SELECT date_from_unix_date(CAST(floor(unix_seconds(current_timestamp()) / 86400) AS INT)) AS d
),
act AS (
  SELECT
    a.learner,
    MIN(CASE WHEN a.is_learning_action THEN a.activity_date END) AS first_active_date,
    MAX(CASE WHEN a.is_learning_action THEN a.activity_date END) AS last_active_date,
    MIN(a.start_week) AS start_week,
    COUNT(DISTINCT CASE WHEN a.is_learning_action THEN a.activity_date END) AS days_active_total,
    COUNT(DISTINCT CASE WHEN a.is_learning_action AND a.activity_date >= date_sub(today.d, 6) THEN a.activity_date END) AS days_active_last_7,
    COUNT(DISTINCT CASE WHEN a.is_learning_action AND a.activity_date >= date_sub(today.d, 27) THEN a.activity_date END) AS days_active_last_28,
    COUNT_IF(a.activity_code = 'lesson_done' AND a.is_first_time AND a.activity_date >= date_sub(today.d, 27)) AS lessons_finished_last_28,
    COUNT_IF(a.activity_code = 'asked') AS tutor_requests,
    COUNT_IF(a.is_typed_question) AS typed_questions,
    COUNT_IF(a.is_typed_question AND a.activity_date >= date_sub(today.d, 6)) AS typed_questions_last_7
  FROM `{insights_catalog}`.drill_insights.activity a
  CROSS JOIN today
  GROUP BY a.learner
),
prog AS (
  SELECT
    p.learner,
    MAX(p.saved_at) AS last_visit_at,
    max_by(p.current_lesson_id, CASE WHEN p.current_lesson_id IS NOT NULL THEN p.saved_epoch END) AS current_lesson_id,
    max_by(p.focus, CASE WHEN p.focus IS NOT NULL THEN p.saved_epoch END) AS focus
  FROM `{insights_catalog}`.drill_insights.progress_docs p
  GROUP BY p.learner
),
solved AS (
  SELECT p.learner, COUNT(DISTINCT s.problem_id) AS exercises_passed
  FROM `{insights_catalog}`.drill_insights.progress_docs p
  LATERAL VIEW explode(p.solved) s AS problem_id, problem_json
  GROUP BY p.learner
),
study_days AS (
  SELECT DISTINCT p.learner, try_cast(dy.d AS DATE) AS study_day
  FROM `{insights_catalog}`.drill_insights.progress_docs p
  LATERAL VIEW explode(p.study_days) dy AS d
),
runs AS (
  -- Days in a row share a run key: the day minus its rank is the same for every day of one run.
  SELECT
    sd.learner,
    sd.study_day,
    date_sub(sd.study_day, CAST(ROW_NUMBER() OVER (PARTITION BY sd.learner ORDER BY sd.study_day) AS INT)) AS run_key
  FROM study_days sd
  WHERE sd.study_day IS NOT NULL
),
streaks AS (
  SELECT r.learner, MAX(r.run_days) AS longest_streak_days
  FROM (SELECT learner, run_key, COUNT(*) AS run_days FROM runs GROUP BY learner, run_key) r
  GROUP BY r.learner
),
done AS (
  SELECT
    ll.learner,
    COUNT(*) AS lessons_opened,
    COUNT_IF(ll.furthest_step_number >= 1) AS lessons_past_learn,
    COUNT_IF(ll.is_finished) AS lessons_finished,
    COUNT_IF(ll.is_finished AND ll.course_part = 'Main path') AS main_path_lessons_finished,
    COUNT_IF(ll.is_finished AND ll.course_part = 'Platform track') AS platform_track_lessons_finished,
    COUNT_IF(ll.first_check_answer_right IS NOT NULL) AS first_check_answers,
    COUNT_IF(ll.first_check_answer_right) AS first_check_answers_right,
    COUNT_IF(ll.is_stuck) AS stuck_lessons,
    COUNT_IF(ll.left_unfinished_after_struggling) AS lessons_left_after_struggling
  FROM `{insights_catalog}`.drill_insights.learner_lessons ll
  GROUP BY ll.learner
),
study AS (
  SELECT si.learner, COUNT_IF(si.status = 'Open') AS study_items_open, COUNT_IF(si.review_due) AS study_reviews_due
  FROM `{insights_catalog}`.drill_insights.study_items si
  GROUP BY si.learner
),
on_board AS (
  SELECT DISTINCT lower(bo.owner) AS learner
  FROM `{lakebase_catalog}`.drill.board bo
  WHERE lower(bo.owner) LIKE '%@%'
),
people AS (
  SELECT learner FROM prog
  UNION
  SELECT learner FROM act
),
base AS (
  SELECT
    pp.learner,
    (coalesce(a.days_active_total, 0) > 0 OR coalesce(d.lessons_past_learn, 0) > 0 OR coalesce(sv.exercises_passed, 0) > 0) AS has_started,
    datediff(today.d, a.last_active_date) AS days_since
  FROM people pp
  CROSS JOIN today
  LEFT JOIN act a ON a.learner = pp.learner
  LEFT JOIN done d ON d.learner = pp.learner
  LEFT JOIN solved sv ON sv.learner = pp.learner
)
SELECT
  b.learner,
  trim(initcap(regexp_replace(substring_index(b.learner, '@', 1), '[._-]+', ' '))) AS learner_name,
  b.has_started,
  CASE
    WHEN NOT b.has_started THEN 'Not started'
    WHEN b.days_since IS NULL THEN 'Started before tracking began'
    WHEN b.days_since <= 6 THEN 'Active'
    WHEN b.days_since <= 20 THEN 'Drifting'
    ELSE 'Gone quiet'
  END AS status,
  NULLIF(concat_ws('; ',
    CASE WHEN NOT b.has_started THEN 'Opened the app but has not begun a lesson' END,
    CASE WHEN b.has_started AND b.days_since >= 7 THEN concat('Nothing done for ', CAST(b.days_since AS STRING), ' days') END,
    CASE WHEN coalesce(d.stuck_lessons, 0) > 0 THEN concat('Stuck on ', CAST(d.stuck_lessons AS STRING), ' unfinished lesson(s)') END), '') AS attention_reason,
  a.first_active_date,
  a.start_week,
  a.last_active_date,
  b.days_since AS days_since_last_active,
  p.last_visit_at,
  coalesce(a.days_active_total, 0) AS days_active_total,
  coalesce(a.days_active_last_7, 0) AS days_active_last_7,
  coalesce(a.days_active_last_28, 0) AS days_active_last_28,
  coalesce(s.longest_streak_days, 0) AS longest_streak_days,
  coalesce(d.lessons_opened, 0) AS lessons_opened,
  coalesce(d.lessons_finished, 0) AS lessons_finished,
  coalesce(a.lessons_finished_last_28, 0) AS lessons_finished_last_28,
  coalesce(d.main_path_lessons_finished, 0) AS main_path_lessons_finished,
  coalesce(d.platform_track_lessons_finished, 0) AS platform_track_lessons_finished,
  -- The course size is a scalar subquery, not a one-row CTE joined in: over a Lakebase catalog, a CTE that is an
  -- aggregate with no GROUP BY comes back as every input row once a query stops reading its column (seen 2026-11-01:
  -- SELECT COUNT(*) FROM learners gave the number of lessons). A scalar subquery cannot multiply rows.
  CAST(round(100 * try_divide(coalesce(d.main_path_lessons_finished, 0),
    (SELECT COUNT_IF(course_part = 'Main path') FROM `{insights_catalog}`.drill_insights.lessons))) AS INT) AS main_path_percent_done,
  coalesce(sv.exercises_passed, 0) AS exercises_passed,
  coalesce(cl.lesson, p.current_lesson_id) AS current_lesson,
  cl.phase AS current_phase,
  CASE p.focus WHEN 'ai' THEN 'AI engineering path' WHEN 'platform' THEN 'Platform track' WHEN 'both' THEN 'Both' ELSE 'Not chosen yet' END AS practising,
  coalesce(d.first_check_answers, 0) AS first_check_answers,
  coalesce(d.first_check_answers_right, 0) AS first_check_answers_right,
  coalesce(d.stuck_lessons, 0) AS stuck_lessons,
  coalesce(d.lessons_left_after_struggling, 0) AS lessons_left_after_struggling,
  coalesce(a.tutor_requests, 0) AS tutor_requests,
  coalesce(a.typed_questions, 0) AS typed_questions,
  coalesce(a.typed_questions_last_7, 0) AS typed_questions_last_7,
  coalesce(st.study_items_open, 0) AS study_items_open,
  coalesce(st.study_reviews_due, 0) AS study_reviews_due,
  bd.learner IS NOT NULL AS on_leaderboard
FROM base b
LEFT JOIN prog p ON p.learner = b.learner
LEFT JOIN act a ON a.learner = b.learner
LEFT JOIN done d ON d.learner = b.learner
LEFT JOIN solved sv ON sv.learner = b.learner
LEFT JOIN streaks s ON s.learner = b.learner
LEFT JOIN study st ON st.learner = b.learner
LEFT JOIN on_board bd ON bd.learner = b.learner
LEFT JOIN `{insights_catalog}`.drill_insights.lessons cl ON cl.lesson_id = p.current_lesson_id
