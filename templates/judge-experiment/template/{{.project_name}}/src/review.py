"""A person's review, in MLflow: the answers the judge failed go to a review queue, and the verdicts come back as labels.

The report step puts every real answer the judge failed (or the jury split on) into a review queue in the experiment
(MLflow, Evaluation, Reviews), with one question: would you show this answer to a user? A reviewer's answer is saved on
the answer's trace as HUMAN feedback. The next run's check step reads those verdicts back into eval_set's
expected_pass, so the judge is measured against people.

Review queues are a Beta feature: a workspace admin turns on "MLflow Review Queues" in Manage previews. Without it, or
on a laptop, these functions say why and carry on, so the job never fails over the review queue.
"""

from __future__ import annotations

QUESTION = "Would you show this answer to a user?"
INSTRUCTION = ("On the left: the context (the only source of truth) and the user's question, then the answer under them. "
               "Say yes only if every fact in the answer is in the context, it answers the question that was asked, and it "
               "makes sense on its own. If no, use the rationale to say what is wrong.")


def _rq():
    import mlflow.genai.databricks.review_queues as rq

    return rq


def _all(page_fn, *args, **kw):
    items, token = [], None
    while True:
        page = page_fn(*args, page_token=token, **kw)
        items += list(page)
        token = getattr(page, "token", None)
        if not token:
            return items


YES, NO = "Yes, show it", "No, don't show it"


def question_id(experiment_id: str) -> str:
    """The review question's id, made the first time it's needed, with labelled buttons (without labels the page shows
    "1" and "2")."""
    rq = _rq()
    answer = rq.InputPassFail(positive_label=YES, negative_label=NO)
    for q in _all(rq.list_review_questions, experiment_id):
        if q.title == QUESTION:
            if getattr(q.input, "positive_label", None) != YES:
                rq.update_review_question(experiment_id, q.question_id, input=answer, instruction=INSTRUCTION)
            return q.question_id
    q = rq.create_review_question(experiment_id, title=QUESTION, type="FEEDBACK", input=answer,
                                  instruction=INSTRUCTION, enable_comment=True)
    return q.question_id


def publish(experiment_id: str, queue_name: str, trace_ids: list[str], reviewers: list[str]) -> str:
    """Put ``trace_ids`` in the queue ``queue_name`` (made if missing) and add the reviewers. Returns what happened."""
    if not trace_ids:
        return "Nothing to review: no queue changes."
    import mlflow

    if not mlflow.get_tracking_uri().startswith("databricks"):
        return "Review queues run in a Databricks workspace; here, the review_queue table lists the answers."
    try:
        rq = _rq()
        qid = question_id(experiment_id)
        queue = next((q for q in _all(rq.list_review_queues, experiment_id) if q.display_name == queue_name), None)
        if queue is None:
            queue = rq.create_review_queue(experiment_id, queue_name, queue_type="CUSTOM", question_ids=[qid])
        have = {i.trace_id for i in _all(rq.list_review_queue_items, experiment_id, queue.queue_id)}
        new = [t for t in trace_ids if t and t not in have]
        if new:
            rq.add_review_queue_items(experiment_id, queue.queue_id, trace_ids=new)
        members = {m.user for m in _all(rq.list_review_queue_members, experiment_id, queue.queue_id)}
        for user in reviewers:
            if user and user not in members:
                rq.add_review_queue_member(experiment_id, queue.queue_id, user)
        return (f"Review queue '{queue_name}': {len(new)} answers added ({len(have)} already there), "
                f"reviewers {', '.join(reviewers) or 'unchanged'}. Open the experiment, then Evaluation, then Reviews.")
    except Exception as exc:  # noqa: BLE001 - a missing preview or a laptop run must not fail the job
        return (f"No review queue made ({type(exc).__name__}: {str(exc)[:200]}). Review queues are a Beta feature: a "
                "workspace admin turns on 'MLflow Review Queues' in Manage previews. The review_queue table still lists the answers.")


def as_pass(value) -> bool | None:
    """A reviewer's answer as True (pass), False (fail) or None (can't read it)."""
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("pass", "passed", "true", "1") or text.startswith("yes"):
        return True
    if text in ("fail", "failed", "false", "0") or text.startswith("no"):
        return False
    return None


def verdicts(experiment_id: str, trace_ids: list[str]) -> dict[str, bool]:
    """Each trace's latest HUMAN answer to the review question, as pass or fail. Empty when there is none, or no access."""
    import mlflow
    from mlflow.entities import AssessmentSourceType

    try:
        names = {QUESTION.lower(), question_id(experiment_id).lower()}
    except Exception:  # noqa: BLE001 - no review queues here: nothing to read back
        return {}
    out: dict[str, bool] = {}
    for tid in trace_ids:
        try:
            trace = mlflow.get_trace(tid)
        except Exception:  # noqa: BLE001 - a trace that's gone has no verdict
            continue
        if trace is None:  # gone, for example with an experiment that was deleted
            continue
        answers = [a for a in (trace.info.assessments or []) if a.source and a.source.source_type == AssessmentSourceType.HUMAN
                   and (a.name or "").lower() in names and getattr(a, "feedback", None) is not None]
        if answers:
            latest = max(answers, key=lambda a: a.last_update_time_ms or a.create_time_ms or 0)
            v = as_pass(latest.feedback.value)
            if v is not None:
                out[tid] = v
    return out
