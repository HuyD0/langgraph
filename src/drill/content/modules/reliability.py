"""Reliability: Timeouts, circuit breakers and error budgets: staying up when the services you rely on don't."""

from drill.content.model import (angle, ask, card, case, evidence, example, exercise, lesson, module, practice, question, rewrite,
                                 seesaw, sortby, sortrow, stack, steps)

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
            'Start anyway and hope it finishes in time',
            'Skip it and return a fallback answer',
            'Wait for retrieval to run again, faster',
        ],
        answer=1,
        why="Starting work that can't finish wastes capacity and still fails the user.",
    ),
    angle=angle(
        pattern='Spend down a time budget',
        text="The big idea: give the whole request a deadline and pass the time left down, so no step starts work it can't finish. Your code starts with all of `deadline_ms` as time left and goes through the steps in order. A step runs only if its time is at most the time left, and then its time is taken off. A step that doesn't fit is skipped, but a shorter one later may still fit. It is like spending pocket money: buy what you can afford, skip what you can't.",
        say='"I pass the [[time left|full timeout|start time::What remains of the deadline.]] down the request. A step only runs if it [[fits|is first|is fast::Its time must be no more than what remains.]] in what remains, so nothing starts work it can\'t finish."',
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
        'A **circuit breaker** stops calling after repeated failures, fails fast to a **fallback** (a cheaper model, a cached answer), and tries again after a cooldown. It has three states: **closed** (calls go through), **open** (calls are blocked) and **half-open** (after the cooldown, one trial call decides whether to close or open again).',
    ],
    example=example('Closed → open → half-open', """closed:    calls go through, failures are counted
open:      calls are blocked for the cooldown
half-open: one trial call; success closes it,
           failure re-opens it"""),
    check=question(
        'Your reranker endpoint is timing out on every call. What should the app do?',
        ['Keep retrying each request until it answers', 'Stop calling it for a while and skip reranking', 'Stop the whole app until the endpoint is back'],
        answer=1,
        why='Serve slightly worse results instead of slow failures.',
    ),
    angle=angle(
        pattern='Remember failures and when it opened',
        text='The big idea: when a service keeps failing, stop calling it for a while instead of making the outage worse. Your code remembers two things: how many failures in a row, and when the breaker opened, which is `None` while it is closed. A call during the cooldown is blocked and changes nothing. A working call resets the count and closes the breaker. A failed call adds 1, and reaching `threshold` opens the breaker at that time, like a fuse box switch that trips.',
        say='"After [[enough failures|one failure|a slow call::Several in a row, up to a set number.]] in a row, the breaker opens and blocks calls for a while, so we fail fast to a [[fallback|retry|queue::A backup answer.]]. One working call closes it again."',
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
        byhand='Time 0 fails: count 1. Time 1 fails: count 2, which reaches the threshold of 2. The breaker opens at 1. 1 plus 10 is 11, so calls before time 11 are blocked. Time 5 is earlier than 11: blocked. The count stays at 2. Time 12 is not earlier than 11, so the breaker is half-open and the call is sent as a trial. It fails: count 3, which is 2 or more, so the breaker re-opens at 12. 12 plus 10 is 22, so calls before time 22 are blocked. Time 30 is not earlier than 22, so it is sent as a trial. It works: ok, the count goes back to 0 and the breaker closes. Return fail, fail, blocked, fail, ok.',
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
        'Errors are running at 0.6 percent against a 0.5 percent budget. Is this an emergency?',
        ['Yes: page the on-call person right now', 'No: the burn rate is about 1.2, so watch it', 'Yes: turn the feature off until errors drop'],
        answer=1,
        why='Slightly over budget is a trend to fix, not a 3am page.',
    ),
    angle=angle(
        pattern='Actual errors over allowed errors',
        text='The big idea: alert on how fast you use up the error budget, not on every error. Your code first returns 0.0 if there were no requests, so it never divides by 0. Then it works out the share that failed, `errors / total`, and the share allowed, `1 - slo`. Dividing the first by the second gives the burn rate, rounded to 1 place. With 72 failures in 1000 and a 99.5% target, that is 0.072 divided by 0.005, or 14.4 times too fast.',
        say='"I alert on how fast we use up the [[error budget|error count|server budget::The failures your target allows.]], not on every error. A burn rate of 1 means [[on budget|no errors|broken::Spending at exactly the allowed pace.]], and 10 means ten times too fast."',
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
                'A high burn rate over the last hour means "page now"; a low one over a few days means "open a ticket and look tomorrow". Teams use both, which Google calls multiwindow, multi-burn-rate alerts.',
            ],
            [
                'Define failure for AI',
                'For an AI feature, a reply that loads fine but gives a wrong answer is also a failure. Count answers your automatic grader marks wrong, not just crashes and errors.',
            ],
        ],
    ),
)

lesson(MODULE, 'answer_incident',
    title='When it goes wrong in production',
    cards=[
        card('First, stop the harm',
             'A business-critical assistant starts giving confident wrong answers. Before anyone fixes the cause, stop the harm: in minutes, not at the next release. Have these switches ready before launch.',
             picture=sortby('How do you stop the harm, fast?',
                            sortrow('Turn the feature off', 'A switch the platform engineer can flip', 'Minutes', icon='power'),
                            sortrow('Send hard questions to a person', 'The assistant hands over instead of answering', 'Minutes', icon='people'),
                            sortrow('Fall back to a safe answer', 'Like "please check the policy page" with a link', 'Minutes', icon='alert')),
             after='The product manager makes the call; the platform engineer flips the switch.'),
        card('A fix can break other things',
             'A prompt change that stops one wrong answer can quietly change hundreds of others. A rushed fix is how one incident becomes two.',
             picture=seesaw(('The bad answer', 'fixed'), ('Other answers', 'quietly broken'), caption='Check every change against everything that already worked, however urgent.')),
        card('The fast, safe lane',
             'Fast and safe at once: every step is quick, and none is skipped.',
             picture=steps(('pencil', 'Fix, as a new version', 'The AI engineer changes the prompt or retrieval settings, saved as a new version.'),
                           ('person', 'Check the answer', 'The subject-matter expert confirms the fix is right.'),
                           ('flask', 'Must-pass and eval', 'Every must-pass case still passes; the eval lists what got better and what got worse.'),
                           ('activity', 'Canary', 'A small share of traffic gets the fix first, and you compare.'),
                           ('reset', 'Move the pointer', 'The platform engineer points @production at the new version. Going back is one step.'),
                           ('eye', 'Watch', 'Traces and alerts for the next days.'))),
        card('Keep the AI apart from the release',
             'Prompts, model versions and retrieval settings shouldn\'t be baked into the monthly release. The app loads them by a named version, so the AI part can change in hours while the rest of the app ships monthly.',
             picture=rewrite(('Prompt baked into the monthly release', 'Prompt versioned on its own, loaded as @production'),
                             ('The fix waits for next month', 'The fix goes out in hours, through the checks'),
                             ('Rolling back means redeploying the app', 'Rolling back means moving the pointer back'))),
        card('Afterwards, close the gap',
             'When it is over, make sure the same mistake can\'t come back unnoticed.',
             picture=steps(('flask', 'Add it to the must-pass set', 'The SME writes the failing question and its right answer as a new case.'),
                           ('pencil', 'Write down what happened', 'What went wrong and why, with no blame, so the team learns.'),
                           ('activity', 'Catch it sooner next time', 'Would monitoring have spotted it before a customer did? If not, add the check.'))),
    ],
    example=example('The release check after a fix', """must-pass:  39 of 40   refund-07 fails
regressions: refund-07, travel-12
improved:    leave-03 (the bad answer)
# a must-pass case fails: hold,
# fix that too, then check again"""),
    check=question(
        'A prompt fix stops the wrong parental-leave answer. What must happen before it goes to everyone?',
        [
            'Run the must-pass set and the eval',
            'Nothing: the bad answer is fixed',
            'Wait for the next monthly release',
        ],
        answer=0,
        why='The fix may have broken other answers. The must-pass set and the eval show that in minutes, so it can go out the same day, safely. Waiting a month leaves the harm in place.',
    ),
    angle=angle(
        pattern='Hold on a must-pass failure or anything that got worse',
        text='The big idea: when an AI feature goes wrong, you stop the harm in minutes, then ship the fix through a fast lane that still checks it against everything that already worked. Your code compares each case before and after the fix. A case that passed before and fails after is broken, so it goes on a list. The fix is held if any must-pass case fails after the fix, or if anything broke. Otherwise it ships. It returns the decision and the broken cases in A-to-Z order. It is like a mechanic fixing your brakes: before you drive off, they check the lights and steering still work.',
        say='"When the assistant goes wrong I stop the [[harm|team|release::The wrong answers reaching people.]] first, fix it as a new version, run the [[must-pass|newest|cheapest::The cases that may never break.]] cases and the eval, then move the pointer, so going back is one [[step|month|release::Point back at the last good version.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Ship or Hold the Fix',
        topic='reliability',
        difficulty='easy',
        fn='release_check',
        prompt="""Your function gets three things:

- `before`: a dict of case id to `True` (passed) or `False` (failed), before the fix.
- `after`: the same cases after the fix.
- `must_pass`: a list of case ids that must never fail.

A case is **broken** if it passed before and fails after.

Return `[decision, broken]`: `decision` is `"hold"` if any must-pass case fails after the fix or anything is broken, otherwise `"ship"`. `broken` is the list of broken case ids, sorted A to Z.""",
        pattern='Compare before and after, case by case; hold on any must-pass failure or anything broken.',
        target='one pass over the cases',
        realworld='Teams that run an AI feature in production check every urgent fix this way before moving the pointer: the must-pass set and the before-and-after eval. It is quick, and it is what stops one incident becoming two.',
        practice=practice(
            intro='The HR assistant is giving wrong answers to staff. Handle it the way the team does: stop the harm, fix it safely, and close the gap.',
            explain='The big idea: when an AI feature goes wrong, stop the harm in minutes, then ship the fix fast through checks that are never skipped. You switched the feature to a safe answer before rewriting anything, held a fix that broke a must-pass case, rolled back by moving the pointer instead of redeploying, and added the failing question to the must-pass set so it can\'t come back unnoticed.',
            pattern='Stop the harm, then the fast safe lane',
            realworld='Before an AI feature launches, agree who flips the switch, who confirms answers, and who moves the pointer. When something goes wrong, there is no time to find out who those people are.',
            gotchas=[
                ['Fixing before stopping the harm', 'A careful fix takes hours. Switch it off, hand over to a person, or fall back to a safe answer first.'],
                ['Skipping the checks because it is urgent', 'A rushed prompt fix can break other answers. The must-pass set and the eval take minutes; run them every time.'],
                ['Baking the prompt into the release', 'If the prompt ships only with the app, a fix waits for the next release and rolling back means redeploying.'],
            ],
            asks=[
                ask('What do you do in the first ten minutes?', ['Stop the harm: a safe answer or a person', 'Start rewriting the whole prompt', 'Wait for more reports to be sure'], answer=0,
                    evidence=evidence('claim', who='A manager reported', text='"Staff are being told they get 52 weeks of fully paid leave. Some are booking it."'),
                    clue='What stops more people acting on wrong answers right now?',
                    why='A fix takes time; the harm is happening now. Switch to a safe answer or hand questions to a person in minutes, then fix the cause properly.',
                    wrong=[None, 'A rewrite takes hours and needs checking. Stop the harm first.', 'Every minute of waiting, more people act on a wrong answer.']),
                ask('Do you ship this fix?', ['No: a must-pass case now fails', 'Yes: the quality score went up', 'Yes: the bad answer is fixed'], answer=0,
                    evidence=evidence('code', title='The eval after the fix', text="""must-pass:   39 of 40
             refund-07 now fails
leave-03:    fixed
quality:     86 to 88 in 100"""),
                    clue='Which line says something that may never break did break?',
                    why='A must-pass case means hold, whatever the average says. The fix broke the refund answer, so fix that too and check again.',
                    wrong=[None, 'A higher average can hide one dangerous break. Read the must-pass line first.', 'Fixing one answer doesn\'t make up for breaking a must-pass one.']),
                ask('The fix made things worse. What is the fastest safe way back?', ['Point @production at the last good version', 'Rebuild and redeploy the whole app', 'Edit the prompt again by hand, live'], answer=0,
                    evidence=evidence('code', title='How the app loads its prompt', text='prompt = load("prompts:/hr_answer@production")'),
                    clue='The app asks for whatever @production points at.',
                    why='Because the app loads the prompt by its alias, moving @production back to the last good version undoes the fix in one step, with no redeploy.',
                    wrong=[None, 'A redeploy takes longer and changes more than the prompt.', 'Editing live skips every check and can make it worse again.']),
                ask('The incident is over. What stops the same mistake coming back unnoticed?', ['Add the question to the must-pass set', 'Remind everyone to be more careful', 'Switch off the monitoring alerts'], answer=0,
                    alone=True,
                    clue='Which one is checked automatically on every future change?',
                    why='A must-pass case runs on every change from now on, so the same wrong answer can never ship again without someone seeing it.',
                    wrong=[None, 'Care fades; a must-pass case is checked every time.', 'Alerts are how you catch the next one sooner. Keep them.']),
            ],
        ),
        starter="""def release_check(before, after, must_pass):
    # your code here
    pass
""",
        solution="""def release_check(before, after, must_pass):
    broken = []
    for case_id in before:
        if before[case_id] and not after.get(case_id, False):
            broken.append(case_id)
    broken.sort()
    hold = len(broken) > 0
    for case_id in must_pass:
        if not after.get(case_id, False):
            hold = True
    if hold:
        return ["hold", broken]
    return ["ship", broken]
""",
        cases=[
            case({"leave-03": False, "refund-07": True, "travel-12": True},
                 {"leave-03": True, "refund-07": False, "travel-12": True},
                 ["refund-07"], expected=["hold", ["refund-07"]], sample=True),
            case({"leave-03": False, "refund-07": True}, {"leave-03": True, "refund-07": True}, ["refund-07"], expected=["ship", []]),
            case({"a": True, "b": True}, {"a": True, "b": False}, [], expected=["hold", ["b"]]),
            case({"a": True}, {"a": True, "c": False}, ["c"], expected=["hold", []]),
        ],
        guided="""def release_check(before, after, must_pass):
    # Replace every ___ with real code, then run the tests.
    broken = []
    for case_id in before:
        # Step 1: passed before, fails after.
        if ___:
            broken.append(case_id)
    broken.sort()
    hold = len(broken) > 0
    # Step 2: any must-pass case failing means hold.
    for case_id in must_pass:
        if ___:
            hold = True
    if hold:
        return ["hold", broken]
    return ["ship", broken]
""",
        fills=['before[case_id] and not after.get(case_id, False)', 'not after.get(case_id, False)'],
        concepts=[
            [
                'get with a default',
                '`after.get(case_id, False)` treats a case missing from `after` as failed, so nothing slips through unchecked.',
                """after = {"a": True}
after.get("b", False)   # False""",
            ],
            [
                'and, not',
                '`before[c] and not after[c]` is True only when it passed before and fails now.',
                'True and not False   # True',
            ],
        ],
        byhand='leave-03 failed before, so it can\'t break. refund-07 passed before and fails after: broken. travel-12 passed both times. Broken: ["refund-07"]. refund-07 is a must-pass case and fails after the fix, so hold. Return ["hold", ["refund-07"]].',
        why='Each case is looked at once, then each must-pass case once.',
        gotchas=[
            [
                'Looking only at the fixed answer',
                'The answer you fixed is one case. Check every case that passed before; that is where the new damage hides.',
            ],
            [
                'Trusting the average',
                'A better average can hide a broken must-pass case. Check the must-pass list on its own.',
            ],
        ],
    ),
)
