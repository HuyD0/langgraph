MODULE = ("production", "Production patterns", "Rate limits, retries, concurrency, race conditions, idempotency and data at scale: the habits that keep AI systems up.",
  ["token_bucket", "retry_wait", "run_with_limit", "optimistic_writes", "upsert_rows", "chunk_rows"])

L = {}
def lesson(id, title, learn, example, check, angle):
    L[id] = dict(title=title, learn=learn, example=example, check=check, angle=angle)

lesson("token_bucket", "Rate limiting before the 429",
 ["Model endpoints limit how many requests (and tokens) you can send per minute. Hitting the limit and retrying works, but it wastes calls and adds delay for everyone.",
  "A **token bucket** keeps you under the limit on your side: a budget that refills at a steady rate, with room for a short burst."],
 ("Rate 2 per second, bucket of 5", "# 5 requests at once: all go (the bucket empties)\n# the 6th must wait about half a second for a token to refill"),
 ("Your batch job sends 200 requests at once and gets 150 rate-limit errors. What's the better fix?",
  ["Retry them all immediately", "Limit the send rate on your side so you stay under the limit", "Use a bigger endpoint"], 1,
  "Retrying in a burst hits the same wall. Pacing the requests avoids the errors."),
 ("Token bucket", "Two numbers, tokens and last time checked; top up for the time that passed, then spend one. One walk through the requests. \"Design a rate limiter\" is a common system design interview question.",
  "\"A token bucket refills at a fixed rate up to a burst size; each request spends a token or waits, which smooths traffic but allows short bursts.\"", None))

lesson("retry_wait", "Retries done right",
 ["Retry only errors that can succeed later (429 rate limits, 503 overload, timeouts). If the server sends **Retry-After**, wait that long.",
  "Otherwise wait longer each time, with **jitter**: a random wait inside a growing window, so many clients don't all retry at the same moment. Always stop after a few attempts."],
 ("Without and with jitter", "# 50 workers, no jitter: all retry at exactly 2 s, 4 s, 8 s → repeated collisions\n# full jitter: each waits a random time in [0, 2], [0, 4], [0, 8] → spread out"),
 ("Fifty workers hit a rate limit at the same time and all retry after exactly 2 seconds. What happens?",
  ["They all succeed", "They all hit the limit again together", "Only one retries"], 1,
  "Identical waits make the retries collide. Jitter spreads them out."),
 ("Testable randomness", "A few steps per attempt. The engineering lesson is passing randomness in as an argument, so the function gives the same answer every time in a test.",
  "\"I honour Retry-After when present, otherwise use capped exponential backoff with full jitter, and inject the random source so it's testable.\"", None))

lesson("run_with_limit", "Many calls at once",
 ["Calling a model is mostly waiting. Running calls **concurrently** (several in flight at once) finishes a batch far sooner than one at a time.",
  "But unlimited concurrency triggers rate limits and overloads services. Use a **cap**: a semaphore lets at most N run at once, and the next starts the moment one finishes."],
 ("100 calls of 2 seconds each", "# one at a time:   200 seconds\n# 10 at a time:     20 seconds\n# all 100 at once:  2 seconds, if nothing pushes back (it will)"),
 ("You wrap 1,000 LLM calls in `asyncio.gather` with no limit. What's the likely result?",
  ["Fastest possible run", "A flood of rate-limit errors and timeouts", "Python runs them one at a time"], 1,
  "All 1,000 start at once. Add a semaphore or max_concurrency."),
 ("Bounded worker pool", "Repeatedly finish the earliest running call and start the next one: one step per call. With a large limit, a heap finds the earliest quickly; this is the \"task scheduler\" interview pattern.",
  "\"A semaphore caps calls in flight; when one finishes the next starts, so throughput is high without exceeding the rate limit.\"", None))

lesson("optimistic_writes", "Race conditions",
 ["A **race condition** happens when the result depends on timing. The classic one: two workers read the same record, both change it, both save, and the first change is silently lost.",
  "**Optimistic concurrency** prevents this: each write says which version it read, and is rejected if the record changed since. The loser re-reads and tries again."],
 ("A lost update", "# worker A reads count = 10, worker B reads count = 10\n# A saves 11, B saves 11  →  one increment is lost\n# with versions: B's write says \"I read version 7\", but it's now 8 → rejected, B retries"),
 ("Two agents update the same ticket at nearly the same time. Which approach avoids losing one update?",
  ["Read, change in Python, then write", "Write only if the version is still the one you read, otherwise retry", "Add a sleep before writing"], 1,
  "The check has to happen as part of the write. A sleep only makes the race rarer."),
 ("Compare-and-set", "One walk through the writes, accepting only those that saw the current version.",
  "\"I use optimistic concurrency: writes carry the version they read and fail if it changed, so the loser re-reads and retries instead of overwriting.\"", None))

lesson("upsert_rows", "Idempotent writes",
 ["Jobs get retried: a cluster dies, a notebook is re-run, a scheduler fires twice. **Idempotent** means running it twice leaves the same result as running it once.",
  "Appending rows is not idempotent; each retry duplicates them. **Upsert** on a stable key (Delta's `MERGE INTO`) is: matching rows are updated, new ones inserted."],
 ("Append vs merge on retry", "# run 1 appends 3 rows, crash, run 2 appends them again → 6 rows\n# run 1 merges 3 rows, crash, run 2 merges again       → still 3 rows"),
 ("A nightly job that writes eval results crashed halfway and was re-run. The table now has duplicate rows. What prevents this?",
  ["Run it less often", "Write with MERGE on a stable key", "Delete the table before each run"], 1,
  "MERGE makes the write idempotent. Deleting first leaves a window where the table is empty."),
 ("Index, then update or insert", "Build a key-to-position map in one walk, then each update is an instant lookup. The same \"hash map of what exists\" idea as Two Sum.",
  "\"I index existing rows by key, replace on match and append otherwise, so re-running the same batch is a no-op.\"", "two_sum"))

lesson("chunk_rows", "Transforming data at scale with Spark",
 ["Spark splits a table into **partitions** and runs your code on each partition in parallel across the cluster. That only works if your function handles **one row at a time** and doesn't depend on other rows or on shared state.",
  "Give every output a **stable id** built from its inputs, so re-running the job produces the same ids and a MERGE overwrites instead of duplicating."],
 ("One document becomes many chunk rows", "doc_id  text                 →  doc_id  chunk_id  text\nd1      \"abcdefg\" (size 3)     d1      d1-0      abc\n                                d1      d1-1      def\n                                d1      d1-2      g"),
 ("Your chunking job uses `uuid4()` for chunk ids and is re-run after a failure. What happens?",
  ["Nothing changes", "Every chunk gets a new id, so the index fills with duplicates", "Spark reuses the old ids"], 1,
  "Random ids differ every run. Ids built from the data are the same every time."),
 ("Map, then flatten", "Each input row produces zero or more output rows, independently: one step per piece. This independence is what lets the work spread across machines.",
  "\"I write a pure per-row function with deterministic ids, so Spark can parallelise it and re-runs are idempotent.\"", None))

STACK = {
 "token_bucket": ("LangChain: a client-side token bucket", "from langchain_core.rate_limiters import InMemoryRateLimiter\nlimiter = InMemoryRateLimiter(requests_per_second=2, check_every_n_seconds=0.1, max_bucket_size=5)\nllm = ChatDatabricks(endpoint=ENDPOINT, rate_limiter=limiter)"),
 "retry_wait": ("tenacity: backoff with jitter", "from tenacity import retry, stop_after_attempt, wait_random_exponential\n\n@retry(wait=wait_random_exponential(multiplier=1, max=30), stop=stop_after_attempt(5))\ndef call_model(messages):\n    return llm.invoke(messages)"),
 "run_with_limit": ("asyncio and LangChain: cap calls in flight", "sem = asyncio.Semaphore(8)\n\nasync def ask(question):\n    async with sem:\n        return await llm.ainvoke(question)\n\nanswers = await asyncio.gather(*(ask(q) for q in questions))\n# or: llm.batch(questions, config={\"max_concurrency\": 8})"),
 "optimistic_writes": ("SQL: a version-checked update", "UPDATE tickets\nSET status = 'closed', version = version + 1\nWHERE ticket_id = 'T2' AND version = 7;\n-- 0 rows updated means someone else changed it first: re-read and retry"),
 "upsert_rows": ("Delta Lake: MERGE INTO", "MERGE INTO main.support.eval_results AS t\nUSING new_results AS s\nON t.run_id = s.run_id AND t.example_id = s.example_id\nWHEN MATCHED THEN UPDATE SET *\nWHEN NOT MATCHED THEN INSERT *"),
 "chunk_rows": ("PySpark: a pandas UDF plus posexplode", "from pyspark.sql import functions as F, types as T\n\n@F.pandas_udf(T.ArrayType(T.StringType()))\ndef split_text(texts: pd.Series) -> pd.Series:\n    return texts.fillna(\"\").map(lambda t: [t[i:i + 1000] for i in range(0, len(t), 1000)])\n\nchunks = (spark.table(\"main.support.docs\")\n    .select(\"doc_id\", F.posexplode(split_text(\"text\")).alias(\"i\", \"text\"))\n    .withColumn(\"chunk_id\", F.concat_ws(\"-\", \"doc_id\", \"i\")))"),
}
