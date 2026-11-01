-- The model-written weekly note per learner per week. Dashboard only; kept out of Genie on purpose.
CREATE OR REPLACE VIEW `{insights_catalog}`.drill_insights.weekly_notes (
  learner COMMENT 'Work email of the learner, in lower case.',
  learner_name COMMENT 'Name taken from the email, such as Sam Kim.',
  week COMMENT 'The week the note is about, written as year and week number, such as 2026-W44 (the week of Monday 26 October 2026). Sorts correctly as text.',
  note COMMENT 'A few plain sentences the app model wrote for managers from the numbers of that week. An opinion to start a conversation, not a measurement.',
  written_at COMMENT 'When the note was last rewritten.'
)
COMMENT 'Dashboard only, not for Genie: one row per learner per week with the model-written weekly note. Rewritten about once a day while the app runs, and only for learners active in the last 7 days. An opinion, not a measure.'
AS
SELECT
  lower(sm.owner) AS learner,
  trim(initcap(regexp_replace(substring_index(lower(sm.owner), '@', 1), '[._-]+', ' '))) AS learner_name,
  sm.week,
  sm.summary AS note,
  timestamp_seconds(sm.made_at) AS written_at
FROM `{lakebase_catalog}`.drill.summaries sm
WHERE lower(sm.owner) LIKE '%@%'
