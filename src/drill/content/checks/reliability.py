"""More Check questions for Reliability (modules/reliability.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "plan_calls": [
        ask("Your app calls a model with no timeout. One day the model service hangs and never "
            "replies. What happens to the user?",
            ["They get a quick error", "They wait, maybe forever", "They get a cached answer"],
            answer=1,
            clue="Nothing tells the call when to give up.",
            why="A call with no timeout can wait forever. Set a timeout on every model and HTTP call."),
        ask("A request must finish within 5 seconds. Retrieval runs first. Then the model call still "
            "gets its own full 5-second timeout. What's wrong?",
            ["It should get only the time that's left", "Its timeout should be even longer", "Retrieval should have no timeout"],
            answer=0,
            clue="Some of the 5 seconds were already spent before the model call started.",
            why="Give the whole request a deadline and pass the remaining time down, so the model "
                "call doesn't plan on time that's already gone."),
    ],
    "circuit_breaker": [
        ask("The circuit breaker opened 5 minutes ago, and its cooldown has just ended. What happens "
            "next?",
            ["All calls go through again", "It stays open for good", "One trial call decides"],
            answer=2,
            clue="This in-between state is called half-open.",
            why="After the cooldown the breaker is half-open: one trial call decides whether it closes "
                "or opens again."),
        ask("While the breaker is open, a user asks a question that needs the model. What should "
            "the user get?",
            ["A long wait while it retries", "A fallback, like a cached answer", "An error page every time"],
            answer=1,
            clue="Calls are blocked, but the user still needs something useful.",
            why="An open breaker fails fast to a fallback, such as a cheaper model or a cached answer, "
                "instead of calling the broken service."),
    ],
    "burn_rate": [
        ask("Your SLO is 99 percent of requests succeeding. How big is your error budget?",
            ["1 in 100 requests can fail", "99 in 100 requests can fail", "No request is allowed to fail"],
            answer=0,
            clue="The budget is the part the target leaves over.",
            why="If 99 in 100 must succeed, the other 1 in 100 is the error budget."),
        ask("One error happened at 3 a.m. and the whole team got paged, though the error budget is "
            "barely touched. What should change?",
            ["Page for every error, even faster", "Turn off all alerts at night", "Alert on burn rate, not single errors"],
            answer=2,
            clue="Does one error put the target at risk?",
            why="Alert on how fast the budget is being used up. A single error with a low burn rate "
                "isn't worth waking anyone."),
    ],
    "answer_incident": [
        ask("The fix is ready, the SME says the answer is right, and the eval passes. Why send it to a "
            "small share of traffic first?",
            ["Real traffic shows what the eval missed", "A small share is cheaper to run for a week", "The eval is only a formality before launch"],
            answer=0,
            clue="Is the eval set the same as everything real users ask?",
            why="The eval covers the cases you thought of. A canary on real traffic catches the ones "
                "you didn't, while only a few people see them."),
        ask("Who should be able to switch the AI feature off in an emergency?",
            ["Someone named before launch", "Anyone who notices a bad answer", "Nobody: it must stay on no matter what"],
            answer=0,
            clue="In an incident, is there time to find out who can do it?",
            why="Agree before launch who flips the switch and who decides, usually the platform engineer "
                "and the product manager, so the harm stops in minutes."),
    ],
}
