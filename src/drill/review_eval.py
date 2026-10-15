"""Score the use case review prompt on cards with planted gaps: ``drill review eval``.

The MLflow calls here (``@scorer``, ``Feedback``, ``mlflow.genai.evaluate``) are built step by step
in notebooks/m11_vet_a_use_case.ipynb, section 5.

Each case is the HR assistant's card with something planted: a blank owner, no test data, no
feedback loop, a success line with no number, or answers nobody checks. A good review flags
each gap as an Unknown or a question, names every pillar, gives the unchecked case a high risk,
and never decides for the reader. The same code checks run on every review the page asks for
(drill.review_checks); this runs them on cases with known answers, so a prompt change can be
tested before it is published. With MLflow reachable the run is logged with
mlflow.genai.evaluate, next to the page's traces; without it the scores are printed.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

from drill.content import review
from drill.review_checks import flags_gap, review_checks

FULL = {key: example for key, _label, example in review.CARD_FIELDS}


def _card(**changes: str) -> dict:
    return {**FULL, **changes}


CASES: list[dict[str, Any]] = [
    {"name": "complete card", "card": _card(), "gaps": [], "high_risk": False},
    {"name": "no owner", "card": _card(owner=""), "gaps": [["owner", ["owner", "who decides", "decide", "accountab"]]], "high_risk": False},
    {"name": "no test data", "card": _card(data=""), "gaps": [["data", ["data", "test", "example", "eval"]]], "high_risk": False},
    {"name": "no feedback loop", "card": _card(feedback=""), "gaps": [["feedback", ["feedback", "improve", "learn", "monitor"]]], "high_risk": False},
    {"name": "vague success", "card": _card(success="happier employees"),
     "gaps": [["success", ["success", "measure", "metric", "target", "number"]]], "high_risk": False},
    {"name": "nobody checks", "card": _card(action="the answer goes straight to the employee",
                                            wrong_answer="nobody checks; a wrong answer could give wrong pay or leave advice"),
     "gaps": [], "high_risk": True},
    {"name": "two gaps", "card": _card(owner="", data=""),
     "gaps": [["owner", ["owner", "who decides", "decide", "accountab"]], ["data", ["data", "test", "example", "eval"]]], "high_risk": False},
]


def score(text: str, case: dict) -> dict:
    """The scores for one review of one case. Every score is True when the review did well."""
    checks = review_checks(text, review.blank_fields(case["card"]))
    flagged = [field for field, words in case["gaps"] if flags_gap(text, words)]
    result = {
        "all_pillars": not checks["missing_pillar"],
        "gaps_flagged": len(flagged) == len(case["gaps"]),
        "no_verdict": not checks["decides_for_them"],
    }
    if case["high_risk"]:
        result["high_risk_named"] = "high" in text.lower()
    result["must_pass"] = result["gaps_flagged"] and result["no_verdict"]
    return result


# The judge is optional and not part of must-pass: its verdicts need checking against
# people's labels before its numbers are trusted (see the lesson "Checking your LLM judge").
JUDGE_VERSION = "grounded-v3"  # v1 flagged fair readings; v2 invented claims itself, so v3 must quote and code checks the quote
JUDGE = """You check a drafted review of an AI use case against the card it was written from.
List only invented facts: specifics the card does not contain, such as a number, a tool, a control,
a person or a process that the card never mentions, stated as true.
Do not list: restatements or fair readings of a card line, questions, Unknowns, risk ratings,
or general advice ("consider adding a fallback").
Copy each one word for word from the review, so it can be found in it.
Reply with JSON only: {{"unsupported": ["exact words from the review", ...]}}

The card:
{card}

The review:
{review}"""


def _router():
    from drill.server.router import ModelRouter

    return ModelRouter.from_env()


def _ask(router, prompt: str, tier: str, context: dict) -> str:
    return asyncio.run(router.ask(prompt, tier, context=context)).text


def judge_grounded(router, card: dict, text: str, tier: str) -> tuple[bool, list[str]]:
    card_text = "\n".join(f"- {k}: {(card.get(k) or '').strip() or 'not written'}" for k, _l, _e in review.CARD_FIELDS)
    reply = asyncio.run(router.ask_json(JUDGE.format(card=card_text, review=text), tier, context={"feature": "use_case_review_judge"}))
    claimed = [str(x) for x in (reply or {}).get("unsupported", [])] if isinstance(reply, dict) else []
    # A judge can invent too: keep only claims that really are in the review, word for word.
    flat = lambda t: re.sub(r"[\s*_`\"']+", " ", t).strip().lower()
    review_flat = flat(text)
    # and only statements: questions and fragments are not claims, whatever the judge says.
    # Statements about what the card lacks ("no mention of timeouts") are observations, not inventions.
    question = re.compile(r"^(what|how|who|which|when|where|why|is|are|does|do|can|will|should)\b", re.I)
    absence = re.compile(r"no mention|not mention|does not|doesn't|not specified|not stated|only mentions|unknown|unclear", re.I)
    unsupported = [c for c in claimed
                   if "?" not in c and len(c.split()) >= 5 and not question.match(c.strip()) and not absence.search(c)
                   and flat(c) in review_flat]
    return not unsupported, unsupported


def run(tier: str = "default", judge: bool = False, use_mlflow: bool = True) -> list[dict]:
    """Ask the model for a review of each case, score it, and return one row per case."""
    router = _router()
    if not router.order(tier):
        raise RuntimeError("No model is available: start Ollama or set a hosted model in .env.")

    def predict(name: str, card: dict) -> str:
        return _ask(router, review.review_prompt(card), tier, {
            "feature": "use_case_review", "door": "eval", "lesson_id": "well_architected",
            "prompt_version": review.REVIEW_VERSION, "blank_fields": ",".join(review.blank_fields(card)), "question": name})

    rows: list[dict] = []
    if use_mlflow and _mlflow_ready():
        rows = _run_with_mlflow(predict, router, tier, judge)
    else:
        for case in CASES:
            text = predict(case["name"], case["card"])
            row = {"case": case["name"], **score(text, case)}
            if judge:
                row["grounded"], row["unsupported"] = judge_grounded(router, case["card"], text, tier)
            rows.append(row)
    return rows


def _mlflow_ready() -> bool:
    from drill.server.observe import default_observer

    observer = default_observer()
    return bool(observer and observer.ready())


def records() -> list[dict]:
    """The cases as evaluation-dataset records: the card in, what a good review must do as expectations."""
    return [{"inputs": {"name": c["name"], "card": c["card"]},
             "expectations": {"gaps": [field for field, _ in c["gaps"]], "high_risk": c["high_risk"]}} for c in CASES]


def eval_dataset(mlflow, experiment_id: str):
    """The review cases as an MLflow evaluation dataset (``review_cases``), created or brought up to date.

    Runs that use it show it as their input, so you can tell which cases a score was measured on.
    ``None`` when the tracking store keeps no datasets; the run then uses the cases directly.
    """
    from drill import mlflow_names

    name = mlflow_names.dataset_name("review_cases")
    try:
        try:
            dataset = mlflow.genai.get_dataset(name=name)
        except Exception:  # noqa: BLE001 - not there yet
            from drill.config import is_databricks_uri

            # Unity Catalog manages a dataset's tags itself, so MLflow tags are only passed elsewhere.
            tags = None if is_databricks_uri(mlflow.get_tracking_uri()) else {"source": "src/drill/review_eval.py", "cases": str(len(CASES))}
            dataset = mlflow.genai.create_dataset(name=name, experiment_id=experiment_id, tags=tags)
        dataset.merge_records(records())
        return dataset
    except Exception as exc:  # noqa: BLE001
        print(f"(no evaluation dataset: {str(exc).splitlines()[0][:120]}; using the cases directly)")
        return None


def _run_with_mlflow(predict, router, tier: str, judge: bool) -> list[dict]:
    import mlflow
    from mlflow.entities import Feedback
    from mlflow.genai.scorers import scorer

    by_name = {c["name"]: c for c in CASES}

    def _case(inputs: dict) -> dict:
        return by_name[inputs["name"]]

    @scorer
    def all_pillars(inputs, outputs) -> bool:
        return score(outputs, _case(inputs))["all_pillars"]

    @scorer
    def gaps_flagged(inputs, outputs) -> Feedback:
        case = _case(inputs)
        missed = [f for f, words in case["gaps"] if not flags_gap(outputs, words)]
        return Feedback(value=not missed, rationale=("missed: " + ", ".join(missed)) if missed else "every planted gap flagged")

    @scorer
    def no_verdict(inputs, outputs) -> bool:
        return score(outputs, _case(inputs))["no_verdict"]

    @scorer
    def high_risk_named(inputs, outputs) -> bool:
        case = _case(inputs)
        return score(outputs, case).get("high_risk_named", True)

    scorers = [all_pillars, gaps_flagged, no_verdict, high_risk_named]
    if judge:
        @scorer
        def grounded(inputs, outputs) -> Feedback:
            ok, unsupported = judge_grounded(router, _case(inputs)["card"], outputs, tier)
            return Feedback(value=ok, rationale="; ".join(unsupported) or "every claim is backed by the card")

        scorers.append(grounded)

    answers: dict[str, str] = {}

    def predict_and_keep(name: str, card: dict) -> str:
        answers[name] = text = predict(name, card)
        return text

    # One case at a time: a single local model cannot answer several reviews at once.
    os.environ["MLFLOW_GENAI_EVAL_MAX_WORKERS"] = "1"
    from drill import mlflow_names
    from drill.review_ops import _model_for
    from drill.server.observe import app_version

    from drill.server.observe import default_observer

    dataset = eval_dataset(mlflow, getattr(default_observer(), "experiment_id", None))
    data = dataset if dataset is not None else [{"inputs": r["inputs"]} for r in records()]
    version = app_version()
    active = mlflow.set_active_model(name=f"daily-drill-{version}")  # the eval's metrics show on this version
    with mlflow.start_run(run_name=mlflow_names.run_name("review-eval", review.REVIEW_VERSION)):
        prompt = None
        try:  # loading the registered prompt inside the run links it to the run
            prompt = mlflow.genai.load_prompt(f"prompts:/{mlflow_names.prompt_name('review')}@production")
        except Exception:  # noqa: BLE001 - not registered here: the run uses the code's prompt
            prompt = None
        mlflow.set_tags({**mlflow_names.context_tags(version), "kind": "review_eval",
                         "mlflow.note.content": f"The use case review prompt ({review.REVIEW_VERSION}) on {len(CASES)} planted "
                                                "cards: does it name every pillar, flag each planted gap, flag unchecked harm, "
                                                "and leave the decision to the learner?"})
        mlflow.log_params({"prompt_version": review.REVIEW_VERSION, "tier": tier, "model": _model_for(router, tier),
                           "prompt": f"{prompt.name}/{prompt.version}" if prompt else mlflow_names.prompt_name("review"),
                           "dataset": mlflow_names.dataset_name("review_cases") if dataset is not None else "inline",
                           "judge": JUDGE_VERSION if judge else "off", "cases": len(CASES)})
        result = mlflow.genai.evaluate(data=data, predict_fn=predict_and_keep, scorers=scorers,
                                       model_id=getattr(active, "model_id", None))
    # The printed table is scored here from the same answers, so it never depends on MLflow's table layout.
    rows = []
    for case in CASES:
        text = answers.get(case["name"], "")
        row = {"case": case["name"], **(score(text, case) if text else {"must_pass": False, "error": "no answer"})}
        rows.append(row)
    print(json.dumps({"mlflow_run": result.run_id, "metrics": result.metrics}, default=str))
    return rows
