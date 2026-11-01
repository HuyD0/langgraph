"""More Check questions for the AI gateway module (the first is in the lesson itself)."""

from drill.content.model import ask

CHECKS = {
    "why_gateway": [
        ask("team-sales wants their app to call a model through the gateway. How should the app prove who it is?",
            ["It signs in with OAuth as its own service principal", "It sends the provider's API key with each call",
             "It borrows a developer's personal access token"],
            answer=0,
            clue="Which one expires on its own and names the app?",
            why="With OAuth the app gets a token that lasts about an hour and names the app, so the gateway knows who "
                "is calling and nothing long-lived sits in the app. The provider's key never leaves the gateway."),
        ask("Which of these is a non-functional requirement for the gateway?",
            ["Each team gets at most 50,000 tokens a minute", "Apps can send a question to a model",
             "The platform team can add a new model"],
            answer=0,
            clue="Which one says how well, with a number you could check?",
            why="It says how well, with a number you can check: that makes it non-functional. The other two say what "
                "the gateway must do, so they are functional."),
    ],
    "gateway_parts": [
        ask("Which kind of service holds the link to an outside provider like Azure OpenAI?",
            ["A model provider service", "A model service", "An MCP service"],
            answer=0,
            clue="Which name is about the provider?",
            why="A model provider service holds the link to the provider and how it signs in. Model services are what "
                "apps call, and MCP services hold tools."),
        ask("An app works in dev, but in prod it still calls `dev_ai.sales.support_chat`. What's wrong?",
            ["It still names the dev catalog", "Prod has a different model provider", "The app's sign-in expired"],
            answer=0,
            clue="Which part of the name says the environment?",
            why="The catalog is the first part of the name, one for each environment. In prod the app should call "
                "`prod_ai.sales.support_chat`, read from its settings rather than written into the code."),
    ],
    "sign_in_not_keys": [
        ask("The usage table shows `auth_mode` PAT for a nightly job. What should happen next?",
            ["Move it to OAuth as its own service principal", "Nothing: the job still works",
             "Give the job a PAT that lasts longer"],
            answer=0,
            clue="Which sign-in expires on its own and belongs to the job?",
            why="A PAT lives for months and belongs to one person. As its own service principal with OAuth, the job "
                "gets tokens that expire within the hour, and it keeps working when people move on."),
        ask("Three agents share one service principal. One gets stuck in a loop. Why is that worse than if each had "
            "its own?",
            ["Its loop uses up the limit all three share", "Shared identities make answers slower",
             "The stuck agent can read more data"],
            answer=0,
            clue="Whose limit does the loop eat?",
            why="One shared identity means one shared limit, so the stuck agent starves the other two, and nobody can "
                "tell which one spent the money. An identity each gives each agent its own limit and its own line in "
                "the usage table."),
    ],
    "who_may_call": [
        ask("Which privilege lets someone change a service's limits and guardrails?",
            ["MANAGE", "EXECUTE", "READ METADATA"],
            answer=0,
            clue="Which one is about changing it?",
            why="MANAGE changes a service and gives access to others, so callers never get it. EXECUTE only calls it, "
                "and READ METADATA only shows its settings."),
        ask("An app had CAN QUERY on an old serving endpoint. It now calls a Unity Gateway service and gets "
            "PERMISSION_DENIED. Why?",
            ["A Unity Gateway service checks EXECUTE", "CAN QUERY expired when the service moved",
             "The app needs MANAGE on the service"],
            answer=0,
            clue="Which privilege does a Unity Gateway service check?",
            why="CAN QUERY belongs to Model Serving endpoints. A Unity Gateway service lives in Unity Catalog, so it "
                "checks EXECUTE, plus USE CATALOG and USE SCHEMA on the way down."),
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
        ask("Ana has a limit of her own, 30,000 tokens a minute, and her group has 50,000. Which applies to Ana?",
            ["Her own 30,000", "The group's 50,000", "Both added up: 80,000"],
            answer=0,
            clue="A named person beats their group.",
            why="A limit for a named user or service principal is used instead of their group's. The service limit "
                "still caps them both."),
    ],
    "model_fails": [
        ask("What does a fallback do?",
            ["Tries the next model when the main one fails", "Sends some requests to a new model on purpose",
             "Blocks requests when spend is too high"],
            answer=0,
            clue="It only acts when something has already gone wrong.",
            why="A fallback is the backup list the gateway tries, in order, when the main model fails. Sending a share "
                "to a new model on purpose is a traffic split, and blocking on spend is a budget."),
        ask("A fallback model at another provider has never been tested on your questions. Why does that matter?",
            ["It answers real users exactly when things go wrong", "It doesn't: fallbacks are only for outages",
             "Untested models cost more for each token"],
            answer=0,
            clue="When does the backup actually answer?",
            why="A fallback only answers during an outage, when everyone is already under pressure. If its answers are "
                "worse, that is when you find out. Test it on the same questions as the main model, before it is "
                "needed."),
    ],
    "who_spent_what": [
        ask("Which column of the usage table would you group by to split one service's spend by project?",
            ["request_tags", "service_tags", "requester"],
            answer=0,
            clue="Which tags does the app add to each call?",
            why="Request tags are added by the app on each call, so they can split one service's spend by project or "
                "by end user. Service tags are the same for every request to that service."),
        ask("A sandbox budget is set to block at $2,000. Spend reaches $2,040 before calls stop. Is the budget broken?",
            ["No: a block is close to real time, not exact", "Yes: a budget is an exact cap",
             "Yes: it should have sent an alert instead"],
            answer=0,
            clue="How exact is a block?",
            why="A Unity Gateway budget blocks from a near real-time estimate, so a little spend can slip past, and "
                "calls already running finish. The bill is the final word."),
    ],
}
