"""More Check questions for Troubleshooting a run (modules/troubleshooting.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "lookup_failed": [
        ask("A plan fails with `Cannot find service principal`, and the error path says `data`. A "
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
