"""Terraform foundations: read a plan, keep state safe, and change infrastructure in the right order."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, module, practice, question, source

MODULE = module('terraform', 'Terraform foundations', 'Read a plan, keep state safe, and change infrastructure in the right order.', setting=PLATFORM_SETTING)


lesson(MODULE, 'summarize_plan',
    title='What a Terraform plan really says',
    checked='2026-10-13',
    sources=[source('Create a Terraform plan', 'https://developer.hashicorp.com/terraform/tutorials/cli/plan'), source('JSON output format', 'https://developer.hashicorp.com/terraform/internals/json-format')],
    learn=[
        '`terraform plan` compares your code with **state** (what Terraform last applied) and reality, then lists what it will create, update, replace or destroy. A **replacement** (destroy the old one, then create it again) shows up in that summary as one add and one destroy, so the line never says "replace".',
        '`terraform show -json` gives the same plan as data. Spacelift policies and PR checks read this JSON, not the text.',
    ],
    example=example('From plan to JSON', """terraform plan -out tfplan
terraform show -json tfplan > plan.json"""),
    check=question(
        'The plan says "1 to add, 0 to change, 1 to destroy" for one resource. What is happening to it?',
        ["Nothing: it's unchanged", "It's being replaced", "It's being renamed"],
        answer=1,
        why='A replacement destroys the old one and creates it again, so it counts once as an add and once as a destroy. The summary line never says "replace".',
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
        practice=practice(
            intro='Read a plan\'s changes the way a reviewer does: work out what the summary line will say, then find which resources the numbers are.',
            explain='Checks and policies read the plan as data, and the summary line only counts. You counted each create, update and delete on its own, so a replacement was one add and one destroy and a no-op was nothing. Then you found which resource each number belonged to before trusting it.',
            pattern='Count each action, then name the resources',
            realworld='Every Spacelift run and every terraform plan ends with a summary line. Before you approve, you match each number to the resources behind it, so a "1 to destroy" that nobody asked for gets a question.',
            asks=[
                ask('Which change will the summary line not count at all?', ['`azurerm_subnet.host`', '`databricks_cluster.etl`', '`databricks_schema.raw`'], answer=0,
                    evidence=evidence('code', title='The plan\'s changes, as data', text="""[
  {"address": "azurerm_subnet.host",      "actions": ["no-op"]},
  {"address": "databricks_cluster.etl",   "actions": ["update"]},
  {"address": "databricks_schema.raw",    "actions": ["create"]},
  {"address": "databricks_catalog.sales", "actions": ["delete", "create"]}
]"""),
                    clue='Look for the action that means nothing will happen.',
                    why='`no-op` means no change, so it counts nowhere. The summary only counts adds, changes and destroys.',
                    wrong=[None, '`update` is a change in place: it counts once in "to change".', '`create` makes something new: it counts once in "to add".']),
                ask('What will the summary line say?', ['Plan: 2 to add, 1 to change, 1 to destroy.', 'Plan: 1 to add, 1 to change, 1 to destroy.', 'Plan: 1 to add, 1 to change, 0 to destroy.'], answer=0,
                    evidence=evidence('code', title='The same changes', text="""[
  {"address": "azurerm_subnet.host",      "actions": ["no-op"]},
  {"address": "databricks_cluster.etl",   "actions": ["update"]},
  {"address": "databricks_schema.raw",    "actions": ["create"]},
  {"address": "databricks_catalog.sales", "actions": ["delete", "create"]}
]"""),
                    clue='The catalog has two actions, and each one counts on its own.',
                    why='The schema and the catalog\'s new copy are 2 adds, the cluster is 1 change, and the catalog\'s old copy is 1 destroy. The subnet counts nowhere.',
                    wrong=[None, 'That counts the catalog only once. A replacement is an add and a destroy.', 'The catalog\'s delete counts too: a replacement destroys the old one first.']),
                ask('The summary says **1 to destroy**, but nobody removed anything from the code. Which resource is it?', ['`azurerm_databricks_workspace.this`', '`databricks_metastore_assignment.this`', '`azurerm_databricks_access_connector.uc`'], answer=1,
                    evidence=evidence('code', title='Another plan\'s changes', text="""[
  {"address": "azurerm_resource_group.this",
   "actions": ["no-op"]},
  {"address": "azurerm_databricks_workspace.this",
   "actions": ["update"]},
  {"address": "azurerm_databricks_access_connector.uc",
   "actions": ["create"]},
  {"address": "databricks_metastore_assignment.this",
   "actions": ["delete", "create"]}
]"""),
                    clue='Find the change whose actions list has more than one action.',
                    why='Its actions are delete and create: a replacement, so the old one is destroyed first. That is the 1 to destroy, even though nobody took it out of the code.',
                    wrong=['`update` changes it in place: it counts in "to change", not "to destroy".', None, '`create` only adds. It counts in "to add".']),
                ask('You go to apply this morning\'s plan and get this. What do you do?', ['Force the old plan through: it was reviewed already', 'Plan again, and review the new plan before applying', 'Unlock the state, then apply the same plan again'], answer=1,
                    evidence=evidence('code', title='The apply log', text="""Error: Saved plan is stale

The given plan file can no longer be applied because the
state was changed by another operation after the plan was
created."""),
                    clue='The plan was worked out against a state that has changed since.',
                    why='A plan is worked out against the state at one moment. Someone applied since, so plan again and read the new numbers: they may not be the same.',
                    wrong=['There\'s no safe way to force it: the old plan doesn\'t know what changed since.', None, 'Nothing is locked here. The plan is out of date.']),
            ],
        ),
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
    checked='2026-10-15',
    sources=[source('Create and manage resources overview', 'https://developer.hashicorp.com/terraform/language/resources/behavior'), source('azurerm_databricks_workspace', 'https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/databricks_workspace'), source('External locations API: update', 'https://docs.databricks.com/api/workspace/externallocations/update')],
    learn=[
        "Some attributes can't change in place. Changing them **forces replacement**: Terraform destroys the resource and creates a new one.",
        'On an Azure Databricks workspace, that means a new URL and losing everything inside it. Always find every `-/+` (the plan\'s mark for a replacement) before approving.',
    ],
    example=example('In the text plan', """-/+ resource "azurerm_databricks_workspace" "this" {
  ~ managed_resource_group_name = "a" -> "b" # forces replacement"""),
    check=question(
        'Which change to `azurerm_databricks_workspace` forces a replacement?',
        ['Adding or changing a tag', 'Changing `managed_resource_group_name`', 'No change: a workspace is never replaced'],
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
        practice=practice(
            intro='Review a Spacelift plan the way a reviewer does: find the change you\'d stop on, then decide.',
            explain='A replacement destroys a resource and makes a new one, and the summary counts it as one add and one destroy. You found which -/+ change the destroy belonged to before approving, then asked what depended on it instead of approving or resetting anything.',
            pattern='Find every -/+, then ask what uses it',
            realworld='When you review a Spacelift plan that touches a workspace, an external location or a storage account, you look for every -/+ before you approve. If you find one, you ask which grants and jobs use it, and agree a safe time to replace it.',
            asks=[
                ask('Which change would you stop on?', [], answer=3, pick=True,
                    evidence=evidence('plan', title='Stack dbx-service-dev · proposed',
                        summary=[['3', 'to add', 'a'], ['1', 'to change', ''], ['1', 'to destroy', 'd']],
                        changes=[
                            {'sym': '+', 'address': 'databricks_cluster.sales_daily-report', 'note': 'new cluster from clusters.yml'},
                            {'sym': '+', 'address': 'databricks_permissions.team_folder', 'note': 'owner CAN_MANAGE, users CAN_READ'},
                            {'sym': '~', 'address': 'databricks_cluster_policy.shared_std', 'note': 'max_workers 8 → 10'},
                            {'sym': '-/+', 'address': 'databricks_external_location.sales_raw', 'note': 'name changed: forces replacement'},
                        ]),
                    clue='Look for the mark that means destroyed, then made again.',
                    why='Replacing the external location removes it before the new one exists: its grants go, and anything reading it fails. Its url can change in place; its name can\'t.',
                    wrong=['A new cluster is expected from the YAML.', 'New access is worth reading, but nothing is lost here.', 'An in-place change to a limit: worth a look, but nothing is destroyed.', None]),
                ask('The summary says **1 to destroy**, but nobody asked to delete anything. Where does it come from?', ['The replacement: the old one is destroyed first', 'A glitch: nobody removed anything from the code'], answer=0,
                    clue='Look for the change marked -/+.',
                    why='Terraform counts a replacement as one add and one destroy. That "1 to destroy" is the external location going away before the new one exists.',
                    wrong=[None, 'The count is right. Find which change it belongs to before you approve.']),
                ask('The author says nothing reads `sales_raw` on weekends, so it\'s fine. What do you do?', ['Approve: the author knows nothing reads it at weekends', 'Ask which grants and jobs use it, and agree a window', 'Reset the state, so the plan stops wanting a replacement'], answer=1,
                    evidence=evidence('code', title='From the planning log', text="""# databricks_external_location.sales_raw must be replaced
-/+ resource "databricks_external_location" "sales_raw" {
    ~ name            = "sales_raw" -> "sales_landing" # forces replacement
      url             = "abfss://raw@stsalesdev..."
      credential_name = "sales-dev-cred"
  }"""),
                    clue='What was attached to the old one?',
                    why='Ask for the evidence: which grants and jobs use it, and when it can be replaced safely. Approving on a promise, or touching state, is not reviewing.',
                    wrong=['A promise isn\'t evidence. What depends on it?', None, 'Never reset state to deal with a plan you don\'t like.']),
            ],
        ),
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

# The lock error from the lesson's example, shown above each practice question.
_LOCK_ERROR = """Error: Error acquiring the state lock

Error message: state blob is already locked
Lock Info:
  ID:        6a3c1f2e-8b7d-4c5a-9e10-2f4b6d8a0c13
  Path:      tfstate/dbx-service-dev.tfstate
  Operation: OperationTypeApply
  Who:       spacelift@worker-7
  Version:   1.5.7
  Created:   2026-10-09 23:25:51 UTC"""

lesson(MODULE, 'lock_info',
    title='State and locking',
    checked='2026-10-13',
    sources=[source('State locking', 'https://developer.hashicorp.com/terraform/language/state/locking'), source('terraform force-unlock', 'https://developer.hashicorp.com/terraform/cli/commands/force-unlock')],
    learn=[
        "**State** is Terraform's record of what it manages. Two runs writing it at once would corrupt it, so runs take a **lock** first.",
        "A crashed run can leave the lock behind. Before `terraform force-unlock`, check who holds it and whether that run is really dead. This stack keeps its state in an Azure storage account (the azurerm backend). A stack whose state Spacelift manages never shows this error: look at the stack's runs instead.",
    ],
    example=example("The error you'll see", """Error: Error acquiring the state lock

Error message: state blob is already locked
Lock Info:
  ID:        6a3c1f2e-8b7d-4c5a-9e10-2f4b6d8a0c13
  Path:      tfstate/dbx-service-dev.tfstate
  Operation: OperationTypeApply
  Who:       spacelift@worker-7
  Version:   1.5.7
  Created:   2026-10-09 23:25:51 UTC"""),
    check=question(
        'When is it safe to run `terraform force-unlock`?',
        ['Whenever a run is blocked by it', 'Once the run holding it has stopped', 'Never: a lock clears on its own'],
        answer=1,
        why='Unlocking while a run is still applying lets two applies write state at once.',
    ),
    angle=angle(
        pattern='Start reading at the heading',
        text='The big idea: before you force-unlock state, read the lock error to see who holds the lock. Your code goes through the lines with a yes-or-no flag called `inside`, which starts at no. When it reaches `Lock Info:`, the flag turns to yes. Every line after that is cut at its first colon only, with `split(":", 1)`, so the `Created` time keeps its own colons. Both parts are trimmed with `strip` and stored in a dict, a lookup table from each key to its value.',
        say='"Before I force-unlock, I read the lock error to see [[who holds|who wants|who made::The person or job that has it right now.]] the lock. If that run is still [[going|finished|queued::It may still be writing state.]], I wait for it."',
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
        practice=practice(
            intro='Read a state lock error the way a reviewer does: who holds the lock, what it was doing, and whether it\'s safe to unlock.',
            explain='Before you force-unlock state, you read the lock error to see who holds the lock. You found the runner in Who, the apply in Operation and the age in Created, and only unlocked with the ID once you knew that run was dead.',
            pattern='Who holds it, doing what, since when',
            realworld='When a plan stops on "Error acquiring the state lock", you read who holds the lock and what it was doing before anyone runs force-unlock. On a stack whose state Spacelift manages, you look at the stack\'s runs instead.',
            asks=[
                ask('Who is holding the lock?', ['`spacelift@worker-7`', '`tfstate/dbx-service-dev.tfstate`', 'Terraform `1.5.7`'], answer=0,
                    evidence=evidence('code', title='The error your run stopped on', text=_LOCK_ERROR),
                    clue='One line names a person or a machine.',
                    why='The Who line says which runner took the lock: a Spacelift worker, not someone on a laptop. Its run is the one to check.',
                    wrong=[None, 'That\'s the Path: which state file is locked, not who locked it.', 'That\'s the Terraform version the run used.']),
                ask('What was that run doing when it took the lock?', ['Making a plan', 'Applying changes', 'Unlocking the state'], answer=1,
                    evidence=evidence('code', title='The same error', text=_LOCK_ERROR),
                    clue='Read the Operation line.',
                    why='`OperationTypeApply` means it was applying: writing to state. Unlocking under a live apply is how state gets corrupted.',
                    wrong=['A plan would say `OperationTypePlan`.', None, 'Taking a lock is the opposite of unlocking. What does the Operation line say?']),
                ask('It\'s 09:10 the next morning. What does the Created time tell you?', ['The run must be over by now, so unlock it straight away', 'A crashed run may have left it: check that run first', 'Nothing: only Who and ID matter before you unlock'], answer=1,
                    evidence=evidence('code', title='The same error', text=_LOCK_ERROR),
                    clue='An apply rarely takes ten hours. What could leave a lock behind?',
                    why='An apply that started last night shouldn\'t still hold the lock, which points to a crashed run. That\'s a lead, not proof: look at the run on worker-7 before you unlock.',
                    wrong=['Old isn\'t proof it stopped. A long apply could still be writing.', None, 'It matters: a lock this old is a clue the run crashed.']),
                ask('The run that took the lock failed when its worker was lost. What now?', ['Force-unlock with the lock\'s ID, then plan again', 'Wait: the lock clears itself after an hour', 'Delete the state file so nothing is locked'], answer=0,
                    evidence=evidence('code', title='That run in Spacelift', text="""Stack:   dbx-service-dev · tracked
State:   FAILED
Worker:  worker-7
Started: Oct 9th, 11:25:40 PM
Last log line: worker lost connection during apply"""),
                    clue='Now you know the run is dead. Which line of the lock error does the unlock command need?',
                    why='The run is dead, so unlock with the ID from Lock Info. Then plan again: the crashed apply may have changed some things before it stopped.',
                    wrong=[None, 'With the azurerm backend the lock is a lease on the state file, and a crashed run\'s lease doesn\'t run out on its own.', 'Never delete state: Terraform would forget everything it manages.']),
            ],
        ),
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
    checked='2026-10-13',
    sources=[source('count meta-argument', 'https://developer.hashicorp.com/terraform/language/meta-arguments/count'), source('for_each meta-argument', 'https://developer.hashicorp.com/terraform/language/meta-arguments/for_each'), source('Refactor modules (moved blocks)', 'https://developer.hashicorp.com/terraform/language/modules/develop/refactoring')],
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
        ['Deletes bronze and leaves the other two alone', 'Replaces silver and gold, drops the last slot', 'Nothing: the other two keep their names'],
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
        practice=practice(
            intro='Predict what a plan does to containers made with `count` when the list changes, the way a reviewer does before approving.',
            explain='With count, Terraform knows each copy by its position, so you compared the old and new lists place by place. A name moving to a new place means a replace, and replacing a container loses its data. Naming copies by key with for_each, with a moved block for each one that exists, keeps the plan free of destroys.',
            pattern='Spot every name that moves place',
            realworld='When a pull request takes a name out of containers made with count, you check whether the later ones slide to a new place before you approve, because a replace deletes their data. When a team switches to for_each, you look for one moved block per container, so the plan shows 0 to destroy.',
            asks=[
                ask('You add `"gold"` at the end of the list. What does the plan do?', ['Creates `lake[2]` and leaves the others alone', 'Replaces every container, because the list changed', 'Replaces `lake[0]`, because a new name was added'], answer=0,
                    evidence=evidence('code', title='storage.tf', text="""variable "containers" {
  default = ["bronze", "silver"]
}

resource "azurerm_storage_container" "lake" {
  count              = length(var.containers)
  name               = var.containers[count.index]
  storage_account_id = azurerm_storage_account.lake.id
}"""),
                    clue='Do bronze and silver change position?',
                    why='Bronze stays at [0] and silver at [1], so their names don\'t change. Gold takes a new position at the end: one create, nothing destroyed.',
                    wrong=[None, 'Only a position whose name changes is replaced. Did any move?', 'Bronze is still at position 0.']),
                ask('The team only removed `"silver"` from the middle of `["bronze", "silver", "gold"]`. What happens to the data in gold?', ['It\'s kept: gold is still in the list', 'It\'s lost: gold\'s old container is destroyed', 'It moves to `lake[1]`, data and all'], answer=1,
                    evidence=evidence('plan', title='Stack dbx-service-dev · proposed',
                        summary=[['1', 'to add', 'a'], ['0', 'to change', ''], ['2', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-/+', 'address': 'azurerm_storage_container.lake[1]', 'note': 'name "silver" → "gold": forces replacement'},
                            {'sym': '-', 'address': 'azurerm_storage_container.lake[2]', 'note': 'name "gold": destroy'},
                        ]),
                    clue='Look at what the plan does to lake[2], where gold lives today.',
                    why='Gold slid from [2] to [1], so Terraform destroys the container at [2] and makes a new one at [1]. Destroying a container deletes the blobs in it.',
                    wrong=['Gold is still in the list, but at a new position, and count only knows positions.', None, 'Terraform doesn\'t move data. It destroys one container and creates another.']),
                ask('An AI assistant suggests this. Does it stop the shift?', ['Yes: a fixed order means every position stays fixed', 'No: removing a name still moves the ones after it'], answer=1,
                    evidence=evidence('claim', text='Easy fix: keep the list in A to Z order, so the positions never change.'),
                    clue='Take gold out of `["bronze", "gold", "silver"]`. Where does silver end up?',
                    why='Sorting fixes the order, not the positions. Remove gold and silver slides from [2] to [1], so it is replaced. Only a key, like the name, stays put.',
                    wrong=['A sorted list still shifts when something in the middle goes.', None]),
                ask('A teammate switched the containers to `for_each` and opened this plan. Approve it?', ['Yes: `for_each` is the safe way to name them', 'Not yet: it needs `moved` blocks first'], answer=1,
                    evidence=evidence('plan', title='Stack dbx-service-dev · proposed',
                        summary=[['3', 'to add', 'a'], ['0', 'to change', ''], ['3', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-', 'address': 'azurerm_storage_container.lake[0]', 'note': 'bronze'},
                            {'sym': '-', 'address': 'azurerm_storage_container.lake[1]', 'note': 'silver'},
                            {'sym': '-', 'address': 'azurerm_storage_container.lake[2]', 'note': 'gold'},
                            {'sym': '+', 'address': 'azurerm_storage_container.lake["bronze"]', 'note': ''},
                            {'sym': '+', 'address': 'azurerm_storage_container.lake["silver"]', 'note': ''},
                            {'sym': '+', 'address': 'azurerm_storage_container.lake["gold"]', 'note': ''},
                        ]),
                    clue='Count the destroys. To Terraform, a new address is a new container.',
                    why='Without `moved` blocks, Terraform thinks `lake["bronze"]` is new and `lake[0]` is gone, so it destroys all three containers and their data. One `moved` block per container maps the old position to the new key, and the plan shows 0 to destroy.',
                    wrong=['for_each is right, but this plan still deletes every container and its data.', None]),
            ],
        ),
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
    checked='2026-10-13',
    sources=[source('Dependency graph', 'https://developer.hashicorp.com/terraform/internals/graph'), source('Stack dependencies', 'https://docs.spacelift.io/concepts/stack/stack-dependencies')],
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
        practice=practice(
            intro='Work out the order Terraform makes things in, the way a reviewer reads a dependency graph: what\'s ready, what waits, and what\'s stuck.',
            explain='Terraform makes each resource only after the ones it needs. You picked what was ready, saw that two resources ready together can be made at the same time, and spotted two resources stuck waiting on each other. Then you found a dependency Terraform couldn\'t see, because nothing referred to the catalog.',
            pattern='Ready, waiting, or stuck in a cycle',
            realworld='When a plan stops with Error: Cycle, you find the two resources that each wait on the other. When a first deploy fails because something "does not exist" yet, you check whether one resource refers to the other or just types its name as text.',
            asks=[
                ask('Which one can Terraform create first?', ['`rg`', '`vnet`', '`workspace`'], answer=0,
                    evidence=evidence('code', title='What each resource needs first', text="""{
  "workspace": ["container", "host"],
  "host":      ["vnet"],
  "container": ["vnet"],
  "vnet":      ["rg"],
  "rg":        []
}"""),
                    clue='Look for the one whose list is empty.',
                    why='`rg`, the resource group, needs nothing, so it goes first. Everything else waits on something.',
                    wrong=[None, '`vnet` needs `rg` first.', '`workspace` waits on both subnets, which wait on `vnet`.']),
                ask('Once `vnet` exists, what is ready next?', ['Only `workspace`', 'Both subnets, `container` and `host`', 'Nothing: they wait on each other'], answer=1,
                    evidence=evidence('code', title='The same resources', text="""{
  "workspace": ["container", "host"],
  "host":      ["vnet"],
  "container": ["vnet"],
  "vnet":      ["rg"],
  "rg":        []
}"""),
                    clue='Which ones need only `vnet`?',
                    why='`container` and `host` each need only `vnet`, so both are ready and Terraform can make them at the same time. The workspace waits until both exist.',
                    wrong=['The workspace needs both subnets, and they don\'t exist yet.', None, 'Nothing here waits in a loop: every list leads back to `rg`.']),
                ask('Terraform stops with `Error: Cycle`. Which two are waiting on each other?', ['`databricks_catalog.sales` and `databricks_schema.raw`', '`databricks_schema.raw` and `databricks_grants.raw`', '`databricks_catalog.sales` and `databricks_grants.raw`'], answer=1,
                    evidence=evidence('code', title='What each resource needs first', text="""{
  "databricks_catalog.sales": [],
  "databricks_schema.raw": [
    "databricks_catalog.sales",
    "databricks_grants.raw"
  ],
  "databricks_grants.raw": [
    "databricks_schema.raw"
  ]
}"""),
                    clue='Find two that each list the other.',
                    why='The schema waits for its grants, and the grants wait for the schema, so neither can go first. The catalog is fine: it needs nothing. Take out one of the two references to break the loop.',
                    wrong=['The catalog needs nothing, so it can go first. Look further down.', None, 'The catalog needs nothing, and the grants don\'t list it.']),
                ask('On a first deploy, the grants sometimes fail with "Catalog \'sales\' does not exist". Why?', ['The grants type `"sales"` as text, not as a reference', 'Terraform creates resources from the top of the file down', 'Grants always run before catalogs on a first deploy'], answer=0,
                    evidence=evidence('code', title='catalogs.tf', text="""resource "databricks_catalog" "sales" {
  name = "sales"
}

resource "databricks_grants" "sales" {
  catalog = "sales"
  grant {
    principal  = "data-engineers"
    privileges = ["USE_CATALOG"]
  }
}"""),
                    clue='Terraform only learns an order when one resource refers to another.',
                    why='Typed as text, it isn\'t a reference, so Terraform may make both at once. Write `catalog = databricks_catalog.sales.name` and the grants wait for the catalog.',
                    wrong=[None, 'File order means nothing to Terraform: it orders by references.', 'There\'s no such rule: Terraform orders by references.']),
            ],
        ),
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

lesson(MODULE, 'variables_outputs',
    title='Variables, outputs and modules',
    checked='2026-10-14',
    sources=[source('Input variables', 'https://developer.hashicorp.com/terraform/language/values/variables'), source('Output values', 'https://developer.hashicorp.com/terraform/language/values/outputs'), source('Modules', 'https://developer.hashicorp.com/terraform/language/modules')],
    learn=[
        "A **module** is a folder of Terraform code you can use again, like a recipe. You hand it values through **variables**, so the same module builds a dev workspace and a prod one: only the values change.",
        "A module keeps its insides private. It hands values back through **outputs**, and the code that called it reads them as `module.<name>.<output>`. It can't reach past the outputs into the resources inside.",
        "So when other code needs a value from a module, the module has to output it first. A reference to an output that isn't there stops the plan with an error.",
    ],
    example=example('Passing values in and reading one back', """module "workspace" {
  source = "./modules/workspace"
  env    = "dev"
}

provider "databricks" {
  host = module.workspace.workspace_url  # the module's output, not the resource inside it
}"""),
    check=question(
        'The workspace module creates `azurerm_databricks_workspace.this` but has no outputs. Your root code needs its URL. What do you do?',
        [
            'Write module.workspace.azurerm_databricks_workspace.this.workspace_url',
            'Add an output for the URL inside the module, then read module.workspace.workspace_url',
            'Copy the URL from the Azure portal into the code',
        ],
        answer=1,
        why="Outside a module you can only read its outputs, so add `output \"workspace_url\"` inside it first. A URL pasted from the portal goes stale the day the workspace is rebuilt.",
    ),
    angle=angle(
        pattern='Only outputs cross the wall',
        text="The big idea: a module is a closed box. Values go in as variables and come out only as outputs, so the code around it can read `module.<name>.<output>` and nothing deeper. Your code cuts each reference at its dots. It is bad if it doesn't have exactly three parts starting with `module`, if no module has that name, or if that module has no output with that name. It is like a vending machine: you only get what comes out of the slot.",
        say='"A module is a closed box. Values go in as [[variables|outputs|resources::What you hand the module.]] and come out only as [[outputs|variables|state::What the module hands back.]], so anything I need from it has to be output first."',
        classic=None,
    ),
    exercise=exercise(
        title='Find the Broken References',
        topic='modules',
        difficulty='easy',
        fn='bad_refs',
        prompt="""Your function gets two things:

- `outputs`: what each module outputs. It's a dict: each key is a module name and its value is the list of that module's output names, like `{"network": ["host_subnet_id"]}`.
- `refs`: the references your root code makes, like `"module.network.host_subnet_id"`.

A reference only works if it has exactly three parts separated by dots, the first part is `module`, the module exists, and it has an output with that name. Anything longer is reaching into the module's resources, which isn't allowed.

Return the references that don't work, in the order they appear in `refs`.""",
        pattern='Cut each reference at its dots, then check each part in turn: the shape, the module, the output.',
        target='one pass over the references',
        realworld="The classic `Error: Unsupported attribute` in a Databricks platform repo: the root stack reads `module.network.host_subnet_id`, but the network module never declared that output. The fix is an `output` block in the module, not a reference into its resources.",
        practice=practice(
            intro='Read modules the way their callers do: only what comes out of them counts.',
            explain='A module is a closed box: values go in as variables and come out only as outputs. You read outputs by name, passed different values to the same module for dev and prod, and fixed a missing value by adding an output rather than reaching inside.',
            pattern='In as variables, out as outputs',
            realworld='When a plan stops with Error: Unsupported attribute on a module\'s value, you check that the module declares that output, and add one if it doesn\'t. When someone needs a prod workspace like the dev one, you pass the same module new values instead of copying its folder.',
            asks=[
                ask('Which reference works in the root code?', ['module.workspace.workspace_url', 'module.workspace.azurerm_databricks_workspace.this.workspace_url', 'azurerm_databricks_workspace.this.workspace_url'], answer=0,
                    evidence=evidence('code', title='modules/workspace/outputs.tf', text="""output "workspace_url" {
  value = azurerm_databricks_workspace.this.workspace_url
}"""),
                    clue='Outside the module, you can only see what it hands back.',
                    why='The module declares one output, `workspace_url`, and the root reads it as `module.workspace.workspace_url`.',
                    wrong=[None, 'That reaches past the output into the resource, which only code inside the module can do.', 'That resource lives inside the module, so the root code has no resource by that name.']),
                ask('The same module builds the dev and prod workspaces. What changes between them?', ['The values passed in as variables, like env = "prod"', 'A copy of the module folder for each one', 'The outputs'], answer=0,
                    clue='One recipe, different ingredients.',
                    why='One module, different variable values. Copies drift apart: someone fixes one and forgets the other.',
                    wrong=[None, 'Copies drift apart: fix one, forget the other.', 'Outputs are what comes back, not what goes in.']),
                ask('The root reads `module.network.host_subnet_id` and the plan stops with this. What is the fix?', ['Add a host_subnet_id output to the network module', 'Rename the subnet resource to host_subnet_id', 'Delete the state file and plan again'], answer=0,
                    evidence=evidence('code', title='The plan', text="""Error: Unsupported attribute

This object does not have an attribute
named "host_subnet_id"."""),
                    clue='The root can only read what the module declares.',
                    why='The module never output that value. Add `output "host_subnet_id"` in the network module, and the reference works.',
                    wrong=[None, "The resource's name isn't what's missing: the output is.", 'Never touch state to fix a code error.']),
            ],
        ),
        starter="""def bad_refs(outputs, refs):
    # your code here
    pass
""",
        solution="""def bad_refs(outputs, refs):
    bad = []
    for ref in refs:
        parts = ref.split(".")
        if len(parts) != 3 or parts[0] != "module":
            bad.append(ref)
        elif parts[1] not in outputs:
            bad.append(ref)
        elif parts[2] not in outputs[parts[1]]:
            bad.append(ref)
    return bad
""",
        cases=[
            case({'workspace': ['workspace_url', 'workspace_id'], 'network': ['host_subnet_id']},
                 ['module.workspace.workspace_url', 'module.network.vnet_id', 'module.storage.account_name', 'module.workspace.azurerm_databricks_workspace.this'],
                 expected=['module.network.vnet_id', 'module.storage.account_name', 'module.workspace.azurerm_databricks_workspace.this'], sample=True),
            case({'network': []}, ['module.network.host_subnet_id'], expected=['module.network.host_subnet_id']),
            case({'workspace': ['workspace_url']}, ['module.workspace.workspace_url', 'module.workspace.workspace_url'], expected=[]),
            case({}, [], expected=[]),
            case({'workspace': ['workspace_id']}, ['module.workspace.this.workspace_id'], expected=['module.workspace.this.workspace_id']),
        ],
        guided="""def bad_refs(outputs, refs):
    # Replace every ___ with real code, then run the tests.

    bad = []
    for ref in refs:
        # Step 1: cut the reference at its dots.
        parts = ___
        # A good one has three parts and starts with "module".
        if len(parts) != 3 or parts[0] != "module":
            bad.append(ref)
        # Step 2: no module has that name.
        elif ___:
            bad.append(ref)
        # Step 3: the module has no output with that name.
        elif ___:
            bad.append(ref)

    return bad
""",
        fills=['ref.split(".")', 'parts[1] not in outputs', 'parts[2] not in outputs[parts[1]]'],
        concepts=[
            ['Cutting text at a character', '`split` cuts text wherever a character appears and gives a list of the pieces.', """"module.network.vnet_id".split(".")
# ['module', 'network', 'vnet_id']"""],
            ['Is this key in the dict?', '`in` on a dict checks its keys.', """outputs = {'network': ['host_subnet_id']}
'network' in outputs     # True
'storage' in outputs     # False"""],
            ['A list inside a dict', "Looking up a key gives its value, here a list, and `in` checks that list.", """outputs['network']                       # ['host_subnet_id']
'vnet_id' in outputs['network']          # False"""],
            ['or', '`a or b` is True when at least one of them is True.', """len(parts) != 3 or parts[0] != 'module'"""],
        ],
        byhand="The workspace module outputs workspace_url and workspace_id; the network module outputs host_subnet_id. module.workspace.workspace_url: three parts, the module exists, the output exists: fine. module.network.vnet_id: network has no vnet_id: bad. module.storage.account_name: there's no storage module: bad. module.workspace.azurerm_databricks_workspace.this: four parts, reaching inside: bad.",
        why='One pass over the references.',
        gotchas=[
            ['Sensitive outputs still sit in state', '`sensitive = true` hides a value in plans and in `terraform output`, but state keeps it in plain text. Keep secrets in Key Vault, and limit who can read state.'],
            ['Outputs are a promise', 'Other code reads them by name. Renaming or removing an output breaks every caller, so treat outputs like a public interface.'],
        ],
    ),
)

lesson(MODULE, 'import_existing',
    title='Bringing existing resources under Terraform',
    checked='2026-10-14',
    sources=[source('Import existing resources', 'https://developer.hashicorp.com/terraform/language/import'), source('import block reference', 'https://developer.hashicorp.com/terraform/language/block/import'), source('Import tutorial', 'https://developer.hashicorp.com/terraform/tutorials/state/state-import')],
    learn=[
        "Terraform only manages what is in its **state**. A storage account someone made by hand in the Azure portal isn't there, so as far as Terraform knows, it doesn't exist.",
        "Write a resource block for it and plan, and Terraform wants to **create** it: the apply fails because the name is taken. Instead, add an **import** block (Terraform 1.5 or later) with the resource's address and its Azure ID. The plan then says \"1 to import\", and nothing new is made.",
        "Read the rest of that plan too. If your code doesn't match the real resource, the same plan also **changes** it to match the code, or even replaces it. Adjust the code until the import changes nothing.",
    ],
    example=example('Adopting a storage account made by hand', """import {
  to = azurerm_storage_account.landing
  id = "/subscriptions/<sub>/resourceGroups/rg-sales-dev/providers/Microsoft.Storage/storageAccounts/stsalesdev"
}

resource "azurerm_storage_account" "landing" {
  name                = "stsalesdev"
  resource_group_name = "rg-sales-dev"
  # ...the rest, matching what exists
}"""),
    check=question(
        'A storage account was made by hand. You add a resource block for it, with no import block, and plan. What does the plan want to do?',
        ['Adopt it automatically', 'Create a new one with the same name', 'Nothing'],
        answer=1,
        why="Terraform only knows what is in state, so it plans a create, and the apply fails because the name is taken. An import block tells it to adopt the existing account instead.",
    ),
    angle=angle(
        pattern='In state, imported, or new',
        text="The big idea: Terraform plans from its state, so anything made by hand looks new until you import it. Your code counts the first plan the way Terraform's summary does. For each address in the code: already in state needs nothing; not in state but with an import block is an import; anything else is an add. It is like moving into a furnished flat: list what is already there, or you will buy a second sofa.",
        say="\"Terraform only knows what's in its [[state|code|portal::Its own record of what it manages.]]. Something made by hand looks new, so I add an [[import|moved|output::A block that adopts it instead of creating it.]] block, and check the plan doesn't [[change|import|read::If the code doesn't match, the plan alters it too.]] it as well.\"",
        classic=None,
    ),
    exercise=exercise(
        title='Count the First Plan',
        topic='import',
        difficulty='easy',
        fn='first_plan',
        prompt="""Your function gets three lists of resource addresses, like `"azurerm_storage_account.landing"`:

- `in_code`: every resource your code declares.
- `in_state`: the ones Terraform already manages.
- `imports`: the ones with an `import` block.

Count the plan for the resources in `in_code`:

- Already in state: nothing to do, even if it also has an import block.
- Not in state, but it has an import block: one to import.
- Anything else: one to add.

Return `[to_import, to_add]`.""",
        pattern='Ask the questions in order for each address, and keep two counters.',
        target='one pass over the code',
        realworld="Platform teams adopt resources that were clicked together before Terraform: a storage account, a resource group, a Databricks workspace. A \"1 to add\" for something that already exists is the warning sign: it will fail with \"already exists\", or make a duplicate.",
        practice=practice(
            intro='Adopt resources made by hand without creating, changing or destroying anything by accident.',
            explain="Terraform only knows what is in its state, so something made by hand looks new. You recognised the \"already exists\" error, added an import block instead of recreating anything, and read the import plan for changes the code would make to the real resource.",
            pattern='Adopt it, then check the plan changes nothing',
            realworld='When your team brings a storage account or workspace made by hand under Terraform, you add an import block instead of recreating it. Then you read the import plan for any change it would make to the live resource, and agree that change with its owner.',
            asks=[
                ask('The apply stops with this error. What do you add?', ['An import block with the account\'s ID', 'A moved block to the new address', 'A depends_on on the resource group'], answer=0,
                    evidence=evidence('code', title='The apply', text="""Error: A resource with the ID
"/subscriptions/<sub>/.../storageAccounts/stsalesdev"
already exists - to be managed via Terraform
this resource needs to be imported into
the State."""),
                    clue='The error says what Terraform needs.',
                    why='The account exists but is not in state. An import block adopts it, and the next plan says "1 to import" instead of trying to create it.',
                    wrong=[None, 'moved renames something Terraform already manages; this account was never in state.', "Order isn't the problem: the account already exists."]),
                ask('The import plan also says **1 to change**. What does that mean?', ['The code differs from the real account', 'Imports always count as one change', 'The import failed and will retry'], answer=0,
                    evidence=evidence('plan', title='Stack team-sales-dev · proposed',
                        summary=[['1', 'to import', ''], ['0', 'to add', ''], ['1', 'to change', ''], ['0', 'to destroy', '']],
                        changes=[{'sym': '~', 'address': 'azurerm_storage_account.landing', 'note': 'imported; min_tls_version TLS1_0 → TLS1_2'}]),
                    clue='Compare what the code says with what exists.',
                    why='The code asks for TLS 1.2 and the real account allows 1.0, so applying would change the live account. Decide on purpose: match the code to reality first, or agree the change with the owner.',
                    wrong=[None, 'An import that matches the code changes nothing.', 'A failed import is an error, not a plan.']),
                ask('A teammate says: delete the hand-made account and let Terraform create a fresh one. When is that a bad idea?', ['When it holds data or other things use it', 'Never: a fresh one is always cleaner'], answer=0,
                    clue='What is inside it, and who uses it?',
                    why='Deleting a storage account deletes its data and breaks anything pointing at it. Importing adopts it as it is.',
                    wrong=[None, 'Deleting it deletes its data and breaks whatever uses it.']),
            ],
        ),
        starter="""def first_plan(in_code, in_state, imports):
    # your code here
    pass
""",
        solution="""def first_plan(in_code, in_state, imports):
    to_import = 0
    to_add = 0
    for address in in_code:
        if address in in_state:
            continue
        if address in imports:
            to_import += 1
        else:
            to_add += 1
    return [to_import, to_add]
""",
        cases=[
            case(['azurerm_resource_group.sales', 'azurerm_storage_account.landing', 'databricks_cluster.etl'], ['azurerm_resource_group.sales'], ['azurerm_storage_account.landing'], expected=[1, 1], sample=True),
            case(['azurerm_resource_group.sales'], ['azurerm_resource_group.sales'], [], expected=[0, 0]),
            case(['azurerm_resource_group.sales'], ['azurerm_resource_group.sales'], ['azurerm_resource_group.sales'], expected=[0, 0]),
            case([], [], [], expected=[0, 0]),
            case(['azurerm_resource_group.sales', 'azurerm_storage_account.landing', 'databricks_cluster.etl'], [], ['azurerm_resource_group.sales', 'azurerm_storage_account.landing'], expected=[2, 1]),
        ],
        guided="""def first_plan(in_code, in_state, imports):
    # Replace every ___ with real code, then run the tests.

    to_import = 0
    to_add = 0
    for address in in_code:
        # Step 1: Terraform already manages it, so skip it.
        if ___:
            continue
        # Step 2: it has an import block.
        if ___:
            to_import += 1
        else:
            # Step 3: anything else is new.
            ___

    return [to_import, to_add]
""",
        fills=['address in in_state', 'address in imports', 'to_add += 1'],
        concepts=[
            ['Is it in the list?', '`in` checks whether a list holds a value.', """'a' in ['a', 'b']   # True"""],
            ['continue', '`continue` skips the rest of this turn of the loop and moves on to the next item.', """for n in [1, 2, 3]:
    if n == 2:
        continue
    print(n)   # 1, then 3"""],
            ['Counters', 'Start a number at 0 and add 1 each time something happens. `+= 1` means "add 1 to it".', """count = 0
count += 1   # now 1"""],
            ['Returning two numbers', 'Put them in a list, in the order the task asks for.', 'return [to_import, to_add]'],
        ],
        byhand="In the code: the resource group, the landing storage account and the etl cluster. The resource group is already in state: nothing. The storage account isn't in state but has an import block: one to import. The cluster is neither: one to add. Return [1, 1].",
        why='One pass over the code.',
        gotchas=[
            ['Generate the code, then tidy it', '`terraform plan -generate-config-out=generated.tf` writes a starting resource block from the real resource. Read it and trim it before you commit it.'],
            ['One owner per resource', 'If two stacks import the same resource, they will fight over it on every run. Make sure exactly one stack manages each thing.'],
        ],
    ),
)

lesson(MODULE, 'moved_blocks',
    title='Renaming without destroying',
    checked='2026-10-14',
    sources=[source('Refactoring with moved blocks', 'https://developer.hashicorp.com/terraform/language/modules/develop/refactoring')],
    learn=[
        "Terraform knows each resource by its **address**, like `databricks_cluster.etl`. Rename it in the code to `databricks_cluster.sales_etl` and the plan sees one address gone and a new one: destroy the old cluster, create a new one.",
        "A **moved** block (Terraform 1.1 or later) says it's the same thing with a new name. Terraform updates the name in its state, and the plan shows nothing destroyed. It works for moving a resource into a module, and from `count` to `for_each`, too.",
        "Keep moved blocks in the code afterwards. An environment that hasn't applied the rename yet still needs them, or it would destroy and recreate.",
    ],
    example=example('A rename that stays a rename', """moved {
  from = databricks_cluster.etl
  to   = databricks_cluster.sales_etl
}"""),
    check=question(
        'You rename `databricks_cluster.etl` to `databricks_cluster.sales_etl` and add a moved block. What should the plan show?',
        ['1 to add, 1 to destroy: a new cluster', 'The cluster moves to its new address', "An error: addresses can't change"],
        answer=1,
        why='The moved block tells Terraform the two addresses are the same cluster, so it renames it in state instead of replacing it.',
    ),
    angle=angle(
        pattern='Keep, move, destroy, create',
        text="The big idea: Terraform matches state to code by address, so a rename looks like a destroy plus a create unless a moved block links the two names. Your code goes through the old addresses. Still in the code: keep. Not there, but a move points it at an address that is: move. Otherwise: destroy. Then every new address that is neither old nor the target of a move is a create. It is like a change-of-address card: tell the post office, and your post follows you.",
        say='"Terraform knows things by their [[address|size|owner::The name in the code, like databricks_cluster.etl.]]. If I rename one without a [[moved|import|output::A block linking the old name to the new one.]] block, it looks like one thing gone and a new one, so Terraform destroys it and makes it again."',
        classic=None,
    ),
    exercise=exercise(
        title='Plan a Rename',
        topic='refactoring',
        difficulty='medium',
        fn='plan_rename',
        prompt="""Your function gets three things:

- `old`: the addresses in state now, like `["databricks_cluster.etl"]`.
- `new`: the addresses in the code after your edit.
- `moves`: your moved blocks, as a dict from the old address to the new one.

Return a dict with one action for each address:

- For each old address: `"keep"` if it's still in `new`; `"move"` if `moves` points it at an address that is in `new`; otherwise `"destroy"`.
- For each new address that is not in `old` and that nothing moved into: `"create"`.""",
        pattern='Go through the old addresses first, remembering where each move lands. Then any new address left over is a create.',
        target='one pass over each list',
        realworld="Renaming a cluster, moving a storage account into a shared module, or switching `count` to `for_each`: without moved blocks each one plans a destroy and a create, and for a storage container that destroy deletes its data.",
        practice=practice(
            intro='Rename and reorganise Terraform code so the plan shows moves, not destroys.',
            explain='Terraform matches state to code by address, so a rename looks like a destroy and a create. You spotted the destroy-and-create pair, linked the names with a moved block, and kept the block for the environments that had not applied it yet.',
            pattern='A destroy plus a create is a rename',
            realworld='When a pull request renames a cluster, moves a resource into a module or switches count to for_each, you look for the matching moved blocks before you approve. If the plan still shows a destroy and a create, a moved block is missing or has a typo.',
            asks=[
                ask('You only renamed the cluster in the code. What is missing?', ['A moved block from the old name to the new', 'An import block for databricks_cluster.sales_etl', 'Nothing: approve the rename as it is'], answer=0,
                    evidence=evidence('plan', title='Stack team-sales-dev · proposed',
                        summary=[['1', 'to add', 'a'], ['0', 'to change', ''], ['1', 'to destroy', 'd']],
                        changes=[{'sym': '-', 'address': 'databricks_cluster.etl', 'note': 'not in the code any more'},
                                 {'sym': '+', 'address': 'databricks_cluster.sales_etl', 'note': 'new in the code'}]),
                    clue="Terraform sees two names and doesn't know they are the same cluster.",
                    why='A moved block links the two addresses, and the plan becomes a rename with nothing destroyed.',
                    wrong=[None, "Import adopts something made outside Terraform; this cluster is already managed.", 'Approving destroys the running cluster and makes a new one.']),
                ask('The rename is applied in DEV. Can you delete the moved block now?', ['No: UAT and PROD still need it', 'Yes: DEV applied it, so it did its job'], answer=0,
                    clue='Which environments still have the old name in their state?',
                    why='Every environment that still has the old address needs the block. Terraform recommends keeping moved blocks for good.',
                    wrong=[None, 'Without it, UAT and PROD would destroy and recreate the cluster.']),
                ask('Why does a team switching from count to for_each add blocks like this one?', ['So each container keeps its data under its new key', 'To make the plan run faster', 'Because for_each needs one block per resource'], answer=0,
                    evidence=evidence('code', title='main.tf', text="""moved {
  from = azurerm_storage_container.lake[0]
  to   = azurerm_storage_container.lake["bronze"]
}"""),
                    clue='Without it, [0] and ["bronze"] look like two different containers.',
                    why='Each block tells Terraform that position 0 and the key "bronze" are the same container, so nothing is destroyed and no data is lost.',
                    wrong=[None, "Speed isn't the point: without it, the containers would be replaced.", 'for_each makes many copies from one resource block.']),
            ],
        ),
        starter="""def plan_rename(old, new, moves):
    # your code here
    pass
""",
        solution="""def plan_rename(old, new, moves):
    plan = {}
    targets = []
    for address in old:
        if address in new:
            plan[address] = "keep"
        elif address in moves and moves[address] in new:
            plan[address] = "move"
            targets.append(moves[address])
        else:
            plan[address] = "destroy"
    for address in new:
        if address not in old and address not in targets:
            plan[address] = "create"
    return plan
""",
        cases=[
            case(['databricks_cluster.etl', 'databricks_job.nightly'], ['databricks_cluster.sales_etl', 'databricks_job.nightly'], {'databricks_cluster.etl': 'databricks_cluster.sales_etl'},
                 expected={'databricks_cluster.etl': 'move', 'databricks_job.nightly': 'keep'}, sample=True),
            case(['databricks_cluster.etl', 'databricks_job.nightly'], ['databricks_cluster.sales_etl', 'databricks_job.nightly'], {},
                 expected={'databricks_cluster.etl': 'destroy', 'databricks_job.nightly': 'keep', 'databricks_cluster.sales_etl': 'create'}),
            case(['azurerm_storage_account.lake'], ['module.lake.azurerm_storage_account.this'], {'azurerm_storage_account.lake': 'module.lake.azurerm_storage_account.this'},
                 expected={'azurerm_storage_account.lake': 'move'}),
            case(['databricks_cluster.etl'], ['databricks_cluster.etl2'], {'databricks_cluster.etl': 'databricks_cluster.etl_v2'},
                 expected={'databricks_cluster.etl': 'destroy', 'databricks_cluster.etl2': 'create'}),
            case([], [], {}, expected={}),
            case(['databricks_job.nightly'], ['databricks_job.nightly', 'databricks_job.weekly'], {},
                 expected={'databricks_job.nightly': 'keep', 'databricks_job.weekly': 'create'}),
        ],
        guided="""def plan_rename(old, new, moves):
    # Replace every ___ with real code, then run the tests.

    plan = {}
    targets = []
    for address in old:
        # Step 1: still in the code under the same name.
        if ___:
            plan[address] = "keep"
        # Step 2: a moved block points it at an address in the code.
        elif address in moves and ___:
            plan[address] = "move"
            targets.append(moves[address])
        else:
            plan[address] = "destroy"
    for address in new:
        # Step 3: new, and nothing moved into it.
        if address not in old and ___:
            plan[address] = "create"

    return plan
""",
        fills=['address in new', 'moves[address] in new', 'address not in targets'],
        concepts=[
            ['Building a dict', 'Start with `{}` and set a key with `plan[key] = value`.', """plan = {}
plan['databricks_job.nightly'] = 'keep'
# {'databricks_job.nightly': 'keep'}"""],
            ['Looking something up', '`moves[address]` gives the new address a move points to. Check `address in moves` first, or a missing key is an error.', """moves = {'a.old': 'a.new'}
'a.old' in moves    # True
moves['a.old']      # 'a.new'"""],
            ['and', '`a and b` is True only when both are. Python stops at the first False, so the lookup after `and` only runs when the key exists.', """'a.old' in moves and moves['a.old'] in new"""],
            ['not in', '`not in` is True when the value is missing.', """'x' not in ['a', 'b']   # True"""],
        ],
        byhand="Old: databricks_cluster.etl and databricks_job.nightly. New: databricks_cluster.sales_etl and databricks_job.nightly. The cluster isn't in new, but moves points it at sales_etl, which is: move, and sales_etl is now a move target. The job is still there: keep. In new, sales_etl was moved into and the job is old, so nothing is created.",
        why='One pass over each list.',
        gotchas=[
            ['A moved block changes only the name', "It renames the resource in state; the real thing is untouched. If the plan still shows a destroy, the from or to address has a typo."],
            ['terraform state mv is the old way', 'Before Terraform 1.1 people ran `terraform state mv` by hand. It works, but it leaves no record in the code, and every other environment has to repeat it. Prefer moved blocks.'],
        ],
    ),
)

lesson(MODULE, 'provider_versions',
    title='Pinning provider versions',
    checked='2026-10-14',
    sources=[source('Version constraints', 'https://developer.hashicorp.com/terraform/language/expressions/version-constraints'), source('Dependency lock file', 'https://developer.hashicorp.com/terraform/language/files/dependency-lock'), source('Provider requirements', 'https://developer.hashicorp.com/terraform/language/providers/requirements')],
    learn=[
        "A **provider** is the plugin Terraform downloads to talk to Azure or Databricks. New versions come out often, and a new version can change defaults or how a resource is planned.",
        "In `required_providers` you write a **version constraint**. `~> 4.40` means 4.40 or newer, but not 5.0: only the last number you wrote may go up. `~> 1.90.0` is stricter: 1.90 bug fixes only. Breaking changes usually come with a new major version, so this keeps them out.",
        "`terraform init` writes the exact version it picked into `.terraform.lock.hcl`. Commit that file: every run, on your laptop or in Spacelift, then uses the same version until someone runs `terraform init -upgrade` and the change is reviewed. The lock file covers providers only, not modules.",
    ],
    example=example('Pinning both providers', """terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.40"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.90.0"
    }
  }
}"""),
    check=question(
        'The code says `version = "~> 4.40"`. Which version could Terraform pick?',
        ['5.0.0', '4.45.0', '4.30.0'],
        answer=1,
        why='Only the last number written, 40, may go up, so anything from 4.40 up to (but not including) 5.0. 4.30 is too old, and 5.0 is a new major version.',
    ),
    angle=angle(
        pattern='Compare part by part',
        text="The big idea: a version constraint decides which provider versions Terraform may pick, and `~>` lets only the last number you wrote go up. Your code turns each version into a list of numbers, pads the constraint to three numbers, and compares the lists. `=` needs them equal, `>=` needs the version to be at least as big, and `~>` also needs every number before the last one you wrote to match. It is like agreeing to any reprint of a book's second edition, but not the third edition.",
        say='"With [[~>|>=|=::It lets small steps up in, but not big ones.]], only the last number I wrote may go up, so a new major version stays out. The [[lock file|README|state::.terraform.lock.hcl, committed to the repo.]] keeps every run on the same version until we upgrade on purpose."',
        classic=None,
    ),
    exercise=exercise(
        title='Does the Constraint Allow It?',
        topic='versions',
        difficulty='medium',
        fn='allows',
        prompt="""Your function gets two strings:

- `constraint`: an operator, a space, then a version with two or three numbers, like `"~> 4.40"`, `">= 1.90.0"` or `"= 1.90.3"`.
- `version`: a provider version with three numbers, like `"4.45.0"`.

Turn both versions into lists of numbers, and add 0s to the constraint's list until it has three. Then:

- `"="`: the lists must be equal.
- `">="`: the version must be at least the constraint.
- `"~>"`: at least the constraint, and every number before the last one written in the constraint must match. So `~> 4.40` keeps the 4, and `~> 1.90.0` keeps the 1 and the 90.

Python compares lists number by number, so `[4, 45, 0] >= [4, 40, 0]` is `True`. Return `True` or `False`.""",
        pattern='Turn versions into lists of numbers, so 3.9 comes before 3.10, then compare whole lists.',
        target='a few steps, no loops over the versions',
        realworld="Why a plan can change overnight with no code change: without a committed lock file, `terraform init` picks the newest provider the constraint allows on every run. With `~>` and a lock file, upgrades happen in their own reviewed PR.",
        practice=practice(
            intro='Keep provider upgrades deliberate: read constraints and the lock file the way Terraform does.',
            explain='A version constraint decides which provider versions Terraform may pick, and ~> lets only the last number written go up. The lock file keeps every run on one exact version, so a surprise plan with no code change is often an unlocked upgrade.',
            pattern='Lock file first, then the constraint',
            realworld='When a plan wants to change dozens of resources overnight and nobody touched the Terraform, you check whether the provider version moved. You\'ll also review provider upgrade pull requests, where the lock file changes and the plan should change very little.',
            asks=[
                ask('Version 1.90.5 comes out. What does the next Spacelift run use?', ['1.90.3, from the lock file', '1.90.5, the newest allowed', '1.91.0, the newest release'], answer=0,
                    evidence=evidence('code', title='.terraform.lock.hcl', text="""provider "registry.terraform.io/databricks/databricks" {
  version     = "1.90.3"
  constraints = "~> 1.90.0"
  hashes = [ ... ]
}"""),
                    clue='Which file wins until someone upgrades on purpose?',
                    why='The lock file pins 1.90.3. Only `terraform init -upgrade` moves to 1.90.5, and that change goes through review.',
                    wrong=[None, 'Only terraform init -upgrade picks a newer version.', '~> 1.90.0 never allows 1.91.']),
                ask('Overnight the plan wants to change 40 clusters, and nobody changed the code. The repo has no .terraform.lock.hcl. What is a likely cause?', ['A new provider version was picked up', 'Someone edited the state by hand', 'Spacelift ran the plan twice'], answer=0,
                    clue='Without a lock file, init picks the newest version allowed, every time.',
                    why='With no lock file, each run can pick up a newer provider, and a new version can change defaults. Commit the lock file and upgrade on purpose.',
                    wrong=[None, 'Possible, but check the provider version first: with no lock file, it can change on every run.', "Running twice doesn't change what the plan wants."]),
                ask('Which constraint lets in bug fixes for azurerm but keeps out 5.0?', ['~> 4.40', '>= 4.40', '= 4.40.0'], answer=0,
                    clue='You want a floor and a ceiling.',
                    why='`~> 4.40` allows 4.40 and later 4.x versions, but not 5.0.',
                    wrong=[None, '>= has no ceiling: 5.0 would get in.', '= allows exactly one version: no bug fixes at all.']),
            ],
        ),
        starter="""def allows(constraint, version):
    # your code here
    pass
""",
        solution="""def allows(constraint, version):
    op, wanted = constraint.split(" ")
    want = [int(n) for n in wanted.split(".")]
    have = [int(n) for n in version.split(".")]
    fixed = len(want) - 1
    while len(want) < 3:
        want.append(0)
    if op == "=":
        return have == want
    if op == ">=":
        return have >= want
    return have >= want and have[:fixed] == want[:fixed]
""",
        cases=[
            case('~> 4.40', '4.45.0', expected=True, sample=True),
            case('~> 4.40', '5.0.0', expected=False),
            case('~> 4.40', '4.30.0', expected=False),
            case('~> 4.40', '4.40.0', expected=True),
            case('~> 3.9', '3.10.0', expected=True),
            case('~> 1.90.0', '1.90.4', expected=True),
            case('~> 1.90.0', '1.91.0', expected=False),
            case('>= 1.90.0', '2.0.0', expected=True),
            case('= 1.90.3', '1.90.3', expected=True),
            case('= 1.90.3', '1.90.4', expected=False),
        ],
        guided="""def allows(constraint, version):
    # Replace every ___ with real code, then run the tests.

    op, wanted = constraint.split(" ")
    want = [int(n) for n in wanted.split(".")]
    # Step 1: the version's numbers, the same way.
    have = ___
    # For ~>, the numbers before the last one written must stay the same.
    fixed = len(want) - 1
    while len(want) < 3:
        want.append(0)
    if op == "=":
        return have == want
    # Step 2: at least the constraint.
    if op == ">=":
        return ___
    # Step 3: at least the constraint, and the fixed numbers match.
    return have >= want and ___
""",
        fills=['[int(n) for n in version.split(".")]', 'have >= want', 'have[:fixed] == want[:fixed]'],
        concepts=[
            ['Two names from one split', 'When you know a split gives two pieces, you can name both at once.', """op, wanted = "~> 4.40".split(" ")
# op is '~>', wanted is '4.40'"""],
            ['Text to numbers', "`int` turns text into a number. `[int(n) for n in pieces]` does it for every piece and makes a new list.", """[int(n) for n in "4.40".split(".")]
# [4, 40]"""],
            ['Comparing lists', 'Python compares lists number by number, from the left, and stops at the first difference. Numbers, unlike text, put 9 before 10.', """[3, 10, 0] > [3, 9, 0]   # True
"3.10" > "3.9"           # False: text compares letter by letter"""],
            ['The first few items', '`have[:2]` is the first two items. `have[:0]` is an empty list.', """[1, 90, 4][:2]   # [1, 90]"""],
        ],
        byhand='"~> 4.40" and "4.45.0". The constraint\'s numbers are [4, 40]: two written, so the first one, 4, is fixed. Padded to three: [4, 40, 0]. The version is [4, 45, 0]. It is at least [4, 40, 0], and its first number, 4, matches. True.',
        why='A few steps, whatever the version.',
        gotchas=[
            ['Upgrade on purpose, in its own PR', 'Run `terraform init -upgrade` on a branch, commit the new lock file, and read the plan. A provider bump on its own should change little; if it changes a lot, read the changelog first.'],
            ["Modules aren't in the lock file", 'The lock file pins providers only. Pin a module with an exact version, like `version = "2.3.1"`, or it can move too.'],
        ],
    ),
)
