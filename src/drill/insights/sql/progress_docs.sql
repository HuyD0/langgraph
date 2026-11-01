-- Helper: one row per saved progress copy, with the JSON read into typed columns.
-- Not for Genie or dashboards. learner_lessons and learners merge the copies of one person.
-- Each lesson entry is parsed on its own, so one odd record cannot blank the rest of a person.
-- Never reads mine (the learner own use case) or said (their own Explain sentence).
CREATE OR REPLACE VIEW `{insights_catalog}`.drill_insights.progress_docs (
  learner COMMENT 'Work email of the learner, in lower case.',
  doc_path COMMENT 'Where the copy is saved: data/users/<id>/progress from the app, or data/users/local/progress from a laptop. One person can have both.',
  saved_at COMMENT 'When this copy was last saved. The page saves it on every visit, so this is the last visit, not the last learning.',
  saved_epoch COMMENT 'The same time as seconds since 1970. Used only to pick the newer copy.',
  current_lesson_id COMMENT 'Short code of the lesson last opened in this copy, or the next one after a finish. Can be empty.',
  focus COMMENT 'What the learner chose to practise in this copy: ai, platform or both. Empty means never chosen (the app then shows the AI path).',
  study_days COMMENT 'Days with real study (finished a lesson, ran tests, finished practice) as dates on the calendar of the learner device, not UTC.',
  lessons COMMENT 'Each opened lesson, read one by one: furthest step (0 Learn to 3 Explain), finished, first pick on Check question 1 (original option number), Check marks and wrong picks per question, latest practice run, Explain help, and the first-time result.',
  solved COMMENT 'Each exercise passed, by exercise code, as the JSON text the app saved (count, last day, hints, mode). Very old records are just true.'
)
COMMENT 'Helper view, not for Genie or dashboards: one row per saved progress copy. learner_lessons and learners merge the copies of one person. The use case a learner writes for themselves (mine) and their own Explain sentences (said) are never read.'
AS
SELECT
  lower(dx.owner) AS learner,
  dx.path AS doc_path,
  timestamp_seconds(dx.updated_at) AS saved_at,
  dx.updated_at AS saved_epoch,
  get_json_object(dx.body, '$.current') AS current_lesson_id,
  get_json_object(dx.body, '$.focus') AS focus,
  from_json(get_json_object(dx.body, '$.days'), 'array<string>') AS study_days,
  -- lessons is read as a map of lesson id -> JSON text first, then each lesson is parsed on its own.
  transform_values(
    from_json(get_json_object(dx.body, '$.lessons'), 'map<string,string>'),
    (k, v) -> from_json(v, 'struct<step:int,checked:int,done:boolean,checks:struct<marks:array<string>,tried:array<array<int>>>,practice:struct<`right`:int,total:int,missed:array<struct<q:string,wrong:array<string>,clue:boolean,answer:boolean>>>,`explain`:struct<wrong:int,answers:int,done:boolean>,`first`:struct<`check`:array<string>,`date`:string>>')
  ) AS lessons,
  from_json(get_json_object(dx.body, '$.solved'), 'map<string,string>') AS solved
FROM `{lakebase_catalog}`.drill.docs dx
-- Cheap prefix filter first, then the learner filter (the app itself owns cache/ and usage/ rows).
WHERE dx.path LIKE 'data/users/%/progress'
  AND lower(dx.owner) LIKE '%@%'
