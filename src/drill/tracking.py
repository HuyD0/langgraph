"""MLflow: tracing what the tutor did, and tracking how you are improving.

Two separate things, often confused:

**Tracing** answers "what happened inside that session?" - every node, every model
call, every prompt and response, as a tree you can open in the MLflow UI. One call
to ``mlflow.langchain.autolog()`` gets this for the whole LangGraph app.

**Run tracking** answers "am I getting better?" - one MLflow run per drill session,
with params (which problem, which topic) and metrics (attempts, hints, solved,
seconds). Over weeks this becomes the chart that tells you which patterns you still
fumble, which is exactly what you want to know before an interview.

Everything degrades gracefully: with no tracking server reachable, practice still
works and you simply get no traces.
"""

from __future__ import annotations

import contextlib
from typing import Any, Iterator

from drill.config import DrillSettings
from drill.problems import Problem
from drill.state import DrillState

_AUTOLOG_ENABLED = False


def setup_tracing(settings: DrillSettings | None = None) -> bool:
    """Turn on MLflow tracing for LangGraph. Returns True if it took effect.

    ``mlflow.langchain.autolog()`` is the only instrumentation this app needs -
    it captures LangGraph node execution and model calls on its own. There is
    deliberately no ``@mlflow.trace`` on the nodes: adding one would produce a
    duplicate span for every node autolog already records.
    """
    global _AUTOLOG_ENABLED
    settings = settings or DrillSettings.from_env()

    try:
        import mlflow

        if settings.mlflow_tracking_uri:
            mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.mlflow_experiment)
        mlflow.langchain.autolog()
        _AUTOLOG_ENABLED = True
        return True
    except Exception:
        _AUTOLOG_ENABLED = False
        return False


@contextlib.contextmanager
def drill_run(problem: Problem, settings: DrillSettings, thread_id: str) -> Iterator[Any]:
    """One MLflow run per practice session.

    Yields the active run, or ``None`` when MLflow is unavailable - so the caller
    writes the same code either way and never needs a tracking server to practise.
    """
    try:
        import mlflow
    except Exception:
        yield None
        return

    try:
        with mlflow.start_run(run_name=f"{problem.id}") as run:
            mlflow.log_params(
                {
                    "problem_id": problem.id,
                    "topic": problem.topic,
                    "difficulty": problem.difficulty,
                    "pattern": problem.pattern,
                    "max_attempts": settings.max_attempts,
                }
            )
            mlflow.set_tags({"thread_id": thread_id, "app": "interview-drill"})
            yield run
    except Exception:
        # A tracking failure must never cost you a practice session.
        yield None


def log_session_metrics(state: DrillState) -> None:
    """Record the outcome of a finished session as MLflow metrics."""
    try:
        import mlflow

        if mlflow.active_run() is None:
            return

        result = state.get("result") or {}
        duration = state.get("finished_at", 0) - state.get("started_at", 0)
        mlflow.log_metrics(
            {
                "solved": float(bool(result.get("passed"))),
                "attempts": float(state.get("attempts", 0)),
                "hints_used": float(len(state.get("hints", []))),
                "cases_passed": float(result.get("passed_count", 0)),
                "cases_total": float(result.get("total", 0)),
                "duration_s": float(max(duration, 0.0)),
            }
        )
    except Exception:
        pass


def tag_trace(thread_id: str, problem_id: str) -> None:
    """Stamp the current trace so you can filter traces by session and problem.

    Lets you run, for example::

        mlflow.search_traces(filter_string="metadata.`mlflow.trace.session` = '<id>'")
    """
    try:
        import mlflow

        mlflow.update_current_trace(
            metadata={"mlflow.trace.session": thread_id, "problem_id": problem_id}
        )
    except Exception:
        pass
