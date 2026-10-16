"""The build pastes the content into one <script> block (build.render_page). Nothing a lesson says
may be able to end that block early: a browser acts on </script> and <!-- wherever it meets them,
so the build writes every "<" in the JSON as the escape \\u003c, which JSON and JavaScript both read
back as "<"."""

from __future__ import annotations

import json

import pytest

from drill.content.build import build_data, build_page


@pytest.fixture(scope="module")
def data() -> dict:
    return build_data()


def _embedded_json(html: str) -> str:
    """The text pasted at /*DATA*/: between `const D = ` and the line that reads it."""
    start = html.index("const D = ") + len("const D = ")
    return html[start:html.index(";\nconst BANK = D.bank", start)]



def _script_blocks(html):
    """The text of each <script> block, cut the way a browser does: at the first </script> after it opens."""
    return [chunk.split("</script>", 1)[0] for chunk in html.split("<script>")[1:]]


def test_lesson_text_cannot_end_the_script_block(data):
    tricky = json.loads(json.dumps(data))
    tricky["modules"][0]["blurb"] = "stops at </script> and <!-- here"
    html = build_page(tricky)
    blocks = _script_blocks(html)
    data_block = next(b for b in blocks if "const D = " in b)
    assert "const BANK = D.bank" in data_block, "the blurb ended the data script early"
    assert len(blocks) == len(_script_blocks(build_page(data)))
    embedded = _embedded_json(html)
    assert "<" not in embedded and "\\u003c/script>" in embedded
    assert json.loads(embedded)["modules"][0]["blurb"] == "stops at </script> and <!-- here"


def test_the_real_content_round_trips_through_the_page(data):
    assert json.loads(_embedded_json(build_page(data))) == data
