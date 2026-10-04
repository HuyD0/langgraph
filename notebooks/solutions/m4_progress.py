"""Milestone 4 answer key - aggregating practice history."""

from __future__ import annotations


def stats_by_topic(history: list) -> dict[str, dict[str, int]]:
    """Group records by topic, counting attempts and solves.

    ``setdefault`` creates the bucket on first sight of a topic, which keeps the
    result free of zero-rows for topics that never appear.
    """
    stats: dict[str, dict[str, int]] = {}
    for record in history:
        bucket = stats.setdefault(record.topic, {"attempted": 0, "solved": 0})
        bucket["attempted"] += 1
        bucket["solved"] += int(record.solved)
    return stats


def weakest_topic(history: list) -> str | None:
    """The topic with the worst solve rate, breaking ties toward least practised.

    The tuple key is the whole trick: ``min`` compares the first element, and only
    consults the second when the first ties. So rate decides, and attempt count
    settles a draw - which stops one lucky solve from retiring a topic.
    """
    stats = stats_by_topic(history)
    if not stats:
        return None
    return min(
        stats.items(),
        key=lambda kv: (kv[1]["solved"] / kv[1]["attempted"], kv[1]["attempted"]),
    )[0]


def unsolved_ids(history: list, all_ids: list[str]) -> list[str]:
    """Ids never solved, in the order given.

    Building the solved set first makes this one pass over ``all_ids`` instead of
    a scan of the history per id.
    """
    solved = {r.problem_id for r in history if r.solved}
    return [i for i in all_ids if i not in solved]
