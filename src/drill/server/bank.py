"""The lessons and exercises the Daily Drill page shows, for the server and the MCP tools.

The content is :func:`drill.content.build_data`, the same dict the page embeds, so the page
and the tools can never disagree about what a lesson is.
"""

from __future__ import annotations

from drill.content import build_data, render_page


class Bank:
    """Modules in path order, lessons by id, exercises by id."""

    def __init__(self, data: dict):
        self.data = data
        self.modules: list[dict] = data["modules"]
        self.lessons: dict[str, dict] = data["lessons"]
        self.problems: dict[str, dict] = {p["id"]: p for p in data["bank"]}
        self.learn: dict[str, dict] = data.get("learn", {})
        self._page: str | None = None

    @classmethod
    def load(cls) -> "Bank":
        return cls(build_data())

    @property
    def page(self) -> str:
        """The page with this content embedded, rendered once."""
        if self._page is None:
            self._page = render_page(self.data)
        return self._page

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
