# The curriculum

Three tracks, meant to be run at the same time.

**Track A — drill.** Use the tutor. 20–40 minutes, most days. This builds the
pattern recognition that interviews test.

**Track B — build.** Reimplement the tutor, one milestone at a time. This builds
the engineering the interview conversation is actually about.

**Track C — the Daily Drill page.** One lesson a day from the learning path: AI
engineering from foundations to shipping, each lesson a short read, a question, an
exercise and an interview angle. This is the AI-specific knowledge; the other two
tracks are the craft underneath it.

They reinforce each other. Track A gives you the problem patterns; track B gives
you something real to talk about when an interviewer asks what you have built;
track C gives you the vocabulary and the stack.

---

## Track A: drilling

```bash
uv run drill start          # picks from your weakest topic
uv run drill stats          # where you actually stand
```

How the tutor is set up to work, and why:

- **Three attempts.** Enough to struggle productively, not enough to spiral.
- **Hints, not answers.** The tutor is instructed never to write code. It nudges,
  then names the concept, then describes the approach in prose — and still makes
  you write it. `drill.evaluation` enforces that mechanically.
- **It holds tests back.** You see one sample case. The rest are hidden, so you
  cannot pass by special-casing the examples. Same deal as a real interview.
- **It reviews solutions that pass.** Getting green is not the end. The review
  covers complexity and the edge case you did not mention, which is where
  interviews are usually won or lost.

### Getting the most out of it

State your approach out loud before you write anything. Interviews are graded on
the narration as much as the code — and if you cannot say it, you do not have it.

When you are stuck, read the failing case before you reach for a hint. Most
failures are a boundary: an empty input, a single element, everything negative.
Learning to find those yourself is the skill.

After you solve one, do not move straight on. Ask what the *pattern* was. The
`pattern` field on each problem states it in one line, and the patterns generalise
where the specific puzzles do not.

### The patterns in the bank

| Topic | Pattern | Problems |
|---|---|---|
| hash-map | Trade memory for time | `two_sum`, `group_anagrams` |
| stack | Match nested pairs | `valid_parentheses` |
| binary-search | Halve the search space | `binary_search` |
| sliding-window | Grow right, shrink left | `longest_unique_substring` |
| dynamic-programming | Build from smaller answers | `climbing_stairs`, `max_subarray` |
| sorting | Sort first, then sweep | `merge_intervals` |
| graph | Flood-fill from each start | `num_islands` |

Nine problems is a starting point, not a course. Add your own — append a `Problem`
to `src/drill/problems/catalog.py` and `tests/test_catalog.py` will check your
reference solution against your own test cases automatically.

---

## Track B: building

```bash
uv run jupyter lab notebooks/   # then open m1_state.ipynb
```

Each milestone is a notebook in `notebooks/`: the explanation, a cell per exercise
for you to fill in, and a cell of tests right after it that runs inline (via
`ipytest`). **The tests are the specification.** Run them before you write
anything and read what they check — that is the habit worth building, and it is
what TDD actually means. Each notebook ends with a "Try it" section that puts
your code to work on something real.

| # | Milestone | You learn | Hardest part |
|---|---|---|---|
| 0 | `m0_python_basics.ipynb` | Loops, dicts, edge cases, what O(n) means | Starting `best` at a real item, not 0 |
| 1 | `m1_state.ipynb` | Typed dicts, partial updates, not mutating shared state | Realising the update is *partial* |
| 2 | `m2_problems.ipynb` | Dataclasses, lookup tables, error messages as design | The KeyError that lists valid ids |
| 3 | `m3_routing.ipynb` | Pure functions, branching policy | Passing on the last attempt still counts |
| 4 | `m4_progress.ipynb` | Aggregation, ratios, tie-breaks | The tie-break rule |
| 5 | `m5_sandbox.ipynb` | Subprocess, serialisation, failure as data | Never raising on a bad submission |
| 6 | `m6_graph.ipynb` | LangGraph: nodes, conditional edges, cycles, checkpointers | Why the checkpointer is mandatory |
| 7 | `m7_inside_the_model.ipynb` | Tokens, next-word chances, temperature/top-k/top-p, reading vs writing speed, the cache, quantization, fair comparisons | Writing your guess down *before* running the experiment |
| 8 | `m8_designing_an_eval.ipynb` | One complete experiment: a written plan, eval set margins, per-group scores with ranges, a paired comparison, the bootstrap, and a decision | Keeping the rule you wrote when the result tempts you |
| 9a | `m9a_build_the_eval_set.ipynb` | Tracing production traffic, expert labels (feedback vs expectations), pulling traces into an MLflow dataset, stratifying, the must-pass set, a dev / test / holdout split | Seeing that grades don't carry into the eval set |
| 9b | `m9b_plan_and_run.ipynb` | Framing and designing a RAG experiment: the plan, oracle and ablation variants, tags and typed spans, a robust reranker parser | Not deciding yet |
| 9c | `m9c_analyse_and_decide.ipynb` | The Evaluate stage in order: must-pass gate, oracle headroom, groups, flaky questions, the paired test, reading regressions and improvements, the reranker check, the ablation, the time guardrail, the holdout | Doing the steps in order |
| 9d | `m9d_ship_monitor_grow.ipynb` | Shipping behind a gate, a monitoring signal, tracing a production failure to its cause, growing the eval set as a new version | Closing the loop |

Milestones 1–4 are ordinary Python and transfer directly to interviews.
Milestone 5 is the one senior engineers will want to talk about — running code you
did not write, safely, is a real systems problem. Milestone 6 is the LangGraph one. Milestone 7 steps
back from the tutor to the model itself: six small experiments on a local model
(through Ollama, or recorded results if you don't have it), each run the
scientific-method way - question, written guess, one change, verdict.

`src/drill/` is the worked answer to all six. Looking is allowed. But write your
version first: reading a solution feels like understanding and usually is not —
the same trap as reading someone else's accepted LeetCode answer and believing you
could have produced it.

`notebooks/solutions/` is the answer key for the notebook exercises specifically —
including milestones 1-4, whose `merge_update`, `build_index` and friends are
teaching constructs that do not exist in `src/drill/` at all.

### A suggested order

0. New to coding? Do milestone 0 first, and keep [CONCEPTS.md](CONCEPTS.md)
   open: it explains every term the notebooks use, what Big-O means, and a
   routine for starting when the cell is blank.
1. Milestone 1 and 3 in one sitting. Both are short; they teach the shape.
2. Drill for a few days. Let track A run.
3. Milestone 2 and 4. Data modelling and aggregation.
4. Milestone 5. Take your time — it is genuinely harder than the rest.
5. Milestone 6, once you have read `src/drill/graph.py` and the LangGraph docs on
   [persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
   and [human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/).
6. Milestone 7 whenever you're curious why the model behaves the way it does.
   It doesn't depend on milestones 1-6, only on milestone 0.
7. Milestone 8 after milestone 7, or before your first real "is my change
   better?" decision at work. [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) is the
   template it follows.
8. Milestones 9a to 9d, in order, to see every stage of the lifecycle in one
   project. [END_TO_END.md](END_TO_END.md) is the map that ties them together.

---

## Track C: the Daily Drill page

```bash
uv run drill-server             # then open http://localhost:8787
```

Or use the published page on claude.ai. Either way the path is the same: 14 modules in
the order of the ML lifecycle (frame, design, build and trace, evaluate, ship, monitor),
and the page keeps track of which lessons are done. One lesson is 15 to 30 minutes.

Each lesson is four steps. **Learn** is a short read with one worked example. **Check**
is a single question, to find out whether the read landed. **Build** is a small Python
function with tests, in the browser, with a fill-in-the-blanks scaffold when you are
stuck. **Interview** is how to talk about the idea, and which classic problem from track
A uses the same pattern. Most lessons also show the same idea in your stack: Databricks,
LangGraph, LangChain or MLflow.

The content is in `src/drill/content`, one file per module; [PAGE.md](PAGE.md) explains
how to add a lesson. The classic problems on the page are the same bank track A drills.

---

## Using MLflow on yourself

Every session is traced. Once you have a week of practice:

```bash
uv run mlflow ui     # then open http://localhost:5000
```

Two things worth doing there.

**Look at your own traces.** Each session is a tree: which node ran, what the
tutor was asked, what it replied. When a hint was useless, this is where you find
out whether the prompt was bad or the failing-case summary was.

**Chart yourself over time.** Every session logs `attempts`, `hints_used`,
`solved` and `duration_s` against a topic. Sort by topic and you have an honest
answer to "what am I still bad at" — which beats the feeling that you are bad at
everything, and it beats grinding problems you can already do.

Then close the loop: edit a prompt in `src/drill/prompts.py`, re-run
`drill.evaluation.evaluate_hints` over your recorded sessions, and see whether the
hints got better or just longer. That loop — change a prompt, measure it against
real recorded data — is the thing most people building with LLMs have never
actually done, and it is worth being able to describe in an interview.

Before you change the prompt, write down how you will judge the change:
[EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) is a fill-in template, with this exact
experiment (which local model gives better hints) worked through. It covers the
eval set and its splits, how many examples you need, comparing case by case, and
the decision rule. The Daily Drill's *Experiment design* and *Evals* modules teach
each part with an exercise.

---

## Teaching this to someone else

See [TEACHING.md](TEACHING.md): per-milestone timings, where people get stuck, how to unstick them without solving it for them, and the three demo moments worth putting on a projector.

The headline for anyone planning a session: **the whole notebook track needs no Azure credentials and no cloud spend.** Milestones 1-3 are pure Python; 4-6 import `drill` only for data structures and a fake chat model; 7, 8 and 9a-9d use a free local model through Ollama if you have one, and recorded results if you don't. Just `uv sync --dev`.
