"""More Check questions for AI & ML foundations (modules/foundations.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "split_by_key": [
        ask("You're training a model on support tickets. Each customer wrote many tickets. "
            "How should you split the tickets into training and test?",
            ["At random, ticket by ticket", "By customer, so each is on one side", "By length, short ones go to test"],
            answer=1,
            clue="Think about what happens if one customer's tickets end up on both sides.",
            why="Splitting by customer means the test only has people the model never saw, so the score "
                "stays honest. A random split lets the same customer leak into both sides."),
        ask("Your model sorts documents into types. It scores 99% on the test set, which feels too "
            "good to be true. What would you check first?",
            ["Whether a document is in both sets", "Whether the model is big enough", "Whether the test set has enough rows"],
            answer=0,
            clue="A score that's too good often means the model has seen the test before.",
            why="If the same document is in training and test, that's leakage: the test is easy and the "
                "score is inflated. It's the most common reason a great score disappoints later."),
    ],
    "precision_recall": [
        ask("Only 1 in 100 machines breaks down. A model that always says \"no breakdown\" gets 99% "
            "accuracy. Is it any good?",
            ["Yes, 99% is an excellent score", "No, it never catches a breakdown", "Yes, if the test set was large"],
            answer=1,
            clue="Count how many of the real breakdowns it found.",
            why="It finds none of the breakdowns, so its recall is zero. The accuracy only looks great "
                "because breakdowns are rare."),
        ask("Your comment filter must catch nearly every toxic comment, even if it hides some harmless "
            "ones too. Which number should you watch most?",
            ["Recall: how many toxic ones it caught", "Precision: how many it hid were toxic", "Accuracy: how many it got right overall"],
            answer=0,
            clue="You care most about the toxic comments that slip through, not the harmless ones it hides.",
            why="Recall counts how many of the real toxic comments it caught. Hiding some harmless ones "
                "lowers precision, which you've said you can live with."),
    ],
    "best_threshold": [
        ask("Your fraud model sends flagged payments to a person to check. The checkers say they're "
            "drowning in false alarms. Which way should the threshold move?",
            ["Lower, so more payments get flagged", "Higher, so fewer payments get flagged", "Nowhere: thresholds don't change alarms"],
            answer=1,
            clue="A stricter threshold lets through only the cases the model is most sure about.",
            why="A higher threshold flags fewer payments, and those are more often fraud: precision goes "
                "up. The cost is missing some real fraud, so recall goes down."),
        ask("You tried thresholds on the validation set and picked 0.7. What do you do with the test set now?",
            ["Try more thresholds on it", "Skip it, validation was enough", "Check 0.7 on it once"],
            answer=2,
            clue="The test set should stay untouched by your tuning, but it still has a job.",
            why="You tune on validation, then check the chosen threshold once on test. Tuning on test as "
                "well would make its score look better than it really is."),
    ],
    "average_precision": [
        ask("1 in 100 orders gets returned. Your return-spotting model has a PR-AUC of 0.01. "
            "What does that tell you?",
            ["It's close to perfect", "It must be a bug", "It's about as good as guessing"],
            answer=2,
            clue="For PR-AUC, random guessing doesn't score 0.5. It depends on how rare the positives are.",
            why="PR-AUC's baseline is the share of positives. With 1 in 100, guessing scores about 0.01, "
                "so this model has learned nothing useful."),
        ask("A teammate reports only ROC-AUC 0.95 for a model that spots rare machine failures. "
            "What should you ask for?",
            ["Accuracy, to back up the 0.95", "PR-AUC for the same model", "Nothing: 0.95 is close to perfect"],
            answer=1,
            clue="When positives are rare, lots of easy negatives can make one of these scores look good.",
            why="ROC-AUC flatters a model when positives are rare. PR-AUC shows how well it finds the "
                "real failures near the top of the list."),
    ],
    "calibration_table": [
        ask("You ask an LLM to rate how sure it is. It says 95% on most answers. Before you "
            "auto-approve those answers, what should you do?",
            ["Check how often its 95% answers are right", "Trust it: the model knows itself", "Raise the threshold to 99% and release it"],
            answer=0,
            clue="LLMs that rate their own confidence are often too sure of themselves.",
            why="Calibration means checking that 95% really comes true about 95 times in 100. LLMs are "
                "often overconfident, so measure it before a rule depends on it."),
        ask("Two models predict which customers will cancel. Model A's Brier score is close to 0. "
            "Model B's is the same as always guessing 50%. Whose chances can you trust more?",
            ["Model A, the one close to 0", "Model B, it plays it safe", "Neither: Brier can't compare them"],
            answer=0,
            clue="The Brier score measures the gaps between what was predicted and what happened.",
            why="For a Brier score lower is better, and 0 is perfect. Scoring the same as a 50% guess "
                "means model B's chances tell you almost nothing."),
    ],
}
