"""Experiment design with MLflow: Runs, grids, fair comparisons and decisions you can defend."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('experiments', 'Experiment design with MLflow', 'Runs, grids, fair comparisons and decisions you can defend.')

lesson(MODULE, 'best_run',
    title='Experiments, runs and the lifecycle',
    learn=[
        'An **experiment** answers one question, like "which chunk size gives the best answers under 1.5 seconds?". Each attempt is a **run** that records its **parameters** (what you set), **metrics** (what you measured) and **artifacts** (files, like the eval results).',
        'MLflow stores all of this so you can compare runs side by side instead of in a spreadsheet. Write the decision rule down before you run anything, for example "highest quality under $2 per 1,000 requests". That\'s what turns an experiment into a decision, and a decision into return on the time spent.',
    ],
    example=example('One run, logged', """import mlflow
mlflow.set_experiment("/Shared/support-bot-rag")
with mlflow.start_run(run_name="cs512-k5"):
    mlflow.log_params({"chunk_size": 512, "k": 5, "model": "fast-model"})
    mlflow.log_metrics({"quality": 0.81, "cost_per_1k": 1.8})"""),
    check=question(
        'You ran 12 configs and the best quality costs 3× your budget. What should the experiment have had from the start?',
        ['More configs', 'A decision rule that includes the budget', 'A bigger model'],
        answer=1,
        why="With the budget in the rule, the answer is the best run you can afford, not a winner you can't use.",
    ),
    angle=angle(
        pattern='Best so far, with a constraint',
        text='Skip anything that breaks the rule, keep the best of the rest, and break ties on purpose. One walk through the runs. Maximum Subarray uses the same keep-the-best-so-far bookkeeping.',
        say='"I filter on the constraint first, then keep a running best with an explicit tie-break, in one pass."',
        classic='max_subarray',
    ),
    stack=stack('MLflow: find the best run within budget', """runs = mlflow.search_runs(
    experiment_names=["/Shared/support-bot-rag"],
    filter_string="metrics.cost_per_1k < 2.0",
    order_by=["metrics.quality DESC"],
)
best = runs.iloc[0]"""),
    exercise=exercise(
        title='Pick the Best Run',
        topic='experiments',
        difficulty='easy',
        fn='best_run',
        prompt="""Each run in an experiment logged its settings and results. `runs` is a list like `{"run_name": "cs512-k5", "quality": 0.81, "cost": 1.8}`, where cost is dollars per 1,000 requests.

Return the `run_name` of the run with the highest `quality` among runs whose `cost` is at most `max_cost`. If two tie on quality, pick the cheaper one. If no run is cheap enough, return `None`.""",
        pattern='Filter by the constraint first, then keep the best so far with a tie rule.',
        target='one walk through the runs',
        realworld='This is what `mlflow.search_runs` with a filter and an order does. Deciding the constraint (budget, latency) before looking at results stops you picking whatever looks best afterwards.',
        starter="""def best_run(runs, max_cost):
    # your code here
    pass
""",
        solution="""def best_run(runs, max_cost):
    best = None
    for r in runs:
        if r["cost"] > max_cost:
            continue
        if best is None or r["quality"] > best["quality"] or (r["quality"] == best["quality"] and r["cost"] < best["cost"]):
            best = r
    return best["run_name"] if best else None
""",
        cases=[
            case([
                {'run_name': 'cs256-k3', 'quality': 0.74, 'cost': 1.1},
                {'run_name': 'cs512-k5', 'quality': 0.81, 'cost': 1.8},
                {'run_name': 'cs1024-k10', 'quality': 0.84, 'cost': 3.2},
            ], 2.0, expected='cs512-k5', sample=True),
            case([], 5.0, expected=None),
            case([{'run_name': 'a', 'quality': 0.9, 'cost': 9.0}], 1.0, expected=None),
            case([{'run_name': 'a', 'quality': 0.8, 'cost': 2.0}, {'run_name': 'b', 'quality': 0.8, 'cost': 1.5}], 2.0, expected='b'),
            case([{'run_name': 'a', 'quality': 0.7, 'cost': 1.0}, {'run_name': 'b', 'quality': 0.75, 'cost': 1.0}], 1.0, expected='b'),
        ],
        guided="""def best_run(runs, max_cost):
    # Replace every ___ with real code, then run the tests.

    best = None
    for r in runs:
        # Step 1: skip runs over budget.
        if ___:
            continue
        # Step 2: better quality wins; equal quality, the cheaper one wins.
        if best is None or r["quality"] > best["quality"] or ___:
            best = r
    # Step 3: the name, or None if nothing fit the budget.
    return best["run_name"] if best else None
""",
        fills=['r["cost"] > max_cost', '(r["quality"] == best["quality"] and r["cost"] < best["cost"])'],
        concepts=[
            [
                'continue',
                'Skips the rest of this loop turn.',
                """for r in runs:
    if r['cost'] > 2:
        continue
    ...""",
            ],
            [
                'None as "nothing yet"',
                'Start with None and replace it with the first real candidate.',
                """best = None
if best is None:
    ...""",
            ],
        ],
        byhand='Budget 2.0. cs256-k3 costs 1.1: fits, quality 0.74. cs512-k5 costs 1.8: fits, quality 0.81, better. cs1024-k10 costs 3.2: over budget, skip. Answer cs512-k5.',
        why='One walk through the runs.',
        gotchas=[
            [
                'Decide the rule before you look',
                "If you choose the metric and the budget after seeing results, you'll pick whatever happens to look good. Write the decision rule down first.",
            ],
            [
                'Compare like with like',
                "Runs evaluated on different eval sets or with different judges can't be compared. Log the eval set version as a parameter on every run.",
            ],
        ],
    ),
)

lesson(MODULE, 'param_grid',
    title='Planning what to vary',
    learn=[
        "A good experiment varies a few things on purpose and holds everything else fixed: the same eval set, the same judge, the same prompt unless the prompt is what you're testing.",
        'Every value you add multiplies the number of runs. 3 chunk sizes × 4 values of k × 2 models is 24 runs, each paying for eval and judge calls. Count the runs, and their cost, before you start.',
    ],
    example=example('A grid, one MLflow run per combination', """for config in grid:
    with mlflow.start_run(run_name=f"cs{config['chunk_size']}-k{config['k']}"):
        mlflow.log_params(config)
        mlflow.log_metrics(run_eval(config))"""),
    check=question(
        'You want to test 4 chunk sizes, 5 values of k and 3 models. How many runs is a full grid?',
        ['12', '60', '20'],
        answer=1,
        why="4 × 5 × 3 = 60. That's why you fix some settings and vary two or three at a time.",
    ),
    angle=angle(
        pattern='Building combinations',
        text='Start with one empty combination and extend every combination with every value of the next setting. The output grows by multiplication, which is the whole point of the lesson. Interviewers call problems like this "generate all combinations".',
        say='"I build the combinations one setting at a time, copying each partial combination before adding a value so they don\'t share state."',
        classic=None,
    ),
    stack=stack('MLflow: one run per combination', """for config in grid:
    with mlflow.start_run(run_name=f"cs{config['chunk_size']}-k{config['k']}"):
        mlflow.log_params(config)
        mlflow.log_metrics(run_eval(config))"""),
    exercise=exercise(
        title='Plan a Grid of Runs',
        topic='experiments',
        difficulty='medium',
        fn='param_grid',
        prompt="""You want to try every combination of a few settings. `space` is a list of `[name, values]` pairs, like `[["chunk_size", [256, 512]], ["k", [3, 5]]]`.

Return every combination as a list of dicts. The first setting changes slowest: `[{"chunk_size": 256, "k": 3}, {"chunk_size": 256, "k": 5}, {"chunk_size": 512, "k": 3}, {"chunk_size": 512, "k": 5}]`. An empty `space` gives one empty combination: `[{}]`.""",
        pattern='Build combinations one setting at a time: start with [{}], and for each setting, extend every combination so far with every value.',
        target='one step per combination you produce',
        realworld='Grid search. The number of runs is the sizes multiplied together: 3 chunk sizes × 4 values of k × 2 models is already 24 runs, each with eval and judge costs. Seeing that number before you start is half of experiment design.',
        starter="""def param_grid(space):
    # your code here
    pass
""",
        solution="""def param_grid(space):
    combos = [{}]
    for name, values in space:
        grown = []
        for combo in combos:
            for v in values:
                c = dict(combo)
                c[name] = v
                grown.append(c)
        combos = grown
    return combos
""",
        cases=[
            case([['chunk_size', [256, 512]], ['k', [3, 5]]], expected=[
                {'chunk_size': 256, 'k': 3},
                {'chunk_size': 256, 'k': 5},
                {'chunk_size': 512, 'k': 3},
                {'chunk_size': 512, 'k': 5},
            ], sample=True),
            case([], expected=[{}]),
            case([['model', ['fast-model']]], expected=[{'model': 'fast-model'}]),
            case([['a', [1, 2, 3]], ['b', ['x']], ['c', [True, False]]], expected=[
                {'a': 1, 'b': 'x', 'c': True},
                {'a': 1, 'b': 'x', 'c': False},
                {'a': 2, 'b': 'x', 'c': True},
                {'a': 2, 'b': 'x', 'c': False},
                {'a': 3, 'b': 'x', 'c': True},
                {'a': 3, 'b': 'x', 'c': False},
            ]),
            case([['k', []]], expected=[]),
        ],
        guided="""def param_grid(space):
    # Replace every ___ with real code, then run the tests.

    combos = [{}]   # one empty combination to build on
    for name, values in space:
        grown = []
        for combo in combos:
            for v in values:
                # Step 1: copy the combination so far (don't change the original).
                c = ___
                # Step 2: add this setting's value.
                c[name] = v
                grown.append(c)
        # Step 3: the grown list becomes the starting point for the next setting.
        combos = ___
    return combos
""",
        fills=['dict(combo)', 'grown'],
        concepts=[
            [
                'Copying a dict',
                '`dict(d)` makes a new dict with the same keys, so changing the copy leaves the original alone.',
                """a = {'k': 3}
b = dict(a)
b['k'] = 5   # a is still {'k': 3}""",
            ],
            [
                'Nested loops build combinations',
                'For every combination so far, try every new value.',
                """for combo in combos:
    for v in values:
        ...""",
            ],
        ],
        byhand='Start with [{}]. Add chunk_size: [{256}, {512}]. Add k to each: {256,3}, {256,5}, {512,3}, {512,5}. Four runs.',
        why='Each combination is built once, and the number of combinations is the sizes multiplied together, so the grid grows fast.',
        gotchas=[
            [
                'Grids explode',
                'Five settings with four values each is 1,024 runs. Fix what you can, vary two or three things at a time, or sample random combinations instead of all of them.',
            ],
            [
                "Copy, don't share",
                'Appending the same dict object several times means changing one changes them all. Always copy before adding a value.',
            ],
        ],
    ),
)

lesson(MODULE, 'cv_folds',
    title='Experiments for classic ML',
    learn=[
        'For a classifier (spam, churn, fraud), one train/test split can be lucky or unlucky. **Cross-validation** splits the data into k folds and trains k times, each time testing on a different fold.',
        'You get k scores instead of one: report the average and how much they vary. Compare models on the same folds, and log every model as an MLflow run so the comparison is reproducible.',
    ],
    example=example('scikit-learn with MLflow autologging', """import mlflow
from sklearn.model_selection import cross_val_score
mlflow.sklearn.autolog()
with mlflow.start_run(run_name="logreg-5fold"):
    scores = cross_val_score(model, X, y, cv=5, scoring="f1")
    mlflow.log_metrics({"f1_mean": scores.mean(), "f1_min": scores.min()})"""),
    check=question(
        'Model A scores 0.80 on every fold. Model B scores 0.95, 0.60, 0.90, 0.70, 0.85 (also 0.80 on average). Which is the safer choice?',
        ['A: same average, much more predictable', 'B: it reaches 0.95', "They're the same"],
        answer=0,
        why='Same average, but B swings widely depending on the data it sees. Production data will swing too.',
    ),
    angle=angle(
        pattern='Dealing round-robin',
        text='Each example goes to fold `i % k`, like dealing cards. One step per example.',
        say='"I assign example i to fold i mod k, so folds differ in size by at most one; with real data I\'d shuffle first and keep each customer in a single fold."',
        classic=None,
    ),
    stack=stack('scikit-learn with MLflow autologging', """mlflow.sklearn.autolog()
with mlflow.start_run(run_name="logreg-5fold"):
    scores = cross_val_score(model, X, y, cv=5, scoring="f1")
    mlflow.log_metrics({"f1_mean": scores.mean(), "f1_min": scores.min()})"""),
    exercise=exercise(
        title='Cross-Validation Folds',
        topic='experiments',
        difficulty='easy',
        fn='cv_folds',
        prompt="""With a small dataset, one test split is noisy. **Cross-validation** splits the data into `k` folds; each fold takes a turn as the test set while the others train.

Given `n` examples (numbered 0 to n-1) and `k` folds, return a list of `k` lists of example numbers, where example `i` goes into fold `i % k` (the remainder when you divide i by k). Keep numbers in increasing order inside each fold.""",
        pattern='Deal the items round-robin, like dealing cards to k players.',
        target='one step per example',
        realworld="This is how a classifier gets a more trustworthy score: train 5 times, test on 5 different folds, and report both the average and how much it varied. `scikit-learn`'s `cross_val_score` does this, and MLflow can log every fold.",
        starter="""def cv_folds(n, k):
    # your code here
    pass
""",
        solution="""def cv_folds(n, k):
    folds = [[] for _ in range(k)]
    for i in range(n):
        folds[i % k].append(i)
    return folds
""",
        cases=[
            case(7, 3, expected=[[0, 3, 6], [1, 4], [2, 5]], sample=True),
            case(0, 2, expected=[[], []]),
            case(4, 1, expected=[[0, 1, 2, 3]]),
            case(3, 5, expected=[[0], [1], [2], [], []]),
            case(6, 2, expected=[[0, 2, 4], [1, 3, 5]]),
        ],
        guided="""def cv_folds(n, k):
    # Replace every ___ with real code, then run the tests.

    # Step 1: k empty lists. (Not [[]] * k: that's the SAME list k times.)
    folds = [[] for _ in range(___)]
    for i in range(n):
        # Step 2: % gives the remainder, which cycles 0, 1, ..., k-1, 0, 1, ...
        folds[___].append(i)
    return folds
""",
        fills=['k', 'i % k'],
        concepts=[
            [
                'The remainder, %',
                "`7 % 3` is 1: what's left after taking out as many 3s as fit. It cycles 0, 1, 2, 0, 1, 2…",
                '[i % 3 for i in range(7)]   # [0, 1, 2, 0, 1, 2, 0]',
            ],
            [
                'A list of empty lists',
                '`[[] for _ in range(k)]` makes k separate lists. `[[]] * k` makes k references to one list, a classic bug.',
                'folds = [[] for _ in range(3)]',
            ],
        ],
        byhand='Seven examples, three folds: 0 → fold 0, 1 → fold 1, 2 → fold 2, 3 → fold 0, 4 → fold 1, 5 → fold 2, 6 → fold 0.',
        why='One step per example.',
        gotchas=[
            [
                'Shuffle first, but split by group',
                'Real data is often sorted (by date, by customer), so shuffle before dealing. If the same customer appears many times, keep all their rows in one fold, the same leakage rule as before.',
            ],
            [
                'Report the spread, not just the average',
                'Five folds scoring 0.80, 0.81, 0.79, 0.80, 0.80 is a stable model. 0.95, 0.60, 0.88, 0.70, 0.87 averages the same and is not.',
            ],
        ],
    ),
)

lesson(MODULE, 'clear_winner',
    title='Telling real gains from noise',
    learn=[
        'LLM outputs and LLM judges vary from run to run. A single comparison of 0.82 against 0.80 may just be luck.',
        'Run each setup several times (3 to 5 is common), and only call a winner when the results clearly separate. If they overlap, choose on cost or speed, or test on more examples.',
    ],
    example=example('Repeat runs as nested MLflow runs', """with mlflow.start_run(run_name="prompt_b"):
    for seed in [1, 2, 3]:
        with mlflow.start_run(run_name=f"seed-{seed}", nested=True):
            mlflow.log_metric("quality", evaluate(prompt_b, seed=seed))"""),
    check=question(
        'Prompt A scored 0.80, 0.83, 0.81. Prompt B scored 0.82, 0.84, 0.80. What can you say?',
        ['B is better', 'No clear winner: the results overlap', 'A is better'],
        answer=1,
        why="B's worst (0.80) doesn't beat A's best (0.83). Pick on cost, or gather more data.",
    ),
    angle=angle(
        pattern='Comparing ranges',
        text="Find each list's smallest and largest once, then compare worst against best. A careful rule beats an exciting one.",
        say='"I only call a winner when one setup\'s worst run beats the other\'s best; otherwise I treat it as a tie and decide on cost."',
        classic=None,
    ),
    stack=stack('MLflow: repeat runs as nested runs', """with mlflow.start_run(run_name="prompt_b"):
    for seed in [1, 2, 3]:
        with mlflow.start_run(run_name=f"seed-{seed}", nested=True):
            mlflow.log_metric("quality", evaluate(prompt_b, seed=seed))"""),
    exercise=exercise(
        title='Is the Difference Real?',
        topic='experiments',
        difficulty='easy',
        fn='clear_winner',
        prompt="""You ran two setups several times each, because LLM outputs and judges vary from run to run. `a_scores` and `b_scores` are their quality scores.

Use a simple, cautious rule: A is the clear winner if its worst score beats B's best score, and the same the other way round. Return `"a"`, `"b"`, or `"tie"` when the ranges overlap. Both lists have at least one score.""",
        pattern='Compare ranges, not single numbers: worst of one against best of the other.',
        target='one walk through each list',
        realworld='A prompt change that scores 0.82 against 0.80 once may just be luck. Running each setup 3 to 5 times and checking whether the results overlap is a cheap guard against shipping noise.',
        starter="""def clear_winner(a_scores, b_scores):
    # your code here
    pass
""",
        solution="""def clear_winner(a_scores, b_scores):
    if min(a_scores) > max(b_scores):
        return "a"
    if min(b_scores) > max(a_scores):
        return "b"
    return "tie"
""",
        cases=[
            case([0.78, 0.8, 0.79], [0.83, 0.85, 0.84], expected='b', sample=True),
            case([0.8, 0.82], [0.81, 0.79], expected='tie'),
            case([0.9], [0.7], expected='a'),
            case([0.8, 0.8], [0.8], expected='tie'),
            case([0.6, 0.95], [0.7, 0.75], expected='tie'),
        ],
        guided="""def clear_winner(a_scores, b_scores):
    # Replace every ___ with real code, then run the tests.

    # Step 1: A's worst beats B's best?
    if ___ > max(b_scores):
        return "a"
    # Step 2: and the other way round.
    if ___:
        return "b"
    return "tie"
""",
        fills=['min(a_scores)', 'min(b_scores) > max(a_scores)'],
        concepts=[
            [
                'min and max',
                'The smallest and largest item of a list.',
                """min([0.78, 0.8])   # 0.78
max([0.78, 0.8])   # 0.8""",
            ],
        ],
        byhand="A ranges from 0.78 to 0.80. B ranges from 0.83 to 0.85. B's worst (0.83) beats A's best (0.80), so B is the clear winner.",
        why='One walk through each list to find its smallest and largest.',
        gotchas=[
            [
                'Same inputs, same judge',
                'Repeat runs should differ only in randomness. If the eval set or judge changed between them, the comparison means nothing.',
            ],
            [
                'Ties are information',
                '"No clear winner" often means: pick the cheaper or faster option. That is a decision too.',
            ],
        ],
    ),
)
