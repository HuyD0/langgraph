"""The Learn panel for the classic interview problems.

The problems themselves (prompt, cases, solution) are :data:`drill.problems.ALL_PROBLEMS`,
the same bank ``drill start`` drills. This is only the page's extra teaching text.

``byhand`` walks through each problem's sample case with its real values, so keep the two
in step: change the sample and you must redo the walk-through. ``guided`` is the scaffold
the Build step starts from; its blanks are the key idea, and every comment says in words
what goes in them.
"""

LEARN = {
    'two_sum': {
        'concepts': [
            [
                'Dictionary (dict)',
                'A dict stores pairs: a key and its value. `key in ages` checks whether a key is there, and it is instant however big the dict gets.',
                """ages = {'ana': 31}
ages['ana']       # 31
ages['bo'] = 25   # adds a pair""",
            ],
            [
                'enumerate',
                "Loops over a list and gives you each item's position along with the item.",
                """for i, w in enumerate(['a', 'b']):
    print(i, w)   # 0 a, then 1 b""",
            ],
            [
                'The partner number',
                'If you are on number `n` and want a total of `target`, the partner you need is `target - n`.',
                """budget = 10
spent = 3
left = budget - spent   # 7""",
            ],
        ],
        'byhand': 'Read the list left to right. Position 0 holds 2. Its partner would be 7, since 2 plus 7 is 9. You haven\'t seen 7 yet, so remember that 2 is at position 0. Position 1 holds 7. Its partner would be 2, and you saw 2 at position 0. Return [0, 1].',
        'why': 'You look at each number once, and each dict check is instant, so the work grows only as fast as the list. The slow way tries every pair, with a loop inside a loop.',
        'guided': """def two_sum(numbers, target):
    # Replace every ___ with real code, then run the tests.

    # A dict of numbers seen so far.
    # key = the number, value = its position
    seen = {}

    for i, n in enumerate(numbers):
        # Step 1: the partner n needs to make target.
        need = ___

        # Step 2: seen the partner already? Return a
        #         list: its position (stored in seen)
        #         first, then i.
        if need in seen:
            return ___

        # Step 3: store n's position, i, in seen.
        ___

    # Never reached: there is always one pair.
    return []
""",
    },
    'valid_parentheses': {
        'concepts': [
            [
                'Looping over a string',
                'A `for` loop over a string gives you one character at a time.',
                """for ch in 'hi':
    print(ch)   # h, then i""",
            ],
            [
                'A list as a stack',
                'A stack is a pile where you only touch the top. `append` puts an item on top, `pile[-1]` looks at the top item, and `pop()` takes the top item off.',
                """pile = ['a']
pile.append('b')   # ['a', 'b']
pile[-1]           # 'b', the top""",
            ],
            [
                'Not equal: !=',
                '`!=` means "is not equal to". `a != b` is `True` when the two are different.',
                """pile = ['a', 'b']
pile[-1] != 'a'   # True: top is 'b'""",
            ],
            [
                'Dict as a lookup table',
                'A dict can map one thing to another. `d[x]` gives the value stored for key `x`. `x in d` checks whether `x` is one of its keys, and `x not in d` checks that it isn\'t.',
                """capital = {'France': 'Paris'}
capital['France']   # 'Paris'
'Peru' in capital   # False""",
            ],
            [
                'An empty list counts as False',
                '`not pile` is `True` when the list is empty, and `False` when it has something in it.',
                """pile = []
not pile   # True""",
            ],
            [
                'elif and or',
                '`elif` means "else, if": it is only checked when the `if` above was false. `a or b` is `True` when either side is true.',
                """pile = []
not pile or 1 > 2   # True: the pile is empty""",
            ],
        ],
        'byhand': 'Read left to right, using a stack (a pile where you only touch the top). "{" opens: put it on the stack. "[" opens: put it on top. "]" closes, and the top is "[", its partner: take it off. "}" closes, and the top is now "{", its partner: take it off. The stack is empty at the end, so return True.',
        'why': 'You read each character once, and putting on or taking off the top of the stack is instant.',
        'guided': """def is_valid(brackets):
    # Replace every ___ with real code, then run the tests.

    # Each closing bracket, and the opener it needs.
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []   # openers still waiting to close

    for bracket in brackets:
        if bracket not in pairs:
            # Step 1: an opener. Put it on the stack.
            ___
        # Step 2: a closer. Fail if nothing is open,
        #         or if the top of the stack isn't
        #         the opener it needs: pairs[bracket].
        elif not stack or ___:
            return False
        else:
            # It matches: take that opener off the top.
            stack.pop()

    # Step 3: valid only if nothing is left open.
    return ___
""",
    },
    'binary_search': {
        'concepts': [
            [
                'Floor division //',
                'Divides and drops anything after the decimal point, so the answer is a whole number you can use as a position.',
                '7 // 2   # 3',
            ],
            [
                'while loop',
                "Repeats while its condition stays true. Use it when you don't know in advance how many rounds you need.",
                """count = 3
while count > 0:
    count = count - 1""",
            ],
            [
                'Comparing: <=',
                '`a <= b` is `True` when `a` is smaller than `b` or equal to it.',
                """3 <= 3   # True
4 <= 3   # False""",
            ],
            [
                'The last position',
                'A list of 5 items has positions 0 to 4, so the last position is `len(items) - 1`.',
                """items = ['a', 'b', 'c']
len(items) - 1   # 2""",
            ],
            [
                'if, elif, else',
                'Checks each condition in order and runs the first one that is true. `else` runs when none of them are.',
                """if age < 13: print('child')
elif age < 20: print('teen')
else: print('adult')""",
            ],
        ],
        'byhand': 'At first the search area is the whole list: low is position 0 and high is position 4. The middle is position 2, which holds 5. 7 is bigger than 5, so it must be to the right: low moves to 3, and the area is positions 3 to 4. Halfway between 3 and 4, rounded down, is position 3. It holds 7. Found it: return 3.',
        'why': "Each step throws away half of what's left. A million items take only about 20 steps, because you can halve a million only about 20 times.",
        'guided': """def search(numbers, target):
    # Replace every ___ with real code, then run the tests.

    # target can only be between positions low and
    # high. At first, that's the whole list.
    low = 0
    high = len(numbers) - 1

    # Step 1: keep going while low is at or before
    #         high. When they're equal, one item is
    #         still left to check.
    while ___:
        mid = (low + high) // 2   # the middle

        if numbers[mid] == target:
            return mid
        elif numbers[mid] < target:
            # Step 2: target is bigger, so it's right
            #         of mid. Move low to just after mid.
            low = ___
        else:
            # Step 3: target is smaller, so it's left
            #         of mid. Move high to just before mid.
            high = ___

    return -1
""",
    },
    'climbing_stairs': {
        'concepts': [
            [
                'range with a start',
                '`range(3, 6)` counts 3, 4, 5. It stops just before the second number, so `range(3, steps + 1)` ends at `steps`.',
                """for k in range(3, 6):
    print(k)   # 3, then 4, then 5""",
            ],
            [
                'Update in the right order',
                'When you shift values along, copy the old value before you overwrite it. Once a name gets a new value, the old one is gone.',
                """today = 5
yesterday = today   # copy first: 5
today = 8           # then move on""",
            ],
        ],
        'byhand': 'Count the ways to reach each step, from the bottom. Step 1: 1 way. Step 2: 2 ways (1 then 1, or 2). Step 3: your last move came from step 2 or step 1, so 2 plus 1 is 3 ways. Step 4: your last move came from step 3 or step 2, so 3 plus 2 is 5 ways. Return 5.',
        'why': 'One walk up the stairs, keeping only two numbers. Listing every order one by one would take far too long for 40 steps.',
        'guided': """def climb_stairs(steps):
    # Replace every ___ with real code, then run the tests.

    if steps == 1:
        return 1

    # Ways to reach the step below you, and the step
    # you're on. Start standing on step 2.
    ways_below = 1   # step 1
    ways_here = 2    # step 2

    # Climb one step at a time, from step 3 to the top.
    for step in range(3, steps + 1):
        # Part 1: you reach the next step from here
        #         (a 1-step move) or from below (a
        #         2-step move). Add the two counts.
        new = ___
        # Part 2: move up one. The old "here" count
        #         is now below, and new is here.
        ways_below = ___
        ways_here = ___

    return ways_here
""",
    },
    'longest_unique_substring': {
        'concepts': [
            [
                'A set',
                "A set holds each item at most once. `add` puts one in, `remove` takes out the one you name, and `in` checks for one instantly. A set has no order, so `seen[0]` doesn't work.",
                """seen = set()
seen.add('x')
'x' in seen   # True""",
            ],
            [
                'Positions in a string',
                "`word[0]` is a string's first character, `word[1]` the second, and so on. `enumerate(word)` gives each position along with its character.",
                """for i, ch in enumerate('hi'):
    print(i, ch)   # 0 h, then 1 i""",
            ],
            [
                'while loop',
                'Repeats while its condition stays true, and stops as soon as it is false.',
                """count = 3
while count > 0:
    count = count - 1""",
            ],
            [
                'Adding 1: +=',
                '`start += 1` is short for `start = start + 1`. It adds 1 to `start`.',
                """start = 2
start += 1   # now 3""",
            ],
            [
                'Length of a stretch',
                'A stretch from position `start` to position `i`, counting both ends, has `i - start + 1` characters.',
                """start = 2
i = 4
i - start + 1   # 3: 2, 3 and 4""",
            ],
            [
                'max',
                '`max(a, b)` gives the bigger of the two. Handy for keeping a best-so-far.',
                """best = 0
best = max(best, 3)   # 3""",
            ],
        ],
        'byhand': 'The window is the stretch of characters you\'re looking at now, with no repeats. It starts empty. p: add it, window "p". w: add it, window "pw". The next w is already in the window, so drop the window\'s first character until it isn\'t: drop p, then drop w. Add the new w: window "w". k: window "wk". e: window "wke", length 3. The last w is in the window, so drop the first character, w: "ke". Add w: "kew", length 3. The longest was 3, so return 3.',
        'why': 'Each character is added to the window once and dropped at most once, so the work grows only as fast as the string.',
        'guided': """def length_of_longest_substring(text):
    # Replace every ___ with real code, then run the tests.

    # The window: the stretch of text you're
    # looking at now, with no repeats.
    window = set()   # its characters
    start = 0        # its first position in text
    best = 0         # longest length so far

    for i, char in enumerate(text):
        # Step 1: while char is already in the window,
        #         drop the window's first character: the
        #         one at position start in text.
        while ___:
            window.remove(___)
            start += 1

        # Add char: now the window runs from start to i.
        window.add(char)

        # Step 2: work out the window's length, from
        #         start to i, and keep the longest.
        best = max(best, ___)

    return best
""",
    },
    'max_subarray': {
        'concepts': [
            [
                'Running total',
                'A number you update as you walk the list, instead of adding everything up again each time.',
                """total = 0
for price in [3, 5]:
    total = total + price""",
            ],
            [
                'max',
                '`max(a, b)` gives the bigger of the two.',
                'max(-2, 7)   # 7',
            ],
            [
                'Skipping the first item',
                '`numbers[1:]` is the list without its first item.',
                '[4, 5, 6][1:]   # [5, 6]',
            ],
        ],
        'byhand': 'Keep two numbers: the running total, and the best total so far. 3: running is 3, best is 3. -4: adding it gives -1, better than starting again at -4, so running is -1. Best stays 3. 2: starting again at 2 beats adding it to -1 (which gives 1), so running is 2. Best stays 3. -1: adding it gives 1, better than -1 alone, so running is 1. Best stays 3. 4: adding it gives 5, better than 4 alone, so running is 5 and best is 5. Return 5.',
        'why': 'One walk with two numbers to update. Checking every possible start and end would take far longer on long lists.',
        'guided': """def max_sub_array(numbers):
    # Replace every ___ with real code, then run the tests.

    # running = best total of a run ending here
    # best    = best total seen anywhere so far
    best = numbers[0]
    running = numbers[0]

    for n in numbers[1:]:
        # Step 1: add n to the run, or start a new
        #         run at n. Keep whichever is bigger.
        running = max(___, n)

        # Step 2: keep the best total you've seen.
        best = ___

    return best
""",
    },
    'merge_intervals': {
        'concepts': [
            [
                'sorted',
                'Returns a new sorted list. A list of pairs sorts by the first item, then by the second.',
                """pairs = [[5, 6], [1, 2]]
sorted(pairs)
# [[1, 2], [5, 6]]""",
            ],
            [
                'Naming both parts in a loop',
                'When each item is a pair, you can name both parts in the `for` line.',
                """for first, last in [['Ana', 'Lee']]:
    print(first, last)   # Ana Lee""",
            ],
            [
                'The last item',
                '`spans[-1]` is the last item in a list, and `spans[-1][1]` is the second part of that item. `if spans:` is true only when the list is not empty.',
                """spans = [[1, 3], [5, 9]]
spans[-1]      # [5, 9]
spans[-1][1]   # 9""",
            ],
            [
                'Comparing: <=',
                '`a <= b` is `True` when `a` is smaller than `b` or equal to it.',
                """3 <= 3   # True
4 <= 3   # False""",
            ],
            [
                'max',
                '`max(a, b)` gives the bigger of the two.',
                'max(4, 9)   # 9',
            ],
        ],
        'byhand': 'Sort by start: they are already in order. Start the result with [1, 3]. [2, 6] starts at 2, before [1, 3] ends at 3, so they overlap: stretch it to [1, 6]. [8, 10] starts after 6, so add it as a new interval. [15, 18] starts after 10, so add it too. Return [[1, 6], [8, 10], [15, 18]].',
        'why': 'Sorting is the slowest part. The walk after it looks at each interval once.',
        'guided': """def merge(intervals):
    # Replace every ___ with real code, then run the tests.

    merged = []

    # Go through the intervals in order of start.
    for start, end in sorted(intervals):
        # Step 1: does this one overlap the last
        #         merged interval? It does if it starts
        #         at or before that interval's end.
        if merged and ___:
            # Step 2: stretch the last interval's end
            #         if this one reaches further.
            merged[-1][1] = ___
        else:
            merged.append([start, end])

    return merged
""",
    },
    'group_anagrams': {
        'concepts': [
            [
                'sorted on a word',
                "`sorted` on a string gives its letters in alphabetical order, as a list.",
                "sorted('cab')   # ['a', 'b', 'c']",
            ],
            [
                'Joining letters back into a string',
                "`''.join(...)` glues a list of letters into one string. A string can be a dict key, but a list can't. You can put `sorted(...)` straight inside it.",
                """''.join(['d', 'o', 'g'])   # 'dog'
''.join(sorted('tab'))     # 'abt'""",
            ],
            [
                'Dict of lists',
                'Each key holds a list. Make the list the first time you see the key, then append to it.',
                """teams = {}
teams['red'] = []
teams['red'].append('ana')""",
            ],
            [
                'Just the values',
                "`d.values()` gives a dict's values without the keys, and `list(...)` turns them into a list.",
                """ages = {'a': 1, 'b': 2}
list(ages.values())   # [1, 2]""",
            ],
        ],
        'byhand': 'Sort each word\'s letters to get its label. "eat" gives "aet": a new group. "tan" gives "ant": a new group. "tea" gives "aet", so it joins "eat". "nat" gives "ant", so it joins "tan". "bat" gives "abt": a new group. Return [["eat", "tea"], ["tan", "nat"], ["bat"]].',
        'why': 'Each word is sorted once to make its label, and stored once in its group.',
        'guided': """def group_anagrams(words):
    # Replace every ___ with real code, then run the tests.

    groups = {}   # label -> words with that label

    for word in words:
        # Step 1: a label that's the same for every
        #         anagram: the word's letters, sorted,
        #         joined back into one string.
        label = ___

        # Step 2: add word to its group. Make the
        #         group first if the label is new.
        if label not in groups:
            groups[label] = []
        ___

    # You only need the groups, not the labels.
    return list(groups.values())
""",
    },
    'num_islands': {
        'concepts': [
            [
                'Grid as a list of rows',
                '`board[row][col]` is the square in that row and column, both counted from 0. `len(board)` is the number of rows, and `len(board[0])` the number of columns.',
                """board = [['a', 'b'],
         ['c', 'd']]
board[1][0]   # 'c'""",
            ],
            [
                'Neighbours',
                'The square above is `row - 1`, the one below is `row + 1`, left is `col - 1` and right is `col + 1`. Check they are still inside the grid.',
                """# around row 2, col 3:
# above (1, 3)  below (3, 3)
# left (2, 2)   right (2, 4)""",
            ],
            [
                'A function that calls itself',
                'A function can call itself to do the same job on a nearby piece. It needs a rule that stops it, or it would never end.',
                """def countdown(k):
    if k > 0:
        countdown(k - 1)""",
            ],
            [
                'A function inside a function',
                'A function defined inside another one can use the outer one\'s names, like `grid`, `height` and `width`.',
                """def outer():
    name = 'Ana'
    def greet(): print(name)""",
            ],
            [
                'Counting with range',
                '`range(3)` counts 0, 1, 2. It stops just before the number you give, so `range(height)` gives every row number.',
                """for row in range(3):
    print(row)   # 0, then 1, then 2""",
            ],
            [
                'Adding 1: +=',
                '`count += 1` is short for `count = count + 1`. It adds 1 to `count`.',
                """count = 0
count += 1   # now 1""",
            ],
        ],
        'byhand': 'Scan row by row. The top-left square is land you haven\'t visited: that\'s island 1. Sink it: it turns to water, and so does the land joined to it, the square to its right and the square below it. Keep scanning. Everything else is water until the bottom-right square, which is land: island 2. Sink it. No land touches it. Return 2.',
        'why': 'Each square is looked at only a few times: once by the scan, and at most once from each of its four neighbours.',
        'guided': """def num_islands(grid):
    # Replace every ___ with real code, then run the tests.

    if not grid:   # an empty grid has no islands
        return 0
    height = len(grid)     # number of rows
    width = len(grid[0])   # number of columns

    def sink(row, col):
        # Stop if outside the grid, or not land.
        if row < 0 or row >= height:
            return
        if col < 0 or col >= width:
            return
        if grid[row][col] != '1':
            return
        # This changes grid itself. Fine for this
        # puzzle; in real code, copy it first.
        # Step 1: mark this land as visited by
        #         turning it into water.
        grid[row][col] = ___
        # Step 2: sink the four neighbours: down, up,
        #         right, and the one on the left.
        sink(row + 1, col)
        sink(row - 1, col)
        sink(row, col + 1)
        ___

    count = 0
    for row in range(height):
        for col in range(width):
            # Step 3: unvisited land is a new island.
            #         Count it, then sink it.
            if grid[row][col] == '1':
                count += 1
                ___

    return count
""",
    },
}
