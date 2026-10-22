# Run the tutor as a local service

The Daily Drill page can be served from your own machine instead of claude.ai, with Ollama
answering for free and your progress in a SQLite file. One small server, two doors, one
core (`src/drill/server`):

```bash
uv run drill-server
# the page:  http://localhost:8787
# the tools: http://localhost:8787/mcp   (MCP over HTTP, for Claude Code)
```

The page is built from `src/drill/content` when the server starts (see [PAGE.md](PAGE.md)),
and `.drill/drill.db` is created on first run. macOS will ask once whether to allow
incoming connections; say yes if you want the phone to reach it. By default the server listens
on every network interface with no sign-in, so anyone on the same Wi-Fi can open it and use your
progress; `DRILL_HOST=127.0.0.1` keeps it to this Mac.

## Which model answers

Ollama on this Mac first (`OLLAMA_MODEL`, or whichever pulled model answers without
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

**At home.** Same Wi-Fi, nothing to install: open `http://<your-mac-name>.local:8787` in
Safari (the Mac's name is under System Settings, General, Sharing) and use "Add to Home
Screen". The Mac has to be awake; `caffeinate -s` keeps it so while plugged in.

**Away from home.** Put a tunnel with a login in front of it, for example
`ngrok http 8787 --basic-auth "you:<long password>"`, and open the `https://` address it
prints. Never expose the port without a login.

## In Claude Code

Register the stdio door once and ask for drills in any session ("give me my next drill",
"check this attempt", "add MERGE to my study list"):

```bash
claude mcp add -s user drill -- /opt/homebrew/bin/uv run --directory /path/to/this/repo drill-mcp
```

The Claude desktop app takes the same command in its MCP settings. Tools: `next_drill`,
`get_drill`, `list_lessons`, `run_tests`, `hint`, `review`, `ask_tutor`, `study_list`,
`save_to_study`, `mark_done`. The web door's `/mcp` endpoint only accepts requests addressed
to this machine (`localhost`, `127.0.0.1`), a defence against DNS rebinding; add hosts with
`DRILL_ALLOWED_HOSTS` if you need to.

## In the cloud

It runs as a Databricks App today: `uv run drill cloud setup --create-lakebase`, then
`uv run drill cloud deploy`. See [DATABRICKS_APP.md](DATABRICKS_APP.md) for what it costs, how it
stops itself when idle, and how to move it to work.

Everything is configuration: `DRILL_DATABASE_URL` for Postgres (Neon on Azure, Lakebase on
Databricks), `DRILL_HOSTED_*` for a model behind Unity Gateway, and the same server
in a container on Azure Container Apps or Databricks Apps, which forwards the signed-in
user's identity in a header (`DRILL_USER_HEADER`, default `x-forwarded-email`) so each
person gets their own progress. The package carries its own content and page, so the
container needs nothing but the repository installed editable from a checkout (`-e .`, the
last line of `requirements.txt`: the code finds its page, `.env` and state next to the checkout).

## The leaderboard

A friendly weekly race (`page/board.js`). It is off until a learner switches on "Show me on the
leaderboard" in the Notebook's Settings. The page works out its own week from its progress and
saves one row: this week's and last week's points and marks, the grade, and today's trial marks.
The server keeps it in the `board` table:

| Route | Does |
|---|---|
| `GET /api/board` | every row saved in the last 15 days, each with an id (a short hash of the owner) and a name, plus `me`, the asker's id |
| `PUT /api/board` | saves the asker's row (only `v`, `week`, `last`, `grade` and `trial` are kept; at most 8 KB) |
| `DELETE /api/board` | takes the asker off the board |

The name comes from the sign-in, never the page: the first part of the work email, so
`sam.kim@…` shows as "Sam Kim" (`DRILL_BOARD_NAME` overrides it). Emails never leave the server.
Answers, questions and study lists stay private: the row holds only counts. In Lakebase, the
`board` table's policies (below) let every learner read it and write only their own row. A
Databricks App reads it as its service principal, which owns the table.

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
| `asked` | asked something in the page | `feature`, `step`, `hint_level`, `chip` |
| `tests_run`, `hint_used`, `saved_to_study` | the same, through Claude's tools | `door: mcp` |

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
each time it connects, using the login on the machine. With Lakebase set, the server
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
time, not money, on your Mac (a hint takes 5 to 20 s with it, about 1 s without), so it is
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

Traces can go to your Databricks workspace's MLflow instead of this Mac's. There are two
places Databricks can keep them, and the choice matters:

| | Traces kept in the experiment | Traces kept in Unity Catalog |
|---|---|---|
| How they get there | MLflow on your Mac uploads each trace's data straight to the workspace's storage account | MLflow sends the spans to the Databricks API, and Databricks writes them into Delta tables |
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
uv run drill tracing use local      # back to this Mac's MLflow (http://localhost:5050)
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
- **Claude Code's own traces stay on this Mac.** MLflow's Claude Code plugin (0.2.0) always
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
| `DRILL_HOST` / `DRILL_PORT` | `0.0.0.0` (`127.0.0.1` with Lakebase) / `8787` | Where the server listens; `127.0.0.1` keeps it to this machine |
| `DRILL_DATABASE_URL` | `sqlite:///.drill/drill.db` | Where progress and the study list live |
| `DRILL_LAKEBASE_ENDPOINT` | *(unset)* | The Lakebase endpoint to get passwords for; set it with a Lakebase `DRILL_DATABASE_URL` |
| `DRILL_HOME` | `.drill/` in the repo | The folder for the SQLite file and local MLflow traces, e.g. `~/Library/Application Support/DailyDrill` |
| `DRILL_OWNER` | `local` | Whose rows a local store reads and writes (Lakebase uses your Databricks user name) |
| `DRILL_HOSTED_BASE_URL`, `_MODEL`, `_API_KEY` | *(unset, so the Azure settings)* | An OpenAI-compatible hosted model, used as the fallback |
| `DRILL_HOSTED_AUTH` | `key` (`databricks` for a Databricks address with no key) | `databricks` signs requests with the Databricks login instead of a key |
| `DRILL_HOSTED_DAILY_TOKENS` | `200000` | Daily cap on hosted usage (about four characters per token) |
| `DRILL_MAX_PROMPT_CHARS` | `60000` | The biggest request (all its messages together) the server takes; bigger gets a 413 |
| `DRILL_CACHE_DAYS` / `DRILL_CACHE_MAX` | `7` / `2000` | How long a cached answer is reused, and how many are kept |
| `DRILL_FIRST_WORD_SECONDS` | `45` | Give up on a model that has not started answering by then, and try the next one |
| `DRILL_THINKING` | `complex` | When a thinking model (Qwen 3, DeepSeek R1...) may think: `off`, `complex` (reviews only) or `on` |
| `DRILL_TRACING` | `1` | One MLflow trace per request; `0` turns it off |
| `DRILL_MLFLOW_EXPERIMENT` | `daily-drill` | The experiment the traces go to (on Databricks, `/Users/<you>/daily-drill` unless you give a path) |
| `MLFLOW_TRACKING_URI` | *(unset, so `.drill/mlflow.db`)* | Where traces go: a local MLflow server, or `databricks` |
| `DATABRICKS_CONFIG_PROFILE` | *(the CLI's default)* | Which Databricks CLI profile `databricks` means |
| `DRILL_ALLOWED_HOSTS` | *(this machine)* | Extra `host:port` values the `/mcp` endpoint accepts |
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
