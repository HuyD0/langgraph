# Teaching from this repo

Written for whoever runs the session — including you, six months from now, having
forgotten where the sharp edges are.

## The thing worth knowing first

**The whole notebook track needs no Azure credentials, and no cloud spend.**

- `m1`–`m3` are pure Python. No `drill` import, no model, nothing to provision.
- `m4`–`m6` import `drill` but only for data structures and a fake chat model.

So you can hand six people a laptop each and run the entire six-milestone
curriculum on `uv sync --dev` alone. Only `drill start` — the live tutor — needs a
Foundry deployment, and that is a demo *you* run once on the projector, not
something every student needs wired up.

This is checked, not hoped: CI runs the whole suite with no Azure variables set.

## Setup, and what actually breaks

```bash
git clone <repo> && cd langgraph
uv sync --dev
uv run pytest            # 143 tests, ~35s. If this passes, everything works.
uv run jupyter lab       # then open notebooks/m1_state.ipynb
```

Have students run `uv run pytest` *before* the session starts. It is the single
check that catches a broken environment, and it catches it at home rather than in
the first ten minutes of your workshop.

Three things that go wrong, in order of how often:

1. **They edit an exercise cell and re-run only the test cell.** The tests use
   whatever is currently defined in the kernel, so nothing changes and they
   conclude their fix did not work. Say this out loud at the start, and again
   at milestone 2.
2. **`uv` is not installed.** The only true prerequisite. Send the install link
   with the invite.
3. **Kernel picks the wrong Python.** `uv run jupyter lab` rather than a
   system-wide `jupyter` avoids it entirely.

## Per milestone

Times assume people who can write Python but have not built a graph before. Halve
them for strong engineers; do not halve the discussion.

| # | Notebook | Time | The one idea | Where they get stuck |
|---|---|---|---|---|
| 1 | `m1_state` | 20 min | A node returns a *partial* update, not the whole state | Returning the merged state from `bump_attempts` instead of just `{"attempts": n}` |
| 2 | `m2_problems` | 30 min | Error messages are a design surface | Forgetting `from None`, so the KeyError shows chained-exception noise |
| 3 | `m3_routing` | 15 min | Isolate the decision; test it exhaustively | Checking the attempt budget *before* `passed`, which fails a last-attempt solve |
| 4 | `m4_progress` | 30 min | Sort by a tuple to get two rules at once | The tie-break — most first drafts rank by rate only |
| 5 | `m5_sandbox` | 45–60 min | Turn every failure into data, never an exception | Letting `TimeoutExpired` escape; forgetting `list(c.args)` because JSON has no tuple |
| 6 | `m6_graph` | 30 min | A cycle needs something that changes, or it never ends | Omitting the checkpointer, then not understanding why `interrupt()` does nothing |

A full day is comfortable. Two half-days is better: 1–4 in the first, 5–6 in the
second, and they will have slept on the state idea before wiring the graph.

### Unsticking without solving it for them

The tutor's own rule is the right rule for you: **no code.** Escalate the same way
it does — ask a question, then name the concept, then describe the approach in
prose, and still make them type it.

For milestone 5 specifically, the productive question is "what happens to your
session if a student's submission has an infinite loop?" That reframes the
timeout from a detail into the whole point of the milestone.

## Demo moments

Three places where showing beats telling. All three are one cell.

**The graph, drawn.** `m6_graph` cell 6 renders the compiled graph as Mermaid
straight from `build_drill_graph()`. Showing that the picture is generated *from
their code* — not drawn in a diagramming tool — reliably lands the idea that the
graph is data.

**Interrupt and resume.** `m6_graph` runs a real pause-and-resume with a fake
model. Invoke, show the graph is parked mid-execution, then resume with
`Command(resume=...)`. This is the moment human-in-the-loop stops being a phrase.

**An MLflow trace.** You need credentials for this one, so run it yourself:

```bash
uv run drill start --problem two_sum     # solve it badly on purpose
uv run mlflow ui                         # open the trace tree
```

Show the span tree: node by node, the prompt the tutor was sent, the reply. Then
point at the `hint` span and ask whether that hint was any good. That question is
the doorway to evaluation, and it is the part most people building with LLMs have
never actually done.

## The answer key

`notebooks/solutions/` holds a worked solution for every exercise, with comments
explaining *why* each line is the way it is — not just what it does.

It is verified. `tests/test_notebooks.py` substitutes the key into each notebook,
runs it in a real kernel, and requires every embedded test to pass. Two failure
modes are caught:

- A notebook whose tests cannot all be satisfied.
- Drift: an exercise renamed without updating the key, or a stale solution left
  behind.

So if you tighten a spec mid-prep, CI tells you before a room full of people does.
A separate CI job also fails if a notebook is ever committed with its `TODO`s
filled in, which is the accident that quietly hands out the answers.

## Adding your own material

**A problem:** append a `Problem` to `src/drill/problems/catalog.py`.
`tests/test_catalog.py` then automatically checks your reference solution against
your own test cases, that your starter code does *not* pass, and that you left
both a sample and a hidden case. A malformed problem fails the suite immediately.

**A milestone:** add `notebooks/m7_*.ipynb` and `notebooks/solutions/m7_*.py`. The
notebook tests pick it up by glob — no registration — and will fail until the
answer key covers every exercise you wrote.

## Known limits

Be straight with students about two things rather than letting them discover them.

**The sandbox is not a security boundary.** It runs their code in a subprocess
with a timeout, which stops an infinite loop from hanging the session. It does not
contain hostile code and does not try to. Fine for a workshop where everyone runs
their own code; not fine as a shared submission service on a network.

**Progress is single-learner.** `.drill/progress.json` is one file with no notion
of who is practising, so `drill stats` cannot show you a cohort. For a group,
today, each student reads their own. Tracking a class properly means giving the
store a learner identity.
