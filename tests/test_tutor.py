"""The tutor material: a curriculum map that matches the content, and an honest snapshot."""

from __future__ import annotations

import re

from drill import tutor
from drill.content import build_data


def test_the_committed_map_matches_the_content():
    """Change a lesson, then run `uv run drill tutor map`; this fails until you do."""
    assert tutor.MAP_PATH.read_text() == tutor.curriculum_map(), "run: uv run drill tutor map"


def test_the_map_has_no_maths_symbols():
    """The tutor copies what its knowledge says, and the learner finds maths symbols hard."""
    text = tutor.curriculum_map()
    assert not re.findall(r"[√Σ±×÷≈≥≤−]", text)
    big_o = [line for line in text.splitlines() if "O(" in line]
    allowed = ("- **Big-O**", "- `m0_python_basics.ipynb`")  # the glossary label, and the notebook that introduces it
    assert big_o and all(line.startswith(allowed) for line in big_o), big_o


def test_the_right_answer_rule_matches_the_page():
    page = (tutor.PROJECT_ROOT / "src" / "drill" / "content" / "page.html").read_text()
    assert "const answer = i % 3" in page  # gotcha_cards() mirrors this line
    cards = tutor.gotcha_cards(build_data())
    assert cards["run_agent"]["title"] == "Always put a limit on agent loops" and cards["run_agent"]["answer"] == 0


def test_the_snapshot_says_what_to_work_on():
    data = build_data()
    question, options, right, _ = data["lessons"]["precision_recall"]["check"]
    progress = {
        "lessons": {
            "split_by_key": {"step": 3, "checked": data["lessons"]["split_by_key"]["check"][2], "done": True},
            "precision_recall": {"step": 2, "checked": (right + 1) % 3, "done": False},
        },
        "solved": {"best_threshold": {"count": 1, "hints": 3}},
        "gotchas": {"run_agent": 1, "split_by_key": tutor.gotcha_cards(data)["split_by_key"]["answer"]},
        "days": ["2026-10-10", "2026-09-01"],
    }
    study = [
        {"id": "a", "text": "pass^k", "status": "got", "reviewAt": 0},
        {"id": "b", "text": "MERGE INTO", "status": "open", "note": "when?"},
    ]
    text = tutor.snapshot(progress, study, data, today="2026-10-11")
    assert "Lessons finished: 1 of 95" in text
    assert "Next lesson: Precision, recall and why accuracy lies (AI & ML foundations), in progress, at the Build step." in text
    assert "Days practised: 1 in the last 7 days, 1 in the last 30." in text  # counted back from today, not the clock
    assert "Spot the gotcha: 1 spotted, 1 missed" in text
    assert "- Always put a limit on agent loops, in The agent loop" in text
    assert f"They chose \"{options[(right + 1) % 3]}\". The right answer is \"{options[right]}\"" in text
    assert "## Started, not finished\n\n- Precision, recall and why accuracy lies (AI & ML foundations), in progress, at the Build step" in text
    assert "## Finished\n\n- Train, validation and test data" in text
    assert "- From scores to decisions (3 hints)" in text
    assert "## Study list: due for review now\n\n- pass^k" in text
    assert "- MERGE INTO (their note: when?)" in text


def test_next_lesson_resumes_the_lesson_in_progress_like_the_page():
    data = build_data()
    progress = {"lessons": {"best_run": {"step": 1, "checked": None, "done": False}}, "current": "best_run"}
    assert "Next lesson: Experiments, runs and the lifecycle" in tutor.snapshot(progress, [], data, today="2026-10-11")
    # The page adds an empty entry for the next lesson after every finished one: that is not a start.
    empty = {"lessons": {"split_by_key": {"step": 3, "done": True}, "precision_recall": {"step": 0, "checked": None, "done": False}},
             "current": "precision_recall"}
    assert "Next lesson: Precision, recall and why accuracy lies (AI & ML foundations), not started." in tutor.snapshot(empty, [], data, today="2026-10-11")
    gone = {"lessons": {"no_such_lesson": {"step": 1}}, "current": "no_such_lesson"}
    assert "Next lesson: Train, validation and test data" in tutor.snapshot(gone, [], data, today="2026-10-11")


def test_progress_from_two_copies_merges_like_the_page():
    """The second copy wins, as the page's browser copy does: checked, solved, gotchas and current."""
    mac = {"lessons": {"x": {"step": 1, "checked": None, "done": False}}, "gotchas": {"x": 0}, "days": ["d1"], "current": "x"}
    phone = {"lessons": {"x": {"step": 3, "checked": 2, "done": True}, "y": {"step": 1}}, "gotchas": {"y": 2}, "days": ["d2"], "current": "y"}
    merged = tutor.merge_progress(mac, phone)
    assert merged["lessons"]["x"] == {"step": 3, "checked": 2, "done": True} and "y" in merged["lessons"]
    assert merged["gotchas"] == {"x": 0, "y": 2} and merged["days"] == ["d1", "d2"] and merged["current"] == "y"
