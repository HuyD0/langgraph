"""LLMOps: Cost and caching in production."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('llmops', 'LLMOps', 'Cost and caching in production.')

lesson(MODULE, 'token_cost',
    title='Tokens and cost',
    learn=[
        'LLM providers bill per **token** (roughly three quarters of a word), with separate prices for input and output. Output usually costs several times more. Prices are quoted in dollars per million tokens.',
        'Track cost per model, per feature and per user from day one. When the bill jumps, that breakdown tells you why.',
    ],
    example=example('Cost of one call', """input_cost = input_tokens * input_price
output_cost = output_tokens * output_price
# prices are per million tokens, so divide by 1000000
cost = (input_cost + output_cost) / 1000000"""),
    check=question(
        "Your bill doubled but the number of requests didn't change. What should you check first?",
        [
            "The model's accuracy",
            'Tokens per request, especially output tokens and agent steps',
            "The API's uptime",
        ],
        answer=1,
        why='Same requests, more cost means more tokens per request: longer prompts, longer answers or more agent steps.',
    ),
    angle=angle(
        pattern='Group and sum',
        text='One walk through the calls, adding each cost into a dict where each key is a model name. Group Anagrams has the same group-by-key shape.',
        say='"I add each cost into a dict where each key is a model name, in one walk through the calls, and round only at the end so rounding errors don\'t pile up."',
        classic='group_anagrams',
    ),
    stack=stack('Databricks: tokens per endpoint from AI Gateway usage tracking', """SELECT served_entity_id,
       sum(input_token_count)  AS input_tokens,
       sum(output_token_count) AS output_tokens
FROM system.serving.endpoint_usage
WHERE request_time >= current_date() - INTERVAL 7 DAYS
GROUP BY served_entity_id"""),
    exercise=exercise(
        title='Cost per Model',
        topic='llmops',
        difficulty='easy',
        fn='token_cost',
        prompt="""Your function gets two things:

- `calls`: a list of LLM calls. Each call is a dict like `{"model": "fast-model", "input_tokens": 1200, "output_tokens": 300}`.
- `prices`: the price of each model, like `{"fast-model": [1, 5]}`. The first number is the input price and the second is the output price, in dollars per million tokens.

For one call, multiply its input tokens by the input price. Multiply its output tokens by the output price. Add the two, then divide by 1000000 (one million). In Python, write big numbers without commas.

Add up the cost of the calls for each model. Return a dict. Each key is a model from `calls`. Its value is that model's total cost, rounded to 4 decimal places at the end. If `calls` is empty, return `{}`.""",
        pattern="Group by model: add each call's cost to that model's total in a dict.",
        target='one pass over the calls',
        realworld='LLM bills are per token, and output tokens usually cost several times more than input. Breaking cost down by model (and by feature or user) is the first thing a team does when the bill jumps.',
        starter="""def token_cost(calls, prices):
    # your code here
    pass
""",
        solution="""def token_cost(calls, prices):
    totals = {}
    for call in calls:
        model = call["model"]
        input_price, output_price = prices[model]
        input_cost = call["input_tokens"] * input_price
        output_cost = call["output_tokens"] * output_price
        cost = (input_cost + output_cost) / 1000000
        totals[model] = totals.get(model, 0) + cost
    rounded = {}
    for model in totals:
        rounded[model] = round(totals[model], 4)
    return rounded
""",
        cases=[
            case([
                {'model': 'fast-model', 'input_tokens': 1200, 'output_tokens': 300},
                {'model': 'smart-model', 'input_tokens': 2000, 'output_tokens': 500},
                {'model': 'fast-model', 'input_tokens': 800, 'output_tokens': 200},
            ], {'fast-model': [1, 5], 'smart-model': [3, 15]}, expected={'fast-model': 0.0045, 'smart-model': 0.0135}, sample=True),
            case([], {'fast-model': [1, 5]}, expected={}),
            case([{'model': 'smart-model', 'input_tokens': 1000000, 'output_tokens': 0}], {'smart-model': [3, 15]}, expected={'smart-model': 3.0}),
            case([
                {'model': 'a', 'input_tokens': 10, 'output_tokens': 10},
                {'model': 'a', 'input_tokens': 10, 'output_tokens': 10},
            ], {'a': [2, 8]}, expected={'a': 0.0002}),
        ],
        guided="""def token_cost(calls, prices):
    # Replace every ___ with real code, then run the tests.

    totals = {}
    for call in calls:
        model = call["model"]
        # Step 1: this model's two prices.
        input_price, output_price = prices[model]
        # Step 2: tokens times price, for input and output.
        input_cost = call["input_tokens"] * input_price
        output_cost = ___
        # Prices are per million tokens.
        cost = (input_cost + output_cost) / 1000000
        # Step 3: add to this model's total (starts at 0).
        totals[model] = ___ + cost

    # Round each total once, at the end.
    rounded = {}
    for model in totals:
        rounded[model] = round(totals[model], 4)
    return rounded
""",
        fills=['call["output_tokens"] * output_price', 'totals.get(model, 0)'],
        concepts=[
            [
                'Adding up into a dict',
                '`d.get(k, 0)` gives the value for `k`, or 0 if `k` is not there yet. So a running total starts at 0.',
                """steps = {}
steps['mon'] = steps.get('mon', 0) + 5
steps['mon'] = steps.get('mon', 0) + 3
# steps['mon'] is now 8""",
            ],
            [
                'Unpacking a pair',
                'Two names on the left take the two values of a list, in order.',
                """low, high = [3, 15]
# low is 3, high is 15""",
            ],
            [
                'Looping over a dict',
                '`for k in d` gives each key in turn. `d[k]` is its value.',
                """ages = {'ann': 30, 'bo': 25}
for name in ages:
    print(name, ages[name])""",
            ],
            [
                'round',
                '`round(x, 4)` keeps 4 decimal places.',
                'round(3.14159, 2)   # 3.14',
            ],
        ],
        byhand='Call 1 is fast-model: 1200 times 1, plus 300 times 5, is 2700. Divided by a million, that is 0.0027. Call 2 is smart-model: 2000 times 3, plus 500 times 15, is 13500, so 0.0135. Call 3 is fast-model again: 800 times 1, plus 200 times 5, is 1800, so 0.0018. fast-model adds up to 0.0027 plus 0.0018, which is 0.0045. smart-model has just the one call, 0.0135. Rounded to 4 places, return {"fast-model": 0.0045, "smart-model": 0.0135}.',
        why='One walk through the calls. Each call just adds to one total in the dict.',
        gotchas=[
            [
                'Output tokens dominate',
                'A long answer can cost more than a long prompt. Capping output length is often the quickest saving.',
            ],
            [
                'Retries cost too',
                'Every retry and every agent step is billed. Count tokens per request in your traces, not just per user message.',
            ],
        ],
    ),
)

lesson(MODULE, 'cache_hits',
    title='Caching responses',
    learn=[
        'Many requests repeat. A **cache** returns a stored answer instead of calling the model again, which saves money and time. It looks answers up by a **key**, usually the prompt text.',
        "Caches have a size limit. **LRU** (least recently used) removes whatever hasn't been used for the longest time.",
    ],
    example=example('LRU in Python', """# used longest ago at the front
cache = ['a', 'b', 'c']
key = 'a'
# on a hit: move it to the newest end
cache.remove(key)
cache.append(key)   # ['b', 'c', 'a']
# full: remove the one used longest ago
cache.pop(0)        # ['c', 'a']"""),
    check=question(
        "A cache returns another user's answer to a question about their own account. What was missing from the cache key?",
        ['The model name', 'Who is asking (the user or their permissions)', 'The time of day'],
        answer=1,
        why='If the answer depends on the user, the user must be part of the key.',
    ),
    angle=angle(
        pattern='LRU cache',
        text='A dict finds things instantly, and a doubly linked list (a chain where each item is linked to the one before and the one after) or Python\'s OrderedDict remembers which item was used least recently. Because each item knows both neighbours, you can unhook it from the middle without searching. Together, every lookup and every removal is instant. "Design an LRU cache" is itself a very common interview question.',
        say='"A dict for instant lookups plus a doubly linked list for the order of use. The dict points straight at each item, and each item links to the one before and after, so reading, adding and removing are all instant."',
        classic=None,
    ),
    stack=stack('LangChain: an LLM cache', """from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
set_llm_cache(InMemoryCache())"""),
    exercise=exercise(
        title='Count Cache Hits',
        topic='llmops',
        difficulty='medium',
        fn='cache_hits',
        prompt="""A cache keeps recent prompts, so a repeated prompt can reuse its stored answer instead of calling the model again.

Your function gets two things:

- `prompts`: the prompts that arrive, in order, like `["hi", "price", "hi"]`.
- `capacity`: how many prompts the cache can hold, like `2`. It is always at least 1.

The cache starts empty. Go through `prompts` in order:

- If the prompt is already in the cache, that's a hit. Count it. It is now the most recently used.
- If it is not in the cache, add it as the most recently used. But if the cache is already full, first remove the prompt used longest ago.

Return the number of hits.""",
        pattern='Keep the cache as a list in order of use: used longest ago at the front, newest at the end.',
        target='one walk through the prompts',
        realworld='Prompt and response caching cuts cost and waiting time for repeated questions. Model providers also offer cheaper prices when many prompts start with the same opening text.',
        starter="""def cache_hits(prompts, capacity):
    # your code here
    pass
""",
        solution="""def cache_hits(prompts, capacity):
    cache = []
    hits = 0
    for prompt in prompts:
        if prompt in cache:
            hits += 1
            cache.remove(prompt)
        elif len(cache) == capacity:
            cache.pop(0)
        cache.append(prompt)
    return hits
""",
        cases=[
            case(['hi', 'price', 'hi', 'refund', 'price'], 2, expected=1, sample=True),
            case([], 3, expected=0),
            case(['a', 'a', 'a'], 1, expected=2),
            case(['a', 'b', 'c', 'a', 'b', 'c'], 3, expected=3),
            case(['a', 'b', 'c', 'a', 'b', 'c'], 2, expected=0),
        ],
        guided="""def cache_hits(prompts, capacity):
    # Replace every ___ with real code, then run the tests.

    # Used longest ago at the front, newest at the end.
    cache = []
    hits = 0
    for prompt in prompts:
        if prompt in cache:
            # Step 1: a hit. Count it, then take it out
            # so it can go back in at the end.
            hits += 1
            ___
        elif len(cache) == capacity:
            # Step 2: full. Remove the first item, the one
            # used longest ago.
            ___
        # Step 3: put this prompt at the end, as the newest.
        cache.append(prompt)
    return hits
""",
        fills=['cache.remove(prompt)', 'cache.pop(0)'],
        concepts=[
            [
                'Moving an item to the end',
                '`q.remove(x)` takes `x` out of the list. `q.append(x)` puts it back at the end.',
                """q = ['a', 'b', 'c']
q.remove('a')
q.append('a')   # ['b', 'c', 'a']""",
            ],
            [
                'pop(0)',
                '`q.pop(0)` removes the first item of the list.',
                """q = ['a', 'b', 'c']
q.pop(0)   # q is now ['b', 'c']""",
            ],
            [
                'Is it in the list? and elif',
                '`x in q` is True when the list `q` holds `x`. `elif` means "else, if": it is checked only when the `if` above was False.',
                """q = ['a', 'b']
if 'b' in q:
    print('found')
elif len(q) == 2:
    print('full')""",
            ],
        ],
        byhand='Capacity 2, and the cache starts empty. hi: not in the cache, so add it: [hi]. price: not there, add it: [hi, price]. hi: a hit, the first one. Move it to the end: [price, hi]. refund: not there, and the cache is full. Remove the first item, price, then add refund: [hi, refund]. price: not there, and full again. Remove hi, then add price: [refund, price]. That is 1 hit, so return 1.',
        why="One walk through the prompts. Checking a list looks at every item, which is fine for a small cache. In interviews people use Python's OrderedDict, which finds and moves items instantly.",
        gotchas=[
            [
                'Exact-match caches miss paraphrases',
                '"what\'s the price" and "how much is it" are different keys. A semantic cache (one that matches by meaning, not exact text) compares embeddings (lists of numbers that capture meaning) instead, at the risk of returning a wrong match.',
            ],
            [
                'Never cache across users by accident',
                "If answers depend on who's asking, the user (or their permissions) must be part of the cache key.",
            ],
        ],
    ),
)
