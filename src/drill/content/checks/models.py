"""More Check questions for Choosing a model (modules/models.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "percentile": [
        ask("Model A: average 1 second, p95 2 seconds. Model B: average just under 1 second, "
            "p95 6 seconds. For a chat app, which will feel faster to users?",
            ["Model A: its p95 is much lower", "Model B: its average is lower", "Neither: the averages are close"],
            answer=0,
            clue="Averages hide the slow requests. Which number shows them?",
            why="Users notice the slow ones, so compare p95: 95 in 100 of A's answers are back within "
                "2 seconds, but B needs 6 seconds to cover the same 95."),
        ask("You time only the model call, and it takes 1 second. Users say answers take 5 seconds. "
            "What should you measure instead?",
            ["Only the model call, more often", "The whole request, start to end", "Only the slowest model call"],
            answer=1,
            clue="Retrieval and tools take time too, before and after the model.",
            why="Users wait for everything: retrieval, tools and model calls. A trace's total duration "
                "gives you that end-to-end latency."),
    ],
    "pareto_models": [
        ask("Model X scores higher on quality than model Y, but costs more. Y is cheaper and faster. "
            "Should either one be thrown out?",
            ["Yes, drop Y: lower quality", "Yes, drop X: it costs more", "No, each one wins on something"],
            answer=2,
            clue="A model is thrown out only if another is at least as good on all three.",
            why="Neither beats the other on everything, so both stay. It's a real trade-off, "
                "decided by what quality is worth to you."),
        ask("You tested model A on one eval set and model B on a different, easier set. B scored higher. "
            "What's wrong with this comparison?",
            ["Nothing, B simply scored higher", "They weren't tested the same way", "A should get a second try"],
            answer=1,
            clue="For a fair race, everyone runs the same track.",
            why="Run every model on the same eval set with the same judge. Otherwise a higher score "
                "may just mean an easier test."),
    ],
    "batch_leftovers": [
        ask("Your batch job on Foundry is 30 hours old and still running. 700 of its 1,000 requests "
            "are done. What do you do?",
            ["Wait: it will expire on its own", "Cancel it, keep the 700, send the 300 again", "Send all 1,000 again as a new job"],
            answer=1,
            clue="On Foundry, 24 hours is a target, not a deadline.",
            why="A late job keeps running until you cancel it. Cancelling returns the 700 that finished, "
                "and you pay only for those. Then send the 300 leftovers as a new job."),
        ask("The output file lists the answers in a different order from your requests. How do you "
            "match each answer to its request?",
            ["By position: line 1 is request 1", "By each line's custom_id", "By the length of each answer"],
            answer=1,
            clue="Each request carried its own label.",
            why="Answers come back in any order, so the custom_id on each line is the only safe way "
                "to find its request."),
    ],
    "better_option": [
        ask("Your manager says: pick the model that's cheapest per call, that saves money. "
            "What does that leave out?",
            ["How new each model is", "How many good answers each gives", "Which one has more users"],
            answer=1,
            clue="Money comes in from good answers, not just out through calls.",
            why="A cheaper model that succeeds less often can end up making less. Net value is what "
                "good answers earn, minus what the calls cost."),
        ask("Model B gets a few more answers right than model A. Those extra good answers earn $50 a "
            "month, but B's calls cost $500 a month more. Which should you pick?",
            ["Model A: B's extra cost is bigger", "Model B: it gets more answers right", "Neither: they come out the same"],
            answer=0,
            clue="Net value is what good answers earn, minus what the calls cost.",
            why="B's extra good answers earn less than its extra calls cost, "
                "so A leaves more money each month."),
    ],
}
