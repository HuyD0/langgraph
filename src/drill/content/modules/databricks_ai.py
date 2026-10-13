"""Agent Bricks, Genie and MCP: Databricks' ready-made agents, data questions in plain words, and the tools agents can call."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('databricks-ai', 'Agent Bricks, Genie and MCP', "Databricks' ready-made agents, data questions in plain words, and the tools agents can call.")

lesson(MODULE, 'choose_brick',
    title='Agent Bricks: start from a template',
    learn=[
        "**Agent Bricks** is Databricks' platform for building agents. The quickest start is a **template**: a ready-made agent for a common job. You describe the task in plain words and point it at your data. It builds the agent, **evaluates** it (scores its answers with MLflow judges, the LLM graders from the Evaluate phase) and tunes it with feedback from your experts.",
        'It runs on **serverless** compute (Databricks starts and stops the machines for you) and is governed by **Unity Catalog**, so the agent only reads data its users are allowed to read.',
        'Four templates. **Knowledge Assistant** answers questions from your documents, with **citations** (links to the passage it used). **Information Extraction** turns documents such as PDFs and emails into fields: one row per document in a table. **Supervisor Agent** (first called Multi-Agent Supervisor) coordinates several agents, Genie Agents and tools such as MCP servers. **Custom LLM** does one text task, such as summarising or classifying, with your own instructions.',
        "Some are **Beta** (an early release that can still change) or **legacy** (kept for old work, not for new). Knowledge Assistant and Supervisor Agent are generally available (ready for production). Custom LLM is legacy and Beta; for new text tasks Databricks now points to AI Functions such as `ai_query`. Check your workspace's Previews page before you plan on one.",
    ],
    example=example('Four tasks, four templates', """task                            template
answer HR policy questions      Knowledge Assistant
pull totals out of invoices     Information Extraction
sum up each support call        Custom LLM
send questions to the sales     Supervisor Agent
  agent or the HR agent"""),
    check=question(
        'A team has 3,000 supplier contracts as PDFs. They want a table with each contract\'s supplier, end date and price. Which template fits?',
        ['Knowledge Assistant', 'Information Extraction', 'Custom LLM'],
        answer=1,
        why='They want fields in a table, one row per contract. A Knowledge Assistant answers one question at a time, like "when does the Fernhill contract end?", and fills no table.',
    ),
    angle=angle(
        pattern='Rules checked in order',
        text='The big idea: pick the template from what the task needs, and check the most specific need first. Your code walks the tasks and checks rules in order with `if`, `elif` and `else`, so only the first match counts. Several agents comes first, because a supervisor can use the other kinds as helpers. Documents plus fields comes before documents alone, since both start from documents. Anything left is a single text task.',
        say='"I pick the template from the shape of the task: several agents need a supervisor, fields from documents is extraction, questions over documents is a knowledge assistant, and a single text job is a custom LLM."',
        classic=None,
    ),
    stack=stack('Agent Bricks: a Knowledge Assistant, in the workspace', """# Agents (left menu) > Create Agent
#   > Knowledge Assistant
# Name:     hr-helper
# Describe: "Answer staff questions
#            about HR policy. Cite the
#            policy page you used."
# Knowledge source: a Unity Catalog
#   volume of files, such as
#   /Volumes/main/hr/policies
# Create, then chat with it in the
# Playground and add expert feedback.
# It ends up as a serving endpoint
# (a web address your app calls)."""),
    exercise=exercise(
        title='Pick the Template',
        topic='agent-bricks',
        difficulty='easy',
        fn='choose_brick',
        prompt="""`tasks` is a list of jobs a team wants an agent for. Each one is a dict like:

`{"name": "hr-helper", "from_documents": True, "output_fields": False, "several_agents": False}`

- `from_documents`: the agent works from documents, like PDFs or emails.
- `output_fields`: the result is fields for a table, not an answer in sentences.
- `several_agents`: the job needs several agents or tools working together.

For each task, check these rules in order and use the first one that matches:

- `several_agents` is True: `"Supervisor Agent"`.
- `from_documents` and `output_fields` are both True: `"Information Extraction"`.
- `from_documents` is True: `"Knowledge Assistant"`.
- Otherwise: `"Custom LLM"`.

Return a list with one `[name, choice]` pair per task, in the same order as `tasks`.""",
        pattern='Rules checked in order with if, elif and else, once for each item in a list.',
        target='one pass over the tasks',
        realworld="Picking the template is the first screen under Agents > Create Agent, and a wrong pick costs a rebuild: an Information Extraction agent gives you a table, not a chatbot. A Supervisor Agent can call a Knowledge Assistant and a Genie Agent as its helpers, so teams often build those first and add the supervisor last.",
        starter="""def choose_brick(tasks):
    # your code here
    pass
""",
        solution="""def choose_brick(tasks):
    picks = []
    for task in tasks:
        if task["several_agents"]:
            choice = "Supervisor Agent"
        elif task["from_documents"] and task["output_fields"]:
            choice = "Information Extraction"
        elif task["from_documents"]:
            choice = "Knowledge Assistant"
        else:
            choice = "Custom LLM"
        picks.append([task["name"], choice])
    return picks
""",
        cases=[
            case([
                {'name': 'hr-helper', 'from_documents': True, 'output_fields': False, 'several_agents': False},
                {'name': 'invoice-reader', 'from_documents': True, 'output_fields': True, 'several_agents': False},
                {'name': 'call-summary', 'from_documents': False, 'output_fields': False, 'several_agents': False},
            ], expected=[
                ['hr-helper', 'Knowledge Assistant'],
                ['invoice-reader', 'Information Extraction'],
                ['call-summary', 'Custom LLM'],
            ], sample=True),
            case([], expected=[]),
            case([
                {'name': 'front-desk', 'from_documents': True, 'output_fields': True, 'several_agents': True},
            ], expected=[['front-desk', 'Supervisor Agent']]),
            case([
                {'name': 'ticket-tagger', 'from_documents': False, 'output_fields': True, 'several_agents': False},
                {'name': 'policy-faq', 'from_documents': True, 'output_fields': False, 'several_agents': False},
            ], expected=[['ticket-tagger', 'Custom LLM'], ['policy-faq', 'Knowledge Assistant']]),
            case([
                {'name': 'sales-and-hr', 'from_documents': False, 'output_fields': False, 'several_agents': True},
                {'name': 'contract-table', 'from_documents': True, 'output_fields': True, 'several_agents': False},
                {'name': 'email-fields', 'from_documents': True, 'output_fields': True, 'several_agents': False},
            ], expected=[
                ['sales-and-hr', 'Supervisor Agent'],
                ['contract-table', 'Information Extraction'],
                ['email-fields', 'Information Extraction'],
            ]),
        ],
        guided="""def choose_brick(tasks):
    # Replace every ___ with real code, then run the tests.

    picks = []
    for task in tasks:
        # Step 1: several agents always means a supervisor.
        if ___:
            choice = "Supervisor Agent"

        # Step 2: from documents AND fields for a table.
        elif ___:
            choice = "Information Extraction"

        # Documents alone: answer questions from them.
        elif task["from_documents"]:
            choice = ___

        # Anything else is one text task.
        else:
            choice = "Custom LLM"

        # Step 3: add the pair [name, choice].
        picks.append(___)

    return picks
""",
        fills=['task["several_agents"]', 'task["from_documents"] and task["output_fields"]', '"Knowledge Assistant"', '[task["name"], choice]'],
        concepts=[
            [
                'if, elif, else',
                'Python tries each condition from the top and runs only the first one that is True. `else` runs when none were.',
                """n = 7
if n > 10: size = 'big'
elif n > 5: size = 'middle'   # this one
else: size = 'small'""",
            ],
            [
                'A True or False field',
                '`task["several_agents"]` is already True or False, so it can go straight after `if`. No need for `== True`.',
                """pet = {'name': 'Rex', 'hungry': True}
if pet['hungry']: print('feed Rex')""",
            ],
            [
                'Two conditions with and',
                '`a and b` is True only when both sides are True.',
                """sunny = True
warm = False
sunny and warm   # False""",
            ],
            [
                'A list of pairs',
                'Each item you append can itself be a short list.',
                """pairs = []
pairs.append(['ana', 3])
pairs   # [['ana', 3]]""",
            ],
        ],
        byhand='hr-helper: several_agents is False. from_documents is True but output_fields is False, so not extraction. from_documents is True, so "Knowledge Assistant". invoice-reader: not several agents; from_documents and output_fields are both True, so "Information Extraction". call-summary: no rule matches, so "Custom LLM". Return [["hr-helper", "Knowledge Assistant"], ["invoice-reader", "Information Extraction"], ["call-summary", "Custom LLM"]].',
        why='One pass over the tasks, with at most three quick checks each.',
        gotchas=[
            [
                'Checking documents before fields',
                'If the "from documents" rule comes first, every extraction task becomes a Knowledge Assistant, because it matches first. Put the rule that needs more things to be True above the one that needs fewer.',
            ],
            [
                'Building on a Beta',
                'A Beta template can change or need an admin to turn it on. Check the workspace Previews page, and keep your test questions so you can rerun them when it changes.',
            ],
        ],
    ),
)

lesson(MODULE, 'genie_benchmark',
    title='Genie: questions about your data in plain words',
    learn=[
        'A **Genie Agent** (called a Genie space until 2026) lets business users ask questions about data in plain words. Genie writes the **SQL** (the language for asking a database questions) over the Unity Catalog tables the author picked, runs it on a **SQL warehouse** (the compute that runs SQL) and shows a table or chart. It runs with the asker\'s own permissions, so people only see rows they are allowed to see.',
        'An author improves an agent with plain-text **instructions**, **example SQL queries** and **trusted assets**: example queries with **parameters** (blanks Genie fills in from the question) and SQL functions. When Genie answers with a trusted asset, the answer is marked as verified.',
        '**Benchmarks** are test questions, each with a SQL answer you trust. A run asks Genie each question fresh and compares the rows it got with the rows your SQL gives. The same rows in a different order still count as right. **Accuracy** is the share that matched. Benchmarks only measure: Genie does not learn from them.',
        "**Genie One** is the newer single chat across all your data, built on the Genie Agents your teams curate. Benchmarks in Agent mode are graded by an LLM judge instead; the lesson \"Checking your LLM judge\" shows how to trust one.",
    ],
    example=example('One benchmark run, three questions', """question               expected        got             result
orders in March?       [[412]]         [[412]]         pass
top 2 regions          [[North],       [[South],       pass:
                        [South]]        [North]]       order only
refunds last week?     [[17]]          [[19]]          fail
accuracy: 2 of 3 = 66.7%"""),
    check=question(
        'Your Genie Agent scores 70% on its benchmarks. What should you do to raise the score?',
        [
            'Add the failing questions again as more benchmarks, so Genie learns them',
            'Add instructions, example SQL or trusted assets that cover what the failures got wrong, then rerun',
            'Rerun the same benchmarks until the score goes up',
        ],
        answer=1,
        why='Benchmarks only measure. Genie does not learn from them, so fix what Genie reads (instructions and examples), then rerun the same questions to see if accuracy moved. Rerunning alone only gives a lucky number.',
    ),
    angle=angle(
        pattern='Compare sorted copies',
        text='The big idea: a benchmark run counts how many answers match a trusted SQL answer, where row order does not matter. Your code walks the results. For each one it makes sorted copies of the expected rows and of the rows Genie got, so order no longer matters, and compares them with `==`. A match adds 1 to passed; a miss goes on the failed list, in order. The percent is passed divided by the total, times 100, rounded to 1 place.',
        say='"I compare each answer\'s rows after sorting both, because the same rows in a different order are still right. Then I report the pass rate and the questions that failed, so we know what to fix."',
        classic=None,
    ),
    stack=stack('Databricks SQL: a trusted asset Genie can use', """-- A SQL function with a parameter.
-- Genie fills in the month from the
-- question, and marks the answer as
-- verified.
CREATE OR REPLACE FUNCTION
  main.sales.orders_in_month(
    month_start DATE)
RETURNS TABLE (orders BIGINT)
COMMENT 'Orders placed in one month'
RETURN
  SELECT COUNT(*) AS orders
  FROM main.sales.orders
  WHERE date_trunc('MONTH', order_date)
        = month_start;
-- Askers need EXECUTE on it."""),
    exercise=exercise(
        title='Score the Genie Benchmarks',
        topic='genie',
        difficulty='easy',
        fn='genie_benchmark',
        prompt="""`results` is one benchmark run on a Genie Agent. Each item is a dict like:

`{"question": "Top 2 regions?", "expected": [["North", 9100], ["South", 8700]], "got": [["South", 8700], ["North", 9100]]}`

- `expected`: the rows your trusted SQL answer gives. Each row is a list.
- `got`: the rows Genie's own SQL gave.

A question passes when `got` has the same rows as `expected`, in any order. Compare sorted copies: `sorted(rows)` gives a new list in order and leaves the original alone.

Return `[percent, failed]`:

- `percent`: the share of questions that passed, times 100, rounded to 1 decimal place.
- `failed`: the `question` of every one that failed, in the same order as `results`.

If `results` is empty, return `[0, []]`.""",
        pattern='Normalise, then compare: sort both sides so order cannot cause a false failure, and count matches.',
        target='one pass over the results',
        realworld="This is a Chat mode run on a Genie Agent's Benchmarks tab. Each question runs as a new conversation, and Genie rates it good when its result set matches the SQL answer, even sorted differently. Extra columns or an empty result count as bad. Teams rerun the same benchmarks after every change to instructions or examples, to see whether accuracy moved.",
        starter="""def genie_benchmark(results):
    # your code here
    pass
""",
        solution="""def genie_benchmark(results):
    if len(results) == 0:
        return [0, []]
    passed = 0
    failed = []
    for item in results:
        if sorted(item["expected"]) == sorted(item["got"]):
            passed += 1
        else:
            failed.append(item["question"])
    percent = round(passed * 100 / len(results), 1)
    return [percent, failed]
""",
        cases=[
            case([
                {'question': 'How many orders in March?', 'expected': [[412]], 'got': [[412]]},
                {'question': 'Top 2 regions by sales?', 'expected': [['North', 9100], ['South', 8700]], 'got': [['South', 8700], ['North', 9100]]},
                {'question': 'How many refunds last week?', 'expected': [[17]], 'got': [[19]]},
            ], expected=[66.7, ['How many refunds last week?']], sample=True),
            case([], expected=[0, []]),
            case([
                {'question': 'Open tickets?', 'expected': [[38]], 'got': [[38]]},
                {'question': 'Stores in Leeds?', 'expected': [['Kirkgate'], ['Briggate']], 'got': [['Briggate'], ['Kirkgate']]},
            ], expected=[100.0, []]),
            case([
                {'question': 'Best seller?', 'expected': [['Ada Moss', 3]], 'got': [['Ada Moss', 3, 'London']]},
                {'question': 'Late deliveries?', 'expected': [[5]], 'got': []},
                {'question': 'Active users?', 'expected': [[1200]], 'got': [[1200]]},
            ], expected=[33.3, ['Best seller?', 'Late deliveries?']]),
            case([
                {'question': 'Items sold today?', 'expected': [['tea'], ['tea'], ['cake']], 'got': [['cake'], ['tea']]},
                {'question': 'Teams?', 'expected': [['blue'], ['green']], 'got': [['green'], ['blue']]},
                {'question': 'Returns?', 'expected': [[0]], 'got': [[0]]},
                {'question': 'New staff?', 'expected': [['Tom Reed']], 'got': [['Tom Reed']]},
            ], expected=[75.0, ['Items sold today?']]),
        ],
        guided="""def genie_benchmark(results):
    # Replace every ___ with real code, then run the tests.

    # No questions: nothing to score.
    if len(results) == 0:
        return [0, []]

    passed = 0
    failed = []
    for item in results:
        # Step 1: same rows in any order?
        # Compare sorted copies of both.
        if ___:
            passed += 1
        else:
            # Step 2: remember which question failed.
            ___

    # Step 3: passed out of all, times 100,
    # rounded to 1 place.
    percent = ___
    return [percent, failed]
""",
        fills=['sorted(item["expected"]) == sorted(item["got"])', 'failed.append(item["question"])', 'round(passed * 100 / len(results), 1)'],
        concepts=[
            [
                'sorted makes an ordered copy',
                '`sorted(a_list)` returns a new list in order. Lists of lists sort by their first item, then the next.',
                """sorted([['b', 2], ['a', 9]])
# [['a', 9], ['b', 2]]""",
            ],
            [
                'Comparing lists with ==',
                '`==` on two lists is True when they hold the same items in the same order.',
                """[1, 2] == [1, 2]   # True
[1, 2] == [2, 1]   # False""",
            ],
            [
                'A percent',
                'Divide the part by the whole, then times 100. `round(x, 1)` keeps 1 decimal place.',
                """round(2 * 100 / 3, 1)   # 66.7""",
            ],
            [
                'Guarding against an empty list',
                'Dividing by `len([])`, which is 0, is an error. Check for the empty case first and return early.',
                """if len(scores) == 0:
    return 0""",
            ],
        ],
        byhand='Three questions. Orders in March: [[412]] and [[412]] match, so passed is 1. Top 2 regions: sorted, both are [["North", 9100], ["South", 8700]], so passed is 2. Refunds: [[17]] and [[19]] differ, so add "How many refunds last week?" to failed. 2 of 3 is 2 times 100 divided by 3, which is 66.66..., rounded to 66.7. Return [66.7, ["How many refunds last week?"]].',
        why='One pass over the results; each one sorts two short lists of rows.',
        gotchas=[
            [
                'Comparing without sorting',
                'SQL gives no promised row order unless the query says ORDER BY, so the same answer can come back in a different order. Comparing the lists as they are fails right answers.',
            ],
            [
                'Teaching to the test',
                'If you copy every benchmark question into the example SQL, the score goes up but real questions do not get better. Keep some benchmarks that are worded differently from any example.',
            ],
        ],
    ),
)

lesson(MODULE, 'managed_mcp_urls',
    title='Managed MCP servers: tools agents can call',
    learn=[
        '**MCP** (Model Context Protocol) is a standard way for an agent to find and call tools on a **server** (a program that waits for requests). The agent asks the server for its list of tools, then calls one by name with arguments. It works the same way whatever the server is.',
        "Databricks runs **managed MCP servers** for you, so you only need a URL. The current ones live in the `system.ai` schema behind **Unity Gateway** (Databricks' AI gateway), at `https://<workspace>/ai-gateway/mcp-services/<name>`. `system.ai.genie_one_mcp` answers questions across your data with Genie One, through its `genie_ask` tool.",
        'Others in `system.ai`: `system.ai.sandbox` runs Python, SQL or shell in an isolated box with no internet (the lesson "An agent that runs code" covers it), `system.ai.dbsql` runs SQL you already wrote, and `system.ai.web_search` searches the web. Each is a Unity Catalog **securable** (something you grant access to). These three are **Beta**: an account admin turns on the Unity Gateway beta on the Previews page.',
        'Older **workspace endpoints** still work: one Genie Agent at `/api/2.0/mcp/genie/{space_id}`, AI Search indexes (AI Search was called Vector Search) at `/api/2.0/mcp/ai-search/{catalog}/{schema}`, and a Unity Catalog function at `/api/2.0/mcp/functions/{catalog}/{schema}/{function}`. Every call runs with the caller\'s Unity Catalog permissions, so an agent can only reach what its identity can.',
    ],
    example=example('Four tools, four URLs', """host: adb-1234.5.azuredatabricks.net

service  system.ai.genie_one_mcp
  /ai-gateway/mcp-services/system.ai.genie_one_mcp
genie    space 01f0aa
  /api/2.0/mcp/genie/01f0aa
ai-search  main / docs
  /api/2.0/mcp/ai-search/main/docs
functions  main / tools / lookup_order
  /api/2.0/mcp/functions/main/tools/lookup_order"""),
    check=question(
        'An agent calls the Genie One MCP server as Priya, who cannot read the salaries table. Someone asks it for the average salary by team. What happens?',
        [
            'Genie answers, because the MCP server has its own admin access',
            "Genie can't read that table for Priya, so it can't answer from it",
            'The server copies the table to the agent first, then answers',
        ],
        answer=1,
        why="Managed MCP calls run with the caller's Unity Catalog permissions. That is why each agent should have its own identity with only the access it needs.",
    ),
    angle=angle(
        pattern='Build a string per kind',
        text='The big idea: every managed MCP server is just a URL on your workspace, made from a fixed path and a few names. Your code walks the tools in order. For each one it checks the kind with `if` and `elif`, joins the fixed path and the tool\'s names with `+` and `"/"`, and puts `"https://"` and the host in front. One URL per tool, in the same order.',
        say='"Each managed MCP server is a URL on the workspace. New agents use the system.ai services through Unity Gateway, older ones the workspace endpoints. Either way, every call runs with the caller\'s own permissions."',
        classic=None,
    ),
    stack=stack('databricks-mcp: connect and list the tools', """# pip install databricks-mcp databricks-sdk
from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksMCPClient

w = WorkspaceClient()
url = (w.config.host
       + "/ai-gateway/mcp-services/"
       + "system.ai.genie_one_mcp")

client = DatabricksMCPClient(
    server_url=url,
    workspace_client=w)

for tool in client.list_tools():
    print(tool.name, tool.inputSchema)

# Then, with the arguments that
# tool's inputSchema asks for:
# client.call_tool(name, arguments)"""),
    exercise=exercise(
        title='Build the MCP Server URLs',
        topic='mcp',
        difficulty='easy',
        fn='mcp_urls',
        prompt="""Your function gets two things:

- `host`: the workspace's address, like `"adb-1234.5.azuredatabricks.net"`.
- `tools`: the MCP servers an agent needs. Each is a dict with a `"kind"` and the names that kind needs.

Build each server's path from its kind:

- `"service"`, with `"name"`: `/ai-gateway/mcp-services/` then the name, like `/ai-gateway/mcp-services/system.ai.genie_one_mcp`.
- `"genie"`, with `"space_id"`: `/api/2.0/mcp/genie/` then the space id.
- `"ai-search"`, with `"catalog"` and `"schema"`: `/api/2.0/mcp/ai-search/` then catalog, `/`, schema.
- `"functions"`, with `"catalog"`, `"schema"` and `"function"`: `/api/2.0/mcp/functions/` then catalog, `/`, schema, `/`, function.

Each full URL is `"https://"` + host + path. Return the URLs in the same order as `tools`.""",
        pattern='Choose a template by kind, then fill it in by joining strings.',
        target='one pass over the tools',
        realworld='This is the setup step for any agent that uses Databricks tools: a LangGraph agent, or a coding agent such as Claude Code or Cursor, takes the same URLs. Find each service under Unity Gateway > MCPs, and grant the agent\'s identity only the ones it needs.',
        starter="""def mcp_urls(host, tools):
    # your code here
    pass
""",
        solution="""def mcp_urls(host, tools):
    urls = []
    for tool in tools:
        kind = tool["kind"]
        if kind == "service":
            path = "/ai-gateway/mcp-services/" + tool["name"]
        elif kind == "genie":
            path = "/api/2.0/mcp/genie/" + tool["space_id"]
        elif kind == "ai-search":
            path = "/api/2.0/mcp/ai-search/" + tool["catalog"] + "/" + tool["schema"]
        else:
            path = ("/api/2.0/mcp/functions/" + tool["catalog"] + "/"
                    + tool["schema"] + "/" + tool["function"])
        urls.append("https://" + host + path)
    return urls
""",
        cases=[
            case('adb-1234.5.azuredatabricks.net', [
                {'kind': 'service', 'name': 'system.ai.genie_one_mcp'},
                {'kind': 'genie', 'space_id': '01f0aa'},
                {'kind': 'ai-search', 'catalog': 'main', 'schema': 'docs'},
                {'kind': 'functions', 'catalog': 'main', 'schema': 'tools', 'function': 'lookup_order'},
            ], expected=[
                'https://adb-1234.5.azuredatabricks.net/ai-gateway/mcp-services/system.ai.genie_one_mcp',
                'https://adb-1234.5.azuredatabricks.net/api/2.0/mcp/genie/01f0aa',
                'https://adb-1234.5.azuredatabricks.net/api/2.0/mcp/ai-search/main/docs',
                'https://adb-1234.5.azuredatabricks.net/api/2.0/mcp/functions/main/tools/lookup_order',
            ], sample=True),
            case('adb-1234.5.azuredatabricks.net', [], expected=[]),
            case('dbc-7f3e.cloud.databricks.com', [
                {'kind': 'service', 'name': 'system.ai.sandbox'},
                {'kind': 'service', 'name': 'system.ai.dbsql'},
            ], expected=[
                'https://dbc-7f3e.cloud.databricks.com/ai-gateway/mcp-services/system.ai.sandbox',
                'https://dbc-7f3e.cloud.databricks.com/ai-gateway/mcp-services/system.ai.dbsql',
            ]),
            case('adb-99.1.azuredatabricks.net', [
                {'kind': 'functions', 'catalog': 'system', 'schema': 'ai', 'function': 'python_exec'},
            ], expected=['https://adb-99.1.azuredatabricks.net/api/2.0/mcp/functions/system/ai/python_exec']),
            case('adb-99.1.azuredatabricks.net', [
                {'kind': 'ai-search', 'catalog': 'hr', 'schema': 'policies'},
                {'kind': 'genie', 'space_id': '01f1bc'},
                {'kind': 'genie', 'space_id': '01f2de'},
            ], expected=[
                'https://adb-99.1.azuredatabricks.net/api/2.0/mcp/ai-search/hr/policies',
                'https://adb-99.1.azuredatabricks.net/api/2.0/mcp/genie/01f1bc',
                'https://adb-99.1.azuredatabricks.net/api/2.0/mcp/genie/01f2de',
            ]),
        ],
        guided="""def mcp_urls(host, tools):
    # Replace every ___ with real code, then run the tests.

    urls = []
    for tool in tools:
        kind = tool["kind"]

        if kind == "service":
            path = "/ai-gateway/mcp-services/" + tool["name"]

        # Step 1: one Genie Agent, by its space id.
        elif kind == "genie":
            path = "/api/2.0/mcp/genie/" + ___

        # Step 2: catalog, a slash, then schema.
        elif kind == "ai-search":
            path = "/api/2.0/mcp/ai-search/" + ___

        # Anything else is "functions".
        else:
            path = ("/api/2.0/mcp/functions/" + tool["catalog"] + "/"
                    + tool["schema"] + "/" + tool["function"])

        # Step 3: "https://", then the host, then the path.
        urls.append(___)

    return urls
""",
        fills=['tool["space_id"]', 'tool["catalog"] + "/" + tool["schema"]', '"https://" + host + path'],
        concepts=[
            [
                'Checking a string with ==',
                '`kind == "genie"` is True only when the text matches exactly, capital letters and dashes too.',
                """kind = 'ai-search'
kind == 'ai-search'   # True
kind == 'AI-search'   # False""",
            ],
            [
                'Joining strings with +',
                '`+` joins strings end to end. Add the `"/"` yourself; it is not added for you.',
                """'main' + '/' + 'docs'   # 'main/docs'""",
            ],
            [
                'Dicts with different keys',
                'Each kind of tool carries only the keys it needs, so read a key only inside the branch that knows it is there.',
                """tool = {'kind': 'genie', 'space_id': '01f0aa'}
tool['space_id']   # '01f0aa'
# tool['catalog'] would be a KeyError""",
            ],
        ],
        byhand='Tool 1 is a service named system.ai.genie_one_mcp, so the path is /ai-gateway/mcp-services/system.ai.genie_one_mcp. Tool 2 is genie with space 01f0aa: /api/2.0/mcp/genie/01f0aa. Tool 3 is ai-search, main and docs: /api/2.0/mcp/ai-search/main/docs. Tool 4 is functions, main, tools and lookup_order: /api/2.0/mcp/functions/main/tools/lookup_order. Put "https://adb-1234.5.azuredatabricks.net" in front of each, and return the four URLs in that order.',
        why='One pass over the tools, joining a few short strings for each.',
        gotchas=[
            [
                'The old Genie One URL is going away',
                '`/api/2.0/mcp/genie`, with no space id, was the Beta Genie One endpoint. It is deprecated and stops working on 31 October 2026. Move to `system.ai.genie_one_mcp`.',
            ],
            [
                'Workspace endpoints skip the gateway',
                'Calls to `/api/2.0/mcp/...` bypass Unity Gateway: they are missing from its tracing tables, and its grants and guardrails for MCP do not apply. Only the permissions on the tables, functions and indexes underneath protect them. An admin must also turn on Managed MCP Servers on the workspace Previews page.',
            ],
            [
                'python_exec is the old code runner',
                'Older examples call `system.ai.python_exec` through the functions server to run Python. New agents use `system.ai.sandbox` instead.',
            ],
        ],
    ),
)
