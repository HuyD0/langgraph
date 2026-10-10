"""The lessons and exercises the Daily Drill page shows, for the server and the MCP tools.

The content lives in web/daily-drill/content and is assembled by web/daily-drill/build.py,
which writes two files into web/daily-drill/dist: the page itself, and ``data.json`` with
the same modules, lessons and exercises as plain data. The server reads that file, so the
page and the tools can never disagree about what a lesson is. If the build is missing or
older than the content, it is rebuilt on first use.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from drill.config import PROJECT_ROOT

DRILL_DIR = PROJECT_ROOT / "web" / "daily-drill"
DIST = DRILL_DIR / "dist"
PAGE = DIST / "daily-drill.html"
DATA = DIST / "data.json"


def _sources() -> list[Path]:
    files = [DRILL_DIR / "app.html", DRILL_DIR / "build.py"]
    files += [p for p in (DRILL_DIR / "content").iterdir() if p.is_file()]
    return files


def ensure_built(force: bool = False) -> None:
    """Run build.py when dist/ is missing or older than any source file."""
    newest = max(p.stat().st_mtime for p in _sources())
    fresh = PAGE.exists() and DATA.exists() and min(PAGE.stat().st_mtime, DATA.stat().st_mtime) >= newest
    if fresh and not force:
        return
    result = subprocess.run([sys.executable, str(DRILL_DIR / "build.py")], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("Building the Daily Drill page failed:\n" + result.stdout + result.stderr)


class Bank:
    """Modules in path order, lessons by id, exercises by id."""

    def __init__(self, data: dict):
        self.modules: list[dict] = data["modules"]
        self.lessons: dict[str, dict] = data["lessons"]
        self.problems: dict[str, dict] = {p["id"]: p for p in data["bank"]}
        self.learn: dict[str, dict] = data.get("learn", {})

    @classmethod
    def load(cls) -> "Bank":
        ensure_built()
        return cls(json.loads(DATA.read_text(encoding="utf-8")))

    def order(self) -> list[str]:
        """Every lesson id, in the order the path shows them."""
        return [lesson_id for module in self.modules for lesson_id in module["lessons"]]

    def module_of(self, lesson_id: str) -> dict | None:
        return next((m for m in self.modules if lesson_id in m["lessons"]), None)

    def next_lesson(self, progress: dict | None) -> str | None:
        """The first lesson not marked done, or ``None`` when the path is finished."""
        done = (progress or {}).get("lessons", {})
        for lesson_id in self.order():
            if not done.get(lesson_id, {}).get("done"):
                return lesson_id
        return None

    def card(self, lesson_id: str) -> dict:
        """One lesson as a compact dict: what to read, the question, the exercise, the interview angle."""
        if lesson_id not in self.lessons:
            raise KeyError(f"No lesson called {lesson_id!r}. Try list_lessons().")
        lesson = self.lessons[lesson_id]
        problem = self.problems[lesson_id]
        learn = self.learn.get(lesson_id, {})
        module = self.module_of(lesson_id) or {}
        question, options, answer, why = lesson["check"]
        pattern, text, say, classic = lesson["angle"]
        cases = problem.get("cases", [])
        sample = next((c for c in cases if c.get("sample")), cases[0] if cases else None)
        card = {
            "id": lesson_id,
            "title": lesson["title"],
            "module": module.get("title"),
            "learn": lesson["learn"],
            "example": {"title": lesson["example"][0], "text": lesson["example"][1]},
            "check": {"question": question, "options": options, "answer_index": answer, "why": why},
            "exercise": {
                "title": problem["title"],
                "prompt": problem["prompt"],
                "pattern": problem.get("pattern"),
                "function": problem["fn"],
                "starter": problem["starter"],
                "scaffold": learn.get("guided"),
                "sample_case": sample,
            },
            "interview": {"pattern": pattern, "angle": text, "say_it_like_this": say, "classic": classic},
        }
        if lesson.get("stack"):
            card["in_your_stack"] = {"title": lesson["stack"][0], "code": lesson["stack"][1]}
        return card
