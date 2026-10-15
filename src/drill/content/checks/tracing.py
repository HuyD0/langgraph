"""More Check questions for Tracing and AgentOps (modules/tracing.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "summarize_by_tag": [
        ask("You want to know if the new prompt made answers slower. Every trace is tagged with its "
            "prompt version. What do you do?",
            ["Read the 10 newest traces one by one", "Group by prompt version, compare times", "Average the time across all traces"],
            answer=1,
            clue="The tag lets you split the traces into one pile per version.",
            why="Group the traces by their prompt version tag and average each pile's time. Then the "
                "two versions sit side by side."),
        ask("Your evaluation needs to find every retrieval step in your traces, but the spans don't "
            "say what kind of step they are. What should you add?",
            ["The model name on each trace", "A longer name for each span", "A RETRIEVER type on those spans"],
            answer=2,
            clue="Spans can be marked with the kind of step they are.",
            why="Marking spans with a type like RETRIEVER, TOOL or CHAT_MODEL lets evaluation and "
                "analysis find them."),
    ],
    "slowest_chain": [
        ask("A run took 9 seconds. Its children took: plan 1 second, search tool 7 seconds, write "
            "1 second. Where do you look next?",
            ["Inside the search tool span", "Inside the plan span", "At the write step's prompt"],
            answer=0,
            clue="Keep following the slowest child down.",
            why="The search tool is the slowest child, so it's on the critical path. Open it and keep "
                "following its slowest child."),
        ask("Your agent team has a planner, a researcher and a writer, each traced under its own name. "
            "Runs are slow. How do you find which helper held things up?",
            ["Count how many spans each helper made", "Compare how long each helper's reply is", "Follow the slowest child from the top"],
            answer=2,
            clue="The tree has one span per helper, and each span has a time.",
            why="Start at the top span and follow the slowest child. It leads to the helper, and then "
                "the tool, that held up the run."),
    ],
    "trace_table_row": [
        ask("You've turned 2,000 traces into rows of numbers. Which runs should you open and read "
            "first?",
            ["The ones with the fewest tokens", "The ones with many steps or tool errors", "The first 20 rows in the table"],
            answer=1,
            clue="Look for rows that stand out as troubled.",
            why="Many steps or many tool errors point at runs that went wrong. Sort by those and read "
                "the top ones."),
        ask("In one run's row, the biggest prompt is close to the model's context window. What is "
            "that warning you about?",
            ["The run nearly ran out of room", "The run made too many tool calls", "The run cost less than usual"],
            answer=0,
            clue="The context window is the most a model can read in one call.",
            why="The biggest prompt shows how close a run came to filling the context window. Near "
                "the limit, the next call may not fit."),
    ],
    "context_fill": [
        ask("Each call in a long run reads more than the last. Call 12 is at 85 percent of the "
            "window, and your line is 80 percent. What should happen?",
            ["Keep going until it hits the limit", "Switch to a model with a bigger window", "Clean up, like clearing old tool results"],
            answer=2,
            clue="The line is there so you act before the run hits the limit.",
            why="Once a call passes the line, clean up: clear old tool results or summarise, before "
                "the run hits the limit."),
        ask("Your prompt puts the question at the very top, followed by 50 retrieved chunks. "
            "Which change is worth trying first?",
            ["Put the question after the chunks", "Add more chunks so nothing is missed", "Send the chunks in a random order"],
            answer=0,
            clue="Models pay the most attention near the end of the prompt.",
            why="Putting the question after the retrieved text puts it where models pay most attention. "
                "Fewer, better chunks can help too."),
    ],
    "summary_recall": [
        ask("Your agent's context is getting full on long runs. Which fix should you try first?",
            ["Summarise everything into one line", "Clear old tool results, keep a note", "Switch off the tools for the run"],
            answer=1,
            clue="Start with the cheapest fix, the one that leaves the conversation itself alone.",
            why="Clearing old tool results, while keeping a note that each tool ran, is the cheap fix. "
                "Summarise only if runs are still too long."),
        ask("Summary prompt A makes summaries half as long as prompt B. With prompt B, the agent "
            "finishes more of its tasks. Which prompt is better?",
            ["A, because it saves more room", "Neither, summaries are always vague", "B, because the agent still finishes"],
            answer=2,
            clue="What matters is whether the agent can still do its job.",
            why="Judge a summary by whether the agent can still finish the task, not by how short "
                "it is."),
    ],
    "detect_loop": [
        ask("Your LangGraph agent got stuck and ran for hours before it stopped. You never set "
            "recursion_limit. What should you do?",
            ["Leave the default, it stops in time", "Pass your own small limit, like 25", "Set it higher so the run can finish"],
            answer=1,
            clue="The default limit is in the thousands.",
            why="The default allows over 10,000 steps, far too many to stop a stuck agent early. "
                "Always pass a small limit like 25."),
        ask("Your agent uses up its token cap halfway through a task, and the guardrail stops it. "
            "What should the guardrail also do?",
            ["Restart the run from the beginning", "Raise the cap and carry on quietly", "Tell the model why it was stopped"],
            answer=2,
            clue="The model is still in the conversation after the stop. What does it need to know?",
            why="Production guardrails cap steps, tokens and time, and tell the model why it was "
                "stopped, so the stop isn't a silent cut."),
    ],
    "failure_counts": [
        ask("Two people label failed traces. One writes \"looped\", the other writes \"kept "
            "repeating\", for the same problem. What fixes this?",
            ["Let each person count their own", "Use longer, more detailed labels", "Agree on a fixed list of labels"],
            answer=2,
            clue="The same problem should always get the same name.",
            why="A fixed list of labels, like the MAST taxonomy, means the same problem always gets "
                "the same name, so the counts add up."),
        ask("You labelled 50 failed traces by hand. Now you want an LLM judge to label the next 500. "
            "What must you check first?",
            ["Its labels match yours on the 50", "It labels faster than a person", "It uses more labels than you did"],
            answer=0,
            clue="You already have a set of labels you trust.",
            why="A judge can help label more only once its labels match yours. Compare it with your "
                "hand-labelled batch first."),
    ],
}
