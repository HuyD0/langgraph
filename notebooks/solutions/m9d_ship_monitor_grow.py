"""Milestone 9d answer key - a monitoring signal, and growing a split without breaking it."""

from __future__ import annotations


def decline_rates(rows):
    """Share of "I don't know" answers per group, from (group, declined) pairs."""
    totals, declines = {}, {}
    for group, declined in rows:
        totals[group] = totals.get(group, 0) + 1
        declines[group] = declines.get(group, 0) + (1 if declined else 0)
    return {group: round(declines[group] / totals[group], 2) for group in totals}


def deal_more(counts, new_ids_by_group):
    """Deal new ids into dev / test / holdout, carrying on each group's pattern where it left off."""
    pattern = ["dev", "dev", "dev", "test", "holdout"]
    split = {}
    for group, ids in new_ids_by_group.items():
        start = counts.get(group, 0)
        for offset, qid in enumerate(ids):
            split[qid] = pattern[(start + offset) % len(pattern)]
    return split
