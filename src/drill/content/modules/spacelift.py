"""Spacelift: stacks, runs and the policies that guard every change."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, module, planned, practice, question, screen, stack, source

MODULE = module('spacelift', 'Spacelift', 'Stacks, runs and the policies that guard every change.', setting=PLATFORM_SETTING)


lesson(MODULE, 'read_a_run',
    title='Reading a Spacelift run',
    checked='2026-11-26',
    sources=[source('Run', 'https://docs.spacelift.io/concepts/run'), source('Proposed run (preview)', 'https://docs.spacelift.io/concepts/run/proposed'), source('Tracked run (deployment)', 'https://docs.spacelift.io/concepts/run/tracked'), source('Plan policy', 'https://docs.spacelift.io/concepts/policy/terraform-plan-policy'), source('Push policy', 'https://docs.spacelift.io/concepts/policy/push-policy')],
    learn=[
        "A **run** is one go of Terraform on a **stack**. A **proposed** run only previews: by default, Spacelift starts one when a push to any other branch than the stack's tracked branch changes files in the stack's folder. It plans, reports back to the pull request, and stops. A **tracked** run deploys: it plans, waits for someone to **confirm**, then applies. Most runs a reviewer sees are proposed.",
        "That \"by default\" matters. A **push policy**, a rule the platform team writes, can change which pushes start which runs. If a run didn't start when you expected one, ask whether your team has one.",
        "Read a run from the top. The header says **which stack, which environment, which commit, and what state**. *Finished* on a proposed run means planning worked. It never means anything was deployed.",
        "Then the **Changes** tab: how many resources would be added, changed or destroyed (a replacement counts as one add and one destroy), and which. Then the **planning log**: the plan summary line, the first error if it failed, and the GO lines. Every GO marks one automatic step that passed: the plan ran, its JSON was made, the resource list was uploaded. Only the GO after **Evaluated N plan policies** is the plan policies' result. None of them is a person approving.",
        "A good review answer says what you saw, where it came from, what you still don't know, and the safest next step. The walkthrough below goes screen by screen through a proposed run for a team's folder permissions.",
    ],
    walkthrough=[
        screen('flow', caption='Where a run fits: from YAML to a decision',
            boxes=[
                {'title': 'YAML', 'sub': 'Desired changes'},
                {'title': 'Validate + PR', 'sub': 'Pydantic and checks'},
                {'title': 'Spacelift', 'sub': 'Proposed run', 'n': 1},
                {'title': 'Terraform', 'sub': 'Read, compare, plan'},
                {'title': 'Human review', 'sub': 'Decide or escalate', 'n': 2},
            ],
            note='A tracked run applies changes only once someone confirms it (or straight away, if the stack has autodeploy on). A finished proposed run is still a preview.',
            steps=[
                'Opening a pull request starts a proposed run on every stack the change touches. It plans and reports; it never applies.',
                'A person reads the plan and decides: approve the PR, ask a question, or stop. Deploying happens later, in a tracked run.',
            ],
            tips=['Review the plan, not just the diff of the YAML: the runbook adds things the YAML never says.'],
        ),
        screen('header', caption='Step 1 · The run header: what you are looking at',
            title={'text': 'Databricks IaC plan review', 'n': 2},
            state={'text': 'FINISHED', 'n': 1},
            path={'text': '.../Platf.../Databricks/DBX_SALES/DEV', 'n': 4},
            meta=['Terraform 1.5.7', 'DEV', 'feature/iac-review'],
            commit={'text': '5b8e1d4', 'n': 3},
            started='Started on Oct 9th, 11:25:43 PM by a Git commit',
            line2=['Committed on Oct 9th, 11:19:40 PM', 'State managed by Spacelift'],
            run_type={'text': 'Proposed', 'n': 4},
            tabs=[{'text': 'History'}, {'text': 'Changes', 'count': '~ 14', 'n': 5}],
            steps=[
                'FINISHED: planning completed without errors. On a proposed run that is all it means.',
                'The run is named after the commit or pull request: the change you are reviewing.',
                'The commit (5b8e1d4) is the exact Git version this plan used. Check it matches the newest commit in the PR.',
                'The stack path ends in DEV: the environment. "Proposed" (under it) says this run only previews.',
                'Changes ~ 14: fourteen resources would change in place. Open this tab next.',
            ],
            tips=[
                'Write down three things before anything else: the stack, the environment (DEV, UAT or PROD) and the commit.',
                '"State managed by Spacelift" means Spacelift keeps Terraform\'s state for this stack and locks it during runs. Never try to fix state by hand.',
                'If the PR has newer commits than the run, wait for the newer run: an old plan reviews old code.',
            ],
        ),
        screen('changes', caption='Step 2 · The Changes tab: the whole change set',
            count={'text': 'Showing 14 of 14', 'n': 1},
            search='Search by name, address, or resource type...',
            filters={'items': ['Address', 'Change type', 'Name', 'Resource type', 'Terraform provider'], 'n': 2},
            expand={'text': 'Expand all', 'n': 4},
            rows=[
                {'sym': '~', 'address': 'module.dbx_workspace[0].databricks_permissions.folder_permissions["team_sales_folder"]', 'status': 'PLANNED', 'n': 3},
                {'sym': '~', 'address': 'module.dbx_workspace[0].databricks_permissions.cluster_permissions["sales-shared-compute"]', 'status': 'PLANNED'},
                {'sym': '~', 'address': 'module.dbx_workspace[0].databricks_permissions.cluster_permissions["hr-shared-compute"]', 'status': 'PLANNED'},
                {'sym': '~', 'address': 'module.dbx_workspace[0].databricks_permissions.cluster_permissions["aiml-shared-compute"]', 'status': 'PLANNED'},
                {'sym': '~', 'address': 'module.dbx_workspace[0].databricks_permissions.cluster_permissions["platform-shared-compute"]', 'status': 'PLANNED'},
            ],
            more='+ 9 more',
            steps=[
                '"Showing 14 of 14": the full count. Write it down before you filter anything.',
                'Filters narrow the list by change type, resource type or provider. Use them after you have the full count, so nothing hides.',
                'Each row is one resource. ~ means changed in place, + added, - destroyed, -/+ or +/- replaced. PLANNED means not applied yet.',
                'Expand only the resource you are investigating; Expand all when you need to read everything.',
            ],
            tips=[
                'An in-place change (~) can still remove someone\'s access. "0 to destroy" is not enough to approve.',
                'Fourteen permission changes from one team\'s YAML edit? Ask why the shared clusters changed too before approving.',
            ],
        ),
        screen('log', caption='Step 3 · The planning log: the summary and the checks',
            phase='Planning', duration='00:46', at='Oct 9th, 11:26:10 PM',
            tail=['    + group_name       = "users"', '    + permission_level = "CAN_READ"', '  }', '', '  # (1 unchanged block hidden)', '}'],
            summary={'text': 'Plan: 0 to add, 14 to change, 0 to destroy.', 'n': 1},
            run_id='01K8R3SV2Q7M4N6P9T5WXD0FHA',
            lines=[
                {'text': 'Changes are GO'},
                {'text': 'Generating JSON representation of the plan...'},
                {'text': 'JSON representation is GO'},
                {'text': 'Uploading the list of managed resources...'},
                {'text': 'Please be aware that the run changes calculation includes output changes.', 'warn': True},
                {'text': 'Resource list upload is GO'},
                {'text': 'Loading custom plan policy inputs...'},
                {'text': '0 custom plan policy inputs found'},
                {'text': 'Evaluated 2 plan policies', 'n': 2},
                {'text': 'Plan checks are GO', 'n': 2},
            ],
            tools={'items': ['Search', 'Full screen', 'Copy', 'Download'], 'n': 3},
            steps=[
                'The plan summary: the same counts as the Changes tab. If they disagree, you are reading two different runs.',
                'Two plan policies were checked, and the GO right after that line is their result. The earlier GOs (Changes, JSON, resource list) are Spacelift\'s own steps passing. Every GO is an automatic check, the policies written in Rego by the platform team, not a reviewer\'s approval.',
                'Search jumps to the first error or the summary in a long log; Copy and Download keep it for your notes.',
            ],
            tips=[
                'When a plan fails, the first error is the useful one. Search for "Error" rather than reading the last line.',
                'A deny policy fails the run in red. A warn policy prints in yellow and never fails it, but on a stack with autodeploy on, a tracked run with a warning waits for a person to confirm it.',
            ],
        ),
        screen('diff', caption='Step 4 · Who gets access: read by group, not by position',
            blocks=[
                {'group': 'grp-sales-dev-analysts', 'level': 'CAN_EDIT', 'n': 1},
                {'group': 'grp-sales-dev-owners', 'level': 'CAN_EDIT', 'n': 2},
                {'group': 'grp-sales-dev-owners', 'level': 'CAN_MANAGE', 'hidden': '# (2 unchanged attributes hidden)', 'n': 3},
                {'group': 'users', 'level': 'CAN_READ', 'n': 4},
            ],
            hidden={'text': '# (1 unchanged block hidden)', 'n': 5},
            steps=[
                'An explicit grant from team.yml: the analysts group can edit.',
                'The owner group\'s own CAN_EDIT grant, also typed in team.yml.',
                'CAN_MANAGE for the same owner group: the runbook adds it for every owner. Listed twice, the group ends up with the higher one.',
                'users CAN_READ: a default the runbook adds to every team folder.',
                'Hidden blocks are unchanged. Expand them before you conclude who has access.',
            ],
            tips=[
                'Check each group and what it ends up with. The order of access_control blocks can shuffle without changing anything.',
                'A permissions resource owns the whole list: access someone clicked in by hand disappears on the next apply.',
            ],
        ),
        screen('history', caption='Step 5 · Run history: finished and proposed is still a preview',
            title={'text': 'Remove ac', 'n': 1},
            state='FINISHED',
            path={'text': '.../Platf.../Databricks/DBX_HR/UAT', 'n': 1},
            context={'text': 'UAT review context', 'n': 2},
            run_type='Proposed',
            changes='~ 3',
            events=[{'state': 'Finished', 'at': 'Oct 5th, 3:06:37 PM', 'buttons': ['Promote', 'Retry'], 'n': 5}],
            phase='Planning', duration='00:48', at='Oct 5th, 3:05:49 PM',
            lines=[
                {'text': '        + service_principal = "sp-hr-etl-uat"', 'code': True, 'n': 3},
                {'text': '      ]', 'code': True},
                {'text': '      name              = "ac-hr-uat-service-credential"', 'code': True},
                {'text': 'Changes are GO'},
                {'text': 'Evaluated 2 plan policies', 'n': 4},
                {'text': 'Plan checks are GO', 'n': 4},
            ],
            steps=[
                'A different stack: the path ends in UAT. Check the environment every time; DEV and UAT runs look alike.',
                'A context is attached: shared settings (and maybe secrets) that many stacks reuse. Changing a context changes every stack it is attached to.',
                'The plan names a service principal. A name in a plan is not proof the identity exists in the workspace yet.',
                'Policies passed again. Still only a preview.',
                'Promote would turn this preview into a tracked run that deploys. Retry plans again. Reviewers don\'t press either.',
            ],
            tips=[
                'Promote only appears when the stack allows it and you hold the promote role. Even then, deploying follows your team\'s approval process.',
                'A proposed run is a snapshot of one commit. If the YAML changed since, the run is out of date.',
            ],
        ),
    ],
    example=example('What each run state proves', """proposed  FINISHED      a preview worked; nothing was deployed
proposed  FAILED        the plan failed: read the first error
tracked   UNCONFIRMED   a plan waits for someone to confirm or discard it
tracked   FINISHED      applied (or nothing to change)
tracked   DISCARDED     someone rejected the plan; nothing was applied
any       QUEUED/READY  not started: waiting for a lock or a worker"""),
    check=question(
        'A run on the UAT stack shows **FINISHED** and **Proposed**, and the planning log says "Plan checks are GO". What has been deployed?',
        [
            'Everything in the plan: it finished and passed the checks',
            'Nothing: a proposed run only previews',
            'Only the resources the policies approved',
        ],
        answer=1,
        why='Proposed runs plan and report; they never apply. Finished means planning worked, and "Plan checks are GO" means the automatic policy checks passed. Deploying needs a tracked run, after review.',
    ),
    angle=angle(
        pattern='Header first, then changes, then the log',
        text='The big idea: a run\'s type and state together say what it proves. A proposed run is only ever a preview; a tracked run deploys once someone confirms it. Your code reads those two fields and returns what the run proves, checking the cases that apply to any run first (not started yet), then proposed runs, then tracked ones. It is like reading a parcel\'s tracking page: "label printed" and "delivered" are both finished steps, but only one means it arrived.',
        say="\"I read a run from the top: the stack, the [[environment|author|cost::DEV, UAT or PROD.]] and the commit, then the Changes tab, then the log. A finished proposed run is only a [[preview|deployment|backup::It plans and reports, and stops.]], and the last GO means the [[policies|reviewers|tests::Automatic checks written in Rego.]] passed, not that a person approved it.\"",
        classic=None,
    ),
    stack=stack('Spacelift: the same states in its Terraform provider', """resource "spacelift_stack" "dbx_service_dev" {
  name           = "dbx-service-dev"
  repository     = "dbx-platform" # the Git repo the stack reads (required)
  branch         = "main"         # pushes here start tracked runs
  autodeploy     = false          # tracked runs wait in UNCONFIRMED for a person
  enable_local_preview = false
}

# A pull request from feature/iac-review starts a proposed run:
# it plans, reports to the PR, and stops."""),
    exercise=exercise(
        title='What Does This Run Prove?',
        topic='spacelift',
        difficulty='easy',
        fn='what_it_proves',
        prompt="""Your function gets `run`, a dict with `"type"` (`"proposed"` or `"tracked"`) and `"state"` (in capitals, like `"FINISHED"`).

Return what the run proves, checking in this order:

- state `"QUEUED"` or `"READY"` (any type) -> `"not started"`
- proposed and `"FINISHED"` -> `"preview only"`
- `"FAILED"` (any type) -> `"failed: read the first error"`
- tracked and `"UNCONFIRMED"` -> `"waiting for confirmation"`
- tracked and `"FINISHED"` -> `"applied"`
- tracked and `"DISCARDED"` -> `"rejected"`
- anything else -> `"still running"`""",
        pattern='Check the cases that apply to any run first, then the ones that depend on the type.',
        target='a few checks, no loops',
        realworld="Spacelift shows a run's type and state at the top of every run. Reviewers who mix up \"finished\" with \"deployed\" approve things that were never applied, or think a fix is live when it isn't. The run list's filters use these same states.",
        practice=practice(
            intro='Read Spacelift runs the way a reviewer does: say what each one proves before you say anything is live.',
            explain='A run\'s type and state together say what it proves: a proposed run is only ever a preview, and a tracked run deploys only once someone confirms it. You read each run from the top, matched its state to what it proves, checked it planned the newest commit, and went to the first error when one failed.',
            pattern='Type and state say what it proves',
            realworld='When a teammate says a fix is live, or a pull request is ready to review, you open the Spacelift run and check its type, state and commit first. When a run fails, you go straight to the first error in the planning log.',
            asks=[
                ask('What does this run prove?', ['It was applied: tracked runs on main deploy', 'It planned, and waits for a person to confirm it', 'It failed: it never got past the plan'], answer=1,
                    evidence=evidence('code', title='The run header', text="""Run:    Add sales_daily-report cluster
Stack:  .../Databricks/DBX_SALES/DEV
Type:   Tracked
State:  UNCONFIRMED
Commit: 7c41e0a on main"""),
                    clue='Find UNCONFIRMED in the run states. Who is it waiting for?',
                    why='UNCONFIRMED on a tracked run means the plan is ready and waits for a person. Nothing is applied until someone confirms it.',
                    wrong=['Applied would be a tracked run that is FINISHED.', None, 'A failed run says FAILED.']),
                ask('A teammate says their fix went out yesterday. This is the run. Is the fix live?', ['Yes: the run is over and nothing failed', 'No: someone rejected the plan'], answer=1,
                    evidence=evidence('code', title='The run header', text="""Run:    Fix cluster policy limits
Stack:  .../Databricks/DBX_SALES/DEV
Type:   Tracked
State:  DISCARDED
Commit: 4e9a2b1 on main"""),
                    clue='Look up DISCARDED in the run states.',
                    why='DISCARDED means someone rejected the plan. Nothing was applied, so the fix isn\'t live yet: it needs a new run.',
                    wrong=['Over isn\'t the same as applied. What does DISCARDED mean?', None]),
                ask('This proposed run FAILED. Which line do you read first?', ['The last line: the exit code says how it ended', 'The first error: the group that wasn\'t found', 'The "Planning failed" line: it sums up the run'], answer=1,
                    evidence=evidence('code', title='The planning log, near the end', text="""module.dbx_workspace[0].data.databricks_group.owner: Reading...

Error: cannot read group: group grp-sales-dev-owners not found

  with module.dbx_workspace[0].data.databricks_group.owner

Planning failed. Terraform encountered an error while
generating this plan.

Unexpected exit code when planning changes: 1"""),
                    clue='The lines after the cause only say that planning stopped.',
                    why='The first error is the cause: the plan looks up a group that doesn\'t exist in the workspace. Everything after it only says planning stopped.',
                    wrong=['The exit code only says something failed, not what.', None, 'That line says planning failed, not why.']),
                ask('Can you review the pull request from this run?', ['Yes: it finished and the checks are GO', 'Not yet: wait for the run on the newest commit', 'Yes, if you also read the YAML diff'], answer=1,
                    evidence=evidence('code', title='The pull request and its run', text="""Pull request #214 · feature/iac-review
  newest commit: 9b2f7d1   pushed 11:41 PM

Run on .../DBX_SALES/DEV · Proposed · FINISHED
  commit: 5b8e1d4          started 11:25 PM
  Plan checks are GO"""),
                    clue='Compare the run\'s commit with the newest one in the pull request.',
                    why='A run is a snapshot of one commit. 5b8e1d4 is older than the newest commit, so this plan reviews old code. Wait for the run on 9b2f7d1.',
                    wrong=['It finished, but on an older commit: this plan reviews old code.', None, 'The YAML diff doesn\'t show what the runbook adds, and this plan is for old code anyway.']),
            ],
        ),
        starter="""def what_it_proves(run):
    # your code here
    pass
""",
        solution="""def what_it_proves(run):
    kind, state = run["type"], run["state"]
    if state in ("QUEUED", "READY"):
        return "not started"
    if kind == "proposed" and state == "FINISHED":
        return "preview only"
    if state == "FAILED":
        return "failed: read the first error"
    if kind == "tracked" and state == "UNCONFIRMED":
        return "waiting for confirmation"
    if kind == "tracked" and state == "FINISHED":
        return "applied"
    if kind == "tracked" and state == "DISCARDED":
        return "rejected"
    return "still running"
""",
        cases=[
            case({'type': 'proposed', 'state': 'FINISHED'}, expected='preview only', sample=True),
            case({'type': 'tracked', 'state': 'FINISHED'}, expected='applied'),
            case({'type': 'tracked', 'state': 'UNCONFIRMED'}, expected='waiting for confirmation'),
            case({'type': 'proposed', 'state': 'FAILED'}, expected='failed: read the first error'),
            case({'type': 'tracked', 'state': 'DISCARDED'}, expected='rejected'),
            case({'type': 'tracked', 'state': 'QUEUED'}, expected='not started'),
            case({'type': 'proposed', 'state': 'PLANNING'}, expected='still running'),
            case({'type': 'tracked', 'state': 'APPLYING'}, expected='still running'),
        ],
        guided="""def what_it_proves(run):
    # Replace every ___ with real code, then run the tests.
    kind, state = run["type"], run["state"]
    # Cases for any run first.
    if state in ("QUEUED", "READY"):
        return "not started"
    if kind == "proposed" and state == "FINISHED":
        return ___
    if state == "FAILED":
        return "failed: read the first error"
    # Tracked runs: they can deploy.
    if kind == "tracked" and state == "UNCONFIRMED":
        return "waiting for confirmation"
    if ___:
        return "applied"
    if kind == "tracked" and state == "DISCARDED":
        return "rejected"
    return "still running"
""",
        fills=['"preview only"', 'kind == "tracked" and state == "FINISHED"'],
        concepts=[
            [
                'Two names at once',
                '`a, b = x, y` sets two names in one line.',
                """kind, state = "tracked", "FINISHED"
kind   # 'tracked'""",
            ],
            [
                'in on a tuple',
                '`state in ("QUEUED", "READY")` is True if state is either one.',
                '"READY" in ("QUEUED", "READY")   # True',
            ],
            [
                'and',
                '`a and b` is True only when both are.',
                '"tracked" == "tracked" and "FINISHED" == "FAILED"   # False',
            ],
        ],
        byhand='The sample is proposed and FINISHED. Not QUEUED or READY. Proposed and FINISHED: return "preview only". Nothing was deployed.',
        why='At most six checks on two fields.',
        gotchas=[
            [
                'Finished is not deployed',
                'On a proposed run, FINISHED only means planning worked. Look for "Proposed" in the header before you say anything is live.',
            ],
            [
                'Unconfirmed runs expire',
                'A tracked run waiting for confirmation is discarded after 30 days. If a change "never went out", look for an old unconfirmed run.',
            ],
        ],
    ),
)


# The stacks from the lesson's example, shown above the practice questions.
_STACKS = """network       waits for nothing
workspace     waits for network
monitoring    waits for network
catalogs      waits for workspace
jobs          waits for workspace, catalogs"""

lesson(MODULE, 'runs_after',
    title='What runs after a change?',
    checked='2026-11-26',
    sources=[source('Stack', 'https://docs.spacelift.io/concepts/stack'), source('Stack dependencies', 'https://docs.spacelift.io/concepts/stack/stack-dependencies')],
    learn=[
        "In **Spacelift**, each piece of infrastructure lives in its own **stack**: one Terraform folder with its own state, run by Spacelift when its code changes. A platform is usually several stacks, like `network`, `workspace`, `catalogs` and `jobs`.",
        "Stacks can **depend on** each other. `workspace` depends on `network` because the workspace needs the network's subnets first. When `network` applies a change, Spacelift starts a run for every stack that depends on it, and for the stacks that depend on those, all the way **downstream**.",
        "Order matters. A stack only runs once **every stack it waits for** has finished, if that stack is running too. If `jobs` waits for `workspace` and `catalogs`, it goes after both, even though `workspace` changed first.",
        "Stacks that don't depend on the change, directly or through another stack, don't run at all. That keeps a small change small.",
        "One exception. A stack can take another stack's **outputs** as its inputs, like the network's subnet ids. Spacelift calls that a **reference**. Then the stack runs only when one of those outputs is new or has changed, unless the reference is set to **Trigger always**. If the outputs stay the same, Spacelift skips it.",
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
        say='"When one stack changes, every stack that [[uses it|it uses|sits beside it::Think about who depends on whose outputs.]] has to run again. I list those, then run them in an order where each one [[waits for|runs before|ignores::A stack can\'t start until what it needs is ready.]] the stacks it needs."',
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
        realworld='This is Spacelift stack dependencies: when an upstream stack applies, its dependents get tracked runs in this order (a stack that takes outputs by reference is skipped when those outputs didn\'t change). A circular dependency is refused when you set it up, so the order always exists.',
        practice=practice(
            intro='Work out which stacks run after a change, and when, the way a platform reviewer does before merging.',
            explain='When a stack changes, every stack downstream of it runs, and each one only after the stacks it waits for. You followed the waits down from the changed stack, saw that stacks upstream or off to the side stay still, and caught a stack that could start too early because one of its waits was missing.',
            pattern='Follow the waits downstream only',
            realworld='Before you merge a change to a shared stack like network, you work out which stacks will run after it, and in what order. When a stack uses another stack\'s outputs, you check that it waits for that stack, so it never runs too early.',
            asks=[
                ask('`catalogs` changes. Which stacks run after it?', ['Only `jobs`', '`jobs` and `workspace`', 'Every stack'], answer=0,
                    evidence=evidence('code', title='The stacks and what they wait for', text=_STACKS),
                    clue='Only stacks downstream run. Which stack waits for catalogs?',
                    why='Only jobs waits for catalogs. workspace and network are upstream, and monitoring doesn\'t depend on it, so they stay still. A small change stays small.',
                    wrong=[None, 'workspace is upstream: catalogs waits for it, not the other way round.', 'Only stacks that wait for catalogs, directly or through another stack, run.']),
                ask('`network` changes. Which stacks can start as soon as it has applied?', ['`workspace` and `catalogs`', '`workspace` and `monitoring`', 'All four, at the same time'], answer=1,
                    evidence=evidence('code', title='The same stacks', text=_STACKS),
                    clue='Which stacks wait for network and nothing else?',
                    why='workspace and monitoring each wait only for network, so both can start once it has applied. catalogs and jobs wait for workspace.',
                    wrong=['catalogs waits for workspace, which hasn\'t run yet.', None, 'catalogs and jobs wait for workspace, which hasn\'t run yet.']),
                ask('`jobs` changes. What runs after it?', ['Nothing: no stack waits for `jobs`', '`catalogs` and `workspace`, to be safe', 'Every stack'], answer=0,
                    evidence=evidence('code', title='The same stacks', text=_STACKS),
                    clue='Look for any stack that lists jobs in what it waits for.',
                    why='jobs is at the end of the line: nothing waits for it, so its change runs on its own.',
                    wrong=[None, 'Those are upstream of jobs. A change only flows downstream.', 'Only stacks downstream of jobs run, and there are none.']),
                ask('`jobs` uses the catalog names that `catalogs` makes, but someone set it to wait only for `workspace`. `workspace` changes. What can go wrong?', ['Nothing: jobs runs after workspace anyway', '`jobs` may run before `catalogs` is done', 'Spacelift refuses to run either one'], answer=1,
                    evidence=evidence('code', title='The stacks now', text="""network       waits for nothing
workspace     waits for network
monitoring    waits for network
catalogs      waits for workspace
jobs          waits for workspace"""),
                    clue='After workspace, which stacks are ready at the same moment?',
                    why='jobs only waits for what it lists. Once workspace is done, catalogs and jobs are both ready, so jobs can run before the new catalogs exist. Add catalogs to what jobs waits for.',
                    wrong=['It runs after workspace, but nothing makes it wait for catalogs.', None, 'Nothing here is a loop, so Spacelift runs both.']),
                ask('`network` applies a change that only adds a tag. `workspace` takes network\'s subnet ids as a reference. Does `workspace` run?', ['Yes: it waits for network, so it always runs', 'No: the outputs it uses didn\'t change', 'Only once someone starts it by hand'], answer=1,
                    evidence=evidence('code', title='The dependency', text="""workspace waits for network
  reference:   subnet_ids
  Trigger always: off

network's apply:
  ~ tags on the network

subnet_ids before:
  ["snet-host", "snet-db"]
subnet_ids after:
  ["snet-host", "snet-db"]"""),
                    clue='Compare the output workspace uses, before and after.',
                    why='With a reference, the next stack runs only when a referenced output is new or changed. A tag change leaves subnet_ids the same, so workspace is skipped. Turn on Trigger always if it must run every time.',
                    wrong=['That is true without a reference. With one, Spacelift checks the outputs first.', None, 'Nothing needs a manual start: Spacelift decides from the outputs.']),
            ],
        ),
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
    checked='2026-11-26',
    sources=[source('Plan policy', 'https://docs.spacelift.io/concepts/policy/terraform-plan-policy'), source('Lock your resources to prevent unexpected changes', 'https://learn.microsoft.com/azure/azure-resource-manager/management/lock-resources')],
    learn=[
        "A **plan policy** runs automatically on every Spacelift run and can warn or block based on the plan. It's code review that never gets tired.",
        "Start with the resources you can't rebuild: workspaces, storage accounts, metastores.",
    ],
    example=example("A Rego rule (Rego is the policy language from Open Policy Agent, which Spacelift uses) that blocks destroying protected resource types", """deny contains msg if {
  rc := input.terraform.resource_changes[_]
  "delete" in rc.change.actions
  rc.type in protected
  msg := sprintf("%s would be destroyed", [rc.address])
}"""),
    check=question(
        'A plan policy blocks destroying storage accounts. Can someone still lose one?',
        [
            'No: the policy sees every change to the account',
            'Yes: a delete outside Spacelift never meets the policy',
            'Only if the Rego rule has a bug',
        ],
        answer=1,
        why='Policies only see plans. A delete in the Azure portal, with the Azure CLI, or from a local apply outside Spacelift never makes one, so pair the policy with RBAC (role-based access control: rules for who may do what) and resource locks.',
    ),
    angle=angle(
        pattern='Check each change against a set',
        text='The big idea: a plan policy checks every run automatically, starting with the resources you can\'t rebuild. Your code first turns the protected types into a set, a collection built to answer "is this in it?" instantly, like a book\'s index. Then it goes through the changes in order. A change gets a message only if its type is protected and its actions include delete. A replacement includes delete, so it counts too. An empty list means the run may go ahead.',
        say='"My plan policy checks every run for changes that would [[delete|update|read::The dangerous change is the one you can\'t undo.]] something we can\'t rebuild, like a workspace. A [[replacement|tag change|comment::Destroying and re-creating something also loses it.]] counts too. If nothing is flagged, the run can [[go ahead|stop|wait::An empty list of problems is a pass.]]."',
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
        practice=practice(
            intro='Read a plan against a plan policy the way the platform team does: what it blocks, what it misses, and what it never sees.',
            explain='A plan policy checks every run automatically, starting with the resources you can\'t rebuild. You flagged only the changes that were both a protected type and a delete, replacements included, noticed a type the protected list was missing, and saw what a policy can\'t catch because it never becomes a plan.',
            pattern='A protected type plus a delete',
            realworld='When the platform team adds a plan policy, you check that its protected types cover everything you can\'t rebuild, like storage containers with data in them. When someone suggests a state command to get past a policy, you ask why the plan wants a delete.',
            asks=[
                ask('The policy protects workspaces, storage accounts and metastores. Which change does it block?', [], answer=2, pick=True,
                    evidence=evidence('plan', title='Stack dbx-service-dev · proposed',
                        summary=[['2', 'to add', 'a'], ['1', 'to change', ''], ['2', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-', 'address': 'databricks_cluster.shared', 'note': 'removed from clusters.yml'},
                            {'sym': '~', 'address': 'azurerm_storage_account.lake', 'note': 'tags updated'},
                            {'sym': '-/+', 'address': 'azurerm_databricks_workspace.this', 'note': 'managed_resource_group_name changed: forces replacement'},
                            {'sym': '+', 'address': 'databricks_schema.raw', 'note': 'new schema'},
                        ]),
                    clue='It needs both: a protected type, and a delete among its actions.',
                    why='The workspace is a protected type, and a replacement includes a delete, so the policy flags it. The cluster is deleted too, but clusters aren\'t on the protected list.',
                    wrong=['It is deleted, but clusters aren\'t on the protected list.', 'A protected type, but a tag update deletes nothing.', None, 'A new schema destroys nothing.']),
                ask('A plan destroys `azurerm_storage_container.lake["bronze"]`, and the lake\'s data is in it. Does this policy stop it?', ['Yes: the container is part of a protected storage account', 'No: containers aren\'t on the protected list'], answer=1,
                    evidence=evidence('code', title='The policy', text="""protected := {
  "azurerm_databricks_workspace",
  "azurerm_storage_account",
  "databricks_metastore"
}

deny contains msg if {
  rc := input.terraform.resource_changes[_]
  "delete" in rc.change.actions
  rc.type in protected
  msg := sprintf("%s would be destroyed", [rc.address])
}"""),
                    clue='Compare the resource\'s type, word for word, with the protected list.',
                    why='The rule matches the type exactly. `azurerm_storage_container` isn\'t `azurerm_storage_account`, so the run goes ahead and the data goes with it. List every type whose loss you can\'t undo.',
                    wrong=['A container is a different type from the account it lives in. The rule only matches exact types.', None]),
                ask('You\'ve written a new rule that blocks deleting any `databricks_catalog`. How do you roll it out?', ['As a deny rule straight away, on every stack', 'As a warn rule first, then switch it to deny', 'As a deny rule on dev stacks only, for good'], answer=1,
                    alone=True,
                    clue='Spacelift plan policies can do more than block.',
                    why='A warn rule prints in yellow and never fails a run, so you see what it would have stopped before it stops anyone. Then switch it to deny. One catch: on a stack with autodeploy on, a warning makes the run wait for a person to confirm it, so tell those teams first.',
                    wrong=['A rule nobody has seen in action can block real work on day one.', None, 'Prod is where a lost catalog hurts most. Dev is a place to try it, not to leave it.']),
                ask('An AI assistant suggests this. What would the command really do?', ['Delete the storage account in Azure, data and all', 'Terraform forgets the account; Azure keeps it', 'Nothing: the policy blocks the command too'], answer=1,
                    evidence=evidence('claim', text='The policy is blocking you? Run `terraform state rm azurerm_storage_account.lake`, and the plan won\'t show a delete any more.'),
                    clue='State commands change what Terraform keeps track of, without making a plan.',
                    why='`state rm` deletes nothing in Azure, but Terraform stops tracking the account, so no plan, and no policy, sees it again. Ask why the plan wants a delete instead.',
                    wrong=['`state rm` never touches Azure. It only edits Terraform\'s record.', None, 'Policies only see plans, and state commands make no plan.']),
                ask('The policy denies this run. Someone renamed the storage account\'s resource block in the code. What is the fix?', ['Add a moved block for the rename', 'Add the label that allows destroys', 'Turn the policy off for one run'], answer=0,
                    evidence=evidence('plan', title='Stack sales-foundation-dev · proposed',
                        summary=[['1', 'to add', 'a'], ['0', 'to change', ''], ['1', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-', 'address': 'azurerm_storage_account.lake', 'note': 'destroy'},
                            {'sym': '+', 'address': 'azurerm_storage_account.datalake', 'note': 'create'},
                        ]),
                    clue='Is anyone trying to get rid of the storage account, or only to call it something else?',
                    why='Only the name in the code changed, but Terraform reads a new name as a new account. A moved block from lake to datalake tells it they are the same one, so the plan shows no destroy and the policy has nothing to stop.',
                    wrong=[None, 'That would let the real account and its data be destroyed, for a rename.', 'The policy is right: the plan really would destroy the account.']),
            ],
        ),
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
                'Spacelift plan policies support `warn` as well as `deny`. Rolling a new rule out as a warning shows you what it would have blocked before it blocks anyone. A warning never fails a run, but on a stack with autodeploy on it stops the automatic apply until someone confirms, so tell those teams before you turn it on.',
            ],
            [
                'A way through, kept in git',
                'Sometimes a destroy is planned, like tearing down an old environment. Build the way through into the rule itself, for example a label on the stack that a reviewed pull request adds, so the exception is written down and can be taken back. Never switch the policy off to get past it.',
            ],
        ],
    ),
)

lesson(MODULE, 'plan_policy',
    title='Policy as code',
    checked='2026-11-26',
    sources=[source('Policy', 'https://docs.spacelift.io/concepts/policy'), source('Plan policy', 'https://docs.spacelift.io/concepts/policy/terraform-plan-policy'), source('Policy language (Rego)', 'https://www.openpolicyagent.org/docs/policy-language'), source('Tests: mocks (mock_provider)', 'https://developer.hashicorp.com/terraform/language/tests/mocking')],
    learn=[
        "Last lesson you wrote one rule. **Policy as code** is a list of such rules that runs on every plan, as a Spacelift plan policy or a `terraform test`, so a review rule that lives in people's heads can't get skipped on a busy day. Add a second rule: never open workspaces or storage to the public internet. Each rule checks every change on its own, so one change can break two rules.",
        'A Spacelift plan policy can **deny** (fail the run, in red) or **warn** (print in yellow; the run doesn\'t fail). One catch: on a stack with **autodeploy** on, a tracked run with a warning doesn\'t apply by itself. It waits for a person to confirm it. Roll a new rule out as a warning first, so you see what it would have blocked before it blocks anyone, and tell the teams with autodeploy on before you do.',
    ],
    example=example('Two rules', 'rule 1: protected type + delete  → "... would be destroyed"\nrule 2: public access on         → "... allows public network access"'),
    check=question(
        'Why roll out a new policy as a warning first?',
        ['So the run still applies while the rule is tested', 'To see what it would block before it blocks anyone', 'Because a deny rule needs an admin to approve it'],
        answer=1,
        why='A warning shows you every plan the rule would have stopped, mistakes in the rule included, without failing any run. Once it flags only real problems, switch it to deny.',
    ),
    angle=angle(
        pattern='Two separate rules per change',
        text="The big idea: policy as code runs your review rules on every plan, starting with never destroying data you can't recreate and never opening things to the public internet. Your code goes through the changes in order and asks two separate `if` questions about each one. The first flags a protected type with a delete action. The second flags `public_access` being `True`. Neither question stops the other, so one change can get both messages, rule 1 first.",
        say='"[[Policy as code|A code review|A unit test::Rules written as code that run on every plan.]] checks our review rules on every plan. I check each change against every rule [[separately|once in total|only if the first passes::Each rule gets its own look at every change.]], so I report [[every problem|the first problem|the worst problem::Stopping early would hide the rest.]], even two from the same change."',
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
                'Roll a new rule out as a warning, see what it would have blocked, then make it a deny. On autodeploy stacks a warning holds the apply for a person to confirm, so warn those teams first.',
            ],
            [
                'Test the policy too',
                'Policies are code: keep sample plans that should pass and fail, and check them in CI.',
            ],
        ],
    ),
)

POLICY_REGO = """# policies/no_catalog_deletes.rego
package spacelift

deny contains msg if {
  some rc in input.terraform.resource_changes
  rc.type == "databricks_catalog"
  "delete" in rc.change.actions
  msg := sprintf("%s would be deleted", [rc.address])
}"""

POLICY_TEST_ONE = """# policies/no_catalog_deletes_test.rego
package spacelift

test_deleting_a_catalog_is_denied if {
  count(deny) == 1 with input as {"terraform": {"resource_changes": [
    {"address": "databricks_catalog.sales", "type": "databricks_catalog",
     "change": {"actions": ["delete"]}}]}}
}"""


lesson(MODULE, 'policy_testing',
    title='Testing a policy before it blocks',
    checked='2026-11-08',
    sources=[source('Policy: testing policies', 'https://docs.spacelift.io/concepts/policy'), source('Plan policy', 'https://docs.spacelift.io/concepts/policy/terraform-plan-policy'), source('Policy testing', 'https://www.openpolicyagent.org/docs/policy-testing')],
    learn=[
        "A plan policy is code, written in Rego, and a wrong rule hurts either way. Too loose, and it lets a catalog delete through. Too strict, and it blocks every team's runs on a Monday morning.",
        "So test it like code. Next to `no_catalog_deletes.rego` you keep `no_catalog_deletes_test.rego`. Each test is a rule whose name starts with **`test_`**. It hands the policy a made-up plan with `with input as {...}` and checks the answer. `opa test policies/` runs them all and prints PASS or FAIL for each.",
        "Test every rule **both ways**: one plan it must stop, and one it must let through. A rule tested only on bad plans may be blocking good ones too, and you won't know until a team is stuck.",
        "Make the made-up plans look like real ones. A replacement shows as `[\"delete\", \"create\"]`, so a test with a `-/+` plan tells you whether your rule treats a replacement as a delete. Spacelift's policy workbench can keep samples of real inputs, if the policy has a `sample` rule, to copy from.",
    ],
    example=example('A rule and its two tests', POLICY_REGO + """

# policies/no_catalog_deletes_test.rego
test_deleting_a_catalog_is_denied if {
  count(deny) == 1 with input as {"terraform": {"resource_changes": [
    {"address": "databricks_catalog.sales", "type": "databricks_catalog",
     "change": {"actions": ["delete"]}}]}}
}

test_adding_a_schema_is_allowed if {
  count(deny) == 0 with input as {"terraform": {"resource_changes": [
    {"address": "databricks_schema.raw", "type": "databricks_schema",
     "change": {"actions": ["create"]}}]}}
}

$ opa test policies/
PASS: 2/2"""),
    check=question(
        'Your policy has one test: a plan deleting a catalog is denied. It passes. What is missing?',
        [
            'A test that a safe plan is allowed',
            'A test with two catalogs in it',
            'Nothing: one test is enough',
        ],
        answer=0,
        why='One test only proves the rule stops a bad plan. Without a test that a good plan gets through, the rule could be blocking everything.',
    ),
    angle=angle(
        pattern='One plan to stop, one to let through',
        text='The big idea: a policy test hands the rule a made-up plan and checks its answer, and every rule needs a plan it must stop and a plan it must let through. Your code runs each test: it works out whether the rule would deny that test\'s changes, compares that with what the test expected, and lists the tests that failed. It is like testing a door lock with the right key and a wrong one: a lock that never opens also keeps burglars out.',
        say="\"I test every rule both ways: one plan it must [[deny|ignore|apply::Stop it.]] and one it must [[allow|delete|import::Let it through.]]. Then I run [[opa test|terraform plan|git push::The command that runs every test_ rule.]] before the policy goes anywhere near a stack.\"",
        classic=None,
    ),
    exercise=exercise(
        title='Which Policy Tests Fail?',
        topic='policy',
        difficulty='medium',
        fn='failing_tests',
        prompt="""Your function gets `tests` and `protected`.

- `tests` is a list of dicts like `{"name": "deleting_a_catalog", "changes": [...], "expect": "deny"}`. Each change is a dict like `{"type": "databricks_catalog", "actions": ["delete"]}`. `expect` is `"deny"` or `"allow"`.
- `protected` is the list of resource types the rule guards, like `["databricks_catalog"]`.

The rule **denies** a test's plan if any change has a `type` in `protected` and `"delete"` in its `actions` (a replacement, `["delete", "create"]`, counts).

A test **fails** when what the rule does doesn't match `expect`. Return the names of the failing tests, in order. An empty list means every test passes.""",
        pattern='For each test, work out the answer, compare with what was expected, and keep the ones that differ.',
        target='one pass over the tests and their changes',
        realworld="This is what `opa test` does for a Spacelift plan policy: run the rule against made-up plans and report the ones where it said the wrong thing. A test with a replacement plan is how you find out whether your rule treats `-/+` as a delete.",
        practice=practice(
            intro='A new plan policy is about to reach every stack. Check its tests before it blocks anyone.',
            explain='A policy test hands the rule a made-up plan and checks its answer. You spotted a rule tested only one way, checked how it treats a replacement, read a failed test as a rule that blocks too much, and caught a test that never runs because of its name.',
            pattern='Test it both ways',
            realworld='When you review a new plan policy, you look for a plan it must stop and a plan it must let through, and a replacement among the made-up plans. When opa test reports a failure, you ask whether the rule or the test is wrong before you change either.',
            asks=[
                ask('This policy has one test. What could still be wrong without any test noticing?', ['It could block safe plans', 'It could run too slowly', 'Its name could be too long'], answer=0,
                    evidence=evidence('code', title='The policy and its only test', text=POLICY_REGO + "\n\n" + POLICY_TEST_ONE),
                    clue='The only test checks one direction. What about the other?',
                    why='Nothing checks that a good plan gets through. If a mistake made the rule deny everything, this test would still pass.',
                    wrong=[None, 'Speed isn\'t what a missing test hides here.', 'Names don\'t change what a rule decides.']),
                ask('Does the rule deny this plan?', ['Yes: a replacement deletes', 'No: it isn\'t a delete'], answer=0,
                    evidence=evidence('plan', title='Stack sales-service-dev · proposed',
                        summary=[['1', 'to add', 'a'], ['0', 'to change', ''], ['1', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-/+', 'address': 'databricks_catalog.sales', 'note': 'storage_root changed: forces replacement'},
                        ]),
                    clue='In the plan\'s data, a -/+ has two actions. Is one of them the one the rule looks for?',
                    why='A replacement\'s actions are ["delete", "create"], and the rule checks for "delete" in the list. So it denies, which is what you want for a catalog.',
                    wrong=[None, 'Look at the actions list a -/+ has: the old catalog is deleted first.']),
                ask('What does this result tell you?', ['The rule blocks a safe plan', 'The test file is broken', 'OPA isn\'t installed'], answer=0,
                    evidence=evidence('code', title='opa test policies/', text="""policies/no_catalog_deletes_test.rego:
data.spacelift.test_deleting_a_catalog_is_denied: PASS
data.spacelift.test_adding_a_schema_is_allowed: FAIL
--------------------------------------------------
PASS: 1/2
FAIL: 1/2"""),
                    clue='Which test failed, and what was it checking?',
                    why='The test that a new schema is allowed failed, so the rule denied a plan it should let through. Look at the rule\'s conditions before it reaches a single stack.',
                    wrong=[None, 'One test passed, so the file runs fine.', 'Without OPA nothing would PASS or FAIL.']),
                ask('`opa test` says PASS: 1/1, but there are two tests in the file. Why?', ['One name lacks test_', 'OPA runs one at random', 'The second one passed twice'], answer=0,
                    evidence=evidence('code', title='policies/no_catalog_deletes_test.rego', text="""test_deleting_a_catalog_is_denied if {
  count(deny) == 1 with input as {...}
}

adding_a_schema_is_allowed if {
  count(deny) == 0 with input as {...}
}"""),
                    clue='Compare how the two rules\' names start.',
                    why='opa test only runs rules whose names start with test_. The second one is never run, so it can never fail. Rename it and watch it run.',
                    wrong=[None, 'opa test runs every test_ rule, every time.', 'Each test runs once and counts once.']),
            ],
        ),
        starter="""def failing_tests(tests, protected):
    # your code here
    pass
""",
        solution="""def failing_tests(tests, protected):
    failing = []
    for t in tests:
        denied = False
        for c in t["changes"]:
            if c["type"] in protected and "delete" in c["actions"]:
                denied = True
        got = "deny" if denied else "allow"
        if got != t["expect"]:
            failing.append(t["name"])
    return failing
""",
        cases=[
            case([
                {'name': 'deleting_a_catalog', 'changes': [{'type': 'databricks_catalog', 'actions': ['delete']}], 'expect': 'deny'},
                {'name': 'adding_a_schema', 'changes': [{'type': 'databricks_schema', 'actions': ['create']}], 'expect': 'allow'},
            ], ['databricks_catalog'], expected=[], sample=True),
            case([
                {'name': 'replacing_a_catalog', 'changes': [{'type': 'databricks_catalog', 'actions': ['delete', 'create']}], 'expect': 'allow'},
            ], ['databricks_catalog'], expected=['replacing_a_catalog']),
            case([
                {'name': 'deleting_a_schema', 'changes': [{'type': 'databricks_schema', 'actions': ['delete']}], 'expect': 'deny'},
            ], ['databricks_catalog'], expected=['deleting_a_schema']),
            case([
                {'name': 'mixed_plan', 'changes': [
                    {'type': 'databricks_schema', 'actions': ['create']},
                    {'type': 'databricks_catalog', 'actions': ['delete']},
                ], 'expect': 'deny'},
                {'name': 'empty_plan', 'changes': [], 'expect': 'allow'},
            ], ['databricks_catalog'], expected=[]),
            case([], ['databricks_catalog'], expected=[]),
        ],
        guided="""def failing_tests(tests, protected):
    # Replace every ___ with real code, then run the tests.
    failing = []
    for t in tests:
        denied = False
        for c in t["changes"]:
            if c["type"] in protected and ___:
                denied = True
        got = "deny" if denied else "allow"
        if ___:
            failing.append(t["name"])
    return failing
""",
        fills=['"delete" in c["actions"]', 'got != t["expect"]'],
        concepts=[
            [
                'A flag',
                'Start a variable at `False` and set it to `True` when you find what you are looking for. After the loop, it tells you whether you ever found it.',
                """found = False
for x in [1, 5, 2]:
    if x > 4:
        found = True""",
            ],
            [
                'Choosing between two values',
                '`a if condition else b` picks one of two values in a single line.',
                """"deny" if True else "allow"    # "deny\"""",
            ],
        ],
        byhand='The sample: the first test\'s plan deletes a catalog, so the rule denies, as expected. The second creates a schema, so the rule allows, as expected. No test fails: [].',
        why='Each test looks at each of its changes once.',
        gotchas=[
            [
                'Names start with test_',
                'opa test only runs rules named test_ something. A test without the prefix is never run, so it never fails.',
            ],
            [
                'Same Rego version as Spacelift',
                'Spacelift supports Rego v0 and v1. Test with the same version the policy is set to, or a rule can pass locally and fail on the stack.',
            ],
            [
                'One folder, many policies',
                'Every file in `policies/` with `package spacelift` joins the same package, so `opa test policies/` adds up the rules of every policy. A test can fail because another policy\'s deny fired. Spacelift checks each attached policy on its own, so test a policy with only its own files: `opa test no_catalog_deletes.rego no_catalog_deletes_test.rego`.',
            ],
        ],
    ),
)


APPROVAL_REGO = """# two_reviews.rego (an approval policy)
package spacelift

approvals := input.reviews.current.approvals
author := input.run.creator_session.identity.ulid

# two approvals, and the run may go on
approve if count(approvals) >= 2

# but never one from its author
reject if {
  some a in approvals
  a.identity.ulid == author
}"""

lesson(MODULE, 'who_confirms',
    title='Who can apply this run?',
    checked='2026-11-26',
    sources=[source('Approval policy', 'https://docs.spacelift.io/concepts/policy/approval-policy'), source('Tracked run (deployment)', 'https://docs.spacelift.io/concepts/run/tracked'), source('Plan policy', 'https://docs.spacelift.io/concepts/policy/terraform-plan-policy')],
    learn=[
        "A tracked run plans, then stops at **Unconfirmed** and waits. Three things decide whether it goes on to apply. **Autodeploy** is a stack setting that skips the wait, so a clean plan applies by itself. **Confirm** is a person clicking Confirm (or Discard). An **approval policy** is a rule in Rego, written by the platform team, that can ask for reviews before the run may go on.",
        "Without an approval policy, anyone with write access to the stack can confirm a run, including the person who started it. Spacelift doesn't stop you confirming your own run. If your team wants a second person, it needs an approval policy that says so.",
        "An approval policy has two kinds of rule, **approve** and **reject**. Approve alone: the run goes on. Reject alone: the run stops. Neither, or both at once: the answer is **undecided**, and the run keeps waiting for more reviews. It waits; it doesn't fail.",
        "Counting approvals never checks who gave them. To stop people approving their own run, add a reject rule that compares each approver with the person who started the run (`input.run.creator_session`).",
    ],
    example=example('Two reviews, and never your own', APPROVAL_REGO),
    check=question(
        'Your stack has no approval policy and autodeploy is off. You started a tracked run. Can you click Confirm yourself?',
        [
            'Yes: nothing stops you',
            'No: Spacelift needs a second person',
            'Only an admin can confirm',
        ],
        answer=0,
        why='Without an approval policy, anyone with write access can confirm a run, you included. A second person is a team rule, and it needs an approval policy to make it stick.',
    ),
    angle=angle(
        pattern='Two rules, then combine',
        text='The big idea: an approval policy works out two rules on their own, approve and reject, then combines them. Approve alone lets the run go on, reject alone stops it, and both or neither leaves it undecided, so it waits. Your code does the same: count the approvals, check whether the person who started the run is among them, then pick one of three answers. It is like a club door with two staff: one lets you in, one turns you away, and if they disagree you wait outside until it is sorted.',
        say='"Without an approval policy, anyone who can write to the stack can [[confirm|delete|import::The button that lets a waiting run apply.]] a run, even their own. To need a second person, I add a [[reject|warn|deny::The approval policy\'s rule that stops a run.]] rule that checks who approved it."',
        classic=None,
    ),
    stack=stack('Spacelift: the policy in its Terraform provider', """resource "spacelift_policy" "two_reviews" {
  name   = "two-reviews-prod"
  type   = "APPROVAL"
  body   = file("policies/two_reviews.rego")
  labels = ["autoattach:env:prod"] # every stack labelled env:prod
}"""),
    exercise=exercise(
        title='What Does the Approval Policy Say?',
        topic='policy',
        difficulty='easy',
        fn='approval_verdict',
        prompt="""Your function gets four things:

- `approvals`: the names of the people who approved the run, like `["ana", "ben"]`.
- `author`: the name of the person who started the run.
- `need`: how many approvals the policy asks for.
- `block_self`: `True` if the policy also has the rule that rejects an approval from the author.

Work out the two rules on their own:

- **approve** fires when there are at least `need` approvals.
- **reject** fires when `block_self` is `True` and `author` is in `approvals`.

Then return:

- `"approve"` if only approve fires
- `"reject"` if only reject fires
- `"undecided"` if both fire, or neither""",
        pattern='Work out each rule as True or False first, then combine the two.',
        target='a few checks, no loops',
        realworld='This is how a Spacelift approval policy decides each time a run reaches it. Undecided is the answer people forget: it is not a failure, the run just waits for more reviews. When approve and reject both fire, neither wins, so a run with the author\'s approval and two others still waits.',
        practice=practice(
            intro='A run is waiting and nobody knows why. Read the approval policy the way the platform team does.',
            explain='Three things decide whether a tracked run applies: autodeploy, a person clicking Confirm, and an approval policy. You found a policy that never attached, saw that approve and reject together leave a run undecided, and saw that counting approvals never checks who gave them.',
            pattern='Approve, reject, or wait',
            realworld='When a run sits at Unconfirmed or a teammate says "I approved my own run", you open the stack\'s approval policies, check they are attached, and read which rule fired before you change anything.',
            asks=[
                ask('Runs on the prod stack apply after anyone confirms, with no reviews. The team thought this policy needed two. Why?', ['The policy never attached to it', 'Reviews are off at weekends', 'The policy approves every run'], answer=0,
                    evidence=evidence('code', title='The policy and the stack', text="""policy  two-reviews-prod   type APPROVAL
  labels: autoattach:env:prd

stack   sales-service-prod
  labels: env:prod, team:sales"""),
                    clue='Compare the label the policy looks for with the stack\'s labels, letter by letter.',
                    why='A policy labelled autoattach:env:prd attaches to stacks labelled env:prd. This stack says env:prod, so no approval policy is attached and anyone with write access can confirm.',
                    wrong=[None, 'Nothing in Spacelift switches reviews off by the day.', 'If it were attached, it would ask for two approvals first.']),
                ask('Ana approved the run and Ben rejected it. What happens now?', ['It waits: the answer is undecided', 'It applies: one approval is enough', 'It stops at once and can\'t go on'], answer=0,
                    evidence=evidence('code', title='The approval policy', text="""approve if {
  count(input.reviews.current.approvals) >= 1
}

reject if {
  count(input.reviews.current.rejections) >= 1
}"""),
                    clue='Both rules can fire at once. What does Spacelift do when they disagree?',
                    why='Approve and reject both fire, and neither wins: the answer is undecided, so the run keeps waiting. Ana and Ben need to settle it, for example by Ben changing his review.',
                    wrong=[None, 'The reject rule fired too, so approve doesn\'t win on its own.', 'Reject alone would stop it. With approve firing as well, it waits.']),
                ask('Cy says: "The policy needs one approval, so I approved my own run and it went through." What is going on?', ['The rule only counts approvals', 'Spacelift had a bug that day', 'Cy must be an admin on it'], answer=0,
                    evidence=evidence('code', title='The approval policy', text="""approve if {
  count(input.reviews.current.approvals) >= 1
}

# run started by: cy
# approvals:      cy"""),
                    clue='Does anything in the rule look at who approved?',
                    why='The rule counts approvals and never checks who gave them, so Cy\'s own approval counts. Add a reject rule that compares each approver with the person who started the run.',
                    wrong=[None, 'Spacelift did what the policy said: one approval, and it had one.', 'Admins aren\'t involved: any approval counts here.']),
                ask('Which rule stops someone approving their own run?', ['A reject rule comparing approver and author', 'An approve rule needing two approvals', 'A plan policy that denies deletes'], answer=0,
                    alone=True,
                    clue='Which rule looks at who approved, not how many?',
                    why='Only a rule that compares each approver with the person who started the run can catch it, and it has to be a reject rule so it stops the run. Needing two approvals still lets the author be one of them.',
                    wrong=[None, 'The author can still be one of the two.', 'A plan policy looks at the plan, not at who approved.']),
            ],
        ),
        starter="""def approval_verdict(approvals, author, need, block_self):
    # your code here
    pass
""",
        solution="""def approval_verdict(approvals, author, need, block_self):
    approve = len(approvals) >= need
    reject = block_self and author in approvals
    if approve and not reject:
        return "approve"
    if reject and not approve:
        return "reject"
    return "undecided"
""",
        cases=[
            case(['ana', 'ben'], 'cy', 2, True, expected='approve', sample=True),
            case(['ana'], 'cy', 2, True, expected='undecided'),
            case(['cy'], 'cy', 1, True, expected='undecided'),
            case(['cy'], 'cy', 2, True, expected='reject'),
            case(['cy'], 'cy', 1, False, expected='approve'),
            case(['ana', 'ben', 'cy'], 'cy', 2, True, expected='undecided'),
            case([], 'cy', 0, True, expected='approve'),
            case([], 'cy', 1, False, expected='undecided'),
        ],
        guided="""def approval_verdict(approvals, author, need, block_self):
    # Replace every ___ with real code, then run the tests.
    approve = len(approvals) >= need
    reject = ___
    if approve and not reject:
        return "approve"
    if ___:
        return "reject"
    return "undecided"
""",
        fills=['block_self and author in approvals', 'reject and not approve'],
        concepts=[
            [
                'Counting a list',
                '`len(x)` gives how many items a list has.',
                """len(["ana", "ben"])   # 2""",
            ],
            [
                'Is it in the list?',
                '`x in list` is `True` when the list holds `x`.',
                """"cy" in ["ana", "cy"]   # True""",
            ],
        ],
        byhand='The sample: there are two approvals and the policy needs two, so approve fires. block_self is on, but cy, who started the run, isn\'t among the approvers, so reject doesn\'t fire. Only approve fires: return "approve".',
        why='Two checks and one decision.',
        gotchas=[
            [
                'Autodeploy skips the wait',
                'With autodeploy on, a clean tracked run doesn\'t stop at Unconfirmed, so nobody is asked there. If a person must look first, turn autodeploy off, or have a plan policy warn, which holds the run for someone to confirm.',
            ],
            [
                'Only the newest review counts',
                'If someone approves and later rejects, the policy sees only the reject. Each person\'s newest review is the one that counts.',
            ],
        ],
    ),
)


TASK_REGO = """# hold_tasks.rego (an approval policy)
package spacelift

approvals := input.reviews.current.approvals
author := input.run.creator_session.identity.ulid

# any run that isn't a task goes on
approve if input.run.type != "TASK"

# a task: one approval from someone else
approve if {
  input.run.type == "TASK"
  some a in approvals
  a.identity.ulid != author
}"""

lesson(MODULE, 'approved_task',
    title='Running a one-off command safely',
    checked='2026-11-26',
    sources=[source('Task', 'https://docs.spacelift.io/concepts/run/task'), source('Approval policy', 'https://docs.spacelift.io/concepts/policy/approval-policy'), source('Plan policy', 'https://docs.spacelift.io/concepts/policy/terraform-plan-policy')],
    learn=[
        "A **task** is a one-off command run on a stack, like `terraform state list` or a small script that fixes one thing. It is a kind of run: it starts like any other, then runs your command in the stack's own environment instead of planning. Spacelift keeps a record of every task and who started it.",
        "A task makes **no plan**, and a plan policy only checks plans. So `terraform state rm`, or a script that revokes grants, can change things no plan policy ever sees. Without an approval policy, anyone with write access to the stack can start one.",
        "Guard tasks with an **approval policy**: approve every run that isn't a task, so normal work flows as before, and make a task wait until someone other than its author approves it.",
        "Write task scripts so a mistake is cheap. Make a **dry run** the default: show what would change, and only change it when told to. Check every input before acting. Do nothing if the change is already there. Then read the result back.",
    ],
    example=example('Hold tasks, let everything else through', TASK_REGO),
    check=question(
        'Your stack has a plan policy that denies deleting a catalog, and no approval policy. Someone runs a task: `terraform state rm databricks_catalog.sales`. What stops it?',
        [
            'Nothing: a task makes no plan',
            'The plan policy denies it',
            'Spacelift asks an admin first',
        ],
        answer=0,
        why='A task runs a command, not a plan, so the plan policy never sees it, and with no approval policy anyone with write access can start one. Terraform forgets the catalog, and nothing checked first.',
    ),
    angle=angle(
        pattern='Let runs through, hold tasks',
        text='The big idea: tasks skip plan policies, so an approval policy has to hold them, and it must still approve every ordinary run or those wait too. Your code checks a run in order: not a task means approve; a task whose command is on the safe list means approve; a task someone other than its author approved means approve; anything else is undecided, so it waits. It is like a building where staff walk in, visitors on the guest list walk in, and anyone else waits at the desk until a member of staff signs them in.',
        say='"A task makes no [[plan|commit|backup::The preview Terraform makes before it changes anything.]], so plan policies never see it. I guard tasks with an [[approval policy|alert|branch rule::The policy that can make a run wait for reviews.]] and write the script so a mistake is cheap: a [[dry run|fast run|second run::Show what would change, change nothing.]] first."',
        classic=None,
    ),
    stack=stack('A task script that is safe by default', """# fix_grants.py: run as a task, dry run unless told otherwise
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

extra = extra_grants(args.catalog)      # check before acting
if not extra:
    print("nothing to do")              # already fixed: do nothing
for grant in extra:
    print("would revoke" if not args.apply else "revoking", grant)
    if args.apply:
        revoke(grant)
print("left now:", extra_grants(args.catalog))   # read it back"""),
    exercise=exercise(
        title='Should This Run Wait?',
        topic='policy',
        difficulty='easy',
        fn='task_verdict',
        prompt="""Your function gets `run` and `allowed`.

- `run` is a dict like `{"type": "TASK", "command": "terraform state list", "author": "cy", "approvals": ["ana"]}`. `type` is `"PROPOSED"`, `"TRACKED"` or `"TASK"`.
- `allowed` is the list of task commands that are safe to run without a review, like `["terraform state list"]`.

Return `"approve"` or `"undecided"`, checking in this order:

- not a task -> `"approve"`
- a task whose `command` is exactly one of `allowed` -> `"approve"`
- a task with an approval from anyone other than its `author` -> `"approve"`
- anything else -> `"undecided"`""",
        pattern='Let ordinary runs through first, then check the safe list, then look for someone else\'s approval.',
        target='one short loop over the approvals',
        realworld='This is a Spacelift approval policy that holds tasks: read-only commands on a safe list run straight away, and anything else waits for a second person. Its first rule matters most: an approval policy that forgets to approve ordinary runs makes every tracked run on the stack wait as well.',
        practice=practice(
            intro='Someone needs to run a one-off command on a production stack. Decide how it should run, and what guards it.',
            explain='A task runs a command, not a plan, so plan policies never check it. You kept initialization on, kept secrets out of a log that is kept for good, saw an approval policy that held every run by mistake, and asked for a dry run before a script changed anything.',
            pattern='No plan, so guard it another way',
            realworld='Before you run a task on a shared stack, you check the command against the safe list, ask for a review if it changes anything, and run the script as a dry run first. When a task waits, you look for the approval policy that holds it.',
            asks=[
                ask('You need `terraform state list` on the stack. Should you switch on "Skip initialization"?', ['No: state commands need init', 'Yes: init only matters for plans', 'Yes: it makes the task safer'], answer=0,
                    evidence=evidence('code', title='New task · sales-service-prod', text="""Command               terraform state list
Skip initialization   off (default)"""),
                    clue='Where does terraform state list read the state from, and what sets that up?',
                    why='Initialization connects Terraform to where the state is kept and loads the providers. Without it, state commands have nothing to read. Skipping it is for rare jobs, like moving the stack to a new tool version.',
                    wrong=[None, 'State commands also need the backend that init sets up.', 'Skipping init changes what works, not how safe it is.']),
                ask('A teammate wants to run `terraform state pull` as a task, to look at the state. Is that a good idea?', ['No: the log would show secrets', 'Yes: it only reads the state', 'Yes: tasks hide their output'], answer=0,
                    evidence=evidence('claim', text='Just run `terraform state pull` as a task and read the whole state in the log.'),
                    clue='Where does the output of a task go, and for how long?',
                    why='state pull prints the whole state, and state can hold secret values in plain text. A task\'s log is kept for good, so the secrets would be too. Read state on your own computer, if at all.',
                    wrong=[None, 'Reading is the problem: everything it reads ends up in the log.', 'A task\'s output is shown and kept, which is the trouble here.']),
                ask('The team adds this approval policy to hold tasks. What happens to ordinary tracked runs?', ['They wait too: nothing approves them', 'They apply as they did before', 'They fail as soon as they start'], answer=0,
                    evidence=evidence('code', title='policies/hold_tasks.rego', text="""approve if {
  input.run.type == "TASK"
  count(input.reviews.current.approvals) >= 1
}"""),
                    clue='Which runs does this approve rule ever fire for?',
                    why='The only approve rule is for tasks, so for any other run nothing fires: undecided, and the run waits. Add `approve if input.run.type != "TASK"` so ordinary runs go on as before.',
                    wrong=[None, 'Once a policy is attached, every run needs it to approve.', 'Undecided waits; only a reject rule stops a run.']),
                ask('Before this script runs as a task on prod, what is it missing?', ['A dry run by default', 'A longer print message', 'A faster loop inside'], answer=0,
                    evidence=evidence('code', title='fix_grants.py', text="""for grant in extra_grants(catalog):
    revoke(grant)
print("done")"""),
                    clue='What would you see if the list of grants were wrong?',
                    why='As written it revokes straight away. Make it print what it would revoke unless it is told to apply, so a wrong list costs nothing, and read the grants back afterwards.',
                    wrong=[None, 'A longer message doesn\'t stop a wrong revoke.', 'Speed isn\'t the risk: changing the wrong thing is.']),
            ],
        ),
        starter="""def task_verdict(run, allowed):
    # your code here
    pass
""",
        solution="""def task_verdict(run, allowed):
    if run["type"] != "TASK":
        return "approve"
    if run["command"] in allowed:
        return "approve"
    for name in run["approvals"]:
        if name != run["author"]:
            return "approve"
    return "undecided"
""",
        cases=[
            case({'type': 'TRACKED', 'command': None, 'author': 'cy', 'approvals': []}, ['terraform state list'], expected='approve', sample=True),
            case({'type': 'TASK', 'command': 'terraform state list', 'author': 'cy', 'approvals': []}, ['terraform state list'], expected='approve'),
            case({'type': 'TASK', 'command': 'terraform state rm databricks_catalog.sales', 'author': 'cy', 'approvals': []}, ['terraform state list'], expected='undecided'),
            case({'type': 'TASK', 'command': 'python fix_grants.py --apply', 'author': 'cy', 'approvals': ['cy']}, ['terraform state list'], expected='undecided'),
            case({'type': 'TASK', 'command': 'python fix_grants.py --apply', 'author': 'cy', 'approvals': ['cy', 'ana']}, ['terraform state list'], expected='approve'),
            case({'type': 'PROPOSED', 'command': None, 'author': 'ben', 'approvals': []}, [], expected='approve'),
            case({'type': 'TASK', 'command': 'terraform state list', 'author': 'ben', 'approvals': []}, [], expected='undecided'),
        ],
        guided="""def task_verdict(run, allowed):
    # Replace every ___ with real code, then run the tests.
    if run["type"] != "TASK":
        return "approve"
    if ___:
        return "approve"
    for name in run["approvals"]:
        if ___:
            return "approve"
    return "undecided"
""",
        fills=['run["command"] in allowed', 'name != run["author"]'],
        concepts=[
            [
                'Returning early',
                '`return` leaves the function at once, so later checks only run when the earlier ones didn\'t match.',
                """def size(n):
    if n > 10:
        return "big"
    return "small\"""",
            ],
            [
                'Looping until you find one',
                'A loop can `return` as soon as it finds what it is looking for, without checking the rest.',
                """for name in ["cy", "ana"]:
    if name != "cy":
        print(name)   # ana""",
            ],
        ],
        byhand='The sample is a tracked run, not a task, so the first check approves it straight away: return "approve". The command and approvals don\'t matter for it.',
        why='At most one look at each approval.',
        gotchas=[
            [
                'A task\'s log is kept for good',
                'Never run a command that prints state or a token in a task, like `terraform state pull` or a script that echoes a secret. Whatever it prints stays in the record.',
            ],
            [
                'Tasks wait their turn',
                'No two tasks run at once on a stack, and a task never runs while a tracked run is going. If a task sits waiting, look for a run in progress first.',
            ],
        ],
    ),
)


planned(MODULE, 'drift_detection', 'Drift detection', 'Finding changes made outside Terraform before they surprise the next apply.')
CONTEXT_HCL = """resource "spacelift_context" "azure" {
  name   = "azure-login"
  labels = ["autoattach:azure"]
}

resource "spacelift_environment_variable" "tenant" {
  context_id = spacelift_context.azure.id
  name       = "ARM_TENANT_ID"
  value      = var.tenant_id
  write_only = false # plain: the default is secret
}

resource "spacelift_environment_variable" "secret" {
  context_id = spacelift_context.azure.id
  name       = "ARM_CLIENT_SECRET"
  value      = "" # pasted in by a person
  write_only = true
  lifecycle {
    ignore_changes = [value]
  }
}"""

lesson(MODULE, 'contexts_secrets',
    title='Contexts and secrets',
    checked='2026-11-26',
    sources=[source('Context', 'https://docs.spacelift.io/concepts/configuration/context'), source('Environment', 'https://docs.spacelift.io/concepts/configuration/environment'), source('Spaces: how access works', 'https://docs.spacelift.io/concepts/spaces/how-access-works'), source('OIDC: Microsoft Azure', 'https://docs.spacelift.io/integrations/cloud-providers/oidc/azure-oidc')],
    learn=[
        "A **context** is a bundle of settings that lives apart from any stack: environment variables, **mounted files** (files placed in the run's folder, like a settings file), and **hooks** (short scripts that run before or after a phase, like `before_init`). Attach one context to many stacks, and a change to it reaches all of them.",
        "You attach a context by hand, or by **label**: give the context the label `autoattach:azure`, and every stack with the plain label `azure` gets it. A context lives in a **Space**: a folder in Spacelift that decides who can see and change what is in it. Spaces sit in a tree, and a stack in a Space below can use the context only while its Space **inherits** from the one above. The web app turns inheritance on for a new Space; a Space made in Terraform has it off unless you set `inherit_entities = true`.",
        "When the same variable is set in two places, **the stack's own setting wins** over any context. Say a context sets `RUNBOOK_REF = main`, the branch of runbook code to use. Set `RUNBOOK_REF = fix-123` on one stack, and that stack uses fix-123. Delete it from the stack afterwards, and main comes back.",
        "A variable is **plain**, which anyone with access can read, or **secret**, which only runs and tasks can see. In the Terraform provider, `write_only` decides, and it **defaults to true**, so a plain setting needs `write_only = false`. The \"(sensitive value)\" you see in a plan is something else: the provider hides every value in plans, secret or not. Better than any stored secret, where your Spacelift plan offers it, is **OIDC** (OpenID Connect): each run proves who it is to Azure with a token that lasts minutes, so no password is stored anywhere.",
    ],
    example=example('One context, many stacks', """context azure-login
  label: autoattach:azure
  ARM_TENANT_ID      plain
  ARM_CLIENT_SECRET  secret

stack sales-foundation-dev
  labels: azure, terraform
  gets azure-login

stack sales-service-dev
  labels: azure, terraform
  gets azure-login"""),
    check=question(
        'A context sets `RUNBOOK_REF = main`. One stack also sets `RUNBOOK_REF = fix-123` on itself. Which value does that stack\'s run use?',
        [
            'fix-123: the stack wins',
            'main: the context wins',
            'Whichever was set last',
        ],
        answer=0,
        why='A setting on the stack beats the same name from any context. Delete it from the stack and the context\'s main comes back.',
    ),
    angle=angle(
        pattern='The label goes on the stack, the prefix on the context',
        text='The big idea: a context is shared settings, and it reaches a stack by label. Your code finds which contexts attach by label: for each context, it looks for a label that starts with `autoattach:`, takes what comes after, and attaches the context when that is `*` or one of the stack\'s labels. It is like a mailing list: you subscribe by putting the list\'s name on yourself, and the list goes to everyone who did.',
        say='"A [[context|module|branch::Shared settings, attached to many stacks.]] holds settings many stacks share, and attaches by label. If the stack sets the same variable itself, the [[stack|context|oldest one::The setting closest to the run.]] wins. Secrets stay [[write-only|plain|in Git::Only runs and tasks can see them.]]."',
        classic=None,
    ),
    stack=stack('Terraform: a context with a plain setting and a secret slot', CONTEXT_HCL),
    exercise=exercise(
        title='Which Contexts Attach by Label?',
        topic='spacelift',
        difficulty='easy',
        fn='auto_attached',
        prompt="""Your function gets `stack_labels`, a list like `["azure", "terraform"]`, and `contexts`, a dict from each context's name to its labels, like `{"azure-login": ["autoattach:azure"]}`.

A context attaches to the stack when it has a label that starts with `"autoattach:"` and the rest of that label is:

- `"*"` (every stack), or
- one of the stack's labels.

Return the names of the contexts that attach, in the order they appear in `contexts`.""",
        pattern='For each context, look at each label: is it an autoattach label, and does what follows match?',
        target='one look at each context\'s labels',
        realworld='This is how Spacelift attaches contexts by label. The prefix goes on the context, and the stack carries the plain label. A stack labelled `autoattach:azure` instead of `azure` gets nothing, and nothing says why.',
        practice=practice(
            intro='A team\'s stacks share settings through contexts. Work out what reaches each stack, and keep the secrets safe.',
            explain='A context is shared settings that attach by label, and a stack\'s own setting wins over them. You found a label on the wrong side, a test branch nobody took off a stack, a secret slot that came back empty, and the sign-in that leaves no secret to leak.',
            pattern='Find where each value really comes from',
            realworld='When a stack gets a setting you didn\'t expect, you look at its own environment first, then the contexts attached by hand, then the ones attached by label. When you set up sign-in to Azure, you ask whether OIDC is open to you before you store a secret.',
            asks=[
                ask('The context didn\'t attach to this stack. Why?', ['The prefix belongs on the context', 'Contexts only attach by hand', 'The stack needs a priority'], answer=0,
                    evidence=evidence('code', title='The context and the stack', text="""context azure-login
  labels: azure

stack sales-foundation-dev
  labels: autoattach:azure"""),
                    clue='Which of the two should carry autoattach:?',
                    why='The context carries autoattach:azure, and the stack carries the plain label azure. Here they are swapped, so nothing matches.',
                    wrong=[None, 'Contexts attach by label too: that is what autoattach is for.', 'Priority is for contexts attached by hand, and it doesn\'t make one attach.']),
                ask('A week after a test, this stack still runs code from the fix-123 branch. Why?', ['Its own setting beats the context', 'The context is out of date', 'Spacelift caches the branch'], answer=0,
                    evidence=evidence('code', title='RUNBOOK_REF', text="""context runbook: RUNBOOK_REF = main
stack sales-service-dev:
  RUNBOOK_REF = fix-123  (set on the stack)"""),
                    clue='Two places set the same variable. Which one wins?',
                    why='A setting on the stack wins over any context. Delete it from the stack, and the context\'s main comes back.',
                    wrong=[None, 'The context says main, which is what you want.', 'The value comes from the stack\'s own setting, not a cache.']),
                ask('Someone renamed the secret\'s resource block. After this apply, is the secret they pasted in still there?', ['No: the pasted value is lost', 'Yes: ignore_changes kept it', 'Yes: Terraform copies it over'], answer=0,
                    evidence=evidence('plan', title='Plan · proposed',
                        summary=[['1', 'to add', 'a'], ['0', 'to change', ''], ['1', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-', 'address': 'spacelift_environment_variable.secret', 'note': 'destroy'},
                            {'sym': '+', 'address': 'spacelift_environment_variable.client_secret', 'note': 'create (value from the code: empty)'},
                        ]),
                    clue='ignore_changes looks after a resource Terraform already has. Does it already have this one?',
                    why='To Terraform a renamed block is a new resource, so ignore_changes never applies to it, and the pasted value is lost. Use a moved block for the rename, or paste the secret in again.',
                    wrong=[None, 'ignore_changes only looks after a resource Terraform already has; this one is new.', 'Nothing copies values between two resources.']),
                ask('Which way of signing in to Azure leaves no secret to leak?', ['OIDC sign-in, one token per run', 'A client secret kept in a context', 'A client secret written in the code'], answer=0,
                    alone=True,
                    clue='Which of these stores a password somewhere, and which doesn\'t?',
                    why='With OIDC, each run swaps a short-lived Spacelift token for temporary Azure access, so nothing is stored. Spacelift offers it on paid plans; without it, a secret in a context is the next best place.',
                    wrong=[None, 'Kept safely, but it is still a long-lived secret that can leak or expire.', 'Never: anyone who can read the code can read the secret.']),
            ],
        ),
        starter="""def auto_attached(stack_labels, contexts):
    # your code here
    pass
""",
        solution="""def auto_attached(stack_labels, contexts):
    attached = []
    for name, labels in contexts.items():
        for label in labels:
            if label.startswith("autoattach:"):
                target = label[len("autoattach:"):]
                if target == "*" or target in stack_labels:
                    attached.append(name)
                    break
    return attached
""",
        cases=[
            case(['azure', 'terraform'], {'azure-login': ['autoattach:azure'], 'tf-version': ['autoattach:terraform'], 'bundle': ['databricks']}, expected=['azure-login', 'tf-version'], sample=True),
            case(['autoattach:azure'], {'azure-login': ['azure']}, expected=[]),
            case(['anything'], {'everyone': ['autoattach:*']}, expected=['everyone']),
            case([], {'azure-login': ['autoattach:azure']}, expected=[]),
            case(['azure'], {'both': ['autoattach:azure', 'autoattach:*']}, expected=['both']),
            case(['databricks'], {}, expected=[]),
        ],
        guided="""def auto_attached(stack_labels, contexts):
    # Replace every ___ with real code, then run the tests.
    attached = []
    for name, labels in contexts.items():
        for label in labels:
            if label.startswith("autoattach:"):
                target = label[len("autoattach:"):]
                if ___:
                    attached.append(name)
                    break
    return attached
""",
        fills=['target == "*" or target in stack_labels'],
        concepts=[
            [
                'startswith()',
                '`text.startswith("autoattach:")` is True when the text begins with those letters.',
                """"autoattach:azure".startswith("autoattach:")   # True""",
            ],
            [
                'Cutting off the front',
                '`text[n:]` gives the text from position n to the end, so `len(prefix)` skips the prefix.',
                """"autoattach:azure"[len("autoattach:"):]   # 'azure'""",
            ],
            [
                'break',
                '`break` stops the inner loop, so a context with two matching labels is added once.',
                """for label in ["a", "b"]:
    if label == "a":
        break""",
            ],
        ],
        byhand='The sample: azure-login has autoattach:azure, and azure is one of the stack\'s labels, so it attaches. tf-version has autoattach:terraform, and terraform is there too. bundle has only a plain label, so it never auto-attaches. Return ["azure-login", "tf-version"].',
        why='One look at each label of each context.',
        gotchas=[
            [
                'A secret slot you fill by hand',
                'Code makes the variable with an empty value and `ignore_changes = [value]`, and a person pastes the secret in the web app. The next apply leaves it alone, but if the resource is ever made again, after a rename for example, it starts empty.',
            ],
            [
                'Hooks travel with the context',
                'A context\'s hooks run on every stack it attaches to, and can only be edited in the context. A failing before hook stops the phase, so test a new hook on one stack first.',
            ],
        ],
    ),
)


ADMIN_HCL = """resource "spacelift_stack" "admin" {
  name                  = "admin"
  repository            = "platform-admin"
  branch                = "main"
  space_id              = spacelift_space.databricks.id
  autodeploy            = false
  protect_from_deletion = true
}

# its power: Space Admin on one Space
resource "spacelift_role_attachment" "admin" {
  stack_id = spacelift_stack.admin.id
  role_id  = var.space_admin_role_id
  space_id = spacelift_space.databricks.id
}"""

lesson(MODULE, 'admin_stack',
    title='The stack that builds the stacks',
    checked='2026-11-26',
    sources=[source('Assigning roles to stacks', 'https://docs.spacelift.io/concepts/authorization/assigning-roles-stacks'), source('Spaces', 'https://docs.spacelift.io/concepts/spaces'), source('Creating a stack: delete a stack', 'https://docs.spacelift.io/concepts/stack/creating-a-stack'), source('Stack dependencies', 'https://docs.spacelift.io/concepts/stack/stack-dependencies')],
    learn=[
        "Stacks, contexts and policies can be Terraform code too, run by a stack of their own: a **management stack**, often called the **admin stack**. One common way to run it: it reads a config file for each environment, like `dev.yml` and `prod.yml`, and creates that environment's stacks, their settings and their dependencies.",
        "Its power comes from a **role**: a named set of things it is allowed to do. Give the admin stack the **Space Admin** role on a Space, and it can create and change stacks and contexts in that Space and the Spaces below it. The Space at the top of the tree is **root**; a role there reaches every Space, so only a stack that lives in root may have one. The old **Administrative** switch on a stack does nothing any more: in June 2026 Spacelift moved every such stack to a Space Admin role instead.",
        "The first one is made by hand. Spacelift's own advice is to create one management stack yourself, give it the Space Admin role, and let it define the rest. To keep that first stack in code as well, you adopt it, and the role you gave it, with `terraform import`, so the next apply doesn't make a second one.",
        "When the admin stack makes its stacks with `for_each` over the environment files, removing a file means its next run plans to delete that environment's stacks. Deleting a stack is not the same as removing what it built: in the web app you choose to keep or delete the resources, and in code you add a **stack destructor** (the `spacelift_stack_destructor` resource), which destroys them before the stack goes. Otherwise they can keep running, and costing money, with no stack looking after them.",
    ],
    example=example('One file per environment', """config/environments/
  dev.yml
  prod.yml

admin stack (Space Admin on databricks)
  makes dev-foundation, dev-service
  makes prod-foundation, prod-service"""),
    check=question(
        'Which gives a stack the power to create other stacks today?',
        [
            'A Space Admin role attachment',
            'The Administrative switch',
            'A label called admin',
        ],
        answer=0,
        why='Spacelift replaced the Administrative switch with role attachments, and the switch now does nothing. Labels attach contexts and policies; they give no power.',
    ),
    angle=angle(
        pattern='Wanted minus existing, both ways',
        text='The big idea: the admin stack makes the stacks the config asks for and deletes the ones it no longer asks for. Your code works out both lists: every environment with every layer gives a wanted name, like dev-foundation. Wanted names that don\'t exist yet are to create; existing names nobody wants any more are to delete. It is like a seating plan: new guests get a chair, and the chairs of guests who left are taken away, but anything they left on them stays behind unless you clear it first.',
        say='"The admin stack builds the other stacks from one [[file|branch|ticket::dev.yml, prod.yml and so on.]] per environment. Its power comes from a [[Space Admin role|label|context::The role attachment that replaced the old switch.]]. Before an environment\'s file goes, I [[destroy|rename|lock::Remove what its stacks built.]] what its stacks built."',
        classic=None,
    ),
    stack=stack('Terraform: the admin stack and its role', ADMIN_HCL),
    exercise=exercise(
        title='Which Stacks Come and Go?',
        topic='spacelift',
        difficulty='easy',
        fn='stacks_to_change',
        prompt="""Your function gets:

- `envs`: the environments that have a config file, like `["dev", "prod"]`.
- `layers`: the layers each environment gets, like `["foundation", "service"]`.
- `existing`: the stacks that exist now, like `["dev-foundation", "dev-service"]`.

Every environment and layer gives a wanted stack named `"<env>-<layer>"`.

Return a dict with two lists:

- `"create"`: wanted stacks that don't exist yet, in order of `envs`, then `layers`.
- `"delete"`: existing stacks that aren't wanted any more, in the order of `existing`.""",
        pattern='Build the wanted names, then compare them with what exists, both ways.',
        target='one pass to build, one pass each way to compare',
        realworld='This is what the admin stack\'s plan shows when someone adds or removes an environment\'s file. The delete list is the one to stop and read: those stacks go, and what they built may stay behind with nobody looking after it.',
        practice=practice(
            intro='A team manages its Spacelift stacks from one admin stack. Read what a change to its config will do.',
            explain='The admin stack makes the stacks the config asks for and deletes the rest. You destroyed what a stack built before its file went, found the Space a role didn\'t reach, saw a config change wait for the admin stack to run, and kept powers that reach every Space for stacks in the root.',
            pattern='Read the delete list first',
            realworld='Before you merge a change to the admin stack\'s config, you read its plan for stacks to delete, and you destroy what they built first. When the admin stack can\'t make a stack, you check its role attachments before anything else.',
            asks=[
                ask('Someone removed test.yml. The plan deletes two stacks. What must happen first?', ['Destroy what those stacks built', 'Nothing: their resources go too', 'Lock both stacks so they stay'], answer=0,
                    evidence=evidence('plan', title='Admin stack · proposed',
                        summary=[['0', 'to add', 'a'], ['0', 'to change', ''], ['2', 'to destroy', 'd']],
                        changes=[
                            {'sym': '-', 'address': 'spacelift_stack.env["test-foundation"]', 'note': 'destroy'},
                            {'sym': '-', 'address': 'spacelift_stack.env["test-service"]', 'note': 'destroy'},
                        ]),
                    clue='Does deleting a stack remove the workspace and storage it made?',
                    why='Deleting a stack is not the same as removing what it built. Run a destroy on each stack first (service before foundation), or the workspace and storage can stay, costing money, with no stack to manage them.',
                    wrong=[None, 'Not unless something destroys them first.', 'Locking stops runs; the plan would still delete the stacks.']),
                ask('The admin stack\'s run fails: it can\'t create a stack in the platform Space. Why?', ['It has no role on that Space', 'The config file has a typo in it', 'Stacks can only be made by hand'], answer=0,
                    evidence=evidence('code', title='The admin stack\'s role attachments', text="""Space Admin on: sales
  (and the Spaces below sales)

wants to create in: platform
  (a sibling of sales)"""),
                    clue='Where does a Space Admin role reach?',
                    why='A role works in its Space and the Spaces below it. platform is beside sales, not below it, so the admin stack needs its own role attachment there.',
                    wrong=[None, 'The run got as far as creating; it was refused for lack of rights.', 'An admin stack exists precisely to make stacks in code.']),
                ask('You merged a new setting into dev.yml an hour ago. The dev stacks still use the old value. What hasn\'t happened yet?', ['The admin stack\'s run hasn\'t applied', 'Spacelift hasn\'t cached it', 'Terraform needs init -upgrade'], answer=0,
                    alone=True,
                    clue='Who turns dev.yml into the stacks\' settings, and when?',
                    why='Only the admin stack turns dev.yml into the stacks\' settings, and only when it runs. Until its run applies, the dev stacks keep their old values.',
                    wrong=[None, 'There is no cache: the settings come from the admin stack.', 'init -upgrade changes providers, not stack settings.']),
                ask('Can the admin stack, which lives in the databricks Space, be given Space Admin on the root Space?', ['No: only a stack in root can', 'Yes, once it has a label', 'Yes, if autodeploy is off'], answer=0,
                    alone=True,
                    clue='What would a role on root reach?',
                    why='A role on root reaches every Space in the account, so Spacelift only allows it for a stack that lives in root itself.',
                    wrong=[None, 'Labels attach contexts and policies; they give no rights.', 'Autodeploy decides when runs apply, not what a stack may touch.']),
            ],
        ),
        starter="""def stacks_to_change(envs, layers, existing):
    # your code here
    pass
""",
        solution="""def stacks_to_change(envs, layers, existing):
    wanted = []
    for env in envs:
        for layer in layers:
            wanted.append(env + "-" + layer)
    create = [name for name in wanted if name not in existing]
    delete = [name for name in existing if name not in wanted]
    return {"create": create, "delete": delete}
""",
        cases=[
            case(['dev', 'prod'], ['foundation', 'service'], ['dev-foundation', 'dev-service'], expected={'create': ['prod-foundation', 'prod-service'], 'delete': []}, sample=True),
            case(['dev'], ['foundation', 'service'], ['dev-foundation', 'dev-service', 'test-foundation', 'test-service'], expected={'create': [], 'delete': ['test-foundation', 'test-service']}),
            case([], ['foundation'], ['dev-foundation'], expected={'create': [], 'delete': ['dev-foundation']}),
            case(['dev'], ['foundation', 'service'], [], expected={'create': ['dev-foundation', 'dev-service'], 'delete': []}),
            case(['dev'], ['foundation'], ['dev-foundation'], expected={'create': [], 'delete': []}),
        ],
        guided="""def stacks_to_change(envs, layers, existing):
    # Replace every ___ with real code, then run the tests.
    wanted = []
    for env in envs:
        for layer in layers:
            wanted.append(___)
    create = [name for name in wanted if name not in existing]
    delete = [name for name in existing if ___]
    return {"create": create, "delete": delete}
""",
        fills=['env + "-" + layer', 'name not in wanted'],
        concepts=[
            [
                'A loop inside a loop',
                'The inner loop runs in full for each item of the outer one, so every environment gets every layer.',
                """for env in ["dev", "prod"]:
    for layer in ["a", "b"]:
        print(env + "-" + layer)""",
            ],
            [
                'Keeping some items',
                '`[x for x in items if test]` makes a new list of the items that pass the test.',
                """[n for n in ["a", "b"] if n != "a"]   # ['b']""",
            ],
        ],
        byhand='The sample: dev and prod with two layers each want dev-foundation, dev-service, prod-foundation and prod-service. The first two exist, so create the prod ones. Both existing stacks are wanted, so delete nothing.',
        why='One pass to build the names, one pass each way to compare.',
        gotchas=[
            [
                'Drop the old switch',
                'If code still sets `administrative = true`, remove it and import the role attachment Spacelift made for you in June 2026, or every plan shows a difference.',
            ],
            [
                'Protect the admin stack',
                '`protect_from_deletion = true` makes any attempt to delete the stack fail. The stack that manages every other stack is the last one you want deleted by a typo.',
            ],
        ],
    ),
)
