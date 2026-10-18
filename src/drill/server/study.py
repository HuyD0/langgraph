"""The study list: when an item is due for review, and merging two copies of the list.

The page keeps the list in one of two places, and they cannot see each other: the claude.ai
page's own database, and this Mac's store when the page is served by ``drill-server``. Both
hold the same items at ``study/<id>``, so two copies merge by id. An item in only one copy
is added to the other; an item in both keeps whichever copy changed last (``updatedAt``,
else ``createdAt``). A removed item is not remembered, so remove it from both copies.

    uv run drill study export study.json     # this Mac's list, as one JSON file
    uv run drill study import study.json     # merge a list (a file, or a folder of item files) into it

Reviews: an item marked "Got it" comes back after 3 days, then 10, 30 and 90 while you keep
remembering it (``stage`` counts the reviews passed, ``reviewAt`` is when it is next due).
The page does the scheduling; ``is_due`` here lets the MCP tools show the same list.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from drill.server.store import DocStore

REVIEW_DAYS = (3, 10, 30, 90)  # the page's REVIEW_DAYS; keep the two the same


def changed_at(item: dict) -> float:
    return float(item.get("updatedAt") or item.get("createdAt") or 0)


def is_due(item: dict, now_ms: float | None = None) -> bool:
    """A "Got it" item whose next review time has come (one with no time yet is due now)."""
    now_ms = time.time() * 1000 if now_ms is None else now_ms
    return item.get("status") == "got" and float(item.get("reviewAt") or 0) <= now_ms


def merge(mine: list[dict], theirs: list[dict]) -> tuple[list[dict], dict]:
    """What to write into ``mine`` so it also holds ``theirs``: ``(items to write, counts)``."""
    by_id = {item["id"]: item for item in mine}
    writes: list[dict] = []
    added = updated = 0
    for item in theirs:
        if not item.get("id") or not item.get("text"):
            continue
        current = by_id.get(item["id"])
        if current is None:
            added += 1
        elif changed_at(item) > changed_at(current):
            updated += 1
        else:
            continue
        writes.append(item)
        by_id[item["id"]] = item
    return writes, {"added": added, "updated": updated, "unchanged": len(mine) - updated}


def read_items(path: Path) -> list[dict]:
    """Items from a JSON file (a list, one item, or ``{"items": [...]}``) or a folder of item files."""
    files = sorted(path.rglob("*.json")) if path.is_dir() else [path]
    items: list[dict] = []
    for file in files:
        data = json.loads(file.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            data = data["items"]
        items.extend(data if isinstance(data, list) else [data])
    return [item for item in items if isinstance(item, dict)]


def load(store: DocStore) -> list[dict]:
    return [{**doc, "id": doc.get("id") or item_id} for item_id, doc in store.list("study")]


def import_items(store: DocStore, items: list[dict]) -> dict:
    """Merge ``items`` into the store's study list and say what changed."""
    writes, counts = merge(load(store), items)
    for item in writes:
        store.set(f"study/{item['id']}", item)
    return counts
