"""AI & ML foundations: How models learn from data, and how you know whether they're any good."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('foundations', 'AI & ML foundations', "How models learn from data, and how you know whether they're any good.")

lesson(MODULE, 'split_by_key',
    title='Train, validation and test data',
    learn=[
        'A model learns patterns from **training** data. To find out whether it learned something real or just memorised, you test it on data it has never seen: the **test** set. A third set, **validation**, is for tuning choices like thresholds without touching the test set.',
        "The split has to be honest. If the same customer, document or day appears in both training and test, the test score is inflated. This is called **leakage**, and it's the most common reason a model that looked great disappoints in production.",
    ],
    example=example('Splitting by user, not by row', """test_users = {'u1', 'u7'}
train = [r for r in rows if r['user'] not in test_users]
test  = [r for r in rows if r['user'] in test_users]"""),
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
        pattern='Hash set lookup',
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
        prompt="""`rows` is a list of dicts like `{"user": "u1", "text": "refund please", "label": 1}`. Split them into training and test sets by one field: every row whose value for `key` is in `test_values` goes to test, the rest go to training. Keep the original order in both.

Return `[train, test]`.""",
        pattern='Turn the test values into a set, then one pass that sends each row left or right.',
        target='one pass over the rows',
        realworld='Splitting by user (or by document, or by day) instead of row by row keeps the same person out of both sides. Otherwise the model is tested on people it has already seen, and the score looks better than it will be in production.',
        starter="""def split_by_key(rows, key, test_values):
    # your code here
    pass
""",
        solution="""def split_by_key(rows, key, test_values):
    test_set = set(test_values)
    train, test = [], []
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

    # Step 1: a set makes "is this value a test value?" instant.
    test_set = set(test_values)
    train, test = [], []

    for row in rows:
        # Step 2: look up this row's value for the key, and check the set.
        if ___ in test_set:
            test.append(row)
        else:
            ___

    return [train, test]
""",
        fills=['row[key]', 'train.append(row)'],
        concepts=[
            [
                'Set membership',
                '`x in some_set` is instant. `x in some_list` checks every item.',
                """test_set = set(['u1', 'u7'])
'u1' in test_set   # True""",
            ],
            [
                'Dict access',
                "`row['user']` gets one field of a row. `row[key]` works when the field name is in a variable.",
                """row = {'user': 'u1'}
key = 'user'
row[key]   # 'u1'""",
            ],
        ],
        byhand='Test users: u1. Row 1 is u1: test. Row 2 is u2: train. Row 3 is u1: test. Row 4 is u3: train. Train is rows 2 and 4, test is rows 1 and 3, each in their original order.',
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
        'When one class is rare (fraud, outages, toxic content), accuracy is misleading: always answering "no" can score 99%. Precision and recall show what the model actually does on the cases you care about, and they trade off against each other.',
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
        prompt="""A classifier predicts 1 (yes) or 0 (no). `preds` are its predictions and `labels` are the right answers, in the same order.

Count true positives (predicted 1, really 1), false positives (predicted 1, really 0) and false negatives (predicted 0, really 1). Then:

- precision = true positives / (true positives + false positives)
- recall = true positives / (true positives + false negatives)

Return `[precision, recall]`, each rounded to 2 decimal places. If a bottom number is 0, that value is `0.0`.""",
        pattern='Count three things in one pass, then divide, guarding each division.',
        target='one pass over the pairs',
        realworld='Accuracy hides problems when one class is rare. A fraud model that always says "not fraud" is 99% accurate and catches nothing: its recall is 0. Precision and recall show the trade-off you actually have to choose.',
        starter="""def precision_recall(preds, labels):
    # your code here
    pass
""",
        solution="""def precision_recall(preds, labels):
    tp = fp = fn = 0
    for p, y in zip(preds, labels):
        if p == 1 and y == 1:
            tp += 1
        elif p == 1 and y == 0:
            fp += 1
        elif p == 0 and y == 1:
            fn += 1
    precision = round(tp / (tp + fp), 2) if tp + fp else 0.0
    recall = round(tp / (tp + fn), 2) if tp + fn else 0.0
    return [precision, recall]
""",
        cases=[
            case([1, 1, 0, 1, 0], [1, 0, 0, 1, 1], expected=[0.67, 0.67], sample=True),
            case([1, 0, 0], [1, 1, 1], expected=[1.0, 0.33]),
            case([0, 0], [0, 0], expected=[0.0, 0.0]),
            case([1, 1], [0, 0], expected=[0.0, 0.0]),
            case([], [], expected=[0.0, 0.0]),
            case([1, 1, 1, 1], [1, 1, 1, 0], expected=[0.75, 1.0]),
        ],
        guided="""def precision_recall(preds, labels):
    # Replace every ___ with real code, then run the tests.

    tp = fp = fn = 0
    # Step 1: zip walks both lists side by side.
    for p, y in zip(preds, labels):
        if p == 1 and y == 1:
            tp += 1
        elif ___:
            fp += 1
        elif p == 0 and y == 1:
            fn += 1

    # Step 2: divide, but only when the bottom number isn't 0.
    precision = round(tp / (tp + fp), 2) if tp + fp else 0.0
    recall = ___
    return [precision, recall]
""",
        fills=['p == 1 and y == 0', 'round(tp / (tp + fn), 2) if tp + fn else 0.0'],
        concepts=[
            [
                'zip',
                'Walks two lists side by side.',
                """for p, y in zip([1, 0], [1, 1]):
    print(p, y)""",
            ],
            ['A one-line if', '`a if condition else b` picks one of two values.', 'x = 10 / n if n else 0.0'],
        ],
        byhand='Pairs: (1,1) true positive, (1,0) false positive, (0,0) nothing, (1,1) true positive, (0,1) false negative. So tp=2, fp=1, fn=1. Precision 2/3 = 0.67, recall 2/3 = 0.67.',
        why='One pass to count, then two divisions.',
        gotchas=[
            [
                'Pick the metric before training',
                "Missing fraud (low recall) and blocking good customers (low precision) cost different amounts. Decide which matters more first, or you'll pick whichever number looks best.",
            ],
            [
                'Averages across classes',
                'With more than two classes, macro-average treats every class equally and micro-average weights by size. They can tell very different stories.',
            ],
        ],
    ),
)

lesson(MODULE, 'best_threshold',
    title='From scores to decisions',
    learn=[
        'Most classifiers output a **score**, not a yes/no. You choose a **threshold**: above it means yes. Moving it trades precision against recall.',
        'You tune the threshold on the validation set, then check it once on the test set. The best threshold for accuracy is often not the one the business wants.',
    ],
    example=example('Same scores, different thresholds', """scores = [0.9, 0.65, 0.4]
# t = 0.5  -> [1, 1, 0]
# t = 0.7  -> [1, 0, 0]  fewer yes: higher precision, lower recall"""),
    check=question(
        'You raise the threshold from 0.5 to 0.9. What usually happens?',
        ['Precision goes up, recall goes down', 'Both go up', 'Recall goes up, precision goes down'],
        answer=0,
        why='Fewer things pass a stricter threshold, so the ones that do are more often right (precision up), but more true cases are missed (recall down).',
    ),
    angle=angle(
        pattern='Sort, then sweep',
        text='Trying every threshold against every example checks every pair, which gets slow on big data: 10,000 examples means 100 million checks. Sorting the examples by score first lets you move the threshold one example at a time and update the count as you go. The same sort-then-sweep idea solves Merge Intervals.',
        say='"Trying every pair is slow on big data. If I sort by score first, each step changes one prediction, so I update the accuracy as I go instead of recounting."',
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
        prompt="""A model gives each example a score between 0 and 1. You turn scores into decisions with a threshold: predict 1 when `score >= t`, otherwise 0.

Try every score in `scores` as the threshold `t`. Return `[t, accuracy]` for the threshold with the highest accuracy (share of decisions that match `labels`), with accuracy rounded to 2 places. If several thresholds tie, return the highest of them. There is at least one score.""",
        pattern='Try each candidate, keep the best so far. Sorting first lets you update the count in one sweep instead of recounting.',
        target='trying each score is fine here; the fast version sorts once and sweeps',
        realworld='Classifiers output scores, and someone has to choose where to cut. Teams tune the threshold on a validation set, never on the test set, and often for precision or recall rather than accuracy.',
        starter="""def best_threshold(scores, labels):
    # your code here
    pass
""",
        solution="""def best_threshold(scores, labels):
    best_t, best_acc = None, -1
    for t in scores:
        right = 0
        for s, y in zip(scores, labels):
            pred = 1 if s >= t else 0
            if pred == y:
                right += 1
        acc = right / len(scores)
        if acc > best_acc or (acc == best_acc and t > best_t):
            best_t, best_acc = t, acc
    return [best_t, round(best_acc, 2)]
""",
        cases=[
            case([0.9, 0.2, 0.65, 0.4], [1, 0, 1, 0], expected=[0.65, 1.0], sample=True),
            case([0.5], [1], expected=[0.5, 1.0]),
            case([0.3, 0.8, 0.6], [0, 0, 1], expected=[0.6, 0.67]),
            case([0.1, 0.9], [1, 0], expected=[0.1, 0.5]),
            case([0.7, 0.7, 0.2], [1, 0, 0], expected=[0.7, 0.67]),
        ],
        guided="""def best_threshold(scores, labels):
    # Replace every ___ with real code, then run the tests.

    best_t, best_acc = None, -1
    # Step 1: try every score as the threshold.
    for t in scores:
        right = 0
        for s, y in zip(scores, labels):
            # Step 2: the decision for this example at threshold t.
            pred = ___
            if pred == y:
                right += 1
        acc = right / len(scores)
        # Step 3: better accuracy wins; on a tie, the higher threshold wins.
        if acc > best_acc or ___:
            best_t, best_acc = t, acc
    return [best_t, round(best_acc, 2)]
""",
        fills=['1 if s >= t else 0', '(acc == best_acc and t > best_t)'],
        concepts=[
            [
                'Nested loops',
                "A loop inside a loop runs the inner one completely for every outer item. With n scores that's n × n steps.",
                """for t in scores:
    for s in scores:
        ...""",
            ],
            [
                'Keeping the best so far',
                'Start with a value anything beats, and replace it when you find better.',
                """best = -1
for x in [3, 7, 5]:
    if x > best:
        best = x""",
            ],
        ],
        byhand='Threshold 0.65: 0.9 → 1 (right), 0.2 → 0 (right), 0.65 → 1 (right), 0.4 → 0 (right). 4 of 4. No threshold beats 1.0, so the answer is [0.65, 1.0].',
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
