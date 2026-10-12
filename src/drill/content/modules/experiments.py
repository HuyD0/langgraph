"""Experiment design with MLflow: Runs, grids, fair comparisons and decisions you can defend."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('experiments', 'Experiment design with MLflow', 'Runs, grids, fair comparisons and decisions you can defend.')

lesson(MODULE, 'best_run',
    title='Experiments, runs and the lifecycle',
    learn=[
        'An **experiment** answers one question, like "which chunk size (how big a piece each document is cut into) gives the best answers under 1.5 seconds?". Each attempt is a **run** that records its **parameters** (what you set), **metrics** (what you measured) and **artifacts** (files, like the eval results).',
        'The metrics usually come from an **eval set**: a fixed list of test questions with known good answers. Each answer is often marked by an **LLM judge**, a model that grades answers.',
        'MLflow stores all of this so you can compare runs side by side instead of in a spreadsheet. Write the decision rule down before you run anything, for example "highest quality at $2 or less per 1,000 requests". That\'s what turns an experiment into a decision, and a decision into return on the time spent.',
        'This course follows one **lifecycle**, the strip at the top of the page: **Frame** (decide the question), **Design** (plan the runs and how you will judge them), **Build and trace**, **Evaluate** (score the runs and read the results against your plan), **Ship** and **Monitor**. This module is about Design.',
    ],
    example=example('One run, logged', """import mlflow
mlflow.set_experiment("/Shared/support-bot-rag")
with mlflow.start_run(run_name="cs512-k5"):
    mlflow.log_params({"chunk_size": 512, "k": 5, "model": "fast-model"})
    mlflow.log_metrics({"quality": 0.81, "cost_per_1k": 1.8})"""),
    check=question(
        'You tried 12 setups (configurations) and the best quality costs three times your budget. What should the experiment have had from the start?',
        ['More setups', 'A decision rule that includes the budget', 'A bigger model'],
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
    filter_string="metrics.cost_per_1k <= 2.0",
    order_by=["metrics.quality DESC"],
)
best = runs.iloc[0]"""),
    exercise=exercise(
        title='Pick the Best Run',
        topic='experiments',
        difficulty='easy',
        fn='best_run',
        prompt="""Your function gets two things:

- `runs`: a list of runs from an experiment. Each run is a dict like `{"run_name": "a", "quality": 0.81, "cost": 1.8}`. `cost` is dollars per 1,000 requests.
- `max_cost`: your budget, like `2`.

Skip every run whose `cost` is more than `max_cost`. A run that costs exactly `max_cost` still fits. Of the runs left, return the `run_name` of the one with the highest `quality`. If two have the same quality, keep the earlier one. If no run fits the budget, return `None`.""",
        pattern='Skip runs over the budget, and keep the best run seen so far.',
        target='one pass over the runs',
        realworld='This is what `mlflow.search_runs` with a filter and an order does. Deciding the constraint (budget, latency) before looking at results stops you picking whatever looks best afterwards.',
        starter="""def best_run(runs, max_cost):
    # your code here
    pass
""",
        solution="""def best_run(runs, max_cost):
    best = None
    for run in runs:
        if run["cost"] > max_cost:
            continue
        if best is None or run["quality"] > best["quality"]:
            best = run
    if best is None:
        return None
    return best["run_name"]
""",
        cases=[
            case([
                {'run_name': 'a', 'quality': 0.74, 'cost': 1.1},
                {'run_name': 'b', 'quality': 0.81, 'cost': 1.8},
                {'run_name': 'c', 'quality': 0.84, 'cost': 3.2},
            ], 2, expected='b', sample=True),
            case([], 5.0, expected=None),
            case([{'run_name': 'a', 'quality': 0.9, 'cost': 9.0}], 1.0, expected=None),
            case([{'run_name': 'a', 'quality': 0.8, 'cost': 2.0}], 2.0, expected='a'),
            case([{'run_name': 'a', 'quality': 0.8, 'cost': 1.0}, {'run_name': 'b', 'quality': 0.8, 'cost': 1.5}], 2.0, expected='a'),
            case([{'run_name': 'a', 'quality': 0.7, 'cost': 1.0}, {'run_name': 'b', 'quality': 0.75, 'cost': 1.0}], 1.0, expected='b'),
        ],
        guided="""def best_run(runs, max_cost):
    # Replace every ___ with real code, then run the tests.

    best = None   # no run kept yet
    for run in runs:
        # Step 1: skip a run that costs more than max_cost.
        if ___:
            continue
        # Step 2: keep this run if nothing is kept yet,
        # or if its quality beats best["quality"].
        # (A tie does not beat it.)
        if best is None or ___:
            best = run
    # Step 3: give back the name, or None if nothing fit.
    if best is None:
        return None
    return best["run_name"]
""",
        fills=['run["cost"] > max_cost', 'run["quality"] > best["quality"]'],
        concepts=[
            [
                'continue',
                'Skips the rest of this turn of the loop and moves on to the next item.',
                """for n in [3, -1, 5]:
    if n < 0:
        continue
    print(n)   # prints 3, then 5""",
            ],
            [
                'None as "nothing yet"',
                'Start a variable at `None`, then replace it with the first real value. `x is None` checks whether anything has been kept yet.',
                """best = None
if best is None:
    print("nothing kept yet")""",
            ],
        ],
        byhand='The budget is 2. Run a costs 1.1, so it fits. Nothing is kept yet, so a is the best so far, with quality 0.74. Run b costs 1.8, so it fits. Its quality, 0.81, beats 0.74, so b is the new best. Run c costs 3.2, more than 2, so skip it, even though its quality is highest. Return "b".',
        why='One pass over the runs.',
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
    "metric": "hint quality; also check speed",
    "runs": 3,
    "test": "paired (same examples for both)",
    "decision_rule": "switch only if B wins clearly and stays fast",
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
        prompt="""`plan` is a dict that describes an experiment before you run it, like `{"question": "Is B better?", "runs": 3}`.

A plan needs these seven fields, in this order: `question`, `change`, `eval_set`, `metric`, `runs`, `test`, `decision_rule`.

A field is a gap if it is missing from `plan`, if its value is `None`, or if its value is empty text, `""`. Return a list of the gaps, in the order above. If there are none, return `[]`.""",
        pattern='Walk the fixed list of required fields once, looking each one up in the dict.',
        target='one pass over the required fields',
        realworld='A team that logs the plan with every MLflow run can show, months later, that the rule came before the result. Blocking a run until the plan is complete turns that from a good intention into a habit.',
        starter="""def plan_gaps(plan):
    # your code here
    pass
""",
        solution="""def plan_gaps(plan):
    required = ["question", "change", "eval_set", "metric",
                "runs", "test", "decision_rule"]
    gaps = []
    for field in required:
        value = plan.get(field)
        if value is None or value == "":
            gaps.append(field)
    return gaps
""",
        cases=[
            case({'question': 'Is B better?', 'change': 'model', 'eval_set': 'v3', 'metric': 'accuracy', 'runs': 3, 'test': ''}, expected=['test', 'decision_rule'], sample=True),
            case({'question': 'Is B better?', 'change': 'model', 'eval_set': 'v3', 'metric': 'accuracy', 'runs': 3, 'test': 'paired', 'decision_rule': 'B wins clearly'}, expected=[]),
            case({}, expected=['question', 'change', 'eval_set', 'metric', 'runs', 'test', 'decision_rule']),
            case({'question': '', 'change': 'prompt', 'eval_set': None, 'metric': 'groundedness', 'runs': 5, 'test': 'paired', 'decision_rule': 'win by 2x'}, expected=['question', 'eval_set']),
        ],
        guided="""def plan_gaps(plan):
    # Replace every ___ with real code, then run the tests.
    required = ["question", "change", "eval_set", "metric",
                "runs", "test", "decision_rule"]
    gaps = []
    for field in required:
        # Step 1: look the field up with .get, which
        # gives None when the field is missing.
        value = ___
        # Step 2: a gap is None, or empty text "".
        if ___:
            gaps.append(field)
    return gaps
""",
        fills=['plan.get(field)', 'value is None or value == ""'],
        concepts=[
            [
                'dict.get',
                'Looks up a key. When the key is missing, it gives `None` instead of an error.',
                """ages = {"ann": 30}
ages.get("ann")   # 30
ages.get("bo")    # None""",
            ],
            [
                'Two checks with or',
                '`a or b` is True when either side is True.',
                """colour = ""
colour is None or colour == ""   # True""",
            ],
        ],
        byhand='Check the seven fields in order. question, change, eval_set, metric and runs all have values. test is "", empty text, so it is a gap. decision_rule is not in the plan at all, so it is a gap too. Return ["test", "decision_rule"].',
        why='One step per required field, and each dict lookup is instant.',
        gotchas=[
            [
                'Spaces are not an answer',
                'A field holding `"   "` looks filled in but says nothing. A stricter check strips the spaces first: `value.strip() == ""`.',
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
        'Every value you add multiplies the number of runs. 3 chunk sizes times 4 values of k (how many pieces to fetch for each question) times 2 models is 24 runs, each paying for eval and judge calls. Count the runs, and their cost, before you start.',
    ],
    example=example('2 chunk sizes times 2 values of k: 4 runs', """chunk_size   k
256          3    run 1
256          5    run 2
512          3    run 3
512          5    run 4
try 3 models as well: 4 times 3 is 12 runs"""),
    check=question(
        'You want to test 4 chunk sizes, 5 values of k and 3 models. How many runs is a full grid?',
        ['12', '60', '20'],
        answer=1,
        why="4 times 5 times 3 is 60. That's why you fix some settings and vary two or three at a time.",
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
        prompt="""`settings` is a list of settings to try. Each setting is a pair, `[name, values]`, like `["k", [3, 5]]`.

Return every combination, with one value for each setting, as a list of dicts like `{"chunk_size": 256, "k": 3}`.

`settings` can hold any number of settings (the tests use 1, 2 and 3), so you can't write one loop per setting. Instead, start from a list with one empty combination, `[{}]`, and build it up one setting at a time.

Keep the order shown in the example: the last setting changes fastest. In the example, `k` goes 3, 5, then 3, 5 again.""",
        pattern='Build the combinations one setting at a time: copy each combination so far once for every value of the next setting.',
        target='one step per combination you produce',
        realworld='Grid search. The number of runs is the sizes multiplied together: 3 chunk sizes times 4 values of k times 2 models is already 24 runs, each with eval and judge costs. Seeing that number before you start is half of experiment design.',
        starter="""def param_grid(settings):
    # your code here
    pass
""",
        solution="""def param_grid(settings):
    combos = [{}]
    for name, values in settings:
        grown = []
        for combo in combos:
            for value in values:
                new_combo = dict(combo)
                new_combo[name] = value
                grown.append(new_combo)
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
            case([['model', ['fast-model']]], expected=[{'model': 'fast-model'}]),
            case([['k', [3, 5, 10]]], expected=[{'k': 3}, {'k': 5}, {'k': 10}]),
            case([['model', ['small', 'large']], ['k', [5]]], expected=[
                {'model': 'small', 'k': 5},
                {'model': 'large', 'k': 5},
            ]),
            case([['a', [1, 2, 3]], ['b', ['x']], ['c', [True, False]]], expected=[
                {'a': 1, 'b': 'x', 'c': True},
                {'a': 1, 'b': 'x', 'c': False},
                {'a': 2, 'b': 'x', 'c': True},
                {'a': 2, 'b': 'x', 'c': False},
                {'a': 3, 'b': 'x', 'c': True},
                {'a': 3, 'b': 'x', 'c': False},
            ]),
        ],
        guided="""def param_grid(settings):
    # Replace every ___ with real code, then run the tests.

    # Start from one empty combination.
    combos = [{}]
    for name, values in settings:
        grown = []
        # Step 1: for every combination so far,
        # try every value of this setting.
        for combo in combos:
            for value in values:
                # Step 2: copy the combination, so the
                # original stays as it is. Add the value.
                new_combo = ___
                new_combo[name] = value
                grown.append(new_combo)
        # Step 3: the grown list is the starting
        # point for the next setting.
        combos = ___
    return combos
""",
        fills=['dict(combo)', 'grown'],
        concepts=[
            [
                'Unpacking pairs in a loop',
                'When each item is a pair, you can give both halves a name in the `for` line.',
                """pairs = [["ann", 30], ["bo", 25]]
for name, age in pairs:
    print(name, age)
# ann 30, then bo 25""",
            ],
            [
                'Copying a dict',
                '`dict(d)` makes a new dict with the same keys, so changing the copy leaves the original alone.',
                """a = {"size": 3}
b = dict(a)
b["size"] = 5   # a is still {"size": 3}""",
            ],
            [
                'Which value changes fastest',
                'With a loop inside a loop, the inner loop runs all the way through for each outer item, so the inner value changes fastest. Here, colour changes fastest.',
                """for size in ["S", "M"]:
    for colour in ["red", "blue"]:
        print(size, colour)
# S red, S blue,
# M red, M blue""",
            ],
        ],
        byhand='Start with one empty combination, {}. Add chunk_size: copy {} once for each value, giving {"chunk_size": 256} and {"chunk_size": 512}. Add k: copy each of those once for 3 and once for 5. That gives 256 with 3, 256 with 5, 512 with 3 and 512 with 5. Return those 4 dicts, in that order.',
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
        'For a classifier (spam, churn, fraud), one train/test split can be lucky or unlucky. **Cross-validation** splits the data into a few equal groups called **folds** (often 5) and trains once per fold: each time it tests on that fold and trains on all the others.',
        'You get one score per fold instead of one overall: report the average and how much they vary. Compare models on the same folds, and log every model as an MLflow run so the comparison is reproducible.',
    ],
    example=example('10 examples, 5 folds, 5 rounds', """fold 0: examples 0, 5
fold 1: examples 1, 6
fold 2: examples 2, 7
fold 3: examples 3, 8
fold 4: examples 4, 9

round 1: test on fold 0, train on folds 1, 2, 3, 4
round 2: test on fold 1, train on folds 0, 2, 3, 4
...
round 5: test on fold 4, train on folds 0, 1, 2, 3
→ 5 scores: report the average and how much they vary"""),
    check=question(
        'Model A scores 0.80 on every fold. Model B scores 0.95, 0.60, 0.90, 0.70, 0.85 (also 0.80 on average). Which is the safer choice?',
        ['A: same average, much more predictable', 'B: it reaches 0.95', "They're the same"],
        answer=0,
        why='Same average, but B swings widely depending on the data it sees. Production data will swing too.',
    ),
    angle=angle(
        pattern='Dealing round-robin',
        text='Each example goes to fold `i % num_folds`, like dealing cards. One step per example.',
        say='"I put example i in the fold given by the remainder when I divide i by the number of folds, so folds differ in size by at most one; with real data I\'d shuffle first and keep each customer in a single fold."',
        classic=None,
    ),
    stack=stack('scikit-learn with MLflow autologging', """import mlflow
from sklearn.model_selection import cross_val_score

mlflow.sklearn.autolog()
with mlflow.start_run(run_name="logreg-5fold"):
    # F1: one score that balances precision and recall
    scores = cross_val_score(model, X, y, cv=5, scoring="f1")
    mlflow.log_metrics({"f1_mean": scores.mean(), "f1_min": scores.min()})"""),
    exercise=exercise(
        title='Cross-Validation Folds',
        topic='experiments',
        difficulty='easy',
        fn='cv_folds',
        prompt="""**Cross-validation** splits the examples into groups called folds. Each fold takes a turn as the test set. Your function gets two things:

- `num_examples`: how many examples there are, like `7`. They are numbered from `0` up to `num_examples - 1`.
- `num_folds`: how many folds to make, like `3`.

Deal the examples out like cards: example `i` goes into fold number `i % num_folds`, the remainder when you divide `i` by `num_folds`.

Return a list with one inner list per fold, fold 0 first. Each fold holds its example numbers, smallest first. If there are fewer examples than folds, some folds stay empty.""",
        pattern='Deal the examples out in turn, like dealing cards to players.',
        target='one step per example',
        realworld="This is how a classifier gets a more trustworthy score: train 5 times, test on 5 different folds, and report both the average and how much it varied. `scikit-learn`'s `cross_val_score` does this, and MLflow can log every fold.",
        starter="""def cv_folds(num_examples, num_folds):
    # your code here
    pass
""",
        solution="""def cv_folds(num_examples, num_folds):
    folds = []
    for f in range(num_folds):
        folds.append([])
    for i in range(num_examples):
        folds[i % num_folds].append(i)
    return folds
""",
        cases=[
            case(7, 3, expected=[[0, 3, 6], [1, 4], [2, 5]], sample=True),
            case(0, 2, expected=[[], []]),
            case(4, 1, expected=[[0, 1, 2, 3]]),
            case(3, 5, expected=[[0], [1], [2], [], []]),
            case(6, 2, expected=[[0, 2, 4], [1, 3, 5]]),
        ],
        guided="""def cv_folds(num_examples, num_folds):
    # Replace every ___ with real code, then run the tests.

    # Step 1: make the folds, one empty list each.
    folds = []
    for f in range(num_folds):
        folds.append(___)
    # Step 2: deal example i into fold i % num_folds.
    for i in range(num_examples):
        folds[___].append(i)
    return folds
""",
        fills=['[]', 'i % num_folds'],
        concepts=[
            [
                'The remainder, %',
                "`7 % 3` is 1: what's left after taking out as many 3s as fit. As the left number counts up, the remainder goes 0, 1, 2, 0, 1, 2 and so on.",
                """7 % 3   # 1
6 % 3   # 0""",
            ],
            [
                'range',
                '`range(3)` gives 0, 1, 2: it starts at 0 and stops just before 3.',
                """for i in range(3):
    print(i)   # 0, then 1, then 2""",
            ],
            [
                'A list of lists',
                'Each item of the outer list is its own list. `groups[1]` is the second one.',
                """groups = [[], []]
groups[1].append(7)   # [[], [7]]""",
            ],
        ],
        byhand='7 examples, 3 folds. Example 0: 0 % 3 is 0, so fold 0. Example 1 goes to fold 1 and example 2 to fold 2. Example 3: 3 % 3 is 0, so back to fold 0. Then 4 goes to fold 1, 5 to fold 2 and 6 to fold 0. Return [[0, 3, 6], [1, 4], [2, 5]].',
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
        'A quick rule for a pass rate: the margin is about **plus or minus 100 divided by the square root of n**, in percentage points, where n is the number of examples. That is a 95% range: built this way, it holds the real rate about 95 times out of 100. It is at its widest when the rate is near 50%. So 100 examples give about plus or minus 10 points (the square root of 100 is 10), and 400 give about plus or minus 5. Halving the margin takes **four times** the examples.',
        "Use it backwards before you run anything: if the improvement you hope to see is smaller than the margin, your eval set can't show it. Add examples first, or compare on the same examples (later in this module), which is more sensitive.",
        'For scores near 0% or 100% (like 49 out of 50) this simple rule breaks down; statisticians use a **Wilson interval** there (two lessons from now). For metrics with no simple formula, use the **bootstrap**: rebuild the eval set 1,000 times by drawing examples at random with repeats allowed, score each, and keep the middle 95% of the scores.',
    ],
    example=example('Margin of error by eval set size', """examples   margin (about)
     25    plus or minus 20 points
    100    plus or minus 10 points
    400    plus or minus 5 points
   1600    plus or minus 2.5 points"""),
    check=question(
        'Your eval set has 100 questions. Prompt B scores 4 points higher than prompt A. Is that evidence B is better?',
        [
            'Yes, 4 points is a real gain',
            'Not on its own: with 100 examples each score is only good to about plus or minus 10 points',
            "No, evals can't compare prompts",
        ],
        answer=1,
        why='A 4-point gap is well inside the noise of a 100-example eval. Compare on the same examples, or use more of them.',
    ),
    angle=angle(
        pattern='Working a formula backwards',
        text='The margin is 100 divided by the square root of n. Flip it around: the square root of n is 100 divided by the margin, so n is that number multiplied by itself. Then round up, because you cannot use part of an example.',
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
        prompt="""`margin_points` is the margin of error you can accept, like `7`. That means your measured pass rate could be up to 7 points too high or too low (for example, 70% could really be anywhere from 63% to 77%).

The lesson's rule, worked backwards: divide 100 by `margin_points`, then multiply the result by itself. That is how many examples you need.

Return it as a whole number. If it has a decimal part, round up, because you cannot use part of an example. For example, 204.08 becomes 205.""",
        pattern='Work the rule backwards, then round up to a whole number.',
        target='a few arithmetic steps',
        realworld='Sizing an eval set before building it saves you from labelling 50 examples, running the comparison, and only then discovering the result is noise.',
        starter="""def examples_needed(margin_points):
    # your code here
    pass
""",
        solution="""def examples_needed(margin_points):
    ratio = 100 / margin_points
    exact = ratio * ratio
    needed = int(exact)
    if needed < exact:
        needed = needed + 1
    return needed
""",
        cases=[
            case(7, expected=205, sample=True),
            case(10, expected=100),
            case(5, expected=400),
            case(20, expected=25),
            case(3, expected=1112),
        ],
        guided="""def examples_needed(margin_points):
    # Replace every ___ with real code, then run the tests.

    # Step 1: divide 100 by the margin.
    ratio = ___
    # Step 2: multiply it by itself.
    exact = ratio * ratio
    # Step 3: round up. int() cuts off the decimal
    # part. If needed is now smaller than exact,
    # add 1.
    needed = int(exact)
    if ___:
        needed = needed + 1
    return needed
""",
        fills=['100 / margin_points', 'needed < exact'],
        concepts=[
            [
                'Rounding up',
                '`int()` throws away the part after the decimal point. If that made the number smaller, add 1.',
                """int(3.2)   # 3, so round up to 4
int(5.0)   # 5, already whole""",
            ],
        ],
        byhand='The margin is 7. 100 / 7 is about 14.2857. That multiplied by itself is about 204.08. int() cuts that to 204, which is smaller than 204.08, so add 1. Return 205.',
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
        'So keep a small **smoke set** for iterating. Make it **stratified**, meaning a few questions from every group, and add the whole **must-pass** set (the questions the app must never get wrong). Try ideas on it in minutes. Only the **finalists** go to the full **dev set** (the bigger set you compare finalists on), and only the final winner goes to the **holdout** (a set kept aside and used only once, at the end).',
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
        prompt="""Your function gets three things:

- `ids_by_group`: a dict. Each key is a group name, and its value is that group's question ids, already shuffled, like `{"billing": ["b3", "b1"]}`.
- `per_group`: how many ids to take from each group, like `1`.
- `must_pass`: ids that must always be included, like `["f2", "f9"]`.

Take the first `per_group` ids from every group. If a group has fewer, take all of them. Add every id in `must_pass`. Return all these ids as one list, sorted alphabetically, with no duplicates.""",
        pattern='Take the first few ids of each group, add the must-pass ids, and let a set remove duplicates.',
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
            case({'billing': ['b3', 'b1', 'b7'], 'fraud': ['f2', 'f9']}, 1, ['f2', 'f9'], expected=['b3', 'f2', 'f9'], sample=True),
            case({}, 3, [], expected=[]),
            case({'x': ['x1', 'x2']}, 5, ['x1'], expected=['x1', 'x2']),
            case({'a': ['a1', 'a2', 'a3'], 'b': ['b1']}, 2, ['z9'], expected=['a1', 'a2', 'b1', 'z9']),
        ],
        guided="""def smoke_set(ids_by_group, per_group, must_pass):
    # Replace every ___ with real code, then run the tests.

    # Step 1: start a set with the must-pass ids.
    # A set drops duplicates for you.
    chosen = set(must_pass)
    for ids in ids_by_group.values():
        # Step 2: add the first per_group ids.
        for qid in ___:
            chosen.add(qid)
    # Step 3: turn the set into a sorted list.
    return ___
""",
        fills=['ids[:per_group]', 'sorted(chosen)'],
        concepts=[
            [
                'A set removes duplicates',
                'A set holds each value once. Adding something it already has changes nothing.',
                """s = set(["a", "b"])
s.add("a")   # still {"a", "b"}""",
            ],
            [
                'Taking the first few with [:n]',
                '`items[:2]` gives the first 2 items. If there are fewer, you get all of them, with no error.',
                """["a", "b", "c"][:2]   # ["a", "b"]
["a"][:5]             # ["a"]""",
            ],
            [
                'dict.values()',
                'Gives each value of a dict, without the keys.',
                """prices = {"tea": 2, "cake": 4}
for p in prices.values():
    print(p)   # 2, then 4""",
            ],
            [
                'sorted',
                'Gives back a new list in order: alphabetical for text. It works on a set too.',
                """sorted({"pear", "apple"})
# ["apple", "pear"]""",
            ],
        ],
        byhand='Take 1 id from each group: b3 from billing and f2 from fraud. Add the must-pass ids: f2 is already in, so it is not added twice, and f9 is new. Sorted alphabetically, return ["b3", "f2", "f9"].',
        why='One pass over the groups, taking a few from each.',
        gotchas=[
            [
                'Keep it fixed',
                'Use the same smoke set for a whole round of ideas, so their numbers are comparable. Refresh it between rounds.',
            ],
            [
                'It leaks into your judgment',
                'You will look at the smoke set a lot. Keep it inside the dev set, never the holdout set you save for the final check.',
            ],
        ],
    ),
)

lesson(MODULE, 'wilson_interval',
    title='Margins near 0% and 100%',
    learn=[
        'The quick margin rule from "How many examples do you need?" (100 divided by the square root of n) breaks down when a pass rate is close to 0% or 100%. For 49 out of 50 it gives 98 plus or minus 14 (the square root of 50 is about 7): 84% to 112%, past 100%, which is impossible. For 0 out of 30 it gives 0 plus or minus 18: below 0%, also impossible.',
        'The **Wilson interval** is the standard fix for a pass rate. It always stays between 0% and 100%, and it stays honest with small samples and extreme rates.',
        'The formula is a few lines of arithmetic. The exercise gives it to you as Python, piece by piece. You do not need to remember it; you need to know to use it near the edges.',
        'This matters most for safety checks. "0 failures in 30 tries" does not mean the failure rate is 0%: the Wilson range goes up to about 11%.',
    ],
    example=example('Simple rule against Wilson', """49 of 50 passed (98%)
simple rule:   84% to 112%    ← past 100%: impossible
Wilson:      89.5% to 99.6%

0 of 30 got past the guardrail
simple rule:  -18% to 18%     ← below 0%: impossible
Wilson:         0% to 11.4%"""),
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
        pattern='Plugging into a formula',
        text='Work out the pass rate, then plug it into the formula one piece at a time, giving each piece a name. A fixed number of steps, whatever the numbers.',
        say='"For pass rates near 0 or 100% I use a Wilson interval, because the simple margin can go past 100% or below 0%."',
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
        prompt="""Your function gets two things:

- `passed`: how many examples passed, like `49`.
- `total`: how many examples there were, like `50`.

Work out the Wilson range with these lines of Python:

- `z = 1.96`, which gives a 95% range
- `n = total`
- `p = passed / n`
- `bottom = 1 + z * z / n`
- `centre = (p + z * z / (2 * n)) / bottom`
- `spread = p * (1 - p) / n + z * z / (4 * n * n)`
- `half = z * (spread ** 0.5) / bottom`

Return `[centre - half, centre + half]`, each rounded to 3 decimal places. These are fractions, so `0.895` means 89.5%.""",
        pattern='Follow the formula one piece at a time, then round.',
        target='a fixed number of steps',
        realworld='Reporting "98% (89.5% to 99.6%)" instead of "98%" tells a reviewer how much to trust the number, and stops anyone reading "0 failures" as "can never fail".',
        starter="""def wilson_interval(passed, total):
    # your code here
    pass
""",
        solution="""def wilson_interval(passed, total):
    z = 1.96
    n = total
    p = passed / n
    bottom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / bottom
    spread = p * (1 - p) / n + z * z / (4 * n * n)
    half = z * (spread ** 0.5) / bottom
    low = round(centre - half, 3)
    high = round(centre + half, 3)
    return [low, high]
""",
        cases=[
            case(49, 50, expected=[0.895, 0.996], sample=True),
            case(0, 30, expected=[0.0, 0.114]),
            case(8, 10, expected=[0.49, 0.943]),
            case(50, 100, expected=[0.404, 0.596]),
            case(30, 30, expected=[0.886, 1.0]),
        ],
        guided="""def wilson_interval(passed, total):
    # Replace every ___ with real code, then run the tests.
    z = 1.96
    n = total
    # Step 1: the pass rate.
    p = ___
    # Step 2: the formula from the task, in pieces.
    bottom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / bottom
    spread = p * (1 - p) / n + z * z / (4 * n * n)
    half = z * (spread ** 0.5) / bottom
    # Step 3: the range goes from centre minus half
    # to centre plus half, each rounded to 3 places.
    low = round(centre - half, 3)
    high = ___
    return [low, high]
""",
        fills=['passed / n', 'round(centre + half, 3)'],
        concepts=[
            [
                'Square root with ** 0.5',
                'Raising a number to the power 0.5 gives its square root, with no import needed.',
                """16 ** 0.5   # 4.0""",
            ],
            [
                'round',
                '`round(x, 3)` keeps 3 digits after the decimal point.',
                """round(0.12345, 3)   # 0.123""",
            ],
        ],
        byhand='Take the lines of the task one at a time. p is 49 out of 50, which is 0.98. bottom comes out at about 1.0768. centre comes out at about 0.94575. spread comes out at about 0.000776. Its square root is about 0.02786, so half comes out at about 0.05071. low is centre minus half, about 0.89504. high is centre plus half, about 0.99646. Rounded to 3 places, return [0.895, 0.996].',
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
        "This rule is deliberately cautious: it rarely crowns a fake winner (about 1 time in 10 with 3 runs each, far less with 5), but it can miss a real one, because overlapping ranges don't prove there is no difference. When both setups ran on the same examples, a **paired comparison** is the standard check, and it is more sensitive. That is the next lesson.",
    ],
    example=example('Three runs each: compare the ranges', """     run 1   run 2   run 3    range
A    0.78    0.80    0.79     0.78 to 0.80
B    0.83    0.85    0.84     0.83 to 0.85
B's lowest (0.83) beats A's highest (0.80)  → B wins

C    0.79    0.86    0.82     0.79 to 0.86
D    0.84    0.81    0.85     0.81 to 0.85
the ranges overlap                          → no clear winner"""),
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
        prompt="""You ran two setups, A and B, several times each, because LLM outputs and judges vary from run to run. Your function gets two things:

- `a_scores`: A's quality score from each run, like `[0.78, 0.8, 0.79]`.
- `b_scores`: B's quality score from each run, like `[0.83, 0.85, 0.84]`.

Return `"a"` if A's lowest score is higher than B's highest score. Return `"b"` if B's lowest score is higher than A's highest score. Otherwise the scores overlap, so return `"tie"`.""",
        pattern="Compare ranges, not single numbers: the lowest of one against the highest of the other.",
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

    # Step 1: A wins if its lowest score is
    # higher than B's highest.
    if ___ > max(b_scores):
        return "a"
    # Step 2: B wins if its lowest score is
    # higher than A's highest.
    if ___:
        return "b"
    # Step 3: otherwise they overlap.
    return "tie"
""",
        fills=['min(a_scores)', 'min(b_scores) > max(a_scores)'],
        concepts=[
            [
                'min and max',
                'The smallest and largest item of a list.',
                """min([4, 9, 2])   # 2
max([4, 9, 2])   # 9""",
            ],
        ],
        byhand='A\'s scores go from 0.78 to 0.80. B\'s go from 0.83 to 0.85. Is A\'s lowest, 0.78, higher than B\'s highest, 0.85? No. Is B\'s lowest, 0.83, higher than A\'s highest, 0.80? Yes, so return "b".',
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
        "The standard check for pass/fail results is **McNemar's test**. In plain words: call a winner only if the gap between the two counts is at least **twice the square root of the number of disagreements**. With 20 disagreements that is about 8.9 (the square root of 20 is about 4.5), so winning 15 to 5 is enough and 12 to 8 is too close to call.",
        'This replaces the "ranges must not overlap" rule from the previous lesson whenever both setups ran on the same examples. For scores that are not pass/fail, the paired versions are a **paired bootstrap** or a **permutation test** (on each example, randomly swap the A and B scores, do that many times, and see how often luck alone makes a gap that big).',
    ],
    example=example('Only disagreements count', """example   A   B
q1        ✓   ✓    agree: ignore
q2        ✓   ✗    A only
q3        ✗   ✓    B only
q4        ✗   ✗    agree: ignore
...
20 disagreements: the gap must be at least 8.9
(twice the square root of 20)
A only 15, B only 5:  gap 10, enough     → A wins
A only 12, B only 8:  gap 4, below 8.9   → too close"""),
    check=question(
        'Out of 200 questions, A and B disagree on 20. A wins 12 of those and B wins 8. What do you conclude?',
        [
            'A is better: it won more',
            'Too close to call: the gap of 4 is below twice the square root of 20, about 8.9',
            'B is better',
        ],
        answer=1,
        why='The 180 agreements say nothing about which is better. Of the 20 that do, a 12 to 8 split is easily luck.',
    ),
    angle=angle(
        pattern='Walking two lists in step',
        text='`zip` walks both lists together, one example at a time, so you count the disagreements in a single pass. Checking `gap * gap` against `4 * (a_only + b_only)` gives the same answer without taking a square root at all.',
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
        prompt="""Two setups, A and B, ran on the same examples. Your function gets two things:

- `a_passed`: one number per example: `1` if A passed it, `0` if not, like `[1, 0, 1]`.
- `b_passed`: the same for B, in the same order, like `[1, 1, 0]`.

Count `a_only`, the examples only A passed, and `b_only`, the examples only B passed. Examples that both passed or both failed don't count. Then `gap = a_only - b_only`.

Return `"a"` if `gap` is above 0 and `gap * gap` is at least `4 * (a_only + b_only)`. Return `"b"` if `gap` is below 0 and the same check holds. Otherwise return `"tie"`. This is the lesson's rule, written without a square root.""",
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
        if a == 1 and b == 0:
            a_only += 1
        elif a == 0 and b == 1:
            b_only += 1
    gap = a_only - b_only
    big_enough = gap * gap >= 4 * (a_only + b_only)
    if big_enough and gap > 0:
        return "a"
    if big_enough and gap < 0:
        return "b"
    return "tie"
""",
        cases=[
            case([1, 1, 1, 1, 1, 1, 1, 0], [1, 0, 0, 0, 0, 0, 0, 0], expected='a', sample=True),
            case([1] * 4 + [1] * 15 + [0] * 5 + [0] * 2,
                 [1] * 4 + [0] * 15 + [1] * 5 + [0] * 2, expected='a'),
            case([1] * 12 + [0] * 8 + [1] * 30,
                 [0] * 12 + [1] * 8 + [1] * 30, expected='tie'),
            case([1, 0, 1], [1, 0, 1], expected='tie'),
            case([0] * 6 + [1] * 10, [1] * 6 + [1] * 10, expected='b'),
            case([1, 1, 1, 0], [0, 0, 0, 0], expected='tie'),
            case([], [], expected='tie'),
        ],
        guided="""def paired_verdict(a_passed, b_passed):
    # Replace every ___ with real code, then run the tests.
    a_only = 0
    b_only = 0

    # Step 1: walk both lists together, and count
    # only the examples where they disagree.
    for a, b in zip(a_passed, b_passed):
        if a == 1 and b == 0:
            a_only += 1
        elif ___:
            b_only += 1

    # Step 2: is the gap big enough to beat luck?
    gap = a_only - b_only
    big_enough = ___ >= 4 * (a_only + b_only)

    # Step 3: if so, the side the gap points to wins.
    if big_enough and gap > 0:
        return "a"
    if big_enough and gap < 0:
        return "b"
    return "tie"
""",
        fills=['a == 0 and b == 1', 'gap * gap'],
        concepts=[
            [
                'zip',
                'Walks two lists side by side, giving you one item from each at a time.',
                """names = ["ann", "bo"]
ages = [30, 25]
for name, age in zip(names, ages):
    print(name, age)
# ann 30, then bo 25""",
            ],
            [
                'elif',
                '`elif` means "else, if": it is checked only when the `if` above it was False.',
                """if n > 0:
    print("positive")
elif n < 0:
    print("negative")""",
            ],
            [
                'Counting with +=',
                '`count += 1` is short for `count = count + 1`.',
                """count = 0
count += 1   # count is now 1""",
            ],
            [
                'Saving a True or False answer',
                'A comparison gives True or False, and you can keep it in a variable to use later.',
                """age = 20
adult = age >= 18   # True
if adult and age < 65:
    print("working age")""",
            ],
        ],
        byhand='Example 1: both passed, so skip it. Examples 2 to 7: A passed and B failed, so a_only is 6. Example 8: both failed, so skip it. b_only is 0. gap is 6 minus 0, which is 6, and 6 times 6 is 36. 4 times 6 disagreements is 24. 36 is at least 24 and gap is above 0, so return "a".',
        why='One step per example, walking both lists together.',
        gotchas=[
            [
                'Small samples cannot decide',
                'Three disagreements all going A\'s way still is not enough: 3 times 3 is 9, less than 4 times 3, which is 12. With few disagreements, the honest answer is "tie".',
            ],
            [
                'Same examples, same order',
                'Pairing only works if position i is the same example for both setups. Line them up by example id first.',
            ],
            [
                'Why 2?',
                "It is a rounded version of 1.96, the number behind a 95% range. That rounding makes the rule slightly stricter than the quick version of McNemar's test. With fewer than about 25 disagreements, use the exact version, which is stricter: this rule calls 5 to 0 a win, but the exact test calls it too close.",
            ],
        ],
    ),
)

lesson(MODULE, 'biggest_gap',
    title='Oracle tests: find the bottleneck',
    learn=[
        'A RAG app (one that first looks up documents, the **retrieval** step, then answers from them) or an agent (a model that calls tools to get a job done) is a chain of steps, and a bad answer could come from any of them. An **oracle test** replaces one step with a perfect version and reruns the eval: hand the model the right documents instead of what retrieval found, or give the agent correct tool results.',
        "The gap between the oracle run and your current system is that step's **headroom**: the most you could gain by perfecting it. If perfect documents only lift you from 78% to 80%, retrieval isn't your problem, and tuning it is wasted effort. If they lift you to 91%, it is.",
        'Plan oracle runs in the **Design** stage, as extra variants alongside the ones you are testing, and read them first in **Evaluate**. They need the right answers for each step in the eval set, like the correct document ids for each question.',
    ],
    example=example('Headroom per step', """current system                         78%
oracle retrieval (right docs given)    91%   → retrieval headroom: 13 points
oracle reranking (right doc first)     84%   → reranking headroom:  6 points
oracle prompt (expert-written)         80%   → prompt headroom:     2 points
→ work on retrieval first
(reranking: reordering the found documents so the best come first)"""),
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
        prompt="""Your function gets two things:

- `current`: your system's pass rate now, like `0.78`.
- `oracles`: a dict. Each key is a step, and its value is the pass rate when that step is made perfect, like `{"retrieval": 0.91, "prompt": 0.8}`.

A step's headroom is its oracle pass rate minus `current`. Return the name of the step with the most headroom. If no step's oracle pass rate is higher than `current`, return `None`.""",
        pattern="Best so far over a dict: work out each step's headroom and keep the biggest.",
        target='one pass over the steps',
        realworld='Oracle tests stop teams from spending a month on the step that was already nearly perfect.',
        starter="""def biggest_gap(current, oracles):
    # your code here
    pass
""",
        solution="""def biggest_gap(current, oracles):
    best_step = None
    best_gain = 0
    for step in oracles:
        gain = oracles[step] - current
        if gain > best_gain:
            best_step = step
            best_gain = gain
    return best_step
""",
        cases=[
            case(0.78, {'retrieval': 0.91, 'reranking': 0.84, 'prompt': 0.8}, expected='retrieval', sample=True),
            case(0.7, {'retrieval': 0.72, 'generation': 0.9}, expected='generation'),
            case(0.9, {'retrieval': 0.88}, expected=None),
            case(0.5, {'memory': 0.55, 'tools': 0.65}, expected='tools'),
            case(0.8, {}, expected=None),
        ],
        guided="""def biggest_gap(current, oracles):
    # Replace every ___ with real code, then run the tests.
    best_step = None   # no step kept yet
    best_gain = 0      # a step must beat 0 to count
    for step in oracles:
        # Step 1: this step's headroom: its oracle
        # pass rate minus current.
        gain = ___
        # Step 2: keep it if it beats the best so far.
        if ___:
            best_step = step
            best_gain = gain
    return best_step
""",
        fills=['oracles[step] - current', 'gain > best_gain'],
        concepts=[
            [
                'Looping over a dict',
                '`for key in d` gives each key in turn. `d[key]` gets the value that goes with it.',
                """prices = {"tea": 2, "cake": 4}
for item in prices:
    print(item, prices[item])
# prints tea 2, then cake 4""",
            ],
        ],
        byhand='current is 0.78. retrieval: 0.91 - 0.78 = 0.13. That is more than 0, so retrieval is the best so far. reranking: 0.84 - 0.78 = 0.06, smaller than 0.13. prompt: 0.8 - 0.78 = 0.02, smaller too. Return "retrieval".',
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
        'A pipeline collects parts over time: query rewriting (rephrasing the user\'s question before searching), a reranker (a model that reorders the search results so the best ones come first), memory (what the app remembers from earlier in the chat), an extra node (one step in a LangGraph graph). Some earn their cost; some do nothing. An **ablation** removes one part at a time, keeping everything else, and reruns the eval.',
        "The drop when a part is removed is that part's **contribution**. A part whose removal changes nothing measurable is a candidate to delete: less to run, pay for and debug.",
        'Plan ablations in the **Design** stage as extra variants of your best version, and read them in **Evaluate**. Each ablation reruns the same questions, so judge each drop with the paired check from "Comparing on the same examples": count only the questions where the two versions disagree. A 1-point drop on 100 questions is a 1-question gap, which never passes.',
    ],
    example=example('Removing one part at a time (100 questions)', """full pipeline (rewrite + rerank + memory)   86%
without query rewrite                      85%   → contributes  1 point (within noise)
without reranker                           79%   → contributes  7 points
without memory                             86%   → contributes  0 points

paired check for the reranker:
  only the full pipeline passed    8 questions
  only the version without it      1 question
  gap 7: 7 times 7 is 49, at least 4 times 9 (36)   → real
→ keep the reranker; the rewrite and memory are candidates to remove"""),
    check=question(
        'Removing query rewriting changes the score from 86% to 85% on 100 questions. What do you conclude?',
        [
            'Rewriting adds 1 point, so keep it',
            "Its effect is within the noise: it may not be worth its cost, so test it with more examples or drop it",
            'Rewriting hurts quality',
        ],
        answer=1,
        why='86% to 85% on 100 questions is a 1-question gap, far too small to pass the paired check (even 1 to 0 fails it). It says nothing either way.',
    ),
    angle=angle(
        pattern='Measure the drop, then sort',
        text='The big idea: to find out what one part of your app is worth, take it out and see how much the score drops. Your code works out that drop for each part: the full score minus the score without it. Then it sorts the parts so the biggest drop comes first. The part you would miss most is at the top, and a part whose drop is 0 is one you could delete: less to run, pay for and fix.',
        say='"I take out one part at a time and rerun the eval. The bigger the drop, the more that part is worth; a part with no drop can go."',
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
        prompt="""Your function gets two things:

- `full`: the pass rate of the whole pipeline, in percent, like `86`.
- `without`: a dict. Each key is a part, and its value is the pass rate in percent with that part removed, like `{"rerank": 79, "memory": 86}`.

A part is worth how far the score drops without it: `full - without[part]`. Return a list of `[part, drop]`, one for each part, biggest drop first. If the score goes up without a part, its drop is negative, like `-4`, and it comes last.""",
        pattern='Work out the drop for each part, then sort, biggest first.',
        target='one pass, then a sort',
        realworld='Pipelines grow parts that nobody dares remove. Ablations give you the evidence to simplify, which saves cost and makes debugging easier.',
        starter="""def ablation_report(full, without):
    # your code here
    pass
""",
        solution="""def ablation_report(full, without):
    rows = []
    for part in without:
        drop = full - without[part]
        rows.append([part, drop])
    rows.sort(key=lambda row: row[1], reverse=True)
    return rows
""",
        cases=[
            case(86, {'rewrite': 85, 'rerank': 79, 'memory': 86}, expected=[['rerank', 7], ['rewrite', 1], ['memory', 0]], sample=True),
            case(90, {}, expected=[]),
            case(80, {'rewrite': 75, 'rerank': 70}, expected=[['rerank', 10], ['rewrite', 5]]),
            case(70, {'cache': 74}, expected=[['cache', -4]]),
            case(80, {'cache': 82, 'rerank': 72}, expected=[['rerank', 8], ['cache', -2]]),
        ],
        guided="""def ablation_report(full, without):
    # Replace every ___ with real code, then run the tests.
    rows = []
    for part in without:
        # Step 1: how much the score drops without
        # this part.
        drop = ___
        rows.append([part, drop])
    # Step 2: sort by the drop, row[1], the
    # second item of each row.
    # reverse=True puts the biggest first.
    rows.sort(key=lambda row: ___, reverse=True)
    return rows
""",
        fills=['full - without[part]', 'row[1]'],
        concepts=[
            [
                'Looping over a dict',
                '`for key in d` gives each key in turn. `d[key]` gets the value that goes with it.',
                """prices = {"tea": 2, "cake": 4}
for item in prices:
    print(item, prices[item])
# prints tea 2, then cake 4""",
            ],
            [
                'Sorting by one item of each row',
                '`lambda row: row[1]` is a tiny function: give it a row and it gives back `row[1]`, the second item. `key=` sorts by that. `reverse=True` puts the biggest first.',
                """pets = [["cat", 3], ["dog", 9]]
pets.sort(key=lambda p: p[1], reverse=True)
# [["dog", 9], ["cat", 3]]""",
            ],
        ],
        byhand='full is 86. rewrite: 86 - 85 = 1. rerank: 86 - 79 = 7. memory: 86 - 86 = 0. Biggest first: rerank 7, rewrite 1, memory 0. Return [["rerank", 7], ["rewrite", 1], ["memory", 0]].',
        why='One subtraction per part, then a sort.',
        gotchas=[
            [
                'A negative contribution',
                'If removing a part *raises* the score, that part is actively hurting. It will show up last, with a negative drop.',
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
        "Two guards. In **Design**, limit how many variants you test, and for a strict check divide the 5% by the number of comparisons (the **Bonferroni** correction). In **Evaluate**, confirm the winner **once** on the holdout set, the examples kept aside that it has never seen. That confirmation is the reason the holdout set exists.",
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
        text='Start at 1 and multiply by 0.95 once per comparison: that is the chance that none of them is a fluke. One minus that is the chance of at least one.',
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
        prompt="""`num_variants` is how many variants you try, like `20`. A variant is one version of your app, such as a different prompt. Each variant is compared once against your current version.

Each comparison has a 5% chance of a fluke: a winner picked by luck. So one comparison is clean 95% of the time, written in Python as `0.95`. To get the chance that all of them are clean, start at `1` and multiply by `0.95` once for each variant. For 2 variants that is `0.95 * 0.95`, about 0.90.

Return the chance of at least one fluke: 1 minus the chance that all are clean, rounded to 2 decimal places (as a decimal, like `0.64`).""",
        pattern='Multiply the chance of a clean result once per variant, then take it away from 1.',
        target='one step per variant',
        realworld='Prompt and hyperparameter searches routinely try dozens of variants. Knowing the fluke rate is why serious teams hold out a final test set.',
        starter="""def fluke_risk(num_variants):
    # your code here
    pass
""",
        solution="""def fluke_risk(num_variants):
    all_clean = 1.0
    for i in range(num_variants):
        all_clean = all_clean * 0.95
    chance = 1 - all_clean
    return round(chance, 2)
""",
        cases=[
            case(20, expected=0.64, sample=True),
            case(1, expected=0.05),
            case(3, expected=0.14),
            case(5, expected=0.23),
            case(10, expected=0.4),
        ],
        guided="""def fluke_risk(num_variants):
    # Replace every ___ with real code, then run the tests.

    # Step 1: the chance that all are clean. Start
    # at 1 and multiply by 0.95 once per variant.
    all_clean = 1.0
    for i in range(num_variants):
        all_clean = ___
    # Step 2: at least one fluke is 1 minus that.
    chance = ___
    return round(chance, 2)
""",
        fills=['all_clean * 0.95', '1 - all_clean'],
        concepts=[
            [
                'Repeating with range',
                '`for i in range(3):` runs the loop body 3 times.',
                """total = 1
for i in range(3):
    total = total * 2
# total ends at 8""",
            ],
            [
                'round',
                '`round(x, 2)` keeps 2 digits after the decimal point.',
                """round(0.6789, 2)   # 0.68""",
            ],
        ],
        byhand='20 variants. Start at 1.0 and multiply by 0.95 twenty times. That leaves about 0.3585, the chance that all 20 are clean. The chance of at least one fluke is 1 - 0.3585 = 0.6415. Rounded to 2 places, return 0.64.',
        why='One multiplication per variant.',
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
