"""Step 4: the numbers, and the review queue for a person.

For each judge (and the jury, when there is one): the share of known-bad answers it catches and of known-good answers it
keeps, each with a 95% range, per planted kind too. With a jury: whether it beats its best member (McNemar) and whether
its split votes really point at mistakes. Then every real answer a judge failed, or the jury split on, goes to the
review_queue table for a person: their verdicts become the labels the judge is checked against next time.
"""

import json

import mlflow
import pandas as pd

import judge_core as core
import tables

a = tables.args(("--experiment", {"required": True}))
mlflow.set_experiment(a.experiment)
votes = tables.read(a, "judge_votes")
judges = [c for c in votes.columns if c == "judge" or c.startswith("jury_")]
truth = [None if v is None else bool(v) for v in votes["expected_pass"]]


def read(col):
    return [None if v is None else bool(v) for v in votes[col]]


report = {"answers": len(votes), "known_bad": sum(t is False for t in truth), "known_good": sum(t is True for t in truth),
          "judges": {}, "by_kind": {}}
for name in judges + ["code_checks"]:
    report["judges"][name] = core.scores(read(name), truth)
    report["by_kind"][name] = {kind: core.wilson(sum(v is False for v, k in zip(read(name), votes["planted"]) if k == kind),
                                                 sum(v is not None for v, k in zip(read(name), votes["planted"]) if k == kind))
                               for kind in sorted(set(votes["planted"]) - {"", None})}
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
else:
    split = [False] * len(votes)

# A person reads what the judge failed (and the jury's splits): real answers only, planted ones are known bad already.
failed = [i for i in range(len(votes)) if not votes["planted"][i] and (read("judge")[i] is False or split[i])]
queue = votes.iloc[failed][["id", "group", "trace_id"]].assign(
    reason=["jury split" if split[i] else "judge failed it" for i in failed], person_verdict=None)
tables.write(a, "review_queue", queue)

flat = {}
for name, s in report["judges"].items():
    flat.update({f"{name}_catch": s["catch"]["rate"], f"{name}_balanced": s["balanced"],
                 **({f"{name}_keep": s["keep"]["rate"]} if s["keep"]["n"] else {})})
with mlflow.start_run(run_name=f"report · {len(judges)} judge(s) · {report['answers']} answers"):
    mlflow.log_metrics({k: v for k, v in flat.items() if v is not None})
    mlflow.log_dict(report, "report.json")
tables.write(a, "judge_report", pd.DataFrame([{"report": json.dumps(report)}]))
print(json.dumps(report, indent=1))
if not report["known_good"]:
    print("No answer is labelled good (expected_pass = true), so the keep rate can't be measured: a judge that fails "
          "everything would look perfect. Label some real answers, starting with the review queue.")
print(f"{len(queue)} answers are waiting for a person in review_queue.")
