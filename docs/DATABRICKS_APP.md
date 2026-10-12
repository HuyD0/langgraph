# Daily Drill as a Databricks App

The same server that runs on your Mac (`uv run drill-server`) runs as a Databricks App, with
the same page, the same lessons and the same tutor. Only the settings change:

| | On your Mac | As a Databricks App |
|---|---|---|
| Who answers | Ollama, then a hosted fallback | a Claude model, through a Unity Gateway model service |
| Where progress lives | `.drill/drill.db` (SQLite) | Lakebase, in its own `drill` schema |
| Who you are | `local` | your Databricks email, from the app's sign-in |
| Traces | your Mac's MLflow | the workspace experiment (Unity Catalog tables) |

## Your personal workspace

Three commands, the first only once:

```bash
uv run drill cloud setup --create-lakebase   # Lakebase project + experiment, values saved for deploy
uv run drill cloud deploy                    # upload the code and start the app (a few minutes)
uv run drill cloud status                    # running or not, and its address
uv run drill cloud check                     # every permission the app needs (deploy runs it too)
```

Open the address it prints and sign in as you would to the workspace. `drill cloud stop`
and `drill cloud start` switch it off and on.

## What it costs, and what scales to zero

| Piece | Scales to zero? | How |
|---|---|---|
| The model | Yes | Pay per token; nothing when nobody asks. A daily cap (`DRILL_HOSTED_DAILY_TOKENS`, 200,000) stops runaway use. |
| Lakebase | Yes | The compute sleeps after 5 idle minutes and wakes in under a second on the next request. Storage is a few cents a month. |
| Traces | Mostly | Writing them costs very little. Reading them uses a SQL warehouse; pick a small serverless one with a short auto-stop. |
| The app | **No** | A running app bills about 0.5 DBU an hour whether anyone uses it or not. Databricks Apps have no scale to zero (even horizontally scaled apps keep at least one instance). |

So the app **stops itself** after 30 minutes with no requests (`DRILL_IDLE_STOP_MINUTES` in
`app.yaml`; `0` keeps it running). Stopped, it costs nothing and your progress waits in
Lakebase. Coming back is `uv run drill cloud start` (or **Start** on the app's page in the
workspace), then a minute or two while it boots. For this, `drill cloud deploy` gives the
app's service principal `CAN_MANAGE` on its own app.

## How it is put together

- **`app.yaml`** says how the app starts and where each setting comes from. It names no
  workspace: the model, the database and the experiment arrive from resources.
- **`databricks.yml`** is the bundle: one app, the three resources it is given (a Unity
  Gateway model service, a Lakebase database, an MLflow experiment), and two targets, `personal` and
  `work`. Attaching a resource grants the app's service principal what it needs on it.
- **`.databricks/bundle/<target>/variable-overrides.json`** holds the values that name real
  things (Lakebase paths, the experiment id). `drill cloud setup` writes it, and git ignores
  it, because this repository is public.
- **`requirements.txt`** is generated from `uv.lock` (`uv run drill cloud requirements`), so the
  app installs the exact versions the tests ran. Its last line, `-e .`, installs this repo.

Inside the app the server notices it is an app (`DATABRICKS_APP_NAME`) and changes three
things: it listens on the port the platform gives it, it believes the `x-forwarded-email`
header the platform's sign-in adds (and only there, so nobody on your home Wi-Fi can claim
to be someone else), and each request reads and writes that person's rows.

## What MLflow records, and where

Every name comes from settings ([`src/drill/mlflow_names.py`](../src/drill/mlflow_names.py)), so
none of it changes in code between workspaces:

| What | Where | Named by |
|---|---|---|
| The deployed app's traces | its own experiment, `/Shared/daily-drill`, traces in Unity Catalog tables `<trace_schema>.daily_drill_otel_*` | `drill cloud setup --experiment --trace-schema` |
| Your laptop's traces and evals | `daily-drill` (on Databricks `/Users/<you>/daily-drill`) | `DRILL_MLFLOW_EXPERIMENT` |
| The terminal tutor's practice runs | `daily-drill-cli` | `DRILL_CLI_MLFLOW_EXPERIMENT` |
| Prompts | `<prompt_schema>.use_case_review`, `.use_case_challenge`, alias `production` | `DRILL_PROMPT_SCHEMA` / `--prompt-schema` |
| The review cases | evaluation dataset `<prompt_schema>.review_cases` (a Unity Catalog table) | the same |
| Each app version | logged model `daily-drill-<commit>`: description, parameters (model, prompt versions, review, challenge and judge versions, target), linked prompt versions | written by `drill cloud deploy` |
| Scorers | `answer_rules`, registered on the app's experiment | written by `drill cloud deploy` |

**On every trace:** the name is what it was for (`ask_lesson`, `hint`, `use_case_review`...);
tags say `feature`, `door`, `lesson_id`, `step`, `environment` (`local` or `app`), `app_name`,
`workspace_id`, `app_version`, `model`, `route`, `cached`, and for reviews the `prompt` version;
MLflow's own fields hold the user (`mlflow.trace.user`, the signed-in email in the app), the
session (each page visit, or one Ask thread), the commit (`mlflow.source.git.commit`), the version
(`mlflow.modelId`), token counts, and the page's request id as `client_request_id`. Spans record
the full prompt, the model, timings (time to first word, total), finish reason and fallbacks, and
a `checks` span the answer rules. Feedback buttons attach HUMAN feedback (who clicked, why).

**Scoring.** The answer rules are on every trace as tags and a span. In the app they are not
written as assessments one by one, because each write to traces kept in Unity Catalog wakes the
SQL warehouse. Instead, score them in a batch, one evaluation run with a pass rate per rule:

```bash
uv run drill traces score --days 7
```

**Evals.** `drill review eval` runs the review prompt over the `review_cases` dataset, linked to the
dataset, the registered prompt version and the app version, with parameters (model, tier, prompt,
judge) and a description; its scores show on the version too. On Databricks set
`DRILL_PROMPT_SCHEMA` (and `MLFLOW_TRACING_SQL_WAREHOUSE_ID`) in `.env` first.

On Databricks a prompt's links to traces are kept with the prompt version in the registry (its page
lists the traces), not on the trace; the `prompt` tag is there to filter traces by it.

## Practising work's model catalog at home

If work names its model services in a catalog of its own (say `<gateway_catalog>.<schema>.<service>`),
make the same names in your personal workspace, so the app, `drill cloud check` and the grants
behave as they will at work. Each service routes to a Databricks-hosted model:

```bash
databricks catalogs create <gateway_catalog> --storage-root <a storage location> --profile DEFAULT
databricks schemas create <schema> <gateway_catalog> --profile DEFAULT
databricks api post "/api/2.1/unity-catalog/model-services?parent=schemas/<gateway_catalog>.<schema>&model_service_id=<service>" --profile DEFAULT --json '{
  "config": {"routing": {"destinations": [{
    "name": "system.ai.databricks-claude-sonnet-4-6",
    "destination_type": "DESTINATION_TYPE_PAY_PER_TOKEN_FOUNDATION_MODEL",
    "traffic_percentage": 100,
    "pay_per_token_config": {"model": "models/system.ai.databricks-claude-sonnet-4-6"}}]}}}'
uv run drill cloud setup --model <gateway_catalog>.<schema>.<service>
uv run drill cloud deploy
```

(A workspace on Default Storage needs a `--storage-root` for a new catalog; the one your
existing catalog uses works, since a catalog of model services stores no data.) Unlike
`system.ai`, account users have no rights on a new catalog, so the deploy has to grant the app
its access: the same path as at work, which `drill cloud check` then confirms.

## Moving it to work

Porting is setup and deploy against the `work` target. Before you start, check these with
your platform team; each one is a setting, not a code change:

1. **A CLI profile for the work workspace.** `databricks auth login --host https://adb-<id>.azuredatabricks.net --profile work`.
   The target expects a profile named `work`; pass `--profile` to use another. Use CLI v1.20 or
   newer; `bundle validate` may warn that `MODEL_SERVICE` is not a known `securable_type`, because
   the CLI's schema lags the API, which accepts it.
2. **The model you are given**, by its three-part name (`catalog.schema.name`): pass it as
   `--model`. Use one your runbook lists as a governed model service, not just one in the
   capacity inventory. It is a Unity Gateway model service on both sides (the default is
   `system.ai.claude-haiku-4-5`), attached as the app's `model` resource, so requests go through the gateway, its
   limits and its usage reports. Attaching it grants the app `EXECUTE` (and `USE CATALOG`,
   `USE SCHEMA`), but only if you hold `MANAGE` on it or every account user already has those
   rights; otherwise ask the platform team to grant the app's service principal directly.
3. **Lakebase.** Use a project the platform team gives you (`--lakebase-project <id>`), or
   create one with `--create-lakebase` if you are allowed. The app creates and owns its
   `drill` schema, so no admin SQL is needed for the app itself.
4. **Where traces go.** A shared path suits a team: `--experiment /Shared/daily-drill`.
   Behind a storage firewall, create the experiment linked to a Unity Catalog schema first
   (`uv run drill tracing check --uc-schema <catalog>.<schema>`, see [SERVER.md](SERVER.md)),
   and grant the app's service principal `USE CATALOG`, `USE SCHEMA`, `SELECT` and `MODIFY` there.
5. **Experiments and prompts at work.** `/Shared` may be locked down: pass a team folder with
   `--experiment /Workspace/Groups/<team>/daily-drill` or similar. Give `--trace-schema` and
   `--prompt-schema` schemas your team owns. Registering scorers and evaluation datasets from your
   laptop uses the `databricks-agents` package (a dev dependency: `uv sync`); the app does not need it.
   Tools on your laptop may set `MLFLOW_EXPERIMENT_NAME` (Claude Code's tracing does); every drill
   command names its experiment outright, so they can't redirect it.
6. **Network.** The app installs packages from PyPI when it deploys. If egress is locked down,
   allow `pypi.org` and `files.pythonhosted.org`, or set `PIP_INDEX_URL` to your mirror as an
   app secret. With Private Link, apps live under `*.azure.databricksapps.com`, which needs its
   own private DNS zone.
7. **Limits for a team.** The daily token cap is shared by everyone using the app: raise
   `DRILL_HOSTED_DAILY_TOKENS` in `app.yaml`, or rely on the gateway's per-user limits. With
   people studying all day, a longer `DRILL_IDLE_STOP_MINUTES` (or `0`) avoids cold starts.

Before deploying, `uv run drill cloud check --target work` says whether you can: it checks
your sign-in, that the model service, Lakebase project and experiment exist, and that you hold
the rights the deploy must hand on to the app. After deploying (which runs it again), it checks
the app's service principal itself, and `--fix` grants what is missing where you are allowed to.

| The app needs | On | Given by |
|---|---|---|
| `USE CATALOG`, `USE SCHEMA`, `EXECUTE` | the model service | the `model` resource |
| a Postgres role | the Lakebase branch | the `postgres` resource |
| `CAN_EDIT` | the MLflow experiment | the `experiment` resource |
| `USE CATALOG`, `USE SCHEMA`, `SELECT`, `MODIFY` | the trace tables (spans, logs and annotations) | nobody: `--fix`, or the platform team |
| `CAN_USE` | the SQL warehouse, to attach feedback to those traces | the `sql-warehouse` resource (or the workspace `users` group) |
| `USE CATALOG`, `USE SCHEMA`, `EXECUTE` | the prompts schema, to link traces to prompt versions | nobody: `--fix`, or the platform team |
| `CAN_MANAGE` | its own app, to stop when idle | `drill cloud deploy` |

And **you** need `USE SCHEMA`, `CREATE FUNCTION`, `CREATE TABLE` and `EXECUTE` on the prompts schema
to register the prompts and the review cases; `drill cloud check` says so before you try.

At home every account user holds broad rights, so all of this passes without effort; at work
the trace tables are the one most likely to need a grant.

Then:

```bash
uv run drill cloud setup --target work --lakebase-project <id> --model <catalog.schema.service> \
  --experiment /Shared/daily-drill --trace-schema <catalog.schema> --prompt-schema <catalog.schema> --warehouse <id>
uv run drill cloud check --target work
uv run drill cloud deploy --target work
```

At work the team's Spacelift stack can run the same `databricks bundle deploy -t work`, with
the overrides file written from its own variables instead of by `drill cloud setup`.

**Managers' view.** In the app, everyone's rows are written by the app's service principal,
with each person's email as the `owner`. Register the Lakebase database in Unity Catalog
(see [SERVER.md](SERVER.md), "The manager's view") and grant managers `SELECT` on
`<catalog>.drill.docs` and `<catalog>.drill.events`. Learners use the app, which only ever
shows them their own rows.
