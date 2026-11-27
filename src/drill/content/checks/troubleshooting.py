"""More Check questions for Troubleshooting a run (modules/troubleshooting.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "lookup_failed": [
        ask("A plan fails with `cannot find SP with name sp-sales-etl-uat`, and the error path says `data`. A "
            "teammate says Terraform should just create it. What's wrong with that?",
            ["Nothing: Terraform creates what's missing", "The SP must be added by hand in Databricks", "`data` means it only looks up what exists"],
            answer=2,
            clue="What does the word data in the error path tell you Terraform was trying to do?",
            why="`data` means a lookup of something that should already exist. Terraform was never "
                "going to create it, so you find which earlier stage isn't done."),
        ask("You're working out why yesterday's Service plan couldn't find an SP. Today, "
            "`service_principals.yml` on main declares it. What do you check before ticking off "
            "the declared stage?",
            ["Nothing: the file on main declares it", "The same file at the run's commit", "That the SP's name is in lower case"],
            answer=1,
            clue="The repo may have changed since that run. Which version of the file did the run read?",
            why="The run used its own commit, and main may have changed since. Check the file at "
                "that commit before you tick off any stage."),
    ],
    "error_kinds": [
        ask("A plan fails with `NOT_FOUND: Catalog sales does not exist`. The catalog is in the "
            "workspace, and you can see it. What do you suspect first?",
            ["The run can't see it, or reads another workspace", "Databricks lost the catalog overnight", "The catalog name needs capitals"],
            answer=0,
            clue="Not found can mean it isn't there, or that this identity can't see it there.",
            why="You can see it, so it exists. Either the run's identity has no right to see it, or the "
                "run points at another workspace. Check both before anything else."),
        ask("An apply fails with `ALREADY_EXISTS` for a schema. Nobody on your team made it. What "
            "do you do?",
            ["Find out who owns it before you touch it", "Import it, since the name matches", "Delete it and apply again"],
            answer=0,
            clue="Import is for things that are yours. Is this one?",
            why="If it's someone else's, importing it would hand it to your stack, and deleting it "
                "would break their work. Find the owner first, then import or pick another name."),
    ],
    "partial_apply": [
        ask("An apply made 6 things and failed on the 7th. A teammate says: \"Nothing changed, it "
            "failed.\" Are they right?",
            ["No: the 6 it made are real", "Yes: a failed apply undoes itself", "Yes, until someone confirms again"],
            answer=0,
            clue="Does Terraform roll back a failed apply?",
            why="Terraform never rolls back. The 6 things exist in Azure and in state until something "
                "changes them."),
        ask("After a partial apply and a fix, the plan wants to add 2 more things than you expected. "
            "The last run was killed. What do you check?",
            ["Whether those 2 already exist", "Whether the plan is out of date", "Whether Azure is having an outage"],
            answer=0,
            clue="A killed run may make things without saving them to state.",
            why="A killed run can make things it never saved. If those 2 are there, import them; "
                "applying would hit already exists."),
    ],
    "evidence_note": [
        ask("Your note to the platform owner ends with: \"Let me know what you think.\" What "
            "should it end with instead?",
            ["One question they can answer yes or no", "A list of everything you tried", "A link to the whole log"],
            answer=0,
            clue="What makes a reply quick?",
            why="A note gets a quick answer when it asks for one decision. Everything else in it is "
                "there to help them make it."),
        ask("You link `service_principals.yml` in your note. Which version do you link?",
            ["The file at the run's commit", "The file on main, as it is now", "A copy pasted into the note"],
            answer=0,
            clue="Which version did the run read?",
            why="The owner should see what the run read. Main may have changed since, and a pasted "
                "copy can't be checked."),
    ],
    "ai_unstuck": [
        ask("You want an AI assistant's help with a failed run. What should you paste in?",
            ["The whole log and the state file", "The first error and the run's commit", "Just \"why did my run fail?\""],
            answer=1,
            clue="Give what a person would need to help, and nothing secret.",
            why="A short excerpt of the first error, with the run, the repo and its commit, is what a "
                "person would need. Whole logs and state files can hold secrets."),
        ask("The assistant says: \"Just re-run the plan, the error will go away.\" What do you do?",
            ["Re-run it: the AI read every file", "Re-run it twice to be sure", "Hold off and find the cause first"],
            answer=2,
            clue="If the error disappears, does the reason it happened disappear too?",
            why="Re-running to make an error go away hides the cause. Treat the AI's idea as a lead, "
                "not a fix, and find out why it failed."),
    ],
}
