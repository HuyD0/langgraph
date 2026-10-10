"""Experiment-design exercises (MLflow-anchored). Same shape as new_problems.py."""
import json
P = []
def add(**k): P.append(k)

add(id="best_run", title="Pick the Best Run", topic="experiments", difficulty="easy", fn="best_run",
 prompt="Each run in an experiment logged its settings and results. `runs` is a list like `{\"run_name\": \"cs512-k5\", \"quality\": 0.81, \"cost\": 1.8}`, where cost is dollars per 1,000 requests.\n\nReturn the `run_name` of the run with the highest `quality` among runs whose `cost` is at most `max_cost`. If two tie on quality, pick the cheaper one. If no run is cheap enough, return `None`.",
 pattern="Filter by the constraint first, then keep the best so far with a tie rule.",
 target="one walk through the runs",
 realworld="This is what `mlflow.search_runs` with a filter and an order does. Deciding the constraint (budget, latency) before looking at results stops you picking whatever looks best afterwards.",
 starter="def best_run(runs, max_cost):\n    # your code here\n    pass\n",
 solution="def best_run(runs, max_cost):\n    best = None\n    for r in runs:\n        if r[\"cost\"] > max_cost:\n            continue\n        if best is None or r[\"quality\"] > best[\"quality\"] or (r[\"quality\"] == best[\"quality\"] and r[\"cost\"] < best[\"cost\"]):\n            best = r\n    return best[\"run_name\"] if best else None\n",
 cases=[([{"run_name": "cs256-k3", "quality": 0.74, "cost": 1.1}, {"run_name": "cs512-k5", "quality": 0.81, "cost": 1.8}, {"run_name": "cs1024-k10", "quality": 0.84, "cost": 3.2}], 2.0, "cs512-k5", True),
        ([], 5.0, None),
        ([{"run_name": "a", "quality": 0.9, "cost": 9.0}], 1.0, None),
        ([{"run_name": "a", "quality": 0.8, "cost": 2.0}, {"run_name": "b", "quality": 0.8, "cost": 1.5}], 2.0, "b"),
        ([{"run_name": "a", "quality": 0.7, "cost": 1.0}, {"run_name": "b", "quality": 0.75, "cost": 1.0}], 1.0, "b")],
 guided="def best_run(runs, max_cost):\n    # Replace every ___ with real code, then run the tests.\n\n    best = None\n    for r in runs:\n        # Step 1: skip runs over budget.\n        if ___:\n            continue\n        # Step 2: better quality wins; equal quality, the cheaper one wins.\n        if best is None or r[\"quality\"] > best[\"quality\"] or ___:\n            best = r\n    # Step 3: the name, or None if nothing fit the budget.\n    return best[\"run_name\"] if best else None\n",
 fills=["r[\"cost\"] > max_cost", "(r[\"quality\"] == best[\"quality\"] and r[\"cost\"] < best[\"cost\"])"],
 learn=dict(concepts=[["continue", "Skips the rest of this loop turn.", "for r in runs:\n    if r['cost'] > 2:\n        continue\n    ..."], ["None as \"nothing yet\"", "Start with None and replace it with the first real candidate.", "best = None\nif best is None:\n    ..."]],
  byhand="Budget 2.0. cs256-k3 costs 1.1: fits, quality 0.74. cs512-k5 costs 1.8: fits, quality 0.81, better. cs1024-k10 costs 3.2: over budget, skip. Answer cs512-k5.",
  why="One walk through the runs.",
  gotchas=[["Decide the rule before you look", "If you choose the metric and the budget after seeing results, you'll pick whatever happens to look good. Write the decision rule down first."], ["Compare like with like", "Runs evaluated on different eval sets or with different judges can't be compared. Log the eval set version as a parameter on every run."]]))

add(id="param_grid", title="Plan a Grid of Runs", topic="experiments", difficulty="medium", fn="param_grid",
 prompt="You want to try every combination of a few settings. `space` is a list of `[name, values]` pairs, like `[[\"chunk_size\", [256, 512]], [\"k\", [3, 5]]]`.\n\nReturn every combination as a list of dicts. The first setting changes slowest: `[{\"chunk_size\": 256, \"k\": 3}, {\"chunk_size\": 256, \"k\": 5}, {\"chunk_size\": 512, \"k\": 3}, {\"chunk_size\": 512, \"k\": 5}]`. An empty `space` gives one empty combination: `[{}]`.",
 pattern="Build combinations one setting at a time: start with [{}], and for each setting, extend every combination so far with every value.",
 target="one step per combination you produce",
 realworld="Grid search. The number of runs is the sizes multiplied together: 3 chunk sizes × 4 values of k × 2 models is already 24 runs, each with eval and judge costs. Seeing that number before you start is half of experiment design.",
 starter="def param_grid(space):\n    # your code here\n    pass\n",
 solution="def param_grid(space):\n    combos = [{}]\n    for name, values in space:\n        grown = []\n        for combo in combos:\n            for v in values:\n                c = dict(combo)\n                c[name] = v\n                grown.append(c)\n        combos = grown\n    return combos\n",
 cases=[([["chunk_size", [256, 512]], ["k", [3, 5]]], [{"chunk_size": 256, "k": 3}, {"chunk_size": 256, "k": 5}, {"chunk_size": 512, "k": 3}, {"chunk_size": 512, "k": 5}], True),
        ([], [{}]),
        ([["model", ["fast-model"]]], [{"model": "fast-model"}]),
        ([["a", [1, 2, 3]], ["b", ["x"]], ["c", [True, False]]], [{"a": 1, "b": "x", "c": True}, {"a": 1, "b": "x", "c": False}, {"a": 2, "b": "x", "c": True}, {"a": 2, "b": "x", "c": False}, {"a": 3, "b": "x", "c": True}, {"a": 3, "b": "x", "c": False}]),
        ([["k", []]], [])],
 guided="def param_grid(space):\n    # Replace every ___ with real code, then run the tests.\n\n    combos = [{}]   # one empty combination to build on\n    for name, values in space:\n        grown = []\n        for combo in combos:\n            for v in values:\n                # Step 1: copy the combination so far (don't change the original).\n                c = ___\n                # Step 2: add this setting's value.\n                c[name] = v\n                grown.append(c)\n        # Step 3: the grown list becomes the starting point for the next setting.\n        combos = ___\n    return combos\n",
 fills=["dict(combo)", "grown"],
 learn=dict(concepts=[["Copying a dict", "`dict(d)` makes a new dict with the same keys, so changing the copy leaves the original alone.", "a = {'k': 3}\nb = dict(a)\nb['k'] = 5   # a is still {'k': 3}"], ["Nested loops build combinations", "For every combination so far, try every new value.", "for combo in combos:\n    for v in values:\n        ..."]],
  byhand="Start with [{}]. Add chunk_size: [{256}, {512}]. Add k to each: {256,3}, {256,5}, {512,3}, {512,5}. Four runs.",
  why="Each combination is built once, and the number of combinations is the sizes multiplied together, so the grid grows fast.",
  gotchas=[["Grids explode", "Five settings with four values each is 1,024 runs. Fix what you can, vary two or three things at a time, or sample random combinations instead of all of them."], ["Copy, don't share", "Appending the same dict object several times means changing one changes them all. Always copy before adding a value."]]))

add(id="cv_folds", title="Cross-Validation Folds", topic="experiments", difficulty="easy", fn="cv_folds",
 prompt="With a small dataset, one test split is noisy. **Cross-validation** splits the data into `k` folds; each fold takes a turn as the test set while the others train.\n\nGiven `n` examples (numbered 0 to n-1) and `k` folds, return a list of `k` lists of example numbers, where example `i` goes into fold `i % k` (the remainder when you divide i by k). Keep numbers in increasing order inside each fold.",
 pattern="Deal the items round-robin, like dealing cards to k players.",
 target="one step per example",
 realworld="This is how a classifier gets a more trustworthy score: train 5 times, test on 5 different folds, and report both the average and how much it varied. `scikit-learn`'s `cross_val_score` does this, and MLflow can log every fold.",
 starter="def cv_folds(n, k):\n    # your code here\n    pass\n",
 solution="def cv_folds(n, k):\n    folds = [[] for _ in range(k)]\n    for i in range(n):\n        folds[i % k].append(i)\n    return folds\n",
 cases=[(7, 3, [[0, 3, 6], [1, 4], [2, 5]], True), (0, 2, [[], []]), (4, 1, [[0, 1, 2, 3]]), (3, 5, [[0], [1], [2], [], []]), (6, 2, [[0, 2, 4], [1, 3, 5]])],
 guided="def cv_folds(n, k):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: k empty lists. (Not [[]] * k: that's the SAME list k times.)\n    folds = [[] for _ in range(___)]\n    for i in range(n):\n        # Step 2: % gives the remainder, which cycles 0, 1, ..., k-1, 0, 1, ...\n        folds[___].append(i)\n    return folds\n",
 fills=["k", "i % k"],
 learn=dict(concepts=[["The remainder, %", "`7 % 3` is 1: what's left after taking out as many 3s as fit. It cycles 0, 1, 2, 0, 1, 2…", "[i % 3 for i in range(7)]   # [0, 1, 2, 0, 1, 2, 0]"], ["A list of empty lists", "`[[] for _ in range(k)]` makes k separate lists. `[[]] * k` makes k references to one list, a classic bug.", "folds = [[] for _ in range(3)]"]],
  byhand="Seven examples, three folds: 0 → fold 0, 1 → fold 1, 2 → fold 2, 3 → fold 0, 4 → fold 1, 5 → fold 2, 6 → fold 0.",
  why="One step per example.",
  gotchas=[["Shuffle first, but split by group", "Real data is often sorted (by date, by customer), so shuffle before dealing. If the same customer appears many times, keep all their rows in one fold, the same leakage rule as before."], ["Report the spread, not just the average", "Five folds scoring 0.80, 0.81, 0.79, 0.80, 0.80 is a stable model. 0.95, 0.60, 0.88, 0.70, 0.87 averages the same and is not."]]))

add(id="clear_winner", title="Is the Difference Real?", topic="experiments", difficulty="easy", fn="clear_winner",
 prompt="You ran two setups several times each, because LLM outputs and judges vary from run to run. `a_scores` and `b_scores` are their quality scores.\n\nUse a simple, cautious rule: A is the clear winner if its worst score beats B's best score, and the same the other way round. Return `\"a\"`, `\"b\"`, or `\"tie\"` when the ranges overlap. Both lists have at least one score.",
 pattern="Compare ranges, not single numbers: worst of one against best of the other.",
 target="one walk through each list",
 realworld="A prompt change that scores 0.82 against 0.80 once may just be luck. Running each setup 3 to 5 times and checking whether the results overlap is a cheap guard against shipping noise.",
 starter="def clear_winner(a_scores, b_scores):\n    # your code here\n    pass\n",
 solution="def clear_winner(a_scores, b_scores):\n    if min(a_scores) > max(b_scores):\n        return \"a\"\n    if min(b_scores) > max(a_scores):\n        return \"b\"\n    return \"tie\"\n",
 cases=[([0.78, 0.80, 0.79], [0.83, 0.85, 0.84], "b", True), ([0.80, 0.82], [0.81, 0.79], "tie"), ([0.9], [0.7], "a"), ([0.8, 0.8], [0.8], "tie"), ([0.6, 0.95], [0.7, 0.75], "tie")],
 guided="def clear_winner(a_scores, b_scores):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: A's worst beats B's best?\n    if ___ > max(b_scores):\n        return \"a\"\n    # Step 2: and the other way round.\n    if ___:\n        return \"b\"\n    return \"tie\"\n",
 fills=["min(a_scores)", "min(b_scores) > max(a_scores)"],
 learn=dict(concepts=[["min and max", "The smallest and largest item of a list.", "min([0.78, 0.8])   # 0.78\nmax([0.78, 0.8])   # 0.8"]],
  byhand="A ranges from 0.78 to 0.80. B ranges from 0.83 to 0.85. B's worst (0.83) beats A's best (0.80), so B is the clear winner.",
  why="One walk through each list to find its smallest and largest.",
  gotchas=[["Same inputs, same judge", "Repeat runs should differ only in randomness. If the eval set or judge changed between them, the comparison means nothing."], ["Ties are information", "\"No clear winner\" often means: pick the cheaper or faster option. That is a decision too."]]))

add(id="recall_at_k", title="Measure Retrieval", topic="rag", difficulty="easy", fn="recall_at_k",
 prompt="For one test question you know which documents are relevant. `retrieved` is the list of document ids your retriever returned, best first, and `relevant` is the list of ids that should be found.\n\nReturn the share of relevant ids that appear in the first `k` retrieved, rounded to 2 places. If `relevant` is empty, return `0.0`.",
 pattern="Take the top k, turn both into sets, count the overlap.",
 target="one walk through the top k",
 realworld="Measure retrieval separately from the final answer. If recall@5 is low, no prompt change will fix the answers: the model never saw the right document.",
 starter="def recall_at_k(retrieved, relevant, k):\n    # your code here\n    pass\n",
 solution="def recall_at_k(retrieved, relevant, k):\n    if not relevant:\n        return 0.0\n    found = set(retrieved[:k]) & set(relevant)\n    return round(len(found) / len(set(relevant)), 2)\n",
 cases=[(["d7", "d2", "d9", "d4"], ["d2", "d4"], 3, 0.5, True), (["a"], [], 1, 0.0), (["a", "b"], ["a", "b"], 2, 1.0), (["x", "y", "z"], ["q"], 3, 0.0), (["a", "b", "c"], ["c", "b", "e"], 5, 0.67)],
 guided="def recall_at_k(retrieved, relevant, k):\n    # Replace every ___ with real code, then run the tests.\n\n    if not relevant:\n        return 0.0\n    # Step 1: the ids in the top k that are also relevant. & is set intersection.\n    found = set(___) & set(relevant)\n    # Step 2: what share of the relevant ids were found?\n    return round(___, 2)\n",
 fills=["retrieved[:k]", "len(found) / len(set(relevant))"],
 learn=dict(concepts=[["Set intersection", "`a & b` keeps what's in both sets.", "{'d2', 'd7'} & {'d2', 'd4'}   # {'d2'}"], ["Slicing past the end", "`items[:5]` on a 3-item list just gives all 3.", "['a', 'b'][:5]   # ['a', 'b']"]],
  byhand="Top 3: d7, d2, d9. Relevant: d2 and d4. Found d2 only, so 1 of 2: 0.5.",
  why="One walk through the top k; set lookups are instant.",
  gotchas=[["You need labelled questions", "Recall needs to know which documents are relevant. Start with 30–50 real questions and mark the right documents by hand; it's the most valuable hour in a RAG project."], ["Higher k isn't free", "Raising k usually raises recall but adds tokens, cost and latency, and can bury the right chunk among wrong ones."]]))

add(id="pick_config", title="Choose Chunk Size and k", topic="rag", difficulty="medium", fn="pick_config",
 prompt="You ran a RAG experiment over chunk sizes and k. Each row of `results` looks like `{\"chunk_size\": 512, \"k\": 5, \"quality\": 0.82, \"p95_ms\": 1400, \"cost\": 2.1}`.\n\nReturn `[chunk_size, k]` for the row with the highest `quality` whose `p95_ms` is at most `max_ms`. If several tie on quality, pick the cheapest. If none is fast enough, return `None`.",
 pattern="Constraint first, then best by the main metric, then a tie-break on cost.",
 target="one walk through the results",
 realworld="Teams often pick the highest-quality config and discover it's too slow for the product. Deciding the latency budget up front, then maximising quality inside it, is how you get a config you can actually ship.",
 starter="def pick_config(results, max_ms):\n    # your code here\n    pass\n",
 solution="def pick_config(results, max_ms):\n    best = None\n    for r in results:\n        if r[\"p95_ms\"] > max_ms:\n            continue\n        if best is None or r[\"quality\"] > best[\"quality\"] or (r[\"quality\"] == best[\"quality\"] and r[\"cost\"] < best[\"cost\"]):\n            best = r\n    return [best[\"chunk_size\"], best[\"k\"]] if best else None\n",
 cases=[([{"chunk_size": 256, "k": 3, "quality": 0.71, "p95_ms": 900, "cost": 1.2}, {"chunk_size": 512, "k": 5, "quality": 0.82, "p95_ms": 1400, "cost": 2.1}, {"chunk_size": 1024, "k": 10, "quality": 0.85, "p95_ms": 2600, "cost": 3.9}], 1500, [512, 5], True),
        ([], 1000, None),
        ([{"chunk_size": 512, "k": 5, "quality": 0.8, "p95_ms": 2000, "cost": 2.0}], 1000, None),
        ([{"chunk_size": 256, "k": 5, "quality": 0.8, "p95_ms": 800, "cost": 1.5}, {"chunk_size": 512, "k": 3, "quality": 0.8, "p95_ms": 700, "cost": 1.1}], 1000, [512, 3])],
 guided="def pick_config(results, max_ms):\n    # Replace every ___ with real code, then run the tests.\n\n    best = None\n    for r in results:\n        # Step 1: too slow? skip it.\n        if ___:\n            continue\n        # Step 2: higher quality wins; on a tie, cheaper wins.\n        if best is None or r[\"quality\"] > best[\"quality\"] or (r[\"quality\"] == best[\"quality\"] and r[\"cost\"] < best[\"cost\"]):\n            best = r\n    # Step 3: return the two settings, or None.\n    return ___ if best else None\n",
 fills=["r[\"p95_ms\"] > max_ms", "[best[\"chunk_size\"], best[\"k\"]]"],
 learn=dict(concepts=[["A one-line if", "`a if condition else b`.", "answer = [512, 5] if best else None"]],
  byhand="Budget 1,500 ms. 256/3 takes 900 ms, quality 0.71. 512/5 takes 1,400 ms, quality 0.82: better. 1024/10 takes 2,600 ms: too slow. Answer [512, 5].",
  why="One walk through the results.",
  gotchas=[["Change one thing at a time when debugging", "If quality drops after changing chunk size, k and the embedding model together, you won't know which one did it."], ["Measure retrieval and answers separately", "Log recall@k and answer quality as separate metrics. A config can retrieve well and still answer badly, and the fixes are different."]]))

add(id="percentile", title="The Latency Users Feel", topic="models", difficulty="easy", fn="percentile",
 prompt="The average response time hides the slow requests users complain about, so teams track a **percentile**: p95 is the time that 95 out of 100 requests beat.\n\nGiven a list of `latencies` in milliseconds and `pct` (like 95), sort them and return the item at position `pct` percent of the way through, rounding the position up, counting from 1. In code: position = `(pct * n + 99) // 100`, and the answer is the item at index position − 1. An empty list gives `None`.",
 pattern="Sort, then pick by position.",
 target="sort once",
 realworld="A model with a 900 ms average can still have a 4-second p95, which is what users notice. Compare models and configs on p95 latency, not the average.",
 starter="def percentile(latencies, pct):\n    # your code here\n    pass\n",
 solution="def percentile(latencies, pct):\n    if not latencies:\n        return None\n    ordered = sorted(latencies)\n    position = (pct * len(ordered) + 99) // 100\n    return ordered[max(position, 1) - 1]\n",
 cases=[([820, 640, 4100, 700, 910, 760, 690, 3900, 720, 800], 90, 3900, True), ([], 95, None), ([500], 99, 500), ([5, 1, 3, 2, 4], 50, 3), ([10, 20, 30, 40], 100, 40), ([7, 8, 9], 1, 7)],
 guided="def percentile(latencies, pct):\n    # Replace every ___ with real code, then run the tests.\n\n    if not latencies:\n        return None\n    # Step 1: sorted() gives a new list, smallest first.\n    ordered = ___\n    # Step 2: the position, rounded up, counting from 1.\n    position = (pct * len(ordered) + 99) // 100\n    # Step 3: positions count from 1 but indexes from 0.\n    return ordered[___]\n",
 fills=["sorted(latencies)", "max(position, 1) - 1"],
 learn=dict(concepts=[["sorted", "Returns a new sorted list and leaves the original alone.", "sorted([3, 1, 2])   # [1, 2, 3]"], ["Rounding up with //", "`(a + 99) // 100` divides by 100 and rounds up, without decimals.", "(901 + 99) // 100   # 10"]],
  byhand="Ten latencies, p90. Sorted: 640, 690, 700, 720, 760, 800, 820, 910, 3900, 4100. 90% of 10 is position 9: 3900 ms. The average is about 1,400 ms, which hides two very slow requests.",
  why="Sorting is the slowest part.",
  gotchas=[["Average lies about latency", "One 30-second timeout and 99 fast requests average 400 ms. The p99 tells you about the timeout."], ["Measure where the user is", "Latency measured inside the model call misses retrieval, tools and network. Use the whole trace's duration."]]))

add(id="pareto_models", title="Compare Models Fairly", topic="models", difficulty="medium", fn="pareto_models",
 prompt="You evaluated several models on the same task. Each row of `models` is `{\"name\": \"fast-model\", \"quality\": 0.78, \"cost\": 0.4, \"p95_ms\": 900}`. Higher quality is better; lower cost and latency are better.\n\nA model is **beaten** if some other model is at least as good on all three and strictly better on at least one. Return the names of the models that are not beaten, in their original order. These are the only ones worth choosing between.",
 pattern="Compare every pair: a candidate survives only if nothing dominates it.",
 target="compare every pair (there are only a handful of models)",
 realworld="There is rarely one best model. A small model can be the right choice for a high-volume, simple task, and a large one for rare, hard questions. Throwing out models that lose on every measure leaves a short list to decide between on value.",
 starter="def pareto_models(models):\n    # your code here\n    pass\n",
 solution="def beats(a, b):\n    no_worse = a[\"quality\"] >= b[\"quality\"] and a[\"cost\"] <= b[\"cost\"] and a[\"p95_ms\"] <= b[\"p95_ms\"]\n    better = a[\"quality\"] > b[\"quality\"] or a[\"cost\"] < b[\"cost\"] or a[\"p95_ms\"] < b[\"p95_ms\"]\n    return no_worse and better\n\ndef pareto_models(models):\n    out = []\n    for m in models:\n        if not any(beats(other, m) for other in models):\n            out.append(m[\"name\"])\n    return out\n",
 cases=[([{"name": "fast-model", "quality": 0.78, "cost": 0.4, "p95_ms": 900}, {"name": "smart-model", "quality": 0.88, "cost": 3.0, "p95_ms": 2400}, {"name": "old-model", "quality": 0.75, "cost": 1.2, "p95_ms": 1500}], ["fast-model", "smart-model"], True),
        ([], []),
        ([{"name": "a", "quality": 0.8, "cost": 1, "p95_ms": 100}, {"name": "b", "quality": 0.8, "cost": 1, "p95_ms": 100}], ["a", "b"]),
        ([{"name": "a", "quality": 0.9, "cost": 1, "p95_ms": 100}, {"name": "b", "quality": 0.8, "cost": 1, "p95_ms": 100}], ["a"]),
        ([{"name": "cheap", "quality": 0.7, "cost": 0.1, "p95_ms": 500}, {"name": "quick", "quality": 0.7, "cost": 0.5, "p95_ms": 200}, {"name": "good", "quality": 0.9, "cost": 2, "p95_ms": 900}], ["cheap", "quick", "good"])],
 guided="def beats(a, b):\n    # a beats b: no worse on every measure, and better on at least one.\n    no_worse = a[\"quality\"] >= b[\"quality\"] and a[\"cost\"] <= b[\"cost\"] and a[\"p95_ms\"] <= b[\"p95_ms\"]\n    better = ___\n    return no_worse and better\n\n\ndef pareto_models(models):\n    # Replace every ___ with real code, then run the tests.\n    out = []\n    for m in models:\n        # Keep m only if no other model beats it.\n        # any(...) is True if at least one item is True.\n        if not any(___ for other in models):\n            out.append(m[\"name\"])\n    return out\n",
 fills=["a[\"quality\"] > b[\"quality\"] or a[\"cost\"] < b[\"cost\"] or a[\"p95_ms\"] < b[\"p95_ms\"]", "beats(other, m)"],
 learn=dict(concepts=[["any", "True if at least one item is true.", "any(x > 5 for x in [1, 7, 3])   # True"], ["A helper function", "Pulling a rule into its own small function makes the main loop easy to read.", "def beats(a, b):\n    ..."]],
  byhand="old-model costs more, is slower and scores lower than fast-model, so it's beaten. fast-model and smart-model each win on something (cheap and quick vs better), so both stay.",
  why="Every model is compared with every other, which is fine for a handful of models.",
  gotchas=[["Same eval set, same judge, same prompt", "Model comparisons are only fair when everything else is held fixed. Prompts tuned for one model often underperform on another, so test each with a reasonable prompt."], ["Quality on your task, not a leaderboard", "Public benchmarks rarely match your data. Thirty real examples from your own task tell you more."]]))

add(id="better_option", title="Return on Investment", topic="models", difficulty="easy", fn="better_option",
 prompt="Each option in `options` is `{\"name\": \"smart-model\", \"success_rate\": 0.9, \"cost_per_call\": 0.03}`. Each month there are `volume` requests, and each successful answer is worth `value_per_success` dollars (for example, a support ticket that doesn't reach a human).\n\nAn option's net monthly value is `volume * success_rate * value_per_success - volume * cost_per_call`. Return `[name, net]` for the option with the highest net value, with net rounded to 2 places. If two tie, the first listed wins. There is at least one option.",
 pattern="Score every option with the same formula, keep the best so far.",
 target="one walk through the options",
 realworld="This is the ROI question behind every experiment. A cheaper model that answers fewer questions can lose money, and an expensive one can pay for itself. Value per success is a business number: get it from the team that owns the outcome.",
 starter="def better_option(options, volume, value_per_success):\n    # your code here\n    pass\n",
 solution="def better_option(options, volume, value_per_success):\n    best = None\n    for o in options:\n        net = volume * o[\"success_rate\"] * value_per_success - volume * o[\"cost_per_call\"]\n        if best is None or net > best[1]:\n            best = [o[\"name\"], net]\n    return [best[0], round(best[1], 2)]\n",
 cases=[([{"name": "fast-model", "success_rate": 0.72, "cost_per_call": 0.002}, {"name": "smart-model", "success_rate": 0.9, "cost_per_call": 0.03}], 10000, 4.0, ["smart-model", 35700.0], True),
        ([{"name": "only", "success_rate": 0.5, "cost_per_call": 0.01}], 100, 1.0, ["only", 49.0]),
        ([{"name": "a", "success_rate": 0.8, "cost_per_call": 0.01}, {"name": "b", "success_rate": 0.81, "cost_per_call": 0.5}], 1000, 1.0, ["a", 790.0]),
        ([{"name": "x", "success_rate": 0.6, "cost_per_call": 0.1}, {"name": "y", "success_rate": 0.6, "cost_per_call": 0.1}], 10, 2.0, ["x", 11.0])],
 guided="def better_option(options, volume, value_per_success):\n    # Replace every ___ with real code, then run the tests.\n\n    best = None   # [name, net] of the best so far\n    for o in options:\n        # Step 1: value earned minus money spent, per month.\n        net = volume * o[\"success_rate\"] * value_per_success - ___\n        # Step 2: strictly better replaces it, so the first wins a tie.\n        if best is None or ___:\n            best = [o[\"name\"], net]\n    return [best[0], round(best[1], 2)]\n",
 fills=["volume * o[\"cost_per_call\"]", "net > best[1]"],
 learn=dict(concepts=[["Keeping a pair", "A two-item list can hold the best name and its score together.", "best = ['fast-model', 28780.0]\nbest[1]   # the score"]],
  byhand="fast-model: 10,000 × 0.72 × $4 = $28,800 earned, minus 10,000 × $0.002 = $20 spent: $28,780. smart-model: 10,000 × 0.9 × $4 = $36,000, minus $300: $35,700. The expensive model is worth $6,920 more a month.",
  why="One walk through the options.",
  gotchas=[["Count every cost", "Per-call model cost is only part of it: retrieval, retries, agent steps, evaluation runs and human review all count. Traces with token counts make this possible."], ["Success must be measured, not assumed", "The success rate comes from your evals and from production feedback. If it's a guess, the ROI is a guess."]]))

add(id="agent_scorecard", title="Score an Agent", topic="agents", difficulty="easy", fn="agent_scorecard",
 prompt="You ran an agent on a set of test tasks. Each run in `runs` is `{\"success\": True, \"steps\": 4, \"cost\": 0.012}`.\n\nReturn `[success_rate, avg_steps_when_successful, cost_per_success]`: the share of successful runs, the average steps of the successful runs, and the total cost of all runs divided by the number of successes. Round each to 2 places, except cost per success, which rounds to 4. If there are no runs, return `[0.0, None, None]`; if none succeeded, the last two are `None`.",
 pattern="One pass, several running totals, then divide with guards.",
 target="one walk through the runs",
 realworld="Success rate alone is misleading for agents. An agent that succeeds 90% of the time but needs 12 steps and $0.40 per success may be worse value than one at 80% with 4 steps. Cost per success puts failures' cost where it belongs.",
 starter="def agent_scorecard(runs):\n    # your code here\n    pass\n",
 solution="def agent_scorecard(runs):\n    if not runs:\n        return [0.0, None, None]\n    wins = 0\n    win_steps = 0\n    total_cost = 0\n    for r in runs:\n        total_cost += r[\"cost\"]\n        if r[\"success\"]:\n            wins += 1\n            win_steps += r[\"steps\"]\n    rate = round(wins / len(runs), 2)\n    if wins == 0:\n        return [rate, None, None]\n    return [rate, round(win_steps / wins, 2), round(total_cost / wins, 4)]\n",
 cases=[([{"success": True, "steps": 4, "cost": 0.012}, {"success": False, "steps": 10, "cost": 0.05}, {"success": True, "steps": 6, "cost": 0.018}], [0.67, 5.0, 0.04], True),
        ([], [0.0, None, None]),
        ([{"success": False, "steps": 3, "cost": 0.01}], [0.0, None, None]),
        ([{"success": True, "steps": 2, "cost": 0.004}, {"success": True, "steps": 3, "cost": 0.006}], [1.0, 2.5, 0.005])],
 guided="def agent_scorecard(runs):\n    # Replace every ___ with real code, then run the tests.\n\n    if not runs:\n        return [0.0, None, None]\n    wins = 0\n    win_steps = 0\n    total_cost = 0\n    for r in runs:\n        # Step 1: every run costs money, successful or not.\n        total_cost += ___\n        if r[\"success\"]:\n            wins += 1\n            win_steps += r[\"steps\"]\n    rate = round(wins / len(runs), 2)\n    if wins == 0:\n        return [rate, None, None]\n    # Step 2: failures' cost is spread over the successes.\n    return [rate, round(win_steps / wins, 2), round(___, 4)]\n",
 fills=["r[\"cost\"]", "total_cost / wins"],
 learn=dict(concepts=[["Running totals", "`+=` adds to a variable.", "total = 0\ntotal += 0.012"]],
  byhand="Two of three succeed: 0.67. Their steps are 4 and 6: average 5. Total cost is 0.012 + 0.05 + 0.018 = 0.08, over 2 successes: 0.04 per success.",
  why="One walk through the runs.",
  gotchas=[["Define success before you run", "\"Did the agent finish the task?\" needs a clear rule or an LLM judge with a rubric, checked against a few human labels."], ["Watch the failures' cost", "Failed runs are often the longest and most expensive, because the agent keeps trying."]]))

add(id="summarize_by_tag", title="Slice Traces by Experiment", topic="tracing", difficulty="medium", fn="summarize_by_tag",
 prompt="Every trace was tagged with the setup that produced it. Each trace in `traces` is like `{\"tags\": {\"config\": \"cs512-k5\"}, \"ms\": 1300, \"tokens\": 2100, \"ok\": True}`.\n\nGroup the traces by `tags[tag]` and return a dict from each value to `[count, average_ms, total_tokens, success_rate]`, with average_ms rounded to a whole number and success_rate to 2 places. Traces without that tag are skipped.",
 pattern="Group by a key into a dict of running totals, then turn totals into averages at the end.",
 target="one walk through the traces",
 realworld="This only works if you tagged traces when you created them. Putting the experiment config, model and prompt version on every trace is what lets you compare setups on real traffic later, not just on the eval set.",
 starter="def summarize_by_tag(traces, tag):\n    # your code here\n    pass\n",
 solution="def summarize_by_tag(traces, tag):\n    groups = {}\n    for t in traces:\n        if tag not in t[\"tags\"]:\n            continue\n        key = t[\"tags\"][tag]\n        g = groups.setdefault(key, [0, 0, 0, 0])\n        g[0] += 1\n        g[1] += t[\"ms\"]\n        g[2] += t[\"tokens\"]\n        if t[\"ok\"]:\n            g[3] += 1\n    out = {}\n    for key, g in groups.items():\n        out[key] = [g[0], round(g[1] / g[0]), g[2], round(g[3] / g[0], 2)]\n    return out\n",
 cases=[([{"tags": {"config": "cs512-k5"}, "ms": 1300, "tokens": 2100, "ok": True}, {"tags": {"config": "cs256-k3"}, "ms": 800, "tokens": 1200, "ok": False}, {"tags": {"config": "cs512-k5"}, "ms": 1500, "tokens": 2300, "ok": True}, {"tags": {}, "ms": 9000, "tokens": 50, "ok": False}], "config", {"cs512-k5": [2, 1400, 4400, 1.0], "cs256-k3": [1, 800, 1200, 0.0]}, True),
        ([], "config", {}),
        ([{"tags": {"model": "fast-model"}, "ms": 100, "tokens": 10, "ok": True}], "config", {}),
        ([{"tags": {"model": "a"}, "ms": 100, "tokens": 5, "ok": True}, {"tags": {"model": "a"}, "ms": 201, "tokens": 5, "ok": False}, {"tags": {"model": "a"}, "ms": 300, "tokens": 5, "ok": True}], "model", {"a": [3, 200, 15, 0.67]})],
 guided="def summarize_by_tag(traces, tag):\n    # Replace every ___ with real code, then run the tests.\n\n    groups = {}   # tag value -> [count, total_ms, total_tokens, successes]\n    for t in traces:\n        if tag not in t[\"tags\"]:\n            continue\n        key = t[\"tags\"][tag]\n        # Step 1: the running totals for this value, created the first time.\n        g = groups.setdefault(key, [0, 0, 0, 0])\n        g[0] += 1\n        g[1] += t[\"ms\"]\n        g[2] += ___\n        if t[\"ok\"]:\n            g[3] += 1\n    out = {}\n    for key, g in groups.items():\n        # Step 2: totals become averages and rates at the end.\n        out[key] = [g[0], round(___), g[2], round(g[3] / g[0], 2)]\n    return out\n",
 fills=["t[\"tokens\"]", "g[1] / g[0]"],
 learn=dict(concepts=[["setdefault for totals", "Creates the starting totals the first time a key appears, then returns the same list each time after.", "g = groups.setdefault('k5', [0, 0])\ng[0] += 1"], ["Totals first, averages last", "Keep sums while looping and divide once at the end.", "avg = total / count"]],
  byhand="cs512-k5 has two traces: 1,300 and 1,500 ms (average 1,400), 2,100 + 2,300 tokens, both ok. cs256-k3 has one trace that failed. The untagged trace is skipped.",
  why="One walk through the traces, one more through the groups.",
  gotchas=[["Tag at creation time", "You can't add the config to a trace you didn't tag. Decide the tags (config, model, prompt version, user segment) before the experiment starts."], ["Keep tags low-cardinality", "Tags like config or model have a few values and slice nicely. Put unique values like request ids in span attributes instead."]]))

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
    print("verified", len(P), "experiment problems")
if __name__ == "__main__":
    check()
