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

planned(MODULE, 'workspace_metastore', 'A workspace, a metastore and a catalog', 'How one Unity Catalog metastore serves several workspaces, and where catalogs live.')
lesson(MODULE, 'private_networking',
    title='Private networking: VNet injection and Private Link',
    checked='2026-11-27',
    sources=[source('Deploy Azure Databricks in your Azure virtual network (VNet injection)', 'https://learn.microsoft.com/azure/databricks/security/network/classic/vnet-inject'), source('Secure cluster connectivity', 'https://learn.microsoft.com/azure/databricks/security/network/classic/secure-cluster-connectivity'), source('Private Link', 'https://learn.microsoft.com/azure/databricks/security/network/classic/private-link'), source('Update workspace network configuration', 'https://learn.microsoft.com/azure/databricks/security/network/classic/update-workspaces')],
    learn=[
        "By default, Databricks puts a workspace's clusters in a network it makes and runs itself, a **managed VNet** (VNet: an Azure virtual network). With **VNet injection** you bring your own VNet instead: two **subnets** (slices of the VNet's addresses) for the workspace, host and container, each handed over (delegated) to Databricks, with a **network security group** (Azure's traffic rules for a subnet) whose rules Databricks manages. Don't edit those rules; you can add your own beside them. In Terraform the host subnet is `public_subnet_name` and the container subnet is `private_subnet_name`.",
        "**Secure cluster connectivity** gives clusters no **public IP address** (an address anyone on the internet can reach), and it is on by default. Clusters still need a way out to the internet, and Azure gives none by default to VNets made after 31 March 2026, so add one: Databricks recommends a **NAT gateway** (one fixed exit to the internet) on both subnets.",
        "**Private Link** connects through a private endpoint, a private address inside your own network, so traffic doesn't use the workspace's public address and you can turn public access off. **Front-end** (inbound) Private Link is for people and tools reaching the workspace; **back-end** is for clusters reaching Databricks' **control plane**, the part Databricks runs for you, which hosts the web app and starts your clusters. Both need the Premium plan, VNet injection and secure cluster connectivity.",
        "Each workspace also has its own storage account in the managed resource group. Its **workspace storage firewall**, which blocks public access to that account, needs VNet injection, secure cluster connectivity and the Premium plan.",
        "Plan the network before the first apply. In Terraform, changing the VNet or a subnet makes a new workspace, and Microsoft's steps for changing the network of a live workspace don't support Terraform. Databricks also plans to require VNet injection for new classic workspaces (ones whose clusters run in your Azure subscription, not serverless), with no date yet.",
    ],
    example=example('A VNet-injected workspace (a network\'s size follows the slash: a smaller number is bigger)', """your VNet 10.10.0.0/20
  host subnet 10.10.0.0/23
    delegated to Databricks
  container subnet 10.10.2.0/23
    delegated to Databricks
  NAT gateway on both
  clusters: no public IPs"""),
    check=question(
        'Clusters in a new VNet-injected workspace can\'t reach the internet. Secure cluster connectivity is on, and there is no NAT gateway. What is missing?',
        [
            'A way out, like a NAT gateway',
            'Public IPs on every cluster',
            'A bigger pair of subnets',
        ],
        answer=0,
        why='With no public IPs, clusters need an explicit way out, and new VNets get none by default. A NAT gateway on both subnets is what Databricks recommends.',
    ),
    angle=angle(
        pattern='Check each rule the network must meet',
        text='The big idea: a VNet-injected workspace has a few network rules and recommendations, and some can\'t be fixed later without a new workspace. Your code checks a planned network, one at a time: the VNet size it must have, the /26 or bigger subnets Databricks recommends, a way out for clusters, and that the storage firewall is only on when VNet injection is too. It lists every rule that fails. It is like a building inspection: each rule on the list gets a tick or a note.',
        say='"With VNet injection our clusters run in [[our own|a shared|a public::A VNet you bring and manage.]] VNet. Secure cluster connectivity takes away their public IPs, so they need a way out, like a [[NAT gateway|bigger subnet|second workspace::What Databricks recommends on both subnets.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Does This Network Pass?',
        topic='azure-databricks',
        difficulty='easy',
        fn='network_issues',
        prompt="""Your function gets `net`, a dict describing a planned workspace network:

- `"injected"`: `True` for VNet injection, `False` for a managed VNet.
- `"vnet_prefix"`: the VNet's size as a number, like `20` for a /20.
- `"subnet_prefixes"`: the two subnets' sizes, like `[23, 23]`.
- `"nat"`: `True` if there is a NAT gateway.
- `"storage_firewall"`: `True` if the workspace storage firewall is on.

Return the issues, in this order:

- injected and `vnet_prefix` isn't from 16 to 24 -> `"VNet must be /16 to /24"`
- injected and any subnet prefix is bigger than 26 -> `"subnets smaller than /26"`
- injected and no NAT -> `"add a way out, like a NAT gateway"`
- storage firewall on and not injected -> `"storage firewall needs VNet injection"`

(A bigger prefix number means a smaller network: a /27 is smaller than a /26.)""",
        pattern='One check per rule, in a fixed order.',
        target='four checks',
        realworld='These are the rules a platform team checks before the first apply, because fixing a network afterwards means a new workspace or Microsoft\'s manual steps outside Terraform.',
        practice=practice(
            intro='A team is moving its workspaces onto its own VNet. Check its choices before anything is built.',
            explain='A VNet-injected workspace works only inside a few rules. You kept clusters\' way out, left Databricks\' network rules alone, stopped a change that would rebuild the workspace, and saw that the storage firewall needs VNet injection.',
            pattern='Get the network right before the first apply',
            realworld='When you review a workspace network, you check the VNet and subnet sizes, the NAT gateway and the network security group, and you stop any change that would replace the workspace.',
            asks=[
                ask('To save money, someone wants to remove the NAT gateway. What happens to the clusters?', ['They lose their way out', 'They start up faster', 'Nothing at all changes'], answer=0,
                    alone=True,
                    clue='With no public IPs, how else would a cluster reach the internet?',
                    why='Clusters have no public IPs, and the subnets give no way out by default, so without the NAT gateway they can\'t reach anything outside.',
                    wrong=[None, 'Removing the way out doesn\'t speed anything up.', 'Clusters that need the internet, for packages or Azure services, start failing.']),
                ask('A security review wants to tighten the network security group rules Databricks added. What do you say?', ['Don\'t edit them: the workspace needs them', 'Delete the ones nobody recognises', 'Copy them to a new security group'], answer=0,
                    alone=True,
                    clue='Who manages those rules, and what are they for?',
                    why='Databricks manages those rules through the subnet delegation, and the workspace needs them to work. To tighten things, add your own rules next to them, or send traffic through a firewall with your own routes.',
                    wrong=[None, 'Those are the rules the workspace runs on.', 'Add your own rules next to them instead; the managed ones stay.']),
                ask('Someone pointed the workspace\'s public_subnet_name at a different subnet. The plan shows this. What do you do?', ['Stop: it makes a new workspace', 'Apply: only the subnet changes', 'Apply it out of working hours'], answer=0,
                    evidence=evidence('plan', title='Stack sales-foundation-dev · proposed',
                        summary=[['1', 'to add', 'a'], ['0', 'to change', ''], ['1', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-/+', 'address': 'azurerm_databricks_workspace.this', 'note': 'public_subnet_name: forces replacement'},
                        ]),
                    clue='What does -/+ do to the workspace?',
                    why='Changing a subnet name replaces the whole workspace. Put the old name back, and use Microsoft\'s documented steps if the network really must change.',
                    wrong=[None, 'The plan replaces the workspace itself, not just the subnet.', 'The time doesn\'t matter: the workspace would still be replaced.']),
                ask('The workspace storage firewall fails to switch on for a workspace on a managed VNet. What does it need?', ['VNet injection first', 'The standard sku', 'A bigger NAT gateway'], answer=0,
                    alone=True,
                    clue='Which kind of network does the storage firewall build on?',
                    why='The workspace storage firewall needs VNet injection and secure cluster connectivity, on the Premium plan, with an access connector. A managed VNet can\'t have it.',
                    wrong=[None, 'It needs Premium, not standard.', 'A NAT gateway is the clusters\' way out; the firewall needs injection.']),
            ],
        ),
        starter="""def network_issues(net):
    # your code here
    pass
""",
        solution="""def network_issues(net):
    issues = []
    if net["injected"]:
        if not 16 <= net["vnet_prefix"] <= 24:
            issues.append("VNet must be /16 to /24")
        if any(p > 26 for p in net["subnet_prefixes"]):
            issues.append("subnets smaller than /26")
        if not net["nat"]:
            issues.append("add a way out, like a NAT gateway")
    if net["storage_firewall"] and not net["injected"]:
        issues.append("storage firewall needs VNet injection")
    return issues
""",
        cases=[
            case({'injected': True, 'vnet_prefix': 20, 'subnet_prefixes': [23, 23], 'nat': True, 'storage_firewall': True}, expected=[], sample=True),
            case({'injected': True, 'vnet_prefix': 25, 'subnet_prefixes': [27, 27], 'nat': True, 'storage_firewall': False}, expected=['VNet must be /16 to /24', 'subnets smaller than /26']),
            case({'injected': True, 'vnet_prefix': 20, 'subnet_prefixes': [23, 23], 'nat': False, 'storage_firewall': False}, expected=['add a way out, like a NAT gateway']),
            case({'injected': False, 'vnet_prefix': 0, 'subnet_prefixes': [], 'nat': False, 'storage_firewall': True}, expected=['storage firewall needs VNet injection']),
            case({'injected': False, 'vnet_prefix': 0, 'subnet_prefixes': [], 'nat': False, 'storage_firewall': False}, expected=[]),
            case({'injected': True, 'vnet_prefix': 16, 'subnet_prefixes': [26, 28], 'nat': True, 'storage_firewall': False}, expected=['subnets smaller than /26']),
        ],
        guided="""def network_issues(net):
    # Replace every ___ with real code, then run the tests.
    issues = []
    if net["injected"]:
        if not 16 <= net["vnet_prefix"] <= 24:
            issues.append("VNet must be /16 to /24")
        if ___:
            issues.append("subnets smaller than /26")
        if not net["nat"]:
            issues.append("add a way out, like a NAT gateway")
    if ___:
        issues.append("storage firewall needs VNet injection")
    return issues
""",
        fills=['any(p > 26 for p in net["subnet_prefixes"])', 'net["storage_firewall"] and not net["injected"]'],
        concepts=[
            [
                'A range check',
                '`16 <= x <= 24` is True when x is anywhere from 16 to 24.',
                """16 <= 20 <= 24   # True""",
            ],
            [
                'any()',
                '`any(...)` is True if at least one item passes.',
                """any(p > 26 for p in [23, 27])   # True""",
            ],
        ],
        byhand='The sample: VNet injection with a /20 VNet (inside 16 to 24), two /23 subnets (not smaller than /26), a NAT gateway, and the firewall on with injection under it. No issues: return [].',
        why='Four checks.',
        gotchas=[
            [
                'The storage firewall needs injection',
                'The workspace storage firewall works only with VNet injection and secure cluster connectivity, on Premium, with an access connector. On a managed VNet, Azure refuses it at apply time.',
            ],
            [
                'Moving networks means stopping clusters',
                'Microsoft\'s steps for moving a live workspace to new subnets or a new VNet need running clusters and jobs stopped, and they aren\'t done through Terraform. Plan a window, and update the code afterwards to match.',
            ],
        ],
    ),
)
