# interview-drill

An agentic coding-interview tutor. It picks a problem from the topic you are
weakest at, waits while you write a solution, runs it against held-back tests, and
gives you a hint instead of the answer — up to three times, then it walks you
through it.

Built on **LangGraph** for the control flow and **MLflow** for tracing, run
tracking and evaluation, against **Azure AI Foundry** for the model.

The point is to learn two things at once. Using it drills interview patterns;
rebuilding it — there is a milestone track with failing tests waiting for you —
teaches the engineering. See [docs/CURRICULUM.md](docs/CURRICULUM.md).

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
uv run pytest          # 124 tests, no credentials needed
uv run drill list      # see the problem bank
```

`drill list`, `drill check` and `drill solution` work with no credentials at all.
The tutored session (`drill start`) needs a model — below.

## Connecting Azure AI Foundry

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

If something is missing, `drill start` tells you exactly which variable — it does
not fail with an auth error from inside an SDK.

| Variable | Default | What it does |
|---|---|---|
| `DRILL_MAX_ATTEMPTS` | `3` | Tries before the tutor explains |
| `DRILL_SANDBOX_TIMEOUT` | `10` | Seconds a submission may run |
| `DRILL_PROGRESS_PATH` | `.drill/progress.json` | Where history is stored |
| `MLFLOW_TRACKING_URI` | *(unset → `./mlruns`)* | Tracking server |
| `MLFLOW_EXPERIMENT_NAME` | `interview-drill` | Experiment for traces and runs |
| `AZURE_FOUNDRY_FLAVOUR` | *(inferred)* | Force `azure_openai` or `azure_inference` |

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
uv run pytest              # 124 tests, ~8s, no credentials
uv run pytest -m rebuild   # the milestone track (fails until you implement it)
```

Everything runs offline. The graph tests use a fake chat model injected through
the config, which is the entire reason the dependencies are passed around instead
of being module globals.

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
