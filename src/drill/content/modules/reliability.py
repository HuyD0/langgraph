"""Reliability: Timeouts, circuit breakers and error budgets: staying up when the services you rely on don't."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('reliability', 'Reliability', "Timeouts, circuit breakers and error budgets: staying up when the services you rely on don't.")

lesson(MODULE, 'plan_calls',
    title='Timeouts and deadlines',
    learn=[
        'Every call that can wait forever eventually will. Set a timeout on every model and HTTP call.',
        "Better still, give the whole request a **deadline** and pass the remaining time down, so no step starts work it can't finish.",
    ],
    example=example('A 2-second budget (2,000 ms; ms means thousandths of a second)',"retrieve 400 ms → rerank 900 ms → generate 1,200 ms won't fit → fall back"),
    check=question(
        'A user-facing request has a 3-second budget and retrieval took 2.8 s. What should the model call do?',
        [
            'Start anyway',
            "Skip it and return a fallback, since it can't finish in time",
            'Wait for retrieval to retry',
        ],
        answer=1,
        why="Starting work that can't finish wastes capacity and still fails the user.",
    ),
    angle=angle(
        pattern='Spend down a time budget',
        text="The big idea: give the whole request a deadline and pass the time left down, so no step starts work it can't finish. Your code starts with all of `deadline_ms` as time left and goes through the steps in order. A step runs only if its time is at most the time left, and then its time is taken off. A step that doesn't fit is skipped, but a shorter one later may still fit. It is like spending pocket money: buy what you can afford, skip what you can't.",
        say='"I pass the time left down the request. Each step runs only if it fits in what remains, so nothing starts work it can\'t finish before the deadline."',
        classic=None,
    ),
    stack=stack('asyncio: a timeout on every call', """async with asyncio.timeout(remaining_seconds):
    answer = await llm.ainvoke(messages)
# raises TimeoutError instead of waiting forever"""),
    exercise=exercise(
        title='Work Within a Deadline',
        topic='reliability',
        difficulty='easy',
        fn='plan_calls',
        prompt="""Your function gets two things:

- `deadline_ms`: the most time the whole request may take, in milliseconds (ms, thousandths of a second), like `2000`.
- `steps`: the steps to try, in order. Each step is `[name, ms]`: its name and how many milliseconds it takes, like `["rerank", 900]`.

Keep track of the time left. It starts at `deadline_ms`. For each step, if its time is at most the time left, the step runs: add its name to your list and take its time off the time left. If not, skip it and go on to the next step. A shorter step later may still fit.

Return the names of the steps that run, in order.""",
        pattern='Carry the time left forward and check it before each step.',
        target='one pass over the steps',
        realworld="Timeouts stop one slow call from stalling everything. Passing the time left to each step (called deadline propagation) means no step starts work it can't finish. Google's site reliability teams use this so one slow service doesn't drag down the others.",
        starter="""def plan_calls(deadline_ms, steps):
    # your code here
    pass
""",
        solution="""def plan_calls(deadline_ms, steps):
    ran = []
    time_left = deadline_ms
    for name, ms in steps:
        if ms <= time_left:
            ran.append(name)
            time_left -= ms
    return ran
""",
        cases=[
            case(2000, [['retrieve', 400], ['rerank', 900], ['generate', 1200], ['cite', 300]], expected=['retrieve', 'rerank', 'cite'], sample=True),
            case(100, [], expected=[]),
            case(500, [['generate', 500]], expected=['generate']),
            case(300, [['rerank', 400], ['cite', 100]], expected=['cite']),
            case(1000, [['retrieve', 600], ['rerank', 600], ['generate', 300]], expected=['retrieve', 'generate']),
        ],
        guided="""def plan_calls(deadline_ms, steps):
    # Replace every ___ with real code, then run the tests.

    ran = []
    time_left = deadline_ms
    for name, ms in steps:
        # Step 1: is ms at most time_left?
        if ___:
            ran.append(name)
            # Step 2: take ms off time_left.
            ___
    return ran
""",
        fills=['ms <= time_left', 'time_left -= ms'],
        concepts=[
            [
                'Two names from each pair',
                'When every item is a pair, `for a, b in items:` puts the two parts of each pair into two names.',
                """prices = [["tea", 3], ["jam", 5]]
for item, price in prices:
    print(item, price)""",
            ],
            [
                'Spend from a budget',
                '`<=` means "at most": `4 <= money` is True when 4 is at most money. `money -= 4` is short for `money = money - 4`.',
                """money = 10
if 4 <= money:
    money -= 4   # money is now 6""",
            ],
        ],
        byhand='Time left: 2000. retrieve takes 400. It fits, so it runs: 1600 left. rerank takes 900. It fits, so it runs: 700 left. generate takes 1200. That is more than 700, so skip it. cite takes 300. It fits, so it runs: 400 left. Return retrieve, rerank and cite.',
        why='One pass over the steps.',
        gotchas=[
            [
                'A skipped step needs a fallback',
                "If generation can't fit, return the retrieved passages or a short canned answer rather than nothing.",
            ],
            [
                'Every call needs a timeout',
                'Libraries often default to waiting forever. Set one on every HTTP and model call.',
            ],
        ],
    ),
)

lesson(MODULE, 'circuit_breaker',
    title='Circuit breakers and fallbacks',
    learn=[
        'When a service you depend on (a dependency, like a reranker or model endpoint) is down, calling it again and again makes everything slower and the outage worse.',
        'A **circuit breaker** stops calling after repeated failures, fails fast to a **fallback** (a cheaper model, a cached answer), and tries again after a cooldown.',
    ],
    example=example('Closed → open → trial', """closed: calls go through, failures are counted
open:   calls are blocked for the cooldown
trial:  one call; success closes it, failure re-opens it"""),
    check=question(
        'Your reranker endpoint is timing out on every call. What should the app do?',
        ['Keep retrying each request', 'Stop calling it for a while and skip reranking', 'Crash'],
        answer=1,
        why='Serve slightly worse results instead of slow failures.',
    ),
    angle=angle(
        pattern='Remember failures and when it opened',
        text='The big idea: when a service keeps failing, stop calling it for a while instead of making the outage worse. Your code remembers two things: how many failures in a row, and when the breaker opened, which is `None` while it is closed. A call during the cooldown is blocked and changes nothing. A working call resets the count and closes the breaker. A failed call adds 1, and reaching `threshold` opens the breaker at that time, like a fuse box switch that trips.',
        say='"After enough failures in a row, the breaker opens and blocks calls for a cooldown, so we fail fast to a fallback. A success closes it again."',
        classic=None,
    ),
    stack=stack('Python: fall back while the breaker is open', """def rerank(docs):
    if breaker.is_open():
        return docs                      # fallback: skip reranking
    try:
        result = reranker.invoke(docs)
        breaker.record_success()
        return result
    except Exception:
        breaker.record_failure()
        return docs"""),
    exercise=exercise(
        title='Stop Calling a Failing Service',
        topic='reliability',
        difficulty='medium',
        fn='circuit_breaker',
        prompt="""A **circuit breaker** stops calling a service that keeps failing.

Your function gets three things:

- `calls`: the calls, in order. Each is `[time, ok]`, like `[5, True]`: the time in seconds, and whether the call works (`True`) or fails (`False`).
- `threshold`: how many failures in a row open the breaker, like `2`.
- `cooldown`: how many seconds calls are blocked after it opens, like `10`.

Start with a failure count of 0 and the breaker closed (calls go through). For each call:

- If the breaker is open and `time` is earlier than the time it opened plus `cooldown`, the result is `"blocked"`. Nothing else changes.
- Otherwise, if the call works, the result is `"ok"`. The count goes back to 0 and the breaker closes.
- Otherwise, the result is `"fail"`. Add 1 to the count (only a success resets it). If the count is now `threshold` or more, the breaker opens at this `time`.

Return one result per call, in order.""",
        pattern='Keep two things as you go: failures in a row, and when the breaker opened. Decide each call from those.',
        target='one pass over the calls',
        realworld='Without a breaker, every request waits for a dead service to time out, and retries make it worse. With one, you switch to a fallback (a cheaper model, a cached answer) at once, and check back after a cooldown.',
        starter="""def circuit_breaker(calls, threshold, cooldown):
    # your code here
    pass
""",
        solution="""def circuit_breaker(calls, threshold, cooldown):
    results = []
    failures = 0
    opened_at = None
    for time, ok in calls:
        if opened_at is not None and time < opened_at + cooldown:
            results.append("blocked")
        elif ok:
            results.append("ok")
            failures = 0
            opened_at = None
        else:
            results.append("fail")
            failures += 1
            if failures >= threshold:
                opened_at = time
    return results
""",
        cases=[
            case([[0, False], [1, False], [5, True], [12, False], [30, True]], 2, 10, expected=['fail', 'fail', 'blocked', 'fail', 'ok'], sample=True),
            case([], 2, 5, expected=[]),
            case([[0, True], [1, False], [2, True], [3, False]], 2, 5, expected=['ok', 'fail', 'ok', 'fail']),
            case([[0, False], [1, False], [5, True], [6, True]], 2, 4, expected=['fail', 'fail', 'ok', 'ok']),
            case([[0, False], [1, False], [2, False], [3, True], [12, False], [13, True], [25, True]], 3, 10, expected=['fail', 'fail', 'fail', 'blocked', 'fail', 'blocked', 'ok']),
        ],
        guided="""def circuit_breaker(calls, threshold, cooldown):
    # Replace every ___ with real code, then run the tests.

    results = []
    failures = 0      # failures in a row
    opened_at = None  # None means the breaker is closed
    for time, ok in calls:
        # Step 1: is time earlier than opened_at + cooldown?
        if opened_at is not None and ___:
            results.append("blocked")
        elif ok:
            # A success resets the count and closes it.
            results.append("ok")
            failures = 0
            opened_at = None
        else:
            results.append("fail")
            failures += 1
            # Step 2: is failures at threshold or more?
            if ___:
                opened_at = time
    return results
""",
        fills=['time < opened_at + cooldown', 'failures >= threshold'],
        concepts=[
            [
                'None means "no value yet"',
                '`None` is how Python says "nothing here". Check for it with `is None` or `is not None`. `a and b` is True only when both are True, so the `if` below checks both.',
                """winner = None
if winner is not None and winner > 3:
    print(winner)""",
            ],
            [
                'if, elif, else',
                'Python tries each test in order and runs only the first block whose test is True. `else` runs when none were. A True/False value can be the test itself: `if ok:` runs when ok is True.',
                """raining = True
if raining:
    print("umbrella")
else:
    print("sunglasses")""",
            ],
            [
                'Two names from each pair',
                'When every item is a pair, `for a, b in items:` puts the two parts of each pair into two names.',
                """prices = [["tea", 3], ["jam", 5]]
for item, price in prices:
    print(item, price)""",
            ],
            [
                'Add one to a count',
                '`n += 1` is short for `n = n + 1`.',
                """misses = 0
misses += 1   # misses is now 1""",
            ],
            [
                'Compare two numbers',
                '`a < b` is True when a is smaller (for times: earlier). `a >= b` is True when a is b or more.',
                """age = 20
print(age < 18)    # False
print(age >= 18)   # True""",
            ],
        ],
        byhand='Time 0 fails: count 1. Time 1 fails: count 2, which reaches the threshold of 2. The breaker opens at 1. 1 plus 10 is 11, so calls before time 11 are blocked. Time 5 is earlier than 11: blocked. The count stays at 2. Time 12 is not earlier than 11, so it is sent as a trial. It fails: count 3, which is 2 or more, so the breaker re-opens at 12. 12 plus 10 is 22, so calls before time 22 are blocked. Time 30 is not earlier than 22, so it is sent as a trial. It works: ok, the count goes back to 0 and the breaker closes. Return fail, fail, blocked, fail, ok.',
        why='One pass over the calls.',
        gotchas=[
            [
                'Have a fallback ready',
                'A breaker without a fallback just fails faster. Decide what users get instead: a cheaper model, a cached answer, or a clear message.',
            ],
            [
                'One breaker per service',
                "Keep one breaker for each service you call, so a broken reranker doesn't block the main model.",
            ],
        ],
    ),
)

lesson(MODULE, 'burn_rate',
    title='SLOs and error budgets',
    learn=[
        'An **SLO** (service level objective) is a reliability target, like 99.5% of requests succeeding. The other 0.5% is your **error budget**.',
        "Alert on how fast you're using up the budget (the **burn rate**), not on every error. That pages people (sends an urgent alert to whoever is on call) only when it matters.",
    ],
    example=example('Burn rate', """allowed failure rate: 0.5%
actual failure rate: 7.2%
burn rate: 7.2 / 0.5 = 14.4 → page someone"""),
    check=question(
        'Errors are at 0.6% against a 0.5% budget. Is this an emergency?',
        ['Yes, page now', 'No: the burn rate is about 1.2, so watch it', 'Turn the feature off'],
        answer=1,
        why='Slightly over budget is a trend to fix, not a 3am page.',
    ),
    angle=angle(
        pattern='Actual errors over allowed errors',
        text='The big idea: alert on how fast you use up the error budget, not on every error. Your code first returns 0.0 if there were no requests, so it never divides by 0. Then it works out the share that failed, `errors / total`, and the share allowed, `1 - slo`. Dividing the first by the second gives the burn rate, rounded to 1 place. With 72 failures in 1000 and a 99.5% target, that is 0.072 divided by 0.005, or 14.4 times too fast.',
        say='"I alert on how fast we use up the error budget, not on raw error counts. A burn rate of 1 is on budget. 10 is ten times too fast."',
        classic=None,
    ),
    stack=stack('Databricks SQL: error rate over the last hour, for an alert', """SELECT try_divide(count_if(status = 'ERROR'), count(*)) AS error_rate
  -- NULL when there were no requests
FROM agent_requests
WHERE request_time >= now() - INTERVAL 1 HOUR"""),
    exercise=exercise(
        title='Error Budgets',
        topic='reliability',
        difficulty='easy',
        fn='burn_rate',
        prompt="""An **SLO** (service level objective) is a reliability target, like 99.5% of requests succeeding. The other 0.5% is your **error budget**: the failures you are allowed. The **burn rate** says how fast you are using it up. 1.0 means exactly on budget. 10 means ten times too fast.

Your function gets three things:

- `errors`: how many requests failed, like `72`.
- `total`: how many requests there were, like `1000`.
- `slo`: the target as a decimal, like `0.995` for 99.5%.

The error rate (the share of requests that failed) is `errors / total`. The allowed rate is `1 - slo`. The burn rate is the error rate divided by the allowed rate. Return it, rounded to 1 decimal place. If `total` is 0, return `0.0`.""",
        pattern='Turn two counts into a rate, then divide it by the rate the target allows.',
        target='a few simple calculations, no loop',
        realworld="Alerting on raw error counts wakes people at 3am for noise. Alerting on the burn rate instead pages someone only when the budget is really at risk, which is the practice Google's site reliability book describes. On Databricks you'd compute it from system tables or traces with a SQL alert.",
        starter="""def burn_rate(errors, total, slo):
    # your code here
    pass
""",
        solution="""def burn_rate(errors, total, slo):
    if total == 0:
        return 0.0
    error_rate = errors / total
    allowed_rate = 1 - slo
    return round(error_rate / allowed_rate, 1)
""",
        cases=[
            case(72, 1000, 0.995, expected=14.4, sample=True),
            case(0, 0, 0.99, expected=0.0),
            case(5, 1000, 0.995, expected=1.0),
            case(30, 2000, 0.99, expected=1.5),
            case(0, 500, 0.999, expected=0.0),
        ],
        guided="""def burn_rate(errors, total, slo):
    # Replace every ___ with real code, then run the tests.

    # No requests means nothing to measure.
    if total == 0:
        return 0.0
    # Step 1: the share of requests that failed.
    error_rate = ___
    # Step 2: the share the SLO allows to fail.
    allowed_rate = ___
    # Step 3: divide error_rate by allowed_rate.
    return round(___, 1)
""",
        fills=['errors / total', '1 - slo', 'error_rate / allowed_rate'],
        concepts=[
            [
                'Division gives a share',
                '`/` divides. `part / whole` gives the share as a decimal.',
                """3 / 4   # 0.75""",
            ],
            [
                'round',
                '`round(x, 1)` keeps 1 decimal place.',
                """round(3.14159, 1)   # 3.1""",
            ],
        ],
        byhand='The error rate is 72 divided by 1000, which is 0.072. The SLO of 0.995 allows 1 minus 0.995, which is 0.005 (the 0.5% budget). 0.072 divided by 0.005 is 14.4 (the same as 72 divided by 5). Return 14.4: the budget is burning 14.4 times too fast.',
        why='Two divisions.',
        gotchas=[
            [
                'Pick the window with the threshold',
                'A high burn rate over the last hour means "page now"; a low one over a few days means "open a ticket and look tomorrow". Teams use both.',
            ],
            [
                'Define failure for AI',
                'For an AI feature, a reply that loads fine but gives a wrong answer is also a failure. Count answers your automatic grader marks wrong, not just crashes and errors.',
            ],
        ],
    ),
)
