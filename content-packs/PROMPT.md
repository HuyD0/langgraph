# A prompt for wiring up the internal curriculum

Paste this into Claude Code inside the **approved private copy** of this repository, with your
source material (a workbook, documentation, screenshots) available to it. It contains no internal
information itself; it tells Claude where your material goes and the standard it must meet.

---

You are working in the private copy of the Daily Drill repository. Read `docs/CONTENT_PACKS.md`,
`content-packs/templates/` and the fictional example in `tests/fixtures/content-packs/example/`
first, then fill in the **Infrastructure as Code: Applied Practice** pack in
`content-packs/iac-applied/` from the material I give you.

Steps:

1. Delete `content-packs/PUBLIC`: this is the private copy, so real lessons belong here.
2. Read my source material and map it to the slots (A1–A6, B1–B6, the capstone C1) using the
   "From a workbook to a pack" table in the guide. List the mapping for me before writing.
3. For each slot you have material for: copy `content-packs/templates/lesson.example.yaml` over
   the slot file, keep its `id`, and write the lesson. Set `status: draft`.
   - **Learn**: why it matters first, then the idea, in plain words and short sentences. Explain
     every term the first time. One approved configuration or code example, cut to what matters.
   - **Views**: a `relationships`, `trace`, `walkthrough`, `plan_review` or `tour` view where the
     material has one. For a screenshot with numbered callouts, make a `tour`: copy the image to
     `assets/`, and give each callout a stop with its box as percentages (x, y, w, h) of the image,
     a short title and one sentence. Set `ratio` to the image's height divided by its width.
   - **Check**: one multiple-choice question on the main idea, with why.
   - **Practice**: the exercise kind that fits (see the guide's table). Practice questions with an
     expected-answer table become a `reasoning` exercise; "why did it fail" becomes
     `troubleshooting` with `next_check` and `handoff`.
   - **Explain**: the reasoning, one sentence to compare, common mistakes, and the investigation
     steps in order.
   - **Evidence**: every source, with its reference, revision, `status` and the date reviewed. Mark
     a source `verified` only if I confirm it is current.
4. Never invent facts. If the material doesn't cover something a lesson needs, leave a `_TODO`
   there, keep the lesson a `draft`, and list what's missing for me.
5. Run `uv run drill content check content-packs/iac-applied` until it passes, and
   `uv run pytest`.
6. Preview with `uv run drill content preview content-packs/iac-applied` at phone width. Check
   each lesson's four steps, and each tour's boxes line up with what they describe.
7. Read every lesson as a beginner would: plain words, no unexplained acronyms, no step that
   assumes knowledge the lesson didn't give. Fix what fails.
8. When I approve a lesson, set it to `ready`. Then turn the pack on: add `DRILL_CONTENT_PACKS`
   with the value `content-packs/iac-applied` to `app.yaml`'s env, and deploy with
   `uv run drill cloud deploy --target work` (or `./scripts/port-to-workspace.sh`).
9. Give the app's address to the learners with `uv run drill cloud share <email>`, and tell them
   their manager can see their progress, study list and questions.

Keep everything inside this private copy. Don't publish the page anywhere public:
everything in it can be read by anyone who can open it.
