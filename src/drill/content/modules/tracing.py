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
        pattern='Group by a tag, then average',
        text="The big idea: tagging every trace lets you compare versions later, like v1 against v2. Your code sorts the traces into piles by their tag. For each pile it keeps a running count and a running total of milliseconds, stored in a dict: a lookup table from the tag's value to its numbers. At the end it divides each total by its count to get the average time per version. Traces without the tag are skipped.",
        say='"I tag every trace with its version, then group the traces by that tag and average their times, so I can compare versions side by side."',
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
        "An agent team makes the same kind of tree when each helper is traced under its own name: one span on top for the whole team run, one span for each helper agent, and each helper's tool calls inside its span. Following the slowest child then shows which helper held the run up.",
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
        pattern='Follow the slowest child down',
        text="The big idea: to find what's slow, start at the root and keep following the slowest child down. Your code first goes through the spans to find the root and build a dict, a lookup table from each parent's name to its children. Then it walks down: it adds the current span's name to the path, picks the child with the biggest `ms`, and moves to it. When a span has no children, it stops. It is like following the thickest branch of a tree out to its tip.",
        say='"I group spans by parent, then start at the root and step into the slowest child each time. The path usually ends at the slow tool or model call."',
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

lesson(MODULE, 'trace_table_row',
    title='Traces to a table',
    learn=[
        'Reading traces one at a time stops working after a few dozen runs. Turn each trace into **one row** of a few numbers: steps (model calls), tool errors, the biggest prompt and total tokens. Then sort and filter the rows, like a spreadsheet, to find the runs worth reading.',
        'Rows with many steps or many tool errors are the runs to open first. The biggest prompt (the most input tokens in one call) shows how close a run came to filling the context window, the most a model can read in one call.',
        'On Databricks, production traces can be stored as tables in **Unity Catalog**, so you can query them with SQL. Keep every trace (with personal data hidden first, as in Security), and save money by judging only a **sample** of them, say 1 in 10. Recording fewer traces can throw away exactly the failing runs you need.',
    ],
    example=example('Three traces as three rows', """trace  steps  errors   peak  total
t-01       3       1   2100   5090
t-02       2       0    900   1950
t-03       9       4  14800  61200
# read t-03 first: most steps and errors"""),
    check=question(
        'Your agent handles 5,000 runs a day, and judging every trace with a model costs too much. What should you do?',
        [
            'Record only 1 run in 10, and judge those',
            'Judge only the runs users complained about',
            'Record every run, and judge only 1 in 10',
        ],
        answer=2,
        why='Runs you never record are gone, failures included, and many failures get no complaint. Keep every trace, and save money by judging a sample.',
    ),
    angle=angle(
        pattern='Four numbers from one trace',
        text="The big idea: turn each trace into one row of a few numbers, so you can sort and filter runs like a spreadsheet. Your code starts four numbers at 0 and looks at each span once. It adds 1 to steps for a model call, and 1 to tool errors for a failed tool call. It keeps the biggest input tokens seen so far, and adds every span's input and output tokens to the total. An empty trace leaves all four at 0.",
        say='"I turn each trace into one row: model steps, tool errors, the biggest prompt and total tokens. Then I sort the rows to find the runs worth reading."',
        classic=None,
    ),
    stack=stack('MLflow 3: one row per trace', """import mlflow
from mlflow.entities import SpanType

# A DataFrame with one row per trace.
# Columns include trace_id, state,
# execution_duration, tags and spans.
df = mlflow.search_traces(max_results=500)
# Traces kept in Unity Catalog: add
# locations=["catalog.schema"]

# Add your own numbers from the spans:
traces = mlflow.search_traces(
    max_results=500, return_type="list")
for t in traces:
    tools = t.search_spans(
        span_type=SpanType.TOOL)
    bad = [s for s in tools
           if s.status.status_code == "ERROR"]
    # token_usage: input, output and total
    print(t.info.trace_id, len(bad),
          t.info.token_usage)"""),
    exercise=exercise(
        title='Turn a Trace into a Row',
        topic='agentops',
        difficulty='easy',
        fn='trace_table_row',
        prompt="""A trace is a list of spans, one for each step of an agent run. Your function gets one input, `spans`: a list of dicts like `{"type": "llm", "input_tokens": 1200, "output_tokens": 80, "error": False}`. `type` is `"llm"` for a model call or `"tool"` for a tool call. `error` is True if that step failed.

Turn the trace into one row of a table. Return a dict with four keys:

- `"steps"`: how many spans have type `"llm"`.
- `"tool_errors"`: how many spans have type `"tool"` and error True.
- `"peak_input_tokens"`: the biggest `input_tokens` of any span.
- `"total_tokens"`: every span's `input_tokens` and `output_tokens`, all added up.

If `spans` is empty, all four numbers are 0.""",
        pattern='One pass over the spans, updating two counts, a running biggest and a running total as you go.',
        target='one pass over the spans',
        realworld='The first step in looking at agents at scale: one row per run, then sort by tool errors or tokens to choose which traces to read. On Databricks the same numbers can come straight from traces stored in Unity Catalog tables.',
        starter="""def trace_table_row(spans):
    # your code here
    pass
""",
        solution="""def trace_table_row(spans):
    steps = 0
    tool_errors = 0
    peak = 0
    total = 0
    for span in spans:
        if span["type"] == "llm":
            steps += 1
        if span["type"] == "tool" and span["error"]:
            tool_errors += 1
        if span["input_tokens"] > peak:
            peak = span["input_tokens"]
        total += span["input_tokens"] + span["output_tokens"]
    return {
        "steps": steps,
        "tool_errors": tool_errors,
        "peak_input_tokens": peak,
        "total_tokens": total,
    }
""",
        cases=[
            case([
                {'type': 'llm', 'input_tokens': 1200, 'output_tokens': 80, 'error': False},
                {'type': 'tool', 'input_tokens': 0, 'output_tokens': 0, 'error': True},
                {'type': 'llm', 'input_tokens': 1500, 'output_tokens': 60, 'error': False},
                {'type': 'tool', 'input_tokens': 0, 'output_tokens': 0, 'error': False},
                {'type': 'llm', 'input_tokens': 2100, 'output_tokens': 150, 'error': False},
            ], expected={'steps': 3, 'tool_errors': 1, 'peak_input_tokens': 2100, 'total_tokens': 5090}, sample=True),
            case([], expected={'steps': 0, 'tool_errors': 0, 'peak_input_tokens': 0, 'total_tokens': 0}),
            case([
                {'type': 'llm', 'input_tokens': 500, 'output_tokens': 20, 'error': True},
                {'type': 'tool', 'input_tokens': 0, 'output_tokens': 0, 'error': True},
                {'type': 'tool', 'input_tokens': 0, 'output_tokens': 0, 'error': True},
            ], expected={'steps': 1, 'tool_errors': 2, 'peak_input_tokens': 500, 'total_tokens': 520}),
            case([
                {'type': 'llm', 'input_tokens': 3000, 'output_tokens': 100, 'error': False},
                {'type': 'llm', 'input_tokens': 2500, 'output_tokens': 50, 'error': False},
            ], expected={'steps': 2, 'tool_errors': 0, 'peak_input_tokens': 3000, 'total_tokens': 5650}),
            case([
                {'type': 'tool', 'input_tokens': 0, 'output_tokens': 0, 'error': False},
            ], expected={'steps': 0, 'tool_errors': 0, 'peak_input_tokens': 0, 'total_tokens': 0}),
        ],
        guided="""def trace_table_row(spans):
    # Replace every ___ with real code, then run the tests.

    steps = 0         # model calls
    tool_errors = 0   # tool calls that failed
    peak = 0          # biggest input_tokens so far
    total = 0         # all tokens, in and out
    for span in spans:
        # Step 1: count the model calls.
        if span["type"] == "llm":
            steps += 1
        # Step 2: a tool call that failed? Count it.
        if ___:
            tool_errors += 1
        # Step 3: a bigger prompt than any so far? Keep it.
        if span["input_tokens"] > peak:
            peak = ___
        # Step 4: add this span's input and output tokens.
        total += ___
    return {
        "steps": steps,
        "tool_errors": tool_errors,
        "peak_input_tokens": peak,
        "total_tokens": total,
    }
""",
        fills=['span["type"] == "tool" and span["error"]', 'span["input_tokens"]', 'span["input_tokens"] + span["output_tokens"]'],
        concepts=[
            [
                'Adding with +=',
                '`n += x` adds x to `n`, so `n += 1` adds one. Start each count at 0 before the loop.',
                """apples = 0
apples += 1
apples += 5   # apples is now 6""",
            ],
            [
                'and, with True or False',
                '`a and b` is True only when both are True. A value that is already True or False, like `span["error"]`, can go straight into an `if`.',
                """done = True
paid = False
if done and paid:
    print("ship it")   # not printed""",
            ],
            [
                'Keeping the biggest so far',
                'Start at 0, then replace it whenever an item is bigger.',
                """best = 0
for n in [4, 9, 2]:
    if n > best: best = n
# best is 9""",
            ],
            [
                'Making a dict to return',
                'Curly braces with `key: value` pairs build a dict in one go.',
                """pet = {"name": "Rex", "age": 3}
pet["age"]   # 3""",
            ],
        ],
        byhand='Span 1 is a model call, so steps is 1. Its 1200 input tokens are the biggest so far, and the total is 1200 plus 80, which is 1280. Span 2 is a tool call that failed, so tool_errors is 1. It has no tokens. Span 3 is a model call, so steps is 2. 1500 beats 1200, so the peak is 1500, and the total grows by 1560 to 2840. Span 4 is a tool call that worked, so nothing changes. Span 5 is a model call, so steps is 3. The peak becomes 2100, and the total grows by 2250 to 5090. Return {"steps": 3, "tool_errors": 1, "peak_input_tokens": 2100, "total_tokens": 5090}.',
        why='One pass over the spans. Each span updates at most four numbers.',
        gotchas=[
            [
                'Blaming a tool for a model error',
                'Model calls fail too, for example when one times out. Check the span type as well as the error flag, or a model timeout gets counted as a broken tool.',
            ],
            [
                'Mixing up peak and total',
                "Each model call re-reads the whole run so far, so input tokens grow every step. The total says what the run cost. The peak says how close it came to filling the context window. They answer different questions.",
            ],
        ],
    ),
)

lesson(MODULE, 'context_fill',
    title='How full is the context?',
    learn=[
        "Answers get worse as the prompt gets longer, even when the right fact is in it. A model's **context window** is the most tokens it can read in one call. This drop is called **context rot**, and a model with a bigger window does not fix it.",
        'An agent sends its whole history again on every call, so each call reads more than the last. Measure the **fill** of each call: its input tokens as a percent of the window. When it passes a line, for example 80 percent, clean up before the run hits the limit: clear old tool results or summarise (next lesson).',
        'Three habits keep the context small and useful. Put the question after the retrieved text, and keep a short goal and plan near the end of the prompt, where models pay the most attention. Fewer, better chunks often beat more: try 5 retrieved chunks against 50 and compare the eval scores.',
    ],
    example=example('The fill grows on every call', """window: 128000 tokens
call 0:  12000 tokens   9%
call 1:  41000 tokens  32%
call 2:  77000 tokens  60%
call 3: 108000 tokens  84%
# first over 80: index 3"""),
    check=question(
        'Your agent gets worse on long runs, even though the right fact is in its prompt. A teammate suggests a model with a window twice as big. What happens?',
        [
            'It still slips as the prompt grows, so keep the context short',
            'The problem goes away, because the fact fits more easily',
            'It slips sooner, because bigger windows read less carefully',
        ],
        answer=0,
        why='Quality drops as the prompt grows, whatever the window size. The fix is a shorter, more focused context, not more room.',
    ),
    angle=angle(
        pattern='Track the biggest, note the first',
        text="The big idea: measure each call's fill, its input tokens as a percent of the window, so you can clean up before a run hits the limit. Your code works out each call's fill in order, and `enumerate` gives each call's position from 0. It keeps the biggest fill so far, like a high score. It also notes the first position over 80, and the `first_over is None` check stops later ones replacing it. At the end it rounds the biggest fill to a whole number.",
        say='"I work out each call\'s fill as a percent of the window, keep the biggest, and note the first call over 80 percent, which is when to clean up."',
        classic=None,
    ),
    stack=stack('MLflow 3: input tokens per model call', """import mlflow
from mlflow.entities import SpanType

WINDOW = 128000   # your model's limit
trace = mlflow.get_trace(trace_id)
calls = trace.search_spans(
    span_type=SpanType.CHAT_MODEL)
for s in calls:
    use = s.get_attribute(
        "mlflow.chat.tokenUsage")
    if use:
        tokens = use["input_tokens"]
        pct = tokens * 100 // WINDOW
        print(s.name, pct)"""),
    exercise=exercise(
        title='Watch the Context Fill Up',
        topic='memory',
        difficulty='easy',
        fn='context_fill',
        prompt="""Your function gets two things:

- `input_tokens`: how many tokens each model call read, in order, like `[2500, 5200, 8300]`.
- `window`: the most tokens the model can read in one call, like `10000`.

A call's fill is its tokens as a percent of the window: `tokens * 100 / window`.

Return a list of two things:

- the biggest fill of any call, rounded to a whole number;
- the index (position, from 0) of the first call with a fill over 80. Exactly 80 does not count. If no call is over 80, use `None`.

If `input_tokens` is empty, return `[0, None]`.""",
        pattern='Work out each fill in one walk. Keep the biggest, and note the first index over 80.',
        target='one pass over the calls',
        realworld='Agents re-read their whole history on every call, so long runs creep toward a full context. Tracking the fill of each call shows when to clear old tool results or summarise, before the answers start to slip.',
        starter="""def context_fill(input_tokens, window):
    # your code here
    pass
""",
        solution="""def context_fill(input_tokens, window):
    peak = 0
    first_over = None
    for i, tokens in enumerate(input_tokens):
        fill = tokens * 100 / window
        if fill > peak:
            peak = fill
        if fill > 80 and first_over is None:
            first_over = i
    return [int(round(peak)), first_over]
""",
        cases=[
            case([2500, 5200, 8300, 9100], 10000, expected=[91, 2], sample=True),
            case([], 10000, expected=[0, None]),
            case([800, 790], 1000, expected=[80, None]),
            case([1000, 2000, 2500], 3000, expected=[83, 2]),
            case([9000, 4000, 8500], 10000, expected=[90, 0]),
            case([1000, 2000], 3000, expected=[67, None]),
        ],
        guided="""def context_fill(input_tokens, window):
    # Replace every ___ with real code, then run the tests.

    peak = 0            # biggest fill so far
    first_over = None   # first call over 80, not found yet
    for i, tokens in enumerate(input_tokens):
        # Step 1: tokens as a percent of the window.
        fill = ___
        # Step 2: keep the biggest fill.
        if fill > peak:
            peak = fill
        # Step 3: over 80, and none noted before? Note i.
        if ___:
            first_over = i
    # Step 4: round the peak to a whole number.
    return [int(round(peak)), first_over]
""",
        fills=['tokens * 100 / window', 'fill > 80 and first_over is None'],
        concepts=[
            [
                'enumerate',
                'Gives you the index (position, from 0) along with each item.',
                """for i, day in enumerate(["mon", "tue"]):
    print(i, day)   # 0 mon, then 1 tue""",
            ],
            [
                'None as "not found yet"',
                'Start with `None`, and check it with `is None`. Once you store a value, `is None` is False, so it is never overwritten.',
                """first_big = None
for n in [2, 7, 9]:
    if n > 5 and first_big is None:
        first_big = n
# first_big is 7""",
            ],
            [
                'Rounding to a whole number',
                '`round(x)` rounds to the nearest whole number. Wrapping it in `int(...)` makes sure you get 67, not 67.0.',
                """int(round(66.67))   # 67
int(round(83.3))    # 83""",
            ],
            [
                'Keeping the biggest so far',
                'Start at 0, then replace it whenever an item is bigger.',
                """best = 0
for n in [4, 9, 2]:
    if n > best: best = n
# best is 9""",
            ],
        ],
        byhand='The window is 10000. Call 0 read 2500 tokens: 2500 times 100, divided by 10000, is 25. Call 1 is 52. Call 2 is 83, the first fill over 80, so note index 2. Call 3 is 91, the biggest fill. It is over 80 too, but index 2 is already noted, so keep 2. Return [91, 2].',
        why='One pass over the calls, keeping two values up to date.',
        gotchas=[
            [
                'Only checking the last call',
                'After a cleanup or a summary the context shrinks, so the last call is not always the fullest. Look at every call.',
            ],
            [
                'Buying a bigger window',
                'A bigger window lets a run go on longer before it errors, but answers still get worse as the prompt grows. Keep the context short and focused instead.',
            ],
        ],
    ),
)

lesson(MODULE, 'summary_recall',
    title='What a summary forgets',
    learn=[
        'When the context gets too full, agents **compact** it: they swap old messages for a short summary. A vague "summarise this" prompt drops exact details like table names, ticket ids and error codes. The agent then redoes work, or says it is finished when it is not.',
        'Try the cheap fix first: clear old tool results, keeping only the note that each tool ran. If runs are still too long, summarise with required sections: the goal, decisions, exact names, ids and error codes, open tasks and the next step. Keep the last few messages word for word.',
        'To test a summary, **plant facts**: put a few details you will ask about later, like a table name, into a long run. Compact it, then ask **probe questions** about those details, like "Which table did we write to?", and count how many the agent still gets right. Judge a summary by whether the agent can still finish the task, not by how short it is.',
    ],
    example=example('A probe question after compaction', """planted: goal, table, ticket_id
summary: "Fix the HR tickets.
          Next: rerun the job."
probe:   Which table did we write to?
agent:   "I'm not sure."  (forgotten)"""),
    check=question(
        'After you add a summary step, runs are shorter, but the agent sometimes rewrites a table it already wrote. Which test catches this?',
        [
            'Check that each summary is under 500 words',
            'Ask the model whether its summary looks complete',
            'Plant facts, compact, then ask probe questions',
        ],
        answer=2,
        why="A summary's length and the model's own opinion say nothing about what was lost. Probe questions check whether the agent still knows the facts it needs to finish.",
    ),
    angle=angle(
        pattern='Check each planted fact in a set',
        text='The big idea: test a summary by planting facts, asking about them later, and counting how many the agent still gets right. Your code turns `answered` into a set, a collection built to answer "is this in it?" instantly, like a book\'s index. Then it checks each planted fact. A hit adds 1 to the count, and a miss goes on the forgotten list. Hits divided by facts planted, rounded to 2 places, is the share kept. The forgotten facts come out sorted A to Z.',
        say='"I plant facts, compact the run, then ask about them. I report the share the agent still knows and list what it forgot."',
        classic='two_sum',
    ),
    stack=stack('LangChain: clear tool results, then summarise', """from langchain.agents import create_agent
from langchain.agents.middleware import (
    ClearToolUsesEdit,
    ContextEditingMiddleware,
    SummarizationMiddleware,
)

agent = create_agent(
    model=llm,
    tools=tools,
    middleware=[
        # Cheap fix: past 60000 tokens, the
        # model sees "[cleared]" in place of
        # all but the 3 newest tool results.
        ContextEditingMiddleware(edits=[
            ClearToolUsesEdit(
                trigger=60000, keep=3)]),
        # Past 100000 tokens, summarise, and
        # keep the last 20 messages as they are.
        SummarizationMiddleware(
            model=llm,
            trigger=("tokens", 100000),
            keep=("messages", 20),
            summary_prompt=MY_PROMPT,
        ),
    ],
)
# MY_PROMPT asks for the goal, decisions,
# exact names, ids and the next step.
# It must contain {messages}."""),
    exercise=exercise(
        title='Score a Summary with Planted Facts',
        topic='memory',
        difficulty='easy',
        fn='summary_recall',
        prompt="""Your function gets two things:

- `planted`: short names for the facts you hid in a long agent run before it was summarised, like `["goal", "table", "next_step"]`.
- `answered`: the facts the agent still got right when you asked about them afterwards, like `["goal", "next_step"]`.

Return a dict with two keys:

- `"kept"`: how many planted facts are in `answered`, divided by how many were planted, rounded to 2 decimal places.
- `"forgotten"`: the planted facts that are not in `answered`, sorted A to Z.

Ignore any name in `answered` that was not planted. `planted` always has at least one fact.""",
        pattern='Look each planted fact up in a set of the answers. Count the hits and collect the misses.',
        target='one pass over the planted facts',
        realworld='Teams test compaction like this before they ship it: plant facts such as a table name or a ticket id, let the run compact, then ask probe questions. A low share kept means the summary prompt needs required sections.',
        starter="""def summary_recall(planted, answered):
    # your code here
    pass
""",
        solution="""def summary_recall(planted, answered):
    found = set(answered)
    hits = 0
    forgotten = []
    for fact in planted:
        if fact in found:
            hits += 1
        else:
            forgotten.append(fact)
    share = round(hits / len(planted), 2)
    return {"kept": share, "forgotten": sorted(forgotten)}
""",
        cases=[
            case(['goal', 'table', 'ticket_id', 'next_step', 'error_code'], ['goal', 'next_step', 'ticket_id'], expected={'kept': 0.6, 'forgotten': ['error_code', 'table']}, sample=True),
            case(['table', 'goal'], ['goal', 'table'], expected={'kept': 1.0, 'forgotten': []}),
            case(['table', 'file', 'goal'], [], expected={'kept': 0.0, 'forgotten': ['file', 'goal', 'table']}),
            case(['table', 'goal', 'next_step'], ['goal', 'weather', 'user_name'], expected={'kept': 0.33, 'forgotten': ['next_step', 'table']}),
            case(['ticket_id', 'error_code', 'table'], ['table', 'ticket_id'], expected={'kept': 0.67, 'forgotten': ['error_code']}),
        ],
        guided="""def summary_recall(planted, answered):
    # Replace every ___ with real code, then run the tests.

    found = set(answered)   # quick "is it in?" checks
    hits = 0                # planted facts still answered
    forgotten = []
    for fact in planted:
        # Step 1: did the agent still answer this fact?
        if ___:
            hits += 1
        else:
            forgotten.append(fact)
    # Step 2: the share kept, out of all planted facts.
    share = round(___, 2)
    # Step 3: the forgotten facts, A to Z.
    return {"kept": share, "forgotten": sorted(forgotten)}
""",
        fills=['fact in found', 'hits / len(planted)'],
        concepts=[
            [
                'Sets',
                'A set is a group of values with no repeats. Checking `x in some_set` is instant. `x in some_list` checks every item.',
                """colors = set(["red", "blue"])
"red" in colors     # True
"green" in colors   # False""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts x on the end of the list.',
                """names = []
names.append("Ana")   # ["Ana"]""",
            ],
            [
                'Dividing',
                '`/` always gives a decimal, even when both numbers are whole.',
                """3 / 5   # 0.6
4 / 2   # 2.0""",
            ],
            [
                'round',
                '`round(x, 2)` keeps 2 decimal places.',
                'round(2 / 3, 2)   # 0.67',
            ],
            [
                'len',
                '`len(items)` is how many items a list has.',
                'len(["a", "b", "c"])   # 3',
            ],
            [
                'sorted',
                '`sorted(items)` gives a new list in order: A to Z for words.',
                """sorted(["pear", "fig", "apple"])
# ["apple", "fig", "pear"]""",
            ],
        ],
        byhand='Five facts were planted. goal is in answered: 1 hit. table is not, so forgotten is ["table"]. ticket_id is in: 2 hits. next_step is in: 3 hits. error_code is not, so forgotten is ["table", "error_code"]. That is 3 hits out of 5, and 3 divided by 5 is 0.6. Sorted A to Z, the forgotten facts are ["error_code", "table"]. Return {"kept": 0.6, "forgotten": ["error_code", "table"]}.',
        why='One pass over the planted facts. Each check is a quick set look-up.',
        gotchas=[
            [
                'A generic summary prompt',
                'A prompt that just says "summarise the conversation" keeps the gist and drops the exact names. Require sections for table names, ids, error codes and the next step.',
            ],
            [
                'Judging a summary by its length',
                'A short summary looks efficient but can drop the one fact the agent needs. Judge it by whether the agent can still answer the probe questions and finish the task.',
            ],
        ],
    ),
)

lesson(MODULE, 'detect_loop',
    title='Guardrails for agents',
    learn=[
        'Agents in production need **guardrails**: limits that stop a run before it does damage or burns money. The simplest catches the same call repeated again and again.',
        'Production systems also cap total steps, tokens and time, and tell the model why it was stopped.',
        "In LangGraph, the step cap is `recursion_limit`. Its default in langgraph 1.2.11 is 10,007 steps, far too many to stop a stuck agent early. Always pass your own small limit, like 25.",
    ],
    example=example('A loop in a trace', """search('weather paris')
search('weather paris')
search('weather paris')   # stop here"""),
    check=question(
        'An agent alternates between two calls forever: A, B, A, B. Does a "same call 3 times in a row" check catch it?',
        [
            'Yes, it sees the same calls coming back',
            'No, so you also need a total step limit',
            'Only if you lower the limit to 2 calls',
        ],
        answer=1,
        why='No call repeats back to back, so you need other limits too.',
    ),
    angle=angle(
        pattern='Count repeats in a row',
        text="The big idea: the simplest guardrail stops an agent that makes the same call again and again. Your code remembers the previous call and a count of repeats in a row. If the current call matches the previous one, the count goes up by 1. If not, the count starts again at 1. As soon as the count reaches `limit`, it returns that call's position. If that never happens, it returns -1.",
        say='"I count how many identical calls come in a row, starting again at 1 when the call changes, and stop the agent once the count reaches the limit."',
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
    return "tools"

# And always set your own step limit:
graph.invoke(inputs,
    config={"recursion_limit": 25})"""),
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

lesson(MODULE, 'failure_counts',
    title='Label failures, then count',
    learn=[
        'With hundreds of failed runs, reading traces at random wastes time, and fixing them one by one never ends. Give each failed trace in a sample, say 50, one **failure label**: a short name for what went wrong. Then count the labels and fix the biggest group first.',
        'Use a fixed list of labels, so the same problem always gets the same name. A research list called **MAST** names the common ways agents fail, such as repeating steps, not knowing when to stop, ignoring the task, and weak or missing checks.',
        'A person labels the first batch by hand. A judge model can help label more later, once its labels match yours. Save each label on its trace in MLflow, and keep a few example ids per label so you can open and read them.',
    ],
    example=example('Failed runs, counted by label', """label           count  read first
repeated step      41  t-193, t-207
never stopped      22  t-150, t-311
ignored task        9  t-402, t-417
# fix repeated step first"""),
    check=question(
        'You have 300 failed runs and one week to improve the agent. What should you do first?',
        [
            'Label a sample, count the labels, fix the biggest group',
            'Fix the newest failure, then the one before it, and so on',
            'Rewrite the whole system prompt, then rerun every task',
        ],
        answer=0,
        why='Counting labels shows which single fix helps the most runs. Going one by one, or rewriting everything, uses up the week without knowing what mattered.',
    ),
    angle=angle(
        pattern='Group by label, count, then sort',
        text='The big idea: label each failed trace, count the labels, and fix the biggest group first. Your code sorts the failures into piles by label, kept in a dict: a lookup table from each label to its list of ids. Then it makes one row per label: the label, how many ids it has, and its first `n` ids. Last, it sorts the rows so the biggest count comes first, and labels with the same count go A to Z.',
        say='"I group failed traces by label, count each group and keep a few example ids. Then I sort biggest first, so I fix the most common failure first."',
        classic='group_anagrams',
    ),
    stack=stack('MLflow 3: save labels on traces, then look them up', """import mlflow
from mlflow.entities import AssessmentSource

# A person's label, saved on the trace
mlflow.log_feedback(
    trace_id=trace_id,
    name="failure_label",
    value="repeated step",
    source=AssessmentSource(
        source_type="HUMAN",
        source_id="reviewer"),
    rationale="Same search 4 times",
)

# Later: every trace with that label
df = mlflow.search_traces(filter_string=
    "feedback.failure_label = 'repeated step'")
print(len(df))"""),
    exercise=exercise(
        title='Count Failures by Label',
        topic='agentops',
        difficulty='medium',
        fn='failure_counts',
        prompt="""Your function gets two things:

- `failures`: a list of failed traces, each already given a label, like `{"id": "t1", "label": "repeated step"}`.
- `n`: how many example ids to keep for each label, like `2`.

Group the failures by label. For each label, make a list of three things: the label, how many failures have it, and the ids of its first `n` failures in the order they appear (all of them, if there are fewer).

Return these lists sorted with the biggest count first. If two labels have the same count, put them A to Z by label. If `failures` is empty, return `[]`.""",
        pattern='Group the ids by label in a dict of lists, make one row per label, then sort by count with the label as the tie-break.',
        target='one pass to group, then one sort of the labels',
        realworld='This is error analysis for agents: label a sample of failed traces, count, and fix the biggest group first. Then rerun the evals and count again to check that the fix worked.',
        starter="""def failure_counts(failures, n):
    # your code here
    pass
""",
        solution="""def failure_counts(failures, n):
    groups = {}
    for failure in failures:
        label = failure["label"]
        if label not in groups:
            groups[label] = []
        groups[label].append(failure["id"])
    rows = []
    for label in groups:
        ids = groups[label]
        rows.append([label, len(ids), ids[:n]])
    rows.sort(key=lambda row: (-row[1], row[0]))
    return rows
""",
        cases=[
            case([
                {'id': 't1', 'label': 'repeated step'},
                {'id': 't2', 'label': 'ignored task'},
                {'id': 't3', 'label': 'repeated step'},
                {'id': 't4', 'label': 'never stopped'},
                {'id': 't5', 'label': 'repeated step'},
            ], 2, expected=[['repeated step', 3, ['t1', 't3']], ['ignored task', 1, ['t2']], ['never stopped', 1, ['t4']]], sample=True),
            case([], 2, expected=[]),
            case([
                {'id': 'a1', 'label': 'weak check'},
                {'id': 'a2', 'label': 'ignored task'},
            ], 3, expected=[['ignored task', 1, ['a2']], ['weak check', 1, ['a1']]]),
            case([
                {'id': 'x1', 'label': 'weak check'},
                {'id': 'x2', 'label': 'never stopped'},
                {'id': 'x3', 'label': 'never stopped'},
                {'id': 'x4', 'label': 'never stopped'},
                {'id': 'x5', 'label': 'weak check'},
            ], 1, expected=[['never stopped', 3, ['x2']], ['weak check', 2, ['x1']]]),
            case([
                {'id': 'r1', 'label': 'repeated step'},
                {'id': 'r2', 'label': 'repeated step'},
                {'id': 'r3', 'label': 'repeated step'},
                {'id': 'r4', 'label': 'repeated step'},
            ], 3, expected=[['repeated step', 4, ['r1', 'r2', 'r3']]]),
            case([{'id': 'b1', 'label': 'never stopped'}], 5, expected=[['never stopped', 1, ['b1']]]),
        ],
        guided="""def failure_counts(failures, n):
    # Replace every ___ with real code, then run the tests.

    # Step 1: group the ids by label, in order.
    groups = {}   # label: list of its ids
    for failure in failures:
        label = failure["label"]
        if label not in groups:
            groups[label] = []
        groups[label].append(failure["id"])

    # Step 2: one row per label: label, count, first n ids.
    rows = []
    for label in groups:
        ids = groups[label]
        rows.append([label, ___, ___])

    # Step 3: biggest count first, then label A to Z.
    rows.sort(key=lambda row: (___, row[0]))
    return rows
""",
        fills=['len(ids)', 'ids[:n]', '-row[1]'],
        concepts=[
            [
                'A dict of lists',
                'Start an empty list the first time a key shows up, then append to that list.',
                """pets = {}
if "cats" not in pets: pets["cats"] = []
pets["cats"].append("Tom")""",
            ],
            [
                'Looping over a dict',
                '`for key in d:` gives you each key in turn. Use `d[key]` to get its value.',
                """ages = {"ann": 30, "bob": 25}
for name in ages:
    print(name, ages[name])""",
            ],
            [
                'Slicing to a limit',
                '`items[:3]` gives at most the first 3 items. If the list is shorter, you get all of it.',
                """[1, 2, 3, 4][:2]   # [1, 2]
[1][:2]            # [1]""",
            ],
            [
                'len',
                '`len(items)` is how many items a list has.',
                'len(["a", "b", "c"])   # 3',
            ],
            [
                'Sorting with a tie-break',
                '`key=` says what to compare. `lambda p: ...` is a tiny function that gives back what to compare. `(-p[1], p[0])` compares the number first, with a minus sign so the biggest comes first. Equal numbers then go by name, A to Z.',
                """pets = [["cat", 3], ["dog", 9],
        ["ant", 9]]
pets.sort(key=lambda p: (-p[1], p[0]))
# ant 9, dog 9, cat 3""",
            ],
        ],
        byhand='Group by label. repeated step gets t1, t3 and t5. ignored task gets t2. never stopped gets t4. repeated step has 3 failures, so keep its first 2 ids, t1 and t3. ignored task and never stopped have 1 each, a tie, so they go A to Z: ignored task first. Return [["repeated step", 3, ["t1", "t3"]], ["ignored task", 1, ["t2"]], ["never stopped", 1, ["t4"]]].',
        why='One pass over the failures to group them, then one sort of the labels.',
        gotchas=[
            [
                'Labels that drift',
                '"loop", "looping" and "repeated step" count as three different labels, so the biggest group looks smaller than it is. Pick labels from a fixed list.',
            ],
            [
                'Trusting a tool to find the broken step',
                'A judge model can name the kind of failure fairly well, but tools that claim to find the exact step where a run went wrong are still unreliable. A person checks before you act on it.',
            ],
        ],
    ),
)
