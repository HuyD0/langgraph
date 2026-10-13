"""How the platform repos fit together: YAML in the config repo, the Terraform runbook that reads
it, the modules and providers it calls, and the Spacelift stacks that run it. All names are invented."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, case, example, exercise, lesson, module, planned, question, stack

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

planned(MODULE, 'which_repo', 'Which repo do I change?', 'A request comes in: is it YAML in the config repo, the runbook, a module, or a question for the platform owner?')
planned(MODULE, 'promote_upgrade', 'Upgrade a module through DEV, UAT and PROD', 'Bump a module or provider version and promote it one environment at a time, with a plan reviewed at each step.')
planned(MODULE, 'run_states', 'Proposed, applied, failed: reading a Spacelift run', 'What each run state proves, and what it doesn\'t.')
planned(MODULE, 'evidence_note', 'What to send the platform owner', 'The stack, the run, the first error, the YAML and runbook links, and the decision you need.')
