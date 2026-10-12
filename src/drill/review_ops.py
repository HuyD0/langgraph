"""Keeping the use case review honest over time (each MLflow call here is an exercise in notebooks/m11_vet_a_use_case.ipynb): ``drill review label``, ``calibrate`` and ``register``.

- **label**: show recent reviews from MLflow traces, one at a time, and record whether each one
  invented a fact. Your answer goes on the trace as HUMAN feedback named ``grounded``.
- **calibrate**: run the groundedness judge on every review you labelled and compare: how often
  it agrees with you, and Cohen's kappa (agreement beyond chance, from the Evals lesson). A judge
  is only worth trusting once its kappa is high on your labels.
- **register**: put the review and challenge prompts in MLflow's prompt registry, one version per
  change, with the ``production`` alias on the one the page uses.
"""

from __future__ import annotations

import os

from typing import Any, Callable

from drill.content import review

from drill import mlflow_names


# -- the maths: agreement and Cohen's kappa ---------------------------------


def agreement(human: list[bool], judge: list[bool]) -> dict:
    """Agreement, Cohen's kappa and the four counts, for paired yes/no labels."""
    pairs = list(zip(human, judge))
    n = len(pairs)
    both_yes = sum(1 for h, j in pairs if h and j)
    both_no = sum(1 for h, j in pairs if not h and not j)
    judge_only = sum(1 for h, j in pairs if j and not h)   # judge says grounded, you found an invention
    human_only = sum(1 for h, j in pairs if h and not j)   # judge flags an invention you did not see
    if not n:
        return {"n": 0, "agreement": None, "kappa": None, "both_grounded": 0, "both_invented": 0, "judge_missed": 0, "judge_false_alarm": 0}
    observed = (both_yes + both_no) / n
    p_h, p_j = sum(human) / n, sum(judge) / n
    expected = p_h * p_j + (1 - p_h) * (1 - p_j)
    # When every label is the same, agreement by chance is total and kappa cannot be worked out.
    kappa = None if expected == 1 else round((observed - expected) / (1 - expected), 3)
    return {"n": n, "agreement": round(observed, 3), "kappa": kappa, "both_grounded": both_yes,
            "both_invented": both_no, "judge_missed": judge_only, "judge_false_alarm": human_only}


# -- reading reviews back from MLflow ---------------------------------------


def _mlflow():
    from drill.server.observe import default_observer

    observer = default_observer()
    if not (observer and observer.ready()):
        raise RuntimeError("MLflow is not reachable. Start it, or check MLFLOW_TRACKING_URI.")
    import mlflow

    return mlflow


def _reviewer(mlflow) -> str:
    """Who is labelling: your Databricks user name there, ``DRILL_OWNER`` (or ``local``) on your Mac."""
    from drill.config import databricks_user, is_databricks_uri

    uri = mlflow.get_tracking_uri()
    if is_databricks_uri(uri):
        try:
            return databricks_user(uri)
        except Exception:  # noqa: BLE001
            pass
    return os.getenv("DRILL_OWNER", "").strip() or "local"


def _review_of(trace) -> tuple[str, str] | None:
    """(prompt, review) from a review trace's root span, or None if it has no answer."""
    for span in trace.data.spans:
        if span.parent_id is None:
            prompt = (span.inputs or {}).get("question") if isinstance(span.inputs, dict) else None
            answer = (span.outputs or {}).get("answer") if isinstance(span.outputs, dict) else None
            if prompt and answer:
                return prompt, answer
    return None


def _assessment(trace, name: str, source_type: str | None = None):
    for a in trace.info.assessments or []:
        if a.name == name and (source_type is None or a.source.source_type == source_type):
            return a
    return None


def review_traces(limit: int = 50) -> list:
    mlflow = _mlflow()
    found = mlflow.search_traces(filter_string="tags.feature = 'use_case_review'", max_results=limit,
                                 order_by=["timestamp_ms DESC"], return_type="list")
    return [mlflow.get_trace(t.info.trace_id) for t in found]


# -- label -------------------------------------------------------------------


def label(n: int, ask: Callable[[str, str, dict], tuple[bool | None, str]]) -> int:
    """Show up to n unlabelled reviews; ``ask(review, card_text, card)`` returns (grounded or None to skip, note)."""
    import mlflow
    from mlflow.entities import AssessmentSource

    done = 0
    reviewer = _reviewer(mlflow)
    for trace in review_traces(limit=200):
        if done >= n:
            break
        if _assessment(trace, "grounded", "HUMAN"):
            continue
        got = _review_of(trace)
        if not got:
            continue
        prompt, answer = got
        card = review.parse_card(prompt)
        verdict, note = ask(answer, review.card_lines(card), card)
        if verdict is None:
            continue
        mlflow.log_feedback(trace_id=trace.info.trace_id, name="grounded", value=verdict, rationale=note or None,
                            source=AssessmentSource(source_type="HUMAN", source_id=reviewer))
        done += 1
    return done


# -- calibrate ---------------------------------------------------------------


def calibrate(tier: str = "default", log_run: bool = True) -> dict:
    """Run the judge on every review you labelled and measure how well it agrees with you."""
    import mlflow
    from mlflow.entities import AssessmentSource

    from drill.review_eval import JUDGE_VERSION, _router, judge_grounded

    router = _router()
    human, judge, rows = [], [], []
    for trace in review_traces(limit=500):
        mine = _assessment(trace, "grounded", "HUMAN")
        got = _review_of(trace)
        if not mine or not got:
            continue
        prompt, answer = got
        ok, unsupported = judge_grounded(router, review.parse_card(prompt), answer, tier)
        mlflow.log_feedback(trace_id=trace.info.trace_id, name="grounded_judge", value=ok, rationale="; ".join(unsupported) or None,
                            source=AssessmentSource(source_type="LLM_JUDGE", source_id=JUDGE_VERSION))
        human.append(bool(mine.value))
        judge.append(ok)
        rows.append({"trace": trace.info.trace_id, "you": bool(mine.value), "judge": ok, "flagged": unsupported[:3]})
    result = {"judge_version": JUDGE_VERSION, **agreement(human, judge), "rows": rows}
    if log_run and result["n"]:
        from drill.server.observe import app_version

        with mlflow.start_run(run_name=mlflow_names.run_name("judge-calibration", JUDGE_VERSION)):
            mlflow.set_tags({**mlflow_names.context_tags(app_version()), "kind": "judge_calibration"})
            mlflow.log_params({"judge_version": JUDGE_VERSION, "tier": tier, "labelled": result["n"],
                               "judge_model": _model_for(router, tier)})
            mlflow.log_metrics({k: float(result[k]) for k in ("agreement", "kappa", "judge_missed", "judge_false_alarm") if result[k] is not None})
    return result


# -- register ----------------------------------------------------------------


def _register(mlflow: Any, name: str, template: str, version_tag: str) -> dict:
    latest = None
    try:
        latest = mlflow.genai.load_prompt(f"prompts:/{name}@latest", link_to_model=False)
    except Exception:
        latest = None
    if latest is not None and latest.template == template:
        version = latest.version
        changed = False
    else:
        pv = mlflow.genai.register_prompt(name=name, template=template, commit_message=version_tag,
                                          tags={"drill_version": version_tag, "source": "src/drill/content/review.py"})
        version, changed = pv.version, True
    mlflow.genai.set_prompt_alias(name, "production", int(version))
    return {"name": name, "version": int(version), "drill_version": version_tag, "registered_new": changed,
            "uri": f"prompts:/{name}/{version}"}


def register() -> list[dict]:
    """Register the review and challenge prompts (a new version only when the text changed).

    On Databricks the registry is Unity Catalog, so the names are ``<DRILL_PROMPT_SCHEMA>.use_case_review``
    and ``.use_case_challenge``; locally they are the short names.
    """
    mlflow = _mlflow()
    if mlflow_names.needs_prompt_schema(mlflow.get_tracking_uri()):
        raise RuntimeError("On Databricks prompts live in Unity Catalog: set DRILL_PROMPT_SCHEMA=<catalog>.<schema> in .env.")
    return [
        _register(mlflow, mlflow_names.prompt_name("review"), review.review_template(), review.REVIEW_VERSION),
        _register(mlflow, mlflow_names.prompt_name("challenge"), review.challenge_template(), review.CHALLENGE_VERSION),
    ]


def _model_for(router, tier: str) -> str:
    """The model a tier's first route uses, for run parameters."""
    try:
        routes = router.order(tier)
        return routes[0].model if routes else "none"
    except Exception:  # noqa: BLE001
        return "unknown"
