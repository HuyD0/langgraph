"""The checks a "Fix the YAML" question runs, in Python. The page runs the same checks in the
browser (``yamlCheck`` in page.html); this copy lets the tests prove every question's starting
YAML has problems and its model answer has none, so a question can't be unfixable.

``rules`` describes the contract, the way the platform team's Pydantic models do:

``path``      where the items are, dotted (``"clusters"``, ``"team.folder_grants"``)
``required``  fields every item must have
``allowed``   the only fields an item may have (Pydantic rejects extra ones)
``types``     field -> ``"str"`` or ``"int"``
``enum``      field -> the values it may take
``forbid``    field -> the message to show if it's there
``size``      True: either ``num_workers`` alone, or ``min_workers`` and ``max_workers`` together

``goal`` says what the fixed file must do: ``{"field", "equals", "message"}`` on the first item,
or ``{"field", "contains", "message"}`` on any item.
"""

from __future__ import annotations

from typing import Any

import yaml

SIZE_MESSAGE = "Use num_workers, or both min_workers and max_workers."


def items_at(doc: Any, path: str) -> list | None:
    node = doc
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    if isinstance(node, dict):
        return [node]
    return node if isinstance(node, list) else None


def problems(text: str, rules: dict, goal: list[dict] | None = None) -> list[str]:
    """Every problem with ``text``, as plain messages (the page adds line numbers)."""
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError:
        return ["The YAML can't be read."]
    items = items_at(doc, rules["path"])
    if items is None:
        return [f"Expected a list under {rules['path']}."]
    out = []
    for item in items:
        if not isinstance(item, dict):
            out.append("Each item needs key: value lines.")
            continue
        for field, message in (rules.get("forbid") or {}).items():
            if field in item:
                out.append(message)
        allowed = rules.get("allowed")
        for field in item:
            if allowed and field not in allowed and field not in (rules.get("forbid") or {}):
                out.append(f"{field} isn't a field the check knows.")
        for field in rules.get("required", []):
            if field not in item:
                out.append(f"{field} is missing.")
        for field, kind in (rules.get("types") or {}).items():
            if field in item and not isinstance(item[field], int if kind == "int" else str):
                out.append(f"{field} must be {'a whole number' if kind == 'int' else 'text'}.")
        for field, values in (rules.get("enum") or {}).items():
            if field in item and item[field] not in values:
                out.append(f"{field} must be one of {', '.join(values)}.")
        if rules.get("size"):
            fixed, lo, hi = "num_workers" in item, "min_workers" in item, "max_workers" in item
            if not (fixed and not lo and not hi) and not (lo and hi and not fixed):
                out.append(SIZE_MESSAGE)
    if out:
        return out
    for g in goal or []:
        if "equals" in g and (not items or items[0].get(g["field"]) != g["equals"]):
            out.append(g["message"])
        if "contains" in g and not any(i.get(g["field"]) == g["contains"] for i in items):
            out.append(g["message"])
    return out
