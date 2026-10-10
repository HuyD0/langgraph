"""LLMOps: Cost and caching in production."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('llmops', 'LLMOps', 'Cost and caching in production.')

lesson(MODULE, 'token_cost',
    title='Tokens and cost',
    learn=[
        'LLM providers bill per **token** (roughly ¾ of a word), with separate prices for input and output. Output usually costs several times more.',
        'Track cost per model, per feature and per user from day one. When the bill jumps, that breakdown tells you why.',
    ],
    example=example('Cost of one call', 'cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000'),
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
        text='One walk through the calls, adding each cost into a dict keyed by model. Group Anagrams has the same group-by-key shape.',
        say='"I add up into a dict keyed by model in one pass, and round only at the end so rounding errors don\'t pile up."',
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
        prompt="""Each LLM call in `calls` looks like `{"model": "fast-model", "input_tokens": 1200, "output_tokens": 300}`. `prices` maps each model to `[input_price, output_price]` in dollars per million tokens.

Return a dict from model to its total cost in dollars, rounded to 4 decimal places. Every model in `calls` is in `prices`. The prices are made up.""",
        pattern='Group by a key and add up into a dict.',
        target='one pass over the calls',
        realworld='LLM bills are per token, and output tokens usually cost several times more than input. Breaking cost down by model (and by feature or user) is the first thing a team does when the bill jumps.',
        starter="""def token_cost(calls, prices):
    # your code here
    pass
""",
        solution="""def token_cost(calls, prices):
    totals = {}
    for c in calls:
        inp, out = prices[c["model"]]
        cost = (c["input_tokens"] * inp + c["output_tokens"] * out) / 1000000
        totals[c["model"]] = totals.get(c["model"], 0) + cost
    return {m: round(v, 4) for m, v in totals.items()}
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
    for c in calls:
        # Step 1: this model's two prices.
        inp, out = prices[c["model"]]
        # Step 2: prices are per MILLION tokens.
        cost = (c["input_tokens"] * inp + ___) / 1000000
        # Step 3: add to this model's running total (0 the first time).
        totals[c["model"]] = ___ + cost
    return {m: round(v, 4) for m, v in totals.items()}
""",
        fills=['c["output_tokens"] * out', 'totals.get(c["model"], 0)'],
        concepts=[
            [
                'Adding up into a dict',
                '`d.get(k, 0) + x` adds to a running total that starts at 0.',
                """totals = {}
totals['a'] = totals.get('a', 0) + 5""",
            ],
            ['Unpacking a pair', 'Two names, one list of two values.', 'inp, out = [3, 15]'],
        ],
        byhand='fast-model: (1200×1 + 300×5) / 1,000,000 = 0.0027, then (800×1 + 200×5) / 1,000,000 = 0.0018, total 0.0045. smart-model: (2000×3 + 500×15) / 1,000,000 = 0.0135.',
        why='One pass; each update is a dict lookup.',
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
        'Many requests repeat. A **cache** returns a stored answer instead of calling the model again, which saves money and time.',
        "Caches have a size limit. **LRU** (least recently used) evicts whatever hasn't been used for the longest time.",
    ],
    example=example('LRU in Python', """from collections import OrderedDict
cache = OrderedDict()
cache.move_to_end(key)       # on a hit
cache.popitem(last=False)    # evict the oldest"""),
    check=question(
        "A cache returns another user's answer to a question about their own account. What was missing from the cache key?",
        ['The model name', 'Who is asking (the user or their permissions)', 'The time of day'],
        answer=1,
        why='If the answer depends on the user, the user must be part of the key.',
    ),
    angle=angle(
        pattern='LRU cache',
        text='A dict finds things instantly, and a linked list (or Python\'s OrderedDict) remembers which item was used least recently. Together, every lookup and every eviction is instant. "Design an LRU cache" is itself a very common interview question.',
        say='"A dict for instant lookups plus a linked list for the order of use, so reading and adding are both instant."',
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
        prompt="""Repeated prompts can be answered from a cache instead of calling the model again. The cache holds at most `capacity` prompts and evicts the least recently used one when full.

Go through `prompts` in order. If a prompt is in the cache, that's a hit, and it becomes the most recently used. If not, add it as most recently used, evicting the least recently used prompt first if the cache is full. Return the number of hits. A capacity of 0 caches nothing.""",
        pattern='An LRU cache: fast lookup plus an order of use. Here a list keeps the order: most recent at the end.',
        target='one walk through the prompts',
        realworld='Prompt and response caching cuts cost and latency for repeated questions. Model providers also offer prompt caching for a shared prefix, priced lower than normal input tokens.',
        starter="""def cache_hits(prompts, capacity):
    # your code here
    pass
""",
        solution="""def cache_hits(prompts, capacity):
    cache = []
    hits = 0
    if capacity == 0:
        return 0
    for p in prompts:
        if p in cache:
            hits += 1
            cache.remove(p)
        elif len(cache) == capacity:
            cache.pop(0)
        cache.append(p)
    return hits
""",
        cases=[
            case(['hi', 'price?', 'hi', 'refund', 'price?', 'hi'], 2, expected=1, sample=True),
            case([], 3, expected=0),
            case(['a', 'a', 'a'], 1, expected=2),
            case(['a', 'b', 'a'], 0, expected=0),
            case(['a', 'b', 'c', 'a', 'b', 'c'], 3, expected=3),
            case(['a', 'b', 'c', 'a', 'b', 'c'], 2, expected=0),
        ],
        guided="""def cache_hits(prompts, capacity):
    # Replace every ___ with real code, then run the tests.

    cache = []   # least recently used first, most recent last
    hits = 0
    if capacity == 0:
        return 0
    for p in prompts:
        if p in cache:
            # Step 1: a hit. Take it out so it can go to the end.
            hits += 1
            ___
        elif len(cache) == capacity:
            # Step 2: full. Evict the least recently used, at the front.
            ___
        # Step 3: p is now the most recently used.
        cache.append(p)
    return hits
""",
        fills=['cache.remove(p)', 'cache.pop(0)'],
        concepts=[
            [
                'pop(0)',
                'Removes and returns the first item.',
                """q = ['a', 'b']
q.pop(0)   # 'a'""",
            ],
            [
                'Least recently used',
                'Every use moves an item to the back, so the front is always the one unused longest.',
                "# use 'a': ['b', 'c', 'a']",
            ],
        ],
        byhand='Capacity 2. hi: miss [hi]. price?: miss [hi, price?]. hi: hit, move it to the back [price?, hi]. refund: miss, full, evict price? → [hi, refund]. price?: miss, evict hi → [refund, price?]. hi: miss. One hit.',
        why="One walk through the prompts. With a list, each lookup means scanning the cache; the interview version uses a dict plus a linked list, or Python's OrderedDict, to make every step instant.",
        gotchas=[
            [
                'Exact-match caches miss paraphrases',
                '"what\'s the price" and "how much is it" are different keys. Semantic caches compare embeddings instead, at the risk of returning a wrong match.',
            ],
            [
                'Never cache across users by accident',
                "If answers depend on who's asking, the user (or their permissions) must be part of the cache key.",
            ],
        ],
    ),
)
