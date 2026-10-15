"""More Check questions for Databricks access control (modules/access.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "missing_acls": [
        ask("A teammate can attach notebooks to your cluster, but can't restart it when it hangs. "
            "What's the smallest step up that lets them restart it?",
            ["CAN_ATTACH_TO", "CAN_RESTART", "CAN_MANAGE"],
            answer=1,
            clue="Give the least that does the job. The top level lets them change everything.",
            why="Cluster levels go CAN_ATTACH_TO, then CAN_RESTART, then CAN_MANAGE. CAN_RESTART is "
                "the smallest step that lets them restart it."),
        ask("Your team has `CAN_USE` on a Vector Search endpoint, but queries to one index still "
            "fail. What else might they need?",
            ["SELECT on the index in Unity Catalog", "CAN_MANAGE on the endpoint", "A bigger cluster for the search"],
            answer=0,
            clue="The index itself is a Unity Catalog object, with its own grants.",
            why="Querying an index needs CAN_USE on the endpoint and SELECT on the index in Unity "
                "Catalog. CAN_MANAGE would be more than they need."),
    ],
    "location_for_path": [
        ask("An external location covers `abfss://raw@lakefict.dfs.core.windows.net/sales`. "
            "Does it cover `.../sales-archive/2025`?",
            ["Yes, the path starts with sales", "No, it must match a whole folder", "Yes, if the role is granted"],
            answer=1,
            clue="Is sales-archive a folder inside sales, or a different folder next to it?",
            why="A location covers its own folder and the folders under it. `sales-archive` is a "
                "different folder that only starts with the same letters."),
        ask("An analyst asks for the storage credential so they can read files themselves. What "
            "do you give them instead?",
            ["The credential, with a warning", "The storage account's access key", "READ FILES on the external location"],
            answer=2,
            clue="People get access to a path, never to the identity behind it.",
            why="You grant the external location to them, with privileges like READ FILES. People "
                "never get the credential itself."),
    ],
    "pick_securable": [
        ask("A notebook must query tables in the team's PostgreSQL database without copying them. "
            "Which object fits?",
            ["A connection and a foreign catalog", "A service credential", "An external location"],
            answer=0,
            clue="You want to query the other database as if it were a catalog.",
            why="That's Lakehouse Federation: a connection plus a foreign catalog lets you query "
                "PostgreSQL as if it were a catalog."),
        ask("Code in a job must call Azure Key Vault. Someone suggests reusing the storage "
            "credential you already have. Which object fits?",
            ["The storage credential, it works", "An HTTP connection", "A service credential"],
            answer=2,
            clue="Key Vault isn't storage. It's another Azure service your code calls.",
            why="A service credential is for code that calls other Azure services, like Key Vault, "
                "and users need ACCESS on it. A storage credential is for files."),
    ],
    "masked_columns": [
        ask("A mask policy applies `TO` all users `EXCEPT` the `pii-readers` group. Lena is in "
            "`pii-readers`. What does she see in the masked column?",
            ["The masked value, like everyone", "An error when she queries it", "The real, unmasked value"],
            answer=2,
            clue="Read who the policy leaves out.",
            why="The EXCEPT list skips the policy for those groups. Lena is in `pii-readers`, so the "
                "mask doesn't apply to her."),
        ask("The same email mask has been added by hand to 40 tables, one at a time. What would "
            "you suggest?",
            ["One ABAC policy that follows a tag", "Keep adding the mask table by table", "Move every email column into one table"],
            answer=0,
            clue="The rule is the same every time. Where could it be written just once?",
            why="When the same rule repeats, one ABAC policy on a governed tag covers every tagged "
                "table, new ones too, with no per-table work."),
    ],
    "grants_to_people": [
        ask("A grant list has `analysts`, `6f1c2a3e-1d4b-...` and `ben@example.com`. Which one "
            "should you flag?",
            ["analysts", "The application ID", "ben@example.com"],
            answer=2,
            clue="Which one names a single person?",
            why="An email means a grant to a person, which goes stale when they move or leave. "
                "`analysts` is a group, and the id is a service principal."),
        ask("A catalog is owned by Sam. Sam leaves, and now nobody can change the catalog. What "
            "would have prevented this?",
            ["Making a group the owner", "Giving Sam a backup account", "Copying the catalog monthly"],
            answer=0,
            clue="Owners follow the same rule as grants.",
            why="Owners should be groups. A group's members are managed in one place, so the "
                "catalog never ends up with nobody in charge."),
    ],
}
