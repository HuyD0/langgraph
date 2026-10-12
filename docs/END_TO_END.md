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
| Statistics | Only big differences show | Margins shrink (about plus or minus 5 points at 400) and per-group results become readable, but more comparisons make the holdout confirmation more important |
| Reading regressions and improvements | Read every one | Sort them automatically first (did retrieval differ, or the answer from the same articles?), then read a sample from each bucket |
| Must-pass set | 6 questions | Still small, 10 to 50: it's a gate, not an eval set |

The Daily Drill has a lesson for each of the new steps: **Splits that don't move**,
**Drafted labels, expert-confirmed** and **Sorting changes before reading them**
(Evals), and **A smoke set for fast iteration** (Experiment design).

For high-stakes answers there is one more layer, after release rather than before
it: **Checking each claim before release** (RAG) checks every answer at request
time and releases, revises or withholds it. It complements the eval set; it
doesn't replace it.

## Agent systems: what to measure

An agent, or a team of agents, goes through the same stages. What changes is what
you measure, because an agent takes many steps, and it can pass a task once and
fail it the next time. The research behind this is in
[research/AGENT_PRACTICES.md](research/AGENT_PRACTICES.md).

| Measure | Why it matters | Lessons |
|---|---|---|
| Success rate, and pass hat k (passed on every one of k tries) | One run hides an agent that is only right some of the time | Reliable every time (pass hat k) · Evaluating agents |
| Cost per success: the cost of all runs, failed ones included, divided by the runs that passed | A design that is cheaper per run but fails more can cost more per success | Dollars per success · Comparing agent designs |
| Steps per run, and how many runs hit the step limit | Repeating steps and not knowing when to stop are common failures; a run stopped by the limit counts as failed | The agent loop · Guardrails for agents |
| How full the context gets | Answers get worse as the context fills, even when the right fact is in it | How full is the context? · What a summary forgets |
| For a team: hand-off facts kept | A supervisor that rewords a helper's report can drop a fact for good, like a game of telephone | Did the hand-off lose it? |
| For a team: tokens per agent | Name each helper's span, and the trace shows which one to make cheaper | Which helper costs the most? |

Grade the end state, not the agent's word for it: query the table, read the
ticket. A judge that reads only "I've updated the ticket" can be fooled.
**Testing the checker with planted mistakes** and **An agent that runs code**
practise this.

Before building a team, ask **Do you need a team?** Start with one agent, move up
only for a problem you can name, and compare the team with that one agent on the
same questions, by cost per success. The **Agent teams** module goes on with
**Split by what each agent needs to know**, **Fan out, then gather**, **Did the
hand-off lose it?**, **A checker with a round limit**, **Dollars per success**
and **Which helper costs the most?**. It ends with **One agent or a team: the
experiment**, which puts it all in one place: the same questions for both
designs, 3 to 5 runs each, one agent as the baseline, and a rule written before
any run. The team must win on "passed every time" by a set margin and stay under
a cost per success limit. The plan template has this experiment filled in, with
where each part lives in MLflow:
[A worked example: one agent or a team?](EXPERIMENT_PLAN.md#a-worked-example-one-agent-or-a-team). One note on tools: build a
supervisor as a main agent made with `create_agent`, with the helper agents as its
tools. The langgraph-supervisor package is no longer maintained, and on
Databricks, Supervisor Agent and the Supervisor API are listed as legacy.

**At scale**, with thousands of runs a day, nobody reads every trace:

- **Traces to a table.** On Databricks, the recommended home for production
  traces is Unity Catalog tables. They don't appear on their own: you create
  the schema first and grant MODIFY and SELECT on the tables, then query them
  with SQL. Keep every trace, and save money by judging only a sample of them.
- **Automatic checks.** The scorers from your eval run on a sample of live traces
  (production monitoring, in Beta on Databricks). Code checks first; an LLM judge
  only where code can't decide, checked against labels a person made.
- **Read what the numbers point at.** Label each failed trace with its cause,
  count the labels and fix the biggest group first (**Label failures, then
  count**). Then read a sample of the traces in that group.

## Before you build: pricing, then graduation

The reranker example starts from an app that already runs. A new idea starts one
step earlier: is it worth building, and how much capacity will it need? Work it
out before the build, then let the POC (proof of concept) swap each guess for a
measured number. The method, with a worked example, is in
[research/LLM_COST_AND_SIZING.md](research/LLM_COST_AND_SIZING.md), and the
**Pricing and sizing** module teaches it one exercise at a time.

1. **Cost per finished task.** The model cost, plus people checking answers, plus
   redoing the wrong ones, plus the errors that slip through (the lesson keeps
   that last part apart). The token bill is usually the smallest part. An agent sends everything so far again at every
   step, so price whole runs. (**Cost per finished task**, **Tokens grow every
   step**)
2. **Is it worth it?** Work out the real saving per task: the staff time freed
   (today's cost, minus checking and redo), counting only the share that is real
   money, minus the model cost and the errors that slip through. The monthly
   net, payback and break-even come from it. Then change one guess at a time to
   find the one to measure hardest. (**Payback and break-even**, **Which guess
   matters most**)
3. **Capacity.** Size for the busiest minute, not the daily average, and check it
   against the Foundry deployment's tokens-per-minute limit and the gateway's
   limits. Start on pay-as-you-go, and reserve only once traffic is steady
   (step 7). (**Size for the busiest minute**)
4. **Write it into the plan.** The [cost and capacity](EXPERIMENT_PLAN.md#cost-and-capacity)
   lines of the plan template say who gives each number.
5. **Run the POC in a shared space with fair limits.** The shared space (some
   teams call it the sandbox) is where many teams try ideas, on a model
   deployment of its own, never production's. Each user's limit sits below the
   shared space's overall limit, so one runaway test can't block everyone.
   (**A shared space with fair limits**)
6. **Graduate on evidence.** A workload leaves the shared space only when it has
   an owner, passes the eval bar and its must-pass set, costs no more per success
   than the bar allows, fits the capacity at its busiest minute, and has
   monitoring. (**The graduation gate**)
7. **Share scarce capacity by tier.** Critical apps come first. Once their
   traffic is steady, they move to reserved capacity (PTU), with spillover to a
   standard deployment for the peaks. For the models in the research,
   reserving mostly buys guaranteed throughput, not a lower price. Graduated
   apps share standard deployments sized from what the POC measured. The shared
   space gets what is left, on its own deployment. (**Who gets capacity when
   it's scarce**)
8. **Check the estimate against the bill** once it runs, and carry the gap into
   the next plan. (**Estimate against actual**)

## Where to start

- New to all of this? Do notebooks 7 and 8 first, then 9a to 9d in order.
- Planning a real experiment at work? Fill in
  [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md); 9b's plan is a filled-in example.
- Already have expert-labelled traces from MLflow? Start at 9a §3 and the
  "Building the eval set from labelled traces" section of the plan template.
- Have a RAG app at work to check against all this? Use the audit prompt in
  [RAG_AUDIT.md](RAG_AUDIT.md).
- Deciding whether an AI idea is worth building? Start with the **Pricing and
  sizing** module and the [cost and capacity](EXPERIMENT_PLAN.md#cost-and-capacity)
  lines of the plan.
- Building with agents? Measure the things in the agent table above, and
  ask **Do you need a team?** before adding a second agent. Comparing a team
  with one agent? Copy the
  [one agent or a team](EXPERIMENT_PLAN.md#a-worked-example-one-agent-or-a-team)
  plan.
  Notebook 10 runs that plan on the help-center app; on its recording the
  rule says to keep one agent.
- Giving an agent memory that lasts between chats? Store each fact with its
  source and version, close old facts instead of overwriting them, check what
  gets written, and test with planted changes: **Memory that knows when it's
  stale**, **When a new fact replaces an old one**, **Guarding what goes into
  memory** and **Testing memory with planted changes**. The evidence is in
  [research/AGENT_MEMORY.md](research/AGENT_MEMORY.md).
