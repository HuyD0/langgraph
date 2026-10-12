"""Answer key for milestone 11: vet a use case with MLflow."""

import mlflow
from mlflow.entities import AssessmentSource, Feedback, SpanType
from mlflow.genai.scorers import scorer
from sklearn.metrics import cohen_kappa_score

from drill.content import review
from drill.review_checks import flags_gap, review_checks

EVAL_DATA: list = []  # defined in the notebook


@mlflow.trace(name="use_case_review", span_type=SpanType.CHAIN)
def traced_review(card, model):
    mlflow.update_current_trace(tags={"feature": "use_case_review", "prompt_version": review.REVIEW_VERSION})
    return model(review.review_prompt(card))


def log_code_checks(trace_id, text, blank):
    for name, value in review_checks(text, blank).items():
        if isinstance(value, bool):
            mlflow.log_feedback(trace_id=trace_id, name=name, value=value,
                                source=AssessmentSource(source_type="CODE", source_id="review_checks"))


def log_label(trace_id, grounded, note=""):
    mlflow.log_feedback(trace_id=trace_id, name="grounded", value=grounded, rationale=note or None,
                        source=AssessmentSource(source_type="HUMAN", source_id="you"))


def read_labels(name="grounded", source_type="HUMAN"):
    labels = {}
    for trace in mlflow.search_traces(filter_string="tags.feature = 'use_case_review'", return_type="list"):
        for a in trace.info.assessments:
            if a.name == name and a.source.source_type == source_type:
                labels[trace.info.trace_id] = a.value
    return labels


@scorer
def gaps_flagged(inputs, outputs, expectations):
    missed = [gap for gap in expectations["gaps"] if not flags_gap(outputs, [gap])]
    if missed:
        return Feedback(value=False, rationale="missed: " + ", ".join(missed))
    return Feedback(value=True, rationale="every planted gap flagged")


def run_eval(model):
    result = mlflow.genai.evaluate(data=EVAL_DATA, predict_fn=lambda card: traced_review(card, model), scorers=[gaps_flagged])
    return result.metrics


def judge_agreement(human, judge):
    if len(set(human) | set(judge)) == 1:
        return None
    return round(cohen_kappa_score(human, judge), 2)


def register_review_prompt():
    version = mlflow.genai.register_prompt(name="drill-use-case-review", template=review.review_template(),
                                           commit_message=review.REVIEW_VERSION)
    mlflow.genai.set_prompt_alias("drill-use-case-review", "production", version.version)
    return version.version


def production_prompt(card):
    prompt = mlflow.genai.load_prompt("prompts:/drill-use-case-review@production")
    return prompt.format(card=review.card_lines(card))
