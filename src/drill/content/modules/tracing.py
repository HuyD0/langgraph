"""Tracing and AgentOps: Traces that answer your questions, slow steps and runaway agents."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('tracing', 'Tracing and AgentOps', 'Traces that answer your questions, slow steps and runaway agents.')

lesson(MODULE, 'summarize_by_tag',
    title='Designing traces for experiments',
    learn=[
        'A **trace** records one request: every model call, retrieval and tool, with timings, inputs, outputs and token counts. Design traces before you need them.',
        "Tag every trace with the things you'll want to split your results by later (for example, comparing two models): **config**, **model**, **prompt version**, **environment**. A trace is made of **spans**, one for each step inside it (a model call, a retrieval, a tool). Mark spans with their type (RETRIEVER, TOOL, CHAT_MODEL) so evaluation and analysis can find them, and put per-request details in span attributes (extra details saved on a span).",
        "Give each version you compare a name with `mlflow.set_active_model(name=...)`, like `rag-rerank-v2`. Every trace and eval run is then linked to that version, which is what lets you line up two versions question by question and read their regressions and improvements. This module sits under **Monitor**, but designing your traces happens earlier, in **Build and trace**, where you build the app and record what it does from the first line: if it isn't in the traces when they're created, no analysis later can recover it.",
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
        why="If nothing recorded which config served each request, you can't work it out later, so tag traces when they are created. Decide the tags before the experiment.",
    ),
    angle=angle(
        pattern='Group by key',
        text='One walk adding into a dict of totals keyed by tag value, then turn totals into averages. The same group-by-key shape as Group Anagrams.',
        say='"I group traces by the tag into running totals in one pass, then divide to get the averages at the end."',
        classic='group_anagrams',
    ),
    stack=stack('MLflow tracing a LangGraph app, with tags', """mlflow.langchain.autolog()   # every LangGraph run becomes a trace

@mlflow.trace
def answer(question):
    mlflow.update_current_trace(tags={"config": "cs512-k5", "model": ENDPOINT})
    return graph.invoke({"messages": [("user", question)]})"""),
    exercise=exercise(
        title='Group Traces by Tag',
        topic='tracing',
        difficulty='medium',
        fn='summarize_by_tag',
        prompt="""Your function gets two things:

- `traces`: a list of traces. Each trace is a dict like `{"tags": {"version": "v1"}, "ms": 1300}`. `tags` holds the labels the trace was given when it was made. `ms` is how long it took, in milliseconds.
- `tag`: the name of the tag to group by, like `"version"`.

Look up each trace's value for that tag, like `"v1"`. Traces with the same value form one group. Skip any trace that does not have that tag.

Return a dict. Each key is a tag value, like `"v1"`. Next to each key, put the average `ms` of that group (add their `ms` up, then divide by how many there are).""",
        pattern='Group by a key: keep a running count and total for each value, then divide once at the end.',
        target='one pass over the traces',
        realworld='This only works if you tagged traces when you created them. Putting the experiment config, model and prompt version on every trace is what lets you compare setups on real traffic later, not just on the eval set.',
        starter="""def summarize_by_tag(traces, tag):
    # your code here
    pass
""",
        solution="""def summarize_by_tag(traces, tag):
    counts = {}
    totals = {}
    for trace in traces:
        if tag not in trace["tags"]:
            continue
        value = trace["tags"][tag]
        counts[value] = counts.get(value, 0) + 1
        totals[value] = totals.get(value, 0) + trace["ms"]
    averages = {}
    for value in counts:
        averages[value] = totals[value] / counts[value]
    return averages
""",
        cases=[
            case([
                {'tags': {'version': 'v1'}, 'ms': 1300},
                {'tags': {'version': 'v2'}, 'ms': 800},
                {'tags': {'version': 'v1'}, 'ms': 1500},
                {'tags': {}, 'ms': 9000},
            ], 'version', expected={'v1': 1400, 'v2': 800}, sample=True),
            case([], 'version', expected={}),
            case([{'tags': {'model': 'small'}, 'ms': 100}], 'version', expected={}),
            case([
                {'tags': {'model': 'large'}, 'ms': 100},
                {'tags': {'model': 'large'}, 'ms': 200},
                {'tags': {'model': 'large'}, 'ms': 300},
            ], 'model', expected={'large': 200}),
            case([
                {'tags': {'model': 'small', 'version': 'v1'}, 'ms': 300},
                {'tags': {'model': 'large', 'version': 'v1'}, 'ms': 900},
                {'tags': {'model': 'small', 'version': 'v2'}, 'ms': 500},
            ], 'model', expected={'small': 400, 'large': 900}),
        ],
        guided="""def summarize_by_tag(traces, tag):
    # Replace every ___ with real code, then run the tests.

    counts = {}   # for each tag value, how many traces
    totals = {}   # for each tag value, total ms
    for trace in traces:
        # Step 1: skip a trace that does not have this tag.
        if tag not in trace["tags"]:
            continue
        value = trace["tags"][tag]
        # Step 2: count the trace, add its ms to the total.
        counts[value] = counts.get(value, 0) + 1
        totals[value] = totals.get(value, 0) + ___

    # Step 3: each average is total divided by count.
    averages = {}
    for value in counts:
        averages[value] = ___
    return averages
""",
        fills=['trace["ms"]', 'totals[value] / counts[value]'],
        concepts=[
            [
                'dict.get with a default',
                '`d.get(key, 0)` gives the value stored for `key`, or 0 if the key is not there yet. Handy for counting and adding up.',
                """stock = {"apples": 3}
stock.get("apples", 0)   # 3
stock.get("pears", 0)    # 0""",
            ],
            [
                'A dict inside a dict',
                '`trace["tags"]` is itself a dict, so a second pair of brackets reads one tag from it.',
                """user = {"home": {"city": "Paris"}}
user["home"]["city"]   # "Paris\"""",
            ],
            [
                'Is the key there?',
                '`key in d` is True when the dict has that key. `not in` is the opposite.',
                """tags = {"model": "small"}
"model" in tags       # True
"version" in tags     # False""",
            ],
            [
                'continue',
                'Inside a loop, `continue` skips the rest of this turn and moves on to the next item.',
                """for word in ["hi", "", "yo"]:
    if word == "": continue
    print(word)   # prints hi, then yo""",
            ],
            [
                'Looping over a dict',
                '`for key in d:` gives you each key in turn. Use `d[key]` to get its value.',
                """ages = {"ann": 30, "bob": 25}
for name in ages:
    print(name, ages[name])""",
            ],
        ],
        byhand='Group by version. Trace 1 is v1 and took 1300 ms. Trace 2 is v2 and took 800 ms. Trace 3 is v1 and took 1500 ms. Trace 4 has no version tag, so skip it. v1 has 2 traces: 1300 and 1500 add up to 2800, and 2800 divided by 2 is 1400. v2 has 1 trace, so its average is 800. Return {"v1": 1400, "v2": 800}. Python writes the result of dividing as 1400.0. That counts the same as 1400.',
        why='One pass over the traces, then one short pass over the groups to divide.',
        gotchas=[
            [
                'Tag at creation time',
                "If nothing recorded which config served each request, you can't work it out later, so tag traces when they are created. Decide the tags (config, model, prompt version, user segment) before the experiment starts.",
            ],
            [
                'Keep tags to a few values',
                'Tags like config or model have only a few values, so they split your results into a few clear groups. Put unique values like request ids in span attributes instead.',
            ],
        ],
    ),
)

lesson(MODULE, 'slowest_chain',
    title='Reading agent traces',
    learn=[
        'A **trace** records one agent run as nested **spans**: the run, each model call, each tool call, each web (HTTP) request inside a tool. MLflow Tracing and LangSmith show them as a tree. A span that holds other spans is their **parent**; the spans directly inside it are its **children**.',
        "To find what's slow, start at the root (the top span, the whole run) and follow the slowest child down. The answer is usually one tool or one model call.",
    ],
    example=example('Spans form a tree', """agent_run      4200 ms
├─ plan           600 ms
├─ tool:search   3100 ms
│  └─ http_get   2900 ms
└─ answer         400 ms"""),
    check=question(
        'A parent span took 4200 ms. Its children ran one after another and took 600, 3100 and 400 ms. How long did the parent take on its own?',
        ['4200 ms', '100 ms', '8300 ms'],
        answer=1,
        why="Parent time includes its children's time. The children add up to 4100 ms (600 plus 3100 plus 400), and 4200 minus 4100 leaves 100 ms of its own.",
    ),
    angle=angle(
        pattern='Tree traversal',
        text='Build a parent-to-children map in one walk, then follow one path down the tree. Number of Islands also starts at one square and keeps stepping into neighbours until there are none left.',
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
        prompt="""A trace is a tree of spans: steps that sit inside other steps. Your function gets one input, `spans`: a list of dicts like `{"name": "plan", "parent": "agent_run", "ms": 600}`.

`ms` is how long it took, in milliseconds. `parent` is the name of the span this one sits inside. A span's children are the spans whose `parent` is that span's name. The top span, the root, has `"parent": None`. The spans can come in any order.

Start at the root. Step into its slowest child, the one with the biggest `ms`. Keep stepping into the slowest child until you reach a span with no children. Return the names you visited, root first. If `spans` is empty, return `[]`.""",
        pattern="List each span's children in one pass, then walk down from the root, always into the slowest child.",
        target='one pass to list the children, then one walk down the tree',
        realworld="This is how you read a slow trace in MLflow Tracing or LangSmith: follow the slowest child at each level until you reach the step that's actually slow, usually one model call or one tool.",
        starter="""def slowest_chain(spans):
    # your code here
    pass
""",
        solution="""def slowest_chain(spans):
    children = {}
    root = None
    for span in spans:
        parent = span["parent"]
        if parent is None:
            root = span
        else:
            if parent not in children:
                children[parent] = []
            children[parent].append(span)
    path = []
    node = root
    while node is not None:
        path.append(node["name"])
        child_spans = children.get(node["name"], [])
        slowest = None
        for child in child_spans:
            if slowest is None or child["ms"] > slowest["ms"]:
                slowest = child
        node = slowest
    return path
""",
        cases=[
            case([
                {'name': 'agent_run', 'parent': None, 'ms': 4200},
                {'name': 'plan', 'parent': 'agent_run', 'ms': 600},
                {'name': 'tool:search', 'parent': 'agent_run', 'ms': 3100},
                {'name': 'http_get', 'parent': 'tool:search', 'ms': 2900},
                {'name': 'answer', 'parent': 'agent_run', 'ms': 400},
            ], expected=['agent_run', 'tool:search', 'http_get'], sample=True),
            case([], expected=[]),
            case([{'name': 'run', 'parent': None, 'ms': 10}], expected=['run']),
            case([
                {'name': 'llm', 'parent': 'run', 'ms': 50},
                {'name': 'run', 'parent': None, 'ms': 120},
                {'name': 'tool', 'parent': 'run', 'ms': 60},
            ], expected=['run', 'tool']),
            case([
                {'name': 'agent', 'parent': None, 'ms': 1000},
                {'name': 'llm_call', 'parent': 'agent', 'ms': 700},
                {'name': 'tool:db', 'parent': 'agent', 'ms': 200},
                {'name': 'prompt', 'parent': 'llm_call', 'ms': 50},
                {'name': 'generate', 'parent': 'llm_call', 'ms': 640},
                {'name': 'sql', 'parent': 'tool:db', 'ms': 190},
            ], expected=['agent', 'llm_call', 'generate']),
        ],
        guided="""def slowest_chain(spans):
    # Replace every ___ with real code, then run the tests.

    # Step 1: find the root, and list each span's children.
    children = {}   # parent name: list of its child spans
    root = None
    for span in spans:
        parent = span["parent"]
        if parent is None:
            root = span
        else:
            if parent not in children:
                children[parent] = []
            children[parent].append(span)

    path = []
    node = root   # the span we are at now
    while node is not None:
        path.append(node["name"])
        # Step 2: look up this span's children by its name.
        child_spans = children.get(___, [])
        slowest = None   # the slowest child span so far
        for child in child_spans:
            # Step 3: child's ms bigger than slowest's ms?
            if slowest is None or ___:
                slowest = child
        # Move down. No children means None: the loop ends.
        node = slowest
    return path
""",
        fills=['node["name"]', 'child["ms"] > slowest["ms"]'],
        concepts=[
            [
                'A dict of lists',
                'Start an empty list the first time a key shows up, then append to that list.',
                """pets = {}
if "cats" not in pets: pets["cats"] = []
pets["cats"].append("Tom")""",
            ],
            [
                'dict.get with a default',
                '`d.get(key, [])` gives the value stored for `key`, or `[]` if the key is missing, instead of an error.',
                """pets = {"cats": ["Tom"]}
pets.get("dogs", [])   # []""",
            ],
            [
                'while loop',
                'Repeats as long as its condition is True. Use it when you do not know ahead of time how many steps there will be.',
                """n = 3
while n > 0:
    n = n - 1""",
            ],
            [
                'Keeping the biggest so far',
                '`None` means "nothing yet", and `is None` checks for it. `is not None` is the opposite: True when there is something. Start with None, then replace it whenever an item beats it. To keep a whole dict, compare one of its keys.',
                """best = None
for n in [4, 9, 2]:
    if best is None or n > best: best = n

top = None
for p in [{"age": 4}, {"age": 9}]:
    if top is None or p["age"] > top["age"]:
        top = p   # top is the whole dict""",
            ],
        ],
        byhand='The root is agent_run, because its parent is None. Its children are plan (600), tool:search (3100) and answer (400). The slowest is tool:search, so step into it. Its only child is http_get (2900), so step into that. http_get has no children, so stop. The slow step is http_get, a web request inside the search tool. Return ["agent_run", "tool:search", "http_get"].',
        why='Listing the children is one pass; the walk then visits one span per level.',
        gotchas=[
            [
                'Child time is inside parent time',
                "When children run one after another, don't add a parent's time to its children's, because the parent already includes them. To find the parent's own time, take away all its children's time. In the example that leaves 100 ms.",
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
        'An agent alternates between two calls forever: A, B, A, B. Does a "same call 3 times in a row" check catch it?',
        ['Yes', 'No, so you also need a total step limit', 'Only with limit 2'],
        answer=1,
        why='No call repeats back to back, so you need other limits too.',
    ),
    angle=angle(
        pattern='Run-length counting',
        text='One walk, counting the current run of identical calls and starting again at 1 when the call changes. Maximum Subarray also keeps a running value in one walk and starts it again when that helps.',
        say='"One pass with a counter for the current run of identical calls, reset whenever the call changes."',
        classic='max_subarray',
    ),
    stack=stack('LangGraph: stop on a repeated call', """def route(state):
    last = state["messages"][-1]
    if not getattr(last, "tool_calls", None):
        return "end"   # a final answer, no tool to call
    # Compare only the tool name and its arguments:
    # each call also has its own id, which never repeats.
    calls = [
        str([(c["name"], c["args"]) for c in m.tool_calls])
        for m in state["messages"]
        if getattr(m, "tool_calls", None)
    ]
    if len(calls) >= 3 and len(set(calls[-3:])) == 1:
        return "stop"
    return "tools\""""),
    exercise=exercise(
        title='Stop a Looping Agent',
        topic='agentops',
        difficulty='easy',
        fn='detect_loop',
        prompt="""Your function gets two things:

- `calls`: the tool calls an agent made, in order. Each call is a list of two strings, the tool's name and what it was asked, like `["search", "weather paris"]`.
- `limit`: how many identical calls in a row count as a loop, like `3`.

Go through the calls and count how many times in a row the same call (same tool and same text) has been made. As soon as that count reaches `limit`, return the index of that call: its position in the list, counting from 0. If it never happens, return `-1`.""",
        pattern='Keep a count of identical calls in a row; start again at 1 when the call changes.',
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
                ['calc', '2+2'],
                ['search', 'weather paris'],
                ['search', 'weather paris'],
                ['search', 'weather paris'],
            ], 3, expected=4, sample=True),
            case([
                ['search', 'weather paris'],
                ['search', 'weather paris'],
                ['calc', '2+2'],
                ['search', 'weather paris'],
                ['search', 'weather paris'],
                ['search', 'weather paris'],
            ], 3, expected=5),
            case([], 3, expected=-1),
            case([['search', 'paris']], 1, expected=0),
            case([['search', 'paris'], ['search', 'rome'], ['search', 'paris']], 2, expected=-1),
            case([['search', 'q'], ['search', 'q']], 2, expected=1),
            case([['search', 'q'], ['search', 'q'], ['search', 'q'], ['search', 'q']], 2, expected=1),
        ],
        guided="""def detect_loop(calls, limit):
    # Replace every ___ with real code, then run the tests.

    run = 0       # identical calls in a row so far
    prev = None   # the call before this one
    for i, call in enumerate(calls):
        # Step 1: same as the call before? The run grows.
        # A different call starts a new run of 1.
        if call == prev:
            run += 1
        else:
            run = ___
        prev = call
        # Step 2: has the run reached the limit? Return i.
        if ___:
            return i
    return -1
""",
        fills=['1', 'run >= limit'],
        concepts=[
            [
                'Comparing lists',
                '`==` on two lists is True only when every item matches, in the same order.',
                """[1, 2] == [1, 2]   # True
[1, 2] == [2, 1]   # False""",
            ],
            [
                'enumerate',
                'Gives you the index (position, from 0) along with each item.',
                """for i, fruit in enumerate(["fig", "kiwi"]):
    print(i, fruit)   # 0 fig, then 1 kiwi""",
            ],
            [
                'None as a starting value',
                '`None` means "nothing yet". No call is equal to None, so the first call always starts a new run.',
                """last = None
last == ["a", "b"]   # False""",
            ],
            [
                'Adding one',
                '`run += 1` is short for `run = run + 1`.',
                """score = 0
score += 1   # score is now 1""",
            ],
        ],
        byhand='Limit 3. Index 0: search weather paris. The run (how many times in a row this same call came up) is 1. Index 1: calc is a different call, so the run starts again at 1. Index 2: search is different from calc, so the run is 1 again. Index 3: the same search again, a run of 2. Index 4: the same search again, a run of 3. That reaches the limit, so return 4.',
        why='One pass with two variables.',
        gotchas=[
            [
                "Loops aren't always identical",
                'Agents also alternate between two calls, or change one word each time. Production guardrails also cap total steps, total tokens and how long the run has been going.',
            ],
            [
                'Tell the model why it stopped',
                'Returning a clear message ("stopped: repeated the same search 3 times") lets the agent change approach instead of failing silently.',
            ],
        ],
    ),
)
