"""Answers for notebooks/learning/evaluating_the_tutor.ipynb. For learning: not run in CI. (Same logic as drill.tutor_prepared_eval.)"""

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


def confusion(judge, reference):
    """The four boxes and three rates, where 'positive' means the answer FAILED (a problem was flagged)."""
    caught = sum(not j and not r for j, r in zip(judge, reference))
    false_alarm = sum(not j and r for j, r in zip(judge, reference))
    missed = sum(j and not r for j, r in zip(judge, reference))
    let_through = sum(j and r for j, r in zip(judge, reference))
    share = lambda top, bottom: top / bottom if bottom else None  # noqa: E731
    return {"caught": caught, "false_alarm": false_alarm, "missed": missed, "let_through": let_through,
            "recall": share(caught, caught + missed), "precision": share(caught, caught + false_alarm),
            "specificity": share(let_through, let_through + false_alarm)}


def ac1(a, b):
    """Gwet's AC1 between two judges' pass/fail verdicts."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    q = (sum(a) / n + sum(b) / n) / 2
    chance = 2 * q * (1 - q)
    if chance >= 1:
        return None
    return (observed - chance) / (1 - chance)


def holm(pvalues):
    """Holm-adjusted p-values, in the same order as given."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    previous = 0.0
    for rank, i in enumerate(order):
        previous = max(previous, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = previous
    return adjusted


def stratified(rows, n, by, rare):
    """Every rare row, then the rest of n spread across the `by` groups in proportion, in order_key order."""
    import hashlib

    order_key = lambda row: hashlib.sha256(f"{row['lesson_id']}/{row['key']}".encode()).hexdigest()  # noqa: E731
    rare_rows = [r for r in rows if rare(r)]
    common = [r for r in rows if not rare(r)]
    want = max(0, n - len(rare_rows))
    groups = {}
    for r in common:
        groups.setdefault(tuple(r[k] for k in by), []).append(r)
    taken = []
    for _, items in sorted(groups.items()):
        items = sorted(items, key=order_key)
        taken += items[:round(want * len(items) / max(1, len(common)))]
    return rare_rows + taken


def allowed_to_look(split, looks_so_far, big_decision=False):
    """The rule for each split: dev any time; test once per candidate; holdout once, for a big decision."""
    if split == "dev":
        return True
    if split == "test":
        return looks_so_far == 0
    return big_decision and looks_so_far == 0
