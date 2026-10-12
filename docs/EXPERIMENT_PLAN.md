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
guardrails:     # Must-not-get-worse numbers: p95 latency, cost per request or per finished task, refusals...
runs:           # Runs per example (3 or more for anything with randomness in it).
size_check:     # n examples -> margin about 100 / sqrt(n) points. Is it smaller than the change you expect?
test:           # How you compare: paired (McNemar) for pass/fail on the same examples.
decision_rule:  # What you will do for each outcome, decided now.
no_result:      # What "too close to call" means you will do.
```

If the work will run on a paid model, or someone must decide whether it is worth
building, add the [cost and capacity](#cost-and-capacity) lines too.

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
so a quality gain cannot hide a cost or speed loss. When the change is meant to
cut cost, it works the other way round: the quality metric is the guardrail
(see [cost guardrails](#cost-guardrails-next-to-the-quality-metric)). If an LLM
judge scores the metric, check it against human labels first, on passes and
failures separately, and with Cohen's kappa. [Checking your LLM judge] [Agreement beyond chance]

For RAG, score retrieval and answers separately: recall@k and nDCG for the
ranking [Ranking quality: nDCG], and include questions your documents cannot
answer, tracking missed refusals and over-refusals [Knowing when not to answer].
For agents, run each task k times and report pass hat k (passed on every one of
the k tries) next to the success rate [Reliable every time (pass hat k)], and score the tool calls and the path where you
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

## Cost and capacity

Add this block to `plan.yaml` when the work will run on a paid model, or when
someone must decide whether it is worth building. Fill it in before you build,
for the same reason you write the metric before the runs. The comment on each
line says who gives you the number. The method, with a worked example for an HR
help desk, is in [research/LLM_COST_AND_SIZING.md](research/LLM_COST_AND_SIZING.md).

```yaml
cost_and_capacity:
  # Today, without AI
  tasks_per_month:     # the business owner
  minutes_per_task:    # the business owner
  hourly_rate:         # the business owner
  # With AI
  share_ai_handles:    # the business owner, then the POC
  share_staff_use_it:  # the business owner, then the POC
  real_money_share:    # the business owner
  input_tokens_per_task:   # measured by the POC
  output_tokens_per_task:  # measured by the POC
  price_in_per_million:    # the price list, with its date
  price_out_per_million:   # the price list, with its date
  # Shares of all the AI's answers
  right_answer_share:  # right; measured by the POC
  caught_share:        # wrong but caught; measured by the POC
  check_share:         # checked by a person; the business owner
  check_minutes:       # the business owner
  redo_cost:           # today's cost for one task; the business owner
  error_cost:          # one wrong answer that slips through; the business owner
  fixed_monthly:       # the price list
  build_cost:          # the engineers
  # Capacity
  busiest_minute:      # measured by the POC
  tpm_limit:           # the platform team
  gateway_limits:      # the platform team
  # Guardrails
  cost_guardrail:      # you, before the runs
  switch_off_rule:     # you and the business owner
```

**Today, without AI.** Tasks a month, minutes for each, and the hourly rate with
the employer's extra costs on top of pay. They come from system records, not
memory. Today's cost for one task is the minutes divided by 60, times the
hourly rate.

**With AI.** How many tasks the AI can take, how many staff will use it, and how
much of the freed time is real money: hiring avoided, less overtime, fewer
contractors. Time saved that nobody stops paying for is not a saving. The
business owner guesses these first; the POC (proof of concept) swaps each guess
for a measured number.

Tokens in and tokens out are separate lines because output costs about 5 to 6
times as much as input. The model cost for one task is the input tokens times
the input price, plus the output tokens times the output price, divided by a
million. The three answer shares are out of all the AI's answers. Whatever is
neither right nor caught slips through: in 100 answers with 80 right and 15
caught, 5 slip through.

**Cost per finished task.** The model cost, plus a person checking some answers,
plus redoing the wrong answers that get caught, plus the cost of the wrong ones
that slip through. Work out each part for one task:

- **Model**: the model cost above.
- **Checking**: `check_share` times `check_minutes`, divided by 60, times
  `hourly_rate`.
- **Redo**: `caught_share` times `redo_cost`. A person redoes each caught answer
  by hand, so one redo costs the same as today's cost for one task.
- **Slip-through**: the share that is neither right nor caught, times
  `error_cost`.

Add the four parts. In the HR help desk example that is 6.5 cents of model, 60
cents of checking, $1.20 of redo and 50 cents of slip-through: $2.365 a ticket.
The token bill is usually the smallest part. The **Cost per finished task**
lesson adds up only the first three parts ($1.865) and keeps slip-through
apart; the real saving below comes out the same either way.

**Real saving per task.** The monthly net, payback and break-even come from this
number, not from the cost per finished task. Work it out in two steps:

1. Staff time freed: today's cost, minus checking, minus redo. In the example,
   $8 minus 60 cents minus $1.20 is $6.20.
2. Real saving: the staff time freed, times `real_money_share`, minus the model
   cost, minus the cost of the errors that slip through. In the example all the
   freed time is real money, so $6.20 minus 6.5 cents minus 50 cents is $5.635.

The share shrinks only the freed staff time, because the model and the errors
are paid either way. Only when the share is 1 does the real saving equal
today's cost minus the cost per finished task. From the real saving:

- **Monthly net**: tasks through the AI (tasks a month, times the share the AI
  handles, times the share of staff who use it), times the real saving, minus
  `fixed_monthly`.
- **Payback**: `build_cost` divided by the monthly net, in months.
- **Break-even**: `fixed_monthly` divided by the real saving: the tasks a month
  needed just to cover the running costs.

Then change one guess at a time: the one that moves the answer most is the one
to measure hardest. [Payback and break-even] [Which guess matters most]

**Capacity.** Size for the busiest minute, not the daily average, with room for
bursts. Check it against the Foundry deployment's tokens-per-minute limit and
the gateway's rate limits; the platform team knows both. Foundry's limit check
counts the prompt plus the longest answer you allow (`max_tokens`), not the
tokens used. Start on pay-as-you-go, and reserve capacity only once traffic is
steady. [Size for the busiest minute]

### Measuring tokens from the POC's traces

Take the token numbers from real POC runs, not from one short test. MLflow 3
records input and output tokens on each trace, so read them back and price them
with a dated table you write yourself:

```python
import mlflow

# Example prices, dollars per million
# tokens, checked 2026-10-11. Check yours.
PRICE_IN = 2.00
PRICE_OUT = 10.00

# Your POC's experiment id: it is on
# the experiment's page in MLflow.
EXPERIMENT_ID = "<your experiment id>"

traces = mlflow.search_traces(
    locations=[EXPERIMENT_ID],
    return_type="list",
)
costs = []
for t in traces:
    use = t.info.token_usage
    if use is None:  # not recorded
        continue
    inp = use["input_tokens"] * PRICE_IN
    out = use["output_tokens"] * PRICE_OUT
    costs.append((inp + out) / 1_000_000)

if not costs:
    print("no token usage recorded")
else:
    costs.sort()
    n = len(costs)
    # 1 in 10 cost less than low,
    # 1 in 10 cost more than high
    low = costs[n // 10]
    typical = costs[n // 2]
    high = costs[n * 9 // 10]
```

- A trace's `token_usage` already adds up every model call inside it. So when
  one trace covers a whole agent run, its cost is the cost of the task. If one
  task is spread over several traces (say, one per chat turn), give them the
  same tag when they are made, for example
  `mlflow.update_current_trace(tags={"task_id": ...})`. Then add up the costs
  of the traces that share a `t.info.tags["task_id"]` before working out low,
  typical and high.
- An agent sends everything so far again at every step, so measure whole runs.
  [Tokens grow every step]
- Put each trace's cost next to its scorer result. All the cost, failed runs
  included, divided by the runs that passed, is the cost of one success.
  [Dollars per success]
- `system.ai_gateway.usage` is a second source. The gateway logs every call with
  its tokens and request tags, even for traces you did not keep. Tag the POC's
  and the eval's requests so their cost shows up on its own.
- MLflow can add a dollar cost itself (from 3.10, through LiteLLM), but on
  Databricks-managed MLflow only if your app installs LiteLLM or you set it. The
  bill of record is Azure Cost Management.

### Cost guardrails next to the quality metric

- **Cost sits next to the metric.** Put cost per finished task (for agents,
  dollars per success) in `guardrails`. A cheaper model that fails more tasks
  can cost more for each success.
- **A cost cut needs the eval too.** A smaller model, a shorter prompt or less
  context can each lower quality. Run the eval set before and after, and keep
  the change only if quality holds: in a cost cut, the eval score is your
  guardrail, and it must not drop past the tolerance you wrote down.
- **Stopped runs are failures.** A run that hits its step or token limit did not
  finish the task, so count it as failed, not as missing.
- **Write the switch-off rule now**: for example a cost ceiling, or too few
  people using it, that pauses the work when crossed.
- **In production, use three layers.** A budget alert tells you, a rate limit
  slows one caller, a loop cap stops a runaway run. An alert alone stops
  nothing.

Once it runs, put the estimate next to the real bill, and carry what the gap
teaches into the next plan. [Estimate against actual]

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
9. **Guardrails.** Time, and cost per request or per finished task. [Cost per finished task]
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

## A worked example: one agent or a team?

The help-center assistant from [END_TO_END.md](END_TO_END.md) answers with one
agent today. Someone suggests a team: a supervisor, two research helpers that
each search one part of the help center, and a checker. Is it worth it? Agents
vary from run to run, and a team costs more, so this plan adds two lines to the
template (`baseline` and `variants`) and reports a few more numbers. The lesson
**One agent or a team: the experiment** practises the decision rule.

```yaml
question:       Does a team answer help-center questions more reliably than one agent, at a cost we accept?
change:         the design: one agent, or a supervisor with two research helpers and a checker
fixed:          model and version, temperature, tools, step limit of 15, scorers, price table
baseline:       one agent, the design that runs today
variants:       one-agent, team-v1, and team-v1 without its checker (the ablation)
eval_set:       help-center-agent, version of 2026-10-12 (50 questions, most from real failures)
split:          dev (we are still building the team)
groups:         one-article questions, two-article questions, questions the help center can't answer
metric:         passed every time: the share of questions passed on all 4 tries, the answer checked by code
also_report:    pass rate, steps per run, hand-off facts kept, tokens per agent, failure labels
guardrails:     dollars per success at most 0.50; a run that hits the step limit counts as failed
runs:           4 per question for each design, so 200 runs per design
size_check:     50 questions -> margin about plus or minus 14 points, so the rule asks for 15.
                20 to 50 is enough to start; with 20, only a very large gap would show.
test:           paired by question, McNemar rule
decision_rule:  switch to team-v1 only if its "passed every time" beats one-agent's by 0.15 or more
                AND its dollars per success stays at most 0.50
no_result:      keep one agent; label the failures and add them to the set
```

The ablation answers a different question: what does the checker buy? If
team-v1 without its checker passes as often, the checker is only cost. The
decision rule is about one-agent against team-v1; the ablation explains it.
[Ablations: what each part is worth]

### Each part, and where it lives in MLflow

- **eval_set.** A versioned evaluation dataset:
  `mlflow.genai.datasets.create_dataset(name=...)`, then `merge_records`. See
  [Building the eval set from labelled traces](#building-the-eval-set-from-labelled-traces).
- **variants.** Give each design a name with
  `mlflow.set_active_model(name="one-agent")` (and `"team-v1"`,
  `"team-v1-no-checker"`). It returns the model; pass its `model_id` to
  evaluate, so every trace knows which design made it.
- **runs.** `mlflow.genai.evaluate(data=..., predict_fn=..., scorers=[...], model_id=...)`
  runs each question once. It has no repeat option, so call it 4 times for
  each design. [Reliable every time (pass hat k)]
- **metric.** A `@scorer` from `mlflow.genai.scorers` that checks the answer
  with code (the expected facts are in it), not the agent's word that it
  answered. [Evaluating agents]
- **hand-off facts kept.** A `@scorer` that takes `trace`. It finds a helper's
  span with `trace.search_spans(span_type=SpanType.AGENT, name="researcher")`,
  reads the facts in its output, and returns the share that reach the final
  answer. [Did the hand-off lose it?]
- **steps and tool calls.** The built-in `ToolCallCorrectness()` and
  `ToolCallEfficiency()` scorers. Both are LLM judges, so check them against a
  few labels of your own. Count the steps from the spans, and count the runs
  that hit the limit as failed. [Right tool, right arguments] [Guardrails for agents]
- **tokens per agent.** Give each helper its own named span:
  `mlflow.start_span(name="researcher", span_type=SpanType.AGENT)`, or the node
  names when LangGraph autolog traces it. Then add up
  `span.get_attribute("mlflow.chat.tokenUsage")` (a dict with `input_tokens`,
  `output_tokens` and `total_tokens`) for the model spans under each helper.
  [Which helper costs the most?]
- **dollars per success.** Each trace's `t.info.token_usage`, times your price
  table, added up over all runs, failed ones included, then divided by the runs
  that passed. See [Measuring tokens from the POC's traces](#measuring-tokens-from-the-pocs-traces).
  [Dollars per success]
- **failure labels.** A person reads each failed trace and logs one cause, such
  as "repeated steps" or "never checked", with
  `mlflow.log_feedback(trace_id=..., name="failure", value="repeated steps")`.
  Count the labels and fix the biggest group first. [Label failures, then count]
- **the results table.** `mlflow.search_traces(model_id=..., return_type="list")`
  for each design, grouped by question, gives "passed every time".

The runs and the table, in short. `one_agent`, `team` and `team_no_checker`
are your three designs. Each one tags its trace with the question's id, using
`mlflow.update_current_trace(tags={"question_id": ...})`. `end_state` and
`handoff` are the two `@scorer` functions above. The one agent has no helper,
so it gets only `end_state`.

```python
import mlflow
from mlflow.genai.datasets import get_dataset

dataset = get_dataset(name="help-center-agent")
designs = {
    "one-agent": one_agent,
    "team-v1": team,
    "team-v1-no-checker": team_no_checker,
}

every_time = {}
for name, predict in designs.items():
    model = mlflow.set_active_model(name=name)
    scorers = [end_state]
    if name != "one-agent":  # has helpers
        scorers.append(handoff)
    for _ in range(4):  # no repeat option
        mlflow.genai.evaluate(
            data=dataset,
            predict_fn=predict,
            scorers=scorers,
            model_id=model.model_id,
        )
    traces = mlflow.search_traces(
        model_id=model.model_id,
        return_type="list",
    )
    tries = {}  # question id -> passes
    for t in traces:
        q = t.info.tags["question_id"]
        a = t.search_assessments("end_state")
        ok = bool(a) and a[0].value is True
        tries.setdefault(q, []).append(ok)
    kept = [q for q in tries if all(tries[q])]
    every_time[name] = len(kept) / len(tries)
```

Then apply the rule you wrote above, and only that rule. If the team wins on
"passed every time" but costs more than 0.50 per success, the answer is still
one agent.
