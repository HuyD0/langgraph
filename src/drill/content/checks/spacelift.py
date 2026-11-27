"""More Check questions for Spacelift (modules/spacelift.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "read_a_run": [
        ask("The plan policies said GO on a proposed run. Your manager asks: \"So someone approved "
            "it?\" What do you say?",
            ["Yes, GO means a reviewer signed off", "No, GO is an automatic check passing", "Yes, GO means it has been deployed"],
            answer=1,
            clue="Who, or what, gives a GO?",
            why="Every GO is an automatic step passing, and the one after the policies line is the "
                "policies' result. None is a person approving, and a proposed run deploys nothing."),
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
    "policy_testing": [
        ask("A policy denies deleting a catalog. Which made-up plan would show whether it also "
            "catches a replacement?",
            ["A plan creating a schema", "A plan with a -/+ catalog", "An empty plan"],
            answer=1,
            clue="A replacement deletes the old one first.",
            why="A -/+ shows up as delete and create. A test with that plan tells you whether the "
                "rule treats a replacement as a delete."),
        ask("`opa test` reports a failing test. What do you check first?",
            ["Whether the rule or the test is wrong", "Whether OPA needs updating", "Whether to delete the test"],
            answer=0,
            clue="A failure means the two disagree. Which one is right?",
            why="Either the rule says the wrong thing or the test expects the wrong thing. Read "
                "both before changing either."),
    ],
    "who_confirms": [
        ask("A tracked run has sat at Unconfirmed for two days. The stack's approval policy needs "
            "two approvals and has one. What is the run waiting for?",
            ["A second approval", "A failed check to clear", "An admin to restart it"],
            answer=0,
            clue="Approve hasn't fired yet, and reject hasn't either. What does that leave?",
            why="Neither rule fires, so the answer is undecided and the run waits. One more approval "
                "lets approve fire."),
        ask("A stack has autodeploy on and no approval policy. A clean tracked run finishes its "
            "plan. Who has to click Confirm?",
            ["Nobody: it applies by itself", "The person who started it", "A second person on the team"],
            answer=0,
            clue="What does autodeploy skip?",
            why="Autodeploy skips the wait at Unconfirmed, so a clean plan applies with no click. "
                "If someone must look first, autodeploy has to be off."),
    ],
    "approved_task": [
        ask("Your team's approval policy approves every run that isn't a task. Someone starts a "
            "task to revoke a grant. Nobody else has reviewed it. What happens?",
            ["It waits for a review", "It runs straight away", "It fails at once"],
            answer=0,
            clue="Which approve rule could fire for a task?",
            why="The only approve rule skips tasks, so for this task nothing fires: undecided, and "
                "it waits until someone approves it."),
        ask("A task script revokes grants. What should it do when you run it without any "
            "options?",
            ["Show what it would revoke", "Revoke the grants at once", "Ask the AI if it is safe"],
            answer=0,
            clue="What makes a wrong list cost nothing?",
            why="A dry run by default shows what would change and changes nothing. You only apply "
                "once the list looks right, then read the result back."),
    ],
    "contexts_secrets": [
        ask("Ten stacks need the same Azure tenant id. Where do you put it?",
            ["In one context the ten stacks share", "On each of the ten stacks", "In the Terraform code of each stack"],
            answer=0,
            clue="Where does one change reach all ten?",
            why="A context holds settings many stacks share. Change it once and every stack it is "
                "attached to gets the new value."),
        ask("In the provider, you add a variable for the workspace URL and leave out `write_only`. "
            "What do you get?",
            ["A secret only runs can read", "A plain value anyone can read", "An error until you set it"],
            answer=0,
            clue="What does write_only default to?",
            why="write_only defaults to true, so the URL becomes a secret only runs and tasks can "
                "see. Set write_only = false for plain settings like a URL."),
    ],
    "admin_stack": [
        ask("A new team needs dev and prod stacks. With an admin stack, what do you change?",
            ["Add their environment files to the config", "Create four stacks in the web app", "Copy another team's stacks by hand"],
            answer=0,
            clue="What does the admin stack read to decide which stacks exist?",
            why="The admin stack makes stacks from the config, so new environment files are all it "
                "needs. Stacks made by hand would sit outside the code."),
        ask("Why does Spacelift advise making the very first management stack by hand?",
            ["Something has to exist to run the code", "Stacks made in code are slower", "The web app needs a stack first"],
            answer=0,
            clue="Code in Spacelift only runs inside a stack. Where would this code run?",
            why="The admin stack runs the code that makes the other stacks, so the first one can't "
                "make itself. Make it by hand, then adopt it into code with import."),
    ],
    "drift_detection": [
        ask("Someone changed a workspace folder's permissions by hand six months ago. Where "
            "can you still find who did it?",
            ["The Databricks audit log", "The Azure Activity Log", "The Terraform state file"],
            answer=0,
            clue="A folder's permissions live inside the workspace, not in Azure's own records.",
            why="Folder permissions are a Databricks change, recorded in the system.access.audit "
                "table, which keeps 395 days, about 13 months, by default. The Azure Activity Log "
                "covers Azure resources, and only for 90 days."),
        ask("A drift schedule is set on a stack, but no drift runs ever appear. The stack runs on "
            "public workers. Why?",
            ["Drift detection needs private workers", "The cron rule must use local time", "Drift runs only start on Mondays"],
            answer=0,
            clue="Where do drift detection runs have to run?",
            why="Spacelift's drift detection works only on private workers, the machines your own "
                "team runs. Move the stack to a private worker pool first."),
    ],
}
