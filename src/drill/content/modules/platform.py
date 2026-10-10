"""ML platform on Azure Databricks: The Terraform and Spacelift work behind the platform."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('platform', 'ML platform on Azure Databricks', 'The Terraform and Spacelift work behind the platform.')

lesson(MODULE, 'summarize_plan',
    title='What a Terraform plan really says',
    learn=[
        '`terraform plan` compares your code with **state** (what Terraform last applied) and reality, then lists what it will create, update, replace or destroy.',
        '`terraform show -json` gives the same plan as data. Spacelift policies and PR checks read this JSON, not the text.',
    ],
    example=example('From plan to JSON', """terraform plan -out tfplan
terraform show -json tfplan > plan.json"""),
    check=question(
        'The plan says "1 to add, 0 to change, 1 to destroy" for one resource. What is happening to it?',
        ['Nothing', "It's being replaced: destroyed and created again", "It's being renamed"],
        answer=1,
        why='A replacement counts once as an add and once as a destroy.',
    ),
    angle=angle(
        pattern='Counting in one pass',
        text='Three counters and one walk through `resource_changes`.',
        say='"I walk the resource changes once and count by action, treating a replacement as both an add and a destroy, the way Terraform does."',
        classic=None,
    ),
    exercise=exercise(
        title='Read the Plan Summary',
        topic='plan-reading',
        difficulty='easy',
        fn='summarize_plan',
        prompt="""`plan` is what `terraform show -json tfplan` prints, loaded into Python as a dict. Its `resource_changes` list has one entry per resource, and each entry's `change.actions` says what will happen: `["create"]`, `["update"]`, `["delete"]`, `["no-op"]`, `["read"]`, or a replacement: `["delete", "create"]`, or `["create", "delete"]` when `create_before_destroy` is set.

Return `[add, change, destroy]`, counted the way Terraform's own line `Plan: 3 to add, 1 to change, 1 to destroy.` counts them: a replacement is one add and one destroy, and `no-op` and `read` count as nothing. A plan with no changes may leave out `resource_changes` entirely.""",
        pattern="Walk the list once and keep three counters. Check what's in the actions list, not the whole list, so replacements land in both counters.",
        target='one pass over resource_changes',
        realworld='This is the line in every Spacelift run and `terraform plan` output. Writing it yourself means you understand what the JSON plan contains, which is what Spacelift policies and PR checks read.',
        starter="""def summarize_plan(plan):
    # your code here
    pass
""",
        solution="""def summarize_plan(plan):
    add = change = destroy = 0
    for rc in plan.get("resource_changes", []):
        actions = rc["change"]["actions"]
        if "create" in actions:
            add += 1
        if "delete" in actions:
            destroy += 1
        if actions == ["update"]:
            change += 1
    return [add, change, destroy]
""",
        cases=[
            case({
                'format_version': '1.2',
                'resource_changes': [
                    {
                        'address': 'azurerm_resource_group.this',
                        'type': 'azurerm_resource_group',
                        'change': {'actions': ['no-op'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'azurerm_databricks_workspace.this',
                        'type': 'azurerm_databricks_workspace',
                        'change': {'actions': ['update'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'azurerm_storage_container.lake["bronze"]',
                        'type': 'azurerm_storage_container',
                        'change': {'actions': ['create'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'azurerm_databricks_access_connector.uc',
                        'type': 'azurerm_databricks_access_connector',
                        'change': {'actions': ['create'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'databricks_metastore_assignment.this',
                        'type': 'databricks_metastore_assignment',
                        'change': {'actions': ['delete', 'create'], 'before': None, 'after': None},
                    },
                ],
            }, expected=[3, 1, 1], sample=True),
            case({'format_version': '1.2', 'resource_changes': []}, expected=[0, 0, 0]),
            case({'format_version': '1.2'}, expected=[0, 0, 0]),
            case({
                'resource_changes': [
                    {
                        'address': 'data.azurerm_client_config.current',
                        'type': 'azurerm_client_config',
                        'change': {'actions': ['read'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'databricks_catalog.sales',
                        'type': 'databricks_catalog',
                        'change': {'actions': ['create', 'delete'], 'before': None, 'after': None},
                    },
                ],
            }, expected=[1, 0, 1]),
            case({
                'resource_changes': [
                    {
                        'address': 'databricks_schema.raw',
                        'type': 'databricks_schema',
                        'change': {'actions': ['delete'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'databricks_schema.curated',
                        'type': 'databricks_schema',
                        'change': {'actions': ['delete'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'databricks_grants.sales',
                        'type': 'databricks_grants',
                        'change': {'actions': ['update'], 'before': None, 'after': None},
                    },
                ],
            }, expected=[0, 1, 2]),
        ],
        guided="""def summarize_plan(plan):
    # Replace every ___ with real code, then run the tests.

    add = change = destroy = 0

    # Step 1: a plan with no changes may not have the key at all.
    #         .get(key, default) gives you the default instead of a KeyError.
    for rc in plan.get("resource_changes", ___):
        actions = rc["change"]["actions"]

        # Step 2: a replacement contains BOTH words, so check each one
        #         separately rather than with if/elif.
        if "create" in actions:
            add += 1
        if ___:
            destroy += 1

        # Step 3: an in-place change is exactly ["update"].
        if ___:
            change += 1

    return [add, change, destroy]
""",
        concepts=[
            [
                'Getting the plan as JSON',
                "Terraform's plan file is binary. `terraform show -json` turns it into JSON, which Python loads as dicts and lists.",
                """terraform plan -out tfplan
terraform show -json tfplan > plan.json""",
            ],
            [
                'dict.get with a default',
                '`d.get(key, default)` returns the default instead of raising KeyError when the key is missing.',
                """plan = {}
plan.get('resource_changes', [])   # []""",
            ],
            [
                'in on a list',
                "`'create' in actions` checks whether the word is anywhere in the list.",
                "'create' in ['delete', 'create']   # True",
            ],
        ],
        byhand='Go down the list. The resource group is no-op: nothing. The workspace is update: change 1. The bronze container and the access connector are create: add 2. The metastore assignment is delete then create: add 3 and destroy 1. Result: [3, 1, 1].',
        why='One pass over the resource changes, with a few checks on a two-item list each time.',
        gotchas=[
            [
                '"0 to change" can still hide a replacement',
                'The summary only counts. `1 to add, 1 to destroy` might be a harmless swap of a grant or a recreated workspace. Always read which resources the numbers are.',
            ],
            [
                'Plans go stale',
                'A plan is computed against the state at that moment. If something else applies first, Spacelift or Terraform will refuse the old plan. Re-plan rather than forcing it.',
            ],
        ],
    ),
)

lesson(MODULE, 'find_replacements',
    title='Spotting dangerous replacements',
    learn=[
        "Some attributes can't change in place. Changing them **forces replacement**: Terraform destroys the resource and creates a new one.",
        'On an Azure Databricks workspace, that means a new URL and losing everything inside it. Always find every `-/+` in a plan before approving.',
    ],
    example=example('In the text plan', """-/+ resource "azurerm_databricks_workspace" "this" {
  ~ managed_resource_group_name = "a" -> "b" # forces replacement"""),
    check=question(
        'Which change to `azurerm_databricks_workspace` forces a replacement?',
        ['Adding a tag', 'Changing `managed_resource_group_name`', 'Nothing can'],
        answer=1,
        why="Tags update in place; the managed resource group name can't change, so the workspace is recreated.",
    ),
    angle=angle(
        pattern='Filter',
        text='Keep the entries that match a rule, in order, in one walk.',
        say='"I keep the resource changes whose actions contain both delete and create, which is how a replacement shows up in plan JSON."',
        classic=None,
    ),
    exercise=exercise(
        title='Spot the Replacements',
        topic='plan-reading',
        difficulty='easy',
        fn='find_replacements',
        prompt="""A replacement destroys a resource and creates a new one. On an `azurerm_databricks_workspace` that means a new workspace URL and ID, and every cluster, job, notebook and secret scope in it is gone.

Given a `plan` (the `terraform show -json` dict), return the `address` of every resource that will be replaced, in plan order. A replacement is any entry whose `change.actions` contains both `"delete"` and `"create"`, in either order.""",
        pattern='Filter: keep the entries that match a rule, in their original order.',
        target='one pass over resource_changes',
        realworld='Approving a plan without spotting a `-/+` is how workspaces get recreated by accident. Changing `managed_resource_group_name`, `location`, or the VNet settings in `custom_parameters` all force a new workspace.',
        starter="""def find_replacements(plan):
    # your code here
    pass
""",
        solution="""def find_replacements(plan):
    out = []
    for rc in plan.get("resource_changes", []):
        actions = rc["change"]["actions"]
        if "delete" in actions and "create" in actions:
            out.append(rc["address"])
    return out
""",
        cases=[
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_databricks_workspace.this',
                        'type': 'azurerm_databricks_workspace',
                        'change': {'actions': ['delete', 'create'], 'before': None, 'after': None},
                        'action_reason': 'replace_because_cannot_update',
                    },
                    {
                        'address': 'databricks_cluster.shared',
                        'type': 'databricks_cluster',
                        'change': {'actions': ['update'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'azurerm_subnet.host',
                        'type': 'azurerm_subnet',
                        'change': {'actions': ['no-op'], 'before': None, 'after': None},
                    },
                ],
            }, expected=['azurerm_databricks_workspace.this'], sample=True),
            case({'resource_changes': []}, expected=[]),
            case({
                'resource_changes': [
                    {
                        'address': 'module.uc.databricks_catalog.sales',
                        'type': 'databricks_catalog',
                        'change': {'actions': ['create', 'delete'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'databricks_schema.raw',
                        'type': 'databricks_schema',
                        'change': {'actions': ['delete'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'databricks_schema.curated',
                        'type': 'databricks_schema',
                        'change': {'actions': ['create'], 'before': None, 'after': None},
                    },
                ],
            }, expected=['module.uc.databricks_catalog.sales']),
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_storage_container.lake[0]',
                        'type': 'azurerm_storage_container',
                        'change': {'actions': ['delete', 'create'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'azurerm_storage_container.lake[1]',
                        'type': 'azurerm_storage_container',
                        'change': {'actions': ['delete', 'create'], 'before': None, 'after': None},
                    },
                ],
            }, expected=['azurerm_storage_container.lake[0]', 'azurerm_storage_container.lake[1]']),
            case({}, expected=[]),
        ],
        guided="""def find_replacements(plan):
    # Replace every ___ with real code, then run the tests.

    out = []
    for rc in plan.get("resource_changes", []):
        actions = rc["change"]["actions"]

        # Step 1: a replacement has both "delete" and "create" in actions.
        #         A plain delete or a plain create is not a replacement.
        if ___:
            # Step 2: keep its address.
            ___

    return out
""",
        concepts=[
            [
                'Replacement in the text plan',
                'In `terraform plan` output a replacement is marked `-/+` (or `+/-` with create_before_destroy), and the attribute that caused it says `# forces replacement`.',
                """-/+ resource "azurerm_databricks_workspace" "this" {
      ~ managed_resource_group_name = "rg-dbw-managed" -> "rg-dbw-sales-managed" # forces replacement""",
            ],
            [
                'Two conditions with and',
                '`and` is true only when both sides are true.',
                "'delete' in a and 'create' in a",
            ],
            [
                'Building a result list',
                'Start empty, append matches in the loop, return it at the end.',
                """out = []
out.append('azurerm_databricks_workspace.this')""",
            ],
        ],
        byhand="The workspace's actions are delete and create: that's a replacement, keep its address. The cluster is only update. The subnet is no-op. Answer: just the workspace.",
        why='One pass, two quick membership checks each.',
        gotchas=[
            [
                'What forces a new workspace',
                'On `azurerm_databricks_workspace`, changing `name`, `location`, `managed_resource_group_name`, or most VNet settings in `custom_parameters` (such as `virtual_network_id`) destroys and recreates it. Read the provider docs\' "forces a new resource" notes before touching them.',
            ],
            [
                'prevent_destroy is a backstop',
                '`lifecycle { prevent_destroy = true }` makes Terraform error instead of destroying. It does not help if someone deletes the whole resource block, because the setting goes with it.',
            ],
        ],
    ),
)

lesson(MODULE, 'guard_destroys',
    title='Policies as guardrails',
    learn=[
        "A **plan policy** runs automatically on every Spacelift run and can warn or block based on the plan. It's code review that never gets tired.",
        "Start with the resources you can't rebuild: workspaces, storage accounts, metastores.",
    ],
    example=example('The same rule in Rego', """deny contains msg if {
  rc := input.terraform.resource_changes[_]
  "delete" in rc.change.actions
  rc.type in protected
  msg := sprintf("%s would be destroyed", [rc.address])
}"""),
    check=question(
        'A plan policy blocks destroying storage accounts. Can someone still lose one?',
        [
            "No, it's fully protected",
            'Yes, by deleting it in the portal or with state commands, which never go through a plan',
            'Only if the policy has a bug',
        ],
        answer=1,
        why='Policies only see plans. Pair them with RBAC and resource locks.',
    ),
    angle=angle(
        pattern='Set lookup inside a filter',
        text='Turn the protected types into a set so each check is instant, then one walk through the plan.',
        say='"I put the protected types in a set and check the plan once."',
        classic='two_sum',
    ),
    exercise=exercise(
        title='Write a Plan Policy',
        topic='policy',
        difficulty='easy',
        fn='guard_destroys',
        prompt="""Spacelift can run a plan policy on every run and block it. Write the same rule in Python: given a `plan` and a list of `protected` resource types, return one message for every resource of a protected type that the plan would destroy, including replacements.

Each message is `"<address> would be destroyed"`, in plan order. An empty list means the run may go ahead.""",
        pattern='Filter, then format. Turn the protected list into a set first so each check is instant.',
        target='one pass over resource_changes',
        realworld='The same logic, in Rego, is what a Spacelift plan policy runs against `input.terraform.resource_changes`. Teams use it to stop a merged PR from deleting a workspace, a storage account or a Unity Catalog metastore.',
        starter="""def guard_destroys(plan, protected):
    # your code here
    pass
""",
        solution="""def guard_destroys(plan, protected):
    protected = set(protected)
    out = []
    for rc in plan.get("resource_changes", []):
        if rc["type"] in protected and "delete" in rc["change"]["actions"]:
            out.append(rc["address"] + " would be destroyed")
    return out
""",
        cases=[
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_databricks_workspace.this',
                        'type': 'azurerm_databricks_workspace',
                        'change': {'actions': ['delete', 'create'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'databricks_cluster.shared',
                        'type': 'databricks_cluster',
                        'change': {'actions': ['delete'], 'before': None, 'after': None},
                    },
                ],
            }, ['azurerm_databricks_workspace', 'azurerm_storage_account'], expected=['azurerm_databricks_workspace.this would be destroyed'], sample=True),
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_storage_account.lake',
                        'type': 'azurerm_storage_account',
                        'change': {'actions': ['update'], 'before': None, 'after': None},
                    },
                ],
            }, ['azurerm_storage_account'], expected=[]),
            case({
                'resource_changes': [
                    {
                        'address': 'databricks_metastore.this',
                        'type': 'databricks_metastore',
                        'change': {'actions': ['delete'], 'before': None, 'after': None},
                    },
                    {
                        'address': 'azurerm_storage_account.lake',
                        'type': 'azurerm_storage_account',
                        'change': {'actions': ['delete'], 'before': None, 'after': None},
                    },
                ],
            }, ['databricks_metastore', 'azurerm_storage_account'], expected=['databricks_metastore.this would be destroyed', 'azurerm_storage_account.lake would be destroyed']),
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_databricks_workspace.this',
                        'type': 'azurerm_databricks_workspace',
                        'change': {'actions': ['delete'], 'before': None, 'after': None},
                    },
                ],
            }, [], expected=[]),
            case({}, ['azurerm_databricks_workspace'], expected=[]),
        ],
        guided="""def guard_destroys(plan, protected):
    # Replace every ___ with real code, then run the tests.

    # Step 1: a set makes "is this type protected?" instant.
    protected = set(protected)
    out = []

    for rc in plan.get("resource_changes", []):
        # Step 2: protected type AND its actions include "delete".
        #         (A replacement includes "delete" too.)
        if rc["type"] in protected and ___:
            # Step 3: add the message in the exact format the tests expect.
            out.append(___)

    return out
""",
        concepts=[
            [
                'Set for lookups',
                'Checking `x in a_set` is instant; checking a list walks every item.',
                """protected = set(['azurerm_storage_account'])
'azurerm_storage_account' in protected""",
            ],
            [
                'The same rule in Rego',
                'Spacelift plan policies are written in Rego, a query language. The rule reads: for any resource change whose actions include delete and whose type is protected, add a deny message.',
                """package spacelift

import rego.v1

protected := {"azurerm_databricks_workspace", "azurerm_storage_account"}

deny contains sprintf("%s would be destroyed", [rc.address]) if {
	rc := input.terraform.resource_changes[_]
	"delete" in rc.change.actions
	rc.type in protected
}""",
            ],
            ['String joining', '`+` joins two strings.', "'databricks_metastore.this' + ' would be destroyed'"],
        ],
        byhand="The workspace is a protected type and its actions include delete (it's a replacement), so it gets a message. The cluster is deleted but its type isn't protected, so it's fine.",
        why='One pass; each check is a set lookup and a short list check.',
        gotchas=[
            [
                'Policies can be bypassed by state surgery',
                'A plan policy only sees plans. `terraform state rm` or a manual delete in the portal never goes through it. Lock down who can run tasks on production stacks too.',
            ],
            [
                'Warn first, then deny',
                'Spacelift plan policies support `warn` as well as `deny`. Rolling a new rule out as a warning shows you what it would have blocked before it blocks anyone.',
            ],
        ],
    ),
)

lesson(MODULE, 'lock_info',
    title='State and locking',
    learn=[
        "**State** is Terraform's record of what it manages. Two runs writing it at once would corrupt it, so runs take a **lock** first.",
        'A crashed run can leave the lock behind. Before `terraform force-unlock`, check who holds it and whether that run is really dead.',
    ],
    example=example("The error you'll see", """Error: Error acquiring the state lock
Error message: state blob is already locked
Lock Info:
  ID:  6a3c...
  Who: spacelift@worker-7"""),
    check=question(
        'When is it safe to run `terraform force-unlock`?',
        ['Whenever a run is blocked', 'Only after confirming the run holding the lock has stopped', 'Never'],
        answer=1,
        why='Unlocking while a run is still applying lets two applies write state at once.',
    ),
    angle=angle(
        pattern='Parsing text',
        text='One walk through the lines, splitting each one on the first colon only.',
        say='"I scan once, start collecting at the Lock Info heading, and split each line on the first colon so the timestamp stays whole."',
        classic=None,
    ),
    exercise=exercise(
        title='Read a State Lock Error',
        topic='state',
        difficulty='easy',
        fn='lock_info',
        prompt="""A run failed with Terraform's state lock error, shown below as `text`. Before anyone runs `terraform force-unlock`, you need the facts: who holds the lock, since when, and doing what.

Return a dict of the fields under `Lock Info:`, with lowercase keys and the values trimmed: `id`, `path`, `operation`, `who`, `version`, `created`. Leave out fields with no value. If there is no `Lock Info:` section, return `{}`.

Careful: `Created` contains colons of its own.""",
        pattern='Find where the section starts, then split each line on the first colon only.',
        target='one pass over the lines',
        realworld="A lock left by a crashed run blocks every later plan. Force-unlocking while a run is genuinely still applying can corrupt state, so you check `Who` and `Created` first. On Spacelift-managed state, Spacelift handles locking and you'd look at the stack's runs instead.",
        starter="""def lock_info(text):
    # your code here
    pass
""",
        solution="""def lock_info(text):
    out = {}
    inside = False
    for line in text.splitlines():
        if line.strip() == "Lock Info:":
            inside = True
            continue
        if inside and ":" in line:
            key, value = line.split(":", 1)
            if value.strip():
                out[key.strip().lower()] = value.strip()
    return out
""",
        cases=[
            case("""Error: Error acquiring the state lock

Error message: state blob is already locked
Lock Info:
  ID:        6a3c1b0e-8f2d-4c1a-9e57-0c2b7d5f9a11
  Path:      tfstate/prod.databricks.tfstate
  Operation: OperationTypeApply
  Who:       spacelift@worker-7
  Version:   1.9.5
  Created:   2026-10-08 22:14:03.123456 +0000 UTC
  Info:      
""", expected={
                'id': '6a3c1b0e-8f2d-4c1a-9e57-0c2b7d5f9a11',
                'path': 'tfstate/prod.databricks.tfstate',
                'operation': 'OperationTypeApply',
                'who': 'spacelift@worker-7',
                'version': '1.9.5',
                'created': '2026-10-08 22:14:03.123456 +0000 UTC',
            }, sample=True),
            case("""Error: Invalid provider configuration
""", expected={}),
            case("""Lock Info:
  ID:        abc
  Who:       ana@laptop
""", expected={'id': 'abc', 'who': 'ana@laptop'}),
            case("""Error message: state blob is already locked
Lock Info:
  ID: x1
  Created:   2026-01-02 03:04:05 +0000 UTC
""", expected={'id': 'x1', 'created': '2026-01-02 03:04:05 +0000 UTC'}),
            case('', expected={}),
        ],
        guided="""def lock_info(text):
    # Replace every ___ with real code, then run the tests.

    out = {}
    inside = False   # have we reached the Lock Info: section yet?

    for line in text.splitlines():
        # Step 1: switch on when you reach the section heading.
        if line.strip() == "Lock Info:":
            inside = True
            continue

        if inside and ":" in line:
            # Step 2: split on the FIRST colon only. The second argument
            #         to split says how many cuts to make.
            key, value = line.split(":", ___)

            # Step 3: skip empty values; store lowercase, trimmed keys.
            if value.strip():
                out[___] = value.strip()

    return out
""",
        concepts=[
            ['splitlines', 'Cuts text into a list of lines.', "'a\\nb'.splitlines()   # ['a', 'b']"],
            [
                'split with a limit',
                "`split(':', 1)` cuts at the first colon only, so a time like 22:14:03 stays in one piece.",
                """'Created: 22:14:03'.split(':', 1)
# ['Created', ' 22:14:03']""",
            ],
            [
                'A flag variable',
                "A True/False variable that remembers whether you've reached the part you care about.",
                """inside = False
...
inside = True""",
            ],
        ],
        byhand='Skip lines until `Lock Info:`. Then `  ID:        6a3c…` splits at the first colon into `ID` and the value; lowercase and trim both. `Created:` keeps its time intact because you only cut once. `Info:` has nothing after it, so leave it out.',
        why='One pass over the lines.',
        gotchas=[
            [
                'Check before you force-unlock',
                "If `Who` is a runner that's still applying, unlocking lets a second apply write the same state at the same time. Confirm the run is dead first, then `terraform force-unlock <ID>`.",
            ],
            [
                'The azurerm backend lock is a blob lease',
                'With the `azurerm` backend, the lock is a lease on the state blob in your storage account. A crashed run can leave the lease behind, which is exactly when this error appears.',
            ],
        ],
    ),
)

lesson(MODULE, 'missing_tags',
    title='Tagging for cost and policy',
    learn=[
        'Azure tags drive **cost allocation** and **Azure Policy**. Missing tags mean spend nobody can attribute.',
        'azurerm has no provider-wide default tags, so teams merge a shared `local.tags` into every resource, and check plans for gaps.',
    ],
    example=example('A shared tag map', """locals {
  tags = { env = var.env, owner = "platform", cost-center = "1234" }
}
tags = merge(local.tags, { component = "dbw" })"""),
    check=question(
        'Which resource in this plan should your tag check skip?',
        [
            '`azurerm_databricks_workspace`',
            '`databricks_catalog` (it has no Azure tags)',
            '`azurerm_storage_account`',
        ],
        answer=1,
        why="Databricks resources aren't Azure resources, so they have no tags attribute.",
    ),
    angle=angle(
        pattern='Dict of results',
        text='One walk through the plan; each missing-tag check is an instant dict lookup.',
        say='"I only check resources that support tags, treat null as no tags, and return a dict from address to the missing keys."',
        classic=None,
    ),
    exercise=exercise(
        title='Enforce Required Tags',
        topic='tagging',
        difficulty='medium',
        fn='missing_tags',
        prompt="""Your Azure policy requires certain tags on every resource that supports them. Given a `plan` and a list of `required` tag keys, check every resource the plan creates or updates (its actions include `"create"` or `"update"`).

Only resources whose `change.after` has a `"tags"` key support tags. Databricks resources and things like `azurerm_subnet` don't have one, so skip them. A `tags` value of `None` means no tags.

Return a dict mapping each failing `address` to its missing keys, sorted. Resources with nothing missing are left out.""",
        pattern="Dict of results, filled only when there's a problem. Guard against `None` before looking inside.",
        target='one pass over resource_changes',
        realworld="Cost allocation and Azure Policy both depend on tags. Catching a missing `cost-center` in the PR's Spacelift run is much cheaper than finding untagged spend at the end of the month.",
        starter="""def missing_tags(plan, required):
    # your code here
    pass
""",
        solution="""def missing_tags(plan, required):
    out = {}
    for rc in plan.get("resource_changes", []):
        actions = rc["change"]["actions"]
        if "create" not in actions and "update" not in actions:
            continue
        after = rc["change"]["after"] or {}
        if "tags" not in after:
            continue
        tags = after["tags"] or {}
        missing = sorted(k for k in required if k not in tags)
        if missing:
            out[rc["address"]] = missing
    return out
""",
        cases=[
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_databricks_workspace.this',
                        'type': 'azurerm_databricks_workspace',
                        'change': {
                            'actions': ['update'],
                            'before': None,
                            'after': {'name': 'dbw-sales-prod', 'sku': 'premium', 'tags': {'env': 'prod'}},
                        },
                    },
                    {
                        'address': 'azurerm_subnet.host',
                        'type': 'azurerm_subnet',
                        'change': {
                            'actions': ['create'],
                            'before': None,
                            'after': {'name': 'snet-dbw-host', 'address_prefixes': ['10.20.1.0/24']},
                        },
                    },
                    {
                        'address': 'databricks_catalog.sales',
                        'type': 'databricks_catalog',
                        'change': {'actions': ['create'], 'before': None, 'after': {'name': 'sales'}},
                    },
                ],
            }, ['cost-center', 'env', 'owner'], expected={'azurerm_databricks_workspace.this': ['cost-center', 'owner']}, sample=True),
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_storage_account.lake',
                        'type': 'azurerm_storage_account',
                        'change': {'actions': ['create'], 'before': None, 'after': {'name': 'stsalesprod', 'tags': None}},
                    },
                ],
            }, ['env'], expected={'azurerm_storage_account.lake': ['env']}),
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_storage_account.old',
                        'type': 'azurerm_storage_account',
                        'change': {'actions': ['delete'], 'before': {'tags': {}}, 'after': None},
                    },
                ],
            }, ['env'], expected={}),
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_databricks_access_connector.uc',
                        'type': 'azurerm_databricks_access_connector',
                        'change': {
                            'actions': ['create'],
                            'before': None,
                            'after': {'name': 'ac-uc', 'tags': {'env': 'dev', 'owner': 'platform', 'cost-center': '1234'}},
                        },
                    },
                ],
            }, ['owner', 'env', 'cost-center'], expected={}),
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_resource_group.this',
                        'type': 'azurerm_resource_group',
                        'change': {'actions': ['no-op'], 'before': None, 'after': {'tags': {}}},
                    },
                ],
            }, ['env'], expected={}),
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_databricks_workspace.this',
                        'type': 'azurerm_databricks_workspace',
                        'change': {'actions': ['delete', 'create'], 'before': None, 'after': {'tags': {'owner': 'ana'}}},
                    },
                ],
            }, ['owner', 'env'], expected={'azurerm_databricks_workspace.this': ['env']}),
        ],
        guided="""def missing_tags(plan, required):
    # Replace every ___ with real code, then run the tests.

    out = {}
    for rc in plan.get("resource_changes", []):
        actions = rc["change"]["actions"]

        # Step 1: only resources being created or updated.
        if "create" not in actions and "update" not in actions:
            continue

        # Step 2: after is None for a plain delete. "or {}" swaps None for an empty dict.
        after = rc["change"]["after"] or {}

        # Step 3: no "tags" key means this resource type can't be tagged.
        if ___:
            continue
        tags = after["tags"] or {}

        # Step 4: which required keys are not in tags? Sort them.
        missing = sorted(___)
        if missing:
            out[rc["address"]] = missing

    return out
""",
        concepts=[
            [
                'or as a fallback',
                '`x or {}` gives `{}` when x is None (or empty). Handy because the plan uses null for "nothing".',
                """after = None
after or {}   # {}""",
            ],
            [
                'continue',
                'Skips the rest of this loop turn and moves to the next item.',
                """for rc in changes:
    if not wanted:
        continue
    ...""",
            ],
            [
                'sorted with a filter',
                'Build a list from another, keeping some items, and sort it in one line.',
                """sorted(k for k in ['owner', 'env'] if k not in {'env': 'prod'})
# ['owner']""",
            ],
        ],
        byhand='The workspace is updated and has tags with only env, so cost-center and owner are missing. The subnet has no tags key: skip. The catalog is a Databricks resource with no tags key: skip.',
        why='One pass over the plan; each tag check is a dict lookup.',
        gotchas=[
            [
                'azurerm has no default_tags',
                'Unlike the AWS provider, azurerm can\'t tag everything for you. Teams keep a `local.tags` map and merge it into every resource: `tags = merge(local.tags, { component = "dbw" })`. A check like this one catches the resources someone forgot.',
            ],
            [
                'Workspace tags reach the managed resource group',
                "Tags on `azurerm_databricks_workspace` are applied to the resources Databricks creates in its managed resource group, which you can't tag directly. Add cluster tags (`custom_tags`) too, so compute cost can be split by team.",
            ],
        ],
    ),
)

lesson(MODULE, 'grants_to_revoke',
    title='Unity Catalog grants',
    learn=[
        '**Unity Catalog** controls who can use which data. `databricks_grants` is **authoritative**: on apply it makes the grants match the code exactly, removing anything else.',
        'Grants added by hand in Catalog Explorer disappear at the next apply. Put them in code, or use the non-authoritative `databricks_grant` for that principal.',
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
        pattern='Set difference',
        text="For each principal, take away the privileges that are in code from the ones that are live. What's left is a set difference.",
        say='"For each principal I take the live privileges minus the ones in code; whatever is left is what an authoritative apply will remove."',
        classic=None,
    ),
    exercise=exercise(
        title='Predict Grant Drift',
        topic='unity-catalog',
        difficulty='medium',
        fn='grants_to_revoke',
        prompt="""`databricks_grants` is authoritative: on every apply it makes a securable's grants exactly match the code, removing anything else. Someone has added grants in Catalog Explorer, so the next apply will take them away.

`code` and `live` are dicts mapping a principal (a group name, or a service principal's application ID) to its list of privileges on one catalog. Return a dict of what the next apply will revoke: each principal mapped to the privileges it has `live` but not in `code`, sorted. Leave out principals with nothing revoked.""",
        pattern='Set difference, per key. A principal missing from `code` entirely loses everything.',
        target='one pass over the live grants',
        realworld='This is the classic surprise with `databricks_grants`: a manual grant in the UI quietly disappears at the next Spacelift apply. Either put it in code, or manage that principal with the non-authoritative `databricks_grant` instead.',
        starter="""def grants_to_revoke(code, live):
    # your code here
    pass
""",
        solution="""def grants_to_revoke(code, live):
    out = {}
    for principal, privileges in live.items():
        keep = set(code.get(principal, []))
        gone = sorted(set(privileges) - keep)
        if gone:
            out[principal] = gone
    return out
""",
        cases=[
            case({'data-engineers': ['USE_CATALOG', 'USE_SCHEMA', 'SELECT', 'MODIFY']}, {
                'data-engineers': ['USE_CATALOG', 'USE_SCHEMA', 'SELECT', 'MODIFY'],
                'analysts': ['USE_CATALOG', 'SELECT'],
            }, expected={'analysts': ['SELECT', 'USE_CATALOG']}, sample=True),
            case({'analysts': ['USE_CATALOG']}, {'analysts': ['USE_CATALOG']}, expected={}),
            case({'analysts': ['USE_CATALOG', 'SELECT']}, {'analysts': ['USE_CATALOG', 'SELECT', 'MODIFY']}, expected={'analysts': ['MODIFY']}),
            case({'data-engineers': ['ALL_PRIVILEGES']}, {}, expected={}),
            case({}, {'6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10': ['USE_CATALOG', 'BROWSE']}, expected={'6f1c2a3e-1d4b-4c8e-9a0f-2b7e5d3c9a10': ['BROWSE', 'USE_CATALOG']}),
        ],
        guided="""def grants_to_revoke(code, live):
    # Replace every ___ with real code, then run the tests.

    out = {}
    for principal, privileges in live.items():
        # Step 1: what the code says this principal should keep.
        #         A principal not in code at all keeps nothing.
        keep = set(code.get(principal, ___))

        # Step 2: live minus keep, sorted.
        gone = sorted(___)

        if gone:
            out[principal] = gone
    return out
""",
        concepts=[
            [
                'Set difference',
                "`a - b` is everything in a that isn't in b.",
                "{'SELECT', 'MODIFY'} - {'SELECT'}   # {'MODIFY'}",
            ],
            [
                'Looping over a dict',
                '`.items()` gives you each key and value together.',
                """for principal, privs in live.items():
    ...""",
            ],
            [
                'Authoritative vs additive',
                "`databricks_grants` (plural) owns all grants on a securable. `databricks_grant` (singular) manages one principal's grants and leaves the rest alone.",
                """resource "databricks_grants" "sales" {
  catalog = databricks_catalog.sales.name
  grant {
    principal  = "data-engineers"
    privileges = ["USE_CATALOG", "USE_SCHEMA", "SELECT"]
  }
}""",
            ],
        ],
        byhand="data-engineers has the same privileges live and in code: nothing revoked. analysts isn't in code at all, so everything it has live goes: SELECT and USE_CATALOG, sorted.",
        why='One pass over the live principals; each difference is a set operation.',
        gotchas=[
            [
                'Never mix plural and singular on one securable',
                'A `databricks_grants` and a `databricks_grant` on the same catalog fight each other on every apply, and the plan never settles.',
            ],
            [
                'Grant to groups, not people',
                'Grants to individual users break when people leave. Grant to account-level groups (synced from Entra ID) and manage membership there.',
            ],
        ],
    ),
)

lesson(MODULE, 'count_shift',
    title='count vs for_each',
    learn=[
        '`count` names copies by position (`[0]`, `[1]`); `for_each` names them by key (`["bronze"]`).',
        'Remove the first item from a `count` list and every later item shifts position. Terraform sees changed names and replaces them, and for storage containers that deletes their data. Use `for_each`, and `moved` blocks to migrate.',
    ],
    example=example('Migrating safely', """moved {
  from = azurerm_storage_container.lake[1]
  to   = azurerm_storage_container.lake["silver"]
}"""),
    check=question(
        'Containers are `["bronze", "silver", "gold"]` with `count`. You remove "bronze". What does the plan do?',
        ['Deletes bronze only', 'Replaces silver and gold, and deletes the last position', 'Nothing'],
        answer=1,
        why='Position 0 becomes silver and position 1 becomes gold, so both are renamed and replaced, and position 2 goes away.',
    ),
    angle=angle(
        pattern='Position-by-position comparison',
        text='Walk both lists side by side, up to the longer one.',
        say='"I compare position by position; a different name at the same position is a replacement, which is why keys beat positions."',
        classic=None,
    ),
    exercise=exercise(
        title='Predict the count Shift',
        topic='refactoring',
        difficulty='medium',
        fn='count_shift',
        prompt="""The lake's containers are created with `count`:

`count = length(var.containers)` and `name = var.containers[count.index]`.

Terraform tracks them by position: `azurerm_storage_container.lake[0]`, `[1]`, and so on. A container's `name` can't be changed in place, so a different name at the same position means destroy and create.

Given the `old` and `new` lists, return what the plan will do as a list of `[address, action]` in index order, where action is `"replace"`, `"create"` or `"delete"`. Unchanged positions are left out.""",
        pattern='Compare two lists position by position, up to the longer one. Past the end of one list is a create or a delete.',
        target='one pass up to the longer list',
        realworld='Removing `bronze` from the front of `["bronze", "silver", "gold"]` shifts every later container up one position, so Terraform plans to destroy and recreate `silver` and `gold`, along with the data in them. `for_each = toset(var.containers)` keys them by name instead, and a `moved` block migrates existing ones without destroying anything.',
        starter="""def count_shift(old, new):
    # your code here
    pass
""",
        solution="""def count_shift(old, new):
    out = []
    for i in range(max(len(old), len(new))):
        address = "azurerm_storage_container.lake[" + str(i) + "]"
        if i >= len(new):
            out.append([address, "delete"])
        elif i >= len(old):
            out.append([address, "create"])
        elif old[i] != new[i]:
            out.append([address, "replace"])
    return out
""",
        cases=[
            case(['bronze', 'silver', 'gold'], ['silver', 'gold'], expected=[
                ['azurerm_storage_container.lake[0]', 'replace'],
                ['azurerm_storage_container.lake[1]', 'replace'],
                ['azurerm_storage_container.lake[2]', 'delete'],
            ], sample=True),
            case(['bronze', 'silver'], ['bronze', 'silver', 'gold'], expected=[['azurerm_storage_container.lake[2]', 'create']]),
            case(['bronze', 'silver', 'gold'], ['bronze', 'silver', 'gold'], expected=[]),
            case([], ['landing'], expected=[['azurerm_storage_container.lake[0]', 'create']]),
            case(['bronze', 'silver', 'gold'], ['bronze', 'gold'], expected=[['azurerm_storage_container.lake[1]', 'replace'], ['azurerm_storage_container.lake[2]', 'delete']]),
        ],
        guided="""def count_shift(old, new):
    # Replace every ___ with real code, then run the tests.

    out = []
    # Step 1: go up to the longer of the two lists.
    for i in range(___):
        address = "azurerm_storage_container.lake[" + str(i) + "]"

        # Step 2: position i no longer exists in new.
        if i >= len(new):
            out.append([address, "delete"])
        # Step 3: position i didn't exist before.
        elif ___:
            out.append([address, "create"])
        # Step 4: same position, different name.
        elif ___:
            out.append([address, "replace"])

    return out
""",
        concepts=[
            [
                'range up to the longer list',
                '`max(len(a), len(b))` lets you visit every position in either list.',
                """for i in range(max(len(old), len(new))):
    ...""",
            ],
            [
                'count vs for_each',
                '`count` names instances by number, so removing one renumbers the rest. `for_each` names them by key, so nothing else moves.',
                """resource "azurerm_storage_container" "lake" {
  for_each           = toset(var.containers)
  name               = each.key
  storage_account_id = azurerm_storage_account.lake.id
}""",
            ],
            [
                'moved blocks',
                'Tell Terraform an existing object has a new address, so it updates state instead of destroying and recreating.',
                """moved {
  from = azurerm_storage_container.lake[1]
  to   = azurerm_storage_container.lake["silver"]
}""",
            ],
        ],
        byhand='Old: bronze, silver, gold. New: silver, gold. Position 0 was bronze, now silver: replace. Position 1 was silver, now gold: replace. Position 2 had gold, now nothing: delete. Removing one container touched all three.',
        why='One pass up to the longer list.',
        gotchas=[
            [
                'Replacing a container deletes its data',
                "Destroying an `azurerm_storage_container` deletes the blobs in it. Soft delete on the storage account is your safety net; check it's on.",
            ],
            [
                'Migrating count to for_each',
                'Change the resource to `for_each`, then add one `moved` block per existing item, mapping `[0]`, `[1]` to their names. The plan should then show no destroys at all.',
            ],
        ],
    ),
)

lesson(MODULE, 'overlapping_subnets',
    title='Networking for Databricks',
    learn=[
        "**VNet injection** puts a Databricks workspace's clusters in your own virtual network, using a **host** and a **container** subnet. They must not overlap each other or anything they connect to.",
        "Each node uses an address in each subnet, and Azure reserves 5 per subnet, so size them for the clusters you'll need.",
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
        pattern='Interval overlap',
        text='Turn each CIDR into a start number and an end number; two ranges overlap when each starts before the other ends. Checking every pair is fine for a handful of subnets. With many ranges, sort them by start and sweep once, like Merge Intervals.',
        say='"I turn each CIDR into a numeric range. Sorted by start, an overlap is any range that starts before the previous one ends."',
        classic='merge_intervals',
    ),
    exercise=exercise(
        title='Check VNet Injection Subnets',
        topic='networking',
        difficulty='medium',
        fn='overlapping_subnets',
        prompt="""A VNet-injected Databricks workspace needs a host subnet and a container subnet, and they can't overlap each other or anything else in the VNet. `subnets` is a list of `[name, cidr]` pairs such as `["snet-dbw-host", "10.20.0.0/24"]`.

Return every overlapping pair as `[first_name, second_name]`, with the earlier subnet first, in list order.

A CIDR is an address plus a prefix length. `10.20.0.0/24` covers 2 to the power (32 - 24) = 256 addresses, starting at 10.20.0.0. To compare them, turn each address into one number: `a.b.c.d` is `a*256**3 + b*256**2 + c*256 + d`.""",
        pattern='Turn each CIDR into a [start, end] range, then two ranges overlap when each starts before the other ends.',
        target='check each pair once (a VNet has only a handful of subnets)',
        realworld="Azure rejects overlapping subnets, but often only at apply time, deep into a Spacelift run. The same check matters for VNet peering to a hub network, where overlap isn't caught until traffic fails.",
        starter="""def overlapping_subnets(subnets):
    # your code here
    pass
""",
        solution="""def to_range(cidr):
    ip, prefix = cidr.split("/")
    a, b, c, d = [int(x) for x in ip.split(".")]
    start = a * 256 ** 3 + b * 256 ** 2 + c * 256 + d
    size = 2 ** (32 - int(prefix))
    return start, start + size - 1

def overlapping_subnets(subnets):
    ranges = [(name, to_range(cidr)) for name, cidr in subnets]
    out = []
    for i in range(len(ranges)):
        for j in range(i + 1, len(ranges)):
            (n1, (s1, e1)), (n2, (s2, e2)) = ranges[i], ranges[j]
            if s1 <= e2 and s2 <= e1:
                out.append([n1, n2])
    return out
""",
        cases=[
            case([
                ['snet-dbw-host', '10.20.0.0/22'],
                ['snet-dbw-container', '10.20.2.0/24'],
                ['snet-privatelink', '10.20.8.0/26'],
            ], expected=[['snet-dbw-host', 'snet-dbw-container']], sample=True),
            case([['snet-dbw-host', '10.20.1.0/24'], ['snet-dbw-container', '10.20.2.0/24']], expected=[]),
            case([], expected=[]),
            case([['a', '10.0.0.0/16'], ['b', '10.0.255.0/24'], ['c', '10.1.0.0/24']], expected=[['a', 'b']]),
            case([['host', '10.30.0.0/26'], ['container', '10.30.0.64/26'], ['pe', '10.30.0.0/27']], expected=[['host', 'pe']]),
            case([['x', '192.168.1.0/24'], ['y', '192.168.1.0/24']], expected=[['x', 'y']]),
        ],
        guided="""def to_range(cidr):
    # Turn "10.20.0.0/24" into (first_address, last_address) as numbers.
    ip, prefix = cidr.split("/")
    a, b, c, d = [int(x) for x in ip.split(".")]
    start = a * 256 ** 3 + b * 256 ** 2 + c * 256 + d
    # Step 1: how many addresses does this prefix cover?
    size = ___
    return start, start + size - 1


def overlapping_subnets(subnets):
    # Replace every ___ with real code, then run the tests.
    ranges = [(name, to_range(cidr)) for name, cidr in subnets]
    out = []
    # Step 2: every pair once: j always comes after i.
    for i in range(len(ranges)):
        for j in range(___, len(ranges)):
            (n1, (s1, e1)), (n2, (s2, e2)) = ranges[i], ranges[j]
            # Step 3: they overlap when each starts before the other ends.
            if ___:
                out.append([n1, n2])
    return out
""",
        concepts=[
            [
                'CIDR notation',
                '`10.20.0.0/24`: the first 24 bits are fixed, the last 8 vary, giving 2**8 = 256 addresses. A smaller number after the slash means a bigger range.',
                """# /24 -> 256 addresses
# /26 -> 64 addresses
# /22 -> 1024 addresses""",
            ],
            [
                'Unpacking a list',
                'Assign several names at once from a list of the right length.',
                'a, b, c, d = [10, 20, 0, 0]',
            ],
            [
                'Every pair once',
                'Start the inner loop at i + 1 so you never compare a subnet with itself or check a pair twice.',
                """for i in range(n):
    for j in range(i + 1, n):
        ...""",
            ],
        ],
        byhand='10.20.0.0/22 covers 10.20.0.0 to 10.20.3.255. 10.20.2.0/24 is 10.20.2.0 to 10.20.2.255, which sits inside it: overlap. 10.20.8.0/26 starts well after both: fine.',
        why='Each pair is compared once, which is fine for the handful of subnets a VNet has. With many ranges, sorting by start first lets you check each one only against its neighbour, like Merge Intervals.',
        gotchas=[
            [
                'Both subnets need the Databricks delegation',
                'VNet injection requires each subnet to be delegated to `Microsoft.Databricks/workspaces` and associated with a network security group. A missing delegation fails at apply, not plan.',
            ],
            [
                "Size for the cluster you'll need",
                'Each cluster node uses one address in each subnet, and Azure reserves 5 addresses per subnet. A /26 leaves room for about 59 nodes, which teams outgrow.',
            ],
        ],
    ),
)

lesson(MODULE, 'apply_order',
    title='Dependencies and stacks',
    learn=[
        'Terraform builds a **dependency graph** from references between resources and creates things in an order that respects it. A loop in that graph is `Error: Cycle`.',
        "A Databricks provider configured from a workspace that doesn't exist yet can't plan. Split the workspace and its contents into separate Spacelift stacks, with a **stack dependency** between them.",
    ],
    example=example('An implicit dependency', """resource "databricks_metastore_assignment" "this" {
  workspace_id = azurerm_databricks_workspace.this.workspace_id
  metastore_id = var.metastore_id
}"""),
    check=question(
        'Why does a separate stack for workspace contents help on the first deploy?',
        [
            "It's faster",
            'The workspace URL exists by the time the second stack plans',
            'Spacelift requires one stack per provider',
        ],
        answer=1,
        why='The provider needs a real URL at plan time, which only exists after the first stack applies.',
    ),
    angle=angle(
        pattern='Topological sort',
        text='Count how many things each resource is still waiting for, start with the ones waiting for nothing, and each time one finishes, tell the ones waiting on it. This is called a topological sort. Number of Islands uses the same build-the-graph-then-walk-it thinking.',
        say='"I count what each resource is waiting for and keep a list of the ready ones. If some never become ready, there\'s a cycle."',
        classic='num_islands',
    ),
    exercise=exercise(
        title='Work Out the Apply Order',
        topic='dependencies',
        difficulty='medium',
        fn='apply_order',
        prompt="""Terraform builds a dependency graph from the references between resources. `deps` maps each resource address to the list of addresses it depends on, which must exist first.

Return one valid creation order. When several resources are ready at the same time, take them in alphabetical order, so there's exactly one right answer. If the dependencies form a loop, return `None`, which is when Terraform stops with `Error: Cycle`.""",
        pattern='Topological sort: count what each resource is still waiting for, start with the ones waiting for nothing, and each time one is done, tell the resources that were waiting on it.',
        target='each resource and each dependency handled once',
        realworld="Why a Databricks provider pointed at `azurerm_databricks_workspace.this.workspace_url` can't plan the first time in the same stack, why `depends_on` exists, and how Spacelift stack dependencies order a workspace stack before the Unity Catalog stack that configures it.",
        starter="""def apply_order(deps):
    # your code here
    pass
""",
        solution="""def apply_order(deps):
    waiting = {r: len(d) for r, d in deps.items()}
    needed_by = {r: [] for r in deps}
    for r, d in deps.items():
        for x in d:
            needed_by[x].append(r)
    ready = sorted(r for r in deps if waiting[r] == 0)
    order = []
    while ready:
        r = ready.pop(0)
        order.append(r)
        for nxt in needed_by[r]:
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                ready.append(nxt)
        ready.sort()
    if len(order) < len(deps):
        return None
    return order
""",
        cases=[
            case({
                'azurerm_resource_group.this': [],
                'azurerm_virtual_network.this': ['azurerm_resource_group.this'],
                'azurerm_subnet.host': ['azurerm_virtual_network.this'],
                'azurerm_subnet.container': ['azurerm_virtual_network.this'],
                'azurerm_databricks_workspace.this': ['azurerm_subnet.container', 'azurerm_subnet.host'],
                'databricks_metastore_assignment.this': ['azurerm_databricks_workspace.this'],
            }, expected=[
                'azurerm_resource_group.this',
                'azurerm_virtual_network.this',
                'azurerm_subnet.container',
                'azurerm_subnet.host',
                'azurerm_databricks_workspace.this',
                'databricks_metastore_assignment.this',
            ], sample=True),
            case({}, expected=[]),
            case({
                'databricks_catalog.sales': ['databricks_external_location.sales'],
                'databricks_external_location.sales': ['databricks_storage_credential.uc'],
                'databricks_storage_credential.uc': ['azurerm_databricks_access_connector.uc'],
                'azurerm_databricks_access_connector.uc': [],
            }, expected=[
                'azurerm_databricks_access_connector.uc',
                'databricks_storage_credential.uc',
                'databricks_external_location.sales',
                'databricks_catalog.sales',
            ]),
            case({'a': ['b'], 'b': ['a']}, expected=None),
            case({
                'databricks_grants.sales': ['databricks_catalog.sales'],
                'databricks_catalog.sales': [],
                'databricks_schema.raw': ['databricks_catalog.sales'],
            }, expected=['databricks_catalog.sales', 'databricks_grants.sales', 'databricks_schema.raw']),
            case({'x': [], 'y': ['x', 'z'], 'z': ['y']}, expected=None),
        ],
        guided="""def apply_order(deps):
    # Replace every ___ with real code, then run the tests.

    # Step 1: how many things each resource is still waiting for.
    waiting = {r: len(d) for r, d in deps.items()}

    # Step 2: the reverse direction: who is waiting on r?
    needed_by = {r: [] for r in deps}
    for r, d in deps.items():
        for x in d:
            needed_by[x].append(r)

    # Step 3: start with everything waiting for nothing, alphabetically.
    ready = sorted(r for r in deps if ___)
    order = []
    while ready:
        r = ready.pop(0)
        order.append(r)
        # Step 4: r is done, so everyone waiting on r waits for one less.
        for nxt in needed_by[r]:
            waiting[nxt] -= 1
            if ___:
                ready.append(nxt)
        ready.sort()

    # Step 5: anything never reached is stuck in a loop.
    if ___:
        return None
    return order
""",
        concepts=[
            [
                'Implicit dependencies',
                "Referencing another resource's attribute creates a dependency automatically. `depends_on` is only for dependencies Terraform can't see.",
                """resource "databricks_metastore_assignment" "this" {
  workspace_id = azurerm_databricks_workspace.this.workspace_id
  metastore_id = var.metastore_id
}""",
            ],
            [
                'pop(0)',
                'Removes and returns the first item of a list.',
                """ready = ['a', 'b']
ready.pop(0)   # 'a'; ready is now ['b']""",
            ],
            [
                'Counting down',
                'Keep a number per item and subtract as things finish; zero means ready.',
                "waiting['vnet'] -= 1",
            ],
        ],
        byhand='Only the resource group waits for nothing, so it goes first. That frees the VNet. The VNet frees both subnets; take container before host alphabetically. Once both are done, the workspace is free, then the metastore assignment.',
        why='Each resource is added to the order once, and each dependency is counted down once.',
        gotchas=[
            [
                "Provider configured from a resource that doesn't exist yet",
                "A `databricks` provider with `host = azurerm_databricks_workspace.this.workspace_url` can't connect during the very first plan, because the URL isn't known. Put the workspace and its contents in separate Spacelift stacks, with a stack dependency passing the URL along.",
            ],
            [
                'Account-level vs workspace-level providers',
                'Metastores, account groups and metastore assignments use a provider with `host = "https://accounts.azuredatabricks.net"` and `account_id`. Clusters, jobs and catalogs use a workspace-level provider. Mixing them up gives confusing auth errors.',
            ],
        ],
    ),
)

lesson(MODULE, 'plan_policy',
    title='Policy as code',
    learn=[
        "Review rules that live in people's heads get skipped on busy days. **Policy as code** runs them on every plan: Spacelift plan policies, OPA/Rego, and `terraform test`.",
        'Start with the rules that prevent real incidents: never destroy stateful resources, never open workspaces or storage to the public internet.',
    ],
    example=example('Two rules', 'rule 1: protected type + delete            → "... would be destroyed"\nrule 2: create/update + public access on   → "... allows public network access"'),
    check=question(
        'Why roll out a new policy as a warning first?',
        ["It's faster", 'To see what it would block before it blocks anyone', 'Warnings are free'],
        answer=1,
        why='You find false positives without stopping deploys.',
    ),
    angle=angle(
        pattern='Independent rules in one pass',
        text='One walk through the plan, each rule adding its own message.',
        say='"I evaluate independent rules over the plan\'s resource changes in one pass and report every violation, not just the first."',
        classic=None,
    ),
    stack=stack('terraform test with a mocked provider', """mock_provider "azurerm" {}

run "workspace_is_private" {
  command = plan
  assert {
    condition     = azurerm_databricks_workspace.this.public_network_access_enabled == false
    error_message = "Workspaces must not allow public network access"
  }
}"""),
    exercise=exercise(
        title='Policy as Code',
        topic='platform',
        difficulty='medium',
        fn='plan_policy',
        prompt="""Write a plan check like a Spacelift plan policy, with two rules. For each resource change in `plan["resource_changes"]`:

1. If its type is in `protected` and its actions include `"delete"`: `"<address> would be destroyed"`.
2. If its actions include `"create"` or `"update"` and `change.after` has `public_network_access_enabled` set to `True`: `"<address> allows public network access"`.

Return all the messages, in plan order (rule 1 before rule 2 for the same resource).""",
        pattern='One pass, several independent rules, each adding its own message.',
        target='one walk through the plan',
        realworld="Spacelift plan policies (Rego) and `terraform test` with `mock_provider` turn reviewers' rules into checks that run on every PR. Workspaces and storage accounts with public network access enabled are a common finding in security reviews of Azure Databricks setups.",
        starter="""def plan_policy(plan, protected):
    # your code here
    pass
""",
        solution="""def plan_policy(plan, protected):
    out = []
    for rc in plan.get("resource_changes", []):
        actions = rc["change"]["actions"]
        if rc["type"] in protected and "delete" in actions:
            out.append(rc["address"] + " would be destroyed")
        after = rc["change"].get("after") or {}
        if ("create" in actions or "update" in actions) and after.get("public_network_access_enabled") is True:
            out.append(rc["address"] + " allows public network access")
    return out
""",
        cases=[
            case({
                'resource_changes': [
                    {
                        'address': 'azurerm_databricks_workspace.this',
                        'type': 'azurerm_databricks_workspace',
                        'change': {'actions': ['update'], 'after': {'public_network_access_enabled': True}},
                    },
                    {
                        'address': 'azurerm_storage_account.lake',
                        'type': 'azurerm_storage_account',
                        'change': {'actions': ['delete'], 'after': None},
                    },
                ],
            }, ['azurerm_storage_account'], expected=[
                'azurerm_databricks_workspace.this allows public network access',
                'azurerm_storage_account.lake would be destroyed',
            ], sample=True),
            case({}, ['x'], expected=[]),
            case({
                'resource_changes': [
                    {
                        'address': 'w',
                        'type': 'azurerm_databricks_workspace',
                        'change': {'actions': ['delete', 'create'], 'after': {'public_network_access_enabled': True}},
                    },
                ],
            }, ['azurerm_databricks_workspace'], expected=['w would be destroyed', 'w allows public network access']),
            case({
                'resource_changes': [
                    {
                        'address': 's',
                        'type': 'azurerm_storage_account',
                        'change': {'actions': ['no-op'], 'after': {'public_network_access_enabled': True}},
                    },
                ],
            }, [], expected=[]),
        ],
        guided="""def plan_policy(plan, protected):
    # Replace every ___ with real code, then run the tests.

    out = []
    for rc in plan.get("resource_changes", []):
        actions = rc["change"]["actions"]
        # Rule 1: protected and being destroyed.
        if rc["type"] in protected and ___:
            out.append(rc["address"] + " would be destroyed")
        # Rule 2: created or updated with public access on.
        after = rc["change"].get("after") or {}
        if ("create" in actions or "update" in actions) and ___ is True:
            out.append(rc["address"] + " allows public network access")
    return out
""",
        fills=['"delete" in actions', 'after.get("public_network_access_enabled")'],
        concepts=[
            [
                'Independent rules',
                'Separate ifs (not elif) so one resource can break several rules.',
                """if rule_one:
    ...
if rule_two:
    ...""",
            ],
        ],
        byhand='The workspace is updated with public access on: rule 2. The storage account is protected and deleted: rule 1. Two messages, in plan order.',
        why='One walk through the plan.',
        gotchas=[
            [
                'Warn first, then deny',
                'Roll a new rule out as a warning, see what it would have blocked, then make it a deny.',
            ],
            [
                'Test the policy too',
                'Policies are code: keep sample plans that should pass and fail, and check them in CI.',
            ],
        ],
    ),
)
