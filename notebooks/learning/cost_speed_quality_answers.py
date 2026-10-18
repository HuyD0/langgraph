"""Answers for notebooks/learning/cost_speed_quality.ipynb. For learning: not run in CI. (Same logic as drill.tradeoff.)"""

import math

from drill import tradeoff as t
from drill import tutor_prepared as tp


def answer_cost(model, input_tokens, output_tokens, cache_read=0, cache_write=0):
    """Dollars for one answer, with the prompt cache counted."""
    pin, pout = tp.PRICES.get(model, (0.0, 0.0))
    return (input_tokens * pin + cache_read * pin * t.CACHE_READ + cache_write * pin * t.CACHE_WRITE + output_tokens * pout) / 1e6


def hit_rate(rows):
    """Share of all input tokens that were read from the cache."""
    read = total = 0
    for r in rows:
        read += r.get("cache_read", 0)
        total += r.get("input_tokens", 0) + r.get("cache_read", 0) + r.get("cache_write", 0)
    return read / total if total else 0.0


def percentile(times, p):
    """The time that p out of 100 requests finish within (nearest rank)."""
    if not times:
        return 0.0
    ordered = sorted(times)
    return ordered[max(1, math.ceil(len(ordered) * p / 100)) - 1]


def pareto(versions):
    """The names of the versions nothing beats."""
    return [v["name"] for v in versions if not any(t.beats(other, v) for other in versions if other is not v)]


def choose(versions, margin, p95_limit):
    """Quality first, then speed, then the cheapest of what's left."""
    dropped, kept = {}, []
    for v in versions:
        if v["diff_low"] < -margin:
            dropped[v["name"]] = "quality"
        elif v["p95"] > p95_limit:
            dropped[v["name"]] = "speed"
        else:
            kept.append(v)
    best = min(kept, key=lambda v: (v["cost"], v["p95"]))["name"] if kept else None
    return {"choice": best, "kept": [v["name"] for v in kept], "dropped": dropped}


def match_by_id(rows, outputs):
    """Each request's answer by its custom_id, or None if it failed or never came back."""
    found = {o["custom_id"]: o.get("text") for o in outputs if "text" in o}
    return {r["custom_id"]: found.get(r["custom_id"]) for r in rows}
