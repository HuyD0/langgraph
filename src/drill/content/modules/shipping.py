"""Shipping models and agents: Graduating, registering, promoting and canarying on Databricks."""

from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, module, practice, question, stack

MODULE = module('shipping', 'Shipping models and agents', 'Graduating, registering, promoting and canarying on Databricks.')

lesson(MODULE, 'graduation_gate',
    title='The graduation gate',
    learn=[
        'A common setup is a **shared experiment space**: one model deployment for everyone, with a spending limit and a rate limit for each person. That keeps trials cheap. But it is no place for an app people rely on: one busy experiment can use up the capacity, and nobody is named to fix things.',
        '**Graduation** moves an app out of that space onto production capacity, with limits sized for it. An app that graduates on enthusiasm alone can hit rate limits, a surprise bill or quiet failures in its first week.',
        'So graduate on evidence. The **proof of concept** (POC, a small trial build) measures it, and the team keeps it in a **graduation pack**.',
        'The pack holds six things: a named owner; the eval pass rate; whether every must-pass question passes (ones it must never get wrong); the cost per success, in dollars (the cost of all runs, failed ones included, divided by the runs that passed); the tokens a minute it needs at its busiest; and monitoring (alerts that tell the owner when it breaks).',
        "The **graduation gate** checks the pack against its **acceptance criteria** (the limits it must meet), written down before the POC started. It lists every check that fails, not just the first, so the team can fix them all in one round. The platform team then sizes the app's capacity from the same numbers.",
    ],
    example=example('One pack, checked against its criteria', """evidence = {
  "owner": "ana",
  "pass_rate": 0.86,        # limit 0.9
  "must_pass_ok": True,
  "cost_per_success": 0.12, # limit 0.1
  "peak_tpm": 75000,        # limit 90000
  "monitoring": True}
# Not yet, for 2 reasons:
# the pass rate is below 0.9,
# and the cost per success is
# above 0.1."""),
    check=question(
        'Before an app graduates, the platform team asks how many tokens a minute it needs at its busiest. Why?',
        [
            'To bill the team for the tokens its trial already used',
            'To check that its answers are right before real users see them',
            'To size the capacity it moves to so it is not rate limited on day one',
        ],
        answer=2,
        why="Graduation moves the app onto capacity sized for it, and its busiest minute says how many tokens a minute that capacity must allow. Checking answers is the pass rate's job.",
    ),
    angle=angle(
        pattern='Check every rule, keep every failure',
        text='The big idea: an app should graduate on evidence the trial measured, and the gate lists every check that fails so the team can fix them all in one round. Your code checks the six rules one after another. Each rule that fails adds its reason to a list, and the code never stops early. Exactly at a limit passes, because it uses `<` and `>`, not `<=` and `>=`. At the end, `sorted` puts the reasons in A to Z order, and an empty list means it graduates.',
        say='"I check [[every rule|the first rule|the main rule::Don\'t stop early.]] and collect all the reasons that fail, instead of stopping at the first one. That way the team can fix everything in [[one round|one line|one day::A single pass of fixes, not back and forth.]]."',
        classic=None,
    ),
    stack=stack('MLflow: log the pack on a run, read it back', """import mlflow

# The POC and the gate share
# one experiment.
mlflow.set_experiment("/Shared/hr-bot")

# The POC logs its pack on one run.
# tpm means tokens a minute.
# Count peak_tpm the way Azure AI Foundry's
# rate limit does: prompt tokens plus
# max_tokens for every call.
with mlflow.start_run(
        run_name="grad-pack",
        tags={"owner": "ana",
              "must_pass_ok": "yes",
              "monitoring": "yes"}):
    mlflow.log_metrics({
        "pass_rate": 0.86,
        "cost_per_success": 0.12,
        "peak_tpm": 75000})

# The gate reads the newest pack back.
runs = mlflow.search_runs(
    experiment_names=["/Shared/hr-bot"],
    filter_string="run_name = 'grad-pack'",
    order_by=["start_time DESC"],
    max_results=1)
row = runs.iloc[0]   # one pandas row
evidence = {
    "owner": row["tags.owner"],
    "pass_rate": row["metrics.pass_rate"],
    "peak_tpm": row["metrics.peak_tpm"],
    "monitoring":
        row["tags.monitoring"] == "yes",
    # ...the rest of the pack the same way
}"""),
    exercise=exercise(
        title='Check the Graduation Pack',
        topic='shipping',
        difficulty='easy',
        fn='graduation_gate',
        prompt="""Your function gets two things:

- `evidence`: what the POC measured, like `{"owner": "ana", "pass_rate": 0.86, "must_pass_ok": True, "cost_per_success": 0.12, "peak_tpm": 75000, "monitoring": True}`. `cost_per_success` is the cost of all runs, failed ones included, divided by the runs that passed, in dollars. `peak_tpm` is the tokens a minute (tpm) it needs at its busiest, bursts included.
- `criteria`: the acceptance criteria, the limits to meet, like `{"min_pass_rate": 0.9, "max_cost_per_success": 0.1, "capacity_tpm": 90000}`. `capacity_tpm` is the most tokens a minute the platform can give it.

Every rule that fails adds its reason:

- `"no owner"`: the owner is `""`.
- `"pass rate below the minimum"`: `pass_rate` is below `min_pass_rate`.
- `"a must-pass question fails"`: `must_pass_ok` is `False`.
- `"cost per success above the maximum"`: `cost_per_success` is above `max_cost_per_success`.
- `"peak tokens a minute above capacity"`: `peak_tpm` is above `capacity_tpm`.
- `"no monitoring"`: `monitoring` is `False`.

Exactly at a limit is fine. Return the reasons sorted A to Z. An empty list means it graduates.""",
        pattern='Check every rule, add a reason for each one that fails, and sort at the end.',
        target='one check per rule, then one sort',
        realworld='A shared experiment space keeps trials cheap, but an app people rely on needs an owner, alerts and capacity sized for it. A written gate turns "is it ready?" into a list the team can work through, and the platform team sizes the app\'s capacity from the same numbers.',
        practice=practice(
            intro='Check graduation packs the way the platform team does: every rule against the acceptance criteria written before the trial, and every failure listed.',
            explain='An app should graduate on evidence the trial measured, so you checked every rule against the acceptance criteria and listed every one that fails, so the team can fix them all in one round. Exactly at a limit passes, even one over doesn\'t, and the acceptance criteria stay where they were written before the trial.',
            pattern='Every check against criteria set first',
            realworld='When an app is ready to leave the shared experiment space, you bring its graduation pack to the platform team. The gate turns "is it ready?" into a list the team can fix in one round, and the same numbers size its capacity.',
            gotchas=[
                ['Stopping at the first failure', 'Stop at the first reason and the team fixes one thing, comes back, and only then finds the next. List every reason at once.'],
                ['Setting the criteria after the results', 'Write the acceptance criteria down before the POC runs. Criteria picked after seeing the numbers tend to move to fit them.'],
            ],
            asks=[
                ask('What does the gate send back for this pack?', ['Just "no owner", the first problem it finds', 'All three: no owner, no monitoring, a must-pass fails', 'Nothing: the numbers all meet the criteria'], answer=1,
                    evidence=evidence('code', title='A graduation pack', text="""evidence = {
  "owner": "",
  "pass_rate": 0.93,        # limit 0.9
  "must_pass_ok": False,
  "cost_per_success": 0.07, # limit 0.1
  "peak_tpm": 40000,        # capacity 75000
  "monitoring": False}"""),
                    clue='The gate checks every rule. Look past the numbers at the other three fields.',
                    why='The numbers are fine, but there\'s no owner, a must-pass question fails and nothing is watching it. The gate lists all three, so the team fixes them in one round.',
                    wrong=['The gate never stops early: the team would fix one thing, come back, and only then find the next.', None, 'The numbers are good, but three other rules fail.']),
                ask('Does sam\'s app graduate?', ['Yes: each number is right on its limit', 'No: a pass rate of 0.9 isn\'t above the minimum', 'No: the peak uses all of its capacity'], answer=0,
                    evidence=evidence('code', title='sam\'s pack', text="""evidence = {
  "owner": "sam",
  "pass_rate": 0.9,         # limit 0.9
  "must_pass_ok": True,
  "cost_per_success": 0.1,  # limit 0.1
  "peak_tpm": 75000,        # capacity 75000
  "monitoring": True}"""),
                    clue='Exactly at a limit is fine. Is any number below or above its limit?',
                    why='Each number sits exactly on its limit, and exactly at a limit passes. The pack is complete, so it graduates.',
                    wrong=[None, 'The minimum is 0.9, and 0.9 is not below 0.9.', '75000 is the capacity itself, not above it.']),
                ask('ana\'s peak is one token a minute over capacity. Does it graduate?', ['Yes: one token is a rounding error', 'Not yet: its peak is above capacity'], answer=1,
                    evidence=evidence('code', title='ana\'s pack', text="""evidence = {
  "owner": "ana",
  "pass_rate": 0.82,        # limit 0.8
  "must_pass_ok": True,
  "cost_per_success": 0.3,  # limit 0.5
  "peak_tpm": 30001,        # capacity 30000
  "monitoring": True}"""),
                    clue='Capacity is the most the platform can give it. What happens in its busiest minute?',
                    why='Above capacity is above capacity: in its busiest minute it would be rate limited on day one. Size the capacity up, or bring the peak down, then check again.',
                    wrong=['Capacity is a hard limit. Even one over means its busiest minute gets rate limited.', None]),
                ask('What do you say?', ['Fine: 0.86 meets a minimum of 0.85', 'Keep the minimum at 0.9 and fix what fails', 'Drop the pass-rate rule for this app'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"We missed the pass-rate minimum of 0.9 with 0.86. Let\'s move it to 0.85, since we\'re close."'),
                    clue='When were the acceptance criteria written down, and why then?',
                    why='Criteria picked after seeing the numbers tend to move to fit them. Keep 0.9 and fix what fails.',
                    wrong=['Moving the minimum to fit the result means the gate measures nothing.', None, 'Without a pass-rate rule, an app that is wrong half the time could graduate.']),
            ],
        ),
        starter="""def graduation_gate(evidence, criteria):
    # your code here
    pass
""",
        solution="""def graduation_gate(evidence, criteria):
    reasons = []
    if evidence["owner"] == "":
        reasons.append("no owner")
    if evidence["pass_rate"] < criteria["min_pass_rate"]:
        reasons.append("pass rate below the minimum")
    if not evidence["must_pass_ok"]:
        reasons.append("a must-pass question fails")
    if evidence["cost_per_success"] > criteria["max_cost_per_success"]:
        reasons.append("cost per success above the maximum")
    if evidence["peak_tpm"] > criteria["capacity_tpm"]:
        reasons.append("peak tokens a minute above capacity")
    if not evidence["monitoring"]:
        reasons.append("no monitoring")
    return sorted(reasons)
""",
        cases=[
            case({
                'owner': 'ana', 'pass_rate': 0.86, 'must_pass_ok': True,
                'cost_per_success': 0.12, 'peak_tpm': 75000, 'monitoring': True,
            }, {'min_pass_rate': 0.9, 'max_cost_per_success': 0.1, 'capacity_tpm': 90000},
                expected=['cost per success above the maximum', 'pass rate below the minimum'], sample=True),
            case({
                'owner': 'li', 'pass_rate': 0.95, 'must_pass_ok': True,
                'cost_per_success': 0.05, 'peak_tpm': 20000, 'monitoring': True,
            }, {'min_pass_rate': 0.9, 'max_cost_per_success': 0.1, 'capacity_tpm': 75000},
                expected=[]),
            case({
                'owner': 'sam', 'pass_rate': 0.9, 'must_pass_ok': True,
                'cost_per_success': 0.1, 'peak_tpm': 75000, 'monitoring': True,
            }, {'min_pass_rate': 0.9, 'max_cost_per_success': 0.1, 'capacity_tpm': 75000},
                expected=[]),
            case({
                'owner': '', 'pass_rate': 0.5, 'must_pass_ok': False,
                'cost_per_success': 0.4, 'peak_tpm': 90000, 'monitoring': False,
            }, {'min_pass_rate': 0.9, 'max_cost_per_success': 0.1, 'capacity_tpm': 75000},
                expected=[
                    'a must-pass question fails',
                    'cost per success above the maximum',
                    'no monitoring',
                    'no owner',
                    'pass rate below the minimum',
                    'peak tokens a minute above capacity',
                ]),
            case({
                'owner': '', 'pass_rate': 0.93, 'must_pass_ok': False,
                'cost_per_success': 0.07, 'peak_tpm': 40000, 'monitoring': False,
            }, {'min_pass_rate': 0.9, 'max_cost_per_success': 0.1, 'capacity_tpm': 75000},
                expected=['a must-pass question fails', 'no monitoring', 'no owner']),
            case({
                'owner': 'ana', 'pass_rate': 0.82, 'must_pass_ok': True,
                'cost_per_success': 0.3, 'peak_tpm': 30001, 'monitoring': True,
            }, {'min_pass_rate': 0.8, 'max_cost_per_success': 0.5, 'capacity_tpm': 30000},
                expected=['peak tokens a minute above capacity']),
        ],
        guided="""def graduation_gate(evidence, criteria):
    # Replace every ___ with real code, then run the tests.

    # Check every rule. Each one that fails adds a reason.
    reasons = []
    if evidence["owner"] == "":
        reasons.append("no owner")
    # Step 1: is pass_rate below criteria's min_pass_rate?
    if ___:
        reasons.append("pass rate below the minimum")
    if not evidence["must_pass_ok"]:
        reasons.append("a must-pass question fails")
    # Step 2: is cost_per_success above max_cost_per_success?
    if ___:
        reasons.append("cost per success above the maximum")
    if evidence["peak_tpm"] > criteria["capacity_tpm"]:
        reasons.append("peak tokens a minute above capacity")
    if not evidence["monitoring"]:
        reasons.append("no monitoring")
    # Step 3: return the reasons, sorted A to Z.
    return ___
""",
        fills=[
            'evidence["pass_rate"] < criteria["min_pass_rate"]',
            'evidence["cost_per_success"] > criteria["max_cost_per_success"]',
            'sorted(reasons)',
        ],
        concepts=[
            [
                'Dict access',
                '`evidence["pass_rate"]` gets one value from a dict by its key.',
                """song = {"title": "Hey", "mins": 3}
song["mins"]   # 3""",
            ],
            [
                'Below and above',
                '`<` means "below" and `>` means "above". A tie is neither, so a value exactly at the limit passes.',
                """18 < 20   # True
20 < 20   # False: a tie""",
            ],
            [
                'not',
                '`not` flips True and False. `if not done:` runs its block when `done` is False.',
                """raining = False
not raining   # True""",
            ],
            [
                'Empty text',
                '`""` is text with nothing in it. `name == ""` is True when there is no name.',
                """name = ""
name == ""   # True""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts x on the end of the list.',
                """names = []
names.append("Ana")   # ["Ana"]""",
            ],
            [
                'sorted',
                '`sorted(a_list)` gives a new list in order. Text goes A to Z.',
                """sorted(["pear", "apple"])
# ["apple", "pear"]""",
            ],
        ],
        byhand='The owner is "ana", so there is one. The pass rate 0.86 is below 0.9: add "pass rate below the minimum". must_pass_ok is True: fine. The cost per success 0.12 is above 0.1: add "cost per success above the maximum". The peak 75000 is not above 90000: fine. monitoring is True: fine. That makes two reasons. Sorted A to Z, "cost" comes before "pass". Return ["cost per success above the maximum", "pass rate below the minimum"].',
        why='Six quick checks, then one sort of a short list.',
        gotchas=[
            [
                'Stopping at the first failure',
                'Return after the first reason and the team fixes one thing, comes back, and only then finds the next. List every reason at once.',
            ],
            [
                'Setting the criteria after the results',
                'Write the acceptance criteria down before the POC runs. Criteria picked after seeing the numbers tend to move to fit them.',
            ],
        ],
    ),
)

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
            'To save storage in the registry',
            'A tiny gain is often just noise',
            'MLflow refuses a smaller gain',
        ],
        answer=1,
        why='A 1-point gain may vanish on new data. Swapping models has a cost, so make it worth it.',
    ),
    angle=angle(
        pattern='Keep the best so far',
        text="The big idea: only promote a challenger when it beats the champion by a meaningful margin on the same data. Your code first works out the threshold: the champion's score plus `min_gain`. Then it goes through the challengers, keeping the best so far, like holding the tallest card you have seen. A challenger takes over only if it clears the threshold and scores higher than the current best. A tie is not higher, so the earlier version stays, and if nobody clears the threshold the champion stays.",
        say='"A challenger only replaces the [[champion|newest model|test data::The version running now.]] if it wins by at least the [[minimum gain|same score|one point::A tiny win could just be luck.]]. Among those, the highest score wins, and a tie goes to the [[earlier|later|cheaper::The one that came first stays.]] version."',
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
        pattern='Keep the best so far, and let a challenger replace it only if it clears the threshold.',
        target='one pass over the challengers',
        realworld="MLflow's model registry uses aliases like `@champion` and `@challenger` for exactly this. Requiring a minimum gain stops you swapping models for noise-level differences, since every swap carries risk.",
        practice=practice(
            intro='Decide promotions the way a reviewer does: a challenger must beat the champion by the minimum gain, on the same data.',
            explain='Only promote a challenger when it beats the champion by a meaningful margin on the same data. You worked out the threshold from the champion\'s score and the minimum gain, kept the best challenger that cleared it, refused a score from a different test set, and rolled back by moving the alias.',
            pattern='Clear the threshold, then take the best',
            realworld='When a retrained model is ready, compare it with `@champion` on the same data, and move the alias only if it wins by the gain you set. If complaints spike afterwards, move the alias back.',
            asks=[
                ask('Which version should get the `@champion` alias?', ['Version 3: keep the champion', 'Version 4', 'Version 6'], answer=2,
                    evidence=evidence('code', title='The registry', text="""champion:     version 3, score 81
min_gain:     2
challengers:  version 4, score 84
              version 5, score 82
              version 6, score 86"""),
                    clue='A challenger must reach 81 plus 2. Of the ones that do, the highest score wins.',
                    why='The threshold is 83. Version 4 (84) and version 6 (86) clear it, version 5 (82) doesn\'t, and 86 is the highest.',
                    wrong=['Two challengers clear the threshold, so the champion is replaced.', 'Version 4 clears the threshold, but version 6 scores higher.', None]),
                ask('Version 4 scores one point more than the champion. Promote it?', ['Yes: it scores higher than the champion', 'No: keep version 3, since 82 doesn\'t reach 83'], answer=1,
                    evidence=evidence('code', title='The registry', text="""champion:     version 3, score 81
min_gain:     2
challengers:  version 4, score 82"""),
                    clue='Add the minimum gain to the champion\'s score.',
                    why='A one-point win can be noise, and every swap carries risk. It has to win by at least 2.',
                    wrong=['Better, but not by the minimum gain. A small win may vanish on new data.', None]),
                ask('What do you do with version 8?', ['Promote it: 91 clears the threshold by a long way', 'Score it on the same data as the champion first', 'Retrain version 3 on the new test set'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"Version 8 scored 91! It was tested on last month\'s test set, but that\'s similar enough."'),
                    clue='Scores are only comparable when they come from the same data.',
                    why='A score on a different test set isn\'t comparable. Log the dataset version with every metric, then compare on the same one.',
                    wrong=['91 on easier data could be worse than 81 on yours.', None, 'Nothing says version 3 needs retraining. The comparison just isn\'t fair yet.']),
                ask('You promoted version 6. An hour later, complaints spike. What is the fastest safe undo?', ['Point `@champion` back to version 3', 'Retrain version 3 and redeploy it', 'Change the code to load version 3\'s model URI'], answer=0,
                    evidence=evidence('code', title='What the promotion did', text="""@champion:  version 3  ->  version 6"""),
                    clue='Look at what the promotion actually moved.',
                    why='Promoting moved an alias, so rolling back is moving it back: instant, and nothing else changes.',
                    wrong=[None, 'Version 3 is still in the registry. Nothing needs retraining.', 'Editing code and redeploying is slow. The alias moves in one step.']),
            ],
        ),
        starter="""def promote_model(champion, challengers, min_gain):
    # your code here
    pass
""",
        solution="""def promote_model(champion, challengers, min_gain):
    threshold = champion["score"] + min_gain
    best = champion
    for challenger in challengers:
        score = challenger["score"]
        if score >= threshold and score > best["score"]:
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

    # Step 1: the threshold is the champion's score plus min_gain.
    threshold = ___
    # best starts as the champion (kept if none counts).
    best = champion
    for challenger in challengers:
        score = challenger["score"]
        # Step 2: keep it only if it reaches the threshold
        # and its score is higher than best["score"].
        if score >= threshold and ___:
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
        byhand="The champion is version 3 with 81. The threshold is 81 plus 2, so 83. Version 4 has 84. It reaches 83 and beats the best so far (81), so it becomes the best. Version 5 has 82. That is below 83, so skip it. Version 6 has 86. It reaches 83 and beats 84, so it becomes the best. Return 6.",
        why='One walk through the challengers.',
        gotchas=[
            [
                'Compare on the same data',
                "A challenger evaluated on a different test set isn't comparable. Log the dataset version with every metric.",
            ],
            [
                'Promote by alias, roll back by alias',
                'Pointing `@champion` at a new version is instant to undo, which is why aliases beat redeploying with a new model URI (the `models:/...` address your code loads).',
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
            'Wait a week to collect more data first',
            'Move its traffic back to 0% and look at its traces',
            'Switch everyone to it to get more data',
        ],
        answer=1,
        why="That's what rollback criteria (limits you set in advance that mean roll back) are for. Roll back first, then investigate.",
    ),
    angle=angle(
        pattern='Add up percents until you pass',
        text="The big idea: a canary release sends a small share of traffic to the new version, and using the user's id means one person always gets the same version. Your code takes the last two digits, `user_id % 100`, as a bucket from 0 to 99. Then it goes through the routes, adding each percent to a running total. The first route whose total is bigger than the bucket answers. With a 90 and 10 split, buckets 0 to 89 get the first version and 90 to 99 the second.",
        say='"I turn each user id into a number from 0 to 99, so a person always sees the [[same version|newest version|random version::Coming back tomorrow shouldn\'t change what they get.]]. Then I add up the route percents, and the first route whose [[running total|own percent|name::Keep adding as you go down the list.]] passes that number wins."',
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
                'Canary needs rollback criteria',
                "Decide in advance what makes you roll back: more errors, slower answers, or lower quality scores on the canary's traces. Then watch for it.",
            ],
        ],
    ),
)

# The rule from "Rolling out a new prompt", in the order the exercise checks it, drawn above
# its practice questions.
ROLLOUT_RULE = """rule, written before the canary:
  under 100 v3 traces         → keep testing
  10 or more points above v2  → promote v3
  below v2                    → roll back to v2
  otherwise                   → keep testing"""

lesson(MODULE, 'prompt_rollout',
    title='Rolling out a new prompt',
    learn=[
        'Before a new prompt version gets the `production` alias, first run an **offline evaluation**: score it on your eval set (your saved test questions) with `mlflow.genai.evaluate`, before any real user sees it. Then give it a small share of real traffic, as a canary.',
        'Tag every trace with the prompt version it used. Then you can compare versions on real questions and decide with a rule you wrote down first: promote, keep testing, or roll back.',
    ],
    example=example('Same traffic, two versions', """v2 (production): 300 of 400 passed → 75%
v3 (candidate):  90 of 100 passed  → 90%
rule: at least 100 traces and 10 points better → promote v3"""),
    check=question(
        'A candidate prompt passed 2 out of 2 traces. Should you promote it?',
        ['Yes: 2 out of 2 is a perfect score', 'Not yet: 2 traces is too few to tell', 'No: roll it back to the old prompt'],
        answer=1,
        why='With tiny samples, luck decides. Set a minimum number of traces before you compare.',
    ),
    angle=angle(
        pattern='Count passes per version, then compare',
        text='The big idea: tag every trace with its prompt version, then decide with a rule you wrote down first: promote, keep testing, or roll back. Your code keeps two dicts, small lookup tables from a version name to a number. One counts traces and one counts passes. If the new version has fewer than `min_traces` traces, it returns `"keep"` before any dividing. Otherwise it works out both pass rates as percents and checks the rules in order: promote, then roll back, then keep.',
        say='"I tag each trace with its [[prompt version|user name|time::Which wording of the prompt made this answer.]] and compare pass rates once the new one has [[enough traces|one trace|a good trace::A few results could just be luck.]]. I promote only on a gain I set in advance."',
        classic=None,
    ),
    stack=stack('Tag traces with the prompt version, then compare', """prod = mlflow.genai.load_prompt("prompts:/main.support.answer@production")
cand = mlflow.genai.load_prompt("prompts:/main.support.answer@candidate")

@mlflow.trace
def answer(question, user_id):
    prompt = cand if user_id % 100 < 10 else prod   # 10 in 100 users to the candidate
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
        practice=practice(
            intro='Decide a prompt canary the way a release owner does: read each version\'s pass rate against the rule you wrote down first.',
            explain='Tag every trace with its prompt version, then decide with a rule you wrote down first. You promoted only on the gain the rule asks for, rolled back a version that did worse, kept testing one that was better but not by enough, and refused a comparison where the two versions saw different questions.',
            pattern='Read the canary against the written rule',
            realworld='When you change a prompt in a live app, write the rule first: how many traces, and how many points better. Then give the new version a small share of traffic and let the rule decide: promote, keep testing or roll back.',
            asks=[
                ask('What does the rule say?', ['Promote v3', 'Keep testing', 'Roll back to v2'], answer=0,
                    evidence=evidence('code', title='The canary so far', text=ROLLOUT_RULE + """

v2 (production): 300 of 400 passed → 75%
v3 (candidate):  108 of 120 passed → 90%"""),
                    clue='Check the rule from the top: enough v3 traces, then how many points better.',
                    why='v3 has 120 traces, over the 100 needed, and 90% is 15 points above 75%. That clears the 10 the rule asks for.',
                    wrong=[None, 'It has enough traces and clears the gain, so the rule has an answer.', 'v3 is above v2, not below.']),
                ask('Same rule, a different canary. What does it say?', ['Promote v3', 'Keep testing', 'Roll back to v2'], answer=1,
                    evidence=evidence('code', title='Another canary', text=ROLLOUT_RULE + """

v2 (production): 300 of 400 passed → 75%
v3 (candidate):  112 of 140 passed → 80%"""),
                    clue='It has enough traces. Is it 10 points better, or below production?',
                    why='Better by 5 points, not 10, and not worse either. So it keeps its share of traffic until the rule says promote or roll back.',
                    wrong=['5 points better is short of the 10 the rule asks for.', None, 'v3 is above v2, not below.']),
                ask('Same rule, one more canary. What does it say?', ['Promote v3', 'Keep testing', 'Roll back to v2'], answer=2,
                    evidence=evidence('code', title='One more canary', text=ROLLOUT_RULE + """

v2 (production): 300 of 400 passed → 75%
v3 (candidate):  105 of 150 passed → 70%"""),
                    clue='Compare the candidate\'s rate with production\'s.',
                    why='v3 has enough traces and does worse than production, so it rolls back to v2.',
                    wrong=['It is below production, not 10 points above.', 'The rule has an answer for a version that does worse.', None]),
                ask('What do you say?', ['Promote: 92% clears the rule', 'Not yet: it only saw easy questions', 'Roll back the candidate to be safe'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"The candidate is at 92% on 120 traces, against 75% for production. Ship it! The canary only sent it password-reset questions, but still."'),
                    clue='Were the two versions answering the same kind of questions?',
                    why='Easy questions make any prompt look good. Compare versions on the same traffic with the same scorer, or the difference may come from the questions, not the prompt.',
                    wrong=['The number clears the rule, but it was measured on easier questions.', None, 'Nothing shows it is worse either. Make the comparison fair first.']),
            ],
        ),
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
        byhand='First count. old has 2 traces and 1 passed. new has 4 traces and 3 passed. Rule 1: new has 4 traces. 4 is not fewer than 4, so we can judge it. old: 1 of 2 passed, so 50 percent. new: 3 of 4 passed, so 75 percent. Rule 2: the threshold is 50 plus 10, so 60. 75 is at least 60. Return "promote".',
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
