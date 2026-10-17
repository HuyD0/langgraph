"""Guards from the audit of page.html and its parts: text that arrives from an account or the page
itself goes through esc() or the app's own lists before it is used, bold may hold an italic word,
the tutor's framing sentence is the server's and names no one's job, and a few screens keep the
fixes the walkthrough asked for. The pure helpers are run by node, lifted from the source by their
first line, so the checks are on the real code."""

from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from drill.content.build import PAGE_PARTS, page_source
from drill.server.tutor import LEARNER as SERVER_LEARNER


def _line(src: str, start: str) -> str:
    for line in src.splitlines():
        if line.startswith(start):
            return line
    raise AssertionError(f"no line starts with {start!r}")


def run_js(js: str, extra: str = "") -> object:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    page, study = page_source(), (PAGE_PARTS / "study-list.js").read_text()
    helpers = "\n".join(_line(page, s) for s in ("const esc = ", "const inline = ", "const md = "))
    helpers += "\n" + _line(study, "const emph = ") + "\n" + extra
    script = helpers + "\nconsole.log(JSON.stringify((() => { " + js + " })()));"
    out = subprocess.run([node, "-e", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout)


def test_study_item_ids_are_escaped_before_they_reach_the_page():
    study = (PAGE_PARTS / "study-list.js").read_text()
    assert "${it.id}" not in study, "an id from the account goes into innerHTML raw: wrap it in esc()"
    assert 'data-snote="${esc(it.id)}"' in page_source()


def test_ids_read_back_from_the_page_are_looked_up_first():
    page = page_source()
    for attr, fn in [("open", "knownLesson"), ("build", "knownLesson"), ("resultOpen", "knownLesson"),
                     ("resultShare", "knownLesson"), ("practice", "knownProblem"), ("classic", "knownProblem")]:
        assert re.search(rf"{fn}\(\w+\.dataset\.{attr}\)", page), f"dataset.{attr} is used without {fn}()"
    assert re.search(r"function openLesson\(id, step\) \{\n\s+if \(!id\) return;", page)
    assert re.search(r"function openPractice\(pid, from\) \{\n\s+if \(!pid\) return;", page)
    assert "knownLesson" not in (PAGE_PARTS / "share.js").read_text(), "one copy, in page.html"


def test_the_highlighters_escape_every_piece_they_colour():
    page = page_source()
    for fn in ("hlPython", "hlInfra"):
        body = page.split(f"function {fn}(src) {{", 1)[1].split("\n}\n", 1)[0]
        assert not re.search(r"\$\{(num|word|m\[1\]|lock\[1\])\}", body), f"{fn} pastes a match raw"
        assert "out += word;" not in body
    assert "out.replace(/<[^>]+>/g" not in page, "test the source text, not the HTML built so far"
    out = run_js('return [hlPython("x = 12 if a else b"), hlInfra("resource \\"a\\" {\\n  n = 1\\n}")];',
                 extra=_js_highlighters())
    assert out[0] == 'x = <span class="n">12</span> <span class="k">if</span> a <span class="k">else</span> b'
    assert out[1] == '<span class="k">resource</span> <span class="s">&quot;a&quot;</span> {\n  <span class="key">n</span> = <span class="n">1</span>\n}'


def _js_highlighters() -> str:
    page = page_source()
    start = page.index("const PY_KW = ")
    return page[start:page.index("// Colour every read-only code box", start)]


def test_bold_can_hold_an_italic_word():
    assert run_js('return emph("The **big question: can you *prove* it?** Show me.");') == \
        "The <b>big question: can you <i>prove</i> it?</b> Show me."
    assert run_js('return md("**a** and **b**");') == "<b>a</b> and <b>b</b>"


def test_the_tutor_framing_is_the_servers_and_names_no_job():
    page = page_source()
    definition = re.search(r"const LEARNER = .*?;\n", page, re.S).group(0)
    assert "Spacelift" not in definition and "at work" not in definition
    said = run_js('const out = [LEARNER()]; progress.focus = "platform"; out.push(LEARNER()); progress.focus = "both"; out.push(LEARNER()); return out;',
                  extra='let progress = { focus: "ai" };\n' + definition)
    assert said[0] == SERVER_LEARNER
    assert said[1] == said[2] == SERVER_LEARNER + " They are also practising the Platform track (Azure Databricks managed with Terraform)."
    for part in ("ask.js", "study-list.js"):
        assert "${LEARNER()}" in (PAGE_PARTS / part).read_text() and "${LEARNER}" not in (PAGE_PARTS / part).read_text()
    assert "${LEARNER}" not in page


def test_the_build_step_recovers_after_a_practice_lesson():
    practice = (PAGE_PARTS / "practice.js").read_text()
    assert '$("paneBuild").classList.remove("flowing")' in practice


def test_steps_are_named_from_the_lesson_not_a_literal():
    page = page_source()
    assert '"Skip to " + stepNames(cur.id)[2]' in page and '"Next: " + stepNames(cur.id)[2]' in page
    assert 'const names = ["Check", stepNames(id)[2], "Explain"];' in (PAGE_PARTS / "share.js").read_text()


def test_the_notebook_drawer_is_a_real_dialog_with_a_tab_list():
    page = page_source()
    for name in ("gloss", "results", "speed", "settings"):
        assert f'id="nb-{name}" class="pane" role="tabpanel" aria-labelledby="nbtab-{name}"' in page
        assert f'id="nbtab-{name}" data-nb="{name}"' in page
    notebook = (PAGE_PARTS / "notebook.js").read_text()
    assert 'if (e.key !== "Tab") return;' in notebook and "ArrowRight: i + 1" in notebook


def test_motion_is_for_everyone_with_no_switch_left_behind():
    """The owner's choice (2026-10-15): effects play for everyone. No rule may gate on a Motion
    switch that no longer exists, and nothing follows the device's reduced-motion setting, so a
    reader never builds for a switch that isn't there."""
    page = page_source()
    assert "data-motion" not in page, "a rule or comment still refers to the retired Motion switch"
    assert "prefers-reduced-motion" not in page


def test_a_sleeping_app_is_named_as_such():
    backends = (PAGE_PARTS / "backends.js").read_text()
    assert "The app has gone to sleep. Reload in a minute, or ask whoever runs it to start it." in backends
    assert "res.json()" not in backends.split("const jsonOf", 1)[1].split("\n", 1)[1], "every body read goes through jsonOf"
    assert 'fetch("/api/me"' in page_source()


def test_learners_at_work_are_told_their_manager_sees_their_progress():
    """docs/DATABRICKS_APP.md promises learners are told up front. /api/health says team mode is on;
    the page then shows the line on the first-visit card and in Settings, and nowhere else."""
    page = page_source()
    assert "team: !!health.team" in page and 'TEAM_LINE = "At work, your manager can see your progress' in page
    assert "${teamOn ? `<li><b>Who sees it:</b>" in page and 'id="teamSetting" hidden' in page
    boot = page.split("const backend = window.claude ?")[1].split("if (db && user)")[0]
    assert "if (backend.team) { teamOn = true;" in boot
