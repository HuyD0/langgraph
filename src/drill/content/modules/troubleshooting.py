"""Troubleshooting a run: when a Spacelift run fails, find the first real error, follow it back to the
YAML, the runbook or a lookup, ask AI for help without handing over secrets, and send the platform
owner what they need. All names are invented."""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import angle, ask, case, evidence, example, exercise, fix, lesson, module, planned, practice, question, stack, source

MODULE = module('troubleshooting', 'Troubleshooting a run',
                'When a run fails: find the first error, trace it back, and ask for help well.',
                setting=PLATFORM_SETTING)


lesson(MODULE, 'lookup_failed',
    title="Why can't the plan find the service principal?",
    checked='2026-10-13',
    sources=[source('Service principals', 'https://learn.microsoft.com/azure/databricks/admin/users-groups/service-principals'), source('Query infrastructure data (data sources)', 'https://developer.hashicorp.com/terraform/language/data-sources'), source('Proposed run (preview)', 'https://docs.spacelift.io/concepts/run/proposed')],
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
        realworld="This is the order a platform team works through a \"Cannot find service principal\" plan failure on Azure Databricks. The answer also tells you who to ask: the identity team for Entra ID, the product team for the YAML, the platform owner for a Foundation apply.",
        practice=practice(
            intro='Work through a "Cannot find service principal" failure stage by stage, and stop at the first gap.',
            explain='A lookup fails when an earlier stage isn\'t done. You checked the stages in the order they must happen: the run\'s commit, Entra ID, declared in YAML, Foundation applied, assigned by Service, and stopped at the first one that wasn\'t true.',
            pattern='Follow the trail until it goes cold',
            realworld='When a Spacelift plan fails with "Cannot find service principal", you\'ll walk these stages before you ask anyone. Where the trail stops tells you who to ask: the identity team for Entra ID, the product team for the YAML, the platform owner for a Foundation apply.',
            asks=[
                ask('What does `data.databricks_service_principal` in the error tell you?', ['Terraform tried to create the SP and failed', 'Terraform looked up an SP that should exist', 'Someone deleted the SP since the last run'], answer=1,
                    evidence=evidence('code', title='The first error in the planning log', text="""Error: Cannot find service principal: sp-sales-etl-uat
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
                ask('Now it\'s declared, and Foundation shows a finished proposed run. The Service plan still fails. What next?', ['Ask for evidence that Foundation was applied', 'Re-run the Service plan until it passes', 'Recreate the SP in Entra ID'], answer=0,
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

lesson(MODULE, 'ai_unstuck',
    title='Getting unstuck with AI, safely',
    checked='2026-10-13',
    sources=[source('Run', 'https://docs.spacelift.io/concepts/run'), source('Create a Terraform plan', 'https://developer.hashicorp.com/terraform/tutorials/cli/plan')],
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
        ],
    ),
)


planned(MODULE, 'evidence_note', 'What to send the platform owner', 'The stack, the run, the first error, the YAML and runbook links, and the decision you need.')
