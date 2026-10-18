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


FAIL = json.dumps({"correct": False, "answers_it": True, "plain": True, "no_giveaway": True, "standalone": True,
                   "notes": "it now contradicts the lesson's number"})
OLD = "This sentence is short and clear and fine. It answers the question in plain words."


def test_a_stale_answer_that_still_passes_is_kept_without_a_new_draft(chip):
    data, lid, c = chip
    drafts, judged = [], []
    previous = {"q": c["q"], "a": OLD, "status": "passed", "fingerprint": "old", "model": "the drafter of the time"}
    rec = tp.prepare_one(data, lid, c, lambda t: drafts.append(t) or "new", lambda t: judged.append(t) or PASS, previous=previous)
    assert rec["a"] == OLD and rec["status"] == "passed" and rec["kept"]
    assert drafts == [] and len(judged) == 1                             # one judge call, no drafting
    assert rec["fingerprint"] == tp.fingerprint(data, lid, c)           # now matches the lesson as it is
    assert rec["model"] == "the drafter of the time"


def test_a_stale_answer_the_judge_now_fails_is_redrafted_with_its_reason(chip):
    data, lid, c = chip
    drafts, verdicts = [], iter([FAIL, PASS])
    previous = {"q": c["q"], "a": OLD, "status": "passed", "fingerprint": "old"}
    rec = tp.prepare_one(data, lid, c, lambda t: drafts.append(t) or "A new short answer in plain words.",
                         lambda _: next(verdicts), previous=previous)
    assert rec["a"] != OLD and rec["status"] == "passed" and not rec.get("kept")
    assert len(drafts) == 1 and "contradicts the lesson's number" in drafts[0]


@pytest.mark.parametrize("change", [{"status": "failed"}, {"status": "rejected"}, {"q": "a question that was reworded"}, {"a": ""}])
def test_only_a_passed_answer_to_the_same_question_is_reused(chip, change):
    data, lid, c = chip
    previous = {"q": c["q"], "a": OLD, "status": "passed", **change}
    assert not tp.reusable(previous, c)
    drafts = []
    tp.prepare_one(data, lid, c, lambda t: drafts.append(t) or OLD, lambda _: PASS, previous=previous)
    assert len(drafts) == 1


def test_the_reasoning_setting_reaches_the_request_and_unknown_ones_are_refused(monkeypatch):
    sent = {}

    class Completions:
        def create(self, **kw):
            sent.update(kw)
            from types import SimpleNamespace as NS
            return NS(choices=[NS(message=NS(content="{}"))], usage=NS(prompt_tokens=1, completion_tokens=1))

    class FakeOpenAI:
        def __init__(self, **_):
            from types import SimpleNamespace as NS
            self.chat = NS(completions=Completions())

    import openai
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    monkeypatch.setattr("drill.server.router.gateway_base_url", lambda host, model: "http://x")
    monkeypatch.setattr("databricks.sdk.config.Config", lambda **_: type("C", (), {"host": "h"})())
    tp.databricks_chat("m", None, "off")("hi")
    assert sent["extra_body"] == {"thinking": {"type": "disabled"}}
    sent.clear()
    tp.databricks_chat("databricks-claude-sonnet-5-5", None, "off")("hi")
    assert sent["extra_body"] == {"thinking": {"type": "between_tools"}}   # what that endpoint asks for
    sent.clear()
    tp.databricks_chat("m", None)("hi")
    assert "extra_body" not in sent
    with pytest.raises(ValueError):
        tp.databricks_chat("m", None, "none")
