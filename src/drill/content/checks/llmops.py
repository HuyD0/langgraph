"""More Check questions for LLMOps (modules/llmops.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "token_cost": [
        ask("After a prompt change, a feature's answers are three times longer. The questions are "
            "the same length as before. What happens to the cost?",
            ["It stays the same, inputs didn't change", "It rises a lot, output costs more", "It drops, long answers need fewer calls"],
            answer=1,
            clue="Which kind of token went up, and which kind usually costs more?",
            why="Output tokens usually cost several times more than input tokens, so much longer "
                "answers raise the bill a lot."),
        ask("The bill jumped last month. You only track one total for the whole company. What's the "
            "problem?",
            ["The total is probably counted wrong", "Bills often jump for no reason", "You can't see which feature caused it"],
            answer=2,
            clue="When a bill jumps, you want to know where the extra came from.",
            why="Tracking cost per model, per feature and per user from day one shows why the bill "
                "jumped. One total can't."),
    ],
    "estimate_vs_actual": [
        ask("You flag projects more than 20 percent over plan. A big project is $3,000 over, which "
            "is 10 percent of its plan. Do you flag it?",
            ["Yes, $3,000 is a lot of money", "No, it's only 10 percent over", "Yes, any project over plan"],
            answer=1,
            clue="The margin is a share of the estimate, not a dollar amount.",
            why="The flag is set on percent over. 10 percent is under the 20 percent margin, so it "
                "isn't flagged, however big the dollar amount looks."),
        ask("Three projects share one model service. The bill is high, but you can't tell which "
            "project sent which requests. What's missing?",
            ["A request tag on each request", "A bigger monthly budget", "A separate bill for each user"],
            answer=0,
            clue="Each request needs a label saying where it came from.",
            why="A request tag on each request lets the usage table show which project used which "
                "tokens."),
    ],
    "cache_hits": [
        ask("Your LRU cache holds 3 prompts and is full. A was last used an hour ago, B a minute ago, "
            "C ten minutes ago. A new prompt comes in. Which is removed?",
            ["B, the most recent one", "C, the one in the middle", "A, unused for the longest"],
            answer=2,
            clue="LRU stands for least recently used.",
            why="LRU removes whatever hasn't been used for the longest time, and that's A."),
        ask("Half of your support questions are the same few, asked again and again. What does "
            "adding a cache give you?",
            ["Cheaper, faster answers on repeats", "Better answers to new questions", "Longer answers to every question"],
            answer=0,
            clue="On a repeat, does the model need to be called at all?",
            why="A cache returns a stored answer instead of calling the model again, which saves "
                "money and time."),
    ],
    "prompt_cache": [
        ask("Your prompt's fixed start is 700 tokens. On a GPT model the cache never hits, but on "
            "Claude Sonnet 5.5 the same prompt does. Why?",
            ["GPT models never cache prompts", "Each model has its own minimum length", "Claude also caches the question"],
            answer=1,
            clue="A start shorter than the model's minimum is never cached.",
            why="700 tokens is enough for Claude 5.5 (512) but too short for GPT (1,024). Look up the "
                "minimum for the model you use."),
        ask("Learners ask about the same lesson about once a day. The cached start lasts about 5 "
            "minutes. What hit rate do you expect?",
            ["High: the start is the same", "Near zero: the cache has gone", "About half of the calls"],
            answer=1,
            clue="How long does the cache keep a start nobody uses?",
            why="The cache forgets a start after a few minutes without use. Calls a day apart always "
                "miss, however identical the start."),
    ],
}
