# Agent long-term memory: keeping it fresh, safe and testable

Researched on 2026-10-12 for the Daily Drill curriculum, as the evidence base for four planned lessons on agent long-term memory. One researcher read primary sources only: papers, the code of the libraries involved, official vendor documentation, the OWASP document itself and the text of the GDPR. Secondary pages were used only as pointers, and the note says so where one is cited. Library behaviour was checked by running code against the versions installed in this repo (langgraph 1.2.11, langchain 1.4.2, mlflow 3.17.0). A final critic pass re-opened every source for every number and quote; what could not be checked is listed at the end of "The critic's notes".

> **Who this is for.** This was written for the curriculum's author and for the chat tutor that
> answers questions from this file. The "In the curriculum" notes and "Changes to the planned
> lessons" describe plans, not lessons that exist. For what exists today, see
> [../tutor/CURRICULUM_MAP.md](../tutor/CURRICULUM_MAP.md). There is no maths here; numbers are
> given as plain counts or percentages with their source.

## The state of practice

Long-term memory means facts an agent keeps between conversations, as opposed to the chat history inside one conversation (short-term memory). Every major framework and platform now ships a store for it: LangGraph's store, Databricks managed agent memory (Beta, on Lakebase), Microsoft Foundry Agent Service memory (preview) and Anthropic's client-side memory tool. The hard part is no longer saving facts. It is three other things. First, knowing when a saved fact has gone out of date: recent benchmarks find that agents and memory systems often fail at this, even when the newer fact is in their memory. Second, keeping bad facts out: an ordinary user can plant false memories just by chatting, and OWASP now lists this as its own risk (ASI06). Third, deleting personal data when the law requires it, which a "never delete anything" design must still allow. The designs that work keep each fact with where it came from and when, close an old fact instead of erasing it when a newer one replaces it, check what goes in, and are tested with changes planted on purpose.

## The self-correcting memory design, checked

The design the learner was shown (store each claim with evidence, compare versions with a fixed rule, flag stale claims instead of deleting them, re-check at use) matches LangChain's post "Building Self-Correcting Memory in OpenWiki" (Colin Francis, 25 Aug 2026). The figures "80 stale claims to 9, 15 hallucinated to 0, 98% supported" come from that post. The post does describe a method, but only in part (see item 9 and "The critic's notes").

| Part of the design | How it lines up with current practice | Verdict |
|---|---|---|
| Each claim stored with evidence: the source and its version | OWASP ASI06 asks for "source attribution". Graphiti keeps, on each fact, the list of conversation episodes it came from. Databricks managed memory has an optional `session_id` "for tracing and provenance". | Matches. Keep. |
| A fixed-rule staleness check that compares versions, with no model call | This is the OpenWiki runtime. It only works when the source has a version you can compare: code in git, a Delta table row. Graphiti, Mem0 and Foundry instead use a model to spot when a new fact contradicts an old one, because conversations have no version number. | Good, but covers only one of the two kinds of staleness. |
| Stale claims flagged, not deleted | Graphiti: old facts are "invalidated — not deleted". Mem0's graph version marks old links invalid "rather than physically removing them". Databricks SCD Type 2 and bitemporal tables keep closed rows. | Matches. Missing: the two timelines (when a fact was true, when we learned it), and the legal exception for personal data. |
| The agent re-checks a stale claim when it uses it | OpenWiki does this. LongMemEval and STALE show that using the updated fact is where agents fail, so this step matters. | Matches. Missing: what to say when the re-check is impossible (abstain). |
| "80 to 9, 15 to 0, 98% supported" | Vendor figures from one replayed code repository, n = 2000, with no named judge, repository or repeat runs. The counts and the percentages don't fully agree. Not replicated. | Treat as a demo, not proof. |
| Not in the design at all | Write-time checks against poisoning (OWASP ASI06, MINJA), a per-user namespace set by code, deleting personal data on request, indexing memories by date, and a planted-change test. | Add these. |

## What to do

### 1. Store every memory as a claim with its evidence

Store every memory as a small record, not as loose text: the claim, the source it came from, the version of that source when the claim was made, when it was recorded, and whose memory it is. In LangGraph this is one JSON value per key in a store namespace. Show the learner the same idea in three real systems: Graphiti's fact edges (`fact`, `episodes`, `valid_at`, `invalid_at`, `expired_at`, `created_at`), Databricks managed memory entries (`actor_id`, optional `session_id`, `path`, `content`, `description`), and OpenWiki claims (a claim plus a line range in a repository file and its version).

**Why:** Without the evidence there is nothing to re-check later, and no way to trace a poisoned fact back to where it came in. OWASP ASI06 mitigation 5 is "Require source attribution and detect suspicious updates or frequencies".

**In the curriculum:** Planned Agents lesson "Memory that knows when it's stale" (the record shape is the starting point). Link back to the existing lesson 40 "Agent memory and context limits", which covers only short-term trimming.

**Sources:** <https://langchain.com/blog/self-correcting-memory-openwiki>, <https://github.com/getzep/graphiti/blob/main/graphiti_core/edges.py>, <https://learn.microsoft.com/azure/databricks/agents/agent-memory/managed-memory>, <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/>

### 2. Teach two kinds of "stale", and the plain rule for the first

A memory goes stale in two different ways. (a) Its source changed: the policy file, the table row or the code it came from has a newer version. A plain rule catches this: compare the stored version with the current one, and flag the claim if they differ. No model call, so it is cheap and repeatable. (b) Something newer contradicts it without touching the source: the user says "I moved to York" when memory says Leeds. Only a model can spot this, and it often fails. The lesson builds (a) by hand and names (b) as the harder, open problem.

On Databricks, a good version for (a) is the row-level `_metadata.row_commit_version` from row tracking (the table version at which that row was last inserted or updated), not the whole table's version, which changes on every write. Row tracking has to be switched on for Delta tables.

**Why:** OpenWiki's check is a fixed rule that makes no model calls, and its author says a version change only triggers a review, since "many code changes do not immediately invalidate a dependent claim". For (b): in STALE (May 2026 preprint, 400 scenarios, 1,200 questions) the best model scored 55.2% overall on tests of noticing that memories are out of date (including a later remark quietly making an old memory wrong). In MemoryAgentBench's fact-update test, the best score on questions that need two linked facts was 28 out of 100. Graphiti itself uses a model to find contradictions.

**In the curriculum:** Planned Agents lesson "Memory that knows when it's stale" (exercise: write `is_stale(claim, current_versions)`).

**Sources:** <https://langchain.com/blog/self-correcting-memory-openwiki>, <https://arxiv.org/abs/2605.06527>, <https://arxiv.org/abs/2507.05257>, <https://github.com/getzep/graphiti/blob/main/graphiti_core/utils/maintenance/edge_operations.py>, <https://learn.microsoft.com/azure/databricks/tables/features/row-tracking>, <https://learn.microsoft.com/azure/databricks/tables/history>

### 3. Stale means "check again", not "wrong"; when you can't check, say so

A flagged claim is not deleted and not trusted. When the agent is about to use it, it re-reads the source. If the claim still holds, refresh its version. If not, write the new claim. If the source can't be read, the agent says it can't confirm the fact rather than repeating it. Teach abstention as a correct answer: "I don't have a current record of that" beats a confident old fact.

**Why:** OpenWiki says a stale claim means it "can no longer safely assume that the claim is still true without checking the source again", and unresolved claims "stay flagged for a future update rather than being silently dropped". LongMemEval (ICLR 2025) counts abstention, saying "I don't know" to a question about something never mentioned, as one of five core memory abilities. STALE found that models often accept an outdated assumption built into a user's question.

**In the curriculum:** Planned Agents lesson "Memory that knows when it's stale" (the re-check step and the "can't confirm" reply).

**Sources:** <https://langchain.com/blog/self-correcting-memory-openwiki>, <https://arxiv.org/abs/2410.10813>, <https://arxiv.org/abs/2605.06527>

### 4. When a new fact replaces an old one, close the old one; don't overwrite it

Give each claim two dates: `valid_from` (when it became true) and `valid_to` (empty while it is still true). When a newer fact arrives, set the old claim's `valid_to` to the new claim's `valid_from` and save the new claim alongside. Current answers filter on "`valid_to` is empty"; questions about the past can still be answered. Then add the second timeline in one sentence: when the fact was true in the world is not the same as when the system learned it. Show the same idea in three places: Graphiti (`valid_at` and `invalid_at` for the world, `created_at` and `expired_at` for the system), Databricks SCD Type 2 tables (`__START_AT`, `__END_AT`) and Databricks bitemporal tables (Beta), which add `__SYSTEM_START_AT` and `__SYSTEM_END_AT`.

Teach the LangGraph trap at the same time. `store.put` on an existing key replaces the whole value. I checked this against the installed langgraph 1.2.11: the old value is gone, and `InMemoryStore` even resets `created_at`. PostgresStore does the same replace. So a history needs one key per version (for example `office@1`, `office@2`), not one key per topic.

**Why:** The Zep paper ends the old fact at the moment the new one became true; the current Graphiti code does `edge.invalid_at = resolved_edge.valid_at` and stamps `expired_at`, and deletes nothing. Mem0's basic version does the opposite (DELETE is "removal of memories contradicted by new information"), while its graph version keeps them to allow reasoning about time. LongMemEval's authors report that designs which ignore time do poorly on time questions. The note on caution: in the Zep paper's own results, the knowledge-update score went down with gpt-4o-mini (76.9% to 74.4%) and up with gpt-4o (78.2% to 83.3%), so the structure alone does not guarantee better answers.

**In the curriculum:** Planned Agents lesson "When a new fact replaces an old one" (exercise: `supersede(store, old_key, new_claim)` that closes the old record and adds the new one). Rename the rule from "never delete" to "close, don't overwrite" because of item 6.

**Sources:** <https://arxiv.org/abs/2501.13956>, <https://github.com/getzep/graphiti>, <https://github.com/getzep/graphiti/blob/main/graphiti_core/utils/maintenance/edge_operations.py>, <https://arxiv.org/abs/2504.19413>, <https://learn.microsoft.com/azure/databricks/ldp/cdc>, <https://learn.microsoft.com/azure/databricks/ldp/cdc-advanced>, <https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/langgraph/store/postgres/base.py>

### 5. Guard what goes into memory

Treat every memory write like a database write from an untrusted user. Four rules the learner can apply: (1) Code, not the model, picks whose memory it is. The user id comes from the verified login, and the namespace is built from it (`("users", user_id, "facts")`). If there is no verified user, refuse rather than fall back to a shared namespace. (2) Label each claim with a trust level by source (an official document, the user saying so, the agent's own guess) and never store the agent's own output as trusted fact. (3) Check each write with simple rules first (no instructions like "always approve", no secrets, length limits), with a model check as a second layer. (4) Make bad memories easy to find and roll back: who wrote it, when, from which conversation.

The version check from item 2 does not help here. If an attacker edits the source itself, or a planted claim is stored with a valid source version, the check says "fresh".

**Why:** OWASP's Agentic Top 10 (Dec 2025) entry ASI06, Memory and Context Poisoning, lists nine mitigations, including "Scan all new memory writes and model outputs (rules + AI)", "Isolate user sessions", "Allow only authenticated, curated sources", "Require source attribution", "Prevent automatic re-ingestion of an agent's own generated outputs into trusted memory", per-tenant namespaces with trust scores, and expiring unverified memory. MINJA (arXiv, v5 Feb 2026) planted malicious memories "by only interacting with the agent via queries and output observations", with an average injection success of 98.2%. A GPT-4o detector prompt tuned for one agent caught 131 of 135 attacks there but 0 of 135 on another; a general prompt caught 53 of 135 but raised 34 false alarms out of 50. So detection is a smoke alarm, and the controls above are the lock. Databricks says to set `actor_id` "in your application code from trusted caller context" and "Never let the model choose it", and warns that `actor_id` "is not an access control": the memory store is the security boundary.

**In the curriculum:** Planned Security lesson "Guarding what goes into memory" (exercise: `check_memory_write(claim, user, source)` returning allow or reject with a reason). Link to the existing lessons 68 "Prompt injection" and 70 "Least privilege for agents".

**Sources:** <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/>, <https://arxiv.org/abs/2503.03704>, <https://learn.microsoft.com/azure/databricks/agents/agent-memory/managed-memory>, <https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-memory>

### 6. "Never delete" has one exception: personal data on request

Closing old facts is right for business facts. Personal data is different: a person can ask for it to be erased, and it should not be kept longer than needed. So the design needs a real delete path per user, and the learner should know where copies hide. Deleting a user's namespace is the easy part. Copies may also sit in Delta table history (time travel keeps deleted rows until `VACUUM` removes the old files), in deletion-vector files (which need `REORG TABLE ... APPLY (PURGE)`), in a search index that hasn't synced yet, in traces and in backups. Add an expiry time for memories nobody has used in a long time.

**Why:** GDPR Article 17 gives "the right to obtain from the controller the erasure of personal data", for example when the data is "no longer necessary"; Article 5 says data must be "kept up to date" and kept "for no longer than is necessary". The UK regulator (ICO) says to respond "without undue delay and at the latest within one month", and that data still in backups must be put "beyond use". Databricks' GDPR guide says Delta "retains table history, including deleted records, for 30 days" by default, and that tables with deletion vectors need `REORG TABLE ... APPLY (PURGE)` before the delete is permanent. Foundry memory offers a per-scope delete "to handle user data deletion requests" and a default expiry time in seconds. Anthropic's memory tool docs say "Periodically delete memory files that haven't been accessed in a long time".

**In the curriculum:** Planned Agents lesson "When a new fact replaces an old one" (one paragraph on the exception) and planned Security lesson "Guarding what goes into memory" (the delete path). Link to the existing lesson 72 "Personal data".

**Sources:** <https://gdpr-info.eu/art-17-gdpr/>, <https://gdpr-info.eu/art-5-gdpr/>, <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/>, <https://learn.microsoft.com/azure/databricks/ldp/gdpr>, <https://learn.microsoft.com/azure/databricks/tables/features/deletion-vectors>, <https://learn.microsoft.com/azure/foundry/agents/how-to/memory-usage>, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool>

### 7. Store dates and key facts with each memory so search finds the right one

How memories are saved decides what can be found. Three habits from LongMemEval: save each turn as its own record rather than a whole session (this helped when GPT-4o was the reader); add the extracted facts to what gets searched, not only the raw text; and store the date of the event so a question like "where did I live in March?" can narrow the search to that time. Sort what you retrieve by date before giving it to the model, so the newest fact comes last and is easy to spot.

**Why:** In LongMemEval's pilot study, ChatGPT and Coze (both on GPT-4o) scored 37% and 64% lower than the same model reading the history offline. Adding extracted facts to the search keys improved recall by 9.4% and final accuracy by 5.4% on average, and time-aware search improved recall by 11.3% when each record was one turn. Its authors sort retrieved items "by their timestamp" before reading.

**In the curriculum:** Planned Agents lesson "Memory that knows when it's stale" (a short Learn panel note), with a link to the RAG retrieval lessons.

**Sources:** <https://arxiv.org/abs/2410.10813>

### 8. Write memories in the background unless the user is waiting for them

LangChain's docs name two moments to write memories. "Hot path": the agent decides and writes during the conversation, so the memory is available at once but every turn gets slower. "Background": a separate job reads finished conversations and writes memories later, so there is no delay, but other conversations may miss the newest facts for a while. The background job is also the natural place for the write checks in item 5 and the staleness sweep in item 2.

**Why:** The LangChain memory concepts page lists exactly this trade-off; LangMem's guide says the same (writing during the chat "adds perceptible latency"). Foundry extracts memories after a set update delay rather than during the turn.

**In the curriculum:** Planned Agents lesson "Memory that knows when it's stale" (one paragraph). Also a fit for the existing lesson 40 "Agent memory and context limits".

**Sources:** <https://docs.langchain.com/oss/python/concepts/memory>, <https://langchain-ai.github.io/langmem/concepts/conceptual_guide/>, <https://learn.microsoft.com/azure/foundry/agents/how-to/memory-usage>

### 9. Test memory with planted changes, scored three ways

Build a small replay: a script of facts, then planted changes (a fact replaced, a source updated, a false premise in a question, an attempted poisoning write), then questions whose right answers you know. Score each answer as one of three outcomes: used the current fact, used the old fact, or said it couldn't confirm. Count each separately. Then add the checks that catch lazy scoring: a code check that reads the store (is the old claim's `valid_to` set? did the planted bad write get rejected?), a "never updates" memory that must score badly on changed facts, and a "forgets everything" memory that must fail the unchanged facts. Run the replay several times and report the counts with how many questions there were.

**Why:** OpenWiki's evaluation replayed a repository's git history with planned checkpoints and sorted claims into Supported, Stale, Hallucinated and Unverified. That is the right shape, but the post doesn't name the repository or who did the sorting. LongMemEval, MemoryAgentBench (fact consolidation) and STALE (premise resistance) are all built on planted changes. Two traps: LongMemEval's judge counts an answer correct "as long as the updated answer is the required answer", so an answer that also repeats the old fact still passes; and MLflow's `RetrievalGroundedness` scorer only asks whether the answer is "aligned with the information provided in the retrieved context", so an answer built on a stale memory scores as grounded. MLflow 3.17's `KnowledgeRetention` scorer checks memory within one conversation, not across a change of facts.

**In the curriculum:** Planned Evals lesson "Testing memory with planted changes" (exercise: `memory_score(results)` counting current, old and abstained answers). Link to the existing lesson 83 "Testing the checker with planted mistakes", which already teaches the do-nothing agent.

**Sources:** <https://langchain.com/blog/self-correcting-memory-openwiki>, <https://arxiv.org/abs/2410.10813>, <https://arxiv.org/abs/2507.05257>, <https://arxiv.org/abs/2605.06527>; MLflow 3.17.0 scorer docstrings, checked in this repo.

### 10. Know which store you are on, and what it doesn't do

Give the learner one comparison card. LangGraph `InMemoryStore`: for tests only, lost on restart, no expiry (it raises `NotImplementedError` if you pass `ttl`), and `search` returns 10 items unless you set `limit`. LangGraph `PostgresStore` (Lakebase is Postgres, and Databricks' LangGraph template keeps long-term memory there): survives restarts, supports expiry but only removes expired items after you call `start_ttl_sweeper()`. Databricks managed agent memory (Beta): per-actor entries, keyword (BM25) search only, up to 100 results, no vector search, access control at the store level only. Foundry Agent Service memory (preview): extracts user profile, chat summary and procedural memories for you and resolves conflicts itself, with a default expiry and a per-user delete. Anthropic's memory tool: Claude asks for file operations in `/memories` and your code carries them out, so you must block paths outside that folder. None of them stores a source version or a `valid_to` for you; that part is always your schema.

**Why:** These are the platforms in the learner's stack (LangGraph, Databricks, Azure AI Foundry), and each has a limit that changes the design.

**In the curriculum:** A "names you'll hear" card in the planned Agents lesson "Memory that knows when it's stale"; the Databricks details fit a Platform lesson.

**Sources:** <https://docs.langchain.com/oss/python/langgraph/add-memory>, <https://docs.langchain.com/langsmith/configure-ttl>, <https://learn.microsoft.com/azure/databricks/agents/custom-agents/agent-bricks-cli>, <https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/langgraph/store/postgres/base.py>, <https://learn.microsoft.com/azure/databricks/agents/agent-memory/managed-memory>, <https://learn.microsoft.com/azure/databricks/oltp/projects/state-management>, <https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-memory>, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool>

## Known failures and their fixes

| Failure | Fix | Card | Source |
|---|---|---|---|
| `store.put(ns, "office", {"city": "York"})` over an existing "office" key. I ran this on the installed langgraph 1.2.11: the Leeds record is gone and even `created_at` is reset, so there is no history to answer "where was the office in March?". | One key per version (`office@1`, `office@2`), each with `valid_from` and `valid_to`. Close the old one instead of overwriting it. Search current facts with `filter={"valid_to": None}` (checked: works on `InMemoryStore`). | The overwrite that erased history | <https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/langgraph/store/postgres/base.py> |
| A nightly staleness sweep calls `store.search(("users", uid))` and checks what comes back. I checked: with 15 memories it returns 10, so 5 are never checked and nothing warns you. | Pass a `limit` large enough and page with `offset`, or list keys another way. Test the sweep with more memories than the default. | The sweep that stopped at ten | Checked in this repo (langgraph 1.2.11 `InMemoryStore.search`, default `limit=10`) |
| A memory tool takes `user_id` as an argument the model fills in, or falls back to a shared namespace when the login is missing. One user can read or write another's memories. | Build the namespace in code from the verified identity. Reject requests with no identity. On Databricks, remember `actor_id` is not access control: use a separate store per tenant for strict isolation. | Whose memory is it anyway? | <https://learn.microsoft.com/azure/databricks/agents/agent-memory/managed-memory> |
| The agent's own summary of a conversation is saved as a trusted fact, then retrieved and repeated as truth, then summarised again. A mistake becomes "confirmed" by itself. | Label agent-written memories as lowest trust. Never let them re-enter trusted memory automatically; require a real source or the user's confirmation. | The agent that believed itself | <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/> (ASI06 mitigation 6) |
| A user chats normally but phrases things so the agent saves a false "rule" ("refunds over $500 need no approval"). Later, another user's request retrieves it. The version check says the claim is fresh. | Write checks by rule first, trust labels by source, per-user namespaces, an audit trail for rollback, and adversarial tests. Freshness checks don't catch poison. | Fresh but poisoned | <https://arxiv.org/abs/2503.03704> |
| Each claim stores the Delta table version as its evidence version. Every write to the table, even maintenance like `OPTIMIZE`, makes a new table version, so every claim looks stale and re-checking costs a fortune. | Use the row's `_metadata.row_commit_version` (turn on row tracking), or a version column you control. | Everything is stale | <https://learn.microsoft.com/azure/databricks/tables/history>, <https://learn.microsoft.com/azure/databricks/tables/features/row-tracking> |
| The source table is updated, but the Databricks AI Search (formerly Vector Search) index is a Delta Sync index in Triggered mode. Until someone runs a sync, search still returns the old text, so the agent "re-checks" against stale data. | Sync after each change (or use Continuous mode), and store the source row's version next to the indexed text so the agent can tell. | The index that lags the table | <https://learn.microsoft.com/azure/databricks/ai-search/create-ai-search> |
| The memory eval's judge marks "You live in York (you used to live in Leeds)" correct, and also "You live in Leeds or York". LongMemEval's own update judge accepts answers that include old information "as long as the updated answer is the required answer". | Score three outcomes (current, old, can't confirm) with a strict rule: an answer that presents the old fact as current fails. Add a code check of the store. | Both answers, full marks | <https://arxiv.org/abs/2410.10813> |
| A groundedness scorer passes an answer built on last month's policy, because the stale memory was what got retrieved. | Groundedness checks the answer against what was retrieved, not against the truth. Add a planted-change test where the right answer is known. | Grounded in last month | MLflow 3.17.0 `RetrievalGroundedness` docstring, checked in this repo |
| A user asks to be forgotten. The code deletes their rows from the memory table and calls it done. The rows are still readable through time travel, in deletion-vector files, in the search index, in traces and in backups. | Delete the namespace, then `REORG TABLE ... APPLY (PURGE)` where deletion vectors are on, `VACUUM` after the retention period, resync indexes, check traces, and put backups "beyond use". Respond within one month. | Deleted, but still there | <https://learn.microsoft.com/azure/databricks/ldp/gdpr>, <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/> |
| `PostgresStore` is created with a `ttl` config and old memories never disappear. | Call `start_ttl_sweeper()` (and `stop_ttl_sweeper()` on shutdown). `InMemoryStore` has no expiry at all; on LangGraph deployments it is set in `langgraph.json` under `store.ttl`, in minutes. | The expiry that never ran | <https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/langgraph/store/postgres/base.py>, <https://docs.langchain.com/langsmith/configure-ttl> |
| A Claude memory-tool handler writes to whatever path Claude sends. A path like `/memories/../../secrets.env` reaches files outside the memory folder. | Resolve every path and reject anything outside `/memories`, including encoded forms like `%2e%2e%2f`. | The path that walked out | <https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool> |

## Gotcha-card ideas

Six cards, in the lessons where they belong:

1. **The overwrite that erased history** ("When a new fact replaces an old one"). Risky code: `store.put(ns, "office", new_value)`. Fix: a new key per version, close the old one with `valid_to`. Verified on langgraph 1.2.11.
2. **Everything is stale** ("Memory that knows when it's stale"). Risky code: storing the whole table's version as evidence. Fix: the row's version. Teaches why the version must be as narrow as the claim.
3. **Fresh but poisoned** ("Guarding what goes into memory"). A planted claim with a valid source version passes the staleness check. Fix: write checks and trust by source; freshness is not trust.
4. **Whose memory is it anyway?** ("Guarding what goes into memory"). Risky code: a memory tool with a `user_id` argument the model fills in. Fix: namespace from the verified login, refuse when missing.
5. **Both answers, full marks** ("Testing memory with planted changes"). Risky code: a judge prompt that passes any answer containing the new value. Fix: three outcomes, old-as-current fails.
6. **Deleted, but still there** ("When a new fact replaces an old one" or the existing "Personal data" lesson). Risky code: `DELETE FROM memories WHERE user_id = 5` and nothing else. Fix: the full erasure path.

Spares if a lesson needs one: "The sweep that stopped at ten", "The agent that believed itself", "Grounded in last month".

## Standards, and how deep to go

| Standard | Status | Depth | Why | Source |
|---|---|---|---|---|
| OWASP Top 10 for Agentic Applications 2026, ASI06 Memory and Context Poisoning | Published Dec 2025 by the OWASP GenAI Security Project (CC BY-SA 4.0). Nine mitigations listed. | use it | The checklist for "Guarding what goes into memory". It also names the agent-specific twist: poisoned memory lasts across sessions and spreads between agents. | <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/> |
| GDPR Article 17 (right to erasure) and Article 5 (accuracy, storage limitation) | EU law since 2018. The ICO's UK guidance is "under review" after the Data (Use and Access) Act. | use it | Decides that "never delete" needs an exception for personal data, and sets the one-month response time. | <https://gdpr-info.eu/art-17-gdpr/>, <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/> |
| Valid time and system time (the bi-temporal model; SCD Type 2) | A long-standing database idea. Used by Zep/Graphiti; built into Databricks AUTO CDC (SCD Type 2 is general; bitemporal is Beta). | use it | The vocabulary for "When a new fact replaces an old one": when it was true, and when we learned it. | <https://arxiv.org/abs/2501.13956>, <https://learn.microsoft.com/azure/databricks/ldp/cdc-advanced> |
| LongMemEval | ICLR 2025 benchmark, 500 questions, five abilities. | use it | Its five abilities (finding facts, joining facts across sessions, time, updates, abstention) make good test categories for the planted-change lesson. | <https://arxiv.org/abs/2410.10813> |
| LangGraph store API (`BaseStore`: `put`, `get`, `search`, `delete`, namespaces, `index`, `ttl`) | Stable, installed (1.2.11). | use it | The store the learner will build on. Know its limits (items 4 and 10). | <https://docs.langchain.com/oss/python/langgraph/add-memory> |
| Databricks managed agent memory and sessions | Beta, on Lakebase. The older Unity Catalog memory stores are legacy and "will be turned down soon". | know what it is | The managed option on the learner's platform, bound with `agentbricks memory bind`. Keyword search only, no source versions or validity dates. | <https://learn.microsoft.com/azure/databricks/agents/agent-memory/managed-memory>, <https://learn.microsoft.com/azure/databricks/agents/custom-agents/stateful-agents>, <https://learn.microsoft.com/azure/databricks/agents/custom-agents/agent-bricks-cli> |
| Microsoft Foundry Agent Service memory | Public preview. | know what it is | Shows the managed "it resolves conflicts for you" approach, with expiry and per-user delete. The learner uses Foundry models through the Databricks gateway, not this service. | <https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-memory> |
| Anthropic memory tool (`memory_20250818`) and context editing | Memory tool available on Claude 4 and later models, no beta header. Context editing is beta (`context-management-2025-06-27`). | know what it is | The file-based design (the agent reads and edits its own notes) and the warning before context is cleared. Whether it works through the learner's gateway was not checked. | <https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool>, <https://platform.claude.com/docs/en/build-with-claude/context-editing> |
| Zep / Graphiti | Open-source library (Apache 2.0), graphiti-core 0.30.2 (8 Sep 2026); paper Jan 2025. | know what it is | The best-documented "invalidate, don't delete" code. Too heavy to run in the drill (needs a graph database). | <https://github.com/getzep/graphiti> |
| MemoryAgentBench, STALE | Preprints (Jul 2025, v4 Jun 2026; May 2026). Not peer-reviewed. | know what it is | Evidence that noticing and acting on changed facts is still unsolved. Use as warnings, not as rules. | <https://arxiv.org/abs/2507.05257>, <https://arxiv.org/abs/2605.06527> |
| LangMem | Pre-1.0 (0.0.30), last PyPI release 27 Oct 2025; repository active, not archived. | skip for now | Adds memory managers on top of the LangGraph store, but the drill teaches the store directly and the package has not had a release in a year. | <https://pypi.org/project/langmem/>, <https://langchain-ai.github.io/langmem/concepts/conceptual_guide/> |

## Changes to the planned lessons

**As built (2026-10-12):** the planned exercise names above were replaced by `stale_claims(memories, current)` (fresh, stale, unknown), `fact_at(facts, subject, day)`, `memory_write_gate(write)` (keep, review or reject; the namespace choice is taught in its Learn text and stack box, not checked in the exercise) and `memory_update_score(answers)` (shares of current, unsure and stale).

Keep all four lessons, with these adjustments.

**"Memory that knows when it's stale" (Agents).** Start from the claim record (item 1). Teach the two kinds of stale, build only the plain version check, and name the contradiction kind as the hard, open problem (item 2). Add the re-check at use and the "can't confirm" reply (item 3). Short Learn-panel notes on storing dates (item 7), background writing (item 8) and the store comparison card (item 10). Place it after lesson 40.

**"When a new fact replaces an old one" (Agents).** Keep `valid_from` and `valid_to`, but change the rule from "never delete" to "close, don't overwrite", with one paragraph on the personal-data exception (item 6). The exercise must show the LangGraph overwrite trap, since a learner who writes `put` on the same key loses the history without any error. Mention the second timeline (when we learned it) in one sentence, not as a second exercise.

**"Guarding what goes into memory" (Security).** Build it on OWASP ASI06 and MINJA. Exercise: a write check that rejects by rule, labels trust by source and takes the namespace from code. Add the erasure path here or link to "Personal data". Make the point that freshness is not trust.

**"Testing memory with planted changes" (Evals).** Three outcomes per question, a code check of the store, a "never updates" baseline and a "forgets everything" baseline, repeat runs, and the strict rule that the old fact presented as current fails. Reuse lesson 83's do-nothing idea.

Where the six gotcha cards go: see "Gotcha-card ideas" above.

## Leave out for now

Building a knowledge graph (Graphiti needs a graph database; the same ideas fit in a table). Model-based contradiction finding as an exercise: even the best systems score poorly (item 2), and a beginner can't tell a model error from their own bug. Memory "strength" or decay formulas. Letting the agent rewrite its own instructions (procedural memory that edits the prompt): it is the easiest way to plant a lasting bad rule. Cleaning embeddings to remove poison: MINJA's authors say it fails because bad and good records are "highly entangled in the embedding space". Vendor headline numbers used as proof (Zep's 94.8% on DMR, Mem0's "26%" over OpenAI, OpenWiki's "98%"): each was measured by the vendor on its own setup. LongMemEval's standard setting, about 115,000 tokens of history per question (as measured in the Zep paper), which is too costly for a drill. Fine-tuning a model to remember facts.

## The critic's notes

**Checked in this repo** (langgraph 1.2.11, mlflow 3.17.0), with scripts in the scratch folder, not the repo:
- `InMemoryStore.put` on an existing key replaces the value and resets `created_at`. PostgresStore's source upserts the value too (it keeps `created_at`).
- `InMemoryStore` takes only `index` in its constructor; `put(..., ttl=...)` raises `NotImplementedError: TTL is not supported by InMemoryStore`.
- `search` returns 10 items by default (15 stored, 10 returned).
- `search` with a `query` but no `index` config ignores the query and returns items with `score` None.
- `filter={"valid_to": None}` and `filter={"source_version": {"$gt": 3}}` work.
- MLflow 3.17.0 has `KnowledgeRetention`, `RetrievalGroundedness`, `PIIDetection` (experimental, regex only) and the `scorer` decorator.

**On the self-correcting memory figures.** The brief said they came "with no method". That is partly wrong: the OpenWiki post describes a git-history replay with checkpoints, four labels and n = 2000 for each arm. What is missing: the repository, who or what assigned the labels, the number of checkpoints, repeat runs and any spread. Two of its numbers don't line up: 80 stale claims out of 2000 would be 4.0%, but the table says 3.5% (70); and "98% supported" is from a single run (T2), while the 2000-claim table says 97.8%. The post's method works only for sources with versions (code); a secondary pattern site says the same and notes the figures "have not been replicated" (pointer only: <https://agentpatterns.ai/patterns/agent-design/self-correcting-memory-evidence-backed-claims/>). The drop in hallucinated claims is plausible but not explained by the version check, which only looks for stale claims; it may come from requiring evidence for every claim.

**Corrected during the critic pass:**
- MINJA's 98.2% and 76.8% are in the paper's introduction, not its abstract; the numbers stand (v5).
- MINJA is not among the references in OWASP ASI06 (those include PoisonedRAG and AgentPoison). It is cited here as separate evidence.
- The Zep paper's update scores went down for one model; the note says so instead of citing "up to 18.5%" alone.
- LangGraph TTL: one search snippet said store TTL applies only to LangGraph Platform deployments. The docs page itself does not say that, so the note says only that `InMemoryStore` has no TTL and PostgresStore needs the sweeper.
- The LangGraph TTL page gives `sweep_interval_minutes` a default of 5; a search summary said there is no sweeping by default. The page was used.

**Could not verify:**
- The official GDPR text on EUR-Lex would not load. The quotes come from gdpr-info.eu, an unofficial reproduction of the regulation's text, cross-checked against the ICO's guidance.
- Whether Anthropic's memory tool and context editing work for Claude served through the Databricks AI gateway or Foundry.
- Whether Databricks managed agent memory (the new, non-legacy version) supports updating or deleting single entries, or stores timestamps. The page shows only add, list and search; the legacy API has update, delete, `create_time` and `update_time`.
- How Foundry memory "resolves" conflicting facts: whether it keeps the old version or overwrites it.
- Whether `row_commit_version` stays the same after `OPTIMIZE`. The docs say it changes on `MERGE` or `UPDATE` and that `OPTIMIZE` rewrites files to store it; not tested on a workspace.
- MemoryAgentBench's numbers come from the current HTML (v4); earlier versions may differ. STALE's results come from its abstract only.
- LongMemEval's question counts per type are only in a figure; the note uses only the totals and the 30 abstention questions stated in the text.

## Evidence

Each finding, its kind, how well its source supported it, and where it came from. All sources read on 2026-10-12.

### The design and where it came from

- The "self-correcting memory" design (claims with evidence and its version, a deterministic staleness check with no model calls, flag rather than drop, re-check during updates) is LangChain's OpenWiki claims runtime. *(vendor post; supported)* LangChain (Colin Francis), 2026-08-25: <https://langchain.com/blog/self-correcting-memory-openwiki>
- Its evaluation replayed git commits with checkpoints; labels Supported, Stale, Hallucinated, Unverified; n = 2000 per arm; Supported 92.9% to 97.8%, Stale 3.5% to 0.5%, Hallucinated 0.7% to 0%; "stale claims fell from 80 in the baseline to 9", "hallucinated claims fell from 15 to 0"; a single run went from 77% to 98% supported. No repository, judge or repeat runs named. *(vendor result; supported as reported, method incomplete)* same source.
- The pattern needs versioned, per-claim addressable sources and does not fit chat or preferences; figures not replicated. *(secondary pointer only)* <https://agentpatterns.ai/patterns/agent-design/self-correcting-memory-evidence-backed-claims/>

### Time, updates and invalidation

- Zep uses two timelines (when events happened, and when Zep ingested them) and four timestamps per fact; on a contradiction it "invalidates the affected edges" by setting their end to the new fact's start. *(research paper, vendor-authored; supported)* Zep, 2025-01-20: <https://arxiv.org/abs/2501.13956>
- On LongMemEval, Zep's knowledge-update score went from 76.9% to 74.4% with gpt-4o-mini and from 78.2% to 83.3% with gpt-4o; latency was measured over a network to a hosted service. *(research result; supported)* same source.
- Current Graphiti code: `EntityEdge` has `fact`, `episodes`, `valid_at`, `invalid_at`, `expired_at`, `reference_time`, plus `created_at` and `group_id` from its base class; contradiction handling sets `edge.invalid_at = resolved_edge.valid_at` and stamps `expired_at`, and deletes nothing; the README says old facts are "invalidated — not deleted". *(code; supported)* Graphiti main branch: <https://github.com/getzep/graphiti/blob/main/graphiti_core/edges.py>, <https://github.com/getzep/graphiti/blob/main/graphiti_core/utils/maintenance/edge_operations.py>, <https://github.com/getzep/graphiti>
- Mem0's update step has ADD, UPDATE, DELETE and NOOP, where DELETE removes "memories contradicted by new information"; the graph version marks them invalid "rather than physically removing them". *(research paper, vendor-authored; supported)* Mem0, 2025-04: <https://arxiv.org/abs/2504.19413>
- Databricks AUTO CDC builds SCD Type 2 history with `__START_AT` and `__END_AT`; bitemporal storage (Beta) adds `__SYSTEM_START_AT` and `__SYSTEM_END_AT` to separate business time from system time. *(vendor docs; supported)* <https://learn.microsoft.com/azure/databricks/ldp/cdc>, <https://learn.microsoft.com/azure/databricks/ldp/cdc-advanced>
- Every write to a Delta table creates a new table version, including maintenance; history is kept 30 days and time travel 7 days by default; "Don't use table history as a long-term backup". Row tracking gives each row a `row_commit_version`, "the Delta log or table version at which the row was last inserted or updated". *(vendor docs; supported)* <https://learn.microsoft.com/azure/databricks/tables/history>, <https://learn.microsoft.com/azure/databricks/tables/features/row-tracking>
- AI Search (formerly Vector Search) Delta Sync indexes in Triggered mode update only when a sync is started; Continuous mode updates automatically; standard endpoints need a change data feed on the source. *(vendor docs; supported)* <https://learn.microsoft.com/azure/databricks/ai-search/create-ai-search>

### Security

- OWASP ASI06 covers persistent corruption of memory and retrievable context across sessions, lists six common forms and six attack scenarios, and nine mitigations: data protection, content validation of writes, segmentation, authenticated curated sources and minimal retention, source attribution, no automatic re-ingestion of the agent's own outputs, adversarial tests with rollback and per-tenant namespaces, expiring unverified memory, and trust-weighted retrieval. *(standard; supported)* OWASP GenAI Security Project, Dec 2025, pages 24-26: <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/>
- MINJA plants malicious memory records through ordinary queries only; average injection success 98.2% and attack success 76.8% across agents built on GPT-4 and GPT-4o; prompt-based detection was either narrow or noisy; embedding-level cleaning judged to fail. *(research result, preprint v5; supported)* Dong et al., 2026-02-12: <https://arxiv.org/abs/2503.03704>
- Databricks managed memory: set `actor_id` from trusted caller context and "Never let the model choose it"; reject requests without an identity; `actor_id` "is not an access control" and the store is the security boundary. *(vendor docs, Beta; supported)* <https://learn.microsoft.com/azure/databricks/agents/agent-memory/managed-memory>
- Foundry memory warns of prompt injection and memory corruption and recommends content-safety checks and adversarial testing. *(vendor docs, preview; supported)* <https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-memory>
- The Claude memory tool runs client-side; handlers must block path traversal; the docs suggest stripping sensitive data, capping file sizes and deleting long-unused files. *(vendor docs; supported)* <https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool>

### Privacy

- GDPR gives a right to erasure (Article 17) and requires data to be accurate, "kept up to date" and kept "for no longer than is necessary" (Article 5). *(law; supported, unofficial text reproduction)* <https://gdpr-info.eu/art-17-gdpr/>, <https://gdpr-info.eu/art-5-gdpr/>
- The ICO: respond within one month (extendable by two for complex cases), put backup copies "beyond use", tell recipients. Guidance under review. *(regulator guidance; supported)* <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/>
- Databricks: Delta keeps deleted records in history for 30 days by default; run `VACUUM`; deletion-vector tables need `REORG TABLE ... APPLY (PURGE)`; delete in upstream sources too. *(vendor docs; supported)* <https://learn.microsoft.com/azure/databricks/ldp/gdpr>, <https://learn.microsoft.com/azure/databricks/tables/features/deletion-vectors>
- Foundry memory supports deleting all memories for a scope "to handle user data deletion requests" and a default expiry in seconds. *(vendor docs, preview; supported)* <https://learn.microsoft.com/azure/foundry/agents/how-to/memory-usage>

### Retrieval and evaluation

- LongMemEval tests five abilities (information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention) with 500 questions; abstention questions are 30 false-premise rewrites. ChatGPT and Coze dropped 37% and 64% against offline reading. Fact-augmented keys gave +9.4% recall and +5.4% accuracy on average; time-aware query expansion +11.3% recall with turn-level records. The GPT-4o judge agreed with humans over 97% of the time; its update rule accepts answers that also mention old information. *(research result, ICLR 2025; supported)* <https://arxiv.org/abs/2410.10813>
- MemoryAgentBench names four competencies including selective forgetting; in its fact-consolidation test later facts override earlier ones; best multi-hop score 28.0 (GPT-5-mini); "Selective Forgetting still poses a significant challenge to all memory mechanisms". *(research result, preprint v4; supported)* <https://arxiv.org/abs/2507.05257>
- STALE: 400 expert-validated scenarios, 1,200 queries, three dimensions (state resolution, premise resistance, implicit policy adaptation); best model 55.2% overall. *(research result, preprint; supported from abstract)* <https://arxiv.org/abs/2605.06527>
- MLflow 3.17.0: `RetrievalGroundedness` checks alignment with the retrieved context; `KnowledgeRetention` checks retention across turns of one conversation. *(installed package docstrings; supported)* checked in this repo.

### Frameworks and platforms

- LangChain memory concepts: short-term (thread) vs long-term (across threads); semantic, episodic and procedural memory; profile vs collection; hot path vs background writes with their trade-offs; namespaces work like folders and keys like file names. The page does not cover conflicts, provenance or expiry. *(vendor docs; supported)* <https://docs.langchain.com/oss/python/concepts/memory>
- LangGraph long-term memory: `compile(store=...)`, `InMemoryStore` for development, `PostgresStore` or `RedisStore` for production, semantic search via `index={"embed": ..., "dims": ...}`; tools read `runtime.store` and take the user id from `runtime.context`. *(vendor docs; supported)* <https://docs.langchain.com/oss/python/langgraph/add-memory>, <https://docs.langchain.com/oss/python/langchain/long-term-memory>
- LangGraph deployment TTL lives in `langgraph.json` under `store.ttl` (`default_ttl` in minutes, `refresh_on_read` default true, `sweep_interval_minutes` default 5), applying only to items created afterwards; PostgresStore needs `start_ttl_sweeper()`. *(vendor docs and code; supported)* <https://docs.langchain.com/langsmith/configure-ttl>, <https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/langgraph/store/postgres/base.py>
- Databricks agent memory: managed sessions and managed memory (both Beta, on Lakebase, billed as Lakebase during preview); memory search is BM25 keyword search returning up to 100 entries, no vector search, store-level access control only; Model Serving agents can use Lakebase-backed LangGraph checkpoints with time travel; the self-managed Lakebase approach is legacy. *(vendor docs; supported)* <https://learn.microsoft.com/azure/databricks/agents/agent-memory/managed-memory>, <https://learn.microsoft.com/azure/databricks/agents/custom-agents/stateful-agents>, <https://learn.microsoft.com/azure/databricks/oltp/projects/state-management>, <https://learn.microsoft.com/azure/databricks/agents/agent-memory/self-managed-memory>
- Foundry Agent Service memory (preview) extracts user profile, chat summary and procedural memories, consolidates them with a model ("Conflicting facts ... are resolved"), allows 100 scopes per store and 10,000 memories per scope, and does not support VNet integration. *(vendor docs; supported)* <https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-memory>
- Anthropic: the memory tool (`memory_20250818`, commands view, create, str_replace, insert, delete, rename) adds an "ASSUME INTERRUPTION" instruction to the system prompt; context editing (beta) warns Claude near the clearing threshold so it can save to memory. *(vendor docs; supported)* <https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool>, <https://platform.claude.com/docs/en/build-with-claude/context-editing>
- LangMem's guide says memory managers must reconcile new information by deleting, invalidating or consolidating old memories; latest release 0.0.30 on 27 Oct 2025. *(vendor docs and package index; supported)* <https://langchain-ai.github.io/langmem/concepts/conceptual_guide/>, <https://pypi.org/project/langmem/>
