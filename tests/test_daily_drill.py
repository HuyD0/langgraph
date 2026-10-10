"""The Daily Drill page's exercises must be solvable, and its lessons must be complete.

Every exercise in web/daily-drill/content is checked twice: its reference solution, and
its fill-in-the-blanks scaffold with the intended answers filled in, both against the
exercise's own test cases. The build is then run end to end, which also fails if Big-O
notation appears in learner-facing text.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "web" / "daily-drill"
CONTENT = ROOT / "content"
PROBLEM_MODULES = ["new_problems", "new_problems2", "new_problems3", "new_problems4", "new_problems5", "new_problems6"]


@pytest.fixture(scope="module", autouse=True)
def content_on_path():
    sys.path.insert(0, str(CONTENT))
    yield
    sys.path.remove(str(CONTENT))


@pytest.mark.parametrize("name", PROBLEM_MODULES)
def test_exercises_and_scaffolds_pass_their_own_tests(name):
    importlib.import_module(name).check()


def test_page_builds(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "build.py")], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (ROOT / "dist" / "daily-drill.html").exists()
