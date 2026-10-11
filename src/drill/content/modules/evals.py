"""Evals: Measuring whether a change made your AI better or worse."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('evals', 'Evals', 'Measuring whether a change made your AI better or worse.')

lesson(MODULE, 'exact_match',
    title='Evaluating model answers',
    learn=[
        "An **eval** is a test set of inputs with expected outputs, plus a way to score answers. It's how you know whether a prompt or model change helped.",
        'Normalise before comparing, or formatting differences ("Paris." vs "paris") count as wrong. For open-ended answers, teams use an LLM judge with a clear rubric and check it against human labels.',
    ],
    example=example('Normalise both sides', """def norm(s):
    return ' '.join(s.lower().replace('.', '').split())"""),
    check=question(
        'Your model answers "Paris." and the expected answer is "paris". Your eval marks it wrong. What\'s the problem?',
        ['The model is wrong', "The comparison isn't normalised", 'The eval set is too small'],
        answer=1,
        why='Clean both strings the same way before comparing.',
    ),
    angle=angle(
        pattern='Pairwise comparison',
        text='zip the two lists and compare each pair once. Check for the empty case before dividing.',
        say='"I clean both sides with the same function, compare pairs with zip, and return 0 for an empty set instead of dividing by zero."',
        classic=None,
    ),
    stack=stack('MLflow: Correctness with expected answers', """from mlflow.genai.scorers import Correctness
data = [{"inputs": {"question": "Capital of France?"},
         "expectations": {"expected_response": "Paris"}}]
mlflow.genai.evaluate(data=data, predict_fn=my_app, scorers=[Correctness()])"""),
    exercise=exercise(
        title='Score Model Answers',
        topic='evals',
        difficulty='easy',
        fn='exact_match',
        prompt="""You're testing a model. You have its `predictions` and the correct `answers`, as two lists in the same order. Before comparing two strings, clean them up: make them lowercase, remove the characters `. , ! ?`, and squeeze runs of spaces down to single spaces (trimming the ends).

Return the share of predictions that match, rounded to 2 decimal places: 2 right out of 3 gives `0.67`. If there are no answers, return `0.0`.""",
        pattern='Clean both sides the same way before comparing. Guard against an empty list before dividing.',
        target='look at each pair once',
        realworld='Evals. "Paris." and "paris" are the same answer, and an eval that says otherwise makes a good model look bad.',
        starter="""def exact_match(predictions, answers):
    # your code here
    pass
""",
        solution="""def normalize(s):
    for ch in ".,!?":
        s = s.replace(ch, "")
    return " ".join(s.lower().split())

def exact_match(predictions, answers):
    if not answers:
        return 0.0
    hits = 0
    for p, a in zip(predictions, answers):
        if normalize(p) == normalize(a):
            hits += 1
    return round(hits / len(answers), 2)
""",
        cases=[
            case(['Paris.', '  london', 'Rome'], ['paris', 'London', 'Madrid'], expected=0.67, sample=True),
            case([], [], expected=0),
            case(['Yes!'], ['yes'], expected=1),
            case(['new   york'], ['New York'], expected=1),
            case(['4', 'five'], ['four', 'five'], expected=0.5),
        ],
        guided="""def normalize(s):
    # Step 1: remove . , ! ?
    for ch in ".,!?":
        s = s.replace(ch, "")
    # Step 2: lowercase, and squeeze the spaces.
    return " ".join(s.___().split())

def exact_match(predictions, answers):
    # Replace every ___ with real code, then run the tests.

    # Step 3: guard against an empty list.
    if not answers:
        return ___

    hits = 0
    for p, a in zip(___, ___):
        if normalize(p) == normalize(a):
            hits += 1

    # Step 4: share that matched, rounded to 2 places.
    return round(___ / len(answers), 2)
""",
        concepts=[
            [
                'zip',
                'Walks two lists side by side, giving you one item from each.',
                """for p, a in zip(['x', 'y'], ['x', 'z']):
    print(p == a)   # True, then False""",
            ],
            [
                'Squeezing spaces',
                "split() with no argument drops all extra spaces, and ' '.join puts single spaces back.",
                "' '.join('  new   york '.split())   # 'new york'",
            ],
            ['round', 'round(x, 2) keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
        ],
        byhand='"Paris." vs "paris": lowercase and drop the dot, both become paris. Match. "  london" vs "London": both become london. Match. "Rome" vs "Madrid": no. That\'s 2 matches out of 3, which is 0.67.',
        why='Each pair is cleaned and compared once.',
        gotchas=[
            ['Dividing by zero', 'An empty test set crashes the whole eval run at the last step. Check first.'],
            [
                'Exact match is strict',
                '"4" and "four" are both right. For open-ended answers, teams use an LLM as a judge with a clear rubric, and check the judge against human labels.',
            ],
            [
                'Randomness in evals',
                "Run with temperature 0 when you can, and run more than once. A score that moves by 5 points between identical runs isn't telling you much.",
            ],
        ],
    ),
)

lesson(MODULE, 'assign_splits',
    title='Dev, test and holdout sets',
    learn=[
        'An eval set for an LLM app is split three ways, and each part has one job. The **dev** set is for iterating: look at it as often as you like while you tune prompts. The **test** set is checked before a release, rarely, and you never tune against it. The **holdout** set is locked away for big decisions. Once you have looked at it and changed things because of what you saw, it is no longer honest, so replace it.',
        'Build the examples from three places: a fixed **golden** set you checked by hand, a sample of **recent real traffic**, and **past failures** you never want to see again. Give every version a name, like `faq-v4`, so results stay comparable.',
        "Then **stratify**: decide which groups behave differently (kinds of question, difficulty, questions that can't be answered, or for an agent, kinds of task) and deal each group's examples across the three sets. Every set then gets every group in the same proportions. A plain random split can leave a small group out of the test set altogether.",
        'Keep anything that must stay together, like all the questions from one user or about one document, inside a single set. That is the leakage rule from the Foundations module.',
    ],
    example=example('Dealing each group, like cards', """billing:  b1 b2 b3 b4 b5   → dev dev dev test holdout
shipping: s1 s2 s3 s4 s5   → dev dev dev test holdout
refunds:  r1 r2 r3 r4 r5   → dev dev dev test holdout
every set gets billing, shipping and refunds in the same proportions"""),
    check=question(
        'Your 300 examples include 15 refund-fraud questions. You split at random and the test set ends up with none. What went wrong?',
        [
            'The test set was too small',
            "The split wasn't stratified, so a small group could miss a set entirely",
            'Refund fraud questions are too hard to evaluate',
        ],
        answer=1,
        why='Dealing each group across the sets guarantees every set has some refund-fraud questions in the right proportion.',
    ),
    angle=angle(
        pattern='A counter per group',
        text='Keep a dict from each group to how many of its examples you have placed so far. Each example looks up its group, takes the next slot in the 3-1-1 pattern, and bumps the count. One pass over the examples.',
        say='"I stratify the eval set by question type, so every split has every type in proportion, and I keep one user\'s questions in one split to avoid leakage."',
        classic='group_anagrams',
    ),
    stack=stack('Spark: a stratified sample of every group', """# 20% of every group goes to test; the rest stays for dev and holdout
fractions = {g: 0.2 for g in ["billing", "shipping", "refunds"]}
test = df.sampleBy("group", fractions=fractions, seed=42)
rest = df.subtract(test)"""),
    exercise=exercise(
        title='Deal the Eval Set',
        topic='evals',
        difficulty='easy',
        fn='assign_splits',
        prompt="""`examples` is a list of dicts like `{"id": "q1", "group": "billing"}`, already shuffled.

Deal each group's examples, in the order they appear, into sets by this repeating pattern: `"dev"`, `"dev"`, `"dev"`, `"test"`, `"holdout"`. So a group's 1st, 2nd and 3rd examples go to dev, its 4th to test, its 5th to holdout, its 6th starts again at dev. Each group follows the pattern on its own.

Return a dict from each example's id to its set.""",
        pattern='Count per group as you go, and use the count to pick the next slot in the pattern.',
        target='one pass over the examples',
        realworld='Dealing by group gives every set the same mix of question types, which a random split only does on average. With small groups, "on average" often means "not this time".',
        starter="""def assign_splits(examples):
    # your code here
    pass
""",
        solution="""def assign_splits(examples):
    pattern = ["dev", "dev", "dev", "test", "holdout"]
    placed = {}
    result = {}
    for example in examples:
        group = example["group"]
        count = placed.get(group, 0)
        result[example["id"]] = pattern[count % len(pattern)]
        placed[group] = count + 1
    return result
""",
        cases=[
            case([
                {'id': 'b1', 'group': 'billing'},
                {'id': 's1', 'group': 'shipping'},
                {'id': 'b2', 'group': 'billing'},
                {'id': 'b3', 'group': 'billing'},
                {'id': 's2', 'group': 'shipping'},
                {'id': 'b4', 'group': 'billing'},
                {'id': 'b5', 'group': 'billing'},
            ], expected={'b1': 'dev', 's1': 'dev', 'b2': 'dev', 'b3': 'dev', 's2': 'dev', 'b4': 'test', 'b5': 'holdout'}, sample=True),
            case([], expected={}),
            case([{'id': 'q' + str(i), 'group': 'faq'} for i in range(1, 7)],
                 expected={'q1': 'dev', 'q2': 'dev', 'q3': 'dev', 'q4': 'test', 'q5': 'holdout', 'q6': 'dev'}),
            case([
                {'id': 'r1', 'group': 'refunds'},
                {'id': 'r2', 'group': 'refunds'},
                {'id': 'r3', 'group': 'refunds'},
                {'id': 'r4', 'group': 'refunds'},
            ], expected={'r1': 'dev', 'r2': 'dev', 'r3': 'dev', 'r4': 'test'}),
        ],
        guided="""def assign_splits(examples):
    # Replace every ___ with real code, then run the tests.
    pattern = ["dev", "dev", "dev", "test", "holdout"]
    placed = {}   # group -> how many of its examples are placed so far
    result = {}

    for example in examples:
        group = example["group"]
        # Step 1: how many of this group have we placed? 0 the first time.
        count = ___
        # Step 2: the count picks the slot; % wraps around after 5.
        result[example["id"]] = ___
        placed[group] = count + 1
    return result
""",
        fills=['placed.get(group, 0)', 'pattern[count % len(pattern)]'],
        concepts=[
            [
                '% (remainder)',
                'What is left over after dividing. It makes a count wrap around a pattern.',
                """0 % 5, 4 % 5, 5 % 5, 6 % 5   # 0, 4, 0, 1""",
            ],
        ],
        byhand='Billing appears as b1, b2, b3, b4, b5: dev, dev, dev, test, holdout. Shipping has its own count: s1 and s2 are its 1st and 2nd, so both go to dev.',
        why='One step per example, and each dict lookup is instant.',
        gotchas=[
            [
                'Small groups miss the late sets',
                'A group with only four examples never reaches holdout. Make sure every group you care about has enough examples, and merge or top up the tiny ones.',
            ],
            [
                'Shuffle once, then freeze',
                'Shuffle before dealing, with a fixed seed, and save the result as a named version. Re-shuffling every run quietly changes the sets.',
            ],
        ],
    ),
)

lesson(MODULE, 'stable_split',
    title="Splits that don't move",
    learn=[
        'Dealing questions into dev, test and holdout by position works for a fixed set. But real eval sets grow every week, and re-dealing would move old questions between splits: a question you tuned on could land in the holdout and quietly inflate it.',
        "So at scale, each question's split is decided by its **id alone**: turn the id into a number with a **hash**, take that number modulo 100, and give 0-59 to dev, 60-79 to test and 80-99 to holdout. The same id always lands in the same split, however many questions are added later.",
        'Hash the right id. To keep one customer or one conversation out of two splits (the leakage rule), hash the **customer or conversation id**, not the question id: then all of its questions land together.',
    ],
    example=example('Same id, same split, forever', """bucket("ticket-1001") = 72  -> test
bucket("ticket-1002") = 29  -> dev
bucket("ticket-1003") = 88  -> holdout
... a month later, 500 questions added ...
bucket("ticket-1001") = 72  -> still test"""),
    check=question(
        'Your eval set grows from 200 to 300 questions, and you re-deal all 300 by position. What can go wrong?',
        [
            'Nothing, the proportions stay the same',
            "Old questions can move between splits, so questions you tuned on can end up in the holdout",
            'The new questions all land in dev',
        ],
        answer=1,
        why='The holdout is only honest if nothing in it was ever looked at while tuning. A split that depends only on the id never moves.',
    ),
    angle=angle(
        pattern='Hashing to a bucket',
        text='Walk the characters once, folding each into a running number, then take the remainder. The same text always gives the same number.',
        say='"For a growing eval set I assign splits by hashing the id, and I hash the conversation id when questions from one conversation must stay together."',
        classic=None,
    ),
    stack=stack('Spark: a stable split column on a Delta table', """from pyspark.sql import functions as F

eval_df = eval_df.withColumn("bucket", F.pmod(F.xxhash64("conversation_id"), F.lit(100)))
eval_df = eval_df.withColumn("split", F.when(F.col("bucket") < 60, "dev")
                                        .when(F.col("bucket") < 80, "test").otherwise("holdout"))"""),
    exercise=exercise(
        title='A Split That Never Moves',
        topic='evals',
        difficulty='easy',
        fn='stable_split',
        prompt="""Return the split for an id, using only the id:

1. Start with `h = 0`. For each character `ch`, set `h = (h * 131 + ord(ch)) % 1000003`.
2. Mix it once more: `h = (h * h) % 1000003`.
3. Take `bucket = h % 100`. Return `"dev"` for 0-59, `"test"` for 60-79 and `"holdout"` for 80-99.""",
        pattern='Fold the characters into a number, then map the number to a bucket.',
        target='one pass over the characters of the id',
        realworld='Eval sets that grow from production traffic use hash-based splits, so that adding this week\'s examples never moves last month\'s.',
        starter="""def stable_split(item_id):
    # your code here
    pass
""",
        solution="""def stable_split(item_id):
    h = 0
    for ch in item_id:
        h = (h * 131 + ord(ch)) % 1000003
    h = (h * h) % 1000003
    bucket = h % 100
    if bucket < 60:
        return "dev"
    if bucket < 80:
        return "test"
    return "holdout"
""",
        cases=[
            case('ticket-1001', expected='test', sample=True),
            case('ticket-1002', expected='dev'),
            case('ticket-1003', expected='holdout'),
            case('billing-01', expected='holdout'),
            case('refund-01', expected='dev'),
        ],
        guided="""def stable_split(item_id):
    # Replace every ___ with real code, then run the tests.
    h = 0
    # Step 1: fold each character into the running number.
    for ch in item_id:
        h = ___
    # Step 2: mix once more, so similar ids land far apart.
    h = (h * h) % 1000003
    # Step 3: a bucket from 0 to 99, then the split.
    bucket = ___
    if bucket < 60:
        return "dev"
    if bucket < 80:
        return "test"
    return "holdout"
""",
        fills=['(h * 131 + ord(ch)) % 1000003', 'h % 100'],
        concepts=[
            [
                'ord',
                'Gives the number behind a character.',
                """ord("a")   # 97
ord("b")   # 98""",
            ],
        ],
        byhand='"ticket-1001" folds to a number whose square, modulo 1000003, ends in bucket 72. 72 is between 60 and 79, so it is test, and it always will be.',
        why='One step per character of the id.',
        gotchas=[
            [
                'Proportions are only approximate',
                'Hashing gives about 60/20/20 overall, but a small group can come out lopsided. Check the counts per group, and top up a thin group in the holdout by hand if you must.',
            ],
            [
                'Use a real hash in production',
                'This hand-written one keeps the exercise runnable in the browser. Real pipelines use a standard hash such as `xxhash64` or `md5` on the id.',
            ],
        ],
    ),
)

lesson(MODULE, 'weighted_score',
    title='Report each group, weighted by real traffic',
    learn=[
        'One overall score hides problems: billing can be at 95% while refunds fail half the time, and the average still looks fine. Report a score **for each group**, with how many examples it is based on.',
        'For the headline number, weight each group by its **share of real traffic**, not its share of the eval set. You deliberately gave small but important groups extra examples, which is right for measuring them, but it would distort a plain average.',
        'If a group shows up in traffic but not in the eval set, that is a blind spot, not a zero. The drift lesson later in this module is about noticing when that happens.',
    ],
    example=example('Same results, two different averages', """group     pass rate   eval examples   real traffic
billing      90%           50              70%
refunds      50%           50              30%

plain average of the eval set:  70%
weighted by real traffic:        0.9 × 0.7 + 0.5 × 0.3 = 78%"""),
    check=question(
        'Refund questions are 5% of real traffic but 30% of your eval set, and they score badly. What is the honest overall number?',
        [
            'The plain average over the eval set',
            "Each group's score weighted by its share of real traffic, reported next to the per-group scores",
            'The refund score, since it is the worst',
        ],
        answer=1,
        why='The headline should reflect what users experience. The per-group scores still show that refunds need work.',
    ),
    angle=angle(
        pattern='Weighted average',
        text='Multiply each score by its weight, add those up, and divide by the total weight. Two running totals in one pass. Dividing by the total weight means the weights do not have to add up to exactly 1.',
        say='"I report every group with its count, and I weight the headline number by production traffic, not by how I sampled the eval set."',
        classic=None,
    ),
    stack=stack('MLflow: a metric per group, plus the weighted one', """with mlflow.start_run(run_name="faq-v4-eval"):
    for group, rate in pass_rates.items():
        mlflow.log_metric(f"pass_rate.{group}", rate)
    mlflow.log_metric("pass_rate.weighted", weighted_score(pass_rates, traffic))"""),
    exercise=exercise(
        title='The Honest Headline Number',
        topic='evals',
        difficulty='easy',
        fn='weighted_score',
        prompt="""`pass_rates` maps each group to its pass rate on the eval set, like `{"billing": 0.9, "refunds": 0.5}`. `traffic` maps each group to its share of real traffic. Shares may be fractions or raw counts, so they don't have to add up to 1.

Return the overall pass rate weighted by traffic, over the groups in `pass_rates`, rounded to 3 decimal places. A group missing from `traffic` has weight 0. If the total weight is 0, return `0.0`.""",
        pattern='Two running totals: score times weight, and weight. Divide at the end.',
        target='one pass over the groups',
        realworld='Eval sets oversample rare but important cases on purpose. Weighting the summary by real traffic keeps the headline honest while the per-group numbers keep the rare cases visible.',
        starter="""def weighted_score(pass_rates, traffic):
    # your code here
    pass
""",
        solution="""def weighted_score(pass_rates, traffic):
    total = 0.0
    weight = 0.0
    for group in pass_rates:
        share = traffic.get(group, 0)
        total += pass_rates[group] * share
        weight += share
    if weight == 0:
        return 0.0
    return round(total / weight, 3)
""",
        cases=[
            case({'billing': 0.9, 'refunds': 0.5}, {'billing': 0.7, 'refunds': 0.3}, expected=0.78, sample=True),
            case({'billing': 0.9, 'refunds': 0.5}, {'billing': 700, 'refunds': 300}, expected=0.78),
            case({'a': 1.0, 'b': 0.8, 'c': 0.2}, {'a': 0.5, 'b': 0.25, 'c': 0.25}, expected=0.75),
            case({'faq': 0.64}, {'faq': 1}, expected=0.64),
            case({'new': 0.5}, {'old': 1.0}, expected=0.0),
        ],
        guided="""def weighted_score(pass_rates, traffic):
    # Replace every ___ with real code, then run the tests.
    total = 0.0
    weight = 0.0
    for group in pass_rates:
        # Step 1: this group's share of traffic, 0 if it has none.
        share = ___
        # Step 2: add score times weight, and the weight on its own.
        total += pass_rates[group] * share
        weight += share
    # Step 3: guard the zero case, then divide.
    if weight == 0:
        return 0.0
    return round(___, 3)
""",
        fills=['traffic.get(group, 0)', 'total / weight'],
        concepts=[
            [
                'Weighted average',
                'Each score counts in proportion to its weight.',
                """(0.9 * 7 + 0.5 * 3) / (7 + 3)   # 0.78""",
            ],
        ],
        byhand='Billing: 0.9 × 0.7 = 0.63. Refunds: 0.5 × 0.3 = 0.15. Total 0.78, total weight 1.0, so 0.78.',
        why='One step per group.',
        gotchas=[
            [
                'Report the groups too',
                'A good weighted number can still hide one group in trouble. Always show the per-group scores next to it.',
            ],
            [
                'Each group needs enough examples',
                'A per-group score on 8 examples is very rough. The "How many examples do you need?" lesson applies to every group on its own.',
            ],
        ],
    ),
)

lesson(MODULE, 'must_pass_gate',
    title='A must-pass set',
    learn=[
        "A new version can win on average and still break the one answer that matters most: the refund policy, the fraud warning, the medical disclaimer. An average can't see that.",
        "So keep a small **must-pass set**: the cases that can never get worse, chosen in the **Frame** stage, before any experiment, from what would be costly or embarrassing to get wrong. Add every serious production failure you fix, so it can't quietly come back.",
        "In **Evaluate** and again at **Ship**, check it first, separately from the overall score. If any must-pass case fails, the version doesn't ship, whatever its average says. That's a **release gate**.",
    ],
    example=example('Winning on average, failing the gate', """version B:  overall 91% (A was 88%)    ✓ better on average
must-pass:  14 of 15 pass                ✗ "fraud-03" now fails
verdict:    do not ship B until fraud-03 passes again"""),
    check=question(
        'Version B scores 4 points higher overall but fails one of your 15 must-pass questions. What happens?',
        [
            'Ship it: 4 points is a clear win',
            "It doesn't ship until that case passes: the gate comes before the average",
            'Remove that question from the must-pass set',
        ],
        answer=1,
        why='The must-pass set exists exactly for this. Moving a case out of it because it failed defeats the purpose.',
    ),
    angle=angle(
        pattern='Membership check over a short list',
        text='Walk the must-pass ids and look each one up in the results dict. A missing result counts as a failure, because "not tested" is not "passed".',
        say='"I keep a must-pass set as a release gate, checked before the overall score, and every fixed production failure gets added to it."',
        classic=None,
    ),
    stack=stack('MLflow: gate a release on the must-pass slice', """result = mlflow.genai.evaluate(data=must_pass_set, predict_fn=app_b, scorers=[correct])
if result.metrics["correct/mean"] < 1.0:
    raise SystemExit("must-pass gate failed: not promoting")"""),
    exercise=exercise(
        title='Check the Release Gate',
        topic='evals',
        difficulty='easy',
        fn='must_pass_gate',
        prompt="""`results` maps question ids to whether the new version passed them, like `{"fraud-03": False, "refund-01": True}`. `must_pass` is the list of ids that must never fail.

Return `[ship, failing]`: `failing` is the list of must-pass ids that did not pass, sorted, and `ship` is `True` only when that list is empty. An id missing from `results` counts as failing: if it wasn't tested, it didn't pass.""",
        pattern='Walk the must-pass ids, look each one up, and treat missing as failed.',
        target='one pass over the must-pass ids',
        realworld='Release pipelines run the must-pass set first and stop before the full eval if any case fails. It is fast, cheap and catches the regressions that matter most.',
        starter="""def must_pass_gate(results, must_pass):
    # your code here
    pass
""",
        solution="""def must_pass_gate(results, must_pass):
    failing = []
    for qid in must_pass:
        if not results.get(qid, False):
            failing.append(qid)
    failing.sort()
    return [len(failing) == 0, failing]
""",
        cases=[
            case({'fraud-03': False, 'refund-01': True, 'billing-07': True}, ['refund-01', 'fraud-03'], expected=[False, ['fraud-03']], sample=True),
            case({'a': True, 'b': True}, ['a', 'b'], expected=[True, []]),
            case({'a': True}, ['a', 'b'], expected=[False, ['b']]),
            case({'x': False}, [], expected=[True, []]),
            case({'z': False, 'y': False}, ['z', 'y'], expected=[False, ['y', 'z']]),
        ],
        guided="""def must_pass_gate(results, must_pass):
    # Replace every ___ with real code, then run the tests.
    failing = []
    for qid in must_pass:
        # Step 1: a missing id counts as failed, so default to False.
        if not ___:
            failing.append(qid)
    failing.sort()
    # Step 2: ship only if nothing failed.
    return [___, failing]
""",
        fills=['results.get(qid, False)', 'len(failing) == 0'],
        concepts=[
            [
                'A safe default',
                '`.get(key, default)` gives the default when the key is missing, so a missing result reads as False.',
                """results = {"a": True}
results.get("b", False)   # False""",
            ],
        ],
        byhand='refund-01 passed. fraud-03 failed. So failing is ["fraud-03"] and the version does not ship.',
        why='One look-up per must-pass id.',
        gotchas=[
            [
                'Keep it small and sharp',
                'Ten to fifty cases that truly must not break. A must-pass set of 500 turns into a second eval set that nobody can get fully green.',
            ],
            [
                'Flaky cases undermine the gate',
                'If a must-pass case passes on some runs and fails on others, run it several times and require it to pass every time, or fix what makes it flaky.',
            ],
        ],
    ),
)

lesson(MODULE, 'first_bad_version',
    title='Finding regressions',
    learn=[
        'A **regression** is a change that made things worse. With many prompt or model versions, re-running every eval is slow and costs money.',
        'If versions pass up to a point and fail after it, **bisect**: test the middle, keep the half that contains the change.',
    ],
    example=example('Bisecting 40 versions', """# test v20: passes -> problem is in v21..v40
# test v30: fails  -> problem is in v21..v30
# ... about 6 evals instead of 40"""),
    check=question(
        'You have 64 prompt versions and the newest fails. About how many evals does bisecting need?',
        ['6', '32', '64'],
        answer=0,
        why='Each eval halves the range: 64 → 32 → 16 → 8 → 4 → 2 → 1.',
    ),
    angle=angle(
        pattern='Binary search',
        text="Each check throws away half of what's left, so 1,000 versions take about 10 checks and a million take about 20. The classic bug is the boundary: whether you move to the middle or one past it.",
        say='"The passing versions all come before the failing ones, so I check the middle and throw away half each time. That needs only a handful of evals."',
        classic='binary_search',
    ),
    stack=stack('MLflow: one named run per version', """with mlflow.start_run(run_name="prompt-v17"):
    mlflow.set_tag("prompt_version", "17")
    mlflow.genai.evaluate(data=eval_set, predict_fn=app_v17, scorers=scorers)"""),
    exercise=exercise(
        title='Find the Change That Broke It',
        topic='evals',
        difficulty='easy',
        fn='first_bad_version',
        prompt="""You changed a prompt many times, and somewhere along the way the eval started failing. `passed` lists, for each version in order, whether it passes: all the passing versions come first, then all the failing ones.

Return the index of the first failing version, or `-1` if every version passes. Each eval costs money, so look at as few versions as possible: about 10 checks for 1,000 versions, not 1,000.""",
        pattern="The list is sorted (passes, then fails), so check the middle and throw away the half that can't contain the answer.",
        target='about 10 checks for 1,000 versions',
        realworld='Bisecting: finding which of 40 prompt or model changes broke an eval in about 6 runs instead of 40. `git bisect` does exactly this for code.',
        starter="""def first_bad_version(passed):
    # your code here
    pass
""",
        solution="""def first_bad_version(passed):
    lo, hi = 0, len(passed) - 1
    answer = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if passed[mid]:
            lo = mid + 1
        else:
            answer = mid
            hi = mid - 1
    return answer
""",
        cases=[
            case([True, True, False, False], expected=2, sample=True),
            case([True, True, True], expected=-1),
            case([False], expected=0),
            case([], expected=-1),
            case([
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ], expected=1000),
            case([True, False], expected=1),
        ],
        guided="""def first_bad_version(passed):
    # Replace every ___ with real code, then run the tests.

    lo, hi = 0, len(passed) - 1
    answer = -1   # best failing index found so far
    while lo <= hi:
        mid = (lo + hi) // 2
        if passed[mid]:
            # Step 1: mid passes, so the first failure is to its right.
            lo = ___
        else:
            # Step 2: mid fails. Remember it, then look left for an earlier one.
            answer = mid
            hi = ___
    return answer
""",
        fills=['mid + 1', 'mid - 1'],
        concepts=[
            [
                'Integer division',
                '`//` divides and rounds down, so the result works as an index.',
                '(0 + 9) // 2   # 4',
            ],
            [
                'Remember and keep looking',
                'When you find a failing version, it might not be the first. Save it, then search the left half.',
                """answer = mid
hi = mid - 1""",
            ],
        ],
        byhand='[pass, pass, fail, fail]. Middle is index 1: passes, so look right of it. Now indexes 2 to 3, middle 2: fails. Remember 2, look left: nothing left. Answer 2.',
        why="Each check halves what's left, so 1,000 versions take about 10 checks.",
        gotchas=[
            [
                'Flaky evals break bisecting',
                'If a version passes on one run and fails on the next, bisecting lands in the wrong place. Run each check more than once, or lower the randomness, before you trust it.',
            ],
            [
                'Version everything',
                'You can only bisect what you kept. Store each prompt version, model name and settings with every eval run, which is what MLflow runs are for.',
            ],
        ],
    ),
)

lesson(MODULE, 'judge_agreement',
    title='Checking your LLM judge',
    learn=[
        'An LLM judge is a model too: it can be wrong. Before trusting its scores, compare it with human labels on the same answers.',
        'Check passes and failures separately. A judge that passes everything looks accurate when most answers are good, and catches nothing.',
    ],
    example=example('Agreement on each side', """humans passed 8, failed 2
judge passed all 10
→ agrees on passes 100%, on failures 0%: useless for finding bugs"""),
    check=question(
        'Your judge agrees with humans 92% of the time overall. Is it good enough?',
        ['Yes', 'Not until you check its agreement on failures separately', 'No judge is ever good enough'],
        answer=1,
        why='Overall agreement hides a judge that never fails anything.',
    ),
    angle=angle(
        pattern='Split by label',
        text='One walk through the pairs with four counters.',
        say='"I measure the judge\'s true-positive and true-negative rates against human labels separately and require both above a threshold."',
        classic=None,
    ),
    stack=stack('scikit-learn: judge vs human labels', """from sklearn.metrics import confusion_matrix
tn, fp, fn, tp = confusion_matrix(human, judge).ravel()
pass_agreement = tp / (tp + fn)
fail_agreement = tn / (tn + fp)"""),
    exercise=exercise(
        title='Can You Trust Your Judge?',
        topic='evals',
        difficulty='easy',
        fn='judge_agreement',
        prompt="""An LLM judge grades answers pass/fail. Before trusting it, compare it with human labels on the same examples. `judge` and `human` are lists of `True`/`False`.

Return `[pass_agreement, fail_agreement, trusted]`: of the answers humans passed, the share the judge also passed; of the answers humans failed, the share the judge also failed (each rounded to 2 places, `0.0` if there are none); and `trusted` is `True` only if both are at least `0.9`.""",
        pattern='Split by the true label, then measure agreement on each side separately.',
        target='one walk through the pairs',
        realworld="A judge that passes everything agrees with humans 95% of the time when 95% of answers are good, and catches no failures at all. Checking each side separately, the way Hamel Husain recommends, exposes that. MLflow's `make_judge` judges can then be aligned to your experts' labels.",
        starter="""def judge_agreement(judge, human):
    # your code here
    pass
""",
        solution="""def judge_agreement(judge, human):
    pos = neg = pos_ok = neg_ok = 0
    for j, h in zip(judge, human):
        if h:
            pos += 1
            if j:
                pos_ok += 1
        else:
            neg += 1
            if not j:
                neg_ok += 1
    tpr = round(pos_ok / pos, 2) if pos else 0.0
    tnr = round(neg_ok / neg, 2) if neg else 0.0
    return [tpr, tnr, tpr >= 0.9 and tnr >= 0.9]
""",
        cases=[
            case([True, True, True, True, True, True, True, True, True, True], [True, True, True, True, True, True, True, True, False, False], expected=[1.0, 0.0, False], sample=True),
            case([], [], expected=[0.0, 0.0, False]),
            case([True, False, True, False], [True, False, True, False], expected=[1.0, 1.0, True]),
            case([True, True, False, False, False], [True, False, True, False, False], expected=[0.5, 0.67, False]),
        ],
        guided="""def judge_agreement(judge, human):
    # Replace every ___ with real code, then run the tests.

    pos = neg = pos_ok = neg_ok = 0
    for j, h in zip(judge, human):
        if h:
            pos += 1
            if j:
                pos_ok += 1
        else:
            # Step 1: humans failed it; did the judge fail it too?
            neg += 1
            if ___:
                neg_ok += 1
    tpr = round(pos_ok / pos, 2) if pos else 0.0
    tnr = round(neg_ok / neg, 2) if neg else 0.0
    # Step 2: trusted only if both sides agree well.
    return [tpr, tnr, ___]
""",
        fills=['not j', 'tpr >= 0.9 and tnr >= 0.9'],
        concepts=[['Counting with conditions', 'Several counters updated in one loop.', 'pos = neg = 0']],
        byhand='Humans passed 8 and failed 2. The judge passed all 10: it agrees on all 8 passes (1.0) but caught neither failure (0.0). Not trustworthy, despite agreeing 80% of the time overall.',
        why='One walk through the pairs.',
        gotchas=[
            [
                'Label a few dozen yourself first',
                "Error analysis starts with reading real outputs and labelling them. That's where the failure categories, and the judge's rubric, come from.",
            ],
            [
                'Re-check after changing the judge',
                'A new judge prompt or model needs re-checking against the same labels before its scores mean anything.',
            ],
        ],
    ),
)

lesson(MODULE, 'cohen_kappa',
    title='Agreement beyond chance',
    learn=[
        'Agreement can be high by luck. If 90% of answers are good, and a judge that never reads anything says "pass" 90% of the time at random, the two still agree on about 82% of answers (0.9 × 0.9 for both saying pass, plus 0.1 × 0.1 for both saying fail).',
        "**Cohen's kappa** subtracts the agreement you would expect by chance: kappa = (observed agreement − chance agreement) ÷ (1 − chance agreement). 1 means perfect agreement, 0 means no better than luck, and below 0 means worse than luck.",
        "Chance agreement comes from how often each side says pass: (judge's pass rate × humans' pass rate) + (judge's fail rate × humans' fail rate). As a common rough guide, above 0.6 is good and above 0.8 is very good. Use kappa alongside the pass-and-fail check from the previous lesson, not instead of it.",
    ],
    example=example('Kappa on ten answers', """humans: pass 8, fail 2      judge: pass 9, fail 1
they agree on 9 of 10      → observed 0.90
chance = 0.8 × 0.9 + 0.2 × 0.1 = 0.74
kappa  = (0.90 − 0.74) ÷ (1 − 0.74) ≈ 0.62"""),
    check=question(
        'Your judge agrees with humans 82% of the time, and kappa is 0.05. What does that tell you?',
        [
            'The judge is good: 82% is high',
            'The judge is barely better than guessing; the agreement mostly comes from most answers being good',
            'Kappa must be wrong when agreement is high',
        ],
        answer=1,
        why='When almost everything passes, a judge that also says pass almost every time agrees a lot without catching anything.',
    ),
    angle=angle(
        pattern='Count once, then a formula',
        text='One pass counts the agreements and each side\'s passes. Everything else is arithmetic on those three counts, with a guard for the case where chance agreement is already 1.',
        say='"I don\'t trust raw agreement for an LLM judge. I check Cohen\'s kappa so that agreement by luck doesn\'t count."',
        classic=None,
    ),
    stack=stack('scikit-learn and MLflow', """from sklearn.metrics import cohen_kappa_score

kappa = cohen_kappa_score(human_labels, judge_labels)
mlflow.log_metric("judge_kappa", kappa)"""),
    exercise=exercise(
        title="Cohen's Kappa",
        topic='evals',
        difficulty='medium',
        fn='cohen_kappa',
        prompt="""`human` and `judge` are lists of booleans of the same length (at least one item): whether a human, and an LLM judge, passed each answer.

Return Cohen's kappa, rounded to 2 decimal places:

- observed = the fraction of answers where they agree
- chance = (human pass rate × judge pass rate) + (human fail rate × judge fail rate)
- kappa = (observed − chance) ÷ (1 − chance)

If chance is exactly 1 (both always gave the same single label), return `1.0`.""",
        pattern='Count agreements and passes in one pass, then apply the formula.',
        target='one pass over the labels',
        realworld='Before letting an LLM judge gate releases, teams label a sample by hand and check kappa. A judge with high agreement but low kappa is just echoing the base rate.',
        starter="""def cohen_kappa(human, judge):
    # your code here
    pass
""",
        solution="""def cohen_kappa(human, judge):
    n = len(human)
    agree = 0
    human_pass = 0
    judge_pass = 0
    for h, j in zip(human, judge):
        if h == j:
            agree += 1
        if h:
            human_pass += 1
        if j:
            judge_pass += 1
    observed = agree / n
    p_human = human_pass / n
    p_judge = judge_pass / n
    chance = p_human * p_judge + (1 - p_human) * (1 - p_judge)
    if chance == 1:
        return 1.0
    return round((observed - chance) / (1 - chance), 2)
""",
        cases=[
            case([True] * 7 + [True, False, False], [True] * 7 + [True, True, False], expected=0.62, sample=True),
            case([True, False, True, False], [True, False, True, False], expected=1.0),
            case([True] * 8 + [False] * 2, [True] * 10, expected=0.0),
            case([True, False, True, False], [False, True, False, True], expected=-1.0),
            case([True, True, True], [True, True, True], expected=1.0),
            case([True, True, False, False, True, False], [True, False, False, True, True, False], expected=0.33),
        ],
        guided="""def cohen_kappa(human, judge):
    # Replace every ___ with real code, then run the tests.
    n = len(human)
    agree = 0
    human_pass = 0
    judge_pass = 0

    # Step 1: one pass to count agreements and each side's passes.
    for h, j in zip(human, judge):
        if ___:
            agree += 1
        if h:
            human_pass += 1
        if j:
            judge_pass += 1

    observed = agree / n
    p_human = human_pass / n
    p_judge = judge_pass / n

    # Step 2: agreement you'd get by luck: both pass, or both fail.
    chance = p_human * p_judge + ___
    if chance == 1:
        return 1.0
    # Step 3: how much of the possible improvement over luck did they get?
    return round((observed - chance) / (1 - chance), 2)
""",
        fills=['h == j', '(1 - p_human) * (1 - p_judge)'],
        concepts=[
            [
                'Chance agreement',
                'If two people label independently, they agree by luck when both happen to say pass, or both say fail.',
                """# human passes 80%, judge passes 90%
0.8 * 0.9 + 0.2 * 0.1   # 0.74""",
            ],
        ],
        byhand='Humans pass 8 of 10, the judge passes 9 of 10, and they agree on 9. Observed 0.9. Chance 0.8 × 0.9 + 0.2 × 0.1 = 0.74. Kappa (0.9 − 0.74) ÷ 0.26 ≈ 0.62.',
        why='One pass to count, then a fixed amount of arithmetic.',
        gotchas=[
            [
                'A judge that always passes scores 0',
                'It agrees with humans whenever the answer was good, which can be most of the time, yet kappa is 0 because it adds nothing beyond the base rate.',
            ],
            [
                'Small samples',
                'Kappa on 20 labels is rough. Label enough answers, including plenty of failures, before trusting it.',
            ],
        ],
    ),
)

lesson(MODULE, 'review_queue',
    title='Drafted labels, expert-confirmed',
    learn=[
        'With hundreds of questions, experts can\'t write every expected answer from scratch. Instead an LLM **drafts** the expected facts from the trace and its source article, and experts **confirm or correct** the drafts. Checking a draft is several times faster than writing one.',
        "Expert time is still the scarce part, so decide which drafts they see first. Highest: **must-pass** questions, where a wrong label is costly. Next: drafts where two independent drafting runs **disagree**, which usually means the question is ambiguous. Then: questions from **rare groups**, where each label carries more weight. Everything else can wait, or be spot-checked.",
        'Track how often experts change a draft. If it is rarely, you can sample fewer for review; if it is often, the drafting prompt needs work before it saves anyone time.',
    ],
    example=example('Who reviews what first', """id          must-pass  drafts agree  group     priority
refund-02      yes         yes       refund        3
billing-31     no          no        billing       2
fraud-44       no          yes       fraud (rare)  1
shipping-08    no          yes       shipping      0
→ with time for 3 reviews: refund-02, billing-31, fraud-44"""),
    check=question(
        'Experts changed only 2 of the last 150 drafted labels. What should you do?',
        [
            'Stop reviewing drafts entirely',
            'Review a smaller sample, keep must-pass and disagreeing drafts in the queue, and keep tracking the change rate',
            'Have experts rewrite every label anyway',
        ],
        answer=1,
        why='A low change rate earns a lighter review, not none. The must-pass and disputed drafts are still where a mistake costs most.',
    ),
    angle=angle(
        pattern='Score, then sort',
        text='Give each item a priority from a few simple rules, then sort by priority with a tie-break, and take the first few.',
        say='"I let an LLM draft expected answers and route expert review by risk: must-pass first, then disputed drafts, then rare groups."',
        classic=None,
    ),
    stack=stack('MLflow: drafts as expectations, then an expert labelling session', """mlflow.log_expectation(trace_id=tid, name="expected_facts", value=draft_facts,
                       source=AssessmentSource(source_type="LLM_JUDGE", source_id="drafter-v1"))
# experts then confirm or correct them in a labeling session (Databricks Review App)"""),
    exercise=exercise(
        title='Build the Review Queue',
        topic='evals',
        difficulty='easy',
        fn='review_queue',
        prompt="""Each item in `items` is a dict like `{"id": "refund-02", "must_pass": True, "drafts_agree": True, "group": "refund"}`. `rare_groups` is a list of groups with few examples, and `budget` is how many reviews the experts have time for.

Give each item a priority: **+3** if it is must-pass, **+2** if its drafts disagree, **+1** if its group is rare. Return the ids of the `budget` items with the highest priority, highest first; break ties by id, alphabetically.""",
        pattern='A score from simple rules, then sort by two keys and slice.',
        target='one pass to score, then a sort',
        realworld='Labelling teams route expert time this way, so the riskiest labels get human eyes first and the rest are checked by sampling.',
        starter="""def review_queue(items, rare_groups, budget):
    # your code here
    pass
""",
        solution="""def review_queue(items, rare_groups, budget):
    scored = []
    for item in items:
        priority = 0
        if item["must_pass"]:
            priority += 3
        if not item["drafts_agree"]:
            priority += 2
        if item["group"] in rare_groups:
            priority += 1
        scored.append((-priority, item["id"]))
    scored.sort()
    return [item_id for _, item_id in scored[:budget]]
""",
        cases=[
            case([
                {'id': 'shipping-08', 'must_pass': False, 'drafts_agree': True, 'group': 'shipping'},
                {'id': 'fraud-44', 'must_pass': False, 'drafts_agree': True, 'group': 'fraud'},
                {'id': 'refund-02', 'must_pass': True, 'drafts_agree': True, 'group': 'refund'},
                {'id': 'billing-31', 'must_pass': False, 'drafts_agree': False, 'group': 'billing'},
            ], ['fraud'], 3, expected=['refund-02', 'billing-31', 'fraud-44'], sample=True),
            case([], ['fraud'], 5, expected=[]),
            case([
                {'id': 'b', 'must_pass': False, 'drafts_agree': True, 'group': 'x'},
                {'id': 'a', 'must_pass': False, 'drafts_agree': True, 'group': 'x'},
            ], [], 5, expected=['a', 'b']),
            case([
                {'id': 'p', 'must_pass': True, 'drafts_agree': False, 'group': 'rare'},
                {'id': 'q', 'must_pass': True, 'drafts_agree': True, 'group': 'common'},
            ], ['rare'], 1, expected=['p']),
        ],
        guided="""def review_queue(items, rare_groups, budget):
    # Replace every ___ with real code, then run the tests.
    scored = []
    for item in items:
        priority = 0
        if item["must_pass"]:
            priority += 3
        # Step 1: disagreeing drafts and rare groups add to the priority.
        if ___:
            priority += 2
        if item["group"] in rare_groups:
            priority += 1
        # Step 2: a minus sign makes the highest priority sort first; the id breaks ties.
        scored.append((-priority, item["id"]))
    scored.sort()
    return ___
""",
        fills=['not item["drafts_agree"]', '[item_id for _, item_id in scored[:budget]]'],
        concepts=[
            [
                'Sorting pairs',
                'Pairs sort by their first item, then their second. Negating a number makes bigger numbers come first.',
                """sorted([(-2, "b"), (-3, "a"), (-2, "a")])   # [(-3, "a"), (-2, "a"), (-2, "b")]""",
            ],
        ],
        byhand='refund-02 is must-pass: 3. billing-31 has disagreeing drafts: 2. fraud-44 is in a rare group: 1. shipping-08 scores 0. With a budget of 3: refund-02, billing-31, fraud-44.',
        why='One pass to score each item, then a sort.',
        gotchas=[
            [
                'Drafts copy the app\'s mistakes',
                'If the drafting model reads the app\'s own answer, it can turn a wrong answer into a wrong label. Draft from the source article, not the answer.',
            ],
            [
                'Record who confirmed what',
                'Keep the draft, the expert\'s version and the expert\'s name on each label. It is the only way to measure the change rate and audit a label later.',
            ],
        ],
    ),
)

lesson(MODULE, 'change_report',
    title='Reading regressions and improvements',
    learn=[
        'When you compare two versions on the same questions, most questions get the same result from both. The informative ones are where they **disagree**: a **regression** is a question the new version gets wrong that the old one got right; an **improvement** is the reverse. Statisticians call these **discordant pairs**.',
        'Counting them decides the comparison (that is McNemar\'s rule, from the Experiment design module). **Reading** them explains it. For each one, open both traces side by side and find the first step where they differ: different documents retrieved, a different order, a different tool, an extra loop. Then label the cause in a few words.',
        'Count the causes in each direction. "6 improvements, mostly *moved the right document up*; 2 regressions, both *pushed a worse document above it*" tells you what the change did and what to fix next. This is called **error analysis**, and it happens in the **Evaluate** stage, after the runs you planned.',
    ],
    example=example('Regressions, improvements and their causes', """question         old  new  cause (from reading both traces)
return-label     ✗    ✓    reranker moved the right doc to the top      improvement
change-address   ✓    ✗    reranker pushed a policy doc above it        regression
refund-time      ✗    ✓    reranker moved the right doc to the top      improvement
charged-twice    ✗    ✗    (same result in both: not compared)

improvements 2: moved right doc up ×2     regressions 1: pushed worse doc up ×1"""),
    check=question(
        'The new version beats the old by 3 questions. Reading the improvements, every one has the same cause: "answer is shorter". What should you suspect?',
        [
            'The new version is clearly better',
            'The scorer may reward short answers, so check the scorer before trusting the win',
            'Nothing, causes do not matter once the count is in',
        ],
        answer=1,
        why='When every improvement shares a cause unrelated to the change you made, the measurement is often the thing that changed. Reading them is how you catch it.',
    ),
    angle=angle(
        pattern='Walking two dicts by the same keys, then counting',
        text='Go through the question ids once, compare the two results for each, and count regressions, improvements and their causes in dicts of running totals.',
        say='"I don\'t stop at the score: I read every regression and improvement, label why it changed, and count the causes each way. That tells me what the change really did."',
        classic='group_anagrams',
    ),
    stack=stack('MLflow: pull both traces for one question', """old = mlflow.search_traces(filter_string="tags.variant = 'v1' AND tags.qid = 'return-label'", return_type="list")[0]
new = mlflow.search_traces(filter_string="tags.variant = 'v2' AND tags.qid = 'return-label'", return_type="list")[0]
for trace in (old, new):
    for span in trace.search_spans(span_type="RETRIEVER"):
        print(span.outputs)   # where did the retrieved documents differ?"""),
    exercise=exercise(
        title='Count Regressions, Improvements and Their Causes',
        topic='evals',
        difficulty='medium',
        fn='change_report',
        prompt="""`old` and `new` map question ids to whether each version passed. Both have the same ids. `causes` maps some question ids to the cause you wrote after reading their traces.

Return a dict:

- `"improvements"`: how many questions `old` failed and `new` passed
- `"regressions"`: how many questions `old` passed and `new` failed
- `"improvement_causes"` and `"regression_causes"`: dicts counting the causes of each. A changed question with no entry in `causes` counts as `"unlabelled"`. Causes written for questions whose result did not change are ignored.""",
        pattern='One pass over the ids, two counters, and two dicts of cause counts.',
        target='one pass over the questions',
        realworld='Error analysis like this is how teams decide what to work on next: the most common cause among regressions is usually the next fix.',
        starter="""def change_report(old, new, causes):
    # your code here
    pass
""",
        solution="""def change_report(old, new, causes):
    report = {"improvements": 0, "regressions": 0, "improvement_causes": {}, "regression_causes": {}}
    for qid in old:
        if old[qid] == new[qid]:
            continue
        cause = causes.get(qid, "unlabelled")
        if new[qid]:
            report["improvements"] += 1
            counts = report["improvement_causes"]
        else:
            report["regressions"] += 1
            counts = report["regression_causes"]
        counts[cause] = counts.get(cause, 0) + 1
    return report
""",
        cases=[
            case({'q1': False, 'q2': True, 'q3': False, 'q4': False},
                 {'q1': True, 'q2': False, 'q3': True, 'q4': False},
                 {'q1': 'moved right doc up', 'q2': 'pushed worse doc up', 'q3': 'moved right doc up', 'q4': 'retrieval missed it'},
                 expected={'improvements': 2, 'regressions': 1, 'improvement_causes': {'moved right doc up': 2}, 'regression_causes': {'pushed worse doc up': 1}}, sample=True),
            case({'q1': True}, {'q1': True}, {}, expected={'improvements': 0, 'regressions': 0, 'improvement_causes': {}, 'regression_causes': {}}),
            case({'q1': False, 'q2': False}, {'q1': True, 'q2': True}, {'q1': 'better tool'},
                 expected={'improvements': 2, 'regressions': 0, 'improvement_causes': {'better tool': 1, 'unlabelled': 1}, 'regression_causes': {}}),
            case({}, {}, {}, expected={'improvements': 0, 'regressions': 0, 'improvement_causes': {}, 'regression_causes': {}}),
        ],
        guided="""def change_report(old, new, causes):
    # Replace every ___ with real code, then run the tests.
    report = {"improvements": 0, "regressions": 0, "improvement_causes": {}, "regression_causes": {}}
    for qid in old:
        # Step 1: same result in both versions? Nothing changed, skip it.
        if ___:
            continue
        cause = causes.get(qid, "unlabelled")
        # Step 2: the new version passed, so it's an improvement; otherwise a regression.
        if new[qid]:
            report["improvements"] += 1
            counts = report["improvement_causes"]
        else:
            report["regressions"] += 1
            counts = report["regression_causes"]
        # Step 3: add one to this cause's count.
        counts[cause] = ___
    return report
""",
        fills=['old[qid] == new[qid]', 'counts.get(cause, 0) + 1'],
        concepts=[
            [
                'Counting with a dict',
                'Look up the current count with a default of 0, then add one.',
                """counts = {}
counts["x"] = counts.get("x", 0) + 1   # {"x": 1}""",
            ],
        ],
        byhand='q1 and q3: old failed, new passed, so 2 improvements, both "moved right doc up". q2: old passed, new failed, so 1 regression, "pushed worse doc up". q4 failed in both, so its cause is ignored.',
        why='One step per question.',
        gotchas=[
            [
                'Check for flaky questions first',
                'If a question passes on one run and fails on another of the *same* version, its change between versions is noise. Run each version more than once and set flaky questions aside.',
            ],
            [
                'Write causes before counting',
                'Label causes while reading the traces, in your own words, then group similar labels. Deciding the categories first makes you see only what you expected.',
            ],
        ],
    ),
)

lesson(MODULE, 'sort_changes',
    title='Sorting changes before reading them',
    learn=[
        'With a few hundred questions, a comparison can produce sixty regressions and improvements: too many to read one by one. Sort them into buckets automatically first, then read a sample from each bucket.',
        'The most useful first cut for RAG comes straight from the traces: did the two versions send **different articles** to the answer step, or the **same articles** and the answer changed anyway? The first points at retrieval, the second at the prompt, the model or the scorer.',
        'Then read a handful from each bucket and label causes as usual. You get the error analysis for a fraction of the reading, and you know which part of the pipeline each cause belongs to.',
    ],
    example=example('Two buckets, from the traces alone', """question      old articles          new articles          bucket
billing-06    kb-12 kb-01 kb-02     kb-04 kb-09 kb-01     retrieval differed
shipping-07   kb-09 kb-03 kb-10     kb-10 kb-07 kb-09     retrieval differed
refund-11     kb-13 kb-16 kb-14     kb-13 kb-14 kb-16     same articles, different answer"""),
    check=question(
        'Most of your regressions are in the "same articles, different answer" bucket. Where should you look?',
        [
            'Retrieval settings',
            'The answer step: the prompt, the model or the scorer',
            'The eval set size',
        ],
        answer=1,
        why='If both versions got the same articles, retrieval did not cause the change. Something after it did.',
    ),
    angle=angle(
        pattern='Compare as sets, then bucket',
        text='Turn each article list into a set so the order does not matter, compare the two sets, and file the question in one of two lists.',
        say='"Before reading regressions I bucket them by whether retrieval changed, using the traces, then read a sample per bucket."',
        classic=None,
    ),
    stack=stack('MLflow: the articles each version sent, from the traces', """def sent(trace):
    steps = trace.search_spans(span_type="RERANKER") or trace.search_spans(span_type="RETRIEVER")
    return [d["doc_id"] for d in steps[0].outputs]"""),
    exercise=exercise(
        title='Bucket the Changes',
        topic='evals',
        difficulty='easy',
        fn='sort_changes',
        prompt="""Each item in `changed` is a question whose result changed between two versions: `{"qid": "billing-06", "old_docs": [...], "new_docs": [...]}`, the articles each version sent to the answer step.

Return `{"retrieval": [...], "answer": [...]}`: the qids where the two versions sent a different **set** of articles go in `"retrieval"`, the rest in `"answer"`. Order does not count as different. Sort both lists.""",
        pattern='Compare the two lists as sets, then file the qid.',
        target='one pass over the changed questions',
        realworld='Teams with large eval sets triage regressions like this every release, so they read thirty traces instead of three hundred.',
        starter="""def sort_changes(changed):
    # your code here
    pass
""",
        solution="""def sort_changes(changed):
    buckets = {"retrieval": [], "answer": []}
    for item in changed:
        if set(item["old_docs"]) != set(item["new_docs"]):
            buckets["retrieval"].append(item["qid"])
        else:
            buckets["answer"].append(item["qid"])
    buckets["retrieval"].sort()
    buckets["answer"].sort()
    return buckets
""",
        cases=[
            case([
                {'qid': 'billing-06', 'old_docs': ['kb-12', 'kb-01', 'kb-02'], 'new_docs': ['kb-04', 'kb-09', 'kb-01']},
                {'qid': 'refund-11', 'old_docs': ['kb-13', 'kb-16', 'kb-14'], 'new_docs': ['kb-13', 'kb-14', 'kb-16']},
                {'qid': 'shipping-07', 'old_docs': ['kb-09', 'kb-03', 'kb-10'], 'new_docs': ['kb-10', 'kb-07', 'kb-09']},
            ], expected={'retrieval': ['billing-06', 'shipping-07'], 'answer': ['refund-11']}, sample=True),
            case([], expected={'retrieval': [], 'answer': []}),
            case([{'qid': 'z', 'old_docs': ['a'], 'new_docs': ['a']}, {'qid': 'y', 'old_docs': [], 'new_docs': []}],
                 expected={'retrieval': [], 'answer': ['y', 'z']}),
        ],
        guided="""def sort_changes(changed):
    # Replace every ___ with real code, then run the tests.
    buckets = {"retrieval": [], "answer": []}
    for item in changed:
        # Step 1: compare as sets, so the order of the articles doesn't matter.
        if ___:
            buckets["retrieval"].append(item["qid"])
        else:
            buckets["answer"].append(item["qid"])
    buckets["retrieval"].sort()
    buckets["answer"].sort()
    return buckets
""",
        fills=['set(item["old_docs"]) != set(item["new_docs"])'],
        concepts=[
            [
                'Comparing as sets',
                'Two sets are equal when they hold the same items, in any order.',
                """set(["a", "b"]) == set(["b", "a"])   # True""",
            ],
        ],
        byhand='billing-06: different articles, so retrieval. refund-11: the same three articles in a different order, so answer. shipping-07: kb-03 was replaced by kb-07, so retrieval.',
        why='One set comparison per changed question.',
        gotchas=[
            [
                'Order can still matter',
                'Some models pay more attention to the first article. If "answer" regressions cluster where the order changed, add a third bucket for "same articles, new order".',
            ],
            [
                'Buckets are a start, not a cause',
                'They tell you which stage to read about. You still have to read a sample to find the actual cause.',
            ],
        ],
    ),
)

lesson(MODULE, 'mix_shift',
    title='Drift monitoring',
    learn=[
        'Your eval set is a snapshot. Real questions change: new products, new policies, new kinds of users.',
        'Watch the mix of production traffic against the eval set. When it shifts, eval scores stop predicting real quality, and the eval set needs refreshing.',
    ],
    example=example('The mix moved', """eval set:   billing 50% · shipping 30% · refunds 20%
production: billing 20% · shipping 30% · refunds 50%"""),
    check=question(
        "Eval scores are steady but users complain more. What's a likely explanation?",
        [
            'The users are wrong',
            'Production questions have drifted away from what the eval set covers',
            'The model got worse overnight',
        ],
        answer=1,
        why='The eval set no longer represents what users ask.',
    ),
    angle=angle(
        pattern='Compare distributions',
        text='One walk through the categories.',
        say='"I compare category shares between baseline and production and alert when the shift passes a threshold, then refresh the eval set."',
        classic=None,
    ),
    stack=stack('Databricks SQL: category mix this week', """SELECT category, count(*) / sum(count(*)) OVER () AS share
FROM main.support.questions
WHERE asked_at >= current_date() - INTERVAL 7 DAYS
GROUP BY category"""),
    exercise=exercise(
        title='Notice Drift',
        topic='evals',
        difficulty='easy',
        fn='mix_shift',
        prompt="""Your eval set reflects last quarter's questions. Production traffic changes. Compare the mix of question categories: `baseline` and `current` are lists of counts per category, in the same category order.

Turn each into shares (count divided by its total). The shift is half the sum of the absolute differences between matching shares: 0 means the same mix, 1 means completely different. Return it rounded to 2 places. If either total is 0, return `0.0`.""",
        pattern='Normalise both to shares, then compare share by share.',
        target='one walk through the categories',
        realworld='When the mix of real questions drifts from your eval set, eval scores stop predicting production quality. MLflow 3 production monitoring runs scorers on live traces; comparing category mix is a cheap first alarm that the eval set needs refreshing.',
        starter="""def mix_shift(baseline, current):
    # your code here
    pass
""",
        solution="""def mix_shift(baseline, current):
    tb, tc = sum(baseline), sum(current)
    if tb == 0 or tc == 0:
        return 0.0
    diff = 0
    for b, c in zip(baseline, current):
        diff += abs(b / tb - c / tc)
    return round(diff / 2, 2)
""",
        cases=[
            case([500, 300, 200], [200, 300, 500], expected=0.3, sample=True),
            case([1, 2], [0, 0], expected=0.0),
            case([10, 10], [20, 20], expected=0.0),
            case([1, 0], [0, 1], expected=1.0),
        ],
        guided="""def mix_shift(baseline, current):
    # Replace every ___ with real code, then run the tests.

    tb, tc = sum(baseline), sum(current)
    if tb == 0 or tc == 0:
        return 0.0
    diff = 0
    for b, c in zip(baseline, current):
        # Step 1: compare shares, not raw counts.
        diff += abs(___)
    # Step 2: half the total difference.
    return round(___, 2)
""",
        fills=['b / tb - c / tc', 'diff / 2'],
        concepts=[['abs', 'Distance from zero, ignoring the sign.', 'abs(-0.3)   # 0.3']],
        byhand='Baseline shares: 50%, 30%, 20%. Current: 20%, 30%, 50%. Differences: 30, 0, 30 points. Half of 60 is 30: a 0.3 shift.',
        why='One walk through the categories.',
        gotchas=[
            [
                'Categories come from somewhere',
                'To compare mixes you need to categorise questions, often with a cheap classifier or ai_classify. Keep that step stable, or it causes drift itself.',
            ],
            [
                'Refresh the eval set on purpose',
                'When the mix shifts, sample new real questions into the eval set, and keep the old ones to catch regressions.',
            ],
        ],
    ),
)
