"""More Check questions for Make and test a change (modules/changes.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "unchecked_fields": [
        ask("A plan suddenly wants to change a warehouse's size back to `2X-Small`, and nobody touched "
            "the warehouse. What do you look for first?",
            ["A misspelled stack setting", "A broken provider version", "A bug in Databricks"],
            answer=0,
            clue="2X-Small is what the variable block uses when nobody sets it.",
            why="A value going back to its default is the sign of a setting that never landed, "
                "often because its name doesn't match the variable."),
        ask("The same typo is in three places: a `.tfvars` file, a `-var` on the command line, and "
            "a `TF_VAR_` environment variable. Which one makes no sound at all?",
            ["The .tfvars file", "The -var on the command line", "The TF_VAR_ variable"],
            answer=2,
            clue="One gets a warning, one is an error. The third is the trap.",
            why="Terraform warns about an unknown name in a .tfvars file and stops on one in -var, "
                "but ignores an environment variable it doesn't know without a word."),
    ],
    "plan_saw_change": [
        ask("You merged a change to `foundation/network.tf`. The service stack's project root is "
            "`service/`. Why did no service run start?",
            ["The stack doesn't watch that folder", "The merge needs a second approval", "Spacelift waits until night"],
            answer=0,
            clue="Compare the folder you changed with the folder the stack watches.",
            why="A stack only starts for changes inside its project root, plus any extra paths it "
                "is told about. foundation/ isn't one of them."),
        ask("A plan starts with \"Objects have changed outside of Terraform\" about some tags, then "
            "says \"Plan: 0 to add, 0 to change, 0 to destroy.\" Will the apply change the tags?",
            ["Yes: the note lists a change", "No: the bottom line says nothing", "Only if you confirm twice"],
            answer=1,
            clue="Which line says what will actually happen?",
            why="The note only says what Terraform found when it looked. The bottom line, 0 to "
                "change, is what the apply will do."),
    ],
    "cheapest_check_first": [
        ask("Your rule should make every warehouse name lower case, but one comes out as "
            "`HR_weekly`. Which is the cheapest check that can catch it?",
            ["terraform validate", "A test with a mock provider", "The apply in DEV"],
            answer=1,
            clue="The name is valid text, just the wrong text. Which check tests your own rules?",
            why="validate only checks names and types. A test with a pretend provider can assert "
                "the name, in seconds, with no cloud."),
        ask("Right after an apply, you plan again. What should the second plan say if the change "
            "settled?",
            ["No changes", "The same changes again", "Plan: 1 to add"],
            answer=0,
            clue="If everything was applied, what is left to do?",
            why="A settled change leaves nothing to do, so the plan says No changes. Anything else "
                "means something keeps changing back."),
    ],
    "validation_rules": [
        ask("You want \"max_workers must be at least min_workers\" as a rule, and the stack runs "
            "Terraform 1.5. Where does the rule go?",
            ["A validation on max_workers", "A precondition in lifecycle", "A comment in the README"],
            answer=1,
            clue="Before 1.9, a validation may only look at its own variable.",
            why="On older versions a validation can't read a second variable. A precondition can, "
                "and it is checked when Terraform plans."),
        ask("Which error message would you rather see in a failed run?",
            ["\"Invalid value.\"", "\"Validation failed.\"", "\"Region must be eastus2 or westeurope.\""],
            answer=2,
            clue="Which one tells you how to fix it?",
            why="It names the setting and the values that would pass, so the person can fix it "
                "without reading the runbook."),
    ],
    "tests_seen_fail": [
        ask("Your rule allows 10 to 60. Your only test checks that 5 is rejected. Which mistake "
            "would your tests miss?",
            ["Changing 10 to 1", "Changing 60 to 600", "Deleting the rule"],
            answer=1,
            clue="Which limit does a test at 5 actually press against?",
            why="5 only tests the bottom limit. Moving the top to 600 still rejects 5, so nothing "
                "goes red. A test at 90 would catch it."),
        ask("A run block has no `command` line and no mock provider. What does it do?",
            ["A plan only, in seconds", "An apply that creates real things", "Nothing until you confirm"],
            answer=1,
            clue="What is the default command for a run block?",
            why="apply is the default, so without command = plan and a mock provider the test "
                "creates real resources."),
    ],
    "lock_every_platform": [
        ask("Your lock file was made on a Windows laptop from the company mirror. Where is the first "
            "run likely to fail on checksums?",
            ["On another Windows laptop", "On Spacelift's Linux worker", "Nowhere: checksums are shared"],
            answer=1,
            clue="Checksums are recorded per platform.",
            why="From a mirror, init records only the checksum for the platform it ran on. The "
                "Linux worker's files have a different fingerprint."),
        ask("CI runs `terraform init -lockfile=readonly`. A pull request needs a newer provider. "
            "How does the upgrade get in?",
            ["CI upgrades it by itself", "Commit a lock file from init -upgrade", "Delete the lock file in CI"],
            answer=1,
            clue="readonly never rewrites the file. Who changes it, then?",
            why="Run terraform init -upgrade, commit the new lock file, and let it be reviewed. "
                "CI then uses exactly what was approved."),
    ],
}
