# Working on Daily Drill (for coding agents)

Read this first. It is the short version of how the project fits together, how to check a
change, and the house rules. Claude Code, Codex, Cursor, Copilot and Gemini all read this file;
`CLAUDE.md` just points here.

## What this is

Daily Drill is a learning path for AI engineering on Databricks: about 190 short lessons, each going
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

CI (`.github/workflows/`) runs on every pull request: `tests.yml` runs the **full** suite
(`uv run pytest -q`, including the slow notebook tests that `scripts/check.sh` skips) with no cloud
credentials, and checks every `notebooks/m*.ipynb` still has its unsolved exercises; `codeql.yml`
scans the Python and the JavaScript. GitHub's secret scanning and push protection are on.

## Done means

1. `scripts/check.sh` passes.
2. You looked at the change in the preview at **375×812 (phone) and 1366×860 (desktop)**, in
   **Dusk and Light**. No sideways scroll. In Dusk, new
   boxes should look like the rest (glass, depth, a glow on what's current): if one looks flat, it
   isn't using the surface tokens.
   Mockups load `tokens.css` and the page's styles too, never hand-copied colours.
3. Docs that describe what you changed are updated (the table above says which). If the change
   is visible, retake the screen gallery (`node scripts/screenshots.mjs`, see
   [docs/screens/README.md](docs/screens/README.md)) so the pictures stay true.
4. Content changes: `uv run drill tutor map` was run.
5. Front-end changes: the beginner course [docs/course/inside-page-html.html](docs/course/inside-page-html.html)
   still tells the truth. It shows real lines from `page.html`, `tokens.css` and `build.py`;
   `tests/test_course.py` fails when one of them disappears and names the lesson to update. If
   you change a pattern it teaches (how screens render, events, saving, tokens, the build),
   update that lesson's snippet and its `anchors` entry, then republish it to its artifact
   (https://claude.ai/artifact/TYnPBikbTkiCJoGLdkQ9Ws; read the live one first).
6. Publishing the page: after `main` is published to the claude.ai artifact as version N, tag the
   commit `v0.N` (`git tag -a v0.N -m "page version N" && git push origin v0.N`). The work copy
   merges tags, never `main` ([docs/PORTING.md](docs/PORTING.md)).

## House rules

**For the learner**
- Plain words, explained on first use; the real industry term, not a made-up one.
- **One plain question per screen** for judgement tasks. Help is **a clue first, then the answer**.
- A game layer or new UI keeps the lesson's own order, wording and scaffold, and never makes it
  harder.

**For the design** (details in [docs/DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md))
- Every colour is a token in `tokens.css`; colour means one thing (blue = what's next,
  violet = the AI path, teal = the platform track, green/red/amber = pass/fail/hint).
- One primary button per screen; tap targets at least 44px. Motion plays for everyone (no Motion
  switch, no reduced-motion fallback): the owner's choice, see docs/DESIGN_SYSTEM.md rule 6.
- Shape carries the phases (one sticker shape per phase; the octagon for the track).

**For the repo**
- Never `git add -A` or `git add .`: the owner keeps untracked folders (like `design-review/`)
  that must not be committed. Add files by path.
- The repo is **public**. Real work names, workspace URLs and ids go only in the git-ignored
  `.databricks/bundle/<target>/variable-overrides.json`.
- Keep franchise or character names out of code, commits and PRs (the Dusk look has a neutral name).
- Don't merge PRs; the owner merges. Stack a PR on another only when it needs that work, and say so.
- Databricks: never choose a CLI profile yourself; ask. Running cloud commands costs money.

**Two copies** (the public repository and the work copy; how they relate is in
[docs/PORTING.md](docs/PORTING.md), "Keeping the work copy in step")
- Which copy you are in: `content-packs/PUBLIC` is in both. An `UPSTREAM` file at the root
  means the work copy, a downstream of the public repository that is merged from it, never
  retyped.
- In the work copy edit only `content-packs/internal/`, `.databricks/` and `.github/`. Never
  `src/`, `docs/` or `app.yaml` there: a fix lands in the public repository first and flows
  down with the next merge. "How this works at our company for lesson X" is a pack lesson in
  `content-packs/internal/` with `prerequisites: [<core lesson id>]`, never an edit to the
  core module.
- Never paste text from the work copy into the public one without the scrub:
  `tests/test_scrub.py`, run by `scripts/check.sh` and the pre-push hook
  (`git config core.hooksPath scripts/hooks`). Its denylist lives outside the repository, in
  `~/.config/daily-drill/denylist.txt`.
- **Changes that port well** (details in [docs/PORTING.md](docs/PORTING.md), "Writing changes that
  port well"). A downstream copy may merge a whole release, pick single commits or adapt them, so:
  - One topic per PR and per commit; no unrelated refactors, renames or reformatting mixed in.
  - A behaviour change comes with a test; generated files are regenerated, never hand-edited.
  - Lesson ids are the contract: never reuse or remove one; a pack lesson names its core
    lesson by id in `prerequisites`, and learners' progress is saved under ids.
  - The PR description names the areas touched (the table above) and has a **Compatibility**
    line when it changes something others rely on: a lesson id, an `/api/*` route or MCP tool, a
    `drill` command or flag, an `app.yaml` or `databricks.yml` variable. Say what breaks and
    how to move over, or "none".
  - Nothing about any downstream goes into public files: no names, paths, branches or code.

## Gotchas

- This machine's shell may set `MLFLOW_EXPERIMENT_NAME`; run Databricks/MLflow commands with
  `env -u MLFLOW_EXPERIMENT_NAME -u MLFLOW_EXPERIMENT_ID ...`.
- Unity Catalog trace outputs come back as JSON strings; UC datasets reject MLflow tags.
- A lesson's sticker picture is a sprite symbol `s-<lesson id>` in `page.html` (a test checks).
- Lesson text lives in Python strings: escape apostrophes in single-quoted strings.
- `dist/` is git-ignored; the page is built, never committed.
- Some sections of `page.html` live in `src/drill/content/page/` and come back in at their
  `/*INCLUDE page/<file>*/` line. Search both places, read the page through `build.page_source()`,
  and when moving a section, check the build's fingerprint is unchanged ([docs/FRONTEND.md](docs/FRONTEND.md), "Parts").
- Other sessions publish the claude.ai artifact too: compare the live page with your build
  before publishing, so you don't undo someone else's work.
