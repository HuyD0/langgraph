"""Guardrails and records: what the gateway writes down about every call, how long it stays, who may read
it, the checks on each request and answer, and how an agent's tool calls go through the same front door.
Follows The AI gateway in the Platform track, same shape: a message from a product team, one idea with one
picture, practice on that same situation. Facts are from Microsoft Learn's Unity Gateway, service policy,
MCP and Delta Lake pages for Azure Databricks.
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


lesson(MODULE, 'records_miss',
    title='What the records miss',
    checked='2026-11-01',
    sources=[source('Track model usage', 'https://learn.microsoft.com/azure/databricks/ai-gateway/usage-tracking'),
             source('Log requests and responses to inference tables', 'https://learn.microsoft.com/azure/databricks/ai-gateway/inference-tables'),
             TRACE_TABLE],
    cards=[
        card('One request, several rows',
             'One call to the gateway can leave more than one row in the usage table. A guardrail check, the '
             "router that picks a model and each turn of an agent get a row of their own, all sharing the request's "
             'id. So count requests by that id, and the guardrail rows are the price of the checks, right there in '
             'the same table.',
             picture=steps(('chat', 'The request arrives', 'one request id'),
                           ('alert', 'A guardrail checks it', 'a row of its own, same request id'),
                           ('reset', 'The router picks a model', 'another row'),
                           ('check', 'The model answers', 'the row with the answer tokens')),
             after='A column called source says which kind each row is.'),
        card('Every record has a hole',
             'No record holds everything, and the holes are written down in the docs. Know them before you promise '
             'anything about a record.',
             picture=sortby('What does it miss?',
                            sortrow('The usage table', 'Tokens for a non-streamed answer over 1 MiB', 'Big answers', icon='chart'),
                            sortrow('An inference table', 'Anything over 10 MiB, and some failed calls', 'Big ones', icon='pencil'),
                            sortrow('The trace table', 'Text cut at 3 MiB, and some failed calls', 'Cut', icon='pencil'),
                            sortrow('The audit log', 'The one record you may promise on', 'Promise', icon='listcheck')),
             after="1 MiB is about a long book's worth of text, so chat never gets there. Document parsing and image "
                   'or audio answers can.'),
        card('Make it trackable',
             'Three ways to keep a big answer in the record: **stream** it (a streamed answer is counted at any '
             "size), cap the answer's length with `max_tokens`, or split the work into smaller calls, which is "
             "usually the better design anyway. If a big answer still has to happen, the app keeps the provider's "
             'own token numbers in its trace, matched by the request id.',
             picture=piles(pile('Keep it countable', [('reset', 'Stream the answer'), ('gauge', 'Cap max_tokens'),
                                                       ('copy', 'Split the work')]),
                           pile('If it must be big', [('pencil', "The app keeps the provider's token count"),
                                                      ('listcheck', 'Matched by the request id')])),
             after='A budget estimates spend from the same token counts, so an uncounted answer slips past it too. '
                   'Rate limits and the cap are the backstop.'),
        card('Prove it with one call',
             'The docs say what is missed; the table says what was recorded. After a change, send one deliberately '
             'oversized request and read what the usage table, the trace table and the budget actually kept. It is '
             'a small test you run after every change so that a sentence in the docs becomes a fact about your setup.',
             picture=steps(('sparkle', 'Send one big request', 'on purpose, after a change'),
                           ('eye', 'Read the three records', 'usage rows, trace, budget estimate'),
                           ('pencil', 'Write down what was missed', 'next to the service, with the date'))),
    ],
    example=example('Counting what was really there', """-- requests, not rows
SELECT COUNT(DISTINCT request_id)
FROM system.ai_gateway.usage;

-- answers the table could not count
SELECT COUNT(*) FROM system.ai_gateway.usage
WHERE status_code = 200
  AND total_tokens IS NULL;"""),
    check=question(
        'The usage table shows 2,400 rows for the support app this morning, but the app itself counted 1,600 '
        'requests. Which is right?',
        ['Both: guardrail and router rows share an id', 'The app: the table double-counts',
         'The table: the app lost 800 requests'],
        answer=0,
        why='One request can leave several rows: its guardrail check and the router each get one, all with the '
            'same request id. Count requests by distinct request id; the extra rows are the price of the checks.',
    ),
    angle=angle(
        pattern='Know the holes, then test them',
        text="The big idea: a record is not the truth, it is what was recorded. One request can leave several rows, "
             "so count by the request id; every record misses something, and the docs say what; and after a change "
             "you prove it with one oversized call. Your code counts the real requests, the guardrail rows and the "
             "answers the table could not count.",
        say='"One request can leave [[several rows|one row|no rows::A guardrail check and the router each get one, '
            'with the same request id.]] in the usage table, so I count requests by their id. And every record has '
            'a hole, so after a change I [[send one oversized call|read the docs again|ask the provider::And read '
            'what the three records actually kept.]] and write down what was missed."',
        classic=None,
    ),
    exercise=exercise(
        title='Count What Was Really There',
        topic='platform',
        difficulty='easy',
        fn='count_requests',
        prompt="""`rows` are usage rows, each a dict like
`{"request_id": "r1", "source": "GUARDRAIL", "status_code": 200, "total_tokens": 120}`.

- `source` is `"GUARDRAIL"` for a guardrail check, `"ROUTER"` for the router, or `"MODEL"` for the answer itself
- `total_tokens` is `None` when the table could not count the answer

Return a dict with three counts:

- `"requests"`: how many different request ids there are
- `"guardrail_rows"`: how many rows have source `"GUARDRAIL"`
- `"uncounted"`: how many rows have status 200 and no token count""",
        pattern='One pass over the rows, keeping a set for "different" and counters for the rest.',
        target='one look at each row',
        realworld="This is the first query on a usage table: the real request count, what the checks cost, and how "
                  'many answers slipped past the count.',
        practice=practice(
            intro='Three situations about what the records hold.',
            explain='A record is what was recorded, not the whole truth. You found where uncounted answers hid in a '
                    'bill, made a big answer small by design, and saw why a budget alone cannot stop what the table '
                    'cannot count.',
            pattern='Count by the id, know the holes, test them',
            realworld="When a bill and the usage table disagree, you'll look for uncounted answers first; when an app "
                      "sends whole documents back, you'll ask for fields and a link instead; and you'll never let a "
                      'budget be the only brake.',
            asks=[
                ask('Where did the $800 go?',
                    ['Answers the table could not count', 'The provider overcharged', 'Guardrail checks, which are free'],
                    answer=0,
                    evidence=evidence('code', title='Last month, prod_ai.sales.docs_reader', text="""Provider invoice:             $3,900
Usage table spend estimate:   $3,100
Rows with status 200 and
  no token count:              1,840"""),
                    clue='Which rows have no token count?',
                    why='1,840 answers were too big to count, so their spend is on the invoice but not in the '
                        'estimate. Find the app, then stream or cap its answers. That is the Cost Optimization pillar.',
                    wrong=[None, 'The invoice is the bill; the gap is what the table could not count.',
                           'Guardrail checks are counted, and they cost tokens.']),
                ask('What do you suggest?',
                    ['Return the clauses that matter plus a link to the contract', 'Keep it: the gateway logs up to 10 MiB',
                     'Turn streaming off so the answer arrives in one piece'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"Our new app returns the whole contract in every answer, so the user '
                                           'can read it."'),
                    clue='Which design makes the answer small?',
                    why='A small answer is counted, costs less (answer tokens are the expensive ones) and is easier '
                        'to judge in a test. The document already lives somewhere: link to it. That is the Cost '
                        'Optimization pillar.',
                    wrong=[None, 'Logging it is not the problem; paying for and judging it is.',
                           'Streaming is what keeps a big answer countable. Turning it off makes it worse.']),
                ask('Will it?',
                    ['No: uncounted answers slip past; add a rate limit and a cap', 'Yes: budgets watch every call',
                     'Yes, as long as the budget is set to block usage'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"If the job starts returning huge answers, our budget will block it."'),
                    clue='What does a budget count spend from?',
                    why='A budget estimates spend from token counts, and an uncounted answer adds nothing to them. A '
                        'rate limit on requests and a cap on answer length stop what the budget cannot see. That is '
                        'the Reliability pillar.',
                    wrong=[None, 'Budgets watch the token counts, and big non-streamed answers have none.',
                           'Blocking only works on spend the budget can see.']),
            ],
        ),
        starter="""def count_requests(rows):
    # your code here
    pass
""",
        solution="""def count_requests(rows):
    ids = set()
    guardrail = 0
    uncounted = 0
    for row in rows:
        ids.add(row["request_id"])
        if row["source"] == "GUARDRAIL":
            guardrail += 1
        if row["status_code"] == 200 and row["total_tokens"] is None:
            uncounted += 1
    return {"requests": len(ids), "guardrail_rows": guardrail, "uncounted": uncounted}
""",
        cases=[
            case([{'request_id': 'r1', 'source': 'GUARDRAIL', 'status_code': 200, 'total_tokens': 120},
                  {'request_id': 'r1', 'source': 'MODEL', 'status_code': 200, 'total_tokens': 900},
                  {'request_id': 'r2', 'source': 'MODEL', 'status_code': 200, 'total_tokens': None}],
                 expected={'requests': 2, 'guardrail_rows': 1, 'uncounted': 1}, sample=True),
            case([], expected={'requests': 0, 'guardrail_rows': 0, 'uncounted': 0}),
            case([{'request_id': 'r9', 'source': 'MODEL', 'status_code': 429, 'total_tokens': None}],
                 expected={'requests': 1, 'guardrail_rows': 0, 'uncounted': 0}),
            case([{'request_id': 'a', 'source': 'GUARDRAIL', 'status_code': 200, 'total_tokens': 50},
                  {'request_id': 'a', 'source': 'ROUTER', 'status_code': 200, 'total_tokens': 10},
                  {'request_id': 'a', 'source': 'MODEL', 'status_code': 200, 'total_tokens': 700},
                  {'request_id': 'b', 'source': 'GUARDRAIL', 'status_code': 200, 'total_tokens': 50},
                  {'request_id': 'b', 'source': 'MODEL', 'status_code': 200, 'total_tokens': None}],
                 expected={'requests': 2, 'guardrail_rows': 2, 'uncounted': 1}),
        ],
        guided="""def count_requests(rows):
    # Replace every ___ with real code, then run the tests.

    ids = set()
    guardrail = 0
    uncounted = 0
    for row in rows:
        # Step 1: remember the request id (a set keeps each one once).
        ___
        if row["source"] == "GUARDRAIL":
            guardrail += 1
        # Step 2: a successful call the table could not count.
        if ___:
            uncounted += 1
    return {"requests": len(ids), "guardrail_rows": guardrail, "uncounted": uncounted}
""",
        fills=['ids.add(row["request_id"])', 'row["status_code"] == 200 and row["total_tokens"] is None'],
        concepts=[
            ['A set for "different"', 'Adding the same id twice keeps it once, so `len(ids)` counts different ids.',
             """ids = set()
ids.add("r1"); ids.add("r1")
len(ids)   # 1"""],
            ['Counting with += 1', 'A counter starts at 0 and goes up by one each time the test is True.',
             """n = 0
for x in [1, 2]:
    n += 1   # 2"""],
            ['Missing values', '`row["total_tokens"] is None` is True when there is no count at all.',
             '{"total_tokens": None}["total_tokens"] is None   # True'],
        ],
        byhand='Go down the rows. Write each request id down once, tick a count for every guardrail row, and tick '
               'another for every successful row with no token count.',
        why='Rows are not requests, and a missing count is not zero spend. These three numbers are the difference '
            'between reading the table and being fooled by it.',
    ),
)


POLICIES = source('Service policies for AI securables', 'https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/service-policies/')
SENSITIVE = source('Detect sensitive data with a service policy', 'https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/service-policies/detect-sensitive-data')
GOVERN_MCP = source('Govern an MCP', 'https://learn.microsoft.com/azure/databricks/ai-gateway/govern-mcp-service')
REGISTER_MCP = source('External MCP servers', 'https://learn.microsoft.com/azure/databricks/ai-gateway/register-mcp-service')
CUSTOM_MCP = source('Host an MCP server on Databricks Apps', 'https://learn.microsoft.com/azure/databricks/agents/mcp-tools/custom-mcp')
AUDIT_LOG = source('Diagnostic log reference', 'https://learn.microsoft.com/azure/databricks/admin/account-settings/audit-logs')
SKILLS = source('Skills support in Unity Gateway', 'https://learn.microsoft.com/azure/databricks/agents/uc-skills/')


lesson(MODULE, 'content_check',
    title='The content check',
    checked='2026-11-01',
    sources=[POLICIES, SENSITIVE, TRACE_TABLE],
    cards=[
        card('Grants say who, a policy says what',
             'A **service policy** is a guardrail attached to the service, so every caller gets the same check and '
             'no app has to write its own. The grants from the last module decide whether an app may call at all. A '
             'policy reads the words and decides how the call goes on: through, blocked, or with a part blanked out. '
             'The built-in policies screen for three things.',
             picture=terms(('alert', 'Jailbreak attempts', "a prompt written to get past the model's rules"),
                           ('x', 'Unsafe content', 'harmful requests, and harmful answers'),
                           ('lock', 'Sensitive data', 'card numbers, national id numbers and the like: blocked, or redacted')),
             after='A jailbreak attempt can arrive as orders hidden in text the model reads, like a pasted document, '
                   'as well as in what a person types. Service policies are in Beta, an early release that can '
                   'still change.'),
        card('On the way in, and on the way out',
             'A policy runs at two moments: on the request, before the model sees it (**ON CALL**), and on the '
             'answer, before the caller sees it (**ON RESULT**). On a model service the jailbreak check reads only '
             'the request, because a jailbreak arrives in what is sent. Sensitive data can be in either, so that '
             'check can run both ways.',
             picture=steps(('chat', 'The request arrives', 'ON CALL: jailbreak, unsafe content, sensitive data'),
                           ('bot', 'The model answers', 'only a request that got through'),
                           ('eye', 'The answer is checked', 'ON RESULT: unsafe content, sensitive data'),
                           ('check', 'The caller gets a reply', 'the answer, or a block with its reason'))),
        card('Blocked, but not an error',
             'A blocked request still gets a normal reply: **HTTP 200**, the code for "all fine". The reply\'s '
             'assistant turn says it was blocked and names the policy, and a `databricks_service_policy` part '
             'carries the reason. Why not an error? Chat clients resend the whole conversation on every turn, and an '
             'error would fire again each time. So count blocks from the logged replies or the trace table, never '
             'from status codes. Redaction is gentler: the sensitive part is replaced with a placeholder like '
             '`[CREDIT_CARD]`, and the rest goes on to the model.',
             picture=sortby('What does the caller get?',
                            sortrow('A jailbreak attempt', 'A 200 reply whose text says it was blocked, and why', 'Blocked', icon='x'),
                            sortrow('A card number in the prompt', 'The same prompt with [CREDIT_CARD] in its place, when the policy redacts', 'Redacted', icon='eye'),
                            sortrow('An ordinary question', "The model's answer, as usual", 'Through', icon='check')),
             after='Every one of those is a 200, so an error count never sees a block.',
             note=('Good to know: the trace shows every decision',
                   "Each policy that ran leaves a policy_evaluated event on the request's trace, with the action it "
                   'took, so you can see which checks ran even when nothing was blocked.')),
        card("Your own rule, or a vendor's",
             "The built-in checks are Databricks' own. A team can also write a rule of its own in SQL: a small "
             'function that sees who is calling and the tags the app put on the request, and answers allow or deny. '
             'Or a policy can send the content to an outside guardrail vendor through a Unity Catalog connection. '
             'Either way, a check that cannot run is a block: policies **fail closed**, so an unreachable vendor or '
             'a bug in your SQL means deny, never a quiet pass. One more answer, **ASK** (a person approves first), '
             'exists only on MCP services, which the next lesson covers: a model service cannot wait for a person, '
             'so ASK blocks there.',
             picture=piles(pile('Who decides', [('layers', "Built-in: Databricks' own checks"),
                                                 ('pencil', 'Custom: your SQL rule, which sees the caller and the tags'),
                                                 ('cloud', 'External: a vendor, through a connection')]),
                           pile('What they can say', [('check', 'ALLOW: let it through'),
                                                      ('x', 'DENY: block, with a reason'),
                                                      ('person', 'ASK: a person first, on MCP services only')])),
             after='Attaching any of them needs **MANAGE** on the service, so a caller cannot switch its own checks off.'),
    ],
    example=example('A blocked reply: status 200, the reason inside', """HTTP/1.1 200 OK
{
  "choices": [{"message": {
    "role": "assistant",
    "content": "Blocked by service policy system.ai.block_jailbreak."
  }}],
  "databricks_service_policy": {
    "reason": "Detected a jailbreak attempt."
  }
}
// an ordinary answer is a 200 too: count blocks from the reply, not the code"""),
    check=question(
        'team-sales says: "Our dashboard counts gateway errors, and it shows zero blocks since the jailbreak policy '
        'went on. So nobody has tried anything." What\'s wrong with that?',
        ['A block is a 200 reply, so an error count never sees one', 'Nothing: zero errors means zero blocks',
         'The policy must be attached to the wrong phase'],
        answer=0,
        why='A blocked request gets a normal HTTP 200 reply whose text names the policy and the reason. Count blocks '
            'from the logged replies or the trace table, not from error codes.',
    ),
    angle=angle(
        pattern='Who may call, then what may be said',
        text="The big idea: grants decide whether an app may call; a service policy reads the words and decides how "
             "the call goes on, on the way in and on the way out. A block is a normal 200 reply that says it was "
             "blocked, so you count blocks from the replies, never from error codes. Your code does that count, "
             "policy by policy.",
        say='"A service policy checks the words on the way [[in and out|in only|out only::Two moments: the request, '
            'and the answer.]]. A blocked request still gets a normal 200 reply that says why, so I count blocks '
            'from the [[replies|error codes|rate limits::Where the block reason is written down.]], not from the codes."',
        classic=None,
    ),
    exercise=exercise(
        title='Count the Blocks',
        topic='platform',
        difficulty='easy',
        fn='blocks_by_policy',
        prompt="""`replies` is a list of logged gateway replies, each a dict like
`{"request_id": "r1", "status_code": 200, "policy": None}`.

- `policy` is the name of the service policy that blocked the reply, taken from its `databricks_service_policy`
  part, or `None` when nothing blocked it
- a block is a 200 like any other reply, so ignore `status_code`; an error reply (a 429, say) has no policy

Return a dict from policy name to how many replies it blocked, like `{"system.ai.block_jailbreak": 2}`. A policy
that blocked nothing is left out.""",
        pattern='One pass over the replies, counting under each policy name.',
        target='one look at each reply',
        realworld='This is the count behind "how often do the guardrails fire, and which ones?": made from the '
                  'replies, because a block is a 200.',
        practice=practice(
            intro='Three situations about the content check.',
            explain='Grants say who may call; a policy reads the words and says how the call goes on, on the way in '
                    'and on the way out. You counted blocks from replies that all said 200, saw where the jailbreak '
                    'check can and cannot run, and kept a broken check failing closed.',
            pattern='Count blocks from the replies, not the codes',
            realworld="When a team says the guardrails never fire, you'll look at the replies before you believe it; "
                      "when card numbers turn up in prompts, you'll redact rather than block; and when a vendor check "
                      "goes down, you'll know why every call is suddenly denied.",
            asks=[
                ask('How many of these were blocked?',
                    ['Two', 'None: every status is 200', 'One: only the jailbreak counts as a block'],
                    answer=0,
                    evidence=evidence('code', title='Three replies logged by prod_ai.sales.support_chat', text="""request  status  reply
r1       200     "Your renewal date is 3 March."
r2       200     "Blocked by service policy system.ai.block_jailbreak."
                 databricks_service_policy.reason: Detected a jailbreak attempt.
r3       200     "Blocked by service policy system.ai.detect_sensitive_data."
                 databricks_service_policy.reason: Detected sensitive data (CREDIT_CARD)."""),
                    clue='Where is a block written down?',
                    why='A block is a 200 reply with a databricks_service_policy reason, and two replies carry one. '
                        'The status code says nothing about blocks. That is the Operational Excellence pillar: watch '
                        'the record that holds the fact.',
                    wrong=[None, 'The status is 200 on every reply, blocked or not.',
                           'The sensitive data policy blocked r3 just as the jailbreak policy blocked r2.']),
                ask('Will that work on a model service?',
                    ['No: on a model service it reads only the request', 'Yes: every built-in check runs on both phases',
                     'Yes, as long as the policy rank is set high enough'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"We\'ll put the jailbreak check on the answer as well, so we catch it '
                                           'both ways."'),
                    clue='A jailbreak is in what someone sends. Which phase holds that?',
                    why='On a model service the jailbreak check reads the request only, because a jailbreak arrives '
                        'in what is sent; on the answer it would judge nothing. Put the sensitive data and unsafe '
                        'content checks on both phases instead. That is the Security pillar: a check that judges '
                        'nothing is false comfort.',
                    wrong=[None, 'Only some checks run on both phases; the jailbreak one reads the request on a model service.',
                           'Rank sets the order of checks, not where they can run.']),
                ask('What do you tell them?',
                    ['No: a policy that cannot check fails closed, by design', 'Yes: set the policy to allow when the vendor times out',
                     'Yes: move the vendor check to the answer phase only'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"The guardrail vendor had an outage this morning and every call to our '
                                           'service was denied for an hour. Can you make it let calls through when '
                                           'the vendor is down?"'),
                    clue='What is a guardrail worth while it is switched off?',
                    why='A check that cannot run denies: an unreachable or slow vendor, an error in your SQL, a '
                        'missing field. Letting calls through would turn every vendor outage into an hour with no '
                        'guardrail, which is when you most want one. Test a new policy in Log mode before you '
                        'enforce it. That is the Security pillar.',
                    wrong=[None, 'There is no allow-on-timeout: a check that cannot run is a deny.',
                           'The phase changes what is checked, not what happens when the vendor is down.']),
            ],
        ),
        starter="""def blocks_by_policy(replies):
    # your code here
    pass
""",
        solution="""def blocks_by_policy(replies):
    counts = {}
    for reply in replies:
        policy = reply["policy"]
        if policy is None:
            continue
        counts[policy] = counts.get(policy, 0) + 1
    return counts
""",
        cases=[
            case([{'request_id': 'r1', 'status_code': 200, 'policy': None},
                  {'request_id': 'r2', 'status_code': 200, 'policy': 'system.ai.block_jailbreak'},
                  {'request_id': 'r3', 'status_code': 200, 'policy': 'system.ai.detect_sensitive_data'}],
                 expected={'system.ai.block_jailbreak': 1, 'system.ai.detect_sensitive_data': 1}, sample=True),
            case([], expected={}),
            case([{'request_id': 'r9', 'status_code': 429, 'policy': None}], expected={}),
            case([{'request_id': 'a', 'status_code': 200, 'policy': 'system.ai.block_jailbreak'},
                  {'request_id': 'b', 'status_code': 200, 'policy': 'system.ai.block_jailbreak'},
                  {'request_id': 'c', 'status_code': 200, 'policy': None}],
                 expected={'system.ai.block_jailbreak': 2}),
            case([{'request_id': 'x', 'status_code': 200, 'policy': 'prod_ai.gov.no_pushes'},
                  {'request_id': 'y', 'status_code': 500, 'policy': None},
                  {'request_id': 'z', 'status_code': 200, 'policy': 'system.ai.block_unsafe_content'}],
                 expected={'prod_ai.gov.no_pushes': 1, 'system.ai.block_unsafe_content': 1}),
        ],
        guided="""def blocks_by_policy(replies):
    # Replace every ___ with real code, then run the tests.

    counts = {}
    for reply in replies:
        policy = reply["policy"]
        # Step 1: an ordinary answer, or an error, has no policy: skip it.
        if ___:
            continue
        # Step 2: one more block under that policy's name (0 so far if it's the first).
        counts[policy] = ___
    return counts
""",
        fills=['policy is None', 'counts.get(policy, 0) + 1'],
        concepts=[
            ['Skipping with continue', '`continue` jumps to the next time round the loop, skipping the rest of this one.',
             """for x in [None, 1]:
    if x is None:
        continue
    print(x)   # 1"""],
            ['Counting under a name', '`counts.get(name, 0)` gives the count so far, or 0 the first time; add one and store it back.',
             """counts = {}
counts["a"] = counts.get("a", 0) + 1   # {"a": 1}"""],
            ['None means nothing there', '`reply["policy"] is None` is True when no policy blocked the reply.',
             '{"policy": None}["policy"] is None   # True'],
        ],
        byhand='Go down the replies and ignore the status code. When a reply names a policy, put a tick under that '
               'name; the ticks under each name are its count.',
        why='An error count that reads zero is wrong by every block. Counting from the replies is how you learn how '
            'often the guardrails fire, and which ones.',
    ),
)


lesson(MODULE, 'tools_front_door',
    title="An agent's tools, governed",
    checked='2026-11-01',
    sources=[GOVERN_MCP, REGISTER_MCP, CUSTOM_MCP, AUDIT_LOG, SKILLS],
    cards=[
        card('The same front door for tools',
             'An **MCP server** (Model Context Protocol, the standard way an agent finds and calls its tools) is '
             "registered in Unity Catalog as an **MCP service**. So an agent's tool calls pass the same gates as its "
             'model calls: sign in, grants, the content check, the rate limit and the records. Three kinds of server '
             'sit behind the one kind of service.',
             picture=terms(('cloud', 'Managed', 'Databricks runs it, like the servers in system.ai'),
                           ('code', 'Custom', 'you host it, for example as a Databricks App'),
                           ('lock', 'External', "someone else's server, reached through a Unity Catalog HTTP connection that holds the credential for that hop, so the agent never does")),
             after='Grants, policies, limits and records work the same on all three, which is why one lesson covers them.'),
        card('Only the tools it needs',
             'A registered server offers every tool it has unless you choose. Select tools by exact name, or by a '
             'prefix like `get_*`. There is no way to say "everything except delete_*": exclusion patterns are not '
             'supported, so list what is allowed. An unselected tool is absent from the list the agent sees, and a '
             'call to it anyway is refused. Keep "automatically include new tools" off, so a tool the server adds '
             'next month is reviewed before any agent can use it. Give the agent only the tools its task needs, the '
             'rule called least privilege: no more access than the job needs.',
             picture=sortby('The selection is get_*: what happens?',
                            sortrow('get_ticket', 'On the list: the call goes on to the other checks', 'Allowed', icon='check'),
                            sortrow('get_comments', 'On the list too: the prefix matches', 'Allowed', icon='check'),
                            sortrow('push_files', 'Not on the list, and a call is refused', 'Refused', icon='x')),
             after='Selection is the first control. A policy is the second: it decides call by call, and can deny a '
                   'tool for one agent while the tool stays on the list.'),
        card('Three grants, and one grant to keep back',
             'Calling a tool needs the same walk down as calling a model: **USE CATALOG**, **USE SCHEMA** and '
             '**EXECUTE** on the MCP service. The HTTP connection behind an external server has a grant of its own, '
             '**USE CONNECTION**, and callers never get it: it would let someone use the connection directly, around '
             'the tool selection and the policies. Keep it for the people who register servers. A rate limit on the '
             "service counts tool calls a minute, so one looping agent cannot take everyone's share.",
             picture=piles(pile('Callers get', [('layers', 'USE CATALOG and USE SCHEMA'),
                                                ('check', 'EXECUTE on the MCP service'),
                                                ('gauge', 'A share of the tool calls a minute')]),
                           pile('Callers never get', [('lock', 'USE CONNECTION: for whoever registers the server'),
                                                      ('alert', 'MANAGE: that would let them change the tool list')]))),
        card('Ask a person first',
             'A policy on an MCP service runs before the tool (**ON CALL**) and after it (**ON RESULT**). On the way '
             'in it can allow, deny, or **ASK**: hold the call until a person approves it. ASK exists only here, '
             'because a tool that writes or sends something cannot be undone by a check on its result. So sort each '
             'tool by what it can do: a tool that only reads needs no approval; one that writes inside the platform, '
             'or acts on an outside system, gets an ASK policy. The result is checked too: it is text from outside, '
             'and a prompt injection can arrive inside it.',
             picture=sortby('What can the tool do?',
                            sortrow('get_ticket: reads', 'Allow it', 'Read', icon='eye'),
                            sortrow('create_ticket: writes inside the platform', 'Ask a person first', 'Write', icon='person'),
                            sortrow('send_email: acts on an outside system', 'Ask a person first', 'Outside', icon='person')),
             after='The jailbreak check screens tool results as well, so a poisoned document cannot steer the next call.',
             note=('Where this sits in the Databricks AI Security Framework',
                   'Databricks publishes a security framework for AI systems, DASF 2.0: 12 parts of an AI system, 62 '
                   'risks and numbered controls, each tied to the Databricks page that sets it up. A 2026 extension '
                   'for agents adds part 13 and controls 68 to 73. This lesson is controls 68, 69 and 70, one for '
                   'each kind of server (managed, custom, external), plus 64, limiting what models and agents may '
                   'reach. The content check from the last lesson is controls 54 (guardrails) and 58 (filters and '
                   'masking). Quoting the numbers in a design review saves a long argument.')),
        card('One call, three records',
             'Every tool call leaves the same three records as a model call. The usage row has '
             "`service_type = MCP_SERVICE` and the tool's name in `mcp_metadata.tool_name`. The audit log gets an "
             '`mcpCall` event with `is_write`, which says whether the tool could change anything; it comes from the '
             "tool's own read-only hint, so check that hint when you register a server. The trace holds the "
             'arguments, the result and every policy decision.',
             picture=steps(('listcheck', 'The agent asks for the tools', 'it gets only the selected ones'),
                           ('bot', 'It calls one', 'signed in as itself, or as the person it works for'),
                           ('lock', 'Grants and the rate limit', 'the same checks as a model call'),
                           ('person', 'The ON CALL policy', 'allow, deny, or ask a person first'),
                           ('cloud', 'The call reaches the server', 'managed, custom or external'),
                           ('pencil', 'The result comes back', 'through the ON RESULT policy; then the usage row, the audit event and the trace are written')),
             after="**Skills** (packaged instructions a coding agent loads, to do one task your team's way) are not "
                   'tools. They are published in Unity Catalog, approved in the coding-agent configuration your '
                   'platform team publishes, and each load is logged.'),
    ],
    example=example('One MCP service, set up', """MCP SERVICE  prod_ai.sales.tickets_mcp
  kind           external, through connection sales_tickets_conn
  tools          get_ticket, create_ticket    (selected by name)
                 delete_ticket, export_all    (absent: not selected)

  EXECUTE        -> sp-docs-agent
  USE CONNECTION -> grp-platform-admins       (never a caller)
  rate limit     60 tool calls a minute

  ON CALL        create_ticket  -> ASK a person
  ON RESULT      sensitive data -> block"""),
    check=question(
        'sp-docs-agent calls push_files on prod_ai.sales.repo_mcp and gets "Tool not allowed by MCP service '
        'configuration", although it has EXECUTE on the service. What happened?',
        ['push_files is not in the tool selection', 'The agent is missing USE CONNECTION',
         'The rate limit for tool calls is set to 0'],
        answer=0,
        why='Selection is the first control: a tool that is not selected is absent from the list and refused if '
            'called, whatever the grants say. USE CONNECTION is for whoever registers the server, never for callers.',
    ),
    angle=angle(
        pattern='Tools through the same front door',
        text="The big idea: an agent's tools are registered as an MCP service, so every tool call passes the gates a "
             "model call does: grants, a share of the calls a minute, a policy on the way in and on the way out, and "
             "three records. Two controls are new: select only the tools the agent needs, and ask a person before a "
             "tool that writes. Your code works out which calls the selection refuses.",
        say='"An agent\'s tools go through the same front door as its models, so I select [[only the tools it needs|'
            'every tool on the server|the read-only tools::Least privilege: name them, no exclusions.]], and a policy '
            'asks a person before a tool that [[writes|reads|lists::A check on the result cannot undo it.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Which Calls Are Refused',
        topic='platform',
        difficulty='easy',
        fn='refused_calls',
        prompt="""`selectors` is an MCP service's tool selection: a list of exact tool names or prefixes ending in `*`,
like `["get_*", "create_ticket"]`. An empty list means every tool is exposed.

`calls` is a list of tool names an agent tried to call, in order.

A call is allowed when any selector matches it: an exact name, or a prefix (the part before the `*`) that the
name starts with. Return the list of calls that are refused, in the order they were made, like `["push_files"]`.""",
        pattern='Check each call against every selector: a prefix matches by its start, a name matches exactly.',
        target='one look at each call for each selector',
        realworld="This is the check the gateway makes on every tool call, and the one you'll run in your head when "
                  'an agent says a tool is "not allowed".',
        practice=practice(
            intro="Three situations about an agent's tools.",
            explain="An agent's tools go through the same front door as its models. You chose the tools an agent "
                    'gets by naming them, gave the tools that write or act outside an ASK policy, and read a refused '
                    'call in the audit log instead of reaching for a grant.',
            pattern='Select by name, ask before a write',
            realworld="When a new server is registered, you'll name the tools the agent needs and leave the rest off; "
                      "when a tool can write or send, you'll want a person to approve it first; and when an agent "
                      "says a tool is not allowed, you'll read the audit log before you touch a grant.",
            asks=[
                ask('What do you do?',
                    ['Select get_* only, and add tools when a task needs them', 'Expose them all, and rely on the rate limit',
                     'Expose them all, and deny the write tools with a policy'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"Our new agent only needs to read tickets. Can you register the ticket '
                                           'server with all its tools exposed, so we don\'t have to come back when '
                                           'it needs more?"'),
                    clue='How many tools does a read-only agent need?',
                    why='Least privilege: name what the task needs. An exposed tool is one a fooled agent can call; a '
                        'policy can deny it, but it stays on the list the agent sees. Coming back is one '
                        'configuration change. That is the Security pillar.',
                    wrong=[None, 'A rate limit slows a misuse down; it does not stop it.',
                           'A denied tool is still on the list, and the deny is a second control, not the first.']),
                ask('Which tools get an ASK policy?',
                    ['update_account and send_invoice', 'send_invoice only: it leaves the platform',
                     'All three: every tool call carries risk'],
                    answer=0,
                    evidence=evidence('code', title='Tools on prod_ai.sales.crm_mcp', text="""get_account      reads one account
update_account   writes a field in the platform
send_invoice     emails an invoice to the customer"""),
                    clue='Which of these could a check on the result not undo?',
                    why='A write inside the platform and an action outside both happen before the result is '
                        'checked, so a person approves first. Reading an account changes nothing, so it needs no '
                        'approval. That is the Security pillar.',
                    wrong=[None, 'A write inside the platform cannot be undone by a check on the result either.',
                           'A tool that only reads changes nothing, so an approval on it is only a delay.']),
                ask('The agent reports delete_ticket as "broken". What is the fix, if any?',
                    ['None: the selection refused it, as designed', 'Grant the agent EXECUTE on delete_ticket',
                     'Grant the agent USE CONNECTION'],
                    answer=0,
                    evidence=evidence('code', title='system.access.audit, last hour, sp-docs-agent', text="""action   tool_name       is_write  error
mcpCall  get_ticket      false
mcpCall  create_ticket   true
mcpCall  delete_ticket   true      Tool not allowed by MCP service configuration"""),
                    clue='Is EXECUTE given per tool, or per service?',
                    why='EXECUTE is on the service, and the agent already calls two tools with it. The refusal is the '
                        'tool selection doing its job; if the task really needs deletes, change the selection and '
                        'give delete_ticket an ASK policy. USE CONNECTION would let the agent around every control. '
                        'That is the Operational Excellence pillar: read the record before you change a grant.',
                    wrong=[None, 'There is no EXECUTE on a single tool: EXECUTE is on the service, and the agent has it.',
                           'USE CONNECTION goes around the selection and the policies. Callers never get it.']),
            ],
        ),
        starter="""def refused_calls(selectors, calls):
    # your code here
    pass
""",
        solution="""def refused_calls(selectors, calls):
    refused = []
    for name in calls:
        allowed = len(selectors) == 0
        for sel in selectors:
            if sel.endswith("*") and name.startswith(sel[:-1]):
                allowed = True
            elif name == sel:
                allowed = True
        if not allowed:
            refused.append(name)
    return refused
""",
        cases=[
            case(['get_*', 'create_ticket'], ['get_ticket', 'push_files', 'create_ticket', 'delete_ticket'],
                 expected=['push_files', 'delete_ticket'], sample=True),
            case([], ['anything', 'delete_all'], expected=[]),
            case(['get_*'], [], expected=[]),
            case(['get_*'], ['get_issue', 'getaway', 'get'], expected=['getaway', 'get']),
            case(['send_email'], ['send_email', 'send_email_batch'], expected=['send_email_batch']),
        ],
        guided="""def refused_calls(selectors, calls):
    # Replace every ___ with real code, then run the tests.

    refused = []
    for name in calls:
        allowed = len(selectors) == 0   # an empty selection exposes every tool
        for sel in selectors:
            # Step 1: a prefix selector like get_*: does the name start with the part before the *?
            if sel.endswith("*") and ___:
                allowed = True
            # Step 2: any other selector must match the whole name.
            elif ___:
                allowed = True
        if not allowed:
            refused.append(name)
    return refused
""",
        fills=['name.startswith(sel[:-1])', 'name == sel'],
        concepts=[
            ['Does it start with?', '`name.startswith("get_")` is True when the name begins with those letters, underscore included.',
             '"get_issue".startswith("get_")   # True'],
            ['All but the last letter', '`sel[:-1]` is the text without its last character.',
             '"get_*"[:-1]   # "get_"'],
            ['A flag that starts False', 'Let any match flip `allowed` to True, then look at it once the inner loop is done.',
             """allowed = False
for s in ["a", "b"]:
    if s == "b":
        allowed = True
allowed   # True"""],
        ],
        byhand='For each call, go down the selectors. One ending in * matches when the name starts with the part '
               'before the *; any other must match the whole name. No match means the call is refused.',
        why='A refused tool call is the most common "my agent is broken" ticket after a new server is registered. '
            'Working the selection out by hand is how you answer it in a minute.',
    ),
)
