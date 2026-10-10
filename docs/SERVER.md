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

Every answer is one MLflow trace, in `.drill/mlflow.db` unless `MLFLOW_TRACKING_URI` points
elsewhere (`uv run mlflow ui --backend-store-uri sqlite:///.drill/mlflow.db`, experiment
`daily-drill`): which route and model answered, the tier, whether it was a cache hit,
whether the model was allowed to think, token counts in MLflow's own format so the token
and cost dashboards work, total time, and a `first_word` child span whose length is the
**time to first token**, the wait the learner actually feels. Thinking costs time, not
money, on your Mac (a hint takes 5 to 20 s with it, about 1 s without), so it is off for
hints and on for reviews by default.

## Knobs

| Variable | Default | What it does |
|---|---|---|
| `DRILL_HOST` / `DRILL_PORT` | `0.0.0.0` / `8787` | Where the server listens; `127.0.0.1` keeps it to this machine |
| `DRILL_DATABASE_URL` | `sqlite:///.drill/drill.db` | Where progress and the study list live |
| `DRILL_HOSTED_BASE_URL`, `_MODEL`, `_API_KEY` | *(unset, so the Azure settings)* | An OpenAI-compatible hosted model, used as the fallback |
| `DRILL_HOSTED_DAILY_TOKENS` | `200000` | Daily cap on hosted usage (about four characters per token) |
| `DRILL_FIRST_WORD_SECONDS` | `45` | Give up on a model that has not started answering by then, and try the next one |
| `DRILL_THINKING` | `complex` | When a thinking model (Qwen 3, DeepSeek R1...) may think: `off`, `complex` (reviews only) or `on` |
| `DRILL_TRACING` | `1` | One MLflow trace per answer; `0` turns it off |
| `DRILL_ALLOWED_HOSTS` | *(this machine)* | Extra `host:port` values the `/mcp` endpoint accepts |
| `DRILL_USER_HEADER` | `x-forwarded-email` | Header a login proxy uses to say who is asking |
