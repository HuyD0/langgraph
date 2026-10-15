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
    "variables_outputs": [
        ask("You want one workspace module to build both dev and prod. What should change between "
            "the two uses?",
            ["Only the values you pass in", "A copy of the module for each", "The resources inside it"],
            answer=0,
            clue="A module is like a recipe. What changes when you cook it twice for different people?",
            why="You hand a module values through variables, so the same code builds dev and prod. "
                "Only the values change."),
        ask("Your root code has `host = module.workspace.workspace_url`. Where does that value "
            "come from?",
            ["A variable you passed into the module", "An output the module hands back", "A resource you made in the root"],
            answer=1,
            clue="Read it as module, then its name, then what it gives back.",
            why="`module.<name>.<output>` reads one of the module's outputs: the values it chooses to "
                "hand back to the code that called it."),
    ],
    "import_existing": [
        ask("You add an import block for a storage account made by hand, and plan. What should "
            "the plan's summary say?",
            ["1 to add", "1 to import", "1 to destroy"],
            answer=1,
            clue="Nothing new is being made. Terraform is taking over something that already exists.",
            why="With an import block, Terraform adopts the existing account into its state. The plan "
                "says \"1 to import\" and nothing new is created."),
        ask("Your import plan also says it will change the account's settings. You only meant to "
            "adopt it. What do you do?",
            ["Apply it: changes are harmless", "Remove the import block", "Fix the code to match it first"],
            answer=2,
            clue="Where does the plan's idea of how the account should look come from?",
            why="If the code doesn't match the real account, the plan changes it to match the code. "
                "Adjust the code until the import changes nothing."),
    ],
    "moved_blocks": [
        ask("You renamed a cluster in the code and the plan says: destroy the old one, create a "
            "new one. What should you add?",
            ["A moved block from old to new", "A second copy of the cluster", "An import block for the old one"],
            answer=0,
            clue="You want Terraform to know it's the same cluster, just with a new name.",
            why="A moved block tells Terraform the old address and the new one are the same thing, "
                "so it updates the name in its state and destroys nothing."),
        ask("Dev has applied your rename, but prod hasn't yet. A teammate wants to delete the moved "
            "block now. What's the risk?",
            ["None: the rename is finished", "Prod destroys and recreates it", "Dev loses the cluster"],
            answer=1,
            clue="Which environment still needs to be told that the old name and the new name match?",
            why="An environment that hasn't applied the rename still needs the moved block. Without "
                "it, that plan destroys the old cluster and creates a new one."),
    ],
    "provider_versions": [
        ask("Your code says `version = \"~> 1.90.0\"`. Which version could Terraform pick?",
            ["1.91.0", "1.90.4", "2.0.0"],
            answer=1,
            clue="With three numbers written, only the last one may go up.",
            why="`~> 1.90.0` allows 1.90 bug fixes only, so 1.90.4 is fine, but 1.91 and 2.0 are not."),
        ask("A run in Spacelift picked a newer provider than your laptop did, and the plans differ. "
            "What keeps them the same?",
            ["Run init again every day", "Delete the .terraform folder", "Commit .terraform.lock.hcl"],
            answer=2,
            clue="init writes down the exact version it picked. Where, and who sees that file?",
            why="The lock file records the exact provider version. Committed, every run uses the same "
                "one until someone runs `terraform init -upgrade` and the change is reviewed."),
    ],
}
