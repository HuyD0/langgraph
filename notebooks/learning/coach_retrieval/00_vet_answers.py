"""Answers for notebooks/learning/coach_retrieval/00_vet.ipynb. For learning: not run in CI.

The notebook only reads these when it is checked end to end (DRILL_FILL_ANSWERS=1); working through it, you fill in the
blanks yourself.
"""

# Exercise 1: the number in the one line is the share of learner-worded questions whose lesson is in the five paragraphs
# retrieved. "Questions answered a day" is traffic, not quality; model size is cost.
SUCCESS_MEASURE = "recall@5 on learner-worded questions"

# Exercise 2: the gate that stays open until stage 2 scores the word table against the champion.
GATE_OPEN = "fixed rule"

# Exercise 3: low value for Daily Drill alone (the main flow has no retrieval problem; 0 typed questions recorded),
# high doable (data ready, plain score, minutes on this computer, the owner can change the coach).
VALUE, DOABLE = "low", "high"

# Exercise 4: a served model with scale-to-zero off runs every hour of the month: 24 x 365 / 12 is about 730.
SERVING_HOURS = 730

# Exercise 5: the quick rule from "Comparing on the same examples": 20 disagreements need a gap of about 9.
NEEDED_GAP = 9
