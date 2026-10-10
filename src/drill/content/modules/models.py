"""Choosing a model: Quality, cost and latency, and which option pays for itself."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('models', 'Choosing a model', 'Quality, cost and latency, and which option pays for itself.')

lesson(MODULE, 'percentile',
    title='Latency that users feel',
    learn=[
        'Averages hide slow requests. **p95** is the time 95 out of 100 requests beat; p99 is for 99 out of 100.',
        "Measure the whole request (retrieval, tools, model calls), which is what a trace's total duration gives you, and compare models and configs on p95.",
    ],
    example=example('Finding slow traces in MLflow', """slow = mlflow.search_traces(
    filter_string="attributes.execution_time_ms > 5000",
    max_results=100,
)"""),
    check=question(
        "A model's average latency is 900 ms and its p95 is 4 seconds. What do users experience?",
        ['Everything feels fast', 'About 1 in 20 requests is slow enough to notice', "It's always 900 ms"],
        answer=1,
        why='p95 at 4 seconds means 5 out of 100 requests take 4 seconds or more.',
    ),
    angle=angle(
        pattern='Sort, then pick by position',
        text='Sort once (the slowest part), then index. The common bug is mixing up counting from 1 and indexing from 0.',
        say='"I sort, compute the rank by rounding up, and subtract one to get the index."',
        classic=None,
    ),
    stack=stack('MLflow: find slow traces', """slow = mlflow.search_traces(
    filter_string="attributes.execution_time_ms > 5000", max_results=100,
)"""),
    exercise=exercise(
        title='The Latency Users Feel',
        topic='models',
        difficulty='easy',
        fn='percentile',
        prompt="""The average response time hides the slow requests users complain about, so teams track a **percentile**: p95 is the time that 95 out of 100 requests beat.

Given a list of `latencies` in milliseconds and `pct` (like 95), sort them and return the item at position `pct` percent of the way through, rounding the position up, counting from 1. In code: position = `(pct * n + 99) // 100`, and the answer is the item at index position − 1. An empty list gives `None`.""",
        pattern='Sort, then pick by position.',
        target='sort once',
        realworld='A model with a 900 ms average can still have a 4-second p95, which is what users notice. Compare models and configs on p95 latency, not the average.',
        starter="""def percentile(latencies, pct):
    # your code here
    pass
""",
        solution="""def percentile(latencies, pct):
    if not latencies:
        return None
    ordered = sorted(latencies)
    position = (pct * len(ordered) + 99) // 100
    return ordered[max(position, 1) - 1]
""",
        cases=[
            case([820, 640, 4100, 700, 910, 760, 690, 3900, 720, 800], 90, expected=3900, sample=True),
            case([], 95, expected=None),
            case([500], 99, expected=500),
            case([5, 1, 3, 2, 4], 50, expected=3),
            case([10, 20, 30, 40], 100, expected=40),
            case([7, 8, 9], 1, expected=7),
        ],
        guided="""def percentile(latencies, pct):
    # Replace every ___ with real code, then run the tests.

    if not latencies:
        return None
    # Step 1: sorted() gives a new list, smallest first.
    ordered = ___
    # Step 2: the position, rounded up, counting from 1.
    position = (pct * len(ordered) + 99) // 100
    # Step 3: positions count from 1 but indexes from 0.
    return ordered[___]
""",
        fills=['sorted(latencies)', 'max(position, 1) - 1'],
        concepts=[
            [
                'sorted',
                'Returns a new sorted list and leaves the original alone.',
                'sorted([3, 1, 2])   # [1, 2, 3]',
            ],
            [
                'Rounding up with //',
                '`(a + 99) // 100` divides by 100 and rounds up, without decimals.',
                '(901 + 99) // 100   # 10',
            ],
        ],
        byhand='Ten latencies, p90. Sorted: 640, 690, 700, 720, 760, 800, 820, 910, 3900, 4100. 90% of 10 is position 9: 3900 ms. The average is about 1,400 ms, which hides two very slow requests.',
        why='Sorting is the slowest part.',
        gotchas=[
            [
                'Average lies about latency',
                'One 30-second timeout and 99 fast requests average 400 ms. The p99 tells you about the timeout.',
            ],
            [
                'Measure where the user is',
                "Latency measured inside the model call misses retrieval, tools and network. Use the whole trace's duration.",
            ],
        ],
    ),
)

lesson(MODULE, 'pareto_models',
    title='Comparing LLMs for a task',
    learn=[
        'To choose a model for a task, run each candidate on the **same eval set**, with the **same judge**, and record **quality, cost and p95 latency** as one MLflow run per model.',
        "Throw out any model that loses on all three to another. What's left is a short list of real trade-offs, decided by what quality is worth to you.",
    ],
    example=example('One run per model, same eval set', """from mlflow.genai.scorers import Correctness

for model in ["fast-model", "smart-model"]:
    with mlflow.start_run(run_name=model):
        mlflow.log_param("model", model)
        mlflow.genai.evaluate(data=eval_set, predict_fn=make_app(model), scorers=[Correctness()])
        mlflow.log_metrics({"cost_per_1k": cost[model], "p95_ms": p95[model]})"""),
    check=question(
        'Model C is more expensive, slower and less accurate than model A on your eval set. Should C stay on the shortlist?',
        ['Yes, for variety', 'No: A beats it on everything', "Only if it's newer"],
        answer=1,
        why='A model beaten on every measure is never the right choice.',
    ),
    angle=angle(
        pattern='Pairwise domination',
        text='Compare every pair and keep the models nothing beats. Fine for a handful of models.',
        say='"A model is out if another is at least as good on quality, cost and latency and strictly better on one; what\'s left is the Pareto front."',
        classic=None,
    ),
    stack=stack('MLflow: one run per candidate endpoint', """for endpoint in candidates:   # Foundation Model API endpoints in your workspace
    with mlflow.start_run(run_name=endpoint):
        mlflow.log_param("endpoint", endpoint)
        mlflow.genai.evaluate(data=eval_set, predict_fn=make_app(endpoint), scorers=[Correctness()])"""),
    exercise=exercise(
        title='Compare Models Fairly',
        topic='models',
        difficulty='medium',
        fn='pareto_models',
        prompt="""You evaluated several models on the same task. Each row of `models` is `{"name": "fast-model", "quality": 0.78, "cost": 0.4, "p95_ms": 900}`. Higher quality is better; lower cost and latency are better.

A model is **beaten** if some other model is at least as good on all three and strictly better on at least one. Return the names of the models that are not beaten, in their original order. These are the only ones worth choosing between.""",
        pattern='Compare every pair: a candidate survives only if nothing dominates it.',
        target='compare every pair (there are only a handful of models)',
        realworld='There is rarely one best model. A small model can be the right choice for a high-volume, simple task, and a large one for rare, hard questions. Throwing out models that lose on every measure leaves a short list to decide between on value.',
        starter="""def pareto_models(models):
    # your code here
    pass
""",
        solution="""def beats(a, b):
    no_worse = a["quality"] >= b["quality"] and a["cost"] <= b["cost"] and a["p95_ms"] <= b["p95_ms"]
    better = a["quality"] > b["quality"] or a["cost"] < b["cost"] or a["p95_ms"] < b["p95_ms"]
    return no_worse and better

def pareto_models(models):
    out = []
    for m in models:
        if not any(beats(other, m) for other in models):
            out.append(m["name"])
    return out
""",
        cases=[
            case([
                {'name': 'fast-model', 'quality': 0.78, 'cost': 0.4, 'p95_ms': 900},
                {'name': 'smart-model', 'quality': 0.88, 'cost': 3.0, 'p95_ms': 2400},
                {'name': 'old-model', 'quality': 0.75, 'cost': 1.2, 'p95_ms': 1500},
            ], expected=['fast-model', 'smart-model'], sample=True),
            case([], expected=[]),
            case([
                {'name': 'a', 'quality': 0.8, 'cost': 1, 'p95_ms': 100},
                {'name': 'b', 'quality': 0.8, 'cost': 1, 'p95_ms': 100},
            ], expected=['a', 'b']),
            case([
                {'name': 'a', 'quality': 0.9, 'cost': 1, 'p95_ms': 100},
                {'name': 'b', 'quality': 0.8, 'cost': 1, 'p95_ms': 100},
            ], expected=['a']),
            case([
                {'name': 'cheap', 'quality': 0.7, 'cost': 0.1, 'p95_ms': 500},
                {'name': 'quick', 'quality': 0.7, 'cost': 0.5, 'p95_ms': 200},
                {'name': 'good', 'quality': 0.9, 'cost': 2, 'p95_ms': 900},
            ], expected=['cheap', 'quick', 'good']),
        ],
        guided="""def beats(a, b):
    # a beats b: no worse on every measure, and better on at least one.
    no_worse = a["quality"] >= b["quality"] and a["cost"] <= b["cost"] and a["p95_ms"] <= b["p95_ms"]
    better = ___
    return no_worse and better


def pareto_models(models):
    # Replace every ___ with real code, then run the tests.
    out = []
    for m in models:
        # Keep m only if no other model beats it.
        # any(...) is True if at least one item is True.
        if not any(___ for other in models):
            out.append(m["name"])
    return out
""",
        fills=[
            'a["quality"] > b["quality"] or a["cost"] < b["cost"] or a["p95_ms"] < b["p95_ms"]',
            'beats(other, m)',
        ],
        concepts=[
            ['any', 'True if at least one item is true.', 'any(x > 5 for x in [1, 7, 3])   # True'],
            [
                'A helper function',
                'Pulling a rule into its own small function makes the main loop easy to read.',
                """def beats(a, b):
    ...""",
            ],
        ],
        byhand="old-model costs more, is slower and scores lower than fast-model, so it's beaten. fast-model and smart-model each win on something (cheap and quick vs better), so both stay.",
        why='Every model is compared with every other, which is fine for a handful of models.',
        gotchas=[
            [
                'Same eval set, same judge, same prompt',
                'Model comparisons are only fair when everything else is held fixed. Prompts tuned for one model often underperform on another, so test each with a reasonable prompt.',
            ],
            [
                'Quality on your task, not a leaderboard',
                'Public benchmarks rarely match your data. Thirty real examples from your own task tell you more.',
            ],
        ],
    ),
)

lesson(MODULE, 'better_option',
    title='Return on investment',
    learn=[
        'Every experiment ends with a decision, and the decision is about value: what does a success earn or save, and what does each call cost?',
        'Net monthly value = volume × success rate × value per success − volume × cost per call. A cheaper model can lose money if it succeeds less often, and an expensive one can pay for itself many times over.',
    ],
    example=example('Log the business number with the run', """with mlflow.start_run(run_name="decision-oct"):
    mlflow.log_params({"volume": 10_000, "value_per_success": 4.0})
    mlflow.log_metric("net_monthly_value", 35_700)
    mlflow.set_tag("decision", "ship smart-model")"""),
    check=question(
        'A model costs 10× more per call but resolves 25% more tickets, each worth $4. Calls cost $0.002 vs $0.02. Is it worth it?',
        [
            "No, it's 10× more expensive",
            'Very likely: the extra resolutions are worth far more than the extra cents',
            "Can't tell",
        ],
        answer=1,
        why='25 extra resolutions per 100 calls is $100; the extra cost is $1.80.',
    ),
    angle=angle(
        pattern='Score and keep the best',
        text='Apply one formula to every option and keep the best so far. The skill is choosing the formula with the business.',
        say='"I compute net value per option with the same formula, then take the maximum; the inputs come from evals and from the team that owns the outcome."',
        classic=None,
    ),
    stack=stack('MLflow: log the decision with its numbers', """with mlflow.start_run(run_name="decision-oct"):
    mlflow.log_params({"volume": 10_000, "value_per_success": 4.0})
    mlflow.log_metric("net_monthly_value", 35_700)
    mlflow.set_tag("decision", "ship smart-model")"""),
    exercise=exercise(
        title='Return on Investment',
        topic='models',
        difficulty='easy',
        fn='better_option',
        prompt="""Each option in `options` is `{"name": "smart-model", "success_rate": 0.9, "cost_per_call": 0.03}`. Each month there are `volume` requests, and each successful answer is worth `value_per_success` dollars (for example, a support ticket that doesn't reach a human).

An option's net monthly value is `volume * success_rate * value_per_success - volume * cost_per_call`. Return `[name, net]` for the option with the highest net value, with net rounded to 2 places. If two tie, the first listed wins. There is at least one option.""",
        pattern='Score every option with the same formula, keep the best so far.',
        target='one walk through the options',
        realworld='This is the ROI question behind every experiment. A cheaper model that answers fewer questions can lose money, and an expensive one can pay for itself. Value per success is a business number: get it from the team that owns the outcome.',
        starter="""def better_option(options, volume, value_per_success):
    # your code here
    pass
""",
        solution="""def better_option(options, volume, value_per_success):
    best = None
    for o in options:
        net = volume * o["success_rate"] * value_per_success - volume * o["cost_per_call"]
        if best is None or net > best[1]:
            best = [o["name"], net]
    return [best[0], round(best[1], 2)]
""",
        cases=[
            case([
                {'name': 'fast-model', 'success_rate': 0.72, 'cost_per_call': 0.002},
                {'name': 'smart-model', 'success_rate': 0.9, 'cost_per_call': 0.03},
            ], 10000, 4.0, expected=['smart-model', 35700.0], sample=True),
            case([{'name': 'only', 'success_rate': 0.5, 'cost_per_call': 0.01}], 100, 1.0, expected=['only', 49.0]),
            case([
                {'name': 'a', 'success_rate': 0.8, 'cost_per_call': 0.01},
                {'name': 'b', 'success_rate': 0.81, 'cost_per_call': 0.5},
            ], 1000, 1.0, expected=['a', 790.0]),
            case([
                {'name': 'x', 'success_rate': 0.6, 'cost_per_call': 0.1},
                {'name': 'y', 'success_rate': 0.6, 'cost_per_call': 0.1},
            ], 10, 2.0, expected=['x', 11.0]),
        ],
        guided="""def better_option(options, volume, value_per_success):
    # Replace every ___ with real code, then run the tests.

    best = None   # [name, net] of the best so far
    for o in options:
        # Step 1: value earned minus money spent, per month.
        net = volume * o["success_rate"] * value_per_success - ___
        # Step 2: strictly better replaces it, so the first wins a tie.
        if best is None or ___:
            best = [o["name"], net]
    return [best[0], round(best[1], 2)]
""",
        fills=['volume * o["cost_per_call"]', 'net > best[1]'],
        concepts=[
            [
                'Keeping a pair',
                'A two-item list can hold the best name and its score together.',
                """best = ['fast-model', 28780.0]
best[1]   # the score""",
            ],
        ],
        byhand='fast-model: 10,000 × 0.72 × $4 = $28,800 earned, minus 10,000 × $0.002 = $20 spent: $28,780. smart-model: 10,000 × 0.9 × $4 = $36,000, minus $300: $35,700. The expensive model is worth $6,920 more a month.',
        why='One walk through the options.',
        gotchas=[
            [
                'Count every cost',
                'Per-call model cost is only part of it: retrieval, retries, agent steps, evaluation runs and human review all count. Traces with token counts make this possible.',
            ],
            [
                'Success must be measured, not assumed',
                "The success rate comes from your evals and from production feedback. If it's a guess, the ROI is a guess.",
            ],
        ],
    ),
)
