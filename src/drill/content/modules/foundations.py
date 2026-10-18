"""AI & ML foundations: What kind of AI fits a job, how an LLM works and why it gets things wrong, then how to judge a model's predictions."""

from drill.content.model import (angle, ask, card, case, evidence, example, exercise, lesson, machine, module, pile, piles, practice,
                                 question, rewrite, seesaw, sortby, sortrow, stack, steps)

MODULE = module('foundations', 'AI & ML foundations', "What kind of AI fits a job, how an LLM works and why it gets things wrong, then how to judge a model's predictions.")

lesson(MODULE, 'kind_of_ai',
    title='What kind of AI is it?',
    cards=[
        card('Four tools, four kinds of job',
             '"AI" covers very different tools. The first question about any idea is which one fits.',
             picture=sortby('Which tool fits the job?',
                            sortrow('A rule', 'The answer follows a fixed rule: refunds over $50 need a manager', 'If-then code', icon='listcheck'),
                            sortrow('A model trained on examples', 'Predict a label or a number from past cases: will this invoice be paid late?', 'Machine learning', icon='chart'),
                            sortrow('A large language model (LLM)', 'Read and write language: draft a reply, sum up a document', 'Generative AI', icon='chat'),
                            sortrow('An LLM with your documents', 'Find the right passage in your own content, then answer from it', 'RAG', icon='search'))),
        card('How a model learns from examples',
             'A **machine learning** model learns from past cases that already have the right answer, called **labels**.',
             picture=steps(('listcheck', 'Examples with answers', 'Three years of invoices, each labelled "paid late" or "on time".'),
                           ('chart', 'Training', 'The model finds patterns that link an invoice\'s details to its label.'),
                           ('target', 'Prediction', 'For a new invoice it gives a score: how likely it is to be late.')),
             after='No labelled examples means nothing to learn from and nothing to test on: one of the gates from "Is this a good AI use case?".'),
        card('An LLM is trained too, just differently',
             'An LLM was trained by its provider on a huge amount of text, so it can do many language jobs from instructions alone, called a **prompt**.',
             picture=piles(pile('A trained model', ['Trained on your own labelled examples', 'One narrow job, like late or not', 'Gives a score you can set a threshold on']),
                           pile('An LLM', ['Trained by the provider on huge amounts of text', 'Many jobs, from a prompt', 'Writes text that has to be checked']))),
        card('Pick the simplest one that works',
             'Each step up costs more and is harder to test, so go only as far as the job needs.',
             picture=steps(('listcheck', 'A rule', 'If a fixed rule always gives the right answer, write the rule.'),
                           ('chart', 'A trained model', 'For one prediction learned from past examples.'),
                           ('chat', 'An LLM', 'For reading and writing language.'),
                           ('search', 'An LLM with your documents (RAG)', 'When answers must come from your own content.'),
                           ('bot', 'An agent', 'An LLM that takes steps and uses tools, when the job needs actions.'))),
    ],
    example=example('Four ideas, four tools', """# flag claims over $500 with no receipt
#   -> a rule
# predict which invoices will be late
#   -> a model trained on past invoices
# answer HR questions from the policy
#   -> an LLM with your documents (RAG)
# read an email, update the order
#   -> an agent: an LLM using tools"""),
    check=question(
        'You need to predict which invoices will be paid late, from 3 years of past invoices marked late or on time. Which fits best?',
        [
            'A model trained on past invoices',
            'An LLM that writes about each invoice',
            'A fixed rule on the invoice amount',
        ],
        answer=0,
        why='You have past cases with the right answer, and the job is one prediction: that is what a trained model is for. An LLM writes language, and one fixed rule rarely captures what makes an invoice late.',
    ),
    angle=angle(
        pattern='Check the simplest tool first, then step up',
        text='The big idea: "AI" covers a rule, a trained model, an LLM, an LLM with your documents, and an agent, and you pick the simplest one that does the job. Your code checks the task\'s facts in that order. If a fixed rule works, it answers "rule". If the task takes actions, it answers "agent". If it is about language, it answers "rag" when the answers must come from your own documents and "llm" otherwise. If there are labelled examples, it answers "trained model". Otherwise there is nothing to build on yet. It is like picking a tool from a toolbox: a screwdriver before a power drill.',
        say='"First I ask which kind of AI fits: a [[rule|chatbot|agent::The simplest: if-then code.]] if the answer is fixed, a model trained on [[labelled|random|recent::Past cases that have the right answer.]] examples for one prediction, and an LLM only for [[language|numbers|storage::Reading and writing text.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Pick the Kind of AI',
        topic='foundations',
        difficulty='easy',
        fn='pick_tool',
        prompt="""Your function gets `task`, a dict of True or False facts:

- `"fixed_rule"`: a fixed rule always gives the right answer
- `"takes_actions"`: it must take steps and use tools
- `"language"`: the job is reading or writing language
- `"own_documents"`: the answers must come from your own documents
- `"labelled_examples"`: you have past cases with the right answer

Check them in this order and return the first that fits:

1. `fixed_rule` → `"rule"`
2. `takes_actions` → `"agent"`
3. `language` and `own_documents` → `"rag"`
4. `language` → `"llm"`
5. `labelled_examples` → `"trained model"`
6. none of these → `"not yet"`""",
        pattern='Test the conditions from simplest to most complex, and return at the first match.',
        target='a few checks in order',
        realworld='Teams vetting AI ideas start with "could a rule do it?" and step up only as far as needed. Many ideas end up as a rule or a small trained model, which are cheaper and easier to test than an LLM.',
        practice=practice(
            intro='Four ideas from around the company. For each, pick the simplest kind of AI that does the job.',
            explain='The big idea: "AI" covers a rule, a trained model, an LLM, an LLM with your documents and an agent, and you pick the simplest one that works. The expenses check needed only a rule, the HR questions needed an LLM answering from the policy pages, predicting who cancels needed a model trained on past customers, and the supplier email needed an agent because it had to take actions.',
            pattern='The simplest tool that does the job',
            realworld='When someone brings an AI idea at work, ask first whether a rule could do it, then whether it is one prediction from past examples, and only then reach for an LLM or an agent.',
            gotchas=[
                ['An LLM for everything', 'An LLM is the most flexible tool and the hardest to test. A rule or a trained model is cheaper and steadier when it fits.'],
                ['Forgetting the labels', 'A trained model needs past cases with the right answer. No labels, no model.'],
            ],
            asks=[
                ask('Which kind of AI fits?', ['A rule: amount and receipt', 'A model trained on past claims', 'An LLM reading every claim'], answer=0,
                    evidence=evidence('claim', who='An idea from finance', text='"Flag every expense claim over $500 that has no receipt."'),
                    clue='Could a plain if-then always give the right answer here?',
                    why='Over $500 and no receipt is a fixed rule, so write the rule. It is free to run and never wrong.',
                    wrong=[None, 'There is nothing to predict: the rule already says which claims to flag.', 'An LLM would cost money on every claim and could get a fixed rule wrong.']),
                ask('Which kind of AI fits?', ['An LLM answering from the policy pages', 'A model trained on past HR questions', 'A rule for each kind of question'], answer=0,
                    evidence=evidence('claim', who='An idea from HR', text='"Answer staff questions about HR policy, and show the policy page each answer comes from."'),
                    clue='It is language, and the answers must come from your own documents.',
                    why='Reading and writing language from your own policy pages is RAG: an LLM that finds the right passage and answers from it, showing its source.',
                    wrong=[None, 'A trained model predicts a label or a number. It can\'t write an answer from a policy page.', 'Staff ask in endless ways. No set of rules can cover them.']),
                ask('Which kind of AI fits?', ['A model trained on those records', 'An LLM asked about each customer', 'A rule on how long they stayed'], answer=0,
                    evidence=evidence('claim', who='An idea from sales', text='"Predict which customers will cancel next month, from two years of records marked stayed or left."'),
                    clue='One prediction, and past cases with the right answer.',
                    why='Past records labelled stayed or left, and one prediction to make: a trained model, which gives a score per customer you can check against what happens.',
                    wrong=[None, 'An LLM can talk about customers, but it doesn\'t learn your records\' patterns the way a trained model does.', 'One rule rarely captures why people leave. The labelled records let a model learn it.']),
                ask('Which kind of AI fits?', ['An agent: an LLM that uses tools', 'A model trained on past emails', 'A rule on the email subject'], answer=0,
                    evidence=evidence('claim', who='An idea from operations', text='"Read a supplier\'s email, look up the order, and update its delivery date in the system."'),
                    clue='It doesn\'t just answer: it has to look things up and change them.',
                    why='Reading the email is language, and looking up and updating the order are actions with tools: that is an agent. It also needs the most care, because it changes real data.',
                    wrong=[None, 'A trained model makes one prediction. This job has to read, look up and update.', 'Suppliers write in many ways, and a rule can\'t update the order for you.']),
            ],
        ),
        starter="""def pick_tool(task):
    # your code here
    pass
""",
        solution="""def pick_tool(task):
    if task["fixed_rule"]:
        return "rule"
    if task["takes_actions"]:
        return "agent"
    if task["language"] and task["own_documents"]:
        return "rag"
    if task["language"]:
        return "llm"
    if task["labelled_examples"]:
        return "trained model"
    return "not yet"
""",
        cases=[
            case({"fixed_rule": False, "takes_actions": False, "language": True, "own_documents": True, "labelled_examples": False},
                 expected="rag", sample=True),
            case({"fixed_rule": True, "takes_actions": False, "language": False, "own_documents": False, "labelled_examples": True}, expected="rule"),
            case({"fixed_rule": False, "takes_actions": False, "language": False, "own_documents": False, "labelled_examples": True}, expected="trained model"),
            case({"fixed_rule": False, "takes_actions": True, "language": True, "own_documents": False, "labelled_examples": False}, expected="agent"),
            case({"fixed_rule": False, "takes_actions": False, "language": False, "own_documents": False, "labelled_examples": False}, expected="not yet"),
        ],
        guided="""def pick_tool(task):
    # Replace every ___ with real code, then run the tests.
    if task["fixed_rule"]:
        return "rule"
    if task["takes_actions"]:
        return "agent"
    # language from your own documents
    if ___:
        return "rag"
    if task["language"]:
        return "llm"
    if task["labelled_examples"]:
        return ___
    return "not yet"
""",
        fills=['task["language"] and task["own_documents"]', '"trained model"'],
        concepts=[
            [
                'Return at the first match',
                'Each `if` returns straight away, so the order of the checks decides which answer wins.',
                """if task["fixed_rule"]:
    return "rule"   # stops here""",
            ],
            [
                'and',
                '`a and b` is True only when both are True.',
                'True and False   # False',
            ],
        ],
        byhand='A fixed rule? No. Takes actions? No. Language and own documents? Yes and yes: return "rag".',
        why='A few checks in a fixed order.',
        gotchas=[
            [
                'Checking the complex tool first',
                'Put the rule check first. If a rule works, nothing else is needed.',
            ],
            [
                'An LLM for a prediction',
                'Predicting a label from past records is a trained model\'s job. An LLM is for language.',
            ],
        ],
    ),
)

lesson(MODULE, 'how_llms_work',
    title='How an LLM works, in plain words',
    cards=[
        card('Text becomes tokens',
             'An LLM doesn\'t read letters or whole words. It reads **tokens**: pieces of words, about three quarters of a word each in English. Models are priced and limited in tokens.',
             picture=piles(pile('What you write', ['Refunds over $50 need a manager', ('listcheck', '6 words')]),
                           pile('What the model reads', ['Ref · unds · over · $ · 50 · need · a · manager', ('chart', '8 tokens')])),
             after='How text splits depends on the model; this is one example. 1,000 tokens is roughly 750 English words.'),
        card('It predicts the next token, again and again',
             'An LLM writes one token at a time.',
             picture=steps(('chat', 'Read the prompt', 'Your instructions, the question, and anything else you send.'),
                           ('sparkle', 'Pick a likely next token', 'From patterns in the text it was trained on.'),
                           ('reset', 'Add it, then repeat', 'Token by token, until the answer is finished.')),
             after='It writes what is likely, not what is checked. That is why it can sound sure and still be wrong: the next lesson.'),
        card('It only reads what fits in the context window',
             'The **context window** is how many tokens the model can take in at once. What isn\'t sent, it never sees, and it remembers nothing between calls unless you send it again.',
             picture=piles(pile('Sent in this call: it sees it', ['Your instructions', 'The question', 'Earlier messages you resend', 'Documents you add']),
                           pile('Not sent: it never sees it', [('x', 'Yesterday\'s chat, unless resent'), ('x', 'Your new policy, unless added'), ('x', 'Anything over the window\'s limit')]))),
        card('Temperature: how varied the answers are',
             '**Temperature** is a setting from low to high.',
             picture=seesaw(('Low temperature', 'steadier, more alike each time'), ('High temperature', 'more varied, more creative'), caption='Even at a low temperature the same question can get a different answer, so test more than once.')),
        card('More context isn\'t better',
             'It is tempting to send everything: every document, the whole chat. That costs more on every call, and the answers often get worse. Answers grow less reliable as the prompt gets longer, even when the right fact is in it: this is called **context rot**, and a bigger window doesn\'t fix it.',
             picture=seesaw(('Sending everything', 'more tokens, paid on every call'), ('Answer quality', 'drops as the prompt grows'), caption='Send only what the model needs for this question.'),
             after='Later lessons show how: fewer, better passages from your documents, and measuring how full the context is.'),
    ],
    example=example('What the model reads for one question', """# instructions        ~50 tokens
# policy page added   ~6,000 tokens
# the question        ~15 tokens
# total read: a little over 6,000,
# paid for on every question"""),
    check=question(
        'Your assistant answered well yesterday. Today it says it has never seen that conversation. Why?',
        [
            'It only sees what is sent in each call',
            'It forgets because it is broken',
            'Its tokens ran out overnight',
        ],
        answer=0,
        why='An LLM remembers nothing between calls. If yesterday\'s conversation isn\'t sent again, it has never seen it. That is normal, not broken.',
    ),
    angle=angle(
        pattern='Add up what is sent, then compare with the window',
        text='The big idea: an LLM reads tokens, predicts the next token again and again, and only sees what is sent in each call, up to its context window. Your code adds up the tokens of every part of the prompt, then adds the room you keep for the answer. If the total is no more than the window, it fits. It returns the total and whether it fits. It is like packing a suitcase: everything has to go in at once, with room left for what you bring back.',
        say='"An LLM reads [[tokens|letters|pages::Pieces of words.]], predicts the next one again and again, and only sees what I send in each [[call|week|session::It remembers nothing between them.]], up to its [[context window|hard drive|training data::How much it can take in at once.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Will It Fit in the Window?',
        topic='foundations',
        difficulty='easy',
        fn='fits_window',
        prompt="""Your function gets three things:

- `parts`: a list of dicts, each with `"name"` and `"tokens"`: the pieces of the prompt.
- `window`: the most tokens the model can take in at once.
- `answer_room`: tokens you keep free for the answer.

The total is the tokens of every part plus `answer_room`.

Return `[total, fits]`, where `fits` is True if the total is no more than `window`.""",
        pattern='Add up a list, then compare with a limit.',
        target='one pass over the parts',
        realworld='Before adding documents or long chat histories to a prompt, teams check it still fits the model\'s window with room for the answer, and remember that every token is paid for on every call.',
        practice=practice(
            intro='A few things people get wrong about how LLMs work, from a team building the HR assistant.',
            explain='The big idea: an LLM reads tokens, predicts the next one again and again, and only sees what is sent in each call. You counted that a policy page makes the model read thousands of tokens per question, saw it can\'t know a new policy unless it is sent, saw why two runs can be worded differently, and matched temperature to the job.',
            pattern='It only knows what you send it',
            realworld='When an AI answer surprises you at work, first ask what was in the prompt: what was sent, what wasn\'t, and how many tokens it took.',
            gotchas=[
                ['Thinking it remembers', 'It remembers nothing between calls. Earlier messages only count if you send them again.'],
                ['Thinking it knows your news', 'It knows its training text, not last week\'s policy. Send the policy, or search your documents for it.'],
            ],
            asks=[
                ask('Roughly how many tokens does the model read for this one question?', ['A little over 6,000', 'About 15, the question', 'About 60, the sentences'], answer=0,
                    evidence=evidence('code', title='The prompt for one question', text="""You are the HR assistant.
Answer from the policy below.
[policy page: 6,000 tokens]
Question: How much parental leave do I get?"""),
                    clue='Everything in the prompt counts, not just the question.',
                    why='The model reads the whole prompt: the instructions, the 6,000-token policy page and the question. That is a little over 6,000 tokens, paid for on every question.',
                    wrong=[None, 'The question is only part of it. The policy page is read every time too.', 'The policy page alone is 6,000 tokens.']),
                ask('Is that right?', ['Only if the policy is sent in the prompt', 'Yes: models read the internet daily', 'Yes: it learns from every question'], answer=0,
                    evidence=evidence('claim', who='A teammate said', text='"The model knows our new travel policy; we published it last week."'),
                    clue='Where does the model get anything it wasn\'t trained on?',
                    why='The model knows its training text, not your new policy. It only sees the policy if you send it in the prompt, or find it in your documents (RAG).',
                    wrong=[None, 'Models don\'t read your intranet. They see what you send.', 'It doesn\'t learn from questions. Each call starts fresh.']),
                ask('You ask the same question twice and get two different wordings. What does it mean?', ['Normal: it picks likely tokens each time', 'It is broken and must be replaced', 'Someone changed the prompt between'], answer=0,
                    alone=True,
                    clue='How does it choose each next token?',
                    why='It picks a likely next token each time, and more than one is likely, so wordings differ. That is why you test on many examples, many times.',
                    wrong=[None, 'Different wordings are normal for an LLM, not a fault.', 'Even with the same prompt, the wording can change.']),
                ask('Why the different temperatures?', ['Variety for slogans, steadiness for policy', 'A higher temperature costs less money', 'A lower temperature answers faster'], answer=0,
                    evidence=evidence('code', title='Settings for two features', text="""marketing slogans:    temperature 0.9
policy answers:       temperature 0.1"""),
                    clue='Which job wants the same answer every time?',
                    why='Slogans benefit from variety, so a high temperature. Policy answers should be steady, so a low one, though even then they can vary a little.',
                    wrong=[None, 'Temperature changes how varied answers are, not the price.', 'Temperature changes how varied answers are, not the speed.']),
            ],
        ),
        starter="""def fits_window(parts, window, answer_room):
    # your code here
    pass
""",
        solution="""def fits_window(parts, window, answer_room):
    total = answer_room
    for part in parts:
        total = total + part["tokens"]
    return [total, total <= window]
""",
        cases=[
            case([{"name": "instructions", "tokens": 50}, {"name": "policy page", "tokens": 6000}, {"name": "question", "tokens": 15}],
                 8000, 500, expected=[6565, True], sample=True),
            case([{"name": "chat history", "tokens": 120000}, {"name": "question", "tokens": 20}], 128000, 8000, expected=[128020, False]),
            case([], 8000, 500, expected=[500, True]),
        ],
        guided="""def fits_window(parts, window, answer_room):
    # Replace every ___ with real code, then run the tests.
    # Start with the room kept for the answer.
    total = answer_room
    for part in parts:
        total = ___
    # It fits if the total is no more than the window.
    return [total, ___]
""",
        fills=['total + part["tokens"]', 'total <= window'],
        concepts=[
            [
                'Adding up in a loop',
                'Start a total, then add each part\'s tokens to it.',
                """total = 500
for t in [50, 6000, 15]:
    total = total + t   # 6565""",
            ],
            [
                'A comparison is True or False',
                '`total <= window` gives True when it fits and False when it doesn\'t.',
                '6565 <= 8000   # True',
            ],
        ],
        byhand='Start with 500 for the answer. Add 50, 6,000 and 15: 6,565. 6,565 is no more than 8,000, so it fits. Return [6565, True].',
        why='Each part is added once.',
        gotchas=[
            [
                'Forgetting room for the answer',
                'The answer\'s tokens count against the window too. Keep room for it.',
            ],
            [
                'Every token is paid for',
                'Fitting isn\'t the only question: a 6,000-token page sent with every question is paid for every time.',
            ],
        ],
    ),
)

lesson(MODULE, 'why_ai_wrong',
    title='Why AI gets it wrong',
    cards=[
        card('Confident and wrong: hallucination',
             'A **hallucination** is an answer that sounds sure but isn\'t true. It happens because the model writes what is likely, not what is checked.',
             picture=sortby('What it can look like',
                            sortrow('A made-up rule', '"You get 52 weeks of paid leave"', 'Wrong fact', icon='alert'),
                            sortrow('A made-up source', 'Quotes a policy page that doesn\'t exist', 'Fake source', icon='alert'),
                            sortrow('A sure tone', 'No "I don\'t know", even when it should say it', 'Overconfident', icon='alert'))),
        card('Same question, different answers',
             'Ordinary code gives the same output for the same input. An LLM may not.',
             picture=piles(pile('Ordinary code', ['Same input, same output', 'Test it once, then trust it']),
                           pile('An LLM', [('reset', 'Same input, maybe a different output'), ('flask', 'Test many examples, many times')]))),
        card('What makes it less likely',
             'You can make it less likely, and catch more of it.',
             picture=steps(('book', 'Give it the facts', 'Answer from your documents (RAG), not from memory.'),
                           ('pencil', 'Say what to do when unsure', '"If the policy doesn\'t say, say so and point to HR."'),
                           ('flask', 'Measure it', 'An eval set with right answers, run on every change.'),
                           ('person', 'A person checks what matters', 'Where a wrong answer causes harm, someone reviews it first.'))),
        card('It can be unfair',
             'An LLM learned from human writing, unfair patterns included. It can treat people differently by name, gender or background, without anyone asking it to.',
             picture=sortby('How to check',
                            sortrow('Pairs that differ in one thing', 'The same question with only the name changed, like Ana or Ahmed', 'Same answer?', icon='people'),
                            sortrow('Where people are affected', 'Hiring, pay, leave, complaints', 'Check first', icon='alert')),
             after='Different answers to the same question with only a name changed is a fairness problem. Put such pairs in your eval set.'),
        card('Why the rest of this course exists',
             'You can\'t make an LLM never wrong. You can measure how often, agree how often is acceptable, and catch the rest.',
             picture=rewrite(('Make it never wrong', 'Measure how often it is wrong'),
                             ('Test it once', 'Test it on every change'),
                             ('Trust a confident answer', 'Check where a wrong one causes harm')),
             after='That is what acceptance criteria, evals, must-pass sets and monitoring are for.'),
    ],
    example=example('Checking an answer against its source', """source = ["5 unused days carry over"]
answer = ["30 unused days carry over"]
# "30 unused days" is not in the source:
# unsupported, a likely hallucination"""),
    check=question(
        'The HR assistant quotes "Policy HR-114, section 3", but there is no such policy. What is that called?',
        ['A hallucination', 'A timeout', 'A rate limit'],
        answer=0,
        why='An answer that sounds sure but isn\'t true, here a made-up source, is a hallucination. A timeout or a rate limit would give no answer at all.',
    ),
    angle=angle(
        pattern='Keep each claim the source doesn\'t back',
        text='The big idea: an LLM writes what is likely, not what is checked, so it can be confidently wrong, and the answer is to give it the facts, measure it and check what matters. Your code goes through the claims in the answer and keeps each one that isn\'t in the source, in order. Those are unsupported: the likely hallucinations. It is like checking a report against the receipts: any amount with no receipt gets questioned.',
        say='"An LLM writes what is [[likely|checked|stored::Not what has been checked.]], so it can be confidently wrong. I give it our documents, measure how often it is wrong on an [[eval set|budget|server::Examples with known right answers.]], and have a person [[check|ignore|retrain::Review it first.]] where a mistake would hurt."',
        classic=None,
    ),
    exercise=exercise(
        title='Find the Unsupported Claims',
        topic='foundations',
        difficulty='easy',
        fn='unsupported',
        prompt="""Your function gets two lists of short claims (strings):

- `answer`: the claims the AI made.
- `source`: the claims in the document it should answer from.

Return a list of the answer's claims that are not in `source`, in the order they appear in `answer`. If every claim is backed, return `[]`.""",
        pattern='Keep the items of one list that are missing from another.',
        target='one pass over the answer',
        realworld='Grounding checks compare what an answer says with the documents it was given. Claims with no support are flagged for a person, or counted by a scorer in the eval.',
        practice=practice(
            intro='The HR assistant is in testing. Decide what each sign of trouble means and what to do.',
            explain='The big idea: an LLM writes what is likely, not what is checked, so it can be confidently wrong and give different answers to the same question. You spotted an answer the policy page didn\'t back, saw that one good test isn\'t enough, saw that an instruction helps but has to be measured, and put a person where a wrong answer could cause harm.',
            pattern='Give it the facts, then measure',
            realworld='When you plan an AI feature at work, assume it will sometimes be confidently wrong. Ask how you will measure how often, and who checks the answers where a mistake would hurt.',
            gotchas=[
                ['Trusting a sure tone', 'A confident answer isn\'t a checked one. Compare it with the source.'],
                ['Testing once', 'The same question can get different answers. Test many examples, many times.'],
            ],
            asks=[
                ask('What went wrong?', ['It answered with something the page doesn\'t say', 'The policy page itself must be out of date', 'The question must have been asked unclearly'], answer=0,
                    evidence=evidence('code', title='The policy page, and the answer', text="""policy page:
  Up to 5 unused days carry over.
the assistant said:
  You can carry over all 30 unused days."""),
                    clue='Is "all 30 days" anywhere on the page?',
                    why='The page says up to 5 days. The assistant said 30, which nothing on the page backs: a hallucination, said with full confidence.',
                    wrong=[None, 'Nothing says the page is old. The answer just doesn\'t match it.', 'The question was clear. The answer made up a number.']),
                ask('You tested the assistant once and it was right. Is it ready?', ['Not yet: test many examples, many times', 'Yes: it was right when you tried', 'Yes: models give the same answer'], answer=0,
                    alone=True,
                    clue='Would the same question always get the same answer?',
                    why='One right answer says little: the same question can get a different answer, and other questions may fail. Measure it on an eval set, more than once.',
                    wrong=[None, 'One try is one sample. Measure on many.', 'An LLM can answer the same question differently.']),
                ask('What do you say?', ['That helps, but measure it with evals too', 'Agreed: one instruction fixes it', 'No: nothing can reduce it at all'], answer=0,
                    evidence=evidence('claim', who='A manager said', text='"Just tell the model not to make things up, and we\'re done."'),
                    clue='Does an instruction guarantee it, or just make it less likely?',
                    why='Telling it what to do when unsure helps, but it still writes what is likely. Measure how often it is wrong with an eval set, and check where it matters.',
                    wrong=[None, 'An instruction makes it less likely, not impossible.', 'Giving it the facts, clear instructions and checks all reduce it.']),
                ask('Where does a person most need to check the answer before it goes out?', ['Where a wrong answer could cause harm', 'On every answer, always, forever', 'Nowhere, if the eval score is high'], answer=0,
                    alone=True,
                    clue='People can\'t check everything. Where does checking matter most?',
                    why='Put people where a wrong answer causes harm, like pay, health or legal advice. Checking everything doesn\'t scale, and a high average still lets some wrong answers through.',
                    wrong=[None, 'Checking every answer doesn\'t scale. Focus people where harm is possible.', 'A high average still lets some wrong answers through.']),
            ],
        ),
        starter="""def unsupported(answer, source):
    # your code here
    pass
""",
        solution="""def unsupported(answer, source):
    missing = []
    for claim in answer:
        if claim not in source:
            missing.append(claim)
    return missing
""",
        cases=[
            case(["30 unused days carry over", "carry-over ends in March"], ["5 unused days carry over", "carry-over ends in March"],
                 expected=["30 unused days carry over"], sample=True),
            case(["5 unused days carry over"], ["5 unused days carry over"], expected=[]),
            case([], ["5 unused days carry over"], expected=[]),
        ],
        guided="""def unsupported(answer, source):
    # Replace every ___ with real code, then run the tests.
    missing = []
    for claim in answer:
        # keep the claims the source doesn't back
        if ___:
            missing.append(___)
    return missing
""",
        fills=['claim not in source', 'claim'],
        concepts=[
            [
                'not in',
                '`x not in items` is True when x isn\'t one of the list\'s items.',
                '"30 days" not in ["5 days"]   # True',
            ],
        ],
        byhand='"30 unused days carry over" is not in the source: keep it. "carry-over ends in March" is in the source: skip it. Return ["30 unused days carry over"].',
        why='Each claim is checked once against the source.',
        gotchas=[
            [
                'Exact text only',
                'This check matches exact wording. Real grounding checks use a model or a scorer to judge whether the source backs a claim said in other words.',
            ],
        ],
    ),
)

lesson(MODULE, 'split_by_key',
    title='Train, validation and test data',
    learn=[
        'A model learns patterns from **training** data. To find out whether it learned something real or just memorised, you test it on data it has never seen: the **test** set. A third set, **validation**, is for tuning choices like thresholds (the score a model needs before it says yes) without touching the test set.',
        "The split has to be honest. If the same customer, document or day appears in both training and test, the test score is inflated. This is called **leakage**, and it's the most common reason a model that looked great disappoints in production (the live system real users depend on).",
    ],
    example=example('Splitting by user, not by row', """test_users = set(['u1', 'u7'])
train = []
test = []
for row in rows:
    if row['user'] in test_users:
        test.append(row)
    else:
        train.append(row)"""),
    check=question(
        "A model scores 97 in 100 in testing and 70 in 100 in production. Rows from the same users were in both training and test. What's the likely cause?",
        [
            'The model is too small for the task',
            'Leakage: the test users were in training too',
            'The test set was too large to score fairly',
        ],
        answer=1,
        why='Seeing the same users in training made the test easy. Splitting by user would have given a more honest, lower score.',
    ),
    angle=angle(
        pattern='Check each row against a set',
        text="The big idea: every row from a test user goes to test, so no user ends up on both sides and the score stays honest. Your code does it by asking one question per row: is this row's user one of the test users? Keeping the test users in a set makes that question instant, like finding a word through a book's index. A plain list is read from the start every time, like checking a guest list name by name: fine for 2 names, slow for 10,000.",
        say='"I split the data by [[user|row|column::Who the rows belong to.]], so nobody shows up in both training and test. Otherwise the model is tested on people it has [[already seen|never seen|forgotten::It would look better than it really is.]]."',
        classic='two_sum',
    ),
    stack=stack('MLflow: record which data trained the model', """with mlflow.start_run(run_name="churn-split-by-user"):
    mlflow.log_params({"split": "by_user", "test_users": len(test_users)})
    mlflow.log_input(mlflow.data.from_pandas(train_df, name="train"), context="training")"""),
    exercise=exercise(
        title='Split Without Leaking',
        topic='foundations',
        difficulty='easy',
        fn='split_by_key',
        machine=machine(bins=['train', 'test'], who=['everyone else', 'rows of the test users'], label_arg=1, leak_arg=1),
        prompt="""Your function gets three things:

- `rows`: the data, a list of rows. Each row is a dict (named values in curly braces), like `{"user": "u1", "label": 1}`.
- `key`: the name of the field to split on, like `"user"`.
- `test_values`: the values of that field that go to the test set, like `["u1"]`.

Look at each row's value for `key`. With `key = "user"`, that is `row["user"]`. You only look at that field. Other fields, like `label`, just come along with the row.

If the value is in `test_values`, add the row to a `test` list. Otherwise, add it to a `train` list. Keep the rows in their original order.

Return `[train, test]`, train first.""",
        pattern='Turn the test values into a set, then one pass that sends each row to train or to test.',
        target='one pass over the rows',
        realworld='Splitting by user (or by document, or by day) instead of row by row keeps the same person out of both sides. Otherwise the model is tested on people it has already seen, and the score looks better than it will be in production.',
        starter="""def split_by_key(rows, key, test_values):
    # your code here
    pass
""",
        solution="""def split_by_key(rows, key, test_values):
    test_set = set(test_values)
    train = []
    test = []
    for row in rows:
        if row[key] in test_set:
            test.append(row)
        else:
            train.append(row)
    return [train, test]
""",
        cases=[
            case([
                {'user': 'u1', 'label': 1},
                {'user': 'u2', 'label': 0},
                {'user': 'u1', 'label': 0},
                {'user': 'u3', 'label': 1},
            ], 'user', ['u1'], expected=[
                [{'user': 'u2', 'label': 0}, {'user': 'u3', 'label': 1}],
                [{'user': 'u1', 'label': 1}, {'user': 'u1', 'label': 0}],
            ], sample=True),
            case([], 'user', ['u1'], expected=[[], []]),
            case([{'doc': 'a'}, {'doc': 'b'}], 'doc', [], expected=[[{'doc': 'a'}, {'doc': 'b'}], []]),
            case([{'day': '2026-10-01'}, {'day': '2026-10-02'}, {'day': '2026-10-03'}], 'day', ['2026-10-03', '2026-10-02'], expected=[[{'day': '2026-10-01'}], [{'day': '2026-10-02'}, {'day': '2026-10-03'}]]),
        ],
        guided="""def split_by_key(rows, key, test_values):
    # Replace every ___ with real code, then run the tests.

    # Step 1: a set makes "is this a test value?" instant.
    test_set = set(test_values)
    train = []
    test = []

    for row in rows:
        # Step 2: get this row's value for key.
        # If it is in the set, the row goes to test.
        if ___ in test_set:
            test.append(row)
        else:
            # Step 3: otherwise, add the row to train.
            ___

    return [train, test]
""",
        fills=['row[key]', 'train.append(row)'],
        concepts=[
            [
                'for and if/else',
                '`for row in rows:` runs the indented lines once for each row. `if ...:` runs its lines when the condition is True; `else:` runs its lines when it is not.',
                """small = []
big = []
for n in [3, 8, 1]:
    if n > 5:   # is n above 5?
        big.append(n)
    else:
        small.append(n)
# big is [8], small is [3, 1]""",
            ],
            [
                'Sets',
                'A set is a group of values with no repeats. Checking `x in some_set` is instant. `x in some_list` checks every item.',
                """colors = set(['red', 'blue'])
'red' in colors    # True
'green' in colors  # False""",
            ],
            [
                'Dict access',
                "A dict holds named values in curly braces. `person['name']` gets one of them. `person[field]` works when the name is in a variable.",
                """person = {'name': 'Ann', 'age': 30}
field = 'name'
person[field]   # 'Ann'""",
            ],
            [
                'Adding to a list',
                '`my_list.append(x)` puts x on the end of the list.',
                """names = []
names.append('Ann')   # ['Ann']
names.append('Bo')    # ['Ann', 'Bo']""",
            ],
        ],
        byhand="The test values are just u1. Row 1's user is u1, a test value, so it goes to test. Row 2's user is u2, so it goes to train. Row 3's user is u1: test. Row 4's user is u3: train. Returns [train, test]: first the u2 and u3 rows, then the two u1 rows.",
        why='One pass over the rows; each set check is instant.',
        gotchas=[
            [
                'Duplicates leak too',
                'The same text can appear under two users (copied tickets, templates). Remove duplicates before splitting, or the test set still contains things the model trained on.',
            ],
            [
                'Time order matters',
                'For anything that predicts the future, split by date: train on the past, test on later data. A random split lets the model peek ahead.',
            ],
        ],
    ),
)

lesson(MODULE, 'precision_recall',
    title='Precision, recall and why accuracy lies',
    learn=[
        '**Precision**: of everything the model flagged, how much was right? **Recall**: of everything it should have flagged, how much did it catch?',
        'When one class, or kind of answer, is rare (fraud, outages, toxic content), **accuracy** (the share of all answers that are right) is misleading: if 1 in 100 cases is fraud, always answering "no" scores 99%. Precision and recall show what the model actually does on the cases you care about, and they trade off against each other.',
    ],
    example=example('The three counts behind both numbers', """tp = predicted yes, really yes
fp = predicted yes, really no
fn = predicted no,  really yes
precision = tp / (tp + fp)
recall    = tp / (tp + fn)"""),
    check=question(
        'A spam filter flags 10 emails; 8 are spam. There were 40 spam emails in total. What are precision and recall?',
        ['Precision 0.8, recall 0.2', 'Precision 0.2, recall 0.8', 'Precision 0.8, recall 0.8'],
        answer=0,
        why='Precision is 8 of the 10 flagged. Recall is 8 of the 40 spam emails that existed.',
    ),
    angle=angle(
        pattern='Count three piles, then divide',
        text='The big idea: when the thing you look for is rare, accuracy can look great while the model misses it, so you measure precision and recall instead. Your code walks through each prediction next to its right answer, using `zip` to pair them up like matching socks. Each pair adds 1 to one of three counters: `tp`, `fp` or `fn`. Pairs where both are 0 are skipped. Then it divides to get precision and recall, and if the bottom number (the denominator) is 0 it uses 0 instead of crashing.',
        say='"When what I\'m looking for is rare, [[accuracy|the test score|the average::Always answering no can score 99 in 100 on this one.]] can fool me. So I check precision, how much of what it [[flagged|missed|skipped::Precision only looks at the cases the model said yes to.]] was right, and recall, how many real cases it [[caught|skipped|guessed::Recall asks how many of the real ones it found.]]."',
        classic=None,
    ),
    stack=stack('MLflow: log both numbers on every run', """mlflow.sklearn.autolog()   # params, metrics and the model on every fit
mlflow.log_metrics({"precision": 0.67, "recall": 0.67})"""),
    exercise=exercise(
        title='Precision and Recall',
        topic='foundations',
        difficulty='easy',
        fn='precision_recall',
        prompt="""Your function gets two things:

- `predictions`: a model's answer for each example, `1` (yes) or `0` (no), like `[1, 0, 1]`.
- `labels`: the right answers, in the same order, like `[1, 1, 0]`.

Go through the pairs (each prediction with its label) and count:

- `tp` (true positive): predicted 1, really 1.
- `fp` (false positive): predicted 1, really 0.
- `fn` (false negative): predicted 0, really 1.

Skip pairs where both are 0.

Precision is `tp / (tp + fp)`: the share of the model's 1s that were right. Recall is `tp / (tp + fn)`: the share of real 1s the model caught.

If the number you divide by is 0, use 0 instead. Return `[precision, recall]`, each rounded to 2 decimal places.""",
        pattern='Count three things in one pass, then divide, checking first that you are not dividing by 0.',
        target='one pass over the pairs',
        realworld='Accuracy hides problems when one class is rare. If 1 in 100 transactions is fraud, a model that always says "not fraud" is 99% accurate and catches nothing: its recall is 0. Precision and recall show the trade-off you actually have to choose.',
        starter="""def precision_recall(predictions, labels):
    # your code here
    pass
""",
        solution="""def precision_recall(predictions, labels):
    tp = 0
    fp = 0
    fn = 0
    for pred, label in zip(predictions, labels):
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 1:
            fn += 1
    precision = 0
    if tp + fp > 0:
        precision = round(tp / (tp + fp), 2)
    recall = 0
    if tp + fn > 0:
        recall = round(tp / (tp + fn), 2)
    return [precision, recall]
""",
        cases=[
            case([1, 1, 0, 0, 0], [1, 0, 1, 0, 1], expected=[0.5, 0.33], sample=True),
            case([1, 1, 0, 1, 0], [1, 0, 0, 1, 1], expected=[0.67, 0.67]),
            case([1, 0, 0], [1, 1, 1], expected=[1.0, 0.33]),
            case([0, 0], [0, 0], expected=[0.0, 0.0]),
            case([1, 1], [0, 0], expected=[0.0, 0.0]),
            case([], [], expected=[0.0, 0.0]),
            case([1, 1, 1, 1], [1, 1, 1, 0], expected=[0.75, 1.0]),
        ],
        guided="""def precision_recall(predictions, labels):
    # Replace every ___ with real code, then run the tests.
    tp = 0
    fp = 0
    fn = 0

    # Step 1: walk both lists together, count each kind.
    for pred, label in zip(predictions, labels):
        if pred == 1 and label == 1:
            tp += 1
        elif ___:   # fp: predicted 1, really 0
            fp += 1
        elif pred == 0 and label == 1:
            fn += 1

    # Step 2: divide, but only if you are not dividing by 0.
    precision = 0
    if tp + fp > 0:
        precision = round(tp / (tp + fp), 2)
    # Recall: the same steps, with fn in place of fp.
    recall = 0
    if ___:
        recall = ___
    return [precision, recall]
""",
        fills=['pred == 1 and label == 0', 'tp + fn > 0', 'round(tp / (tp + fn), 2)'],
        concepts=[
            [
                'zip',
                'Walks two lists side by side, one pair at a time.',
                """for x, y in zip([1, 2], [5, 6]):
    print(x, y)   # 1 5, then 2 6""",
            ],
            [
                'elif and "and"',
                '`elif` means "else, if": Python tries each condition in order and runs the first one that is true. `a and b` is true only when both sides are true. `==` asks "are these equal?" and gives True or False. A single `=` stores a value in a name.',
                """x = 1
y = 0
x == 1 and y == 0   # True""",
            ],
            [
                'Counting with +=',
                '`count += 1` adds 1 to `count`. It is short for `count = count + 1`.',
                """count = 0
count += 1
count += 1   # count is now 2""",
            ],
            ['round', '`round(x, 2)` keeps 2 digits after the dot.', 'round(2 / 3, 2)   # 0.67'],
        ],
        byhand='Pair 1: predicted 1, really 1, so tp. Pair 2: predicted 1, really 0, so fp. Pair 3: predicted 0, really 1, so fn. Pair 4: both 0, not counted. Pair 5: predicted 0, really 1, so fn. That makes tp 1, fp 1, fn 2. Precision is tp divided by the total of tp and fp: 1 divided by (1 + 1), which is 0.5. Recall is tp divided by the total of tp and fn: 1 divided by (1 + 2), which is 0.333, rounded to 0.33. Returns [0.5, 0.33].',
        why='One pass to count, then two divisions.',
        gotchas=[
            [
                'Pick the metric before training',
                "Missing fraud (low recall) and blocking good customers (low precision) cost different amounts. Decide which matters more first, or you'll pick whichever number looks best.",
            ],
            [
                'Averages across classes',
                'With more than two classes, you can macro-average: average the score of each class, so every class counts the same. Or you can micro-average: count all examples together, so big classes count more. The two can tell very different stories.',
            ],
        ],
    ),
)

lesson(MODULE, 'best_threshold',
    title='From scores to decisions',
    learn=[
        'Most classifiers (models that sort things into groups, like spam or not spam) output a **score**, not a yes/no. You choose a **threshold**: at or above it means yes. Moving it trades precision against recall.',
        'You tune the threshold on the validation set, then check it once on the test set. The best threshold for accuracy is often not the one the business wants.',
    ],
    example=example('Same scores, different thresholds', """scores = [0.9, 0.65, 0.4]
# t = 0.5  -> [1, 1, 0]
# t = 0.7  -> [1, 0, 0]  fewer yes: usually higher precision, lower recall"""),
    check=question(
        'You raise the threshold from 0.5 to 0.9. What usually happens?',
        ['Precision goes up, recall goes down', 'Both go up', 'Recall goes up, precision goes down'],
        answer=0,
        why='Fewer things pass a stricter threshold, so the ones that do are more often right (precision up), but more true cases are missed (recall down).',
    ),
    angle=angle(
        pattern='Try every threshold, keep the best',
        text='The big idea: a model gives a score, and you pick the threshold where at or above means yes. Your code tries each score in the list as the threshold. For each one, it turns every score into a 1 or a 0 and counts how many match the right answer. It keeps the threshold with the most right so far, and a later one only wins if it gets strictly more right. This checks every threshold against every example: fine for 100 examples, slow for 10,000, because that is 100 million checks.',
        say='"I try each score as the [[threshold|average|label::At or above this, the answer is yes.]] and keep the one that gets the most answers right. I tune it on the [[validation|test|training::This set is for tuning, so the final check stays honest.]] set, then check it once on test."',
        classic='merge_intervals',
    ),
    stack=stack('MLflow: the threshold is a parameter', """with mlflow.start_run(run_name="threshold-0.65"):
    mlflow.log_param("threshold", 0.65)
    mlflow.log_metric("val_accuracy", 1.0)"""),
    exercise=exercise(
        title='Choose a Decision Threshold',
        topic='foundations',
        difficulty='medium',
        fn='best_threshold',
        prompt="""Your function gets two things:

- `scores`: the model's score for each example, from 0 to 1, like `[0.9, 0.2]`. There is at least one.
- `labels`: the right answer for each example, `1` (yes) or `0` (no), in the same order, like `[1, 0]`.

A threshold turns a score into a decision: `1` if the score is equal to or above the threshold, otherwise `0`.

Try each score in `scores` as the threshold. For each one, count how many decisions match `labels`. Return the threshold that gets the most right (the highest accuracy). There is always just one best threshold.""",
        pattern='Try each threshold, count how many it gets right, and keep the best so far.',
        target='a loop inside a loop is fine here',
        realworld='Classifiers output scores, and someone has to choose where to cut. Teams tune the threshold on a validation set, never on the test set, and often for precision or recall rather than accuracy.',
        starter="""def best_threshold(scores, labels):
    # your code here
    pass
""",
        solution="""def best_threshold(scores, labels):
    best = None
    best_right = -1
    for threshold in scores:
        right = 0
        for score, label in zip(scores, labels):
            if score >= threshold:
                decision = 1
            else:
                decision = 0
            if decision == label:
                right += 1
        if right > best_right:
            best = threshold
            best_right = right
    return best
""",
        cases=[
            case([0.9, 0.2, 0.65, 0.4], [1, 0, 1, 0], expected=0.65, sample=True),
            case([0.5], [1], expected=0.5),
            case([0.3, 0.8, 0.6], [0, 0, 1], expected=0.6),
            case([0.1, 0.9], [1, 0], expected=0.1),
            case([0.7, 0.7, 0.2], [1, 0, 0], expected=0.7),
            case([0.3, 0.6, 0.9], [1, 1, 1], expected=0.3),
            case([0.2, 0.5, 0.8], [0, 0, 1], expected=0.8),
        ],
        guided="""def best_threshold(scores, labels):
    # Replace every ___ with real code, then run the tests.
    best = None       # None means nothing picked yet
    best_right = -1   # any count beats -1

    # Step 1: try each score as the threshold.
    for threshold in scores:
        right = 0
        for score, label in zip(scores, labels):
            # Step 2: decision is 1 if score is equal to
            # or above threshold, else 0.
            if ___:
                decision = 1
            else:
                decision = 0
            if decision == label:
                right += 1
        # Step 3: if right is more than best_right, keep it.
        if ___:
            best = threshold
            best_right = right
    return best
""",
        fills=['score >= threshold', 'right > best_right'],
        concepts=[
            [
                'Comparing numbers',
                '`a >= b` means "a is equal to or above b". `a > b` means "a is above b", so it is False when they are equal.',
                """0.65 >= 0.65   # True
0.65 > 0.65    # False""",
            ],
            [
                'zip',
                'Walks two lists side by side, one pair at a time.',
                """for x, y in zip([1, 2], [5, 6]):
    print(x, y)   # 1 5, then 2 6""",
            ],
            [
                'A loop inside a loop',
                'The inner loop runs all the way through for each item of the outer loop. This prints 4 lines.',
                """for size in ['S', 'M']:
    for color in ['red', 'blue']:
        print(size, color)""",
            ],
            [
                'Keeping the best so far',
                'Start with a value anything beats. Replace it each time you find something better. Here `best_count` ends as 7.',
                """best_count = -1
for n in [3, 7, 5]:
    if n > best_count:
        best_count = n""",
            ],
            [
                'Counting with +=',
                '`count += 1` adds 1 to `count`. It is short for `count = count + 1`.',
                """count = 0
count += 1
count += 1   # count is now 2""",
            ],
        ],
        byhand='The right answers are 1, 0, 1, 0. Threshold 0.9: decisions 1, 0, 0, 0, so 3 right. Threshold 0.2: decisions 1, 1, 1, 1, so 2 right. Threshold 0.65: decisions 1, 0, 1, 0, so 4 right. Threshold 0.4: decisions 1, 0, 1, 1, so 3 right. 0.65 gets the most right, so it returns 0.65.',
        why='Trying every threshold and checking every example means checking every pair, which slows down a lot on big data. Sorting by score first lets you move the threshold one example at a time and keep a running count.',
        gotchas=[
            [
                'Tuning on the test set',
                'If you pick the threshold using the test set, the test score is no longer an honest estimate. Use a separate validation set.',
            ],
            [
                'Thresholds drift',
                "When the incoming data changes, the scores shift and yesterday's best threshold quietly gets worse. Monitor the rate of positive predictions.",
            ],
        ],
    ),
)
