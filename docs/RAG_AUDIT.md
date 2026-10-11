# Auditing a RAG app you can't bring here

Say you have a RAG app at work and a coding agent there that can read its code, but you
can't run Claude on that machine. Then the work agent does the inspecting, and only a
summary with no code or company details comes back here.

1. **Copy the prompt below into your work coding agent**, in the repository of
   your RAG app. It maps the pipeline, checks it against everything in this
   project, and writes a report in two parts: internal findings with file and
   line evidence, which stay at work, and a shareable summary.
2. **Read the shareable summary yourself** before it leaves work. Remove anything
   that identifies your company, its customers or its systems, and check your
   company's policy on sharing even a summary like this.
3. **Paste the summary into a Claude conversation.** Claude can rank the gaps, link
   each one to the lesson or notebook that covers it, fill in an
   [experiment plan](EXPERIMENT_PLAN.md) for the most important one, and write
   follow-up prompts for your work agent.

> This repository is public. Keep the findings from work out of it, even the
> shareable summary.

If your agent struggles with one long prompt, run it in three goes: Part 1;
then Part 2, sections A to D; then sections E to I and Part 3.

## The prompt

```text
You are auditing the retrieval-augmented generation (RAG) application in this
repository, to find gaps against the checklist below.

Read only. Do not edit, create or delete files in the repository, and do not
commit. Do not call production endpoints or paid model APIs, and do not write to
any table, index or database. If running something would help (counting the rows
in a local eval file, running existing unit tests), tell me what and why, and wait
for my go-ahead.

Base every finding on evidence you can point to. If you are guessing, say so. Do
not assume a feature is used just because a library supports it.

PART 1 - MAP THE PIPELINE

For each stage, write what the code actually does, with file:line evidence. If a
stage doesn't exist, write "none found". If you can't tell, write "unclear" and
what you would need to find out.

1. Sources and ingestion: which documents, how they are loaded, how often refreshed.
2. Chunking: method, size, overlap, and the metadata kept with each chunk
   (document id, title, section, last-updated date).
3. Removing duplicate or near-duplicate chunks or documents.
4. Embeddings: which model, and whether queries and documents use the same one.
5. Index: which product (for example Databricks Vector Search, Azure AI Search,
   FAISS, pgvector), and how and when it is rebuilt or synced.
6. Query handling: rewriting, expansion, filters, use of conversation history.
7. Retrieval: keyword, vector or hybrid; how many results (k); how hybrid results
   are merged.
8. Reranking: which model or method, how many candidates in and how many out.
9. Prompt and generation: which model and temperature, how retrieved text is put
   into the prompt, any instruction to answer only from that text, what it says
   when it can't answer, and whether it cites sources.
10. After generation: any checks on the answer (groundedness, citations, safety,
    personal data), and what happens when a check fails.
11. Tracing and logging: which tool (for example MLflow), and what is recorded per
    request: retrieved document ids and scores, prompt, answer, latency, tokens,
    version tags.
12. Evaluation: eval sets, scorers, LLM judges, scripts, notebooks, CI jobs.
13. Release and monitoring: how a change reaches production, any gates, dashboards
    or alerts.

PART 2 - CHECK FOR GAPS

For every item give: Status (Yes / Partly / No / Can't tell); Evidence (file:line,
or what you searched for and didn't find); Risk if missing (one sentence about
this app).

A. Ingestion and index
A1. Chunk size and overlap were chosen by comparing settings on an eval, not left
    at a default. Look for experiments, notebooks or comments comparing settings.
A2. Near-duplicate chunks are removed, so copies can't crowd out the top results.
A3. Every chunk keeps a stable document id and title, so retrieval can be scored
    against the expected document.
A4. When documents are added or changed, the index is rebuilt or synced
    automatically, and something would notice if it wasn't. A stale index makes
    new content unfindable while the app looks healthy.
A5. Retrieved text is treated as untrusted: instructions written inside a
    document can't override the system prompt (indirect prompt injection).

B. Retrieval and reranking
B1. Retrieval is measured on its own, separately from answer quality: recall@k
    (is the right document in the top k), and nDCG if relevance is graded.
B2. k and similar settings were chosen by experiment.
B3. Keyword and vector search are combined (hybrid, for example reciprocal rank
    fusion), or there is evidence that one alone is enough. Exact terms such as
    product codes, error codes and names are where vector-only search fails.
B4. If there is a reranker or a query rewriter: it was compared against not having
    it (an ablation), and its effect was checked question by question, not only on
    average. A step can help most questions and break a critical one.
B5. Questions whose right document never reaches the candidate list can be found.
    No reranker can fix those.

C. Generation
C1. The prompt says to answer only from the provided text, and gives exact
    wording for "I don't know".
C2. Declining is measured both ways: unanswerable questions are in the eval set
    and get declined, and answerable questions don't get declined.
C3. Answers cite sources per statement, and every citation points to a document
    that was actually retrieved.
C4. Model version and temperature are pinned, and recorded with each request.

D. Checks before the user sees the answer
D1. A groundedness or claim check (is each statement supported by its cited
    passage). If there is one: what happens to unsupported or contradicted
    statements (release, revise or decline), and has the checker itself been
    compared against human labels?
D2. A separate relevance check. A statement can match its source and still not
    answer the question.
D3. Handling of personal data, secrets and unsafe output, as the domain requires.

E. Tracing
E1. Every request is traced with typed steps (retrieval, reranking, model calls),
    and the trace records which document ids went to the answer step.
E2. Every trace is tagged with the app version or configuration, so two versions
    can be compared request by request.
E3. Latency and token cost are recorded per request and per step.
E4. User feedback and expert labels are attached to traces (in MLflow:
    assessments, with feedback for grades and expectations for expected answers).

F. The eval set
F1. An eval set exists. Give its approximate size, where it lives and how it is
    versioned.
F2. Its questions come from real traffic (production traces), not only synthetic
    ones, and its mix of topics roughly matches real traffic.
F3. Each question has an expected answer (or expected facts) and the expected
    document id(s). Say who wrote them: domain experts, or an LLM with experts
    confirming.
F4. It includes unanswerable questions, and questions on rare but important topics.
F5. It is split into dev (for tuning), test, and holdout (looked at once, at the
    end). Questions from one user, conversation or document stay in one split, and
    a question's split doesn't change when the set grows (for example, assigned
    from a hash of an id).
F6. There is a must-pass set: a short list of critical questions that must never
    get worse.
F7. Labels used to tune an LLM judge are kept apart from labels used to test it.

G. Scoring
G1. Deterministic checks are used where possible, LLM judges where needed, and
    retrieval and answer scores are reported separately.
G2. Every LLM judge has been compared against human labels (agreement rate,
    Cohen's kappa), and is re-checked when its prompt or model changes.
G3. There is a way to catch scorer mistakes, such as expected answers so strict
    that correct answers are marked wrong.

H. Comparing versions and deciding
H1. A written plan exists before a comparison: the question, the metric,
    guardrails such as latency and cost, and the rule for deciding.
H2. Versions are compared on the same questions, question by question
    (regressions, improvements, a paired test such as McNemar's), not only by
    average score.
H3. Each version runs more than once, or questions that give different results
    across identical runs are identified and set aside.
H4. Results are reported per topic, with a range (confidence interval), not only
    as one overall number.
H5. Regressions are read and labelled with a cause before a decision is made.
H6. An oracle test exists, or could be run: give the model the right document
    directly, to measure how much better retrieval could make the answers.
H7. When many variants are tried, the winner is confirmed on data that wasn't used
    to choose it (the holdout).

I. Release and monitoring
I1. The must-pass set, or the eval, runs automatically before release and blocks
    it on a regression.
I2. New versions are rolled out gradually (a canary), or checked in an equivalent
    way.
I3. Production signals are watched per topic: decline rate, latency, cost, user
    feedback, and how fresh the index is.
I4. A sample of production traffic is labelled regularly, and new failures are
    added to the eval set.

If this runs on Databricks, also check: the Vector Search index's sync mode
(triggered or continuous) and what triggers it; whether hybrid queries or
reranking are used; eval datasets in Unity Catalog (mlflow.genai.datasets);
labelling sessions or the Review App; mlflow.genai.evaluate runs and their
scorers; inference tables or production monitoring.

PART 3 - WRITE THE REPORT

Write two sections.

Section 1, "Internal findings": the Part 1 map and the Part 2 checklist, with
file:line evidence. This stays inside the company.

Section 2, "Shareable summary": the same findings, rewritten so they are safe to
share outside the company. It must contain no source code; no file paths; no
names of repositories, tables, indexes, endpoints, internal products or teams; no
hostnames or URLs; no document text, user questions or customer data; no secrets;
and no business numbers. Use generic descriptions, such as "a vector index
synced by a nightly job" or "an eval set of about 200 questions in a table".
It must contain:
1. One paragraph describing the pipeline stage by stage, in generic terms.
2. The checklist as a table: ID, status, and one line of explanation.
3. The five biggest risks, most serious first, each with why it matters here.
4. Questions you couldn't answer from the code that someone on the team would
   know.
```

## Where each check comes from

| Section | Daily Drill lessons | Notebooks |
|---|---|---|
| A. Ingestion and index | Chunking documents; Cleaning the index; Prompt injection | 9d (the stale index) |
| B. Retrieval and reranking | Measuring retrieval; Ranking quality: nDCG; Hybrid search and rank fusion; Did the reranker help?; Ablations; Designing a RAG experiment | 9c |
| C. Generation | Knowing when not to answer | 9a, 9c |
| D. Checks before release | Checking each claim before release; Personal data; Never trust model output | |
| E. Tracing | Designing traces for experiments; Tokens and cost | 9b |
| F. The eval set | Dev, test and holdout sets; Splits that don't move; Report each group, weighted by real traffic; A must-pass set; Drafted labels, expert-confirmed | 9a |
| G. Scoring | Evaluating model answers; Checking your LLM judge; Agreement beyond chance | 8 |
| H. Comparing and deciding | Write the plan before the runs; Comparing on the same examples; Margins near 0% and 100%; Reading regressions and improvements; Oracle tests; Testing many variants | 8, 9c |
| I. Release and monitoring | A must-pass set; Canary releases; Drift monitoring | 9d |
