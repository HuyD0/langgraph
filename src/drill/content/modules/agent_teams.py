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
        pattern='Rules in order',
        text='A short chain of if checks where the first one that fits gives the answer, so the order of the checks is the logic. No loop needed.',
        say='"I start with the simplest design that works, and only move up from one call to a workflow, to one agent, to a team, when I can name the problem the next step fixes and my eval shows it."',
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
        pattern='Count by key',
        text='Count how many tasks write each resource in a dict, then keep the counts above one. Group Anagrams builds the same kind of dict, keyed by something you work out.',
        say='"I split helpers by what they need to know and give each shared thing one writer, so nothing gets overwritten and each change has a clear owner."',
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
        pattern='Fan out, then gather',
        text='Each worker is looked at on its own, then one step combines them: a running biggest value plus two lists, in a single pass.',
        say='"I fan read-only workers out with Send, gather their results through a reducer, and give each worker a timeout so one slow source can\'t hold up the whole answer."',
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
        pattern='A loop with a cap',
        text='A loop with two ways out: the work is clean, or the cap is reached. Saying what happens at the cap is what interviewers listen for.',
        say='"My checker gets a written checklist and a fresh context, and the fix loop stops after three rounds. At the cap it returns the best attempt with a warning, or hands it to a person."',
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
        pattern='Subtract, then divide',
        text='Subtract to find what the team adds in cost and in passes, then divide one by the other, with a guard for when it adds no passes. No loop needed.',
        say='"I price the team\'s extra passes: the extra dollars divided by the extra passes. If one more pass is worth less than that, I keep one agent."',
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
