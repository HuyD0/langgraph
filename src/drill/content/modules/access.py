"""Databricks access control: who can do what, and the permissions people forget.

The spine of this module: teams remember table grants, then miss the access lists on
experiments, catalogs, compute, access connectors, service credentials and connections.
"""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, case, example, exercise, lesson, module, question, stack, source

MODULE = module('access', 'Databricks access control', 'Who can do what: Unity Catalog privileges, object permissions, credentials, connections and ABAC.', setting=PLATFORM_SETTING)

lesson(MODULE, 'missing_acls',
    title='Workspace objects have their own permissions',
    checked='2026-10-12',
    sources=[source('Access control lists', 'https://docs.databricks.com/aws/en/security/auth/access-control/')],
    learn=[
        'Unity Catalog grants cover data: catalogs, schemas, tables, volumes, functions and models. Everything else in a workspace has its own **access control list** (ACL): a list of who may do what to that one object.',
        'Each object type has its own **permission levels**, from least to most. MLflow experiments: `CAN_READ` < `CAN_EDIT` < `CAN_MANAGE`. Clusters: `CAN_ATTACH_TO` < `CAN_RESTART` < `CAN_MANAGE`. Jobs: `CAN_VIEW` < `CAN_MANAGE_RUN` < `CAN_MANAGE`, plus `IS_OWNER`.',
        'SQL warehouses: `CAN_VIEW` < `CAN_MONITOR` < `CAN_USE` < `CAN_MANAGE`. Model serving endpoints: `CAN_VIEW` < `CAN_QUERY` < `CAN_MANAGE`. Compute policies (rules for what clusters people may create): `CAN_USE`. Databricks Vector Search endpoints: `CAN_USE` < `CAN_MANAGE`, and querying an index also needs `SELECT` on the index in Unity Catalog.',
        'Registered models live in Unity Catalog, so they use UC grants such as `EXECUTE` instead of an ACL.',
        '**Experiments are the classic miss.** You log runs and traces to an experiment in your own user folder, and a teammate cannot see any of it. Put team experiments in a shared folder and give the team group `CAN_READ` or `CAN_EDIT`.',
    ],
    example=example('Share an experiment with the team', """# Experiment lives in /Users/ana@example.com/churn  -> only Ana can see it.
# Better: /Shared/churn (or a team folder), with:
#   ml-team      CAN_EDIT
#   ml-reviewers CAN_READ"""),
    check=question(
        'A teammate has `SELECT` on every table you used, but cannot see your MLflow runs. What is missing?',
        ['More Unity Catalog grants', 'A permission on the experiment itself, like CAN_READ', 'A bigger cluster'],
        answer=1,
        why='Experiments are workspace objects with their own ACL. Table grants do not reach them.',
    ),
    angle=angle(
        pattern='Compare positions in an ordered list',
        text='The big idea: each object type has its levels in order, weakest first, so "is this level high enough?" becomes "does it sit at the same place or later in the list?". Your code goes through each need. It finds the object type from the name, looks up what the principal has on that object, and if they have nothing, the need is missing. Otherwise it compares positions with `list.index`: a smaller position means a weaker level, so the need is missing too.',
        say='"For each need I look up the principal\'s [[current level|email|group name::What it has on that object today.]] on that object. No level, or a level [[earlier|later|the same::Lower in the type\'s ordered list.]] than the need, means the ACL is [[missing|fine|too generous::Someone will be refused.]]."',
        classic=None,
    ),
    stack=stack('An experiment ACL in Terraform', """resource "databricks_mlflow_experiment" "churn" {
  name = "/Shared/churn"
}

resource "databricks_permissions" "churn" {
  experiment_id = databricks_mlflow_experiment.churn.id
  access_control {
    group_name       = "ml-team"
    permission_level = "CAN_EDIT"
  }
  access_control {
    group_name       = "ml-reviewers"
    permission_level = "CAN_READ"
  }
}"""),
    exercise=exercise(
        title='Find the Missing ACLs',
        topic='permissions',
        difficulty='medium',
        fn='missing_acls',
        prompt="""Your function gets three things:

- `needs`: what people need. Each is a dict like `{"object": "experiment:/Shared/churn", "principal": "ml-team", "level": "CAN_READ"}`. The object's type is the text before the first `:`, here `"experiment"`.
- `acls`: what they have now. A dict from object name to another dict from principal to level, like `{"experiment:/Shared/churn": {"ana": "CAN_MANAGE"}}`. An object may be missing from `acls` entirely.
- `levels`: for each object type, its levels from weakest to strongest, like `{"experiment": ["CAN_READ", "CAN_EDIT", "CAN_MANAGE"]}`.

A need is **missing** when the principal has no level on that object, or has a level that comes earlier in the list than the level they need.

Return `[object, principal, needed_level]` for every missing need, in the same order as `needs`.""",
        pattern='Look up, then compare positions. `levels[kind].index(level)` turns a level name into a number you can compare.',
        target='one pass over the needs',
        realworld='Run this before a launch: list who needs what (the team on the experiment, the app on the serving endpoint, the job\'s service principal on the warehouse) and compare it with the live ACLs from the Permissions API.',
        starter="""def missing_acls(needs, acls, levels):
    # your code here
    pass
""",
        solution="""def missing_acls(needs, acls, levels):
    missing = []
    for need in needs:
        obj = need["object"]
        who = need["principal"]
        wanted = need["level"]
        kind = obj.split(":")[0]
        order = levels[kind]
        current = acls.get(obj, {}).get(who)
        if current is None:
            missing.append([obj, who, wanted])
        elif order.index(current) < order.index(wanted):
            missing.append([obj, who, wanted])
    return missing
""",
        cases=[
            case([
                {'object': 'experiment:/Users/ana/churn', 'principal': 'ml-team', 'level': 'CAN_READ'},
                {'object': 'cluster:gpu-dev', 'principal': 'ml-team', 'level': 'CAN_ATTACH_TO'},
            ], {
                'experiment:/Users/ana/churn': {'ana': 'CAN_MANAGE'},
                'cluster:gpu-dev': {'ml-team': 'CAN_RESTART'},
            }, {
                'experiment': ['CAN_READ', 'CAN_EDIT', 'CAN_MANAGE'],
                'cluster': ['CAN_ATTACH_TO', 'CAN_RESTART', 'CAN_MANAGE'],
            }, expected=[['experiment:/Users/ana/churn', 'ml-team', 'CAN_READ']], sample=True),
            case([], {}, {'experiment': ['CAN_READ', 'CAN_EDIT', 'CAN_MANAGE']}, expected=[]),
            case([
                {'object': 'endpoint:support-bot', 'principal': 'support-app', 'level': 'CAN_QUERY'},
            ], {
                'endpoint:support-bot': {'support-app': 'CAN_VIEW'},
            }, {
                'endpoint': ['CAN_VIEW', 'CAN_QUERY', 'CAN_MANAGE'],
            }, expected=[['endpoint:support-bot', 'support-app', 'CAN_QUERY']]),
            case([
                {'object': 'warehouse:bi-small', 'principal': 'analysts', 'level': 'CAN_USE'},
                {'object': 'job:nightly-eval', 'principal': 'ml-team', 'level': 'CAN_MANAGE_RUN'},
            ], {}, {
                'warehouse': ['CAN_VIEW', 'CAN_MONITOR', 'CAN_USE', 'CAN_MANAGE'],
                'job': ['CAN_VIEW', 'CAN_MANAGE_RUN', 'CAN_MANAGE', 'IS_OWNER'],
            }, expected=[['warehouse:bi-small', 'analysts', 'CAN_USE'], ['job:nightly-eval', 'ml-team', 'CAN_MANAGE_RUN']]),
            case([
                {'object': 'warehouse:bi-small', 'principal': 'analysts', 'level': 'CAN_USE'},
                {'object': 'experiment:/Shared/churn', 'principal': 'ml-team', 'level': 'CAN_EDIT'},
            ], {
                'warehouse:bi-small': {'analysts': 'CAN_MANAGE'},
                'experiment:/Shared/churn': {'ml-team': 'CAN_EDIT'},
            }, {
                'warehouse': ['CAN_VIEW', 'CAN_MONITOR', 'CAN_USE', 'CAN_MANAGE'],
                'experiment': ['CAN_READ', 'CAN_EDIT', 'CAN_MANAGE'],
            }, expected=[]),
            case([
                {'object': 'policy:small-gpu', 'principal': 'ml-team', 'level': 'CAN_USE'},
                {'object': 'experiment:/Shared/churn', 'principal': 'ml-reviewers', 'level': 'CAN_READ'},
                {'object': 'experiment:/Shared/churn', 'principal': 'ml-team', 'level': 'CAN_MANAGE'},
            ], {
                'policy:small-gpu': {'ml-team': 'CAN_USE'},
                'experiment:/Shared/churn': {'ml-team': 'CAN_EDIT'},
            }, {
                'policy': ['CAN_USE'],
                'experiment': ['CAN_READ', 'CAN_EDIT', 'CAN_MANAGE'],
            }, expected=[['experiment:/Shared/churn', 'ml-reviewers', 'CAN_READ'], ['experiment:/Shared/churn', 'ml-team', 'CAN_MANAGE']]),
        ],
        guided="""def missing_acls(needs, acls, levels):
    # Replace every ___ with real code, then run the tests.

    missing = []
    for need in needs:
        obj = need["object"]
        who = need["principal"]
        wanted = need["level"]

        # Step 1: the type is the text before the first ":".
        kind = ___
        order = levels[kind]

        # What this principal has on this object now (None if nothing).
        current = acls.get(obj, {}).get(who)

        if current is None:
            missing.append([obj, who, wanted])
        # Step 2: an earlier position in the list means a weaker level.
        elif ___:
            missing.append([obj, who, wanted])

    return missing
""",
        fills=['obj.split(":")[0]', 'order.index(current) < order.index(wanted)'],
        concepts=[
            [
                'Position in a list',
                '`a_list.index(x)` gives the position of x, starting at 0.',
                """sizes = ['small', 'medium', 'large']
sizes.index('large')   # 2""",
            ],
            [
                'Two .get calls in a row',
                '`a.get(k, {})` gives an empty dict when k is missing, so the next `.get` still works. `.get(k)` with no default gives None.',
                """rooms = {'kitchen': {'ana': 'key'}}
rooms.get('hall', {}).get('ana')   # None""",
            ],
            [
                'Checking for None',
                '`x is None` is True when there is no value at all.',
                """found = None
found is None   # True""",
            ],
        ],
        byhand='Need 1: the experiment in Ana\'s folder. The ACL there only has ana, so ml-team has nothing: missing. Need 2: the cluster. ml-team has CAN_RESTART, position 1; they need CAN_ATTACH_TO, position 0. 1 is not smaller than 0, so it is fine. Return [["experiment:/Users/ana/churn", "ml-team", "CAN_READ"]].',
        why='One pass over the needs; each check is two lookups and two short list searches.',
        gotchas=[
            [
                'The often-forgotten list',
                'Teams set table grants, then forget: experiments, catalogs (`USE CATALOG`), compute (clusters, warehouses, policies), access connectors, service credentials and connections. Check each one before you say "access is done".',
            ],
            [
                'Folders pass permissions down',
                'An experiment or notebook inherits its folder\'s ACL. A `/Shared` folder is open to all workspace users by default; a team folder with a group ACL is often a better home.',
            ],
            [
                'Dedicated compute ignores the ACL for running code',
                'A cluster in dedicated (single user) access mode only runs code for its assigned user or group. `CAN_ATTACH_TO` is not enough if you are not that user or in that group.',
            ],
            [
                'Traces in Unity Catalog need UC grants too',
                'If your MLflow traces are stored in Unity Catalog tables, the team needs grants on those tables as well as the experiment ACL.',
            ],
        ],
    ),
)

lesson(MODULE, 'location_for_path',
    title='Access connectors, storage credentials and external locations',
    checked='2026-10-12',
    sources=[source('ADLS external locations (Azure)', 'https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-storage/external-locations-adls')],
    learn=[
        'On Azure, Unity Catalog reaches your storage through a chain of four links. Miss one and reads fail with a "permission denied" that is hard to trace.',
        '1. An **access connector** (`azurerm_databricks_access_connector`) is an Azure resource with a **managed identity**: an identity Azure looks after for you, so there is no password or secret to rotate. 2. In Azure, give that identity the **Storage Blob Data Contributor** role on the storage account.',
        '3. In Unity Catalog, a **storage credential** points at the access connector. 4. An **external location** is a storage path, like `abfss://raw@lakefict.dfs.core.windows.net/sales`, plus that credential.',
        'Then grant the external location to groups: `READ FILES`, `WRITE FILES`, `CREATE EXTERNAL TABLE`. People never get the credential itself.',
        'External locations cannot overlap: Unity Catalog refuses one inside another. So any path belongs to at most one location, and it must match a **whole folder**: `.../sales` covers `.../sales/2026` but not `.../sales-archive`.',
    ],
    example=example('The chain, link by link', """access connector (managed identity)
  -> Azure role: Storage Blob Data Contributor on the storage account
  -> storage credential "lake-cred"
  -> external location "raw-sales" = abfss://raw@lakefict.dfs.core.windows.net/sales + lake-cred
  -> GRANT READ FILES ON EXTERNAL LOCATION `raw-sales` TO `data-engineers`"""),
    check=question(
        'An external location is set up and granted, but every read fails with a 403 from Azure storage. What is the likely gap?',
        ['The table has no SELECT grant', "The access connector's identity has no role on the storage account", 'The cluster is too small'],
        answer=1,
        why='Unity Catalog allowed the read, but Azure refused the identity behind the credential. The Azure role is link 2 of the chain.',
    ),
    angle=angle(
        pattern='Prefix match on whole folders',
        text='The big idea: a path is covered by a location when it is the location\'s path or sits in a folder under it. Your code goes through the locations and, for each, checks two things: is the path exactly the url, or does the path start with the url followed by "/"? Adding the "/" is what stops `sales` from matching `sales-archive`. Because locations cannot overlap, the first match is the answer. No match means no location covers it.',
        say='"I look for the location whose url is the path or a [[parent folder|sibling folder|file::A folder the path sits inside.]] of it, matching on a [[whole folder|first letter|file type::So sales never matches sales-archive.]]. Locations can\'t [[overlap|be renamed|be read::One can\'t sit inside another.]], so at most one matches."',
        classic=None,
    ),
    stack=stack('The whole chain in Terraform', """resource "azurerm_databricks_access_connector" "uc" {
  name                = "ac-lake"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  identity { type = "SystemAssigned" }
}

resource "azurerm_role_assignment" "lake" {
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.uc.identity[0].principal_id
}

resource "databricks_storage_credential" "lake" {
  name = "lake-cred"
  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.uc.id
  }
}

resource "databricks_external_location" "raw_sales" {
  name            = "raw-sales"
  url             = "abfss://raw@lakefict.dfs.core.windows.net/sales"
  credential_name = databricks_storage_credential.lake.name
}

resource "databricks_grants" "raw_sales" {
  external_location = databricks_external_location.raw_sales.id
  grant {
    principal  = "data-engineers"
    privileges = ["READ_FILES", "WRITE_FILES", "CREATE_EXTERNAL_TABLE"]
  }
}"""),
    exercise=exercise(
        title='Which Location Covers This Path?',
        topic='storage',
        difficulty='easy',
        fn='location_for_path',
        prompt="""Your function gets two things:

- `locations`: the external locations. Each is a dict like `{"name": "raw-sales", "url": "abfss://raw@lakefict.dfs.core.windows.net/sales", "credential": "lake-cred"}`. No url ends with `/`, and no location sits inside another.
- `path`: a storage path someone wants to read, like `"abfss://raw@lakefict.dfs.core.windows.net/sales/2026/jan.csv"`.

A location **covers** the path when the path is exactly its url, or starts with its url followed by `/`. So `.../sales` covers `.../sales/2026` but not `.../sales-archive`.

Return `[name, credential]` of the location that covers the path, or `None` if none does.""",
        pattern='Go through the locations; return as soon as one covers the path. Return None after the loop.',
        target='one pass over the locations',
        realworld='This is how you answer "which credential will this read use, and who can grant me access?". In SQL, `SHOW EXTERNAL LOCATIONS` lists the urls and `DESCRIBE EXTERNAL LOCATION raw-sales` shows its credential.',
        starter="""def location_for_path(locations, path):
    # your code here
    pass
""",
        solution="""def location_for_path(locations, path):
    for loc in locations:
        url = loc["url"]
        if path == url or path.startswith(url + "/"):
            return [loc["name"], loc["credential"]]
    return None
""",
        cases=[
            case([
                {'name': 'raw-sales', 'url': 'abfss://raw@lakefict.dfs.core.windows.net/sales', 'credential': 'lake-cred'},
                {'name': 'raw-hr', 'url': 'abfss://raw@lakefict.dfs.core.windows.net/hr', 'credential': 'hr-cred'},
            ], 'abfss://raw@lakefict.dfs.core.windows.net/sales/2026/jan.csv', expected=['raw-sales', 'lake-cred'], sample=True),
            case([], 'abfss://raw@lakefict.dfs.core.windows.net/sales', expected=None),
            case([
                {'name': 'raw-sales', 'url': 'abfss://raw@lakefict.dfs.core.windows.net/sales', 'credential': 'lake-cred'},
            ], 'abfss://raw@lakefict.dfs.core.windows.net/sales-archive/2019.csv', expected=None),
            case([
                {'name': 'raw-sales', 'url': 'abfss://raw@lakefict.dfs.core.windows.net/sales', 'credential': 'lake-cred'},
            ], 'abfss://raw@lakefict.dfs.core.windows.net/sales', expected=['raw-sales', 'lake-cred']),
            case([
                {'name': 'raw-sales', 'url': 'abfss://raw@lakefict.dfs.core.windows.net/sales', 'credential': 'lake-cred'},
                {'name': 'curated', 'url': 'abfss://curated@lakefict.dfs.core.windows.net', 'credential': 'lake-cred'},
                {'name': 'ml-scratch', 'url': 'abfss://scratch@mlfict.dfs.core.windows.net/team', 'credential': 'ml-cred'},
            ], 'abfss://scratch@mlfict.dfs.core.windows.net/team/ana/features.parquet', expected=['ml-scratch', 'ml-cred']),
            case([
                {'name': 'raw-sales', 'url': 'abfss://raw@lakefict.dfs.core.windows.net/sales', 'credential': 'lake-cred'},
            ], 'abfss://raw@otherfict.dfs.core.windows.net/sales/jan.csv', expected=None),
        ],
        guided="""def location_for_path(locations, path):
    # Replace every ___ with real code, then run the tests.

    for loc in locations:
        url = loc["url"]

        # Step 1: the path is the url itself, or a folder under it.
        # Add "/" so "sales" does not match "sales-archive".
        if path == url or ___:
            # Step 2: give back the name and the credential.
            return ___

    return None
""",
        fills=['path.startswith(url + "/")', '[loc["name"], loc["credential"]]'],
        concepts=[
            [
                'startswith',
                '`text.startswith(start)` is True when text begins with exactly those characters.',
                """'sales/2026'.startswith('sales/')      # True
'sales-archive'.startswith('sales/')   # False""",
            ],
            [
                'Returning from inside a loop',
                '`return` inside a loop stops the whole function at once, with that answer.',
                """def first_even(nums):
    for n in nums:
        if n % 2 == 0:
            return n
    return None""",
            ],
            [
                'None means "no answer"',
                '`None` is Python\'s value for "nothing here". Return it when no item matches.',
                """result = None
result is None   # True""",
            ],
        ],
        byhand='Location 1 is .../sales. The path is .../sales/2026/jan.csv, which starts with ".../sales/", so it is covered. Return ["raw-sales", "lake-cred"] straight away, without looking at raw-hr.',
        why='One pass over the locations, with one string check each.',
        gotchas=[
            [
                'It takes rights on both sides',
                'In Azure, creating the access connector needs Contributor or Owner on its resource group, and giving it a role on the storage account needs Owner or User Access Administrator there. In Databricks, creating the storage credential needs `CREATE STORAGE CREDENTIAL` on the metastore. One missing piece on either side stops the chain.',
            ],
            [
                'Firewalled storage',
                'If the storage account has a firewall, it must also allow the access connector (as a trusted resource instance) or serverless compute\'s network. A correct role still gets a 403 otherwise.',
            ],
            [
                'Tables inside locations',
                'Create external tables in folders under an external location, not at its very top. Tables and volumes cannot overlap each other either.',
            ],
        ],
    ),
)

lesson(MODULE, 'pick_securable',
    title='Service credentials and connections',
    checked='2026-10-12',
    sources=[source('Service credentials (Azure)', 'https://learn.microsoft.com/en-us/azure/databricks/connect/unity-catalog/cloud-services/use-service-credentials'), source('Lakehouse Federation', 'https://docs.databricks.com/aws/en/query-federation/')],
    learn=[
        'Different targets need different Unity Catalog objects. Using the wrong one is a common reason "the permissions look right but nothing works".',
        'Files in cloud storage (`abfss://...`): a **storage credential** plus an **external location** (last lesson).',
        'Code that calls other Azure services, like Key Vault, Event Hubs or Azure OpenAI: a **service credential**. It is also built on an access connector, and users need the `ACCESS` privilege on it. It is not for reading storage.',
        'Another database, like PostgreSQL or SQL Server: a **connection** plus a **foreign catalog**. This is **Lakehouse Federation**: you query the other database as if it were a catalog. Creating one needs `CREATE CONNECTION`; then grant `USE CONNECTION` or `CREATE FOREIGN CATALOG`.',
        'An outside web API: an **HTTP connection**, which agents can call as a tool; users need `USE CONNECTION`. A plain secret value for a notebook: a **secret scope**, with its own ACL of `READ`, `WRITE` or `MANAGE`.',
    ],
    example=example('Use a service credential from Python', """from azure.keyvault.secrets import SecretClient

cred = dbutils.credentials.getServiceCredentialsProvider("kv-cred")
client = SecretClient("https://kv-fict.vault.azure.net", cred)
api_key = client.get_secret("ticket-api-key").value"""),
    check=question(
        'Your agent must call an outside ticketing API with a bearer token. Which object fits best?',
        ['An external location', 'A service credential', 'An HTTP connection, with USE CONNECTION granted to the agent\'s principal'],
        answer=2,
        why='An HTTP connection stores the host and the token, and you control who can call it with USE CONNECTION.',
    ),
    angle=angle(
        pattern='Rules in order, first match wins',
        text='The big idea: you choose the object by looking at where the target lives. Your code checks each target against simple rules in order: storage paths first, then Azure service hosts, then any other web address, then database addresses. The first rule that fits gives the answer, and anything unknown goes to a person. Checking the Azure hosts before the general "https://" rule matters, because both start the same way.',
        say='"I route by target: storage paths to [[external locations|service credentials|secret scopes::A storage path plus its credential.]], Azure service calls to [[service credentials|external locations|HTTP connections::Built on an access connector, not for storage.]], other web APIs to [[HTTP connections|foreign catalogs|volumes::Needs USE CONNECTION.]], and databases to federation connections."',
        classic=None,
    ),
    stack=stack('Connections in SQL', """-- A database, through Lakehouse Federation
CREATE CONNECTION orders_pg TYPE postgresql
  OPTIONS (host 'orders-fict.postgres.database.azure.com', port '5432',
           user secret('orders', 'user'), password secret('orders', 'password'));
CREATE FOREIGN CATALOG orders USING CONNECTION orders_pg OPTIONS (database 'orders');
GRANT USE CATALOG ON CATALOG orders TO `analysts`;

-- An outside web API, for agents and http_request
CREATE CONNECTION ticket_api TYPE HTTP
  OPTIONS (host 'https://api.tickets-fict.example', port '443', base_path '/v1',
           bearer_token secret('tickets', 'token'));
GRANT USE CONNECTION ON CONNECTION ticket_api TO `support-agents`;"""),
    exercise=exercise(
        title='Pick the Right Object',
        topic='credentials',
        difficulty='easy',
        fn='pick_securable',
        prompt="""`targets` is a list of strings: things some code wants to reach. Use your team's rules, checked in this order:

1. Starts with `"abfss://"`: `"external location"`.
2. Starts with `"https://"` and contains `".vault.azure.net"`, `".servicebus.windows.net"` or `".openai.azure.com"` (Key Vault, Event Hubs, Azure OpenAI): `"service credential"`.
3. Any other `"https://"`: `"http connection"`.
4. Starts with `"jdbc:"`, `"postgresql://"` or `"sqlserver://"`: `"connection (federation)"`.
5. Anything else: `"ask the platform team"`.

Return a list of `[target, answer]`, in the same order as `targets`.""",
        pattern='One small function with if / elif in rule order, called for each target.',
        target='one pass over the targets',
        realworld='This is the triage a platform team does on every new access request: "what are you trying to reach?" decides which object to create and which privilege to grant.',
        starter="""def pick_securable(targets):
    # your code here
    pass
""",
        solution="""def pick_one(target):
    if target.startswith("abfss://"):
        return "external location"
    if target.startswith("https://"):
        if ".vault.azure.net" in target or ".servicebus.windows.net" in target or ".openai.azure.com" in target:
            return "service credential"
        return "http connection"
    if target.startswith("jdbc:") or target.startswith("postgresql://") or target.startswith("sqlserver://"):
        return "connection (federation)"
    return "ask the platform team"


def pick_securable(targets):
    answers = []
    for target in targets:
        answers.append([target, pick_one(target)])
    return answers
""",
        cases=[
            case([
                'abfss://raw@lakefict.dfs.core.windows.net/sales',
                'https://kv-fict.vault.azure.net',
                'https://api.tickets-fict.example/v1',
            ], expected=[
                ['abfss://raw@lakefict.dfs.core.windows.net/sales', 'external location'],
                ['https://kv-fict.vault.azure.net', 'service credential'],
                ['https://api.tickets-fict.example/v1', 'http connection'],
            ], sample=True),
            case([], expected=[]),
            case([
                'postgresql://orders-fict.postgres.database.azure.com:5432/orders',
                'jdbc:sqlserver://erp-fict.database.windows.net:1433',
            ], expected=[
                ['postgresql://orders-fict.postgres.database.azure.com:5432/orders', 'connection (federation)'],
                ['jdbc:sqlserver://erp-fict.database.windows.net:1433', 'connection (federation)'],
            ]),
            case([
                'https://events-fict.servicebus.windows.net',
                'https://chat-fict.openai.azure.com/openai/deployments/small',
            ], expected=[
                ['https://events-fict.servicebus.windows.net', 'service credential'],
                ['https://chat-fict.openai.azure.com/openai/deployments/small', 'service credential'],
            ]),
            case([
                'ftp://old-fict.example/files',
                'sqlserver://erp-fict.database.windows.net',
            ], expected=[
                ['ftp://old-fict.example/files', 'ask the platform team'],
                ['sqlserver://erp-fict.database.windows.net', 'connection (federation)'],
            ]),
        ],
        guided="""def pick_one(target):
    # Replace every ___ with real code, then run the tests.

    if target.startswith("abfss://"):
        return "external location"

    if target.startswith("https://"):
        # Step 1: Azure service hosts come before the general web rule.
        if ".vault.azure.net" in target or ".servicebus.windows.net" in target or ".openai.azure.com" in target:
            return ___
        return "http connection"

    # Step 2: any of the three database starts.
    if target.startswith("jdbc:") or target.startswith("postgresql://") or ___:
        return "connection (federation)"

    return "ask the platform team"


def pick_securable(targets):
    answers = []
    for target in targets:
        # Step 3: the target, then its answer.
        answers.append(___)
    return answers
""",
        fills=['"service credential"', 'target.startswith("sqlserver://")', '[target, pick_one(target)]'],
        concepts=[
            [
                'Rules in order',
                'Python checks `if` blocks from the top. Put the more specific rule first, or the general one catches everything.',
                """def size(n):
    if n > 100: return 'huge'
    if n > 10: return 'big'
    return 'small'""",
            ],
            [
                'in on a string',
                '`"vault" in text` is True when those letters appear anywhere in the text.',
                """'.vault.azure.net' in 'https://kv.vault.azure.net'   # True""",
            ],
            [
                'or',
                '`a or b` is True when at least one side is True.',
                """day = 'sat'
day == 'sat' or day == 'sun'   # True""",
            ],
        ],
        byhand='The abfss path starts with "abfss://": external location. The Key Vault address starts with "https://" and contains ".vault.azure.net": service credential. The ticket API starts with "https://" but has no Azure host: http connection.',
        why='One pass over the targets, with a few short string checks each.',
        gotchas=[
            [
                'Service credentials are not for storage',
                'For storage paths Unity Catalog wants a storage credential and an external location, so it can govern files and tables. A service credential only gives your code a token for other cloud services.',
            ],
            [
                'Connections hide secrets, so guard them',
                'Anyone with `USE CONNECTION` can use the stored token or password through that connection. Grant it to the group or service principal that needs it, not to everyone.',
            ],
            [
                'Secret scopes have their own ACL',
                'A secret scope has `READ`, `WRITE` and `MANAGE` per principal. Unity Catalog grants do not reach it, so it is another place access gets forgotten.',
            ],
        ],
    ),
)

lesson(MODULE, 'masked_columns',
    title='ABAC: policies that follow tags',
    checked='2026-10-12',
    sources=[source('ABAC policies', 'https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies')],
    learn=[
        '**ABAC** (attribute-based access control) means rules follow labels on the data, not a list of tables. You write the rule once and it covers every table that carries the label.',
        'The labels are **governed tags**: tags defined for the whole account with a fixed set of allowed values, like `pii` with values `email`, `phone`, `ssn`. Data stewards put them on columns or tables.',
        'A **column mask policy** or **row filter policy** is attached to a catalog, schema or table. It matches columns by tag, applies `TO` some groups `EXCEPT` others, and runs a SQL function (a **UDF**, user-defined function) that does the hiding.',
        'New tables with the tag are covered at once, with no per-table work. That is why ABAC is recommended over per-table masks and filters when the same rule repeats.',
        'It needs serverless compute or Databricks Runtime 16.4 or above. Creating or changing a policy needs `MANAGE` on the object or ownership, plus `EXECUTE` on the function.',
    ],
    example=example('Mask every email column in a schema', """CREATE FUNCTION sales.gov.mask_email(email STRING) RETURNS STRING
  RETURN '***';

CREATE POLICY mask_emails
ON SCHEMA sales.crm
COLUMN MASK sales.gov.mask_email
TO `account users` EXCEPT `pii-readers`
FOR TABLES
MATCH COLUMNS has_tag_value('pii', 'email') AS c
ON COLUMN c;"""),
    check=question(
        'A policy masks columns tagged `pii=email` in schema `sales.crm`. Tomorrow someone adds a new table there with a tagged email column. What happens?',
        ['Nothing until someone adds a mask to the new table', 'The column is masked straight away, because the policy follows the tag', 'The table cannot be created'],
        answer=1,
        why='ABAC policies match by tag, so any new table with the tag is covered automatically.',
    ),
    angle=angle(
        pattern='For each item, does any rule match?',
        text='The big idea: a column is masked for you when some policy matches its tag and applies to you. Your code goes through the columns in order. For each one it tries every policy: does the column have that tag with that value? Are you in one of the "to" groups, or does "to" say everyone? Are you in none of the "except" groups? If one policy says yes to all three, the column goes in the list and you move on.',
        say='"For each column I look for a policy whose [[tag and value|name and size|owner and date::What the governed tag says on the column.]] match, that targets one of my groups, and that doesn\'t [[exempt|name|charge::The EXCEPT part.]] any of my groups. [[One|Every|Two::How many matching policies does it take?]] such policy is enough to mask it."',
        classic=None,
    ),
    stack=stack('A row filter policy, as a sketch', """CREATE FUNCTION sales.gov.not_eu(region STRING) RETURNS BOOLEAN
  RETURN region <> 'eu';

CREATE POLICY hide_eu_rows
ON SCHEMA sales.crm
ROW FILTER sales.gov.not_eu
TO `us-analysts`
FOR TABLES
WHEN has_tag_value('sensitivity', 'high')
MATCH COLUMNS has_tag('geo_region') AS region
USING COLUMNS (region);"""),
    exercise=exercise(
        title='Which Columns Are Masked?',
        topic='abac',
        difficulty='medium',
        fn='masked_columns',
        prompt="""Your function gets three things:

- `columns`: a table's columns. Each is a dict like `{"name": "email", "tags": {"pii": "email"}}`. `tags` can be empty.
- `policies`: column mask policies. Each is a dict like `{"tag": "pii", "value": "email", "to": ["account users"], "except": ["pii-readers"]}`.
- `groups`: the groups the user is in, like `["analysts"]`.

A policy masks a column for this user when all three are true:

1. The column's `tags` has the policy's `tag` with exactly the policy's `value`.
2. The user is in at least one `to` group, or `to` contains `"account users"` (everyone).
3. The user is in none of the `except` groups.

Return the names of the columns masked for this user, in column order. List each column once.""",
        pattern='Nested loops: for each column, try each policy. One policy that applies is enough to mask it.',
        target='one pass over the columns, trying each policy',
        realworld='This is what Unity Catalog works out on every query against a table under an ABAC policy. Writing it out shows why `EXCEPT` is how you let a small group, like `pii-readers`, see the real values.',
        starter="""def masked_columns(columns, policies, groups):
    # your code here
    pass
""",
        solution="""def in_any(groups, names):
    for group in groups:
        if group in names:
            return True
    return False


def masked_columns(columns, policies, groups):
    masked = []
    for column in columns:
        hit = False
        for policy in policies:
            if column["tags"].get(policy["tag"]) != policy["value"]:
                continue
            targeted = "account users" in policy["to"] or in_any(groups, policy["to"])
            exempt = in_any(groups, policy["except"])
            if targeted and not exempt:
                hit = True
        if hit:
            masked.append(column["name"])
    return masked
""",
        cases=[
            case([
                {'name': 'customer_id', 'tags': {}},
                {'name': 'email', 'tags': {'pii': 'email'}},
                {'name': 'phone', 'tags': {'pii': 'phone'}},
            ], [
                {'tag': 'pii', 'value': 'email', 'to': ['account users'], 'except': ['pii-readers']},
            ], ['analysts'], expected=['email'], sample=True),
            case([
                {'name': 'email', 'tags': {'pii': 'email'}},
            ], [
                {'tag': 'pii', 'value': 'email', 'to': ['account users'], 'except': ['pii-readers']},
            ], ['analysts', 'pii-readers'], expected=[]),
            case([
                {'name': 'email', 'tags': {'pii': 'email'}},
                {'name': 'phone', 'tags': {'pii': 'phone'}},
            ], [
                {'tag': 'pii', 'value': 'email', 'to': ['contractors'], 'except': []},
                {'tag': 'pii', 'value': 'phone', 'to': ['contractors', 'analysts'], 'except': []},
            ], ['analysts'], expected=['phone']),
            case([], [
                {'tag': 'pii', 'value': 'email', 'to': ['account users'], 'except': []},
            ], ['analysts'], expected=[]),
            case([
                {'name': 'email', 'tags': {'pii': 'email', 'domain': 'crm'}},
                {'name': 'salary', 'tags': {'sensitivity': 'high'}},
                {'name': 'notes', 'tags': {'pii': 'free_text'}},
            ], [
                {'tag': 'pii', 'value': 'email', 'to': ['account users'], 'except': []},
                {'tag': 'domain', 'value': 'crm', 'to': ['account users'], 'except': []},
                {'tag': 'sensitivity', 'value': 'high', 'to': ['account users'], 'except': ['hr']},
            ], ['analysts'], expected=['email', 'salary']),
            case([
                {'name': 'salary', 'tags': {'sensitivity': 'high'}},
            ], [
                {'tag': 'sensitivity', 'value': 'high', 'to': ['account users'], 'except': ['hr']},
            ], ['hr', 'managers'], expected=[]),
        ],
        guided="""def in_any(groups, names):
    # True when at least one of my groups is in names.
    for group in groups:
        if group in names:
            return True
    return False


def masked_columns(columns, policies, groups):
    # Replace every ___ with real code, then run the tests.

    masked = []
    for column in columns:
        hit = False
        for policy in policies:
            # Rule 1: the column must have this tag with this value.
            if column["tags"].get(policy["tag"]) != policy["value"]:
                continue

            # Rule 2: everyone, or one of my groups, is in "to".
            targeted = "account users" in policy["to"] or ___

            # Rule 3: none of my groups is in "except".
            exempt = in_any(groups, policy["except"])

            if targeted and ___:
                hit = True

        if hit:
            masked.append(column["name"])
    return masked
""",
        fills=['in_any(groups, policy["to"])', 'not exempt'],
        concepts=[
            [
                'A loop inside a loop',
                'The inner loop runs fully for each turn of the outer loop.',
                """for size in ['S', 'M']:
    for colour in ['red', 'blue']:
        print(size, colour)   # 4 lines""",
            ],
            [
                'continue',
                '`continue` skips the rest of this turn of the loop and moves to the next item.',
                """for n in [1, 2, 3]:
    if n == 2:
        continue
    print(n)   # prints 1 and 3""",
            ],
            [
                'A flag',
                'Start a True/False variable at False and set it to True when you find a match. Check it after the loop.',
                """found = False
for x in [3, 8]:
    if x > 5: found = True""",
            ],
            [
                'dict.get with no default',
                '`tags.get("pii")` gives None when the key is missing, so it never equals a real value.',
                """tags = {'pii': 'email'}
tags.get('domain')   # None""",
            ],
        ],
        byhand='customer_id has no tags: no policy matches. email has pii=email, which matches the policy. "to" has account users, so analysts are targeted; analysts are not in pii-readers, so not exempt: mask it. phone has pii=phone, which is not "email": no match. Return ["email"].',
        why='Each column tries each policy once, and each try checks a few short lists.',
        gotchas=[
            [
                'Tags are only as good as the tagging',
                'A column with no tag is not masked. Pair ABAC with a check that new PII columns get tagged, for example data classification or a review step.',
            ],
            [
                'EXCEPT wins',
                'Being in any `EXCEPT` group exempts you, even if you are also in a `TO` group. Keep exempt groups small and reviewed.',
            ],
            [
                'Older compute',
                'Compute below Databricks Runtime 16.4 (and not serverless) cannot read tables under ABAC policies. Upgrade clusters before you switch policies on.',
            ],
        ],
    ),
)

lesson(MODULE, 'grants_to_people',
    title='Grant to groups, run as service principals',
    checked='2026-10-12',
    sources=[source('Users, groups and service principals', 'https://docs.databricks.com/aws/en/admin/users-groups/'), source('Unity Catalog privileges', 'https://docs.databricks.com/aws/en/data-governance/unity-catalog/manage-privileges/privileges')],
    learn=[
        'Grant to **groups**, not to people. People move teams and leave; a grant to a person goes stale, while a group\'s membership is managed in one place.',
        'Groups usually come from **Entra ID** (Azure\'s sign-in and user directory), synced by **SCIM** provisioning (a standard way to copy users and groups between systems) or by automatic identity management.',
        'Jobs and production apps should run as a **service principal**: an identity for software, not a person. On Azure its name is an application ID, a long id like `6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10`.',
        'Owners should be groups too. If a person owns a catalog, job or experiment and leaves, things break or nobody can change them.',
        'This applies to every list in this module: table grants, experiment and cluster ACLs, service credentials and connections. A person\'s email in any of them is a smell.',
    ],
    example=example('Who is who in a grant list', """ana@example.com                          -> a person   (flag it)
data-engineers                           -> a group    (good)
6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10     -> a service principal (good for jobs)"""),
    check=question(
        'A nightly job runs as Ana and reads three tables. Ana moves to another team and loses access. What should have been done?',
        ['Give Ana permanent access', 'Run the job as a service principal with its own grants', 'Copy the tables into Ana\'s new team'],
        answer=1,
        why='A service principal belongs to no one, so the job keeps working when people move.',
    ),
    angle=angle(
        pattern='Filter by a simple mark',
        text='The big idea: people show up in grant lists by their email address, so an "@" is a cheap, reliable sign of a grant to a person. Your code goes through the grants in order and keeps every one whose principal contains "@". Groups have plain names and service principals have application IDs, so neither contains "@" and neither is flagged.',
        say='"I flag every grant whose principal is an [[email address|application ID|group name::Something with an @ in it.]], because those are grants to [[people|programs|teams::They move teams and leave.]]. Groups and [[service principals|admins|owners::Identities for programs and jobs.]] pass."',
        classic=None,
    ),
    stack=stack('Groups and a service principal in Terraform', """resource "databricks_grants" "crm" {
  schema = "sales.crm"
  grant {
    principal  = "analysts"                                # a group
    privileges = ["USE_SCHEMA", "SELECT"]
  }
  grant {
    principal  = "6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10"    # the job's service principal
    privileges = ["USE_SCHEMA", "SELECT", "MODIFY"]
  }
}

resource "databricks_job" "nightly" {
  name = "nightly-scores"
  run_as {
    service_principal_name = "6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10"
  }
  # tasks ...
}"""),
    exercise=exercise(
        title='Find Grants to People',
        topic='identity',
        difficulty='easy',
        fn='grants_to_people',
        prompt="""`grants` is a list of grants. Each is a dict like `{"principal": "analysts", "privilege": "SELECT", "on": "sales.crm"}`.

Principals come in three kinds:

- People: an email address, like `"ana@example.com"`.
- Groups: a plain name, like `"data-engineers"`.
- Service principals: an application ID, like `"6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10"`.

Find the grants to people: the ones whose principal contains `"@"`. Return `[principal, privilege, on]` for each, in the same order as `grants`.""",
        pattern='Filter, then reshape: keep the matching dicts and turn each into a short list.',
        target='one pass over the grants',
        realworld='Run this over `SHOW GRANTS` output, or over the Permissions API for experiments, clusters and jobs, to find grants that will break when someone leaves. Then move each one to a group.',
        starter="""def grants_to_people(grants):
    # your code here
    pass
""",
        solution="""def grants_to_people(grants):
    people = []
    for grant in grants:
        if "@" in grant["principal"]:
            people.append([grant["principal"], grant["privilege"], grant["on"]])
    return people
""",
        cases=[
            case([
                {'principal': 'ana@example.com', 'privilege': 'SELECT', 'on': 'sales.crm.accounts'},
                {'principal': 'data-engineers', 'privilege': 'MODIFY', 'on': 'sales.crm'},
                {'principal': '6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10', 'privilege': 'SELECT', 'on': 'sales.crm'},
            ], expected=[['ana@example.com', 'SELECT', 'sales.crm.accounts']], sample=True),
            case([], expected=[]),
            case([
                {'principal': 'analysts', 'privilege': 'USE CATALOG', 'on': 'sales'},
                {'principal': 'analysts', 'privilege': 'USE SCHEMA', 'on': 'sales.crm'},
            ], expected=[]),
            case([
                {'principal': 'bo@example.com', 'privilege': 'USE CATALOG', 'on': 'sales'},
                {'principal': 'kai@example.com', 'privilege': 'ALL PRIVILEGES', 'on': 'sales.crm'},
            ], expected=[['bo@example.com', 'USE CATALOG', 'sales'], ['kai@example.com', 'ALL PRIVILEGES', 'sales.crm']]),
            case([
                {'principal': 'ml-team', 'privilege': 'EXECUTE', 'on': 'ml.models.churn'},
                {'principal': 'ana@example.com', 'privilege': 'EXECUTE', 'on': 'ml.models.churn'},
                {'principal': '0b9d7e21-5c3a-4f6b-8e2d-1a4c6f8b0d39', 'privilege': 'EXECUTE', 'on': 'ml.models.churn'},
                {'principal': 'bo@example.com', 'privilege': 'MANAGE', 'on': 'ml.models'},
            ], expected=[['ana@example.com', 'EXECUTE', 'ml.models.churn'], ['bo@example.com', 'MANAGE', 'ml.models']]),
        ],
        guided="""def grants_to_people(grants):
    # Replace every ___ with real code, then run the tests.

    people = []
    for grant in grants:
        # Step 1: an email address has an "@" in it.
        if ___:
            # Step 2: principal, privilege, on, in that order.
            people.append(___)
    return people
""",
        fills=['"@" in grant["principal"]', '[grant["principal"], grant["privilege"], grant["on"]]'],
        concepts=[
            [
                'in on a string',
                '`"@" in text` is True when the text contains that character anywhere.',
                """'@' in 'ana@example.com'   # True
'@' in 'analysts'          # False""",
            ],
            [
                'Building a small list',
                'Square brackets with values inside make a new list.',
                """name = 'ana'
row = [name, 'SELECT']   # ['ana', 'SELECT']""",
            ],
            [
                'Building a result list',
                'Start with an empty list, append each match in the loop, return it at the end.',
                """found = []
found.append('ana')   # ['ana']""",
            ],
        ],
        byhand='Grant 1 is to ana@example.com: it has an "@", so keep ["ana@example.com", "SELECT", "sales.crm.accounts"]. Grant 2 is to data-engineers, a group: skip. Grant 3 is to an application ID, a service principal: skip.',
        why='One pass over the grants, with one character check each.',
        gotchas=[
            [
                'Owners count too',
                'Ownership is not in the grant list but gives every privilege. Check `owner` on catalogs, schemas, jobs and experiments, and set it to a group or service principal.',
            ],
            [
                'Groups must be account-level',
                'Unity Catalog grants work with account-level groups. Old workspace-local groups cannot be granted Unity Catalog privileges; migrate them to account groups.',
            ],
            [
                'Service principals need the whole list too',
                'A job\'s service principal needs table grants, `CAN_USE` on the warehouse or cluster policy, and access to any experiment, credential or connection it touches. Missing one fails the first scheduled run.',
            ],
        ],
    ),
)
