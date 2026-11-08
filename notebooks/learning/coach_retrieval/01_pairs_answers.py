"""Answers for notebooks/learning/coach_retrieval/01_pairs.ipynb. For learning: not run in CI.

The notebook only reads these when it is checked end to end (DRILL_FILL_ANSWERS=1); working through it, you fill in
the blanks yourself. The hand check of the paraphrases (VERDICTS) has no answer here on purpose: only a person's
reading counts, so the filled-in run still reports the honest test as model-made.
"""

# Exercise 1: a question that appears under several lessons has no single right lesson, so it makes no pair at all.
PAIRS_FROM_SHARED_QUESTION = 0

# Exercise 2: the split is dealt by whole lesson, so every question of "Evaluating agents" lands where its lesson is.
SPLIT_OF_SIBLING = "test"

# Exercise 3: the holdout split is scored once, at the very end of the lab, and never before.
HOLDOUT_SCORED_TIMES = 1

# Exercise 4: a sentence copied from the lesson shares every content word with it, so the overlap is 1.0.
OVERLAP_OF_COPY = 1.0
