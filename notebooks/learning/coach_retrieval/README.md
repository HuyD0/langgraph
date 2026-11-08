# The coach-retrieval lab: fine-tune an embedding model, start to finish

*Learning material. Nothing here runs in CI. Run it by hand, locally first, then push the same
stages to Azure Databricks.*

## What we are building, and why

When a learner asks the coach a question on a lesson page, the page tells the coach which lesson it is,
so today the coach has nothing to find. Where no lesson is known (a follow-up on the study list, the
blueprint's coach, or Claude's tools, which reach the app over MCP: see the glossary) the coach would
first have to **find the lesson paragraphs that answer it** (retrieval) with an **embedding model**: a model that turns text into a list of numbers so that texts
with similar meaning land close together. The champion for that step is `bge-large` straight from its
makers, scored at recall@5 0.84 on the course's own Check questions (`drill experiment embeddings`,
PR #170); it is not wired into the coach yet (stage 6). This lab's **recall@5** counts a question as found
when its lesson has any paragraph in the top five; with one right lesson per question, that is the **hit
rate at 5** (the course's lesson *Measuring retrieval* explains both).

This lab **fine-tunes that embedding model on the course**, so that a learner's question in their own
words finds the right lesson more often. It is small enough to run on your computer in minutes, its
score is a plain yes-or-no ("did the right lesson come up?"), and the result plugs straight into the
coach. That makes it the right first proof of concept for the whole AI/ML operations lifecycle (the
real terms: MLOps and LLMOps, in the glossary): every stage below is one you would run for any model, at
work, on Azure Databricks.

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
| 3 | **Train** | `03_train.ipynb`: one step by hand; the loss; hard negatives; learning rate; seeds; checkpoints; every run logged | A GPU job (`databricks air run`) with this same code, logging to the workspace's MLflow. Databricks' managed fine-tuning product never covered embedding models and has reached end of life, so bring your own training code | Train, validation and test data, Retrieval: finding the right chunks, What an embedding is: meaning as a place, Dev, test and holdout sets, Telling real gains from noise, Margins near 0% and 100%, The cost of embeddings, Comparing on the same examples, Embedding models have blind spots (no lesson yet on learning rates or overfitting: the glossary's "Training a model" group has the words, and the lessons are proposed below); the Steam lab's training notebook (one step by hand, checkpoints) |
| 4 | **Evaluate** | `04_evaluate.ipynb`: hit@1 (the closest paragraph is from the right lesson; glossary: hit@1) and recall@5 against the champion on the test lessons; Wilson intervals; a paired test (McNemar's test, from the lesson *Comparing on the same examples*); the forgetting check | Same code; the eval dataset lives in Unity Catalog | Telling real gains from noise, Comparing on the same examples, Margins near 0% and 100% |
| 5 | **Register** and promote | `05_register.ipynb`: the local MLflow registry; aliases `champion` and `challenger`; the gate that moves the alias | The Unity Catalog model registry (`catalog.schema.model`) with grants; CI runs the eval and moves the alias: trunk-based, no copies per environment | Ship a change, Canary releases |
| 6 | **Serve** | `06_serve.ipynb`: the drill server loads the model by its alias; the coach retrieves with it | The model logged with `mlflow.sentence_transformers`, registered in Unity Catalog, served on a Model Serving endpoint (scale-to-zero off); AI Search (formerly Vector Search) uses that endpoint as the index's embedding model | Ship a change, Stop it fast |
| 7 | **Monitor** | `07_monitor.ipynb`: log which lesson retrieval picked for each coach question; watch Still stuck by lesson; drift | Inference tables, the `drill_insights` views and Genie | Drift monitoring, Prove nothing drifted |
| 8 | **Push to Databricks** | | `08_databricks/`: one notebook per stage above, run in the workspace with the bundle's `personal` target | Platform track: the AI gateway (P9–P11) |
| 9 | **Lifecycle** | `09_lifecycle.ipynb` and `DECISION.md`: when to re-embed (new lesson text), when to retrain (new ways of asking), when to retire | A scheduled job re-embeds; retraining stays a decision | Prove nothing drifted, Databricks Runtime versions |

Stages 0–3 exist. The rest are written as you reach them, so each one can use what the last one found.

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
embedding model *last*: first fix chunking (the lesson *Chunking documents*), the query prompt and hybrid search, then check whether a much
stronger embedding model beats the free one by a wide margin. If it does not, the embedding model is not
the problem and fine-tuning will not help. Stage 2 runs that diagnosis with the models on this computer,
and stage 8 adds `databricks-gte-large-en` and an external model as the ceiling check: a much stronger model as
the ceiling, the same idea as an oracle test (glossary: oracle test). If the lab stops
there with "not worth it", that is a finding, written in `DECISION.md`, as it was for the Steam lab.

## Every term, and where it is taught

Every term or method below is explained in plain words where the lab first uses it, and the right-hand
column names the course lesson (in *italics*) or the glossary entry that teaches it. The rows are grouped
by topic: search, measures, statistics, data and splits, training, then MLflow and Databricks.

| Term | Where the lab first uses it | Where the course teaches it |
|---|---|---|
| Retrieval | README, "What we are building" | *Retrieval: finding the right chunks*; Glossary: retrieval |
| Embedding, embedding model, vector | README, "What we are building" | *What an embedding is: meaning as a place*; Glossary: embedding, embedding model |
| Cosine similarity | `01_pairs.ipynb` §3, the near-duplicate check | *What an embedding is: meaning as a place*; Glossary: cosine similarity |
| Normalising a vector to length 1; dot product | `02_baselines.ipynb` §4 | *What an embedding is: meaning as a place*; Glossary: cosine similarity |
| Exact (brute-force) search, and why no vector index | `vetting/assessment.md`, Scale | *Finding neighbours fast*; Glossary: exact nearest-neighbour search |
| Corpus (the haystack) | `01_pairs.ipynb` §1 | Glossary: corpus |
| Chunk, chunking (here one chunk is one Learn paragraph) | README, "What Databricks' own guidance says" | *Chunking documents*; Glossary: chunk, chunk size and overlap |
| Search prompt (query instruction) | README, "How every comparison is run" | *Retrieval: finding the right chunks*; Glossary: query instruction (search prompt) |
| Dimensions (vector size, "768") | `02_baselines.ipynb` §1 | *How big should a vector be?*; Glossary: dimensions (vector size) |
| TF-IDF (the word-count table) | `00_vet.ipynb` §2 | *Hybrid search and rank fusion*; Glossary: TF-IDF |
| Word overlap; stop words | `00_vet.ipynb` §2 | Glossary: stop words |
| Hybrid search; AI Search; vector index | README, stage 6 and "What Databricks' own guidance says" | *Hybrid search and rank fusion*, *Databricks AI Search: endpoints, indexes and sync*; Glossary: hybrid search, Databricks AI Search |
| recall@5 (in this lab, the hit rate at 5) | README, "What we are building" | *Measuring retrieval*; Glossary: Recall@k |
| hit@1 | README, stage 4 | *Measuring retrieval*; Glossary: hit@1 |
| MRR (mean reciprocal rank) | README, "How every comparison is run" | *Measuring retrieval*, *Ranking quality: nDCG*; Glossary: MRR (mean reciprocal rank) |
| Rank; top k | `02_baselines.ipynb` Exercise 1 | *Retrieval: finding the right chunks*; Glossary: k (top k) |
| Weakest module; report each group | README, "How every comparison is run" | *Embedding models have blind spots*, *Report each group, weighted by real traffic* |
| Latency; the median and spread of timing passes | README, "How every comparison is run"; `02_baselines.ipynb` §5 | *Latency that users feel*; Glossary: latency, median |
| Seconds to embed the course | README, "How every comparison is run" | *The cost of embeddings* |
| Wilson interval; confidence interval (about 95 times in 100) | `00_vet.ipynb` §2 | *Margins near 0% and 100%*, *How many examples do you need?*; Glossary: Wilson interval, confidence interval |
| Bootstrap range (paired); sampling with replacement; point estimate | `00_vet.ipynb` §2 | *How many examples do you need?*; Glossary: bootstrap, confidence interval |
| Paired comparison | README, "How every comparison is run" | *Comparing on the same examples*; Glossary: paired comparison, discordant pairs |
| McNemar's test; about twice the square root of the disagreements | README, stage 4 | *Comparing on the same examples*; Glossary: McNemar's test |
| p-value | `00_vet.ipynb` §2 | *Comparing on the same examples*; Glossary: p-value |
| The 0.05 line, and its reason | `02_baselines.ipynb` §4; its reason in §7 | *Testing many variants* |
| Multiple comparisons; the chance of at least one fluke (the family-wise error rate) | `02_baselines.ipynb` §4 | *Testing many variants*; Glossary: multiple comparisons problem |
| Bonferroni correction | `02_baselines.ipynb` §4 | *Testing many variants*; Glossary: Bonferroni correction |
| Pre-registration | `02_baselines.ipynb` §4 | Glossary: pre-registration |
| "Not shown" is not "no difference" | `02_baselines.ipynb` §4 | *Telling real gains from noise*, *Enough to notice a difference* |
| Statistical power | `00_vet.ipynb` §7 | *Enough to notice a difference*; Glossary: statistical power |
| Both tests must agree | `02_baselines.ipynb` §7 | *Comparing on the same examples*, *One decision from many outcomes* |
| Seed; seed-to-seed variation | `00_vet.ipynb` §2; seed-to-seed variation in `03_train.ipynb` §5 | *Telling real gains from noise*; Glossary: seed, seed-to-seed variation |
| Selection bias (the winner's curse): picking on dev makes dev optimistic | `03_train.ipynb`, intro and §4 | *Testing many variants*; Glossary: selection bias (winner's curse) |
| Headroom | `02_baselines.ipynb` §7 | *Oracle tests: find the step worth fixing*; Glossary: headroom |
| Ceiling check (a much stronger model as the ceiling) | README, "What Databricks' own guidance says" | *Oracle tests: find the step worth fixing*, *Checking your LLM judge*; Glossary: oracle test |
| Pair; measure the population first | `01_pairs.ipynb` §1 | *Dev, test and holdout sets*, *How many examples do you need?* |
| Stratified split | README, stage 1 | *Dev, test and holdout sets*, *A smoke set for fast iteration*; Glossary: stratify |
| Train, dev, test and holdout (60/20/10/10) | README, stage 1 | *Train, validation and test data*, *Dev, test and holdout sets*; Glossary: dev, test and holdout sets |
| Split by whole lesson; leakage; the near-duplicate line at 0.9 | README, stage 1; `01_pairs.ipynb` §2 and §3 | *Train, validation and test data*, *Dev, test and holdout sets*, *Splits that don't move*; Glossary: leakage |
| Frozen split; a re-deal on purpose (`force=True`) | README, stage 1 and "Running it" | *Splits that don't move* |
| Hash order (sha256) | `01_pairs.ipynb` §2 | *Splits that don't move*; Glossary: hash split |
| The holdout lock | `01_pairs.ipynb` §2 | *Dev, test and holdout sets*, *Testing many variants* |
| Honest test and easy test (the lab's own names) | `00_vet.ipynb` §2; named as such in `01_pairs.ipynb` §4 | *Embedding models have blind spots* |
| Model-made labels, and a person's reading | `00_vet.ipynb` §2; `01_pairs.ipynb` §4 | *Drafted labels, expert-confirmed*; Glossary: drafted label |
| Temperature; one seed per rewrite | `01_pairs.ipynb` §4 | *How an LLM works, in plain words*; Glossary: temperature |
| Caching model outputs | `01_pairs.ipynb` §4 | *Caching responses*; Glossary: cache |
| Synthetic training data | `03_train.ipynb` §1 | *Embedding models have blind spots*; Glossary: synthetic training data |
| MLflow dataset and its digest; the content fingerprint | README, stage 1; `00_vet.ipynb` §4 (the card) | Glossary: MLflow dataset (and digest); the fingerprint is the lab's own, explained in `00_vet.ipynb` and `03_train.ipynb` §0 |
| Fine-tuning | README, "What we are building" | *Designing a RAG experiment*; Glossary: fine-tuning |
| Weights (parameters); base model | `01_pairs.ipynb` §4 ("14 billion learned numbers") | Glossary: weights (parameters), base model |
| Contrastive learning; anchor, positive, hard negative; in-batch negatives | README, "How the fine-tuning works" | Glossary: contrastive learning, hard negative, in-batch negatives |
| False negative (in training) | `03_train.ipynb` §1 | Glossary: false negative (in training) |
| Training step, batch, epoch | README, "How the fine-tuning works" | Glossary: training step, batch (in training), epoch |
| Loss; softmax and cross-entropy | README, stage 3; `03_train.ipynb` §2 | Glossary: loss (in training) |
| Gradient; learning rate; "2e-5" | `03_train.ipynb` §2 | Glossary: gradient, learning rate |
| Optimiser (AdamW); warm-up | `03_train.ipynb` §2 and §4 | Glossary: optimiser, warm-up |
| Checkpoint; the best checkpoint | README, stage 3 | Glossary: checkpoint (in training) |
| Overfitting; train loss against a held-out score | `03_train.ipynb` §3 | *Train, validation and test data*; Glossary: overfitting |
| Dropout; evaluation mode | `03_train.ipynb` §5 | Glossary: dropout |
| Hyperparameter; sweep | `03_train.ipynb` §4 | *Planning what to vary*; Glossary: hyperparameter |
| LoRA (adapter) | `03_train.ipynb` §6 | Glossary: LoRA (adapter) |
| Gradient checkpointing; forward and backward pass | `03_train.ipynb`, intro and §0 | Glossary: gradient checkpointing |
| Precision (fp32, half precision) | `02_baselines.ipynb` §5; explained in `03_train.ipynb` §0 | *Finding neighbours fast*; Glossary: precision (fp32, half precision) |
| GPU; training memory | README, stage 3; `03_train.ipynb` §0 | *Which compute for which work*; Glossary: GPU |
| Catastrophic forgetting; the forgetting check | README, stage 4 | *Reading regressions and improvements*; Glossary: catastrophic forgetting |
| Token (a word piece) and token (an access key) | README, "How every comparison is run" (token prices); `03_train.ipynb`, intro | *How an LLM works, in plain words*, *Short-lived tokens, not PATs*; Glossary: token |
| Ollama; Hugging Face; sentence-transformers | README, "Where things are" and "Running it"; Hugging Face in `02_baselines.ipynb`, intro | Glossary: Ollama, Hugging Face, sentence-transformers |
| Environment variable (`DRILL_FILL_ANSWERS=1`) | README, "Where things are" | Glossary: environment variable |
| MLflow; the local tracking server | README, the lifecycle | *Experiments, runs and the lifecycle*; Glossary: MLflow |
| Experiment, run, description | README, "How every comparison is run" | *Experiments, runs and the lifecycle*; Glossary: experiment (MLflow), run (MLflow) |
| Params, metrics, tags, artifacts | `00_vet.ipynb`, first code cell | *Experiments, runs and the lifecycle*; Glossary: tag (MLflow) |
| Parent and child runs | `00_vet.ipynb` §2 (the smoke run) | Glossary: nested runs (parent and child) |
| Smoke run (smoke test) | `00_vet.ipynb`, intro and §2 | Glossary: smoke test (a different job from *A smoke set for fast iteration*) |
| Baseline; eval run | README, stage 2; `02_baselines.ipynb`, intro | *Experiments, runs and the lifecycle*; Glossary: baseline |
| Champion and challenger | README, "What we are building" and "How every comparison is run" | *Model registry and promotion*; Glossary: champion and challenger |
| Offline evaluation; A/B test | README, "How every comparison is run" | *Testing with real users (A/B tests)*; Glossary: offline evaluation, A/B test |
| Logged model; signature; input example | README, stage 6; `03_train.ipynb` §5 | Glossary: logged model |
| Model registry; alias; rollback | README, stage 5 | *Model registry and promotion*; Glossary: model registry, alias |
| Unity Catalog model registry and grants | README, stage 5 | *Model registry and promotion*; Glossary: Unity Catalog |
| Serving endpoint; pay-per-token | README, stage 6 and "How every comparison is run" | *Pay-per-token or provisioned throughput?*, *Canary releases*; Glossary: serving endpoint |
| Scale to zero | README, stage 6 | Glossary: scale to zero |
| DBU; token prices | README, stage 0 | *Which compute for which work*, *The cost of embeddings*; Glossary: DBU (Databricks Unit) |
| Inference tables | README, stage 7 | *What the records miss*; Glossary: inference table |
| Drift | README, stage 7 | *Drift monitoring*, *Prove nothing drifted*; Glossary: data drift |
| Delta table; Unity Catalog; time travel (reading old versions) | README, stage 1 | Glossary: Delta table, Unity Catalog |
| CI eval gate; trunk-based development; canary releases | README, stage 5 | *Ship a change*, *Canary releases*; Glossary: release gate, trunk-based development, canary release |
| Genie and the `drill_insights` views | README, stage 7 | *Genie: questions about your data in plain words*; Glossary: Genie Agent |
| Databricks Runtime; bundle target | README, stages 8 and 9 | *Databricks Runtime versions*; Glossary: Databricks Runtime (DBR), bundle target |
| MLOps and LLMOps | README, "What we are building" | Glossary: MLOps and LLMOps |
| MCP (Claude's tools) | README, "What we are building" | *Managed MCP servers: tools agents can call*; Glossary: MCP (Model Context Protocol) |
| Proof of concept | README, "What we are building" | Glossary: proof of concept (POC) |
| Use case, the three gates, the value-by-doable map, the card, augment | `00_vet.ipynb` §1 to §4 | *Is this a good AI use case?*, *Write the use case down*; Glossary: use case card, automate or augment |
| Requirements, Well-Architected review, total cost of ownership, fit for purpose, must-pass set | `00_vet.ipynb` §5 to §7 | *Functional and non-functional requirements*, *A well-architected review*, *Total cost of ownership*, *Is it fit for purpose?*, *A must-pass set* |
| Pay-per-token against billed by the hour | README, stage 6 and "How every comparison is run"; `00_vet.ipynb` §6 | *Pay-per-token or provisioned throughput?* |
| Open-source licence (MIT) | `vetting/assessment.md` | Glossary: open-source licence |
| Lab-only words: option chips, ambiguous questions, step 0 equals the champion, the candidate tag, served and local copies agree, guess then reveal, exercises with blanks | `00_vet.ipynb` to `03_train.ipynb` | Not course terms: each is explained in the notebook where it is first used |

**Lessons proposed, not yet written.** Until they exist, the glossary entries above and the notebooks' own
"In plain words" boxes carry these ideas:

- *Fine-tune an embedding model, or not?* (Build phase, after *Embedding models have blind spots*): the order to try fixes, training pairs, hard negatives, in-batch negatives, synthetic questions from train data only, and when to re-embed or retrain.
- *One training step by hand* (Build phase or Foundations): weights, a batch, the loss, the gradient, the learning rate, the optimiser and warm-up, steps and epochs, on a three-row example.
- *Overfitting and the dev curve* (Evaluate phase): training loss against a held-out score, checkpoints, why the best-checkpoint pick is optimistic, seed-to-seed variation, and resuming a stopped run.
- *LoRA and adapters* (Ship or Pricing): one frozen base model with small add-ons, a 6 MB adapter against a 1.3 GB copy, and serving several fine-tunes on Databricks.
- *Serve your own model on Databricks* (Ship phase): log it with a flavour and signature, register it with an alias, a custom endpoint with scale to zero against pay-per-token, inference tables, and an AI Search index that embeds with it.
- *Running models on your own computer* (Build phase): Ollama, model files and gated weights on Hugging Face, the GPU and its memory, 32-bit against 16-bit precision, and why training needs far more memory than the model file.

## Where things are

- `retrieval.py`: the lab's own code (pairs, splits, measures, baselines), kept out of the notebooks so
  the cells stay short. It reuses the app's `drill.embedding_compare` (the Ollama embeddings, the
  paired test) and `drill.tutor_prepared_eval` (Wilson intervals, McNemar).
- `tracking.py`: the MLflow side (connect, the computer, datasets, logging as you train).
- `training.py`: stage 3's training code (training rows with the leakage check, the rewrites of train questions, `train`
  with dev curves, checkpoints and a paired test against step 0, one step by hand, overfit on purpose).
- `outputs/`: git-ignored; checkpoints. Only each run's best keeps its weights (1.3 GB); the rest keep their scores in
  `checkpoint.json` and `trim.json`.
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

# the local MLflow server must be up (it is, on this computer: port 5050), and Ollama for the baselines and for rewriting training questions (stage 3)
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

212 lessons in 28 modules. 744 Learn paragraphs (the haystack). 212 Check questions and 418 more
practice questions (630 in all), plus the coach's prepared question chips (1,050 once shared chips are
dropped): 1,680 pairs. Real learner questions, typed to the coach, arrive as `asked` events and join the
honest test as they come.
