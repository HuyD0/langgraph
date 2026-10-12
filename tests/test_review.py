"""The use case review: its shared prompt, the code checks, the planted-gap scoring and feedback."""

import re
from pathlib import Path

from drill.content import modules, review
from drill.content.build import build_data
from drill.review_checks import flags_gap, missing_pillars, review_checks
from drill.review_eval import CASES, score
from drill.server.observe import answer_checks, clean_context

GOOD = """**Reliability**
Risk: medium. Findings: "HR reviews each draft before sending".
**Security**
Risk: low.
**Cost Optimization**
Risk: medium. Unknown: is there a budget alert?
**Operational Excellence**
Risk: medium. Unknown: who is the owner who decides on releases?
**Performance Efficiency**
Risk: low.
**Data and AI governance**
Risk: medium. Unknown: which test data or examples exist?"""


def test_the_prompt_lists_the_card_every_pillar_and_the_rules():
    text = review.review_prompt({"user": "HR team", "owner": "  "})
    assert "- user: HR team" in text and "- owner: not written" in text
    assert all(f"## {p}" in text for p in review.PILLARS)
    assert text.endswith(review.ANSWER_FORMAT) and review.RULES[-1] in text


def test_the_page_and_the_lesson_use_the_shared_card_and_prompt():
    data = build_data()
    assert data["review"]["cardFields"] == review.CARD_FIELDS and data["review"]["pillars"] == review.PILLARS
    page = (Path(__file__).resolve().parents[1] / "src/drill/content/page.html").read_text()
    assert "const RV = D.review;" in page and "Reliability" not in page.split("const RV = D.review;")[1].split("// ---------- views")[0]
    lesson = {p["id"]: p for p in data["bank"]}["use_case_card"]
    fields = re.findall(r'"(\w+)"', lesson["solution"].split("fields = [")[1].split("]")[0])
    assert fields == [k for k, _l, _e in review.CARD_FIELDS], "the card lesson checks the same fields the page and review use"


def test_the_checks_catch_a_missing_pillar_a_verdict_and_silence_about_blanks():
    assert missing_pillars(GOOD) == []
    assert missing_pillars("Reliability only") == [p for p in review.PILLARS if p != "Reliability"]
    bad = review_checks("Reliability, Security. You should build it.", ["owner"])
    assert bad["missing_pillar"] and bad["decides_for_them"] and bad["no_unknowns_for_blanks"]
    ok = review_checks(GOOD, ["owner"])
    assert not ok["missing_pillar"] and not ok["decides_for_them"] and not ok["no_unknowns_for_blanks"]
    assert flags_gap(GOOD, ["owner"]) and not flags_gap(GOOD, ["feedback"])


def test_scoring_a_planted_gap_case():
    two = next(c for c in CASES if c["name"] == "two gaps")
    assert score(GOOD, two) == {"all_pillars": True, "gaps_flagged": True, "no_verdict": True, "must_pass": True}
    assert score(GOOD.replace("which test data or examples exist?", "none."), two)["gaps_flagged"] is False
    unchecked = next(c for c in CASES if c["high_risk"])
    assert score(GOOD, unchecked)["high_risk_named"] is False


def test_every_planted_case_is_a_real_card_with_known_gaps():
    keys = [k for k, _l, _e in review.CARD_FIELDS]
    for case in CASES:
        assert list(case["card"]) == keys, case["name"]
        for field, words in case["gaps"]:
            assert field in keys and words, case["name"]


def test_the_server_checks_reviews_and_keeps_the_request_id():
    checks = answer_checks("Reliability. I recommend building it.", {"feature": "use_case_review", "blank_fields": "owner"})
    assert checks["decides_for_them"] and checks["missing_pillar"] and checks["no_unknowns_for_blanks"]
    assert "decides_for_them" not in answer_checks("hello", {"feature": "ask_lesson"})
    ctx = clean_context({"request": "abc123def", "prompt_version": "review-v1", "blank_fields": "owner,data"})
    assert ctx == {"request": "abc123def", "prompt_version": "review-v1", "blank_fields": "owner,data"}


def test_the_judge_keeps_only_real_quoted_inventions():
    from drill import review_eval

    review_text = "Security: high. The system encrypts every answer with AES-256 keys. Unknown: who owns it?"
    claims = [
        "The HR team uses a tool called PolicyCentral for every answer",   # not in the review: the judge invented it
        "What specific data sources will the model use",                   # a question, not a claim
        "There's no mention of timeouts in the card at all",               # an observation about the card
        "The system encrypts every answer with AES-256 keys",              # really in the review, and not on the card
    ]

    class FakeRouter:
        async def ask_json(self, prompt, tier, context=None):
            return {"unsupported": claims}

    ok, kept = review_eval.judge_grounded(FakeRouter(), review_eval.FULL, review_text, "default")
    assert not ok and kept == ["The system encrypts every answer with AES-256 keys"]
