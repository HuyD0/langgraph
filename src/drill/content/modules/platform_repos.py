"""How the platform repos fit together: YAML in the config repo, the Terraform runbook that reads
it, the modules and providers it calls, and the Spacelift stacks that run it. All names are invented."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, fix, lesson, module, planned, practice, question, stack

MODULE = module('platform-repos', 'How the platform repos fit together',
                'Follow one request from YAML through the runbook and Spacelift to Azure Databricks.',
                setting=PLATFORM_SETTING)


lesson(MODULE, 'field_status',
    title='What happened to my YAML field?',
    learn=[
        "On a platform team, product teams don't write Terraform. They ask for things in **YAML** in the **config repo**: `env.yml` lists the teams in an environment, each team's `team.yml` names its owner group and points to resource files like `clusters.yml`. **Pydantic** checks each file against a contract: a field it doesn't know, or a value of the wrong type, is rejected.",
        "The **runbook** is Terraform code that reads that YAML. It loads the files, fills in **defaults** for anything left out, **transforms** some values (a cluster's name gets the team's short code in front), and passes the result to **modules**, which call the Databricks and Azure **providers**. **Spacelift** runs all of it as a plan someone reviews before anything is applied.",
        "So a field goes through five points: **the YAML, the check, the runbook, the module, the provider**. Valid YAML is not enough. If the runbook never passes a field on, it is **dropped**: it looks fine in the YAML and does nothing.",
        "Reviewers describe what happened to a field with one word: **SUPPORTED** (it reaches the provider as written), **DEFAULTED** (it was left out and the runbook supplied a value), **TRANSFORMED** (changed on the way), **DROPPED** (accepted, never used), **INVALID** (the check rejects it) or **UNKNOWN** (you haven't traced it all the way yet).",
    ],
    example=example('Tracing one field', """clusters.yml        policy_name: Shared Compute - Standard
Pydantic check      policy_name is a known text field      -> valid
runbook             policy_name = try(c.policy_name, "Personal Compute")
workspace module    looks the policy up by name, passes its id
provider            databricks_cluster.policy_id = <that id>
                    -> SUPPORTED

Leave policy_name out, and the runbook's try(...) uses "Personal Compute"
                    -> DEFAULTED"""),
    check=question(
        'A team adds `autoscale_note: "keep it small"` to `clusters.yml`. Pydantic accepts it as free text, but the runbook never reads it. What happened to the field?',
        [
            'SUPPORTED: the YAML is valid',
            'DROPPED: it is accepted but never passed on',
            'INVALID: the check rejects it',
        ],
        answer=1,
        why='Passing the check only means the YAML is well formed. The field has to reach the provider to do anything, and this one stops at the runbook, so it is dropped. A dropped field is a blocker: nobody should rely on it.',
    ),
    angle=angle(
        pattern='Follow the field all the way down',
        text='The big idea: a field in YAML only matters if it reaches the provider. You follow it through five points: the YAML, the check, the runbook, the module and the provider, and give it one word for what happened. Your code asks the questions in a set order. Rejected by the check: INVALID. Any step not traced yet: UNKNOWN. Not passed on, or never reaching the provider: DROPPED. Left out and filled in by the runbook: DEFAULTED. Changed on the way: TRANSFORMED. Otherwise: SUPPORTED. It is like posting a parcel: it only counts if it is delivered, not if the label was filled in correctly.',
        say="\"Valid YAML isn't enough. I follow a field from the YAML through the [[runbook|README|pull request::The Terraform code that reads the YAML.]] to the provider. If it never gets there, it's [[dropped|supported|invalid::Accepted, but it does nothing.]], even though the YAML looks [[fine|broken|empty::Nothing in the file itself looks wrong.]].\"",
        classic=None,
    ),
    stack=stack('Terraform: where the runbook reads YAML', """locals {
  team     = yamldecode(file("${path.module}/config/DEV/team-sales/team.yml"))
  clusters = yamldecode(file("${path.module}/config/DEV/team-sales/clusters.yml")).clusters

  dbx_clusters = [for c in local.clusters : {
    name        = lower("${c.code}_${c.name}")             # TRANSFORMED
    policy_name = try(c.policy_name, "Personal Compute")    # DEFAULTED if left out
  }]                                                        # anything else: DROPPED
}"""),
    exercise=exercise(
        title='Name What Happened',
        topic='iac-review',
        difficulty='easy',
        fn='field_status',
        prompt="""Your function gets `trace`, a dict describing one YAML field's journey:

- `"in_yaml"`: `True` if the team wrote the field, `False` if they left it out.
- `"valid"`: `True` if the Pydantic check accepts it, `False` if it rejects it, `None` if not checked yet.
- `"runbook"`: what the runbook does with it: `"passes"`, `"defaults"`, `"transforms"` or `"ignores"`, or `None` if not checked yet.
- `"reaches_provider"`: `True`, `False`, or `None` if not checked yet.

Return one word, asking in this order:

1. `valid` is `False` -> `"INVALID"`
2. any of `valid`, `runbook`, `reaches_provider` is `None` -> `"UNKNOWN"`
3. `runbook` is `"ignores"`, or `reaches_provider` is `False` -> `"DROPPED"`
4. `in_yaml` is `False` and `runbook` is `"defaults"` -> `"DEFAULTED"`
5. `runbook` is `"transforms"` -> `"TRANSFORMED"`
6. otherwise -> `"SUPPORTED"`""",
        pattern='Ask the questions in a fixed order and return at the first one that fits.',
        target='a few checks, no loops',
        realworld="This is how a careful reviewer reads a config PR on a Databricks platform team: for each changed YAML field, find where the runbook reads it and where the module passes it to the provider. A field that stops on the way is the classic \"I changed the YAML but the plan didn't change\".",
        practice=practice(
            intro='Follow fields down the chain and name what happened to each, the way a reviewer reads a config PR.',
            explain='A field only matters if it reaches the provider. You followed it stop by stop: the YAML, the check, the runbook, the module, the provider, and named what happened: supported, defaulted, transformed, dropped or invalid.',
            asks=[
                ask('Does the runbook pass `autoscale_note` on?', ['Yes', 'No'], answer=1,
                    evidence=evidence('chain', stops=[
                        {'label': 'clusters.yml', 'sub': 'autoscale_note: "keep it small"', 'state': 'ok', 'tag': 'IN YAML'},
                        {'label': 'Pydantic check', 'sub': 'free text: accepted', 'state': 'ok', 'tag': 'VALID'},
                        {'label': 'The runbook', 'sub': 'Service/parsing_clusters.tf', 'state': 'now', 'tag': 'NOW'},
                        {'label': 'Workspace module', 'state': 'later'},
                        {'label': 'Provider', 'state': 'later'},
                    ], snippet='dbx_clusters = [for c in local.clusters : {\n  name        = lower("${c.code}_${c.name}")\n  policy_name = try(c.policy_name, "Personal Compute")\n  min_workers = try(c.min_workers, null)\n  max_workers = try(c.max_workers, null)\n}]'),
                    clue='Look for the field\'s name among the ones the snippet reads from `c`.',
                    why='The runbook reads name, code, policy_name and the worker counts. `autoscale_note` isn\'t one of them, so it stops here.',
                    wrong=['Check the snippet again: which fields does it read from `c`?', None]),
                ask('So what happened to `autoscale_note`?', ['SUPPORTED', 'DROPPED', 'INVALID'], answer=1,
                    clue='It passed the check, then went no further.',
                    why='Accepted by the check, never passed on: dropped. It looks fine in the YAML and does nothing, so nobody should rely on it.',
                    wrong=['Supported means it reaches the provider as written. Did it?', None, 'Invalid means the check rejects it. Pydantic accepted it.']),
                ask('A cluster leaves out `policy_name`. What happened to that field?', ['SUPPORTED', 'DEFAULTED', 'DROPPED'], answer=1,
                    evidence=evidence('code', title='The runbook line', text='policy_name = try(c.policy_name, "Personal Compute")'),
                    clue='`try()` uses its second value when the first one is missing.',
                    why='Left out, and the runbook filled in Personal Compute: defaulted.',
                    wrong=['The team never wrote it, so it can\'t reach the provider as written.', None, 'Something still reaches the provider: the runbook\'s fallback.']),
                ask('The team writes `name: Daily-Report` with `code: SALES`, and the plan creates `sales_daily-report`. What happened to `name`?', ['SUPPORTED', 'TRANSFORMED', 'DEFAULTED'], answer=1,
                    clue='Compare what was typed with what was built.',
                    why='The runbook put the code in front and lowered the case: transformed. Search the plan for the new name, not the one in the YAML.',
                    wrong=['It reached the provider, but not as written.', None, 'The team did write a name, so nothing was filled in for them.']),
            ],
        ),
        starter="""def field_status(trace):
    # your code here
    pass
""",
        solution="""def field_status(trace):
    if trace["valid"] is False:
        return "INVALID"
    if None in (trace["valid"], trace["runbook"], trace["reaches_provider"]):
        return "UNKNOWN"
    if trace["runbook"] == "ignores" or not trace["reaches_provider"]:
        return "DROPPED"
    if not trace["in_yaml"] and trace["runbook"] == "defaults":
        return "DEFAULTED"
    if trace["runbook"] == "transforms":
        return "TRANSFORMED"
    return "SUPPORTED"
""",
        cases=[
            case({'in_yaml': True, 'valid': True, 'runbook': 'passes', 'reaches_provider': True}, expected='SUPPORTED', sample=True),
            case({'in_yaml': True, 'valid': True, 'runbook': 'ignores', 'reaches_provider': False}, expected='DROPPED'),
            case({'in_yaml': True, 'valid': False, 'runbook': None, 'reaches_provider': None}, expected='INVALID'),
            case({'in_yaml': False, 'valid': True, 'runbook': 'defaults', 'reaches_provider': True}, expected='DEFAULTED'),
            case({'in_yaml': True, 'valid': True, 'runbook': 'transforms', 'reaches_provider': True}, expected='TRANSFORMED'),
            case({'in_yaml': True, 'valid': True, 'runbook': 'passes', 'reaches_provider': None}, expected='UNKNOWN'),
            case({'in_yaml': True, 'valid': True, 'runbook': 'defaults', 'reaches_provider': True}, expected='SUPPORTED'),
            case({'in_yaml': True, 'valid': True, 'runbook': 'transforms', 'reaches_provider': False}, expected='DROPPED'),
        ],
        guided="""def field_status(trace):
    # Replace every ___ with real code, then run the tests.
    # 1. The check said no.
    if trace["valid"] is False:
        return "INVALID"
    # 2. Some step hasn't been traced yet.
    if None in (trace["valid"], trace["runbook"], trace["reaches_provider"]):
        return ___
    # 3. It stops before the provider.
    if trace["runbook"] == "ignores" or not trace["reaches_provider"]:
        return "DROPPED"
    # 4. Left out, and the runbook filled it in.
    if ___ and trace["runbook"] == "defaults":
        return "DEFAULTED"
    if trace["runbook"] == "transforms":
        return "TRANSFORMED"
    return "SUPPORTED"
""",
        fills=['"UNKNOWN"', 'not trace["in_yaml"]'],
        concepts=[
            [
                'Return early',
                'A function stops at its first `return`. Asking questions in order and returning as soon as one fits keeps each check simple.',
                """def size(n):
    if n > 100:
        return "big"
    return "small\"""",
            ],
            [
                'is False and None',
                '`x is False` is only true for `False` itself, not for `None`. That matters when `None` means "not checked yet".',
                """None is False    # False
False is False   # True""",
            ],
            [
                'in on a tuple',
                '`None in (a, b, c)` asks whether any of the three is `None`.',
                'None in (True, None, "passes")   # True',
            ],
        ],
        byhand='The sample: valid is True, nothing is None, runbook is "passes" (not "ignores") and it reaches the provider, the team wrote it so it is not DEFAULTED, and it is not transformed. So: SUPPORTED.',
        why='At most six checks, each looking at one or two fields.',
        gotchas=[
            [
                'Valid is not the same as used',
                'Pydantic only says the YAML is well formed. Always find the line in the runbook that reads the field before you rely on it.',
            ],
            [
                'Check the same version as the run',
                'Trace the field at the commit the Spacelift run used, not today\'s main branch: the runbook may have changed since.',
            ],
        ],
    ),
)


lesson(MODULE, 'folder_access',
    title='Where did that access come from?',
    learn=[
        "A team's `team.yml` can name an `owner_group` and list `folder_grants`: other groups and the permission each should have on the team's workspace folder, like `CAN_EDIT`. A **group** is a named set of people or identities from Microsoft Entra ID.",
        "The runbook doesn't copy that list as it is. It **adds access you didn't type**: the owner group gets `CAN_MANAGE`, and every workspace user gets `CAN_READ` by default. Then it joins those with the explicit grants and hands the whole list to the module.",
        "Databricks folder permissions go up in steps: `CAN_READ`, then `CAN_RUN`, then `CAN_EDIT`, then `CAN_MANAGE`. A group listed twice ends up with the **highest** of its permissions, not both.",
        "So when a plan shows `CAN_MANAGE` for a group that only asked for `CAN_EDIT`, Terraform isn't making it up. Look at what the runbook adds before you call it a mistake, and review **who ends up with what**, not the order of the list.",
    ],
    example=example('What team.yml asks for, and what the plan shows', """# config/DEV/team-sales/team.yml
team:
  owner_group: grp-sales-dev-owners
  folder_grants:
    - group_name: grp-sales-dev-analysts
      privilege: CAN_EDIT

# what the plan gives the folder
grp-sales-dev-owners     CAN_MANAGE   <- added by the runbook (owner)
grp-sales-dev-analysts   CAN_EDIT     <- from team.yml
users                    CAN_READ     <- added by the runbook (default)"""),
    check=question(
        '`team.yml` names `grp-sales-dev-owners` as owner and also grants that same group `CAN_EDIT`. What does the group end up with on the folder?',
        [
            'CAN_EDIT, because that is what the YAML says',
            'CAN_MANAGE, the higher of the two',
            'Both, as two separate permissions',
        ],
        answer=1,
        why='The runbook gives the owner CAN_MANAGE, and the explicit grant adds CAN_EDIT. A group listed twice keeps the higher permission, so the owners have CAN_MANAGE.',
    ),
    angle=angle(
        pattern='Add what the runbook adds, keep the highest',
        text='The big idea: the permissions in a plan are the YAML plus whatever the runbook adds. Your code starts with every workspace user at CAN_READ. If there is an owner group, it gets CAN_MANAGE. Then each explicit grant is added, and for a group that is already there it keeps whichever permission ranks higher. The ranks are a list in order, so the higher one is the one with the bigger position. It is like a guest list where the host is always on it, everyone gets in the lobby, and someone on the list twice gets the better of their two passes.',
        say="\"The plan can show access nobody typed. The runbook gives the owner group [[CAN_MANAGE|CAN_READ|CAN_EDIT::The owner can do everything with the folder.]] and every user CAN_READ. If a group shows up twice, it keeps the [[higher|first|lower::Two passes, and you use the better one.]] permission.\"",
        classic=None,
    ),
    stack=stack('Terraform: the runbook rule, and the permissions resource', """locals {
  folder_access = concat(
    local.team.owner_group != null ? [{
      group_name = local.team.owner_group, permission_level = "CAN_MANAGE"
    }] : [],
    [for g in local.team.folder_grants : { group_name = g.group_name, permission_level = g.privilege }],
    [{ group_name = "users", permission_level = "CAN_READ" }],
  )
}

resource "databricks_permissions" "team_folder" {
  directory_path = "/Teams/team-sales"
  dynamic "access_control" {
    for_each = local.folder_access
    content {
      group_name       = access_control.value.group_name
      permission_level = access_control.value.permission_level
    }
  }
}"""),
    exercise=exercise(
        title='Who Gets What on the Folder',
        topic='iac-review',
        difficulty='easy',
        fn='folder_permissions',
        prompt="""Your function gets `team`, the part of a `team.yml` that matters here:

- `"owner_group"`: a group name, or `None`.
- `"folder_grants"`: a list of dicts like `{"group_name": "grp-sales-dev-analysts", "privilege": "CAN_EDIT"}`.

Work out what each group ends up with, the way the runbook does:

- `"users"` gets `"CAN_READ"`.
- The owner group, if there is one, gets `"CAN_MANAGE"`.
- Each folder grant gives its group its privilege.
- A group given more than one permission keeps the highest. In order, lowest first: `CAN_READ`, `CAN_RUN`, `CAN_EDIT`, `CAN_MANAGE`.

Return a dict from group name to permission.""",
        pattern='Start from the defaults, then add each grant, keeping the higher permission for a group seen before.',
        target='one pass over the grants',
        realworld="This is exactly why a Spacelift plan for a team folder shows more access than the YAML lists. Review the result group by group: the databricks_permissions resource is authoritative, so it also removes any access someone added by hand.",
        practice=practice(
            intro='Read the team\'s YAML and predict what the plan will give each group, including what the runbook adds.',
            explain='The plan\'s permissions are the YAML plus what the runbook adds: the owner group gets CAN_MANAGE, every user gets CAN_READ, and a group listed twice keeps the higher permission.',
            asks=[
                ask('What does `grp-sales-dev-analysts` get on the folder?', ['CAN_EDIT', 'CAN_MANAGE', 'CAN_READ'], answer=0,
                    evidence=evidence('code', title='team.yml', text='# config/DEV/team-sales/team.yml\nteam:\n  owner_group: grp-sales-dev-owners\n  folder_grants:\n    - group_name: grp-sales-dev-analysts\n      privilege: CAN_EDIT'),
                    clue='Analysts aren\'t the owner; read their own grant.',
                    why='Their grant says CAN_EDIT, and nothing else gives them more.',
                    wrong=[None, 'Only the owner group gets CAN_MANAGE from the runbook.', 'Everyone gets CAN_READ, but analysts were also given something higher.']),
                ask('What does `grp-sales-dev-owners` get?', ['Nothing: it isn\'t in folder_grants', 'CAN_MANAGE', 'CAN_EDIT'], answer=1,
                    evidence=evidence('code', title='team.yml', text='# config/DEV/team-sales/team.yml\nteam:\n  owner_group: grp-sales-dev-owners\n  folder_grants:\n    - group_name: grp-sales-dev-analysts\n      privilege: CAN_EDIT'),
                    clue='The runbook adds something for whoever is named as owner.',
                    why='The runbook gives the owner group CAN_MANAGE, even though the YAML only names it as owner.',
                    wrong=['The YAML isn\'t the whole story: the runbook adds access for the owner.', None, 'Nobody typed CAN_EDIT for the owners. What does the runbook add?']),
                ask('Which group gets access that nobody typed at all?', ['users', 'grp-sales-dev-analysts', 'Nobody'], answer=0,
                    clue='Think of everyone in the workspace.',
                    why='The runbook adds `users` with CAN_READ to every team folder.',
                    wrong=[None, 'The analysts were typed in folder_grants.', 'Look again: the runbook adds a default for everyone.']),
                ask('Now the owners are also granted `CAN_EDIT` in folder_grants. What do they end up with?', ['CAN_EDIT', 'CAN_MANAGE', 'Both, as two permissions'], answer=1,
                    evidence=evidence('code', title='team.yml', text="""team:
  owner_group: grp-sales-dev-owners
  folder_grants:
    - group_name: grp-sales-dev-owners
      privilege: CAN_EDIT"""),
                    clue='A group listed twice keeps one permission, the stronger one.',
                    why='The runbook adds CAN_MANAGE and the YAML adds CAN_EDIT. The plan may list both blocks, but the group can manage.',
                    wrong=['The runbook\'s owner rule still applies.', None, 'The plan can show two blocks, but a group ends up with one level: the higher.']),
                fix('The check rejects this team.yml. Fix it so the analysts can edit the folder.',
                    file='config/DEV/team-sales/team.yml',
                    start="""team:
  owner_group: grp-sales-dev-owners
  folder_grants:
    - group: grp-sales-dev-analysts
      privilage: CAN_EDIT
""",
                    answer="""team:
  owner_group: grp-sales-dev-owners
  folder_grants:
    - group_name: grp-sales-dev-analysts
      privilege: CAN_EDIT
""",
                    rules={'path': 'team.folder_grants', 'required': ['group_name', 'privilege'], 'allowed': ['group_name', 'privilege'],
                           'types': {'group_name': 'str', 'privilege': 'str'},
                           'enum': {'privilege': ['CAN_READ', 'CAN_RUN', 'CAN_EDIT', 'CAN_MANAGE']}},
                    goal=[{'field': 'group_name', 'contains': 'grp-sales-dev-analysts', 'message': 'The analysts\' group should be in folder_grants.'}],
                    clue='Two field names are spelled differently from the contract. Compare them with the example in Learn.',
                    why='Pydantic only knows group_name and privilege. A misspelled field is rejected, not guessed at, so nothing quietly goes wrong.'),
            ],
        ),
        starter="""LEVELS = ["CAN_READ", "CAN_RUN", "CAN_EDIT", "CAN_MANAGE"]

def folder_permissions(team):
    # your code here
    pass
""",
        solution="""LEVELS = ["CAN_READ", "CAN_RUN", "CAN_EDIT", "CAN_MANAGE"]

def folder_permissions(team):
    result = {"users": "CAN_READ"}

    def give(group, level):
        old = result.get(group)
        if old is None or LEVELS.index(level) > LEVELS.index(old):
            result[group] = level

    if team["owner_group"] is not None:
        give(team["owner_group"], "CAN_MANAGE")
    for g in team["folder_grants"]:
        give(g["group_name"], g["privilege"])
    return result
""",
        cases=[
            case({'owner_group': 'grp-sales-dev-owners', 'folder_grants': [{'group_name': 'grp-sales-dev-analysts', 'privilege': 'CAN_EDIT'}]},
                 expected={'users': 'CAN_READ', 'grp-sales-dev-owners': 'CAN_MANAGE', 'grp-sales-dev-analysts': 'CAN_EDIT'}, sample=True),
            case({'owner_group': 'grp-sales-dev-owners', 'folder_grants': [{'group_name': 'grp-sales-dev-owners', 'privilege': 'CAN_EDIT'}]},
                 expected={'users': 'CAN_READ', 'grp-sales-dev-owners': 'CAN_MANAGE'}),
            case({'owner_group': None, 'folder_grants': []}, expected={'users': 'CAN_READ'}),
            case({'owner_group': None, 'folder_grants': [{'group_name': 'users', 'privilege': 'CAN_RUN'}]},
                 expected={'users': 'CAN_RUN'}),
            case({'owner_group': 'grp-hr-dev-owners', 'folder_grants': [
                    {'group_name': 'grp-hr-dev-viewers', 'privilege': 'CAN_RUN'},
                    {'group_name': 'grp-hr-dev-viewers', 'privilege': 'CAN_READ'},
                 ]},
                 expected={'users': 'CAN_READ', 'grp-hr-dev-owners': 'CAN_MANAGE', 'grp-hr-dev-viewers': 'CAN_RUN'}),
        ],
        guided="""LEVELS = ["CAN_READ", "CAN_RUN", "CAN_EDIT", "CAN_MANAGE"]

def folder_permissions(team):
    # Replace every ___ with real code, then run the tests.
    result = {"users": "CAN_READ"}   # the runbook's default

    # Give a group a level, but never lower what it already has.
    def give(group, level):
        old = result.get(group)
        if old is None or ___:
            result[group] = level

    if team["owner_group"] is not None:
        give(team["owner_group"], ___)
    for g in team["folder_grants"]:
        give(g["group_name"], g["privilege"])
    return result
""",
        fills=['LEVELS.index(level) > LEVELS.index(old)', '"CAN_MANAGE"'],
        concepts=[
            [
                'A list as a ranking',
                'When a list is in order, `.index(x)` gives a thing\'s place, so comparing places compares ranks.',
                """LEVELS = ["CAN_READ", "CAN_EDIT"]
LEVELS.index("CAN_EDIT") > LEVELS.index("CAN_READ")   # True""",
            ],
            [
                'dict.get',
                '`d.get(key)` gives the value, or `None` if the key isn\'t there, instead of an error.',
                """d = {"a": 1}
d.get("b")   # None""",
            ],
            [
                'A small helper inside the function',
                'A `def` inside a function can change the dict around it. It saves writing the "keep the higher one" rule twice.',
                """def outer():
    seen = {}
    def add(k):
        seen[k] = True
    add("x")
    return seen""",
            ],
        ],
        byhand='Start: users CAN_READ. The owner grp-sales-dev-owners is new, so it gets CAN_MANAGE. The grant grp-sales-dev-analysts CAN_EDIT is new too, so it gets CAN_EDIT. Result: users CAN_READ, owners CAN_MANAGE, analysts CAN_EDIT.',
        why='One pass over the grants; each one is a quick lookup in the dict.',
        gotchas=[
            [
                'Read by group, not by position',
                'The order of access_control blocks in a plan can shuffle without changing anything. Compare who has what.',
            ],
            [
                'Permissions resources replace manual grants',
                'databricks_permissions owns the whole list for that folder: access someone clicked in by hand disappears on the next apply.',
            ],
        ],
    ),
)


lesson(MODULE, 'cluster_from_yaml',
    title='What will Terraform build from clusters.yml?',
    learn=[
        "A team asks for a cluster in its own `clusters.yml`, and `team.yml` points to that file. The first file is only a **pointer**; the second describes the cluster: a name, the team's short **code**, its size and a **cluster policy**, the set of rules that limits what a cluster may be.",
        "The runbook changes some of it on the way. The final name is the code and the name joined with `_`, in **lower case**: `SALES` and `daily-report` become `sales_daily-report`. If no policy is named, it uses **Personal Compute**. It also gives the team's owner group permission to manage the cluster.",
        "Some things are **not allowed** in YAML. A raw `policy_id` is rejected: teams name the policy, and the module looks up its id. Size is either a fixed `num_workers`, or both `min_workers` and `max_workers` for autoscaling, never a mix and never neither.",
        "Reading the plan, you compare what Terraform will build with what the YAML asked for. A difference can be on purpose (the name prefix, the default policy) or a mistake, and you should be able to say which.",
    ],
    example=example('One cluster, before and after the runbook', """# config/DEV/team-sales/clusters.yml
clusters:
  - name: daily-report
    code: SALES
    min_workers: 1
    max_workers: 4

# what the plan will build
name         sales_daily-report        <- code + name, lower case
policy       Personal Compute          <- default: none was named
workers      1 to 4 (autoscaling)
can_manage   grp-sales-dev-owners      <- the team's owner group"""),
    check=question(
        'A cluster in `clusters.yml` has `num_workers: 2` and also `max_workers: 6`. What happens?',
        [
            'It autoscales from 2 to 6',
            'It is rejected: use num_workers, or both min and max',
            'Terraform ignores max_workers',
        ],
        answer=1,
        why='Size is one or the other: a fixed num_workers, or min_workers and max_workers together. A mix is invalid, and it is better caught in review than in a failed plan.',
    ),
    angle=angle(
        pattern='Check it, then build what the runbook would',
        text='The big idea: before you trust a plan, predict it from the YAML. Your code first collects problems: a raw policy_id, or a size that is not exactly num_workers or both min and max. Any problem means you return the list of problems. Otherwise it builds the cluster the way the runbook does: code and name joined and lower-cased, the named policy or Personal Compute, the size as given, and the owner group as manager. It is like checking an order form before the kitchen cooks it: send back the impossible ones, then make the rest the house way.',
        say="\"Before I read the plan, I work out what the runbook will build. I reject a raw [[policy_id|policy_name|cluster name::Teams name the policy; the module looks up the id.]] and a size that mixes the two styles. Then I add the team's [[code|owner|region::It goes in front of the name, in lower case.]] to the name and use Personal Compute if no policy is [[named|approved|paid for::The team left that field out.]].\"",
        classic=None,
    ),
    stack=stack('Terraform: the runbook, then the module\'s policy lookup', """locals {
  dbx_clusters = [for c in local.clusters : {
    name        = lower("${c.code}_${c.name}")
    policy_name = try(c.policy_name, "Personal Compute")
    min_workers = try(c.min_workers, null)
    max_workers = try(c.max_workers, null)
  }]
}

# in the workspace module
data "databricks_cluster_policy" "by_name" {
  for_each = toset([for c in var.clusters : c.policy_name])
  name     = each.value   # a lookup: the policy must already exist
}"""),
    exercise=exercise(
        title='Predict the Cluster',
        topic='iac-review',
        difficulty='medium',
        fn='build_cluster',
        prompt="""Your function gets `cluster`, one entry from `clusters.yml`, and `owner_group`, the team's owner group.

First collect problems, in this order:

- If `"policy_id"` is in the cluster: `"policy_id is not allowed: name the policy"`.
- The size must be exactly one of: `num_workers` alone, or both `min_workers` and `max_workers` (and no `num_workers`). Otherwise: `"use num_workers, or both min_workers and max_workers"`.

If there are any problems, return `{"errors": [...]}` with them in that order.

Otherwise return the cluster the runbook would build:

- `"name"`: the `code`, an `_`, then the `name`, all lower case.
- `"policy_name"`: the cluster's `policy_name`, or `"Personal Compute"` if it has none.
- The size keys exactly as given (`num_workers`, or `min_workers` and `max_workers`).
- `"can_manage"`: the owner group.""",
        pattern='Collect every problem first; only if there are none, build the result with the defaults filled in.',
        target='a few checks and one dict',
        realworld="Product teams on a Databricks platform ask for clusters in YAML exactly like this, and the runbook renames them, applies a default policy and adds the owner. Predicting the result before opening the Spacelift plan is how you spot a surprise in review instead of in production.",
        practice=practice(
            intro='Predict what the runbook will build from a team\'s clusters.yml, and catch what the check would reject.',
            explain='Before reading the plan, you predicted it from the YAML: the code in front of the name in lower case, Personal Compute if no policy is named, and the size as given. You also caught the two things a team can\'t write: a raw policy_id, or a size that mixes num_workers with min and max.',
            asks=[
                ask('What will the cluster be called?', ['daily-report', 'sales_daily-report', 'SALES_daily-report'], answer=1,
                    evidence=evidence('code', title='config/DEV/team-sales/clusters.yml', text="""clusters:
  - name: daily-report
    code: SALES
    min_workers: 1
    max_workers: 4"""),
                    clue='The runbook puts the team\'s code in front, then lowers the case.',
                    why='lower("SALES" + "_" + "daily-report"): sales_daily-report.',
                    wrong=['The runbook changes the name on the way.', None, 'Close, but the runbook lowers the case too.']),
                ask('Which policy will it use?', ['Personal Compute', 'Shared Compute - Standard', 'None: the plan fails'], answer=0,
                    clue='No policy is named, so the runbook falls back to its default.',
                    why='`try(c.policy_name, "Personal Compute")`: with no policy_name, Personal Compute.',
                    wrong=[None, 'Nobody named that policy here.', 'Leaving it out is allowed; the runbook fills it in.']),
                ask('This cluster has `num_workers: 2` and `max_workers: 6`. What happens?', ['It autoscales from 2 to 6', 'It\'s rejected: use num_workers, or both min and max', 'Terraform ignores max_workers'], answer=1,
                    evidence=evidence('code', title='clusters.yml', text="""clusters:
  - name: etl
    code: HR
    num_workers: 2
    max_workers: 6"""),
                    clue='Size is one style or the other, never a mix.',
                    why='A fixed size is num_workers alone; autoscaling is min_workers and max_workers together. A mix is rejected.',
                    wrong=['Autoscaling needs min_workers and max_workers together.', None, 'It isn\'t ignored: the mix is caught before the plan.']),
                ask('What\'s wrong with this one?', ['Nothing', 'policy_id isn\'t allowed: name the policy', 'policy_id must be lower case'], answer=1,
                    evidence=evidence('code', title='clusters.yml', text="""clusters:
  - name: etl
    code: HR
    num_workers: 1
    policy_id: ABC123"""),
                    clue='Teams name the policy; the module looks up its id.',
                    why='A raw policy_id isn\'t allowed in team YAML. Use policy_name, and the workspace module finds the id.',
                    wrong=['Look at the last line: teams don\'t write ids.', None, 'Case isn\'t the problem: teams don\'t write ids at all.']),
                fix('Make this cluster valid. It should autoscale from 1 to 6 workers on the `Shared Compute - Standard` policy.',
                    file='config/DEV/team-hr/clusters.yml',
                    start="""clusters:
  - name: etl
    code: HR
    num_workers: 2
    max_workers: 6
    policy_id: ABC123
""",
                    answer="""clusters:
  - name: etl
    code: HR
    min_workers: 1
    max_workers: 6
    policy_name: Shared Compute - Standard
""",
                    rules={'path': 'clusters', 'required': ['name', 'code'],
                           'allowed': ['name', 'code', 'num_workers', 'min_workers', 'max_workers', 'policy_name', 'autotermination_minutes'],
                           'types': {'name': 'str', 'code': 'str', 'num_workers': 'int', 'min_workers': 'int', 'max_workers': 'int', 'policy_name': 'str'},
                           'forbid': {'policy_id': "policy_id isn't allowed: name the policy with policy_name."}, 'size': True},
                    goal=[{'field': 'min_workers', 'equals': 1, 'message': 'It should start at 1 worker.'},
                          {'field': 'max_workers', 'equals': 6, 'message': 'It should grow to at most 6 workers.'},
                          {'field': 'policy_name', 'equals': 'Shared Compute - Standard', 'message': 'It should use the Shared Compute - Standard policy.'}],
                    clue='Swap the fixed size for a range, and replace the id line with the policy\'s name.',
                    why='Autoscaling is min_workers and max_workers together, and teams name the policy; the module looks up its id.'),
            ],
        ),
        starter="""def build_cluster(cluster, owner_group):
    # your code here
    pass
""",
        solution="""def build_cluster(cluster, owner_group):
    errors = []
    if "policy_id" in cluster:
        errors.append("policy_id is not allowed: name the policy")
    fixed = "num_workers" in cluster
    auto = "min_workers" in cluster and "max_workers" in cluster
    partial = ("min_workers" in cluster) != ("max_workers" in cluster)
    if fixed == auto or partial:
        errors.append("use num_workers, or both min_workers and max_workers")
    if errors:
        return {"errors": errors}

    built = {
        "name": (cluster["code"] + "_" + cluster["name"]).lower(),
        "policy_name": cluster.get("policy_name", "Personal Compute"),
        "can_manage": owner_group,
    }
    for key in ("num_workers", "min_workers", "max_workers"):
        if key in cluster:
            built[key] = cluster[key]
    return built
""",
        cases=[
            case({'name': 'daily-report', 'code': 'SALES', 'min_workers': 1, 'max_workers': 4}, 'grp-sales-dev-owners',
                 expected={'name': 'sales_daily-report', 'policy_name': 'Personal Compute', 'can_manage': 'grp-sales-dev-owners', 'min_workers': 1, 'max_workers': 4}, sample=True),
            case({'name': 'Model-Train', 'code': 'AIML', 'num_workers': 2, 'policy_name': 'Shared Compute - Standard'}, 'grp-aiml-dev-owners',
                 expected={'name': 'aiml_model-train', 'policy_name': 'Shared Compute - Standard', 'can_manage': 'grp-aiml-dev-owners', 'num_workers': 2}),
            case({'name': 'etl', 'code': 'HR', 'num_workers': 2, 'max_workers': 6}, 'grp-hr-dev-owners',
                 expected={'errors': ['use num_workers, or both min_workers and max_workers']}),
            case({'name': 'etl', 'code': 'HR', 'num_workers': 1, 'policy_id': 'ABC123'}, 'grp-hr-dev-owners',
                 expected={'errors': ['policy_id is not allowed: name the policy']}),
            case({'name': 'etl', 'code': 'HR', 'policy_id': 'ABC123'}, 'grp-hr-dev-owners',
                 expected={'errors': ['policy_id is not allowed: name the policy', 'use num_workers, or both min_workers and max_workers']}),
            case({'name': 'etl', 'code': 'HR', 'min_workers': 1}, 'grp-hr-dev-owners',
                 expected={'errors': ['use num_workers, or both min_workers and max_workers']}),
        ],
        guided="""def build_cluster(cluster, owner_group):
    # Replace every ___ with real code, then run the tests.
    errors = []
    if "policy_id" in cluster:
        errors.append("policy_id is not allowed: name the policy")

    # Size: exactly one style, and min and max always together.
    fixed = "num_workers" in cluster
    auto = "min_workers" in cluster and "max_workers" in cluster
    partial = ("min_workers" in cluster) != ("max_workers" in cluster)
    if fixed == auto or partial:
        errors.append("use num_workers, or both min_workers and max_workers")
    if errors:
        return {"errors": errors}

    built = {
        "name": ___,
        "policy_name": cluster.get("policy_name", ___),
        "can_manage": owner_group,
    }
    for key in ("num_workers", "min_workers", "max_workers"):
        if key in cluster:
            built[key] = cluster[key]
    return built
""",
        fills=['(cluster["code"] + "_" + cluster["name"]).lower()', '"Personal Compute"'],
        concepts=[
            [
                'in on a dict',
                '`"key" in d` asks whether the dict has that key.',
                """c = {"num_workers": 2}
"num_workers" in c    # True
"policy_id" in c      # False""",
            ],
            [
                'get with a default',
                '`d.get(key, fallback)` gives the value, or the fallback if the key is missing: the same idea as Terraform\'s try().',
                """c = {}
c.get("policy_name", "Personal Compute")   # 'Personal Compute'""",
            ],
            [
                'Exactly one of two',
                '`a == b` on two True/False values is True when both are True or both are False: exactly the cases where it is not "one or the other".',
                """fixed, auto = True, True
fixed == auto   # True: both styles at once, a problem""",
            ],
            [
                'lower()',
                '`text.lower()` gives the same text in lower case.',
                '"SALES_daily-report".lower()   # \'sales_daily-report\'',
            ],
        ],
        byhand='The sample has no policy_id. It has min_workers and max_workers and no num_workers: fixed is False, auto is True, partial is False, so no size problem. Name: "SALES" + "_" + "daily-report", lower case: sales_daily-report. No policy_name, so Personal Compute. Add the min and max as given and the owner group.',
        why='A handful of key checks and one small dict.',
        gotchas=[
            [
                'A policy name is a lookup',
                'The module finds the policy by name with a data source. A typo in policy_name fails the plan before anything is created.',
            ],
            [
                'The name you see is not the name you typed',
                'Search the plan for the transformed name (code_name, lower case), not the YAML name.',
            ],
        ],
    ),
)


lesson(MODULE, 'lookup_failed',
    title="Why can't the plan find the service principal?",
    learn=[
        "A **service principal** (SP) is an identity for a program, not a person: a job or a connector uses it to reach data. A common failed plan says `Cannot find service principal: sp-sales-etl-uat`. The word **data** in the error path means Terraform tried to **look up** something that should already exist; it was never going to create it.",
        "An SP has to pass several **stages**, in order, before a lookup works. It must exist in **Microsoft Entra ID**. It must be **declared** in the team's `service_principals.yml`. The **Foundation** stack must have been **applied**, which registers it in the Databricks account. Then the **Service** stack assigns it to the workspace.",
        "Each stage is separate: one being done says nothing about the next. A name in YAML is not proof the SP exists. A green **proposed** run in Spacelift is a preview, not an apply. And an SP named only in a connector's permissions, not in `service_principals.yml`, is never picked up by Foundation.",
        "So you check the stages **in order** and stop at the first one that isn't true. Before anything else, make sure you are reading the config at the **same commit** the failed run used: the repo may have changed since.",
    ],
    example=example('Stopping at the first missing stage', """Cannot find service principal: sp-sales-etl-uat
  module.dbx_credentials.data.databricks_service_principal.by_name

same commit as the run?          yes
exists in Entra ID?              yes
declared in service_principals?  no: only in dbx_access_connector.yml
                                 -> stop here: declare it, Foundation never saw it"""),
    check=question(
        'The SP is declared in `service_principals.yml` and the Foundation stack shows a **proposed** run that finished. The Service plan still cannot find it. What do you check next?',
        [
            'Whether Foundation was actually applied',
            'Rerun the Service plan until it passes',
            'Delete and recreate the SP in Entra ID',
        ],
        answer=0,
        why='A finished proposed run is only a preview: it does not register anything. Ask for evidence that Foundation was applied. Rerunning or recreating identities changes things without knowing the cause.',
    ),
    angle=angle(
        pattern='Check the stages in order, stop at the first gap',
        text='The big idea: a lookup fails when an earlier stage is not done, so you check the stages in the order they must happen and stop at the first one that is not true. Your code goes through the facts in a fixed order: the same commit as the run, the SP in Entra ID, declared in service_principals.yml, Foundation applied, assigned by Service. It returns the name of the first missing step. If all are true, what is left is the name or scope. It is like a parcel that never arrived: check it was sent, then that it reached the depot, then the van, in that order.',
        say="\"A failed lookup means an earlier [[stage|test|branch::Entra ID, then Foundation, then Service.]] isn't done. I check them in order: Entra ID, declared in the YAML, Foundation [[applied|proposed|merged::A preview doesn't register anything.]], then assigned to the workspace. I stop at the first one that's [[missing|done|slow::That's where the trail goes cold.]].\"",
        classic=None,
    ),
    stack=stack('Terraform: a lookup, not a create', """# in the catalog module
data "databricks_service_principal" "by_name" {
  for_each     = toset(var.credential_principals)
  display_name = each.value      # fails at plan time if it isn't registered yet
}

# compare: this would create one
# resource "databricks_service_principal" "etl" { ... }"""),
    exercise=exercise(
        title='Find the First Missing Stage',
        topic='iac-review',
        difficulty='easy',
        fn='next_check',
        prompt="""Your function gets `facts`, what you have confirmed about one SP lookup failure, each `True` or `False`:

- `"same_commit"`: you are reading the config at the commit the failed run used.
- `"in_entra"`: the SP exists in Microsoft Entra ID.
- `"declared"`: it is declared in the team's `service_principals.yml` (not only in a connector's permissions).
- `"foundation_applied"`: the Foundation stack was applied, not just proposed.
- `"assigned"`: the Service stack assigned it to the workspace.

Check them in that order and return the first one that is `False`, as one of: `"commit"`, `"entra"`, `"declare"`, `"foundation"`, `"assign"`. If they are all `True`, return `"name or scope"`.""",
        pattern='Walk the stages in the order they must happen and return at the first gap.',
        target='one pass over five facts',
        realworld="This is the order a platform team works through a \"Cannot find service principal\" plan failure on Azure Databricks. The answer also tells you who to ask: the identity team for Entra ID, the product team for the YAML, the platform owner for a Foundation apply.",
        practice=practice(
            intro='Work through a "Cannot find service principal" failure stage by stage, and stop at the first gap.',
            explain='A lookup fails when an earlier stage isn\'t done. You checked the stages in the order they must happen: the run\'s commit, Entra ID, declared in YAML, Foundation applied, assigned by Service, and stopped at the first one that wasn\'t true.',
            asks=[
                ask('What does `data.databricks_service_principal` in the error tell you?', ['Terraform tried to create the SP', 'Terraform looked up an SP that should already exist', 'The SP was deleted'], answer=1,
                    evidence=evidence('code', title='The first error in the planning log', text="""Error: Cannot find service principal: sp-sales-etl-uat
  with module.dbx_credentials[0]
    .data.databricks_service_principal.by_name["sp-sales-etl-uat"]"""),
                    clue='In Terraform, `data` means read, not make.',
                    why='A data source only reads. The SP had to exist and be registered before this plan could find it.',
                    wrong=['A create would be a `resource`, not `data`.', None, 'Nothing here says it was deleted, only that it wasn\'t found.']),
                ask('The SP is named only in the connector\'s permissions. Where does the trail stop?', ['Declared: Foundation never sees it', 'Foundation applied', 'Entra ID'], answer=0,
                    evidence=evidence('chain', stops=[
                        {'label': 'Same commit as the run', 'state': 'ok', 'tag': 'YES'},
                        {'label': 'Exists in Entra ID', 'state': 'ok', 'tag': 'YES'},
                        {'label': 'Declared in service_principals.yml', 'sub': 'only in dbx_access_connector.yml', 'state': 'now', 'tag': '?'},
                        {'label': 'Foundation applied', 'state': 'later'},
                        {'label': 'Assigned by Service', 'state': 'later'},
                    ]),
                    clue='Foundation only collects SPs from the files that declare them.',
                    why='A name in a connector grant isn\'t a declaration, so Foundation never registers it. Declare it in service_principals.yml.',
                    wrong=[None, 'Foundation can\'t register an SP it was never told about. Look one stage earlier.', 'Entra ID was checked: it exists there.']),
                ask('Now it\'s declared, and Foundation shows a finished proposed run. The Service plan still fails. What next?', ['Ask for evidence that Foundation was applied', 'Re-run the Service plan until it passes', 'Recreate the SP in Entra ID'], answer=0,
                    clue='A proposed run is a preview.',
                    why='Finished and proposed only means planning worked. Ask the platform owner for the applied run, or the account showing the SP.',
                    wrong=[None, 'Re-running changes nothing if the earlier stage isn\'t done, and hides the cause.', 'Never change identities to make an error go away.']),
                fix('Declare the service principal so Foundation picks it up.',
                    file='config/UAT/team-sales/service_principals.yml',
                    start="""servicePrincipals:
  - name: sp-sales-reporting-uat
    workspace_access: true
""",
                    answer="""servicePrincipals:
  - name: sp-sales-reporting-uat
    workspace_access: true
  - name: sp-sales-etl-uat
    workspace_access: true
""",
                    rules={'path': 'servicePrincipals', 'required': ['name'], 'allowed': ['name', 'workspace_access'], 'types': {'name': 'str'}},
                    goal=[{'field': 'name', 'contains': 'sp-sales-etl-uat', 'message': 'sp-sales-etl-uat still isn\'t declared.'}],
                    clue='Add a second item to the list, shaped like the first one.',
                    why='Declared here, Foundation registers it in the Databricks account on its next apply; then Service can assign it to the workspace.'),
            ],
        ),
        starter="""def next_check(facts):
    # your code here
    pass
""",
        solution="""STAGES = [
    ("same_commit", "commit"),
    ("in_entra", "entra"),
    ("declared", "declare"),
    ("foundation_applied", "foundation"),
    ("assigned", "assign"),
]

def next_check(facts):
    for fact, step in STAGES:
        if not facts[fact]:
            return step
    return "name or scope"
""",
        cases=[
            case({'same_commit': True, 'in_entra': True, 'declared': False, 'foundation_applied': False, 'assigned': False}, expected='declare', sample=True),
            case({'same_commit': False, 'in_entra': True, 'declared': True, 'foundation_applied': True, 'assigned': True}, expected='commit'),
            case({'same_commit': True, 'in_entra': False, 'declared': True, 'foundation_applied': False, 'assigned': False}, expected='entra'),
            case({'same_commit': True, 'in_entra': True, 'declared': True, 'foundation_applied': False, 'assigned': False}, expected='foundation'),
            case({'same_commit': True, 'in_entra': True, 'declared': True, 'foundation_applied': True, 'assigned': False}, expected='assign'),
            case({'same_commit': True, 'in_entra': True, 'declared': True, 'foundation_applied': True, 'assigned': True}, expected='name or scope'),
        ],
        guided="""STAGES = [
    ("same_commit", "commit"),
    ("in_entra", "entra"),
    ("declared", "declare"),
    ("foundation_applied", "foundation"),
    ("assigned", "assign"),
]

def next_check(facts):
    # Replace every ___ with real code, then run the tests.
    for fact, step in STAGES:
        if ___:
            return step
    return ___
""",
        fills=['not facts[fact]', '"name or scope"'],
        concepts=[
            [
                'A list of pairs',
                'Each item can hold two things in round brackets, and the loop can name both.',
                """for key, word in [("a", "first"), ("b", "second")]:
    print(key, word)""",
            ],
            [
                'Return inside a loop',
                '`return` inside a loop stops the whole function at once: perfect for "the first one that...".',
                """def first_even(xs):
    for x in xs:
        if x % 2 == 0:
            return x
    return None""",
            ],
        ],
        byhand='Same commit: yes. In Entra ID: yes. Declared: no. Stop there and return "declare". The later stages don\'t matter yet: Foundation can\'t register an SP it was never told about.',
        why='At most five checks, in order.',
        gotchas=[
            [
                'Proposed is not applied',
                'A finished proposed run in Spacelift is a preview. Ask for the applied run, or the account showing the SP.',
            ],
            [
                "Don't fix blindly",
                'Never reset state, recreate identities or rerun a plan over and over to make an error go away. Find the missing stage and send the evidence to the platform owner.',
            ],
        ],
    ),
)

lesson(MODULE, 'ai_unstuck',
    title='Getting unstuck with AI, safely',
    learn=[
        "AI assistants like GitHub Copilot or an enterprise ChatGPT are good at three things here: **explaining** an unfamiliar term or error, **tracing** a name across files (YAML, then the runbook, then the module), and **suggesting checks**. They are not evidence. Anything they say is a lead until you've seen it yourself.",
        "A good prompt gives the AI what a person would need: **the run** (stack, environment, run link), **the first error** (a short excerpt, not the whole log), **the repo and the commit the run used**, and the rules: **read-only**, link every source, mark guesses as guesses, give one safe next check, and don't edit or deploy anything.",
        "Then check the answer against **three rules**. *Version*: does it read the same commit as the run, not today's main branch? *Evidence*: does each claim point at a file and line you can open, and does that line really say it? *Safety*: did you paste anything secret, and does it suggest changing something without approval?",
        "Never paste secrets, tokens, keys, state files or whole logs with credentials in them. And never let an assistant change infrastructure for you: re-running a plan, resetting state or recreating an identity to make an error go away hides the cause.",
    ],
    example=example('A prompt for an unfamiliar Spacelift failure', """I am new to Databricks IaC. Investigate READ-ONLY.
Run: dbx-service-uat, run 4182 (UAT)
First error: Cannot find service principal: sp-sales-etl-uat
Config repo and commit: config-repo @ 300d269 (the run's commit)
Explain the error plainly. Trace YAML -> check -> runbook -> module -> provider.
Link each source. Mark guesses as guesses.
Give one safe next check. Do not edit or deploy."""),
    check=question(
        'An AI assistant says the service principal "must be registered, because it is declared in service_principals.yml on main". What is wrong with relying on that?',
        [
            'Nothing: it names the file',
            'It read main, not the run\'s commit, and a declaration doesn\'t prove Foundation registered it',
            'It should have suggested deleting and recreating the SP',
        ],
        answer=1,
        why='Two of the three rules fail: the version (main, not the run\'s commit) and the evidence (a name in YAML isn\'t proof that an earlier stage ran). Recreating identities would break the safety rule.',
    ),
    angle=angle(
        pattern='Give it the facts, check its claims',
        text='The big idea: an AI assistant is a fast reader, not a witness. You give it what a person would need (the run, the first error, the repo and the commit, read-only), then treat every claim as a lead until you have seen the file yourself, at the run\'s commit. Your code checks a prompt before it is sent: it lists what is missing, in a fixed order, and flags anything that looks like a secret. It is like briefing a new colleague: give them the facts and the ground rules, then check their findings before you act.',
        say="\"I give the AI the run, the first error and the [[commit|branch name|state file::The exact version the failed run used.]] the run used, and tell it to stay read-only. Then I check every claim against the [[file|chat|summary::Open the source it points at, yourself.]] at that commit, and I never paste [[secrets|error messages|run links::Tokens, keys and passwords stay out.]].\"",
        classic=None,
    ),
    stack=stack('A prompt for reviewing a config pull request', """Review this Databricks configuration PR READ-ONLY: <PR link>.
Explain each important YAML change in plain language.
Find where the runbook and modules read each changed field;
say which are transformed, defaulted or dropped.
Call out permissions, destruction, dependencies and validation.
Link evidence. Do not merge, apply or change any file."""),
    exercise=exercise(
        title='Is This Prompt Ready?',
        topic='iac-review',
        difficulty='easy',
        fn='prompt_gaps',
        prompt="""Your function gets `prompt`, the text you are about to send to an AI assistant about a failed run.

Return a list of what is missing or wrong, in this order (compare in lower case):

- no `"read-only"` in it -> `"say read-only"`
- no `"run"` in it -> `"name the run"`
- no `"error"` in it -> `"add the first error"`
- no `"commit"` in it -> `"add the commit"`
- any of `"password"`, `"token"`, `"secret"`, `"private key"` in it -> `"remove secrets"`

A ready prompt returns `[]`.""",
        pattern='Check each required fact in a fixed order, then look for anything secret.',
        target='a few checks on one string',
        realworld="Platform teams that allow AI assistants on infrastructure ask for exactly this: read-only questions with the run, the first error and the commit, and no secrets. A prompt missing the commit is the most common reason an assistant explains the wrong version of the code.",
        practice=practice(
            intro='Build a good prompt for a failed run, then check what the AI says, the way the platform team\'s guidance asks.',
            explain='You gave the assistant the facts a person would need and the read-only rule, kept secrets out, and then checked its claims against the three rules: the same version as the run, evidence you have seen yourself, and nothing changed without approval.',
            asks=[
                ask('What goes in the commit line?', ['The commit the failed run used', 'Today\'s main branch', 'The Terraform state file'], answer=0,
                    evidence=evidence('prompt', title='Your prompt', text="""I am new to Databricks IaC. Investigate READ-ONLY.
Run: dbx-service-uat, run 4182 (UAT)
First error: Cannot find service principal: sp-sales-etl-uat
Config repo and commit: ___
Trace YAML -> check -> runbook -> module -> provider.
Link each source. Mark guesses as guesses.
Give one safe next check. Do not edit or deploy."""),
                    clue='The assistant must read the same version of the code that the run did.',
                    why='The run planned one exact commit. If the assistant reads main, it may explain code that has changed since.',
                    wrong=[None, 'Main may have moved on since the run. Which version did the run use?', 'Never paste state: it can hold secrets, and it isn\'t the code.']),
                ask('Can you send this?', ['Yes: more detail helps', 'No: take the secret out first', 'Only to Copilot, not ChatGPT'], answer=1,
                    evidence=evidence('code', title='Part of the log you were about to paste', text="""Initializing provider "azurerm"...
  ARM_CLIENT_ID     = 9a1c...
  ARM_CLIENT_SECRET = Qx8~kD2...
Error: Cannot find service principal: sp-sales-etl-uat"""),
                    clue='Look for anything that would let someone sign in.',
                    why='A client secret lets anyone act as that identity. Send only the first error, redacted.',
                    wrong=['Detail helps, but not a credential.', None, 'No assistant should get secrets, whichever one it is.']),
                ask('What\'s wrong with this answer?', ['Nothing: it names the file', 'Wrong version, and a guess about Foundation', 'It should delete the SP first'], answer=1,
                    evidence=evidence('claim', text='"The SP is declared in `service_principals.yml` on **main**, so Foundation must have registered it. **Re-run the Service plan** to fix it."'),
                    clue='Which commit did the run use? And does a declaration prove an earlier stage ran?',
                    why='It read main instead of the run\'s commit, it guessed that Foundation ran, and re-running a plan isn\'t a fix.',
                    wrong=['Naming a file isn\'t enough: check the version and whether it\'s evidence or a guess.', None, 'Deleting identities would break the safety rule.']),
                ask('Can you rely on this one?', ['Yes, once you open that file at that commit and see the line', 'Yes: it cites a file, so it\'s true', 'No: never trust an AI answer'], answer=0,
                    evidence=evidence('claim', text='"In `Service/parsing_teams.tf` at commit 300d269, the runbook adds `CAN_MANAGE` for `owner_group` (the `team_workspace_folders` block)."'),
                    clue='A good claim points somewhere you can check yourself.',
                    why='This is a good answer: right commit, an exact place to look. It becomes evidence when you have read the line yourself.',
                    wrong=[None, 'A citation is a lead, not proof, until you\'ve read it.', 'A precise, checkable claim is useful: check it, don\'t throw it away.']),
            ],
        ),
        starter="""def prompt_gaps(prompt):
    # your code here
    pass
""",
        solution="""def prompt_gaps(prompt):
    text = prompt.lower()
    gaps = []
    if "read-only" not in text:
        gaps.append("say read-only")
    if "run" not in text:
        gaps.append("name the run")
    if "error" not in text:
        gaps.append("add the first error")
    if "commit" not in text:
        gaps.append("add the commit")
    if any(word in text for word in ("password", "token", "secret", "private key")):
        gaps.append("remove secrets")
    return gaps
""",
        cases=[
            case('Investigate READ-ONLY. Run: dbx-service-uat 4182. First error: Cannot find service principal. Commit: 300d269.', expected=[], sample=True),
            case('Why does my plan fail? Error: Cannot find service principal.', expected=['say read-only', 'name the run', 'add the commit']),
            case('Read-only please. Run 4182, error below, commit 300d269. ARM_CLIENT_SECRET = Qx8', expected=['remove secrets']),
            case('READ-ONLY. Run 4182 at commit 300d269 failed.', expected=['add the first error']),
            case('', expected=['say read-only', 'name the run', 'add the first error', 'add the commit']),
        ],
        guided="""def prompt_gaps(prompt):
    # Replace every ___ with real code, then run the tests.
    text = prompt.lower()
    gaps = []
    if "read-only" not in text:
        gaps.append("say read-only")
    if "run" not in text:
        gaps.append("name the run")
    if "error" not in text:
        gaps.append("add the first error")
    if ___:
        gaps.append("add the commit")
    # Anything that looks secret has to go before you send it.
    if any(word in text for word in ___):
        gaps.append("remove secrets")
    return gaps
""",
        fills=['"commit" not in text', '("password", "token", "secret", "private key")'],
        concepts=[
            [
                'lower()',
                '`text.lower()` makes the comparison ignore capitals: "READ-ONLY" and "read-only" match.',
                '"READ-ONLY".lower()   # \'read-only\'',
            ],
            [
                'in on a string',
                '`"run" in text` asks whether those letters appear anywhere in the text.',
                '"run" in "run 4182"   # True',
            ],
            [
                'any()',
                '`any(...)` is True if at least one item is True: here, if any secret word appears.',
                'any(w in "a token" for w in ("password", "token"))   # True',
            ],
        ],
        byhand='The sample, in lower case, has "read-only", "run", "error" and "commit", and none of the secret words. Nothing is missing: return [].',
        why='Five checks on one lower-cased string.',
        gotchas=[
            [
                'A citation is a lead, not proof',
                'Open the file at the run\'s commit and read the line before you repeat what the assistant said.',
            ],
            [
                'Never let it act',
                'Assistants suggest re-running, resetting state or recreating identities. Those hide the cause: find the missing stage instead.',
            ],
        ],
    ),
)

planned(MODULE, 'which_repo', 'Which repo do I change?', 'A request comes in: is it YAML in the config repo, the runbook, a module, or a question for the platform owner?')
planned(MODULE, 'promote_upgrade', 'Upgrade a module through DEV, UAT and PROD', 'Bump a module or provider version and promote it one environment at a time, with a plan reviewed at each step.')
planned(MODULE, 'evidence_note', 'What to send the platform owner', 'The stack, the run, the first error, the YAML and runbook links, and the decision you need.')
