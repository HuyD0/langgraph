"""The Learn panel for the classic interview problems.

The problems themselves (prompt, cases, solution) are :data:`drill.problems.ALL_PROBLEMS`,
the same bank ``drill start`` drills. This is only the page's extra teaching text.
"""

LEARN = {
    'two_sum': {
        'concepts': [
            [
                'Dictionary (dict)',
                'Stores pairs of key and value. Checking whether a key is in a dict is instant, however big it gets.',
                """ages = {'ana': 31}
'ana' in ages     # True, and fast
ages['bo'] = 25   # add a pair""",
            ],
            [
                'enumerate',
                "Loops over a list and gives you each item's position (index) along with the item.",
                """for i, word in enumerate(['a', 'b']):
    print(i, word)   # 0 a, then 1 b""",
            ],
            [
                'The complement',
                'If you are at number n and need a total of target, the partner you need is target - n.',
                """target, n = 9, 2
need = target - n   # 7""",
            ],
        ],
        'byhand': 'Take [2, 7, 11, 15] with target 9. Read left to right. At 2 you need 7. You haven\'t seen 7 yet, so remember "2 is at index 0". At 7 you need 2, and you have seen 2, at index 0. The answer is [0, 1].',
        'why': 'You look at each number once, and each dict check is instant, so the work grows only as fast as the list. The slow version tries every pair with a loop inside a loop.',
        'guided': """def two_sum(nums, target):
    # Replace every ___ with real code, then run the tests.

    # Step 1: a dict to remember numbers you've already seen.
    #         key = the number, value = its index
    seen = {}

    # Step 2: walk the list. enumerate gives you the index AND the number.
    for i, n in enumerate(nums):
        # Step 3: which number would pair with n to make target?
        need = ___

        # Step 4: have you already seen it? Then return both indices,
        #         the earlier one first.
        if ___:
            return ___

        # Step 5: remember n and its index for the numbers still to come.
        ___

    return []
""",
    },
    'valid_parentheses': {
        'concepts': [
            [
                'Stack',
                'A pile where you only touch the top. In Python a plain list works: append() puts on top, pop() takes the top off.',
                """stack = []
stack.append('(')
stack.append('[')
stack.pop()        # '[' comes off first""",
            ],
            [
                'Dict as a lookup table',
                'Map each closing bracket to the opening bracket it needs.',
                """pairs = {')': '('}
pairs[')']   # '('""",
            ],
            [
                'Empty means falsy',
                'An empty list counts as False in an if. not stack is True when the stack is empty.',
                """stack = []
if not stack:
    print('empty')""",
            ],
        ],
        'byhand': 'Take "([)]". Push "(", push "[". Now ")" arrives, but the top of the pile is "[". They don\'t match, so the answer is False. Try "{[]}" yourself: every closer should find its partner on top.',
        'why': 'You read each character once, and adding to or taking from the stack is instant. If the string is all openers, the stack holds all of them.',
        'guided': """def is_valid(s):
    # Replace every ___ with real code, then run the tests.

    # Step 1: map each closing bracket to the opener it needs.
    pairs = {')': '(', ']': '[', '}': '{'}

    # Step 2: a list used as a stack.
    stack = []

    for ch in s:
        if ch in pairs:
            # Step 3: ch is a closer. It must match the most recent opener.
            #         What should happen if the stack is empty?
            if ___:
                return False
        else:
            # Step 4: ch is an opener. Save it for later.
            ___

    # Step 5: the string is valid only if nothing is left open.
    return ___
""",
    },
    'binary_search': {
        'concepts': [
            [
                'Sorted input is a clue',
                'When a list is sorted, one look at the middle tells you which half the target must be in.',
                """nums = [1, 3, 5, 7, 9]
# middle is 5. Looking for 7? It must be to the right.""",
            ],
            [
                'Integer division //',
                'Divides and rounds down, so the result can be used as an index.',
                '7 // 2   # 3',
            ],
            [
                'while loop',
                "Repeats while a condition stays true. Use it when you don't know in advance how many steps you need.",
                """lo, hi = 0, 4
while lo <= hi:
    ...   # shrink lo..hi each time""",
            ],
        ],
        'byhand': 'Find 9 in [-1, 0, 3, 5, 9, 12]. Look at the middle (index 2, value 3). 9 is bigger, so drop everything up to index 2. Now look between index 3 and 5: middle is index 4, value 9. Found it.',
        'why': "Each step throws away half of what's left. A million items take only about 20 steps, because you can halve a million only about 20 times.",
        'guided': """def search(nums, target):
    # Replace every ___ with real code, then run the tests.

    # Step 1: lo and hi mark the part of the list that could still hold target.
    lo, hi = 0, len(nums) - 1

    # Step 2: keep going while that part still has at least one item.
    while ___:
        mid = (lo + hi) // 2

        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            # Step 3: target is bigger. Which half can you throw away?
            lo = ___
        else:
            hi = ___

    return -1
""",
    },
    'climbing_stairs': {
        'concepts': [
            [
                'Build on smaller answers',
                'To reach step k your last move was 1 step (from k-1) or 2 steps (from k-2). So ways(k) = ways(k-1) + ways(k-2).',
                """# ways(1) = 1, ways(2) = 2
# ways(3) = ways(2) + ways(1) = 3""",
            ],
            [
                'Swapping two variables at once',
                'Python can update two names in one line. Both right-hand values are worked out first.',
                """a, b = 1, 2
a, b = b, a + b   # a is 2, b is 3""",
            ],
            [
                'range',
                'range(2, 6) counts 2, 3, 4, 5. It stops before the second number.',
                """for k in range(2, 6):
    print(k)""",
            ],
        ],
        'byhand': 'Write the counts in a row: step 1 has 1 way, step 2 has 2 ways. Each next one is the sum of the two before it: 3, 5, 8. So 5 steps has 8 ways. You only ever need the last two numbers.',
        'why': 'One walk from step 2 up to n, keeping only two numbers. The obvious recursive version works out the same steps over and over, which is why it times out on bigger inputs.',
        'guided': """def climb_stairs(n):
    # Replace every ___ with real code, then run the tests.

    # ways(k) = ways(k - 1) + ways(k - 2)
    # Step 1: prev is ways(k - 1) and curr is ways(k), starting at k = 1.
    prev, curr = 1, 1

    # Step 2: move up one step at a time until you reach n.
    for _ in range(2, n + 1):
        # The new curr is the sum of the last two; the old curr becomes prev.
        prev, curr = ___, ___

    return curr
""",
    },
    'longest_unique_substring': {
        'concepts': [
            [
                'Sliding window',
                'Track a stretch of the string with a left edge (start) and a right edge (i). Move right every step, and move left only when the stretch breaks the rule.',
                """s = 'abcab'
# window s[start:i + 1]""",
            ],
            [
                'Substring vs subsequence',
                'A substring is a run of characters next to each other. A subsequence may skip characters. This problem wants a substring.',
                "'pwwkew'  # 'wke' is a substring, 'pwke' is not",
            ],
            [
                'max',
                'Returns the bigger of its arguments. Handy for keeping a best-so-far.',
                """best = 0
best = max(best, 3)   # 3""",
            ],
        ],
        'byhand': 'Take "abcabcbb". Grow the window: a, ab, abc (length 3). The next "a" is already inside, so move the left edge past the old "a": now "bca". Keep going. The longest the window ever gets is 3.',
        'why': 'Both edges of the window only move forward, so each character is visited only a couple of times. The dict holds at most one entry per different character.',
        'guided': """def length_of_longest_substring(s):
    # Replace every ___ with real code, then run the tests.

    last_seen = {}   # character -> the last index it appeared at
    start = 0        # left edge of the current window
    best = 0

    for i, ch in enumerate(s):
        # Step 1: if ch already appears INSIDE the window (at or after start),
        #         move start to just past that earlier copy.
        if ch in last_seen and ___:
            start = ___

        # Step 2: record where you saw ch.
        last_seen[ch] = i

        # Step 3: the window runs from start to i. How long is that?
        best = max(best, ___)

    return best
""",
    },
    'max_subarray': {
        'concepts': [
            [
                'Running total',
                'Keep a number that you update as you walk the list, instead of re-adding everything each time.',
                """total = 0
for n in [3, -1, 2]:
    total += n""",
            ],
            [
                'Slicing',
                'nums[1:] is the list without its first item. nums[-1] is the last item.',
                '[4, 5, 6][1:]   # [5, 6]',
            ],
            [
                'Two kinds of best',
                "current is the best sum of a run that ends right here. best is the best you've seen anywhere.",
                'best = current = nums[0]',
            ],
        ],
        'byhand': 'Take [-2, 1, -3, 4, -1, 2, 1, -5, 4]. At each number ask: am I better off adding it to the run I have, or starting fresh here? At 4 the old run (-2+1-3 = -4) only hurts, so start fresh. 4, -1, 2, 1 adds up to 6, the best.',
        'why': 'One walk with two numbers to update. Checking every possible start and end would check every pair, which gets slow on long lists.',
        'guided': """def max_sub_array(nums):
    # Replace every ___ with real code, then run the tests.

    # current = best sum of a run that ENDS at this element
    # best    = best sum seen anywhere so far
    best = current = nums[0]

    for n in nums[1:]:
        # Step 1: either extend the run with n, or start a new run at n.
        current = max(___, ___)

        # Step 2: keep the best you've seen.
        best = ___

    return best
""",
    },
    'merge_intervals': {
        'concepts': [
            [
                'sorted',
                'Returns a new sorted list. Lists of pairs sort by their first item, then their second.',
                'sorted([[5, 6], [1, 2]])   # [[1, 2], [5, 6]]',
            ],
            [
                'Unpacking in a loop',
                'When each item is a pair, you can name both parts in the for line.',
                """for start, end in [[1, 3], [2, 6]]:
    print(start, end)""",
            ],
            [
                'The last item',
                'result[-1] is the last thing you added. result[-1][1] is its end.',
                """merged = [[1, 3]]
merged[-1][1]   # 3""",
            ],
        ],
        'byhand': 'Sort [[1,3],[2,6],[8,10],[15,18]] by start (already sorted). Start a result with [1,3]. [2,6] starts at 2, before 3 ends, so stretch to [1,6]. [8,10] starts after 6, so add it. Same for [15,18].',
        'why': 'Sorting is the slowest part; the sweep after it is a single walk. The result can hold every interval.',
        'guided': """def merge(intervals):
    # Replace every ___ with real code, then run the tests.

    merged = []

    # Step 1: go through the intervals in order of their start.
    for start, end in sorted(intervals):
        # Step 2: does this one overlap the last interval in merged?
        #         Touching counts: [1, 4] and [4, 5] overlap.
        if merged and ___:
            # Step 3: stretch the last interval's end if this one goes further.
            merged[-1][1] = ___
        else:
            merged.append([start, end])

    return merged
""",
    },
    'group_anagrams': {
        'concepts': [
            [
                'Anagram',
                'Two words with exactly the same letters in a different order, like tea and eat.',
                "sorted('tea') == sorted('eat')   # True",
            ],
            [
                'Turning a list back into a string',
                "''.join(...) glues a list of characters into one string, which can be a dict key.",
                "''.join(['a', 'e', 't'])   # 'aet'",
            ],
            [
                'Dict of lists',
                'Group things by giving each group a key and a list.',
                """groups = {}
groups.setdefault('aet', []).append('tea')""",
            ],
        ],
        'byhand': 'For each word, sort its letters: eat → aet, tea → aet, tan → ant, ate → aet, nat → ant, bat → abt. Words with the same sorted letters go in the same group.',
        'why': 'Each word is sorted once to make its key, and every word is stored once in its group.',
        'guided': """def group_anagrams(strs):
    # Replace every ___ with real code, then run the tests.

    groups = {}   # key -> list of words that share the key

    for word in strs:
        # Step 1: build a key that comes out the same for every anagram.
        #         sorted('tea') gives ['a', 'e', 't'] - a list can't be a
        #         dict key, but a string can.
        key = ___

        # Step 2: put word in its group, creating the group first if needed.
        if key not in groups:
            groups[key] = []
        ___

    # Step 3: you only need the groups, not the keys.
    return list(groups.values())
""",
    },
    'num_islands': {
        'concepts': [
            [
                'Grid as a list of lists',
                'grid[r][c] is row r, column c. len(grid) is the number of rows.',
                """grid = [['1', '0'],
        ['0', '1']]
grid[1][1]   # '1'""",
            ],
            [
                'Neighbours',
                'From (r, c) the four neighbours are one row up or down, or one column left or right. Check they are still inside the grid.',
                """for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    nr, nc = r + dr, c + dc""",
            ],
            [
                'Recursion',
                "A function that calls itself on a smaller piece of the problem. It needs a stopping rule so it doesn't go forever.",
                """def countdown(k):
    if k == 0:
        return
    countdown(k - 1)""",
            ],
        ],
        'byhand': 'Scan the grid row by row. The first "1" you hit is a new island: count it, then flood out from it, turning every connected "1" into "0" so you don\'t count it again. Keep scanning. Each new "1" you meet after that is a new island.',
        'why': 'Every cell is looked at only a couple of times: once by the scan, and at most once by a flood.',
        'guided': """def num_islands(grid):
    # Replace every ___ with real code, then run the tests.

    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])

    def sink(r, c):
        # Step 1: stop if (r, c) is outside the grid, or is water.
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1':
            return
        # Step 2: mark this land as visited by turning it into water.
        grid[r][c] = '0'
        # Step 3: sink the four neighbours: up, down, left and right.
        ___

    count = 0
    for r in range(rows):
        for c in range(cols):
            # Step 4: unvisited land means a new island.
            if grid[r][c] == '1':
                count += 1
                ___

    return count
""",
    },
}
