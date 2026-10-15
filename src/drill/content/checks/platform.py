"""More Check questions for Databricks as code (modules/platform.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "missing_tags": [
        ask("A new storage account in the plan has none of the team's tags. Why should the "
            "reviewer care?",
            ["Nobody can say whose spend it is", "Terraform won't be able to apply it", "The account will be read-only"],
            answer=0,
            clue="Think about what finance does with tags.",
            why="Tags drive cost allocation. Without them, the account's spend is spend nobody can "
                "attribute."),
        ask("A teammate thinks the azurerm provider adds the team's tags to every resource by "
            "itself. What do you tell them?",
            ["Right: set them once on the provider", "Wrong: merge `local.tags` into each one", "Right, but only on storage accounts"],
            answer=1,
            clue="Why would teams bother keeping a shared map of tags in `locals`?",
            why="The azurerm provider has no provider-wide default tags, so teams merge a shared "
                "`local.tags` into every resource and check plans for gaps."),
    ],
    "grants_to_revoke": [
        ask("The sales catalog uses `databricks_grants`, and the code gives `contractors` SELECT. "
            "You want to take that away. How?",
            ["Revoke it by hand in Catalog Explorer", "Remove it from the code, then apply", "Wait for the grant to run out"],
            answer=1,
            clue="If the code still lists them, what does the next apply do?",
            why="The code is the source of truth. Revoke it by hand and the next apply gives it "
                "back, because the grants must match the code exactly."),
        ask("Your Terraform should add one group's grant to a catalog and leave every other grant "
            "alone. Which resource does that?",
            ["`databricks_grants`, the authoritative one", "`databricks_grant`, the non-authoritative one", "Neither: add it by hand in Catalog Explorer"],
            answer=1,
            clue="Which kind removes every grant that isn't in its own code?",
            why="`databricks_grant` adds that one group's grant and leaves the rest alone. "
                "`databricks_grants` would remove every grant not in its code."),
    ],
    "overlapping_subnets": [
        ask("Your clusters will grow, and you need room for more nodes. Should the host subnet be "
            "a /24 or a /22?",
            ["/22: smaller number, bigger block", "/24: bigger number, more room", "Same size: only the start differs"],
            answer=0,
            clue="Remember which way the number after the slash goes.",
            why="A smaller number after the slash means a bigger block, so a /22 holds more "
                "addresses, and more nodes."),
        ask("At your busiest, your clusters will need 64 nodes. You pick a /26 host subnet, "
            "which has 64 addresses. Why will it run short?",
            ["Azure keeps 5 addresses in every subnet", "Each node takes two addresses in it", "A /26 is too small for any cluster"],
            answer=0,
            clue="Not every address in a subnet can go to a node.",
            why="Azure reserves 5 addresses in each subnet, so fewer than 64 are left for nodes. "
                "Size subnets for the clusters you'll need, with room to spare."),
    ],
    "allocate_capacity": [
        ask("A weekend experiment sends a huge burst, and the customer help-center assistant gets "
            "error 429. What would have prevented it?",
            ["Tiers, with critical apps served first", "More capacity for the experiment", "Giving every app the same share"],
            answer=0,
            clue="Decide who matters most before capacity runs short.",
            why="Tiers decide who comes first ahead of time. The help-center app is critical, so "
                "it's served before any experiment."),
        ask("A critical app runs on provisioned throughput. At its busiest, the PTU deployment is "
            "full. What should happen to the extra requests?",
            ["They fail with error 429", "They wait in line until later", "Spillover sends them to pay-as-you-go"],
            answer=2,
            clue="Look for the setting that catches the overflow.",
            why="With spillover on, requests the PTU deployment can't take go to a pay-as-you-go "
                "deployment instead of failing."),
    ],
    "check_limits": [
        ask("The space limit is 100,000 tokens a minute. The research group's limit is set to "
            "120,000. Does that group limit protect anything?",
            ["Yes, the group gets more room", "No, the space limit wins anyway", "Yes, it replaces the space limit"],
            answer=1,
            clue="Which limit always has the last word?",
            why="The service limit always wins, so a group limit at or above it protects nothing. "
                "Set it below the space limit."),
        ask("The sandbox shares a Foundry deployment with a live app. An eval run loops all "
            "afternoon. What's the risk?",
            ["The live app runs short of capacity", "The eval run gets cheaper", "Nothing: the two are separate"],
            answer=0,
            clue="They both draw from the same deployment.",
            why="Experiments eat the capacity live apps need. Give the sandbox a deployment of its "
                "own."),
    ],
}
