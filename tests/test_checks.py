"""The Check step's extra questions (content/checks/): real lessons, one plain question each, three
believable options, a clue that doesn't give the answer away. The writing rules are in
content/checks/__init__.py; these are the ones a test can see."""
from __future__ import annotations

import re

from drill.content import build_data, modules
from drill.content.checks import more_checks

# Words that make a beginner stop: maths notation and jargon the lessons don't use in Check.
HARD = re.compile(r"\bO\(|\b(?:asymptotic|heuristic|idempotent|orthogonal|aforementioned|utili[sz]e)\b", re.I)


def test_extra_questions_belong_to_real_lessons_and_follow_the_rules():
    lessons = {l["id"]: l for m in modules.load() for l in m.lessons}
    more = more_checks()
    assert more, "at least one module has more questions"
    for lid, asks in more.items():
        assert lid in lessons, f"content/checks names a lesson that doesn't exist: {lid}"
        assert 1 <= len(asks) <= 2, f"{lid}: one or two more questions (three in all)"
        texts = [lessons[lid]["check"]["question"]] + [a["question"] for a in asks]
        assert len(set(texts)) == len(texts), f"{lid}: a question repeats"
        for a in asks:
            q, opts = a["question"], a["options"]
            assert len(opts) == 3 and len(set(opts)) == 3, f"{lid}: three different options"
            assert 0 <= a["answer"] < 3 and a["clue"] and a["why"], f"{lid}: {q[:40]}"
            assert len(q) <= 240, f"{lid}: keep the question short ({len(q)} characters): {q[:60]}"
            assert all(len(o) <= 60 for o in opts), f"{lid}: keep options short: {opts}"
            assert max(map(len, opts)) <= 3 * min(map(len, opts)) + 10, f"{lid}: options of very different lengths give the answer away: {opts}"
            assert len(a["why"]) <= 300, f"{lid}: one or two sentences of why"
            for text in [q, *opts, a["clue"], a["why"]]:
                assert not HARD.search(text), f"{lid}: plain words, please: {text[:80]}"


def test_the_page_gets_every_question_with_its_clue():
    data = build_data()
    for lid, asks in more_checks().items():
        page = data["lessons"][lid]["more"]
        assert [p[0] for p in page] == [a["question"] for a in asks] and all(p[4] for p in page)


def test_question_one_is_not_answered_by_option_length():
    """Every lesson's own Check question (question 1): the right option is no longer than 1.3 times
    the longest wrong one plus 10 characters, so the longest answer is never a giveaway."""
    too_long = []
    for m in modules.load():
        for lesson in m.lessons:
            check = lesson["check"]
            right = check["options"][check["answer"]]
            wrong = [o for i, o in enumerate(check["options"]) if i != check["answer"]]
            limit = 1.3 * max(map(len, wrong)) + 10
            if len(right) > limit:
                too_long.append(f"{lesson['id']}: right {len(right)} chars, longest wrong {max(map(len, wrong))}: {check['options']}")
    assert not too_long, "the right option gives itself away by length:\n" + "\n".join(too_long)


def test_no_checks_file_lists_a_lesson_twice():
    """Two branches appending to the same checks file merge by union (.gitattributes), which could leave
    the same lesson id in one CHECKS dict twice; a Python dict literal would silently keep the last."""
    import ast
    from pathlib import Path

    for path in sorted((Path(__file__).resolve().parents[1] / "src" / "drill" / "content" / "checks").glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                keys = [k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
                dupes = sorted({k for k in keys if keys.count(k) > 1})
                assert not dupes, f"{path.name}: listed twice: {dupes}"

