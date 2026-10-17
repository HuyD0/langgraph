"""Sticker callbacks and Look again questions (content/callbacks.py): the rules that keep them honest."""
import re

import pytest

from drill.content import build_data, modules
from drill.content.build import page_source
from drill.content.callbacks import CALLBACKS
from drill.content.modules import PATH, TRACKS
from drill.content.trust import NOTES


@pytest.fixture(scope="module")
def data():
    return build_data()


@pytest.fixture(scope="module")
def loaded():
    return modules.load()


@pytest.fixture(scope="module")
def order(data):
    """Every lesson in the order a learner meets them: the path, then the track."""
    by_id = {m["id"]: m for m in data["modules"]}
    mids = list(PATH) + [m for t in TRACKS for m in t[3]]
    return [lid for mid in mids if mid in by_id for lid in by_id[mid]["lessons"]]


def test_each_callback_points_back_to_an_earlier_lesson(order):
    place = {lid: i for i, lid in enumerate(order)}
    for lesson_id, links in CALLBACKS.items():
        assert lesson_id in place, f"callbacks for unknown lesson {lesson_id}"
        assert 1 <= len(links) <= 2, f"{lesson_id}: one or two callbacks, never more"
        assert sum(1 for c in links if c["again"]) <= 1, f"{lesson_id}: at most one Look again question"
        assert len({c["to"] for c in links}) == len(links), f"{lesson_id}: one callback per earlier lesson"
        for c in links:
            assert c["to"] in place and place[c["to"]] < place[lesson_id], f"{lesson_id}: {c['to']} must come earlier"


def test_each_callback_sits_on_real_words(loaded):
    learn = {entry["id"]: entry["learn"] for mod in loaded for entry in mod.lessons}
    for lesson_id, links in CALLBACKS.items():
        trust_phrase = NOTES.get(lesson_id, {}).get("phrase")
        for c in links:
            hits = [p for p in learn[lesson_id] if c["phrase"] in p]
            assert len(hits) == 1 and hits[0].count(c["phrase"]) == 1, f"{lesson_id}: phrase must appear exactly once"
            before = hits[0].split(c["phrase"])[0] + c["phrase"]
            assert before.count("**") % 2 == 0 and before.count("`") % 2 == 0, f"{lesson_id}: phrase cuts through markup"
            if trust_phrase:
                assert c["phrase"] not in trust_phrase and trust_phrase not in c["phrase"], f"{lesson_id}: overlaps the trust mark"
            assert len(c["idea"].split()) <= 4, f"{lesson_id}: idea is a few words, the card's heading"
            assert 30 < len(c["here"]) < 200 and "*" not in c["here"], f"{lesson_id}: here is one or two short plain sentences"
        phrases = [c["phrase"] for c in links]
        assert not any(a != b and a in b for a in phrases for b in phrases), f"{lesson_id}: phrases overlap"


def test_look_again_questions_follow_the_check_rules():
    for lesson_id, links in CALLBACKS.items():
        for c in links:
            q = c["again"]
            if not q:
                continue
            opts, right = q["options"], q["options"][q["answer"]]
            assert len(opts) == 3, f"{lesson_id}: three options, like the Check step"
            assert q["clue"] and right.lower() not in q["clue"].lower(), f"{lesson_id}: a clue that doesn't give it away"
            longest_wrong = max(len(o) for i, o in enumerate(opts) if i != q["answer"])
            assert len(right) <= 1.3 * longest_wrong + 10, f"{lesson_id}: the right option gives itself away by length"
            assert not re.search(r"\d+\s*%", q["question"] + "".join(opts)), f"{lesson_id}: say 9 in 10, not 90%"


def test_the_page_gets_callbacks_and_one_look_again(data):
    for lesson_id, links in CALLBACKS.items():
        entry = data["lessons"][lesson_id]
        assert [c[0] for c in entry["callbacks"]] == [c["to"] for c in links]
        again = [c for c in links if c["again"]]
        assert ("again" in entry) == bool(again)
        if again:
            assert entry["again"][0] == again[0]["to"] and entry["again"][3] == again[0]["again"]["answer"]
    assert sum(1 for e in data["lessons"].values() if "callbacks" in e) == len(CALLBACKS)


def test_callbacks_are_wired_into_the_learn_step():
    """The mark goes after its phrase inside withTrust, the card opens under the paragraph, the
    Look again card sits after Learn's example, and its picks are saved and merged like the rest."""
    page = page_source()
    learn = page.split("function learnPane()")[1].split("\n}")[0]
    assert "closeCb()" in learn and "againHtml(cur.id)" in learn
    with_trust = page.split("function withTrust(")[1].split("\n}")[0]
    assert "cbMarkHtml(id, i)" in with_trust and "cbPopHtml(id, i)" in with_trust
    assert 'store.set("drill-cb-seen"' in page and "again: v.again || o.again" in page
    assert "--path" in page.split("callbacks (content/callbacks.py)")[1] and ".cbmark.tr" in page


def test_the_tutor_merge_keeps_look_again():
    from drill.tutor import merge_progress

    a = {"lessons": {"backoff_delays": {"step": 1, "done": False, "again": {"wrong": [1], "right": True}}}}
    b = {"lessons": {"backoff_delays": {"step": 2, "done": True}}}
    assert merge_progress(a, b)["lessons"]["backoff_delays"]["again"] == {"wrong": [1], "right": True}


def test_every_called_back_lesson_is_a_real_lesson(data):
    called = {c["to"] for links in CALLBACKS.values() for c in links}
    assert called <= set(data["lessons"]), called - set(data["lessons"])
    assert {"split_requirements", "well_architected", "fit_for_purpose"} <= called, "the Frame foundations come back"
