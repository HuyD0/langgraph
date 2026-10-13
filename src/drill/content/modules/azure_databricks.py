"""Azure Databricks: the workspace, Unity Catalog and who can see what, before any of it goes into Terraform."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, case, example, exercise, lesson, module, planned, question, stack

MODULE = module('azure-databricks', 'Azure Databricks', 'The workspace, Unity Catalog and who can see what, before any of it goes into code.', setting=PLATFORM_SETTING)


lesson(MODULE, 'can_read_table',
    title='Who can read this table?',
    learn=[
        "In Azure Databricks every table lives at a three-part address: **catalog.schema.table**, like `main.sales.orders`. **Unity Catalog** is the part of Databricks that keeps those addresses and decides who may use them. A **catalog** is the top folder, a **schema** is a folder inside it, and a **table** sits in a schema.",
        "To read a table you need a key at **every level on the way down**: `USE CATALOG` on the catalog, `USE SCHEMA` on the schema, and `SELECT` on the table. Missing any one of them, and the query fails, even if the other two are there.",
        "A key given higher up **counts for everything below it**. `SELECT` granted on the schema `main.sales` lets you read every table in it, and `USE SCHEMA` granted on the catalog `main` opens every schema in it. `ALL PRIVILEGES` counts as every key at once.",
        "Keys are given to **principals**: a person, a group, or a service principal (an identity for a program, like a Spacelift run). You hold every key given to you and to any group you are in. Teams grant to groups, not people, so a new joiner gets access by joining the group.",
    ],
    example=example('Three keys for one table', """GRANT USE CATALOG ON CATALOG main TO analysts;
GRANT USE SCHEMA ON SCHEMA main.sales TO analysts;
GRANT SELECT ON TABLE main.sales.orders TO analysts;
-- Ana is in analysts: she can read main.sales.orders.
-- Without the second line she can't, whatever the third says."""),
    check=question(
        'Ana is in `analysts`, which has `USE CATALOG` on `main` and `SELECT` on `main.sales.orders`. Nobody granted `USE SCHEMA` on `main.sales` or on `main`. Can she read the table?',
        [
            'Yes: SELECT on the table is what matters',
            'No: she also needs USE SCHEMA on the way down',
            'Yes, but only from a notebook',
        ],
        answer=1,
        why='Every level on the way down needs its key. SELECT on the table is the last one, not the only one: with no USE SCHEMA on main.sales (or on main, which would cover it), the query stops at the schema.',
    ),
    angle=angle(
        pattern='A key at every level on the way down',
        text='The big idea: Unity Catalog checks three keys before you read a table: USE CATALOG on its catalog, USE SCHEMA on its schema, SELECT on the table. A key given higher up counts below it, and ALL PRIVILEGES counts as any key. Your code first collects every key the person holds, through any of their groups, as a set of (privilege, where) pairs. Then it asks three questions: USE CATALOG on the catalog; USE SCHEMA on the catalog or the schema; SELECT on the catalog, the schema or the table. Only three yeses mean yes. It is like walking into an office: the front door, then the floor, then the room, and a master key opens all three.',
        say='"To read a table in Unity Catalog, I need [[three keys|one key|two keys::A key for the catalog, the schema and the table.]]: USE CATALOG, USE SCHEMA and SELECT. A key given [[higher up|lower down|to a table::A grant on a catalog covers what\'s inside it.]] covers everything below it, but one missing key means [[no access|read-only|a warning::Every key on the way down must be there.]]."',
        classic=None,
    ),
    stack=stack('Terraform: the same keys as code', """resource "databricks_grants" "sales" {
  schema = "main.sales"
  grant {
    principal  = "analysts"
    privileges = ["USE_SCHEMA", "SELECT"]   # Terraform writes them with _
  }
}"""),
    exercise=exercise(
        title='Can They Read It?',
        topic='unity-catalog',
        difficulty='easy',
        fn='can_read',
        prompt="""Your function gets three things:

- `table`: a three-part name like `"main.sales.orders"` (catalog, schema, table).
- `principals`: everyone the person counts as: their own name and their groups, like `["ana@corp.com", "analysts"]`.
- `grants`: a list of dicts, each one key given to one principal on one place, like `{"to": "analysts", "privilege": "SELECT", "on": "main.sales"}`. `"on"` is a catalog (`"main"`), a schema (`"main.sales"`) or a table (`"main.sales.orders"`).

The person can read the table when they hold all three:

- `USE CATALOG` on the catalog.
- `USE SCHEMA` on the catalog or the schema.
- `SELECT` on the catalog, the schema or the table.

A grant counts when its `"to"` is one of `principals`. `ALL PRIVILEGES` counts as any privilege. Return `True` or `False`.""",
        pattern='Collect the keys they hold, then check each level: catalog, schema, table, each on its own place or above.',
        target='one pass over the grants',
        realworld="Unity Catalog runs exactly this check on every query in Azure Databricks. When someone says \"I have SELECT but it still fails\", the missing key is almost always USE SCHEMA or USE CATALOG higher up. In Terraform the same keys are `databricks_grants` resources, written with underscores (`USE_SCHEMA`).",
        starter="""def can_read(table, principals, grants):
    # your code here
    pass
""",
        solution="""def can_read(table, principals, grants):
    catalog, schema, name = table.split(".")
    schema_name = catalog + "." + schema
    held = set()
    for g in grants:
        if g["to"] in principals:
            held.add((g["privilege"], g["on"]))

    def has(privilege, places):
        for place in places:
            if (privilege, place) in held or ("ALL PRIVILEGES", place) in held:
                return True
        return False

    return (has("USE CATALOG", [catalog])
            and has("USE SCHEMA", [catalog, schema_name])
            and has("SELECT", [catalog, schema_name, table]))
""",
        cases=[
            case('main.sales.orders', ['ana@corp.com', 'analysts'], [
                {'to': 'analysts', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'analysts', 'privilege': 'USE SCHEMA', 'on': 'main.sales'},
                {'to': 'analysts', 'privilege': 'SELECT', 'on': 'main.sales.orders'},
            ], expected=True, sample=True),
            case('main.sales.orders', ['ana@corp.com', 'analysts'], [
                {'to': 'analysts', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'analysts', 'privilege': 'SELECT', 'on': 'main.sales.orders'},
            ], expected=False),
            case('main.sales.orders', ['bo@corp.com', 'finance'], [
                {'to': 'finance', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'finance', 'privilege': 'USE SCHEMA', 'on': 'main'},
                {'to': 'finance', 'privilege': 'SELECT', 'on': 'main.sales'},
            ], expected=True),
            case('main.sales.orders', ['cy@corp.com', 'platform-admins'], [
                {'to': 'platform-admins', 'privilege': 'ALL PRIVILEGES', 'on': 'main'},
            ], expected=True),
            case('main.sales.orders', ['ana@corp.com', 'analysts'], [
                {'to': 'engineers', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'engineers', 'privilege': 'USE SCHEMA', 'on': 'main.sales'},
                {'to': 'engineers', 'privilege': 'SELECT', 'on': 'main.sales.orders'},
            ], expected=False),
            case('main.hr.salaries', ['ana@corp.com', 'analysts'], [
                {'to': 'analysts', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'analysts', 'privilege': 'USE SCHEMA', 'on': 'main.sales'},
                {'to': 'analysts', 'privilege': 'SELECT', 'on': 'main.sales'},
            ], expected=False),
            case('main.sales.orders', ['ana@corp.com'], [], expected=False),
        ],
        guided="""def can_read(table, principals, grants):
    # Replace every ___ with real code, then run the tests.
    catalog, schema, name = table.split(".")
    schema_name = catalog + "." + schema

    # Step 1: every key this person holds, through any of their principals.
    held = set()
    for g in grants:
        if ___:
            held.add((g["privilege"], g["on"]))

    # Step 2: do they hold this privilege (or ALL PRIVILEGES) on any of these places?
    def has(privilege, places):
        for place in places:
            if (privilege, place) in held or ("ALL PRIVILEGES", place) in held:
                return True
        return False

    # Step 3: a key at every level, on that level or above it.
    return (has("USE CATALOG", [catalog])
            and has("USE SCHEMA", ___)
            and has("SELECT", [catalog, schema_name, table]))
""",
        fills=['g["to"] in principals', '[catalog, schema_name]'],
        concepts=[
            [
                'Splitting a string',
                '`text.split(".")` cuts a string at every dot and gives the pieces as a list; three names can catch three pieces.',
                """a, b, c = "main.sales.orders".split(".")
b   # 'sales'""",
            ],
            [
                'A set of pairs',
                'A set holds each thing once and answers `in` instantly. A pair in round brackets, like `("SELECT", "main")`, can go in a set.',
                """keys = {("SELECT", "main")}
("SELECT", "main") in keys   # True""",
            ],
            [
                'A small function inside a function',
                'A `def` inside another function can use the names around it, like `held`. It saves writing the same check three times.',
                """def outer():
    seen = {1, 2}
    def has(x):
        return x in seen
    return has(2)   # True""",
            ],
            [
                'and',
                '`a and b and c` is True only when all three are True.',
                'True and True and False   # False',
            ],
        ],
        byhand='Ana counts as ana@corp.com and analysts. All three grants are to analysts, so she holds (USE CATALOG, main), (USE SCHEMA, main.sales) and (SELECT, main.sales.orders). USE CATALOG on main: yes. USE SCHEMA on main or main.sales: yes. SELECT on main, main.sales or main.sales.orders: yes. Three yeses: True.',
        why='One pass over the grants to collect the keys, then three quick checks.',
        gotchas=[
            [
                'SELECT alone is not enough',
                'The classic "I have SELECT but it fails": USE SCHEMA or USE CATALOG is missing higher up. Check the whole way down.',
            ],
            [
                'Grant to groups, not people',
                'A grant to one person breaks when they leave and is hard to review. Grant to account-level groups synced from Entra ID, and manage who is in the group.',
            ],
        ],
    ),
)

planned(MODULE, 'workspace_metastore', 'A workspace, a metastore and a catalog', 'How one Unity Catalog metastore serves several workspaces, and where catalogs live.')
planned(MODULE, 'compute_choices', 'Clusters, SQL warehouses and serverless', 'Which compute runs notebooks, jobs and SQL, and what each costs while idle.')
planned(MODULE, 'service_principals', 'People, groups and service principals', 'The identities that run jobs and Spacelift, and why they never use a person\'s login.')
planned(MODULE, 'external_locations', 'External locations and storage credentials', 'How Unity Catalog reaches your Azure storage account without anyone holding its keys.')
planned(MODULE, 'private_networking', 'Private networking: VNet injection and Private Link', 'Keeping the workspace and its traffic off the public internet.')
