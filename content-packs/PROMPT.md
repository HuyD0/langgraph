# A prompt for wiring up the internal curriculum

Paste this into Claude Code (or Copilot) inside the **work copy** of this repository, with your
source material (a workbook, documentation, screenshots) available to it. It contains no internal
information itself; it tells the agent where your material goes and the standard it must meet.

---

You are working in the work copy of the Daily Drill repository: a downstream of the public
repository, merged from it and never retyped (read `docs/PORTING.md`, "Keeping the work copy in
step", and the "Two copies" rules in `AGENTS.md`). Read `docs/CONTENT_PACKS.md`,
`content-packs/templates/` and the fictional example in `tests/fixtures/content-packs/example/`
first, then fill in the **Infrastructure as Code: Applied Practice** pack in
`content-packs/internal/` from the material I give you.

Rules that hold throughout:

- Edit only `content-packs/internal/`. Never `src/`, `docs/`, `app.yaml`,
  `content-packs/iac-applied/` or `content-packs/PUBLIC`: those belong to the public repository.
  If you find a bug or better wording there, write it down for me as a note with no internal
  names, so I can take it upstream.
- "How this works at our company for lesson X" is a new pack lesson in `content-packs/internal/`
  with `prerequisites: [<the core lesson's id>]`, so it follows its public twin on the path.
  Never an edit to `src/drill/content/modules/`.

Steps:

1. If `content-packs/internal/` doesn't exist yet, create it by copying
   `content-packs/iac-applied/` (its `pack.yaml`, `lessons/` and `assets/`), keeping every lesson
   id. Leave `content-packs/PUBLIC` and `content-packs/iac-applied/` exactly as they are.
2. Read my source material and map it to the slots (A1–A6, B1–B6, the capstone C1) using the
   "From a workbook to a pack" table in the guide. List the mapping for me before writing.
3. For each slot you have material for: copy `content-packs/templates/lesson.example.yaml` over
   the slot file in `content-packs/internal/lessons/`, keep its `id`, and write the lesson. Set
   `status: draft`.
   - **Learn**: why it matters first, then the idea, in plain words and short sentences. Explain
     every term the first time. One approved configuration or code example, cut to what matters.
   - **Views**: a `relationships`, `trace`, `walkthrough`, `plan_review` or `tour` view where the
     material has one. For a screenshot with numbered callouts, make a `tour`: copy the image to
     `content-packs/internal/assets/`, and give each callout a stop with its box as percentages
     (x, y, w, h) of the image, a short title and one sentence. Set `ratio` to the image's height
     divided by its width.
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
5. Run `uv run drill content check content-packs/internal` until it passes, and
   `uv run pytest`.
6. Preview with `uv run drill content preview content-packs/internal` at phone width. Check
   each lesson's four steps, and each tour's boxes line up with what they describe.
7. Read every lesson as a beginner would: plain words, no unexplained acronyms, no step that
   assumes knowledge the lesson didn't give. Fix what fails.
8. When I approve a lesson, set it to `ready`. `app.yaml` already points `DRILL_CONTENT_PACKS` at
   `content-packs/internal`, so don't edit it: commit the pack and deploy with
   `uv run drill cloud deploy --target work` (or `./scripts/port-to-workspace.sh`).
9. Give the app's address to the learners with `uv run drill cloud share <email>`, and tell them
   their manager can see their progress, study list and questions.

Keep everything inside this work copy. Don't publish the page anywhere public:
everything in it can be read by anyone who can open it.
