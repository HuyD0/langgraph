# Experiment design + MLflow spine. Lessons here use the plain-language angle directly: (pattern, text, say, classic).
MODULES = [
 ("foundations", "AI & ML foundations", "How models learn from data, and how you know whether they're any good.",
  ["split_by_key", "precision_recall", "best_threshold"]),
 ("experiments", "Experiment design with MLflow", "Turning \"I think this is better\" into evidence: runs, grids, fair comparisons and decisions you can defend.",
  ["best_run", "param_grid", "cv_folds", "clear_winner"]),
 ("llm-apps", "Building with LLMs", "Calling a model reliably: prompts, parsing replies, batching and retries.",
  ["fill_template", "extract_code_block", "batch_items", "backoff_delays"]),
 ("rag", "Retrieval (RAG) and RAG experiments", "Giving a model the right documents, then measuring which chunking and k actually work.",
  ["chunk_text", "dedupe_chunks", "retrieve", "recall_at_k", "pick_config"]),
 ("agents", "Agents", "Models that call tools in a loop, keeping that loop under control, and scoring it.",
  ["run_agent", "trim_history", "tool_pairs", "agent_scorecard"]),
 ("evals", "Evals", "Measuring whether a change made your AI better or worse.",
  ["exact_match", "first_bad_version"]),
 ("models", "Choosing a model: quality, cost, latency", "Comparing LLMs for a task on the three things that matter, and working out which one pays for itself.",
  ["percentile", "pareto_models", "better_option"]),
 ("tracing", "Tracing and AgentOps", "Designing traces that answer your questions, then using them to find slow steps and runaway agents.",
  ["summarize_by_tag", "slowest_chain", "detect_loop"]),
 ("llmops", "LLMOps", "Running LLM features in production: cost and caching.",
  ["token_cost", "cache_hits"]),
 ("mlops", "MLOps", "Shipping and replacing models safely with a model registry.",
  ["promote_model"]),
 ("platform", "ML platform on Azure Databricks", "The Terraform and Spacelift work behind an ML platform: plans, state, Unity Catalog and networking.",
  ["summarize_plan", "find_replacements", "guard_destroys", "lock_info", "missing_tags", "grants_to_revoke", "count_shift", "overlapping_subnets", "apply_order"]),
]

LIFECYCLE = [
 ("Frame", "Decide the question, the metric and what success is worth.", ["foundations"]),
 ("Design", "Plan the runs: what you vary, what you hold fixed, what it will cost.", ["experiments"]),
 ("Build and trace", "Build the app with tracing and tags from the first line.", ["llm-apps", "rag", "agents"]),
 ("Evaluate", "Score runs on the same eval set and compare quality, cost and latency.", ["evals", "models"]),
 ("Decide and ship", "Pick with a rule you wrote down first, register it, roll out safely.", ["mlops", "platform"]),
 ("Monitor and improve", "Watch real traffic in traces, catch regressions, feed new cases back into evals.", ["tracing", "llmops"]),
]

L = {}
def lesson(id, title, learn, example, check, angle):
    L[id] = dict(title=title, learn=learn, example=example, check=check, angle=angle)

lesson("best_run", "Experiments, runs and the lifecycle",
 ["An **experiment** answers one question, like \"which chunk size gives the best answers under 1.5 seconds?\". Each attempt is a **run** that records its **parameters** (what you set), **metrics** (what you measured) and **artifacts** (files, like the eval results).",
  "MLflow stores all of this so you can compare runs side by side instead of in a spreadsheet. Write the decision rule down before you run anything, for example \"highest quality under $2 per 1,000 requests\". That's what turns an experiment into a decision, and a decision into return on the time spent."],
 ("One run, logged", "import mlflow\nmlflow.set_experiment(\"/Shared/support-bot-rag\")\nwith mlflow.start_run(run_name=\"cs512-k5\"):\n    mlflow.log_params({\"chunk_size\": 512, \"k\": 5, \"model\": \"fast-model\"})\n    mlflow.log_metrics({\"quality\": 0.81, \"cost_per_1k\": 1.8})"),
 ("You ran 12 configs and the best quality costs 3× your budget. What should the experiment have had from the start?",
  ["More configs", "A decision rule that includes the budget", "A bigger model"], 1,
  "With the budget in the rule, the answer is the best run you can afford, not a winner you can't use."),
 ("Best so far, with a constraint", "Skip anything that breaks the rule, keep the best of the rest, and break ties on purpose. One walk through the runs. Maximum Subarray uses the same keep-the-best-so-far bookkeeping.",
  "\"I filter on the constraint first, then keep a running best with an explicit tie-break, in one pass.\"", "max_subarray"))

lesson("param_grid", "Planning what to vary",
 ["A good experiment varies a few things on purpose and holds everything else fixed: the same eval set, the same judge, the same prompt unless the prompt is what you're testing.",
  "Every value you add multiplies the number of runs. 3 chunk sizes × 4 values of k × 2 models is 24 runs, each paying for eval and judge calls. Count the runs, and their cost, before you start."],
 ("A grid, one MLflow run per combination", "for config in grid:\n    with mlflow.start_run(run_name=f\"cs{config['chunk_size']}-k{config['k']}\"):\n        mlflow.log_params(config)\n        mlflow.log_metrics(run_eval(config))"),
 ("You want to test 4 chunk sizes, 5 values of k and 3 models. How many runs is a full grid?",
  ["12", "60", "20"], 1,
  "4 × 5 × 3 = 60. That's why you fix some settings and vary two or three at a time."),
 ("Building combinations", "Start with one empty combination and extend every combination with every value of the next setting. The output grows by multiplication, which is the whole point of the lesson. Interviewers call problems like this \"generate all combinations\".",
  "\"I build the combinations one setting at a time, copying each partial combination before adding a value so they don't share state.\"", None))

lesson("cv_folds", "Experiments for classic ML",
 ["For a classifier (spam, churn, fraud), one train/test split can be lucky or unlucky. **Cross-validation** splits the data into k folds and trains k times, each time testing on a different fold.",
  "You get k scores instead of one: report the average and how much they vary. Compare models on the same folds, and log every model as an MLflow run so the comparison is reproducible."],
 ("scikit-learn with MLflow autologging", "import mlflow\nfrom sklearn.model_selection import cross_val_score\nmlflow.sklearn.autolog()\nwith mlflow.start_run(run_name=\"logreg-5fold\"):\n    scores = cross_val_score(model, X, y, cv=5, scoring=\"f1\")\n    mlflow.log_metrics({\"f1_mean\": scores.mean(), \"f1_min\": scores.min()})"),
 ("Model A scores 0.80 on every fold. Model B scores 0.95, 0.60, 0.90, 0.70, 0.85 (also 0.80 on average). Which is the safer choice?",
  ["A: same average, much more predictable", "B: it reaches 0.95", "They're the same"], 0,
  "Same average, but B swings widely depending on the data it sees. Production data will swing too."),
 ("Dealing round-robin", "Each example goes to fold `i % k`, like dealing cards. One step per example.",
  "\"I assign example i to fold i mod k, so folds differ in size by at most one; with real data I'd shuffle first and keep each customer in a single fold.\"", None))

lesson("clear_winner", "Telling real gains from noise",
 ["LLM outputs and LLM judges vary from run to run. A single comparison of 0.82 against 0.80 may just be luck.",
  "Run each setup several times (3 to 5 is common), and only call a winner when the results clearly separate. If they overlap, choose on cost or speed, or test on more examples."],
 ("Repeat runs as nested MLflow runs", "with mlflow.start_run(run_name=\"prompt_b\"):\n    for seed in [1, 2, 3]:\n        with mlflow.start_run(run_name=f\"seed-{seed}\", nested=True):\n            mlflow.log_metric(\"quality\", evaluate(prompt_b, seed=seed))"),
 ("Prompt A scored 0.80, 0.83, 0.81. Prompt B scored 0.82, 0.84, 0.80. What can you say?",
  ["B is better", "No clear winner: the results overlap", "A is better"], 1,
  "B's worst (0.80) doesn't beat A's best (0.83). Pick on cost, or gather more data."),
 ("Comparing ranges", "Find each list's smallest and largest once, then compare worst against best. A careful rule beats an exciting one.",
  "\"I only call a winner when one setup's worst run beats the other's best; otherwise I treat it as a tie and decide on cost.\"", None))

lesson("recall_at_k", "Measuring retrieval",
 ["A RAG answer can fail in two places: retrieval didn't find the right document, or the model didn't use it well. Measure them separately.",
  "**Recall@k** asks: of the documents that should have been found, how many were in the top k? It needs a small set of questions where you've marked the right documents by hand."],
 ("A recall@5 scorer for mlflow.genai.evaluate", "from mlflow.genai.scorers import scorer\n\n@scorer\ndef recall_at_5(outputs, expectations):\n    found = set(outputs[\"doc_ids\"][:5])\n    wanted = set(expectations[\"relevant_ids\"])\n    return len(found & wanted) / len(wanted) if wanted else 0.0"),
 ("Recall@5 is 0.3 and answers are poor. What should you work on first?",
  ["The prompt", "Retrieval: chunking, the embedding model or k", "A bigger LLM"], 1,
  "The model can't answer from documents it never saw. Fix retrieval first."),
 ("Set overlap", "Take the top k, turn both lists into sets and count what they share. The same \"is it in here?\" lookup as Two Sum.",
  "\"I intersect the top-k ids with the relevant set and divide by the number of relevant ids, guarding the empty case.\"", "two_sum"))

lesson("pick_config", "Designing a RAG experiment",
 ["The settings that matter most in RAG: **chunk size** and **overlap**, **k** (how many chunks go into the prompt), the **embedding model**, and whether you **rerank**. Vary two at a time.",
  "Hold the eval set, the judge and the answering model fixed. Log retrieval quality, answer quality, p95 latency and cost for every run. Then pick using the rule you wrote down: best answer quality within the latency budget."],
 ("One evaluated run per config", "from mlflow.genai.scorers import RelevanceToQuery, RetrievalGroundedness\n\nfor chunk_size, k in [(256, 3), (512, 5), (1024, 10)]:\n    with mlflow.start_run(run_name=f\"cs{chunk_size}-k{k}\"):\n        mlflow.log_params({\"chunk_size\": chunk_size, \"k\": k})\n        mlflow.genai.evaluate(data=eval_set, predict_fn=make_app(chunk_size, k),\n                              scorers=[RetrievalGroundedness(), RelevanceToQuery()])"),
 ("Your best-quality config has a p95 of 2.6 seconds; the product needs under 1.5. What do you ship?",
  ["The best-quality config anyway", "The best config within 1.5 seconds", "The fastest config"], 1,
  "A config the product can't use has no return. Maximise quality inside the budget."),
 ("Constraint, then best, then tie-break", "Skip what breaks the budget, keep the best of the rest, and break ties on cost. One walk through the results.",
  "\"I filter by the latency budget, then take the highest quality, with cost as the tie-break.\"", None))

lesson("agent_scorecard", "Evaluating agents",
 ["Agents need more than one number. Track **success rate** (did it finish the task?), **steps** (how much work it took) and **cost per success**, which spreads the cost of failed runs over the successful ones.",
  "Define success with a clear rule, or an LLM judge with a rubric that you check against a few human labels."],
 ("An LLM judge for task success", "from mlflow.genai.judges import make_judge\n\ntask_done = make_judge(\n    name=\"task_success\",\n    instructions=\"Did the agent complete the user's task?\\n\"\n                 \"User: {{ inputs }}\\nAgent: {{ outputs }}\\nAnswer yes or no.\",\n)\nmlflow.genai.evaluate(data=tasks, predict_fn=run_agent, scorers=[task_done])"),
 ("Agent A: 90% success, $0.40 per success. Agent B: 80% success, $0.05 per success. Which is better?",
  ["Always A", "Depends on what a success is worth and what a failure costs", "Always B"], 1,
  "If a success saves $20 of human time, A may win; if it saves $0.50, B does. That's the ROI question."),
 ("Running totals", "One walk with a few counters, then divide with guards for the zero cases.",
  "\"One pass to total successes, steps and cost, then ratios guarded against zero successes.\"", None))

lesson("percentile", "Latency that users feel",
 ["Averages hide slow requests. **p95** is the time 95 out of 100 requests beat; p99 is for 99 out of 100.",
  "Measure the whole request (retrieval, tools, model calls), which is what a trace's total duration gives you, and compare models and configs on p95."],
 ("Finding slow traces in MLflow", "slow = mlflow.search_traces(\n    filter_string=\"attributes.execution_time_ms > 5000\",\n    max_results=100,\n)"),
 ("A model's average latency is 900 ms and its p95 is 4 seconds. What do users experience?",
  ["Everything feels fast", "About 1 in 20 requests is slow enough to notice", "It's always 900 ms"], 1,
  "p95 at 4 seconds means 5 out of 100 requests take 4 seconds or more."),
 ("Sort, then pick by position", "Sort once (the slowest part), then index. The common bug is mixing up counting from 1 and indexing from 0.",
  "\"I sort, compute the rank by rounding up, and subtract one to get the index.\"", None))

lesson("pareto_models", "Comparing LLMs for a task",
 ["To choose a model for a task, run each candidate on the **same eval set**, with the **same judge**, and record **quality, cost and p95 latency** as one MLflow run per model.",
  "Throw out any model that loses on all three to another. What's left is a short list of real trade-offs, decided by what quality is worth to you."],
 ("One run per model, same eval set", "from mlflow.genai.scorers import Correctness\n\nfor model in [\"fast-model\", \"smart-model\"]:\n    with mlflow.start_run(run_name=model):\n        mlflow.log_param(\"model\", model)\n        mlflow.genai.evaluate(data=eval_set, predict_fn=make_app(model), scorers=[Correctness()])\n        mlflow.log_metrics({\"cost_per_1k\": cost[model], \"p95_ms\": p95[model]})"),
 ("Model C is more expensive, slower and less accurate than model A on your eval set. Should C stay on the shortlist?",
  ["Yes, for variety", "No: A beats it on everything", "Only if it's newer"], 1,
  "A model beaten on every measure is never the right choice."),
 ("Pairwise domination", "Compare every pair and keep the models nothing beats. Fine for a handful of models.",
  "\"A model is out if another is at least as good on quality, cost and latency and strictly better on one; what's left is the Pareto front.\"", None))

lesson("better_option", "Return on investment",
 ["Every experiment ends with a decision, and the decision is about value: what does a success earn or save, and what does each call cost?",
  "Net monthly value = volume × success rate × value per success − volume × cost per call. A cheaper model can lose money if it succeeds less often, and an expensive one can pay for itself many times over."],
 ("Log the business number with the run", "with mlflow.start_run(run_name=\"decision-oct\"):\n    mlflow.log_params({\"volume\": 10_000, \"value_per_success\": 4.0})\n    mlflow.log_metric(\"net_monthly_value\", 35_700)\n    mlflow.set_tag(\"decision\", \"ship smart-model\")"),
 ("A model costs 10× more per call but resolves 25% more tickets, each worth $4. Calls cost $0.002 vs $0.02. Is it worth it?",
  ["No, it's 10× more expensive", "Very likely: the extra resolutions are worth far more than the extra cents", "Can't tell"], 1,
  "25 extra resolutions per 100 calls is $100; the extra cost is $1.80."),
 ("Score and keep the best", "Apply one formula to every option and keep the best so far. The skill is choosing the formula with the business.",
  "\"I compute net value per option with the same formula, then take the maximum; the inputs come from evals and from the team that owns the outcome.\"", None))

lesson("summarize_by_tag", "Designing traces for experiments",
 ["A **trace** records one request: every model call, retrieval and tool, with timings, inputs, outputs and token counts. Design traces before you need them.",
  "Tag every trace with the things you'll want to slice by later: **config**, **model**, **prompt version**, **environment**. Mark spans with their type (RETRIEVER, TOOL, CHAT_MODEL) so evaluation and analysis can find them, and put per-request details in span attributes."],
 ("Tags and span types in MLflow Tracing", "import mlflow\n\n@mlflow.trace(span_type=\"RETRIEVER\")\ndef retrieve(question, k):\n    ...\n\n@mlflow.trace\ndef answer(question):\n    mlflow.update_current_trace(tags={\"config\": \"cs512-k5\", \"model\": \"fast-model\"})\n    docs = retrieve(question, k=5)\n    ...\n\ntraces = mlflow.search_traces(filter_string=\"tags.config = 'cs512-k5'\")"),
 ("You want to compare two configs on last week's production traffic. What must already be true?",
  ["Nothing, MLflow figures it out", "Each trace was tagged with its config when it was created", "You need a new eval set"], 1,
  "Tags can't be recovered later. Decide them before the experiment."),
 ("Group by key", "One walk adding into a dict of totals keyed by tag value, then turn totals into averages. The same group-by-key shape as Group Anagrams.",
  "\"I group traces by the tag into running totals in one pass and compute averages and rates at the end.\"", "group_anagrams"))

# "In MLflow" box for existing lessons (platform lessons are Terraform, no box)
MLFLOW = {
 "split_by_key": ("Record which data trained and tested the model", "with mlflow.start_run(run_name=\"churn-split-by-user\"):\n    mlflow.log_params({\"split\": \"by_user\", \"test_users\": len(test_users)})\n    mlflow.log_input(mlflow.data.from_pandas(train_df, name=\"train\"), context=\"training\")"),
 "precision_recall": ("Log both numbers on every run", "mlflow.sklearn.autolog()   # logs params, metrics and the model on fit\n...\nmlflow.log_metrics({\"precision\": 0.67, \"recall\": 0.67})"),
 "best_threshold": ("The threshold is a parameter", "with mlflow.start_run(run_name=\"threshold-0.65\"):\n    mlflow.log_param(\"threshold\", 0.65)\n    mlflow.log_metric(\"val_accuracy\", 1.0)"),
 "fill_template": ("Version prompts in the Prompt Registry", "prompt = mlflow.genai.register_prompt(\n    name=\"support_answer\",\n    template=\"Answer using the context.\\nContext: {{context}}\\nQuestion: {{question}}\",\n)\ntext = prompt.format(context=docs, question=q)\n# Double braces leave single-brace JSON examples alone."),
 "extract_code_block": ("Trace the parsing step", "@mlflow.trace(span_type=\"PARSER\")\ndef parse_reply(reply):\n    ..."),
 "batch_items": ("Trace each embedding batch", "@mlflow.trace(span_type=\"EMBEDDING\")\ndef embed_batch(texts):\n    ..."),
 "backoff_delays": ("Record retries on the span", "with mlflow.start_span(name=\"call_model\") as span:\n    span.set_attribute(\"retries\", retries)"),
 "chunk_text": ("Chunking settings are parameters", "mlflow.log_params({\"chunk_size\": 512, \"chunk_overlap\": 64, \"splitter\": \"characters\"})"),
 "dedupe_chunks": ("Log what cleaning removed", "mlflow.log_metrics({\"chunks_in\": 12_400, \"duplicates_removed\": 1_830})"),
 "retrieve": ("Mark retrieval as a RETRIEVER span", "@mlflow.trace(span_type=\"RETRIEVER\")\ndef retrieve(question, k=5):\n    ...\n# RetrievalGroundedness needs this span type to find the documents."),
 "run_agent": ("Trace the whole agent automatically", "mlflow.langchain.autolog()   # LangGraph runs become traces, one span per step"),
 "trim_history": ("Note what was dropped", "with mlflow.start_span(name=\"trim_history\") as span:\n    span.set_attribute(\"messages_dropped\", dropped)"),
 "tool_pairs": ("Mark tools as TOOL spans", "@mlflow.trace(span_type=\"TOOL\")\ndef search(query):\n    ..."),
 "exact_match": ("Correctness with expected answers", "from mlflow.genai.scorers import Correctness\n\ndata = [{\"inputs\": {\"question\": \"Capital of France?\"},\n         \"expectations\": {\"expected_response\": \"Paris\"}}]\nmlflow.genai.evaluate(data=data, predict_fn=my_app, scorers=[Correctness()])"),
 "first_bad_version": ("One named run per version", "with mlflow.start_run(run_name=\"prompt-v17\"):\n    mlflow.set_tag(\"prompt_version\", \"17\")\n    mlflow.genai.evaluate(data=eval_set, predict_fn=app_v17, scorers=scorers)"),
 "token_cost": ("Autolog records token counts", "mlflow.openai.autolog()   # each model call becomes a span with its token usage"),
 "cache_hits": ("Tag cache hits on the trace", "mlflow.update_current_trace(tags={\"cache\": \"hit\"})"),
 "promote_model": ("Move the champion alias", "from mlflow import MlflowClient\nMlflowClient().set_registered_model_alias(\"main.ml.churn\", \"champion\", version=4)"),
 "slowest_chain": ("Find slow spans in code", "from mlflow.entities import SpanType\nllm_spans = trace.search_spans(span_type=SpanType.CHAT_MODEL)\nslowest = max(llm_spans, key=lambda s: s.end_time_ns - s.start_time_ns)"),
 "detect_loop": ("Mark stopped runs so you can find them", "mlflow.update_current_trace(tags={\"stopped\": \"repeated_tool_call\"})\n# later: mlflow.search_traces(filter_string=\"tags.stopped = 'repeated_tool_call'\")"),
}
