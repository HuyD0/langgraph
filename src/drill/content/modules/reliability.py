"""Reliability: Timeouts, circuit breakers and error budgets: staying up when dependencies don't."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('reliability', 'Reliability', "Timeouts, circuit breakers and error budgets: staying up when dependencies don't.")

lesson(MODULE, 'plan_calls',
    title='Timeouts and deadlines',
    learn=[
        'Every call that can wait forever eventually will. Set a timeout on every model and HTTP call.',
        "Better still, give the whole request a **deadline** and pass the remaining time down, so no step starts work it can't finish.",
    ],
    example=example('A 2-second budget', "retrieve 400 ms → rerank 900 ms → generate 1,200 ms won't fit → fall back"),
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
        pattern='Carry a budget forward',
        text='One walk through the steps.',
        say='"I propagate a deadline: each step gets the remaining budget and is skipped or degraded if it can\'t finish in time."',
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
        prompt="""A request must answer within `deadline_ms`. It has optional steps to run in order, each `[name, expected_ms]`. Run a step only if it can finish within what's left of the deadline; otherwise skip it and try the next one, since a shorter later step may still fit.

Return `[ran, skipped, elapsed_ms]`.""",
        pattern='Carry the remaining budget forward and check it before each step.',
        target='one walk through the steps',
        realworld="Timeouts stop one slow call from stalling everything. Passing the remaining time to each step (deadline propagation) means no step starts work it can't finish, which is how Google's SRE practices avoid cascading failures.",
        starter="""def plan_calls(deadline_ms, steps):
    # your code here
    pass
""",
        solution="""def plan_calls(deadline_ms, steps):
    ran, skipped = [], []
    elapsed = 0
    for name, ms in steps:
        if elapsed + ms <= deadline_ms:
            ran.append(name)
            elapsed += ms
        else:
            skipped.append(name)
    return [ran, skipped, elapsed]
""",
        cases=[
            case(2000, [['retrieve', 400], ['rerank', 900], ['generate', 1200], ['cite', 300]], expected=[['retrieve', 'rerank', 'cite'], ['generate'], 1600], sample=True),
            case(100, [], expected=[[], [], 0]),
            case(500, [['a', 500]], expected=[['a'], [], 500]),
            case(300, [['a', 400], ['b', 100]], expected=[['b'], ['a'], 100]),
        ],
        guided="""def plan_calls(deadline_ms, steps):
    # Replace every ___ with real code, then run the tests.

    ran, skipped = [], []
    elapsed = 0
    for name, ms in steps:
        # Step 1: does it fit in what's left?
        if ___:
            ran.append(name)
            elapsed += ms
        else:
            ___
    return [ran, skipped, elapsed]
""",
        fills=['elapsed + ms <= deadline_ms', 'skipped.append(name)'],
        concepts=[
            [
                'A budget that shrinks',
                "Keep how much you've used, and compare against the limit before each step.",
                """if used + cost <= limit:
    used += cost""",
            ],
        ],
        byhand='2,000 ms budget. retrieve 400 (400 used). rerank 900 (1,300). generate 1,200 would make 2,500: skip. cite 300 (1,600): runs.',
        why='One walk through the steps.',
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
        'When a dependency is down, calling it again and again makes everything slower and the outage worse.',
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
        pattern='State machine',
        text='One walk through the events with a couple of state variables. "Design a circuit breaker" is a common system design question.',
        say='"After N consecutive failures the breaker opens and fails fast to a fallback; after a cooldown one trial call decides whether to close it."',
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
        prompt="""A **circuit breaker** stops calling an endpoint that keeps failing, so you fail fast and fall back instead of piling on.

`events` is a list of `[time, ok]`: a call attempted at `time` and whether it would succeed. The breaker starts **closed**. After `threshold` failures in a row it **opens** at that failure's time. While open, calls before `opened_at + cooldown` are blocked (not sent). The first call at or after that time is a trial: if it succeeds the breaker closes and the failure count resets; if it fails, the breaker opens again at that time.

Return, for each event, `"ok"`, `"fail"` or `"blocked"`.""",
        pattern='A small state machine: track the state, the failure count and when it opened; decide each event from those.',
        target='one walk through the events',
        realworld='Without a breaker, every request waits for a dead endpoint to time out, and retries make it worse. With one, you switch to a fallback (a cheaper model, a cached answer) immediately, and check back after a cooldown.',
        starter="""def circuit_breaker(events, threshold, cooldown):
    # your code here
    pass
""",
        solution="""def circuit_breaker(events, threshold, cooldown):
    out = []
    failures = 0
    opened_at = None
    for t, ok in events:
        if opened_at is not None and t < opened_at + cooldown:
            out.append("blocked")
            continue
        if ok:
            out.append("ok")
            failures = 0
            opened_at = None
        else:
            out.append("fail")
            failures += 1
            if opened_at is not None or failures >= threshold:
                opened_at = t
    return out
""",
        cases=[
            case([[0, False], [1, False], [2, False], [3, True], [12, False], [13, True], [25, True]], 3, 10, expected=['fail', 'fail', 'fail', 'blocked', 'fail', 'blocked', 'ok'], sample=True),
            case([], 2, 5, expected=[]),
            case([[0, True], [1, False], [2, True], [3, False]], 2, 5, expected=['ok', 'fail', 'ok', 'fail']),
            case([[0, False], [1, False], [5, True], [6, True]], 2, 4, expected=['fail', 'fail', 'ok', 'ok']),
        ],
        guided="""def circuit_breaker(events, threshold, cooldown):
    # Replace every ___ with real code, then run the tests.

    out = []
    failures = 0       # failures in a row
    opened_at = None   # when the breaker last opened (None = closed)
    for t, ok in events:
        # Step 1: open and still cooling down? Don't send it.
        if opened_at is not None and ___:
            out.append("blocked")
            continue
        if ok:
            # Step 2: a success closes the breaker and resets the count.
            out.append("ok")
            failures = 0
            opened_at = None
        else:
            out.append("fail")
            failures += 1
            # Step 3: a failed trial, or too many failures in a row, opens it (again).
            if opened_at is not None or ___:
                opened_at = t
    return out
""",
        fills=['t < opened_at + cooldown', 'failures >= threshold'],
        concepts=[
            [
                'State in a few variables',
                'A state machine can be just two variables you update as events arrive.',
                """failures = 0
opened_at = None""",
            ],
            [
                'continue',
                'Skip the rest of this loop turn.',
                """if blocked:
    continue""",
            ],
        ],
        byhand='Three failures at 0, 1, 2: the breaker opens at 2. The call at 3 is before 12: blocked. At 12 the trial fails: open again at 12. At 13 (before 22): blocked. At 25 the trial succeeds: closed.',
        why='One walk through the events.',
        gotchas=[
            [
                'Have a fallback ready',
                'A breaker without a fallback just fails faster. Decide what users get instead: a cheaper model, a cached answer, or a clear message.',
            ],
            [
                'Per endpoint, not global',
                "Keep one breaker per dependency, so a broken reranker doesn't block the main model.",
            ],
        ],
    ),
)

lesson(MODULE, 'burn_rate',
    title='SLOs and error budgets',
    learn=[
        'An **SLO** is a reliability target, like 99.5% of requests succeeding. The other 0.5% is your **error budget**.',
        "Alert on how fast you're using up the budget (the **burn rate**), not on every error. That pages people only when it matters.",
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
        pattern='Ratios against a target',
        text='Two divisions.',
        say='"I alert on error-budget burn rate over a window, which ties paging to user impact instead of raw error counts."',
        classic=None,
    ),
    stack=stack('Databricks SQL: error rate over the last hour, for an alert', """SELECT count_if(status = 'ERROR') / count(*) AS error_rate
FROM agent_requests
WHERE request_time >= now() - INTERVAL 1 HOUR"""),
    exercise=exercise(
        title='Error Budgets',
        topic='reliability',
        difficulty='easy',
        fn='burn_rate',
        prompt="""An SLO (service level objective) like 99.5% success means you're allowed 0.5% failures: your **error budget**. The **burn rate** says how fast you're spending it: the error rate divided by the allowed error rate. 1.0 means you'll use exactly the budget; 10 means ten times too fast.

Given `errors` and `total` requests in a window, the `slo` (like 0.995) and an `alert_at` burn rate, return `[burn, alert]`, with burn rounded to 1 place. With no requests, return `[0.0, False]`.""",
        pattern='Turn two raw counts into a ratio against a target, then compare to a threshold.',
        target='a few arithmetic steps',
        realworld="Alerting on raw error counts pages people at 3am for noise. Alerting on burn rate pages only when the budget is really at risk, which is the practice Google's SRE book describes. On Databricks you'd compute it from system tables or traces with a SQL alert.",
        starter="""def burn_rate(errors, total, slo, alert_at):
    # your code here
    pass
""",
        solution="""def burn_rate(errors, total, slo, alert_at):
    if total == 0:
        return [0.0, False]
    burn = round((errors / total) / (1 - slo), 1)
    return [burn, burn >= alert_at]
""",
        cases=[
            case(72, 1000, 0.995, 10, expected=[14.4, True], sample=True),
            case(0, 0, 0.99, 2, expected=[0.0, False]),
            case(5, 1000, 0.995, 2, expected=[1.0, False]),
            case(30, 2000, 0.99, 1.5, expected=[1.5, True]),
        ],
        guided="""def burn_rate(errors, total, slo, alert_at):
    # Replace every ___ with real code, then run the tests.

    if total == 0:
        return [0.0, False]
    # Step 1: error rate divided by the allowed error rate (1 - slo).
    burn = round((errors / total) / ___, 1)
    # Step 2: alert when it's burning at least that fast.
    return [burn, ___]
""",
        fills=['(1 - slo)', 'burn >= alert_at'],
        concepts=[['Division for rates', 'errors / total gives the share that failed.', '72 / 1000   # 0.072']],
        byhand='72 errors in 1,000 is 7.2% failing. The SLO allows 0.5%. 7.2 / 0.5 = 14.4 times too fast: alert.',
        why='Two divisions.',
        gotchas=[
            [
                'Pick the window with the threshold',
                'A high burn rate over 5 minutes means "page now"; a lower one over 6 hours means "look tomorrow". Teams use both.',
            ],
            [
                'Define failure for AI',
                'For an AI feature, a 200 response with a wrong answer is also a failure. Count judge failures from production monitoring, not just HTTP errors.',
            ],
        ],
    ),
)
