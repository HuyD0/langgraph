"""A person's review of prepared answers: sent to a review queue as traces, read back, and compared with the judges."""

from __future__ import annotations

import pytest

mlflow = pytest.importorskip("mlflow")

from mlflow.entities import AssessmentSource, AssessmentSourceType  # noqa: E402

from drill import tutor_prepared as tp  # noqa: E402
from drill import tutor_prepared_eval as tpe  # noqa: E402
from drill import tutor_review as tr  # noqa: E402
from drill.content.build import build_data  # noqa: E402


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.delenv("MLFLOW_EXPERIMENT_NAME", raising=False)
    monkeypatch.delenv("MLFLOW_EXPERIMENT_ID", raising=False)
    monkeypatch.setattr(tr, "PROJECT_ROOT", tmp_path)  # the file of what was sent goes in tmp, not the repo's .drill/
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path}/mlflow.db")
    mlflow.set_registry_uri(f"sqlite:///{tmp_path}/mlflow.db")
    yield mlflow.set_experiment("review").experiment_id
    mlflow.set_tracking_uri(None)


def human(trace_id, name, value, rationale=None, expectation=False):
    source = AssessmentSource(AssessmentSourceType.HUMAN, "reviewer@example.com")
    if expectation:
        mlflow.log_expectation(trace_id=trace_id, name=name, value=value, source=source)
    else:
        mlflow.log_feedback(trace_id=trace_id, name=name, value=value, rationale=rationale, source=source)


def two_answers():
    """Two real prepared answers that still match their lessons."""
    data, answers = build_data(), tp.load()
    by_key = {(lid, c["key"]): c for lid, cs in tp.chips(data).items() for c in cs}
    ids = [f"{lid}:{key}" for lid, recs in answers.items() for key, rec in recs.items()
           if rec.get("status") == "passed" and (lid, key) in by_key and rec["fingerprint"] == tp.fingerprint(data, lid, by_key[(lid, key)])][:2]
    return data, answers, ids


def test_send_then_read_on_a_local_store(store):
    data, answers, ids = two_answers()
    votes = {ids[0]: {"gpt-5.4": {"pass": False, "notes": "too long", "checks": {"plain": False, "correct": True},
                                  "model": "gpt-5.4", "prompt": "tutor_judge/1"}}}
    first = tr.send(data, answers, ids, votes, store, [], queues=tr.Local())
    again = tr.send(data, answers, ids, votes, store, [], queues=tr.Local())
    assert (first["added"], again["added"], again["already"]) == (2, 0, 2)
    tr.sent_path("local").unlink()  # as if a send stopped before its record: the traces are found and reused
    third = tr.send(data, answers, ids, votes, store, [], queues=tr.Local())
    assert (third["reused"], third["added"]) == (2, 0)
    sent = tr.load_sent("local")
    sent["items"]["tr-never-saved"] = {"id": ids[0], "fingerprint": "x", "votes": {}}  # a failed upload
    tr.save_sent("local", sent)
    fourth = tr.send(data, answers, ids, votes, store, [], queues=tr.Local())
    assert "tr-never-saved" not in tr.load_sent("local")["items"] and not fourth["not_saved"]
    sent = tr.load_sent("local")
    assert set(tr.Local().items(store, sent["queue_ids"][0])) == set(sent["items"])
    no, yes = [t for t, v in sent["items"].items() if v["id"] == ids[0]][0], [t for t, v in sent["items"].items() if v["id"] == ids[1]][0]
    trace = mlflow.get_trace(no)
    assert trace.info.tags["lesson_id"] == ids[0].split(":")[0]
    assert not [a for a in trace.info.assessments if a.source.source_type == AssessmentSourceType.LLM_JUDGE]  # votes stay hidden

    human(no, tr.SERVE, False, "It says the opposite of the lesson.")
    human(no, tr.PROBLEMS, ["A fact is wrong or not in the lesson"])
    human(no, tr.SURE, "Sure")
    human(no, tr.BETTER, "A plainer answer.", expectation=True)
    human(yes, tr.SERVE, True)
    reviews = tr.read(list(sent["items"]), tr.Local().questions(store))
    assert reviews[no].problems == ["A fact is wrong or not in the lesson"] and reviews[no].better == "A plainer answer."
    assert reviews[yes].serve and not reviews[no].serve

    counts = tr.apply(answers, sent, reviews)
    lid, _, key = ids[0].partition(":")
    assert counts["failed"] == 1 and counts["served"] == 1
    assert answers[lid][key]["status"] == "failed" and "opposite of the lesson" in answers[lid][key]["judge"]["notes"]
    assert "A plainer answer." in answers[lid][key]["judge"]["notes"]  # the next draft starts from it
    assert tr.log_votes(sent, reviews) == 1 and tr.log_votes(sent, reviews) == 0  # once only
    judged = [a for a in mlflow.get_trace(no).info.assessments if a.source.source_type == AssessmentSourceType.LLM_JUDGE]
    assert judged[0].metadata["prompt"] == "tutor_judge/1" and judged[0].metadata["rule.plain"] == "False"


def test_a_full_queue_spills_into_a_numbered_one(store):
    class Small(tr.Local):
        cap = 1  # Databricks holds 150 a queue; one here, to see the spill

    data, answers, ids = two_answers()
    result = tr.send(data, answers, ids, {}, store, [], queues=Small())
    assert result["queues"] == [tr.QUEUE, f"{tr.QUEUE}-2"] and result["added"] == 2
    again = tr.send(data, answers, ids, {}, store, [], queues=Small())
    assert (again["added"], again["already"]) == (0, 2)
    assert tr.bare("trace:/cat.schema.prefix/abc123") == "abc123" and tr.bare("tr-abc") == "tr-abc"


def test_a_yes_serves_a_failed_answer_and_a_changed_answer_is_left_alone():
    k, j = tp.answer_print("Answer k."), tp.answer_print("Answer j.")
    answers = {"a": {"k": {"a": "Answer k.", "status": "failed", "fingerprint": "f1"},
                     "j": {"a": "Answer j.", "status": "passed", "fingerprint": "new"}}}
    sent = {"items": {"t1": {"id": "a:k", "fingerprint": "f1", "votes": {}}, "t2": {"id": "a:j", "fingerprint": "old", "votes": {}}}}
    counts = tr.apply(answers, sent, {"t1": tr.Review(serve=True, answer=k), "t2": tr.Review(serve=False, answer=j)})
    assert counts == {"served": 0, "rescued": 1, "failed": 0, "changed_since": 1}
    assert answers["a"]["k"]["status"] == "passed" and answers["a"]["j"]["status"] == "passed"


def test_a_verdict_never_lands_on_text_the_person_did_not_read():
    """The lesson and the question are the same, but the answer was redrafted after it was sent: the verdict on the
    old text is not applied to the new one, whichever way it went."""
    old, new = tp.answer_print("The old draft."), tp.answer_print("A redraft.")
    for serve, status in ((True, "failed"), (False, "passed")):
        answers = {"a": {"k": {"a": "A redraft.", "status": status, "fingerprint": "f1"}}}
        sent = {"items": {"t1": {"id": "a:k", "fingerprint": "f1", "answer": old, "votes": {}}}}
        counts = tr.apply(answers, sent, {"t1": tr.Review(serve=serve, answer=old)})
        assert counts["changed_since"] == 1 and answers["a"]["k"]["status"] == status and "review" not in answers["a"]["k"]
    # The text the trace showed is what counts, even when the record of what was sent says otherwise.
    answers = {"a": {"k": {"a": "A redraft.", "status": "failed", "fingerprint": "f1"}}}
    sent = {"items": {"t1": {"id": "a:k", "fingerprint": "f1", "answer": new, "votes": {}}}}
    assert tr.apply(answers, sent, {"t1": tr.Review(serve=True, answer=old)})["changed_since"] == 1
    # And with no print at all (an item from before prints, whose trace showed nothing readable), nothing is applied.
    sent = {"items": {"t1": {"id": "a:k", "fingerprint": "f1", "votes": {}}}}
    assert tr.apply(answers, sent, {"t1": tr.Review(serve=True)})["changed_since"] == 1
    assert answers["a"]["k"]["status"] == "failed"


def test_a_redraft_goes_back_to_the_queue_and_the_old_no_stays_with_the_old_text(store):
    data, answers, ids = two_answers()
    tr.send(data, answers, ids[:1], {}, store, [], queues=tr.Local())
    sent = tr.load_sent("local")
    (first,) = sent["items"]
    human(first, tr.SERVE, False, "Too long.")
    lid, _, key = ids[0].partition(":")
    reviews = tr.read(list(sent["items"]), tr.Local().questions(store))
    assert reviews[first].answer == tp.answer_print(answers[lid][key]["a"])  # the text the trace showed
    assert tr.apply(answers, sent, reviews)["failed"] == 1

    answers[lid][key].update(a="A shorter redraft, written after the person said no.", status="passed")  # drill tutor prepare
    again = tr.send(data, answers, ids[:1], {}, store, [], queues=tr.Local())
    assert again["added"] == 1  # the new text is its own trace for a person to read
    sent = tr.load_sent("local")
    assert len(sent["items"]) == 2
    reviews = tr.read(list(sent["items"]), tr.Local().questions(store))
    assert list(reviews) == [first]  # nobody has read the redraft yet
    counts = tr.apply(answers, sent, reviews)
    assert counts["changed_since"] == 1 and counts["failed"] == 0
    assert answers[lid][key]["status"] == "passed"  # the old "no" was about the old text


def test_an_answer_sent_before_prints_is_not_sent_twice(store):
    data, answers, ids = two_answers()
    tr.send(data, answers, ids, {}, store, [], queues=tr.Local())
    sent = tr.load_sent("local")
    for tid, item in sent["items"].items():  # as written by the code before this change: no print in the record,
        del item["answer"]                     # and no "answer" tag on the trace
        mlflow.delete_trace_tag(tid, "answer")
    tr.save_sent("local", sent)
    again = tr.send(data, answers, ids, {}, store, [], queues=tr.Local())
    assert (again["added"], again["already"]) == (0, 2)
    assert all(v["answer"] for v in tr.load_sent("local")["items"].values())  # filled in from each trace's own text


def test_only_a_persons_answer_counts_as_the_review(store):
    """The judges' votes go on the same trace under the same question (log_votes): they must never count as the
    review, and a judge's later vote must never overrule the person."""
    data, answers, ids = two_answers()
    tr.send(data, answers, ids, {}, store, [], queues=tr.Local())
    sent = tr.load_sent("local")
    person, judged_only = list(sent["items"])
    judge = AssessmentSource(AssessmentSourceType.LLM_JUDGE, "gpt-5.4")
    human(person, tr.SERVE, False, "Wrong.")
    mlflow.log_feedback(trace_id=person, name=tr.SERVE, value=True, source=judge)  # later than the person's "no"
    mlflow.log_feedback(trace_id=judged_only, name=tr.SERVE, value=True, source=judge)
    reviews = tr.read(list(sent["items"]), tr.Local().questions(store))
    assert set(reviews) == {person} and reviews[person].serve is False


def test_compare_counts_verdicts_and_each_rule_against_the_person():
    sent = {"items": {
        "t1": {"votes": {"g": {"pass": False, "checks": {"plain": False, "correct": True}}}},
        "t2": {"votes": {"g": {"pass": False, "checks": {"plain": False, "correct": False}}}},
    }}
    reviews = {"t1": tr.Review(serve=True), "t2": tr.Review(serve=False, problems=["A fact is wrong or not in the lesson"])}
    s = tr.compare(sent, reviews)["g"]
    assert (s["answers"], s["agreed"]) == (2, 1)
    assert s["rules"]["plain"] == {"flagged": 2, "person_agreed": 0}  # flagged twice, the person never agreed
    assert s["rules"]["correct"] == {"flagged": 1, "person_agreed": 1}


def test_as_pass_reads_buttons_and_booleans():
    assert tr.as_pass(True) and tr.as_pass(tr.YES) and tr.as_pass("yes")
    assert tr.as_pass(tr.NO) is False and tr.as_pass("fail") is False
    assert tr.as_pass("maybe") is None


def test_prepare_links_the_registered_prompts_and_refuses_a_mismatch(store):
    prompts = tpe.register_prompts(mlflow, 1)
    with mlflow.start_run() as run:
        uris = tpe.link_prompts(mlflow, prompts, 1)
    assert set(uris) == {f"prompts:/{v.name}/{v.version}" for v in prompts.values()}
    assert "tutor_prepared_judge" in mlflow.get_run(run.info.run_id).data.tags["mlflow.linkedPrompts"]
    stale = {"tutor_prepared_judge": mlflow.genai.register_prompt(name=prompts["tutor_prepared_judge"].name, template="old text")}
    with pytest.raises(RuntimeError, match="differs"):
        tpe.link_prompts(mlflow, stale, 1)


def test_the_text_a_trace_shows_is_read_from_json_text_too():
    """Unity Catalog hands span outputs back as JSON text, not a dict."""
    from types import SimpleNamespace as NS

    out = {"choices": [{"index": 0, "message": {"role": "assistant", "content": "The answer."}}]}
    as_dict, as_text = (NS(data=NS(spans=[NS(outputs=o)])) for o in (out, __import__("json").dumps(out)))
    assert tr.shown(as_dict) == tr.shown(as_text) == "The answer."
    assert tr.shown(NS(data=NS(spans=[NS(outputs="not json")]))) == "" and tr.shown(None) == ""


def test_an_old_item_whose_text_cannot_be_read_is_neither_lost_nor_sent_twice(store, monkeypatch):
    data, answers, ids = two_answers()
    tr.send(data, answers, ids, {}, store, [], queues=tr.Local())
    sent = tr.load_sent("local")
    for tid, item in sent["items"].items():  # sent before prints, as above
        del item["answer"]
        mlflow.delete_trace_tag(tid, "answer")
    tr.save_sent("local", sent)

    def down(trace_id):
        raise RuntimeError("the network is down")

    monkeypatch.setattr(mlflow, "get_trace", down)
    again = tr.send(data, answers, ids, {}, store, [], queues=tr.Local())  # no crash, and nothing queued twice
    assert (again["added"], again["already"]) == (0, 2)
    assert not any(v.get("answer") for v in tr.load_sent("local")["items"].values())  # left for the next send
    monkeypatch.undo()
    tr.send(data, answers, ids, {}, store, [], queues=tr.Local())
    assert all(v["answer"] for v in tr.load_sent("local")["items"].values())


def test_a_redraft_is_sent_without_being_named_and_without_the_old_votes(store):
    data, answers, ids = two_answers()
    votes = {ids[0]: {"g": {"pass": False, "notes": "too long", "checks": {}}}}
    tr.send(data, answers, ids[:1], votes, store, [], queues=tr.Local())
    lid, _, key = ids[0].partition(":")
    answers[lid][key]["a"] = "A redraft the judges never read."
    again = tr.send(data, answers, [], votes, store, [], queues=tr.Local())  # nothing named, the old votes file
    assert again["added"] == 1
    items = list(tr.load_sent("local")["items"].values())
    redraft = next(v for v in items if v["answer"] == tp.answer_print("A redraft the judges never read."))
    assert redraft["votes"] == {}, "the judges voted on the old text, not this one"


def test_an_answer_of_only_spaces_counts_as_no_answer(store):
    data, answers, ids = two_answers()
    lid, _, key = ids[0].partition(":")
    answers[lid][key]["a"] = "   "
    result = tr.send(data, answers, ids[:1], {}, store, [], queues=tr.Local())
    assert result["skipped"] == ids[:1] and result["added"] == 0
