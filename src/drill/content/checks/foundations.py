"""More Check questions for AI & ML foundations (modules/foundations.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "models_on_your_computer": [
        ask("A model file is 2 GB, stored in 32-bit. Before the in-between numbers, roughly how much memory does "
            "training it with AdamW need?",
            ["About 8 GB", "About 2 GB", "About 4 GB"],
            answer=0,
            clue="Beside each weight, training keeps a gradient and the optimiser's two running averages.",
            why="Four numbers for every weight: the weight, its gradient and two running averages. Four times 2 GB "
                "is about 8 GB, and the in-between numbers come on top."),
        ask("Ollama's copy of a model is about half the size of the copy in your Hugging Face cache. What is the "
            "most likely reason?",
            ["It keeps each weight in 16 bits", "It left out half of the weights", "It is a different, smaller model"],
            answer=0,
            clue="Count the bits each number is kept in.",
            why="Half precision keeps each number in 16 bits instead of 32, so the same weights take half the memory, "
                "and each number is kept a little less exactly. In the lab the two copies gave the same answers."),
    ],
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
}
