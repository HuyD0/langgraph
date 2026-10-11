"""Building with LLMs: Prompts, parsing replies, batching and retries, with LangChain and Databricks model endpoints."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('llm-apps', 'Building with LLMs', 'Prompts, parsing replies, batching and retries, with LangChain and Databricks model endpoints.')

lesson(MODULE, 'fill_template',
    title='Prompts are templates',
    learn=[
        "Real prompts are built from templates with placeholders: instructions, the user's question, retrieved documents, examples.",
        'Prompts often contain JSON (a common text format for data, written with curly braces, like `{"ok": true}`) or code with curly braces of their own, so filling them with str.format (the built-in Python way to fill placeholders) breaks. Replace only the placeholders you mean to replace.',
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
        text='One replace per value you were given. The point is correctness: only touch what you own. Valid Parentheses, linked below, is a related brace puzzle: it checks that every opening brace has a closing one.',
        say='"I loop over the values I was given and replace exactly those placeholders, so any other braces in the text survive."',
        classic='valid_parentheses',
    ),
    stack=stack('LangChain (a Python library for building LLM apps): braces you want to keep are doubled', """from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", 'Reply as JSON like {{"ok": true}}'),
    ("human", "{question}"),
])"""),
    exercise=exercise(
        title='Fill a Prompt Template',
        topic='prompts',
        difficulty='easy',
        fn='fill_template',
        prompt="""Your function gets two things:

- `template`: the prompt text, with placeholders in it. A placeholder is a name in curly braces, like `{user}`.
- `values`: a dict with the text for each placeholder, like `{"user": "Ana"}`.

For each name in `values`, replace every copy of its placeholder with its value. Leave everything else exactly as it is. That includes placeholders you have no value for, and other curly braces, such as example JSON (a text format for data) like `{"a": 1}`. Return the filled-in text.""",
        pattern='Only replace what you were asked to replace. Loop over the values, not over the braces in the text.',
        target='one replace for each value',
        realworld="Building prompts from templates. Python's `str.format` crashes on prompts that contain JSON examples, which is a classic bug.",
        starter="""def fill_template(template, values):
    # your code here
    pass
""",
        solution="""def fill_template(template, values):
    for name, value in values.items():
        placeholder = "{" + name + "}"
        template = template.replace(placeholder, value)
    return template
""",
        cases=[
            case('Hi {user}!', {'user': 'Ana'}, expected='Hi Ana!', sample=True),
            case('Return JSON like {"a": 1} about {topic}', {'topic': 'cats'}, expected='Return JSON like {"a": 1} about cats'),
            case('{x} and {x}', {'x': '1'}, expected='1 and 1'),
            case('No placeholders', {}, expected='No placeholders'),
            case('{missing} stays', {'other': 'y'}, expected='{missing} stays'),
        ],
        guided="""def fill_template(template, values):
    # Replace every ___ with real code, then run the tests.

    # Step 1: go through each name and value you were given.
    for name, value in values.items():
        # Step 2: put { and } around the name, like {user}.
        placeholder = "{" + ___ + "}"
        # Step 3: swap the placeholder for the value.
        # replace gives back a NEW string, so save it.
        template = ___

    return template
""",
        fills=['name', 'template.replace(placeholder, value)'],
        concepts=[
            [
                'str.replace',
                'Gives back a new string with every copy of one piece of text swapped for another. The old string never changes, so save the result.',
                """s = 'hi NAME'
s = s.replace('NAME', 'Ana')
s   # 'hi Ana'""",
            ],
            [
                'Looping over a dict',
                '.items() gives you each key and its value together.',
                """for k, v in {'apple': 3}.items():
    print(k, v)   # apple 3""",
            ],
            [
                'Joining strings with +',
                '+ glues strings together, so you can build the exact text you are looking for.',
                """word = 'cat'
'<' + word + '>'   # '<cat>'""",
            ],
        ],
        byhand='The template is "Hi {user}!". values has one entry: user, with the value Ana. Its placeholder is {user}. Replace {user} with Ana. Return "Hi Ana!".',
        why="One replace for each value you're given. Templates are short, so this is instant.",
        gotchas=[
            [
                "str.format and JSON don't mix",
                "`'Reply like {\"a\": 1} about {topic}'.format(topic=\"x\")` crashes with KeyError, because format treats every brace as a placeholder. LangChain prompt templates have the same trap: you double the braces, {{ }}, to keep them.",
            ],
            [
                'User input inside prompts',
                'If a user\'s text goes into a template, it can contain instructions like "ignore the above". That\'s prompt injection. Keep user text clearly marked as data.',
            ],
        ],
    ),
)

# The registry most of the resolve_prompt cases look things up in.
_REGISTRY = {
    'answer': {
        'versions': {
            '1': 'Q: {{question}}',
            '2': 'Use the context. Q: {{question}}',
            '3': 'Cite sources. Q: {{question}}',
        },
        'aliases': {'production': '2', 'staging': '3'},
    },
    'main.support.summary': {
        'versions': {'1': 'Summarise: {{text}}'},
        'aliases': {'production': '1'},
    },
}

lesson(MODULE, 'resolve_prompt',
    title='The prompt registry',
    learn=[
        'Changing one word in a prompt can change every answer, so treat prompts like code. The **MLflow Prompt Registry** is a shared store for prompts, like the one MLflow keeps for models: each save makes a new numbered **version**, and versions never change.',
        'Your app loads an **alias** (a nickname like `production` that points at one version), not a number. Shipping or rolling back a prompt means moving the alias: no code change, no redeploy. On Databricks, prompts live in Unity Catalog, the catalog that holds your tables and models, with the same three-part names (like `main.support.answer`) and permissions.',
        'Watch the braces: MLflow writes placeholders with double braces, like `{{question}}`. That is the opposite of LangChain, where single braces are placeholders and doubled braces are kept as plain text. `prompt.to_single_brace_format()` converts an MLflow prompt for LangChain.',
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
        text='Split the address into a name and an alias, then a couple of dict lookups. Interviewers like hearing about settings you can change without a deploy.',
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

# LangChain uses single braces for placeholders, so convert:
lc_prompt = ChatPromptTemplate.from_template(prompt.to_single_brace_format())"""),
    exercise=exercise(
        title='Load a Prompt by Alias',
        topic='llm-apps',
        difficulty='medium',
        fn='resolve_prompt',
        prompt="""Your function gets two things:

- `registry`: a dict of saved prompts. Each key is a prompt name, like `"answer"`.
- `address`: which prompt to load, like `"prompts:/answer@production"`. After `prompts:/` comes the prompt name, then `@`, then an alias. An alias is a nickname for one version.

Each prompt has two dicts, `"versions"` and `"aliases"`. In `"versions"`, each key is a version number stored as text, like `"2"`, and its value is that version's prompt text. In `"aliases"`, each key is an alias and its value is a version number, like `{"production": "2"}`.

Return the text of the version the alias points to, unchanged, braces and all. If the name or the alias isn't in the registry, return `None`.""",
        pattern='Split the address into a name and an alias. Then look up the alias to get a version, and the version to get the template.',
        target='one split, then a few lookups',
        realworld='This is how `mlflow.genai.load_prompt("prompts:/main.support.answer@production")` works. Saved versions never change, so moving the `production` alias is how you ship or roll back a prompt without redeploying the app.',
        starter="""def resolve_prompt(registry, address):
    # your code here
    pass
""",
        solution="""def resolve_prompt(registry, address):
    rest = address.replace("prompts:/", "")
    name, alias = rest.split("@")
    prompt = registry.get(name)
    if prompt is None:
        return None
    version = prompt["aliases"].get(alias)
    if version is None:
        return None
    return prompt["versions"][version]
""",
        cases=[
            case({
                'answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Be brief. Q: {{question}}',
                    },
                    'aliases': {'production': '2'},
                },
            }, 'prompts:/answer@production', expected='Be brief. Q: {{question}}', sample=True),
            case(_REGISTRY, 'prompts:/answer@staging', expected='Cite sources. Q: {{question}}'),
            case(_REGISTRY, 'prompts:/main.support.summary@production', expected='Summarise: {{text}}'),
            case({
                'answer': {
                    'versions': {
                        '1': 'Q: {{question}}',
                        '2': 'Use the context. Q: {{question}}',
                    },
                    'aliases': {'production': '1'},
                },
            }, 'prompts:/answer@production', expected='Q: {{question}}'),
            case(_REGISTRY, 'prompts:/answer@beta', expected=None),
            case(_REGISTRY, 'prompts:/other@production', expected=None),
        ],
        guided="""def resolve_prompt(registry, address):
    # Replace every ___ with real code, then run the tests.

    # Step 1: drop "prompts:/", then split at the @.
    rest = address.replace("prompts:/", "")
    name, alias = ___

    # Step 2: find the prompt. None if the name is unknown.
    prompt = registry.get(name)
    if prompt is None:
        return None

    # Step 3: look up the alias in prompt["aliases"].
    # .get gives None if the alias isn't there.
    version = ___
    if version is None:
        return None

    # Step 4: look up that version in prompt["versions"].
    return ___
""",
        fills=[
            'rest.split("@")',
            'prompt["aliases"].get(alias)',
            'prompt["versions"][version]',
        ],
        concepts=[
            [
                'Removing text with replace',
                'Replacing some text with an empty string removes it.',
                """s = 'Dr. Ana'.replace('Dr. ', '')
s   # 'Ana'""",
            ],
            [
                'split into two names',
                'split cuts a string at a separator and gives back a list of the pieces. If there are exactly two pieces, you can catch them in two names at once.',
                """first, last = 'Ana-Lee'.split('-')
first   # 'Ana'
last    # 'Lee'""",
            ],
            [
                'dict.get',
                "d.get(key) gives the value, or None if the key isn't there. d[key] would crash instead.",
                """ages = {'ana': 30}
ages.get('ana')   # 30
ages.get('bob')   # None""",
            ],
            [
                'A dict inside a dict',
                'Chain the lookups: the first [ ] gets the inner dict, the second gets a value from it.',
                """pet = {'sizes': {'cat': 'small'}}
pet['sizes']['cat']   # 'small'""",
            ],
        ],
        byhand='The address is "prompts:/answer@production". Drop "prompts:/" to get "answer@production". Split at the @: the name is answer and the alias is production. The registry has a prompt called answer. Its aliases say production is version "2". Version "2" is "Be brief. Q: {{question}}". Return that.',
        why='One split, then a few dict lookups. Each lookup is instant.',
        gotchas=[
            [
                'Version numbers stored as text',
                'Here versions are stored as text, like "2". If you ever pick the newest one yourself, turn them into ints first: as text, "9" sorts after "10".',
            ],
            [
                "Don't ship @latest",
                'MLflow also has a `latest` alias, which moves whenever anyone saves a version. Use it in notebooks; deployed agents load a named alias like `production`.',
            ],
        ],
    ),
)

lesson(MODULE, 'extract_code_block',
    title='Parsing what the model says',
    learn=[
        'Even when you ask for "JSON only", models often wrap the answer in chatter or a markdown code fence (a line of three backticks above and below it).',
        "Parse defensively: find the structure you expect, and have a fallback when it isn't there. Where the API (the web address and rules your code uses to send requests to the model) supports structured output (a setting that makes the model reply in the exact JSON shape you ask for), use it, but still check what comes back.",
    ],
    example=example('A typical reply', 'reply = \'Sure!\\n```json\\n{"a": 1}\\n```\\nHope that helps\'\n# you want: \'{"a": 1}\''),
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
        pattern='Find fences, then slice',
        text="`find` reads the text once. What interviewers look for is handling the case where the fence isn't there, not just the happy path.",
        say='"I find the fences, slice between them, and fall back to the whole trimmed reply when there\'s no fence."',
        classic=None,
    ),
    stack=stack('LangChain: ask for structured output instead', """from pydantic import BaseModel
from databricks_langchain import ChatDatabricks
# ChatDatabricks: LangChain's link to a Databricks model endpoint
# (a model hosted on Databricks that your code sends requests to)

class Ticket(BaseModel):
    category: str
    urgent: bool

llm = ChatDatabricks(endpoint=ENDPOINT).with_structured_output(Ticket)"""),
    exercise=exercise(
        title='Pull Code Out of a Reply',
        topic='prompts',
        difficulty='easy',
        fn='extract_code_block',
        prompt="""`reply` is the text a model sent back. In the example below, `\\n` is a line break.

A fence is three backticks in a row. A backtick is the small slanted quote mark (on an iPhone, hold the ' key). The part you want sits between two fences.

The opening fence starts a line, and may have a word after it, like `json`. Skip that whole line. The text you want starts on the next line and stops at the next fence.

Return the text inside the first fenced block, with spaces and line breaks trimmed from both ends. If there is no fence at all, return the whole reply, trimmed.""",
        pattern='Find the fences, then slice the text between them. If there is no fence, fall back to the whole reply, trimmed.',
        target='read the reply once',
        realworld='Parsing model output. Models wrap answers in markdown fences even when you ask them not to.',
        starter="""def extract_code_block(reply):
    # your code here
    pass
""",
        solution='def extract_code_block(reply):\n    start = reply.find("```")\n    if start == -1:\n        return reply.strip()\n    line_end = reply.find("\\n", start)\n    end = reply.find("```", line_end)\n    return reply[line_end + 1:end].strip()\n',
        cases=[
            case('Sure!\n```python\nx = 1\n```\nDone.', expected='x = 1', sample=True),
            case('Sure!\n```json\n{"a": 1}\n```\nHope that helps', expected='{"a": 1}'),
            case('{"a": 1}', expected='{"a": 1}'),
            case('   plain answer  \n', expected='plain answer'),
            case('```\ny = 2\n```', expected='y = 2'),
            case('```python\nprint(1)\n```\nand also\n```\nsecond\n```', expected='print(1)'),
        ],
        guided='def extract_code_block(reply):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: find the first fence. -1 means there is none,\n    # so give back the whole reply, trimmed.\n    start = reply.find("```")\n    if start == -1:\n        return ___\n\n    # Step 2: skip to the end of the fence line\n    # (it may say python). The block starts after it.\n    line_end = reply.find("\\n", start)\n\n    # Step 3: find the closing fence, after that line.\n    end = reply.find("```", ___)\n\n    # Step 4: the block starts at line_end + 1 and stops\n    # just before end. Slice it, then trim.\n    return reply[___].strip()\n',
        fills=['reply.strip()', 'line_end', 'line_end + 1:end'],
        concepts=[
            [
                'str.find',
                "Gives the position of some text, or -1 if it isn't there. A second number says where to start looking.",
                """s = 'a-b-c'
s.find('-')      # 1
s.find('-', 2)   # 3
s.find('x')      # -1""",
            ],
            [
                'Line breaks',
                '`\\n` inside a string is one character: a line break. You can find it like any other text.',
                "'hi\\nthere'.find('\\n')   # 2",
            ],
            ['str.strip', 'Removes spaces and line breaks from both ends.', "'  hi\\n'.strip()   # 'hi'"],
            [
                'Slicing a string',
                '`s[start:stop]` gives the characters from the start position up to, but not including, the stop position.',
                "'hello'[1:4]   # 'ell'",
            ],
        ],
        byhand='Positions count from 0. "Sure!" and its line break fill positions 0 to 5, so the first fence starts at 6: start is 6. The fence line ends with python, and its line break is at 15: line_end is 15. The block starts just after that, at 16, with x = 1. The closing fence starts at 22: end is 22. reply[16:22] is "x = 1" plus a line break. Trim it and return "x = 1".',
        why='Each find picks up where the last one stopped, so you read the reply once.',
        gotchas=[
            [
                'Calling json.loads on the raw reply',
                'It works in testing, then breaks the first time the model says "Sure! Here\'s your JSON". Strip the fences first, and wrap parsing in try/except (code that catches the error so your program keeps going).',
            ],
            [
                "Better: don't parse at all",
                'Most APIs now have structured output, where the model must return JSON that fits a schema (a description of the exact fields and types you expect). Use that when you can, and keep this as the fallback.',
            ],
        ],
    ),
)

lesson(MODULE, 'batch_items',
    title='Batching API calls',
    learn=[
        'APIs limit how much you can send per request, and every request has **overhead**: a fixed delay before any work starts. Sending items in **batches** is faster and often cheaper.',
        'The last batch is usually smaller, and losing it is a classic bug: a thousand documents sent, one silently missing.',
    ],
    example=example('Slicing in steps', """items = [0, 1, 2, 3, 4, 5, 6]
batches = []
for start in range(0, 7, 3):
    group = items[start:start + 3]
    batches.append(group)
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
    stack=stack('Databricks: batch inference (a model run on every row) with ai_query', """-- Turn each ticket into an embedding (a list of numbers)
SELECT ticket_id,
       ai_query('databricks-gte-large-en', text) AS embedding
FROM main.support.tickets"""),
    exercise=exercise(
        title='Batch Requests',
        topic='api-calls',
        difficulty='easy',
        fn='batch',
        prompt="""Your function gets two things:

- `items`: the things to send, like `["a", "b", "c"]`.
- `size`: how many items fit in one request, like `2`.

Cut `items` into batches (small groups) of `size` items, keeping their order. Return the list of batches. The last batch holds whatever is left over, so it can be smaller. If `items` is empty, return an empty list.""",
        pattern='Walk through the list in jumps of `size`, cutting out one slice each time.',
        target='walk through the list once',
        realworld='Sending texts to an embedding API (a model that turns text into a list of numbers), or rows to a database, a few hundred at a time.',
        starter="""def batch(items, size):
    # your code here
    pass
""",
        solution="""def batch(items, size):
    batches = []
    for start in range(0, len(items), size):
        batches.append(items[start:start + size])
    return batches
""",
        cases=[
            case(['a', 'b', 'c', 'd', 'e'], 2, expected=[['a', 'b'], ['c', 'd'], ['e']], sample=True),
            case([], 3, expected=[]),
            case([1, 2], 5, expected=[[1, 2]]),
            case(['a', 'b', 'c'], 1, expected=[['a'], ['b'], ['c']]),
            case(['q1', 'q2', 'q3', 'q4'], 2, expected=[['q1', 'q2'], ['q3', 'q4']]),
            case([1, 2, 3, 4, 5, 6, 7], 3, expected=[[1, 2, 3], [4, 5, 6], [7]]),
        ],
        guided="""def batch(items, size):
    # Replace every ___ with real code, then run the tests.

    # Step 1: a list to collect the batches.
    batches = []

    # Step 2: start at 0 and jump by size each time,
    # until you reach the end of items.
    for start in range(0, len(items), ___):
        # Step 3: slice from start up to start + size,
        # and add that batch.
        batches.append(items[___])

    return batches
""",
        fills=['size', 'start:start + size'],
        concepts=[
            [
                'Slicing',
                '`items[start:stop]` gives the items from the start position up to, but not including, the stop position. Going past the end is safe: you just get fewer items.',
                """letters = ['a', 'b', 'c']
letters[0:2]   # ['a', 'b']
letters[2:10]  # ['c'], no error""",
            ],
            [
                'range with a step',
                '`range(start, stop, step)` counts from start in jumps of step, and stops before stop.',
                'list(range(0, 7, 3))   # [0, 3, 6]',
            ],
        ],
        byhand='Start at position 0 and take 2 items: ["a", "b"]. Jump to position 2 and take ["c", "d"]. Jump to position 4: only "e" is left, so that batch is ["e"]. Position 6 is past the end, so stop. Return [["a", "b"], ["c", "d"], ["e"]].',
        why='Each item is copied into exactly one batch, so the work grows in step with the list.',
        gotchas=[
            [
                'Forgetting the last batch',
                'A loop that only emits full batches silently drops the leftovers. With 1,001 documents and batches of 100, one document never gets sent.',
            ],
            ['Batch size 0', '`range(0, len(items), 0)` raises an error. In real code, check the size before looping.'],
        ],
    ),
)

lesson(MODULE, 'backoff_delays',
    title='Retries and backoff',
    learn=[
        "APIs fail for temporary reasons: rate limits (a cap on how many requests you may send per minute), timeouts, overload. Good clients **retry**, waiting longer each time (**exponential backoff**: each wait is double the one before), with a **cap** so waits don't grow forever.",
        'Only retry errors that can fix themselves. A bad request or wrong key fails the same way every time.',
    ],
    example=example('Doubling with a cap', """wait = 1
for attempt in range(5):
    sleep(min(wait, 5))
    wait = wait * 2
# waits: 1, 2, 4, 5, 5 (the cap of 5 kicks in)"""),
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
# This retries EVERY error by default, even a wrong key.
# Pass retry_if_exception_type=(...) to retry only some.
# A 429 from a Databricks endpoint usually means an AI Gateway
# rate limit (AI Gateway: the Databricks layer that sets limits
# on model endpoints)."""),
    exercise=exercise(
        title='Retry Wait Times',
        topic='api-calls',
        difficulty='easy',
        fn='backoff_delays',
        prompt="""When a call to a model fails, good code waits and tries again, and waits longer each time. Your function gets three things:

- `retries`: how many times to try again, like `5`.
- `base`: the starting wait, in seconds, like `1`.
- `cap`: the longest wait allowed, like `5`.

Return a list with one wait time for each retry. Start with `base`. Each next wait is double the one before. If a wait would be more than `cap`, use `cap` instead. This applies to the first wait too.""",
        pattern='Keep a running value, double it each round, and clip it with `min`.',
        target='one step per retry',
        realworld='Every call to an LLM API needs this. Without a cap, a dozen failures in a row (starting at 1 second) add up to over an hour of waiting.',
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
            case(5, 1, 5, expected=[1, 2, 4, 5, 5], sample=True),
            case(4, 1, 100, expected=[1, 2, 4, 8]),
            case(0, 1, 10, expected=[]),
            case(3, 0.5, 10, expected=[0.5, 1, 2]),
            case(2, 3, 2, expected=[2, 2]),
        ],
        guided="""def backoff_delays(retries, base, cap):
    # Replace every ___ with real code, then run the tests.

    delays = []
    # Step 1: the first wait is base.
    wait = base

    # Step 2: once for each retry...
    for _ in range(retries):
        # ...add the wait, but never more than cap,
        delays.append(___)
        # ...then double the wait for next time.
        wait = ___

    return delays
""",
        fills=['min(wait, cap)', 'wait * 2'],
        concepts=[
            [
                'min',
                'Gives back the smaller of its arguments. `min(wait, cap)` is the usual way to say "the wait, but never more than the cap".',
                """min(8, 5)   # 5
min(3, 5)   # 3""",
            ],
            [
                'Loop a fixed number of times',
                "`range(3)` runs the loop 3 times. When you don't need the counter, name it `_`.",
                """for _ in range(3):
    print('again')""",
            ],
        ],
        byhand='5 retries, base 1, cap 5. Start with 1: write 1. Double it to 2: write 2. Double it to 4: write 4. Double it to 8: that is more than the cap of 5, so write 5. Double it to 16: still more than 5, so write 5. That makes 5 waits. Return [1, 2, 4, 5, 5].',
        why='One small step per retry.',
        gotchas=[
            [
                "Retrying errors that won't fix themselves",
                'Retry on "too many requests" (429), timeouts and server errors (codes in the 500s). Don\'t retry "bad request" (400) or "unauthorized" (401). They fail the same way every time.',
            ],
            [
                'Everyone retrying at the same moment',
                'If a thousand clients all wait exactly 2 seconds, they hit the server together again. Real code adds a little randomness, called jitter.',
            ],
            [
                'Use a library',
                "In real projects, the tenacity library, or the max_retries option built into your SDK (the API's official Python library), does this for you. Knowing how it works helps you set it well.",
            ],
        ],
    ),
)

lesson(MODULE, 'parse_labels',
    title='Testing AI code',
    learn=[
        'Model calls are slow, cost money and give different answers each time, which makes tests **flaky**: passing one run, failing the next.',
        "Keep the model call thin and separate. Test the logic around it (parsing, routing, error handling) with **fake** replies, in **unit tests**: small automatic checks of your code. Test the model's quality with **evals**: example inputs with expected answers, plus a way to score them.",
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
        pattern='Keep the logic apart from the model call',
        text='One walk through the replies. Designing for testability is a big part of senior interviews.',
        say='"I separate the model call from the logic, unit-test the logic with a scripted fake model, and cover quality with evals."',
        classic=None,
    ),
    stack=stack('LangChain: a fake chat model for tests', 'from langchain_core.language_models.fake_chat_models import GenericFakeChatModel\nfrom langchain_core.messages import AIMessage\n\nfake = GenericFakeChatModel(messages=iter([AIMessage(content="Billing.")]))\n# classify is your own function: it calls llm, then cleans up the reply\nassert classify("Why was I charged twice?", llm=fake) == "billing"'),
    exercise=exercise(
        title='Clean Up Model Replies',
        topic='testing',
        difficulty='easy',
        fn='parse_labels',
        prompt="""Your function gets two things:

- `replies`: what a classifier model said about each customer message, like `["Billing.", " refund "]`. A classifier is a model that picks a label, like billing, for each message.
- `allowed`: the labels you accept, like `["billing", "refund"]`.

Clean each reply: trim spaces from both ends, make it lowercase, then remove a `.` from the end if there is one. If the cleaned reply is in `allowed`, that's its label. If not, its label is `"unknown"`. Return the labels in the same order as `replies`.

These replies are fake, the kind you use in unit tests (small automatic checks of your code) so you don't call a real model.""",
        pattern='Clean every reply the same way (trim, lowercase, drop the dot), then check it against `allowed`. Because the replies come in as an input, you can test this with fake replies and no real model.',
        target='one walk through the replies',
        realworld="LangChain ships `GenericFakeChatModel` for this: it returns scripted replies, so unit tests run fast, free and the same every time. Test the parsing, routing and error handling with fakes; test the model's quality with evals.",
        starter="""def parse_labels(replies, allowed):
    # your code here
    pass
""",
        solution="""def parse_labels(replies, allowed):
    labels = []
    for reply in replies:
        label = reply.strip().lower()
        if label.endswith("."):
            label = label[:-1]
        if label in allowed:
            labels.append(label)
        else:
            labels.append("unknown")
    return labels
""",
        cases=[
            case(['Billing.', ' refund ', "I think it's billing", 'SHIPPING'], ['billing', 'refund', 'shipping'], expected=['billing', 'refund', 'unknown', 'shipping'], sample=True),
            case([], ['a'], expected=[]),
            case(['.'], ['a'], expected=['unknown']),
            case(['a.', 'b'], ['a'], expected=['a', 'unknown']),
            case([' Refund. ', 'billing'], ['billing', 'refund'], expected=['refund', 'billing']),
        ],
        guided="""def parse_labels(replies, allowed):
    # Replace every ___ with real code, then run the tests.

    labels = []
    for reply in replies:
        # Step 1: trim the spaces, then make it lowercase.
        label = reply.strip().___()
        # Step 2: drop the "." at the end, if there is one.
        if label.endswith("."):
            label = label[:-1]
        # Step 3: keep it if it's allowed, else "unknown".
        if ___:
            labels.append(label)
        else:
            labels.append("unknown")
    return labels
""",
        fills=['lower', 'label in allowed'],
        concepts=[
            [
                'strip and lower',
                'strip() trims spaces from both ends. lower() makes every letter lowercase. You can chain them.',
                "' Hello '.strip().lower()   # 'hello'",
            ],
            ['endswith', 'Checks how a string ends. Gives True or False.', "'cats'.endswith('s')   # True"],
            [
                'Dropping the last character',
                '`s[:-1]` is everything except the last character.',
                "'cats'[:-1]   # 'cat'",
            ],
            [
                'in with a list',
                '`x in some_list` is True if x is one of the items.',
                "'b' in ['a', 'b']   # True",
            ],
        ],
        byhand='"Billing." trims to itself, lowercases to "billing.", and loses its dot: "billing". That is allowed, so keep it. " refund " trims to "refund": allowed. "I think it\'s billing" is not an allowed label, so it becomes "unknown". "SHIPPING" lowercases to "shipping": allowed. Return ["billing", "refund", "unknown", "shipping"].',
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
