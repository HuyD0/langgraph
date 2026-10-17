"""Spacelift: stacks, runs and the policies that guard every change."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, module, planned, practice, question, screen, stack, source

MODULE = module('spacelift', 'Spacelift', 'Stacks, runs and the policies that guard every change.', setting=PLATFORM_SETTING)


lesson(MODULE, 'read_a_run',
    title='Reading a Spacelift run',
    checked='2026-10-15',
    sources=[source('Run', 'https://docs.spacelift.io/concepts/run'), source('Proposed run (preview)', 'https://docs.spacelift.io/concepts/run/proposed'), source('Tracked run (deployment)', 'https://docs.spacelift.io/concepts/run/tracked'), source('Plan policy', 'https://docs.spacelift.io/concepts/policy/terraform-plan-policy')],
    learn=[
        "A **run** is one go of Terraform on a **stack**. A **proposed** run only previews: Spacelift starts one for a push to any branch that isn't the stack's tracked branch, plans, reports back to the pull request, and stops. A **tracked** run deploys: it plans, then applies. Most runs a reviewer sees are proposed.",
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
            note='Only an approved tracked run applies changes. A finished proposed run is still a preview.',
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
                'Each row is one resource. ~ means changed in place, + added, - destroyed, -/+ replaced. PLANNED means not applied yet.',
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
                'A deny policy fails the run in red; a warn policy prints in yellow and lets it through for a person to judge.',
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
- tracked and `"UNCONFIRMED"` -> `"waiting for approval"`
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
        return "waiting for approval"
    if kind == "tracked" and state == "FINISHED":
        return "applied"
    if kind == "tracked" and state == "DISCARDED":
        return "rejected"
    return "still running"
""",
        cases=[
            case({'type': 'proposed', 'state': 'FINISHED'}, expected='preview only', sample=True),
            case({'type': 'tracked', 'state': 'FINISHED'}, expected='applied'),
            case({'type': 'tracked', 'state': 'UNCONFIRMED'}, expected='waiting for approval'),
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
        return "waiting for approval"
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
    checked='2026-10-13',
    sources=[source('Stack', 'https://docs.spacelift.io/concepts/stack'), source('Stack dependencies', 'https://docs.spacelift.io/concepts/stack/stack-dependencies')],
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
        realworld='This is Spacelift stack dependencies: when an upstream stack applies, its dependents get tracked runs in this order, and an upstream stack can pass its outputs (like subnet ids) down as the next stack\'s inputs. A circular dependency is refused when you set it up, so the order always exists.',
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
    checked='2026-10-13',
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
                    clue='Spacelift plan policies can do more than block.',
                    why='A warn rule prints in yellow and lets the run through, so you see what it would have stopped before it stops anyone. Then switch it to deny.',
                    wrong=['A rule nobody has seen in action can block real work on day one.', None, 'Prod is where a lost catalog hurts most. Dev is a place to try it, not to leave it.']),
                ask('An AI assistant suggests this. What would the command really do?', ['Delete the storage account in Azure, data and all', 'Terraform forgets the account; Azure keeps it', 'Nothing: the policy blocks the command too'], answer=1,
                    evidence=evidence('claim', text='The policy is blocking you? Run `terraform state rm azurerm_storage_account.lake`, and the plan won\'t show a delete any more.'),
                    clue='State commands change what Terraform keeps track of, without making a plan.',
                    why='`state rm` deletes nothing in Azure, but Terraform stops tracking the account, so no plan, and no policy, sees it again. Ask why the plan wants a delete instead.',
                    wrong=['`state rm` never touches Azure. It only edits Terraform\'s record.', None, 'Policies only see plans, and state commands make no plan.']),
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
                'Spacelift plan policies support `warn` as well as `deny`. Rolling a new rule out as a warning shows you what it would have blocked before it blocks anyone.',
            ],
        ],
    ),
)

lesson(MODULE, 'plan_policy',
    title='Policy as code',
    checked='2026-10-13',
    sources=[source('Policy', 'https://docs.spacelift.io/concepts/policy'), source('Plan policy', 'https://docs.spacelift.io/concepts/policy/terraform-plan-policy'), source('Policy language (Rego)', 'https://www.openpolicyagent.org/docs/policy-language')],
    learn=[
        "Last lesson you wrote one rule. **Policy as code** is a list of such rules that runs on every plan, as a Spacelift plan policy or a `terraform test`, so a review rule that lives in people's heads can't get skipped on a busy day. Add a second rule: never open workspaces or storage to the public internet. Each rule checks every change on its own, so one change can break two rules.",
        'A Spacelift plan policy can **deny** (block the run, in red) or **warn** (print in yellow and let it through). Roll a new rule out as a warning first, so you see what it would have blocked before it blocks anyone.',
    ],
    example=example('Two rules', 'rule 1: protected type + delete  → "... would be destroyed"\nrule 2: public access on         → "... allows public network access"'),
    check=question(
        'Why roll out a new policy as a warning first?',
        ['So the run still applies while the rule is tested', 'To see what it would block before it blocks anyone', 'Because a deny rule needs an admin to approve it'],
        answer=1,
        why='A warning shows you every plan the rule would have stopped, mistakes in the rule included, without stopping anyone. Once it flags only real problems, switch it to deny.',
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
                'Roll a new rule out as a warning, see what it would have blocked, then make it a deny.',
            ],
            [
                'Test the policy too',
                'Policies are code: keep sample plans that should pass and fail, and check them in CI.',
            ],
        ],
    ),
)

planned(MODULE, 'drift_detection', 'Drift detection', 'Finding changes made outside Terraform before they surprise the next apply.')
planned(MODULE, 'contexts_secrets', 'Contexts and secrets', 'Sharing settings and credentials between stacks without copying them.')
planned(MODULE, 'policy_testing', 'Testing a policy before it blocks', 'Rolling out a new rule as a warning, and testing it against real plans.')
