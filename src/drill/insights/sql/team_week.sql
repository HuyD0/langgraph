-- Trusted answer to "how did everyone do this week / last week?": one row per started learner for one week,
-- with the week before for comparison. Status and stuck lessons are as of today.
CREATE OR REPLACE FUNCTION `{insights_catalog}`.drill_insights.team_week(
  -- Text, not DATE: Genie refuses a trusted function with a DATE parameter ("argument type is not supported: date").
  for_week STRING DEFAULT '' COMMENT 'Any day in the week you want, written like 2026-10-14. Empty means the current week. Weeks run Monday to Sunday on UTC days.'
)
RETURNS TABLE (
  learner STRING COMMENT 'Work email of the learner.',
  learner_name STRING COMMENT 'Name taken from the email.',
  status STRING COMMENT 'Status as of today: Active, Drifting, Gone quiet or Started before tracking began.',
  week_start DATE COMMENT 'Monday of the week asked for.',
  days_active BIGINT COMMENT 'Days with a learning action that week.',
  days_active_week_before BIGINT COMMENT 'Days with a learning action the week before.',
  lessons_finished BIGINT COMMENT 'Lessons finished for the first time that week.',
  lessons_finished_week_before BIGINT COMMENT 'Lessons finished for the first time the week before.',
  exercises_passed BIGINT COMMENT 'Exercises passed for the first time that week.',
  typed_questions BIGINT COMMENT 'Questions they wrote to the tutor that week.',
  first_check_answers BIGINT COMMENT 'First answers to Check question 1 that week.',
  first_check_answers_right BIGINT COMMENT 'Of those, how many were right.',
  stuck_lessons BIGINT COMMENT 'Lessons they are stuck on, as of today.'
)
COMMENT 'One row per learner who has started, for one week (Monday to Sunday on UTC days), with the week before for comparison. Answers how everyone did this week or last week, who is ahead and who slowed down.'
RETURN
  WITH wk AS (
    -- The Monday of the week asked for; today is worked out as a UTC day, whatever the session time zone.
    SELECT CAST(date_trunc('WEEK', coalesce(try_to_date(nullif(trim(team_week.for_week), '')),
      date_from_unix_date(CAST(floor(unix_seconds(current_timestamp()) / 86400) AS INT)))) AS DATE) AS ws
  ),
  wa AS (
    SELECT
      a.learner,
      COUNT(DISTINCT CASE WHEN a.is_learning_action AND a.activity_week = wk.ws THEN a.activity_date END) AS days_active,
      COUNT(DISTINCT CASE WHEN a.is_learning_action AND a.activity_week = date_sub(wk.ws, 7) THEN a.activity_date END) AS days_active_before,
      COUNT_IF(a.activity_week = wk.ws AND a.activity_code = 'lesson_done' AND a.is_first_time) AS lessons_finished,
      COUNT_IF(a.activity_week = date_sub(wk.ws, 7) AND a.activity_code = 'lesson_done' AND a.is_first_time) AS lessons_finished_before,
      COUNT_IF(a.activity_week = wk.ws AND a.activity_code = 'solved' AND a.is_first_time) AS exercises_passed,
      COUNT_IF(a.activity_week = wk.ws AND a.is_typed_question) AS typed_questions,
      COUNT_IF(a.activity_week = wk.ws AND a.activity_code = 'checked' AND a.is_first_time AND a.check_first_answer_right IS NOT NULL) AS first_check_answers,
      COUNT_IF(a.activity_week = wk.ws AND a.activity_code = 'checked' AND a.is_first_time AND a.check_first_answer_right) AS first_check_answers_right
    FROM `{insights_catalog}`.drill_insights.activity a
    CROSS JOIN wk
    WHERE a.activity_week BETWEEN date_sub(wk.ws, 7) AND wk.ws
    GROUP BY a.learner
  )
  SELECT
    l.learner,
    l.learner_name,
    l.status,
    wk.ws AS week_start,
    coalesce(wa.days_active, 0) AS days_active,
    coalesce(wa.days_active_before, 0) AS days_active_week_before,
    coalesce(wa.lessons_finished, 0) AS lessons_finished,
    coalesce(wa.lessons_finished_before, 0) AS lessons_finished_week_before,
    coalesce(wa.exercises_passed, 0) AS exercises_passed,
    coalesce(wa.typed_questions, 0) AS typed_questions,
    coalesce(wa.first_check_answers, 0) AS first_check_answers,
    coalesce(wa.first_check_answers_right, 0) AS first_check_answers_right,
    l.stuck_lessons
  FROM `{insights_catalog}`.drill_insights.learners l
  CROSS JOIN wk
  LEFT JOIN wa ON wa.learner = l.learner
  WHERE l.has_started
