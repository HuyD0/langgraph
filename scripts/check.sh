#!/usr/bin/env bash
# Build the page and run the fast tests: what every change must pass before a commit.
# Usage: scripts/check.sh            (from anywhere in the repo)
set -euo pipefail
cd "$(dirname "$0")/.."
uv run drill build-page
uv run drill tutor map >/dev/null
git diff --quiet -- docs/tutor/CURRICULUM_MAP.md || echo "note: docs/tutor/CURRICULUM_MAP.md changed; commit it with your content change"
uv run pytest -q -m "not slow"
