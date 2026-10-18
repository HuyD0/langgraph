"""The tutor's feedback, read back from MLflow: how often its answers worked, and the eval cases they make.

    uv run drill tutor feedback                    # this computer's traces from the last 7 days
    uv run drill tutor feedback --days 30 --dataset
    uv run drill tutor feedback --target work      # the deployed app's traces (Databricks)

Every answer in "Ask about this lesson" is an ``ask_lesson`` trace with the page's request id
(``client_request_id``). The page attaches to it:

- ``resolved``: Got it (true) or Still stuck (false), from the learner (HUMAN);
- ``saved``, ``asked_again``, ``gave_up``, ``next_right``: what the page saw them do next (CODE);

and a Still stuck re-explanation is tagged ``retry_of`` with the request id of the answer that
didn't help. :func:`summarise` turns that into the numbers to watch, and :func:`cases` into
evaluation-dataset records (``tutor_cases``): the question, the answer that didn't help, and, when
the simpler one got a Got it, that answer as the better one. A new prompt version should do at
least as well as the better answers on these questions before it is promoted.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

SIGNALS = ("saved", "asked_again", "gave_up", "next_right")


@dataclass
class Answer:
    """One tutor answer, as its trace records it."""

    request: str
    lesson_id: str = ""
    step: str = ""
    question: str = ""
    answer: str = ""
    retry_of: str = ""
    chip: bool = False
    feedback: dict[str, Any] = field(default_factory=dict)  # name -> value (the latest one)

    @property
    def resolved(self) -> bool | None:
        value = self.feedback.get("resolved")
        return None if value is None else bool(value)


def _text(value: Any) -> str:
    """A span's input or output as text, from a dict, a JSON string (Unity Catalog) or plain text."""
    import json

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return value
    if isinstance(value, dict):
        for key in ("answer", "question", "output", "text", "content"):
            if isinstance(value.get(key), str):
                return value[key]
    return "" if value is None else str(value)


def answer_from(trace) -> Answer | None:
    """Read one ``ask_lesson`` trace; ``None`` for anything else (or a trace without a request id)."""
    info, tags = trace.info, trace.info.tags or {}
    if tags.get("feature") != "ask_lesson" or not info.client_request_id:
        return None
    root = next((s for s in trace.data.spans if s.parent_id is None), None)
    inputs = root.inputs if root is not None else {}
    feedback = {}
    for a in sorted(info.assessments or [], key=lambda a: getattr(a, "create_time_ms", 0) or 0):
        if a.name == "resolved" or a.name in SIGNALS:
            feedback[a.name] = a.value
    return Answer(
        request=info.client_request_id, lesson_id=tags.get("lesson_id", ""), step=tags.get("step", ""),
        question=_text(inputs if not isinstance(inputs, dict) else inputs.get("question", "")),
        answer=_text(root.outputs if root is not None else ""), retry_of=tags.get("retry_of", ""),
        chip=str(tags.get("chip", "")).lower() == "true", feedback=feedback,
    )


def read(experiment_id: str, days: float) -> list[Answer]:
    """The tutor's answers from the last ``days`` in one experiment, oldest first."""
    import mlflow

    since = int((time.time() - days * 86400) * 1000)
    traces = mlflow.search_traces(
        locations=[experiment_id], return_type="list", max_results=5000,
        filter_string=f"tags.feature = 'ask_lesson' AND trace.timestamp_ms > {since}",
    )
    answers = []
    for t in traces:
        full = t if t.data and t.data.spans else mlflow.get_trace(t.info.trace_id)
        if full is not None and (a := answer_from(full)) is not None:
            answers.append(a)
    return answers


def summarise(answers: list[Answer]) -> dict:
    """The numbers to watch. ``first_answer_resolved``: of the first answers that got Got it or Still
    stuck, the share that got Got it (re-explanations are left out: they are second chances)."""
    first = [a for a in answers if not a.retry_of]
    rated = [a for a in first if a.resolved is not None]
    by_request = {a.request: a for a in answers}
    retries = [a for a in answers if a.retry_of in by_request]
    out: dict[str, Any] = {
        "answers": len(answers),
        "first_answers": len(first),
        "rated": len(rated),
        "first_answer_resolved": round(sum(a.resolved for a in rated) / len(rated), 3) if rated else None,
        "still_stuck": sum(a.resolved is False for a in first),
        "retry_resolved": round(sum(bool(a.resolved) for a in retries) / len(retries), 3) if retries else None,
    }
    for name in SIGNALS:
        seen = [a.feedback[name] for a in answers if name in a.feedback]
        out[name] = {"answers": len(seen), "true": sum(bool(v) for v in seen)}
    stuck: dict[str, int] = {}
    for a in first:
        if a.resolved is False or a.feedback.get("asked_again") or a.feedback.get("gave_up"):
            stuck[a.lesson_id] = stuck.get(a.lesson_id, 0) + 1
    out["lessons_most_stuck"] = sorted(stuck.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return out


def cases(answers: list[Answer]) -> list[dict]:
    """Evaluation records from answers that didn't help: Still stuck, or asked again. The re-explanation
    that got Got it, if there was one, is kept as the better answer."""
    retries: dict[str, list[Answer]] = {}
    for a in answers:
        if a.retry_of:
            retries.setdefault(a.retry_of, []).append(a)
    records = []
    for a in answers:
        if a.retry_of or not (a.resolved is False or a.feedback.get("asked_again")):
            continue
        better = next((r for r in retries.get(a.request, []) if r.resolved), None)
        expectations = {"failed_answer": a.answer}
        if better is not None:
            expectations["better_answer"] = better.answer
        records.append({
            "inputs": {"question": a.question, "lesson_id": a.lesson_id, "step": a.step},
            "expectations": expectations,
        })
    return records


def save_cases(mlflow, experiment_id: str, records: list[dict]):
    """Add the records to the ``tutor_cases`` evaluation dataset (a Unity Catalog table on Databricks).
    ``None`` when the tracking store keeps no datasets."""
    from drill import mlflow_names
    from drill.config import is_databricks_uri

    name = mlflow_names.dataset_name("tutor_cases")
    try:
        try:
            dataset = mlflow.genai.get_dataset(name=name)
        except Exception:  # noqa: BLE001 - not there yet
            tags = None if is_databricks_uri(mlflow.get_tracking_uri()) else {"source": "src/drill/tutor_feedback.py"}
            dataset = mlflow.genai.create_dataset(name=name, experiment_id=experiment_id, tags=tags)
        dataset.merge_records(records)
        return dataset
    except Exception as exc:  # noqa: BLE001
        print(f"(no evaluation dataset: {str(exc).splitlines()[0][:120]})")
        return None
