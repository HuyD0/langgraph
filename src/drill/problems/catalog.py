"""The starting problem bank.

Nine problems, each chosen for a *different* transferable pattern rather than for
being a famous puzzle. Passing interviews is mostly about recognising which of a
dozen patterns a question is wearing as a disguise, so the bank is organised around
`Problem.pattern`, and the tutor picks your weakest pattern first.

Adding your own is deliberately easy: append a `Problem` to `ALL_PROBLEMS`.
`tests/test_catalog.py` then automatically checks that your reference solution
passes your own test cases, so a malformed problem fails the suite immediately.

The prompts are written for someone new to coding who reads on a phone: every input
is named with a tiny example, every rule the hidden cases check is stated, and the
sample case shows the main behaviour rather than an edge case.
"""

from __future__ import annotations

from drill.problems.model import Problem, TestCase

ALL_PROBLEMS: tuple[Problem, ...] = (
    Problem(
        id="two_sum",
        title="Two Sum",
        topic="hash-map",
        difficulty="easy",
        pattern=(
            "Remember what you've already seen. A dictionary lets you ask \"have I "
            'already seen the partner I need?" instantly, so you only walk through the '
            "list once."
        ),
        target_complexity="one pass over the list (a dict to remember numbers is fine)",
        prompt=(
            "Your function gets two things:\n\n"
            "- `numbers`: a list of numbers, like `[2, 7, 11, 15]`.\n"
            "- `target`: the total you want, like `9`.\n\n"
            "Exactly one pair of numbers in the list adds up to `target`. Return the "
            "positions of those two numbers as a list, smaller position first. Positions "
            "start at 0.\n\n"
            "Don't use the same position twice. Two different positions can hold the same "
            "number, though, like the two 3s in `[3, 3]`."
        ),
        function_name="two_sum",
        starter_code="def two_sum(numbers, target):\n    # your code here\n    pass\n",
        reference_solution=(
            "def two_sum(numbers, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(numbers):\n"
            "        need = target - n\n"
            "        if need in seen:\n"
            "            return [seen[need], i]\n"
            "        seen[n] = i\n"
            "    return []\n"
        ),
        test_cases=(
            TestCase(args=([2, 7, 11, 15], 9), expected=[0, 1], is_sample=True),
            TestCase(args=([3, 2, 4], 6), expected=[1, 2]),
            TestCase(args=([3, 3], 6), expected=[0, 1]),
            TestCase(args=([-1, -2, -3, -4, -5], -8), expected=[2, 4]),
            TestCase(args=([0, 4, 3, 0], 0), expected=[0, 3]),
        ),
        tags=("array", "dict"),
    ),
    Problem(
        id="valid_parentheses",
        title="Valid Parentheses",
        topic="stack",
        difficulty="easy",
        pattern=(
            "Use a stack, like a pile of plates. Put each opening bracket on top. When a "
            "closing bracket shows up, the plate on top must be its partner."
        ),
        target_complexity="one pass over the string",
        prompt=(
            "Your function gets one string, `brackets`, made only of the characters "
            '`( ) [ ] { }`, like `"{[]}"`.\n\n'
            "Return `True` if the brackets match up, or `False` if they don't. They match "
            "up when:\n\n"
            "- every opening bracket is closed by one of the same kind, like `(` by `)`.\n"
            "- the last bracket opened is the first to close, so `\"([])\"` matches but "
            '`"([)]"` doesn\'t.\n'
            "- nothing is left open at the end, and nothing closes that was never opened."
            "\n\n"
            "An empty string counts as `True`."
        ),
        function_name="is_valid",
        starter_code="def is_valid(brackets):\n    # your code here\n    pass\n",
        reference_solution=(
            "def is_valid(brackets):\n"
            "    pairs = {')': '(', ']': '[', '}': '{'}\n"
            "    stack = []\n"
            "    for bracket in brackets:\n"
            "        if bracket not in pairs:\n"
            "            stack.append(bracket)\n"
            "        elif not stack or stack[-1] != pairs[bracket]:\n"
            "            return False\n"
            "        else:\n"
            "            stack.pop()\n"
            "    return not stack\n"
        ),
        test_cases=(
            TestCase(args=("{[]}",), expected=True, is_sample=True),
            TestCase(args=("()",), expected=True),
            TestCase(args=("()[]{}",), expected=True),
            TestCase(args=("(]",), expected=False),
            TestCase(args=("([)]",), expected=False),
            TestCase(args=("",), expected=True),
            TestCase(args=("(",), expected=False),
            TestCase(args=("]",), expected=False),
        ),
        tags=("string", "stack"),
    ),
    Problem(
        id="binary_search",
        title="Binary Search",
        topic="binary-search",
        difficulty="easy",
        pattern=(
            "Halve the search area each step. Like finding a word in a paper dictionary: "
            "open the middle, decide which half it's in, ignore the other half, and repeat."
        ),
        target_complexity="halve the search area each step, instead of checking every item",
        prompt=(
            "Your function gets two things:\n\n"
            "- `numbers`: a list sorted from smallest to largest, like `[1, 3, 5, 7, 9]`. "
            "No number appears twice.\n"
            "- `target`: the number to find, like `7`.\n\n"
            "Return the position of `target` in the list. Positions start at 0. If "
            "`target` isn't in the list, return `-1`. An empty list gives `-1` too.\n\n"
            "Don't check every item one by one. Look at the middle item instead: because "
            "the list is sorted, it tells you which half `target` must be in, so you can "
            "ignore the other half."
        ),
        function_name="search",
        starter_code="def search(numbers, target):\n    # your code here\n    pass\n",
        reference_solution=(
            "def search(numbers, target):\n"
            "    low = 0\n"
            "    high = len(numbers) - 1\n"
            "    while low <= high:\n"
            "        mid = (low + high) // 2\n"
            "        if numbers[mid] == target:\n"
            "            return mid\n"
            "        elif numbers[mid] < target:\n"
            "            low = mid + 1\n"
            "        else:\n"
            "            high = mid - 1\n"
            "    return -1\n"
        ),
        test_cases=(
            TestCase(args=([1, 3, 5, 7, 9], 7), expected=3, is_sample=True),
            TestCase(args=([-1, 0, 3, 5, 9, 12], 9), expected=4),
            TestCase(args=([-1, 0, 3, 5, 9, 12], 2), expected=-1),
            TestCase(args=([5], 5), expected=0),
            TestCase(args=([], 1), expected=-1),
            TestCase(args=([1, 2], 2), expected=1),
            TestCase(args=(list(range(0, 10000, 2)), 9998), expected=4999),
        ),
        tags=("array", "search"),
    ),
    Problem(
        id="climbing_stairs",
        title="Climbing Stairs",
        topic="dynamic-programming",
        difficulty="easy",
        pattern=(
            "Build the answer from smaller answers. The ways to reach step 5 are the ways "
            "to reach step 4 plus the ways to reach step 3, so you only need to remember "
            "the last two counts."
        ),
        target_complexity="one pass up the stairs, remembering just two counts",
        prompt=(
            "Your function gets one number, `steps`: how many steps the staircase has, "
            "like `4`. It is always at least 1.\n\n"
            "Each move, you climb either 1 step or 2 steps. Count how many different "
            "orders of moves take you exactly to the top, and return that count. For 3 "
            "steps there are 3 orders: 1 then 1 then 1, 1 then 2, or 2 then 1.\n\n"
            "`steps` can be as big as 40, which has over 100 million orders, so don't "
            "list them one by one. Build the count up from the bottom step instead."
        ),
        function_name="climb_stairs",
        starter_code="def climb_stairs(steps):\n    # your code here\n    pass\n",
        reference_solution=(
            "def climb_stairs(steps):\n"
            "    if steps == 1:\n"
            "        return 1\n"
            "    ways_below = 1\n"
            "    ways_here = 2\n"
            "    for step in range(3, steps + 1):\n"
            "        new = ways_here + ways_below\n"
            "        ways_below = ways_here\n"
            "        ways_here = new\n"
            "    return ways_here\n"
        ),
        test_cases=(
            TestCase(args=(4,), expected=5, is_sample=True),
            TestCase(args=(2,), expected=2),
            TestCase(args=(3,), expected=3),
            TestCase(args=(1,), expected=1),
            TestCase(args=(5,), expected=8),
            TestCase(args=(10,), expected=89),
            TestCase(args=(40,), expected=165580141),
        ),
        tags=("dp", "fibonacci"),
    ),
    Problem(
        id="longest_unique_substring",
        title="Longest Substring Without Repeating Characters",
        topic="sliding-window",
        difficulty="medium",
        pattern=(
            "Slide a window along the string. Stretch it on the right. When a character "
            "repeats, shrink it from the left until the repeat is gone."
        ),
        target_complexity=(
            "one walk along the string. The inner while loop is fine: each character "
            "joins the window once and leaves it at most once"
        ),
        prompt=(
            'Your function gets one string, `text`, like `"pwwkew"`.\n\n'
            "A substring is a run of characters that sit next to each other in `text`. "
            "Find the longest substring in which no character appears twice, and return "
            "its length.\n\n"
            '- In `"abcabcbb"` the longest is `"abc"`, so return `3`.\n'
            '- No skipping: in `"pwwkew"`, `"wke"` counts, but `"pwke"` doesn\'t, because '
            "those characters aren't side by side.\n"
            "- An empty string gives `0`."
        ),
        function_name="length_of_longest_substring",
        starter_code=(
            "def length_of_longest_substring(text):\n    # your code here\n    pass\n"
        ),
        reference_solution=(
            "def length_of_longest_substring(text):\n"
            "    window = set()\n"
            "    start = 0\n"
            "    best = 0\n"
            "    for i, char in enumerate(text):\n"
            "        while char in window:\n"
            "            window.remove(text[start])\n"
            "            start += 1\n"
            "        window.add(char)\n"
            "        best = max(best, i - start + 1)\n"
            "    return best\n"
        ),
        test_cases=(
            TestCase(args=("pwwkew",), expected=3, is_sample=True),
            TestCase(args=("abcabcbb",), expected=3),
            TestCase(args=("bbbbb",), expected=1),
            TestCase(args=("",), expected=0),
            TestCase(args=("dvdf",), expected=3),
            TestCase(args=("tmmzuxt",), expected=5),
        ),
        tags=("string", "window"),
    ),
    Problem(
        id="max_subarray",
        title="Maximum Subarray",
        topic="dynamic-programming",
        difficulty="medium",
        pattern=(
            "Keep a running total as you walk the list. At each number, ask: am I better "
            "off adding this to my running total, or starting fresh from here?"
        ),
        target_complexity="one pass over the list, keeping just two totals",
        prompt=(
            "Your function gets one list, `numbers`, like `[3, -4, 2, -1, 4]`. It has at "
            "least one number, and numbers can be negative.\n\n"
            "A subarray is a run of numbers that sit next to each other in the list. Find "
            "the subarray with the biggest total, and return that total.\n\n"
            "A subarray has at least one number. So if every number is negative, the "
            "answer is the biggest single number, like `-1` for `[-3, -1, -2]`."
        ),
        function_name="max_sub_array",
        starter_code="def max_sub_array(numbers):\n    # your code here\n    pass\n",
        reference_solution=(
            "def max_sub_array(numbers):\n"
            "    best = numbers[0]\n"
            "    running = numbers[0]\n"
            "    for n in numbers[1:]:\n"
            "        running = max(running + n, n)\n"
            "        best = max(best, running)\n"
            "    return best\n"
        ),
        test_cases=(
            TestCase(args=([3, -4, 2, -1, 4],), expected=5, is_sample=True),
            TestCase(args=([-2, 1, -3, 4, -1, 2, 1, -5, 4],), expected=6),
            TestCase(args=([1],), expected=1),
            TestCase(args=([5, 4, -1, 7, 8],), expected=23),
            TestCase(args=([-1],), expected=-1),
            TestCase(args=([-3, -2, -5, -1],), expected=-1),
            TestCase(args=([0, 0, 0],), expected=0),
        ),
        tags=("array", "kadane"),
    ),
    Problem(
        id="merge_intervals",
        title="Merge Intervals",
        topic="sorting",
        difficulty="medium",
        pattern=(
            "Sort the intervals by where they start. Then walk through once: each one "
            "either joins the one before it or starts a new one."
        ),
        target_complexity="sort once, then one pass over the intervals",
        prompt=(
            "Your function gets one list, `intervals`, like `[[1, 3], [2, 6], [8, 10]]`. "
            "Each interval is a range of numbers written as `[start, end]`.\n\n"
            "Merge intervals that overlap into one interval that covers them both, so "
            "`[1, 3]` and `[2, 6]` become `[1, 6]`. Intervals that only touch, like "
            "`[1, 4]` and `[4, 5]`, merge too, into `[1, 5]`. Intervals that don't "
            "overlap stay as they are.\n\n"
            "Return the merged intervals in order of their start. The input can come in "
            "any order, and an empty list gives `[]`."
        ),
        function_name="merge",
        starter_code="def merge(intervals):\n    # your code here\n    pass\n",
        reference_solution=(
            "def merge(intervals):\n"
            "    merged = []\n"
            "    for start, end in sorted(intervals):\n"
            "        if merged and start <= merged[-1][1]:\n"
            "            merged[-1][1] = max(merged[-1][1], end)\n"
            "        else:\n"
            "            merged.append([start, end])\n"
            "    return merged\n"
        ),
        test_cases=(
            TestCase(
                args=([[1, 3], [2, 6], [8, 10], [15, 18]],),
                expected=[[1, 6], [8, 10], [15, 18]],
                is_sample=True,
            ),
            TestCase(args=([[1, 4], [4, 5]],), expected=[[1, 5]]),
            TestCase(args=([],), expected=[]),
            TestCase(args=([[1, 4], [0, 4]],), expected=[[0, 4]]),
            TestCase(args=([[1, 4], [2, 3]],), expected=[[1, 4]]),
            TestCase(args=([[5, 6], [1, 2]],), expected=[[1, 2], [5, 6]]),
        ),
        tags=("array", "intervals"),
    ),
    Problem(
        id="group_anagrams",
        title="Group Anagrams",
        topic="hash-map",
        difficulty="medium",
        pattern=(
            "Give every word a label that's identical for words with the same letters, such"
            " as its letters in alphabetical order. Then group words by label in a "
            "dictionary."
        ),
        target_complexity="one pass over the words",
        prompt=(
            'Your function gets one list, `words`, like `["eat", "tan", "tea"]`.\n\n'
            "Two words are anagrams when they have exactly the same letters in a different "
            'order, like `"eat"` and `"tea"`. Put words that are anagrams of each other '
            "in the same group. A word with no anagram gets a group of its own.\n\n"
            "Return a list of the groups, where each group is a list of words. The order "
            "of the groups, and of the words inside a group, doesn't matter. An empty "
            "list gives `[]`."
        ),
        function_name="group_anagrams",
        starter_code="def group_anagrams(words):\n    # your code here\n    pass\n",
        reference_solution=(
            "def group_anagrams(words):\n"
            "    groups = {}\n"
            "    for word in words:\n"
            "        label = ''.join(sorted(word))\n"
            "        if label not in groups:\n"
            "            groups[label] = []\n"
            "        groups[label].append(word)\n"
            "    return list(groups.values())\n"
        ),
        unordered=True,
        test_cases=(
            TestCase(
                args=(["eat", "tan", "tea", "nat", "bat"],),
                expected=[["eat", "tea"], ["tan", "nat"], ["bat"]],
                is_sample=True,
            ),
            TestCase(
                args=(["eat", "tea", "tan", "ate", "nat", "bat"],),
                expected=[["eat", "tea", "ate"], ["tan", "nat"], ["bat"]],
            ),
            TestCase(args=(["a"],), expected=[["a"]]),
            TestCase(args=([],), expected=[]),
            TestCase(args=(["abc", "cba", "xyz"],), expected=[["abc", "cba"], ["xyz"]]),
        ),
        tags=("string", "dict"),
    ),
    Problem(
        id="num_islands",
        title="Number of Islands",
        topic="graph",
        difficulty="medium",
        pattern=(
            "When you find land you haven't visited yet, that's a new island. Count it, "
            "then sink it: turn it and all the land joined to it into water, so you "
            "don't count it twice."
        ),
        target_complexity=(
            "look at each square only a few times. A loop over the rows with a loop over "
            "the columns inside is fine: together they visit each square once"
        ),
        prompt=(
            "Your function gets one thing, `grid`: a map written as a list of rows, like "
            '`[["1", "1"], ["0", "1"]]`. Each square is the text `"1"` (land) or `"0"` '
            "(water).\n\n"
            "An island is a patch of land squares joined up, down, left or right. Count "
            "the islands and return the count.\n\n"
            "Squares that only touch at a corner are not joined, so "
            '`[["1", "0"], ["0", "1"]]` has 2 islands, not 1. Everything outside the grid '
            "is water. An empty grid, `[]`, has 0 islands."
        ),
        function_name="num_islands",
        starter_code="def num_islands(grid):\n    # your code here\n    pass\n",
        reference_solution=(
            "def num_islands(grid):\n"
            "    if not grid:\n"
            "        return 0\n"
            "    height = len(grid)\n"
            "    width = len(grid[0])\n"
            "\n"
            "    def sink(row, col):\n"
            "        if row < 0 or row >= height:\n"
            "            return\n"
            "        if col < 0 or col >= width:\n"
            "            return\n"
            "        if grid[row][col] != '1':\n"
            "            return\n"
            "        grid[row][col] = '0'\n"
            "        sink(row + 1, col)\n"
            "        sink(row - 1, col)\n"
            "        sink(row, col + 1)\n"
            "        sink(row, col - 1)\n"
            "\n"
            "    count = 0\n"
            "    for row in range(height):\n"
            "        for col in range(width):\n"
            "            if grid[row][col] == '1':\n"
            "                count += 1\n"
            "                sink(row, col)\n"
            "    return count\n"
        ),
        test_cases=(
            TestCase(
                args=([["1", "1", "0"], ["1", "0", "0"], ["0", "0", "1"]],),
                expected=2,
                is_sample=True,
            ),
            TestCase(args=([["1"]],), expected=1),
            TestCase(args=([["0"]],), expected=0),
            TestCase(args=([],), expected=0),
            TestCase(
                args=([["1", "0", "1"], ["0", "1", "0"], ["1", "0", "1"]],),
                expected=5,
            ),
            TestCase(args=([["1", "1"], ["1", "1"]],), expected=1),
        ),
        tags=("grid", "dfs", "bfs"),
    ),
)

# Stable lookup table, built once at import. This is cheap, pure-Python work with
# no I/O, so it does not violate the "no side effects at import" rule.
_BY_ID: dict[str, Problem] = {p.id: p for p in ALL_PROBLEMS}

TOPICS: tuple[str, ...] = tuple(sorted({p.topic for p in ALL_PROBLEMS}))


def problem_ids() -> tuple[str, ...]:
    return tuple(p.id for p in ALL_PROBLEMS)


def get_problem(problem_id: str) -> Problem:
    """Look up one problem, with a message that lists the valid ids on a typo."""
    try:
        return _BY_ID[problem_id]
    except KeyError:
        raise KeyError(
            f"No problem with id {problem_id!r}. Available: {', '.join(problem_ids())}"
        ) from None


def list_problems(
    topic: str | None = None, difficulty: str | None = None
) -> tuple[Problem, ...]:
    """Filter the bank by topic and/or difficulty."""
    out = ALL_PROBLEMS
    if topic:
        out = tuple(p for p in out if p.topic == topic)
    if difficulty:
        out = tuple(p for p in out if p.difficulty == difficulty)
    return out
