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
}
