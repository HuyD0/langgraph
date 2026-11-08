"""Make and test a change: put a change where the checks can see it, then prove it works with the
cheapest check that can, before Spacelift ever plans it. All names are invented."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, fix, lesson, module, practice, question, stack, source

MODULE = module('changes', 'Make and test a change',
                'Make a change the checks can see, then prove it works before it costs anything.',
                setting=PLATFORM_SETTING)


STACK_VARS = """# admin repo: stacks/sales-dev.yml
vars:
  warehouse_size: Small
  auto_stop_minute: 10"""

VARIABLES_TF = """# runbook: Service/variables.tf
variable "warehouse_size" {
  type    = string
  default = "2X-Small"
}

variable "auto_stop_minutes" {
  type    = number
  default = 120
}"""


lesson(MODULE, 'unchecked_fields',
    title='Why did my typo change something else?',
    checked='2026-11-08',
    sources=[source('Input variables: assigning values', 'https://developer.hashicorp.com/terraform/language/values/variables'), source('Spacelift environment', 'https://docs.spacelift.io/concepts/configuration/environment')],
    learn=[
        "Not every setting passes the Pydantic check. A team's YAML in the config repo does. But each Spacelift stack also has its own **settings**, kept as YAML in the admin repo, and they reach Terraform as **environment variables**: `TF_VAR_` followed by the variable's name. `TF_VAR_auto_stop_minutes=10` sets `var.auto_stop_minutes`.",
        "Here is the trap. Terraform **ignores** an environment variable that doesn't match a `variable` block it knows. No error, no warning. So a typo like `auto_stop_minute` is thrown away, and the variable quietly uses its **default**, the value its `variable` block says to use when nobody sets it.",
        "Terraform is stricter elsewhere: an unknown name in a `.tfvars` file gets a warning, and on the command line with `-var` it is an error. Environment variables are the one place a typo makes no sound at all.",
        "You usually find out from the plan: it changes something you didn't mean to touch, because the default isn't what you wanted. The fix is a check of your own: compare every key under `vars:` with the variables the runbook declares, and stop on any name that doesn't match.",
    ],
    example=example('One letter missing, and a default takes over', """# admin repo: stacks/sales-dev.yml
vars:
  warehouse_size: Small
  auto_stop_minute: 10        # the variable is auto_stop_minutes

# what Spacelift sets for the run
TF_VAR_warehouse_size=Small
TF_VAR_auto_stop_minute=10    # no variable by that name: ignored

# runbook: Service/variables.tf
variable "auto_stop_minutes" { default = 120 }

# the plan
~ databricks_sql_endpoint.sales
    auto_stop_mins: 10 -> 120"""),
    check=question(
        'A stack sets `TF_VAR_max_worker = 4`, but the runbook\'s variable is `max_workers`, with a default of 2. What does Terraform use for `max_workers`?',
        [
            '4: it picks the closest name',
            '2: the setting is ignored',
            'Nothing: the run stops',
        ],
        answer=1,
        why='Terraform ignores an environment variable with no matching variable block, without a warning. So `max_workers` keeps its default, 2, and nobody is told.',
    ),
    angle=angle(
        pattern='Compare every key with what is declared',
        text='The big idea: Terraform throws away an environment variable whose name it doesn\'t know, so a misspelled stack setting fails silently. Your code is the check Terraform doesn\'t do: it walks through the keys under vars: and keeps every one that isn\'t among the declared variable names, in the order they were written. An empty answer means every setting will land. It is like a guest list at the door: a name that isn\'t on the list doesn\'t get in, and nobody tells the person waiting outside.',
        say="\"Terraform [[ignores|rejects|renames::No error, no warning: it just throws it away.]] an environment variable it has no variable for, so a typo falls back to the [[default|last value|plan::What the variable block uses when nobody sets it.]]. That's why I check every key against the [[declared|planned|applied::The variable blocks the runbook has.]] names.\"",
        classic=None,
    ),
    stack=stack('Spacelift: how a stack setting reaches Terraform', """# admin repo: one environment variable per setting
resource "spacelift_environment_variable" "vars" {
  for_each   = local.stack.vars
  stack_id   = spacelift_stack.service.id
  name       = "TF_VAR_${each.key}"
  value      = tostring(each.value)
  write_only = false
}"""),
    exercise=exercise(
        title='Find the Settings That Will Be Ignored',
        topic='iac-review',
        difficulty='easy',
        fn='unknown_keys',
        prompt="""Your function gets two lists:

- `keys`: the setting names under a stack's `vars:`, in the order they were written, like `["warehouse_size", "auto_stop_minute"]`.
- `declared`: the variable names the runbook declares, like `["warehouse_size", "auto_stop_minutes"]`.

Return a list of every key that is **not** in `declared`, in the same order as `keys`. These are the settings Terraform will quietly ignore. An empty list means every setting will land.""",
        pattern='Filter: keep the items that fail a test, in their original order.',
        target='one pass over the keys',
        realworld="This is the check a platform team adds to the admin repo's pull requests, because Terraform won't complain about an environment variable it doesn't know. It turns a silent default into a red build before anything is planned.",
        practice=practice(
            intro='Follow a stack setting from the admin repo to the plan, and catch the one Terraform throws away.',
            explain='Terraform ignores an environment variable it has no variable block for, so a misspelled stack setting makes no sound: the variable keeps its default and the plan changes something you never meant to touch. You matched each setting against the declared names, traced the surprise in the plan back to the typo, and fixed the name.',
            pattern='Match each setting to a declared name',
            realworld='When you review a pull request that changes stack settings, you check every name against the runbook\'s variables before you look at the plan. When a plan changes something nobody touched, a misspelled setting falling back to its default is one of the first things you look for.',
            asks=[
                ask('Which setting will Terraform throw away?', ['warehouse_size', 'auto_stop_minute', 'Neither of them'], answer=1,
                    evidence=evidence('code', title='The stack settings and the runbook\'s variables', text=STACK_VARS + "\n\n" + VARIABLES_TF),
                    clue='Compare each name under vars: letter by letter with the variable blocks.',
                    why='The variable is `auto_stop_minutes`, with an s. `TF_VAR_auto_stop_minute` matches nothing, so Terraform ignores it without a word.',
                    wrong=['warehouse_size matches a variable block exactly.', None, 'Look again at the last letter of each name.']),
                ask('So what auto-stop will the warehouse get?', ['10 minutes', '120 minutes', 'The run fails'], answer=1,
                    evidence=evidence('code', title='runbook: Service/variables.tf', text='variable "auto_stop_minutes" {\n  type    = number\n  default = 120\n}'),
                    clue='Nobody set this variable. What does the block say to use then?',
                    why='The setting was ignored, so the variable uses its default: 120 minutes. The warehouse now idles six times longer than the team asked for.',
                    wrong=['10 was the value in the YAML, but it never reached this variable.', None, 'Terraform doesn\'t stop on an unknown environment variable.']),
                ask('Which change in the plan is the typo\'s doing?', [], answer=1, pick=True,
                    evidence=evidence('plan', title='Stack sales-service-dev · proposed',
                        summary=[['1', 'to add', 'a'], ['1', 'to change', ''], ['0', 'to destroy', 'd']],
                        changes=[
                            {'sym': '+', 'address': 'databricks_schema.sales_raw', 'note': 'new schema the team asked for'},
                            {'sym': '~', 'address': 'databricks_sql_endpoint.sales', 'note': 'auto_stop_mins 10 → 120'},
                        ]),
                    clue='Look for a value going back to the default the variable block names.',
                    why='The warehouse had 10 minutes, set by hand or by an older run. With the setting ignored, Terraform wants the default, 120. That row is a change nobody asked for.',
                    wrong=['The team asked for this schema: it\'s the change they meant.', None]),
                fix('Your new check flags the stack\'s settings. Fix the file so every setting lands.',
                    file='stacks/sales-dev.yml',
                    start="""vars:
  warehouse_size: Small
  auto_stop_minute: 10
""",
                    answer="""vars:
  warehouse_size: Small
  auto_stop_minutes: 10
""",
                    rules={'path': 'vars', 'required': ['warehouse_size', 'auto_stop_minutes'], 'allowed': ['warehouse_size', 'auto_stop_minutes'],
                           'types': {'warehouse_size': 'str', 'auto_stop_minutes': 'int'}},
                    goal=[{'field': 'auto_stop_minutes', 'equals': 10, 'message': 'The team asked for 10 minutes of auto-stop.'}],
                    clue='One name is a letter short of the variable in variables.tf.',
                    why='With the name spelled like the variable block, `TF_VAR_auto_stop_minutes` lands and the plan stops trying to go back to 120.'),
                ask('Why didn\'t the run stop with an error?', ['Unknown TF_VAR_ names are skipped', 'Proposed runs hide their errors', 'Pydantic fixed the spelling'], answer=0,
                    alone=True,
                    clue='Think about where stack settings come from, and which check they pass through on the way.',
                    why='Stack settings never pass the Pydantic check, and Terraform skips an environment variable it doesn\'t know. Nothing in the path says a word, which is why the team adds its own check.',
                    wrong=[None, 'Proposed runs show errors like any other run.', 'Pydantic checks the config repo\'s team files, not stack settings.']),
            ],
        ),
        starter="""def unknown_keys(keys, declared):
    # your code here
    pass
""",
        solution="""def unknown_keys(keys, declared):
    known = set(declared)
    return [k for k in keys if k not in known]
""",
        cases=[
            case(['warehouse_size', 'auto_stop_minute'], ['warehouse_size', 'auto_stop_minutes'], expected=['auto_stop_minute'], sample=True),
            case(['warehouse_size', 'auto_stop_minutes'], ['warehouse_size', 'auto_stop_minutes'], expected=[]),
            case([], ['warehouse_size'], expected=[]),
            case(['max_worker', 'min_worker', 'node_type'], ['max_workers', 'min_workers', 'node_type'], expected=['max_worker', 'min_worker']),
            case(['Region'], ['region'], expected=['Region']),
            case(['region', 'regoin', 'region'], ['region'], expected=['regoin']),
        ],
        guided="""def unknown_keys(keys, declared):
    # Replace every ___ with real code, then run the tests.
    known = set(declared)        # quick to ask "is this name in it?"
    result = []
    for k in keys:
        if ___:
            result.append(k)
    return ___
""",
        fills=['k not in known', 'result'],
        concepts=[
            [
                'not in',
                '`x not in things` is `True` when `x` isn\'t one of them. It reads like the question you are asking.',
                """"regoin" not in {"region"}   # True""",
            ],
            [
                'A set for quick lookups',
                '`set(names)` keeps each name once and answers "is it in here?" straight away, however many names there are.',
                """known = set(["a", "b"])
"a" in known   # True""",
            ],
        ],
        byhand='The sample: warehouse_size is declared, so it is skipped. auto_stop_minute is not (the variable has an s at the end), so it goes in the list. Result: ["auto_stop_minute"].',
        why='One pass over the keys, each a quick lookup in the set.',
        gotchas=[
            [
                'Upper and lower case count',
                'Terraform names are case-sensitive: `Region` and `region` are different variables, so `TF_VAR_Region` is ignored too.',
            ],
            [
                'The plan is where it shows',
                'Nothing fails. The only sign is a plan that changes a value nobody touched, back to a default.',
            ],
        ],
    ),
)


lesson(MODULE, 'plan_saw_change',
    title='Is this plan showing my change?',
    checked='2026-11-08',
    sources=[source('Stack settings: project root and branch', 'https://docs.spacelift.io/concepts/stack/stack-settings'), source('Create a Terraform plan', 'https://developer.hashicorp.com/terraform/tutorials/cli/plan'), source('Module sources: selecting a revision', 'https://developer.hashicorp.com/terraform/language/modules/sources')],
    learn=[
        "Before you open a plan, say what you expect: \"one schema added, nothing else.\" Then read it. A plan that matches is good news. A plan **missing your change**, or showing **changes you didn't make**, is telling you something.",
        "When your change is missing, ask what the run actually read. Four usual answers. The run used **another commit** than yours. Your file is **outside the stack's project root**, the folder the stack watches, so your push never started it. The stack uses a module **pinned to an older version**, so your module change isn't in it yet. Or the value is **set somewhere else**, like a stack setting, that your pull request didn't touch.",
        "Changes you didn't make have their own story. \"Objects have changed outside of Terraform\" is a **note**: Terraform read the real resources and saw someone changed something by hand. It only becomes a change if the plan's own list proposes setting it back. The bottom line, \"Plan: 1 to add, 0 to change, 0 to destroy\", is what will actually happen.",
        "Never confirm a plan that doesn't match what you predicted until you can say why.",
    ],
    example=example('Predict first, then read', """You expect:   + databricks_schema.sales_raw
                nothing else

The plan:     No changes. Your infrastructure
              matches the configuration.

Ask what the run read:
  commit         a1b2c3d on main   (yours is 9f8e7d6)
  project root   service/          (you changed foundation/)
  module         catalog ?ref=v1.4.0  (your fix is in v1.5.0)"""),
    check=question(
        'You fixed a bug in the catalog module and released v1.5.0. The DEV plan shows no changes. The runbook says `?ref=v1.4.0`. Why is your fix missing?',
        [
            'The plan is cached from yesterday',
            'The runbook still uses v1.4.0',
            'Small fixes never show in plans',
        ],
        answer=1,
        why='A module pinned with ?ref=v1.4.0 stays on v1.4.0 until someone bumps the version in the runbook. Releasing v1.5.0 changes nothing on its own.',
    ),
    angle=angle(
        pattern='Predict, then find what the run read',
        text='The big idea: when a plan doesn\'t show your change, the run read something other than what you think. Your code asks the questions in the order a reviewer does: did it use your commit, does the stack watch the folder you changed, is the module at the version with your change, and is the value set where you changed it. The first "no" is the answer. It is like a parcel that never arrived: check the address, then the postcode, then whether it was ever posted.',
        say="\"Before I read a plan I [[predict|approve|apply::Say what you expect to see first.]] it. If my change isn't there, I ask what the run actually [[read|deleted|locked::Which commit, folder, version and values it used.]]: the commit, the project root and the module [[version|owner|size::The ?ref= at the end of the source.]].\"",
        classic=None,
    ),
    exercise=exercise(
        title='Why Is My Change Missing?',
        topic='plan-reading',
        difficulty='easy',
        fn='why_missing',
        prompt="""Your function gets `run`, a dict about a run that doesn't show your change:

- `"your_commit"`: `True` if the run used your commit.
- `"watched"`: `True` if the file you changed is inside the stack's project root.
- `"module_has_change"`: `True` if the module version the runbook pins includes your change (also `True` when you didn't change a module).
- `"set_here"`: `True` if the value is set in the file you changed, not somewhere else.

Return the first reason that fits, in this order:

1. not `your_commit` -> `"another commit"`
2. not `watched` -> `"not watched"`
3. not `module_has_change` -> `"old module version"`
4. not `set_here` -> `"set elsewhere"`
5. otherwise -> `"read the plan again"`""",
        pattern='Ask the questions in a fixed order and return at the first one that fits.',
        target='a few checks, no loops',
        realworld="This is the order to check when a Spacelift plan doesn't show your change. Most of the time it's the first or second: the run used main's commit, or the stack doesn't watch the folder you changed.",
        practice=practice(
            intro='Your change is missing from the plan. Find out what the run really read.',
            explain='A plan shows what the run read, not what you meant. You predicted the plan first, and when your change was missing you checked the run\'s commit, the folder the stack watches and the module version it pins. Then you read the bottom line instead of the note above it.',
            pattern='Predict, then check what it read',
            realworld='When a team says "I merged it but the plan shows nothing", you open the run and check its commit, the stack\'s project root and the module version before you suspect anything else. When a plan shows changes nobody made, you trust its bottom line and ask where each extra change came from before anyone confirms.',
            asks=[
                ask('Which commit did this run plan?', ['Your commit, 9f8e7d6', 'Main\'s commit, a1b2c3d', 'Both of them'], answer=1,
                    evidence=evidence('code', title='Run header · stack sales-service-dev', text="""Run      01J8XK  PROPOSED  finished
Branch   main
Commit   a1b2c3d  "Bump warehouse size"

Your pull request: branch add-sales-raw, commit 9f8e7d6"""),
                    clue='Read the Commit line, then compare it with yours.',
                    why='The run planned main at a1b2c3d, not your branch. Find the run for your pull request\'s commit before you read any plan.',
                    wrong=['Your commit is 9f8e7d6. Is that the one in the header?', None, 'A run plans exactly one commit.']),
                ask('Why didn\'t your push start the service stack?', ['The file is outside its project root', 'The service stack is locked right now', 'The changed file has a typo in it'], answer=0,
                    evidence=evidence('code', title='Stack settings and your change', text="""Stack            sales-service-dev
Project root     service/
Branch           main

Your pull request changes:
  foundation/locals.tf"""),
                    clue='Compare the folder the stack watches with the folder you changed.',
                    why='A stack only starts for changes inside its project root, plus any extra paths it is told to watch. foundation/ isn\'t one, so the service stack never ran.',
                    wrong=[None, 'A locked stack still queues a run. This one never started.', 'A typo would make the run fail, not stop it from starting.']),
                ask('Will the DEV plan show your module fix?', ['Yes, from tonight onwards', 'No, it still uses v1.4.0', 'Only in PROD at first'], answer=1,
                    evidence=evidence('code', title='runbook: Service/catalog.tf', text="""module "catalog" {
  source = "git::https://git.example.com/modules/catalog.git?ref=v1.4.0"
  name   = "sales"
}

# your fix was released as v1.5.0"""),
                    clue='Look at the end of the source line.',
                    why='?ref=v1.4.0 pins the module. Your fix reaches DEV only when a pull request changes it to v1.5.0, and then UAT and PROD one at a time.',
                    wrong=['Nothing changes tonight unless the version in the runbook changes.', None, 'PROD follows DEV. Nothing reaches PROD first.']),
                ask('How many changes will this plan make?', ['One: add the schema', 'Two: the schema and the tags', 'None'], answer=0,
                    evidence=evidence('code', title='Plan output', text="""Note: Objects have changed outside of Terraform
  # azurerm_resource_group.sales has changed
  ~ tags = { + "owner" = "someone" }

Terraform will perform the following actions:
  + databricks_schema.sales_raw

Plan: 1 to add, 0 to change, 0 to destroy."""),
                    clue='Which part of the output is a list of actions, and which is only telling you something?',
                    why='The note says someone changed the tags by hand. The plan doesn\'t list setting them back, and the bottom line says 1 to add, 0 to change. Worth telling the platform owner, but it isn\'t your change.',
                    wrong=[None, 'The tags are in the note, not in the list of actions.', 'The bottom line says 1 to add.']),
                ask('The plan matches what you predicted, plus one cluster change you didn\'t make. What now?', ['Approve it: most of it is yours', 'Find where the extra change came from', 'Run it again until it goes away'], answer=1,
                    alone=True,
                    clue='Confirming applies every line, not just yours.',
                    why='Confirming applies the whole plan, including the change nobody can explain. Find its source first: drift, a default, or someone else\'s merge.',
                    wrong=['Approving applies every line, including the one nobody can explain.', None, 'Running again doesn\'t explain it. The same change will come back.']),
            ],
        ),
        starter="""def why_missing(run):
    # your code here
    pass
""",
        solution="""def why_missing(run):
    if not run["your_commit"]:
        return "another commit"
    if not run["watched"]:
        return "not watched"
    if not run["module_has_change"]:
        return "old module version"
    if not run["set_here"]:
        return "set elsewhere"
    return "read the plan again"
""",
        cases=[
            case({'your_commit': False, 'watched': True, 'module_has_change': True, 'set_here': True}, expected='another commit', sample=True),
            case({'your_commit': True, 'watched': False, 'module_has_change': True, 'set_here': True}, expected='not watched'),
            case({'your_commit': True, 'watched': True, 'module_has_change': False, 'set_here': True}, expected='old module version'),
            case({'your_commit': True, 'watched': True, 'module_has_change': True, 'set_here': False}, expected='set elsewhere'),
            case({'your_commit': True, 'watched': True, 'module_has_change': True, 'set_here': True}, expected='read the plan again'),
            case({'your_commit': False, 'watched': False, 'module_has_change': False, 'set_here': False}, expected='another commit'),
        ],
        guided="""def why_missing(run):
    # Replace every ___ with real code, then run the tests.
    if not run["your_commit"]:
        return "another commit"
    if not run["watched"]:
        return ___
    if ___:
        return "old module version"
    if not run["set_here"]:
        return "set elsewhere"
    return "read the plan again"
""",
        fills=['"not watched"', 'not run["module_has_change"]'],
        concepts=[
            [
                'not',
                '`not x` turns `True` into `False` and back. `if not run["watched"]:` reads "if it isn\'t watched".',
                """not True    # False
not False   # True""",
            ],
            [
                'Return early',
                'A function stops at its first `return`, so the order of the questions decides which reason wins.',
                """def first(a, b):
    if a:
        return "a"
    return "b\"""",
            ],
        ],
        byhand='The sample: your_commit is False, so the first question already fits: "another commit". The rest are never asked.',
        why='At most four checks, each looking at one field.',
        gotchas=[
            [
                'Main is not your branch',
                'A tracked run plans the stack\'s branch. Your pull request gets its own proposed run, on your commit.',
            ],
            [
                'A note is not a change',
                '"Objects have changed outside of Terraform" only tells you what it read. The list of actions and the bottom line say what will happen.',
            ],
        ],
    ),
)


lesson(MODULE, 'cheapest_check_first',
    title='Which check catches this first?',
    checked='2026-11-08',
    sources=[source('terraform validate', 'https://developer.hashicorp.com/terraform/cli/commands/validate'), source('terraform fmt', 'https://developer.hashicorp.com/terraform/cli/commands/fmt'), source('Tests', 'https://developer.hashicorp.com/terraform/language/tests'), source('Resolve errors for storage account names', 'https://learn.microsoft.com/azure/azure-resource-manager/troubleshooting/error-storage-account-name')],
    learn=[
        "There are four kinds of check, from cheapest to dearest. **Static checks** come first: `terraform fmt -check` (is it laid out the standard way?), `terraform validate` (are the names and types right?) and a linter like TFLint. They take seconds and never call Azure or Databricks.",
        "**Tests** come next. `terraform test` runs `.tftest.hcl` files. With a **mock provider**, a pretend provider that makes up the values Azure would send back, a test checks your own logic, like names, counts and rules, without creating anything or needing credentials.",
        "**The plan** reads what really exists and shows what would change. It needs credentials and real state, but changes nothing. **Apply, then plan again** is the only check that really creates things, and the second plan should say \"No changes\". If it doesn't, something keeps changing back.",
        "Each check sees things the cheaper ones can't. A pretend provider doesn't know Azure's rules: a storage account name someone else already has (`StorageAccountAlreadyTaken`) passes validate, the tests and the plan, and only fails at apply. So catch all you can early, and know which problems only the later checks can find.",
    ],
    example=example('What each check can see', """fmt -check, validate, lint   seconds, no cloud
  a misspelled argument, a wrong type, untidy layout
tests with a mock provider   seconds, no cloud
  a name built wrong, a rule that lets 5 through
plan                         minutes, real state
  a schema someone deleted by hand
apply, then plan again       real changes
  a name already taken in Azure
  a value that keeps changing back"""),
    check=question(
        'A resource uses `var.enviroment`, but the variable is declared as `environment`. Which check finds it first?',
        [
            'terraform validate',
            'The plan',
            'The apply',
        ],
        answer=0,
        why='A reference to a variable that doesn\'t exist is an internal mistake, and validate finds those in seconds without calling Azure.',
    ),
    angle=angle(
        pattern='The cheapest check that can see it',
        text='The big idea: every problem has a cheapest check that can find it, and you want to meet it there, not at apply. Your code asks the checks in order, cheapest first: a wrong name or type is static, a logic mistake is a test, anything that depends on what really exists is the plan, and anything only Azure decides when creating is the apply. It is like proofreading: a spell-checker finds typos instantly, but only the printer tells you the paper ran out.',
        say="\"I run the cheap checks first: [[validate|apply|import::It checks names and types without calling Azure.]] and tests with a pretend provider. Some problems only Azure knows, like a name that's already [[taken|valid|formatted::Someone else in Azure already has it.]], so those wait for the apply.\"",
        classic=None,
    ),
    stack=stack('A pull request check, cheapest first', """terraform fmt -check -recursive
terraform init -backend=false
terraform validate
tflint
terraform test            # mock providers: no cloud
# the Spacelift proposed run is the plan"""),
    exercise=exercise(
        title='Find the First Check That Catches It',
        topic='testing',
        difficulty='easy',
        fn='first_check',
        prompt="""Your function gets `bug`, a dict about a problem in a change:

- `"wrong_name_or_type"`: `True` if it's a misspelled name, a missing argument or a wrong type.
- `"logic"`: `True` if it's your own rule or name-building doing the wrong thing.
- `"needs_real_state"`: `True` if it depends on what really exists today.

Return the cheapest check that finds it, asking in this order:

1. `wrong_name_or_type` -> `"static"`
2. `logic` -> `"test"`
3. `needs_real_state` -> `"plan"`
4. otherwise -> `"apply"`""",
        pattern='Ask the questions in a fixed order, cheapest first, and return at the first one that fits.',
        target='a few checks, no loops',
        realworld="This is how a platform team orders its pull request checks: fmt, validate and lint first, then terraform test with mock providers, and only then the Spacelift plan. Each problem is found at the cheapest point that can see it.",
        practice=practice(
            intro='For each problem, pick the cheapest check that would catch it.',
            explain='Every problem has a cheapest check that can find it. You placed each one: names and types at the static checks, your own rules at the tests, anything about what really exists at the plan, and what only Azure decides at the apply, plus the second plan that shows whether a change settled.',
            pattern='Cheapest first, then what it can\'t see',
            realworld='When you set up checks on a repo, you put fmt, validate, lint and tests before the Spacelift plan. When something fails late, at the apply, you ask whether a cheaper check could have caught it, and add one if it could.',
            asks=[
                ask('Which check catches this first?', ['terraform validate', 'A test with mocks', 'The Spacelift plan'], answer=0,
                    evidence=evidence('code', title='runbook: Service/schemas.tf', text="""resource "databricks_schema" "raw" {
  catalog_nme = "sales"
  name        = "raw"
}"""),
                    clue='Is this about your logic, about Azure, or about a name Terraform doesn\'t know?',
                    why='catalog_nme isn\'t an argument databricks_schema has. validate knows every argument\'s name and type, so it fails in seconds.',
                    wrong=[None, 'A test would fail too, but a cheaper check gets there first.', 'The plan would fail too, after logging in and reading state. Something cheaper finds it.']),
                ask('The warehouse name should be lower case, but comes out as `SALES_daily`. Which check catches this first?', ['terraform validate', 'A mock test', 'The apply'], answer=1,
                    evidence=evidence('code', title='runbook: Service/warehouse.tf', text="""locals {
  warehouse_name = "${var.code}_${var.name}"   # forgot lower()
}"""),
                    clue='The code is valid. It just builds the wrong name. Which check tests your own rules?',
                    why='Every name and type here is valid, so validate passes. A test with a pretend provider can assert the name is "sales_daily" and fail, with no cloud.',
                    wrong=['validate only checks names and types, and these are fine.', None, 'Databricks would accept SALES_daily. Nothing at apply would complain.']),
                ask('Someone deleted the `sales_raw` schema by hand yesterday. Which check notices first?', ['The plan', 'terraform validate', 'A mock test'], answer=0,
                    alone=True,
                    clue='Which check is the first to look at what really exists?',
                    why='Only the plan reads the real workspace. It sees the schema is gone and plans to create it again.',
                    wrong=[None, 'validate never calls Databricks, so it can\'t know.', 'A mock test uses a pretend provider. It can\'t see the real workspace.']),
                ask('Which check could have caught this?', ['Only the apply', 'terraform validate', 'A mock test'], answer=0,
                    evidence=evidence('code', title='Apply log', text="""azurerm_storage_account.lake: Creating...
Error: creating Storage Account "stsalesdev":
  StorageAccountAlreadyTaken: The storage account
  named stsalesdev is already taken."""),
                    clue='Storage account names are shared across all of Azure. Which check asks Azure to create one?',
                    why='Whether a name is free is only decided when Azure tries to create the account. Use a name with a unique part, like a short code from the subscription, so it can\'t clash.',
                    wrong=[None, 'The name is well formed, so validate is happy.', 'A pretend provider has no idea which names other people use.']),
                ask('After the apply you plan again. What does this second plan tell you?', ['The change has settled', 'Something keeps changing back', 'The apply failed halfway'], answer=1,
                    evidence=evidence('plan', title='Stack sales-service-dev · second plan',
                        summary=[['0', 'to add', 'a'], ['1', 'to change', ''], ['0', 'to destroy', 'd']],
                        changes=[
                            {'sym': '~', 'address': 'databricks_permissions.team_folder', 'note': 'grp-sales-dev-owners CAN_EDIT → CAN_MANAGE'},
                        ]),
                    clue='Right after an apply, what should a plan say?',
                    why='Right after an apply the plan should say No changes. A change that comes back every time means something fights Terraform, like a group listed twice or a setting changed by a job.',
                    wrong=['A settled change gives No changes on the next plan.', None, 'The apply finished. This is the plan after it.']),
            ],
        ),
        starter="""def first_check(bug):
    # your code here
    pass
""",
        solution="""def first_check(bug):
    if bug["wrong_name_or_type"]:
        return "static"
    if bug["logic"]:
        return "test"
    if bug["needs_real_state"]:
        return "plan"
    return "apply"
""",
        cases=[
            case({'wrong_name_or_type': True, 'logic': False, 'needs_real_state': False}, expected='static', sample=True),
            case({'wrong_name_or_type': False, 'logic': True, 'needs_real_state': False}, expected='test'),
            case({'wrong_name_or_type': False, 'logic': False, 'needs_real_state': True}, expected='plan'),
            case({'wrong_name_or_type': False, 'logic': False, 'needs_real_state': False}, expected='apply'),
            case({'wrong_name_or_type': True, 'logic': True, 'needs_real_state': True}, expected='static'),
            case({'wrong_name_or_type': False, 'logic': True, 'needs_real_state': True}, expected='test'),
        ],
        guided="""def first_check(bug):
    # Replace every ___ with real code, then run the tests.
    # Cheapest first.
    if bug["wrong_name_or_type"]:
        return "static"
    if bug["logic"]:
        return ___
    if ___:
        return "plan"
    return "apply"
""",
        fills=['"test"', 'bug["needs_real_state"]'],
        concepts=[
            [
                'Order matters',
                'When more than one question fits, the first `if` that is true wins. Putting the cheapest check first makes it win.',
                """if cheap:
    return "static"
if dear:
    return "apply\"""",
            ],
            [
                'A dict of yes/no answers',
                'Each value is `True` or `False`, so `if bug["logic"]:` reads like the question itself.',
                """bug = {"logic": True}
if bug["logic"]:
    print("test it")""",
            ],
        ],
        byhand='The sample: wrong_name_or_type is True, so the first question fits and the answer is "static". The other checks would find it too, just later.',
        why='At most three checks, each looking at one field.',
        gotchas=[
            [
                'validate needs init',
                '`terraform validate` needs the providers and modules installed. `terraform init -backend=false` does that without touching any state.',
            ],
            [
                'Tests create real things by default',
                'A run block applies unless you set `command = plan`. Use mock providers so a test never needs the cloud.',
            ],
        ],
    ),
)


lesson(MODULE, 'validation_rules',
    title='Stop a bad value at the door',
    checked='2026-11-08',
    sources=[source('Custom conditions', 'https://developer.hashicorp.com/terraform/language/expressions/custom-conditions'), source('Terraform 1.9 enhances input variable validations', 'https://www.hashicorp.com/blog/terraform-1-9-enhances-input-variable-validations'), source('Input variables', 'https://developer.hashicorp.com/terraform/language/values/variables')],
    learn=[
        "A `validation` block inside a `variable` stops a bad value **before Terraform plans anything**. It has a `condition` that must be true and an `error_message` shown when it isn't.",
        "Write the message for the person who will see it, often someone on a product team. Say what's wrong and what's allowed: \"auto_stop_minutes must be between 10 and 60.\" tells them the fix. \"Invalid value.\" sends them digging. Terraform asks for full sentences.",
        "A rule that compares two variables, like \"max_workers must be at least min_workers\", needs **Terraform 1.9** or later. Before 1.9, a validation could only look at its own variable, and older versions stop with an `Invalid reference` error. On those versions, put the rule in a **precondition** instead: a `condition` and `error_message` inside a resource's `lifecycle` block, checked when Terraform plans.",
        "A rule nobody has seen say no might never say no. The next lesson tests that it does.",
    ],
    example=example('A rule with a helpful message', """variable "auto_stop_minutes" {
  type    = number
  default = 20

  validation {
    condition     = var.auto_stop_minutes >= 10 && var.auto_stop_minutes <= 60
    error_message = "auto_stop_minutes must be between 10 and 60."
  }
}

# a team sets auto_stop_minutes = 5:
# Error: Invalid value for variable
#   auto_stop_minutes must be between 10 and 60."""),
    check=question(
        'A team sets `auto_stop_minutes = 5`, and the variable has the rule above. When does the run stop?',
        [
            'Before the plan, at the rule',
            'At apply, when Databricks says no',
            'Never: 5 is used as given',
        ],
        answer=0,
        why='Variable validations are checked first, before Terraform plans anything. The run stops straight away with the rule\'s error message.',
    ),
    angle=angle(
        pattern='Say no early, and say why',
        text='The big idea: a validation stops a bad value at the door, and its message tells people how to fix it. Your code does what the rule does: if the value is outside the allowed range it gives back the message, built from the variable\'s name and the limits, and if it\'s fine it gives back nothing. It is like a form that says "Postcode must have 6 characters" next to the box, instead of failing after you post it.',
        say="\"A [[validation|output|provider::A block inside the variable.]] block stops a bad value before the plan. Its error message says what's [[allowed|deleted|planned::The values that would pass.]], so nobody has to dig through the runbook to find out.\"",
        classic=None,
    ),
    stack=stack('Older Terraform: the same rule as a precondition', """resource "databricks_cluster" "this" {
  # ...
  lifecycle {
    precondition {
      condition     = var.max_workers >= var.min_workers
      error_message = "max_workers must be at least min_workers."
    }
  }
}"""),
    exercise=exercise(
        title='Write the Rule and Its Message',
        topic='testing',
        difficulty='easy',
        fn='check_range',
        prompt="""Your function gets a variable's `name`, its `value`, and the allowed range `low` to `high` (both allowed).

- If `value` is between `low` and `high`, return `None`: the value passes.
- Otherwise return the error message, exactly like this: `"auto_stop_minutes must be between 10 and 60."`, using the name and the limits you were given.""",
        pattern='Check a condition, and build a helpful message when it fails.',
        target='one comparison',
        realworld="This is a validation block written as a function. The message format matters: a product team reads it in a failed Spacelift run, and it should tell them the fix without opening the runbook.",
        practice=practice(
            intro='Read the rules on a few variables, and decide what passes, what helps, and what to do on an older Terraform.',
            explain='A validation stops a bad value before anything is planned, and a good message says what is allowed. You checked values against a rule, picked the message a product team could act on, and moved a rule that compares two variables into a precondition for an older Terraform.',
            pattern='Stop it early, say the fix',
            realworld='When you add a setting that teams can change, you add a validation with a message that names the allowed values. When a team asks why their run failed before the plan, you read them the message and point at the allowed values, not the runbook.',
            asks=[
                ask('Which value passes this rule?', ['5', '45', '90'], answer=1,
                    evidence=evidence('code', title='runbook: Service/variables.tf', text="""variable "auto_stop_minutes" {
  type = number
  validation {
    condition     = var.auto_stop_minutes >= 10 && var.auto_stop_minutes <= 60
    error_message = "auto_stop_minutes must be between 10 and 60."
  }
}"""),
                    clue='Both parts of the condition must be true.',
                    why='45 is at least 10 and at most 60, so both parts are true.',
                    wrong=['5 is below 10.', None, '90 is above 60.']),
                ask('A product team\'s run fails on one of these rules. Which message helps them most?', ['Message A', 'Message B'], answer=1,
                    evidence=evidence('code', title='Two ways to write the same rule', text="""# A
error_message = "Invalid value."

# B
error_message = "max_workers must be 8 or fewer in DEV. Ask the platform team for more."
"""),
                    clue='Which one could they act on without opening the runbook?',
                    why='B says what is allowed and what to do next. A sends them digging through Terraform they don\'t own.',
                    wrong=['"Invalid value" doesn\'t say which value, or what would be valid.', None]),
                ask('Your Terraform is 1.5. What\'s the fix?', ['Move it into a precondition', 'Delete the rule for now', 'Rename both of the variables'], answer=0,
                    evidence=evidence('code', title='The run on Terraform 1.5', text="""variable "min_workers" {
  type = number
  validation {
    condition     = var.min_workers <= var.max_workers
    error_message = "min_workers must not be more than max_workers."
  }
}

Error: Invalid reference in variable validation"""),
                    clue='Before 1.9 a validation may only look at its own variable. Where else can a condition go?',
                    why='A precondition in the resource\'s lifecycle block can compare two variables on any recent version, and it is checked when Terraform plans.',
                    wrong=[None, 'The rule is worth keeping. It just needs another home.', 'The names are fine. The problem is looking at a second variable.']),
                ask('When is a precondition checked?', ['When Terraform plans', 'Only after the apply', 'Only in tests'], answer=0,
                    evidence=evidence('code', title='runbook: Service/cluster.tf', text="""lifecycle {
  precondition {
    condition     = var.max_workers >= var.min_workers
    error_message = "max_workers must be at least min_workers."
  }
}"""),
                    clue='Pre means before. Before what?',
                    why='Terraform checks a precondition when it makes the plan, and again just before it creates the resource. A bad pair of values stops the plan.',
                    wrong=[None, 'That would be a postcondition, which checks the result.', 'Tests run it too, but so does every plan.']),
            ],
        ),
        starter="""def check_range(name, value, low, high):
    # your code here
    pass
""",
        solution="""def check_range(name, value, low, high):
    if low <= value <= high:
        return None
    return f"{name} must be between {low} and {high}."
""",
        cases=[
            case('auto_stop_minutes', 5, 10, 60, expected='auto_stop_minutes must be between 10 and 60.', sample=True),
            case('auto_stop_minutes', 45, 10, 60, expected=None),
            case('auto_stop_minutes', 10, 10, 60, expected=None),
            case('auto_stop_minutes', 60, 10, 60, expected=None),
            case('max_workers', 9, 1, 8, expected='max_workers must be between 1 and 8.'),
            case('max_workers', 0, 1, 8, expected='max_workers must be between 1 and 8.'),
        ],
        guided="""def check_range(name, value, low, high):
    # Replace every ___ with real code, then run the tests.
    if ___:
        return None
    return f"{name} must be between {low} and ___."
""",
        fills=['low <= value <= high', '{high}'],
        concepts=[
            [
                'A range check in one line',
                '`low <= value <= high` is true only when both comparisons are true, so the limits themselves pass.',
                """10 <= 10 <= 60   # True
10 <= 61 <= 60   # False""",
            ],
            [
                'f-strings',
                'Put `f` before a string and anything in `{}` is filled in with its value.',
                """name = "max_workers"
f"{name} must be 8 or fewer.\"""",
            ],
        ],
        byhand='The sample: 5 is not between 10 and 60, so the value fails and the message is built: "auto_stop_minutes must be between 10 and 60."',
        why='One comparison and, at most, one message.',
        gotchas=[
            [
                'The limits are allowed',
                'Use `>=` and `<=` when the edges are fine. Check the edges in your tests: 10 and 60 should pass.',
            ],
            [
                'Check the Terraform version first',
                'A validation that looks at another variable needs 1.9 or later. The version Spacelift runs is set on the stack, not on your laptop.',
            ],
        ],
    ),
)


lesson(MODULE, 'tests_seen_fail',
    title='Would this test catch the break?',
    checked='2026-11-08',
    sources=[source('Tests', 'https://developer.hashicorp.com/terraform/language/tests'), source('Tests: mocks', 'https://developer.hashicorp.com/terraform/language/tests/mocking'), source('terraform test command', 'https://developer.hashicorp.com/terraform/cli/commands/test')],
    learn=[
        "`terraform test` runs files ending in `.tftest.hcl`. Each `run` block does a plan or an apply (apply is the default, and it creates real things), then its `assert` blocks check the result.",
        "For quick tests with no cloud, set `command = plan` and add a `mock_provider`: a pretend provider that makes up the values Azure or Databricks would normally fill in, like a random 8-letter text for a name or 0 for a number. Nothing is created and no credentials are needed. Mock providers arrived in Terraform 1.7.",
        "To prove a rule says no, give it a bad value and list the rule in `expect_failures`. That run passes only if the rule fails.",
        "**A test you have never seen fail proves nothing.** It might check the wrong thing, or nothing at all. So once, break the rule on purpose (change 60 to 600) and watch a test go red. If none does, you are missing a test. Then put the rule back.",
    ],
    example=example('Two tests, one for each edge', """mock_provider "databricks" {}

run "rejects_five_minutes" {
  command = plan
  variables { auto_stop_minutes = 5 }
  expect_failures = [var.auto_stop_minutes]
}

run "rejects_ninety_minutes" {
  command = plan
  variables { auto_stop_minutes = 90 }
  expect_failures = [var.auto_stop_minutes]
}"""),
    check=question(
        'A test sets `auto_stop_minutes = 5` and lists `var.auto_stop_minutes` in `expect_failures`. The rule rejects 5. Does the test pass?',
        [
            'Yes: the failure was expected',
            'No: a rule failed',
            'Only with a real provider',
        ],
        answer=0,
        why='expect_failures turns it around: the run passes because the rule failed, which is exactly what the test wanted to see.',
    ),
    angle=angle(
        pattern='Break it once, watch it go red',
        text='The big idea: a test only earns trust once you\'ve seen it fail. Your code plays the tests against a rule: for each test it works out whether the rule rejects that value, compares that with what the test expected, and says whether any test went red. Run it with the real rule and then with a broken one: if the broken rule still gives no red, a test is missing. It is like testing a smoke alarm by pressing its button, not by waiting for a fire.',
        say="\"A test I've never seen [[fail|pass|run::Watch it go red once.]] proves nothing. So I break the rule on purpose, watch a test go red, and put it back. With a [[mock|real|remote::A pretend provider.]] provider, that costs nothing.\"",
        classic=None,
    ),
    exercise=exercise(
        title='Does Any Test Go Red?',
        topic='testing',
        difficulty='medium',
        fn='goes_red',
        prompt="""Your function gets `tests`, a list of dicts like `{"value": 5, "expect_fail": True}`, and a rule's limits `low` and `high` (both allowed).

For each test:
- the rule **rejects** the value if it is below `low` or above `high`;
- the test **goes red** if what the rule did doesn't match what the test expected: rejected but `expect_fail` is `False`, or allowed but `expect_fail` is `True`.

Return `True` if any test goes red, otherwise `False`.""",
        pattern='Check every item and stop as soon as one breaks the expectation.',
        target='one pass over the tests',
        realworld="This is why you break a rule on purpose before trusting its tests. With only a test at 5, changing the top limit from 60 to 600 turns nothing red, so a mistake there would ship. A test at 90 catches it.",
        practice=practice(
            intro='Read a module\'s tests and decide whether they would catch a broken rule.',
            explain='A test only earns trust once you have seen it fail. You checked whether the tests would notice a broken rule, found the edge nobody tested, and saw what a pretend provider can and cannot know about Azure.',
            pattern='Imagine the break, then look for the red',
            realworld='When you review a pull request that adds a rule or a test, you ask which test goes red if the rule breaks, and ask for one at each edge. When tests pass but a real run fails, you check whether it was something only Azure could know.',
            asks=[
                ask('Someone changes the rule\'s top limit from 60 to 600 by mistake. Does this test go red?', ['Yes', 'No'], answer=1,
                    evidence=evidence('code', title='tests/warehouse.tftest.hcl', text="""mock_provider "databricks" {}

run "rejects_five_minutes" {
  command = plan
  variables { auto_stop_minutes = 5 }
  expect_failures = [var.auto_stop_minutes]
}"""),
                    clue='With the top at 600, is 5 still rejected?',
                    why='5 is still below 10, so the rule still rejects it and the test still passes. Nothing tests the top limit, so the mistake would ship.',
                    wrong=['5 breaks the bottom limit, which didn\'t change.', None]),
                ask('Which extra test would catch that mistake?', ['90, expected to fail', '30, expected to pass', '5, run once more'], answer=0,
                    evidence=evidence('code', title='The rule, and the mistake', text="""condition = var.auto_stop_minutes >= 10 && var.auto_stop_minutes <= 60
# by mistake:
condition = var.auto_stop_minutes >= 10 && var.auto_stop_minutes <= 600"""),
                    clue='You need a value the right rule rejects but the broken one allows.',
                    why='90 is rejected by the real rule and allowed by the broken one. The test expects a failure, gets none, and goes red.',
                    wrong=[None, '30 passes under both rules, so it can\'t tell them apart.', 'Running the same test again gives the same answer.']),
                ask('What does running these tests create in Azure?', ['Nothing at all', 'A small warehouse', 'One DEV apply'], answer=0,
                    evidence=evidence('code', title='tests/warehouse.tftest.hcl', text="""mock_provider "databricks" {}

run "names_are_lower_case" {
  command = plan
  variables { code = "SALES", name = "Daily" }
  assert {
    condition     = databricks_sql_endpoint.this.name == "sales_daily"
    error_message = "The warehouse name should be lower case."
  }
}"""),
                    clue='Look at the first line and the command.',
                    why='A mock provider never calls Databricks, and command = plan never applies. The test runs in seconds with no credentials.',
                    wrong=[None, 'Without the mock and with command = apply it would. Here it doesn\'t.', 'Tests never touch the DEV stack\'s state.']),
                ask('The mock tests all passed. Why didn\'t they catch this?', ['Mocks can\'t see Azure', 'The test had a typo', 'Tests skip storage'], answer=0,
                    evidence=evidence('code', title='The first real apply', text="""Error: creating Storage Account "stsalesdev":
  StorageAccountAlreadyTaken: The storage account
  named stsalesdev is already taken."""),
                    clue='Where does the pretend provider get its answers from?',
                    why='A pretend provider makes up its answers. Only Azure knows a name is taken somewhere else, so only a real apply can find this.',
                    wrong=[None, 'The tests ran fine. They just can\'t know this.', 'Tests can check a storage account\'s settings, just not what Azure decides.']),
                ask('You wrote a new test and it passed first time. What do you do before trusting it?', ['Make it fail on purpose', 'Run it again twice', 'Merge it straight away'], answer=0,
                    alone=True,
                    clue='How do you know it can say no?',
                    why='Break the rule it guards for a moment and watch it go red. If it stays green, it isn\'t testing what you think. Then put the rule back.',
                    wrong=[None, 'It will pass every time, and that still proves nothing.', 'A test that has never failed may be checking nothing.']),
            ],
        ),
        starter="""def goes_red(tests, low, high):
    # your code here
    pass
""",
        solution="""def goes_red(tests, low, high):
    for t in tests:
        rejected = t["value"] < low or t["value"] > high
        if rejected != t["expect_fail"]:
            return True
    return False
""",
        cases=[
            case([{'value': 5, 'expect_fail': True}], 10, 600, expected=False, sample=True),
            case([{'value': 5, 'expect_fail': True}, {'value': 90, 'expect_fail': True}], 10, 600, expected=True),
            case([{'value': 5, 'expect_fail': True}, {'value': 90, 'expect_fail': True}], 10, 60, expected=False),
            case([{'value': 30, 'expect_fail': False}], 10, 60, expected=False),
            case([{'value': 30, 'expect_fail': False}], 40, 60, expected=True),
            case([], 10, 60, expected=False),
            case([{'value': 10, 'expect_fail': False}, {'value': 60, 'expect_fail': False}], 10, 60, expected=False),
        ],
        guided="""def goes_red(tests, low, high):
    # Replace every ___ with real code, then run the tests.
    for t in tests:
        rejected = t["value"] < low or ___
        if rejected != t["expect_fail"]:
            return ___
    return False
""",
        fills=['t["value"] > high', 'True'],
        concepts=[
            [
                '!= on True and False',
                '`a != b` is `True` when the two differ. Comparing what happened with what was expected is exactly that.',
                """True != False   # True
True != True    # False""",
            ],
            [
                'Stop at the first one',
                'A `return` inside the loop ends the function as soon as one test goes red: no need to look at the rest.',
                """for t in tests:
    if broken(t):
        return True
return False""",
            ],
        ],
        byhand='The sample: one test, value 5, expected to fail. With limits 10 and 600, 5 is below 10, so it is rejected, which matches. No test goes red: False. That is the problem: the broken limit is invisible.',
        why='One pass over the tests, stopping at the first red one.',
        gotchas=[
            [
                'Test both edges',
                'A range has two limits. Test a value just outside each one, and one just inside.',
            ],
            [
                'apply is the default',
                'A run block without `command = plan` applies, and creates real things unless the provider is mocked.',
            ],
        ],
    ),
)


lesson(MODULE, 'lock_every_platform',
    title='Why did the run pick a different provider?',
    checked='2026-11-08',
    sources=[source('Dependency lock file', 'https://developer.hashicorp.com/terraform/language/files/dependency-lock'), source('terraform providers lock', 'https://developer.hashicorp.com/terraform/cli/commands/providers/lock'), source('terraform init', 'https://developer.hashicorp.com/terraform/cli/commands/init')],
    learn=[
        "`.terraform.lock.hcl` records the exact provider version a folder uses, plus **checksums**: fingerprints of the provider's files, so Terraform can tell the download is the real one. The lesson on pinning provider versions covered why you commit it.",
        "A stack folder **with no lock file** gets the newest version its constraint allows, every time a fresh run starts. That's how a Spacelift run can pick a newer provider than the one you tried on your laptop, with nobody changing a line.",
        "Checksums are per **platform**: the operating system and chip, like `windows_amd64` or `linux_amd64`. If your team installs providers from a **mirror** (the company's own copy of the registry), `init` can only record the checksum for the platform it ran on. A lock file made on a Windows laptop then fails on Spacelift's Linux workers, with \"doesn't match any of the checksums previously recorded in the dependency lock file\". `terraform providers lock -platform=windows_amd64 -platform=linux_amd64` records every platform at once.",
        "In CI, `terraform init -lockfile=readonly` uses the recorded versions and checksums and never rewrites the file. Upgrades then happen only on purpose, with `terraform init -upgrade` in a reviewed pull request.",
    ],
    example=example('A lock file entry, and how to fill it for everyone', """provider "registry.terraform.io/databricks/databricks" {
  version     = "1.90.2"
  constraints = "~> 1.90.0"
  hashes = [
    "h1:...",   # one line per platform it was checked on
    "zh:...",
  ]
}

# record checksums for laptops and workers in one go
terraform providers lock \\
  -platform=windows_amd64 \\
  -platform=darwin_amd64 \\
  -platform=linux_amd64"""),
    check=question(
        'A stack folder has no `.terraform.lock.hcl`. Its constraint is `~> 1.90`, and the provider releases 1.92 tonight. What does tomorrow\'s run use?',
        [
            '1.92, the newest allowed',
            '1.90, the oldest allowed',
            'Whatever your laptop has',
        ],
        answer=0,
        why='With nothing recorded, Terraform picks the newest version the constraint allows. ~> 1.90 allows 1.92, so the run quietly moves up.',
    ),
    angle=angle(
        pattern='Record it once, use it everywhere',
        text='The big idea: a lock file only keeps runs the same if it covers every provider on every platform that runs them. Your code goes through each provider and each platform you need, and lists every pair that has no checksum yet. An empty answer means laptops and workers will all accept the same files. It is like a guest list that has to be printed for every door: one door without it, and that door turns everyone away.',
        say="\"I commit the [[lock file|README|state file::.terraform.lock.hcl, next to the code.]] with checksums for every [[platform|branch|stack::Windows laptops and Linux workers.]], so every run gets the same provider until a reviewed [[upgrade|apply|import::A new version, chosen on purpose and reviewed.]].\"",
        classic=None,
    ),
    exercise=exercise(
        title='Which Platforms Are Missing?',
        topic='versions',
        difficulty='easy',
        fn='missing_platforms',
        prompt="""Your function gets:

- `lock`: a dict from provider name to the list of platforms it has checksums for, like `{"databricks": ["windows_amd64"], "azurerm": ["windows_amd64", "linux_amd64"]}`.
- `needed`: the platforms your team and your workers use, like `["windows_amd64", "linux_amd64"]`.

Return a list of strings `"provider:platform"` for every pair that is missing, providers in the order of `lock`, platforms in the order of `needed`. For the example: `["databricks:linux_amd64"]`.""",
        pattern='Two loops: for each provider, check each needed platform.',
        target='one pass over providers times platforms',
        realworld="This is the check a team adds before merging a lock file change: every provider must have checksums for the laptops people use and for the Linux workers Spacelift runs on, or the first run on the missing platform fails.",
        practice=practice(
            intro='A run picked a provider nobody chose, then another one failed on checksums. Work out why, and what fixes it for everyone.',
            explain='A lock file only keeps runs the same if it is committed and covers every platform that runs them. You traced a surprise upgrade to a missing lock file, a checksum error to a lock file made on one platform, and kept CI from rewriting it.',
            pattern='Same versions, every platform',
            realworld='When a run uses a provider version nobody chose, you check whether that stack folder has a committed lock file. When CI fails on checksums after a lock file change, you ask which platform it was made on, and record the others.',
            asks=[
                ask('Why did this run get databricks 1.92?', ['There is no lock file', 'Spacelift upgrades nightly', 'The constraint says 1.92'], answer=0,
                    evidence=evidence('code', title='Stack folder and init log', text="""service/
  main.tf
  variables.tf
  versions.tf        required_providers: databricks "~> 1.90"

Initializing provider plugins...
- Finding databricks/databricks versions matching "~> 1.90"...
- Installing databricks/databricks v1.92.0..."""),
                    clue='Which file would have kept the run on the version you tested?',
                    why='There\'s no .terraform.lock.hcl, so every fresh run picks the newest version that ~> 1.90 allows. Commit the lock file to stop it.',
                    wrong=[None, 'Spacelift runs what init picks. It doesn\'t upgrade on its own.', '~> 1.90 allows 1.92, but doesn\'t ask for it.']),
                ask('What\'s the most likely cause of this error?', ['No Linux checksums recorded', 'The provider is broken', 'The state is locked'], answer=0,
                    evidence=evidence('code', title='Spacelift run on a Linux worker', text="""Error: Failed to install provider

the local package for registry.terraform.io/databricks/databricks
1.90.2 doesn't match any of the checksums previously recorded in
the dependency lock file

# the lock file was made on a Windows laptop, providers from the company mirror"""),
                    clue='Where was the lock file made, and where is the run?',
                    why='Installed from the mirror on Windows, init recorded only the Windows checksum. The Linux worker\'s files have a different fingerprint, so it refuses them.',
                    wrong=[None, 'The same version works on the laptop. The fingerprint is what differs.', 'A state lock gives a different error, about the lock id.']),
                ask('What fixes it for everyone?', ['Record checksums for each platform', 'Upgrade every provider today', 'Delete the lock file and rerun'], answer=0,
                    alone=True,
                    clue='You want laptops and workers to accept the same version.',
                    why='terraform providers lock with a -platform for each one records every checksum. Commit the result and every platform accepts the same files.',
                    wrong=[None, 'An upgrade changes the version but still records one platform.', 'Without a lock file every run picks its own version again.']),
                ask('A teammate ran `init -upgrade` on their laptop but didn\'t commit the lock file. What does CI use?', ['The committed lock file\'s versions', 'The teammate\'s newer versions', 'The newest versions there are'], answer=0,
                    evidence=evidence('code', title='CI step', text='terraform init -lockfile=readonly'),
                    clue='CI only sees what is in the repo, and readonly never rewrites it.',
                    why='CI reads the lock file from the repo and won\'t change it. The upgrade only reaches CI when the new lock file is committed and reviewed.',
                    wrong=[None, 'Their laptop\'s lock file never left their laptop.', 'readonly uses what is recorded, not the newest.']),
            ],
        ),
        starter="""def missing_platforms(lock, needed):
    # your code here
    pass
""",
        solution="""def missing_platforms(lock, needed):
    missing = []
    for provider, platforms in lock.items():
        for p in needed:
            if p not in platforms:
                missing.append(provider + ":" + p)
    return missing
""",
        cases=[
            case({'databricks': ['windows_amd64'], 'azurerm': ['windows_amd64', 'linux_amd64']}, ['windows_amd64', 'linux_amd64'], expected=['databricks:linux_amd64'], sample=True),
            case({'databricks': ['windows_amd64', 'linux_amd64']}, ['windows_amd64', 'linux_amd64'], expected=[]),
            case({'databricks': [], 'azurerm': []}, ['linux_amd64'], expected=['databricks:linux_amd64', 'azurerm:linux_amd64']),
            case({'azurerm': ['linux_amd64']}, ['windows_amd64', 'darwin_amd64', 'linux_amd64'], expected=['azurerm:windows_amd64', 'azurerm:darwin_amd64']),
            case({}, ['linux_amd64'], expected=[]),
        ],
        guided="""def missing_platforms(lock, needed):
    # Replace every ___ with real code, then run the tests.
    missing = []
    for provider, platforms in lock.items():
        for p in ___:
            if p not in platforms:
                missing.append(___)
    return missing
""",
        fills=['needed', 'provider + ":" + p'],
        concepts=[
            [
                'Looping over a dict',
                '`for key, value in d.items():` gives each key with its value, in the order they were added.',
                """for name, ps in {"a": [1]}.items():
    print(name, ps)""",
            ],
            [
                'A loop inside a loop',
                'The inner loop runs fully for each turn of the outer one, so every provider meets every platform.',
                """for a in ["x", "y"]:
    for b in [1, 2]:
        print(a, b)""",
            ],
        ],
        byhand='The sample: databricks has windows_amd64 but not linux_amd64, so "databricks:linux_amd64" is missing. azurerm has both. Result: ["databricks:linux_amd64"].',
        why='Each provider meets each needed platform once.',
        gotchas=[
            [
                'One lock file per folder',
                'Each stack folder that runs init needs its own committed lock file. One in the module repo doesn\'t cover the runbook.',
            ],
            [
                'Modules aren\'t locked',
                'The lock file covers providers only. Pin modules with an exact ?ref= version.',
            ],
        ],
    ),
)
