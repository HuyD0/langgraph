# Building and evaluating agent systems: current practice

Researched on 2026-10-11 for the Daily Drill curriculum. Seven researchers each covered one area (orchestration, known failures, context, evaluation, observability, protocols and security, cost) using primary sources only: official documentation, papers and engineering posts from the teams that built the systems. A second agent then re-opened every cited source and checked the claim; 82 findings survived, and claims a source only partly supported were reworded to what the source says. A final critic checked the plan against the evidence and against the library versions installed in this repo.

> **Who this is for.** This was written for the curriculum's author: the "In the curriculum"
> notes and "Changes to the planned lessons" describe plans, not lessons that exist. For what
> exists today, see [../tutor/CURRICULUM_MAP.md](../tutor/CURRICULUM_MAP.md).

## The state of practice

Builders and researchers now agree on the default: start with one agent, and add a team only when you can name the problem it fixes. Teams use several times more tokens, and they often do worse on step-by-step work. When a team does help, the setups that work keep one agent in charge of every change, give helpers a clean context and ask them for short reports, and add a checker that has a written checklist and a round limit. Measuring agents at scale now means repeat runs, cost per successful task, labelled failures, and checking the real end state rather than what the agent says it did. Several tools changed in 2026: langgraph-supervisor is archived, Databricks moved team building to the Agent Bricks CLI, production traces now live in Unity Catalog tables, and the OpenTelemetry agent naming rules are still a draft.

## What to do

### 1. Open the Agent teams module with a 'Do you need a team?' ladder

Open the Agent teams module with a 'Do you need a team?' ladder. The steps are one model call, then a fixed LangGraph workflow, then one agent with tools, then a team. At each step the learner names the problem that forces the move up: a prompt full of if-then branches, tools that overlap, or a separate security boundary. Before adding a second agent, they first fix the tool names and descriptions and run the evals again. Two plain tests replace the maths. First: 'Could I hand these pieces to people who never talk to each other?' (is the task wide or long?). Second: 'Does one agent already pass about half the eval?' If it does, a team probably won't help.

**Why:** Anthropic, OpenAI, Microsoft, LangChain and Databricks all give this same default. In a controlled study by Google, DeepMind and MIT, every team design lost 39-70% on step-by-step planning, and once one agent scored above about 45%, adding agents gave nothing or made things worse.

**In the curriculum:** Planned Agent teams lesson 'when a team is worth it': move it to first place and widen it into the ladder

**Sources:** <https://www.anthropic.com/engineering/building-effective-agents>, <https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf>, <https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns>, <https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them>, <https://arxiv.org/html/2512.08296>, <https://learn.microsoft.com/en-us/azure/databricks/agents/concepts/>

### 2. Make 'dollars per successful task' the main number whenever a team is compared with one agent

Make 'dollars per successful task' the main number whenever a team is compared with one agent. It is the total cost of the eval run, failed tasks included, divided by the number of tasks that passed. Put rough token multipliers on one card: a chat costs 1, one agent about 4, a team about 15. Log tokens per agent as well as per run, by reading trace.info.token_usage and multiplying by a price table the learner writes. MLflow's automatic cost field can show $0.00 for Databricks endpoint names.

**Why:** Anthropic's research team used about 15 times the tokens of a chat, and token use alone explained 80% of the differences in its BrowseComp scores. Princeton found a simple approach scoring 93.2% for about $2.45, while a complex one scored 88.0% for about $134.50. If cost doesn't sit next to quality, teams look better than they are.

**In the curriculum:** The first Agent teams lesson (exercise: dollars per success for two designs). Link it to the existing 'Comparing agent designs' lesson, which already shows cost per success. Also the results table in notebook 10.

**Sources:** <https://www.anthropic.com/engineering/multi-agent-research-system>, <https://arxiv.org/html/2407.01502v1>, <https://arxiv.org/abs/2504.13359>, <https://mlflow.org/docs/latest/genai/tracing/token-usage-cost/>, <https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them>

### 3. Teach two rules together

Teach two rules together. First, split work by what each agent needs to know, not by job title: a planner-coder-tester split loses information at every handoff, like a game of telephone. Second, keep one writer. Parallel helpers only read or report back, and one node owns every change (the final answer, a Delta table, a file). Each helper gets a short brief (the goal, what is out of scope, the output format, which tools to use) and returns a short report of about 1,000-2,000 tokens, or a pointer to where it saved its full output.

**Why:** Anthropic calls splits by type of work 'often counterproductive'. Cognition's April 2026 update still warns against several agents writing in parallel and endorses one-writer designs. Anthropic's 16 compiler agents overwrote each other's fixes until the work was split by file. Vague briefs caused duplicated work in Anthropic's research system.

**In the curriculum:** Planned Agent teams lesson 'splitting work so agents don't collide' (rename it 'Split by what each agent needs to know')

**Sources:** <https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them>, <https://cognition.com/blog/dont-build-multi-agents>, <https://cognition.com/blog/multi-agents-working>, <https://www.anthropic.com/engineering/building-c-compiler>, <https://www.anthropic.com/engineering/multi-agent-research-system>, <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

### 4. In the fan-out lesson, workers sent out with Send are read-only (search, read a table)

In the fan-out lesson, workers sent out with Send are read-only (search, read a table). They write into a state key that has a reducer (Annotated[list, operator.add]), so the gather step receives every result. Teach the barrier in plain words: the gather waits for the slowest helper, so one slow helper holds up the whole run. Give each helper a timeout. Add one alias card so that 'parallelization', 'fan-out/gather', ADK ParallelAgent and LangGraph Send are recognised as the same idea.

**Why:** Pattern names now line up across vendors, and the LangGraph form is Send plus a reducer. Anthropic reports that its lead agent waits for each batch of helpers, so one slow helper blocks the run. Microsoft lists sharing changeable state between agents running at the same time as an antipattern.

**In the curriculum:** Planned Agent teams lesson 'fan out then gather (Send; pipeline vs barrier timing)'

**Sources:** <https://docs.langchain.com/oss/python/langgraph/workflows-agents>, <https://www.anthropic.com/engineering/building-effective-agents>, <https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns>, <https://www.anthropic.com/engineering/multi-agent-research-system>

### 5. Build supervisors the current way: a main agent made with create_agent, whose tools are the helper agents

Build supervisors the current way: a main agent made with create_agent, whose tools are the helper agents. Do not use create_supervisor or the langgraph-supervisor package. Helpers put every finding in their final message. They get only the task, unless they must continue earlier work. The supervisor passes a helper's answer on word for word instead of rewording it. On Databricks, label Supervisor Agent, the Supervisor API and the old custom multi-agent guide as legacy. The current path is a LangGraph main agent that calls Genie Agents and other agents as tools, deployed with the Agent Bricks CLI.

**Why:** LangChain says langgraph-supervisor 'is no longer maintained', and its repository was archived on 20 Sep 2026. LangChain's benchmark found the naive supervisor lost quality by rewording helper answers, and that forwarding them unchanged (after removing handoff messages) gave a 'nearly 50%' improvement. Databricks' October 2026 docs list the older team-building routes as legacy.

**In the curriculum:** Existing Agents lesson 'Comparing agent designs': its stack snippet builds a 'supervisor', so show the create_agent-with-tools version. Also the notebook 10 build, and a one-line legacy note in docs/END_TO_END.md.

**Sources:** <https://docs.langchain.com/oss/python/langchain/multi-agent/subagents>, <https://github.com/langchain-ai/langgraph-supervisor-py>, <https://www.langchain.com/blog/benchmarking-multi-agent-architectures>, <https://learn.microsoft.com/en-us/azure/databricks/agents/legacy/>, <https://learn.microsoft.com/en-us/azure/databricks/agents/concepts/>

### 6. Build the checker lesson on four rules

Build the checker lesson on four rules. (1) Write the pass/fail checklist first. (2) Give the checker only the finished work and the checklist: a fresh context, ideally a different model. (3) Cap the rounds, for example at 3, and decide in advance what happens at the cap: return the best attempt with a warning, or hand it to a human. (4) Include negative checks so passing is not trivial. Where possible, the checker looks at real evidence (runs the query, reads the table) rather than at the agent's explanation. Never use debate or majority vote as the checker.

**Why:** In MAST, a check against the overall goal was the largest single fix (+15.6 points). Anthropic found agents 'reliably skew positive when grading their own work'. Without concrete criteria, a checker runs one or two tests and declares victory. In multi-agent debate, agents drop correct answers in order to agree.

**In the curriculum:** Planned Agent teams lesson 'a checker with a round limit'

**Sources:** <https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them>, <https://www.anthropic.com/engineering/harness-design-long-running-apps>, <https://arxiv.org/html/2503.13657v3>, <https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns>, <https://arxiv.org/abs/2509.05396>

### 7. In 'testing the checker with planted mistakes', plant two kinds of fault

In 'testing the checker with planted mistakes', plant two kinds of fault. One is a wrong answer. The other is a confident claim that didn't happen ('I've updated the ticket' when the table never changed). Compare a judge that reads only the final message with a code scorer that checks the table. Add a 'do-nothing agent' row that must score 0. Before trusting any judge, compare it with 20-50 traces the learner labelled by hand.

**Why:** In a 2026 study, no LLM judge reading agent transcripts did much better than a coin flip at spotting these false successes, because judges were swayed by confident closing words. Berkeley RDI got top scores on major agent benchmarks with an agent that mostly solved nothing, so a do-nothing agent scoring above 0 means the grader has a bug.

**In the curriculum:** Planned Evals lesson 'testing the checker with planted mistakes'

**Sources:** <https://arxiv.org/abs/2606.09863>, <https://rdi.berkeley.edu/blog/trustworthy-benchmarks-cont/>, <https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents>, <https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/align-judges>

### 8. Turn 'which traces to read' into 'label failures, then count'

Turn 'which traces to read' into 'label failures, then count'. The learner tags each failed trace with one MAST label, such as repeated steps, saying one thing and doing another, not knowing when to stop, ignoring the task, or weak or missing checking. They log the label as MLflow feedback, count the labels, and fix the biggest group first. A person does the labelling, because automated blame-finding is unreliable.

**Why:** MAST (NeurIPS 2025, more than 1,600 traces from 7 frameworks) is the reference map of how agent teams fail. Its three most common labels cover about 41% of failures. The best automated method found the step where a run went wrong only 14.2% of the time.

**In the curriculum:** Planned Tracing lesson 'which traces to read (failures per cause)'

**Sources:** <https://arxiv.org/html/2503.13657v3>, <https://arxiv.org/abs/2505.00212>, <https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/tracing/observe-with-traces/analyze-traces>

### 9. In 'how full is the context', teach that answers get worse as the context fills up, even when the right fact is in it, and that a bigger window doesn't fix this

In 'how full is the context', teach that answers get worse as the context fills up, even when the right fact is in it, and that a bigger window doesn't fix this. Three habits follow. Put the question after the retrieved chunks. Keep a short 'goal and plan' field in state and add it near the end of each prompt. Run one eval with 5 retrieved chunks and one with 50, and compare the scores.

**Why:** Chroma tested 18 models, and all of them did much better with focused prompts of about 300 tokens. Databricks' own study saw RAG quality fall after 32k-64k tokens. Once the window is more than about half full, mostly facts near the end are still used well.

**In the curriculum:** Planned Tracing lesson 'how full is the context', linked back to the RAG retrieval lessons

**Sources:** <https://www.trychroma.com/research/context-rot>, <https://arxiv.org/abs/2510.05381v1>, <https://www.databricks.com/blog/long-context-rag-performance-llms>, <https://arxiv.org/abs/2508.07479>, <https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus>

### 10. Teach the order of fixes

Teach the order of fixes. First, clear old tool outputs: keep the record that a tool was called but drop its bulky result (ClearToolUsesEdit). Summarise only if runs still get too long. A summary prompt must have required sections: the goal, decisions, exact table names and file paths, IDs and error codes, open tasks and the next step. The last few turns stay word for word. Test compaction with probe questions asked after it runs ('Which table did we write to?', 'What is next?'), plus a planted fact the agent must still recover.

**Why:** JetBrains found that clearing old tool outputs matched LLM summaries on solve rate at similar cost. A generic 'compress the history' prompt cut accuracy from 56.0 to 43.5 in ACON. Factory found every compaction method was weakest at keeping track of which files changed. Current practice judges compaction by whether the agent can still finish the task.

**In the curriculum:** Existing Agents lesson 'Agent memory and context limits' (currently teaches only trimming) and planned Tracing lesson 'what compaction forgets (planted facts)'

**Sources:** <https://arxiv.org/html/2508.21433v3>, <https://arxiv.org/html/2510.00615>, <https://factory.com/news/evaluating-compression>, <https://www.langchain.com/blog/context-management-for-deepagents>, <https://docs.langchain.com/oss/python/langchain/middleware/built-in>

### 11. Add one LLMOps lesson on prompt (prefix) caching

Add one LLMOps lesson on prompt (prefix) caching. Things that stay the same go first and never change during a run: tools and instructions. Things that change go last: the date, user data, new messages. Keep one fixed tool list per agent, and don't switch model or effort partway through a conversation. Exercise: compute a cache hit rate from cache_read_input_tokens, cache_creation_input_tokens and input_tokens in the usage block.

**Why:** An agent re-sends its whole growing context at every step; Manus reports about 100 input tokens for every output token. Cached reads cost about a tenth of normal input or less. One timestamp at the top of the system prompt means the cache never gets a hit. Databricks-hosted Claude supports cache_control on content blocks. The existing 'Caching responses' lesson covers only response caching (LRU), which is a different idea.

**In the curriculum:** New LLMOps lesson placed after 'Caching responses'

**Sources:** <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>, <https://claude.dev/blog/lessons-from-building-claude-code-prompt-caching-is-everything/>, <https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus>, <https://docs.databricks.com/aws/en/machine-learning/model-serving/score-foundation-models>

### 12. Layer the stops

Layer the stops. Always pass your own recursion_limit, because the default no longer works as a safety stop. Add a remaining_steps: RemainingSteps field so the graph routes to a 'summarise what you have' node before it hits the limit. Cap model calls and costly tool calls with ModelCallLimitMiddleware and ToolCallLimitMiddleware. In evals, count hitting a limit as a failure, not a silent crash.

**Why:** Old tutorials say the default is 25. The current docs say 1000, and the langgraph 1.2.11 installed in this repo sets 10,007. Repeating steps (15.7%) and not knowing when to stop (12.4%) are two of the three most common MAST failures.

**In the curriculum:** Existing Agents lesson 'The agent loop' (already sets recursion_limit 10; add why the default no longer protects you) and Tracing lesson 'Guardrails for agents'

**Sources:** <https://docs.langchain.com/oss/python/langgraph/graph-api>, <https://docs.langchain.com/oss/python/langchain/middleware/built-in>, <https://arxiv.org/html/2503.13657v3>

### 13. In 'traces to a table', show the current Azure Databricks setup: traces stored as OpenTelemetry Delta tables in Unity Catalog (MLflow 3.14 or later) and read with plain SQL

In 'traces to a table', show the current Azure Databricks setup: traces stored as OpenTelemetry Delta tables in Unity Catalog (MLflow 3.14 or later) and read with plain SQL. Teach the gotchas. The schema must exist first. Grants must name MODIFY and SELECT on each table, because ALL_PRIVILEGES is not enough. The limit starts at 200 traces per second per workspace. Private Link is not supported. Rule of thumb: keep every trace, and save money by judging only a sample of them with ScorerSamplingConfig.

**Why:** Databricks now recommends Unity Catalog for production traces. OpenTelemetry suggests sampling traces only at around 1,000 or more per second, and simple trace sampling can throw away the failing runs you need. The grants make a natural Terraform exercise for this learner.

**In the curriculum:** Planned Tracing lesson 'traces to a table', with a grants example in a Platform lesson

**Sources:** <https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/tracing/trace-unity-catalog>, <https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/production-monitoring>, <https://mlflow.org/docs/latest/genai/tracing/prod-tracing/>, <https://opentelemetry.io/docs/concepts/sampling/>

### 14. Measuring at scale, as a short recipe

Measuring at scale, as a short recipe. Start with 20-50 tasks taken from real failures. Run each task 3-5 times and report 'passed every time' next to 'passed at least once'. Add reworded copies of some questions. Compare designs on the same questions. Keep the endpoint, model version and settings fixed, and log them as run parameters. Read a sample of transcripts every time.

**Why:** Anthropic's eval guide, tau-bench and Princeton's reliability study all say one run per task hides inconsistency. Rewording questions was the main robustness gap. Infrastructure settings alone moved one benchmark by 6 points.

**In the curriculum:** Notebook 10 evaluation section. Also extend the existing 'Reliable every time: pass^k' lesson's Learn panel with the reworded-copy idea.

**Sources:** <https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents>, <https://arxiv.org/abs/2406.12045>, <https://arxiv.org/abs/2602.16666>, <https://www.anthropic.com/engineering/infrastructure-noise>

### 15. Add the Rule of Two to 'Least privilege for agents'

Add the Rule of Two to 'Least privilege for agents'. Label every tool A (reads untrusted content), B (touches private data) or C (changes things or sends data out); no single agent run should hold all three. Then the team version: each helper gets its own identity and only its own tools, never inherits the supervisor's access, and treats messages from other agents as untrusted input. Treat guardrail classifiers as a smoke alarm, not a lock.

**Why:** Prompt injection is still unsolved: adaptive attacks got past most of 12 published defences more than 90% of the time. Protection therefore has to come from limiting what a hijacked agent can do. Meta's Rule of Two and OWASP's 2026 agentic list (ASI03, ASI07, ASI08) give a checklist the learner can apply directly.

**In the curriculum:** Existing Security lessons 'Least privilege for agents' and 'Prompt injection', plus one Interview angle in the Agent teams module

**Sources:** <https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/>, <https://ai.meta.com/blog/practical-ai-agent-security/>, <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/>, <https://arxiv.org/abs/2510.09023>, <https://arxiv.org/html/2506.08837v3>

## Known failures and their fixes

| Failure | Fix | Card | Source |
|---|---|---|---|
| Two workers started with Send both return {'result': ...} into a plain str key with no reducer. I ran this against the langgraph 1.2.11 installed in this repo: the run stops with InvalidUpdateError ('Can receive only one value per step'). It does not quietly lose one result, as the research note suggested. | Give the shared key a reducer, results: Annotated[list, operator.add], so the gather node receives every worker's result. Or give each worker its own key. Either way, keep the parallel workers read-only and let one node do the writing. | Two workers, one key | <https://docs.langchain.com/oss/python/langgraph/workflows-agents> |
| graph.invoke(inputs) with no recursion_limit, written by someone who remembers the old default of 25. The docs now say 1000, and the installed 1.2.11 uses 10,007, so a stuck agent keeps calling tools and spending money for a long time. | Pass a recursion_limit that fits your graph. Add remaining_steps: RemainingSteps and route to a 'summarise what you have' node when it reaches 2. Cap model and tool calls with ModelCallLimitMiddleware and ToolCallLimitMiddleware. | The loop with no ceiling | <https://docs.langchain.com/oss/python/langgraph/graph-api> |
| A supervisor calls a research helper as a tool, then rewrites the helper's answer in its own words. Any detail the helper left out of its final message is gone for good, because the supervisor sees only that final message. | Tell helpers to put every finding in their final message, and let the supervisor pass the answer on word for word. Build the supervisor with create_agent and helpers as tools, not the archived langgraph-supervisor package. | The supervisor plays telephone | <https://docs.langchain.com/oss/python/langchain/multi-agent/subagents> |
| After writing an answer, the same agent is asked 'Are you sure this is correct?' and says yes. Or a judge reads only the final message, 'I've updated the ticket', and marks the run as passed. | Use a separate checker with a fresh context and a written checklist. Check the real end state with code (query the table, read the ticket) instead of believing what the agent says it did. | Grading its own homework | <https://www.anthropic.com/engineering/harness-design-long-running-apps> |
| while not checker_passes(answer): answer = fix(answer). There is no round limit and no plan for what happens if the checker never passes. | Cap the loop (for example at 3 rounds). Decide in advance what happens at the cap: return the best attempt with a warning, or hand it to a human. | The checker that never lets go | <https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns> |
| system = f'Today is {datetime.now()}. You are a support agent...', and the tool list is built from a set, so its order changes between calls. Every request starts with different text, so cache_read_input_tokens stays at 0. | Keep the system prompt and the tool list fixed and sorted. Put the date and anything else that changes into the newest message. | The timestamp that kills the cache | <https://claude.dev/blog/lessons-from-building-claude-code-prompt-caching-is-everything/> |
| A summarisation step whose prompt just says 'Summarise the conversation'. After it runs, the agent no longer knows which Unity Catalog table it wrote to. It searches for the table again, or says it is finished. | Clear old tool outputs first. Give the summary prompt required sections: goal, decisions, exact table names and paths, IDs and error codes, open tasks, next step. Keep the last few turns word for word. Test with probe questions after compaction. | The summary that forgot the table | <https://factory.com/news/evaluating-compression> |
| An agent on Databricks user authorization is missing the forwarded user token. get_user_workspace_client() falls back to the app's service principal without raising an error, so the agent answers normally but with the app's access instead of the user's. | Call get_user_workspace_client() inside invoke/stream. Test with two different users. Make a whoami check fail loudly if it returns a UUID (the service principal) instead of an email address, and remove that diagnostic tool before release. | The agent that forgot who it was | <https://learn.microsoft.com/en-us/azure/databricks/agents/custom-agents/agent-authentication> |
| An eval counts any HTTP 200 response as success. A Databricks service policy that DENIES a call also returns HTTP 200, with the reason in a databricks_service_policy field, so blocked runs are counted as passes. | Have the scorer read databricks_service_policy and mark those runs 'blocked'. Count denials separately. Keep LLM-judge policies in Log mode until they have been reviewed. | Blocked, but marked as passed | <https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/service-policies/create-service-policy> |
| A LangGraph node issues the refund and then calls interrupt() for approval, and the deployed app is compiled with InMemorySaver. On resume the whole node runs again, so the refund can happen twice, and a restart loses the paused run. | Call interrupt() first and do the side effect after it, or make the side effect safe to run twice. Use a durable checkpointer, such as PostgresSaver or one backed by Lakebase. To deny an action, use 'reject', not 'respond', because a 'respond' reply counts as a successful tool result. | Refund first, ask later | <https://docs.langchain.com/oss/python/langgraph/interrupts> |
| One support agent has fetch_url (reads untrusted web pages), query_customers (private data) and send_email (sends data out). An instruction planted on a web page can make it email customer data to an outsider. | Remove one leg for that run. You can split it into two agents with different permissions, drop the outbound tool, read only trusted sources, or require human approval before send_email. | All three legs in one agent | <https://ai.meta.com/blog/practical-ai-agent-security/> |
| MLFLOW_TRACE_SAMPLING_RATIO=0.1 is set to save money at a few thousand runs a day. The keep-or-drop decision is made when a run starts, so 9 in 10 failing runs are never recorded. | At this volume, keep every trace (Unity Catalog accepts 200 traces per second per workspace at first) and save money by judging only a sample: ScorerSamplingConfig(sample_rate=0.1). If you really must cut trace volume, use tail sampling with a rule that always keeps errors. | Sampling away the failures | <https://mlflow.org/docs/latest/genai/tracing/prod-tracing/> |

## Standards, and how deep to go

| Standard | Status | Depth | Why | Source |
|---|---|---|---|---|
| OWASP Top 10 for Agentic Applications (2026) | Published 9 Dec 2025 by the OWASP GenAI Security Project; the main community checklist for agent risks | use it | ASI03 (identity and privilege abuse), ASI07 (insecure messages between agents) and ASI08 (cascading failures) map straight onto agent teams. They make a good security backbone for the module. | <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/> |
| OWASP Top 10 for LLM Applications 2025 (LLM06 Excessive Agency) | Still the current edition | use it | The clearest least-privilege checklist for tools. Its key idea: a grant or policy decides whether an action is allowed, never the prompt. It fits the existing 'Least privilege for agents' lesson. | <https://genai.owasp.org/llmrisk/llm062025-excessive-agency/> |
| Agents Rule of Two / the lethal trifecta | A design rule from Meta (Oct 2025), building on Simon Willison (Jun 2025); cited in Databricks DASF v3.0. Not a formal standard. | use it | One checklist the learner can apply to any agent: label each tool A, B or C, and never give one run all three. | <https://ai.meta.com/blog/practical-ai-agent-security/> |
| MAST failure taxonomy | Peer-reviewed research taxonomy (NeurIPS 2025): 14 failure modes in 3 groups | use it | Ready-made labels for tagging failed traces and counting them, which is error analysis without maths. | <https://arxiv.org/html/2503.13657v3> |
| pass^k (all k tries succeed) | Metric from tau-bench (2024), now common in agent evals and built into Inspect | use it | Already taught. Reuse it in notebook 10 so the team-versus-one-agent comparison reports 'passed every time'. | <https://arxiv.org/abs/2406.12045> |
| OpenTelemetry GenAI semantic conventions (agent spans and metrics) | Development (not stable). Moved to a separate repository in June 2026 with no tagged release yet, and changed as recently as 5 Oct 2026. | know what it is | MLflow 3 can write these names for you. The learner should know the shape (one workflow span, one named agent span per helper, tool spans inside each), not memorise the attribute strings. | <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md> |
| W3C Trace Context (traceparent header) | Stable web standard. MLflow distributed tracing and the MCP tracing conventions both use it. | know what it is | It is how one trace survives a call to another service. Without it, a team split across services shows up as separate, broken traces. | <https://mlflow.org/docs/latest/genai/tracing/app-instrumentation/distributed-tracing> |
| Model Context Protocol (MCP) 2026-07-28 | Current specification. A breaking redesign: no sessions and no initialize handshake. | know what it is | Databricks exposes tools through MCP. The learner should pin the SDK version, recognise tutorials written for the old protocol, and know the one auth rule: never forward a user's token to another service. | <https://modelcontextprotocol.io/specification/2026-07-28/changelog> |
| Agent2Agent (A2A) 1.0 | Linux Foundation project, in the Agentic AI Foundation since Aug 2026 | know what it is | One sentence is enough: it matters only when your agent calls an agent that another team runs as a separate service. Agents inside one LangGraph app share graph state instead. | <https://a2a-protocol.org/latest/specification/> |
| NIST AI 600-1 (Generative AI Profile) | July 2024. It barely mentions agents, and NIST's agent-specific work is still in progress. | know what it is | Useful vocabulary for company risk reviews (for example 'Information Security' and 'Human-AI Configuration'). Take the practical controls from OWASP instead. | <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence> |
| Databricks AI Security Framework (DASF) v3.0 | Mar 2026. Adds 35 agent risks and 6 controls. | know what it is | It is the framework a company's platform or security team is likely to cite. It names tool poisoning and the 'confused deputy' risk. | <https://www.databricks.com/blog/agentic-ai-security-new-risks-and-controls-databricks-ai-security-framework-dasf-v30> |
| OpenInference | Arize's alternative naming scheme, also built on OpenTelemetry. MLflow and Phoenix translate it automatically. | skip for now | It only matters if a library the learner imports writes these names, and MLflow already converts them. | <https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md> |

## Changes to the planned lessons

Agent teams module: keep 4 lessons, but reorder and rename them. (1) 'Do you need a team?' replaces 'when a team is worth it' and moves to first place. It covers the ladder (one call, workflow, one agent, team), the two plain tests (are the pieces independent? does one agent already pass about half?), the cost multipliers and dollars per success. (2) 'Split by what each agent needs to know' replaces 'splitting work so agents don't collide'. It covers splitting by context rather than job title, helper briefs, short reports and the one-writer rule. (3) 'Fan out, then gather' stays. Workers are read-only, use Send plus a reducer, the gather waits for the slowest helper, and each helper gets a timeout. (4) 'A checker with a round limit' stays. The checklist comes first, the checker gets a fresh context, and the loop has a cap and a fallback. Don't add a separate supervisor lesson. Instead, update the existing 'Comparing agent designs' lesson to build the supervisor with create_agent and helpers as tools, with a note that langgraph-supervisor is archived.

Tracing and AgentOps: keep 'Traces to a table' and add Unity Catalog trace tables, the MODIFY and SELECT grants, and the rule 'keep every trace, judge a sample'. Keep 'How full is the context' and add context rot and where facts sit in the prompt. Rename 'What compaction forgets' to 'What a summary forgets' and make it a probe-question test comparing two approaches, clearing old tool outputs versus summarising, with a planted fact. Rename 'Which traces to read' to 'Label failures, then count', built on the MAST labels. Also update the existing 'Reading agent traces' lesson with the shape of a team trace: one workflow span on top, one named agent span per helper, tool spans inside each. Add one line saying the trace splits in two when a helper runs as a separate service, unless the trace context is passed along.

Evals: keep 'Testing the checker with planted mistakes'. Add false-success plants, a code check of the real end state next to the judge, and a do-nothing agent that must score 0.

Existing lessons to update rather than replace: 'The agent loop' and 'Guardrails for agents' (the recursion default is no longer a safety stop; add RemainingSteps and the limit middleware). 'Agent memory and context limits' (clear old tool outputs before trimming or summarising). 'Human approval in LangGraph' (durable checkpointer, interrupt before the side effect, reject instead of respond). 'Least privilege for agents' (Rule of Two and one identity per agent). 'Reliable every time: pass^k' (add reworded copies).

Only one new lesson outside the plan: LLMOps 'Prompt caching: keep the start fixed', placed after 'Caching responses'.

Notebook 10, in build order. First run a single-agent baseline on about 20 real help-center questions, 3-5 runs each. Then build the team: read-only parallel retrieval with Send and a reducer, a supervisor built with create_agent and helpers as tools, one writer for the final answer, and a claim checker with a written checklist and at most 3 rounds. Give every helper a name so MLflow shows tokens per agent. Report the pass rate, 'passed every time', dollars per success and MAST labels for the failures, with team and single agent side by side. Add one closing cell on deploying with the Agent Bricks CLI, with a legacy note on Supervisor Agent and the Supervisor API.

Where the 12 gotcha cards go: 'Two workers, one key' in Fan out. 'The loop with no ceiling' in The agent loop. 'The supervisor plays telephone' in Comparing agent designs. 'Grading its own homework' and 'The checker that never lets go' in the checker lesson. 'The timestamp that kills the cache' in the new prompt caching lesson. 'The summary that forgot the table' in What a summary forgets. 'Refund first, ask later' in Human approval. 'All three legs in one agent' and 'The agent that forgot who it was' in Least privilege. 'Blocked, but marked as passed' in Testing the checker. 'Sampling away the failures' in Traces to a table.

## Leave out for now

Free-form swarms, group chat between agents, and debate or majority vote used as a checker: Cognition calls swarms 'mostly a distraction', and debate makes agents drop correct answers to agree. Don't present Anthropic's +90.2% team result as general proof that teams win. It is an internal eval nobody else has reproduced, and much of the gain came from spending more tokens. Teach Kim et al.'s numbers as rough guides only (their model explains about 37-41% of the variation, and the error-amplification figures were not statistically significant once other factors were controlled). Leave out automatically designed teams (an unreviewed preprint found them worse than one agent). Leave out the contested speed claim (one Anthropic post says parallel helpers cut time by up to 90%, a later one says teams often take longer). Leave out large-swarm research such as 80-agent collusion and sabotage. Leave out automated blame-finding tools, which are not reliable enough to trust yet.

Too advanced for this learner right now: MCP protocol internals (multi-round requests, the OAuth RFCs, the enterprise token-exchange extension), A2A message details, Omnigent (Beta, aimed at coding agents), OpenInference attribute mapping, and hand-typing OpenTelemetry gen_ai.* strings. Also skip clustered standard errors and power analysis (keep the paired comparison already taught), learned model routers such as RouteLLM and Databricks Smart Routing (teach only 'use a smaller model for a node once your eval proves it still passes'), and model-specific quirks such as 'context anxiety'. Teach ideas, not dated beta header names such as compact-2026-09-04, task budgets or the advisor tool, because they change often. Skip the public benchmark saga (SWE-bench Verified, Pro) beyond one 'read a leaderboard with care' line. Don't build anything on OpenAI's hosted Evals, which shuts down on 30 Nov 2026.

## The critic's notes

**Checked in this repo** (langgraph 1.2.11, langchain 1.4.2, mlflow 3.17.0):
- The default recursion limit is 10,007.
- Two Send workers writing to a plain key raise `InvalidUpdateError: At key 'result': Can receive only one value per step`.
- These all exist: `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware`, `ClearToolUsesEdit`, `SummarizationMiddleware`, `HumanInTheLoopMiddleware`, `ScorerSamplingConfig` and `TraceInfo.token_usage`.

Those plan claims hold.

## 1. Covered by the evidence but missing from the plan

- **Clearing context breaks the prompt cache.** The evidence says editing the start or middle of the context throws away cached work, so clearing should happen in large batches. The plan teaches ClearToolUsesEdit (item 10) and prefix caching (item 11) as separate ideas, and they work against each other. Put one linking line in each lesson.
- **Parallel helpers and the cache.** A cache entry is only available once the first response starts. Send one helper first, then the rest. This belongs in the fan-out lesson.
- **Where a trace breaks.** The evidence says traces break across threads and MCP calls too, not only across separate services. The plan names only separate services.
- **Personal data in traces.** "Keep every trace" says nothing about redaction or how long raw data is kept. The evidence says the standard is to not record prompt and output content by default. Link it to the existing security lesson 'Personal data' (`redact_pii`).
- **Second source for cost and errors.** `system.ai_gateway.usage` records every gateway call even when traces were sampled away. Databricks has three cost levels: per trace, per endpoint or user, and the account budget. The plan only uses `token_usage` plus a hand-written price table.
- **Latency.** The evidence says to report cost and latency next to success. Notebook 10's results table has no latency column.
- **Noise in small evals.** The evidence says to treat gaps under about 3 points as suspect and to compare designs question by question. With about 20 questions, one question is worth 5 points. Add the plain rule "a gap of one or two questions is noise; look at which questions flipped".
- **Judge design.**
  - Judges can be prompt-injected by the text they grade. Add a planted case to 'Testing the checker'.
  - Prefer pass/fail over 1-10 scores, use one judge per quality, and give the judge an "Unknown" option.
  - Watch for position, length and self-preference bias.
  - Grade the outcome first. Add path checks only where the path matters; for teams that means hand-offs and checking steps.
- **Approval fatigue.** The plan's fixes lean on human approval (Rule of Two card, Human approval lesson). The evidence says 93% of prompts get approved and Meta says users confirm blindly. Teach approval as the weakest way to remove a leg, kept for high-impact actions.
- **MCP supply-chain risks.**
  - Tool poisoning, rug pulls and shadowing are not covered. The MCP entry only covers passing tokens through.
  - Databricks MCP governance: choose tools by hand, leave auto-include off, never grant USE CONNECTION.
  - The serverless network policy: only "Restricted access" limits outbound calls, while "Full access" allows them by default. This is the concrete way on Databricks to remove the "sends data out" leg.
- **Tool design** gets no lesson. The evidence covers combining tools, name prefixes, small tool results, clear error messages, and token cuts of 37-98%. The plan only mentions "fix tool names" as a step on the ladder.
- **Trimming pitfalls**, for 'Agent memory and context limits':
  - Trimming must not separate a tool call from its result.
  - SummarizationMiddleware with no trigger never runs.
- **Effort settings and offline evals.**
  - Effort and thinking budgets are hints, not caps; `max_tokens` is the hard limit.
  - HAL found that more reasoning effort gave equal or lower accuracy in 21 of 36 combinations. Put this next to dollars per success.
  - Offline evals and judge scoring can run through a batch path at about half the price. Notebook 10 is a direct fit.
- **Six-shape alias card.** The evidence lists six shapes. The plan's alias card covers only fan-out, and its ladder has no router step, which is the cheapest move before a full agent. Make one card for all six shapes.
- **Progress files and handoff files.** The plan skips these along with "context anxiety", but the practice is general, not model-specific.

## 2. Not backed by the evidence, or overstated

- **Item 6: "+15.6 from a check against the overall goal".** In the evidence, +15.6 was ChatDev's cyclic review loop, a structural change in one system. It is not a MAST-wide "largest single fix".
- **Item 7 cites Berkeley RDI as a "do-nothing agent".**
  - Berkeley RDI actually exploited the graders with a curl wrapper and a conftest.py hook.
  - The real do-nothing example in the evidence is ABC: tau-bench counted empty responses as successes. Swap the citations.
  - "No better than a coin flip" goes further than the evidence, which says judges "mostly can't tell".
- **Plain test 2 (one agent passes about half, so a team won't help)** turns Kim's 45% saturation point into a rule. Their model explains only about 37-41% of the variation. Present it as a hint to check against your own eval, not as one of two main tests.
- **"Keep one writer" as an absolute rule.** Anthropic's 16 parallel writers did deliver a working compiler once each agent worked on separate files and GCC served as a known-good reference. Teach one writer as the default and give that exception.
- **"Never use majority vote as the checker".** The evidence only covers debate, so drop or soften the majority-vote part.
- **The 1/4/15 token multipliers** come from Anthropic's own research system. Label them as that, not as general figures.
- **"A person labels because automated blame-finding is unreliable"** mixes up two tasks. MAST showed an LLM judge can name the failure type with high agreement with humans. Finding the step where it went wrong is the unreliable part.
- **Contradictions a beginner will notice:**
  - The fan-out lesson calls workers "read-only" while they also "write into a state key". Define read-only as "changes nothing outside the graph".
  - "Never forward a user's token" (MCP) sits next to a card built on Databricks' forwarded user token. Explain the difference.
  - The cache card says set order changes "between calls". It is usually stable within one process and changes across restarts or replicas.
- **Specifics not in the evidence** (verify or drop):
  - Princeton's 93.2%/$2.45 vs 88.0%/$134.50.
  - LangChain's "nearly 50%" and the 20 Sep 2026 archive date.
  - MAST's 15.7%, 12.4% and 41%, and the 14.2% step-finding figure.
  - Chroma's 18 models and 300-token prompts; Databricks' 32k-64k drop.
  - 1,000-2,000-token helper reports.
  - "12 defences, more than 90%".
  - MLflow's $0.00 cost field; `cache_control` on Databricks-hosted Claude.
  - Unity Catalog trace details: 200 per second, MODIFY+SELECT, ALL_PRIVILEGES not enough, no Private Link, MLflow 3.14.
  - The `databricks_service_policy` field and "Log mode".
  - OpenTelemetry's 1,000-per-second sampling guidance.
  - In the skip section: "error amplification not significant", "up to 90% faster", and "auto-designed teams worse".
  - OWASP ASI07. The evidence confirms only ASI02, ASI03, ASI08 and ASI09.

## 3. Too much for this learner

- **Notebook 10** is about 8 builds in one. Split it the way 9a-9d were split:
  - 10a: baseline and metrics
  - 10b: the team
  - 10c: the checker
  - 10d: the comparison and MAST labels

  Make the deploy cell optional. Run cost is also high: 20 questions times 3-5 runs times 2 designs times about 15x tokens for the team, plus judges. Have the learner estimate the bill first; that is a natural warm-up for dollars per success.
- **Agent teams lesson 1** packs in the ladder, two tests, the multipliers and dollars per success. Move the cost part into 'Comparing agent designs'.
- **'Traces to a table'** carries 6 platform pitfalls. Keep: traces live in a table, query them with SQL, keep every trace, judge a sample. Move grants, limits and Private Link to the Platform lesson.
- **Stops lesson.** Teach `recursion_limit` plus one call-limit middleware. Make RemainingSteps routing a stretch goal.
- **Standards list (12 entries).** Keep the "use it" items and fold the rest into one "names you'll hear" card.
- **Preview features need a label on their cards:** user authorization (Public Preview), service policies (Beta), production monitoring (Beta).
- **The prompt-caching exercise** uses Anthropic's usage field names. On Databricks' OpenAI-compatible endpoints or on Ollama (the learner's default) those fields may not exist. Give a recorded usage sample or name the API.

## 4. Gaps in the research to search next

- **Local models (Ollama on a laptop):**
  - How reliable are tool calling, Send and supervisor setups on small models?
  - Is the default context size small, and does Ollama cut off long prompts without an error? That would break the 5-vs-50-chunk exercise.
  - Are there any cache usage fields?
- **MLflow autolog with create_agent helpers-as-tools and Send:** does it really produce one named span per helper with its own token usage? The plan assumes it does.
- **Helper timeouts and retries in LangGraph:** how to set them (`step_timeout`, RetryPolicy, ToolRetryMiddleware), and what the gather step does when one helper times out.
- **Testing graphs with fake chat models** (no real model calls). The repo has a pytest suite.
- **Changing graph code or state shape while runs are paused** in a checkpointer. The evidence names "upgrades during runs" but gives no practice.
- **The parallel-tool-call formatting mistake.** The evidence mentions it but never says what it is.
- **How to log MAST labels as MLflow feedback**, or use labeling sessions.
- **Whether Unity Catalog trace storage works on a workspace that uses Private Link**, and which Terraform resources cover the grants.
- **Batch-inference eval cost on Databricks** (for example `ai_query`). The evidence only covers batch pricing in general.

## Evidence

Each verified finding, its kind, how well its source supported it, and where it came from.

### orchestration

- Every major builder gives the same default: use the simplest design that works. Try one model call first, then a fixed workflow, then one agent with tools. Move to several agents only when you hit a limit you can name. *(widely adopted practice; supported)* Anthropic, 2024-12-19: <https://www.anthropic.com/engineering/building-effective-agents> (+5 more)
- Agent teams cost a lot more, and the gain only shows up on hard, valuable tasks that split into independent parts. Expect several times more tokens. Sometimes you pay more and get a worse answer. *(research result; supported)* Anthropic, 2025-06-13: <https://www.anthropic.com/engineering/multi-agent-research-system> (+4 more)
- Same as stated, except that on SWE-bench Verified every team design did worse than one agent: three were slightly worse (-2.1% to -5.4%) and the Independent design was clearly worse (-14.9%). *(research result; partly supported)* Google Research, Google DeepMind, MIT (arXiv), 2025-12-09 (v3 2026-04-08): <https://arxiv.org/html/2512.08296> (+1 more)
- Split work by what each agent needs to know, not by job title. Planner, coder, tester and reviewer splits lose information at every handoff, like a game of telephone. *(vendor advice; supported)* Anthropic (Claude blog), 2026-01-23: <https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them> (+1 more)
- Cognition (2025, 2026) finds that multi-agent setups work best when writes stay single-threaded and extra agents add intelligence (a clean-context reviewer, a 'smart friend', manager-led map-reduce). It says most setups today are limited to read-only search helpers. Parallel writers on one shared piece of work tend to clash: Anthropic's 16 agents overwrote each other's kernel fixes until the work was split by file with a reference compiler as the oracle. *(emerging pattern; partly supported)* Cognition, 2025-06-12: <https://cognition.com/blog/dont-build-multi-agents> (+3 more)
- The pattern names now line up across vendors. Learn about six shapes and their aliases: chain, router, parallel fan-out and gather, supervisor (agents as tools), handoffs (swarm), and generator-checker loop. Hierarchical teams are supervisors stacked in layers. *(widely adopted practice; supported)* Anthropic, 2024-12-19: <https://www.anthropic.com/engineering/building-effective-agents> (+5 more)
- LangGraph's own advice has changed. The langgraph-supervisor package is no longer maintained. LangChain now recommends a main agent that calls helper agents as tools. A naive supervisor that rewrites its helpers' answers loses quality. *(known issue; supported)* LangChain, undated (accessed 2026-10-11): <https://docs.langchain.com/oss/python/langchain/multi-agent/subagents> (+4 more)
- As of Databricks docs updated Oct 6-8, 2026, Supervisor Agent, the deprecated Supervisor API and the 'build a custom multi-agent system' guide are listed as legacy. New code-based agents, including multi-agent ones, should use the Agent Bricks CLI, with Genie Agents added as tools. Omnigent (Beta) is a meta-harness for composing and coordinating agents, mainly coding agents such as Claude Code and Codex, and it can also wrap your own agents. *(vendor advice; partly supported)* Databricks (Azure Databricks docs), 2026-10-08: <https://learn.microsoft.com/en-us/azure/databricks/agents/legacy/> (+2 more)
- Agent teams fail in a known, catalogued set of ways. The most common are repeating steps, saying one thing and doing another, not knowing when to stop, ignoring the task, and weak or missing checking. *(known issue; supported)* UC Berkeley et al. (arXiv), 2025-03-17 (v3 2025-10-26): <https://arxiv.org/html/2503.13657> (+2 more)
- The most reliable second agent is a checker: a fresh-context agent that tests finished work against clear pass criteria, run in a loop with a limit. It needs concrete criteria, or it declares success too early. *(widely adopted practice; supported)* Anthropic (Claude blog), 2026-01-23: <https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them> (+3 more)
- Running agent teams in production is a distributed-systems job. Plan for failures that build on each other, restarts, slow helpers, upgrades during runs, and cost tracked per agent. *(vendor advice; supported)* Anthropic, 2025-06-13: <https://www.anthropic.com/engineering/multi-agent-research-system> (+2 more)
- There is now an emerging open standard for tracing agent teams. OpenTelemetry's GenAI conventions define spans for invoking an agent and for invoking a multi-agent workflow, such as a LangGraph graph. They are still marked Development and are changing. *(emerging pattern; supported)* OpenTelemetry, last updated 2026-10-05 (status: Development): <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md> (+2 more)

### failures

- MAST is the reference map of how multi-agent LLM systems fail. It has 14 failure modes in 3 groups, built from more than 1,600 real traces across 7 frameworks. Most failures come from how the system is designed and how the agents coordinate, not from the model being too weak. *(known issue; supported)* arXiv (Cemri, Pan, Yang et al., UC Berkeley), 2025-10-26 (v1 2025-03-17): <https://arxiv.org/abs/2503.13657> (+2 more)
- Adding agents is not free. In a controlled Google-led study, multi-agent setups helped a lot on tasks that split into independent parts, but cut performance by 39-70% on step-by-step tasks. Teams of independent agents also spread errors much more than teams with a central coordinator that checks work. *(research result; supported)* arXiv (Kim et al., Google Research and others), 2026-04-08 (v1 2025-12-09): <https://arxiv.org/abs/2512.08296> (+5 more)
- When work is split across agents, each sub-agent sees only part of the picture. They make conflicting assumptions, lose information in hand-offs, or redo each other's work. The fixes that builders report are detailed task briefs, shared written state, and keeping all 'write' actions in one agent. *(known issue; supported)* Cognition (Walden Yan), 2025-06-12: <https://cognition.com/blog/dont-build-multi-agents> (+4 more)
- The main claim stands. Correct the detail to: Anthropic evals (Jan 2026): Opus 4.5 first scored 42% on CORE-Bench. After fixing rigid grading, ambiguous task specs and unreproducible stochastic tasks, and switching to a less constrained scaffold, it scored 95%. *(known issue; partly supported)* Anthropic (Prithvi Rajasekaran), 2026-03-24: <https://www.anthropic.com/engineering/harness-design-long-running-apps> (+6 more)
- Agents that repeat steps or don't know when to stop are among the most common failures. Frameworks answer with hard step limits plus a progress check that can trigger re-planning or a clean exit. *(known issue; supported)* LangChain, accessed 2026-10-11: <https://docs.langchain.com/oss/python/langgraph/graph-api> (+5 more)
- Agents often stop too early or declare 'done' without checking the result. The fixes that work keep a machine-readable 'definition of done' outside the model and require an end-to-end check before anything is marked complete. *(known issue; supported)* Anthropic, 2025-11-26: <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents> (+3 more)
- Small mistakes add up over long tasks, and once a mistake is in the context the model is more likely to make further mistakes. Failures usually start in the first few steps but only show up at the end. *(known issue; supported)* arXiv / ICLR 2026 (Sinha, Arun, Goel, Staab, Geiping), 2026-03-13 (v3; v1 2025-09-11): <https://arxiv.org/abs/2509.09677> (+5 more)
- Main claim stands. Correct the detail to: Magentic-One's risky behaviours were repeated logins that got an account temporarily suspended, accepting cookie agreements and terms and conditions without a human, and trying to reach the real Reddit site, which network-layer restrictions blocked. *(known issue; partly supported)* Anthropic, 2025-09-11: <https://www.anthropic.com/engineering/writing-tools-for-agents> (+5 more)
- Measuring agents at scale is itself unreliable: one successful run hides inconsistency, and even frontier models struggle to say which agent and which step caused a failure. Current practice is to run repeated trials, track 'succeeds every time' (pass^k), add perturbation tests, and have humans review traces. *(emerging pattern; supported)* arXiv (Zhang, Yin et al.), 2025-06-02 (v3): <https://arxiv.org/abs/2505.00212> (+5 more)
- Agents drift from their instructions as conversations grow (significant drift within 8 rounds in Li et al.). In MAST, role violations are rare (1.5%), while task-spec violations (11.8%) and derailment (7.4%) are common. ChatDev's +9.4-point gain came from refined role prompts that let only superior agents end conversations, bundled with better verifier specs. Its structural change (a cyclic review loop) gave +15.6. In large swarms, prompt-only role structures made little difference. *(known issue; partly supported)* arXiv, 2025-10-26: <https://arxiv.org/html/2503.13657v3> (+3 more)
- Large agent swarms show further failures: duplicated choices, flooded shared resources, little merged work, and sabotage between agents with conflicting goals. Prompt-level role structures barely helped. The authors offer only untested ideas and frame mitigation as an open problem: a central forum, social-pressure environments, restructured incentives and multi-agent alignment. *(known issue; partly supported)* Anthropic Frontier Red Team, 2026-08-13: <https://www.anthropic.com/research/multiagent-systems> (+2 more)

### context

- Answer quality drops as the context window fills up, even on easy tasks and even when the right facts are in the context. A bigger window does not fix this. Anthropic's API docs now call it 'context rot'. *(research result; supported)* Chroma, 2025-07-14: <https://www.trychroma.com/research/context-rot> (+5 more)
- Where a fact sits in the context matters. Models use the start and the end better than the middle. Once the window is more than about half full, mostly the end still works well. *(research result; supported)* arXiv (TACL), 2023-07-06 (v3 2023-11-20): <https://arxiv.org/html/2307.03172v3> (+2 more)
- The cheapest first fix is to clear old tool outputs: keep the record that a tool was called, but drop its bulky result. In one coding-agent study this matched LLM summarisation's solve rate at similar or slightly lower cost. Both methods cut cost roughly in half compared with no context management. (JetBrains/TU Munich, DL4C workshop at NeurIPS 2025.) *(research result; partly supported)* arXiv (JetBrains Research / TU Munich), 2025-08-29 (v3 2025-10-27): <https://arxiv.org/html/2508.21433v3> (+3 more)
- Same claim. Fix the detail: ACON used 4,096-token history and 1,024-token observation thresholds (512 for OfficeBench) as settings; they were not shown to be optimal. *(known issue; partly supported)* arXiv (Microsoft / KAIST, ICML 2026), 2025-10-01 (v3 2026-06-01): <https://arxiv.org/html/2510.00615> (+5 more)
- Judge compaction by whether the agent can still finish the task afterwards, not by how short the summary is or how much it looks like the original. *(emerging pattern; supported)* Factory Research, 2025-12-16: <https://factory.com/news/evaluating-compression> (+6 more)
- Anthropic now offers three tools for managing context: server-side compaction (summarise), context editing (clear old tool results or thinking), and a client-side memory tool. Its docs say to prefer on-demand compaction wherever it is available. *(vendor advice; supported)* Anthropic (Claude Platform docs), undated, read 2026-10-11: <https://platform.claude.com/docs/en/build-with-claude/compaction> (+5 more)
- OpenAI, LangChain/LangGraph and Google ADK all ship automatic summarisation or compaction triggered by a size or interval limit. LangChain also ships rule-based clearing of old tool results, while the documented ADK compaction keeps recent events raw and summarises older ones. Defaults differ. *(widely adopted practice; partly supported)* OpenAI API docs, undated, read 2026-10-11: <https://developers.openai.com/api/docs/guides/compaction> (+5 more)
- For long or multi-session work, have the agent write its progress to files outside the context (a to-do list, a progress log, notes) and read them back. Anthropic says compaction alone is not enough. *(widely adopted practice; supported)* Anthropic, 2025-11-26: <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents> (+4 more)
- Load information just in time. Keep small pointers in context (file paths, table names, URLs, tool names) and fetch the full content only when it is needed. Design tools to return small, readable results. *(widely adopted practice; supported)* Anthropic, 2025-09-29: <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents> (+4 more)
- Sub-agents, each with its own clean context, keep messy exploration out of the main agent and help on wide, parallel research. But they use many more tokens and can lose shared decisions, so use them for read-heavy work that splits cleanly. *(emerging pattern; supported)* Anthropic, 2025-06-13: <https://www.anthropic.com/engineering/multi-agent-research-system> (+4 more)
- Context management interacts with prompt caching. Editing the start or middle of the context throws away cached work, so keep the start of the prompt fixed, only add to the end, and clear in large batches. *(widely adopted practice; supported)* Manus, 2025-07-18: <https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus> (+3 more)
- Some models get worse as they think their context is running out. They wrap up early or claim the task is done. Long tasks may then need a fresh start from a handoff file instead of compaction. *(known issue; supported)* Anthropic, 2026-03-24: <https://www.anthropic.com/engineering/harness-design-long-running-apps> (+3 more)

### evaluation

- Current guidance agrees on how an agent eval is built: a task, several trials, one or more graders, the full transcript, and the end state of the environment. Use code-based graders first, LLM judges where code can't decide, and humans to check the judges. A first suite of 20 to 50 tasks taken from real failures is enough to start. *(widely adopted practice; supported)* Anthropic Engineering, 2026-01-09: <https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents> (+1 more)
- For agents that serve customers, one run per task is not enough. Run each task several times and report pass^k, the chance the agent succeeds on every one of k tries. pass^k drops as k grows, while pass@k (at least one success in k tries) rises. *(standard; supported)* arXiv (Sierra / Princeton), 2024-06-17: <https://arxiv.org/html/2406.12045> (+3 more)
- Grade the outcome (the end state or final answer) first. Add trajectory and tool-call checks only where the path itself matters, such as a required verification step, a turn limit, or a policy lookup before an action. Rigid step-by-step matching is brittle. *(widely adopted practice; supported)* Anthropic Engineering, 2026-01-09: <https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents> (+3 more)
- An LLM judge is a measuring tool that has to be calibrated against human labels before you trust it. Prefer pass/fail or pairwise questions over 1-10 scores, use one judge per quality dimension, give the judge an 'Unknown' option, and watch for position, verbosity, self-preference, and leniency bias. *(widely adopted practice; supported)* arXiv / NeurIPS 2023, 2023-06-09: <https://arxiv.org/abs/2306.05685> (+5 more)
- Known issue: LLM judges reading agent transcripts are easily fooled by confident wording. Agents often say they succeeded when the environment shows they did not ('false success'), and judges given the transcript mostly can't tell. Judges can also be prompt-injected by the text they are grading. *(known issue; supported)* arXiv (FAGEN@ICML 2026 workshop), 2026-06-01: <https://arxiv.org/abs/2606.09863> (+3 more)
- The headline claim stands. Fix the detail as follows. Epoch's review reports OpenAI's 23 Feb 2026 audit: 27.6% of tasks audited, 59.4% of those with flawed tests (a floor of 16.4%), and contamination. OpenAI's own Feb 2026 post supplies the 138 tasks, the six reviewers, the end of reporting and the Pro recommendation. OpenAI's 8 Jul 2026 post estimated about 30% of SWE-bench Pro's 731 public tasks were broken, and secondary coverage reports it retracted the recommendation. Terminal-Bench went 2.0 → 3.0 → 4.0, and the 19 fixes and 8 removals are stated for 4.0 without saying which earlier version they are counted against. *(known issue; partly supported)* Epoch AI, 2026-09-03: <https://epoch.ai/benchmarks/swe-bench-verified/review> (+6 more)
- Small score differences between agents are often noise. CPU and memory limits moved Terminal-Bench 2.0 scores by 6 points. Pass rates have been seen to drift with time of day, though this has not been measured. Small question sets give wide error bars. So report standard errors, compare agents question by question on the same questions, and treat gaps under about 3 points with suspicion until the setups match. *(vendor advice; partly supported)* Anthropic Engineering, 2026-02-05: <https://www.anthropic.com/engineering/infrastructure-noise> (+2 more)
- Accuracy alone is misleading. Report cost and latency next to success, ideally as cost per successful task, and show the trade-off. More spend often buys little extra accuracy, and sometimes less. *(emerging pattern; supported)* arXiv (Princeton), 2024-07-01: <https://arxiv.org/abs/2407.01502> (+3 more)
- To evaluate agent teams, compare them with a single-agent baseline and score the hand-offs, roles, and verification steps as well as the final answer. Multi-agent setups often fail through design problems, and they can make things worse on step-by-step tasks. *(research result; supported)* arXiv (UC Berkeley), 2025-03-17 (v3 2025-10-26): <https://arxiv.org/html/2503.13657v3> (+3 more)
- Reliability is now treated as more than average success. It also covers consistency across runs, robustness to small changes, predictable failure, and how bad the failures are. Recent capability gains have improved it only a little. *(research result; supported)* arXiv / ICML 2026 (Princeton), 2026-02-18 (v3 2026-06-02): <https://arxiv.org/abs/2602.16666> (+1 more)
- On Databricks the current tool is MLflow 3's GenAI evaluation (`mlflow.genai.evaluate` with scorers and judges), which replaced the older Mosaic AI Agent Evaluation API. The same scorers run in development and on sampled production traffic, and multi-turn (session) evaluation and conversation simulation now exist but are still experimental. *(vendor advice; supported)* Microsoft Azure (China) mirror of Azure Databricks docs, 2026-08-24 (last updated): <https://docs.azure.cn/en-us/databricks/mlflow3/genai/agent-eval-migration> (+4 more)
- Outside Databricks, Inspect (UK AI Security Institute with Meridian Labs) is a prominent open-source eval framework with sandboxed tool use, repeated runs ('epochs') with pass^k-style reducers, and clustered standard errors. OpenAI is shutting down its hosted Evals platform (read-only 31 Oct 2026, shut down 30 Nov 2026, migration guide to Promptfoo), and its agent-eval guide recommends grading traces first. *(vendor advice; partly supported)* UK AI Security Institute, undated (read 2026-10-11): <https://inspect.aisi.org.uk/> (+3 more)

### observability

- The OpenTelemetry GenAI semantic conventions are becoming the shared vocabulary for agent traces. They define a fixed set of span types for agents, workflows and tools, but every part of them is still marked 'Development' (not stable). In June 2026 they moved out of the main OpenTelemetry repository into a new one that has no tagged release yet. *(emerging pattern; supported)* OpenTelemetry, main branch, accessed 2026-10-11 (Status: Development): <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md> (+3 more)
- MLflow 3 tracing is built on top of the OpenTelemetry SDK and translates in both directions. It can take in OpenTelemetry spans written in several dialects, and it can send its own traces out in the GenAI convention format. *(vendor advice; supported)* MLflow, latest docs, accessed 2026-10-11: <https://mlflow.org/docs/latest/genai/tracing/app-instrumentation/opentelemetry/> (+3 more)
- On Azure Databricks, the recommended home for production traces is now Unity Catalog. Traces are stored as OpenTelemetry-format Delta tables that are still linked to an MLflow experiment. This lifts the 100,000-traces-per-experiment cap but comes with hard ingestion limits and some gaps. *(vendor advice; supported)* Microsoft Learn / Databricks, 2026-09-15: <https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/tracing/trace-unity-catalog> (+2 more)
- Databricks production monitoring runs the same MLflow scorers used in offline evals automatically on a sample of live traces, and attaches the results to each trace as feedback. It is in Beta and has specific limits and packaging rules. *(vendor advice; supported)* Microsoft Learn / Databricks, 2026-09-15 (updated 2026-10-08): <https://learn.microsoft.com/en-us/azure/databricks/mlflow3/genai/eval-monitor/production-monitoring> (+2 more)
- There are two different kinds of sampling, and mixing them up causes real problems. Trace sampling decides which runs are recorded at all. Scorer sampling decides which recorded runs get judged. Simple trace sampling, and a full logging queue, can both silently throw away exactly the failing runs you need. *(known issue; supported)* OpenTelemetry, accessed 2026-10-11 (undated page): <https://opentelemetry.io/docs/concepts/sampling/> (+1 more)
- Prompts, model outputs and tool arguments often contain personal data. The standard says not to record them by default, and the vendors provide redaction before export, redaction after storage, and time limits on how long raw data is kept. *(known issue; supported)* OpenTelemetry, main branch, accessed 2026-10-11: <https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-spans.md> (+3 more)
- A good agent dashboard combines the classic service health signals (speed, traffic, errors, how full the system is) with agent-specific counts. The newest OpenTelemetry GenAI metrics add exactly those counts: model calls per agent run, tool calls per agent run, and how long each tool takes. *(emerging pattern; supported)* OpenTelemetry, main branch, accessed 2026-10-11 (Development): <https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/gen-ai-metrics.md> (+3 more)
- Alerts for agents should page on things users would notice: error rate, slow responses, a drop in quality scores, cost spikes, and traffic suddenly falling. They should use short windows and thresholds you can act on. A successful-looking HTTP status code is not proof that the agent worked. *(widely adopted practice; supported)* LangChain, accessed 2026-10-11 (undated page): <https://docs.langchain.com/langsmith/alerts> (+4 more)
- For agent teams, the trace breaks into separate pieces whenever the work crosses a service boundary, a thread or an MCP call, unless the trace context is passed along on purpose. Both MLflow and the OpenTelemetry MCP conventions describe how to pass it. *(known issue; supported)* MLflow, latest docs, accessed 2026-10-11: <https://mlflow.org/docs/latest/genai/tracing/app-instrumentation/distributed-tracing> (+3 more)
- OpenInference is a second, separate set of naming rules for AI traces, made by Arize and also built on OpenTelemetry. It labels spans by kind and flattens message lists into numbered attributes. The main tools now translate between it and the OTel GenAI conventions automatically. *(vendor advice; supported)* Arize AI, main branch, accessed 2026-10-11: <https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md> (+2 more)
- On Databricks, the gateway's usage table is a second, independent source for speed, cost and error numbers. It records every model and MCP call that goes through the gateway, whether or not the agent's own traces were kept. *(vendor advice; supported)* Microsoft Learn / Databricks, 2026-09-29: <https://learn.microsoft.com/en-us/azure/databricks/ai-gateway/usage-tracking>
- To decide what to score in production for multi-agent systems, use a research taxonomy of how they fail instead of generic quality judges. The MAST study found 14 failure modes in 3 groups and showed an LLM judge can label them with high agreement with human annotators. *(research result; supported)* arXiv (UC Berkeley et al.), 2025-03-17 (v3 2025-10-26): <https://arxiv.org/abs/2503.13657> (+2 more)

### protocols-security

- Same claim, but only DASF v3.0 (20 Mar 2026) describes a compromised agent as a 'confused deputy'. The 11 Mar 2026 prompt-injection blog cites the Lethal Trifecta and the Rule of Two but does not use that phrase. *(emerging pattern; partly supported)* Simon Willison's Weblog, 2025-06-16: <https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/> (+2 more)
- Prompt injection is still unsolved. Guardrail classifiers and prompt hardening lower the attack success rate but can be beaten by attackers who adapt. Protection has to come from the architecture: limiting what the agent can do, not only from detecting bad text. *(known issue; supported)* arXiv (Nasr, Carlini, Tramèr et al.), 2025-10-10: <https://arxiv.org/abs/2510.09023> (+3 more)
- Same Databricks settings, but serverless egress is restricted to an allowlist only when the workspace's serverless network policy is set to Restricted access. Full access allows outbound by default. The M2M advice for unattended agents is in the MCP authentication and networking doc, not in the pages cited. *(vendor advice; partly supported)* Microsoft Learn / Azure Databricks, 2026-10-07: <https://learn.microsoft.com/en-us/azure/databricks/agents/custom-agents/agent-authentication> (+3 more)
- Agents on Databricks can quietly run with the wrong identity or report a blocked action as a success. User authorization silently falls back to the app's service principal when the user's token is missing, and a DENY from a service policy comes back as HTTP 200, not as an error. *(known issue; supported)* Microsoft Learn / Azure Databricks, 2026-10-07: <https://learn.microsoft.com/en-us/azure/databricks/agents/custom-agents/agent-authentication> (+1 more)
- Same claim, but the dry-run/diff preview advice is in OWASP ASI02. ASI09 adds plain-language risk summaries (not model-generated rationales), confidence and risk visual cues, and separating preview from effect. *(widely adopted practice; partly supported)* Model Context Protocol, 2026-07-28: <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> (+5 more)
- The OWASP Top 10 for Agentic Applications (labelled '2026', published 9 Dec 2025) is the main community checklist for agent risks. It adds a 'Least-Agency' principle: do not give agents autonomy the task does not need. It also makes observability non-negotiable. *(standard; supported)* OWASP GenAI Security Project, 2025-12-09: <https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/> (+1 more)
- The OWASP Top 10 for LLM Applications 2025 is still the current edition; no newer one is listed. Its LLM06 'Excessive Agency' entry gives the clearest least-privilege checklist for tools. *(standard; supported)* OWASP GenAI Security Project, 2026-10-11 (accessed; 2025 edition): <https://genai.owasp.org/llm-top-10/> (+1 more)
- The current MCP specification is version 2026-07-28. It is a large, breaking redesign: no sessions, no initialize handshake, and several features deprecated. Teaching material written before mid-2026 shows the old flow. *(standard; supported)* Model Context Protocol, 2026-10-11 (accessed; current = 2026-07-28): <https://modelcontextprotocol.io/specification/versioning> (+2 more)
- MCP authorization is OAuth 2.1, with the MCP server acting as a resource server, meaning the server that holds the data and checks access tokens. The rules that matter most: tokens must be issued for that specific server, servers must never pass tokens through to other services, and scopes should start small and grow only when needed. *(standard; supported)* Model Context Protocol, 2026-07-28: <https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization> (+3 more)
- MCP has a known supply-chain risk. Tool descriptions are text the model reads, so a malicious or compromised server can hide instructions in them ('tool poisoning'), change them after approval ('rug pull'), or steer a trusted server's tools ('shadowing'). Even honest servers can be chained into a data leak. *(known issue; supported)* Invariant Labs, 2025-04-01: <https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks> (+2 more)
- Same claim. In the detail, A2A 1.0 requires servers to authenticate every request and to scope results to the caller's authorised access, but leaves other authorisation logic to implementations. The implicit and password OAuth flows are deprecated (What's New calls them removed). *(standard; partly supported)* A2A Project (Linux Foundation), 2026-10-11 (accessed): <https://a2a-protocol.org/latest/specification/> (+6 more)
- NIST AI 600-1 (July 2024) predates agents becoming common. NIST's 2026 agent work (CAISI's AI Agent Standards Initiative and the NCCoE identity and authorization project) points to deterministic policy enforcement and distinct agent identities. OAuth is one of several candidate building blocks (with WIMSE/SPIFFE and others), not a settled consensus. *(standard; partly supported)* NIST, 2024-07-26: <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence> (+3 more)

### cost-performance

- Prompt caching is the biggest single cost and speed lever for agents. An agent re-sends a long, growing context on every step, so most of what it pays for is input that has already been seen. Cached reads cost about one tenth of the normal input price, or less, and they cut time-to-first-token sharply. *(widely adopted practice; supported)* Anthropic, current docs, accessed 2026-10-11: <https://platform.claude.com/docs/en/build-with-claude/prompt-caching> (+7 more)
- Anthropic notes that for concurrent requests, a cache entry only becomes available after the first response begins, so you should wait for the first response before sending the parallel ones. *(known issue; partly supported)* Anthropic, 2026-04-30: <https://claude.dev/blog/lessons-from-building-claude-code-prompt-caching-is-everything/> (+3 more)
- Judge agents by cost per successful task, not by accuracy alone and not by cost per call. Simple, cheap setups often match complex, expensive ones, and you only see this when both numbers sit side by side. *(emerging pattern; supported)* arXiv (Princeton; TMLR 2025), 2024-07-01: <https://arxiv.org/html/2407.01502v1> (+4 more)
- On Databricks you can measure cost at three levels: per trace in MLflow 3, per endpoint and user in system tables, and as an account-wide budget. Each has gaps you need to know about. *(vendor advice; supported)* MLflow, current docs, accessed 2026-10-11: <https://mlflow.org/docs/latest/genai/tracing/token-usage-cost/> (+3 more)
- HAL found that the most costly model run was on the cost-accuracy frontier in only 1 of 9 benchmarks (Opus 4.1: 1 of 8, since it was not run on one benchmark), while Gemini 2.0 Flash was on it in 7 of 9. *(research result; partly supported)* Anthropic, 2025-06-13: <https://www.anthropic.com/engineering/multi-agent-research-system> (+4 more)
- Put hard stops at several levels, because the framework defaults will not protect your budget. LangGraph's default step limit is now so high that it no longer works as a safety stop. The model-side 'budget' features are hints, not caps. *(known issue; supported)* LangChain, current docs, accessed 2026-10-11: <https://docs.langchain.com/oss/python/langgraph/graph-api> (+3 more)
- Routing easy work to smaller, cheaper models saves a lot with little quality loss, if you have an eval to prove it. Newer patterns let a cheap model do the work and call a stronger model only when stuck, or give a cheap model to each subagent. *(research result; supported)* arXiv (LMSYS / UC Berkeley), 2024-06-26, v4 2025-02-23: <https://arxiv.org/abs/2406.18665> (+5 more)
- On Claude Opus 4.5, the only extended-thinking-only model that supports effort, effort works alongside budget_tokens; where adaptive thinking is available, effort is the recommended way to control thinking depth. *(vendor advice; partly supported)* Anthropic, current docs, accessed 2026-10-11: <https://platform.claude.com/docs/en/build-with-claude/effort> (+3 more)
- Letting the model call several independent tools at once, and running them concurrently, cuts agent wall-clock time a lot. But one common message-formatting mistake quietly teaches the model to stop doing it. *(widely adopted practice; supported)* Anthropic, current docs, accessed 2026-10-11: <https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use> (+3 more)
- Shrinking what goes into the context window, meaning tool outputs, tool definitions and old history, is often cheaper and faster than any model change. Engineering teams report token reductions of 37% to 98% from tool design alone. *(vendor advice; supported)* Anthropic, 2025-09-11: <https://www.anthropic.com/engineering/writing-tools-for-agents> (+4 more)
- Any work that doesn't need an answer within seconds, like offline evals, LLM-judge scoring and backfills, should go through a batch path. That roughly halves the price, and the discount can stack with caching. *(widely adopted practice; supported)* Anthropic, current docs, accessed 2026-10-11: <https://platform.claude.com/docs/en/build-with-claude/batch-processing> (+3 more)
