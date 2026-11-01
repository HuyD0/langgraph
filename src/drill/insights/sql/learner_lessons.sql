-- Where each learner stands on each lesson they have opened: one row per learner per lesson.
-- Built from the saved progress (both copies of a person merged) plus their recorded actions.
-- Stuck means: past Learn, not finished, needed help, last touched 7 to 30 days ago, and the learner has not
-- moved on (it is their current lesson, or no later lesson was finished after it). Older or moved-on struggles
-- are counted apart as left_unfinished_after_struggling.
CREATE OR REPLACE VIEW `{insights_catalog}`.drill_insights.learner_lessons (
  learner COMMENT 'Work email of the learner, in lower case.',
  learner_name COMMENT 'Name taken from the email, such as Sam Kim. Use it to show people.',
  lesson_id COMMENT 'Short code of the lesson. Links to lesson_summary.lesson_id.',
  lesson COMMENT 'Lesson number and title together. Use this to name a lesson.',
  lesson_number COMMENT 'The number learners see, like 2.11 or P3.4. Text, so sort by position.',
  phase COMMENT 'Stage of the course: Frame, Design, Build and trace, Evaluate, Ship, Monitor, Platform track, or No longer in the course (removed after the learner opened it).',
  phase_order COMMENT 'Order of the phase, 1 for Frame. Empty for lessons no longer in the course.',
  course_part COMMENT 'Main path, Platform track or No longer in the course. Report them separately.',
  position COMMENT 'Place of the lesson in the course. Sort lessons by this.',
  furthest_step COMMENT 'The furthest of the four steps reached: Learn, Check, Build (called Practice on question lessons) or Explain. A finished lesson counts as Explain. Learners can skip ahead, so this is how far they got, not proof they did every step.',
  furthest_step_number COMMENT 'The same step as a number: 0 Learn, 1 Check, 2 Build, 3 Explain.',
  is_finished COMMENT 'True when the learner pressed Finish on this lesson, on any of their saved copies. A finished lesson stays finished.',
  first_finished_date COMMENT 'The day they first finished it, by the calendar on the learner device; otherwise the UTC day it was recorded. Empty if not finished, or finished before dates were kept.',
  is_current_lesson COMMENT 'True when this is the lesson they last opened (or the next one after their last finish).',
  first_check_answer_right COMMENT 'Check question 1 only: true when their very first pick was right, false when wrong, empty if not answered. Judged by the option words recorded at the time when they exist, so rewording the question later does not change it.',
  first_check_picked COMMENT 'Check question 1 only: the words of the option they picked first. Empty for older answers.',
  first_check_right_answer COMMENT 'Check question 1 only: the words of the right option at the time. Empty for older answers.',
  check_q1_result COMMENT 'How Check question 1 went: On their own, With a clue or another try, Answer shown, or Tried, not right yet. Taken from the first time through when the app kept it; only when that is missing, from the current attempt (see check_results_from). Empty if not tried.',
  check_q2_result COMMENT 'The same for Check question 2. A few lessons have only one Check question.',
  check_q3_result COMMENT 'The same for Check question 3.',
  check_results_from COMMENT 'Where the three Check results come from: First time through (kept by the app at the first finish) or Current attempt (the marks and wrong tries of the attempt in progress, which Try the check again resets). Empty if no Check question was tried.',
  check_questions_tried COMMENT 'Check questions (0 to 3) they have tried, whether or not they got them right yet.',
  check_questions_on_own COMMENT 'Check questions they got right on the first pick without a clue.',
  check_answers_shown COMMENT 'Check questions where they asked to see the answer.',
  practice_right_first_time COMMENT 'Practice-question lessons only: questions right on the first try in their latest run.',
  practice_questions COMMENT 'Practice-question lessons only: questions in that latest run. Empty if they never finished the practice inside the lesson.',
  practice_missed COMMENT 'Practice questions not right first time in the latest run, each with the wrong options picked and whether a clue or the answer was shown. A list; hidden from Genie.',
  explain_gaps_done COMMENT 'True when they filled every gap in the Explain sentence.',
  explain_wrong_picks COMMENT 'Wrong words picked while filling the Explain gaps, running total for this lesson.',
  explain_answers_shown COMMENT 'Explain gaps where they asked to see the word.',
  exercise_solved COMMENT 'True when they passed this lesson exercise at least once (code tests passed, practice set finished, or team exercise done). A lesson can be finished without it.',
  exercise_solved_how COMMENT 'How they passed it most recently: Code, Practice questions or Team exercise. Empty if not passed.',
  code_hint_level COMMENT 'Code exercises only: the highest hint step used, 0 none to 3. Step 1 can be just Show the pattern, so 2 or more means real help. Never compare or average with practice results.',
  tutor_requests COMMENT 'Requests to the AI tutor about this lesson: questions, hints, code reviews and study list help.',
  typed_questions COMMENT 'Questions about this lesson they wrote to the tutor themselves.',
  still_stuck_presses COMMENT 'Times they pressed Still stuck after a tutor answer on this lesson.',
  needed_help COMMENT 'True when any sign of difficulty shows: a wrong first pick on Check question 1, a Check answer shown, a Check question not right yet, code hint step 2 or more, fewer than half the practice questions right first time, Explain words shown, or Still stuck pressed.',
  help_signals COMMENT 'Which signs of difficulty apply, in words. Empty when none.',
  last_activity_at COMMENT 'The last time the app recorded a learning action on this lesson. Empty if none was recorded (for example, work done before actions were kept).',
  days_since_last_activity COMMENT 'Days from that last action to today (UTC days). Empty if none was recorded.',
  moved_on COMMENT 'True when the learner finished a later lesson in the course after their last action on this one: they left it behind rather than being held up by it.',
  is_stalled COMMENT 'True when they went past the Learn step, have not finished, and their last recorded action on it is 7 or more days old. A week is the rhythm of the app. Lessons only peeked at, or with no recorded action, are never stalled.',
  is_stuck COMMENT 'True when the lesson is stalled, they needed help on it, the last action is 7 to 30 days old, and they have not moved on (it is their current lesson, or no later lesson was finished after it). This is what stuck means: held up right now.',
  left_unfinished_after_struggling COMMENT 'True when they struggled on the lesson and left it unfinished, but it no longer counts as stuck: they moved on to later lessons, or the last action is more than 30 days old.'
)
COMMENT 'Where each learner stands on each lesson they have opened: one row per learner per lesson, from their saved progress (both copies merged when a person has two) plus their recorded actions. It is the truth for finished or not, but has no history. Lessons never opened have no row. Stuck means held up right now (7 to 30 quiet days, not moved on, needed help); older struggles are left_unfinished_after_struggling. The use case a learner writes for themselves and their own Explain sentence are never read.'
AS
WITH today AS (
  -- Today as a UTC day, by arithmetic on the clock, whatever the session time zone.
  SELECT date_from_unix_date(CAST(floor(unix_seconds(current_timestamp()) / 86400) AS INT)) AS d
),
opened AS (
  SELECT p.learner, p.saved_epoch, x.lesson_id, x.info
  FROM `{insights_catalog}`.drill_insights.progress_docs p
  LATERAL VIEW explode(p.lessons) x AS lesson_id, info
),
merged AS (
  -- A person can have two progress copies (app and laptop): finished and furthest step take the best of both,
  -- the details come from the newest copy that has them.
  SELECT
    o.learner,
    o.lesson_id,
    bool_or(coalesce(o.info.done, false)) AS is_finished,
    greatest(max(coalesce(o.info.step, 0)), CASE WHEN bool_or(coalesce(o.info.done, false)) THEN 3 ELSE 0 END) AS step_n,
    max_by(o.info.checked, CASE WHEN o.info.checked IS NOT NULL THEN o.saved_epoch END) AS checked,
    max_by(o.info.checks, CASE WHEN o.info.checks IS NOT NULL THEN o.saved_epoch END) AS checks,
    max_by(o.info.`first`, CASE WHEN o.info.`first` IS NOT NULL THEN o.saved_epoch END) AS first_result,
    max_by(o.info.practice, CASE WHEN o.info.practice IS NOT NULL THEN o.saved_epoch END) AS practice,
    max_by(o.info.`explain`, CASE WHEN o.info.`explain` IS NOT NULL THEN o.saved_epoch END) AS explain_help
  FROM opened o
  GROUP BY o.learner, o.lesson_id
),
current_lesson AS (
  SELECT p.learner, max_by(p.current_lesson_id, CASE WHEN p.current_lesson_id IS NOT NULL THEN p.saved_epoch END) AS lesson_id
  FROM `{insights_catalog}`.drill_insights.progress_docs p
  GROUP BY p.learner
),
solved AS (
  SELECT
    p.learner,
    s.problem_id,
    max_by(coalesce(get_json_object(s.problem_json, '$.mode'), 'code'), p.saved_epoch) AS mode,
    max_by(try_cast(get_json_object(s.problem_json, '$.hints') AS INT), p.saved_epoch) AS hints
  FROM `{insights_catalog}`.drill_insights.progress_docs p
  LATERAL VIEW explode(p.solved) s AS problem_id, problem_json
  GROUP BY p.learner, s.problem_id
),
ev AS (
  SELECT
    a.learner,
    a.lesson_id,
    MIN(CASE WHEN a.activity_code = 'lesson_done' THEN a.happened_at END) AS first_done_at,
    MIN(CASE WHEN a.activity_code = 'lesson_done' THEN a.activity_date END) AS first_done_date,
    min_by(a.check_first_answer_right, CASE WHEN a.activity_code = 'checked' THEN a.happened_at END) AS q1_right_event,
    min_by(a.check_picked_text, CASE WHEN a.activity_code = 'checked' THEN a.happened_at END) AS q1_picked,
    min_by(a.check_right_text, CASE WHEN a.activity_code = 'checked' THEN a.happened_at END) AS q1_right_text,
    MAX(a.hint_level) AS top_hint_asked,
    COUNT_IF(a.activity_code = 'asked') AS tutor_requests,
    COUNT_IF(a.is_typed_question) AS typed_questions,
    COUNT_IF(a.is_still_stuck) AS still_stuck_presses,
    MAX(CASE WHEN a.is_learning_action THEN a.happened_at END) AS last_activity_at,
    MAX(CASE WHEN a.is_learning_action THEN a.activity_date END) AS last_activity_date
  FROM `{insights_catalog}`.drill_insights.activity a
  WHERE a.lesson_id IS NOT NULL
  GROUP BY a.learner, a.lesson_id
),
base AS (
  SELECT
    m.learner,
    m.lesson_id,
    l.lesson,
    l.lesson_number,
    l.phase,
    l.phase_order,
    l.course_part,
    l.`position`,
    m.step_n,
    m.is_finished,
    m.first_result,
    m.practice,
    m.explain_help,
    coalesce(m.lesson_id = c.lesson_id, false) AS is_current,
    coalesce(e.q1_right_event, m.checked = l.check_right_option_index) AS q1_right,
    e.q1_picked,
    e.q1_right_text,
    -- Check results: the first time through when the app kept it, else the attempt in progress.
    m.first_result.`check` IS NOT NULL AS has_first_check,
    coalesce(m.first_result.`check`, m.checks.marks) AS marks,
    CASE WHEN m.first_result.`check` IS NULL THEN m.checks.tried END AS tried,
    sv.problem_id IS NOT NULL AS exercise_solved,
    sv.mode,
    greatest(CASE WHEN sv.mode = 'code' THEN sv.hints END, e.top_hint_asked) AS code_hint_level,
    coalesce(e.tutor_requests, 0) AS tutor_requests,
    coalesce(e.typed_questions, 0) AS typed_questions,
    coalesce(e.still_stuck_presses, 0) AS still_stuck_presses,
    e.first_done_at,
    e.first_done_date,
    e.last_activity_at,
    e.last_activity_date
  FROM merged m
  LEFT JOIN `{insights_catalog}`.drill_insights.lessons l ON l.lesson_id = m.lesson_id
  LEFT JOIN current_lesson c ON c.learner = m.learner
  LEFT JOIN solved sv ON sv.learner = m.learner AND sv.problem_id = m.lesson_id
  LEFT JOIN ev e ON e.learner = m.learner AND e.lesson_id = m.lesson_id
),
q_results AS (
  SELECT
    b.*,
    CASE try_element_at(b.marks, 1)
      WHEN 'sign' THEN 'On their own'
      WHEN 'knot' THEN 'With a clue or another try'
      WHEN 'curtain' THEN 'Answer shown'
      ELSE CASE
        WHEN coalesce(size(try_element_at(b.tried, 1)), 0) > 0 OR (NOT b.has_first_check AND b.q1_right = false) THEN 'Tried, not right yet'
        WHEN NOT b.has_first_check AND b.q1_right THEN 'On their own'
      END
    END AS q1_result,
    CASE try_element_at(b.marks, 2)
      WHEN 'sign' THEN 'On their own'
      WHEN 'knot' THEN 'With a clue or another try'
      WHEN 'curtain' THEN 'Answer shown'
      ELSE CASE WHEN coalesce(size(try_element_at(b.tried, 2)), 0) > 0 THEN 'Tried, not right yet' END
    END AS q2_result,
    CASE try_element_at(b.marks, 3)
      WHEN 'sign' THEN 'On their own'
      WHEN 'knot' THEN 'With a clue or another try'
      WHEN 'curtain' THEN 'Answer shown'
      ELSE CASE WHEN coalesce(size(try_element_at(b.tried, 3)), 0) > 0 THEN 'Tried, not right yet' END
    END AS q3_result
  FROM base b
),
counted AS (
  SELECT
    r.*,
    (CASE WHEN r.q1_result IS NOT NULL THEN 1 ELSE 0 END
      + CASE WHEN r.q2_result IS NOT NULL THEN 1 ELSE 0 END
      + CASE WHEN r.q3_result IS NOT NULL THEN 1 ELSE 0 END) AS check_tried,
    (CASE WHEN r.q1_result = 'On their own' THEN 1 ELSE 0 END
      + CASE WHEN r.q2_result = 'On their own' THEN 1 ELSE 0 END
      + CASE WHEN r.q3_result = 'On their own' THEN 1 ELSE 0 END) AS check_own,
    (CASE WHEN r.q1_result = 'Answer shown' THEN 1 ELSE 0 END
      + CASE WHEN r.q2_result = 'Answer shown' THEN 1 ELSE 0 END
      + CASE WHEN r.q3_result = 'Answer shown' THEN 1 ELSE 0 END) AS check_shown,
    (CASE WHEN r.q1_result = 'Tried, not right yet' THEN 1 ELSE 0 END
      + CASE WHEN r.q2_result = 'Tried, not right yet' THEN 1 ELSE 0 END
      + CASE WHEN r.q3_result = 'Tried, not right yet' THEN 1 ELSE 0 END) AS check_not_yet
  FROM q_results r
),
signals AS (
  SELECT
    c.*,
    NULLIF(concat_ws('; ',
      CASE WHEN c.q1_right = false THEN 'Wrong first pick on Check question 1' END,
      CASE WHEN c.check_shown > 0 THEN 'Needed a Check answer shown' END,
      CASE WHEN c.check_not_yet > 0 THEN 'A Check question not right yet' END,
      CASE WHEN c.code_hint_level >= 2 THEN concat('Needed hint step ', CAST(c.code_hint_level AS STRING), ' on the code') END,
      CASE WHEN c.practice.total > 0 AND c.practice.`right` * 2 < c.practice.total
        THEN concat(CAST(c.practice.`right` AS STRING), ' of ', CAST(c.practice.total AS STRING), ' practice questions right first time') END,
      CASE WHEN c.explain_help.answers > 0 THEN 'Needed Explain words shown' END,
      CASE WHEN c.still_stuck_presses > 0 THEN 'Pressed Still stuck on the tutor' END), '') AS help_signals,
    -- Both sides are UTC days (activity_date comes from the seconds), so no cast through the session time zone.
    datediff(today.d, c.last_activity_date) AS days_since,
    -- The latest first-finish time among lessons later in the course: did they move on past this one?
    MAX(c.first_done_at) OVER (PARTITION BY c.learner ORDER BY c.`position` ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING) AS later_finish_at
  FROM counted c
  CROSS JOIN today
),
flags AS (
  SELECT
    s.*,
    s.help_signals IS NOT NULL AS needed_help,
    coalesce(s.later_finish_at > s.last_activity_at, false) AS moved_on,
    NOT s.is_finished AND s.step_n >= 1 AND s.days_since >= 7 AS stalled
  FROM signals s
)
SELECT
  f.learner,
  trim(initcap(regexp_replace(substring_index(f.learner, '@', 1), '[._-]+', ' '))) AS learner_name,
  f.lesson_id,
  coalesce(f.lesson, f.lesson_id) AS lesson,
  f.lesson_number,
  coalesce(f.phase, 'No longer in the course') AS phase,
  f.phase_order,
  coalesce(f.course_part, 'No longer in the course') AS course_part,
  f.`position`,
  CASE f.step_n WHEN 0 THEN 'Learn' WHEN 1 THEN 'Check' WHEN 2 THEN 'Build' ELSE 'Explain' END AS furthest_step,
  CAST(f.step_n AS INT) AS furthest_step_number,
  f.is_finished,
  CASE WHEN f.is_finished THEN coalesce(try_cast(f.first_result.`date` AS DATE), f.first_done_date) END AS first_finished_date,
  f.is_current AS is_current_lesson,
  f.q1_right AS first_check_answer_right,
  f.q1_picked AS first_check_picked,
  f.q1_right_text AS first_check_right_answer,
  f.q1_result AS check_q1_result,
  f.q2_result AS check_q2_result,
  f.q3_result AS check_q3_result,
  CASE WHEN f.check_tried = 0 THEN NULL WHEN f.has_first_check THEN 'First time through' ELSE 'Current attempt' END AS check_results_from,
  f.check_tried AS check_questions_tried,
  f.check_own AS check_questions_on_own,
  f.check_shown AS check_answers_shown,
  f.practice.`right` AS practice_right_first_time,
  f.practice.total AS practice_questions,
  f.practice.missed AS practice_missed,
  coalesce(f.explain_help.done, false) AS explain_gaps_done,
  f.explain_help.wrong AS explain_wrong_picks,
  f.explain_help.answers AS explain_answers_shown,
  f.exercise_solved,
  CASE WHEN NOT f.exercise_solved THEN NULL WHEN f.mode = 'practice' THEN 'Practice questions' WHEN f.mode = 'pack' THEN 'Team exercise' ELSE 'Code' END AS exercise_solved_how,
  f.code_hint_level,
  f.tutor_requests,
  f.typed_questions,
  f.still_stuck_presses,
  f.needed_help,
  f.help_signals,
  f.last_activity_at,
  f.days_since AS days_since_last_activity,
  f.moved_on,
  coalesce(f.stalled, false) AS is_stalled,
  coalesce(f.stalled AND f.needed_help AND f.days_since <= 30 AND (f.is_current OR NOT f.moved_on), false) AS is_stuck,
  coalesce(f.stalled AND f.needed_help AND NOT (f.days_since <= 30 AND (f.is_current OR NOT f.moved_on)), false) AS left_unfinished_after_struggling
FROM flags f
