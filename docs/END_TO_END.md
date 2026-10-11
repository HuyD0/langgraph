# End to end: one experiment, every stage

The lessons and notebooks each teach one piece. This page shows how the pieces fit
together, using one running example: **is a reranker worth adding to a help-center
assistant?** Notebooks 9a to 9d run that example for real, on your Mac, with MLflow
tracing and a local model (or recorded replies if Ollama isn't running).

```text
 Collect ─▶ Label ─▶ Eval set ─▶ Frame ─▶ Design ─▶ Build & trace ─▶ Evaluate ─▶ Ship ─▶ Monitor
    ▲                                                                                    │
    └──────────────── new failures become new labelled examples ◀────────────────────────┘
```

## The stages, in order

| Stage | What you do | Where it's in the example | Lessons that teach the pieces |
|---|---|---|---|
| **Collect** | Trace what the app does on real traffic | 9a §1: v1 answers 55 customer questions, every request an MLflow trace | Designing traces for experiments |
| **Label** | Experts grade answers (feedback) and say what a right answer must contain (expectations) | 9a §2: grades and expected facts logged on each trace | Checking your LLM judge · Agreement beyond chance |
| **Build the eval set** | Pull labelled traces into a versioned dataset; group, stratify, choose the must-pass set; split dev / test / holdout | 9a §3-5: `merge_records`, groups against traffic, 6 must-pass questions, 3-1-1 split | Dev, test and holdout sets · Report each group · A must-pass set · How many examples do you need? |
| **Frame** | Write the question, the metric, the guardrails and the decision rule before any result | 9b §1: the plan | Write the plan before the runs |
| **Design** | Choose the variants: the change, plus oracle and ablation runs to explain it; size check; limit comparisons | 9b §2: v1, v2, v2 without rewrite, oracle; 2 runs each | Oracle tests · Ablations · Testing many variants · Margins near 0% and 100% |
| **Build and trace** | Tag traces, type the steps, name each version, so the runs can be inspected | 9b §3-4: tags, RETRIEVER / RERANKER / CHAT_MODEL spans, `set_active_model` | Designing traces for experiments |
| **Evaluate** | Gate on must-pass; read the oracle; compare by group; paired test; read regressions and improvements; set aside flaky questions; check the reranker and the ablation; decide by the rule; confirm on the holdout | 9c, step by step in that order | A must-pass set · Oracle tests · Comparing on the same examples · Reading regressions and improvements · Did the reranker help? · Ablations |
| **Ship** | Release behind the must-pass gate, then a canary | 9d §1 | Canary releases · Rolling out a new prompt |
| **Monitor** | Watch real traffic for signals like a rising "I don't know" rate; trace back to a cause; fix | 9d §2-3: a new article that search can't find | Drift monitoring · Reading agent traces |
| **Grow the eval set** | Label the new failures and merge them in as a new version | 9d §4: dataset version 2, with the new group | Dev, test and holdout sets |

Then the loop starts again: the next experiment begins from the bigger eval set.

## When each thing happens

The part that confuses most people is that most of the analysis tools are **set up
early and used late**:

- The **must-pass set** is chosen when the eval set is built, long before any
  experiment, and checked first in Evaluate and again at Ship.
- **Oracle tests** and **ablations** are extra variants planned in Design and run
  alongside the real comparison. They only get read in Evaluate.
- **Repeat runs** are decided in Design; they are what lets Evaluate tell flaky
  questions from real changes.
- **Tags and typed steps** are added in Build and trace. Without them, the
  question-by-question analysis in Evaluate is impossible, because it can't be
  added to traces afterwards.
- The **holdout** is created when the eval set is split, then left alone until the
  very end of Evaluate, when the winner is confirmed on it once.

## When the set gets big: hundreds of questions

The notebooks use 55 questions so they run in minutes. With hundreds, the method
is the same; these steps change:

| Step | With 55 questions | With hundreds |
|---|---|---|
| Expected answers | Experts write them | An LLM drafts expected facts from the trace and its source article; experts confirm or fix. Expert time goes to the must-pass set, rare groups and disputed drafts. |
| Grading | A deterministic check | An LLM judge aligned to the experts, with expert spot checks each round and kappa tracked over time |
| Duplicates and groups | Hand-picked | Cluster near-duplicates by meaning (embeddings); keep a few per cluster. The clusters are often the groups. |
| Splits | Dealt by position | Assigned from a hash of the question id, so a question never changes split as the set grows; one user or conversation stays in one split |
| Running variants | Everything, every time | A stratified "smoke" sample of 50-100 while iterating; the full set for finalists; parallel requests with a concurrency cap; cache steps that don't change between variants |
| Statistics | Only big differences show | Margins shrink (about ±5 points at 400) and per-group results become readable, but more comparisons make the holdout confirmation more important |
| Reading regressions and improvements | Read every one | Sort them automatically first (did retrieval differ, or the answer from the same articles?), then read a sample from each bucket |
| Must-pass set | 6 questions | Still small, 10 to 50: it's a gate, not an eval set |

The Daily Drill has a lesson for each of the new steps: **Splits that don't move**,
**Drafted labels, expert-confirmed** and **Sorting changes before reading them**
(Evals), and **A smoke set for fast iteration** (Experiment design).

For high-stakes answers there is one more layer, after release rather than before
it: **Checking each claim before release** (RAG) checks every answer at request
time and releases, revises or withholds it. It complements the eval set; it
doesn't replace it.

## Where to start

- New to all of this? Do notebooks 7 and 8 first, then 9a to 9d in order.
- Planning a real experiment at work? Fill in
  [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md); 9b's plan is a filled-in example.
- Already have expert-labelled traces from MLflow? Start at 9a §3 and the
  "Building the eval set from labelled traces" section of the plan template.
