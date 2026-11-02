"""Run the gateway: how a change reaches production, how to stop a runaway agent fast, how to prove the workspace
still matches the code, and one request followed through every layer. Follows Guardrails and records in the
Platform track, same shape: a message from a product team, one idea with one picture, practice on that same
situation. Facts are from Microsoft Learn's Unity Gateway, agent server, audit log and MLOps pages for Azure
Databricks, and GitHub's page on deployment environments, checked 2026-11-01. Where the docs don't confirm a
detail yet (a rate limit of 0, how queued runs are cancelled), the lesson says so.
"""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import (angle, ask, card, case, evidence, example, exercise, lesson, module, pile, piles,
                                 practice, question, sortby, sortrow, source, steps, terms)

MODULE = module('gateway-operations', 'Run the gateway',
                'How a change ships, how to stop an agent fast, how to prove nothing drifted, and one request end to end.',
                setting=PLATFORM_SETTING)

MLOPS = source('MLOps workflows on Azure Databricks', 'https://learn.microsoft.com/azure/databricks/machine-learning/mlops/mlops-workflow')
APP_VERSIONS = source('Track prompt and app versions', 'https://learn.microsoft.com/azure/databricks/mlflow3/genai/prompt-version-mgmt/prompt-registry/track-prompts-app-versions')
GITHUB_ENVS = source('Using environments for deployment', 'https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment')
ROUTING = source('Configure routing and fallbacks for models', 'https://learn.microsoft.com/azure/databricks/ai-gateway/configure-traffic-splitting')
LIFECYCLE = source('Manage model lifecycle in Unity Catalog', 'https://learn.microsoft.com/azure/databricks/machine-learning/manage-model-lifecycle/')
RATE_LIMITS = source('Apply rate limits to model and MCP services', 'https://learn.microsoft.com/azure/databricks/ai-gateway/rate-limits')
POLICIES = source('Service policies for AI securables', 'https://learn.microsoft.com/azure/databricks/data-governance/unity-catalog/service-policies/')
GOVERN_SERVICES = source('Discover and govern access to model services', 'https://learn.microsoft.com/azure/databricks/ai-gateway/govern-model-services')
AGENT_SERVER = source('Agent server', 'https://learn.microsoft.com/azure/databricks/agents/deploy/agent-server')
AGENT_RUNTIME = source('Agent Runtime', 'https://learn.microsoft.com/azure/databricks/agents/deploy/agent-runtime')
BUDGETS = source('Manage budgets for Unity Gateway', 'https://learn.microsoft.com/azure/databricks/ai-gateway/budgets')
AUDIT_LOG = source('Diagnostic log reference', 'https://learn.microsoft.com/azure/databricks/admin/account-settings/audit-logs')
GRANT_POLICIES = source('Govern models and MCPs with GRANT policies', 'https://learn.microsoft.com/azure/databricks/ai-gateway/govern-access-to-models-with-grant-policies')
AUTO_TTL = source('Automatic row deletion with auto time-to-live', 'https://learn.microsoft.com/azure/databricks/tables/operations/auto-ttl')
CONCEPTS = source('Unity Gateway concepts', 'https://learn.microsoft.com/azure/databricks/unity-gateway/concepts')
OAUTH_SP = source('Authorize service principal access to Azure Databricks with OAuth', 'https://learn.microsoft.com/azure/databricks/dev-tools/auth/oauth-m2m')
USAGE = source('Track model usage', 'https://learn.microsoft.com/azure/databricks/ai-gateway/usage-tracking')
GOVERN_MCP = source('Govern an MCP', 'https://learn.microsoft.com/azure/databricks/ai-gateway/govern-mcp-service')


lesson(MODULE, 'ship_a_change',
    title='Ship a change',
    checked='2026-11-01',
    sources=[MLOPS, APP_VERSIONS, GITHUB_ENVS, ROUTING, LIFECYCLE],
    cards=[
        card('One main branch, one change at a time',
             'Teams that change AI systems safely use **trunk-based development**: one main branch, `main`, that is '
             'always ready to deploy. Each change starts on a short branch that lives a few hours, or a day or two. '
             'It changes one thing: a prompt, a model, a route or a policy. Why only one? When a test score moves, '
             'you know which change moved it.',
             picture=sortby('Is it one change?',
                            sortrow('A new prompt', 'One thing: if a score moves, it points to the prompt', 'Ship it', icon='check'),
                            sortrow('A new prompt and a new model together', 'Two things: if the score drops, which one did it?', 'Split it', icon='x'),
                            sortrow('A prompt branch kept open for a month', 'The model behind it changes while it waits', 'Too old', icon='clock')),
             after='There are no branches for each environment either: dev, test and prod read the same code, with '
                   'different settings.'),
        card('A release is a list of versions',
             "An AI system's behaviour depends on more than its code. So a **release** is written down as a fixed "
             'set of versions that belong together, which teams call the release **tuple**. A change to any one of '
             'them is a candidate release, and it goes through the gate. That includes updating a library the code '
             'depends on, called a **dependency**.',
             picture=terms(('code', 'Code commit', 'the exact version of the code'),
                           ('chat', 'Prompt version', 'the prompt, as saved in the prompt registry'),
                           ('chart', 'Model', 'a pinned model name or version'),
                           ('cloud', 'Gateway configuration', 'routes, fallbacks, limits and policies, as applied'),
                           ('layers', 'Eval dataset version', 'the test items, and their fingerprint'),
                           ('scale', 'Judge', 'the model that grades the answers, and its prompt version')),
             after="These six are the main ones. The agent's own version, its runtime and the scorers belong on the "
                   'list too. The release note lists them all, and every trace points back to the release that '
                   'wrote it.'),
        card('The eval gate',
             "A change passes two test runs before it reaches users. Together they are the **eval gate**: a fail "
             "stops the change before any user sees it. Both runs use MLflow's GenAI evaluation, "
             '`mlflow.genai.evaluate`. The older `mlflow.evaluate` is for classic machine learning. Each run is '
             'logged as an MLflow run. The new version, the **candidate**, is compared with the champion, the '
             'version running now. They are compared on the same items, one at a time. That is a **paired** '
             'comparison. Some items are marked **must pass**, and they are read first. If the candidate fails '
             'one, it stops there, whatever its other results.',
             picture=steps(('flask', 'On the pull request', 'a quick smoke run on a small set of test items'),
                           ('flask', 'Before promotion', 'the full test set, frozen: the same items every time'),
                           ('scale', 'Against the champion', 'item by item, on the same items'),
                           ('x', 'A fail stops it', 'the change goes no further')),
             after='A real gate also says how sure it is. It repeats the run first, to see how much scores move on '
                   'their own, so a gap smaller than that is not called worse. Changing the test set, a pass mark '
                   'or the judge is a pull request of its own, with its own review. That way nobody can make the '
                   'gate easier just to let one change through.'),
        card('The same commit, dev to test to prod',
             'The commit that passed is the one that ships: it is promoted from dev to test to prod, never rebuilt '
             'on the way. Test and prod are each a GitHub **protected environment** with a **required reviewer**: the '
             'deploy waits until a named person approves it. GitHub Actions signs in to Azure Databricks as a service principal '
             'for each environment, with no secret stored in GitHub.',
             picture=steps(('code', 'Merge to main', 'it deploys to dev'),
                           ('flask', 'Test', 'the full test set runs'),
                           ('person', 'Prod', 'a required reviewer approves the deploy'),
                           ('rocket', 'Canary', 'a slice of real requests goes to the new version')),
             ),
        card('Land it dark, roll it back',
             'A new model or prompt can be merged before it gets any traffic: teams say it **lands dark**. The '
             'traffic split decides who gets it. A release is then a configuration change that moves traffic. It '
             'starts with a **canary**, a small slice of real requests. The same scorers, the checks that grade '
             'real answers, watch both slices. And a rollback is setting the split back to the trusted version, in '
             'one change.',
             picture=piles(pile('Release', [('rocket', 'Move 1 in 10 requests to the new version'),
                                            ('eye', 'The same scorers watch both slices')]),
                           pile('Rollback', [('reset', 'Move them back to the old version'),
                                             ('check', 'The same change, reversed')]))),
    ],
    example=example('One release, written down', """release  support-chat 2026-11-01
  code commit        4f2a91c
  prompt             support_answer v7
  model              the pinned name, unchanged
  gateway config     support_chat.yml, plan applied
  eval dataset       support_test v3, fingerprint 9b1e
  judge              correctness judge, prompt v2

gate      smoke on the pull request: passed
          full test set, paired with champion: passed
approve   prod: required reviewer approved
canary    1 in 10 requests"""),
    check=question(
        'team-sales opens one pull request that changes the support app\'s prompt and also switches to a newer '
        'model. What is the problem with that?',
        ['If a score drops, nobody can tell which change did it', 'Nothing: one pull request means one review',
         'The model change has to wait for the prompt to ship'],
        answer=0,
        clue='When a test score moves, what does changing only one thing let you see?',
        why='With one change per branch, a moved score points at one cause. One review does not fix that: if the '
            'score drops, it could be the prompt, the model or both, so you would not know which to undo.',
    ),
    angle=angle(
        pattern='One change, one gate, one commit',
        text="The big idea: a change ships one thing at a time, as a release you can name, through an eval gate that "
             "compares it with the champion item by item, and the same commit goes from dev to prod. Your code is "
             "the gate's last step. It holds if a must-pass item failed, or if the candidate is worse on more items "
             "than it is better. Otherwise it promotes.",
        say='"I ship one change at a time. The [[same commit|newest build|release branch::What passed the tests is '
            'what ships, never rebuilt.]] goes from dev to prod, and only if it is no worse than the champion, '
            'compared [[item by item|on average|by feel::How does a paired comparison line up the two versions?]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Promote or Hold',
        topic='platform',
        difficulty='easy',
        fn='promote_or_hold',
        prompt="""The function gets one test run for two versions of an app, and says whether the new one may ship.

- `champion` is the version running now, and `candidate` is the new one.
- Each is a dict from a test item id to whether that version passed it, like `{"q01": True, "q02": False}`. Both have the same items.
- `must_pass` is a list of item ids that must never fail, like `["q02"]`.

The candidate is **better** on an item when it passed and the champion failed. It is **worse** on an item when
the champion passed and it failed.

Return `"hold"` if the candidate failed any must-pass item. Also return `"hold"` if it is worse on more items
than it is better. Otherwise return `"promote"`.

Example: champion `{"q01": True, "q02": True}`, candidate `{"q01": True, "q02": False}` and must_pass `["q02"]`
give `"hold"`, because q02 must never fail.""",
        pattern='Check the must-pass items first, then count better and worse item by item.',
        target='one look at each item',
        realworld="This is the last step of an eval gate: the same items, compared one at a time, with the cases "
                  'that must never break checked first.',
        practice=practice(
            intro='Three situations about shipping a change.',
            explain='A change ships one thing at a time, through a gate that compares it with the champion item by '
                    'item, and the commit that passed is the one that ships. You held a candidate that broke a '
                    'must-pass item, kept one commit moving through every stage, and rolled back before fixing.',
            pattern='Compare item by item, ship what passed',
            realworld="When a candidate wins on average, you'll still read the must-pass items first; when someone "
                      "wants a branch for prod, you'll promote the same commit instead; and when a canary goes wrong, "
                      "you'll set the split back before anyone starts a fix.",
            asks=[
                ask('The candidate is better than the champion on q03 and q05, and worse on q02. Item q02 is '
                    'marked must pass. Promote it or hold it?',
                    ['Hold: it failed a must-pass item', 'Promote: it wins more items than it loses',
                     'Promote: its average score is higher'],
                    answer=0,
                    evidence=evidence('code', title='The full test set, paired', text="""item  champion  candidate
q01   pass      pass
q02   pass      fail       must pass
q03   fail      pass
q04   pass      pass
q05   fail      pass"""),
                    clue='Which items does the gate read before it counts wins and losses?',
                    why='The gate reads the must-pass items first, and the candidate broke q02. Promoting it on a '
                        '2 to 1 win would break that answer for every user. That is the Reliability pillar.',
                    wrong=[None, 'Winning 2 items to 1 does not excuse breaking one that must pass.',
                           'An average hides which item broke, and q02 must never break.']),
                ask('A developer on team-sales wants a branch called prod. They would copy changes into it at '
                    'each release. What do you tell them?',
                    ['No: ship the same commit to every stage', 'Yes: a prod branch keeps prod safe',
                     'Yes, as long as each copy is reviewed'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"Let\'s keep a branch called prod, and copy changes into it when we '
                                           'release."'),
                    clue='Is a copied change the same thing that passed the eval gate?',
                    why='Copying a change into another branch makes a new commit, so what reaches prod is not the '
                        'commit that passed the gate. Keep one main branch, and promote the same commit through dev, '
                        'test and prod. That is the Operational Excellence pillar.',
                    wrong=[None, 'A prod branch drifts away from main, so what ships is no longer what was tested.',
                           'A review reads the copy, but the copy never went through the eval gate.']),
                ask("The new version gets 1 in 10 requests as a canary. The scorers pass 71 in 100 of its answers, "
                    "and 94 in 100 of the champion's. What do you do first?",
                    ['Roll back now, then fix it on a branch', 'Edit the prompt in prod tonight',
                     'Leave it running: it is only 1 in 10'],
                    answer=0,
                    evidence=evidence('code', title='Canary, prod_ai.sales.support_chat, last hour', text="""slice       requests  answers that passed the scorers
champion       2,700  94 in 100
candidate        300  71 in 100"""),
                    clue='Which change gives every user the trusted version back fastest?',
                    why='Moving the split back to the champion is one change, and every user gets the trusted version '
                        'again. Then the fix goes through a branch and the gate like any other. That is the '
                        'Reliability pillar.',
                    wrong=[None, 'A hand edit in prod skips the gate, so the code no longer says what runs.',
                           '1 in 10 is still real people getting worse answers: 300 in the last hour.']),
            ],
        ),
        starter="""def promote_or_hold(champion, candidate, must_pass):
    # your code here
    pass
""",
        solution="""def promote_or_hold(champion, candidate, must_pass):
    for item in must_pass:
        if not candidate[item]:
            return "hold"
    better = 0
    worse = 0
    for item in champion:
        if candidate[item] and not champion[item]:
            better += 1
        elif champion[item] and not candidate[item]:
            worse += 1
    if worse > better:
        return "hold"
    return "promote"
""",
        cases=[
            case({'q01': True, 'q02': True, 'q03': False, 'q04': True, 'q05': False},
                 {'q01': True, 'q02': False, 'q03': True, 'q04': True, 'q05': True}, ['q01'],
                 expected='promote', sample=True),
            case({'q01': True, 'q02': True, 'q03': False, 'q04': True, 'q05': False},
                 {'q01': True, 'q02': False, 'q03': True, 'q04': True, 'q05': True}, ['q02'],
                 expected='hold'),
            case({}, {}, [], expected='promote'),
            case({'a': True, 'b': True, 'c': False}, {'a': False, 'b': False, 'c': True}, [], expected='hold'),
            case({'a': True, 'b': False}, {'a': False, 'b': True}, [], expected='promote'),
            case({'a': False}, {'a': False}, ['a'], expected='hold'),
        ],
        guided="""def promote_or_hold(champion, candidate, must_pass):
    # Replace every ___ with real code, then run the tests.

    for item in must_pass:
        # Step 1: a must-pass item the candidate failed stops it straight away.
        if ___:
            return "hold"
    better = 0
    worse = 0
    for item in champion:
        if candidate[item] and not champion[item]:
            better += 1
        # Step 2: the champion passed it, and the candidate did not.
        elif ___:
            worse += 1
    if worse > better:
        return "hold"
    return "promote"
""",
        fills=['not candidate[item]', 'champion[item] and not candidate[item]'],
        concepts=[
            ['Returning early', '`return` ends the function at once, so later checks never run.',
             """for x in [1, 2]:
    if x == 1:
        return "stop"   # 2 is never looked at"""],
            ['True and not False', '`a and not b` is True only when a is True and b is False.',
             'True and not False   # True'],
            ['Looping over a dict', 'A `for` loop over a dict goes through its keys, so `champion[item]` reads each value.',
             """d = {"q01": True}
for item in d:
    d[item]   # True"""],
        ],
        byhand='First read the must-pass items: if the candidate failed one, hold. Then go down the items and tick '
               '"better" where only the candidate passed and "worse" where only the champion did. More worse than '
               'better means hold.',
        why='An average can rise while an important answer breaks. Checking must-pass items first, then comparing '
            'item by item, is how a gate catches that.',
    ),
)


lesson(MODULE, 'stop_it_fast',
    title='Stop it fast',
    checked='2026-11-01',
    sources=[RATE_LIMITS, POLICIES, GOVERN_SERVICES, AGENT_SERVER, AGENT_RUNTIME, BUDGETS],
    cards=[
        card('Five switches, fastest first',
             'One switch is not enough, because each works at a different level and speed. So every agent gets a '
             'list of **kill switches** (ways to stop it), written down fastest first. The first one is quick, and '
             'it touches nobody else. That is because the agent has a limit of its own on the model service, and '
             'on each MCP service it uses. The second is a deny policy: a policy rule that sees who is calling and '
             'blocks only that one agent.',
             picture=steps(('gauge', 'Cut its rate limit', 'to the lowest value the service accepts: new calls stop within about a minute'),
                           ('x', 'A deny policy', 'a service policy, still in Beta, that refuses that agent at the gateway'),
                           ('lock', 'Revoke EXECUTE', 'checked again on its next request'),
                           ('bot', 'Disable its service principal', 'a token it already has can work for up to an hour'),
                           ('power', 'Stop the runtime', 'drain it first, then stop the app')),
             after="Is 0 accepted as a limit? The docs don't confirm it yet, so the practice run in dev checks. Until "
                   'then, the first switch is the lowest value the service accepts.'),
        card('Drain before you stop',
             '**DurableAgentServer** is the agent server that recovers from crashes. After a crash, it restarts the '
             'runs the crash interrupted. It has no limit on attempts, unless its **recovery handler**, code you '
             'write, stops it. So stop it in order. First **drain** it: let the runs already started finish, and '
             'start no new ones. Then stop the Agent Runtime app with `agentbricks deployments stop`. Write its '
             'recovery handler to check a stop flag and the number of attempts, so a stopped agent stays stopped.',
             picture=steps(('clock', 'Drain', 'the runs already started finish; no new ones start'),
                           ('power', 'Stop', 'stop the Agent Runtime app'),
                           ('check', 'It stays stopped', 'crash recovery has nothing to restart')),
             after="How runs that are queued or in progress get cancelled isn't confirmed in the docs yet: find out "
                   'in the practice run.'),
        card('An alert rule pulls the first switch',
             'An **alert rule** spots a runaway agent and pulls the first switch for you. It looks for '
             'signs like one agent calling 50 times a minute. Another sign is the same tool, with the same '
             'arguments, again and again. A SQL alert runs a job that cuts the limit. It also sends an urgent alert '
             'to the person on call, who decides about the other switches.',
             picture=steps(('activity', 'The signal', 'calls a minute, steps per task, the same tool again and again'),
                           ('alert', 'The alert fires', 'a SQL alert crosses its line'),
                           ('gauge', 'The first switch', "a job cuts the agent's limit"),
                           ('person', 'A person decides', 'told at once, and chooses the next switch'), decide=True),
             after='Every automatic stop is logged, with what set it off and the evidence.'),
        card('Practise it, and time it',
             'A switch nobody has pulled is a hope. So once a quarter, start a runaway on purpose in dev, like a loop '
             'or a flood of tool calls. Then pull each switch in turn. Write down what you learn in the runbook, next to '
             'each switch.',
             picture=terms(('clock', 'How long it takes', 'from pulling it to the last new call'),
                           ('person', 'Who may pull it', 'named, so nobody waits for permission'),
                           ('reset', 'What still finishes', 'calls already sent, runs already started'),
                           ('chat', 'What the user sees', 'written down, so support can explain it'))),
        card('A budget is a backstop',
             'A budget can block more calls, but it is not a switch. It blocks only when the month\'s spend '
             'reaches its line. Even then the block is approximate: some spend can pass the line, and calls '
             'already running finish. So keep it as the last thing that stops spend, after the switches.',
             picture=piles(pile('A switch', [('gauge', 'Works in about a minute'), ('person', 'Pulled on purpose')]),
                           pile('A budget block', [('coin', 'Acts only when the month\'s money is spent'),
                                                   ('alert', 'Approximate: some spend passes the line')]))),
    ],
    example=example('The kill switches for one agent', """agent  sp-sales-agent      runbook, fastest first
1  rate limit on support_chat and its MCP services
     -> the lowest value the service accepts
2  deny service policy for sp-sales-agent
3  revoke EXECUTE on prod_ai.sales.support_chat
4  disable the service principal   (a token can last an hour)
5  drain, then: agentbricks deployments stop
backstop  the team budget block

alert rule  50 calls a minute or more -> switch 1, alert the person on call"""),
    check=question(
        'sp-sales-agent is stuck in a loop and calls the model service 300 times a minute. Other apps use the '
        'same service. Which switch do you pull first?',
        ["Cut the agent's own rate limit", "Disable the agent's service principal",
         "Cut the service's limit for everyone"],
        answer=0,
        clue='Which switch works in about a minute and touches only this agent?',
        why="The agent's own limit stops its new calls within about a minute and leaves other apps alone. The "
            'service-wide limit is as fast but stops every app, and a disabled service principal can keep its '
            'token for up to an hour.',
    ),
    angle=angle(
        pattern='Fastest switch first, and try it before you need it',
        text="The big idea: every agent has a list of kill switches, fastest first: its own rate limit, a deny "
             "policy, the grant, the sign-in, then the runtime. An alert rule pulls the first one for you, and each one "
             "is tried in dev and timed. Your code is the alert rule: it finds the first minute an agent's calls reach the line.",
        say='"Every agent gets kill switches, written down [[fastest first|strongest first|newest first::Its own '
            'rate limit comes before anything else.]], and an alert rule pulls the first one for it. We [[try each '
            'one in dev|trust the runbook|test them in prod::Where can you pull a switch without hurting real '
            'users?]] and time how long it takes."',
        classic=None,
    ),
    exercise=exercise(
        title='When Does the Alert Fire?',
        topic='platform',
        difficulty='easy',
        fn='first_trip',
        prompt="""The function reads one agent's calls, minute by minute, and finds when the alert rule fires.

- `log` is a list of dicts, one for each minute, in time order, like `{"minute": "10:42", "calls": 55}`.
- `threshold` is the alert rule's line, like `50`.

The rule fires in the first minute whose `calls` is at or above the line. A minute equal to the line counts.

Return that minute, like `"10:42"`. If no minute reaches the line, return `None`.

Example: `[{"minute": "10:41", "calls": 48}, {"minute": "10:42", "calls": 55}]` with a threshold of `50` gives
`"10:42"`, the first minute at or above 50.""",
        pattern='Walk the minutes in order and stop at the first one that reaches the line.',
        target='one look at each minute, stopping early',
        realworld='This is the rule behind an alert rule: the first minute an agent crosses its line is the '
                  'moment the first switch should be pulled.',
        practice=practice(
            intro='Three situations about stopping an agent.',
            explain='Every agent has a list of kill switches, fastest first, and an alert rule pulls the first one. You '
                    'put the switches in the right order, kept the budget as a backstop, and asked for a practice '
                    'run instead of trusting a list nobody had tried.',
            pattern='Fastest first, tried in dev',
            realworld="When you write a runbook, you'll put the agent's own limit first; when someone says the budget "
                      "will stop it, you'll ask how fast; and when switches have never been pulled, you'll book a "
                      'practice run in dev.',
            asks=[
                ask("This draft runbook lists sp-sales-agent's kill switches in the order you pull them. What is "
                    'wrong with the order?',
                    ['The fastest switch should come first', 'Nothing: the strongest switch goes first',
                     'The budget block should be at the top'],
                    answer=0,
                    evidence=evidence('code', title='Draft runbook for sp-sales-agent', text="""1  disable the service principal
2  cut its rate limit
3  a deny policy
4  revoke EXECUTE"""),
                    clue="A disabled identity's token can keep working. For how long?",
                    why="A disabled service principal can keep its token for up to an hour. The agent's own limit "
                        'stops new calls within about a minute, so it goes first, and the runaway stops in a minute, '
                        'not an hour. That is the Operational Excellence pillar.',
                    wrong=[None, 'Strongest is not fastest: a token can keep working for an hour after the disable.',
                           'A budget blocks only after the month\'s money is spent, so it goes last.']),
                ask('team-sales says their budget blocks spend at $500 a month, so their agent needs no kill '
                    'switches. Is the budget enough?',
                    ['No: it blocks only after the money is spent', 'Yes: a budget block stops every call at once',
                     'Yes, if the budget is checked every minute'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"Our budget blocks at $500 a month, so we don\'t need kill switches."'),
                    clue='A runaway starts on day 2 of the month. How much can it spend before the budget acts?',
                    why='A budget blocks only once the month\'s $500 is spent, and some spend can pass the line before '
                        'the block lands. The agent\'s own rate limit stops a runaway in about a minute and saves the '
                        'rest of the money. That is the Cost Optimization pillar.',
                    wrong=[None, 'The block is approximate: some spend passes the line, and calls already '
                                 'running finish.',
                           'Checking more often does not help. It still waits until the month\'s money is spent.']),
                ask('A developer on team-sales says the kill switches were written down last year. Nobody has '
                    'pulled them since, so they must work. What do you do?',
                    ['Book a practice run in dev and time each one', 'Nothing: the switches are written down',
                     'Test each switch in prod at a quiet hour'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"We wrote the kill switches down last year. We\'ve never needed them, so '
                                           'they work."'),
                    clue='What do you really know about a switch nobody has pulled?',
                    why='Never needed is not the same as working. Start a runaway in dev, pull each switch, and write '
                        'down how long it took and what still finished. That is the Reliability pillar.',
                    wrong=[None, 'A switch nobody has pulled may not work when you need it.',
                           'A test in prod cuts off real users. Dev is where you practise.']),
            ],
        ),
        starter="""def first_trip(log, threshold):
    # your code here
    pass
""",
        solution="""def first_trip(log, threshold):
    for row in log:
        if row["calls"] >= threshold:
            return row["minute"]
    return None
""",
        cases=[
            case([{'minute': '10:40', 'calls': 12}, {'minute': '10:41', 'calls': 48},
                  {'minute': '10:42', 'calls': 55}, {'minute': '10:43', 'calls': 300}], 50,
                 expected='10:42', sample=True),
            case([], 50, expected=None),
            case([{'minute': '09:00', 'calls': 50}], 50, expected='09:00'),
            case([{'minute': '09:00', 'calls': 49}, {'minute': '09:01', 'calls': 10}], 50, expected=None),
            case([{'minute': '14:10', 'calls': 5}, {'minute': '14:11', 'calls': 90},
                  {'minute': '14:12', 'calls': 20}, {'minute': '14:13', 'calls': 95}], 60, expected='14:11'),
        ],
        guided="""def first_trip(log, threshold):
    # Replace every ___ with real code, then run the tests.

    for row in log:
        # Step 1: has this minute reached the line? Equal counts too.
        if ___:
            # Step 2: give back the minute, and stop looking.
            return ___
    return None
""",
        fills=['row["calls"] >= threshold', 'row["minute"]'],
        concepts=[
            ['At or above', '`>=` is True when the left side is bigger or the same.',
             '50 >= 50   # True'],
            ['Stop at the first match', 'A `return` inside the loop ends it at the first row that passes.',
             """for n in [3, 8, 9]:
    if n > 5:
        return n   # 8"""],
            ['None for nothing found', 'After the loop, `return None` says no row ever passed.',
             'first_trip([], 50)   # None'],
        ],
        byhand="Go down the minutes in order. The first one whose calls are at or above the line is the answer; if "
               "you reach the end without one, the answer is None.",
        why='An alert rule is only useful if it fires at the first bad minute. Stopping at the first match is how it '
            'pulls the switch early instead of at the end of a bad hour.',
    ),
)


lesson(MODULE, 'nothing_drifted',
    title='Prove nothing drifted',
    checked='2026-11-01',
    sources=[AUDIT_LOG, GOVERN_SERVICES, GRANT_POLICIES, BUDGETS, AUTO_TTL],
    cards=[
        card('What drift means',
             '**Configuration drift**, or just **drift**, is the gap between what the workspace really has and what '
             'the code says it should have. Monitoring uses the same word for a change in what people ask. That is '
             'a different kind of drift. '
             'It starts with a change made by hand: a grant given in a hurry, a limit raised for a demo, a tag '
             'removed by mistake. Nothing breaks that day, which is why nobody notices.',
             picture=piles(pile('The code says', [('check', 'EXECUTE for sp-sales-chat-prod'),
                                                  ('gauge', 'A limit for sp-sales-agent')]),
                           pile('The workspace has', [('check', 'EXECUTE for sp-sales-chat-prod'),
                                                      ('person', 'EXECUTE for one person, by hand'),
                                                      ('alert', 'A higher limit, raised for a demo')])),
             after='The rule in the code: grants go to groups and service principals, never to one person.'),
        card('A daily audit',
             'A scheduled audit job runs every day. It only reads, so it is cheap, and it compares the repository '
             'with each workspace. Each check writes one row into an audit results table. A row holds the check, '
             'the object, pass or fail, the evidence and the time. That table feeds a dashboard and alerts.',
             picture=terms(('lock', 'Grants', 'who has what, from databricks grants get-effective or the information schema: the docs do not yet say which covers services'),
                           ('gauge', 'Rate limits', 'the same as in the code'),
                           ('x', 'Service policies', 'attached, and the same'),
                           ('tag', 'Tags', 'service tags and governed tags on every service'),
                           ('coin', 'Budgets', 'there, with the same thresholds'),
                           ('clock', 'Record lifetimes', 'set on every trace and inference table')),
             after='The record lifetimes you set earlier are checked too. So if someone removes one, it shows up the '
                   'next morning. The audit also lists new objects, not only changed ones. That is because a new '
                   'service in system.ai arrives with the default access. Each quarter, every service owner '
                   'confirms who may call their service, using the audit results.'),
        card('Two silent failures',
             'Two missing tags break things, and nothing warns you when the tag goes. A missing '
             '**governed tag** silently removes access '
             'that came from a GRANT policy. That is because the policy gives EXECUTE only to services that carry '
             'the tag. A missing **service tag** silently drops spend from a budget. That is because budgets pick '
             'services by their tags, and never see an untagged one.',
             picture=sortby('What happens when the tag is missing?',
                            sortrow('Governed tag access_status = approved', 'The GRANT policy no longer matches, and apps that got access from it lose it', 'No access', icon='lock'),
                            sortrow('Service tag team: sales', "The team's budget no longer counts that service", 'Not counted', icon='coin')),
             after='So the audit checks every service carries both kinds of tag.'),
        card('Who changed it, and the fix',
             "Between audits, the audit log is the detector. It is not the daily audit: it is the workspace's own "
             'record of changes, `system.access.audit`. It records an `updatePermissions` event for every grant and '
             "revoke, and an `mcpCall` event for every tool call. Alert on a change made by anyone other than the "
             "pipeline's own service principal. That is a change made by hand. A finding, a check that failed, is "
             'never fixed by hand either. The pipeline undoes it, or a pull request writes it into the code. The '
             'audit keeps failing until one of those happens.',
             picture=piles(pile('Find it', [('listcheck', 'The daily audit fails a check'),
                                            ('search', 'The audit log says who changed it')]),
                           pile('Fix it in code', [('reset', 'The pipeline undoes it'),
                                                   ('code', 'Or a pull request adopts it')])),
             after='Test the audit itself: in dev, make one grant by hand on purpose and check the audit catches it '
                   'and the pipeline removes it. A check that has never caught anything is not proven yet.'),
    ],
    example=example('One audit row a day, for each check', """check              object                       result  evidence
grants: no people  prod_ai.sales.support_chat   FAIL    EXECUTE -> a user account
rate limit         sp-sales-agent               FAIL    code 120, workspace 600
service tags       prod_ai.sales.docs_reader    FAIL    no team tag
lifetime           prod_ai.gov.gateway_traces   PASS    17 days"""),
    check=question(
        'The audit log shows a person on team-sales gave their own account `EXECUTE`, the grant to call '
        '`prod_ai.sales.support_chat`, by hand. They say they need it for a week of testing. What do you do?',
        ['The pipeline undoes it; their group gets it by pull request', 'Leave it for the week, then revoke it by hand',
         'Revoke it by hand now, and close the ticket'],
        answer=0,
        clue='Two rules apply: who a grant may go to, and how drift is fixed.',
        why='Grants go to groups, never to one person, and a change made by hand is never fixed by hand. The '
            'pipeline removes it, and a pull request grants their group if the need is real. Leaving it for a week '
            'keeps access nobody reviewed.',
    ),
    angle=angle(
        pattern='The code is the truth, the audit proves it',
        text="The big idea: drift is the gap between the workspace and the code. A daily audit compares them, the "
             "audit log says who made a change by hand, and every finding is fixed in code: undone by the pipeline "
             "or adopted by a pull request. Your code does the comparison: it lists every setting that differs, or "
             "that one side is missing.",
        say='"Drift is the gap between the workspace and the [[code|bill|docs::What the pipeline deploys from.]], so '
            'a daily audit compares them. A change made by hand is never fixed by hand: the [[pipeline|owner|'
            'audit::It undoes the change, unless a pull request adds it to the code.]] puts it right."',
        classic=None,
    ),
    exercise=exercise(
        title='Find the Drift',
        topic='platform',
        difficulty='easy',
        fn='drifted',
        prompt="""The function compares what the code says with what the workspace has, and lists every setting that differs.

- `in_code` is what the repository says: a dict from a setting's name to its value, like `{"support_chat.rate_limit": 120}`.
- `in_workspace` is what the workspace really has, in the same shape.

A setting has drifted when the two values differ. It has also drifted when only one side has it.

Return the names of every drifted setting, as a list in alphabetical order.

Example: `{"support_chat.rate_limit": 120, "support_chat.tag.team": "sales"}` in code and
`{"support_chat.rate_limit": 600, "support_chat.tag.team": "sales"}` in the workspace give
`["support_chat.rate_limit"]`.""",
        pattern='Look at every name from both sides once, and keep the ones that differ or are missing.',
        target='one look at each setting name',
        realworld="This is the heart of a drift audit: every setting the code and the workspace disagree on, "
                  'including the ones only one side has.',
        practice=practice(
            intro='Three situations about drift.',
            explain="Drift is the gap between the workspace and the code, and the fix always goes through the code. "
                    'You turned a hand-made change into a pull request, traced missing spend to a missing tag, and '
                    'picked out the change made by a person in the audit log.',
            pattern='Find it by comparing, fix it in code',
            realworld="When a team changes something by hand, you'll ask for the pull request; when a budget looks "
                      "too low, you'll check the service tags; and when a grant appears from nowhere, you'll read the "
                      'audit log to see who made it.',
            asks=[
                ask('team-sales raised their rate limit by hand for a demo yesterday. They want to keep the new '
                    'value. What do you tell them?',
                    ['Put it in code by pull request, or it is undone', 'Fine: the audit only reports it',
                     'Fine, as long as it is lowered next week'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"We raised our rate limit by hand for the demo yesterday. It\'s fine, '
                                           'we\'ll leave it."'),
                    clue='What does the next pipeline run do to a value that differs from the code?',
                    why='The code stays the truth. Either the higher limit goes into code with a reason, or the next '
                        'pipeline run sets it back, and their traffic starts getting 429s with no warning. That is '
                        'the Operational Excellence pillar.',
                    wrong=[None, 'The audit keeps failing until the code and the workspace agree again.',
                           'A promise to lower it later is still a change by hand that nobody reviewed.']),
                ask("team-sales's budget shows $1,200 spent this month. The billing table, `system.billing.usage`, "
                    "shows $3,000 for the team's services. Why is the budget so low?",
                    ['A service lost its team tag', 'The budget only counts at month end',
                     'The billing table counts each call twice'],
                    answer=0,
                    evidence=evidence('code', title='This month, team-sales', text="""Budget team-sales (filter team = sales)   spend: $1,200
Billing table, team-sales's services       spend: $3,000

prod_ai.sales.support_chat   tags: team: sales, app: support, env: prod
prod_ai.sales.docs_reader    tags: app: docs, env: prod"""),
                    clue='Which service would a budget filter of team = sales miss?',
                    why='`docs_reader` has no team tag, so the budget never counts its spend, and the team could '
                        'overspend with no alert. Put the tag back in code, and the audit checks every service has '
                        'it. That is the Cost Optimization pillar.',
                    wrong=[None, 'A budget counts as the month goes. The gap is spend it never saw.',
                           'The billing table is not the problem. The budget is missing a whole service.']),
                ask('The audit log shows two `updatePermissions` events, which are grant changes, on '
                    '`prod_ai.sales.support_chat` today. Which one needs an alert?',
                    ["The 14:47 change, by a person's account", 'The 09:12 change, by the pipeline',
                     'Both: every grant change is a risk'],
                    answer=0,
                    evidence=evidence('code', title='system.access.audit, today, prod_ai.sales.support_chat', text="""time   action             changed by
09:12  updatePermissions  sp-platform-deploy   (the pipeline)
14:47  updatePermissions  a person's account"""),
                    clue='Which change did not come through the pipeline?',
                    why="The pipeline's change came from a reviewed pull request, and the person's did not. Alert on a "
                        'grant change by anyone but the pipeline, so the change by hand is not buried. That is the '
                        'Security pillar.',
                    wrong=[None, 'That one came from the code, through a reviewed pull request.',
                           "Alerting on the pipeline's own changes buries the one that matters."]),
            ],
        ),
        starter="""def drifted(in_code, in_workspace):
    # your code here
    pass
""",
        solution="""def drifted(in_code, in_workspace):
    names = set(in_code) | set(in_workspace)
    out = []
    for name in names:
        if name not in in_code or name not in in_workspace:
            out.append(name)
        elif in_code[name] != in_workspace[name]:
            out.append(name)
    return sorted(out)
""",
        cases=[
            case({'support_chat.rate_limit': 120, 'support_chat.tag.team': 'sales'},
                 {'support_chat.rate_limit': 600, 'support_chat.tag.team': 'sales'},
                 expected=['support_chat.rate_limit'], sample=True),
            case({}, {}, expected=[]),
            case({'a': 1}, {'a': 1}, expected=[]),
            case({'budget.team-sales': 500}, {}, expected=['budget.team-sales']),
            case({'grant.execute': 'sp-sales-chat-prod'},
                 {'grant.execute': 'sp-sales-chat-prod', 'grant.manage': 'a user account'},
                 expected=['grant.manage']),
            case({'z.limit': 60, 'a.tag': 'sales', 'm.ttl': 17}, {'z.limit': 90, 'a.tag': 'docs', 'm.ttl': 17},
                 expected=['a.tag', 'z.limit']),
        ],
        guided="""def drifted(in_code, in_workspace):
    # Replace every ___ with real code, then run the tests.

    # Step 1: every name from both sides, each once.
    names = ___
    out = []
    for name in names:
        if name not in in_code or name not in in_workspace:
            out.append(name)
        # Step 2: on both sides, but with different values.
        elif ___:
            out.append(name)
    return sorted(out)
""",
        fills=['set(in_code) | set(in_workspace)', 'in_code[name] != in_workspace[name]'],
        concepts=[
            ['Every name from two dicts', '`set(d)` is the set of its keys, and `|` joins two sets, keeping each once.',
             'set({"a": 1}) | set({"a": 2, "b": 3})   # {"a", "b"}'],
            ['Missing on one side', '`name not in d` is True when the dict has no such key.',
             '"b" not in {"a": 1}   # True'],
            ['Sorted output', '`sorted(...)` gives a new list in order, so the answer is the same every time.',
             'sorted(["z", "a"])   # ["a", "z"]'],
        ],
        byhand='Write down every setting name from both lists, once each. Cross off the ones on both sides with the '
               'same value; what is left has drifted. Put them in alphabetical order.',
        why="A setting that only one side has is drift too, and it's the kind that hides: a grant made by hand, or a "
            'budget nobody created. Looking at both sides catches it.',
    ),
)


lesson(MODULE, 'one_request',
    title='One request, start to finish',
    checked='2026-11-01',
    sources=[CONCEPTS, OAUTH_SP, GOVERN_SERVICES, POLICIES, RATE_LIMITS, ROUTING, USAGE, GOVERN_MCP],
    cards=[
        card('Sign in, then three grants',
             'Follow one call from the support app to `prod_ai.sales.support_chat`, through every layer you have '
             'met. First the app signs in with OAuth, as its own service principal, sp-sales-chat-prod. It gets a '
             "token that lasts about an hour, as in Sign in, don't carry keys. Then the gateway checks the three "
             'grants from Who may call it. EXECUTE can also come from a GRANT policy, which covers every '
             'service that carries a governed tag. If a grant is missing, the app gets PERMISSION_DENIED.',
             picture=steps(('lock', 'Sign in', 'OAuth, as sp-sales-chat-prod: no key anywhere'),
                           ('layers', 'USE CATALOG and USE SCHEMA', 'on prod_ai and on prod_ai.sales'),
                           ('check', 'EXECUTE', 'on prod_ai.sales.support_chat itself'))),
        card('Checked, limited, routed',
             'Next, the service policies read the request on the way in. You met them in The content check. They '
             'block a jailbreak attempt, a prompt written to get past the model\'s rules. On a model service, the '
             'jailbreak check reads only the request. They also block or redact a card number. A block comes '
             'back as a 200 reply that '
             'names its reason, not as an error. Then comes the rate limit, from Fair limits. If the app is over its '
             "share this minute, it gets a 429 and waits. Then comes routing, from When a model fails. The traffic "
             'split picks a model, and a fallback takes over if that model fails.',
             picture=steps(('alert', 'Policies, on the way in', 'blocked or redacted: a 200 with a reason'),
                           ('gauge', 'The rate limit', 'over its share: a 429, then wait and retry'),
                           ('reset', 'Routing', 'the split picks a model; a fallback if it fails'))),
        card('The answer, and what it leaves',
             'The model answers, and the output policy reads the answer before the app sees it. Then the records '
             'are written, as in Who spent what and How long we keep it. An ordinary call leaves no audit log event: the '
             'audit log records changes, like a grant, and tool calls.',
             picture=terms(('chat', 'The answer', 'checked again on the way out'),
                           ('chart', 'A usage row', 'who, which service, how many tokens'),
                           ('pencil', 'A trace', 'the prompt and the answer, word for word'),
                           ('listcheck', 'The audit log', 'only for changes and tool calls')),
             after='The same path is drawn as one picture in the blueprint (blueprint.html).'),
        card("An agent's tool call",
             "An agent, sp-sales-agent, calls a tool the same way, through its MCP service. You met this in An "
             "agent's tools, governed. It signs in, passes the three grants, and stays within its share of tool "
             'calls a minute. The tool '
             'must be on the selected list, and the ON CALL policy can ask a person first. The result comes back '
             'through the ON RESULT policy, and this time the audit log gets an `mcpCall` event.',
             picture=steps(('listcheck', 'Selected tools only', 'a tool not on the list is refused'),
                           ('person', 'The ON CALL policy', 'allow, deny, or ask a person first'),
                           ('cloud', 'The server', 'managed, custom or external'),
                           ('pencil', 'The records', 'a usage row, an mcpCall event, a trace'))),
        card('Around the path',
             'Two more layers are not stops on the path. They look after the path itself. The first is **LLMOps**, '
             'how changes to an AI system are tested and promoted. It decides how any part of the path changes: one '
             'change at a time, through the eval gate, with the same commit promoted. That was Ship a change. The '
             'second is the kill switch and the audit. Each kill switch is one of these stops turned against the '
             'agent when it runs away. That was Stop it fast. And the daily audit, from Prove nothing drifted, '
             'proves every stop still matches the code.',
             picture=piles(pile('How it changes', [('flask', 'The eval gate'), ('rocket', 'The same commit, dev to prod')]),
                           pile('How it stops', [('gauge', 'Cut the limit, deny, revoke'),
                                                 ('listcheck', 'A daily audit against the code')]))),
    ],
    example=example('One request, stage by stage', """stage        result  what the app sees
sign in      pass    sp-sales-chat-prod, OAuth
grants       pass    USE CATALOG, USE SCHEMA, EXECUTE
policy in    pass    nothing to block
rate limit   pass    within its share
routing      pass    main model, 9 in 10 slice
model        pass
policy out   pass
records      done    usage row, trace (no audit event)
-> answered"""),
    check=question(
        'The support app sends a request and gets back a 200 reply. The reply says the jailbreak check blocked it. '
        'Which stop on the path sent it back?',
        ['The service policy on the way in', 'The service policy on the way out', 'The grants on the service'],
        answer=0,
        clue='A 200 with a reason means a policy. Which words does a jailbreak check read?',
        why='A missing grant gives PERMISSION_DENIED, so a 200 that names its reason is a policy. A jailbreak arrives '
            'in what is sent, so the jailbreak check reads only the request: it is the policy on the way in.',
    ),
    angle=angle(
        pattern='Follow the request, find the first no',
        text="The big idea: one request meets every layer in order: sign in, the grants, the policies on the way in, "
             "the rate limit, routing, the model, the policy on the way out, then the records. Each stop answers in "
             "its own way, so what the caller saw tells you where it stopped. Your code finds the first stage that "
             "said no and what the caller saw.",
        say='"A request signs in, passes the grants, the policies and the limit, then reaches a model. When a call '
            'fails, I look for the [[first stop that said no|last stop it passed|model that answered::The stop where '
            'the path ended.]], because each stop answers [[differently|the same way|with an error::A 429, '
            'PERMISSION_DENIED, or a 200 with a reason.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Where Did It Stop?',
        topic='platform',
        difficulty='easy',
        fn='first_stop',
        prompt="""The function follows one request through the gateway, and says where it stopped and what the caller saw.

`stages` is a list of dicts, one for each stage, in order, like `{"stage": "grants", "result": "pass"}`.
`result` is `"pass"` or `"stop"`.

The stage names are `"sign_in"`, `"grants"`, `"policy_in"`, `"rate_limit"`, `"routing"`, `"model"`,
`"policy_out"` and `"records"`.

The starter gives you a dict called `sees`. It says what the caller gets back from four stages, like `"429"`
for `"rate_limit"`. Any other stage that stops a request shows `"an error"`.

Return a dict for the first stage that stopped the request, with two keys: `"stage"` and `"caller_sees"`. If no
stage stopped it, return `{"stage": None, "caller_sees": "answered"}`.

Example: `sign_in`, `grants` and `policy_in` pass, then `rate_limit` stops. That gives
`{"stage": "rate_limit", "caller_sees": "429"}`.""",
        pattern='Walk the stages in order, stop at the first "stop", and look up what that stage shows.',
        target='one look at each stage, stopping early',
        realworld='This is how you answer "why did my call fail?": find the first stage that said no, and match it '
                  'to what the caller saw.',
        practice=practice(
            intro='Three situations about one request.',
            explain='One request meets every layer in order, and each stop answers in its own way. You read a 429 as '
                    'a limit and waited, opened the trace to see which policy blocked a call, and saw a tool call '
                    'held for a person before it could send anything.',
            pattern='What the caller saw says where it stopped',
            realworld="When a team says the gateway broke their app, you'll ask what they saw first. A 429, "
                      "PERMISSION_DENIED and a 200 that names a policy each point to a different stop, and a "
                      'different fix.',
            asks=[
                ask("The support app's request passed sign-in, the grants and the policies. Then the rate limit "
                    'sent back a 429. What should the app do?',
                    ['Wait a little longer each time, then retry', 'Ask for MANAGE, the right to change the service',
                     'Retry at once, as fast as it can'],
                    answer=0,
                    evidence=evidence('code', title='One request from the support app', text="""sign in      pass   sp-sales-chat-prod
grants       pass
policy in    pass
rate limit   STOP   429 Too Many Requests"""),
                    clue="What does a 429 say about this minute's share?",
                    why='A 429 means the app used up its share for this minute, and nothing is broken. Waiting a '
                        'little longer each time, called backoff, turns a busy minute into a short delay. That is '
                        'the Reliability pillar.',
                    wrong=[None, "MANAGE lets you change the service. It never raises a caller's share.",
                           "Retrying at once uses up the next minute's share even faster."]),
                ask("A customer's question looked fine, but the support app replied 'Blocked by service policy'. A "
                    'support lead sends you the request id. Which record do you open first?',
                    ['The trace for that request id', 'The audit log for that hour',
                     'The usage table totals for the day'],
                    answer=0,
                    evidence=evidence('claim', who='A support lead on team-sales',
                                      text='"A customer asked why the app said \'Blocked by service policy\' when '
                                           'their question was fine. Here\'s the request id."'),
                    clue='Which record holds the exact words of that one request?',
                    why="The trace holds that request's exact words, if logging is on for the service. Read it with "
                        "the reply's block reason to see what the check reacted to, then tune the policy. The docs do "
                        'not yet say where block decisions are stored. That is the Operational Excellence pillar.',
                    wrong=[None, 'An ordinary call leaves no audit event. The audit log is for changes and tool calls.',
                           'Totals tell you how many calls were blocked, not why this one was.']),
                ask('sp-sales-agent calls the `send_invoice` tool through its MCP service. The ON CALL policy for '
                    'that tool says ASK. What happens to this call?',
                    ['It waits until a person approves it', 'It runs, and the result is checked after',
                     'It is refused, because tools cannot send'],
                    answer=0,
                    evidence=evidence('code', title='sp-sales-agent calls prod_ai.sales.crm_mcp', text="""tool         send_invoice       (on the selected list)
grants       pass
rate limit   pass
ON CALL      send_invoice -> ASK a person"""),
                    clue='What does ASK do before the tool runs?',
                    why='ASK holds the call until a person approves it. A sent invoice cannot be undone, so a check on '
                        'the result would come too late. That is the Security pillar.',
                    wrong=[None, 'A check on the result comes too late: the invoice would already be sent.',
                           'The tool is on the selected list, so it can run once a person approves.']),
            ],
        ),
        starter="""def first_stop(stages):
    sees = {"grants": "PERMISSION_DENIED", "policy_in": "200 with a block reason",
            "rate_limit": "429", "policy_out": "200 with a block reason"}
    # your code here
    pass
""",
        solution="""def first_stop(stages):
    sees = {"grants": "PERMISSION_DENIED", "policy_in": "200 with a block reason",
            "rate_limit": "429", "policy_out": "200 with a block reason"}
    for s in stages:
        if s["result"] == "stop":
            return {"stage": s["stage"], "caller_sees": sees.get(s["stage"], "an error")}
    return {"stage": None, "caller_sees": "answered"}
""",
        cases=[
            case([{'stage': 'sign_in', 'result': 'pass'}, {'stage': 'grants', 'result': 'pass'},
                  {'stage': 'policy_in', 'result': 'pass'}, {'stage': 'rate_limit', 'result': 'stop'}],
                 expected={'stage': 'rate_limit', 'caller_sees': '429'}, sample=True),
            case([], expected={'stage': None, 'caller_sees': 'answered'}),
            case([{'stage': 'sign_in', 'result': 'pass'}, {'stage': 'grants', 'result': 'stop'}],
                 expected={'stage': 'grants', 'caller_sees': 'PERMISSION_DENIED'}),
            case([{'stage': 'sign_in', 'result': 'pass'}, {'stage': 'grants', 'result': 'pass'},
                  {'stage': 'policy_in', 'result': 'pass'}, {'stage': 'rate_limit', 'result': 'pass'},
                  {'stage': 'routing', 'result': 'pass'}, {'stage': 'model', 'result': 'pass'},
                  {'stage': 'policy_out', 'result': 'stop'}],
                 expected={'stage': 'policy_out', 'caller_sees': '200 with a block reason'}),
            case([{'stage': 'sign_in', 'result': 'stop'}, {'stage': 'grants', 'result': 'stop'}],
                 expected={'stage': 'sign_in', 'caller_sees': 'an error'}),
            case([{'stage': 'sign_in', 'result': 'pass'}, {'stage': 'records', 'result': 'pass'}],
                 expected={'stage': None, 'caller_sees': 'answered'}),
        ],
        guided="""def first_stop(stages):
    # Replace every ___ with real code, then run the tests.

    sees = {"grants": "PERMISSION_DENIED", "policy_in": "200 with a block reason",
            "rate_limit": "429", "policy_out": "200 with a block reason"}
    for s in stages:
        # Step 1: is this the stage that stopped it?
        if ___:
            # Step 2: what that stage shows, or "an error" for any other stage.
            return {"stage": s["stage"], "caller_sees": ___}
    return {"stage": None, "caller_sees": "answered"}
""",
        fills=['s["result"] == "stop"', 'sees.get(s["stage"], "an error")'],
        concepts=[
            ['Stop at the first match', 'A `return` inside the loop ends it, so later stages are never read.',
             """for s in ["pass", "stop", "stop"]:
    if s == "stop":
        return s   # the first one"""],
            ['A lookup with a fallback', '`d.get(key, other)` gives the value for key, or `other` if the key is missing.',
             '{"a": "429"}.get("b", "an error")   # "an error"'],
            ['A dict as the answer', 'Return two facts together by putting them in one dict.',
             'return {"stage": "grants", "caller_sees": "PERMISSION_DENIED"}'],
        ],
        byhand='Go down the stages in order. At the first one marked stop, write its name and what it shows: '
               'PERMISSION_DENIED for grants, a 429 for the rate limit, a 200 with a reason for either policy, an error '
               'for anything else. No stop at all means answered.',
        why='"My call failed" has a different fix at every stage. Finding the first stop, and matching it to what '
            'the caller saw, turns a vague ticket into one clear answer.',
    ),
)
