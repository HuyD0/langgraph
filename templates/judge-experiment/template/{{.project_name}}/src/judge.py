# Databricks notebook source
# MAGIC %md
# MAGIC # 3 · Judge every answer
# MAGIC
# MAGIC **What this does:** grades every answer in `eval_set_checked` (the real ones and the planted mistakes) with the
# MAGIC judge model, plus code checks for the rules a computer can count, as one MLflow evaluation run.
# MAGIC
# MAGIC **What the judge sees:** only each answer's context, question and answer, never its id, group or whether it was
# MAGIC planted. **What it's asked:** the instructions in `src/judge_instructions.md`, registered as a prompt.
# MAGIC
# MAGIC **What the run records, so any result can be traced back and repeated:**
# MAGIC - **the prompt:** `<catalog>.<schema>.judge_instructions`, a new version only when the text changes; the run links
# MAGIC   the exact version, and the `in_use` alias points at it;
# MAGIC - **the dataset:** `<catalog>.<schema>.judge_eval_dataset`, linked to the run with its digest;
# MAGIC - **one trace per answer**, stored in Unity Catalog: a `judged_answer` span with the context, question and answer,
# MAGIC   tags for its id, group and planted kind, and each judge's verdict and reason;
# MAGIC - **who made each label:** a planted mistake's label is recorded as CODE, a person's as HUMAN;
# MAGIC - **tokens and cost** for every judge call, added up on the run;
# MAGIC - **every setting** as a parameter, with tags and a description. Step 4 adds its numbers to this same run.
# MAGIC
# MAGIC **Why one judge by default:** in the experiment this template comes from, a jury of three did worse than its best
# MAGIC member twice. Judges that share blind spots can't vote them away, and two weak judges outvote a strong one. Set
# MAGIC `jury_models` to measure that on your own answers before you pay for it.

# COMMAND ----------

# MAGIC %pip install -q "mlflow[databricks]>=3.17,<4" markdown

# COMMAND ----------

try:
    dbutils.library.restartPython()  # noqa: F821 - defined in a Databricks notebook
except NameError:
    pass  # on a laptop: nothing to restart

# COMMAND ----------

import json

import mlflow
import pandas as pd
from mlflow.entities import AssessmentSource, SpanType
from mlflow.genai.judges import make_judge
from mlflow.genai.scorers import scorer

import judge_core as core
import tables

a = tables.args(("--judge-model", {"required": True}), ("--jury-models", {"default": ""}),
                ("--max-words", {"type": int, "default": 200}), ("--target", {"default": "local"}))
experiment = tables.experiment(a)
rows = tables.rows(tables.read(a, "eval_set_checked"))
models = [a.judge_model] + [m.strip() for m in a.jury_models.split(",") if m.strip()]
names = ["judge"] + [f"jury_{i}" for i in range(1, len(models))]
prefix = f"{a.catalog}.{a.schema}." if a.catalog else ""  # Unity Catalog names on Databricks, plain names on a laptop
TOKENS_IN, TOKENS_OUT, COST = "mlflow.assessment.judgeInputTokens", "mlflow.assessment.judgeOutputTokens", "mlflow.assessment.judgeCost"


def judge_prompt():
    """The judge's instructions as a registered prompt: a new version only when the text changed; `in_use` points at it."""
    name = prefix + "judge_instructions"
    text = (tables.root(a) / "src" / "judge_instructions.md").read_text(encoding="utf-8")
    try:
        found = mlflow.MlflowClient().search_prompt_versions(name)
        same = [v for v in getattr(found, "prompt_versions", found) or [] if v.template == text]
    except Exception:  # noqa: BLE001 - not registered yet
        same = []
    version = same[0] if same else mlflow.genai.register_prompt(
        name=name, template=text, commit_message="judge instructions from src/judge_instructions.md",
        tags={"source": "src/judge_instructions.md", "project": a.project})
    mlflow.genai.set_prompt_alias(name, "in_use", int(version.version))
    return name, int(version.version)


def eval_dataset():
    """The eval set as a registered evaluation dataset, brought up to date with this run's rows."""
    from mlflow.genai.datasets import create_dataset, get_dataset

    name = prefix + "judge_eval_dataset"
    try:
        ds = get_dataset(name=name)
    except Exception:  # noqa: BLE001 - first run
        # A Unity Catalog dataset takes no MLflow tags (Unity Catalog manages its own), so tags only on a laptop.
        ds = create_dataset(name=name, experiment_id=experiment.experiment_id,
                            **({} if prefix else {"tags": {"project": a.project}}))
    ds.merge_records([{"inputs": {"context": r["context"], "question": r["question"]}, "outputs": {"answer": r["answer"]},
                       **({"expectations": {"expected_pass": r["expected_pass"]}} if r["expected_pass"] is not None else {}),
                       "tags": {"row_id": r["id"], "group": str(r.get("group") or ""), "planted": r.get("planted") or "no"}}
                      for r in rows])
    return ds


def label_source(r: dict) -> AssessmentSource:
    if r.get("planted"):
        return AssessmentSource(source_type="CODE", source_id=f"judge_core.plant.{r['planted']}")
    return AssessmentSource(source_type="HUMAN", source_id="eval_set.expected_pass")


@scorer(name="code_checks")
def code_checks(outputs) -> bool:
    """The rules a computer can check (word limit, leaning on an earlier chat): no judge needed for these."""
    answer = outputs.get("answer", "") if isinstance(outputs, dict) else str(outputs)
    return core.code_checks(answer, a.max_words)["pass"]


def as_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.lower() in ("yes", "no", "true", "false"):
        return v.lower() in ("yes", "true")
    return None


# COMMAND ----------

prompt_name, prompt_version = judge_prompt()
dataset = eval_dataset()
n_planted = {k: sum(1 for r in rows if r.get("planted") == k) for k in core.PLANT_KINDS}
model_short = a.judge_model.split(":/")[-1]
run_name = (f"judge {model_short}" + (f" + jury of {len(models)}" if len(models) > 1 else "")
            + f" · prompt v{prompt_version} · {len(rows)} answers ({sum(n_planted.values())} planted) · {a.target}")
with mlflow.start_run(run_name=run_name) as run:
    mlflow.set_tags({"kind": "judge_experiment", "project": a.project, "target": a.target,
                     "catalog": a.catalog or "local", "schema": a.schema or "local", "judge_model": a.judge_model,
                     "jury": "yes" if len(models) > 1 else "no", "dataset": dataset.name, "prompt": f"{prompt_name}/{prompt_version}"})
    mlflow.set_tag("mlflow.note.content", "\n\n".join([
        "**Question:** how well does the judge grade these answers: does it catch the known-bad ones and keep the "
        "known-good ones?" + (" And does a jury beat its best member?" if len(models) > 1 else ""),
        f"**What ran:** {len(rows)} answers from `{dataset.name}` ({len(rows) - sum(n_planted.values())} real, "
        f"{sum(n_planted.values())} planted with one rule broken each), judged by {', '.join(models)} with prompt "
        f"`{prompt_name}` version {prompt_version}, plus code checks (word limit {a.max_words}, no leaning on an earlier "
        "chat).",
        "**How it's measured:** the report step adds catch and keep rates with Wilson 95% ranges, per planted kind, and "
        "with a jury its comparison with the best member (McNemar), to this run. Labels: planted answers are bad by "
        "construction (source CODE), others carry a person's verdict (source HUMAN) or none.",
        f"**Reproduce:** `databricks bundle run` on target `{a.target}`, or src/judge.py with the same arguments.",
    ]))
    mlflow.log_params({"judge_model": a.judge_model, "jury_models": ",".join(models[1:]) or "none", "judges": len(models),
                       "judge_prompt": f"prompts:/{prompt_name}/{prompt_version}", "dataset": dataset.name,
                       "dataset_digest": dataset.digest, "answers": len(rows), "real_answers": len(rows) - sum(n_planted.values()),
                       "labelled_good": sum(1 for r in rows if r["expected_pass"] is True),
                       "labelled_bad_real": sum(1 for r in rows if r["expected_pass"] is False and not r.get("planted")),
                       **{f"planted_{k}": v for k, v in n_planted.items()}, "max_words": a.max_words,
                       "catalog": a.catalog or "local", "schema": a.schema or "local", "target": a.target,
                       "mlflow_version": mlflow.__version__})
    prompt = mlflow.genai.load_prompt(f"prompts:/{prompt_name}/{prompt_version}")  # loading it here links it to the run
    judges = {n: make_judge(name=n, instructions=prompt.template, feedback_value_type=bool, model=m) for n, m in zip(names, models)}

    # One trace per answer, made here so its span has a name and its labels the right source. The judge sees only the
    # span's inputs (context and question) and output (the answer): never the id, group or planted kind.
    trace_of = {}
    for r in rows:
        with mlflow.start_span(name="judged_answer", span_type=SpanType.CHAIN) as span:
            span.set_inputs({"context": r["context"], "question": r["question"]})
            span.set_outputs({"answer": r["answer"]})  # an object: Databricks' evaluation reads outputs as JSON
            span.set_attributes({"row_id": r["id"], "group": str(r.get("group") or ""), "planted": r.get("planted") or "no"})
            mlflow.update_current_trace(tags={"row_id": r["id"], "group": str(r.get("group") or ""),
                                              "planted": r.get("planted") or "no", "dataset": dataset.name})
            trace_of[r["id"]] = span.trace_id
    mlflow.flush_trace_async_logging()
    for r in rows:
        if r["expected_pass"] is not None:
            mlflow.log_expectation(trace_id=trace_of[r["id"]], name="expected_pass", value=r["expected_pass"], source=label_source(r))
    mlflow.flush_trace_async_logging()

    def named(trace_ids):
        """The traces to evaluate, carrying the registered dataset's name and digest, so the run's dataset is
        `judge_eval_dataset` and not an unnamed table MLflow would otherwise build from the traces."""
        data = pd.DataFrame({"trace": [mlflow.get_trace(t) for t in trace_ids]})
        attach = getattr(dataset, "_attach_identity", None)  # MLflow's own step for a table built from a dataset
        data = attach(data) if attach else data
        if not data.attrs:  # an MLflow without it: link the dataset directly instead
            mlflow.log_input(dataset, context="evaluation")
        return data

    # evaluate() can come back without some answers, or without every vote on one (a trace that failed to save, for
    # example), so each answer counts only with all its votes; the rest are tried again, and the run stops if any never
    # come back.
    columns = ["code_checks", *judges]
    frames, todo = [], list(trace_of.values())
    for attempt in range(3):
        part = mlflow.genai.evaluate(data=named(todo), scorers=[code_checks, *judges.values()]).result_df
        cols = [f"{c}/value" if f"{c}/value" in part.columns else c for c in columns]
        complete = part[part[cols].notna().all(axis=1)] if all(c in part.columns for c in cols) else part.iloc[0:0]
        frames.append(complete)
        done = set(complete["trace_id"])
        todo = [t for t in todo if t not in done]
        if not todo:
            break
        print(f"{len(todo)} answers came back missing or without every vote: trying them again ({attempt + 1} of 2).")
    mlflow.log_metric("answers_missing", len(todo))
    if todo:
        raise SystemExit(f"{len(todo)} answers never came back with every vote: {todo[:10]}")
    df = pd.concat(frames, ignore_index=True).drop_duplicates("trace_id", keep="last")

    # Token use and cost per judge, from what MLflow records on each verdict.
    spend = {n: {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0} for n in judges}
    for assessments in df["assessments"]:
        for x in assessments or []:
            d = x if isinstance(x, dict) else x.to_dictionary()
            name = d.get("assessment_name") or d.get("name")
            meta = d.get("metadata") or {}
            if name in spend:
                spend[name]["input_tokens"] += int(float(meta.get(TOKENS_IN, 0) or 0))
                spend[name]["output_tokens"] += int(float(meta.get(TOKENS_OUT, 0) or 0))
                spend[name]["cost_usd"] += float(meta.get(COST, 0) or 0)
    mlflow.log_metrics({f"{n}_{k}": v for n, s in spend.items() for k, v in s.items()}
                       | {"cost_usd": round(sum(s["cost_usd"] for s in spend.values()), 4)})

# COMMAND ----------

row_of = {t: i for i, t in trace_of.items()}
value = lambda c: df[f"{c}/value" if f"{c}/value" in df.columns else c].map(as_bool)  # noqa: E731
votes = pd.DataFrame({"id": df["trace_id"].map(row_of), "trace_id": df["trace_id"], "code_checks": value("code_checks"),
                      **{n: value(n) for n in judges}})
by_id = {r["id"]: r for r in rows}
votes["group"] = votes["id"].map(lambda i: by_id[i].get("group"))
votes["planted"] = votes["id"].map(lambda i: by_id[i].get("planted") or "")
votes["expected_pass"] = votes["id"].map(lambda i: by_id[i]["expected_pass"])
votes["run_id"] = run.info.run_id
votes["judge_models"] = json.dumps(dict(zip(judges, models)))
tables.write(a, "judge_votes", votes)
total = sum(s["cost_usd"] for s in spend.values())
run_link = tables.link(f"/ml/experiments/{experiment.experiment_id}/runs/{run.info.run_id}")
tables.say(f"### Judged {len(votes)} answers for ${total:.2f}\n\n"
           f"- **Run:** [{run_name}]({run_link})\n"
           f"- **Prompt:** `{prompt_name}` version {prompt_version} (alias `in_use`)\n"
           f"- **Dataset:** `{dataset.name}`, digest `{dataset.digest}`\n"
           f"- **Votes:** on each answer's trace, and in `{tables.where(a, 'judge_votes')}`\n\n"
           "Tokens and cost per judge, from what MLflow records on each verdict:")
tables.show(pd.DataFrame([{"judge": n, "model": m, "input tokens": spend[n]["input_tokens"], "output tokens": spend[n]["output_tokens"],
                           "cost (US$)": round(spend[n]["cost_usd"], 4)} for n, m in zip(judges, models)]))
