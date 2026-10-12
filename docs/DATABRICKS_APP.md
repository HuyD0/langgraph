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
   The target expects a profile named `work`; pass `--profile` to use another.
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
5. **Network.** The app installs packages from PyPI when it deploys. If egress is locked down,
   allow `pypi.org` and `files.pythonhosted.org`, or set `PIP_INDEX_URL` to your mirror as an
   app secret. With Private Link, apps live under `*.azure.databricksapps.com`, which needs its
   own private DNS zone.
6. **Limits for a team.** The daily token cap is shared by everyone using the app: raise
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
| `USE CATALOG`, `USE SCHEMA`, `SELECT`, `MODIFY` | the trace tables (spans and logs) | nobody: `--fix`, or the platform team |
| `CAN_MANAGE` | its own app, to stop when idle | `drill cloud deploy` |

At home every account user holds broad rights, so all of this passes without effort; at work
the trace tables are the one most likely to need a grant.

Then:

```bash
uv run drill cloud setup --target work --lakebase-project <id> --model <catalog.schema.service> --experiment /Shared/daily-drill
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
