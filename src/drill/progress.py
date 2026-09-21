"""Your practice history, and the problem-selection logic built on top of it.

Stored as one JSON file (``.drill/progress.json`` by default) so you can read it,
diff it, and delete it without ceremony. MLflow records the same sessions in far
more detail; this file exists so problem selection does not need a tracking server
running to work.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from drill.problems import ALL_PROBLEMS, Problem, get_problem


@dataclass
class AttemptRecord:
    """One finished session on one problem."""

    problem_id: str
    topic: str
    solved: bool
    attempts: int
    hints_used: int
    duration_s: float
    timestamp: float


class ProgressStore:
    """Reads and writes the practice history."""

    def __init__(self, path: Path):
        self.path = Path(path)

    # -- persistence ---------------------------------------------------------

    def load(self) -> list[AttemptRecord]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # A corrupt history should never block practice. Start fresh instead.
            return []
        records = []
        for item in raw.get("attempts", []):
            try:
                records.append(AttemptRecord(**item))
            except TypeError:
                continue  # skip rows written by an older schema
        return records

    def record(self, attempt: AttemptRecord) -> None:
        history = self.load()
        history.append(attempt)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"attempts": [asdict(a) for a in history]}, indent=2),
            encoding="utf-8",
        )

    # -- what the history tells us ------------------------------------------

    def stats_by_topic(self) -> dict[str, dict[str, int]]:
        """Per topic: how many sessions, and how many you solved."""
        stats: dict[str, dict[str, int]] = {}
        for record in self.load():
            bucket = stats.setdefault(record.topic, {"attempted": 0, "solved": 0})
            bucket["attempted"] += 1
            bucket["solved"] += int(record.solved)
        return stats

    def solved_ids(self) -> set[str]:
        return {r.problem_id for r in self.load() if r.solved}

    def weakest_topic(self) -> str | None:
        """The topic with the worst solve rate among those you have tried.

        Ties break toward the topic you have practised least, so a single lucky
        solve does not retire a topic you barely know.
        """
        stats = self.stats_by_topic()
        if not stats:
            return None
        return min(
            stats.items(),
            key=lambda kv: (kv[1]["solved"] / kv[1]["attempted"], kv[1]["attempted"]),
        )[0]

    # -- selection -----------------------------------------------------------

    def choose_problem(
        self,
        problem_id: str | None = None,
        topic: str | None = None,
        rng: random.Random | None = None,
    ) -> Problem:
        """Pick what to practise next.

        The order of preference, and why:

        1. An explicit ``problem_id`` - you asked for it.
        2. Anything unsolved in ``topic``, if you named one.
        3. Anything unsolved in your weakest topic - spend time where you are worst.
        4. Any unsolved problem at all.
        5. Failing all that, everything is solved, so revisit at random.
        """
        rng = rng or random.Random()

        if problem_id:
            return get_problem(problem_id)

        solved = self.solved_ids()
        unsolved = [p for p in ALL_PROBLEMS if p.id not in solved]

        if topic:
            pool = [p for p in unsolved if p.topic == topic] or [
                p for p in ALL_PROBLEMS if p.topic == topic
            ]
            if not pool:
                raise KeyError(f"No problems with topic {topic!r}")
            return rng.choice(pool)

        weakest = self.weakest_topic()
        if weakest:
            pool = [p for p in unsolved if p.topic == weakest]
            if pool:
                return rng.choice(pool)

        return rng.choice(unsolved or list(ALL_PROBLEMS))


def new_attempt(
    problem: Problem, *, solved: bool, attempts: int, hints_used: int, duration_s: float
) -> AttemptRecord:
    return AttemptRecord(
        problem_id=problem.id,
        topic=problem.topic,
        solved=solved,
        attempts=attempts,
        hints_used=hints_used,
        duration_s=duration_s,
        timestamp=time.time(),
    )
