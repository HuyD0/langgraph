"""The signals in drill.draft_uncertainty, with no model and no Azure."""

from __future__ import annotations

import math

import pytest

from drill import draft_uncertainty as du
from drill import foundry_batch as fb


def test_confidence_reads_token_log_probabilities():
    toks = [("Recall", -0.1), ("@", -0.05), ("5", -2.0), (" counts", -0.2), (" the", -0.01), (" top", -0.3), (" Ana", -1.5), (".", -0.01)]
    c = du.confidence(toks)
    assert c["mean_logprob"] == pytest.approx(sum(lp for _, lp in toks) / len(toks))
    assert c["min_prob"] == pytest.approx(math.exp(-2.0))
    assert c["risky_min_prob"] == pytest.approx(math.exp(-2.0))       # the digit "5" (0.14) is riskier than " Ana" (0.22)
    assert all(math.isnan(v) for v in du.confidence([]).values())


def test_disagreement_between_drafts():
    same = ["Recall@5 counts the right documents in the top 5.", "Recall@5 counts the right documents in the top 5."]
    d = du.disagreement(same)
    assert d[0]["disagreement"] == pytest.approx(0.0) and d[0]["numbers_differ"] == 0.0
    diff = ["Recall@5 counts the right documents in the top 5.", "Precision measures how many results were useful, about 40%."]
    d = du.disagreement(diff)
    assert d[0]["disagreement"] > 0.5 and d[0]["numbers_differ"] == 1.0


def test_auc_is_half_for_no_signal_and_one_for_perfect():
    assert du.auc([0.9, 0.8, 0.2, 0.1], [True, True, False, False]) == 1.0
    assert du.auc([0.5, 0.5, 0.5, 0.5], [True, True, False, False]) == 0.5
    assert du.auc([0.1, 0.2, 0.8, 0.9], [True, True, False, False]) == 0.0
    assert du.auc([0.1, 0.2], [True, True]) is None


def test_batch_lines_can_ask_for_logprobs_and_the_output_keeps_them():
    row = fb.lines([("q", [{"role": "user", "content": "hi"}])], "dep", extra={"logprobs": True})[0]
    assert row["body"]["logprobs"] is True
    out = fb.parse_line({"custom_id": "q", "response": {"status_code": 200, "body": {
        "choices": [{"message": {"content": "Hi"}, "finish_reason": "stop", "logprobs": {"content": [{"token": "Hi", "logprob": -0.2}]}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1}}}})
    assert out["logprobs"] == [("Hi", -0.2)] and out["text"] == "Hi"


def test_numbers_ignore_trailing_punctuation_and_empty_siblings_do_not_poison():
    assert du.numbers_in("Keep the top 5.") == {"5"} and du.numbers_in("1,536 numbers, say.") == {"1536"}
    same = "Keep the top 5 results."
    d = du.disagreement([same, same, ""])
    assert d[0]["disagreement"] == pytest.approx(0.0) and d[0]["numbers_differ"] == 0.0
    assert math.isnan(d[2]["disagreement"]) and math.isnan(d[2]["numbers_differ"])
    assert all(math.isnan(x["disagreement"]) for x in du.disagreement([same, ""]))   # one draft can't disagree with itself
