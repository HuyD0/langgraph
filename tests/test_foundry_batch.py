"""The batch pieces in drill.foundry_batch that need no Azure: the request file and reading the output."""

from __future__ import annotations

import json

import pytest

from drill import foundry_batch as fb


def test_one_line_per_request_with_its_custom_id():
    rows = fb.lines([("l/a", [{"role": "user", "content": "hi"}]), ("l/b", [{"role": "user", "content": "yo"}])], "dep", max_tokens=99)
    assert [r["custom_id"] for r in rows] == ["l/a", "l/b"]
    assert rows[0] == {"custom_id": "l/a", "method": "POST", "url": "/chat/completions",
                       "body": {"model": "dep", "messages": [{"role": "user", "content": "hi"}], "max_completion_tokens": 99}}
    assert [json.loads(x) for x in fb.jsonl(rows).decode().splitlines()] == rows


def test_custom_ids_must_be_unique():
    with pytest.raises(ValueError):
        fb.lines([("same", []), ("same", [])], "dep")


def test_reading_output_lines():
    ok = {"custom_id": "a", "response": {"status_code": 200, "body": {
        "choices": [{"message": {"content": "Hello"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 2}}}}
    bad = {"custom_id": "b", "response": {"status_code": 429, "body": {"error": {"message": "Too many requests"}}}}
    err = {"custom_id": "c", "error": {"message": "invalid"}}
    assert fb.parse_line(ok) == {"text": "Hello", "finish": "stop", "usage": {"prompt_tokens": 10, "completion_tokens": 2}}
    assert fb.parse_line(bad) == {"error": "Too many requests"}
    assert fb.parse_line(err) == {"error": "invalid"}


def test_retry_what_failed_or_never_came_back():
    rows = [{"custom_id": c} for c in "abc"]
    assert fb.to_retry(rows, {"a": {"text": "x"}, "b": {"error": "y"}}) == [{"custom_id": "b"}, {"custom_id": "c"}]


def test_batch_is_half_price_and_cached_input_a_tenth():
    usage = {"prompt_tokens": 1000, "completion_tokens": 200, "prompt_tokens_details": {"cached_tokens": 400}}
    standard = fb.cost("gpt-5.4-mini", "standard", usage)
    assert standard == pytest.approx((600 * 0.75 + 400 * 0.075 + 200 * 4.5) / 1e6)
    assert fb.cost("gpt-5.4-mini", "batch", usage) == pytest.approx(standard / 2)


def test_the_tutor_and_judge_requests():
    from drill import tutor_prepared as tp
    from drill.content.build import build_data

    data = build_data()
    lid, items = next(iter(tp.chips(data).items()))
    q = {"lesson_id": lid, "key": items[0]["key"], "chip": items[0]}
    (cid, messages), = fb.answer_requests(data, [q])
    assert cid == f"{lid}/{items[0]['key']}" and items[0]["q"] in messages[0]["content"]
    assert fb.judge_requests(data, [q], {}) == []
    (jcid, jm), = fb.judge_requests(data, [q], {cid: "An answer."})
    assert jcid == cid and "An answer." in jm[0]["content"] and "Reply with JSON only" in jm[0]["content"]


def test_live_answers_may_end_with_a_question():
    strict, live = fb.judge_prompt(live=False), fb.judge_prompt(live=True)
    assert fb.STRICT_STANDALONE in strict and fb.STRICT_STANDALONE not in live
    assert "Ending with one question back to the learner is fine" in live
    assert strict.replace(fb.STRICT_STANDALONE, "") == live.replace(fb.LIVE_STANDALONE, "")


def test_newer_models_charge_to_write_the_cache():
    usage = {"prompt_tokens": 1000, "completion_tokens": 100, "prompt_tokens_details": {"cached_tokens": 300, "cache_write_tokens": 200}}
    assert fb.cost("gpt-6.1-sol", "standard", usage) == pytest.approx((500 * 2.0 + 300 * 0.1 + 200 * 2.5 + 100 * 10.0) / 1e6)


def test_chunks_stay_under_the_enqueued_limit():
    rows = fb.lines([(f"q{i}", [{"role": "user", "content": "x" * 400}]) for i in range(10)], "dep")
    parts = fb.chunks(rows, limit_tokens=300)
    assert [r["custom_id"] for p in parts for r in p] == [r["custom_id"] for r in rows]
    assert len(parts) > 1 and all(sum(len(json.dumps(r["body"]["messages"])) // 4 + 1 for r in p) <= 300 for p in parts)


def test_an_empty_reply_is_a_missing_verdict_not_a_fail():
    line = {"custom_id": "a", "response": {"status_code": 200, "body": {
        "choices": [{"message": {"content": None}, "finish_reason": "length"}], "usage": {"prompt_tokens": 9, "completion_tokens": 2000}}}}
    out = fb.parse_line(line)
    assert "text" not in out and "empty reply" in out["error"]
    assert fb.to_retry([{"custom_id": "a"}], {"a": out}) == [{"custom_id": "a"}]


def test_unknown_prices_refuse_rather_than_cost_nothing():
    with pytest.raises(ValueError):
        fb.cost("gpt-5.6-luna", "batch", {"prompt_tokens": 10, "completion_tokens": 1})
    assert fb.chunks([]) == []


class _FailingBatchApi:
    """A Foundry whose batch job ends failed with no output file."""

    class files:
        @staticmethod
        def create(file, purpose):
            class F: id = "file-1"
            return F()

        @staticmethod
        def content(file_id):
            raise AssertionError("no output file should be read")

    class batches:
        @staticmethod
        def create(**kw):
            class B: id = "batch-1"
            return B()

        @staticmethod
        def retrieve(bid):
            class Counts: total, completed, failed = 3, 0, 3

            class B:
                id, status, output_file_id, error_file_id, request_counts = "batch-1", "failed", None, None, Counts()
            return B()


def test_a_part_the_queue_refused_is_not_resent_and_not_dropped():
    with pytest.raises(RuntimeError, match="ended failed"):
        fb.batched_chat({"a": "p1", "b": "p2", "c": "p3"}, "dep", "gpt-5.4", api=_FailingBatchApi(), every=0)


def test_the_live_judge_prompt_exists_for_both_checklists():
    for version in (1, 2):
        live = fb.judge_prompt(live=True, version=version)
        assert fb.LIVE_STANDALONE in live and fb.STRICT_STANDALONE not in live
    assert fb.giveaway_clause({"step": "Learn"}, "f").endswith("is right") and fb.giveaway_clause({"step": "Check"}, "") == ""
