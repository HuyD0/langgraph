"""Shipping models and agents: Registering, promoting and canarying on Databricks."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('shipping', 'Shipping models and agents', 'Registering, promoting and canarying on Databricks.')

lesson(MODULE, 'promote_model',
    title='Model registry and promotion',
    learn=[
        "A **model registry** (such as MLflow's on Databricks) stores every trained version with its metrics. **Aliases** like `@champion` point at the version serving traffic.",
        'Promote a **challenger** only when it beats the champion by a meaningful margin on the same data. Rolling back is just moving the alias back.',
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
        prompt="""In a model registry, the `champion` alias points at the version serving traffic. `versions` is a list like `[{"version": 3, "f1": 0.81}, ...]` that includes the champion.

Return the version that should be champion: the version with the highest f1 that beats the current champion's f1 by at least `min_gain`. If several tie, pick the lowest version number. If none beats it by enough, keep the current champion.""",
        pattern='Keep the best candidate so far, with a rule for ties, and only accept a new best that clears the bar.',
        target='one pass over the versions',
        realworld="MLflow's model registry uses aliases like `@champion` and `@challenger` for exactly this. Requiring a minimum gain stops you swapping models for noise-level differences, since every swap carries risk.",
        starter="""def promote_model(versions, champion, min_gain):
    # your code here
    pass
""",
        solution="""def promote_model(versions, champion, min_gain):
    champ_f1 = None
    for v in versions:
        if v["version"] == champion:
            champ_f1 = v["f1"]
    best = champion
    best_f1 = champ_f1
    for v in versions:
        if v["f1"] - champ_f1 >= min_gain - 1e-9:
            if v["f1"] > best_f1 or (v["f1"] == best_f1 and v["version"] < best):
                best, best_f1 = v["version"], v["f1"]
    return best
""",
        cases=[
            case([{'version': 3, 'f1': 0.81}, {'version': 4, 'f1': 0.84}, {'version': 5, 'f1': 0.82}], 3, 0.02, expected=4, sample=True),
            case([{'version': 3, 'f1': 0.81}, {'version': 4, 'f1': 0.82}], 3, 0.02, expected=3),
            case([{'version': 1, 'f1': 0.7}], 1, 0.01, expected=1),
            case([{'version': 2, 'f1': 0.6}, {'version': 7, 'f1': 0.9}, {'version': 5, 'f1': 0.9}], 2, 0.05, expected=5),
            case([{'version': 4, 'f1': 0.8}, {'version': 6, 'f1': 0.75}], 4, 0.0, expected=4),
        ],
        guided="""def promote_model(versions, champion, min_gain):
    # Replace every ___ with real code, then run the tests.

    # Step 1: find the current champion's score.
    champ_f1 = None
    for v in versions:
        if v["version"] == champion:
            champ_f1 = v["f1"]

    best = champion
    best_f1 = champ_f1
    for v in versions:
        # Step 2: only versions that beat the champion by at least min_gain.
        #         (1e-9 absorbs tiny floating-point rounding.)
        if ___ >= min_gain - 1e-9:
            # Step 3: higher f1 wins; on a tie, the lower version number.
            if v["f1"] > best_f1 or ___:
                best, best_f1 = v["version"], v["f1"]
    return best
""",
        fills=['v["f1"] - champ_f1', '(v["f1"] == best_f1 and v["version"] < best)'],
        concepts=[
            [
                'Floating-point rounding',
                '0.84 - 0.81 is 0.02999999... in binary. Comparing against `min_gain - 1e-9` stops a tiny rounding error deciding the answer.',
                '0.84 - 0.81   # 0.029999999999999916',
            ],
            [
                'Two passes',
                'First find a reference value, then compare everything against it.',
                """ref = ...
for v in versions:
    ...""",
            ],
        ],
        byhand='Champion v3 has 0.81, so a challenger needs 0.83 or more. v4 has 0.84: yes. v5 has 0.82: no. Best is v4.',
        why="Two walks through the versions: one to find the champion's score, one to pick the best.",
        gotchas=[
            [
                'Compare on the same data',
                "A challenger evaluated on a different test set isn't comparable. Log the dataset version with every metric.",
            ],
            [
                'Promote by alias, roll back by alias',
                'Pointing `@champion` at a new version is instant to undo, which is why aliases beat redeploying a new model URI.',
            ],
        ],
    ),
)

lesson(MODULE, 'route_request',
    title='Canary releases',
    learn=[
        'Never switch all traffic to a new agent at once. Send a small share (say 10%) to the new version, compare its traces and evals with the old one, then move the split.',
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
        why="That's what a stop rule is for. Roll back first, then investigate.",
    ),
    angle=angle(
        pattern='Running total',
        text='Walk the routes adding percentages and stop at the first total that passes the bucket. One walk through the routes.',
        say='"I bucket the request id into 0–99 and walk the routes with a running total; the first route whose total exceeds the bucket wins."',
        classic=None,
    ),
    stack=stack('Databricks: a 90/10 split on a serving endpoint', """deploy = mlflow.deployments.get_deploy_client("databricks")
deploy.update_endpoint(endpoint="support-agent", config={
    "served_entities": [...],   # versions 3 and 4
    "traffic_config": {"routes": [
        {"served_model_name": "support_agent-3", "traffic_percentage": 90},
        {"served_model_name": "support_agent-4", "traffic_percentage": 10}]},
})"""),
    exercise=exercise(
        title='Canary a New Agent Version',
        topic='shipping',
        difficulty='easy',
        fn='route_request',
        prompt="""A serving endpoint can split traffic between versions: for example 90% to the current agent and 10% to the new one. `routes` is a list like `[{"served_entity_name": "support_agent-3", "traffic_percentage": 90}, {"served_entity_name": "support_agent-4", "traffic_percentage": 10}]`.

Given a numeric `request_id`, put it in a bucket from 0 to 99 with `request_id % 100`, then walk the routes in order adding up percentages: the first route whose running total is greater than the bucket gets the request. Return its `served_entity_name`. If the percentages don't add up to 100, return `None`.""",
        pattern='Running total over a list: find the first point where the total passes the target.',
        target='one walk through the routes',
        realworld="Canary releases: send a small share of real traffic to the new agent version, watch its traces and evals, then move the split to 100% or back to 0%. On Databricks this is the endpoint's `traffic_config`.",
        starter="""def route_request(routes, request_id):
    # your code here
    pass
""",
        solution="""def route_request(routes, request_id):
    if sum(r["traffic_percentage"] for r in routes) != 100:
        return None
    bucket = request_id % 100
    total = 0
    for r in routes:
        total += r["traffic_percentage"]
        if bucket < total:
            return r["served_entity_name"]
    return None
""",
        cases=[
            case([
                {'served_entity_name': 'support_agent-3', 'traffic_percentage': 90},
                {'served_entity_name': 'support_agent-4', 'traffic_percentage': 10},
            ], 1093, expected='support_agent-4', sample=True),
            case([
                {'served_entity_name': 'support_agent-3', 'traffic_percentage': 90},
                {'served_entity_name': 'support_agent-4', 'traffic_percentage': 10},
            ], 1089, expected='support_agent-3'),
            case([{'served_entity_name': 'a-1', 'traffic_percentage': 100}], 57, expected='a-1'),
            case([
                {'served_entity_name': 'a-1', 'traffic_percentage': 50},
                {'served_entity_name': 'a-2', 'traffic_percentage': 30},
            ], 5, expected=None),
            case([
                {'served_entity_name': 'a-1', 'traffic_percentage': 0},
                {'served_entity_name': 'a-2', 'traffic_percentage': 100},
            ], 0, expected='a-2'),
            case([], 3, expected=None),
        ],
        guided="""def route_request(routes, request_id):
    # Replace every ___ with real code, then run the tests.

    # Step 1: the split must add up to 100.
    if sum(r["traffic_percentage"] for r in routes) != 100:
        return None
    # Step 2: a bucket from 0 to 99.
    bucket = ___
    total = 0
    for r in routes:
        total += r["traffic_percentage"]
        # Step 3: the first route whose running total passes the bucket.
        if ___:
            return r["served_entity_name"]
    return None
""",
        fills=['request_id % 100', 'bucket < total'],
        concepts=[
            [
                'sum over a list of dicts',
                '`sum(x for x in ...)` adds up values picked from each item.',
                "sum(r['traffic_percentage'] for r in routes)",
            ],
            ['The remainder, %', '`1093 % 100` is 93: the last two digits.', '1093 % 100   # 93'],
        ],
        byhand="Request 1093 lands in bucket 93. Version 3 covers buckets 0–89 (running total 90): 93 isn't below 90. Version 4 brings the total to 100: 93 is below 100, so version 4 gets it.",
        why='One walk through the routes.',
        gotchas=[
            [
                'Same user, same version',
                "Bucket by a stable id (user or conversation), not a random number, so one person doesn't bounce between versions mid-conversation.",
            ],
            [
                'Canary needs a stop rule',
                'Decide in advance what makes you roll back: error rate, p95 latency, judge scores on canary traces. Then watch for it.',
            ],
        ],
    ),
)

lesson(MODULE, 'prompt_rollout',
    title='Rolling out a new prompt',
    learn=[
        'Before a new prompt version gets the `production` alias, score it offline with `mlflow.genai.evaluate`, then give it a small share of real traffic.',
        'Tag every trace with the prompt version it used. Then you can compare versions on real questions and decide with a rule you wrote down first: promote, keep testing, or roll back.',
    ],
    example=example('Same traffic, two versions', """v2 (production): 6 of 8 passed  → 75%
v3 (candidate):  4 of 4 passed  → 100%
rule: at least 4 traces and 5 points better → promote v3"""),
    check=question(
        'A candidate prompt passed 2 out of 2 traces. Should you promote it?',
        ["Yes, it's perfect", 'Not yet: 2 traces is too few to tell', 'Roll it back'],
        answer=1,
        why='With tiny samples, luck decides. Set a minimum number of traces before you compare.',
    ),
    angle=angle(
        pattern='Group and count',
        text='One walk through the traces, counting totals and passes per version in dicts, then a few comparisons.',
        say='"I tag traces with the prompt version, compare pass rates once each version has enough traffic, and promote only on a gain I set in advance."',
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
        prompt="""You're testing a new prompt version on a slice of real traffic. Each trace is `[version, ok]`: the prompt version it used and whether the judge passed it.

Compute each version's pass rate as a whole percent, rounded down (`100 * passed // total`). Then decide, comparing `candidate` against `current`:
- `"wait"` if `current` has no traces or `candidate` has fewer than `min_traces`
- `"promote"` if the candidate's rate is at least `min_gain` points higher
- `"rollback"` if it's lower
- `"keep"` otherwise (keep testing)

Return `{"decision": ..., "current": rate, "candidate": rate}`, using `None` for a version with no traces.""",
        pattern='Count per key in one walk, then apply a rule you wrote down before looking at the numbers.',
        target='one walk through the traces',
        realworld="Tag every trace with the prompt version it used, and MLflow can split production quality by version. Decide the minimum sample and the gain you need first, so a lucky afternoon doesn't ship a worse prompt.",
        starter="""def prompt_rollout(traces, current, candidate, min_traces, min_gain):
    # your code here
    pass
""",
        solution="""def prompt_rollout(traces, current, candidate, min_traces, min_gain):
    total, passed = {}, {}
    for version, ok in traces:
        total[version] = total.get(version, 0) + 1
        if ok:
            passed[version] = passed.get(version, 0) + 1
    def rate(v):
        if total.get(v, 0) == 0:
            return None
        return 100 * passed.get(v, 0) // total[v]
    cur, cand = rate(current), rate(candidate)
    if cur is None or total.get(candidate, 0) < min_traces:
        decision = "wait"
    elif cand >= cur + min_gain:
        decision = "promote"
    elif cand < cur:
        decision = "rollback"
    else:
        decision = "keep"
    return {"decision": decision, "current": cur, "candidate": cand}
""",
        cases=[
            case([
                [2, True],
                [3, True],
                [2, True],
                [2, False],
                [3, True],
                [2, True],
                [1, False],
                [2, True],
                [3, True],
                [2, False],
                [2, True],
                [3, True],
                [2, True],
            ], 2, 3, 4, 5, expected={'decision': 'promote', 'current': 75, 'candidate': 100}, sample=True),
            case([[2, True], [3, True], [3, False]], 2, 3, 4, 5, expected={'decision': 'wait', 'current': 100, 'candidate': 50}),
            case([], 2, 3, 1, 5, expected={'decision': 'wait', 'current': None, 'candidate': None}),
            case([[3, True]], 2, 3, 1, 5, expected={'decision': 'wait', 'current': None, 'candidate': 100}),
            case([[1, True], [1, True], [2, True], [2, False]], 1, 2, 2, 5, expected={'decision': 'rollback', 'current': 100, 'candidate': 50}),
            case([[1, True], [1, True], [1, True], [1, False], [2, True], [2, True], [2, True], [2, False]], 1, 2, 4, 5, expected={'decision': 'keep', 'current': 75, 'candidate': 75}),
        ],
        guided="""def prompt_rollout(traces, current, candidate, min_traces, min_gain):
    # Replace every ___ with real code, then run the tests.

    total, passed = {}, {}
    for version, ok in traces:
        # Step 1: count every trace, and the passing ones.
        total[version] = ___
        if ok:
            passed[version] = passed.get(version, 0) + 1
    def rate(v):
        if total.get(v, 0) == 0:
            return None
        # Step 2: whole percent, rounded down.
        return ___
    cur, cand = rate(current), rate(candidate)
    # Step 3: not enough evidence yet?
    if cur is None or ___:
        decision = "wait"
    elif ___:
        decision = "promote"
    elif cand < cur:
        decision = "rollback"
    else:
        decision = "keep"
    return {"decision": decision, "current": cur, "candidate": cand}
""",
        fills=[
            'total.get(version, 0) + 1',
            '100 * passed.get(v, 0) // total[v]',
            'total.get(candidate, 0) < min_traces',
            'cand >= cur + min_gain',
        ],
        concepts=[
            ['Counting per key', 'get with a default of 0, then add one.', 'seen[v] = seen.get(v, 0) + 1'],
            ['Whole percent, rounded down', '// divides and drops the remainder.', '100 * 6 // 8   # 75'],
        ],
        byhand="Version 2: 6 passed out of 8, so 75. Version 3: 4 of 4, so 100. Version 1 isn't part of the test: ignore it. Version 3 has at least 4 traces, and 100 is at least 75 + 5: promote.",
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
