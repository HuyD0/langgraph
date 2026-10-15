"""More Check questions for Pricing and sizing (modules/pricing.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "cost_per_finished_task": [
        ask("You're pricing an HR ticket bot. You need to know how long it takes a person to check "
            "one answer. Who should give you that number?",
            ["The model's price list", "The business owner", "The POC's traces"],
            answer=1,
            clue="Who knows how the team works today, and what their time costs?",
            why="The business owner gives the hourly rate, how many answers get checked and how long a "
                "check takes. The price list only gives the token price."),
        ask("In a trial, 1 in 5 answers fails and has to be redone. A prompt fix halves the failures, "
            "with the same tokens. What happens to the cost per finished task?",
            ["It goes down: less rework to pay for", "It stays the same: tokens didn't change", "It goes up: fixes always cost more"],
            answer=0,
            clue="The cost per finished task has three parts, not just the model's bill.",
            why="Redoing failed answers is part of the cost. Fewer failures means less rework, so the "
                "cost per finished task drops even though the tokens are the same."),
    ],
    "run_tokens": [
        ask("You're about to price a new agent. A teammate has the token count of one test call. "
            "What should you price it from instead?",
            ["Whole runs on real tasks, from traces", "That one call, times the price list", "A plain chat with the same model"],
            answer=0,
            clue="One task is never just one call for an agent.",
            why="An agent makes many calls per task, and each one resends more. Price it from whole runs "
                "on real tasks, measured in the POC's traces."),
        ask("The POC measured 20 tasks. Easy ones took 3 steps, hard ones took 12. How should you "
            "report the tokens per task?",
            ["Only the easy count, the usual case", "A low, a typical and a high count", "Only the hardest, to be safe"],
            answer=1,
            clue="You won't know in advance whether an easy or a hard task arrives next.",
            why="Hard tasks take more steps, so give a low, typical and high count. One number hides how "
                "much a task can vary."),
    ],
    "total_cost": [
        ask("You're listing costs for a RAG assistant. Which one is paid once, not every month?",
            ["Tokens for each question", "Indexing all the documents at first", "Searching the vector index"],
            answer=1,
            clue="Most lines come back every month. Look for the one that happens only at the start.",
            why="The first indexing of all the documents is a one-off. Tokens and search come every "
                "month, for as long as the system runs."),
        ask("Each time the model or prompt changes, someone reruns the evals. Which group of costs "
            "does that belong to?",
            ["Build, paid once", "Run, paid every month", "Maintain, keeping it working"],
            answer=2,
            clue="It isn't part of building it, or of answering questions. It's about keeping it healthy.",
            why="Rerunning evals, updating prompts and being on call keep the system working, so they're "
                "Maintain costs, paid every month."),
    ],
    "payback_plan": [
        ask("The bot saves staff time, but the business owner says nobody will be hired less and no "
            "overtime is cut. What kind of saving is that?",
            ["A hard saving: it cuts the bill", "A soft saving: time, not money", "A fixed cost: it comes monthly"],
            answer=1,
            clue="Ask whether any money actually stops being spent.",
            why="A hard saving is real money, like fewer new hires or less overtime. Time freed up with "
                "no money saved is a soft saving, so it shouldn't count in the payback."),
        ask("The build costs more than you planned. Tasks a month and the saving per task stay the "
            "same. What changes?",
            ["Payback takes longer", "Break-even needs more tasks", "The monthly net goes down"],
            answer=0,
            clue="Which of the three numbers uses the build cost at all?",
            why="Payback is the build cost divided by the monthly net, so a bigger build takes longer to "
                "pay back. Break-even and the monthly net don't use the build cost."),
    ],
    "biggest_swing": [
        ask("You're doing a sensitivity analysis. A teammate moves the task count and the accuracy "
            "guess at the same time. What's the problem?",
            ["Nothing: two at a time is faster", "They should move every guess at once", "You can't tell which guess moved it"],
            answer=2,
            clue="A sensitivity analysis changes guesses in a particular way, and keeps the rest still.",
            why="Move one guess at a time and keep the others at their expected values. Move two and you "
                "can't tell which one caused the swing."),
        ask("Before building the whole HR bot, you want to know how often the AI answers right. "
            "What's a cheap way to measure that?",
            ["Try it on 50 past tickets labelled by hand", "Ask staff how good they think it will be", "Read the model maker's benchmark scores"],
            answer=0,
            clue="Use real tickets where you already know the right answer.",
            why="Running the prompt on past tickets labelled by hand measures accuracy on your own work. "
                "Opinions and general benchmarks don't tell you how it does on your tickets."),
    ],
    "peak_capacity": [
        ask("Your tokens in the busiest minute fit the Foundry deployment's per-minute limit. "
            "What else should you check?",
            ["The daily token total", "The gateway's rate limits too", "Nothing: that's the only limit"],
            answer=1,
            clue="A request passes through more than one place on its way to the model.",
            why="Check the busiest minute against every limit on the path: the deployment's tokens per "
                "minute and the gateway's rate limits. Either one can send back error 429."),
        ask("You worked out the average tasks a minute in the busiest hour. Why multiply that by a "
            "burst factor, like 3?",
            ["Each task is sent three times", "To leave room for three models", "Some minutes are far busier than others"],
            answer=2,
            clue="Even inside the busiest hour, requests don't arrive evenly.",
            why="The burst factor covers how much busier the busiest minute is than an average minute of "
                "that hour. Size for that minute, or users hit the limit."),
    ],
    "make_a_skill": [
        ask("You wrote a skill, but Claude never uses it when you ask it to assess an idea. Which part "
            "should you fix first?",
            ["The script that adds up costs", "The output format at the end", "The description: when to use it"],
            answer=2,
            clue="Claude reads only two things about every skill up front.",
            why="Claude decides whether to load a skill from its name and description. If the description "
                "doesn't say when to use it, the skill never runs."),
        ask("You want everyone on your project to get the skill in Claude Code. Where should the "
            "folder go?",
            ["In ~/.claude/skills/ in your home", "In the project's .claude/skills/", "Zipped and uploaded in Settings"],
            answer=1,
            clue="One place is just for you. The other travels with the project.",
            why="A project's .claude/skills/ folder is shared with everyone on the project. The folder in "
                "your home is just for you, and uploading in Settings is for claude.ai."),
    ],
}
