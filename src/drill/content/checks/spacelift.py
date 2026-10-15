"""More Check questions for Spacelift (modules/spacelift.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "read_a_run": [
        ask("The plan policies said GO on a proposed run. Your manager asks: \"So someone approved "
            "it?\" What do you say?",
            ["Yes, GO means a reviewer signed off", "No, GO is an automatic check passing", "Yes, GO means it has been deployed"],
            answer=1,
            clue="Who, or what, gives a GO?",
            why="A GO comes from the plan policies, which run on their own. It's a check passing, "
                "not a person approving, and a proposed run deploys nothing."),
        ask("You push to a feature branch, and a run starts on the stack. The stack tracks `main`. "
            "What kind of run is it?",
            ["Tracked: it plans, then it applies", "None: a feature branch starts nothing", "Proposed: it plans and reports back"],
            answer=2,
            clue="Is the feature branch the one the stack tracks?",
            why="A push to any branch that isn't the stack's tracked branch starts a proposed run: "
                "it plans, reports to the pull request, and stops."),
    ],
    "runs_after": [
        ask("`workspace` waits for `network`. `billing` waits for nothing. `network` changes. Does "
            "`billing` run?",
            ["Yes, every stack runs on a change", "No, it doesn't depend on network", "Yes, but only after workspace"],
            answer=1,
            clue="Follow the waits from network. Does any path reach billing?",
            why="Only stacks downstream of the change run. Billing doesn't wait for network, directly "
                "or through another stack, so it stays still."),
        ask("`catalogs` waits for `workspace`, and `workspace` waits for `network`. Only "
            "`workspace` changes. Which stacks run?",
            ["network, workspace and catalogs", "Only workspace", "workspace, then catalogs"],
            answer=2,
            clue="Runs flow downstream from the change, not back up to what it waits for.",
            why="Network is upstream, so it doesn't run. Workspace runs because it changed, then "
                "catalogs, which waits for it."),
    ],
    "guard_destroys": [
        ask("It's Friday evening, and a tired reviewer only skims a plan. Does the plan policy "
            "still check it?",
            ["Yes, it runs on every run by itself", "Only if the reviewer turns it on", "No, it waits for a person to look"],
            answer=0,
            clue="Think about what makes a policy different from a person reviewing.",
            why="A plan policy runs automatically on every Spacelift run. It's code review that never "
                "gets tired, so a skim on a busy day doesn't skip it."),
        ask("Your team is writing its first plan policy. Which resources should it protect first?",
            ["Tags on every resource", "Storage accounts and workspaces", "Clusters people start by hand"],
            answer=1,
            clue="Start with what you can't get back once it's gone.",
            why="Begin with the resources you can't rebuild, like workspaces, storage accounts and "
                "metastores. Losing one of those is the real incident."),
    ],
    "plan_policy": [
        ask("A plan wants to open a storage account to the public internet. Nothing is being "
            "deleted. Which rule should catch it?",
            ["Never open things to the public internet", "Never destroy data you can't recreate", "Always tag every resource"],
            answer=0,
            clue="Nothing is lost here. Think about who could now reach the data.",
            why="Never opening workspaces or storage to the public internet is one of the first "
                "rules worth writing as code, because a leak is a real incident."),
        ask("Your team's rule \"check for deletes before approving\" lives on a wiki page. Last "
            "Friday a delete slipped through. What fixes that?",
            ["Make the wiki page easier to find", "Add a line to the review checklist", "Turn it into a plan policy"],
            answer=2,
            clue="Busy days are when people skip steps. What never gets tired?",
            why="Policy as code runs the rule on every plan, by itself. A rule that lives in "
                "people's heads, or on a wiki, gets skipped on busy days."),
    ],
}
