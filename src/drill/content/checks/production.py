"""More Check questions for Production patterns (modules/production.py). See checks/__init__.py."""
from drill.content.model import ask

CHECKS = {
    "token_bucket": [
        ask("Your token bucket has room for a burst of 5, and it's full. Eight requests arrive at the "
            "same moment. What happens?",
            ["All 8 go straight away", "The first 5 go, the rest wait", "All 8 wait for the bucket to refill"],
            answer=1,
            clue="Each request spends one token. How many tokens are there?",
            why="A full bucket lets a short burst through, one token each. The rest wait for tokens "
                "to refill, so you stay under the limit."),
        ask("A teammate reads \"token bucket\" and thinks it counts the words in each prompt. "
            "What does one token stand for here?",
            ["A permit to send one request", "A word or piece of the prompt", "A password for the endpoint"],
            answer=0,
            clue="Here it's not about text at all. Think of a ticket to get in.",
            why="In a token bucket, a token is just a permit to send one request. It's a different "
                "thing from the tokens a model reads and writes."),
    ],
    "retry_wait": [
        ask("A call fails with a 429, and the server's reply says Retry-After: 30 seconds. "
            "Your backoff would wait 2 seconds. How long do you wait?",
            ["30 seconds, as the server asked", "2 seconds, as your backoff says", "Somewhere between 2 and 30"],
            answer=0,
            clue="When the server tells you how long to wait, who knows best?",
            why="If the server gives a Retry-After value, wait that long. Backoff with jitter is only "
                "for when the server doesn't say."),
        ask("Your code retries every failed call, including ones that failed because the API key is wrong. "
            "What's the problem?",
            ["It should wait longer between tries", "It needs more jitter on each try", "A wrong key won't fix itself later"],
            answer=2,
            clue="Which errors can succeed if you just try again later?",
            why="Only retry errors that can pass later, like rate limits, overload or timeouts. "
                "A wrong key fails every time, so retrying just wastes calls."),
    ],
    "run_with_limit": [
        ask("Your batch of 100 model calls runs one at a time and takes over 3 minutes. "
            "What change makes it faster without a flood of 429 errors?",
            ["Start all 100 at the same time", "Add a pause after every call", "Let up to 10 run at once"],
            answer=2,
            clue="One at a time is slow, all at once is too many. Look for the middle.",
            why="A concurrency limit gets most of the speed of running calls together, while "
                "staying under the rate limit."),
        ask("Your limit is 3. Three calls are running and one of them finishes. "
            "When does the fourth call start?",
            ["Right away, in the free place", "When all three have finished", "After a short fixed pause"],
            answer=0,
            clue="A semaphore counts free places. What happens when one opens up?",
            why="The semaphore hands the free place to the next call the moment one finishes, "
                "so the places stay busy and the batch ends sooner."),
    ],
    "optimistic_writes": [
        ask("A ticket is at version 7. Worker A saves, saying \"I read version 7\", so it becomes 8. "
            "Then worker B saves, also saying \"I read version 7\". What happens to B's save?",
            ["It's accepted and replaces A's", "It's rejected, so B re-reads first", "It waits until A's save is undone"],
            answer=1,
            clue="B read the ticket before A saved. Is version 7 still the current one?",
            why="B's write is based on old data, so it's rejected instead of silently erasing A's change. "
                "B re-reads version 8 and tries again."),
        ask("Two workers each add 1 to a counter that shows 10. Both read 10, and both save 11. "
            "One add is lost. What is this problem called?",
            ["A race condition", "A rate limit", "A timeout"],
            answer=0,
            clue="The result depends on which worker got there first.",
            why="When the result depends on timing, it's a race condition. Here the second save "
                "silently overwrote the first."),
    ],
    "upsert_rows": [
        ask("You upsert support tickets into a table. Which field makes the best key?",
            ["The time the row was saved", "The row's place in the table", "The ticket id"],
            answer=2,
            clue="Pick the one that names the ticket and never changes between runs.",
            why="A key must be stable. The ticket id stays the same on every run, so a retry finds "
                "the same row and replaces it. A save time changes every run."),
        ask("Ticket T1 is saved with status \"open\". A later run upserts T1 with status \"closed\". "
            "What does the table hold now?",
            ["Two T1 rows: open and closed", "One T1 row, now closed", "One T1 row, still open"],
            answer=1,
            clue="An upsert checks whether the key is already there.",
            why="T1's key is already in the table, so the update replaces that row. "
                "New keys are added, existing ones are updated."),
    ],
    "chunk_rows": [
        ask("Your function gets one row, but it also peeks at the row before it. "
            "Why is that a problem on Spark?",
            ["The row before may be on another machine", "Spark can only work on number columns", "Spark lets each row be read only once"],
            answer=0,
            clue="Spark cuts the table into partitions. Where do they run?",
            why="Spark runs partitions at the same time on different machines, so the row before may "
                "not be there. Your function may only use its own row."),
        ask("Document d1 had chunks d1-0 and d1-1. After an edit it makes d1-0, d1-1 and d1-2. "
            "You re-run the job with MERGE. What does the table hold for d1?",
            ["Three rows: two updated, one new", "Five rows: the old two plus three new", "Two rows: the new chunk is skipped"],
            answer=0,
            clue="MERGE matches rows by id. Which ids are already in the table?",
            why="d1-0 and d1-1 match rows already there, so they're updated. d1-2 is a new id, "
                "so it's added."),
    ],
    "process_new": [
        ask("Last night's run saved offset 500. Tonight the log has events up to 520. "
            "Which events does tonight's run handle?",
            ["All events from 1 to 520", "Only event 520", "Only 501 to 520"],
            answer=2,
            clue="The offset remembers where the last run got to.",
            why="The job starts after the saved offset, so it only handles the new events. "
                "Then it saves 520 for next time."),
        ask("Your watermark says events from before 9 am no longer count. An event stamped 8:50 "
            "arrives late, at 9:30. What happens to it?",
            ["It's skipped as too late", "It's counted like the others", "The whole job stops"],
            answer=0,
            clue="Compare the event's own time, not its arrival time, with the cut-off.",
            why="The watermark decides how late is too late. The event happened before the cut-off, "
                "so it's left out."),
    ],
    "validate_rows": [
        ask("A row has every column in the contract, with the right kinds of value, plus a new column "
            "called channel. You allow extra columns. What happens to the row?",
            ["It's good and gets loaded", "It goes to quarantine", "The load stops with an error"],
            answer=0,
            clue="Check what the contract asks for. Is anything missing or the wrong kind?",
            why="Nothing in the contract is broken, so the row is good. Letting new columns in was a "
                "choice you made on purpose: that's schema evolution."),
        ask("A row is missing the minutes column completely. Everything else is fine. "
            "Where should it go?",
            ["Loaded, with minutes left blank", "To quarantine, to check later", "Loaded, since only one is missing"],
            answer=1,
            clue="The contract lists the columns every row must have.",
            why="A missing column breaks the contract, so the row is set aside to look at later. "
                "The other rows still load."),
    ],
    "skew_report": [
        ask("You group rows by customer, and one key, \"unknown\", holds most of the rows. "
            "Which of these fixes the slow job?",
            ["Sort the rows before grouping", "Handle the unknown rows separately", "Run the job less often"],
            answer=1,
            clue="The trouble is one key. Do something about that key.",
            why="Pulling the hot key out and handling it on its own stops one task doing most of the work. "
                "Salting the key also helps: it spreads those rows out."),
        ask("The Spark UI shows one task running far longer than all the rest. A teammate wants to "
            "double the cluster. Will that help much?",
            ["Not much: one task still has most rows", "Yes: twice the machines, half the time", "Yes: every task gets more room"],
            answer=0,
            clue="Where do all the rows for one key go?",
            why="All rows for the hot key still land in one task, so the extra machines mostly wait. "
                "Fix the skew instead."),
    ],
}
