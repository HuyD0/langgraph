# Content packs

Optional lessons kept apart from the public curriculum, written as YAML. A pack loads only when
asked (`DRILL_CONTENT_PACKS`, or `drill build-page --pack`), so the public page never holds one.

| Here | What it is |
|---|---|
| `iac-applied/` | **Infrastructure as Code: Applied Practice**: the slots for an internal curriculum (Journey A, Journey B, a capstone). Every lesson is a slot, so it shows nothing until filled in. It stays slots only in both copies of the repository. |
| `internal/` | **Work copy only.** The real pack: a copy of `iac-applied/` (its `pack.yaml`, `lessons/`, `assets/`) with the same lesson ids, filled in. The public repository never has this folder; `app.yaml` already points `DRILL_CONTENT_PACKS` at it, and a folder that isn't there is skipped. An upstream merge never touches it. |
| `templates/` | Copy these to write a pack, a lesson, an exercise (all ten kinds), a case study or evidence. |
| `PROMPT.md` | A prompt to paste into Claude Code in the work copy: it fills `internal/` from your material, checks, previews and deploys. |
| `PUBLIC` | Marks the shared packs as slots only: tests then check that every lesson in `iac-applied/` is still a slot. It stays in both copies. |

The guide: [docs/CONTENT_PACKS.md](../docs/CONTENT_PACKS.md). A complete, fictional example pack
(used by the tests) is in `tests/fixtures/content-packs/example/`. How the two copies relate, and
how fixes travel between them: [docs/PORTING.md](../docs/PORTING.md), "Keeping the work copy in step".

Keep real material out of this public repository. Anything that must reach the Databricks App has
to be a tracked folder in the work copy (`internal/`): `databricks bundle deploy` honours
`.gitignore`, so a git-ignored folder never leaves the laptop. `content-packs/private/`, which git
ignores, is for laptop-only previews (`drill content preview`), or point `DRILL_CONTENT_PACKS` at a
folder outside the repository.
