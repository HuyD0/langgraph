# Putting Daily Drill in a work workspace

How to run Daily Drill in an Azure Databricks workspace for a team: the app, everyone's
progress in Lakebase, and a dashboard for managers. Nothing in the code changes; only settings,
which stay in a git-ignored file because this repository is public.

## The quick way

From a clone of this repository, on a Mac:

```bash
./scripts/port-to-workspace.sh
```

It installs or upgrades the tools (git, uv, the Databricks CLI v1.20+), signs you in, asks
four questions, shows the plan and asks before changing anything. Run it again any time; it
only fills gaps. The same thing by hand:

```bash
databricks auth login --host https://adb-<id>.azuredatabricks.net --profile work
uv run drill cloud port --target work --catalog <team catalog> --model <catalog.schema.service>
uv run drill cloud port --target work --catalog <team catalog> --model <catalog.schema.service> \
  --apply --managers <managers group> --learner <email>
```

## Before you start

| You need | Why |
|---|---|
| **Databricks Apps** and **serverless** on in the workspace | The app, and the warehouse the dashboard reads through |
| **Lakebase** (Autoscaling) in the workspace's region | Everyone's progress, study lists and activity |
| A **governed model service** in Unity Gateway, `catalog.schema.service` | The tutor's model, with the gateway's limits and usage reports |
| A **catalog** your team owns | Traces and prompts go in schemas inside it |
| **Network**: the app can reach PyPI (or a mirror via `PIP_INDEX_URL`); with Private Link, a private DNS zone for `*.azure.databricksapps.com` | The app installs its packages when it deploys |
| Rights to create schemas, a SQL warehouse, a Lakebase project and a catalog, and to grant on them | The script creates and grants these; `drill cloud port` says which are missing |

## What gets created

| Thing | Name | Notes |
|---|---|---|
| Schema for traces | `<catalog>.drill_traces` | MLflow keeps the app's traces here, so a storage firewall doesn't block them |
| Schema for prompts | `<catalog>.daily_drill` | Prompt versions, scorers and review cases |
| SQL warehouse | `daily-drill` | 2X-Small serverless, stops after 5 idle minutes |
| Lakebase project | `daily-drill` | Sleeps after 5 idle minutes |
| Experiment | `/Shared/daily-drill` (or `--experiment`) | Traces kept in `<catalog>.drill_traces` |
| App | `daily-drill` | Stops itself after 30 idle minutes |
| Catalog over Lakebase | `daily_drill_lakebase` | Read-only, for the dashboard |
| Dashboard | "Daily Drill: learners" | In your workspace folder, shared with the managers group |

## Who sees what

- **Learners** (`--learner`, or later `uv run drill cloud share <email>`) can use the app, and
  only ever see their own progress, study list and questions.
- **Managers** (`--managers <group>`) can use the app and read the dashboard: every learner's
  progress, where they're stuck, their study list, their questions and a weekly note.
- Tell learners up front that their manager can see this.

## What it costs

The app bills about 0.5 DBU an hour while it runs and stops itself after 30 idle minutes
(`DRILL_IDLE_STOP_MINUTES` in `app.yaml`; raise it if people study all day, to avoid cold
starts). The model is pay per token through the gateway; the app caps itself at 200,000 tokens a
day shared by everyone (`DRILL_HOSTED_DAILY_TOKENS`), which the weekly notes also use. Lakebase
and the warehouse sleep when idle.

## When something is blocked

`drill cloud port` marks each blocked line with what to do. The usual ones:

| Blocked | Do this |
|---|---|
| signed in with profile 'work' | `databricks auth login --host https://adb-<id>.azuredatabricks.net --profile work` |
| Databricks Apps enabled / Lakebase available | Turn the feature on for the workspace, or use one that has it |
| model service | Create it in Unity Gateway, or pass `--model` with one that exists |
| catalog | Create the catalog, or pass `--catalog` with one you own |
| a grant after deploy | `uv run drill cloud check --target work --fix`, or grant what it lists |
| the deploy fails installing packages | Network: let apps reach PyPI, or set `PIP_INDEX_URL` as an app secret |

`uv run drill cloud check --target work` lists every permission the app needs and whether it
has it, at any time.

## Day to day

```bash
uv run drill cloud status --target work      # running or not, and its address
uv run drill cloud start  --target work      # after it stopped itself
uv run drill cloud deploy --target work      # after merging changes to the app
uv run drill cloud share <email> --target work
```

## Taking it down

Stop it with `uv run drill cloud stop --target work`; progress stays in Lakebase. To remove it
entirely, delete the app, the dashboard, the `daily_drill_lakebase` catalog, the Lakebase
project (this deletes everyone's progress), the warehouse and the two schemas, in the workspace
UI or with the Databricks CLI.

More detail: [DATABRICKS_APP.md](DATABRICKS_APP.md).
