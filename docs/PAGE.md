# The Daily Drill page

The learning-path page published at https://claude.ai/artifact/G7841w2YuwNwEGjwEWiDMg:
130 lessons in 17 modules (use cases and fit, AI & ML foundations through agents and agent teams, security,
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

- **Phase tabs and the room.** On Home the six phases are tabs on a violet strip (the path), and
  the phase you picked opens below as a room: one piece, with the chosen tab cut from the room's
  own paper and no gap between them. The room is rimmed in blue when it is where you are and in
  violet for any other phase, and its title shape is the only thing that glows. A small blue dot
  marks your phase on the strip, and a thin violet line along the top fills as phases are done.
  Tap a tab (or use the arrow keys, Home and End) to see its page of stickers; "Back to today"
  returns to the current phase. It is a real tab list (`role="tablist"`, `tab`, `tabpanel`).
  The look lives in `.phasebox`, `.rail.phtabs` and `.book.room` in `page.html`; the colours are
  the `--path*` tokens. Above every lesson the small rail is a reminder only, so a tap never
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

Shape and position carry the phases, not colour: colour stays for passed, failed, the next
step and the path (violet, only on the phase tabs). The shapes and rail icons are `phShape` and `PH_ICON` in `page.html`; there are six, so
`tests/test_content.py` keeps the path at six phases.

## Your own use case

The graded exercises in Use case and fit, and Total cost of ownership, use the HR assistant, so
every test has a known answer. After each one the Build step offers the same thing for your own
idea, ungraded:

- **Is this a good AI use case?**: your problem, the use case in one line ("Help [who] [do
  what] so [a number] improves"), the three gates, automate or augment, and value and doable,
  which place your idea on a small 2 by 2 map. "Challenge my use case" asks the model to argue
  against it.
- **Write the use case down**: your own card (shaped like the AI Canvas: the decision, the
  action, feedback), with the open lines listed as you type.
- **Functional and non-functional requirements**: your requirements, one per line, sorted live.
- **A well-architected review**: "Ask the model to draft the review" sends your card (or the HR
  card, until you write yours) with a review prompt like the one you built.
- **Is it fit for purpose?**: your bars, and later your pilot's results, with the go, fix or
  stop call worked out by the exercise's rule.
- **Turn your vetting into a skill** (the last lesson of Frame): the repository's Claude skill,
  `.claude/skills/vet-ai-use-case` (a `SKILL.md`, reference files and `scripts/tco.py`), in an
  editor checked against the skill rules as you type. "Run my skill on my use case" sends your
  version, with your card, requirements, bars and the cost table worked out from your worksheet,
  to the model. In Claude Code the skill runs as `/vet-ai-use-case`.
- **Total cost of ownership**: a worksheet laid out like the bill of a RAG pipeline on Azure: LLM
  calls (answers and embeddings, pay as you go or provisioned), retrieval (Azure AI Search or
  Databricks Vector Search), Databricks compute (the chunk-and-embed jobs, and serving), storage,
  people and one-off costs. The page ships no prices; each group links to the Azure pricing page
  to take them from.

**Improving the review and the challenge.** Their prompts live in `src/drill/content/review.py`
(versioned: `review-v2`, `challenge-v1`), which the page, the server and the eval all read.

- **Traces**: every draft is traced in MLflow with its feature, prompt version and a request id.
  The server checks every review by code (`drill.review_checks`: a missing pillar, a verdict, no
  Unknowns for blank lines) and attaches the results to the trace.
- **Your feedback**: under each draft, "Was this useful?" and a reason ("Made something up",
  "Missed a risk", "Caught a risk I missed"...). Served locally it goes to `/api/feedback` and onto
  the draft's trace as human feedback; everywhere it is also kept in your progress (`mine.feedback`).
- **What you did next**: changing your rating, gates or card after a draft is logged as a signal
  on that draft (`changed_rating_after`, `edited_card_after`).
- **The eval**: `uv run drill review eval` asks the model to review cards with planted gaps (no
  owner, no test data, no feedback loop, vague success, nobody checking, two gaps) and scores
  every planted gap flagged, every pillar named, no verdict, and a high risk where nobody checks.
  It fails if a must-pass case fails, and logs an MLflow evaluation run. `--judge` adds a
  groundedness judge; it must quote the review word for word and code drops anything else, but
  it was tuned on these same cases, so check it against your own labels before trusting it.
  Run it before changing a prompt, and bump the version.
- **Labels and the judge**: `uv run drill review label` shows recent reviews from MLflow, one at a
  time, and asks whether each invented a fact; your answer goes on the trace as HUMAN feedback
  (`grounded`). `uv run drill review calibrate` runs the judge on everything you labelled, logs
  its verdicts (`grounded_judge`), and reports agreement and Cohen's kappa as an MLflow run.
  Label about ten a week; lean on the judge only once kappa stays above about 0.6 on 20 or more.
- **The pilot's outcome**: when you enter pilot results in "Is it fit for purpose?", the go, fix
  or stop call is attached to the review and challenge drafts that vetted that idea
  (`pilot_outcome`), so you can later see whether the vetting predicted the pilot.
- **The prompt registry**: `uv run drill review register` puts both prompts in MLflow's prompt
  registry (`use_case_review`, `use_case_challenge`; on Databricks `<DRILL_PROMPT_SCHEMA>.use_case_review`
  and so on, since the registry there is Unity Catalog), a new version only when the text changed,
  with the `production` alias on the current one. See [DATABRICKS_APP.md](DATABRICKS_APP.md) for
  how versions, traces, evals and the review cases link to them.

It is saved in your own progress only (`mine` in the progress document; on claude.ai under
`data/users/<you>`, which nobody else can read) and the tutor snapshot includes it.

## Search

The magnifier in the top bar, or the `/` key, opens search. As you type it finds:

- **Words** from the glossary, each with its meaning and a "Where it's taught" list of the
  lessons that use it.
- **Lessons** whose title, text or function name holds every word typed, title matches first.
  Each shows its phase shape, its number (like 2.11), its module and whether it's done.
- **Your study list** items whose text, note or explanation match; choosing one opens it in
  the study list's tray.

With nothing typed it offers the six phases to jump to, the lessons you're in the middle of,
and a few example searches. Enter opens the first lesson; Escape or Close goes back to where
you were.

## The study list

Select any text in a lesson, or a line of your code, to save it to the study list. It lives in
a **tray**: on the path it waits at the bottom, one line tall, saying what's due; on any other
page a chip in the header opens it (glowing, with a count, when something is due). Tap the tray
to slide it up. Three tabs:

- **To review**: items you marked "Got it" whose review has come round.
- **Still learning**: everything you saved and haven't marked "Got it" yet.
- **Got it**: each waiting for its next review.

Each row is one line: the item, the shape of the phase it came from, and four **seals** for the
reviews after 3, 10, 30 and 90 days (filled once passed, ringed for the one it's waiting for).
Opening an item shows it with its review ladder and **one** main step, which changes as you go:
**Explain it to me**, then **Quiz me**, then **Got it**. Notes, follow-up questions and a new
quiz are small links; removing it is under "⋯".

**Reviewing** happens in the focus field. **Start review** opens it, with the page's "space"
effect: one card at a time. Try to recall it first, then **Show what I saved**, then say whether
you remembered. Remembering stamps a seal (and a spark) and pushes the next review further out
(3, 10, 30, 90 days); forgetting puts it back on Learning. It ends with how many you sealed. With
Motion off the effects don't play; everything else is the same.

The search button in the tray looks through the text, your notes, the explanations and the lesson names.

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

## Ask about this lesson

When an AI tutor is available, Learn, Check (once answered) and Explain end with a short
conversation about the lesson. Its suggested questions are built from that lesson, by
`askChips()` in `page.html`, so they change from lesson to lesson:

| Step | Questions |
|---|---|
| Learn | how the lesson's two key terms differ ("How is “training” different from “test”?"); when the rule stops working (LLM and RAG apps, data that changes, little data); how you'd spot it going wrong; Quiz me |
| Check | "Why not …?" for each wrong option; a harder question like it |
| Explain | "Is my sentence right?" (once you've written one); Quiz me; how to say the pattern in an interview; why the lesson's gotcha matters |

"Apply it to my situation…" puts "In my situation, " in the box for the learner to finish, so the
tutor answers for their real setup rather than an invented one. The choice follows what learners
ask most: the questions saved to the study list ("does this still hold for an LLM app?") and
common questions online (how is X different from Y, how do I tell it's gone wrong, why is this
answer wrong). Quiz me is retrieval practice, the study technique with the strongest evidence.

Each question carries its own instruction to the tutor. None of them asks about the exercise,
and two guards still stop any answer from writing the exercise's code.

## Motion

(The wider design system, its tokens and how to change them: [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).)

Short effects mark real moments: finishing something, getting something right, fixing a bug.
They decorate what already happened and never change a lesson's order, wording or difficulty.

| # | Effect | Plays when | Length | Where in `page.html` |
|---|---|---|---|---|
| 1 | Space opens | You finish a lesson | about 1.5 s | `goNext` → `fxScreen("space")` |
| 2 | Merge | You finish a whole phase (six times on the path) | about 1.7 s | `goNext` → `fxScreen("merge")` |
| 3 | Spark | Every test passes on your first run, with no hints, the first time you solve it | under 1 s | `runTests` → `fxScreen("spark")` |
| 4 | Step turn | You move between Learn, Check, Build and Explain | 0.4 s | `setStep` → `fxMove` + `fxScreen("turn")` |
| 5 | Curtain | Your first keystroke in an exercise | 0.6 s | editor input → `fxScreen("curtain", …, cover)` |
| 6 | Heal | Tests pass after a run that failed | about 1 s | `runTests` → `fxOn(result, "heal")` |
| 7 | Smoke | You spot a gotcha | about 1 s | `answerGotcha` → `fxScreen("smoke")` |
| 8 | Charge | Your first practice of the day lights today's dot; day 7 of a streak bursts | 0.5 s | `renderTop` (`.week i.lit`, `.burst`) |
| 9 | Grade | Every few lessons the done screen promotes you (Grade 4, 3 at 10, 2 at 25, 1 at 50, Special at 90) | 1.2 s | `showDone` (`.promo`), `GRADES` |
| 10 | Seal | A right answer in Check | 0.5 s | the Check click → `fxOn(option, "seal")` |
| 11 | Energy flow | A row travels into the machine's function box | with each row | `machineRender` (`.mtok.fly`) |
| 12 | Unveil | A hint opens | about 1 s | `hint` → `fxOn(note, "unveil")` |
| 13 | Room | You change phase on Home: the tab slides over, the page's words follow it, rings ripple from the title shape and a red-black spark runs along the top edge. Once per visit, the path's line first fills to where you are | 0.3 s (about 1 s the first time) | phase tab click → `phaseFx` → `fxMove` + `fxOn(book, "room", …, shape)` |

Grades are worked out from lessons done, so nothing new is saved and they can't disagree with progress.

**How it's built.** Timings (`--dur-*`), curves (`--ease-*`) and effect colours (`--fx-*`) are
tokens in `tokens.css`, set for every look. The looks are the rules between `/* fx: start */`
and `/* fx: end */` in `page.html`. Every effect is played by one of three functions:

- `fxScreen(name, html, at, cover)`: over the screen, centred on the element `at` (or, with
  `cover`, only over the part of `at` you can see). One at a time: a new one replaces the last.
- `fxOn(el, name, html, at)`: inside one element, clipped to its box; with `at`, centred on that
  element (`--x`, `--y` in the effect's own box).
- `fxMove(el, frames)`: the element itself moves, with the Web Animations API, and is left as it was.

**The promises,** checked by `tests/test_content.py`:

- An effect never takes a tap (it ignores the pointer) and never blocks the next step: the
  page has already moved on underneath it.
- It removes itself when its root's `fx-end` animation ends, or after 4 seconds if that never
  comes (a hidden tab, say). Nothing is left behind: no elements, timers or listeners.
- Nothing loops or blurs, and moving parts use transform and opacity, which phones draw cheaply.
- Nothing plays when the phone asks for reduced motion, when **Motion** is Off in the Notebook
  (which also stills the glow on the next step), or when the tab is hidden.
- An error inside an effect is caught, so it can't break the step it decorates.

**Adding an effect:** put its markup in `FX`, its rules (`.fx-<name>`, keyframes named `fx-…`)
in the fx block with a `--hold` for how long it stays, and call `fxScreen` or `fxOn` at the
moment. Add a row to the table above. To look at one frame by frame, pause it partway with
`document.getAnimations()` in the browser console.

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
- `checked` and `sources`: the day (`'2026-10-12'`) you checked the lesson's facts, and the
  pages you checked them against (`source(title, url)`). Required for lessons about products that
  change often (the Databricks modules); welcome on any lesson. See "Keeping content current".
- `exercise`: the `prompt`, `starter`, `solution` and `cases` (mark one `sample=True`), the
  `guided` scaffold with `___` blanks and the matching `fills`, and the Learn panel
  (`concepts`, `byhand`, `why`, `gotchas`).
- `machine`: optional, for an exercise that sorts rows into groups (the first argument is
  a list of dicts, and the sample case returns one list per group holding exactly those
  rows). `machine(bins=[...], who=[...], label_field=... or label_arg=..., leak_arg=...)`
  draws the Build step's "Watch the rows" card: the example's rows travel through the
  function into named bins (four bins make a 2 by 2 map), with a replay slider, a table per bin and, with `leak_arg`, a
  check that no value of that field lands in two bins. `split_by_key` and `validate_rows`
  use it; `tests/test_content.py` checks each machine fits its example.
- `sort`: optional, for a lesson whose real skill is judgement, not code.
  `sort_task(intro=..., bins=[(id, label, who), ...], items=[{"name", "say", "bin", "why"}, ...])`
  makes the Build step a sorting board: one idea at a time, placed by tapping or dragging
  onto a 2 by 2 map (the first four bins, in map order) or a tray above it (a fifth bin).
  Every move shows the item's `why`; a wrong move keeps the card, and the score is how many
  were right first time. "Place one for me" is the hint. The Python exercise stays, behind
  "Rather write it in Python?", and the page remembers which one the learner chose.
  Lesson 1.1 uses it; `tests/test_content.py` checks its answers match the Python solution's.

Every exercise whose example takes a list of rows also shows those rows as a table, and,
after a run, your result for the example beside the expected rows when it returns rows.

Then `uv run drill build-page`. It runs the solution and the filled-in scaffold against the
cases, so a lesson that cannot be solved never reaches the page. A new chapter is a new
file with its own `MODULE = module(...)`, plus its id in `ORDER` and in one `LIFECYCLE` stage.
A hyphen in the id becomes an underscore in the file name: `agent-teams` lives in
`agent_teams.py`.

Keep the wording plain and the page quiet: no Big-O, and visuals only where they replace
text.

## Keeping content current

Databricks, Azure, MLflow and LangGraph rename and move things often (in 2026 alone: Asset
Bundles became Declarative Automation Bundles, Genie spaces became Genie Agents, Vector Search
became Databricks AI Search). So a lesson records **when** its facts were last checked and
**against what**:

```python
lesson(MODULE, 'masked_columns',
    title='ABAC: policies that follow tags',
    checked='2026-10-12',
    sources=[source('ABAC policies', 'https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies')],
    ...
```

The page shows "Checked against the docs on 12 Oct 2026" under Learn, with the sources one tap
away. Lessons with no date of their own show "Content as of 12 Oct 2026", the day dates were
first tracked (`CONTENT_DATE` in `src/drill/content/freshness.py`). After 180 days either note
turns amber and says names and steps may have changed.

**To find what needs a look:**

```bash
uv run drill content stale          # lessons checked over 180 days ago, with their sources
uv run drill content stale --all    # also the fresh ones
```

**To update a lesson:** open each source, compare it with the lesson's Learn text, stack box,
gotchas and exercise wording, fix what moved (keep the old name once, "formerly ..."), then set
`checked` to today and add any new source. Run `uv run drill build-page` and `uv run pytest`.
Only change the date when you actually checked: a date says "true as of this day".

**To add new content:** a new lesson in an existing module, or a new module (see "Adding a
lesson"), dated and sourced like the above. Private or company-specific material goes in a
content pack instead (`docs/CONTENT_PACKS.md` once that lands), which has its own dated evidence.

