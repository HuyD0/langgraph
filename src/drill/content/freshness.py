"""How fresh each lesson's facts are: when they were last checked against their sources.

Lessons about products that change often (Databricks, Azure, MLflow, LangGraph) carry a
``checked`` date and the ``sources`` it was checked against. This lists the ones due for
another look, so an update starts from the right lessons and the right pages.
"""

from __future__ import annotations

import datetime

from drill.content.model import Module

STALE_DAYS = 180  # the page warns after this too (STALE_DAYS in page.html)
# The day dates were first tracked. Lessons with no ``checked`` date of their own carry it
# ("content as of") but never come due: the facts that go out of date live in sourced lessons.
CONTENT_DATE = "2026-10-12"


def freshness(loaded: list[Module], today: datetime.date, days: int = STALE_DAYS) -> dict:
    """Sort every lesson into due (checked against its sources too long ago), fresh, and never:
    lessons with no sources, which are dated by the content and do not age. Undated rows carry
    ``as_of``."""
    due, never, fresh = [], [], []
    for mod in loaded:
        for lesson in mod.lessons:
            row = {"id": lesson["id"], "title": lesson["title"], "module": mod.title,
                   "checked": lesson.get("checked"), "sources": lesson.get("sources") or []}
            if not row["checked"]:
                row["checked"], row["as_of"] = CONTENT_DATE, True
            row["age"] = (today - datetime.date.fromisoformat(row["checked"])).days
            if not row["sources"]:
                never.append(row)
                continue
            (due if row["age"] > days else fresh).append(row)
    due.sort(key=lambda r: -r["age"])
    return {"due": due, "never": never, "fresh": fresh}
