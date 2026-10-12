"""AI & ML foundations: How models learn from data, and how you know whether they're any good."""

from drill.content.model import angle, case, example, exercise, lesson, machine, module, question, stack

MODULE = module('foundations', 'AI & ML foundations', "How models learn from data, and how you know whether they're any good.")

lesson(MODULE, 'split_by_key',
    title='Train, validation and test data',
    learn=[
        'A model learns patterns from **training** data. To find out whether it learned something real or just memorised, you test it on data it has never seen: the **test** set. A third set, **validation**, is for tuning choices like thresholds (the score a model needs before it says yes) without touching the test set.',
        "The split has to be honest. If the same customer, document or day appears in both training and test, the test score is inflated. This is called **leakage**, and it's the most common reason a model that looked great disappoints in production (the live system real users depend on).",
    ],
    example=example('Splitting by user, not by row', """test_users = set(['u1', 'u7'])
train = []
test = []
for row in rows:
    if row['user'] in test_users:
        test.append(row)
    else:
        train.append(row)"""),
    check=question(
        "A model scores 97% in testing and 70% in production. Rows from the same users were in both training and test. What's the likely cause?",
        [
            'The model is too small',
            'Leakage: it was tested on people it had already seen',
            'The test set was too large',
        ],
        answer=1,
        why='Seeing the same users in training made the test easy. Splitting by user would have given a more honest, lower score.',
    ),
    angle=angle(
        pattern='Set lookup',
        text='You check every row against a set of test values. A set answers "is this in here?" in one step however big it is, so the whole split is a single walk through the rows. Checking a list instead means scanning the list for every row, which gets slow fast.',
        say='"I put the test keys in a set so each check is instant, which makes the split one pass over the rows."',
        classic='two_sum',
    ),
    stack=stack('MLflow: record which data trained the model', """with mlflow.start_run(run_name="churn-split-by-user"):
    mlflow.log_params({"split": "by_user", "test_users": len(test_users)})
    mlflow.log_input(mlflow.data.from_pandas(train_df, name="train"), context="training")"""),
    exercise=exercise(
        title='Split Without Leaking',
        topic='foundations',
        difficulty='easy',
        fn='split_by_key',
        machine=machine(bins=['train', 'test'], who=['everyone else', 'rows of the test users'], label_arg=1, leak_arg=1),
        prompt="""Your function gets three things:

- `rows`: the data, a list of rows. Each row is a dict (named values in curly braces), like `{"user": "u1", "label": 1}`.
- `key`: the name of the field to split on, like `"user"`.
- `test_values`: the values of that field that go to the test set, like `["u1"]`.

Look at each row's value for `key`. With `key = "user"`, that is `row["user"]`. You only look at that field. Other fields, like `label`, just come along with the row.

If the value is in `test_values`, add the row to a `test` list. Otherwise, add it to a `train` list. Keep the rows in their original order.

Return `[train, test]`, train first.""",
        pattern='Turn the test values into a set, then one pass that sends each row to train or to test.',
        target='one pass over the rows',
        realworld='Splitting by user (or by document, or by day) instead of row by row keeps the same person out of both sides. Otherwise the model is tested on people it has already seen, and the score looks better than it will be in production.',
        starter="""def split_by_key(rows, key, test_values):
    # your code here
    pass
""",
        solution="""def split_by_key(rows, key, test_values):
    test_set = set(test_values)
    train = []
    test = []
    for row in rows:
        if row[key] in test_set:
            test.append(row)
        else:
            train.append(row)
    return [train, test]
""",
        cases=[
            case([
                {'user': 'u1', 'label': 1},
                {'user': 'u2', 'label': 0},
                {'user': 'u1', 'label': 0},
                {'user': 'u3', 'label': 1},
            ], 'user', ['u1'], expected=[
                [{'user': 'u2', 'label': 0}, {'user': 'u3', 'label': 1}],
                [{'user': 'u1', 'label': 1}, {'user': 'u1', 'label': 0}],
            ], sample=True),
            case([], 'user', ['u1'], expected=[[], []]),
            case([{'doc': 'a'}, {'doc': 'b'}], 'doc', [], expected=[[{'doc': 'a'}, {'doc': 'b'}], []]),
            case([{'day': '2026-10-01'}, {'day': '2026-10-02'}, {'day': '2026-10-03'}], 'day', ['2026-10-03', '2026-10-02'], expected=[[{'day': '2026-10-01'}], [{'day': '2026-10-02'}, {'day': '2026-10-03'}]]),
        ],
        guided="""def split_by_key(rows, key, test_values):
    # Replace every ___ with real code, then run the tests.

    # Step 1: a set makes "is this a test value?" instant.
    test_set = set(test_values)
    train = []
    test = []

    for row in rows:
        # Step 2: get this row's value for key.
        # If it is in the set, the row goes to test.
        if ___ in test_set:
            test.append(row)
        else:
            # Step 3: otherwise, add the row to train.
            ___

    return [train, test]
""",
        fills=['row[key]', 'train.append(row)'],
        concepts=[
            [
                'for and if/else',
                '`for row in rows:` runs the indented lines once for each row. `if ...:` runs its lines when the condition is True; `else:` runs its lines when it is not.',
                """small = []
big = []
for n in [3, 8, 1]:
    if n > 5:   # is n above 5?
        big.append(n)
    else:
        small.append(n)
# big is [8], small is [3, 1]""",
            ],
            [
                'Sets',
                'A set is a group of values with no repeats. Checking `x in some_set` is instant. `x in some_list` checks every item.',
                """colors = set(['red', 'blue'])
'red' in colors    # True
'green' in colors  # False""",
            ],
            [
                'Dict access',
                "A dict holds named values in curly braces. `person['name']` gets one of them. `person[field]` works when the name is in a variable.",
                """person = {'name': 'Ann', 'age': 30}
field = 'name'
person[field]   # 'Ann'""",
            ],
            [
                'Adding to a list',
                '`my_list.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ann')   # ['Ann']
names.append('Bo')    # ['Ann', 'Bo']""",
            ],
        ],
        byhand="The test values are just u1. Row 1's user is u1, a test value, so it goes to test. Row 2's user is u2, so it goes to train. Row 3's user is u1: test. Row 4's user is u3: train. Returns [train, test]: first the u2 and u3 rows, then the two u1 rows.",
        why='One pass over the rows; each set check is instant.',
        gotchas=[
            [
                'Duplicates leak too',
                'The same text can appear under two users (copied tickets, templates). Remove duplicates before splitting, or the test set still contains things the model trained on.',
            ],
            [
                'Time order matters',
                'For anything that predicts the future, split by date: train on the past, test on later data. A random split lets the model peek ahead.',
            ],
        ],
    ),
)

lesson(MODULE, 'precision_recall',
    title='Precision, recall and why accuracy lies',
    learn=[
        '**Precision**: of everything the model flagged, how much was right? **Recall**: of everything it should have flagged, how much did it catch?',
        'When one class, or kind of answer, is rare (fraud, outages, toxic content), **accuracy** (the share of all answers that are right) is misleading: if 1 in 100 cases is fraud, always answering "no" scores 99%. Precision and recall show what the model actually does on the cases you care about, and they trade off against each other.',
    ],
    example=example('The three counts behind both numbers', """tp = predicted yes, really yes
fp = predicted yes, really no
fn = predicted no,  really yes
precision = tp / (tp + fp)
recall    = tp / (tp + fn)"""),
    check=question(
        'A spam filter flags 10 emails; 8 are spam. There were 40 spam emails in total. What are precision and recall?',
        ['Precision 0.8, recall 0.2', 'Precision 0.2, recall 0.8', 'Precision 0.8, recall 0.8'],
        answer=0,
        why='Precision is 8 of the 10 flagged. Recall is 8 of the 40 spam emails that existed.',
    ),
    angle=angle(
        pattern='Counting in one pass',
        text='Each pair goes into one bucket and gets counted, in one walk through the lists, with just three counters. Interviewers like to hear that you guard against dividing by zero.',
        say='"One pass to count true positives, false positives and false negatives, then two divisions, each guarded in case the bottom number is zero."',
        classic=None,
    ),
    stack=stack('MLflow: log both numbers on every run', """mlflow.sklearn.autolog()   # params, metrics and the model on every fit
mlflow.log_metrics({"precision": 0.67, "recall": 0.67})"""),
    exercise=exercise(
        title='Precision and Recall',
        topic='foundations',
        difficulty='easy',
        fn='precision_recall',
        prompt="""Your function gets two things:

- `predictions`: a model's answer for each example, `1` (yes) or `0` (no), like `[1, 0, 1]`.
- `labels`: the right answers, in the same order, like `[1, 1, 0]`.

Go through the pairs (each prediction with its label) and count:

- `tp` (true positive): predicted 1, really 1.
- `fp` (false positive): predicted 1, really 0.
- `fn` (false negative): predicted 0, really 1.

Skip pairs where both are 0.

Precision is `tp / (tp + fp)`: the share of the model's 1s that were right. Recall is `tp / (tp + fn)`: the share of real 1s the model caught.

If the number you divide by is 0, use 0 instead. Return `[precision, recall]`, each rounded to 2 decimal places.""",
        pattern='Count three things in one pass, then divide, checking first that you are not dividing by 0.',
        target='one pass over the pairs',
        realworld='Accuracy hides problems when one class is rare. If 1 in 100 transactions is fraud, a model that always says "not fraud" is 99% accurate and catches nothing: its recall is 0. Precision and recall show the trade-off you actually have to choose.',
        starter="""def precision_recall(predictions, labels):
    # your code here
    pass
""",
        solution="""def precision_recall(predictions, labels):
    tp = 0
    fp = 0
    fn = 0
    for pred, label in zip(predictions, labels):
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 1:
            fn += 1
    precision = 0
    if tp + fp > 0:
        precision = round(tp / (tp + fp), 2)
    recall = 0
    if tp + fn > 0:
        recall = round(tp / (tp + fn), 2)
    return [precision, recall]
""",
        cases=[
            case([1, 1, 0, 0, 0], [1, 0, 1, 0, 1], expected=[0.5, 0.33], sample=True),
            case([1, 1, 0, 1, 0], [1, 0, 0, 1, 1], expected=[0.67, 0.67]),
            case([1, 0, 0], [1, 1, 1], expected=[1.0, 0.33]),
            case([0, 0], [0, 0], expected=[0.0, 0.0]),
            case([1, 1], [0, 0], expected=[0.0, 0.0]),
            case([], [], expected=[0.0, 0.0]),
            case([1, 1, 1, 1], [1, 1, 1, 0], expected=[0.75, 1.0]),
        ],
        guided="""def precision_recall(predictions, labels):
    # Replace every ___ with real code, then run the tests.
    tp = 0
    fp = 0
    fn = 0

    # Step 1: walk both lists together, count each kind.
    for pred, label in zip(predictions, labels):
        if pred == 1 and label == 1:
            tp += 1
        elif ___:   # fp: predicted 1, really 0
            fp += 1
        elif pred == 0 and label == 1:
            fn += 1

    # Step 2: divide, but only if you are not dividing by 0.
    precision = 0
    if tp + fp > 0:
        precision = round(tp / (tp + fp), 2)
    # Recall: the same steps, with fn in place of fp.
    recall = 0
    if ___:
        recall = ___
    return [precision, recall]
""",
        fills=['pred == 1 and label == 0', 'tp + fn > 0', 'round(tp / (tp + fn), 2)'],
        concepts=[
            [
                'zip',
                'Walks two lists side by side, one pair at a time.',
                """for x, y in zip([1, 2], [5, 6]):
    print(x, y)   # 1 5, then 2 6""",
            ],
            [
                'elif and "and"',
                '`elif` means "else, if": Python tries each condition in order and runs the first one that is true. `a and b` is true only when both sides are true. `==` asks "are these equal?" and gives True or False. A single `=` stores a value in a name.',
                """x = 1
y = 0
x == 1 and y == 0   # True""",
            ],
            [
                'Counting with +=',
                '`count += 1` adds 1 to `count`. It is short for `count = count + 1`.',
                """count = 0
count += 1
count += 1   # count is now 2""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
        ],
        byhand='Pair 1: predicted 1, really 1, so tp. Pair 2: predicted 1, really 0, so fp. Pair 3: predicted 0, really 1, so fn. Pair 4: both 0, not counted. Pair 5: predicted 0, really 1, so fn. That makes tp 1, fp 1, fn 2. Precision is tp divided by the total of tp and fp: 1 divided by (1 + 1), which is 0.5. Recall is tp divided by the total of tp and fn: 1 divided by (1 + 2), which is 0.333, rounded to 0.33. Returns [0.5, 0.33].',
        why='One pass to count, then two divisions.',
        gotchas=[
            [
                'Pick the metric before training',
                "Missing fraud (low recall) and blocking good customers (low precision) cost different amounts. Decide which matters more first, or you'll pick whichever number looks best.",
            ],
            [
                'Averages across classes',
                'With more than two classes, you can average the score of each class (every class counts the same), or count all examples together (big classes count more). The two can tell very different stories.',
            ],
        ],
    ),
)

lesson(MODULE, 'best_threshold',
    title='From scores to decisions',
    learn=[
        'Most classifiers (models that sort things into groups, like spam or not spam) output a **score**, not a yes/no. You choose a **threshold**: at or above it means yes. Moving it trades precision against recall.',
        'You tune the threshold on the validation set, then check it once on the test set. The best threshold for accuracy is often not the one the business wants.',
    ],
    example=example('Same scores, different thresholds', """scores = [0.9, 0.65, 0.4]
# t = 0.5  -> [1, 1, 0]
# t = 0.7  -> [1, 0, 0]  fewer yes: usually higher precision, lower recall"""),
    check=question(
        'You raise the threshold from 0.5 to 0.9. What usually happens?',
        ['Precision goes up, recall goes down', 'Both go up', 'Recall goes up, precision goes down'],
        answer=0,
        why='Fewer things pass a stricter threshold, so the ones that do are more often right (precision up), but more true cases are missed (recall down).',
    ),
    angle=angle(
        pattern='Try every threshold, keep the best',
        text='You tried each threshold, counted how many it got right, and kept the best so far. That is the right first answer. On big data it gets slow, because it checks every threshold against every example: 10,000 examples means 100 million checks. A faster way is to sort the examples by score first. Then you can move the threshold one example at a time and update the count as you go. The same sort-first idea solves Merge Intervals.',
        say='"I try every threshold and keep the one with the best accuracy. On big data I would sort by score first, so each step changes one prediction and I update the count instead of recounting."',
        classic='merge_intervals',
    ),
    stack=stack('MLflow: the threshold is a parameter', """with mlflow.start_run(run_name="threshold-0.65"):
    mlflow.log_param("threshold", 0.65)
    mlflow.log_metric("val_accuracy", 1.0)"""),
    exercise=exercise(
        title='Choose a Decision Threshold',
        topic='foundations',
        difficulty='medium',
        fn='best_threshold',
        prompt="""Your function gets two things:

- `scores`: the model's score for each example, from 0 to 1, like `[0.9, 0.2]`. There is at least one.
- `labels`: the right answer for each example, `1` (yes) or `0` (no), in the same order, like `[1, 0]`.

A threshold turns a score into a decision: `1` if the score is equal to or above the threshold, otherwise `0`.

Try each score in `scores` as the threshold. For each one, count how many decisions match `labels`. Return the threshold that gets the most right (the highest accuracy). There is always just one best threshold.""",
        pattern='Try each threshold, count how many it gets right, and keep the best so far.',
        target='a loop inside a loop is fine here',
        realworld='Classifiers output scores, and someone has to choose where to cut. Teams tune the threshold on a validation set, never on the test set, and often for precision or recall rather than accuracy.',
        starter="""def best_threshold(scores, labels):
    # your code here
    pass
""",
        solution="""def best_threshold(scores, labels):
    best = None
    best_right = -1
    for threshold in scores:
        right = 0
        for score, label in zip(scores, labels):
            if score >= threshold:
                decision = 1
            else:
                decision = 0
            if decision == label:
                right += 1
        if right > best_right:
            best = threshold
            best_right = right
    return best
""",
        cases=[
            case([0.9, 0.2, 0.65, 0.4], [1, 0, 1, 0], expected=0.65, sample=True),
            case([0.5], [1], expected=0.5),
            case([0.3, 0.8, 0.6], [0, 0, 1], expected=0.6),
            case([0.1, 0.9], [1, 0], expected=0.1),
            case([0.7, 0.7, 0.2], [1, 0, 0], expected=0.7),
            case([0.3, 0.6, 0.9], [1, 1, 1], expected=0.3),
            case([0.2, 0.5, 0.8], [0, 0, 1], expected=0.8),
        ],
        guided="""def best_threshold(scores, labels):
    # Replace every ___ with real code, then run the tests.
    best = None       # None means nothing picked yet
    best_right = -1   # any count beats -1

    # Step 1: try each score as the threshold.
    for threshold in scores:
        right = 0
        for score, label in zip(scores, labels):
            # Step 2: decision is 1 if score is equal to
            # or above threshold, else 0.
            if ___:
                decision = 1
            else:
                decision = 0
            if decision == label:
                right += 1
        # Step 3: if right is more than best_right, keep it.
        if ___:
            best = threshold
            best_right = right
    return best
""",
        fills=['score >= threshold', 'right > best_right'],
        concepts=[
            [
                'Comparing numbers',
                '`a >= b` means "a is equal to or above b". `a > b` means "a is above b", so it is False when they are equal.',
                """0.65 >= 0.65   # True
0.65 > 0.65    # False""",
            ],
            [
                'zip',
                'Walks two lists side by side, one pair at a time.',
                """for x, y in zip([1, 2], [5, 6]):
    print(x, y)   # 1 5, then 2 6""",
            ],
            [
                'A loop inside a loop',
                'The inner loop runs all the way through for each item of the outer loop. This prints 4 lines.',
                """for size in ['S', 'M']:
    for color in ['red', 'blue']:
        print(size, color)""",
            ],
            [
                'Keeping the best so far',
                'Start with a value anything beats. Replace it each time you find something better. Here `best_count` ends as 7.',
                """best_count = -1
for n in [3, 7, 5]:
    if n > best_count:
        best_count = n""",
            ],
            [
                'Counting with +=',
                '`count += 1` adds 1 to `count`. It is short for `count = count + 1`.',
                """count = 0
count += 1
count += 1   # count is now 2""",
            ],
        ],
        byhand='The right answers are 1, 0, 1, 0. Threshold 0.9: decisions 1, 0, 0, 0, so 3 right. Threshold 0.2: decisions 1, 1, 1, 1, so 2 right. Threshold 0.65: decisions 1, 0, 1, 0, so 4 right. Threshold 0.4: decisions 1, 0, 1, 1, so 3 right. 0.65 gets the most right, so it returns 0.65.',
        why='Trying every threshold and checking every example means checking every pair, which slows down a lot on big data. Sorting by score first lets you move the threshold one example at a time and keep a running count.',
        gotchas=[
            [
                'Tuning on the test set',
                'If you pick the threshold using the test set, the test score is no longer an honest estimate. Use a separate validation set.',
            ],
            [
                'Thresholds drift',
                "When the incoming data changes, the scores shift and yesterday's best threshold quietly gets worse. Monitor the rate of positive predictions.",
            ],
        ],
    ),
)

lesson(MODULE, 'average_precision',
    title='Quality across every threshold: PR-AUC',
    learn=[
        "Precision and recall depend on where you set the threshold. To judge the model itself, across every possible threshold, you draw how it does at each threshold as a curve and measure the **area under the curve** (AUC). Bigger is better. You don't need to draw it: below, each AUC is put in plain words, and PR-AUC comes with a simple walk down the list that gives the same number.",
        "**ROC-AUC** (ROC is just a name to remember; it comes from old radar work) is the chance that a random real positive (an example that is really 1) gets a higher score than a random negative (an example that is really 0): 0.5 is guessing, 1.0 is perfect. It's popular, but when positives are rare it flatters the model, because there are so many easy negatives to rank below them.",
        "**PR-AUC** is the area under the precision-recall curve, usually computed as **average precision**: walk down the list from the highest score, and each time you reach a real positive, note the precision so far. Average those. For rare events (fraud, failures, the one document that answers a question) it is the honest number. Its baseline (what random guessing scores) is the share of positives, not 0.5: a random model on 1% positives scores about 0.01.",
    ],
    example=example('Average precision, by hand', """score  label   precision each time a real positive is reached
0.95     1     1 of 1 = 1.00
0.80     0
0.70     1     2 of 3 = 0.67
0.40     0
0.20     1     3 of 5 = 0.60
average precision = (1.00 + 0.67 + 0.60) / 3, about 0.76"""),
    check=question(
        'Fraud is 1 in 200 transactions. Your model has ROC-AUC 0.97 and PR-AUC 0.18. What is true?',
        [
            'The model is excellent: 0.97 is near perfect',
            "ROC-AUC flatters it. PR-AUC shows most of what it flags isn't fraud, though it's far better than random",
            'PR-AUC must be a bug when ROC-AUC is that high',
        ],
        answer=1,
        why='A random model would score about 0.005 PR-AUC here, so 0.18 is real skill. But it also means most alerts are false alarms, which ROC-AUC hides.',
    ),
    angle=angle(
        pattern='Sort, then one walk with running counts',
        text="Sort the examples by score, highest first. Then walk down once, counting how many you've seen and how many were real positives, and add up the precision at each positive. Sorting is the slowest step.",
        say='"For rare positives I report PR-AUC, computed as average precision, because ROC-AUC looks great on easy negatives."',
        classic=None,
    ),
    stack=stack('scikit-learn and MLflow', """from sklearn.metrics import average_precision_score, roc_auc_score

mlflow.log_metrics({
    "pr_auc": average_precision_score(labels, scores),
    "roc_auc": roc_auc_score(labels, scores),
})"""),
    exercise=exercise(
        title='Average Precision',
        topic='foundations',
        difficulty='medium',
        fn='average_precision',
        prompt="""Your function gets two things:

- `scores`: the model's score for each example, like `[0.2, 0.95, 0.4]`. No two scores are the same.
- `labels`: for each example, `1` if it really is a positive (the thing you are looking for) or `0` if not, in the same order, like `[1, 1, 0]`.

Sort the examples by score, highest first, keeping each label with its score, and walk down the list. Each time you reach a positive, work out the precision so far: positives found so far divided by examples seen so far.

Return the average of those precisions: add them up, then divide by the number of positives. Round it to 2 decimal places. If there are no positives, return 0.""",
        pattern='Sort by score, then one walk down the list keeping two counts.',
        target='a sort, then one walk down the list',
        realworld='Fraud, safety and retrieval teams report PR-AUC (average precision) because the thing they care about is rare. scikit-learn calls it `average_precision_score`.',
        starter="""def average_precision(scores, labels):
    # your code here
    pass
""",
        solution="""def average_precision(scores, labels):
    positives = sum(labels)
    if positives == 0:
        return 0
    pairs = sorted(zip(scores, labels), reverse=True)
    seen = 0
    found = 0
    total = 0.0
    for score, label in pairs:
        seen += 1
        if label == 1:
            found += 1
            total += found / seen
    return round(total / positives, 2)
""",
        cases=[
            case([0.2, 0.95, 0.4, 0.8, 0.7], [1, 1, 0, 0, 1], expected=0.76, sample=True),
            case([0.9, 0.8, 0.1], [1, 1, 0], expected=1.0),
            case([0.9, 0.8, 0.1], [0, 0, 1], expected=0.33),
            case([0.5, 0.4], [0, 0], expected=0.0),
            case([0.9, 0.6, 0.5, 0.3], [0, 1, 1, 0], expected=0.58),
        ],
        guided="""def average_precision(scores, labels):
    # Replace every ___ with real code, then run the tests.
    positives = sum(labels)
    if positives == 0:
        return 0

    # Step 1: pair each score with its label, highest first.
    pairs = sorted(zip(scores, labels), reverse=True)

    seen = 0      # examples seen so far
    found = 0     # positives found so far
    total = 0.0   # the precisions added up
    # Step 2: at each positive, add the precision so far.
    for score, label in pairs:
        seen += 1
        if label == 1:
            found += 1
            total += ___
    # Step 3: average: divide the total by the positives.
    return round(___, 2)
""",
        fills=['found / seen', 'total / positives'],
        concepts=[
            [
                'Pairing and sorting',
                '`zip(a, b)` pairs the items up. `sorted(..., reverse=True)` sorts the pairs by their first item, biggest first. A `for` loop can then take each pair apart: `for age, name in pairs:`.',
                """pairs = sorted(zip([30, 45], ['Ann', 'Bo']), reverse=True)
# [(45, 'Bo'), (30, 'Ann')]""",
            ],
            ['sum', '`sum(numbers)` adds up a list. On a list of 1s and 0s it counts the 1s.', 'sum([1, 0, 1])   # 2'],
            [
                'Counting with +=',
                '`count += 1` adds 1 to `count`. It is short for `count = count + 1`.',
                """count = 0
count += 1
count += 1   # count is now 2""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
        ],
        byhand='There are 3 positives. Sorted by score: 0.95 (positive), 0.8, 0.7 (positive), 0.4, 0.2 (positive). At 0.95: 1 positive found in 1 seen, precision 1.0. At 0.7: 2 found in 3 seen, 0.667. At 0.2: 3 found in 5 seen, 0.6. 1.0, 0.667 and 0.6 add up to 2.267. Divided by the 3 positives, that is 0.756, which rounds to 0.76. Returns 0.76.',
        why='Sorting is the slowest step; the walk after it looks at each example once.',
        gotchas=[
            [
                'Know the baseline',
                'A PR-AUC of 0.3 is poor when half the examples are positive, and excellent when 1 in 100 is. Always say what share is positive.',
            ],
            [
                'Ties in scores',
                'Real models often give equal scores. Libraries handle ties carefully; this exercise keeps the scores distinct so the order is clear.',
            ],
        ],
    ),
)

lesson(MODULE, 'calibration_table',
    title='Are the probabilities honest?',
    learn=[
        'A model that says "70% likely" should be right about 70% of the time when it says that. That is **calibration**. Many models are overconfident, and LLMs (large language models, the kind behind chatbots) asked to rate their own confidence often are.',
        "To check, put the predictions into buckets by their probability (0-20%, 20-40%, and so on) and compare, in each bucket, the average prediction with how often the thing really happened. In a calibrated model the two numbers match. The chart of these pairs is called a **reliability diagram**.",
        'One number for all of it is the **Brier score**. For each prediction, take the gap between the predicted probability and what happened (1 or 0), and multiply the gap by itself. The Brier score is the average of those. Lower is better, 0 is perfect, and always guessing 50% scores 0.25.',
        'Calibration matters whenever the probability itself drives a decision: auto-approve above 90%, send to a person below. An overconfident model makes that threshold mean something it does not.',
    ],
    example=example('A reliability table', """bucket      predictions   average prediction   really happened
0-20%           40              0.12                0.10   ✓ close
40-60%          25              0.51                0.48   ✓ close
80-100%         35              0.92                0.61   ✗ overconfident"""),
    check=question(
        'In the 80-100% bucket the average prediction is 0.92 but only 61% really happened. What does that mean for an "auto-approve above 90%" rule?',
        [
            'Nothing, the threshold is still 90%',
            'The model is overconfident, so many "90%+" cases are wrong. The rule approves far more mistakes than it seems to',
            'The model is underconfident, so lower the threshold',
        ],
        answer=1,
        why='The threshold assumes 90% means 90%. Here it means about 61%. Recalibrate the scores (adjust them so 0.9 really means about 90%), or set the threshold from the table.',
    ),
    angle=angle(
        pattern='Buckets as a list of totals',
        text='Work out each prediction\'s bucket number with one multiplication, and keep running totals per bucket in lists. One pass over the predictions, then one over the buckets.',
        say='"Before I put a probability threshold in front of a decision, I check calibration with a reliability table and the Brier score."',
        classic=None,
    ),
    stack=stack('scikit-learn: reliability curve and Brier score', """from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

really, predicted = calibration_curve(outcomes, predictions, n_bins=5)
mlflow.log_metric("brier", brier_score_loss(outcomes, predictions))"""),
    exercise=exercise(
        title='The Reliability Table',
        topic='foundations',
        difficulty='medium',
        fn='calibration_table',
        prompt="""Your function gets two things:

- `predictions`: how likely the model said each thing was, from 0 to just under 1, like `[0.1, 0.9]`.
- `outcomes`: what really happened, `1` (it did) or `0` (it didn't), in the same order, like `[0, 1]`.

Put each prediction `p` in a bucket numbered 0 to 4 with `int(p * 5)`. `int` cuts off the decimals, so `int(1.75)` is `1`. Bucket 0 holds 0 to 0.2, bucket 1 holds 0.2 to 0.4, and so on.

Go from bucket 0 up to bucket 4, skipping empty ones. For each, make a row `[bucket, average, share]`:

- `average`: its predictions added up, divided by how many it has.
- `share`: how many of its outcomes are 1, divided by how many it has.

Round both to 2 decimal places. Return the list of rows.""",
        pattern='Add up totals per bucket in one pass, then one pass over the buckets to build the rows.',
        target='one pass over the predictions, then one over the buckets',
        realworld='A reliability table is how you find out whether "confidence: 0.9" from a model or an LLM judge (an LLM that grades answers) can be used as a threshold, or needs recalibrating first.',
        starter="""def calibration_table(predictions, outcomes):
    # your code here
    pass
""",
        solution="""def calibration_table(predictions, outcomes):
    counts = [0, 0, 0, 0, 0]
    totals = [0, 0, 0, 0, 0]
    happened = [0, 0, 0, 0, 0]
    for p, outcome in zip(predictions, outcomes):
        bucket = int(p * 5)
        counts[bucket] += 1
        totals[bucket] += p
        happened[bucket] += outcome
    rows = []
    for bucket in range(5):
        if counts[bucket] > 0:
            average = round(totals[bucket] / counts[bucket], 2)
            share = round(happened[bucket] / counts[bucket], 2)
            rows.append([bucket, average, share])
    return rows
""",
        cases=[
            case([0.25, 0.35, 0.9, 0.95, 0.85], [0, 1, 1, 0, 1], expected=[[1, 0.3, 0.5], [4, 0.9, 0.67]], sample=True),
            case([0.1, 0.3, 0.9, 0.95, 0.85], [0, 1, 1, 0, 1], expected=[[0, 0.1, 0.0], [1, 0.3, 1.0], [4, 0.9, 0.67]]),
            case([], [], expected=[]),
            case([0.1, 0.16, 0.35, 0.9, 0.95, 0.85], [0, 0, 1, 1, 0, 1], expected=[[0, 0.13, 0.0], [1, 0.35, 1.0], [4, 0.9, 0.67]]),
            case([0.25, 0.35, 0.65, 0.75], [0, 1, 1, 1], expected=[[1, 0.3, 0.5], [3, 0.7, 1.0]]),
            case([0.5, 0.45, 0.55], [1, 0, 0], expected=[[2, 0.5, 0.33]]),
            case([0.99], [1], expected=[[4, 0.99, 1.0]]),
        ],
        guided="""def calibration_table(predictions, outcomes):
    # Replace every ___ with real code, then run the tests.
    counts = [0, 0, 0, 0, 0]     # predictions per bucket
    totals = [0, 0, 0, 0, 0]     # predictions added up
    happened = [0, 0, 0, 0, 0]   # outcomes that were 1

    for p, outcome in zip(predictions, outcomes):
        # Step 1: the bucket is p times 5, decimals cut off.
        bucket = ___
        counts[bucket] += 1
        totals[bucket] += p
        happened[bucket] += outcome

    # Step 2: one row per bucket that has predictions.
    rows = []
    for bucket in range(5):
        if counts[bucket] > 0:
            average = round(totals[bucket] / counts[bucket], 2)
            # share: happened, divided by the count
            share = round(___, 2)
            rows.append([bucket, average, share])
    return rows
""",
        fills=['int(p * 5)', 'happened[bucket] / counts[bucket]'],
        concepts=[
            [
                'Bucket number',
                'Multiply by 5, then `int` cuts off the decimals.',
                'int(0.35 * 5)   # 1.75 becomes 1',
            ],
            [
                'A list of totals',
                '`totals[1]` is the slot at position 1 (positions start at 0). `totals[1] += 0.3` adds 0.3 to that slot. Keep one slot per bucket.',
                """totals = [0, 0]
totals[1] += 0.3
# totals is now [0, 0.3]""",
            ],
            [
                'zip',
                'Walks two lists side by side, one pair at a time.',
                """for x, y in zip([1, 2], [5, 6]):
    print(x, y)   # 1 5, then 2 6""",
            ],
            [
                'range',
                '`range(5)` gives 0, 1, 2, 3 and 4, one at a time.',
                """for i in range(3):
    print(i)   # 0, then 1, then 2""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
            [
                'Adding to a list',
                '`my_list.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ann')   # ['Ann']""",
            ],
        ],
        byhand='0.25 and 0.35 times 5 are 1.25 and 1.75: bucket 1. 0.9, 0.95 and 0.85 times 5 are 4.5, 4.75 and 4.25: bucket 4. Buckets 0, 2 and 3 are empty, so they get no row. Bucket 1: 0.25 and 0.35 add up to 0.6. 0.6 divided by 2 is 0.3. 1 of its 2 outcomes is 1: 1 divided by 2 is 0.5. Row [1, 0.3, 0.5]. Bucket 4: 0.9, 0.95 and 0.85 add up to 2.7. 2.7 divided by 3 is 0.9. 2 of its 3 outcomes are 1: 2 divided by 3 is 0.667, rounded to 0.67. Row [4, 0.9, 0.67]. The model said about 0.9, but it happened only 0.67 of the time: it is overconfident. Returns [[1, 0.3, 0.5], [4, 0.9, 0.67]].',
        why='One step per prediction, then one per bucket.',
        gotchas=[
            [
                'Small buckets are noisy',
                'A bucket with 3 predictions tells you little. Use fewer buckets, or more data, before concluding the model is miscalibrated.',
            ],
            [
                'Calibrated is not the same as good',
                'A model that gives every example the same overall rate (say 5%, when 5% of cases are positive) is perfectly calibrated and useless. Look at calibration alongside PR-AUC or precision and recall.',
            ],
        ],
    ),
)
