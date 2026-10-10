"""The money & health problems must be solvable, and the real-data loaders must
produce the shapes the problems promise.

None of these tests read your real finance database: the loaders run against a
small in-memory copy of its schema instead.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

import pytest

from drill.mine import data
from drill.mine.export import page_track
from drill.mine.fake import fake_args
from drill.mine.learn import LEARN
from drill.mine.problems import MINE_PROBLEMS, REAL_WORLD
from drill.problems import TestCase
from drill.sandbox import run_submission

IDS = [p.id for p in MINE_PROBLEMS]


@pytest.mark.parametrize("problem", MINE_PROBLEMS, ids=IDS)
def test_reference_solution_passes(problem):
    result = run_submission(problem, problem.reference_solution, timeout=30)
    assert result["fatal_error"] is None, result["fatal_error"]
    assert result["passed"], [c for c in result["cases"] if not c["passed"]][:1]


@pytest.mark.parametrize("problem", MINE_PROBLEMS, ids=IDS)
def test_starter_code_does_not_pass(problem):
    assert not run_submission(problem, problem.starter_code, timeout=30)["passed"]


@pytest.mark.parametrize("problem", MINE_PROBLEMS, ids=IDS)
def test_problem_has_lesson_and_sample(problem):
    assert problem.samples
    assert problem.id in REAL_WORLD
    lesson = LEARN[problem.id]
    assert lesson["concepts"] and lesson["byhand"] and lesson["gotchas"]
    assert "___" in lesson["guided"]
    assert f"def {problem.function_name}(" in lesson["guided"]


@pytest.mark.parametrize("problem", MINE_PROBLEMS, ids=IDS)
def test_reference_runs_on_fake_data(problem):
    import dataclasses

    args = fake_args(problem.id)
    case = TestCase(args=args, expected=None)
    result = run_submission(dataclasses.replace(problem, test_cases=(case,)),
                            problem.reference_solution, timeout=30)
    assert result["fatal_error"] is None
    assert result["cases"][0]["error"] is None


def test_fake_data_has_something_to_find():
    track = {p["id"]: p for p in page_track()["problems"]}
    last = lambda pid: track[pid]["cases"][-1]["expected"]  # noqa: E731
    assert "Netflix" in last("subscriptions")
    assert last("unusual_charges")
    assert last("logging_streak") > 1
    assert "Bench Press" in last("personal_bests")


def test_page_export_is_json_and_marked_as_its_own_track():
    track = page_track()
    json.dumps(track)
    assert {p["track"] for p in track["problems"]} == {"mine"}
    assert set(track["learn"]) == set(IDS)


@pytest.fixture
def finance_db(tmp_path):
    path = tmp_path / "finance.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE category(name VARCHAR, kind VARCHAR);
        CREATE TABLE "transaction"(id INTEGER, date DATE, description VARCHAR, merchant VARCHAR,
                                   amount_cents INTEGER, category VARCHAR);
        CREATE TABLE nutritionentry(date DATE);
        CREATE VIEW meal AS SELECT date FROM nutritionentry;
        CREATE TABLE measurement(id INTEGER, date DATE, kind VARCHAR, value FLOAT);
        CREATE TABLE exerciseentry(id INTEGER, date DATE, name VARCHAR, kind VARCHAR, weight_kg FLOAT);
        INSERT INTO category VALUES ('Coffee', 'expense'), ('Transfers', 'transfer');
        INSERT INTO "transaction" VALUES
            (1, '2026-09-02', 'TIM HORTONS #12', 'Tim Hortons', -245, 'Coffee'),
            (2, '2026-09-03', 'E-TRANSFER', NULL, -5000, 'Transfers'),
            (3, '2026-10-01', 'TIM HORTONS #12', '', -310, 'Coffee');
        INSERT INTO nutritionentry VALUES ('2026-09-01'), ('2026-09-02'), ('2026-09-02');
        INSERT INTO measurement VALUES (1, '2026-09-01', 'Weight', 80.0), (2, '2026-09-01', 'Fitbit Steps', 9000);
        INSERT INTO exerciseentry VALUES (1, '2026-09-01', 'Squat', 'strength', 80.0),
                                         (2, '2026-09-01', 'Run', 'cardio', NULL);
        """
    )
    conn.commit()
    conn.close()
    return path


def test_loaders_read_only_and_shaped_like_the_problems(finance_db):
    conn = data.connect(finance_db)
    today = dt.date(2026, 10, 9)

    (txns, kinds), label = data.load("spending_by_category", conn, today)
    assert [t["merchant"] for t in txns] == ["Tim Hortons", "E-TRANSFER"]  # September only
    assert kinds == {"Coffee": "expense", "Transfers": "transfer"}
    assert "September 2026" in label

    (all_txns,), _ = data.load("subscriptions", conn, today)
    assert all_txns[-1]["merchant"] == "TIM HORTONS #12"  # empty merchant falls back to description

    (days,), _ = data.load("logging_streak", conn, today)
    assert sorted(days) == [dt.date(2026, 9, 1).toordinal(), dt.date(2026, 9, 2).toordinal()]

    assert data.load("monthly_low_weight", conn, today)[0] == ([["2026-09-01", 80.0]],)
    assert data.load("personal_bests", conn, today)[0] == ([["2026-09-01", "Squat", 80.0]],)

    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM category")


def test_every_problem_has_a_loader():
    assert set(data.LOADERS) == set(IDS)


def test_missing_database_has_a_clear_message(tmp_path):
    with pytest.raises(FileNotFoundError, match="DRILL_FINANCE_DB"):
        data.connect(tmp_path / "nope.db")
