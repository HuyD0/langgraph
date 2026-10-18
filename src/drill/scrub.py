"""Shapes that mean a real name has reached text that must stay public.

Two layers. **Always on**: shapes that are real whoever you are (a workspace address with a real id, an
application id, a company email, a personal access token, a cloud resource id, an organisation's address
at a SaaS provider). **Your denylist**: words only real for you (team codes, catalogs, people), one per line
in ``~/.config/daily-drill/denylist.txt`` or the file ``DRILL_DENYLIST_FILE`` names; ``re:`` starts a
pattern. The list never lives in the repository.

tests/test_scrub.py runs both over every tracked text file; ``drill tutor prepare`` runs :func:`find` over
every model-written answer before saving it, because the model quotes the lesson it was given, and in the
work copy that lesson may name real things.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Callable

DEFAULT_DENYLIST = "~/.config/daily-drill/denylist.txt"

# Domains the lessons, tests and fixtures use for made-up people and shops.
PLACEHOLDER_DOMAINS = {"example.com", "example.org", "example.net", "corp.com", "corp.io", "shop.com", "onlineshop.com"}
# The lessons' made-up workspace: the digits in order, which no real workspace id is.
FAKE_WORKSPACE_IDS = {"1234567890123456"}
# Organisation names that are clearly placeholders in an address like <org>.atlassian.net.
PLACEHOLDER_ORGS = {"example", "your-org", "yourorg", "org", "contoso", "acme", "fictional", "myorg", "my-org", "company"}


def _real_workspace(m: re.Match) -> bool:
    digits = m.group(1)
    return digits not in FAKE_WORKSPACE_IDS and len(set(digits)) > 1


def _company_email(m: re.Match) -> bool:
    domain = m.group(1).lower()
    # in JSON, a code example's escaped line break followed by a decorator (backslash, n, at-sign) is not an address
    escaped_break = m.string[max(0, m.start() - 1):m.start() + 1] in ("\\n", "\\t", "\\r") and "@" == m.string[m.start() + 1]
    # container@account.dfs.core.windows.net is a storage path, not a person
    return domain not in PLACEHOLDER_DOMAINS and not domain.endswith(".windows.net") and not escaped_break


def _real_org(m: re.Match) -> bool:
    org = next(g for g in m.groups() if g)
    return org.lower() not in PLACEHOLDER_ORGS


GENERIC: list[tuple[str, re.Pattern, Callable[[re.Match], bool]]] = [
    ("an Azure Databricks workspace address", re.compile(r"adb-(\d{10,})\.\d+\.azuredatabricks\.net"), _real_workspace),
    ("a 32-character application id", re.compile(r"\b[0-9a-f]{32}\b"), lambda m: True),
    # the domain must end in letters: `skulpt@1.2.0/dist` in a CDN address is a version, not a person
    ("an email address at a company", re.compile(r"[A-Za-z0-9._%+-]+@((?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})\b"), _company_email),
    # a real personal access token is dapi plus 32 hex characters; the lessons' dapi0123456789abcdef is shorter
    ("a Databricks personal access token", re.compile(r"\bdapi[0-9a-f]{32}\b"), lambda m: True),
    # a real AWS or GCP workspace host is dbc-<8 hex>-<4 hex>; the lessons' dbc-7f3e is shorter
    ("a Databricks workspace address", re.compile(r"\b(dbc-[0-9a-f]{8}-[0-9a-f]{4})\.(?:cloud|gcp)\.databricks\.com\b"), lambda m: True),
    ("an Azure resource id with a subscription", re.compile(r"/subscriptions/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b"), lambda m: True),
    ("an organisation's address at a SaaS provider", re.compile(r"\b([a-z0-9-]+)\.(?:atlassian\.net|app\.spacelift\.io)\b|\bdev\.azure\.com/([A-Za-z0-9_-]+)"), _real_org),
]


def denylist_path() -> Path:
    return Path(os.getenv("DRILL_DENYLIST_FILE") or DEFAULT_DENYLIST).expanduser()


def denylist_patterns(path: Path | None = None) -> list[tuple[int, re.Pattern]]:
    """The denylist as (line number, pattern); an empty list when there is no file."""
    path = path or denylist_path()
    if not path.is_file():
        return []
    patterns = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append((n, re.compile(line[3:].strip() if line.startswith("re:") else re.escape(line), re.I)))
    return patterns


@lru_cache(maxsize=1)
def _denylist_cached() -> tuple[tuple[int, re.Pattern], ...]:
    return tuple(denylist_patterns())


def find(text: str) -> list[str]:
    """What in ``text`` looks like a real name: the shape's label, or "denylist line N" (never the word itself)."""
    hits = []
    for what, rx, keep in GENERIC:
        if any(keep(m) for m in rx.finditer(text)):
            hits.append(what)
    for n, rx in _denylist_cached():
        if rx.search(text):
            hits.append(f"denylist line {n}")
    return hits
