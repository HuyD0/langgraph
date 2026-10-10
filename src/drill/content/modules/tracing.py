"""Tracing and AgentOps: Traces that answer your questions, slow steps and runaway agents."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('tracing', 'Tracing and AgentOps', 'Traces that answer your questions, slow steps and runaway agents.')

lesson(MODULE, 'summarize_by_tag',
    title='Designing traces for experiments',
    learn=[
        'A **trace** records one request: every model call, retrieval and tool, with timings, inputs, outputs and token counts. Design traces before you need them.',
        "Tag every trace with the things you'll want to slice by later: **config**, **model**, **prompt version**, **environment**. Mark spans with their type (RETRIEVER, TOOL, CHAT_MODEL) so evaluation and analysis can find them, and put per-request details in span attributes.",
    ],
    example=example('Tags and span types in MLflow Tracing', """import mlflow

@mlflow.trace(span_type="RETRIEVER")
def retrieve(question, k):
    ...

@mlflow.trace
def answer(question):
    mlflow.update_current_trace(tags={"config": "cs512-k5", "model": "fast-model"})
    docs = retrieve(question, k=5)
    ...

traces = mlflow.search_traces(filter_string="tags.config = 'cs512-k5'")"""),
    check=question(
        "You want to compare two configs on last week's production traffic. What must already be true?",
        [
            'Nothing, MLflow figures it out',
            'Each trace was tagged with its config when it was created',
            'You need a new eval set',
        ],
        answer=1,
        why="Tags can't be recovered later. Decide them before the experiment.",
    ),
    angle=angle(
        pattern='Group by key',
        text='One walk adding into a dict of totals keyed by tag value, then turn totals into averages. The same group-by-key shape as Group Anagrams.',
        say='"I group traces by the tag into running totals in one pass and compute averages and rates at the end."',
        classic='group_anagrams',
    ),
    stack=stack('MLflow tracing a LangGraph app, with tags', """mlflow.langchain.autolog()   # every LangGraph run becomes a trace

@mlflow.trace
def answer(question):
    mlflow.update_current_trace(tags={"config": "cs512-k5", "model": ENDPOINT})
    return graph.invoke({"messages": [("user", question)]})"""),
    exercise=exercise(
        title='Slice Traces by Experiment',
        topic='tracing',
        difficulty='medium',
        fn='summarize_by_tag',
        prompt="""Every trace was tagged with the setup that produced it. Each trace in `traces` is like `{"tags": {"config": "cs512-k5"}, "ms": 1300, "tokens": 2100, "ok": True}`.

Group the traces by `tags[tag]` and return a dict from each value to `[count, average_ms, total_tokens, success_rate]`, with average_ms rounded to a whole number and success_rate to 2 places. Traces without that tag are skipped.""",
        pattern='Group by a key into a dict of running totals, then turn totals into averages at the end.',
        target='one walk through the traces',
        realworld='This only works if you tagged traces when you created them. Putting the experiment config, model and prompt version on every trace is what lets you compare setups on real traffic later, not just on the eval set.',
        starter="""def summarize_by_tag(traces, tag):
    # your code here
    pass
""",
        solution="""def summarize_by_tag(traces, tag):
    groups = {}
    for t in traces:
        if tag not in t["tags"]:
            continue
        key = t["tags"][tag]
        g = groups.setdefault(key, [0, 0, 0, 0])
        g[0] += 1
        g[1] += t["ms"]
        g[2] += t["tokens"]
        if t["ok"]:
            g[3] += 1
    out = {}
    for key, g in groups.items():
        out[key] = [g[0], round(g[1] / g[0]), g[2], round(g[3] / g[0], 2)]
    return out
""",
        cases=[
            case([
                {'tags': {'config': 'cs512-k5'}, 'ms': 1300, 'tokens': 2100, 'ok': True},
                {'tags': {'config': 'cs256-k3'}, 'ms': 800, 'tokens': 1200, 'ok': False},
                {'tags': {'config': 'cs512-k5'}, 'ms': 1500, 'tokens': 2300, 'ok': True},
                {'tags': {}, 'ms': 9000, 'tokens': 50, 'ok': False},
            ], 'config', expected={'cs512-k5': [2, 1400, 4400, 1.0], 'cs256-k3': [1, 800, 1200, 0.0]}, sample=True),
            case([], 'config', expected={}),
            case([{'tags': {'model': 'fast-model'}, 'ms': 100, 'tokens': 10, 'ok': True}], 'config', expected={}),
            case([
                {'tags': {'model': 'a'}, 'ms': 100, 'tokens': 5, 'ok': True},
                {'tags': {'model': 'a'}, 'ms': 201, 'tokens': 5, 'ok': False},
                {'tags': {'model': 'a'}, 'ms': 300, 'tokens': 5, 'ok': True},
            ], 'model', expected={'a': [3, 200, 15, 0.67]}),
        ],
        guided="""def summarize_by_tag(traces, tag):
    # Replace every ___ with real code, then run the tests.

    groups = {}   # tag value -> [count, total_ms, total_tokens, successes]
    for t in traces:
        if tag not in t["tags"]:
            continue
        key = t["tags"][tag]
        # Step 1: the running totals for this value, created the first time.
        g = groups.setdefault(key, [0, 0, 0, 0])
        g[0] += 1
        g[1] += t["ms"]
        g[2] += ___
        if t["ok"]:
            g[3] += 1
    out = {}
    for key, g in groups.items():
        # Step 2: totals become averages and rates at the end.
        out[key] = [g[0], round(___), g[2], round(g[3] / g[0], 2)]
    return out
""",
        fills=['t["tokens"]', 'g[1] / g[0]'],
        concepts=[
            [
                'setdefault for totals',
                'Creates the starting totals the first time a key appears, then returns the same list each time after.',
                """g = groups.setdefault('k5', [0, 0])
g[0] += 1""",
            ],
            [
                'Totals first, averages last',
                'Keep sums while looping and divide once at the end.',
                'avg = total / count',
            ],
        ],
        byhand='cs512-k5 has two traces: 1,300 and 1,500 ms (average 1,400), 2,100 + 2,300 tokens, both ok. cs256-k3 has one trace that failed. The untagged trace is skipped.',
        why='One walk through the traces, one more through the groups.',
        gotchas=[
            [
                'Tag at creation time',
                "You can't add the config to a trace you didn't tag. Decide the tags (config, model, prompt version, user segment) before the experiment starts.",
            ],
            [
                'Keep tags low-cardinality',
                'Tags like config or model have a few values and slice nicely. Put unique values like request ids in span attributes instead.',
            ],
        ],
    ),
)

lesson(MODULE, 'slowest_chain',
    title='Reading agent traces',
    learn=[
        'A **trace** records one agent run as nested **spans**: the run, each model call, each tool call, each HTTP request inside a tool. MLflow Tracing and LangSmith show them as a tree.',
        "To find what's slow, start at the root and follow the slowest child down. The answer is usually one tool or one model call.",
    ],
    example=example('Spans form a tree', """agent_run      4200 ms
├─ plan           600 ms
├─ tool:search   3100 ms
│  └─ http_get   2900 ms
└─ answer         400 ms"""),
    check=question(
        'A parent span took 4200 ms and its children took 600, 3100 and 400 ms. How long did the parent take on its own?',
        ['4200 ms', '100 ms', '8300 ms'],
        answer=1,
        why='Parent time includes its children: 4200 − (600 + 3100 + 400) = 100 ms of its own.',
    ),
    angle=angle(
        pattern='Tree traversal',
        text='Build a parent-to-children map in one walk, then follow one path down the tree. Number of Islands also builds the structure first and then walks it.',
        say='"I group spans by parent in one pass, then keep stepping into the slowest child until there are none."',
        classic='num_islands',
    ),
    stack=stack('MLflow: find the slowest model call', """from mlflow.entities import SpanType
spans = trace.search_spans(span_type=SpanType.CHAT_MODEL)
slowest = max(spans, key=lambda s: s.end_time_ns - s.start_time_ns)"""),
    exercise=exercise(
        title='Find the Slow Path in a Trace',
        topic='agentops',
        difficulty='medium',
        fn='slowest_chain',
        prompt="""A trace records an agent run as spans: `{"id": "s2", "parent": "s1", "name": "retrieve", "ms": 840}`. The root span has `"parent": None`, and a span's time includes its children's.

Start at the root. Repeatedly step into the child that took the longest (the first one listed wins a tie) until you reach a span with no children. Return the names along the way, root first. No spans gives `[]`.""",
        pattern='Build a parent → children map, then walk down the tree.',
        target='one pass to build the map, one walk down',
        realworld="This is how you read a slow trace in MLflow Tracing or LangSmith: follow the slowest child at each level until you reach the step that's actually slow, usually one model call or one tool.",
        starter="""def slowest_chain(spans):
    # your code here
    pass
""",
        solution="""def slowest_chain(spans):
    children = {}
    root = None
    for s in spans:
        if s["parent"] is None:
            root = s
        else:
            children.setdefault(s["parent"], []).append(s)
    path = []
    node = root
    while node is not None:
        path.append(node["name"])
        kids = children.get(node["id"], [])
        node = None
        for k in kids:
            if node is None or k["ms"] > node["ms"]:
                node = k
    return path
""",
        cases=[
            case([
                {'id': 's1', 'parent': None, 'name': 'agent_run', 'ms': 4200},
                {'id': 's2', 'parent': 's1', 'name': 'plan', 'ms': 600},
                {'id': 's3', 'parent': 's1', 'name': 'tool:search', 'ms': 3100},
                {'id': 's4', 'parent': 's3', 'name': 'http_get', 'ms': 2900},
                {'id': 's5', 'parent': 's1', 'name': 'answer', 'ms': 400},
            ], expected=['agent_run', 'tool:search', 'http_get'], sample=True),
            case([], expected=[]),
            case([{'id': 'r', 'parent': None, 'name': 'run', 'ms': 10}], expected=['run']),
            case([
                {'id': 'c', 'parent': 'r', 'name': 'llm_a', 'ms': 50},
                {'id': 'r', 'parent': None, 'name': 'run', 'ms': 120},
                {'id': 'd', 'parent': 'r', 'name': 'llm_b', 'ms': 50},
            ], expected=['run', 'llm_a']),
        ],
        guided="""def slowest_chain(spans):
    # Replace every ___ with real code, then run the tests.

    # Step 1: find the root and build parent id -> list of child spans.
    children = {}
    root = None
    for s in spans:
        if s["parent"] is None:
            root = s
        else:
            children.setdefault(s["parent"], []).append(s)

    path = []
    node = root
    while node is not None:
        path.append(node["name"])
        # Step 2: this span's children (none for a leaf).
        kids = children.get(___, [])
        # Step 3: step into the slowest child; the first wins a tie.
        node = None
        for k in kids:
            if node is None or ___:
                node = k
    return path
""",
        fills=['node["id"]', 'k["ms"] > node["ms"]'],
        concepts=[
            [
                'setdefault',
                "Gets a key's value, creating it with a default first if it's missing. Handy for dicts of lists.",
                """kids = {}
kids.setdefault('s1', []).append('s2')""",
            ],
            [
                'is None',
                'The right way to check for None.',
                """if node is None:
    ...""",
            ],
        ],
        byhand='agent_run has three children: plan (600), tool:search (3100), answer (400). Step into tool:search. Its only child is http_get (2900). http_get has no children. Path: agent_run, tool:search, http_get. The slow part is an HTTP call inside a tool, not the model.',
        why='Building the map is one pass; the walk visits one span per level.',
        gotchas=[
            [
                'Child time is inside parent time',
                "Don't add a parent's time to its children's; the parent already includes them. The gap between a parent and its slowest child is time spent in the parent itself.",
            ],
            [
                'Parallel children overlap',
                'When tools run at the same time, their times overlap. The slowest one sets the pace, not the sum.',
            ],
        ],
    ),
)

lesson(MODULE, 'detect_loop',
    title='Guardrails for agents',
    learn=[
        'Agents in production need **guardrails**: limits that stop a run before it does damage or burns money. The simplest catches the same call repeated again and again.',
        'Production systems also cap total steps, tokens and time, and tell the model why it was stopped.',
    ],
    example=example('A loop in a trace', """search('weather paris')
search('weather paris')
search('weather paris')   # stop here"""),
    check=question(
        'An agent alternates between two calls forever: A, B, A, B. Does a "same call N times in a row" check catch it?',
        ['Yes', 'No, so you also need a total step limit', 'Only with limit 2'],
        answer=1,
        why='No call repeats back to back, so you need other limits too.',
    ),
    angle=angle(
        pattern='Run-length counting',
        text='One walk, counting the current run of identical calls and starting again at 1 when the call changes.',
        say='"One pass with a counter for the current run of identical calls, reset whenever the call changes."',
        classic='longest_unique_substring',
    ),
    stack=stack('LangGraph: stop on a repeated call', 'def route(state):\n    calls = [str(m.tool_calls) for m in state["messages"] if getattr(m, "tool_calls", None)]\n    if len(calls) >= 3 and len(set(calls[-3:])) == 1:\n        return "stop"\n    return "tools" if state["messages"][-1].tool_calls else "end"'),
    exercise=exercise(
        title='Stop a Looping Agent',
        topic='agentops',
        difficulty='easy',
        fn='detect_loop',
        prompt="""An agent sometimes gets stuck making the same tool call over and over. `calls` is the list of calls it made, each `[tool, argument]`. Return the index of the call where the same call has now happened `limit` times in a row, so the run can be stopped there. If that never happens, return `-1`.

For `limit` 3, `[["search", "x"], ["search", "x"], ["search", "x"]]` gives `2`.""",
        pattern='Count the current run of identical items; reset the count when the item changes.',
        target='one pass over the calls',
        realworld='A guardrail every agent in production needs: without it, a model that keeps retrying the same search can loop until it hits the step limit, spending tokens the whole time.',
        starter="""def detect_loop(calls, limit):
    # your code here
    pass
""",
        solution="""def detect_loop(calls, limit):
    run = 0
    prev = None
    for i, call in enumerate(calls):
        if call == prev:
            run += 1
        else:
            run = 1
        prev = call
        if run >= limit:
            return i
    return -1
""",
        cases=[
            case([
                ['search', 'weather paris'],
                ['search', 'weather paris'],
                ['calc', '2+2'],
                ['search', 'weather paris'],
                ['search', 'weather paris'],
                ['search', 'weather paris'],
            ], 3, expected=5, sample=True),
            case([], 3, expected=-1),
            case([['a', '1']], 1, expected=0),
            case([['a', '1'], ['a', '2'], ['a', '1']], 2, expected=-1),
            case([['s', 'q'], ['s', 'q']], 2, expected=1),
        ],
        guided="""def detect_loop(calls, limit):
    # Replace every ___ with real code, then run the tests.

    run = 0       # how many identical calls in a row so far
    prev = None   # the call before this one
    for i, call in enumerate(calls):
        # Step 1: same as the previous call? The run grows. Otherwise it restarts at 1.
        if call == prev:
            run += 1
        else:
            run = ___
        prev = call
        # Step 2: reached the limit? Stop here.
        if ___:
            return i
    return -1
""",
        fills=['1', 'run >= limit'],
        concepts=[
            [
                'Comparing lists',
                '`==` on two lists checks every item, in order.',
                "['search', 'x'] == ['search', 'x']   # True",
            ],
            [
                'enumerate',
                'Gives the index along with each item.',
                """for i, call in enumerate(calls):
    ...""",
            ],
        ],
        byhand='search, search: run 2. calc: run resets to 1. search: 1, search: 2, search: 3 at index 5. Limit reached: return 5.',
        why='One pass with two variables.',
        gotchas=[
            [
                "Loops aren't always identical",
                'Agents also alternate between two calls, or change one word each time. Production guardrails also cap total steps, total tokens and wall-clock time.',
            ],
            [
                'Tell the model why it stopped',
                'Returning a clear message ("stopped: repeated the same search 3 times") lets the agent change approach instead of failing silently.',
            ],
        ],
    ),
)
