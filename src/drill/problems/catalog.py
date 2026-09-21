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
        pattern="Trade memory for time: a dict turns a nested scan into one pass.",
        target_complexity="O(n) time, O(n) space",
        prompt=(
            "Given a list of integers `nums` and an integer `target`, return the "
            "indices of the two numbers that add up to `target`.\n\n"
            "Exactly one valid answer exists, and you may not use the same element "
            "twice. Return the indices in increasing order."
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
        pattern="A stack matches nested pairs: push openers, pop on the closer.",
        target_complexity="O(n) time, O(n) space",
        prompt=(
            "Given a string `s` containing only the characters `()[]{}`, return "
            "`True` if every bracket is closed by the same type in the correct "
            "order, and `False` otherwise.\n\n"
            "An empty string is valid."
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
        pattern="Halve the search space each step; the bug is always the boundary.",
        target_complexity="O(log n) time, O(1) space",
        prompt=(
            "Given a list `nums` sorted in ascending order and an integer "
            "`target`, return the index of `target`, or `-1` if it is not "
            "present.\n\nYour solution must run in O(log n) time."
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
        pattern="Build the answer from smaller answers; keep only what you still need.",
        target_complexity="O(n) time, O(1) space",
        prompt=(
            "You are climbing a staircase with `n` steps. Each move you may climb "
            "either 1 or 2 steps. Return the number of distinct ways to reach the "
            "top.\n\n`n` is at least 1."
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
        pattern="Grow a window from the right; shrink from the left when it breaks the rule.",
        target_complexity="O(n) time, O(k) space",
        prompt=(
            "Given a string `s`, return the length of the longest substring that "
            "contains no repeated characters.\n\n"
            "A substring is contiguous; a subsequence is not. You want the former."
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
        pattern="At each element, decide: extend the run, or start a new one.",
        target_complexity="O(n) time, O(1) space",
        prompt=(
            "Given a list of integers `nums`, find the contiguous subarray with the "
            "largest sum and return that sum.\n\n"
            "The list has at least one element, and may be entirely negative."
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
        pattern="Sort first, then a single sweep makes the overlap rule obvious.",
        target_complexity="O(n log n) time, O(n) space",
        prompt=(
            "Given a list of intervals `[start, end]`, merge all overlapping "
            "intervals and return the result sorted by start.\n\n"
            "Intervals that merely touch, such as `[1, 4]` and `[4, 5]`, do overlap."
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
        pattern="Design a key that collides exactly when two things should group.",
        target_complexity="O(n k log k) time, O(n k) space",
        prompt=(
            "Given a list of strings `strs`, group the anagrams together and "
            "return the groups as a list of lists.\n\n"
            "Neither the order of the groups nor the order within a group matters."
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
        pattern="A grid is a graph. Flood-fill from each unvisited start, count the starts.",
        target_complexity="O(rows * cols) time",
        prompt=(
            "Given a 2D grid of `'1'` (land) and `'0'` (water) characters, return "
            "the number of islands.\n\n"
            "An island is land connected horizontally or vertically - not "
            "diagonally - and the grid is surrounded by water on all sides."
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
