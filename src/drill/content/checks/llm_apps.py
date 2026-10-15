"""More Check questions for Building with LLMs (modules/llm_apps.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "fill_template": [
        ask("A teammate's prompt builder works fine, then crashes with a KeyError the day someone "
            "adds a JSON example to the prompt. What is the likely cause?",
            ["It fills the prompt with `str.format`", "The JSON example is too long", "The model can't read JSON"],
            answer=0,
            clue="Think about what Python's built-in filler does with every pair of curly braces it finds.",
            why="`str.format` treats every `{...}` as a placeholder, so the braces in the JSON example "
                "break it. Replace only your own placeholders instead."),
        ask("Your template is `Answer {question} using {docs}. Reply like {\"ok\": true}.` You fill in "
            "question and docs. What should the result still contain?",
            ["No curly braces anywhere", "The `{\"ok\": true}` example, untouched", "Both placeholders and the example"],
            answer=1,
            clue="Only the named slots you were given a value for get filled in.",
            why="Only `{question}` and `{docs}` were yours to fill. The JSON example is part of the prompt "
                "the model should see, so it stays as it was."),
    ],
    "resolve_prompt": [
        ask("Your app loads prompt version 4 by its number, not by an alias. You save a better "
            "version 5. How do you ship it?",
            ["Edit version 4 to match version 5", "Nothing: the app picks up the newest", "Change the code to 5 and redeploy"],
            answer=2,
            clue="The app points at one fixed number, not a nickname that can move.",
            why="A version number always means the same version, so a new prompt needs a code change and "
                "a redeploy. Loading an alias like `production` lets you just move the alias."),
        ask("You load the prompt `Answer {{question}}` from the MLflow Prompt Registry. You give it "
            "to LangChain without changing it. What goes wrong?",
            ["The question is filled in twice", "The placeholder is never filled in", "MLflow deletes the braces first"],
            answer=1,
            clue="In LangChain, what do doubled braces mean?",
            why="MLflow writes placeholders with double braces, but LangChain reads doubled braces as plain "
                "text. Convert it with `to_single_brace_format()` first."),
    ],
    "extract_code_block": [
        ask("Your code passes the model's whole reply straight to the JSON parser. Most days it works, "
            "but some days it crashes. What is the likely reason?",
            ["The reply is too long to parse", "The parser is slower on busy days", "Sometimes the model adds chatter"],
            answer=2,
            clue="Look at what the model sometimes puts around the JSON, even when you asked for JSON only.",
            why="Models often wrap the answer in a sentence or a code fence. Find the JSON you expect first, "
                "with a fallback when it isn't wrapped."),
        ask("You turned on structured output, so the model should reply in your exact JSON shape. "
            "Can you drop the check on what comes back?",
            ["Yes, the setting promises it", "No, still check the reply", "Yes, but only for short replies"],
            answer=1,
            clue="Parsing defensively means planning for a reply that isn't what you asked for.",
            why="Structured output makes the right shape much more likely, but you should still check "
                "what comes back and have a fallback."),
    ],
    "batch_items": [
        ask("You send 250 documents in batches of 100. Afterwards the index holds only 200. What went wrong?",
            ["The batch size of 100 is too big", "The API rejected 50 at random", "The last, smaller batch was lost"],
            answer=2,
            clue="250 doesn't split evenly into hundreds. Where did the leftovers go?",
            why="Two full batches make 200. The last 50 were a short batch that got skipped. Always keep "
                "the last batch, even when it's smaller."),
        ask("You send 5,000 texts one request at a time and it takes ages. A colleague suggests batches "
            "of 100. Why is that faster?",
            ["The model reads batches more carefully", "Fewer requests, so less fixed delay", "Batches don't count toward the limit"],
            answer=1,
            clue="Every request pays a wait before any work starts. How many times do you pay it?",
            why="Each request carries the same overhead. 50 requests pay it 50 times instead of 5,000."),
    ],
    "backoff_delays": [
        ask("A call fails with 401 Unauthorized because the API key is wrong. Your code retries it "
            "5 times with backoff. What's the problem?",
            ["A wrong key fails the same way each time", "Five retries is not enough for a 401", "The waits between tries are too short"],
            answer=0,
            clue="Will the key be any more right on the next try?",
            why="Only retry errors that can fix themselves. A wrong key fails every time, so fix the key "
                "instead of waiting."),
        ask("Your retries wait 1, 2, 4, 8, 16, 32, 64 seconds and keep going. What is missing?",
            ["A shorter first wait", "Waits that stay the same", "A cap so waits stop growing"],
            answer=2,
            clue="Doubling again and again gets very long very quickly.",
            why="Exponential backoff doubles each wait, so it needs a cap. With a cap of 30, the waits "
                "stop at 30 seconds instead of growing forever."),
    ],
    "parse_labels": [
        ask("You want to test that your code turns the reply \" Billing. \" into the label billing. "
            "What should the unit test use?",
            ["A fake model that returns that reply", "The real model, asked a billing question", "An eval set scored by a judge"],
            answer=0,
            clue="You're testing the cleaning code, not the model. You want the same reply on every run.",
            why="A fake reply never changes, so the test checks your parsing and never flakes."),
        ask("Your unit tests all pass with fake replies. Your manager asks: are the model's answers "
            "actually any good? What do you use?",
            ["More unit tests with fake replies", "Evals: examples with expected answers", "The same unit tests, run more often"],
            answer=1,
            clue="Fake replies test the code around the model. What tests the model itself?",
            why="Unit tests check your logic. Evals check the model's quality: example inputs with "
                "expected answers, plus a way to score them."),
    ],
}
