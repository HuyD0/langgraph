"""Troubleshooting a run: when a Spacelift run fails, find the first real error, follow it back to the
YAML, the runbook or a lookup, ask AI for help without handing over secrets, and send the platform
owner what they need. All names are invented."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, fix, lesson, module, practice, question, stack, source

MODULE = module('troubleshooting', 'Troubleshooting a run',
                'When a run fails: find the first error, trace it back, and ask for help well.',
                setting=PLATFORM_SETTING)


lesson(MODULE, 'lookup_failed',
    title="Why can't the plan find the service principal?",
    checked='2026-11-01',
    sources=[source('Service principals', 'https://learn.microsoft.com/azure/databricks/admin/users-groups/service-principals'), source('Query infrastructure data (data sources)', 'https://developer.hashicorp.com/terraform/language/data-sources'), source('Proposed run (preview)', 'https://docs.spacelift.io/concepts/run/proposed'), source('databricks_service_principal data source', 'https://registry.terraform.io/providers/databricks/databricks/latest/docs/data-sources/service_principal')],
    learn=[
        "A **service principal** (SP) is an identity for a program, not a person: a job or a connector uses it to reach data. A common failed plan says `cannot find SP with name sp-sales-etl-uat`. The word **data** in the error path means Terraform tried to **look up** something that should already exist; it was never going to create it.",
        "An SP has to pass several **stages**, in order, before a lookup works. It must exist in **Microsoft Entra ID**. It must be **declared** in the team's `service_principals.yml`. The **Foundation** stack must have been **applied**, which registers it in the Databricks account. Then the **Service** stack assigns it to the workspace.",
        "Each stage is separate: one being done says nothing about the next. A name in YAML is not proof the SP exists. A green **proposed** run in Spacelift is a preview, not an apply. And an SP named only in a connector's permissions, not in `service_principals.yml`, is never picked up by Foundation.",
        "So you check the stages **in order** and stop at the first one that isn't true. Before anything else, make sure you are reading the config at the **same commit** the failed run used: the repo may have changed since.",
    ],
    example=example('Stopping at the first missing stage', """cannot find SP with name sp-sales-etl-uat
  module.dbx_credentials.data.databricks_service_principal.by_name

same commit as the run?          yes
exists in Entra ID?              yes
declared in service_principals?  no: only in dbx_access_connector.yml
                                 -> stop here: declare it, Foundation never saw it"""),
    check=question(
        'The Foundation stack was applied yesterday, but today\'s Service plan still can\'t find the SP. The SP was declared this morning. What does that tell you?',
        [
            'Foundation applied before the declaration: apply again',
            'The Service stack is reading an old copy of the YAML',
            'The SP was never created in Microsoft Entra ID',
        ],
        answer=0,
        why='Yesterday\'s apply ran on YAML that didn\'t declare the SP yet, so Foundation never registered it. Each stage is separate: declared this morning means Foundation has to apply again before Service can find it.',
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
        realworld="This is the order a platform team works through a \"cannot find SP\" plan failure on Azure Databricks. The answer also tells you who to ask: the identity team for Entra ID, the product team for the YAML, the platform owner for a Foundation apply.",
        practice=practice(
            intro='Work through a "cannot find SP" failure stage by stage, and stop at the first gap.',
            explain='A lookup fails when an earlier stage isn\'t done. You checked the stages in the order they must happen: the run\'s commit, Entra ID, declared in YAML, Foundation applied, assigned by Service, and stopped at the first one that wasn\'t true.',
            pattern='Follow the trail until it goes cold',
            realworld='When a Spacelift plan fails with "cannot find SP with name ...", you\'ll walk these stages before you ask anyone. Where the trail stops tells you who to ask: the identity team for Entra ID, the product team for the YAML, the platform owner for a Foundation apply.',
            asks=[
                ask('What does `data.databricks_service_principal` in the error tell you?', ['Terraform tried to create the SP and failed', 'Terraform looked up an SP that should exist', 'Someone deleted the SP since the last run'], answer=1,
                    evidence=evidence('code', title='The first error in the planning log', text="""Error: cannot find SP with name sp-sales-etl-uat
  with module.dbx_credentials[0]
    .data.databricks_service_principal.by_name["sp-sales-etl-uat"]"""),
                    clue='In Terraform, `data` means read, not make.',
                    why='A data source only reads. The SP had to exist and be registered before this plan could find it.',
                    wrong=['A create would be a `resource`, not `data`.', None, 'Nothing here says it was deleted, only that it wasn\'t found.']),
                ask('The SP is named only in the connector\'s permissions. Where does the trail stop?', ['Declared: Foundation never sees it', 'Foundation applied: it skipped the SP', 'Entra ID: the SP doesn\'t exist there'], answer=0,
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
                ask('Now the SP is declared in service_principals.yml, and Foundation shows a finished proposed run. The Service plan still fails. What next?', ['Ask for evidence that Foundation was applied', 'Re-run the Service plan until it passes', 'Recreate the SP in Entra ID'], answer=0,
                    evidence=evidence('chain', stops=[
                        {'label': 'Same commit as the run', 'state': 'ok', 'tag': 'YES'},
                        {'label': 'Exists in Entra ID', 'state': 'ok', 'tag': 'YES'},
                        {'label': 'Declared in service_principals.yml', 'state': 'ok', 'tag': 'YES'},
                        {'label': 'Foundation applied', 'sub': 'a finished proposed run', 'state': 'now', 'tag': '?'},
                        {'label': 'Assigned by Service', 'state': 'later'},
                    ]),
                    clue='A proposed run is a preview.',
                    why='Finished and proposed only means planning worked. Ask the platform owner for the applied run, or the account showing the SP.',
                    wrong=[None, 'Re-running changes nothing if the earlier stage isn\'t done, and hides the cause.', 'Never change identities to make an error go away.']),
                fix('Declare the service principal so Foundation picks it up.',
                    file='config/UAT/team-sales/service_principals.yml',
                    start="""service_principals:
  - name: sp-sales-reporting-uat
    workspace_access: true
""",
                    answer="""service_principals:
  - name: sp-sales-reporting-uat
    workspace_access: true
  - name: sp-sales-etl-uat
    workspace_access: true
""",
                    rules={'path': 'service_principals', 'required': ['name'], 'allowed': ['name', 'workspace_access'], 'types': {'name': 'str'}},
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

lesson(MODULE, 'error_kinds',
    title='What kind of no is this?',
    checked='2026-11-26',
    sources=[source('Databricks REST API: error codes', 'https://docs.databricks.com/api/workspace/errors'), source('Azure Storage: common REST API error codes', 'https://learn.microsoft.com/rest/api/storageservices/common-rest-api-error-codes'), source('Microsoft Entra: authentication and authorization error codes', 'https://learn.microsoft.com/entra/identity-platform/reference-error-codes'), source('terraform apply', 'https://developer.hashicorp.com/terraform/cli/commands/apply')],
    learn=[
        "When a run fails, read it in four steps. Which **phase** failed: initializing, planning or applying? What is the **first error**, not the last line? What **kind** of error is it? Then name two suspects before you change anything.",
        "Most errors are one of five kinds of no. **Not signed in** (HTTP 401, `UNAUTHENTICATED`, or a Microsoft Entra error starting `AADSTS`): the identity itself didn't get in, so look at its secret or its sign-in setup. **Not allowed** (403, `PERMISSION_DENIED`): it got in, but it lacks a right on that thing. **Not found** (404, `NOT_FOUND`): what it points at isn't there, or it can't see it.",
        "**Already exists** (409, `ALREADY_EXISTS`, or azurerm's \"already exists - to be managed via Terraform\"): something with that name is there, but not in state. If it's yours, import it. If the name belongs to someone else, pick another. And **a value that never arrived**, like `No value for required variable`: the problem is in the config, not the cloud.",
        "Read the error's **name**, not only its number. Azure Storage reports a bad signature, `AuthenticationFailed`, as a 403, but it's a sign-in problem, not a missing right.",
    ],
    example=example('Four steps through one failed run', """phase: applying
first error:
  PERMISSION_DENIED:
  no CREATE CATALOG
  on the metastore
kind: not allowed (403):
  signed in, missing a right
suspects:
  1. the pipeline isn't
     an admin yet
  2. the grant went to
     another group"""),
    check=question(
        'A run fails at initializing with `AADSTS7000215: Invalid client secret provided`. Which kind of no is it?',
        [
            'Not signed in',
            'Not allowed',
            'Already exists',
        ],
        answer=0,
        why='An AADSTS code is a Microsoft Entra sign-in error: the identity never got in. Check its secret before you look at any rights.',
    ),
    angle=angle(
        pattern='Name it before you number it',
        text='The big idea: most failed runs are one of a few kinds of no, and the kind tells you where to look. Your code reads the error in lower case and checks the kinds in a fixed order, sign-in first, because a sign-in failure can also carry a 403. The first kind whose words appear wins; if none do, it says it doesn\'t know. It is like a doctor asking where it hurts before reaching for a cure.',
        say='"I find the [[first|last|longest::The one that set the rest off.]] error, then name its kind. A 401 or an AADSTS code means the identity isn\'t [[signed in|allowed|found::It never got through the door.]]; a 403 means it got in but lacks a right. Then I name two suspects before I change anything."',
        classic=None,
    ),
    stack=stack('Databricks error codes and their HTTP numbers', """UNAUTHENTICATED     401
PERMISSION_DENIED   403
NOT_FOUND           404
ALREADY_EXISTS      409"""),
    exercise=exercise(
        title='Name the Kind of No',
        topic='iac-review',
        difficulty='easy',
        fn='kind_of_no',
        prompt="""Your function gets `error`, the first error line from a failed run.

Compare in lower case, and check the kinds in this order. Return the first kind with any of its words in the error:

- `"not signed in"`: `"aadsts"`, `"unauthenticated"`, `"authenticationfailed"`, `"401"`
- `"not allowed"`: `"permission_denied"`, `"forbidden"`, `"403"`
- `"already exists"`: `"already exists"`, `"already_exists"`, `"409"`
- `"not found"`: `"not_found"`, `"not found"`, `"does not exist"`, `"404"`
- `"missing value"`: `"no value for required variable"`

If none match, return `"unknown"`.""",
        pattern='Check the kinds in a fixed order and return the first one whose words appear.',
        target='one pass over a short list of words',
        realworld="Sorting the error first tells you who to ask: a sign-in problem goes to whoever owns the identity's secret or sign-in setup, a missing right to whoever grants it, an already-exists to whoever made the thing by hand. Sign-in is checked first because Azure Storage reports AuthenticationFailed with a 403.",
        practice=practice(
            intro='A run is red. Read it the way the platform team does: phase, first error, kind, then two suspects.',
            explain='Most failed runs are one of a few kinds of no. You started at the first error, read a 403 by its name and found a sign-in problem, imported something that was yours instead of deleting it, and named the missing right instead of handing out admin.',
            pattern='First error, then its kind',
            realworld='When a Spacelift run fails, you open the log, find the phase and the first Error line, and say which kind of no it is before you suggest a fix. Your note to the platform owner names the kind and your two suspects.',
            asks=[
                ask('Which line do you read first?', ['The first Error line', 'The last line of the log', 'The longest Error line'], answer=0,
                    evidence=evidence('code', title='The run log, applying phase', text="""databricks_catalog.sales: Creating...
Error: cannot create catalog:
  PERMISSION_DENIED: no CREATE CATALOG
Error: cannot create schema raw:
  NOT_FOUND: catalog sales
Error: cannot create grants:
  NOT_FOUND: schema sales.raw"""),
                    clue='Did the later errors happen on their own, or because of an earlier one?',
                    why='The catalog failed, so the schema and the grants had nothing to go in. Fix the first error and the others usually go with it.',
                    wrong=[None, 'The last lines are the knock-on effects of the first failure.', 'Length says nothing about which one set the rest off.']),
                ask('Which kind of no is this?', ['Not signed in', 'Not allowed', 'Not found'], answer=0,
                    evidence=evidence('code', title='First error', text="""Error: retrieving Storage Account
  "stsalesdev": Status=403
  Code="AuthenticationFailed"
  Server failed to authenticate
  the request."""),
                    clue='Read the code name, not only the number.',
                    why='AuthenticationFailed means the request didn\'t sign in properly, even though Azure Storage sends it as a 403. Look at the key or the sign-in setup, not at the account\'s rights.',
                    wrong=[None, 'The number says 403, but the name says the sign-in itself failed.', 'The account was found: it refused the sign-in.']),
                ask('The storage account was made by hand last week, and it\'s the one the code means. What do you do?', ['Import it into state', 'Delete it, then apply again', 'Rename it in the code'], answer=0,
                    evidence=evidence('code', title='First error', text="""Error: A resource with the ID
  ".../storageAccounts/stsalesdev"
  already exists - to be managed via
  Terraform this resource needs to be
  imported into the State."""),
                    clue='Is the thing in Azure the right one, just unknown to Terraform?',
                    why='It\'s the right account; Terraform just doesn\'t know it. Import it so state knows it, and the next plan should show no create. Deleting it would throw away whatever is in it.',
                    wrong=[None, 'Deleting a storage account deletes its data too.', 'Renaming would make a second account and leave this one unmanaged.']),
                ask('A teammate says: "It\'s a 403, just make the pipeline an account admin." What do you do first?', ['Name the right it lacks, and who grants it', 'Make it admin now, take it back later', 'Rerun the stack to see if it passes'], answer=0,
                    evidence=evidence('code', title='First error', text="""Error: cannot create catalog:
  PERMISSION_DENIED: no CREATE CATALOG
  on the metastore"""),
                    clue='The error names one missing right. Who gives that right?',
                    why='The error says exactly what is missing: CREATE CATALOG on the metastore. Ask whoever grants it for that one right. Admin for everything would hide the gap and give far more than the run needs.',
                    wrong=[None, '"Later" rarely comes, and admin gives far more than one missing right.', 'A rerun finds the same missing right.']),
            ],
        ),
        starter="""def kind_of_no(error):
    # your code here
    pass
""",
        solution="""KINDS = [
    (["aadsts", "unauthenticated", "authenticationfailed", "401"], "not signed in"),
    (["permission_denied", "forbidden", "403"], "not allowed"),
    (["already exists", "already_exists", "409"], "already exists"),
    (["not_found", "not found", "does not exist", "404"], "not found"),
    (["no value for required variable"], "missing value"),
]

def kind_of_no(error):
    text = error.lower()
    for words, kind in KINDS:
        for word in words:
            if word in text:
                return kind
    return "unknown"
""",
        cases=[
            case('Error: AADSTS7000215: Invalid client secret provided.', expected='not signed in', sample=True),
            case('Error: cannot create catalog: PERMISSION_DENIED: no CREATE CATALOG on the metastore', expected='not allowed'),
            case('Error: retrieving Storage Account: Status=403 Code="AuthenticationFailed"', expected='not signed in'),
            case('Error: Status=403 Code="AuthorizationFailed"', expected='not allowed'),
            case('Error: A resource with the ID "/subscriptions/.../stsalesdev" already exists - to be managed via Terraform this resource needs to be imported into the State.', expected='already exists'),
            case('Error: cannot read schema: NOT_FOUND: Catalog sales does not exist.', expected='not found'),
            case('Error: No value for required variable', expected='missing value'),
            case('Error: Cycle: databricks_schema.raw, databricks_grants.raw', expected='unknown'),
        ],
        guided="""KINDS = [
    (["aadsts", "unauthenticated", "authenticationfailed", "401"], "not signed in"),
    (["permission_denied", "forbidden", "403"], "not allowed"),
    (["already exists", "already_exists", "409"], "already exists"),
    (["not_found", "not found", "does not exist", "404"], "not found"),
    (["no value for required variable"], "missing value"),
]

def kind_of_no(error):
    # Replace every ___ with real code, then run the tests.
    text = ___
    for words, kind in KINDS:
        for word in words:
            if ___:
                return kind
    return "unknown"
""",
        fills=['error.lower()', 'word in text'],
        concepts=[
            [
                'A list of pairs',
                'Each item can hold two things in round brackets, and the loop can name both.',
                """for words, kind in [(["a"], "first"), (["b"], "second")]:
    print(kind)""",
            ],
            [
                'Order decides',
                'When two kinds could match, the one checked first wins. That is why sign-in comes before the 403 check.',
                """text = 'status=403 code="authenticationfailed"'
"authenticationfailed" in text   # True: checked first""",
            ],
        ],
        byhand='The sample in lower case has "aadsts" in it, and that is one of the words for the first kind, so return "not signed in" straight away. No later kind is checked.',
        why='At most one look at each word, in order.',
        gotchas=[
            [
                'The name beats the number',
                'A 403 can be a sign-in failure (AuthenticationFailed) or a missing right (AuthorizationFailed, PERMISSION_DENIED). Read the code name before you decide.',
            ],
            [
                'Import yours, rename theirs',
                'For "already exists", ask whose it is first. Yours: import it. Someone else\'s, or a name all of Azure shares like a storage account: pick another name.',
            ],
        ],
    ),
)

lesson(MODULE, 'partial_apply',
    title='The apply failed halfway: what is real now?',
    checked='2026-11-26',
    sources=[source('terraform apply', 'https://developer.hashicorp.com/terraform/cli/commands/apply'), source('Environment variables: TF_STATE_PERSIST_INTERVAL', 'https://developer.hashicorp.com/terraform/cli/config/environment-variables'), source('Import existing resources', 'https://developer.hashicorp.com/terraform/language/import')],
    learn=[
        "Terraform doesn't roll back a failed apply. Whatever it made before the error is real, and it writes those into state. So after **10 created, 1 failed, 4 not tried**, Azure has 10 new things, and so does state.",
        "Fix the cause, then plan again. The plan should add about **the 5 left**: the one that failed and the 4 it never got to. That number is your check that state and reality still agree.",
        "If the run itself was **killed**, not just one resource failing, Terraform may not have saved its last few creates to state. Then the next apply says **already exists** for them. They're yours: import them, don't delete them.",
        "A plan that wants to add **everything** again, 15 to add, means Terraform is reading the wrong state, or none. Stop. Applying would hit \"already exists\" on every one, or make copies.",
    ],
    example=example('What the next plan should say', """apply: 10 created, 1 failed,
       4 not tried
fix it, then plan again:

Plan: 5 to add
  the 5 left: go on
Plan: 7 to add
  2 made, not saved:
  look closer, import them
Plan: 15 to add
  wrong state, or none: stop"""),
    check=question(
        'An apply created 10 things, failed on 1 and never tried 4. You fixed the failure. What should the next plan show?',
        [
            'About 5 to add',
            '15 to add',
            '10 to destroy',
        ],
        answer=0,
        why='The 10 it made are real and in state, so the plan only adds what is left: the one that failed and the 4 it never tried.',
    ),
    angle=angle(
        pattern='Count what should be left',
        text='The big idea: a failed apply leaves real things behind and records them, so the next plan should add only what is left. Your code compares the plan\'s count with what you expect. Exactly the leftovers means go on. Everything again, when something was made, means stop: it is reading the wrong state. Anything else means look closer before you apply. It is like a half-unpacked delivery: you count what is still in the box before you order more.',
        say='"Terraform doesn\'t [[roll back|retry|skip::Undo what it already made.]] a failed apply, so what it made is real. After a fix, the plan should add only the [[leftovers|whole stack|failed one::The one that failed plus the ones it never tried.]]. If it wants to add everything, I stop."',
        classic=None,
    ),
    stack=stack('The apply log, cut short', """databricks_catalog.sales: Creation complete
databricks_schema.raw: Creation complete
...
databricks_storage_credential.uc: Creating...
Error: cannot create storage credential:
  PERMISSION_DENIED

# no rollback: the 10 "Creation complete"
# above are real, and saved in state"""),
    exercise=exercise(
        title='Is the Next Plan Right?',
        topic='iac-review',
        difficulty='easy',
        fn='after_failure',
        prompt="""Your function gets four numbers from a failed apply and the plan you made after fixing it:

- `created`: how many things the apply made before it stopped.
- `failed`: how many failed.
- `not_tried`: how many it never got to.
- `plan_add`: how many the new plan wants to add.

Return, checking in this order:

- `"go on"` if `plan_add` equals `failed + not_tried`
- `"stop"` if `created` is more than 0 and `plan_add` is at least `created + failed + not_tried`
- `"look closer"` otherwise""",
        pattern='Work out what should be left, compare, then check for the everything-again case.',
        target='a couple of sums and checks',
        realworld='After a partial apply you plan again before anything else. The add count tells you whether state matches what Azure has: the leftovers mean go on, more than that means some creates weren\'t saved (import them), and everything again means the stack is reading the wrong state.',
        practice=practice(
            intro='An apply stopped halfway. Work out what is real now before anyone applies again.',
            explain='A failed apply leaves real things behind and records them in state. You saw what exists after the error, used the next plan\'s count to check state, stopped when it wanted everything again, and imported what a killed run made but never saved.',
            pattern='No rollback: check the count first',
            realworld='When a run fails during apply, you fix the cause and plan again, and you read the add count before you confirm anything. If it\'s more than you expect, you find out why first.',
            asks=[
                ask('The apply stopped with this. What exists in Azure now?', ['Everything marked Creation complete', 'Nothing: Terraform rolled it back', 'Everything that was in the plan'], answer=0,
                    evidence=evidence('code', title='The end of the apply log', text="""azurerm_storage_account.lake: Creation complete
azurerm_databricks_access_connector.uc:
  Creation complete
databricks_storage_credential.uc: Creating...
Error: cannot create storage credential:
  PERMISSION_DENIED"""),
                    clue='Does Terraform undo what it already made when something fails?',
                    why='Terraform doesn\'t roll back. The storage account and the connector were made and saved in state; only the credential, and what came after it, is missing.',
                    wrong=[None, 'There is no rollback: what finished stays.', 'The ones after the error were never tried.']),
                ask('After the fix, the plan says this. What do you do?', ['Stop: it is reading the wrong state', 'Apply: it makes what is missing', 'Delete the 10, then apply again'], answer=0,
                    evidence=evidence('plan', title='Stack sales-foundation-dev · after the fix',
                        summary=[['15', 'to add', 'a'], ['0', 'to change', ''], ['0', 'to destroy', 'd']],
                        changes=[
                            {'sym': '+', 'address': 'azurerm_storage_account.lake', 'note': 'create'},
                            {'sym': '+', 'address': 'azurerm_databricks_access_connector.uc', 'note': 'create'},
                        ]),
                    clue='The last apply made 10 things. Why would the plan want to make them again?',
                    why='It wants to make everything, including the 10 that exist, so it isn\'t reading the state that recorded them. Stop and find out which state the stack is using before anyone applies.',
                    wrong=[None, 'It would try to make 10 things that already exist.', 'Deleting real resources to suit the wrong state loses data.']),
                ask('The last run was killed while it was creating the catalog. Now the apply says the catalog already exists. What do you do?', ['Import it into state', 'Delete it in the workspace', 'Rename the catalog'], answer=0,
                    alone=True,
                    clue='Who made that catalog?',
                    why='The killed run made it but didn\'t get to save it in state. It\'s yours: import it so state knows it, then plan again.',
                    wrong=[None, 'It\'s the right catalog: deleting it throws away what is in it.', 'A new name would leave this one behind, unmanaged.']),
            ],
        ),
        starter="""def after_failure(created, failed, not_tried, plan_add):
    # your code here
    pass
""",
        solution="""def after_failure(created, failed, not_tried, plan_add):
    left = failed + not_tried
    if plan_add == left:
        return "go on"
    if created > 0 and plan_add >= created + left:
        return "stop"
    return "look closer"
""",
        cases=[
            case(10, 1, 4, 5, expected='go on', sample=True),
            case(10, 1, 4, 15, expected='stop'),
            case(10, 1, 4, 7, expected='look closer'),
            case(10, 1, 4, 3, expected='look closer'),
            case(0, 1, 0, 1, expected='go on'),
            case(3, 0, 2, 5, expected='stop'),
            case(0, 2, 3, 5, expected='go on'),
        ],
        guided="""def after_failure(created, failed, not_tried, plan_add):
    # Replace every ___ with real code, then run the tests.
    left = failed + not_tried
    if ___:
        return "go on"
    if created > 0 and ___:
        return "stop"
    return "look closer"
""",
        fills=['plan_add == left', 'plan_add >= created + left'],
        concepts=[
            [
                'A name for a sum',
                'Store a sum under a name once, then use the name: easier to read than repeating it.',
                """left = 1 + 4
left == 5   # True""",
            ],
            [
                'Comparing numbers',
                '`==` asks "equal?", `>=` asks "at least?", `>` asks "more than?".',
                """15 >= 15   # True
0 > 0      # False""",
            ],
        ],
        byhand='The sample: 1 failed and 4 not tried, so 5 are left. The plan wants to add 5, exactly the leftovers: return "go on".',
        why='A sum and two comparisons.',
        gotchas=[
            [
                'No rollback',
                'Terraform never undoes a failed apply. Whatever finished stays, in Azure and in state, until a later apply or destroy changes it.',
            ],
            [
                'Fix the cause, not the count',
                'Don\'t delete resources or edit state to make the plan look like you expected. Find out why it differs, then fix that.',
            ],
        ],
    ),
)

lesson(MODULE, 'ai_unstuck',
    title='Getting unstuck with AI, safely',
    checked='2026-11-01',
    sources=[source('Run', 'https://docs.spacelift.io/concepts/run'), source('Create a Terraform plan', 'https://developer.hashicorp.com/terraform/tutorials/cli/plan')],
    learn=[
        "AI assistants like GitHub Copilot or an enterprise ChatGPT are good at three things here: **explaining** an unfamiliar term or error, **tracing** a name across files (YAML, then the runbook, then the module), and **suggesting checks**. They are not evidence. Anything they say is a lead until you've seen it yourself.",
        "A good prompt gives the AI what a person would need: **the run** (stack, environment, run link), **the first error** (a short excerpt, not the whole log), **the repo and the commit the run used**, and the rules: **read-only**, link every source, mark guesses as guesses, give one safe next check, and don't edit or deploy anything.",
        "Then check the answer against **three rules**. *Version*: does it read the same commit as the run, not today's main branch? *Evidence*: does each claim point at a file and line you can open, and does that line really say it? *Safety*: did you paste anything secret, and does it suggest changing something without approval?",
        "Never paste secrets, tokens, keys, state files or whole logs with credentials in them. And never let an assistant change infrastructure for you: re-running a plan, resetting state or recreating an identity to make an error go away hides the cause.",
    ],
    example=example('A prompt for an unfamiliar Spacelift failure', """I am new to Databricks IaC. Investigate READ-ONLY.
Run: dbx-service-uat, run 4182 (UAT)
First error: cannot find SP with name sp-sales-etl-uat
Config repo and commit: config-repo @ 300d269 (the run's commit)
Explain the error plainly. Trace YAML -> check -> runbook -> module -> provider.
Link each source. Mark guesses as guesses.
Give one safe next check. Do not edit or deploy."""),
    check=question(
        'The failed run used commit 300d269. The assistant says a setting is turned off and links to the file. You open the link: it shows the latest version of that file. What do you do?',
        [
            'Trust it: the link opens and the file says so',
            'Open the same file at commit 300d269 and look',
            'Re-run the plan and see if the error comes back',
        ],
        answer=1,
        why='The version rule: the evidence must come from the commit the run used, and the file may have changed since. Re-running a plan to make an error go away would break the safety rule.',
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
            pattern='Three rules: version, evidence, safety',
            realworld="When a run fails and you ask Copilot or an enterprise ChatGPT for help, you'll send the run, the first error and the commit, with secrets taken out. Then you'll open each file it points at, at that commit, before you repeat what it said or act on it.",
            asks=[
                ask('What goes in the commit line?', ['The commit the failed run used', 'Today\'s main branch', 'The Terraform state file'], answer=0,
                    evidence=evidence('prompt', title='Your prompt', text="""I am new to Databricks IaC. Investigate READ-ONLY.
Run: dbx-service-uat, run 4182 (UAT)
First error: cannot find SP with name sp-sales-etl-uat
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
Error: cannot find SP with name sp-sales-etl-uat"""),
                    clue='Look for anything that would let someone sign in.',
                    why='A client secret lets anyone act as that identity. Send only the first error, redacted.',
                    wrong=['Detail helps, but not a credential.', None, 'No assistant should get secrets, whichever one it is.']),
                ask('What\'s wrong with this answer?', ['Nothing: it names the file and the line to change', 'Wrong version, and a guess about Foundation', 'It should tell you to delete and recreate the SP'], answer=1,
                    evidence=evidence('claim', text='"The SP is declared in `service_principals.yml` on **main**, so Foundation must have registered it. **Re-run the Service plan** to fix it."'),
                    clue='Which commit did the run use? And does a declaration prove an earlier stage ran?',
                    why='It read main instead of the run\'s commit, it guessed that Foundation ran, and re-running a plan isn\'t a fix.',
                    wrong=['Naming a file isn\'t enough: check the version and whether it\'s evidence or a guess.', None, 'Deleting identities would break the safety rule.']),
                ask('Can you rely on this one?', ['Yes, once you see that line at that commit', 'Yes: it cites a file, so it\'s true', 'No: never trust an AI answer'], answer=0,
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
            [
                'Two repos, two versions',
                'If the run also copied in code from a second repo, like a runbook, find the branch or tag it took, and read that code as it was when the run started. Give the assistant both versions.',
            ],
        ],
    ),
)


lesson(MODULE, 'evidence_note',
    title='What to send the platform owner',
    checked='2026-11-26',
    sources=[source('Run', 'https://docs.spacelift.io/concepts/run'), source('Proposed run (preview)', 'https://docs.spacelift.io/concepts/run/proposed')],
    learn=[
        "When you need the platform owner, send a note they can act on without coming back to you with questions. Six lines, always in the same order.",
        "**The run**: a link to it. **The phase and the first error**, with anything secret taken out. **The commit** the run used. **The YAML and runbook lines** involved, as links at that commit. **What you ruled out**, and how you checked each one. **The decision you need**, asked as one question.",
        "Leave out the whole log, guesses that read like facts, and anything secret. A note that ends with a clear question gets a quick answer. One that ends with \"any ideas?\" gets a meeting.",
    ],
    example=example('A note the owner can act on', """Run: dbx-service-uat, run 4182
Error: planning, cannot find
  SP sp-sales-etl-uat
Commit: 300d269
Lines: service_principals.yml
  line 4, at 300d269
Ruled out: Entra ID (the SP
  exists); declared (yes)
Ask: Can you apply Foundation
  to UAT?"""),
    check=question(
        'Your note links the run and quotes the first error. What else must it have before you send it?',
        [
            'The decision you need, as a question',
            'The whole log, just in case',
            'Your best guess at the cause',
        ],
        answer=0,
        why='The owner needs to know what you want them to do. Without one clear question, the note starts a conversation instead of getting an answer.',
    ),
    angle=angle(
        pattern='Six lines, same order, one question',
        text='The big idea: a note to the platform owner is a form, not a story: the run, the first error, the commit, the lines, what you ruled out, and one question. Your code checks a draft note before it goes: it lists every line that is missing or empty, in the fixed order, and flags an ask that isn\'t a question. It is like a recipe card: if a line is missing, the cook has to come and ask you.',
        say='"My note gives the run, the [[first error|whole log|last line::Just the one that set the rest off, secrets out.]], the commit and the lines, then what I [[ruled out|guessed|tried twice::Each one with how you checked.]]. It ends with one [[question|summary|apology::The decision you need from them.]]."',
        classic=None,
    ),
    stack=stack('The same note, as a template', """Run:
Error:     phase + first error
Commit:
Lines:     links at that commit
Ruled out: each, and how
Ask:       one question"""),
    exercise=exercise(
        title='Is This Note Ready?',
        topic='iac-review',
        difficulty='easy',
        fn='note_gaps',
        prompt="""Your function gets `note`, a draft note as a dict, like `{"run": "dbx-service-uat 4182", "error": "...", "ask": "Can you apply Foundation for UAT?"}`.

It should have six lines, in this order: `"run"`, `"error"`, `"commit"`, `"lines"`, `"ruled_out"`, `"ask"`.

Return a list:

- each of the six that is missing, or only spaces, in that order
- then `"ask as a question"` if there is an `"ask"` with text in it that doesn't end with `?`

A ready note returns `[]`.""",
        pattern='Go through the six names in order, then check how the last one ends.',
        target='one pass over six names',
        realworld='Platform teams that look after many product teams ask for exactly this shape, often as an issue template: run, error, commit, lines, what you ruled out, and the ask. A note that fits it gets picked up first.',
        practice=practice(
            intro='Your investigation is done. Turn it into a note the platform owner can act on.',
            explain='A note to the platform owner is a form with six lines and one question. You swapped a whole log for the first error, kept the ruled-out lines that say how you checked, and turned "any ideas?" into a decision someone can make.',
            pattern='Six lines, one question',
            realworld='When you need the platform owner, you send the run, the first error, the commit, the lines, what you ruled out and one question, in that order. Then they can answer from their phone.',
            asks=[
                ask('What should replace the attached log?', ['The first error, secrets taken out', 'A zip of every log from the run', 'A screenshot of the last line'], answer=0,
                    evidence=evidence('code', title='Your draft', text="""Run:    dbx-service-uat, run 4182
Error:  see the log (attached, 4 MB)
Commit: 300d269"""),
                    clue='What does the owner need to read first?',
                    why='The first error tells them where it went wrong, in one line. A whole log hides it, and can hold secrets.',
                    wrong=[None, 'More logs make the one useful line harder to find.', 'The last line is usually a knock-on effect, not the cause.']),
                ask('Which ruled-out line helps the owner most?', ['Entra ID: checked, the SP is there', 'Probably not an Entra problem', 'Tried lots of things, none worked'], answer=0,
                    alone=True,
                    clue='Which one can the owner trust without checking again?',
                    why='It says what you checked and what you found, so the owner can skip it. A guess or "lots of things" makes them start from scratch.',
                    wrong=[None, 'A guess has to be checked again: say what you looked at.', 'They can\'t tell what you tried, so they will try it all again.']),
                ask('Which ask gets the quickest answer?', ['Can you apply Foundation for UAT?', 'Any ideas what this could be?', 'Can we set up a call this week?'], answer=0,
                    alone=True,
                    clue='Which one can the owner say yes or no to, straight away?',
                    why='It names one action they can take or refuse. "Any ideas?" hands the whole problem back, and a call waits for a free slot.',
                    wrong=[None, 'It gives the owner the whole problem to solve again.', 'A call might help later; first ask for the one thing you need.']),
            ],
        ),
        starter="""def note_gaps(note):
    # your code here
    pass
""",
        solution="""FIELDS = ["run", "error", "commit", "lines", "ruled_out", "ask"]

def note_gaps(note):
    gaps = []
    for field in FIELDS:
        if field not in note or note[field].strip() == "":
            gaps.append(field)
    ask = note.get("ask", "").strip()
    if ask and not ask.endswith("?"):
        gaps.append("ask as a question")
    return gaps
""",
        cases=[
            case({'run': 'dbx-service-uat 4182', 'error': 'planning: cannot find SP sp-sales-etl-uat', 'commit': '300d269', 'lines': 'service_principals.yml line 4', 'ruled_out': 'Entra ID: the SP is there', 'ask': 'Can you apply Foundation for UAT?'}, expected=[], sample=True),
            case({'run': 'dbx-service-uat 4182', 'error': 'planning: cannot find SP', 'lines': 'service_principals.yml line 4', 'ask': 'Can you apply Foundation for UAT?'}, expected=['commit', 'ruled_out']),
            case({'run': 'dbx-service-uat 4182', 'error': 'planning: cannot find SP', 'commit': '300d269', 'lines': 'line 4', 'ruled_out': 'Entra ID', 'ask': 'Please apply Foundation'}, expected=['ask as a question']),
            case({}, expected=['run', 'error', 'commit', 'lines', 'ruled_out', 'ask']),
            case({'run': 'run 4182', 'error': '   ', 'commit': '300d269', 'lines': 'line 4', 'ruled_out': 'Entra ID', 'ask': 'Any ideas?'}, expected=['error']),
        ],
        guided="""FIELDS = ["run", "error", "commit", "lines", "ruled_out", "ask"]

def note_gaps(note):
    # Replace every ___ with real code, then run the tests.
    gaps = []
    for field in FIELDS:
        if field not in note or ___:
            gaps.append(field)
    ask = note.get("ask", "").strip()
    if ask and ___:
        gaps.append("ask as a question")
    return gaps
""",
        fills=['note[field].strip() == ""', 'not ask.endswith("?")'],
        concepts=[
            [
                'strip()',
                '`text.strip()` takes spaces off both ends, so a line of only spaces becomes empty.',
                """"   ".strip() == ""   # True""",
            ],
            [
                'get() with a default',
                '`d.get(key, "")` gives the value, or `""` when the key isn\'t there, instead of an error.',
                """{"a": "x"}.get("b", "")   # ''""",
            ],
            [
                'endswith()',
                '`text.endswith("?")` is True when the text finishes with a question mark.',
                """"Can you apply it?".endswith("?")   # True""",
            ],
        ],
        byhand='The sample has all six lines, each with text in it, and the ask ends with a question mark. Nothing is missing: return [].',
        why='Six checks and one look at the ask.',
        gotchas=[
            [
                'Links at the run\'s commit',
                'Link files at the commit the run used, not at main. The owner should see exactly what the run read.',
            ],
            [
                'One decision per note',
                'If you need two things, send two notes, or ask the one that unblocks you first. A note with three questions gets one answer.',
            ],
        ],
    ),
)
