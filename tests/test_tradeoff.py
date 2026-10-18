"""The cost, speed and quality pieces in drill.tradeoff."""

from __future__ import annotations

from pathlib import Path

import pytest

from drill import tradeoff as t
from drill import tutor_prepared as tp
from drill.content.build import build_data

ASK_JS = Path(__file__).resolve().parents[1] / "src" / "drill" / "content" / "page" / "ask.js"


@pytest.fixture(scope="module")
def data():
    return build_data()


def test_the_rules_are_the_pages_own():
    """The cacheable version moves the rules, never rewords them: each line is in page/ask.js as written."""
    page = ASK_JS.read_text(encoding="utf-8").replace("\\`", "`").replace("${cur.p.fn}", "{fn}")
    for line in t.rules("{fn}", practice=True).splitlines():
        assert line in page, f"not in page/ask.js: {line}"


def test_both_versions_send_the_same_words(data):
    lid, items = next(iter(tp.chips(data).items()))
    chip = items[0]
    today = t.today_messages(data, lid, chip)[0]["content"]
    system, user = t.cacheable_messages(data, lid, chip)
    assert system["content"][0]["cache_control"] == {"type": "ephemeral"}
    words = lambda s: sorted(s.split())
    assert words(today) == words(system["content"][0]["text"] + " " + user["content"])
    assert today.startswith(t.INTRO + tp.LEARNER) and "Their message: " + chip["q"] in today
    assert t.fixed_start(data, lid, chip, "cacheable") > t.fixed_start(data, lid, chip, "today")


def test_answer_cost_counts_the_cache():
    full = t.answer_cost("databricks-claude-sonnet-5-5", 2000, 300)
    cached = t.answer_cost("databricks-claude-sonnet-5-5", 200, 300, cache_read=1800)
    assert full == pytest.approx((2000 * 2 + 300 * 10) / 1e6)
    assert cached == pytest.approx((200 * 2 + 1800 * 2 * 0.05 + 300 * 10) / 1e6)  # Sonnet 5.5 reads at 0.05x
    assert t.answer_cost("databricks-claude-haiku-5-5", 200, 300, cache_read=1800) == pytest.approx(
        (200 * 0.1 + 1800 * 0.1 * 0.1 + 300 * 0.5) / 1e6)
    assert t.answer_cost("databricks-claude-sonnet-5-5", 200, 300, cache_write=1800) > full
    assert t.answer_cost("a-local-model", 2000, 300) == 0.0


def test_hit_rate():
    rows = [{"input_tokens": 200, "cache_write": 1800}, {"input_tokens": 200, "cache_read": 1800}]
    assert t.hit_rate(rows) == pytest.approx(1800 / 4000)
    assert t.hit_rate([]) == 0.0


def test_percentile():
    times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert t.percentile(times, 50) == 5
    assert t.percentile(times, 95) == 10
    assert t.percentile([3.0], 95) == 3.0
    assert t.percentile([], 95) == 0.0


def test_cache_pass_needs_a_long_start_and_a_recent_call():
    order = [{"lesson_id": "a", "at": 0}, {"lesson_id": "a", "at": 60}, {"lesson_id": "a", "at": 60 + 6 * 60},
             {"lesson_id": "b", "at": 400}]
    out = t.cache_pass(order, {"a": 1500, "b": 700}, minimum=1024)
    assert out == [{"cache_read": 0, "cache_write": 1500}, {"cache_read": 1500, "cache_write": 0},
                   {"cache_read": 0, "cache_write": 1500}, {"cache_read": 0, "cache_write": 0}]


def test_pareto_drops_what_is_beaten():
    vs = [{"name": "a", "quality": .9, "cost": 2, "p95": 3}, {"name": "b", "quality": .8, "cost": 1, "p95": 3},
          {"name": "c", "quality": .8, "cost": 3, "p95": 4}, {"name": "d", "quality": .9, "cost": 2, "p95": 3}]
    assert t.pareto(vs) == ["a", "b", "d"]  # c loses to a on everything; a and d tie, so both stay


def test_paired_difference_on_the_same_questions():
    base = {("l1", "q1"): True, ("l1", "q2"): False, ("l2", "q1"): True, ("l2", "q2"): True}
    new = {**base, ("l1", "q2"): True, ("l9", "q1"): False}  # l9 only in new: not counted
    diff, lo, hi = t.paired_difference(base, new)
    assert diff == pytest.approx(0.25) and lo <= diff <= hi


def test_choose_applies_the_rule_in_order():
    vs = [{"name": "base", "diff_low": 0.0, "p95": 4, "cost": 5},
          {"name": "cheap-but-worse", "diff_low": -0.08, "p95": 2, "cost": 1},
          {"name": "cheap-and-slow", "diff_low": -0.01, "p95": 9, "cost": 1},
          {"name": "cheaper", "diff_low": -0.02, "p95": 3, "cost": 2}]
    out = t.choose(vs, margin=0.03, p95_limit=5)
    assert out["choice"] == "cheaper"
    assert out["dropped"] == {"cheap-but-worse": "quality", "cheap-and-slow": "speed"}
    assert t.choose(vs[1:3], margin=0.03, p95_limit=5)["choice"] is None


def test_each_model_has_its_own_minimum_and_read_rate():
    assert t.min_cacheable("databricks-claude-sonnet-5-5") == 512
    assert t.min_cacheable("databricks-claude-haiku-5-5") == 512
    assert t.min_cacheable("gpt-5.4-mini") == 1024
    assert t.cache_read_rate("databricks-claude-opus-5-5") == 0.05
    assert t.cache_read_rate("databricks-claude-haiku-5-5") == 0.1
