"""Saved progress can name a lesson this page doesn't have. An unknown id (from another version of
the app, or a removed pack lesson) must not become "the lesson you are on" (nextLesson): the path
decides instead, or Home, search and the phase tabs throw and the page stays blank. The old id of a
renamed lesson follows it to its new id (migrateAliases). The real functions are lifted from the
page source and run by node against a small stand-in path."""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from drill.content.build import PAGE_PARTS, page_source


def _function(src: str, first_line: str) -> str:
    start = src.index(first_line)
    return src[start:src.index("\n}\n", start) + 2]


HARNESS = r"""
const D = { aliases: { old_name: "b" } };      // a renamed core lesson
const ORDER = ["a", "b", "c", "d"];             // the AI path
const LESSONS = { a: {}, b: {}, c: {}, d: { pack: { aliases: ["old_pack_name"] } },  // d: a renamed pack lesson
                  t1: {} };                     // t1 is on the platform track, not the path
const ALL_LESSONS = Object.keys(LESSONS);
const trackOf = { t1: {} };
const kept = new Map();                         // this device's other saved keys (drafts, practice)
const store = { get: k => kept.has(k) ? kept.get(k) : null, set: (k, v) => kept.set(k, v), remove: k => kept.delete(k) };
let progress;
/*CODE*/
const run = (saved) => {
  progress = Object.assign({ solved: {}, days: [], lessons: {}, gotchas: {}, current: null }, saved);
  migrateAliases();
  return { next: nextLesson(), current: progress.current };
};
"""

def run(js: str) -> object:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    page, packs = page_source(), (PAGE_PARTS / "packs.js").read_text(encoding="utf-8")
    start = page.index("const RENAMED = ")
    code = page[start:page.index("\n", page.index("const knownLesson = ", start)) + 1]
    code += _function(page, "function nextLesson() {")
    code += packs[packs.index("const RENAMED_KEYS = "):packs.index("\n", packs.index("const RENAMED_KEYS = ")) + 1]
    code += _function(packs, "function migrateAliases() {")
    script = HARNESS.replace("/*CODE*/", code) + "\nconsole.log(JSON.stringify((() => { " + js + " })()));"
    out = subprocess.run([node, "-e", script], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr[-1500:]
    return json.loads(out.stdout)


def test_a_saved_lesson_the_page_does_not_have_falls_back_to_the_path():
    got = run("""return run({ current: "from_another_branch",
                             lessons: { from_another_branch: { step: 1, done: false }, a: { step: 4, done: true } } });""")
    assert got["next"] == "b", "an unknown saved lesson must not become the lesson you are on"


def test_the_lesson_you_were_on_is_kept_when_the_page_has_it():
    got = run("""return [run({ current: "c", lessons: { c: { step: 2, done: false } } }).next,
                         run({ current: "c", lessons: { c: { step: 4, done: true } } }).next,
                         run({ current: "t1", lessons: { t1: { step: 1, done: false } } }).next];""")
    assert got == ["c", "a", "a"], "on the path and not done: kept; done or a track lesson: the path decides"


def test_a_renamed_lesson_you_were_on_follows_its_new_id():
    got = run("""return [run({ current: "old_name", lessons: { old_name: { step: 2, done: false } } }),
                         run({ current: "old_pack_name", lessons: { old_pack_name: { step: 1, done: false } } })];""")
    assert got == [{"next": "b", "current": "b"}, {"next": "d", "current": "d"}], "core and pack renames both"


def test_everything_saved_under_an_old_id_moves_and_the_old_entry_goes():
    got = run("""
      kept.set("drill-draft-old_name", "def f(): pass"); kept.set("drill-px-old_name", "{}");
      run({ current: "old_name", lessons: { old_name: { step: 3, done: true, first: { day: "2026-11-02" } } },
            solved: { old_name: { count: 1 } }, gotchas: { old_name: 1 } });
      return { lessons: progress.lessons, solved: progress.solved, gotchas: progress.gotchas,
               keys: [...kept.keys()].sort() };""")
    assert got["lessons"] == {"b": {"step": 3, "done": True, "first": {"day": "2026-11-02"}}}, "one record, so it counts once"
    assert got["solved"] == {"b": {"count": 1}} and got["gotchas"] == {"b": 1}
    assert got["keys"] == ["drill-draft-b", "drill-px-b"], "unfinished code and practice follow the lesson"


def test_records_under_both_ids_are_joined():
    got = run("""run({ lessons: { old_name: { step: 3, done: true, first: { day: "d1" } }, b: { step: 1, done: false, checked: 2 } } });
                 return progress.lessons;""")
    assert got == {"b": {"step": 3, "done": True, "checked": 2, "first": {"day": "d1"}}}, "done in either, the further step"


def test_old_links_find_the_renamed_lesson():
    got = run("""return [knownLesson("old_name"), knownLesson("old_pack_name"), knownLesson("c"),
                         knownLesson("nope"), knownLesson("__proto__"), knownLesson("constructor")];""")
    assert got == ["b", "d", "c", None, None, None]
