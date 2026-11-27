"""More Check questions for Azure Databricks (modules/azure_databricks.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "can_read_table": [
        ask("`analysts` has `USE CATALOG` on `main`, `USE SCHEMA` on `main.sales`, and `SELECT` on "
            "the schema `main.sales`. Can Ana, who is in `analysts`, read `main.sales.orders`?",
            ["Yes: SELECT on the schema covers its tables", "No: SELECT must be on the table itself", "No: she also needs ALL PRIVILEGES"],
            answer=0,
            clue="A key given at one level counts for everything below it.",
            why="SELECT on the schema reaches every table in it, and she has USE CATALOG and USE "
                "SCHEMA too. That's all three keys, so she can read it."),
        ask("Ben joins the team and needs to read the same tables as the analysts. What's the best "
            "way to give him access?",
            ["Grant SELECT to Ben on each table", "Give Ben ALL PRIVILEGES on main", "Add Ben to the analysts group"],
            answer=2,
            clue="Teams grant keys to something people can join and leave.",
            why="Ben holds every key given to any group he's in. Joining `analysts` gives him their "
                "access, and leaving it takes that away in one place."),
    ],
    "private_networking": [
        ask("What does secure cluster connectivity take away from clusters?",
            ["Their public IP addresses", "Their access to storage", "Their network security group"],
            answer=0,
            clue="What makes a machine reachable straight from the internet?",
            why="With secure cluster connectivity, clusters have no public IPs, so nothing on the "
                "internet can reach them directly."),
        ask("A workspace needs people to reach it only over Microsoft's network. Which Private Link "
            "is that?",
            ["Front-end (inbound)", "Back-end", "Neither: use a NAT gateway"],
            answer=0,
            clue="Is the traffic coming in from people, or going out from clusters?",
            why="Front-end, or inbound, Private Link is for people and tools reaching the workspace. "
                "Back-end is for clusters reaching Databricks' control plane."),
    ],
    "workspace_metastore": [
        ask("Two workspaces in the same region need to see the same sales data. How?",
            ["Link both to the region's metastore", "Copy the tables into each workspace", "Give each its own metastore"],
            answer=0,
            clue="What do all workspaces in one region share?",
            why="Every workspace linked to the region's metastore sees the same catalogs, so the "
                "data lives once and both see it."),
        ask("Where does Databricks recommend giving managed tables their storage?",
            ["On each catalog", "On the whole metastore", "On each table"],
            answer=0,
            clue="Think of two teams in one metastore whose data must sit in separate places. Which level does each team own?",
            why="Managed storage on each catalog keeps each catalog's data in its own place, which "
                "Databricks recommends for keeping data apart."),
    ],
}
