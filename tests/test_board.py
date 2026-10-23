"""The leaderboard (page/board.js and /api/board): points from the marks, the grade league, last
week's seals, the daily trial, and the server keeping everyone's rows. The page's scoring is plain
functions, so node runs them straight from the part files."""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from drill.content.build import PAGE_PARTS, page_source
from drill.server.api import create_app
from drill.server.bank import Bank
from drill.server.router import ModelRouter
from drill.server.store import DocStore


def _page_line(start: str) -> str:
    for line in page_source().splitlines():
        if line.startswith(start):
            return line
    raise AssertionError(f"no line starts with {start!r}")


def run_board(js: str) -> object:
    """Run share.js and board.js in node (with the page's date helpers and grades), then `js`."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    stubs = "\n".join([
        "const document = { addEventListener() {} };",
        "const ic = n => n;",
        _page_line("const dayKey ="), _page_line("const GRADES ="), _page_line("const gradeAt ="),
    ])
    script = "\n".join([stubs, (PAGE_PARTS / "share.js").read_text(), (PAGE_PARTS / "board.js").read_text(),
                        "console.log(JSON.stringify((() => { " + js + " })()));"])
    out = subprocess.run([node, "-e", script], capture_output=True, text=True, timeout=30)
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
    assert not invite({}, shared=False), "alone on your own Mac there is nobody to race"
    assert invite({}, shared=False, others=True), "unless someone is already on the board"
    assert not invite({"on": True}, shared=True), "joined: the card shows your place instead"
    assert not invite({"snooze": "2026-10-28"}, shared=True), "Not now hides it for the week"
    assert invite({"snooze": "2026-10-21"}, shared=True), "and it comes back after"


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
