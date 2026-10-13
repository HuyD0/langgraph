"""Databricks building blocks: Compute, runtimes, jobs, bundles, tags and what they cost."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack, source

MODULE = module('workspace', 'Databricks building blocks', 'Compute, runtimes, jobs, bundles, tags and what they cost.')

lesson(MODULE, 'pick_compute',
    title='Which compute for which work',
    checked='2026-10-12',
    sources=[source('Compute', 'https://docs.databricks.com/aws/en/compute/'), source('Serverless compute', 'https://docs.databricks.com/aws/en/compute/serverless/')],
    learn=[
        '**Compute** is the machines that run your code. Databricks bills it in **DBUs** (Databricks Units): a unit of processing time. Your bill is the DBUs used times a price per DBU, and that price depends on the kind of compute.',
        '**All-purpose compute** (also called classic compute) is a cluster you start, share and work in from notebooks. **Jobs compute** is created for one job run and shut down when the run ends. It costs less per DBU than all-purpose.',
        '**Serverless compute** means Databricks runs the machines for you. It starts in seconds and there is nothing to size. It works for notebooks, jobs and pipelines.',
        'A **SQL warehouse** runs SQL, dashboards and Genie (ask questions of your data in plain words). A serverless SQL warehouse is the recommended kind.',
        "Serverless doesn't take **init scripts** (a script that sets up each machine as it starts) or other custom machine setup. Work that needs a GPU (a chip built for training models) usually means classic compute too.",
    ],
    example=example('Matching work to compute', """# The work                         -> compute
# SQL for a dashboard              -> SQL warehouse (serverless)
# Exploring data in a notebook     -> serverless
# A scheduled job, plain Python    -> serverless
# A notebook that needs a GPU      -> all-purpose (classic, GPU machine)
# A job that needs an init script  -> jobs compute (classic)"""),
    check=question(
        'A nightly job needs an init script that installs a company certificate on every machine. Which compute fits?',
        ['Serverless compute', 'Jobs compute', 'A SQL warehouse'],
        answer=1,
        why="Serverless doesn't run init scripts, so it needs classic compute. Jobs compute is classic, made just for the run and cheaper per DBU than all-purpose.",
    ),
    angle=angle(
        pattern='Rules in order, first match wins',
        text='The big idea: the kind of work and its special needs decide the compute. Your code goes through the workloads one by one and asks questions in a fixed order. Is it SQL? Then a SQL warehouse, whatever else it needs. If not, does it need a GPU or an init script? Then classic compute: all-purpose for a notebook, jobs compute for a job. Anything left goes to serverless. The order matters: the first rule that fits decides.',
        say='"I check SQL first, then special machine needs, and default the rest to serverless. Classic compute only when serverless can\'t do the job, and jobs compute rather than all-purpose for anything scheduled."',
        classic=None,
    ),
    stack=stack('Terraform: a serverless SQL warehouse and a job on jobs compute', """resource "databricks_sql_endpoint" "bi" {
  name                      = "bi-serverless"
  cluster_size              = "Small"
  enable_serverless_compute = true
  auto_stop_mins            = 10
}

# Jobs compute: a new cluster for each
# run, gone when the run ends.
resource "databricks_job" "nightly_load" {
  name = "nightly-load"
  job_cluster {
    job_cluster_key = "main"
    new_cluster {
      spark_version = "15.4.x-scala2.12"
      node_type_id  = "Standard_D4ds_v5"
      num_workers   = 2
      init_scripts {
        workspace { destination = "/Shared/init/certs.sh" }
      }
    }
  }
  task {
    task_key        = "load"
    job_cluster_key = "main"
    notebook_task { notebook_path = "/Workspace/etl/load" }
  }
}"""),
    exercise=exercise(
        title='Pick the Compute',
        topic='compute',
        difficulty='easy',
        fn='pick_compute',
        prompt="""`workloads` is a list of work to place. Each one is a dict like `{"name": "nightly_load", "kind": "job", "needs_gpu": False, "init_script": True}`.

`kind` is `"sql"`, `"notebook"` or `"job"`. `needs_gpu` and `init_script` are True or False.

Pick the compute for each one, checking in this order:

- `kind` is `"sql"`: `"sql warehouse"`.
- Otherwise, if it needs a GPU or an init script: `"all-purpose"` for a notebook, `"jobs compute"` for a job.
- Otherwise: `"serverless"`.

Return a list of `[name, choice]` pairs, in the same order as `workloads`.""",
        pattern='Walk the list once. For each item, an if / elif / else chain where the first rule that fits decides.',
        target='one pass over the workloads',
        realworld='Platform teams write this down as a short guide for new users, and back it up with compute policies. The costly mistake it prevents is running scheduled jobs on an all-purpose cluster, which pays the higher all-purpose price per DBU for work that jobs compute or serverless would do for less.',
        starter="""def pick_compute(workloads):
    # your code here
    pass
""",
        solution="""def pick_compute(workloads):
    picks = []
    for w in workloads:
        if w["kind"] == "sql":
            choice = "sql warehouse"
        elif w["needs_gpu"] or w["init_script"]:
            if w["kind"] == "notebook":
                choice = "all-purpose"
            else:
                choice = "jobs compute"
        else:
            choice = "serverless"
        picks.append([w["name"], choice])
    return picks
""",
        cases=[
            case([
                {'name': 'sales_dashboard', 'kind': 'sql', 'needs_gpu': False, 'init_script': False},
                {'name': 'explore_returns', 'kind': 'notebook', 'needs_gpu': False, 'init_script': False},
                {'name': 'train_vision', 'kind': 'notebook', 'needs_gpu': True, 'init_script': False},
                {'name': 'nightly_load', 'kind': 'job', 'needs_gpu': False, 'init_script': True},
            ], expected=[
                ['sales_dashboard', 'sql warehouse'],
                ['explore_returns', 'serverless'],
                ['train_vision', 'all-purpose'],
                ['nightly_load', 'jobs compute'],
            ], sample=True),
            case([], expected=[]),
            case([
                {'name': 'genie_sales', 'kind': 'sql', 'needs_gpu': True, 'init_script': True},
            ], expected=[['genie_sales', 'sql warehouse']]),
            case([
                {'name': 'hourly_ingest', 'kind': 'job', 'needs_gpu': False, 'init_script': False},
                {'name': 'weekly_finetune', 'kind': 'job', 'needs_gpu': True, 'init_script': False},
            ], expected=[['hourly_ingest', 'serverless'], ['weekly_finetune', 'jobs compute']]),
            case([
                {'name': 'geo_notebook', 'kind': 'notebook', 'needs_gpu': False, 'init_script': True},
                {'name': 'quick_look', 'kind': 'notebook', 'needs_gpu': False, 'init_script': False},
                {'name': 'gpu_batch', 'kind': 'job', 'needs_gpu': True, 'init_script': True},
            ], expected=[['geo_notebook', 'all-purpose'], ['quick_look', 'serverless'], ['gpu_batch', 'jobs compute']]),
        ],
        guided="""def pick_compute(workloads):
    # Replace every ___ with real code, then run the tests.

    picks = []
    for w in workloads:
        # SQL always goes to a SQL warehouse.
        if w["kind"] == "sql":
            choice = "sql warehouse"

        # Step 1: True when it needs a GPU or an init script.
        elif ___:
            if w["kind"] == "notebook":
                # Step 2: classic compute for a notebook.
                choice = ___
            else:
                choice = "jobs compute"

        # Step 3: everything else.
        else:
            choice = ___

        picks.append([w["name"], choice])
    return picks
""",
        fills=['w["needs_gpu"] or w["init_script"]', '"all-purpose"', '"serverless"'],
        concepts=[
            [
                'if, elif, else',
                'Python tries each test from the top and runs only the first one that is True. `else` catches everything left.',
                """size = 7
if size > 10: label = 'big'
elif size > 5: label = 'medium'   # this one runs
else: label = 'small'""",
            ],
            [
                'Either one with or',
                '`a or b` is True when at least one side is True.',
                """raining = False
cold = True
raining or cold   # True""",
            ],
            [
                'A pair as a small list',
                '`[name, choice]` keeps two values together, and the result is a list of these pairs.',
                """pairs = []
pairs.append(['tea', 'hot'])   # [['tea', 'hot']]""",
            ],
        ],
        byhand='sales_dashboard is SQL: "sql warehouse". explore_returns is a notebook with no GPU and no init script: "serverless". train_vision is a notebook that needs a GPU: "all-purpose". nightly_load is a job with an init script: "jobs compute". Return the four pairs in that order.',
        why='One pass, with a few quick checks for each workload.',
        gotchas=[
            [
                "Serverless isn't always cheaper per DBU",
                'Its price per DBU can be higher than classic, but it includes the machines, starts in seconds and stops quickly when idle. On classic compute in Azure you also pay Azure for the virtual machines, on a separate bill, and for the minutes spent starting up and sitting idle.',
            ],
            [
                'Scheduled work on all-purpose',
                'A job pointed at an existing all-purpose cluster runs at the all-purpose price, and keeps that cluster busy for everyone else. Give jobs their own jobs compute or run them on serverless.',
            ],
        ],
    ),
)

lesson(MODULE, 'unsupported_runtimes',
    title='Databricks Runtime versions',
    checked='2026-10-12',
    sources=[source('Databricks Runtime release notes', 'https://docs.databricks.com/aws/en/release-notes/runtime/')],
    learn=[
        'The **Databricks Runtime** (DBR) is the software image on the compute: Spark, Python and a set of libraries, each at a fixed version. You pick it when you create classic compute.',
        '**LTS** means long-term support: a version that gets fixes for about three years. Pick LTS for anything that runs on a schedule.',
        'The **ML runtime** adds machine learning libraries on top. Terraform and the API name a runtime with a `spark_version` string: `"15.4.x-scala2.12"` is 15.4, `"16.4.x-cpu-ml-scala2.13"` is the 16.4 ML runtime, `"14.3.x-gpu-ml-scala2.12"` is 14.3 ML for GPU machines.',
        'Support dates, as of October 2026: 12.2 LTS ended in March 2026 and 13.3 LTS in August 2026. 14.3 LTS is supported until February 2027 and 15.4 LTS until August 2027. The docs keep a table for every version.',
        'Serverless picks and upgrades its runtime for you. Some features need a newer runtime: tables protected by ABAC (access rules driven by tags) need 16.4 or later on classic compute.',
    ],
    example=example('Reading spark_version', """"15.4.x-scala2.12"          # 15.4 LTS, standard
"16.4.x-cpu-ml-scala2.13"   # 16.4 LTS, ML runtime
"14.3.x-gpu-ml-scala2.12"   # 14.3 LTS, ML runtime for GPU
# The version is the part before ".x\""""),
    check=question(
        'It is October 2026 and a cluster runs `13.3.x-scala2.12`. What should you do?',
        [
            'Nothing, LTS versions are supported forever',
            'Move it to a supported LTS such as 15.4 or 16.4, because 13.3 LTS support ended in August 2026',
            'Switch the cluster off and on again to pick up fixes',
        ],
        answer=1,
        why="Once support ends there are no more fixes, security ones included. Restarting doesn't change the version; you have to change `spark_version`.",
    ),
    angle=angle(
        pattern='Cut out the key, then check membership',
        text='The big idea: every cluster names its runtime in one string, so you can check a whole workspace against the supported list. Your code goes through the clusters in order. For each one it cuts the version out of `spark_version` by splitting the text at `".x"` and keeping the first piece. Then it asks one question: is that version in the supported list? If not, the cluster\'s name goes into the result.',
        say='"I take the version from each cluster\'s spark_version, the part before .x, and flag every cluster whose version isn\'t on the supported list."',
        classic='two_sum',
    ),
    stack=stack('Terraform: always pick the latest LTS', """data "databricks_spark_version" "lts" {
  long_term_support = true
}

data "databricks_spark_version" "lts_ml" {
  long_term_support = true
  ml                = true
}

resource "databricks_cluster" "shared" {
  cluster_name            = "etl-shared"
  spark_version           = data.databricks_spark_version.lts.id
  node_type_id            = "Standard_D4ds_v5"
  num_workers             = 2
  autotermination_minutes = 30
}"""),
    exercise=exercise(
        title='Find Old Runtimes',
        topic='runtimes',
        difficulty='easy',
        fn='unsupported_runtimes',
        prompt="""Your function gets two things:

- `clusters`: a list of dicts like `{"name": "etl-shared", "spark_version": "15.4.x-scala2.12"}`.
- `supported`: the runtime versions still supported, like `["14.3", "15.4", "16.4", "17.3"]`.

A cluster's version is the text before `".x"` in its `spark_version`. So `"16.4.x-cpu-ml-scala2.13"` is version `"16.4"`.

Return the `name` of every cluster whose version is not in `supported`, in the same order as `clusters`.""",
        pattern='Filter: split each string to get the key, then keep the ones not in the list.',
        target='one pass over the clusters',
        realworld='Before a runtime reaches end of support, a platform team lists every cluster and job still on it and asks the owners to move. The real list comes from the Clusters API or `databricks clusters list`, and the `system.compute.clusters` table keeps each cluster\'s `dbr_version` too.',
        starter="""def unsupported_runtimes(clusters, supported):
    # your code here
    pass
""",
        solution="""def unsupported_runtimes(clusters, supported):
    old = []
    for c in clusters:
        version = c["spark_version"].split(".x")[0]
        if version not in supported:
            old.append(c["name"])
    return old
""",
        cases=[
            case([
                {'name': 'etl-shared', 'spark_version': '15.4.x-scala2.12'},
                {'name': 'old-reports', 'spark_version': '13.3.x-scala2.12'},
                {'name': 'ml-train', 'spark_version': '16.4.x-cpu-ml-scala2.13'},
                {'name': 'legacy-gpu', 'spark_version': '12.2.x-gpu-ml-scala2.12'},
            ], ['14.3', '15.4', '16.4', '17.3'], expected=['old-reports', 'legacy-gpu'], sample=True),
            case([], ['15.4'], expected=[]),
            case([
                {'name': 'vision-gpu', 'spark_version': '14.3.x-gpu-ml-scala2.12'},
                {'name': 'new-etl', 'spark_version': '17.3.x-scala2.13'},
            ], ['14.3', '15.4', '16.4', '17.3'], expected=[]),
            case([
                {'name': 'a', 'spark_version': '15.4.x-scala2.12'},
                {'name': 'b', 'spark_version': '16.4.x-scala2.12'},
            ], [], expected=['a', 'b']),
            case([
                {'name': 'etl', 'spark_version': '15.4.x-scala2.12'},
                {'name': 'ml', 'spark_version': '16.4.x-cpu-ml-scala2.13'},
            ], ['5.4', '16.4'], expected=['etl']),
        ],
        guided="""def unsupported_runtimes(clusters, supported):
    # Replace every ___ with real code, then run the tests.

    old = []
    for c in clusters:
        # Step 1: the text before ".x" in spark_version.
        version = ___

        # Step 2: True when the version isn't supported.
        if ___:
            old.append(c["name"])

    return old
""",
        fills=['c["spark_version"].split(".x")[0]', 'version not in supported'],
        concepts=[
            [
                'Splitting text',
                '`text.split(sep)` cuts the text wherever `sep` appears and gives a list of the pieces. `[0]` is the first piece.',
                """'tea-with-milk'.split('-')      # ['tea', 'with', 'milk']
'tea-with-milk'.split('-')[0]   # 'tea'""",
            ],
            [
                'not in',
                '`x not in a_list` is True when x is nowhere in the list. It matches whole items, not parts of them.',
                """'5.4' not in ['15.4']   # True: '5.4' is not the item '15.4'""",
            ],
        ],
        byhand='etl-shared: "15.4" is supported, skip. old-reports: "13.3" is not, keep. ml-train: "16.4" is supported, skip. legacy-gpu: "12.2" is not, keep. Return ["old-reports", "legacy-gpu"].',
        why='One pass, with a split and a check against a short list for each cluster.',
        gotchas=[
            [
                '"Latest LTS" moves under you',
                'The `databricks_spark_version` data source picks the newest LTS when Terraform plans. When a new LTS comes out, the next plan changes every cluster that uses it. That is usually what you want, but it should be a change you notice, not a surprise.',
            ],
            [
                'Jobs hide runtimes too',
                "A job's `new_cluster` has its own `spark_version`. Checking only all-purpose clusters misses every scheduled job still on an old runtime.",
            ],
        ],
    ),
)

lesson(MODULE, 'policy_violations',
    title='Cluster policies',
    checked='2026-10-12',
    sources=[source('Compute policy reference', 'https://docs.databricks.com/aws/en/admin/clusters/policy-definition')],
    learn=[
        'A **compute policy** (older docs say cluster policy) limits what people can set when they create compute. Each rule targets one setting.',
        'A rule can **fix** a value, allow only values from an **allowlist**, or keep a number in a **range**. Typical targets are `autotermination_minutes`, `node_type_id` (the machine size) and `custom_tags.team`.',
        'This keeps cost and tags in line without anyone checking by hand. Users need the CAN_USE permission on a policy to create compute with it.',
    ],
    example=example('A real policy definition (JSON)', """{
  "autotermination_minutes": {"type": "range", "maxValue": 60},
  "node_type_id": {
    "type": "allowlist",
    "values": ["Standard_D4ds_v5", "Standard_D8ds_v5"]
  },
  "custom_tags.team": {"type": "fixed", "value": "data"}
}"""),
    check=question(
        'A policy has `"autotermination_minutes": {"type": "range", "maxValue": 60}`. Someone sets it to 0. Does the policy stop them?',
        [
            'Yes, 0 means never stop, which is longer than 60',
            "No, 0 is a number between nothing and 60, so it passes. Add a minValue too",
            'Yes, ranges never allow 0',
        ],
        answer=1,
        why='0 means "never auto-terminate", but the rule only compares numbers. With no `minValue`, 0 is inside the range. Set `"minValue": 10` as well.',
    ),
    angle=angle(
        pattern='Look up each rule, check by its type',
        text='The big idea: a policy is a set of rules, one per setting, and each rule type has its own simple test. Your code goes through the policy\'s rules in order. For each one it first looks up the setting in the cluster. Missing breaks the rule. Otherwise it checks by type: fixed means equal, allowlist means in the list, range means not below `minValue` and not above `maxValue`, checking only the limits that are given.',
        say='"I check every policy rule against the cluster: a fixed value must match, an allowlist must contain it, a range must hold it. Missing settings break the rule too."',
        classic=None,
    ),
    stack=stack('Terraform: the policy, and who may use it', """resource "databricks_cluster_policy" "data_team" {
  name = "data-team-small"
  definition = jsonencode({
    "autotermination_minutes" = {
      type = "range", minValue = 10, maxValue = 60
    }
    "node_type_id" = {
      type   = "allowlist"
      values = ["Standard_D4ds_v5", "Standard_D8ds_v5"]
    }
    "custom_tags.team" = { type = "fixed", value = "data" }
  })
}

resource "databricks_permissions" "data_team_policy" {
  cluster_policy_id = databricks_cluster_policy.data_team.id
  access_control {
    group_name       = "data-engineers"
    permission_level = "CAN_USE"
  }
}"""),
    exercise=exercise(
        title='Check Against the Policy',
        topic='policy',
        difficulty='medium',
        fn='policy_violations',
        prompt="""Your function gets two dicts:

- `cluster`: the settings someone wants, like `{"autotermination_minutes": 120, "node_type_id": "Standard_D4ds_v5", "custom_tags.team": "marketing"}`.
- `policy`: setting name to rule, like `{"autotermination_minutes": {"type": "range", "maxValue": 60}}`.

Names like `"custom_tags.team"` are plain keys: look them up directly in `cluster`.

A setting breaks its rule when:

- it is missing from `cluster`, or
- the rule is `"fixed"` and the value isn't equal to the rule's `"value"`, or
- the rule is `"allowlist"` and the value isn't in the rule's `"values"`, or
- the rule is `"range"` and the value is below `"minValue"` or above `"maxValue"`. Check only the limits the rule has.

Return the names of the settings that break the policy, in policy order.""",
        pattern='Go through the rules. For each, look up the setting, then pick the test by the rule\'s type.',
        target='one pass over the policy rules',
        realworld='Databricks runs these checks itself when someone creates compute with a policy. Writing them yourself is useful for reviewing cluster specs in Terraform or bundle code before they are applied, so a PR check fails early with a clear message.',
        starter="""def policy_violations(cluster, policy):
    # your code here
    pass
""",
        solution="""def policy_violations(cluster, policy):
    broken = []
    for name in policy:
        rule = policy[name]
        ok = name in cluster
        if ok:
            value = cluster[name]
            if rule["type"] == "fixed":
                ok = value == rule["value"]
            elif rule["type"] == "allowlist":
                ok = value in rule["values"]
            elif rule["type"] == "range":
                if "minValue" in rule and value < rule["minValue"]:
                    ok = False
                if "maxValue" in rule and value > rule["maxValue"]:
                    ok = False
        if not ok:
            broken.append(name)
    return broken
""",
        cases=[
            case(
                {'autotermination_minutes': 120, 'node_type_id': 'Standard_D4ds_v5', 'custom_tags.team': 'marketing'},
                {
                    'autotermination_minutes': {'type': 'range', 'maxValue': 60},
                    'node_type_id': {'type': 'allowlist', 'values': ['Standard_D4ds_v5', 'Standard_D8ds_v5']},
                    'custom_tags.team': {'type': 'fixed', 'value': 'data'},
                },
                expected=['autotermination_minutes', 'custom_tags.team'], sample=True),
            case(
                {'autotermination_minutes': 60, 'node_type_id': 'Standard_D8ds_v5', 'custom_tags.team': 'data'},
                {
                    'autotermination_minutes': {'type': 'range', 'maxValue': 60},
                    'node_type_id': {'type': 'allowlist', 'values': ['Standard_D4ds_v5', 'Standard_D8ds_v5']},
                    'custom_tags.team': {'type': 'fixed', 'value': 'data'},
                },
                expected=[]),
            case(
                {'node_type_id': 'Standard_E16ds_v5'},
                {
                    'autotermination_minutes': {'type': 'range', 'maxValue': 60},
                    'node_type_id': {'type': 'allowlist', 'values': ['Standard_D4ds_v5', 'Standard_D8ds_v5']},
                    'custom_tags.team': {'type': 'fixed', 'value': 'data'},
                },
                expected=['autotermination_minutes', 'node_type_id', 'custom_tags.team']),
            case(
                {'num_workers': 0, 'spark_version': '15.4.x-scala2.12'},
                {
                    'num_workers': {'type': 'range', 'minValue': 1, 'maxValue': 8},
                    'spark_version': {'type': 'fixed', 'value': '15.4.x-scala2.12'},
                },
                expected=['num_workers']),
            case(
                {'autotermination_minutes': 0, 'num_workers': 8},
                {
                    'autotermination_minutes': {'type': 'range', 'minValue': 10, 'maxValue': 60},
                    'num_workers': {'type': 'range', 'minValue': 1, 'maxValue': 8},
                },
                expected=['autotermination_minutes']),
            case({}, {}, expected=[]),
        ],
        guided="""def policy_violations(cluster, policy):
    # Replace every ___ with real code, then run the tests.

    broken = []
    for name in policy:
        rule = policy[name]

        # A missing setting breaks the rule.
        ok = name in cluster

        if ok:
            value = cluster[name]
            if rule["type"] == "fixed":
                # Step 1: True when value equals the rule's value.
                ok = ___
            elif rule["type"] == "allowlist":
                # Step 2: True when value is in the rule's values.
                ok = ___
            elif rule["type"] == "range":
                if "minValue" in rule and value < rule["minValue"]:
                    ok = False
                # Step 3: too big, when the rule has a maxValue.
                if "maxValue" in rule and ___:
                    ok = False

        if not ok:
            broken.append(name)
    return broken
""",
        fills=['value == rule["value"]', 'value in rule["values"]', 'value > rule["maxValue"]'],
        concepts=[
            [
                'Looping over a dict',
                '`for key in a_dict` gives each key in the order it was added. `a_dict[key]` gets its value.',
                """prices = {'tea': 2, 'cake': 4}
for item in prices:
    print(item, prices[item])   # tea 2, then cake 4""",
            ],
            [
                'Is the key there?',
                '`key in a_dict` is True when the dict has that key. Check before you read, or a missing key stops the program.',
                """pet = {'name': 'Rex'}
'age' in pet   # False""",
            ],
            [
                'Keeping a yes or no and changing it',
                'Start with `ok` as True or False, and set it to False whenever a test fails.',
                """ok = True
if 7 > 5: ok = False
ok   # False""",
            ],
        ],
        byhand='autotermination_minutes: 120 is above the max of 60, broken. node_type_id: "Standard_D4ds_v5" is in the allowlist, fine. custom_tags.team: "marketing" is not the fixed "data", broken. Return ["autotermination_minutes", "custom_tags.team"].',
        why='One pass over the rules; each check is a lookup and a comparison.',
        gotchas=[
            [
                'In Databricks, fixed values fill themselves in',
                "When someone creates compute with a policy, Databricks sets fixed values for them and can hide them from the form. This exercise checks a spec as written, the way a review of Terraform code would, so there a missing setting counts as broken.",
            ],
            [
                'More rule types',
                'Real policies also have `blocklist`, `regex` and `unlimited` types, plus `defaultValue`, `isOptional` and `hidden`. Start with fixed, allowlist and range; they cover most cost and tag rules.',
            ],
        ],
    ),
)

lesson(MODULE, 'skipped_tasks',
    title='Jobs: tasks that depend on each other',
    checked='2026-10-12',
    sources=[source('Lakeflow Jobs', 'https://docs.databricks.com/aws/en/jobs/'), source('Repair job failures', 'https://docs.databricks.com/aws/en/jobs/repair-job-failures')],
    learn=[
        '**Lakeflow Jobs** (formerly Databricks Workflows) run your work on a schedule. A job has **tasks**, and `depends_on` says which tasks must finish before a task starts.',
        'Each task has a **Run if** condition. The default is "all succeeded": run only if every task it depends on succeeded.',
        "So when a task fails, every task downstream of it (depending on it, directly or through others) doesn't run. The run marks them as upstream failed, not as failures of their own.",
        'A **repair run** reruns only the failed tasks and the ones that were skipped because of them, not the whole job. Run production jobs as a **service principal** (an identity for software, not a person), so they keep working when someone leaves.',
    ],
    example=example('A job as a chain', """ingest -> clean -> features -> report
       \\-> audit -----------/

clean fails:
  features: upstream failed (skipped)
  report:   upstream failed (skipped)
  audit:    runs, it only needs ingest"""),
    check=question(
        '`clean` failed and `features` and `report` were skipped. You fix the bug. What does a repair run do?',
        [
            'Reruns every task from the start',
            'Reruns clean, features and report, and keeps the earlier results of ingest and audit',
            'Reruns only clean',
        ],
        answer=1,
        why='A repair run picks up the failed task and everything skipped after it. Tasks that succeeded keep their results, which saves time and compute.',
    ),
    angle=angle(
        pattern='Spread through a list in order',
        text='The big idea: a failure spreads downstream, so you track which tasks are stopped. Your code starts a list of stopped tasks with only the failed one. Because each task comes after the tasks it depends on, one pass in order is enough. For each task it asks: does it depend on any stopped task? If yes, it is skipped. Add it to the result and to the stopped list, so the tasks after it see it too.',
        say='"I keep a list of stopped tasks, starting with the failed one. Going in order, any task that depends on a stopped task is skipped and joins the list."',
        classic='num_islands',
    ),
    stack=stack('A job in a bundle: depends_on and run_if', """resources:
  jobs:
    nightly_sales:
      name: nightly-sales
      tasks:
        - task_key: ingest
          notebook_task: {notebook_path: ../src/ingest.py}
        - task_key: clean
          depends_on: [{task_key: ingest}]
          notebook_task: {notebook_path: ../src/clean.py}
        - task_key: report
          depends_on: [{task_key: clean}]
          notebook_task: {notebook_path: ../src/report.py}
        # Runs only when something upstream failed.
        - task_key: page_on_call
          depends_on: [{task_key: report}]
          run_if: AT_LEAST_ONE_FAILED
          notebook_task: {notebook_path: ../src/alert.py}"""),
    exercise=exercise(
        title='Find the Skipped Tasks',
        topic='jobs',
        difficulty='medium',
        fn='skipped_tasks',
        prompt="""Your function gets two things:

- `tasks`: the job's tasks, each a dict like `{"task_key": "report", "depends_on": ["features", "audit"]}`. They are listed so that every task comes after the tasks it depends on.
- `failed`: the `task_key` of the task that failed.

With the default "all succeeded" rule, a task is skipped when it depends on the failed task, or on a task that was skipped, directly or through others.

Return the `task_key` of every skipped task, in the same order as `tasks`. The failed task itself is not skipped.""",
        pattern='Keep a list of stopped tasks. Walk the tasks in order; any task that depends on a stopped one is skipped and becomes stopped too.',
        target='one pass over the tasks',
        realworld='This is the "upstream failed" view on a job run page, and the set of tasks a repair run will rerun. Knowing it before you click tells you how much compute and time the repair will take.',
        starter="""def skipped_tasks(tasks, failed):
    # your code here
    pass
""",
        solution="""def skipped_tasks(tasks, failed):
    stopped = [failed]
    skipped = []
    for task in tasks:
        hit = False
        for key in task["depends_on"]:
            if key in stopped:
                hit = True
        if hit:
            skipped.append(task["task_key"])
            stopped.append(task["task_key"])
    return skipped
""",
        cases=[
            case([
                {'task_key': 'ingest', 'depends_on': []},
                {'task_key': 'clean', 'depends_on': ['ingest']},
                {'task_key': 'audit', 'depends_on': ['ingest']},
                {'task_key': 'features', 'depends_on': ['clean']},
                {'task_key': 'report', 'depends_on': ['features', 'audit']},
            ], 'clean', expected=['features', 'report'], sample=True),
            case([
                {'task_key': 'ingest', 'depends_on': []},
                {'task_key': 'clean', 'depends_on': ['ingest']},
                {'task_key': 'report', 'depends_on': ['clean']},
            ], 'report', expected=[]),
            case([
                {'task_key': 'ingest', 'depends_on': []},
                {'task_key': 'clean', 'depends_on': ['ingest']},
                {'task_key': 'audit', 'depends_on': ['ingest']},
                {'task_key': 'features', 'depends_on': ['clean']},
                {'task_key': 'report', 'depends_on': ['features', 'audit']},
            ], 'ingest', expected=['clean', 'audit', 'features', 'report']),
            case([], 'ingest', expected=[]),
            case([
                {'task_key': 'load_orders', 'depends_on': []},
                {'task_key': 'load_stores', 'depends_on': []},
                {'task_key': 'join', 'depends_on': ['load_orders']},
                {'task_key': 'store_report', 'depends_on': ['load_stores']},
                {'task_key': 'publish', 'depends_on': ['join']},
            ], 'load_orders', expected=['join', 'publish']),
        ],
        guided="""def skipped_tasks(tasks, failed):
    # Replace every ___ with real code, then run the tests.

    # Tasks that didn't succeed, starting with the failed one.
    stopped = [failed]
    skipped = []

    for task in tasks:
        hit = False
        for key in task["depends_on"]:
            # Step 1: True when this dependency is stopped.
            if ___:
                hit = True

        if hit:
            skipped.append(task["task_key"])
            # Step 2: tasks after this one must see it as stopped.
            ___

    return skipped
""",
        fills=['key in stopped', 'stopped.append(task["task_key"])'],
        concepts=[
            [
                'A loop inside a loop',
                'The inner loop runs fully for each turn of the outer loop. Here: for each task, look at each of its dependencies.',
                """for meal in ['lunch', 'dinner']:
    for dish in ['soup', 'bread']:
        print(meal, dish)   # 4 lines""",
            ],
            [
                'A flag',
                'Set `hit = False`, and switch it to True if any check matches. After the loop, the flag says whether anything matched.',
                """hit = False
for n in [3, 8, 2]:
    if n > 5: hit = True
hit   # True""",
            ],
            [
                'A list that grows as you go',
                'Appending to `stopped` inside the loop means later tasks see the new entries.',
                """seen = ['a']
seen.append('b')
'b' in seen   # True""",
            ],
        ],
        byhand='Stopped starts as [clean]. ingest depends on nothing: runs. clean is the failed one; its dependency ingest is not stopped. audit depends on ingest: runs. features depends on clean, which is stopped: skipped, and features joins stopped. report depends on features, now stopped: skipped. Return ["features", "report"].',
        why='One pass over the tasks, checking each dependency against the stopped list.',
        gotchas=[
            [
                'Run if can change who runs',
                'A task with `run_if: ALL_DONE` runs whether its upstream tasks succeeded or not, which is how clean-up tasks work. `AT_LEAST_ONE_FAILED` is for alerting. This exercise assumes the default for every task.',
            ],
            [
                'Retries come before skipping',
                "A task can retry on failure (`max_retries`). Downstream tasks only skip after the last retry fails, so a flaky task with retries may never stop the chain.",
            ],
        ],
    ),
)

lesson(MODULE, 'resolve_variables',
    title='Bundles: one source, many targets',
    checked='2026-10-12',
    sources=[source('Declarative Automation Bundles', 'https://docs.databricks.com/aws/en/dev-tools/bundles/'), source('Bundles release notes (the rename)', 'https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles')],
    learn=[
        '**Declarative Automation Bundles** (called Databricks Asset Bundles until March 2026, still "DABs") describe jobs, pipelines and other resources as code, in a `databricks.yml` file. Only the name changed: same `databricks bundle` commands, same files.',
        '`databricks bundle validate` checks the files, `databricks bundle deploy -t dev` creates or updates the resources in the dev **target**, and `databricks bundle run` starts a job. Targets are places to deploy to, usually dev and prod.',
        '**Variables** have defaults and are used as `${var.catalog}`. A target can set its own value, which wins over the default.',
        "`mode: development` puts your name in front of resource names, so people don't overwrite each other in dev. In prod, set `run_as` to a service principal so jobs don't run as a person.",
    ],
    example=example('Variables and targets in databricks.yml', """variables:
  catalog:
    default: dev_sales
  warehouse_id:
    description: SQL warehouse for reports

targets:
  dev:
    mode: development
    default: true
    variables:
      warehouse_id: 4f2a9c1e7b3d5a60
  prod:
    mode: production
    variables:
      catalog: prod_sales
      warehouse_id: 9b1d3e5f7a2c4e68
    run_as:
      service_principal_name: 6a1c2e3f-0b4d-4e5f-8a9b-1c2d3e4f5a6b"""),
    check=question(
        '`catalog` has a default of `dev_sales`, and the prod target sets it to `prod_sales`. What does `${var.catalog}` become in `deploy -t prod`?',
        ['dev_sales', 'prod_sales', 'An error, it is set twice'],
        answer=1,
        why="The target's value wins over the default. The default is what's used when nothing else sets it.",
    ),
    angle=angle(
        pattern='Layered lookup: specific value, then default',
        text="The big idea: one set of files deploys to many places, and each place fills in its own values. Your code goes through the declared variables. For each name it asks in order: does the target set it? Use that. Is there a default? Use that. Neither? Then it's missing. The missing names are sorted at the end, so the error message is the same every time.",
        say='"For each variable, the target value wins, then the default. Anything with neither is missing, and validate should fail on it before anything deploys."',
        classic=None,
    ),
    stack=stack('The bundle commands', """databricks bundle validate -t prod
databricks bundle deploy -t dev
databricks bundle run -t dev nightly_sales

# Set a variable for one command
databricks bundle deploy -t dev --var="catalog=sandbox_ana"

# Or with an environment variable
export BUNDLE_VAR_catalog=sandbox_ana"""),
    exercise=exercise(
        title='Fill In the Variables',
        topic='bundles',
        difficulty='medium',
        fn='resolve_variables',
        prompt="""Your function gets two dicts:

- `variables`: each declared variable and its default, like `{"catalog": "dev_sales", "warehouse_id": None}`. `None` means it has no default.
- `target`: the values the target sets, like `{"warehouse_id": "4f2a9c1e7b3d5a60"}`.

For each declared variable:

- If the target sets it, use the target's value.
- Otherwise, if it has a default, use the default.
- Otherwise it is missing.

Return `[resolved, missing]`. `resolved` is a dict of name to value, leaving the missing ones out. `missing` is a list of the missing names, sorted A to Z.""",
        pattern='Go through the declared names, check the more specific source first, and collect what falls through.',
        target='one pass over the variables',
        realworld='This is what `databricks bundle validate` works out for each target. A variable with no value fails validation, which is exactly where you want a missing warehouse ID or catalog name to show up: before anything is deployed.',
        starter="""def resolve_variables(variables, target):
    # your code here
    pass
""",
        solution="""def resolve_variables(variables, target):
    resolved = {}
    missing = []
    for name in variables:
        if name in target:
            resolved[name] = target[name]
        elif variables[name] is not None:
            resolved[name] = variables[name]
        else:
            missing.append(name)
    missing.sort()
    return [resolved, missing]
""",
        cases=[
            case(
                {'catalog': 'dev_sales', 'schema': 'forecast', 'warehouse_id': None, 'alert_email': None},
                {'catalog': 'prod_sales', 'warehouse_id': '4f2a9c1e7b3d5a60'},
                expected=[{'catalog': 'prod_sales', 'schema': 'forecast', 'warehouse_id': '4f2a9c1e7b3d5a60'}, ['alert_email']],
                sample=True),
            case({}, {}, expected=[{}, []]),
            case({'catalog': 'dev_sales', 'schema': 'raw'}, {}, expected=[{'catalog': 'dev_sales', 'schema': 'raw'}, []]),
            case(
                {'warehouse_id': None, 'catalog': None, 'node_type': 'Standard_D4ds_v5'},
                {},
                expected=[{'node_type': 'Standard_D4ds_v5'}, ['catalog', 'warehouse_id']]),
            case({'catalog': None}, {'catalog': 'prod_sales'}, expected=[{'catalog': 'prod_sales'}, []]),
        ],
        guided="""def resolve_variables(variables, target):
    # Replace every ___ with real code, then run the tests.

    resolved = {}
    missing = []

    for name in variables:
        # The target's value wins.
        if name in target:
            resolved[name] = target[name]

        # Step 1: True when this variable has a default.
        elif ___:
            resolved[name] = variables[name]

        # Step 2: neither, so it's missing.
        else:
            ___

    # Step 3: sort missing A to Z.
    ___
    return [resolved, missing]
""",
        fills=['variables[name] is not None', 'missing.append(name)', 'missing.sort()'],
        concepts=[
            [
                'None means "no value"',
                '`None` is Python\'s empty value. Check it with `is None` or `is not None`.',
                """phone = None
phone is None       # True
'tea' is not None   # True""",
            ],
            [
                'Adding to a dict',
                '`a_dict[key] = value` adds the key, or replaces its value if it is already there.',
                """order = {}
order['drink'] = 'tea'   # {'drink': 'tea'}""",
            ],
            [
                'Sorting a list in place',
                '`a_list.sort()` puts the items in order, A to Z for text. It changes the list itself.',
                """names = ['zoe', 'ana']
names.sort()   # names is now ['ana', 'zoe']""",
            ],
        ],
        byhand='catalog: the target sets "prod_sales", use it. schema: not in target, default "forecast". warehouse_id: the target sets it. alert_email: not in target, no default: missing. Return [{"catalog": "prod_sales", "schema": "forecast", "warehouse_id": "4f2a9c1e7b3d5a60"}, ["alert_email"]].',
        why='One pass over the variables, then a sort of the short missing list.',
        gotchas=[
            [
                'Command line beats target',
                'Values passed with `--var` or `BUNDLE_VAR_name` win over the target\'s value. Handy in dev, risky in CI: a stray environment variable can point a prod deploy at the wrong catalog.',
            ],
            [
                'Development mode is for dev only',
                '`mode: development` also pauses schedules and lets anyone with access deploy their own copy. Never use it for prod; `mode: production` adds checks, such as requiring a run_as identity that isn\'t a person.',
            ],
        ],
    ),
)

lesson(MODULE, 'tag_coverage',
    title='Why tagging matters',
    checked='2026-10-12',
    sources=[source('Serverless budget policies', 'https://docs.databricks.com/aws/en/admin/usage/budget-policies'), source('Billing system tables', 'https://docs.databricks.com/aws/en/admin/system-tables/billing')],
    learn=[
        '**Tags** are key-value labels, like `team = data`. On Databricks they do four jobs.',
        '**Cost.** Compute `custom_tags`, and serverless budget policies (newer docs: serverless usage policies), are copied into `system.billing.usage.custom_tags`, so spend can be split by team or project. On Azure, classic compute tags also reach the virtual machines, so they show up in Azure Cost Management.',
        '**Access.** Governed tags on catalogs, schemas, tables and columns drive ABAC policies (attribute-based access control): column masks and row filters that follow the tag, wherever the data is.',
        '**Finding and classifying data.** Tags make data searchable, and data classification can tag sensitive columns for you. **Ownership and clean-up.** An `owner` tag says who to ask before deleting something.',
        "Databricks adds its own default tags too: Vendor, Creator, ClusterName and ClusterId. Tags only apply to usage after they're set, never backwards. Untagged spend is spend nobody owns.",
    ],
    example=example('One cluster, tagged', """resource "databricks_cluster" "forecast" {
  cluster_name  = "forecast-dev"
  spark_version = "15.4.x-scala2.12"
  node_type_id  = "Standard_D4ds_v5"
  num_workers   = 2
  custom_tags = {
    team    = "data"
    project = "sales-forecast"
    owner   = "data-platform"
  }
}"""),
    check=question(
        'You add `team = ml` to a cluster today. What happens to last month\'s usage rows for that cluster?',
        [
            'They are updated to team = ml',
            'They stay untagged. Tags only apply from now on',
            'They are deleted',
        ],
        answer=1,
        why="Usage rows record the tags that were there at the time. Tag early, ideally through a policy, because you can't fix the past.",
    ),
    angle=angle(
        pattern='Two running totals, then a share',
        text='The big idea: tags only help if most of the spend carries them, so you measure coverage. Your code keeps two running totals. For each usage row it asks one question: does `custom_tags` have the key? Its cost goes into tagged or untagged. At the end the percent is tagged divided by the total, times 100. If the total is 0, the percent is 0, so you never divide by zero.',
        say='"I add up tagged and untagged cost for the key, and report the tagged share. Untagged spend is what nobody owns, so that number is the one to drive down."',
        classic=None,
    ),
    stack=stack('SQL: how much of last month\'s usage has a team tag', """SELECT
  SUM(CASE WHEN custom_tags['team'] IS NOT NULL
           THEN usage_quantity ELSE 0 END) AS tagged_dbus,
  SUM(CASE WHEN custom_tags['team'] IS NULL
           THEN usage_quantity ELSE 0 END) AS untagged_dbus
FROM system.billing.usage
WHERE usage_date >= date_sub(current_date(), 30)
  AND usage_unit = 'DBU';"""),
    exercise=exercise(
        title='Measure Tag Coverage',
        topic='tags',
        difficulty='easy',
        fn='tag_coverage',
        prompt="""Your function gets two things:

- `rows`: usage rows, each a dict like `{"cost": 120.0, "custom_tags": {"team": "data"}}`. `cost` is in dollars.
- `key`: the tag to check, like `"team"`.

A row is tagged when its `custom_tags` has `key`. Add up the cost of tagged rows and of untagged rows.

The percent tagged is tagged cost divided by total cost, times 100. If the total is 0, the percent is 0.

Return `[tagged_dollars, untagged_dollars, percent_tagged]`, each rounded to 2 places with `round(x, 2)`.""",
        pattern='Two running totals in one pass, then one division, guarded against a total of 0.',
        target='one pass over the rows',
        realworld='FinOps teams (the people who own cloud spend) track this number every month. Many set a goal like "95% of spend carries a team tag" and back it with compute policies that fix `custom_tags.team`, so new compute can\'t be created without it.',
        starter="""def tag_coverage(rows, key):
    # your code here
    pass
""",
        solution="""def tag_coverage(rows, key):
    tagged = 0
    untagged = 0
    for row in rows:
        if key in row["custom_tags"]:
            tagged += row["cost"]
        else:
            untagged += row["cost"]
    total = tagged + untagged
    if total == 0:
        percent = 0
    else:
        percent = tagged / total * 100
    return [round(tagged, 2), round(untagged, 2), round(percent, 2)]
""",
        cases=[
            case([
                {'cost': 120.0, 'custom_tags': {'team': 'data', 'project': 'forecast'}},
                {'cost': 80.0, 'custom_tags': {}},
                {'cost': 200.0, 'custom_tags': {'team': 'ml'}},
            ], 'team', expected=[320.0, 80.0, 80.0], sample=True),
            case([], 'team', expected=[0, 0, 0]),
            case([
                {'cost': 50.5, 'custom_tags': {'project': 'forecast'}},
            ], 'team', expected=[0, 50.5, 0.0]),
            case([
                {'cost': 10, 'custom_tags': {'team': 'data'}},
                {'cost': 10, 'custom_tags': {'owner': 'data-platform'}},
                {'cost': 10, 'custom_tags': {}},
            ], 'team', expected=[10, 20, 33.33]),
            case([
                {'cost': 19.99, 'custom_tags': {'project': 'churn'}},
                {'cost': 5.01, 'custom_tags': {'team': 'ml'}},
            ], 'project', expected=[19.99, 5.01, 79.96]),
            case([
                {'cost': 0, 'custom_tags': {'team': 'data'}},
            ], 'team', expected=[0, 0, 0]),
        ],
        guided="""def tag_coverage(rows, key):
    # Replace every ___ with real code, then run the tests.

    tagged = 0
    untagged = 0

    for row in rows:
        # Step 1: True when this row's custom_tags has the key.
        if ___:
            tagged += row["cost"]
        else:
            untagged += row["cost"]

    total = tagged + untagged

    # Step 2: no spend at all, so the percent is 0.
    if ___:
        percent = 0
    else:
        # Step 3: the tagged share, as a percent.
        percent = ___

    return [round(tagged, 2), round(untagged, 2), round(percent, 2)]
""",
        fills=['key in row["custom_tags"]', 'total == 0', 'tagged / total * 100'],
        concepts=[
            [
                'A dict inside a dict',
                '`row["custom_tags"]` is itself a dict, so you can check a key in it.',
                """row = {'cost': 5, 'custom_tags': {'team': 'data'}}
'team' in row['custom_tags']   # True""",
            ],
            [
                'Never divide by zero',
                'Dividing by 0 stops the program with an error. Check first.',
                """total = 0
share = 0 if total == 0 else 5 / total   # 0""",
            ],
            [
                'Rounding money',
                '`round(x, 2)` keeps 2 places after the dot.',
                """round(33.3333, 2)   # 33.33""",
            ],
        ],
        byhand='Row 1 has team: tagged is 120. Row 2 has no tags: untagged is 80. Row 3 has team: tagged is 320. Total 400. 320 divided by 400 is 0.8, times 100 is 80. Return [320.0, 80.0, 80.0].',
        why='One pass to add up, then one division.',
        gotchas=[
            [
                'Tag keys must match exactly',
                '`team`, `Team` and `team_name` are three different keys. Agree the keys once, write them into compute policies, and check for near-misses in the usage table.',
            ],
            [
                'Not everything carries your tags',
                "Some usage, such as serverless work outside a budget policy, or some platform charges, never gets your custom tags. Expect a small untagged share, and look for where it comes from before blaming people.",
            ],
        ],
    ),
)

lesson(MODULE, 'cost_by_tag',
    title='Who spent what',
    checked='2026-10-12',
    sources=[source('Billing system tables', 'https://docs.databricks.com/aws/en/admin/system-tables/billing'), source('System tables', 'https://docs.databricks.com/aws/en/admin/system-tables/')],
    learn=[
        '`system.billing.usage` has one row per piece of usage: `usage_quantity` (how many DBUs), `sku_name` (what kind of compute, which sets the price), `custom_tags` (a map of tags) and `usage_date`.',
        '`system.billing.list_prices` has the **list price** per DBU for each SKU. It is the public price, not any discount you have agreed, so treat the result as a guide, not the invoice.',
        'Join the two on `sku_name`, multiply DBUs by the price, and group by a tag to see who spent what. **Budgets** in the account console send email alerts when spend passes a threshold you choose.',
    ],
    example=example('Dollars for one row', """usage_quantity = 40                  # DBUs
sku_name = "PREMIUM_JOBS_COMPUTE"    # price: 0.30 a DBU (made up)
40 * 0.30 = 12.00 dollars, counted under custom_tags["team"]"""),
    check=question(
        "Your query says the ml team spent $4,000 last month at list price. Finance says the invoice was lower. Who's right?",
        [
            'The query, list prices are the real bill',
            "Both can be right. List price ignores your discount, so it's a fair way to compare teams, not the exact invoice",
            'Finance, the system tables are often wrong',
        ],
        answer=1,
        why='`list_prices` holds public prices. Use it to compare and trend; use the invoice or your agreed rates for exact money.',
    ),
    angle=angle(
        pattern='Group and add up',
        text='The big idea: spend only means something when you can say whose it is. Your code keeps a dict from tag value to dollars. For each usage row it finds the group: the tag value, or "untagged" if the row has no such tag. Then it works out the dollars, DBUs times the price for that SKU, and adds them to the group, starting it at the first dollars if it is new. At the end it rounds each total.',
        say='"I group usage by the tag, price each row from its SKU, and add it up. Untagged gets its own line so it can\'t hide."',
        classic='group_anagrams',
    ),
    stack=stack('SQL: last month\'s list-price spend by team', """SELECT
  COALESCE(u.custom_tags['team'], 'untagged') AS team,
  ROUND(SUM(u.usage_quantity * p.pricing.default), 2) AS list_dollars
FROM system.billing.usage u
JOIN system.billing.list_prices p
  ON u.sku_name = p.sku_name
 AND u.cloud = p.cloud
 AND u.usage_start_time >= p.price_start_time
 AND (p.price_end_time IS NULL
      OR u.usage_start_time < p.price_end_time)
WHERE u.usage_date >= date_sub(current_date(), 30)
GROUP BY 1
ORDER BY list_dollars DESC;"""),
    exercise=exercise(
        title='Spend by Team',
        topic='cost',
        difficulty='medium',
        fn='cost_by_tag',
        prompt="""Your function gets three things:

- `rows`: usage rows, each a dict like `{"sku_name": "PREMIUM_JOBS_COMPUTE", "usage_quantity": 40, "custom_tags": {"team": "ml"}}`. `usage_quantity` is in DBUs.
- `prices`: the price in dollars per DBU for each SKU, like `{"PREMIUM_JOBS_COMPUTE": 0.3}`.
- `key`: the tag to group by, like `"team"`.

For each row, its dollars are `usage_quantity` times the price for its `sku_name`. Its group is the value of `key` in its `custom_tags`, or `"untagged"` if the key isn't there.

Return a dict of group to total dollars, each rounded with `round(x, 2)`.""",
        pattern='Group by a key in a dict: add to the total if the group is there, start it if not. Round at the end.',
        target='one pass over the rows',
        realworld='This is the monthly "who spent what" report, built on `system.billing.usage` joined with `system.billing.list_prices`. The SKU names here are shortened; real ones can carry a region, and the prices are made-up round numbers.',
        starter="""def cost_by_tag(rows, prices, key):
    # your code here
    pass
""",
        solution="""def cost_by_tag(rows, prices, key):
    totals = {}
    for row in rows:
        tags = row["custom_tags"]
        if key in tags:
            group = tags[key]
        else:
            group = "untagged"
        dollars = row["usage_quantity"] * prices[row["sku_name"]]
        if group in totals:
            totals[group] += dollars
        else:
            totals[group] = dollars
    rounded = {}
    for group in totals:
        rounded[group] = round(totals[group], 2)
    return rounded
""",
        cases=[
            case([
                {'sku_name': 'PREMIUM_JOBS_COMPUTE', 'usage_quantity': 100, 'custom_tags': {'team': 'data'}},
                {'sku_name': 'PREMIUM_ALL_PURPOSE_COMPUTE', 'usage_quantity': 20, 'custom_tags': {'team': 'ml'}},
                {'sku_name': 'PREMIUM_JOBS_COMPUTE', 'usage_quantity': 40, 'custom_tags': {'team': 'ml'}},
                {'sku_name': 'PREMIUM_SERVERLESS_SQL_COMPUTE', 'usage_quantity': 10, 'custom_tags': {}},
            ], {
                'PREMIUM_JOBS_COMPUTE': 0.3,
                'PREMIUM_ALL_PURPOSE_COMPUTE': 0.55,
                'PREMIUM_SERVERLESS_SQL_COMPUTE': 0.7,
            }, 'team', expected={'data': 30.0, 'ml': 23.0, 'untagged': 7.0}, sample=True),
            case([], {'PREMIUM_JOBS_COMPUTE': 0.3}, 'team', expected={}),
            case([
                {'sku_name': 'PREMIUM_JOBS_COMPUTE', 'usage_quantity': 10, 'custom_tags': {'owner': 'data-platform'}},
                {'sku_name': 'PREMIUM_JOBS_COMPUTE', 'usage_quantity': 5, 'custom_tags': {}},
            ], {'PREMIUM_JOBS_COMPUTE': 0.3}, 'team', expected={'untagged': 4.5}),
            case([
                {'sku_name': 'PREMIUM_ALL_PURPOSE_COMPUTE', 'usage_quantity': 12.4, 'custom_tags': {'project': 'churn', 'team': 'ml'}},
                {'sku_name': 'PREMIUM_JOBS_COMPUTE', 'usage_quantity': 3.2, 'custom_tags': {'project': 'forecast'}},
                {'sku_name': 'PREMIUM_JOBS_COMPUTE', 'usage_quantity': 6.8, 'custom_tags': {'project': 'churn'}},
            ], {
                'PREMIUM_JOBS_COMPUTE': 0.3,
                'PREMIUM_ALL_PURPOSE_COMPUTE': 0.55,
            }, 'project', expected={'churn': 8.86, 'forecast': 0.96}),
            case([
                {'sku_name': 'PREMIUM_SERVERLESS_SQL_COMPUTE', 'usage_quantity': 1, 'custom_tags': {'team': 'bi'}},
                {'sku_name': 'PREMIUM_SERVERLESS_SQL_COMPUTE', 'usage_quantity': 2, 'custom_tags': {'team': 'bi'}},
                {'sku_name': 'PREMIUM_SERVERLESS_SQL_COMPUTE', 'usage_quantity': 4, 'custom_tags': {'team': 'bi'}},
            ], {'PREMIUM_SERVERLESS_SQL_COMPUTE': 0.7}, 'team', expected={'bi': 4.9}),
        ],
        guided="""def cost_by_tag(rows, prices, key):
    # Replace every ___ with real code, then run the tests.

    totals = {}
    for row in rows:
        tags = row["custom_tags"]

        # Step 1: the tag's value, or "untagged".
        if key in tags:
            group = tags[key]
        else:
            group = ___

        # Step 2: DBUs times the price for this row's SKU.
        dollars = ___

        if group in totals:
            totals[group] += dollars
        else:
            # Step 3: a new group starts at these dollars.
            ___

    rounded = {}
    for group in totals:
        rounded[group] = round(totals[group], 2)
    return rounded
""",
        fills=['"untagged"', 'row["usage_quantity"] * prices[row["sku_name"]]', 'totals[group] = dollars'],
        concepts=[
            [
                'Grouping with a dict',
                'Use the group name as the key. Add to it if it is there, start it if it is not.',
                """totals = {}
for fruit, n in [['apple', 2], ['pear', 1], ['apple', 3]]:
    if fruit in totals: totals[fruit] += n
    else: totals[fruit] = n
totals   # {'apple': 5, 'pear': 1}""",
            ],
            [
                'Looking up with a looked-up key',
                '`prices[row["sku_name"]]` first reads the SKU name from the row, then uses it to read the price.',
                """menu = {'tea': 2}
order = {'item': 'tea'}
menu[order['item']]   # 2""",
            ],
            [
                'Round at the end',
                'Add up the exact numbers first and round once at the end. Rounding each row first can make the total drift by a cent or two.',
                """round(0.333 + 0.333 + 0.333, 2)   # 1.0""",
            ],
        ],
        byhand='Row 1: 100 DBUs times 0.3 is 30, team data: data is 30. Row 2: 20 times 0.55 is 11, team ml: ml is 11. Row 3: 40 times 0.3 is 12, team ml: ml is 23. Row 4: 10 times 0.7 is 7, no team tag: untagged is 7. Return {"data": 30.0, "ml": 23.0, "untagged": 7.0}.',
        why='One pass to add up, then a short pass over the groups to round.',
        gotchas=[
            [
                'Prices change over time',
                '`list_prices` keeps every price with a start and end time. Join on the time too, as the SQL does, or a price change will be applied to old usage.',
            ],
            [
                'Budgets alert, they don\'t stop',
                'A budget in the account console emails people when spend passes the threshold. It does not shut anything down. To actually limit spend, use compute policies, auto-termination and smaller warehouses.',
            ],
        ],
    ),
)

lesson(MODULE, 'idle_cost',
    title='Idle compute is the quiet bill',
    checked='2026-10-12',
    sources=[source('Manage compute', 'https://docs.databricks.com/aws/en/compute/clusters-manage'), source('Compute policy reference', 'https://docs.databricks.com/aws/en/admin/clusters/policy-definition')],
    learn=[
        'A classic cluster bills for every minute it is running, busy or not. When nobody is using it, it keeps billing until **auto-termination** stops it.',
        '`autotermination_minutes` sets how long a cluster may sit idle before it stops. **0 means never**: it runs until someone stops it.',
        'SQL warehouses have **auto stop** (`auto_stop_mins`). Serverless compute stops quickly on its own. A compute policy can force a maximum, so no one can set 0.',
    ],
    example=example('A day of idle time', """idle 300 minutes, autotermination_minutes 0
  -> billed for all 300 idle minutes
idle 240 minutes, autotermination_minutes 30
  -> stops after 30, billed for 30 idle minutes"""),
    check=question(
        'A cluster uses 4 DBUs an hour at $0.55 a DBU, and sits idle 5 hours every day with auto-termination off. Roughly what does the idle time cost in 30 days?',
        ['About $11', 'About $330', 'Nothing, idle clusters are free'],
        answer=1,
        why='5 hours a day for 30 days is 150 hours. 150 times 4 DBUs is 600 DBUs, times $0.55 is $330, plus the Azure machine bill on top.',
    ),
    angle=angle(
        pattern='Cap each value, work out the cost, sort',
        text="The big idea: idle minutes are paid for but do nothing, and auto-termination caps them. Your code goes through the clusters. For each one it works out the idle minutes billed each day: all of them if auto-termination is 0, otherwise whichever is smaller, the idle minutes or the auto-termination setting. Turn minutes into hours, times the days, times DBUs an hour, times the price. Round it, and sort with the most expensive first.",
        say='"For each cluster I cap the idle time at its auto-termination setting, price the idle hours, and sort so the biggest waste is at the top."',
        classic=None,
    ),
    stack=stack('Terraform: idle limits on a cluster, a warehouse and a policy', """resource "databricks_cluster" "shared" {
  cluster_name            = "shared-analytics"
  spark_version           = "15.4.x-scala2.12"
  node_type_id            = "Standard_D4ds_v5"
  num_workers             = 2
  autotermination_minutes = 30
}

resource "databricks_sql_endpoint" "bi" {
  name                      = "bi-serverless"
  cluster_size              = "Small"
  enable_serverless_compute = true
  auto_stop_mins            = 10
}

# Nobody using this policy can turn
# auto-termination off or set it high.
resource "databricks_cluster_policy" "idle" {
  name = "idle-limits"
  definition = jsonencode({
    "autotermination_minutes" = {
      type = "range", minValue = 10, maxValue = 60
    }
  })
}"""),
    exercise=exercise(
        title='Price the Idle Time',
        topic='cost',
        difficulty='medium',
        fn='idle_cost',
        prompt="""Your function gets two things:

- `clusters`: each a dict like `{"name": "ml-dev", "dbu_per_hour": 6, "price_per_dbu": 0.55, "idle_minutes_per_day": 240, "autotermination_minutes": 30}`.
- `days`: how many days to cost.

For each cluster, the idle minutes billed each day are:

- all of `idle_minutes_per_day` if `autotermination_minutes` is 0 (never stops), otherwise
- the smaller of `idle_minutes_per_day` and `autotermination_minutes`.

The idle cost is those minutes turned into hours (divide by 60), times `days`, times `dbu_per_hour`, times `price_per_dbu`.

Return a list of `[name, dollars]` pairs, dollars rounded with `round(x, 2)`, sorted with the most expensive first. Clusters with the same cost keep their input order.""",
        pattern='Work out one number per item, then sort the pairs by that number, biggest first.',
        target='one pass over the clusters, then a sort',
        realworld='This is the first report a platform team runs when the bill jumps: which clusters cost the most while doing nothing. In real life the idle time comes from cluster events in the Clusters API or the `system.compute` tables, and it assumes one idle stretch a day, which is a simplification.',
        starter="""def idle_cost(clusters, days):
    # your code here
    pass
""",
        solution="""def idle_cost(clusters, days):
    rows = []
    for c in clusters:
        idle = c["idle_minutes_per_day"]
        stop = c["autotermination_minutes"]
        if stop != 0 and stop < idle:
            idle = stop
        hours = idle / 60 * days
        dollars = hours * c["dbu_per_hour"] * c["price_per_dbu"]
        rows.append([c["name"], round(dollars, 2)])
    rows.sort(key=lambda row: -row[1])
    return rows
""",
        cases=[
            case([
                {'name': 'etl-debug', 'dbu_per_hour': 2, 'price_per_dbu': 0.55, 'idle_minutes_per_day': 20, 'autotermination_minutes': 60},
                {'name': 'shared-analytics', 'dbu_per_hour': 4, 'price_per_dbu': 0.55, 'idle_minutes_per_day': 300, 'autotermination_minutes': 0},
                {'name': 'ml-dev', 'dbu_per_hour': 6, 'price_per_dbu': 0.55, 'idle_minutes_per_day': 240, 'autotermination_minutes': 30},
            ], 30, expected=[['shared-analytics', 330.0], ['ml-dev', 49.5], ['etl-debug', 11.0]], sample=True),
            case([], 30, expected=[]),
            case([
                {'name': 'gpu-small', 'dbu_per_hour': 8, 'price_per_dbu': 0.5, 'idle_minutes_per_day': 15, 'autotermination_minutes': 10},
                {'name': 'team-a', 'dbu_per_hour': 2, 'price_per_dbu': 0.5, 'idle_minutes_per_day': 60, 'autotermination_minutes': 0},
                {'name': 'team-b', 'dbu_per_hour': 4, 'price_per_dbu': 0.25, 'idle_minutes_per_day': 120, 'autotermination_minutes': 60},
            ], 7, expected=[['team-a', 7.0], ['team-b', 7.0], ['gpu-small', 4.67]]),
            case([
                {'name': 'a', 'dbu_per_hour': 4, 'price_per_dbu': 0.55, 'idle_minutes_per_day': 300, 'autotermination_minutes': 0},
                {'name': 'b', 'dbu_per_hour': 2, 'price_per_dbu': 0.55, 'idle_minutes_per_day': 60, 'autotermination_minutes': 30},
            ], 0, expected=[['a', 0.0], ['b', 0.0]]),
            case([
                {'name': 'night-batch', 'dbu_per_hour': 3, 'price_per_dbu': 0.3, 'idle_minutes_per_day': 45, 'autotermination_minutes': 120},
                {'name': 'notebooks', 'dbu_per_hour': 3, 'price_per_dbu': 0.55, 'idle_minutes_per_day': 600, 'autotermination_minutes': 60},
            ], 20, expected=[['notebooks', 33.0], ['night-batch', 13.5]]),
        ],
        guided="""def idle_cost(clusters, days):
    # Replace every ___ with real code, then run the tests.

    rows = []
    for c in clusters:
        idle = c["idle_minutes_per_day"]
        stop = c["autotermination_minutes"]

        # Step 1: auto-termination is on (not 0) and stops it sooner.
        if ___:
            idle = stop

        # Step 2: minutes to hours, times the number of days.
        hours = ___

        dollars = hours * c["dbu_per_hour"] * c["price_per_dbu"]
        rows.append([c["name"], round(dollars, 2)])

    # Step 3: biggest cost first (the minus sign flips the order).
    rows.sort(key=lambda row: ___)
    return rows
""",
        fills=['stop != 0 and stop < idle', 'idle / 60 * days', '-row[1]'],
        concepts=[
            [
                'Taking the smaller one',
                'Compare two numbers and keep the smaller. Here, only when the limit is switched on.',
                """idle = 240
stop = 30
if stop != 0 and stop < idle: idle = stop
idle   # 30""",
            ],
            [
                'Sorting by part of each item',
                '`key=lambda row: row[1]` says "sort by the second value". A minus sign in front sorts biggest first. Items with the same value keep their order.',
                """pets = [['rex', 3], ['tom', 9], ['ana', 3]]
pets.sort(key=lambda p: -p[1])
pets   # [['tom', 9], ['rex', 3], ['ana', 3]]""",
            ],
            [
                'Dividing gives a decimal',
                '`/` always gives a decimal number in Python 3, so 30 / 60 is 0.5, not 0.',
                """30 / 60   # 0.5""",
            ],
        ],
        byhand='etl-debug: idle 20, limit 60, so 20 minutes. 20/60 times 30 days is 10 hours, times 2 DBUs times 0.55 is 11.0. shared-analytics: limit 0, so all 300 minutes: 5 hours times 30 is 150, times 4 times 0.55 is 330.0. ml-dev: idle 240, limit 30, so 30 minutes: 0.5 times 30 is 15 hours, times 6 times 0.55 is 49.5. Sorted: [["shared-analytics", 330.0], ["ml-dev", 49.5], ["etl-debug", 11.0]].',
        why='One pass to work out each cost, then one sort.',
        gotchas=[
            [
                'DBUs are only half the bill on classic',
                'On Azure, a classic cluster also runs virtual machines that Azure bills separately, idle or not. The real idle cost is higher than the DBU figure; serverless includes the machines in its price.',
            ],
            [
                'Something keeps it awake',
                'Auto-termination counts from the last activity. A scheduled job, a dashboard refresh or a forgotten streaming query pointed at the cluster resets the clock, so it may never stop. Check what is running before blaming the setting.',
            ],
        ],
    ),
)
