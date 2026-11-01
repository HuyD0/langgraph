"""More Check questions for the AI gateway module (the first is in the lesson itself).

The last question of each lesson needs two things weighed at once, the way the engineer who builds and
runs the gateway has to: a named limit and its group, a grant set that calls but can't change, a budget
and the tags it reads, a canary during an outage.
"""

from drill.content.model import ask

CHECKS = {
    "why_gateway": [
        ask("Which of these is a non-functional requirement for the gateway?",
            ["Each team gets at most 50,000 tokens a minute", "Apps can send a question to a model",
             "The platform team can add a new model"],
            answer=0,
            clue="Which one says how well, with a number you could check?",
            why="It says how well, with a number you can check: that makes it non-functional. The other two say what "
                "the gateway must do, so they are functional."),
        ask("A security reviewer asks two things of the gateway: name the app behind every call, and make a leaked "
            "secret stop working on its own. Which pair answers both?",
            ["A usage record, and OAuth sign-ins that expire", "A bigger provider quota, and a backup model",
             "A monthly budget, and one shared service for all"],
            answer=0,
            clue="One asks for a record, the other for a sign-in that dies by itself.",
            why="The usage table names the user, app or agent behind every call, and an OAuth token dies within the "
                "hour, so a leak stops on its own. A quota, a backup model or a budget answers neither question."),
    ],
    "gateway_parts": [
        ask("An app works in dev, but in prod it still calls `dev_ai.sales.support_chat`. What's wrong?",
            ["It still names the dev catalog", "Prod has a different model provider", "The app's sign-in expired"],
            answer=0,
            clue="Which part of the name says the environment?",
            why="The catalog is the first part of the name, one for each environment. In prod the app should call "
                "`prod_ai.sales.support_chat`, read from its settings rather than written into the code."),
        ask("team-sales's summary app must use the same Azure OpenAI link as the support app, but with limits and a "
            "record of its own. What do you create?",
            ["A new model service for summary, on the same provider", "A new provider service, one for each app",
             "Nothing: both apps call prod_ai.sales.support_chat"],
            answer=0,
            clue="Which part carries an app's own limits and record, and which holds the provider link?",
            why="Limits and the record live on the model service, so summary needs one of its own, like "
                "prod_ai.sales.summary. The provider link is held once, in the provider service, and both model "
                "services point at it."),
    ],
    "sign_in_not_keys": [
        ask("Three agents share one service principal. One gets stuck in a loop. Why is that worse than if each had "
            "its own?",
            ["Its loop uses up the limit all three share", "Shared identities make answers slower",
             "The stuck agent can read more data"],
            answer=0,
            clue="Whose limit does the loop eat?",
            why="One shared identity means one shared limit, so the stuck agent starves the other two, and nobody can "
                "tell which one spent the money. An identity each gives each agent its own limit and its own line in "
                "the usage table."),
        ask("One agent answers Ana's questions about her team's tickets by day, and every night it writes a summary "
            "nobody asked for. Which identity should it use for each?",
            ["Ana's access when she asks, its own identity at night", "Its own identity for both, with wide grants to be safe",
             "Ana's token for both, kept for the night run"],
            answer=0,
            clue="Whose work is each call: one person's, or nobody's in particular?",
            why="A request for Ana runs with her access, through user authorization, so she never sees more than she "
                "may. The night run is nobody's in particular, so the agent signs in as itself, and a kept token would "
                "have expired within the hour anyway."),
    ],
    "who_may_call": [
        ask("An app had CAN QUERY on an old serving endpoint. It now calls a Unity Gateway service and gets "
            "PERMISSION_DENIED. Why?",
            ["A Unity Gateway service checks EXECUTE", "CAN QUERY expired when the service moved",
             "The app needs MANAGE on the service"],
            answer=0,
            clue="Which privilege does a Unity Gateway service check?",
            why="CAN QUERY belongs to Model Serving endpoints. A Unity Gateway service lives in Unity Catalog, so it "
                "checks EXECUTE, plus USE CATALOG and USE SCHEMA on the way down."),
        ask("sp-sales-chat-prod must be able to call prod_ai.sales.support_chat, and must never be able to change it. "
            "Which set of grants does exactly that?",
            ["USE CATALOG, USE SCHEMA and EXECUTE on the service", "USE CATALOG, USE SCHEMA and MANAGE on the service",
             "USE SCHEMA and EXECUTE on the service, nothing else"],
            answer=0,
            clue="One set is missing a level on the way down; one set gives too much.",
            why="Without USE CATALOG the call is refused at the first level, and MANAGE is the right to change the "
                "service, so the app could loosen its own limits. The three grants, with EXECUTE on the service, let "
                "it call and nothing more."),
    ],
    "fair_limits": [
        ask("A service allows 1,000 requests and 100,000 tokens a minute. In one minute an app sends 200 big requests "
            "that add up to 150,000 tokens. What happens?",
            ["It gets 429s: the token limit runs out first", "Nothing: it is well under 1,000 requests",
             "The gateway raises the limit for that minute"],
            answer=0,
            clue="Which limit runs out first?",
            why="When both are set, the stricter one applies. 200 requests is well under 1,000, but 150,000 tokens is "
                "over 100,000."),
        ask("grp-sales shares 30,000 tokens a minute, under a service ceiling of 100,000. sp-sales-batch, a member, "
            "needs 60,000 of its own at night, and the rest of the group must keep their 30,000. What do you set?",
            ["A named limit of 60,000 for sp-sales-batch", "Raise grp-sales to 90,000 for everyone in it",
             "Move sp-sales-batch out of grp-sales"],
            answer=0,
            clue="Which change touches only the batch job's slice?",
            why="A limit for a named service principal replaces its group's for that one caller, so the batch job gets "
                "60,000 while grp-sales keeps its shared 30,000, all under the service's 100,000. A bigger group pool "
                "lets the batch job eat the lot, and out of the group it drops to the default."),
    ],
    "model_fails": [
        ask("A fallback model at another provider has never been tested on your questions. Why does that matter?",
            ["It answers real users exactly when things go wrong", "It doesn't: fallbacks are only for outages",
             "Untested models cost more for each token"],
            answer=0,
            clue="When does the backup actually answer?",
            why="A fallback only answers during an outage, when everyone is already under pressure. If its answers are "
                "worse, that is when you find out. Test it on the same questions as the main model, before it is "
                "needed."),
        ask("support_chat sends 90 in 100 requests to the trusted model and 10 in 100 to a new one, both at the same "
            "provider, with a fallback at another provider. That provider has an outage. Where do requests go?",
            ["All of them, to the fallback at the other provider", "The 10 in 100 to the new model; the rest fail",
             "All of them, to the new model, until it is back"],
            answer=0,
            clue="Both main destinations sit at the provider that is down.",
            why="The split only chooses between the main destinations, and both are down, so every request falls "
                "through to the fallback. The canary comparison waits until the provider is back: none of those "
                "answers came from the new model."),
    ],
    "who_spent_what": [
        ask("A sandbox budget is set to block at $2,000. Spend reaches $2,040 before calls stop. Is the budget broken?",
            ["No: a block is close to real time, not exact", "Yes: a budget is an exact cap",
             "Yes: it should have sent an alert instead"],
            answer=0,
            clue="How exact is a block?",
            why="A Unity Gateway budget blocks from a near real-time estimate, so a little spend can slip past, and "
                "calls already running finish. The bill is the final word."),
        ask("team-sales adds a `project` request tag to every call and asks for a budget that blocks the refunds "
            "project at $500 a month. Can a budget do that?",
            ["No: a budget filters on service tags, not request tags", "Yes: set the budget's filter to project: refunds",
             "Yes: a budget reads every tag on a usage row"],
            answer=0,
            clue="Which tags are set on the service, and which does the app add to each call?",
            why="Budgets pick their services by service tags, so a project tag the app adds to each call can split "
                "spend in the usage table but can't drive a block. Give refunds its own service with its own tags, or "
                "set the budget on the whole service."),
    ],
}
