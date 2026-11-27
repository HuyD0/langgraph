"""Azure Databricks: the workspace, Unity Catalog and who can see what, before any of it goes into Terraform."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, module, planned, practice, question, stack, source

MODULE = module('azure-databricks', 'Azure Databricks', 'The workspace, Unity Catalog and who can see what, before any of it goes into code.', setting=PLATFORM_SETTING)


lesson(MODULE, 'can_read_table',
    title='Who can read this table?',
    checked='2026-11-27',
    sources=[source('Unity Catalog permissions model concepts', 'https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts'), source('REVOKE', 'https://learn.microsoft.com/azure/databricks/sql/language-manual/security-revoke'), source('Identity best practices', 'https://learn.microsoft.com/azure/databricks/admin/users-groups/best-practices')],
    learn=[
        "In Azure Databricks every table lives at a three-part address: **catalog.schema.table**, like `main.sales.orders`. **Unity Catalog** is the part of Databricks that keeps those addresses and decides who may use them. A **catalog** is the top folder, a **schema** is a folder inside it, and a **table** sits in a schema.",
        "To read a table you need a key at **every level on the way down**: `USE CATALOG` on the catalog, `USE SCHEMA` on the schema, and `SELECT` on the table. Missing any one of them, and the query fails, even if the other two are there.",
        "A key given higher up **counts for everything below it**. `SELECT` granted on the schema `main.sales` lets you read every table in it, and `USE SCHEMA` granted on the catalog `main` opens every schema in it. `ALL PRIVILEGES` on the catalog `main` counts as all three keys at once. It covers **things made later** too: `SELECT` on the catalog reaches a schema added next month, and a `REVOKE` (the command that takes a grant back) on that one schema can't remove it, because nothing lower down can take away `SELECT`. So don't grant `SELECT` on a whole catalog: give it schema by schema.",
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
        text='The big idea: Unity Catalog checks three keys before you read a table: USE CATALOG on its catalog, USE SCHEMA on its schema, SELECT on the table. A key given higher up counts below it, and ALL PRIVILEGES on the catalog counts as any key. Your code first collects every key the person holds, through any of their groups, as a set of (privilege, where) pairs. Then it asks three questions: USE CATALOG on the catalog; USE SCHEMA on the catalog or the schema; SELECT on the catalog, the schema or the table. Only three yeses mean yes. It is like walking into an office: the front door, then the floor, then the room, and a master key opens all three.',
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
- `principals`: everyone the person counts as: their own name and their groups, like `["ana@example.com", "analysts"]`.
- `grants`: a list of dicts, each one key given to one principal on one place, like `{"to": "analysts", "privilege": "SELECT", "on": "main.sales"}`. `"on"` is a catalog (`"main"`), a schema (`"main.sales"`) or a table (`"main.sales.orders"`).

The person can read the table when they hold all three:

- `USE CATALOG` on the catalog.
- `USE SCHEMA` on the catalog or the schema.
- `SELECT` on the catalog, the schema or the table.

A grant counts when its `"to"` is one of `principals`. `ALL PRIVILEGES` counts as any of the three, on the place it is given. Return `True` or `False`.""",
        pattern='Collect the keys they hold, then check each level: catalog, schema, table, each on its own place or above.',
        target='one pass over the grants',
        realworld="Unity Catalog runs exactly this check on every query in Azure Databricks. When someone says \"I have SELECT but it still fails\", the missing key is almost always USE SCHEMA or USE CATALOG higher up. In Terraform the same keys are `databricks_grants` resources, written with underscores (`USE_SCHEMA`).",
        practice=practice(
            intro='Review the grants the way a platform reviewer does when someone asks "why can\'t I read this?": who holds each key, and where.',
            explain='Unity Catalog checks three keys before anyone reads a table: USE CATALOG, USE SCHEMA and SELECT, each on its own level or higher up. You checked who each key was given to and where it was given, so a key on the catalog covered everything below it, and a key on the wrong schema or for the wrong group counted for nothing.',
            pattern='Who holds each key, and where',
            realworld='When someone says "I have SELECT but my query still fails", you read the grants for who got each key and where. Usually USE SCHEMA or USE CATALOG is missing higher up, or the keys went to a group they aren\'t in.',
            asks=[
                ask('Ana is in `analysts`. Can she read `main.sales.orders`?', ['Yes: she holds all three keys through `analysts`', 'No: the keys went to the group, not to her'], answer=0,
                    evidence=evidence('code', title='The grants', text="""GRANT USE CATALOG ON CATALOG main TO analysts;
GRANT USE SCHEMA ON SCHEMA main.sales TO analysts;
GRANT SELECT ON TABLE main.sales.orders TO analysts;"""),
                    clue='You hold every key given to any group you are in.',
                    why='All three keys went to analysts, and Ana is in analysts, so she holds them all: the catalog, the schema and the table.',
                    wrong=[None, 'Keys given to a group count for everyone in it. That\'s why teams grant to groups.']),
                ask('Bo is in `finance`. Can he read `main.sales.orders`?', ['Yes: keys given higher up count for everything below', 'No: nothing is granted on the table itself', 'No: USE SCHEMA has to be on the schema'], answer=0,
                    evidence=evidence('code', title='The grants', text="""GRANT USE CATALOG ON CATALOG main TO finance;
GRANT USE SCHEMA ON CATALOG main TO finance;
GRANT SELECT ON SCHEMA main.sales TO finance;"""),
                    clue='A key given on a catalog or a schema covers what\'s inside it.',
                    why='USE SCHEMA on the catalog main opens every schema in it, and SELECT on the schema main.sales covers every table in it, so Bo holds all three keys.',
                    wrong=[None, 'SELECT on the schema covers every table in it, orders included.', 'USE SCHEMA on the catalog covers every schema in it.']),
                ask('Ana asks for `main.hr.salaries`. Can she read it?', ['Yes: she has USE CATALOG, USE SCHEMA and SELECT', 'No: those keys are on `main.sales`, not `main.hr`'], answer=1,
                    evidence=evidence('code', title='The grants', text="""GRANT USE CATALOG ON CATALOG main TO analysts;
GRANT USE SCHEMA ON SCHEMA main.sales TO analysts;
GRANT SELECT ON SCHEMA main.sales TO analysts;"""),
                    clue='Check where each key was given, not just which keys she has.',
                    why='A key on main.sales only covers what\'s inside main.sales. Nothing covers main.hr, so her query stops at the schema.',
                    wrong=['She does, but USE SCHEMA and SELECT are on a different schema.', None]),
                ask('A teammate says Ana must be able to read `main.sales.orders`: all three keys are granted on the way down. Ana is only in `analysts`. Is the teammate right?', ['Yes: all three keys are granted on the way down', 'No: the keys went to `engineers`, not `analysts`'], answer=1,
                    evidence=evidence('code', title='The grants', text="""GRANT USE CATALOG ON CATALOG main TO engineers;
GRANT USE SCHEMA ON SCHEMA main.sales TO engineers;
GRANT SELECT ON TABLE main.sales.orders TO engineers;"""),
                    clue='Read who each key was given to.',
                    why='The keys are all there, but for engineers. Ana only holds keys given to her or to a group she\'s in, so she has none of them.',
                    wrong=['The keys are there, but who holds them?', None]),
            ],
        ),
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
            case('main.sales.orders', ['ana@example.com', 'analysts'], [
                {'to': 'analysts', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'analysts', 'privilege': 'USE SCHEMA', 'on': 'main.sales'},
                {'to': 'analysts', 'privilege': 'SELECT', 'on': 'main.sales.orders'},
            ], expected=True, sample=True),
            case('main.sales.orders', ['ana@example.com', 'analysts'], [
                {'to': 'analysts', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'analysts', 'privilege': 'SELECT', 'on': 'main.sales.orders'},
            ], expected=False),
            case('main.sales.orders', ['bo@example.com', 'finance'], [
                {'to': 'finance', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'finance', 'privilege': 'USE SCHEMA', 'on': 'main'},
                {'to': 'finance', 'privilege': 'SELECT', 'on': 'main.sales'},
            ], expected=True),
            case('main.sales.orders', ['cy@example.com', 'platform-admins'], [
                {'to': 'platform-admins', 'privilege': 'ALL PRIVILEGES', 'on': 'main'},
            ], expected=True),
            case('main.sales.orders', ['ana@example.com', 'analysts'], [
                {'to': 'engineers', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'engineers', 'privilege': 'USE SCHEMA', 'on': 'main.sales'},
                {'to': 'engineers', 'privilege': 'SELECT', 'on': 'main.sales.orders'},
            ], expected=False),
            case('main.hr.salaries', ['ana@example.com', 'analysts'], [
                {'to': 'analysts', 'privilege': 'USE CATALOG', 'on': 'main'},
                {'to': 'analysts', 'privilege': 'USE SCHEMA', 'on': 'main.sales'},
                {'to': 'analysts', 'privilege': 'SELECT', 'on': 'main.sales'},
            ], expected=False),
            case('main.sales.orders', ['ana@example.com'], [], expected=False),
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
        byhand='Ana counts as ana@example.com and analysts. All three grants are to analysts, so she holds (USE CATALOG, main), (USE SCHEMA, main.sales) and (SELECT, main.sales.orders). USE CATALOG on main: yes. USE SCHEMA on main or main.sales: yes. SELECT on main, main.sales or main.sales.orders: yes. Three yeses: True.',
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

lesson(MODULE, 'workspace_metastore',
    title='A workspace, a metastore and a catalog',
    checked='2026-11-27',
    sources=[source('Create a Unity Catalog metastore', 'https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/create-metastore'), source('Manage a metastore', 'https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/manage-metastore'), source('Get started with Unity Catalog', 'https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/get-started'), source('Managed storage', 'https://learn.microsoft.com/azure/databricks/connect/unity-catalog/managed-storage')],
    learn=[
        "A **metastore** is Unity Catalog's top-level store: it holds the catalogs, and through them the schemas and tables. You have one for each region you work in, and every workspace in that region can be linked to it, so they all see the same data. Each workspace is linked to exactly one metastore.",
        "Since November 2023, new workspaces usually get Unity Catalog switched on automatically, rolled out gradually across accounts. They are linked to their region's metastore if it is set to take new workspaces, or to one made for them if the region had none. So when a workspace is built, the link may already exist: check first, and later, in Terraform, you'll adopt an existing link (an **import**) rather than make a second one.",
        "A **managed table** is one where Unity Catalog looks after the data files for you, and deletes them when the table is dropped. Those files live in **managed storage**, which can be set on the metastore, a catalog or a schema; the lowest level that has one wins. Databricks recommends giving each catalog its own. A metastore made automatically has none of its own, so set it on each catalog.",
        "The metastore is shared by every workspace in the region, so one team's Terraform must never destroy it. Deleting it cuts every workspace off from its data, and managed data is deleted after 30 days. A restore is possible for only 5 days (a Public Preview feature), and only if you saved its id.",
    ],
    example=example('One metastore, many workspaces', """region westeurope
  metastore (one)
    sales-dev workspace   linked
    sales-prod workspace  linked
  catalog sales_dev
    storage: its own container
  catalog sales_prod
    storage: its own container"""),
    check=question(
        'Terraform tries to link a workspace made last week to its region\'s metastore, and the apply fails. What is the likely reason?',
        [
            'It was linked automatically',
            'A region needs two metastores',
            'Links can only be made by hand',
        ],
        answer=0,
        why='New workspaces are usually linked automatically, when the region\'s metastore is set to take new workspaces or was made for them. Adopt the existing link instead of creating a second one.',
    ),
    angle=angle(
        pattern='Is it linked, is there one, or make one',
        text='The big idea: every workspace links to its region\'s one metastore, and the link may already exist. Your code decides the next step in order: if the workspace is already linked, import the link; if its region already has a metastore, link to that one; only if neither, the region needs a metastore of its own. It is like a new house on a street: if it\'s already on the water main, record it; if the street has one, connect; only on a new street do you lay one.',
        say='"There\'s one [[metastore|catalog|workspace::Unity Catalog\'s top-level store.]] per region, shared by every workspace there. If a workspace is already linked to it, I [[import|delete|rename::Adopt it instead of making a second one.]] the link instead of making a new one."',
        classic=None,
    ),
    exercise=exercise(
        title='What Does This Workspace Need?',
        topic='azure-databricks',
        difficulty='easy',
        fn='metastore_step',
        prompt="""Your function gets:

- `metastores`: a dict from each region to its metastore, like `{"westeurope": "ms-weu"}`.
- `region`: the workspace's region.
- `linked`: `True` if the workspace is already linked to a metastore.

Return, checking in this order:

- `linked` is `True` -> `"import the link"`
- the region has a metastore -> `"link to " + that metastore`
- otherwise -> `"create a metastore for " + region`""",
        pattern='Check what already exists before you make anything.',
        target='a few checks, no loops',
        realworld='This is the first question when a new workspace joins the platform. Creating a link that already exists fails, and creating a second metastore in a region isn\'t allowed.',
        practice=practice(
            intro='A team is adding a production workspace in a region where their dev workspace already runs.',
            explain='One metastore serves every workspace in a region, and the link may already exist. You shared the region\'s metastore instead of making another, stopped a teardown that would have destroyed it, and set managed storage on the catalog.',
            pattern='One per region, shared by all',
            realworld='When you add a workspace, you check the region\'s metastore and the workspace\'s link before you write any Terraform for them. In a teardown plan, you look for the metastore and stop if it is there.',
            asks=[
                ask('Should the new production workspace get its own metastore?', ['No: it shares the region\'s one', 'Yes: one per workspace', 'Yes, but only for production'], answer=0,
                    alone=True,
                    clue='How many metastores can one region have?',
                    why='A region has one metastore, and every workspace there links to it. Separate catalogs, not separate metastores, keep production\'s data apart.',
                    wrong=[None, 'A region allows only one metastore.', 'Production shares it too; its own catalogs keep it apart.']),
                ask('The dev stack is being torn down. Its plan shows this. What do you do?', ['Stop: every workspace uses it', 'Apply: dev is going anyway', 'Apply, then restore it later'], answer=0,
                    evidence=evidence('plan', title='Dev teardown plan',
                        summary=[['0', 'to add', 'a'], ['0', 'to change', ''], ['3', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-', 'address': 'databricks_metastore_assignment.this', 'note': 'destroy'},
                            {'sym': '-', 'address': 'databricks_metastore.this', 'note': 'destroy'},
                            {'sym': '-', 'address': 'azurerm_databricks_workspace.this', 'note': 'destroy'},
                        ]),
                    clue='Who else uses the region\'s metastore?',
                    why='Removing dev\'s link is fine, but destroying the metastore cuts every workspace in the region off from its data. Ask for the dev code to stop managing the metastore first, so tearing dev down leaves it alone.',
                    wrong=[None, 'Dev is going, but the metastore serves production too.', 'A restore works for only 5 days, and only with its id saved.']),
                ask('The metastore was made automatically, and a new catalog has no storage of its own. Where do you set it?', ['On the catalog', 'On the workspace', 'On each table'], answer=0,
                    alone=True,
                    clue='Where does Databricks recommend putting managed storage?',
                    why='Databricks recommends managed storage on each catalog, and an automatically made metastore has none of its own to fall back on.',
                    wrong=[None, 'Workspaces don\'t hold Unity Catalog storage settings.', 'Managed storage is set on the metastore, a catalog or a schema, not on a table.']),
            ],
        ),
        starter="""def metastore_step(metastores, region, linked):
    # your code here
    pass
""",
        solution="""def metastore_step(metastores, region, linked):
    if linked:
        return "import the link"
    if region in metastores:
        return "link to " + metastores[region]
    return "create a metastore for " + region
""",
        cases=[
            case({'westeurope': 'ms-weu'}, 'westeurope', False, expected='link to ms-weu', sample=True),
            case({'westeurope': 'ms-weu'}, 'westeurope', True, expected='import the link'),
            case({'westeurope': 'ms-weu'}, 'northeurope', False, expected='create a metastore for northeurope'),
            case({}, 'uksouth', False, expected='create a metastore for uksouth'),
            case({}, 'uksouth', True, expected='import the link'),
        ],
        guided="""def metastore_step(metastores, region, linked):
    # Replace every ___ with real code, then run the tests.
    if linked:
        return "import the link"
    if ___:
        return "link to " + metastores[region]
    return ___
""",
        fills=['region in metastores', '"create a metastore for " + region'],
        concepts=[
            [
                'in on a dict',
                '`key in a_dict` asks whether the dict has that key.',
                """"westeurope" in {"westeurope": "ms-weu"}   # True""",
            ],
            [
                'Joining text',
                '`+` joins two pieces of text into one.',
                """"link to " + "ms-weu"   # 'link to ms-weu'""",
            ],
        ],
        byhand='The sample: the workspace isn\'t linked yet, and westeurope has the metastore ms-weu. Return "link to ms-weu".',
        why='At most three checks.',
        gotchas=[
            [
                'Save the metastore id',
                'A deleted metastore can be restored only with its id, and deleted metastores can\'t be listed. Record the id somewhere safe now.',
            ],
            [
                'Switching Unity Catalog on is one way',
                'Once a workspace is enabled for Unity Catalog, it can\'t be switched back. Plan the catalogs and their storage before you enable it.',
            ],
        ],
    ),
)
planned(MODULE, 'private_networking', 'Private networking: VNet injection and Private Link', 'Keeping the workspace and its traffic off the public internet.')
