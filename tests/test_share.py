"""The result you share after a lesson (page/share.js): what gets copied, and what a screen reader
says. Both are plain functions of the result, so node runs them straight from the part file."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from drill.content.build import PAGE_PARTS, page_source


def run_share(js: str) -> object:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    src = (PAGE_PARTS / "share.js").read_text()
    script = src + "\nconsole.log(JSON.stringify((() => { " + js + " })()));"
    out = subprocess.run([node, "-e", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout)


def test_the_copied_result_shows_marks_not_answers():
    r = {"no": "2.4", "day": 12, "spark": False, "gate": False, "streak": 5,
         "rows": [["Check", ["sign", "sign", "knot"]], ["Build", None], ["Explain", ["sign", "curtain"]]]}
    text = run_share(f"return shareText({json.dumps(r)});")
    assert text.splitlines() == ["Daily Drill 2.4 · Day 12", "Check ✌️✌️🪢", "Build skipped", "Explain ✌️🌫️", "📿 5-day streak"]
    words = run_share(f"return resultWords({json.dumps(r)});")
    assert words.startswith("Lesson 2.4, day 12. Check: 2 of 3 on your own, 1 of 3 with a clue or another go. Build: skipped.")
    assert words.endswith("Explain: 1 of 2 on your own, 1 of 2 answer shown. 5-day streak.")


def test_a_flawless_finish_that_ends_a_module_says_so():
    r = {"no": "P1.3", "day": 40, "spark": True, "gate": True, "streak": 1,
         "rows": [["Check", ["sign"]], ["Practice", ["sign"]], ["Explain", ["sign", "sign"]]]}
    text = run_share(f"return shareText({json.dumps(r)});")
    assert text.splitlines()[0] == "Daily Drill P1.3 · Day 40 ⚡ ⛩️" and "streak" not in text, "a one-day streak isn't news"
    assert run_share(f"return resultWords({json.dumps(r)});").endswith("Every step on your own. Module finished.")


def test_every_mark_has_a_symbol_words_and_an_emoji_twin():
    page = page_source()
    marks = run_share("return { marks: MARKS, words: MARK_WORDS, emoji: SHARE_MARKS };")
    for m in marks["marks"] + ["spark", "gate"]:
        assert f'<symbol id="i-{m}"' in page, f"the sprite needs i-{m}"
        assert marks["emoji"].get(m), f"{m} needs an emoji for the copied text"
    assert set(marks["words"]) == set(marks["marks"])
    assert re.search(r"/\*INCLUDE page/share\.js\*/", page) is None, "page_source fills the part in"


def test_a_step_done_before_results_began_says_so_instead_of_hiding_the_card():
    r = {"no": "1.1", "day": 3, "spark": False, "gate": False, "streak": 1,
         "rows": [["Check", "earlier"], ["Build", "earlier"], ["Explain", ["sign", "knot"]]]}
    assert run_share(f"return shareText({json.dumps(r)});").splitlines()[1:] == ["Check done", "Build done", "Explain ✌️🪢"]
    assert "Check: done earlier. Build: done earlier." in run_share(f"return resultWords({json.dumps(r)});")
