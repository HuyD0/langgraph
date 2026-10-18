# Putting Daily Drill in a work workspace

How to run Daily Drill in an Azure Databricks workspace for a team: the app, everyone's
progress in Lakebase, and a dashboard for managers. Nothing in the code changes; only settings,
which stay in a git-ignored file because this repository is public, and the real lessons, which
live in an overlay folder of the work copy ("Keeping the work copy in step", below).

## The quick way

From a clone of this repository, on a Mac:

```bash
./scripts/port-to-workspace.sh
```

On Windows, in PowerShell (it installs the tools with `winget` instead of Homebrew):

```powershell
.\scripts\port-to-workspace.ps1
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

## Writing changes that port well

This part is for changes made **here**, in the public repository. The setup below is one way to
run a downstream copy. A downstream may merge whole releases, pick single commits, or adapt a
change to its own code, and this repository is not the source of truth for what it keeps
privately. So write each change so that it still makes sense when taken on its own.

**Which parts change how often.** This is a *proposal*, read from how the repository is built
today; nothing promises any of it yet.

| Kind | Paths | Why |
|---|---|---|
| Surfaces others rely on: change with care and say so | Lesson `id`s in `src/drill/content/modules/` and packs (progress is saved under them; pack lessons name core ids in `prerequisites`); the pack format and `content-packs/PUBLIC` ([CONTENT_PACKS.md](CONTENT_PACKS.md)); `/api/*` routes and MCP tools ([SERVER.md](SERVER.md)); `drill` commands and flags; variables in `app.yaml` and `databricks.yml`; `tests/test_scrub.py` and its denylist settings; `templates/enterprise/overlay.yml`; `scripts/hooks/pre-push` | A downstream copy, a deployed app or a learner's saved progress depends on the name or shape |
| Generated: regenerate, never hand-edit | `dist/` and `docs/tutor/CURRICULUM_MAP.md` (both git-ignored), `requirements.txt` (`uv run drill cloud requirements`, from `uv.lock`), `docs/screens/` (`node scripts/screenshots.mjs`), `src/drill/content/prepared/` (`uv run drill tutor prepare`, which calls a paid model) | A downstream copy can regenerate them instead of merging them |
| Examples and learning material | `notebooks/`, `ai-starter/`, `docs/course/`, `docs/proposals/`, `docs/research/` | Self-contained; safe to skip or take as they are |
| Implementation details: expected to change often | `src/drill/content/page.html`, `page/`, `tokens.css`, lesson wording, server internals behind the routes | Change freely, as long as the surfaces above keep working |

**Conventions** (the short list is in [AGENTS.md](../AGENTS.md), "Changes that port well"):

- One topic per pull request and per commit. Keep refactors, renames and reformatting out of
  behaviour changes, in pull requests of their own.
- A behaviour change comes with a test that shows it; generated files are regenerated in the same
  pull request.
- The pull request description says which areas it touches (the table in AGENTS.md) and has a
  **Compatibility** line: "none", or what breaks for someone who relied on a surface above and
  how to move over. To rename a pack lesson's id, keep the old one in `aliases`
  ([CONTENT_PACKS.md](CONTENT_PACKS.md)).
- Nothing about a downstream copy goes into this repository: no names, addresses, paths, branch
  names or code. The scrub (below) catches some of it, not all of it.

**Checks that exist today:**

| Where | What runs |
|---|---|
| Before each commit | `scripts/check.sh`: `uv run drill build-page`, `uv run drill tutor map`, `uv run pytest -q -m "not slow"` (includes the scrub) |
| Before each push, once set up | `scripts/hooks/pre-push` (`git config core.hooksPath scripts/hooks`): `uv run pytest -q tests/test_scrub.py` |
| CI, `.github/workflows/tests.yml` | `uv sync --dev`, then the full `uv run pytest -q` (with the `slow` notebook tests) on Python 3.12 with no cloud credentials; a job that fails if a `notebooks/m*.ipynb` has no `NotImplementedError` left |
| CI, `.github/workflows/codeql.yml` | CodeQL `security-and-quality` on Python and JavaScript, pull requests to `main` and weekly |
| GitHub settings | Secret scanning and push protection are on |

**Releases are tags.** Each time `main` is published to the claude.ai page as version N, that commit
is tagged `v0.N`, so a tag is a build someone has looked at. `git tag` lists them; the work copy merges
tags, never `main`.

**Not automated, on purpose.** A sync script, a path manifest or a workflow that labels pull
requests by surface would need to know which paths each downstream actually takes, how it
records the commit it last took, and which checks it runs. Those are not in this repository.
The table above is a starting point for a manifest, once it has been agreed.

## Keeping the work copy in step

The work copy is a **downstream** of this public repository, not a hand-made copy: it has the
public repository as a git remote named `upstream`, and it takes changes by merging, never by
retyping them. Everything work-specific lives in a few **overlay** paths that this repository
never creates, so a merge is fast and conflict-free:

| In the work copy | Holds |
|---|---|
| `content-packs/internal/` | The real lessons: a copy of `content-packs/iac-applied/` with the same lesson ids, filled in ([CONTENT_PACKS.md](CONTENT_PACKS.md)). "How this works at our company for lesson X" is a pack lesson there with `prerequisites: [<core lesson id>]`, never an edit to the core module |
| `.databricks/bundle/work/variable-overrides.json` | Real workspace names and ids (git-ignored, as here) |
| `.github/workflows/overlay.yml` | The guard below, copied from [`templates/enterprise/overlay.yml`](../templates/enterprise/overlay.yml) |
| `UPSTREAM` | One line: the public commit the work copy was last merged with |
| `README-internal.md` | Anything a colleague needs that cannot be said here |

**Set it up once**, on the work laptop, from a release tag of this repository (each published
build is tagged `v0.N`, N being the page's version, so the work copy pins a build someone has looked at;
`git tag` lists them):

```bash
git clone --branch v0.84 https://github.com/HuyD0/langgraph.git daily-drill && cd daily-drill
git switch -c main
git remote rename origin upstream                 # this repository is "upstream" from here on
git remote add origin <the work repository's address>
git rev-parse HEAD > UPSTREAM                     # the public commit this copy is built on
cp templates/enterprise/overlay.yml .github/workflows/overlay.yml
git add UPSTREAM .github/workflows/overlay.yml
git commit -m "Daily Drill: downstream of the public repository at v0.84"
git push -u origin main
```

Then fill `content-packs/internal/` ([CONTENT_PACKS.md](CONTENT_PACKS.md)) and run the quick
way above. The public test suite runs unchanged in the work copy: the `UPSTREAM` file switches the
few two-copy tests (`tests/test_porting.py`, `tests/test_packs.py`, `tests/test_scrub.py`) to the
work copy's expectations, so a sync pull request there is green when nothing is wrong. `app.yaml` already points `DRILL_CONTENT_PACKS` at that folder, so nothing the public
repository owns is edited at work.

**Bring in a new release** whenever one is tagged here. Do it on a branch and open a pull
request with the label `upstream-sync`: the guard in `overlay.yml` fails any other pull request
that touches a path outside the overlay.

```bash
git fetch upstream --tags
git switch -c upstream-sync-v0.85
git merge --no-ff --no-commit v0.85               # stops before committing, so UPSTREAM goes in too
git rev-parse v0.85 > UPSTREAM
git add UPSTREAM
git commit -m "Merge daily-drill v0.85"
git push -u origin upstream-sync-v0.85            # then a PR labelled upstream-sync
```

`UPSTREAM` is the record: `git diff $(cat UPSTREAM) -- . ':!content-packs/internal'
':!.github' ':!UPSTREAM' ':!README-internal.md'` shows what changed at work against the public
build, and should print nothing.

## Found something while at work

A bug, a wrong fact, better wording: the fix goes to the public repository **first** and flows
down with the next merge. It is never retyped into the public copy from internal text, and never
fixed only at work. Security findings are the same: CodeQL and dependency alerts in the work
repository show up on code it did not write, so they are fixed here and flow down.

1. Write it down as a note with no internal names: what, where, how to see it.
2. In the public clone, make the change, run `scripts/check.sh` (`.\scripts\check.ps1` on Windows; it runs the
   scrub), open a pull request; the owner merges and tags a release.
3. In the work copy, bring in that release as above.

If it must ship at work before that (a broken lesson learners are on today), make the change in
the work copy on a branch named `to-upstream/<topic>` (the `upstream/` prefix is taken by the
remote's branches), label its pull request `upstream-sync` so the guard lets it through, and port
it here the same week. The next merge from upstream then brings the same change back and git
merges it cleanly; if it conflicts, take upstream's version.

## Copilot and two copies

- The public clone lives on the Mac, the work copy on the work laptop, and **never both in one
  editor window** or one Copilot workspace: Copilot takes open files as context and will carry
  internal strings into public edits.
- In the work repository, configure Copilot content exclusion (repository settings, Copilot) for
  `.env`, `.databricks/**` and `content-packs/internal/assets/**`, so keys, workspace ids and
  screenshots never become context.
- `.env` is never committed (git ignores it) and never pasted into a chat, Copilot's or anyone's.
- Copilot reads `AGENTS.md`; its "Two copies" rules say which paths it may edit in each copy.
- **The scrub.** `tests/test_scrub.py` fails on real-looking names in any tracked text file: an
  Azure Databricks workspace address with a real id, a 32-character application id, an email at
  a company, and every word in your denylist, `~/.config/daily-drill/denylist.txt` (one word per
  line: team codes, group and catalog names, repository names, people; `re:` starts a pattern). The
  file lives outside the repository on both machines, so it is never committed; without it the
  test skips and says so. `scripts/check.sh` runs it with the other tests, and the pre-push hook
  (`git config core.hooksPath scripts/hooks`, once per clone) runs it alone before every push. In
  the work copy, `content-packs/internal/` is exempt, since that is where the real names belong.
  In the work repository's Actions, `overlay.yml` runs it with the denylist kept as the
  repository secret `DRILL_DENYLIST`. GitHub secret scanning and push protection are on for this
  public repository too (free for public repositories).

## Taking it down

Stop it with `uv run drill cloud stop --target work`; progress stays in Lakebase. To remove it
entirely, delete the app, the dashboard, the `daily_drill_lakebase` catalog, the Lakebase
project (this deletes everyone's progress), the warehouse and the two schemas, in the workspace
UI or with the Databricks CLI.

More detail: [DATABRICKS_APP.md](DATABRICKS_APP.md).
