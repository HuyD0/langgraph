#!/usr/bin/env bash
# Build the page and run the fast tests: what every change must pass before a commit.
# The same as `make check` or `uv run drill dev check` (those work on Windows too).
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run drill dev check "$@"
