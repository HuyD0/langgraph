"""More Check questions: up to two more for each lesson, after the lesson's own.

The lesson's own question (``check=question(...)`` in its module file) stays question 1. The
ones here follow it on the page, one at a time, like Practice: a wrong pick is crossed out, help
is the clue first, then the answer.

One file per module, named like the module's file in ``modules/``, each with::

    CHECKS = {"lesson_id": [ask(...), ask(...)]}

How to write one (the learner is new to coding; tests/test_checks.py checks the rules it can):

- **Use the idea, don't recite it.** A small situation ("Your filter flagged 10 emails...") and a
  choice: spot the mistake, pick the next step, say which one fits. Never "which sentence did the
  lesson say".
- **Plain words.** Short sentences, everyday words, the real term explained if it's new. No maths
  notation, no Big-O. Read it aloud: it should sound like a colleague asking.
- **Three options**, all believable, about the same length, none a joke. Only one is right.
- **A clue** that points at the answer without saying it, and a **why** of one or two sentences
  that says why the right one is right.
- **Different from question 1** and from each other: a new situation, not the same one reworded.
"""
from __future__ import annotations

import importlib
import pkgutil
from functools import cache


@cache
def more_checks() -> dict[str, list[dict]]:
    """Every lesson's extra questions, by lesson id."""
    out: dict[str, list[dict]] = {}
    for info in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"{__name__}.{info.name}")
        for lesson_id, asks in mod.CHECKS.items():
            assert lesson_id not in out, f"{lesson_id} has more questions in two files"
            out[lesson_id] = asks
    return out
