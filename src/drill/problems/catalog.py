"""The starting problem bank.

Nine problems, each chosen for a *different* transferable pattern rather than for
being a famous puzzle. Passing interviews is mostly about recognising which of a
dozen patterns a question is wearing as a disguise, so the bank is organised around
`Problem.pattern`, and the tutor picks your weakest pattern first.

Adding your own is deliberately easy: append a `Problem` to `ALL_PROBLEMS`.
`tests/test_catalog.py` then automatically checks that your reference solution
passes your own test cases, so a malformed problem fails the suite immediately.
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
            'Remember what you\'ve already seen. A dictionary lets you ask "have I already '
            'seen the number I need?" instantly, so you only walk through the list once.'
        ),
        target_complexity='walk through the list once. Using extra memory is fine',
        prompt=(
            'You get a list of numbers, `nums`, and a number, `target`. Find the two '
            'numbers in the list that add up to `target`, and return their positions in the'
            ' list. Positions start at 0.\n\n'
            "There is always exactly one right pair, and you can't use the same spot twice."
            ' Put the smaller position first.'
        ),
        function_name="two_sum",
        starter_code="def two_sum(nums, target):\n    # your code here\n    pass\n",
        reference_solution=(
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        if target - n in seen:\n"
            "            return [seen[target - n], i]\n"
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
            'Use a stack, like a pile of plates. Put each opening bracket on top. When a '
            'closing bracket shows up, the plate on top must be its partner.'
        ),
        target_complexity='walk through the string once',
        prompt=(
            'You get a string `s` made only of brackets: `( ) [ ] { }`. Return `True` if '
            'every bracket is closed by the same kind, in the right order. Otherwise return'
            ' `False`.\n\n'
            'An empty string counts as `True`.'
        ),
        function_name="is_valid",
        starter_code="def is_valid(s):\n    # your code here\n    pass\n",
        reference_solution=(
            "def is_valid(s):\n"
            "    pairs = {')': '(', ']': '[', '}': '{'}\n"
            "    stack = []\n"
            "    for ch in s:\n"
            "        if ch in pairs:\n"
            "            if not stack or stack.pop() != pairs[ch]:\n"
            "                return False\n"
            "        else:\n"
            "            stack.append(ch)\n"
            "    return not stack\n"
        ),
        test_cases=(
            TestCase(args=("()",), expected=True, is_sample=True),
            TestCase(args=("()[]{}",), expected=True),
            TestCase(args=("(]",), expected=False),
            TestCase(args=("([)]",), expected=False),
            TestCase(args=("{[]}",), expected=True),
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
            'Like finding a word in a paper dictionary: open the middle, decide which half '
            "it's in, ignore the other half, and repeat. Most mistakes happen at the very "
            'ends.'
        ),
        target_complexity="cut the part you're searching in half each step",
        prompt=(
            'You get a list `nums` that is already sorted from smallest to largest, and a '
            'number `target`. Return the position of `target` in the list, or `-1` if it '
            "isn't there.\n\n"
            "Don't check every item one by one. Use the fact that the list is sorted to "
            'skip most of it.'
        ),
        function_name="search",
        starter_code="def search(nums, target):\n    # your code here\n    pass\n",
        reference_solution=(
            "def search(nums, target):\n"
            "    lo, hi = 0, len(nums) - 1\n"
            "    while lo <= hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if nums[mid] == target:\n"
            "            return mid\n"
            "        if nums[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1\n"
        ),
        test_cases=(
            TestCase(args=([-1, 0, 3, 5, 9, 12], 9), expected=4, is_sample=True),
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
            'Build the answer from smaller answers. The ways to reach step 5 come from the '
            'ways to reach step 4 plus the ways to reach step 3. You only need to remember '
            'the last two.'
        ),
        target_complexity='go up the stairs once, remembering just two counts',
        prompt=(
            'A staircase has `n` steps. Each move, you climb either 1 step or 2 steps. How '
            'many different ways can you get to the top? Return that count.\n\n'
            '`n` is always at least 1.'
        ),
        function_name="climb_stairs",
        starter_code="def climb_stairs(n):\n    # your code here\n    pass\n",
        reference_solution=(
            "def climb_stairs(n):\n"
            "    a, b = 1, 1\n"
            "    for _ in range(n - 1):\n"
            "        a, b = b, a + b\n"
            "    return b\n"
        ),
        test_cases=(
            TestCase(args=(2,), expected=2, is_sample=True),
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
            'Slide a window along the string. Stretch it on the right. When a character '
            'repeats, shrink it from the left until the repeat is gone.'
        ),
        target_complexity='walk through the string once',
        prompt=(
            'You get a string `s`. Find the longest run of characters, side by side, where '
            'no character repeats. Return how long that run is.\n\n'
            'The characters must be next to each other. For `"abcabcbb"` the answer is 3, '
            'from `"abc"`.'
        ),
        function_name="length_of_longest_substring",
        starter_code=(
            "def length_of_longest_substring(s):\n    # your code here\n    pass\n"
        ),
        reference_solution=(
            "def length_of_longest_substring(s):\n"
            "    last = {}\n"
            "    best = start = 0\n"
            "    for i, ch in enumerate(s):\n"
            "        if ch in last and last[ch] >= start:\n"
            "            start = last[ch] + 1\n"
            "        last[ch] = i\n"
            "        best = max(best, i - start + 1)\n"
            "    return best\n"
        ),
        test_cases=(
            TestCase(args=("abcabcbb",), expected=3, is_sample=True),
            TestCase(args=("bbbbb",), expected=1),
            TestCase(args=("pwwkew",), expected=3),
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
            'Walk along the list keeping a running total. At each number, ask: am I better '
            'off adding this to my running total, or starting fresh from here?'
        ),
        target_complexity=(
            'walk through the list once, keeping just a couple of numbers in your head'
        ),
        prompt=(
            'You get a list of numbers, `nums`, which can include negative numbers. Find '
            'the run of numbers, side by side, that adds up to the biggest total. Return '
            'that total.\n\n'
            'The list has at least one number, and all of them might be negative.'
        ),
        function_name="max_sub_array",
        starter_code="def max_sub_array(nums):\n    # your code here\n    pass\n",
        reference_solution=(
            "def max_sub_array(nums):\n"
            "    best = current = nums[0]\n"
            "    for n in nums[1:]:\n"
            "        current = max(n, current + n)\n"
            "        best = max(best, current)\n"
            "    return best\n"
        ),
        test_cases=(
            TestCase(args=([-2, 1, -3, 4, -1, 2, 1, -5, 4],), expected=6, is_sample=True),
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
            'Sort the ranges by where they start. Then walk through once: each range either'
            ' joins the one before it or starts a new one.'
        ),
        target_complexity='sorting first is fine; after that, walk through once',
        prompt=(
            'You get a list of ranges, each written as `[start, end]`. Combine any ranges '
            'that overlap, and return the result ordered by where each range starts.\n\n'
            'Ranges that only touch, like `[1, 4]` and `[4, 5]`, still count as overlapping'
            ' and become `[1, 5]`.'
        ),
        function_name="merge",
        starter_code="def merge(intervals):\n    # your code here\n    pass\n",
        reference_solution=(
            "def merge(intervals):\n"
            "    if not intervals:\n"
            "        return []\n"
            "    out = []\n"
            "    for start, end in sorted(intervals):\n"
            "        if out and start <= out[-1][1]:\n"
            "            out[-1][1] = max(out[-1][1], end)\n"
            "        else:\n"
            "            out.append([start, end])\n"
            "    return out\n"
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
            ' as its letters in alphabetical order. Then group words by label in a '
            'dictionary.'
        ),
        target_complexity='look at each word once',
        prompt=(
            'You get a list of words, `strs`. Put words that use exactly the same letters '
            'into the same group, like `"eat"`, `"tea"` and `"ate"`. Return the groups as a'
            ' list of lists.\n\n'
            "The order of the groups, and of the words inside each group, doesn't matter."
        ),
        function_name="group_anagrams",
        starter_code="def group_anagrams(strs):\n    # your code here\n    pass\n",
        reference_solution=(
            "def group_anagrams(strs):\n"
            "    groups = {}\n"
            "    for word in strs:\n"
            "        key = ''.join(sorted(word))\n"
            "        groups.setdefault(key, []).append(word)\n"
            "    return list(groups.values())\n"
        ),
        unordered=True,
        test_cases=(
            TestCase(
                args=(["eat", "tea", "tan", "ate", "nat", "bat"],),
                expected=[["eat", "tea", "ate"], ["tan", "nat"], ["bat"]],
                is_sample=True,
            ),
            TestCase(args=([""],), expected=[[""]]),
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
            "then mark all the land joined to it as visited so you don't count it twice."
        ),
        target_complexity='visit each square in the grid once',
        prompt=(
            "You get a grid, written as a list of rows, where `'1'` is land and `'0'` is "
            'water. Count the islands.\n\n'
            "An island is land squares joined up, down, left or right. Diagonal doesn't "
            'count. Everything outside the grid is water.'
        ),
        function_name="num_islands",
        starter_code="def num_islands(grid):\n    # your code here\n    pass\n",
        reference_solution=(
            "def num_islands(grid):\n"
            "    if not grid:\n"
            "        return 0\n"
            "    rows, cols = len(grid), len(grid[0])\n"
            "    count = 0\n"
            "    for r in range(rows):\n"
            "        for c in range(cols):\n"
            "            if grid[r][c] != '1':\n"
            "                continue\n"
            "            count += 1\n"
            "            stack = [(r, c)]\n"
            "            grid[r][c] = '0'\n"
            "            while stack:\n"
            "                y, x = stack.pop()\n"
            "                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
            "                    ny, nx = y + dy, x + dx\n"
            "                    if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] == '1':\n"
            "                        grid[ny][nx] = '0'\n"
            "                        stack.append((ny, nx))\n"
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
