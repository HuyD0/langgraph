"""Answer key for notebooks/m13_evaluating_the_tutor.ipynb (the same logic as drill.tutor_prepared_eval)."""

import math

PATTERN = ["dev", "dev", "dev", "test", "holdout"]


def deal_by_phase(lessons_by_phase):
    """Each phase's lessons dealt across dev, test and holdout in the pattern above."""
    dealt = {}
    for lessons in lessons_by_phase.values():
        for count, lesson in enumerate(lessons):
            dealt[lesson] = PATTERN[count % 5]
    return dealt


def wilson(passed, n, z=1.96):
    """The pass rate and its Wilson 95% interval."""
    if not n:
        return 0.0, 0.0, 0.0
    p = passed / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, max(0.0, centre - half), min(1.0, centre + half)


def kappa(a, b):
    """Cohen's kappa between two judges' pass/fail verdicts."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    if chance >= 1:
        return None
    return (observed - chance) / (1 - chance)


def catch_and_keep(answers):
    """How often the new judge matches the reference on its failures, and on its passes."""
    failed = [a for a in answers if not a["reference_pass"]]
    passed = [a for a in answers if a["reference_pass"]]
    return {"catch": (sum(not a["passes"] for a in failed), len(failed)),
            "keep": (sum(a["passes"] for a in passed), len(passed))}


def mcnemar(b, c):
    """The exact two-sided McNemar p-value from the disagreements alone."""
    n = b + c
    if not n:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)
