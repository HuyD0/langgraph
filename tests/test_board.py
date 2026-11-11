"""The leaderboard (page/board.js and /api/board): points from the marks, the grade league, last
week's seals, the daily trial, and the server keeping everyone's rows. The page's scoring is plain
functions, so node runs them straight from the part files."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert

from drill.content.build import PAGE_PARTS, page_source
from drill.server import api
from drill.server.api import create_app
from drill.server.bank import Bank
from drill.server.router import ModelRouter
from drill.server.store import DocStore
from drill.server.store import board as board_table


def _page_line(start: str) -> str:
    for line in page_source().splitlines():
        if line.startswith(start):
            return line
    raise AssertionError(f"no line starts with {start!r}")


def run_board(js: str) -> object:
    """Run share.js and board.js in node (with the page's date helpers, grades and esc), then `js`, which may `await`."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    stubs = "\n".join([
        "const document = { addEventListener() {} };",
        "const ic = n => n;",
        _page_line("const dayKey ="), _page_line("const GRADES ="), _page_line("const gradeAt ="), _page_line("const gradeName ="),
        _page_line("const esc ="),
    ])
    script = "\n".join([stubs, (PAGE_PARTS / "share.js").read_text(encoding="utf-8"), (PAGE_PARTS / "board.js").read_text(encoding="utf-8"),
                        "(async () => { " + js + " })().then(out => console.log(JSON.stringify(out)));"])
    # From a file, not `node -e`: the two scripts together are longer than a Windows command line may be.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "board_test.js"
        path.write_text(script, encoding="utf-8")
        out = subprocess.run([node, str(path)], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout)


def lesson(date: str, check=("sign",), build=("sign",), explain=("sign",)) -> dict:
    return {"done": True, "first": {"check": list(check), "build": list(build), "explain": list(explain), "day": 1, "date": date}}


MONDAY = "2026-10-19"


def week(lessons: dict, extra: dict | None = None, monday: str = MONDAY) -> dict:
    return run_board(f"return boardWeek({json.dumps(lessons)}, {json.dumps(extra or {})}, {json.dumps(monday)});")


def test_a_lesson_scores_ten_plus_its_marks_and_hints_cost_nothing():
    w = week({"a": lesson("2026-10-21", check=["sign"], build=["sign", "knot"], explain=["curtain"])})
    assert w["pts"] == 10 + 3 + 3 + 2 + 1
    assert w["tally"] == [2, 1, 1] and w["lessons"] == 1 and w["spark"] == 0
    assert w["days"] == 1


def test_a_lesson_all_on_your_own_is_a_spark_and_skipped_steps_score_nothing():
    w = week({"a": lesson("2026-10-20"), "b": lesson("2026-10-20", build=["knot"])})
    w2 = week({"b": {"first": {"check": ["sign"], "build": None, "explain": ["sign"], "day": 2, "date": "2026-10-20"}}})
    assert w["spark"] == 1, "only the lesson with every step on your own"
    assert w2["pts"] == 10 + 3 + 3 and w2["spark"] == 0, "a skipped step is no spark and no points"


def test_only_a_days_best_three_lessons_count():
    lessons = {f"l{i}": lesson("2026-10-22") for i in range(4)}
    lessons["weak"] = lesson("2026-10-22", check=["curtain"], build=["curtain"], explain=["curtain"])
    w = week(lessons)
    assert w["lessons"] == 3 and w["pts"] == 3 * (10 + 9), "cramming a fourth and fifth lesson adds nothing"
    spread = week({f"l{i}": lesson(d) for i, d in enumerate(["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22"])})
    assert spread["lessons"] == 4 and spread["days"] == 4, "the same four lessons over four days all count"


def test_last_weeks_lessons_count_for_last_week_only():
    lessons = {"old": lesson("2026-10-18"), "new": lesson("2026-10-19")}
    assert week(lessons)["lessons"] == 1
    assert week(lessons, monday="2026-10-12")["lessons"] == 1
    assert week({"before": {"first": {"check": ["sign"]}}})["pts"] == 0, "no date: done before results began"


def test_the_trial_reviews_and_questions_add_up_and_count_as_days():
    extra = {"trial": {"2026-10-20": {"id": "x", "marks": ["sign", "knot", "curtain"]}},
             "reviews": {"2026-10-21": 2}, "asked": {"2026-10-23": 4, "2026-10-12": 9}}
    w = week({}, extra)
    assert w["pts"] == (3 + 2 + 1) + 2 * 2
    assert w["asked"] == 4 and w["reviews"] == 2 and w["days"] == 3
    assert w["tally"] == [1, 1, 1], "the trial's marks join the week's marks"


def rows(*people) -> list:
    """[id, grade, points this week, last week's {days, sure, asked, spark, pts}]."""
    out = []
    for pid, grade, pts, last in people:
        out.append({"id": pid, "name": pid.title(), "row": {
            "grade": grade, "week": {"week": MONDAY, "pts": pts, "tally": [0, 0, 0]},
            "last": {"week": "2026-10-12", "pts": last.get("pts", 0), "days": last.get("days", 0), "tally": [last.get("sure", 0), 0, 0],
                     "asked": last.get("asked", 0), "spark": last.get("spark", 0)}}})
    return out


def test_your_league_is_your_grade_and_equal_points_share_a_place():
    board = rows(("ann", 2, 50, {}), ("bo", 2, 70, {}), ("cy", 2, 50, {}), ("dee", 0, 200, {}))
    league = run_board(f"return boardLeague({json.dumps(board)}, 'ann', {json.dumps(MONDAY)});")
    assert league["grade"] == 2
    assert [(r["id"], r["place"]) for r in league["rows"]] == [("bo", 1), ("ann", 2), ("cy", 2)]
    assert league["others"] == {"0": 1}, "the Grade 4 learner far ahead is in another league"


def test_a_league_too_small_to_race_becomes_everyone():
    board = rows(("ann", 1, 10, {}), ("bo", 2, 70, {}), ("cy", 3, 50, {}))
    league = run_board(f"return boardLeague({json.dumps(board)}, 'ann', {json.dumps(MONDAY)});")
    assert league["grade"] is None and len(league["rows"]) == 3


def test_seals_go_to_different_people_where_they_can():
    board = rows(("ann", 1, 0, {"days": 6, "sure": 30, "asked": 1, "spark": 3, "pts": 300}),
                 ("bo", 1, 0, {"days": 5, "sure": 20, "asked": 9, "pts": 200}),
                 ("cy", 1, 0, {"days": 4, "sure": 25, "pts": 100}))
    seals = run_board(f"return boardSeals({json.dumps(board)}, '2026-10-12').map(s => [s.seal.key, s.id]);")
    assert seals == [["unbroken", "ann"], ["sure", "cy"], ["curious", "bo"], ["spark", "ann"]], \
        "ann has the most days; Sure hand passes to the next person without a seal; nobody else made a spark"


def test_nobody_gets_a_seal_for_zero():
    board = rows(("ann", 1, 0, {"days": 2}))
    assert run_board(f"return boardSeals({json.dumps(board)}, '2026-10-12').map(s => s.seal.key);") == ["unbroken"]


def test_the_trial_is_the_same_lesson_for_everyone_on_a_day():
    pool = ["a", "b", "c", "d", "e"]
    picks = run_board(f"const p = {json.dumps(pool)}; return ['2026-10-22', '2026-10-22', '2026-10-23', '2026-10-24'].map(d => trialLesson(d, p));")
    assert picks[0] == picks[1] and all(p in pool for p in picks)
    assert run_board("return trialLesson('2026-10-22', []);") is None


def test_the_row_carries_this_week_last_week_grade_and_todays_trial():
    p = {"lessons": {"a": lesson("2026-10-22")}, "board": {"trial": {"2026-10-22": {"id": "x", "marks": ["sign"]}}}}
    row = run_board(f"return boardRow({json.dumps(p)}, 12, '2026-10-22');")
    assert row["week"]["week"] == MONDAY and row["last"]["week"] == "2026-10-12"
    assert row["grade"] == 1 and row["trial"] == {"date": "2026-10-22", "marks": ["sign"]}


def invite(board: dict, shared: bool, others: bool = False) -> bool:
    """Would the Home card invite you? `others`: someone else already has a row this week."""
    rows = [{"id": "x", "row": {"week": {"week": MONDAY}}}] if others else []
    return run_board(f"""globalThis.progress = {{ board: {json.dumps(board)} }}; globalThis.today = () => "2026-10-22";
      boardApi = {{}}; boardLoaded = true; boardShared = {json.dumps(shared)}; boardRows = {json.dumps(rows)}; boardMe = "me";
      return boardInvite();""")


def test_the_invitation_shows_where_others_could_race_and_waits_a_week_after_not_now():
    assert invite({}, shared=True), "on claude.ai or at work, the first person is invited too"
    assert not invite({}, shared=False), "alone on your own computer there is nobody to race"
    assert invite({}, shared=False, others=True), "unless someone is already on the board"
    assert not invite({"on": True}, shared=True), "joined: the card shows your place instead"
    assert not invite({"snooze": "2026-10-28"}, shared=True), "Not now hides it for the week"
    assert invite({"snooze": "2026-10-21"}, shared=True), "and it comes back after"


def test_a_big_league_shows_the_top_five_then_you_and_your_neighbours():
    league = [{"id": f"p{i}"} for i in range(109)]
    shown = run_board(f"return boardShown({json.dumps(league)}, 'p40').map(r => r.gap ? 'gap ' + r.gap : r.id);")
    assert shown == ["p0", "p1", "p2", "p3", "p4", "gap 34", "p39", "p40", "p41", "gap 67"]
    near_top = run_board(f"return boardShown({json.dumps(league[:7])}, 'p5').map(r => r.gap ? 'gap ' + r.gap : r.id);")
    assert near_top == ["p0", "p1", "p2", "p3", "p4", "p5", "p6"], "no gap row for nothing left out"
    assert len(run_board(f"return boardShown({json.dumps(league)}, 'nobody');")) == 6, "not on the board: the top five and a count"


def test_tutor_errors_show_the_servers_words_and_never_a_partial_answer():
    page = page_source()
    assert page.count("tutorSays(") >= 9, "every tutor call says what the server said (a limit, the allowance)"
    assert 'e.code === "asleep" && e.text' not in page
    src = (PAGE_PARTS / "backends.js").read_text(encoding="utf-8")
    fn = src[src.index("function tutorSays"):src.index("async function claudeBackend")]
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    cases = """[
      tutorSays({ server: true, code: "allowance", text: "You've used today's tutor allowance." }, "fallback"),
      tutorSays({ code: "rate_limited", text: "half an answ" }, "fallback"),
      tutorSays({ code: "error", text: "half an answ" }, "fallback"),
      tutorSays(undefined, "fallback")]"""
    out = subprocess.run([node, "-e", fn + f"console.log(JSON.stringify({cases}));"], capture_output=True, text=True, timeout=30)
    assert json.loads(out.stdout) == ["You've used today's tutor allowance.", "Too many requests right now. Wait a minute, then try again.",
                                      "fallback", "fallback"], "claude.ai's partial answer is never shown as an error"


def test_the_page_has_what_the_board_needs():
    page = page_source()
    for needed in ['<main id="board"', 'id="boardSetting"', "data-board-pick", "${boardCardHtml()}", "${boardDoneLine(id)}",
                   'if (backend.board) connectBoard(backend.board, ', '<symbol id="i-chat"', '<symbol id="i-clock"', "data-board-snooze"]:
        assert needed in page, needed


# ---------------------------------------------------------------------------
# the server: everyone reads every row, each writes their own, no emails leave
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABRICKS_APP_NAME", "daily-drill")
    monkeypatch.delenv("DRILL_BOARD_NAME", raising=False)
    store = DocStore(f"sqlite:///{tmp_path / 'drill.db'}")
    return TestClient(create_app(store=store, router=ModelRouter(None, None, store), bank=Bank.load(), with_mcp=False))


SAM, KIM = {"x-forwarded-email": "sam.kim@example.com"}, {"x-forwarded-email": "lee_park@example.com"}
ROW = {"v": 1, "week": {"week": MONDAY, "pts": 19, "tally": [2, 1, 1]}, "grade": 0, "extra": "dropped"}


def test_joined_people_see_each_other_by_name_and_never_by_email(client):
    saved = client.put("/api/board", json=ROW, headers=SAM)
    assert saved.status_code == 200
    client.put("/api/board", json={**ROW, "week": {**ROW["week"], "pts": 30}}, headers=KIM)
    got = client.get("/api/board", headers=SAM).json()
    names = {r["name"]: r for r in got["rows"]}
    assert set(names) == {"Sam Kim", "Lee Park"}
    assert got["me"] == names["Sam Kim"]["id"] and names["Lee Park"]["row"]["week"]["pts"] == 30
    assert "extra" not in names["Sam Kim"]["row"], "only the row's own parts are kept"
    assert "example.com" not in json.dumps(got), "nobody's email reaches anyone else's page"


def test_leaving_takes_your_row_off(client):
    client.put("/api/board", json=ROW, headers=SAM)
    client.put("/api/board", json=ROW, headers=KIM)
    left = client.delete("/api/board", headers=SAM)
    assert left.status_code == 200
    assert [r["name"] for r in client.get("/api/board", headers=KIM).json()["rows"]] == ["Lee Park"]


def test_a_row_without_points_or_too_big_is_refused(client):
    no_points = client.put("/api/board", json={"week": {}}, headers=SAM)
    too_big = client.put("/api/board", json={**ROW, "pad": "x" * 9000}, headers=SAM)
    assert no_points.status_code == 400 and too_big.status_code == 413


# ---------------------------------------------------------------------------
# what a row may hold: the server checks it on the way in and on the way out, and the page checks
# it again as rows arrive, because everyone's page draws everyone's row
# ---------------------------------------------------------------------------

DAY = "2026-10-22"
HTML = '"><img src=x onerror=alert(1)>'  # a piece of HTML: it runs as script in a page that writes it in as it came
WEEK = {"week": MONDAY, "pts": 19, "tally": [2, 1, 1]}
BUSY = {"lessons": {"a": lesson(DAY), "b": lesson("2026-10-20", build=["knot"]), "old": lesson("2026-10-14", explain=["curtain"])},
        "board": {"trial": {DAY: {"id": "x", "marks": ["sign", "knot", "curtain"]}}, "asked": {"2026-10-21": 2, "2026-10-13": 1}, "reviews": {"2026-10-20": 1}}}


def this_week(**parts) -> dict:
    return {"week": {**WEEK, **parts}}


# Rows no page builds: the server refuses each one, and the page leaves each one out.
BAD_ROWS = {
    "HTML in the tally": this_week(tally=[HTML, 1, 1]),
    "HTML for the points": this_week(pts=HTML),
    "HTML for a mark": {"week": WEEK, "trial": {"date": DAY, "marks": [HTML]}},
    "true for the points": this_week(pts=True),
    "a negative number": this_week(pts=-1),
    "a number that is not whole": this_week(pts=1.5),
    "a number far too large": this_week(pts=10**7),
    "a count written as text": this_week(days="3"),
    "a tally of two": this_week(tally=[1, 1]),
    "no tally": {"week": {"week": MONDAY, "pts": 19}},
    "an unknown mark": {"week": WEEK, "trial": {"date": DAY, "marks": ["sign", "star"]}},
    "four marks": {"week": WEEK, "trial": {"date": DAY, "marks": ["sign"] * 4}},
    "a trial that is only text": {"week": WEEK, "trial": HTML},
    "a trial with no date": {"week": WEEK, "trial": {"marks": ["sign"]}},
    "a grade of 99": {"week": WEEK, "grade": 99},
    "a grade written as text": {"week": WEEK, "grade": "2"},
    "a date not written YYYY-MM-DD": this_week(week="19 October 2026"),
    "a day that does not exist": this_week(week="2026-02-30"),
    "a year before 1000": this_week(week="0999-12-28"),
    "last week as text": {"week": WEEK, "last": HTML},
    "HTML in last week's tally": {"week": WEEK, "last": {**WEEK, "week": "2026-10-12", "tally": [0, 0, HTML]}},
}


@pytest.mark.parametrize("what", BAD_ROWS)
def test_a_row_with_a_part_of_the_wrong_kind_is_refused(client, what):
    sent = client.put("/api/board", json=BAD_ROWS[what], headers=SAM)
    assert sent.status_code == 400
    assert "leaderboard row" in sent.json()["detail"]["text"] and "img" not in sent.text, "a plain message, without the row's own text in it"
    assert client.get("/api/board", headers=SAM).json()["rows"] == [], "and nothing was saved"


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_points_that_are_not_a_real_number_are_refused(client, number):
    body = json.dumps(this_week(pts="?")).replace('"?"', number)  # not JSON, but Python reads NaN and Infinity all the same
    sent = client.put("/api/board", content=body, headers={**SAM, "content-type": "application/json"})
    assert sent.status_code == 400


@pytest.mark.parametrize("v", ["1", 1.5, -1, True, None, 2_000_000])
def test_a_version_that_is_not_a_whole_number_is_refused(client, v):
    sent = client.put("/api/board", json={"v": v, "week": WEEK}, headers=SAM)
    assert sent.status_code == 400 and "leaderboard row" in sent.json()["detail"]["text"]
    assert client.get("/api/board", headers=SAM).json()["rows"] == []


def test_the_message_for_a_bad_last_week_never_says_the_row_needs_it(client):
    def says(row: dict) -> str:
        sent = client.put("/api/board", json=row, headers=SAM)
        assert sent.status_code == 400, row
        return sent.json()["detail"]["text"]

    for last in ("x", {}, [1], {"week": "2026-10-12", "tally": [0, 0, 0]}):
        text = says({"week": WEEK, "last": last})
        assert "last week must be null, left out, or hold" in text and "needs" not in text, "last week may be left out"
    for row in ({}, {"week": "x"}, {"week": {"week": MONDAY, "tally": [0, 0, 0]}}):
        assert says(row) == "A leaderboard row needs this week's points.", "this week is the part a row must have"


@pytest.mark.parametrize("progress", [BUSY, {}], ids=["two busy weeks", "a new learner"])
def test_the_row_the_page_builds_is_saved_just_as_it_is(client, progress):
    row = run_board(f"return boardRow({json.dumps(progress)}, 12, {json.dumps(DAY)});")
    assert client.put("/api/board", json=row, headers=SAM).status_code == 200
    assert client.get("/api/board", headers=SAM).json()["rows"][0]["row"] == row


def test_a_row_may_leave_out_all_but_this_weeks_date_points_and_tally(client):
    for row in ({"week": WEEK}, {"week": WEEK, "last": None, "grade": None, "trial": None}, {"v": 1, "week": {**WEEK, "days": 2}, "grade": 4}):
        assert client.put("/api/board", json=row, headers=SAM).status_code == 200, row
        assert client.get("/api/board", headers=SAM).json()["rows"][0]["row"] == row
    extra = {"week": {**WEEK, "note": HTML}, "trial": {"date": DAY, "marks": ["knot"], "note": HTML}, "note": HTML}
    assert client.put("/api/board", json=extra, headers=SAM).status_code == 200
    assert client.get("/api/board", headers=SAM).json()["rows"][0]["row"] == {"week": WEEK, "trial": {"date": DAY, "marks": ["knot"]}}, \
        "a part the page does not save is dropped, wherever it sits"


def test_a_bad_row_already_in_the_table_is_left_out_and_the_rest_still_show(client):
    store = client.app.state.store
    for i, row in enumerate(BAD_ROWS.values()):  # saved before rows were checked
        store.for_owner(f"old{i}@example.com").board_set(f"Old {i}", row)
    with store.engine.begin() as conn:  # typed into the table by hand: not a row at all, or not even JSON
        for i, body in enumerate(["null", '"text"', "[1]", "not json", "[" * 100_000]):
            conn.execute(insert(board_table).values(owner=f"hand{i}@example.com", name=f"Hand {i}", body=body, updated_at=time.time()))
    client.put("/api/board", json=ROW, headers=SAM)
    got = client.get("/api/board", headers=KIM)
    assert got.status_code == 200, "never an error for the reader"
    assert [r["name"] for r in got.json()["rows"]] == ["Sam Kim"]


def test_a_good_row_in_the_table_is_sent_with_only_the_parts_the_page_saves(client):
    saved = {"week": {**WEEK, "note": HTML}, "trial": {"date": DAY, "marks": ["knot"], "note": HTML}, "note": HTML}
    client.app.state.store.for_owner("old@example.com").board_set("Old", saved)  # saved before rows were checked
    got = client.get("/api/board", headers=KIM)
    assert [r["row"] for r in got.json()["rows"]] == [{"week": WEEK, "trial": {"date": DAY, "marks": ["knot"]}}]
    assert "img" not in got.text, "a part the page does not save never leaves the table"


def test_the_server_and_the_page_agree_on_what_a_row_may_hold():
    limits = run_board("return [GRADES.length, MARKS, TRIAL_QS, BOARD_MAX, BOARD_COUNTS];")
    assert limits == [api.BOARD_GRADES, list(api.BOARD_MARKS), api.BOARD_TRIAL, api.BOARD_MAX, list(api.BOARD_COUNTS)]


def test_the_page_keeps_a_good_row_and_leaves_a_bad_one_out():
    row = run_board(f"return boardRow({json.dumps(BUSY)}, 12, {json.dumps(DAY)});")
    out = run_board(f"""const good = {json.dumps(row)}, bad = {json.dumps(list(BAD_ROWS.values()))}, week = good.week;
      return {{ kept: boardSafe({{ id: "a", name: "Ann", row: good }}), least: boardSafe({{ id: "b", row: {json.dumps({"week": WEEK})} }}),
        bad: bad.map(row => boardSafe({{ id: "c", name: "Cy", row }})),
        odd: [null, "text", {{ id: "d" }}, {{ id: "d", row: "text" }}, {{ id: 7, row: good }}, {{ id: "d", row: {{ ...good, week: {{ ...week, pts: NaN }} }} }},
              {{ id: "d", row: {{ ...good, week: {{ ...week, pts: Infinity }} }} }}, {{ id: "d", row: {{ ...good, trial: {{ date: week.week, marks: "sign" }} }} }},
              {{ id: "d", row: {{ ...good, week: {{ ...week, tally: [1, , 3] }} }} }}].map(boardSafe) }};""")
    assert out["kept"] == {"id": "a", "name": "Ann", "row": {k: row[k] for k in ("week", "last", "grade", "trial")}}, "the page's own row comes through as it was"
    assert out["least"] == {"id": "b", "name": "", "row": {"week": {**WEEK, **{k: 0 for k in api.BOARD_COUNTS}}, "last": None, "grade": None, "trial": None}}, \
        "a part left out is nothing: a count of 0, no last week, no grade, no trial"
    assert [what for what, kept in zip(BAD_ROWS, out["bad"]) if kept is not None] == [], "every row the server refuses, the page leaves out"
    assert out["odd"] == [None] * 9, \
        "and so is anything that is not a row at all (NaN, Infinity and a tally with a missing entry never come by JSON, so they are tried here)"


# The page around board.js, as much as the board needs to draw: you ("me") have joined and done today's trial, and the board is open.
ON_SCREEN = """const box = { hidden: false, innerHTML: "" };
  globalThis.$ = () => box; globalThis.today = () => "2026-10-22"; globalThis.cur = null; globalThis.renderHome = () => {};
  globalThis.progress = { lessons: {}, board: { on: true, trial: { "2026-10-22": { id: "x", marks: ["sign", "sign", "knot"] } } } };
  globalThis.ALL_LESSONS = ["x"]; globalThis.LESSONS = { x: { title: "A lesson" } };
  globalThis.checkQs = () => [[], [], []]; globalThis.isDoneL = () => false; globalThis.hzCoach = (kind, html) => html;
"""


def person(pid: str, pts=40, grade=1, tally=(1, 1, 1), marks=None, name=None) -> dict:
    """One person's row as the board holds it; `marks` are today's trial marks."""
    return {"id": pid, "name": name or pid.title(), "row": {
        "week": {"week": MONDAY, "pts": pts, "tally": list(tally), "days": 1, "asked": 0, "spark": 0, "lessons": 1, "reviews": 0},
        "last": None, "grade": grade, "trial": None if marks is None else {"date": DAY, "marks": marks}}}


def test_bad_rows_from_outside_never_reach_the_board():
    good = [person("me"), person("ann", pts=70, marks=["sign", "knot", "curtain"]), person("bo", pts=50, name=HTML), person("cy", grade=3)]
    bad = [{"id": f"bad{i}", "name": f"Bad {i}", "row": {"grade": 1, **row}} for i, row in enumerate(BAD_ROWS.values())]
    out = run_board(ON_SCREEN + f"""boardApi = {{ list: async () => ({{ me: "me", rows: [...{json.dumps(bad)}, null, {{ id: "odd" }}, ...{json.dumps(good)}] }}) }};
      await boardRefresh();  // the way rows really arrive, from the server and from claude.ai's database alike; it draws the open board too
      return {{ ids: boardRows.map(r => r.id), board: box.innerHTML, card: boardCardHtml() }};""")
    assert out["ids"] == ["me", "ann", "bo", "cy"], "only the good rows are kept"
    for html in (out["board"], out["card"]):
        assert "<img" not in html and "Bad" not in html
        assert "Ann" in html and "&lt;img" in html, "the good rows are drawn, and a name is shown as text"
    assert "Grade 3 league" in out["board"] and "Grade 1 · 1" in out["board"] and "+6" in out["board"], "your league, the other one, and Ann's trial"


def test_an_answer_whose_rows_are_not_a_list_leaves_the_board_empty():
    out = run_board(ON_SCREEN + f"""const seen = [];
      for (const rows of ["text", 7, {{}}, {{ length: 1, 0: {json.dumps(person("ann"))} }}, null, undefined]) {{
        boardRows = [{json.dumps(person("old"))}]; boardLoaded = false;  // what the board held before this answer
        boardApi = {{ list: async () => ({{ me: "me", rows }}) }};
        await boardRefresh();
        seen.push([boardRows.length, boardLoaded]);
      }}
      return seen;""")
    assert out == [[0, True]] * 6, "no rows and no error: the board is loaded, and empty"


def test_a_value_the_cleaning_missed_still_cannot_become_html():
    counts = [person(p, pts=HTML, tally=[HTML] * 3) for p in ("me", "ann", "bo")]
    marks = [person("me"), person("ann", marks=[HTML, "sign"]), person("bo", marks=HTML), person("cy", marks=["constructor"]), person("dee", marks=["sign", "lesson"])]
    grades = [person("me", grade=99), person("ann", grade=99), person("bo", grade=99), person("cy", grade=HTML), person("dee", grade=3), person("eve", grade=None)]
    gap = [person("me"), {**person("ann"), "gap": HTML}, person("bo")]  # the board's own "12 more" lines are {gap: 12}
    out = run_board(ON_SCREEN + f"""boardApi = {{}}; boardLoaded = true; boardMe = "me";
      const draw = rows => {{ boardRows = rows; renderBoard(); return {{ board: box.innerHTML, card: boardCardHtml(), trial: trialHtml() }}; }};  // straight in, past boardSafe
      return {{ counts: draw({json.dumps(counts)}), marks: draw({json.dumps(marks)}), grades: draw({json.dumps(grades)}), gap: draw({json.dumps(gap)}),
        tally: {{ odd: [undefined, null, "text", [], [{json.dumps(HTML)}], [1, 2]].map(tallyHtml).join("") }} }};""")
    for what, drawn in out.items():
        for part, html in drawn.items():
            assert "<img" not in html, f"{what}: {part}"
    assert "Ann" in out["counts"]["board"] and "Ann" in out["counts"]["card"], "the rows are drawn, with 0 where a count was not a number"
    trial = out["marks"]["trial"]
    assert "Ann" in trial and "Bo" not in trial and "Cy" not in trial, "only the marks the page knows are drawn"
    assert "Dee" in trial and trial.count("+3") == 2 and "+13" not in trial, "and counted: Ann's and Dee's one known mark is 3 points each"
    assert "Everyone" in out["grades"]["board"] and "Everyone" in out["grades"]["card"], "a grade that does not exist names no league"
    assert "Grade 1 · 1" in out["grades"]["board"], "and the real other league still shows"
    assert "Ann" in out["gap"]["board"] and "more</li>" not in out["gap"]["board"], "a person's row is drawn as a person, never as a line of how many more"
