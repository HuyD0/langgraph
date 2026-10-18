"""Nothing with a real name reaches the public repository.

Two layers, both over every text file git tracks (`git ls-files`):

1. **Always on.** Shapes that are real whoever you are: an Azure Databricks workspace address with
   a real-looking id, a 32-character hex application id, and an email address at a company. The
   lessons' made-up addresses (`adb-1234567890123456.7`, short ids like `adb-1234.5`) and
   placeholder domains (`example.com`, `corp.com`...) are allowed.
2. **Your denylist.** Words that are only real for you: team codes, group names, catalog names,
   repository names, people. They live outside the repository, one per line (`re:` starts a
   regular expression), in `~/.config/daily-drill/denylist.txt` or the file `DRILL_DENYLIST_FILE`
   names, so the list itself is never committed. Without the file the test skips and says so.

In the work copy (marked by an `UPSTREAM` file at the root, see docs/PORTING.md) the overlay paths
`content-packs/internal/` and `README-internal.md` are exempt: that is where real names belong.
Everywhere else, and everywhere in the public copy, they are a failure.

A failure names the file and line, and for the denylist only the pattern's line number, so a CI
log never prints the word itself. scripts/check.sh runs this with the other fast tests, and
scripts/hooks/pre-push runs it alone before every push.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Iterator

import pytest

from drill.scrub import DEFAULT_DENYLIST, GENERIC, _company_email, _real_org, _real_workspace, denylist_patterns, denylist_path, find

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".pdf"}
# Where real names may live in the work copy only.
OVERLAY = ("content-packs/internal/", "README-internal.md")
WORK_COPY = (ROOT / "UPSTREAM").is_file()


def tracked_text_files() -> Iterator[tuple[str, Path]]:
    """Every file git tracks that is text, as (path relative to the root, path)."""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    for name in out.decode("utf-8").split("\0"):
        path = ROOT / name
        if not name or path.suffix.lower() in IMAGE_SUFFIXES or not path.is_file():
            continue
        with path.open("rb") as f:
            if b"\0" in f.read(8192):
                continue
        yield name, path


def may_hold_real_names(name: str) -> bool:
    return WORK_COPY and name.startswith(OVERLAY)


def lines_of(path: Path) -> Iterator[tuple[int, str]]:
    return enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1)


def test_no_tracked_file_holds_a_real_workspace_id_or_company_email():
    hits = []
    for name, path in tracked_text_files():
        if may_hold_real_names(name):
            continue
        for n, line in lines_of(path):
            for what, rx, keep in GENERIC:
                if any(keep(m) for m in rx.finditer(line)):
                    hits.append(f"{name}:{n}: {what}")
    assert not hits, "real-looking names in tracked files (use a made-up one, or move it to the work copy's overlay):\n" + "\n".join(hits)


def test_no_tracked_file_holds_a_word_from_your_denylist():
    path = denylist_path()
    if not path.is_file():
        pytest.skip(f"no denylist at {path}: put your company's names there, one per line (or set DRILL_DENYLIST_FILE)")
    patterns = denylist_patterns(path)
    if not patterns:
        pytest.skip(f"{path} has no patterns in it")
    hits = []
    for name, file in tracked_text_files():
        if may_hold_real_names(name):
            continue
        for n, line in lines_of(file):
            for pattern_line, rx in patterns:
                if rx.search(line):
                    hits.append(f"{name}:{n}: matches denylist line {pattern_line}")
    assert not hits, "words from your denylist in tracked files:\n" + "\n".join(hits)


def test_the_lessons_made_up_names_are_still_allowed():
    """The allowances above must keep letting the teaching placeholders through, and nothing else.
    The real-looking examples are pieced together here so this file passes its own scan."""
    workspace, email = GENERIC[0][1], GENERIC[2][1]
    assert not any(_real_workspace(m) for m in workspace.finditer("https://adb-1234567890123456.7.azuredatabricks.net"))
    assert not any(_real_workspace(m) for m in workspace.finditer("adb-1234.5.azuredatabricks.net")), "short ids are the lessons' shorthand"
    real_host = "adb-" + "8364920175938201" + ".3." + "azuredatabricks.net"
    assert [m.group(1) for m in workspace.finditer(real_host) if _real_workspace(m)] == ["8364920175938201"]
    assert not any(_company_email(m) for m in email.finditer("sam@example.com ana@corp.com Sam@Example.com raw@lakefict.dfs.core.windows.net"))
    assert not any(_company_email(m) for m in email.finditer('"code": "x = 1\\n@mlflow.trace\\ndef f():"')), "an escaped line break before a decorator"
    assert not list(email.finditer("https://cdn.jsdelivr.net/npm/skulpt@1.2.0/dist/skulpt.min.js")), "a package version is not an address"
    real_email = "someone@" + "a-real-company.co.uk"
    assert [m.group(1) for m in email.finditer(real_email) if _company_email(m)] == ["a-real-company.co.uk"]


def test_the_newer_shapes_catch_real_things_and_pass_the_lessons_placeholders():
    labels = {what: rx for what, rx, _ in GENERIC}
    token = labels["a Databricks personal access token"]
    assert not token.search("dapi0123456789abcdef"), "the lessons' short placeholder token"
    assert token.search("dapi" + "0123456789abcdef" * 2)
    host = labels["a Databricks workspace address"]
    assert not host.search("https://dbc-7f3e.cloud.databricks.com") and not host.search("dbc-1.cloud.databricks.com")
    assert host.search("https://dbc-" + "a1b2c3d4" + "-e5f6.cloud.databricks.com")
    sub = labels["an Azure resource id with a subscription"]
    assert sub.search("/subscriptions/" + "12345678-1234-1234-1234-" + "123456789abc" + "/resourceGroups/rg")
    org = labels["an organisation's address at a SaaS provider"]
    assert not any(_real_org(m) for m in org.finditer("https://example.atlassian.net/wiki and https://dev.azure.com/your-org/project"))
    assert [m for m in org.finditer("https://" + "northwind-ltd" + ".atlassian.net/") if _real_org(m)]
    assert find("Ask " + "someone@" + "a-real-company.co.uk" + " for it") == ["an email address at a company"]
    assert find("plain text about the HR assistant at ana@example.com") == []

