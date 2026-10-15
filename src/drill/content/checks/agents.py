"""More Check questions for Agents with LangGraph (modules/agents.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "run_agent": [
        ask("Your agent asks for a tool called \"weather\", but you never gave it one. "
            "What should your code do?",
            ["Stop the whole run with a crash", "Send back an error the model can read", "Skip it quietly and ask the model again"],
            answer=1,
            clue="The model can fix its own mistake, but only if it finds out what went wrong.",
            why="Turning the error into a message lets the model see the mistake and pick a real tool. "
                "A crash would end the whole run over one bad call."),
        ask("Your agent has looked up an order and checked the refund policy. It isn't stuck. "
            "What makes the loop stop on its own?",
            ["A tool sends back an error", "The model gives a final answer", "Every tool has been used once"],
            answer=1,
            clue="Look at the line in the example that says return.",
            why="The loop repeats until the model gives a final answer instead of picking a tool. "
                "The step limit is only there for when that never happens."),
    ],
    "trim_history": [
        ask("A chat has grown too long for the model, so some messages must go. Which ones should "
            "you drop first?",
            ["The system prompt, since the model already read it", "The oldest ones, but keep the system prompt", "The newest ones, since the model hasn't used them"],
            answer=1,
            clue="Recent messages matter most, and one message must always stay.",
            why="Always keep the instructions, then keep the newest messages that fit. The oldest "
                "messages are the ones to let go."),
        ask("A support chat has run for two hours. An early message holds the customer's order "
            "number, and you need to make room. How can you keep that detail?",
            ["Summarise the old messages instead of dropping them", "Keep only the last 10 messages of the chat", "Drop the system prompt to make more room"],
            answer=0,
            clue="Dropping isn't the only way to make old messages take less space.",
            why="Old messages can be summarised instead of dropped, so a short version of the "
                "important details stays in the chat."),
    ],
    "stale_claims": [
        ask("The agent remembers \"the office opens at 9\", saved from the sites page at version 7. "
            "The sites page is still at version 7. What can the agent do?",
            ["Use it, since the fact is still fresh", "Delete it, since it may be out of date", "Ask a model if the fact is still true"],
            answer=0,
            clue="Compare the number saved with the number now.",
            why="Matching versions mean the source hasn't changed since the fact was saved, so it counts "
                "as fresh. The check is plain code, with no model call."),
        ask("A fact came from something the user said in chat, so its source has no version to "
            "compare. How do you stop it going out of date without anyone noticing?",
            ["Delete it at the end of each chat", "Ask the user to confirm it every time", "Give it an expiry date"],
            answer=2,
            clue="With no version number to compare, what else could tell you it's getting old?",
            why="A fact whose source has no version can't be compared, so it gets an expiry date "
                "instead."),
    ],
    "fact_history": [
        ask("The office was in Leeds from day 1 to day 50. It has been in York from day 50, with no "
            "end day yet. Where was the office on day 50?",
            ["Leeds, since its fact ends that day", "York, since its fact starts that day", "Neither, since it was moving day"],
            answer=1,
            clue="In the worked example, look at what happened on the day Leeds ended.",
            why="On its `to` day a fact has already ended, and the new fact starts that same day. "
                "So on day 50 the office was in York."),
        ask("A customer asks you to forget everything about them. Your agent keeps their address "
            "facts with `from` and `to` days. What do you do?",
            ["Delete their facts for real", "Close each fact so it ends today", "Keep them, since history matters"],
            answer=0,
            clue="Remember the one exception to keeping the history.",
            why="Personal data is the exception: when a person asks to be forgotten, deleting wins "
                "over keeping history."),
    ],
    "tool_schema": [
        ask("Three teams on Databricks each wrote their own \"find customer\" tool inside their agent "
            "code, and nobody controls who can run them. What's a better home for it?",
            ["A longer system prompt in each agent", "One Unity Catalog function, shared by all", "A shared file in one team's code folder"],
            answer=1,
            clue="Look for a place that is governed, has permissions, and can be reused.",
            why="A Unity Catalog function is governed, permissioned and reusable, so every team uses "
                "one tool with clear rules about who can run it."),
        ask("A user writes \"Where is my parcel? My order is A-1042.\" The model decides to call "
            "`lookup_order`. What does it send to the tool?",
            ["order_id set to A-1042", "The user's whole message", "Nothing, the tool finds it"],
            answer=0,
            clue="Look at the parameters in the example: the inputs the tool takes.",
            why="The parameters list what the tool needs, and order_id is required. The model fills "
                "it in from the chat, so the tool gets just A-1042."),
    ],
    "tool_pairs": [
        ask("The model calls a search tool with id call_7. What must the result message you send "
            "back include?",
            ["The id call_7", "The name of the model", "The time the search ended"],
            answer=0,
            clue="Look at how the call and its result are linked in the worked example.",
            why="Each tool call gets an id, and its result must reference that id. Without the "
                "match, the API rejects the conversation."),
        ask("Your agent worked fine until you added code that trims old messages. Now the model "
            "API rejects some requests. What's the likely cause?",
            ["The trim kept too few messages", "The trim removed the system prompt", "The trim split a tool call from its result"],
            answer=2,
            clue="Every tool call needs something to match it. What could a trim break?",
            why="A call left without its result breaks the chat, and trimming history is where that "
                "happens most often."),
    ],
    "agent_scorecard": [
        ask("Your report works out cost per success using only the bills of the runs that "
            "succeeded. What does it miss?",
            ["The cost of the failed runs", "How many steps each run took", "Which model the agent used"],
            answer=0,
            clue="A run that fails still sends a bill.",
            why="Failed runs cost money too. Cost per success spreads the whole bill, failed runs "
                "included, over the runs that worked."),
        ask("You want a model to grade whether each agent run finished its task. What should you "
            "do before trusting its grades?",
            ["Use the same model the agent uses", "Run it twice on every single task", "Write a rubric, test it on human labels"],
            answer=2,
            clue="How would you know the grader's grades are right?",
            why="An LLM judge needs written grading rules, a rubric, and a check against a few human "
                "labels, so you know it grades the way a person would."),
    ],
    "pass_rates": [
        ask("The agent writes three drafts of a reply, and a person picks the best one. When does "
            "this task count as a success?",
            ["When at least one draft is good", "Only when all three drafts are good", "Only when the first draft is good"],
            answer=0,
            clue="The person only sends one draft.",
            why="When someone picks the best attempt, one good try is enough. That is the pass@k "
                "number: at least one try worked."),
        ask("Your dashboard runs each task once and shows 85 percent success, yet users say the agent "
            "often lets them down. What would show the problem?",
            ["Test it on many more tasks, one try each", "Run each task 5 times; count the ones that always pass", "Run each task twice and average the two scores"],
            answer=1,
            clue="Each user gets one try. Would the agent pass for every one of them?",
            why="One try per task hides how inconsistent an agent is. Counting only the tasks that "
                "pass every time (pass hat k) is closer to what users feel."),
    ],
    "tool_call_scores": [
        ask("The expected calls are lookup_order, then refund. The agent called lookup_order, "
            "refund, refund. How should the score treat the extra refund?",
            ["Count it as a wrong call", "Ignore it, as the first two match", "Count it as right, refund was expected"],
            answer=0,
            clue="A second refund could pay the customer twice.",
            why="Missing and extra calls count as wrong, because you divide by the longer list. An "
                "extra refund is real damage, not a free pass."),
        ask("The agent's calls differ a little from your reference. You want to know whether the "
            "order really ended up cancelled. What can you check?",
            ["The agent's last message to the user", "The number of tool calls it made", "The order's row in the database"],
            answer=2,
            clue="Look at what the task changed, not at what the agent said.",
            why="Checking the final state, like the database after the task, shows whether the job "
                "really got done, whichever calls the agent made."),
    ],
    "trajectory_match": [
        ask("An agent should only ever read data. It may skip some of its tools, but it must never "
            "call a tool that isn't on its list. Which mode fits?",
            ["subset", "superset", "strict"],
            answer=0,
            clue="The risk is a tool that isn't on the list at all.",
            why="Subset passes only if every tool called is on the expected list, so a surprise "
                "tool fails the test."),
        ask("A task must call lookup_order and lookup_customer, once each and nothing else. Either "
            "one can go first. Which mode fits?",
            ["strict", "superset", "unordered"],
            answer=2,
            clue="Strict would fail a run that did them the other way round.",
            why="Unordered passes when the same tools are called the same number of times, in any "
                "order. Superset would also let extra calls through."),
    ],
    "compare_designs": [
        ask("You test ReAct on 50 tasks, and plan-and-execute on 30 different, easier tasks. "
            "Plan-and-execute wins. What's wrong?",
            ["Nothing, plan-and-execute won", "The designs didn't run the same tasks", "The tasks should have been harder"],
            answer=1,
            clue="Would a race be fair if one runner had a shorter track?",
            why="Every design must run on the same tasks, the same number of times. Otherwise the "
                "comparison means nothing."),
        ask("Reading the traces, plan-and-execute fails on tasks where the first search turns up "
            "a surprise. Why is that likely?",
            ["It always makes too many tool calls", "It can't call the search tool itself", "It sticks to a plan made before the surprise"],
            answer=2,
            clue="When was the plan written, and what did the agent know then?",
            why="Plan-and-execute writes the plan first. That often saves tool calls, but it breaks "
                "when the plan turns out to be wrong."),
    ],
    "approval_run": [
        ask("Your agent may issue a refund, but only after a person says yes. Where should it "
            "call interrupt() to pause?",
            ["Just before the refund step", "Just after the refund step", "At the very end of the run"],
            answer=0,
            clue="The person has to answer while the refund can still be stopped.",
            why="The pause has to come before the risky action, so nothing happens until a person "
                "says yes. After the refund, it's too late to say no."),
        ask("Your agent paused at 5pm, waiting for a manager. The yes arrives the next morning. "
            "What tells LangGraph which saved run to carry on?",
            ["The time the pause started", "The thread_id it was saved under", "The manager's name on the reply"],
            answer=1,
            clue="The checkpointer keeps many paused runs. How does it tell them apart?",
            why="The checkpointer saves the state under a thread_id. Resuming with the same "
                "thread_id picks up exactly where that run stopped, even hours later."),
    ],
    "next_action": [
        ask("Round 1 of 3 fails with: NameError: name 'totl' is not defined. It's a typo in the "
            "code. What should the agent do next?",
            ["Ask a person: it's an environment error", "Read the error and write a fix", "Stop: this code can't be fixed"],
            answer=1,
            clue="Is the problem in the setup, or in the code the agent wrote?",
            why="A typo is a bug in the code, so a fix can help, and there are rounds left. "
                "Environment errors, like a missing package, are the ones to send to a person."),
        ask("The agent says \"Done, the table is updated\", and its last run ended with exit code 0. "
            "What should you do?",
            ["Check the table really has the new rows", "Trust it: exit code 0 means it worked", "Run the same code again to be sure"],
            answer=0,
            clue="Exit code 0 only tells you nothing crashed.",
            why="Agents often report success that never happened. Check the real result yourself, "
                "like reading the table."),
    ],
    "assemble_stream": [
        ask("Your app waits for the whole reply before showing anything, so users stare at a blank "
            "screen for 8 seconds. What would help most?",
            ["Stream the reply as it's written", "Use a longer system prompt", "Give the agent more tools"],
            answer=0,
            clue="People feel better when the first words show up quickly.",
            why="Streaming shows the answer as it's generated, so users see something in a few hundred "
                "milliseconds instead of waiting for all of it."),
        ask("A streamed reply arrives as three pieces: \"The ord\", \"er ship\", \"ped\". What should "
            "your code do with them?",
            ["Show only the newest piece on screen", "Join the pieces in order into one text", "Keep the first piece and drop the rest"],
            answer=1,
            clue="Each piece is only part of a word. Together they make the reply.",
            why="Text arrives in small pieces, so your code puts them back together in order to "
                "get the whole reply."),
    ],
}
