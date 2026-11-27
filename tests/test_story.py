"""The films ("The Watch"): built from the course itself, one per phase, and found by the page's links.

The films live in ``src/drill/content/story/`` and are built by :func:`drill.content.build.story_sources`:
the overview (``the-watch.html``) and one short film per phase (``the-watch-<phase>.html``). They are
pages of their own, published beside the page on claude.ai and served beside it by the server.
"""

from __future__ import annotations

import re

from drill.content import modules
from drill.content.build import STORY, _story_course, film_files, film_key, page_source, story_sources, write

PARTS = ("template.html", "engine.js", "acts.js", "beats.js")


def test_every_phase_has_a_film_and_the_page_finds_it():
    files = list(film_files())
    assert files[0] == "the-watch.html"
    assert files[1:] == [f"the-watch-{film_key(n)}.html" for n, _, _ in modules.LIFECYCLE]
    assert len(set(files)) == len(modules.LIFECYCLE) + 1, "two phases share a first word, so their films would share a name"
    # The page links to each phase's film by the same rule as build.film_key.
    assert 'ph.name.split(" ")[0].toLowerCase()' in page_source()
    assert 'href="the-watch.html"' in page_source()


def test_every_module_on_the_path_has_plain_words_in_the_films():
    beats = (STORY / "beats.js").read_text(encoding="utf-8")
    start = beats.index("const PLAIN = {")
    have = set(re.findall(r'"([a-z0-9-]+)":', beats[start:beats.index("};", start)]))
    want = {m for _, _, ms in modules.LIFECYCLE for m in ms}
    assert want <= have, f"add a few plain words for {sorted(want - have)} to PLAIN in story/beats.js"


def test_the_films_carry_no_colour_of_their_own():
    """Every colour comes from tokens.css, stitched in at build time (DESIGN_SYSTEM.md rule 1)."""
    for name in PARTS:
        text = (STORY / name).read_text(encoding="utf-8")
        found = re.findall(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(", text)
        assert not found, f"story/{name} types a colour ({found[:3]}); use a token from tokens.css"


def test_each_film_is_whole_and_starts_at_a_real_lesson():
    ids = {lesson["id"] if isinstance(lesson, dict) else lesson.id for m in modules.load() for lesson in m.lessons}
    course = _story_course()
    assert course["first"]["lesson"] in ids
    assert all(p["first"]["lesson"] in ids for p in course["phases"])
    for name, page in story_sources().items():
        left = [m for m in ("/*TOKENS*/", "/*HORIZON_CSS*/", "/*HORIZON_JS*/", "/*PH_SHAPE*/", "/*COURSE*/",
                            "/*ENGINE*/", "/*ACTS*/", "/*BEATS*/", "/*FILM*/") if m in page]
        assert not left, (name, left)
        assert page.startswith("<title>The Watch"), name
        # Start goes back to the page beside the film, wherever it is served: never a fixed address.
        assert 'const APP_URL = "./"' in page and "claude.ai/artifact" not in page, name


def test_the_films_have_one_part_per_phase():
    """The films are written for the path's phases one by one: a new phase needs its stop, action and night."""
    n = len(modules.LIFECYCLE)
    beats, acts, engine = ((STORY / f).read_text(encoding="utf-8") for f in ("beats.js", "acts.js", "engine.js"))
    assert beats.count("purpose:") == n, "add the new phase's stop to STOPS in story/beats.js"
    assert len(re.findall(r"^  \{ start\(\)", acts, re.M)) == n, "add the new phase's action to ACTS in story/acts.js"
    assert re.search(r"\bN = (\d+);", engine).group(1) == str(n), "set N in story/engine.js"
    night = re.search(r"const NIGHT = \[([^\]]*)\]", engine).group(1)
    assert len(night.split(",")) == n, "give the new phase a NIGHT value in story/engine.js"


def test_the_build_writes_the_films_beside_the_page_as_whole_documents(tmp_path):
    """claude.ai serves a file published beside the page exactly as given, so each is a whole document."""
    write(tmp_path)
    assert {p.name for p in tmp_path.glob("the-watch*.html")} == set(film_files())
    for name in [*film_files(), "blueprint.html"]:
        text = (tmp_path / name).read_text(encoding="utf-8")
        head = text.split("</head>")[0]
        assert text.startswith("<!doctype html>") and '<meta charset="utf-8">' in head and 'name="viewport"' in head, name
        assert "<title>" in head and text.rstrip().endswith("</html>"), name
