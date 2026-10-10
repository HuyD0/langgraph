"""Builds the money & health track for the browser practice page.

Only made-up data goes into the export (see :mod:`drill.mine.fake`). Each problem
gets its hand-written test cases plus one larger look-alike case, with the
expected answer worked out by the reference solution.

    uv run python -m drill.mine.export > mine.json
"""

from __future__ import annotations

import copy
import json

from drill.mine.fake import fake_args
from drill.mine.learn import LEARN
from drill.mine.problems import MINE_PROBLEMS, REAL_WORLD


def _reference_answer(problem, args):
    namespace: dict = {}
    exec(compile(problem.reference_solution, "<reference>", "exec"), namespace)
    return namespace[problem.function_name](*copy.deepcopy(args))


def page_track() -> dict:
    problems = []
    for p in MINE_PROBLEMS:
        cases = [{"args": list(tc.args), "expected": tc.expected, "sample": tc.is_sample}
                 for tc in p.test_cases]
        args = fake_args(p.id)
        cases.append({"args": list(args), "expected": _reference_answer(p, args), "sample": False})
        problems.append({
            "id": p.id, "title": p.title, "topic": p.topic, "difficulty": p.difficulty,
            "pattern": p.pattern, "target": p.target_complexity, "prompt": p.prompt,
            "fn": p.function_name, "starter": p.starter_code, "solution": p.reference_solution,
            "unordered": p.unordered, "realworld": REAL_WORLD[p.id], "track": "mine",
            "cases": json.loads(json.dumps(cases)),
        })
    return {"problems": problems, "learn": LEARN}


if __name__ == "__main__":
    print(json.dumps(page_track(), separators=(",", ":")))
