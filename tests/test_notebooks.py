"""Every teaching notebook must be solvable, and must stay in step with its answer key.

This is the test that matters if you are *teaching* from `notebooks/`. The notebooks
ship with their exercises unsolved, so nothing about them is exercised by simply
importing the package - a notebook whose tests contradict each other, or whose
exercise you renamed without updating `notebooks/solutions/`, would sit broken in
the repo until someone hit it live in front of a room.

So: for each notebook, substitute the answer key into the exercise cells, run the
notebook in a real kernel with `ipytest` set to raise, and require that every
embedded test passes.

Two failure modes are caught, and they are different:

- **Unsolvable spec.** The notebook's own tests cannot all pass. Reported as a
  failure in whichever cell raised.
- **Drift.** An exercise defines a name the answer key does not cover, or vice
  versa. Caught by `test_answer_key_covers_every_exercise` *without* starting a
  kernel, so it fails fast and points at the mismatch by name.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

nbformat = pytest.importorskip("nbformat", reason="notebook tooling not installed")
pytest.importorskip("nbclient", reason="notebook tooling not installed")
from nbclient import NotebookClient  # noqa: E402
from nbclient.exceptions import CellExecutionError  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = REPO_ROOT / "notebooks"
SOLUTION_DIR = NOTEBOOK_DIR / "solutions"

NOTEBOOKS = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
NOTEBOOK_IDS = [p.stem for p in NOTEBOOKS]

# Matches the `ipytest.autoconfig(...)` call in each notebook's setup cell, so the
# arguments can be extended without caring what they currently are.
_AUTOCONFIG = re.compile(r"ipytest\.autoconfig\((.*?)\)", re.DOTALL)


def _is_exercise(source: str) -> bool:
    """An exercise cell is one left for the learner to fill in."""
    return "NotImplementedError" in source or "TODO" in source


def _is_test_cell(source: str) -> bool:
    return source.lstrip().startswith("%%ipytest")


def _defined_names(source: str) -> list[str]:
    """Top-level function and class names bound by a cell."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def _segment_with_decorators(lines: list[str], node) -> str:
    """Source text for a definition, decorators included.

    `ast.get_source_segment` starts at the `def`/`class` line, so it silently drops
    decorators - which turns a solved `@dataclass` into a plain class and produces a
    baffling "takes no arguments" error at the call site rather than here.
    """
    start = min([node.lineno] + [d.lineno for d in node.decorator_list])
    return "\n".join(lines[start - 1 : node.end_lineno]).rstrip()


def _solution_segments(stem: str) -> dict[str, str]:
    """name -> its source text, from the milestone's answer-key module.

    Only definitions are extracted, never the module's imports: the notebook's own
    setup cell already imports what the exercises need, and re-importing inside a
    substituted cell would diverge from what a learner actually types.
    """
    path = SOLUTION_DIR / f"{stem}.py"
    if not path.exists():
        return {}
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)
    return {
        node.name: _segment_with_decorators(lines, node)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _exercise_names(notebook) -> list[str]:
    names: list[str] = []
    for cell in notebook.cells:
        if cell.cell_type == "code" and _is_exercise(cell.source):
            names.extend(_defined_names(cell.source))
    return names


def _load(path: Path):
    return nbformat.read(path, as_version=4)


# ---------------------------------------------------------------------------
# Fast structural checks - no kernel, so these fail in milliseconds
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", NOTEBOOKS, ids=NOTEBOOK_IDS)
def test_answer_key_covers_every_exercise(path: Path):
    """Each exercise name has a solution, and the key has no orphans.

    The orphan half is what catches a renamed exercise: the old solution would
    otherwise linger, the cell would go unpatched, and the notebook would fail
    with a confusing NotImplementedError instead of naming the real problem.
    """
    notebook = _load(path)
    exercises = set(_exercise_names(notebook))
    solutions = set(_solution_segments(path.stem))

    assert exercises, f"{path.name} has no exercise cells - did the TODO markers change?"

    missing = exercises - solutions
    assert not missing, (
        f"{path.name} exercises have no answer key: {sorted(missing)}. "
        f"Add them to notebooks/solutions/{path.stem}.py"
    )

    orphans = solutions - exercises
    assert not orphans, (
        f"notebooks/solutions/{path.stem}.py solves {sorted(orphans)}, which is not an "
        f"exercise in {path.name} any more. Remove it or fix the name."
    )


@pytest.mark.parametrize("path", NOTEBOOKS, ids=NOTEBOOK_IDS)
def test_notebook_has_tests_and_ships_unsolved(path: Path):
    """A teaching notebook needs specs, and must not arrive already answered."""
    notebook = _load(path)
    assert any(_is_test_cell(c.source) for c in notebook.cells if c.cell_type == "code"), (
        f"{path.name} has no %%ipytest cell, so nothing specifies the exercise"
    )
    assert any(_is_exercise(c.source) for c in notebook.cells if c.cell_type == "code"), (
        f"{path.name} ships with its exercises already solved"
    )


def test_every_notebook_has_an_answer_key_module():
    stems = {p.stem for p in NOTEBOOKS}
    keys = {p.stem for p in SOLUTION_DIR.glob("m*.py")}
    assert stems == keys, f"notebooks {sorted(stems)} vs answer keys {sorted(keys)}"


# ---------------------------------------------------------------------------
# The real thing: execute each notebook, solved, in a kernel
# ---------------------------------------------------------------------------


def _solve(notebook, stem: str) -> int:
    """Substitute the answer key and make ipytest raise. Returns cells patched."""
    segments = _solution_segments(stem)
    patched = 0

    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue

        # Without raise_on_error, %%ipytest prints failures and the cell still
        # "succeeds" - the notebook would execute cleanly with every test red.
        if "ipytest.autoconfig(" in cell.source:
            cell.source = _AUTOCONFIG.sub(
                lambda m: f"ipytest.autoconfig({m.group(1).strip()}, raise_on_error=True)",
                cell.source,
                count=1,
            )
            continue

        if not _is_exercise(cell.source):
            continue

        names = _defined_names(cell.source)
        replacement = "\n\n\n".join(segments[n] for n in names if n in segments)
        if replacement:
            cell.source = replacement
            patched += 1

    return patched


@pytest.mark.slow
@pytest.mark.parametrize("path", NOTEBOOKS, ids=NOTEBOOK_IDS)
def test_notebook_is_solvable(path: Path):
    """With the answer key substituted, every test in the notebook passes."""
    notebook = _load(path)
    patched = _solve(notebook, path.stem)
    assert patched, f"no exercise cell in {path.name} was substituted"

    client = NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        # Run as if launched from the repo root, so `import drill` resolves and the
        # notebook's own relative paths behave as they do for a learner.
        resources={"metadata": {"path": str(REPO_ROOT)}},
    )

    try:
        client.execute()
    except CellExecutionError as exc:
        pytest.fail(
            f"{path.name} does not pass its own tests when solved with "
            f"notebooks/solutions/{path.stem}.py:\n\n{exc}",
            pytrace=False,
        )
