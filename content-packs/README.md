# Content packs

Optional lessons kept apart from the public curriculum, written as YAML. A pack loads only when
asked (`DRILL_CONTENT_PACKS`, or `drill build-page --pack`), so the public page never holds one.

| Here | What it is |
|---|---|
| `iac-applied/` | **Infrastructure as Code: Applied Practice**: the slots for an internal curriculum (Journey A, Journey B, a capstone). Every lesson is a slot, so it shows nothing until filled in, in a private copy. |
| `templates/` | Copy these to write a pack, a lesson, an exercise (all ten kinds), a case study or evidence. |
| `PROMPT.md` | A prompt to paste into Claude Code in the private copy: it fills the slots from your material, checks, previews and deploys. |
| `PUBLIC` | Marks this as the public repository: tests then check that every lesson here is still a slot. Delete it in the private copy. |

The guide: [docs/CONTENT_PACKS.md](../docs/CONTENT_PACKS.md). A complete, fictional example pack
(used by the tests) is in `tests/fixtures/content-packs/example/`.

Keep real material out of this public repository: put private packs **outside it** (point
`DRILL_CONTENT_PACKS` at them), or in `content-packs/private/`, which git ignores.
