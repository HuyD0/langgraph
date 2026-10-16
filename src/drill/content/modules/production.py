"""Production patterns: Rate limits, retries, concurrency, race conditions, idempotency and data at scale: the habits that keep AI systems up."""

from drill.content.model import angle, case, example, exercise, lesson, machine, module, question, source, stack

MODULE = module('production', 'Production patterns', 'Rate limits, retries, concurrency, race conditions, idempotency and data at scale: the habits that keep AI systems up.')

lesson(MODULE, 'token_bucket',
    title='Rate limiting before the 429',
    learn=[
        'Model endpoints limit how many requests (and tokens) you can send per minute. Hitting the limit (the server answers with error 429, "too many requests") and retrying works, but it wastes calls and adds delay for everyone.',
        'A **token bucket** keeps you under the limit on your side: a budget of tokens that refills at a steady rate, with room for a short burst. Here a token is just a permit to send one request, not a piece of text.',
    ],
    example=example('Rate 2 per second, bucket of 5', """# 5 requests at once: all go (the bucket empties)
# the 6th has no token left (a real limiter waits about half a second)"""),
    check=question(
        "Your batch job sends 200 requests at once and gets 150 rate-limit errors. What's the better fix?",
        [
            'Retry the 150 straight away, before the limit resets',
            'Pace the requests on your side to stay under the limit',
            'Run the job on a bigger cluster so it sends faster',
        ],
        answer=1,
        why='Retrying in a burst hits the same wall. Pacing the requests avoids the errors.',
    ),
    angle=angle(
        pattern='Top up, then spend one',
        text='The big idea: a token bucket keeps you under the rate limit on your side, so you avoid 429 errors. Your code remembers two numbers: how many tokens are in the bucket, and when the last request came. For each request, it adds `rate` tokens for every second since then, but never more than `bucket_size`. If at least one token is there, it spends one and marks the request `True`. Otherwise it marks it `False`. It is like a jar of tickets that slowly refills, so a full jar lets a short burst through.',
        say='"I keep a [[token bucket|request queue|retry loop::It\'s like a jar of tickets that slowly refills.]] that refills at a steady rate. Each request spends one token, so a short [[burst|delay|error::A full jar lets several through at once.]] is fine but we stay under the [[rate limit|bucket size|timeout::Go past it and the server answers with error 429.]]."',
        classic=None,
    ),
    stack=stack('LangChain: a client-side token bucket', """from langchain_core.rate_limiters import InMemoryRateLimiter
limiter = InMemoryRateLimiter(requests_per_second=2, check_every_n_seconds=0.1, max_bucket_size=5)
# LangChain's bucket starts empty: the first request waits about 0.5 s,
# and bursts only happen once it has filled up
llm = ChatDatabricks(endpoint=ENDPOINT, rate_limiter=limiter)"""),
    exercise=exercise(
        title='Rate-Limit Before the 429',
        topic='production',
        difficulty='medium',
        fn='token_bucket',
        prompt="""A **token bucket** keeps you under a rate limit, so you avoid 429 errors. Each request spends one token (a permit, not a piece of text); tokens drip back in over time.

Your function gets three things:

- `request_times`: the second each request happens, in order, like `[0, 0, 1]`.
- `rate`: how many tokens drip back in each second, like `1`.
- `bucket_size`: the most tokens the bucket can hold, like `2`. It starts full.

Before each request, add `rate` tokens for each second since the previous request (for the first request, count from second 0), but never go above `bucket_size`.

Then, if there is at least one token, spend it and send the request (`True`). If not, mark it `False` (a real limiter would wait; here you don't).

Return a list of these True/False values, one per request, in order.""",
        pattern='Keep two numbers: the tokens left and the time of the previous request. Before each request, top up for the time that passed, but never above the bucket size.',
        target='one pass over the requests',
        realworld="Sending requests until the endpoint says 429 wastes calls and slows everyone down. A client-side limiter (LangChain's `InMemoryRateLimiter` is a token bucket) keeps you under the AI Gateway's limit in the first place, while still allowing short bursts.",
        starter="""def token_bucket(request_times, rate, bucket_size):
    # your code here
    pass
""",
        solution="""def token_bucket(request_times, rate, bucket_size):
    tokens = bucket_size
    last = 0
    sent = []
    for now in request_times:
        tokens = min(bucket_size, tokens + (now - last) * rate)
        last = now
        if tokens >= 1:
            tokens = tokens - 1
            sent.append(True)
        else:
            sent.append(False)
    return sent
""",
        cases=[
            case([0, 0, 0, 1, 1], 1, 2, expected=[True, True, False, True, False], sample=True),
            case([0, 0, 0, 1, 1, 3], 1, 2, expected=[True, True, False, True, False, True]),
            case([], 5, 5, expected=[]),
            case([0, 1, 2, 3], 1, 1, expected=[True, True, True, True]),
            case([0, 0, 0, 0], 10, 3, expected=[True, True, True, False]),
            case([0, 0, 10, 10, 10], 1, 2, expected=[True, True, True, True, False]),
        ],
        guided="""def token_bucket(request_times, rate, bucket_size):
    # Replace every ___ with real code, then run the tests.

    tokens = bucket_size   # the bucket starts full
    last = 0               # time of the previous request
    sent = []
    for now in request_times:
        # Step 1: (now - last) seconds have passed.
        # Each second adds rate tokens. Add them to
        # tokens, but never go above bucket_size.
        tokens = min(bucket_size, ___)
        last = now
        # Step 2: at least one token? Spend it and send.
        if ___:
            tokens = tokens - 1
            sent.append(True)
        else:
            sent.append(False)
    return sent
""",
        fills=['tokens + (now - last) * rate', 'tokens >= 1'],
        concepts=[
            [
                'min as a cap',
                '`min(a, b)` gives the smaller of the two. So `min(limit, value)` never goes above limit.',
                """min(100, 120)   # 100
min(100, 80)    # 80""",
            ],
            [
                'Comparing numbers',
                '`a >= b` means a is at least b (greater or equal).',
                """3 >= 1   # True
0 >= 1   # False""",
            ],
            [
                'Multiplying, and brackets first',
                '`*` multiplies. Anything in brackets is worked out first.',
                """(5 - 2) * 3       # 9
10 + (5 - 2) * 3  # 19""",
            ],
        ],
        byhand='The bucket starts with 2 tokens. At second 0, the first request spends one (1 left): True. The second spends the last one: True. The third finds none: False. At second 1, one second has passed and rate is 1, so 1 token drips in. The fourth request spends it: True. The fifth finds none: False. Returns [True, True, False, True, False].',
        why='One pass over the requests, two numbers to track.',
        gotchas=[
            [
                'Limits are usually per minute and per token',
                'Model endpoints often limit text tokens (the pieces of text the model reads and writes) per minute as well as requests. Stay under whichever limit you would hit first.',
            ],
            [
                "One limiter per process isn't one limiter",
                'Ten workers each with their own bucket send ten times the rate. Shared limits need shared state, or a gateway that enforces them.',
            ],
        ],
    ),
)

lesson(MODULE, 'retry_wait',
    title='Retries done right',
    learn=[
        'Retry only errors that can succeed later (429 rate limits, 503 overload, timeouts). If the server says how long to wait (a **Retry-After** value), wait that long.',
        "Otherwise use **exponential backoff**: wait longer each time, doubling the window (1, 2, 4, 8 seconds), with **jitter**: a random wait inside that growing window, so many clients don't all retry at the same moment. Always stop after a few attempts.",
    ],
    example=example('Without and with jitter', """# 50 workers, no jitter: all retry at exactly 2 s, 4 s, 8 s → repeated collisions
# full jitter: each waits a random time up to 2 s, then up to 4 s, then up to 8 s → spread out"""),
    check=question(
        'Fifty workers hit a rate limit at the same time and all retry after exactly 2 seconds. What happens?',
        ['They all succeed, since the limit has reset', 'They all hit the limit again together', 'Only the first one to retry gets through'],
        answer=1,
        why='Identical waits make the retries collide. Jitter spreads them out.',
    ),
    angle=angle(
        pattern='Retry-After first, else backoff with jitter',
        text='The big idea: when retrying, wait as long as the server asks, and otherwise wait longer each time with jitter. Your code first checks `retry_after`, and if the server gave a wait, it returns that. Otherwise the window is `2 ** attempt` seconds, so 1, 2, 4, 8 and so on, but never more than `max_wait`. It returns `random_number` times the window, a random spot inside it. Because the random number is passed in, a test can give the same number and get the same answer every time.',
        say='"If the server says how long to wait, I wait [[that long|twice as long|a fixed time::Its Retry-After header tells you.]]. If not, I pick a [[random|fixed|short::Jitter stops every client trying again at the same moment.]] wait, and the window [[doubles|halves|stays the same::1, 2, 4, 8 seconds and so on.]] each try, up to a cap."',
        classic=None,
    ),
    stack=stack('tenacity: backoff with jitter', """from tenacity import retry, stop_after_attempt, wait_random_exponential

@retry(wait=wait_random_exponential(multiplier=1, max=30), stop=stop_after_attempt(5))
def call_model(messages):
    return llm.invoke(messages)"""),
    exercise=exercise(
        title='Retries With Jitter',
        topic='production',
        difficulty='easy',
        fn='retry_wait',
        prompt="""Work out how long to wait before retrying a rate-limited call.

You wait a random time between 0 and a limit called the **window**. The window doubles with each retry: this is **exponential backoff**. This random part, **jitter**, stops many clients retrying at the same moment.

Your function gets four things:

- `attempt`: which retry this is, counting from 0, like `3`.
- `max_wait`: the biggest the window may get, in seconds, like `30`.
- `retry_after`: the wait the server asked for, in seconds, like `7`, or `None` if it didn't say.
- `random_number`: a random number from 0 to 1, like `0.3`.

If `retry_after` is not `None`, return it. Otherwise the window is `2 ** attempt` seconds (1, 2, 4, 8...), but never more than `max_wait`. Return `random_number * window`.""",
        pattern='Prefer what the server tells you. Otherwise grow the window and pick a random point inside it.',
        target='a few simple steps, no loop',
        realworld='If 50 workers hit a limit at the same moment and all wait exactly 2 seconds, they all retry together and hit it again. Random jitter spreads them out. Passing the random number in, instead of calling `random()` inside, is a standard trick that makes code like this testable.',
        starter="""def retry_wait(attempt, max_wait, retry_after, random_number):
    # your code here
    pass
""",
        solution="""def retry_wait(attempt, max_wait, retry_after, random_number):
    if retry_after is not None:
        return retry_after
    window = min(max_wait, 2 ** attempt)
    return random_number * window
""",
        cases=[
            case(3, 30, None, 0.3, expected=2.4, sample=True),
            case(3, 30, None, 0.5, expected=4.0),
            case(0, 30, 7, 0.9, expected=7),
            case(10, 30, None, 0.25, expected=7.5),
            case(2, 10, None, 0.0, expected=0.0),
            case(1, 60, None, 1.0, expected=2.0),
            case(0, 30, None, 0.5, expected=0.5),
        ],
        guided="""def retry_wait(attempt, max_wait, retry_after, random_number):
    # Replace every ___ with real code, then run the tests.

    # Step 1: if the server said how long, wait that long.
    if retry_after is not None:
        return ___
    # Step 2: the window is 2 ** attempt seconds,
    # but never more than max_wait.
    window = min(max_wait, ___)
    # Step 3: wait a random part of the window.
    return random_number * window
""",
        fills=['retry_after', '2 ** attempt'],
        concepts=[
            [
                'Powers with **',
                '`2 ** 3` means 2 multiplied by itself 3 times, which is 8.',
                """2 ** 3   # 8
2 ** 0   # 1""",
            ],
            [
                'is not None',
                '`None` means "no value". `x is not None` is True when a real value was given.',
                """answer = None
answer is not None   # False""",
            ],
            [
                'min as a cap',
                '`min(a, b)` gives the smaller of the two. So `min(limit, value)` never goes above limit.',
                'min(100, 120)   # 100',
            ],
        ],
        byhand='retry_after is None, so work out the window. Attempt 3: 2 ** 3 is 8 seconds. 8 is less than max_wait (30), so the window stays 8. Then random_number times the window: 0.3 times 8 is 2.4. Returns 2.4.',
        why='A few steps, however many retries.',
        gotchas=[
            [
                'Only retry what can succeed later',
                '429 and 503 are worth retrying. 400 and 401 will fail the same way every time.',
            ],
            [
                'Cap the total, not just each wait',
                "Also stop after a few attempts or a total time limit, so a user isn't left waiting minutes.",
            ],
        ],
    ),
)

lesson(MODULE, 'run_with_limit',
    title='Many calls at once',
    learn=[
        'Calling a model is mostly waiting. Running calls **concurrently** (several in flight at once) finishes a batch far sooner than one at a time.',
        'But unlimited concurrency triggers rate limits and overloads services. Use a **concurrency limit**: a **semaphore** (a counter of free places that each call must take before it starts) lets at most a set number (say 8) run at once, and the next starts the moment one finishes.',
    ],
    example=example('100 calls of 2 seconds each', """# one at a time:   200 seconds
# 10 at a time:     20 seconds
# all 100 at once:  2 seconds, if nothing pushes back (it will)"""),
    check=question(
        "You wrap 1,000 LLM calls in `asyncio.gather` (Python's way to start many calls together) with no limit. What's the likely result?",
        [
            'Fastest possible run',
            'A flood of rate-limit errors and timeouts',
            'Python runs them one at a time',
        ],
        answer=1,
        why="All 1,000 start at once. Add a semaphore or LangChain's max_concurrency setting.",
    ),
    angle=angle(
        pattern='Give each call the first free slot',
        text="The big idea: running several calls at once finishes sooner, but a cap stops you from hitting rate limits. Your code keeps a list of slots, each holding the time that slot becomes free, all starting at 0. For each call, it sorts the slots so the one free soonest comes first, then adds the call's time to it. It is like a shop with a few tills, where each new customer goes to the till that frees up first. At the end, the latest slot time is when every call has finished.",
        say='"I cap how many calls run [[at once|in total|per day::Think of a shop with only a few tills.]]. When one finishes, the next one [[takes its place|waits a minute|starts over::The till that frees up first serves the next customer.]], so the batch is quick without hitting [[rate limits|memory limits|time limits::Too many calls together and the server starts saying 429.]]."',
        classic=None,
    ),
    stack=stack('asyncio and LangChain: cap calls in flight', """sem = asyncio.Semaphore(8)

async def ask(question):
    async with sem:
        return await llm.ainvoke(question)

answers = await asyncio.gather(*(ask(q) for q in questions))
# or: llm.batch(questions, config={"max_concurrency": 8})"""),
    exercise=exercise(
        title='Many Calls, a Few at a Time',
        topic='production',
        difficulty='medium',
        fn='run_with_limit',
        prompt="""You need to make several LLM calls, but only a few may run at the same time.

Your function gets two things:

- `durations`: how long each call takes, in seconds, like `[3, 1, 2]`.
- `limit`: the most calls that may run at once, like `2`.

Think of `limit` **slots**, one for each call that can run at once. Calls start in list order. The first `limit` calls start at time 0. Each time a call finishes, the next waiting call takes its slot at that moment.

Return the time when every call has finished. That is the latest finish time, which is not always the last call in the list. With no calls, return `0`.""",
        pattern='Keep one "free at" time per slot. Each call goes into the slot that is free first.',
        target='one step per call',
        realworld="This is what `asyncio.Semaphore`, a thread pool's `max_workers` (a thread pool is a fixed group of workers that take calls in turn) and LangChain's `max_concurrency` do. Unlimited concurrency triggers rate limits; one at a time is slow. A cap gets most of the speed without the 429s.",
        starter="""def run_with_limit(durations, limit):
    # your code here
    pass
""",
        solution="""def run_with_limit(durations, limit):
    slots = [0] * limit
    for duration in durations:
        slots.sort()
        slots[0] = slots[0] + duration
    return max(slots)
""",
        cases=[
            case([3, 1, 2, 4], 2, expected=7, sample=True),
            case([], 3, expected=0),
            case([5, 5, 5], 3, expected=5),
            case([2, 2, 2], 1, expected=6),
            case([4, 1, 1, 1], 2, expected=4),
            case([3, 1], 5, expected=3),
        ],
        guided="""def run_with_limit(durations, limit):
    # Replace every ___ with real code, then run the tests.

    # One number per slot (limit of them): the time
    # that slot is next free. Every slot is free at 0.
    slots = [0] * limit
    for duration in durations:
        # Step 1: put the slot that is free first
        # at the front.
        slots.sort()
        # Step 2: the call starts when that slot is free,
        # and keeps it busy for duration more seconds.
        slots[0] = ___
    # Step 3: all calls are done when the busiest slot
    # is free: the biggest number in slots.
    return ___
""",
        fills=['slots[0] + duration', 'max(slots)'],
        concepts=[
            [
                'A list of zeros',
                '`[0] * 3` makes a list holding three zeros.',
                'counts = [0] * 3   # [0, 0, 0]',
            ],
            [
                'Sorting in place',
                '`items.sort()` puts a list in order, smallest first. It changes the list itself.',
                """ages = [40, 7, 19]
ages.sort()  # [7, 19, 40]""",
            ],
            [
                'The first item',
                '`items[0]` is the first item. `items[0] = x` replaces it.',
                """ages = [7, 19]
ages[0] = ages[0] + 1  # [8, 19]""",
            ],
            [
                'max of a list',
                '`max(items)` gives the biggest item.',
                'max([4, 9, 2])   # 9',
            ],
        ],
        byhand='Limit 2, so two slots, both free at 0. At 0, the 3-second call and the 1-second call start, one in each slot. At 1, the 1-second call finishes, so the 2-second call takes its slot; it ends at 3. At 3, both slots are free, so the 4-second call starts; it ends at 7. In the code: slots start [0, 0]. 3-second call: [3, 0]. Sort: [0, 3]; 1-second call: [1, 3]. 2-second call: [3, 3]. 4-second call: [7, 3]. The biggest is 7. Returns 7.',
        why='Each call is placed once. Sorting the few slots each time is fine for a small limit; a heap (a structure that always hands back the smallest number quickly) is faster when the limit is large.',
        gotchas=[
            [
                'gather without a limit',
                '`asyncio.gather` on 1,000 calls starts all 1,000 at once. Wrap each call in a semaphore.',
            ],
            [
                'One slow call holds a slot',
                "Give every call a timeout, so a stuck request doesn't quietly cut your throughput (how many calls finish per minute).",
            ],
        ],
    ),
)

lesson(MODULE, 'optimistic_writes',
    title='Race conditions',
    learn=[
        'A **race condition** happens when the result depends on timing. The classic one: two workers read the same record, both change it, both save, and the first change is silently lost.',
        '**Optimistic concurrency** prevents this: each write says which version it read, and is rejected if the record changed since. The loser re-reads and tries again.',
    ],
    example=example('A lost update', """# the record also stores a version number, 7, that goes up on every save
# worker A reads count = 10, worker B reads count = 10
# A saves 11, B saves 11  →  one increment is lost
# with versions: B's write says "I read version 7", but it's now 8 → rejected, B retries"""),
    check=question(
        'Two agents update the same ticket at nearly the same time. Which approach avoids losing one update?',
        [
            'Read the ticket, change it in Python, then write it back',
            'Write only if the version is still the one you read',
            'Add a short sleep before each write so they take turns',
        ],
        answer=1,
        why='The check has to happen as part of the write. A sleep only makes the race rarer.',
    ),
    angle=angle(
        pattern='Accept only up-to-date writes',
        text="The big idea: each write says which version it read, so a write based on old data is rejected instead of silently erasing someone else's change. Your code goes through the writes in the order they arrive, using a loop: a block of code that runs once for each item. If a write read the record's current version, it is accepted and the version goes up by 1. Otherwise it is rejected. It is like a shared document: if someone saved after you opened it, you must reopen it before you save.",
        say='"Each write says which [[version|user|time::It goes up by 1 every time someone saves.]] it read. If someone saved since then, the write is [[rejected|merged|queued::Like a shared doc: if it changed, you must reopen it first.]], so they re-read and try again instead of [[overwriting|deleting|copying::The danger is silently erasing someone else\'s change.]] it."',
        classic=None,
    ),
    stack=stack('SQL: a version-checked update', """UPDATE tickets
SET status = 'closed', version = version + 1
WHERE ticket_id = 'T2' AND version = 7;
-- 0 rows updated means someone else changed it first: re-read and retry"""),
    exercise=exercise(
        title='Two Writers, One Record',
        topic='production',
        difficulty='easy',
        fn='optimistic_writes',
        prompt="""**Optimistic concurrency** stops two writers from erasing each other's changes. Each write says which version of the record its writer read. It is accepted only if the record is still at that version.

Your function gets two things:

- `version`: the record's version number at the start, like `3`.
- `read_versions`: for each write, in the order they arrive, the version its writer read, like `[3, 3, 4]`.

Go through the writes in order. If the version a write read equals the record's current version, accept it and add 1 to the version. Otherwise reject it. Return a list with `True` (accepted) or `False` (rejected) for each write, in order.""",
        pattern='Compare-and-set: change only if the value is still what you saw.',
        target='one pass over the writes',
        realworld="Delta Lake commits work this way: if another job committed a conflicting change first, your commit fails and you retry. It's also how version-checked updates and HTTP ETags stop two writers from clobbering each other. Terraform state locking solves the same problem the other way round, by holding a lock until the run finishes.",
        starter="""def optimistic_writes(version, read_versions):
    # your code here
    pass
""",
        solution="""def optimistic_writes(version, read_versions):
    results = []
    for read in read_versions:
        if read == version:
            results.append(True)
            version = version + 1
        else:
            results.append(False)
    return results
""",
        cases=[
            case(3, [3, 3, 4], expected=[True, False, True], sample=True),
            case(1, [], expected=[]),
            case(0, [1], expected=[False]),
            case(7, [7, 8, 9], expected=[True, True, True]),
            case(5, [5, 5, 5], expected=[True, False, False]),
            case(2, [1, 2, 2, 3], expected=[False, True, False, True]),
        ],
        guided="""def optimistic_writes(version, read_versions):
    # Replace every ___ with real code, then run the tests.

    results = []
    for read in read_versions:
        # Step 1: is the record still at the version
        # this writer read?
        if ___:
            results.append(True)
            # Step 2: an accepted write adds 1 to
            # the version.
            ___
        else:
            results.append(False)
    return results
""",
        fills=['read == version', 'version = version + 1'],
        concepts=[
            [
                '== and =',
                '`a == b` asks "are these equal?" and gives True or False. `a = b` stores a value in a name.',
                """size = 4
size == 4   # True""",
            ],
            [
                'Adding one',
                '`n = n + 1` makes n one bigger.',
                """count = 7
count = count + 1   # count is now 8""",
            ],
        ],
        byhand='The record starts at version 3. Write 1 read version 3: that matches, so True, and the record moves to version 4. Write 2 also read 3, but the record is now at 4: False. Write 3 read 4 (its writer re-read after being rejected): that matches, so True, and the record moves to 5. Returns [True, False, True].',
        why='One pass over the writes.',
        gotchas=[
            [
                'Check-then-act is the bug',
                "Reading, deciding in Python, then writing is two steps, and another writer can act in between. The check must happen inside the write itself, for example in the database's WHERE clause.",
            ],
            [
                'Retries need a fresh read',
                'A rejected writer must re-read the latest version and redo its change, not resend the old one.',
            ],
        ],
    ),
)

lesson(MODULE, 'upsert_rows',
    title='Idempotent writes',
    learn=[
        'Jobs get retried: a cluster dies, a notebook is re-run, a scheduler fires twice. **Idempotent** means running it twice leaves the same result as running it once.',
        "Appending rows is not idempotent; each retry duplicates them. **Upsert** on a stable key (a field that names the row and never changes, like a ticket id) is: matching rows are updated, new ones inserted. In Delta this is `MERGE INTO`.",
    ],
    example=example('Append vs merge on retry', """# run 1 appends 3 rows, crash, run 2 appends them again → 6 rows
# run 1 merges 3 rows, crash, run 2 merges again       → still 3 rows"""),
    check=question(
        'A nightly job that writes eval results crashed halfway and was re-run. The table now has duplicate rows. What prevents this?',
        ['Run it less often', 'Write with MERGE on a stable key', 'Delete the table before each run'],
        answer=1,
        why='MERGE makes the write idempotent. Deleting first leaves a window where the table is empty.',
    ),
    angle=angle(
        pattern='Remember where each row is',
        text="The big idea: saving rows by a stable key means a retried job replaces rows instead of adding duplicates. Your code first builds a dict, a lookup table, from each row's key to its position in the table. Then for each update it asks: is this key already in the table? If yes, the update replaces the row in that spot. If no, it goes on the end. The dict works like a book's index: you jump straight to the right page instead of reading every row.",
        say='"I save rows by a [[stable key|row number|timestamp::Something that stays the same every time the job runs.]]. If the key is already there I [[replace|skip|duplicate::A retried job should not leave two copies.]] that row, otherwise I add it. So running the same batch [[twice|once|in order::Think about a job that gets retried.]] changes nothing."',
        classic='two_sum',
    ),
    stack=stack('Delta Lake: MERGE INTO', """MERGE INTO main.support.eval_results AS t
USING new_results AS s
ON t.run_id = s.run_id AND t.example_id = s.example_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *"""),
    exercise=exercise(
        title='Safe to Run Twice',
        topic='production',
        difficulty='medium',
        fn='upsert_rows',
        prompt="""An **upsert** saves a row by its key: if a row with that key is already there, replace it; if not, add it. Saving the same rows twice then changes nothing, so a retried job can't create duplicates.

Your function gets three things:

- `table`: the rows already saved, a list of dicts like `{"id": "T1", "status": "open"}`.
- `updates`: the rows to save, in the same shape.
- `key`: the name of the field that identifies a row, like `"id"`.

Return the new table. If a saved row has the same value for `key` as an update (for example the same id), the update replaces that row, in the same place. Otherwise the update goes on the end, in the order given.""",
        pattern="Make a dict from each key to its row's position. Then each update either replaces the row at that position or goes on the end.",
        target='one pass over the table, then one over the updates',
        realworld="This is Delta Lake's `MERGE INTO`. Writing results with MERGE on a stable key, instead of appending, means a retried job or a re-run notebook leaves the table exactly as one run would. That property is called idempotency.",
        starter="""def upsert_rows(table, updates, key):
    # your code here
    pass
""",
        solution="""def upsert_rows(table, updates, key):
    result = []
    position = {}
    for row in table:
        position[row[key]] = len(result)
        result.append(row)
    for row in updates:
        if row[key] in position:
            result[position[row[key]]] = row
        else:
            result.append(row)
    return result
""",
        cases=[
            case([{'id': 'T1', 'status': 'open'}, {'id': 'T2', 'status': 'open'}], [{'id': 'T2', 'status': 'closed'}, {'id': 'T3', 'status': 'open'}], 'id', expected=[
                {'id': 'T1', 'status': 'open'},
                {'id': 'T2', 'status': 'closed'},
                {'id': 'T3', 'status': 'open'},
            ], sample=True),
            case([], [], 'id', expected=[]),
            case([{'id': 1, 'v': 'a'}], [{'id': 1, 'v': 'a'}], 'id', expected=[{'id': 1, 'v': 'a'}]),
            case([], [{'id': 5, 'v': 'x'}], 'id', expected=[{'id': 5, 'v': 'x'}]),
            case([{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'b'}], [{'id': 1, 'v': 'z'}], 'id', expected=[{'id': 1, 'v': 'z'}, {'id': 2, 'v': 'b'}]),
            case([{'run': 'r1', 'score': 0.5}], [{'run': 'r2', 'score': 0.9}, {'run': 'r1', 'score': 0.7}], 'run', expected=[{'run': 'r1', 'score': 0.7}, {'run': 'r2', 'score': 0.9}]),
        ],
        guided="""def upsert_rows(table, updates, key):
    # Replace every ___ with real code, then run the tests.

    result = []
    position = {}   # key value -> where that row sits
    # Step 1: copy the saved rows, noting where each sits.
    for row in table:
        position[row[key]] = len(result)
        result.append(row)
    for row in updates:
        if row[key] in position:
            # Step 2: key already there: look up where it
            # sits in position, and replace the row there.
            result[___] = row
        else:
            # Step 3: new key: add the row on the end.
            ___
    return result
""",
        fills=['position[row[key]]', 'result.append(row)'],
        concepts=[
            [
                'A field name in a variable',
                "`row['id']` gets one field. `row[key]` does the same when the field name is stored in `key`.",
                """pet = {'name': 'Rex'}
field = 'name'
pet[field]   # 'Rex'""",
            ],
            [
                'len before append',
                '`len(items)` is the position the next appended item will get, because positions start at 0.',
                """names = ['ann', 'bo']
len(names)   # 2, the next position""",
            ],
            [
                'A dict from key to position',
                '`d[k] = v` adds a key (or changes it). `k in d` is True when the dict has that key. Use a dict to remember where each item sits.',
                """spot = {}
spot['bo'] = 1   # add a key
'bo' in spot     # True
spot['bo']       # 1, where bo sits""",
            ],
            [
                'Replacing a list item',
                '`items[i] = x` puts x at position i, replacing what was there.',
                """names = ['ann', 'bo']
names[1] = 'cy'  # ['ann', 'cy']""",
            ],
        ],
        byhand='The key is id. The saved table has T1 at position 0 and T2 at position 1. The first update is T2: T2 is already there, so it replaces position 1, and T2 is now closed. The second update is T3: it is new, so it goes on the end. Returns T1 open, T2 closed, T3 open.',
        why='One pass to note where each row sits, one through the updates; each lookup is instant.',
        gotchas=[
            [
                'Appending is not idempotent',
                "INSERT on retry doubles your rows. MERGE (or overwrite by partition) on a stable key doesn't.",
            ],
            [
                'Duplicate keys in the source',
                "If one batch has the same key twice, MERGE fails when that key is already in the table, and quietly inserts both rows when it isn't. Remove duplicates in the source first.",
            ],
        ],
    ),
)

lesson(MODULE, 'chunk_rows',
    title='Transforming data at scale with Spark',
    learn=[
        "Spark splits a table into **partitions** and works on them in parallel across the cluster. A function you write for Spark to run on the rows (a **UDF**) must get each row's answer from that row alone: not from other rows, and not from **shared state** (a value kept outside the function), because Spark may run it on any machine and more than once. Grouping and joining rows is Spark's own job: ask for a groupBy or a join and Spark brings the matching rows together for you.",
        'Give every output a **deterministic id** (a stable id built only from its inputs), so re-running the job produces the same ids and a MERGE overwrites instead of duplicating.',
    ],
    example=example('One document becomes many chunk rows', """id  text                  →  id    text
d1  "abcdefg" (size 3)       d1-0  abc
                             d1-1  def
                             d1-2  g"""),
    check=question(
        'Your chunking job uses `uuid4()` (which makes a new random id each call) for chunk ids and is re-run after a failure. What happens?',
        [
            'Nothing changes: the re-run overwrites the old rows',
            'Every chunk gets a new id and is added again',
            'Spark looks up and reuses the ids from the first run',
        ],
        answer=1,
        why='Random ids differ every run, so nothing matches the old rows and the index fills with duplicates. Ids built from the data are the same every time.',
    ),
    angle=angle(
        pattern='Cut each document on its own',
        text='The big idea: a function you give Spark to run on the rows must get each row\'s answer from that row alone, so Spark can run it on any machine. Your code takes one document at a time and cuts its text into slices of `size` characters. `range(0, len(text), size)` counts 0, 3, 6 and so on when size is 3, and the last slice can be shorter. Each chunk gets an id made from the document\'s id and a count that restarts at 0, like `"d1-0"`. So a re-run gives the same ids, and a MERGE overwrites instead of duplicating.',
        say='"My function only looks at [[one document|every document|the whole table::Spark can only split the work if each piece stands alone.]] at a time, so Spark can spread the work across machines. Each chunk id comes from the [[document\'s id|current time|a random number::Like d1-0: built from data that never changes.]], so a re-run gives the [[same ids|new ids|more rows::Then a MERGE overwrites instead of duplicating.]]."',
        classic=None,
    ),
    stack=stack('PySpark: a pandas UDF plus posexplode', """import pandas as pd   # pandas holds each batch of rows the UDF gets
from pyspark.sql import functions as F, types as T

# a UDF is a function you write that Spark runs on the rows
@F.pandas_udf(T.ArrayType(T.StringType()))
def split_text(texts: pd.Series) -> pd.Series:
    return texts.fillna("").map(lambda t: [t[i:i + 1000] for i in range(0, len(t), 1000)])

# posexplode turns each list into one row per item, plus its position
chunks = (spark.table("main.support.docs")
    .select("doc_id", F.posexplode(split_text("text")).alias("i", "text"))
    .withColumn("chunk_id", F.concat_ws("-", "doc_id", "i")))"""),
    checked='2026-10-15',
    sources=[source('Databricks: pandas user-defined functions', 'https://docs.databricks.com/aws/en/udf/pandas')],
    exercise=exercise(
        title='Chunking at Scale',
        topic='production',
        difficulty='easy',
        fn='chunk_rows',
        prompt="""Spark runs one small function on every row, spread over many machines. So that function may only use its own row. Your function cuts each document into chunks, looking at one document at a time.

Your function gets two things:

- `docs`: a list of documents, each a dict like `{"id": "d1", "text": "abcdefg"}`.
- `size`: how many characters go in each chunk, like `3`.

Cut each text into chunks of `size` characters, from the start. The last chunk may be shorter. Each chunk becomes a row like `{"id": "d1-0", "text": "abc"}`. Its id is the document's id, a dash, and the chunk number, counting from 0 in each document: `"d1-0"`, `"d1-1"`. Return all the rows in order. Empty text gives no rows.""",
        pattern='Turn each input row into zero or more output rows, using only that row. Build every id from the data, so it is the same on every run.',
        target='one step per chunk',
        realworld='In Spark this is a UDF (a function you write that Spark runs on the rows) plus `posexplode`, or `mapInPandas`. Because each row is handled on its own, Spark can split the work across the cluster. Ids like `d1-0` are built from the data, so re-running the job produces the same ids and a MERGE overwrites instead of duplicating.',
        starter="""def chunk_rows(docs, size):
    # your code here
    pass
""",
        solution="""def chunk_rows(docs, size):
    rows = []
    for doc in docs:
        text = doc["text"]
        number = 0
        for start in range(0, len(text), size):
            chunk = text[start:start + size]
            chunk_id = doc["id"] + "-" + str(number)
            rows.append({"id": chunk_id, "text": chunk})
            number = number + 1
    return rows
""",
        cases=[
            case([{'id': 'd1', 'text': 'abcdefg'}, {'id': 'd2', 'text': 'xy'}], 3, expected=[
                {'id': 'd1-0', 'text': 'abc'},
                {'id': 'd1-1', 'text': 'def'},
                {'id': 'd1-2', 'text': 'g'},
                {'id': 'd2-0', 'text': 'xy'},
            ], sample=True),
            case([], 5, expected=[]),
            case([{'id': 'e', 'text': ''}], 4, expected=[]),
            case([{'id': 'a', 'text': 'abcd'}], 4, expected=[{'id': 'a-0', 'text': 'abcd'}]),
            case([{'id': 'k', 'text': 'hello'}], 2, expected=[
                {'id': 'k-0', 'text': 'he'},
                {'id': 'k-1', 'text': 'll'},
                {'id': 'k-2', 'text': 'o'},
            ]),
        ],
        guided="""def chunk_rows(docs, size):
    # Replace every ___ with real code, then run the tests.

    rows = []
    for doc in docs:
        text = doc["text"]
        number = 0   # chunk number, from 0 in each doc
        # Step 1: start at 0 and jump forward size
        # characters each time.
        for start in range(0, len(text), ___):
            chunk = text[start:start + size]
            # Step 2: the doc id, a dash, the chunk number.
            chunk_id = ___
            rows.append({"id": chunk_id, "text": chunk})
            number = number + 1
    return rows
""",
        fills=['size', 'doc["id"] + "-" + str(number)'],
        concepts=[
            [
                'range with a step',
                '`range(start, stop, step)` counts from start, jumping by step, and stops before stop.',
                'list(range(0, 10, 4))   # [0, 4, 8]',
            ],
            [
                'Slicing text',
                '`text[a:b]` is the characters from position a up to, but not including, b. Running past the end just stops at the end.',
                """'hello'[0:2]   # 'he'
'hello'[4:6]   # 'o'""",
            ],
            [
                'Joining text and a number',
                '`str(n)` turns a number into text, so `+` can join it to other text.',
                "'page' + '-' + str(2)   # 'page-2'",
            ],
        ],
        byhand='Size 3. d1 is "abcdefg", so chunks start at positions 0, 3 and 6. "abc" is d1-0, "def" is d1-1, and "g" is d1-2 (shorter, because the text ran out). d2 is "xy": one chunk, d2-0, because the count starts again at 0. Returns those four rows, in that order.',
        why='One step per chunk, and every document is handled on its own, which is what lets Spark spread it out.',
        gotchas=[
            [
                'Random ids break re-runs',
                'uuid4() gives new ids every run, so a re-run duplicates every chunk. Build ids from the data.',
            ],
            [
                'Python UDFs are slow row by row',
                'Prefer built-in Spark functions; when you need Python, a pandas UDF processes a batch of rows at a time and is much faster.',
            ],
        ],
    ),
)

lesson(MODULE, 'process_new',
    title='Incremental processing',
    learn=[
        "Reprocessing a whole table every night gets slow and expensive as it grows. Incremental jobs remember where they got to (an **offset** in a **checkpoint**) and process only what's new.",
        'Events can arrive late. A **watermark** decides how late is too late to count.',
    ],
    example=example('Only the new events', """saved offset: 1 → read events 2, 3, 4
watermark: time 100 → event 3 (time 90) is too late"""),
    check=question(
        "Your nightly embedding job re-embeds all 10 million documents every run. What's the fix?",
        [
            'A bigger cluster, so the full run finishes sooner',
            'Checkpoint where it got to and process only what is new',
            'Run it weekly instead of nightly to cut the cost',
        ],
        answer=1,
        why='Incremental processing makes cost follow what changed, not what exists. A bigger cluster or a rarer run still re-embeds every document.',
    ),
    angle=angle(
        pattern='Skip what you have already read',
        text="The big idea: an incremental job remembers where it stopped, so each run handles only new events instead of the whole table. Your code goes through the events and skips any whose offset is not past `saved_offset`. For each new event it moves `new_offset` forward, even if the event is late, so the next run won't read it again. It keeps the value only if the event's time is at least the `watermark`. It is like a bookmark: you start reading where you left off.",
        say='"I save the [[offset|time|count::It works like a bookmark in the stream of events.]] of the last event I read, and next run I only handle events [[after it|before it|near it::You start reading where you left off.]]. A [[watermark|checkpoint|schema::A cut-off time: events older than it are dropped.]] decides which late events are too late to count."',
        classic=None,
    ),
    stack=stack('Structured Streaming: checkpoint, watermark, run as a batch', """(spark.readStream.table("main.support.events")
    .withWatermark("event_time", "1 hour")
    # the watermark lets Spark forget ids older than an hour, so late copies are dropped
    .dropDuplicates(["event_id", "event_time"])
    .writeStream
    .option("checkpointLocation", "/Volumes/main/support/checkpoints/events")
    .trigger(availableNow=True)
    .toTable("main.support.events_clean"))"""),
    exercise=exercise(
        title="Process Only What's New",
        topic='production',
        difficulty='medium',
        fn='process_new',
        prompt="""An incremental job only handles new events. It saves an **offset**: the number of the last event it read. It also skips late events: those whose time is before the **watermark**.

Your function gets three things:

- `events`: the event log, in offset order. Each event is `[offset, time, value]`, like `[2, 105, "b"]`.
- `saved_offset`: the offset saved after the last run, like `1`.
- `watermark`: the earliest time that still counts, like `100`.

An event is new if its offset is greater than `saved_offset`. Keep the value of each new event whose time is at least `watermark`. Return `[kept_values, new_offset]`. `new_offset` is the offset of the last new event, late or not, or `saved_offset` if nothing was new.""",
        pattern="Remember where you got to; resume from there; decide what's too late.",
        target='one pass over the events',
        realworld="This is what Structured Streaming's `checkpointLocation` (the saved offset) and `withWatermark` (how long aggregations, like counts and sums, and duplicate removal wait for late data; in Spark it moves: the latest time seen minus the delay) do. With `trigger(availableNow=True)` the same job runs as a cheap batch that only processes new data each time.",
        starter="""def process_new(events, saved_offset, watermark):
    # your code here
    pass
""",
        solution="""def process_new(events, saved_offset, watermark):
    kept = []
    new_offset = saved_offset
    for offset, time, value in events:
        if offset > saved_offset:
            new_offset = offset
            if time >= watermark:
                kept.append(value)
    return [kept, new_offset]
""",
        cases=[
            case([[1, 100, 'a'], [2, 105, 'b'], [3, 90, 'c'], [4, 120, 'd']], 1, 100, expected=[['b', 'd'], 4], sample=True),
            case([], 7, 0, expected=[[], 7]),
            case([[1, 5, 'x']], 3, 0, expected=[[], 3]),
            case([[5, 50, 'p'], [6, 49, 'q']], 4, 50, expected=[['p'], 6]),
            case([[1, 10, 'a'], [2, 20, 'b']], 0, 0, expected=[['a', 'b'], 2]),
            case([[3, 80, 'x'], [4, 70, 'y']], 2, 100, expected=[[], 4]),
        ],
        guided="""def process_new(events, saved_offset, watermark):
    # Replace every ___ with real code, then run the tests.

    kept = []
    # new_offset stays put if nothing is new.
    new_offset = saved_offset
    for offset, time, value in events:
        # Step 1: only events after saved_offset are new.
        if ___:
            new_offset = offset
            # Step 2: keep it if its time is at least
            # watermark.
            if ___:
                kept.append(value)
    return [kept, new_offset]
""",
        fills=['offset > saved_offset', 'time >= watermark'],
        concepts=[
            [
                'Three names in a for loop',
                'When each item is a list of three, `for a, b, c in items` gives each part its own name.',
                """people = [['Ann', 31, 'Oslo']]
for name, age, city in people:
    print(city)   # Oslo""",
            ],
            [
                'Comparing numbers',
                '`a > b` means a is greater than b. `a >= b` means a is at least b (greater or equal).',
                """105 >= 100   # True
100 > 100    # False""",
            ],
        ],
        byhand='Saved offset 1, watermark 100. Event 1 is not after offset 1, so skip it. Event 2 is new, and time 105 is at least 100: keep "b". Event 3 is new, but time 90 is before 100, so it is too late: skip "c". Event 4 is new, time 120: keep "d". The last new event was offset 4. Returns [["b", "d"], 4].',
        why='One pass over the events.',
        gotchas=[
            [
                'Never delete the checkpoint casually',
                "Deleting a stream's checkpoint makes it reprocess everything from the start, or skip data, depending on settings.",
            ],
            [
                'Late data is a business decision',
                'How late is too late? An hour for dashboards, never for billing. Pick the watermark with the people who use the data.',
            ],
        ],
    ),
)

lesson(MODULE, 'validate_rows',
    title='Data contracts',
    learn=[
        'Pipelines break when data changes shape: a number arrives as text, a column disappears, a new one appears.',
        'Check rows against a **contract** (the agreed list of columns each row must have, and the **data type**, or kind of value, that goes in each), quarantine the bad ones (set them aside to look at later) instead of failing the whole load, and decide on purpose whether new columns are allowed in (**schema evolution**).',
    ],
    example=example('Good, quarantined, new columns', 'A1 {minutes: 12}       → good\nA2 {minutes: "twelve"} → quarantine\nA3 {..., channel}      → good; "channel" is a new column'),
    check=question(
        "One malformed row in a million breaks your nightly load. What's the better design?",
        ['Fail the whole load until someone fixes the row', 'Quarantine bad rows, load the rest, and alert', 'Drop the bad row quietly and load the rest'],
        answer=1,
        why='Keep data flowing, but make bad rows visible.',
    ),
    angle=angle(
        pattern='Check every column, then sort the row',
        text='The big idea: a row that breaks the contract goes to quarantine, so one bad row doesn\'t stop the whole load. Your code checks each row against every column in `schema`. If a column is missing, or its value is the wrong kind, the row is marked bad. A small helper, `kind_of`, names each value\'s kind: a string is "text", and an int or float is "number". Good and bad rows go into two lists, like sorting mail into keep and check-later piles. Extra columns are never looked at, so they are allowed.',
        say='"I check each row against the [[contract|last row|sample::It lists every column and the kind of value it must hold.]]. Bad rows go to [[quarantine|the bin|the log::A check-later pile, so one bad row doesn\'t stop the load.]] instead of failing the whole load. I decide on purpose that [[extra columns|missing columns|wrong types::The code never looks at columns beyond the schema.]] are allowed."',
        classic=None,
    ),
    stack=stack('Lakeflow pipelines: expectations plus a quarantine table', """-- DROP ROW throws a bad row away and only counts it in the event log
CREATE OR REFRESH STREAMING TABLE tickets_clean (
  CONSTRAINT valid_id EXPECT (ticket_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_minutes EXPECT (minutes >= 0) ON VIOLATION DROP ROW
) AS SELECT * FROM STREAM(main.support.tickets_raw);

-- quarantine: a second table keeps the rows that break the rules
CREATE OR REFRESH STREAMING TABLE tickets_quarantine
AS SELECT * FROM STREAM(main.support.tickets_raw)
WHERE ticket_id IS NULL OR minutes < 0;"""),
    exercise=exercise(
        title='Data Contracts',
        topic='production',
        difficulty='medium',
        fn='validate_rows',
        machine=machine(bins=['good', 'bad'], who=['rows that keep the contract', 'rows for quarantine'], label_field='id'),
        prompt="""A **data contract** says which columns each row needs, and what kind of value each one holds. Rows that break it go to **quarantine** (set aside to look at later) instead of stopping the whole job.

Your function gets two things:

- `rows`: the rows to load, each a dict like `{"id": "T1", "minutes": 12}`. Each key is a column.
- `schema`: the contract, a dict from column name to `"text"` or `"number"`, like `{"id": "text", "minutes": "number"}`.

A row is good if it has every column in `schema`, each holding the right kind of value: a string for `"text"`, a whole number (int) or a decimal (float) for `"number"`. Extra columns are fine. Return `[good_rows, quarantined_rows]`, each in the original order.""",
        pattern='Check each row against the contract. Set failures aside instead of crashing.',
        target='one pass over the rows',
        realworld="Lakeflow pipeline expectations check the rules, but `ON VIOLATION DROP ROW` throws a bad row away and only counts it, so to quarantine you add a second table that keeps the rows that break the rules. Delta's `mergeSchema` decides whether new columns are allowed in. Quarantining bad rows keeps one malformed record from stopping the whole pipeline.",
        starter="""def validate_rows(rows, schema):
    # your code here
    pass
""",
        solution="""def validate_rows(rows, schema):
    good = []
    bad = []
    for row in rows:
        ok = True
        for column in schema:
            if column not in row:
                ok = False
            elif kind_of(row[column]) != schema[column]:
                ok = False
        if ok:
            good.append(row)
        else:
            bad.append(row)
    return [good, bad]


def kind_of(value):
    if type(value) == str:
        return "text"
    if type(value) == int or type(value) == float:
        return "number"
    return "other"
""",
        cases=[
            case([
                {'id': 'T1', 'minutes': 12},
                {'id': 'T2', 'minutes': 'ten'},
                {'id': 'T3'},
                {'id': 'T4', 'minutes': 7.5},
            ], {'id': 'text', 'minutes': 'number'}, expected=[
                [{'id': 'T1', 'minutes': 12}, {'id': 'T4', 'minutes': 7.5}],
                [{'id': 'T2', 'minutes': 'ten'}, {'id': 'T3'}],
            ], sample=True),
            case([], {'a': 'number'}, expected=[[], []]),
            case([{'b': 1}], {'a': 'number'}, expected=[[], [{'b': 1}]]),
            case([{'name': 'x', 'extra': 5}], {'name': 'text'}, expected=[[{'name': 'x', 'extra': 5}], []]),
            case([{'id': 7}], {'id': 'text'}, expected=[[], [{'id': 7}]]),
            case([
                {'ticket': 'T1', 'minutes': 12, 'score': 0.9},
                {'ticket': 'T2', 'minutes': 'twelve', 'score': 0.8},
                {'ticket': 'T3', 'minutes': 5, 'score': 1, 'channel': 'chat'},
            ], {'ticket': 'text', 'minutes': 'number', 'score': 'number'}, expected=[
                [
                    {'ticket': 'T1', 'minutes': 12, 'score': 0.9},
                    {'ticket': 'T3', 'minutes': 5, 'score': 1, 'channel': 'chat'},
                ],
                [{'ticket': 'T2', 'minutes': 'twelve', 'score': 0.8}],
            ]),
        ],
        guided="""def validate_rows(rows, schema):
    # Replace every ___ with real code, then run the tests.

    good = []
    bad = []
    for row in rows:
        ok = True
        for column in schema:
            # Step 1: a missing column breaks the contract.
            if ___:
                ok = False
            # Step 2: so does a value whose kind is not
            # the one schema gives for this column.
            # kind_of is written for you, below.
            elif kind_of(row[column]) != ___:
                ok = False
        # Step 3: good rows load; bad rows go to quarantine.
        if ok:
            good.append(row)
        else:
            ___
    return [good, bad]


def kind_of(value):
    # Already written for you: gives "text" for a string,
    # "number" for an int or a float, "other" for the rest.
    if type(value) == str:
        return "text"
    if type(value) == int or type(value) == float:
        return "number"
    return "other"
""",
        fills=['column not in row', 'schema[column]', 'bad.append(row)'],
        concepts=[
            [
                'Looping over a dict',
                '`for k in some_dict` gives each key in turn. `some_dict[k]` is that key\'s value.',
                """ages = {'ann': 31, 'bo': 25}
for name in ages:
    print(name, ages[name])""",
            ],
            [
                'in and not in',
                '`k in some_dict` is True when the dict has that key. `not in` is the opposite.',
                """pet = {'name': 'Rex'}
'age' not in pet   # True""",
            ],
            [
                'Not equal',
                '`a != b` means a is not equal to b. It is True when they differ.',
                """'cat' != 'dog'   # True
'cat' != 'cat'   # False""",
            ],
            [
                'if and elif',
                '`elif` is only checked when the `if` above it was False. Here, that means a value is only read once you know the column is there.',
                """if n < 0: print('negative')
elif n == 0: print('zero')""",
            ],
            [
                'Checking a type',
                '`type(x) == str` is True when x is a string. `int` is a whole number and `float` a number with a decimal point.',
                """type('hi') == str    # True
type(7.5) == float   # True""",
            ],
        ],
        byhand='T1: id is text and minutes 12 is a number: good. T2: minutes is "ten", text where a number should be: quarantine. T3 has no minutes column: quarantine. T4: minutes 7.5 is a number: good. Returns [good, quarantined]: the T1 and T4 rows, then the T2 and T3 rows.',
        why='One pass over the rows, checking each column.',
        gotchas=[
            [
                'Quarantine, then look',
                'A quarantine table nobody reads is a slow data leak. Alert when it grows.',
            ],
            [
                'Schema changes need an owner',
                'Turning on automatic schema merging means any upstream typo becomes a new column. Decide who approves new columns.',
            ],
        ],
    ),
)

lesson(MODULE, 'skew_report',
    title='Data skew in Spark',
    learn=[
        'Spark puts rows with the same key in the same partition. If one key has most of the rows (a **hot key**), one task (a task is one worker\'s share of the job) does most of the work while the others wait.',
        'Watch for it in the Spark UI (one task far slower than the rest). Fixes: check Adaptive Query Execution is on (AQE: Spark re-plans the job while it runs and can split a skewed join; it is on by default on Databricks and in Spark 3.2 and later, so only check nobody turned it off), handle the hot key separately, or salt it (add a random ending to the hot key so its rows spread over several partitions).',
    ],
    example=example('One hot key', """acme 9,000 rows · bolt 300 · cora 350 · dyna 350
→ the partition holding acme does about 3.6 times the average work"""),
    check=question(
        "199 tasks finish in a minute and one runs for an hour. What's the likely cause?",
        ['Not enough memory everywhere', 'One key with far more rows than the others', 'A slow network'],
        answer=1,
        why="That's the signature of skew.",
    ),
    angle=angle(
        pattern='Compare each key with the average',
        text='The big idea: if one key has far more rows than the rest, one worker does most of the job while the others wait. Your code goes through the keys twice. The first time it adds up all the rows, then divides by the number of keys to get the average. The second time it keeps every key whose count is more than `factor` times that average. You need the full total before you can judge any key, like needing every test mark before you know the class average.',
        say='"I compare each key\'s row count with the [[average|biggest|smallest::Add up all the rows and divide by the number of keys.]]. When one key has far more, I check AQE is on, handle that key [[separately|first|later::Pull it out from the others.]], or [[salt|drop|sort::Add a random bit to the key so its rows spread out.]] it."',
        classic=None,
    ),
    stack=stack('Spark: adaptive skew-join handling', """spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")   # on by default on Databricks"""),
    checked='2026-10-15',
    sources=[
        source('Databricks: adaptive query execution', 'https://docs.databricks.com/aws/en/optimizations/aqe'),
        source('Apache Spark: performance tuning', 'https://spark.apache.org/docs/latest/sql-performance-tuning.html'),
    ],
    exercise=exercise(
        title='Spot a Skewed Key',
        topic='production',
        difficulty='medium',
        fn='skew_report',
        prompt="""Spark groups rows by a **key** (for example a customer name) and gives each key's rows to one **task** (one worker). If one key has far more rows than the rest, its task does most of the work while the others sit idle. This is called **skew**.

Your function gets two things:

- `rows_per_key`: each key with its number of rows, like `[["acme", 9000], ["bolt", 300]]`.
- `factor`: how many times bigger than the average a key must be to count as skewed, like `2`.

The average is the total number of rows divided by the number of keys. Return the keys that have more than `factor` times the average (exactly equal does not count), in the order given, or `[]` if there are none.""",
        pattern='Add up the rows to get the average, then compare each key with it.',
        target='two passes over the keys: one to add up, one to compare',
        realworld='A join or groupBy on a skewed key (one huge customer, a null key, "unknown") makes one task run for an hour while 199 finish in a minute. Adaptive Query Execution handles many skewed joins automatically; otherwise salt the hot key or handle it separately.',
        starter="""def skew_report(rows_per_key, factor):
    # your code here
    pass
""",
        solution="""def skew_report(rows_per_key, factor):
    total = 0
    for key, count in rows_per_key:
        total = total + count
    average = total / len(rows_per_key)
    skewed = []
    for key, count in rows_per_key:
        if count > factor * average:
            skewed.append(key)
    return skewed
""",
        cases=[
            case([['acme', 9000], ['bolt', 300], ['cora', 350], ['dyna', 350]], 2, expected=['acme'], sample=True),
            case([['a', 10], ['b', 10]], 2, expected=[]),
            case([['x', 5]], 2, expected=[]),
            case([['a', 50], ['b', 50], ['c', 0], ['d', 0]], 1.5, expected=['a', 'b']),
            case([['null', 700], ['u1', 100], ['u2', 100], ['u3', 100]], 2, expected=['null']),
            case([['a', 60], ['b', 10], ['c', 10], ['d', 0]], 3, expected=[]),
        ],
        guided="""def skew_report(rows_per_key, factor):
    # Replace every ___ with real code, then run the tests.

    # Step 1: add up all the rows.
    total = 0
    for key, count in rows_per_key:
        total = total + count
    # Step 2: the average is the total divided by
    # the number of keys.
    average = ___
    skewed = []
    for key, count in rows_per_key:
        # Step 3: more than factor times the average?
        if ___:
            skewed.append(key)
    return skewed
""",
        fills=['total / len(rows_per_key)', 'count > factor * average'],
        concepts=[
            [
                'Two names in a for loop',
                'When each item is a pair, `for a, b in items` gives each part its own name.',
                """pairs = [['ann', 3], ['bo', 5]]
for name, score in pairs:
    print(name, score)""",
            ],
            [
                'Dividing, multiplying and len',
                '`len(items)` is how many items a list has. `/` divides, and can give a number with a decimal point. `*` multiplies.',
                """len(['a', 'b', 'c', 'd'])   # 4
10 / 4                      # 2.5
2 * 2.5                     # 5.0""",
            ],
        ],
        byhand='The rows add up to 10,000. There are 4 keys, so the average is 2,500 rows per key. Factor 2 times 2,500 is 5,000. acme has 9,000, more than 5,000: skewed. bolt, cora and dyna have 350 or fewer: fine. Returns ["acme"].',
        why='Two passes over the keys: one to add up, one to compare.',
        gotchas=[
            [
                'Nulls are a hot key',
                'Rows with a null join key all land together. Filter or handle them separately.',
            ],
            [
                'Salting trades work for balance',
                'Adding a random suffix to a hot key spreads it out, but the other side of the join must be repeated for each suffix.',
            ],
        ],
    ),
)
