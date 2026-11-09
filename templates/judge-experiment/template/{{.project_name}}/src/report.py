# Databricks notebook source
# MAGIC %md
# MAGIC # 4 · Report, and send answers to a person
# MAGIC
# MAGIC **What this does:** turns the votes from step 3 into numbers you can act on, adds them to the same MLflow run, and
# MAGIC puts the answers worth a person's time in a review queue.
# MAGIC
# MAGIC **How to read the numbers:**
# MAGIC - **Catch:** of the answers known to be bad, the share the judge failed. **Keep:** of the answers known to be good,
# MAGIC   the share it passed. A judge needs both: one that fails everything catches 100%.
# MAGIC - **Balanced:** the two averaged. Empty when no answer is labelled good, because then keep can't be measured.
# MAGIC - **The range** after each share is its 95% range (Wilson): with few answers it is wide, so don't read much into
# MAGIC   small differences.
# MAGIC - **By kind:** catches per kind of planted mistake. A kind near 0% is a blind spot: fix the judge's instructions,
# MAGIC   or move that rule into code.
# MAGIC - **Jury** (only when there is one): whether it is right where its best member is wrong more often than the
# MAGIC   reverse. Below p = 0.05, the difference is unlikely to be luck.
# MAGIC
# MAGIC **The review queue:** every real answer the judge failed (or a jury split on) goes to a queue in the experiment
# MAGIC (MLflow, Evaluation, Reviews). A reviewer answers one question per answer, and the next run reads their verdicts
# MAGIC back as labels.

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

import judge_core as core
import review
import tables

a = tables.args(("--reviewers", {"default": ""}))
experiment = tables.experiment(a)
votes = tables.read(a, "judge_votes")
judges = [c for c in votes.columns if c == "judge" or c.startswith("jury_")]
truth = [None if v is None else bool(v) for v in votes["expected_pass"]]
models = json.loads(votes["judge_models"].iloc[0])


def read(col):
    return [None if v is None else bool(v) for v in votes[col]]


def pct(s: dict) -> str:
    return f"{s['rate']:.0%} ({s['low']:.0%} to {s['high']:.0%}) of {s['n']}" if s["n"] else "not measured"


report = {"answers": len(votes), "known_bad": sum(t is False for t in truth), "known_good": sum(t is True for t in truth),
          "judges": {}, "by_kind": {}}
for name in judges + ["code_checks"]:
    report["judges"][name] = core.scores(read(name), truth)
    report["by_kind"][name] = {kind: core.wilson(sum(v is False for v, k in zip(read(name), votes["planted"]) if k == kind),
                                                 sum(v is not None for v, k in zip(read(name), votes["planted"]) if k == kind))
                               for kind in sorted(set(votes["planted"]) - {"", None})}
split = [False] * len(votes)
if len(judges) > 1:
    jury = [core.consensus([read(j)[i] for j in judges]) for i in range(len(votes))]
    verdict, split = [v for v, _ in jury], [s for _, s in jury]
    report["judges"]["jury"] = core.scores(verdict, truth)
    # The best member is right most often on bad and good answers alike; without good labels, only catches can rank them.
    best = max(judges, key=lambda j: report["judges"][j]["balanced"] if report["judges"][j]["balanced"] is not None
               else report["judges"][j]["catch"]["rate"])
    report["jury_vs_best"] = {"best": best, **core.compare(verdict, read(best), truth)}
    wrong = lambda rows: core.wilson(sum(verdict[i] != truth[i] for i in rows), len(rows))  # noqa: E731
    known = [i for i in range(len(votes)) if truth[i] is not None and verdict[i] is not None]
    report["jury_wrong_when_split"] = wrong([i for i in known if split[i]])
    report["jury_wrong_when_unanimous"] = wrong([i for i in known if not split[i]])

who = {**models, "code_checks": "rules in code", "jury": "majority of the judges"}
tables.say(f"### How each grader did\n\n{report['answers']} answers: **{report['known_bad']}** known bad, "
           f"**{report['known_good']}** known good.")
tables.show(pd.DataFrame([{"grader": n, "model": who.get(n, ""), "catch (bad answers failed)": pct(s["catch"]),
                           "keep (good answers passed)": pct(s["keep"]),
                           "balanced": "" if s["balanced"] is None else f"{s['balanced']:.0%}"}
                          for n, s in report["judges"].items()]))
tables.say("### Catches by kind of planted mistake\n\nA kind near 0% is a blind spot.")
tables.show(pd.DataFrame([{"kind": k, **{n: f"{report['by_kind'][n][k]['rate']:.0%}" for n in report["by_kind"]}}
                          for k in sorted({k for d in report["by_kind"].values() for k in d})]))
if len(judges) > 1:
    b = report["jury_vs_best"]
    tables.say(f"### Jury against its best member ({b['best']})\n\nOnly the jury right: **{b['only_first_right']}** · only "
               f"{b['best']} right: **{b['only_second_right']}** · p = {b['p_value']}. "
               + ("The difference is unlikely to be luck." if b["p_value"] < 0.05 else "The difference could be luck.")
               + f"\n\nThe jury was wrong on {pct(report['jury_wrong_when_split'])} split votes and "
               f"{pct(report['jury_wrong_when_unanimous'])} unanimous ones.")
if not report["known_good"]:
    tables.say("**No answer is labelled good**, so keep can't be measured: a judge that fails everything would look "
               "perfect. Label some real answers, starting with the review queue below.")

# COMMAND ----------

# A person reads what the judge failed (and the jury's splits): real answers only, planted ones are known bad already.
failed = [i for i in range(len(votes)) if not votes["planted"][i] and (read("judge")[i] is False or split[i])]
queue = votes.iloc[failed][["id", "group", "trace_id"]].assign(
    reason=["jury split" if split[i] else "judge failed it" for i in failed], person_verdict=None)
tables.write(a, "review_queue", queue)
reviewers = [r.strip() for r in a.reviewers.split(",") if r.strip()]
if not reviewers:
    try:
        from databricks.sdk import WorkspaceClient

        reviewers = [WorkspaceClient().current_user.me().user_name]
    except Exception:  # noqa: BLE001 - on a laptop there's no workspace user
        reviewers = []
published = review.publish(experiment.experiment_id, f"{a.schema} review", [t for t in queue["trace_id"] if t], reviewers)
tables.say(f"### Review queue\n\n**{len(queue)}** answers need a person. {published}\n\n"
           f"[Open the experiment]({tables.link('/ml/experiments/' + experiment.experiment_id)}) and choose **Reviews**.")
if len(queue):
    tables.show(queue[["id", "group", "reason"]])

# COMMAND ----------

# The numbers go on the judge step's own run, so one run holds the settings, the votes and the results.
flat = {}
for name, s in report["judges"].items():
    flat.update({f"{name}_catch": s["catch"]["rate"], f"{name}_balanced": s["balanced"],
                 **({f"{name}_keep": s["keep"]["rate"]} if s["keep"]["n"] else {})})
run_id = votes["run_id"].iloc[0]
with mlflow.start_run(run_id=run_id):
    mlflow.log_metrics({k: v for k, v in flat.items() if v is not None}
                       | {"review_queue_answers": len(queue), "known_bad": report["known_bad"], "known_good": report["known_good"]})
    mlflow.log_dict(report, "report.json")
    mlflow.set_tag("report", "complete")
tables.write(a, "judge_report", pd.DataFrame([{"report": json.dumps(report)}]))
tables.say(f"### Saved\n\nThe numbers are on [the evaluation run]({tables.link(f'/ml/experiments/{experiment.experiment_id}/runs/{run_id}')}) "
           f"(metrics, and `report.json`), and in `{tables.where(a, 'judge_report')}`.")
