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
const trackOf = { t1: {} };
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
    code = _function(page_source(), "function nextLesson() {")
    code += _function((PAGE_PARTS / "packs.js").read_text(encoding="utf-8"), "function migrateAliases() {")
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
