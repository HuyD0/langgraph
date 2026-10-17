# Proposal: Quiet ink

Status: **being built** on branch `claude/quiet-ink-build`. The research pass that ran alongside turned out to be
the audit in PR #101: nothing in it conflicts with this plan, and its design fixes (dead CSS gone, the Dusk
primary button on tokens, 44px targets) make the build simpler. Built so far: the type, the ink wash, motion E
(step rise and the finish bloom), the short brush done line, and a still glow instead of the flicker on the
primary button and the current step. Not yet: follow-up 2 (the ink spreading into the wash) and follow-up 3
(E-style marks); the stickers' aura and the walkthrough's flame are kept for now.

## The idea in one line

Give Dusk a calmer, more crafted feel: a characterful heading face, one brush-written line for the
moments that matter, a soft ink wash under the glass, and motion that settles instead of flaring.

## What's proposed

### 1. Type

| Role | Today | Proposed | Where |
|---|---|---|---|
| Headings | Bricolage Grotesque 800 | **Kaisei Tokumin** 700/800 | Greeting, lesson titles, card titles, section heads |
| The "moment" line | Bricolage Grotesque 800 | **Yuji Boku** (brush) | "Lesson done." and the phase-done line only |
| Brand name, body, code, labels | Bricolage / IBM Plex Sans / JetBrains Mono | no change | |

Both are Google Fonts under the Open Font License; only their Latin letters load, about 60 to 90 KB
together. As tokens: `--head` replaces `--display` on headings, and a new `--moment` is used for the
one big line. The brand name keeps Bricolage so the logo doesn't change.

### 2. Ink wash (Dusk only)

Soft violet-blue clouds drawn by the page itself (SVG noise, no image file), behind the cards, at
about a quarter strength. Light stays plain. It doesn't move on its own; it only stirs once on a finish (follow-up 2).
A first version at double strength competed with the text; keep it quiet.

### 3. Motion: direction E, "Quiet ink"

Chosen from five directions (A Ink stroke, B Seal stamp, C Ember, D Panel cut, E Quiet ink).

- **Step change:** the new step rises in softly (6px, 280ms, transform and opacity only).
- **Finish:** "Lesson done." fades up and one ink drop blooms under it; the result marks fade in one
  by one.
- **Glyphs:** hairline strokes in `--muted` with a single `--accent` dot. Used for earned marks (result
  marks, study-list seals, Check verdicts) in Dusk; today's line icons stay for buttons and menus.

Follows the existing motion rules: real moments only, nothing loops or blocks. Since PR #98 all animation
plays for everyone (no Motion switch, no reduced-motion fallback), so E being gentle matters more:
nothing in it flashes, loops or moves far.

### 4. Follow-ups that make the rest of the app match

1. **A motion budget for Dusk.** The flickering primary button, the burning aura on the current step
   and today's sticker, and the dark "space" opening on finish feel loud next to E. Keep one
   signature moment for finishing a lesson and one for finishing a phase; turn the rest into a still
   glow.
2. **The ink wash responds.** On finishing a lesson, E's ink drop spreads into the background wash
   for a second, then settles.
3. **E-style marks** for everything you earn, in Dusk.

### 5. Later, separate PR (the remaining calmer-lessons items; check what other work already did)

- Learn text in short steps headed by their key term, framework names in a small note.
- Real figures for the ~29 lessons that draw tables and maps in characters.
- No lesson text under 13px; every tap target at least 44px.

## Mockups

Open from a local server at the repo root (`python3 -m http.server`), or straight from the file.

- [type-mock.html](quiet-ink/type-mock.html): four heading faces side by side, with paper, ink and
  photocopy textures.
- [type-combo.html](quiet-ink/type-combo.html): the chosen combination across Home, Learn, Check and
  the done screen, with Before/After and Dusk/Light switches.
- [motion-options.html](quiet-ink/motion-options.html): the five motion directions as live mini lessons;
  E is the one chosen.

All marks and textures are drawn from scratch; nothing is taken from other artwork.

## Questions for the research to answer

- Does the research suggest a different heading face, or a different place for the brush line?
- Does it support cutting back the Dusk flames (follow-up 1), or keeping some of them?
- Anything on readability for beginners on a phone that should change the order of the work?

## Build plan once agreed

One PR on this branch: the tokens (`--head`, `--moment`, the ink layer), direction E's step change and
finish in the fx engine, the E-style marks, and follow-ups 1 to 3. Check at 375×812 and 1366×860 in
Dusk and Light, then update the Design System artifact (type tokens, a Motion card
for E) and retake the screen gallery.
