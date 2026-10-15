"""More Check questions for How the platform repos fit together (modules/platform_repos.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "field_status": [
        ask("A team writes `name: daily-report` in `clusters.yml`. The plan shows the cluster as "
            "`sales_daily-report`. What happened to the name field?",
            ["SUPPORTED: it arrived exactly as written", "TRANSFORMED: it was changed on the way", "DEFAULTED: the runbook filled it in"],
            answer=1,
            clue="The team did write a value, and something reached the plan. Is it the same value?",
            why="The runbook put the team's code in front of the name, so the value changed on the "
                "way to the provider. That's TRANSFORMED."),
        ask("The check allows a new field in `clusters.yml`. You haven't opened the runbook or the "
            "module yet. What word do you give the field for now?",
            ["SUPPORTED: the check allowed it", "DROPPED: nothing uses it yet", "UNKNOWN: not traced all the way yet"],
            answer=2,
            clue="You've checked two of the five points. What about the other three?",
            why="Until you follow it through the runbook, the module and the provider, you can't say. "
                "UNKNOWN is the honest word: valid YAML alone proves nothing."),
    ],
    "folder_access": [
        ask("A plan gives every workspace user `CAN_READ` on the team's folder, but nobody typed "
            "that in `team.yml`. What should the reviewer say?",
            ["It's a mistake: take it out of the plan", "It's expected: the runbook adds it", "It's a leak: someone edited it by hand"],
            answer=1,
            clue="Before calling it a mistake, think about the access that shows up without anyone typing it.",
            why="The runbook gives every workspace user CAN_READ by default. Knowing what it adds "
                "stops you flagging something that's on purpose."),
        ask("Two plans give the same groups the same permissions on a folder, but list them in a "
            "different order. Should the reviewer flag it?",
            ["Yes: the first group listed wins", "Yes: it must match the order in team.yml", "No: only who ends up with what matters"],
            answer=2,
            clue="Once it's applied, can any group do something different in one plan than in the other?",
            why="The order of the list doesn't change anyone's access. Review the end result: each "
                "group and the permission it finally has."),
    ],
    "cluster_from_yaml": [
        ask("A team's code is `MKT` and its cluster's name in `clusters.yml` is `Weekly-Load`. "
            "What name will the plan show?",
            ["mkt_weekly-load", "MKT_Weekly-Load", "weekly-load"],
            answer=0,
            clue="Two things happen on the way: the code goes in front, and the letters change.",
            why="The runbook joins the code and the name with `_` and makes it all lower case, "
                "so `MKT` and `Weekly-Load` become `mkt_weekly-load`."),
        ask("A team copies a policy's id from the workspace and puts `policy_id: 0012AB` in "
            "`clusters.yml`. What happens?",
            ["It works: an id is more exact than a name", "The runbook swaps in Personal Compute", "It's rejected: teams name the policy"],
            answer=2,
            clue="Who is meant to look up a policy's id: the team, or the module?",
            why="A raw policy_id isn't allowed in YAML. Teams name the policy, and the module looks "
                "up its id."),
    ],
}
