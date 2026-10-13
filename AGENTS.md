# Working on Daily Drill (for coding agents)

Read this first. It is the short version of how the project fits together, how to check a
change, and the house rules. Claude Code, Codex, Cursor, Copilot and Gemini all read this file;
`CLAUDE.md` just points here.

## What this is

Daily Drill is a learning path for AI engineering on Databricks: 130+ short lessons, each going
**Learn → Check → Build → Explain**. The learner is **new to coding**. Everything they see uses
plain words and no maths notation (no Big-O).

## How it fits together

```
src/drill/content/modules/*.py  ──build.py──▶  one page: dist/daily-drill.html
  (lessons, written with model.py)               (page.html + tokens.css + the content as JSON)
                                                     │
            ┌────────────────────────────────────────┼─────────────────────────────┐
            ▼                                        ▼                             ▼
   claude.ai artifact                    drill-server (FastAPI, src/drill/server)   Databricks App
   (sample + db capabilities)            /api/*, MCP tools, the AI tutor, SQLite   (same server, Lakebase,
                                         or Postgres                                databricks.yml + app.yaml)
```

| Area | Start here | Doc |
|---|---|---|
| Lesson content | `src/drill/content/modules/`, helpers in `model.py`, order in `modules/__init__.py` | [docs/PAGE.md](docs/PAGE.md), [docs/CURRICULUM.md](docs/CURRICULUM.md) |
| The page (front end) | `src/drill/content/page.html` (one file), `tokens.css` | [docs/FRONTEND.md](docs/FRONTEND.md), [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md), [docs/screens/](docs/screens/README.md) (every screen, with what draws it) |
| Local server, API, MCP, tutor | `src/drill/server/` | [docs/SERVER.md](docs/SERVER.md) |
| Databricks App and porting to work | `databricks.yml`, `app.yaml`, `src/drill/cloud*.py` | [docs/DATABRICKS_APP.md](docs/DATABRICKS_APP.md), [docs/PORTING.md](docs/PORTING.md) |
| MLflow names, traces, evals | `src/drill/mlflow_names.py`, `trace_scoring.py`, `review_eval.py` | [docs/DATABRICKS_APP.md](docs/DATABRICKS_APP.md) |
| The claude.ai tutor project | `src/drill/tutor.py`, `docs/tutor/` | [docs/tutor/README.md](docs/tutor/README.md) |

## Commands

```bash
uv sync                                  # install
scripts/check.sh                         # build the page + run the fast tests: run before every commit
uv run drill build-page                  # page only -> dist/daily-drill.html
uv run pytest -q -m "not slow"           # fast tests (the full suite also runs notebooks)
uv run drill tutor map                   # regenerate docs/tutor/CURRICULUM_MAP.md after content changes
uv run python scripts/contrast.py        # colour contrast in every look, after colour changes
node scripts/screenshots.mjs URL         # retake docs/screens/ from a running server (Chrome, no installs)
```

Preview the page (the raw file in `dist/` has no viewport tag, so use the server):

```bash
DRILL_PORT=8788 DRILL_DATABASE_URL=sqlite:///.drill/preview.db uv run drill-server
```

The server **caches the page when it starts**: restart it after every `build-page`.

## Done means

1. `scripts/check.sh` passes.
2. You looked at the change in the preview at **375×812 (phone) and 1366×860 (desktop)**, in
   **Dusk and Light**, with Motion on and off if anything moves. No sideways scroll.
3. Docs that describe what you changed are updated (the table above says which). If the change
   is visible, retake the screen gallery (`node scripts/screenshots.mjs`, see
   [docs/screens/README.md](docs/screens/README.md)) so the pictures stay true.
4. Content changes: `uv run drill tutor map` was run.

## House rules

**For the learner**
- Plain words, explained on first use; the real industry term, not a made-up one.
- **One plain question per screen** for judgement tasks. Help is **a clue first, then the answer**.
- A game layer or new UI keeps the lesson's own order, wording and scaffold, and never makes it
  harder.

**For the design** (details in [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md))
- Every colour is a token in `tokens.css`; colour means one thing (blue = what's next,
  violet = the AI path, teal = the platform track, green/red/amber = pass/fail/hint).
- One primary button per screen; tap targets at least 44px; works with Motion off.
- Shape carries the phases (one sticker shape per phase; the octagon for the track).

**For the repo**
- Never `git add -A` or `git add .`: the owner keeps untracked folders (like `design-review/`)
  that must not be committed. Add files by path.
- The repo is **public**. Real work names, workspace URLs and ids go only in the git-ignored
  `.databricks/bundle/<target>/variable-overrides.json`.
- Keep franchise or character names out of code, commits and PRs (the Dusk look has a neutral name).
- Don't merge PRs; the owner merges. Stack a PR on another only when it needs that work, and say so.
- Databricks: never choose a CLI profile yourself; ask. Running cloud commands costs money.

## Gotchas

- This machine's shell may set `MLFLOW_EXPERIMENT_NAME`; run Databricks/MLflow commands with
  `env -u MLFLOW_EXPERIMENT_NAME -u MLFLOW_EXPERIMENT_ID ...`.
- Unity Catalog trace outputs come back as JSON strings; UC datasets reject MLflow tags.
- A lesson's sticker picture is a sprite symbol `s-<lesson id>` in `page.html` (a test checks).
- Lesson text lives in Python strings: escape apostrophes in single-quoted strings.
- `dist/` is git-ignored; the page is built, never committed.
- Other sessions publish the claude.ai artifact too: compare the live page with your build
  before publishing, so you don't undo someone else's work.
