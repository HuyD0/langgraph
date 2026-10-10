# daily-drill

An agentic coding-interview tutor. It picks a problem from the topic you are
weakest at, waits while you write a solution, runs it against held-back tests, and
gives you a hint instead of the answer — up to three times, then it walks you
through it.

Built on **LangGraph** for the control flow and **MLflow** for tracing, run
tracking and evaluation, against **Azure AI Foundry** for the model.

The point is to learn two things at once. Using it drills interview patterns;
rebuilding it — there is a track of milestone notebooks with failing tests waiting for you —
teaches the engineering. See [docs/CURRICULUM.md](docs/CURRICULUM.md), and
[docs/TEACHING.md](docs/TEACHING.md) if you are running a session for other people.

A session looks like this (the hint text is illustrative — everything else is
real output):

```
$ uv run drill start

╭─ Two Sum · easy · hash-map ──────────────────────────────────────────────╮
│ Given a list of integers `nums` and an integer `target`, return the      │
│ indices of the two numbers that add up to `target`.                      │
╰──────────────────────────────────── target: O(n) time, O(n) space ───────╯

  example call            expected
  two_sum([2,7,11,15], 9) [0, 1]

attempt 1 of 3
[your $EDITOR opens]

2/5 test cases passed
╭─ first failing case ─────────────────────────────────────────────────────╮
│ call:     ([3, 2, 4], 6)                                                 │
│ expected: [1, 2]                                                         │
│ got:      [0, 1]                                                         │
╰──────────────────────────────────────────────────────────────────────────╯
╭─ hint ───────────────────────────────────────────────────────────────────╮
│ Your code finds the first pair that works from the left. Walk through    │
│ [3, 2, 4] by hand — which pair does it land on, and which one did the    │
│ problem want? What are you checking against as you scan?                 │
╰──────────────────────────────────────────────────────────────────────────╯
```

## Quick start

```bash
uv sync --dev          # install
uv run pytest          # 143 tests, no credentials needed
uv run drill list      # see the problem bank
```

`drill list`, `drill check` and `drill solution` work with no credentials at all.
The tutored session (`drill start`) needs a model — below.

## Connecting Azure AI Foundry

### Provision it from scratch

If you do not have a Foundry resource yet, `scripts/azure_up.sh` creates one and
writes your `.env`. It needs the Azure CLI and `jq`, and it signs you in if you
are not already.

```bash
scripts/azure_up.sh          # ~2 minutes, prompts before it creates anything
uv run drill start
```

It makes a resource group, an `AIServices` resource, and one chat deployment
named `drill-chat`. The model is whichever of `gpt-5.4-nano`, `gpt-5-nano`,
`gpt-5.4-mini`, `gpt-5-mini`, `gpt-4.1-mini`, `gpt-4o-mini` your subscription can
*actually* deploy in that region — it skips versions Azure lists but has marked
`Deprecating`, which otherwise fail with `ServiceModelDeprecating`. It then asks
the deployed model whether it accepts a custom temperature (reasoning models
reject one) and writes `DRILL_TEMPERATURE` to match. Deployments are
pay-per-token, so an idle resource costs nothing. Re-running the script is safe:
it reuses whatever already exists.

**Your subscription must be Pay-As-You-Go.** Azure allocates *zero* tokens/min of
Azure OpenAI quota to Free Trial, Azure Pass and Lightweight Trial subscriptions,
for every model and every region — deployment fails with `InsufficientQuota`. The
script checks your offer type up front and says so before creating anything.
Upgrading keeps any remaining free credit.

Override the defaults with environment variables:

```bash
DRILL_LOCATION=swedencentral DRILL_MODEL=gpt-4o scripts/azure_up.sh
```

`DRILL_RG`, `DRILL_LOCATION`, `DRILL_ACCOUNT`, `DRILL_DEPLOYMENT`, `DRILL_MODEL`
and `DRILL_CAPACITY` are all honoured. When you are done, `scripts/azure_down.sh`
deletes the resource group and purges the soft-deleted resource so it stops
holding your model quota.

### Or point it at a resource you already have

A Foundry resource exposes one of two chat surfaces. You do not have to work out
which you have: the endpoint URL is inspected and the right client is used. Put
the values in a `.env` at the repo root (it is gitignored) or export them.

**Azure OpenAI deployments** — endpoint ends in `.openai.azure.com`:

```bash
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_KEY=<key>
# AZURE_OPENAI_API_VERSION=2024-10-21   # optional, this is the default
```

**Foundry models endpoint** — endpoint ends in `.services.ai.azure.com/models`:

```bash
AZURE_INFERENCE_ENDPOINT=https://<your-resource>.services.ai.azure.com/models
AZURE_OPENAI_DEPLOYMENT=<your-model-name>
AZURE_OPENAI_API_KEY=<key>
```

**Service principal instead of a key** — set these three and leave the key unset,
and an AAD token is fetched and refreshed for you:

```bash
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
```

### Or run a local model with Ollama

No Azure, no keys, works offline. Install [Ollama](https://ollama.com), pull a
model, and name it:

```bash
brew install ollama && brew services start ollama
ollama pull gemma3:12b
```

```bash
OLLAMA_MODEL=gemma3:12b
# OLLAMA_BASE_URL=http://localhost:11434/v1   # optional, this is the default
```

`OLLAMA_MODEL` takes precedence over any Azure settings, so comment it out to go
back to Foundry. The tutor only needs plain-text replies, no tool calling, so any
instruction-tuned chat model works. Expect weaker hints than a hosted model.
A 12B model needs about 8 GB of free memory.

### Or route through an MLflow AI Gateway

An MLflow server (3.x) has a built-in AI Gateway: you create named endpoints in its
UI, each pointed at a model (Ollama, Azure, Databricks...), and every call through
it is recorded. Point the tutor at an endpoint by name:

```bash
MLFLOW_GATEWAY_ENDPOINT=drill-tutor
# MLFLOW_GATEWAY_URL=http://localhost:5050/gateway/mlflow/v1   # optional, this is the default
MLFLOW_TRACKING_URI=http://localhost:5050                      # send the tutor's traces there too
```

`MLFLOW_GATEWAY_ENDPOINT` takes precedence over `OLLAMA_MODEL` and Azure. Switching
the model behind the tutor is then done in the gateway, not in `.env`. The server
must be running while you practise.

If something is missing, `drill start` tells you exactly which variable — it does
not fail with an auth error from inside an SDK.

| Variable | Default | What it does |
|---|---|---|
| `DRILL_TEMPERATURE` | `0.2` | Sampling temperature; **empty** omits it, which reasoning models require |
| `DRILL_MAX_ATTEMPTS` | `3` | Tries before the tutor explains |
| `DRILL_SANDBOX_TIMEOUT` | `10` | Seconds a submission may run |
| `DRILL_PROGRESS_PATH` | `.drill/progress.json` | Where history is stored |
| `MLFLOW_TRACKING_URI` | *(unset → `./mlruns`)* | Tracking server |
| `MLFLOW_EXPERIMENT_NAME` | `daily-drill` | Experiment for traces and runs |
| `AZURE_FOUNDRY_FLAVOUR` | *(inferred)* | Force `azure_openai` or `azure_inference` |
| `OLLAMA_MODEL` | *(unset)* | Use a local Ollama model instead of Azure |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Where Ollama is listening |
| `MLFLOW_GATEWAY_ENDPOINT` | *(unset)* | Use an MLflow AI Gateway endpoint; wins over everything |
| `MLFLOW_GATEWAY_URL` | `http://localhost:5050/gateway/mlflow/v1` | Where the gateway is |

## Run the tutor as a local service

The Daily Drill page (`web/daily-drill`) can be served from your own machine instead of
claude.ai, with Ollama answering for free and your progress in a SQLite file. One small
server, two doors, one core (`src/drill/server`):

```bash
uv run drill-server
# the page:  http://localhost:8787
# the tools: http://localhost:8787/mcp   (MCP over HTTP, for Claude Code)
```

The first run builds the page and creates `.drill/drill.db`. macOS will ask once whether
to allow incoming connections; say yes if you want the phone to reach it.

**Which model answers.** Ollama on this Mac first (`OLLAMA_MODEL`, or whichever pulled
model answers without "thinking" first, so hints take seconds). A hosted model is the
fallback: the Azure settings above, or any OpenAI-compatible endpoint named with
`DRILL_HOSTED_BASE_URL` / `DRILL_HOSTED_MODEL` / `DRILL_HOSTED_API_KEY`, such as a
Databricks serving endpoint. Only "complex" jobs (reviews) start with the hosted model, and
it stops being used past `DRILL_HOSTED_DAILY_TOKENS` a day. Every answer is cached by its
exact prompt, so asking the same hint twice is free.

**From your phone, at home.** Same Wi-Fi, nothing to install: open
`http://<your-mac-name>.local:8787` in Safari (the Mac's name is under System Settings →
General → Sharing) and use "Add to Home Screen". The Mac has to be awake; `caffeinate -s`
keeps it so while plugged in.

**From your phone, away from home.** Put a tunnel with a login in front of it, for example
`ngrok http 8787 --basic-auth "you:<long password>"`, and open the `https://` address it
prints. Never expose the port without a login.

**In Claude Code.** Register the stdio door once and ask for drills in any session
("give me my next drill", "check this attempt", "add MERGE to my study list"):

```bash
claude mcp add -s user drill -- /opt/homebrew/bin/uv run --directory /path/to/this/repo drill-mcp
```

The Claude desktop app takes the same command in its MCP settings. Tools: `next_drill`,
`get_drill`, `list_lessons`, `run_tests`, `hint`, `review`, `ask_tutor`, `study_list`,
`save_to_study`, `mark_done`. The web door's `/mcp` endpoint only accepts requests addressed
to this machine (`localhost`, `127.0.0.1`), a defence against DNS rebinding; add hosts with
`DRILL_ALLOWED_HOSTS` if you need to.

**Later, in the cloud.** Everything is configuration: `DRILL_DATABASE_URL` for Postgres
(Neon on Azure, Lakebase on Databricks), `DRILL_HOSTED_*` for a serving endpoint behind AI
Gateway, and the same server in a container on Azure Container Apps or Databricks Apps,
which forwards the signed-in user's identity in a header (`DRILL_USER_HEADER`, default
`x-forwarded-email`) so each person gets their own progress.

| Variable | Default | What it does |
|---|---|---|
| `DRILL_HOST` / `DRILL_PORT` | `0.0.0.0` / `8787` | Where the server listens; `127.0.0.1` keeps it to this machine |
| `DRILL_DATABASE_URL` | `sqlite:///.drill/drill.db` | Where progress and the study list live |
| `DRILL_HOSTED_BASE_URL`, `_MODEL`, `_API_KEY` | *(unset → Azure settings)* | An OpenAI-compatible hosted model, used as the fallback |
| `DRILL_HOSTED_DAILY_TOKENS` | `200000` | Daily cap on hosted usage (about four characters per token) |
| `DRILL_FIRST_WORD_SECONDS` | `45` | Give up on a model that has not started answering by then, and try the next one |
| `DRILL_THINKING` | `complex` | When a thinking model (Qwen 3, DeepSeek R1...) may think: `off`, `complex` (reviews only) or `on` |
| `DRILL_TRACING` | `1` | One MLflow trace per answer; `0` turns it off |
| `DRILL_ALLOWED_HOSTS` | *(this machine)* | Extra `host:port` values the `/mcp` endpoint accepts |
| `DRILL_USER_HEADER` | `x-forwarded-email` | Header a login proxy uses to say who is asking |

**What gets measured.** Every answer is one MLflow trace, in `.drill/mlflow.db` unless
`MLFLOW_TRACKING_URI` points elsewhere (`uv run mlflow ui --backend-store-uri
sqlite:///.drill/mlflow.db`, experiment `daily-drill`): which route and model answered, the tier, whether it was a cache hit,
whether the model was allowed to think, token counts in MLflow's own format so the token
and cost dashboards work, total time, and a `first_word` child span whose length is the
**time to first token**, the wait the learner actually feels. Thinking costs time, not
money, on your Mac (a hint takes 5–20 s with it, about 1 s without), so it is off for
hints and on for reviews by default.

## Commands

```bash
uv run drill start                        # weakest topic picks the problem
uv run drill start --problem two_sum      # a specific problem
uv run drill start --topic sliding-window # a specific topic
uv run drill list                         # the bank, with what you have solved
uv run drill stats                        # solve rate per topic
uv run drill check mine.py -p two_sum     # just run the tests, no tutor, no LLM
uv run drill solution two_sum             # the worked answer
```

## How it works

```
START -> select_problem -> await_submission -> run_tests
                                ^                  |
                                |    passed -------+---> review --+
                                |    no tries left -+--> explain --+
                                +--- otherwise ----+--> hint       |
                                                                   v
                                                         record -> END
```

`await_submission` calls LangGraph's `interrupt()`, which suspends the entire
graph and hands control back to the CLI. You write code; the CLI resumes with
`Command(resume={"submission": ...})` and the node picks up where it left off.
That is what makes this a human-in-the-loop agent rather than a chatbot, and it is
why a checkpointer is mandatory — there has to be somewhere to save the
half-finished state.

The loop from `hint` back to `await_submission` is the reason this is a graph and
not a pipeline.

| Module | Job |
|---|---|
| `config.py` | Settings from the environment. No I/O at import. |
| `llm.py` | Builds the Azure Foundry chat model, either surface. |
| `state.py` | The state every node reads and writes. |
| `problems/` | The problem bank. |
| `sandbox.py` | Runs submissions in a subprocess with a timeout. |
| `nodes.py` | One function per step. |
| `graph.py` | The wiring. |
| `session.py` | Drives one session; calls back for code. |
| `tracking.py` | MLflow traces and per-session runs. |
| `evaluation.py` | Scores the tutor — mainly, does it leak answers. |
| `cli.py` | The terminal. |

### On the sandbox

`sandbox.py` runs **your** code on **your** machine in a subprocess with a
timeout. That protects you from the infinite loop you will eventually write and
stops a crash from taking the session down. It is **not** a security boundary and
does not try to be — code run through it has your privileges. Do not paste
anything you would not run directly.

### On MLflow

One `mlflow.langchain.autolog()` call traces the whole graph: every node, every
prompt, every response. Each session is also an MLflow run with metrics
(`attempts`, `hints_used`, `solved`, `duration_s`) tagged by topic — so after a
couple of weeks you have an honest chart of what you are still bad at.

```bash
uv run mlflow ui     # http://localhost:5000
```

`drill.evaluation` scores the tutor itself. The rule that matters is that hints
must never contain code, and it is checked by a deterministic detector — regexes
for the obvious shapes, plus Python's own parser for the rest, because no regex
can tell `for i in range(n):` from the English phrase "...for each element in the
list:". Edit a prompt, re-run the eval, and a regression shows up as a number.

## Tests

```bash
uv run pytest                      # 143 tests, ~35s, no credentials
uv run pytest -m "not slow"        # skip the notebook executions, ~10s
uv run jupyter lab notebooks/      # the milestone track (tests run inside each notebook)
```

Everything runs offline. The graph tests use a fake chat model injected through the
config, which is the entire reason the dependencies are passed around instead of
being module globals.

The notebooks are tested too, which matters if you teach from them.
`tests/test_notebooks.py` substitutes the answer key in `notebooks/solutions/`
into every exercise cell, executes each notebook in a real kernel, and requires
all of its embedded tests to pass. That catches a spec that cannot be satisfied,
and it catches drift — an exercise renamed without updating the key, or a stale
solution left behind. A second CI job fails if a notebook is ever committed with
its `TODO`s already filled in.

## History

This started as a Databricks Asset Bundle containing a LangGraph map-reduce RAG
agent. That code was replaced, and some of it is worth recording as a warning:

- The project was named `langgraph` in `pyproject.toml`, shadowing the real
  package, and its console script pointed at a module that did not exist.
- The package directory was `src/lg-agent` — not a legal Python identifier, so its
  `__init__.py` could never be imported. The notebook worked around it with a bare
  `from agent import ...` that depended on the working directory.
- `agent.py` built a `WorkspaceClient`, a `ChatDatabricks` and an Azure Search
  client at import time, so importing the module required live cloud credentials.
  Nothing in it could be unit-tested.
- `tests/` contained no tests, and `conftest.py` raised `ImportError` unless
  `databricks-connect` was installed — so `pytest` failed before collecting
  anything.

The last two are the ones to take forward: **side effects at import time make code
untestable**, and **a test suite you cannot run is not a test suite**.
