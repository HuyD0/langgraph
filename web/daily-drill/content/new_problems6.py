"""Reliability, agents, data, evals and craft exercises. Sample cases are marked with the string "S"."""
import json
P = []
def add(**k): P.append(k)
H = "    # Replace every ___ with real code, then run the tests.\n"

# ---------------- reliability ----------------
add(id="plan_calls", title="Work Within a Deadline", topic="reliability", difficulty="easy", fn="plan_calls",
 prompt="A request must answer within `deadline_ms`. It has optional steps to run in order, each `[name, expected_ms]`. Run a step only if it can finish within what's left of the deadline; otherwise skip it and try the next one, since a shorter later step may still fit.\n\nReturn `[ran, skipped, elapsed_ms]`.",
 pattern="Carry the remaining budget forward and check it before each step.",
 target="one walk through the steps",
 realworld="Timeouts stop one slow call from stalling everything. Passing the remaining time to each step (deadline propagation) means no step starts work it can't finish, which is how Google's SRE practices avoid cascading failures.",
 starter="def plan_calls(deadline_ms, steps):\n    # your code here\n    pass\n",
 solution="def plan_calls(deadline_ms, steps):\n    ran, skipped = [], []\n    elapsed = 0\n    for name, ms in steps:\n        if elapsed + ms <= deadline_ms:\n            ran.append(name)\n            elapsed += ms\n        else:\n            skipped.append(name)\n    return [ran, skipped, elapsed]\n",
 cases=[(2000, [["retrieve", 400], ["rerank", 900], ["generate", 1200], ["cite", 300]], [["retrieve", "rerank", "cite"], ["generate"], 1600], "S"),
        (100, [], [[], [], 0]), (500, [["a", 500]], [["a"], [], 500]), (300, [["a", 400], ["b", 100]], [["b"], ["a"], 100])],
 guided="def plan_calls(deadline_ms, steps):\n" + H + "\n    ran, skipped = [], []\n    elapsed = 0\n    for name, ms in steps:\n        # Step 1: does it fit in what's left?\n        if ___:\n            ran.append(name)\n            elapsed += ms\n        else:\n            ___\n    return [ran, skipped, elapsed]\n",
 fills=["elapsed + ms <= deadline_ms", "skipped.append(name)"],
 learn=dict(concepts=[["A budget that shrinks", "Keep how much you've used, and compare against the limit before each step.", "if used + cost <= limit:\n    used += cost"]],
  byhand="2,000 ms budget. retrieve 400 (400 used). rerank 900 (1,300). generate 1,200 would make 2,500: skip. cite 300 (1,600): runs.",
  why="One walk through the steps.",
  gotchas=[["A skipped step needs a fallback", "If generation can't fit, return the retrieved passages or a short canned answer rather than nothing."], ["Every call needs a timeout", "Libraries often default to waiting forever. Set one on every HTTP and model call."]]))

add(id="circuit_breaker", title="Stop Calling a Failing Service", topic="reliability", difficulty="medium", fn="circuit_breaker",
 prompt="A **circuit breaker** stops calling an endpoint that keeps failing, so you fail fast and fall back instead of piling on.\n\n`events` is a list of `[time, ok]`: a call attempted at `time` and whether it would succeed. The breaker starts **closed**. After `threshold` failures in a row it **opens** at that failure's time. While open, calls before `opened_at + cooldown` are blocked (not sent). The first call at or after that time is a trial: if it succeeds the breaker closes and the failure count resets; if it fails, the breaker opens again at that time.\n\nReturn, for each event, `\"ok\"`, `\"fail\"` or `\"blocked\"`.",
 pattern="A small state machine: track the state, the failure count and when it opened; decide each event from those.",
 target="one walk through the events",
 realworld="Without a breaker, every request waits for a dead endpoint to time out, and retries make it worse. With one, you switch to a fallback (a cheaper model, a cached answer) immediately, and check back after a cooldown.",
 starter="def circuit_breaker(events, threshold, cooldown):\n    # your code here\n    pass\n",
 solution="def circuit_breaker(events, threshold, cooldown):\n    out = []\n    failures = 0\n    opened_at = None\n    for t, ok in events:\n        if opened_at is not None and t < opened_at + cooldown:\n            out.append(\"blocked\")\n            continue\n        if ok:\n            out.append(\"ok\")\n            failures = 0\n            opened_at = None\n        else:\n            out.append(\"fail\")\n            failures += 1\n            if opened_at is not None or failures >= threshold:\n                opened_at = t\n    return out\n",
 cases=[([[0, False], [1, False], [2, False], [3, True], [12, False], [13, True], [25, True]], 3, 10, ["fail", "fail", "fail", "blocked", "fail", "blocked", "ok"], "S"),
        ([], 2, 5, []), ([[0, True], [1, False], [2, True], [3, False]], 2, 5, ["ok", "fail", "ok", "fail"]),
        ([[0, False], [1, False], [5, True], [6, True]], 2, 4, ["fail", "fail", "ok", "ok"])],
 guided="def circuit_breaker(events, threshold, cooldown):\n" + H + "\n    out = []\n    failures = 0       # failures in a row\n    opened_at = None   # when the breaker last opened (None = closed)\n    for t, ok in events:\n        # Step 1: open and still cooling down? Don't send it.\n        if opened_at is not None and ___:\n            out.append(\"blocked\")\n            continue\n        if ok:\n            # Step 2: a success closes the breaker and resets the count.\n            out.append(\"ok\")\n            failures = 0\n            opened_at = None\n        else:\n            out.append(\"fail\")\n            failures += 1\n            # Step 3: a failed trial, or too many failures in a row, opens it (again).\n            if opened_at is not None or ___:\n                opened_at = t\n    return out\n",
 fills=["t < opened_at + cooldown", "failures >= threshold"],
 learn=dict(concepts=[["State in a few variables", "A state machine can be just two variables you update as events arrive.", "failures = 0\nopened_at = None"], ["continue", "Skip the rest of this loop turn.", "if blocked:\n    continue"]],
  byhand="Three failures at 0, 1, 2: the breaker opens at 2. The call at 3 is before 12: blocked. At 12 the trial fails: open again at 12. At 13 (before 22): blocked. At 25 the trial succeeds: closed.",
  why="One walk through the events.",
  gotchas=[["Have a fallback ready", "A breaker without a fallback just fails faster. Decide what users get instead: a cheaper model, a cached answer, or a clear message."], ["Per endpoint, not global", "Keep one breaker per dependency, so a broken reranker doesn't block the main model."]]))

add(id="burn_rate", title="Error Budgets", topic="reliability", difficulty="easy", fn="burn_rate",
 prompt="An SLO (service level objective) like 99.5% success means you're allowed 0.5% failures: your **error budget**. The **burn rate** says how fast you're spending it: the error rate divided by the allowed error rate. 1.0 means you'll use exactly the budget; 10 means ten times too fast.\n\nGiven `errors` and `total` requests in a window, the `slo` (like 0.995) and an `alert_at` burn rate, return `[burn, alert]`, with burn rounded to 1 place. With no requests, return `[0.0, False]`.",
 pattern="Turn two raw counts into a ratio against a target, then compare to a threshold.",
 target="a few arithmetic steps",
 realworld="Alerting on raw error counts pages people at 3am for noise. Alerting on burn rate pages only when the budget is really at risk, which is the practice Google's SRE book describes. On Databricks you'd compute it from system tables or traces with a SQL alert.",
 starter="def burn_rate(errors, total, slo, alert_at):\n    # your code here\n    pass\n",
 solution="def burn_rate(errors, total, slo, alert_at):\n    if total == 0:\n        return [0.0, False]\n    burn = round((errors / total) / (1 - slo), 1)\n    return [burn, burn >= alert_at]\n",
 cases=[(72, 1000, 0.995, 10, [14.4, True], "S"), (0, 0, 0.99, 2, [0.0, False]), (5, 1000, 0.995, 2, [1.0, False]), (30, 2000, 0.99, 1.5, [1.5, True])],
 guided="def burn_rate(errors, total, slo, alert_at):\n" + H + "\n    if total == 0:\n        return [0.0, False]\n    # Step 1: error rate divided by the allowed error rate (1 - slo).\n    burn = round((errors / total) / ___, 1)\n    # Step 2: alert when it's burning at least that fast.\n    return [burn, ___]\n",
 fills=["(1 - slo)", "burn >= alert_at"],
 learn=dict(concepts=[["Division for rates", "errors / total gives the share that failed.", "72 / 1000   # 0.072"]],
  byhand="72 errors in 1,000 is 7.2% failing. The SLO allows 0.5%. 7.2 / 0.5 = 14.4 times too fast: alert.",
  why="Two divisions.",
  gotchas=[["Pick the window with the threshold", "A high burn rate over 5 minutes means \"page now\"; a lower one over 6 hours means \"look tomorrow\". Teams use both."], ["Define failure for AI", "For an AI feature, a 200 response with a wrong answer is also a failure. Count judge failures from production monitoring, not just HTTP errors."]]))

# ---------------- agents ----------------
add(id="approval_run", title="Pause for a Human", topic="agents", difficulty="medium", fn="approval_run",
 prompt="An agent runs `steps` in order, each `[name, risky]`. Before a risky step it pauses for a person, unless `decisions` (a dict from step name to `\"approve\"` or `\"reject\"`) already holds an answer for it.\n\nGo through the steps. A safe step runs. A risky step: with `\"approve\"` it runs; with `\"reject\"` the run stops; with no decision the run pauses there.\n\nReturn `{\"status\": \"done\" | \"paused\" | \"stopped\", \"ran\": [...], \"at\": name or None}`, where `at` is the step it paused or stopped on.",
 pattern="Walk the steps; at each risky one, look up a decision and either continue, stop or pause.",
 target="one walk through the steps",
 realworld="This is human-in-the-loop in LangGraph: `interrupt()` pauses the graph, a checkpointer saves its state under a `thread_id`, and `Command(resume=...)` continues it later, even after a restart. Running the same function again with the decision filled in is exactly how resuming works.",
 starter="def approval_run(steps, decisions):\n    # your code here\n    pass\n",
 solution="def approval_run(steps, decisions):\n    ran = []\n    for name, risky in steps:\n        if risky:\n            d = decisions.get(name)\n            if d is None:\n                return {\"status\": \"paused\", \"ran\": ran, \"at\": name}\n            if d == \"reject\":\n                return {\"status\": \"stopped\", \"ran\": ran, \"at\": name}\n        ran.append(name)\n    return {\"status\": \"done\", \"ran\": ran, \"at\": None}\n",
 cases=[([["look_up_order", False], ["issue_refund", True], ["email_customer", False]], {}, {"status": "paused", "ran": ["look_up_order"], "at": "issue_refund"}, "S"),
        ([["look_up_order", False], ["issue_refund", True], ["email_customer", False]], {"issue_refund": "approve"}, {"status": "done", "ran": ["look_up_order", "issue_refund", "email_customer"], "at": None}),
        ([["a", True]], {"a": "reject"}, {"status": "stopped", "ran": [], "at": "a"}),
        ([], {}, {"status": "done", "ran": [], "at": None})],
 guided="def approval_run(steps, decisions):\n" + H + "\n    ran = []\n    for name, risky in steps:\n        if risky:\n            d = decisions.get(name)\n            # Step 1: no decision yet: pause here.\n            if d is None:\n                return {\"status\": \"paused\", \"ran\": ran, \"at\": name}\n            # Step 2: a person said no: stop.\n            if ___:\n                return {\"status\": \"stopped\", \"ran\": ran, \"at\": name}\n        ran.append(name)\n    return {\"status\": ___, \"ran\": ran, \"at\": None}\n",
 fills=["d == \"reject\"", "\"done\""],
 learn=dict(concepts=[["Returning early", "`return` inside a loop ends the function right there.", "for s in steps:\n    if must_stop:\n        return result"]],
  byhand="look_up_order is safe: run it. issue_refund is risky and there's no decision: pause there. Run again with issue_refund approved and everything runs.",
  why="One walk through the steps.",
  gotchas=[["Steps before the pause may run twice", "When LangGraph resumes, the node containing interrupt() runs again from its start. Keep side effects after the interrupt, or make them idempotent."], ["Show the person what they're approving", "Pass the action and its arguments to the interrupt, so the reviewer sees \"refund $250 on A-1042\", not just \"approve?\"."]]))

add(id="assemble_stream", title="Put a Stream Back Together", topic="agents", difficulty="medium", fn="assemble_stream",
 prompt="Streaming sends a reply in small pieces as it's generated. `chunks` is a list of events: `[\"text\", piece]` adds to the visible reply; `[\"tool_start\", name]` begins a tool call; `[\"tool_args\", piece]` adds to the current tool call's arguments; `[\"tool_end\", \"\"]` finishes it.\n\nReturn `[text, tool_calls]`: the full reply text, and a list of `[name, arguments]` for each finished tool call, in order.",
 pattern="Accumulate pieces into buffers, and close a buffer when its end marker arrives.",
 target="one walk through the chunks",
 realworld="Users see the first words in a few hundred milliseconds instead of waiting for the whole answer. LangGraph streams with `stream_mode=\"messages\"` (token pieces) or `\"updates\"` (node results), and `ResponsesAgent.predict_stream` streams from a Databricks endpoint. Tool-call arguments arrive in pieces too, and are only valid JSON once complete.",
 starter="def assemble_stream(chunks):\n    # your code here\n    pass\n",
 solution="def assemble_stream(chunks):\n    text = \"\"\n    calls = []\n    name, args = None, \"\"\n    for kind, piece in chunks:\n        if kind == \"text\":\n            text += piece\n        elif kind == \"tool_start\":\n            name, args = piece, \"\"\n        elif kind == \"tool_args\":\n            args += piece\n        elif kind == \"tool_end\":\n            calls.append([name, args])\n            name, args = None, \"\"\n    return [text, calls]\n",
 cases=[([["text", "Let me "], ["text", "check."], ["tool_start", "lookup_order"], ["tool_args", "{\"order_id\": "], ["tool_args", "\"A-1042\"}"], ["tool_end", ""]], ["Let me check.", [["lookup_order", "{\"order_id\": \"A-1042\"}"]]], "S"),
        ([], ["", []]), ([["text", "Hi"]], ["Hi", []]),
        ([["tool_start", "a"], ["tool_end", ""], ["tool_start", "b"], ["tool_args", "{}"], ["tool_end", ""]], ["", [["a", ""], ["b", "{}"]]])],
 guided="def assemble_stream(chunks):\n" + H + "\n    text = \"\"\n    calls = []\n    name, args = None, \"\"   # the tool call being built\n    for kind, piece in chunks:\n        if kind == \"text\":\n            text += piece\n        elif kind == \"tool_start\":\n            name, args = piece, \"\"\n        elif kind == \"tool_args\":\n            # Step 1: arguments arrive in pieces.\n            ___\n        elif kind == \"tool_end\":\n            # Step 2: the call is complete: save it and reset.\n            calls.append(___)\n            name, args = None, \"\"\n    return [text, calls]\n",
 fills=["args += piece", "[name, args]"],
 learn=dict(concepts=[["Adding to a string", "`+=` appends text.", "s = 'Let me '\ns += 'check.'"], ["Tuple-style unpacking in a loop", "Each event is a pair, so name both parts.", "for kind, piece in chunks:\n    ..."]],
  byhand="Two text pieces make \"Let me check.\". tool_start opens lookup_order; two argument pieces build {\"order_id\": \"A-1042\"}; tool_end saves it.",
  why="One walk through the chunks.",
  gotchas=[["Don't parse arguments early", "Half a JSON object isn't valid JSON. Parse tool arguments only when the call ends."], ["Streaming changes error handling", "An error can arrive after you've already shown half an answer. Decide how the UI shows a stream that fails midway."]]))

# ---------------- data ----------------
add(id="process_new", title="Process Only What's New", topic="production", difficulty="medium", fn="process_new",
 prompt="A job reads from an event log. It remembers the last `offset` it processed, and ignores events older than a **watermark** (too late to count).\n\n`events` is a list of `[offset, event_time, value]`. Process events with offset greater than the saved `offset`. Of those, keep the ones with `event_time >= watermark` and drop the late ones. Return `[kept_values, dropped_values, new_offset]`, where new_offset is the highest offset read (or the old one if nothing was new).",
 pattern="Remember where you got to; resume from there; decide what's too late.",
 target="one walk through the events",
 realworld="This is what Structured Streaming's `checkpointLocation` (the saved offset) and `withWatermark` (the late cutoff) do. With `trigger(availableNow=True)` the same job runs as a cheap batch that only processes new data each time.",
 starter="def process_new(events, offset, watermark):\n    # your code here\n    pass\n",
 solution="def process_new(events, offset, watermark):\n    kept, dropped = [], []\n    new_offset = offset\n    for off, t, value in events:\n        if off <= offset:\n            continue\n        new_offset = max(new_offset, off)\n        if t >= watermark:\n            kept.append(value)\n        else:\n            dropped.append(value)\n    return [kept, dropped, new_offset]\n",
 cases=[([[1, 100, "a"], [2, 105, "b"], [3, 90, "c"], [4, 120, "d"]], 1, 100, [["b", "d"], ["c"], 4], "S"),
        ([], 7, 0, [[], [], 7]), ([[1, 5, "x"]], 3, 0, [[], [], 3]), ([[5, 50, "p"], [6, 49, "q"]], 4, 50, [["p"], ["q"], 6])],
 guided="def process_new(events, offset, watermark):\n" + H + "\n    kept, dropped = [], []\n    new_offset = offset\n    for off, t, value in events:\n        # Step 1: already processed last time? skip it.\n        if ___:\n            continue\n        new_offset = max(new_offset, off)\n        # Step 2: on time, or too late?\n        if ___:\n            kept.append(value)\n        else:\n            dropped.append(value)\n    return [kept, dropped, new_offset]\n",
 fills=["off <= offset", "t >= watermark"],
 learn=dict(concepts=[["max to track the highest", "`max(a, b)` keeps the larger, so it ratchets upward.", "best = max(best, off)"]],
  byhand="Saved offset 1, so skip event 1. Event 2 at time 105: keep b. Event 3 at 90 is before the watermark 100: drop c. Event 4: keep d. The new offset is 4.",
  why="One walk through the events.",
  gotchas=[["Never delete the checkpoint casually", "Deleting a stream's checkpoint makes it reprocess everything from the start, or skip data, depending on settings."], ["Late data is a business decision", "How late is too late? An hour for dashboards, never for billing. Pick the watermark with the people who use the data."]]))

add(id="validate_rows", title="Data Contracts", topic="production", difficulty="medium", fn="validate_rows",
 prompt="Before loading rows into a table, check them against a schema: `schema` maps each column to `\"str\"`, `\"int\"` or `\"float\"` (an int is fine where a float is expected, but `True`/`False` never count as numbers).\n\nA row is good if every schema column is present and has the right type. Bad rows go to quarantine instead of breaking the load. Also collect any column names that aren't in the schema: new columns someone started sending.\n\nReturn `[good_rows, quarantined_rows, new_columns]`, with new_columns sorted and without repeats.",
 pattern="Check each row against a contract; route failures aside instead of crashing; report surprises.",
 target="one walk through the rows",
 realworld="Lakeflow pipeline expectations do this (`EXPECT ... ON VIOLATION DROP ROW`, or fail the update), and Delta's `mergeSchema` decides whether new columns are allowed in. Quarantining bad rows keeps one malformed record from stopping the whole pipeline.",
 starter="def validate_rows(rows, schema):\n    # your code here\n    pass\n",
 solution="def type_ok(value, kind):\n    name = type(value).__name__\n    if kind == \"float\":\n        return name in (\"float\", \"int\")\n    return name == kind\n\ndef validate_rows(rows, schema):\n    good, bad, extra = [], [], set()\n    for r in rows:\n        for col in r:\n            if col not in schema:\n                extra.add(col)\n        ok = all(col in r and type_ok(r[col], kind) for col, kind in schema.items())\n        (good if ok else bad).append(r)\n    return [good, bad, sorted(extra)]\n",
 cases=[([{"ticket_id": "T1", "minutes": 12, "score": 0.9}, {"ticket_id": "T2", "minutes": "twelve", "score": 0.8}, {"ticket_id": "T3", "minutes": 5, "score": 1, "channel": "chat"}], {"ticket_id": "str", "minutes": "int", "score": "float"},
         [[{"ticket_id": "T1", "minutes": 12, "score": 0.9}, {"ticket_id": "T3", "minutes": 5, "score": 1, "channel": "chat"}], [{"ticket_id": "T2", "minutes": "twelve", "score": 0.8}], ["channel"]], "S"),
        ([], {"a": "int"}, [[], [], []]), ([{"a": True}], {"a": "int"}, [[], [{"a": True}], []]), ([{"b": 1}], {"a": "int"}, [[], [{"b": 1}], ["b"]])],
 guided="def type_ok(value, kind):\n    # type(x).__name__ is 'str', 'int', 'float' or 'bool' - so True isn't an int here.\n    name = type(value).__name__\n    if kind == \"float\":\n        return name in (\"float\", \"int\")\n    return name == kind\n\n\ndef validate_rows(rows, schema):\n" + H + "\n    good, bad, extra = [], [], set()\n    for r in rows:\n        # Step 1: note any column the schema doesn't know.\n        for col in r:\n            if ___:\n                extra.add(col)\n        # Step 2: every schema column present, with the right type.\n        ok = all(col in r and ___ for col, kind in schema.items())\n        (good if ok else bad).append(r)\n    return [good, bad, sorted(extra)]\n",
 fills=["col not in schema", "type_ok(r[col], kind)"],
 learn=dict(concepts=[["all", "True only if the condition holds for every item.", "all(x > 0 for x in [1, 2, 3])   # True"], ["A set for unique names", "Adding the same name twice keeps one copy.", "s = set()\ns.add('channel'); s.add('channel')   # {'channel'}"]],
  byhand="T1 matches the schema: good. T2's minutes is text: quarantine. T3 is fine (an int is OK for score) but has an extra column, channel: good, and report channel.",
  why="One walk through the rows, checking each column.",
  gotchas=[["Quarantine, then look", "A quarantine table nobody reads is a slow data leak. Alert when it grows."], ["Schema changes need an owner", "Turning on automatic schema merging means any upstream typo becomes a new column. Decide who approves new columns."]]))

add(id="skew_report", title="Spot a Skewed Key", topic="production", difficulty="medium", fn="skew_report",
 prompt="Spark sends all rows with the same key to the same partition. If one key has most of the rows, one task does most of the work while the others sit idle: **skew**.\n\n`counts` is a list of `[key, rows]`. Each key goes to partition `sum of its character codes % partitions` (use `ord(c)` for a character's code). Return `[imbalance, heaviest_key]`: the busiest partition's rows divided by the average rows per partition, rounded to 1 place, and the key with the most rows (the first one listed wins a tie).",
 pattern="Group into buckets, then compare the biggest bucket with the average.",
 target="one walk through the keys",
 realworld="A join or groupBy on a skewed key (one huge customer, a null key, \"unknown\") makes one task run for an hour while 199 finish in a minute. Adaptive Query Execution handles many skewed joins automatically; otherwise salt the hot key or handle it separately.",
 starter="def skew_report(counts, partitions):\n    # your code here\n    pass\n",
 solution="def skew_report(counts, partitions):\n    load = [0] * partitions\n    total = 0\n    heaviest, most = None, -1\n    for key, rows in counts:\n        p = sum(ord(c) for c in key) % partitions\n        load[p] += rows\n        total += rows\n        if rows > most:\n            heaviest, most = key, rows\n    if total == 0:\n        return [0.0, heaviest]\n    return [round(max(load) / (total / partitions), 1), heaviest]\n",
 cases=[([["acme", 9000], ["bolt", 300], ["cora", 350], ["dyna", 350]], 4, [3.6, "acme"], "S"),
        ([], 3, [0.0, None]), ([["a", 10], ["b", 10]], 2, [1.0, "a"]), ([["x", 5]], 1, [1.0, "x"])],
 guided="def skew_report(counts, partitions):\n" + H + "\n    load = [0] * partitions   # rows per partition\n    total = 0\n    heaviest, most = None, -1\n    for key, rows in counts:\n        # Step 1: which partition does this key land in?\n        p = sum(ord(c) for c in key) % ___\n        load[p] += rows\n        total += rows\n        if rows > most:\n            heaviest, most = key, rows\n    if total == 0:\n        return [0.0, heaviest]\n    # Step 2: busiest partition compared with the average.\n    return [round(___ / (total / partitions), 1), heaviest]\n",
 fills=["partitions", "max(load)"],
 learn=dict(concepts=[["ord", "The number behind a character.", "ord('a')   # 97"], ["A list of zeros", "`[0] * 4` makes four counters.", "load = [0] * 4"]],
  byhand="10,000 rows over 4 partitions is 2,500 on average. acme alone is 9,000, so its partition holds at least 9,000: about 3.6 times the average. One task does most of the work.",
  why="One walk through the keys.",
  gotchas=[["Nulls are a hot key", "Rows with a null join key all land together. Filter or handle them separately."], ["Salting trades work for balance", "Adding a random suffix to a hot key spreads it out, but the other side of the join must be repeated for each suffix."]]))

# ---------------- evals / rag ----------------
add(id="judge_agreement", title="Can You Trust Your Judge?", topic="evals", difficulty="easy", fn="judge_agreement",
 prompt="An LLM judge grades answers pass/fail. Before trusting it, compare it with human labels on the same examples. `judge` and `human` are lists of `True`/`False`.\n\nReturn `[pass_agreement, fail_agreement, trusted]`: of the answers humans passed, the share the judge also passed; of the answers humans failed, the share the judge also failed (each rounded to 2 places, `0.0` if there are none); and `trusted` is `True` only if both are at least `0.9`.",
 pattern="Split by the true label, then measure agreement on each side separately.",
 target="one walk through the pairs",
 realworld="A judge that passes everything agrees with humans 95% of the time when 95% of answers are good, and catches no failures at all. Checking each side separately, the way Hamel Husain recommends, exposes that. MLflow's `make_judge` judges can then be aligned to your experts' labels.",
 starter="def judge_agreement(judge, human):\n    # your code here\n    pass\n",
 solution="def judge_agreement(judge, human):\n    pos = neg = pos_ok = neg_ok = 0\n    for j, h in zip(judge, human):\n        if h:\n            pos += 1\n            if j:\n                pos_ok += 1\n        else:\n            neg += 1\n            if not j:\n                neg_ok += 1\n    tpr = round(pos_ok / pos, 2) if pos else 0.0\n    tnr = round(neg_ok / neg, 2) if neg else 0.0\n    return [tpr, tnr, tpr >= 0.9 and tnr >= 0.9]\n",
 cases=[([True, True, True, True, True, True, True, True, True, True], [True, True, True, True, True, True, True, True, False, False], [1.0, 0.0, False], "S"),
        ([], [], [0.0, 0.0, False]), ([True, False, True, False], [True, False, True, False], [1.0, 1.0, True]),
        ([True, True, False, False, False], [True, False, True, False, False], [0.5, 0.67, False])],
 guided="def judge_agreement(judge, human):\n" + H + "\n    pos = neg = pos_ok = neg_ok = 0\n    for j, h in zip(judge, human):\n        if h:\n            pos += 1\n            if j:\n                pos_ok += 1\n        else:\n            # Step 1: humans failed it; did the judge fail it too?\n            neg += 1\n            if ___:\n                neg_ok += 1\n    tpr = round(pos_ok / pos, 2) if pos else 0.0\n    tnr = round(neg_ok / neg, 2) if neg else 0.0\n    # Step 2: trusted only if both sides agree well.\n    return [tpr, tnr, ___]\n",
 fills=["not j", "tpr >= 0.9 and tnr >= 0.9"],
 learn=dict(concepts=[["Counting with conditions", "Several counters updated in one loop.", "pos = neg = 0"]],
  byhand="Humans passed 8 and failed 2. The judge passed all 10: it agrees on all 8 passes (1.0) but caught neither failure (0.0). Not trustworthy, despite agreeing 80% of the time overall.",
  why="One walk through the pairs.",
  gotchas=[["Label a few dozen yourself first", "Error analysis starts with reading real outputs and labelling them. That's where the failure categories, and the judge's rubric, come from."], ["Re-check after changing the judge", "A new judge prompt or model needs re-checking against the same labels before its scores mean anything."]]))

add(id="mix_shift", title="Notice Drift", topic="evals", difficulty="easy", fn="mix_shift",
 prompt="Your eval set reflects last quarter's questions. Production traffic changes. Compare the mix of question categories: `baseline` and `current` are lists of counts per category, in the same category order.\n\nTurn each into shares (count divided by its total). The shift is half the sum of the absolute differences between matching shares: 0 means the same mix, 1 means completely different. Return it rounded to 2 places. If either total is 0, return `0.0`.",
 pattern="Normalise both to shares, then compare share by share.",
 target="one walk through the categories",
 realworld="When the mix of real questions drifts from your eval set, eval scores stop predicting production quality. MLflow 3 production monitoring runs scorers on live traces; comparing category mix is a cheap first alarm that the eval set needs refreshing.",
 starter="def mix_shift(baseline, current):\n    # your code here\n    pass\n",
 solution="def mix_shift(baseline, current):\n    tb, tc = sum(baseline), sum(current)\n    if tb == 0 or tc == 0:\n        return 0.0\n    diff = 0\n    for b, c in zip(baseline, current):\n        diff += abs(b / tb - c / tc)\n    return round(diff / 2, 2)\n",
 cases=[([500, 300, 200], [200, 300, 500], 0.3, "S"), ([1, 2], [0, 0], 0.0), ([10, 10], [20, 20], 0.0), ([1, 0], [0, 1], 1.0)],
 guided="def mix_shift(baseline, current):\n" + H + "\n    tb, tc = sum(baseline), sum(current)\n    if tb == 0 or tc == 0:\n        return 0.0\n    diff = 0\n    for b, c in zip(baseline, current):\n        # Step 1: compare shares, not raw counts.\n        diff += abs(___)\n    # Step 2: half the total difference.\n    return round(___, 2)\n",
 fills=["b / tb - c / tc", "diff / 2"],
 learn=dict(concepts=[["abs", "Distance from zero, ignoring the sign.", "abs(-0.3)   # 0.3"]],
  byhand="Baseline shares: 50%, 30%, 20%. Current: 20%, 30%, 50%. Differences: 30, 0, 30 points. Half of 60 is 30: a 0.3 shift.",
  why="One walk through the categories.",
  gotchas=[["Categories come from somewhere", "To compare mixes you need to categorise questions, often with a cheap classifier or ai_classify. Keep that step stable, or it causes drift itself."], ["Refresh the eval set on purpose", "When the mix shifts, sample new real questions into the eval set, and keep the old ones to catch regressions."]]))

add(id="rrf", title="Combine Two Rankings", topic="rag", difficulty="medium", fn="rrf",
 prompt="Hybrid search runs a keyword search and a vector search, then merges their rankings. **Reciprocal rank fusion** gives each document `1 / (k + rank)` from each list it appears in (rank counts from 1), and adds them up.\n\n`rankings` is a list of ranked lists of document ids. Return all the ids, highest total score first; break ties alphabetically.",
 pattern="Score by position, add across lists, sort by score with a tie-break.",
 target="one step per ranked item, then a sort",
 realworld="Keyword search finds exact terms (error codes, product names); vector search finds meaning. Fusing them by rank avoids comparing scores on different scales. Databricks Vector Search does hybrid search with `query_type=\"HYBRID\"`.",
 starter="def rrf(rankings, k):\n    # your code here\n    pass\n",
 solution="def rrf(rankings, k):\n    score = {}\n    for ranking in rankings:\n        for rank, doc in enumerate(ranking, start=1):\n            score[doc] = score.get(doc, 0) + 1 / (k + rank)\n    return sorted(score, key=lambda d: (-score[d], d))\n",
 cases=[([["d3", "d1", "d7"], ["d1", "d9", "d3"]], 60, ["d1", "d3", "d9", "d7"], "S"), ([], 60, []), ([["a", "b"]], 1, ["a", "b"]), ([["a", "b"], ["b", "a"]], 60, ["a", "b"])],
 guided="def rrf(rankings, k):\n" + H + "\n    score = {}\n    for ranking in rankings:\n        # Step 1: enumerate(..., start=1) gives ranks 1, 2, 3...\n        for rank, doc in enumerate(ranking, start=1):\n            score[doc] = score.get(doc, 0) + ___\n    # Step 2: highest score first, then alphabetical.\n    return sorted(score, key=lambda d: (___, d))\n",
 fills=["1 / (k + rank)", "-score[d]"],
 learn=dict(concepts=[["enumerate with start", "`start=1` counts from 1 instead of 0.", "list(enumerate(['a', 'b'], start=1))   # [(1, 'a'), (2, 'b')]"], ["Sorting with a key", "`key` says what to sort by; a minus sign puts the biggest first.", "sorted(['a', 'b'], key=lambda d: (-scores[d], d))"]],
  byhand="With k = 60: d1 is 2nd in one list and 1st in the other, so it scores highest. d3 is 1st and 3rd, next. d9 and d7 appear once each, and d9's rank is better.",
  why="One step per ranked item, then one sort.",
  gotchas=[["Measure before and after", "Hybrid search usually helps on queries with exact terms. Check recall@k on your own eval set rather than assuming."], ["Rerankers come after fusion", "A reranker model re-scores the fused top results more carefully, at extra latency and cost."]]))

# ---------------- craft ----------------
add(id="parse_labels", title="Test the Logic, Fake the Model", topic="testing", difficulty="easy", fn="parse_labels",
 prompt="Good code keeps the model call separate from the logic around it, so the logic can be tested with canned replies instead of real (slow, random, costly) model calls.\n\nHere, `replies` are what a classifier model returned. Clean each one: lowercase, trim spaces, and remove a trailing `.`. If the result is in `allowed`, keep it; otherwise use `\"unknown\"`. Return the list of labels.",
 pattern="Make the messy outside world an input, so the logic is a pure function you can test.",
 target="one walk through the replies",
 realworld="LangChain ships `GenericFakeChatModel` for this: it returns scripted replies, so unit tests run fast, free and the same every time. Test the parsing, routing and error handling with fakes; test the model's quality with evals.",
 starter="def parse_labels(replies, allowed):\n    # your code here\n    pass\n",
 solution="def parse_labels(replies, allowed):\n    out = []\n    for r in replies:\n        label = r.strip().lower()\n        if label.endswith(\".\"):\n            label = label[:-1]\n        out.append(label if label in allowed else \"unknown\")\n    return out\n",
 cases=[(["Billing.", " refund ", "I think it's billing", "SHIPPING"], ["billing", "refund", "shipping"], ["billing", "refund", "unknown", "shipping"], "S"), ([], ["a"], []), (["."], ["a"], ["unknown"]), (["a.", "b"], ["a"], ["a", "unknown"])],
 guided="def parse_labels(replies, allowed):\n" + H + "\n    out = []\n    for r in replies:\n        # Step 1: clean it up.\n        label = r.strip().___()\n        if label.endswith(\".\"):\n            label = label[:-1]\n        # Step 2: anything unexpected becomes \"unknown\", never a crash.\n        out.append(___)\n    return out\n",
 fills=["lower", "label if label in allowed else \"unknown\""],
 learn=dict(concepts=[["strip and lower", "Trim spaces and lowercase in one line.", "' Billing '.strip().lower()   # 'billing'"], ["endswith", "Checks how a string ends.", "'billing.'.endswith('.')   # True"]],
  byhand="\"Billing.\" becomes billing: allowed. \" refund \" becomes refund. \"I think it's billing\" isn't a label: unknown. \"SHIPPING\" becomes shipping.",
  why="One walk through the replies.",
  gotchas=[["Fakes test code, evals test quality", "A fake model tells you the parser handles \"Billing.\"; only an eval tells you the model picks billing for the right tickets."], ["Pin the weird cases", "Every strange reply you see in production is a free test case. Add it to the scripted fakes."]]))

add(id="plan_policy", title="Policy as Code", topic="platform", difficulty="medium", fn="plan_policy",
 prompt="Write a plan check like a Spacelift plan policy, with two rules. For each resource change in `plan[\"resource_changes\"]`:\n\n1. If its type is in `protected` and its actions include `\"delete\"`: `\"<address> would be destroyed\"`.\n2. If its actions include `\"create\"` or `\"update\"` and `change.after` has `public_network_access_enabled` set to `True`: `\"<address> allows public network access\"`.\n\nReturn all the messages, in plan order (rule 1 before rule 2 for the same resource).",
 pattern="One pass, several independent rules, each adding its own message.",
 target="one walk through the plan",
 realworld="Spacelift plan policies (Rego) and `terraform test` with `mock_provider` turn reviewers' rules into checks that run on every PR. Workspaces and storage accounts with public network access enabled are a common finding in security reviews of Azure Databricks setups.",
 starter="def plan_policy(plan, protected):\n    # your code here\n    pass\n",
 solution="def plan_policy(plan, protected):\n    out = []\n    for rc in plan.get(\"resource_changes\", []):\n        actions = rc[\"change\"][\"actions\"]\n        if rc[\"type\"] in protected and \"delete\" in actions:\n            out.append(rc[\"address\"] + \" would be destroyed\")\n        after = rc[\"change\"].get(\"after\") or {}\n        if (\"create\" in actions or \"update\" in actions) and after.get(\"public_network_access_enabled\") is True:\n            out.append(rc[\"address\"] + \" allows public network access\")\n    return out\n",
 cases=[({"resource_changes": [{"address": "azurerm_databricks_workspace.this", "type": "azurerm_databricks_workspace", "change": {"actions": ["update"], "after": {"public_network_access_enabled": True}}}, {"address": "azurerm_storage_account.lake", "type": "azurerm_storage_account", "change": {"actions": ["delete"], "after": None}}]}, ["azurerm_storage_account"],
         ["azurerm_databricks_workspace.this allows public network access", "azurerm_storage_account.lake would be destroyed"], "S"),
        ({}, ["x"], []),
        ({"resource_changes": [{"address": "w", "type": "azurerm_databricks_workspace", "change": {"actions": ["delete", "create"], "after": {"public_network_access_enabled": True}}}]}, ["azurerm_databricks_workspace"], ["w would be destroyed", "w allows public network access"]),
        ({"resource_changes": [{"address": "s", "type": "azurerm_storage_account", "change": {"actions": ["no-op"], "after": {"public_network_access_enabled": True}}}]}, [], [])],
 guided="def plan_policy(plan, protected):\n" + H + "\n    out = []\n    for rc in plan.get(\"resource_changes\", []):\n        actions = rc[\"change\"][\"actions\"]\n        # Rule 1: protected and being destroyed.\n        if rc[\"type\"] in protected and ___:\n            out.append(rc[\"address\"] + \" would be destroyed\")\n        # Rule 2: created or updated with public access on.\n        after = rc[\"change\"].get(\"after\") or {}\n        if (\"create\" in actions or \"update\" in actions) and ___ is True:\n            out.append(rc[\"address\"] + \" allows public network access\")\n    return out\n",
 fills=["\"delete\" in actions", "after.get(\"public_network_access_enabled\")"],
 learn=dict(concepts=[["Independent rules", "Separate ifs (not elif) so one resource can break several rules.", "if rule_one:\n    ...\nif rule_two:\n    ..."]],
  byhand="The workspace is updated with public access on: rule 2. The storage account is protected and deleted: rule 1. Two messages, in plan order.",
  why="One walk through the plan.",
  gotchas=[["Warn first, then deny", "Roll a new rule out as a warning, see what it would have blocked, then make it a deny."], ["Test the policy too", "Policies are code: keep sample plans that should pass and fail, and check them in CI."]]))

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
                body = c[:-1] if c[-1] == "S" else c
                args, exp = list(body[:-1]), body[-1]
                got = fn(*json.loads(json.dumps(args)))
                assert got == exp, (p["id"], variant, args, exp, got)
    print("verified", len(P), "batch-2 problems")
if __name__ == "__main__":
    check()
