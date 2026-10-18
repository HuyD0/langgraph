"""LLMOps: Cost and caching in production."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, source, stack

MODULE = module('llmops', 'LLMOps', 'Cost and caching in production.')

lesson(MODULE, 'token_cost',
    title='Tokens and cost',
    checked='2026-10-18',
    sources=[source('OpenAI: What are tokens and how to count them', 'https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them'),
             source('OpenAI API pricing', 'https://developers.openai.com/api/docs/pricing')],
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
            "The model's accuracy on last month's eval set",
            'Tokens per request, especially output tokens',
            "The API's uptime, in case retries doubled the calls",
        ],
        answer=1,
        why='Same requests, more cost means more tokens per request: longer prompts, longer answers or more agent steps.',
    ),
    angle=angle(
        pattern='Add up cost per model',
        text="The big idea: track cost per model from day one, so when the bill jumps you can see why. For each call, your code multiplies input tokens by the input price and output tokens by the output price, then divides the sum by one million. It adds that cost to its model's running total, kept in a dict, a lookup table from model name to number. `totals.get(model, 0)` starts a new model at 0. Rounding to 4 places happens only at the end.",
        say='"For each call I work out the cost from its [[input and output|total|average::Two kinds of tokens, each with its own price.]] prices, and add it to that model\'s total. I [[round|add|check::Cutting off extra decimal places.]] only at the end, so small errors don\'t pile up."',
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

lesson(MODULE, 'estimate_vs_actual',
    title='Estimate against actual',
    checked='2026-10-17',
    sources=[source('Track model usage (Unity Gateway usage table)', 'https://docs.databricks.com/aws/en/ai-gateway/usage-tracking'), source('Track model usage - Azure Databricks', 'https://learn.microsoft.com/en-us/azure/databricks/ai-gateway/usage-tracking')],
    learn=[
        'Before launch, every cost number is a guess. If nobody checks it against the real bill, a project can run far over for months before anyone notices.',
        'So each month, set the **estimate** (what the plan said a project would cost) next to the **actual** (what it really cost). **Percent over** is the extra spend as a share of the estimate. A project planned at $400 that cost $520 is $120 over, which is 30 percent of $400.',
        "When several projects share one model service, each request needs a label saying which project sent it. On the Databricks AI gateway (now called Unity Gateway), a **request tag** does this, and the usage table records it next to each request's tokens.",
        "By default, querying that table takes two admin roles: account admin and metastore admin (the admin of Unity Catalog's top-level store). Admins can give others access. Usage tracking is billed too: Databricks charges for what it logs.",
        'Flag only projects over by a set margin, such as 20 percent, and look at the biggest first. Then replace the guess in the plan with the measured number.',
    ],
    example=example('Percent over for one project', """estimate = 400   # the plan, dollars
actual = 520     # the real bill
over = (actual - estimate) / estimate
# over is 0.3
percent = int(round(over * 100))
# percent is 30"""),
    check=question(
        'Project A planned $100 a month and spent $150. Project B planned $1,000 and spent $1,200. Whose estimate was the worse guess for its size?',
        [
            'B, because it spent $200 more than planned',
            'Neither, both are off by about the same',
            'A, because it spent 50 percent more than planned',
        ],
        answer=2,
        why="Percent over compares each project with its own estimate. A is 50 percent over and B only 20 percent, even though B's extra dollars are bigger.",
    ),
    angle=angle(
        pattern='Keep the overruns, biggest first',
        text='The big idea: check every estimate against the real bill each month, and look at the biggest overruns first. For each project, your code works out how far over it is: the extra spend divided by the estimate. It keeps the project only if that share is at least the threshold, and turns it into a whole percent. Then it sorts the pairs so the biggest percent comes first, with equal percents in A to Z order by name.',
        say='"Each month I compare every project\'s real bill with its [[estimate|contract|last bill::The number you guessed at the start.]]. I flag the ones that went over by my margin or more, and look at the [[biggest|newest|smallest::Deal with the worst overrun first.]] first."',
        classic=None,
    ),
    stack=stack('Databricks: actual tokens per project from request tags', """-- Unity Gateway's own usage table; the
-- older endpoint table in 'Tokens and
-- cost' has no request tags
-- each app sends its project name in
-- the Databricks-Ai-Gateway-Request-Tags
-- header; it lands in request_tags
SELECT
  request_tags['project'] AS project,
  destination_model,
  SUM(input_tokens) AS input_tokens,
  SUM(output_tokens) AS output_tokens
FROM system.ai_gateway.usage
WHERE request_tags['project'] IS NOT NULL
  AND event_time >=
      current_date() - INTERVAL 30 DAYS
GROUP BY request_tags['project'],
         destination_model
-- times each model's prices: a close
-- guess at the actual. Add up each
-- project's rows. Azure's bill is
-- final. Set it next to each estimate."""),
    exercise=exercise(
        title='Projects Over Estimate',
        topic='llmops',
        difficulty='easy',
        fn='estimate_vs_actual',
        prompt="""Your function gets two things:

- `rows`: one dict per project, like `{"project": "search", "estimate": 100, "actual": 165}`. `estimate` is the planned dollars for the month and `actual` is what it really cost. `estimate` is always above 0.
- `threshold`: how far over counts as a problem, as a share, like `0.2` for 20 percent.

For each project, work out `over = (actual - estimate) / estimate`. Keep the project only if `over` is at least `threshold`.

For each kept project, make a pair `[project, percent]`. `percent` is `over` times 100 as a whole number: `int(round(over * 100))`.

Return the list of pairs, biggest percent first. When two percents are equal, put those names in A to Z order. If no project is kept, return `[]`.""",
        pattern="Filter and rank: work out each project's percent over, keep the ones at or above the threshold, then sort biggest first with the name breaking ties.",
        target='one pass over the rows, then one sort',
        realworld="After launch, teams set each project's planned spend next to its real spend every month. When projects share one model service, tagging every request with its project (a request tag on the Databricks AI gateway) is what lets the real spend be split by project. A project with its own model service can use a service tag set in Terraform instead.",
        starter="""def estimate_vs_actual(rows, threshold):
    # your code here
    pass
""",
        solution="""def estimate_vs_actual(rows, threshold):
    kept = []
    for row in rows:
        estimate = row["estimate"]
        actual = row["actual"]
        over = (actual - estimate) / estimate
        if over >= threshold:
            percent = int(round(over * 100))
            kept.append([row["project"], percent])
    kept.sort(key=lambda p: (-p[1], p[0]))
    return kept
""",
        cases=[
            case([
                {'project': 'help-center', 'estimate': 400, 'actual': 520},
                {'project': 'hr-bot', 'estimate': 250, 'actual': 240},
                {'project': 'search', 'estimate': 100, 'actual': 165},
                {'project': 'summaries', 'estimate': 300, 'actual': 330},
            ], 0.2, expected=[['search', 65], ['help-center', 30]], sample=True),
            case([], 0.2, expected=[]),
            case([
                {'project': 'faq', 'estimate': 100, 'actual': 90},
                {'project': 'triage', 'estimate': 200, 'actual': 210},
            ], 0.2, expected=[]),
            case([
                {'project': 'rag-search', 'estimate': 200, 'actual': 250},
                {'project': 'chat', 'estimate': 80, 'actual': 100},
                {'project': 'triage', 'estimate': 40, 'actual': 60},
                {'project': 'faq', 'estimate': 100, 'actual': 124},
            ], 0.25, expected=[['triage', 50], ['chat', 25], ['rag-search', 25]]),
            case([
                {'project': 'agent', 'estimate': 300, 'actual': 1000},
                {'project': 'docs', 'estimate': 70, 'actual': 79},
                {'project': 'faq', 'estimate': 50, 'actual': 50},
            ], 0.1, expected=[['agent', 233], ['docs', 13]]),
        ],
        guided="""def estimate_vs_actual(rows, threshold):
    # Replace every ___ with real code, then run the tests.

    kept = []
    for row in rows:
        estimate = row["estimate"]
        actual = row["actual"]
        # Step 1: the extra, as a share of the estimate.
        over = ___
        # Step 2: keep it if over is at least threshold.
        if ___:
            percent = int(round(over * 100))
            kept.append([row["project"], percent])

    # Step 3: biggest percent first, ties A to Z.
    kept.sort(key=lambda p: (-p[1], p[0]))
    return kept
""",
        fills=['(actual - estimate) / estimate', 'over >= threshold'],
        concepts=[
            [
                'Dividing to get a share',
                '`a / b` divides and gives a decimal. Dividing a part by the whole gives a share: 0.25 means 25 percent.',
                """late = 15
share = late / 60   # 0.25""",
            ],
            [
                'At least: >=',
                '`a >= b` is True when `a` is equal to `b` or bigger.',
                """5 >= 5   # True
4 >= 5   # False""",
            ],
            [
                'A whole number: int(round(x))',
                '`round(x)` goes to the nearest whole number. `int(...)` makes it show as 30, not 30.0.',
                """int(round(29.6))   # 30
int(round(12.4))   # 12""",
            ],
            [
                'append',
                '`items.append(x)` adds `x` to the end of a list. `x` can itself be a list, like a pair.',
                """pairs = []
pairs.append(["ann", 30])
# [["ann", 30]]""",
            ],
            [
                'Sorting with a tie-break',
                '`key=` says what to sort by. `lambda p: ...` is a tiny function: give it a pair `p` and it gives back what to sort by. `p[1]` is the second item (the number) and `p[0]` the first (the name). Python compares the first thing, and looks at the second only when the first is equal. The minus sign flips the number, so the biggest comes first.',
                """pets = [["cat", 3], ["dog", 9],
        ["ant", 9]]
pets.sort(key=lambda p: (-p[1], p[0]))
# ant 9, dog 9, cat 3""",
            ],
        ],
        byhand='The threshold is 0.2, so a project must be at least 20 percent over. help-center: 520 minus 400 is 120, and 120 divided by 400 is 0.3. That is at least 0.2, so keep it as 30 percent. hr-bot: 240 is less than its estimate of 250, so it came in under. Leave it out. search: 165 minus 100 is 65, and 65 divided by 100 is 0.65. Keep it as 65 percent. summaries: 330 minus 300 is 30, and 30 divided by 300 is 0.1. That is below 0.2, so leave it out. Biggest first, return [["search", 65], ["help-center", 30]].',
        why='One pass over the rows to work out and keep each percent, then one sort of the kept pairs.',
        gotchas=[
            [
                'Untagged requests go missing',
                'A request sent without a project tag belongs to no project, so its project looks cheaper than it is. Count the untagged requests too.',
            ],
            [
                'A big percent on a tiny bill',
                'A $10 project that is 200 percent over costs only $20 more. Look at the dollars as well before you act.',
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
# miss on 'd' with room for 3: full, so drop the front
cache.pop(0)        # ['c', 'a']
cache.append('d')   # ['c', 'a', 'd']"""),
    check=question(
        "A cache returns another user's answer to a question about their own account. What was missing from the cache key?",
        ['The model name that produced the answer', 'Who is asking: the user or their permissions', 'The time of day the question was asked'],
        answer=1,
        why='If the answer depends on the user, the user must be part of the key.',
    ),
    angle=angle(
        pattern='A list kept in order of use',
        text='The big idea: a cache reuses stored answers to save money and time, and when full it removes the prompt used longest ago. Your code keeps the cache as a list in order of use, oldest at the front. On a hit it counts it, takes the prompt out and puts it back at the end. On a miss with a full cache, `pop(0)` first removes the front one. Finding a prompt in a list means reading it from the start: fine for 2 prompts, slow for 10,000.',
        say='"I keep the prompts in the order they were [[used|added|written::A hit counts too, not just when it was first stored.]]. A hit moves a prompt to the back. When the cache is full, I remove the one at the [[front|back|middle::That\'s the one nobody has asked for in the longest time.]]."',
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
        realworld='Prompt and response caching cuts cost and waiting time for repeated questions. Model providers also offer prompt caching: cheaper prices when many prompts start with the same opening text (the same prefix).',
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
