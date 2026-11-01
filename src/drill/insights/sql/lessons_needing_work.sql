-- Trusted answer to "which lessons need work?": six warning signs, each counted only when the lesson is
-- clearly worse than the typical lesson on it. Returns nothing while fewer than 10 lessons have enough learners.
CREATE OR REPLACE FUNCTION `{insights_catalog}`.drill_insights.lessons_needing_work(
  min_learners INT DEFAULT 5 COMMENT 'Only lessons at least this many learners went past the Learn step on, and only signs resting on at least this many answers, solvers or events. Below 5, one person moves a rate by 20 points or more.'
)
RETURNS TABLE (
  lesson STRING COMMENT 'Lesson number and title.',
  phase STRING COMMENT 'Phase of the course, or Platform track.',
  course_part STRING COMMENT 'Main path or Platform track.',
  position INT COMMENT 'Place in the course. Sort by this to read in course order.',
  learners_past_learn BIGINT COMMENT 'Learners who reached Check or further.',
  learners_stalled BIGINT COMMENT 'Learners past Learn, unfinished, untouched for 7 or more days.',
  learners_stuck BIGINT COMMENT 'Learners stuck on it right now.',
  finish_rate DOUBLE COMMENT 'Of settled learners (finished or stalled), the share who finished, 0 to 1. People working on it now are left out.',
  check_on_own_rate DOUBLE COMMENT 'Check questions right on the first pick without a clue, divided by Check questions tried, 0 to 1.',
  practice_right_rate DOUBLE COMMENT 'Practice-question lessons only: share right first time in each learner latest run, 0 to 1.',
  code_two_plus_hints_rate DOUBLE COMMENT 'Code exercises only: share of code solvers who needed hint step 2 or more, 0 to 1.',
  explain_wrong_picks_per_learner DOUBLE COMMENT 'Average wrong word picks among learners who filled every Explain gap.',
  still_stuck_per_learner DOUBLE COMMENT 'Still stuck presses per learner past Learn.',
  warning_signs INT COMMENT 'How many of the six signs count against this lesson (0 to 6).',
  main_problem STRING COMMENT 'The sign on which the lesson stands out most, in words, or No warning sign.'
)
COMMENT 'Trusted answer to which lessons need work. Six signs: not finished, Check questions missed, practice questions missed, code needing hint step 2 or more, Explain wrong picks, Still stuck presses. A sign counts only when its number is above zero, above the middle (median) lesson, and rests on at least min_learners answers, solvers or events. The finish rate counts settled learners only (finished or stalled), never people working on the lesson now. Nothing is returned while fewer than 10 lessons have min_learners past Learn, because a ranking of a handful of lessons says nothing. It ranks what to look at first; it does not pass or fail a lesson. Sort by warning_signs, then learners_stuck.'
RETURN
  WITH base AS (
    SELECT
      s.lesson,
      s.phase,
      s.course_part,
      s.`position`,
      s.learners_past_learn,
      s.learners_stalled,
      s.learners_stuck,
      s.finish_rate,
      s.check_on_own_rate,
      s.practice_right_rate,
      s.code_two_plus_hints_rate,
      s.explain_wrong_picks_per_learner,
      try_divide(s.still_stuck_presses, s.learners_past_learn) AS still_stuck_per_learner,
      -- Each sign as a number where higher is worse, and NULL when it rests on too few people.
      CASE WHEN s.learners_finished + s.learners_stalled >= lessons_needing_work.min_learners THEN 1 - s.finish_rate END AS t_finish,
      CASE WHEN s.check_questions_tried >= lessons_needing_work.min_learners THEN 1 - s.check_on_own_rate END AS t_check,
      CASE WHEN s.practice_learners >= lessons_needing_work.min_learners THEN 1 - s.practice_right_rate END AS t_practice,
      CASE WHEN s.code_solvers >= lessons_needing_work.min_learners THEN s.code_two_plus_hints_rate END AS t_code,
      CASE WHEN s.explain_completions >= lessons_needing_work.min_learners THEN s.explain_wrong_picks_per_learner END AS t_explain,
      CASE WHEN s.still_stuck_presses >= lessons_needing_work.min_learners THEN try_divide(s.still_stuck_presses, s.learners_past_learn) END AS t_stuck
    FROM `{insights_catalog}`.drill_insights.lesson_summary s
    WHERE s.learners_past_learn >= lessons_needing_work.min_learners
  ),
  typical AS (
    -- The middle lesson on each sign, among the lessons that have the sign.
    SELECT
      COUNT(*) AS lessons,
      median(b.t_finish) AS m_finish,
      median(b.t_check) AS m_check,
      median(b.t_practice) AS m_practice,
      median(b.t_code) AS m_code,
      median(b.t_explain) AS m_explain,
      median(b.t_stuck) AS m_stuck
    FROM base b
  ),
  scored AS (
    SELECT
      b.*,
      t.lessons,
      -- A sign counts when above zero and above the middle lesson. How far above, as a multiple of the middle
      -- (a middle of zero counts as very far), decides the main problem.
      CASE WHEN b.t_finish > 0 AND b.t_finish > t.m_finish THEN coalesce(try_divide(b.t_finish, t.m_finish), 99) END AS r_finish,
      CASE WHEN b.t_check > 0 AND b.t_check > t.m_check THEN coalesce(try_divide(b.t_check, t.m_check), 99) END AS r_check,
      CASE WHEN b.t_practice > 0 AND b.t_practice > t.m_practice THEN coalesce(try_divide(b.t_practice, t.m_practice), 99) END AS r_practice,
      CASE WHEN b.t_code > 0 AND b.t_code > t.m_code THEN coalesce(try_divide(b.t_code, t.m_code), 99) END AS r_code,
      CASE WHEN b.t_explain > 0 AND b.t_explain > t.m_explain THEN coalesce(try_divide(b.t_explain, t.m_explain), 99) END AS r_explain,
      CASE WHEN b.t_stuck > 0 AND b.t_stuck > t.m_stuck THEN coalesce(try_divide(b.t_stuck, t.m_stuck), 99) END AS r_stuck
    FROM base b
    CROSS JOIN typical t
  ),
  ranked AS (
    SELECT
      sc.*,
      greatest(coalesce(sc.r_finish, 0), coalesce(sc.r_check, 0), coalesce(sc.r_practice, 0),
               coalesce(sc.r_code, 0), coalesce(sc.r_explain, 0), coalesce(sc.r_stuck, 0)) AS worst,
      CAST((CASE WHEN sc.r_finish IS NOT NULL THEN 1 ELSE 0 END)
        + (CASE WHEN sc.r_check IS NOT NULL THEN 1 ELSE 0 END)
        + (CASE WHEN sc.r_practice IS NOT NULL THEN 1 ELSE 0 END)
        + (CASE WHEN sc.r_code IS NOT NULL THEN 1 ELSE 0 END)
        + (CASE WHEN sc.r_explain IS NOT NULL THEN 1 ELSE 0 END)
        + (CASE WHEN sc.r_stuck IS NOT NULL THEN 1 ELSE 0 END) AS INT) AS signs
    FROM scored sc
  )
  SELECT
    r.lesson,
    r.phase,
    r.course_part,
    r.`position`,
    r.learners_past_learn,
    r.learners_stalled,
    r.learners_stuck,
    r.finish_rate,
    r.check_on_own_rate,
    r.practice_right_rate,
    r.code_two_plus_hints_rate,
    r.explain_wrong_picks_per_learner,
    r.still_stuck_per_learner,
    r.signs AS warning_signs,
    CASE
      WHEN r.signs = 0 THEN 'No warning sign'
      WHEN coalesce(r.r_finish, 0) = r.worst THEN 'Many learners do not finish it'
      WHEN coalesce(r.r_check, 0) = r.worst THEN 'Check questions are often missed'
      WHEN coalesce(r.r_practice, 0) = r.worst THEN 'Practice questions are often missed'
      WHEN coalesce(r.r_code, 0) = r.worst THEN 'The code exercise needs a lot of hints'
      WHEN coalesce(r.r_explain, 0) = r.worst THEN 'The Explain gaps get many wrong picks'
      ELSE 'Learners often press Still stuck on the tutor'
    END AS main_problem
  FROM ranked r
  -- Fewer than 10 lessons with enough learners: say nothing rather than rank a handful.
  WHERE r.lessons >= 10
