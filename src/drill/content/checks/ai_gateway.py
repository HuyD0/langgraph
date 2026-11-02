"""More Check questions for the AI gateway module (the first is in the lesson itself).

The last question of each lesson needs two things weighed at once, the way the engineer who builds and
runs the gateway has to: a named limit and its group, grants given to a group the app isn't in, a budget
and the tags it reads, a canary during an outage.
"""

from drill.content.model import ask

CHECKS = {
    "why_gateway": [
        ask("You are listing the gateway's requirements. Functional ones say what it must do. Non-functional ones "
            "say how well. Which line is non-functional?",
            ["Each team can make at most 1,000 calls a minute", "Apps can send a question to a model",
             "The platform team can add a new model"],
            answer=0,
            clue="Does the line add something the gateway can do, or set a bar for how well it does it?",
            why="The call limit says how well the gateway must work, and you can test it with a number. Sending a "
                "question and adding a model say what it must do, so they are functional."),
        ask("A security reviewer wants two things. Every call must name the app that made it. A leaked secret must "
            "stop working on its own. Which pair gives both?",
            ["A record of every call, and sign-ins that expire", "A spend total for the month, and one shared key",
             "A higher call limit, and a second key"],
            answer=0,
            clue="Which part answers \"who called\", and which makes a leak short-lived?",
            why="The gateway's record names the app behind every call. A sign-in that expires within the hour stops a "
                "leak on its own. A shared key does the opposite: it works for whoever holds it, until someone "
                "changes it."),
    ],
    "gateway_parts": [
        ask("The prod support app gets 429s. The usage table shows almost no traffic on "
            "`prod_ai.sales.support_chat`, but a lot on `dev_ai.sales.support_chat`. What is the likely cause?",
            ["The prod app's settings name the dev catalog", "The prod service's limit is set too low",
             "The prod app's sign-in has expired"],
            answer=0,
            clue="Which service is the traffic actually reaching?",
            why="The catalog, the first part of the name, picks the environment. The prod app is calling the dev "
                "copy, so it hits dev's limits and lands in dev's record. Fix the name in its settings."),
        ask("team-sales adds a summary app. It must use the same Azure OpenAI link as the support app, but with its "
            "own limits and its own record. What do you create?",
            ["A new model service for summary, on the same provider", "A new provider service, one for each app",
             "Nothing: both apps call prod_ai.sales.support_chat"],
            answer=0,
            clue="Which kind of service carries an app's limits, and which holds the provider link?",
            why="Limits and the record belong to the model service, so summary gets its own, like "
                "`prod_ai.sales.summary`. The provider link stays in one provider service that both point at, so "
                "there is still only one link to guard."),
    ],
    "sign_in_not_keys": [
        ask("Three agents share one service principal, so they sign in as one identity. One agent gets stuck in a "
            "loop overnight. Why is sharing worse than one identity each?",
            ["Its loop uses up the limit all three share", "Shared identities make answers slower",
             "The stuck agent can read more data"],
            answer=0,
            clue="Limits are set for each identity. Whose limit does the loop use up?",
            why="One identity means one shared limit, so the stuck agent uses it up and the other two get errors. The "
                "usage table also shows one name, so nobody can tell which agent spent the money."),
        ask("An agent answers Ana's questions about her team's tickets during the day. Every night it also writes a "
            "summary for the whole team. Which identity should it use for each?",
            ["Ana's access when she asks, its own identity at night",
             "Its own identity for both, with wide grants to be safe",
             "Ana's token for both, kept for the night run"],
            answer=0,
            clue="Whose work is each call: one person's, or nobody's in particular?",
            why="Ana's questions run with her access, through user authorization, so she never sees more than she "
                "may. The night summary is nobody's in particular, so the agent signs in as itself. A kept token "
                "would have expired within the hour anyway."),
    ],
    "who_may_call": [
        ask("An app had `CAN_QUERY`, the permission to call an old Model Serving endpoint. It now calls a Unity "
            "Gateway service and gets PERMISSION_DENIED. Why?",
            ["A Unity Gateway service checks EXECUTE", "CAN_QUERY expired when the service moved",
             "The app needs MANAGE on the service"],
            answer=0,
            clue="Where does each permission live: on the old endpoint, or in Unity Catalog?",
            why="`CAN_QUERY` is a Model Serving endpoint permission, and it doesn't carry over. A Unity Gateway "
                "service lives in Unity Catalog, so it checks `EXECUTE`, plus `USE CATALOG` and `USE SCHEMA` above it."),
        ask("All three grants for calling `prod_ai.sales.support_chat` go to grp-sales-dev-users. The support app "
            "signs in as sp-sales-chat-prod, which is not in that group. Can the app call the service?",
            ["No: grant the three to sp-sales-chat-prod too", "Yes: a group's grants cover every app",
             "Yes: the people who built it are in the group"],
            answer=0,
            clue="Who did the grants go to, and is the app one of them?",
            why="A grant reaches only the group's members, and the app's service principal isn't one. Until "
                "sp-sales-chat-prod gets the three grants too, every call it makes gets PERMISSION_DENIED."),
    ],
    "fair_limits": [
        ask("A service allows 1,000 requests and 100,000 tokens a minute. In one minute an app sends 200 big "
            "requests that add up to 150,000 tokens. What happens?",
            ["It gets 429s: the token limit runs out first", "Nothing: it is well under 1,000 requests",
             "The gateway raises the limit for that minute"],
            answer=0,
            clue="Check each limit on its own. Which one runs out first?",
            why="When both limits are set, the stricter one applies. 200 requests is well under 1,000, but 150,000 "
                "tokens is over 100,000, so the app gets 429s until the next minute."),
        ask("grp-sales shares 30,000 tokens a minute on a service capped at 100,000. Its member sp-sales-batch "
            "needs 60,000 at night. The rest of the group must keep their 30,000. What do you set?",
            ["A named limit of 60,000 for sp-sales-batch", "Raise grp-sales to 90,000 for everyone in it",
             "Move sp-sales-batch out of grp-sales"],
            answer=0,
            clue="Which change touches only the batch job's share?",
            why="A named service principal's own limit is used instead of its group's. So the batch job gets 60,000 "
                "and grp-sales keeps its 30,000, all under 100,000. A bigger group pool would let the batch job use "
                "it all."),
    ],
    "model_fails": [
        ask("support_chat has a fallback model at another provider. Nobody has run it on the team's test "
            "questions. Why does that matter?",
            ["It answers real users exactly when things go wrong", "It doesn't: fallbacks are only for outages",
             "Untested models cost more for each request"],
            answer=0,
            clue="When does the fallback actually answer?",
            why="A fallback answers only when the main model fails, so real users meet it at the worst moment. If "
                "its answers are worse, that is when you find out. Run it on the same test set as the main model "
                "first."),
        ask("support_chat splits requests: 90 in 100 to the trusted model, 10 in 100 to a new one. Both are at one "
            "provider, and a fallback is at another. The first provider goes down. Where do requests go?",
            ["All of them, to the fallback at the other provider", "All of them, to the new model at that provider",
             "None: the app shows errors until it is back"],
            answer=0,
            clue="Which models are still up?",
            why="The split only shares requests between the two main models, and both are down, so every request "
                "goes to the fallback. Pause the canary comparison: none of those answers came from the new model."),
    ],
    "who_spent_what": [
        ask("A sandbox budget is set to block calls at $2,000 a month. Spend reaches $2,040 before calls stop. Is "
            "the budget broken?",
            ["No: a block is close to real time, not exact", "Yes: a budget is an exact cap",
             "Yes: it should have sent an alert instead"],
            answer=0,
            clue="How quickly, and how exactly, does a budget see spend?",
            why="A budget blocks from a near real-time estimate, so a little spend can slip past, and calls already "
                "running finish. The billing records and the provider's invoice are the final word."),
        ask("team-sales adds a `project` request tag to every call. They want a budget that blocks the refunds "
            "project at $500 a month. Can a budget do that?",
            ["No: a budget filters on service tags, not request tags", "Yes: set the budget's filter to project: refunds",
             "Yes: a budget reads every tag on a usage row"],
            answer=0,
            clue="Which tags are set on the service, and which does the app add to each call?",
            why="Budgets pick services by their service tags. A request tag can split spend in the usage table, but "
                "it can't drive a block. Give refunds its own service with its own tags, or budget the whole service."),
    ],
}
