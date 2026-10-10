"""Loads your real finance-tracker data, read-only, in the shapes the problems take.

The database is opened with SQLite's ``mode=ro``, so nothing here can change it.
Rows stay on this Mac: they go to your solution in a local subprocess and to the
terminal, and are never written anywhere else or sent to a model.

Point ``DRILL_FINANCE_DB`` at the file if it isn't in the default place.
"""

from __future__ import annotations

import datetime as dt
import os
import sqlite3
from pathlib import Path
from typing import Any, Callable

DEFAULT_DB = Path.home() / "Developer" / "finance" / "data" / "finance.db"


def db_path() -> Path:
    return Path(os.environ.get("DRILL_FINANCE_DB") or DEFAULT_DB).expanduser()


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or db_path()
    if not path.exists():
        raise FileNotFoundError(
            f"No finance database at {path}. Set DRILL_FINANCE_DB to its location."
        )
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def transactions(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        'SELECT date, COALESCE(NULLIF(merchant, \'\'), description), amount_cents, category '
        'FROM "transaction" ORDER BY date, id'
    ).fetchall()
    return [{"date": d, "merchant": m, "amount_cents": c, "category": cat} for d, m, c, cat in rows]


def kinds(conn: sqlite3.Connection) -> dict[str, str]:
    return dict(conn.execute("SELECT name, kind FROM category").fetchall())


def _last_full_month(today: dt.date) -> str:
    first = today.replace(day=1)
    return (first - dt.timedelta(days=1)).strftime("%Y-%m")


def _month_name(month: str) -> str:
    return dt.date.fromisoformat(month + "-01").strftime("%B %Y")


# Each loader returns (args for the function, a plain description of what you're looking at).
Loader = Callable[[sqlite3.Connection, dt.date], tuple[tuple[Any, ...], str]]


def _spending(conn, today):
    month = _last_full_month(today)
    txns = [t for t in transactions(conn) if t["date"].startswith(month)]
    return (txns, kinds(conn)), f"your {len(txns)} transactions in {_month_name(month)}"


def _top_merchants(conn, today):
    since = (today - dt.timedelta(days=90)).isoformat()
    txns = [t for t in transactions(conn) if t["date"] >= since]
    return (txns, kinds(conn), 5), f"your {len(txns)} transactions in the last 90 days, top 5"


def _all_txns(conn, today):
    txns = transactions(conn)
    return (txns,), f"all {len(txns)} of your transactions"


def _summary(conn, today):
    month = _last_full_month(today)
    txns = [t for t in transactions(conn) if t["date"].startswith(month)]
    return (txns, kinds(conn), 6), f"{_month_name(month)}, at most 6 lines"


def _streak(conn, today):
    dates = [d for (d,) in conn.execute("SELECT DISTINCT date FROM meal")]
    days = [dt.date.fromisoformat(d).toordinal() for d in dates]
    return (days,), f"the {len(days)} days you logged food"


def _weights(conn, today):
    rows = conn.execute(
        "SELECT date, value FROM measurement WHERE kind = 'Weight' ORDER BY date, id"
    ).fetchall()
    return ([[d, kg] for d, kg in rows],), f"your {len(rows)} weigh-ins"


def _lifts(conn, today):
    rows = conn.execute(
        "SELECT date, name, weight_kg FROM exerciseentry "
        "WHERE kind = 'strength' AND weight_kg IS NOT NULL ORDER BY date, id"
    ).fetchall()
    return ([[d, n, kg] for d, n, kg in rows],), f"your {len(rows)} logged lifts"


LOADERS: dict[str, Loader] = {
    "spending_by_category": _spending,
    "top_merchants": _top_merchants,
    "subscriptions": _all_txns,
    "unusual_charges": _all_txns,
    "monthly_summary": _summary,
    "logging_streak": _streak,
    "monthly_low_weight": _weights,
    "personal_bests": _lifts,
}


def load(problem_id: str, conn: sqlite3.Connection, today: dt.date | None = None):
    return LOADERS[problem_id](conn, today or dt.date.today())
