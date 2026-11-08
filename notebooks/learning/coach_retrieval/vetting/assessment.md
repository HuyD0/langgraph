# Use case assessment: Help the Daily Drill coach find the right lesson for a question typed in a learner's own words, when the page has not told it the lesson, so the share of those questions whose lesson is among the five paragraphs retrieved (recall@5) improves.

**Corner:** incubate (value low, doable high)
**Gates:** 2 passed, 1 open: "a fixed rule could do it" is settled by stage 2's word-match baseline  ·  **Mode:** augment

*Vetted 2026-11-08 with the `vet-ai-use-case` skill. The owner is the lab's learner, who also runs Daily Drill. Every
number below was measured on this computer (MLflow experiment `coach-retrieval-lab`, http://localhost:5050) or read from the
course content; where nothing was measured it says **Unknown** and asks. Each claim says whether it is a finding or a hunch,
and what would make it wrong.*

**Said plainly first.** Today's coach does **not** retrieve with an embedding model at all. The page sends `/api/ask` the
lesson the learner is on (`trace.lesson_id`) and the lesson's own text in the prompt, so the coach never has to find
anything. The champion for *this* step is therefore `bge-large` as its makers ship it, with its search prompt, scored at
recall@5 0.84 on 150 Check questions (`drill experiment embeddings`, PR #170). A fine-tune has to earn a place only where
the lesson is **not** known: a follow-up typed on the study list, the blueprint's coach ("ask your own"), Claude's tools
(`ask_tutor` over MCP, which carries no lesson), and the claude.ai tutor project. On this computer none of those doors
has recorded a typed question yet (0 `asked` events in `.drill/drill.db`). The business value for Daily Drill alone is
modest; the enterprise value is rehearsing the whole model lifecycle (vet, data, baselines, train, evaluate, register,
serve, monitor) on a problem small enough to run in minutes.

## Gaps to close first

- Unknown: How many questions a month arrive with no lesson known (study list, blueprint coach, MCP tools, tutor project), and what share of them does the coach answer badly today? The work copy has learners; this computer has 0 recorded typed questions.
- Unknown: What do real learners type? Every question in the test set is either written from the Learn text (Check and more, 627) or a prepared chip tapped beside a question (1,050), or a model-made paraphrase (3 when this vetting began, more as stages 1 and 2 fill the cache, none yet read by a person). The honest test stands on paraphrases until real `asked` events arrive. **Risk:** the paraphrases are not how learners ask; one of the first three already changed the meaning ("Agent A succeeds 9 times in 10" became "one person makes money 9 out of 10 times").
- Unknown: Which prepared chips count as retrieval questions? Option chips ("Why not 'a timeout'?") name no topic and are only ever tapped beside a question; the champion finds their lesson 0.45 of the time. Leaving them out is the recommendation; the owner decides.
- Unknown: On Databricks, is the champion the pay-per-token `databricks-bge-large-en` endpoint (no upkeep) or a served copy? Its price per million tokens and your region's DBU price (for stage 8's cost sheet).
- Unknown: Who reads the model-made paraphrases before they count, and who owns a custom model's upkeep at work (hours a month)?
- Owner to confirm: recall@5 on the lesson's Learn paragraphs is the success number, with hit@1 reported beside it (the coach reads five paragraphs; the learner sees none).

## 1. Problem

When the lesson is known, the coach has nothing to find. Where it is not, the coach today answers from the curriculum map
and whatever the learner typed, with no lesson text in front of it; how often that misses is **Unknown** (no typed questions
recorded here). What *is* measured: on the 328 dev-split questions, the shipped `bge-large` puts the right lesson in its top
five 0.63 of the time (Wilson 95% range 0.58 to 0.68), and that average hides two very different groups:

| Question group (dev split) | Found in top 5 | 95% range | n |
|---|---|---|---|
| Check questions (written from the Learn text) | 0.88 | 0.75 to 0.95 | 42 |
| More practice questions (same) | 0.84 | 0.75 to 0.90 | 82 |
| Prepared chips, "what does X mean here?" (term) | 0.81 | 0.62 to 0.91 | 26 |
| Prepared chips, "why not <wrong answer>?" (option) | 0.45 | 0.38 to 0.53 | 174 |

(Run "smoke · retrieval.py · dev by question source", child "bge-large · all dev · 328 questions". A finding, not a hunch: it
was a hunch when the 20-question smoke sample scored 0.50, and checking all 328 confirmed it. It is wrong if learners turn out
to type option-chip-shaped questions, but today nobody types them: they are tapped.)

The easy questions reproduce PR #170's 0.84. The problem the fine-tune would solve is the **hard** question: a learner's own
words, which share fewer words with the lesson. How much worse the champion is on those is the first number stage 2 produces.

## 2. One line

Help the Daily Drill coach find the right lesson for a question typed in a learner's own words, when the page has not told
it the lesson, so recall@5 on learner-worded questions improves (today's number on learner-worded questions: **Unknown**
until stage 2; 0.84 to 0.88 on the easy Check questions).

## 3. Gates

| Gate | Result | Evidence |
|---|---|---|
| A fixed rule could do it | **Open** | A word-count table (TF-IDF, the "fixed rule": no learning from pairs, no GPU, 0.05 ms a question) is the baseline. In the 20-question smoke it found 12 of 20 against the champion's 10, McNemar p 0.5, bootstrap gap -0.25 to 0.00: too few questions to say anything, and exactly the known flaw (Check questions share the lesson's words). Stage 2 scores both on all dev questions and on the learner-worded ones. The fine-tune is only worth building if the champion itself beats the word table there; if the word table wins on learner-worded questions, the gate fails and the lab stops with a finding. |
| No past examples with right answers | **Passed, with a risk** | 1,677 question-to-lesson pairs with a known right lesson (211 Check, 416 more, 1,050 prepared chips), 741 Learn paragraphs as the haystack, split by whole lesson into train 123 / dev 42 / test 28 / holdout 18 lessons (pairs 970 / 328 / 226 / 153), frozen in `data/splits.json`, all four leakage checks passing. Ten question texts that sit under several lessons were dropped (329 copies; "when does this stop working?" is under 151 lessons). **But none of these is a real typed learner question** (0 `asked` events here). The learner-worded test is model-made paraphrases, `checked: false` until a person reads them. That is an Unknown and the lab's biggest risk. |
| A wrong answer causes harm and nobody checks | **Passed** | Augment. A wrong lesson gives the coach the wrong paragraphs; the learner reads the answer and rates it (Got it / Still stuck), and the rating is an event the app already records. Nothing is graded or decided by the retrieval; the worst case is a confusing answer and a Still stuck, which is also the monitoring signal (stage 7). |

**Mode: augment.** Retrieval drafts the context, the coach drafts the answer, the learner decides whether it helped.

## 4. Map

- **Value: low**, for Daily Drill alone. The main flow has no retrieval problem (the page tells the coach the lesson). The
  doors that need retrieval exist but have 0 recorded typed questions on this computer; their traffic at work is Unknown.
  Hunch: it will stay low until the study list and the tutor project are used daily; wrong if the work copy already shows
  many `asked` events without a lesson.
- **Doable: high.** The data is ready and measured, the score is a plain yes-or-no per question, the champion runs in 5 to
  6 ms a question on this computer and embeds the whole course in about 10 to 16 s, a fine-tune of a 1.3 GB model fits in
  minutes on this computer's GPU, and the owner can change how the coach works (it is their code).
- **Corner: incubate**: a safe way to learn. That matches what the lab is for: the enterprise value is the lifecycle
  rehearsal (the same nine stages, then the same on Azure Databricks), with every stage logged as MLflow runs that can be
  shown at work. To move to **accelerate**, the owner needs recorded questions where the coach missed because it did not
  know the lesson.

## 5. Card

| Field | Answer |
|---|---|
| user | The Daily Drill coach (the AI tutor in the app), on behalf of a learner who typed a question where no lesson is known |
| task | Put the right lesson's Learn paragraphs in front of the coach before it answers |
| decision | For a typed question, which five of the 741 Learn paragraphs are closest in meaning (an embedding model turns each text into numbers; closest means the smallest angle between them) |
| action | The coach answers with those paragraphs as context; the learner reads it and taps Got it or Still stuck |
| today | Where the lesson is known: no retrieval, the page sends the lesson. Where it is not: the coach answers from the curriculum map alone. Cost today: **Unknown** (no typed questions recorded here) |
| success | recall@5: the share of learner-worded questions whose lesson has a paragraph in the five retrieved; hit@1 and MRR reported beside it; the weakest module named |
| wrong_answer | A confusing answer; caught by the learner, recorded as Still stuck. No grade, no decision, nothing irreversible |
| data | 1,677 pairs (question, lesson) from the course content, fingerprint `33910f9634f6`; 741 paragraphs; frozen lesson splits 60/20/10/10 (seed 7); model-made paraphrases of the dev and test Check and more questions as the learner-worded test, each marked `checked: false` until read. Registered as MLflow datasets with digests |
| feedback | `asked` events (question, lesson_id, chip) and Got it / Still stuck ratings already recorded by the app; stage 7 adds which lesson retrieval picked. Real typed questions join the honest test as they arrive |
| owner | The lab's learner, who owns Daily Drill |

Blank: **today** (the cost of the problem); part of **data** (no real typed questions yet).

## 6. Requirements

**Must do:** given a question and no lesson, return the five closest Learn paragraphs with their lesson ids; search the whole
course every time (the haystack is never narrowed by split); log which lesson it picked with every coach answer; load the
model by its registry alias (`champion`), so a rollback is an alias move; never touch the holdout lessons before the final,
once-only score.

**How well:**

| Requirement | Number |
|---|---|
| Speed | Per question, no slower than the champion by more than the champion's own pass-to-pass spread, both measured in the same session on the same questions (median of several passes, same batch size, model load off the clock; stage 2 measured the champion at about 4 to 7 ms a question depending on the set and the pass, and the coach's own answer takes seconds, so retrieval must stay invisible) |
| Uptime | If the model fails to load, the coach answers as it does today, without paragraphs (augment: a worse answer, not an outage) |
| Cost | $0 on this computer (stages 0 to 7). On Databricks: Unknown until stage 8; the comparison is a pay-per-token endpoint with no upkeep |
| Privacy | Questions are the learner's own words and may name their work; they stay on this computer in stages 0 to 7 and go only to the workspace's own endpoints in stage 8. Nothing goes to a public API |
| Security | The model only ranks paragraphs; a typed question cannot make it act. Prompt injection is the coach's problem, already handled by the server's rules (`drill.server.guard`) |
| Scale | 741 paragraphs; a brute-force search over them is a single matrix multiply. The work copy's 109 learners: busiest minute Unknown |
| Audit | Every score is an MLflow run with the data fingerprint, the git commit and this computer's chip and library versions; the model is a registry version with an alias |

## 7. Well-Architected review

| Pillar | Risk | Findings (quoting the card) | Unknowns |
|---|---|---|---|
| Reliability | Low | "If the model fails to load, the coach answers as it does today": the fallback is the current behaviour. The model file is 1.34 GB and loads in about 5 s; a served endpoint on Databricks needs scale-to-zero off or the first question waits. | Who notices when the alias points at a model that will not load? |
| Security | Low | "The model only ranks paragraphs": the worst a hostile question can do is retrieve the wrong lesson. Questions "may name their work", so where traces go matters (local now, the workspace later). | Do the work copy's traces keep the question text, and for how long? |
| Cost Optimization | Medium | "$0 on this computer"; on Databricks the custom model competes with "a pay-per-token endpoint with no upkeep". A served custom model with scale-to-zero off runs about 730 hours a month whatever the traffic; at low traffic that is the biggest item, and it buys a gain measured in a few questions in a hundred. | The DBU price and serving size; how many no-lesson questions a month. |
| Operational Excellence | Low | Every stage is "an MLflow run with the data fingerprint, the git commit" and "the model is a registry version with an alias"; the eval set is frozen and the holdout is locked in code. What is missing is the online signal: "Got it / Still stuck" exists, but nothing yet records which lesson retrieval picked (stage 7). | How many Still stuck ratings a month arrive without a lesson, so stage 7 has something to watch. |
| Performance Efficiency | Low | "5 to 6 ms a question"; "a brute-force search over 741 paragraphs is a single matrix multiply". Embedding the course takes 10 to 16 s and is a one-off per model version or lesson-text change. | The work copy's busiest minute (109 learners). |
| Data and AI governance | Medium | "1,677 pairs ... from the course content" is the owner's own text, so it may be used freely. The base model `BAAI/bge-large-en-v1.5` is MIT-licensed. But "model-made paraphrases ... marked checked: false until read": a test set nobody has read is not yet a test set, and a result on it should not be promoted. | Who reads the paraphrases; whether real questions may be kept as test data (learners' own words about their work). |

A pilot can accept the Cost and Governance gaps because stages 0 to 7 spend nothing and nothing leaves this computer; the
work copy could not, and stage 8 is where both get numbers.

## 8. Total cost of ownership

From `scripts/tco.py` with [`tco_inputs.json`](tco_inputs.json). The script prints only the lines above $0, and today there
are none, so its own table comes out empty (`Total: $0, of which $0 a month to run. Biggest item: none.`). Here is every line
by hand, so nothing looks dropped:

| Item | Over 2 years |
|---|---|
| LLM: answers (the coach's own model, unchanged by this lab) | Unknown (counted as 0) |
| LLM: embeddings (the pay-per-token champion, `databricks-bge-large-en`) | Unknown (counted as 0) |
| Azure AI Search | $0 (not used: the paragraphs are searched in the app or in Databricks AI Search) |
| Databricks AI Search (formerly Vector Search) | Unknown (counted as 0) |
| Databricks jobs: fine-tune, re-embed | Unknown (counted as 0) |
| Databricks serving (a custom model, about 730 hours a month) | Unknown (counted as 0); the line most likely to be the biggest |
| Storage (about 2 GB) | Unknown price (counted as 0) |
| People: reading paraphrases; upkeep of a custom model | Hours, Unknown |
| One-off: the build, the honest test read by a person | $0 in money (the owner's own time) |

**Total: $0**, of which $0 a month to run. Biggest item: none yet.

Every local line is $0 by construction: Ollama, the local MLflow server and a model already in the Hugging Face cache; the
owner's hours are the real cost and are counted in hours. Every Databricks line is **Unknown**, counted as 0 and listed in the
file's `_unknowns` with the question for the owner: the no-lesson question volume, the price of `databricks-bge-large-en`
per million tokens (the champion's cost, $0 upkeep), the DBU price, the GPU job for training, model serving at about 730
hours a month with scale-to-zero off (the line most likely to be the biggest), storage, and the people hours for reading
paraphrases and upkeep. Stage 8 fills them in from the workspace's prices; nothing here is guessed.

## 9. Pilot bars (to agree before the pilot starts)

- **Quality:** on the test lessons' learner-worded questions (the paraphrases of the 84 Check and more questions in the test
  split, read and corrected by a person first), the fine-tune's recall@5 beats the champion `bge-large` with the paired
  bootstrap 95% range of the gap above zero, and McNemar's test on the disagreements agreeing. *Why this bar and not a
  number:* the champion is already at 0.84 to 0.88 on the easy questions, and serving a custom model adds upkeep that a
  pay-per-token endpoint does not have, so a win must be unmistakable on the hard questions, not a point estimate that
  could be luck. *What 84 questions can show:* if the two disagree on about 20, the challenger must win about 15 to 5; a
  real gain of a few points will read as "not shown", which is the honest outcome, not a failure of the test.
- **Must-pass:** (1) on every module in the test split, the fine-tune is not worse than the champion by more than the
  bootstrap noise (the module's paired range for the gap includes zero or sits above it); (2) the forgetting check, stated
  the same way as the win: on the course-worded Check and practice questions (the easy test, the same questions for both
  models), the paired bootstrap 95% range of (fine-tune minus champion) includes zero or sits above it, and McNemar's test
  does not show a champion win. *Why paired, not "inside the champion's Wilson range":* that range only says how uncertain
  the champion's own share is; a fine-tune could sit inside it while losing nine questions the champion found and none the
  other way, which McNemar calls a real loss (p 0.004). A model taught the course's wording must not lose what the makers
  taught it; (3) all four leakage checks pass on the exact data scored; (4) the holdout is scored once, after the model is
  chosen, and that number is reported as the final one whatever it says.
- **Speed:** milliseconds per question no slower than the champion by more than the champion's own pass-to-pass spread,
  both measured in the same session on the same questions: the median of several passes, same batch size, model load off
  the clock (stage 2 measures the champion's spread this way and writes the numbers in its run; a single pass moved from
  4.5 ms on one set to 6.6 ms on another, which is why one number is not enough). *Why:* a difference smaller than the
  pass-to-pass noise cannot be told from the champion; a bigger one is a real slowdown, and for a fine-tune of the same
  weights (the same 1.34 GB) that would mean a mistake in how it is served, not a trade-off worth paying. If the base model
  changes (embeddinggemma), the speed line is re-measured for that base and this reason rewritten.
- **Cost:** $0 on this computer. On Databricks, filled in at stage 8: the custom model's serving line against the
  pay-per-token champion's line at the real no-lesson question volume, with the gain in questions found per month written
  beside it, so the owner can say whether each extra found question is worth its price.
