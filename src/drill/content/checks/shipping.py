"""More Check questions for Shipping models and agents (modules/shipping.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "graduation_gate": [
        ask("The pack shows a good pass rate, every must-pass question passing and a fair cost. "
            "But there's no named owner and no monitoring. What does the gate report?",
            ["Pass: the numbers are good", "Two problems: no owner, no monitoring", "One problem: the first it finds"],
            answer=1,
            clue="Does the gate stop at the first problem, or keep checking?",
            why="The gate lists every check that fails, so the team can fix both in one round. "
                "Good numbers aren't enough without an owner and alerts."),
        ask("Your team's app is popular, but it still runs in the shared experiment space. "
            "What could go wrong there?",
            ["Its answers slowly get less accurate", "Its eval scores reset every week", "A busy experiment eats its capacity"],
            answer=2,
            clue="Everyone in the shared space uses the same deployment.",
            why="One busy experiment can use up the shared capacity, and nobody is named to fix things. "
                "An app people rely on needs its own capacity."),
    ],
    "promote_model": [
        ask("Your LLM judge holds @champion. You keep its prompt but switch the model that runs it to a "
            "cheaper one. How should you treat the result?",
            ["As the same judge: the prompt defines it", "As a new version that keeps @champion", "As a new version that must earn its aliases"],
            answer=2,
            clue="The prompt is only half of what grades your answers.",
            why="A judge is its prompt plus its model, so a new model means a new version. Like any challenger "
                "it starts with no alias and earns @challenger, then @champion, by beating the old judge against "
                "grades people gave."),
        ask("You promoted version 5 to @champion. An hour later it's giving bad answers. "
            "What's the quickest fix?",
            ["Retrain version 5 overnight", "Point @champion back to version 4", "Delete version 5 from the registry"],
            answer=1,
            clue="The alias is just a pointer to a version.",
            why="Rolling back is just moving the alias back. Version 4 is still in the registry, "
                "with its metrics."),
    ],
    "route_request": [
        ask("You've just built version 4 of your agent. Version 3 serves everyone today. "
            "How much traffic should version 4 get on day one?",
            ["All of it, it passed the tests", "A small share, like 10 in 100", "None until next month"],
            answer=1,
            clue="Never switch everyone at once.",
            why="A canary gets a small share first, so you can compare its traces and evals with the "
                "old version before moving the split."),
        ask("The canary has run for a day. Its traces and evals look as good as the old version's. "
            "What's the next step?",
            ["Move more traffic to it, bit by bit", "Switch everyone over at once", "Set it to 0% to be safe"],
            answer=0,
            clue="The canary passed this round. You still don't jump straight to the end.",
            why="When the canary holds up, you move the split towards it in steps, watching as you go. "
                "If it slips, set it back to 0%."),
    ],
    "prompt_rollout": [
        ask("Your rule: at least 100 traces and 10 points better. The new prompt has 200 traces "
            "and beats the old one by 12 points. What does the rule say?",
            ["Keep testing", "Roll it back", "Promote it"],
            answer=2,
            clue="Check both parts: enough traces, and a big enough gain.",
            why="200 traces is enough, and 12 points clears the 10-point threshold. The rule you wrote "
                "down first says promote."),
        ask("Traces from two prompt versions are all mixed together, with no version tag. "
            "What can't you do now?",
            ["Run an offline evaluation first", "Give the new one a canary share", "Compare the versions on real questions"],
            answer=2,
            clue="To compare two versions, you need to know which trace came from which.",
            why="Tag every trace with its prompt version. Without the tag, you can't split real "
                "questions by version, so you can't compare them."),
    ],
}
