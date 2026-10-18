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
    "embedding_cost": [
        ask("A RAG app gets 300,000 questions a month of 25 tokens each, and embeddings cost $0.02 per "
            "million tokens. What do the questions cost to embed each month?",
            ["$0.15", "$1.50", "$150"],
            answer=0,
            clue="Count the tokens first, then use the price per million.",
            why="300,000 times 25 = 7,500,000 tokens, times $0.02 divided by 1,000,000 = $0.15. Embedding is cheap; "
                "the search service that holds the vectors is usually the bigger line."),
        ask("Which embedding cost is easiest to forget when you plan a RAG app?",
            ["Embedding everything again after a model change", "Embedding the documents the first time", "Embedding new documents each month"],
            answer=0,
            clue="Which one only happens if something changes later?",
            why="Vectors from two models can't be compared, so a new embedding model means embedding "
                "every document again. Put that one-off in the plan before anyone swaps the model."),
    ],
    "vector_storage": [
        ask("You switch from 1,536 to 3,072 dimensions for the same 5 million chunks. What happens to "
            "the space the vectors take?",
            ["It doubles", "It stays the same", "It halves"],
            answer=0,
            clue="Which number in vectors times dimensions times 4 bytes changed?",
            why="5,000,000 times 1,536 times 4 bytes is about 30.7 GB; with 3,072 dimensions it is about "
                "61.4 GB, twice as much, and it may need another unit."),
        ask("Nobody has searched your Databricks AI Search endpoint for a month. What does it cost?",
            ["It still bills every hour it exists", "Nothing, because nobody searched", "Only the space the vectors take"],
            answer=0,
            clue="Is the endpoint billed for searches, or for being there?",
            why="Endpoints are billed by the unit per hour while they exist, used or not. Delete "
                "the ones nobody uses."),
    ],
    "paid_tools": [
        ask("You need the text, not the tables, from 50,000 scanned pages. Read costs $1.50 per 1,000 "
            "pages and Layout $10. What do you pay with the right one?",
            ["$75", "$500", "$7.50"],
            answer=0,
            clue="Text only needs Read. Then pages times price divided by 1,000.",
            why="50,000 times $1.50 divided by 1,000 = $75. Layout would be $500 for tables you don't need."),
        ask("An agent's design says one web search per question, but the traces show 4. What happens "
            "to the search bill?",
            ["It is 4 times the plan", "It stays as planned", "It is a quarter of the plan"],
            answer=0,
            clue="The bill counts searches, not questions.",
            why="Each search is billed, so 4 searches per question cost 4 times the plan. Take calls "
                "per task from traces, and cap them."),
    ],
    "find_the_price": [
        ask("An embedding model costs $0.02 per million tokens in a Global deployment and $0.022 in one "
            "region. Why might you still pick the region?",
            ["Your data must stay in that region", "One region is always faster", "Global prices change every day"],
            answer=0,
            clue="Where can a Global deployment process your data?",
            why="A Global deployment can process data in any region. If your rules say data stays in "
                "one place, the extra 10 percent pays for that."),
        ask("Where do you look first for what your AI feature really cost last month on Databricks?",
            ["The system.billing.usage table", "The pricing calculator", "The model's documentation"],
            answer=0,
            clue="Which one shows what was billed, not what would be?",
            why="The calculator and the docs give estimates and list prices. The billing table shows "
                "what you were actually charged."),
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
        ask("You're doing a sensitivity analysis on the HR plan. A teammate moves the task count and "
            "how often the AI is right at the same time. What's the problem?",
            ["Nothing: two at a time is faster", "They should move every guess at once", "You can't tell which guess moved it"],
            answer=2,
            clue="A sensitivity analysis changes guesses in a particular way, and keeps the rest still.",
            why="Move one guess at a time and keep the others at their expected values. Move two and you "
                "can't tell which one caused the swing."),
        ask("In the HR plan, how often the AI is right swings the value from $11,000 to $29,900. "
            "Before building the whole bot, what's a cheap way to measure it?",
            ["Try it on 50 past tickets labelled by hand", "Ask staff how good they think it will be", "Read the model maker's benchmark scores"],
            answer=0,
            clue="Use real work where somebody already knows the correct reply.",
            why="Running the prompt on past tickets labelled by hand shows how often it is right on your own "
                "work. Opinions and general benchmarks don't tell you how it does on your tickets."),
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
    "deployment_types": [
        ask("A new model is out, but only as Global Standard so far. Your data must stay in the EU. What do you do?",
            ["Wait for it in the EU Data Zone", "Use Global: it is only a test", "Use Global, then delete the data"],
            answer=0,
            clue="Where may a Global deployment process your requests?",
            why="Global may process requests in any region, which your rules forbid, even for a test. New "
                "models often reach Data Zone and Regional later, so wait or use an allowed model."),
        ask("Global Standard costs $2.00 per million input tokens and Data Zone $2.20. Your app sends 500 "
            "million input tokens a month. What does Data Zone add?",
            ["$100 a month", "$10 a month", "$1,000 a month"],
            answer=0,
            clue="The difference per million, times how many millions.",
            why="$2.20 minus $2.00 is $0.20 per million, and 500 times $0.20 = $100 a month."),
    ],
    "ptu_or_paygo": [
        ask("Your PTU deployment sits unused all weekend. What do you pay for those hours?",
            ["The full hourly price", "Nothing, because it was idle", "Half the hourly price"],
            answer=0,
            clue="What are PTUs billed for: tokens, or hours?",
            why="PTUs are billed every hour the deployment exists, used or not. Only deleting the "
                "deployment stops the bill."),
        ask("Your PTU deployment is full at the busiest minute. With spillover on, what happens to the "
            "extra requests?",
            ["They go to a pay-per-token deployment", "They fail with error 429", "They wait for the next hour"],
            answer=0,
            clue="Spillover sends overflow somewhere instead of failing it.",
            why="Spillover routes the overflow to a standard pay-per-token deployment in the same resource, "
                "so users get answers, at pay-per-token prices."),
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
