-- The course: one row per lesson in the version of the app running now.
-- Reads the raw lessons table only. Every other view joins to this one for numbers, titles and phases.
CREATE OR REPLACE VIEW `{insights_catalog}`.drill_insights.lessons (
  lesson_id COMMENT 'Short code of the lesson, for example split_by_key. Links the views together; learners never see it.',
  lesson_number COMMENT 'The number learners see. 2.11 is phase 2, lesson 11. P3.4 is part 3, lesson 4 of the Platform track. It is text, so sort by position, never by this.',
  lesson COMMENT 'Lesson number and title together, for example 2.11 followed by the title. Use this to name a lesson.',
  title COMMENT 'The lesson title as learners see it.',
  position COMMENT 'Place of the lesson in the course, 1 is the first. Main path lessons come first, then the Platform track. Sort lessons by this.',
  phase COMMENT 'Stage of the course: Frame, Design, Build and trace, Evaluate, Ship, Monitor, or Platform track (a separate side track, not a later stage). Lessons a team adds at work join one of these and count in its totals.',
  phase_order COMMENT 'Order of the phase in the course, 1 for Frame. Sort phases by this, not by name.',
  module COMMENT 'Title of the small group of lessons on one topic inside a phase, for example Use case and fit.',
  course_part COMMENT 'Main path (the six-phase AI engineering path) or Platform track (Azure Databricks, Terraform and Spacelift practice). Report them separately: someone on the track is not behind on the path.',
  lessons_in_phase COMMENT 'How many lessons the phase has in the version of the app running now.',
  check_right_option_index COMMENT 'Internal answer key: which option of Check question 1 is right, counted from 0 in the original order. Hidden from Genie.'
)
COMMENT 'The course: one row per lesson in the version of Daily Drill running now. The app rewrites its lesson list every time it starts, so lessons can appear or disappear. Count rows; never assume a number.'
AS
WITH base AS (
  SELECT
    lx.id,
    lx.`no` AS lesson_no,
    lx.`position` AS pos,
    lx.title,
    lx.phase,
    lx.module,
    -- Track lessons are numbered P<part>.<n>; everything else is the main path.
    -- Lessons a team adds (content packs) join a phase or the track and keep its name, so they need no case of their own.
    CASE WHEN lx.`no` LIKE 'P%' THEN lx.phase ELSE 'Main path' END AS part,
    lx.check_answer
  FROM `{lakebase_catalog}`.drill.lessons lx
),
ranked AS (
  SELECT base.*, MIN(pos) OVER (PARTITION BY phase) AS phase_start
  FROM base
)
SELECT
  id AS lesson_id,
  lesson_no AS lesson_number,
  concat_ws(' ', lesson_no, title) AS lesson,
  title,
  pos AS position,
  phase,
  CAST(DENSE_RANK() OVER (ORDER BY phase_start) AS INT) AS phase_order,
  module,
  part AS course_part,
  CAST(COUNT(*) OVER (PARTITION BY phase) AS INT) AS lessons_in_phase,
  check_answer AS check_right_option_index
FROM ranked
