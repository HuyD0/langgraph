"""Shipping models and agents: Registering, promoting and canarying on Databricks."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('shipping', 'Shipping models and agents', 'Registering, promoting and canarying on Databricks.')

lesson(MODULE, 'promote_model',
    title='Model registry and promotion',
    learn=[
        "A **model registry** (such as MLflow's on Databricks) stores every trained version with its metrics. **Aliases** like `@champion` point at the version serving traffic.",
        'Promote a **challenger** (a newer version that wants the job) only when it beats the champion by a meaningful margin on the same data. Rolling back is just moving the alias back.',
    ],
    example=example('Loading by alias with MLflow', """import mlflow
model = mlflow.pyfunc.load_model('models:/main.ml.churn@champion')"""),
    check=question(
        'Why require a minimum gain before promoting?',
        [
            'To save storage',
            'Tiny differences are often noise, and every swap carries risk',
            'MLflow requires it',
        ],
        answer=1,
        why='A 0.001 improvement may vanish on new data. Swapping models has a cost, so make it worth it.',
    ),
    angle=angle(
        pattern='Running best with a rule',
        text='One walk through the versions, keeping the best candidate so far, with a clear rule for ties. Maximum Subarray uses the same keep-the-best-so-far bookkeeping.',
        say='"One pass with a running best. Only candidates that clear the minimum gain can replace it, and ties go to the earlier version."',
        classic='max_subarray',
    ),
    stack=stack('Databricks: move the champion alias in Unity Catalog', """from mlflow import MlflowClient
MlflowClient(registry_uri="databricks-uc").set_registered_model_alias(
    "main.support.support_agent", "champion", version=4)"""),
    exercise=exercise(
        title='Promote a Challenger',
        topic='mlops',
        difficulty='medium',
        fn='promote_model',
        prompt="""Your function gets three things:

- `champion`: the version in use now, like `{"version": 3, "score": 81}`. Scores are out of 100.
- `challengers`: newer versions, in version order. Each is a dict like `{"version": 4, "score": 84}`.
- `min_gain`: how many points better a challenger must be, like `2`. It is always 1 or more.

A challenger counts only if its score is at least the champion's score plus `min_gain`. Of the ones that count, pick the one with the highest score. If two tie, keep the earlier one. Return its `version`. If none counts, return the champion's `version`.""",
        pattern='Keep the best so far, and let a challenger replace it only if it clears the bar.',
        target='one pass over the challengers',
        realworld="MLflow's model registry uses aliases like `@champion` and `@challenger` for exactly this. Requiring a minimum gain stops you swapping models for noise-level differences, since every swap carries risk.",
        starter="""def promote_model(champion, challengers, min_gain):
    # your code here
    pass
""",
        solution="""def promote_model(champion, challengers, min_gain):
    bar = champion["score"] + min_gain
    best = champion
    for challenger in challengers:
        score = challenger["score"]
        if score >= bar and score > best["score"]:
            best = challenger
    return best["version"]
""",
        cases=[
            case({'version': 3, 'score': 81}, [
                {'version': 4, 'score': 84},
                {'version': 5, 'score': 82},
                {'version': 6, 'score': 86},
            ], 2, expected=6, sample=True),
            case({'version': 3, 'score': 81}, [
                {'version': 4, 'score': 84},
                {'version': 5, 'score': 82},
            ], 2, expected=4),
            case({'version': 3, 'score': 81}, [{'version': 4, 'score': 82}], 2, expected=3),
            case({'version': 1, 'score': 70}, [], 1, expected=1),
            case({'version': 4, 'score': 80}, [{'version': 5, 'score': 82}], 2, expected=5),
            case({'version': 2, 'score': 60}, [
                {'version': 5, 'score': 90},
                {'version': 7, 'score': 90},
            ], 5, expected=5),
            case({'version': 1, 'score': 70}, [
                {'version': 2, 'score': 90},
                {'version': 3, 'score': 80},
            ], 5, expected=2),
            case({'version': 4, 'score': 80}, [{'version': 6, 'score': 75}], 1, expected=4),
        ],
        guided="""def promote_model(champion, challengers, min_gain):
    # Replace every ___ with real code, then run the tests.

    # Step 1: the bar is the champion's score plus min_gain.
    bar = ___
    # best starts as the champion (kept if none counts).
    best = champion
    for challenger in challengers:
        score = challenger["score"]
        # Step 2: keep it only if it reaches the bar
        # and its score is higher than best["score"].
        if score >= bar and ___:
            best = challenger
    return best["version"]
""",
        fills=['champion["score"] + min_gain', 'score > best["score"]'],
        concepts=[
            [
                'Dict access',
                '`champion["score"]` gets one field of a dict.',
                """song = {"title": "Hey", "mins": 3}
song["mins"]   # 3""",
            ],
            [
                'At least, or higher',
                '`>=` means "at least": a tie passes. `>` means "higher": a tie fails, so the earlier one is kept.',
                """5 >= 5   # True
5 > 5    # False""",
            ],
            [
                'Two conditions with and',
                '`a and b` is True only when both are True.',
                """age = 20
has_ticket = True
age >= 18 and has_ticket   # True""",
            ],
        ],
        byhand="The champion is version 3 with 81. The bar is 81 plus 2, so 83. Version 4 has 84. It reaches 83 and beats the best so far (81), so it becomes the best. Version 5 has 82. That is below 83, so skip it. Version 6 has 86. It reaches 83 and beats 84, so it becomes the best. Return 6.",
        why='One walk through the challengers.',
        gotchas=[
            [
                'Compare on the same data',
                "A challenger evaluated on a different test set isn't comparable. Log the dataset version with every metric.",
            ],
            [
                'Promote by alias, roll back by alias',
                'Pointing `@champion` at a new version is instant to undo, which is why aliases beat redeploying with a new model address (the `models:/...` string your code loads).',
            ],
        ],
    ),
)

lesson(MODULE, 'route_request',
    title='Canary releases',
    learn=[
        'Never switch all traffic to a new agent at once. In a **canary release**, you send a small share (say 10%) to the new version (the canary), compare its traces and evals with the old one, then move the split.',
        'A Databricks serving endpoint can serve several versions and split traffic between them by percentage. Rolling back is just setting the new version to 0%.',
    ],
    example=example('A 90/10 split', """routes = [
  {"served_entity_name": "support_agent-3", "traffic_percentage": 90},
  {"served_entity_name": "support_agent-4", "traffic_percentage": 10},
]"""),
    check=question(
        "The canary's error rate doubles in the first hour. What do you do?",
        [
            'Wait a week for more data',
            'Move its traffic back to 0% and look at its traces',
            'Switch everyone to it',
        ],
        answer=1,
        why="That's what a stop rule (a limit you set in advance that means roll back) is for. Roll back first, then investigate.",
    ),
    angle=angle(
        pattern='Running total',
        text='Walk the routes adding percentages and stop at the first total that is bigger than the bucket. One walk through the routes.',
        say='"I bucket the user id into 0 to 99, so one person always gets the same version, and walk the routes with a running total; the first route whose total exceeds the bucket wins."',
        classic=None,
    ),
    stack=stack('Databricks: a 90/10 split on a serving endpoint', """import mlflow.deployments
deploy = mlflow.deployments.get_deploy_client("databricks")
deploy.update_endpoint_config(endpoint="support-agent", config={
    "served_entities": [...],   # versions 3 and 4
    "traffic_config": {"routes": [
        {"served_entity_name": "support_agent-3", "traffic_percentage": 90},
        {"served_entity_name": "support_agent-4", "traffic_percentage": 10}]},
})"""),
    exercise=exercise(
        title='Canary a New Agent Version',
        topic='shipping',
        difficulty='easy',
        fn='route_request',
        prompt="""A canary release sends a small share of requests to a new version first. Your job: pick which version answers one request.

Your function gets two things:

- `routes`: the versions, in order. Each is a dict like `{"name": "v3", "percent": 90}`, meaning v3 gets about 90 of every 100 requests. The percents add up to 100.
- `user_id`: the id of the person who sent the request, a whole number like `1093`. Using their id (not a new number per request) means one person always gets the same version.

First find the bucket: the last two digits, `user_id % 100`, a number from 0 to 99.

Walk the routes, adding up their percents. Return the `name` of the first route where this running total is bigger than the bucket.

A route with 0 percent must never be picked. That is why the check is `>`, not `>=`.""",
        pattern='A running total: stop at the first route where the total is bigger than the bucket.',
        target='one walk through the routes',
        realworld="Canary releases: send a small share of real traffic to the new agent version, watch its traces and evals, then move the split to 100% or back to 0%. On Databricks this is the endpoint's `traffic_config`, where each route has a `served_entity_name` and a `traffic_percentage`.",
        starter="""def route_request(routes, user_id):
    # your code here
    pass
""",
        solution="""def route_request(routes, user_id):
    bucket = user_id % 100
    total = 0
    for route in routes:
        total += route["percent"]
        if total > bucket:
            return route["name"]
""",
        cases=[
            case([
                {'name': 'v3', 'percent': 90},
                {'name': 'v4', 'percent': 10},
            ], 1093, expected='v4', sample=True),
            case([
                {'name': 'v3', 'percent': 90},
                {'name': 'v4', 'percent': 10},
            ], 1089, expected='v3'),
            case([
                {'name': 'v3', 'percent': 90},
                {'name': 'v4', 'percent': 10},
            ], 99, expected='v4'),
            case([{'name': 'v1', 'percent': 100}], 57, expected='v1'),
            case([
                {'name': 'v1', 'percent': 50},
                {'name': 'v2', 'percent': 30},
                {'name': 'v3', 'percent': 20},
            ], 250, expected='v2'),
            case([
                {'name': 'v1', 'percent': 0},
                {'name': 'v2', 'percent': 100},
            ], 0, expected='v2'),
        ],
        guided="""def route_request(routes, user_id):
    # Replace every ___ with real code, then run the tests.

    # Step 1: the bucket is the last two digits (0 to 99).
    bucket = ___
    total = 0
    for route in routes:
        # Step 2: add this route's percent to the total.
        total += route["percent"]
        # Step 3: is the total bigger than the bucket?
        if ___:
            return route["name"]
""",
        fills=['user_id % 100', 'total > bucket'],
        concepts=[
            [
                'The remainder, %',
                '`%` gives what is left over after dividing. `% 100` keeps the last two digits.',
                '1093 % 100   # 93',
            ],
            [
                'A running total',
                'Start at 0 and add each item as you go. `total += x` is short for `total = total + x`.',
                """total = 0
for price in [3, 5, 2]:
    total += price   # 3, then 8, then 10""",
            ],
            [
                'Dict access',
                '`route["name"]` gets one field of a dict.',
                """song = {"title": "Hey", "mins": 3}
song["mins"]   # 3""",
            ],
            [
                'return inside a loop',
                '`return` ends the function at once, even in the middle of a loop. Here `first_big([4, 7, 9])` gives 7 and never looks at 9.',
                """def first_big(nums):
    for n in nums:
        if n > 5: return n""",
            ],
        ],
        byhand='1093 % 100 is 93, the last two digits, so the bucket is 93. Route v3: the total is 90. Is 90 bigger than 93? No, so keep going. Route v4: the total is now 100. Is 100 bigger than 93? Yes. Return "v4".',
        why='One walk through the routes.',
        gotchas=[
            [
                'Same user, same version',
                "Bucket by a stable id (user or conversation), not a random number, so one person doesn't bounce between versions mid-conversation.",
            ],
            [
                'Canary needs a stop rule',
                "Decide in advance what makes you roll back: more errors, slower answers, or lower quality scores on the canary's traces. Then watch for it.",
            ],
        ],
    ),
)

lesson(MODULE, 'prompt_rollout',
    title='Rolling out a new prompt',
    learn=[
        'Before a new prompt version gets the `production` alias, first score it on your saved test questions (before any real user sees it) with `mlflow.genai.evaluate`, then give it a small share of real traffic.',
        'Tag every trace with the prompt version it used. Then you can compare versions on real questions and decide with a rule you wrote down first: promote, keep testing, or roll back.',
    ],
    example=example('Same traffic, two versions', """v2 (production): 300 of 400 passed → 75%
v3 (candidate):  90 of 100 passed  → 90%
rule: at least 100 traces and 10 points better → promote v3"""),
    check=question(
        'A candidate prompt passed 2 out of 2 traces. Should you promote it?',
        ["Yes, it's perfect", 'Not yet: 2 traces is too few to tell', 'Roll it back'],
        answer=1,
        why='With tiny samples, luck decides. Set a minimum number of traces before you compare.',
    ),
    angle=angle(
        pattern='Group and count',
        text='One walk through the traces, counting totals and passes per version in dicts, then a few comparisons.',
        say='"I tag traces with the prompt version, compare pass rates once the new version has enough traffic, and promote only on a gain I set in advance."',
        classic=None,
    ),
    stack=stack('Tag traces with the prompt version, then compare', """prod = mlflow.genai.load_prompt("prompts:/main.support.answer@production")
cand = mlflow.genai.load_prompt("prompts:/main.support.answer@candidate")

@mlflow.trace
def answer(question, user_id):
    prompt = cand if bucket(user_id) < 10 else prod   # 10% to the candidate
    mlflow.update_current_trace(tags={"prompt_version": str(prompt.version)})
    ...

mlflow.search_traces(filter_string="tags.prompt_version = '3'")

# when the rule says promote:
mlflow.genai.set_prompt_alias("main.support.answer", alias="production", version=3)"""),
    exercise=exercise(
        title='Promote a Prompt Version',
        topic='shipping',
        difficulty='medium',
        fn='prompt_rollout',
        prompt="""Your function gets three things:

- `traces`: saved answers (traces), each a pair like `["new", True]`: which prompt answered (`"old"` is the one in use now, `"new"` the one on test), then `True` if it passed. `"old"` always has at least one trace.
- `min_traces`: the fewest new traces needed to judge, like `4`.
- `min_gain`: how many points higher the new pass rate must be, like `10`.

Pass rate: the percent that passed, `100 * passed / total`.

Return the word from the first rule that fits:

- `"keep"` if new has fewer than `min_traces` traces (it can have 0, so check this before dividing).
- `"promote"` if the new rate is at least the old rate plus `min_gain`.
- `"rollback"` if the new rate is below the old rate.
- `"keep"` otherwise.

The tests use tiny numbers so you can check them by hand; a real rollout needs hundreds of traces.""",
        pattern='Count per version in one walk, then apply a rule you wrote down before looking at the numbers.',
        target='one walk through the traces',
        realworld="Tag every trace with the prompt version it used, and MLflow can split production quality by version. Decide the minimum sample and the gain you need first, so a lucky afternoon doesn't ship a worse prompt.",
        starter="""def prompt_rollout(traces, min_traces, min_gain):
    # your code here
    pass
""",
        solution="""def prompt_rollout(traces, min_traces, min_gain):
    total = {"old": 0, "new": 0}
    passed = {"old": 0, "new": 0}
    for version, ok in traces:
        total[version] += 1
        if ok:
            passed[version] += 1

    if total["new"] < min_traces:
        return "keep"

    old_rate = 100 * passed["old"] / total["old"]
    new_rate = 100 * passed["new"] / total["new"]
    if new_rate >= old_rate + min_gain:
        return "promote"
    if new_rate < old_rate:
        return "rollback"
    return "keep"
""",
        cases=[
            case([
                ['old', True],
                ['new', True],
                ['new', True],
                ['old', False],
                ['new', False],
                ['new', True],
            ], 4, 10, expected='promote', sample=True),
            case([['old', True], ['new', True], ['new', False]], 4, 5, expected='keep'),
            case([['old', True]], 1, 5, expected='keep'),
            case([['old', True], ['old', True], ['new', True], ['new', False]], 2, 5, expected='rollback'),
            case([
                ['old', True], ['old', True], ['old', True], ['old', False],
                ['new', True], ['new', True], ['new', True], ['new', False],
            ], 4, 5, expected='keep'),
            case([
                ['old', True], ['old', False],
                ['new', True], ['new', True], ['new', True], ['new', False], ['new', False],
            ], 5, 20, expected='keep'),
            case([
                ['old', True], ['old', False],
                ['new', True], ['new', True], ['new', True], ['new', False], ['new', False],
            ], 5, 10, expected='promote'),
        ],
        guided="""def prompt_rollout(traces, min_traces, min_gain):
    # Replace every ___ with real code, then run the tests.

    # One counter per version, starting at 0.
    total = {"old": 0, "new": 0}
    passed = {"old": 0, "new": 0}
    for version, ok in traces:
        total[version] += 1
        # Step 1: if it passed, add 1 to passed[version].
        if ok:
            ___

    # Step 2: total["new"] is how many new traces there are.
    # Fewer than min_traces? Keep testing.
    if ___:
        return "keep"

    old_rate = 100 * passed["old"] / total["old"]
    new_rate = 100 * passed["new"] / total["new"]
    # Step 3: promote if new_rate is at least
    # old_rate plus min_gain.
    if ___:
        return "promote"
    if new_rate < old_rate:
        return "rollback"
    return "keep"
""",
        fills=[
            'passed[version] += 1',
            'total["new"] < min_traces',
            'new_rate >= old_rate + min_gain',
        ],
        concepts=[
            [
                'Unpacking a pair',
                '`for a, b in pairs:` splits each two-item list into two names.',
                """for name, age in [["Ann", 30], ["Bo", 25]]:
    print(name)   # Ann, then Bo""",
            ],
            [
                'A dict of counters',
                'A dict can hold one counter per name. `votes["yes"] += 1` adds one to the "yes" counter.',
                """votes = {"yes": 0, "no": 0}
votes["yes"] += 1   # {"yes": 1, "no": 0}""",
            ],
            [
                'Percent with /',
                '`/` divides and gives a decimal, like 75.0. Comparing 75.0 with a whole number works fine.',
                '100 * 3 / 4   # 75.0',
            ],
            [
                'At least: >=',
                '`>=` means "at least", so a tie counts. `>` means "more than", so a tie does not.',
                """60 >= 60   # True
60 > 60    # False""",
            ],
            [
                'return ends the function',
                '`return` leaves the function at once, so later checks only run if earlier ones did not match. That is why the order of the rules matters.',
                """def grade(score):
    if score < 50: return "fail"
    return "pass"   # only if 50 or more""",
            ],
        ],
        byhand='First count. old has 2 traces and 1 passed. new has 4 traces and 3 passed. Rule 1: new has 4 traces. 4 is not fewer than 4, so we can judge it. old: 1 of 2 passed, so 50 percent. new: 3 of 4 passed, so 75 percent. Rule 2: the bar is 50 plus 10, so 60. 75 is at least 60. Return "promote".',
        why='One walk through the traces, then a few comparisons.',
        gotchas=[
            [
                'Same traffic, same judge',
                'Compare versions on the same kind of questions with the same scorer, or the difference may come from the questions, not the prompt.',
            ],
            [
                'Prompt and model travel together',
                'A prompt tuned for one model can get worse on another. Tag the model on the trace too, and re-test prompts when you change models.',
            ],
        ],
    ),
)
