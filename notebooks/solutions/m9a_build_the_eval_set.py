"""Milestone 9a answer key - checking an answer against expected facts, and a stratified split."""

from __future__ import annotations


def has_facts(answer, facts):
    """Every fact must appear somewhere in the answer; " | " separates acceptable wordings."""
    text = answer.lower()
    for fact in facts:
        options = [option.strip().lower() for option in fact.split("|")]
        if not any(option in text for option in options):
            return False
    return True


def deal_splits(ids_by_group):
    """Deal each group's ids 3-1-1, in order, so every split gets every group in proportion."""
    pattern = ["dev", "dev", "dev", "test", "holdout"]
    split = {}
    for ids in ids_by_group.values():
        for position, qid in enumerate(ids):
            split[qid] = pattern[position % len(pattern)]
    return split
