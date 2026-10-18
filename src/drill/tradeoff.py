"""Cost, speed and quality together: the pieces for comparing versions of the tutor.

The experiment (``notebooks/learning/cost_speed_quality.ipynb``) runs several versions of the tutor
on the same questions and scores every answer three ways: did it pass the judge, how long did it
take, and what did it cost. This module holds the parts that don't change between the notebook
and a live run:

- the tutor's Ask prompt as ``page/ask.js`` builds it today, split into the part that is the same
  for every question about a lesson and the part that changes;
- a **cacheable** version of the same prompt, to test as a version, not a change to the live tutor:
  everything fixed goes first, marked for the model's prompt cache, and only the question comes after;
- what an answer costs once the prompt cache is counted, the cache hit rate, the p95 time, the
  versions nothing beats (the Pareto front), and the decision rule written before the results.

Prices are :data:`drill.tutor_prepared.PRICES`. The cache rates are Anthropic's first-party ones for
the 5-minute cache; Databricks bills Claude in DBUs, so the exact charge can differ.
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterable

from drill import tutor_prepared as tp

INTRO = "You are a patient tutor helping with one lesson of an AI engineering course. "

# Reading a cached start costs a tenth of normal input; writing it the first time costs a quarter more.
CACHE_READ = 0.1
CACHE_WRITE = 1.25
CACHE_MINUTES = 5
# The shortest start a model will cache. It differs by model and some need more: check the provider's
# prompt-caching page for the model you test, and pass its number in.
MIN_CACHEABLE = 1024


def estimate_tokens(text: str) -> int:
    """Roughly four characters per token, as the server's fallback does. A real run reads the usage block."""
    return len(text) // 4 + 1


def rules(fn: str = "", practice: bool = False) -> str:
    """The tutor's rules, as ``page/ask.js`` writes them (``tests/test_tradeoff.py`` checks they match)."""
    lines = [
        "- Stay on this lesson's topic. If the question is unrelated, answer in one sentence and steer back.",
        (f"- Never write code for the lesson's coding exercise (`{fn}`), not even part of it, even if asked. If they ask "
         "about the exercise, explain the approach in words only and suggest the step-by-step hints in the Build step. "
         "Small code examples about other things are fine, in a ```python block."),
    ]
    if practice:
        lines.append("- The Practice step asks questions with one right option each. Never say which option is right: give a clue "
                     "that points at the evidence, and let them choose.")
    lines += [
        ("- If your last message asked them a question, their message is their answer: say what is right, fix what is "
         "not, then ask one more question."),
        ("- If they describe their own situation, answer for that situation, and say which part of the lesson applies "
         "and which part changes."),
        "- Only add a code example if it makes the answer clearer, and make sure it matches what you said.",
        "- Plain words, short paragraphs, under 180 words. Explain any jargon you use. Wrap identifiers in backticks.",
        "- Reply with the answer only.",
    ]
    return "Rules:\n" + "\n".join(lines)


def _exercise(data: dict, lid: str) -> dict:
    return next((p for p in data["bank"] if p["id"] == lid), {})


def parts(data: dict, lid: str, chip: dict) -> dict[str, str]:
    """One Ask request in three pieces: ``lesson`` (the same for every question on this lesson),
    ``question`` (what changes) and ``rules`` (the same again, but today it comes after the question)."""
    problem = _exercise(data, lid)
    question = f"They are on the {chip['step']} step of the lesson.\n\nTheir message: {chip['q']}\n"
    if chip.get("how"):
        question += f"How to answer: {chip['how']}\n"
    return {"lesson": INTRO + tp.LEARNER + "\n\n" + tp._context(data, lid),
            "question": question,
            "rules": rules(problem.get("fn") or "", bool(problem.get("practice")))}


def today_messages(data: dict, lid: str, chip: dict) -> list[dict]:
    """The prompt as the page sends it now: one message, the question in the middle, nothing marked for caching."""
    p = parts(data, lid, chip)
    return [{"role": "user", "content": f"{p['lesson']}\n\n{p['question']}\n{p['rules']}"}]


def cacheable_messages(data: dict, lid: str, chip: dict) -> list[dict]:
    """The version to test: lesson and rules first, marked for the prompt cache, then only the question."""
    p = parts(data, lid, chip)
    return [{"role": "system", "content": [{"type": "text", "text": f"{p['lesson']}\n\n{p['rules']}",
                                            "cache_control": {"type": "ephemeral"}}]},
            {"role": "user", "content": p["question"]}]


def fixed_start(data: dict, lid: str, chip: dict, version: str = "today") -> int:
    """Tokens at the start of the prompt that are the same for every question on this lesson."""
    p = parts(data, lid, chip)
    return estimate_tokens(p["lesson"] if version == "today" else f"{p['lesson']}\n\n{p['rules']}")


# -- cost, the cache and speed -------------------------------------------------------------------

def answer_cost(model: str, input_tokens: int, output_tokens: int, cache_read: int = 0, cache_write: int = 0) -> float:
    """Dollars for one answer. ``input_tokens`` is the input that was neither read from nor written to the
    cache, as Claude's usage block counts it."""
    pin, pout = tp.PRICES.get(model, (0.0, 0.0))
    return (input_tokens * pin + cache_read * pin * CACHE_READ + cache_write * pin * CACHE_WRITE + output_tokens * pout) / 1e6


def hit_rate(rows: Iterable[dict]) -> float:
    """Share of all input tokens that were read from the cache."""
    read = total = 0
    for r in rows:
        read += r.get("cache_read", 0)
        total += r.get("input_tokens", 0) + r.get("cache_read", 0) + r.get("cache_write", 0)
    return read / total if total else 0.0


def percentile(times: list[float], p: float) -> float:
    """The time that p out of 100 requests finish within (nearest rank)."""
    if not times:
        return 0.0
    ordered = sorted(times)
    return ordered[max(1, math.ceil(len(ordered) * p / 100)) - 1]


def cache_pass(order: list[dict], start_tokens: dict[str, int], minimum: int = MIN_CACHEABLE,
               minutes: float = CACHE_MINUTES) -> list[dict]:
    """Which calls would read the cache, written or missed, in the order they were sent.

    ``order`` items have ``lesson_id`` and ``at`` (seconds); ``start_tokens`` is each lesson's fixed start.
    A start shorter than ``minimum`` is never cached. Reading it keeps it alive for another ``minutes``."""
    alive: dict[str, float] = {}
    out = []
    for call in order:
        lid, at, size = call["lesson_id"], call["at"], start_tokens[call["lesson_id"]]
        if size < minimum:
            out.append({"cache_read": 0, "cache_write": 0})
        elif lid in alive and at - alive[lid] <= minutes * 60:
            out.append({"cache_read": size, "cache_write": 0})
        else:
            out.append({"cache_read": 0, "cache_write": size})
        if size >= minimum:
            alive[lid] = at
    return out


# -- comparing versions --------------------------------------------------------------------------

def beats(a: dict, b: dict) -> bool:
    """``a`` is at least as good as ``b`` on quality, cost and p95 time, and better on at least one."""
    as_good = a["quality"] >= b["quality"] and a["cost"] <= b["cost"] and a["p95"] <= b["p95"]
    better = a["quality"] > b["quality"] or a["cost"] < b["cost"] or a["p95"] < b["p95"]
    return as_good and better


def pareto(versions: list[dict]) -> list[str]:
    """The names of the versions nothing beats."""
    return [v["name"] for v in versions if not any(beats(o, v) for o in versions if o is not v)]


def paired_difference(base: dict[tuple, bool], new: dict[tuple, bool], n_boot: int = 1000, seed: int = 7) -> tuple[float, float, float]:
    """New pass rate minus base, on the same questions, with a 95% interval from resampling whole lessons.
    Keys are ``(lesson_id, key)``; only questions both versions answered count."""
    shared = sorted(set(base) & set(new))
    by_lesson: dict[str, list[tuple]] = {}
    for k in shared:
        by_lesson.setdefault(k[0], []).append(k)
    lessons = list(by_lesson)

    def diff(keys: list[tuple]) -> float:
        return sum(new[k] - base[k] for k in keys) / len(keys) if keys else 0.0

    rng = random.Random(seed)
    boots = sorted(diff([k for l in (rng.choice(lessons) for _ in lessons) for k in by_lesson[l]]) for _ in range(n_boot))
    return diff(shared), boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]


def choose(versions: list[dict], margin: float, p95_limit: float) -> dict:
    """The decision rule: quality no worse than the baseline by more than ``margin`` (the lower end of the
    paired interval, ``diff_low``), the slow case under ``p95_limit``, then the cheapest of what's left."""
    passed = [v for v in versions if v["diff_low"] >= -margin and v["p95"] <= p95_limit]
    reasons = {v["name"]: ("quality" if v["diff_low"] < -margin else "speed") for v in versions if v not in passed}
    best = min(passed, key=lambda v: (v["cost"], v["p95"]))["name"] if passed else None
    return {"choice": best, "kept": [v["name"] for v in passed], "dropped": reasons}
