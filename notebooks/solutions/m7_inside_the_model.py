"""Milestone 7 answer key - inside the model: choosing words, speed, size, fair comparisons."""

from __future__ import annotations


def greedy_pick(choices):
    """The "best so far" pattern from milestone 0, over a dict instead of a list.

    max(choices, key=choices.get) is the one-line version; the loop is here so
    you can see it is the same idea.
    """
    best_word = None
    best_chance = -1.0
    for word, chance in choices.items():
        if chance > best_chance:
            best_word, best_chance = word, chance
    return best_word


def keep_top_k(choices, k):
    """Sort most-likely first, slice off the first k, then share out to 1 again."""
    ranked = sorted(choices.items(), key=lambda pair: pair[1], reverse=True)
    return normalize(dict(ranked[:k]))  # noqa: F821 - normalize is given in the notebook


def keep_top_p(choices, p):
    """Add words most-likely first until their chances reach p, then stop.

    Unlike top-k, the number kept changes with the prompt: one word when the
    model is sure, many when it is not. That is the whole point of top-p.
    """
    ranked = sorted(choices.items(), key=lambda pair: pair[1], reverse=True)
    kept = {}
    total = 0.0
    for word, chance in ranked:
        kept[word] = chance
        total += chance
        if total >= p:
            break
    return normalize(kept)  # noqa: F821 - normalize is given in the notebook


def speeds(stats):
    """Count divided by seconds, twice. Ollama reports time in nanoseconds."""
    reading_seconds = stats["prompt_eval_duration"] / 1_000_000_000
    writing_seconds = stats["eval_duration"] / 1_000_000_000
    return {
        "reading": stats["prompt_eval_count"] / reading_seconds,
        "writing": stats["eval_count"] / writing_seconds,
    }


def weights_size_gb(billions, bits):
    """Each number takes bits / 8 bytes, and a billion bytes is a gigabyte."""
    return billions * bits / 8


def verdict(a_runs, b_runs):
    """Only call a winner when the ranges do not overlap at all.

    A blunt rule, and deliberately so: it cannot be fooled by one lucky run.
    """
    if min(a_runs) > max(b_runs):
        return "A"
    if min(b_runs) > max(a_runs):
        return "B"
    return "too close to call"
