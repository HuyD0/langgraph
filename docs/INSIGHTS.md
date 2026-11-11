# Insights: how the app is doing

The managers' dashboard shows each learner. This layer answers the next question: how is the whole
programme doing? It is a thin, commented schema, `<insights catalog>.drill_insights`, built over the
read-only catalog of the app's Lakebase database: eight views, one metric view and four trusted SQL
functions. A Genie Agent, **Daily Drill insights**, reads five of those objects and the four functions,
so the owner and managers can ask in plain words how many people learn each week, whether they come
back, how far they get, where they get stuck and whether the tutor helps. The managers' dashboard is
rebuilt on the same layer, in place, so it keeps its link. One command builds all of it:

```bash
uv run drill cloud insights --dry-run --insights-catalog <catalog>   # print every statement and both JSON documents; runs nothing
uv run drill cloud insights --step layer --insights-catalog <catalog> --managers <group>
uv run drill cloud insights --step genie
uv run drill cloud insights --step dashboard
```

**Nothing in this document has been run.** Every statement is a draft, checked column by column against
the code, that the owner runs later: first with `--dry-run` to read it, then for real with a chosen CLI
profile. The catalog, warehouse, group, dashboard id and Genie Agent id live in the git-ignored
`.databricks/bundle/<target>/variable-overrides.json` (`insights_catalog`, `warehouse_id`, `managers_group`,
`manager_dashboard_id`, `insights_genie_id`), never in code, so the same command works for the personal
target now and the work target later.

## Is the data ready?

Not yet as it is, but it is close, and the layer is what makes it ready. The raw tables have everything:
the event log, the saved progress and a clean lessons table. Pointed straight at them, though, Genie
would give confident wrong answers. Most facts are JSON stored as text (a learner's whole progress is one
blob). Times are seconds since 1970, and three calendars are mixed (server time, the learner's own day,
the app server's day). The owner column mixes learners with the app's own rows, and one person can have
two progress copies and two spellings of their email. Steps, marks and tutor features are codes, the
same key means different things in different events (`right` is option text in one, a count in another;
`hints` means three different things), events repeat and get backfilled, choosing a focus looks like
learning, and private free text sits beside the numbers.

The layer leaves out the app's own rows, merges a person's two copies, turns times into UTC days and
Monday weeks by arithmetic, parses each lesson's JSON on its own so one odd record cannot blank a
person, names steps and results in words, counts first times once, judges the first Check answer by the
option words recorded at the time, and never reads the learner's own use case or Explain sentence. The
raw tables stay as they are. A few questions stay only partly answerable until the app writes more:
the wording of Check questions 2 and 3, practice lessons against code lessons, and before-and-after a
content fix.

## The layer

`src/drill/insights/sql/` holds one file per object; `drill.insights.layer` loads them in this order
(a view only reads views above it) and fills in the two placeholders.

| Object | One row per | What it answers |
|---|---|---|
| `lessons` (view) | lesson in the running course | Numbers, titles, phases in order, module, main path or Platform track. Every other view joins to it. |
| `progress_docs` (view, helper) | saved progress copy | The JSON read into typed columns, each lesson parsed on its own. Not for Genie or dashboards. |
| `activity` (view) | recorded action, learners only | What happened, in words, with the UTC day and Monday week, start week, first-time flag, the first Check answer judged by option words, tutor help type, how a question was asked, for questions with no lesson whether the tutor searched the course and the lesson it found closest, Got it / Still stuck, and for the Unity Gateway blueprint the layer, layers seen, visit and where it was opened from. The source of the metric view. |
| `learner_lessons` (view) | learner × opened lesson | How far they got, finished or not, how each Check question went, practice, Explain, tutor use, the signs of difficulty, stuck or left behind. The truth for finished or not. |
| `study_items` (view) | study list item today | Saved text, the learner's note, status, next review. Dashboard only. |
| `learners` (view) | person | Started or not, status in words (Active, Drifting, Gone quiet, Not started, Started before tracking began), why to check in, days active, streak, lessons finished per course part, current lesson, stuck lessons, tutor and study use. |
| `lesson_summary` (view) | lesson, zeros included | Learners who opened, passed Learn, reached Build and Explain, finished, are working on it, stalled, stuck or left after struggling; Check, practice, code hint and Explain rates; tutor use. |
| `weekly_notes` (view) | learner × week | The model-written weekly note. Dashboard only, kept out of Genie: an opinion, not a measure. |
| `engagement_metrics` (metric view) | action, recounted at any grain | Active and new learners, days studied per learner, lessons finished, exercises passed, Check question 1 right first time, tutor requests, typed questions, Got it rate, blueprint visits, viewers, visits that reached the whole system and lessons opened from it, by day, week, month, start week, person, lesson, phase or help type. |
| `retention_by_start_week(weeks_back)` (function) | start week × weeks later | Do people come back? Of those who started in a week, how many did a learning action 1, 2, 3 weeks later. |
| `who_is_stuck(lesson_search)` (function) | learner × stuck lesson | Who is held up right now, on which lesson, and what tripped them up, in words. |
| `lessons_needing_work(min_learners)` (function) | lesson with enough learners | Which lessons to look at first: six warning signs and the main problem in words. Returns nothing until 10 lessons qualify. |
| `team_week(for_week)` (function) | started learner, one week | How did everyone do this week or last week, next to the week before. |

Days and weeks are **UTC days**, worked out from the seconds themselves
(`date_from_unix_date(floor(at / 86400))`), so a warehouse whose session time zone an admin changed cannot
shift them; the page text says "day" and "week" and explains this once. The one exception is the
learner's streak, which follows the calendar on their own device, as the app does.

**Stuck** means: past Learn, not finished, needed help, last touched 7 to 30 days ago, and the learner
has not moved on (it is their current lesson, or no later lesson was finished after it). Older or
moved-on struggles are counted apart as *left unfinished after struggling*, so a lesson someone
abandoned months ago does not sit in the stuck list forever. **Finish rate** counts settled learners only:
finished divided by finished plus stalled; people working on a lesson now do not count against it.
A **warning sign** in `lessons_needing_work` counts only when its number is above zero, above the middle
(median) lesson, and rests on at least `min_learners` answers, solvers or events.

## The Genie Agent

`drill.insights.genie` builds the agent (`serialized_space` version 2). It knows the metric view and the
`learners`, `learner_lessons`, `lesson_summary` and `activity` views, join specs between them, a few SQL
snippets (this week, last week, last 7 days, started learners, stuck now, and the two rates that combine
across lessons), twelve example queries (one per query shape), one text instruction, and the four
functions as **trusted assets**: an answer that uses one is marked verified, which is the pattern the
course's own Genie lesson teaches. The API rejects the whole payload on any key it does not know, and the
reference allows only `identifier` and `column_configs` on a table or metric view entry, so the one-line
description of each object sits in the text instruction (`## WHERE TO LOOK`), not on the entry. The key
that attaches the functions is `instructions.sql_functions` (confirmed on the first build, 2026-11-01; the
build still drops one unknown key and retries, in case the API changes). Three more things that build
found: a `column_configs` entry may use only the version 2 switches `enable_entity_matching` and
`enable_format_assistance` (the version 1 names make the API reject the space); a trusted function may not
take a `DATE` parameter ("argument type is not supported: date"), so `team_week` takes the day as text;
and the API files the metric view under `data_sources.tables` whatever array it arrived in.

How to ask: for counts and rates over time, Genie uses the metric view (never adding active learners
across weeks). For people it uses `learners`; for a person on a lesson, `learner_lessons`; for a lesson,
`lesson_summary`. "Do people come back", "who is stuck", "which lessons need work" and "how did
everyone do this week" go to the functions. The instruction tells it to show the count next to every
rate, to say when fewer than 5 people are behind a number, and that Got it and Still stuck ratings
carry no lesson, so when asked to split them by lesson, phase or help type it must say so and offer the
split by week, day or learner instead.

Example questions (also the agent's sample questions):

- How many people were active this week, compared with last week?
- Of the people who started in each week, how many were still coming back two and four weeks later?
- On average, how many days a week do active learners study?
- Which lessons should we look at first, and why?
- Who is stuck on lesson 2.11, and what tripped them up?
- Is the tutor helping: what share of rated answers were Got it, week by week?

`genie.BENCHMARKS` holds 36 test questions, worded differently from the examples, with 2 to 4 phrasings
per core question and every expected answer naming its columns. One asks about a lesson nobody is stuck
on (the right answer is "nobody"), and one asks for the Got it rate by lesson (the right answer is an
explanation, graded by a note, not SQL). They travel inside the agent; run them from its Benchmarks tab
(or the Beta eval-run API) after each change to what Genie reads, and rerun the same set: that loop,
"fix what Genie reads, then rerun", is the one the course teaches.

## The dashboard

`drill.insights.dashboard` rebuilds the managers' dashboard in place as **Daily Drill: how it is going**,
on a 12-column grid, every dataset reading the layer by its full name. A Filters page holds a date range
(for the weekly charts, tutor requests and questions) and a Learner picker (for every per-person table).

| Page | The question it answers |
|---|---|
| How it's going | How many people are learning, how often, and is it growing? Four counters (last 7 days against the 7 before) and the weekly lines. |
| Do they come back? | After their first week, do people keep coming back, and who has drifted? The start-week table, where everyone is now, and who needs a check-in. |
| How far they get | How far through the course do learners get, and where does each lesson lose them? Phase bars, lessons finished per learner, and the lesson-by-lesson funnel. |
| Where they're stuck | Which lessons and questions trip people up, and who is stuck right now? Lessons to look at first, Check questions missed, wrong first picks in words, practice questions missed, who is stuck. |
| Team | Where is each person this week and overall, and what did they save to come back to? |
| Questions and the tutor | How much do people use the tutor, what for, and do its answers help? Got it next to how many ratings it rests on. |
| Weekly notes | What does the weekly note say about each person? |

Ask Genie on the dashboard is **off** until the curated agent exists; with `insights_genie_id` saved, the
build links that agent (`uiSettings.genieSpace`), so each viewer asks with their own rights. The
dashboard has no scheduled refresh and no subscriptions: every open reads the live app database.

## Privacy

- **Who sees what.** The schema, the agent and the dashboard show every learner, so they are shared
  with the managers group only; learners get nothing. The app itself still shows each learner only their
  own rows. Managers see progress, the study list and the questions typed to the tutor, which is what the
  first-visit card tells learners.
- **Never shown by this layer, to anyone.** The learner's own use case (`progress.mine`) and their own
  Explain sentence (`said`) are never read. The raw tables still hold them, so whoever can read those
  (the grants in the last point of this list) can read them too. At work the page says so for the use
  case, in the note under each form ([PAGE.md](PAGE.md), "Your own use case"). The traces of the
  use-case helper hold what the learner wrote as well, so whoever can open the trace experiment or the
  trace tables can read it there: keep both to the people who run the app. Requests to the use-case
  helper and every rating or outcome of its drafts (`useful`, `pilot_outcome` and the reason names) are
  dropped from `activity` entirely, not just unnamed; the only per-person feedback signals are Got it,
  Still stuck, Saved, Asked again, Gave up and Got the next question right.
- **Entity matching and example values are off** for emails, names, question text, the Check option
  words, help signals, and the metric view's Learner and Learner name, because matched values become
  shared context for every asker. It is on only for stable words a manager names directly: status,
  phase, lesson, course part, step, how asked, Check results.
- **Learner words are data.** Question text, saved text and notes can contain instructions; the agent is
  told to quote or summarise them and never follow them. The weekly notes stay out of Genie.
- **Ownership and grants are documented here, not coded.** The schema should live where no other group
  inherits `SELECT` or `EXECUTE` (Unity Catalog grants flow down from the catalog, and a team catalog
  that also holds the trace tables is probably shared with the learners): a dedicated catalog is safest.
  Run `SHOW GRANTS ON CATALOG <catalog>` before creating anything. Make a small admin group or a service
  principal with raw `SELECT` the owner of the schema, views and functions, so nothing breaks when one
  person leaves; keep the dashboard and the agent in a shared folder with a second `CAN MANAGE` holder.
  The build command grants the managers group `USE CATALOG` on the insights catalog and `USE SCHEMA`,
  `SELECT`, `EXECUTE` on `drill_insights`, and touches no raw-catalog grant. Today `drill cloud share`
  and `drill cloud port` also grant that group `SELECT` on the raw Lakebase catalog (and the app grants
  the Postgres role `drill_managers` every table): whether to revoke those, so managers see only the
  layer, is the owner's decision below.

## Cost and load

Every Genie question and every dashboard open runs SQL on the serverless warehouse and reads the live
Postgres through the Lakebase catalog, parsing every learner's progress JSON, which can wake a
scaled-down Lakebase. It should be fine for about 100 learners; if it gets slow, snapshot the views to
Delta tables on a schedule under the same names and point the metric view and the dashboard at those.
Genie use by people is free until **31 January 2027** (calls from a service principal are billed, so
never call the agent from the app's own identity); set a Genie budget with an alert, and put a review
date before February 2027 in the calendar. The dashboard has no schedule and no subscription; add at
most one daily refresh later, and allow subscribers from the managers group only.

## Building it, step by step

Each step needs the owner's approval and a chosen CLI profile; print every statement first with
`drill cloud insights --dry-run`. On 2026-11-01 steps 2 to 4 ran on the personal workspace (catalog
`dbx_dev`, the saved serverless warehouse, no managers group, so no grants): every view, function and the
metric view was created and queried, the Genie Agent answered its questions (one through a trusted
function), and the dashboard was republished at its old link with Ask Genie linked. The second half of
step 1, the test as a principal with no raw grant, cannot run in a one-person workspace: do it at work.

0. **Look at Ask Genie on today's dashboard.** It is published with embedded credentials. Open the
   published dashboard and look for the Ask Genie button; whether an API-published dashboard has it on
   by default is not confirmed, so look rather than assume. If it is there, an auto-made Genie answers any
   viewer with the publisher's rights over every row, question text included: turn it off (Settings →
   General, or publish the rebuilt board, which sets `genieSpace.isEnabled: false`) and keep it off until
   the curated agent is linked.
1. **Scratch test, twice.** In a scratch schema create one view (`lessons` is enough), the metric view and
   one function, and query each. Then do the same **as a principal with no grant on the raw Lakebase
   catalog** (a test user, or a temporary group holding only the insights grants): the whole privacy
   model depends on a view, a metric view and a function reading the Lakebase catalog with their owner's
   rights for a manager who has none, and no document says outright that a saved view over a Lakebase
   catalog does that. If it fails, switch to the Delta snapshot fallback before building pages.
   While the scratch schema is there, make a scratch Genie agent in the UI over that one view, attach the
   one function to it as a trusted asset, then run `databricks genie get-space <id> --include-serialized-space`
   and copy the exact key it uses for functions into `drill.insights.genie.serialized_space` (today it
   guesses `instructions.sql_functions`); check at the same time whether a table entry carries any key
   beyond `identifier` and `column_configs`. Delete the scratch agent and schema afterwards.
2. **The layer:** `drill cloud insights --step layer --insights-catalog <catalog> --managers <group>`
   creates the schema, the eight views, the four functions and the metric view, then runs the grants.
   Each statement goes through the SQL statement API, not the CLI's query tool: that tool reads a leading
   `-- comment` as a flag and did not carry the metric view's YAML through whole from a file (the
   personal build found both). If the Lakebase catalog has no `board` table yet (the app creates it the first time a
   version with the leaderboard starts), `learners` is built with `on_leaderboard` false for everyone and
   the command says so; run `--step layer` again after the app has been redeployed.
   Check two or three people by hand: lessons finished, exercises passed and the first Check result
   should match what the app shows them.
3. **The agent and its benchmarks:** `--step genie` creates the Genie Agent (or updates it in place)
   with its benchmarks inside; run the benchmarks, fix what Genie reads, rerun the same set. If the API
   answers "Unknown field", the build drops that one key, tries once more and prints what the agent was
   saved without; a second unknown key, or any other error, stops it. With `--step all`, a failed agent
   does not stop the dashboard: it is still rebuilt and republished with Ask Genie **off** (that republish
   is what closes step 0's exposure), and the command then exits with the agent's error.
4. **The dashboard:** `--step dashboard` rebuilds the managers' dashboard in place and republishes it
   with embedded credentials, Ask Genie linked to the agent (off when no agent id is saved). Once step 1
   has shown the layer works for a manager with no raw grant, publishing without embedded credentials is
   the better choice: each manager then sees with their own rights.
5. **Share:** give the managers group `CAN USE` on the warehouse, `CAN RUN` on the agent and `CAN VIEW`
   on the dashboard (the schema grants came with step 2). Then decide on the raw-catalog grants below.

## What is not yet proven

- **First follow-up, before anything is run:** the JSON reading matches today's page by hand. If a
  progress field is renamed (`step`, `done`, `checks.marks`, `practice`, `explain`, `first`), the
  matching columns go empty without an error. The repo test that pins those names in `page.html`, the
  way `tests/test_course.py` does, is still to write; it comes before the scratch test.
- A saved view, a metric view and a SQL function **over a Lakebase catalog** work for their owner (built
  and queried on 2026-11-01). Whether they resolve with the owner's rights for an asker who has **no raw
  grant** is still unproven: a one-person workspace has no second principal to try it with. Test it at
  work before sharing (step 1).
- Speed and load: the window functions in `activity` stop filters reaching Postgres, `learners` reads
  four other views, and Genie cancels SQL that runs over 5 minutes. With one learner every view answers
  in seconds; nothing is known yet about a hundred.
- **An engine fault to design around (seen 2026-11-01):** over a Lakebase catalog, a CTE or subquery that
  is an aggregate with no `GROUP BY` comes back as *every input row* once the query stops reading its
  columns (the engine prunes the aggregate away; a Delta table does not do this). `SELECT COUNT(*) FROM
  learners` answered with the number of lessons until the course-size CTE became a scalar subquery. Such a
  value goes in a scalar subquery or a window over the whole set (`OVER ()`), never in a joined relation;
  `tests/test_insights.py` scans every view, function and dashboard dataset for the shape.
- Syntax, all confirmed on the first run: `from_json` to `map<string,string>`, `transform_values` with
  `from_json` in the lambda, `max_by` and `min_by`, `stack()`, `explode()` in a function body, `median()`
  (as a window too), `DEFAULT` values on function parameters, the metric view's `dimensions`, `FILTER`,
  `MEASURE()` ratios and `format` blocks. `genieSpace.isEnabled: false` still needs a look at the
  published board.
- The shape of `serialized_space` is settled (see The Genie Agent above). Still open: whether a table or
  metric view entry may carry a `description` (the descriptions sit in the text instruction for now).
- Dashboard details: the API accepted the rebuilt board and all 17 dataset queries run (2026-11-01), but
  nobody has yet opened the published pages and looked. The filters use the same
  `associative_filter_predicate_group` companion field as the old managers' dashboard; the new pages'
  tables use widget version 2 for the percentage formatting; categorical bars take a `custom-order` sort
  so phases, statuses and steps draw in course order. If a table or filter shows an error on the page,
  the dashboard reference suggests the plain filter field alone (`associativity=False` on
  `_learner_filter` and `_multi_select`) and table version 1 (`version=1` on `_table`).
- Bursts and late arrivals: the first save into a new database records everything already done at one
  time, so that week spikes; offline work arrives when it is saved. First-time counting stops double
  counting but cannot move a replayed lesson back to its real date.
- The thresholds are judgement calls: stalled after 7 quiet days (the app's weekly rhythm), stuck for
  7 to 30 days, Drifting at 7 and Gone quiet at 21, hint step 2 as real help, fewer than half the
  practice right, at least 5 learners behind a rate, at least 10 lessons before ranking. Check them
  against the first month of data and the managers' own sense of who needed help.
- Coverage: only Databricks App users (and laptop pushes) appear; the email is the only identity, so
  questions by team need a mapping table from outside the app.

## Decisions only the owner can make

1. Who is this for: just you, every manager seeing every learner (today's rule), or each manager seeing
   only their own reports? The last needs a people-to-manager table and row filters, which switch off
   entity matching.
2. May managers lose direct access to the raw Lakebase catalog and the `drill_managers` Postgres role,
   so they see only the layer? Should `drill cloud share` and `port` grant the insights schema instead?
3. Which catalog holds `drill_insights` at work, who has grants on it today, and should the platform
   team create it through Terraform and Spacelift rather than the CLI?
4. Who owns the views, functions, agent and dashboard: you, a small admin group, or a service principal?
5. UTC days (the default here), or the team's local time, for days and weeks?
6. What should "stuck" mean, and after how many quiet days should it stop counting? The layer says
   7 to 30 days and "not moved on".
7. Should your own account, test accounts and managers who are also learning be left out?
8. Personal workspace first (this plan), or straight to work? Which CLI profile, and is the scratch
   test approved? It runs warehouse and Lakebase compute.
9. Live numbers, or an hourly or daily copy that keeps load off the database the app runs on?
10. Should the first-visit card tell learners that managers can now ask free-form questions about their
    data and see labels like Drifting or stuck? Today it names progress, the study list and tutor questions.

## Moving it to work

Nothing changes in code. Sign in with the work profile, choose the work catalog and group with the
platform team (step 3 above), and run the same commands with `--target work`:

```bash
uv run drill cloud insights --target work --dry-run --insights-catalog <work catalog>
uv run drill cloud insights --target work --step layer --insights-catalog <work catalog> --managers <work managers group>
uv run drill cloud insights --target work --step genie
uv run drill cloud insights --target work --step dashboard
```

The work overrides file gets its own `insights_catalog`, `managers_group`, `insights_genie_id` and
`manager_dashboard_id`. At work the lessons table also holds the team's own lessons (content packs);
they join a phase or the track and count in its totals, so "Main path" there includes them. Repeat the
scratch test (step 1) there too: the work warehouses may have a different session time zone and
different inherited grants, which is exactly what the UTC arithmetic and the dedicated catalog are for.
