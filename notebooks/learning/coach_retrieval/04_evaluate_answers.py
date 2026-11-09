"""Answers for notebooks/learning/coach_retrieval/04_evaluate.ipynb. For learning: not run in CI.

The notebook only reads these when it is checked end to end (DRILL_FILL_ANSWERS=1); working through it, you fill in the
blanks yourself. Your guesses (you.guess) have no answers here: a guess is only a guess if you make it before you look.
"""

# Exercise 1: two challengers share the usual 0.05 (the Bonferroni correction), so each McNemar test must come in under
# 0.05 / 2 = 0.025. At 0.05 each, the chance that one of them wins by luck would be nearly double.
P_FOR_EACH = 0.025

# Exercise 2: a rule written after the result can be bent to fit it; logged first, with its time, it cannot (pre-registration).
# MLflow takes params and metrics in any order, and speed has nothing to do with it.
WHY_BEFORE = "a"

# Exercise 3: one minus (0.975 x 0.975) = 0.049, just under what a single test at 0.05 would have.
FLUKE_CHANCE = 0.049

# Exercise 4: the winner's curse (selection bias): what came out best on dev did so partly by luck on dev, and that luck
# does not come along to test, so the gap over the champion is most likely smaller on test.
WINNERS_CURSE = "smaller"

# Exercise 5: the forgetting check is a paired comparison of challenger against champion on the course-worded questions, and
# it uses two numbers: the paired bootstrap range of (challenger minus champion) recall@5 must include zero or sit above it,
# and McNemar's test must not show a champion win at 0.05. Losing what the champion could already do shows on the course's
# own wording, and only a paired count on the same questions can see a one-sided loss.
FORGETTING_NUMBER = "b"
