"""Agents with LangGraph: The agent loop, memory, tools from Unity Catalog, and scoring the result."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('agents', 'Agents with LangGraph', 'The agent loop, memory, tools from Unity Catalog, and scoring the result.')

lesson(MODULE, 'run_agent',
    title='The agent loop',
    learn=[
        'An **agent** is a loop: the model picks a tool, your code runs it, the result goes back to the model, repeat until it gives a final answer.',
        'Two rules keep it safe: a **hard step limit** (LangGraph calls it the **recursion limit**), and turning tool errors into messages the model can read instead of crashes.',
        "Don't count on LangGraph's built-in limit. It is about 10,000 steps, so a stuck agent can spend money for a long time first. Always set your own small limit.",
    ],
    example=example('The shape of every agent', """for step in range(MAX_STEPS):
    action = model(history)
    if action.final:
        return action.text
    history.append(run_tool(action))"""),
    check=question(
        'Why must an agent loop have a maximum number of steps?',
        [
            'To keep each answer short and to the point',
            'The model API refuses runs that have no limit',
            'A confused model can loop forever, spending money',
        ],
        answer=2,
        why="Nothing else stops a model that keeps calling the same tool. LangGraph's own default limit is about 10,000 steps, so pass your own small recursion_limit.",
    ),
    angle=angle(
        pattern='A loop with a hard stop',
        text='The big idea: an agent is a loop, so it needs your own small step limit, and tool errors should become messages instead of crashes. A loop repeats the same work for each item. Your code loops over only the first `max_steps` steps of the plan, so it can never run longer. A final step adds the answer and returns at once. An unknown tool adds an error line and the loop keeps going. Any other tool adds its result. If the loop ends with no final answer, it adds `"stopped"`.',
        say='"My agent loop has a [[step limit|time limit|word limit::A fixed number of turns, so it can never go on forever.]], so it always stops. If a tool fails, I send the error back as a [[message|log entry|silent skip::The model should be able to read what went wrong and carry on.]], so one bad call doesn\'t end the run."',
        classic=None,
    ),
    stack=stack('LangGraph: a hard step limit', """graph = builder.compile()
# The default limit is 10,007 steps:
# far too many to protect your bill.
graph.invoke(
    {"messages": messages},
    config={"recursion_limit": 25})
# A model call, then its tool calls, is
# 2 steps (tools run together count as
# one), so 25 allows about 12 rounds.
# At the limit: GraphRecursionError."""),
    exercise=exercise(
        title='Run an Agent Loop',
        topic='agents',
        difficulty='medium',
        fn='run_agent',
        prompt="""The model's picks are already written down for you, as a plan.

Your function gets three things:

- `plan`: the steps, in order. Each is `[name, arg]`: a tool's name and what to give it, like `["search", "cats"]`.
- `tools`: what each tool gives back. `{"search": {"cats": "meow"}}` means searching for "cats" gives "meow".
- `max_steps`: the most steps you may run, like `5`.

Build a list called `log`. Run at most `max_steps` steps of the plan:

- `["final", text]`: add `"answer: " + text` and return `log`.
- a tool not in `tools`: add `"error: unknown tool " + name` and keep going.
- any other tool: add its result, `tools[name][arg]`.

If the plan runs out, or you reach `max_steps` steps, with no final answer, add `"stopped"` and return `log`.""",
        pattern='A loop with a hard stop. Errors become messages the agent can see, not crashes.',
        target='one pass over the plan, never more than `max_steps` steps',
        realworld="The core of LangGraph's ReAct agent (think, call a tool, look, repeat) and every tool-calling loop. Without `max_steps`, a confused model can loop forever and run up your bill.",
        starter="""def run_agent(plan, tools, max_steps):
    # your code here
    pass
""",
        solution="""def run_agent(plan, tools, max_steps):
    log = []
    for name, arg in plan[:max_steps]:
        if name == "final":
            log.append("answer: " + arg)
            return log
        if name not in tools:
            log.append("error: unknown tool " + name)
        else:
            log.append(tools[name][arg])
    log.append("stopped")
    return log
""",
        cases=[
            case([['search', 'paris'], ['final', "It's sunny"]], {'search': {'paris': 'sunny 22C'}}, 5, expected=['sunny 22C', "answer: It's sunny"], sample=True),
            case([['calc', '2+2'], ['final', '4']], {'search': {}}, 5, expected=['error: unknown tool calc', 'answer: 4']),
            case([['search', 'a'], ['search', 'a'], ['search', 'a'], ['final', 'x']], {'search': {'a': 'b'}}, 2, expected=['b', 'b', 'stopped']),
            case([], {}, 3, expected=['stopped']),
            case([['final', 'hi']], {}, 1, expected=['answer: hi']),
            case([['lookup', 'id7'], ['search', 'q']], {'lookup': {'id7': 'Ana'}, 'search': {'q': 'found'}}, 10, expected=['Ana', 'found', 'stopped']),
        ],
        guided="""def run_agent(plan, tools, max_steps):
    # Replace every ___ with real code, then run the tests.

    log = []
    # Step 1: take at most max_steps steps from the plan.
    for name, arg in plan[:___]:
        # Step 2: a final answer ends the run.
        if name == "final":
            log.append("answer: " + arg)
            return log
        # Step 3: a tool you don't have? Log an error.
        if ___:
            log.append("error: unknown tool " + name)
        else:
            # Step 4: run the tool: look up its result.
            log.append(___)

    # Step 5: the plan ran out or hit max_steps
    #         with no final answer.
    log.append("stopped")
    return log
""",
        fills=['max_steps', 'name not in tools', 'tools[name][arg]'],
        concepts=[
            [
                'Unpacking in a for loop',
                'When each item is a pair, the for line can name both parts.',
                """pets = [['cat', 'meow']]
for animal, sound in pets:
    print(animal, sound)""",
            ],
            [
                'Slicing to a limit',
                '`items[:3]` gives at most the first 3 items. If the list is shorter, you get all of it.',
                """[1, 2, 3, 4][:2]   # [1, 2]
[1][:2]            # [1]""",
            ],
            [
                '`in` with a dict',
                '`key in d` is True when the dict has that key. `not in` is the opposite.',
                """pets = {'cat': 1}
'dog' not in pets   # True""",
            ],
            [
                'A dict inside a dict',
                "`d['a']['b']` looks up 'a', then looks up 'b' in what it found.",
                """sounds = {'cat': {'happy': 'purr'}}
sounds['cat']['happy']   # 'purr'""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ana')   # ['Ana']""",
            ],
            [
                'Returning early',
                '`return` inside a loop ends the whole function right there, even mid-loop. Here `first_big([1, 5, 2])` gives 5.',
                """def first_big(nums):
    for n in nums:
        if n > 3:
            return n""",
            ],
        ],
        byhand='max_steps is 5 and the plan has 2 steps, so both can run. Step 1 is search, a tool you have. Look up "paris" in it and add "sunny 22C" to the log. Step 2 is final, so add "answer: It\'s sunny" and return. The log is ["sunny 22C", "answer: It\'s sunny"].',
        why='At most max_steps steps, each one a single dict lookup.',
        gotchas=[
            [
                'No step limit',
                "A model that keeps calling the same tool will loop and spend money the whole time. LangGraph's default recursion_limit is about 10,000 steps, so pass your own, like 25.",
            ],
            [
                'Crashing on bad tool calls',
                "Models sometimes call tools that don't exist or pass bad arguments. Send the error back as a message so the model can correct itself, instead of crashing.",
            ],
            [
                'Trusting tool output',
                'A web page or document a tool returns can contain instructions aimed at the model (prompt injection). Treat tool results as data, and require a human to approve risky actions like sending email or deleting files.',
            ],
        ],
    ),
)

lesson(MODULE, 'trim_history',
    title='Agent memory and context limits',
    learn=[
        'Models can only read a limited **context window**. Long chats and agent runs must drop or summarise old messages.',
        'Always keep the **system prompt** (the instructions), then keep the newest messages that fit.',
    ],
    example=example('Keep instructions, then fill from the newest end', """system, rest = messages[0], messages[1:]
# walk rest from newest to oldest, keep while within budget"""),
    check=question(
        'You keep only `messages[-10:]`, the last 10 messages. What can go wrong?',
        [
            'Nothing',
            'The system prompt falls off and the assistant forgets its instructions',
            'The reply gets slower',
        ],
        answer=1,
        why='The system prompt is the first message. Slicing from the end drops it once the chat is long enough.',
    ),
    angle=angle(
        pattern='Keep the newest that fit',
        text="The big idea: a model can only read so much, so keep the system prompt and then the newest messages that fit. Your code counts the system message's words first. Then it walks backwards from the newest message, adding each one while the total stays within `max_words`. At the first message that doesn't fit, it stops, so there are no gaps in the middle. It is like packing a bag with your newest things first. Finally it flips the kept messages back to oldest first and puts the system message in front.",
        say='"I always keep the [[system message|first message|longest message::The instructions at the very top never get dropped.]]. Then I add messages starting with the [[newest|oldest|shortest::Recent things matter most, so begin there and work backwards.]] one, and I stop at the first one that doesn\'t fit."',
        classic=None,
    ),
    stack=stack('LangChain: trim_messages', """from langchain_core.messages import trim_messages
trimmed = trim_messages(
    messages, max_tokens=2000, strategy="last",
    token_counter=llm, include_system=True, start_on="human",
)"""),
    exercise=exercise(
        title='Trim Chat Memory',
        topic='memory',
        difficulty='medium',
        fn='trim_history',
        prompt="""A chat model can only read so much, so old messages have to go.

Your function gets two things:

- `messages`: the chat, oldest first. Each message is `[role, text]`, like `["user", "hi there"]`. The first one is always the system message (the instructions), like `["system", "be nice"]`.
- `max_words`: the most words you may keep in total, like `7`.

Count a message's words with `len(text.split())`. Always keep the system message, even if it alone is over `max_words`. Its words count toward the total.

Then go from the newest message back, keeping each one while the total stays at most `max_words`. Stop at the first one that doesn't fit, so there are no gaps.

Return the system message, then the kept messages, oldest first.""",
        pattern='Pin what must stay, then fill the remaining budget from the newest end.',
        target='walk back through the messages once',
        realworld='Chat memory in every assistant. Dropping the system prompt by accident is one of the most common bugs, and the bot suddenly forgets its instructions.',
        starter="""def trim_history(messages, max_words):
    # your code here
    pass
""",
        solution="""def trim_history(messages, max_words):
    system = messages[0]
    used = len(system[1].split())
    kept = []
    for m in reversed(messages[1:]):
        words = len(m[1].split())
        if used + words > max_words:
            break
        kept.append(m)
        used += words
    return [system] + kept[::-1]
""",
        cases=[
            case([
                ['system', 'be nice'],
                ['user', 'hi there'],
                ['assistant', 'hello how are you'],
                ['user', 'good thanks'],
            ], 7, expected=[['system', 'be nice'], ['user', 'good thanks']], sample=True),
            case([
                ['system', 'be nice'],
                ['user', 'hi there'],
                ['assistant', 'hello how are you'],
                ['user', 'good thanks'],
            ], 100, expected=[
                ['system', 'be nice'],
                ['user', 'hi there'],
                ['assistant', 'hello how are you'],
                ['user', 'good thanks'],
            ]),
            case([['system', 'x y z']], 1, expected=[['system', 'x y z']]),
            case([['system', 'be brief'], ['user', 'a b c']], 2, expected=[['system', 'be brief']]),
            case([['system', 'x'], ['user', 'a b'], ['assistant', 'c d']], 5, expected=[['system', 'x'], ['user', 'a b'], ['assistant', 'c d']]),
            case([['system', 'hi'], ['user', 'one'], ['assistant', 'a b c d e f'], ['user', 'two']], 4, expected=[['system', 'hi'], ['user', 'two']]),
        ],
        guided="""def trim_history(messages, max_words):
    # Replace every ___ with real code, then run the tests.

    # Step 1: always keep the system message,
    #         and count its words.
    #         (system[1] is its text.)
    system = messages[0]
    used = len(system[1].split())

    # Step 2: skip the system message and go
    #         from the newest message back.
    kept = []
    for m in reversed(___):
        words = len(m[1].split())
        # Step 3: if used plus its words is over
        #         max_words, it doesn't fit: stop.
        if ___ > max_words:
            break
        kept.append(m)
        used += words

    # Step 4: kept is newest first. Flip it back.
    return [system] + ___
""",
        fills=['messages[1:]', 'used + words', 'kept[::-1]'],
        concepts=[
            [
                'Counting words',
                '`text.split()` cuts text into words at the spaces, and `len` counts them.',
                "len('hello how are you'.split())   # 4",
            ],
            [
                'Skipping the first item',
                '`items[1:]` is every item except the first.',
                "['a', 'b', 'c'][1:]   # ['b', 'c']",
            ],
            [
                'reversed',
                'Walks a list from the last item to the first, without changing the list.',
                """for m in reversed(['a', 'b', 'c']):
    print(m)   # c, b, a""",
            ],
            [
                'break',
                'Leaves the loop straight away. The code after the loop runs next.',
                """for n in [1, 5, 2]:
    if n > 3:
        break   # stops at 5""",
            ],
            [
                'Running totals',
                '`+=` adds to a variable, so it can keep a total as you loop.',
                """total = 0
for price in [2, 3]:
    total += price   # total is 5""",
            ],
            ['[::-1]', 'Gives a reversed copy of a list.', '[1, 2, 3][::-1]   # [3, 2, 1]'],
            [
                'Joining lists',
                '`+` puts two lists together into one new list.',
                "['a'] + ['b', 'c']   # ['a', 'b', 'c']",
            ],
        ],
        byhand='The budget is 7. Keep the system message "be nice": 2 words, so 2 are used. Now go from the newest. "good thanks" is 2 words: 2 + 2 = 4, within 7, so keep it. "hello how are you" is 4 words: 4 + 4 = 8, over 7, so stop. "hi there" is never checked, even though it would fit: no gaps. Return the system message, then "good thanks".',
        why='You walk back through the messages once, and stop early when the budget runs out.',
        gotchas=[
            [
                'Losing the system prompt',
                'messages[-10:] looks like a fine way to keep the last 10, until the system prompt falls off and the assistant forgets its instructions.',
            ],
            [
                'Breaking tool-call pairs',
                'In agent chats, a tool result must follow the message that called the tool. Cutting between them makes the API reject the request.',
            ],
            [
                "Words aren't tokens",
                "Real limits are in tokens. Count with the model's tokenizer, or leave a safety margin. Summarizing old messages is a common alternative to dropping them.",
            ],
        ],
    ),
)

lesson(MODULE, 'stale_claims',
    title="Memory that knows when it's stale",
    learn=[
        'An agent\'s **long-term memory** keeps facts between chats, like "refunds over $100 need a manager". When the policy changes, the memory doesn\'t, and the agent repeats the old rule with full confidence.',
        "So save each fact with its **source** (where it came from) and that source's **version**: a number that goes up each time the source changes. Before using the fact, compare the saved version with the source's version now, in plain code with no model call. If they differ, the fact is **stale**.",
        'Stale means "check again", not "wrong": don\'t delete it, and don\'t use it as if nothing happened. Re-read the source, then refresh the fact or save the new one; if you can\'t, say "I can\'t confirm that right now". A fact whose source has no version, like something the user said, gets an expiry date instead.',
        'This check only catches facts whose **source changed**. If a user says "I moved to York", no source gets a new version, so the old "lives in Leeds" fact still looks fresh. Spotting that needs a model, and it is hard: in one 2026 test of noticing out-of-date memories, the best model got only about 55 percent right overall.',
    ],
    example=example('Saved versions next to the sources now ("-" means the source has no version)', """fact    source  saved  now  result
refund  policy  3      4    stale
office  sites   7      7    fresh
pet     chat    1      -    unknown"""),
    check=question(
        "A remembered fact was saved at version 3 of its source, and the source is now at version 4. What should the agent do before using the fact?",
        [
            'Re-read the source, then refresh or replace it',
            'Delete it, since its source has changed',
            "Use it, since most changes don't affect it",
        ],
        answer=0,
        why='A new version only means the fact might be out of date. Many changes leave it true, so check the source rather than trusting or deleting the fact blindly.',
    ),
    angle=angle(
        pattern='Compare versions, sort into three lists',
        text="The big idea: save each fact with its source's version, and compare versions in plain code before using it. Your code goes through the memories in order. It looks up each source in `current`, a dict: a lookup table from source name to its version now. If the source isn't there, the fact goes in unknown, because there is nothing to compare. If the versions match, it is fresh. Otherwise it is stale, which means check again, not wrong. Unknown stays apart because not being able to tell is not the same as fresh.",
        say='"I save each fact with its source\'s [[version|date|author::A label that changes whenever the source changes.]] and compare before I use it. If they don\'t match, the fact is [[stale|wrong|deleted::Not false, just maybe out of date.]], so I re-read the source."',
        classic=None,
    ),
    stack=stack('LangGraph store and Databricks row versions', '''# LangGraph: save the fact with its
# evidence. user_id comes from login.
ns = ("facts", user_id)
store.put(ns, "refund", {
    "text": "Refunds over $100 "
            "need a manager",
    "source": "main.hr.policies/12",
    "version": 3})

# Databricks: read that ROW's version
# now (row tracking must be on). Not
# the table's version: that changes
# on every write to the table.
row = spark.sql("""
  SELECT _metadata.row_commit_version
         AS version
  FROM main.hr.policies
  WHERE id = 12""").first()

fact = store.get(ns, "refund").value
if row["version"] != fact["version"]:
    ...  # stale: re-read the row'''),
    exercise=exercise(
        title='Spot Stale Memories',
        topic='memory',
        difficulty='easy',
        fn='stale_claims',
        prompt="""Sort remembered facts by whether their source has changed since they were saved.

Your function gets two things:

- `memories`: the saved facts. Each is a dict like `{"id": "refund", "source": "policy", "version": 3}`: the fact's name, where it came from, and that source's version when it was saved.
- `current`: each source's version now, like `{"policy": 4}`.

For each memory, in order:

- its source is not in `current`: there is nothing to compare, so add its id to `"unknown"`.
- its version is the same as the source's version now: add its id to `"fresh"`.
- otherwise: add its id to `"stale"`.

Return `{"fresh": [...], "stale": [...], "unknown": [...]}`, each list in the same order as `memories`. A group with no ids is `[]`.""",
        pattern='Compare each item with a lookup table and sort it into one of three lists.',
        target='one pass over the memories, one lookup each',
        realworld="LangChain's OpenWiki memory saves each claim with the file and version it came from, and checks versions with plain code, no model call, before trusting a claim. On Databricks, the row's `_metadata.row_commit_version` is a good version to save.",
        starter="""def stale_claims(memories, current):
    # your code here
    pass
""",
        solution="""def stale_claims(memories, current):
    result = {"fresh": [],
              "stale": [],
              "unknown": []}
    for m in memories:
        source = m["source"]
        if source not in current:
            result["unknown"].append(m["id"])
        elif current[source] == m["version"]:
            result["fresh"].append(m["id"])
        else:
            result["stale"].append(m["id"])
    return result
""",
        cases=[
            case([
                {'id': 'refund', 'source': 'policy', 'version': 3},
                {'id': 'office', 'source': 'sites', 'version': 7},
                {'id': 'pet', 'source': 'chat', 'version': 1},
            ], {'policy': 4, 'sites': 7}, expected={'fresh': ['office'], 'stale': ['refund'], 'unknown': ['pet']}, sample=True),
            case([], {'policy': 4}, expected={'fresh': [], 'stale': [], 'unknown': []}),
            case([
                {'id': 'a', 'source': 'wiki', 'version': 2},
                {'id': 'b', 'source': 'faq', 'version': 5},
                {'id': 'c', 'source': 'wiki', 'version': 2},
            ], {'wiki': 2, 'faq': 5}, expected={'fresh': ['a', 'b', 'c'], 'stale': [], 'unknown': []}),
            case([
                {'id': 'old', 'source': 'doc', 'version': 1},
                {'id': 'new', 'source': 'doc', 'version': 2},
            ], {'doc': 2}, expected={'fresh': ['new'], 'stale': ['old'], 'unknown': []}),
            case([
                {'id': 'x', 'source': 'wiki', 'version': 1},
                {'id': 'y', 'source': 'gone', 'version': 4},
                {'id': 'z', 'source': 'wiki', 'version': 3},
                {'id': 'w', 'source': 'gone', 'version': 1},
            ], {'wiki': 3, 'other': 9}, expected={'fresh': ['z'], 'stale': ['x'], 'unknown': ['y', 'w']}),
            case([{'id': 'rule', 'source': 'policy', 'version': 6}], {'policy': 5}, expected={'fresh': [], 'stale': ['rule'], 'unknown': []}),
        ],
        guided="""def stale_claims(memories, current):
    # Replace every ___ with real code, then run the tests.

    # Step 1: three empty lists to fill.
    result = {"fresh": [],
              "stale": [],
              "unknown": []}
    for m in memories:
        source = m["source"]
        # Step 2: no version now for this source?
        if ___:
            result["unknown"].append(m["id"])
        # Step 3: is the version now the same as
        #         the saved one, m["version"]?
        elif ___:
            result["fresh"].append(m["id"])
        # Step 4: the source changed: stale.
        else:
            result["stale"].append(m["id"])
    return result
""",
        fills=['source not in current', 'current[source] == m["version"]'],
        concepts=[
            [
                'Reading a dict',
                '`d["key"]` gives the value saved under that key.',
                """pet = {'name': 'Rex', 'age': 3}
pet['name']   # 'Rex'""",
            ],
            [
                '`in` with a dict',
                '`key in d` is True when the dict has that key. `not in` is the opposite.',
                """ages = {'Ana': 30}
'Bo' not in ages   # True""",
            ],
            [
                'if, elif, else',
                'Python tries each test in order and runs only the first one that is True. `else` runs when none were.',
                """if n > 10:
    size = 'big'
elif n > 3:
    size = 'medium'
else:
    size = 'small'""",
            ],
            [
                'Same or not',
                '`a == b` is True when a and b are the same. `a != b` is True when they differ.',
                """3 == 3   # True
3 != 4   # True""",
            ],
            [
                'A dict of lists',
                'Each key holds its own list, and `.append` adds to the end of one of them.',
                """groups = {'big': [], 'small': []}
groups['big'].append(9)
# {'big': [9], 'small': []}""",
            ],
        ],
        byhand='current has policy at 4 and sites at 7. refund came from policy at version 3. policy is now at 4, not 3, so refund is stale. office came from sites at version 7, and sites is still at 7, so office is fresh. pet came from chat, and chat is not in current, so there is nothing to compare: unknown. Return {"fresh": ["office"], "stale": ["refund"], "unknown": ["pet"]}.',
        why='One pass over the memories, with one dict lookup for each.',
        gotchas=[
            [
                "Saving the whole table's version",
                "A Delta table gets a new version on every write, even maintenance like OPTIMIZE, so every fact looks stale and you re-check everything. Save the row's `_metadata.row_commit_version`, or a version column you control.",
            ],
            [
                'Deleting stale facts',
                'Many source changes leave a fact true. Re-read the source, then refresh the fact or save the new one. If you can\'t, say "I can\'t confirm that" rather than repeating the old fact.',
            ],
        ],
    ),
)

lesson(MODULE, 'fact_history',
    title='When a new fact replaces an old one',
    learn=[
        'When a new fact replaces an old one, **overwriting** the old one loses the history. You can no longer answer "where was the office in March?", or see what the agent believed when it made an old decision. In LangGraph, `store.put` on a key that already exists replaces the whole value, with no warning.',
        "Instead, **close** the old fact. Give each fact a `from` day (when it became true) and a `to` day (`None` while it is still true). When a new fact arrives, set the old fact's `to` to the new fact's `from`, and save the new fact next to it under its own key. Data teams know this pattern as **SCD Type 2** (slowly changing dimension, type 2).",
        'Now "what\'s true now?" means the facts whose `to` is `None`. "What was true on day 30?" means the fact that started on or before day 30 and hadn\'t ended yet. Some systems also save a second date, the day they **learned** the fact, because it can differ from the day it became true. Keeping both dates is called **bitemporal** data.',
        'One exception is **personal data**. When a person asks to be forgotten, deleting wins over keeping history (see the "Personal data" lesson in Security).',
    ],
    example=example('Two facts about the office', """value  from  to
Leeds  1     40
York   40    None

day 10  ->  Leeds
day 40  ->  York  (Leeds ended)
day 99  ->  York"""),
    check=question(
        'The agent runs `store.put(ns, "office", {"city": "York"})` on the key that held "Leeds". What is lost?',
        [
            'Nothing, as the store keeps each old value too',
            'Only the time the Leeds fact was first saved',
            'Any way to answer where the office used to be',
        ],
        answer=2,
        why='put on an existing key replaces the whole value, with no error. With one key per fact and the old fact closed, "where was the office in March?" still has an answer.',
    ),
    angle=angle(
        pattern='Find the fact that covers the day',
        text='The big idea: never overwrite a fact. Close it with a `to` day, so you can still ask what was true then. Your code skips any fact with a different subject, or that started after the day asked about. A fact still counts if its `to` is `None`, meaning still true, or if the day is before `to`. On the `to` day itself the fact has already ended, like a hotel stay where you are gone on checkout day. The code returns the first match, or `None` if no fact covers that day.',
        say='"I never [[overwrite|delete|copy::Replacing the old fact would lose its history.]] a fact. I give the old one an [[end day|start day|owner::It marks when the fact stopped being true.]] and save the new one beside it, so I can still tell what was true on any day."',
        classic=None,
    ),
    stack=stack('LangGraph store: one key per version', '''# put on an existing key REPLACES the
# value. So use one key per version.
ns = ("facts", user_id)
old = store.get(ns, "office@1").value
old["to"] = 40          # close it
store.put(ns, "office@1", old)
store.put(ns, "office@2", {
    "subject": "office",
    "value": "York",
    "from": 40, "to": None})

# What's true now: "to" is still None.
now = store.search(ns, filter={
    "subject": "office", "to": None})

# Databricks AUTO CDC keeps the same
# kind of history for a table (SCD
# Type 2): each row gets __START_AT
# and __END_AT, and __END_AT is empty
# on the current row:
#   SELECT value FROM office_history
#   WHERE __END_AT IS NULL'''),
    exercise=exercise(
        title='Look Up a Fact on a Day',
        topic='memory',
        difficulty='easy',
        fn='fact_at',
        prompt="""Find the fact that was true on a given day.

Your function gets three things:

- `facts`: every saved fact, in any order. Each is a dict like `{"subject": "office", "value": "Leeds", "from": 1, "to": 40}`. `from` is the day it became true. `to` is the day it stopped, or `None` while it is still true.
- `subject`: what to ask about, like `"office"`.
- `day`: the day to ask about, like `30`.

A fact was true on `day` when all three hold:

- its `subject` matches.
- its `from` is `day` or earlier.
- its `to` is `None`, or `day` is before `to`. So on day 40, a fact with `to` 40 has already ended.

Return that fact's `value`, or `None` if no fact was true that day.""",
        pattern='Find the one range that holds the day: start on or before it, end after it.',
        target='one pass over the facts, stopping at the first match',
        realworld="Graphiti, Zep's memory library, closes an old fact by setting its end to the new fact's start, and deletes nothing. Databricks AUTO CDC builds the same history for tables (SCD Type 2), with `__START_AT` and `__END_AT` columns.",
        starter="""def fact_at(facts, subject, day):
    # your code here
    pass
""",
        solution="""def fact_at(facts, subject, day):
    for f in facts:
        if f["subject"] != subject:
            continue
        if f["from"] > day:
            continue
        if f["to"] is None or day < f["to"]:
            return f["value"]
    return None
""",
        cases=[
            case([
                {'subject': 'office', 'value': 'Leeds', 'from': 1, 'to': 40},
                {'subject': 'manager', 'value': 'Ana', 'from': 5, 'to': None},
                {'subject': 'office', 'value': 'York', 'from': 40, 'to': None},
            ], 'office', 30, expected='Leeds', sample=True),
            case([
                {'subject': 'office', 'value': 'Leeds', 'from': 1, 'to': 40},
                {'subject': 'manager', 'value': 'Ana', 'from': 5, 'to': None},
                {'subject': 'office', 'value': 'York', 'from': 40, 'to': None},
            ], 'office', 40, expected='York'),
            case([
                {'subject': 'office', 'value': 'Leeds', 'from': 1, 'to': 40},
                {'subject': 'office', 'value': 'York', 'from': 40, 'to': None},
            ], 'office', 0, expected=None),
            case([
                {'subject': 'office', 'value': 'Leeds', 'from': 1, 'to': 40},
                {'subject': 'office', 'value': 'York', 'from': 40, 'to': None},
            ], 'parking', 30, expected=None),
            case([
                {'subject': 'plan', 'value': 'Pro', 'from': 20, 'to': 50},
                {'subject': 'plan', 'value': 'Free', 'from': 1, 'to': 20},
                {'subject': 'plan', 'value': 'Team', 'from': 50, 'to': None},
            ], 'plan', 20, expected='Pro'),
            case([
                {'subject': 'manager', 'value': 'Ana', 'from': 1, 'to': 10},
                {'subject': 'office', 'value': 'York', 'from': 1, 'to': None},
            ], 'manager', 15, expected=None),
        ],
        guided="""def fact_at(facts, subject, day):
    # Replace every ___ with real code, then run the tests.

    for f in facts:
        # Step 1: skip facts about something else.
        if f["subject"] != subject:
            continue
        # Step 2: skip facts that start after day.
        if ___:
            continue
        # Step 3: still true (to is None), or
        #         day is before f["to"]?
        if ___:
            return f["value"]

    # Step 4: nothing was true that day.
    return None
""",
        fills=['f["from"] > day', 'f["to"] is None or day < f["to"]'],
        concepts=[
            [
                'continue',
                'Skips the rest of this round of the loop and goes on to the next item.',
                """for n in [1, -2, 3]:
    if n < 0:
        continue
    print(n)   # 1, then 3""",
            ],
            [
                '`is None`',
                '`None` means "no value". `x is None` is True when x holds nothing.',
                """end = None
end is None   # True""",
            ],
            [
                '`or`',
                'True when either side is True. Python stops at the first True side, so here `n > 3` never runs when n is None.',
                """n = None
n is None or n > 3   # True""",
            ],
            [
                'Comparing numbers',
                '`a < b` is True when a is smaller, and `a > b` when a is bigger. `a != b` is True when they are not the same.',
                """30 < 40       # True
40 < 40       # False
'a' != 'b'    # True""",
            ],
            [
                'Returning early',
                '`return` inside a loop ends the whole function right there. If the loop finishes, the code after it runs.',
                """def first_big(nums):
    for n in nums:
        if n > 3:
            return n
    return None""",
            ],
        ],
        byhand='Look for "office" on day 30. The first fact is about the office. Its from is 1, which is not after day 30, so it had started. Its to is 40, and 30 is before 40, so it hadn\'t ended. Return "Leeds". The loop stops there, so the other facts are never checked.',
        why='One pass over the facts, and it stops at the first one that was true that day.',
        gotchas=[
            [
                'Overwriting the same key',
                '`store.put(ns, "office", new_value)` replaces the old value with no error, and InMemoryStore even resets its created_at. Use one key per version, like office@1 and office@2, and close the old one.',
            ],
            [
                'Keeping personal data forever',
                "Closing old facts is right for business facts. When a person asks to be erased, delete their memories for real, including copies in Delta table history, search indexes and traces.",
            ],
        ],
    ),
)

lesson(MODULE, 'tool_schema',
    title='Tools from Unity Catalog',
    learn=[
        "An agent's tools are described to the model as a **name**, a **description** and **parameters** (the inputs the tool takes). The model picks a tool by reading those descriptions, so they are part of your prompt. Together they are called the **tool schema**, written in a format called JSON Schema.",
        'On Databricks, a common pattern is to write tools as **Unity Catalog functions**: governed, permissioned and reusable. `UCFunctionToolkit` turns them into LangChain tools, using the function and parameter comments as descriptions.',
    ],
    example=example('A tool as the model sees it', """{"type": "function", "function": {
  "name": "lookup_order",
  "description": "Look up an order's status and delivery date",
  "parameters": {"type": "object",
    "properties": {"order_id": {"type": "string", "description": "The order number, like A-1042"}},
    "required": ["order_id"]}}}"""),
    check=question(
        "Your agent keeps calling `get_data` when it should call `lookup_order`. What's the cheapest fix to try first?",
        ['A bigger model', 'Clearer function and parameter comments', 'More tools'],
        answer=1,
        why='The model chooses from the descriptions. Vague comments cause wrong picks.',
    ),
    angle=angle(
        pattern='Fill the inside, then wrap it',
        text='The big idea: the model picks a tool by reading its name, description and parameters, so this description is part of your prompt. Your code goes through each parameter once. It turns the database type into the model\'s word using `TYPES`, a dict: a lookup table, like a small translation dictionary. Each parameter goes into `properties` with its type and comment, and its name goes into `required`, in order. Then the code wraps everything from the inside out, like nesting boxes: `parameters`, then the `"function"` dict, then the outer dict.',
        say='"The model picks a tool by reading its [[description|code|logs::It sees words about the tool, not how it\'s built.]], so that\'s part of my prompt. I list each parameter with its type and comment, mark it [[required|optional|hidden::The model must always fill these in.]], and wrap it in the shape models expect."',
        classic=None,
    ),
    stack=stack('databricks_langchain: Unity Catalog functions as tools', """from databricks_langchain import ChatDatabricks, UCFunctionToolkit
tools = UCFunctionToolkit(function_names=["main.support.lookup_order"]).tools
llm = ChatDatabricks(endpoint=ENDPOINT).bind_tools(tools)"""),
    exercise=exercise(
        title='Describe a Tool for the Model',
        topic='agents',
        difficulty='medium',
        fn='tool_schema',
        prompt="""Turn a Unity Catalog function into the tool description that chat models read.

Your function gets three things:

- `name`: the tool's name, like `"refund"`.
- `description`: what the tool does, like `"Refund an order"`.
- `params`: its parameters. Each is `[pname, sql_type, comment]`, like `["amount", "DOUBLE", "Dollars to refund"]`. `pname` is the parameter's name, and `sql_type` its type in the database.

For each parameter, make `{"type": json_type, "description": comment}`. `json_type` is the model's word for the type. Look it up in the `TYPES` table at the top: `TYPES["DOUBLE"]` is `"number"`. Put these in a dict called `properties`, with each `pname` as the key. List every `pname` in `required`, in order.

Then wrap it all up, from the inside out, like the tool in the Learn example: put `"type": "object"`, `properties` and `required` in a dict called `parameters`. Put `name`, `description` and `parameters` in a dict under the key `"function"`. Return a dict with `"type": "function"` and that `"function"` dict.""",
        pattern='A lookup table for the types, then build the result one level at a time, from the inside out.',
        target='one pass over the parameters',
        realworld="`UCFunctionToolkit` in `databricks_langchain` builds exactly this from a function in Unity Catalog, using the function's and parameters' comments as the descriptions. Vague comments make the model call the wrong tool or pass bad arguments, so the comment is part of your prompt.",
        starter="""TYPES = {
    "STRING": "string",
    "INT": "integer",
    "DOUBLE": "number",
    "BOOLEAN": "boolean",
}

def tool_schema(name, description, params):
    # your code here
    pass
""",
        solution="""TYPES = {
    "STRING": "string",
    "INT": "integer",
    "DOUBLE": "number",
    "BOOLEAN": "boolean",
}

def tool_schema(name, description, params):
    properties = {}
    required = []
    for pname, sql_type, comment in params:
        properties[pname] = {"type": TYPES[sql_type], "description": comment}
        required.append(pname)
    parameters = {
        "type": "object",
        "properties": properties,
        "required": required,
    }
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }
""",
        cases=[
            case('refund', 'Refund an order', [
                ['order_id', 'STRING', 'Order number'],
                ['amount', 'DOUBLE', 'Dollars to refund'],
            ], expected={
                'type': 'function',
                'function': {
                    'name': 'refund',
                    'description': 'Refund an order',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'order_id': {'type': 'string', 'description': 'Order number'},
                            'amount': {'type': 'number', 'description': 'Dollars to refund'},
                        },
                        'required': ['order_id', 'amount'],
                    },
                },
            }, sample=True),
            case('ping', 'Check the service is up', [], expected={
                'type': 'function',
                'function': {
                    'name': 'ping',
                    'description': 'Check the service is up',
                    'parameters': {'type': 'object', 'properties': {}, 'required': []},
                },
            }),
            case('lookup_order', "Look up an order's status", [['order_id', 'STRING', 'The order number, like A-1042']], expected={
                'type': 'function',
                'function': {
                    'name': 'lookup_order',
                    'description': "Look up an order's status",
                    'parameters': {
                        'type': 'object',
                        'properties': {'order_id': {'type': 'string', 'description': 'The order number, like A-1042'}},
                        'required': ['order_id'],
                    },
                },
            }),
            case('cancel_order', 'Cancel an order', [
                ['order_id', 'STRING', 'Order number'],
                ['reason_code', 'INT', '1 damaged, 2 late'],
                ['notify', 'BOOLEAN', 'Email the customer'],
            ], expected={
                'type': 'function',
                'function': {
                    'name': 'cancel_order',
                    'description': 'Cancel an order',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'order_id': {'type': 'string', 'description': 'Order number'},
                            'reason_code': {'type': 'integer', 'description': '1 damaged, 2 late'},
                            'notify': {'type': 'boolean', 'description': 'Email the customer'},
                        },
                        'required': ['order_id', 'reason_code', 'notify'],
                    },
                },
            }),
        ],
        guided="""TYPES = {
    "STRING": "string",
    "INT": "integer",
    "DOUBLE": "number",
    "BOOLEAN": "boolean",
}

def tool_schema(name, description, params):
    # Replace every ___ with real code, then run the tests.

    properties = {}
    required = []
    for pname, sql_type, comment in params:
        # Step 1: describe this parameter. Look up
        #         sql_type in TYPES to get json_type.
        properties[pname] = {"type": ___, "description": comment}
        # Step 2: add pname to the required list.
        ___

    # Step 3: wrap it all in the shape models expect.
    parameters = {
        "type": "object",
        "properties": properties,
        "required": required,
    }
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }
""",
        fills=['TYPES[sql_type]', 'required.append(pname)'],
        concepts=[
            [
                'A lookup table',
                'A dict that turns one name into another.',
                """colors = {'red': '#f00'}
colors['red']   # '#f00'""",
            ],
            [
                'Unpacking three values',
                'When each item is a list of three, the for line can name all three.',
                """rows = [['Ana', 30, 'Rome']]
for name, age, city in rows:
    print(name, city)""",
            ],
            [
                'Adding a key to a dict',
                '`d[key] = value` adds the key, or replaces its value if it is already there.',
                """ages = {}
ages['Ana'] = 30   # {'Ana': 30}""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ana')   # ['Ana']""",
            ],
        ],
        byhand='Two parameters. order_id is STRING, and `TYPES["STRING"]` is "string", so its property is `{"type": "string", "description": "Order number"}`. amount is DOUBLE, which becomes "number": `{"type": "number", "description": "Dollars to refund"}`. required is `["order_id", "amount"]`. Put "type": "object", properties and required inside "parameters". Put the name, description and parameters inside "function". Add "type": "function" at the top, and return it.',
        why='One step per parameter.',
        gotchas=[
            [
                'The comment is the prompt',
                '"id" tells the model nothing. "The order number, like A-1042" tells it the format, and fewer calls fail.',
            ],
            [
                'Give the agent least privilege',
                "A Unity Catalog function runs with the permissions it's granted. Grant the agent EXECUTE on the few functions it needs, not on a whole schema (the Unity Catalog folder that holds many functions).",
            ],
        ],
    ),
)

lesson(MODULE, 'tool_pairs',
    title='Tool calls and results',
    learn=[
        'When a model calls tools, each call gets an **id**, and each result must reference it. Model APIs reject a conversation where a call has no matching result. A call left without a result is often called a **dangling tool call**.',
        'This breaks most often after trimming history, or when a tool crashes and no result is sent. Send the error as the result instead.',
    ],
    example=example('A call and its result', """{'role': 'assistant', 'tool_calls': [{'id': 'call_1', 'name': 'search'}]}
{'role': 'tool', 'tool_call_id': 'call_1', 'content': '...'}"""),
    check=question(
        'A tool crashed and you skipped sending its result. What happens on the next model call?',
        [
            'The model ignores it',
            'The API rejects the request because a tool call has no result',
            'The tool is called again automatically',
        ],
        answer=1,
        why='Every call needs an answer. Send the error message as the tool result.',
    ),
    angle=angle(
        pattern='A waiting list of open calls',
        text="The big idea: every tool call needs a matching result, or the model's service rejects the whole chat. Your code keeps a list called `waiting`. Each time it sees a tool call, it adds that call's id to the list. Each time it sees a tool result, it removes the id that result answers. It is like a coat check, where each ticket waits until its coat is collected. Whatever ids are still waiting at the end never got a result, and they are already in the order the calls were made.",
        say='"Every tool call needs a matching [[result|retry|summary::The answer that comes back after the tool runs.]]. I keep a list of open call ids and cross one off each time an answer arrives. Anything left over means the API would [[reject|accept|ignore::The service refuses a chat with unanswered calls.]] the chat."',
        classic='valid_parentheses',
    ),
    stack=stack('LangGraph: ToolNode answers every tool call', """from langgraph.prebuilt import ToolNode
builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
# handle_tool_errors=True: a crash comes back as the tool's result, so every call gets one.
# By default, a crashing tool stops the run instead."""),
    exercise=exercise(
        title='Match Tool Calls to Results',
        topic='agents',
        difficulty='medium',
        fn='tool_pairs',
        prompt="""When a model calls a tool, the call gets an id, and a tool result must answer that id. A call with no result makes the model's service reject the chat.

`messages` is the chat, oldest first: a list of dicts. Two kinds matter:

- An assistant message may have `"tool_calls"`, a list like `[{"id": "call_1", "name": "search"}]`.
- A tool result has `"role": "tool"` and the id it answers, like `{"role": "tool", "tool_call_id": "call_1"}`.

Other messages have neither. Every result answers a call made earlier.

Return the ids of the calls that never got a result, in the order the calls were made.""",
        pattern='Matching pairs: a call opens, its result closes it. Whatever is still open at the end has no result.',
        target='one pass over the messages',
        realworld="Model services reject a conversation where a tool call has no result. This usually happens after trimming chat history cuts a call away from its result, and it shows up in production as a confusing 'bad request' error.",
        starter="""def tool_pairs(messages):
    # your code here
    pass
""",
        solution="""def tool_pairs(messages):
    waiting = []
    for m in messages:
        for call in m.get("tool_calls", []):
            waiting.append(call["id"])
        if m.get("role") == "tool":
            waiting.remove(m["tool_call_id"])
    return waiting
""",
        cases=[
            case([
                {'role': 'user', 'content': 'Paris and Rome?'},
                {
                    'role': 'assistant',
                    'tool_calls': [{'id': 'call_1', 'name': 'weather'}, {'id': 'call_2', 'name': 'weather'}],
                },
                {'role': 'tool', 'tool_call_id': 'call_1', 'content': '22C'},
            ], expected=['call_2'], sample=True),
            case([], expected=[]),
            case([
                {'role': 'assistant', 'content': 'hello'},
                {'role': 'assistant', 'tool_calls': [{'id': 'c1', 'name': 'x'}, {'id': 'c2', 'name': 'y'}]},
                {'role': 'tool', 'tool_call_id': 'c2'},
                {'role': 'tool', 'tool_call_id': 'c1'},
            ], expected=[]),
            case([
                {'role': 'assistant', 'tool_calls': [{'id': 'a', 'name': 'search'}]},
                {'role': 'tool', 'tool_call_id': 'a'},
                {'role': 'assistant', 'tool_calls': [{'id': 'b', 'name': 'search'}]},
            ], expected=['b']),
            case([
                {'role': 'user', 'content': 'hi'},
                {'role': 'assistant', 'tool_calls': [{'id': 'c1', 'name': 'x'}, {'id': 'c2', 'name': 'y'}]},
            ], expected=['c1', 'c2']),
        ],
        guided="""def tool_pairs(messages):
    # Replace every ___ with real code, then run the tests.

    waiting = []   # ids of calls with no result yet
    for m in messages:
        # Step 1: add each call's id to waiting.
        #         (No tool_calls? m.get gives [].)
        for call in m.get("tool_calls", []):
            ___

        # Step 2: a tool result? Take its
        #         tool_call_id out of waiting.
        if m.get("role") == "tool":
            ___

    # Step 3: whatever still waits never got a result.
    return waiting
""",
        fills=['waiting.append(call["id"])', 'waiting.remove(m["tool_call_id"])'],
        concepts=[
            [
                'dict.get with a default',
                "`d.get(key, default)` gives the default when the key isn't there, instead of crashing. With no default, it gives None.",
                """pet = {'name': 'Rex'}
pet.get('toys', [])   # []""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ana')   # ['Ana']""",
            ],
            [
                'list.remove',
                'Takes the first matching item out of a list.',
                """fruit = ['apple', 'pear']
fruit.remove('apple')
# fruit is now ['pear']""",
            ],
        ],
        byhand='The user message has no calls and is not a result. The assistant message calls call_1 and call_2, so both are waiting. The tool result answers call_1, so call_1 stops waiting. Nothing answers call_2. Return ["call_2"].',
        why='One walk through the messages. Removing from a list means searching it, which is fine for a handful of waiting calls.',
        gotchas=[
            [
                'Trim in pairs',
                'When you cut old messages, never separate a tool call from its result. Treat them as one unit.',
            ],
            [
                'Parallel calls',
                'Models can request several tools at once. Every one needs a result before the next model call, even if a tool failed: send the error as the result.',
            ],
        ],
    ),
)

lesson(MODULE, 'agent_scorecard',
    title='Evaluating agents',
    learn=[
        'Agents need more than one number. Track **success rate** (did it finish the task?), **steps** (how much work it took) and **cost per success**, which spreads the cost of failed runs over the successful ones.',
        'Define success with a clear rule, or an **LLM judge** (a model that grades each run) with a rubric (written grading rules) that you check against a few human labels.',
    ],
    example=example('Three runs, scored by hand', """run 1: success, 4 steps, $0.30
run 2: success, 6 steps, $0.40
run 3: failed,  9 steps, $0.20

success rate:     2 successes out of 3 runs   -> 0.67
average steps:    (4 + 6) / 2 successes       -> 5
cost per success: $0.90 total / 2 successes   -> $0.45"""),
    check=question(
        'Agent A: 90% success, $0.40 per success. Agent B: 80% success, $0.05 per success. Which is better?',
        ['Always A', 'Depends on what a success is worth and what a failure costs', 'Always B'],
        answer=1,
        why="If a success saves $20 of human time, A may win; if it saves $0.50, B does. That's the return on investment (ROI) question: what you get back for what you spend.",
    ),
    angle=angle(
        pattern='Running totals, then divide',
        text="The big idea: one number isn't enough for an agent, so track success rate, steps and cost per success. Your code goes through the runs once, keeping three running totals. Every run adds its cost, failed ones too. Successful runs also add one win and their steps. Then it divides: wins by all runs for the success rate, steps by wins for the average steps, and total cost by wins for the cost per success. If nothing succeeded, the last two are `None`, because you can't divide by zero.",
        say='"I report how often the agent [[succeeds|runs|answers::Out of all runs, how many actually worked.]], how many steps the good runs take, and the cost per success. That cost includes the [[failed runs|fast runs|first run::You still pay for the tries that didn\'t work.]], so the price is honest."',
        classic=None,
    ),
    stack=stack('MLflow: an LLM judge for task success', 'from mlflow.genai.judges import make_judge\ntask_done = make_judge(\n    name="task_success",\n    instructions="Did the agent complete the user\'s task?\\nUser: {{ inputs }}\\nAgent: {{ outputs }}\\nAnswer yes or no.",\n)\nmlflow.genai.evaluate(data=tasks, predict_fn=run_agent, scorers=[task_done])'),
    exercise=exercise(
        title='Score an Agent',
        topic='agents',
        difficulty='easy',
        fn='agent_scorecard',
        prompt="""You ran an agent on some test tasks. `runs` has one dict per run, like `{"success": True, "steps": 4, "cost": 0.1}`, where cost is in dollars. There is always at least one run.

Return a list of three numbers, each rounded to 2 decimal places:

- the success rate: the number of successful runs divided by the number of runs
- the average `steps` of the successful runs (add up their steps, then divide by the number of successful runs)
- the cost per success: the total cost of **all** runs divided by the number of successful runs

If no run succeeded, the last two are `None`.""",
        pattern='One pass with a few running totals, then divide, with a guard for zero successes.',
        target='one walk through the runs',
        realworld="Success rate alone is misleading for agents. An agent that succeeds 90% of the time but needs 12 steps and $0.40 per success may be worse value than one at 80% with 4 steps. Cost per success puts failures' cost where it belongs.",
        starter="""def agent_scorecard(runs):
    # your code here
    pass
""",
        solution="""def agent_scorecard(runs):
    wins = 0
    win_steps = 0
    total_cost = 0
    for run in runs:
        total_cost += run["cost"]
        if run["success"]:
            wins += 1
            win_steps += run["steps"]
    rate = round(wins / len(runs), 2)
    if wins == 0:
        return [rate, None, None]
    return [rate, round(win_steps / wins, 2), round(total_cost / wins, 2)]
""",
        cases=[
            case([
                {'success': True, 'steps': 4, 'cost': 0.1},
                {'success': False, 'steps': 10, 'cost': 0.5},
                {'success': True, 'steps': 6, 'cost': 0.3},
            ], expected=[0.67, 5.0, 0.45], sample=True),
            case([{'success': False, 'steps': 3, 'cost': 0.2}], expected=[0.0, None, None]),
            case([{'success': True, 'steps': 2, 'cost': 0.1}, {'success': True, 'steps': 3, 'cost': 0.3}], expected=[1.0, 2.5, 0.2]),
            case([
                {'success': True, 'steps': 5, 'cost': 0.2},
                {'success': False, 'steps': 8, 'cost': 0.6},
                {'success': False, 'steps': 9, 'cost': 0.6},
                {'success': False, 'steps': 12, 'cost': 0.6},
            ], expected=[0.25, 5.0, 2.0]),
        ],
        guided="""def agent_scorecard(runs):
    # Replace every ___ with real code, then run the tests.

    wins = 0
    win_steps = 0
    total_cost = 0
    for run in runs:
        # Step 1: add this run's cost. Every run counts,
        #         success or not.
        total_cost += ___
        if run["success"]:
            wins += 1
            win_steps += run["steps"]

    rate = round(wins / len(runs), 2)
    # Step 2: no successes? Nothing to divide by.
    if ___:
        return [rate, None, None]
    # Step 3: total cost divided by the number of wins.
    return [rate, round(win_steps / wins, 2), round(___, 2)]
""",
        fills=['run["cost"]', 'wins == 0', 'total_cost / wins'],
        concepts=[
            [
                'Running totals',
                '`+=` adds to a variable, so it can keep a total as you loop.',
                """total = 0
for price in [2, 3]:
    total += price   # total is 5""",
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
        byhand='3 runs, and 2 succeeded: 2 divided by 3 rounds to 0.67. The successful runs took 4 and 6 steps: 4 + 6 = 10, and 10 divided by 2 is 5. All three runs cost money: 0.1 + 0.5 + 0.3 = 0.9 dollars. Spread over 2 successes, that is 0.45 each. Return [0.67, 5, 0.45].',
        why='One walk through the runs.',
        gotchas=[
            [
                'Define success before you run',
                '"Did the agent finish the task?" needs a clear rule or an LLM judge with a rubric, checked against a few human labels.',
            ],
            [
                "Watch the failures' cost",
                'Failed runs are often the longest and most expensive, because the agent keeps trying.',
            ],
        ],
    ),
)

lesson(MODULE, 'pass_rates',
    title='Reliable every time (pass hat k)',
    learn=[
        'A success rate from one try per task hides how inconsistent an agent is. Run each task several times, say k times, and look at two numbers.',
        '**pass@k**: the task succeeded **at least once** in k tries. Useful when a person picks the best attempt. **pass^k** (read "pass hat k"): the task succeeded **every time** in k tries. That is closer to what users feel, because each user gets one try.',
        'The gap grows fast. If each try succeeds 80% of the time on its own, three in a row succeed only about 51% of the time: multiply 0.8 by itself three times and you get 0.512. Agent benchmarks such as tau-bench report pass^k for exactly this reason.',
    ],
    example=example('Three tasks, three tries each', """task       try 1   try 2   try 3
refund       ✓       ✓       ✓     → counts for pass@3 and pass^3
address      ✓       ✗       ✓     → counts for pass@3 only
cancel       ✗       ✗       ✗     → counts for neither
pass@3 = 2/3, about 0.67    pass^3 = 1/3, about 0.33"""),
    check=question(
        'Each try of your agent succeeds 90% of the time. Roughly how often does it succeed five times in a row?',
        ['90%', 'About 59%', 'About 45%'],
        answer=1,
        why='Multiply 0.9 by itself five times and you get about 0.59. A 90% agent fails at least once in five runs about 4 times in 10.',
    ),
    angle=angle(
        pattern="Count 'at least once' and 'every time'",
        text="The big idea: one try per task hides how unreliable an agent is, so you run each task several times and count two things. Your code goes through the tasks one by one. For each task, Python's `any` says whether at least one try worked, and `all` says whether every try worked. Dividing each count by the number of tasks gives pass@k and pass^k. The second is the one users feel, because each user only gets one try.",
        say='"I run each task several times. I count how often it worked [[at least once|on average|the first time::One good try out of many is enough for this count.]] and how often it worked [[every time|most times|sometimes::No try is allowed to fail.]]. Users feel the second number, because they only get one try."',
        classic=None,
    ),
    stack=stack('MLflow: log both rates for an agent version', """with mlflow.start_run(run_name="agent-v7-k3"):
    mlflow.log_params({"k": 3, "tasks": len(runs)})
    mlflow.log_metrics(pass_rates(runs))"""),
    exercise=exercise(
        title='Lucky or Reliable?',
        topic='agents',
        difficulty='easy',
        fn='pass_rates',
        prompt="""Each test task was tried several times (call it k times; you don't need k itself). `runs` has one list per task, holding `True` or `False` for each try, like `[[True, True], [True, False]]`. There is always at least one task.

Return a dict with two numbers, each rounded to 2 decimal places:

- `"pass_at_k"`: the number of tasks that succeeded on at least one try, divided by the number of tasks
- `"pass_hat_k"`: the number of tasks that succeeded on every try, divided by the number of tasks""",
        pattern='One pass over the tasks with two counters, using any and all.',
        target='one pass over all the tries',
        realworld='An agent that solves a task 2 times out of 3 looks fine in a demo and fails one user in three. pass^k is the number that predicts the support tickets.',
        starter="""def pass_rates(runs):
    # your code here
    pass
""",
        solution="""def pass_rates(runs):
    at_least_once = 0
    every_time = 0
    for tries in runs:
        if any(tries):
            at_least_once += 1
        if all(tries):
            every_time += 1
    n = len(runs)
    return {
        "pass_at_k": round(at_least_once / n, 2),
        "pass_hat_k": round(every_time / n, 2),
    }
""",
        cases=[
            case([[True, True, True], [True, False, True], [False, False, False]], expected={'pass_at_k': 0.67, 'pass_hat_k': 0.33}, sample=True),
            case([[True, True], [True, True]], expected={'pass_at_k': 1.0, 'pass_hat_k': 1.0}),
            case([[True, False], [False, True], [True, True], [False, False]], expected={'pass_at_k': 0.75, 'pass_hat_k': 0.25}),
            case([[False, True]], expected={'pass_at_k': 1.0, 'pass_hat_k': 0.0}),
            case([[False, False, False]], expected={'pass_at_k': 0.0, 'pass_hat_k': 0.0}),
        ],
        guided="""def pass_rates(runs):
    # Replace every ___ with real code, then run the tests.

    at_least_once = 0
    every_time = 0
    for tries in runs:
        # Step 1: succeeded on at least one try?
        if ___:
            at_least_once += 1
        # Step 2: succeeded on every try?
        if ___:
            every_time += 1

    # Step 3: turn the counts into shares of all tasks.
    n = len(runs)
    return {
        "pass_at_k": round(at_least_once / n, 2),
        "pass_hat_k": round(every_time / n, 2),
    }
""",
        fills=['any(tries)', 'all(tries)'],
        concepts=[
            [
                'any and all',
                '`any`: is at least one item True? `all`: is every item True?',
                """any([True, False])   # True
all([True, False])   # False""",
            ],
            [
                'round',
                '`round(x, 2)` keeps 2 decimal places.',
                'round(1 / 3, 2)   # 0.33',
            ],
        ],
        byhand='Task 1 is True, True, True: it succeeded at least once, and every time. Task 2 is True, False, True: at least once, but not every time. Task 3 is False, False, False: neither. At least once: 2 tasks out of 3, which rounds to 0.67. Every time: 1 task out of 3, which rounds to 0.33. Return {"pass_at_k": 0.67, "pass_hat_k": 0.33}.',
        why='One look at each try.',
        gotchas=[
            [
                'Independent tries',
                'Each try must start fresh: new session, no memory of the previous try, ideally a different random seed (the starting number that controls the randomness in the model). Otherwise you are measuring one try three times.',
            ],
            [
                'k changes the number',
                'pass^3 and pass^8 are different metrics. Always say which k you used, and keep it fixed when comparing versions.',
            ],
        ],
    ),
)

lesson(MODULE, 'tool_call_scores',
    title='Right tool, right arguments',
    learn=[
        'An agent can reach the right answer the wrong way, or fail because one call had a bad argument. For test tasks where you know the correct calls, score the calls themselves.',
        'Score two levels. **Tool selection**: was the right tool called at each step? **Arguments**: was it the right tool *and* the right arguments? A refund with the amount 25 instead of 250 picked the right tool and still did real damage.',
        'Count missing and extra calls as wrong, by dividing by the length of the longer list. Where you have a reference like this, the check is plain code, with no LLM judge to argue with. Benchmarks such as tau-bench go one step further and check the **final state**, like the database after the task.',
    ],
    example=example('Two levels of correct', """expected                              actual                               tool  args
lookup_order(order_id="A-1")          lookup_order(order_id="A-1")          ✓     ✓
refund(order_id="A-1", amount=250)    refund(order_id="A-1", amount=25)     ✓     ✗
tool selection 2/2 = 1.0      arguments 1/2 = 0.5"""),
    check=question(
        'The agent called exactly the right tools, in the right order, but one argument was wrong. What do the two scores look like?',
        [
            'Both 1.0: the tools were right',
            'Tool selection 1.0, arguments below 1.0',
            'Both below 1.0',
        ],
        answer=1,
        why='Tool selection only checks names. The argument score is what catches the wrong amount.',
    ),
    angle=angle(
        pattern='Compare the lists side by side',
        text='The big idea: an agent can pick the right tool with the wrong argument, so score tool choice and arguments separately. Your code lines up the two lists and compares first with first, second with second, for as many places as both lists have. If the names match, that counts as a right tool. If the args match as well, it also counts as right args. Then it divides both counts by the length of the longer list. So a missing or extra call counts as wrong, like a blank answer on a test.',
        say='"When I know the right calls, I score the [[tool choice|tool speed|tool count::Did it pick the right tool?]] and the [[arguments|answers|timings::What it passed into the tool.]] separately. A missing or extra call counts as [[wrong|half right|skipped::Like leaving a test question blank.]]."',
        classic=None,
    ),
    stack=stack('MLflow: a code scorer over the agent\'s tool calls', """from mlflow.genai.scorers import scorer

@scorer
def tool_args_correct(outputs, expectations):
    scores = tool_call_scores(expectations["calls"], outputs["calls"])
    return scores["args"]"""),
    exercise=exercise(
        title='Score the Tool Calls',
        topic='agents',
        difficulty='easy',
        fn='tool_call_scores',
        prompt="""Your function gets two things:

- `expected`: the tool calls the agent should make, in order.
- `actual`: the tool calls it really made, in order.

Each call is a dict like `{"name": "refund", "args": {"amount": 250}}`. `args` are the values passed to the tool. `expected` always has at least one call.

Compare the lists position by position: first with first, second with second, and so on. Count two things:

- right tool: positions where both calls have the same name
- right args: positions where the names match and the args are equal

Divide each count by the length of the longer list, so a missing or extra call counts as wrong. Return `{"tool": ..., "args": ...}` with the two results, each rounded to 2 decimal places.""",
        pattern='One walk over the positions both lists have, then divide by the longer list.',
        target='one pass over the calls',
        realworld='Agent teams run these checks automatically on every code change (CI), on a set of tasks with known correct calls. A drop in the argument score after a prompt change often explains a drop in task success before anyone reads a trace (MLflow\'s saved record of every step one run took).',
        starter="""def tool_call_scores(expected, actual):
    # your code here
    pass
""",
        solution="""def tool_call_scores(expected, actual):
    longest = max(len(expected), len(actual))
    right_tool = 0
    right_args = 0
    for i in range(min(len(expected), len(actual))):
        if expected[i]["name"] == actual[i]["name"]:
            right_tool += 1
            if expected[i]["args"] == actual[i]["args"]:
                right_args += 1
    return {
        "tool": round(right_tool / longest, 2),
        "args": round(right_args / longest, 2),
    }
""",
        cases=[
            case([{'name': 'lookup_order', 'args': {'order_id': 'A-1'}}, {'name': 'refund', 'args': {'amount': 250}}],
                 [{'name': 'lookup_order', 'args': {'order_id': 'A-1'}}, {'name': 'refund', 'args': {'amount': 25}}],
                 expected={'tool': 1.0, 'args': 0.5}, sample=True),
            case([{'name': 'search', 'args': {'q': 'x'}}], [{'name': 'search', 'args': {'q': 'x'}}, {'name': 'search', 'args': {'q': 'x'}}],
                 expected={'tool': 0.5, 'args': 0.5}),
            case([{'name': 'a', 'args': {}}, {'name': 'b', 'args': {}}], [{'name': 'b', 'args': {}}, {'name': 'a', 'args': {}}],
                 expected={'tool': 0.0, 'args': 0.0}),
            case([{'name': 'a', 'args': {}}, {'name': 'b', 'args': {}}], [{'name': 'a', 'args': {}}],
                 expected={'tool': 0.5, 'args': 0.5}),
            case([{'name': 'lookup_order', 'args': {'order_id': 'A-1'}}, {'name': 'refund', 'args': {'amount': 250}}, {'name': 'email', 'args': {}}],
                 [{'name': 'lookup_order', 'args': {'order_id': 'A-1'}}, {'name': 'refund', 'args': {'amount': 25}}, {'name': 'close', 'args': {}}],
                 expected={'tool': 0.67, 'args': 0.33}),
            case([{'name': 'search', 'args': {'q': 'x'}}], [], expected={'tool': 0.0, 'args': 0.0}),
        ],
        guided="""def tool_call_scores(expected, actual):
    # Replace every ___ with real code, then run the tests.

    # Step 1: the length of the longer list.
    #         Dividing by it makes a missing or extra
    #         call count as wrong.
    longest = ___
    right_tool = 0
    right_args = 0

    # Step 2: compare the positions both lists have.
    for i in range(min(len(expected), len(actual))):
        if expected[i]["name"] == actual[i]["name"]:
            right_tool += 1
            # Step 3: right tool. Are the args equal too?
            if ___:
                right_args += 1

    return {
        "tool": round(right_tool / longest, 2),
        "args": round(right_args / longest, 2),
    }
""",
        fills=['max(len(expected), len(actual))', 'expected[i]["args"] == actual[i]["args"]'],
        concepts=[
            [
                'max and min',
                '`max` gives the bigger of its values, `min` the smaller.',
                """max(2, 3)   # 3
min(2, 3)   # 2""",
            ],
            [
                'Walking positions with range',
                '`range(n)` counts from 0 up to, but not including, n. Use each number to look up the item at that position.',
                """names = ['a', 'b']
for i in range(2):
    print(i, names[i])
# 0 a, then 1 b""",
            ],
            [
                'Comparing dicts',
                '`==` on two dicts is True when they have the same keys with the same values, in any order.',
                """a = {'x': 1, 'y': 2}
a == {'y': 2, 'x': 1}   # True""",
            ],
        ],
        byhand='Both lists have 2 calls, so divide by 2. Position 1: lookup_order and lookup_order, with the same args. Right tool, right args. Position 2: refund and refund, but amount 250 against 25. Right tool, wrong args. Tool: 2 out of 2, which is 1. Args: 1 out of 2, which is 0.5. Return {"tool": 1, "args": 0.5}.',
        why='One step per position.',
        gotchas=[
            [
                'Order may not matter',
                'Two independent lookups can happen in either order. When order does not matter, compare the calls in any order instead, like the unordered mode in the next lesson.',
            ],
            [
                'Normalise arguments first',
                '"A-1" and "a-1", or 250 and 250.0, may mean the same thing. Decide what counts as equal before you score.',
            ],
        ],
    ),
)

lesson(MODULE, 'trajectory_match',
    title='Did it take a sensible path?',
    learn=[
        'The path an agent takes matters as well as the answer. An agent that searches twelve times before answering costs more and breaks more easily, even when the answer is right. The list of tools it called is its **trajectory**.',
        "Compare it with a reference path, choosing how strict to be. These four modes are the ones LangChain's AgentEvals library uses: **strict**, the same tools in the same order; **unordered**, the same tools, each the same number of times, in any order; **superset**, every expected tool was called, and extra calls are fine; **subset**, it only called tools from the expected list, though it may have skipped some.",
        'Pick the mode for each task. Use strict for a required procedure, like checking identity before a refund. Use superset when an extra lookup is harmless. Use subset when calling an unexpected tool is the risk, like an agent that should only ever read.',
    ],
    example=example('One path, four verdicts', """expected: lookup_order, refund
actual:   lookup_order, check_policy, refund

strict     ✗  (an extra call)
unordered  ✗  (not the same tools)
superset   ✓  (both expected tools were called)
subset     ✗  (check_policy was not expected)"""),
    check=question(
        'Refunds must only happen after an identity check. Which mode should the test use?',
        ['superset', 'unordered', 'strict'],
        answer=2,
        why='Only strict checks the order. superset and unordered would pass an agent that refunds first and checks identity afterwards.',
    ),
    angle=angle(
        pattern='Four ways to compare a path',
        text='The big idea: the path an agent takes matters, and you choose how strict to be for each task. Your code looks at `mode` and runs one test. Strict asks whether the two lists are exactly equal. Unordered sorts both lists, putting them in order, then compares them, so the same tools the same number of times will pass. Superset checks that every expected tool shows up in `actual`. Subset checks that every tool in `actual` was on the expected list. Any other mode returns `False`.',
        say='"I pick how strict to be for each task. I use strict when the [[order|cost|speed::Sometimes step one must come before step two.]] is a rule, superset when [[extra|fewer|slow::Additional lookups do no harm here.]] lookups are fine, and subset when a surprise tool is the risk."',
        classic=None,
    ),
    stack=stack("AgentEvals: the same modes on LangChain message lists", """from agentevals.trajectory.match import create_trajectory_match_evaluator

evaluator = create_trajectory_match_evaluator(trajectory_match_mode="superset")
result = evaluator(outputs=agent_messages, reference_outputs=reference_messages)"""),
    exercise=exercise(
        title='Match the Trajectory',
        topic='agents',
        difficulty='easy',
        fn='trajectory_match',
        prompt="""An agent's trajectory is the list of tools it called. Check it against the tools it should have called.

Your function gets three things:

- `expected`: the tool names the agent should call, in order, like `["lookup_order", "refund"]`.
- `actual`: the tool names it really called, in order, like `["lookup_order", "check_policy", "refund"]`.
- `mode`: how strict to be, like `"superset"`: one of the four below.

Return `True` if `actual` passes for that mode, otherwise `False`:

- `"strict"`: the same tools in the same order.
- `"unordered"`: the same tools, each the same number of times, in any order.
- `"superset"`: every tool in `expected` is somewhere in `actual`. Extra calls are fine.
- `"subset"`: every tool in `actual` is somewhere in `expected`. Skipping some is fine.""",
        pattern='One comparison per mode: equal lists, equal sorted lists, or "is each one in the other list?" in one direction.',
        target='a sort for unordered; for the others, one check per tool against the other list',
        realworld='Teams write one reference path per test task and choose a mode for it, so a test fails when the agent breaks a rule that matters and passes when it just takes a harmless detour.',
        starter="""def trajectory_match(expected, actual, mode):
    # your code here
    pass
""",
        solution="""def trajectory_match(expected, actual, mode):
    if mode == "strict":
        return expected == actual
    if mode == "unordered":
        return sorted(expected) == sorted(actual)
    if mode == "superset":
        for tool in expected:
            if tool not in actual:
                return False
        return True
    if mode == "subset":
        for tool in actual:
            if tool not in expected:
                return False
        return True
    return False
""",
        cases=[
            case(['lookup_order', 'refund'], ['lookup_order', 'check_policy', 'refund'], 'superset', expected=True, sample=True),
            case(['lookup_order', 'refund'], ['lookup_order', 'check_policy', 'refund'], 'strict', expected=False),
            case(['lookup_order', 'refund'], ['lookup_order', 'check_policy', 'refund'], 'subset', expected=False),
            case(['a', 'b'], ['b', 'a'], 'unordered', expected=True),
            case(['a', 'b'], ['b', 'a'], 'strict', expected=False),
            case(['search', 'search', 'answer'], ['search', 'answer'], 'unordered', expected=False),
            case(['search', 'answer'], ['answer'], 'subset', expected=True),
            case([], ['delete_table'], 'subset', expected=False),
        ],
        guided="""def trajectory_match(expected, actual, mode):
    # Replace every ___ with real code, then run the tests.

    # strict: the same lists, order included.
    if mode == "strict":
        return expected == actual
    # Step 1: same tools in any order? Compare them sorted.
    if mode == "unordered":
        return ___
    # Step 2: every expected tool must have been called.
    if mode == "superset":
        for tool in expected:
            if tool not in actual:
                return False
        return True
    # Step 3: every tool it called must have been expected.
    if mode == "subset":
        for tool in actual:
            if ___:
                return False
        return True
    return False
""",
        fills=['sorted(expected) == sorted(actual)', 'tool not in expected'],
        concepts=[
            [
                'Comparing lists',
                '`==` on two lists is True when they hold the same items in the same order.',
                """[1, 2] == [1, 2]   # True
[1, 2] == [2, 1]   # False""",
            ],
            [
                'Sorting to ignore order',
                '`sorted(items)` gives a new list in order, A to Z. Two lists hold the same items, repeats included, exactly when their sorted versions are equal.',
                """sorted(['b', 'a'])   # ['a', 'b']
sorted(['a', 'b'])   # ['a', 'b']
# equal, so same items""",
            ],
            [
                '`in` with a list',
                '`x in items` is True when x is somewhere in the list. `not in` is the opposite.',
                """fruit = ['apple', 'pear']
'pear' in fruit       # True
'kiwi' not in fruit   # True""",
            ],
        ],
        byhand='The mode is superset, so check each expected tool. lookup_order is in actual. refund is in actual too. Every expected tool was called, and the extra check_policy is fine in this mode. Return True.',
        why='Sorting is the slowest step for unordered. superset and subset check each tool against the other list, which is fine for a short list of tools.',
        gotchas=[
            [
                'Loops hide inside superset',
                'superset passes an agent that called search twenty times. Pair it with a step limit or a loop check, covered later in the Tracing module.',
            ],
            [
                'One mode per task, written down',
                'Choose the mode when you write the test, not after you see the agent fail it.',
            ],
        ],
    ),
)

lesson(MODULE, 'compare_designs',
    title='Comparing agent designs',
    learn=[
        'There are several ways to build the same agent. **ReAct**: think, call a tool, look, repeat. **Plan-and-execute**: write the plan first, then follow it.',
        'A **supervisor** is a main agent whose tools are specialist helper agents. In LangGraph each design is a different graph. Which is better depends on your tasks, so measure it instead of guessing.',
        'Run every design on **the same tasks**, several times each. Compare how often a run succeeds, and how many tasks succeed on **every** try (the pass^k idea). Also compare the **cost per success**: the cost of all runs, failed ones included, spread over the runs that worked.',
        'Then read the tasks one design fails and another passes, trace by trace. Planning first often wastes fewer tool calls but breaks when the plan is wrong. A supervisor adds overhead that only pays off on tasks with genuinely separate parts.',
    ],
    example=example('Three designs, same 20 tasks, 3 tries each', """design            success   reliable tasks   cost per success
react               80%          65%             $0.040
plan_execute        78%          75%             $0.028
supervisor          83%          70%             $0.090
→ plan_execute: almost as successful, the most reliable, the cheapest"""),
    check=question(
        'Supervisor succeeds 3 points more often than ReAct but costs more than twice as much per success. What should you do next?',
        [
            'Check the gap is real, then weigh it against cost',
            'Pick Supervisor, since it solves the most tasks',
            'Pick ReAct, since it costs less per success',
        ],
        answer=0,
        why='First check the 3 points are more than the normal ups and downs between repeat runs. Then decide if they are worth paying more than twice as much per success.',
    ),
    angle=angle(
        pattern='Group by design, then work out rates',
        text="The big idea: measure agent designs on the same tasks instead of guessing, and compare success rate and cost per success. Your code sorts the runs into piles by design. For each pile it keeps three running numbers: runs, wins and cost. They live in a dict, a lookup table from the design's name to its numbers. At the end it divides wins by runs for the success rate. It divides cost by wins for the cost per success, or gives `None` if that design never succeeded.",
        say='"I run every design on the [[same tasks|easiest tasks|its own tasks::A fair race uses one course for everyone.]]. Then I compare success rate and cost per success, with the cost of [[failed runs|setup|training::You pay for every try, even ones that didn\'t work.]] counted in."',
        classic='group_anagrams',
    ),
    stack=stack('LangChain: build a supervisor, then compare', '''from langchain.agents import create_agent
from langchain.tools import tool

# create_agent builds a LangGraph graph.
# The supervisor sees only a helper's
# last message, so put everything there.
researcher = create_agent(
    llm, tools=[search],
    system_prompt="Put every finding "
                  "in your final answer.")

@tool
def research(question: str) -> str:
    """Research a question and report."""
    out = researcher.invoke(
        {"messages": [("user", question)]})
    return out["messages"][-1].text

# Rewording a helper's answer loses
# details, so pass it on as it is.
supervisor = create_agent(
    llm, tools=[research, refunds],
    system_prompt="Pass helper answers "
                  "on word for word.")
# (langgraph-supervisor is archived.)

# react: a plain create_agent with the
# same tools. Same tasks, 3 tries each.
for agent in [react, supervisor]:
    for task in tasks:
        for attempt in range(3):
            agent.invoke(task)
# Log success and cost for each run,
# then score them as in the exercise.'''),
    exercise=exercise(
        title='Score Each Agent Design',
        topic='agents',
        difficulty='medium',
        fn='compare_designs',
        prompt="""You ran several agent designs on the same tasks. `runs` has one dict per run, like `{"design": "react", "success": True, "cost": 0.04}`, where cost is in dollars.

Group the runs by `design`. Return a dict with one key per design name. Each value is a dict with two numbers, each rounded to 2 decimal places:

- `"success_rate"`: the number of the design's successful runs divided by the number of all its runs
- `"cost_per_success"`: the total cost of all its runs divided by the number of its successful runs, or `None` if it never succeeded

For example: `{"react": {"success_rate": 0.67, "cost_per_success": 0.06}}`.

(The lesson's "reliable tasks" number needs a task id for each run, so it is left out here.)""",
        pattern='Group the runs by design, keeping running totals, then summarise each group.',
        target='one pass over the runs, then one over the designs',
        realworld='Agent teams compare designs exactly like this before committing to a graph shape, because the most successful design is often not the cheapest per useful answer.',
        starter="""def compare_designs(runs):
    # your code here
    pass
""",
        solution="""def compare_designs(runs):
    totals = {}
    for run in runs:
        name = run["design"]
        if name not in totals:
            totals[name] = {"runs": 0, "wins": 0, "cost": 0}
        totals[name]["runs"] += 1
        totals[name]["cost"] += run["cost"]
        if run["success"]:
            totals[name]["wins"] += 1
    report = {}
    for name in totals:
        t = totals[name]
        cost_per_success = None
        if t["wins"] > 0:
            cost_per_success = round(t["cost"] / t["wins"], 2)
        report[name] = {
            "success_rate": round(t["wins"] / t["runs"], 2),
            "cost_per_success": cost_per_success,
        }
    return report
""",
        cases=[
            case([
                {'design': 'react', 'success': True, 'cost': 0.04},
                {'design': 'react', 'success': False, 'cost': 0.05},
                {'design': 'react', 'success': True, 'cost': 0.03},
                {'design': 'plan', 'success': True, 'cost': 0.02},
            ], expected={'react': {'success_rate': 0.67, 'cost_per_success': 0.06},
                         'plan': {'success_rate': 1.0, 'cost_per_success': 0.02}}, sample=True),
            case([{'design': 'super', 'success': False, 'cost': 0.1}],
                 expected={'super': {'success_rate': 0.0, 'cost_per_success': None}}),
            case([
                {'design': 'a', 'success': True, 'cost': 0.1},
                {'design': 'b', 'success': False, 'cost': 0.2},
                {'design': 'a', 'success': False, 'cost': 0.3},
                {'design': 'c', 'success': True, 'cost': 0.5},
                {'design': 'b', 'success': True, 'cost': 0.4},
            ], expected={'a': {'success_rate': 0.5, 'cost_per_success': 0.4},
                         'b': {'success_rate': 0.5, 'cost_per_success': 0.6},
                         'c': {'success_rate': 1.0, 'cost_per_success': 0.5}}),
            case([
                {'design': 'react', 'success': True, 'cost': 0.1},
                {'design': 'react', 'success': True, 'cost': 0.3},
                {'design': 'react', 'success': True, 'cost': 0.2},
            ], expected={'react': {'success_rate': 1.0, 'cost_per_success': 0.2}}),
        ],
        guided="""def compare_designs(runs):
    # Replace every ___ with real code, then run the tests.

    totals = {}
    for run in runs:
        name = run["design"]
        # Step 1: first time you see this design?
        #         Start its totals at zero.
        if ___:
            totals[name] = {"runs": 0, "wins": 0, "cost": 0}
        # Add this run to its design's totals.
        totals[name]["runs"] += 1
        totals[name]["cost"] += run["cost"]
        if run["success"]:
            totals[name]["wins"] += 1

    report = {}
    for name in totals:
        t = totals[name]   # this design's totals
        # Step 2: total cost divided by wins,
        #         if there were any wins.
        cost_per_success = None
        if t["wins"] > 0:
            cost_per_success = round(___, 2)
        report[name] = {
            # Step 3: successful runs out of all runs.
            "success_rate": round(___, 2),
            "cost_per_success": cost_per_success,
        }
    return report
""",
        fills=['name not in totals', 't["cost"] / t["wins"]', 't["wins"] / t["runs"]'],
        concepts=[
            [
                'Starting a group',
                'Before you add to a group in a dict, create it the first time you see its name.',
                """if fruit not in counts:
    counts[fruit] = 0
counts[fruit] += 1""",
            ],
            [
                'A dict inside a dict',
                "`d['a']['b']` looks up 'a', then looks up 'b' in what it found.",
                """totals = {'react': {'runs': 2}}
totals['react']['runs']   # 2""",
            ],
            [
                'Looping over a dict',
                '`for key in d` gives each key, in the order they were added.',
                """for name in {'react': 1, 'plan': 2}:
    print(name)   # react, then plan""",
            ],
            [
                'Running totals',
                '`+=` adds to a variable, so it can keep a total as you loop.',
                """total = 0
for price in [2, 3]:
    total += price   # total is 5""",
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
        byhand='Group by design. react has 3 runs, and 2 succeeded: 2 out of 3 rounds to 0.67. Its costs, 0.04, 0.05 and 0.03, add up to 0.12, and 0.12 divided by 2 successes is 0.06 each. plan has 1 run, and it succeeded: 1 out of 1 is 1.0. It cost 0.02 for 1 success, so 0.02 each. Return {"react": {"success_rate": 0.67, "cost_per_success": 0.06}, "plan": {"success_rate": 1.0, "cost_per_success": 0.02}}.',
        why='One step per run, then one per design.',
        gotchas=[
            [
                'Same tasks for every design',
                'If one design ran on easier tasks, the comparison means nothing. Check every design has the same task list and the same number of attempts.',
            ],
            [
                'Cost per success, not per run',
                'A cheap design that fails half the time can cost more per *useful* answer than an expensive one that rarely fails.',
            ],
        ],
    ),
)

lesson(MODULE, 'approval_run',
    title='Human approval in LangGraph',
    learn=[
        'Some agent actions need a person to say yes. The agent should **pause**, save exactly where it was, and **resume** when the answer comes, even hours later.',
        'In LangGraph, `interrupt()` pauses, a **checkpointer** saves the state under a `thread_id` (an id for this conversation), and `Command(resume=...)` continues from that point.',
    ],
    example=example('Pause and resume', """run 1: look_up_order → issue_refund? (pause, waiting for a person)
run 2 with "approve": issue_refund → email_customer → done"""),
    check=question(
        'Why does pausing for a person to approve (human-in-the-loop) need a checkpointer?',
        ['To make it faster', "To save the agent's state so it can resume after the pause", 'For logging'],
        answer=1,
        why='Without saved state, the agent would have to start over.',
    ),
    angle=angle(
        pattern='Stop at the first unapproved risky step',
        text="The big idea: some agent actions need a person to say yes, so the agent pauses there and resumes later. Your code goes through the steps in order. A step that isn't risky runs and is added to `ran`. A risky step runs only if its name is in `approved`. At the first risky step nobody approved, the code returns right away with what ran so far and the name of the step it paused at. If it reaches the end, `paused_at` is `None`.",
        say='"Risky steps [[pause|fail|get skipped::They wait instead of running.]] until a person says yes. LangGraph saves the state under a [[thread id|password|file name::A label that lets you find this one run again.]], so the run picks up from that exact point once someone approves."',
        classic=None,
    ),
    stack=stack('LangGraph: interrupt and resume', """from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

def refund_node(state):
    decision = interrupt({"action": "refund", "amount": state["amount"]})
    ...

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "ticket-1042"}}
graph.invoke(inputs, config)                     # pauses at the interrupt
graph.invoke(Command(resume="approve"), config)  # continues"""),
    exercise=exercise(
        title='Pause for a Human',
        topic='agents',
        difficulty='medium',
        fn='approval_run',
        prompt="""Some agent steps are risky, so a person must approve them first.

Your function gets two things:

- `steps`: the steps to run, in order. Each is `[name, risky]`, like `["issue_refund", True]`. `risky` is `True` when a person must approve the step.
- `approved`: the names of the risky steps a person has already approved, like `["issue_refund"]`.

Go through the steps in order. A step with `risky` False runs. A risky step runs only if its name is in `approved`. If it isn't, the agent pauses there and runs nothing more.

Return a dict with two keys:

- `"ran"`: the names of the steps that ran, in order
- `"paused_at"`: the name of the step it paused on, or `None` if every step ran""",
        pattern='Walk the steps in order, and pause at the first risky step nobody has approved.',
        target='one walk through the steps',
        realworld='This is human-in-the-loop in LangGraph: `interrupt()` pauses the graph, a checkpointer saves its state under a `thread_id`, and `Command(resume=...)` continues it later, even after a restart. Your function runs every step again from the start. LangGraph is smarter: the checkpointer saved the finished steps, so it picks up at the paused step with the approval filled in.',
        starter="""def approval_run(steps, approved):
    # your code here
    pass
""",
        solution="""def approval_run(steps, approved):
    ran = []
    for name, risky in steps:
        if risky and name not in approved:
            return {"ran": ran, "paused_at": name}
        ran.append(name)
    return {"ran": ran, "paused_at": None}
""",
        cases=[
            case([['look_up_order', False], ['issue_refund', True], ['email_customer', False]], [], expected={'ran': ['look_up_order'], 'paused_at': 'issue_refund'}, sample=True),
            case([['look_up_order', False], ['issue_refund', True], ['email_customer', False]], ['issue_refund'], expected={'ran': ['look_up_order', 'issue_refund', 'email_customer'], 'paused_at': None}),
            case([['delete_table', True], ['report', False]], [], expected={'ran': [], 'paused_at': 'delete_table'}),
            case([['refund', True], ['email', False], ['close_account', True]], ['refund'], expected={'ran': ['refund', 'email'], 'paused_at': 'close_account'}),
            case([['search', False], ['answer', False]], [], expected={'ran': ['search', 'answer'], 'paused_at': None}),
            case([], [], expected={'ran': [], 'paused_at': None}),
        ],
        guided="""def approval_run(steps, approved):
    # Replace every ___ with real code, then run the tests.

    ran = []
    for name, risky in steps:
        # Step 1: risky and not approved? Pause here.
        if risky and ___:
            return {"ran": ran, "paused_at": name}
        # Step 2: otherwise it runs: add its name to ran.
        ___

    # Step 3: every step ran, so nothing is paused.
    return {"ran": ran, "paused_at": ___}
""",
        fills=['name not in approved', 'ran.append(name)', 'None'],
        concepts=[
            [
                'Unpacking in a for loop',
                'When each item is a pair, the for line can name both parts.',
                """for city, sunny in [['Rome', True]]:
    print(city, sunny)""",
            ],
            [
                '`in` with a list',
                '`x in items` is True when x is somewhere in the list. `not in` is the opposite.',
                """fruit = ['apple', 'pear']
'kiwi' not in fruit   # True""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ana')   # ['Ana']""",
            ],
            [
                'Returning early',
                '`return` inside a loop ends the whole function right there, even mid-loop. Here `first_big([1, 5, 2])` gives 5.',
                """def first_big(nums):
    for n in nums:
        if n > 3:
            return n""",
            ],
            [
                'None',
                "Python's way to say \"no value\".",
                'paused_at = None',
            ],
        ],
        byhand='look_up_order is not risky, so it runs. issue_refund is risky, and approved is empty, so pause there. email_customer never runs. Return {"ran": ["look_up_order"], "paused_at": "issue_refund"}.',
        why='One walk through the steps.',
        gotchas=[
            [
                'Steps before the pause may run twice',
                'When LangGraph resumes, the node containing interrupt() runs again from its start. Put actions that change things, like sending an email, after the interrupt, or make them **idempotent** (safe to run twice).',
            ],
            [
                "Show the person what they're approving",
                'Pass the action and its arguments to the interrupt, so the reviewer sees "refund $250 on A-1042", not just "approve?".',
            ],
        ],
    ),
)

lesson(MODULE, 'next_action',
    title='An agent that runs code',
    learn=[
        'Code a model writes often fails on the first try. A **coding agent** runs its code, reads the error, writes a fix and runs it again. Each run ends with an **exit code**: 0 means no error, and anything else means it failed.',
        'Give the loop a **retry limit** (often called max retries): the most rounds it gets, such as 3. Without one, a stuck agent keeps spending money.',
        "Some errors are **environment errors** (problems with the setup), not bugs in the code, so rewriting the code rarely helps. Teams call these **non-retryable** errors. A missing **dependency** (a package of code someone else wrote, like pandas, that isn't installed) or a **permission error** (the code isn't allowed to touch that file) fails the same way every round. Send those to a person instead of retrying.",
        "Run the code in a **sandbox**: a locked-down computer of its own, with a time limit and no internet, so a bad run can't touch real data. When the agent says \"done\", check the real result yourself: run the tests, or read the table. Agents often report success that never happened.",
    ],
    example=example('Four separate runs, with 3 rounds allowed', """exit  round  last line         next
0     1      3 passed          done
1     1      NameError: ...    fix
1     2      PermissionError   ask
1     3      KeyError: 'id'    stop"""),
    check=question(
        "A run fails with `PermissionError: [Errno 13] Permission denied: 'out.csv'`. Why should the agent ask a person instead of writing a fix?",
        [
            'Permission errors often clear up if you just run the code again',
            'Asking a person is cheaper than one more call to the model',
            'The file is blocked, and changing the code can only work around that',
        ],
        answer=2,
        why='No rewrite grants access. An agent that tries anyway tends to work around the block, for example by writing somewhere else, so a person should decide.',
    ),
    angle=angle(
        pattern='Rules checked in order',
        text="The big idea: a coding agent retries after errors, but it needs a retry limit, and environment errors should go to a person. Your code checks rules in order and stops at the first match. Exit code 0 means done. Reaching the retry limit means stop, because there are no tries left. A permission error or a missing package means ask a person, since rewriting the code won't help. Anything else is a bug the agent can try to fix. The order matters: a run that passes on its last round still returns done.",
        say='"I stop when the [[check passes|code looks right|agent says done::Trust a real test, not a feeling.]] or the retry limit is hit. Permission and missing-package errors go to a [[person|retry|log::Rewriting the code won\'t fix these.]]. Only real code bugs get another try."',
        classic=None,
    ),
    stack=stack('LangGraph: route after each run', '''# startswith can take a tuple: it is
# True if the line starts with any one.
SETUP = ("PermissionError",
         "ModuleNotFoundError")

def route(state):
    line = state["last_line"]
    if state["exit_code"] == 0:
        return "check_result"
    if state["round"] >= 3:
        return "stop"
    if line.startswith(SETUP):
        return "ask_human"   # interrupt()
    if "Permission denied" in line:
        return "ask_human"
    return "write_fix"

builder.add_conditional_edges(
    "run_code", route)
# run_code calls a sandbox. On
# Databricks, the system.ai.sandbox MCP
# service (a tool server the agent can
# call) runs Python, SQL or shell with
# no internet (it needs the Unity
# Gateway beta).'''),
    exercise=exercise(
        title='Pick the Next Step',
        topic='agents',
        difficulty='easy',
        fn='next_action',
        prompt="""A coding agent just ran its code. Decide what it does next.

Your function gets four things:

- `exit_code`: how the run ended. `0` means no error; anything else, like `1`, means it failed.
- `last_line`: the last line the run printed, like `"NameError: name 'totl' is not defined"`.
- `round_number`: which round just ran, counting from 1, like `2`.
- `max_rounds`: the most rounds allowed, like `3`.

Check these rules in order, and return at the first one that matches:

- `exit_code` is 0: return `"done"`.
- `round_number` is at least `max_rounds`: return `"stop"`.
- `last_line` starts with `"PermissionError"` or `"ModuleNotFoundError"`, or contains `"Permission denied"`: return `"ask"`.
- Otherwise, return `"fix"`.""",
        pattern='Rules checked in order: return at the first one that matches.',
        target='a few checks, one after another, with no loop',
        realworld='This is the routing step after each run in a coding agent, like a LangGraph conditional edge after a `run_code` node, with a sandbox running the code. "done" should lead to a real check (run the tests, read the table), not straight to "finished", because agents often report success that never happened.',
        starter="""def next_action(exit_code, last_line,
                round_number, max_rounds):
    # your code here
    pass
""",
        solution="""def next_action(exit_code, last_line,
                round_number, max_rounds):
    if exit_code == 0:
        return "done"
    if round_number >= max_rounds:
        return "stop"
    if last_line.startswith("PermissionError"):
        return "ask"
    if last_line.startswith("ModuleNotFoundError"):
        return "ask"
    if "Permission denied" in last_line:
        return "ask"
    return "fix"
""",
        cases=[
            case(1, "NameError: name 'totl' is not defined", 2, 3, expected='fix', sample=True),
            case(0, '3 passed in 0.12s', 3, 3, expected='done'),
            case(1, "ModuleNotFoundError: No module named 'pandas'", 3, 3, expected='stop'),
            case(1, "ModuleNotFoundError: No module named 'pandas'", 1, 3, expected='ask'),
            case(1, "PermissionError: [Errno 1] Operation not permitted: 'out.csv'", 2, 3, expected='ask'),
            case(126, 'bash: ./run.sh: Permission denied', 1, 5, expected='ask'),
        ],
        guided="""def next_action(exit_code, last_line,
                round_number, max_rounds):
    # Replace every ___ with real code, then run the tests.

    # Step 1: exit code 0 means no error.
    if exit_code == 0:
        return "done"

    # Step 2: is round_number at least max_rounds?
    if ___:
        return "stop"

    # Step 3: environment errors go to a person.
    if last_line.startswith("PermissionError"):
        return "ask"
    # Same again, for "ModuleNotFoundError".
    if ___:
        return "ask"
    # Step 4: does last_line contain
    #         "Permission denied"?
    if ___:
        return "ask"

    # Step 5: any other error is a bug to fix.
    return "fix"
""",
        fills=['round_number >= max_rounds', 'last_line.startswith("ModuleNotFoundError")', '"Permission denied" in last_line'],
        concepts=[
            [
                'Returning early',
                '`return` ends the function right there, so the checks after it never run. That is why the order of the checks matters.',
                """def size(n):
    if n > 100:
        return 'big'
    return 'small'""",
            ],
            [
                'Comparing numbers',
                '`a >= b` is True when a is b or more, so it means "at least".',
                """4 >= 4   # True
3 >= 4   # False""",
            ],
            [
                'startswith',
                '`text.startswith(x)` is True when the text begins with x. Capital letters must match too.',
                """'Hi Ana'.startswith('Hi')   # True
'hi'.startswith('Hi')       # False""",
            ],
            [
                '`in` with text',
                '`x in text` is True when x appears anywhere in the text.',
                "'tea' in 'green tea'   # True",
            ],
        ],
        byhand='exit_code is 1, not 0, so the run failed: not "done". round_number is 2 and max_rounds is 3, and 2 is not at least 3: not "stop". last_line starts with "NameError", not "PermissionError" or "ModuleNotFoundError", and it doesn\'t contain "Permission denied": not "ask". No rule matched, so return "fix".',
        why='A few checks one after another, with nothing to loop over.',
        gotchas=[
            [
                'Retrying environment errors',
                'A package that isn\'t installed or a blocked file fails the same way every round, so the agent burns all its rounds. Worse, it may "fix" it by working around the block. Send these to a person.',
            ],
            [
                'Trusting "done"',
                'Exit code 0 only means nothing crashed. Before you call the task finished, check the real result: the tests pass, or the table has the new rows.',
            ],
        ],
    ),
)

lesson(MODULE, 'assemble_stream',
    title='Streaming responses',
    learn=[
        "**Streaming** shows the answer as it's generated, so users see something in a few hundred milliseconds instead of waiting for the whole reply.",
        "Text arrives in small pieces, and so do tool-call arguments. Your code has to put the pieces back together, and only parse a tool call once it's complete.",
    ],
    example=example('A stream of pieces', """text "Let me " · text "check." · tool_start lookup_order
tool_args '{"order_id": ' · tool_args '"A-1042"}' · tool_end"""),
    check=question(
        "When can you safely parse a tool call's JSON arguments?",
        ['On each piece', 'Once the tool call has finished streaming', 'Never'],
        answer=1,
        why="Half a JSON object isn't valid JSON.",
    ),
    angle=angle(
        pattern='Join the pieces as they arrive',
        text="The big idea: streaming sends the answer in small pieces, so your code must put them back together and only use a tool call once it is complete. Your code goes through the events one by one. Text pieces are added onto one long string. A tool start remembers the tool's name and begins an empty argument string. Argument pieces are added onto that. A tool end saves the finished name and arguments to `calls`, then clears them. It is like writing down a phone number someone reads out one digit at a time.",
        say='"The answer streams in small pieces, so I [[join|drop|sort::Put the bits back together as they come.]] them as they arrive. I only use a tool call once its [[end event|first piece|name::The signal that says the call is complete.]] comes, so I never act on half the arguments."',
        classic=None,
    ),
    stack=stack('LangGraph: stream tokens as they arrive', """for chunk, metadata in graph.stream(inputs, stream_mode="messages"):
    print(chunk.content, end="", flush=True)"""),
    exercise=exercise(
        title='Put a Stream Back Together',
        topic='agents',
        difficulty='medium',
        fn='assemble_stream',
        prompt="""Streaming sends a reply in small pieces while it is being written. `chunks` is the stream: a list of events, each `[kind, piece]`. There are four kinds:

- `["text", piece]`: more of the reply text.
- `["tool_start", name]`: a tool call begins.
- `["tool_args", piece]`: more of the current tool call's arguments.
- `["tool_end", ""]`: the current tool call is finished.

Join all the text pieces into one string. Join each tool call's argument pieces (the details the tool needs, like the search words) into one string too.

Return `[text, calls]`. `calls` has one `[name, args]` for each finished call, in order. `args` is that call's argument pieces joined together.""",
        pattern='Add pieces to a buffer (a string you keep growing), and save the buffer when its end marker arrives.',
        target='one walk through the chunks',
        realworld='Users see the first words in a few hundred milliseconds instead of waiting for the whole answer. LangGraph streams with `stream_mode="messages"` (token pieces) or `"updates"` (node results), and `ResponsesAgent.predict_stream` streams from a Databricks endpoint. Tool-call arguments arrive in pieces too, and are only valid JSON once complete.',
        starter="""def assemble_stream(chunks):
    # your code here
    pass
""",
        solution="""def assemble_stream(chunks):
    text = ""
    calls = []
    name, args = None, ""
    for kind, piece in chunks:
        if kind == "text":
            text += piece
        elif kind == "tool_start":
            name, args = piece, ""
        elif kind == "tool_args":
            args += piece
        elif kind == "tool_end":
            calls.append([name, args])
            name, args = None, ""
    return [text, calls]
""",
        cases=[
            case([
                ['text', 'Let me '],
                ['text', 'check.'],
                ['tool_start', 'search'],
                ['tool_args', 'weather in '],
                ['tool_args', 'Paris'],
                ['tool_end', ''],
            ], expected=['Let me check.', [['search', 'weather in Paris']]], sample=True),
            case([
                ['text', 'One moment.'],
                ['tool_start', 'lookup_order'],
                ['tool_args', '{"order_id": '],
                ['tool_args', '"A-1042"}'],
                ['tool_end', ''],
            ], expected=['One moment.', [['lookup_order', '{"order_id": "A-1042"}']]]),
            case([], expected=['', []]),
            case([['text', 'Hi']], expected=['Hi', []]),
            case([['tool_start', 'a'], ['tool_end', ''], ['tool_start', 'b'], ['tool_args', '{}'], ['tool_end', '']], expected=['', [['a', ''], ['b', '{}']]]),
        ],
        guided="""def assemble_stream(chunks):
    # Replace every ___ with real code, then run the tests.

    text = ""
    calls = []
    name, args = None, ""   # the tool call being built
    for kind, piece in chunks:
        if kind == "text":
            text += piece   # more reply text
        elif kind == "tool_start":
            # A new call: keep its name, empty args.
            name, args = piece, ""
        elif kind == "tool_args":
            # Step 1: add this piece to the arguments.
            ___
        elif kind == "tool_end":
            # Step 2: call done. Save [name, args], a list,
            #         to calls. Then reset.
            calls.append(___)
            name, args = None, ""
    return [text, calls]
""",
        fills=['args += piece', '[name, args]'],
        concepts=[
            [
                'Adding to a string',
                '`+=` sticks more text onto the end of a string.',
                """s = 'Good '
s += 'morning'   # 'Good morning'""",
            ],
            [
                'Unpacking in a for loop',
                'When each item is a pair, the for line can name both parts.',
                """pets = [['cat', 'meow']]
for animal, sound in pets:
    print(animal, sound)""",
            ],
            [
                'elif',
                'Short for "else if". It is checked only when the ifs above it were False.',
                """if n > 10:
    size = 'big'
elif n > 3:
    size = 'medium'""",
            ],
            [
                'Setting two names at once',
                '`a, b = 1, 2` sets a to 1 and b to 2 in one line.',
                """first, last = 'Ana', 'Lee'""",
            ],
            [
                'None',
                "Python's way to say \"no value\". The code starts `name` as None because no tool call has started yet.",
                """best = None
if best is None:
    print('nothing yet')""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts x on the end of the list. x can be a list too.',
                """pairs = []
pairs.append(['Ana', 30])
# pairs is [['Ana', 30]]""",
            ],
        ],
        byhand='The two text pieces join into "Let me check.". tool_start begins a call named search, with empty arguments. The two tool_args pieces join into "weather in Paris". tool_end finishes the call, so save ["search", "weather in Paris"]. Return the text and the list of calls: ["Let me check.", [["search", "weather in Paris"]]].',
        why='One walk through the chunks.',
        gotchas=[
            [
                "Don't parse arguments early",
                "Half a JSON object isn't valid JSON. Parse tool arguments only when the call ends.",
            ],
            [
                'Streaming changes error handling',
                "An error can arrive after you've already shown half an answer. Decide how the UI shows a stream that fails midway.",
            ],
        ],
    ),
)
