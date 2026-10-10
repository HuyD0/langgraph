# Daily Drill page

The source for the **Daily Drill** learning-path page published at
https://claude.ai/artifact/G7841w2YuwNwEGjwEWiDMg — 67 lessons in 14 modules
(AI & ML foundations through agents, security, reliability, shipping and the Azure
Databricks platform), each lesson going Learn → Check → Build → Interview.

The page is one self-contained HTML file. Python exercises run in the browser with
[Skulpt](https://skulpt.org); hints, reviews and the study list use the artifact's
`sample` and `db` capabilities.

## Build

```bash
uv run python web/daily-drill/build.py     # writes web/daily-drill/dist/daily-drill.html
uv run pytest tests/test_daily_drill.py    # every exercise and scaffold against its tests
```

The build refuses to finish if Big-O notation (`O(n)` and friends) appears in anything
the learner reads; the learner prefers plain language ("walks through the list once").

To also check the exercises in Skulpt, which supports less than CPython:

```bash
cd web/daily-drill/tools && npm install && node check_in_browser_python.js
```

## Publish

Ask Claude Code to publish `web/daily-drill/dist/daily-drill.html` to the URL above.
Publishing to the same URL keeps learners' progress, which lives in the artifact's
database, not in the HTML.

## Run it from your own machine

The same page can be served by the local tutor server in `src/drill/server`, which
answers with Ollama (free, on your Mac) and keeps progress in a SQLite file:

```bash
uv run drill-server        # http://localhost:8787, and http://<your-mac>.local:8787 on your Wi-Fi
```

On claude.ai the page talks to the artifact's `sample` and `db`; served locally it talks
to `/api/*` instead. The switch is `claudeBackend()` / `localBackend()` at the bottom of
`app.html`; both hand the rest of the page the same three objects. The build also writes
`dist/data.json`, which the server and its MCP tools read, so the page and the tools
always agree on the content. See the root README for the phone and Claude Code setup.

## Where things are

| File | What it holds |
|---|---|
| `app.html` | The page: layout, styles and all the JavaScript. `/*DATA*/` is replaced with the content at build time. |
| `build.py` | Merges everything, decides module order, writes `dist/`. |
| `content/base_content.json` | Content carried over from the earlier version of the page: the 9 classic interview problems, the first 9 AI exercises, the 8 "My money & health" problems (made-up data from `drill.mine.export`), the 9 Azure Databricks Terraform exercises, and the glossary, gotchas and habits lists. |
| `content/new_problems.py` … `new_problems7.py` | The exercises added since, in the order they were written: foundations/RAG/agents/LLMOps, experiment design, agents on Databricks, production patterns, security, then reliability/agents/data/evals/craft, then the MLflow Prompt Registry. Each file has a `check()` that runs the solution and the filled-in scaffold against the test cases. |
| `content/curriculum.py` … `curriculum6.py` | Lessons: the Learn text, Check question, Interview angle and the "In your stack" snippet for each exercise, plus the module list (`curriculum3.MODULES` is the base order; `build.py` inserts later modules). |
| `content/plain.py` | Plain-language rewrites of earlier interview-angle text, applied at build time. |

### Adding a lesson

1. Add an exercise with `add(...)` in a `new_problems*.py` file: `prompt`, `solution`,
   `cases` (mark the one shown as the example), a `guided` scaffold with `___` blanks and
   the matching `fills`, and `learn` (concepts, worked example, gotchas).
2. Add the lesson with `lesson(...)` in a `curriculum*.py` file, and optionally a `STACK`
   snippet, which is the "In your stack" box.
3. Put its id in a module's lesson list, rebuild, run the tests, publish.

Keep the wording plain and the page quiet: no Big-O, and add visuals only where they
replace text.
