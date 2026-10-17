"""The tutor's feedback, read back: the numbers to watch and the eval cases (drill.tutor_feedback)."""

from drill.tutor_feedback import Answer, cases, summarise


def answers():
    return [
        Answer("a1", "split_requirements", "Check", "Why not B?", "Because...", feedback={"resolved": False}),
        Answer("a2", "split_requirements", "Check", "Still stuck", "Simpler...", retry_of="a1", feedback={"resolved": True}),
        Answer("b1", "use_case_score", "Learn", "What is a gate?", "A gate is...", feedback={"resolved": True, "saved": True, "next_right": True}),
        Answer("c1", "use_case_score", "Learn", "What's a gate", "A gate...", feedback={"asked_again": True}),
        Answer("d1", "field_status", "Explain", "Quiz me", "Which field...", feedback={"gave_up": True}),
    ]


def test_first_answer_resolution_leaves_re_explanations_out():
    s = summarise(answers())
    assert (s["answers"], s["first_answers"], s["rated"]) == (5, 4, 2)
    assert s["first_answer_resolved"] == 0.5 and s["still_stuck"] == 1 and s["retry_resolved"] == 1.0
    assert s["saved"] == {"answers": 1, "true": 1} and s["next_right"] == {"answers": 1, "true": 1}
    assert dict(s["lessons_most_stuck"]) == {"split_requirements": 1, "use_case_score": 1, "field_status": 1}


def test_answers_that_did_not_help_become_cases_with_the_better_answer_when_there_is_one():
    by_question = {r["inputs"]["question"]: r["expectations"] for r in cases(answers())}
    assert set(by_question) == {"Why not B?", "What's a gate"}  # Still stuck, and asked again
    assert by_question["Why not B?"] == {"failed_answer": "Because...", "better_answer": "Simpler..."}
    assert by_question["What's a gate"] == {"failed_answer": "A gate..."}


def test_no_ratings_is_not_zero():
    assert summarise([Answer("x1")])["first_answer_resolved"] is None
