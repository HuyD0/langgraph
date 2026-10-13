# The front end: how the page is built, and how to change it safely

The whole front end is one file, `src/drill/content/page.html`: styles, markup and JavaScript,
with no framework and no build tools beyond `uv run drill build-page`. That keeps it publishable
as a single claude.ai artifact and servable by `drill-server` unchanged. This page explains how
it is organised so you can find things, change them and leave them as tidy as you found them.

Read with: [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) (tokens, rules, looks), [PAGE.md](PAGE.md)
(what each feature does, for the learner) and [SERVER.md](SERVER.md) (the `/api/*` it talks to).

## How the page is made

```
modules/*.py ──build_data()──▶ JSON ─┐
tokens.css ──────────────────────────┼─▶ page.html ──render_page()──▶ dist/daily-drill.html
page.html (template) ────────────────┘    /*DATA*/  and  /*TOKENS*/  are replaced
```

- `build.py` turns every lesson into plain data and inlines it at `/*DATA*/`; `tokens.css` goes
  in at `/*TOKENS*/`. Nothing else is generated.
- The page reads its content from that data (`D`, then `LESSONS`, `MOD`, `ORDER`, `TRACKS` ...).
  **Never hard-code lesson text in `page.html`**: put it in the module file, and add a field to
  `build_data()` if the page needs something new.
- The same file runs in two places. `claudeBackend()` (claude.ai: the `sample` and `db`
  capabilities) and `localBackend()` (`drill-server`: `/api/*`) give it one interface, chosen at
  boot. A feature that saves or asks a model goes through that interface, never `fetch` directly.

## The four layers, top to bottom

| Layer | Where | Rule |
|---|---|---|
| Tokens | `tokens.css` | Every colour, font and timing. Change values here, not in rules |
| Components | `<style>` in `page.html` | Use `var(--token)` only; a test checks every name exists |
| Markup skeleton | the `<main>` views: `home`, `lesson`, `done`, `search`, plus the drawer, tray and toasts | Mostly empty containers that JavaScript fills |
| Behaviour | the big `<script>` | Sections marked `// ---------- name ----------` (map below) |

## How the script works

It's deliberately simple, and every feature follows the same three steps:

1. **State is plain objects.** `progress` is everything saved (lessons, solved, days), with
   `lp(id)` for one lesson's record. Save with `saveProgress()`; it syncs through the backend.
   `cur` is what's open now (`{ kind, id, p, step }`). Short-lived state for one feature lives in
   one small object next to its code: `SO` (sorting board), `CLZ` (Explain gaps), `M` (the
   machine), `rv` (review).
2. **Rendering is functions that return HTML strings**, set with `innerHTML`: `renderHome()`,
   `learnPane()`, `checkPane()`, `anglePane()`, `renderFoot()`, `renderPocket()`. After changing
   state, call the render function for the part that changed. Wrap anything from content or
   the user in `esc()` (plain text) or `md()` (lesson text with **bold** and `code`); never put
   raw strings into HTML.
3. **Events are delegated.** One `document` click handler, in the `events` section, routes on
   `data-*` attributes: `data-open="<lesson id>"`, `data-step`, `data-opt`, `data-clz` and so on.
   To add a button, render it with a new `data-` attribute and add one line to that handler.
   Feature-local handlers (`#sortBox`, `#pkTabs`, the editor) follow the same pattern.

Small helpers used everywhere: `$(id)` is `getElementById`; `ic(name)` draws an icon from the
sprite (`<symbol id="i-name">`); `fxScreen` / `fxOn` / `fxMove` run effects through the motion
engine, which respects Motion off and reduced motion.

## Map of the script

Find a section by searching for its marker, `// ---------- <name> ----------`:

| Marker | What it holds |
|---|---|
| `motion: short effects for real moments` | The `FX` markup and the `fxScreen` / `fxOn` / `fxMove` engine |
| `Python literals and test harness` | Running the learner's code with Skulpt and checking the cases |
| `progress (account when signed in, this browser otherwise)` | `progress`, `lp`, saving, streak days |
| `home: the learning path` | Phases, stickers, the hover card, the Platform track, `renderHome` |
| `build it for real` | The "with the real libraries" notebook panel |
| `your own use case: the thread through Frame` | The own-idea panels (`MINE_PANELS`, `renderMine`) |
| `feedback on drafted reviews and challenges` | Thumbs and reasons on AI drafts |
| `search: lessons, glossary words and the study list` | The search view |
| `views` | `show(view)`, `openLesson`, `setStep`, the bottom bar `renderFoot`, `goNext` |
| `step panes` | `learnPane`, `checkPane`, the Explain gaps (`clozeHtml`), `anglePane` |
| `spot the gotcha` | The gotcha challenge in Explain |
| `ask about this lesson` | The tutor chips and answers |
| `build step` | `loadProblem`, the editor area, running tests |
| `the sorting board` | Build as a judgement task (`SO`, `sortRender`, `sortPlace`) |
| `the machine` | Rows travelling through the learner's function |
| `hints, review, solution` | Hint levels, code review, showing the answer |
| `notebook` | The drawer: glossary, look and motion switches |
| `study list` / `the pocket` | Saved items, the tray, spaced review |
| `selection toolbar` | Save or explain selected text |
| `editor` | Auto-indent, Tab, the symbol keys on phones |
| `events` | The one delegated click handler |
| `backends` | `claudeBackend()` and `localBackend()` |
| `boot` | Load data and progress, pick the look, first render |

The CSS follows the same order, with its own markers (`/* ---------- the pocket ... */`,
`/* fx: start */ ... /* fx: end */`).

## Recipes

**Show a new lesson field.** Add it to the helper in `model.py` (with a docstring), pass it
through `build_data()` in `build.py`, read it in the pane function, and add a content test that
it is well formed. Example to copy: `angle(say=...)` with gaps → `model.cloze` → `LESSONS[id].angle[4]`
→ `clozeHtml()` → `test_every_explain_gap_is_answerable_and_the_plain_sentence_reads_right`.

**Add a component.** Start from the nearest existing one in the `<style>` block (cards, chips,
`.btn`, `.stk`). Use tokens and the existing spacing (4–24px) and corners (4, 8, 10, 12, 14,
pill). Put its CSS next to the feature's other rules with a one-line comment saying what it is.
Add it to the components table in [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).

**Add a button or action.** Render `<button data-thing="...">`, add a line in the `events`
handler, change state, call the render function. Keep one primary button per screen.

**Add a colour.** That's a new token: [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md), "Add a token".

**Add an effect.** [PAGE.md](PAGE.md), "Motion". Only through `fxScreen` / `fxOn` / `fxMove`.

**Add a module or a track.** A module file plus its place in `PATH` or `TRACKS` in
`modules/__init__.py`; a sprite `s-<lesson id>` for each lesson's sticker; `MOD_ICON` for the
module's icon. [PAGE.md](PAGE.md), "Tracks".

## Before you call it done

- `scripts/check.sh` passes (build + fast tests).
- Restart the preview server (it caches the page), then check **375×812 and 1366×860**, in
  **Dusk and Light**, Motion on and off. No sideways scroll; taps at least 44px; keyboard focus
  visible; text readable.
- New UI text is plain, short and kind. Judgement tasks ask one question per screen; help is a
  clue first, then the answer.
- Update this page, [PAGE.md](PAGE.md) and [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) where they
  describe what you changed. `tests/test_content.py` checks that the section markers above still
  exist in `page.html`, so renaming a section means updating the map.
