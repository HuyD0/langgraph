"""Terraform foundations: read a plan, keep state safe, and change infrastructure in the right order."""

from drill.content.model import angle, case, example, exercise, lesson, module, planned, question, stack

MODULE = module('terraform', 'Terraform foundations', 'Read a plan, keep state safe, and change infrastructure in the right order.')


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
        say='"I count the plan\'s changes by [[action|resource|file::Create, update or delete.]], like Terraform\'s summary line. A [[replacement|no-op|update::It destroys the old one and makes a new one.]] counts as both an add and a destroy."',
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
        say='"A replacement [[destroys|updates|moves::The old resource is gone for good.]] a resource and makes a new one, so I find every one before approving. In the plan JSON it shows up as a change with [[both|either|neither::It needs delete and create, not just one.]] delete and create."',
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
        say='"Before I force-unlock, I read the lock error to see [[who holds|who wants|who made::The person or job that has it right now.]] the lock. I split each line at its [[first colon|last colon|every colon::The time has colons in it too, so cut only once.]], so the time stays whole."',
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
        say='"With count, Terraform knows each copy by its [[position|name|key::Like numbered lockers.]]. Remove one item and every later one [[shifts|stays|vanishes::Everyone moves along a locker.]], so Terraform replaces them. That\'s why I name copies by [[key|number|position::A stable name, not a place in line.]]."',
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
        say='"Terraform makes each resource only after the ones it [[needs|replaces|names::Socks before shoes.]]. I keep picking a resource whose needs are all done. If some are left but none is ready, they\'re stuck in a [[cycle|queue|batch::They all wait on each other in a loop.]]."',
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

planned(MODULE, 'variables_outputs', 'Variables, outputs and modules', 'Passing values in and out of a module, so one module serves dev and prod.')
planned(MODULE, 'import_existing', 'Bringing existing resources under Terraform', 'Importing something made by hand, so the next apply does not recreate it.')
planned(MODULE, 'moved_blocks', 'Renaming without destroying', 'Using a moved block so a rename is a rename, not a destroy and a create.')
planned(MODULE, 'provider_versions', 'Pinning provider versions', 'Why an unpinned provider can change your plan overnight, and how the lock file stops it.')
