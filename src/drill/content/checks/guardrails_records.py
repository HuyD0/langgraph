"""More Check questions for the Guardrails and records module (the first is in the lesson itself)."""

from drill.content.model import ask

CHECKS = {
    "record_lifetimes": [
        ask("Which record is Databricks' own, kept about a year, and holds no prompt text?",
            ["The usage table", "The trace table", "A masked copy of the traces"],
            answer=0,
            clue="Which one did finance use?",
            why="The usage table is a Databricks system table: who called which service and how many tokens, kept "
                "for a year, with no text in it. The traces and any copy are tables of yours."),
        ask("You set DELETE ROWS 30 DAYS AFTER time on the trace table. Roughly when is a row really gone?",
            ["Up to about 43 days later", "Exactly 30 days later", "The same night"],
            answer=0,
            clue="Add the lag, then the week the old files are kept.",
            why="30 days, plus up to 6 for the delete to run, plus 7 while the old files are kept: up to 43. To be "
                "gone within 30, set 17."),
    ],
}
