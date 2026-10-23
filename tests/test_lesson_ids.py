"""Lesson ids are the contract with everything outside this repository.

Learners' progress is saved under them (on this device and in the claude.ai account), and a content
pack's lessons name core lessons by id in ``prerequisites``. So an id, once shipped, is never reused
or removed: tests/fixtures/lesson_ids.txt lists every id ever shipped (append-only), and a renamed
lesson keeps its old id in ``modules.ALIASES``, which the page and the packs both honour.
"""

from __future__ import annotations

from pathlib import Path

from drill.content import modules

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "lesson_ids.txt"


def shipped() -> list[str]:
    return [line.strip() for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def current() -> set[str]:
    return {lesson["id"] for m in modules.load() for lesson in m.lessons}


def test_every_id_ever_shipped_still_resolves():
    ids = shipped()
    assert len(ids) == len(set(ids)), "an id is listed twice in tests/fixtures/lesson_ids.txt"
    gone = sorted(i for i in ids if i not in current() and i not in modules.ALIASES)
    assert not gone, ("these ids were shipped, so learners may have progress under them and packs may name them: "
                      f"{gone}. Renamed? add old: new to modules.ALIASES. Never remove a lesson id.")


def test_every_current_id_is_on_the_list():
    missing = sorted(current() - set(shipped()))
    assert not missing, f"new lesson ids: append them to tests/fixtures/lesson_ids.txt, one per line: {missing}"


def test_aliases_point_at_current_lessons_and_never_shadow_one():
    for old, new in modules.ALIASES.items():
        assert new in current(), f"ALIASES[{old!r}] = {new!r}, which is not a lesson"
        assert old not in current(), f"{old!r} is a current lesson and an alias at once"
        assert old in shipped(), f"{old!r} was never shipped, so nothing needs the alias"
