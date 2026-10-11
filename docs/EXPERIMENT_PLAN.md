# Experiment plan

Fill this in **before** the first run, and save it with the results. Deciding the
metric and the winning rule after seeing the numbers is the easiest way to fool
yourself. Writing them down first is called pre-registration, and it makes a
result something you can defend.

The Daily Drill lessons behind each part are named in brackets. Notebook
milestone 8 walks through one complete experiment using this template, and
milestones 9a to 9d run a full RAG experiment through every lifecycle stage;
[END_TO_END.md](END_TO_END.md) shows how the stages fit together.

## The template

Copy this block into a `plan.yaml` in a folder for the experiment, for example
`experiments/2026-10-hints-model/plan.yaml`, and fill in every line.

```yaml
question:       # One sentence. "Does X improve Y on Z?"
change:         # The ONE thing that differs between the setups. Everything else stays fixed.
fixed:          # What you hold constant: prompt, temperature, judge, retrieval settings...
eval_set:       # Name and version, e.g. faq-v4. Never compare runs on different versions.
split:          # dev, test or holdout. Holdout only for a final decision.
groups:         # The groups you report separately, e.g. billing / shipping / refunds.
metric:         # The main metric, and how it is scored (rule, or judge + its kappa).
guardrails:     # Must-not-get-worse numbers: p95 latency, cost per request, refusals...
runs:           # Runs per example (3 or more for anything with randomness in it).
size_check:     # n examples -> margin about 100 / sqrt(n) points. Is it smaller than the change you expect?
test:           # How you compare: paired (McNemar) for pass/fail on the same examples.
decision_rule:  # What you will do for each outcome, decided now.
no_result:      # What "too close to call" means you will do.
```

## How to fill in each line

**question and change.** One question, one change. If you change the model *and*
the prompt, a better score cannot tell you which one helped. [Planning what to vary]

**eval_set and split.** Use a named, frozen version. Tune on **dev** as much as you
like; check **test** before a release; open **holdout** only for a final decision,
and replace it once you have changed things because of what it showed.
[Dev, test and holdout sets]

**groups.** Pick the kinds of example that behave differently and report each
one, with its count. For the headline number, weight the groups by their share
of real traffic. [Report each group, weighted by real traffic]

**metric and guardrails.** Start from the failure that hurts most: a made-up
answer, a missed fraud, a leaked solution. Pair the main metric with guardrails
so a quality gain cannot hide a cost or speed loss. If an LLM judge scores the
metric, check it against human labels first, on passes and failures separately,
and with Cohen's kappa. [Checking your LLM judge] [Agreement beyond chance]

For RAG, score retrieval and answers separately: recall@k and nDCG for the
ranking [Ranking quality: nDCG], and include questions your documents cannot
answer, tracking missed refusals and over-refusals [Knowing when not to answer].
For agents, run each task k times and report pass^k next to the success rate
[Reliable every time: pass^k], and score the tool calls and the path where you
know the right ones [Right tool, right arguments] [Did it take a sensible path?].
For a classifier with rare positives, report PR-AUC rather than ROC-AUC
[Quality across every threshold: PR-AUC], and check calibration before a
probability threshold drives a decision [Are the probabilities honest?].

**runs and size_check.** LLM output and judges vary between runs, so run each
example more than once. Then check the eval set can see the change you hope for:

| Examples | Margin, about |
|---|---|
| 25 | plus or minus 20 points |
| 100 | plus or minus 10 points |
| 400 | plus or minus 5 points |

If the change you expect is smaller than the margin, add examples before running.
[How many examples do you need?] Near 0% or 100%, like 49 out of 50 or 0 failures
in 30 tries, use a Wilson interval instead of the simple margin.
[Margins near 0% and 100%]

**test.** When both setups run on the same examples, compare them example by
example and count only the disagreements. Call a winner only if the gap between
the two counts is at least twice the square root of how many disagreements there were. That is McNemar's test in plain
words, and it is the standard for pass/fail results. For scores that are not
pass/fail, use a paired bootstrap or a permutation test.
[Comparing on the same examples]

The "worst run beats best run" rule from [Telling real gains from noise] is a
cautious fallback when you can't pair the examples: it never crowns a fake
winner, but it misses real ones.

**decision_rule and no_result.** Write what you will do for every outcome, for
example "switch to B if it wins clearly and p95 stays under 10 seconds; if it is
too close to call, keep A and grow the eval set to 100 cases". Then follow it.

## After the runs: reading what happened

The comparison says *whether* the change helped. These steps, done in this order
in the Evaluate stage, say *why*, and what to try next. Most of them were set up
earlier: oracle and ablation runs are extra variants planned in Design, repeat
runs are decided in Design, and the tags they rely on are added in Build and trace.

1. **Must-pass gate.** Any must-pass failure stops the release, whatever the average. [A must-pass set]
2. **Oracle headroom.** How much could a perfect version of the step you changed gain? [Oracle tests: find the bottleneck]
3. **Groups.** Did one group get worse while the average improved? [Report each group, weighted by real traffic]
4. **Flaky questions.** Questions that change between runs of the same version are noise; set them aside. [Comparing on the same examples]
5. **Paired test.** Count improvements and regressions on the remaining questions. [Comparing on the same examples]
6. **Read them.** Open both traces for each improvement and regression, find where they diverge, label the cause, count the causes. [Reading regressions and improvements]
7. **Component checks.** For example, what the reranker did on the same candidates, and how many misses were out of reach. [Did the reranker help?]
8. **Ablations.** Is each part worth its cost? [Ablations: what each part is worth]
9. **Guardrails.** Time and cost per request.
10. **Decide by the rule, then confirm once on the holdout.** [Testing many variants]

## Log the plan with the run

Save the plan next to the results, so anyone can see the rule came first:

```python
import mlflow
import yaml

with open("experiments/2026-10-hints-model/plan.yaml") as f:
    plan = yaml.safe_load(f)

with mlflow.start_run(run_name="hints-gemma-vs-qwen"):
    mlflow.log_dict(plan, "plan.json")
    mlflow.log_params({"eval_set": plan["eval_set"], "test": plan["test"], "runs": plan["runs"]})
    # ... run both setups, then log the results:
    mlflow.log_metrics({"a_only": a_only, "b_only": b_only})
```

## Building the eval set from labelled traces

A good eval set is mostly real traffic. With MLflow 3 the usual loop is:

1. **Collect feedback on traces.** End users leave a thumbs up or down, logged
   with `mlflow.log_feedback`, and subject-matter experts (SMEs) review traces
   in a **labeling session** in the Databricks Review App, using label schemas
   you define (`mlflow.genai.label_schemas`).
2. **Turn labelled traces into a versioned dataset.** Search the traces you
   want and add them to an evaluation dataset (`mlflow.genai.datasets`,
   `create_dataset` and `merge_records`), backed by a Unity Catalog table on
   Databricks.
3. **Evaluate every new version against it** with `mlflow.genai.evaluate`.
4. **Use the same SME labels to check your LLM judge**, or to align it
   (MemAlign, on Databricks).

This is sound, and it's the workflow MLflow is built for. The method in this
document still applies to it; these are the places it usually goes wrong:

- **Ask SMEs for the right answer, not only a grade.** A grade (a `feedback`
  label schema) says whether *that* response was good. It stops being useful
  once the app changes and gives a different response. What the eval set needs
  is what a good answer must contain: an `expectation` label schema, such as
  expected facts or guidelines, logged with `mlflow.log_expectation`. Collect
  both where you can.
- **Choose which traces get labelled on purpose.** If SMEs only see traces that
  got a thumbs down, or the first 200 of the week, the eval set over-represents
  some problems and misses others. Sample by group: kinds of question, users,
  difficulty, plus a random slice and the past failures. [Dev, test and
  holdout sets]
- **Write a rubric, and check that the SMEs agree.** Put the rubric in the label
  schema's instructions. Have two SMEs label an overlapping sample and compute
  Cohen's kappa. If experts disagree, the labels are not ground truth yet.
  [Agreement beyond chance]
- **Keep the judge's training labels apart from its test labels.** If the same
  SME labels are used to align a judge and then to measure how well it agrees
  with SMEs, the agreement is inflated. That is leakage. Hold some labelled
  traces back for checking the judge.
- **Split and freeze.** Keep each user's or conversation's traces in a single
  split, hold out a locked set, and version the dataset, so results stay
  comparable across releases.
- **Refresh it on purpose.** As production questions drift, sample new traces
  into the set and keep the old ones to catch regressions. [Drift monitoring]

## A worked example: which local model gives better hints?

```yaml
question:       Does qwen3:14b give hints that avoid giveaways more often than gemma3:12b?
change:         the model behind the drill-tutor gateway endpoint
fixed:          hint prompt, temperature 0.2, giveaway scorer, problem set
eval_set:       evals/hints.jsonl, version of 2026-10-10 (27 cases)
split:          dev (we are still iterating)
groups:         problem pattern (hash map, two pointers, sliding window, other)
metric:         no-giveaway rate, scored by the deterministic leak detector (no judge)
guardrails:     p95 seconds per hint under 10
runs:           3 per case, so 81 hints per model
size_check:     27 cases -> margin about plus or minus 19 points. Only a large difference will show.
test:           paired by case and run, McNemar rule
decision_rule:  switch to qwen3 only if it wins clearly and stays under 10 s at p95
no_result:      keep gemma3 (faster), and add cases until the set has 100
```

The size check is the honest part: with 27 cases, this experiment can only find a
big difference. That is still worth knowing, and the plan says in advance what a
small or no difference will mean.
