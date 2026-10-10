"""11 new Build exercises for the learning path. Run to verify solutions and guided fills."""
import json
P = []
def add(**k): P.append(k)

add(id="split_by_key", title="Split Without Leaking", topic="foundations", difficulty="easy", fn="split_by_key",
 prompt="`rows` is a list of dicts like `{\"user\": \"u1\", \"text\": \"refund please\", \"label\": 1}`. Split them into training and test sets by one field: every row whose value for `key` is in `test_values` goes to test, the rest go to training. Keep the original order in both.\n\nReturn `[train, test]`.",
 pattern="Turn the test values into a set, then one pass that sends each row left or right.",
 target="one pass over the rows",
 realworld="Splitting by user (or by document, or by day) instead of row by row keeps the same person out of both sides. Otherwise the model is tested on people it has already seen, and the score looks better than it will be in production.",
 starter="def split_by_key(rows, key, test_values):\n    # your code here\n    pass\n",
 solution="def split_by_key(rows, key, test_values):\n    test_set = set(test_values)\n    train, test = [], []\n    for row in rows:\n        if row[key] in test_set:\n            test.append(row)\n        else:\n            train.append(row)\n    return [train, test]\n",
 cases=[
  ([{"user": "u1", "label": 1}, {"user": "u2", "label": 0}, {"user": "u1", "label": 0}, {"user": "u3", "label": 1}], "user", ["u1"], [[{"user": "u2", "label": 0}, {"user": "u3", "label": 1}], [{"user": "u1", "label": 1}, {"user": "u1", "label": 0}]], True),
  ([], "user", ["u1"], [[], []]),
  ([{"doc": "a"}, {"doc": "b"}], "doc", [], [[{"doc": "a"}, {"doc": "b"}], []]),
  ([{"day": "2026-10-01"}, {"day": "2026-10-02"}, {"day": "2026-10-03"}], "day", ["2026-10-03", "2026-10-02"], [[{"day": "2026-10-01"}], [{"day": "2026-10-02"}, {"day": "2026-10-03"}]]),
 ],
 guided="def split_by_key(rows, key, test_values):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: a set makes \"is this value a test value?\" instant.\n    test_set = set(test_values)\n    train, test = [], []\n\n    for row in rows:\n        # Step 2: look up this row's value for the key, and check the set.\n        if ___ in test_set:\n            test.append(row)\n        else:\n            ___\n\n    return [train, test]\n",
 fills=["row[key]", "train.append(row)"],
 learn=dict(
  concepts=[["Set membership", "`x in some_set` is instant. `x in some_list` checks every item.", "test_set = set(['u1', 'u7'])\n'u1' in test_set   # True"],
            ["Dict access", "`row['user']` gets one field of a row. `row[key]` works when the field name is in a variable.", "row = {'user': 'u1'}\nkey = 'user'\nrow[key]   # 'u1'"]],
  byhand="Test users: u1. Row 1 is u1: test. Row 2 is u2: train. Row 3 is u1: test. Row 4 is u3: train. Train is rows 2 and 4, test is rows 1 and 3, each in their original order.",
  why="One pass over the rows; each set check is instant.",
  gotchas=[["Duplicates leak too", "The same text can appear under two users (copied tickets, templates). Remove duplicates before splitting, or the test set still contains things the model trained on."],
           ["Time order matters", "For anything that predicts the future, split by date: train on the past, test on later data. A random split lets the model peek ahead."]]))

add(id="precision_recall", title="Precision and Recall", topic="foundations", difficulty="easy", fn="precision_recall",
 prompt="A classifier predicts 1 (yes) or 0 (no). `preds` are its predictions and `labels` are the right answers, in the same order.\n\nCount true positives (predicted 1, really 1), false positives (predicted 1, really 0) and false negatives (predicted 0, really 1). Then:\n\n- precision = true positives / (true positives + false positives)\n- recall = true positives / (true positives + false negatives)\n\nReturn `[precision, recall]`, each rounded to 2 decimal places. If a bottom number is 0, that value is `0.0`.",
 pattern="Count three things in one pass, then divide, guarding each division.",
 target="one pass over the pairs",
 realworld="Accuracy hides problems when one class is rare. A fraud model that always says \"not fraud\" is 99% accurate and catches nothing: its recall is 0. Precision and recall show the trade-off you actually have to choose.",
 starter="def precision_recall(preds, labels):\n    # your code here\n    pass\n",
 solution="def precision_recall(preds, labels):\n    tp = fp = fn = 0\n    for p, y in zip(preds, labels):\n        if p == 1 and y == 1:\n            tp += 1\n        elif p == 1 and y == 0:\n            fp += 1\n        elif p == 0 and y == 1:\n            fn += 1\n    precision = round(tp / (tp + fp), 2) if tp + fp else 0.0\n    recall = round(tp / (tp + fn), 2) if tp + fn else 0.0\n    return [precision, recall]\n",
 cases=[([1, 1, 0, 1, 0], [1, 0, 0, 1, 1], [0.67, 0.67], True), ([1, 0, 0], [1, 1, 1], [1.0, 0.33]), ([0, 0], [0, 0], [0.0, 0.0]), ([1, 1], [0, 0], [0.0, 0.0]), ([], [], [0.0, 0.0]), ([1, 1, 1, 1], [1, 1, 1, 0], [0.75, 1.0])],
 guided="def precision_recall(preds, labels):\n    # Replace every ___ with real code, then run the tests.\n\n    tp = fp = fn = 0\n    # Step 1: zip walks both lists side by side.\n    for p, y in zip(preds, labels):\n        if p == 1 and y == 1:\n            tp += 1\n        elif ___:\n            fp += 1\n        elif p == 0 and y == 1:\n            fn += 1\n\n    # Step 2: divide, but only when the bottom number isn't 0.\n    precision = round(tp / (tp + fp), 2) if tp + fp else 0.0\n    recall = ___\n    return [precision, recall]\n",
 fills=["p == 1 and y == 0", "round(tp / (tp + fn), 2) if tp + fn else 0.0"],
 learn=dict(
  concepts=[["zip", "Walks two lists side by side.", "for p, y in zip([1, 0], [1, 1]):\n    print(p, y)"],
            ["A one-line if", "`a if condition else b` picks one of two values.", "x = 10 / n if n else 0.0"]],
  byhand="Pairs: (1,1) true positive, (1,0) false positive, (0,0) nothing, (1,1) true positive, (0,1) false negative. So tp=2, fp=1, fn=1. Precision 2/3 = 0.67, recall 2/3 = 0.67.",
  why="One pass to count, then two divisions.",
  gotchas=[["Pick the metric before training", "Missing fraud (low recall) and blocking good customers (low precision) cost different amounts. Decide which matters more first, or you'll pick whichever number looks best."],
           ["Averages across classes", "With more than two classes, macro-average treats every class equally and micro-average weights by size. They can tell very different stories."]]))

add(id="best_threshold", title="Choose a Decision Threshold", topic="foundations", difficulty="medium", fn="best_threshold",
 prompt="A model gives each example a score between 0 and 1. You turn scores into decisions with a threshold: predict 1 when `score >= t`, otherwise 0.\n\nTry every score in `scores` as the threshold `t`. Return `[t, accuracy]` for the threshold with the highest accuracy (share of decisions that match `labels`), with accuracy rounded to 2 places. If several thresholds tie, return the highest of them. There is at least one score.",
 pattern="Try each candidate, keep the best so far. Sorting first lets you update the count in one sweep instead of recounting.",
 target="trying each score is fine here; the fast version sorts once and sweeps",
 realworld="Classifiers output scores, and someone has to choose where to cut. Teams tune the threshold on a validation set, never on the test set, and often for precision or recall rather than accuracy.",
 starter="def best_threshold(scores, labels):\n    # your code here\n    pass\n",
 solution="def best_threshold(scores, labels):\n    best_t, best_acc = None, -1\n    for t in scores:\n        right = 0\n        for s, y in zip(scores, labels):\n            pred = 1 if s >= t else 0\n            if pred == y:\n                right += 1\n        acc = right / len(scores)\n        if acc > best_acc or (acc == best_acc and t > best_t):\n            best_t, best_acc = t, acc\n    return [best_t, round(best_acc, 2)]\n",
 cases=[([0.9, 0.2, 0.65, 0.4], [1, 0, 1, 0], [0.65, 1.0], True), ([0.5], [1], [0.5, 1.0]), ([0.3, 0.8, 0.6], [0, 0, 1], [0.6, 0.67]), ([0.1, 0.9], [1, 0], [0.1, 0.5]), ([0.7, 0.7, 0.2], [1, 0, 0], [0.7, 0.67])],
 guided="def best_threshold(scores, labels):\n    # Replace every ___ with real code, then run the tests.\n\n    best_t, best_acc = None, -1\n    # Step 1: try every score as the threshold.\n    for t in scores:\n        right = 0\n        for s, y in zip(scores, labels):\n            # Step 2: the decision for this example at threshold t.\n            pred = ___\n            if pred == y:\n                right += 1\n        acc = right / len(scores)\n        # Step 3: better accuracy wins; on a tie, the higher threshold wins.\n        if acc > best_acc or ___:\n            best_t, best_acc = t, acc\n    return [best_t, round(best_acc, 2)]\n",
 fills=["1 if s >= t else 0", "(acc == best_acc and t > best_t)"],
 learn=dict(
  concepts=[["Nested loops", "A loop inside a loop runs the inner one completely for every outer item. With n scores that's n × n steps.", "for t in scores:\n    for s in scores:\n        ..."],
            ["Keeping the best so far", "Start with a value anything beats, and replace it when you find better.", "best = -1\nfor x in [3, 7, 5]:\n    if x > best:\n        best = x"]],
  byhand="Threshold 0.65: 0.9 → 1 (right), 0.2 → 0 (right), 0.65 → 1 (right), 0.4 → 0 (right). 4 of 4. No threshold beats 1.0, so the answer is [0.65, 1.0].",
  why="Trying every threshold and checking every example is O(n²). Sorting by score first lets you move the threshold one example at a time and update the count, which is O(n log n).",
  gotchas=[["Tuning on the test set", "If you pick the threshold using the test set, the test score is no longer an honest estimate. Use a separate validation set."],
           ["Thresholds drift", "When the incoming data changes, the scores shift and yesterday's best threshold quietly gets worse. Monitor the rate of positive predictions."]]))

add(id="dedupe_chunks", title="Remove Duplicate Chunks", topic="rag", difficulty="easy", fn="dedupe_chunks",
 prompt="The same text shows up many times in a document collection: footers, disclaimers, copied paragraphs. Given a list of `chunks`, remove duplicates, where two chunks count as the same if they match after lowercasing and squeezing all runs of whitespace (spaces, newlines, tabs) to single spaces, with the ends trimmed.\n\nKeep the first copy of each, unchanged, in the original order.",
 pattern="Design a key that is equal exactly when two things should count as the same, then remember the keys you've seen.",
 target="one pass over the chunks",
 realworld="Duplicates waste embedding money and crowd retrieval: if the top 5 results are the same disclaimer five times, the model never sees the paragraph that answers the question.",
 starter="def dedupe_chunks(chunks):\n    # your code here\n    pass\n",
 solution="def dedupe_chunks(chunks):\n    seen = set()\n    out = []\n    for chunk in chunks:\n        key = \" \".join(chunk.lower().split())\n        if key not in seen:\n            seen.add(key)\n            out.append(chunk)\n    return out\n",
 cases=[(["Refunds take 5 days.", "All rights reserved.", "refunds   take 5 days.", "ALL RIGHTS\nRESERVED."], ["Refunds take 5 days.", "All rights reserved."], True), ([], []), (["a", "b", "a "], ["a", "b"]), (["Hi there", "hi\tthere", "hithere"], ["Hi there", "hithere"])],
 guided="def dedupe_chunks(chunks):\n    # Replace every ___ with real code, then run the tests.\n\n    seen = set()   # keys you've already kept\n    out = []\n    for chunk in chunks:\n        # Step 1: the key: lowercase, then split() and join with single spaces.\n        key = \" \".join(___)\n        # Step 2: first time you see this key? Keep the chunk.\n        if key not in seen:\n            seen.add(key)\n            ___\n    return out\n",
 fills=["chunk.lower().split()", "out.append(chunk)"],
 learn=dict(
  concepts=[["split with no argument", "Splits on any run of whitespace, including newlines and tabs, and drops empty pieces.", "'a  b\\nc'.split()   # ['a', 'b', 'c']"],
            ["A set of seen keys", "Add each key after you use it; check before adding.", "seen = set()\nseen.add('x')\n'x' in seen   # True"]],
  byhand="\"Refunds take 5 days.\" becomes the key \"refunds take 5 days.\". Keep it. \"refunds   take 5 days.\" gives the same key: skip. The two disclaimers both become \"all rights reserved.\": keep the first only.",
  why="One pass; each key check is a set lookup.",
  gotchas=[["Near-duplicates", "Exact keys miss text that differs by a date or a name. Real pipelines also use hashing tricks such as MinHash to catch near-duplicates."],
           ["Dedupe before you embed", "Embedding costs money per token. Removing duplicates first is the cheapest optimisation in most RAG pipelines."]]))

add(id="tool_pairs", title="Match Tool Calls to Results", topic="agents", difficulty="medium", fn="tool_pairs",
 prompt="In a tool-using chat, the assistant asks for tools and each request gets an id. Each result message must answer one of those ids.\n\n`messages` is a list of dicts. An assistant message may have `\"tool_calls\"`, a list like `[{\"id\": \"call_1\", \"name\": \"search\"}]`. A tool result looks like `{\"role\": \"tool\", \"tool_call_id\": \"call_1\"}`. Other messages have neither.\n\nReturn `[unanswered, orphans]`: the ids of calls that never got a result, and the ids of results that don't answer an earlier, still-open call. Both in the order they appear.",
 pattern="Matching pairs: open something, close it later. Track what's open, and complain about anything closed that wasn't open.",
 target="one pass over the messages",
 realworld="Model APIs reject a conversation where a tool call has no result. This usually happens after trimming chat history cuts a call away from its result, and it shows up as a confusing 400 error in production.",
 starter="def tool_pairs(messages):\n    # your code here\n    pass\n",
 solution="def tool_pairs(messages):\n    open_ids = []\n    orphans = []\n    for m in messages:\n        for call in m.get(\"tool_calls\", []):\n            open_ids.append(call[\"id\"])\n        if m.get(\"role\") == \"tool\":\n            cid = m[\"tool_call_id\"]\n            if cid in open_ids:\n                open_ids.remove(cid)\n            else:\n                orphans.append(cid)\n    return [open_ids, orphans]\n",
 cases=[
  ([{"role": "user", "content": "weather in Paris and Rome?"}, {"role": "assistant", "tool_calls": [{"id": "call_1", "name": "weather"}, {"id": "call_2", "name": "weather"}]}, {"role": "tool", "tool_call_id": "call_1", "content": "22C"}], [["call_2"], []], True),
  ([], [[], []]),
  ([{"role": "tool", "tool_call_id": "call_9"}, {"role": "assistant", "tool_calls": [{"id": "call_9", "name": "search"}]}], [["call_9"], ["call_9"]]),
  ([{"role": "assistant", "tool_calls": [{"id": "a", "name": "x"}]}, {"role": "tool", "tool_call_id": "a"}, {"role": "tool", "tool_call_id": "a"}], [[], ["a"]]),
  ([{"role": "assistant", "content": "hello"}, {"role": "assistant", "tool_calls": [{"id": "c1", "name": "x"}, {"id": "c2", "name": "y"}]}, {"role": "tool", "tool_call_id": "c2"}, {"role": "tool", "tool_call_id": "c1"}], [[], []]),
 ],
 guided="def tool_pairs(messages):\n    # Replace every ___ with real code, then run the tests.\n\n    open_ids = []   # calls waiting for a result, in order\n    orphans = []\n    for m in messages:\n        # Step 1: every call this message makes is now open.\n        #         .get(\"tool_calls\", []) is empty for messages without calls.\n        for call in m.get(\"tool_calls\", []):\n            ___\n\n        # Step 2: a tool result closes its call, if that call is open.\n        if m.get(\"role\") == \"tool\":\n            cid = m[\"tool_call_id\"]\n            if ___:\n                open_ids.remove(cid)\n            else:\n                orphans.append(cid)\n\n    return [open_ids, orphans]\n",
 fills=["open_ids.append(call[\"id\"])", "cid in open_ids"],
 learn=dict(
  concepts=[["dict.get with a default", "Returns the default when the key isn't there, so messages without tool calls just give an empty list.", "m = {'role': 'user'}\nm.get('tool_calls', [])   # []"],
            ["list.remove", "Removes the first matching item.", "ids = ['a', 'b']\nids.remove('a')   # ids is ['b']"]],
  byhand="The assistant opens call_1 and call_2. The tool result answers call_1, so it closes. Nothing answers call_2, so it's unanswered. No result arrived for a call that wasn't open, so there are no orphans.",
  why="One pass. Removing from a list is O(n), which is fine for a handful of open calls; a dict or set makes it instant.",
  gotchas=[["Trim in pairs", "When you cut old messages, never separate a tool call from its result. Treat them as one unit."],
           ["Parallel calls", "Models can request several tools at once. Every one needs a result before the next model call, even if a tool failed: send the error as the result."]]))

add(id="first_bad_version", title="Find the Change That Broke It", topic="evals", difficulty="easy", fn="first_bad_version",
 prompt="You changed a prompt many times, and somewhere along the way the eval started failing. `passed` lists, for each version in order, whether it passes: all the passing versions come first, then all the failing ones.\n\nReturn the index of the first failing version, or `-1` if every version passes. Each eval costs money, so look at as few versions as possible: about log n of them, not all n.",
 pattern="The list is sorted (passes, then fails), so check the middle and throw away the half that can't contain the answer.",
 target="O(log n): about 10 checks for 1,000 versions",
 realworld="Bisecting: finding which of 40 prompt or model changes broke an eval in about 6 runs instead of 40. `git bisect` does exactly this for code.",
 starter="def first_bad_version(passed):\n    # your code here\n    pass\n",
 solution="def first_bad_version(passed):\n    lo, hi = 0, len(passed) - 1\n    answer = -1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if passed[mid]:\n            lo = mid + 1\n        else:\n            answer = mid\n            hi = mid - 1\n    return answer\n",
 cases=[([True, True, False, False], 2, True), ([True, True, True], -1), ([False], 0), ([], -1), ([True] * 1000 + [False] * 24, 1000), ([True, False], 1)],
 guided="def first_bad_version(passed):\n    # Replace every ___ with real code, then run the tests.\n\n    lo, hi = 0, len(passed) - 1\n    answer = -1   # best failing index found so far\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if passed[mid]:\n            # Step 1: mid passes, so the first failure is to its right.\n            lo = ___\n        else:\n            # Step 2: mid fails. Remember it, then look left for an earlier one.\n            answer = mid\n            hi = ___\n    return answer\n",
 fills=["mid + 1", "mid - 1"],
 learn=dict(
  concepts=[["Integer division", "`//` divides and rounds down, so the result works as an index.", "(0 + 9) // 2   # 4"],
            ["Remember and keep looking", "When you find a failing version, it might not be the first. Save it, then search the left half.", "answer = mid\nhi = mid - 1"]],
  byhand="[pass, pass, fail, fail]. Middle is index 1: passes, so look right of it. Now indexes 2 to 3, middle 2: fails. Remember 2, look left: nothing left. Answer 2.",
  why="Each check halves what's left, so 1,000 versions take about 10 checks.",
  gotchas=[["Flaky evals break bisecting", "If a version passes on one run and fails on the next, bisecting lands in the wrong place. Run each check more than once, or lower the randomness, before you trust it."],
           ["Version everything", "You can only bisect what you kept. Store each prompt version, model name and settings with every eval run, which is what MLflow runs are for."]]))

add(id="token_cost", title="Cost per Model", topic="llmops", difficulty="easy", fn="token_cost",
 prompt="Each LLM call in `calls` looks like `{\"model\": \"fast-model\", \"input_tokens\": 1200, \"output_tokens\": 300}`. `prices` maps each model to `[input_price, output_price]` in dollars per million tokens.\n\nReturn a dict from model to its total cost in dollars, rounded to 4 decimal places. Every model in `calls` is in `prices`. The prices are made up.",
 pattern="Group by a key and add up into a dict.",
 target="one pass over the calls",
 realworld="LLM bills are per token, and output tokens usually cost several times more than input. Breaking cost down by model (and by feature or user) is the first thing a team does when the bill jumps.",
 starter="def token_cost(calls, prices):\n    # your code here\n    pass\n",
 solution="def token_cost(calls, prices):\n    totals = {}\n    for c in calls:\n        inp, out = prices[c[\"model\"]]\n        cost = (c[\"input_tokens\"] * inp + c[\"output_tokens\"] * out) / 1000000\n        totals[c[\"model\"]] = totals.get(c[\"model\"], 0) + cost\n    return {m: round(v, 4) for m, v in totals.items()}\n",
 cases=[
  ([{"model": "fast-model", "input_tokens": 1200, "output_tokens": 300}, {"model": "smart-model", "input_tokens": 2000, "output_tokens": 500}, {"model": "fast-model", "input_tokens": 800, "output_tokens": 200}], {"fast-model": [1, 5], "smart-model": [3, 15]}, {"fast-model": 0.0045, "smart-model": 0.0135}, True),
  ([], {"fast-model": [1, 5]}, {}),
  ([{"model": "smart-model", "input_tokens": 1000000, "output_tokens": 0}], {"smart-model": [3, 15]}, {"smart-model": 3.0}),
  ([{"model": "a", "input_tokens": 10, "output_tokens": 10}, {"model": "a", "input_tokens": 10, "output_tokens": 10}], {"a": [2, 8]}, {"a": 0.0002}),
 ],
 guided="def token_cost(calls, prices):\n    # Replace every ___ with real code, then run the tests.\n\n    totals = {}\n    for c in calls:\n        # Step 1: this model's two prices.\n        inp, out = prices[c[\"model\"]]\n        # Step 2: prices are per MILLION tokens.\n        cost = (c[\"input_tokens\"] * inp + ___) / 1000000\n        # Step 3: add to this model's running total (0 the first time).\n        totals[c[\"model\"]] = ___ + cost\n    return {m: round(v, 4) for m, v in totals.items()}\n",
 fills=["c[\"output_tokens\"] * out", "totals.get(c[\"model\"], 0)"],
 learn=dict(
  concepts=[["Adding up into a dict", "`d.get(k, 0) + x` adds to a running total that starts at 0.", "totals = {}\ntotals['a'] = totals.get('a', 0) + 5"],
            ["Unpacking a pair", "Two names, one list of two values.", "inp, out = [3, 15]"]],
  byhand="fast-model: (1200×1 + 300×5) / 1,000,000 = 0.0027, then (800×1 + 200×5) / 1,000,000 = 0.0018, total 0.0045. smart-model: (2000×3 + 500×15) / 1,000,000 = 0.0135.",
  why="One pass; each update is a dict lookup.",
  gotchas=[["Output tokens dominate", "A long answer can cost more than a long prompt. Capping output length is often the quickest saving."],
           ["Retries cost too", "Every retry and every agent step is billed. Count tokens per request in your traces, not just per user message."]]))

add(id="cache_hits", title="Count Cache Hits", topic="llmops", difficulty="medium", fn="cache_hits",
 prompt="Repeated prompts can be answered from a cache instead of calling the model again. The cache holds at most `capacity` prompts and evicts the least recently used one when full.\n\nGo through `prompts` in order. If a prompt is in the cache, that's a hit, and it becomes the most recently used. If not, add it as most recently used, evicting the least recently used prompt first if the cache is full. Return the number of hits. A capacity of 0 caches nothing.",
 pattern="An LRU cache: fast lookup plus an order of use. Here a list keeps the order: most recent at the end.",
 target="one pass over the prompts (the list makes each step O(capacity))",
 realworld="Prompt and response caching cuts cost and latency for repeated questions. Model providers also offer prompt caching for a shared prefix, priced lower than normal input tokens.",
 starter="def cache_hits(prompts, capacity):\n    # your code here\n    pass\n",
 solution="def cache_hits(prompts, capacity):\n    cache = []\n    hits = 0\n    if capacity == 0:\n        return 0\n    for p in prompts:\n        if p in cache:\n            hits += 1\n            cache.remove(p)\n        elif len(cache) == capacity:\n            cache.pop(0)\n        cache.append(p)\n    return hits\n",
 cases=[(["hi", "price?", "hi", "refund", "price?", "hi"], 2, 1, True), ([], 3, 0), (["a", "a", "a"], 1, 2), (["a", "b", "a"], 0, 0), (["a", "b", "c", "a", "b", "c"], 3, 3), (["a", "b", "c", "a", "b", "c"], 2, 0)],
 guided="def cache_hits(prompts, capacity):\n    # Replace every ___ with real code, then run the tests.\n\n    cache = []   # least recently used first, most recent last\n    hits = 0\n    if capacity == 0:\n        return 0\n    for p in prompts:\n        if p in cache:\n            # Step 1: a hit. Take it out so it can go to the end.\n            hits += 1\n            ___\n        elif len(cache) == capacity:\n            # Step 2: full. Evict the least recently used, at the front.\n            ___\n        # Step 3: p is now the most recently used.\n        cache.append(p)\n    return hits\n",
 fills=["cache.remove(p)", "cache.pop(0)"],
 learn=dict(
  concepts=[["pop(0)", "Removes and returns the first item.", "q = ['a', 'b']\nq.pop(0)   # 'a'"],
            ["Least recently used", "Every use moves an item to the back, so the front is always the one unused longest.", "# use 'a': ['b', 'c', 'a']"]],
  byhand="Capacity 2. hi: miss [hi]. price?: miss [hi, price?]. hi: hit, move it to the back [price?, hi]. refund: miss, full, evict price? → [hi, refund]. price?: miss, evict hi → [refund, price?]. hi: miss. One hit.",
  why="One pass. With a list each lookup and removal is O(capacity); the interview version uses a dict plus a linked list, or Python's OrderedDict, to make each step O(1).",
  gotchas=[["Exact-match caches miss paraphrases", "\"what's the price\" and \"how much is it\" are different keys. Semantic caches compare embeddings instead, at the risk of returning a wrong match."],
           ["Never cache across users by accident", "If answers depend on who's asking, the user (or their permissions) must be part of the cache key."]]))

add(id="promote_model", title="Promote a Challenger", topic="mlops", difficulty="medium", fn="promote_model",
 prompt="In a model registry, the `champion` alias points at the version serving traffic. `versions` is a list like `[{\"version\": 3, \"f1\": 0.81}, ...]` that includes the champion.\n\nReturn the version that should be champion: the version with the highest f1 that beats the current champion's f1 by at least `min_gain`. If several tie, pick the lowest version number. If none beats it by enough, keep the current champion.",
 pattern="Keep the best candidate so far, with a rule for ties, and only accept a new best that clears the bar.",
 target="one pass over the versions",
 realworld="MLflow's model registry uses aliases like `@champion` and `@challenger` for exactly this. Requiring a minimum gain stops you swapping models for noise-level differences, since every swap carries risk.",
 starter="def promote_model(versions, champion, min_gain):\n    # your code here\n    pass\n",
 solution="def promote_model(versions, champion, min_gain):\n    champ_f1 = None\n    for v in versions:\n        if v[\"version\"] == champion:\n            champ_f1 = v[\"f1\"]\n    best = champion\n    best_f1 = champ_f1\n    for v in versions:\n        if v[\"f1\"] - champ_f1 >= min_gain - 1e-9:\n            if v[\"f1\"] > best_f1 or (v[\"f1\"] == best_f1 and v[\"version\"] < best):\n                best, best_f1 = v[\"version\"], v[\"f1\"]\n    return best\n",
 cases=[
  ([{"version": 3, "f1": 0.81}, {"version": 4, "f1": 0.84}, {"version": 5, "f1": 0.82}], 3, 0.02, 4, True),
  ([{"version": 3, "f1": 0.81}, {"version": 4, "f1": 0.82}], 3, 0.02, 3),
  ([{"version": 1, "f1": 0.7}], 1, 0.01, 1),
  ([{"version": 2, "f1": 0.6}, {"version": 7, "f1": 0.9}, {"version": 5, "f1": 0.9}], 2, 0.05, 5),
  ([{"version": 4, "f1": 0.8}, {"version": 6, "f1": 0.75}], 4, 0.0, 4),
 ],
 guided="def promote_model(versions, champion, min_gain):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: find the current champion's score.\n    champ_f1 = None\n    for v in versions:\n        if v[\"version\"] == champion:\n            champ_f1 = v[\"f1\"]\n\n    best = champion\n    best_f1 = champ_f1\n    for v in versions:\n        # Step 2: only versions that beat the champion by at least min_gain.\n        #         (1e-9 absorbs tiny floating-point rounding.)\n        if ___ >= min_gain - 1e-9:\n            # Step 3: higher f1 wins; on a tie, the lower version number.\n            if v[\"f1\"] > best_f1 or ___:\n                best, best_f1 = v[\"version\"], v[\"f1\"]\n    return best\n",
 fills=["v[\"f1\"] - champ_f1", "(v[\"f1\"] == best_f1 and v[\"version\"] < best)"],
 learn=dict(
  concepts=[["Floating-point rounding", "0.84 - 0.81 is 0.02999999... in binary. Comparing against `min_gain - 1e-9` stops a tiny rounding error deciding the answer.", "0.84 - 0.81   # 0.029999999999999916"],
            ["Two passes", "First find a reference value, then compare everything against it.", "ref = ...\nfor v in versions:\n    ..."]],
  byhand="Champion v3 has 0.81, so a challenger needs 0.83 or more. v4 has 0.84: yes. v5 has 0.82: no. Best is v4.",
  why="Two passes over the versions, each O(n).",
  gotchas=[["Compare on the same data", "A challenger evaluated on a different test set isn't comparable. Log the dataset version with every metric."],
           ["Promote by alias, roll back by alias", "Pointing `@champion` at a new version is instant to undo, which is why aliases beat redeploying a new model URI."]]))

add(id="slowest_chain", title="Find the Slow Path in a Trace", topic="agentops", difficulty="medium", fn="slowest_chain",
 prompt="A trace records an agent run as spans: `{\"id\": \"s2\", \"parent\": \"s1\", \"name\": \"retrieve\", \"ms\": 840}`. The root span has `\"parent\": None`, and a span's time includes its children's.\n\nStart at the root. Repeatedly step into the child that took the longest (the first one listed wins a tie) until you reach a span with no children. Return the names along the way, root first. No spans gives `[]`.",
 pattern="Build a parent → children map, then walk down the tree.",
 target="one pass to build the map, one walk down",
 realworld="This is how you read a slow trace in MLflow Tracing or LangSmith: follow the slowest child at each level until you reach the step that's actually slow, usually one model call or one tool.",
 starter="def slowest_chain(spans):\n    # your code here\n    pass\n",
 solution="def slowest_chain(spans):\n    children = {}\n    root = None\n    for s in spans:\n        if s[\"parent\"] is None:\n            root = s\n        else:\n            children.setdefault(s[\"parent\"], []).append(s)\n    path = []\n    node = root\n    while node is not None:\n        path.append(node[\"name\"])\n        kids = children.get(node[\"id\"], [])\n        node = None\n        for k in kids:\n            if node is None or k[\"ms\"] > node[\"ms\"]:\n                node = k\n    return path\n",
 cases=[
  ([{"id": "s1", "parent": None, "name": "agent_run", "ms": 4200}, {"id": "s2", "parent": "s1", "name": "plan", "ms": 600}, {"id": "s3", "parent": "s1", "name": "tool:search", "ms": 3100}, {"id": "s4", "parent": "s3", "name": "http_get", "ms": 2900}, {"id": "s5", "parent": "s1", "name": "answer", "ms": 400}], ["agent_run", "tool:search", "http_get"], True),
  ([], []),
  ([{"id": "r", "parent": None, "name": "run", "ms": 10}], ["run"]),
  ([{"id": "c", "parent": "r", "name": "llm_a", "ms": 50}, {"id": "r", "parent": None, "name": "run", "ms": 120}, {"id": "d", "parent": "r", "name": "llm_b", "ms": 50}], ["run", "llm_a"]),
 ],
 guided="def slowest_chain(spans):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: find the root and build parent id -> list of child spans.\n    children = {}\n    root = None\n    for s in spans:\n        if s[\"parent\"] is None:\n            root = s\n        else:\n            children.setdefault(s[\"parent\"], []).append(s)\n\n    path = []\n    node = root\n    while node is not None:\n        path.append(node[\"name\"])\n        # Step 2: this span's children (none for a leaf).\n        kids = children.get(___, [])\n        # Step 3: step into the slowest child; the first wins a tie.\n        node = None\n        for k in kids:\n            if node is None or ___:\n                node = k\n    return path\n",
 fills=["node[\"id\"]", "k[\"ms\"] > node[\"ms\"]"],
 learn=dict(
  concepts=[["setdefault", "Gets a key's value, creating it with a default first if it's missing. Handy for dicts of lists.", "kids = {}\nkids.setdefault('s1', []).append('s2')"],
            ["is None", "The right way to check for None.", "if node is None:\n    ..."]],
  byhand="agent_run has three children: plan (600), tool:search (3100), answer (400). Step into tool:search. Its only child is http_get (2900). http_get has no children. Path: agent_run, tool:search, http_get. The slow part is an HTTP call inside a tool, not the model.",
  why="Building the map is one pass; the walk visits one span per level.",
  gotchas=[["Child time is inside parent time", "Don't add a parent's time to its children's; the parent already includes them. The gap between a parent and its slowest child is time spent in the parent itself."],
           ["Parallel children overlap", "When tools run at the same time, their times overlap. The slowest one sets the pace, not the sum."]]))

add(id="detect_loop", title="Stop a Looping Agent", topic="agentops", difficulty="easy", fn="detect_loop",
 prompt="An agent sometimes gets stuck making the same tool call over and over. `calls` is the list of calls it made, each `[tool, argument]`. Return the index of the call where the same call has now happened `limit` times in a row, so the run can be stopped there. If that never happens, return `-1`.\n\nFor `limit` 3, `[[\"search\", \"x\"], [\"search\", \"x\"], [\"search\", \"x\"]]` gives `2`.",
 pattern="Count the current run of identical items; reset the count when the item changes.",
 target="one pass over the calls",
 realworld="A guardrail every agent in production needs: without it, a model that keeps retrying the same search can loop until it hits the step limit, spending tokens the whole time.",
 starter="def detect_loop(calls, limit):\n    # your code here\n    pass\n",
 solution="def detect_loop(calls, limit):\n    run = 0\n    prev = None\n    for i, call in enumerate(calls):\n        if call == prev:\n            run += 1\n        else:\n            run = 1\n        prev = call\n        if run >= limit:\n            return i\n    return -1\n",
 cases=[([["search", "weather paris"], ["search", "weather paris"], ["calc", "2+2"], ["search", "weather paris"], ["search", "weather paris"], ["search", "weather paris"]], 3, 5, True), ([], 3, -1), ([["a", "1"]], 1, 0), ([["a", "1"], ["a", "2"], ["a", "1"]], 2, -1), ([["s", "q"], ["s", "q"]], 2, 1)],
 guided="def detect_loop(calls, limit):\n    # Replace every ___ with real code, then run the tests.\n\n    run = 0       # how many identical calls in a row so far\n    prev = None   # the call before this one\n    for i, call in enumerate(calls):\n        # Step 1: same as the previous call? The run grows. Otherwise it restarts at 1.\n        if call == prev:\n            run += 1\n        else:\n            run = ___\n        prev = call\n        # Step 2: reached the limit? Stop here.\n        if ___:\n            return i\n    return -1\n",
 fills=["1", "run >= limit"],
 learn=dict(
  concepts=[["Comparing lists", "`==` on two lists checks every item, in order.", "['search', 'x'] == ['search', 'x']   # True"],
            ["enumerate", "Gives the index along with each item.", "for i, call in enumerate(calls):\n    ..."]],
  byhand="search, search: run 2. calc: run resets to 1. search: 1, search: 2, search: 3 at index 5. Limit reached: return 5.",
  why="One pass with two variables.",
  gotchas=[["Loops aren't always identical", "Agents also alternate between two calls, or change one word each time. Production guardrails also cap total steps, total tokens and wall-clock time."],
           ["Tell the model why it stopped", "Returning a clear message (\"stopped: repeated the same search 3 times\") lets the agent change approach instead of failing silently."]]))

def check():
    for p in P:
        for variant in ("solution", "guided"):
            code = p["solution"] if variant == "solution" else p["guided"].replace("# Replace every ___ with real code, then run the tests.", "#")
            if variant == "guided":
                for f in p["fills"]:
                    assert "___" in code, (p["id"], "too many fills"); code = code.replace("___", f, 1)
                assert "___" not in code, (p["id"], "unfilled")
            ns = {}; exec(code, ns); fn = ns[p["fn"]]
            for c in p["cases"]:
                sample = c[-1] is True
                body = c[:-1] if sample else c
                args, exp = list(body[:-1]), body[-1]
                got = fn(*json.loads(json.dumps(args)))
                assert got == exp, (p["id"], variant, args, exp, got)
    print("verified", len(P), "new problems")
if __name__ == "__main__":
    check()
