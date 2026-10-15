"""More Check questions for Databricks building blocks (modules/workspace.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "pick_compute": [
        ask("An analyst wants a sales dashboard and to ask questions of the data in plain words "
            "with Genie. Which compute fits?",
            ["A serverless SQL warehouse", "All-purpose compute", "Jobs compute"],
            answer=0,
            clue="Dashboards and Genie both run on SQL.",
            why="SQL, dashboards and Genie run on a SQL warehouse, and the serverless kind is the "
                "one Databricks recommends."),
        ask("A data scientist explores data in a notebook every day. They need no special setup "
            "and don't want to pick machine sizes. Which compute fits?",
            ["Jobs compute", "Serverless compute", "A SQL warehouse"],
            answer=1,
            clue="Nothing special is needed, and they'd rather not size anything.",
            why="Serverless works for notebooks, starts in seconds and has nothing to size. With no "
                "init script or GPU, nothing pushes it to classic compute."),
    ],
    "unsupported_runtimes": [
        ask("You're setting up a new job that will run every night for the next year. Which "
            "runtime should you pick?",
            ["The newest version that isn't LTS", "A recent LTS version", "Whatever the last job used"],
            answer=1,
            clue="Scheduled work wants a version that keeps getting fixes for years.",
            why="LTS versions get fixes for about three years, so they're the pick for anything "
                "that runs on a schedule."),
        ask("A team needs tables protected by ABAC on classic compute. Their cluster runs "
            "`15.4.x-scala2.12`. What's the problem?",
            ["15.4 is too old: ABAC needs 16.4 or later", "Nothing: 15.4 LTS is still supported", "ABAC only works on SQL warehouses"],
            answer=0,
            clue="Being supported isn't the same as having every feature.",
            why="Tables protected by ABAC need 16.4 or later on classic compute. 15.4 is still "
                "supported, but too old for that feature."),
    ],
    "policy_violations": [
        ask("A policy fixes `custom_tags.team` to `data`. Someone creates a cluster with "
            "`team = ml`. What happens?",
            ["It's allowed: tags are free text", "It breaks the rule: it must be data", "It's allowed if they have CAN_USE"],
            answer=1,
            clue="A fixed rule leaves room for one value only.",
            why="A fixed rule means the setting must equal that value. `ml` isn't `data`, so the "
                "policy stops it."),
        ask("A new teammate can't create compute with the team's policy. What do they need on "
            "that policy?",
            ["SELECT on the team's tables", "CAN_MANAGE on the workspace", "The CAN_USE permission"],
            answer=2,
            clue="A policy has one permission of its own that lets people build with it.",
            why="Users need CAN_USE on a policy to create compute with it. Table grants and "
                "workspace rights don't cover that."),
    ],
    "skipped_tasks": [
        ask("`clean` depends on `ingest`, and `report` depends on `clean`. `ingest` fails. "
            "What happens to `report`?",
            ["It runs on yesterday's data", "It doesn't run: marked upstream failed", "It fails with its own error"],
            answer=1,
            clue="The default Run if needs every task before it to have gone well. Did they?",
            why="With the default \"all succeeded\", a failure stops everything downstream, even "
                "two steps away. `report` is marked upstream failed, not as a failure of its own."),
        ask("`check_sales` and `check_stock` each depend only on `load`. `load` succeeds, then "
            "`check_sales` fails. What happens to `check_stock`?",
            ["It runs: it only waits for load", "It's skipped: a task in the job failed", "It waits until check_sales is fixed"],
            answer=0,
            clue="Is `check_stock` downstream of the task that failed?",
            why="Only tasks that depend on the failed one are skipped. `check_stock` needs just "
                "`load`, which succeeded, so it runs."),
    ],
    "resolve_variables": [
        ask("`warehouse` has a default of `small`, and the dev target doesn't set it. What does "
            "`${var.warehouse}` become in `deploy -t dev`?",
            ["small, from the default", "Nothing: dev didn't set it", "Whatever the prod target uses"],
            answer=0,
            clue="If the target says nothing, where else can a value come from?",
            why="A target's own value wins when it sets one. Dev sets nothing, so the default, "
                "`small`, is used."),
        ask("Two people deploy the same bundle to dev at the same time. Why don't they overwrite "
            "each other's jobs?",
            ["Dev allows one deploy at a time", "`run_as` gives each their own copy", "`mode: development` adds their name"],
            answer=2,
            clue="Look at what happens to resource names in the dev target.",
            why="`mode: development` puts your name in front of resource names, so each person gets "
                "their own copy in dev."),
    ],
    "tag_coverage": [
        ask("Before deleting an old cluster, you want to know who to ask. Which tag helps?",
            ["An `owner` tag", "The `ClusterId` tag", "The `Vendor` tag"],
            answer=0,
            clue="Two of these Databricks adds by itself. Which one names a person or team?",
            why="An owner tag says who to ask before deleting something. Vendor and ClusterId are "
                "default tags Databricks adds, and they name nobody."),
        ask("Finance reads spend in Azure Cost Management, not in Databricks. Will they see a "
            "classic cluster's `team` tag there?",
            ["No: tags stay inside Databricks", "Yes: the tags reach its virtual machines", "Only if the cluster is serverless"],
            answer=1,
            clue="Think about where a classic cluster's machines actually live.",
            why="On Azure, classic compute tags are copied to the virtual machines, so finance sees "
                "them in Azure Cost Management too."),
    ],
    "cost_by_tag": [
        ask("A spend query adds up `usage_quantity` by team and calls the total dollars. What's "
            "wrong with it?",
            ["Nothing: one DBU costs one dollar", "DBUs need multiplying by the SKU price", "It should group by usage_date"],
            answer=1,
            clue="`usage_quantity` counts DBUs. What turns DBUs into money?",
            why="Usage rows count DBUs, and the price depends on the SKU. Join list_prices on "
                "sku_name and multiply to get dollars."),
        ask("Your manager wants an email when the team's spend passes 2,000 dollars this month. "
            "What do you set up?",
            ["A tag on every cluster", "A daily query you read by hand", "A budget in the account console"],
            answer=2,
            clue="Look for the one that sends an alert when a line is crossed, with no one watching.",
            why="Budgets in the account console send email alerts when spend passes a threshold "
                "you choose."),
    ],
    "idle_cost": [
        ask("A cluster has `autotermination_minutes` set to 0. It's Friday evening and nobody is "
            "using it. When does it stop?",
            ["Straight away, because it's idle", "After 60 minutes of idle time", "Not until someone stops it"],
            answer=2,
            clue="Here, zero doesn't mean zero minutes.",
            why="0 means never: the cluster keeps running, and billing, until someone stops it."),
        ask("People on your team keep setting auto-termination to 0 on new clusters. How do you "
            "stop that for good?",
            ["Send a reminder email each month", "Force a maximum in a compute policy", "Switch everything off each night"],
            answer=1,
            clue="Look for something that applies when the cluster is created, not after.",
            why="A compute policy can force a maximum, so no one can set 0 when they create "
                "compute."),
    ],
}
