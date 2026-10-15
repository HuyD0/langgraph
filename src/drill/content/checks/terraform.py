"""More Check questions for Terraform foundations (modules/terraform.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "summarize_plan": [
        ask("A plan's summary says \"0 to add, 2 to change, 0 to destroy\". What will happen to "
            "those two resources?",
            ["They're updated in place", "They're destroyed and made again", "Two new ones are created"],
            answer=0,
            clue="Look at which of the three counters the 2 is in.",
            why="Change means update: the resources stay, and some of their settings change. A "
                "replacement would show up in both add and destroy."),
        ask("You're writing a check for pull requests that reads the plan. What should it read?",
            ["The text printed by terraform plan", "The JSON from terraform show -json", "The state file from the last apply"],
            answer=1,
            clue="A check wants the plan as data, not as words for a person to read.",
            why="`terraform show -json` gives the same plan as data, which is what Spacelift "
                "policies and PR checks read. The text is meant for people."),
    ],
    "find_replacements": [
        ask("A plan shows `-/+` next to the team's Azure Databricks workspace. What does approving "
            "it mean?",
            ["A new workspace, with a new URL and nothing in it", "The workspace gets a new tag, nothing more", "The workspace restarts and keeps its contents"],
            answer=0,
            clue="The mark has both a minus and a plus. What does each one do?",
            why="`-/+` is a replacement: Terraform destroys the workspace and creates a new one. "
                "That means a new URL and losing everything inside it."),
        ask("A plan has 40 changes. Your teammate checked the first ten and found no `-/+`. What "
            "do you do before approving?",
            ["Approve: ten is a fair sample", "Check the other thirty for `-/+` too", "Ask for the plan to be split up"],
            answer=1,
            clue="A single replacement anywhere in the plan can wipe a workspace.",
            why="You need to find every replacement before approving. One missed `-/+` on a "
                "workspace loses everything in it."),
    ],
    "lock_info": [
        ask("A run fails with a lock error. The lock info shows another run took the lock two "
            "minutes ago, and that run is still planning. What do you do?",
            ["Wait for that run to finish", "Run terraform force-unlock now", "Delete the state file and retry"],
            answer=0,
            clue="Is the run holding the lock dead, or still working?",
            why="The lock is doing its job: another run is using the state. Forcing it open would "
                "let two runs write at once and corrupt it."),
        ask("Two teammates start an apply on the same stack at the same moment, and there's no "
            "lock. What could go wrong?",
            ["Both applies just run more slowly", "Terraform keeps the newer code", "The state record could get corrupted"],
            answer=2,
            clue="Think of two people writing on the same page of a notebook at once.",
            why="State is Terraform's record of what it manages. Two runs writing it at once can "
                "corrupt it, which is why runs take a lock first."),
    ],
    "count_shift": [
        ask("Your team keeps a list of storage containers that will change over time. Why build "
            "them with `for_each` instead of `count`?",
            ["Each keeps its name when another is removed", "It creates the containers faster", "It stops anyone deleting a container"],
            answer=0,
            clue="With `count`, removing one shifts the ones after it. What if each had its own key?",
            why="`for_each` names each copy by its key, like `[\"silver\"]`. Removing one key leaves "
                "the other names alone, so nothing else is replaced."),
        ask("You're switching containers from `count` to `for_each`. Under `count`, gold was "
            "`lake[2]`. Which `moved` block keeps gold and its data?",
            ["from `lake[2]` to `lake[\"gold\"]`", "from `lake[\"gold\"]` to `lake[2]`", "from `lake[0]` to `lake[\"gold\"]`"],
            answer=0,
            clue="A `moved` block goes from the name Terraform knows today to the new one.",
            why="Gold's old name is `lake[2]` and its new one is `lake[\"gold\"]`. The block tells "
                "Terraform they're the same container, so it isn't deleted and made again."),
    ],
    "apply_order": [
        ask("Resource A uses a value from resource B, and B uses a value from A. What happens "
            "when you plan?",
            ["It creates A first, then B", "It stops with a Cycle error", "It creates both at the same time"],
            answer=1,
            clue="Each one is waiting for the other to exist first.",
            why="Terraform orders resources by what they need. If two wait on each other, no order "
                "works, so it stops with `Error: Cycle`."),
        ask("A storage container uses the name of the storage account it lives in. In what order "
            "does Terraform create them?",
            ["The container first, then the account", "Both at once, the order doesn't matter", "The account first, then the container"],
            answer=2,
            clue="Socks before shoes: which one needs the other to be there already?",
            why="Because the container refers to the account, the dependency graph puts the account "
                "first. Terraform creates the account, then the container."),
    ],
}
