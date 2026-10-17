"""Lesson diagrams: one picture in the Learn step, drawn by the page from this data in the app's own look
(page/diagrams.js), so it follows Dusk and Light and fits a phone. The shapes are the ordinary ones the
learner will meet at work, and each is drawn from the lesson's own example, so picture and text tell
one story. Five kinds:

- ``flow``: boxes and arrows, left to right; one box may be opened up with a few detail lines, and the
  last box may split into shares (a canary release).
- ``tree``: rows with a bar each, to scale: a trace, workers over time, tokens per helper.
- ``graph``: boxes placed on a small grid with labelled arrows: a state diagram, stacks that depend on
  each other.
- ``table``: columns and rows; one column may be drawn as pills (dev, test, holdout).
- ``chart``: lines, bars or dots over two axes, with a dashed reference line and one marked point.

Every diagram has a plain ``caption`` and numbered ``callouts``; the page draws the numbers on the
picture and the list under it, so a screen reader gets the same explanation. Blue (``accent``) marks
the one thing this lesson is about, amber the callout numbers, grey everything else; no other colour
means anything. One diagram per lesson at most, placed after the Learn paragraph ``after``
(0 = the first). tests/test_diagrams.py checks the shapes and that every label on a picture also
appears in the lesson's words, its caption or its callouts.
"""

from drill.content.model import diagram

DIAGRAMS = {
    # ---- Frame
    'use_case_score': diagram('chart', after=1,
        caption='The example map: value up the side, doable along the bottom. Each dot is an idea from the example, and the corner it lands in says what to do with it; the staffing forecast is low on both, so it is shelved.',
        callouts=['Accelerate: HR policy answers are valuable and doable, so start a pilot',
                  'Research: contract review is valuable, but the data and the definition are not ready yet',
                  'Incubate: meeting summaries are doable but small, a safe place to learn'],
        x={'label': 'doable', 'max': 10, 'ticks': []}, y={'label': 'value', 'max': 10, 'ticks': []},
        quadrants=['shelve', 'incubate', 'research', 'accelerate'],
        points=[{'x': 8.4, 'y': 8.8, 'label': 'HR policy answers', 'now': True, 'n': 1}, {'x': 2.2, 'y': 6.8, 'label': 'contract review', 'n': 2},
                {'x': 8.6, 'y': 1.6, 'label': 'meeting summaries', 'n': 3}, {'x': 1.6, 'y': 3.4, 'label': 'staffing forecast'}]),
    # ---- Build
    'backoff_delays': diagram('chart', after=0,
        caption='The waits from the example, one bar per attempt: 1, 2, 4, then the cap of 5 seconds holds the last two.',
        callouts=['Each wait is double the one before', 'The cap: waits never grow past 5 seconds'],
        x={'label': 'attempt', 'max': 5, 'ticks': [1, 2, 3, 4, 5]}, y={'label': 'seconds', 'max': 6, 'ticks': [0, 2, 4, 6]},
        bars=[1, 2, 4, 5, 5], reference={'y': 5, 'label': 'the cap of 5 seconds'}, marks=[{'x': 2, 'y': 2, 'n': 1}, {'x': 5, 'y': 5, 'n': 2}]),
    'retrieve': diagram('flow', after=0,
        caption='The question, step by step, through a retrieval app. This lesson is the retrieve step: for \u201cCan I carry leave over?\u201d it might keep #41 leave.md at 0.91, #07 leave.md at 0.86 and #12 pay.md at 0.80.',
        callouts=['Pages: the files the app may read', 'Chunks: each page split into pieces a model can read at once',
                  'Index: every chunk as a list of numbers', 'Retrieve: the top k chunks closest to the question, with their scores', 'Answer: written from those chunks, naming the page it came from, its source'],
        question='Can I carry leave over?',
        nodes=[{'label': 'Pages', 'word': 'files', 'n': 1}, {'label': 'Chunks', 'word': 'pieces', 'n': 2}, {'label': 'Index', 'word': 'numbers', 'n': 3},
               {'label': 'Retrieve', 'word': 'top k', 'now': True, 'n': 4}, {'label': 'Answer', 'word': 'source', 'n': 5}],
        detail={'at': 3, 'rows': [['#41 leave.md', '0.91'], ['#07 leave.md', '0.86'], ['#12 pay.md', '0.80']]}),
    'gather_results': diagram('tree', after=3,
        caption='The example as bars over time: three workers start together; wiki and tickets finish, billing is stopped at the 10 second timeout, and the gather runs then, not at 30.',
        callouts=['Billing is cut off at the timeout and counted as timed out', 'The gather runs at 10 seconds with wiki and tickets'],
        unit='s', max=12, rows=[{'name': 'wiki', 'start': 0, 'size': 2}, {'name': 'tickets', 'start': 0, 'size': 4},
                                 {'name': 'billing', 'start': 0, 'size': 10, 'cut': True, 'n': 1}, {'name': 'gather', 'start': 10, 'size': 1, 'hot': True, 'n': 2}],
        marker={'at': 10, 'label': 'the 10 second timeout'}),
    # ---- Evaluate and ship
    'assign_splits': diagram('table', after=2,
        caption='The example as a table: each group dealt across the three sets in the same proportions, three to dev, one to test, one to holdout.',
        callouts=['Every set gets every group, so no group is missing from the test', 'The dealing is by position; the next lesson makes it stable as the set grows'],
        columns=['group', 'dev', 'test', 'holdout'],
        rows=[['billing', 'b1 b2 b3', 'b4', 'b5'], ['shipping', 's1 s2 s3', 's4', 's5'], ['refunds', 'r1 r2 r3', 'r4', 'r5']],
        marks=[{'row': 0, 'col': 1, 'n': 1}, {'row': 2, 'col': 3, 'n': 2}]),
    'stable_split': diagram('table', after=1,
        caption='Three ids from the example, the number each hashes to (its hash % 100), and the split that number lands in. For ticket-1001, a month later and 500 questions on, the number is still 72, so it is still in test.',
        callouts=['0 to 59 is dev, 60 to 79 test, 80 to 99 holdout', 'The same id gives the same number every time, so a question never moves'],
        columns=['id', 'hash % 100', 'split'], pill=2,
        rows=[['ticket-1001', '72', 'test'], ['ticket-1002', '29', 'dev'], ['ticket-1003', '88', 'holdout'], ['ticket-1001, a month later', '72', 'test']],
        marks=[{'row': 0, 'col': 2, 'n': 1}, {'row': 3, 'col': 1, 'n': 2}]),
    'route_request': diagram('flow', after=0,
        caption='The 90/10 split from the example: requests arrive at the endpoint, which sends 90 in 100 to version 3 and 10 in 100 to version 4, the canary. Rolling back is setting the canary to 0.',
        callouts=['The endpoint splits traffic by percentage', 'The canary: a small share, watched through its traces and evals'],
        nodes=[{'label': 'Requests', 'word': 'all traffic'}, {'label': 'Endpoint', 'word': 'the split', 'n': 1}],
        branches=[{'label': 'support_agent-3', 'share': '90 in 100'}, {'label': 'support_agent-4', 'share': '10 in 100', 'now': True, 'n': 2}]),
    # ---- Run
    'slowest_chain': diagram('tree', after=0,
        caption='The example trace as the tool shows it: the tree on the left is which step ran inside which, the bars are when and for how long. A parent\'s bar covers its children\'s. The filled bars are the critical path: the slowest child at every level.',
        callouts=['agent_run, 4200 ms: the whole request', 'tool:search, 3100 ms: the slowest of the run\'s three children', 'http_get, 2900 ms: the slowest inside the tool call, so the thing to fix'],
        unit='ms', max=4200,
        rows=[{'name': 'agent_run', 'depth': 0, 'start': 0, 'size': 4200, 'hot': True, 'n': 1}, {'name': 'plan', 'depth': 1, 'start': 0, 'size': 600},
              {'name': 'tool:search', 'depth': 1, 'start': 600, 'size': 3100, 'hot': True, 'n': 2}, {'name': 'http_get', 'depth': 2, 'start': 700, 'size': 2900, 'hot': True, 'n': 3},
              {'name': 'answer', 'depth': 1, 'start': 3800, 'size': 400}]),
    'tokens_by_agent': diagram('tree', after=1,
        caption='The example\'s team run as bars, but the width is tokens, not time: each model call sits under the helper that made it. The researcher\'s two calls add up to 6400; the writer\'s one to 1200.',
        callouts=['researcher: 3400 plus 3000 tokens, the helper to look at first', 'writer: 1200 tokens'],
        unit='tokens', max=7600,
        rows=[{'name': 'team run', 'depth': 0, 'start': 0, 'size': 7600}, {'name': 'researcher', 'depth': 1, 'start': 0, 'size': 3400, 'hot': True, 'n': 1},
              {'name': 'writer', 'depth': 1, 'start': 3400, 'size': 1200, 'n': 2}, {'name': 'researcher', 'depth': 1, 'start': 4600, 'size': 3000, 'hot': True}]),
    'circuit_breaker': diagram('graph', after=1,
        caption='The three states as a state diagram: the boxes are the states, the arrows are what moves the breaker between them. It starts closed.',
        callouts=['Closed: calls go through, failures are counted', 'Open: calls are blocked and the fallback answers', 'Half-open: one trial call decides which way it goes'],
        nodes=[{'id': 'closed', 'label': 'Closed', 'sub': 'calls go through', 'at': [0, 0], 'now': True, 'n': 1},
               {'id': 'open', 'label': 'Open', 'sub': 'fallback answers', 'at': [2, 0], 'n': 2},
               {'id': 'half', 'label': 'Half-open', 'sub': 'one trial call', 'at': [1, 1], 'n': 3}],
        edges=[{'from': 'closed', 'to': 'open', 'label': 'repeated failures'}, {'from': 'open', 'to': 'half', 'label': 'after a cooldown'},
               {'from': 'half', 'to': 'closed', 'label': 'success closes it'}, {'from': 'half', 'to': 'open', 'label': 'failure re-opens it', 'bend': 1}]),
    'burn_rate': diagram('chart', after=1,
        caption='The month\'s error budget, day by day. The dashed line is a steady burn that lasts all 30 days. At the example\'s burn rate of 14.4, the budget is gone on day 3.',
        callouts=['Burning at 14.4 times the steady rate, the budget runs out on day 3: page someone', 'Where a steady burn reaches zero: day 30'],
        x={'label': 'day', 'max': 30, 'ticks': [1, 10, 20, 30]}, y={'label': 'budget left', 'max': 100, 'ticks': [0, 50, 100], 'unit': '%'},
        lines=[{'points': [[1, 100], [30, 0]], 'dashed': True, 'label': 'steady burn'}, {'points': [[1, 100], [2, 50], [3, 0]], 'hot': True, 'label': 'actual'}],
        marks=[{'x': 3, 'y': 0, 'n': 1, 'label': 'gone on day 3'}, {'x': 30, 'y': 0, 'n': 2}]),
    'token_bucket': diagram('chart', after=1,
        caption='The example over the first two seconds: five requests at once empty the bucket, the sixth waits until the refill hands it a token half a second later, and the bucket climbs again at 2 a second.',
        callouts=['Five requests at once: the bucket goes from 5 to 0', 'The sixth request gets the first refilled token at 0.5 seconds'],
        x={'label': 'seconds', 'max': 2, 'ticks': [0, 0.5, 1, 1.5, 2]}, y={'label': 'tokens in the bucket', 'max': 5, 'ticks': [0, 5]},
        lines=[{'points': [[0, 5], [0.02, 0], [0.5, 1], [0.52, 0], [2, 2.96]], 'hot': True, 'label': 'tokens'}],
        marks=[{'x': 0.02, 'y': 0, 'n': 1}, {'x': 0.5, 'y': 1, 'n': 2}]),
    # ---- Security
    'sweep_memory': diagram('table', after=2,
        caption='The nightly clean-up from the example, on day 100: each memory\'s kind decides how long it is kept, and a person who asked to be forgotten loses everything.',
        callouts=['An address kept 30 days, saved on day 40: expired and deleted', 'Health details are never stored, so this one is deleted whoever saved it', 'cy asked to be forgotten: every memory goes'],
        columns=['user', 'kind', 'saved', 'keep', 'day 100'], pill=4,
        rows=[['ana', 'preference', 'day 20', '365 days', 'keep'], ['ana', 'address', 'day 40', '30 days', 'expire'],
              ['bo', 'health', 'day 95', 'never', 'delete'], ['cy', 'preference', 'day 90', 'forgotten', 'delete']],
        marks=[{'row': 1, 'col': 4, 'n': 1}, {'row': 2, 'col': 4, 'n': 2}, {'row': 3, 'col': 4, 'n': 3}]),
    # ---- Platform track
    'field_status': diagram('flow', after=1,
        caption='One field, policy_name, going past the five stops from the example: the YAML says it, the check allows it, the runbook reads it with a default, the module turns it into an id, and the provider gets that id. So it is SUPPORTED.',
        callouts=['The YAML: what the team asked for', 'The check: a known text field, so valid', 'The runbook: reads it, with "Personal Compute" as the default if it is missing', 'The provider: gets the policy\'s id, so the field reached the end'],
        nodes=[{'label': 'YAML', 'word': 'asked', 'n': 1}, {'label': 'Check', 'word': 'valid', 'n': 2}, {'label': 'Runbook', 'word': 'reads it', 'now': True, 'n': 3},
               {'label': 'Module', 'word': 'passes its id'}, {'label': 'Provider', 'word': 'policy_id', 'n': 4}],
        detail={'at': 2, 'rows': [['try(c.policy_name,', ''], ['  "Personal Compute")', '']]}),
    'runs_after': diagram('graph', after=1,
        caption='The example\'s stacks and what each waits for. When network changes, every stack downstream of it runs, in an order that respects the arrows: monitoring and workspace first, then catalogs, then jobs.',
        callouts=['network changed, so the run starts here', 'jobs waits for workspace and catalogs, so it goes last'],
        nodes=[{'id': 'network', 'label': 'network', 'sub': 'changed', 'at': [0, 0.5], 'now': True, 'n': 1},
               {'id': 'workspace', 'label': 'workspace', 'at': [1, 0]}, {'id': 'monitoring', 'label': 'monitoring', 'at': [1, 1]},
               {'id': 'catalogs', 'label': 'catalogs', 'at': [2, 0]}, {'id': 'jobs', 'label': 'jobs', 'at': [3, 0.5], 'n': 2}],
        edges=[{'from': 'network', 'to': 'workspace'}, {'from': 'network', 'to': 'monitoring'}, {'from': 'workspace', 'to': 'catalogs'},
               {'from': 'workspace', 'to': 'jobs'}, {'from': 'catalogs', 'to': 'jobs'}]),
}
