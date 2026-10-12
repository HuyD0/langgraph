# The design system: how to use it, change it and improve it

Daily Drill's look is a small design system: named values (tokens), a handful of components,
two looks (Dusk and Light), a motion layer, and a few rules. This page says where each part
lives, the rules, and how to make the common changes safely.

## Where it lives

| What | Where | Notes |
|---|---|---|
| **Tokens**: every colour, font, timing and the column width | `src/drill/content/tokens.css` | The one source of truth. `build.py` inlines it into the page at `/*TOKENS*/` |
| **Components and looks**: buttons, cards, the stepper, the machine, Dusk's glass and glow | `src/drill/content/page.html`, in `<style>` | Every rule uses `var(--token)`, never a raw colour (a test checks the names exist) |
| **Motion**: the twelve effects | `page.html`, between `/* fx: start */` and `/* fx: end */`, plus the `fxScreen` / `fxOn` / `fxMove` engine | Catalogue and rules: [PAGE.md](PAGE.md), "Motion" |
| **Design System artifact** (reference, for designing new screens) | https://claude.ai/artifact/Pfq6TaX5tHMs1iUbZCqZ9U | Colour tokens (light and dark), type, spacing, radii, component cards, the brand book README |
| **Design canvas** (why things look the way they do) | https://claude.ai/artifact/DA8WMYSJh7jTSwnsyDgQVa | Boards for colour, type, spacing, components and patterns |
| **Explorations** (palettes, the Dusk look, animation drafts) | https://claude.ai/artifact/SSb5sYRyKLtgnY1owsTY2o | Playable drafts; nothing here ships until it's built into the page |

The code is the truth. The artifacts describe it; when they disagree, the code wins and the
artifact gets updated.

## The rules

1. **One reading column**, at most `--col` (760px) wide. Side things slide in as a drawer.
2. **Colour means one thing.** `pass` only means passed or done, `fail` only failed or wrong,
   `hint` only a hint or a warning, `accent` the one thing to do next. `--path` (violet) marks
   the route through the phases. Effects use only the `--fx-*` colours.
3. **One primary button per screen**, for the next step.
4. **Thumb first.** Controls are at least 44px tall on touch; check every change at phone width.
5. **Readable in every look.** Text 4.5:1 against its background, icons and borders 3:1
   (`scripts/contrast.py` checks the main pairs).
6. **Motion marks real moments** and never blocks a tap. Nothing moves with reduced motion or
   Motion: Off.
7. **Plain words.** No Big-O, no maths notation, a term explained the first time it appears.

## The tokens

| Family | Names | Used for |
|---|---|---|
| Ground | `bg`, `surface`, `sunk`, `code-bg`, `line` | The page, cards, recessed fills, code, borders |
| Text | `fg`, `muted` | Reading text, secondary text |
| Accent | `accent`, `accent-ink`, `accent-soft` | The next action, focus rings, the current step |
| Verdicts | `pass`/`pass-bg`, `fail`/`fail-bg`, `hint`/`hint-bg` | Strong colour for text and icons, `-bg` twin for the fill behind |
| Path | `path`, `path-bg`, `path-line`, `path-ink` | The phase tabs on Home |
| Code | `syn-kw`, `syn-str`, `syn-num`, `syn-com`, `syn-fn`, `syn-bi` | Code colours; never green or red |
| Machine | `tok-a` to `tok-d` | The row pills |
| Type | `display`, `body`, `mono` | Headings, reading, anything the computer said |
| Motion | `dur-tap`, `dur-step`, `dur-moment`, `dur-big`, `dur-slide`, `ease-out`, `ease-in`, `ease-pop` | How long things move, and how |
| Effects | `fx-core`, `fx-glow`, `fx-veil`, `fx-red`, `fx-mix` | Only the motion effects |
| Layout | `col` | The column width |

## The looks

`<html data-theme="...">` picks the look. A small script at the top of the page sets it before
anything draws, from `drill-theme` in the browser's storage: **Dusk** unless Light was chosen
(the Look switch in the Notebook). `tokens.css` defines the light values on `:root`, then
overrides them for `data-theme="dark"` (and the system's dark mode) and `data-theme="dusk"`.
Dusk adds glass, grain and the burning glow on what's current; those rules sit in `page.html`
under `:root[data-theme="dusk"]`, with fallbacks for reduced motion and reduced transparency.

## How to make common changes

**Change a colour.** Edit it in `tokens.css`, in every look that sets it. Then:

```bash
uv run python scripts/contrast.py      # every pair in every look still readable?
uv run drill build-page && uv run pytest -q tests/test_content.py
```

**Add a token.** Add it to `:root` in `tokens.css` with a comment saying what it's for, then to
the dark and dusk blocks if it should differ there. Use it as `var(--name)`. A test fails if the
page uses a name `tokens.css` doesn't define.

**Style a new component.** Build it from existing tokens and the spacing and radius steps the
page already uses (gaps of 4 to 24px; corners of 4, 8, 10, 12, 14 or pill). Start from the
nearest existing component in `page.html`. If it needs a new colour, that's a new token, not a
hex value in the rule.

**Add a motion effect.** Follow [PAGE.md](PAGE.md), "Motion": markup in `FX`, rules in the fx
block with an `fx-end` finish, and a call to `fxScreen` or `fxOn` at the moment. The tests check
it never loops or blurs and that its keyframes exist.

**Add a look.** Add a `:root[data-theme="<name>"]` block to `tokens.css` overriding what
differs (including the `--fx-*` colours), add it to the contrast checker's `looks()`, add a
button to the Look switch in `page.html` (`LOOKS` and the `data-theme-pick` buttons), and update
the motion tokens test, which counts one `--fx-*` set per look.

**Try ideas before building them.** Ask Claude for mockups on the exploration canvas (or a new
one), compare them at phone size, then build the chosen one into `tokens.css` and `page.html`.

## Look at a change before it ships

```bash
uv run drill build-page
DRILL_PORT=8790 DRILL_DATABASE_URL=sqlite:///.drill/preview.db uv run drill-server
```

Open http://127.0.0.1:8790 at phone width (the raw `dist/daily-drill.html` has no viewport tag,
so use the server). Check both looks (Notebook → Look), Motion On and Off, and a lesson's four
steps. The preview database keeps your real progress out of it. Restart the server after editing
`page.html`: it caches the page when it starts.

## Keep the design system artifact in step

When tokens or components change, the Design System artifact should follow. Ask Claude to
"update the design system" with what changed: colour tokens go in its `tokens.json` (light and
dark values; it has no Dusk theme yet), and rules go in its README's sections. Its format has no
motion family, so timings and curves are described in the README's Motion section instead.

## Ship it

```bash
uv run drill build-page
uv run pytest -q
```

Open a PR; after it's merged, publish `dist/daily-drill.html` to the Daily Drill artifact, and
run `uv run drill cloud deploy` for the Databricks app. Other sessions publish too: compare the
live page with your build first, so you don't undo someone else's work.
