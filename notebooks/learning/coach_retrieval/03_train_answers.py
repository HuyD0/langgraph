"""Answers for notebooks/learning/coach_retrieval/03_train.ipynb. For learning: not run in CI.

The notebook only reads these when it is checked end to end (DRILL_FILL_ANSWERS=1); working through it, you fill in the
blanks yourself. Your guesses (you.guess) have no answers here: a guess is only a guess if you make it before you look.
"""

# Exercise 1: a hard negative is a paragraph of another TRAIN lesson. A dev, test or holdout paragraph used as a wrong answer
# would carry those lessons' words into training, and their scores would stop meaning "lessons it never saw".
NEGATIVE_SPLIT = "train"

# Exercise 2: the question should move towards its own paragraph, so the cosine to the positive goes up; the cosine to the
# hard negative and the loss go down.
GOES_UP = "cosine to the positive"

# Exercise 3: the train loss is measured on the rows being trained on and can reach zero while the model gets worse
# elsewhere; only a held-out score (dev, learner-worded, lessons never trained on) says the skill improved.
SKILL_NUMBER = "dev honest recall@5"

# Exercise 4: a tenth of 150 steps.
WARMUP_STEPS = 15

# Exercise 5: two seeds of the same setting differ by 0.04, so a 0.02 win is inside the seed-to-seed variation
# (what changing only the seed does): not a finding.
SEED_READING = "no"
