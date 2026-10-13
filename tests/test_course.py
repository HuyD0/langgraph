"""The beginner course, docs/course/inside-page-html.html, teaches from the real code. These checks
keep it honest: every line it shows from the project still exists, every lesson it names is real,
and its own script parses."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "docs" / "course" / "inside-page-html.html"


def _course() -> str:
    return COURSE.read_text(encoding="utf-8")


def _anchors() -> list[dict]:
    block = _course().split('<script type="application/json" id="anchors">', 1)[1].split("</script>", 1)[0]
    return json.loads(block)


def test_every_line_the_course_shows_still_exists():
    missing = []
    try:  # page.html with its parts filled in (src/drill/content/page/), like the build reads it
        from drill.content.build import page_source
    except ImportError:  # before the page was split into parts
        page_source = None
    for a in _anchors():
        if a["file"] == "src/drill/content/page.html" and page_source:
            text = page_source()
        else:
            text = (ROOT / a["file"]).read_text(encoding="utf-8")
        if a["find"] not in text:
            missing.append(f'lesson "{a["lesson"]}": {a["file"]} no longer has {a["find"]!r}')
    assert not missing, "The course shows code that changed. Update the lesson's snippet and anchor, then republish:\n" + "\n".join(missing)


def test_anchors_name_real_lessons_and_cover_every_code_lesson():
    course = _course()
    lesson_ids = set(re.findall(r'^\{ id: "([a-z-]+)"', course, re.M))
    assert len(lesson_ids) >= 16
    named = {a["lesson"] for a in _anchors()}
    assert named <= lesson_ids, f"anchors name lessons that don't exist: {named - lesson_ids}"
    code_lessons = set(re.findall(r'^\{ id: "([a-z-]+)", part: \d+, title:', course, re.M))
    assert code_lessons <= named, f"lessons that show code but have no anchor: {code_lessons - named}"


def test_the_course_script_parses(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    course = _course()
    script = course[course.index("<script>\n(() => {") + len("<script>"):]
    script = script[: script.index("</script>")]
    (tmp_path / "course.js").write_text(script)
    result = subprocess.run([node, "--check", str(tmp_path / "course.js")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-800:]
