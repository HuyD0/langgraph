# Concepts, for people new to coding

Read this alongside the notebooks. Start with `notebooks/m0_python_basics.ipynb`
if loops, dicts and functions are new to you.

---

## How to start when the page is blank

Looking at sample code feels like understanding. Then you face an empty cell
and nothing comes. That's normal: reading trains you to *recognise* code, and
writing needs you to *recall* it. This routine gets you from blank to something
that runs.

1. **Read the tests first.** In these notebooks the tests are the
   specification. Each `assert` is one thing your code must do.
2. **Solve one example by hand,** on paper. Notice what you kept track of in
   your head. That's usually a variable, a list or a dict.
3. **Write the steps as comments** before any code:
   ```python
   def count_positives(nums):
       # start a count at 0
       # look at each number
       # if it's above 0, add one to the count
       # give back the count
   ```
4. **Turn each comment into one line.** Write the plainest version that could
   work, even if it's slow.
5. **Run the tests. Read the first failure,** and walk that input through by
   hand. Most failures are edge cases: empty input, one item, all negative.

When you do look at a solution, close it afterwards and rewrite it from memory.
What you had to look back for is what you still need to learn.

---

## Big-O: what `O(n)` means

Big-O describes **how much more work your code does as the input grows**. `n`
is the size of the input, such as the number of items in a list.

| Big-O | In words | Typical code | n = 1,000 | n = 1,000,000 |
|---|---|---|---|---|
| O(1) | Same work at any size | `key in my_dict` | 1 step | 1 step |
| O(log n) | Halve the problem each step | binary search | ~10 | ~20 |
| O(n) | One step per item | one `for` loop | 1,000 | 1,000,000 |
| O(n log n) | A bit more than one pass | `sorted(nums)` | ~10,000 | ~20,000,000 |
| O(n²) | Every item against every item | a loop inside a loop | 1,000,000 | 1,000,000,000,000 |

Python does roughly 10 million simple steps a second. So at a million items
O(n) takes a tenth of a second and O(n²) takes more than a day. That's why
interview problems say "aim for O(n)".

**Working it out:** count how many times the innermost line can run.

- One loop over the list → O(n)
- A loop inside a loop over the same list → O(n²)
- Cutting what's left in half each time → O(log n)
- A fixed number of steps whatever the input → O(1)

**Hidden loops count.** `x in my_list` checks every item, so it's O(n), and
putting it inside a loop makes O(n²). `x in my_set` and `x in my_dict` are O(1).
That swap is the most common way to make slow code fast.

**Time vs space.** *Time* complexity counts steps. *Space* complexity counts
the extra memory you use, such as a dict that might hold every item. "O(n) time,
O(1) space" means one pass and only a few variables.

Big-O ignores constants: two passes over a list is still O(n). It answers "what
happens when the input gets huge?", not "exactly how many seconds?".

---

## Good habits and standards

Python's official style guide is **PEP 8**. Professional code also usually has
type hints, docstrings and tests. You can see all of these in `src/drill/`.

| Habit | Avoid | Prefer |
|---|---|---|
| Name things for what they hold | `x = {}` | `seen = {}` |
| snake_case names, 4-space indents (PEP 8) | `def TwoSum(Nums):` | `def two_sum(nums):` |
| Return the answer; `print` is for debugging | `print(total)` | `return total` |
| Don't change a list you were given | `nums.sort()` | `ordered = sorted(nums)` |
| Handle edge cases first | crash on `[]` | `if not nums: return None` |
| One function, one job, with a docstring | 60-line function | several short ones |

More habits:

- **Make it work, then make it fast.** A slow answer that passes beats a clever
  one that doesn't run.
- **Read errors from the bottom up.** The last line names the problem
  (`NameError` is usually a typo; `IndexError` means you went past the end of a
  list). The line number above it says where.
- **Run your code often.** After every few lines, not at the end.
- **Type hints** say what a function takes and returns:
  `def average(nums: list[float]) -> float:`. Python doesn't enforce them, but
  your editor and tools use them to catch mistakes.
- **Tests** are code that checks code. This repo uses `pytest`: a test is a
  function named `test_...` containing `assert` lines.

---

## Glossary

### Python basics

- **variable** — a name that points at a value: `total = 0`.
- **function** — a named, reusable block of code, started with `def`.
- **parameter / argument** — the parameter is the name in the `def` line; the
  argument is the value you pass in.
- **return** — hands a value back to the caller and ends the function.
- **list** — an ordered collection: `[3, 1, 2]`.
- **index** — an item's position. Counting starts at 0; `nums[-1]` is the last.
- **slice** — part of a list or string: `nums[1:3]`.
- **dict** — key-value pairs with instant lookup: `{"ana": 31}`. Also called a
  hash map.
- **set** — a collection with no duplicates and instant `in` checks.
- **tuple** — like a list, but can't be changed: `(3, 4)`.
- **None** — Python's "nothing here". A function with no `return` gives `None`.
- **exception** — an error raised while code runs, like `KeyError`.

### Problem solving

- **brute force** — try every possibility. Usually correct and slow.
- **edge case** — an unusual input at the boundary: empty, one item, negatives.
- **pattern** — a reusable idea that solves a family of problems.
- **stack** — a pile where the last item added is the first taken off.
- **sliding window** — two indices marking a stretch of a list, grown on one
  side and shrunk on the other.
- **binary search** — find something in sorted data by checking the middle and
  dropping half.
- **dynamic programming** — build the answer from answers to smaller versions.
- **recursion** — a function that calls itself on a smaller input, with a
  stopping rule.

### Terms from milestones 1-6

- **TypedDict** — a dict with a declared set of keys and types (milestone 1).
- **mutate** — change a value in place. Mutating something other code still
  holds causes surprising bugs (milestone 1).
- **partial update** — a node returns only the keys it changed (milestone 1).
- **dataclass** — a short way to write a class that mostly holds data
  (milestone 2).
- **pure function** — output depends only on inputs, and nothing outside is
  changed. The easiest kind to test (milestone 3).
- **aggregation** — combining many records into a summary, like a count or an
  average per topic (milestone 4).
- **subprocess** — running another program from your program (milestone 5).
- **serialisation** — turning data into text (often JSON) so it can be saved or
  sent, and back again (milestone 5).
- **state / node / edge** — in LangGraph, the state is the data passed along;
  a node is a function that updates it; an edge says what runs next
  (milestone 6).
- **conditional edge** — an edge that picks the next node from the state, which
  is how a graph branches or loops (milestone 6).
- **checkpointer** — saves state after each step so a graph can pause and
  resume (milestone 6).
- **TDD** — test-driven development: read or write the test first, watch it
  fail, then write code until it passes.
