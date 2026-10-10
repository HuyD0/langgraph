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
            "You get `txns`, a list of your transactions, and `kinds`, a dict saying what kind "
            "each category is: `\"expense\"`, `\"income\"` or `\"transfer\"`.\n\n"
            "Each transaction looks like `{\"date\": \"2026-09-14\", \"merchant\": \"Tim Hortons\", "
            "\"amount_cents\": -245, \"category\": \"Coffee\"}`. Amounts are in cents, and a "
            "negative amount means money went out.\n\n"
            "Return a dict of how much you spent in each category, in dollars rounded to 2 "
            "decimal places. Only count money going out, and only in categories whose kind is "
            "`\"expense\"`. Leave out categories with no spending."
        ),
        function_name="spending_by_category",
        starter_code="def spending_by_category(txns, kinds):\n    # your code here\n    pass\n",
        reference_solution=(
            "def spending_by_category(txns, kinds):\n"
            "    cents = {}\n"
            "    for t in txns:\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(t[\"category\"]) == \"expense\":\n"
            "            cat = t[\"category\"]\n"
            "            cents[cat] = cents.get(cat, 0) - t[\"amount_cents\"]\n"
            "    return {cat: round(c / 100, 2) for cat, c in cents.items()}\n"
        ),
        target_complexity="walk through the transactions once",
        pattern="Add up into a dict, keyed by the thing you're grouping by. Filter first, convert units last.",
        test_cases=(
            TestCase(args=(_SEPT, KINDS), expected={"Coffee": 5.55, "Groceries": 83.12}, is_sample=True),
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
                       _t("2026-09-09", "Tim Hortons", -20, "Coffee"),
                       _t("2026-09-10", "Mystery shop", -999, None)], KINDS),
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
            "Same `txns` and `kinds` as before, plus a number `k`. Return the names of the `k` "
            "merchants you spent the most at, biggest first.\n\n"
            "Count only money going out in `\"expense\"` categories. If two merchants have the "
            "same total, put them in alphabetical order. Return fewer than `k` if there aren't "
            "enough merchants."
        ),
        function_name="top_merchants",
        starter_code="def top_merchants(txns, kinds, k):\n    # your code here\n    pass\n",
        reference_solution=(
            "def top_merchants(txns, kinds, k):\n"
            "    spent = {}\n"
            "    for t in txns:\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(t[\"category\"]) == \"expense\":\n"
            "            m = t[\"merchant\"]\n"
            "            spent[m] = spent.get(m, 0) - t[\"amount_cents\"]\n"
            "    ranked = sorted(spent, key=lambda m: (-spent[m], m))\n"
            "    return ranked[:k]\n"
        ),
        target_complexity="add up once, then sort",
        pattern="Total into a dict, then sort with a key that says exactly what 'best' means, ties included.",
        test_cases=(
            TestCase(args=(_SEPT + [_t("2026-09-04", "Shell", -6000, "Gas")], KINDS, 2),
                     expected=["Loblaws", "Shell"], is_sample=True),
            TestCase(args=([_t("2026-09-01", "Pizza Pizza", -1500, "Dining"),
                            _t("2026-09-02", "Amazon", -1500, "Shopping"),
                            _t("2026-09-03", "Tim Hortons", -500, "Coffee")], KINDS, 2),
                     expected=["Amazon", "Pizza Pizza"]),
            TestCase(args=([_t("2026-09-01", "RBC Visa payment", -90000, "Credit Card Payment"),
                            _t("2026-09-02", "Tim Hortons", -245, "Coffee")], KINDS, 1),
                     expected=["Tim Hortons"]),
            TestCase(args=(_SEPT, KINDS, 10), expected=["Loblaws", "Tim Hortons"]),
            TestCase(args=([], KINDS, 3), expected=[]),
        ),
    ),
    Problem(
        id="subscriptions",
        title="Find Your Subscriptions",
        topic="patterns",
        difficulty="medium",
        prompt=(
            "Find the charges that repeat like a subscription. Given `txns`, return a dict of "
            "merchant to monthly price in dollars (2 decimal places) for every merchant that "
            "took money out in **at least 3 different months**, for **exactly the same amount** "
            "every time.\n\n"
            "Ignore money coming in, like refunds. Three charges in the same month count as one "
            "month. Months are the first 7 characters of the date, like `\"2026-09\"`."
        ),
        function_name="subscriptions",
        starter_code="def subscriptions(txns):\n    # your code here\n    pass\n",
        reference_solution=(
            "def subscriptions(txns):\n"
            "    months = {}\n"
            "    amounts = {}\n"
            "    for t in txns:\n"
            "        if t[\"amount_cents\"] >= 0:\n"
            "            continue\n"
            "        m = t[\"merchant\"]\n"
            "        months.setdefault(m, set()).add(t[\"date\"][:7])\n"
            "        amounts.setdefault(m, set()).add(t[\"amount_cents\"])\n"
            "    found = {}\n"
            "    for m in months:\n"
            "        if len(months[m]) >= 3 and len(amounts[m]) == 1:\n"
            "            only = list(amounts[m])[0]\n"
            "            found[m] = round(-only / 100, 2)\n"
            "    return found\n"
        ),
        target_complexity="walk through the transactions once, collecting as you go",
        pattern="Collect sets per key (which months, which amounts), then check a rule against each key.",
        test_cases=(
            TestCase(
                args=([_t("2026-07-03", "Netflix", -1699, "Subscriptions"),
                       _t("2026-07-04", "Tim Hortons", -245, "Coffee"),
                       _t("2026-08-03", "Netflix", -1699, "Subscriptions"),
                       _t("2026-08-09", "Tim Hortons", -310, "Coffee"),
                       _t("2026-09-03", "Netflix", -1699, "Subscriptions"),
                       _t("2026-09-11", "Tim Hortons", -245, "Coffee")],),
                expected={"Netflix": 16.99}, is_sample=True,
            ),
            TestCase(args=([_t("2026-08-03", "Spotify", -1199, "Subscriptions"),
                            _t("2026-09-03", "Spotify", -1199, "Subscriptions")],), expected={}),
            TestCase(args=([_t("2026-09-01", "Uber", -900, "Transportation"),
                            _t("2026-09-08", "Uber", -900, "Transportation"),
                            _t("2026-09-15", "Uber", -900, "Transportation")],), expected={}),
            TestCase(args=([_t("2026-07-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-08-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-09-03", "Netflix", -1899, "Subscriptions")],), expected={}),
            TestCase(args=([_t("2026-07-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-08-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-08-20", "Netflix", 1699, "Subscriptions"),
                            _t("2026-09-03", "Netflix", -1699, "Subscriptions"),
                            _t("2026-07-15", "Rogers", -8500, "Phone & Internet"),
                            _t("2026-08-15", "Rogers", -8500, "Phone & Internet"),
                            _t("2026-09-15", "Rogers", -8500, "Phone & Internet")],),
                     expected={"Netflix": 16.99, "Rogers": 85.0}),
            TestCase(args=([],), expected={}),
        ),
    ),
    Problem(
        id="unusual_charges",
        title="Spot Unusual Charges",
        topic="patterns",
        difficulty="medium",
        prompt=(
            "Your tracker warns you about odd charges. Given `txns` in date order, return the "
            "positions (0, 1, 2, ...) of charges that are **more than double** the biggest "
            "earlier charge at the same merchant.\n\n"
            "Only money going out counts, both for flagging and for \"biggest earlier charge\". "
            "A merchant's first charge is never flagged, because there's nothing to compare it "
            "with. Exactly double is not flagged."
        ),
        function_name="unusual_charges",
        starter_code="def unusual_charges(txns):\n    # your code here\n    pass\n",
        reference_solution=(
            "def unusual_charges(txns):\n"
            "    biggest = {}\n"
            "    flagged = []\n"
            "    for i, t in enumerate(txns):\n"
            "        if t[\"amount_cents\"] >= 0:\n"
            "            continue\n"
            "        spent = -t[\"amount_cents\"]\n"
            "        m = t[\"merchant\"]\n"
            "        if m in biggest and spent > 2 * biggest[m]:\n"
            "            flagged.append(i)\n"
            "        biggest[m] = max(biggest.get(m, 0), spent)\n"
            "    return flagged\n"
        ),
        target_complexity="walk through the transactions once",
        pattern="Remember the best-so-far per key, and compare each new item against it before updating.",
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
            "Your tracker's weekly check-in sends your spending to a model, and prompts should "
            "be short. Given `txns`, `kinds` and `max_lines`, return a list of lines like "
            "`\"Groceries: $83.12\"`, one per expense category, biggest first (ties in "
            "alphabetical order). Count money going out in `\"expense\"` categories only.\n\n"
            "If there are more categories than `max_lines`, keep the top `max_lines - 1` and add "
            "a last line `\"Everything else: $X.XX\"` with the rest added together. Always show "
            "2 decimal places, like `$60.00`."
        ),
        function_name="monthly_summary",
        starter_code="def monthly_summary(txns, kinds, max_lines):\n    # your code here\n    pass\n",
        reference_solution=(
            "def monthly_summary(txns, kinds, max_lines):\n"
            "    cents = {}\n"
            "    for t in txns:\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(t[\"category\"]) == \"expense\":\n"
            "            cat = t[\"category\"]\n"
            "            cents[cat] = cents.get(cat, 0) - t[\"amount_cents\"]\n"
            "    ranked = sorted(cents, key=lambda c: (-cents[c], c))\n"
            "    if len(ranked) <= max_lines:\n"
            "        return [f\"{c}: ${cents[c] / 100:.2f}\" for c in ranked]\n"
            "    lines = [f\"{c}: ${cents[c] / 100:.2f}\" for c in ranked[:max_lines - 1]]\n"
            "    rest = sum(cents[c] for c in ranked[max_lines - 1:])\n"
            "    lines.append(f\"Everything else: ${rest / 100:.2f}\")\n"
            "    return lines\n"
        ),
        target_complexity="add up once, sort, then keep the top few",
        pattern="Rank, keep the top, and roll the long tail into one line so nothing is silently dropped.",
        test_cases=(
            TestCase(args=(_SEPT + [_t("2026-09-04", "Shell", -6000, "Gas")], KINDS, 5),
                     expected=["Groceries: $83.12", "Gas: $60.00", "Coffee: $5.55"], is_sample=True),
            TestCase(args=(_SEPT + [_t("2026-09-04", "Shell", -6000, "Gas"),
                                    _t("2026-09-05", "Pizza Pizza", -1500, "Dining")], KINDS, 3),
                     expected=["Groceries: $83.12", "Gas: $60.00", "Everything else: $20.55"]),
            TestCase(args=(_SEPT + [_t("2026-09-04", "Shell", -6000, "Gas")], KINDS, 3),
                     expected=["Groceries: $83.12", "Gas: $60.00", "Coffee: $5.55"]),
            TestCase(args=([_t("2026-09-01", "RBC Visa payment", -50000, "Credit Card Payment")], KINDS, 4),
                     expected=[]),
            TestCase(args=([_t("2026-09-01", "Rent", -180000, "Housing")], KINDS, 2),
                     expected=["Housing: $1800.00"]),
        ),
    ),
    Problem(
        id="logging_streak",
        title="Longest Meal-Logging Streak",
        topic="health",
        difficulty="medium",
        prompt=(
            "You get `days`, the days you logged food, as day numbers: the day after day 100 "
            "is day 101. They're in no particular order and some may repeat.\n\n"
            "Return the length of your longest streak of days in a row. No days means 0."
        ),
        function_name="logging_streak",
        starter_code="def logging_streak(days):\n    # your code here\n    pass\n",
        reference_solution=(
            "def logging_streak(days):\n"
            "    logged = set(days)\n"
            "    best = 0\n"
            "    for d in logged:\n"
            "        if d - 1 not in logged:\n"
            "            length = 1\n"
            "            while d + length in logged:\n"
            "                length += 1\n"
            "            best = max(best, length)\n"
            "    return best\n"
        ),
        target_complexity="look at each day a fixed number of times",
        pattern="Put everything in a set, then only start counting from days that begin a streak.",
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
            "You get `weigh_ins`, a list of `[date, kg]` pairs like `[\"2026-09-15\", 79.2]`. "
            "Your tracker stores kilograms, but you think in pounds.\n\n"
            "Return a dict of month (like `\"2026-09\"`) to your lowest weight that month, in "
            "pounds, rounded to 1 decimal place. To turn kg into lb, divide by `0.45359237`."
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
            "    return {m: round(kg / 0.45359237, 1) for m, kg in lowest.items()}\n"
        ),
        target_complexity="walk through the weigh-ins once",
        pattern="Keep the best-so-far per group. Convert units once, at the very end.",
        test_cases=(
            TestCase(args=([["2026-09-01", 80.0], ["2026-09-15", 79.2], ["2026-10-02", 79.5]],),
                     expected={"2026-09": 174.6, "2026-10": 175.3}, is_sample=True),
            TestCase(args=([],), expected={}),
            TestCase(args=([["2026-08-31", 81.0]],), expected={"2026-08": 178.6}),
            TestCase(args=([["2026-09-03", 80.0], ["2026-09-03", 79.0], ["2026-09-04", 80.5]],),
                     expected={"2026-09": 174.2}),
        ),
    ),
    Problem(
        id="personal_bests",
        title="Your Personal Bests",
        topic="health",
        difficulty="easy",
        prompt=(
            "You get `lifts`, a list of `[date, exercise, weight_kg]` entries from your workout "
            "log, like `[\"2026-09-02\", \"Bench Press\", 60.0]`.\n\n"
            "Return a dict of each exercise to the heaviest weight you've lifted for it, in kg. "
            "Leave out entries with a weight of 0, like bodyweight exercises."
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
        target_complexity="walk through your log once",
        pattern="One pass, one dict, keep the max per key.",
        test_cases=(
            TestCase(args=([["2026-09-02", "Bench Press", 60.0], ["2026-09-05", "Squat", 80.0],
                            ["2026-09-09", "Bench Press", 62.5], ["2026-09-12", "Bench Press", 60.0]],),
                     expected={"Bench Press": 62.5, "Squat": 80.0}, is_sample=True),
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


# Where each problem shows up in your own tracker. Shown on the page's Learn tab.
REAL_WORLD = {
    "spending_by_category": "This is the number behind your tracker's spending chart. Its SQL follows the same two rules: money out only, and transfers like credit card payments don't count, or they'd be counted twice.",
    "top_merchants": "The \"where does my money go\" question you'd ask Claude from your phone. Total first, rank second.",
    "subscriptions": "Forgotten subscriptions are the classic money leak. Your tracker's monitor looks for patterns like this after each import.",
    "unusual_charges": "This is a simple version of what your tracker's monitor does before it sends a phone alert: compare a new charge with what's normal for that merchant.",
    "monthly_summary": "Context engineering: your weekly check-in sends data to a model. Short, ranked lines with the long tail rolled up give the model what matters without wasting tokens.",
    "logging_streak": "Streaks are what keep habits going. Your meal log has gaps, so this finds the longest run without one.",
    "monthly_low_weight": "Daily weight jumps around with water and food. The monthly low is a calmer way to see the trend, in the unit you actually think in.",
    "personal_bests": "Your workout log has thousands of sets. One pass with a dict turns them into the numbers you actually care about.",
}
