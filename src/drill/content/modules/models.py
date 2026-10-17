"""Choosing a model: Quality, cost and latency, and which option pays for itself."""

from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, module, practice, question, source, stack

MODULE = module('models', 'Choosing a model', 'Quality, cost and latency, and which option pays for itself.')

lesson(MODULE, 'percentile',
    title='Latency that users feel',
    checked='2026-10-15',
    sources=[source('MLflow: Search Traces', 'https://mlflow.org/docs/latest/genai/tracing/search-traces/')],
    learn=[
        '**Latency** is how long a request takes to come back, often in milliseconds (ms; 1,000 ms is one second). Averages hide slow requests. **p95** is the time that 95 out of 100 requests finish within (they take that long or less). p99 is the same for 99 out of 100.',
        "Measure **end-to-end latency**: the whole request (retrieval, tools, model calls), which is what a trace's total duration gives you. A **trace** is MLflow's record of every step one request went through. Compare models and configs (their settings) on p95.",
    ],
    example=example('Finding slow traces in MLflow', """slow = mlflow.search_traces(
    filter_string="trace.execution_time_ms > 5000",   # slower than 5 seconds
    max_results=100,
)"""),
    check=question(
        "A model's average latency is 900 ms and its p95 is 4 seconds. What do users experience?",
        ['Everything feels fast: the average is 900 ms', 'About 1 in 20 requests feels slow', 'Every request takes about 900 ms'],
        answer=1,
        why='p95 at 4 seconds means 5 out of 100 requests take 4 seconds or more: slow enough to notice.',
    ),
    angle=angle(
        pattern='Sort, then pick by position',
        text='The big idea: averages hide slow requests, so teams look at p95, the time that 95 out of 100 requests finish within. Your code sorts the times, fastest first. Then it works out the position: length times percent, divided by 100, rounded up. Adding 99 before whole-number division with `//` is a trick that rounds up. Python counts list places from 0, so position 3 is `ordered[2]`, which is why the code subtracts 1. Mixing those two up is the most common bug.',
        say='"Averages hide the slow requests, so I look at [[p95|the average|the fastest::The time 95 out of 100 requests finish within.]]. If p95 is slow, about one user in [[twenty|two|a thousand::5 out of every 100.]] waits that long."',
        classic=None,
    ),
    stack=stack('MLflow: p95 of your real traces', """traces = mlflow.search_traces(max_results=1000)
# each trace's total time, in milliseconds
durations = list(traces["execution_duration"])
p95 = percentile(durations, 95)   # the function you write here"""),
    exercise=exercise(
        title='The Latency Users Feel',
        topic='models',
        difficulty='easy',
        fn='percentile',
        prompt="""Teams track a **percentile** of response times, not the average. p95, the 95th percentile, is the time that 95 out of 100 requests finish within.

Your function gets two things:

- `latencies`: response times in milliseconds, like `[820, 640, 4100]`.
- `percent`: which percentile you want, like `95` for p95.

Sort the latencies, fastest first. Multiply the list's length by `percent`, divide by 100, and round up to a whole number. That is the position of your answer, counting from 1. This way of finding a percentile is called the **nearest-rank method**. For example, 5 items at 50 percent is 5 times 50 divided by 100, which is 2.5, so round up to position 3. Return the latency at that position.

If `latencies` is empty, return `None`.""",
        pattern='Sort, then pick by position.',
        target='sort the list once, then pick one item',
        realworld='A model with a 900 ms average can still have a 4-second p95, which is what users notice. Compare models and configs on p95 latency, not the average.',
        starter="""def percentile(latencies, percent):
    # your code here
    pass
""",
        solution="""def percentile(latencies, percent):
    if not latencies:
        return None
    ordered = sorted(latencies)
    position = (percent * len(ordered) + 99) // 100
    return ordered[position - 1]
""",
        cases=[
            case([820, 3900, 640, 4100, 700], 80, expected=3900, sample=True),
            case([820, 640, 4100, 700, 910, 760, 690, 3900, 720, 800], 90, expected=3900),
            case([], 95, expected=None),
            case([500], 99, expected=500),
            case([5, 1, 3, 2, 4], 50, expected=3),
            case([10, 20, 30, 40], 100, expected=40),
            case([7, 8, 9], 1, expected=7),
        ],
        guided="""def percentile(latencies, percent):
    # Replace every ___ with real code, then run the tests.

    if not latencies:
        return None
    # Step 1: sort the latencies, fastest first.
    ordered = ___
    # Step 2: the position, rounded up (done for you).
    position = (percent * len(ordered) + 99) // 100
    # Step 3: return the item at that position.
    # Indexes start at 0, so take 1 off position.
    return ordered[___]
""",
        fills=['sorted(latencies)', 'position - 1'],
        concepts=[
            [
                'sorted',
                'Gives back a new list, smallest first, and leaves the original alone.',
                'sorted([3, 1, 2])   # [1, 2, 3]',
            ],
            [
                'Indexes start at 0',
                'The first item of a list is at index 0, the second at index 1, and so on.',
                """letters = ['a', 'b', 'c']
letters[0]   # 'a'
letters[2]   # 'c'""",
            ],
            [
                'Rounding up with //',
                '`//` divides and drops anything after the decimal point. Adding 99 before dividing by 100 makes it round up instead.',
                """250 // 100          # 2
(250 + 99) // 100   # 3
(400 + 99) // 100   # 4""",
            ],
            [
                'if not',
                '`not items` is True when the list is empty, so the code under `if not items:` runs only for an empty list.',
                """items = []
if not items:
    print('nothing here')""",
            ],
        ],
        byhand='Sorted, fastest first: 640, 700, 820, 3900, 4100. 5 times 80 divided by 100 is exactly 4, so there is nothing to round up. (If it came to 3.5, you would round up to position 4.) The answer is at position 4. Position 4 is index 3, because indexes start at 0. That latency is 3900. Check: 4 of the 5 requests take 3900 ms or less, which is 80 percent. So return 3900.',
        why='Sorting the list is the most work. Picking one item after that is quick.',
        gotchas=[
            [
                'Average lies about latency',
                'Out of 100 requests, 98 take 100 ms and 2 time out at 30 seconds. The average is about 700 ms, but the p99 is 30 seconds.',
            ],
            [
                'Measure where the user is',
                "Latency measured inside the model call misses retrieval, tools and network. Use the whole trace's duration.",
            ],
        ],
    ),
)

# The exercise's sample runs, drawn above the practice questions in "Comparing LLMs for a task".
MODEL_RUNS_TITLE = 'One run per model, same eval set · cost per 1,000 calls'
MODEL_RUNS = """model         quality  cost   p95_ms
fast-model    0.78     $0.40   900
smart-model   0.88     $3.00  2400
old-model     0.75     $1.20  1500"""

lesson(MODULE, 'pareto_models',
    title='Comparing LLMs for a task',
    learn=[
        'To choose a model for a task, run each candidate on the **same eval set**, with the **same judge**, and record **quality, cost and p95 latency** as one MLflow run per model.',
        "Throw out any model that another model beats: at least as good on quality, cost and latency, and better on at least one. The usual term is that the winner **dominates** the loser. What's left is a short list of real trade-offs, decided by what quality is worth to you. The models nothing beats are called the **Pareto front**.",
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
        pattern='Compare every pair',
        text="The big idea: throw out any model that another model beats, and what's left is a short list of real trade-offs. A helper, `beats`, says model A beats B if A is at least as good on quality, cost and latency, and better on at least one. Your code compares each model with every model in the list and keeps it only if none beats it. That is fine for a handful of models, but with thousands the number of comparisons grows very fast.",
        say='"I drop any model that another one beats: at least as good on quality, cost and speed, and [[better on one|worse on one|equal on all::Matching everywhere isn\'t enough; it has to win somewhere.]]. What\'s left is the [[Pareto front|best model|test set::The models nothing else beats.]], a short list of real [[trade-offs|winners|mistakes::Each one is better at something and worse at something else.]]."',
        classic=None,
    ),
    stack=stack('MLflow: one run per candidate endpoint', """# candidates: names of the models you can call in Databricks.
# Each one is a serving endpoint: a web address your code sends questions to.
for endpoint in candidates:
    with mlflow.start_run(run_name=endpoint):
        mlflow.log_param("endpoint", endpoint)
        mlflow.genai.evaluate(data=eval_set, predict_fn=make_app(endpoint), scorers=[Correctness()])"""),
    exercise=exercise(
        title='Keep the Models Nothing Beats',
        topic='models',
        difficulty='medium',
        fn='pareto_models',
        prompt="""You tested some models on the same task. `models` is a list of dicts, one per model, like `{"name": "fast-model", "quality": 0.78, "cost": 0.4, "p95_ms": 900}`.

- `quality`: the eval score. Higher is better.
- `cost`: dollars per 1,000 calls. Lower is better.
- `p95_ms`: the p95 latency in milliseconds. Lower is better.

Model A **beats** model B (the usual term is **dominates**) when A is at least as good on all three, and better on at least one. So two models with the same numbers do not beat each other.

Return the names of the models that no other model beats, in their original order. These are called the Pareto front, which is where the name `pareto_models` comes from.""",
        pattern='Compare every pair: keep a model only if no other model beats it.',
        target='compare each model with every other one (fine for a handful)',
        realworld='There is rarely one best model. A small model can be the right choice for a high-volume, simple task, and a large one for rare, hard questions. Throwing out models that lose on every measure leaves a short list to decide between on value.',
        practice=practice(
            intro='Read one run per model the way a reviewer does: throw out any model another one beats, and check the comparison was fair.',
            explain='You threw out any model that another one beats on quality, cost and latency together, and kept the ones nothing beats: the Pareto front, a short list of real trade-offs. Two models with the same numbers both stay, and a score from a different judge can\'t be compared fairly.',
            pattern='Throw out any model another one beats',
            realworld='When your team picks a model for a new task, run each candidate on the same eval set with the same judge, and log quality, cost and p95 latency. Drop the ones another model beats, then choose from the rest on what quality is worth to you.',
            asks=[
                ask('Which model can you throw out?', ['fast-model', 'smart-model', 'old-model'], answer=2,
                    evidence=evidence('code', title=MODEL_RUNS_TITLE, text=MODEL_RUNS),
                    clue='Look for a row that loses to one other row on quality, cost and p95 all at once.',
                    why='fast-model beats old-model on all three: higher quality, cheaper and faster. Nothing makes old-model the right choice.',
                    wrong=['Nothing is cheaper or faster than fast-model, so nothing beats it.', 'Nothing scores higher than smart-model, so nothing beats it.', None]),
                ask('smart-model costs over seven times as much as fast-model. Does fast-model beat it?', ['Yes: it\'s far cheaper and faster', 'No: smart-model scores higher'], answer=1,
                    evidence=evidence('code', title=MODEL_RUNS_TITLE, text=MODEL_RUNS),
                    clue='To beat it, fast-model must be at least as good on every column, quality included.',
                    why='fast-model is cheaper and faster but scores lower, so neither beats the other. Both stay on the shortlist, and what quality is worth to you decides between them.',
                    wrong=['Beating needs at least as good on all three, and fast-model scores lower.', None]),
                ask('Two endpoints come back with exactly the same numbers. Which stay on the shortlist?', ['Both: neither is better at anything', 'Neither: they cancel each other out', 'Only the first one in the list'], answer=0,
                    evidence=evidence('code', title='Two more runs', text="""model     quality  cost   p95_ms
model-a   0.80     $1.00  100
model-b   0.80     $1.00  100"""),
                    clue='To beat another model, one has to be better on at least one column.',
                    why='Equal on everything means neither beats the other, so both stay. Choose between them on something else, like which one your team already runs.',
                    wrong=[None, 'A model is only thrown out when something beats it, and nothing does.', 'Being listed first isn\'t a measure.']),
                ask('What do you do?', ['Use it: the numbers are close enough', 'Rerun it with the same judge first', 'Drop smart-model from the shortlist'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"smart-model\'s 0.88 is from last month\'s run, with a different judge. Close enough to compare."'),
                    clue='A comparison is only fair when the eval set and the judge are held fixed.',
                    why='A different judge can score the same answers differently, so the gap might be the judge, not the model. Same eval set, same judge, then compare.',
                    wrong=['A different judge can move a score by more than the gap between models.', None, 'It may be the best model. You just can\'t tell from this number.']),
            ],
        ),
        starter="""def pareto_models(models):
    # your code here
    pass
""",
        solution="""def beats(a, b):
    no_worse = (a["quality"] >= b["quality"]
                and a["cost"] <= b["cost"]
                and a["p95_ms"] <= b["p95_ms"])
    better = (a["quality"] > b["quality"]
              or a["cost"] < b["cost"]
              or a["p95_ms"] < b["p95_ms"])
    return no_worse and better


def pareto_models(models):
    kept = []
    for model in models:
        beaten = False
        for other in models:
            if beats(other, model):
                beaten = True
        if not beaten:
            kept.append(model["name"])
    return kept
""",
        cases=[
            case([
                {'name': 'fast-model', 'quality': 0.78, 'cost': 0.4, 'p95_ms': 900},
                {'name': 'smart-model', 'quality': 0.88, 'cost': 3, 'p95_ms': 2400},
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
        guided="""# Replace every ___ with real code, then run the tests.

def beats(a, b):
    # True when model a beats model b.
    # Step 1: a is at least as good as b on all three.
    no_worse = (a["quality"] >= b["quality"]
                and a["cost"] <= b["cost"]
                and a["p95_ms"] <= b["p95_ms"])
    # Step 2: a is better on at least one.
    # For p95_ms, lower is better.
    better = (a["quality"] > b["quality"]
              or a["cost"] < b["cost"]
              or ___)
    return no_worse and better


def pareto_models(models):
    kept = []
    for model in models:
        # Step 3: ask beats() if other beats this model.
        # A model never beats itself, so no need to skip it.
        beaten = False
        for other in models:
            if ___:
                beaten = True
        # Step 4: keep the name only if nothing beat it.
        if ___:
            kept.append(model["name"])
    return kept
""",
        fills=['a["p95_ms"] < b["p95_ms"]', 'beats(other, model)', 'not beaten'],
        concepts=[
            [
                'Dict access',
                '`model["name"]` gets one field from a dict.',
                """car = {'colour': 'red', 'seats': 4}
car['seats']   # 4""",
            ],
            [
                'and, or',
                '`and` is True only when both sides are True. `or` is True when at least one side is. Brackets let a long condition run over several lines.',
                """ok = (age >= 18
      and has_ticket)
free = (age < 5
        or is_member)""",
            ],
            [
                'A helper function',
                'Putting one rule in its own small function keeps the main loop easy to read. You call it like any other function.',
                """def is_long(word):
    return len(word) > 5
is_long('banana')   # True""",
            ],
            [
                'A True/False flag',
                'Start a variable at False. Set it to True inside the loop when you find what you are looking for. After the loop, `if not found:` means it never happened.',
                """found = False
for word in ['hi', 'stop']:
    if word == 'stop':
        found = True""",
            ],
            [
                'A loop inside a loop',
                'For each item of the outer loop, the inner loop goes through the whole list again. So every item meets every other item.',
                """for a in ['x', 'y']:
    for b in ['x', 'y']:
        print(a, b)   # x x, x y, y x, y y""",
            ],
            [
                'Adding to a list',
                '`my_list.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ana')   # ['Ana']""",
            ],
        ],
        byhand='fast-model: smart-model does not beat fast-model, because smart-model costs more (3 against 0.4). old-model does not beat fast-model either, because old-model costs more (1.2 against 0.4). Keep fast-model. smart-model: fast-model scores lower (0.78 against 0.88), so fast-model does not beat smart-model. old-model scores lower too (0.75 against 0.88). Keep smart-model. old-model: fast-model beats it. fast-model scores higher (0.78 against 0.75), costs less (0.4 against 1.2) and is faster (900 ms against 1500 ms). Drop old-model. So return ["fast-model", "smart-model"], in their original order.',
        why='Every model is compared with every other, which is fine for a handful of models.',
        gotchas=[
            [
                'Same eval set, same judge, fair prompts',
                'Model comparisons are only fair when the eval set and the judge are held fixed. Use the same prompt for every model unless the prompt is what you are testing. If one prompt was tuned for one model, give the others a fair version too.',
            ],
            [
                'Quality on your task, not a leaderboard',
                'Public benchmarks (standard test sets that every model gets scored on) rarely match your data. Thirty real examples from your own task tell you more.',
            ],
        ],
    ),
)

lesson(MODULE, 'better_option',
    title='Net value per month',
    learn=[
        'Every experiment ends with a decision, and the decision is about value: what does a success earn or save, and what does each call cost?',
        'Net monthly value is what good answers earn (volume times success rate times value per success) minus what the calls cost (volume times cost per call). A cheaper model can end up making less money if it succeeds less often, and an expensive one can pay for itself many times over.',
        'People often call this the return on investment (ROI) question. Strictly, ROI is profit divided by cost, but for choosing a model, the total net value is what matters.',
    ],
    example=example('Log the business number with the run', """with mlflow.start_run(run_name="decision-oct"):
    mlflow.log_params({"volume": 10000, "value_per_success": 4.0})
    mlflow.log_metric("net_monthly_value", 35700)
    mlflow.set_tag("decision", "ship smart-model")"""),
    check=question(
        'A model costs 10 times more per call but resolves 25 more tickets out of every 100, each worth $4. Its calls cost $0.02 instead of $0.002. Is it worth it?',
        [
            'No: it costs 10 times more per call',
            'Yes: the extra tickets are worth more',
            "Can't tell without the monthly volume",
        ],
        answer=1,
        why='25 extra resolutions per 100 calls are worth $100 (25 times $4). Those 100 calls cost only $1.80 more (100 times the extra $0.018 per call), so the extra tickets are worth far more than the extra cents.',
    ),
    angle=angle(
        pattern='Work out the net, keep the best',
        text='The big idea: choose a model by the money it makes after paying for its calls, not by its price or success rate alone. For each option, your code works out the net: volume times success rate times value per success, minus volume times cost per call. It remembers the best net so far, like holding on to the highest card you have seen. A new option replaces it only if its net is strictly bigger, so on a tie the one listed first wins.',
        say='"For each model, I take what good answers earn and [[subtract|add|multiply by::Paying for calls takes money away.]] what the calls cost. I pick the one that leaves the most money each month, not just the [[cheapest|fastest|newest::A low price per call can still lose if it fails often.]]."',
        classic=None,
    ),
    stack=stack('MLflow: log each option\'s inputs', """for option in options:   # one run per model
    with mlflow.start_run(run_name=option["name"]):
        mlflow.log_metrics({
            "success_rate": option["success_rate"],
            "cost_per_call": option["cost_per_call"],
        })"""),
    exercise=exercise(
        title='Most Value per Month',
        topic='models',
        difficulty='easy',
        fn='better_option',
        prompt="""Pick the model that makes the most money each month, after paying for its calls.

Your function gets three things:

- `options`: the models you could use, each a dict like `{"name": "smart-model", "success_rate": 0.9, "cost_per_call": 0.03}`. A `success_rate` of 0.9 means 9 in 10 answers are good. `cost_per_call` is dollars per call.
- `volume`: how many requests come in each month, like `10000`.
- `value_per_success`: how many dollars one good answer is worth, like `4.0`.

For each option, work out:

- earned: `volume` times its `success_rate` times `value_per_success`.
- spent: `volume` times its `cost_per_call`.
- net: earned minus spent.

Return the name of the option with the highest net. If two tie, return the one listed first. There is always at least one option.""",
        pattern='Score every option with the same formula, keep the best so far.',
        target='one pass over the options',
        realworld='People often call this the return on investment (ROI) question. Strictly, ROI is profit divided by cost, which can pick a different winner, so say "net value". A cheaper model that answers fewer questions can end up making less money, and an expensive one can pay for itself. Value per success is a business number: get it from the team that owns the outcome.',
        starter="""def better_option(options, volume, value_per_success):
    # your code here
    pass
""",
        solution="""def better_option(options, volume, value_per_success):
    best_name = None
    best_net = None
    for option in options:
        rate = option["success_rate"]
        earned = volume * rate * value_per_success
        spent = volume * option["cost_per_call"]
        net = earned - spent
        if best_net is None or net > best_net:
            best_name = option["name"]
            best_net = net
    return best_name
""",
        cases=[
            case([
                {'name': 'fast-model', 'success_rate': 0.72, 'cost_per_call': 0.002},
                {'name': 'smart-model', 'success_rate': 0.9, 'cost_per_call': 0.03},
            ], 10000, 4.0, expected='smart-model', sample=True),
            case([
                {'name': 'fast-model', 'success_rate': 0.72, 'cost_per_call': 0.002},
                {'name': 'smart-model', 'success_rate': 0.9, 'cost_per_call': 0.03},
            ], 10000, 0.1, expected='fast-model'),
            case([{'name': 'only', 'success_rate': 0.5, 'cost_per_call': 0.01}], 100, 1.0, expected='only'),
            case([
                {'name': 'a', 'success_rate': 0.8, 'cost_per_call': 0.01},
                {'name': 'b', 'success_rate': 0.81, 'cost_per_call': 0.5},
            ], 1000, 1.0, expected='a'),
            case([
                {'name': 'x', 'success_rate': 0.6, 'cost_per_call': 0.1},
                {'name': 'y', 'success_rate': 0.6, 'cost_per_call': 0.1},
            ], 10, 2.0, expected='x'),
        ],
        guided="""def better_option(options, volume, value_per_success):
    # Replace every ___ with real code, then run the tests.

    best_name = None   # name of the best option so far
    best_net = None    # its net value
    for option in options:
        # Money earned by good answers this month.
        rate = option["success_rate"]
        earned = volume * rate * value_per_success
        # Step 1: money spent on calls this month.
        spent = ___
        net = earned - spent
        # Step 2: replace the best only if net is bigger.
        # A tie keeps the earlier option.
        if best_net is None or ___:
            best_name = option["name"]
            best_net = net
    return best_name
""",
        fills=['volume * option["cost_per_call"]', 'net > best_net'],
        concepts=[
            [
                'Dict access',
                '`option["name"]` gets one field from a dict.',
                """car = {'colour': 'red', 'seats': 4}
car['seats']   # 4""",
            ],
            [
                'Best so far',
                'Start with None, which means "nothing yet". Replace it each time you find something bigger. `is None` checks for it.',
                """best = None
for n in [3, 9, 4]:
    if best is None or n > best:
        best = n""",
            ],
        ],
        byhand='fast-model earns 10,000 times 0.72 times 4, which is 28,800 dollars. It spends 10,000 times 0.002, which is 20 dollars. Its net is 28,780. smart-model earns 10,000 times 0.9 times 4, which is 36,000 dollars. It spends 10,000 times 0.03, which is 300 dollars. Its net is 35,700. 35,700 is higher, so return "smart-model".',
        why='One pass over the options.',
        gotchas=[
            [
                'Count every cost',
                'Per-call model cost is only part of it: retrieval, retries, agent steps, evaluation runs and human review all count. Traces with token counts make this possible.',
            ],
            [
                'Success must be measured, not assumed',
                "The success rate comes from your evals and from production feedback. If it's a guess, the net value is a guess.",
            ],
        ],
    ),
)
