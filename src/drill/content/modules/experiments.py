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

lesson(MODULE, 'plan_gaps',
    title='Write the plan before the runs',
    learn=[
        'Decide how you will judge an experiment **before** you see a single result: the question, the one thing you change, the eval set and its version, the metric, how many runs, how you will compare, and the rule that picks a winner.',
        "If you choose the metric or the rule after looking, you can talk yourself into almost any answer. Writing it down first is called **pre-registration** in research. It's the cheapest protection against fooling yourself, and it makes a result easy to defend to someone else.",
        'Also write down what "no result" means. "Too close to call, keep the current version and add more examples" is a decision you can make in advance.',
    ],
    example=example('A plan, written before the first run', """plan = {
    "question": "Does model B give better hints than model A?",
    "change": "the model (prompt, temperature, judge fixed)",
    "eval_set": "hints-v3, 27 cases",
    "metric": "no-giveaway rate; guardrail: p95 latency",
    "runs": 3,
    "test": "paired, McNemar",
    "decision_rule": "switch only if B wins clearly and p95 < 10 s",
}"""),
    check=question(
        'You compared two prompts. B lost on quality but was faster, so you decided speed was the main metric after all. What went wrong?',
        [
            'Nothing: speed matters',
            'The rule was chosen after seeing the results, so the comparison proves nothing',
            'You should have run more prompts',
        ],
        answer=1,
        why='Picking the metric that favours the result you already saw is the classic way to fool yourself. Decide the main metric and the rule before running.',
    ),
    angle=angle(
        pattern='Checklist walk',
        text='Walk a fixed list of required fields once, looking each one up in the dict. A dict lookup is instant, so checking the plan is one short pass however many fields it has.',
        say='"I write the decision rule before I run anything, and I check the plan is complete before the first run."',
        classic=None,
    ),
    stack=stack('MLflow: log the plan with the run', """with mlflow.start_run(run_name="hints-a-vs-b"):
    mlflow.log_dict(plan, "plan.json")          # the plan, saved next to the results
    mlflow.log_params({"eval_set": plan["eval_set"], "test": plan["test"]})"""),
    exercise=exercise(
        title='Is the Plan Complete?',
        topic='experiments',
        difficulty='easy',
        fn='plan_gaps',
        prompt="""Before running an experiment, check its plan is complete. `plan` is a dict. These fields are required, in this order:

`question`, `change`, `eval_set`, `metric`, `runs`, `test`, `decision_rule`

A field is a gap if it's missing, if its value is `None`, or if it's text that is empty or only spaces. Return the list of gaps in the order above. Return `[]` when the plan is complete.""",
        pattern='One walk over a fixed list of required fields, with a dict lookup for each.',
        target='one pass over the required fields',
        realworld='A team that logs the plan with every MLflow run can show, months later, that the rule came before the result. Blocking a run until the plan is complete turns that from a good intention into a habit.',
        starter="""def plan_gaps(plan):
    # your code here
    pass
""",
        solution="""def plan_gaps(plan):
    required = ["question", "change", "eval_set", "metric", "runs", "test", "decision_rule"]
    gaps = []
    for field in required:
        value = plan.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            gaps.append(field)
    return gaps
""",
        cases=[
            case({'question': 'Is B better?', 'change': 'model', 'eval_set': 'v3', 'metric': 'accuracy', 'runs': 3, 'test': ''}, expected=['test', 'decision_rule'], sample=True),
            case({'question': 'Is B better?', 'change': 'model', 'eval_set': 'v3', 'metric': 'accuracy', 'runs': 3, 'test': 'paired', 'decision_rule': 'B wins clearly'}, expected=[]),
            case({}, expected=['question', 'change', 'eval_set', 'metric', 'runs', 'test', 'decision_rule']),
            case({'question': '   ', 'change': 'prompt', 'eval_set': None, 'metric': 'groundedness', 'runs': 5, 'test': 'paired', 'decision_rule': 'win by 2x'}, expected=['question', 'eval_set']),
        ],
        guided="""def plan_gaps(plan):
    # Replace every ___ with real code, then run the tests.
    required = ["question", "change", "eval_set", "metric", "runs", "test", "decision_rule"]
    gaps = []
    for field in required:
        # Step 1: .get gives None when the field is missing, instead of an error.
        value = ___
        # Step 2: a gap is None, or text that is empty once the spaces are stripped.
        if value is None or (isinstance(value, str) and ___):
            gaps.append(field)
    return gaps
""",
        fills=['plan.get(field)', 'value.strip() == ""'],
        concepts=[
            [
                'dict.get',
                'Looks up a key, and gives a default (None unless you say otherwise) when the key is missing.',
                """plan = {"runs": 3}
plan.get("runs")    # 3
plan.get("test")    # None""",
            ],
            [
                'isinstance',
                'Checks what kind of value something is, so you only call text methods on text.',
                """isinstance("abc", str)   # True
isinstance(3, str)       # False""",
            ],
        ],
        byhand='The first plan has everything up to `runs`. `test` is an empty string, so it counts as a gap, and `decision_rule` is missing. Answer: `["test", "decision_rule"]`.',
        why='One step per required field, and each dict lookup is instant.',
        gotchas=[
            [
                'Spaces are not an answer',
                'A field holding `"   "` looks filled in but says nothing. Strip it before checking.',
            ],
            [
                'Zero is not blank',
                'Only text is checked for emptiness. A number like `runs: 0` is a real (if odd) value, not a missing one.',
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

lesson(MODULE, 'examples_needed',
    title='How many examples do you need?',
    learn=[
        'A pass rate measured on an eval set is an estimate, not the truth. Score 70% on 25 questions and the real rate could easily be anywhere from 50% to 90%. The fewer the examples, the wider that **margin of error**.',
        'A quick rule for a pass rate: the margin is about **±100 ÷ √n percentage points**, where n is the number of examples (that is a 95% range, at its widest when the rate is near 50%). So 100 examples give about ±10 points, and 400 give about ±5. Halving the margin takes **four times** the examples.',
        "Use it backwards before you run anything: if the improvement you hope to see is smaller than the margin, your eval set can't show it. Add examples first, or compare on the same examples (next lessons), which is more sensitive.",
        'For scores near 0% or 100% (like 49 out of 50) this simple rule breaks down; statisticians use a **Wilson interval** there (next lesson). For metrics with no simple formula, use the **bootstrap**: rebuild the eval set 1,000 times by drawing examples at random with repeats allowed, score each, and keep the middle 95% of the scores.',
    ],
    example=example('Margin of error by eval set size', """examples   margin (about)
     25      ±20 points
    100      ±10 points
    400      ± 5 points
   1600      ± 2.5 points"""),
    check=question(
        'Your eval set has 100 questions. Prompt B scores 4 points higher than prompt A. Is that evidence B is better?',
        [
            'Yes, 4 points is a real gain',
            'Not on its own: with 100 examples each score is only good to about ±10 points',
            "No, evals can't compare prompts",
        ],
        answer=1,
        why='A 4-point gap is well inside the noise of a 100-example eval. Compare on the same examples, or use more of them.',
    ),
    angle=angle(
        pattern='Working a formula backwards',
        text='The margin is 100 divided by the square root of n. Flip it around: the square root of n is 100 divided by the margin, so n is that number squared. Then round up, because you cannot use part of an example.',
        say='"Before running, I check the eval set is big enough to detect the change I care about. To halve the margin I need four times the examples."',
        classic=None,
    ),
    stack=stack('MLflow: log the size and the margin with every run', """n = len(eval_set)
with mlflow.start_run(run_name="prompt-b"):
    mlflow.log_params({"eval_set": "faq-v4", "n_examples": n})
    mlflow.log_metric("margin_points", 100 / n ** 0.5)"""),
    exercise=exercise(
        title='How Big Must the Eval Set Be?',
        topic='experiments',
        difficulty='easy',
        fn='examples_needed',
        prompt="""Use the rule of thumb from the lesson: with `n` examples, a pass rate is good to about `100 / √n` percentage points.

Given the margin you can accept, `margin_points` (a number above 0), return the smallest whole number of examples that gets the margin down to that size or smaller.

For example, a margin of 10 points needs 100 examples, because 100 / √100 = 10.""",
        pattern='Rearrange the formula, then round up to a whole number.',
        target='a few arithmetic steps',
        realworld='Sizing an eval set before building it saves you from labelling 50 examples, running the comparison, and only then discovering the result is noise.',
        starter="""def examples_needed(margin_points):
    # your code here
    pass
""",
        solution="""def examples_needed(margin_points):
    root = 100 / margin_points
    exact = root * root
    n = int(exact)
    if n < exact:
        n += 1
    return n
""",
        cases=[
            case(10, expected=100, sample=True),
            case(5, expected=400),
            case(20, expected=25),
            case(3, expected=1112),
            case(7, expected=205),
        ],
        guided="""def examples_needed(margin_points):
    # Replace every ___ with real code, then run the tests.

    # Step 1: margin = 100 / sqrt(n), so sqrt(n) = 100 / margin.
    root = ___
    # Step 2: square it to get n.
    exact = root * root
    # Step 3: round up: int() rounds down, so add one if anything was cut off.
    n = int(exact)
    if ___:
        n += 1
    return n
""",
        fills=['100 / margin_points', 'n < exact'],
        concepts=[
            [
                'Rounding up',
                '`int()` throws away the part after the decimal point. If that changed the number, add one.',
                """int(204.08)   # 204, so round up to 205
int(100.0)    # 100, already whole""",
            ],
        ],
        byhand='A margin of 5: 100 / 5 = 20, and 20 × 20 = 400 examples. A margin of 7: 100 / 7 is about 14.29, squared about 204.08, so you need 205.',
        why='A fixed handful of arithmetic steps, whatever the margin.',
        gotchas=[
            [
                'It is a rule of thumb',
                'This margin assumes a pass rate near 50%, where it is widest. It is a planning number, not a precise one.',
            ],
            [
                'Per group, not just overall',
                'If you report each kind of question separately, each group needs enough examples on its own.',
            ],
        ],
    ),
)

lesson(MODULE, 'smoke_set',
    title='A smoke set for fast iteration',
    learn=[
        'Running every variant on hundreds of questions, several times, is slow and costs money. Most ideas are bad, and you can tell they are bad from far fewer questions.',
        'So keep a small, stratified **smoke set** for iterating: a few questions from every group, plus the whole must-pass set. Try ideas on it in minutes. Only the **finalists** go to the full dev set, and only the final winner goes to the holdout.',
        "Don't decide on the smoke set: it's too small for the margins to mean much. It's a filter for obviously bad ideas, not evidence for good ones.",
    ],
    example=example('Three stages, three sizes', """smoke set    40 questions    every idea           minutes, rough
dev set     400 questions    the 2-3 finalists    an hour, the real comparison
holdout     100 questions    the one winner       once, the confirmation"""),
    check=question(
        'A new prompt beats the current one 21 to 19 on your 40-question smoke set. What next?',
        [
            'Ship it',
            'Treat it as a finalist and compare properly on the full dev set',
            'Drop it',
        ],
        answer=1,
        why='The smoke set only screens out clear losers. A 2-question gap on 40 is noise, so the real comparison happens on the dev set.',
    ),
    angle=angle(
        pattern='Take the first few of each group',
        text='Walk the groups, take the first few ids from each (the ids are already shuffled), add the must-pass ids, and remove duplicates.',
        say='"I iterate on a stratified smoke set with the must-pass questions in it, and only run finalists on the full set."',
        classic=None,
    ),
    stack=stack('MLflow: the smoke set as its own dataset', """df = full.to_df()
df["group"] = df["tags"].map(lambda tags: tags["group"])
smoke = mlflow.genai.datasets.create_dataset(name="support-eval-smoke")
smoke.merge_records(df.groupby("group").head(8)[["inputs", "expectations", "tags"]])   # 8 per group"""),
    exercise=exercise(
        title='Pick the Smoke Set',
        topic='experiments',
        difficulty='easy',
        fn='smoke_set',
        prompt="""`ids_by_group` maps each group to its question ids, already shuffled. Take the first `per_group` ids from every group, add every id in `must_pass`, and return them all as one sorted list with no duplicates.""",
        pattern='First few of each group, plus a fixed list, as a set.',
        target='one pass over the groups',
        realworld='Teams iterate on a smoke set many times a day and run the full eval only for finalists, which keeps experiments fast and cheap.',
        starter="""def smoke_set(ids_by_group, per_group, must_pass):
    # your code here
    pass
""",
        solution="""def smoke_set(ids_by_group, per_group, must_pass):
    chosen = set(must_pass)
    for ids in ids_by_group.values():
        for qid in ids[:per_group]:
            chosen.add(qid)
    return sorted(chosen)
""",
        cases=[
            case({'billing': ['b3', 'b1', 'b7'], 'fraud': ['f2', 'f9']}, 1, ['f9'], expected=['b3', 'f2', 'f9'], sample=True),
            case({}, 3, [], expected=[]),
            case({'x': ['x1', 'x2']}, 5, ['x1'], expected=['x1', 'x2']),
            case({'a': ['a1', 'a2', 'a3'], 'b': ['b1']}, 2, ['z9'], expected=['a1', 'a2', 'b1', 'z9']),
        ],
        guided="""def smoke_set(ids_by_group, per_group, must_pass):
    # Replace every ___ with real code, then run the tests.
    # Step 1: a set removes duplicates for free. Start with every must-pass id.
    chosen = set(must_pass)
    for ids in ids_by_group.values():
        # Step 2: the first few of each group.
        for qid in ___:
            chosen.add(qid)
    return sorted(chosen)
""",
        fills=['ids[:per_group]'],
        concepts=[
            [
                'A set removes duplicates',
                'Adding something a set already has changes nothing.',
                """s = {"a"}
s.add("a")   # still {"a"}""",
            ],
        ],
        byhand='One per group: b3 from billing and f2 from fraud. Add the must-pass f9. Sorted: b3, f2, f9.',
        why='One pass over the groups, taking a few from each.',
        gotchas=[
            [
                'Keep it fixed',
                'Use the same smoke set for a whole round of ideas, so their numbers are comparable. Refresh it between rounds.',
            ],
            [
                'It leaks into your judgment',
                'You will look at the smoke set a lot. Keep it inside dev, never the holdout.',
            ],
        ],
    ),
)

lesson(MODULE, 'wilson_interval',
    title='Margins near 0% and 100%',
    learn=[
        'The ±100 ÷ √n rule from the last lesson breaks down when a pass rate is close to 0% or 100%. For 49 out of 50 it gives 94% to 102%: past 100%, which is impossible. And for 0 out of 30 it gives exactly 0% ± 0, as if one more test could never fail.',
        'The **Wilson interval** is the standard fix for a pass rate. It always stays between 0% and 100%, and it stays honest with small samples and extreme rates. With z = 1.96 for a 95% range, p the pass rate and n the number of examples:',
        'centre = (p + z² ÷ 2n) ÷ (1 + z² ÷ n), and half-width = z × √(p(1 − p) ÷ n + z² ÷ 4n²) ÷ (1 + z² ÷ n). The range is centre ± half-width. You do not need to remember it; you need to know to use it near the edges.',
        'This matters most for safety checks. "0 failures in 30 tries" does not mean the failure rate is 0%: the Wilson range goes up to about 11%.',
    ],
    example=example('Simple rule against Wilson', """49 of 50 passed (98%)
simple rule:  94.1% to 101.9%   ← past 100%: impossible
Wilson:       89.5% to  99.6%

0 of 30 got past the guardrail
simple rule:   0%  to 0%        ← "it can never happen"
Wilson:        0%  to 11.4%"""),
    check=question(
        '0 of 30 risky prompts got past your guardrail. What can you honestly say?',
        [
            'The leak rate is 0%',
            'The leak rate is probably low, but could be as high as about 11%',
            "Nothing at all, 30 is too few to say anything",
        ],
        answer=1,
        why='The Wilson range for 0 of 30 is 0% to about 11%. Thirty clean runs is evidence, but nowhere near proof of zero.',
    ),
    angle=angle(
        pattern='Plugging into a formula, then clamping',
        text='Work out the pass rate, plug it into the formula, then clamp the result to the range 0 to 1, because floating-point arithmetic can land a hair outside it. A fixed number of steps.',
        say='"For pass rates near 0 or 100% I use a Wilson interval, because the simple margin can go past 100% or claim zero risk."',
        classic=None,
    ),
    stack=stack('statsmodels: the same interval', """from statsmodels.stats.proportion import proportion_confint

low, high = proportion_confint(count=49, nobs=50, alpha=0.05, method="wilson")
mlflow.log_metrics({"pass_rate_low": low, "pass_rate_high": high})"""),
    exercise=exercise(
        title='The Wilson Interval',
        topic='experiments',
        difficulty='medium',
        fn='wilson_interval',
        prompt="""`passed` out of `total` examples passed. Return the 95% Wilson interval for the pass rate as `[low, high]`, each rounded to 3 decimal places. Use `z = 1.96`, `p = passed / total` and `n = total`:

- `centre = (p + z*z / (2*n)) / (1 + z*z / n)`
- `half = z * ((p * (1 - p) / n + z*z / (4*n*n)) ** 0.5) / (1 + z*z / n)`

Clamp `low` to at least `0.0` and `high` to at most `1.0`. If `total` is 0, return `[0.0, 1.0]`: with no data, anything is possible.""",
        pattern='Follow the formula step by step, then clamp.',
        target='a fixed number of steps',
        realworld='Reporting "98% (89.5% to 99.6%)" instead of "98%" tells a reviewer how much to trust the number, and stops anyone reading "0 failures" as "can never fail".',
        starter="""def wilson_interval(passed, total):
    # your code here
    pass
""",
        solution="""def wilson_interval(passed, total):
    if total == 0:
        return [0.0, 1.0]
    z = 1.96
    n = total
    p = passed / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denominator
    low = max(0.0, centre - half)
    high = min(1.0, centre + half)
    return [round(low, 3), round(high, 3)]
""",
        cases=[
            case(49, 50, expected=[0.895, 0.996], sample=True),
            case(0, 30, expected=[0.0, 0.114]),
            case(8, 10, expected=[0.49, 0.943]),
            case(50, 100, expected=[0.404, 0.596]),
            case(0, 0, expected=[0.0, 1.0]),
        ],
        guided="""def wilson_interval(passed, total):
    # Replace every ___ with real code, then run the tests.
    if total == 0:
        return [0.0, 1.0]
    z = 1.96
    n = total
    # Step 1: the pass rate.
    p = ___
    # Step 2: the formula, in pieces.
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denominator
    # Step 3: clamp to 0..1, because rounding can land a hair outside.
    low = max(0.0, centre - half)
    high = ___
    return [round(low, 3), round(high, 3)]
""",
        fills=['passed / n', 'min(1.0, centre + half)'],
        concepts=[
            [
                'Square root without an import',
                'Raising to the power 0.5 is the same as taking the square root.',
                """16 ** 0.5   # 4.0""",
            ],
            [
                'Clamping',
                '`max` keeps a value from going below a floor; `min` keeps it from going above a ceiling.',
                """max(0.0, -0.00001)   # 0.0
min(1.0, 1.00001)    # 1.0""",
            ],
        ],
        byhand='49 of 50: p = 0.98, n = 50, z² ≈ 3.84. The denominator is 1 + 3.84 ÷ 50 ≈ 1.077. The centre is (0.98 + 0.038) ÷ 1.077 ≈ 0.946, and the half-width about 0.051, so roughly 0.895 to 0.996.',
        why='A handful of arithmetic steps, whatever the numbers.',
        gotchas=[
            [
                'The centre is not the pass rate',
                'Wilson pulls the centre slightly towards 50%. That is deliberate: with few examples, extreme rates are usually a bit less extreme in reality.',
            ],
            [
                'Still assumes independent examples',
                'If many examples are near-copies of each other, the real uncertainty is bigger than any formula says.',
            ],
        ],
    ),
)

lesson(MODULE, 'clear_winner',
    title='Telling real gains from noise',
    learn=[
        'LLM outputs and LLM judges vary from run to run. A single comparison of 0.82 against 0.80 may just be luck.',
        'Run each setup several times (3 to 5 is common), and only call a winner when the results clearly separate. If they overlap, choose on cost or speed, or test on more examples.',
        "This rule is deliberately cautious: it never crowns a fake winner, but it can miss a real one, because overlapping ranges don't prove there is no difference. When both setups ran on the same examples, a **paired comparison** is the standard check, and it is more sensitive. That is the next lesson.",
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

lesson(MODULE, 'paired_verdict',
    title='Comparing on the same examples',
    learn=[
        'The best way to compare two setups is to run both on **the same examples** and look example by example. This is a **paired comparison**. It is much more sensitive than comparing two overall scores, because the hard examples are hard for both setups and that difficulty cancels out.',
        'Where both pass, or both fail, an example tells you nothing about which is better. Only the **disagreements** count: how often A passed where B failed, and the other way round. If the disagreements split about evenly, the difference is noise.',
        "The standard check for pass/fail results is **McNemar's test**. In plain words: call a winner only if the gap between the two counts is at least **2 × √(number of disagreements)**. With 20 disagreements that means winning about 15 to 5; 12 to 8 is too close to call.",
        'This replaces the "ranges must not overlap" rule from the previous lesson whenever both setups ran on the same examples. For scores that are not pass/fail, the paired versions are a **paired bootstrap** or a **permutation test**.',
    ],
    example=example('Only disagreements count', """example   A   B
q1        ✓   ✓    agree: ignore
q2        ✓   ✗    A only
q3        ✗   ✓    B only
q4        ✗   ✗    agree: ignore
...
A only 15, B only 5:  15 - 5 = 10,  2 × √20 ≈ 8.9,  10 ≥ 8.9  → A wins
A only 12, B only 8:  12 - 8 = 4,   4 < 8.9                → too close"""),
    check=question(
        'Out of 200 questions, A and B disagree on 20. A wins 12 of those and B wins 8. What do you conclude?',
        [
            'A is better: it won more',
            'Too close to call: the gap of 4 is below 2 × √20, about 8.9',
            'B is better',
        ],
        answer=1,
        why='The 180 agreements say nothing about which is better. Of the 20 that do, a 12 to 8 split is easily luck.',
    ),
    angle=angle(
        pattern='Walking two lists in step',
        text='`zip` walks both lists together, one example at a time, so you count the disagreements in a single pass. Comparing squared numbers avoids taking a square root at all.',
        say='"I run both systems on the same examples and only count where they disagree. That is McNemar\'s test, and it is far more sensitive than comparing two averages."',
        classic=None,
    ),
    stack=stack('MLflow: log the paired counts', """with mlflow.start_run(run_name="prompt-a-vs-b"):
    mlflow.log_params({"eval_set": "faq-v4", "test": "mcnemar"})
    mlflow.log_metrics({"a_only": a_only, "b_only": b_only})"""),
    exercise=exercise(
        title='Who Wins on the Same Examples?',
        topic='experiments',
        difficulty='medium',
        fn='paired_verdict',
        prompt="""Two setups ran on the same examples. `a_passed[i]` and `b_passed[i]` say whether each one passed example `i` (the lists are the same length).

Count the examples where only A passed, and where only B passed. Call a winner only if the gap between those two counts is at least `2 × √(their total)`. Return `"a"` or `"b"` for a clear winner, or `"tie"` otherwise, including when they never disagree.""",
        pattern='Count the disagreements in one pass, then apply the rule.',
        target='one walk through both lists together',
        realworld='This is how a careful team decides whether a new prompt or model is really better on an eval set: same examples, count where they differ, and refuse to ship on a split that luck could explain.',
        starter="""def paired_verdict(a_passed, b_passed):
    # your code here
    pass
""",
        solution="""def paired_verdict(a_passed, b_passed):
    a_only = 0
    b_only = 0
    for a, b in zip(a_passed, b_passed):
        if a and not b:
            a_only += 1
        elif b and not a:
            b_only += 1
    disagreements = a_only + b_only
    diff = a_only - b_only
    if disagreements == 0 or diff * diff < 4 * disagreements:
        return "tie"
    return "a" if diff > 0 else "b"
""",
        cases=[
            case([True] * 4 + [True] * 15 + [False] * 5 + [False] * 2,
                 [True] * 4 + [False] * 15 + [True] * 5 + [False] * 2, expected='a', sample=True),
            case([True] * 12 + [False] * 8 + [True] * 30,
                 [False] * 12 + [True] * 8 + [True] * 30, expected='tie'),
            case([True, False, True], [True, False, True], expected='tie'),
            case([False] * 6 + [True] * 10, [True] * 6 + [True] * 10, expected='b'),
            case([True, True, True, False], [False, False, False, False], expected='tie'),
            case([], [], expected='tie'),
        ],
        guided="""def paired_verdict(a_passed, b_passed):
    # Replace every ___ with real code, then run the tests.
    a_only = 0
    b_only = 0

    # Step 1: walk both lists together; only disagreements count.
    for a, b in zip(a_passed, b_passed):
        if a and not b:
            a_only += 1
        elif ___:
            b_only += 1

    disagreements = a_only + b_only
    diff = a_only - b_only

    # Step 2: the rule is |diff| >= 2 * sqrt(disagreements).
    # Squaring both sides gives diff * diff >= 4 * disagreements, with no square root.
    if disagreements == 0 or ___ < 4 * disagreements:
        return "tie"
    return "a" if diff > 0 else "b"
""",
        fills=['b and not a', 'diff * diff'],
        concepts=[
            [
                'zip',
                'Walks two lists side by side, giving you one item from each at a time.',
                """for a, b in zip([True, False], [True, True]):
    print(a, b)   # True True, then False True""",
            ],
        ],
        byhand='The first case: 4 examples both pass, 15 only A passes, 5 only B passes, 2 both fail. Disagreements: 20. Gap: 15 - 5 = 10. 10 × 10 = 100, and 4 × 20 = 80. 100 is at least 80, so A wins.',
        why='One step per example, walking both lists together.',
        gotchas=[
            [
                'Small samples cannot decide',
                'Three disagreements all going A\'s way still is not enough: 3 × 3 = 9 is less than 4 × 3 = 12. With few disagreements, the honest answer is "tie".',
            ],
            [
                'Same examples, same order',
                'Pairing only works if position i is the same example for both setups. Line them up by example id first.',
            ],
            [
                'Why 2?',
                "It is a rounded version of 1.96, the number behind a 95% range. That rounding makes the rule very slightly stricter than McNemar's test, which is the safe direction.",
            ],
        ],
    ),
)

lesson(MODULE, 'biggest_gap',
    title='Oracle tests: find the bottleneck',
    learn=[
        'A RAG app or an agent is a chain of steps, and a bad answer could come from any of them. An **oracle test** replaces one step with a perfect version and reruns the eval: hand the model the right documents instead of what retrieval found, or give the agent correct tool results.',
        "The gap between the oracle run and your current system is that step's **headroom**: the most you could gain by perfecting it. If perfect documents only lift you from 78% to 80%, retrieval isn't your problem, and tuning it is wasted effort. If they lift you to 91%, it is.",
        'Plan oracle runs in the **Design** stage, as extra variants alongside the ones you are testing, and read them first in **Evaluate**. They need the right answers for each step in the eval set, like the correct document ids for each question.',
    ],
    example=example('Headroom per step', """current system                         78%
oracle retrieval (right docs given)    91%   → retrieval headroom: 13 points
oracle reranking (right doc first)     84%   → reranking headroom:  6 points
oracle prompt (expert-written)         80%   → prompt headroom:     2 points
→ work on retrieval first"""),
    check=question(
        'Your RAG app scores 70%. Given the right documents directly, it scores 72%. Where should you look next?',
        [
            'Retrieval: it must be the problem',
            'Generation: even with perfect documents the answers are poor, so the prompt or model is the bottleneck',
            'Nowhere, 70% is fine',
        ],
        answer=1,
        why='Perfect retrieval only adds 2 points, so most misses happen after the documents arrive.',
    ),
    angle=angle(
        pattern='Find the largest gap',
        text='Subtract the current score from each oracle score and keep the biggest: the "best so far" pattern over a dict.',
        say='"Before optimising a pipeline I run oracle tests on each step, so I know which step has the most headroom."',
        classic=None,
    ),
    stack=stack('MLflow: the oracle as one more named variant', """def oracle_app(question, gold_doc_ids):
    docs = [lookup(i) for i in gold_doc_ids]        # skip retrieval: the right docs, directly
    return generate(question, docs)

mlflow.set_active_model(name="rag-oracle-retrieval")
mlflow.genai.evaluate(data=eval_set, predict_fn=oracle_app, scorers=[correct])"""),
    exercise=exercise(
        title='Where Is the Headroom?',
        topic='experiments',
        difficulty='easy',
        fn='biggest_gap',
        prompt="""`current` is your system's pass rate, like `0.78`. `oracles` maps each step to the pass rate when that step is replaced by a perfect version, like `{"retrieval": 0.91, "reranking": 0.84}`.

Return `[step, points]` for the step with the most headroom, where `points` is `(oracle - current) × 100`, rounded to a whole number. If two steps tie, pick the one that comes first alphabetically. If no oracle beats the current system, return `[None, 0]`.""",
        pattern='Best so far over a dict, with a tie-break.',
        target='one pass over the steps',
        realworld='Oracle tests stop teams from spending a month on the step that was already nearly perfect.',
        starter="""def biggest_gap(current, oracles):
    # your code here
    pass
""",
        solution="""def biggest_gap(current, oracles):
    best_step = None
    best_points = 0
    for step in sorted(oracles):
        points = int(round((oracles[step] - current) * 100))
        if points > best_points:
            best_step, best_points = step, points
    return [best_step, best_points]
""",
        cases=[
            case(0.78, {'retrieval': 0.91, 'reranking': 0.84, 'prompt': 0.8}, expected=['retrieval', 13], sample=True),
            case(0.7, {'retrieval': 0.72, 'generation': 0.9}, expected=['generation', 20]),
            case(0.9, {'retrieval': 0.88}, expected=[None, 0]),
            case(0.5, {'b': 0.6, 'a': 0.6}, expected=['a', 10]),
            case(0.8, {}, expected=[None, 0]),
        ],
        guided="""def biggest_gap(current, oracles):
    # Replace every ___ with real code, then run the tests.
    best_step = None
    best_points = 0
    # Step 1: alphabetical order, so the first of any tie wins.
    for step in sorted(oracles):
        # Step 2: headroom in whole points.
        points = ___
        # Step 3: keep it only if it beats the best so far.
        if ___:
            best_step, best_points = step, points
    return [best_step, best_points]
""",
        fills=['int(round((oracles[step] - current) * 100))', 'points > best_points'],
        concepts=[
            [
                'sorted over a dict',
                'Sorting a dict gives its keys in order, which makes tie-breaks predictable.',
                """sorted({"b": 1, "a": 2})   # ["a", "b"]""",
            ],
        ],
        byhand='retrieval: 91 − 78 = 13 points. reranking: 84 − 78 = 6. prompt: 80 − 78 = 2. The biggest is retrieval, 13.',
        why='One look at each step.',
        gotchas=[
            [
                'Headroom is not a promise',
                'The oracle is perfect; your real fix will not be. Headroom tells you where gains are possible, not how much you will get.',
            ],
            [
                'Gaps need margins too',
                'On a small eval set, a 2-point gap is noise. Compare oracle and current on the same questions, the paired way.',
            ],
        ],
    ),
)

lesson(MODULE, 'ablation_report',
    title='Ablations: what each part is worth',
    learn=[
        'A pipeline collects parts over time: query rewriting, a reranker, memory, an extra node in the graph. Some earn their cost; some do nothing. An **ablation** removes one part at a time, keeping everything else, and reruns the eval.',
        "The drop when a part is removed is that part's **contribution**. A part whose removal changes nothing measurable is a candidate to delete: less to run, pay for and debug.",
        'Plan ablations in the **Design** stage as extra variants of your best version, and read them in **Evaluate**. Judge each drop against the margin of your eval set: a 1-point drop on 100 questions is noise.',
    ],
    example=example('Removing one part at a time', """full pipeline (rewrite + rerank + memory)   86%
without query rewrite                      85%   → contributes  1 point (within noise)
without reranker                           79%   → contributes  7 points
without memory                             86%   → contributes  0 points
→ keep the reranker; the rewrite and memory are candidates to remove"""),
    check=question(
        'Removing query rewriting changes the score from 86% to 85% on 100 questions. What do you conclude?',
        [
            'Rewriting adds 1 point, so keep it',
            "Its effect is within the noise: it may not be worth its cost, so test it with more examples or drop it",
            'Rewriting hurts quality',
        ],
        answer=1,
        why='With 100 questions the margin is around 10 points. A 1-point drop says nothing either way.',
    ),
    angle=angle(
        pattern='Differences, then sort',
        text='Subtract each ablation score from the full score, then sort by the drop, biggest first, with a tie-break so the order is always the same.',
        say='"I ablate each component of the pipeline and keep only the ones whose removal costs more than the noise."',
        classic=None,
    ),
    stack=stack('LangGraph: build the graph with a part switched off', """def build_graph(use_rerank=True, use_rewrite=True):
    g = StateGraph(State)
    g.add_node("retrieve", retrieve)
    if use_rewrite:
        g.add_node("rewrite", rewrite)
    if use_rerank:
        g.add_node("rerank", rerank)
    ...   # wire the edges for the parts that are on
    return g.compile()"""),
    exercise=exercise(
        title='What Is Each Part Worth?',
        topic='experiments',
        difficulty='easy',
        fn='ablation_report',
        prompt="""`full` is the pass rate of the whole pipeline, like `0.86`. `without` maps each part to the pass rate with that part removed, like `{"rerank": 0.79, "memory": 0.86}`.

Return a list of `[part, points]`, where `points` is `(full - without) × 100` rounded to a whole number: what the part contributes. Sort by points, biggest first; break ties alphabetically by part.""",
        pattern='Compute a difference per part, then sort by two keys.',
        target='one pass, then a sort',
        realworld='Pipelines grow parts that nobody dares remove. Ablations give you the evidence to simplify, which saves cost and makes debugging easier.',
        starter="""def ablation_report(full, without):
    # your code here
    pass
""",
        solution="""def ablation_report(full, without):
    rows = []
    for part in without:
        rows.append([part, int(round((full - without[part]) * 100))])
    rows.sort(key=lambda row: (-row[1], row[0]))
    return rows
""",
        cases=[
            case(0.86, {'rewrite': 0.85, 'rerank': 0.79, 'memory': 0.86}, expected=[['rerank', 7], ['rewrite', 1], ['memory', 0]], sample=True),
            case(0.9, {}, expected=[]),
            case(0.8, {'b': 0.75, 'a': 0.75}, expected=[['a', 5], ['b', 5]]),
            case(0.7, {'cache': 0.74}, expected=[['cache', -4]]),
        ],
        guided="""def ablation_report(full, without):
    # Replace every ___ with real code, then run the tests.
    rows = []
    for part in without:
        # Step 1: what removing this part cost, in whole points.
        rows.append([part, ___])
    # Step 2: biggest contribution first; ties alphabetical.
    rows.sort(key=lambda row: ___)
    return rows
""",
        fills=['int(round((full - without[part]) * 100))', '(-row[1], row[0])'],
        concepts=[
            [
                'Sorting by two things',
                'A key that returns a pair sorts by the first item, then the second. A minus sign makes numbers sort biggest first.',
                """rows = [["b", 5], ["a", 5], ["c", 9]]
rows.sort(key=lambda r: (-r[1], r[0]))   # c, a, b""",
            ],
        ],
        byhand='rerank: 86 − 79 = 7. rewrite: 86 − 85 = 1. memory: 86 − 86 = 0. Sorted biggest first: rerank 7, rewrite 1, memory 0.',
        why='One subtraction per part, then a sort.',
        gotchas=[
            [
                'A negative contribution',
                'If removing a part *raises* the score, that part is actively hurting. It will show up last, with negative points.',
            ],
            [
                'Parts can depend on each other',
                'Query rewriting might only help when the reranker is on. Removing one part at a time can miss that; if you suspect it, also test them removed together.',
            ],
        ],
    ),
)

lesson(MODULE, 'fluke_risk',
    title='Testing many variants',
    learn=[
        'Each comparison has a small chance of declaring a winner by luck. With the usual 95% standard, that is 5%. Test one variant and a fluke is unlikely; test twenty, and the chance that at least one "wins" by luck is about 64%.',
        'This is how teams fool themselves: try many prompts, keep the best, report its score. The best of many is partly luck, so its score on the same eval set is too optimistic.',
        "Two guards. In **Design**, limit how many variants you test, and for a strict check divide the 5% by the number of comparisons (the **Bonferroni** correction). In **Evaluate**, confirm the winner **once** on the holdout set it has never seen. That confirmation is the reason the holdout set exists.",
    ],
    example=example('The chance of at least one fluke', """variants tested    chance one wins by luck    stricter threshold
       1                    5%                    5%
       5                   23%                    1%
      10                   40%                    0.5%
      20                   64%                    0.25%"""),
    check=question(
        'You tried 15 prompt variants on the dev set and one beat the current prompt clearly. What should you do before shipping it?',
        [
            'Ship it: it won clearly',
            'Confirm it once on the holdout set, because the best of 15 is partly luck',
            'Try 15 more variants to be sure',
        ],
        answer=1,
        why='Picking the best of many inflates its score. One clean test on unseen examples tells you whether the win was real.',
    ),
    angle=angle(
        pattern='Chance of at least one',
        text='The chance that none of n comparisons is a fluke is 0.95 multiplied by itself n times. One minus that is the chance of at least one.',
        say='"When I compare many variants I limit how many, and I confirm the winner once on a holdout set before trusting its score."',
        classic=None,
    ),
    stack=stack('MLflow: confirm the dev winner on the holdout, once', """winner = pick_best(mlflow.search_runs(experiment_names=["prompt-search"], filter_string="tags.split = 'dev'"))
with mlflow.start_run(run_name=f"{winner}-holdout"):
    mlflow.set_tag("split", "holdout")
    mlflow.genai.evaluate(data=holdout_set, predict_fn=build_app(winner), scorers=[correct])"""),
    exercise=exercise(
        title='How Likely Is a Fluke?',
        topic='experiments',
        difficulty='easy',
        fn='fluke_risk',
        prompt="""You will compare `n` variants (at least 1), each tested at the usual 5% fluke rate.

Return `[chance, threshold]`:

- `chance`: the probability that at least one comparison wins by luck, `1 - 0.95 ** n`, rounded to 2 decimal places
- `threshold`: the stricter Bonferroni threshold, `0.05 / n`, rounded to 4 decimal places""",
        pattern='Two short formulas.',
        target='a fixed number of steps',
        realworld='Prompt and hyperparameter searches routinely try dozens of variants. Knowing the fluke rate is why serious teams hold out a final test set.',
        starter="""def fluke_risk(n):
    # your code here
    pass
""",
        solution="""def fluke_risk(n):
    chance = 1 - 0.95 ** n
    threshold = 0.05 / n
    return [round(chance, 2), round(threshold, 4)]
""",
        cases=[
            case(20, expected=[0.64, 0.0025], sample=True),
            case(1, expected=[0.05, 0.05]),
            case(10, expected=[0.4, 0.005]),
            case(5, expected=[0.23, 0.01]),
        ],
        guided="""def fluke_risk(n):
    # Replace every ___ with real code, then run the tests.
    # Step 1: chance that no comparison is a fluke is 0.95, n times over.
    chance = 1 - ___
    # Step 2: the stricter threshold shares the 5% across all n comparisons.
    threshold = ___
    return [round(chance, 2), round(threshold, 4)]
""",
        fills=['0.95 ** n', '0.05 / n'],
        concepts=[
            [
                'Powers',
                '`**` multiplies a number by itself that many times.',
                """0.95 ** 2   # 0.9025, the chance two comparisons are both clean""",
            ],
        ],
        byhand='20 variants: 0.95 to the power 20 is about 0.36, so the chance of at least one fluke is about 0.64. The stricter threshold is 0.05 ÷ 20 = 0.0025.',
        why='Two arithmetic steps.',
        gotchas=[
            [
                'It counts every look',
                'Checking the results after each tweak and stopping when one looks good is also many comparisons, even if you never wrote them down.',
            ],
            [
                'Bonferroni is strict',
                'It makes real wins harder to detect. The holdout confirmation is often the more practical guard.',
            ],
        ],
    ),
)
