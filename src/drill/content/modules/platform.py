"""Databricks as code: the workspace, catalogs and network of an ML platform, kept in Terraform."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, module, planned, practice, question, stack, source

MODULE = module('platform', 'Databricks as code', 'The workspace, catalogs and network of an ML platform, kept in Terraform.', setting=PLATFORM_SETTING)


lesson(MODULE, 'missing_tags',
    title='Tagging for cost and policy',
    checked='2026-10-13',
    sources=[source('Use tags to organize your Azure resources', 'https://learn.microsoft.com/azure/azure-resource-manager/management/tag-resources'), source('Manage tag governance with Azure Policy', 'https://learn.microsoft.com/azure/governance/policy/tutorials/govern-tags')],
    learn=[
        'Azure tags drive **cost allocation** and **Azure Policy**. Missing tags mean spend nobody can attribute.',
        'The azurerm provider (Terraform\'s plugin for Azure) has no provider-wide default tags, so teams merge a shared `local.tags` into every resource, and check plans for gaps.',
    ],
    example=example('A shared tag map', """locals {
  tags = { env = var.env, owner = "platform", cost-center = "1234" }
}
tags = merge(local.tags, { component = "dbw" })"""),
    check=question(
        'Which of these resources should your tag check skip?',
        [
            '`azurerm_databricks_workspace`',
            '`databricks_catalog`',
            '`azurerm_storage_account`',
        ],
        answer=1,
        why="Resources from the databricks provider (names starting `databricks_`, like `databricks_catalog`) have no Azure tags attribute. `azurerm_databricks_*` resources, like the workspace, are Azure resources, so they do.",
    ),
    angle=angle(
        pattern='List the gaps per resource',
        text='The big idea: tags decide who pays for what, and the azurerm provider has no default tags, so teams check every plan for gaps. Your code skips any resource with no `"tags"` key, since it can\'t be tagged. For every other resource, it goes through `required` in order and lists each name missing from its tags. If that list isn\'t empty, it goes into a dict, a lookup table from each address to its missing names. Resources with nothing missing are left out.',
        say='"Tags decide [[who pays|who owns|who logs in::Think about splitting the cloud bill.]] for what. I skip resources that [[can\'t be tagged|are already tagged|cost nothing::They have no tags field at all.]], then list the [[required|optional|extra::The tags every resource must have.]] tags each one is missing."',
        classic=None,
    ),
    exercise=exercise(
        title='Enforce Required Tags',
        topic='tagging',
        difficulty='medium',
        fn='missing_tags',
        prompt="""Your function gets two things:

- `resources`: the resources a plan creates or updates. Each one is a dict like `{"address": "azurerm_storage_account.lake", "tags": {"env": "prod"}}`.
- `required`: the tag names every resource must have, like `["env", "owner"]`.

Some resources can't be tagged, such as subnets and resources from the databricks provider (names starting `databricks_`, like `databricks_catalog`). They have no `"tags"` key: skip them. `azurerm_databricks_*` resources are Azure resources, so they do have tags.

For every other resource, list the `required` tag names that are missing from its `tags`, in the same order as `required`. Return a dict. Each key is a resource's `address` and its value is that resource's list of missing tag names. Leave out resources with nothing missing.""",
        pattern="Dict of results, filled only when something is missing.",
        target='one pass over the resources',
        realworld="Cost allocation and Azure Policy both depend on tags. Catching a missing `cost-center` in the PR's Spacelift run is much cheaper than finding untagged spend at the end of the month.",
        practice=practice(
            intro='Check a plan for missing tags the way a platform reviewer does: which resources have gaps, and which tags they lack.',
            explain='Tags decide who pays for what, and azurerm has no default tags, so you checked the plan for gaps. You listed the required tags each resource was missing, caught a resource that forgot to merge the shared tags, and saw that cluster costs need tags of their own.',
            asks=[
                ask('Every resource needs `env` and `owner`. Which one is missing a tag?', ['`azurerm_storage_account.lake`', '`azurerm_databricks_workspace.this`', '`databricks_catalog.sales`'], answer=1,
                    evidence=evidence('code', title='Resources in the plan, with their tags', text="""[
  {"address": "azurerm_storage_account.lake",
   "tags": {"env": "prod", "owner": "data"}},
  {"address": "azurerm_databricks_workspace.this",
   "tags": {"env": "prod"}},
  {"address": "databricks_catalog.sales"}
]"""),
                    clue='Check each tags list for both names. Skip anything with no tags list at all.',
                    why='The workspace has env but no owner, so its cost has nobody to go to. The storage account has both, and the catalog can\'t be tagged.',
                    wrong=['It has both env and owner.', None, 'It has no tags at all: the databricks provider can\'t tag it, so the check skips it.']),
                ask('Now every resource needs `owner`, `env` and `cost-center`. What is the workspace missing?', ['`env` and `cost-center`', 'Only `cost-center`', 'Nothing: it has an owner'], answer=0,
                    evidence=evidence('code', title='Another plan', text="""[
  {"address": "azurerm_databricks_access_connector.uc",
   "tags": {"env": "dev"}},
  {"address": "azurerm_subnet.host"},
  {"address": "azurerm_databricks_workspace.this",
   "tags": {"owner": "ana"}}
]"""),
                    clue='Go through the three required names one by one.',
                    why='The workspace only has owner, so env and cost-center are both missing. List every gap, so it can be fixed in one go.',
                    wrong=[None, 'It has no env either.', 'Owner is only one of the three.']),
                ask('Which resource will the tag check flag?', ['`azurerm_storage_account.lake`', '`azurerm_databricks_access_connector.uc`', 'Neither: each one sets its own tags'], answer=1,
                    evidence=evidence('code', title='storage.tf', text="""locals {
  tags = { env = var.env, owner = "platform", cost-center = "1234" }
}

resource "azurerm_storage_account" "lake" {
  # ...
  tags = merge(local.tags, { component = "lake" })
}

resource "azurerm_databricks_access_connector" "uc" {
  # ...
  tags = { component = "uc" }
}"""),
                    clue='Which one leaves out the shared `local.tags`?',
                    why='The connector sets its own tags without merging `local.tags`, so it has only component: env, owner and cost-center are all missing. azurerm has no default tags to fill them in.',
                    wrong=['It merges the shared tags, so it has every one.', None, 'Having some tags isn\'t enough: the connector has none of the required ones.']),
                ask('Several teams share this workspace, and an AI assistant says this. Is it right?', ['Yes: workspace tags cover everything inside it', 'No: each cluster needs its own `custom_tags`'], answer=1,
                    evidence=evidence('claim', text='The workspace has every required tag, so each team\'s cluster costs are split out too.'),
                    clue='Clusters have a tags field of their own, which this check doesn\'t look at.',
                    why='Workspace tags reach the resources Databricks makes for it, but they are the same for everyone. To split compute cost by team, set `custom_tags` on each cluster.',
                    wrong=['Every cluster gets the same workspace tags, so they can\'t tell teams apart.', None]),
            ],
        ),
        starter="""def missing_tags(resources, required):
    # your code here
    pass
""",
        solution="""def missing_tags(resources, required):
    problems = {}
    for resource in resources:
        if "tags" not in resource:
            continue
        tags = resource["tags"]
        missing = []
        for key in required:
            if key not in tags:
                missing.append(key)
        if missing:
            problems[resource["address"]] = missing
    return problems
""",
        cases=[
            case([
                {'address': 'azurerm_storage_account.lake', 'tags': {'env': 'prod', 'owner': 'data'}},
                {'address': 'azurerm_databricks_workspace.this', 'tags': {'env': 'prod'}},
                {'address': 'databricks_catalog.sales'},
            ], ['env', 'owner'], expected={'azurerm_databricks_workspace.this': ['owner']}, sample=True),
            case([
                {'address': 'azurerm_storage_account.lake', 'tags': {}},
            ], ['env'], expected={'azurerm_storage_account.lake': ['env']}),
            case([
                {
                    'address': 'azurerm_databricks_access_connector.uc',
                    'tags': {'env': 'dev', 'owner': 'platform', 'cost-center': '1234'},
                },
            ], ['owner', 'env', 'cost-center'], expected={}),
            case([], ['env'], expected={}),
            case([
                {'address': 'azurerm_databricks_access_connector.uc', 'tags': {'env': 'dev'}},
                {'address': 'azurerm_subnet.host'},
                {'address': 'azurerm_databricks_workspace.this', 'tags': {'owner': 'ana'}},
            ], ['owner', 'env', 'cost-center'], expected={
                'azurerm_databricks_access_connector.uc': ['owner', 'cost-center'],
                'azurerm_databricks_workspace.this': ['env', 'cost-center'],
            }),
        ],
        guided="""def missing_tags(resources, required):
    # Replace every ___ with real code, then run the tests.

    problems = {}
    for resource in resources:
        # Step 1: no "tags" key means it can't be tagged.
        # Skip it.
        if ___:
            continue
        tags = resource["tags"]

        # Step 2: collect each required key that tags lacks.
        missing = []
        for key in required:
            if ___:
                missing.append(key)

        # Step 3: if anything is missing, store the list
        # in problems under this resource's address.
        if missing:
            ___

    return problems
""",
        fills=['"tags" not in resource', 'key not in tags', 'problems[resource["address"]] = missing'],
        concepts=[
            [
                'not in on a dict',
                '`key not in a_dict` is True when the dict has no such key.',
                """prices = {'tea': 2}
'cake' not in prices   # True""",
            ],
            [
                'continue',
                'Skips the rest of this turn of the loop and moves on to the next item.',
                """for n in [1, 2, 3]:
    if n == 2: continue
    print(n)   # prints 1, then 3""",
            ],
            [
                'An empty list counts as False',
                '`if a_list:` runs its block only when the list has at least one item.',
                """basket = []
if basket: print('not empty')   # prints nothing""",
            ],
            [
                'Adding to a dict',
                '`a_dict[key] = value` stores a value under a key.',
                """ages = {}
ages['ana'] = 30   # {'ana': 30}""",
            ],
        ],
        byhand='Required: env and owner. The storage account has both, so nothing is missing: leave it out. The workspace has env but not owner: missing ["owner"]. The catalog has no tags key: skip it. Return {"azurerm_databricks_workspace.this": ["owner"]}.',
        why='One pass over the resources; each tag check is a dict lookup.',
        gotchas=[
            [
                'azurerm has no default_tags',
                'Unlike the AWS provider, azurerm can\'t tag everything for you. Teams keep a `local.tags` map and merge it into every resource: `tags = merge(local.tags, { component = "dbw" })`. A check like this one catches the resources someone forgot.',
            ],
            [
                'Workspace tags reach the managed resource group',
                "Tags on `azurerm_databricks_workspace` are applied to the resources Databricks creates in its managed resource group, which you can't tag directly. Clusters use a separate `custom_tags` field, which this check doesn't look at. Set it too, so compute cost can be split by team.",
            ],
        ],
    ),
)

lesson(MODULE, 'grants_to_revoke',
    title='Unity Catalog grants',
    checked='2026-10-13',
    sources=[source('databricks_grants resource', 'https://registry.terraform.io/providers/databricks/databricks/latest/docs/resources/grants'), source('databricks_grant resource', 'https://registry.terraform.io/providers/databricks/databricks/latest/docs/resources/grant')],
    learn=[
        '**Unity Catalog** controls who can use which data. `databricks_grants` is **authoritative**: on apply it makes the grants match the code exactly, removing anything else.',
        'Grants added by hand in Catalog Explorer disappear at the next apply. Put them in code, or use the non-authoritative `databricks_grant` for that principal (the user, group or service being given access).',
    ],
    example=example('Authoritative grants', """resource "databricks_grants" "sales" {
  catalog = databricks_catalog.sales.name
  grant {
    principal  = "data-engineers"
    privileges = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
  }
}"""),
    check=question(
        'Someone gave `analysts` SELECT in the UI. The code uses `databricks_grants` without analysts. What happens at the next apply?',
        ['Nothing', "The analysts' grant is removed", 'The apply fails'],
        answer=1,
        why='Authoritative means the code is the whole list.',
    ),
    angle=angle(
        pattern='Live minus code, per principal',
        text="The big idea: `databricks_grants` makes the live grants match the code exactly, so anything not in code is removed at the next apply. Your code goes through each principal in `live`. It finds that principal's privileges in `code` with `code.get(principal, [])`, which gives an empty list if the principal is missing, so they lose everything. Each live privilege not in that list is added to a list called `gone`. Principals who lose something are stored in a dict, a lookup table from name to list.",
        say='"databricks_grants makes the live grants match the code [[exactly|roughly|eventually::Terraform owns the whole list for that object.]]. So anything someone added by hand, that [[isn\'t in the code|is in the code|was added today::Terraform only keeps what it can see written down.]], gets [[removed|kept|logged::The next apply puts things back to what the code says.]] on the next apply."',
        classic=None,
    ),
    exercise=exercise(
        title='Predict Grant Drift',
        topic='unity-catalog',
        difficulty='medium',
        fn='grants_to_revoke',
        prompt="""Your function gets two things:

- `code`: the grants written in Terraform, like `{"analysts": ["SELECT"]}`. It's a dict. Each key is a principal (a user, group or service that can be given access). Its value is that principal's list of privileges (permissions, like `SELECT` to read data).
- `live`: the grants that exist in Databricks right now, in the same shape.

`databricks_grants` makes the live grants match the code. So the next apply (the next time Terraform makes its changes) removes every privilege in `live` but not in `code`. A principal missing from `code` loses everything.

Return a dict in the same shape, with the privileges each principal will lose, in the same order as in `live`. Leave out principals that lose nothing.""",
        pattern="For each principal, keep the live privileges that the code doesn't list. A principal missing from `code` loses everything.",
        target='one pass over the live grants',
        realworld='This is the classic surprise with `databricks_grants`: a manual grant in the UI quietly disappears at the next Spacelift apply. Either put it in code, or manage that principal with the non-authoritative `databricks_grant` instead.',
        practice=practice(
            intro='Predict what the next apply does to a catalog\'s grants, the way a reviewer does before approving.',
            explain='databricks_grants makes the live grants match the code exactly, so anything not in the code is removed at the next apply. You compared live with code for each principal, found a lost privilege hiding inside an in-place change, and kept a grant the safe way: by writing it into the code.',
            asks=[
                ask('What does `engineers` lose at the next apply?', ['`MODIFY`', '`SELECT`', 'Nothing'], answer=0,
                    evidence=evidence('code', title='Catalog sales: code and live', text="""# In the code (databricks_grants)
engineers:  USE_CATALOG, SELECT

# Live in Databricks right now
engineers:  USE_CATALOG, SELECT, MODIFY
analysts:   SELECT"""),
                    clue='Find the privilege it has live that the code doesn\'t list.',
                    why='The code lists USE_CATALOG and SELECT for engineers, so MODIFY, added by hand, is removed. They can still read, but no longer change data.',
                    wrong=[None, 'SELECT is in the code, so it stays.', 'Live has one more privilege than the code lists.']),
                ask('The plan says **0 to destroy**. Does anyone lose access?', ['No: nothing is destroyed', 'Yes: analysts lose SELECT'], answer=1,
                    evidence=evidence('code', title='From the planning log', text="""  ~ resource "databricks_grants" "sales" {
        id      = "catalog/sales"
      - grant {
          - principal  = "analysts" -> null
          - privileges = [
              - "SELECT",
            ] -> null
        }

        # (1 unchanged block hidden)
    }

Plan: 0 to add, 1 to change, 0 to destroy."""),
                    clue='Look inside the change marked ~ for lines starting with -.',
                    why='The grants resource is changed in place, but the change removes the analysts\' grant block. "0 to destroy" only counts resources, not the access inside them.',
                    wrong=['No resource is destroyed, but one is changed, and the change removes a grant.', None]),
                ask('The analysts need to keep SELECT. What do you change?', ['Add analysts to the `databricks_grants` block in the code', 'Grant it again in the UI after each apply', 'Add a `databricks_grant` for analysts on the same catalog'], answer=0,
                    evidence=evidence('code', title='catalogs.tf', text="""resource "databricks_grants" "sales" {
  catalog = databricks_catalog.sales.name
  grant {
    principal  = "engineers"
    privileges = ["USE_CATALOG", "SELECT"]
  }
}"""),
                    clue='This resource owns the whole list for the catalog.',
                    why='The code is the whole list, so the lasting fix is a second grant block for analysts in it. Then the next apply keeps their access.',
                    wrong=[None, 'Every apply would take it away again, and nobody could review it.', 'A singular and a plural grant on the same catalog fight on every apply, and the plan never settles.']),
            ],
        ),
        starter="""def grants_to_revoke(code, live):
    # your code here
    pass
""",
        solution="""def grants_to_revoke(code, live):
    revoke = {}
    for principal, privileges in live.items():
        keep = code.get(principal, [])
        gone = []
        for privilege in privileges:
            if privilege not in keep:
                gone.append(privilege)
        if gone:
            revoke[principal] = gone
    return revoke
""",
        cases=[
            case({'engineers': ['USE_CATALOG', 'SELECT']}, {
                'engineers': ['USE_CATALOG', 'SELECT', 'MODIFY'],
                'analysts': ['SELECT'],
            }, expected={'engineers': ['MODIFY'], 'analysts': ['SELECT']}, sample=True),
            case({'analysts': ['USE_CATALOG']}, {'analysts': ['USE_CATALOG']}, expected={}),
            case({'analysts': ['USE_CATALOG', 'SELECT']}, {'analysts': ['USE_CATALOG', 'SELECT', 'MODIFY']}, expected={'analysts': ['MODIFY']}),
            case({'data-engineers': ['ALL_PRIVILEGES']}, {}, expected={}),
            case({}, {'6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10': ['USE_CATALOG', 'BROWSE']}, expected={'6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10': ['USE_CATALOG', 'BROWSE']}),
            case({'data-engineers': ['USE_CATALOG', 'USE_SCHEMA', 'SELECT', 'MODIFY']}, {
                'data-engineers': ['USE_CATALOG', 'USE_SCHEMA', 'SELECT', 'MODIFY'],
                'analysts': ['USE_CATALOG', 'SELECT'],
            }, expected={'analysts': ['USE_CATALOG', 'SELECT']}),
        ],
        guided="""def grants_to_revoke(code, live):
    # Replace every ___ with real code, then run the tests.

    revoke = {}
    for principal, privileges in live.items():
        # Step 1: what the code lets this principal keep.
        # Not in code at all? Then it keeps an empty list.
        keep = code.get(principal, ___)

        # Step 2: every live privilege that is not in keep.
        gone = []
        for privilege in privileges:
            if ___:
                gone.append(privilege)

        if gone:
            revoke[principal] = gone

    return revoke
""",
        fills=['[]', 'privilege not in keep'],
        concepts=[
            [
                'Looping over a dict',
                '`.items()` gives you each key and its value together.',
                """for name, age in {'ana': 30}.items():
    print(name, age)   # ana 30""",
            ],
            [
                'dict.get with a default',
                '`a_dict.get(key, default)` gives the default when the key is missing, instead of an error.',
                """ages = {'ana': 30}
ages.get('bo', 0)   # 0""",
            ],
            [
                'not in on a list',
                '`x not in a_list` is True when x is nowhere in the list.',
                "'tea' not in ['coffee', 'milk']   # True",
            ],
            [
                'An empty list counts as False',
                '`if a_list:` runs its block only when the list has at least one item.',
                """basket = []
if basket: print('not empty')   # prints nothing""",
            ],
        ],
        byhand='engineers is in code with USE_CATALOG and SELECT. Live, it also has MODIFY, which the code doesn\'t list, so it loses MODIFY. analysts isn\'t in code at all, so it keeps nothing and loses SELECT. Return {"engineers": ["MODIFY"], "analysts": ["SELECT"]}.',
        why='One pass over the live grants, checking each privilege against the code.',
        gotchas=[
            [
                'Never mix plural and singular on the same object',
                'A `databricks_grants` and a `databricks_grant` on the same object (a catalog, schema or table) fight each other on every apply, and the plan never settles.',
            ],
            [
                'Grant to groups, not people',
                'Grants to individual users break when people leave. Grant to account-level groups (synced from Entra ID, Azure\'s sign-in and user directory) and manage membership there.',
            ],
        ],
    ),
)

lesson(MODULE, 'overlapping_subnets',
    title='Networking for Databricks',
    checked='2026-10-13',
    sources=[source('Deploy Azure Databricks in your Azure virtual network (VNet injection)', 'https://learn.microsoft.com/azure/databricks/security/network/classic/vnet-inject')],
    learn=[
        "**VNet injection** puts a Databricks workspace's clusters in your own virtual network, using a **host** and a **container** subnet (each a slice of the network's addresses). They must not overlap each other or anything they connect to.",
        "A subnet's addresses are written as a **CIDR** block, like `10.20.0.0/24`. The number after the slash sets the size: a smaller number means a bigger block.",
        "Each node (one machine in a cluster) uses an address in each subnet, and Azure reserves 5 per subnet, so size them for the clusters you'll need.",
    ],
    example=example('CIDR as a range', """10.20.0.0/24 -> 256 addresses: 10.20.0.0 to 10.20.0.255
10.20.0.0/22 -> 1024 addresses: 10.20.0.0 to 10.20.3.255"""),
    check=question(
        'Do 10.20.0.0/22 and 10.20.2.0/24 overlap?',
        ['No', 'Yes: the /24 is inside the /22', "Only if they're in different VNets"],
        answer=1,
        why='The /22 runs to 10.20.3.255, which covers all of 10.20.2.x.',
    ),
    angle=angle(
        pattern='Turn blocks into ranges, compare pairs',
        text='The big idea: the host and container subnets must not overlap each other or anything they connect to. Your code uses `to_range` to turn each CIDR into its first and last address as plain numbers. Then a loop inside a loop compares every subnet with each one after it. A loop is code that repeats for each item. Two ranges overlap when each starts at or before the other ends, like two bookings that share a time. Checking every pair is fine for a handful of subnets.',
        say='"I turn each CIDR into a [[first and last|middle|single::The two ends of the range, as plain numbers.]] address, then compare every [[pair|row|third::Each subnet against each one after it.]]. Two ranges overlap when each [[starts|ends|grows::Like two bookings that share a time.]] at or before the other ends."',
        classic='merge_intervals',
    ),
    exercise=exercise(
        title='Check VNet Injection Subnets',
        topic='networking',
        difficulty='medium',
        fn='overlapping_subnets',
        prompt="""`subnets` is a list of `[name, cidr]` pairs, one per subnet (a slice of the network's addresses), like `["snet-host", "10.20.0.0/24"]`. A CIDR is a block of network addresses: `10.20.0.0/24` runs from 10.20.0.0 to 10.20.0.255.

Call the ready-made helper `to_range(cidr)` to get `[first, last]`: the block's first and last address, as plain numbers.

Two subnets overlap when each one's first address is at or below the other one's last address. Compare every subnet with each one after it in the list. Return every overlapping pair as `[earlier_name, later_name]`, in the order you find them.""",
        pattern="Turn each CIDR into a [first, last] range. Two ranges overlap when each one's first is at or below the other one's last.",
        target='check each pair once (a VNet has only a handful of subnets)',
        realworld="Azure rejects overlapping subnets, but often only at apply time, deep into a Spacelift run. The same check matters for VNet peering (connecting two virtual networks) to a hub network, where overlap isn't caught until traffic fails.",
        starter="""def overlapping_subnets(subnets):
    # your code here
    pass


def to_range(cidr):
    # Ready-made helper: call to_range(cidr) in your
    # code. You don't need to read it or change it.
    address, size = cidr.split("/")
    a, b, c, d = [int(part) for part in address.split(".")]
    first = a * 256 ** 3 + b * 256 ** 2 + c * 256 + d
    count = 2 ** (32 - int(size))
    return [first, first + count - 1]
""",
        solution="""def overlapping_subnets(subnets):
    pairs = []
    for i in range(len(subnets)):
        for j in range(i + 1, len(subnets)):
            name1, cidr1 = subnets[i]
            name2, cidr2 = subnets[j]
            first1, last1 = to_range(cidr1)
            first2, last2 = to_range(cidr2)
            if first1 <= last2 and first2 <= last1:
                pairs.append([name1, name2])
    return pairs


def to_range(cidr):
    address, size = cidr.split("/")
    a, b, c, d = [int(part) for part in address.split(".")]
    first = a * 256 ** 3 + b * 256 ** 2 + c * 256 + d
    count = 2 ** (32 - int(size))
    return [first, first + count - 1]
""",
        cases=[
            case([
                ['snet-host', '10.20.0.0/22'],
                ['snet-container', '10.20.2.0/24'],
                ['snet-link', '10.20.8.0/26'],
            ], expected=[['snet-host', 'snet-container']], sample=True),
            case([['snet-dbw-host', '10.20.1.0/24'], ['snet-dbw-container', '10.20.2.0/24']], expected=[]),
            case([], expected=[]),
            case([['a', '10.0.0.0/16'], ['b', '10.0.255.0/24'], ['c', '10.1.0.0/24']], expected=[['a', 'b']]),
            case([['host', '10.30.0.0/26'], ['container', '10.30.0.64/26'], ['pe', '10.30.0.0/27']], expected=[['host', 'pe']]),
            case([['x', '192.168.1.0/24'], ['y', '192.168.1.0/24']], expected=[['x', 'y']]),
            case([['a', '10.0.0.0/16'], ['b', '10.0.1.0/24'], ['c', '10.0.2.0/24']], expected=[['a', 'b'], ['a', 'c']]),
        ],
        guided="""def overlapping_subnets(subnets):
    # Replace every ___ with real code, then run the tests.

    pairs = []
    for i in range(len(subnets)):
        # Step 1: every pair once, so j starts just after i.
        for j in range(___, len(subnets)):
            name1, cidr1 = subnets[i]
            name2, cidr2 = subnets[j]
            first1, last1 = to_range(cidr1)
            first2, last2 = to_range(cidr2)
            # Step 2: overlap when each one's first is at
            # or below the other one's last (use <= twice).
            if ___:
                pairs.append([name1, name2])

    return pairs


def to_range(cidr):
    # Ready-made helper, used above. You don't
    # need to read it or change it.
    address, size = cidr.split("/")
    a, b, c, d = [int(part) for part in address.split(".")]
    first = a * 256 ** 3 + b * 256 ** 2 + c * 256 + d
    count = 2 ** (32 - int(size))
    return [first, first + count - 1]
""",
        fills=['i + 1', 'first1 <= last2 and first2 <= last1'],
        concepts=[
            [
                'Every pair once',
                '`range(start, stop)` counts from start up to just before stop. Start the inner loop at `i + 1`. Then you never compare an item with itself, and never check the same pair twice.',
                """for i in range(3):
    for j in range(i + 1, 3):
        print(i, j)   # 0 1, 0 2, 1 2""",
            ],
            [
                'Two names from a pair',
                'A two-item list can be unpacked into two names at once.',
                """name, age = ['ana', 30]
name   # 'ana'""",
            ],
            [
                'Do two ranges overlap?',
                "Two ranges share a number when each one's start is at or below the other one's end.",
                """# 3 to 7 and 5 to 9 share 5, 6 and 7:
3 <= 9 and 5 <= 7   # True""",
            ],
            [
                'CIDR sizes',
                'The number after the slash sets the size of the block. A smaller number means a bigger block.',
                """# /26 -> 64 addresses
# /24 -> 256 addresses
# /22 -> 1024 addresses""",
            ],
        ],
        byhand="to_range gives these blocks, shown here as addresses so they're easy to read. snet-host is 10.20.0.0 to 10.20.3.255 (a /22 is 1024 addresses). snet-container is 10.20.2.0 to 10.20.2.255. snet-link is 10.20.8.0 to 10.20.8.63. Host and container: host starts at 10.20.0.0, which is at or below container's last, 10.20.2.255. Container starts at 10.20.2.0, which is at or below host's last, 10.20.3.255. Both are true, so they overlap. Host and link: link's first address is above host's last address, so no. Container and link: no, for the same reason. Return [[\"snet-host\", \"snet-container\"]].",
        why='Each pair is compared once, which is quick for the handful of subnets a VNet has.',
        gotchas=[
            [
                'Both subnets need the Databricks delegation',
                'VNet injection requires each subnet to be delegated to `Microsoft.Databricks/workspaces` and associated with a network security group (Azure\'s firewall rules for a subnet). A missing delegation fails at apply, not plan.',
            ],
            [
                "Size for the cluster you'll need",
                'Each cluster node uses one address in each subnet, and Azure reserves 5 addresses per subnet. A /26 leaves room for about 59 nodes, which teams outgrow.',
            ],
        ],
    ),
)

lesson(MODULE, 'allocate_capacity',
    title="Who gets capacity when it's scarce",
    checked='2026-10-13',
    sources=[source('Provisioned throughput billing and cost management', 'https://learn.microsoft.com/azure/foundry/openai/concepts/provisioned-throughput-billing'), source('Manage traffic with spillover for provisioned deployments', 'https://learn.microsoft.com/azure/foundry/openai/how-to/spillover-traffic-management')],
    learn=[
        'When capacity is scarce, whoever sends the biggest burst wins. That might be a weekend experiment, while the help-center assistant that customers rely on gets error 429 ("too many requests"). So decide **who comes first** before it happens, by putting each app in a **tier**: a group with its own rule, served most important first.',
        'Once its traffic is steady, a **critical** app moves to **provisioned throughput**: reserved capacity, counted in PTUs (provisioned throughput units). You pay for it every hour, used or not, so it mostly buys guaranteed capacity, not a lower price: a 1-year reservation only works out cheaper when it is busy nearly all the time. Turn on **spillover**: when the PTU deployment is full, extra requests go to a pay-as-you-go deployment instead of failing.',
        '**Graduated** apps proved themselves in the **sandbox**, the shared experiment space. They get standard pay-as-you-go deployments, sized from the busiest minute they measured. The sandbox gets a deployment of its own.',
        "Critical apps come first and get what they ask for. Each graduated app gets what it asked for, capped at an even share of the rest, so one big app can't crowd out the others. This simple plan does not share out the spare a second time: it all drops to the sandbox, even if a graduated app is still short.",
    ],
    example=example('Sharing 60,000 tokens a minute', """help-center (critical) wants 25,000
  gets 25,000, so 35,000 left
2 graduated apps: up to 17,500 each
  hr-bot wants 5,000: gets 5,000
  doc-search wants 30,000: gets 17,500
  so 12,500 left
the sandbox apps split the 12,500"""),
    check=question(
        'Two graduated apps share 60,000 tokens a minute. One wants 10,000 and the other wants 50,000. Each gets its even share or what it wants, whichever is less. In this plan, where do the spare 20,000 go?',
        [
            'Down to the sandbox tier',
            'To the app that wanted 50,000',
            'Nowhere, they stay unused',
        ],
        answer=0,
        why="The even share of 30,000 is a cap, and this plan does not share the spare a second time. So the 20,000 the smaller app didn't need drop to the next tier, the sandbox.",
    ),
    angle=angle(
        pattern='Serve tiers in order of importance',
        text='The big idea: decide who comes first before capacity runs out, by serving tiers most important first. Your code first puts the apps into three piles by tier. Critical apps take what they want, or all that is left. What remains is split evenly among graduated apps with `//`, whole-number division, and each takes its share or less. Then every sandbox app gets an equal share of whatever is still left, even if it wanted less. Spare is never offered to graduated apps a second time.',
        say='"I serve the most important tier first. [[Critical|Sandbox|Graduated::The apps that must never go short.]] apps take what they need, graduated apps split the rest [[evenly|by size|randomly::So no big app crowds out the others.]], and the [[sandbox|top tier|first tier::Where people try things out.]] gets whatever\'s left."',
        classic=None,
    ),
    stack=stack('Terraform: a PTU deployment with spillover (azapi provider)', """# The critical app's reserved capacity,
# added once its traffic is steady.
# Requests it can't take spill over to
# a pay-as-you-go (Global Standard)
# deployment of the same model in the
# same resource.
resource "azapi_resource" "help_center" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "help-center-ptu"
  parent_id = azurerm_cognitive_account.foundry.id
  body = {
    sku = {
      name     = "GlobalProvisionedManaged"
      capacity = 15 # PTUs: Global starts at 15
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = var.model_name
        version = var.model_version
      }
      spilloverDeploymentName = "help-center-paygo"
    }
  }
}"""),
    exercise=exercise(
        title='Share Out Scarce Capacity',
        topic='platform',
        difficulty='medium',
        fn='allocate_capacity',
        prompt="""Your function gets two things:

- `total_tpm`: tokens per minute to hand out, like `100000`.
- `apps`: a list of dicts like `{"name": "hr-bot", "tier": "graduated", "wants": 10000}`. `tier` is `"critical"`, `"graduated"` or `"sandbox"`.

Hand it out in three rounds. Skip a round with no apps.

- Critical apps, in list order: each gets what it wants, or all that is left if less.
- Graduated apps: divide what is left by how many there are, with `//`. Each gets that share, or what it wants if less.
- Sandbox apps: divide what is still left the same way. Each gets the full share, even if it wanted less.

Return a dict of every app's name and its tokens per minute, even when it is 0 (`{}` if no apps).""",
        pattern='Priority, then fair shares: serve the most important tier first, then split what is left evenly, capping graduated apps at what they asked for.',
        target='one pass to group the apps by tier, then one pass over each tier',
        realworld="When Foundry quota is tight, this is the plan a platform team writes down: critical apps on provisioned throughput with spillover once their traffic is steady, graduated apps on standard deployments sized from their busiest minute, and the sandbox on its own deployment with what is left. Agreeing the order ahead of time beats arguing about it during an outage. Real schedulers often give the spare to graduated apps still short before the sandbox.",
        starter="""def allocate_capacity(total_tpm, apps):
    # your code here
    pass
""",
        solution="""def allocate_capacity(total_tpm, apps):
    tiers = {"critical": [], "graduated": [],
             "sandbox": []}
    for app in apps:
        tiers[app["tier"]].append(app)

    given = {}
    left = total_tpm
    for app in tiers["critical"]:
        amount = min(app["wants"], left)
        given[app["name"]] = amount
        left = left - amount

    graduated = tiers["graduated"]
    if graduated:
        share = left // len(graduated)
        for app in graduated:
            amount = min(app["wants"], share)
            given[app["name"]] = amount
            left = left - amount

    sandbox = tiers["sandbox"]
    if sandbox:
        share = left // len(sandbox)
        for app in sandbox:
            given[app["name"]] = share
    return given
""",
        cases=[
            case(100000, [
                {'name': 'help-center', 'tier': 'critical', 'wants': 40000},
                {'name': 'hr-bot', 'tier': 'graduated', 'wants': 10000},
                {'name': 'doc-search', 'tier': 'graduated', 'wants': 40000},
                {'name': 'chat-poc', 'tier': 'sandbox', 'wants': 30000},
                {'name': 'summary-poc', 'tier': 'sandbox', 'wants': 30000},
            ], expected={
                'help-center': 40000,
                'hr-bot': 10000,
                'doc-search': 30000,
                'chat-poc': 10000,
                'summary-poc': 10000,
            }, sample=True),
            case(50000, [
                {'name': 'hr-bot', 'tier': 'graduated', 'wants': 10000},
                {'name': 'help-center', 'tier': 'critical', 'wants': 30000},
                {'name': 'order-status', 'tier': 'critical', 'wants': 30000},
                {'name': 'chat-poc', 'tier': 'sandbox', 'wants': 5000},
            ], expected={'hr-bot': 0, 'help-center': 30000, 'order-status': 20000, 'chat-poc': 0}),
            case(60000, [
                {'name': 'help-center', 'tier': 'critical', 'wants': 20000},
                {'name': 'poc-a', 'tier': 'sandbox', 'wants': 5000},
                {'name': 'poc-b', 'tier': 'sandbox', 'wants': 5000},
                {'name': 'poc-c', 'tier': 'sandbox', 'wants': 5000},
            ], expected={'help-center': 20000, 'poc-a': 13333, 'poc-b': 13333, 'poc-c': 13333}),
            case(100000, [
                {'name': 'hr-bot', 'tier': 'graduated', 'wants': 50000},
                {'name': 'doc-search', 'tier': 'graduated', 'wants': 50000},
                {'name': 'claims-helper', 'tier': 'graduated', 'wants': 50000},
            ], expected={'hr-bot': 33333, 'doc-search': 33333, 'claims-helper': 33333}),
            case(100000, [], expected={}),
            case(80000, [
                {'name': 'help-center', 'tier': 'critical', 'wants': 10000},
                {'name': 'hr-bot', 'tier': 'graduated', 'wants': 5000},
                {'name': 'doc-search', 'tier': 'graduated', 'wants': 5000},
                {'name': 'poc-a', 'tier': 'sandbox', 'wants': 1000},
            ], expected={'help-center': 10000, 'hr-bot': 5000, 'doc-search': 5000, 'poc-a': 60000}),
        ],
        guided="""def allocate_capacity(total_tpm, apps):
    # Replace every ___ with real code, then run the tests.

    # Group the apps into their three tiers.
    tiers = {"critical": [], "graduated": [],
             "sandbox": []}
    for app in apps:
        tiers[app["tier"]].append(app)

    given = {}
    left = total_tpm

    # Round 1: critical apps, in list order.
    for app in tiers["critical"]:
        # Step 1: what it wants, or all that is left if less.
        amount = ___
        given[app["name"]] = amount
        left = left - amount

    # Round 2: graduated apps split what is left evenly.
    graduated = tiers["graduated"]
    if graduated:
        # Step 2: what is left, divided by how many, with //.
        share = ___
        for app in graduated:
            # Step 3: its share, or what it wants if smaller.
            amount = ___
            given[app["name"]] = amount
            left = left - amount

    # Round 3: sandbox apps split the rest, with no cap.
    sandbox = tiers["sandbox"]
    if sandbox:
        share = left // len(sandbox)
        for app in sandbox:
            given[app["name"]] = share

    return given
""",
        fills=['min(app["wants"], left)', 'left // len(graduated)', 'min(app["wants"], share)'],
        concepts=[
            [
                'A dict of lists',
                'Start each key with an empty list, then append each item to the list for its key.',
                """by_colour = {'red': [], 'green': []}
by_colour['red'].append('apple')
# {'red': ['apple'], 'green': []}""",
            ],
            [
                'min',
                '`min(a, b)` gives the smaller of two numbers.',
                'min(5, 3)   # 3',
            ],
            [
                'Splitting evenly',
                '`len(a_list)` counts its items. `//` divides and drops anything after the point, so the answer is a whole number.',
                """len(['ana', 'bo'])   # 2
7 // 2               # 3
10000 // 3           # 3333""",
            ],
            [
                'An empty list counts as False',
                '`if a_list:` runs its block only when the list has at least one item. Here it also stops you dividing by 0.',
                """guests = []
if guests: print('party')   # prints nothing""",
            ],
            [
                'Adding to a dict',
                '`a_dict[key] = value` stores a value under a key.',
                """ages = {}
ages['ana'] = 30   # {'ana': 30}""",
            ],
        ],
        byhand='There are 100000 tokens a minute to hand out. Round 1: help-center is critical and wants 40000, so it gets 40000, and 60000 are left. Round 2: two graduated apps, so each can have up to half of 60000, which is 30000. hr-bot wants 10000, which is smaller, so it gets 10000. doc-search wants 40000, so it gets its share of 30000. hr-bot and doc-search took 10000 plus 30000, so 20000 are left. doc-search is still short, but the spare is not shared a second time. Round 3: two sandbox apps split 20000, so 10000 each. Return {"help-center": 40000, "hr-bot": 10000, "doc-search": 30000, "chat-poc": 10000, "summary-poc": 10000}.',
        why='One pass to group the apps into tiers, then one pass over each tier.',
        gotchas=[
            [
                'Reserving for the peak',
                'PTUs cost the same every hour, busy or idle. Reserve the steady baseline for critical apps and let spillover carry the peaks to pay-as-you-go.',
            ],
            [
                'Spillover needs a pay-as-you-go deployment first',
                'Spillover only goes to a pay-as-you-go deployment of the same model and version, in the same Foundry resource, so create that one first. Models from other providers, such as DeepSeek or Llama, cannot spill over.',
            ],
        ],
    ),
)

# A sandbox config from the lesson's tests, shown above the first practice questions.
_SPACE = """{
  "space_tpm": 80000,
  "user_tpm": None,
  "group_tpm": {},
  "sandbox_deployment": "shared-gpt",
  "production_deployments": ["help-center-gpt", "shared-gpt"]
}"""

lesson(MODULE, 'check_limits',
    title='A shared space with fair limits',
    checked='2026-10-13',
    sources=[source('Apply rate limits to model and MCP services', 'https://learn.microsoft.com/azure/databricks/ai-gateway/rate-limits')],
    learn=[
        'In a shared experiment space (the **sandbox**), one looping agent or eval run can use the whole limit, and everyone else gets error 429 ("too many requests"). A **per-user rate limit** stops that: each person gets a slice, well below the whole.',
        'The Databricks AI gateway (now called Unity Gateway) sets limits on a **service** (the whole space), a default for each **user**, and custom ones for a **group**. A group limit is one pool for all its members, used instead of their per-user limit. The service limit always wins, so a group limit at or above it protects nothing.',
        "Give the sandbox its own Foundry deployment. If it shares a production deployment, experiments eat the capacity live apps need. An app that proves itself **graduates** out of the space onto capacity of its own.",
    ],
    example=example('A fair space, and two mistakes', """space:   100,000 tokens a minute
user:     20,000 each, a slice
team-a:   50,000 shared, replaces
          the 20,000 for members
sandbox: "sandbox-gpt", its own

Mistakes:
user:    100,000, the whole space
team-b:  120,000, more than the space"""),
    check=question(
        'The space limit is 100,000 tokens a minute, and the per-user limit is also 100,000. What goes wrong?',
        [
            'Nothing, because users can never go past the space limit anyway',
            'Every request fails, because the two limits are the same number',
            'One busy user can use the whole space, so everyone else gets 429s',
        ],
        answer=2,
        why='A per-user limit only helps when it is a slice of the whole. Set it well below the space limit, so one script can never block everyone.',
    ),
    angle=angle(
        pattern='Three rules, three fixed messages',
        text="The big idea: in a shared space, user and group limits must sit below the whole space's limit, and the sandbox needs its own deployment. Your code checks three rules in order. The user limit fails if it is `None` or at least the space limit. For groups, it looks at every group's limit and raises one flag if any is too high, so that message is added only once. Last, it checks whether the sandbox deployment is in the production list.",
        say='"In a shared space, user and group limits must sit [[below|above|equal to::They can\'t reach the limit of the whole space.]] the space\'s limit. I check each rule [[separately|in one go|only once::Don\'t stop at the first one that breaks.]] and report [[every failure|the first failure|one failure::A reviewer can fix them all in one pass.]], not just the first."',
        classic=None,
    ),
    stack=stack('Unity Gateway (AI gateway): limits for the space, each user and a group', """# Rate limits on the sandbox's model
# service, in tokens a minute. Terraform
# keeps them in the config of a
# databricks_ai_gateway_model_service.
databricks ai-gateway update-model-service \\
  model-services/main.sandbox.chat \\
  config.rate_limits --json '{
  "config": {"rate_limits": [
    {"key": "RATE_LIMIT_KEY_SERVICE",
     "tokens": 100000,
     "renewal_period":
       "RATE_LIMIT_RENEWAL_PERIOD_MINUTE"},
    {"key": "RATE_LIMIT_KEY_USER_DEFAULT",
     "tokens": 20000,
     "renewal_period":
       "RATE_LIMIT_RENEWAL_PERIOD_MINUTE"},
    {"key": "RATE_LIMIT_KEY_USER_GROUP",
     "principal": "team-a",
     "tokens": 50000,
     "renewal_period":
       "RATE_LIMIT_RENEWAL_PERIOD_MINUTE"}
  ]}
}'"""),
    exercise=exercise(
        title='Check the Shared Space Limits',
        topic='platform',
        difficulty='easy',
        fn='check_limits',
        prompt="""`config` is a dict for the sandbox, a shared experiment space. Limits are tokens per minute.

- `space_tpm`: the whole space's limit, like `100000`.
- `user_tpm`: each user's limit, like `20000`, or `None`.
- `group_tpm`: each group's name and shared limit, like `{"team-a": 50000}`, or `{}`.
- `sandbox_deployment`: the sandbox's deployment, like `"sandbox-gpt"`.
- `production_deployments`: deployments live apps use, like `["prod-gpt"]`.

Each rule below that fails adds its message once:

- `user_tpm` is `None`, or equal to or above `space_tpm` (that is no slice): `"user limit missing or too high"`
- any group's limit is equal to or above `space_tpm`: `"group limit too high"`
- `sandbox_deployment` is in `production_deployments`: `"sandbox shares a production deployment"`

Return the messages in the order above, or `[]` if all pass.""",
        pattern='Check each rule on its own, in order, and add a fixed message for each one that fails.',
        target='one look at each setting',
        realworld="This is the review a platform team runs before opening a shared space: a service limit for the whole space, a default per-user limit well below it, a few group limits, each below it too (the gateway allows at most 5 per service), and a sandbox deployment that no production app uses.",
        practice=practice(
            intro='Review a shared space\'s limits the way a platform team does before opening it: check each rule, and report every one that fails.',
            explain='In a shared space, user and group limits must sit below the whole space\'s limit, and the sandbox needs a deployment of its own. You checked each rule on its own and reported every one that failed, and saw that a group\'s limit is one pool its members share, not a limit for each person.',
            asks=[
                ask('What is wrong with the user limit?', ['It\'s missing, so one person can use it all', 'It\'s too low for a busy team to work', 'Nothing: `None` means no limit is needed'], answer=0,
                    evidence=evidence('code', title='The sandbox settings (tokens a minute)', text=_SPACE),
                    clue='Look at `user_tpm`.',
                    why='`None` means there is no per-user limit, so one looping script can use all 80,000 and everyone else gets 429s.',
                    wrong=[None, 'There is no number to be too low.', '`None` is the problem: there is no slice at all.']),
                ask('Which other rule fails for the same settings?', ['The sandbox uses a production deployment', 'There are no group limits for the teams', 'The space limit is too low for a sandbox'], answer=0,
                    evidence=evidence('code', title='The same settings', text=_SPACE),
                    clue='Compare `sandbox_deployment` with the production list.',
                    why='`shared-gpt` is in the production list, so experiments eat the capacity the help-center app needs. Give the sandbox its own deployment.',
                    wrong=[None, 'Group limits are optional. None at all passes.', 'The space limit is a choice, not a rule this check makes.']),
                ask('team-a\'s limit is the same as the space limit. Is that all right?', ['Yes: it isn\'t above the space limit', 'No: team-a could use the whole space'], answer=1,
                    evidence=evidence('code', title='Another space', text="""{
  "space_tpm": 50000,
  "user_tpm": 10000,
  "group_tpm": {"team-a": 50000},
  "sandbox_deployment": "sandbox-gpt",
  "production_deployments": ["prod-gpt"]
}"""),
                    clue='The service limit always wins. What is left for everyone else?',
                    why='A group limit at the space limit lets team-a take all of it. It has to sit below the space limit to leave room for anyone else.',
                    wrong=['Equal is not a slice: team-a could still use everything.', None]),
                ask('team-a has ten busy people. About how much can each one use?', ['20,000 each: the per-user limit still applies', 'About 5,000 each: they share one pool of 50,000', '50,000 each: the group limit is per person'], answer=1,
                    evidence=evidence('code', title='A space that passes', text="""{
  "space_tpm": 100000,
  "user_tpm": 20000,
  "group_tpm": {"team-a": 50000},
  "sandbox_deployment": "sandbox-gpt",
  "production_deployments": ["prod-gpt"]
}"""),
                    clue='A group limit is one pool for all its members, used instead of their per-user limit.',
                    why='team-a\'s 50,000 is shared, and it replaces the 20,000 each for its members. Ten busy people get about 5,000 each.',
                    wrong=['For team-a members, the group limit replaces the per-user one.', None, 'The group limit is one pool for everyone in it, not each.']),
            ],
        ),
        starter="""def check_limits(config):
    # your code here
    pass
""",
        solution="""def check_limits(config):
    problems = []
    space = config["space_tpm"]
    user = config["user_tpm"]
    if user is None or user >= space:
        problems.append("user limit missing or too high")

    group_too_high = False
    for limit in config["group_tpm"].values():
        if limit >= space:
            group_too_high = True
    if group_too_high:
        problems.append("group limit too high")

    sandbox = config["sandbox_deployment"]
    production = config["production_deployments"]
    if sandbox in production:
        problems.append("sandbox shares a production deployment")
    return problems
""",
        cases=[
            case({
                'space_tpm': 100000,
                'user_tpm': 100000,
                'group_tpm': {'team-a': 50000, 'team-b': 120000},
                'sandbox_deployment': 'sandbox-gpt',
                'production_deployments': ['prod-gpt'],
            }, expected=['user limit missing or too high', 'group limit too high'], sample=True),
            case({
                'space_tpm': 100000,
                'user_tpm': 20000,
                'group_tpm': {'team-a': 50000},
                'sandbox_deployment': 'sandbox-gpt',
                'production_deployments': ['prod-gpt'],
            }, expected=[]),
            case({
                'space_tpm': 80000,
                'user_tpm': None,
                'group_tpm': {},
                'sandbox_deployment': 'shared-gpt',
                'production_deployments': ['help-center-gpt', 'shared-gpt'],
            }, expected=['user limit missing or too high', 'sandbox shares a production deployment']),
            case({
                'space_tpm': 100000,
                'user_tpm': 10000,
                'group_tpm': {'team-a': 150000, 'team-b': 200000},
                'sandbox_deployment': 'sandbox-gpt',
                'production_deployments': [],
            }, expected=['group limit too high']),
            case({
                'space_tpm': 50000,
                'user_tpm': 10000,
                'group_tpm': {'team-a': 50000},
                'sandbox_deployment': 'sandbox-gpt',
                'production_deployments': ['prod-gpt'],
            }, expected=['group limit too high']),
            case({
                'space_tpm': 100000,
                'user_tpm': 200000,
                'group_tpm': {'team-a': 30000, 'team-b': 100001},
                'sandbox_deployment': 'prod-gpt',
                'production_deployments': ['prod-gpt'],
            }, expected=['user limit missing or too high', 'group limit too high', 'sandbox shares a production deployment']),
        ],
        guided="""def check_limits(config):
    # Replace every ___ with real code, then run the tests.

    problems = []
    space = config["space_tpm"]
    user = config["user_tpm"]

    # Step 1: no user limit, or one at or above the space.
    if user is None or ___:
        problems.append("user limit missing or too high")

    # Step 2: is any group's limit at or above the space?
    group_too_high = False
    for limit in config["group_tpm"].values():
        if ___:
            group_too_high = True
    if group_too_high:
        problems.append("group limit too high")

    # Step 3: the sandbox is one of the production ones.
    sandbox = config["sandbox_deployment"]
    production = config["production_deployments"]
    if ___:
        problems.append("sandbox shares a production deployment")

    return problems
""",
        fills=['user >= space', 'limit >= space', 'sandbox in production'],
        concepts=[
            [
                'None and is None',
                "`None` is Python's value for \"nothing\". Test for it with `is None`.",
                """phone = None
phone is None   # True""",
            ],
            [
                'Comparing numbers',
                '`a > b` is True when a is above b. `a >= b` is True when a is equal to or above b.',
                """3 > 3    # False
3 >= 3   # True""",
            ],
            [
                'or stops early',
                '`a or b` is True when either side is True. If `a` is already True, Python never looks at `b`, so `user >= space` never runs on `None`.',
                """age = None
age is None or age > 18   # True""",
            ],
            [
                'Looping over dict values',
                '`.values()` gives just the values of a dict, without the keys.',
                """for price in {'tea': 2, 'cake': 4}.values():
    print(price)   # 2, then 4""",
            ],
            [
                'A flag variable',
                "A True/False variable that remembers whether you've seen something. Set it once, check it after the loop.",
                """found_cake = False
for item in ['tea', 'cake']:
    if item == 'cake': found_cake = True""",
            ],
            [
                'in on a list',
                '`x in a_list` is True when x is anywhere in the list.',
                "'tea' in ['coffee', 'tea']   # True",
            ],
        ],
        byhand='The space limit is 100000. The user limit is also 100000, equal to the space, so add "user limit missing or too high". team-a\'s 50000 is below 100000, but team-b\'s 120000 is above it, so add "group limit too high". "sandbox-gpt" is not in ["prod-gpt"], so that rule passes. Return ["user limit missing or too high", "group limit too high"].',
        why='Each setting is looked at once, and each group limit once.',
        gotchas=[
            [
                'A group limit is shared',
                "A group's limit is one pool for all its members, not a limit for each person. It also replaces the per-user default for its members, so one person in team-a could use all 50,000. Ten busy people in that group get about 5,000 each.",
            ],
            [
                'Bursts slip through, then pause',
                'The gateway counts usage after each answer, so requests arriving together can all get through. Later ones get 429 until usage drops back. Retry with exponential backoff: a wait that grows each time.',
            ],
        ],
    ),
)

planned(MODULE, 'workspace_as_code', 'A workspace in Terraform', 'The azurerm and databricks providers working together to stand up a workspace.')
planned(MODULE, 'cluster_policies', 'Cluster policies as code', 'Limits on size, cost and runtime, so nobody starts a cluster that breaks the budget.')
planned(MODULE, 'metastore_as_code', 'The metastore and catalogs as code', 'Unity Catalog metastore, catalogs and schemas declared once, the same in every environment.')
planned(MODULE, 'sp_permissions', 'Service principals and their permissions', 'Giving a pipeline exactly the access it needs, in code.')
