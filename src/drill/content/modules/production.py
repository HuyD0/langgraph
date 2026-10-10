"""Production patterns: Rate limits, retries, concurrency, race conditions, idempotency and data at scale: the habits that keep AI systems up."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('production', 'Production patterns', 'Rate limits, retries, concurrency, race conditions, idempotency and data at scale: the habits that keep AI systems up.')

lesson(MODULE, 'token_bucket',
    title='Rate limiting before the 429',
    learn=[
        'Model endpoints limit how many requests (and tokens) you can send per minute. Hitting the limit and retrying works, but it wastes calls and adds delay for everyone.',
        'A **token bucket** keeps you under the limit on your side: a budget that refills at a steady rate, with room for a short burst.',
    ],
    example=example('Rate 2 per second, bucket of 5', """# 5 requests at once: all go (the bucket empties)
# the 6th must wait about half a second for a token to refill"""),
    check=question(
        "Your batch job sends 200 requests at once and gets 150 rate-limit errors. What's the better fix?",
        [
            'Retry them all immediately',
            'Limit the send rate on your side so you stay under the limit',
            'Use a bigger endpoint',
        ],
        answer=1,
        why='Retrying in a burst hits the same wall. Pacing the requests avoids the errors.',
    ),
    angle=angle(
        pattern='Token bucket',
        text='Two numbers, tokens and last time checked; top up for the time that passed, then spend one. One walk through the requests. "Design a rate limiter" is a common system design interview question.',
        say='"A token bucket refills at a fixed rate up to a burst size; each request spends a token or waits, which smooths traffic but allows short bursts."',
        classic=None,
    ),
    stack=stack('LangChain: a client-side token bucket', """from langchain_core.rate_limiters import InMemoryRateLimiter
limiter = InMemoryRateLimiter(requests_per_second=2, check_every_n_seconds=0.1, max_bucket_size=5)
llm = ChatDatabricks(endpoint=ENDPOINT, rate_limiter=limiter)"""),
    exercise=exercise(
        title='Rate-Limit Before the 429',
        topic='production',
        difficulty='medium',
        fn='token_bucket',
        prompt="""A **token bucket** keeps you under an API's rate limit. The bucket holds at most `burst` tokens and starts full. It refills at `rate` tokens per second, never above `burst`. Each request spends one token; with less than one token left, the request is held back.

`times` is a list of request times in seconds, in order. Return a list of `True` (sent) or `False` (held back), one per request.""",
        pattern='Keep two numbers, tokens and the last time you looked. Before each request, top up for the time that passed, capped at the bucket size.',
        target='one walk through the requests',
        realworld="Sending requests until the endpoint says 429 wastes calls and slows everyone down. A client-side limiter (LangChain's `InMemoryRateLimiter` is a token bucket) keeps you under the AI Gateway's limit in the first place, while still allowing short bursts.",
        starter="""def token_bucket(times, rate, burst):
    # your code here
    pass
""",
        solution="""def token_bucket(times, rate, burst):
    tokens = burst
    last = times[0] if times else 0
    out = []
    for t in times:
        tokens = min(burst, tokens + (t - last) * rate)
        last = t
        if tokens >= 1:
            tokens -= 1
            out.append(True)
        else:
            out.append(False)
    return out
""",
        cases=[
            case([0, 0, 0, 1, 1, 3], 1, 2, expected=[True, True, False, True, False, True], sample=True),
            case([], 5, 5, expected=[]),
            case([0, 1, 2, 3], 1, 1, expected=[True, True, True, True]),
            case([0, 0, 0, 0], 10, 3, expected=[True, True, True, False]),
            case([0, 0, 10, 10, 10], 1, 2, expected=[True, True, True, True, False]),
        ],
        guided="""def token_bucket(times, rate, burst):
    # Replace every ___ with real code, then run the tests.

    tokens = burst                    # the bucket starts full
    last = times[0] if times else 0   # when we last topped up
    out = []
    for t in times:
        # Step 1: refill for the seconds that passed, but never above burst.
        tokens = min(burst, ___)
        last = t
        # Step 2: spend a token if there is one.
        if ___:
            tokens -= 1
            out.append(True)
        else:
            out.append(False)
    return out
""",
        fills=['tokens + (t - last) * rate', 'tokens >= 1'],
        concepts=[['min as a cap', '`min(limit, value)` never lets value go above limit.', 'min(2, 5)   # 2']],
        byhand="Rate 1 per second, bucket of 2. At second 0: three requests. The first two spend the two tokens; the third is held back. At second 1 one token has refilled: the next request goes, the one after it doesn't. By second 3 two tokens have refilled (the bucket is full again), so it goes.",
        why='One walk through the requests, two numbers to track.',
        gotchas=[
            [
                'Limits are usually per minute and per token',
                'Model endpoints often limit tokens per minute as well as requests. Budget for the bigger of the two.',
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
        'Retry only errors that can succeed later (429 rate limits, 503 overload, timeouts). If the server sends **Retry-After**, wait that long.',
        "Otherwise wait longer each time, with **jitter**: a random wait inside a growing window, so many clients don't all retry at the same moment. Always stop after a few attempts.",
    ],
    example=example('Without and with jitter', """# 50 workers, no jitter: all retry at exactly 2 s, 4 s, 8 s → repeated collisions
# full jitter: each waits a random time in [0, 2], [0, 4], [0, 8] → spread out"""),
    check=question(
        'Fifty workers hit a rate limit at the same time and all retry after exactly 2 seconds. What happens?',
        ['They all succeed', 'They all hit the limit again together', 'Only one retries'],
        answer=1,
        why='Identical waits make the retries collide. Jitter spreads them out.',
    ),
    angle=angle(
        pattern='Testable randomness',
        text='A few steps per attempt. The engineering lesson is passing randomness in as an argument, so the function gives the same answer every time in a test.',
        say='"I honour Retry-After when present, otherwise use capped exponential backoff with full jitter, and inject the random source so it\'s testable."',
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
        prompt="""When a call fails with a rate limit, wait before retrying. Rules, in order:

1. If the server sent a `Retry-After` value (`retry_after` is not `None`), wait exactly that long.
2. Otherwise use **full jitter**: wait `rand * min(cap, base * 2 ** attempt)`, where `rand` is a random number between 0 and 1.

`attempt` counts from 0. Return the wait in seconds, rounded to 2 places. The random number is passed in as `rand` so your function is easy to test.""",
        pattern='Prefer what the server tells you; otherwise grow the window and pick a random point inside it.',
        target='a few arithmetic steps',
        realworld='If 50 workers hit a limit at the same moment and all wait exactly 2 seconds, they all retry together and hit it again. Random jitter spreads them out. Passing the random number in, instead of calling `random()` inside, is a standard trick that makes code like this testable.',
        starter="""def retry_wait(attempt, base, cap, retry_after, rand):
    # your code here
    pass
""",
        solution="""def retry_wait(attempt, base, cap, retry_after, rand):
    if retry_after is not None:
        return retry_after
    window = min(cap, base * 2 ** attempt)
    return round(rand * window, 2)
""",
        cases=[
            case(3, 1, 30, None, 0.5, expected=4.0, sample=True),
            case(0, 1, 30, 7, 0.9, expected=7),
            case(10, 1, 30, None, 0.25, expected=7.5),
            case(2, 0.5, 10, None, 0.0, expected=0.0),
            case(1, 2, 60, None, 1.0, expected=4.0),
        ],
        guided="""def retry_wait(attempt, base, cap, retry_after, rand):
    # Replace every ___ with real code, then run the tests.

    # Step 1: the server knows best.
    if retry_after is not None:
        return ___
    # Step 2: the window doubles each attempt, up to cap.
    window = min(cap, ___)
    # Step 3: pick a random point inside the window.
    return round(rand * window, 2)
""",
        fills=['retry_after', 'base * 2 ** attempt'],
        concepts=[
            ['Powers with **', '`2 ** 3` is 2 × 2 × 2 = 8.', '2 ** 3   # 8'],
            [
                'is not None',
                'The right way to check that a value was given.',
                """if retry_after is not None:
    ...""",
            ],
        ],
        byhand='Attempt 3, base 1, cap 30: the window is 1 × 2 × 2 × 2 = 8 seconds. With rand 0.5, wait 4 seconds. If the server had said Retry-After 7, wait 7 instead.',
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
        'But unlimited concurrency triggers rate limits and overloads services. Use a **cap**: a semaphore lets at most N run at once, and the next starts the moment one finishes.',
    ],
    example=example('100 calls of 2 seconds each', """# one at a time:   200 seconds
# 10 at a time:     20 seconds
# all 100 at once:  2 seconds, if nothing pushes back (it will)"""),
    check=question(
        "You wrap 1,000 LLM calls in `asyncio.gather` with no limit. What's the likely result?",
        [
            'Fastest possible run',
            'A flood of rate-limit errors and timeouts',
            'Python runs them one at a time',
        ],
        answer=1,
        why='All 1,000 start at once. Add a semaphore or max_concurrency.',
    ),
    angle=angle(
        pattern='Bounded worker pool',
        text='Repeatedly finish the earliest running call and start the next one: one step per call. With a large limit, a heap finds the earliest quickly; this is the "task scheduler" interview pattern.',
        say='"A semaphore caps calls in flight; when one finishes the next starts, so throughput is high without exceeding the rate limit."',
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
        prompt="""You need to make many LLM calls, but at most `limit` may run at the same time. Calls start in list order; whenever one finishes, the next waiting call starts immediately. `durations` gives how long each call takes, in seconds.

Return `[total_time, finish_order]`: when the last call finishes, and the positions of the calls in the order they finished. If two finish at the same moment, the lower position finishes first. No calls gives `[0, []]`.""",
        pattern='Keep the set of running calls with their end times; repeatedly finish the earliest one and start the next waiting call.',
        target='one step per call finishing',
        realworld="This is what `asyncio.Semaphore`, a thread pool's `max_workers` and LangChain's `max_concurrency` do. Unlimited concurrency triggers rate limits; one at a time is slow. A cap gets most of the speed without the 429s.",
        starter="""def run_with_limit(durations, limit):
    # your code here
    pass
""",
        solution="""def run_with_limit(durations, limit):
    running = []   # [end_time, position]
    order = []
    nxt = 0
    now = 0
    while nxt < len(durations) and len(running) < limit:
        running.append([durations[nxt], nxt])
        nxt += 1
    while running:
        running.sort()
        end, pos = running.pop(0)
        now = end
        order.append(pos)
        if nxt < len(durations):
            running.append([now + durations[nxt], nxt])
            nxt += 1
    return [now, order]
""",
        cases=[
            case([3, 1, 2, 4], 2, expected=[7, [1, 0, 2, 3]], sample=True),
            case([], 3, expected=[0, []]),
            case([5, 5, 5], 3, expected=[5, [0, 1, 2]]),
            case([2, 2, 2], 1, expected=[6, [0, 1, 2]]),
            case([4, 1, 1, 1], 2, expected=[4, [1, 2, 3, 0]]),
        ],
        guided="""def run_with_limit(durations, limit):
    # Replace every ___ with real code, then run the tests.

    running = []   # [end_time, position] for each call in flight
    order = []
    nxt = 0        # the next call waiting to start
    now = 0
    # Step 1: start the first `limit` calls at time 0.
    while nxt < len(durations) and len(running) < limit:
        running.append([durations[nxt], nxt])
        nxt += 1
    while running:
        # Step 2: the earliest end time finishes next (sorting pairs breaks ties by position).
        running.sort()
        end, pos = running.pop(0)
        now = end
        order.append(pos)
        # Step 3: a slot is free, so start the next waiting call now.
        if nxt < len(durations):
            running.append([___, nxt])
            nxt += 1
    return [now, order]
""",
        fills=['now + durations[nxt]'],
        concepts=[
            [
                'Sorting pairs',
                'Lists of pairs sort by the first item, then the second, which gives the tie-break for free.',
                'sorted([[3, 0], [3, 2], [1, 1]])   # [[1, 1], [3, 0], [3, 2]]',
            ],
            [
                'pop(0)',
                'Removes and returns the first item.',
                """q = [[1, 1], [3, 0]]
q.pop(0)   # [1, 1]""",
            ],
        ],
        byhand='Limit 2: calls 0 (3 s) and 1 (1 s) start. At 1 s call 1 finishes and call 2 (2 s) starts, ending at 3 s. At 3 s calls 0 and 2 both finish: 0 first. Call 3 (4 s) starts at 3 s and ends at 7 s.',
        why='Each call is started once and finished once. Sorting the few running calls each time is fine for a small limit; a heap makes it faster when the limit is large.',
        gotchas=[
            [
                'gather without a limit',
                '`asyncio.gather` on 1,000 calls starts all 1,000 at once. Wrap each call in a semaphore.',
            ],
            [
                'One slow call holds a slot',
                "Give every call a timeout, so a stuck request doesn't quietly halve your throughput.",
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
    example=example('A lost update', """# worker A reads count = 10, worker B reads count = 10
# A saves 11, B saves 11  →  one increment is lost
# with versions: B's write says "I read version 7", but it's now 8 → rejected, B retries"""),
    check=question(
        'Two agents update the same ticket at nearly the same time. Which approach avoids losing one update?',
        [
            'Read, change in Python, then write',
            'Write only if the version is still the one you read, otherwise retry',
            'Add a sleep before writing',
        ],
        answer=1,
        why='The check has to happen as part of the write. A sleep only makes the race rarer.',
    ),
    angle=angle(
        pattern='Compare-and-set',
        text='One walk through the writes, accepting only those that saw the current version.',
        say='"I use optimistic concurrency: writes carry the version they read and fail if it changed, so the loser re-reads and retries instead of overwriting."',
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
        prompt="""Two workers read a record at version 3, both change it, and both save. Without care, the second save silently erases the first: a **lost update**, the classic race condition.

**Optimistic concurrency** fixes it: each write says which version it read, and it's accepted only if the record is still at that version (then the version goes up by one). Otherwise it's rejected, and that writer must re-read and try again.

Given the record's starting `version` and `writes`, a list of `[writer, expected_version]` in arrival order, return `[accepted, rejected, final_version]`.""",
        pattern='Compare-and-set: change only if the value is still what you saw.',
        target='one walk through the writes',
        realworld="Delta Lake commits work this way: if another job committed a conflicting change first, your commit fails and you retry. It's also how version-checked updates, HTTP ETags and Terraform state locking stop two writers from clobbering each other.",
        starter="""def optimistic_writes(version, writes):
    # your code here
    pass
""",
        solution="""def optimistic_writes(version, writes):
    accepted, rejected = [], []
    for writer, expected in writes:
        if expected == version:
            accepted.append(writer)
            version += 1
        else:
            rejected.append(writer)
    return [accepted, rejected, version]
""",
        cases=[
            case(3, [['job_a', 3], ['job_b', 3], ['job_b', 4]], expected=[['job_a', 'job_b'], ['job_b'], 5], sample=True),
            case(1, [], expected=[[], [], 1]),
            case(0, [['x', 1]], expected=[[], ['x'], 0]),
            case(7, [['a', 7], ['b', 8], ['c', 9]], expected=[['a', 'b', 'c'], [], 10]),
        ],
        guided="""def optimistic_writes(version, writes):
    # Replace every ___ with real code, then run the tests.

    accepted, rejected = [], []
    for writer, expected in writes:
        # Step 1: is the record still at the version this writer read?
        if ___:
            accepted.append(writer)
            # Step 2: a successful write bumps the version.
            ___
        else:
            rejected.append(writer)
    return [accepted, rejected, version]
""",
        fills=['expected == version', 'version += 1'],
        concepts=[
            [
                'Compare, then change',
                'Check a condition and update together in one step, so nothing can slip in between.',
                """if expected == version:
    version += 1""",
            ],
        ],
        byhand="Version 3. job_a expected 3: accepted, now version 4. job_b expected 3, but it's 4: rejected. job_b re-reads and tries with 4: accepted, version 5.",
        why='One walk through the writes.',
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
        "Appending rows is not idempotent; each retry duplicates them. **Upsert** on a stable key (Delta's `MERGE INTO`) is: matching rows are updated, new ones inserted.",
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
        pattern='Index, then update or insert',
        text='Build a key-to-position map in one walk, then each update is an instant lookup. The same "hash map of what exists" idea as Two Sum.',
        say='"I index existing rows by key, replace on match and append otherwise, so re-running the same batch is a no-op."',
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
        prompt="""A job that saves results may be retried after a crash, so saving twice must not create duplicates. An **upsert** updates the row with the same key if it exists, and inserts it otherwise.

`table` and `updates` are lists of dicts, and `key` names the field that identifies a row. Return the new table: existing rows stay in place (replaced by the update when keys match), new rows are added at the end in order, and if two updates share a key, the later one wins. Don't change `table` itself.""",
        pattern='Index the existing rows by key, then each update either replaces in place or appends.',
        target='one walk through the table, one through the updates',
        realworld="This is Delta Lake's `MERGE INTO`. Writing results with MERGE on a stable key, instead of appending, means a retried job or a re-run notebook leaves the table exactly as one run would. That property is called idempotency.",
        starter="""def upsert_rows(table, updates, key):
    # your code here
    pass
""",
        solution="""def upsert_rows(table, updates, key):
    out = [dict(r) for r in table]
    where = {}
    for i, r in enumerate(out):
        where[r[key]] = i
    for u in updates:
        if u[key] in where:
            out[where[u[key]]] = dict(u)
        else:
            where[u[key]] = len(out)
            out.append(dict(u))
    return out
""",
        cases=[
            case([{'ticket_id': 'T1', 'status': 'open'}, {'ticket_id': 'T2', 'status': 'open'}], [{'ticket_id': 'T2', 'status': 'closed'}, {'ticket_id': 'T3', 'status': 'open'}], 'ticket_id', expected=[
                {'ticket_id': 'T1', 'status': 'open'},
                {'ticket_id': 'T2', 'status': 'closed'},
                {'ticket_id': 'T3', 'status': 'open'},
            ], sample=True),
            case([], [], 'id', expected=[]),
            case([{'id': 1, 'v': 'a'}], [{'id': 1, 'v': 'a'}], 'id', expected=[{'id': 1, 'v': 'a'}]),
            case([], [{'id': 5, 'v': 'x'}, {'id': 5, 'v': 'y'}], 'id', expected=[{'id': 5, 'v': 'y'}]),
            case([{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'b'}], [{'id': 1, 'v': 'z'}], 'id', expected=[{'id': 1, 'v': 'z'}, {'id': 2, 'v': 'b'}]),
        ],
        guided="""def upsert_rows(table, updates, key):
    # Replace every ___ with real code, then run the tests.

    # Step 1: copy the rows, so the caller's table is untouched.
    out = [dict(r) for r in table]
    # Step 2: key -> position, for instant lookups.
    where = {}
    for i, r in enumerate(out):
        where[r[key]] = i
    for u in updates:
        if u[key] in where:
            # Step 3: replace the existing row in place.
            out[___] = dict(u)
        else:
            # Step 4: remember where the new row goes, then add it.
            where[u[key]] = ___
            out.append(dict(u))
    return out
""",
        fills=['where[u[key]]', 'len(out)'],
        concepts=[
            [
                'Copying a list of dicts',
                "`[dict(r) for r in rows]` copies each row, so changes don't leak back to the original.",
                'copy = [dict(r) for r in rows]',
            ],
            [
                'Key to position',
                'A dict from key to index finds the row to replace instantly.',
                """where = {'T2': 1}
out[where['T2']]""",
            ],
        ],
        byhand='T1 and T2 exist at positions 0 and 1. Update T2 → closed: replace position 1. T3 is new: add it at position 2. Run the same updates again and nothing changes.',
        why='One walk to index the table, one through the updates; each lookup is instant.',
        gotchas=[
            [
                'Appending is not idempotent',
                "INSERT on retry doubles your rows. MERGE (or overwrite by partition) on a stable key doesn't.",
            ],
            [
                'Duplicate keys in the source',
                "If one batch contains the same key twice, MERGE on Delta fails because it can't tell which row wins. Remove duplicates in the source first.",
            ],
        ],
    ),
)

lesson(MODULE, 'chunk_rows',
    title='Transforming data at scale with Spark',
    learn=[
        "Spark splits a table into **partitions** and runs your code on each partition in parallel across the cluster. That only works if your function handles **one row at a time** and doesn't depend on other rows or on shared state.",
        'Give every output a **stable id** built from its inputs, so re-running the job produces the same ids and a MERGE overwrites instead of duplicating.',
    ],
    example=example('One document becomes many chunk rows', """doc_id  text                 →  doc_id  chunk_id  text
d1      "abcdefg" (size 3)     d1      d1-0      abc
                                d1      d1-1      def
                                d1      d1-2      g"""),
    check=question(
        'Your chunking job uses `uuid4()` for chunk ids and is re-run after a failure. What happens?',
        [
            'Nothing changes',
            'Every chunk gets a new id, so the index fills with duplicates',
            'Spark reuses the old ids',
        ],
        answer=1,
        why='Random ids differ every run. Ids built from the data are the same every time.',
    ),
    angle=angle(
        pattern='Map, then flatten',
        text='Each input row produces zero or more output rows, independently: one step per piece. This independence is what lets the work spread across machines.',
        say='"I write a pure per-row function with deterministic ids, so Spark can parallelise it and re-runs are idempotent."',
        classic=None,
    ),
    stack=stack('PySpark: a pandas UDF plus posexplode', """from pyspark.sql import functions as F, types as T

@F.pandas_udf(T.ArrayType(T.StringType()))
def split_text(texts: pd.Series) -> pd.Series:
    return texts.fillna("").map(lambda t: [t[i:i + 1000] for i in range(0, len(t), 1000)])

chunks = (spark.table("main.support.docs")
    .select("doc_id", F.posexplode(split_text("text")).alias("i", "text"))
    .withColumn("chunk_id", F.concat_ws("-", "doc_id", "i")))"""),
    exercise=exercise(
        title='Chunking at Scale',
        topic='production',
        difficulty='easy',
        fn='chunk_rows',
        prompt="""To chunk millions of documents, Spark runs the same small function on every row, spread across many machines. That function must depend only on its own row.

Given `docs`, a list like `[{"doc_id": "d1", "text": "..."}]`, split each text into pieces of `size` characters (no overlap; the last may be shorter) and return one row per piece: `{"doc_id": ..., "chunk_id": doc_id + "-" + str(i), "text": piece}`, with `i` counting from 0 within each document. Documents with empty text produce no rows.""",
        pattern='Map each input row to zero or more output rows, using only that row. Give every output a stable id built from its inputs.',
        target='one step per piece',
        realworld='In Spark this is a UDF plus `posexplode`, or `mapInPandas`. Because each row is handled on its own, Spark can split the work across the cluster. Ids like `d1-0` are deterministic, so re-running the job produces the same ids and a MERGE overwrites instead of duplicating.',
        starter="""def chunk_rows(docs, size):
    # your code here
    pass
""",
        solution="""def chunk_rows(docs, size):
    out = []
    for d in docs:
        text = d["text"]
        for i, start in enumerate(range(0, len(text), size)):
            out.append({"doc_id": d["doc_id"], "chunk_id": d["doc_id"] + "-" + str(i), "text": text[start:start + size]})
    return out
""",
        cases=[
            case([{'doc_id': 'd1', 'text': 'abcdefg'}, {'doc_id': 'd2', 'text': 'xy'}], 3, expected=[
                {'doc_id': 'd1', 'chunk_id': 'd1-0', 'text': 'abc'},
                {'doc_id': 'd1', 'chunk_id': 'd1-1', 'text': 'def'},
                {'doc_id': 'd1', 'chunk_id': 'd1-2', 'text': 'g'},
                {'doc_id': 'd2', 'chunk_id': 'd2-0', 'text': 'xy'},
            ], sample=True),
            case([], 5, expected=[]),
            case([{'doc_id': 'e', 'text': ''}], 4, expected=[]),
            case([{'doc_id': 'a', 'text': 'abcd'}], 4, expected=[{'doc_id': 'a', 'chunk_id': 'a-0', 'text': 'abcd'}]),
        ],
        guided="""def chunk_rows(docs, size):
    # Replace every ___ with real code, then run the tests.

    out = []
    for d in docs:
        text = d["text"]
        # Step 1: starts at 0, size, 2*size... and i counts the pieces.
        for i, start in enumerate(range(0, len(text), ___)):
            # Step 2: a stable id built from the document id and piece number.
            out.append({"doc_id": d["doc_id"], "chunk_id": ___, "text": text[start:start + size]})
    return out
""",
        fills=['size', 'd["doc_id"] + "-" + str(i)'],
        concepts=[
            [
                'enumerate over a range',
                'Counts the pieces while stepping through start positions.',
                'list(enumerate(range(0, 7, 3)))   # [(0, 0), (1, 3), (2, 6)]',
            ],
            [
                'Building an id',
                '`str(i)` turns a number into text so it can be joined.',
                "'d1' + '-' + str(2)   # 'd1-2'",
            ],
        ],
        byhand='d1 is "abcdefg" with size 3: "abc" (d1-0), "def" (d1-1), "g" (d1-2). d2 is "xy": one piece, d2-0.',
        why='One step per piece, and every document is handled on its own, which is what lets Spark spread it out.',
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
            'A bigger cluster',
            'Process only new or changed documents, tracked with a checkpoint',
            'Run it weekly',
        ],
        answer=1,
        why='Incremental processing makes cost follow what changed, not what exists.',
    ),
    angle=angle(
        pattern='Resume from a checkpoint',
        text='One walk through the events.',
        say='"I persist the last processed offset, read only past it, and use a watermark to bound how long I wait for late data."',
        classic=None,
    ),
    stack=stack('Structured Streaming: checkpoint, watermark, run as a batch', """(spark.readStream.table("main.support.events")
    .withWatermark("event_time", "1 hour")
    .writeStream
    .option("checkpointLocation", "/Volumes/main/support/checkpoints/events")
    .trigger(availableNow=True)
    .toTable("main.support.events_clean"))"""),
    exercise=exercise(
        title="Process Only What's New",
        topic='production',
        difficulty='medium',
        fn='process_new',
        prompt="""A job reads from an event log. It remembers the last `offset` it processed, and ignores events older than a **watermark** (too late to count).

`events` is a list of `[offset, event_time, value]`. Process events with offset greater than the saved `offset`. Of those, keep the ones with `event_time >= watermark` and drop the late ones. Return `[kept_values, dropped_values, new_offset]`, where new_offset is the highest offset read (or the old one if nothing was new).""",
        pattern="Remember where you got to; resume from there; decide what's too late.",
        target='one walk through the events',
        realworld="This is what Structured Streaming's `checkpointLocation` (the saved offset) and `withWatermark` (the late cutoff) do. With `trigger(availableNow=True)` the same job runs as a cheap batch that only processes new data each time.",
        starter="""def process_new(events, offset, watermark):
    # your code here
    pass
""",
        solution="""def process_new(events, offset, watermark):
    kept, dropped = [], []
    new_offset = offset
    for off, t, value in events:
        if off <= offset:
            continue
        new_offset = max(new_offset, off)
        if t >= watermark:
            kept.append(value)
        else:
            dropped.append(value)
    return [kept, dropped, new_offset]
""",
        cases=[
            case([[1, 100, 'a'], [2, 105, 'b'], [3, 90, 'c'], [4, 120, 'd']], 1, 100, expected=[['b', 'd'], ['c'], 4], sample=True),
            case([], 7, 0, expected=[[], [], 7]),
            case([[1, 5, 'x']], 3, 0, expected=[[], [], 3]),
            case([[5, 50, 'p'], [6, 49, 'q']], 4, 50, expected=[['p'], ['q'], 6]),
        ],
        guided="""def process_new(events, offset, watermark):
    # Replace every ___ with real code, then run the tests.

    kept, dropped = [], []
    new_offset = offset
    for off, t, value in events:
        # Step 1: already processed last time? skip it.
        if ___:
            continue
        new_offset = max(new_offset, off)
        # Step 2: on time, or too late?
        if ___:
            kept.append(value)
        else:
            dropped.append(value)
    return [kept, dropped, new_offset]
""",
        fills=['off <= offset', 't >= watermark'],
        concepts=[
            [
                'max to track the highest',
                '`max(a, b)` keeps the larger, so it ratchets upward.',
                'best = max(best, off)',
            ],
        ],
        byhand='Saved offset 1, so skip event 1. Event 2 at time 105: keep b. Event 3 at 90 is before the watermark 100: drop c. Event 4: keep d. The new offset is 4.',
        why='One walk through the events.',
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
        'Check rows against a **contract**, quarantine the bad ones instead of failing the whole load, and decide on purpose whether new columns are allowed in.',
    ],
    example=example('Good, quarantined, new columns', 'T1 {minutes: 12}       → good\nT2 {minutes: "twelve"} → quarantine\nT3 {..., channel}      → good, report new column "channel"'),
    check=question(
        "One malformed row in a million breaks your nightly load. What's the better design?",
        ['Fail the whole load', 'Quarantine bad rows, load the rest, and alert', 'Ignore bad rows silently'],
        answer=1,
        why='Keep data flowing, but make bad rows visible.',
    ),
    angle=angle(
        pattern='Validate and route',
        text='One walk through the rows, checking each column.',
        say='"I validate each row against the schema, route failures to a quarantine table with alerts, and surface unexpected columns for review."',
        classic=None,
    ),
    stack=stack('Lakeflow pipelines: expectations in SQL', """CREATE OR REFRESH STREAMING TABLE tickets_clean (
  CONSTRAINT valid_id EXPECT (ticket_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_minutes EXPECT (minutes >= 0)
) AS SELECT * FROM STREAM(main.support.tickets_raw)"""),
    exercise=exercise(
        title='Data Contracts',
        topic='production',
        difficulty='medium',
        fn='validate_rows',
        prompt="""Before loading rows into a table, check them against a schema: `schema` maps each column to `"str"`, `"int"` or `"float"` (an int is fine where a float is expected, but `True`/`False` never count as numbers).

A row is good if every schema column is present and has the right type. Bad rows go to quarantine instead of breaking the load. Also collect any column names that aren't in the schema: new columns someone started sending.

Return `[good_rows, quarantined_rows, new_columns]`, with new_columns sorted and without repeats.""",
        pattern='Check each row against a contract; route failures aside instead of crashing; report surprises.',
        target='one walk through the rows',
        realworld="Lakeflow pipeline expectations do this (`EXPECT ... ON VIOLATION DROP ROW`, or fail the update), and Delta's `mergeSchema` decides whether new columns are allowed in. Quarantining bad rows keeps one malformed record from stopping the whole pipeline.",
        starter="""def validate_rows(rows, schema):
    # your code here
    pass
""",
        solution="""def type_ok(value, kind):
    name = type(value).__name__
    if kind == "float":
        return name in ("float", "int")
    return name == kind

def validate_rows(rows, schema):
    good, bad, extra = [], [], set()
    for r in rows:
        for col in r:
            if col not in schema:
                extra.add(col)
        ok = all(col in r and type_ok(r[col], kind) for col, kind in schema.items())
        (good if ok else bad).append(r)
    return [good, bad, sorted(extra)]
""",
        cases=[
            case([
                {'ticket_id': 'T1', 'minutes': 12, 'score': 0.9},
                {'ticket_id': 'T2', 'minutes': 'twelve', 'score': 0.8},
                {'ticket_id': 'T3', 'minutes': 5, 'score': 1, 'channel': 'chat'},
            ], {'ticket_id': 'str', 'minutes': 'int', 'score': 'float'}, expected=[
                [
                    {'ticket_id': 'T1', 'minutes': 12, 'score': 0.9},
                    {'ticket_id': 'T3', 'minutes': 5, 'score': 1, 'channel': 'chat'},
                ],
                [{'ticket_id': 'T2', 'minutes': 'twelve', 'score': 0.8}],
                ['channel'],
            ], sample=True),
            case([], {'a': 'int'}, expected=[[], [], []]),
            case([{'a': True}], {'a': 'int'}, expected=[[], [{'a': True}], []]),
            case([{'b': 1}], {'a': 'int'}, expected=[[], [{'b': 1}], ['b']]),
        ],
        guided="""def type_ok(value, kind):
    # type(x).__name__ is 'str', 'int', 'float' or 'bool' - so True isn't an int here.
    name = type(value).__name__
    if kind == "float":
        return name in ("float", "int")
    return name == kind


def validate_rows(rows, schema):
    # Replace every ___ with real code, then run the tests.

    good, bad, extra = [], [], set()
    for r in rows:
        # Step 1: note any column the schema doesn't know.
        for col in r:
            if ___:
                extra.add(col)
        # Step 2: every schema column present, with the right type.
        ok = all(col in r and ___ for col, kind in schema.items())
        (good if ok else bad).append(r)
    return [good, bad, sorted(extra)]
""",
        fills=['col not in schema', 'type_ok(r[col], kind)'],
        concepts=[
            [
                'all',
                'True only if the condition holds for every item.',
                'all(x > 0 for x in [1, 2, 3])   # True',
            ],
            [
                'A set for unique names',
                'Adding the same name twice keeps one copy.',
                """s = set()
s.add('channel'); s.add('channel')   # {'channel'}""",
            ],
        ],
        byhand="T1 matches the schema: good. T2's minutes is text: quarantine. T3 is fine (an int is OK for score) but has an extra column, channel: good, and report channel.",
        why='One walk through the rows, checking each column.',
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
        'Spark puts rows with the same key in the same partition. If one key has most of the rows, one task does most of the work while the others wait.',
        'Watch for it in the Spark UI (one task far slower than the rest). Fixes: let Adaptive Query Execution split skewed joins, handle the hot key separately, or salt it.',
    ],
    example=example('One hot key', """acme 9,000 rows · bolt 300 · cora 350 · dyna 350
→ the partition holding acme does ~3.6× the average work"""),
    check=question(
        "199 tasks finish in a minute and one runs for an hour. What's the likely cause?",
        ['Not enough memory everywhere', 'One key with far more rows than the others', 'A slow network'],
        answer=1,
        why="That's the signature of skew.",
    ),
    angle=angle(
        pattern='Bucket and compare',
        text='One walk through the keys, then compare the biggest bucket with the average.',
        say='"I check per-partition row counts; when one key dominates I rely on AQE skew handling or salt the hot key."',
        classic=None,
    ),
    stack=stack('Spark: adaptive skew-join handling', """spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")   # on by default on Databricks"""),
    exercise=exercise(
        title='Spot a Skewed Key',
        topic='production',
        difficulty='medium',
        fn='skew_report',
        prompt="""Spark sends all rows with the same key to the same partition. If one key has most of the rows, one task does most of the work while the others sit idle: **skew**.

`counts` is a list of `[key, rows]`. Each key goes to partition `sum of its character codes % partitions` (use `ord(c)` for a character's code). Return `[imbalance, heaviest_key]`: the busiest partition's rows divided by the average rows per partition, rounded to 1 place, and the key with the most rows (the first one listed wins a tie).""",
        pattern='Group into buckets, then compare the biggest bucket with the average.',
        target='one walk through the keys',
        realworld='A join or groupBy on a skewed key (one huge customer, a null key, "unknown") makes one task run for an hour while 199 finish in a minute. Adaptive Query Execution handles many skewed joins automatically; otherwise salt the hot key or handle it separately.',
        starter="""def skew_report(counts, partitions):
    # your code here
    pass
""",
        solution="""def skew_report(counts, partitions):
    load = [0] * partitions
    total = 0
    heaviest, most = None, -1
    for key, rows in counts:
        p = sum(ord(c) for c in key) % partitions
        load[p] += rows
        total += rows
        if rows > most:
            heaviest, most = key, rows
    if total == 0:
        return [0.0, heaviest]
    return [round(max(load) / (total / partitions), 1), heaviest]
""",
        cases=[
            case([['acme', 9000], ['bolt', 300], ['cora', 350], ['dyna', 350]], 4, expected=[3.6, 'acme'], sample=True),
            case([], 3, expected=[0.0, None]),
            case([['a', 10], ['b', 10]], 2, expected=[1.0, 'a']),
            case([['x', 5]], 1, expected=[1.0, 'x']),
        ],
        guided="""def skew_report(counts, partitions):
    # Replace every ___ with real code, then run the tests.

    load = [0] * partitions   # rows per partition
    total = 0
    heaviest, most = None, -1
    for key, rows in counts:
        # Step 1: which partition does this key land in?
        p = sum(ord(c) for c in key) % ___
        load[p] += rows
        total += rows
        if rows > most:
            heaviest, most = key, rows
    if total == 0:
        return [0.0, heaviest]
    # Step 2: busiest partition compared with the average.
    return [round(___ / (total / partitions), 1), heaviest]
""",
        fills=['partitions', 'max(load)'],
        concepts=[
            ['ord', 'The number behind a character.', "ord('a')   # 97"],
            ['A list of zeros', '`[0] * 4` makes four counters.', 'load = [0] * 4'],
        ],
        byhand='10,000 rows over 4 partitions is 2,500 on average. acme alone is 9,000, so its partition holds at least 9,000: about 3.6 times the average. One task does most of the work.',
        why='One walk through the keys.',
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
