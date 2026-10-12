"""Rules every drafted use case review should keep, checked by code (no model needed).

Used twice: by the server, on every review the page asks for (they land on the trace as
feedback from CODE), and by ``drill review eval`` on cards with planted gaps. ``True`` in a
check result means the rule was broken, like the server's other answer checks.
"""

from __future__ import annotations

import re

from drill.content.review import PILLARS

# A verdict on whether to build it: the decision belongs to a person.
_VERDICT = re.compile(
    r"\b(you should (not )?(build|proceed|go ahead)|i (would )?recommend (building|proceeding|going ahead|not building)"
    r"|(do not|don't) build (it|this)|go ahead and build|this should (not )?be built|worth building|not worth building)\b",
    re.I,
)


def missing_pillars(text: str) -> list[str]:
    """Pillars the review never names. Matching ignores case and markdown."""
    flat = re.sub(r"[*#_`]", "", text).lower()
    return [p for p in PILLARS if p.lower() not in flat]


def unknown_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if re.search(r"\bunknown\b|\?", line, re.I)]


def flags_gap(text: str, keywords: list[str]) -> bool:
    """Does any Unknown or question line mention one of the gap's words?"""
    lines = [line.lower() for line in unknown_lines(text)]
    return any(k.lower() in line for line in lines for k in keywords)


def review_checks(text: str, blank: list[str] | None = None) -> dict:
    """The checks, as broken (True) or kept (False), plus a count for reading."""
    blank = [b for b in (blank or []) if b]
    return {
        "missing_pillar": bool(missing_pillars(text)),
        "no_unknowns_for_blanks": bool(blank) and not unknown_lines(text),
        "decides_for_them": bool(_VERDICT.search(text)),
        "pillars_named": len(PILLARS) - len(missing_pillars(text)),
    }
