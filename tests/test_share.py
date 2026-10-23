"""The result you share after a lesson (page/share.js): what gets copied, and what a screen reader
says. Both are plain functions of the result, so node runs them straight from the part file."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from drill.content.build import PAGE_PARTS, page_source


def run_share(js: str, extra: str = "") -> object:
    """Run share.js in node, then `js`; `extra` is script put in front of it (stubs for the page's globals)."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    src = (PAGE_PARTS / "share.js").read_text(encoding="utf-8")
    script = extra + "\n" + src + "\nconsole.log(JSON.stringify((() => { " + js + " })()));"
    out = subprocess.run([node, "-e", script], capture_output=True, text=True, encoding="utf-8")
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


# The Notebook's Results tab: the page's globals it leans on, stubbed. dayKey and today are the
# page's own lines (lifted from page.html), so the date words are tested on the real formatter.
def _page_line(start: str) -> str:
    for line in page_source().splitlines():
        if line.startswith(start):
            return line
    raise AssertionError(f"no line starts with {start!r}")


def _results_stubs(lessons: dict) -> str:
    return "\n".join([
        _page_line("const dayKey = "), _page_line("const today = "),
        "const boxes = {}; const $ = id => boxes[id] || (boxes[id] = { innerHTML: '' });",
        "const ALL_LESSONS = ['a', 'b', 'c'];",
        "const LESSONS = { a: { title: 'Alpha' }, b: { title: 'Beta <i>' }, c: { title: 'Gamma' } };",
        f"const progress = {{ lessons: {json.dumps(lessons)} }};",
        "const lp = id => progress.lessons[id] || (progress.lessons[id] = {});",
        "const lessonNo = id => ({ a: '1.1', b: '1.2', c: '1.3' })[id];",
        "const stepNames = id => ['Learn', 'Check', id === 'b' ? 'Practice' : 'Build', 'Explain'];",
        "const streak = () => 4; const stickerSvg = () => '<svg></svg>';",
        "const ic = n => `<i>${n}</i>`; const esc = s => String(s).replace(/</g, '&lt;');",
    ])


def test_the_results_tab_scores_only_the_steps_that_have_marks():
    r = {"rows": [["Check", ["sign", "knot"]], ["Build", None], ["Explain", ["sign", "sign", "curtain"]]]}
    assert run_share(f"return resultScore({json.dumps(r)});") == "3 of 5 on your own"
    r = {"rows": [["Check", "earlier"], ["Build", "earlier"], ["Explain", None]]}
    assert run_share(f"return resultScore({json.dumps(r)});") == "Done before results began"


def test_the_results_tab_says_when_a_lesson_was_finished_in_plain_words():
    out = run_share("const y = new Date(); y.setDate(y.getDate() - 1);"
                    "return [whenFinished({ day: 3, date: today() }), whenFinished({ day: 3, date: dayKey(y) }),"
                    " whenFinished({ day: 3, date: null }), whenFinished({ day: 3, date: '2026-01-05' })];",
                    extra=_results_stubs({}))
    assert out[:3] == ["Today", "Yesterday", "Day 3"]
    assert "Jan" in out[3] and "5" in out[3], "an older day shows its date"


def test_the_results_tab_lists_finished_lessons_newest_first_with_a_summary():
    lessons = {
        "a": {"first": {"check": ["sign", "knot"], "day": 1, "streak": 1}},  # no date: a result from before dates were kept
        "b": {"first": {"check": ["sign"], "build": ["sign", "sign"], "explain": ["sign"], "day": 2, "streak": 2, "gate": True}},
        "c": {"done": True},
    }
    html = run_share("renderResults(); return $('resultsBody').innerHTML;", extra=_results_stubs(lessons))
    assert "<b>2</b>lessons" in html and "<b>1</b>spark" in html and "<b>4</b>day streak" in html
    assert html.index('data-result-open="b"') < html.index('data-result-open="a"'), "newest first"
    assert 'data-result-open="c"' not in html, "a lesson with no first-time marks has no result"
    assert "Day 2 · 4 of 4 on your own · module done" in html and "Day 1 · 1 of 2 on your own" in html
    assert "Beta &lt;i>" in html, "titles are escaped"
    assert "Practice:" in run_share("return resultWords(resultOf('b'));", extra=_results_stubs(lessons))
    empty = run_share("renderResults(); return $('resultsBody').innerHTML;", extra=_results_stubs({}))
    assert "Finish a lesson and its result shows here" in empty


def test_an_old_single_answer_check_becomes_a_checks_record():
    """A learner who answered question 1 before Check grew to several questions is shown question 2
    (if they were right) or question 1 again (if not), never a blank slate."""
    page = page_source()
    fn = "function checkState(id) {" + page.split("function checkState(id) {", 1)[1].split("\n}\n", 1)[0] + "\n}"
    stubs = ("const LESSONS = { x: { check: ['q', ['a', 'b', 'c'], 2] } }; const checkQs = () => [1, 2, 3];"
             "let progress; const lp = id => progress.lessons[id];\n" + fn)
    run = lambda checked: run_share(f"progress = {{ lessons: {{ x: {{ checked: {json.dumps(checked)} }} }} }}; return checkState('x');", extra=stubs)
    assert run(2) == {"at": 1, "solved": [True], "tried": [[]], "help": [], "marks": []}
    assert run(0) == {"at": 0, "solved": [False], "tried": [[0]], "help": [], "marks": []}
    assert run(None) == {"at": 0, "solved": [False], "tried": [[]], "help": [], "marks": []}
