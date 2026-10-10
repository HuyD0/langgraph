"""Made-up data shaped like your finance tracker's, for the browser practice page.

Nothing here comes from your real database. It's generated from a fixed seed, so
it's the same every time: three months of everyday Canadian spending, a few
subscriptions, one odd charge, a meal log with gaps, slowly falling weigh-ins and
a lifting log that gets heavier.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Any

from drill.mine.problems import KINDS

START = dt.date(2026, 7, 1)
END = dt.date(2026, 9, 30)


def _days():
    d = START
    while d <= END:
        yield d
        d += dt.timedelta(days=1)


def transactions() -> list[dict]:
    rng = random.Random(7)
    out: list[dict] = []

    def add(day: dt.date, merchant: str, cents: int, category: str) -> None:
        out.append({"date": day.isoformat(), "merchant": merchant,
                    "amount_cents": cents, "category": category})

    for day in _days():
        if day.day == 1:
            add(day, "Rent", -185000, "Housing")
            add(day, "Transfer to savings", -50000, "Transfers")
        if day.day == 3:
            add(day, "Netflix", -1699, "Subscriptions")
        if day.day == 8:
            add(day, "Spotify", -1199, "Subscriptions")
        if day.day == 12:
            add(day, "GoodLife Fitness", -3999, "Health & Fitness")
        if day.day == 15:
            add(day, "Rogers", -8500, "Phone & Internet")
        if day.day in (15, 30):
            add(day, "Payroll", 265000, "Income")
        if day.day == 22:
            add(day, "RBC Visa payment", -120000, "Credit Card Payment")
        if day.weekday() < 5 and rng.random() < 0.6:
            add(day, rng.choice(["Tim Hortons", "Starbucks"]), -rng.choice([245, 310, 525, 615]), "Coffee")
        if day.weekday() == 5:
            add(day, rng.choice(["Loblaws", "No Frills"]), -rng.randint(6000, 14000), "Groceries")
        if day.weekday() == 6 and rng.random() < 0.5:
            add(day, "Shell", -rng.randint(4500, 7000), "Gas")
        if rng.random() < 0.15:
            add(day, rng.choice(["Pizza Pizza", "A&W", "Pho Hung"]), -rng.randint(1400, 4200), "Dining")
        if rng.random() < 0.08:
            add(day, "Uber", -rng.randint(900, 2600), "Transportation")
        if rng.random() < 0.06:
            add(day, "Amazon", -rng.randint(1500, 6000), "Shopping")
    # One odd charge for the monitor problem to find, and a refund to ignore.
    add(dt.date(2026, 9, 18), "Amazon", -38999, "Shopping")
    add(dt.date(2026, 9, 25), "Amazon", 2999, "Shopping")
    out.sort(key=lambda t: t["date"])
    return out


def meal_days() -> list[int]:
    rng = random.Random(11)
    days = [d.toordinal() for d in _days() if rng.random() < 0.8]
    rng.shuffle(days)
    return days


def weigh_ins() -> list[list]:
    rng = random.Random(13)
    out, kg = [], 82.0
    for d in _days():
        kg -= 0.02
        if rng.random() < 0.3:
            out.append([d.isoformat(), round(kg + rng.uniform(-0.8, 0.8), 1)])
    return out


def lifts() -> list[list]:
    rng = random.Random(17)
    plan = {"Bench Press": 60.0, "Squat": 80.0, "Deadlift": 100.0, "Lat Pulldown": 50.0, "Push Up": 0.0}
    out = []
    for i, d in enumerate(_days()):
        if d.weekday() in (0, 2, 4):
            for name, start in plan.items():
                if rng.random() < 0.7:
                    kg = 0.0 if start == 0 else start + 2.5 * (i // 14) - rng.choice([0, 0, 2.5, 5])
                    out.append([d.isoformat(), name, kg])
    return out


def fake_args(problem_id: str) -> tuple[Any, ...]:
    """The look-alike version of what ``drill.mine.data.load`` returns."""
    txns = transactions()
    september = [t for t in txns if t["date"].startswith("2026-09")]
    return {
        "spending_by_category": (september, KINDS),
        "top_merchants": (txns, KINDS, 5),
        "subscriptions": (txns,),
        "unusual_charges": (txns,),
        "monthly_summary": (september, KINDS, 6),
        "logging_streak": (meal_days(),),
        "monthly_low_weight": (weigh_ins(),),
        "personal_bests": (lifts(),),
    }[problem_id]
