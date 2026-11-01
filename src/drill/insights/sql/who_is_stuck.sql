-- Trusted answer to "who is stuck (on lesson X)?": the learners held up right now, with what tripped them up in words.
CREATE OR REPLACE FUNCTION `{insights_catalog}`.drill_insights.who_is_stuck(
  lesson_search STRING DEFAULT '' COMMENT 'A lesson number such as 2.11 or P3.4 (matched exactly), a lesson code such as split_by_key, or words from the title. Empty means every lesson.'
)
RETURNS TABLE (
  learner STRING COMMENT 'Work email of the learner.',
  learner_name STRING COMMENT 'Name taken from the email.',
  status STRING COMMENT 'Active, Drifting, Gone quiet or Started before tracking began, as in learners.status.',
  lesson STRING COMMENT 'Lesson number and title.',
  phase STRING COMMENT 'Phase of the lesson.',
  furthest_step STRING COMMENT 'Furthest step reached: Check, Build or Explain.',
  help_signals STRING COMMENT 'The signs of difficulty, in words.',
  first_check_picked STRING COMMENT 'Check question 1: the words of the option picked first.',
  first_check_right_answer STRING COMMENT 'Check question 1: the words of the right option.',
  practice_missed_questions STRING COMMENT 'Practice questions not right first time in the latest run, with the wrong options picked.',
  tutor_requests BIGINT COMMENT 'Requests to the AI tutor about this lesson.',
  last_activity_at TIMESTAMP COMMENT 'Last recorded learning action on this lesson.',
  days_since_last_activity INT COMMENT 'Days since that action, 7 to 30 for a stuck lesson.'
)
COMMENT 'Trusted answer to who is stuck: learners who went past the Learn step on a lesson, needed help, have not finished it, last touched it 7 to 30 days ago and have not moved on to later lessons, with what tripped them up. Returns no rows when nobody is stuck. Optionally only the lessons matching lesson_search.'
RETURN
  SELECT
    ll.learner,
    ll.learner_name,
    lr.status,
    ll.lesson,
    ll.phase,
    ll.furthest_step,
    ll.help_signals,
    ll.first_check_picked,
    ll.first_check_right_answer,
    CASE WHEN coalesce(size(ll.practice_missed), 0) > 0 THEN
      array_join(transform(ll.practice_missed, x -> concat(coalesce(x.q, ''),
        CASE WHEN coalesce(size(x.wrong), 0) > 0 THEN concat(' (picked: ', array_join(x.wrong, ', '), ')') ELSE '' END)), ' | ')
    END AS practice_missed_questions,
    ll.tutor_requests,
    ll.last_activity_at,
    ll.days_since_last_activity
  FROM `{insights_catalog}`.drill_insights.learner_lessons ll
  JOIN `{insights_catalog}`.drill_insights.learners lr ON lr.learner = ll.learner
  WHERE ll.is_stuck
    AND (
      trim(coalesce(who_is_stuck.lesson_search, '')) = ''
      OR (trim(who_is_stuck.lesson_search) RLIKE '^[Pp]?[0-9]+[.][0-9]+$'
          AND lower(ll.lesson_number) = lower(trim(who_is_stuck.lesson_search)))
      OR (NOT (trim(who_is_stuck.lesson_search) RLIKE '^[Pp]?[0-9]+[.][0-9]+$')
          AND (ll.lesson_id = trim(who_is_stuck.lesson_search)
               OR lower(ll.lesson) LIKE concat('%', lower(trim(who_is_stuck.lesson_search)), '%')))
    )
