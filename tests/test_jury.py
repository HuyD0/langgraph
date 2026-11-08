"""The jury's pure parts: votes, planted answers, labels, the numbers. No model, no MLflow."""

from __future__ import annotations

import json

from drill import jury


def test_consensus_majority_split_and_tie():
    assert jury.consensus([True, True, False]) == (True, True)
    assert jury.consensus([True, True, True]) == (True, False)
    assert jury.consensus([False, False, False]) == (False, False)
    assert jury.consensus([True, False]) == (False, True)  # a tie is not a pass, and it is a split
    assert jury.consensus([True, None, None]) == (True, False)  # unread votes don't count
    assert jury.consensus([None, None]) == (None, False)


def _real(i: int, phase: str = "Design", step: str = "Learn") -> dict:
    return {"id": f"l{i}:k", "lesson_id": f"l{i}", "key": "k", "step": step, "phase": phase, "kind": "term",
            "question": "q", "answer": f"answer {i}", "fingerprint": "f", "planted": "", "truth": None, "reference_pass": True}


def test_plants_break_one_rule_each_and_are_repeatable():
    data = {"lessons": {f"l{i}": {"check": ["Which?", ["A", "B"], 1, "why"]} for i in range(80)}}
    pool = [_real(i, phase="Design" if i % 2 else "Ship", step="Check" if i % 3 == 0 else "Learn") for i in range(80)]
    a = jury.plants(pool, data, per_kind=5)
    assert [p["id"] for p in a] == [p["id"] for p in jury.plants(pool, data, per_kind=5)]
    assert {p["planted"] for p in a} == set(jury.PLANT_KINDS) and len(a) == 15
    assert all(p["truth"] is False and p["reference_pass"] is None for p in a)
    for p in a:
        base = next(r for r in pool if r["lesson_id"] == p["lesson_id"])
        if p["planted"] == "giveaway":
            assert p["step"] != "Check" and p["answer"].endswith('the right option is "B".')
        elif p["planted"] == "maths":
            assert p["answer"] == base["answer"] + jury.MATHS
        else:
            assert p["answer"] != base["answer"]


def test_features_measure_the_text():
    f = jury.features("First sentence here. Second one.\n\n- a list item\n\nUse `x`.")
    assert f["words"] == 11 and f["has_list"] and f["has_code"] and f["est_tokens"] > 0


def test_cache_key_depends_on_model_and_prompt(tmp_path):
    a, b = jury.PANELS["local"][0], jury.PANELS["local"][1]
    assert jury.VerdictCache.key(a, "p") == jury.VerdictCache.key(a, "p")
    assert jury.VerdictCache.key(a, "p") != jury.VerdictCache.key(b, "p")
    assert jury.VerdictCache.key(a, "p") != jury.VerdictCache.key(a, "q")
    c = jury.VerdictCache(tmp_path / "c.jsonl")
    c.put("k", '{"correct": true}', {"seconds": 1})
    assert jury.VerdictCache(tmp_path / "c.jsonl").get("k")["reply"] == '{"correct": true}'


def test_ask_reuses_the_cache_and_counts_unread_replies(tmp_path):
    judge = jury.PANELS["local"][0]
    calls = []
    ok = '{"correct": true, "answers_it": true, "plain": true, "no_giveaway": true, "standalone": true, "notes": ""}'

    def chat(prompt):
        calls.append(prompt)
        return (ok if prompt == "good" else "no json here"), {"seconds": 0.1}

    cache = jury.VerdictCache(tmp_path / "c.jsonl")
    first = jury.ask(judge, {"a": "good", "b": "bad"}, cache, chat=chat, workers=1)
    assert first["a"]["pass"] and first["a"]["parsed"] and not first["a"]["cached"]
    assert not first["b"]["parsed"]  # unread, not a fail
    again = jury.ask(judge, {"a": "good"}, cache, chat=chat, workers=1)
    assert again["a"]["cached"] and len(calls) == 2
    jury.ask(judge, {"a": "good"}, cache, chat=chat, workers=1, fresh=True)
    assert len(calls) == 3


def test_labels_count_only_for_the_text_seen(tmp_path):
    path = tmp_path / "labels.json"
    item = {"id": "l1:k", "fingerprint": "f1", "planted": ""}
    jury.save_label("l1:k", "f1", False, "wrong fact", "me", path)
    labels = jury.load_labels(path)
    assert jury.person_label(item, labels) is False
    assert jury.person_label({**item, "fingerprint": "f2"}, labels) is None


def _row(i, planted, votes, person=None, words=50, ref=True):
    jv, split = jury.consensus(list(votes.values()))
    return {"id": str(i), "planted": planted, "reference_pass": None if planted else ref, "person": person,
            "votes": votes, "jury": jv, "split": split, "features": {"words": words}}


def test_analyse_scores_catches_keeps_and_splits():
    rows = ([_row(i, "maths", {"a": False, "b": False, "c": True}) for i in range(10)]
            + [_row(10 + i, "giveaway", {"a": True, "b": False, "c": True}) for i in range(10)]
            + [_row(20 + i, "", {"a": True, "b": True, "c": True}, person=True, words=20 + i) for i in range(30)])
    n = jury.analyse(rows, ["a", "b", "c"])
    a, b = n["judges"][0], n["judges"][1]
    assert a["catch_planted"]["rate"] == 0.5 and b["catch_planted"]["rate"] == 1.0
    assert n["jury"]["catch_planted"]["rate"] == 0.5 and n["jury"]["keep_reference_passed"]["rate"] == 1.0
    assert n["jury"]["vs_labels"]["n"] == 30
    assert n["wrong_when_split"]["n"] == 20 and n["wrong_when_split"]["rate"] == 0.5
    assert n["wrong_when_unanimous"]["rate"] == 0.0
    assert n["jury_vs_best"]["best"] == "b" and n["jury_vs_best"]["only_best_right"] == 10
    assert n["bias"]["a"]["short"]["n"] + n["bias"]["a"]["long"]["n"] == 30


def test_import_keeps_agreed_labels_as_ai_and_measures_agreement(tmp_path):
    items = [{"id": f"l{i}:k", "fingerprint": "f", "planted": ""} for i in range(4)]
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text("\n".join(json.dumps({"id": f"l{i}:k", "fingerprint": "f", "pass": i != 0, "note": "wrong" if i == 0 else ""}) for i in range(4)))
    b.write_text("\n".join(json.dumps({"id": f"l{i}:k", "fingerprint": "f", "pass": i not in (0, 1), "note": ""}) for i in range(4)))
    labels = tmp_path / "labels.json"
    out = jury.import_labels({"a": a, "b": b}, items, labels)
    assert out["disagree"] == ["l1:k"] and out["saved"] == 3 and out["labeller_agreement"] == 0.75
    saved = jury.load_labels(labels)
    assert saved["l0:k"]["pass"] is False and saved["l0:k"]["source"] == "ai" and "l1:k" not in saved
    jury.import_labels({"a": a, "b": b}, items, labels, settled={"l1:k": {"pass": True, "by": "third read"}})
    assert jury.load_labels(labels)["l1:k"]["pass"] is True
