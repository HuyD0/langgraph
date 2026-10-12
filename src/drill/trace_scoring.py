"""Score the app's traces with MLflow scorers, in one batch, and register the scorers on the experiment.

    uv run drill traces score                 # the deployed app's traces from the last day
    uv run drill traces score --days 7 --target work

Every answer already carries its checks (a ``checks`` span and tags, from :func:`drill.server.observe.answer_checks`).
Here they become **scorers**: :func:`answer_rules` reads that span and returns one ``Feedback`` per rule,
named for what a passing answer does (``no_solution_leak``, ``plain_language``...), so ``True`` is a pass
and each metric is a pass rate. ``mlflow.genai.evaluate`` runs it over the traces, attaches the feedback
to each one and records an evaluation run with the pass rates: one SQL warehouse wake for the batch,
instead of one per answer.
"""

from __future__ import annotations

import time

from mlflow.genai.scorers import scorer


@scorer
def answer_rules(trace):
    """One pass/fail per rule the answer had to keep, from the trace's ``checks`` span. True is a pass."""
    from mlflow.entities import AssessmentSource, Feedback

    passes = {
        "solution_leak": "no_solution_leak", "big_o": "plain_language", "over_word_limit": "within_word_limit",
        "missing_pillar": "covers_all_pillars", "no_unknowns_for_blanks": "flags_blank_fields",
        "decides_for_them": "leaves_decision_to_learner",
    }
    import json

    checks = next((s.outputs for s in trace.data.spans if s.name == "checks"), None)
    if isinstance(checks, str):  # traces read back from Unity Catalog give span outputs as JSON text
        try:
            checks = json.loads(checks)
        except ValueError:
            checks = None
    if not isinstance(checks, dict):
        return []
    source = AssessmentSource(source_type="CODE", source_id="drill.answer_rules")
    return [Feedback(name=passes[k], value=not bool(v), source=source) for k, v in checks.items() if k in passes]


SCORERS = [answer_rules]


def register(experiment_id: str) -> list[str]:
    """Register the scorers on an experiment, so they show on its Scorers tab. Registering runs nothing."""
    import mlflow

    names = []
    for s in SCORERS:
        try:  # replace any earlier registration, so the experiment always holds this code's version
            mlflow.genai.delete_scorer(name=s.name, experiment_id=experiment_id)
        except ImportError:
            raise
        except Exception:  # noqa: BLE001 - nothing registered yet
            pass
        s.register(name=s.name, experiment_id=experiment_id)
        names.append(s.name)
    return names


def score(experiment_id: str, days: float = 1.0, limit: int = 500) -> dict:
    """Run the scorers over the experiment's traces from the last ``days``, as one evaluation run."""
    import mlflow

    from drill import mlflow_names
    from drill.server.observe import app_version

    since = int((time.time() - days * 86400) * 1000)
    traces = mlflow.search_traces(locations=[experiment_id], filter_string=f"trace.timestamp_ms > {since}",
                                  max_results=limit)
    if traces is None or len(traces) == 0:
        return {"traces": 0, "run_id": None, "metrics": {}}
    mlflow.set_experiment(experiment_id=experiment_id)
    with mlflow.start_run(run_name=mlflow_names.run_name("trace-scoring", time.strftime("%Y-%m-%d"))) as run:
        mlflow.set_tags({**mlflow_names.context_tags(app_version()), "kind": "trace_scoring",
                         "mlflow.note.content": f"answer_rules over the app's traces from the last {days:g} day(s): "
                                                "each metric is the share of answers that kept that rule."})
        mlflow.log_params({"days": days, "traces": len(traces), "scorers": ",".join(s.name for s in SCORERS)})
        result = mlflow.genai.evaluate(data=traces, scorers=SCORERS)
    return {"traces": len(traces), "run_id": run.info.run_id, "metrics": result.metrics}
