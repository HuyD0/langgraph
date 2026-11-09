"""Step 3: code checks plus the judge (and any jury), as one MLflow evaluation run.

Every answer becomes a trace; each judge's verdict and the code checks' result land on it as feedback, so you can open
any answer in the MLflow UI and see every vote with its reason. The votes also go to the judge_votes table.

Why one strong judge by default: in the experiment this template comes from, a jury of three did worse than its best
member twice (local models and Claude models), because judges that share blind spots can't vote them away and two weak
judges outvote a strong one. Add --jury-models to measure that on your own answers before you pay for it.
"""

import json
from pathlib import Path

import mlflow
import pandas as pd
from mlflow.genai.judges import make_judge
from mlflow.genai.scorers import scorer

import judge_core as core
import tables

a = tables.args(("--judge-model", {"required": True}), ("--jury-models", {"default": ""}),
                ("--max-words", {"type": int, "default": 200}), ("--experiment", {"required": True}))
INSTRUCTIONS = (Path(__file__).with_name("judge_instructions.md")).read_text(encoding="utf-8")

mlflow.set_experiment(a.experiment)
rows = tables.rows(tables.read(a, "eval_set_checked"))
models = [a.judge_model] + [m.strip() for m in a.jury_models.split(",") if m.strip()]
judges = {("judge" if i == 0 else f"jury_{i}"): make_judge(name=("judge" if i == 0 else f"jury_{i}"), instructions=INSTRUCTIONS,
                                                           feedback_value_type=bool, model=m)
          for i, m in enumerate(models)}


@scorer(name="code_checks")
def code_checks(outputs) -> bool:
    """The rules a computer can check (word limit, leaning on an earlier chat): no judge needed for these."""
    return core.code_checks(outputs, a.max_words)["pass"]


data = [{"inputs": {"row_id": r["id"], "context": r["context"], "question": r["question"]}, "outputs": r["answer"],
         **({"expectations": {"expected_pass": r["expected_pass"]}} if r["expected_pass"] is not None else {})}
        for r in rows]
with mlflow.start_run(run_name=f"judge {a.judge_model.split(':/')[-1]}" + (f" + jury of {len(models)}" if len(models) > 1 else "")
                      + f" · {len(rows)} answers") as run:
    mlflow.log_params({"judge_model": a.judge_model, "jury_models": ",".join(models[1:]) or "none", "max_words": a.max_words,
                       "answers": len(rows), "planted": sum(1 for r in rows if r.get("planted"))})
    # evaluate() can leave a row out of its results without an error (a trace that failed to save, for example), so
    # every answer is checked to have come back, the missing ones are tried again, and the run stops if any stay missing.
    def row_id(r):
        return (r if isinstance(r, dict) else json.loads(r))["row_id"]

    def value_columns(part):
        return [c for name in ["code_checks", *judges] for c in (f"{name}/value", name) if c in part.columns][: len(judges) + 1]

    frames, todo = [], data
    for attempt in range(3):
        part = mlflow.genai.evaluate(data=todo, scorers=[code_checks, *judges.values()]).result_df
        cols = value_columns(part)
        complete = part[part[cols].notna().all(axis=1)] if len(cols) == len(judges) + 1 else part.iloc[0:0]
        frames.append(complete)  # an answer counts only when every judge's vote came back with it
        got = {row_id(r) for r in complete["request" if "request" in complete.columns else "inputs"]}
        todo = [d for d in todo if d["inputs"]["row_id"] not in got]
        if not todo:
            break
        print(f"{len(todo)} answers came back missing or without every vote: trying them again ({attempt + 1} of 2).")
    mlflow.log_metric("answers_missing", len(todo))
    if todo:
        raise SystemExit(f"{len(todo)} answers never came back with every vote: {[d['inputs']['row_id'] for d in todo][:10]}")

df = pd.concat(frames, ignore_index=True)


def column(name: str) -> str:
    """The result table's column for a scorer's value (MLflow names it '<scorer>/value' or '<scorer>')."""
    for c in (f"{name}/value", name):
        if c in df.columns:
            return c
    raise KeyError(f"no column for {name}: {list(df.columns)}")


def as_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.lower() in ("yes", "no", "true", "false"):
        return v.lower() in ("yes", "true")
    return None


ids = df["request" if "request" in df.columns else "inputs"].map(row_id)
votes = pd.DataFrame({"id": ids, "trace_id": df.get("trace_id"),
                      "code_checks": df[column("code_checks")].map(as_bool),
                      **{name: df[column(name)].map(as_bool) for name in judges}})
by_id = {r["id"]: r for r in rows}
votes["group"] = votes["id"].map(lambda i: by_id[i].get("group"))
votes["planted"] = votes["id"].map(lambda i: by_id[i].get("planted") or "")
votes["expected_pass"] = votes["id"].map(lambda i: by_id[i]["expected_pass"])
votes["run_id"] = run.info.run_id
votes["judge_models"] = json.dumps({name: m for name, m in zip(judges, models)})
tables.write(a, "judge_votes", votes)
print(f"Judged {len(votes)} answers with {len(models)} judge(s); votes in judge_votes and on each trace (run {run.info.run_id}).")
