# Using a Claude Project as your tutor

The Daily Drill page is for practice: lessons, exercises and your study list. A Claude
Project is for conversation: explaining something another way, quizzing you, mock
interviews, reviewing an attempt, or planning a POC. These files let the project teach from
the same curriculum and know where you are.

The knowledge files, all in this repository:

- `docs/tutor/CURRICULUM_MAP.md`: every lesson (its Learn text, check question and answer,
  exercise, interview pattern, gotcha card), plus the practice sets, notebooks and glossary
- `docs/research/AGENT_PRACTICES.md`: current practice for agents, every claim checked against its source
- `docs/research/LLM_COST_AND_SIZING.md`: how to price, size and judge the ROI of LLM work before building it, with a worked example
- `docs/END_TO_END.md`, `docs/EXPERIMENT_PLAN.md`, `docs/CONCEPTS.md`, `docs/RAG_AUDIT.md`

Together they use about half of a project's space, so Claude reads them in full. The
instructions are in [PROJECT_INSTRUCTIONS.md](PROJECT_INSTRUCTIONS.md). Your snapshot is
made on your Mac and stays private.

## Set it up once (about 10 minutes)

1. **The project.** On claude.ai, open Projects and either open your tutor project or create
   one (for example "Daily Drill tutor").
2. **Instructions.** Open [PROJECT_INSTRUCTIONS.md](PROJECT_INSTRUCTIONS.md), copy the text
   in its box, and paste it into the project's instructions.
3. **Knowledge.** Two ways:
   - **Upload** (works now): in the project's knowledge, select **+**, choose to upload, and
     pick the files above from `~/Developer/langgraph/docs/`, `docs/tutor/` and `docs/research/`.
   - **From GitHub** (once these files are merged to `main`; ask Claude Code to commit and
     merge them): select **+** and choose **GitHub**. Sign in to GitHub if asked, paste
     `https://github.com/HuyD0/langgraph`, tick the files above, and select **Add files**. It
     reads the `main` branch, only works in a project you haven't shared, and lets you press
     **Sync now** when the files change.
4. **Your first snapshot** (next section).

## Every week: a fresh snapshot

Most of your practice happens on the claude.ai page, which only Claude Code can read. So
ask Claude Code, in this repository: **"make my tutor snapshot"** (the steps it follows are
at the end of this page). It writes `~/Documents/daily-drill/tutor-snapshot.md`.

Then in the project's knowledge, remove last week's `tutor-snapshot.md` and add the new one.
The snapshot is personal: it is kept outside the repository so it can't be committed.

On your own, this covers only the practice you did through `drill-server` on this Mac:

```bash
cd ~/Developer/langgraph
uv run drill tutor snapshot --copy
```

`--copy` also puts the text on the clipboard, if you'd rather paste it into the project as text.

## When the lessons change

The map is generated from the lessons, so it can't drift. After lessons change, run
`uv run drill tutor map` (the tests fail until you do), then commit, push and merge to
`main`. In the project's knowledge, select **Sync now** on the repository, or re-upload the
file.

## Things to say to it

- "quiz me"
- "explain the Wilson lesson differently"
- "mock interview: Evals"
- "review my attempt" (then paste the exercise, your code and the test output)
- "plan my POC"
- "weekly review"

Voice mode on the phone is good for talking ideas through; type when the question is about
code. Keep work specifics out of a personal project: for work questions, describe things in
general terms, like the shareable summary in [RAG_AUDIT.md](../RAG_AUDIT.md).

## For Claude Code: making the snapshot

First delete `.drill/export/study` if it exists, so items removed on the page don't come back.

1. Read the learner's progress from the page's database with ArtifactData: `get`, collection
   `data/users/me`, doc `progress`, on https://claude.ai/artifact/G7841w2YuwNwEGjwEWiDMg, with
   `out_dir` set to `.drill/export`. It lands in `.drill/export/data/users/me/progress.json`.
2. List the `study` collection the same way, into `.drill/export`, with `query.limit` 1000
   (it lands in `.drill/export/study/`).
3. Run:

   ```bash
   uv run drill tutor snapshot --progress .drill/export/data/users/me/progress.json --study .drill/export/study
   ```

`.drill/` is ignored by git, so the exports stay private too.
