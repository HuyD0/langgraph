"""The code checks in drill.answer_quality: readable, concise, inside the lesson."""

from __future__ import annotations

from drill import answer_quality as aq
from drill import tutor_prepared as tp

LESSON = "Recall@5 asks whether the right documents made the top 5. A cache returns a stored answer. Databricks AI Search holds 2 million vectors."


def test_readability_grade_rises_with_long_words_and_sentences():
    easy = "The cat sat on the mat. It was warm."
    hard = ("Notwithstanding the aforementioned considerations, the implementation necessitates comprehensive "
            "architectural reorganisation across heterogeneous infrastructural components simultaneously.")
    assert aq.readability_grade(easy) < 4
    assert aq.readability_grade(hard) > 14
    assert aq.readability_grade("") == 0.0


def test_fillers_and_repeats():
    text = "Great question! Recall@5 counts the right documents in the top 5. Recall@5 counts the right documents in the top 5."
    assert aq.filler_openers(text) == ["great question"]
    assert aq.repeated_sentences(text) == 1
    assert aq.repeated_sentences("Short. Short.") == 0  # too short to count as a repeat


def test_terms_numbers_and_names_outside_the_lesson():
    text = "Recall@5 is the share in the top 5. Precision is different. An embedding (a list of numbers) helps. Then Ana saw 40% on Azure."
    assert aq.unexplained_terms(text, ["precision", "embedding", "recall"], LESSON) == ["precision"]  # embedding is glossed; recall is in the lesson
    assert aq.unknown_numbers(text, LESSON) == ["40"]            # 5 is in the lesson and small anyway
    assert aq.unknown_names(text, LESSON, allow=["Azure"]) == ["Ana"]


def test_quality_checks_names_what_blocks():
    text = "Great question! " + "This sentence is long enough to count as repeated text. " * 2
    c = aq.quality_checks(text, LESSON, ["precision"], word_limit=5)
    assert c["over_word_limit"] and c["repeated"] and c["fillers"] == ["great question"]
    assert c["blocking"] == ["over_word_limit", "repeated"]
    assert aq.quality_checks("Recall@5 counts the right documents in the top 5.", LESSON)["blocking"] == []


def test_the_two_checklists_parse_their_own_verdicts():
    v1 = tp._verdict('{"correct": true, "answers_it": true, "plain": false, "no_giveaway": true, "standalone": true, "notes": "jargon"}')
    assert v1["pass"] is False and v1["plain"] is False
    v2 = tp._verdict('{"no_contradiction": true, "within_lesson": false, "answers_it": true, "no_giveaway": true, "standalone": true, '
                     '"concise": false, "tone": true, "notes": "adds a fact"}', version=2)
    assert v2["pass"] is True and v2["within_lesson"] is False and v2["concise"] is False   # scored checks don't block
    assert tp._verdict('{"no_contradiction": false, "answers_it": true, "no_giveaway": true, "standalone": true}', version=2)["pass"] is False
    assert "within_lesson" in tp.JUDGE2 and "plain" not in tp.JUDGE2
