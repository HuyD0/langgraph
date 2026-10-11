"""Agents with LangGraph: The agent loop, memory, tools from Unity Catalog, and scoring the result."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('agents', 'Agents with LangGraph', 'The agent loop, memory, tools from Unity Catalog, and scoring the result.')

lesson(MODULE, 'run_agent',
    title='The agent loop',
    learn=[
        'An **agent** is a loop: the model picks a tool, your code runs it, the result goes back to the model, repeat until it gives a final answer.',
        'Two rules keep it safe: a **hard step limit**, and turning tool errors into messages the model can read instead of crashes.',
    ],
    example=example('The shape of every agent', """for step in range(MAX_STEPS):
    action = model(history)
    if action.final:
        return action.text
    history.append(run_tool(action))"""),
    check=question(
        'Why must an agent loop have a maximum number of steps?',
        [
            'To make answers shorter',
            'A confused model can loop forever and keep spending tokens',
            'The API requires it',
        ],
        answer=1,
        why="Nothing else stops a model that keeps calling the same tool. LangGraph's recursion_limit exists for this.",
    ),
    angle=angle(
        pattern='Bounded iteration',
        text='The loop runs at most max_steps times, and each step is one lookup. The interview point is the stopping rules: a final answer, the step limit, or the end of the plan.',
        say='"Every loop that depends on a model has a hard limit, and tool errors go back to the model as messages so it can recover."',
        classic=None,
    ),
    stack=stack('LangGraph: a hard step limit', """graph = builder.compile()
graph.invoke({"messages": messages}, config={"recursion_limit": 10})
# Raises GraphRecursionError instead of looping forever."""),
    exercise=exercise(
        title='Run an Agent Loop',
        topic='agents',
        difficulty='medium',
        fn='run_agent',
        prompt="""An agent is a loop: the model picks a tool, the tool runs, the result goes back to the model. Here the model's choices are already written down in `plan`, a list of `[name, arg]` steps. `tools` is a dict of tools, each a dict from argument to result.

Go through at most `max_steps` steps and build a list called the log. For `["final", text]`, add `"answer: " + text` and return the log. For a tool you don't have, add `"error: unknown tool " + name` and keep going. Otherwise add the tool's result. If you run out of steps or plan without a final answer, add `"stopped"` and return.""",
        pattern='A loop with a hard stop. Errors become messages the agent can see, not crashes.',
        target='one pass, never more than `max_steps`',
        realworld="The core of LangGraph's ReAct agent and every tool-calling loop. Without `max_steps`, a confused model can loop forever and run up your bill.",
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
            case([['search', 'weather paris'], ['final', "It's sunny"]], {'search': {'weather paris': 'sunny, 22C'}}, 5, expected=['sunny, 22C', "answer: It's sunny"], sample=True),
            case([['calc', '2+2'], ['final', '4']], {'search': {}}, 5, expected=['error: unknown tool calc', 'answer: 4']),
            case([['search', 'a'], ['search', 'a'], ['search', 'a'], ['final', 'x']], {'search': {'a': 'b'}}, 2, expected=['b', 'b', 'stopped']),
            case([], {}, 3, expected=['stopped']),
            case([['final', 'hi']], {}, 1, expected=['answer: hi']),
            case([['lookup', 'id7'], ['search', 'q']], {'lookup': {'id7': 'Ana'}, 'search': {'q': 'found'}}, 10, expected=['Ana', 'found', 'stopped']),
        ],
        guided="""def run_agent(plan, tools, max_steps):
    # Replace every ___ with real code, then run the tests.

    log = []
    # Step 1: never go past max_steps.
    for name, arg in plan[:___]:
        # Step 2: a final answer ends the loop.
        if name == "final":
            log.append("answer: " + ___)
            return log
        # Step 3: unknown tool? Log an error and keep going.
        if name not in ___:
            log.append("error: unknown tool " + name)
        else:
            log.append(tools[___][___])

    # Step 4: no final answer in time.
    log.append("___")
    return log
""",
        concepts=[
            [
                'Unpacking in a for loop',
                'If each item is a pair, you can name both parts right in the loop.',
                """for name, arg in [['search', 'cats']]:
    print(name, arg)""",
            ],
            [
                'Slicing to a limit',
                'plan[:3] gives at most the first 3 steps, even if the plan is shorter.',
                '[1, 2][:3]   # [1, 2]',
            ],
            [
                'Nested dicts',
                "tools['search']['cats'] looks up the search tool, then the result for 'cats'.",
                """tools = {'search': {'cats': 'meow'}}
tools['search']['cats']   # 'meow'""",
            ],
        ],
        byhand='Plan: search "weather paris", then final "It\'s sunny". Step 1 is a tool you have, so log its result, "sunny, 22C". Step 2 is final, so log "answer: It\'s sunny" and stop. Now try max_steps 1: you\'d only get the search step, then "stopped".',
        why='At most max_steps steps, each one a single dict lookup.',
        gotchas=[
            [
                'No step limit',
                'A model that keeps calling the same tool will loop forever and spend money the whole time. LangGraph has recursion_limit for exactly this reason.',
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
# walk rest from newest to oldest, keep while under budget"""),
    check=question(
        'You keep only `messages[-10:]`. What can go wrong?',
        [
            'Nothing',
            'The system prompt falls off and the assistant forgets its instructions',
            'The reply gets slower',
        ],
        answer=1,
        why='The system prompt is the first message. Slicing from the end drops it once the chat is long enough.',
    ),
    angle=angle(
        pattern='Greedy from one end',
        text='Walk backwards once and stop at the first message that doesn\'t fit. Many "budget" problems, including two-pointer and sliding-window ones, use the same thinking.',
        say='"I keep the system message, then fill the rest of the budget from the newest message backwards and stop at the first that doesn\'t fit, so there are no gaps."',
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
        prompt="""A chat model can only read so much. `messages` is a list of `[role, text]` pairs, oldest first. Keep the conversation under `max_words` words in total by dropping the oldest messages.

Rules: if the first message has the role `"system"`, always keep it, even if it alone goes over. Then keep the newest messages that still fit, and stop at the first one that doesn't, so there are no gaps. Return the kept messages in their original order.""",
        pattern='Pin what must stay, then fill the remaining budget from the newest end.',
        target='walk back through the messages once',
        realworld='Chat memory in every assistant. Dropping the system prompt by accident is one of the most common bugs, and the bot suddenly forgets its instructions.',
        starter="""def trim_history(messages, max_words):
    # your code here
    pass
""",
        solution="""def trim_history(messages, max_words):
    system = []
    rest = messages
    if messages and messages[0][0] == "system":
        system = [messages[0]]
        rest = messages[1:]
    used = 0
    for m in system:
        used += len(m[1].split())
    kept = []
    for m in reversed(rest):
        words = len(m[1].split())
        if used + words > max_words:
            break
        kept.append(m)
        used += words
    return system + kept[::-1]
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
            case([['user', 'a b c'], ['assistant', 'd e']], 2, expected=[['assistant', 'd e']]),
            case([['system', 'x y z']], 1, expected=[['system', 'x y z']]),
            case([], 5, expected=[]),
            case([['user', 'one'], ['assistant', 'a b c d e f'], ['user', 'two']], 3, expected=[['user', 'two']]),
        ],
        guided="""def trim_history(messages, max_words):
    # Replace every ___ with real code, then run the tests.

    # Step 1: pin the system message, if there is one.
    system = []
    rest = messages
    if messages and messages[0][0] == ___:
        system = [messages[0]]
        rest = messages[___:]

    # Step 2: count the words the system message already uses.
    used = 0
    for m in system:
        used += len(m[1].split())

    # Step 3: newest first, keep messages while they fit.
    kept = []
    for m in reversed(___):
        words = len(m[1].split())
        if used + words > ___:
            break
        kept.append(m)
        used += words

    # Step 4: kept is newest-first. Flip it back.
    return system + kept[___]
""",
        concepts=[
            [
                'reversed',
                'Walks a list from the last item to the first, without changing the list.',
                """for m in reversed(['a', 'b', 'c']):
    print(m)   # c, b, a""",
            ],
            ['[::-1]', 'Gives a reversed copy of a list.', '[1, 2, 3][::-1]   # [3, 2, 1]'],
            [
                'Counting words',
                'len(text.split()) is a quick word count.',
                "len('hello how are you'.split())   # 4",
            ],
        ],
        byhand='Budget 7. The system message "be nice" (2 words) always stays, so 5 are left. Go from the newest: "good thanks" (2) fits, 3 left. "hello how are you" (4) doesn\'t fit, so stop there, even though "hi there" would fit. You want no gaps. Put them back in order: system, then "good thanks".',
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

lesson(MODULE, 'tool_schema',
    title='Tools from Unity Catalog',
    learn=[
        "An agent's tools are described to the model as a **name**, a **description** and **parameters**. The model picks a tool by reading those descriptions, so they are part of your prompt.",
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
        pattern='Building nested structures',
        text='A lookup table for the types, then one step per parameter to fill the properties. Interviews test this as "transform this data into that shape".',
        say='"I map each parameter through a type lookup table into the properties dict, collect the required names in order, and wrap it in the schema."',
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
        prompt="""A model can only call a tool it has been told about. Turn a Unity Catalog function into the tool description that chat models read.

You get the function's `name`, its `description`, and `params`, a list of `[name, sql_type, comment]` like `["order_id", "STRING", "The order number"]`. Map SQL types to JSON types: `STRING` → `"string"`, `INT` and `BIGINT` → `"integer"`, `DOUBLE` and `FLOAT` → `"number"`, `BOOLEAN` → `"boolean"`.

Return `{"type": "function", "function": {"name": ..., "description": ..., "parameters": {"type": "object", "properties": {...}, "required": [...]}}}`, where each property is `{"type": json_type, "description": comment}` and every parameter is required, in order.""",
        pattern='A lookup table for the type mapping, then build a nested dict one level at a time.',
        target='one step per parameter',
        realworld="`UCFunctionToolkit` in `databricks_langchain` builds exactly this from a function in Unity Catalog, using the function's and parameters' comments as the descriptions. Vague comments make the model call the wrong tool or pass bad arguments, so the comment is part of your prompt.",
        starter="""def tool_schema(name, description, params):
    # your code here
    pass
""",
        solution="""TYPES = {"STRING": "string", "INT": "integer", "BIGINT": "integer", "DOUBLE": "number", "FLOAT": "number", "BOOLEAN": "boolean"}

def tool_schema(name, description, params):
    properties = {}
    required = []
    for pname, sql_type, comment in params:
        properties[pname] = {"type": TYPES[sql_type], "description": comment}
        required.append(pname)
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required}}}
""",
        cases=[
            case('lookup_order', "Look up an order's status and delivery date", [['order_id', 'STRING', 'The order number, like A-1042']], expected={
                'type': 'function',
                'function': {
                    'name': 'lookup_order',
                    'description': "Look up an order's status and delivery date",
                    'parameters': {
                        'type': 'object',
                        'properties': {'order_id': {'type': 'string', 'description': 'The order number, like A-1042'}},
                        'required': ['order_id'],
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
            case('refund', 'Refund part of an order', [
                ['order_id', 'STRING', 'Order number'],
                ['amount', 'DOUBLE', 'Dollars to refund'],
                ['notify', 'BOOLEAN', 'Email the customer'],
                ['reason_code', 'INT', '1 damaged, 2 late'],
            ], expected={
                'type': 'function',
                'function': {
                    'name': 'refund',
                    'description': 'Refund part of an order',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'order_id': {'type': 'string', 'description': 'Order number'},
                            'amount': {'type': 'number', 'description': 'Dollars to refund'},
                            'notify': {'type': 'boolean', 'description': 'Email the customer'},
                            'reason_code': {'type': 'integer', 'description': '1 damaged, 2 late'},
                        },
                        'required': ['order_id', 'amount', 'notify', 'reason_code'],
                    },
                },
            }),
        ],
        guided="""TYPES = {"STRING": "string", "INT": "integer", "BIGINT": "integer", "DOUBLE": "number", "FLOAT": "number", "BOOLEAN": "boolean"}

def tool_schema(name, description, params):
    # Replace every ___ with real code, then run the tests.

    properties = {}
    required = []
    for pname, sql_type, comment in params:
        # Step 1: describe this parameter, using the TYPES lookup.
        properties[pname] = {"type": ___, "description": comment}
        # Step 2: every parameter is required.
        ___
    # Step 3: wrap it up in the shape models expect.
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required}}}
""",
        fills=['TYPES[sql_type]', 'required.append(pname)'],
        concepts=[
            [
                'A lookup table',
                'A dict that translates one name into another.',
                """TYPES = {'STRING': 'string'}
TYPES['STRING']   # 'string'""",
            ],
            [
                'Unpacking three values',
                'Each param is a list of three, so the for line can name all three.',
                """for pname, sql_type, comment in params:
    ...""",
            ],
        ],
        byhand='One parameter: order_id, STRING, "The order number". Its property is {"type": "string", "description": "The order number"} and required is ["order_id"]. Wrap that in parameters, then in function, then add type "function" at the top.',
        why='One step per parameter.',
        gotchas=[
            [
                'The comment is the prompt',
                '"id" tells the model nothing. "The order number, like A-1042" tells it the format, and fewer calls fail.',
            ],
            [
                'Give the agent least privilege',
                "A Unity Catalog function runs with the permissions it's granted. Grant the agent EXECUTE on the few functions it needs, not on a whole schema.",
            ],
        ],
    ),
)

lesson(MODULE, 'tool_pairs',
    title='Tool calls and results',
    learn=[
        'When a model calls tools, each call gets an **id**, and each result must reference it. Model APIs reject a conversation where a call has no matching result.',
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
        pattern='Matching pairs',
        text='Open on a call, close on its result, and report anything left open or closed without being opened, in one walk through the messages. Valid Parentheses is the same idea with a stack, because brackets must close in order.',
        say='"I track open call ids and each result closes one. Whatever is still open at the end, or closed without being opened, is an error."',
        classic='valid_parentheses',
    ),
    stack=stack('LangGraph: ToolNode answers every tool call', """from langgraph.prebuilt import ToolNode
builder.add_node("tools", ToolNode(tools))
# One ToolMessage per call, with the matching tool_call_id, errors included."""),
    exercise=exercise(
        title='Match Tool Calls to Results',
        topic='agents',
        difficulty='medium',
        fn='tool_pairs',
        prompt="""In a tool-using chat, the assistant asks for tools and each request gets an id. Each result message must answer one of those ids.

`messages` is a list of dicts. An assistant message may have `"tool_calls"`, a list like `[{"id": "call_1", "name": "search"}]`. A tool result looks like `{"role": "tool", "tool_call_id": "call_1"}`. Other messages have neither.

Return `[unanswered, orphans]`: the ids of calls that never got a result, and the ids of results that don't answer an earlier, still-open call. Both in the order they appear.""",
        pattern="Matching pairs: open something, close it later. Track what's open, and complain about anything closed that wasn't open.",
        target='one pass over the messages',
        realworld='Model APIs reject a conversation where a tool call has no result. This usually happens after trimming chat history cuts a call away from its result, and it shows up as a confusing 400 error in production.',
        starter="""def tool_pairs(messages):
    # your code here
    pass
""",
        solution="""def tool_pairs(messages):
    open_ids = []
    orphans = []
    for m in messages:
        for call in m.get("tool_calls", []):
            open_ids.append(call["id"])
        if m.get("role") == "tool":
            cid = m["tool_call_id"]
            if cid in open_ids:
                open_ids.remove(cid)
            else:
                orphans.append(cid)
    return [open_ids, orphans]
""",
        cases=[
            case([
                {'role': 'user', 'content': 'weather in Paris and Rome?'},
                {
                    'role': 'assistant',
                    'tool_calls': [{'id': 'call_1', 'name': 'weather'}, {'id': 'call_2', 'name': 'weather'}],
                },
                {'role': 'tool', 'tool_call_id': 'call_1', 'content': '22C'},
            ], expected=[['call_2'], []], sample=True),
            case([], expected=[[], []]),
            case([
                {'role': 'tool', 'tool_call_id': 'call_9'},
                {'role': 'assistant', 'tool_calls': [{'id': 'call_9', 'name': 'search'}]},
            ], expected=[['call_9'], ['call_9']]),
            case([
                {'role': 'assistant', 'tool_calls': [{'id': 'a', 'name': 'x'}]},
                {'role': 'tool', 'tool_call_id': 'a'},
                {'role': 'tool', 'tool_call_id': 'a'},
            ], expected=[[], ['a']]),
            case([
                {'role': 'assistant', 'content': 'hello'},
                {'role': 'assistant', 'tool_calls': [{'id': 'c1', 'name': 'x'}, {'id': 'c2', 'name': 'y'}]},
                {'role': 'tool', 'tool_call_id': 'c2'},
                {'role': 'tool', 'tool_call_id': 'c1'},
            ], expected=[[], []]),
        ],
        guided="""def tool_pairs(messages):
    # Replace every ___ with real code, then run the tests.

    open_ids = []   # calls waiting for a result, in order
    orphans = []
    for m in messages:
        # Step 1: every call this message makes is now open.
        #         .get("tool_calls", []) is empty for messages without calls.
        for call in m.get("tool_calls", []):
            ___

        # Step 2: a tool result closes its call, if that call is open.
        if m.get("role") == "tool":
            cid = m["tool_call_id"]
            if ___:
                open_ids.remove(cid)
            else:
                orphans.append(cid)

    return [open_ids, orphans]
""",
        fills=['open_ids.append(call["id"])', 'cid in open_ids'],
        concepts=[
            [
                'dict.get with a default',
                "Returns the default when the key isn't there, so messages without tool calls just give an empty list.",
                """m = {'role': 'user'}
m.get('tool_calls', [])   # []""",
            ],
            [
                'list.remove',
                'Removes the first matching item.',
                """ids = ['a', 'b']
ids.remove('a')   # ids is ['b']""",
            ],
        ],
        byhand="The assistant opens call_1 and call_2. The tool result answers call_1, so it closes. Nothing answers call_2, so it's unanswered. No result arrived for a call that wasn't open, so there are no orphans.",
        why='One walk through the messages. Removing from a list means searching it, which is fine for a handful of open calls; a set would make it instant.',
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
        'Define success with a clear rule, or an LLM judge with a rubric that you check against a few human labels.',
    ],
    example=example('An LLM judge for task success', 'from mlflow.genai.judges import make_judge\n\ntask_done = make_judge(\n    name="task_success",\n    instructions="Did the agent complete the user\'s task?\\n"\n                 "User: {{ inputs }}\\nAgent: {{ outputs }}\\nAnswer yes or no.",\n)\nmlflow.genai.evaluate(data=tasks, predict_fn=run_agent, scorers=[task_done])'),
    check=question(
        'Agent A: 90% success, $0.40 per success. Agent B: 80% success, $0.05 per success. Which is better?',
        ['Always A', 'Depends on what a success is worth and what a failure costs', 'Always B'],
        answer=1,
        why="If a success saves $20 of human time, A may win; if it saves $0.50, B does. That's the ROI question.",
    ),
    angle=angle(
        pattern='Running totals',
        text='One walk with a few counters, then divide with guards for the zero cases.',
        say='"One pass to total successes, steps and cost, then ratios guarded against zero successes."',
        classic=None,
    ),
    stack=stack('MLflow: an LLM judge for task success', 'from mlflow.genai.judges import make_judge\ntask_done = make_judge(\n    name="task_success",\n    instructions="Did the agent complete the user\'s task?\\nUser: {{ inputs }}\\nAgent: {{ outputs }}\\nAnswer yes or no.",\n)\nmlflow.genai.evaluate(data=tasks, predict_fn=run_agent, scorers=[task_done])'),
    exercise=exercise(
        title='Score an Agent',
        topic='agents',
        difficulty='easy',
        fn='agent_scorecard',
        prompt="""You ran an agent on a set of test tasks. Each run in `runs` is `{"success": True, "steps": 4, "cost": 0.012}`.

Return `[success_rate, avg_steps_when_successful, cost_per_success]`: the share of successful runs, the average steps of the successful runs, and the total cost of all runs divided by the number of successes. Round each to 2 places, except cost per success, which rounds to 4. If there are no runs, return `[0.0, None, None]`; if none succeeded, the last two are `None`.""",
        pattern='One pass, several running totals, then divide with guards.',
        target='one walk through the runs',
        realworld="Success rate alone is misleading for agents. An agent that succeeds 90% of the time but needs 12 steps and $0.40 per success may be worse value than one at 80% with 4 steps. Cost per success puts failures' cost where it belongs.",
        starter="""def agent_scorecard(runs):
    # your code here
    pass
""",
        solution="""def agent_scorecard(runs):
    if not runs:
        return [0.0, None, None]
    wins = 0
    win_steps = 0
    total_cost = 0
    for r in runs:
        total_cost += r["cost"]
        if r["success"]:
            wins += 1
            win_steps += r["steps"]
    rate = round(wins / len(runs), 2)
    if wins == 0:
        return [rate, None, None]
    return [rate, round(win_steps / wins, 2), round(total_cost / wins, 4)]
""",
        cases=[
            case([
                {'success': True, 'steps': 4, 'cost': 0.012},
                {'success': False, 'steps': 10, 'cost': 0.05},
                {'success': True, 'steps': 6, 'cost': 0.018},
            ], expected=[0.67, 5.0, 0.04], sample=True),
            case([], expected=[0.0, None, None]),
            case([{'success': False, 'steps': 3, 'cost': 0.01}], expected=[0.0, None, None]),
            case([{'success': True, 'steps': 2, 'cost': 0.004}, {'success': True, 'steps': 3, 'cost': 0.006}], expected=[1.0, 2.5, 0.005]),
        ],
        guided="""def agent_scorecard(runs):
    # Replace every ___ with real code, then run the tests.

    if not runs:
        return [0.0, None, None]
    wins = 0
    win_steps = 0
    total_cost = 0
    for r in runs:
        # Step 1: every run costs money, successful or not.
        total_cost += ___
        if r["success"]:
            wins += 1
            win_steps += r["steps"]
    rate = round(wins / len(runs), 2)
    if wins == 0:
        return [rate, None, None]
    # Step 2: failures' cost is spread over the successes.
    return [rate, round(win_steps / wins, 2), round(___, 4)]
""",
        fills=['r["cost"]', 'total_cost / wins'],
        concepts=[
            [
                'Running totals',
                '`+=` adds to a variable.',
                """total = 0
total += 0.012""",
            ],
        ],
        byhand='Two of three succeed: 0.67. Their steps are 4 and 6: average 5. Total cost is 0.012 + 0.05 + 0.018 = 0.08, over 2 successes: 0.04 per success.',
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
    title='Reliable every time: pass^k',
    learn=[
        'A success rate from one try per task hides how inconsistent an agent is. Run each task several times, say k times, and look at two numbers.',
        '**pass@k**: the task succeeded **at least once** in k tries. Useful when a person picks the best attempt. **pass^k** (read "pass hat k"): the task succeeded **every time** in k tries. That is closer to what users feel, because each user gets one try.',
        'The gap grows fast. If each try succeeds 80% of the time on its own, three in a row succeed only 0.8 × 0.8 × 0.8 ≈ 51% of the time. Agent benchmarks such as τ-bench report pass^k for exactly this reason.',
    ],
    example=example('Three tasks, three tries each', """task       try 1   try 2   try 3
refund       ✓       ✓       ✓     → counts for pass@3 and pass^3
address      ✓       ✗       ✓     → counts for pass@3 only
cancel       ✗       ✗       ✗     → counts for neither
pass@3 = 2/3 ≈ 0.67        pass^3 = 1/3 ≈ 0.33"""),
    check=question(
        'Each try of your agent succeeds 90% of the time. Roughly how often does it succeed five times in a row?',
        ['90%', 'About 59%', 'About 45%'],
        answer=1,
        why='0.9 × 0.9 × 0.9 × 0.9 × 0.9 is about 0.59. A 90% agent fails at least once in five runs about 4 times in 10.',
    ),
    angle=angle(
        pattern='any and all',
        text='`any` is true if at least one item is true; `all` is true only if every item is. One pass over the tasks, counting each.',
        say='"I report pass^k next to the single-try success rate, because users feel the inconsistency that one try per task hides."',
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
        prompt="""`runs` has one list per task, each holding the results of k tries as booleans, like `[[True, True, True], [True, False, True]]`.

Return `{"pass_at_k": ..., "pass_hat_k": ...}`:

- `pass_at_k`: the fraction of tasks that succeeded at least once
- `pass_hat_k`: the fraction of tasks that succeeded on every try

Round both to 2 decimal places. With no tasks, both are `0.0`.""",
        pattern='One pass over the tasks with two counters, using any and all.',
        target='one pass over all the tries',
        realworld='An agent that solves a task 2 times out of 3 looks fine in a demo and fails one user in three. pass^k is the number that predicts the support tickets.',
        starter="""def pass_rates(runs):
    # your code here
    pass
""",
        solution="""def pass_rates(runs):
    if not runs:
        return {"pass_at_k": 0.0, "pass_hat_k": 0.0}
    at_least_once = 0
    every_time = 0
    for tries in runs:
        if any(tries):
            at_least_once += 1
        if all(tries):
            every_time += 1
    n = len(runs)
    return {"pass_at_k": round(at_least_once / n, 2), "pass_hat_k": round(every_time / n, 2)}
""",
        cases=[
            case([[True, True, True], [True, False, True], [False, False, False]], expected={'pass_at_k': 0.67, 'pass_hat_k': 0.33}, sample=True),
            case([[True, True], [True, True]], expected={'pass_at_k': 1.0, 'pass_hat_k': 1.0}),
            case([], expected={'pass_at_k': 0.0, 'pass_hat_k': 0.0}),
            case([[True, False], [False, True], [True, True], [False, False]], expected={'pass_at_k': 0.75, 'pass_hat_k': 0.25}),
        ],
        guided="""def pass_rates(runs):
    # Replace every ___ with real code, then run the tests.
    if not runs:
        return {"pass_at_k": 0.0, "pass_hat_k": 0.0}
    at_least_once = 0
    every_time = 0
    for tries in runs:
        # Step 1: succeeded on at least one try?
        if ___:
            at_least_once += 1
        # Step 2: succeeded on every try?
        if ___:
            every_time += 1
    n = len(runs)
    return {"pass_at_k": round(at_least_once / n, 2), "pass_hat_k": round(every_time / n, 2)}
""",
        fills=['any(tries)', 'all(tries)'],
        concepts=[
            [
                'any and all',
                'any: is at least one item true? all: is every item true?',
                """any([True, False])   # True
all([True, False])   # False""",
            ],
        ],
        byhand='Refund passed every try: counts for both. Address passed twice: at least once, but not every time. Cancel never passed. pass@3 = 2/3, pass^3 = 1/3.',
        why='One look at each try.',
        gotchas=[
            [
                'Independent tries',
                'Each try must start fresh: new session, no memory of the previous try, ideally a different random seed. Otherwise you are measuring one try three times.',
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
        'Count missing and extra calls as wrong, by dividing by the longer of the two lists. Where you have a reference like this, the check is plain code, with no LLM judge to argue with. Benchmarks such as τ-bench go one step further and check the **final state**, like the database after the task.',
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
        pattern='Comparing two lists position by position',
        text='Walk the longer list once, checking the same position in both. A missing position on either side counts as wrong.',
        say='"For tasks with a known correct path I score tool selection and arguments separately, and count missing or extra calls as errors."',
        classic=None,
    ),
    stack=stack('MLflow: a code scorer over the trace\'s tool calls', """from mlflow.genai.scorers import scorer

@scorer
def tool_args_correct(outputs, expectations):
    scores = tool_call_scores(expectations["calls"], outputs["calls"])
    return scores["args"]"""),
    exercise=exercise(
        title='Score the Tool Calls',
        topic='agents',
        difficulty='easy',
        fn='tool_call_scores',
        prompt="""`expected` and `actual` are lists of tool calls, in order, each like `{"name": "refund", "args": {"order_id": "A-1", "amount": 250}}`.

Compare them position by position, over the length of the longer list (a call missing on either side counts as wrong). Return:

- `"tool"`: the fraction of positions where both calls exist and the names match
- `"args"`: the fraction where the names match *and* the args are equal

Round both to 2 decimal places. If both lists are empty, both scores are `1.0`.""",
        pattern='One walk over the longer list, checking the same position in both.',
        target='one pass over the calls',
        realworld='Agent teams run these checks in CI on a set of tasks with known correct calls. A drop in the argument score after a prompt change often explains a drop in task success before anyone reads a trace.',
        starter="""def tool_call_scores(expected, actual):
    # your code here
    pass
""",
        solution="""def tool_call_scores(expected, actual):
    longest = max(len(expected), len(actual))
    if longest == 0:
        return {"tool": 1.0, "args": 1.0}
    right_tool = 0
    right_args = 0
    for i in range(min(len(expected), len(actual))):
        if expected[i]["name"] == actual[i]["name"]:
            right_tool += 1
            if expected[i]["args"] == actual[i]["args"]:
                right_args += 1
    return {"tool": round(right_tool / longest, 2), "args": round(right_args / longest, 2)}
""",
        cases=[
            case([{'name': 'lookup_order', 'args': {'order_id': 'A-1'}}, {'name': 'refund', 'args': {'order_id': 'A-1', 'amount': 250}}],
                 [{'name': 'lookup_order', 'args': {'order_id': 'A-1'}}, {'name': 'refund', 'args': {'order_id': 'A-1', 'amount': 25}}],
                 expected={'tool': 1.0, 'args': 0.5}, sample=True),
            case([{'name': 'search', 'args': {'q': 'x'}}], [{'name': 'search', 'args': {'q': 'x'}}, {'name': 'search', 'args': {'q': 'x'}}],
                 expected={'tool': 0.5, 'args': 0.5}),
            case([{'name': 'a', 'args': {}}, {'name': 'b', 'args': {}}], [{'name': 'b', 'args': {}}, {'name': 'a', 'args': {}}],
                 expected={'tool': 0.0, 'args': 0.0}),
            case([{'name': 'a', 'args': {}}, {'name': 'b', 'args': {}}], [{'name': 'a', 'args': {}}],
                 expected={'tool': 0.5, 'args': 0.5}),
            case([], [], expected={'tool': 1.0, 'args': 1.0}),
        ],
        guided="""def tool_call_scores(expected, actual):
    # Replace every ___ with real code, then run the tests.

    # Step 1: missing or extra calls count as wrong, so divide by the longer list.
    longest = ___
    if longest == 0:
        return {"tool": 1.0, "args": 1.0}
    right_tool = 0
    right_args = 0

    # Step 2: compare the positions that exist in both lists.
    for i in range(min(len(expected), len(actual))):
        if expected[i]["name"] == actual[i]["name"]:
            right_tool += 1
            if ___:
                right_args += 1
    return {"tool": round(right_tool / longest, 2), "args": round(right_args / longest, 2)}
""",
        fills=['max(len(expected), len(actual))', 'expected[i]["args"] == actual[i]["args"]'],
        concepts=[
            [
                'Comparing dicts',
                '`==` on two dicts is true when they have the same keys with the same values, in any order.',
                """{"a": 1, "b": 2} == {"b": 2, "a": 1}   # True""",
            ],
        ],
        byhand='Two expected calls, two actual. Position 1: same name, same args. Position 2: same name, amount 250 against 25. Tool 2 of 2 = 1.0; args 1 of 2 = 0.5.',
        why='One step per position.',
        gotchas=[
            [
                'Order may not matter',
                'Two independent lookups can happen in either order. When order does not matter, compare the calls as a set instead, as the next lesson shows.',
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
        "Compare it with a reference path, choosing how strict to be. These four modes are the ones LangChain's AgentEvals library uses: **strict**, the same tools in the same order; **unordered**, the same tools in any order; **superset**, every expected tool was called, and extra calls are fine; **subset**, it only called tools from the expected list, though it may have skipped some.",
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
        pattern='Choosing the right comparison',
        text='strict compares the lists directly. unordered compares them sorted. superset and subset check membership, one item at a time, in one direction or the other.',
        say='"I pick the trajectory match mode per task: strict where order is a rule, superset where extra lookups are fine, subset where unexpected tools are the risk."',
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
        prompt="""`expected` and `actual` are lists of tool names, in the order they were called. Return `True` or `False` for the given `mode`:

- `"strict"`: the same tools in the same order
- `"unordered"`: the same tools, in any order (repeats count)
- `"superset"`: every tool in `expected` appears in `actual`; extra calls are fine
- `"subset"`: every tool in `actual` appears in `expected`; skipping some is fine""",
        pattern='One comparison per mode: direct, sorted, or membership in one direction.',
        target='a sort for unordered; one pass for the others',
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
    if mode == "strict":
        return expected == actual
    # Step 1: same tools in any order: compare them sorted.
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
                'Sorting to ignore order',
                'Two lists hold the same items, repeats included, exactly when their sorted versions are equal.',
                """sorted(["b", "a"]) == sorted(["a", "b"])   # True""",
            ],
        ],
        byhand='Expected lookup_order then refund; the agent added check_policy in between. Both expected tools were called, so superset passes. The lists differ, so strict fails. check_policy was not expected, so subset fails.',
        why='Sorting is the slowest step for unordered; the membership checks look at each tool once.',
        gotchas=[
            [
                'Loops hide inside superset',
                'superset passes an agent that called search twenty times. Pair it with a step limit or a loop check from the Tracing module.',
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
        'There are several ways to build the same agent: **ReAct** (think, call a tool, look, repeat), **plan then execute** (write the plan first, then follow it), or a **supervisor** handing parts of the task to specialist sub-agents. In LangGraph each is a different graph. Which is better depends on your tasks, so measure it.',
        'Run every design on **the same tasks**, several times each, and compare three things side by side: how often a run succeeds, how many tasks succeed on **every** try (the pass^k idea), and the **cost per success**, which spreads the cost of failed runs over the successful ones.',
        'Then read the regressions and improvements, trace by trace. Planning first often wastes fewer tool calls but breaks when the plan is wrong. A supervisor adds overhead that only pays off on tasks with genuinely separate parts.',
    ],
    example=example('Three designs, same 20 tasks, 3 tries each', """design            success   reliable tasks   cost per success
react               80%          65%             $0.040
plan_execute        78%          75%             $0.028
supervisor          83%          70%             $0.090
→ plan_execute: almost as successful, the most reliable, the cheapest"""),
    check=question(
        'Supervisor succeeds 3 points more often than ReAct but costs more than twice as much per success. What do you need to decide?',
        [
            'Always pick the higher success rate',
            "Whether 3 extra points (if they are real) are worth the cost: it's a value question, decided by the rule you wrote first",
            'Always pick the cheaper one',
        ],
        answer=1,
        why='Check the 3 points are more than noise, then weigh them against cost using the decision rule from your plan.',
    ),
    angle=angle(
        pattern='Group by key, then summarise',
        text='Group the runs by design, and within a design by task, keeping running counts. Then turn the counts into rates at the end, guarding against zero successes.',
        say='"I compare agent designs on the same tasks with repeat runs, on success, reliability and cost per success, then read the traces to see why."',
        classic='group_anagrams',
    ),
    stack=stack('LangGraph: the same tasks through each graph, tagged', """designs = {"react": build_react(), "plan_execute": build_planner(), "supervisor": build_supervisor()}
for name, graph in designs.items():
    mlflow.set_active_model(name=f"support-agent-{name}")
    for task in tasks:
        for attempt in range(3):
            run_and_score(graph, task, tags={"design": name, "attempt": str(attempt)})"""),
    exercise=exercise(
        title='Score Each Agent Design',
        topic='agents',
        difficulty='medium',
        fn='compare_designs',
        prompt="""`runs` is a list of dicts like `{"design": "react", "task": "t1", "success": True, "cost": 0.04}`: every attempt of every task with every design.

Return a dict from each design to:

- `"success_rate"`: successful runs ÷ all its runs, rounded to 2 decimal places
- `"reliable"`: the share of its tasks where **every** run succeeded, rounded to 2 decimal places
- `"cost_per_success"`: its total cost ÷ its successful runs, rounded to 3 decimal places, or `None` if it never succeeded""",
        pattern='Group by design, and by task within a design, then summarise each group.',
        target='one pass over the runs, then one over the designs',
        realworld='Agent teams compare designs exactly like this before committing to a graph shape, because the most successful design is often not the most reliable or the cheapest.',
        starter="""def compare_designs(runs):
    # your code here
    pass
""",
        solution="""def compare_designs(runs):
    groups = {}
    for run in runs:
        g = groups.setdefault(run["design"], {"runs": 0, "wins": 0, "cost": 0.0, "tasks": {}})
        g["runs"] += 1
        g["cost"] += run["cost"]
        if run["success"]:
            g["wins"] += 1
        g["tasks"][run["task"]] = g["tasks"].get(run["task"], True) and run["success"]
    report = {}
    for design, g in groups.items():
        steady = 0
        for ok in g["tasks"].values():
            if ok:
                steady += 1
        reliable = steady / len(g["tasks"])
        report[design] = {
            "success_rate": round(g["wins"] / g["runs"], 2),
            "reliable": round(reliable, 2),
            "cost_per_success": round(g["cost"] / g["wins"], 3) if g["wins"] else None,
        }
    return report
""",
        cases=[
            case([
                {'design': 'react', 'task': 't1', 'success': True, 'cost': 0.04},
                {'design': 'react', 'task': 't1', 'success': False, 'cost': 0.05},
                {'design': 'react', 'task': 't2', 'success': True, 'cost': 0.03},
                {'design': 'plan', 'task': 't1', 'success': True, 'cost': 0.02},
                {'design': 'plan', 'task': 't2', 'success': True, 'cost': 0.02},
            ], expected={'react': {'success_rate': 0.67, 'reliable': 0.5, 'cost_per_success': 0.06},
                         'plan': {'success_rate': 1.0, 'reliable': 1.0, 'cost_per_success': 0.02}}, sample=True),
            case([], expected={}),
            case([{'design': 'super', 'task': 't1', 'success': False, 'cost': 0.1}],
                 expected={'super': {'success_rate': 0.0, 'reliable': 0.0, 'cost_per_success': None}}),
        ],
        guided="""def compare_designs(runs):
    # Replace every ___ with real code, then run the tests.
    groups = {}
    for run in runs:
        g = groups.setdefault(run["design"], {"runs": 0, "wins": 0, "cost": 0.0, "tasks": {}})
        g["runs"] += 1
        g["cost"] += run["cost"]
        if run["success"]:
            g["wins"] += 1
        # Step 1: a task stays reliable only while every run of it succeeds.
        g["tasks"][run["task"]] = ___
    report = {}
    for design, g in groups.items():
        steady = 0
        for ok in g["tasks"].values():
            if ok:
                steady += 1
        reliable = steady / len(g["tasks"])
        report[design] = {
            "success_rate": round(g["wins"] / g["runs"], 2),
            "reliable": round(reliable, 2),
            # Step 2: spread the total cost over the successes, if there were any.
            "cost_per_success": ___,
        }
    return report
""",
        fills=['g["tasks"].get(run["task"], True) and run["success"]', 'round(g["cost"] / g["wins"], 3) if g["wins"] else None'],
        concepts=[
            [
                'setdefault',
                'Gets a key\'s value, first inserting a starting value if the key is new. Handy for building groups in one pass.',
                """groups = {}
groups.setdefault("react", []).append(1)   # {"react": [1]}""",
            ],
        ],
        byhand='react: 2 of 3 runs succeeded (0.67). Task t1 failed once, t2 succeeded, so 1 of 2 tasks is reliable (0.5). Cost 0.04 + 0.05 + 0.03 = 0.12 over 2 successes is 0.06. plan: everything succeeded, 0.04 over 2 successes is 0.02.',
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
        'In LangGraph, `interrupt()` pauses, a **checkpointer** saves the state under a `thread_id`, and `Command(resume=...)` continues from that point.',
    ],
    example=example('Pause and resume', """run 1: look_up_order → issue_refund? (pause, waiting for a person)
run 2 with "approve": issue_refund → email_customer → done"""),
    check=question(
        'Why does human-in-the-loop need a checkpointer?',
        ['To make it faster', "To save the agent's state so it can resume after the pause", 'For logging'],
        answer=1,
        why='Without saved state, the agent would have to start over.',
    ),
    angle=angle(
        pattern='Resumable workflow',
        text='One walk through the steps, stopping at the first undecided risky one.',
        say='"Risky steps interrupt; state is checkpointed per thread, and resuming replays to the same point with the human\'s decision."',
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
        prompt="""An agent runs `steps` in order, each `[name, risky]`. Before a risky step it pauses for a person, unless `decisions` (a dict from step name to `"approve"` or `"reject"`) already holds an answer for it.

Go through the steps. A safe step runs. A risky step: with `"approve"` it runs; with `"reject"` the run stops; with no decision the run pauses there.

Return `{"status": "done" | "paused" | "stopped", "ran": [...], "at": name or None}`, where `at` is the step it paused or stopped on.""",
        pattern='Walk the steps; at each risky one, look up a decision and either continue, stop or pause.',
        target='one walk through the steps',
        realworld='This is human-in-the-loop in LangGraph: `interrupt()` pauses the graph, a checkpointer saves its state under a `thread_id`, and `Command(resume=...)` continues it later, even after a restart. Running the same function again with the decision filled in is exactly how resuming works.',
        starter="""def approval_run(steps, decisions):
    # your code here
    pass
""",
        solution="""def approval_run(steps, decisions):
    ran = []
    for name, risky in steps:
        if risky:
            d = decisions.get(name)
            if d is None:
                return {"status": "paused", "ran": ran, "at": name}
            if d == "reject":
                return {"status": "stopped", "ran": ran, "at": name}
        ran.append(name)
    return {"status": "done", "ran": ran, "at": None}
""",
        cases=[
            case([['look_up_order', False], ['issue_refund', True], ['email_customer', False]], {}, expected={'status': 'paused', 'ran': ['look_up_order'], 'at': 'issue_refund'}, sample=True),
            case([['look_up_order', False], ['issue_refund', True], ['email_customer', False]], {'issue_refund': 'approve'}, expected={'status': 'done', 'ran': ['look_up_order', 'issue_refund', 'email_customer'], 'at': None}),
            case([['a', True]], {'a': 'reject'}, expected={'status': 'stopped', 'ran': [], 'at': 'a'}),
            case([], {}, expected={'status': 'done', 'ran': [], 'at': None}),
        ],
        guided="""def approval_run(steps, decisions):
    # Replace every ___ with real code, then run the tests.

    ran = []
    for name, risky in steps:
        if risky:
            d = decisions.get(name)
            # Step 1: no decision yet: pause here.
            if d is None:
                return {"status": "paused", "ran": ran, "at": name}
            # Step 2: a person said no: stop.
            if ___:
                return {"status": "stopped", "ran": ran, "at": name}
        ran.append(name)
    return {"status": ___, "ran": ran, "at": None}
""",
        fills=['d == "reject"', '"done"'],
        concepts=[
            [
                'Returning early',
                '`return` inside a loop ends the function right there.',
                """for s in steps:
    if must_stop:
        return result""",
            ],
        ],
        byhand="look_up_order is safe: run it. issue_refund is risky and there's no decision: pause there. Run again with issue_refund approved and everything runs.",
        why='One walk through the steps.',
        gotchas=[
            [
                'Steps before the pause may run twice',
                'When LangGraph resumes, the node containing interrupt() runs again from its start. Keep side effects after the interrupt, or make them idempotent.',
            ],
            [
                "Show the person what they're approving",
                'Pass the action and its arguments to the interrupt, so the reviewer sees "refund $250 on A-1042", not just "approve?".',
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
        pattern='Buffers and end markers',
        text='One walk through the chunks.',
        say='"I append deltas to buffers and finalise each tool call on its end event, then parse the arguments once."',
        classic=None,
    ),
    stack=stack('LangGraph: stream tokens as they arrive', """for chunk, metadata in graph.stream(inputs, stream_mode="messages"):
    print(chunk.content, end="", flush=True)"""),
    exercise=exercise(
        title='Put a Stream Back Together',
        topic='agents',
        difficulty='medium',
        fn='assemble_stream',
        prompt="""Streaming sends a reply in small pieces as it's generated. `chunks` is a list of events: `["text", piece]` adds to the visible reply; `["tool_start", name]` begins a tool call; `["tool_args", piece]` adds to the current tool call's arguments; `["tool_end", ""]` finishes it.

Return `[text, tool_calls]`: the full reply text, and a list of `[name, arguments]` for each finished tool call, in order.""",
        pattern='Accumulate pieces into buffers, and close a buffer when its end marker arrives.',
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
                ['tool_start', 'lookup_order'],
                ['tool_args', '{"order_id": '],
                ['tool_args', '"A-1042"}'],
                ['tool_end', ''],
            ], expected=['Let me check.', [['lookup_order', '{"order_id": "A-1042"}']]], sample=True),
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
            text += piece
        elif kind == "tool_start":
            name, args = piece, ""
        elif kind == "tool_args":
            # Step 1: arguments arrive in pieces.
            ___
        elif kind == "tool_end":
            # Step 2: the call is complete: save it and reset.
            calls.append(___)
            name, args = None, ""
    return [text, calls]
""",
        fills=['args += piece', '[name, args]'],
        concepts=[
            [
                'Adding to a string',
                '`+=` appends text.',
                """s = 'Let me '
s += 'check.'""",
            ],
            [
                'Tuple-style unpacking in a loop',
                'Each event is a pair, so name both parts.',
                """for kind, piece in chunks:
    ...""",
            ],
        ],
        byhand='Two text pieces make "Let me check.". tool_start opens lookup_order; two argument pieces build {"order_id": "A-1042"}; tool_end saves it.',
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
