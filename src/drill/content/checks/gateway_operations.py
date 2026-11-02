"""More Check questions for the Run the gateway module (the first is in the lesson itself)."""

from drill.content.model import ask

CHECKS = {
    "ship_a_change": [
        ask("A new prompt version passed the quick smoke run on its pull request. That run uses a small set of test "
            "items. Is it ready to promote to prod?",
            ["No: the full frozen test set has to pass first", "Yes: the smoke run is the whole eval gate",
             "Yes, as soon as the canary has started"],
            answer=0,
            clue="The eval gate has two runs. How many has this change passed so far?",
            why="The smoke run is only the first of the gate's two runs. The full frozen test set still has to run, "
                "item by item against the champion, or a change tested on a few items reaches every user."),
        ask("One pull request changes the support prompt and also edits the judge's prompt. The judge is the model "
            "that grades the answers. The candidate wins 6 items to 2 and passes every must-pass item. Promote it?",
            ["No: the judge change needs its own pull request", "Yes: it wins 6 to 2 and passes every must-pass item",
             "Yes, once a required reviewer approves the deploy"],
            answer=0,
            clue="If the grader changed too, what does the 6 to 2 win really measure?",
            why="A new judge can move every score on its own, so the 6 to 2 win says nothing sure about the prompt. "
                "Put the judge change in its own pull request with its own review, then gate the prompt with the "
                "judge everyone agreed on."),
    ],
    "stop_it_fast": [
        ask("You disabled sp-sales-agent's service principal at 10:00. It kept calling the model until 10:40. "
            "What kept it working?",
            ["A sign-in token it already had", "Disabling waits for the next deploy",
             "Its rate limit was still 300 a minute"],
            answer=0,
            clue="Signing in gives the agent something with an expiry time. How long can it last?",
            why="A token already issued can keep working until it expires, up to an hour. That is why the agent's "
                "own rate limit and the deny policy come before disabling it in the list."),
        ask("sp-sales-agent runs on DurableAgentServer, which restarts runs a crash interrupted. You must stop it "
            "while 12 of its runs are half done. What do you do first?",
            ["Drain it: finish started runs, start no new ones", "Stop the Agent Runtime app straight away",
             "Restart the app so the runs begin again cleanly"],
            answer=0,
            clue="What does this server do with runs that were cut off halfway?",
            why="DurableAgentServer restarts interrupted runs, with no limit on attempts unless its recovery handler "
                "stops them. Draining lets the 12 runs finish and starts none, so after you stop the app, nothing is "
                "left to restart."),
    ],
    "nothing_drifted": [
        ask("A GRANT policy gives apps `EXECUTE`, the grant to call a service, on every service tagged "
            "`access_status = approved`. Yesterday someone removed that tag from `prod_ai.sales.support_chat` by "
            "hand. What happens to the apps that call it?",
            ["Apps that got access from the policy lose it", "Nothing changes until the next deploy",
             "The team budget stops counting its spend"],
            answer=0,
            clue="What must a service carry for the GRANT policy to cover it?",
            why="The policy gives EXECUTE only on services with the tag, so those apps lose access. Nothing warns "
                "anyone until their calls start getting PERMISSION_DENIED. Spend drops out of a budget when a service "
                "tag like team is missing, not a governed tag."),
        ask("This morning's audit found a grant on `prod_ai.sales.support_chat` that is not in the code. You need "
            "to know who made it, and when. Where do you look?",
            ["The audit log, for an `updatePermissions` event", "The usage table, for rows on that service",
             "The trace table, for that service's last prompts"],
            answer=0,
            clue="Which record keeps changes to grants, not calls?",
            why="`system.access.audit` records an `updatePermissions` event for every grant and revoke, with who "
                "made it and when. The usage table and the traces record calls, so they show who used the grant, "
                "not who gave it."),
    ],
    "one_request": [
        ask("`sp-sales-chat-prod` gets `EXECUTE` on `prod_ai.sales.support_chat` from a GRANT policy. Today its "
            "calls get PERMISSION_DENIED, and the audit log shows no grant change. What most likely changed?",
            ["The service lost its governed tag", "Its rate limit was cut to the lowest value",
             "The output policy blocked the answer"],
            answer=0,
            clue="PERMISSION_DENIED points at the grants. What does a GRANT policy depend on?",
            why="PERMISSION_DENIED comes from the grants, and no grant changed, so the policy's governed tag is the "
                "likely cause. A cut limit would give a 429, and a policy block would be a 200 that names its reason."),
        ask("You need to know how many calls `sp-sales-chat-prod` made to `prod_ai.sales.support_chat` "
            "yesterday. Which record do you query?",
            ["The usage table, which has rows for each call", "The audit log, which has an event for each call",
             "The team budget, which adds up each day's spend"],
            answer=0,
            clue="Which record is written for every call, with who called and which service?",
            why="Every call leaves rows in the usage table, `system.ai_gateway.usage`. One call can leave several "
                "rows, so count each request id once. An ordinary call leaves no audit log event, and a budget adds "
                "up money, not calls."),
    ],
}
