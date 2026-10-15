"""The lessons and exercises the Daily Drill page shows, for the server and the MCP tools.

The content is :func:`drill.content.build_data`, the same dict the page embeds, so the page
and the tools can never disagree about what a lesson is.
"""

from __future__ import annotations

from drill.content import build_data, render_page


class Bank:
    """Modules in path order, lessons by id, exercises by id."""

    def __init__(self, data: dict, packs: list | None = None):
        self.data = data
        self.packs = packs or []  # content packs shown on this server (DRILL_CONTENT_PACKS)
        self.modules: list[dict] = data["modules"]
        self.lessons: dict[str, dict] = data["lessons"]
        self.problems: dict[str, dict] = {p["id"]: p for p in data["bank"]}
        self.learn: dict[str, dict] = data.get("learn", {})
        self._page: str | None = None

    @classmethod
    def load(cls) -> "Bank":
        """The curriculum, plus any content packs ``DRILL_CONTENT_PACKS`` names (none by default)."""
        from drill.content import modules
        from drill.content.packs import load_packs

        loaded = modules.load()
        packs = load_packs(taken={lesson["id"] for m in loaded for lesson in m.lessons})
        return cls(build_data(loaded, packs), packs)

    def pack_asset(self, pack_id: str, path: str) -> str | None:
        """The file on disk for one of a loaded pack's assets, or ``None``: only files its lessons name."""
        pack = next((p for p in self.packs if p.id == pack_id), None)
        return pack.assets.get(path) if pack else None

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
        question, options, answer, why = lesson["check"][:4]
        pattern, text, say, classic = lesson["angle"][:4]
        if problem.get("practice") and lesson.get("pack"):  # a content-pack lesson: a practice exercise, not code
            extra = lesson["pack"]
            return {
                "id": lesson_id, "title": lesson["title"], "module": module.get("title"), "learn": lesson["learn"],
                "objective": extra["objective"],
                "check": {"question": question, "options": options, "answer_index": answer, "why": why},
                "practice": {"kind": extra["practice"]["kind"], "prompt": extra["practice"]["prompt"]},
                "explain": {"reasoning": text, "say_it_like_this": say},
            }
        cases = problem.get("cases", [])
        sample = next((c for c in cases if c.get("sample")), cases[0] if cases else None)
        card = {
            "id": lesson_id,
            "title": lesson["title"],
            "module": module.get("title"),
            "learn": lesson["learn"],
            "example": {"title": lesson["example"][0], "text": lesson["example"][1]},
            "check": {"question": question, "options": options, "answer_index": answer, "why": why},
            "more_checks": [{"question": q, "options": o, "answer_index": r, "why": w, "clue": c} for q, o, r, w, c in lesson.get("more") or []],
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
