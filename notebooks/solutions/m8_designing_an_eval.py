"""Milestone 8 answer key - scoring by group, pairing two setups, and the bootstrap."""

from __future__ import annotations

import random


def group_counts(results):
    """A dict of running totals, one entry per group: the aggregation pattern from milestone 4."""
    counts = {}
    for group, passed in results:
        if group not in counts:
            counts[group] = [0, 0]
        counts[group][1] += 1
        if passed:
            counts[group][0] += 1
    return counts


def paired_counts(a_passed, b_passed):
    """Only disagreements say anything about which setup is better."""
    a_only = 0
    b_only = 0
    for a, b in zip(a_passed, b_passed):
        if a and not b:
            a_only += 1
        elif b and not a:
            b_only += 1
    return [a_only, b_only]


def bootstrap_range(values, draws, seed):
    """Rebuild the eval set `draws` times, with repeats allowed, and keep the middle 95%.

    A seeded random.Random makes the answer repeatable: run it twice, get the same range.
    """
    if not values:
        return [0.0, 0.0]
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(draws):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    cut = int(draws * 0.025)
    return [round(means[cut], 3), round(means[draws - 1 - cut], 3)]
