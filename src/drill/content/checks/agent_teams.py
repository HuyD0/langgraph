"""More Check questions for Agent teams (modules/agent_teams.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "need_a_team": [
        ask("Your task is always the same three steps in the same order: read a form, check it, "
            "file it. Which step on the ladder fits?",
            ["A fixed workflow", "One agent with tools", "A team of agents"],
            answer=0,
            clue="If you already know every step and its order, does anything need to choose?",
            why="Fixed steps in a set order are a workflow: your code runs them, and no agent has "
                "to decide what comes next."),
        ask("A research job splits into five parts that never need each other. One agent passes "
            "only 30 percent of your eval. What should you try?",
            ["Go back to a single model call", "Try a team, and check it on your eval", "Give the one agent a longer prompt"],
            answer=1,
            clue="Look at two things: does the work split, and how well does one agent do?",
            why="Independent parts and a low pass rate are when a team can help. The 45 percent hint "
                "is rough, so let your own eval make the call."),
    ],
    "one_writer": [
        ask("You split the work into a planner, a coder and a tester. Details keep going missing "
            "between them. How should you split it instead?",
            ["By what each agent needs to know", "By adding a fourth agent to check", "By giving each agent more tools"],
            answer=0,
            clue="Think about the information each piece of work depends on, not the job name.",
            why="Splitting by job title loses details at every hand-off. Splitting by context means "
                "each agent has what it needs for its own piece."),
        ask("A helper's brief just says \"look into refunds\". Two helpers end up running the same "
            "search. What was missing?",
            ["A bigger model for each helper", "A clear goal and what's out of scope", "More tools for each helper"],
            answer=1,
            clue="Did each helper know which part was someone else's job?",
            why="A good brief gives the goal, what's out of scope, what the report looks like and which "
                "tools to use. Vague briefs lead to the same work done twice."),
    ],
    "gather_results": [
        ask("In LangGraph, three workers write to the same \"results\" key, and that key has no "
            "reducer. What happens?",
            ["Only the last write is kept", "The lists are joined up anyway", "The run stops with an error"],
            answer=2,
            clue="Without a rule for combining updates, LangGraph won't guess.",
            why="Two workers writing the same plain key make the run fail. A reducer like "
                "operator.add joins their lists instead."),
        ask("Your fan-out workers each search a source, and each also saves notes straight into a "
            "shared table. What's the safer design?",
            ["Let the fastest worker write first", "Workers only search; one later step saves", "Each worker writes to its own table copy"],
            answer=1,
            clue="How many places should change the table?",
            why="Keep workers read-only. One step after the gather does the writing, so nothing gets "
                "quietly overwritten."),
    ],
    "handoff_kept": [
        ask("Before answering, your main agent retells each helper's report in its own words. The "
            "answers read well. What's the risk?",
            ["The helpers have to run all over again", "A key fact, like a refund date, drops out", "The answers become far too long to read"],
            answer=1,
            clue="Think of a game of telephone: what happens to a message passed along in new words?",
            why="The main agent sees only each helper's final message. Retelling it in new words can "
                "lose the one fact that mattered, even when the answer reads well."),
        ask("Your team's final answers score well with the grader, but users say small facts the "
            "helpers found are missing. What should you add?",
            ["Allow longer final answers", "Grade writing style more strictly", "Check which found facts reach the answer"],
            answer=2,
            clue="The answer reads well. The trouble is somewhere between the helper and the answer.",
            why="An answer can read well and still drop a fact a helper found. A hand-off check lists "
                "the facts and shows which ones fell out."),
    ],
    "checker_loop": [
        ask("Your fix loop has a cap of 3 rounds. After round 3, the checker still finds 2 issues. "
            "What should happen?",
            ["Do what you planned: warn, or ask a person", "Keep going until the checker passes", "Quietly return the last try as done"],
            answer=0,
            clue="A cap only helps if you planned what happens when you reach it.",
            why="Decide in advance what happens at the cap: return the best attempt with a warning, "
                "or hand it to a person. Don't loop forever or pretend it passed."),
        ask("The checker reads the agent's explanation of why its query is correct, and passes it. "
            "What would be a better check?",
            ["Ask the agent if it is sure", "Run the query and look at the result", "Ask for a longer explanation"],
            answer=1,
            clue="Trust evidence over what the agent says about its own work.",
            why="Where you can, the checker looks at real evidence, like running the query, instead "
                "of the agent's own explanation."),
    ],
    "dollars_per_success": [
        ask("A team passes 8 tasks and one agent passes 6. You want the price of each extra pass. "
            "What do you divide the extra dollars by?",
            ["8, all of the team's passes", "2, just the extra passes", "6, one agent's passes"],
            answer=1,
            clue="The team would get 6 of those anyway, even as one agent.",
            why="Only the 2 extra passes are what the team's extra money buys. Divide the extra cost "
                "by those 2, not by all 8."),
        ask("A report says the team passes 3 more tasks than one agent, and nothing else. What "
            "should sit next to that number?",
            ["How many helpers the team uses", "How long each helper's prompt is", "What each extra pass costs in dollars"],
            answer=2,
            clue="More passes sound good. Ask what you pay to get them.",
            why="Put the cost of each extra pass next to the pass rate every time. More spending "
                "often buys little extra accuracy."),
    ],
    "tokens_by_agent": [
        ask("Named spans show the researcher uses 40,000 tokens a run, the writer 6,000 and the "
            "checker 4,000. The researcher reads long documents. What do you try first?",
            ["A smaller model for the researcher, then rerun the eval", "A smaller model for every helper at once", "Remove the checker, since it costs least"],
            answer=0,
            clue="Start with the biggest, change one thing, and make sure quality holds.",
            why="Start with the biggest helper and try a smaller model for just that one. Keep the "
                "change only if your eval still passes."),
        ask("Your script adds up the writer's tokens, but it only counts the tokens sent to the "
            "model. What is missing from its tokens per agent?",
            ["The tokens used by the other helpers", "The tokens in your eval questions", "The tokens the model sent back"],
            answer=2,
            clue="Tokens travel two ways in every model call.",
            why="Tokens per agent are the input tokens you sent plus the output tokens that came "
                "back. Counting only one side gives too small a number."),
    ],
    "team_experiment": [
        ask("Your rule said the team must pass at least 1 more question in every 10 than one agent. "
            "It managed fewer, so someone wants to lower the rule to match. What's wrong?",
            ["It moves the goalposts after the result", "A gain that small is too hard to measure", "The rule should only be about cost"],
            answer=0,
            clue="When was the rule supposed to be written down?",
            why="The decision rule is written before any run, so a lucky result can't move the "
                "goalposts. Changing it now just picks a rule the team happens to meet."),
        ask("You test one agent, the team, and the team without its checker. What does that third "
            "design tell you?",
            ["How many tries each question needs", "Whether the team beats one agent", "What the checker adds to the team"],
            answer=2,
            clue="Compare the two teams: they differ in only one part.",
            why="This is an ablation: take one part out and see what changes. The gap between the "
                "two teams is what the checker buys you."),
    ],
}
