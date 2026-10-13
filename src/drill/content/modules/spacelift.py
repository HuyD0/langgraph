"""Spacelift: stacks, runs and the policies that guard every change."""

from drill.content.model import angle, case, example, exercise, lesson, module, planned, question, stack

MODULE = module('spacelift', 'Spacelift', 'Stacks, runs and the policies that guard every change.')


lesson(MODULE, 'runs_after',
    title='What runs after a change?',
    learn=[
        "In **Spacelift**, each piece of infrastructure lives in its own **stack**: one Terraform folder with its own state, run by Spacelift when its code changes. A platform is usually several stacks, like `network`, `workspace`, `catalogs` and `jobs`.",
        "Stacks can **depend on** each other. `workspace` depends on `network` because the workspace needs the network's subnets first. When `network` applies a change, Spacelift starts a run for every stack that depends on it, and for the stacks that depend on those, all the way **downstream**.",
        "Order matters. A stack only runs once **every stack it waits for** has finished, if that stack is running too. If `jobs` waits for `workspace` and `catalogs`, it goes after both, even though `workspace` changed first.",
        "Stacks that don't depend on the change, directly or through another stack, don't run at all. That keeps a small change small.",
    ],
    example=example('Who runs when network changes', """network       changed
  workspace     waits for network
  monitoring    waits for network
    catalogs      waits for workspace
      jobs          waits for workspace, catalogs
order: monitoring, workspace, catalogs, jobs"""),
    check=question(
        '`network` changes. `jobs` waits for `workspace` and `catalogs`, and `catalogs` waits for `workspace`. When can `jobs` run?',
        [
            'Straight after network',
            'Once workspace and catalogs have both finished',
            'At the same time as workspace',
        ],
        answer=1,
        why='A stack runs only after every stack it waits for has finished, when those are running too. workspace runs first, then catalogs, and only then jobs.',
    ),
    angle=angle(
        pattern='Downstream, then in waiting order',
        text='The big idea: when a stack changes, every stack downstream of it runs, and each one only after the stacks it waits for. Your code works in two steps. First it finds who runs: start from the changed stack, add every stack that waits for it, then every stack that waits for those, using a to-do list until nothing new turns up. Then it puts them in order: over and over, pick the stacks whose waits are all done (or not running at all), take the first by name, and add it to the order. It is like a relay race: a runner leaves only when every runner handing them the baton has arrived.',
        say='"When a stack changes I find everything [[downstream|upstream|beside it::Which stacks are affected: the ones that use this stack\'s outputs, or the ones it uses?]] of it, then order them so each stack runs only after every stack it [[waits for|feeds into|is named after::A stack can\'t start until its inputs are ready.]] has finished."',
        classic=None,
    ),
    exercise=exercise(
        title='Order the Downstream Runs',
        topic='spacelift',
        difficulty='medium',
        fn='runs_after',
        prompt="""Your function gets two things:

- `depends_on`: a dict of every stack and the stacks it waits for, like `{"network": [], "workspace": ["network"]}`.
- `changed`: the name of the stack that just applied a change.

Return the list of stacks that will run after it, in the order they run:

- A stack runs if it waits for `changed`, or for a stack that runs (all the way downstream). `changed` itself is not in the list.
- A stack goes only after every stack it waits for that is also running.
- When more than one stack is ready, the one whose name comes first in the alphabet goes first.""",
        pattern='Find everything downstream with a to-do list, then repeatedly take the first ready stack by name.',
        target='a short loop for each stack that runs',
        realworld='This is Spacelift stack dependencies: when an upstream stack applies, its dependents get tracked runs in this order, and an upstream stack can pass its outputs (like subnet ids) down as the next stack\'s inputs. A circular dependency is refused when you set it up, so the order always exists.',
        starter="""def runs_after(depends_on, changed):
    # your code here
    pass
""",
        solution="""def runs_after(depends_on, changed):
    # Step 1: who runs: everything downstream of the changed stack.
    running = set()
    todo = [changed]
    while todo:
        upstream = todo.pop()
        for stack, waits in depends_on.items():
            if upstream in waits and stack not in running:
                running.add(stack)
                todo.append(stack)

    # Step 2: in what order: a stack goes once everything it waits for (that runs) has gone.
    order = []
    while len(order) < len(running):
        ready = []
        for stack in running:
            if stack not in order and all(w not in running or w in order for w in depends_on[stack]):
                ready.append(stack)
        order.append(sorted(ready)[0])
    return order
""",
        cases=[
            case({'network': [], 'workspace': ['network'], 'monitoring': ['network'], 'catalogs': ['workspace'], 'jobs': ['workspace', 'catalogs']},
                 'network', expected=['monitoring', 'workspace', 'catalogs', 'jobs'], sample=True),
            case({'network': [], 'workspace': ['network'], 'monitoring': ['network'], 'catalogs': ['workspace'], 'jobs': ['workspace', 'catalogs']},
                 'catalogs', expected=['jobs']),
            case({'network': [], 'workspace': ['network'], 'jobs': ['workspace']}, 'jobs', expected=[]),
            case({'a': [], 'b': ['a'], 'c': ['a'], 'd': ['b', 'c']}, 'a', expected=['b', 'c', 'd']),
            case({'net': [], 'dns': [], 'app': ['net', 'dns']}, 'net', expected=['app']),
            case({'base': [], 'z-edge': ['base'], 'a-core': ['base'], 'm-app': ['a-core', 'z-edge']}, 'base', expected=['a-core', 'z-edge', 'm-app']),
        ],
        guided="""def runs_after(depends_on, changed):
    # Replace every ___ with real code, then run the tests.

    # Step 1: who runs. Start from the changed stack and keep a to-do list.
    running = set()
    todo = [changed]
    while todo:
        upstream = todo.pop()
        for stack, waits in depends_on.items():
            # Does this stack wait for the one we took off the list?
            if ___ and stack not in running:
                running.add(stack)
                todo.append(stack)

    # Step 2: the order. Each time round, take the first ready stack by name.
    order = []
    while len(order) < len(running):
        ready = []
        for stack in running:
            # Ready: not placed yet, and every stack it waits for has gone (or isn't running).
            if stack not in order and all(w not in running or ___ for w in depends_on[stack]):
                ready.append(stack)
        order.append(sorted(ready)[0])
    return order
""",
        fills=['upstream in waits', 'w in order'],
        concepts=[
            [
                'A to-do list with while',
                '`while todo:` keeps going as long as the list has something in it; `todo.pop()` takes the last item off.',
                """todo = ['a', 'b']
while todo:
    item = todo.pop()   # 'b', then 'a'""",
            ],
            [
                'A set for "seen already"',
                'A set holds each name once, so `stack not in running` stops you adding (and visiting) a stack twice.',
                """seen = set()
seen.add('a'); seen.add('a')
len(seen)   # 1""",
            ],
            [
                'all(...)',
                '`all(check for x in things)` is True when the check is True for every item, and True for an empty list.',
                """all(n > 0 for n in [1, 2, 3])   # True
all(n > 0 for n in [])          # True""",
            ],
            [
                'sorted(...)[0]',
                '`sorted(names)` puts names in alphabetical order; `[0]` takes the first.',
                "sorted(['workspace', 'monitoring'])[0]   # 'monitoring'",
            ],
        ],
        byhand='network changed. workspace and monitoring wait for network, so they run; catalogs waits for workspace and jobs for workspace and catalogs, so they run too. Order: monitoring and workspace are both ready; monitoring comes first by name. Then workspace. Then catalogs (its wait, workspace, has gone). Then jobs. Return [monitoring, workspace, catalogs, jobs].',
        why='Each running stack is found once, and each time round the order loop checks the stacks still waiting.',
        gotchas=[
            [
                'Running a stack before its inputs exist',
                'If jobs ran before catalogs, it would read the old catalog names. Waiting for every upstream stack that runs is what makes outputs safe to use.',
            ],
            [
                'One giant stack',
                'Putting everything in one stack means every small change plans the whole platform. Split by how often things change and who owns them, and link them with dependencies.',
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
        say='"I put the protected types in a set, then flag every change that would [[delete|update|read::The dangerous change is the one you can\'t undo.]] one of them, [[replacements|tags|comments::Destroying and re-creating something also loses it.]] included. No messages means the run can [[go ahead|stop|wait::An empty list of problems is a pass.]]."',
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
        say='"I check every change against each rule [[separately|once in total|only if the first passes::Each rule gets its own look at every change.]] and report every problem, not just the [[first|last|biggest::Stopping early would hide the rest.]]. One change can break both rules and get [[both|one|no::Rules are checked independently.]] messages."',
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

planned(MODULE, 'run_states', "A run's life: queued, planning, unconfirmed, applying", 'What each run state means, and when a person has to confirm.')
planned(MODULE, 'drift_detection', 'Drift detection', 'Finding changes made outside Terraform before they surprise the next apply.')
planned(MODULE, 'contexts_secrets', 'Contexts and secrets', 'Sharing settings and credentials between stacks without copying them.')
planned(MODULE, 'policy_testing', 'Testing a policy before it blocks', 'Rolling out a new rule as a warning, and testing it against real plans.')
