# Learning path: modules -> lessons. Lesson id == the Build exercise id.
# learn: paragraphs (backticks = code), example: (caption, code)
# check: (question, [options], answer_index, why)
# angle: (pattern, explanation, what_to_say, classic_problem_id or None)

MODULES = [
 ("foundations", "AI & ML foundations", "How models learn from data, and how you know whether they're any good.",
  ["split_by_key", "precision_recall", "best_threshold"]),
 ("llm-apps", "Building with LLMs", "Calling a model reliably: prompts, parsing replies, batching and retries.",
  ["fill_template", "extract_code_block", "batch_items", "backoff_delays"]),
 ("rag", "Retrieval (RAG)", "Giving a model the right documents to answer from.",
  ["chunk_text", "dedupe_chunks", "retrieve"]),
 ("agents", "Agents", "Models that call tools in a loop, and keeping that loop under control.",
  ["run_agent", "trim_history", "tool_pairs"]),
 ("evals", "Evals", "Measuring whether a change made your AI better or worse.",
  ["exact_match", "first_bad_version"]),
 ("llmops", "LLMOps", "Running LLM features in production: cost, caching and speed.",
  ["token_cost", "cache_hits"]),
 ("mlops", "MLOps", "Shipping and replacing models safely with a model registry.",
  ["promote_model"]),
 ("platform", "ML platform on Azure Databricks", "The Terraform and Spacelift work behind an ML platform: plans, state, Unity Catalog and networking.",
  ["summarize_plan", "find_replacements", "guard_destroys", "lock_info", "missing_tags", "grants_to_revoke", "count_shift", "overlapping_subnets", "apply_order"]),
 ("agentops", "AgentOps", "Watching agents in production: traces, slow steps and runaway loops.",
  ["slowest_chain", "detect_loop"]),
]

L = {}
def lesson(id, title, learn, example, check, angle):
    L[id] = dict(title=title, learn=learn, example=example, check=check, angle=angle)

# ---- foundations
lesson("split_by_key", "Train, validation and test data",
 ["A model learns patterns from **training** data. To find out whether it learned something real or just memorised, you test it on data it has never seen: the **test** set. A third set, **validation**, is for tuning choices like thresholds without touching the test set.",
  "The split has to be honest. If the same customer, document or day appears in both training and test, the test score is inflated. This is called **leakage**, and it's the most common reason a model that looked great disappoints in production."],
 ("Splitting by user, not by row", "test_users = {'u1', 'u7'}\ntrain = [r for r in rows if r['user'] not in test_users]\ntest  = [r for r in rows if r['user'] in test_users]"),
 ("A model scores 97% in testing and 70% in production. Rows from the same users were in both training and test. What's the likely cause?",
  ["The model is too small", "Leakage: it was tested on people it had already seen", "The test set was too large"], 1,
  "Seeing the same users in training made the test easy. Splitting by user would have given a more honest, lower score."),
 ("Hash set lookup", "You check every row against a set of test values. A set answers \"is this in here?\" in one step, so the whole split is O(n). Checking a list instead would be O(n) per row and O(n²) overall.",
  "\"I put the test keys in a set so each membership check is O(1), which makes the split a single O(n) pass.\"", "two_sum"))

lesson("precision_recall", "Precision, recall and why accuracy lies",
 ["**Precision**: of everything the model flagged, how much was right? **Recall**: of everything it should have flagged, how much did it catch?",
  "When one class is rare (fraud, outages, toxic content), accuracy is misleading: always answering \"no\" can score 99%. Precision and recall show what the model actually does on the cases you care about, and they trade off against each other."],
 ("The three counts behind both numbers", "tp = predicted yes, really yes\nfp = predicted yes, really no\nfn = predicted no,  really yes\nprecision = tp / (tp + fp)\nrecall    = tp / (tp + fn)"),
 ("A spam filter flags 10 emails; 8 are spam. There were 40 spam emails in total. What are precision and recall?",
  ["Precision 0.8, recall 0.2", "Precision 0.2, recall 0.8", "Precision 0.8, recall 0.8"], 0,
  "Precision is 8 of the 10 flagged. Recall is 8 of the 40 spam emails that existed."),
 ("Counting in one pass", "Every pair is classified into one bucket and counted, so it's O(n) time and O(1) space. Interviewers want to hear that you guard against dividing by zero.",
  "\"One pass to count true positives, false positives and false negatives, then two divisions, each guarded for an empty denominator.\"", None))

lesson("best_threshold", "From scores to decisions",
 ["Most classifiers output a **score**, not a yes/no. You choose a **threshold**: above it means yes. Moving it trades precision against recall.",
  "You tune the threshold on the validation set, then check it once on the test set. The best threshold for accuracy is often not the one the business wants."],
 ("Same scores, different thresholds", "scores = [0.9, 0.65, 0.4]\n# t = 0.5  -> [1, 1, 0]\n# t = 0.7  -> [1, 0, 0]  fewer yes: higher precision, lower recall"),
 ("You raise the threshold from 0.5 to 0.9. What usually happens?",
  ["Precision goes up, recall goes down", "Both go up", "Recall goes up, precision goes down"], 0,
  "Fewer things pass a stricter threshold, so the ones that do are more often right (precision up), but more true cases are missed (recall down)."),
 ("Sort, then sweep", "Trying every threshold against every example is O(n²). Sort examples by score once, then move the threshold down one example at a time, updating the count as you go: O(n log n). The same sort-then-sweep idea solves Merge Intervals.",
  "\"Brute force is O(n²). If I sort by score, each step changes one prediction, so I can update accuracy incrementally in O(n log n).\"", "merge_intervals"))

# ---- llm apps
lesson("fill_template", "Prompts are templates",
 ["Real prompts are built from templates with placeholders: instructions, the user's question, retrieved documents, examples.",
  "Prompts often contain JSON or code with curly braces of their own, so naive formatting breaks. Replace only the placeholders you mean to replace."],
 ("Why str.format breaks", "template = 'Reply as JSON like {\"ok\": true}. Question: {q}'\ntemplate.format(q='hi')   # KeyError: '\"ok\"'"),
 ("Your prompt contains an example `{\"answer\": \"...\"}` and a placeholder `{question}`. What's the safe way to fill it?",
  ["`template.format(question=q)`", "Replace exactly `{question}` and nothing else", "Remove all braces first"], 1,
  "`format` treats every `{...}` as a placeholder and fails on the JSON. Replacing only the placeholders you own leaves the example untouched."),
 ("String replacement", "One `replace` per value: O(v × n) for v values and n characters, fine for prompts. The interview point is correctness: scan only for what you own. Matching open and close markers properly is the Valid Parentheses idea.",
  "\"I loop over the values I was given and replace exactly those placeholders, so any other braces in the text survive.\"", "valid_parentheses"))

lesson("extract_code_block", "Parsing what the model says",
 ["Even when you ask for \"JSON only\", models often wrap the answer in chatter or a markdown code fence.",
  "Parse defensively: find the structure you expect, and have a fallback when it isn't there. Where the API supports structured output, use it, but still validate."],
 ("A typical reply", "reply = 'Sure! ```json\\n{\"a\": 1}\\n``` Hope that helps'\n# you want: '{\"a\": 1}'"),
 ("The model sometimes returns JSON inside a ```json fence and sometimes plain. What should your code do?",
  ["Fail when there's no fence, so you notice", "Extract from the fence if present, otherwise use the whole reply", "Ask the model again every time"], 1,
  "Handle both shapes and validate after. Failing on the common plain case would break a working feature."),
 ("Find markers, then slice", "`find` scans once: O(n). The interview skill is handling the missing-marker case instead of assuming the happy path.",
  "\"I locate the fence with find, slice between the markers, and fall back to the whole trimmed string when there's no fence.\"", None))

lesson("batch_items", "Batching API calls",
 ["APIs limit how much you can send per request, and every request has overhead. Sending items in **batches** is faster and often cheaper.",
  "The last batch is usually smaller, and losing it is a classic bug: a thousand documents indexed, one silently missing."],
 ("Slicing in steps", "items = list(range(7))\n[items[i:i + 3] for i in range(0, len(items), 3)]\n# [[0, 1, 2], [3, 4, 5], [6]]"),
 ("You have 1,001 texts and a batch size of 100. How many requests do you send?",
  ["10", "11", "100"], 1,
  "Ten full batches plus one batch with the last text."),
 ("Stepping through a list", "`range(0, n, size)` visits each start once and each item lands in exactly one slice: O(n).",
  "\"I step through the list in jumps of the batch size and slice each batch; the last slice is just shorter, so nothing is dropped.\"", None))

lesson("backoff_delays", "Retries and backoff",
 ["APIs fail for temporary reasons: rate limits, timeouts, overload. Good clients **retry**, waiting longer each time (**exponential backoff**), with a **cap** so waits don't grow forever.",
  "Only retry errors that can fix themselves. A bad request or wrong key fails the same way every time."],
 ("Doubling with a cap", "wait = 1\nfor attempt in range(5):\n    sleep(min(wait, 30))\n    wait *= 2"),
 ("Which error is worth retrying?",
  ["401 Unauthorized", "429 Too Many Requests", "400 Bad Request"], 1,
  "A 429 means \"slow down\"; waiting fixes it. A wrong key or a malformed request will fail again however long you wait."),
 ("Each value from the previous one", "Every wait is computed from the one before (double it, then cap), the same \"build the next answer from the last\" idea as Climbing Stairs. O(k) for k retries.",
  "\"I keep one running value, double it each retry and clip it with min, so it's O(k) time and I never store more than I need.\"", "climbing_stairs"))

# ---- rag
lesson("chunk_text", "Chunking documents",
 ["RAG (retrieval-augmented generation) answers questions from your documents. First you cut each document into **chunks** small enough to search and to fit in a prompt.",
  "Chunks **overlap** a little, so a sentence that crosses a boundary appears whole in at least one chunk."],
 ("Size 4, overlap 1", "'abcdefghij' -> 'abcd', 'defg', 'ghij'\n# each new chunk starts size - overlap = 3 characters later"),
 ("Why do chunks overlap?",
  ["To make the index bigger", "So text cut at a boundary still appears whole in one chunk", "Because embeddings need it"], 1,
  "Without overlap, an answer split across two chunks may never be retrieved in one piece."),
 ("Sliding window", "A fixed-size window moves along the text in steps: O(n) chunks' worth of work. Longest Substring Without Repeating Characters uses a window that grows and shrinks instead.",
  "\"I slide a fixed window by size minus overlap and stop once a window reaches the end, so the last chunk isn't duplicated.\"", "longest_unique_substring"))

lesson("dedupe_chunks", "Cleaning the index",
 ["Real document sets are full of repeats: footers, disclaimers, copied pages. Duplicates waste embedding money and push useful chunks out of the top results.",
  "Normalise text (case, whitespace) into a **key**, and keep only the first chunk for each key."],
 ("Same text, same key", "' '.join('ALL RIGHTS\\nRESERVED.'.lower().split())\n# 'all rights reserved.'"),
 ("Your top 5 retrieved chunks are the same disclaimer from 5 pages. What's the best fix?",
  ["Retrieve 50 chunks instead", "Remove duplicate chunks before indexing", "Use a bigger model"], 1,
  "Fix the index. Retrieving more just pays for more copies of the same text."),
 ("Design a key", "Normalise each item into a key that collides exactly when items should count as the same, and keep a set of seen keys: O(n × length). Group Anagrams is the same trick with sorted letters as the key.",
  "\"I map each chunk to a normalised key and keep a set of keys I've seen, so the first copy survives and the rest are dropped in one pass.\"", "group_anagrams"))

lesson("retrieve", "Retrieval: finding the right chunks",
 ["Retrieval scores every chunk against the question and keeps the top **k** to put in the prompt.",
  "Real systems score with **embeddings** (vectors where similar meanings are close), often combined with keyword search. The shape is the same: score, sort, keep the top k, break ties consistently."],
 ("Score, sort, slice", "scored = sorted(docs, key=score, reverse=True)\ntop = scored[:k]"),
 ("Why decide how ties are broken?",
  ["It makes the code faster", "So results don't change between runs and tests stay stable", "Embeddings require it"], 1,
  "Without a rule, equal scores can come back in any order, which makes results and tests flaky."),
 ("Top k", "Score everything (O(n)) then sort (O(n log n)). In an interview, mention a heap: `heapq.nlargest(k, ...)` keeps only k items, O(n log k), which matters when n is millions.",
  "\"Sorting is O(n log n); with a size-k heap it's O(n log k), which is what you want when k is small and n is huge.\"", None))

# ---- agents
lesson("run_agent", "The agent loop",
 ["An **agent** is a loop: the model picks a tool, your code runs it, the result goes back to the model, repeat until it gives a final answer.",
  "Two rules keep it safe: a **hard step limit**, and turning tool errors into messages the model can read instead of crashes."],
 ("The shape of every agent", "for step in range(MAX_STEPS):\n    action = model(history)\n    if action.final:\n        return action.text\n    history.append(run_tool(action))"),
 ("Why must an agent loop have a maximum number of steps?",
  ["To make answers shorter", "A confused model can loop forever and keep spending tokens", "The API requires it"], 1,
  "Nothing else stops a model that keeps calling the same tool. LangGraph's recursion_limit exists for this."),
 ("Bounded iteration", "At most `max_steps` iterations, each a dict lookup: O(min(n, max_steps)). The interview point is the stopping conditions: final answer, step limit, end of plan.",
  "\"Every loop that depends on a model has a hard upper bound, and errors are returned as observations so the model can recover.\"", None))

lesson("trim_history", "Agent memory and context limits",
 ["Models can only read a limited **context window**. Long chats and agent runs must drop or summarise old messages.",
  "Always keep the **system prompt** (the instructions), then keep the newest messages that fit."],
 ("Keep instructions, then fill from the newest end", "system, rest = messages[0], messages[1:]\n# walk rest from newest to oldest, keep while under budget"),
 ("You keep only `messages[-10:]`. What can go wrong?",
  ["Nothing", "The system prompt falls off and the assistant forgets its instructions", "The reply gets slower"], 1,
  "The system prompt is the first message. Slicing from the end drops it once the chat is long enough."),
 ("Greedy from one end", "Walk backwards once, stop at the first message that doesn't fit: O(n). Two-pointer and sliding-window problems use the same \"budget\" thinking.",
  "\"I pin the system message, then fill the remaining budget from the newest message backwards and stop at the first that doesn't fit, so there are no gaps.\"", None))

lesson("tool_pairs", "Tool calls and results",
 ["When a model calls tools, each call gets an **id**, and each result must reference it. Model APIs reject a conversation where a call has no matching result.",
  "This breaks most often after trimming history, or when a tool crashes and no result is sent. Send the error as the result instead."],
 ("A call and its result", "{'role': 'assistant', 'tool_calls': [{'id': 'call_1', 'name': 'search'}]}\n{'role': 'tool', 'tool_call_id': 'call_1', 'content': '...'}"),
 ("A tool crashed and you skipped sending its result. What happens on the next model call?",
  ["The model ignores it", "The API rejects the request because a tool call has no result", "The tool is called again automatically"], 1,
  "Every call needs an answer. Send the error message as the tool result."),
 ("Matching pairs", "Open on a call, close on its result, report anything left open or closed without opening: O(n). Valid Parentheses is the same with a stack, because brackets must close in order.",
  "\"I track open call ids; each result closes one. Whatever is still open at the end, or closed without being opened, is an error.\"", "valid_parentheses"))

# ---- evals
lesson("exact_match", "Evaluating model answers",
 ["An **eval** is a test set of inputs with expected outputs, plus a way to score answers. It's how you know whether a prompt or model change helped.",
  "Normalise before comparing, or formatting differences (\"Paris.\" vs \"paris\") count as wrong. For open-ended answers, teams use an LLM judge with a clear rubric and check it against human labels."],
 ("Normalise both sides", "def norm(s):\n    return ' '.join(s.lower().replace('.', '').split())"),
 ("Your model answers \"Paris.\" and the expected answer is \"paris\". Your eval marks it wrong. What's the problem?",
  ["The model is wrong", "The comparison isn't normalised", "The eval set is too small"], 1,
  "Clean both strings the same way before comparing."),
 ("Pairwise comparison", "zip the two lists and compare each pair once: O(n). Guard the empty case before dividing.",
  "\"I normalise both sides with the same function, compare pairwise with zip, and return 0 for an empty set instead of dividing by zero.\"", None))

lesson("first_bad_version", "Finding regressions",
 ["A **regression** is a change that made things worse. With many prompt or model versions, re-running every eval is slow and costs money.",
  "If versions pass up to a point and fail after it, **bisect**: test the middle, keep the half that contains the change."],
 ("Bisecting 40 versions", "# test v20: passes -> problem is in v21..v40\n# test v30: fails  -> problem is in v21..v30\n# ... about 6 evals instead of 40"),
 ("You have 64 prompt versions and the newest fails. About how many evals does bisecting need?",
  ["6", "32", "64"], 0,
  "Each eval halves the range: 64 → 32 → 16 → 8 → 4 → 2 → 1."),
 ("Binary search", "Halve the search space each step: O(log n). The classic bug is the boundary: whether you move to mid or mid ± 1.",
  "\"The passes come before the fails, so it's sorted; binary search finds the first failure in O(log n) evals.\"", "binary_search"))

# ---- llmops
lesson("token_cost", "Tokens and cost",
 ["LLM providers bill per **token** (roughly ¾ of a word), with separate prices for input and output. Output usually costs several times more.",
  "Track cost per model, per feature and per user from day one. When the bill jumps, that breakdown tells you why."],
 ("Cost of one call", "cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000"),
 ("Your bill doubled but the number of requests didn't change. What should you check first?",
  ["The model's accuracy", "Tokens per request, especially output tokens and agent steps", "The API's uptime"], 1,
  "Same requests, more cost means more tokens per request: longer prompts, longer answers or more agent steps."),
 ("Group and sum", "One pass, adding each call's cost into a dict keyed by model: O(n). Group Anagrams has the same group-by-key shape.",
  "\"I aggregate into a dict keyed by model in one pass, and round only at the end so rounding errors don't pile up.\"", "group_anagrams"))

lesson("cache_hits", "Caching responses",
 ["Many requests repeat. A **cache** returns a stored answer instead of calling the model again, which saves money and time.",
  "Caches have a size limit. **LRU** (least recently used) evicts whatever hasn't been used for the longest time."],
 ("LRU in Python", "from collections import OrderedDict\ncache = OrderedDict()\ncache.move_to_end(key)       # on a hit\ncache.popitem(last=False)    # evict the oldest"),
 ("A cache returns another user's answer to a question about their own account. What was missing from the cache key?",
  ["The model name", "Who is asking (the user or their permissions)", "The time of day"], 1,
  "If the answer depends on the user, the user must be part of the key."),
 ("LRU cache", "A hash map for O(1) lookup plus an ordering (a linked list, or OrderedDict) for O(1) eviction. \"Design an LRU cache\" is itself a very common interview question.",
  "\"A dict gives O(1) lookups and a doubly linked list keeps recency order, so get and put are both O(1).\"", None))

# ---- mlops
lesson("promote_model", "Model registry and promotion",
 ["A **model registry** (such as MLflow's on Databricks) stores every trained version with its metrics. **Aliases** like `@champion` point at the version serving traffic.",
  "Promote a **challenger** only when it beats the champion by a meaningful margin on the same data. Rolling back is just moving the alias back."],
 ("Loading by alias with MLflow", "import mlflow\nmodel = mlflow.pyfunc.load_model('models:/main.ml.churn@champion')"),
 ("Why require a minimum gain before promoting?",
  ["To save storage", "Tiny differences are often noise, and every swap carries risk", "MLflow requires it"], 1,
  "A 0.001 improvement may vanish on new data. Swapping models has a cost, so make it worth it."),
 ("Running best with a rule", "One pass keeping the best candidate so far, with an explicit tie rule: O(n). Maximum Subarray uses the same \"keep the best so far\" bookkeeping.",
  "\"One pass with a running best; only candidates that clear the gain threshold can replace it, and ties go to the earlier version.\"", "max_subarray"))

# ---- platform (Azure Databricks IaC)
lesson("summarize_plan", "What a Terraform plan really says",
 ["`terraform plan` compares your code with **state** (what Terraform last applied) and reality, then lists what it will create, update, replace or destroy.",
  "`terraform show -json` gives the same plan as data. Spacelift policies and PR checks read this JSON, not the text."],
 ("From plan to JSON", "terraform plan -out tfplan\nterraform show -json tfplan > plan.json"),
 ("The plan says \"1 to add, 0 to change, 1 to destroy\" for one resource. What is happening to it?",
  ["Nothing", "It's being replaced: destroyed and created again", "It's being renamed"], 1,
  "A replacement counts once as an add and once as a destroy."),
 ("Counting in one pass", "Three counters, one pass over `resource_changes`: O(n).", "\"I walk the resource changes once and count by action, treating a replacement as both an add and a destroy, the way Terraform does.\"", None))

lesson("find_replacements", "Spotting dangerous replacements",
 ["Some attributes can't change in place. Changing them **forces replacement**: Terraform destroys the resource and creates a new one.",
  "On an Azure Databricks workspace, that means a new URL and losing everything inside it. Always find every `-/+` in a plan before approving."],
 ("In the text plan", "-/+ resource \"azurerm_databricks_workspace\" \"this\" {\n  ~ managed_resource_group_name = \"a\" -> \"b\" # forces replacement"),
 ("Which change to `azurerm_databricks_workspace` forces a replacement?",
  ["Adding a tag", "Changing `managed_resource_group_name`", "Nothing can"], 1,
  "Tags update in place; the managed resource group name can't change, so the workspace is recreated."),
 ("Filter", "Keep entries matching a condition, in order: O(n).", "\"I filter the resource changes for actions containing both delete and create, which is how a replacement appears in plan JSON.\"", None))

lesson("guard_destroys", "Policies as guardrails",
 ["A **plan policy** runs automatically on every Spacelift run and can warn or block based on the plan. It's code review that never gets tired.",
  "Start with the resources you can't rebuild: workspaces, storage accounts, metastores."],
 ("The same rule in Rego", "deny contains msg if {\n  rc := input.terraform.resource_changes[_]\n  \"delete\" in rc.change.actions\n  rc.type in protected\n  msg := sprintf(\"%s would be destroyed\", [rc.address])\n}"),
 ("A plan policy blocks destroying storage accounts. Can someone still lose one?",
  ["No, it's fully protected", "Yes, by deleting it in the portal or with state commands, which never go through a plan", "Only if the policy has a bug"], 1,
  "Policies only see plans. Pair them with RBAC and resource locks."),
 ("Set lookup inside a filter", "Turn the protected types into a set so each check is O(1): O(n) overall.", "\"I put protected types in a set and filter the plan once, so the policy is linear in the number of changes.\"", "two_sum"))

lesson("lock_info", "State and locking",
 ["**State** is Terraform's record of what it manages. Two runs writing it at once would corrupt it, so runs take a **lock** first.",
  "A crashed run can leave the lock behind. Before `terraform force-unlock`, check who holds it and whether that run is really dead."],
 ("The error you'll see", "Error: Error acquiring the state lock\nError message: state blob is already locked\nLock Info:\n  ID:  6a3c...\n  Who: spacelift@worker-7"),
 ("When is it safe to run `terraform force-unlock`?",
  ["Whenever a run is blocked", "Only after confirming the run holding the lock has stopped", "Never"], 1,
  "Unlocking while a run is still applying lets two applies write state at once."),
 ("Parsing text", "One pass over the lines, splitting on the first colon only: O(n).", "\"I scan once, switch on at the Lock Info header, and split each line on the first colon so timestamps stay intact.\"", None))

lesson("missing_tags", "Tagging for cost and policy",
 ["Azure tags drive **cost allocation** and **Azure Policy**. Missing tags mean spend nobody can attribute.",
  "azurerm has no provider-wide default tags, so teams merge a shared `local.tags` into every resource, and check plans for gaps."],
 ("A shared tag map", "locals {\n  tags = { env = var.env, owner = \"platform\", cost-center = \"1234\" }\n}\ntags = merge(local.tags, { component = \"dbw\" })"),
 ("Which resource in this plan should your tag check skip?",
  ["`azurerm_databricks_workspace`", "`databricks_catalog` (it has no Azure tags)", "`azurerm_storage_account`"], 1,
  "Databricks resources aren't Azure resources, so they have no tags attribute."),
 ("Dict of results", "One pass; each missing-key check is a dict lookup: O(n × k) for k required tags.", "\"I only report resources that support tags, treat null as empty, and return a dict from address to sorted missing keys.\"", None))

lesson("grants_to_revoke", "Unity Catalog grants",
 ["**Unity Catalog** controls who can use which data. `databricks_grants` is **authoritative**: on apply it makes the grants match the code exactly, removing anything else.",
  "Grants added by hand in Catalog Explorer disappear at the next apply. Put them in code, or use the non-authoritative `databricks_grant` for that principal."],
 ("Authoritative grants", "resource \"databricks_grants\" \"sales\" {\n  catalog = databricks_catalog.sales.name\n  grant {\n    principal  = \"data-engineers\"\n    privileges = [\"USE_CATALOG\", \"USE_SCHEMA\", \"SELECT\"]\n  }\n}"),
 ("Someone gave `analysts` SELECT in the UI. The code uses `databricks_grants` without analysts. What happens at the next apply?",
  ["Nothing", "The analysts' grant is removed", "The apply fails"], 1,
  "Authoritative means the code is the whole list."),
 ("Set difference", "Per principal, live minus code: O(total privileges).", "\"For each principal I take the live privileges minus the ones in code; whatever is left is what an authoritative apply will revoke.\"", None))

lesson("count_shift", "count vs for_each",
 ["`count` names copies by position (`[0]`, `[1]`); `for_each` names them by key (`[\"bronze\"]`).",
  "Remove the first item from a `count` list and every later item shifts position. Terraform sees changed names and replaces them, and for storage containers that deletes their data. Use `for_each`, and `moved` blocks to migrate."],
 ("Migrating safely", "moved {\n  from = azurerm_storage_container.lake[1]\n  to   = azurerm_storage_container.lake[\"silver\"]\n}"),
 ("Containers are `[\"bronze\", \"silver\", \"gold\"]` with `count`. You remove \"bronze\". What does the plan do?",
  ["Deletes bronze only", "Replaces silver and gold, and deletes the last position", "Nothing"], 1,
  "Position 0 becomes silver and position 1 becomes gold, so both are renamed and replaced, and position 2 goes away."),
 ("Position-by-position comparison", "Walk both lists up to the longer one: O(n).", "\"I compare by index up to the longer list; a different name at the same index is a replacement, which is why keys beat positions.\"", None))

lesson("overlapping_subnets", "Networking for Databricks",
 ["**VNet injection** puts a Databricks workspace's clusters in your own virtual network, using a **host** and a **container** subnet. They must not overlap each other or anything they connect to.",
  "Each node uses an address in each subnet, and Azure reserves 5 per subnet, so size them for the clusters you'll need."],
 ("CIDR as a range", "10.20.0.0/24 -> 256 addresses: 10.20.0.0 to 10.20.0.255\n10.20.0.0/22 -> 1024 addresses: 10.20.0.0 to 10.20.3.255"),
 ("Do 10.20.0.0/22 and 10.20.2.0/24 overlap?",
  ["No", "Yes: the /24 is inside the /22", "Only if they're in different VNets"], 1,
  "The /22 runs to 10.20.3.255, which covers all of 10.20.2.x."),
 ("Interval overlap", "Turn each CIDR into a [start, end] range; two ranges overlap when each starts before the other ends. Checking every pair is O(n²); sorting by start and sweeping is O(n log n), like Merge Intervals.",
  "\"I convert CIDRs to integer ranges; sorted by start, an overlap is any range starting before the previous one ends.\"", "merge_intervals"))

lesson("apply_order", "Dependencies and stacks",
 ["Terraform builds a **dependency graph** from references between resources and creates things in an order that respects it. A loop in that graph is `Error: Cycle`.",
  "A Databricks provider configured from a workspace that doesn't exist yet can't plan. Split the workspace and its contents into separate Spacelift stacks, with a **stack dependency** between them."],
 ("An implicit dependency", "resource \"databricks_metastore_assignment\" \"this\" {\n  workspace_id = azurerm_databricks_workspace.this.workspace_id\n  metastore_id = var.metastore_id\n}"),
 ("Why does a separate stack for workspace contents help on the first deploy?",
  ["It's faster", "The workspace URL exists by the time the second stack plans", "Spacelift requires one stack per provider"], 1,
  "The provider needs a real URL at plan time, which only exists after the first stack applies."),
 ("Topological sort", "Count each node's unmet dependencies, start with those at zero, and release dependents as you go (Kahn's algorithm): O(V + E). Graph problems like Number of Islands use the same build-a-graph-then-traverse thinking.",
  "\"Kahn's algorithm: in-degree counts and a queue of ready nodes, O(V + E); if not every node is output, there's a cycle.\"", "num_islands"))

# ---- agentops
lesson("slowest_chain", "Reading agent traces",
 ["A **trace** records one agent run as nested **spans**: the run, each model call, each tool call, each HTTP request inside a tool. MLflow Tracing and LangSmith show them as a tree.",
  "To find what's slow, start at the root and follow the slowest child down. The answer is usually one tool or one model call."],
 ("Spans form a tree", "agent_run      4200 ms\n├─ plan           600 ms\n├─ tool:search   3100 ms\n│  └─ http_get   2900 ms\n└─ answer         400 ms"),
 ("A parent span took 4200 ms and its children took 600, 3100 and 400 ms. How long did the parent take on its own?",
  ["4200 ms", "100 ms", "8300 ms"], 1,
  "Parent time includes its children: 4200 − (600 + 3100 + 400) = 100 ms of its own."),
 ("Tree traversal", "Build a parent → children map in one pass (O(n)), then walk down one path. Number of Islands also builds structure first and then traverses it.",
  "\"I index children by parent id in one pass, then greedily descend into the slowest child until I hit a leaf.\"", "num_islands"))

lesson("detect_loop", "Guardrails for agents",
 ["Agents in production need **guardrails**: limits that stop a run before it does damage or burns money. The simplest catches the same call repeated again and again.",
  "Production systems also cap total steps, tokens and time, and tell the model why it was stopped."],
 ("A loop in a trace", "search('weather paris')\nsearch('weather paris')\nsearch('weather paris')   # stop here"),
 ("An agent alternates between two calls forever: A, B, A, B. Does a \"same call N times in a row\" check catch it?",
  ["Yes", "No, so you also need a total step limit", "Only with limit 2"], 1,
  "No call repeats back to back, so you need other limits too."),
 ("Run-length counting", "One pass, counting the current run and resetting when the item changes: O(n). Sliding-window problems track a run in the same way.",
  "\"One pass with a counter for the current run of identical calls, reset whenever the call changes.\"", "longest_unique_substring"))

assert all(l in L for _, _, _, ls in MODULES for l in ls), [l for _, _, _, ls in MODULES for l in ls if l not in L]
assert len(L) == sum(len(ls) for *_, ls in MODULES)
print(len(L), "lessons OK")
