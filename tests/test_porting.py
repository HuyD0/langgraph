"""The two copies of the repository (this public one, and the work copy) stay mergeable.

Everything work-specific is an overlay the public repository never creates, so an upstream merge
never conflicts with it: the real lessons in content-packs/internal/, the guard workflow copied
from templates/enterprise/overlay.yml, the UPSTREAM record. See docs/PORTING.md, "Keeping the
work copy in step".
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
# The same suite runs in both copies: an UPSTREAM file at the root means the work copy, which holds
# the things the public repository must not (tests/test_scrub.py uses the same switch).
WORK_COPY = (ROOT / "UPSTREAM").is_file()


def test_the_internal_pack_folder_is_tracked_not_ignored():
    """`databricks bundle deploy` honours .gitignore, so an ignored pack would never reach the app."""
    for name in ("content-packs/internal", "content-packs/internal/pack.yaml",
                 "content-packs/internal/lessons/a1-workflow.yaml", "content-packs/internal/assets/plan.png"):
        done = subprocess.run(["git", "check-ignore", "-q", name], cwd=ROOT)
        assert done.returncode == 1, f"{name} is git-ignored; the work copy's pack must be tracked to deploy"
    # the laptop-only folder stays ignored, so a preview pack never leaves the machine by accident
    assert subprocess.run(["git", "check-ignore", "-q", "content-packs/private/pack.yaml"], cwd=ROOT).returncode == 0


def test_app_yaml_points_at_the_internal_pack_so_the_work_copy_never_edits_it():
    """The same app.yaml serves both copies: here the folder is missing and nothing loads."""
    app = yaml.safe_load((ROOT / "app.yaml").read_text())
    env = {e["name"]: e for e in app["env"]}
    assert env["DRILL_CONTENT_PACKS"]["value"] == "content-packs/internal"
    if WORK_COPY:
        assert (ROOT / "content-packs" / "internal").is_dir(), "the work copy keeps its real lessons in content-packs/internal/"
    else:
        assert not (ROOT / "content-packs" / "internal").exists(), "the public repository never holds the internal pack"


def test_the_overlay_guard_is_a_template_the_work_copy_copies():
    text = (ROOT / "templates" / "enterprise" / "overlay.yml").read_text()
    for needle in ("content-packs/internal/", "upstream-sync", "git diff --name-only origin/main...HEAD", "tests/test_scrub.py"):
        assert needle in text, needle
    guard = ROOT / ".github" / "workflows" / "overlay.yml"
    if WORK_COPY:
        assert guard.is_file(), "the work copy copies the guard into .github/workflows/ (docs/PORTING.md)"
    else:
        assert not guard.exists(), "the guard runs in the work copy only"
    assert "templates/enterprise/overlay.yml" in (ROOT / "docs" / "PORTING.md").read_text()


def test_the_pre_push_hook_runs_the_scrub():
    hook = ROOT / "scripts" / "hooks" / "pre-push"
    assert os.access(hook, os.X_OK), "scripts/hooks/pre-push must be executable (git ignores a hook that isn't)"
    text = hook.read_text()
    assert "tests/test_scrub.py" in text and "core.hooksPath scripts/hooks" in text
