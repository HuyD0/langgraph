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
        pattern='Three counters, one check each',
        text="The big idea: checks and policies read the plan as data, so you count its changes the way Terraform's summary line does. Your code starts three counters at 0: add, change and destroy. For each change it asks three separate questions. Does `actions` include create? Update? Delete? Each yes adds 1 to its counter. Because the questions are separate, a replacement counts once in add and once in destroy, and a no-op counts nowhere.",
        say='"I go through the plan\'s changes and count by action. A replacement counts as both an add and a destroy, the same as Terraform\'s summary."',
        classic=None,
    ),
    exercise=exercise(
        title='Read the Plan Summary',
        topic='plan-reading',
        difficulty='easy',
        fn='summarize_plan',
        prompt="""`changes` is the list of resource changes in a Terraform plan. Each one is a dict like `{"address": "azurerm_subnet.host", "actions": ["create"]}`.

The `actions` list says what will happen: `["create"]`, `["update"]`, `["delete"]` or `["no-op"]` (no change). A replacement has two actions: `["delete", "create"]` or `["create", "delete"]`.

Count them the way Terraform's summary line does: keep three counts, `add`, `change` and `destroy`, each starting at 0:

- If the actions include `"create"`, count it in `add`.
- If they include `"update"`, count it in `change`.
- If they include `"delete"`, count it in `destroy`.

So a replacement counts once in `add` and once in `destroy`, and `no-op` counts nowhere. Return `[add, change, destroy]`.""",
        pattern='Walk the list once and keep three counters. Check each word with its own `if`, so a replacement counts as both an add and a destroy.',
        target='one pass over the changes',
        realworld='This is the summary line in every Spacelift run and `terraform plan` output. In the real JSON from `terraform show -json`, the list is `plan["resource_changes"]` and each entry keeps its actions at `["change"]["actions"]`. Spacelift policies and PR checks read exactly that.',
        starter="""def summarize_plan(changes):
    # your code here
    pass
""",
        solution="""def summarize_plan(changes):
    add = 0
    change = 0
    destroy = 0
    for item in changes:
        actions = item["actions"]
        if "create" in actions:
            add += 1
        if "delete" in actions:
            destroy += 1
        if "update" in actions:
            change += 1
    return [add, change, destroy]
""",
        cases=[
            case([
                {'address': 'azurerm_subnet.host', 'actions': ['no-op']},
                {'address': 'databricks_cluster.etl', 'actions': ['update']},
                {'address': 'databricks_schema.raw', 'actions': ['create']},
                {'address': 'databricks_catalog.sales', 'actions': ['delete', 'create']},
            ], expected=[2, 1, 1], sample=True),
            case([], expected=[0, 0, 0]),
            case([
                {'address': 'azurerm_resource_group.this', 'actions': ['no-op']},
                {'address': 'databricks_catalog.sales', 'actions': ['create', 'delete']},
            ], expected=[1, 0, 1]),
            case([
                {'address': 'databricks_schema.raw', 'actions': ['delete']},
                {'address': 'databricks_schema.curated', 'actions': ['delete']},
                {'address': 'databricks_grants.sales', 'actions': ['update']},
            ], expected=[0, 1, 2]),
            case([
                {'address': 'azurerm_resource_group.this', 'actions': ['no-op']},
                {'address': 'azurerm_databricks_workspace.this', 'actions': ['update']},
                {'address': 'azurerm_storage_container.lake["bronze"]', 'actions': ['create']},
                {'address': 'azurerm_databricks_access_connector.uc', 'actions': ['create']},
                {'address': 'databricks_metastore_assignment.this', 'actions': ['delete', 'create']},
            ], expected=[3, 1, 1]),
        ],
        guided="""def summarize_plan(changes):
    # Replace every ___ with real code, then run the tests.

    add = 0
    change = 0
    destroy = 0

    for item in changes:
        actions = item["actions"]

        # "create" anywhere in actions counts as an add.
        if "create" in actions:
            add += 1

        # Step 1: "delete" anywhere counts as a destroy.
        # Use a new if, not elif: a replacement has both.
        if ___:
            destroy += 1

        # Step 2: "update" counts as a change.
        if ___:
            change += 1

    return [add, change, destroy]
""",
        fills=['"delete" in actions', '"update" in actions'],
        concepts=[
            [
                'Reading a field from a dict',
                '`item["actions"]` gets the value stored under that key.',
                """pet = {'name': 'Rex', 'age': 3}
pet['name']   # 'Rex'""",
            ],
            [
                'in on a list',
                '`"create" in actions` is True when that word is anywhere in the list.',
                """'tea' in ['coffee', 'tea']    # True
'milk' in ['coffee', 'tea']   # False""",
            ],
            [
                'Separate ifs, not elif',
                'Python checks every `if` on its own. With `elif`, it would stop at the first one that is True, so a replacement would only count once.',
                """drinks = ['tea', 'milk']
if 'tea' in drinks: print('tea')
if 'milk' in drinks: print('milk')   # prints both""",
            ],
            [
                'Adding 1 to a counter',
                '`count += 1` is short for `count = count + 1`.',
                """count = 0
count += 1   # count is now 1""",
            ],
        ],
        byhand='Item 1 is no-op: nothing. Item 2 is update: change is now 1. Item 3 is create: add is now 1. Item 4 is delete and create, a replacement: add goes up to 2 and destroy to 1. Return [2, 1, 1].',
        why='One pass over the changes, with a quick check of a short list each time.',
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
        'On an Azure Databricks workspace, that means a new URL and losing everything inside it. Always find every `-/+` (the plan\'s mark for a replacement) before approving.',
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
        pattern='Keep changes with delete and create',
        text='The big idea: a replacement destroys a resource and makes a new one, so on a Databricks workspace you must find every one before approving. Your code goes through the changes in order. For each one it asks whether `actions` has both `"delete"` and `"create"`. The `and` means both must be there, so a plain delete or a plain create is skipped. Matching addresses go into a list, which keeps them in the same order as the plan.',
        say='"I keep every change whose actions include both delete and create, because that is how a replacement shows up in the plan JSON."',
        classic=None,
    ),
    exercise=exercise(
        title='Spot the Replacements',
        topic='plan-reading',
        difficulty='easy',
        fn='find_replacements',
        prompt="""`changes` is the list of resource changes in a Terraform plan. Each one is a dict like `{"address": "azurerm_subnet.host", "actions": ["create"]}`.

A replacement destroys a resource and creates a new one. On a Databricks workspace, that means a new URL, and everything inside the old one is gone.

A change is a replacement when its `actions` include both `"delete"` and `"create"`, in either order. A plain delete or a plain create is not a replacement.

Return the `address` of every replacement, in the same order as `changes`.""",
        pattern='Filter: keep the entries that match a rule, in their original order.',
        target='one pass over the changes',
        realworld='Approving a plan without spotting a `-/+` is how workspaces get recreated by accident. Changing `managed_resource_group_name`, `location`, or the VNet settings in `custom_parameters` all force a new workspace.',
        starter="""def find_replacements(changes):
    # your code here
    pass
""",
        solution="""def find_replacements(changes):
    found = []
    for item in changes:
        actions = item["actions"]
        if "delete" in actions and "create" in actions:
            found.append(item["address"])
    return found
""",
        cases=[
            case([
                {'address': 'azurerm_databricks_workspace.this', 'actions': ['delete', 'create']},
                {'address': 'databricks_cluster.shared', 'actions': ['update']},
                {'address': 'azurerm_subnet.host', 'actions': ['no-op']},
            ], expected=['azurerm_databricks_workspace.this'], sample=True),
            case([], expected=[]),
            case([
                {'address': 'module.uc.databricks_catalog.sales', 'actions': ['create', 'delete']},
                {'address': 'databricks_schema.raw', 'actions': ['delete']},
                {'address': 'databricks_schema.curated', 'actions': ['create']},
            ], expected=['module.uc.databricks_catalog.sales']),
            case([
                {'address': 'azurerm_storage_container.lake[0]', 'actions': ['delete', 'create']},
                {'address': 'azurerm_storage_container.lake[1]', 'actions': ['delete', 'create']},
            ], expected=['azurerm_storage_container.lake[0]', 'azurerm_storage_container.lake[1]']),
            case([
                {'address': 'databricks_cluster.shared', 'actions': ['update']},
                {'address': 'databricks_job.nightly', 'actions': ['delete']},
            ], expected=[]),
        ],
        guided="""def find_replacements(changes):
    # Replace every ___ with real code, then run the tests.

    found = []
    for item in changes:
        actions = item["actions"]

        # Step 1: a replacement has "delete" AND "create".
        if ___:
            # Step 2: add this change's address to found.
            ___

    return found
""",
        fills=['"delete" in actions and "create" in actions', 'found.append(item["address"])'],
        concepts=[
            [
                'Two conditions with and',
                '`a and b` is True only when both sides are True.',
                """basket = ['milk', 'eggs']
'milk' in basket and 'eggs' in basket   # True""",
            ],
            [
                'Reading a field from a dict',
                '`item["address"]` gets the value stored under that key.',
                """pet = {'name': 'Rex', 'age': 3}
pet['name']   # 'Rex'""",
            ],
            [
                'Building a result list',
                'Start with an empty list, append each match in the loop, return it at the end.',
                """names = []
names.append('ana')   # ['ana']""",
            ],
        ],
        byhand='Change 1, the workspace, has delete and create: a replacement, so keep its address. Change 2, the cluster, is only update: skip it. Change 3, the subnet, is no-op: skip it. Return ["azurerm_databricks_workspace.this"].',
        why='One pass, with two quick checks for each change.',
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
    example=example("A Rego rule (Rego is Spacelift's policy language) that blocks destroying protected resource types", """deny contains msg if {
  rc := input.terraform.resource_changes[_]
  "delete" in rc.change.actions
  rc.type in protected
  msg := sprintf("%s would be destroyed", [rc.address])
}"""),
    check=question(
        'A plan policy blocks destroying storage accounts. Can someone still lose one?',
        [
            "No, it's fully protected",
            'Yes, by deleting it in the Azure portal, with the Azure CLI, or with a local apply outside Spacelift, none of which go through the policy',
            'Only if the policy has a bug',
        ],
        answer=1,
        why='Policies only see plans. Pair them with RBAC (role-based access control: rules for who may do what) and resource locks.',
    ),
    angle=angle(
        pattern='Check each change against a set',
        text='The big idea: a plan policy checks every run automatically, starting with the resources you can\'t rebuild. Your code first turns the protected types into a set, a collection built to answer "is this in it?" instantly, like a book\'s index. Then it goes through the changes in order. A change gets a message only if its type is protected and its actions include delete. A replacement includes delete, so it counts too. An empty list means the run may go ahead.',
        say='"I put the protected types in a set, then flag every change that would delete one of them, replacements included. No messages means the run can go ahead."',
        classic='two_sum',
    ),
    exercise=exercise(
        title='Write a Plan Policy',
        topic='policy',
        difficulty='easy',
        fn='guard_destroys',
        prompt="""Your function gets two things:

- `changes`: the resource changes in a plan. Each one is a dict like `{"address": "azurerm_storage_account.lake", "type": "azurerm_storage_account", "actions": ["delete"]}`. `type` is the kind of resource.
- `protected`: the resource types that must never be destroyed, like `["azurerm_storage_account"]`.

For each change whose `type` is in `protected` and whose `actions` include `"delete"`, make a message: its address followed by `" would be destroyed"`, like `"azurerm_storage_account.lake would be destroyed"`. A replacement, like `["delete", "create"]`, includes `"delete"`, so it counts too.

Return the messages in the same order as `changes`. An empty list means the run may go ahead.""",
        pattern='Filter, then format. Turn the protected list into a set first so each check is instant.',
        target='one pass over the changes',
        realworld='The same logic, in Rego, is what a Spacelift plan policy runs against `input.terraform.resource_changes`. Teams use it to stop a merged PR from deleting a workspace, a storage account or a Unity Catalog metastore.',
        starter="""def guard_destroys(changes, protected):
    # your code here
    pass
""",
        solution="""def guard_destroys(changes, protected):
    protected_types = set(protected)
    messages = []
    for item in changes:
        is_protected = item["type"] in protected_types
        destroyed = "delete" in item["actions"]
        if is_protected and destroyed:
            messages.append(item["address"] + " would be destroyed")
    return messages
""",
        cases=[
            case([
                {
                    'address': 'azurerm_databricks_workspace.this',
                    'type': 'azurerm_databricks_workspace',
                    'actions': ['delete', 'create'],
                },
                {
                    'address': 'databricks_cluster.shared',
                    'type': 'databricks_cluster',
                    'actions': ['delete'],
                },
            ], ['azurerm_databricks_workspace', 'azurerm_storage_account'], expected=['azurerm_databricks_workspace.this would be destroyed'], sample=True),
            case([
                {'address': 'azurerm_storage_account.lake', 'type': 'azurerm_storage_account', 'actions': ['update']},
            ], ['azurerm_storage_account'], expected=[]),
            case([
                {'address': 'databricks_metastore.this', 'type': 'databricks_metastore', 'actions': ['delete']},
                {'address': 'azurerm_storage_account.lake', 'type': 'azurerm_storage_account', 'actions': ['delete']},
            ], ['databricks_metastore', 'azurerm_storage_account'], expected=['databricks_metastore.this would be destroyed', 'azurerm_storage_account.lake would be destroyed']),
            case([
                {'address': 'azurerm_databricks_workspace.this', 'type': 'azurerm_databricks_workspace', 'actions': ['delete']},
            ], [], expected=[]),
            case([], ['azurerm_databricks_workspace'], expected=[]),
        ],
        guided="""def guard_destroys(changes, protected):
    # Replace every ___ with real code, then run the tests.

    # A set makes "is this type protected?" instant.
    protected_types = set(protected)
    messages = []

    for item in changes:
        is_protected = item["type"] in protected_types

        # Step 1: True when "delete" is in this item's actions.
        destroyed = ___

        if is_protected and destroyed:
            # Step 2: the address, then " would be destroyed".
            messages.append(___)

    return messages
""",
        fills=['"delete" in item["actions"]', 'item["address"] + " would be destroyed"'],
        concepts=[
            [
                'Set for lookups',
                '`set(a_list)` makes a set. Checking `x in a_set` is instant; checking a list looks at every item.',
                """fruit = set(['apple', 'pear'])
'pear' in fruit   # True""",
            ],
            [
                'Keeping True or False in a name',
                'A check like `x in y` gives True or False. You can store it in a variable and use it later.',
                """has_tea = 'tea' in ['tea', 'milk']
has_tea   # True""",
            ],
            [
                'Joining strings with +',
                '`+` joins two strings into one.',
                "'ana' + ' is here'   # 'ana is here'",
            ],
        ],
        byhand='Protected: the workspace and storage account types. Change 1 is the workspace. Its type is protected, and its actions include delete (it\'s a replacement). So add "azurerm_databricks_workspace.this would be destroyed". Change 2 is the cluster. It\'s deleted, but its type isn\'t protected, so no message. Return ["azurerm_databricks_workspace.this would be destroyed"].',
        why='One pass; each check is a set lookup and a short list check.',
        gotchas=[
            [
                'Policies only see plans',
                'A delete in the Azure portal, with the Azure CLI, or from a local `terraform apply` outside Spacelift never goes through a plan policy. State commands skip it too: they change what Terraform tracks without a plan. `terraform state rm` doesn\'t delete anything in Azure, but Terraform forgets the resource, so it is no longer managed or protected. Lock down who can run tasks on production stacks too.',
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
        pattern='Start reading at the heading',
        text='The big idea: before you force-unlock state, read the lock error to see who holds the lock. Your code goes through the lines with a yes-or-no flag called `inside`, which starts at no. When it reaches `Lock Info:`, the flag turns to yes. Every line after that is cut at its first colon only, with `split(":", 1)`, so the `Created` time keeps its own colons. Both parts are trimmed with `strip` and stored in a dict, a lookup table from each key to its value.',
        say='"I skip lines until the Lock Info heading, then split each line at its first colon only, so the time stays whole. That tells me who holds the lock."',
        classic=None,
    ),
    exercise=exercise(
        title='Read a State Lock Error',
        topic='state',
        difficulty='easy',
        fn='lock_info',
        prompt="""`lines` is a Terraform state lock error as a list, one string per line, like `["Lock Info:", "  Who: ana@laptop"]`.

Find the line `Lock Info:` and skip every line before it. Each line after it is one field. It starts with a few spaces, like `Who: ana@laptop` with two spaces in front.

Cut each field line at its first colon only, because the `Created` time has colons of its own. The part before the colon is the key, and the part after is the value. Trim both (remove the spaces at each end).

Return a dict of all the fields, like `{"Who": "ana@laptop"}`. If there is no `Lock Info:` line, return `{}`.""",
        pattern='Find where the section starts, then split each line on the first colon only.',
        target='one pass over the lines',
        realworld="A lock left by a crashed run blocks every later plan. Force-unlocking while a run is genuinely still applying can corrupt state, so you check `Who` and `Created` first. On Spacelift-managed state, Spacelift handles locking and you'd look at the stack's runs instead.",
        starter="""def lock_info(lines):
    # your code here
    pass
""",
        solution="""def lock_info(lines):
    info = {}
    inside = False
    for line in lines:
        if line == "Lock Info:":
            inside = True
        elif inside:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info
""",
        cases=[
            case([
                'Error: state blob is already locked',
                'Lock Info:',
                '  ID:      6a3c1b0e',
                '  Who:     spacelift@worker-7',
                '  Created: 2026-10-08 22:14:03 UTC',
            ], expected={
                'ID': '6a3c1b0e',
                'Who': 'spacelift@worker-7',
                'Created': '2026-10-08 22:14:03 UTC',
            }, sample=True),
            case(['Error: Invalid provider configuration'], expected={}),
            case([], expected={}),
            case([
                'Error: Error acquiring the state lock',
                '',
                'Error message: state blob is already locked',
                'Lock Info:',
                '  ID:        6a3c1b0e-8f2d-4c1a-9e57-0c2b7d5f9a11',
                '  Path:      tfstate/prod.databricks.tfstate',
                '  Operation: OperationTypeApply',
                '  Who:       spacelift@worker-7',
                '  Version:   1.9.5',
                '  Created:   2026-10-08 22:14:03.123456 +0000 UTC',
            ], expected={
                'ID': '6a3c1b0e-8f2d-4c1a-9e57-0c2b7d5f9a11',
                'Path': 'tfstate/prod.databricks.tfstate',
                'Operation': 'OperationTypeApply',
                'Who': 'spacelift@worker-7',
                'Version': '1.9.5',
                'Created': '2026-10-08 22:14:03.123456 +0000 UTC',
            }),
            case(['Lock Info:', '  ID: abc', '  Who: ana@laptop'], expected={'ID': 'abc', 'Who': 'ana@laptop'}),
        ],
        guided="""def lock_info(lines):
    # Replace every ___ with real code, then run the tests.

    info = {}
    inside = False   # a flag: reached "Lock Info:" yet?

    for line in lines:
        if line == "Lock Info:":
            # Step 1: we've reached it, so turn the flag on.
            inside = ___
        elif inside:
            # Step 2: cut at the FIRST colon only.
            key, value = line.split(":", ___)
            # Step 3: the key, with its spaces trimmed off.
            info[___] = value.strip()

    return info
""",
        fills=['True', '1', 'key.strip()'],
        concepts=[
            [
                'A flag variable',
                "A True/False variable that remembers whether you've reached the part you care about.",
                """seen_start = False
# later, at the line you were waiting for:
seen_start = True""",
            ],
            [
                'elif with a flag',
                '`elif inside:` means "otherwise, if the flag is on". It runs only when the `if` above it was False.',
                """if line == 'Start': on = True
elif on: print(line)   # lines after 'Start'""",
            ],
            [
                'split with a limit',
                "`split(':', 1)` cuts at the first colon only, so a time like 10:30 stays whole. The two parts can go straight into two names.",
                """key, value = 'Start: 10:30'.split(':', 1)
# key is 'Start', value is ' 10:30'""",
            ],
            [
                'strip',
                '`strip()` removes the spaces from both ends of a string.',
                """'  Name '.strip()   # 'Name'""",
            ],
            [
                'Adding to a dict',
                '`a_dict[key] = value` stores a value under a key.',
                """ages = {}
ages['ana'] = 30   # {'ana': 30}""",
            ],
        ],
        byhand='Line 1 comes before `Lock Info:`, so skip it. Line 2 is `Lock Info:`, so turn the flag on. From now on, every line is a field. Cut line 3 at its first colon. The key is ID with two spaces in front, and the value is 6a3c1b0e with six spaces in front. Trim both: ID is 6a3c1b0e. Line 4 works the same way: Who is spacelift@worker-7. Line 5 is cut at its first colon only, so the time stays whole: Created is 2026-10-08 22:14:03 UTC. Return {"ID": "6a3c1b0e", "Who": "spacelift@worker-7", "Created": "2026-10-08 22:14:03 UTC"}.',
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
        say='"I skip resources that can\'t be tagged, then list the required tags each one is missing. The result pairs each address with its gaps."',
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
        say='"For each principal, I take the live privileges and drop the ones in code. Whatever is left is what the next apply will remove."',
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
        pattern='Compare names position by position',
        text="The big idea: `count` knows copies by position, so removing one item shifts every later name and Terraform replaces them. Your code finds the longer list's length and checks every position up to it. If `new` has run out, the action is delete. If `old` has run out, it is create. Otherwise a different name means replace and the same name means keep. It is like numbered lockers: take out the first person, everyone moves along, and every locker gets a new owner.",
        say='"I compare the old and new names position by position. A different name at the same position is a replacement, which is why naming by key is safer."',
        classic=None,
    ),
    exercise=exercise(
        title='Predict the count Shift',
        topic='refactoring',
        difficulty='medium',
        fn='count_shift',
        prompt="""Your function gets two things:

- `old`: the storage container names in the code now, like `["bronze", "silver"]`.
- `new`: the names after your edit, like `["silver"]`.

The containers use `count`, so Terraform knows them by position: `lake[0]`, `lake[1]`, and so on. A container's name can't be edited. So when a position gets a different name, Terraform deletes that container and makes a new one. That is a replace.

Check every position, up to the end of the longer list, and give one action for each:

- `"keep"`: the same name in both.
- `"replace"`: a different name.
- `"delete"`: `new` has nothing there.
- `"create"`: `old` has nothing there.

Return the actions in position order.""",
        pattern='Compare two lists position by position, up to the longer one. Past the end of one list is a create or a delete.',
        target='one pass up to the longer list',
        realworld='Removing `bronze` from the front of `["bronze", "silver", "gold"]` shifts every later container up one position, so Terraform plans to destroy and recreate `silver` and `gold`, along with the data in them. `for_each = toset(var.containers)` keys them by name instead, and a `moved` block migrates existing ones without destroying anything.',
        starter="""def count_shift(old, new):
    # your code here
    pass
""",
        solution="""def count_shift(old, new):
    actions = []
    longest = max(len(old), len(new))
    for i in range(longest):
        if i >= len(new):
            actions.append("delete")
        elif i >= len(old):
            actions.append("create")
        elif old[i] != new[i]:
            actions.append("replace")
        else:
            actions.append("keep")
    return actions
""",
        cases=[
            case(['bronze', 'silver', 'gold'], ['silver', 'gold'], expected=['replace', 'replace', 'delete'], sample=True),
            case(['bronze', 'silver'], ['bronze', 'silver', 'gold'], expected=['keep', 'keep', 'create']),
            case(['bronze', 'silver', 'gold'], ['bronze', 'silver', 'gold'], expected=['keep', 'keep', 'keep']),
            case([], ['landing'], expected=['create']),
            case(['bronze', 'silver', 'gold'], ['bronze', 'gold'], expected=['keep', 'replace', 'delete']),
            case(['bronze'], [], expected=['delete']),
        ],
        guided="""def count_shift(old, new):
    # Replace every ___ with real code, then run the tests.

    actions = []
    # Step 1: the length of the longer list.
    longest = ___
    for i in range(longest):
        # Position i is past the end of new.
        if i >= len(new):
            actions.append("delete")
        # Step 2: position i is past the end of old.
        elif ___:
            actions.append("create")
        # Step 3: same position, different name.
        elif ___:
            actions.append("replace")
        else:
            actions.append("keep")

    return actions
""",
        fills=['max(len(old), len(new))', 'i >= len(old)', 'old[i] != new[i]'],
        concepts=[
            [
                'range(n)',
                '`range(3)` gives 0, 1, 2: one number for each position. Positions start at 0.',
                """for i in range(3):
    print(i)   # 0, then 1, then 2""",
            ],
            [
                'The longer of two lists',
                '`len` counts the items in a list. `max` picks the bigger of two numbers.',
                "max(len(['a', 'b']), len(['c']))   # 2",
            ],
            [
                'Reading by position',
                '`names[1]` is the item at position 1. A position equal to `len(names)` or more is past the end, so check first. `!=` means "is not equal to".',
                """names = ['ana', 'bo']
names[1]            # 'bo'
names[1] != 'ana'   # True""",
            ],
            [
                'if, elif, else',
                'Python tries each test from the top and runs only the first one that is True. `else` runs when none of them were.',
                """if 7 > 10: size = 'big'
elif 7 > 5: size = 'medium'   # this runs
else: size = 'small'""",
            ],
        ],
        byhand="Old: bronze, silver, gold. New: silver, gold. The longer list has 3 items, so check positions 0, 1 and 2. Position 0 was bronze, now silver: replace. Position 1 was silver, now gold: replace. Position 2 was gold, and new has nothing there: delete. Return [\"replace\", \"replace\", \"delete\"].",
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
        say='"I turn each CIDR into a first and last number, then compare every pair. Two ranges overlap when each starts at or before the other ends."',
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

lesson(MODULE, 'apply_order',
    title='Dependencies and stacks',
    learn=[
        'Terraform builds a **dependency graph** (a map of which resource needs which other one first) from references between resources and creates things in an order that respects it. A loop in that graph is `Error: Cycle`.',
        "A Databricks provider configured from a workspace that doesn't exist yet can't plan. Split the workspace and its contents into separate Spacelift **stacks** (a stack is one set of Terraform code with its own state, planned and applied on its own), with a **stack dependency** between them.",
    ],
    example=example('A dependency Terraform finds on its own, because one resource refers to another', """resource "databricks_metastore_assignment" "this" {
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
        pattern='Add whatever is ready next',
        text='The big idea: Terraform creates each resource after the ones it needs, and resources that wait on each other in a loop cause `Error: Cycle`. Your code repeats until every resource is in the list. Each round it goes through the names A to Z and picks the first one not yet listed whose dependencies are all listed already. It is like getting dressed: socks before shoes. If a round finds nothing ready, the leftovers are waiting on each other, so it returns `None`.',
        say='"I keep adding a resource whose dependencies are already in the list. If some are left but none is ready, they wait on each other in a cycle."',
        classic=None,
    ),
    exercise=exercise(
        title='Work Out the Apply Order',
        topic='dependencies',
        difficulty='medium',
        fn='apply_order',
        prompt="""`deps` says what each resource needs first. It's a dict. Each key is a resource name and its value is the list of names it depends on, like `{"vnet": ["rg"], "rg": []}`.

Build an order Terraform could create them in. Start with an empty list, then repeat:

- Find the resources not in your list yet whose dependencies are all in it.
- Add the one that comes first alphabetically.

When every resource is in the list, return it. If you get stuck, with resources left but none of them ready, they depend on each other in a loop. Then return `None`, like Terraform's `Error: Cycle`.""",
        pattern='Topological sort: keep adding the first resource whose dependencies are all in the list. If none is ready but some are left, there is a loop.',
        target='one look over the names for each resource you add',
        realworld="Why a Databricks provider pointed at `azurerm_databricks_workspace.this.workspace_url` can't plan the first time in the same stack, why `depends_on` exists, and how Spacelift stack dependencies order a workspace stack before the Unity Catalog stack that configures it.",
        starter="""def apply_order(deps):
    # your code here
    pass
""",
        solution="""def apply_order(deps):
    order = []
    while len(order) < len(deps):
        picked = None
        for name in sorted(deps):
            if name in order:
                continue
            waiting = 0
            for dep in deps[name]:
                if dep not in order:
                    waiting += 1
            if waiting == 0:
                picked = name
                break
        if picked is None:
            return None
        order.append(picked)
    return order
""",
        cases=[
            case({
                'workspace': ['container', 'host'],
                'host': ['vnet'],
                'container': ['vnet'],
                'vnet': ['rg'],
                'rg': [],
            }, expected=['rg', 'vnet', 'container', 'host', 'workspace'], sample=True),
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
            ]),
        ],
        guided="""def apply_order(deps):
    # Replace every ___ with real code, then run the tests.

    order = []
    while len(order) < len(deps):
        picked = None
        # Go through the names alphabetically. Skip any
        # that are already in the order list.
        for name in sorted(deps):
            if name in order:
                continue
            # Step 1: count its deps not in the order list yet.
            waiting = 0
            for dep in deps[name]:
                if ___:
                    waiting += 1
            # Step 2: is waiting 0? (use ==, not =)
            # If so, pick it and stop looking.
            if ___:
                picked = name
                break
        # Step 3: if nothing was picked, it's a loop.
        if ___:
            return None
        order.append(picked)

    return order
""",
        fills=['dep not in order', 'waiting == 0', 'picked is None'],
        concepts=[
            [
                'while',
                'Repeats its block for as long as the test is True.',
                """n = 0
while n < 3:
    n += 1   # runs 3 times""",
            ],
            [
                'sorted on a dict',
                '`sorted(a_dict)` gives the keys in alphabetical order.',
                "sorted({'b': 1, 'a': 2})   # ['a', 'b']",
            ],
            [
                'in and not in on a list',
                '`x in a_list` is True when x is in the list. `x not in a_list` is the opposite.',
                """'tea' in ['tea', 'milk']       # True
'cake' not in ['tea', 'milk']  # True""",
            ],
            [
                'continue and break',
                '`continue` skips to the next item. `break` stops the loop straight away, skipping the items left.',
                """for word in ['a', 'skip', 'stop', 'b']:
    if word == 'skip': continue
    if word == 'stop': break""",
            ],
            [
                '== is not =',
                'A single `=` stores a value. `==` asks "are these equal?" and gives True or False.',
                """n = 0    # n now holds 0
n == 0   # True""",
            ],
            [
                'None',
                "Python's value for \"nothing\". Test for it with `is None`.",
                """found = None
found is None   # True""",
            ],
        ],
        byhand="rg is the resource group and vnet is the virtual network. Only rg depends on nothing, so add rg. Now vnet's only dependency, rg, is in the list: add vnet. Now container and host are both ready, and container comes first alphabetically: add it, then host. Now workspace has both its dependencies in the list: add it. Every resource is in, so return [\"rg\", \"vnet\", \"container\", \"host\", \"workspace\"].",
        why='Each round looks over the names once and adds one resource, which is quick for the few dozen resources in a stack.',
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
        "Review rules that live in people's heads get skipped on busy days. **Policy as code** runs them on every plan: Spacelift plan policies, written in Rego (the policy language from Open Policy Agent, or OPA, which Spacelift uses), and `terraform test`.",
        'Start with the rules that prevent real incidents: never destroy resources that hold data you can\'t recreate, like storage accounts and metastores, and never open workspaces or storage to the public internet.',
    ],
    example=example('Two rules', 'rule 1: protected type + delete  → "... would be destroyed"\nrule 2: public access on         → "... allows public network access"'),
    check=question(
        'Why roll out a new policy as a warning first?',
        ["It's faster", 'To see what it would block before it blocks anyone', 'Warnings are free'],
        answer=1,
        why='You find false positives without stopping deploys.',
    ),
    angle=angle(
        pattern='Two separate rules per change',
        text="The big idea: policy as code runs your review rules on every plan, starting with never destroying data you can't recreate and never opening things to the public internet. Your code goes through the changes in order and asks two separate `if` questions about each one. The first flags a protected type with a delete action. The second flags `public_access` being `True`. Neither question stops the other, so one change can get both messages, rule 1 first.",
        say='"I check every change against each rule separately and report every problem, not just the first. One change can break both rules and get both messages."',
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
        prompt="""Your function gets two things:

- `changes`: the resource changes in a plan. Each one is a dict like `{"address": "azurerm_subnet.host", "type": "azurerm_subnet", "actions": ["update"], "public_access": False}`. `public_access` is `True` when the resource will be open to the public internet after this run.
- `protected`: the resource types that must never be destroyed, like `["azurerm_storage_account"]`.

Check each change, in order, against two rules:

- Rule 1: its `type` is in `protected` and its `actions` include `"delete"`. Add its address followed by `" would be destroyed"`.
- Rule 2: its `public_access` is `True`. Add its address followed by `" allows public network access"`.

A change can break both rules: then add both messages, rule 1 first. Return all the messages.""",
        pattern='One pass, two independent rules, each adding its own message.',
        target='one walk through the changes',
        realworld="Spacelift plan policies (Rego) and `terraform test` with `mock_provider` turn reviewers' rules into checks that run on every PR. Workspaces and storage accounts with public network access enabled are a common finding in security reviews of Azure Databricks setups.",
        starter="""def plan_policy(changes, protected):
    # your code here
    pass
""",
        solution="""def plan_policy(changes, protected):
    messages = []
    for item in changes:
        address = item["address"]
        if item["type"] in protected and "delete" in item["actions"]:
            messages.append(address + " would be destroyed")
        if item["public_access"]:
            messages.append(address + " allows public network access")
    return messages
""",
        cases=[
            case([
                {
                    'address': 'azurerm_databricks_workspace.this',
                    'type': 'azurerm_databricks_workspace',
                    'actions': ['update'],
                    'public_access': True,
                },
                {
                    'address': 'azurerm_storage_account.lake',
                    'type': 'azurerm_storage_account',
                    'actions': ['delete'],
                    'public_access': False,
                },
            ], ['azurerm_storage_account'], expected=[
                'azurerm_databricks_workspace.this allows public network access',
                'azurerm_storage_account.lake would be destroyed',
            ], sample=True),
            case([], ['azurerm_storage_account'], expected=[]),
            case([
                {
                    'address': 'azurerm_databricks_workspace.this',
                    'type': 'azurerm_databricks_workspace',
                    'actions': ['delete', 'create'],
                    'public_access': True,
                },
            ], ['azurerm_databricks_workspace'], expected=[
                'azurerm_databricks_workspace.this would be destroyed',
                'azurerm_databricks_workspace.this allows public network access',
            ]),
            case([
                {
                    'address': 'azurerm_storage_account.lake',
                    'type': 'azurerm_storage_account',
                    'actions': ['update'],
                    'public_access': False,
                },
            ], ['azurerm_storage_account'], expected=[]),
            case([
                {
                    'address': 'databricks_cluster.shared',
                    'type': 'databricks_cluster',
                    'actions': ['delete'],
                    'public_access': False,
                },
                {
                    'address': 'azurerm_storage_account.new',
                    'type': 'azurerm_storage_account',
                    'actions': ['create'],
                    'public_access': True,
                },
            ], ['azurerm_storage_account'], expected=['azurerm_storage_account.new allows public network access']),
        ],
        guided="""def plan_policy(changes, protected):
    # Replace every ___ with real code, then run the tests.

    messages = []
    for item in changes:
        address = item["address"]

        # Step 1 (rule 1): protected, and "delete" is in
        # this item's actions.
        if item["type"] in protected and ___:
            messages.append(address + " would be destroyed")

        # Step 2 (rule 2): its public_access is True. Use a
        # new if, not elif, so one item can break both rules.
        if ___:
            messages.append(address + " allows public network access")

    return messages
""",
        fills=['"delete" in item["actions"]', 'item["public_access"]'],
        concepts=[
            [
                'in on a list',
                '`x in a_list` is True when x is anywhere in the list.',
                """'tea' in ['coffee', 'tea']    # True
'milk' in ['coffee', 'tea']   # False""",
            ],
            [
                'Separate ifs for separate rules',
                'Python checks every `if` on its own. With `elif`, it would stop at the first rule that matched.',
                """drinks = ['tea', 'milk']
if 'tea' in drinks: print('tea')
if 'milk' in drinks: print('milk')   # prints both""",
            ],
            [
                'A True/False field',
                '`if task["done"]:` runs its block when that field is True.',
                """task = {'done': True}
if task['done']: print('finished')""",
            ],
            [
                'Joining strings with +',
                '`+` joins two strings into one.',
                "'ana' + ' is here'   # 'ana is here'",
            ],
        ],
        byhand='Change 1 is the workspace. Its type isn\'t protected, so rule 1 doesn\'t apply. Its public_access is True, so rule 2 adds "azurerm_databricks_workspace.this allows public network access". Change 2 is the storage account. It\'s protected and its actions include delete, so rule 1 adds "azurerm_storage_account.lake would be destroyed". Its public_access is False: no rule 2. Return both messages, in that order.',
        why='One walk through the changes.',
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

lesson(MODULE, 'allocate_capacity',
    title="Who gets capacity when it's scarce",
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
        say='"Critical apps are served first. Graduated apps get up to an even share each, so no big app crowds out the rest. Whatever is left goes to the sandbox."',
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

lesson(MODULE, 'check_limits',
    title='A shared space with fair limits',
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
        say='"I check each rule separately and add a fixed message for each failure, so a reviewer sees every problem at once, not just the first."',
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
