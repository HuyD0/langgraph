"""The tutor material: a curriculum map that matches the content, and an honest snapshot."""

from __future__ import annotations

import re

from drill import tutor
from drill.content import build_data
from drill.content.build import page_source


def test_the_map_is_generated_from_the_content(tmp_path):
    """The map is not committed (every inserted lesson renumbered it): `uv run drill tutor map` writes it
    from the lessons, and make check runs that, so a local copy is always fresh."""
    out = tutor.write_map(tmp_path / "CURRICULUM_MAP.md")
    assert out.read_text(encoding="utf-8") == tutor.curriculum_map() and "### 1. " in out.read_text(encoding="utf-8")
    assert "docs/tutor/CURRICULUM_MAP.md" in (tutor.PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8"), "the map is generated, never committed"


def test_the_map_describes_the_check_step_as_the_page_has_it():
    """The page asks up to three Check questions one at a time; the map the tutor trusts must say the same."""
    text = tutor.curriculum_map()
    assert "Check (up to three multiple-choice questions, one at a time)" in text
    assert "Check (one multiple-choice question)" not in text


def test_the_map_has_no_maths_symbols():
    """The tutor copies what its knowledge says, and the learner finds maths symbols hard."""
    text = tutor.curriculum_map()
    assert not re.findall(r"[√Σ±×÷≈≥≤−]", text)
    big_o = [line for line in text.splitlines() if "O(" in line]
    allowed = ("- **Big-O**", "- `m0_python_basics.ipynb`")  # the glossary label, and the notebook that introduces it
    assert big_o and all(line.startswith(allowed) for line in big_o), big_o


def test_the_right_answer_rule_matches_the_page():
    page = page_source()
    assert "const answer = i % 3" in page  # gotcha_cards() mirrors this line
    cards = tutor.gotcha_cards(build_data())
    assert cards["run_agent"]["title"] == "Always put a limit on agent loops" and cards["run_agent"]["answer"] == 0


def test_the_snapshot_says_what_to_work_on():
    data = build_data()
    _question, options, right, _ = data["lessons"]["precision_recall"]["check"]
    progress = {
        "lessons": {
            "split_by_key": {"step": 3, "checked": data["lessons"]["split_by_key"]["check"][2], "done": True},
            "precision_recall": {"step": 2, "checked": (right + 1) % 3, "done": False},
        },
        "solved": {"best_threshold": {"count": 1, "hints": 3}},
        "gotchas": {"run_agent": 1, "split_by_key": tutor.gotcha_cards(data)["split_by_key"]["answer"]},
        "days": ["2026-10-10", "2026-09-01"],
        "current": "precision_recall",
    }
    study = [
        {"id": "a", "text": "pass^k", "status": "got", "reviewAt": 0},
        {"id": "b", "text": "MERGE INTO", "status": "open", "note": "when?"},
    ]
    text = tutor.snapshot(progress, study, data, today="2026-10-11")
    assert f"Lessons finished: 1 of {len(data['lessons'])}" in text
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
    # With no lesson to resume, the next lesson is the first one not done: the start of the path.
    first = data["lessons"][data["modules"][0]["lessons"][0]]["title"]
    assert f"Next lesson: {first}" in tutor.snapshot(gone, [], data, today="2026-10-11")


def test_progress_from_two_copies_merges_like_the_page():
    """The second copy wins, as the page's browser copy does: checked, solved, gotchas and current."""
    mac = {"lessons": {"x": {"step": 1, "checked": None, "done": False}}, "gotchas": {"x": 0}, "days": ["d1"], "current": "x"}
    phone = {"lessons": {"x": {"step": 3, "checked": 2, "done": True}, "y": {"step": 1}}, "gotchas": {"y": 2}, "days": ["d2"], "current": "y"}
    merged = tutor.merge_progress(mac, phone)
    assert merged["lessons"]["x"] == {"step": 3, "checked": 2, "done": True} and "y" in merged["lessons"]
    assert merged["gotchas"] == {"x": 0, "y": 2} and merged["days"] == ["d1", "d2"] and merged["current"] == "y"
    mac["lessons"]["x"]["said"] = "I used a set so each check is instant."
    assert tutor.merge_progress(mac, phone)["lessons"]["x"]["said"] == mac["lessons"]["x"]["said"], "the sentence survives a merge"
    mac["lessons"]["x"]["first"] = {"check": ["sign"], "build": None, "explain": ["sign"], "day": 3}
    phone["lessons"]["x"]["first"] = {"check": ["curtain"], "build": None, "explain": ["sign"], "day": 9}
    assert tutor.merge_progress(mac, phone)["lessons"]["x"]["first"]["day"] == 3, "the shared result stays the first one"


def test_their_own_use_case_reaches_the_snapshot_and_survives_a_merge():
    data = build_data()
    own = {"updatedAt": 5, "card": {"user": "Platform team", "success": "90 in 100 tickets routed right", "owner": ""},
           "reqs": "Route tickets to the right team\nReply within 3 seconds",
           "bars": {"quality": "90", "seconds": "3", "cost": "0.5", "mustpass": "never close a P1"},
           "costs": {"summary": {"years": 2, "perMonth": 1200, "total": 40800, "biggest": "Azure AI Search", "items": [["Azure AI Search", 14400]]}}}
    text = tutor.snapshot({"lessons": {}, "mine": own}, [], data, today="2026-10-12")
    assert "## Their own use case" in text and "user: Platform team" in text and "owner" not in text.split("## Their own use case")[1].split("##")[0].split("Their use case card:")[1].split(".")[0]
    assert "Reply within 3 seconds" in text and "must never: never close a P1" in text
    assert "$40,800 over 2 years" in text and "Azure AI Search $14,400" in text
    older = dict(own, updatedAt=1, card={"user": "old"})
    assert tutor.merge_progress({"mine": own}, {"mine": older})["mine"]["card"]["user"] == "Platform team", "the newer copy wins"
    assert "Not written yet." in tutor.snapshot({"lessons": {}}, [], data, today="2026-10-12")
    idea = {"updatedAt": 1, "idea": {"problem": "people wait a day for answers", "who": "platform users", "what": "get answers from runbooks",
                                     "measure": "wait under 1 hour", "harm": True, "mode": "augment", "value": "high", "doable": "high"}}
    text = tutor.snapshot({"lessons": {}, "mine": idea}, [], data, today="2026-10-12")
    assert 'use case "Help platform users get answers from runbooks so wait under 1 hour"' in text
    assert "failed gates: unchecked harm" in text and "rated high value, high doable" in text

