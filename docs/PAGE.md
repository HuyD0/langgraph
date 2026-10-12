# The Daily Drill page

The learning-path page published at https://claude.ai/artifact/G7841w2YuwNwEGjwEWiDMg:
129 lessons in 17 modules (use cases and fit, AI & ML foundations through agents and agent teams, security,
pricing and sizing, reliability, shipping and the Azure Databricks platform), each lesson
going Learn, Check, Build, Explain. The same page is what `drill-server` serves on your Mac ([SERVER.md](SERVER.md)).

The page is one self-contained HTML file. Python exercises run in the browser with
[Skulpt](https://skulpt.org). On claude.ai, hints, reviews and the study list use the
artifact's `sample` and `db` capabilities; served locally they talk to `/api/*` instead.
The switch is `claudeBackend()` / `localBackend()` at the bottom of `page.html`.

## Where things are

Everything is in the package, under `src/drill/content/`:

| File | What it holds |
|---|---|
| `modules/<module>.py` | One file per chapter, lessons in the order they appear: `foundations.py`, `rag.py`, `agents.py`... |
| `modules/__init__.py` | `ORDER`, the order of the chapters, and `LIFECYCLE`, the strip at the top of the page |
| `model.py` | The helpers a lesson is written with: `lesson`, `exercise`, `case`, `question`, `angle`, `stack` |
| `classics.py` | The Learn panel for the 9 classic interview problems. The problems themselves are `drill.problems`, the same bank `drill start` drills |
| `extras.py` | The glossary, and the gotcha cards: each names the lesson whose Explain step shows it as a "Spot the gotcha" challenge, or the Build-step moment a working habit appears |
| `page.html` | The page: layout, styles and all the JavaScript. `/*DATA*/` is replaced with the content at build time |
| `build.py` | Puts it together: `build_data()` is the content as one dict, `render_page()` embeds it |

## The path: a sticker book

Home shows the path as a sticker book, with the six phases always in view:

- **The phase rail** shows the six phases in order, done phases filled, the current one large and
  blue. On Home each phase is a button: tap one to see its page of stickers, and "Back to today"
  returns to the current phase. Above every lesson the rail is a reminder only, so a tap never
  leaves the lesson.
- **One shape per phase**: circle (Frame), rounded square (Design), hexagon (Build and trace),
  diamond (Evaluate), shield (Ship), pentagon (Monitor). Every lesson is a sticker in its phase's
  shape, with its module's icon inside, so one sticker tells you where an idea lives.
- **A phase's page** holds its stickers, one scene per module. Small phases open in full; in a big
  one, the scene with the next lesson is open and the rest fold to a row of small shapes. Today's
  page previews the next phase below it.
- **Each phase page opens with a title card**: the phase's shape large, a "You are here", "Done",
  "Earlier" or "Coming up" label, and what you come out with. The page is printed on the phase's
  own paper, matched to its shape: dots, graph paper, a lattice, ruled lines, hatching, dashes.
- **Lesson pictures**: every lesson has its own small line drawing on its sticker, faded until you
  get there. A new lesson needs one: put a `<symbol id="s-<lesson id>" viewBox="-12 -12 24 24">` in
  the sprite at the top of `page.html`, drawn as strokes on a 24 grid centred on 0, and make it
  look different from its neighbours. Until it has one, its sticker shows the module's icon and
  `tests/test_content.py` fails to remind you.
- **Order**: each sticker carries its place, like 2.11 (phase 2, lesson 11), and a dotted trail
  links stickers in reading order, turning at the end of each row. The first lesson not yet done
  is tagged Next. Opening a lesson further on shows a gentle note naming the next one in order,
  with "Go to the next one" and "Stay here"; it never blocks.
- **Hover card**: hovering a sticker, or reaching it with the keyboard, shows its place, a one-line
  idea from its first Learn paragraph, the function you build, and where you are with it. On a
  phone a long press shows the same card; a tap still opens the lesson.
- **Finishing a lesson** shows its new sticker.

Shape and position carry the phases, not colour: colour stays for passed, failed and the next
step. The shapes and rail icons are `phShape` and `PH_ICON` in `page.html`; there are six, so
`tests/test_content.py` keeps the path at six phases.

## Your own use case

The graded exercises in Use case and fit, and Total cost of ownership, use the HR assistant, so
every test has a known answer. After each one the Build step offers the same thing for your own
idea, ungraded:

- **Write the use case down**: your own card, with the open lines listed as you type.
- **Functional and non-functional requirements**: your requirements, one per line, sorted live.
- **A well-architected review**: "Ask the model to draft the review" sends your card (or the HR
  card, until you write yours) with a review prompt like the one you built.
- **Is it fit for purpose?**: your bars, and later your pilot's results, with the go, fix or
  stop call worked out by the exercise's rule.
- **Total cost of ownership**: a worksheet laid out like the bill of a RAG pipeline on Azure: LLM
  calls (answers and embeddings, pay as you go or provisioned), retrieval (Azure AI Search or
  Databricks Vector Search), Databricks compute (the chunk-and-embed jobs, and serving), storage,
  people and one-off costs. The page ships no prices; each group links to the Azure pricing page
  to take them from.

It is saved in your own progress only (`mine` in the progress document; on claude.ai under
`data/users/<you>`, which nobody else can read) and the tutor snapshot includes it.

## Search

The magnifier in the top bar, or the `/` key, opens search. As you type it finds:

- **Words** from the glossary, each with its meaning and a "Where it's taught" list of the
  lessons that use it.
- **Lessons** whose title, text or function name holds every word typed, title matches first.
  Each shows its phase shape, its number (like 2.11), its module and whether it's done.
- **Your study list** items whose text, note or explanation match; choosing one opens it in
  the Notebook.

With nothing typed it offers the six phases to jump to, the lessons you're in the middle of,
and a few example searches. Enter opens the first lesson; Escape or Close goes back to where
you were.

## The study list

Select any text in a lesson, or a line of your code, to save it to the study list in the
Notebook. Each item shows as one line until you open it, grouped by the lesson it came from in
path order, under three headings:

- **Review now**: items you marked "Got it" whose review has come round. Try to recall it, check
  what you saved, then say whether you remembered. Remembering pushes the next review further
  out (3 days, then 10, 30 and 90); forgetting puts it back on To learn.
- **To learn**: everything still being learned, with its explanation, quiz and follow-ups inside.
- **Got it**: closed by default, each with its next review date.

The search box looks through the text, your notes, the explanations and the lesson names.

**Two copies.** On claude.ai the list lives in the artifact's database; served by `drill-server`
it lives in `.drill/drill.db`. The two cannot reach each other, so they don't sync by themselves.
Both keep items by id with a last-changed time, so they merge safely, as often as you like:

```bash
uv run drill study export study.json     # this Mac's list
uv run drill study import study.json     # merge a list in: new items added, the newer copy of an item wins
```

For the claude.ai side, ask Claude Code to "sync my study lists": it reads the artifact's
`study` collection, imports it here, and writes back anything newer from this Mac. Removing an
item is not remembered, so remove it from both copies. The merge rules are in
`src/drill/server/study.py`.

## Build and publish

```bash
uv run drill build-page           # checks every exercise, then writes dist/daily-drill.html and dist/data.json
uv run pytest tests/test_content.py
```

The build refuses to finish if Big-O notation (`O(n)` and friends) appears in anything the
learner reads: the wording is plain language throughout ("walks through the list once").

To also check the exercises in Skulpt, which supports less Python than CPython:

```bash
cd scripts/skulpt-check && npm install && node check_in_browser_python.js
```

Then ask Claude Code to publish `dist/daily-drill.html` to the URL above. Publishing to the
same URL keeps learners' progress, which lives in the artifact's database, not in the HTML.

## Adding a lesson

Open the module's file in `src/drill/content/modules/` and add a `lesson(MODULE, ...)` call
where it should appear. Copy a neighbour; every field is named. In short:

- `title` and `learn`: the heading and the paragraphs to read (backticks for code,
  `**bold**` for a term).
- `example`: a caption and a few lines showing the idea.
- `check`: a multiple-choice `question(...)`, with `answer` as the index of the right option
  and `why` shown after answering.
- `angle`: the interview angle: the `pattern` name, the plain-language `text`, a sentence
  to `say` out loud, and optionally the `classic` interview problem that uses the same idea.
- `stack`: optional, the same idea in Databricks, LangGraph, LangChain or MLflow.
- `exercise`: the `prompt`, `starter`, `solution` and `cases` (mark one `sample=True`), the
  `guided` scaffold with `___` blanks and the matching `fills`, and the Learn panel
  (`concepts`, `byhand`, `why`, `gotchas`).
- `machine`: optional, for an exercise that sorts rows into groups (the first argument is
  a list of dicts, and the sample case returns one list per group holding exactly those
  rows). `machine(bins=[...], who=[...], label_field=... or label_arg=..., leak_arg=...)`
  draws the Build step's "Watch the rows" card: the example's rows travel through the
  function into named bins, with a replay slider, a table per bin and, with `leak_arg`, a
  check that no value of that field lands in two bins. `split_by_key` and `validate_rows`
  use it; `tests/test_content.py` checks each machine fits its example.

Every exercise whose example takes a list of rows also shows those rows as a table, and,
after a run, your result for the example beside the expected rows when it returns rows.

Then `uv run drill build-page`. It runs the solution and the filled-in scaffold against the
cases, so a lesson that cannot be solved never reaches the page. A new chapter is a new
file with its own `MODULE = module(...)`, plus its id in `ORDER` and in one `LIFECYCLE` stage.
A hyphen in the id becomes an underscore in the file name: `agent-teams` lives in
`agent_teams.py`.

Keep the wording plain and the page quiet: no Big-O, and visuals only where they replace
text.
