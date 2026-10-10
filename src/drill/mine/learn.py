"""Beginner lessons for the money & health problems, shown on the practice page.

Same shape as the page's other lessons: building-block concepts (name, plain
explanation, tiny example), a worked example to do by hand, why the approach is
quick enough, real-world gotchas, and a guided starter with ___ blanks.
"""

LEARN = {
    "spending_by_category": {
        "concepts": [
            ["Reading a dict", "Each transaction is a dict. Square brackets get a value by its name.", "t = {'merchant': 'Shell', 'amount_cents': -6000}\nt['amount_cents']   # -6000"],
            ["dict.get with a default", "get returns a fallback instead of crashing when the key isn't there. Handy for running totals.", "totals = {}\ntotals['Gas'] = totals.get('Gas', 0) + 6000"],
            ["Work in cents, convert at the end", "Whole numbers add up exactly. Decimals don't always: 0.1 + 0.2 gives 0.30000000000000004.", "cents = 10 + 20\nround(cents / 100, 2)   # 0.3"],
        ],
        "byhand": "Tim Hortons -245 (Coffee), Loblaws -8312 (Groceries), Tim Hortons -310 (Coffee). All three are money out in expense categories. Coffee: 245 + 310 = 555 cents, which is $5.55. Groceries: 8312 cents, which is $83.12.",
        "why": "Each transaction is looked at once and added to one running total.",
        "gotchas": [
            ["Counting the credit card payment", "Paying your Visa moves money between your own accounts. The spending already showed up as the Visa charges, so counting the payment too doubles it. That's why your tracker marks it as a transfer."],
            ["Mixing up the sign", "Money out is negative. Adding the raw amounts gives a negative total, and refunds (positive) quietly cancel out spending."],
            ["Adding dollars as decimals", "Sum whole cents and convert once at the end, like your tracker does with amount_cents."],
        ],
        "guided": "def spending_by_category(txns, kinds):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: running totals in cents, one per category.\n    cents = {}\n\n    for t in txns:\n        # Step 2: only money out (negative), only expense categories.\n        if t[\"amount_cents\"] < ___ and kinds.get(t[\"category\"]) == ___:\n            cat = t[\"category\"]\n            # Step 3: add the amount as a positive number.\n            cents[cat] = cents.get(cat, 0) - ___\n\n    # Step 4: convert cents to dollars, rounded to 2 places.\n    return {cat: round(c / ___, 2) for cat, c in cents.items()}\n",
    },
    "top_merchants": {
        "concepts": [
            ["sorted with a key", "key tells sorted what to compare. Here, each merchant's total.", "spent = {'A': 50, 'B': 90}\nsorted(spent, key=lambda m: spent[m])   # ['A', 'B']"],
            ["Biggest first, ties A to Z", "Sort by a pair: the negative total (so bigger comes first), then the name.", "sorted(spent, key=lambda m: (-spent[m], m))"],
            ["Slicing the top", "[:k] keeps at most k items, and is fine when the list is shorter.", "['a', 'b'][:5]   # ['a', 'b']"],
        ],
        "byhand": "Totals: Loblaws 8312, Shell 6000, Tim Hortons 245 + 310 = 555. Biggest first: Loblaws, Shell, Tim Hortons. With k = 2 the answer is Loblaws and Shell.",
        "why": "One pass to total, then a sort of the merchants, which is a much shorter list than the transactions.",
        "gotchas": [
            ["Same merchant, different names", "Bank exports write merchants inconsistently, like \"TIM HORTONS #1234\" and \"Tim Hortons\". Real apps clean the names first, or the totals get split."],
            ["Ties in random order", "Without a tie rule, two runs can give different answers, which makes tests and charts flicker."],
        ],
        "guided": "def top_merchants(txns, kinds, k):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: total spent per merchant, in cents (money out, expense only).\n    spent = {}\n    for t in txns:\n        if t[\"amount_cents\"] < 0 and kinds.get(t[\"category\"]) == \"expense\":\n            m = t[\"merchant\"]\n            spent[m] = spent.get(m, 0) - ___\n\n    # Step 2: biggest total first; ties in alphabetical order.\n    ranked = sorted(spent, key=lambda m: (___, m))\n\n    # Step 3: keep the first k.\n    return ranked[:___]\n",
    },
    "subscriptions": {
        "concepts": [
            ["set", "A collection with no repeats. Adding the same month twice still leaves one.", "months = set()\nmonths.add('2026-09')\nmonths.add('2026-09')\nlen(months)   # 1"],
            ["setdefault", "Gets the value for a key, creating it first if it's missing. Good for dicts of sets.", "seen = {}\nseen.setdefault('Netflix', set()).add('2026-09')"],
            ["The month from a date", "The first 7 characters of \"2026-09-14\" are \"2026-09\".", "'2026-09-14'[:7]   # '2026-09'"],
        ],
        "byhand": "Netflix: charged in July, August and September, always 1699. That's 3 months and 1 amount, so it's a subscription at $16.99. Tim Hortons: 3 months, but the amounts were 245 and 310, so no.",
        "why": "One pass to collect months and amounts per merchant, then one quick check per merchant.",
        "gotchas": [
            ["Prices change", "Real subscriptions go up in price now and then. An exact-match rule misses them, so real tools allow a small difference."],
            ["Annual plans", "A yearly charge never shows up 3 months in a row. Looking for the same amount about 12 months apart catches those."],
        ],
        "guided": "def subscriptions(txns):\n    # Replace every ___ with real code, then run the tests.\n\n    months = {}    # merchant -> set of months charged\n    amounts = {}   # merchant -> set of amounts charged\n    for t in txns:\n        # Step 1: skip money coming in.\n        if t[\"amount_cents\"] >= ___:\n            continue\n        m = t[\"merchant\"]\n        # Step 2: remember the month and the amount.\n        months.setdefault(m, set()).add(t[\"date\"][:___])\n        amounts.setdefault(m, set()).add(t[\"amount_cents\"])\n\n    found = {}\n    for m in months:\n        # Step 3: at least 3 months, and only one amount ever.\n        if len(months[m]) >= ___ and len(amounts[m]) == ___:\n            only = list(amounts[m])[0]\n            found[m] = round(-only / 100, 2)\n    return found\n",
    },
    "unusual_charges": {
        "concepts": [
            ["enumerate", "Gives each item's position along with the item.", "for i, t in enumerate(['a', 'b']):\n    print(i, t)   # 0 a, then 1 b"],
            ["Best so far", "Keep a dict of the biggest value seen per key, and update it after each item.", "biggest = {}\nbiggest['Shell'] = max(biggest.get('Shell', 0), 6000)"],
            ["Check, then update", "Compare the new charge with the old biggest before you update it, or it would compare against itself.", "if spent > 2 * biggest[m]:\n    ...\nbiggest[m] = max(...)"],
        ],
        "byhand": "Tim Hortons 245: first one, nothing to compare, so biggest is 245. Then 310: double 245 is 490, and 310 isn't more, so biggest becomes 310. Then 1890: double 310 is 620, and 1890 is more, so flag position 2.",
        "why": "One pass, with one dict lookup per transaction.",
        "gotchas": [
            ["Too many alerts", "A simple rule like this flags a $6 coffee after a $2.45 one. Real monitors look at more history, and your tracker asks a model to decide what's worth a phone notification."],
            ["Alerting twice", "Re-importing the same file shouldn't send the same alert again. Your tracker keeps a dedupe key for each alert for this reason."],
        ],
        "guided": "def unusual_charges(txns):\n    # Replace every ___ with real code, then run the tests.\n\n    biggest = {}   # merchant -> biggest charge so far, in cents\n    flagged = []\n    for i, t in enumerate(txns):\n        # Step 1: only money going out.\n        if t[\"amount_cents\"] >= 0:\n            continue\n        spent = -t[\"amount_cents\"]\n        m = t[\"merchant\"]\n        # Step 2: seen this merchant before, and more than double its biggest?\n        if m in biggest and spent > ___ * biggest[m]:\n            flagged.append(___)\n        # Step 3: update the biggest AFTER checking.\n        biggest[m] = max(biggest.get(m, 0), ___)\n    return flagged\n",
    },
    "monthly_summary": {
        "concepts": [
            ["f-strings with 2 decimals", ":.2f inside the braces always shows 2 decimal places.", "x = 60\nf\"Gas: ${x:.2f}\"   # 'Gas: $60.00'"],
            ["Slicing a ranked list", "ranked[:n] is the top n, and ranked[n:] is everything after.", "ranked = ['a', 'b', 'c', 'd']\nranked[:2], ranked[2:]   # ['a', 'b'], ['c', 'd']"],
            ["sum of a generator", "Adds up values as you loop, in one line.", "sum(cents[c] for c in ['a', 'b'])"],
        ],
        "byhand": "Totals: Groceries $83.12, Gas $60.00, Dining $15.00, Coffee $5.55. With max_lines 3, keep the top 2 and roll the other two into one line: 15.00 + 5.55 = $20.55. That gives 3 lines.",
        "why": "One pass to total, a sort of the categories, then a few lines of text.",
        "gotchas": [
            ["Dropping the tail silently", "If you only keep the top lines, the model never knows the rest exist and the total looks wrong. Rolling them into one line keeps the total honest."],
            ["Raw data in prompts", "Sending every transaction costs more and buries what matters. Summarize first. This is the core of context engineering: give the model the least it needs."],
            ["Private data in prompts", "Summaries also send less personal detail to the model provider, which is a good habit with financial data."],
        ],
        "guided": "def monthly_summary(txns, kinds, max_lines):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: total per expense category in cents (same as Spending by Category).\n    cents = {}\n    for t in txns:\n        if t[\"amount_cents\"] < 0 and kinds.get(t[\"category\"]) == \"expense\":\n            cat = t[\"category\"]\n            cents[cat] = cents.get(cat, 0) - t[\"amount_cents\"]\n\n    # Step 2: biggest first, ties A to Z.\n    ranked = sorted(cents, key=lambda c: (-cents[c], c))\n\n    # Step 3: everything fits? One line each.\n    if len(ranked) <= max_lines:\n        return [f\"{c}: ${cents[c] / 100:.2f}\" for c in ranked]\n\n    # Step 4: keep the top max_lines - 1, roll the rest into one line.\n    lines = [f\"{c}: ${cents[c] / 100:.2f}\" for c in ranked[:___]]\n    rest = sum(cents[c] for c in ranked[___:])\n    lines.append(f\"Everything else: ${rest / 100:___}\")\n    return lines\n",
    },
    "logging_streak": {
        "concepts": [
            ["Fast membership with a set", "x in my_set is instant. x in my_list checks every item.", "logged = set([1, 2, 3])\n2 in logged   # True, instantly"],
            ["Find where a streak starts", "A day starts a streak if the day before it isn't logged.", "if d - 1 not in logged:\n    # d starts a streak"],
            ["Count forward with while", "Keep going while the next day is there.", "length = 1\nwhile d + length in logged:\n    length += 1"],
        ],
        "byhand": "Days 1, 2, 3, 5, 6. Day 1 starts a streak (day 0 is missing): 1, 2, 3 gives 3. Day 2 doesn't start one, because day 1 is there, so skip it. Day 5 starts one: 5, 6 gives 2. The longest is 3.",
        "why": "Each day is counted at most twice: once when checking if it starts a streak, and once while counting a streak.",
        "gotchas": [
            ["Time zones", "A meal logged at 11:30 pm while travelling can land on the next day. Decide which time zone counts before computing streaks."],
            ["Sorting is fine too", "Sorting the days and walking through once also works. It's a little slower but often easier to get right."],
        ],
        "guided": "def logging_streak(days):\n    # Replace every ___ with real code, then run the tests.\n\n    # Step 1: a set removes repeats and makes lookups instant.\n    logged = set(___)\n    best = 0\n    for d in logged:\n        # Step 2: only start counting at the first day of a streak.\n        if d - 1 not in ___:\n            length = 1\n            # Step 3: count forward while the next day is logged.\n            while d + length in logged:\n                length += ___\n            best = max(best, length)\n    return best\n",
    },
    "monthly_low_weight": {
        "concepts": [
            ["Unpacking pairs", "Each weigh-in is [date, kg], so you can name both parts in the loop.", "for date, kg in [['2026-09-01', 80.0]]:\n    print(date, kg)"],
            ["Lowest so far per month", "Same idea as a running total, but keep the smaller value.", "if month not in lowest or kg < lowest[month]:\n    lowest[month] = kg"],
            ["Converting units", "Divide kg by 0.45359237 to get pounds.", "round(80 / 0.45359237, 1)   # 176.4"],
        ],
        "byhand": "September has 80.0 and 79.2, and the lower is 79.2. That's 79.2 / 0.45359237 = 174.6 lb. October only has 79.5, which is 175.3 lb.",
        "why": "One pass through the weigh-ins, then a quick conversion per month.",
        "gotchas": [
            ["Mixing units", "Your tracker stores kg and you think in lb. Comparing a kg number with a lb number is a silent bug. Pick one unit inside the code and convert only for display."],
            ["Rounding too early", "Round at the end. Rounding each value first can change which one is lowest."],
        ],
        "guided": "def monthly_low_weight(weigh_ins):\n    # Replace every ___ with real code, then run the tests.\n\n    lowest = {}   # month -> lowest kg\n    for date, kg in weigh_ins:\n        # Step 1: the month is the first 7 characters of the date.\n        month = date[:___]\n        # Step 2: keep the smaller weight.\n        if month not in lowest or kg < lowest[___]:\n            lowest[month] = kg\n\n    # Step 3: convert to pounds at the end, rounded to 1 place.\n    return {m: round(kg / ___, 1) for m, kg in lowest.items()}\n",
    },
    "personal_bests": {
        "concepts": [
            ["Unpacking three values", "Each entry is [date, exercise, kg].", "for date, exercise, kg in [['2026-09-02', 'Squat', 80.0]]:\n    print(exercise, kg)"],
            ["Max per key", "Keep the biggest value seen for each exercise.", "best = {}\nif kg > best.get('Squat', 0):\n    best['Squat'] = kg"],
        ],
        "byhand": "Bench Press: 60.0, then 62.5 (new best), then 60.0 (not a best). Squat: 80.0. Answer: Bench Press 62.5, Squat 80.0.",
        "why": "One pass through your log, however many sets it has.",
        "gotchas": [
            ["Same exercise, different names", "\"Bench Press\" and \"Barbell Bench Press\" may be the same lift. Real apps keep a list of name aliases."],
            ["Heaviest isn't always best", "Lifting 100 kg once and 90 kg for 8 reps are hard to compare. That's why your workout log also stores an estimated one-rep max."],
        ],
        "guided": "def personal_bests(lifts):\n    # Replace every ___ with real code, then run the tests.\n\n    best = {}\n    for date, exercise, kg in lifts:\n        # Step 1: skip weight 0, and keep it only if it beats the best so far.\n        if kg > ___ and kg > best.get(exercise, 0):\n            best[___] = kg\n    return best\n",
    },
}
