"""More Check questions for the Run the gateway module (the first is in the lesson itself)."""

from drill.content.model import ask

CHECKS = {
    "ship_a_change": [
        ask("The candidate passed the quick smoke run on its pull request. Is it ready for prod?",
            ["No: the full frozen test set runs first", "Yes: the smoke run is the whole gate",
             "Yes, once the canary has started"],
            answer=0,
            clue="Which run uses every test item, the same ones each time?",
            why="The smoke run is a small, fast check on the pull request. Before promotion the full frozen test set "
                "runs, compared with the champion item by item."),
        ask("One pull request changes the support prompt and also edits the judge's prompt. The candidate wins 6 "
            "items to 2, and every must-pass item passes. Promote it?",
            ["No: split it, the judge change needs its own run", "Yes: it wins 6 to 2, must-pass items included",
             "Yes, once a required reviewer approves it"],
            answer=0,
            clue="Which part of that pull request could have moved every score on its own?",
            why="A new judge can move every score, so a win measured with it says nothing about the prompt. The judge "
                "change goes in its own pull request with its own run. Then the prompt is gated by the judge everyone "
                "agreed on."),
    ],
    "stop_it_fast": [
        ask("You disabled sp-sales-agent's service principal, but it kept calling for another 40 minutes. Why?",
            ["A token it already had kept working", "Its group still had EXECUTE on the service",
             "Its rate limit was still set to 300"],
            answer=0,
            clue="How long does a sign-in token last?",
            why="A token already issued can keep working until it expires, up to an hour. That is why the agent's own "
                "rate limit and the deny policy come first in the list."),
        ask("Why drain an agent on DurableAgentServer before you stop it?",
            ["So crash recovery has nothing to restart", "So its rate limit goes back to normal",
             "So its traces are deleted first"],
            answer=0,
            clue="What does that server do with runs a crash interrupted?",
            why="It restarts interrupted runs, with no limit on attempts unless the recovery handler stops it. "
                "Draining lets started runs finish and starts no new ones, so a stopped agent stays stopped."),
    ],
    "nothing_drifted": [
        ask("Someone removed the governed tag access_status = approved from a model service yesterday. What "
            "happens to the apps that call it?",
            ["Apps that got access by tag lose it", "Nothing until the next deploy", "Their spend stops being counted"],
            answer=0,
            clue="What does a GRANT policy match on?",
            why="A GRANT policy gives EXECUTE only to services that carry the tag, so access that came from the "
                "policy disappears with no error. The audit checks every service still has its tags."),
        ask("The audit found a grant on prod_ai.sales.support_chat that no code ever made. Where do you find who "
            "made it?",
            ["The audit log: an updatePermissions event", "The usage table: rows for that service",
             "The trace table: the last prompts"],
            answer=0,
            clue="Which record keeps changes to grants, not calls?",
            why="system.access.audit records an updatePermissions event for every grant and revoke, with who made "
                "it. The usage table and traces record calls, not changes."),
    ],
    "one_request": [
        ask("sp-sales-chat-prod gets EXECUTE on prod_ai.sales.support_chat from a GRANT policy. Today it gets "
            "PERMISSION_DENIED, and the audit log shows no updatePermissions event. What changed?",
            ["The service lost its governed tag", "Its rate limit was cut to the lowest value",
             "The output policy blocked the answer"],
            answer=0,
            clue="PERMISSION_DENIED means a grant is missing. What does a GRANT policy match on?",
            why="PERMISSION_DENIED comes from the grants. With no grant changed, look at the governed tag the policy "
                "matches. Without it, the policy stops giving EXECUTE, with no error of its own. A cut limit gives a "
                "429, and a policy block is a 200 that names its reason."),
        ask("An ordinary chat call goes through the gateway. Which of these records is NOT written for it?",
            ["An event in the audit log", "A row in the usage table", "A trace, when tracing is on"],
            answer=0,
            clue="Which record is about changes and tool calls?",
            why="Every call leaves a usage row, and a trace once tracing is on. The audit log records what happens "
                "around the service, like a grant or a tool call, not each model request."),
    ],
}
