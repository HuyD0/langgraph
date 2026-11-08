# The coach-retrieval lab: fine-tune an embedding model, start to finish

*Learning material. Nothing here runs in CI. Run it by hand, locally first, then push the same
stages to Azure Databricks.*

## What we are building, and why

When a learner asks the coach a question on a lesson page, the page tells the coach which lesson it is,
so today the coach has nothing to find. Where no lesson is known (a follow-up on the study list, the
blueprint's coach, Claude's tools) the coach would first have to **find the lesson paragraphs that answer
it** (retrieval) with an **embedding model**: a model that turns text into a list of numbers so that texts
with similar meaning land close together. The champion for that step is `bge-large` straight from its
makers, scored at recall@5 0.84 on the course's own Check questions (`drill experiment embeddings`,
PR #170); it is not wired into the coach yet (stage 6).

This lab **fine-tunes that embedding model on the course**, so that a learner's question in their own
words finds the right lesson more often. It is small enough to run on your computer in minutes, its
score is a plain yes-or-no ("did the right lesson come up?"), and the result plugs straight into the
coach. That makes it the right first proof of concept for the whole AI/ML operations lifecycle: every
stage below is one you would run for any model, at work, on Azure Databricks.

**How the fine-tuning works, in plain words.** The model is shown pairs: a question and the paragraph
that answers it. Each training step pulls the two closer together and pushes the other paragraphs in
the batch away. The real term is **contrastive learning**. The hard cases, which teach the most, are
paragraphs from the *neighbouring* lesson in the same module, because that is what the model confuses
today.

## The lifecycle, locally and then on Azure Databricks

Each stage is one notebook. You do it on your computer with the local MLflow server, then repeat it in
the workspace (stage 8), so you see what changes and what does not. The right-hand column names the
Daily Drill lessons each stage applies.

| # | Stage | On your computer | On Azure Databricks | Lessons applied |
|---|---|---|---|---|
| 0 | **Vet** the use case | `00_vet.ipynb`, `vetting/assessment.md`: the one line, the three gates, the card, the bars with reasons | The same card; the cost sheet gets real DBU prices | Is this a good AI use case?, Is it fit for purpose?, A must-pass set, Total cost of ownership |
| 1 | **Data** and splits | `01_pairs.ipynb`: pairs from the content; split by *whole lesson*, stratified by module, 60/20/10/10 (train/dev/test/holdout, the holdout locked), frozen; registered as MLflow datasets with digests | The same pairs as a Delta table in Unity Catalog, versioned by time travel | Splits that don't move, Dev, test and holdout sets |
| 2 | **Baselines** | `02_baselines.ipynb`: `bge-large` and `embeddinggemma` as they come; the honest test (learner-worded questions) on the dev lessons, test closed until stage 4; the champion and the bar | Same code, same datasets | Measuring retrieval, Embedding models have blind spots, Comparing on the same examples, Report each group, weighted by real traffic |
| 3 | **Train** | `03_train.ipynb`: one step by hand; the loss; hard negatives; learning rate; seeds; checkpoints; every run logged | A GPU job (`databricks air run`) with this same code, logging to the workspace's MLflow. Databricks' managed fine-tuning product never covered embedding models and has reached end of life, so bring your own training code | Pinning provider versions; the Steam lab's training notebook (one step by hand, checkpoints) |
| 4 | **Evaluate** | `04_evaluate.ipynb`: hit@1 and recall@5 against the champion on the test lessons; Wilson intervals; a paired test (McNemar); the forgetting check | Same code; the eval dataset lives in Unity Catalog | Telling real gains from noise, Comparing on the same examples, Margins near 0% and 100% |
| 5 | **Register** and promote | `05_register.ipynb`: the local MLflow registry; aliases `champion` and `challenger`; the gate that moves the alias | The Unity Catalog model registry (`catalog.schema.model`) with grants; CI runs the eval and moves the alias: trunk-based, no copies per environment | Ship a change, Canary releases |
| 6 | **Serve** | `06_serve.ipynb`: the drill server loads the model by its alias; the coach retrieves with it | The model logged with `mlflow.sentence_transformers`, registered in Unity Catalog, served on a Model Serving endpoint (scale-to-zero off); AI Search (formerly Vector Search) uses that endpoint as the index's embedding model | Ship a change, Stop it fast |
| 7 | **Monitor** | `07_monitor.ipynb`: log which lesson retrieval picked for each coach question; watch Still stuck by lesson; drift | Inference tables, the `drill_insights` views and Genie | Drift monitoring, Prove nothing drifted |
| 8 | **Push to Databricks** | | `08_databricks/`: one notebook per stage above, run in the workspace with the bundle's `personal` target | Platform track: the AI gateway (P9–P11) |
| 9 | **Lifecycle** | `09_lifecycle.ipynb` and `DECISION.md`: when to re-embed (new lesson text), when to retrain (new ways of asking), when to retire | A scheduled job re-embeds; retraining stays a decision | Prove nothing drifted, Databricks Runtime versions |

Stages 0–2 exist. The rest are written as you reach them, so each one can use what the last one found.

## How every comparison is run: champion against challenger

Every model is tried the same way, so the lab is one long experiment with an A/B test at the end:

- **The champion** is what runs today. For the retrieval step that is `bge-large` as its makers ship it,
  with its search prompt. On Databricks the very same model is a pay-per-token endpoint,
  `databricks-bge-large-en`, with no upkeep at all, which is part of why the bar for a custom model is high. For the coach as a whole it is today's coach, which does not retrieve at all:
  the page tells it which lesson the learner is on. So the fine-tune has to earn a place where the
  lesson is *not* known: a question typed on the study list, to the blueprint's coach, or through
  Claude's tools without a lesson. Stage 0 says this plainly and stage 6 wires it in there.
- **A challenger** is anything new: a fine-tuned model, a different base model, a different prompt.
- **Offline first (stages 2 and 4).** Champion and challenger answer the *same* questions, so they are
  compared pair by pair: the questions only one of them found, and McNemar's test on those (the course's
  "Comparing on the same examples" and "Telling real gains from noise"). Every run logs **quality** (hit@1, recall@5, MRR, the weakest module), **speed**
  (milliseconds per question, seconds to embed the course) and **cost** (model size and memory now; DBU
  and token prices once it runs on Databricks), so the trade-off is read from one table, the way the cost, speed and quality experiment
  (`notebooks/learning/cost_speed_quality.ipynb`) reads its own.
- **Online second (stage 7).** Once served, real questions are split between champion and challenger,
  and the measure is what learners do next: Got it against Still stuck, and whether the next Check
  question goes right. That is the A/B test proper, and it needs real traffic, which the work copy has
  and this computer does not yet (no typed questions recorded here as of 2026-11-08).
- **Promotion (stage 5)** moves the `champion` alias only when the offline gate passes with a reason
  written down, never on a round number.

**What Databricks' own guidance says.** Its AI Search retrieval quality guide puts fine-tuning the
embedding model *last*: first fix chunking, the query prompt and hybrid search, then check whether a much
stronger embedding model beats the free one by a wide margin. If it does not, the embedding model is not
the problem and fine-tuning will not help. Stage 2 runs that diagnosis with the models on this computer,
and stage 8 adds `databricks-gte-large-en` and an external model as the ceiling check. If the lab stops
there with "not worth it", that is a finding, written in `DECISION.md`, as it was for the Steam lab.

## Where things are

- `retrieval.py`: the lab's own code (pairs, splits, measures, baselines), kept out of the notebooks so
  the cells stay short. It reuses the app's `drill.embedding_compare` (the Ollama embeddings, the
  paired test) and `drill.tutor_prepared_eval` (Wilson intervals, McNemar).
- `tracking.py`: the MLflow side (connect, the computer, datasets, logging as you train).
- `data/`: git-ignored; the frozen pairs and splits are written here **and** registered in MLflow, which
  is the copy that counts.
- `*_answers.py`: the filled-in answers to each notebook's exercises; `DRILL_FILL_ANSWERS=1` makes a
  notebook use them, for checking it runs end to end.
- MLflow experiment: `coach-retrieval-lab` on the local server (`http://localhost:5050`). One run per
  thing tried, with a readable name and a full description.

## Running it

```bash
# once: the lab's own environment (sentence-transformers and torch; the app does not need them)
uv sync --project notebooks/learning/coach_retrieval

# the local MLflow server must be up (it is, on this computer: port 5050), and Ollama for the baselines
uv run --project notebooks/learning/coach_retrieval jupyter lab notebooks/learning/coach_retrieval

# check a notebook runs end to end with the answers filled in (what a reviewer does; not CI)
DRILL_FILL_ANSWERS=1 uv run --project notebooks/learning/coach_retrieval \
  jupyter nbconvert --to notebook --execute --inplace notebooks/learning/coach_retrieval/01_pairs.ipynb
```

The notebooks run in order from a clean checkout. `data/` is git-ignored, so the first notebook to need the
lesson split deals it: `00_vet.ipynb` calls the same `freeze_splits` that stage 1 explains, and stage 1
then finds the file already there and unchanged. Any content change (a lesson added, removed or renamed)
changes the deal, so it needs a redeal on purpose (`force=True`), logged, and every score before it stops
being comparable.

The Databricks stages cost money and need a CLI profile you choose. Nothing in stages 0–7 leaves
this computer.

## The numbers behind the data (2026-11-08)

211 lessons in 28 modules. 741 Learn paragraphs (the haystack). 211 Check questions and 416 more
practice questions (627 in all), plus the coach's prepared question chips (1,050 once shared chips are
dropped): 1,677 pairs. Real learner questions, typed to the coach, arrive as `asked` events and join the
honest test as they come.
