"""The AI gateway: one front desk for every AI model, in the Platform track.

Written for someone new to all of it: each lesson starts from a real-looking message from a product team, shows
one idea with one picture, and practises it on that same situation. Facts are from Microsoft Learn's Unity
Gateway pages for Azure Databricks.
"""

from drill.content.modules.platform_world import PLATFORM_SETTING
from drill.content.model import (angle, ask, card, case, evidence, example, exercise, lesson, module, pile, piles,
                                 pillar, pillars, practice, question, sortby, sortrow, source, split, steps, terms,
                                 tile)

MODULE = module('ai-gateway', 'The AI gateway',
                'One front desk for every AI model: who may call it, how much, and a record of every call.',
                setting=PLATFORM_SETTING)

PROVIDERS = source('Model providers external to Databricks', 'https://learn.microsoft.com/azure/databricks/ai-gateway/model-provider-services')
PROVIDER_SETUP = source('Create and manage providers with Model Provider Services', 'https://learn.microsoft.com/azure/databricks/ai-gateway/create-model-provider-services')
MODEL_SERVICES = source('Custom model services', 'https://learn.microsoft.com/azure/databricks/ai-gateway/model-services')
RELEASE_NOTES = source('Unity Gateway release notes', 'https://learn.microsoft.com/azure/databricks/release-notes/unity-gateway/')
CONCEPTS = source('Unity Gateway concepts', 'https://learn.microsoft.com/azure/databricks/unity-gateway/concepts')
OAUTH_SP = source('Authorize service principal access to Azure Databricks with OAuth', 'https://learn.microsoft.com/azure/databricks/dev-tools/auth/oauth-m2m')
PATS = source('Monitor and revoke personal access tokens', 'https://learn.microsoft.com/azure/databricks/admin/access-control/tokens')
APP_AUTH = source('Configure authorization in a Databricks app', 'https://learn.microsoft.com/azure/databricks/dev-tools/databricks-apps/auth')
AGENT_RUNTIME = source('Agent Runtime', 'https://learn.microsoft.com/azure/databricks/agents/deploy/agent-runtime')
GOVERN_SERVICES = source('Discover and govern access to model services', 'https://learn.microsoft.com/azure/databricks/ai-gateway/govern-model-services')
MIGRATE = source('Migrate to Unity Gateway', 'https://learn.microsoft.com/azure/databricks/ai-gateway/migrate-to-unity-gateway')
RATE_LIMITS = source('Apply rate limits to model and MCP services', 'https://learn.microsoft.com/azure/databricks/ai-gateway/rate-limits')
ROUTING = source('Configure routing and fallbacks for models', 'https://learn.microsoft.com/azure/databricks/ai-gateway/configure-traffic-splitting')
USAGE = source('Track model usage', 'https://learn.microsoft.com/azure/databricks/ai-gateway/usage-tracking')
BUDGETS = source('Manage budgets for Unity Gateway', 'https://learn.microsoft.com/azure/databricks/ai-gateway/budgets')


lesson(MODULE, 'why_gateway',
    title='Why a gateway?',
    checked='2026-11-01',
    sources=[PROVIDERS, MODEL_SERVICES, RELEASE_NOTES],
    cards=[
        card('Two ways to reach a model',
             'team-sales has three apps that call an AI model straight at the **model provider** (the company that '
             'runs the model, such as Azure OpenAI). Each app keeps its own secret key, sets its own limits or none, '
             'and keeps no shared record of what it asked.',
             picture=piles(pile('Every app on its own', [('lock', 'A secret key copied into every app'),
                                                         ('alert', 'Nothing stops a runaway script'),
                                                         ('x', 'No record of who asked what'),
                                                         ('coin', 'A bill nobody can explain')]),
                           pile('Through a gateway', [('person', 'No keys: each app signs in as itself'),
                                                      ('gauge', 'Fair limits for every team'),
                                                      ('listcheck', 'A record of every call'),
                                                      ('chart', 'Spend for each team and app')]))),
        card('One front desk for every model',
             'A **gateway** is one front desk that every app goes through to reach a model. On Azure Databricks it '
             'is called **Unity Gateway**. It does four jobs:',
             picture=terms(('people', 'OAuth sign-in', 'everyone signs in as who they are, and each sign-in expires '
                                                        'within the hour'),
                           ('lock', 'Model provider service', 'the link to the provider, set up once by the platform '
                                                              'team and never handed to apps'),
                           ('clock', 'Rate limits', 'how many calls a team can make in a minute'),
                           ('pencil', 'Usage table', 'a record of every call: who, when and how much'))),
        card('What it must do, and how well',
             'Like every system, a gateway has **functional** requirements, what it must do, and **non-functional** '
             'ones, how well it must do it. One sentence often holds both, so cut it in two:',
             picture=split(['Let apps call a model', 'signed in, within limits, with a record'],
                           [tile('Let apps call a model'),
                            tile('Apps sign in, with no keys', icon='lock', look='dashed'),
                            tile('Limit each team, every minute', icon='clock', look='dashed'),
                            tile('Record every call', icon='listcheck', look='dashed')]),
             after='The solid line is functional. The dashed ones are non-functional: each can be checked with a yes '
                   'or no, or a number.'),
        card('Pillar by pillar',
             'Each part of the front desk holds up one of the pillars of a well-architected review that you used on '
             'the HR assistant.',
             picture=pillars('The AI gateway',
                             pillar('Security', 'lock', 'Who is calling, and may they?'),
                             pillar('Reliability', 'power', 'What stops one app taking everything?'),
                             pillar('Cost Optimization', 'coin', 'Who spent what, this month?', short='Cost'),
                             pillar('Operational Excellence', 'eye', 'Can we see what happened, and when?', short='Operations')),
             after='Each of these gets its own lesson in this module.'),
    ],
    example=example('Two ways an app reaches a model', """Without a gateway, in each app's settings:
  provider key: a secret, copied in
  limit:        none
  record:       none

Through the gateway, in the app:
  signs in as: sp-sales-chat-prod
  model: prod_ai.sales.support_chat
  (no key: the gateway keeps the
   provider link, limits and record)"""),
    check=question(
        "team-sales has three apps. Each calls the model provider with its own key, and nothing records the calls. "
        "The bill doubled this month. Which question can nobody answer?",
        ['Which app made the extra calls', 'Which provider sent the bill', 'How much the bill went up'],
        answer=0,
        clue='What would you need a record of to answer it?',
        why="The bill shows the provider and the total, but no app names. A gateway keeps a record of every call, so "
            "the extra spend would have an app's name next to it.",
    ),
    angle=angle(
        pattern='One front desk for every model',
        text="The big idea: a gateway is one front desk between your apps and the AI models they call. Apps sign in "
             "as themselves instead of holding the provider's key, the gateway limits how much each team can use, "
             "and it records every call. Your code lists the apps that still keep a key of their own: those are the "
             "first to move behind the gateway.",
        say='"Every app reaches our AI models through [[one gateway|its own key|a faster model::One place that every '
            'call goes through.]]. Apps sign in as themselves, with no keys, a limit stops a runaway, and every call '
            'is [[recorded|blocked|hidden::So we can say who spent what.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Find the Keys in Apps',
        topic='platform',
        difficulty='easy',
        fn='keys_in_apps',
        prompt="""`keys_in_apps(apps)` gets a list of apps that call an AI model. Each app is a dict, like
`{"name": "sales-chat", "key_in_app": True}`.

`key_in_app` is `True` when the app keeps the model provider's secret key in its own settings. `False` means it
calls the model through the gateway.

Return the names of the apps that keep a key, in alphabetical order. Return `[]` if none do.

Example: `sales-chat` keeps a key and `hr-helper` doesn't, so the answer is `["sales-chat"]`.""",
        pattern='Go through each item once and keep the ones that match.',
        target='one look at each app',
        realworld='This is the first list a platform team makes when it brings in a gateway: which apps keep a '
                  'provider key today, so each one can move to signing in as itself and calling a model by name.',
        practice=practice(
            intro='Three real-looking situations from team-sales. For each one, decide what the gateway would change.',
            explain="A gateway is one front desk between apps and models: apps sign in as themselves instead of "
                    "keeping the provider's key, the gateway limits how much each app or team can use, and it records "
                    "every call. You saw that each of these answers a different problem: a copied key, a runaway "
                    "script, and a bill nobody could explain.",
            pattern='One way in: sign-ins, limits and records',
            realworld="When a team wants to call a model straight from their app, you'll ask three questions: how "
                      "does it sign in, with no keys; what stops a runaway script; and how will we know who spent what?",
            asks=[
                ask("team-sales's support app keeps the provider's secret key in its own settings. What is the "
                    'biggest risk?',
                    ['Anyone who can read the settings can copy the key', 'The app answers slower because it holds a key',
                     'The model gives worse answers when called directly'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"Our support app calls the model with a provider key we keep in the '
                                           'app\'s settings. It works fine, so why move it behind the gateway?"'),
                    clue="Who can read an app's settings?",
                    why="Anyone who can read the settings can copy the key, and a copied key works until someone "
                        "changes it in every app. Through the gateway, the app signs in as itself and never holds the "
                        "key. That is the Security pillar: a leak stays small.",
                    wrong=[None, "Holding a key doesn't change speed. The risk is who can copy it.",
                           'The answers are the same either way. The risk is the copied key.']),
                ask("The provider's bill doubled, and nobody can say which app made the extra calls. Which gateway "
                    'feature would answer that?',
                    ['A record of calls and spend per app', 'A lower price for every call', 'An alert when the bill passed $3,000'],
                    answer=0,
                    evidence=evidence('code', title="The model provider's bill", text="""This month:   $4,200
Last month:   $2,100

Which app made the extra calls?
  (no record anywhere)"""),
                    clue='What was missing when you tried to answer the question?',
                    why="The gateway records every call and its cost, for each user, team and app. With that record, "
                        "the doubled bill has an app's name next to it, so you know where to save. That is the Cost "
                        'Optimization pillar.',
                    wrong=[None, 'The price comes from the provider. The gateway shows who spent it.',
                           "A budget alert says the bill is high. It can't say which app made it high."]),
                ask("sales-summary got stuck last night and used the provider's whole quota, the most it allows a "
                    'minute. Which gateway feature would have stopped it?',
                    ['A limit on how much each app can use', 'A record of every call it made', 'A second copy of the provider key'],
                    answer=0,
                    evidence=evidence('code', title='Three apps, one provider', text="""sales-chat     limit: none
sales-summary  limit: none
sales-search   limit: none

Last night sales-summary got stuck and
used up the provider's whole quota
(the most it allows a minute).
This morning the other two get errors."""),
                    clue='The problem is how much one app could use.',
                    why='A **rate limit** caps how much one app can use each minute. One stuck script can\'t take '
                        'everything, so the other apps keep working. That is the Reliability pillar. A record only '
                        'shows what happened afterwards.',
                    wrong=[None, "A record shows it afterwards. It doesn't stop it.",
                           'A second key would just let it use even more.']),
            ],
        ),
        starter="""def keys_in_apps(apps):
    # your code here
    pass
""",
        solution="""def keys_in_apps(apps):
    names = []
    for app in apps:
        if app["key_in_app"]:
            names.append(app["name"])
    return sorted(names)
""",
        cases=[
            case([{'name': 'sales-chat', 'key_in_app': True}, {'name': 'hr-helper', 'key_in_app': False},
                  {'name': 'ops-summary', 'key_in_app': True}], expected=['ops-summary', 'sales-chat'], sample=True),
            case([], expected=[]),
            case([{'name': 'sales-chat', 'key_in_app': False}, {'name': 'hr-helper', 'key_in_app': False}], expected=[]),
            case([{'name': 'sales-search', 'key_in_app': True}], expected=['sales-search']),
            case([{'name': 'zeta', 'key_in_app': True}, {'name': 'alpha', 'key_in_app': True},
                  {'name': 'mid', 'key_in_app': True}], expected=['alpha', 'mid', 'zeta']),
        ],
        guided="""def keys_in_apps(apps):
    # Replace every ___ with real code, then run the tests.

    names = []
    for app in apps:
        # Step 1: does this app keep a key of its own?
        if ___:
            names.append(app["name"])

    # Step 2: put the names in alphabetical order.
    return ___
""",
        fills=['app["key_in_app"]', 'sorted(names)'],
        concepts=[
            ['Looping over a list', '`for app in apps:` runs the same steps once for each item in the list.',
             """for name in ["tea", "cake"]:
    print(name)   # tea, then cake"""],
            ['Reading a value from a dict', '`app["key_in_app"]` gives the value stored under that name.',
             """app = {"name": "sales-chat", "key_in_app": True}
app["key_in_app"]   # True"""],
            ['Putting names in order', '`sorted(names)` gives a new list in alphabetical order.',
             """sorted(["b", "a"])   # ["a", "b"]"""],
        ],
        byhand='Read each app in turn. If it keeps a key, write its name down. Then put the names in alphabetical order.',
        why='Every key kept inside an app is one more copy to guard, and one more place to change if it leaks. The '
            'list says which apps to move behind the gateway first.',
    ),
)


_NAMES = """prod_ai.providers.azure_openai
  a model provider service
prod_ai.sales.support_chat
  a model service
system.ai.microsoft_365
  an MCP service"""


lesson(MODULE, 'gateway_parts',
    title='The parts and their names',
    checked='2026-11-01',
    sources=[CONCEPTS, MODEL_SERVICES, PROVIDER_SETUP],
    cards=[
        card('Three kinds of service',
             'Behind the front desk sit three kinds of **service** you will use most. Each one lives in Unity '
             'Catalog, so people and apps can be given access to it, the same way as to a table.',
             picture=terms(('cloud', 'Model provider service', 'the link to an outside provider. For Azure OpenAI it '
                                                                'signs in with a Unity Catalog service credential, an '
                                                                'identity Azure manages, so there is no key. Other '
                                                                'providers keep their API key in a Unity Catalog secret.'),
                           ('chat', 'Model service', 'the name an app calls; it sends each request on to a model'),
                           ('bot', 'MCP service', 'a set of tools an agent can use, such as reading Outlook mail')),
             after="Databricks' own models and tools are there already, in a part of the catalog called `system.ai`."),
        card('Every service has a three-part name',
             'Like a table, every service has a full name in three parts: the catalog, the schema and the service. '
             'Apps, grants and the records all use the full name.',
             picture=steps(('layers', 'Catalog', 'prod_ai: one for each environment'),
                           ('layers', 'Schema', 'sales: one for each app or team'),
                           ('chat', 'Service', 'support_chat: the thing the app calls')),
             after='Put together: `prod_ai.sales.support_chat`.'),
        card('Call it by name',
             "team-sales's app only knows the name. What sits behind the name is the platform team's to change, so "
             'the app never breaks when a model is replaced.',
             picture=piles(pile('The app knows', [('chat', 'The name: prod_ai.sales.support_chat')]),
                           pile('The platform can change', [('reset', 'Which model answers'),
                                                            ('sparkle', 'A new model, on a slice of requests'),
                                                            ('copy', 'A backup model')])),
             after='This is why each app gets its own model service: its own name, limits and record.'),
    ],
    example=example('The parts, by full name', _NAMES),
    check=question(
        "team-sales's app calls the model service `prod_ai.sales.support_chat`. The platform team swaps the model "
        'behind it for a newer one. What must team-sales change in their app?',
        ['Nothing: the name stays the same', 'The model name in their code', 'The way the app signs in'],
        answer=0,
        clue='What does the app actually name when it calls?',
        why="The app calls the service's name, not the model. The platform team changes what sits behind the name, "
            'so the app keeps working with no code change.',
    ),
    angle=angle(
        pattern='Call it by name',
        text="The big idea: the gateway has three kinds of service, each with a three-part name. Apps call a model "
             "service by name, so the model behind it can change without the app changing. Your code splits a full "
             "name into its three parts, and gives back None when it isn't one.",
        say='"An app calls a model service by its [[full name|key|model::Three parts: catalog, schema and service.]], '
            'like prod_ai.sales.support_chat. Behind that name we can [[change the model|change the app|change the '
            'sign-in::The app never needs to know.]] without breaking anything."',
        classic=None,
    ),
    exercise=exercise(
        title='Split a Service Name',
        topic='platform',
        difficulty='easy',
        fn='split_name',
        prompt="""`split_name(full_name)` gets a service's full name as text, like `"prod_ai.sales.support_chat"`.

Return a dict with its three parts. For that name, return
`{"catalog": "prod_ai", "schema": "sales", "service": "support_chat"}`.

Some text isn't a full name. It may not have exactly three parts, or one part may be empty. Then return `None`.

Example: `"prod_ai.sales"` has only two parts, so the answer is `None`.""",
        pattern='Split at a separator, check the count, then name the parts.',
        target='one pass over the name',
        realworld="Platform scripts do this all the time: reading a service's full name from a request or a record, "
                  'and checking it has all three parts before granting anything on it.',
        practice=practice(
            intro="Three situations from team-sales about the gateway's parts and names.",
            explain='The gateway keeps three kinds of service: model provider services hold the link to a provider, '
                    'model services are what apps call, and MCP services hold tools. You picked the service an app '
                    'calls, kept the provider secret out of the app, and put the full name in the prod settings.',
            pattern='The right service, by its full name',
            realworld="When a team asks how to reach a model, you'll give them a model service's full name, and keep "
                      'the provider link and any tools in their own services.',
            asks=[
                ask("team-sales's support app needs to send a question to a model. Which of these names should it "
                    'call?',
                    ['prod_ai.sales.support_chat', 'prod_ai.providers.azure_openai', 'system.ai.microsoft_365'],
                    answer=0,
                    evidence=evidence('code', title='What team-sales can see in Unity Gateway', text=_NAMES),
                    clue='Which kind of service is made for an app to call?',
                    why="`prod_ai.sales.support_chat` is the model service: the name made for apps to call, with the "
                        "app's own limits and record. That is the Operational Excellence pillar: one name to call, so "
                        'the model behind it can change without breaking the app.',
                    wrong=[None, "That's the provider service: the link to Azure OpenAI that model services point at. "
                                 + 'Apps call a model service.',
                           "That's an MCP service: a set of tools for agents, not a model that answers questions."]),
                ask('team-sales is adding a summary app that uses Azure OpenAI. The provider service '
                    '`prod_ai.providers.azure_openai` already links to Azure OpenAI. Where should the Azure OpenAI '
                    'secret go?',
                    ['Nowhere: the provider service already holds the link', "In the summary app's own settings",
                     'In a second provider service, just for summary'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"We\'re adding a summary app. Where do we put the Azure OpenAI key?"'),
                    clue='How many times should the link to a provider be set up?',
                    why='The provider service holds the Azure OpenAI link once. For Azure OpenAI it signs in with a '
                        'service credential, so there is no key at all. The summary app never holds a secret. '
                        'That is the Security pillar: no copy of a secret to leak.',
                    wrong=[None, 'A key in the app\'s settings is a copy that anyone who can read them can take.',
                           'A second provider service is a second link to set up and guard, for no gain.']),
                ask('The same model service exists in two catalogs, dev_ai and prod_ai. Which name goes in the prod '
                    "app's settings?",
                    ['prod_ai.sales.support_chat', 'dev_ai.sales.support_chat', 'sales.support_chat, with no catalog'],
                    answer=0,
                    evidence=evidence('code', title='In Unity Catalog', text="""dev_ai.sales.support_chat
  the dev copy
prod_ai.sales.support_chat
  the prod copy"""),
                    clue='Which part of the name says the environment?',
                    why='The catalog, the first part of the full name, says which environment a call goes to. Grants, '
                        'limits and records all use the full name, so prod calls are counted against prod. That is the '
                        'Operational Excellence pillar.',
                    wrong=[None, 'That is the dev copy, with dev\'s limits and record. Prod calls would land there.',
                           "Without the catalog, the name can't say dev or prod. Use all three parts."]),
            ],
        ),
        starter="""def split_name(full_name):
    # your code here
    pass
""",
        solution="""def split_name(full_name):
    parts = full_name.split(".")
    if len(parts) != 3 or "" in parts:
        return None
    return {"catalog": parts[0], "schema": parts[1], "service": parts[2]}
""",
        cases=[
            case('prod_ai.sales.support_chat', expected={'catalog': 'prod_ai', 'schema': 'sales', 'service': 'support_chat'}, sample=True),
            case('system.ai.microsoft_365', expected={'catalog': 'system', 'schema': 'ai', 'service': 'microsoft_365'}),
            case('support_chat', expected=None),
            case('prod_ai.sales', expected=None),
            case('a.b.c.d', expected=None),
            case('prod_ai..support_chat', expected=None),
        ],
        guided="""def split_name(full_name):
    # Replace every ___ with real code, then run the tests.

    # Step 1: cut the name at each dot.
    parts = ___

    # Step 2: a full name has exactly three parts, none of them empty.
    if len(parts) != 3 or "" in parts:
        return None

    # Step 3: name each part.
    return {"catalog": parts[0], "schema": ___, "service": parts[2]}
""",
        fills=['full_name.split(".")', 'parts[1]'],
        concepts=[
            ['Splitting a string', '`text.split(".")` cuts a string at each dot and gives a list of the pieces.',
             '"a.b.c".split(".")   # ["a", "b", "c"]'],
            ['Counting items', '`len(parts)` is how many items a list holds.', 'len(["a", "b", "c"])   # 3'],
            ['Is it in the list?', '`"" in parts` is True when one of the pieces is empty, like two dots in a row.',
             '"" in "a..c".split(".")   # True'],
            ['Building a dict', 'Curly brackets pair each name with a value.', '{"catalog": "prod_ai", "schema": "sales"}'],
        ],
        byhand="Cut the name at each dot. If there aren't exactly three pieces, or one is empty, stop. Otherwise call "
               'them catalog, schema and service.',
        why='Grants and records only work with the full name. Catching a missing part early stops a grant landing on '
            'the wrong thing.',
    ),
)


lesson(MODULE, 'sign_in_not_keys',
    title="Sign in, don't carry keys",
    checked='2026-11-01',
    sources=[OAUTH_SP, PATS, APP_AUTH, AGENT_RUNTIME, USAGE],
    cards=[
        card('No keys, only sign-ins',
             'Every caller of the gateway signs in with **OAuth**. A person signs in as themselves. An app, job or '
             'agent signs in as its own **service principal**: an identity for a program, with no person behind it. '
             'Each one gets a **token**, a pass that works for about an hour and then renews itself. Nobody carries an API key or a personal access token (PAT), because a key works for '
             'whoever holds it, until someone changes it. A developer\'s coding agent signs in the same way, through '
             '`ug`, the Unity Gateway command-line tool, so no settings file on their computer holds a key.',
             picture=piles(pile('A key or a PAT', [('alert', 'Works for whoever holds it'),
                                                   ('clock', 'Lasts for months'),
                                                   ('x', "Can't say who is really using it")]),
                           pile('An OAuth sign-in', [('person', 'Tied to one person, app or agent'),
                                                     ('clock', 'Expires within the hour'),
                                                     ('check', 'Switched off in one place')])),
             after='The gateway records how every call signed in: the usage table says `OAUTH` or `PAT` for each one.'),
        card('Acting for a person',
             'When an agent helps Ana, it acts **on her behalf** with her token. This is called **delegated '
             'access**: Databricks Apps calls it **user authorization**, and Agent Runtime calls it **request-user '
             "authorization**. Either way the agent gets Ana's access, never more. If Ana may not read a table, "
             'neither may the agent working for her.',
             picture=steps(('person', 'Ana asks the agent', "to sum up her team's tickets"),
                           ('bot', 'The agent acts as Ana', 'with her token, for this request only'),
                           ('check', "Unity Catalog checks Ana's rights", 'including row filters and column masks, '
                                                                          'the rules that hide some rows and columns '
                                                                          'from some people'))),
        card('Every agent gets its own identity',
             'An agent that works on its own, like a nightly job, signs in as itself: its own **agent identity**, a '
             'service principal for that one agent and no other. Then its calls, its limits and its spend are its own.',
             picture=terms(('bot', 'Its own identity', 'one service principal, for one agent'),
                           ('lock', 'Its own grants', 'only what its job needs'),
                           ('gauge', 'Its own limit', "a runaway hits its own ceiling, not everyone's"),
                           ('eye', 'Its own record', 'every call names it in the usage table')),
             after="In Agent Runtime, an agent runs as its app's own service principal."),
        card('Why it matters for agents',
             'Agents read text nobody checked, and some of it can carry instructions (prompt injection). They act '
             'fast, and they can loop. So a leaked key or a runaway agent does more damage, more quickly, than a '
             'person could on their own. Signing in holds up three pillars:',
             picture=pillars('Agents that sign in',
                             pillar('Security', 'lock', 'If a token leaks, it dies within the hour'),
                             pillar('Cost Optimization', 'coin', "A stuck agent hits its own limit, not everyone's",
                                    short='Cost'),
                             pillar('Operational Excellence', 'eye', 'Every call says who made it',
                                    short='Operations'))),
    ],
    example=example('Two ways an agent can call the gateway', """With a key, in the agent's settings:
  key: a long secret, copied in
  works for: anyone who has it,
             for months

With OAuth:
  signs in as: sp-sales-agent
  for Ana:     Ana's token, Ana's access
  each token:  an hour, renewed for it"""),
    check=question(
        "An agent's OAuth token turns up in a public code repository. Why is that less dangerous than a leaked API "
        'key?',
        ['It stops working within the hour', 'Only the agent itself can use it', 'It is longer, so harder to guess'],
        answer=0,
        clue='How long does each one keep working?',
        why='An OAuth token expires within the hour, so a leak stops on its own. A leaked API key keeps working for '
            'anyone who has it, until someone notices and changes it.',
    ),
    angle=angle(
        pattern='Short-lived sign-ins, one identity each',
        text="The big idea: nobody carries a long-lived key. Every caller signs in with OAuth and gets a token that "
             "expires within the hour. An agent working for a person acts with that person's access. Each agent has "
             "its own identity, so its calls, limits and spend are its own. Your code lists who still signs in with "
             "a PAT: that list has to reach zero before PATs are switched off.",
        say='"Our agents [[sign in with OAuth|keep API keys|share one login::A short-lived token, tied to who is '
            'calling.]], and each has [[its own identity|a shared account|an admin login::One service principal for '
            'one agent.]]. A leaked token stops within the hour, and a runaway agent only uses up its own limit."',
        classic=None,
    ),
    exercise=exercise(
        title='Who Still Uses a PAT?',
        topic='platform',
        difficulty='easy',
        fn='still_on_pats',
        prompt="""`still_on_pats(rows)` gets rows from the gateway's usage table, one row for each request, like
`{"requester": "sp-sales-agent", "auth_mode": "OAUTH"}`.

`requester` is who sent the request. `auth_mode` says how it signed in: `"OAUTH"` or `"PAT"`.

Return the requesters that sent at least one request with a PAT. List each one once, in alphabetical order. Return
`[]` if every request used OAuth.

Example: two PAT rows from `old-report-job` and one OAuth row from `sp-sales-agent` give `["old-report-job"]`.""",
        pattern='Keep the items that match, with no repeats, then put them in order.',
        target='one look at each row',
        realworld='This is the list behind switching PATs off: the usage table records how every request signed in, '
                  'and each name on the list has to move to OAuth first.',
        practice=practice(
            intro='Three situations about how apps and agents sign in to the gateway.',
            explain="Every caller signs in with OAuth: short-lived tokens tied to who is calling. You offered a "
                    "sign-in instead of a key, moved the last PAT user to OAuth before the switch-off, and saw why an "
                    "agent working for a person should use that person's access.",
            pattern='Sign in as yourself, for an hour',
            realworld="When a team asks for an API key for their agent, you'll offer an OAuth sign-in instead: its own "
                      "identity for work it does alone, and the person's own access when someone is behind the request.",
            asks=[
                ask('A developer asks for an API key to put in their agent\'s settings, so it can call the model '
                    'service. What do you offer instead?',
                    ["An OAuth sign-in as the agent's own identity", 'A key that never expires, kept safe',
                     'A personal login of yours to share'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"Our agent needs to call the model service. Can you give us an API key to '
                                           'put in its settings?"'),
                    clue="Which one expires on its own and says who's calling?",
                    why="OAuth gives the agent tokens tied to its own identity, renewed for it about every hour. If one "
                        'leaks, it stops working within the hour, and there is no key to change. That is the Security '
                        'pillar.',
                    wrong=[None, "A key that never expires is the riskiest kind: it works for whoever finds it.",
                           "A shared login hides who really acted, and gives the agent all of that person's access."]),
                ask('PATs will be switched off for the workspace next week. The usage table shows old-report-job still '
                    'signs in with a PAT. What do you do first?',
                    ['Move old-report-job to OAuth before the switch', 'Switch PATs off now, and fix what breaks',
                     'Give old-report-job a PAT that lasts longer'],
                    answer=0,
                    evidence=evidence('code', title='The usage table, last week', text="""requester         auth_mode
sp-sales-agent    OAUTH
old-report-job    PAT
ana@example.com   OAUTH"""),
                    clue='What happens to the report job on the day PATs go off?',
                    why='Switching PATs off stops every caller that still uses one, so the report job would fail that '
                        'day. Move it to OAuth as its own service principal first, then check the usage table shows no '
                        'PAT rows. That is the Operational Excellence pillar.',
                    wrong=[None, 'Then the report fails on the day, and its users find out first.',
                           'A longer PAT goes the wrong way, and it stops working on switch-off day anyway.']),
                ask('The helpdesk agent reads tickets for whoever asks, and it runs as an admin account. What is the '
                    'risk?',
                    ["It can show people data they mustn't see", 'Admin accounts make the agent answer slower',
                     'None: an admin is trusted with everything'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"Our helpdesk agent reads tickets for whoever asks. It runs as an admin '
                                           'account so it can always see everything."'),
                    clue='Whose access should it use when Ana asks?',
                    why="As an admin, the agent can hand Ana tickets she isn't allowed to see. With user authorization "
                        "it acts with her access. Unity Catalog's row filters and column masks, the rules that hide "
                        'some rows and columns from some people, still apply. That is the Security pillar.',
                    wrong=[None, "Speed isn't the problem. Who can see what is.",
                           "Trusting the admin doesn't make it right to show Ana the admin's data."]),
            ],
        ),
        starter="""def still_on_pats(rows):
    # your code here
    pass
""",
        solution="""def still_on_pats(rows):
    names = set()
    for row in rows:
        if row["auth_mode"] == "PAT":
            names.add(row["requester"])
    return sorted(names)
""",
        cases=[
            case([{'requester': 'sp-sales-agent', 'auth_mode': 'OAUTH'},
                  {'requester': 'old-report-job', 'auth_mode': 'PAT'},
                  {'requester': 'ana@example.com', 'auth_mode': 'PAT'},
                  {'requester': 'old-report-job', 'auth_mode': 'PAT'}],
                 expected=['ana@example.com', 'old-report-job'], sample=True),
            case([], expected=[]),
            case([{'requester': 'sp-sales-agent', 'auth_mode': 'OAUTH'}], expected=[]),
            case([{'requester': 'ben@example.com', 'auth_mode': 'OAUTH'},
                  {'requester': 'ben@example.com', 'auth_mode': 'PAT'}], expected=['ben@example.com']),
            case([{'requester': 'z-job', 'auth_mode': 'PAT'}, {'requester': 'a-job', 'auth_mode': 'PAT'}],
                 expected=['a-job', 'z-job']),
        ],
        guided="""def still_on_pats(rows):
    # Replace every ___ with real code, then run the tests.

    names = set()
    for row in rows:
        # Step 1: did this request sign in with a PAT?
        if ___:
            # Step 2: remember who sent it (a set keeps each name once).
            ___

    # Step 3: alphabetical order.
    return sorted(names)
""",
        fills=['row["auth_mode"] == "PAT"', 'names.add(row["requester"])'],
        concepts=[
            ['A set', 'A set holds each value once, however many times you add it.',
             """names = set()
names.add("a")
names.add("a")
names   # {"a"}"""],
            ['Comparing text', '`a == b` is True when the two strings are exactly the same, capitals included.',
             '"PAT" == "PAT"   # True'],
            ['Putting names in order', '`sorted(names)` gives a list in alphabetical order, even from a set.',
             'sorted({"b", "a"})   # ["a", "b"]'],
        ],
        byhand='Go down the rows. For each one that says PAT, write its requester down, unless it is already on your '
               'list. Then sort the list.',
        why='Switching PATs off breaks whoever still uses them. The list says exactly who to move to OAuth first, so '
            'the switch breaks nothing.',
    ),
)


lesson(MODULE, 'who_may_call',
    title='Who may call it',
    checked='2026-11-01',
    sources=[GOVERN_SERVICES, CONCEPTS, MIGRATE],
    cards=[
        card('Three grants on the way down',
             'A **grant** is a permission given to someone: the right to use a catalog, a schema or a service. To call a '
             'service, an app needs the same three grants as for reading a table, one at every level on the way down. '
             'Miss one, and the gateway answers **PERMISSION_DENIED**.',
             picture=steps(('layers', 'USE CATALOG', 'on the catalog: prod_ai'),
                           ('layers', 'USE SCHEMA', 'on the schema: prod_ai.sales'),
                           ('check', 'EXECUTE', 'on the service itself: prod_ai.sales.support_chat'))),
        card('Give grants to groups and apps, not people',
             'An app calls as its own **service principal**, signed in with OAuth. People get access through groups, '
             'so one change covers everyone in the team.',
             picture=piles(pile('Grant to', [('people', 'A group: grp-sales-dev-users'),
                                                 ('bot', "An app's identity: sp-sales-chat-prod")]),
                           pile('Not to', [('person', 'One person, by name'),
                                           ('alert', 'Everyone in the company')]))),
        card('Calling is not managing',
             "Three privileges, three jobs. Callers get EXECUTE and nothing more, and the platform team keeps MANAGE, "
             "so nobody can quietly loosen a service's limits or guardrails.",
             picture=terms(('check', 'EXECUTE', 'call the service'),
                           ('eye', 'READ METADATA', 'see its settings'),
                           ('lock', 'MANAGE', 'change it, and give access to others'))),
        card('Two traps',
             'Two things catch teams out:',
             picture=sortby('Does it give the right access?',
                            sortrow('CAN_QUERY on an old Model Serving endpoint', 'Not to a Unity Gateway service: that needs EXECUTE', 'No', icon='x'),
                            sortrow('Being in "account users"', 'Yes, to everything in system.ai, until someone removes that wide grant', 'Too much', icon='alert'))),
    ],
    example=example('The grants for one service', """ON CATALOG prod_ai
  USE CATALOG  -> grp-sales-dev-users,
                  sp-sales-chat-prod
ON SCHEMA prod_ai.sales
  USE SCHEMA   -> grp-sales-dev-users,
                  sp-sales-chat-prod
ON SERVICE prod_ai.sales.support_chat
  EXECUTE      -> grp-sales-dev-users,
                  sp-sales-chat-prod
  MANAGE       -> grp-platform-admins"""),
    check=question(
        'The support app signs in as sp-sales-chat-prod. It has `USE CATALOG` on prod_ai and `USE SCHEMA` on '
        'prod_ai.sales. It still gets PERMISSION_DENIED calling `prod_ai.sales.support_chat`. What is missing?',
        ['EXECUTE on the service', 'MANAGE on the service', 'SELECT on the schema'],
        answer=0,
        clue='Count the levels on the way down: catalog, schema, then what?',
        why='The third grant is `EXECUTE` on the service itself, the right to call it. `MANAGE` would also let the app '
            'change the service and its limits, which a caller should never be able to do.',
    ),
    angle=angle(
        pattern='Three grants, given to groups and apps',
        text="The big idea: calling a service needs a grant at each level, the catalog, the schema and the service "
             "itself, and callers get EXECUTE, nothing more. Your code works out which of the three grants a principal "
             "is missing, so a PERMISSION_DENIED ticket gets a precise answer.",
        say='"To call a model service, an app needs [[three grants|one grant|two grants::One for each part of the '
            'name.]]. I give them to [[groups and service principals|single people|everyone::So access changes in one '
            'place.]]. Callers never get MANAGE, the right to change the service."',
        classic=None,
    ),
    exercise=exercise(
        title='Find the Missing Grant',
        topic='platform',
        difficulty='easy',
        fn='missing_grants',
        prompt="""`missing_grants(service, principal, grants)` gets a service's full name, like
`"prod_ai.sales.support_chat"`, the name of a caller, and a list of grants. To call the service, the caller needs
three privileges, each on its own level:

- `USE CATALOG` on the catalog, like `"prod_ai"`
- `USE SCHEMA` on the schema, like `"prod_ai.sales"`
- `EXECUTE` on the service, like `"prod_ai.sales.support_chat"`

`grants` is a list of dicts like `{"privilege": "USE SCHEMA", "on": "prod_ai.sales", "to": "sp-sales-chat-prod"}`.
Only count grants given straight to `principal`.

Return the privileges `principal` is missing, in the order above, or `[]` if it has all three.

Example: `sp-sales-chat-prod` has only the `USE CATALOG` and `USE SCHEMA` grants, so the answer is `["EXECUTE"]`.""",
        pattern="For each thing you need, look through what you have, and keep the ones you never find.",
        target='one look at each row for each grant',
        realworld='This is the first check on a PERMISSION_DENIED ticket: which of the three grants the caller lacks, so '
                  'the fix is one precise grant instead of a guess.',
        practice=practice(
            intro='Three tickets from team-sales about access. For each one, find the right fix.',
            explain='Calling a service needs three grants: USE CATALOG, USE SCHEMA and EXECUTE on the service. You '
                    'turned down MANAGE for a caller, moved a grant from one person to a group, and closed a wide '
                    'grant that let everyone in.',
            pattern='Find the missing grant, give the least',
            realworld="When a PERMISSION_DENIED ticket comes in, you'll check the three grants for the app's service "
                      'principal first, and grant only EXECUTE, to a group or an app, never MANAGE to a caller.',
            asks=[
                ask('team-sales asks for `MANAGE` on the support service for their app, so it never gets '
                    'PERMISSION_DENIED again. What do you grant the app?',
                    ['EXECUTE, plus USE CATALOG and USE SCHEMA', 'MANAGE, as they asked, to be safe',
                     'MANAGE now, and take it back next month'],
                    answer=0,
                    evidence=evidence('claim', who='A developer on team-sales',
                                      text='"Our app keeps getting PERMISSION_DENIED. Can you give sp-sales-chat-prod '
                                           'MANAGE on prod_ai.sales.support_chat, so it never happens again?"'),
                    clue='Which privilege lets the app call, and which lets it change the service?',
                    why='Calling needs `EXECUTE` and the two grants above it, nothing more. With `MANAGE`, the app could '
                        'change the service, its limits and guardrails included, and give access to others. That is '
                        'the Security pillar.',
                    wrong=[None, 'MANAGE is the right to change the service. A caller only needs to call it.',
                           'For a month, the app could loosen its own limits. Give the least it needs from the start.']),
                ask('Three grants of `EXECUTE` let callers use prod_ai.sales.support_chat. One goes to Ana by name. '
                    'Which grant would you change?',
                    ['The one to ana@example.com: use a group', 'The one to sp-sales-chat-prod',
                     'The one to grp-sales-dev-users'],
                    answer=0,
                    evidence=evidence('code', title='Who can call prod_ai.sales.support_chat', text="""EXECUTE  -> grp-sales-dev-users
EXECUTE  -> sp-sales-chat-prod
EXECUTE  -> ana@example.com"""),
                    clue='Which one breaks the "groups and apps" rule?',
                    why="Ana should get access through her team's group. When she moves team, taking her out of the "
                        'group removes her access. A grant to her by name gets forgotten, and she keeps it. '
                        'That is the Security pillar.',
                    wrong=[None, "That's the app's own identity: exactly what an app should use.",
                           "Granting to a team's group is the right way for people."]),
                ask("A security reviewer finds that everyone in the company can call every model and tool in "
                    "`system.ai`, Databricks' own services. Nobody chose that. What should the platform team do?",
                    ['Remove the wide grant, then approve models one by one', "Nothing: Databricks' own models are always safe",
                     'Ask every team to stop using system.ai'],
                    answer=0,
                    evidence=evidence('claim', who='A security reviewer',
                                      text='"Anyone in the company can call every model and tool in system.ai. Did '
                                           'anyone decide that?"'),
                    clue='Who has the grant right now, and who chose that?',
                    why='By default, every account user can call everything in `system.ai`. Remove that wide grant, then '
                        'grant the approved services to the groups that need them, so each use has a chosen owner. '
                        'That is the Security pillar.',
                    wrong=[None, 'Safe or not, nobody chose who may use them, or how much.',
                           'Asking changes nothing: the grant still lets everyone in. Change the grant.']),
            ],
        ),
        starter="""def missing_grants(service, principal, grants):
    # your code here
    pass
""",
        solution="""def missing_grants(service, principal, grants):
    catalog, schema, name = service.split(".")
    needed = [("USE CATALOG", catalog), ("USE SCHEMA", catalog + "." + schema), ("EXECUTE", service)]
    missing = []
    for privilege, on in needed:
        found = False
        for g in grants:
            if g["privilege"] == privilege and g["on"] == on and g["to"] == principal:
                found = True
        if not found:
            missing.append(privilege)
    return missing
""",
        cases=[
            case('prod_ai.sales.support_chat', 'sp-sales-chat-prod',
                 [{'privilege': 'USE CATALOG', 'on': 'prod_ai', 'to': 'sp-sales-chat-prod'},
                  {'privilege': 'USE SCHEMA', 'on': 'prod_ai.sales', 'to': 'sp-sales-chat-prod'}],
                 expected=['EXECUTE'], sample=True),
            case('prod_ai.sales.support_chat', 'sp-sales-chat-prod',
                 [{'privilege': 'USE CATALOG', 'on': 'prod_ai', 'to': 'sp-sales-chat-prod'},
                  {'privilege': 'USE SCHEMA', 'on': 'prod_ai.sales', 'to': 'sp-sales-chat-prod'},
                  {'privilege': 'EXECUTE', 'on': 'prod_ai.sales.support_chat', 'to': 'sp-sales-chat-prod'}],
                 expected=[]),
            case('prod_ai.sales.support_chat', 'sp-sales-chat-prod', [], expected=['USE CATALOG', 'USE SCHEMA', 'EXECUTE']),
            case('prod_ai.sales.support_chat', 'sp-sales-chat-prod',
                 [{'privilege': 'USE CATALOG', 'on': 'prod_ai', 'to': 'grp-sales-dev-users'},
                  {'privilege': 'USE SCHEMA', 'on': 'prod_ai.sales', 'to': 'grp-sales-dev-users'},
                  {'privilege': 'EXECUTE', 'on': 'prod_ai.sales.support_chat', 'to': 'grp-sales-dev-users'}],
                 expected=['USE CATALOG', 'USE SCHEMA', 'EXECUTE']),
            case('prod_ai.sales.support_chat', 'sp-sales-chat-prod',
                 [{'privilege': 'USE CATALOG', 'on': 'prod_ai', 'to': 'sp-sales-chat-prod'},
                  {'privilege': 'USE SCHEMA', 'on': 'prod_ai.hr', 'to': 'sp-sales-chat-prod'},
                  {'privilege': 'EXECUTE', 'on': 'prod_ai.sales.support_chat', 'to': 'sp-sales-chat-prod'}],
                 expected=['USE SCHEMA']),
        ],
        guided="""def missing_grants(service, principal, grants):
    # Replace every ___ with real code, then run the tests.

    catalog, schema, name = service.split(".")
    needed = [("USE CATALOG", catalog), ("USE SCHEMA", catalog + "." + schema), ("EXECUTE", service)]
    missing = []
    for privilege, on in needed:
        found = False
        for g in grants:
            # Step 1: this grant gives the privilege, on the right object, to this principal.
            if g["privilege"] == privilege and g["on"] == on and ___:
                found = True
        # Step 2: no grant gave it.
        if ___:
            missing.append(privilege)
    return missing
""",
        fills=['g["to"] == principal', 'not found'],
        concepts=[
            ['Unpacking', 'Three names on the left take the three pieces of a list in order.',
             'a, b, c = "x.y.z".split(".")   # a is "x"'],
            ['A loop inside a loop', 'For each grant you need, the inner loop looks at every row.',
             """for size in ["S", "M"]:
    for colour in ["red", "blue"]:
        print(size, colour)"""],
            ['A flag variable', "A True/False variable that remembers whether you've found something.",
             """found = False
for item in ["tea", "cake"]:
    if item == "cake":
        found = True"""],
        ],
        byhand='For each of the three grants you need, look down the list for one with that privilege, on that object, '
               'to this principal. Write down every one you never find.',
        why='A PERMISSION_DENIED ticket is almost always one missing grant. Naming it exactly means the fix is one '
            'precise grant, not a wider one "to be safe".',
    ),
)


_LIMITS = """service:          100,000
default per user:  20,000
grp-sales:         50,000  (shared)
sp-sales-batch:    60,000  (its own)"""


lesson(MODULE, 'fair_limits',
    title='Fair limits',
    checked='2026-11-01',
    sources=[RATE_LIMITS, USAGE],
    cards=[
        card('What a 429 means',
             'Error **429** means "too many requests": a limit was reached for this minute. Nothing is broken. The '
             'right move is to wait a little longer each time, then try again. The usage table, the gateway\'s record '
             'of every call, shows the 429s for each caller.',
             picture=steps(('alert', '429', 'a limit was reached this minute'),
                           ('clock', 'Wait', '1 second, then 2, then 4'),
                           ('reset', 'Try again', 'limits refill every minute'))),
        card('A limit of its own',
             'A service can have limits at four levels. The service limit is one ceiling for everyone. Each user '
             'gets a default slice. A group shares one pool. A **named** user or service principal can also get a '
             "limit of its own, used instead of its group's. Nothing goes above the service limit.",
             picture=terms(('cloud', 'The service', "one ceiling for everyone: when it's full, everyone waits"),
                           ('person', 'A named user or app', "its own limit, used instead of its group's"),
                           ('people', 'A group', 'one shared pool for a whole team'),
                           ('listcheck', 'The default', "each person's own slice when nothing else is set")),
             after='Give every agent its own limit, so a runaway loop stops at its own ceiling.'),
        card('Requests and tokens',
             'Model services can limit requests a minute and tokens a minute, and whichever runs out first stops you. '
             'A token here is a short piece of text, about four letters, not the sign-in token. MCP services only '
             'count tool calls a minute.',
             picture=piles(pile('Model service', [('chat', 'Requests a minute'), ('coin', 'Tokens a minute')]),
                           pile('MCP service', [('bot', 'Tool calls a minute')]))),
    ],
    example=example('Limits on one service (tokens a minute)', _LIMITS),
    check=question(
        'The support app gets 429 errors, "too many requests", for a few minutes every day at 2 pm. What do you '
        'check first?',
        ['Its traffic around 2 pm, in the usage table', 'Whether its sign-in expired at 2 pm',
         'Whether the model behind it changed'],
        answer=0,
        clue='A 429 means a limit was reached. Where would you see how busy 2 pm is?',
        why="Start with the traffic. The usage table shows the app's requests and tokens around 2 pm. From that you can "
            'tell a daily burst from a limit that is set too low.',
    ),
    angle=angle(
        pattern='Find the limit, then wait and retry',
        text="The big idea: a 429 is a limit doing its job. Work out which limit applied, a named app's own, its "
             "group's or the default, all under the service limit, and make the app wait longer each time before "
             "trying again. Your code works out which limit applies to a caller.",
        say='"A 429 means a [[limit was reached|model crashed|sign-in expired::Too many requests this minute.]], not '
            'that something broke. The usage table shows which caller hit it, and the app should [[wait and '
            'retry|give up|retry at once::Give the limit time to refill.]], a little longer each time."',
        classic=None,
    ),
    exercise=exercise(
        title='Which Limit Applies?',
        topic='platform',
        difficulty='easy',
        fn='limit_for',
        prompt="""`limit_for(principal, group, limits)` gets a caller's name, the group it is in, and a service's
limits. `limits` holds the limits in tokens a minute:

- `"service"`: the ceiling for everyone, like `100000`
- `"user_default"`: each person's own slice, like `20000`
- `"groups"`: each group's shared limit, like `{"grp-sales": 50000}`
- `"own"`: limits for named users or apps, like `{"sp-sales-batch": 60000}`

`group` is `None` when the caller is in no group. Return the limit that applies to the caller:

1. its own limit, if it has one
2. otherwise its group's limit, if the group has one
3. otherwise the default

Whichever it is, it can't be more than the service limit.

Example: `"sp-sales-batch"` in `"grp-sales"` has its own `60000`, so the answer is `60000`.""",
        pattern='Try the most specific rule first, fall back step by step, then cap it.',
        target='a few lookups, no loop',
        realworld="This is the question behind every 429 ticket: which limit did this caller actually have? Knowing "
                  'it tells you whether to raise a limit or change when the app sends its requests.',
        practice=practice(
            intro='Three situations about limits from team-sales.',
            explain="A 429 means a limit was reached. You made the app wait before retrying, worked out which limit "
                    "applies, and gave a busy batch job a limit of its own. A named app's own limit beats its group's, "
                    "a group's beats the default, and the service limit caps them all.",
            pattern='Which slice, under which ceiling',
            realworld="When an app reports 429s, you'll find its traffic in the usage table, decide whether its limit "
                      "or its timing needs changing, and check the app waits longer before each retry.",
            asks=[
                ask('The support app gets this 429 error, "too many requests". What should the app do next?',
                    ['Wait, then retry with longer gaps', 'Retry straight away until it works', "Switch to another team's service"],
                    answer=0,
                    evidence=evidence('code', title='The error team-sales sees', text="""HTTP 429 Too Many Requests
The rate limit for this service was reached.
Try again later."""),
                    clue='Retrying at once just adds to the crowd.',
                    why='Waiting longer after each try gives the limit time to refill. It also stops many apps retrying '
                        'at once and making it worse. That is the Reliability pillar: the app slows down instead of '
                        'failing.',
                    wrong=[None, 'Instant retries hit the same full limit, and make it worse for everyone.',
                           "Another team's service has its own owners and limits. Use your own, and wait."]),
                ask('Ana is in grp-sales and has no limit of her own. Which limit applies to her calls?',
                    ["grp-sales's shared 50,000", 'The default 20,000 for each user', "The service's 100,000"],
                    answer=0,
                    evidence=evidence('code', title='Limits on prod_ai.sales.support_chat (tokens a minute)', text=_LIMITS),
                    clue='She has no limit of her own. What is the next most specific one?',
                    why="With no limit of her own, Ana falls under her group's: one pool of 50,000 that she shares with "
                        'all of grp-sales. That is the Reliability pillar: when the group is busy, she can get 429s '
                        'even if she sent little.',
                    wrong=[None, 'The default is only for callers with no other limit, and her group has one.',
                           'The service limit is the ceiling for everyone, not her share.']),
                ask('The service allows 100,000 tokens a minute. Every night the batch job uses 90,000 of them, and the '
                    'chat app gets 429s until morning. What fixes it?',
                    ['Give the batch job its own lower limit', 'Give the chat app a higher limit of its own',
                     'Turn off the service limit'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"Every night our batch job uses 90,000 tokens a minute, and our chat app '
                                           'gets 429s until morning."'),
                    clue='One caller is taking most of the shared space.',
                    why="A limit of the batch job's own, well below the service's, leaves room for the chat app. The "
                        'job only runs a little slower. That is the Reliability pillar.',
                    wrong=[None, "The chat app can't use more while the batch job fills the service.",
                           'Without it, one caller could take everything.']),
            ],
        ),
        starter="""def limit_for(principal, group, limits):
    # your code here
    pass
""",
        solution="""def limit_for(principal, group, limits):
    own = limits["own"].get(principal)
    if own is not None:
        chosen = own
    elif group in limits["groups"]:
        chosen = limits["groups"][group]
    else:
        chosen = limits["user_default"]
    return min(chosen, limits["service"])
""",
        cases=[
            case('sp-sales-batch', 'grp-sales',
                 {'service': 100000, 'user_default': 20000, 'groups': {'grp-sales': 50000}, 'own': {'sp-sales-batch': 60000}},
                 expected=60000, sample=True),
            case('ana', 'grp-sales',
                 {'service': 100000, 'user_default': 20000, 'groups': {'grp-sales': 50000}, 'own': {'sp-sales-batch': 60000}},
                 expected=50000),
            case('ben', None,
                 {'service': 100000, 'user_default': 20000, 'groups': {'grp-sales': 50000}, 'own': {}},
                 expected=20000),
            case('sp-big', None,
                 {'service': 100000, 'user_default': 20000, 'groups': {}, 'own': {'sp-big': 150000}},
                 expected=100000),
            case('cara', 'grp-hr',
                 {'service': 100000, 'user_default': 20000, 'groups': {'grp-sales': 50000}, 'own': {}},
                 expected=20000),
        ],
        guided="""def limit_for(principal, group, limits):
    # Replace every ___ with real code, then run the tests.

    own = limits["own"].get(principal)
    # Step 1: a named user or app with a limit of its own.
    if ___:
        chosen = own
    elif group in limits["groups"]:
        chosen = limits["groups"][group]
    else:
        chosen = limits["user_default"]

    # Step 2: nothing can go above the service limit.
    return ___
""",
        fills=['own is not None', 'min(chosen, limits["service"])'],
        concepts=[
            ['dict.get', '`d.get(key)` gives the value, or `None` when the key is missing, instead of an error.',
             '{"a": 1}.get("b")   # None'],
            ['if, elif, else', 'Python tries each test in order and runs the first one that is True.',
             """if x > 10:
    size = "big"
elif x > 5:
    size = "medium"
else:
    size = "small\""""],
            ['The smaller of two', '`min(a, b)` gives the smaller number, which works as a cap.', 'min(150000, 100000)   # 100000'],
        ],
        byhand="Look for the caller's own limit. If there isn't one, use its group's, and if there isn't one of those, "
               'use the default. Then, if that is above the service limit, use the service limit.',
        why='Most 429 tickets come down to one question: which limit did this caller really have? With that answer you '
            'know whether to change a limit or change when the app sends its requests.',
    ),
)


lesson(MODULE, 'model_fails',
    title='When a model fails',
    checked='2026-11-01',
    sources=[ROUTING, MODEL_SERVICES, USAGE],
    cards=[
        card('A backup model',
             'Providers have bad days: an outage, or no capacity left. A **fallback** is a backup model the gateway '
             'tries when the main one fails, in the order you set, so the app keeps answering.',
             picture=steps(('chat', 'The main model', 'answers as usual'),
                           ('alert', 'It fails', 'an outage, or no capacity left'),
                           ('reset', 'The backup answers', 'the next model in the fallback list'))),
        card('Test the backup too',
             'A fallback is a different model, sometimes at another provider, and it only answers when something has '
             'already gone wrong. So it gets the same tests as the main model, before anyone needs it.',
             picture=steps(('listcheck', 'Before go-live', 'the fallback runs the same test set'),
                           ('alert', 'The main model fails', 'an outage, or too many errors'),
                           ('check', 'The fallback answers', 'and you already know it is good enough')),
             after='The same goes for anything behind the name: a new model version, new code around it, or a new '
                   'place it runs. If it changed, test it again.'),
        card('Try a new model on a slice',
             'A new model goes live a slice at a time. A **traffic split** sends 1 request in 10 to it and keeps 9 in '
             '10 on the model you trust, while you compare the two. This is called a **canary** release. Then you '
             'move more. The shares always add up to 100.',
             picture=piles(pile('90 in 100', [('check', 'The trusted model')]),
                           pile('10 in 100', [('sparkle', 'The new model, watched closely')]))),
        card('Rolling back',
             'If the new model does worse, set the split back to 100 for the old one in the gateway. That is one '
             'change, with nothing to change in the app.',
             picture=steps(('alert', 'Worse answers', 'from the new model'),
                           ('reset', 'Set the split back', '100 for the trusted model'),
                           ('check', 'Done', 'no change to the app')),
             after='Write the rollback down before the split starts, and try it once.'),
    ],
    example=example('One model service, three destinations', """main:
  trusted model     90
  new model         10
fallback, in order:
  model at another provider"""),
    check=question(
        "A traffic split sends 1 in 10 of support_chat's requests to a new model. Its answers are worse than the old "
        "model's. What is the quickest safe fix?",
        ['Set the split back to 100 on the old model', 'Ask team-sales to change their code', 'Delete the new model at the provider'],
        answer=0,
        clue='Which change happens in one place, with no change to the app?',
        why='Setting the split back is one change in the gateway, so every request goes to the trusted model again at '
            'once. The app only names the service, so its code needs no change.',
    ),
    angle=angle(
        pattern='A backup, a slice, a way back',
        text="The big idea: plan for failure and for change. A fallback keeps the app answering when a model fails, "
             "and it gets the same tests as the main model. A traffic split tries a new model on a slice first. "
             "Setting the split back is the rollback. Your code checks a split before it goes live.",
        say='"For every production model service I set a [[fallback|second sign-in|bigger limit::What the gateway tries '
            'when the main model fails.]], and I try a new model on [[a slice of requests|every request|a '
            'weekend::1 in 10, next to the trusted model.]] first, so rolling back is one change."',
        classic=None,
    ),
    exercise=exercise(
        title='Check a Traffic Split',
        topic='platform',
        difficulty='easy',
        fn='check_split',
        prompt="""`check_split(destinations)` gets the destinations of a model service's traffic split: the models
that share its requests, not its fallbacks. Each one is a dict like `{"name": "trusted", "percent": 90}`.

Check two rules, and add a message for each one that fails:

- the percents add up to 100: otherwise `"percentages must add up to 100"`
- there are at most 5 destinations: otherwise `"at most 5 destinations"`

Return the messages in that order, or `[]` if both pass.

Example: `trusted` at 90 and `new` at 20 add up to 110, so the answer is `["percentages must add up to 100"]`.""",
        pattern='Add up as you go, then check each rule and report every failure.',
        target='one pass over the destinations',
        realworld='This is the check before a split goes live: shares that add up, and no more destinations than the '
                  'gateway allows, so the change is accepted the first time.',
        practice=practice(
            intro='Three situations about models failing and changing.',
            explain='A fallback keeps an app answering when its main model fails, and a split tries a new model on a '
                    'slice of requests first. You picked the backup for an outage, a slice for a launch, and had the '
                    'rollback written down before the canary started.',
            pattern='Plan the backup, the slice and the way back',
            realworld="Before a model goes live, you'll check it has a tested fallback, start any new model on a small "
                      'slice, and write down the rollback so anyone can do it.',
            asks=[
                ask('The support app showed "Sorry, something went wrong" while its provider had an outage. What would '
                    'have kept it answering?',
                    ['A fallback to a model at another provider', 'A higher limit on calls a minute',
                     'A record of every failed call'],
                    answer=0,
                    evidence=evidence('code', title='What the support app showed', text="""12:04  "Sorry, something went wrong."
12:05  "Sorry, something went wrong."

Provider status: outage in your region"""),
                    clue='The main model is down. What else could answer?',
                    why='A fallback sends each request to the next model in its list when the main one fails. Users '
                        'still get answers while the provider is down. That is the Reliability pillar.',
                    wrong=[None, 'Limits control how much, not what happens when a model is down.',
                           "A record shows the failures afterwards. It doesn't answer anyone."]),
                ask("The new model scored better in team-sales's tests. They want to move every request to it "
                    'tomorrow. What is the safer plan?',
                    ['Start with a slice of requests and compare', 'Switch everyone, then check next week',
                     'Ask each user which model they want'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"The new model scored better in our tests. Let\'s switch everyone to it '
                                           'tomorrow."'),
                    clue='Tests are a start. What about real requests?',
                    why='Real requests are different from any test set. A canary slice, like 1 in 10, tests the new '
                        'model on real use, and most people stay on the trusted one. That is the Reliability '
                        'pillar: if it does worse, few people notice.',
                    wrong=[None, "If it's worse, everyone has a bad week.",
                           "Which model answers is the platform's choice, not each user's."]),
                ask('team-sales starts a canary tomorrow: 1 in 10 requests to a new model. What should be ready '
                    'before it starts?',
                    ['A written rollback, tried once', 'The old model deleted, to save money',
                     'The fallback switched off for the test'],
                    answer=0,
                    evidence=evidence('code', title='support_chat, from tomorrow', text="""main:     trusted model   90
          new model       10
fallback: model at another provider"""),
                    clue='If the new model goes wrong at night, what does the person on call need?',
                    why='If the new model does worse, whoever is on call can set the split back in one change, '
                        'without guessing. Trying it once proves it works. That is the Operational Excellence pillar.',
                    wrong=[None, 'With the old model gone, there is nothing to roll back to.',
                           'The fallback still guards against an outage during the canary. Keep it on.']),
            ],
        ),
        starter="""def check_split(destinations):
    # your code here
    pass
""",
        solution="""def check_split(destinations):
    problems = []
    total = 0
    for d in destinations:
        total += d["percent"]
    if total != 100:
        problems.append("percentages must add up to 100")
    if len(destinations) > 5:
        problems.append("at most 5 destinations")
    return problems
""",
        cases=[
            case([{'name': 'trusted', 'percent': 90}, {'name': 'new', 'percent': 10}], expected=[], sample=True),
            case([{'name': 'trusted', 'percent': 90}, {'name': 'new', 'percent': 20}],
                 expected=['percentages must add up to 100']),
            case([{'name': 'only', 'percent': 100}], expected=[]),
            case([], expected=['percentages must add up to 100']),
            case([{'name': f'm{i}', 'percent': 20} for i in range(5)], expected=[]),
            case([{'name': f'm{i}', 'percent': 20} for i in range(4)]
                 + [{'name': 'm4', 'percent': 10}, {'name': 'm5', 'percent': 10}],
                 expected=['at most 5 destinations']),
            case([{'name': f'm{i}', 'percent': 20} for i in range(6)],
                 expected=['percentages must add up to 100', 'at most 5 destinations']),
        ],
        guided="""def check_split(destinations):
    # Replace every ___ with real code, then run the tests.

    problems = []
    total = 0
    for d in destinations:
        # Step 1: add this destination's share to the total.
        ___

    if total != 100:
        problems.append("percentages must add up to 100")

    # Step 2: no more than 5 destinations.
    if ___:
        problems.append("at most 5 destinations")
    return problems
""",
        fills=['total += d["percent"]', 'len(destinations) > 5'],
        concepts=[
            ['Adding up as you go', '`total += x` adds x to total each time round.',
             """total = 0
for n in [90, 10]:
    total += n   # 90, then 100"""],
            ['Not equal', '`a != b` is True when a and b are different.', '110 != 100   # True'],
            ['Counting items', '`len(items)` is how many items a list holds.', 'len([1, 2, 3])   # 3'],
        ],
        byhand="Add up every percent. If it isn't exactly 100, note that. Then count the destinations. If there are "
               'more than 5, note that too.',
        why='A split that is rejected, or sends more traffic than you meant to a new model, is exactly the surprise a '
            'careful rollout is meant to avoid.',
    ),
)


lesson(MODULE, 'who_spent_what',
    title='Who spent what',
    checked='2026-11-01',
    sources=[USAGE, BUDGETS, MODEL_SERVICES],
    cards=[
        card('The usage table',
             "Unity Gateway records every request in a system table, `system.ai_gateway.usage`: who called, which "
             "service, how many tokens and how long it took. A token is a short piece of text that the provider "
             "charges for. Finance's questions start here.",
             picture=terms(('person', 'Who', 'the user, app or agent that called'),
                           ('chat', 'Which service', 'its full three-part name'),
                           ('coin', 'How much', 'tokens in and out'),
                           ('clock', 'How long', 'the time each request took'))),
        card('Tags say whose spend it is',
             'Tags turn rows into answers. Put `team`, `app` and `env` tags on every service, and let an app add '
             '**request tags**, like a project name, to each call, so spend can be split even inside one service.',
             picture=piles(pile('On the service', [('tag', 'team: sales'), ('tag', 'app: support'), ('tag', 'env: prod')]),
                           pile('On each request', [('tag', 'project: refunds')]))),
        card('Budgets: warn, or stop',
             'A **budget** watches spend for the month, for a whole team or for each person. When spend passes a '
             'line, it can **send an alert**, **block** more calls, or both. Decide in advance which one '
             'each budget does. A block on a live app is an outage, so live apps usually get an alert, and sandboxes '
             'a block. A budget picks its services by their service tags, like `team: sales`. It never '
             'reads request tags, so a project tag can split the spend in the table but not stop it.',
             picture=piles(pile('A rate limit', [('clock', 'Counts each minute'), ('gauge', 'Stops a burst straight away')]),
                           pile('A budget', [('coin', 'Counts the month'), ('alert', 'Sends an alert'),
                                             ('x', 'Can block more calls')])),
             after='A block is close to real time but not exact, so a little spend can slip past it. The bill is still '
                   'the final word.'),
    ],
    example=example('Tokens last month, by app tag', """support       4,100,000
summary       9,800,000
search          600,000
untagged      3,200,000"""),
    check=question(
        'Finance asks which app spent the most on models last month. Where do you look first?',
        ['The usage table, grouped by app tag', "The provider's invoice for the month", "Each app's own settings page"],
        answer=0,
        clue='Which one names the app behind each call?',
        why="The provider's invoice shows one total for everything. The usage table has a row for each request, with "
            'its service and tags. You can add those rows up for each app.',
    ),
    angle=angle(
        pattern='Tag it, then add it up',
        text="The big idea: the usage table is the gateway's record of spend, and tags say whose it is. A rate "
             "limit caps each minute. A budget watches the month and can warn or block. Your code adds up tokens for "
             "each app tag, with untagged spend on its own line so it can't hide.",
        say='"Every request lands in the usage table, so I can say [[who spent what|which model is best|what people '
            'typed::For each user, team and app.]]. Tags split it up, and a budget can [[warn or block|lower '
            'prices|pick the model::It watches the month.]] when spend passes a line."',
        classic=None,
    ),
    exercise=exercise(
        title='Spend by App',
        topic='platform',
        difficulty='easy',
        fn='spend_by_app',
        prompt="""`spend_by_app(rows)` gets rows from the usage table. Each row is a dict like
`{"service": "prod_ai.sales.support_chat", "tokens": 1200, "tags": {"app": "support"}}`.

Add up `tokens` for each `app` tag. A row with no `app` tag counts under `"untagged"`.

Return a dict from each app to its total tokens.

Example: two `support` rows of 1200 and 800 tokens, and one row with no tags of 500, give
`{"support": 2000, "untagged": 500}`.""",
        pattern='Keep a running total for each app, with "untagged" for anything unlabelled.',
        target='one pass over the rows',
        realworld='This is the monthly showback a platform team sends: spend for each app, with an untagged line that '
                  'should shrink to zero.',
        practice=practice(
            intro='Three questions about spend, from team-sales and finance.',
            explain='The usage table records every request, and tags on services and requests say whose it was. You '
                    'found the biggest spender, chased untagged spend, and chose an alert, not a block, for a live '
                    'app\'s budget.',
            pattern='Every row tagged, every total explained',
            realworld="When finance asks who spent what, you'll answer from the usage table grouped by tags, and chase "
                      'any untagged spend until every row has an owner.',
            asks=[
                ask('Last month summary used 9.8 million tokens, support 4.1 million and search 0.6 million. You want '
                    'to cut spend. Which app do you look at first?',
                    ['summary: most of the spend', "support: it's customer-facing", "search: it's the smallest"],
                    answer=0,
                    evidence=evidence('code', title='Tokens last month, by app tag', text="""support    4,100,000
summary    9,800,000
search       600,000"""),
                    clue='Where would a saving count most?',
                    why='summary used more than the other two put together. A change there, like a smaller model or a '
                        'shorter prompt, saves the most. That is the Cost Optimization pillar.',
                    wrong=[None, 'Customer-facing matters for quality, but the spend is in summary.',
                           'The smallest saves the least.']),
                ask('Last month 3.2 million tokens had no app tag, so no owner. What needs fixing first?',
                    ['Find who made the untagged calls', 'Share it out evenly across the apps', 'Delete the untagged rows'],
                    answer=0,
                    evidence=evidence('code', title='Tokens last month, by app tag', text="""support      4,100,000
summary      9,800,000
untagged     3,200,000"""),
                    clue='Which spend has no owner?',
                    why="Spend with no tag can't be charged to anyone, and a budget that filters on tags can't see it. "
                        'Find the service or app behind it and tag it. That is the Cost Optimization pillar.',
                    wrong=[None, 'That is a guess. The spend would still have no real owner.',
                           'The rows are the evidence. Fix the tags, not the record.']),
                ask('team-sales wants a $500 monthly budget on the live support chat that customers use. Should it '
                    'block calls at $500, or only send an alert?',
                    ['Alert: a block would stop the live app', 'Block: a budget must never be passed',
                     'Block: the provider stops at $500 too'],
                    answer=0,
                    evidence=evidence('claim', who='team-sales',
                                      text='"Can you set a $500 budget on the support chat, so we never spend more than '
                                           'that in a month?"'),
                    clue='What do customers see when calls are blocked?',
                    why='A block on a live app is an outage: customers get errors until the next month. Send an alert so '
                        'a person decides, and keep blocks for sandboxes. That is the Cost Optimization pillar, weighed '
                        'against Reliability.',
                    wrong=[None, 'A block is not exact anyway, and here it would turn spend into an outage.',
                           "The provider bills what you use. It doesn't stop at your budget."]),
            ],
        ),
        starter="""def spend_by_app(rows):
    # your code here
    pass
""",
        solution="""def spend_by_app(rows):
    totals = {}
    for row in rows:
        app = row["tags"].get("app", "untagged")
        totals[app] = totals.get(app, 0) + row["tokens"]
    return totals
""",
        cases=[
            case([{'service': 'prod_ai.sales.support_chat', 'tokens': 1200, 'tags': {'app': 'support'}},
                  {'service': 'prod_ai.sales.summary', 'tokens': 3000, 'tags': {'app': 'summary'}},
                  {'service': 'prod_ai.sales.support_chat', 'tokens': 800, 'tags': {'app': 'support'}}],
                 expected={'support': 2000, 'summary': 3000}, sample=True),
            case([], expected={}),
            case([{'service': 'prod_ai.sales.search', 'tokens': 500, 'tags': {}}], expected={'untagged': 500}),
            case([{'service': 'a', 'tokens': 10, 'tags': {'team': 'sales'}},
                  {'service': 'b', 'tokens': 5, 'tags': {'app': 'search', 'team': 'sales'}}],
                 expected={'untagged': 10, 'search': 5}),
        ],
        guided="""def spend_by_app(rows):
    # Replace every ___ with real code, then run the tests.

    totals = {}
    for row in rows:
        # Step 1: the row's app tag, or "untagged" when it has none.
        app = ___
        # Step 2: add this row's tokens to that app's total.
        totals[app] = ___
    return totals
""",
        fills=['row["tags"].get("app", "untagged")', 'totals.get(app, 0) + row["tokens"]'],
        concepts=[
            ['dict.get with a default', '`d.get(key, default)` gives the default when the key is missing.',
             '{"team": "sales"}.get("app", "untagged")   # "untagged"'],
            ['A running total in a dict', 'Start each new name at 0 with `.get(name, 0)`, then add.',
             """totals = {}
totals["tea"] = totals.get("tea", 0) + 2   # {"tea": 2}"""],
        ],
        byhand="Go down the rows. For each one, find its app tag, or call it untagged, and add its tokens to that "
               "app's total.",
        why="Spend you can't attribute is spend nobody manages. Totals for each app, with an untagged line, show "
            'exactly where to look and what still needs a tag.',
    ),
)
