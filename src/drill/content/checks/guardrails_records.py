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
    "records_miss": [
        ask("Which answer can the usage table not count tokens for?",
            ["A non-streamed answer over 1 MiB", "Any answer from an outside provider", "Any answer longer than a page"],
            answer=0,
            clue="Think size, and whether it was streamed.",
            why="The hole is specific: a non-streamed answer over 1 MiB. A streamed answer is counted at any size, "
                "and ordinary chat answers are far smaller than that."),
        ask("An app returns whole documents in each answer. What's the first thing to change?",
            ["Return the fields that matter and a link to the document", "Turn off the usage table to save money",
             "Ask the platform team to raise the limit"],
            answer=0,
            clue="Which change makes the answer small and cheaper?",
            why="A small answer is counted, costs less and is easier to judge in a test. The limit is fixed; the "
                "design is yours to change."),
    ],
}
