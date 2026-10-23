"""Prepared answers for the tutor's standard questions (drill.tutor_prepared)."""

import json
import shutil
import subprocess

import pytest

from drill import tutor_prepared as tp
from drill.content.build import PAGE_TEMPLATE, build_data


@pytest.fixture(scope="module")
def data():
    return build_data()


def test_the_prepared_questions_are_the_pages_own_words(data, tmp_path):
    """askChips() in page/ask.js and chips() here must ask the same questions with the same keys:
    the page serves a prepared answer only on an exact match."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    ask = (PAGE_TEMPLATE.parent / "page" / "ask.js").read_text(encoding="utf-8")
    gotchas = tp._gotchas(data)
    probe = f"""
const D = {json.dumps({"lessons": data["lessons"], "glossary": data["glossary"]}, ensure_ascii=False)};
const LESSONS = D.lessons, GOTCHAS = {json.dumps(gotchas, ensure_ascii=False)};
const GLOSS = D.glossary.flatMap(([, terms]) => terms.map(([term, def]) => ({{ term, def }})));
const short = (s, n = 90) => s.length > n ? s.slice(0, n - 1) + "…" : s;
const words = t => (t || "").trim().split(/\\s+/).filter(Boolean).length, SAY_WORDS = 4;
let cur, at = 0;
const lp = () => ({{ said: "" }}), checkQs = id => [LESSONS[id].check, ...(LESSONS[id].more || [])];
const checkState = () => ({{ at, solved: [true, true, true, true] }});
{ask}
const out = {{}};
for (const id of Object.keys(LESSONS)) {{
  if (!LESSONS[id].learn || !LESSONS[id].learn.length) continue;
  const got = [];
  cur = {{ id, step: 0 }}; got.push(...askChips());
  for (at = 0; at < checkQs(id).length; at++) {{ cur = {{ id, step: 1 }}; got.push(...askChips()); }}
  cur = {{ id, step: 3 }}; got.push(...askChips());
  out[id] = got.filter(c => c.key).map(c => [c.key, c.q]);
}}
console.log(JSON.stringify(out));"""
    (tmp_path / "chips.js").write_text(probe, encoding="utf-8")
    page = json.loads(subprocess.run([node, str(tmp_path / "chips.js")], capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    ours = {lid: [[c["key"], c["q"]] for c in items] for lid, items in tp.chips(data).items()}
    for lid, items in ours.items():
        assert sorted(map(tuple, page[lid])) == sorted(map(tuple, items)), lid


def test_only_answers_that_passed_and_still_match_their_lesson_are_served(data):
    lid, items = next(iter(tp.chips(data).items()))
    chip = items[0]
    rec = {"q": chip["q"], "a": "An answer.", "fingerprint": tp.fingerprint(data, lid, chip), "status": "passed"}
    assert tp.served(data, {lid: {chip["key"]: rec}}) == {lid: {chip["key"]: {"q": chip["q"], "a": "An answer."}}}
    for broken in ({"status": "failed"}, {"status": "rejected"}, {"fingerprint": "old"}, {"q": "Another question?"}):
        assert tp.served(data, {lid: {chip["key"]: {**rec, **broken}}}) == {}


def test_a_draft_the_judge_rejects_is_redrafted_once_with_its_note(data):
    lid, items = next(iter(tp.chips(data).items()))
    drafts, verdicts = iter(["First try.", "Second try."]), iter([
        '{"correct": false, "answers_it": true, "plain": true, "no_giveaway": true, "standalone": true, "notes": "Wrong about gates."}',
        '{"correct": true, "answers_it": true, "plain": true, "no_giveaway": true, "standalone": true, "notes": ""}'])
    prompts = []
    rec = tp.prepare_one(data, lid, items[0], lambda p: (prompts.append(p), next(drafts))[1], lambda _: next(verdicts))
    assert rec["a"] == "Second try." and rec["status"] == "passed" and "Wrong about gates." in prompts[1]


def test_the_page_carries_the_served_answers(data):
    assert data["prepared"] == tp.served(data)


def test_a_packs_answers_live_inside_the_pack(tmp_path):
    """In the work copy the overlay is content-packs/internal/: a pack lesson's answers are saved there,
    never in the curriculum's folder, and load/served see both together."""
    import shutil
    from pathlib import Path

    from drill import tutor_prepared as tp
    from drill.content import modules, packs
    from drill.content.build import build_data

    root = tmp_path / "example"
    shutil.copytree(Path(__file__).resolve().parent / "fixtures" / "content-packs" / "example", root)
    loaded = modules.load()
    pack = packs.load_pack(root, drafts=False, taken={lesson["id"] for m in loaded for lesson in m.lessons})
    data = build_data(loaded, [pack])
    chips = tp.chips(data)
    core_lid, pack_lid = loaded[0].lesson_ids[0], pack.modules[0].lesson_ids[0]

    def record(lid):
        chip = chips[lid][0]
        return {chip["key"]: {"q": chip["q"], "a": "A checked answer.", "step": chip["step"], "fingerprint": tp.fingerprint(data, lid, chip),
                              "status": "passed", "model": "m", "judge": {"model": "j", "pass": True, "notes": ""}}}

    answers = {core_lid: record(core_lid), pack_lid: record(pack_lid)}
    core_dir = tmp_path / "core"
    tp.save(data, answers, directory=core_dir, packs=[pack])
    assert list((root / "prepared").glob("*.json")), "the pack's answers are written inside the pack"
    assert not any(pack_lid in f.read_text(encoding="utf-8") for f in core_dir.glob("*.json")), "and not in the curriculum's folder"
    assert tp.load(directory=core_dir, packs=[pack]) == answers
    served = tp.served(data, tp.load(directory=core_dir, packs=[pack]))
    assert core_lid in served and pack_lid in served

