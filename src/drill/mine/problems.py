"""Practice problems about your own money and health.

Every problem here takes the same shapes your finance tracker stores
(``~/Developer/finance``): transactions in integer cents with negative meaning
money out, a category -> kind map so transfers are not counted as spending,
weights in kg, meal-log dates, and logged lifts.

Each problem is used two ways:

* ``drill mine check`` runs it on your **real** data, read-only, on this Mac
  (see :mod:`drill.mine.data`). Nothing leaves the machine.
* The browser practice page gets the same problems with **made-up** look-alike
  data (see :mod:`drill.mine.fake`), because real rows must never be published.

The test cases below are small hand-written edge cases. The real-data check adds
one more case on top: your actual data, with the expected answer worked out by
the reference solution.
"""

from __future__ import annotations

from drill.problems.model import Problem, TestCase


def _t(date: str, merchant: str, cents: int, category: str | None) -> dict:
    return {"date": date, "merchant": merchant, "amount_cents": cents, "category": category}


KINDS = {
    "Coffee": "expense", "Groceries": "expense", "Gas": "expense", "Dining": "expense",
    "Shopping": "expense", "Subscriptions": "expense", "Housing": "expense",
    "Phone & Internet": "expense", "Transportation": "expense", "Health & Fitness": "expense",
    "Income": "income", "Transfers": "transfer", "Credit Card Payment": "transfer",
}

_SEPT = [
    _t("2026-09-01", "Tim Hortons", -245, "Coffee"),
    _t("2026-09-02", "Loblaws", -8312, "Groceries"),
    _t("2026-09-03", "Tim Hortons", -310, "Coffee"),
]


MINE_PROBLEMS: tuple[Problem, ...] = (
    Problem(
        id="spending_by_category",
        title="Spending by Category",
        topic="spending",
        difficulty="easy",
        prompt=(
            "Your function gets two things:\n\n"
            "- `transactions`: a list of your transactions. Each one is a dict like "
            "`{\"date\": \"2026-09-01\", \"merchant\": \"Tim Hortons\", \"amount_cents\": -245, "
            "\"category\": \"Coffee\"}`. Amounts are in cents. A negative amount means money "
            "went out.\n"
            "- `kinds`: what kind each category is, like `{\"Coffee\": \"expense\", "
            "\"Transfers\": \"transfer\"}`. A transfer, like paying your credit card, just "
            "moves money between your own accounts, so it isn't spending.\n\n"
            "Add up the money that went out in each category whose kind is `\"expense\"`. "
            "Skip money coming in, like refunds.\n\n"
            "Return a dict of each category to the dollars you spent there, as a positive "
            "number, like `{\"Coffee\": 5.55}`. Add up in cents and divide by 100 at the end. "
            "Leave out categories with nothing spent."
        ),
        function_name="spending_by_category",
        starter_code="def spending_by_category(transactions, kinds):\n    # your code here\n    pass\n",
        reference_solution=(
            "def spending_by_category(transactions, kinds):\n"
            "    cents = {}\n"
            "    for t in transactions:\n"
            "        cat = t[\"category\"]\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(cat) == \"expense\":\n"
            "            cents[cat] = cents.get(cat, 0) - t[\"amount_cents\"]\n"
            "    dollars = {}\n"
            "    for cat in cents:\n"
            "        dollars[cat] = cents[cat] / 100\n"
            "    return dollars\n"
        ),
        target_complexity="one pass over the transactions",
        pattern=(
            "Keep a running total for each category in a dict. Skip what doesn't count "
            "first, and turn cents into dollars last."
        ),
        test_cases=(
            TestCase(
                args=([_t("2026-09-01", "Tim Hortons", -245, "Coffee"),
                       _t("2026-09-02", "RBC Visa payment", -50000, "Credit Card Payment"),
                       _t("2026-09-03", "Tim Hortons", -310, "Coffee"),
                       _t("2026-09-04", "Loblaws", -8312, "Groceries")],
                      {"Coffee": "expense", "Groceries": "expense",
                       "Credit Card Payment": "transfer"}),
                expected={"Coffee": 5.55, "Groceries": 83.12}, is_sample=True,
            ),
            TestCase(
                args=([_t("2026-09-05", "RBC Visa payment", -50000, "Credit Card Payment"),
                       _t("2026-09-06", "Shell", -6000, "Gas")], KINDS),
                expected={"Gas": 60.0},
            ),
            TestCase(
                args=([_t("2026-09-07", "Amazon", -4999, "Shopping"),
                       _t("2026-09-20", "Amazon", 4999, "Shopping")], KINDS),
                expected={"Shopping": 49.99},
            ),
            TestCase(args=([_t("2026-09-15", "Payroll", 250000, "Income")], KINDS), expected={}),
            TestCase(args=([], KINDS), expected={}),
            TestCase(
                args=([_t("2026-09-08", "Tim Hortons", -10, "Coffee"),
                       _t("2026-09-09", "Tim Hortons", -20, "Coffee")], KINDS),
                expected={"Coffee": 0.3},
            ),
        ),
    ),
    Problem(
        id="top_merchants",
        title="Where Your Money Goes",
        topic="spending",
        difficulty="easy",
        prompt=(
            "Your function gets three things:\n\n"
            "- `transactions`: a list of your transactions. Each one is a dict like "
            "`{\"date\": \"2026-09-01\", \"merchant\": \"Amazon\", \"amount_cents\": -4000, "
            "\"category\": \"Shopping\"}`. Amounts are in cents. A negative amount means money "
            "went out.\n"
            "- `kinds`: what kind each category is, like `{\"Shopping\": \"expense\", "
            "\"Transfers\": \"transfer\"}`.\n"
            "- `how_many`: how many merchants to return, like `2`.\n\n"
            "Add up how much you spent at each merchant. Count only money going out, in "
            "categories whose kind is `\"expense\"`.\n\n"
            "Return a list of the names of the `how_many` merchants you spent the most at, biggest "
            "first. If two have the same total, put them in alphabetical order. If there are "
            "fewer merchants than `how_many`, return them all."
        ),
        function_name="top_merchants",
        starter_code="def top_merchants(transactions, kinds, how_many):\n    # your code here\n    pass\n",
        reference_solution=(
            "def top_merchants(transactions, kinds, how_many):\n"
            "    spent = {}\n"
            "    for t in transactions:\n"
            "        cat = t[\"category\"]\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(cat) == \"expense\":\n"
            "            name = t[\"merchant\"]\n"
            "            spent[name] = spent.get(name, 0) - t[\"amount_cents\"]\n"
            "    ranked = sorted(spent, key=lambda name: (-spent[name], name))\n"
            "    return ranked[:how_many]\n"
        ),
        target_complexity="one pass to add up, then one sort of the merchants",
        pattern="Total into a dict, then sort with a key that says exactly what 'most' means, ties included.",
        test_cases=(
            TestCase(
                args=([_t("2026-09-01", "Amazon", -4000, "Shopping"),
                       _t("2026-09-02", "Loblaws", -8312, "Groceries"),
                       _t("2026-09-03", "Amazon", -3000, "Shopping"),
                       _t("2026-09-04", "Shell", -6000, "Gas")],
                      {"Shopping": "expense", "Groceries": "expense", "Gas": "expense"}, 2),
                expected=["Loblaws", "Amazon"], is_sample=True,
            ),
            TestCase(args=([_t("2026-09-01", "Pizza Pizza", -1500, "Dining"),
                            _t("2026-09-02", "Amazon", -1500, "Shopping"),
                            _t("2026-09-03", "Tim Hortons", -500, "Coffee")], KINDS, 2),
                     expected=["Amazon", "Pizza Pizza"]),
            TestCase(args=([_t("2026-09-01", "RBC Visa payment", -90000, "Credit Card Payment"),
                            _t("2026-09-02", "Tim Hortons", -245, "Coffee")], KINDS, 1),
                     expected=["Tim Hortons"]),
            TestCase(args=(_SEPT, KINDS, 10), expected=["Loblaws", "Tim Hortons"]),
            TestCase(args=([_t("2026-09-01", "Amazon", -5000, "Shopping"),
                            _t("2026-09-05", "Amazon", 4000, "Shopping"),
                            _t("2026-09-06", "Shell", -3000, "Gas")], KINDS, 1),
                     expected=["Amazon"]),
            TestCase(args=([], KINDS, 3), expected=[]),
        ),
    ),
    Problem(
        id="subscriptions",
        title="Find Your Subscriptions",
        topic="patterns",
        difficulty="medium",
        prompt=(
            "You get `transactions`, a list of your transactions. Each one is a dict like "
            "`{\"date\": \"2026-09-03\", \"merchant\": \"Netflix\", \"amount_cents\": -1699, "
            "\"category\": \"Subscriptions\"}`. Amounts are in cents. A negative amount means "
            "money went out.\n\n"
            "A merchant looks like a subscription if it took money out:\n\n"
            "- in at least 3 different months, and\n"
            "- for exactly the same amount every time.\n\n"
            "Return the names of those merchants, in alphabetical order. The month is the first "
            "7 characters of the date, like `\"2026-09\"`. Two charges in the same month count "
            "as one month. Skip money coming in, like refunds."
        ),
        function_name="subscriptions",
        starter_code="def subscriptions(transactions):\n    # your code here\n    pass\n",
        reference_solution=(
            "def subscriptions(transactions):\n"
            "    months = {}\n"
            "    amounts = {}\n"
            "    for t in transactions:\n"
            "        if t[\"amount_cents\"] >= 0:\n"
            "            continue\n"
            "        name = t[\"merchant\"]\n"
            "        if name not in months:\n"
            "            months[name] = set()\n"
            "            amounts[name] = set()\n"
            "        months[name].add(t[\"date\"][:7])\n"
            "        amounts[name].add(t[\"amount_cents\"])\n"
            "    found = []\n"
            "    for name in months:\n"
            "        if len(months[name]) >= 3 and len(amounts[name]) == 1:\n"
            "            found.append(name)\n"
            "    return sorted(found)\n"
        ),
        target_complexity="one pass to collect, then one check per merchant",
        pattern=(
            "Collect a set for each merchant (which months, which amounts), then check the "
            "rule for each merchant."
        ),
        test_cases=(
            TestCase(
                args=([_t("2026-07-03", "Netflix", -1699, "Subscriptions"),
                       _t("2026-08-03", "Netflix", -1699, "Subscriptions"),
                       _t("2026-08-09", "Tim Hortons", -245, "Coffee"),
                       _t("2026-09-03", "Netflix", -1699, "Subscriptions"),
                       _t("2026-09-11", "Tim Hortons", -310, "Coffee")],),
                expected=["Netflix"], is_sample=True,
            ),
            TestCase(args=([_t("2026-08-03", "Spotify", -1199, "Subscriptions"),
                            _t("2026-09-03", "Spotify", -1199, "Subscriptions")],), expected=[]),
            TestCase(args=([_t("2026-09-01", "Uber", -900, "Transportation"),
                            _t("2026-09-08", "Uber", -900, "Transportation"),
                            _t("2026-09-15", "Uber", -900, "Transportation")],), expected=[]),
            TestCase(args=([_t("2026-07-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-08-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-09-03", "Netflix", -1899, "Subscriptions")],), expected=[]),
            TestCase(args=([_t("2026-07-01", "Rogers", -8500, "Phone & Internet"),
                            _t("2026-07-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-08-01", "Rogers", -8500, "Phone & Internet"),
                            _t("2026-08-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-08-20", "Netflix", 1699, "Subscriptions"),
                            _t("2026-09-01", "Rogers", -8500, "Phone & Internet"),
                            _t("2026-09-03", "Netflix", -1699, "Subscriptions")],),
                     expected=["Netflix", "Rogers"]),
            TestCase(args=([],), expected=[]),
        ),
    ),
    Problem(
        id="unusual_charges",
        title="Spot Unusual Charges",
        topic="patterns",
        difficulty="medium",
        prompt=(
            "You get `transactions`, a list of your transactions in date order. Each one is a "
            "dict like `{\"date\": \"2026-09-03\", \"merchant\": \"Tim Hortons\", "
            "\"amount_cents\": -1890, \"category\": \"Coffee\"}`. Amounts are in cents. A "
            "negative amount means money went out.\n\n"
            "A charge is unusual when it's more than double the biggest earlier charge at the "
            "same merchant. Return the positions of the unusual charges, first to last. A "
            "position is a transaction's place in the list, counting from 0.\n\n"
            "- Skip money coming in: never flag it, and don't count it as an earlier charge.\n"
            "- A merchant's first charge is never unusual, because there's nothing to compare "
            "it with.\n"
            "- Exactly double is not unusual."
        ),
        function_name="unusual_charges",
        starter_code="def unusual_charges(transactions):\n    # your code here\n    pass\n",
        reference_solution=(
            "def unusual_charges(transactions):\n"
            "    biggest = {}\n"
            "    flagged = []\n"
            "    for position, t in enumerate(transactions):\n"
            "        if t[\"amount_cents\"] >= 0:\n"
            "            continue\n"
            "        spent = -t[\"amount_cents\"]\n"
            "        name = t[\"merchant\"]\n"
            "        if name in biggest and spent > 2 * biggest[name]:\n"
            "            flagged.append(position)\n"
            "        biggest[name] = max(biggest.get(name, 0), spent)\n"
            "    return flagged\n"
        ),
        target_complexity="one pass over the transactions",
        pattern=(
            "Remember the biggest so far for each merchant. Compare each new charge with it "
            "before you update it."
        ),
        test_cases=(
            TestCase(args=([_t("2026-09-01", "Tim Hortons", -245, "Coffee"),
                            _t("2026-09-02", "Tim Hortons", -310, "Coffee"),
                            _t("2026-09-03", "Tim Hortons", -1890, "Coffee")],),
                     expected=[2], is_sample=True),
            TestCase(args=([_t("2026-09-01", "Amazon", -2000, "Shopping"),
                            _t("2026-09-05", "Amazon", -9000, "Shopping"),
                            _t("2026-09-09", "Amazon", -15000, "Shopping")],), expected=[1]),
            TestCase(args=([_t("2026-09-01", "Shell", -3000, "Gas"),
                            _t("2026-09-08", "Shell", -6000, "Gas")],), expected=[]),
            TestCase(args=([_t("2026-09-01", "Apple", -129900, "Shopping")],), expected=[]),
            TestCase(args=([_t("2026-09-01", "Payroll", 250000, "Income"),
                            _t("2026-09-15", "Payroll", 900000, "Income")],), expected=[]),
            TestCase(args=([_t("2026-09-01", "Uber", -1000, "Transportation"),
                            _t("2026-09-02", "Uber", 5000, "Transportation"),
                            _t("2026-09-03", "Uber", -2500, "Transportation")],), expected=[2]),
            TestCase(args=([],), expected=[]),
        ),
    ),
    Problem(
        id="monthly_summary",
        title="Summarize a Month for the AI",
        topic="context",
        difficulty="medium",
        prompt=(
            "Your function gets three things:\n\n"
            "- `transactions`: a month of your transactions. Each one is a dict like "
            "`{\"date\": \"2026-09-03\", \"merchant\": \"Shell\", \"amount_cents\": -6050, "
            "\"category\": \"Gas\"}`. Amounts are in cents. A negative amount means money "
            "went out.\n"
            "- `kinds`: what kind each category is, like `{\"Gas\": \"expense\", "
            "\"Transfers\": \"transfer\"}`.\n"
            "- `max_lines`: the most lines the summary can have, like `3`.\n\n"
            "Total the money going out in each `\"expense\"` category. Return a list of "
            "`[category, dollars]` lines, biggest first, like "
            "`[[\"Groceries\", 83.12], [\"Gas\", 60.5]]`. If two categories have the same "
            "total, put them in A to Z order.\n\n"
            "If there are more categories than `max_lines`, keep only the biggest "
            "`max_lines - 1` (2 when `max_lines` is 3), then add one last line, "
            "`[\"Everything else\", dollars]`, for all the others.\n\n"
            "Add up in cents (the last line too) and divide by 100 at the end."
        ),
        function_name="monthly_summary",
        starter_code="def monthly_summary(transactions, kinds, max_lines):\n    # your code here\n    pass\n",
        reference_solution=(
            "def monthly_summary(transactions, kinds, max_lines):\n"
            "    cents = {}\n"
            "    for t in transactions:\n"
            "        cat = t[\"category\"]\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(cat) == \"expense\":\n"
            "            cents[cat] = cents.get(cat, 0) - t[\"amount_cents\"]\n"
            "    ranked = sorted(cents, key=lambda cat: (-cents[cat], cat))\n"
            "    if len(ranked) <= max_lines:\n"
            "        top = ranked\n"
            "        rest = []\n"
            "    else:\n"
            "        top = ranked[:max_lines - 1]\n"
            "        rest = ranked[max_lines - 1:]\n"
            "    lines = []\n"
            "    for cat in top:\n"
            "        lines.append([cat, cents[cat] / 100])\n"
            "    if len(rest) > 0:\n"
            "        rest_cents = 0\n"
            "        for cat in rest:\n"
            "            rest_cents += cents[cat]\n"
            "        lines.append([\"Everything else\", rest_cents / 100])\n"
            "    return lines\n"
        ),
        target_complexity="one pass to add up, one sort, then keep the top few",
        pattern="Rank, keep the top few, and roll the rest into one line so nothing is silently dropped.",
        test_cases=(
            TestCase(
                args=([_t("2026-09-01", "Loblaws", -8312, "Groceries"),
                       _t("2026-09-02", "Tim Hortons", -555, "Coffee"),
                       _t("2026-09-03", "Shell", -6050, "Gas"),
                       _t("2026-09-04", "Pizza Pizza", -1500, "Dining")],
                      {"Coffee": "expense", "Groceries": "expense", "Gas": "expense",
                       "Dining": "expense"}, 3),
                expected=[["Groceries", 83.12], ["Gas", 60.5], ["Everything else", 20.55]],
                is_sample=True,
            ),
            TestCase(args=(_SEPT + [_t("2026-09-04", "Shell", -6050, "Gas")], KINDS, 5),
                     expected=[["Groceries", 83.12], ["Gas", 60.5], ["Coffee", 5.55]]),
            TestCase(args=(_SEPT + [_t("2026-09-04", "Shell", -6050, "Gas")], KINDS, 3),
                     expected=[["Groceries", 83.12], ["Gas", 60.5], ["Coffee", 5.55]]),
            TestCase(args=(_SEPT + [_t("2026-09-04", "Shell", -6050, "Gas"),
                                    _t("2026-09-05", "Pizza Pizza", -1500, "Dining"),
                                    _t("2026-09-06", "RBC Visa payment", -50000,
                                       "Credit Card Payment")], KINDS, 2),
                     expected=[["Groceries", 83.12], ["Everything else", 81.05]]),
            TestCase(args=([_t("2026-09-01", "RBC Visa payment", -50000, "Credit Card Payment")], KINDS, 4),
                     expected=[]),
            TestCase(args=([_t("2026-09-01", "Rent", -180000, "Housing")], KINDS, 2),
                     expected=[["Housing", 1800.0]]),
            TestCase(args=([_t("2026-09-01", "Loblaws", -8312, "Groceries"),
                            _t("2026-09-02", "Tim Hortons", -10, "Coffee"),
                            _t("2026-09-03", "Pizza Pizza", -20, "Dining")], KINDS, 2),
                     expected=[["Groceries", 83.12], ["Everything else", 0.3]]),
        ),
    ),
    Problem(
        id="logging_streak",
        title="Longest Meal-Logging Streak",
        topic="health",
        difficulty="medium",
        prompt=(
            "You get `days`, a list of the days you logged food, as day numbers, like "
            "`[1, 2, 3, 5, 6]`. "
            "Days are plain counting numbers, so day 4 is the day after day 3. The numbers "
            "can be in any order, and the same "
            "day can appear more than once.\n\n"
            "A streak is a run of days in a row, like 1, 2, 3. Return the length of your "
            "longest streak. If `days` is empty, return 0."
        ),
        function_name="logging_streak",
        starter_code="def logging_streak(days):\n    # your code here\n    pass\n",
        reference_solution=(
            "def logging_streak(days):\n"
            "    logged = set(days)\n"
            "    best = 0\n"
            "    for day in logged:\n"
            "        if day - 1 not in logged:\n"
            "            length = 1\n"
            "            while day + length in logged:\n"
            "                length += 1\n"
            "            best = max(best, length)\n"
            "    return best\n"
        ),
        target_complexity="a set, and count each streak once, from its first day",
        pattern="Put the days in a set, then only start counting from days that begin a streak.",
        test_cases=(
            TestCase(args=([1, 2, 3, 5, 6],), expected=3, is_sample=True),
            TestCase(args=([],), expected=0),
            TestCase(args=([42],), expected=1),
            TestCase(args=([10, 9, 8, 1, 2],), expected=3),
            TestCase(args=([3, 3, 4, 4, 5],), expected=3),
            TestCase(args=([5, 7, 9],), expected=1),
        ),
    ),
    Problem(
        id="monthly_low_weight",
        title="Lowest Weight Each Month",
        topic="health",
        difficulty="easy",
        prompt=(
            "You get `weigh_ins`, a list of your weigh-ins. Each one is a `[date, kg]` pair, "
            "like `[\"2026-09-15\", 79.2]`.\n\n"
            "Return a dict of each month to your lowest weight that month, in kg, like "
            "`{\"2026-09\": 79.2}`. The month is the first 7 characters of the date."
        ),
        function_name="monthly_low_weight",
        starter_code="def monthly_low_weight(weigh_ins):\n    # your code here\n    pass\n",
        reference_solution=(
            "def monthly_low_weight(weigh_ins):\n"
            "    lowest = {}\n"
            "    for date, kg in weigh_ins:\n"
            "        month = date[:7]\n"
            "        if month not in lowest or kg < lowest[month]:\n"
            "            lowest[month] = kg\n"
            "    return lowest\n"
        ),
        target_complexity="one pass over the weigh-ins",
        pattern="Keep the lowest so far for each month in one dict.",
        test_cases=(
            TestCase(args=([["2026-09-01", 80.4], ["2026-09-15", 79.2], ["2026-09-28", 79.6],
                            ["2026-10-02", 79.5]],),
                     expected={"2026-09": 79.2, "2026-10": 79.5}, is_sample=True),
            TestCase(args=([],), expected={}),
            TestCase(args=([["2026-08-31", 81.0]],), expected={"2026-08": 81.0}),
            TestCase(args=([["2026-09-03", 80.0], ["2026-09-03", 79.0], ["2026-09-04", 80.5]],),
                     expected={"2026-09": 79.0}),
            TestCase(args=([["2026-12-30", 78.1], ["2027-01-02", 78.4], ["2027-01-20", 77.9]],),
                     expected={"2026-12": 78.1, "2027-01": 77.9}),
        ),
    ),
    Problem(
        id="personal_bests",
        title="Your Personal Bests",
        topic="health",
        difficulty="easy",
        prompt=(
            "You get `lifts`, a list of the entries from your workout log. Each entry is "
            "`[date, exercise, kg]`, like `[\"2026-09-02\", \"Bench Press\", 57.5]`.\n\n"
            "Return a dict of each exercise to the heaviest weight you lifted for it, in kg, "
            "like `{\"Bench Press\": 62.5}`. Leave out entries with a weight of 0, like push "
            "ups, which use your body weight."
        ),
        function_name="personal_bests",
        starter_code="def personal_bests(lifts):\n    # your code here\n    pass\n",
        reference_solution=(
            "def personal_bests(lifts):\n"
            "    best = {}\n"
            "    for date, exercise, kg in lifts:\n"
            "        if kg > 0 and kg > best.get(exercise, 0):\n"
            "            best[exercise] = kg\n"
            "    return best\n"
        ),
        target_complexity="one pass over your log",
        pattern="One pass, one dict, keep the biggest for each exercise.",
        test_cases=(
            TestCase(args=([["2026-09-02", "Bench Press", 57.5], ["2026-09-05", "Squat", 82.5],
                            ["2026-09-09", "Bench Press", 62.5], ["2026-09-12", "Bench Press", 57.5]],),
                     expected={"Bench Press": 62.5, "Squat": 82.5}, is_sample=True),
            TestCase(args=([],), expected={}),
            TestCase(args=([["2026-09-02", "Push Up", 0.0], ["2026-09-03", "Deadlift", 100.0]],),
                     expected={"Deadlift": 100.0}),
            TestCase(args=([["2026-09-02", "Squat", 90.0], ["2026-09-09", "Squat", 85.0]],),
                     expected={"Squat": 90.0}),
        ),
    ),
)

_BY_ID = {p.id: p for p in MINE_PROBLEMS}


def get_mine_problem(problem_id: str) -> Problem:
    try:
        return _BY_ID[problem_id]
    except KeyError:
        raise KeyError(
            f"No problem with id {problem_id!r}. Available: {', '.join(_BY_ID)}"
        ) from None


# Where each problem shows up in your own tracker. The page doesn't show this for
# practice problems; it goes to the AI tutor as context when you ask for a hint.
REAL_WORLD = {
    "spending_by_category": "This is the number behind your tracker's spending chart. Its SQL follows the same two rules: money out only, and transfers like credit card payments don't count, or they'd be counted twice.",
    "top_merchants": "The \"where does my money go\" question you'd ask Claude from your phone. Total first, rank second.",
    "subscriptions": "Forgotten subscriptions are the classic money leak. Your tracker's monitor looks for patterns like this after each import.",
    "unusual_charges": "This is a simple version of what your tracker's monitor does before it sends a phone alert: compare a new charge with what's normal for that merchant.",
    "monthly_summary": "Context engineering: your weekly check-in sends data to a model. A few ranked lines, with the small stuff rolled into one, give the model what matters without wasting tokens (the small chunks of text a model reads and charges for).",
    "logging_streak": "Streaks are what keep habits going. Your meal log has gaps, so this finds the longest run without one.",
    "monthly_low_weight": "Daily weight jumps around with water and food. Looking at one number per month, like the lowest, is a simple first way to see the trend.",
    "personal_bests": "Your workout log has thousands of sets. One pass with a dict turns them into the numbers you actually care about.",
}
