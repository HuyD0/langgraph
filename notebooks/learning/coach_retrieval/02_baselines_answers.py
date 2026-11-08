"""Answers for notebooks/learning/coach_retrieval/02_baselines.ipynb. For learning: not run in CI.

The notebook only reads these when it is checked end to end (DRILL_FILL_ANSWERS=1); working through it, you fill in the
blanks yourself. Your guesses (you.guess) have no answers here: a guess is only a guess if you make it before you look.
"""

# Exercise 1: first ranks [1, 3, None, 7, 1]. hit@1 counts the two at rank 1; recall@5 counts ranks 1, 3 and 1 (rank 7 is
# too far down, None never came up).
HIT1_AND_RECALL5 = (0.4, 0.6)

# Exercise 2: only the champion found b and f; only the word table found e. a and d (both) and c (neither) do not count.
ONLY_COUNTS = (2, 1)

# Exercise 3: a range from -0.10 to +0.02 straddles zero, so neither side's win is shown, whatever the point estimate says.
READING = "not shown"

# Exercise 4: the learner waits for their own question to be embedded; the course is embedded once, before anyone asks.
WAIT_COLUMN = "ms/question"
