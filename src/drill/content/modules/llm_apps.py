"""Building with LLMs: Prompts, parsing replies, batching and retries, with LangChain and Databricks model endpoints."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('llm-apps', 'Building with LLMs', 'Prompts, parsing replies, batching and retries, with LangChain and Databricks model endpoints.')

lesson(MODULE, 'fill_template',
    title='Prompts are templates',
    learn=[
        "Real prompts are built from templates with placeholders: instructions, the user's question, retrieved documents, examples.",
        'Prompts often contain JSON or code with curly braces of their own, so naive formatting breaks. Replace only the placeholders you mean to replace.',
    ],
    example=example('Why str.format breaks', """template = 'Reply as JSON like {"ok": true}. Question: {q}'
template.format(q='hi')   # KeyError: '"ok"'"""),
    check=question(
        'Your prompt contains an example `{"answer": "..."}` and a placeholder `{question}`. What\'s the safe way to fill it?',
        [
            '`template.format(question=q)`',
            'Replace exactly `{question}` and nothing else',
            'Remove all braces first',
        ],
        answer=1,
        why='`format` treats every `{...}` as a placeholder and fails on the JSON. Replacing only the placeholders you own leaves the example untouched.',
    ),
    angle=angle(
        pattern='String replacement',
        text='One replace per value you were given. The point is correctness: only touch what you own. Matching opening and closing markers properly is the idea behind Valid Parentheses.',
        say='"I loop over the values I was given and replace exactly those placeholders, so any other braces in the text survive."',
        classic='valid_parentheses',
    ),
    stack=stack('LangChain: literal braces are doubled', """from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", 'Reply as JSON like {{"ok": true}}'),
    ("human", "{question}"),
])"""),
    exercise=exercise(
        title='Fill a Prompt Template',
        topic='prompts',
        difficulty='easy',
        fn='fill_template',
        prompt="""You get a prompt `template` with placeholders like `{name}`, and a dict `values` such as `{"name": "Ana"}`. Replace each placeholder whose name is in `values` with its value. Leave everything else exactly as it is, including other curly braces.

Prompts often contain example JSON like `{"a": 1}`, and that must survive untouched.""",
        pattern='Only replace what you were asked to replace. Loop over the values, not over the braces in the text.',
        target='one replace per value',
        realworld="Building prompts from templates. Python's `str.format` crashes on prompts that contain JSON examples, which is a classic bug.",
        starter="""def fill_template(template, values):
    # your code here
    pass
""",
        solution="""def fill_template(template, values):
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template
""",
        cases=[
            case('Hi {name}!', {'name': 'Ana'}, expected='Hi Ana!', sample=True),
            case('Return JSON like {"a": 1} about {topic}', {'topic': 'cats'}, expected='Return JSON like {"a": 1} about cats'),
            case('{x} and {x}', {'x': '1'}, expected='1 and 1'),
            case('No placeholders', {}, expected='No placeholders'),
            case('{missing} stays', {'other': 'y'}, expected='{missing} stays'),
        ],
        guided="""def fill_template(template, values):
    # Replace every ___ with real code, then run the tests.

    # Step 1: go through each key and value you were given.
    for key, value in values.___():
        # Step 2: build the placeholder text, like {name}.
        placeholder = "{" + ___ + "}"
        # Step 3: swap it for the value. replace returns a NEW string.
        template = template.replace(___, ___)

    return template
""",
        concepts=[
            [
                'str.replace',
                'Returns a new string with every copy of one piece of text swapped for another. Strings never change in place.',
                """s = 'hi NAME'
s = s.replace('NAME', 'Ana')   # 'hi Ana'""",
            ],
            [
                'Looping over a dict',
                '.items() gives you each key and value together.',
                """for key, value in {'a': '1'}.items():
    print(key, value)""",
            ],
            [
                'Building a string',
                "+ joins strings, so '{' + key + '}' builds the exact placeholder text.",
                """key = 'name'
'{' + key + '}'   # '{name}'""",
            ],
        ],
        byhand='Template "Hi {name}!" with values {"name": "Ana"}. There\'s one value, name. Its placeholder is the text {name}. Swap that for Ana and you get "Hi Ana!". Any brace you weren\'t given a value for, you never touch.',
        why="One replace for each value you're given. Templates are short, so this is instant.",
        gotchas=[
            [
                "str.format and JSON don't mix",
                '"Reply like {\\"a\\": 1} about {topic}".format(topic=\'x\') crashes with KeyError, because format treats every brace as a placeholder. LangChain prompt templates have the same trap: you double the braces, {{ }}, to keep them.',
            ],
            [
                'User input inside prompts',
                'If a user\'s text goes into a template, it can contain instructions like "ignore the above". That\'s prompt injection. Keep user text clearly marked as data.',
            ],
        ],
    ),
)

lesson(MODULE, 'resolve_prompt',
    title='The prompt registry',
    learn=[
        'Changing one word in a prompt can change every answer, so treat prompts like code. The **MLflow Prompt Registry** stores them the way the model registry stores models: each save makes a new numbered **version**, and versions never change.',
        'Your app loads an **alias** like `production`, not a number. Shipping or rolling back a prompt means moving the alias: no code change, no redeploy. On Databricks, prompts live in Unity Catalog, with the same three-part names and permissions as tables and models.',
    ],
    example=example('Versions and an alias', """main.support.answer
  v1  Q: {{question}}
  v2  Use the context. {{context}} Q: {{question}}   ← production
  v3  Cite sources. {{context}} Q: {{question}}

load_prompt("prompts:/main.support.answer@production")  → v2"""),
    check=question(
        "Version 3 of a prompt made answers worse in production. What's the fastest safe fix?",
        [
            'Edit version 3 back to the old wording',
            'Point the production alias back at version 2',
            'Paste the old prompt into the code and redeploy',
        ],
        answer=1,
        why='Versions never change, so version 2 is exactly what ran before. Moving the alias is instant and leaves a record.',
    ),
    angle=angle(
        pattern='Parse, then look up',
        text='Split the address into a name and a version or alias, then a few dict lookups. Interviewers like hearing about settings you can change without a deploy.',
        say='"Prompts are versioned and never edited in place. The app loads by alias, so promoting or rolling back is moving a pointer, not shipping code."',
        classic=None,
    ),
    stack=stack('MLflow Prompt Registry in Unity Catalog', """import mlflow

p = mlflow.genai.register_prompt(
    name="main.support.answer",
    template="Use the context. {{context}} Q: {{question}}",
    commit_message="Ground answers in retrieved context",
)
mlflow.genai.set_prompt_alias("main.support.answer", alias="production", version=p.version)

prompt = mlflow.genai.load_prompt("prompts:/main.support.answer@production")
text = prompt.format(context=docs, question=q)

# LangChain templates use single braces:
lc_prompt = ChatPromptTemplate.from_template(prompt.to_single_brace_format())"""),
    exercise=exercise(
        title='Load a Prompt by Alias',
        topic='llm-apps',
        difficulty='medium',
        fn='resolve_prompt',
        prompt="""A prompt registry keeps every version of each prompt. `registry` maps a prompt name to `{"versions": {"1": template, ...}, "aliases": {"production": 2, ...}}`.

Apps load prompts by address, in one of two forms:
- `prompts:/<name>/<version>`, like `prompts:/main.support.answer/2`
- `prompts:/<name>@<alias>`, like `prompts:/main.support.answer@production`. The alias `latest` means the highest version number.

Return `[version, template]` with the version as a number, or `None` if the address doesn't start with `prompts:/`, or the name, version or alias doesn't exist.""",
        pattern='Parse the address into its parts, then a couple of dict lookups.',
        target='one pass over the address, then lookups',
        realworld='This is how `mlflow.genai.load_prompt("prompts:/main.support.answer@production")` works. Saved versions never change, so moving the `production` alias is how you ship or roll back a prompt without redeploying the app.',
        starter="""def resolve_prompt(registry, uri):
    # your code here
    pass
""",
        solution="""def resolve_prompt(registry, uri):
    prefix = "prompts:/"
    if not uri.startswith(prefix):
        return None
    rest = uri[len(prefix):]
    if "@" in rest:
        name, alias = rest.split("@", 1)
        entry = registry.get(name)
        if entry is None:
            return None
        if alias == "latest":
            version = max(int(v) for v in entry["versions"])
        elif alias in entry["aliases"]:
            version = entry["aliases"][alias]
        else:
            return None
    elif "/" in rest:
        name, v = rest.split("/", 1)
        entry = registry.get(name)
        if entry is None or not v.isdigit():
            return None
        version = int(v)
    else:
        return None
    template = entry["versions"].get(str(version))
    if template is None:
        return None
    return [version, template]
""",
        cases=[
            case({
                'main.support.answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Use the context. {{context}} Q: {{question}}',
                        '10': 'Cite sources. {{context}} Q: {{question}}',
                    },
                    'aliases': {'production': 2},
                },
            }, 'prompts:/main.support.answer@production', expected=[2, 'Use the context. {{context}} Q: {{question}}'], sample=True),
            case({
                'main.support.answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Use the context. {{context}} Q: {{question}}',
                        '10': 'Cite sources. {{context}} Q: {{question}}',
                    },
                    'aliases': {'production': 2},
                },
            }, 'prompts:/main.support.answer/10', expected=[10, 'Cite sources. {{context}} Q: {{question}}']),
            case({
                'main.support.answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Use the context. {{context}} Q: {{question}}',
                        '10': 'Cite sources. {{context}} Q: {{question}}',
                    },
                    'aliases': {'production': 2},
                },
            }, 'prompts:/main.support.answer@latest', expected=[10, 'Cite sources. {{context}} Q: {{question}}']),
            case({
                'main.support.answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Use the context. {{context}} Q: {{question}}',
                        '10': 'Cite sources. {{context}} Q: {{question}}',
                    },
                    'aliases': {'production': 2},
                },
            }, 'prompts:/main.support.answer@staging', expected=None),
            case({
                'main.support.answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Use the context. {{context}} Q: {{question}}',
                        '10': 'Cite sources. {{context}} Q: {{question}}',
                    },
                    'aliases': {'production': 2},
                },
            }, 'prompts:/main.support.answer/7', expected=None),
            case({
                'main.support.answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Use the context. {{context}} Q: {{question}}',
                        '10': 'Cite sources. {{context}} Q: {{question}}',
                    },
                    'aliases': {'production': 2},
                },
            }, 'prompts:/main.support.other@production', expected=None),
            case({
                'main.support.answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Use the context. {{context}} Q: {{question}}',
                        '10': 'Cite sources. {{context}} Q: {{question}}',
                    },
                    'aliases': {'production': 2},
                },
            }, 'runs:/abc123/model', expected=None),
        ],
        guided="""def resolve_prompt(registry, uri):
    # Replace every ___ with real code, then run the tests.

    prefix = "prompts:/"
    if not uri.startswith(prefix):
        return None
    rest = uri[len(prefix):]
    if "@" in rest:
        # Step 1: split once into the name and the alias.
        name, alias = ___
        entry = registry.get(name)
        if entry is None:
            return None
        if alias == "latest":
            # Step 2: the highest version, compared as numbers.
            version = ___
        elif alias in entry["aliases"]:
            version = ___
        else:
            return None
    elif "/" in rest:
        name, v = rest.split("/", 1)
        entry = registry.get(name)
        if entry is None or not v.isdigit():
            return None
        version = int(v)
    else:
        return None
    # Step 3: version keys are strings; return None if it's missing.
    template = ___
    if template is None:
        return None
    return [version, template]
""",
        fills=[
            'rest.split("@", 1)',
            'max(int(v) for v in entry["versions"])',
            'entry["aliases"][alias]',
            'entry["versions"].get(str(version))',
        ],
        concepts=[
            [
                'split with a limit',
                'Split at the first separator only.',
                '"a@b@c".split("@", 1)   # [\'a\', \'b@c\']',
            ],
            [
                'max over converted values',
                'Convert each one as you go, then take the biggest.',
                'max(int(v) for v in ["2", "10"])   # 10',
            ],
        ],
        byhand='Strip prompts:/ and split at @: the name is main.support.answer, the alias is production. The alias points at 2. Look up "2" in versions: found, so return [2, its template].',
        why='One pass over the address, then a few dict lookups.',
        gotchas=[
            [
                'Compare versions as numbers',
                'As text, "9" sorts after "10". Convert version strings to ints before picking the latest.',
            ],
            [
                "Don't ship @latest",
                '`latest` changes whenever anyone saves a version. Use it in notebooks; deployed agents load a named alias like `production`.',
            ],
        ],
    ),
)

lesson(MODULE, 'extract_code_block',
    title='Parsing what the model says',
    learn=[
        'Even when you ask for "JSON only", models often wrap the answer in chatter or a markdown code fence.',
        "Parse defensively: find the structure you expect, and have a fallback when it isn't there. Where the API supports structured output, use it, but still validate.",
    ],
    example=example('A typical reply', 'reply = \'Sure! ```json\\n{"a": 1}\\n``` Hope that helps\'\n# you want: \'{"a": 1}\''),
    check=question(
        'The model sometimes returns JSON inside a ```json fence and sometimes plain. What should your code do?',
        [
            "Fail when there's no fence, so you notice",
            'Extract from the fence if present, otherwise use the whole reply',
            'Ask the model again every time',
        ],
        answer=1,
        why='Handle both shapes and validate after. Failing on the common plain case would break a working feature.',
    ),
    angle=angle(
        pattern='Find markers, then slice',
        text="`find` reads the text once. What interviewers look for is handling the case where the marker isn't there, not just the happy path.",
        say='"I find the fence, slice between the markers, and fall back to the whole trimmed reply when there\'s no fence."',
        classic=None,
    ),
    stack=stack('LangChain: ask for structured output instead', """from pydantic import BaseModel
from databricks_langchain import ChatDatabricks

class Ticket(BaseModel):
    category: str
    urgent: bool

llm = ChatDatabricks(endpoint=ENDPOINT).with_structured_output(Ticket)"""),
    exercise=exercise(
        title='Pull Code Out of a Reply',
        topic='prompts',
        difficulty='easy',
        fn='extract_code_block',
        prompt="""You asked a model for JSON, but it replied with chatter around it, like `Sure! ```json {...} ``` Hope that helps`. Given the `reply` string, return the text inside the first fenced block (between the line that opens with three backticks and the next three backticks), with spaces and newlines trimmed from both ends.

The opening fence may have a word after it, like `json` or `python`. If there is no fence at all, return the whole reply, trimmed.""",
        pattern="Find the markers, then slice between them. Always have a fallback for when the markers aren't there.",
        target='read the reply once',
        realworld='Parsing model output. Models wrap answers in markdown fences even when you ask them not to.',
        starter="""def extract_code_block(reply):
    # your code here
    pass
""",
        solution='def extract_code_block(reply):\n    start = reply.find("```")\n    if start == -1:\n        return reply.strip()\n    line_end = reply.find("\\n", start)\n    end = reply.find("```", line_end)\n    return reply[line_end + 1:end].strip()\n',
        cases=[
            case("""Sure!
```json
{"a": 1}
```
Hope that helps""", expected='{"a": 1}', sample=True),
            case('{"a": 1}', expected='{"a": 1}'),
            case("""   plain answer  
""", expected='plain answer'),
            case("""```
x = 1
```""", expected='x = 1'),
            case("""```python
print(1)
```
and also
```
second
```""", expected='print(1)'),
        ],
        guided='def extract_code_block(reply):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: where does the first fence start? (-1 means there isn\'t one)\n    start = reply.find("```")\n    if start == ___:\n        return reply.___()\n\n    # Step 2: skip the rest of the fence line (it may say json or python).\n    line_end = reply.find("\\n", ___)\n\n    # Step 3: find the closing fence after that line.\n    end = reply.find("```", ___)\n\n    # Step 4: slice out what\'s between, and trim it.\n    return reply[___:___].strip()\n',
        concepts=[
            [
                'str.find',
                "Returns the position of some text, or -1 if it isn't there. A second number says where to start looking.",
                """s = 'a```b```'
s.find('```')      # 1
s.find('```', 2)   # 5""",
            ],
            ['str.strip', 'Removes spaces and newlines from both ends.', "'  hi\\n'.strip()   # 'hi'"],
            [
                'Slicing a string',
                's[a:b] works on strings the same way it does on lists.',
                "'hello'[1:4]   # 'ell'",
            ],
        ],
        byhand='Reply: Sure! then a fence line ```json, then {"a": 1}, then a closing ```. Find the first fence. Skip to the end of that line, so the word json isn\'t included. Find the next fence after that. Everything in between is your answer.',
        why='find reads through the reply once or twice. Fast for any reply length.',
        gotchas=[
            [
                'Calling json.loads on the raw reply',
                'It works in testing, then breaks the first time the model says "Sure! Here\'s your JSON". Strip the fences first, and wrap parsing in try/except.',
            ],
            [
                "Better: don't parse at all",
                'Most APIs now have structured output or tool calling, where the model must return JSON that fits a schema. Use that when you can, and keep this as the fallback.',
            ],
        ],
    ),
)

lesson(MODULE, 'batch_items',
    title='Batching API calls',
    learn=[
        'APIs limit how much you can send per request, and every request has overhead. Sending items in **batches** is faster and often cheaper.',
        'The last batch is usually smaller, and losing it is a classic bug: a thousand documents indexed, one silently missing.',
    ],
    example=example('Slicing in steps', """items = list(range(7))
[items[i:i + 3] for i in range(0, len(items), 3)]
# [[0, 1, 2], [3, 4, 5], [6]]"""),
    check=question(
        'You have 1,001 texts and a batch size of 100. How many requests do you send?',
        ['10', '11', '100'],
        answer=1,
        why='Ten full batches plus one batch with the last text.',
    ),
    angle=angle(
        pattern='Stepping through a list',
        text="`range(0, len(items), size)` visits each starting point once, and every item lands in exactly one slice, so it's one walk through the list.",
        say='"I step through the list in jumps of the batch size and slice each batch; the last slice is just shorter, so nothing is dropped."',
        classic=None,
    ),
    stack=stack('Databricks: batch inference over a table with ai_query', """SELECT ticket_id,
       ai_query('databricks-gte-large-en', text) AS embedding
FROM main.support.tickets"""),
    exercise=exercise(
        title='Batch Requests',
        topic='api-calls',
        difficulty='easy',
        fn='batch',
        prompt="""Embedding APIs take a limited number of texts per request. You get a list `items` and a number `size`. Split the list into batches of `size` items, in order, and return a list of batches.

The last batch can be smaller. An empty list gives an empty list of batches.""",
        pattern='Walk through the list in jumps of `size`, cutting out one slice each time.',
        target='walk through the list once',
        realworld='Sending texts to an embedding API, or rows to a database, a few hundred at a time.',
        starter="""def batch(items, size):
    # your code here
    pass
""",
        solution="""def batch(items, size):
    out = []
    for start in range(0, len(items), size):
        out.append(items[start:start + size])
    return out
""",
        cases=[
            case([1, 2, 3, 4, 5], 2, expected=[[1, 2], [3, 4], [5]], sample=True),
            case([], 3, expected=[]),
            case([1, 2], 5, expected=[[1, 2]]),
            case(['a', 'b', 'c'], 1, expected=[['a'], ['b'], ['c']]),
            case(['q1', 'q2', 'q3', 'q4'], 2, expected=[['q1', 'q2'], ['q3', 'q4']]),
        ],
        guided="""def batch(items, size):
    # Replace every ___ with real code, then run the tests.

    # Step 1: a list to collect the batches.
    out = []

    # Step 2: start positions 0, size, 2*size, ... up to the end of items.
    for start in range(___, ___, ___):
        # Step 3: cut out one batch with a slice and add it.
        out.append(items[___:___])

    return out
""",
        concepts=[
            [
                'Slicing',
                'items[a:b] gives the items from position a up to, but not including, b. Going past the end is safe: you just get fewer items.',
                """letters = ['a', 'b', 'c']
letters[0:2]   # ['a', 'b']
letters[2:10]  # ['c'], no error""",
            ],
            [
                'range with a step',
                'range(start, stop, step) counts in jumps.',
                'list(range(0, 7, 3))   # [0, 3, 6]',
            ],
        ],
        byhand='With [1, 2, 3, 4, 5] and size 2: start at 0 and take 2, giving [1, 2]. Jump to 2 and take [3, 4]. Jump to 4 and take [5]. Jumping to 6 is past the end, so stop.',
        why='Each item is copied into exactly one batch, so the work grows in step with the list.',
        gotchas=[
            [
                'Forgetting the last batch',
                'A loop that only emits full batches silently drops the leftovers. With 1,001 documents and batches of 100, one document never gets indexed.',
            ],
            ['Batch size 0', 'range(0, n, 0) raises an error. In real code, check the size before looping.'],
        ],
    ),
)

lesson(MODULE, 'backoff_delays',
    title='Retries and backoff',
    learn=[
        "APIs fail for temporary reasons: rate limits, timeouts, overload. Good clients **retry**, waiting longer each time (**exponential backoff**), with a **cap** so waits don't grow forever.",
        'Only retry errors that can fix themselves. A bad request or wrong key fails the same way every time.',
    ],
    example=example('Doubling with a cap', """wait = 1
for attempt in range(5):
    sleep(min(wait, 30))
    wait *= 2"""),
    check=question(
        'Which error is worth retrying?',
        ['401 Unauthorized', '429 Too Many Requests', '400 Bad Request'],
        answer=1,
        why='A 429 means "slow down"; waiting fixes it. A wrong key or a malformed request will fail again however long you wait.',
    ),
    angle=angle(
        pattern='Each value from the previous one',
        text='Every wait is worked out from the one before: double it, then cap it. That "build the next answer from the last one" idea is the heart of Climbing Stairs. One step per retry.',
        say='"I keep one running value, double it each retry and cap it with min, so I never store more than I need."',
        classic='climbing_stairs',
    ),
    stack=stack('LangChain: retries with growing waits', """llm = ChatDatabricks(endpoint=ENDPOINT).with_retry(
    stop_after_attempt=4,
    wait_exponential_jitter=True,
)
# A 429 from a Databricks endpoint usually means an AI Gateway rate limit."""),
    exercise=exercise(
        title='Retry Wait Times',
        topic='api-calls',
        difficulty='easy',
        fn='backoff_delays',
        prompt="""When an API says "too many requests", good code waits and tries again, waiting longer each time. Return a list with `retries` wait times. The first wait is `base` seconds and each next wait is double the one before, but no wait may be longer than `cap`.

For 4 retries, base 1 and cap 100 that's `[1, 2, 4, 8]`. With cap 5 and 5 retries it's `[1, 2, 4, 5, 5]`.""",
        pattern='Keep a running value, double it each round, and clip it with `min`.',
        target='one step per retry',
        realworld='Every call to an LLM API needs this. Without a cap, a few failures in a row make you wait for hours.',
        starter="""def backoff_delays(retries, base, cap):
    # your code here
    pass
""",
        solution="""def backoff_delays(retries, base, cap):
    delays = []
    wait = base
    for _ in range(retries):
        delays.append(min(wait, cap))
        wait = wait * 2
    return delays
""",
        cases=[
            case(4, 1, 100, expected=[1, 2, 4, 8], sample=True),
            case(5, 1, 5, expected=[1, 2, 4, 5, 5]),
            case(0, 1, 10, expected=[]),
            case(3, 0.5, 10, expected=[0.5, 1, 2]),
            case(2, 3, 2, expected=[2, 2]),
        ],
        guided="""def backoff_delays(retries, base, cap):
    # Replace every ___ with real code, then run the tests.

    delays = []
    # Step 1: the first wait is base.
    wait = ___

    # Step 2: once per retry...
    for _ in range(___):
        # ...record the wait, but never more than cap
        delays.append(min(___, ___))
        # ...and double it for next time.
        wait = ___

    return delays
""",
        concepts=[
            [
                'min',
                'Gives back the smaller of its arguments. min(x, cap) is the usual way to say "x, but never more than cap".',
                """min(8, 5)   # 5
min(3, 5)   # 3""",
            ],
            [
                'Loop a fixed number of times',
                "When you don't need the counter, name it _.",
                """for _ in range(3):
    print('again')""",
            ],
        ],
        byhand='base 1, cap 5, 5 retries. The waits go 1, then 2, then 4. Doubling gives 8, but the cap is 5, so write 5. Doubling again gives 16, still capped at 5. The answer is [1, 2, 4, 5, 5].',
        why='One small step per retry.',
        gotchas=[
            [
                "Retrying errors that won't fix themselves",
                'Retry on "too many requests" (429), timeouts and server errors (5xx). Don\'t retry "bad request" (400) or "unauthorized" (401). They fail the same way every time.',
            ],
            [
                'Everyone retrying at the same moment',
                'If a thousand clients all wait exactly 2 seconds, they hit the server together again. Real code adds a little randomness, called jitter.',
            ],
            [
                'Use a library',
                "In real projects, the tenacity library or your SDK's built-in max_retries option does this for you. Knowing how it works helps you set it well.",
            ],
        ],
    ),
)

lesson(MODULE, 'parse_labels',
    title='Testing AI code',
    learn=[
        'Model calls are slow, cost money and give different answers each time, which makes tests flaky.',
        "Keep the model call thin and separate. Test the logic around it (parsing, routing, error handling) with **fake** replies, and test the model's quality with evals.",
    ],
    example=example('Fake the model, test the logic', """fake replies: ["Billing.", " refund ", "I think it's billing"]
expected:     ["billing",  "refund",   "unknown"]"""),
    check=question(
        "Your unit tests call the real model and fail randomly. What's the fix?",
        ['Retry failing tests', 'Use a fake model with scripted replies in unit tests', 'Delete the tests'],
        answer=1,
        why='Unit tests should be fast and the same every run.',
    ),
    angle=angle(
        pattern='Pure functions are testable',
        text='One walk through the replies. Designing for testability is a big part of senior interviews.',
        say='"I separate the model call from the logic, unit-test the logic with a scripted fake model, and cover quality with evals."',
        classic=None,
    ),
    stack=stack('LangChain: a fake chat model for tests', 'from langchain_core.language_models.fake_chat_models import GenericFakeChatModel\nfrom langchain_core.messages import AIMessage\n\nfake = GenericFakeChatModel(messages=iter([AIMessage(content="Billing.")]))\nassert classify("Why was I charged twice?", llm=fake) == "billing"'),
    exercise=exercise(
        title='Test the Logic, Fake the Model',
        topic='testing',
        difficulty='easy',
        fn='parse_labels',
        prompt="""Good code keeps the model call separate from the logic around it, so the logic can be tested with canned replies instead of real (slow, random, costly) model calls.

Here, `replies` are what a classifier model returned. Clean each one: lowercase, trim spaces, and remove a trailing `.`. If the result is in `allowed`, keep it; otherwise use `"unknown"`. Return the list of labels.""",
        pattern='Make the messy outside world an input, so the logic is a pure function you can test.',
        target='one walk through the replies',
        realworld="LangChain ships `GenericFakeChatModel` for this: it returns scripted replies, so unit tests run fast, free and the same every time. Test the parsing, routing and error handling with fakes; test the model's quality with evals.",
        starter="""def parse_labels(replies, allowed):
    # your code here
    pass
""",
        solution="""def parse_labels(replies, allowed):
    out = []
    for r in replies:
        label = r.strip().lower()
        if label.endswith("."):
            label = label[:-1]
        out.append(label if label in allowed else "unknown")
    return out
""",
        cases=[
            case(['Billing.', ' refund ', "I think it's billing", 'SHIPPING'], ['billing', 'refund', 'shipping'], expected=['billing', 'refund', 'unknown', 'shipping'], sample=True),
            case([], ['a'], expected=[]),
            case(['.'], ['a'], expected=['unknown']),
            case(['a.', 'b'], ['a'], expected=['a', 'unknown']),
        ],
        guided="""def parse_labels(replies, allowed):
    # Replace every ___ with real code, then run the tests.

    out = []
    for r in replies:
        # Step 1: clean it up.
        label = r.strip().___()
        if label.endswith("."):
            label = label[:-1]
        # Step 2: anything unexpected becomes "unknown", never a crash.
        out.append(___)
    return out
""",
        fills=['lower', 'label if label in allowed else "unknown"'],
        concepts=[
            [
                'strip and lower',
                'Trim spaces and lowercase in one line.',
                "' Billing '.strip().lower()   # 'billing'",
            ],
            ['endswith', 'Checks how a string ends.', "'billing.'.endswith('.')   # True"],
        ],
        byhand='"Billing." becomes billing: allowed. " refund " becomes refund. "I think it\'s billing" isn\'t a label: unknown. "SHIPPING" becomes shipping.',
        why='One walk through the replies.',
        gotchas=[
            [
                'Fakes test code, evals test quality',
                'A fake model tells you the parser handles "Billing."; only an eval tells you the model picks billing for the right tickets.',
            ],
            [
                'Pin the weird cases',
                'Every strange reply you see in production is a free test case. Add it to the scripted fakes.',
            ],
        ],
    ),
)
