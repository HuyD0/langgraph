"""Trust marks: where a lesson touches responsible AI, privacy or governance, the page puts a small
ember right after a phrase in its Learn text. Tapping it opens a tooltip with a perspective (why this
moment matters for trust) and one practical tip.

Each note names one of the seven traits of trustworthy AI and a reference in the NIST AI Risk
Management Framework (AI RMF 1.0, 2023), whose four functions are Govern, Map, Measure and Manage.
``tevv=True`` tags the moments that produce test evidence: NIST calls testing TEVV (test, evaluation,
verification and validation), and experiments, eval runs and registries are its record.
"Confabulation" is the word NIST's Generative AI Profile (NIST AI 600-1, 2024) uses for confident
answers with nothing behind them.

Rules, checked by tests/test_content.py: one note per lesson at most; ``phrase`` appears exactly
once in that lesson's Learn text and doesn't cut through **bold** or `code`; keep ``view`` and
``tip`` to one or two short, plain sentences. Notes go only where the lesson really is about trust,
so most lessons have none. The order here follows the path.
"""

from drill.content.model import trust

NOTES = {
    # ---- Frame
    'use_case_score': trust(
        'safe', phrase='If a wrong answer causes real harm and nobody checks, AI must not decide it.', rmf='Map 5.1',
        view='This gate is the heart of responsible AI: how much the AI decides should match how much harm a mistake can do.',
        tip='Where a mistake can hurt someone, let the AI draft and a named person decide.'),
    'use_case_card': trust(
        'accountable', phrase='And the **owner** who decides.', rmf='Govern 2.1',
        view='NIST asks for clear roles first. A risk with no owner is a risk nobody manages.',
        tip="Write a person's name, not a team's. If nobody will put their name on it, it isn't ready."),
    'split_requirements': trust(
        'private', phrase='privacy (where personal data may go)', rmf='Govern 1.1',
        view='Privacy laws such as GDPR decide where personal data may go, so this requirement often comes from your legal team, not from you.',
        tip='Ask early: does personal data reach the model, the logs or another country? Write the answer on the card.'),
    'well_architected': trust(
        'accountable', phrase='**data and AI governance** (who may use which data and models)', rmf='Govern 1',
        view='Governance sits across every other pillar: it decides who may use which data and models, and who answers for them.',
        tip='Give access to groups, not to single people, so you can see and change who has it in one place.'),
    'fit_for_purpose': trust(
        'accountable', phrase='Writing the bars down first stops anyone from moving them to fit the result.', rmf='Manage 1.1',
        view="NIST calls this the go or no-go decision: does it meet its purpose, and should it go ahead? Bars written first make that decision honest.",
        tip='Keep the bars, the results and the decision together, with a date and the name of who decided.'),
    'split_by_key': trust(
        'valid', phrase='This is called **leakage**', rmf='Measure 2.5',
        view='An inflated test score is how an AI that doesn\'t work gets approved. Every claim that "it works" starts with an honest split.',
        tip='Split by the thing that repeats, like the customer or the document, never row by row.'),
    'calibration_table': trust(
        'explainable', phrase='An overconfident model makes that threshold mean something it does not.', rmf='Measure 2.9',
        view="People read a model's confidence as a promise. Calibration is what makes the promise true.",
        tip='Before showing a score to people, check its calibration, and say what it means in words, like "likely" or "unsure".'),
    # ---- Design
    'best_run': trust(
        'accountable', phrase='MLflow is the **ledger** that keeps that evidence.', rmf='Measure 2.1', tevv=True,
        view='This record is test evidence. NIST asks that the test sets, metrics and tools behind every result are written down.',
        tip='Log the eval set version and the judge with every run, so anyone can repeat the test.'),
    'plan_gaps': trust(
        'accountable', phrase='it makes a result easy to defend to someone else', rmf='Map 2.3', tevv=True,
        view="NIST asks for experiment design to be written down. Picking the metric before the results makes the test believable to someone who wasn't there.",
        tip='Save the plan with the experiment before the first run, so the record shows it came first.'),
    'find_confounds': trust(
        'valid', phrase='you can no longer tell which one caused the difference', rmf='Map 2.3', tevv=True,
        view="A result with a confound isn't evidence about anything. NIST asks for experiment designs that hold up to that question.",
        tip='Run a confound check before any comparison is shared, so it fails loudly instead of quietly.'),
    'replay_tools': trust(
        'valid', phrase='**freeze the world**', rmf='Measure 2.5', tevv=True,
        view='Repeatable tests turn an agent demo into evidence: the same inputs and the same world, every run.',
        tip='Keep the recordings with the eval set version, so a later rerun faces the same world.'),
    'decide_release': trust(
        'accountable', phrase='Save the reasons with the decision.', rmf='Manage 1.1', tevv=True,
        view="This is NIST's go or no-go decision, written down: what was checked, what failed, and who decided.",
        tip='Log the decision and its reasons in the same MLflow experiment as the evaluation run behind it.'),
    # ---- Build and trace
    'resolve_prompt': trust(
        'secure', phrase='versions never change', rmf='Measure 2.7',
        view='A system prompt is code that steers the model. Whoever can edit it can change what the app does, so guard and version it like code.',
        tip='Let only a few people edit production prompts, and never put secrets in a system prompt: assume it can leak.'),
    'abstention_rates': trust(
        'valid', phrase="That's the dangerous one.", rmf='Measure 2.5',
        view="NIST's guide to generative AI calls this confabulation: a confident answer with nothing behind it.",
        tip='Write the unanswerable questions from real near-misses in your traffic, not from ones you make up.'),
    'claim_gate': trust(
        'valid', phrase='if nothing is supported', rmf='Measure 2.5',
        view='"I couldn\'t verify that" is a trust feature, not a failure. People forgive a refusal faster than a wrong answer.',
        tip='Tag every revise and abstain on its trace, and watch the rate: a sudden jump means something upstream broke.'),
    'fact_history': trust(
        'private', phrase='When a person asks to be forgotten, deleting wins over keeping history', rmf='Measure 2.10',
        view='This is the right to erasure in privacy laws such as GDPR: everything kept about a person must be deletable on request.',
        tip='Key every memory by user id, so one request can find and delete everything about one person.'),
    'tool_schema': trust(
        'secure', phrase='governed, permissioned and reusable', rmf='Measure 2.7',
        view='Tools are how an agent acts in the world, so who may run each one is a security decision, not a prompt setting.',
        tip='Run tools as the signed-in user, so the agent can never do more than that person could.'),
    'trajectory_match': trust(
        'safe', phrase='Use subset when calling an unexpected tool is the risk', rmf='Measure 2.6',
        view="Checking the path, not just the answer, catches an agent that got the right result while doing something it shouldn't.",
        tip='For an agent that should only read, fail the eval the moment it calls any tool that writes.'),
    'approval_run': trust(
        'accountable', phrase='Some agent actions need a person to say yes.', rmf='Map 3.5',
        view='NIST asks you to plan human oversight up front: which actions, which person, and what they see before saying yes.',
        tip="Show the approver the exact action and its inputs, not the agent's summary of it."),
    'wrap_untrusted': trust(
        'secure', phrase="limit what the agent can do if it's fooled", rmf='Measure 2.7',
        view='Assume some injection will get through. A resilient system is one where a fooled agent still can\'t do much harm.',
        tip='List what your agent could do if it obeyed the worst email it reads, then take away what you can.'),
    'is_safe_sql': trust(
        'secure', phrase='Running it unchecked is how a chat feature becomes a data breach.', rmf='Measure 2.7',
        view="A data breach is a privacy failure as well as a security one, and the model's output is where it starts.",
        tip='Run model-written SQL as a read-only user that can see only the tables this feature needs.'),
    'authorize_tool': trust(
        'secure', phrase='a policy check is a rule', rmf='Measure 2.7',
        view="A rule the model can be talked out of isn't a control. Real limits live in code and permissions.",
        tip='Write a test that politely asks the agent to break each rule, and check the code refuses.'),
    'agent_can_read': trust(
        'secure', phrase='This is the **confused deputy** problem', rmf='Measure 2.7',
        view='An agent with more access than its user is a way around your access rules. Acting on behalf of the user keeps every rule in force.',
        tip="Use the app's identity only for shared data that isn't about one person, and log which identity each tool call used."),
    'shell_policy': trust(
        'safe', phrase='avoid the **lethal trifecta**', rmf='Measure 2.6',
        view='The clearest safety rule for agents: private data, untrusted text and a way to send data out should never meet in one agent.',
        tip='For each agent, tick the three. If all three are ticked, split the agent or remove one.'),
    'memory_write_gate': trust(
        'accountable', phrase='Save where each memory came from (its **provenance**)', rmf='Measure 2.8',
        view='Provenance lets you answer "why did the agent believe that?" weeks later, and undo it.',
        tip="Store who wrote each memory and when, and keep a way to roll back one user's memory."),
    'sweep_memory': trust(
        'private', phrase='Expired memories are deleted on a schedule, not just hidden from the agent.', rmf='Measure 2.10',
        view='Memory makes an agent helpful, and it also makes the agent a store of personal data, with every duty that brings.',
        tip='Agree the retention table with your privacy team before the first memory is saved.'),
    'redact_pii': trust(
        'private', phrase='Every copy is a liability.', rmf='Measure 2.10',
        view='Privacy by design means collecting less. The safest personal data is the data you never stored.',
        tip="Mask before logging, and give traces an expiry date. Keep only what you'd be happy to show the person it's about."),
    'scrub_secrets': trust(
        'secure', phrase='more than through hacks', rmf='Measure 2.7',
        view='Most leaks are accidents, not attacks, so the defence is a habit: secrets never appear as plain text anywhere.',
        tip='Turn on secret scanning for your Git repository, so keys are caught before they are pushed.'),
    'token_findings': trust(
        'secure', phrase='It **lives long**, so a leaked copy stays useful for weeks.', rmf='Measure 2.7',
        view="Short-lived credentials limit the damage of the leak you haven't found yet. Good security plans for failure, not only prevention.",
        tip='Ask an admin to turn off new PATs and set a maximum token lifetime for the workspace.'),
    # ---- Evaluate
    'assign_splits': trust(
        'fair', phrase='A plain random split can leave a small group out of the test set altogether.', rmf='Measure 2.11',
        view="If a group isn't in the test set, nobody has measured how the system treats it.",
        tip='List the groups you serve before splitting, and check that each one has examples in every set.'),
    'weighted_score': trust(
        'fair', phrase='One overall score hides problems', rmf='Measure 2.11',
        view='This is how unfairness hides: a system can be good on average and bad for one group of people.',
        tip='Where it is lawful and you have the data, also score by groups of people, such as language or region, not only by topic.'),
    'must_pass_gate': trust(
        'safe', phrase='the medical disclaimer', rmf='Measure 2.6',
        view="Safety isn't an average. A few failures can matter more than thousands of good answers.",
        tip='Write must-pass cases with the people who handle complaints. They know which mistakes hurt people.'),
    'judge_agreement': trust(
        'valid', phrase='it can be wrong', rmf='Measure 2.5',
        view='When a model grades a model, a person has to check the grader, or nobody has checked anything.',
        tip="Check the judge against fresh human labels again after any change to the judge's prompt or model.", tevv=True),
    'review_queue': trust(
        'accountable', phrase='experts **confirm or correct** the drafts', rmf='Map 3.5',
        view='AI-drafted labels are only as trustworthy as the person really checking them.',
        tip='Watch the change rate. If it falls to almost zero, the experts may have stopped reading.'),
    'change_report': trust(
        'explainable', phrase='**Reading** them explains it.', rmf='Measure 2.9',
        view='Being able to say why a new version behaves differently is explainability for the whole team.',
        tip='Write each cause in plain words someone outside the team could follow.'),
    'mix_shift': trust(
        'valid', phrase='eval scores stop predicting real quality', rmf='Manage 4.1',
        view='NIST expects monitoring after launch, because a system that was safe on day one can drift.',
        tip='Alert on drift, and refresh the eval set from recent traffic, with personal data masked first.'),
    # ---- Ship
    'graduation_gate': trust(
        'accountable', phrase='a named owner', rmf='Manage 1.1', tevv=True,
        view='The graduation pack is a governance record: an owner, evidence and monitoring, agreed before it goes live.',
        tip='Keep each pack with the version it approved, so you can always show why it shipped.'),
    'promote_model': trust(
        'accountable', phrase='stores every trained version with its metrics', rmf='Govern 1.6', tevv=True,
        view='NIST asks for an inventory of your AI systems. A registry, with each version and its evidence, is that inventory.',
        tip='Register agents and prompts too, not just models, with the evaluation run that approved each version.'),
    'route_request': trust(
        'safe', phrase='Never switch all traffic to a new agent at once.', rmf='Measure 2.6',
        view='A canary limits how many people a bad version can hurt before you notice.',
        tip='Agree the rollback rule before the canary starts, and let anyone on call trigger it.'),
    'prompt_rollout': trust(
        'valid', phrase='before any real user sees it', rmf='Measure 2.3', tevv=True,
        view='Testing offline first, then on a small share of real traffic, gives evidence it works in conditions like the real ones.',
        tip='Save the evaluation run id with the prompt version you promote, so the evidence travels with it.'),
    'grants_to_revoke': trust(
        'private', phrase='controls who can use which data', rmf='Govern 1',
        view='Data access is where privacy is won or lost. Grants kept in code can be reviewed like any other change.',
        tip='Review grant changes in pull requests, and grant to groups, not to single people.'),
    # ---- Monitor
    'summarize_by_tag': trust(
        'accountable', phrase='no analysis later can recover it', rmf='Measure 2.8', tevv=True,
        view='Traces are your audit trail: they let you explain any answer after the fact.',
        tip='Tag the model and prompt version on every trace from the first day.'),
    'trace_table_row': trust(
        'private', phrase='with personal data hidden first', rmf='Measure 2.10',
        view='Traces hold the most detailed record of what people told your app, so they need the same care as any customer data.',
        tip='Give the trace table an expiry date and limit who can read it.'),
    'detect_loop': trust(
        'safe', phrase='limits that stop a run before it does damage or burns money', rmf='Manage 2.4',
        view='NIST asks for a way to stop or switch off an AI system that goes wrong. Guardrails are the automatic version.',
        tip='Also keep a manual off switch: one setting that stops the agent without a redeploy.'),
    'cache_hits': trust(
        'private', phrase='usually the prompt text', rmf='Measure 2.10',
        view="A shared cache can hand one person's answer, with their details in it, to someone else.",
        tip='Put the user id in the cache key for anything personal, or cache only answers with no personal data.'),
}
