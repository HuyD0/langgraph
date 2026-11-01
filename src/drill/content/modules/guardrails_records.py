"""Guardrails and records: what the gateway writes down about every call, how long it stays, who may read
it, and the checks on each request. Follows The AI gateway in the Platform track, same shape: a message
from a product team, one idea with one picture, practice on that same situation. Facts are from Microsoft
Learn's Unity Gateway and Delta Lake pages for Azure Databricks.
"""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import (angle, ask, card, case, evidence, example, exercise, lesson, module, pile, piles,
                                 practice, question, sortby, sortrow, source, steps, terms)

MODULE = module('guardrails-records', 'Guardrails and records',
                'What the gateway writes down about every call, how long it stays, and who may read it.',
                setting=PLATFORM_SETTING)

TRACE_TABLE = source('Monitor all AI activity using the unified trace table', 'https://learn.microsoft.com/azure/databricks/ai-gateway/unified-trace-table')
AUTO_TTL = source('Automatic row deletion with auto time-to-live', 'https://learn.microsoft.com/azure/databricks/tables/operations/auto-ttl')
SYSTEM_TABLES = source('System tables reference', 'https://learn.microsoft.com/azure/databricks/admin/system-tables/')
REDACT = source('Govern and redact traces in Unity Catalog', 'https://learn.microsoft.com/azure/databricks/mlflow3/genai/tracing/govern-redact')


lesson(MODULE, 'record_lifetimes',
    title='How long we keep it',
    checked='2026-11-01',
    sources=[TRACE_TABLE, AUTO_TTL, SYSTEM_TABLES, REDACT],
    cards=[
        card('Three kinds of record',
             'Every call through the gateway leaves three kinds of record, and only one of them holds what people '
             'typed. The usage table you met in the last module is the first kind.',
             picture=terms(('chart', 'Usage rows', 'who called which service, and how many tokens: no text in them'),
                           ('pencil', 'Traces', 'the prompt and the answer, word for word: the sensitive part'),
                           ('listcheck', 'The audit log', 'who changed what: a grant, a setting, a tool call')),
             after="The usage table and the audit log are Databricks' own system tables, kept for a year. Traces "
                   'live in a table of yours.'),
        card("Nothing keeps itself, unless you let it",
             'The trace table is yours, in Unity Catalog, and it grows without limit unless you give its rows a '
             "**lifetime**. Microsoft's advice is to decide the lifetime before tracing goes live, because a table "
             'that already holds a year of prompts is much harder to shrink than an empty one.',
             picture=piles(pile('Databricks keeps', [('chart', 'Usage rows: a year'), ('listcheck', 'The audit log: a year')]),
                           pile('You decide', [('pencil', 'Traces: no limit until you set one'),
                                               ('copy', 'Any copy you make: the same')]))),
        card('Three shelves, each with a date',
             'Give each kind of record its own shelf, and each shelf a date with a reason. The raw text gets the '
             'shortest shelf: it is the sensitive part, and every extra day is more to protect and more to pay for.',
             picture=sortby('How long does it stay?',
                            sortrow('Raw prompts and answers', 'About a month: long enough to debug a problem and pull test examples', 'Shortest', icon='clock'),
                            sortrow('A masked copy, names and numbers hidden', 'About a year: long enough to compare this month with last year', 'Longer', icon='eye'),
                            sortrow('Usage totals', 'Keep them: there is no text in them', 'Keep', icon='chart')),
             after='Write the shelf and its reason next to each table, in the same file that creates the table.'),
        card("Deleting isn't instant",
             'A lifetime is one line of SQL: `DELETE ROWS 17 DAYS AFTER time`. But the row is not gone that day. '
             'The delete can lag by up to six days, and the old files are kept for seven more so you can look '
             "back. Like an agent's memory, an expired row must really be deleted on a schedule rather than hidden.",
             picture=steps(('clock', 'The row expires', 'the lifetime you set, counted from its time column'),
                           ('reset', 'The delete runs', 'up to six days later'),
                           ('copy', 'Old files are kept', 'seven more days, so you can look back'),
                           ('check', 'Gone', 'the clean-up removes the files')),
             after='So to be gone within 30 days, set 17: 30, minus 6 for the lag, minus 7 for the kept files. '
                   "When someone asks to be forgotten by a date, don't wait for the schedule: run the delete and "
                   'the clean-up yourself, then check.'),
    ],
    example=example('A lifetime on the trace table', """ALTER TABLE prod_ai.gov.gateway_traces
  DELETE ROWS 17 DAYS AFTER time;

-- wanted: gone within 30 days
-- 30 - 6 (lag) - 7 (kept files) = 17"""),
    check=question(
        'team-sales asks you to keep every prompt and answer forever, "in case we need them". What\'s wrong with that?',
        ['Every day the text stays is more risk and cost', 'Nothing: storage is cheap enough to keep it all',
         'The gateway deletes them after a year anyway'],
        answer=0,
        why='The raw text is the sensitive part, and the table grows without limit. Keep the totals forever, give '
            'the text a short shelf, and keep a masked copy if you need to look back.',
    ),
    angle=angle(
        pattern='Three shelves, each with a date',
        text="The big idea: every record gets a shelf and a date with a reason. The raw text has the shortest shelf "
             "because it is the sensitive part; totals have no text, so they stay. And deleting isn't instant: the "
             "delete can lag and old files are kept a week, so the lifetime you set is shorter than the deadline you "
             "promised. Your code works out that setting for each table.",
        say='"Prompts and answers are the sensitive part, so they get the [[shortest|longest|same::Long enough to '
            'debug, then gone.]] shelf, and usage totals have no text, so we keep them. Deleting isn\'t '
            '[[instant|allowed|logged::Up to six days of lag, plus a week the old files are kept.]], so I set the '
            'lifetime shorter than the deadline."',
        classic=None,
    ),
    exercise=exercise(
        title='Work Out the Lifetimes',
        topic='platform',
        difficulty='easy',
        fn='lifetimes',
        prompt="""`tables` is a list of dicts, one for each table, like
`{"name": "gateway_traces", "deadline_days": 30, "kept_days": 7}`.

- `deadline_days` is how soon a row must really be gone
- `kept_days` is how long deleted files are kept so you can look back

The delete can lag by up to 6 days, so the lifetime to set is `deadline_days - 6 - kept_days`. If that would be
below 0, the deadline can't be met: use 0.

Return a dict from table name to the lifetime to set, like `{"gateway_traces": 17}`.""",
        pattern='A sum for each item, with a floor.',
        target='one look at each table',
        realworld='This is the arithmetic behind every retention setting: the deadline you promised, minus the '
                  "delete's lag, minus the days old files are kept.",
        practice=practice(
            intro='Three situations about how long records stay.',
            explain='Every record gets a shelf and a date with a reason: the raw text the shortest, a masked copy '
                    "longer, totals kept. You gave the text a shelf, set a lifetime on a table nobody had, and saw "
                    "that a person's deadline needs a delete by hand, because the automatic one lags.",
            pattern='The sensitive part gets the shortest shelf',
            realworld="When a team asks to keep everything, you'll give the text a short shelf with a reason, a "
                      "masked copy a longer one, and the totals no end. When a deadline is promised, you'll set the "
                      'lifetime shorter and check the delete really ran.',
            asks=[
                ask('What do you offer instead?',
                    ['A short shelf for the text, and totals kept forever', 'Forever, but in a cheaper storage tier',
                     'A year for everything, then delete it all'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"Just keep every prompt and answer forever, in case we need them."'),
                    clue='Which part of a record is the sensitive part?',
                    why='The text is the sensitive part, so it gets a short shelf; the totals have none, so they can '
                        'stay. Keeping text nobody reads is risk with no benefit: that is the Security pillar.',
                    wrong=[None, 'Cheaper storage is still a growing pile of sensitive text.',
                           'Totals are worth keeping, and a year of raw text is a long time to protect.']),
                ask("What's the first fix?",
                    ['Set a lifetime on the table today', 'Export the rows to a laptop and delete the table',
                     'Wait for Databricks to clean it up'],
                    answer=0,
                    evidence=evidence('code', title='Table properties for prod_ai.gov.gateway_traces', text="""autottl.expireInDays:     (not set)
autottl.timestampColumn:  (not set)
rows:       41,000,000
first row:  11 months ago"""),
                    clue="Who owns this table's lifetime?",
                    why='The trace table is yours, and nothing deletes from it until you set a lifetime. Set it now, '
                        'with the reason written next to it, and the backlog drains on the schedule. That is the '
                        'Operational Excellence pillar.',
                    wrong=[None, 'A laptop is the worst place for 41 million prompts.',
                           "Databricks doesn't manage this table's lifecycle. Its own docs say so."]),
                ask('Are they?',
                    ['No: run the delete and clean-up for that person now', 'Yes: 30 days is the usual deadline',
                     'Yes, as long as the lifetime is set to 30'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"A customer asked to be forgotten. Our traces auto-delete within 30 days, '
                                           'so we\'re covered."'),
                    clue='How exact is the automatic delete?',
                    why="Auto-delete lags by days and keeps old files a week, so a lifetime of 30 means gone in up to "
                        "43. A person's request has a date: delete their rows and run the clean-up yourself, then "
                        'check. That is the Security pillar.',
                    wrong=[None, 'The deadline comes from the request, and the automatic delete is not exact.',
                           'A lifetime of 30 means gone in up to 43 days, not 30.']),
            ],
        ),
        starter="""def lifetimes(tables):
    # your code here
    pass
""",
        solution="""def lifetimes(tables):
    out = {}
    for t in tables:
        days = t["deadline_days"] - 6 - t["kept_days"]
        out[t["name"]] = max(days, 0)
    return out
""",
        cases=[
            case([{'name': 'gateway_traces', 'deadline_days': 30, 'kept_days': 7}], expected={'gateway_traces': 17}, sample=True),
            case([], expected={}),
            case([{'name': 'raw_spans', 'deadline_days': 90, 'kept_days': 30}], expected={'raw_spans': 54}),
            case([{'name': 'tiny', 'deadline_days': 10, 'kept_days': 7}], expected={'tiny': 0}),
            case([{'name': 'a', 'deadline_days': 14, 'kept_days': 7}, {'name': 'b', 'deadline_days': 365, 'kept_days': 7}],
                 expected={'a': 1, 'b': 352}),
        ],
        guided="""def lifetimes(tables):
    # Replace every ___ with real code, then run the tests.

    out = {}
    for t in tables:
        # Step 1: the deadline, minus 6 days of lag, minus the days old files are kept.
        days = ___
        # Step 2: never below 0.
        out[t["name"]] = ___
    return out
""",
        fills=['t["deadline_days"] - 6 - t["kept_days"]', 'max(days, 0)'],
        concepts=[
            ['Taking away in one line', 'Subtract each part in turn; Python reads it left to right.',
             '30 - 6 - 7   # 17'],
            ['A floor with max', '`max(days, 0)` gives days, unless it is below 0, when it gives 0.',
             'max(-3, 0)   # 0'],
            ['Filling a dict in a loop', 'Each time round, store a value under that item\'s name.',
             """out = {}
for t in [{"name": "a", "v": 1}]:
    out[t["name"]] = t["v"]   # {"a": 1}"""],
        ],
        byhand='For each table, take the deadline, subtract 6 for the lag and then the kept days. If it goes below '
               "0, use 0. Write the answer next to the table's name.",
        why="The number you set isn't the number you promised. Working it out for each table, with the floor at 0, "
            'is how a promise like "gone within 30 days" is kept.',
    ),
)
