"""Agent teams: When one agent isn't enough: whether you need a team, splitting the work, fanning out, checking, and what it costs."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('agent-teams', 'Agent teams', "When one agent isn't enough: whether you need a team, splitting the work, fanning out, checking, and what it costs.")

lesson(MODULE, 'need_a_team',
    title='Do you need a team?',
    learn=[
        "Most tasks don't need a **team** of agents (several agents that split up the work). Teams use several times more tokens, and in one large study every team design did worse on step-by-step tasks.",
        'Picture a **ladder**: one model call, then a **fixed workflow** (steps your code runs in a set order), then one agent with tools, then a team. Climb a step only for a problem you can name, like a prompt full of if-then branches.',
        "Before adding a second agent, fix the first one's tool names and descriptions, then run your evals again. A team fits work that splits into **independent parts**: pieces you could hand to people who never talk to each other.",
        'One rough hint from that study: once one agent passed about 45 percent of the tasks, more agents helped little or made it worse. Treat it as a hint, and check it on your own eval.',
    ],
    example=example('Four jobs, four steps on the ladder', """Summarise one ticket
  → one call
Tag it, route it, draft a reply
  → workflow (same steps every time)
Look up an order, maybe refund it
  → one agent with tools
Research 6 vendors, each on its own,
and one agent passes 30 percent
  → try a team, then measure it"""),
    check=question(
        'One agent passes 70 percent of your eval. Most misses come from it mixing up two tools with similar names. What should you try first?',
        [
            'Rename and describe the two tools clearly, then rerun the eval',
            'Add a second agent, so each agent owns one of the two tools',
            'Move to a bigger model, so it can tell the two tools apart',
        ],
        answer=0,
        why="Overlapping tools are a problem you can fix on the step you're on, for free. A team costs several times more tokens, and 70 percent is past the point where extra agents tended to help.",
    ),
    angle=angle(
        pattern='Climb the ladder',
        text="The big idea: most tasks don't need a team, so pick the lowest step on the ladder that does the job. Your code checks four rules in order and returns the first that fits. Fixed steps mean a workflow. No tools needed means one model call. A team wins only if the work splits into at least 2 independent parts and one agent passes less than 0.45 of your eval. Everything else gets one agent. There is no loop here, just a few questions asked in order.",
        say='"I start with the simplest design and climb from one call to a workflow, one agent, then a team, only for a problem I can name and my eval confirms."',
        classic=None,
    ),
    stack=stack('LangGraph and LangChain: the four steps', """from langchain.agents import create_agent
from langgraph.graph import StateGraph, START

# llm: your model on the AI gateway,
# like ChatDatabricks(endpoint=ENDPOINT)

# 1. One call
llm.invoke("Summarise: " + ticket)

# 2. A workflow: your code fixes
#    the order of the steps
b = StateGraph(State)
b.add_node("tag", tag)
b.add_node("reply", reply)
b.add_edge(START, "tag")
b.add_edge("tag", "reply")

# 3. One agent: the model picks
#    which tool to call, and when
agent = create_agent(
    llm, tools=[lookup_order, refund])

# 4. A team: helper agents become
#    the tools of one main agent
#    (the next lesson)"""),
    exercise=exercise(
        title='Pick the Simplest Design',
        topic='agents',
        difficulty='easy',
        fn='need_a_team',
        prompt="""`task` is a dict that describes a job for your app, like `{"fixed_steps": False, "needs_tools": True, "independent_parts": 3, "one_agent_pass_rate": 0.3}`. Its keys:

- `fixed_steps`: True if the steps always run in the same order.
- `needs_tools`: True if the job must look things up or take actions.
- `independent_parts`: how many pieces could be done separately.
- `one_agent_pass_rate`: the share of your eval that one agent passes, from 0 to 1.

Check these rules in order. Return the answer of the first one that fits:

- `fixed_steps` is True: return `"workflow"`.
- `needs_tools` is False: return `"one call"`.
- `independent_parts` is at least 2 and `one_agent_pass_rate` is below 0.45: return `"team"`. A rate of exactly 0.45 is not below.
- Anything else: return `"one agent"`.""",
        pattern='Rules checked in order: the first one that fits gives the answer.',
        target='a few checks in order, no loop',
        realworld='Every major agent builder gives the same advice: start with the simplest design that works. A team costs several times more tokens, so it has to earn its place on your eval.',
        starter="""def need_a_team(task):
    # your code here
    pass
""",
        solution="""def need_a_team(task):
    if task["fixed_steps"]:
        return "workflow"
    if not task["needs_tools"]:
        return "one call"
    parts = task["independent_parts"]
    rate = task["one_agent_pass_rate"]
    if parts >= 2 and rate < 0.45:
        return "team"
    return "one agent"
""",
        cases=[
            case({'fixed_steps': False, 'needs_tools': True, 'independent_parts': 3, 'one_agent_pass_rate': 0.3}, expected='team', sample=True),
            case({'fixed_steps': True, 'needs_tools': True, 'independent_parts': 3, 'one_agent_pass_rate': 0.2}, expected='workflow'),
            case({'fixed_steps': False, 'needs_tools': False, 'independent_parts': 1, 'one_agent_pass_rate': 0.9}, expected='one call'),
            case({'fixed_steps': False, 'needs_tools': True, 'independent_parts': 2, 'one_agent_pass_rate': 0.44}, expected='team'),
            case({'fixed_steps': False, 'needs_tools': True, 'independent_parts': 1, 'one_agent_pass_rate': 0.2}, expected='one agent'),
            case({'fixed_steps': False, 'needs_tools': True, 'independent_parts': 4, 'one_agent_pass_rate': 0.45}, expected='one agent'),
        ],
        guided="""def need_a_team(task):
    # Replace every ___ with real code, then run the tests.

    # Step 1: same steps every time? A workflow.
    if task["fixed_steps"]:
        return "workflow"
    # Step 2: no tools needed? One call will do.
    if ___:
        return "one call"
    parts = task["independent_parts"]
    rate = task["one_agent_pass_rate"]
    # Step 3: at least 2 parts, and the rate
    #         below 0.45? Then a team.
    if ___:
        return "team"
    # Step 4: anything else.
    return ___
""",
        fills=['not task["needs_tools"]', 'parts >= 2 and rate < 0.45', '"one agent"'],
        concepts=[
            [
                'Reading a dict',
                '`d["key"]` gives the value stored under that key.',
                """pet = {"name": "Rex", "age": 3}
pet["age"]   # 3""",
            ],
            [
                'not',
                '`not x` turns True into False, and False into True.',
                """raining = False
not raining   # True""",
            ],
            [
                'and',
                '`a and b` is True only when both sides are True.',
                """age = 20
age >= 18 and age < 65   # True""",
            ],
            [
                'Returning early',
                '`return` ends the function right there. So with rules in order, the first rule that fits wins and the rest never run.',
                """def size(n):
    if n > 100:
        return 'big'
    return 'small'""",
            ],
        ],
        byhand='fixed_steps is False, so it is not a workflow. needs_tools is True, so one call is not enough. independent_parts is 3, which is at least 2, and the pass rate 0.3 is below 0.45. Return "team".',
        why='A few checks, each one a dict lookup.',
        gotchas=[
            [
                'Reaching for a team first',
                'A team costs several times more tokens and adds hand-offs that can lose details. Name the problem it fixes before you build it.',
            ],
            [
                'Treating 0.45 as a law',
                'It is a rough hint from one study. Your own eval, with one agent and the team run side by side, makes the call.',
            ],
        ],
    ),
)

lesson(MODULE, 'one_writer',
    title='Split by what each agent needs to know',
    learn=[
        'Splitting agents by job title (a planner, a coder, a tester) loses details at every hand-off, like a game of telephone. Split by **context** instead: what each agent needs to know to do its piece.',
        'Give each thing that changes **one writer**: the final answer, a table, a file. Helpers that share it only read it and report back. When two agents change the same thing, one quietly overwrites the other.',
        'Give each helper a short **brief**: the goal, what is out of scope, what its report should look like, and which tools to use. Vague briefs lead to helpers doing the same work twice.',
        'In LangChain, the helpers become tools of one main agent made with `create_agent`. The older langgraph-supervisor package is archived, so skip tutorials built on it.',
    ],
    example=example('Who reads and who writes', """tasks = {
  "triage":  {"reads": ["tickets"],
              "writes": ["tags"]},
  "billing": {"reads": ["invoices"],
              "writes": ["tags"]},
  "reply":   {"reads": ["tags"],
              "writes": ["drafts"]},
}
# "tags" has two writers: a clash.
# Fix: billing reports to triage,
# and only triage writes "tags"."""),
    check=question(
        'Two helper agents run at the same time, and both may update the same ticket\'s tags. What is the safest way to set this up?',
        [
            'Let both write, and keep whichever update lands last',
            'Run them one after the other, so they never overlap',
            'Have both report back, and let one agent write the tags',
        ],
        answer=2,
        why='Two writers on one thing means one quietly overwrites the other. With one writer, the helpers can still run side by side, and every change has a single owner.',
    ),
    angle=angle(
        pattern='Count the writers of each thing',
        text="The big idea: give each thing that changes one writer, because when two agents change the same thing, one quietly overwrites the other. Your code goes through every task's `writes` list and counts how many tasks write each resource. The counts live in a dict, a lookup table from each resource's name to its count. Reads are ignored, since sharing what you read is fine. Then it keeps every resource with a count above 1 and returns them sorted A to Z.",
        say='"I split helpers by what they need to know, and I give each shared thing one writer, so nothing gets quietly overwritten."',
        classic='group_anagrams',
    ),
    stack=stack('LangChain: helpers as tools, one writer', """from langchain.agents import create_agent
from langchain.tools import tool

# A helper: read-only tools, a brief
billing = create_agent(
    llm, tools=[read_invoices],
    system_prompt=BILLING_BRIEF)

@tool
def ask_billing(question: str) -> str:
    \"\"\"Billing facts for a ticket.\"\"\"
    out = billing.invoke({"messages": [
        {"role": "user",
         "content": question}]})
    # its final message is the report
    return out["messages"][-1].content

# Only the main agent writes tags.
# (Not create_supervisor: the
# langgraph-supervisor package
# is archived.)
main = create_agent(
    llm, tools=[ask_billing, save_tags])"""),
    exercise=exercise(
        title='Find Two Writers',
        topic='agents',
        difficulty='easy',
        fn='one_writer',
        prompt="""`tasks` is a dict of helper tasks. Each key is a task's name, and its value lists what it reads and what it writes, like `{"triage": {"reads": ["tickets"], "writes": ["tags"]}}`.

Find every resource (a table, a file, a field) that more than one task writes. Only writes count: many tasks reading the same thing is fine.

Return those resources as a list, sorted A to Z. If no resource has more than one writer, return `[]`.""",
        pattern='Count by key: count the writers of each resource in a dict, then keep the ones above 1.',
        target='one pass over the tasks, then one over the counts',
        realworld="Teams that run agents side by side give each shared thing one writer and keep the other helpers read-only. When Anthropic ran 16 coding agents on one codebase, they overwrote each other's fixes until the work was split by file.",
        starter="""def one_writer(tasks):
    # your code here
    pass
""",
        solution="""def one_writer(tasks):
    writers = {}
    for name in tasks:
        for thing in tasks[name]["writes"]:
            writers[thing] = writers.get(thing, 0) + 1
    clashes = []
    for thing in writers:
        if writers[thing] > 1:
            clashes.append(thing)
    return sorted(clashes)
""",
        cases=[
            case({
                'triage': {'reads': ['tickets'], 'writes': ['tags']},
                'billing': {'reads': ['invoices'], 'writes': ['tags', 'notes']},
                'reply': {'reads': ['tags'], 'writes': ['drafts']},
            }, expected=['tags'], sample=True),
            case({
                'search': {'reads': ['docs'], 'writes': ['notes']},
                'answer': {'reads': ['notes'], 'writes': ['reply']},
            }, expected=[]),
            case({}, expected=[]),
            case({
                'a': {'reads': [], 'writes': ['orders', 'drafts']},
                'b': {'reads': ['orders'], 'writes': ['drafts']},
                'c': {'reads': [], 'writes': ['orders', 'log']},
            }, expected=['drafts', 'orders']),
            case({
                'x': {'reads': [], 'writes': ['answer']},
                'y': {'reads': [], 'writes': ['answer']},
                'z': {'reads': [], 'writes': ['answer']},
            }, expected=['answer']),
            case({
                'wiki': {'reads': ['kb'], 'writes': []},
                'faq': {'reads': ['kb'], 'writes': []},
                'editor': {'reads': ['kb'], 'writes': ['kb']},
            }, expected=[]),
        ],
        guided="""def one_writer(tasks):
    # Replace every ___ with real code, then run the tests.

    # Count how many tasks write each resource.
    writers = {}
    for name in tasks:
        for thing in tasks[name]["writes"]:
            # Step 1: add 1 to this resource's count
            #         (it starts at 0).
            writers[thing] = ___ + 1
    # Step 2: keep resources with more than one writer.
    clashes = []
    for thing in writers:
        if ___:
            clashes.append(thing)
    # Step 3: sorted, A to Z.
    return ___
""",
        fills=['writers.get(thing, 0)', 'writers[thing] > 1', 'sorted(clashes)'],
        concepts=[
            [
                'A dict inside a dict',
                "`d['a']['b']` looks up 'a', then looks up 'b' in what it found.",
                """pets = {'rex': {'age': 3}}
pets['rex']['age']   # 3""",
            ],
            [
                'Looping over a dict',
                '`for k in d` gives each key in turn. `d[k]` is its value.',
                """ages = {'ann': 30, 'bo': 25}
for name in ages:
    print(name, ages[name])""",
            ],
            [
                'Counting with a dict',
                '`d.get(k, 0)` gives the count for `k`, or 0 if `k` is not there yet. Add 1 to it each time you see `k`.',
                """seen = {}
for word in ['hi', 'yo', 'hi']:
    seen[word] = seen.get(word, 0) + 1
# seen is {'hi': 2, 'yo': 1}""",
            ],
            [
                'A loop inside a loop',
                'The inner loop runs fully for each turn of the outer loop.',
                """for row in [[1, 2], [3]]:
    for n in row:
        print(n)   # 1, 2, then 3""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts `x` on the end of the list.',
                """fruit = ['fig']
fruit.append('kiwi')
# fruit is ['fig', 'kiwi']""",
            ],
            [
                'sorted',
                '`sorted(items)` gives a new list in order, A to Z for words.',
                "sorted(['pear', 'apple'])   # ['apple', 'pear']",
            ],
        ],
        byhand='Go through each task\'s writes. triage writes tags, so tags has 1 writer. billing writes tags and notes, so tags has 2 and notes has 1. reply writes drafts, so drafts has 1. reply also reads tags, but reads don\'t count. Only tags has more than one writer. Return ["tags"].',
        why='Each write is counted once, then each resource is checked once.',
        gotchas=[
            [
                'Counting reads as clashes',
                'Many helpers reading the same table is fine and common. Only two writers on one thing is a clash.',
            ],
            [
                "Rewording a helper's report",
                'The main agent sees only the helper\'s final message. If it rewrites that in its own words, details get lost, so ask helpers to put every finding in the final message and pass it on as it is.',
            ],
        ],
    ),
)

lesson(MODULE, 'gather_results',
    title='Fan out, then gather',
    learn=[
        'When a job splits into independent parts, like searching five sources, helpers can work at the same time. This is **fan-out**: send each part to its own worker, then **gather** the results in one place.',
        'In LangGraph, `Send` starts one worker per part. A **reducer** (a rule for combining updates; here `operator.add`, which joins lists) lets every worker add to the same list. Without one, two workers writing the same key make the run fail with an error.',
        'Keep the workers **read-only**: they change nothing outside the graph, and one step after the gather does any writing.',
        'The gather waits for the slowest worker, so one stuck search holds up the whole run. Give each worker a **timeout**, and carry on with whatever came back in time.',
    ],
    example=example('Three workers, a 10 second timeout', """wiki      2 seconds   done
tickets   4 seconds   done
billing  30 seconds   stopped at 10
→ the gather runs after 10 seconds,
  not 30
  results:   wiki, tickets
  timed out: billing"""),
    check=question(
        'Five search workers run at the same time. Four finish in 2 seconds, and one takes 40 seconds. With no timeouts, when does the gather step run?',
        [
            'After about 2 seconds, with the four results it has',
            'After about 40 seconds, once the slowest worker is done',
            'After about 10 seconds, the average time of the five',
        ],
        answer=1,
        why='The gather waits for every worker it started, so the slowest one sets the pace. A timeout on each worker caps that wait.',
    ),
    angle=angle(
        pattern='Wait for the slowest, with a limit',
        text='The big idea: workers run at the same time and the gather waits for the slowest one, so each worker needs a timeout. Your code goes through the workers once. For each, it works out how long you would wait: its time, but never more than `timeout`. It keeps the biggest of those, which is how long the gather waits. Workers within the timeout add their result. Late ones add their name to the timed-out list. It is like waiting for friends at a restaurant, but only until a set time.',
        say='"I fan out read-only workers, gather what they find, and give each one a timeout, so one slow source can\'t hold up the whole answer."',
        classic=None,
    ),
    stack=stack('LangGraph: Send, a reducer and a timeout', """import asyncio, operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START
from langgraph.types import Send

class State(TypedDict):
    sources: list[str]
    # reducers: join every worker's list
    found: Annotated[list, operator.add]
    late: Annotated[list, operator.add]

def fan_out(state):
    return [
        Send("search", {"source": s})
        for s in state["sources"]]

async def search(job):
    src = job["source"]
    try:
        result = await asyncio.wait_for(
            search_tool(src),
            timeout=10)
        return {"found": [result]}
    except asyncio.TimeoutError:
        return {"late": [src]}

b = StateGraph(State)
b.add_node("search", search)
b.add_node("gather", gather)
b.add_conditional_edges(
    START, fan_out, ["search"])
b.add_edge("search", "gather")
# add_node also takes timeout=, but a
# timeout there stops the whole run.
# async nodes: run it with
# await b.compile().ainvoke(...)"""),
    exercise=exercise(
        title='Gather What Came Back',
        topic='agents',
        difficulty='medium',
        fn='gather_results',
        prompt="""Your function gets two things:

- `workers`: the helpers you started at the same time. Each is a dict like `{"name": "wiki", "seconds": 2, "result": "3 pages"}`: its name, how many seconds it takes, and what it finds.
- `timeout`: the most seconds you wait for any one worker, like `10`.

A worker is in time if its `seconds` is at most `timeout`. Otherwise it is late. Return a dict with three keys:

- `"waited"`: how long the gather waits: the longest time any worker ran, where a late worker counts as `timeout`. Use 0 if there are no workers.
- `"results"`: the `result` of each worker in time, in the order of `workers`.
- `"timed_out"`: the names of the late workers, in the order of `workers`.""",
        pattern='One pass with a running biggest value, putting each worker in one of two lists.',
        target='one pass over the workers',
        realworld='Research agents send several searches out at once and gather the answers. The lead agent waits for the whole batch, so one slow helper delays everything unless each helper has a timeout.',
        starter="""def gather_results(workers, timeout):
    # your code here
    pass
""",
        solution="""def gather_results(workers, timeout):
    waited = 0
    results = []
    late = []
    for w in workers:
        ran = min(w["seconds"], timeout)
        if ran > waited:
            waited = ran
        if w["seconds"] <= timeout:
            results.append(w["result"])
        else:
            late.append(w["name"])
    return {"waited": waited, "results": results,
            "timed_out": late}
""",
        cases=[
            case([
                {'name': 'wiki', 'seconds': 2, 'result': '3 pages'},
                {'name': 'billing', 'seconds': 30, 'result': '2 invoices'},
                {'name': 'tickets', 'seconds': 4, 'result': '5 tickets'},
            ], 10, expected={'waited': 10, 'results': ['3 pages', '5 tickets'], 'timed_out': ['billing']}, sample=True),
            case([
                {'name': 'a', 'seconds': 3, 'result': 'x'},
                {'name': 'b', 'seconds': 7, 'result': 'y'},
            ], 10, expected={'waited': 7, 'results': ['x', 'y'], 'timed_out': []}),
            case([
                {'name': 'a', 'seconds': 10, 'result': 'x'},
                {'name': 'b', 'seconds': 11, 'result': 'y'},
            ], 10, expected={'waited': 10, 'results': ['x'], 'timed_out': ['b']}),
            case([], 5, expected={'waited': 0, 'results': [], 'timed_out': []}),
            case([
                {'name': 'zeta', 'seconds': 20, 'result': 'z'},
                {'name': 'alpha', 'seconds': 30, 'result': 'a'},
            ], 15, expected={'waited': 15, 'results': [], 'timed_out': ['zeta', 'alpha']}),
            case([
                {'name': 'slow', 'seconds': 8, 'result': 's'},
                {'name': 'fast', 'seconds': 1, 'result': 'f'},
                {'name': 'mid', 'seconds': 5, 'result': 'm'},
            ], 9, expected={'waited': 8, 'results': ['s', 'f', 'm'], 'timed_out': []}),
        ],
        guided="""def gather_results(workers, timeout):
    # Replace every ___ with real code, then run the tests.

    waited = 0
    results = []
    late = []
    for w in workers:
        # Step 1: how long it ran. Late counts as timeout.
        ran = ___
        if ran > waited:
            waited = ran
        # Step 2: in time? Keep its result.
        if ___:
            results.append(w["result"])
        else:
            # Step 3: late. Keep its name.
            late.append(___)
    return {"waited": waited, "results": results,
            "timed_out": late}
""",
        fills=['min(w["seconds"], timeout)', 'w["seconds"] <= timeout', 'w["name"]'],
        concepts=[
            [
                'min of two numbers',
                '`min(a, b)` gives the smaller one. It caps a value: `min(x, 10)` is never more than 10.',
                """min(30, 10)   # 10
min(4, 10)    # 4""",
            ],
            [
                'Keeping the biggest so far',
                'Start at 0, and whenever you see something bigger, keep it instead.',
                """best = 0
for score in [3, 8, 5]:
    if score > best:
        best = score   # ends as 8""",
            ],
            [
                'if and else',
                '`else` runs when the `if` test is False, so each item goes down exactly one path.',
                """if age >= 18:
    adults.append(name)
else:
    kids.append(name)""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts `x` on the end of the list, so the list keeps the order you added things in.',
                """fruit = ['fig']
fruit.append('kiwi')
# fruit is ['fig', 'kiwi']""",
            ],
        ],
        byhand='timeout is 10. wiki takes 2 seconds, so it is in time: keep "3 pages". billing takes 30, so it is late: it counts as 10 seconds, and its name goes on the late list. tickets takes 4, in time: keep "5 tickets". The longest wait is 10. Return {"waited": 10, "results": ["3 pages", "5 tickets"], "timed_out": ["billing"]}.',
        why='One look at each worker.',
        gotchas=[
            [
                'Two workers, one key',
                'In LangGraph, two workers writing the same plain state key stop the run with InvalidUpdateError. Give the key a reducer, like `Annotated[list, operator.add]`.',
            ],
            [
                'No timeout on a worker',
                'The gather waits for the slowest worker, so one stuck API call stalls the whole run, and the person waiting gets nothing.',
            ],
        ],
    ),
)

lesson(MODULE, 'handoff_kept',
    title='Did the hand-off lose it?',
    learn=[
        "In a team, the main agent sees only each helper's **final message**. If it retells that message in its own words, details fall out, like a game of telephone. The answer can still read well while the one fact that mattered, like an order number, is gone.",
        'So check the **hand-off** (the moment one agent passes its work to another): list the facts a helper found, and see which ones reach the final answer word for word. The share kept says how much the hand-off loses, and the lost list says what.',
        'The fix is in the prompts. Helpers put every finding in their final message, and the main agent passes it on word for word. In LangChain\'s tests, passing helper answers on unchanged, instead of rewording them, made the answers nearly 50 percent better.',
        'Grade the final answer first. Then add hand-off checks, because hand-offs are where teams lose information.',
    ],
    example=example('One helper, one final answer', """The researcher found:
  order 4412
  refund approved
  card ends 0099
Final answer:
  "Order 4412: refund approved.
   It reaches you in 5 days."
kept: 2 of 3, about 0.67
lost: card ends 0099"""),
    check=question(
        "Your team's answers often leave out the order number, yet the trace shows the research helper found it. What should you try first?",
        [
            'Add one more helper that looks up the order number again',
            'Give the main agent a bigger model, so it remembers more',
            'Have helpers report every finding, passed on word for word',
        ],
        answer=2,
        why='The fact was found, then lost at the hand-off. Another helper or a bigger model pays more for the same leak; passing the report on unchanged closes it.',
    ),
    angle=angle(
        pattern='Check each fact against the answer',
        text="The big idea: hand-offs lose details when the main agent rewords a helper's message, so check which facts reach the final answer. Your code turns the final answer into lower case once. Then for each fact, it uses `in` to ask whether the text contains the lower-case fact anywhere. Missing facts go into the lost list. The share kept is the facts found divided by all the facts, and the lost list comes back sorted A to Z. With no facts at all, nothing was lost, so it returns 1.0.",
        say='"I grade the final answer first, then check the hand-offs: which facts each helper found actually reach the answer, and which got lost."',
        classic=None,
    ),
    stack=stack('MLflow 3: a scorer that checks the hand-off', """from mlflow.entities import (
    Feedback, SpanType)
from mlflow.genai.scorers import scorer

# The researcher runs inside
# mlflow.start_span(name="researcher",
#   span_type=SpanType.AGENT)
# and sets its outputs to
# {"facts": [...]}.

@scorer
def handoff(trace, outputs):
    helper = trace.search_spans(
        span_type=SpanType.AGENT,
        name="researcher")[0]
    facts = helper.outputs["facts"]
    final = str(outputs).lower()
    kept = []
    for f in facts:
        if f.lower() in final:
            kept.append(f)
    share = len(kept) / len(facts)
    return Feedback(
        value=round(share, 2),
        rationale="kept " + str(kept))

# mlflow.genai.evaluate(data=data,
#   predict_fn=run_team,
#   scorers=[end_state, handoff])"""),
    exercise=exercise(
        title='What Got Lost',
        topic='agents',
        difficulty='easy',
        fn='handoff_kept',
        prompt="""Your function gets two things:

- `found`: the facts a helper reported, as short strings, like `["order 4412", "refund approved"]`.
- `final`: the text of the final answer, like `"Order 4412: refund approved."`.

A fact is kept if it appears inside `final`, ignoring upper and lower case. Return a dict:

- `"kept"`: the share of facts kept, from 0 to 1, rounded to 2 decimal places.
- `"lost"`: the facts that were not kept, sorted A to Z.

If `found` is empty, return `{"kept": 1.0, "lost": []}`.""",
        pattern='Check each fact against the text, and keep the misses in a list.',
        target='one pass over the facts',
        realworld="LangChain found its simple supervisor lost quality by rewording its helpers' answers. Passing them on unchanged made answers nearly 50 percent better, and a hand-off check is how you spot the leak.",
        starter="""def handoff_kept(found, final):
    # your code here
    pass
""",
        solution="""def handoff_kept(found, final):
    if len(found) == 0:
        return {"kept": 1.0, "lost": []}
    text = final.lower()
    lost = []
    for fact in found:
        if fact.lower() not in text:
            lost.append(fact)
    kept = len(found) - len(lost)
    share = kept / len(found)
    return {"kept": round(share, 2),
            "lost": sorted(lost)}
""",
        cases=[
            case(['order 4412', 'refund approved', 'card ends 0099'],
                 'Order 4412: refund approved. It reaches you in 5 days.',
                 expected={'kept': 0.67, 'lost': ['card ends 0099']}, sample=True),
            case(['Refund Approved', '5 days'], 'refund approved, back in 5 days',
                 expected={'kept': 1.0, 'lost': []}),
            case([], 'Anything at all.', expected={'kept': 1.0, 'lost': []}),
            case(['order 77', 'late fee'], 'Sorry, I could not find that.',
                 expected={'kept': 0.0, 'lost': ['late fee', 'order 77']}),
            case(['refund approved', 'order 4412', 'ships monday'],
                 'We approved the refund for order 4412.',
                 expected={'kept': 0.33, 'lost': ['refund approved', 'ships monday']}),
        ],
        guided="""def handoff_kept(found, final):
    # Replace every ___ with real code, then run the tests.

    # No facts? Nothing could be lost.
    if len(found) == 0:
        return {"kept": 1.0, "lost": []}
    # Step 1: the final answer in lower case.
    text = ___
    lost = []
    for fact in found:
        # Step 2: this fact, in lower case,
        #         is not inside text?
        if ___:
            lost.append(fact)
    kept = len(found) - len(lost)
    share = kept / len(found)
    # Step 3: share rounded to 2 places.
    return {"kept": ___,
            "lost": sorted(lost)}
""",
        fills=['final.lower()', 'fact.lower() not in text', 'round(share, 2)'],
        concepts=[
            [
                'lower',
                '`s.lower()` gives a copy of the text in lower case, so "Order" and "order" match.',
                """"Hello World".lower()
# 'hello world'""",
            ],
            [
                'in and not in, on text',
                '`a in b` is True when the text `a` appears somewhere inside `b`. `not in` is the opposite.',
                """"cat" in "a black cat"     # True
"dog" not in "a black cat" # True""",
            ],
            [
                'len',
                '`len(items)` gives how many items a list holds. An empty list has length 0.',
                """len(['a', 'b', 'c'])   # 3
len([])                # 0""",
            ],
            [
                'round',
                '`round(x, 2)` keeps 2 decimal places.',
                'round(2 / 3, 2)   # 0.67',
            ],
            [
                'sorted',
                '`sorted(items)` gives a new list in order, A to Z for words.',
                "sorted(['pear', 'apple'])   # ['apple', 'pear']",
            ],
        ],
        byhand='In lower case, final is "order 4412: refund approved. it reaches you in 5 days." "order 4412" is inside it: kept. "refund approved" is inside it: kept. "card ends 0099" is not: lost. That is 2 kept out of 3, and 2 divided by 3 is about 0.667, which rounds to 0.67. Return {"kept": 0.67, "lost": ["card ends 0099"]}.',
        why='One look at each fact.',
        gotchas=[
            [
                'Forgetting lower case',
                '"Order 4412" is not inside "order 4412" for Python, because capitals count. Lower both sides before you compare.',
            ],
            [
                'Grading only the final answer',
                'An answer can read well and still drop a fact a helper found. The hand-off check shows where it fell out.',
            ],
        ],
    ),
)

lesson(MODULE, 'checker_loop',
    title='A checker with a round limit',
    learn=[
        'Ask an agent to grade its own work and it tends to say the work is fine. A **checker** is a second agent that starts fresh: it sees only the finished work and a written **checklist** of pass or fail rules, not the chat that made it.',
        'The loop is: check, fix what the checker found, check again. Without concrete rules, a checker runs one or two tests and declares victory, so write the checklist first and include checks that can really fail.',
        'Cap the rounds, for example at 3, and decide in advance what happens at the cap: return the best attempt with a warning, or hand it to a person. Where you can, the checker looks at real evidence, like running the query, rather than at the agent\'s own explanation.',
    ],
    example=example('A help-center answer, at most 3 rounds', """Checklist: answers the question;
cites a help article; no made-up
order numbers
round 1: 4 issues → fix
round 2: 2 issues → fix
round 3: 1 issue  → limit reached
→ send it to a person, with
  the 1 issue left"""),
    check=question(
        'Your checker passes almost every answer, even ones a person later marks wrong. What is the most likely fix?',
        [
            'Give the checker a written checklist of pass or fail rules',
            'Let the agent that wrote the answer check it once more',
            'Raise the round limit from 3 rounds up to 10 rounds',
        ],
        answer=0,
        why='Without concrete rules a checker declares victory early. More rounds change nothing if every round passes, and an agent grading its own work skews positive.',
    ),
    angle=angle(
        pattern='A loop with two ways out',
        text='The big idea: an agent that grades its own work says it is fine, so a fresh checker reviews it, and the fix loop needs a round cap decided in advance. Your code goes round by round, up to `max_rounds`. If a round finds 0 issues, it stops right away and reports clean, with the number of rounds it took. If the last allowed round still finds issues, it stops at the limit and reports how many that round found. Saying what happens at the cap is the part interviewers listen for.',
        say='"My checker starts fresh with a written checklist, and the fix loop has a round cap. At the cap I warn or hand it to a person."',
        classic=None,
    ),
    stack=stack('LangGraph: check, fix, and a round cap', """from langchain.agents import create_agent
from langgraph.graph import END

# The checker sees only the work and
# the checklist, not the chat so far.
# A different model is even better.
checker = create_agent(
    checker_llm, tools=[run_query],
    system_prompt=CHECKLIST)

# The check node adds 1 to "round".
def route(state):
    if state["issues"] == 0:
        return "done"
    if state["round"] >= 3:
        return "to_person"
    return "fix"

b.add_conditional_edges(
    "check", route, {
        "done": END,
        "to_person": "flag_for_review",
        "fix": "fix"})
b.add_edge("fix", "check")"""),
    exercise=exercise(
        title='Check, Fix, Stop',
        topic='agents',
        difficulty='easy',
        fn='checker_loop',
        prompt="""Your function gets two things:

- `issues_per_round`: how many problems the checker finds in each round, in order, like `[4, 2, 1, 0]`. The first number is round 1.
- `max_rounds`: the most rounds you allow, like `3`. It is at least 1, and the list has a number for every round you run.

Go round by round. If a round finds 0 issues, stop: the work is clean. If round `max_rounds` still finds issues, stop at the limit.

Return a dict:

- `"rounds"`: how many rounds you ran.
- `"ended"`: `"clean"` or `"limit"`.
- `"left"`: the issues found in the last round you ran (0 when clean).""",
        pattern='A loop with two exits: clean early, or stopped by the cap.',
        target='one look per round, at most max_rounds of them',
        realworld='A checker is the most reliable second agent to add. Teams that build one write the pass criteria first, give the checker a fresh context, and cap the fix loop.',
        starter="""def checker_loop(issues_per_round, max_rounds):
    # your code here
    pass
""",
        solution="""def checker_loop(issues_per_round, max_rounds):
    for i in range(max_rounds):
        if issues_per_round[i] == 0:
            return {"rounds": i + 1, "ended": "clean",
                    "left": 0}
    last = issues_per_round[max_rounds - 1]
    return {"rounds": max_rounds, "ended": "limit",
            "left": last}
""",
        cases=[
            case([4, 2, 1, 0], 3, expected={'rounds': 3, 'ended': 'limit', 'left': 1}, sample=True),
            case([3, 1, 0], 3, expected={'rounds': 3, 'ended': 'clean', 'left': 0}),
            case([0], 3, expected={'rounds': 1, 'ended': 'clean', 'left': 0}),
            case([2, 0, 5], 5, expected={'rounds': 2, 'ended': 'clean', 'left': 0}),
            case([5, 5, 5], 1, expected={'rounds': 1, 'ended': 'limit', 'left': 5}),
            case([3, 2, 2, 1], 4, expected={'rounds': 4, 'ended': 'limit', 'left': 1}),
        ],
        guided="""def checker_loop(issues_per_round, max_rounds):
    # Replace every ___ with real code, then run the tests.

    # i is 0 for round 1, 1 for round 2, and so on.
    for i in range(___):
        # Step 1: no issues? Clean. Rounds count from 1.
        if issues_per_round[i] == 0:
            return {"rounds": ___, "ended": "clean",
                    "left": 0}
    # Step 2: the cap. Report the last round's issues.
    last = issues_per_round[___]
    return {"rounds": max_rounds, "ended": "limit",
            "left": last}
""",
        fills=['max_rounds', 'i + 1', 'max_rounds - 1'],
        concepts=[
            [
                'range',
                '`range(n)` counts 0, 1, 2 and so on, stopping before n. So `range(3)` gives 0, 1 and 2.',
                """for i in range(3):
    print(i)   # 0, then 1, then 2""",
            ],
            [
                'List positions start at 0',
                'The first item is at position 0, so each item sits one place lower than its number: the 3rd item is at position 2.',
                """days = ['mon', 'tue', 'wed']
days[0]   # 'mon'
days[2]   # 'wed', the 3rd day""",
            ],
            [
                'Returning early',
                '`return` inside a loop ends the whole function right there, even mid-loop.',
                """def first_big(nums):
    for n in nums:
        if n > 10:
            return n
# first_big([3, 12, 40]) gives 12""",
            ],
        ],
        byhand='max_rounds is 3. Round 1 finds 4 issues, so fix and go on. Round 2 finds 2. Round 3 finds 1, and 3 is the limit, so stop there. The 0 in round 4 is never reached. Return {"rounds": 3, "ended": "limit", "left": 1}.',
        why='One look per round, and never more than max_rounds rounds.',
        gotchas=[
            [
                'Grading its own homework',
                'The agent that wrote the answer, asked "are you sure?", usually says yes. Use a separate checker with a fresh context and a checklist.',
            ],
            [
                'The checker that never lets go',
                'A loop that runs until the checker passes may never end. Cap it, and decide in advance what happens at the cap.',
            ],
        ],
    ),
)

lesson(MODULE, 'dollars_per_success',
    title='Dollars per success',
    learn=[
        'A team can pass a few more tasks and still be the worse choice. In one company\'s research system, one agent used about 4 times the tokens of a chat, and a team about 15 times.',
        'You already know **dollars per success** from Evaluating agents: the whole bill, failed runs included, divided by the runs that passed. It says what one passed task costs. It does not say whether the team\'s extra passes are worth their price.',
        'For that, work out what each **extra pass** costs: how many more dollars the team spends, divided by how many more tasks it passes. If one more passed task is worth less than that to you, keep one agent.',
        'Put this number next to the pass rate every time a team is compared with one agent. More spending often buys little extra accuracy, and sometimes less.',
    ],
    example=example('Same 10 tasks, two designs', """one agent: $0.50, passed 6 of 10
team:      $5.90, passed 8 of 10

$5.90 minus $0.50 → $5.40 more
8 minus 6         → 2 more passes
$5.40 divided by 2
→ $2.70 for each extra pass

Cost per success hides this: the
team's is only about $0.74."""),
    check=question(
        'One agent: $1 for 6 passes. A team: $7 for 8 passes. An extra passed task is worth $2 to you. What do you do?',
        [
            'Pick the team: it passes 2 more tasks than one agent',
            'Keep one agent: each extra pass costs $3, too much',
            'Pick the team: its cost per success is still under $1',
        ],
        answer=1,
        why='$6 more for 2 more passes is $3 each, and that is more than the $2 a pass is worth to you. The team\'s low cost per success hides this, because it counts the 6 passes one agent gets anyway.',
    ),
    angle=angle(
        pattern='Extra dollars over extra passes',
        text="The big idea: a team that passes a few more tasks may not be worth its price, so work out what each extra pass costs. Your code subtracts one agent's passes from the team's. If the team passes no more, it returns `None`, since there is nothing extra to pay for. Otherwise it subtracts the costs too and divides the extra dollars by the extra passes. In the example, $5.40 more for 2 more passes is $2.70 each. If one more pass is worth less than that to you, keep one agent.",
        say='"I price the team\'s extra passes: extra dollars divided by extra passes. If one more pass is worth less than that, I keep one agent."',
        classic=None,
    ),
    stack=stack('MLflow 3: tokens per design from traces', """import mlflow

# Tag the design inside the traced
# function your eval calls (its
# predict_fn). Outside a trace, the
# tag is lost.
@mlflow.trace
def run_team(question):
    mlflow.update_current_trace(
        tags={"design": "team"})
    ...  # call the team here

# After the eval, read that design's
# traces:
team_only = "tags.design = 'team'"
traces = mlflow.search_traces(
    filter_string=team_only,
    return_type="list")
for t in traces:
    usage = t.info.token_usage or {}
    print(usage.get("input_tokens"),
          usage.get("output_tokens"))
    # times your own price table
    # gives this trace's cost

# The gateway's system.ai_gateway.usage
# table logs every model call too: a
# second source to check against."""),
    exercise=exercise(
        title='Price of an Extra Pass',
        topic='agents',
        difficulty='easy',
        fn='extra_pass_cost',
        prompt="""Your function gets two things:

- `one`: how one agent did on your eval, like `{"cost": 0.5, "passed": 6}`. `cost` is the dollars for all its runs, failed ones too. `passed` is how many tasks it passed.
- `team`: how a team did on the same tasks, in the same shape, like `{"cost": 5.9, "passed": 8}`.

Work out what each extra pass costs: the team's cost minus one agent's cost, divided by the team's passes minus one agent's passes.

Return that, rounded to 2 decimal places. If the team passes no more tasks than one agent (the same number or fewer), return `None`.""",
        pattern='Subtract to see what the team adds, then divide one difference by the other.',
        target='two subtractions and one division, no loop',
        realworld='Agent leaderboards and research teams now report cost next to accuracy, because simple, cheap setups often match complex, expensive ones. You only see that when both numbers sit side by side.',
        starter="""def extra_pass_cost(one, team):
    # your code here
    pass
""",
        solution="""def extra_pass_cost(one, team):
    more_passes = team["passed"] - one["passed"]
    if more_passes <= 0:
        return None
    more_cost = team["cost"] - one["cost"]
    return round(more_cost / more_passes, 2)
""",
        cases=[
            case({'cost': 0.5, 'passed': 6}, {'cost': 5.9, 'passed': 8}, expected=2.7, sample=True),
            case({'cost': 1.2, 'passed': 5}, {'cost': 2.2, 'passed': 8}, expected=0.33),
            case({'cost': 0.2, 'passed': 4}, {'cost': 0.9, 'passed': 5}, expected=0.7),
            case({'cost': 0.8, 'passed': 0}, {'cost': 3.3, 'passed': 5}, expected=0.5),
            case({'cost': 0.3, 'passed': 7}, {'cost': 2.4, 'passed': 7}, expected=None),
            case({'cost': 0.5, 'passed': 9}, {'cost': 4.5, 'passed': 8}, expected=None),
        ],
        guided="""def extra_pass_cost(one, team):
    # Replace every ___ with real code, then run the tests.

    # Step 1: how many more tasks the team passes.
    more_passes = ___
    # No extra passes? Nothing to price.
    if more_passes <= 0:
        return None
    # Step 2: how many more dollars the team costs.
    more_cost = ___
    # Step 3: more_cost divided by more_passes,
    #         rounded to 2 places.
    return ___
""",
        fills=['team["passed"] - one["passed"]', 'team["cost"] - one["cost"]', 'round(more_cost / more_passes, 2)'],
        concepts=[
            [
                'Reading a dict',
                '`d["key"]` gives the value stored under that key.',
                """pet = {"name": "Rex", "age": 3}
pet["age"]   # 3""",
            ],
            [
                'Returning early',
                '`return` ends the function right there, so the lines after it never run.',
                """def grade(score):
    if score < 50:
        return 'fail'
    return 'pass'""",
            ],
            [
                'round',
                '`round(x, 2)` keeps 2 decimal places.',
                'round(2 / 3, 2)   # 0.67',
            ],
            [
                'None',
                "Python's way to say \"no value\". Use it when an answer doesn't exist.",
                """best = None
if best is None:
    print('nothing yet')""",
            ],
        ],
        byhand='The team passes 8 tasks and one agent passes 6, so the team passes 2 more. The team costs 5.9 and one agent costs 0.5, so the team costs 5.4 more. 5.4 divided by 2 is 2.7. Return 2.7.',
        why='Two subtractions and one division.',
        gotchas=[
            [
                'Looking only at the pass rate',
                'Two more passes sounds like a win. At $2.70 each, they may cost more than those answers are worth to you.',
            ],
            [
                'Dividing by all the team\'s passes',
                'The team\'s 8 passes include the 6 one agent gets anyway. Divide the extra cost by the 2 extra passes, not by 8.',
            ],
        ],
    ),
)

lesson(MODULE, 'tokens_by_agent',
    title='Which helper costs the most?',
    learn=[
        "A team's bill is the sum of every helper's model calls. If the trace shows only one total, you can't tell which helper to make cheaper.",
        'Give each helper its own **named span** (a labelled box in the trace), like "researcher" or "writer". Then the model calls inside each box add up to **tokens per agent**: the input tokens you sent plus the output tokens that came back.',
        'Start with the biggest one. It is often a helper that reads long documents. Try a smaller model for just that helper, and keep the change only if your eval still passes.',
    ],
    example=example('One team run, three model calls', """researcher  3000 in, 400 out
writer       900 in, 300 out
researcher  2500 in, 500 out

researcher: 3400 plus 3000, 6400
writer:     1200
→ look at the researcher first"""),
    check=question(
        'Your team\'s traces show 50,000 tokens a run, and every helper\'s span is called "agent". What should you do first to cut the cost?',
        [
            'Give each helper\'s span its own name, then see who uses most',
            'Move every helper to a smaller model, then rerun the eval',
            'Cut the team down to one agent, so it spends fewer tokens',
        ],
        answer=0,
        why='With every span called "agent" you are guessing. Named spans show which helper uses the tokens, so you change one helper and leave the rest alone.',
    ),
    angle=angle(
        pattern='Total per helper, then pick the biggest',
        text="The big idea: give each helper its own named span, so you can see which one costs the most and work on that first. Your code goes through the calls and adds each call's input plus output tokens to its agent's total. The totals live in a dict, a lookup table from agent name to tokens. Then it goes through the names in A to Z order and keeps the biggest total. It only swaps for a bigger total, never an equal one, so a tie goes to the name that comes first.",
        say='"I name every helper\'s span so I can see tokens per agent. I work on the biggest first, and try a smaller model there only if my eval still passes."',
        classic=None,
    ),
    stack=stack('MLflow 3: tokens per named helper', """import mlflow
from mlflow.entities import SpanType
from mlflow.tracing.constant import (
    SpanAttributeKey)

# 1. Name each helper's span. Under
# mlflow.langchain.autolog(), each
# LangGraph node's span is already
# named after the node.
def researcher(state):
    with mlflow.start_span(
            name="researcher",
            span_type=SpanType.AGENT):
        return research(state)

# 2. A model call's span holds its
# tokens, like {"input_tokens": 3000,
# "output_tokens": 400,
# "total_tokens": 3400}. Add each to
# the span it sits in.
USAGE = SpanAttributeKey.CHAT_USAGE
totals = {}
for t in mlflow.search_traces(
        return_type="list"):
    names = {}
    for s in t.data.spans:
        names[s.span_id] = s.name
    for s in t.data.spans:
        u = s.get_attribute(USAGE)
        if u:
            who = names.get(s.parent_id)
            used = (u["input_tokens"]
                    + u["output_tokens"])
            totals[who] = (
                totals.get(who, 0) + used)
print(totals)"""),
    exercise=exercise(
        title='Tokens per Helper',
        topic='agents',
        difficulty='easy',
        fn='tokens_by_agent',
        prompt="""`calls` is a list of the model calls in one team run. Each is a dict like `{"agent": "researcher", "input_tokens": 3000, "output_tokens": 400}`: the helper that made the call, the tokens it sent, and the tokens that came back. There is at least one call.

Add up each agent's tokens: input plus output, over all of its calls.

Return a list of two things:

- the name of the agent with the most tokens. If two agents tie, pick the name that comes first A to Z.
- a dict of each agent's total, like `{"researcher": 6400, "writer": 1200}`.""",
        pattern='Total by key in a dict, then keep the biggest.',
        target='one pass over the calls, then one over the names',
        realworld="Teams that run agents in production track cost per agent, not just per run. Anthropic's research team found that token use alone explained most of the differences in its results, so knowing which helper spends them matters.",
        starter="""def tokens_by_agent(calls):
    # your code here
    pass
""",
        solution="""def tokens_by_agent(calls):
    totals = {}
    for c in calls:
        used = c["input_tokens"] + c["output_tokens"]
        name = c["agent"]
        totals[name] = totals.get(name, 0) + used
    top = None
    for name in sorted(totals):
        if top is None or totals[name] > totals[top]:
            top = name
    return [top, totals]
""",
        cases=[
            case([
                {'agent': 'researcher', 'input_tokens': 3000, 'output_tokens': 400},
                {'agent': 'writer', 'input_tokens': 900, 'output_tokens': 300},
                {'agent': 'researcher', 'input_tokens': 2500, 'output_tokens': 500},
            ], expected=['researcher', {'researcher': 6400, 'writer': 1200}], sample=True),
            case([
                {'agent': 'solo', 'input_tokens': 100, 'output_tokens': 20},
            ], expected=['solo', {'solo': 120}]),
            case([
                {'agent': 'writer', 'input_tokens': 500, 'output_tokens': 100},
                {'agent': 'checker', 'input_tokens': 400, 'output_tokens': 200},
            ], expected=['checker', {'writer': 600, 'checker': 600}]),
            case([
                {'agent': 'a', 'input_tokens': 1000, 'output_tokens': 0},
                {'agent': 'b', 'input_tokens': 200, 'output_tokens': 900},
            ], expected=['b', {'a': 1000, 'b': 1100}]),
            case([
                {'agent': 'planner', 'input_tokens': 200, 'output_tokens': 50},
                {'agent': 'search', 'input_tokens': 1500, 'output_tokens': 100},
                {'agent': 'search', 'input_tokens': 1500, 'output_tokens': 100},
                {'agent': 'writer', 'input_tokens': 800, 'output_tokens': 900},
                {'agent': 'planner', 'input_tokens': 300, 'output_tokens': 50},
            ], expected=['search', {'planner': 600, 'search': 3200, 'writer': 1700}]),
        ],
        guided="""def tokens_by_agent(calls):
    # Replace every ___ with real code, then run the tests.

    totals = {}
    for c in calls:
        # Step 1: this call's tokens, input plus output.
        used = ___
        name = c["agent"]
        # Step 2: add them to this agent's total
        #         (it starts at 0).
        totals[name] = ___ + used
    # Names A to Z, so a tie keeps the first name.
    top = None
    for name in sorted(totals):
        # Step 3: first name, or more than top's total?
        if top is None or ___:
            top = name
    return [top, totals]
""",
        fills=['c["input_tokens"] + c["output_tokens"]', 'totals.get(name, 0)', 'totals[name] > totals[top]'],
        concepts=[
            [
                'Adding up with a dict',
                '`d.get(k, 0)` gives the total so far for `k`, or 0 if `k` is not there yet. Add the new amount to it.',
                """spent = {}
for item, cost in [('tea', 2), ('tea', 3)]:
    spent[item] = spent.get(item, 0) + cost
# spent is {'tea': 5}""",
            ],
            [
                'sorted on a dict',
                '`sorted(d)` gives the dict\'s keys as a list, A to Z.',
                """ages = {'bo': 25, 'ann': 30}
sorted(ages)   # ['ann', 'bo']""",
            ],
            [
                'None and is None',
                '`None` means "nothing yet". `x is None` checks for it.',
                """best = None
best is None   # True""",
            ],
            [
                'or',
                '`a or b` is True when either side is True. Python stops at the first True side, so the right side never runs when the left is True.',
                """n = 0
n == 0 or 10 / n > 1   # True, no error""",
            ],
            [
                'A list of two things',
                'A list can hold different kinds of things, like a word and a dict.',
                """pair = ['tea', {'tea': 5}]
pair[0]   # 'tea'""",
            ],
        ],
        byhand='researcher\'s first call: 3000 plus 400 is 3400. writer: 900 plus 300 is 1200. researcher\'s second call: 2500 plus 500 is 3000, so researcher is now 3400 plus 3000, which is 6400. Now the names A to Z: researcher comes first, so it is the top so far. writer has 1200, which is not more than 6400. Return ["researcher", {"researcher": 6400, "writer": 1200}].',
        why='Each call is added once, then each name is looked at once.',
        gotchas=[
            [
                'Counting only input tokens',
                'Output tokens usually cost several times more than input tokens. A helper that writes long reports can be the expensive one even if it reads little.',
            ],
            [
                'Every helper called "agent"',
                'If all the helper spans share one name, the trace adds them into one total, and you can\'t tell which helper to make cheaper.',
            ],
        ],
    ),
)

lesson(MODULE, 'team_experiment',
    title='One agent or a team: the experiment',
    learn=[
        'This lesson puts the module together. To find out whether a team beats one agent, run an **experiment**: both designs answer the same questions, and one agent is the **baseline**, the design you compare against.',
        'Agents give different answers on different tries, so run each question 3 to 5 times. As in Reliable every time (pass hat k), a question counts as **passed every time** only if every try passed.',
        'Write the **decision rule** before any run, so a lucky result can\'t move the goalposts. For example: the team wins only if it passes every time on at least 10 percent more of the questions, and one success costs at most 50 cents.',
        'Add a third design: the team without its checker. Comparing the two teams shows what the checker buys you. Taking one part out to see what changes is called an **ablation**.',
    ],
    example=example('20 questions, 3 tries each', """Rule, written first: the team must
gain at least 0.1 on "passed every
time", at $0.50 a success or less.

           every time   $ a success
one agent  12 of 20     $0.04
team       15 of 20     $0.35
team, no
checker    12 of 20     $0.30

team gain: 0.75 minus 0.6 is 0.15
→ the team wins, and the checker
  is what wins it"""),
    check=question(
        'You run one agent and a team once each on 20 questions. The team passes 14 and one agent passes 12. What is the main problem with picking the team?',
        [
            'Twenty questions is too few to compare any two designs',
            'One run each: agents vary, so 2 more passes may be luck',
            'The team should have been run on harder questions only',
        ],
        answer=1,
        why='The same agent can pass a question on one try and fail it on the next. Run each question 3 to 5 times and compare "passed every time", using a rule you wrote before the runs.',
    ),
    angle=angle(
        pattern='Score both designs, then apply the rule',
        text="The big idea: test a team against one agent with a decision rule written before any run, so a lucky result can't move the goalposts. A small helper scores each design. It uses Python's `all` to ask whether every try of a question passed, then divides that count by the number of questions. Your code subtracts the two scores and rounds to 2 places. It divides the team's cost by its passed tries. The team wins only if it has passed tries, reaches the gain in the rule, and stays within the cost limit.",
        say='"I write the decision rule before any run. The team must beat one agent on passed every time by a set margin and stay under a cost per success."',
        classic=None,
    ),
    stack=stack('MLflow 3: the experiment, k runs per design', """import mlflow
from mlflow.genai.scorers import scorer

# The same questions for every design
data = []
for q in QUESTIONS:
    data.append({"inputs": {"question": q}})

@scorer
def end_state(inputs, outputs):
    # look up the real result in code
    return refund_done(inputs["question"])

designs = {"one-agent": run_one,
           "team-v1": run_team,
           "team-no-checker": run_bare}

def tries(model_id):
    # each question's tries, like the
    # "runs" dict in the exercise
    runs = {}
    for t in mlflow.search_traces(
            model_id=model_id,
            return_type="list"):
        q = t.data.request
        a = t.search_assessments(
            name="end_state")[0]
        runs.setdefault(q, [])
        runs[q].append(a.value)
    return runs

for name in designs:
    m = mlflow.set_active_model(name=name)
    # no repeat option: loop 3 times
    for k in range(3):
        mlflow.genai.evaluate(
            data=data,
            predict_fn=designs[name],
            scorers=[end_state],
            model_id=m.model_id)
    print(name, tries(m.model_id))
# cost: each trace's t.info.token_usage
# times your price list"""),
    exercise=exercise(
        title='Who Wins the Experiment',
        topic='agents',
        difficulty='medium',
        fn='team_verdict',
        prompt="""Your function gets three things:

- `one`: how one agent did, like `{"runs": {"q1": [True, False, True]}, "cost": 0.5}`. `runs` lists each question's tries (True means passed). `cost` is the dollars for all the tries.
- `team`: how the team did, in the same shape, on the same questions.
- `rule`: your decision rule, like `{"min_gain": 0.1, "max_cost_per_success": 0.5}`.

For each design, "every time" is the share of its questions passed on every try.

Return `"team"` if both of these hold:

- the team's "every time" minus one agent's "every time", rounded to 2 places, is at least `min_gain`.
- the team's cost divided by its passed tries is at most `max_cost_per_success`. With no passed tries, the team can't win.

Otherwise return `"one agent"`.""",
        pattern='Score each design with a small helper, then apply a rule written in advance.',
        target='one pass over each design\'s tries',
        realworld='Agent researchers now compare every team with a one-agent baseline on the same tasks, with repeat runs and cost next to accuracy. Teams often look better on one run than they are.',
        starter="""def team_verdict(one, team, rule):
    # your code here
    pass
""",
        solution="""def team_verdict(one, team, rule):
    team_rate = every_time(team["runs"])
    one_rate = every_time(one["runs"])
    gain = round(team_rate - one_rate, 2)
    wins = 0
    for q in team["runs"]:
        wins += team["runs"][q].count(True)
    if wins == 0:
        return "one agent"
    per_success = team["cost"] / wins
    if gain < rule["min_gain"]:
        return "one agent"
    if per_success > rule["max_cost_per_success"]:
        return "one agent"
    return "team"


def every_time(runs):
    passed = 0
    for q in runs:
        if all(runs[q]):
            passed += 1
    return passed / len(runs)
""",
        cases=[
            case(
                {'runs': {'q1': [True, True, True], 'q2': [True, False, True]}, 'cost': 0.5},
                {'runs': {'q1': [True, True, True], 'q2': [True, True, True]}, 'cost': 1.8},
                {'min_gain': 0.1, 'max_cost_per_success': 0.5},
                expected='team', sample=True),
            case(
                {'runs': {'q1': [True, True, True], 'q2': [True, False, True]}, 'cost': 0.5},
                {'runs': {'q1': [True, True, True], 'q2': [False, True, True]}, 'cost': 1.0},
                {'min_gain': 0.1, 'max_cost_per_success': 0.5},
                expected='one agent'),
            case(
                {'runs': {'q1': [True, False, True], 'q2': [False, False, True]}, 'cost': 0.3},
                {'runs': {'q1': [True, True, True], 'q2': [True, True, True]}, 'cost': 6.0},
                {'min_gain': 0.1, 'max_cost_per_success': 0.5},
                expected='one agent'),
            case(
                {'runs': {'a': [True, True], 'b': [True, True], 'c': [True, False], 'd': [False, False], 'e': [False, True]}, 'cost': 1.0},
                {'runs': {'a': [True, True], 'b': [True, True], 'c': [True, True], 'd': [False, True], 'e': [True, False]}, 'cost': 2.0},
                {'min_gain': 0.2, 'max_cost_per_success': 0.5},
                expected='team'),
            case(
                {'runs': {'q1': [False, False], 'q2': [False, False]}, 'cost': 0.4},
                {'runs': {'q1': [False, False], 'q2': [False, False]}, 'cost': 1.0},
                {'min_gain': 0.0, 'max_cost_per_success': 1.0},
                expected='one agent'),
            case(
                {'runs': {'q1': [False, False], 'q2': [True, True]}, 'cost': 0.2},
                {'runs': {'q1': [True, True], 'q2': [True, True]}, 'cost': 2.0},
                {'min_gain': 0.5, 'max_cost_per_success': 0.5},
                expected='team'),
        ],
        guided="""def team_verdict(one, team, rule):
    # Replace every ___ with real code, then run the tests.

    # every_time is the helper below.
    team_rate = every_time(team["runs"])
    one_rate = every_time(one["runs"])
    gain = round(team_rate - one_rate, 2)
    # Step 1: count the team's passed tries.
    wins = 0
    for q in team["runs"]:
        wins += ___
    if wins == 0:
        return "one agent"
    per_success = team["cost"] / wins
    # Step 2: either check fails? One agent.
    if gain < rule["min_gain"]:
        return "one agent"
    if ___:
        return "one agent"
    return "team"


def every_time(runs):
    # Share of questions passed on every try.
    passed = 0
    for q in runs:
        # Step 3: did every try of q pass?
        if ___:
            passed += 1
    return passed / len(runs)
""",
        fills=['team["runs"][q].count(True)', 'per_success > rule["max_cost_per_success"]', 'all(runs[q])'],
        concepts=[
            [
                'A helper function',
                'You can write your own small function and call it from another, so the same work is written once. It can sit below the function that uses it.',
                """def double(n):
    return n * 2

double(4) + double(1)   # 10""",
            ],
            [
                'all',
                '`all(items)` is True only if every item in the list is True.',
                """all([True, True])    # True
all([True, False])   # False""",
            ],
            [
                'count',
                '`items.count(x)` says how many times `x` is in the list.',
                """['a', 'b', 'a'].count('a')   # 2""",
            ],
            [
                'round',
                '`round(x, 2)` keeps 2 decimal places. Rounding first makes 0.6 minus 0.4 compare as 0.2, not 0.19999999999999996.',
                """0.6 - 0.4             # 0.19999999999999996
round(0.6 - 0.4, 2)   # 0.2""",
            ],
            [
                'Returning early',
                '`return` ends the function right there, so the checks after it never run.',
                """def grade(score):
    if score < 50:
        return 'fail'
    return 'pass'""",
            ],
        ],
        byhand='One agent: q1 passed all 3 tries, q2 failed one, so 1 of its 2 questions passed every time: 0.5. The team: q1 and q2 both passed all 3 tries, so 2 of 2: 1.0. The gain is 1.0 minus 0.5, which is 0.5, and that is at least 0.1. The team passed 6 tries for $1.80, so one success cost 1.8 divided by 6, which is 0.3, and that is at most 0.5. Both checks hold. Return "team".',
        why='Each try is looked at once, then two checks.',
        gotchas=[
            [
                'Writing the rule after the runs',
                'Once you have seen the numbers, it is easy to pick a rule the team happens to meet. Write the rule down first.',
            ],
            [
                'One run per design',
                'Agents vary from try to try, so one run each can crown a lucky design. Run each question 3 to 5 times and compare "passed every time".',
            ],
        ],
    ),
)
