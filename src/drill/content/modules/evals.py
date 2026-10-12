"""Evals: Measuring whether a change made your AI better or worse."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('evals', 'Evals', 'Measuring whether a change made your AI better or worse.')

lesson(MODULE, 'exact_match',
    title='Evaluating model answers',
    learn=[
        "An **eval** is a test set of inputs with expected outputs, plus a way to score answers. It's how you know whether a prompt or model change helped.",
        'Normalise (clean) both sides before comparing, or formatting differences ("Paris." vs "paris") count as wrong. In the exercise, cleaning means: make it lowercase, remove `.` `,` `!` and `?`, and trim spaces off both ends. For open-ended answers, teams use an **LLM judge** (a second model that grades each answer) with a clear **rubric** (written grading rules), and check it against human labels.',
    ],
    example=example('Cleaning one answer', """'Paris.'.replace('.', '')   # 'Paris'
'Paris'.lower()             # 'paris'
'  london '.strip()         # 'london'"""),
    check=question(
        'Your model answers "Paris." and the expected answer is "paris". Your eval marks it wrong. What\'s the problem?',
        ["The comparison isn't normalised", 'The model is wrong', 'The eval set is too small'],
        answer=0,
        why='Clean both strings the same way before comparing.',
    ),
    angle=angle(
        pattern='Clean both sides, then compare',
        text='The big idea: clean both the answer and the expected answer before comparing, so "Paris." and "paris" count as a match. Your code has one helper, `normalize`, that removes the marks, makes the text lowercase and trims spaces. `zip` pairs each prediction with its answer, like matching left and right shoes. The code counts the pairs that match after cleaning and divides by the number of answers. It checks for an empty list first, because dividing by zero would crash.',
        say='"I clean both sides with the same function, compare each pair, and return the share that match. An empty set returns 0 instead of dividing by zero."',
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
        prompt="""Your function gets two things:

- `predictions`: the model's answers, a list of strings like `["Paris.", "Rome"]`.
- `answers`: the correct answers in the same order, like `["paris", "Madrid"]`.

Clean every string before comparing it: make it lowercase, remove the marks `.` `,` `!` `?`, and trim spaces off both ends. So `"Paris."` becomes `"paris"`.

Return the share of predictions that match their answer after cleaning, rounded to 2 decimal places. 2 matches out of 3 gives `0.67`. If there are no answers, return `0.0`.""",
        pattern='Clean both sides the same way before comparing. Guard against an empty list before dividing.',
        target='look at each pair once',
        realworld='Evals. "Paris." and "paris" are the same answer, and an eval that says otherwise makes a good model look bad.',
        starter="""def exact_match(predictions, answers):
    # your code here
    pass
""",
        solution="""def normalize(text):
    for mark in ".,!?":
        text = text.replace(mark, "")
    return text.lower().strip()

def exact_match(predictions, answers):
    if len(answers) == 0:
        return 0.0
    hits = 0
    for pred, answer in zip(predictions, answers):
        if normalize(pred) == normalize(answer):
            hits += 1
    return round(hits / len(answers), 2)
""",
        cases=[
            case(['Paris.', '  london', 'Rome'], ['paris', 'London', 'Madrid'], expected=0.67, sample=True),
            case([], [], expected=0.0),
            case(['Yes!'], ['yes'], expected=1.0),
            case(['New York? '], ['new york'], expected=1.0),
            case(['4', 'five'], ['four', 'five'], expected=0.5),
        ],
        guided="""# Replace every ___ with real code, then run the tests.

# Cleans one string: "Paris." gives "paris".
def normalize(text):
    # Remove the marks . , ! and ? (done for you).
    for mark in ".,!?":
        text = text.replace(mark, "")
    # Step 1: make it lowercase, then trim the spaces
    # off both ends.
    return ___

def exact_match(predictions, answers):
    # No answers: nothing to score.
    if len(answers) == 0:
        return 0.0

    hits = 0
    for pred, answer in zip(predictions, answers):
        # Step 2: clean both with normalize(...),
        # then compare them with ==.
        if ___:
            hits += 1

    # Step 3: matches divided by how many answers,
    # rounded to 2 places.
    return round(___, 2)
""",
        fills=['text.lower().strip()', 'normalize(pred) == normalize(answer)', 'hits / len(answers)'],
        concepts=[
            [
                'Cleaning text',
                '`for mark in ".,!?":` visits each character in turn. `.replace(a, b)` swaps every `a` for `b`. `.lower()` makes text lowercase. `.strip()` trims spaces off both ends.',
                """'Hi!'.replace('!', '')   # 'Hi'
'  Hi '.lower().strip()   # 'hi'""",
            ],
            [
                'zip',
                'Walks two lists side by side, giving you one item from each.',
                """for x, y in zip([1, 2], [1, 5]):
    print(x == y)   # True, then False""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
        ],
        byhand='Pair 1: "Paris." cleans to "paris", and "paris" stays "paris". A match. Pair 2: "  london" and "London" both clean to "london". A match. Pair 3: "Rome" and "Madrid" clean to "rome" and "madrid". No match. That is 2 matches out of 3 answers. 2 divided by 3 is 0.666..., which rounds to 0.67.',
        why='Each pair is cleaned and compared once.',
        gotchas=[
            ['Dividing by zero', 'An empty test set crashes the whole eval run at the last step. Check first.'],
            [
                'Exact match is strict',
                '"4" and "four" are both right. For open-ended answers, teams use an LLM as a judge with a clear rubric, and check the judge against human labels.',
            ],
            [
                'Randomness in evals',
                "Run with temperature 0 (the setting for how random the model's wording is; 0 is the least random) when you can, and run more than once. A score that moves by 5 points between identical runs isn't telling you much.",
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
            'Refund fraud questions are too hard to evaluate',
            "The split wasn't stratified, so a small group could miss a set entirely",
        ],
        answer=2,
        why='Dealing each group across the sets guarantees every set has some refund-fraud questions in the right proportion.',
    ),
    angle=angle(
        pattern='A counter per group',
        text="The big idea: deal each group's examples across dev, test and holdout, so every set gets every group in the same proportions. Your code keeps a dict from each group to how many of its examples it has placed so far. Each example looks up its group's count and takes that slot in the pattern: 3 dev, 1 test, 1 holdout. `count % 5` is the remainder after dividing by 5, so the 6th example starts again at dev. It is like dealing cards, with a separate deck for each group.",
        say='"I stratify the eval set by group, so every split has every group in proportion. I keep one user\'s questions in one split to avoid leakage."',
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
        prompt="""Your function gets `examples`: a list of eval examples, already shuffled. Each one is a dict like `{"id": "b1", "group": "billing"}`.

Deal each group's examples, in the order they appear, using this repeating pattern: `"dev"`, `"dev"`, `"dev"`, `"test"`, `"holdout"`. Each group keeps its own count. So a group's 1st, 2nd and 3rd examples go to dev, its 4th to test and its 5th to holdout. Its 6th starts again at dev.

Return a dict from each example's id to its set, like `{"b1": "dev"}`.""",
        pattern='Count per group as you go, and use the count to pick the next slot in the pattern.',
        target='one walk through the examples',
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
        result[example["id"]] = pattern[count % 5]
        placed[group] = count + 1
    return result
""",
        cases=[
            case([
                {'id': 'b1', 'group': 'billing'},
                {'id': 'r1', 'group': 'refunds'},
                {'id': 'b2', 'group': 'billing'},
                {'id': 'b3', 'group': 'billing'},
                {'id': 'b4', 'group': 'billing'},
                {'id': 'b5', 'group': 'billing'},
            ], expected={'b1': 'dev', 'r1': 'dev', 'b2': 'dev', 'b3': 'dev', 'b4': 'test', 'b5': 'holdout'}, sample=True),
            case([
                {'id': 'b1', 'group': 'billing'},
                {'id': 's1', 'group': 'shipping'},
                {'id': 'b2', 'group': 'billing'},
                {'id': 's2', 'group': 'shipping'},
                {'id': 'b3', 'group': 'billing'},
                {'id': 's3', 'group': 'shipping'},
                {'id': 's4', 'group': 'shipping'},
            ], expected={'b1': 'dev', 's1': 'dev', 'b2': 'dev', 's2': 'dev', 'b3': 'dev', 's3': 'dev', 's4': 'test'}),
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
    placed = {}   # group -> how many placed so far
    result = {}

    for example in examples:
        group = example["group"]
        # Step 1: how many of this group are placed
        # already? Use 0 if the group is new.
        count = ___
        # Step 2: use the count to pick from the pattern.
        # pattern[0] is the 1st slot, and a new group's
        # count is 0. % 5 starts again after the 5th.
        result[example["id"]] = ___
        placed[group] = count + 1
    return result
""",
        fills=['placed.get(group, 0)', 'pattern[count % 5]'],
        concepts=[
            [
                'dict.get with a default',
                '`d.get(key, 0)` gives the value for `key`, or 0 when the key is not in the dict yet.',
                """seen = {"a": 2}
seen.get("a", 0)   # 2
seen.get("b", 0)   # 0""",
            ],
            [
                '% (remainder)',
                '`a % b` is what is left over after dividing a by b. It makes a count wrap back to the start of a pattern.',
                """colors = ["red", "blue"]
colors[2 % 2]   # "red", as 2 % 2 is 0
colors[3 % 2]   # "blue", as 3 % 2 is 1""",
            ],
        ],
        byhand='b1 is billing\'s 1st: dev. r1 is refunds\' 1st, since refunds has its own count: dev. b2 is billing\'s 2nd: dev. b3 is billing\'s 3rd: dev. b4 is billing\'s 4th: test. b5 is billing\'s 5th: holdout. So b1, r1, b2 and b3 map to "dev", b4 to "test" and b5 to "holdout".',
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
        "So at scale, each question's split is decided by its **id alone**: turn the id into a number with a **hash**, take the remainder after dividing that number by 100 (`% 100`), and give 0 to 59 to dev, 60 to 79 to test and 80 to 99 to holdout. The same id always lands in the same split, however many questions are added later.",
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
        pattern='Turn the id into a bucket',
        text="The big idea: decide each question's split from its id alone, so old questions never move when new ones are added. Your code calls `hash_id`, which turns the id into a big number. The same id always gives the same number. `% 100` keeps the remainder after dividing by 100, a bucket from 0 to 99. Buckets under 60 go to dev, 60 to 79 go to test, and the rest go to holdout. It is like sorting letters by the last two digits of a house number.",
        say='"For a growing eval set I pick the split by hashing the id. I hash the conversation id when its questions must stay together."',
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
        prompt="""Your function gets `item_id`, one question's id like `"ticket-1001"`, and returns its split: `"dev"`, `"test"` or `"holdout"`.

A helper, `hash_id`, is already written for you. It turns an id into a big number, and the same id always gives the same number. You don't need to change it or follow how it works.

- Call `hash_id(item_id)` to get the number.
- Keep the remainder after dividing it by 100 (`number % 100`). That is the bucket, from 0 to 99.
- Return `"dev"` for buckets 0 to 59, `"test"` for 60 to 79 and `"holdout"` for 80 to 99.""",
        pattern='Turn the id into a number, keep a bucket from 0 to 99, then pick the split by range.',
        target='one hash, then two checks',
        realworld='Eval sets that grow from production traffic use hash-based splits, so that adding this week\'s examples never moves last month\'s.',
        starter="""def hash_id(item_id):
    # Given, no need to read it: turns an id
    # into a big number. The same id always
    # gives the same number.
    h = 0
    for ch in item_id:
        h = (h * 131 + ord(ch)) % 1000003
    return (h * h) % 1000003

def stable_split(item_id):
    # your code here
    pass
""",
        solution="""def hash_id(item_id):
    h = 0
    for ch in item_id:
        h = (h * 131 + ord(ch)) % 1000003
    return (h * h) % 1000003

def stable_split(item_id):
    number = hash_id(item_id)
    bucket = number % 100
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
        guided="""# Replace every ___ with real code, then run the tests.

def hash_id(item_id):
    # Given, no need to read it: turns an id
    # into a big number. The same id always
    # gives the same number.
    h = 0
    for ch in item_id:
        h = (h * 131 + ord(ch)) % 1000003
    return (h * h) % 1000003

def stable_split(item_id):
    # Step 1: turn the id into a number with hash_id.
    number = ___
    # Step 2: the remainder after dividing by 100.
    # It is always from 0 to 99.
    bucket = ___
    # Step 3: 0 to 59 is dev, 60 to 79 is test,
    # and 80 to 99 is holdout.
    if bucket < 60:
        return "dev"
    if bucket < ___:
        return "test"
    return "holdout"
""",
        fills=['hash_id(item_id)', 'number % 100', '80'],
        concepts=[
            [
                '% 100 (remainder)',
                '`n % 100` is what is left over after dividing `n` by 100. For a whole number that is its last two digits, so it is always from 0 to 99.',
                """1234 % 100   # 34
7 % 100      # 7""",
            ],
            [
                'return stops the function',
                '`return` ends the function straight away. So a later `if` only runs when the earlier ones were false. Here `age < 20` only sees ages 13 and up.',
                """if age < 13: return 'child'
if age < 20: return 'teen'
return 'adult'""",
            ],
        ],
        byhand='hash_id("ticket-1001") gives 683372. The remainder after dividing by 100 is its last two digits, so the bucket is 72. 72 is not below 60, but it is below 80, so the split is "test". The same id gives 683372 every time, so it will always be "test".',
        why='One hash and two checks per id.',
        gotchas=[
            [
                'Proportions are only approximate',
                'Hashing gives about 60 dev, 20 test and 20 holdout out of every 100 questions, but a small group can come out lopsided. Check the counts per group, and top up a thin group in the holdout by hand if you must.',
            ],
            [
                'Use a real hash in production',
                'The hand-written `hash_id` keeps the exercise runnable in the browser. Real pipelines use a standard hash such as `xxhash64` or `md5` on the id.',
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
weighted by real traffic:        78%
  (0.9 times 0.7, plus 0.5 times 0.3)"""),
    check=question(
        'Refund questions are 5% of real traffic but 30% of your eval set, and they score badly. What is the honest overall number?',
        [
            "Each group's score weighted by its share of real traffic, reported next to the per-group scores",
            'The plain average over the eval set',
            'The refund score, since it is the worst',
        ],
        answer=0,
        why='The headline should reflect what users experience. The per-group scores still show that refunds need work.',
    ),
    angle=angle(
        pattern='A weighted average',
        text="The big idea: the headline score should count each group as much as real users meet it, not as much as your eval set happens to test it. Your code multiplies each group's score by its share of traffic, adds those up, and divides by the total traffic. It is like a school average where bigger classes count for more. Dividing by the total means the traffic can be given as shares like 0.7 or as counts like 700.",
        say='"I report a score for every group, and I weight the overall number by each group\'s share of real traffic, not by how many eval examples it has."',
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
        prompt="""Your function gets two things, with the same groups in both:

- `pass_rates`: each group's pass rate on the eval set, like `{"billing": 0.9, "refunds": 0.5}`.
- `traffic`: each group's share of real traffic, like `{"billing": 0.7, "refunds": 0.3}`. The traffic numbers may be shares like `0.7` or counts like `700`, so they don't always add up to 1. That is why you divide by their total at the end.

For each group, multiply its pass rate by its traffic number, and add these up. Then divide by the total of all the traffic numbers. Return the result rounded to 2 decimal places.""",
        pattern='Two running totals: pass rate times share, and the shares. Divide at the end.',
        target='one walk through the groups',
        realworld='Eval sets oversample rare but important cases on purpose. Weighting the summary by real traffic keeps the headline honest while the per-group numbers keep the rare cases visible.',
        starter="""def weighted_score(pass_rates, traffic):
    # your code here
    pass
""",
        solution="""def weighted_score(pass_rates, traffic):
    total = 0
    weight = 0
    for group in pass_rates:
        total += pass_rates[group] * traffic[group]
        weight += traffic[group]
    return round(total / weight, 2)
""",
        cases=[
            case({'billing': 0.9, 'refunds': 0.5}, {'billing': 0.7, 'refunds': 0.3}, expected=0.78, sample=True),
            case({'billing': 0.9, 'refunds': 0.5}, {'billing': 700, 'refunds': 300}, expected=0.78),
            case({'billing': 0.9, 'refunds': 0.5}, {'billing': 1, 'refunds': 1}, expected=0.7),
            case({'a': 1.0, 'b': 0.8, 'c': 0.2}, {'a': 0.5, 'b': 0.25, 'c': 0.25}, expected=0.75),
            case({'faq': 0.64}, {'faq': 1}, expected=0.64),
        ],
        guided="""def weighted_score(pass_rates, traffic):
    # Replace every ___ with real code, then run the tests.
    total = 0    # pass rate times share, added up
    weight = 0   # the shares, added up
    for group in pass_rates:
        # Step 1: add this group's pass rate times
        # its traffic share.
        total += ___
        # Step 2: add its traffic share on its own.
        weight += ___
    # Step 3: divide, then round to 2 places.
    return round(___, 2)
""",
        fills=['pass_rates[group] * traffic[group]', 'traffic[group]', 'total / weight'],
        concepts=[
            [
                'Looping over a dict',
                '`for key in d:` gives you each key in turn. `d[key]` is the value for that key.',
                """ages = {"ann": 30, "bo": 25}
for name in ages:
    print(name, ages[name])""",
            ],
            [
                'Weighted average',
                'Each score counts in proportion to its weight: multiply each score by its weight, add those up, then divide by the total weight.',
                """(0.9 * 7 + 0.5 * 3) / (7 + 3)   # 0.78""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(0.7812, 2)   # 0.78'],
        ],
        byhand='Billing: 0.9 times 0.7 is 0.63. Refunds: 0.5 times 0.3 is 0.15. Added up, that is 0.78. The traffic shares add up to 0.7 plus 0.3, which is 1.0. 0.78 divided by 1.0 is 0.78, so return 0.78.',
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
        "So keep a small **must-pass set**: the cases that can never get worse, chosen in the **Frame** stage (the first step of a project, where you decide the question and what success means), before any experiment, from what would be costly or embarrassing to get wrong. Add every serious production failure you fix, so it can't quietly come back.",
        "In **Evaluate** (the stage where you score each version on the eval set) and again at **Ship** (the stage where you release it), check it first, separately from the overall score. If any must-pass case fails, the version doesn't ship, whatever its average says. That's a **release gate**.",
    ],
    example=example('Winning on average, failing the gate', """version B:  overall 92% (A was 88%)    ✓ better on average
must-pass:  14 of 15 pass                ✗ "fraud-03" now fails
verdict:    do not ship B until fraud-03 passes again"""),
    check=question(
        'Version B scores 4 points higher overall but fails one of your 15 must-pass questions. What happens?',
        [
            'Ship it: 4 points is a clear win',
            'Remove that question from the must-pass set',
            "It doesn't ship until that case passes: the gate comes before the average",
        ],
        answer=2,
        why='The must-pass set exists exactly for this. Moving a case out of it because it failed defeats the purpose.',
    ),
    angle=angle(
        pattern='Look up each must-pass case',
        text="The big idea: a version can win on average and still break the one answer that matters most, so must-pass cases are checked on their own. Your code goes through the `must_pass` ids in order and looks each one up in the `results` dict. `results.get(qid, False)` gives False when an id is missing, because not tested is not passed. Every id that didn't pass goes on the failing list. An empty list means the version can ship, like a checklist where every box must be ticked.",
        say='"I keep a must-pass set as a release gate, checked before the overall score. Every serious production failure I fix gets added to it."',
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
        prompt="""Your function gets two things:

- `results`: whether the new version passed each question, like `{"fraud-03": False, "refund-01": True}`.
- `must_pass`: the ids of the questions that must never fail, like `["refund-01", "fraud-03"]`.

Return a list of the must-pass ids that did not pass, in the order they appear in `must_pass`. An id missing from `results` counts as not passed: if it wasn't tested, it didn't pass. An empty list means the version can ship.""",
        pattern='Walk the must-pass ids, look each one up, and treat missing as failed.',
        target='one look-up per must-pass id',
        realworld='Release pipelines run the must-pass set first and stop before the full eval if any case fails. It is fast, cheap and catches the regressions that matter most: answers that used to pass and now fail.',
        starter="""def must_pass_gate(results, must_pass):
    # your code here
    pass
""",
        solution="""def must_pass_gate(results, must_pass):
    failing = []
    for qid in must_pass:
        passed = results.get(qid, False)
        if not passed:
            failing.append(qid)
    return failing
""",
        cases=[
            case({'fraud-03': False, 'refund-01': True, 'billing-07': True}, ['refund-01', 'fraud-03'], expected=['fraud-03'], sample=True),
            case({'a': True, 'b': True}, ['a', 'b'], expected=[]),
            case({'a': True}, ['a', 'b'], expected=['b']),
            case({'x': False}, [], expected=[]),
            case({'z': False, 'y': False}, ['z', 'y'], expected=['z', 'y']),
        ],
        guided="""def must_pass_gate(results, must_pass):
    # Replace every ___ with real code, then run the tests.
    failing = []
    for qid in must_pass:
        # Step 1: look up this id's result. A missing
        # id counts as failed, so the default is False.
        passed = ___
        # Step 2: if it did not pass, add it to failing.
        if not passed:
            ___
    return failing
""",
        fills=['results.get(qid, False)', 'failing.append(qid)'],
        concepts=[
            [
                'A safe default',
                '`.get(key, default)` gives the default when the key is missing, so a missing result reads as False.',
                """results = {"a": True}
results.get("a", False)   # True
results.get("b", False)   # False""",
            ],
            [
                'not',
                '`not` flips `True` to `False` and `False` to `True`.',
                """done = False
if not done:
    print("keep going")""",
            ],
            [
                'Adding to a list',
                '`my_list.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ann')   # ['Ann']""",
            ],
        ],
        byhand='Walk must_pass in order. refund-01: results says True, so it passed. fraud-03: results says False, so add it to failing. billing-07 is not a must-pass id, so it is never checked. Return ["fraud-03"]. The list is not empty, so this version does not ship.',
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
        why='Each eval halves what is left: 64, then 32, 16, 8, 4, 2 and 1. That is 6 halvings, so about 6 evals.',
    ),
    angle=angle(
        pattern='Check the middle, drop half',
        text='The big idea: each eval run costs money, so instead of testing every version you test the middle one and keep the half that holds the change. This is called bisecting. Your code keeps `low` and `high`, the two ends of the part still in question. If the middle version passes, the first failure must be later. If it fails, the code remembers it and looks earlier. Each check throws away half, so 1,000 versions need only about 10 checks, like finding a word in a dictionary by opening it in the middle.',
        say='"The passing versions all come before the failing ones, so I check the middle and throw away half each time. That needs only a handful of eval runs."',
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
        prompt="""Your function gets `passed`: one `True` (passes) or `False` (fails) for each prompt version, oldest first, like `[True, True, False, False]`. All the passing versions come first, then all the failing ones.

Return the index (the position, counting from 0) of the first failing version. If every version passes, or the list is empty, return `-1`.

Each check is an eval run that costs money, so don't look at every version. Bisect instead. Look at the middle version. If it passes, the first failure is after it. If it fails, remember it: the first failure is that one or an earlier one. Repeat on the part that is left.""",
        pattern="The list is sorted (passes, then fails), so check the middle and throw away the half that can't contain the answer.",
        target='about 10 checks for 1,000 versions',
        realworld='Bisecting: finding which of 40 prompt or model changes broke an eval in about 6 runs instead of 40. `git bisect` does exactly this for code.',
        starter="""def first_bad_version(passed):
    # your code here
    pass
""",
        solution="""def first_bad_version(passed):
    low = 0
    high = len(passed) - 1
    answer = -1
    while low <= high:
        mid = (low + high) // 2
        if passed[mid]:
            low = mid + 1
        else:
            answer = mid
            high = mid - 1
    return answer
""",
        cases=[
            case([True, True, False, False], expected=2, sample=True),
            case([True, True, True], expected=-1),
            case([False], expected=0),
            case([], expected=-1),
            case([True] * 1000 + [False] * 24, expected=1000),
            case([True, False], expected=1),
        ],
        guided="""def first_bad_version(passed):
    # Replace every ___ with real code, then run the tests.

    # Still to search: positions low to high.
    low = 0
    high = len(passed) - 1
    answer = -1   # the first failure found so far
    while low <= high:
        mid = (low + high) // 2   # the middle
        if passed[mid]:
            # Step 1: mid passes, so the first failure
            # is after it. Move low to just after mid.
            low = ___
        else:
            # Step 2: mid fails. Remember it, then look
            # earlier: move high to just before mid.
            answer = mid
            high = ___
    return answer
""",
        fills=['mid + 1', 'mid - 1'],
        concepts=[
            [
                'while',
                '`while` repeats its block for as long as its condition is true.',
                """n = 3
while n > 0:
    n = n - 1   # runs 3 times""",
            ],
            [
                'Integer division',
                '`//` divides and rounds down to a whole number, so the result works as a position.',
                '(0 + 9) // 2   # 4',
            ],
        ],
        byhand='Search positions 0 to 3. The middle is 0 plus 3, halved and rounded down, which is 1. The version at position 1 passes, so the first failure is after it: low moves to 2. Now search positions 2 to 3. The middle is 2 plus 3, halved and rounded down, which is 2. The version at position 2 fails: remember 2, and high moves to 1. Now low is past high, so nothing is left to search. Return 2.',
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
        pattern='Count passes and fails separately',
        text="The big idea: a judge that passes everything looks accurate when most answers are good, so you check its passes and its failures separately. Your code pairs each human label with the judge's label using `zip`. It keeps four counts: answers the human passed, how many of those the judge passed too, and the same two for failures. Dividing gives two shares. A judge that passes everything scores 1 on the first but 0 on the second, which shows it catches nothing.",
        say='"I check how often the judge agrees with humans on the answers they passed, and separately on the ones they failed. Both need to be high."',
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
        prompt="""Your function gets two lists, with one item per answer, in the same order. `True` means pass and `False` means fail.

- `human`: what a human said, like `[True, False, True]`.
- `judge`: what the LLM judge said about the same answers, like `[True, True, True]`.

Work out two numbers:

- pass agreement: of the answers the human passed, the share the judge also passed.
- fail agreement: of the answers the human failed, the share the judge also failed.

Return `[pass_agreement, fail_agreement]`, each rounded to 2 decimal places. The human always passed at least one answer and failed at least one.""",
        pattern='Split by the human label, then measure agreement on each side separately.',
        target='one walk through the pairs',
        realworld="A judge that passes everything agrees with humans 95% of the time when 95% of answers are good, and catches no failures at all. Checking each side separately, the way Hamel Husain recommends, exposes that. MLflow's `make_judge` judges can then be tuned so they agree more often with your experts' labels.",
        starter="""def judge_agreement(human, judge):
    # your code here
    pass
""",
        solution="""def judge_agreement(human, judge):
    human_passed = 0
    both_passed = 0
    human_failed = 0
    both_failed = 0
    for h, j in zip(human, judge):
        if h:
            human_passed += 1
            if j:
                both_passed += 1
        else:
            human_failed += 1
            if not j:
                both_failed += 1
    pass_agreement = round(both_passed / human_passed, 2)
    fail_agreement = round(both_failed / human_failed, 2)
    return [pass_agreement, fail_agreement]
""",
        cases=[
            case([True, True, False, False, True], [True, False, True, False, True], expected=[0.67, 0.5], sample=True),
            case([True, True, False, False, True], [True, True, True, False, True], expected=[1.0, 0.5]),
            case([True] * 8 + [False] * 2, [True] * 10, expected=[1.0, 0.0]),
            case([True, False, True, False], [True, False, True, False], expected=[1.0, 1.0]),
            case([True, False, True, False, False], [True, True, False, False, False], expected=[0.5, 0.67]),
            case([True, True, False], [False, False, False], expected=[0.0, 1.0]),
        ],
        guided="""def judge_agreement(human, judge):
    # Replace every ___ with real code, then run the tests.
    human_passed = 0   # answers the human passed
    both_passed = 0    # ...that the judge passed too
    human_failed = 0   # answers the human failed
    both_failed = 0    # ...that the judge failed too

    # h is the human's label, j the judge's.
    for h, j in zip(human, judge):
        if h:
            human_passed += 1
            if j:
                both_passed += 1
        else:
            human_failed += 1
            # Step 1: count it if the judge failed it too.
            if ___:
                both_failed += 1

    # Step 2: each side's share, rounded to 2 places.
    pass_agreement = round(both_passed / human_passed, 2)
    fail_agreement = round(___, 2)
    return [pass_agreement, fail_agreement]
""",
        fills=['not j', 'both_failed / human_failed'],
        concepts=[
            [
                'zip',
                'Walks two lists side by side, giving you one item from each.',
                """for x, y in zip([1, 2], [1, 5]):
    print(x == y)   # True, then False""",
            ],
            [
                'not',
                '`not` flips `True` to `False` and `False` to `True`. So `if not j:` runs when the judge said fail.',
                """j = False
not j   # True""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
        ],
        byhand='Answer 1: human pass, judge pass. Answer 2: human pass, judge fail. Answer 3: human fail, judge pass. Answer 4: human fail, judge fail. Answer 5: human pass, judge pass. The human passed answers 1, 2 and 5, and the judge passed 2 of those (1 and 5). 2 out of 3 is 0.666..., which rounds to 0.67. The human failed answers 3 and 4, and the judge failed only 1 of those (4). 1 out of 2 is 0.5. Return [0.67, 0.5].',
        why='One walk through the pairs.',
        gotchas=[
            [
                'Label a few dozen yourself first',
                "Error analysis (reading failures and naming why each one happened) starts with reading real outputs and labelling them. That's where the failure categories, and the judge's rubric, come from.",
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
        'Agreement can be high by luck. If 90% of answers are good, and a judge that never reads anything says "pass" 90% of the time at random, the two still agree on about 82% of answers (0.9 times 0.9 for both saying pass, plus 0.1 times 0.1 for both saying fail).',
        "**Cohen's kappa** takes away the agreement you would expect by chance. Kappa is (observed agreement minus chance agreement) divided by (1 minus chance agreement). 1 means perfect agreement, 0 means no better than luck, and below 0 means worse than luck.",
        "Chance agreement comes from how often each side says pass: the judge's pass rate times the humans' pass rate, plus the judge's fail rate times the humans' fail rate. As a common rough guide, above 0.6 is good and above 0.8 is very good. Use kappa alongside the pass-and-fail check from the previous lesson, not instead of it.",
    ],
    example=example('Kappa on ten answers', """humans: pass 8, fail 2      judge: pass 9, fail 1
they agree on 9 of 10      → observed 0.90
chance = 0.8 * 0.9 + 0.2 * 0.1       # 0.74
kappa = (0.90 - 0.74) / (1 - 0.74)   # about 0.62"""),
    check=question(
        'Your judge agrees with humans 82% of the time, and kappa is 0.05. What does that tell you?',
        [
            'The judge is good: 82% is high',
            'Kappa must be wrong when agreement is high',
            'The judge is barely better than guessing; the agreement mostly comes from most answers being good',
        ],
        answer=2,
        why='When almost everything passes, a judge that also says pass almost every time agrees a lot without catching anything.',
    ),
    angle=angle(
        pattern='Count, then use the formula',
        text="The big idea: a judge and a human can agree a lot just by luck, so Cohen's kappa takes away the agreement you would expect by chance. Your code goes through the pairs once and counts three things: how often they agree, how often the human says pass, and how often the judge says pass. It turns each count into a share, works out chance agreement from the two pass rates, and puts it all into the kappa formula. 1 means perfect, and 0 means no better than luck.",
        say='"I don\'t trust raw agreement for an LLM judge. I use Cohen\'s kappa, so agreement that would happen by luck doesn\'t count."',
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
        prompt="""Your function gets two lists, in the same order. `True` means pass and `False` means fail.

- `human`: what a human said, like `[True, True, True, False]`.
- `judge`: what the LLM judge said, like `[True, True, False, False]`.

Work out three numbers:

- observed: the share of answers they agree on.
- chance: how often they would agree by luck. A pass rate is the share of `True` in a list, and a fail rate is 1 minus it. Chance is the human's and the judge's pass rates multiplied together, plus their fail rates multiplied together.
- kappa: (observed minus chance) divided by (1 minus chance).

Return kappa rounded to 2 decimal places. You will never divide by zero.""",
        pattern='Count agreements and passes in one walk through the labels, then a few lines of arithmetic.',
        target='one walk through the labels',
        realworld='Before letting an LLM judge gate releases, teams label a sample by hand and check kappa. A judge with high agreement but low kappa is just echoing how often answers pass anyway.',
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
    human_rate = human_pass / n
    judge_rate = judge_pass / n
    both_pass = human_rate * judge_rate
    both_fail = (1 - human_rate) * (1 - judge_rate)
    chance = both_pass + both_fail
    return round((observed - chance) / (1 - chance), 2)
""",
        cases=[
            case([True, True, True, False], [True, True, False, False], expected=0.5, sample=True),
            case([True] * 7 + [True, False, False], [True] * 7 + [True, True, False], expected=0.62),
            case([True, False, True, False], [True, False, True, False], expected=1.0),
            case([True] * 8 + [False] * 2, [True] * 10, expected=0.0),
            case([True, False, True, False], [False, True, False, True], expected=-1.0),
            case([True, True, False, False, True, False], [True, False, False, True, True, False], expected=0.33),
        ],
        guided="""def cohen_kappa(human, judge):
    # Replace every ___ with real code, then run the tests.
    n = len(human)
    agree = 0
    human_pass = 0
    judge_pass = 0

    # h is the human's label, j the judge's.
    for h, j in zip(human, judge):
        # Step 1: count the answers where they agree.
        if ___:
            agree += 1
        if h:
            human_pass += 1
        if j:
            judge_pass += 1

    observed = agree / n
    human_rate = human_pass / n   # pass rates
    judge_rate = judge_pass / n

    # Agreeing by luck: both pass, or both fail.
    both_pass = human_rate * judge_rate
    # Step 2: both fail by luck. Put each fail
    # rate in brackets:
    # (1 - human_rate) times (1 - judge_rate).
    both_fail = ___
    chance = both_pass + both_fail

    # Step 3: (observed - chance) divided by
    # (1 - chance), rounded to 2 places.
    return round(___, 2)
""",
        fills=['h == j', '(1 - human_rate) * (1 - judge_rate)', '(observed - chance) / (1 - chance)'],
        concepts=[
            [
                'zip',
                'Walks two lists side by side, giving you one item from each.',
                """for x, y in zip([1, 2], [1, 5]):
    print(x == y)   # True, then False""",
            ],
            [
                'Comparing two labels',
                '`h == j` is `True` when both are `True` or both are `False`, which is exactly when the two agree.',
                """True == True     # True
False == False   # True
True == False    # False""",
            ],
            [
                'Chance agreement',
                'If two people label independently, they agree by luck when both happen to say pass, or both say fail.',
                """# human passes 80%, judge passes 90%
round(0.8 * 0.9 + 0.2 * 0.1, 2)   # 0.74""",
            ],
            [
                'Brackets first',
                'Python multiplies and divides before it adds and subtracts. Brackets make the part inside happen first.',
                """10 - 4 / 2     # 8.0
(10 - 4) / 2   # 3.0""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(0.6153, 2)   # 0.62'],
        ],
        byhand='They agree on answers 1, 2 and 4: 3 out of 4, so observed is 0.75. The human passed 3 of 4, a pass rate of 0.75 and a fail rate of 0.25. The judge passed 2 of 4, a pass rate of 0.5 and a fail rate of 0.5. Both pass by luck: 0.75 times 0.5 is 0.375. Both fail by luck: 0.25 times 0.5 is 0.125. So chance is 0.375 plus 0.125, which is 0.5. Observed minus chance is 0.75 minus 0.5, which is 0.25. 1 minus chance is 1 minus 0.5, which is 0.5. 0.25 divided by 0.5 is 0.5. Return 0.5.',
        why='One walk through the labels to count, then a fixed amount of arithmetic.',
        gotchas=[
            [
                'A judge that always passes scores 0',
                'It agrees with humans whenever the answer was good, which can be most of the time, yet kappa is 0 because it adds nothing beyond how often answers pass anyway.',
            ],
            [
                'Small samples',
                'Kappa on 20 labels is rough. Label enough answers, including plenty of failures, before trusting it.',
            ],
        ],
    ),
)

lesson(MODULE, 'checker_score',
    title='Testing the checker with planted mistakes',
    learn=[
        'A **checker** is whatever marks each run pass or fail: an LLM judge, or a bit of code. A checker that misses mistakes looks just like one that works: every run passes. So test it on **planted mistakes**: runs where you put a fault in on purpose, so you already know which ones should fail.',
        'Plant more than wrong answers. Plant **false successes** too: the agent says "I\'ve closed the ticket", but the ticket is still open. A judge that reads only the agent\'s last message is easily fooled by a confident claim like that.',
        'Add a **do-nothing agent**: it changes nothing and just replies "Done!". It must score 0. If the checker passes even one of its runs, the checker has a bug.',
        'The fix is a **code check of the real end state**: read the ticket table, not the reply. Run it next to the judge. For each checker, count what it caught, what it missed, and its **false alarms** (good runs it failed by mistake).',
    ],
    example=example('Two checkers on the same planted runs', """planted: wrong-1 claim-1 idle-1
  wrong = ticket closed, reply wrong
  claim = says done, ticket still open
  idle  = the do-nothing agent
  ok    = a good run, nothing planted
  flagged = marked as failing

judge (reads the reply)
  flagged wrong-1 ok-2
  caught 1 of 3, 1 false alarm
code (reads the ticket table)
  flagged claim-1 idle-1
  caught 2 of 3, 0 false alarms
together (fail if either flags):
  caught 3 of 3, 1 false alarm"""),
    check=question(
        'Every task in your eval asks the agent to close an open ticket. A do-nothing agent (it changes nothing, then replies "Done!") passes 4 of 10 runs. What does that tell you?',
        [
            'Four of those tickets needed no work to close',
            'The checker trusts the reply instead of the ticket',
            'The real agent only has to beat 4 out of 10',
        ],
        answer=1,
        why='Nothing changed, so all 10 runs should fail. A checker that passes any of them is reading the claim, not the real end state.',
    ),
    angle=angle(
        pattern='Compare two lists both ways',
        text='The big idea: a checker that misses mistakes looks just like one that works, so you test it on runs where you planted mistakes on purpose. Your code first goes through the planted ids and asks if each one was flagged. Yes is a catch, and no is a miss. Then it goes through the flagged ids and asks if each one was planted. A no there is a false alarm: a good run failed by mistake. It is like hiding errors in an essay to see if a proofreader finds them.',
        say='"Before I trust a checker, I run it on planted mistakes, including false successes and a do-nothing agent. I report what it caught, missed and wrongly failed."',
        classic=None,
    ),
    stack=stack('MLflow 3: a code check next to the judge', """import mlflow
from mlflow.genai.scorers import (
    Guidelines, scorer)

# Code check: read the real ticket.
# get_ticket is your own lookup.
@scorer
def ticket_closed(inputs):
    t = get_ticket(inputs["ticket_id"])
    return t["status"] == "closed"

# Judge: reads the request and reply,
# never the ticket.
resolved = Guidelines(
    name="resolved",
    guidelines="The reply resolves "
    "the user's request.")

# planted: recorded runs (inputs and
# outputs), including do-nothing runs
res = mlflow.genai.evaluate(
    data=planted,
    scorers=[ticket_closed, resolved])

# One row per run, one column per
# checker: compare with what you planted
res.result_df[["ticket_closed/value",
               "resolved/value"]]"""),
    exercise=exercise(
        title='Score the Checker',
        topic='evals',
        difficulty='easy',
        fn='checker_score',
        prompt="""You planted mistakes in some agent runs, then ran your checker over every run. Now score the checker.

Your function gets two things:

- `planted`: ids of the runs where you planted a mistake, like `["wrong-1", "claim-1"]`. It always has at least one id.
- `flagged`: ids of the runs the checker marked as failing, like `["wrong-1", "ok-2"]`.

Return a dict with three keys:

- `"caught"`: the share of planted ids that are also in `flagged`, rounded to 2 decimal places. 1 out of 3 gives `0.33`.
- `"missed"`: the planted ids that are not in `flagged`, sorted A to Z.
- `"false_alarms"`: the flagged ids that are not in `planted`, sorted A to Z. These are good runs the checker failed by mistake.""",
        pattern='Check each list against the other: planted but not flagged is a miss, and flagged but not planted is a false alarm.',
        target='for each id, check the other list',
        realworld="Agents often claim a success that never happened, and LLM judges, even ones that read the whole conversation, mostly can't tell. Keep a small planted set and run it again whenever the judge's prompt or model changes.",
        starter="""def checker_score(planted, flagged):
    # your code here
    pass
""",
        solution="""def checker_score(planted, flagged):
    caught = 0
    missed = []
    for run in planted:
        if run in flagged:
            caught += 1
        else:
            missed.append(run)
    alarms = []
    for run in flagged:
        if run not in planted:
            alarms.append(run)
    return {
        "caught": round(caught / len(planted), 2),
        "missed": sorted(missed),
        "false_alarms": sorted(alarms),
    }
""",
        cases=[
            case(['wrong-1', 'claim-1', 'idle-1'], ['wrong-1', 'ok-2'],
                 expected={'caught': 0.33, 'missed': ['claim-1', 'idle-1'], 'false_alarms': ['ok-2']}, sample=True),
            case(['claim-1', 'wrong-2'], ['wrong-2', 'claim-1'],
                 expected={'caught': 1.0, 'missed': [], 'false_alarms': []}),
            case(['idle-2', 'claim-3', 'idle-1'], [],
                 expected={'caught': 0.0, 'missed': ['claim-3', 'idle-1', 'idle-2'], 'false_alarms': []}),
            case(['wrong-1'], ['ok-3', 'wrong-1', 'ok-1'],
                 expected={'caught': 1.0, 'missed': [], 'false_alarms': ['ok-1', 'ok-3']}),
            case(['wrong-3', 'claim-2', 'wrong-1'], ['wrong-3', 'ok-4', 'claim-2'],
                 expected={'caught': 0.67, 'missed': ['wrong-1'], 'false_alarms': ['ok-4']}),
            case(['claim-1', 'idle-1', 'claim-2', 'wrong-1'], ['claim-2', 'ok-1'],
                 expected={'caught': 0.25, 'missed': ['claim-1', 'idle-1', 'wrong-1'], 'false_alarms': ['ok-1']}),
        ],
        guided="""# Replace every ___ with real code, then run the tests.

def checker_score(planted, flagged):
    caught = 0
    missed = []
    for run in planted:
        # Step 1: did the checker flag this
        # planted run?
        if ___:
            caught += 1
        else:
            missed.append(run)

    alarms = []
    for run in flagged:
        # Step 2: flagged, but nothing was
        # planted here: a false alarm.
        if ___:
            alarms.append(run)

    # Step 3: caught divided by how many
    # were planted, rounded to 2 places.
    return {
        "caught": round(___, 2),
        "missed": sorted(missed),
        "false_alarms": sorted(alarms),
    }
""",
        fills=['run in flagged', 'run not in planted', 'caught / len(planted)'],
        concepts=[
            [
                '`in` with a list',
                '`x in items` is True when the list holds x. `not in` is the opposite.',
                """pets = ["cat", "dog"]
"cat" in pets       # True
"cow" not in pets   # True""",
            ],
            [
                'Adding to a list',
                '`items.append(x)` puts x on the end of the list.',
                """names = []
names.append("Ana")   # ["Ana"]""",
            ],
            [
                'sorted',
                '`sorted(items)` gives a new list in order: A to Z for text.',
                'sorted(["pear", "fig"])   # ["fig", "pear"]',
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
        ],
        byhand='Walk the planted ids first. wrong-1 is in flagged, so it was caught. claim-1 is not in flagged: missed. idle-1 is not in flagged: missed. That is 1 caught out of 3 planted, and 1 divided by 3 is 0.333..., which rounds to 0.33. Now walk the flagged ids. wrong-1 was planted, so that flag was right. ok-2 was not planted, so it is a false alarm. Sorted, missed is ["claim-1", "idle-1"]. Return {"caught": 0.33, "missed": ["claim-1", "idle-1"], "false_alarms": ["ok-2"]}.',
        why='For each id in one list, we check whether the other list holds it. The lists are short, so this is quick.',
        gotchas=[
            [
                'Planting only wrong answers',
                'A judge can catch a wrong answer and still believe "I\'ve closed the ticket" when nothing changed. Plant false successes and do-nothing runs too, or the test is too easy.',
            ],
            [
                'Ignoring false alarms',
                'A checker that fails every run catches 100 percent of the planted mistakes. Count its false alarms too, or the "best" checker is one that blocks everything.',
            ],
        ],
    ),
)

lesson(MODULE, 'memory_update_score',
    title='Testing memory with planted changes',
    learn=[
        'An agent with memory can keep giving an old fact after its source has changed. An ordinary eval never notices, because nothing changes while it runs. So **plant a change**: update a source on purpose (the office moves from Leeds to York), then ask a question that depends on it.',
        'Score each answer as one of three outcomes: **current** (it used the new fact), **unsure** (it said it can\'t confirm, which is honest) or **stale** (it used the old fact). Be strict: an answer that mentions the old fact counts as stale, even if it gives the new one too, because the user cannot tell which is right. The price: a correct answer like "you moved from Silver to Gold" also scores as stale, so read a few of the stale ones by hand.',
        'Watch for two scoring traps. A judge that passes any answer containing "York" also passes "Leeds or York". And MLflow\'s `RetrievalGroundedness` only checks the answer against what the agent looked up, so an answer built on a stale memory still passes.',
        'Then add checks that catch lazy scoring. A code check reads the memory store itself: was the old fact marked as replaced? Two **baselines** (simple stand-ins to compare with) must do badly: a memory that never updates must fail the changed facts, and no memory at all must fail the facts that did not change.',
    ],
    example=example('One planted change, four answers', """change: office Leeds → York
question: "Where is my office?"

"Your office is in York."  current
"I can't confirm that."    unsure
"It's in Leeds."           stale
"York, or maybe Leeds."    stale"""),
    check=question(
        'The office moved to York last week. Your agent answers "Your office is in Leeds" from an old memory it looked up, and `RetrievalGroundedness` passes it. Why?',
        [
            'It trusts any memory saved less than a month ago',
            'It compares the answer with what was looked up',
            'It only fails answers that sound unsure of themselves',
        ],
        answer=1,
        why='Grounded means "matches what was looked up", not "true". The old memory was looked up, so the answer matches it. Only a planted change, where you know the right answer, catches this.',
    ),
    angle=angle(
        pattern='Label each answer, then count',
        text="The big idea: an agent with memory can keep giving an old fact after it changed, so you plant a change and score each answer as current, unsure or stale. Your code makes the answer lowercase and checks for the old fact first. If it's there, the answer is stale, even if the new fact is there too, because the user can't tell which is right. Otherwise it checks for the new fact. If neither is there, the answer is unsure. Last, each count is divided by the number of answers.",
        say='"I change a fact on purpose and score answers as current, unsure or stale. Any answer that mentions the old fact counts as stale."',
        classic=None,
    ),
    stack=stack('MLflow 3: a code scorer with three labels', """import mlflow
from mlflow.genai.scorers import scorer

# One label per answer: the same
# rule as your exercise.
@scorer
def memory_update(outputs,
                  expectations):
    text = outputs.lower()
    old = expectations["old"].lower()
    new = expectations["new"].lower()
    if old in text:
        return "stale"
    if new in text:
        return "current"
    return "unsure"

# Answers recorded after you changed
# the source on purpose.
planted = [{
    "inputs": {"question":
        "Where is my office?"},
    "outputs": "York, or maybe Leeds.",
    "expectations": {"new": "York",
                     "old": "Leeds"},
}]

res = mlflow.genai.evaluate(
    data=planted,
    scorers=[memory_update])

# The share of each label
col = res.result_df[
    "memory_update/value"]
print(col.value_counts(normalize=True))"""),
    exercise=exercise(
        title='Score the Memory Test',
        topic='evals',
        difficulty='easy',
        fn='memory_update_score',
        prompt="""You changed some facts on purpose, then asked your agent questions about them. Now score its answers.

`answers` is a list with at least one item. Each item is a dict like `{"answer": "It's in York.", "new": "York", "old": "Leeds"}`: the agent's answer, the fact after your change, and the fact before it.

Label each answer, ignoring upper and lower case:

- `"stale"` if the answer contains `old`. This counts even if it contains `new` too.
- `"current"` if it contains `new` (and not `old`).
- `"unsure"` otherwise.

Return a dict with the share of answers for each label, like `{"current": 0.5, "unsure": 0.0, "stale": 0.5}`. A share is that label's count divided by the number of answers, rounded to 2 decimal places.""",
        pattern='Give each answer one label, checking the worst outcome first, then turn the counts into shares.',
        target='one pass over the answers',
        realworld='Research tests of agent memory (LongMemEval, STALE) are built on planted changes too, and find that agents often fail to use the updated fact. Run your planted set a few times and report the counts with how many questions there were. In MLflow 3, a code `@scorer` can return the label for each answer.',
        starter="""def memory_update_score(answers):
    # your code here
    pass
""",
        solution="""def memory_update_score(answers):
    counts = {"current": 0, "unsure": 0,
              "stale": 0}
    for a in answers:
        text = a["answer"].lower()
        if a["old"].lower() in text:
            counts["stale"] += 1
        elif a["new"].lower() in text:
            counts["current"] += 1
        else:
            counts["unsure"] += 1
    n = len(answers)
    shares = {}
    for label in counts:
        shares[label] = round(
            counts[label] / n, 2)
    return shares
""",
        cases=[
            case([
                {'answer': 'Your office is in York.', 'new': 'York', 'old': 'Leeds'},
                {'answer': "It's in Leeds.", 'new': 'York', 'old': 'Leeds'},
                {'answer': 'York, or maybe Leeds.', 'new': 'York', 'old': 'Leeds'},
                {'answer': "I can't confirm that.", 'new': 'York', 'old': 'Leeds'},
            ], expected={'current': 0.25, 'unsure': 0.25, 'stale': 0.5}, sample=True),
            case([
                {'answer': 'Refunds take 3 days.', 'new': '3 days', 'old': '5 days'},
            ], expected={'current': 1.0, 'unsure': 0.0, 'stale': 0.0}),
            case([
                {'answer': 'The policy now says 3 DAYS.', 'new': '3 days', 'old': '5 days'},
                {'answer': "Sorry, I don't know.", 'new': '3 days', 'old': '5 days'},
                {'answer': 'Still 5 Days.', 'new': '3 days', 'old': '5 days'},
            ], expected={'current': 0.33, 'unsure': 0.33, 'stale': 0.33}),
            case([
                {'answer': 'Your manager is Priya.', 'new': 'Priya', 'old': 'Sam'},
                {'answer': 'You are on the Gold plan.', 'new': 'Gold', 'old': 'Silver'},
                {'answer': 'Gold, or maybe still Silver.', 'new': 'Gold', 'old': 'Silver'},
            ], expected={'current': 0.67, 'unsure': 0.0, 'stale': 0.33}),
            case([
                {'answer': "I don't have a current record of that.", 'new': 'York', 'old': 'Leeds'},
                {'answer': 'Please check with HR.', 'new': 'Priya', 'old': 'Sam'},
            ], expected={'current': 0.0, 'unsure': 1.0, 'stale': 0.0}),
            case([
                {'answer': 'Leeds.', 'new': 'York', 'old': 'Leeds'},
                {'answer': 'leeds, I think', 'new': 'York', 'old': 'Leeds'},
            ], expected={'current': 0.0, 'unsure': 0.0, 'stale': 1.0}),
        ],
        guided="""def memory_update_score(answers):
    # Replace every ___ with real code, then run the tests.

    counts = {"current": 0, "unsure": 0,
              "stale": 0}
    for a in answers:
        text = a["answer"].lower()
        # Step 1: mentions the old fact? Stale,
        # even if it says the new one too.
        if ___ in text:
            counts["stale"] += 1
        # Step 2: says the new fact? Current.
        elif a["new"].lower() in text:
            counts["current"] += 1
        else:
            counts["unsure"] += 1
    # Step 3: each count divided by how
    # many answers, rounded to 2 places.
    n = len(answers)
    shares = {}
    for label in counts:
        shares[label] = round(
            ___, 2)
    return shares
""",
        fills=['a["old"].lower()', 'counts[label] / n'],
        concepts=[
            [
                'lower and in',
                '`lower()` gives a lowercase copy of the text. `"ab" in text` is True if those characters appear anywhere in the text. Lowercase both sides so "York" and "york" match.',
                """'Green TEA'.lower()           # 'green tea'
'tea' in 'green tea'          # True""",
            ],
            [
                'if, elif, else',
                'Python tries each test from the top and runs only the first one that is True. `else` runs when none were.',
                """size = 7
if size > 10:
    print('big')
elif size > 5:
    print('medium')   # this one
else:
    print('small')""",
            ],
            [
                'Counting with a dict',
                'Start each label at 0, then add 1 with `+= 1` each time you see it.',
                """votes = {'yes': 0, 'no': 0}
votes['yes'] += 1
votes   # {'yes': 1, 'no': 0}""",
            ],
            [
                'Looping over a dict',
                '`for key in a_dict:` gives you each key in turn. Use `a_dict[key]` to get its value.',
                """ages = {'ana': 30, 'bo': 25}
for name in ages:
    print(name, ages[name])""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
        ],
        byhand='All four answers are about the office: old is Leeds, new is York. Answer 1, "Your office is in York.", has no "leeds" but has "york": current. Answer 2, "It\'s in Leeds.", has "leeds": stale. Answer 3, "York, or maybe Leeds.", has "leeds", so it is stale even though it says York too. Answer 4, "I can\'t confirm that.", has neither: unsure. That is 1 current, 1 unsure and 2 stale out of 4. 1 divided by 4 is 0.25, and 2 divided by 4 is 0.5. Return {"current": 0.25, "unsure": 0.25, "stale": 0.5}.',
        why='One pass over the answers, then one step per label.',
        gotchas=[
            [
                'Passing answers that give both',
                'A judge that only looks for the new fact passes "Leeds or York". The user still can\'t tell which is right, so score it stale.',
            ],
            [
                'Counting "unsure" as wrong',
                'An honest "I can\'t confirm that" beats a confident old fact. Report it as its own number. If you count it as wrong, an agent that guesses scores better than one that admits it doesn\'t know.',
            ],
        ],
    ),
)

lesson(MODULE, 'review_queue',
    title='Drafted labels, expert-confirmed',
    learn=[
        'With hundreds of questions, experts can\'t write every expected answer from scratch. Instead an LLM **drafts** the expected facts from the question and its source article, and experts **confirm or correct** the drafts. The drafter may also see the articles the app found, from the **trace** (the saved record of each step the app took for that question), but never the app\'s own answer. Checking a draft is several times faster than writing one.',
        "Expert time is still the scarce part, so decide which drafts they see first. Highest: **must-pass** questions, where a wrong label is costly. Next: drafts where two independent drafting runs **disagree**, which usually means the question is ambiguous. Then: questions from **rare groups**, where each label carries more weight. Everything else can wait, or be spot-checked.",
        'Track how often experts change a draft. If they rarely do, you can send fewer drafts for review; if they often do, the drafting prompt needs work before it saves anyone time.',
    ],
    example=example('Who reviews what first', """id          must-pass  drafts agree  group     priority
refund-02      yes         yes       refund        4
billing-31     no          no        billing       2
fraud-44       no          yes       fraud (rare)  1
shipping-08    no          yes       shipping      0
→ with time for 3 reviews: refund-02, billing-31, fraud-44"""),
    check=question(
        'Experts changed only 2 of the last 150 drafted labels. What should you do?',
        [
            'Review a smaller sample, keep must-pass and disagreeing drafts in the queue, and keep tracking the change rate',
            'Stop reviewing drafts entirely',
            'Have experts rewrite every label anyway',
        ],
        answer=0,
        why='A low change rate earns a lighter review, not none. The must-pass and disputed drafts are still where a mistake costs most.',
    ),
    angle=angle(
        pattern='Score, then sort',
        text='The big idea: expert time is scarce, so the riskiest drafts get reviewed first. Your code gives each item points: 4 for must-pass, 2 if the two drafts disagree, and 1 for a rare group. It stores each item as a pair: minus its points, then its id. Sorting puts smaller numbers first, so the minus sign brings the most points to the top, and items with equal points fall into A to Z order by id. It is like a hospital waiting room, where the most urgent go first.',
        say='"I let an LLM draft expected answers, then send them to experts by risk: must-pass first, then disputed drafts, then rare groups."',
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
        prompt="""Your function gets two things:

- `items`: drafted expected answers (labels) waiting for an expert to check. Each is a dict like `{"id": "refund-02", "must_pass": True, "drafts_agree": True, "group": "refund"}`.
- `rare_groups`: the groups with few examples, like `["fraud"]`.

In each item, `must_pass` is `True` for a must-pass question, `drafts_agree` is `False` when two drafts of the label came out different, and `group` is the question's group.

Give each item a priority. Start at 0, then:

- add 4 if `must_pass` is `True` (more than the other two together, so must-pass items always come first)
- add 2 if `drafts_agree` is `False`
- add 1 if its `group` is in `rare_groups`

Return all the ids in review order, highest priority first. When two items have the same priority, put their ids in alphabetical order.""",
        pattern='A score from simple rules, then sort by score, with the id to break ties.',
        target='one walk through the items to score, then a sort',
        realworld='Labelling teams route expert time this way, so the riskiest labels get human eyes first and the rest are checked by sampling.',
        starter="""def review_queue(items, rare_groups):
    # your code here
    pass
""",
        solution="""def review_queue(items, rare_groups):
    scored = []
    for item in items:
        priority = 0
        if item["must_pass"]:
            priority += 4
        if not item["drafts_agree"]:
            priority += 2
        if item["group"] in rare_groups:
            priority += 1
        scored.append((-priority, item["id"]))
    scored.sort()
    queue = []
    for pair in scored:
        queue.append(pair[1])
    return queue
""",
        cases=[
            case([
                {'id': 'shipping-08', 'must_pass': False, 'drafts_agree': True, 'group': 'shipping'},
                {'id': 'fraud-44', 'must_pass': False, 'drafts_agree': True, 'group': 'fraud'},
                {'id': 'refund-02', 'must_pass': True, 'drafts_agree': True, 'group': 'refund'},
                {'id': 'billing-31', 'must_pass': False, 'drafts_agree': False, 'group': 'billing'},
            ], ['fraud'], expected=['refund-02', 'billing-31', 'fraud-44', 'shipping-08'], sample=True),
            case([], ['fraud'], expected=[]),
            case([
                {'id': 'b', 'must_pass': False, 'drafts_agree': True, 'group': 'x'},
                {'id': 'a', 'must_pass': False, 'drafts_agree': True, 'group': 'x'},
            ], [], expected=['a', 'b']),
            case([
                {'id': 'q', 'must_pass': True, 'drafts_agree': True, 'group': 'common'},
                {'id': 'p', 'must_pass': True, 'drafts_agree': False, 'group': 'rare'},
            ], ['rare'], expected=['p', 'q']),
            case([
                {'id': 'm2', 'must_pass': False, 'drafts_agree': False, 'group': 'g'},
                {'id': 'r1', 'must_pass': False, 'drafts_agree': True, 'group': 'rare'},
                {'id': 'm1', 'must_pass': False, 'drafts_agree': False, 'group': 'g'},
            ], ['rare'], expected=['m1', 'm2', 'r1']),
        ],
        guided="""def review_queue(items, rare_groups):
    # Replace every ___ with real code, then run the tests.
    scored = []
    for item in items:
        priority = 0
        if item["must_pass"]:
            priority += 4
        # Step 1: add 2 when the drafts do not agree.
        if ___:
            priority += 2
        if item["group"] in rare_groups:
            priority += 1
        # Step 2: add one pair: minus the priority,
        # then the item's id, item["id"]. The pair
        # needs its own brackets inside append( ).
        # The minus sign sorts the highest first.
        scored.append(___)
    scored.sort()

    queue = []
    for pair in scored:
        # Step 3: keep just the id, the pair's 2nd item.
        queue.append(___)
    return queue
""",
        fills=['not item["drafts_agree"]', '(-priority, item["id"])', 'pair[1]'],
        concepts=[
            [
                'not',
                '`not` flips `True` to `False` and `False` to `True`.',
                """agree = False
not agree   # True""",
            ],
            [
                'in',
                '`x in some_list` is `True` when `x` is one of the items.',
                """'fraud' in ['fraud', 'tax']   # True""",
            ],
            [
                'Sorting pairs',
                '`.sort()` puts the smallest first. A list of pairs sorts by the first item, and ties are sorted by the second item. -3 is smaller than -1, so a minus sign in front of the priority puts the biggest priority first. To add a pair with `.append`, the pair needs its own brackets inside append\'s. `pair[1]` is the second item of a pair.',
                """pairs = [(-1,'b'), (-3,'c')]
pairs.append((-1,'a'))   # 2 sets of brackets:
                         # append's, and the pair's
pairs.sort()
# [(-3,'c'), (-1,'a'), (-1,'b')]
pairs[0][1]   # 'c'""",
            ],
        ],
        byhand='shipping-08: not must-pass, drafts agree, not a rare group, so 0. fraud-44: fraud is a rare group, so 1. refund-02: must-pass, so 4. billing-31: drafts disagree, so 2. Highest first: refund-02 (4), billing-31 (2), fraud-44 (1), shipping-08 (0). No two share a priority, so return ["refund-02", "billing-31", "fraud-44", "shipping-08"].',
        why='One walk through the items to score each one, then a sort.',
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
        'Counting them decides the comparison (that is McNemar\'s test, from the Experiment design module). **Reading** them explains it. For each one, open both traces side by side and find the first step where they differ: different documents retrieved, a different order, a different tool, an extra loop. Then label the cause in a few words.',
        'Count the causes in each direction. "6 improvements, mostly *moved the right document up*; 2 regressions, both *pushed a worse document above it*" tells you what the change did and what to fix next. This is called **error analysis**, and it happens in the **Evaluate** stage, where you score and compare the versions you ran.',
    ],
    example=example('Regressions, improvements and their causes', """question         old  new  cause (from reading both traces)
return-label     ✗    ✓    reranker moved the right doc to the top      improvement
change-address   ✓    ✗    reranker pushed a policy doc above it        regression
refund-time      ✗    ✓    reranker moved the right doc to the top      improvement
charged-twice    ✗    ✗    (same result in both: not compared)

improvements: {"moved right doc up": 2}     regressions: {"pushed worse doc up": 1}"""),
    check=question(
        'You swapped in a new reranker. The new version beats the old by 3 questions. Reading the improvements, every one has the same cause: "answer is shorter". What should you suspect?',
        [
            'The new version is clearly better',
            'The scorer may reward short answers, so check the scorer before trusting the win',
            'Nothing, causes do not matter once the count is in',
        ],
        answer=1,
        why='When every improvement shares a cause unrelated to the change you made, the measurement is often the thing that changed. Reading them is how you catch it.',
    ),
    angle=angle(
        pattern='Find what changed, count the causes',
        text="The big idea: the questions where two versions disagree are the ones that explain a change, so you label why each one changed and count the causes. Your code goes through every question id. If the old version failed and the new one passed, it is an improvement. If the old passed and the new failed, it is a regression. For each one it looks up the cause and adds 1 to that cause's count in a dict, a lookup table, like keeping tally marks. Questions with the same result are skipped.",
        say='"I don\'t stop at the score. I read every regression and improvement, label why it changed, and count the causes each way."',
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
        prompt="""Your function gets three things:

- `old`: whether the old version passed each question, like `{"q1": False, "q2": True}`.
- `new`: the same for the new version, with the same question ids, like `{"q1": True, "q2": True}`.
- `causes`: the cause you wrote for each question whose result changed, like `{"q1": "moved right doc up"}`.

An improvement is a question that `old` failed and `new` passed. A regression is the reverse: `old` passed and `new` failed. A question with the same result in both is not counted, and it has no cause, so only look up `causes` for a question that changed.

Return `{"improvements": ..., "regressions": ...}`. Each is a dict from a cause to how many questions had that cause.""",
        pattern='One walk through the ids, counting each change into one of two dicts of causes.',
        target='one walk through the questions',
        realworld='Error analysis like this is how teams decide what to work on next: the most common cause among regressions is usually the next fix.',
        starter="""def change_report(old, new, causes):
    # your code here
    pass
""",
        solution="""def change_report(old, new, causes):
    improvements = {}
    regressions = {}
    for qid in old:
        if not old[qid] and new[qid]:
            cause = causes[qid]
            improvements[cause] = improvements.get(cause, 0) + 1
        elif old[qid] and not new[qid]:
            cause = causes[qid]
            regressions[cause] = regressions.get(cause, 0) + 1
    return {"improvements": improvements,
            "regressions": regressions}
""",
        cases=[
            case({'q1': False, 'q2': True, 'q3': False, 'q4': False},
                 {'q1': True, 'q2': False, 'q3': True, 'q4': False},
                 {'q1': 'moved right doc up', 'q2': 'pushed worse doc up', 'q3': 'moved right doc up'},
                 expected={'improvements': {'moved right doc up': 2}, 'regressions': {'pushed worse doc up': 1}}, sample=True),
            case({'q1': True}, {'q1': True}, {}, expected={'improvements': {}, 'regressions': {}}),
            case({'q1': False, 'q2': False}, {'q1': True, 'q2': True}, {'q1': 'better tool', 'q2': 'shorter answer'},
                 expected={'improvements': {'better tool': 1, 'shorter answer': 1}, 'regressions': {}}),
            case({'a': True, 'b': True, 'c': True}, {'a': False, 'b': False, 'c': True}, {'a': 'wrong tool', 'b': 'wrong tool'},
                 expected={'improvements': {}, 'regressions': {'wrong tool': 2}}),
            case({}, {}, {}, expected={'improvements': {}, 'regressions': {}}),
        ],
        guided="""def change_report(old, new, causes):
    # Replace every ___ with real code, then run the tests.
    improvements = {}   # cause -> how many
    regressions = {}    # cause -> how many
    for qid in old:
        # Step 1: improvement: old[qid] is False
        # and new[qid] is True.
        if ___:
            cause = causes[qid]
            # Step 2: add one to this cause's count.
            improvements[cause] = ___
        # Step 3: regression: old[qid] is True
        # and new[qid] is False.
        elif ___:
            cause = causes[qid]
            regressions[cause] = regressions.get(cause, 0) + 1
        # Same result in both: nothing to count.
    return {"improvements": improvements,
            "regressions": regressions}
""",
        fills=['not old[qid] and new[qid]', 'improvements.get(cause, 0) + 1', 'old[qid] and not new[qid]'],
        concepts=[
            [
                'Looping over a dict',
                '`for key in d:` gives you each key in turn. `d[key]` is the value for that key.',
                """ages = {"ann": 30, "bo": 25}
for name in ages:
    print(name, ages[name])""",
            ],
            [
                'not, and',
                '`not x` flips `True` and `False`. `a and b` is `True` only when both are `True`. Use them on one question\'s result, like `old[qid]`, not on the whole dict.',
                """sunny = True
warm = False
sunny and not warm   # True""",
            ],
            [
                'elif',
                'Short for "else if". It is only checked when the `if` above it was false.',
                """if n > 0: print('positive')
elif n < 0: print('negative')""",
            ],
            [
                'Counting with a dict',
                'Look up the current count with a default of 0, then add one.',
                """counts = {}
counts["x"] = counts.get("x", 0) + 1
counts   # {"x": 1}""",
            ],
        ],
        byhand='q1: old failed, new passed. An improvement, cause "moved right doc up". q2: old passed, new failed. A regression, cause "pushed worse doc up". q3: old failed, new passed. Another improvement with the same cause. q4: failed in both, so it is not counted. Return improvements {"moved right doc up": 2} and regressions {"pushed worse doc up": 1}.',
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
            'The eval set size',
            'The answer step: the prompt, the model or the scorer',
        ],
        answer=2,
        why='If both versions got the same articles, retrieval did not cause the change. Something after it did.',
    ),
    angle=angle(
        pattern='Compare as sets, then bucket',
        text="The big idea: sort changed questions by whether the articles found changed, so you know which part of the pipeline to look at. Your code turns each article list into a set: a collection where order and repeats don't matter. If the old and new sets differ, the versions found different articles, so the question goes under retrieval. If the sets are the same, even in a different order, it goes under answer. It is like checking two shopping bags hold the same items, however they were packed.",
        say='"Before reading regressions, I bucket them by whether retrieval changed, using the traces. Then I read a sample from each bucket."',
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
        prompt="""Your function gets `changed`: the questions whose result changed between two versions. Each is a dict like `{"qid": "billing-06", "old_docs": ["kb-12", "kb-01"], "new_docs": ["kb-04", "kb-01"]}`. `qid` is the question's id. `old_docs` and `new_docs` are the help articles each version found and gave to the model to write its answer.

If the two versions sent different articles, the qid goes in a list called `retrieval`. If they sent the same articles, even in a different order, it goes in a list called `answer`.

Return `{"retrieval": retrieval, "answer": answer}`, with the qids in the order they appear in `changed`.""",
        pattern='Compare the two lists as sets, then file the qid.',
        target='one walk through the changed questions',
        realworld='Teams with large eval sets triage regressions like this every release, so they read thirty traces instead of three hundred.',
        starter="""def sort_changes(changed):
    # your code here
    pass
""",
        solution="""def sort_changes(changed):
    retrieval = []
    answer = []
    for item in changed:
        if set(item["old_docs"]) != set(item["new_docs"]):
            retrieval.append(item["qid"])
        else:
            answer.append(item["qid"])
    return {"retrieval": retrieval, "answer": answer}
""",
        cases=[
            case([
                {'qid': 'billing-06', 'old_docs': ['kb-12', 'kb-01', 'kb-02'], 'new_docs': ['kb-04', 'kb-09', 'kb-01']},
                {'qid': 'refund-11', 'old_docs': ['kb-13', 'kb-16', 'kb-14'], 'new_docs': ['kb-13', 'kb-14', 'kb-16']},
                {'qid': 'shipping-07', 'old_docs': ['kb-09', 'kb-03', 'kb-10'], 'new_docs': ['kb-10', 'kb-07', 'kb-09']},
            ], expected={'retrieval': ['billing-06', 'shipping-07'], 'answer': ['refund-11']}, sample=True),
            case([], expected={'retrieval': [], 'answer': []}),
            case([{'qid': 'z', 'old_docs': ['a'], 'new_docs': ['a']}, {'qid': 'y', 'old_docs': [], 'new_docs': []}],
                 expected={'retrieval': [], 'answer': ['z', 'y']}),
            case([{'qid': 'q1', 'old_docs': ['kb-1'], 'new_docs': ['kb-1', 'kb-2']}, {'qid': 'q2', 'old_docs': ['kb-3', 'kb-4'], 'new_docs': ['kb-4']}],
                 expected={'retrieval': ['q1', 'q2'], 'answer': []}),
        ],
        guided="""def sort_changes(changed):
    # Replace every ___ with real code, then run the tests.
    retrieval = []
    answer = []
    for item in changed:
        # Step 1: compare the two article lists as sets,
        # so their order doesn't matter. Not equal means
        # the articles changed.
        if ___:
            retrieval.append(item["qid"])
        else:
            # Step 2: same articles: add the qid to answer.
            ___
    return {"retrieval": retrieval, "answer": answer}
""",
        fills=['set(item["old_docs"]) != set(item["new_docs"])', 'answer.append(item["qid"])'],
        concepts=[
            [
                'Comparing as sets',
                '`set(a_list)` keeps the items and forgets their order. Two sets are equal when they hold the same items. `!=` means "not equal".',
                """a = set(["x", "y"])
a == set(["y", "x"])   # True
a != set(["x"])        # True""",
            ],
        ],
        byhand='billing-06: the new version dropped kb-12 and kb-02 and added kb-04 and kb-09. The sets differ, so retrieval. refund-11: the same three articles in a different order. The sets match, so answer. shipping-07: kb-03 was replaced by kb-07. The sets differ, so retrieval. Return retrieval ["billing-06", "shipping-07"] and answer ["refund-11"].',
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
        '**Drift** is when the mix of real questions moves away from your eval set. One simple measure: turn both into shares, add up the gap for each category, and halve it. 0 means the same mix, 1 means completely different.',
    ],
    example=example('The mix moved', """eval set:   billing 50% · shipping 30% · refunds 20%
production: billing 20% · shipping 30% · refunds 50%
shift:      gaps 0.3 + 0 + 0.3 = 0.6, halved = 0.3"""),
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
        pattern='Compare shares, add up the gaps',
        text='The big idea: when real questions move away from your eval set, its scores stop predicting real quality, so you measure that drift. Your code first adds up each list with `sum`. Then for each category it turns both counts into shares of their own total and takes the gap between them, using `abs` so the gap is never negative. It adds up the gaps and halves the result. 0 means the same mix, and 1 means completely different. Shares let you compare a list of 10 questions with one of 10,000.',
        say='"I compare category shares between the eval set and real traffic. When the shift gets too big, I refresh the eval set."',
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
        prompt="""Your function gets two lists of counts, one count per question category, with the categories in the same order:

- `baseline`: the counts in your eval set, like `[5, 3, 2]`.
- `current`: the counts in this week's real traffic, like `[4, 6, 10]`.

Turn each count into a share: the count divided by its own list's total. Then, for each category, take the gap between its two shares, ignoring which one is bigger. Add up the gaps and halve the result.

Return that shift rounded to 2 decimal places. 0 means the same mix, and 1 means a completely different one. Each list has at least one count above 0.""",
        pattern='Turn both lists into shares, then compare them category by category.',
        target='one walk through the categories',
        realworld='When the mix of real questions drifts from your eval set, eval scores stop predicting production quality. MLflow 3 production monitoring runs scorers on live traces; comparing category mix is a cheap first alarm that the eval set needs refreshing.',
        starter="""def mix_shift(baseline, current):
    # your code here
    pass
""",
        solution="""def mix_shift(baseline, current):
    baseline_total = sum(baseline)
    current_total = sum(current)
    gaps = 0
    for b, c in zip(baseline, current):
        b_share = b / baseline_total
        c_share = c / current_total
        gaps += abs(b_share - c_share)
    return round(gaps / 2, 2)
""",
        cases=[
            case([5, 3, 2], [4, 6, 10], expected=0.3, sample=True),
            case([500, 300, 200], [200, 300, 500], expected=0.3),
            case([10, 10], [20, 20], expected=0.0),
            case([1, 0], [0, 1], expected=1.0),
            case([3, 1], [1, 1], expected=0.25),
        ],
        guided="""def mix_shift(baseline, current):
    # Replace every ___ with real code, then run the tests.
    baseline_total = sum(baseline)
    current_total = sum(current)
    gaps = 0
    # b and c: one category's count in each list.
    for b, c in zip(baseline, current):
        # Step 1: turn each count into a share.
        b_share = b / baseline_total
        c_share = ___
        # Step 2: add the gap, ignoring the sign.
        gaps += ___
    # Step 3: half of all the gaps, to 2 places.
    return round(___, 2)
""",
        fills=['c / current_total', 'abs(b_share - c_share)', 'gaps / 2'],
        concepts=[
            ['sum', '`sum(a_list)` adds up all the numbers in a list.', 'sum([5, 3, 2])   # 10'],
            [
                'zip',
                'Walks two lists side by side, giving you one item from each.',
                """for x, y in zip([1, 2], [1, 5]):
    print(x == y)   # True, then False""",
            ],
            [
                'abs',
                '`abs(x)` drops the minus sign, if there is one. So the gap between two numbers is the same whichever comes first.',
                """abs(0.5 - 0.2)   # 0.3
abs(0.2 - 0.5)   # 0.3""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(0.30000004, 2)   # 0.3'],
        ],
        byhand='The baseline total is 10, so its shares are 0.5, 0.3 and 0.2. The current total is 20, so its shares are 0.2, 0.3 and 0.5. The gaps are 0.3, 0 and 0.3. They add up to 0.6, and half of that is 0.3. Return 0.3.',
        why='One walk through the categories.',
        gotchas=[
            [
                'Categories come from somewhere',
                'To compare mixes you need to categorise questions, often with a cheap classifier or Databricks\' `ai_classify` SQL function. Keep that step stable, or it causes drift itself.',
            ],
            [
                'Refresh the eval set on purpose',
                'When the mix shifts, sample new real questions into the eval set, and keep the old ones to catch regressions.',
            ],
        ],
    ),
)
