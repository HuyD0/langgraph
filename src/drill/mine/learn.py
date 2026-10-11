"""Beginner lessons for the money & health problems, shown on the practice page.

Same shape as the page's other lessons: building-block concepts (name, plain
explanation, tiny example), a worked example to do by hand, why the approach is
quick enough, real-world gotchas, and a guided starter with ___ blanks.
"""

LEARN = {
    "spending_by_category": {
        "concepts": [
            ["Reading a dict", "Square brackets get a value by its name.", "song = {'title': 'Hey', 'plays': 12}\nsong['plays']   # 12"],
            ["dict.get", "`d.get(key)` gives `None` (Python's word for 'nothing') instead of crashing when the key isn't there. `d.get(key, 0)` gives 0 instead, which is handy for running totals.", "votes = {}\nvotes['yes'] = votes.get('yes', 0) + 1\nvotes   # {'yes': 1}"],
            ["Looping over a dict", "`for key in d:` goes through the dict's keys.", "ages = {'Al': 30, 'Bo': 25}\nfor name in ages:\n    print(name, ages[name])"],
            ["Cents first, dollars last", "Whole numbers add up exactly. Decimals don't always: `0.1 + 0.2` gives `0.30000000000000004`. So add up cents, then divide by 100 once at the end.", "cents = 10 + 20\ncents / 100   # 0.3"],
        ],
        "byhand": "Coffee and Groceries are expenses. Credit Card Payment is a transfer. Tim Hortons takes 245 cents out, for Coffee. Coffee's total is now 245. RBC Visa payment is in Credit Card Payment, which is a transfer, so skip it. Tim Hortons takes 310 more, for Coffee. Coffee is now 245 plus 310, which makes 555. Loblaws takes 8312 cents out, for Groceries. Groceries is now 8312. In dollars that's 5.55 and 83.12, so return `{\"Coffee\": 5.55, \"Groceries\": 83.12}`.",
        "why": "Each transaction is looked at once and added to one running total.",
        "gotchas": [
            ["Counting the credit card payment", "Paying your Visa moves money between your own accounts. The spending already showed up as the Visa charges, so counting the payment too doubles it. That's why your tracker marks it as a transfer."],
            ["Mixing up the sign", "Money out is negative. Adding the raw amounts gives a negative total, and refunds (positive) quietly cancel out spending."],
            ["Adding dollars as decimals", "Sum whole cents and convert once at the end, like your tracker does with amount_cents."],
        ],
        "guided": (
            "def spending_by_category(transactions, kinds):\n"
            "    # Replace every ___ with real code, then run the tests.\n"
            "\n"
            "    # Step 1: a running total in cents for each category.\n"
            "    cents = {}\n"
            "    for t in transactions:\n"
            "        cat = t[\"category\"]\n"
            "        # Step 2: only money out, only \"expense\" categories.\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(cat) == ___:\n"
            "            # Step 3: the amount is negative, so subtract it\n"
            "            # to add it as a positive number.\n"
            "            cents[cat] = cents.get(cat, 0) - ___\n"
            "\n"
            "    # Step 4: turn cents into dollars: divide by 100.\n"
            "    dollars = {}\n"
            "    for cat in cents:\n"
            "        dollars[cat] = cents[cat] / ___\n"
            "    return dollars\n"
        ),
    },
    "top_merchants": {
        "concepts": [
            ["dict.get for totals", "`d.get(key, 0)` gives 0 when the key isn't there yet, so a running total can start from nothing.", "votes = {}\nvotes['yes'] = votes.get('yes', 0) + 1"],
            ["sorted with a key", "`sorted(d)` on a dict sorts its keys. `key=` says what to compare. `lambda n: ages[n]` is a tiny function: give it a name, get back that person's age.", "ages = {'Al': 30, 'Bo': 25}\nsorted(ages, key=lambda n: ages[n])\n# ['Bo', 'Al']"],
            ["Biggest first, ties A to Z", "Sort by a pair. Python compares the first values, and only looks at the second ones when the first are equal. A minus sign puts bigger numbers first.", "scores = {'Bo': 7, 'Al': 7, 'Cy': 9}\nsorted(scores,\n       key=lambda n: (-scores[n], n))\n# ['Cy', 'Al', 'Bo']"],
            ["Taking the first few", "`items[:3]` keeps the first 3 items. It's fine when the list is shorter.", "['a', 'b'][:3]   # ['a', 'b']"],
        ],
        "byhand": "Everything here is money out in an expense category. Amazon: 4000 and 3000 make 7000 cents. Loblaws: 8312. Shell: 6000. Biggest first: Loblaws, Amazon, Shell. `how_many` is 2, so return the first 2: `[\"Loblaws\", \"Amazon\"]`.",
        "why": "One pass to total, then a sort of the merchants, which is a much shorter list than the transactions.",
        "gotchas": [
            ["Same merchant, different names", "Bank exports write merchants inconsistently, like \"TIM HORTONS #1234\" and \"Tim Hortons\". Real apps clean the names first, or the totals get split."],
            ["No tie rule", "Without a tie rule, tied merchants come out in whatever order they first showed up. Import the same rows in a different order, or read them from a database query with no tie rule, and the answer changes. That makes tests and charts flicker."],
        ],
        "guided": (
            "def top_merchants(transactions, kinds, how_many):\n"
            "    # Replace every ___ with real code, then run the tests.\n"
            "\n"
            "    # Step 1 (done for you): cents spent at each merchant.\n"
            "    spent = {}\n"
            "    for t in transactions:\n"
            "        cat = t[\"category\"]\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(cat) == \"expense\":\n"
            "            name = t[\"merchant\"]\n"
            "            spent[name] = spent.get(name, 0) - t[\"amount_cents\"]\n"
            "\n"
            "    # Step 2: sort the names, biggest total first.\n"
            "    # A minus sign puts big totals first.\n"
            "    # The name breaks ties, A to Z.\n"
            "    ranked = sorted(spent, key=lambda name: (___, name))\n"
            "\n"
            "    # Step 3: keep the first how_many names.\n"
            "    return ranked[:___]\n"
        ),
    },
    "subscriptions": {
        "concepts": [
            ["set", "A collection with no repeats. Adding something that's already there changes nothing, so `len` counts the different values.", "seen = set(['red', 'blue'])\nseen.add('red')\nlen(seen)   # still 2"],
            ["A set for each merchant", "The first time you meet a key, give it an empty set. After that, add to its set.", "if 'Al' not in hobbies:\n    hobbies['Al'] = set()\nhobbies['Al'].add('chess')"],
            ["The first few characters", "`text[:4]` is the first 4 characters of a string.", "'2026-09-14'[:4]   # '2026'"],
            ["continue", "Inside a loop, `continue` skips the rest of the loop for this item and moves on to the next one.", "for n in [4, -1, 7]:\n    if n < 0:\n        continue   # -1 goes no further"],
        ],
        "byhand": "Netflix charged in 2026-07, 2026-08 and 2026-09: 3 months. It was 1699 cents every time: 1 amount. So Netflix is a subscription. Tim Hortons charged in only 2 months, 2026-08 and 2026-09, and its amounts were 245 and 310: 2 amounts. So it isn't. Return `[\"Netflix\"]`.",
        "why": "One pass to collect months and amounts for each merchant, then one quick check per merchant.",
        "gotchas": [
            ["Prices change", "Real subscriptions go up in price now and then. An exact-match rule misses them, so real tools allow a small difference."],
            ["Annual plans", "A yearly charge shows up only once a year, so this rule finds it only at its third charge, two years after the first. Looking for the same amount about 12 months apart catches it much sooner."],
            ["Rent and transfers", "Rent and transfers also repeat for the same amount every month, so this rule finds them too. A real tool would skip categories that aren't subscriptions."],
        ],
        "guided": (
            "def subscriptions(transactions):\n"
            "    # Replace every ___ with real code, then run the tests.\n"
            "\n"
            "    months = {}    # each merchant's set of months\n"
            "    amounts = {}   # each merchant's set of amounts\n"
            "    for t in transactions:\n"
            "        if t[\"amount_cents\"] >= 0:\n"
            "            continue   # money coming in: skip it\n"
            "        name = t[\"merchant\"]\n"
            "        if name not in months:\n"
            "            months[name] = set()\n"
            "            amounts[name] = set()\n"
            "        # Step 1: add this charge's month and its amount.\n"
            "        months[name].add(t[\"date\"][:___])\n"
            "        amounts[name].add(___)\n"
            "\n"
            "    # Step 2: 3 or more months, and only 1 amount.\n"
            "    found = []\n"
            "    for name in months:\n"
            "        if len(months[name]) >= 3 and len(amounts[name]) == ___:\n"
            "            found.append(name)   # add name to the end of found\n"
            "\n"
            "    # Step 3: sorted() puts the names in A to Z order.\n"
            "    return sorted(found)\n"
        ),
    },
    "unusual_charges": {
        "concepts": [
            ["enumerate", "Gives each item's position along with the item, counting from 0.", "fruits = ['fig', 'kiwi']\nfor i, fruit in enumerate(fruits):\n    print(i, fruit)\n# 0 fig, then 1 kiwi"],
            ["continue", "Inside a loop, `continue` skips the rest of the loop for this item and moves on to the next one.", "for n in [4, -1, 7]:\n    if n < 0:\n        continue   # -1 goes no further"],
            ["Biggest so far", "`max(a, b)` gives the bigger of two numbers. With `d.get(key, 0)`, a key you haven't seen yet starts at 0.", "best = {}\nbest['Al'] = max(best.get('Al', 0), 12)\nbest   # {'Al': 12}"],
            ["Check first, then update", "Compare with the old biggest before you update it. Otherwise a big charge is compared with itself and never looks unusual. Checking `name in best` first means a name you haven't seen yet is skipped instead of crashing.", "if name in best and score > 2 * best[name]:\n    print('big jump')\nbest[name] = max(best.get(name, 0), score)"],
        ],
        "byhand": "Position 0: Tim Hortons, 245 cents. It's the first Tim Hortons charge, so it's not unusual. Biggest so far: 245. Position 1: 310. Double 245 is 490, and 310 is not more. Biggest so far: 310. Position 2: 1890. Double 310 is 620, and 1890 is more, so it's unusual. Return `[2]`.",
        "why": "One pass, with one dict lookup per transaction.",
        "gotchas": [
            ["Too many alerts", "A simple rule like this flags a $6 coffee after a $2.45 one. Real monitors look at more history, and your tracker asks a model to decide what's worth a phone notification."],
            ["Alerting twice", "Re-importing the same file shouldn't send the same alert again. Your tracker gives each alert a dedupe key (a label that marks it as already sent) for this reason."],
        ],
        "guided": (
            "def unusual_charges(transactions):\n"
            "    # Replace every ___ with real code, then run the tests.\n"
            "\n"
            "    biggest = {}   # each merchant's biggest charge so far\n"
            "    flagged = []\n"
            "    for position, t in enumerate(transactions):\n"
            "        if t[\"amount_cents\"] >= 0:\n"
            "            continue   # money coming in: skip it\n"
            "        spent = -t[\"amount_cents\"]   # as a positive number\n"
            "        name = t[\"merchant\"]\n"
            "        # Step 1: seen this merchant before, and is this\n"
            "        # charge more than double its biggest?\n"
            "        if name in biggest and spent > ___:\n"
            "            # If so, add its position to flagged.\n"
            "            flagged.append(___)\n"
            "        # Step 2: update the biggest AFTER checking.\n"
            "        biggest[name] = max(biggest.get(name, 0), ___)\n"
            "    return flagged\n"
        ),
    },
    "monthly_summary": {
        "concepts": [
            ["sorted, biggest first, ties A to Z", "`sorted(d)` on a dict sorts its keys. `key=` says what to compare. Sorting by a pair, like `(-d[k], k)`, puts the biggest values first (that's what the minus sign does), and the name breaks ties, A to Z.", "ages = {'Al': 30, 'Bo': 41, 'Cy': 41}\nsorted(ages,\n       key=lambda n: (-ages[n], n))\n# ['Bo', 'Cy', 'Al']"],
            ["Slicing a list", "`items[:2]` is the first 2 items. `items[2:]` is everything after them.", "items = ['a', 'b', 'c', 'd']\nitems[:2]   # ['a', 'b']\nitems[2:]   # ['c', 'd']"],
            ["Cents first, dollars last", "Add up whole cents, then divide by 100 once at the end. Adding decimals can give tiny errors: `0.1 + 0.2` gives `0.30000000000000004`. `total += 555` is short for `total = total + 555`.", "total = 1500\ntotal += 555   # now 2055\ntotal / 100    # 20.55"],
            ["A list of pairs", "Each line is a small list of two things. `append` adds one to the end of a list.", "people = []\npeople.append(['Al', 30])\npeople   # [['Al', 30]]"],
        ],
        "byhand": "Totals in cents: Groceries 8312, Coffee 555, Gas 6050, Dining 1500. Biggest first: Groceries, Gas, Dining, Coffee. That's 4 categories, more than `max_lines` (3). So keep the biggest 2. That's one less than `max_lines`, to leave room for the last line. In dollars they are Groceries 83.12 and Gas 60.5. Add up the rest in cents: Dining 1500 plus Coffee 555 makes 2055. That's 20.55 dollars. Return `[[\"Groceries\", 83.12], [\"Gas\", 60.5], [\"Everything else\", 20.55]]`.",
        "why": "One pass to total, a sort of the categories, then a few lines.",
        "gotchas": [
            ["Dropping the rest silently", "If you only keep the top lines, the model never knows the rest exist and the total looks wrong. Rolling them into one line keeps the total honest."],
            ["Raw data in prompts", "Sending every transaction costs more and buries what matters. Summarize first. This is the core of context engineering: give the model the least it needs."],
            ["Private data in prompts", "Summaries also send less personal detail to the model provider, which is a good habit with financial data."],
        ],
        "guided": (
            "def monthly_summary(transactions, kinds, max_lines):\n"
            "    # Replace every ___ with real code, then run the tests.\n"
            "\n"
            "    # Step 1 (done for you): cents per expense category.\n"
            "    cents = {}\n"
            "    for t in transactions:\n"
            "        cat = t[\"category\"]\n"
            "        if t[\"amount_cents\"] < 0 and kinds.get(cat) == \"expense\":\n"
            "            cents[cat] = cents.get(cat, 0) - t[\"amount_cents\"]\n"
            "\n"
            "    # Step 2 (done for you): categories, biggest first.\n"
            "    # The name breaks ties, A to Z.\n"
            "    ranked = sorted(cents, key=lambda cat: (-cents[cat], cat))\n"
            "\n"
            "    # Step 3: if they all fit, keep them all. If not, keep\n"
            "    # the top max_lines - 1, and the rest get rolled up.\n"
            "    if len(ranked) <= max_lines:\n"
            "        top = ranked\n"
            "        rest = []\n"
            "    else:\n"
            "        top = ranked[:___]\n"
            "        rest = ranked[___:]\n"
            "\n"
            "    lines = []\n"
            "    for cat in top:\n"
            "        lines.append([cat, cents[cat] / 100])\n"
            "\n"
            "    # Step 4: add up the rest in cents, then one last line.\n"
            "    if len(rest) > 0:\n"
            "        rest_cents = 0\n"
            "        for cat in rest:\n"
            "            rest_cents += ___\n"
            "        lines.append([\"Everything else\", rest_cents / 100])\n"
            "    return lines\n"
        ),
    },
    "logging_streak": {
        "concepts": [
            ["Sets: no repeats, instant lookups", "`set(...)` drops repeats. `x in some_set` answers instantly, while `x in some_list` checks every item. `not in` is the opposite.", "seen = set(['a', 'b', 'a'])\n# seen is {'a', 'b'}\n'b' in seen       # True\n'z' not in seen   # True"],
            ["while loops", "A while loop repeats as long as its condition is True. `n += 1` is short for `n = n + 1`.", "n = 0\nwhile n < 3:\n    n += 1\nn   # 3"],
            ["max", "`max(a, b)` gives the bigger of two numbers.", "best = max(3, 8)   # 8"],
        ],
        "byhand": "The set holds 1, 2, 3, 5, 6. Day 1: day 0 isn't there, so a streak starts. Days 2 and 3 follow, so its length is 3. Days 2 and 3: the day before is there, so they don't start a streak. Skip them. Day 5: day 4 isn't there, so a streak starts. Day 6 follows, so its length is 2. Day 6: day 5 is there, so skip it. The longest streak is 3, so return 3.",
        "why": "Each day is counted at most twice: once when checking if it starts a streak, and once while counting a streak.",
        "gotchas": [
            ["Time zones", "A meal logged at 11:30 pm while travelling can land on the next day. Decide which time zone counts before computing streaks."],
            ["Sorting is fine too", "Sorting the days and walking through once also works. It's a little slower but often easier to get right."],
        ],
        "guided": (
            "def logging_streak(days):\n"
            "    # Replace every ___ with real code, then run the tests.\n"
            "\n"
            "    # A set drops repeats and makes lookups instant.\n"
            "    logged = set(days)\n"
            "    best = 0\n"
            "    for day in logged:\n"
            "        # Step 1: a streak starts here if the day\n"
            "        # before it is not logged.\n"
            "        if ___ not in logged:\n"
            "            length = 1\n"
            "            # Step 2: count on while the next day is logged.\n"
            "            # The next day is day + length.\n"
            "            while ___ in logged:\n"
            "                length += 1\n"
            "            best = max(best, length)\n"
            "    return best\n"
        ),
    },
    "monthly_low_weight": {
        "concepts": [
            ["Unpacking pairs", "When each item is a pair, you can name both parts in the `for` line.", "pairs = [['Al', 30], ['Bo', 25]]\nfor name, age in pairs:\n    print(name, age)"],
            ["The first few characters", "`text[:4]` is the first 4 characters of a string.", "'2026-09-14'[:4]   # '2026'"],
            ["Lowest so far, per key", "Store a value the first time you see its key. After that, replace it only when the new value is smaller. With `or`, either side being True is enough.", "if city not in low or temp < low[city]:\n    low[city] = temp"],
        ],
        "byhand": "2026-09-01, 80.4: the first weigh-in in 2026-09, so the lowest is 80.4. 2026-09-15, 79.2: lower, so the lowest is now 79.2. 2026-09-28, 79.6: not lower, so it stays 79.2. 2026-10-02, 79.5: the first in 2026-10, so its lowest is 79.5. Return `{\"2026-09\": 79.2, \"2026-10\": 79.5}`.",
        "why": "One pass through the weigh-ins, with one dict check each.",
        "gotchas": [
            ["Mixing units", "Your tracker stores kg and you think in lb. Comparing a kg number with a lb number is a silent bug. Keep one unit inside the code, and convert only when you show the result."],
            ["One odd reading", "A single low weigh-in after a long run or a hot day can be low mostly because of lost water. The monthly low is a simple view; an average over a week is steadier."],
        ],
        "guided": (
            "def monthly_low_weight(weigh_ins):\n"
            "    # Replace every ___ with real code, then run the tests.\n"
            "\n"
            "    lowest = {}   # each month's lowest kg so far\n"
            "    for date, kg in weigh_ins:\n"
            "        # Step 1: the month is the first 7 characters\n"
            "        # of the date.\n"
            "        month = ___\n"
            "        # Step 2: a new month, or lower than its lowest?\n"
            "        if month not in lowest or kg < ___:\n"
            "            lowest[month] = kg\n"
            "    return lowest\n"
        ),
    },
    "personal_bests": {
        "concepts": [
            ["Unpacking three values", "When each entry is a list of 3 things, you can name all 3 in the `for` line.", "rows = [['Al', 'Oslo', 30]]\nfor name, city, age in rows:\n    print(name, age)"],
            ["Biggest so far, per key", "`d.get(key, 0)` gives 0 for a key you haven't seen yet, so any real weight beats it.", "best = {}\nif 7 > best.get('Al', 0):\n    best['Al'] = 7"],
        ],
        "byhand": "Bench Press 57.5: the first Bench Press, so its best is 57.5. Squat 82.5: the first Squat, so its best is 82.5. Bench Press 62.5: heavier than 57.5, so its best is now 62.5. Bench Press 57.5: not heavier than 62.5, so no change. Return `{\"Bench Press\": 62.5, \"Squat\": 82.5}`.",
        "why": "One pass through your log, however many sets it has.",
        "gotchas": [
            ["Same exercise, different names", "\"Bench Press\" and \"Barbell Bench Press\" may be the same lift. Real apps keep a list of name aliases."],
            ["Heaviest isn't always best", "Lifting 100 kg once and 90 kg for 8 reps are hard to compare. That's why your workout log also stores an estimated one-rep max: the most you could lift once."],
        ],
        "guided": (
            "def personal_bests(lifts):\n"
            "    # Replace every ___ with real code, then run the tests.\n"
            "\n"
            "    best = {}   # each exercise's heaviest kg so far\n"
            "    for date, exercise, kg in lifts:\n"
            "        # Step 1: skip weight 0. Keep kg only if it beats\n"
            "        # the best so far. A new exercise counts as 0.\n"
            "        if kg > 0 and kg > ___:\n"
            "            best[exercise] = ___\n"
            "    return best\n"
        ),
    },
}

# What goes in each ___ of the guided starters, in order. With these filled in, a
# starter should pass every case. Kept out of LEARN so the page never gets them.
FILLS = {
    "spending_by_category": ['"expense"', 't["amount_cents"]', "100"],
    "top_merchants": ["-spent[name]", "how_many"],
    "subscriptions": ["7", 't["amount_cents"]', "1"],
    "unusual_charges": ["2 * biggest[name]", "position", "spent"],
    "monthly_summary": ["max_lines - 1", "max_lines - 1", "cents[cat]"],
    "logging_streak": ["day - 1", "day + length"],
    "monthly_low_weight": ["date[:7]", "lowest[month]"],
    "personal_bests": ["best.get(exercise, 0)", "kg"],
}
