# Screen gallery

Every main screen of the Daily Drill page, as it looks today, at phone (375×812) and desktop
(1366×860) size, in the Dusk and Light looks. Each picture says what the learner sees, which code
draws it, and how to change it safely. Use it to find your way around before you open
`page.html`, and to compare after a change.

How the code is organised: [../FRONTEND.md](../FRONTEND.md). Tokens, rules and components:
[../DESIGN_SYSTEM.md](../DESIGN_SYSTEM.md).

## Retake the pictures

After any change you can see, retake them and look at the difference in the PR:

```bash
uv run drill build-page
DRILL_PORT=8791 DRILL_DATABASE_URL=sqlite:///.drill/screens.db uv run drill-server   # fresh database, leave it running
node scripts/screenshots.mjs http://127.0.0.1:8791
```

Delete `.drill/screens.db` first for a clean start (the done screen marks a lesson finished). The
script uses the Google Chrome on this Mac; set `CHROME=/path/to/chrome` if it lives elsewhere. To
add a screen, add a line to `SHOTS` in `scripts/screenshots.mjs` and a section here.

---

## Home: today and the path

| Phone, Dusk | Phone, Light |
|---|---|
| ![Home on a phone in Dusk](home-phone-dusk.webp) | ![Home on a phone in Light](home-phone-light.webp) |

![Home on a desktop in Dusk](home-desktop-dusk.webp)

**What the learner sees.** The greeting, one card with the next lesson and one primary button,
then the path: six phase tabs on a violet strip, joined to the phase's room below. A first visit
shows "How it works" instead of the next lesson.

**What draws it.** `renderHome()` in the `home: the learning path` section; the tabs are
`railHtml(null, viewing)`; the card is `.next`. Colours: `--accent` for the button, `--path*` for the
strip.

**Change it safely.** Keep one primary button. New home sections go between `${upnext}` and
"Practice sets" in `renderHome()`. Text comes from the content (`D.lifecycle`), not the page.

## A phase room

![A phase room on a phone](phase-room-phone-dusk.webp)

**What the learner sees.** The chosen phase as a room: its shape glowing in the title card, what
you come out with, then one scene per module. The scene with the next lesson is open; the
others fold to a row of small shapes.

**What draws it.** `phasePage()` (scenes, `sticker()`, `minis()`), `.book.room`, `.paperN` (each
phase has its own paper), `badgeSvg()` for the title shape.

**Change it safely.** A new phase is a content change (`LIFECYCLE` in `modules/__init__.py`) plus
a shape in `phShape` and a paper. The six-phase count is tested.

## The Platform track

| Phone, Dusk | Desktop, Light |
|---|---|
| ![The Platform track on a phone](track-phone-dusk.webp) | ![The Platform track on a desktop](track-desktop-light.webp) |

**What the learner sees.** A teal side track under the path: the same room design on blueprint
paper, octagon stickers numbered P1.1, and faded "Soon" stickers for lessons not written yet.
It never moves the path's next lesson.

**What draws it.** `trackPage()`, `TRACKS`, `trackOf`, `.book.room.track`, `.paper6`, `.stk.soon`;
teal comes from the `--track*` tokens.

**Change it safely.** Add modules to the track in `TRACKS` (`modules/__init__.py`). Placeholders are
`planned(...)` in the module file. Keep teal for the track only.

## A lesson: Learn

![The Learn step on a phone](lesson-learn-phone-dusk.webp)

**What the learner sees.** One line saying where they are (back, the phase's shape, "1.1 Use case
and fit"), the title and the sticker they'll earn, the four-step stepper, then the lesson text and
its example.

**What draws it.** `openLesson()` → `lessonBar()` for the line, then `setStep(0)` → `learnPane()`;
the stepper and bottom bar are `setStep()` and `renderFoot()`. Styles `.lessonbar`, `.lb-shape`,
`.lb-t`.

**Change it safely.** Lesson words live in `modules/<module>.py` (`learn=`, `example=`). The
bottom bar has one primary button, "Next".

## A lesson: a trust mark

![A trust mark's tooltip, opened](trust-mark-phone-dusk.webp)

**What the learner sees.** A small ember right after the words where the lesson touches
responsible AI, privacy or governance. Tapping it opens a tooltip: the trustworthy-AI trait, the
NIST AI RMF reference, a perspective, one tip, and seven dots for the traits practised so far.
Unopened marks give off embers; with Motion off (as here) they are a still glow.

**What draws it.** `learnPane()` calls `withTrust()` for each paragraph, which places
`trustMarkHtml()` after the note's phrase and adds `trustPopHtml()`; `openTrust()` and
`closeTrust()` run from their own click and Escape listeners in the `trust marks` section.

**Change it safely.** The notes are `content/trust.py`, one per lesson at most; the phrase must
appear once in the Learn text (a test checks). Colours are `--mark` and `--mark-glow`.

## A lesson: Check

![The Check step after answering](lesson-check-phone-dusk.webp)

**What the learner sees.** Up to three multiple-choice questions, one at a time ("Question 1 of
3"). A wrong pick is crossed out and they try again; help is a clue, then the answer. Once a
question is right, the reason shows and the tutor offers "Why not ...?" and "Give me a harder one
like this" (not before: it would give the answer away).

**What draws it.** `checkPane()` with `checkQs()`; answers are `checkPick`, `checkHelp`, `checkNext` (`data-opt`, `data-chk-help`, `data-chk-next` in the `events` section); the
tutor chips are `askPanel()`, and the tutor gets `askContext()`, which includes the module's
`setting`.

**Change it safely.** Question 1 is `question(...)` in the lesson; questions 2 and 3 are `ask(...)` in `content/checks/<module>.py`, with the writing rules at the top of `content/checks/__init__.py`. Keep exactly one right answer
and a plain `why`.

## A lesson: Build (code)

![The Build step with code on a desktop](build-code-desktop-dusk.webp)

**What the learner sees.** The task, a fill-in-the-blanks scaffold (or a blank start), Run tests
in the bottom bar, hints that go step by step, and a Learn panel with the ideas it needs.

**What draws it.** `loadProblem()` and the `build step`, `hints, review, solution` and `editor`
sections; the code runs in the browser with Skulpt (`Python literals and test harness`).

**Change it safely.** Everything about an exercise is `exercise(...)` in the lesson.
`drill build-page` fills each scaffold's blanks with `fills` and runs the tests, so they can't
drift apart.

## A lesson: Explain

| Gaps, with a clue (Dusk) | Finished (Light) |
|---|---|
| ![Explain with a gap and a clue](explain-gaps-phone-dusk.webp) | ![Explain finished](explain-done-phone-light.webp) |

**What the learner sees.** The lesson's sentence with two or three gaps, filled one at a time from
three words. A wrong word is crossed out; "Give me a clue" comes first, then "Tell me the answer".
Writing it your own way is optional, underneath.

**What draws it.** `clozeHtml()`, `clozePick()` and `CLZ` in `step panes`, inside `anglePane()`;
styles `.cloze`, `.gap`, `.clzchip`, `.clzclue`.

**Change it safely.** The sentence and its gaps are `angle(say=...)`, written
`[[answer|wrong|wrong::clue]]`. It must sound like a person talking (see [../PAGE.md](../PAGE.md)).
Tests check every gap.

## A walkthrough of a tool's screens

![A Spacelift run header, redrawn with numbered callouts](walkthrough-phone-dusk.webp)

**What the learner sees.** In "Reading a Spacelift run", the real screens of a Spacelift run
(header, Changes tab, planning log, plan diff, run history) redrawn in the app's look, so they fit a
phone and follow the theme. Numbered callouts in the hint colour match the numbered steps under
each screen, followed by "Good habits" tips.

**What draws it.** `walkHtml()` and `SL_VIEW` (one function per kind of screen) in the
`walkthrough` section; styles `.sl-*`. The content is `walkthrough=[screen(...)]` in the lesson.

**Change it safely.** Each part with `"n": 3` needs step 3; `screen()` fails at build time if the
numbers and steps don't match. A new kind of screen needs a renderer in `SL_VIEW` (a test checks).

## Finishing a lesson

![The done screen](done-screen-phone-dusk.webp)

**What the learner sees.** A check, how far they are in the phase or track, their result to
share (a mark for each step, the first time through), the new sticker, what they did in the
lesson, and what's next. "Done for today" is the primary button; Share result is quiet.

**What draws it.** `showDone()` in `views`, reached from `goNext()` on the last step; the result
card is `resultHtml()` in `page/share.js`.

## A lesson: Practice questions

![A practice question on a phone](practice-phone-dusk.webp)

**What the learner sees.** In lessons whose skill is a decision or reading evidence (which compute
for this work, is the pilot fit for purpose, what a plan really does), the step is called Practice
and is a short run of questions instead of code:
a piece of evidence (a YAML file, a chain of stops, a plan, a claim, a prompt), then one plain
question with two to four answers, in a fixed shuffled order. "Give me a clue" comes first, then the answer; the dots show how far
along they are. Some questions are "Fix the YAML": edit the file until it passes. Python stays
one tap away.

**What draws it.** `qfRender()`, `qfPick()`, `qfHelp()` and `QF` in the `practice questions` section; Fix the
YAML is `yamlRead()` and `yamlCheck()`, mirrored in Python by `content/yaml_rules.py`. The content
is `exercise(practice=practice(asks=[ask(...), fix(...)]))` in the lesson.

**Change it safely.** One question per screen, clue before answer. Each `ask` needs exactly one
right answer and a `clue`, and the right option mustn't be much the longest; a `fix` needs a start
that fails and an answer that passes (tests check all three).

## The study list

| On Home | Opened |
|---|---|
| ![The study list row on Home](study-row-phone-dusk.webp) | ![The study list opened](study-list-phone-dusk.webp) |

**What the learner sees.** Closed, one quiet row under the Today card: a ring with a count and
"3 learning · 2 to review". It never floats over a lesson or pulses. Tapping it opens the sheet:
everything they saved, in three tabs (To review, Still learning, Got it), with seals for each
spaced review. Due reviews also show as one line on the Today card ("Also: 2 quick reviews").

**What draws it.** `studyRowHtml()`, `renderPocket()` and `openPocket()` in
`page/study-list.js`; styles `.studyrow`, `.reviewline` and `.pocket` in `page/pocket.css`. Saved
items come from the backend (`study` docs).

**Change it safely.** Keep it out of the lesson screens: it appears when asked for. The row is
hidden when nothing is saved.

## Search

![Search on a phone](search-phone-dusk.webp)

**What the learner sees.** One box that finds lessons, glossary words and study-list items.

**What draws it.** `openSearch()`, `renderSearch()` in `search: lessons, glossary words and the
study list`; the index is `SEARCH_INDEX`.
