"""What happened, as rows a dashboard can count: the events behind team progress.

The page saves your whole progress document each time something changes, which is
right for the page and awkward for a report ("who finished module 4?" means opening
every document). So when a progress document is saved, the server compares it with the
copy it had and writes one event per change:

    step         reached a lesson's next step (Learn 0, Check 1, Build 2, Interview 3)
    checked      answered the lesson's check question (``answer``)
    lesson_done  finished a lesson
    solved       passed an exercise's tests (``hints`` used, ``count`` times solved)

The tutor's own routes add ``asked`` (a question in the page, with what it was for),
``tests_run``, ``hint_used`` and ``saved_to_study``. Each event has an owner, a time, a
kind, a lesson and a small JSON ``detail``; see ``events`` in :mod:`drill.server.store`.
"""

from __future__ import annotations

import re
from typing import Iterator

PROGRESS_PATH = re.compile(r"^data/users/[^/]+/progress$")


def is_progress(path: str) -> bool:
    return bool(PROGRESS_PATH.match(path))


def progress_events(before: dict | None, after: dict | None) -> Iterator[tuple[str, str, dict]]:
    """``(kind, lesson_id, detail)`` for each change from ``before`` to ``after``."""
    before, after = before or {}, after or {}
    old_lessons = before.get("lessons") or {}
    for lesson_id, now in (after.get("lessons") or {}).items():
        if not isinstance(now, dict):
            continue
        was = old_lessons.get(lesson_id) or {}
        if (now.get("step") or 0) > (was.get("step") or 0):
            yield "step", lesson_id, {"step": now.get("step")}
        if now.get("checked") is not None and was.get("checked") is None:
            yield "checked", lesson_id, {"answer": now.get("checked")}
        if now.get("done") and not was.get("done"):
            yield "lesson_done", lesson_id, {}
    old_solved = before.get("solved") or {}
    for problem_id, now in (after.get("solved") or {}).items():
        was = old_solved.get(problem_id)
        count = now.get("count", 1) if isinstance(now, dict) else 1
        was_count = (was.get("count", 1) if isinstance(was, dict) else 1) if was else 0
        if count > was_count:
            yield "solved", problem_id, {"hints": now.get("hints") if isinstance(now, dict) else None, "count": count}
