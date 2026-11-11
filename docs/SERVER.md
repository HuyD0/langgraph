# Run the tutor as a local service

The Daily Drill page can be served from your own machine instead of claude.ai, with Ollama
answering for free and your progress in a SQLite file. One small server, two doors, one
core (`src/drill/server`):

```bash
uv run drill-server
# the page:      http://localhost:8787
# the blueprint: http://localhost:8787/blueprint.html   (the Unity Gateway drawing, a page of its own)
# the tools:     http://localhost:8787/mcp   (MCP over HTTP, for Claude Code)
```

The page is built from `src/drill/content` when the server starts (see [PAGE.md](PAGE.md)),
and the blueprint (`src/drill/content/blueprint.html`) is read once at the same time and served
with the same wrapper, ETag and gzip as the page,
and `.drill/drill.db` is created on first run.

By default the server listens on `127.0.0.1`, the address that means "this computer only" (it is
called the loopback address: what is sent to it never leaves the computer). No other device can
open the page, which matters because the server has no sign-in. `DRILL_HOST` changes the
address: [From your phone](#from-your-phone) says when you would, and what that opens.

## Which model answers

Ollama on this computer first (`OLLAMA_MODEL`, or whichever pulled model answers without
"thinking" first, so hints take seconds). A hosted model is the fallback: the Azure settings
in [SETUP.md](SETUP.md), or any OpenAI-compatible endpoint named with `DRILL_HOSTED_BASE_URL`
/ `DRILL_HOSTED_MODEL` / `DRILL_HOSTED_API_KEY`, such as a Databricks serving endpoint. Only
"complex" jobs (reviews) start with the hosted model, and it stops being used past
`DRILL_HOSTED_DAILY_TOKENS` a day; a request that would not fit in what is left of that budget
goes to Ollama instead. Only the server's own features pick "complex": the page can ask for
"quick" or "default", and anything else it sends counts as "default". A request bigger than
`DRILL_MAX_PROMPT_CHARS` is refused with a 413 before any model sees it, and so is a request
body over its route's limit (`BODY_LIMITS` in `api.py`: 2 MB for a document, 400 KB for a
question). Every answer is cached by its exact prompt, so asking the same hint twice is free;
cached answers are forgotten after `DRILL_CACHE_DAYS`, and at most `DRILL_CACHE_MAX` are kept.
If Ollama starts or stops while the server runs, the server notices within 30 seconds; no
restart needed.

**At work, through Databricks Unity Gateway (formerly AI Gateway).** No key to create or
keep: sign in once with `databricks auth login --host https://adb-<id>.azuredatabricks.net`
(it goes through Entra), and put two lines in `.env`:

```bash
DRILL_HOSTED_AUTH=databricks
DRILL_HOSTED_MODEL=<the model's name>
```

Each request is signed with that login, and the token is renewed as it runs out, so a
server left running all day keeps working. The model's name says where to send it:

| `DRILL_HOSTED_MODEL` looks like | It is | Requests go to |
|---|---|---|
| `catalog.schema.service`, e.g. `system.ai.<model>` | a Unity Gateway model service | `/ai-gateway/mlflow/v1` |
| anything else, e.g. `drill-claude` | a model serving endpoint (the legacy route) | `/serving-endpoints` |

Ask your platform team which one they give you; you need `EXECUTE` on a model service.
`DRILL_HOSTED_BASE_URL` overrides the address, and a Databricks address with no
`DRILL_HOSTED_API_KEY` uses the login too. With no Ollama on the
laptop, every question goes to the gateway, and your gateway's own limits and usage
reports apply per person.

## From your phone

**At home.** The server keeps to this computer until you tell it otherwise, so a phone cannot
reach it yet. To let the phone in, put this line in `.env` and start the server again:

```bash
DRILL_HOST=0.0.0.0
```

`0.0.0.0` means "every address this computer has", the one on your Wi-Fi included, where
`127.0.0.1` means "this computer only". Know what that opens before you do it. The server has no
sign-in, so **anyone on the same network**, not only your phone, can open the page, read and
change the progress saved there, and use the tutor. Do it on a network you trust (home, not a
coffee shop or an office), and take the line out again when you are done. While the server is open like
this the agent tools at `/mcp` are left out, and the start-up line says so; the stdio door
(`drill-mcp`, see [In Claude Code](#in-claude-code)) still works on this computer.

One name, two meanings: `make setup` (`uv run drill cloud port --ask`, see
[PORTING.md](PORTING.md)) reads `DRILL_HOST` too, as the address of a Databricks workspace to
sign in to. Take the line out of `.env` before you run that.

Then, on the same Wi-Fi, open `http://<computer-name>.local:8787` in the phone's browser (the
computer's name is in its system settings) and use "Add to Home Screen". Your computer's firewall
may ask once whether to allow incoming connections; say yes. The computer has to stay awake, so
set it not to sleep while plugged in.

**Away from home.** Put a tunnel with a login in front of it, for example
`ngrok http 8787 --basic-auth "you:<long password>"`, and open the `https://` address it
prints. Leave `DRILL_HOST` alone for this: the tunnel program runs on this computer, so it
reaches the server at its default address. Never expose the port without a login: whoever gets
through can read and change your progress and use the tutor. The agent tools at `/mcp` are not
for the tunnel's visitors: a tunnel like this one marks each request it passes on for a visitor
(it adds an `X-Forwarded-For` header, a line at the top of the request naming the address the
visitor came from), and `/mcp` refuses every request marked that way. A tunnel that only
passes the raw connection along (a TCP tunnel) adds no mark, so its visitors would look
like this computer: do not put the server behind one.

## In Claude Code

Register the stdio door once and ask for drills in any session ("give me my next drill",
"check this attempt", "add MERGE to my study list"):

```bash
claude mcp add -s user drill -- /opt/homebrew/bin/uv run --directory /path/to/this/repo drill-mcp
```

The Claude desktop app takes the same command in its MCP settings. Tools: `next_drill`,
`get_drill`, `list_lessons`, `run_tests`, `hint`, `review`, `ask_tutor`, `study_list`,
`save_to_study`, `mark_done`.

The web door's `/mcp` endpoint answers this computer only, because it has no sign-in and two of
its tools (`run_tests`, and `hint` when it is given code) run the code they are sent:

- It is served only while the server listens on a this-computer-only address: `127.0.0.1` (the
  default), `localhost`, `::1`, or another loopback address such as `127.0.0.2`. With a
  `DRILL_HOST` other devices can reach, such as `0.0.0.0`, `/mcp` is left out.
- Every request to it is checked by the address the connection really came from, which the
  server reads from the network connection, not by the name the request says it is for; any
  address but this computer's own gets a 403.
- A request that says a tunnel or a proxy passed it on for someone else gets a 403 too. They
  say so in a header (a named line at the top of a request): `X-Forwarded-For` and the other
  `X-Forwarded-` headers, `Forwarded`, `X-Real-IP` or `Via`. A program on this computer talking
  to `/mcp` directly sends none of them. So nobody gets in by typing `127.0.0.1` into such a
  header, whichever senders the server is told to believe (`FORWARDED_ALLOW_IPS`, a setting of
  uvicorn, the program that runs the server).
- The request must also be addressed to this computer (`localhost`, `127.0.0.1`, or the server's
  own address when `DRILL_HOST` is another loopback address). That is a
  defence against DNS rebinding, where a web page open in a browser on this computer points its
  own name at `127.0.0.1` to reach the door. `DRILL_ALLOWED_HOSTS` adds other names for this
  computer; it does not let other devices in.

## In the cloud

It runs as a Databricks App today: `uv run drill cloud setup --create-lakebase`, then
`uv run drill cloud deploy`. See [DATABRICKS_APP.md](DATABRICKS_APP.md) for what it costs, how it
stops itself when idle, and how to move it to work.

Everything is configuration: `DRILL_DATABASE_URL` for Postgres (Neon on Azure, Lakebase on
Databricks), `DRILL_HOSTED_*` for a model behind Unity Gateway, and the same server
in a container on Azure Container Apps or Databricks Apps, which forwards the signed-in
user's identity in a header (`DRILL_USER_HEADER`, default `x-forwarded-email`) so each
person gets their own progress. A Databricks App listens on every address by itself; any other
container needs `DRILL_HOST=0.0.0.0` (the default address is only reachable from inside the
container) and a login in front of it. The package carries its own content and page, so the
container needs nothing but the repository installed editable from a checkout (`-e .`, the
last line of `requirements.txt`: the code finds its page, `.env` and state next to the checkout).

## The leaderboard

A friendly weekly race (`page/board.js`). It is off until a learner joins: from the invitation on
Home or the done screen, or "Show me on the leaderboard" in the Notebook's Settings. A server only
you use (no login in front, not team mode) invites nobody until someone else is on the board. The page works out its own week from its progress and
saves one row: this week's and last week's points and marks, the grade, and today's trial marks.
The server keeps it in the `board` table:

| Route | Does |
|---|---|
| `GET /api/board` | every row saved in the last 15 days, each with an id (a short hash of the owner) and a name, plus `me`, the asker's id. Each row is sent with only the parts below; a saved row that fails the check below is left out, never an error |
| `PUT /api/board` | saves the asker's row, rebuilt from the parts below. A row without this week's date, points and tally, or with a part of the wrong kind, is refused with a 400 that says which part; at most 8 KB |
| `DELETE /api/board` | takes the asker off the board |

The name comes from the sign-in, never the page: the first part of the work email, so
`sam.kim@…` shows as "Sam Kim" (`DRILL_BOARD_NAME` overrides it). Emails never leave the server.
Answers, questions and study lists stay private: the row holds only counts. In Lakebase, the
`board` table's policies (below) let every learner read it and write only their own row. A
Databricks App reads it as its service principal, which owns the table.

**What a row may hold.** Everyone's page draws everyone's row. So a row that held a piece of HTML
where a count goes would run as script in every reader's page (cross-site scripting), and a row of
the wrong shape would break the board for all of them. The server checks each row on the way in
and again on the way out (`board_checked` in `api.py`) and keeps only these parts:

| Part | May hold |
|---|---|
| `week` | this week, and the one part a row must have: `week` (the day the week starts, written like `2026-10-19`: the page sends the Monday, and any real day passes), `pts`, `tally` (exactly three numbers: answers on your own, with a clue, answer shown) and, when sent, `days`, `asked`, `spark`, `lessons` and `reviews` |
| `last` | last week, the same shape as `week`, or `null` |
| `grade` | `null`, or a number from 0 to 4 (a place in the page's `GRADES`) |
| `trial` | `null`, or today's trial: `date` (a real day) and `marks`, at most three, each one `sign`, `knot` or `curtain` |
| `v` | the row's version, a number |

Every count, and `v`, is a whole number from 0 to 1,000,000 (the grade is from 0 to 4), so `true`,
`NaN`, `Infinity`, a negative number and text are all refused. A date is a real day in the year
1000 or later. Anything else in a row is dropped. The row the page builds (`boardRow`) always
passes. The check on the way out is for rows the check on the way in never saw: one saved before
rows were checked, or typed into the table by hand (the Lakebase policies let a learner write
their own row). A person whose saved row is left out is back on the board the next time their page
saves a row: a lesson finished for the first time, a review, a question to the tutor, a trial
answer, or joining again.

The page checks the same parts as rows arrive (`boardSafe` in `page/board.js`; all but `v`, which
it never reads), because on claude.ai rows come straight from the artifact's database with no
server in between. `tests/test_board.py` checks that the two share their limits and refuse the
same list of bad rows.

## Keeping the tutor for the course

The page writes its tutor prompts in the browser (on claude.ai there is no server to do it), so a
signed-in learner could send the server anything. `drill.server.guard` keeps the tutor for the course:

- **The server's rules come first.** Every `/api/ask` request reaches the model after a system
  message the page can't change: help with this course and the person's work in it, nothing else.
  A "system" message the page sends is passed on as ordinary text. An off-topic request gets one
  fixed sentence ("I can only help with Daily Drill lessons and the work they teach."), and the
  server writes an `off_topic` event for it, so managers can see who tried:
  `SELECT owner, count(*) FROM drill.events WHERE kind = 'off_topic' GROUP BY owner`.
- **Each person has a share** behind a login, where everyone shares one allowance: 6 requests a
  minute and 15,000 tokens a day (about ten questions; a question costs about 1,500 tokens, measured
  in a load test). Their day's use is a `usage/<date>` document in their own rows. Reaching a limit
  gets a 429 whose words the page shows ("Wait a minute", "comes back tomorrow"). A cached answer
  costs nothing. On your own computer there are no per-person limits (`DRILL_PERSON_LIMITS=1` adds them).
- **Sizes are capped.** Prompts over `DRILL_MAX_PROMPT_CHARS` get a 413 (20,000 in the app: the
  longest prompt the page builds is the use-case skill run, about 9,000 characters plus the card),
  and the hosted model writes at most `DRILL_MAX_ANSWER_TOKENS`.
- **The managers' notes have their own allowance** (`DRILL_NOTES_DAILY_TOKENS`), so a big team's
  notes can't use up the tutor's day.

A learner can still type an off-topic question. What stops it being answered is the model
following the rules, which is why every refusal is counted. On claude.ai none of this applies: the
tutor there runs on each viewer's own claude.ai account.

## Finding the lesson when a question comes with none

On a lesson page the page sends that lesson's text with the question, so the tutor has nothing to
find. Some questions come with no lesson: a follow-up on a study list item saved from no exercise
(`ask_study_item`, and its Explain button, which searches with the saved text; its quiz sends no question, so it never searches), Claude's `ask_tutor` tool over MCP, and any
`/api/ask` without a `lesson_id`. For those, `drill.server.retrieve` does **retrieval**: it turns the
question into a list of numbers with an **embedding model** and finds the five Learn paragraphs
closest in meaning (the top 5). They go into the prompt in front of the learner's message, each under
its lesson's title, where a lesson page puts its lesson. Putting found text into the prompt is
retrieval-augmented generation (RAG).

- **The model** is the coach-retrieval lab's champion (`notebooks/learning/coach_retrieval`):
  `bge-large` as its makers ship it, with their search prompt before the question. On your computer
  Ollama serves it (`ollama pull bge-large`). In a Databricks App retrieval is off (`app.yaml` sets
  `DRILL_RETRIEVAL=off`; why, and how to turn it on: [DATABRICKS_APP.md](DATABRICKS_APP.md)).
- **The paragraphs are embedded once**, on a background thread when the server starts (751
  paragraphs took 12 seconds in Ollama on this computer), and saved in `DRILL_HOME/retrieval/`, named by the
  model and a fingerprint of the text: a restart with the same lessons reads them back, and a changed
  paragraph means a fresh embed. `/api/health` says whether they are ready (`retrieval`). `drill-mcp`
  over stdio starts this as soon as it launches, so the first `ask_tutor` of a session can use vectors
  already on disk.
- **It never gets in the way.** The question is embedded with a time limit (`DRILL_RETRIEVAL_SECONDS`,
  2; Ollama takes about 30 ms once the model is loaded). On a timeout, an error, before the
  paragraphs are ready, or when the found text would push the prompt over `DRILL_MAX_PROMPT_CHARS`
  (fewer paragraphs are tried first, dropping the furthest one at a time), the tutor answers exactly as
  it did before, and the event says why. A question too long on its own is refused before any search
  (a 413 on the page, an error from `ask_tutor`), so it is never recorded as a retrieval problem.
- **Never on a lesson, never for the use case.** A lesson the page sent is never replaced, and asks
  that carry one are unchanged. The help with a learner's own use case (`use_case_*`) never retrieves,
  so nothing about retrieval is recorded for it. Only the server writes the retrieval record: a
  `retrieval` key the page puts in its `trace` is dropped, so it can never add a made-up RETRIEVER span
  or switch tracing off.
- `DRILL_RETRIEVAL`: `auto` (the default) retrieves when the embedding model is there and goes
  without when it is not; `on` does the same but records a missing model as an `error` (also on each
  retry while it is still missing); `off` never retrieves. `0`, `false` and `no` also mean off, and `1`,
  `true` and `yes` mean on, as for `DRILL_TRACING`; any other value means `auto`, with a warning in the log.

**What is recorded**, for watching it and for a later A/B test (real questions split between two
models, compared on what learners do next). On the `asked` event of every ask with no lesson:

| detail | what it is |
|---|---|
| `retrieval` | `on` (paragraphs were added), `off` (switched off, no question, not ready yet, or no room), `error` or `timeout` |
| `retrieved` | the lessons of the paragraphs found, closest first, each once |
| `retrieved_paragraphs` | the paragraphs themselves, as `lesson#n` |
| `retrieval_model`, `retrieval_ms` | which model searched, and how long the search took |
| `retrieval_why` | for anything but `on`: why, in a few words |

The question itself is already there (`question`, for the managers). The MLflow trace gets a
`retrieve` span of type RETRIEVER, with the question searched, the paragraphs found (MLflow's document
shape, with `lesson_id`, `title` and the similarity score) and the same fields, plus a
`retrieval` tag (`tags.retrieval = 'timeout'` finds the slow ones). The reports show it as
`retrieval_ran` and `retrieved_lesson` in `drill_insights.activity` ([INSIGHTS.md](INSIGHTS.md)).
Claude's `ask_tutor` now writes an `asked` event too (`door: mcp`), so its searches are counted the
same way.

## Moving progress to Lakebase

At home, progress stays in one SQLite file. At work, the same code keeps everyone's
progress in Lakebase (Postgres on Databricks) so a manager can see how the team is doing.
Nothing changes in the page; it is settings, plus a one-off setup in the workspace.

**What is stored.** Every row has an `owner`: `local` at home, the person's work email in
Lakebase. Next to the documents (progress, study list) there is an `events` table with one
row per thing that happened, which is what a dashboard counts:

| kind | when | detail |
|---|---|---|
| `step` | reached a lesson's next step (Learn 0, Check 1, Build 2, Explain 3) | `step` |
| `checked` | answered the lesson's own Check question (question 1), the first time | `answer` |
| `check_marks` | every Check question's mark: on your own, a clue or another go, or the answer shown (the sign, knot and curtain) | `marks` |
| `lesson_done` | finished a lesson | |
| `solved` | passed an exercise's tests | `hints`, `count`, and `mode`: code, practice or pack |
| `practised` | finished a practice set (judgement lessons): how many were right first time, and each miss with the wrong answers picked, whether the clue or the answer was needed, and for Fix the YAML the checks run and the problems seen | `right`, `total`, `missed` |
| `explained` | finished the Explain gaps | `wrong` picks, `clues` and `answers` used |
| `focus_set` | chose what to practise (no lesson) | `focus`: ai, platform or both |
| `asked` | asked something in the page | `feature`, `step`, `hint_level`, `chip`, `question`; with no lesson, what retrieval found (`retrieval`, `retrieved`... see "Finding the lesson when a question comes with none") |
| `tests_run`, `hint_used`, `saved_to_study`, `asked` | the same, through Claude's tools (`asked` for `ask_tutor`) | `door: mcp` |
| `blueprint_opened` | opened the Unity Gateway blueprint (`/blueprint.html`). A reload or Back in the same tab carries on the same visit | `visit`, `step` it opened on, `came_from`: drill or link |
| `blueprint_layer` | the blueprint showed a layer for the first time in this visit | `visit`, `step`, `layer` name (filled in by the server), `seen` (layers shown so far) |
| `blueprint_finished` | the blueprint reached the whole system | `visit`, `seen` |
| `blueprint_lesson` | tapped a lesson link in the blueprint (the lesson is the event's lesson; it never counts as work on it) | `visit`, `step`, `layer` |

The blueprint posts these to `POST /api/blueprint` only when this server sent the page (it
checks `/api/health` first), so the claude.ai copies record nothing. It sends no text: just
step numbers and a random id per visit, and the server names the layer from its own copy of
the page. Anyone can be sent the blueprint's link, so none of these is a learning action: they
never make someone an active or new learner, never count as work on a lesson, and never make a
weekly note due. The reports count them with their own measures.

**Setting up the workspace (once, by an admin).** Create the project; it comes with a
`production` branch and a `databricks_postgres` database:

```bash
databricks postgres create-project daily-drill --json '{"spec": {"display_name": "Daily Drill"}}' --profile <work-profile>
databricks postgres list-endpoints projects/daily-drill/branches/production --profile <work-profile>
```

Then connect (`databricks psql --project daily-drill`) and create the tables, with
row-level security so each person only sees their own rows, and a login role for each person:

```sql
CREATE TABLE IF NOT EXISTS docs (
  owner varchar(320), path varchar(512), body text NOT NULL, updated_at double precision NOT NULL,
  PRIMARY KEY (owner, path));
CREATE TABLE IF NOT EXISTS events (
  id varchar(32) PRIMARY KEY, owner varchar(320) NOT NULL, at double precision NOT NULL,
  kind varchar(40) NOT NULL, lesson_id varchar(120) NOT NULL DEFAULT '', detail text NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS ix_events_owner ON events (owner);
CREATE TABLE IF NOT EXISTS board (
  owner varchar(320) PRIMARY KEY, name varchar(200) NOT NULL, body text NOT NULL, updated_at double precision NOT NULL);

-- Each person reads and writes only their own rows. In Lakebase current_user is the
-- person's Databricks user name, which is the owner the app writes.
ALTER TABLE docs ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
CREATE POLICY own_docs ON docs USING (owner = current_user) WITH CHECK (owner = current_user);
CREATE POLICY own_events ON events USING (owner = current_user) WITH CHECK (owner = current_user);
-- The leaderboard: everyone reads every row (only people who joined have one), each writes their own.
ALTER TABLE board ENABLE ROW LEVEL SECURITY;
CREATE POLICY board_read ON board FOR SELECT USING (true);
CREATE POLICY board_own ON board FOR ALL USING (owner = current_user) WITH CHECK (owner = current_user);

-- Two Postgres group roles that hold the permissions.
CREATE ROLE drill_learners NOLOGIN;
CREATE ROLE drill_managers NOLOGIN;
GRANT SELECT, INSERT, UPDATE, DELETE ON docs, events, board TO drill_learners;
GRANT SELECT ON docs, events TO drill_managers;
CREATE POLICY managers_read_docs ON docs FOR SELECT TO drill_managers USING (true);
CREATE POLICY managers_read_events ON events FOR SELECT TO drill_managers USING (true);

-- A login role for each person, named after their Databricks user (their work email),
-- then a group role on top. Once per database for the extension.
CREATE EXTENSION IF NOT EXISTS databricks_auth;
SELECT databricks_create_role('sam@example.com', 'USER');   -- one pair of lines per person
GRANT drill_learners TO "sam@example.com";
```

Give each person their own `USER` role, not a role for a Databricks group. Lakebase can make
a role for a whole group, but its members then sign in *as the group*, so `current_user` is
the group's name: everyone would share one owner and see each other's progress. Roles live
on a branch, so add them on `production`. Your own role (the project creator) owns the tables
and is not held to row-level security.

**On each work laptop.** Install with the Postgres driver, sign in through Entra, and add
two lines to `.env` (the host comes from `list-endpoints` above):

```bash
uv sync --extra lakebase
databricks auth login --host https://adb-<id>.azuredatabricks.net
```

```bash
DRILL_DATABASE_URL=postgresql+psycopg://<host>/databricks_postgres?sslmode=require
DRILL_LAKEBASE_ENDPOINT=projects/daily-drill/branches/production/endpoints/<endpoint-id>
```

There is no password to set: the app asks Databricks for a one-hour Lakebase password
each time it connects, using the login on the machine. As with SQLite, the server
listens on `127.0.0.1` only unless `DRILL_HOST` says otherwise. `uv run drill store status`
says where progress is going and as whom.

**When Lakebase is out of reach** (no VPN, on a plane), the server starts on the local
SQLite file instead and the health check shows `store_fallback: true`. Once it is back,
`uv run drill store push` sends that work up; the newer copy of each document wins and
events already sent are skipped. The same command brings your home history (saved as
`local`) to work, if you copy `drill.db` over first.

The Databricks App doesn't do this. Its disk is wiped every time it restarts, so a local
file there would quietly lose everyone's work. Instead it keeps trying Lakebase for two
minutes (it may still be waking up), then refuses to start with a message saying why.

**The manager's view.** Register the Lakebase database in Unity Catalog: in Catalog Explorer,
**Create a catalog**, type **Lakebase Postgres**, **Autoscaling**, then the `daily-drill`
project, `production` branch and `databricks_postgres` database (or `databricks postgres
create-catalog`). That makes a read-only catalog, say `drill`, so `drill.public.events` can be
queried from a **Serverless** SQL warehouse (Pro and Classic are refused) and an AI/BI
dashboard built on it. Who may look is a Unity Catalog grant:

```sql
GRANT USE CATALOG, SELECT ON CATALOG drill TO `drill-managers`;
```

The queries still reach Postgres as a person, so row-level security applies: whoever
publishes the dashboard (its credentials are embedded by default) needs `GRANT drill_managers
TO "<their email>";` in Lakebase, or the dashboard shows only their own rows.

*Optional history.* Lakebase Change Data Feed (Public Preview, switched on from the
workspace's Previews page) copies every change into Delta tables named `lb_<table>_history`,
useful for trends over time. Each table needs `ALTER TABLE <table> REPLICA IDENTITY FULL;`
first. It does not work when the destination catalog's storage is only reachable through a
private endpoint, which is the case behind a workspace storage firewall, so check that
before relying on it.

Managers see everything: every person's progress, study list and events. Learners still see
only their own rows in Lakebase. The Unity Catalog copies have no per-person filter, so
anyone who can read them sees everyone: give `SELECT` on them (and the dashboard) to a
managers group only, not to learners:

```sql
GRANT SELECT ON TABLE <catalog>.<schema>.lb_docs_history TO `drill-managers`;
GRANT SELECT ON TABLE <catalog>.<schema>.lb_events_history TO `drill-managers`;
```

Learners are told up front: in team mode (`team` in `/api/health`) the page shows that their manager can see their progress, study list and tutor questions, on the first-visit card and in Settings.

## What gets measured

Every request is one MLflow trace, in experiment `daily-drill` (in `.drill/mlflow.db` unless
`MLFLOW_TRACKING_URI` points elsewhere; view it with
`uv run mlflow ui --backend-store-uri sqlite:///.drill/mlflow.db`). A question in the page's
Ask box looks like this:

```
ask_lesson                 the learner's question, lesson and step in; the answer out
  retrieve                 only when no lesson came with it: the paragraphs found (RETRIEVER)
  tutor.ask                the full prompt, model, route, temperature, tokens, why it stopped
    first_word             time to first token: how long "Thinking..." showed
    attempt local          only when a model failed and the next one was tried, with the error
  checks                   did it leak the exercise's code, use Big-O, go over its word limit
```

- **Named and tagged by what it was for.** The trace name is the feature (`ask_lesson`,
  `hint`, `review`, `explain`, `ask_study_item`, `quiz`, or the MCP tool), and the tags say
  `feature`, `door` (`page` or `mcp`), `lesson_id`, `step`, `hint_level`, `chip` (a one-tap
  question), `guard` (`solution_request` when the page turned a request for the solution
  into a hint) and `retry_of` (on a Still stuck re-explanation: the request id of the answer
  that didn't help, which carries `resolved = false` as human feedback).
- **Prepared answers.** `POST /api/served` (`answer`, `trace`) records an answer the page showed
  without asking a model as an `ask_lesson` trace tagged `route = prepared`, and logs the question
  like any other (`prepared: true`) for the manager's view.
- **Feedback.** `POST /api/feedback` (`request`, `name`, `value`, `rationale`, `source`) attaches
  feedback to the trace with that request id: HUMAN from the learner, or CODE (`source: "code"`,
  from `drill.page.signals`) for what the page saw them do. `uv run drill tutor feedback` reads it back. Search them in the UI, for example `tags.lesson_id = 'claim_gate'`.
- **Sessions.** Follow-ups in one Ask thread share a session; so do the questions about one
  study-list item, and every tool call from one Claude Code session.
- **Versions.** `app_version` is the git commit the server runs, with `-dirty` when tracked
  files have uncommitted changes, and each trace is linked to a model version of that name,
  so two versions can be compared in the UI.
- **Checks.** Each answer is checked by code, and the result shows three ways: a `checks`
  span, tags (`tags.solution_leak = 'true'` finds every leak) and feedback columns in the UI.
- **MCP tool calls.** Every tool Claude calls is a `TOOL` trace with its arguments and result;
  for `hint`, `review` and `ask_tutor` the model call and checks sit inside it.

Token counts use MLflow's own format, so its token and cost charts work. Thinking costs
time, not money, on your computer (a hint takes 5 to 20 s with it, about 1 s without), so it is
off for hints and on for reviews by default. When MLflow isn't running, tracing is off and
is tried again every 30 seconds, on a background thread, so starting MLflow later turns it
back on, and no answer ever waits for it (the requests during a retry just go untraced).

### What Claude does around the tool calls

The app's traces start when a tool is called. To see the rest of a Claude Code turn (your
message, each call Claude made to its model, which tools it picked and with what, what came
back, and its reply), trace Claude Code itself, into its own experiment:

```bash
uv run mlflow autolog claude -d . -u http://localhost:5050 -n claude-code --local -y
```

This installs MLflow's Claude Code plugin for this folder only and writes the settings to
`.claude/settings.local.json`, which git ignores. A trace is written when each turn ends.
It records whole conversations, including any file contents Claude read. Turn it off with
`uv run mlflow autolog claude --disable`.

### Sending traces to Databricks instead

Traces can go to your Databricks workspace's MLflow instead of this computer's. There are two
places Databricks can keep them, and the choice matters:

| | Traces kept in the experiment | Traces kept in Unity Catalog |
|---|---|---|
| How they get there | MLflow on your computer uploads each trace's data straight to the workspace's storage account | MLflow sends the spans to the Databricks API, and Databricks writes them into Delta tables |
| Workspace storage firewall on | **Blocked** (403 `AuthorizationFailure`) | Works |
| Reading them (UI or `mlflow.search_traces`) | No SQL warehouse needed | Needs a SQL warehouse, which costs compute while it runs |
| Limit | 100,000 traces per experiment | None |

If your workspace has its storage firewall on (`defaultStorageFirewall: Enabled`), use Unity
Catalog. Set it up once, with a schema to hold the tables and a new experiment linked to it
(the link can only be made when the experiment is created):

```bash
databricks schemas create drill_traces <catalog> --profile DEFAULT
MLFLOW_TRACKING_URI=databricks DATABRICKS_CONFIG_PROFILE=DEFAULT \
  uv run drill tracing check --uc-schema <catalog>.drill_traces
```

Then add these to `.env`:

```bash
DATABRICKS_CONFIG_PROFILE=DEFAULT            # the CLI profile for your workspace
MLFLOW_TRACING_SQL_WAREHOUSE_ID=<warehouse>  # only for reading traces back
```

Local stays the default. Switch when you want Databricks, and back when you're done, then
restart drill-server each time:

```bash
uv run drill tracing use databricks
uv run drill tracing use local      # back to this computer's MLflow (http://localhost:5050)
```

Only the `MLFLOW_TRACKING_URI` line in `.env` changes. Traces in Databricks can cost money:
Unity Catalog trace storage runs on Databricks' serverless side and reading uses a SQL
warehouse, so check the workspace's usage page while it is on.

The experiment is `/Users/<you>/daily-drill` (Databricks needs a workspace path; set
`DRILL_MLFLOW_EXPERIMENT` to choose another). `uv run drill tracing check` says where traces go
and how they are stored, writes one test trace and reads it back. Pick the smallest serverless
warehouse with a short auto-stop, so reading traces costs cents, not dollars.

**Good to know:**

- **What else costs money:** built-in LLM judges (they call a Databricks-hosted model),
  production monitoring (serverless compute), and model calls through the gateway.
- **Claude Code's own traces stay on this computer.** MLflow's Claude Code plugin (0.2.0) always
  uploads trace data straight to storage, even for a Unity Catalog experiment, so a storage
  firewall blocks it.
- **Processes started by Claude Code** (such as `drill-mcp`) inherit its
  `MLFLOW_TRACKING_URI`, which wins over `.env`.
- Old traces stay where they were; nothing is copied over. To go back, set
  `MLFLOW_TRACKING_URI` to your local server again.
- The notebooks always use their own local stores, whatever `.env` says.

## Knobs

| Variable | Default | What it does |
|---|---|---|
| `DRILL_HOST` / `DRILL_PORT` | `127.0.0.1` (`0.0.0.0` in a Databricks App) / `8787` | Where the server listens. `127.0.0.1` is this computer only; `0.0.0.0` is every address it has, so any device on the same network can open the page with no sign-in, and `/mcp` is left out |
| `DRILL_DATABASE_URL` | `sqlite:///.drill/drill.db` | Where progress and the study list live |
| `DRILL_LAKEBASE_ENDPOINT` | *(unset)* | The Lakebase endpoint to get passwords for; set it with a Lakebase `DRILL_DATABASE_URL` |
| `DRILL_HOME` | `.drill/` in the repo | The folder for the SQLite file and local MLflow traces, e.g. `~/Library/Application Support/DailyDrill` on a Mac, `%LOCALAPPDATA%\DailyDrill` on Windows |
| `DRILL_OWNER` | `local` | Whose rows a local store reads and writes (Lakebase uses your Databricks user name) |
| `DRILL_HOSTED_BASE_URL`, `_MODEL`, `_API_KEY` | *(unset, so the Azure settings)* | An OpenAI-compatible hosted model, used as the fallback |
| `DRILL_HOSTED_AUTH` | `key` (`databricks` for a Databricks address with no key) | `databricks` signs requests with the Databricks login instead of a key |
| `DRILL_HOSTED_DAILY_TOKENS` | `200000` (`500000` in the app's `app.yaml`) | Daily cap on the tutor's hosted usage, for everyone together (about four characters per token) |
| `DRILL_NOTES_DAILY_TOKENS` | `150000` | The managers' weekly notes: their own daily cap, so they never use the tutor's |
| `DRILL_MAX_ANSWER_TOKENS` | `1200` | The longest answer the hosted model may write |
| `DRILL_PERSON_DAILY_TOKENS` / `DRILL_PERSON_PER_MINUTE` | `15000` / `6` | Behind a login: each person's daily share of the tutor and requests a minute; `0` turns one off |
| `DRILL_PERSON_LIMITS` | `0` | `1` applies the per-person limits outside a Databricks App too |
| `DRILL_MAX_PROMPT_CHARS` | `60000` (`20000` in `app.yaml`) | The biggest request (all its messages together) the server takes; bigger gets a 413 |
| `DRILL_CACHE_DAYS` / `DRILL_CACHE_MAX` | `7` / `2000` | How long a cached answer is reused, and how many are kept |
| `DRILL_FIRST_WORD_SECONDS` | `45` | Give up on a model that has not started answering by then, and try the next one |
| `DRILL_THINKING` | `complex` | When a thinking model (Qwen 3, DeepSeek R1...) may think: `off`, `complex` (reviews only) or `on`. A hosted Claude that can stop thinking (Haiku 5.5, Sonnet 5.5) thinks only with `on`, so its answers stay as quick and short as Haiku 4.5's |
| `DRILL_TRACING` | `1` | One MLflow trace per request; `0` turns it off |
| `DRILL_RETRIEVAL` | `auto` (`off` in the app's `app.yaml`) | For questions with no lesson: find the closest Learn paragraphs first. `auto` when the embedding model is there, `on` (a missing model counts as an error), `off`. Also `0`/`false`/`no` (off) and `1`/`true`/`yes` (on); anything else means `auto`, with a warning |
| `DRILL_RETRIEVAL_SECONDS` | `2` | The time limit for embedding a question; past it the tutor answers without retrieval |
| `DRILL_EMBEDDING_ENDPOINT` | `databricks-bge-large-en` | In a Databricks App with retrieval turned on: the embedding endpoint, or a Unity Gateway model service such as `system.ai.bge-large-en` (on your computer it is Ollama's `bge-large`) |
| `DRILL_MLFLOW_EXPERIMENT` | `daily-drill` | The experiment the traces go to (on Databricks, `/Users/<you>/daily-drill` unless you give a path) |
| `MLFLOW_TRACKING_URI` | *(unset, so `.drill/mlflow.db`)* | Where traces go: a local MLflow server, or `databricks` |
| `DATABRICKS_CONFIG_PROFILE` | *(the CLI's default)* | Which Databricks CLI profile `databricks` means |
| `DRILL_ALLOWED_HOSTS` | *(this machine)* | Extra `host:port` names for this computer that a request to `/mcp` may be addressed to; it does not let other devices in |
| `DRILL_USER_HEADER` | `x-forwarded-email` | Header a login proxy uses to say who is asking |
| `DRILL_TRUST_USER_HEADER` | `0` | `1` makes the server believe that header outside a Databricks App (where it is always believed). **Only behind a login proxy that sets the header itself**: otherwise anyone who can reach the port can send the header and read or write any person's rows |
| `DRILL_DB_SCHEMA` | *(the database's default)* | The Postgres schema the tables live in (`drill` in the app); lowercase letters, digits and underscores |
| `DRILL_CONTENT_PACKS` | *(unset)* | Content pack folders to load, separated by `:` (`content-packs/internal` in `app.yaml`); a folder that doesn't exist is skipped ([CONTENT_PACKS.md](CONTENT_PACKS.md)) |
| `DRILL_SHOW_DRAFTS` | `0` | `1` shows a pack's draft lessons, marked Draft (`drill content preview` sets it) |
| `DRILL_TEAM_SUMMARIES` | *(on with a shared database, off with SQLite)* | `1` or `0` forces the managers' weekly notes on or off |
| `DRILL_IDLE_STOP_MINUTES` | `0` | In a Databricks App only: stop the app after this many minutes with no requests (`30` in `app.yaml`); `0` keeps it running |
| `DRILL_MLFLOW_EXPERIMENT_ID` | *(unset)* | The experiment by id instead of name: how a Databricks App names the experiment resource attached to it; wins over `DRILL_MLFLOW_EXPERIMENT` |
| `DRILL_SIGNALS_EVERY_MINUTES` | `0` | Hold the page's quiet signals on tutor answers (`saved`, `asked_again`, `gave_up`, `next_right`) and write them in one burst this often; `0` writes each at once. The app uses `60`, so the warehouse that keeps Unity Catalog traces wakes once an hour for them. Got it / Still stuck is always written at once, and held signals are written when the server stops |
| `DRILL_CHECKS_AS_FEEDBACK` | `1` | Write each answer's checks to its trace as feedback, one by one; `0` (the app) keeps them as tags and a span, and `drill traces score` adds them in a batch |

Not the server's, but read from the same `.env`: the terminal tutor's `DRILL_TEMPERATURE`,
`DRILL_MAX_ATTEMPTS`, `DRILL_SANDBOX_TIMEOUT` and `DRILL_PROGRESS_PATH` (`drill start`'s model
temperature, tries, sandbox seconds and progress file), `DRILL_ENVIRONMENT` (`local` or `app` on
every trace; the app sets it by being one) and `DRILL_NOTEBOOK_OFFLINE` (`1` makes the RAG
notebooks use their recorded runs).

## What the platform lessons record

They are in the events table above: `practised` (a practice set, with each miss and the help it
needed), `explained` (the Explain gaps) and `focus_set` (ai, platform or both), and `solved` says
how (`mode`: code, practice or pack).

The managers' weekly note gets the practice misses and Explain help, so it can name the actual
sticking point ("picked CAN_EDIT for the owner group twice").

The managers' dashboard shows them too: a "practising" column (ai, platform or both) on the team
table, and "Platform practice questions they missed" (the question, what they picked, the help
they needed, any YAML problems) on "Where they're stuck". After deploying a new version, update
the dashboard with `uv run drill cloud manager-view --target work`. Nothing in Lakebase needs
migrating: new event kinds are new rows in the same `events` table.
