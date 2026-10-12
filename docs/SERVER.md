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
incoming connections; say yes if you want the phone to reach it.

## Which model answers

Ollama on this Mac first (`OLLAMA_MODEL`, or whichever pulled model answers without
"thinking" first, so hints take seconds). A hosted model is the fallback: the Azure settings
in [SETUP.md](SETUP.md), or any OpenAI-compatible endpoint named with `DRILL_HOSTED_BASE_URL`
/ `DRILL_HOSTED_MODEL` / `DRILL_HOSTED_API_KEY`, such as a Databricks serving endpoint. Only
"complex" jobs (reviews) start with the hosted model, and it stops being used past
`DRILL_HOSTED_DAILY_TOKENS` a day. Every answer is cached by its exact prompt, so asking the
same hint twice is free.

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

## Later, in the cloud

Everything is configuration: `DRILL_DATABASE_URL` for Postgres (Neon on Azure, Lakebase on
Databricks), `DRILL_HOSTED_*` for a serving endpoint behind AI Gateway, and the same server
in a container on Azure Container Apps or Databricks Apps, which forwards the signed-in
user's identity in a header (`DRILL_USER_HEADER`, default `x-forwarded-email`) so each
person gets their own progress. The package carries its own content and page, so the
container needs nothing but `pip install .`.

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
  question) and `guard` (`solution_request` when the page turned a request for the solution
  into a hint). Search them in the UI, for example `tags.lesson_id = 'claim_gate'`.
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
is tried again every 30 seconds, so starting MLflow later turns it back on, and no answer
ever waits for it.

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

Traces can go to your Databricks workspace's MLflow instead of this Mac's. Put two lines in
`.env` and restart the server:

```bash
MLFLOW_TRACKING_URI=databricks
DATABRICKS_CONFIG_PROFILE=DEFAULT   # the CLI profile for your workspace
```

The experiment becomes `/Users/<you>/daily-drill` (Databricks needs a workspace path; set
`DRILL_MLFLOW_EXPERIMENT=/Shared/...` to choose another). Check it first:

```bash
uv run drill tracing check
```

It says where traces go, creates the experiment, writes one test trace and reads it back.

**Before you switch:**

- **A storage firewall stops it working from your Mac.** Traces are written to the
  workspace's own storage account. If the workspace has its default storage firewall on
  (`defaultStorageFirewall: Enabled`), only the workspace's own networks may write there.
  Your Mac can still create the experiment, but every trace's data is refused (403
  `AuthorizationFailure`), and `drill tracing check` says so. Keep tracing on this Mac then,
  or log from code that runs inside Databricks.
- **Experiment storage is free to browse; Unity Catalog storage is not.** By default traces
  are kept in the experiment itself, up to 100,000 per experiment, and reading them in the
  UI or with `mlflow.search_traces` needs no SQL warehouse. If an experiment stores its
  traces in Unity Catalog tables, every read needs a SQL warehouse, which costs compute;
  `drill tracing check` tells you which kind you have.
- **What does cost money:** built-in LLM judges (they call a Databricks-hosted model),
  production monitoring (serverless compute), and model calls through the gateway.
- Old traces stay on this Mac; nothing is copied over. To go back, set
  `MLFLOW_TRACKING_URI` to your local server again.
- The notebooks always use their own local stores, whatever `.env` says.

## Knobs

| Variable | Default | What it does |
|---|---|---|
| `DRILL_HOST` / `DRILL_PORT` | `0.0.0.0` / `8787` | Where the server listens; `127.0.0.1` keeps it to this machine |
| `DRILL_DATABASE_URL` | `sqlite:///.drill/drill.db` | Where progress and the study list live |
| `DRILL_HOSTED_BASE_URL`, `_MODEL`, `_API_KEY` | *(unset, so the Azure settings)* | An OpenAI-compatible hosted model, used as the fallback |
| `DRILL_HOSTED_DAILY_TOKENS` | `200000` | Daily cap on hosted usage (about four characters per token) |
| `DRILL_FIRST_WORD_SECONDS` | `45` | Give up on a model that has not started answering by then, and try the next one |
| `DRILL_THINKING` | `complex` | When a thinking model (Qwen 3, DeepSeek R1...) may think: `off`, `complex` (reviews only) or `on` |
| `DRILL_TRACING` | `1` | One MLflow trace per request; `0` turns it off |
| `DRILL_MLFLOW_EXPERIMENT` | `daily-drill` | The experiment the traces go to (on Databricks, `/Users/<you>/daily-drill` unless you give a path) |
| `MLFLOW_TRACKING_URI` | *(unset, so `.drill/mlflow.db`)* | Where traces go: a local MLflow server, or `databricks` |
| `DATABRICKS_CONFIG_PROFILE` | *(the CLI's default)* | Which Databricks CLI profile `databricks` means |
| `DRILL_ALLOWED_HOSTS` | *(this machine)* | Extra `host:port` values the `/mcp` endpoint accepts |
| `DRILL_USER_HEADER` | `x-forwarded-email` | Header a login proxy uses to say who is asking |
