"""prepare_one runs the code checks before the judge, and redrafts with the reason."""

from __future__ import annotations

import json

import pytest

from drill import tutor_prepared as tp
from drill.content.build import build_data

PASS = json.dumps({"correct": True, "answers_it": True, "plain": True, "no_giveaway": True, "standalone": True, "notes": ""})


@pytest.fixture(scope="module")
def chip():
    data = build_data()
    lid, items = next(iter(tp.chips(data).items()))
    return data, lid, items[0]


def test_a_draft_that_breaks_a_code_check_is_redrafted_before_the_judge_sees_it(chip):
    data, lid, c = chip
    prompts, judged = [], []
    long = "This sentence is short and clear and fine. " * 60      # about 480 words: over the limit
    good = "This sentence is short and clear and fine. It answers the question in plain words."

    def draft(text):
        prompts.append(text)
        return long if len(prompts) == 1 else good

    def judge(text):
        judged.append(text)
        return PASS

    rec = tp.prepare_one(data, lid, c, draft, judge)
    assert rec["status"] == "passed" and rec["a"] == good
    assert len(prompts) == 2 and "over the word limit" in prompts[1]   # the second draft was told why
    assert len(judged) == 1                                          # the judge saw only the draft that could be served
    assert rec["quality"]["blocking"] == [] and rec["judge"]["version"] == 1


def test_checklist_two_can_judge_a_draft(chip):
    data, lid, c = chip
    v2 = json.dumps({"no_contradiction": True, "within_lesson": False, "answers_it": True, "no_giveaway": True, "standalone": True,
                     "concise": True, "tone": True, "notes": "adds a fact"})
    rec = tp.prepare_one(data, lid, c, lambda _: "A short, clear answer in plain words.", lambda _: v2, judge_version=2)
    assert rec["status"] == "passed" and rec["judge"]["within_lesson"] is False and rec["judge"]["version"] == 2
