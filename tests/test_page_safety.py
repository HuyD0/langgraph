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
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from drill.content.build import PAGE_PARTS, page_source
from drill.server.api import create_app
from drill.server.bank import Bank
from drill.server.router import ModelRouter
from drill.server.store import DocStore
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
    page, study = page_source(), (PAGE_PARTS / "study-list.js").read_text(encoding="utf-8")
    helpers = "\n".join(_line(page, s) for s in ("const esc = ", "const inline = ", "const md = "))
    helpers += "\n" + _line(study, "const emph = ") + "\n" + extra
    script = helpers + "\nconsole.log(JSON.stringify((() => { " + js + " })()));"
    out = subprocess.run([node, "-e", script], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout)


def test_study_item_ids_are_escaped_before_they_reach_the_page():
    study = (PAGE_PARTS / "study-list.js").read_text(encoding="utf-8")
    assert "${it.id}" not in study, "an id from the account goes into innerHTML raw: wrap it in esc()"
    assert 'data-snote="${esc(it.id)}"' in page_source()


def test_ids_read_back_from_the_page_are_looked_up_first():
    page = page_source()
    for attr, fn in [("open", "knownLesson"), ("build", "knownLesson"), ("resultOpen", "knownLesson"),
                     ("resultShare", "knownLesson"), ("practice", "knownProblem"), ("classic", "knownProblem")]:
        assert re.search(rf"{fn}\(\w+\.dataset\.{attr}\)", page), f"dataset.{attr} is used without {fn}()"
    assert re.search(r"function openLesson\(id, step\) \{\n\s+if \(!id\) return;", page)
    assert re.search(r"function openPractice\(pid, from\) \{\n\s+if \(!pid\) return;", page)
    assert "knownLesson" not in (PAGE_PARTS / "share.js").read_text(encoding="utf-8"), "one copy, in page.html"


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
        assert "${LEARNER()}" in (PAGE_PARTS / part).read_text(encoding="utf-8") and "${LEARNER}" not in (PAGE_PARTS / part).read_text(encoding="utf-8")
    assert "${LEARNER}" not in page


def test_the_build_step_recovers_after_a_practice_lesson():
    practice = (PAGE_PARTS / "practice.js").read_text(encoding="utf-8")
    assert '$("paneBuild").classList.remove("flowing")' in practice


def test_steps_are_named_from_the_lesson_not_a_literal():
    page = page_source()
    assert '"Skip to " + stepNames(cur.id)[2]' in page and '"Next: " + stepNames(cur.id)[2]' in page
    assert 'const names = ["Check", stepNames(id)[2], "Explain"];' in (PAGE_PARTS / "share.js").read_text(encoding="utf-8")


def test_the_notebook_drawer_is_a_real_dialog_with_a_tab_list():
    page = page_source()
    for name in ("gloss", "results", "speed", "settings"):
        assert f'id="nb-{name}" class="pane" role="tabpanel" aria-labelledby="nbtab-{name}"' in page
        assert f'id="nbtab-{name}" data-nb="{name}"' in page
    notebook = (PAGE_PARTS / "notebook.js").read_text(encoding="utf-8")
    assert 'if (e.key !== "Tab") return;' in notebook and "ArrowRight: i + 1" in notebook


def test_motion_is_for_everyone_with_no_switch_left_behind():
    """The owner's choice (2026-10-15): effects play for everyone. No rule may gate on a Motion
    switch that no longer exists, and nothing follows the device's reduced-motion setting, so a
    reader never builds for a switch that isn't there."""
    page = page_source()
    assert "data-motion" not in page, "a rule or comment still refers to the retired Motion switch"
    assert "prefers-reduced-motion" not in page


def test_a_sleeping_app_is_named_as_such():
    backends = (PAGE_PARTS / "backends.js").read_text(encoding="utf-8")
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


# The note under each "your own use case" form. Its four sentences, from the strongest promise down:
ONLY_YOU = "Saved only in your own progress. Nobody else can see it."
SIGNED_IN = ("Saved in your own progress. This app doesn't show it to other learners. "
             "The people who run this app, and managers with access to its data, can read it.")
NO_SIGN_IN = "Saved in your own progress. The people who run this app, and managers with access to its data, can read it."
NOT_KNOWN_YET = "Saved in your own progress."
# True only where people sign in: the server then keeps each person's progress apart.
KEPT_APART = "This app doesn't show it to other learners."
# What /api/health can answer. Only the first is a server whose saved work nobody else can read.
OWN_FILE = {"store": "sqlite", "store_fallback": False, "app": False, "team": False}
HEALTH = {
    "own_file": OWN_FILE,
    "behind_a_login": {**OWN_FILE, "app": True},
    "managers_reports_on": {**OWN_FILE, "team": True},
    "at_work": {"store": "lakebase", "store_fallback": False, "app": True, "team": True},
    "shared_database_reports_off": {**OWN_FILE, "store": "lakebase"},
    "postgres_reports_off": {**OWN_FILE, "store": "postgresql"},
    "file_waiting_to_be_sent_up": {**OWN_FILE, "store_fallback": True},
}
# The addresses a browser on the server's own computer opens it at. At any other address the reader may be
# on another device, so the page counts the server as shared.
OWN_ADDRESSES = ("localhost", "127.0.0.1", "[::1]")
OTHER_ADDRESSES = ("sams-computer.local", "192.168.1.20", "0.0.0.0", "tunnel.example.com")
USE_CASE_FORMS = {"use_case_score", "make_a_skill", "use_case_card", "split_requirements", "fit_for_purpose", "total_cost"}
NOTE_LINES = ("const privateLine = ", "let sharedHere = ", "const privateNote = ", "function whereKnown(")


def note_for(health: dict, address: str = "localhost") -> str:
    """The sentence a server that answers `health` must get, on a page opened at `address`."""
    if all(health.get(k) == v for k, v in OWN_FILE.items()) and address in OWN_ADDRESSES:
        return ONLY_YOU
    return SIGNED_IN if health.get("app") is True else NO_SIGN_IN


def test_the_use_case_note_says_nobody_else_only_on_a_plain_no():
    """privateLine() is told whether anyone but the learner can read what is saved here, and whether
    people sign in. Only a plain `false` earns "Nobody else can see it". A plain `true` gets the careful
    sentence, which says the app doesn't show it to other learners only on a plain `true` for sign-in:
    with no sign-in every visitor reads the same progress. Anything else (not known yet, or an answer
    of the wrong kind) promises nothing more, so a slip can only say less."""
    odd = '[null, undefined, 0, 1, "", "true", "false", {}, [], { shared: false }]'
    got = run_js(f"""return {{ no: [privateLine(false), privateLine(false, true), privateLine(false, false)],
      signedIn: privateLine(true, true), noSignIn: [privateLine(true), privateLine(true, false), ...{odd}.map(v => privateLine(true, v))],
      other: {odd}.flatMap(v => [privateLine(v), privateLine(v, true)]) }};""", _line(page_source(), "const privateLine = "))
    assert got["no"] == [ONLY_YOU] * 3
    assert got["signedIn"] == SIGNED_IN
    assert got["noSignIn"] == [NO_SIGN_IN] * 12
    assert got["other"] == [NOT_KNOWN_YET] * 20
    for weaker in (SIGNED_IN, NO_SIGN_IN, NOT_KNOWN_YET):
        assert "Nobody else" not in weaker and "only in your own" not in weaker
    assert SIGNED_IN.replace(KEPT_APART + " ", "") == NO_SIGN_IN, "the same sentence, without the claim that needs a sign-in"
    assert "other learners" not in NO_SIGN_IN + NOT_KNOWN_YET


def test_a_server_counts_as_private_only_when_it_says_all_four():
    """sharedServer() reads /api/health. The people who run a shared database can read it even with
    managers' reports switched off, and a file kept while that database is out of reach is sent up to
    it later (`drill store push`), so both count as shared. So does an answer with a field missing or
    of the wrong kind: when the page cannot tell, it does not make the stronger promise."""
    broken = [{k: v for k, v in OWN_FILE.items() if k != gone} for gone in OWN_FILE]
    broken += [{}, {**OWN_FILE, "app": None}, {**OWN_FILE, "team": 0}, {**OWN_FILE, "store_fallback": "false"},
               {**OWN_FILE, "store": "SQLite"}]
    got = run_js(f"""return {{ named: Object.fromEntries(Object.entries({json.dumps(HEALTH)}).map(([name, h]) => [name, sharedServer(h)])),
      broken: {json.dumps(broken)}.map(h => sharedServer(h)) }};""", _line(page_source(), "const sharedServer = "))
    assert got["named"] == {name: name != "own_file" for name in HEALTH}
    assert got["broken"] == [True] * len(broken)


def test_only_this_computers_own_address_counts_as_opened_here():
    """ownAddress() is given the page's own address (location.hostname). Only the three names a browser
    on the server's own computer uses count. The computer's name on the Wi-Fi, its network address, a
    tunnel, a look-alike name, or no address at all do not: the reader may be on another device, where
    "Nobody else can see it" is not true with no sign-in."""
    look_alikes = ["localhost.", "localhost.example.com", "example.localhost", "notlocalhost", "LOCALHOST", " localhost",
                   "127.0.0.1.example.com", "127.0.0.2", "127.0.0.1:8787", "::1", "[::1]:8787", "[::]", "[fe80::1]"]
    got = run_js(f"""return {{ own: {json.dumps(list(OWN_ADDRESSES))}.map(ownAddress),
      other: {json.dumps(list(OTHER_ADDRESSES) + look_alikes)}.map(ownAddress),
      odd: [undefined, null, "", 0, 1, true, {{}}, [], ["localhost"]].map(ownAddress) }};""",
                 _line((PAGE_PARTS / "backends.js").read_text(encoding="utf-8"), "const ownAddress = "))
    assert got["own"] == [True] * len(OWN_ADDRESSES)
    assert got["other"] == [False] * (len(OTHER_ADDRESSES) + len(look_alikes))
    assert got["odd"] == [False] * 9


def test_the_use_case_note_is_written_in_one_place_and_follows_the_backend():
    """Read as plain text, so these also run where node is not installed."""
    page, backends = page_source(), (PAGE_PARTS / "backends.js").read_text(encoding="utf-8")
    line = _line(page, "const privateLine = ")
    assert page.count("Nobody else can see it") == 1
    assert 'shared === false ? "Saved only in your own progress. Nobody else can see it." :' in line
    assert page.count("This app doesn't show it to other learners") == 1
    assert '${signIn === true ? "This app doesn\'t show it to other learners. " : ""}' in line, "said only where people sign in"
    assert page.count('class="meta mine-private"') == 1, "every form's note comes from privateNote()"
    assert "privateLine(sharedHere, signInHere)" in _line(page, "const privateNote = ")
    assert _line(page, "let sharedHere = ").startswith("let sharedHere = null, signInHere = null;"), "nothing is known before the backend answers"
    known = _line(page, "function whereKnown(")
    assert page.count("sharedHere = ") == 2 and "sharedHere = backend.shared;" in known, "set in one place only: whereKnown()"
    assert page.count("signInHere = ") == 2 and "signInHere = backend.signIn;" in known, "set in one place only: whereKnown()"
    assert "note.outerHTML = privateNote()" in known, "a note already on the screen is put right"
    boot = page.split("const backend = window.claude ?")[1].split("if (db && user)")[0]
    assert re.search(r"if \(!backend\) return;\n\s*whereKnown\(backend\);", boot), "told as soon as the backend answers"
    server = _line(backends, "const sharedServer = ")
    assert server.startswith("const sharedServer = health => !(")
    for needed in ('health.store === "sqlite"', "health.store_fallback === false", "health.app === false", "health.team === false"):
        assert needed in server, f"the server is private only when {needed}"
    assert _line(backends, "const ownAddress = ") == 'const ownAddress = host => host === "localhost" || host === "127.0.0.1" || host === "[::1]";'
    assert "shared: sharedServer(health) || !ownAddress(location.hostname), signIn: health.app === true," in backends, \
        "a server is private only when it says so and the page was opened at its computer's own address"
    assert backends.count("ownAddress(") == 1 and backends.count("sharedServer(") == 1, "each is asked once, in localBackend()"
    assert "return { s, db, user, board, shared: false };" in backends
    assert len(re.findall(r", shared: ", backends)) == 2, "each backend says it once"
    assert len(re.findall(r"\bsignIn: ", backends)) == 1, "only a server can say people sign in, and it says it once"


def test_every_use_case_form_carries_the_note():
    page = page_source()
    panels = re.split(r"\n  (\w+): \(\) =>", page.split("const MINE_PANELS = {", 1)[1].split("\n};", 1)[0])
    noted = {name for name, body in zip(panels[1::2], panels[2::2]) if body.count("${privateNote()}") == 1}
    assert noted >= USE_CASE_FORMS, f"a form lost its note: {sorted(USE_CASE_FORMS - noted)}"
    assert page.count("${privateNote()}") == len(noted)


def run_backends(js: str, extra: str = "") -> object:
    """Run the real page/backends.js in node, with the browser's `location`, `fetch` and claude.ai's
    `claude.use` stood in, then `extra` (more of the page's own code) and `js` (which may wait for
    things). `answer` is what fetch gives back. The page is opened at the computer's own address
    (`localhost`) until a test sets `location.hostname` to another one."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    script = "\n".join([
        "(async () => {",
        'const location = { protocol: "http:", hostname: "localhost" }, document = { addEventListener() {}, hidden: false };',
        'let answer = async () => { throw new Error("no server"); };',
        "const fetch = (...args) => answer(...args), claude = { use: async name => ({ name }) };",
        (PAGE_PARTS / "backends.js").read_text(encoding="utf-8"),
        extra,
        js,
        "})().then(value => console.log(JSON.stringify(value)), e => { console.error(e); process.exit(1); });",
    ])
    # From a file, not `node -e`: the script is longer than a command line may be on some systems.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "backends_test.js"
        path.write_text(script, encoding="utf-8")
        out = subprocess.run([node, str(path)], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout)


def note_code() -> str:
    """The page's own lines that write the note, for run_backends(): the icon is stood in, and `drawn`
    holds the notes already on the screen."""
    page = page_source()
    return ('const ic = () => "<svg></svg>", drawn = [];\n'
            'document.querySelectorAll = sel => sel === ".mine-private" ? drawn : [];\n'
            + "\n".join(_line(page, s) for s in NOTE_LINES))


def said(note: str) -> str:
    """The sentence inside a note's HTML."""
    assert note.startswith('<p class="meta mine-private"><svg></svg> ') and note.endswith("</p>"), note
    return note.split("</svg> ", 1)[1][: -len("</p>")]


def notes_for(answers: dict, address: str = "localhost") -> dict:
    """The sentence the page writes for each /api/health answer when it is opened at `address`, by the
    page's own code from end to end: localBackend() reads the answer and the address, whereKnown() is
    told, privateNote() writes the note."""
    got = run_backends(f"""const notes = {{}}; location.hostname = {json.dumps(address)};
      for (const [name, health] of Object.entries({json.dumps(answers)})) {{
        answer = async () => ({{ ok: true, json: async () => health }});
        whereKnown(await localBackend()); notes[name] = privateNote();
      }}
      return notes;""", note_code())
    return {name: said(note) for name, note in got.items()}


def test_each_backend_says_whether_other_people_can_read_what_is_saved():
    """The real localBackend() and claudeBackend(). A server that cannot be reached, or does not answer
    as drill-server does, gives no backend at all: boot stops there, so the note stays at the sentence
    that promises nothing. A server that answers is `shared` unless its answer says all four, and it
    says people sign in (`signIn`) only when its answer says so with a plain `true`."""
    got = run_backends(f"""
      const says = async json => {{ answer = async () => ({{ ok: true, json }}); const b = await localBackend(); return b && [b.shared, b.signIn]; }};
      const out = {{ servers: {{}}, oddSignIn: [] }};
      out.offline = await localBackend();
      answer = async () => ({{ ok: false, json: async () => ({{ ok: true }}) }}); out.error = await localBackend();
      out.asleep = await says(async () => {{ throw new Error("a web page, not JSON"); }});
      out.empty = await says(async () => null);
      out.notOurs = await says(async () => ({{ ok: false, store: "sqlite", store_fallback: false, app: false, team: false }}));
      for (const [name, health] of Object.entries({json.dumps(HEALTH)})) out.servers[name] = await says(async () => ({{ ok: true, user: "local", ...health }}));
      for (const app of [1, "true", "yes", {{}}, null]) out.oddSignIn.push(await says(async () => ({{ ok: true, user: "local", ...{json.dumps(OWN_FILE)}, app }})));
      out.older = await says(async () => ({{ ok: true, user: "local", app: false, team: false }}));
      out.claude = (await claudeBackend()).shared;
      out.ownAddresses = []; out.otherAddresses = [];
      for (const host of {json.dumps(list(OWN_ADDRESSES))}) {{ location.hostname = host; out.ownAddresses.push(await says(async () => ({{ ok: true, user: "local", ...{json.dumps(OWN_FILE)} }}))); }}
      for (const host of {json.dumps(list(OTHER_ADDRESSES) + [None])}) {{
        location.hostname = host === null ? undefined : host;
        out.otherAddresses.push(await says(async () => ({{ ok: true, user: "local", ...{json.dumps(OWN_FILE)} }})));
      }}
      out.claudeElsewhere = (await claudeBackend()).shared; location.hostname = "localhost";
      location.protocol = "file:"; out.file = await says(async () => ({{ ok: true, ...{json.dumps(OWN_FILE)} }}));
      return out;""")
    assert [got[k] for k in ("offline", "error", "asleep", "empty", "notOurs", "file")] == [None] * 6
    assert got["servers"] == {name: [name != "own_file", health["app"] is True] for name, health in HEALTH.items()}
    assert got["oddSignIn"] == [[True, False]] * 5, "sign-in said any other way: shared, and no word about other learners"
    assert got["older"] == [True, False], "a server that does not say where it saves counts as shared"
    assert got["claude"] is False, "on claude.ai each person's progress is theirs alone"
    assert got["ownAddresses"] == [[False, False]] * len(OWN_ADDRESSES), "its own file, opened at the computer's own address"
    assert got["otherAddresses"] == [[True, False]] * (len(OTHER_ADDRESSES) + 1), \
        "the same server opened at any other address, or with no address to read: shared, and no word about other learners"
    assert got["claudeElsewhere"] is False, "claude.ai's answer does not depend on the page's address"


@pytest.mark.parametrize("address", ["localhost", "sams-computer.local"])
@pytest.mark.parametrize("server", sorted(HEALTH))
def test_a_use_case_form_drawn_before_the_server_answers_gets_the_true_note(server, address):
    """A lesson can open on its Build step before /api/health has answered (Home is drawn at once, and a
    lesson opens at the step it was left on). The form drawn then promises nothing, and its note is put
    right when the answer arrives, without drawing the form again. Opened from another device
    (`sams-computer.local`), no server gets "Nobody else"."""
    health = {"ok": True, "user": "local", **HEALTH[server]}
    got = run_backends(f"""location.hostname = {json.dumps(address)}; drawn.push({{ outerHTML: privateNote() }});
      const before = drawn[0].outerHTML;
      answer = async () => ({{ ok: true, json: async () => ({json.dumps(health)}) }});
      whereKnown(await localBackend());
      return {{ before, after: drawn[0].outerHTML, next: privateNote() }};""", note_code())
    assert said(got["before"]) == NOT_KNOWN_YET
    assert got["after"] == got["next"] and said(got["after"]) == note_for(HEALTH[server], address)
    assert ("Nobody else" in got["after"]) == (server == "own_file" and address == "localhost")
    assert (KEPT_APART in got["after"]) == (server in ("behind_a_login", "at_work"))


def test_a_backend_that_does_not_say_leaves_the_note_promising_nothing():
    got = run_backends("""drawn.push({ outerHTML: privateNote() }); whereKnown({ s: null, db: {}, user: {} });
      const silent = [drawn[0].outerHTML, privateNote()];
      whereKnown({ signIn: true });
      return [...silent, privateNote()];""", note_code())
    assert [said(note) for note in got] == [NOT_KNOWN_YET] * 3


def test_the_note_follows_what_the_server_itself_answers(tmp_path, monkeypatch):
    """From drill-server's own /api/health answer to the sentence on the page, with nothing stood in
    between: the server run in this process, then the page's own code run by node."""
    for name in ("DATABRICKS_APP_NAME", "DRILL_TRUST_USER_HEADER", "DRILL_TEAM_SUMMARIES"):
        monkeypatch.delenv(name, raising=False)
    store = DocStore(f"sqlite:///{tmp_path / 'drill.db'}")
    client = TestClient(create_app(store=store, router=ModelRouter(None, None, store), bank=Bank.load(), with_mcp=False))

    def health(env: dict | None = None, kind: str = "", fallback: bool = False) -> dict:
        with monkeypatch.context() as m:
            for name, value in (env or {}).items():
                m.setenv(name, value)
            if kind:  # a shared database, without connecting to one
                m.setattr(DocStore, "kind", property(lambda self: kind))
            m.setattr(store, "fallback", fallback)
            return client.get("/api/health").json()

    answers = {
        "own_file": health(),
        "managers_reports_on": health({"DRILL_TEAM_SUMMARIES": "1"}),
        "a_login_in_front": health({"DRILL_TRUST_USER_HEADER": "1"}),
        "a_databricks_app": health({"DATABRICKS_APP_NAME": "daily-drill"}, kind="lakebase"),
        "shared_database": health(kind="lakebase"),
        "shared_database_reports_off": health({"DRILL_TEAM_SUMMARIES": "0"}, kind="lakebase"),
        "postgres_reports_off": health({"DRILL_TEAM_SUMMARIES": "0"}, kind="postgresql"),
        "file_waiting_to_be_sent_up": health(fallback=True),
    }
    assert {k: answers["own_file"][k] for k in OWN_FILE} == OWN_FILE
    assert answers["shared_database_reports_off"]["team"] is False and answers["file_waiting_to_be_sent_up"]["team"] is False
    signs_in = {"a_login_in_front", "a_databricks_app"}
    assert {name for name, answer in answers.items() if answer["app"]} == signs_in
    assert notes_for(answers) == {name: ONLY_YOU if name == "own_file" else SIGNED_IN if name in signs_in else NO_SIGN_IN
                                  for name in answers}


SAM, KIM = {"x-forwarded-email": "sam@example.com"}, {"x-forwarded-email": "kim@example.com"}


@pytest.mark.parametrize("env, sam, kim", [
    ({"DRILL_TEAM_SUMMARIES": "1"}, {}, {}),  # nobody signs in, so no request says who it is from
    ({"DRILL_TRUST_USER_HEADER": "1"}, SAM, KIM),
    ({"DRILL_TRUST_USER_HEADER": "1", "DRILL_TEAM_SUMMARIES": "1"}, SAM, KIM),
], ids=["reports_on_no_sign_in", "sign_in", "sign_in_and_reports_on"])
def test_the_note_says_other_learners_cannot_see_it_only_where_the_server_keeps_them_apart(env, sam, kim, tmp_path, monkeypatch):
    """Two visitors to one server. Where people sign in, the second cannot load what the first wrote,
    and the note says so. With no sign-in every visitor is the same person to the server (owner_for
    in api.py): the second loads the first one's use case, so the note must not say the app keeps
    it from other learners."""
    for name in ("DATABRICKS_APP_NAME", "DRILL_TRUST_USER_HEADER", "DRILL_TEAM_SUMMARIES", "DRILL_USER_HEADER"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    store = DocStore(f"sqlite:///{tmp_path / 'drill.db'}")
    client = TestClient(create_app(store=store, router=ModelRouter(None, None, store), bank=Bank.load(), with_mcp=False))
    sams = client.get("/api/health", headers=sam).json()
    client.put(f"/api/docs/data/users/{sams['user']}/progress", headers=sam, json={"mine": {"card": {"problem": "Sam's own use case"}}})
    kims = client.get("/api/health", headers=kim).json()
    # Kim's page loads her own progress; she could also ask for Sam's document by its path.
    loaded = [client.get(f"/api/docs/data/users/{who['user']}/progress", headers=kim).json()["data"] for who in (kims, sams)]
    kim_can_read_it = "Sam's own use case" in json.dumps(loaded)
    note = notes_for({"kim": kims})["kim"]
    signs_in = "DRILL_TRUST_USER_HEADER" in env
    assert kims["app"] is signs_in and kim_can_read_it is (not signs_in)
    assert (KEPT_APART in note) is signs_in, "the note says the app keeps it from other learners exactly where the server does"
    assert note == (SIGNED_IN if signs_in else NO_SIGN_IN)


@pytest.mark.parametrize("address", OTHER_ADDRESSES)
def test_no_server_opened_from_another_device_says_nobody_else(address):
    """Whatever the server answers, a page opened at any address but the computer's own never makes the
    stronger promise. The other sentences do not depend on the address."""
    answers = {name: {"ok": True, "user": "local", **health} for name, health in HEALTH.items()}
    notes = notes_for(answers, address)
    assert notes == {name: note_for(health, address) for name, health in HEALTH.items()}
    assert ONLY_YOU not in notes.values() and notes["own_file"] == NO_SIGN_IN
    at_the_computer = notes_for(answers)
    assert at_the_computer["own_file"] == ONLY_YOU
    assert {name: note for name, note in notes.items() if name != "own_file"} == \
        {name: note for name, note in at_the_computer.items() if name != "own_file"}


def test_a_visitor_from_another_device_is_not_told_nobody_else_can_see_it(tmp_path, monkeypatch):
    """A server on your own computer with no sign-in. By default other devices on the same network can
    open it (docs/SERVER.md, "From your phone"), and every visitor is the same person to the server. So
    the second visitor loads what the first wrote, and the page that visitor opened, at the computer's
    name on the network, must not say "Nobody else can see it". The page cannot see which addresses the
    server listens on, so at the computer's own address the sentence stays (docs/PAGE.md says so)."""
    for name in ("DATABRICKS_APP_NAME", "DRILL_TRUST_USER_HEADER", "DRILL_TEAM_SUMMARIES", "DRILL_USER_HEADER"):
        monkeypatch.delenv(name, raising=False)
    store = DocStore(f"sqlite:///{tmp_path / 'drill.db'}")
    client = TestClient(create_app(store=store, router=ModelRouter(None, None, store), bank=Bank.load(), with_mcp=False))
    sams = client.get("/api/health").json()
    assert {k: sams[k] for k in OWN_FILE} == OWN_FILE
    client.put(f"/api/docs/data/users/{sams['user']}/progress", json={"mine": {"card": {"problem": "Sam's own use case"}}})
    kims = client.get("/api/health").json()  # a second device: nothing in the request says it is someone else
    loaded = client.get(f"/api/docs/data/users/{kims['user']}/progress").json()["data"]
    assert "Sam's own use case" in json.dumps(loaded), "with no sign-in the second visitor reads the first one's use case"
    for address in OTHER_ADDRESSES:
        note = notes_for({"kim": kims}, address)["kim"]
        assert note == NO_SIGN_IN and "Nobody else" not in note and KEPT_APART not in note, address
    assert notes_for({"sam": sams})["sam"] == ONLY_YOU, "at the computer itself the sentence stays"

