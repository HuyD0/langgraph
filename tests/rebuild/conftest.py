"""Every test under tests/rebuild/ is a milestone test.

They are marked `rebuild` automatically, and the default pytest run excludes that
marker (see [tool.pytest.ini_options] in pyproject.toml). So `uv run pytest` stays
green while these sit unimplemented, and you opt in with:

    uv run pytest -m rebuild
"""

from pathlib import Path

import pytest

_HERE = Path(__file__).parent


def pytest_collection_modifyitems(items):
    """Mark only the tests in this directory.

    pytest hands this hook the WHOLE collected suite, not just the items under
    this conftest - so it has to filter by path. Without the check, the marker
    lands on every test in the project and the default run deselects all of them.
    """
    for item in items:
        if _HERE in Path(str(item.fspath)).parents:
            item.add_marker(pytest.mark.rebuild)
