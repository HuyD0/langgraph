"""How fresh each lesson's facts are: when they were last checked against their sources.

Lessons about products that change often (Databricks, Azure, MLflow, LangGraph) carry a
``checked`` date and the ``sources`` it was checked against. This lists the ones due for
another look, so an update starts from the right lessons and the right pages.
"""

from __future__ import annotations

import datetime

from drill.content.model import Module

STALE_DAYS = 180  # the page warns after this too (STALE_DAYS in page.html)
# The day dates were first tracked. Lessons with no ``checked`` date of their own count from
# here ("content as of"), so every lesson comes due for a look on the same cycle.
CONTENT_DATE = "2026-10-12"


def freshness(loaded: list[Module], today: datetime.date, days: int = STALE_DAYS) -> dict:
    """Sort every lesson into due (looked at too long ago) and fresh. ``never`` stays empty now
    that undated lessons count from CONTENT_DATE; their rows carry ``as_of``."""
    due, never, fresh = [], [], []
    for mod in loaded:
        for lesson in mod.lessons:
            row = {"id": lesson["id"], "title": lesson["title"], "module": mod.title,
                   "checked": lesson.get("checked"), "sources": lesson.get("sources") or []}
            if not row["checked"]:
                row["checked"], row["as_of"] = CONTENT_DATE, True
            row["age"] = (today - datetime.date.fromisoformat(row["checked"])).days
            (due if row["age"] > days else fresh).append(row)
    due.sort(key=lambda r: -r["age"])
    return {"due": due, "never": never, "fresh": fresh}
