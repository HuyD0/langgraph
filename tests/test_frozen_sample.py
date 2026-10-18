"""The judge-tuning sample is drawn once and then frozen, like the splits."""

from __future__ import annotations

import json

from drill import tutor_prepared_eval as tpe


def rows(n, failed=(0, 1)):
    return [{"inputs": {"lesson_id": f"l{i % 7}", "key": f"k{i}", "phase": "Frame" if i % 2 else "Build", "kind": "check"},
             "expectations": {"reference_pass": i not in failed}} for i in range(n)]


def test_the_sample_is_frozen_and_new_answers_do_not_join(tmp_path, monkeypatch):
    monkeypatch.setattr(tpe, "SAMPLE_FILE", tmp_path / "prepared_sample.json")
    first, note = tpe.frozen_sample(rows(40), "dev", 20)
    assert note["sample_state"] == "frozen now" and 19 <= len(first) <= 21
    assert {r["inputs"]["key"] for r in first} >= {"k0", "k1"}                      # every reference failure is in
    again, note = tpe.frozen_sample(rows(60), "dev", 20)                              # 20 new answers appeared
    assert note == {"sample_state": "frozen", "sample_missing": 0, "sample_changed": 0}
    assert [r["inputs"]["key"] for r in again] == [r["inputs"]["key"] for r in first]
    saved = json.loads((tmp_path / "prepared_sample.json").read_text())
    assert len(saved["dev"]["20"]) == 20


def test_a_stale_answer_drops_out_and_refresh_redraws(tmp_path, monkeypatch):
    monkeypatch.setattr(tpe, "SAMPLE_FILE", tmp_path / "prepared_sample.json")
    first, _ = tpe.frozen_sample(rows(40), "dev", 20)
    fewer = [r for r in rows(40) if r["inputs"]["key"] != first[0]["inputs"]["key"]]  # that answer is no longer served
    kept, note = tpe.frozen_sample(fewer, "dev", 20)
    assert len(kept) == 19 and note["sample_missing"] == 1
    redrawn, note = tpe.frozen_sample(fewer, "dev", 20, refresh=True)
    assert 19 <= len(redrawn) <= 21 and note["sample_state"] == "refreshed"   # the draw rounds per group: about n


def test_a_redrafted_answer_is_counted_as_changed(tmp_path, monkeypatch):
    monkeypatch.setattr(tpe, "SAMPLE_FILE", tmp_path / "prepared_sample.json")
    fps = {(r["inputs"]["lesson_id"], r["inputs"]["key"]): "fp-old" for r in rows(40)}
    first, _ = tpe.frozen_sample(rows(40), "dev", 20, fingerprints=fps)
    changed = dict(fps)
    changed[(first[0]["inputs"]["lesson_id"], first[0]["inputs"]["key"])] = "fp-new"
    _, note = tpe.frozen_sample(rows(40), "dev", 20, fingerprints=changed)
    assert note["sample_changed"] == 1 and note["sample_missing"] == 0
