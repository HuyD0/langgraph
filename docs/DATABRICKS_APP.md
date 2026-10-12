# Daily Drill as a Databricks App

The same server that runs on your Mac (`uv run drill-server`) runs as a Databricks App, with
the same page, the same lessons and the same tutor. Only the settings change:

| | On your Mac | As a Databricks App |
|---|---|---|
| Who answers | Ollama, then a hosted fallback | Haiku, through a serving endpoint |
| Where progress lives | `.drill/drill.db` (SQLite) | Lakebase, in its own `drill` schema |
| Who you are | `local` | your Databricks email, from the app's sign-in |
| Traces | your Mac's MLflow | the workspace experiment (Unity Catalog tables) |

## Your personal workspace

Three commands, the first only once:

```bash
uv run drill cloud setup --create-lakebase   # Lakebase project + experiment, values saved for deploy
uv run drill cloud deploy                    # upload the code and start the app (a few minutes)
uv run drill cloud status                    # running or not, and its address
```

Open the address it prints and sign in as you would to the workspace. `drill cloud stop`
and `drill cloud start` switch it off and on.

## What it costs, and what scales to zero

| Piece | Scales to zero? | How |
|---|---|---|
| Haiku | Yes | Pay per token; nothing when nobody asks. A daily cap (`DRILL_HOSTED_DAILY_TOKENS`, 200,000) stops runaway use. |
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
- **`databricks.yml`** is the bundle: one app, the three resources it is given (a serving
  endpoint, a Lakebase database, an MLflow experiment), and two targets, `personal` and
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

## Moving it to work

Porting is setup and deploy against the `work` target. Before you start, check these with
your platform team; each one is a setting, not a code change:

1. **A CLI profile for the work workspace.** `databricks auth login --host https://adb-<id>.azuredatabricks.net --profile work`.
   The target expects a profile named `work`; pass `--profile` to use another.
2. **The Haiku you are given.** Ask which kind it is:
   - *A serving endpoint* (for example `ai-gateway-haiku`): pass it as `--model`. Nothing else changes.
   - *A Unity Gateway model service* (three parts, `catalog.schema.name`): a serving-endpoint
     resource cannot point at it. In `app.yaml`, replace the `valueFrom: serving-endpoint`
     line with `value: <catalog.schema.name>`, remove the serving-endpoint resource from
     `databricks.yml`, and have the service principal granted `EXECUTE` on the model service.
     The router already sends three-part names to `/ai-gateway/mlflow/v1`.
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

Then:

```bash
uv run drill cloud setup --target work --lakebase-project <id> --model <haiku endpoint> --experiment /Shared/daily-drill
uv run drill cloud deploy --target work
```

At work the team's Spacelift stack can run the same `databricks bundle deploy -t work`, with
the overrides file written from its own variables instead of by `drill cloud setup`.

**Managers' view.** In the app, everyone's rows are written by the app's service principal,
with each person's email as the `owner`. Register the Lakebase database in Unity Catalog
(see [SERVER.md](SERVER.md), "The manager's view") and grant managers `SELECT` on
`<catalog>.drill.docs` and `<catalog>.drill.events`. Learners use the app, which only ever
shows them their own rows.
