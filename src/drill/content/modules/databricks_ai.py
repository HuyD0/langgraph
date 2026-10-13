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
        'Older **workspace endpoints** still work: one Genie Agent at `/api/2.0/mcp/genie/{space_id}`, Databricks Vector Search indexes (renamed Databricks AI Search in 2026; not the same as Azure AI Search from Microsoft) at `/api/2.0/mcp/ai-search/{catalog}/{schema}`, and a Unity Catalog function at `/api/2.0/mcp/functions/{catalog}/{schema}/{function}`. Every call runs with the caller\'s Unity Catalog permissions, so an agent can only reach what its identity can.',
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

lesson(MODULE, 'callable_tools',
    title='Unity Catalog functions: tools with permissions',
    learn=[
        'The lesson "Tools from Unity Catalog" showed how a function becomes a tool the model can read. This lesson is about the other half: who is allowed to run it. A **Unity Catalog function** lives at `catalog.schema.function`, like `main.support.lookup_order`, the same three parts as a table.',
        'There are two kinds. A **SQL function** says `LANGUAGE SQL` and then `RETURN` with one expression or one query. A **Python function** says `LANGUAGE PYTHON`, puts its code between two `$$` marks, and declares its **return type** (the kind of value it gives back, like `STRING`). If the Python code needs extra packages, an `ENVIRONMENT` clause lists them (from PyPI, volumes or URLs), and then `environment_version` must be set too.',
        'Write a `COMMENT` on the function and on each parameter. Those comments become the tool description the model reads, so a vague comment leads to wrong tool picks.',
        'To **create** a function you need `USE CATALOG`, `USE SCHEMA` and `CREATE FUNCTION` on the schema. To **call** one you need `EXECUTE` on the function, plus `USE CATALOG` and `USE SCHEMA`. `EXECUTE` granted on a schema or a catalog flows down to every function inside, the same idea as in "Unity Catalog privileges flow down".',
        "Agents call functions through `UCFunctionToolkit` or the managed MCP functions server, `https://<host>/api/2.0/mcp/functions/{catalog}/{schema}/{function}`. Every call runs with the **caller's** permissions. A deployed agent often runs as a **service principal** (an identity for an app, not a person), so that service principal needs `EXECUTE`. The classic miss: the team grants it to people, tests in a notebook, it works, and then the deployed agent is refused.",
    ],
    example=example('A SQL function, described and granted', """CREATE FUNCTION main.support.lookup_order(
  order_id STRING COMMENT 'The order number, like A-1042')
RETURNS STRING
COMMENT 'Look up the status of one order'
LANGUAGE SQL
RETURN SELECT status FROM main.support.orders
       WHERE id = order_id;

-- People who test it:
GRANT EXECUTE ON FUNCTION main.support.lookup_order TO `support-agents`;
-- The group the agent's service principal is in:
GRANT EXECUTE ON FUNCTION main.support.lookup_order TO `support-bots`;"""),
    check=question(
        "Mai is in `support-agents`, which has `EXECUTE` on `main.support.lookup_order`. The agent works when she tests it in a notebook, but once deployed it gets a permission error on that tool. What is the most likely cause?",
        [
            "The function's COMMENT is too short",
            "The agent's service principal has no EXECUTE on the function, its schema or its catalog",
            'SQL functions cannot be called by deployed agents',
        ],
        answer=1,
        why="Every call runs with the caller's permissions. In the notebook the caller was Mai; once deployed it is the agent's service principal. Grant EXECUTE, plus USE CATALOG and USE SCHEMA, to a group the service principal is in.",
    ),
    angle=angle(
        pattern='Three checks per function, each looking up the tree',
        text='The big idea: an agent can call a function only when three privileges line up, and each one can come from the place itself or a place above it. Your code goes through the functions one by one and splits each name into catalog and schema. A small helper, `has`, asks one question: "does any of the agent\'s names have this privilege on one of these places?" You ask it three times: USE CATALOG on the catalog; USE SCHEMA on the catalog or schema; EXECUTE on the catalog, schema or function. When all three say yes, the function goes on the list.',
        say='"An agent calls Unity Catalog functions as its own identity. So before deploying, I check that its service principal, or a group it is in, has USE CATALOG, USE SCHEMA and EXECUTE, each granted on the object or above it."',
        classic=None,
    ),
    stack=stack('A Python function an agent can call', """CREATE OR REPLACE FUNCTION
  main.support.parcel_size(
    weight_kg DOUBLE
      COMMENT 'Parcel weight in kilograms')
RETURNS STRING
COMMENT 'Size band for a parcel: small, medium or large'
LANGUAGE PYTHON
AS $$
if weight_kg <= 2:
    return "small"
if weight_kg <= 20:
    return "medium"
return "large"
$$;

-- The agent's group needs all three.
-- EXECUTE on the schema covers every
-- function in main.support.
GRANT USE CATALOG ON CATALOG main TO `support-bots`;
GRANT USE SCHEMA ON SCHEMA main.support TO `support-bots`;
GRANT EXECUTE ON SCHEMA main.support TO `support-bots`;"""),
    exercise=exercise(
        title='Which Tools Can the Agent Call?',
        topic='unity-catalog',
        difficulty='easy',
        fn='callable_tools',
        prompt="""An agent has a list of Unity Catalog functions as tools. Find the ones it is really allowed to call.

Your function gets three things:

- `functions`: full function names, like `"main.support.lookup_order"`.
- `grants`: a list of grants. Each one is a dict like `{"principal": "support-bots", "privilege": "EXECUTE", "on": "main.support"}`. `on` is a catalog (`"main"`), a schema (`"main.support"`) or a function (`"main.support.lookup_order"`).
- `principals`: every name the agent counts as: its service principal plus the groups it is in, like `["order-bot", "support-bots"]`.

The agent can call a function only when all three of these are true, through a grant to any name in `principals`:

1. `USE CATALOG` on the catalog.
2. `USE SCHEMA` on the schema, or on the catalog.
3. `EXECUTE` on the function, its schema or its catalog.

A grant of `ALL PRIVILEGES` counts as any privilege. Return the functions the agent can call, in the same order as `functions`.""",
        pattern='Write one helper that answers "is this privilege granted to the agent on any of these places?", then ask it three times for each function.',
        target='one pass over the grants for each check, for each function',
        realworld="Run this check for the agent's service principal before every deploy, on every function in its tool list. In SQL, `SHOW GRANTS ON FUNCTION main.support.lookup_order` lists who has what on one function.",
        starter="""def callable_tools(functions, grants, principals):
    # your code here
    pass
""",
        solution="""def callable_tools(functions, grants, principals):
    def has(privilege, places):
        for grant in grants:
            if grant["principal"] in principals and grant["on"] in places:
                if grant["privilege"] == privilege or grant["privilege"] == "ALL PRIVILEGES":
                    return True
        return False

    usable = []
    for name in functions:
        parts = name.split(".")
        catalog = parts[0]
        schema = parts[0] + "." + parts[1]
        if (has("USE CATALOG", [catalog])
                and has("USE SCHEMA", [catalog, schema])
                and has("EXECUTE", [catalog, schema, name])):
            usable.append(name)
    return usable
""",
        cases=[
            case(
                ['main.support.lookup_order', 'main.support.refund_order', 'main.billing.invoice_total'],
                [
                    {'principal': 'support-bots', 'privilege': 'USE CATALOG', 'on': 'main'},
                    {'principal': 'support-bots', 'privilege': 'USE SCHEMA', 'on': 'main.support'},
                    {'principal': 'support-bots', 'privilege': 'EXECUTE', 'on': 'main.support.lookup_order'},
                    {'principal': 'support-agents', 'privilege': 'EXECUTE', 'on': 'main.support.refund_order'},
                    {'principal': 'support-bots', 'privilege': 'EXECUTE', 'on': 'main.billing'},
                ],
                ['order-bot', 'support-bots'],
                expected=['main.support.lookup_order'], sample=True),
            case(
                ['main.support.lookup_order', 'main.hr.leave_balance', 'main.support.order_status'],
                [
                    {'principal': 'support-bots', 'privilege': 'USE CATALOG', 'on': 'main'},
                    {'principal': 'support-bots', 'privilege': 'USE SCHEMA', 'on': 'main'},
                    {'principal': 'support-bots', 'privilege': 'EXECUTE', 'on': 'main.support'},
                    {'principal': 'support-bots', 'privilege': 'EXECUTE', 'on': 'main.hr.leave_balance_v2'},
                ],
                ['order-bot', 'support-bots'],
                expected=['main.support.lookup_order', 'main.support.order_status']),
            case(
                ['tools.web.fetch_page', 'main.support.lookup_order', 'tools.math.add_tax'],
                [
                    {'principal': 'sp-helpdesk', 'privilege': 'ALL PRIVILEGES', 'on': 'tools'},
                ],
                ['sp-helpdesk', 'helpdesk-bots'],
                expected=['tools.web.fetch_page', 'tools.math.add_tax']),
            case(
                [],
                [
                    {'principal': 'support-bots', 'privilege': 'USE CATALOG', 'on': 'main'},
                ],
                ['order-bot', 'support-bots'],
                expected=[]),
            case(
                ['main.support.lookup_order', 'main.support.order_status'],
                [
                    {'principal': 'analysts', 'privilege': 'USE CATALOG', 'on': 'main'},
                    {'principal': 'support-bots', 'privilege': 'USE SCHEMA', 'on': 'main.support'},
                    {'principal': 'support-bots', 'privilege': 'EXECUTE', 'on': 'main.support'},
                ],
                ['order-bot', 'support-bots'],
                expected=[]),
        ],
        guided="""def callable_tools(functions, grants, principals):
    # Replace every ___ with real code, then run the tests.

    def has(privilege, places):
        # True when one of the agent's names has this privilege on one of these places.
        for grant in grants:
            if grant["principal"] in principals and grant["on"] in places:
                # ALL PRIVILEGES counts as any privilege.
                if grant["privilege"] == privilege or grant["privilege"] == "ALL PRIVILEGES":
                    return True
        return False

    usable = []
    for name in functions:
        parts = name.split(".")
        catalog = parts[0]

        # Step 1: the schema is the first two parts, joined by a dot.
        schema = ___

        # Step 2: all three must be True. Each list holds the places
        # the privilege may come from.
        if (has("USE CATALOG", [catalog])
                and has("USE SCHEMA", [catalog, schema])
                and has("EXECUTE", ___)):
            # Step 3: the agent can call this one, so keep it.
            ___

    return usable
""",
        fills=['parts[0] + "." + parts[1]', '[catalog, schema, name]', 'usable.append(name)'],
        concepts=[
            [
                'A helper inside a function',
                'A function written inside another one can read the outer one\'s variables. Here `has` reads `grants` and `principals` without being handed them.',
                """def greet_all(names, greeting):
    def greet(name):
        return greeting + ', ' + name
    return [greet(n) for n in names]

greet_all(['Ada', 'Bo'], 'Hi')   # ['Hi, Ada', 'Hi, Bo']""",
            ],
            [
                'Joining checks with and',
                '`a and b and c` is True only when all three are True. Python stops at the first False, so later checks are skipped.',
                """age = 20
has_ticket = False
age >= 18 and has_ticket   # False""",
            ],
            [
                'in on a list',
                '`x in a_list` compares whole items. So `"main.hr.leave_balance"` is not in `["main.hr.leave_balance_v2"]`, even though the text starts the same.',
                """'main.hr' in ['main', 'main.hr']   # True
'main.h' in ['main', 'main.hr']    # False""",
            ],
        ],
        byhand='The agent counts as order-bot and support-bots. lookup_order: USE CATALOG on main, yes; USE SCHEMA on main.support, yes; EXECUTE on main.support.lookup_order, yes. Keep it. refund_order: EXECUTE went to support-agents, the people, not to the agent, so no. invoice_total: EXECUTE on main.billing is there, but nobody gave support-bots USE SCHEMA on main.billing or on main, so no. The answer is ["main.support.lookup_order"].',
        why='For each function, at most three passes over the grants, one for each check.',
        gotchas=[
            [
                'Tested as a person, deployed as an app',
                'A notebook test runs as you, so it passes with your own grants. The deployed agent runs as its service principal. Put the service principal in a group and grant that group USE CATALOG, USE SCHEMA and EXECUTE.',
            ],
            [
                'Python functions and the network',
                'Python functions on serverless or standard access mode compute may use network ports 80, 443 and 53. A **port** is a numbered door on a machine; 443 is the usual one for `https` links. To call an Azure service from a Python function, use a service credential (see "Service credentials and connections"); whoever creates the function needs `ACCESS` on it.',
            ],
            [
                'Where Python functions run',
                'Python functions run on serverless compute, pro or serverless SQL warehouses, or classic compute with Databricks Runtime 13.3 LTS and above. `STRICT ISOLATION` is for functions that run arbitrary code (any code at all, not one fixed job).',
            ],
        ],
    ),
)

lesson(MODULE, 'cited_sources',
    title='Web search for agents',
    learn=[
        '`system.ai.web_search` is a built-in MCP service that searches the public web. It gives back a **synthesized** answer (one answer written from several pages) with **citations**: links to the pages it used. Its URL is `https://<host>/ai-gateway/mcp-services/system.ai.web_search`.',
        'It is a Unity Catalog securable reached through Unity Gateway: grants decide who can call it, and policies govern each call. It is **Beta**: an account admin turns on the Unity Gateway beta on the Previews page of the account console. It is not available in workspaces with HIPAA compliance enabled (HIPAA is a US rule for health data). It is available in supported US regions, or in workspaces that allow **cross-Geo processing**, which means your data may be processed outside your region. Check with your data team before you turn that on.',
        'Good practice: answer company questions from **internal retrieval** (searching your own data), such as Databricks Vector Search, Azure AI Search or Genie. Use web search only for public, fresh information, like a product release from last week. Never put private or personal data in a search query, because the query leaves your workspace.',
        'Treat everything that comes back as untrusted text: a web page can carry prompt injection (see "Prompt injection"). Keep the citations, show them to the user, and check they come from sources you trust. Log which answers used the web, so you can find them in your **traces** (the step-by-step record of each agent run).',
        'To check a source, look at the link\'s **host**: the site name, which is the text after `://` up to the next `/`. In `https://learn.microsoft.com/azure/search`, the host is `learn.microsoft.com`.',
    ],
    example=example('Citations checked against an allow list', """allowed: microsoft.com, databricks.com

link                                     host                        result
https://learn.microsoft.com/azure/x      learn.microsoft.com         kept
https://docs.databricks.com/genai/mcp    docs.databricks.com         kept
https://evilmicrosoft.com/azure          evilmicrosoft.com           dropped
https://microsoft.com.fake-docs.example  microsoft.com.fake-docs...  dropped"""),
    check=question(
        'A user asks your agent: "What is our refund policy for business customers?" Where should the answer come from?',
        [
            'Web search, because it always has the newest information',
            'Internal retrieval over your own policy documents, such as Databricks Vector Search or Azure AI Search',
            "Web search with the customer's name in the query, so it finds the right page",
        ],
        answer=1,
        why="Company facts live in company documents. The web may hold old or wrong copies, and a query with a customer's name sends personal data out of your workspace.",
    ),
    angle=angle(
        pattern='Cut out the host, then match the end',
        text='The big idea: a citation only helps if it comes from a site you trust, and the host in the link tells you which site that is. Your code goes through the links in order. It cuts the text after `"://"`, then cuts again at the first `"/"`, to get the host. A link with no `"://"` has no host, so it can never match. Then it checks each allowed domain: the host is that domain exactly, or ends with `"."` plus it. The dot matters: it stops `evilmicrosoft.com` from passing as `microsoft.com`. Each link goes in kept or dropped, in order.',
        say='"I use web search only for public, fresh facts, and keep company questions on internal retrieval. I check every citation\'s host against an allow list, matching the exact domain or a dot before it, so lookalike sites fail."',
        classic=None,
    ),
    stack=stack('databricks-mcp: connect to web search', """# pip install databricks-mcp databricks-sdk
from databricks.sdk import WorkspaceClient
from databricks_mcp import DatabricksMCPClient

w = WorkspaceClient()
url = (w.config.host
       + "/ai-gateway/mcp-services/"
       + "system.ai.web_search")

client = DatabricksMCPClient(
    server_url=url,
    workspace_client=w)

for tool in client.list_tools():
    print(tool.name, tool.inputSchema)

# Call it with client.call_tool(name, arguments).
# Then check each citation's host before
# you show the answer, and fence the text
# as data, not instructions."""),
    exercise=exercise(
        title='Keep Trusted Citations',
        topic='mcp',
        difficulty='easy',
        fn='cited_sources',
        prompt="""Web search sends back an answer with citations: links to the pages it used. Before you show them, keep only links from sites your team trusts.

Your function gets two things:

- `urls`: the citation links, like `"https://learn.microsoft.com/azure/search/x"`.
- `allowed`: trusted domains, like `["microsoft.com", "databricks.com"]`.

For each link:

1. If it has no `"://"`, drop it.
2. Its **host** is the text after `"://"` up to the next `"/"` (or to the end, if there is no `"/"`). For the link above, that is `"learn.microsoft.com"`.
3. Keep the link when its host equals an allowed domain, or ends with `"."` plus that domain. So `"learn.microsoft.com"` matches `"microsoft.com"`, but `"evilmicrosoft.com"` does not.

Return `[kept, dropped]`: two lists, each in the same order as `urls`.""",
        pattern='Cut each link down to its host, then compare the host with each allowed domain.',
        target='one pass over the links, checking each against the allow list',
        realworld="Run this check in the agent right after each web search call, before the answer reaches the user. Record the kept and dropped links in the trace, so a reviewer can see which answers used the web and which sources were thrown away.",
        starter="""def cited_sources(urls, allowed):
    # your code here
    pass
""",
        solution="""def cited_sources(urls, allowed):
    kept = []
    dropped = []
    for url in urls:
        host = ""
        if "://" in url:
            after = url.split("://")[1]
            host = after.split("/")[0]
        trusted = False
        for domain in allowed:
            if host == domain or host.endswith("." + domain):
                trusted = True
        if trusted:
            kept.append(url)
        else:
            dropped.append(url)
    return [kept, dropped]
""",
        cases=[
            case(
                [
                    'https://learn.microsoft.com/azure/search/x',
                    'https://evilmicrosoft.com/azure/search',
                    'https://docs.databricks.com/genai/mcp',
                    'https://microsoft.com.fake-docs.example/x',
                ],
                ['microsoft.com', 'databricks.com'],
                expected=[
                    ['https://learn.microsoft.com/azure/search/x', 'https://docs.databricks.com/genai/mcp'],
                    ['https://evilmicrosoft.com/azure/search', 'https://microsoft.com.fake-docs.example/x'],
                ], sample=True),
            case(
                ['https://databricks.com', 'https://www.databricks.com/blog/x', 'docs.databricks.com/genai'],
                ['databricks.com'],
                expected=[
                    ['https://databricks.com', 'https://www.databricks.com/blog/x'],
                    ['docs.databricks.com/genai'],
                ]),
            case([], ['microsoft.com'], expected=[[], []]),
            case(
                ['https://learn.microsoft.com/x', 'https://docs.databricks.com/y'],
                [],
                expected=[[], ['https://learn.microsoft.com/x', 'https://docs.databricks.com/y']]),
            case(
                [
                    'https://news-fict.example/microsoft.com/x',
                    'http://azure.microsoft.com/updates/y',
                    'https://notdatabricks.com/z',
                ],
                ['microsoft.com', 'databricks.com'],
                expected=[
                    ['http://azure.microsoft.com/updates/y'],
                    ['https://news-fict.example/microsoft.com/x', 'https://notdatabricks.com/z'],
                ]),
        ],
        guided="""def cited_sources(urls, allowed):
    # Replace every ___ with real code, then run the tests.

    kept = []
    dropped = []
    for url in urls:
        # Step 1: cut out the host. A link without "://" has no host.
        host = ""
        if "://" in url:
            after = url.split("://")[1]
            host = ___

        # Step 2: is the host an allowed domain, or does it end with "." + one?
        trusted = False
        for domain in allowed:
            if host == domain or ___:
                trusted = True

        # Put the link in the right list.
        if trusted:
            kept.append(url)
        else:
            dropped.append(url)

    # Step 3: both lists, kept first.
    return ___
""",
        fills=['after.split("/")[0]', 'host.endswith("." + domain)', '[kept, dropped]'],
        concepts=[
            [
                'Splitting and picking a piece',
                '`text.split(sep)` cuts the text at every `sep` and gives a list of pieces. `[0]` is the first piece, `[1]` the second.',
                """'https://a.com/b/c'.split('://')   # ['https', 'a.com/b/c']
'a.com/b/c'.split('/')[0]          # 'a.com'
'a.com'.split('/')[0]              # 'a.com' (no '/' at all)""",
            ],
            [
                'endswith',
                '`text.endswith(end)` is True when the text finishes with exactly `end`. Adding the dot first makes it match a whole part of the name, not just the last letters.',
                """'learn.microsoft.com'.endswith('.microsoft.com')   # True
'evilmicrosoft.com'.endswith('.microsoft.com')     # False
'evilmicrosoft.com'.endswith('microsoft.com')      # True, which is why you add the dot""",
            ],
            [
                'A yes/no flag',
                'Start a variable at `False`, and set it to `True` when you find a match. After the loop it tells you whether any match was found.',
                """found = False
for word in ['tea', 'milk']:
    if word == 'milk':
        found = True
found   # True""",
            ],
        ],
        byhand='Link 1: after "://" is "learn.microsoft.com/azure/search/x"; cut at the first "/" to get "learn.microsoft.com". It ends with ".microsoft.com", so keep it. Link 2: the host is "evilmicrosoft.com". It is not "microsoft.com" and does not end with ".microsoft.com" (there is no dot before "microsoft"), so drop it. Link 3: "docs.databricks.com" ends with ".databricks.com", keep. Link 4: "microsoft.com.fake-docs.example" starts with microsoft.com but ends with ".example", drop. Return [[link 1, link 3], [link 2, link 4]].',
        why='One pass over the links; each host is checked against the short allow list.',
        gotchas=[
            [
                'Trusted site, untrusted text',
                'A page on an allowed site can still hold text that tries to give your model orders, for example in a comment. The allow list checks where the text came from, not what it says. Fence it as data too.',
            ],
            [
                'The domain in the path',
                '`https://news-fict.example/microsoft.com/x` mentions microsoft.com, but the site is news-fict.example. Always cut out the host first; never search the whole link for the domain.',
            ],
            [
                'Your query leaves the workspace',
                'Whatever the agent searches for goes out to the public web. Keep customer names, order numbers and other private data out of search queries.',
            ],
        ],
    ),
)
