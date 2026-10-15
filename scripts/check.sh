#!/usr/bin/env bash
# Build the page and run the fast tests: what every change must pass before a commit.
# Usage: scripts/check.sh            (from anywhere in the repo)
set -euo pipefail
cd "$(dirname "$0")/.."
uv run drill build-page
uv run drill tutor map >/dev/null
git diff --quiet -- docs/tutor/CURRICULUM_MAP.md || echo "note: docs/tutor/CURRICULUM_MAP.md changed; commit it with your content change"
# The fast tests include tests/test_scrub.py: with a denylist at ~/.config/daily-drill/denylist.txt
# (or DRILL_DENYLIST_FILE) it fails on any real name in a tracked file. scripts/hooks/pre-push runs
# that one test alone before every push (install once: git config core.hooksPath scripts/hooks).
uv run pytest -q -m "not slow"
