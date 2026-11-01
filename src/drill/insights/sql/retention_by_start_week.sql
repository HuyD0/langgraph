-- Trusted answer to "do people come back?": for each start week, how many of the learners who began
-- then did a learning action again 1, 2, 3 and more weeks later. Learning actions only.
CREATE OR REPLACE FUNCTION `{insights_catalog}`.drill_insights.retention_by_start_week(
  weeks_back INT DEFAULT 12 COMMENT 'How many recent start weeks to include. 12 is about the last three months.'
)
RETURNS TABLE (
  start_week DATE COMMENT 'Monday of the week these learners first did a learning action.',
  learners_started BIGINT COMMENT 'How many learners had their first learning action that week.',
  week_number INT COMMENT 'Weeks after the start week: 0 is the start week itself, 1 the week after, up to the current week.',
  learners_active BIGINT COMMENT 'How many of those learners did a learning action that week. 0 when nobody came back.',
  share_active DOUBLE COMMENT 'learners_active divided by learners_started, from 0 to 1.'
)
COMMENT 'Do people come back? For each start week, how many of the learners who began then did a learning action again 1, 2, 3 and more weeks later. Weeks run Monday to Sunday on UTC days; the current week is still in progress, so its numbers will grow.'
RETURN
  WITH this_week AS (
    -- Monday of the current week, from the UTC day, whatever the session time zone.
    SELECT CAST(date_trunc('WEEK', date_from_unix_date(CAST(floor(unix_seconds(current_timestamp()) / 86400) AS INT))) AS DATE) AS monday
  ),
  la AS (
    SELECT a.learner, a.start_week, a.weeks_since_start
    FROM `{insights_catalog}`.drill_insights.activity a
    WHERE a.is_learning_action
  ),
  starts AS (
    SELECT la.start_week, COUNT(DISTINCT la.learner) AS learners_started
    FROM la
    CROSS JOIN this_week
    WHERE la.start_week >= date_sub(this_week.monday, 7 * retention_by_start_week.weeks_back)
    GROUP BY la.start_week
  ),
  active AS (
    SELECT la.start_week, la.weeks_since_start AS week_number, COUNT(DISTINCT la.learner) AS learners_active
    FROM la
    GROUP BY la.start_week, la.weeks_since_start
  ),
  grid AS (
    -- Every week from the start week to the current week, so weeks with nobody back show as 0.
    SELECT
      s.start_week,
      s.learners_started,
      explode(sequence(0, GREATEST(0, CAST(datediff(this_week.monday, s.start_week) DIV 7 AS INT)))) AS week_number
    FROM starts s
    CROSS JOIN this_week
  )
  SELECT
    g.start_week,
    g.learners_started,
    g.week_number,
    coalesce(ac.learners_active, 0) AS learners_active,
    try_divide(coalesce(ac.learners_active, 0), g.learners_started) AS share_active
  FROM grid g
  LEFT JOIN active ac ON ac.start_week = g.start_week AND ac.week_number = g.week_number
