"""Production-pattern exercises: rate limits, retries, concurrency, races, idempotency, distributed chunking."""
import json
P = []
def add(**k): P.append(k)

add(id="token_bucket", title="Rate-Limit Before the 429", topic="production", difficulty="medium", fn="token_bucket",
 prompt="A **token bucket** keeps you under an API's rate limit. The bucket holds at most `burst` tokens and starts full. It refills at `rate` tokens per second, never above `burst`. Each request spends one token; with less than one token left, the request is held back.\n\n`times` is a list of request times in seconds, in order. Return a list of `True` (sent) or `False` (held back), one per request.",
 pattern="Keep two numbers, tokens and the last time you looked. Before each request, top up for the time that passed, capped at the bucket size.",
 target="one walk through the requests",
 realworld="Sending requests until the endpoint says 429 wastes calls and slows everyone down. A client-side limiter (LangChain's `InMemoryRateLimiter` is a token bucket) keeps you under the AI Gateway's limit in the first place, while still allowing short bursts.",
 starter="def token_bucket(times, rate, burst):\n    # your code here\n    pass\n",
 solution="def token_bucket(times, rate, burst):\n    tokens = burst\n    last = times[0] if times else 0\n    out = []\n    for t in times:\n        tokens = min(burst, tokens + (t - last) * rate)\n        last = t\n        if tokens >= 1:\n            tokens -= 1\n            out.append(True)\n        else:\n            out.append(False)\n    return out\n",
 cases=[([0, 0, 0, 1, 1, 3], 1, 2, [True, True, False, True, False, True], True), ([], 5, 5, []), ([0, 1, 2, 3], 1, 1, [True, True, True, True]), ([0, 0, 0, 0], 10, 3, [True, True, True, False]), ([0, 0, 10, 10, 10], 1, 2, [True, True, True, True, False])],
 guided="def token_bucket(times, rate, burst):\n    # Replace every ___ with real code, then run the tests.\n\n    tokens = burst                    # the bucket starts full\n    last = times[0] if times else 0   # when we last topped up\n    out = []\n    for t in times:\n        # Step 1: refill for the seconds that passed, but never above burst.\n        tokens = min(burst, ___)\n        last = t\n        # Step 2: spend a token if there is one.\n        if ___:\n            tokens -= 1\n            out.append(True)\n        else:\n            out.append(False)\n    return out\n",
 fills=["tokens + (t - last) * rate", "tokens >= 1"],
 learn=dict(concepts=[["min as a cap", "`min(limit, value)` never lets value go above limit.", "min(2, 5)   # 2"]],
  byhand="Rate 1 per second, bucket of 2. At second 0: three requests. The first two spend the two tokens; the third is held back. At second 1 one token has refilled: the next request goes, the one after it doesn't. By second 3 two tokens have refilled (the bucket is full again), so it goes.",
  why="One walk through the requests, two numbers to track.",
  gotchas=[["Limits are usually per minute and per token", "Model endpoints often limit tokens per minute as well as requests. Budget for the bigger of the two."], ["One limiter per process isn't one limiter", "Ten workers each with their own bucket send ten times the rate. Shared limits need shared state, or a gateway that enforces them."]]))

add(id="retry_wait", title="Retries With Jitter", topic="production", difficulty="easy", fn="retry_wait",
 prompt="When a call fails with a rate limit, wait before retrying. Rules, in order:\n\n1. If the server sent a `Retry-After` value (`retry_after` is not `None`), wait exactly that long.\n2. Otherwise use **full jitter**: wait `rand * min(cap, base * 2 ** attempt)`, where `rand` is a random number between 0 and 1.\n\n`attempt` counts from 0. Return the wait in seconds, rounded to 2 places. The random number is passed in as `rand` so your function is easy to test.",
 pattern="Prefer what the server tells you; otherwise grow the window and pick a random point inside it.",
 target="a few arithmetic steps",
 realworld="If 50 workers hit a limit at the same moment and all wait exactly 2 seconds, they all retry together and hit it again. Random jitter spreads them out. Passing the random number in, instead of calling `random()` inside, is a standard trick that makes code like this testable.",
 starter="def retry_wait(attempt, base, cap, retry_after, rand):\n    # your code here\n    pass\n",
 solution="def retry_wait(attempt, base, cap, retry_after, rand):\n    if retry_after is not None:\n        return retry_after\n    window = min(cap, base * 2 ** attempt)\n    return round(rand * window, 2)\n",
 cases=[(3, 1, 30, None, 0.5, 4.0, True), (0, 1, 30, 7, 0.9, 7), (10, 1, 30, None, 0.25, 7.5), (2, 0.5, 10, None, 0.0, 0.0), (1, 2, 60, None, 1.0, 4.0)],
 guided="def retry_wait(attempt, base, cap, retry_after, rand):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: the server knows best.\n    if retry_after is not None:\n        return ___\n    # Step 2: the window doubles each attempt, up to cap.\n    window = min(cap, ___)\n    # Step 3: pick a random point inside the window.\n    return round(rand * window, 2)\n",
 fills=["retry_after", "base * 2 ** attempt"],
 learn=dict(concepts=[["Powers with **", "`2 ** 3` is 2 × 2 × 2 = 8.", "2 ** 3   # 8"], ["is not None", "The right way to check that a value was given.", "if retry_after is not None:\n    ..."]],
  byhand="Attempt 3, base 1, cap 30: the window is 1 × 2 × 2 × 2 = 8 seconds. With rand 0.5, wait 4 seconds. If the server had said Retry-After 7, wait 7 instead.",
  why="A few steps, however many retries.",
  gotchas=[["Only retry what can succeed later", "429 and 503 are worth retrying. 400 and 401 will fail the same way every time."], ["Cap the total, not just each wait", "Also stop after a few attempts or a total time limit, so a user isn't left waiting minutes."]]))

add(id="run_with_limit", title="Many Calls, a Few at a Time", topic="production", difficulty="medium", fn="run_with_limit",
 prompt="You need to make many LLM calls, but at most `limit` may run at the same time. Calls start in list order; whenever one finishes, the next waiting call starts immediately. `durations` gives how long each call takes, in seconds.\n\nReturn `[total_time, finish_order]`: when the last call finishes, and the positions of the calls in the order they finished. If two finish at the same moment, the lower position finishes first. No calls gives `[0, []]`.",
 pattern="Keep the set of running calls with their end times; repeatedly finish the earliest one and start the next waiting call.",
 target="one step per call finishing",
 realworld="This is what `asyncio.Semaphore`, a thread pool's `max_workers` and LangChain's `max_concurrency` do. Unlimited concurrency triggers rate limits; one at a time is slow. A cap gets most of the speed without the 429s.",
 starter="def run_with_limit(durations, limit):\n    # your code here\n    pass\n",
 solution="def run_with_limit(durations, limit):\n    running = []   # [end_time, position]\n    order = []\n    nxt = 0\n    now = 0\n    while nxt < len(durations) and len(running) < limit:\n        running.append([durations[nxt], nxt])\n        nxt += 1\n    while running:\n        running.sort()\n        end, pos = running.pop(0)\n        now = end\n        order.append(pos)\n        if nxt < len(durations):\n            running.append([now + durations[nxt], nxt])\n            nxt += 1\n    return [now, order]\n",
 cases=[([3, 1, 2, 4], 2, [7, [1, 0, 2, 3]], True), ([], 3, [0, []]), ([5, 5, 5], 3, [5, [0, 1, 2]]), ([2, 2, 2], 1, [6, [0, 1, 2]]), ([4, 1, 1, 1], 2, [4, [1, 2, 3, 0]])],
 guided="def run_with_limit(durations, limit):\n    # Replace every ___ with real code, then run the tests.\n\n    running = []   # [end_time, position] for each call in flight\n    order = []\n    nxt = 0        # the next call waiting to start\n    now = 0\n    # Step 1: start the first `limit` calls at time 0.\n    while nxt < len(durations) and len(running) < limit:\n        running.append([durations[nxt], nxt])\n        nxt += 1\n    while running:\n        # Step 2: the earliest end time finishes next (sorting pairs breaks ties by position).\n        running.sort()\n        end, pos = running.pop(0)\n        now = end\n        order.append(pos)\n        # Step 3: a slot is free, so start the next waiting call now.\n        if nxt < len(durations):\n            running.append([___, nxt])\n            nxt += 1\n    return [now, order]\n",
 fills=["now + durations[nxt]"],
 learn=dict(concepts=[["Sorting pairs", "Lists of pairs sort by the first item, then the second, which gives the tie-break for free.", "sorted([[3, 0], [3, 2], [1, 1]])   # [[1, 1], [3, 0], [3, 2]]"], ["pop(0)", "Removes and returns the first item.", "q = [[1, 1], [3, 0]]\nq.pop(0)   # [1, 1]"]],
  byhand="Limit 2: calls 0 (3 s) and 1 (1 s) start. At 1 s call 1 finishes and call 2 (2 s) starts, ending at 3 s. At 3 s calls 0 and 2 both finish: 0 first. Call 3 (4 s) starts at 3 s and ends at 7 s.",
  why="Each call is started once and finished once. Sorting the few running calls each time is fine for a small limit; a heap makes it faster when the limit is large.",
  gotchas=[["gather without a limit", "`asyncio.gather` on 1,000 calls starts all 1,000 at once. Wrap each call in a semaphore."], ["One slow call holds a slot", "Give every call a timeout, so a stuck request doesn't quietly halve your throughput."]]))

add(id="optimistic_writes", title="Two Writers, One Record", topic="production", difficulty="easy", fn="optimistic_writes",
 prompt="Two workers read a record at version 3, both change it, and both save. Without care, the second save silently erases the first: a **lost update**, the classic race condition.\n\n**Optimistic concurrency** fixes it: each write says which version it read, and it's accepted only if the record is still at that version (then the version goes up by one). Otherwise it's rejected, and that writer must re-read and try again.\n\nGiven the record's starting `version` and `writes`, a list of `[writer, expected_version]` in arrival order, return `[accepted, rejected, final_version]`.",
 pattern="Compare-and-set: change only if the value is still what you saw.",
 target="one walk through the writes",
 realworld="Delta Lake commits work this way: if another job committed a conflicting change first, your commit fails and you retry. It's also how version-checked updates, HTTP ETags and Terraform state locking stop two writers from clobbering each other.",
 starter="def optimistic_writes(version, writes):\n    # your code here\n    pass\n",
 solution="def optimistic_writes(version, writes):\n    accepted, rejected = [], []\n    for writer, expected in writes:\n        if expected == version:\n            accepted.append(writer)\n            version += 1\n        else:\n            rejected.append(writer)\n    return [accepted, rejected, version]\n",
 cases=[(3, [["job_a", 3], ["job_b", 3], ["job_b", 4]], [["job_a", "job_b"], ["job_b"], 5], True), (1, [], [[], [], 1]), (0, [["x", 1]], [[], ["x"], 0]), (7, [["a", 7], ["b", 8], ["c", 9]], [["a", "b", "c"], [], 10])],
 guided="def optimistic_writes(version, writes):\n    # Replace every ___ with real code, then run the tests.\n\n    accepted, rejected = [], []\n    for writer, expected in writes:\n        # Step 1: is the record still at the version this writer read?\n        if ___:\n            accepted.append(writer)\n            # Step 2: a successful write bumps the version.\n            ___\n        else:\n            rejected.append(writer)\n    return [accepted, rejected, version]\n",
 fills=["expected == version", "version += 1"],
 learn=dict(concepts=[["Compare, then change", "Check a condition and update together in one step, so nothing can slip in between.", "if expected == version:\n    version += 1"]],
  byhand="Version 3. job_a expected 3: accepted, now version 4. job_b expected 3, but it's 4: rejected. job_b re-reads and tries with 4: accepted, version 5.",
  why="One walk through the writes.",
  gotchas=[["Check-then-act is the bug", "Reading, deciding in Python, then writing is two steps, and another writer can act in between. The check must happen inside the write itself, for example in the database's WHERE clause."], ["Retries need a fresh read", "A rejected writer must re-read the latest version and redo its change, not resend the old one."]]))

add(id="upsert_rows", title="Safe to Run Twice", topic="production", difficulty="medium", fn="upsert_rows",
 prompt="A job that saves results may be retried after a crash, so saving twice must not create duplicates. An **upsert** updates the row with the same key if it exists, and inserts it otherwise.\n\n`table` and `updates` are lists of dicts, and `key` names the field that identifies a row. Return the new table: existing rows stay in place (replaced by the update when keys match), new rows are added at the end in order, and if two updates share a key, the later one wins. Don't change `table` itself.",
 pattern="Index the existing rows by key, then each update either replaces in place or appends.",
 target="one walk through the table, one through the updates",
 realworld="This is Delta Lake's `MERGE INTO`. Writing results with MERGE on a stable key, instead of appending, means a retried job or a re-run notebook leaves the table exactly as one run would. That property is called idempotency.",
 starter="def upsert_rows(table, updates, key):\n    # your code here\n    pass\n",
 solution="def upsert_rows(table, updates, key):\n    out = [dict(r) for r in table]\n    where = {}\n    for i, r in enumerate(out):\n        where[r[key]] = i\n    for u in updates:\n        if u[key] in where:\n            out[where[u[key]]] = dict(u)\n        else:\n            where[u[key]] = len(out)\n            out.append(dict(u))\n    return out\n",
 cases=[([{"ticket_id": "T1", "status": "open"}, {"ticket_id": "T2", "status": "open"}], [{"ticket_id": "T2", "status": "closed"}, {"ticket_id": "T3", "status": "open"}], "ticket_id", [{"ticket_id": "T1", "status": "open"}, {"ticket_id": "T2", "status": "closed"}, {"ticket_id": "T3", "status": "open"}], True),
        ([], [], "id", []),
        ([{"id": 1, "v": "a"}], [{"id": 1, "v": "a"}], "id", [{"id": 1, "v": "a"}]),
        ([], [{"id": 5, "v": "x"}, {"id": 5, "v": "y"}], "id", [{"id": 5, "v": "y"}]),
        ([{"id": 1, "v": "a"}, {"id": 2, "v": "b"}], [{"id": 1, "v": "z"}], "id", [{"id": 1, "v": "z"}, {"id": 2, "v": "b"}])],
 guided="def upsert_rows(table, updates, key):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: copy the rows, so the caller's table is untouched.\n    out = [dict(r) for r in table]\n    # Step 2: key -> position, for instant lookups.\n    where = {}\n    for i, r in enumerate(out):\n        where[r[key]] = i\n    for u in updates:\n        if u[key] in where:\n            # Step 3: replace the existing row in place.\n            out[___] = dict(u)\n        else:\n            # Step 4: remember where the new row goes, then add it.\n            where[u[key]] = ___\n            out.append(dict(u))\n    return out\n",
 fills=["where[u[key]]", "len(out)"],
 learn=dict(concepts=[["Copying a list of dicts", "`[dict(r) for r in rows]` copies each row, so changes don't leak back to the original.", "copy = [dict(r) for r in rows]"], ["Key to position", "A dict from key to index finds the row to replace instantly.", "where = {'T2': 1}\nout[where['T2']]"]],
  byhand="T1 and T2 exist at positions 0 and 1. Update T2 → closed: replace position 1. T3 is new: add it at position 2. Run the same updates again and nothing changes.",
  why="One walk to index the table, one through the updates; each lookup is instant.",
  gotchas=[["Appending is not idempotent", "INSERT on retry doubles your rows. MERGE (or overwrite by partition) on a stable key doesn't."], ["Duplicate keys in the source", "If one batch contains the same key twice, MERGE on Delta fails because it can't tell which row wins. Remove duplicates in the source first."]]))

add(id="chunk_rows", title="Chunking at Scale", topic="production", difficulty="easy", fn="chunk_rows",
 prompt="To chunk millions of documents, Spark runs the same small function on every row, spread across many machines. That function must depend only on its own row.\n\nGiven `docs`, a list like `[{\"doc_id\": \"d1\", \"text\": \"...\"}]`, split each text into pieces of `size` characters (no overlap; the last may be shorter) and return one row per piece: `{\"doc_id\": ..., \"chunk_id\": doc_id + \"-\" + str(i), \"text\": piece}`, with `i` counting from 0 within each document. Documents with empty text produce no rows.",
 pattern="Map each input row to zero or more output rows, using only that row. Give every output a stable id built from its inputs.",
 target="one step per piece",
 realworld="In Spark this is a UDF plus `posexplode`, or `mapInPandas`. Because each row is handled on its own, Spark can split the work across the cluster. Ids like `d1-0` are deterministic, so re-running the job produces the same ids and a MERGE overwrites instead of duplicating.",
 starter="def chunk_rows(docs, size):\n    # your code here\n    pass\n",
 solution="def chunk_rows(docs, size):\n    out = []\n    for d in docs:\n        text = d[\"text\"]\n        for i, start in enumerate(range(0, len(text), size)):\n            out.append({\"doc_id\": d[\"doc_id\"], \"chunk_id\": d[\"doc_id\"] + \"-\" + str(i), \"text\": text[start:start + size]})\n    return out\n",
 cases=[([{"doc_id": "d1", "text": "abcdefg"}, {"doc_id": "d2", "text": "xy"}], 3, [{"doc_id": "d1", "chunk_id": "d1-0", "text": "abc"}, {"doc_id": "d1", "chunk_id": "d1-1", "text": "def"}, {"doc_id": "d1", "chunk_id": "d1-2", "text": "g"}, {"doc_id": "d2", "chunk_id": "d2-0", "text": "xy"}], True),
        ([], 5, []), ([{"doc_id": "e", "text": ""}], 4, []), ([{"doc_id": "a", "text": "abcd"}], 4, [{"doc_id": "a", "chunk_id": "a-0", "text": "abcd"}])],
 guided="def chunk_rows(docs, size):\n    # Replace every ___ with real code, then run the tests.\n\n    out = []\n    for d in docs:\n        text = d[\"text\"]\n        # Step 1: starts at 0, size, 2*size... and i counts the pieces.\n        for i, start in enumerate(range(0, len(text), ___)):\n            # Step 2: a stable id built from the document id and piece number.\n            out.append({\"doc_id\": d[\"doc_id\"], \"chunk_id\": ___, \"text\": text[start:start + size]})\n    return out\n",
 fills=["size", "d[\"doc_id\"] + \"-\" + str(i)"],
 learn=dict(concepts=[["enumerate over a range", "Counts the pieces while stepping through start positions.", "list(enumerate(range(0, 7, 3)))   # [(0, 0), (1, 3), (2, 6)]"], ["Building an id", "`str(i)` turns a number into text so it can be joined.", "'d1' + '-' + str(2)   # 'd1-2'"]],
  byhand="d1 is \"abcdefg\" with size 3: \"abc\" (d1-0), \"def\" (d1-1), \"g\" (d1-2). d2 is \"xy\": one piece, d2-0.",
  why="One step per piece, and every document is handled on its own, which is what lets Spark spread it out.",
  gotchas=[["Random ids break re-runs", "uuid4() gives new ids every run, so a re-run duplicates every chunk. Build ids from the data."], ["Python UDFs are slow row by row", "Prefer built-in Spark functions; when you need Python, a pandas UDF processes a batch of rows at a time and is much faster."]]))

def check():
    for p in P:
        for variant in ("solution", "guided"):
            code = p["solution"] if variant == "solution" else p["guided"].replace("# Replace every ___ with real code, then run the tests.", "#")
            if variant == "guided":
                for f in p["fills"]:
                    assert "___" in code, (p["id"], "too many fills"); code = code.replace("___", f, 1)
                assert "___" not in code, (p["id"], "unfilled")
            ns = {}; exec(code, ns); fn = ns[p["fn"]]
            for c in p["cases"]:
                sample = c[-1] is True
                body = c[:-1] if sample else c
                args, exp = list(body[:-1]), body[-1]
                got = fn(*json.loads(json.dumps(args)))
                assert got == exp, (p["id"], variant, args, exp, got)
    print("verified", len(P), "production problems")
if __name__ == "__main__":
    check()
