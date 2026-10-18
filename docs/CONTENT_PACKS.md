# Adding an Internal IaC Curriculum

Daily Drill can show lessons that live outside its public curriculum: a **content pack**, a
folder of YAML files. The slots for **Infrastructure as Code: Applied Practice** are already in
`content-packs/iac-applied/` (Journey A, Journey B and a capstone, all empty). This guide shows
how to fill them in, check them, preview them, and turn them on in an internal deployment,
without changing the application's code or any file the public repository owns.

## Where things go

The work copy of the repository is a downstream of the public one ([PORTING.md](PORTING.md),
"Keeping the work copy in step"), so real material goes in one **overlay** folder that the public
repository never creates and an upstream merge never touches: `content-packs/internal/`, a copy
of `content-packs/iac-applied/` (its `pack.yaml`, `lessons/` and `assets/`) with the **same lesson
ids**, filled in. The shared slots stay slots in both copies.

| Material | Where | In the public repository? |
|---|---|---|
| The pack's structure (journeys, lesson slots) | `content-packs/iac-applied/` | Yes, as empty slots only, in both copies |
| Templates | `content-packs/templates/` | Yes |
| A complete fictional example | `tests/fixtures/content-packs/example/` | Yes (made-up names only) |
| Real lessons, answer keys, configuration examples | `content-packs/internal/lessons/` in the **work copy** | **Never** |
| Screenshots and diagrams | `content-packs/internal/assets/` in the work copy | **Never** |
| Links to internal docs, repositories, runs | each lesson's `evidence:` in the work copy | **Never** |
| "How this works at our company for lesson X" | a pack lesson in `content-packs/internal/` with `prerequisites: [<core lesson id>]`, so it follows its public twin on the path; **never** an edit to `src/drill/content/modules/` | **Never** |
| Laptop-only previews | `content-packs/private/`, which git ignores. A git-ignored folder never reaches the Databricks App (the deploy honours `.gitignore`), so anything to deploy must be in the tracked `content-packs/internal/` | No |

Three safeguards. `content-packs/PUBLIC` stays in **both** copies and makes the tests fail if any
lesson in the shared packs stops being a slot or an asset appears there; don't delete it at work.
The scrub (`tests/test_scrub.py`, run by `scripts/check.sh` and the pre-push hook) fails on real
names in any tracked file; in the work copy `content-packs/internal/` is exempt, since that is
where they belong. And `app.yaml` already names `content-packs/internal` in `DRILL_CONTENT_PACKS`,
so turning the pack on needs no edit to a file the public repository owns.

## How a pack works

```text
content-packs/iac-applied/
  pack.yaml            id, title, version, where it joins (track: platform), its journeys and their lessons
  lessons/*.yaml       one lesson per file
  assets/              screenshots and diagrams the lessons name
```

Each lesson keeps the four steps learners know: **Learn, Check, Practice, Explain**. Practice is
one exercise (below) in place of the Python editor. Each lesson has a `status`:

- `slot`: a placeholder. Never shown.
- `draft`: being written. Shown only in previews, marked Draft.
- `ready`: shown to learners. It must pass every check and contain no `_TODO` placeholder.

A journey with nothing to show is left off the path, so learners never meet an empty page.

## Fill in a lesson

1. **Copy the template** over the slot, keeping the slot's `id` (the first time, create the
   overlay by copying the whole of `content-packs/iac-applied/` to `content-packs/internal/`):
   `cp content-packs/templates/lesson.example.yaml content-packs/internal/lessons/a1-workflow.yaml`
2. **Write the explanation** (`learn.text`) and the **objective**: plain words, short sentences,
   explain each term the first time. Start with why it matters.
3. **Add configuration or code examples** under `learn.examples`: approved snippets, cut down to
   what the lesson needs, with a one-line caption.
4. **Add a picture** of the investigation under `learn.views` (see below), and any
   **screenshots** under `learn.screenshots` (files go in `assets/`).
5. **Write the Check question** (`check`): one multiple-choice question on the main idea.
6. **Choose an exercise** (`practice`) from `content-packs/templates/exercise.example.yaml` and
   give its correct answer.
7. **Write Explain**: the reasoning, one sentence to compare (`say`), common mistakes, and the
   investigation steps in order.
8. **Link the evidence**: every source the lesson relies on goes under `evidence` with its
   reference, revision and whether it's verified (with the date). `learn.sources` and
   `explain.evidence` name them by id; learners see how far to trust each one.
9. Set `status: draft`, **check** it and **preview** it (below). When it reads well, set `status: ready`.

## Exercise types

| `kind` | What the learner does | What you supply |
|---|---|---|
| `multiple_choice` | Picks the right explanation | `options`, `answer`, `why` |
| `identify_error` | Finds the problem in a snippet | an artifact, `options`, `answer`, `why` |
| `troubleshooting` | Diagnoses an error, then sees the next safe check | a log artifact, `options`, `answer`, `why`, `next_check`, optional `handoff` |
| `review_decision` | Approves, requests changes or escalates | artifacts (often a `diff`), `answer`, `why`, `next_check` |
| `source_tracing` | Finds the layer that set a value | a `trace` artifact, `options`, `answer`, `why` |
| `difference_review` | Reads a before and after | a `diff` artifact, `options`, `answer`, `why` |
| `ordering` | Taps steps into order | `steps` in the right order (the page shuffles them) |
| `relationship_mapping` | Matches each reference to its target | `pairs` |
| `configuration_repair` | Edits a broken config until rules pass | `broken`, `fixed`, `rules` (must contain / must not contain) |
| `reasoning` | Answers in their own words, then compares | `questions` (ask, expected, why), optional `success` |

Artifacts shown above an exercise can be `code`, `config`, `log`, `plan`, `text`, a `diff`
(`before`, `after`), or any view.

## Views: pictures of an investigation

| View | Shows | Good for |
|---|---|---|
| `relationships` | file → reference → file, one row each | how configuration files point at each other |
| `trace` | a field, layer by layer, marking where it was added or changed | following a value from config to plan |
| `walkthrough` | symptom → what you looked at → suspects → root cause → fix → can't verify | a troubleshooting story |
| `plan_review` | each planned change, its action and risk, then the decision | reviewing a plan |
| `tour` | a screenshot with a highlighted box per step, a close-up and Back / Next | finding your way around a tool's pages |

For a `tour`, give each stop's box as percentages of the image (`x`, `y`, `w`, `h`), and the
image's `ratio` (height divided by width) so the close-up keeps its shape.

## From a workbook to a pack

If the material starts as a document (a workbook with numbered sections, steps, screenshots with
numbered callouts, practice questions and an answer table), it maps over like this:

| In the workbook | In the pack |
|---|---|
| A numbered section ("Read your first plan") | a lesson |
| "Follow one request from start to finish" | A1, with an `ordering` exercise and a `relationships` view |
| Its "Step 1, Step 2..." | `explain.steps`, or a `walkthrough` view's `steps` |
| A screenshot with numbered callouts | a `tour` view: the screenshot in `assets/`, one stop per callout |
| "Where did that value come from?" | a `trace` view and a `source_tracing` exercise |
| "Why did the lookup fail?" | a `walkthrough` view and a `troubleshooting` exercise, with `next_check` and `handoff` |
| Practice questions with an expected-answer table | a `reasoning` exercise: each row is a question's `expected` and `why` |
| A success criterion | the reasoning exercise's `success` |
| "What to send to the owner" | the troubleshooting exercise's `handoff` |
| Links and source excerpts | `evidence`, each with its revision and date reviewed |
| A full worked case | the capstone, from `content-packs/templates/case-study.example.yaml` |

## Check, preview, build

```bash
uv run drill content check content-packs/internal          # every problem, by file and field
uv run drill content preview content-packs/internal        # http://127.0.0.1:8790, drafts shown
```

The preview uses a scratch progress file, not yours. To see the fictional example working:
`uv run drill content preview tests/fixtures/content-packs/example`.

A static page with a pack (for a private file share) is `uv run drill build-page --pack
content-packs/internal`. It writes `dist/private/`, which git ignores, with the screenshots
inside the page. Never publish that file anywhere public: everything in a static page can be read
by anyone who opens it.

## Turn it on in an internal deployment

The server loads the folders named in `DRILL_CONTENT_PACKS` (separate several with `:`), and a
folder that isn't there is skipped. `app.yaml` already names `content-packs/internal`, in both
copies, so there is nothing to edit: in the public repository the folder doesn't exist and
nothing loads; in the work copy the pack is tracked, travels with the deploy and loads. Commit
the pack and deploy as usual (`uv run drill cloud deploy --target work`, or
`./scripts/port-to-workspace.sh`).
The pack's lessons are part of the page the server sends, so **everyone who can open the app can
read them**: who can use the app is the access control (`uv run drill cloud share`). Screenshots are
served at `pack-assets/<pack>/<file>` by the same app, and only files a lesson names.

## Update a lesson without losing progress

Progress is saved under each lesson's `id`, so:

- **Change the text, exercise or evidence freely**: the id stays, and so does progress.
- **Never reuse an id** for a different lesson.
- **To rename an id**, put the old one in `aliases: [old_id]`; the page carries progress over.
  (A **core** lesson is renamed the same way, with `old: new` in `ALIASES` in
  `src/drill/content/modules/__init__.py`; the old id stays in `tests/fixtures/lesson_ids.txt`, and a
  pack whose `prerequisites` name the old id still loads.)
- **To retire a lesson**, set it back to `slot` rather than deleting it, so its id stays taken.
- Bump `version` in `pack.yaml` when lessons change; it travels with the evidence.

## What's deferred until real content exists

- No connection to real repositories, plan runs or deployment systems: views and exercises read
  the YAML you write.
- `configuration_repair` checks text rules (must contain, must not contain), not a real parser
  or schema; add a rule for each thing the fix must get right.
- The AI tutor's "Ask about this lesson" works on pack lessons, but its prompts were written for
  the public curriculum; review them once real lessons exist.
