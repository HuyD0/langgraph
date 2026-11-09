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
    answers = {"a": {"k": {"status": "failed", "fingerprint": "f1"}, "j": {"status": "passed", "fingerprint": "new"}}}
    sent = {"items": {"t1": {"id": "a:k", "fingerprint": "f1", "votes": {}}, "t2": {"id": "a:j", "fingerprint": "old", "votes": {}}}}
    counts = tr.apply(answers, sent, {"t1": tr.Review(serve=True), "t2": tr.Review(serve=False)})
    assert counts == {"served": 0, "rescued": 1, "failed": 0, "changed_since": 1}
    assert answers["a"]["k"]["status"] == "passed" and answers["a"]["j"]["status"] == "passed"


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
