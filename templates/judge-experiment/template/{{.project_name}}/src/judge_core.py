"""The experiment's logic in plain Python: synthetic failures, the can-it-fail gate, code checks, votes and the numbers.

No Spark and no model here, so it runs and tests on a laptop. The task files (check_set.py, judge.py, report.py) read
and write the tables and call this.

An eval set row is a dict with: id, group, context, question, answer, and optionally expected_pass (True or False when a
person or a planted mistake says so, None when nobody has). Planted rows also carry `planted` (the kind of mistake).
"""

from __future__ import annotations

import math
import random
import re
from typing import Any

SEED = 7

# -- synthetic failures: a good answer with one rule broken on purpose ------------------------------------------------
# One kind per way an answer can fail. A real past failure is better than any of these: replace them as you collect
# real ones, and report each kind on its own, because a planted mistake is usually plainer than a real one.
PLANT_KINDS = ("wrong_answer", "wrong_number", "made_up_fact", "not_standalone")
MADE_UP = " This rule was introduced in 1987 by the European Commission and applies in every country."
_NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")


def change_number(answer: str) -> str | None:
    """The answer with its first number multiplied by ten, or None if it has no number."""
    m = _NUMBER.search(answer)
    if not m:
        return None
    n = m.group(1)
    new = f"{float(n) * 10:g}" if "." in n else str(int(n) * 10)
    return answer[:m.start()] + new + answer[m.end():]


def plant(kind: str, row: dict, donor: dict | None = None) -> dict | None:
    """``row`` with one rule broken, or None when the kind can't apply to it."""
    out = {**row, "id": f"plant:{kind}:{row['id']}", "planted": kind, "expected_pass": False}
    if kind == "wrong_answer":
        if donor is None or donor["id"] == row["id"]:
            return None
        out["answer"] = donor["answer"]  # an answer to a different question
    elif kind == "wrong_number":
        changed = change_number(row["answer"])
        if changed is None:
            return None
        out["answer"] = changed
    elif kind == "made_up_fact":
        out["answer"] = row["answer"].rstrip() + MADE_UP
    elif kind == "not_standalone":
        out["answer"] = ("As I said in my last message, this follows on from your earlier question.\n\n" + row["answer"]
                         + "\n\nReply and tell me which part you want next.")
    else:
        raise ValueError(f"unknown kind {kind}")
    return out


def plants(rows: list[dict], per_kind: int, seed: int = SEED) -> list[dict]:
    """Up to ``per_kind`` planted rows of each kind, built from good rows (expected_pass not False), the same every run."""
    good = sorted((r for r in rows if r.get("expected_pass") is not False and not r.get("planted")), key=lambda r: r["id"])
    rng = random.Random(seed)
    out = []
    for kind in PLANT_KINDS:
        order = good[:]
        rng.shuffle(order)
        made = 0
        for i, row in enumerate(order):
            if made == per_kind:
                break
            donor = order[(i + 1) % len(order)] if kind == "wrong_answer" else None
            p = plant(kind, row, donor)
            if p is not None:
                out.append(p)
                made += 1
    return out


# -- the gate: can this set fail? --------------------------------------------------------------------------------------
def measurable(rows: list[dict], need: int) -> dict[str, Any]:
    """Count the known-bad rows (planted, or labelled bad), overall and per group. ``ok`` is False when there are
    fewer than ``need``: a catch rate measured on fewer would have a range too wide to decide anything."""
    bad = [r for r in rows if r.get("expected_pass") is False]
    by_kind: dict[str, int] = {}
    by_group: dict[str, int] = {}
    for r in bad:
        k = r.get("planted") or "labelled"
        by_kind[k] = by_kind.get(k, 0) + 1
        by_group[r.get("group") or "?"] = by_group.get(r.get("group") or "?", 0) + 1
    return {"ok": len(bad) >= need, "known_bad": len(bad), "need": need,
            "labelled_good": sum(1 for r in rows if r.get("expected_pass") is True),
            "by_kind": dict(sorted(by_kind.items())), "by_group": dict(sorted(by_group.items()))}


# -- code checks: rules a computer can check, so no judge has to ------------------------------------------------------
LEANS_ON_CHAT = re.compile(r"\b(as I said|as mentioned (earlier|before)|in my last message|reply and tell me)\b", re.I)


def code_checks(answer: str, max_words: int) -> dict[str, Any]:
    """Each rule's result and whether all pass. Add your own rules here: anything a regex or a count can decide."""
    words = len(answer.split())
    checks = {"short_enough": words <= max_words, "stands_alone": not LEANS_ON_CHAT.search(answer)}
    return {"pass": all(checks.values()), "words": words, **checks}


# -- votes ----------------------------------------------------------------------------------------------------------------
def consensus(votes: list[bool | None]) -> tuple[bool | None, bool]:
    """The jury's verdict and whether it split. Unread votes (None) don't count. A pass needs more than half; a tie is
    not a pass, and it is a split."""
    counted = [v for v in votes if v is not None]
    if not counted:
        return None, False
    passes = sum(counted)
    return passes * 2 > len(counted), 0 < passes < len(counted)


# -- the numbers ----------------------------------------------------------------------------------------------------------
def wilson(hits: int, n: int, z: float = 1.96) -> dict[str, float]:
    """A share with its 95% range (Wilson), safe for small counts and for 0 or n hits."""
    if n == 0:
        return {"rate": 0.0, "low": 0.0, "high": 0.0, "n": 0}
    p = hits / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"rate": round(p, 3), "low": round(max(0.0, c - h), 3), "high": round(min(1.0, c + h), 3), "n": n}


def kappa(a: list[bool], b: list[bool]) -> float | None:
    """Cohen's kappa: agreement beyond chance. None when chance agreement is total (one side always says the same)."""
    n = len(a)
    if not n:
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    return None if chance == 1 else round((observed - chance) / (1 - chance), 3)


def mcnemar(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value from the disagreements: ``b`` items only the first got right, ``c`` only the
    second. Small p: the difference is unlikely to be luck."""
    n = b + c
    if not n:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n)


def scores(verdicts: list[bool | None], truth: list[bool | None]) -> dict[str, Any]:
    """How one judge did where the right verdict is known: catches of known-bad rows, keeps of known-good rows."""
    pairs = [(v, t) for v, t in zip(verdicts, truth) if t is not None and v is not None]
    bad = [v for v, t in pairs if t is False]
    good = [v for v, t in pairs if t is True]
    catch, keep = wilson(sum(not v for v in bad), len(bad)), wilson(sum(good), len(good))
    # Balanced accuracy needs both halves: with no known-good answers the keep rate is unknown, so it stays empty.
    return {"catch": catch, "keep": keep, "balanced": round((catch["rate"] + keep["rate"]) / 2, 3) if good and bad else None,
            "kappa": kappa([v for v, _ in pairs], [t for _, t in pairs]),
            "unread": sum(v is None for v, t in zip(verdicts, truth) if t is not None)}


def compare(first: list[bool | None], second: list[bool | None], truth: list[bool | None]) -> dict[str, Any]:
    """Two judges on the same rows with a known answer: who was right where the other was wrong, and is it luck?"""
    only_first = only_second = 0
    for a, b, t in zip(first, second, truth):
        if t is None or a is None or b is None:
            continue
        only_first += (a == t) and (b != t)
        only_second += (b == t) and (a != t)
    return {"only_first_right": only_first, "only_second_right": only_second, "p_value": round(mcnemar(only_first, only_second), 4)}
