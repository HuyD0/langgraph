"""Lesson diagrams (content/diagrams.py): the shapes hold, and every label on a picture is in the lesson's words."""
import re

import pytest

from drill.content import build_data, modules
from drill.content.build import page_source
from drill.content.diagrams import DIAGRAMS
from drill.content.model import DIAGRAM_KINDS


@pytest.fixture(scope="module")
def data():
    return build_data()


def _labels(d):
    """Every word a learner can read on the picture."""
    out = []
    for n in d.get("nodes", []):
        out += [n["label"], n.get("sub"), n.get("word")]
    for b in d.get("branches", []):
        out += [b["label"], b.get("share")]
    for r in d.get("rows", []):
        out += [r["name"]] if isinstance(r, dict) else list(r)
    out += d.get("columns", [])
    out += [p["label"] for p in d.get("points", [])] + [m.get("label") for m in d.get("marks", [])]
    out += [l.get("label") for l in d.get("lines", [])] + list(d.get("quadrants", []))
    out += [e.get("label") for e in d.get("edges", [])] + [d.get("question")]
    for row in (d.get("detail") or {}).get("rows", []):
        out += list(row)
    if d.get("marker"):
        out.append(d["marker"]["label"])
    if d.get("reference"):
        out.append(d["reference"]["label"])
    return [str(x) for x in out if x]


def test_every_diagram_belongs_to_a_real_lesson_and_holds_its_shape(data):
    for lesson_id, d in DIAGRAMS.items():
        assert lesson_id in data["lessons"], f"diagram for unknown lesson {lesson_id}"
        assert d["kind"] in DIAGRAM_KINDS
        assert 0 <= d["after"] < len(data["lessons"][lesson_id]["learn"]), f"{lesson_id}: 'after' names a Learn paragraph"
        assert data["lessons"][lesson_id]["diagram"] == d
        for c in d["callouts"]:
            assert 10 < len(c) < 160 and not re.search(r"\d+\s*%", c), f"{lesson_id}: a short plain callout, no % signs"
    assert len(DIAGRAMS) >= 12


def test_every_label_on_a_picture_is_in_the_lessons_words():
    """A screen reader hears the caption and the callouts; a sighted learner reads the labels. The two must
    agree, so every label appears in the Learn text, the example, the caption or the callouts."""
    learn = {e["id"]: e for m in modules.load() for e in m.lessons}
    problems = {}
    for lesson_id, d in DIAGRAMS.items():
        entry = learn[lesson_id]
        words = (" ".join(entry["learn"]) + " " + entry["example"]["code"] + " " + d["caption"] + " " + " ".join(d["callouts"])).lower()
        words = re.sub(r"\s+", " ", words.replace("**", "").replace("`", ""))
        missing = [label for label in _labels(d) if re.sub(r"[.,:;]$", "", re.sub(r"\s+", " ", label.lower().strip())) not in words]
        if missing:
            problems[lesson_id] = missing
    assert not problems, f"pictures say things their lessons never do: {problems}"


def test_numbers_on_the_picture_match_the_notes_under_it():
    for lesson_id, d in DIAGRAMS.items():
        ns = []
        for key in ("nodes", "branches", "rows", "points", "marks"):
            ns += [x["n"] for x in d.get(key, []) if isinstance(x, dict) and x.get("n")]
        assert sorted(ns) == list(range(1, len(d["callouts"]) + 1)), f"{lesson_id}: callout numbers {sorted(ns)} vs {len(d['callouts'])} notes"


def test_diagrams_are_wired_into_the_learn_step():
    page = page_source()
    learn = page.split("function learnPane()")[1].split("\n}")[0]
    assert "diagramHtml(L.diagram)" in learn and "L.diagram.after" in learn
    assert all(f"function dg{k.capitalize()}(" in page for k in DIAGRAM_KINDS)
    css = page.split("lesson diagrams (content/diagrams.py")[1]
    assert ".dg-co circle { fill: var(--hint); }" in css and "fill: var(--bg); }" in css, "callout numbers use the walkthrough's amber-on-background pair, readable in Light too"
