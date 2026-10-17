"""Use case and fit: pick an AI use case worth doing, write it down, and decide whether it is fit for purpose."""

from drill.content.model import angle, ask, case, evidence, example, exercise, lesson, machine, module, practice, question, source

MODULE = module('use-case', 'Use case and fit', 'Pick an AI use case worth doing, write it down, and decide whether it is fit for purpose.')


# Lesson 1.1's six ideas, one practice question each. ``bin`` is where it lands; ``value``,
# ``doable`` and ``gate`` are the facts the Python exercise sorts by (a test checks they agree).
WHERE = [
    ('gate', 'Stopped at a gate, so shelved'),
    ('accelerate', 'Accelerate: worth a lot and doable now, so pilot it'),
    ('research', 'Research: worth a lot, but not doable yet'),
    ('incubate', 'Incubate: doable, but small, so learn on it'),
    ('shelve', 'Shelve: small and hard to do'),
]
MAP = {'accelerate': ('high', 'high'), 'research': ('high', 'low'), 'incubate': ('low', 'high'), 'shelve': ('low', 'low')}
IDEAS = [
    {'name': 'Rejecting job applicants', 'say': 'Reads CVs and sends rejections on its own. Nobody looks before they go out.',
     'bin': 'gate', 'why': 'A wrong rejection harms a real person, and nobody checks. That fails the harm gate, however much time it saves.',
     'clue': 'Who sees a rejection before it goes out, and what happens to a person if it is wrong?',
     'value': 'high', 'doable': 'high', 'gate': 'harm, nobody checks'},
    {'name': 'Customer email replies', 'say': 'Support answers 3,000 similar emails a month. Past replies are rated, and an agent checks every draft before it is sent.',
     'bin': 'accelerate', 'why': 'Lots of repeated work, rated past replies to test on, and a person checks each draft. Valuable and doable: pilot it.',
     'clue': 'No gate stops it: a person checks every draft. Now ask how much 3,000 emails a month is worth, and whether you could start.',
     'value': 'high', 'doable': 'high', 'gate': ''},
    {'name': 'Naming scanned files', 'say': "Suggests names for scanned files in one team's drive. Easy to try, and saves a few minutes a week.",
     'bin': 'incubate', 'why': 'Doable, but small. A safe first project to learn on, not one to bet a budget on.',
     'clue': 'It is easy to try. How much do a few minutes a week add up to?',
     'value': 'low', 'doable': 'high', 'gate': ''},
    {'name': 'Spotting fraud in expenses', 'say': 'Would save auditors weeks. Past claims were checked, but the records sit in three old systems, and audits would have to change how they work.',
     'bin': 'research', 'why': 'Valuable, but not doable yet: the data has to be pulled together and the team has to agree to work differently. Fix that first, then look again.',
     'clue': 'Weeks of auditors\' time is a lot. Could the team start tomorrow, with the records where they are?',
     'value': 'high', 'doable': 'low', 'gate': ''},
    {'name': 'Busy meeting rooms', 'say': 'Guesses which meeting rooms will be busy next year. Few people asked for it, and bookings live in three systems.',
     'bin': 'shelve', 'why': 'Small value and hard to do. Shelve it and spend the effort elsewhere.',
     'clue': 'How many people asked for it, and how easy is the data to get at?',
     'value': 'low', 'doable': 'low', 'gate': ''},
    {'name': 'Currency on invoices', 'say': "Converts invoice amounts into dollars using today's exchange rate.",
     'bin': 'gate', 'why': 'Amount times rate is a fixed rule. Write the rule: it is cheaper than AI and never wrong.',
     'clue': 'Could you write this as one simple sum?',
     'value': 'low', 'doable': 'high', 'gate': 'a rule does it'},
]


def _wrong(idea: dict, pick: str) -> str | None:
    """One plain sentence for a wrong place, worked out from the idea's facts."""
    if pick == idea['bin']:
        return None
    if idea['gate']:
        return 'Check the gates first: one of them stops this idea before value matters.'
    if pick == 'gate':
        return 'No gate stops this one: a rule can\'t do it, there is something to test on, and nobody is harmed unchecked.'
    value, doable = MAP[idea['bin']]
    if MAP[pick][0] != value:
        return 'Look again at how much it is worth.'
    return 'Look again at whether you could do it now.'


def _place(k: int, idea: dict) -> dict:
    ids = [w for w, _ in WHERE]
    return ask('Where does this idea land?', [label for _, label in WHERE], answer=ids.index(idea['bin']),
               clue=idea['clue'], why=idea['why'], wrong=[_wrong(idea, w) for w in ids],
               evidence=evidence('claim', who=f"Idea {k + 1} of {len(IDEAS)} · {idea['name']}", text=idea['say']))


lesson(MODULE, 'use_case_score',
    title='Is this a good AI use case?',
    learn=[
        "Most AI projects that fail went wrong before any code: they started from the technology (\"we need an agent\") instead of a problem. Microsoft's Cloud Adoption Framework starts with **business problems**: where results miss expectations, or people repeat the same work. Then write the use case in one line, **\"Help [who] [do what] so [a number] improves\"**, and check the task happens often enough to matter.",
        "Next, three **gates**. If a fixed rule can do the job, write the rule: it is cheaper and never wrong. If there are no past examples with right answers, you cannot test it. If a wrong answer causes real harm and nobody checks, AI must not decide it. Also choose **automate or augment**: automate tasks that are tedious, need scale and have an agreed right answer, and keep people in charge where they value the work or disagree on the answer. Most good first projects augment: AI drafts, a person decides.",
        "Ideas that pass the gates go on a **map** with two axes, usually called a value-versus-feasibility map. **Value**: what the problem costs and how much the business cares. **Doable** (feasibility): the data is ready, AI suits the task, and the team can change how it works. High value and doable: **accelerate** to a pilot. High value, not doable yet: **research**, usually fixing the data first. Doable but small: **incubate**, a safe way to learn. Neither, or failed a gate: **shelve**.",
        "Keep the two axes apart rather than adding scores together: a risky, valuable idea and a safe, trivial one can add up to the same total. Where an idea lands tells you what to do next.",
    ],
    example=example('Six ideas on the map', """             not doable yet   doable
high value   research:        accelerate:
             contract review  HR policy answers
low value    shelve:          incubate:
             staffing         meeting summaries
             forecast
failed a gate, so shelved:
  loan approvals (harm, nobody checks)
  date formats (a rule does it)"""),
    check=question(
        'Predicting which machines will break down would save a lot of downtime. Past failures are on record, but the sensor data sits in three systems and nobody has joined it up. Where does it go?',
        [
            'Accelerate: the value is high enough to start',
            'Research: valuable, but not doable yet',
            'Shelve: the data is in too many systems',
        ],
        answer=1,
        why='The value is real, but it is not doable yet: the data has to be pulled together before anything can be tested. Research means fixing that first, then looking again. Shelve is for ideas worth little.',
    ),
    angle=angle(
        pattern='Gates first, then the map',
        text='The big idea: vet an AI idea by starting from a real problem, ruling it out at once if a rule could do it, there is nothing to test on, or a wrong answer would do harm unchecked, and then placing it by value and how doable it is. The order matters. The gates come first, because a valuable idea that does harm unchecked is still shelved. Then two separate questions, value and doable, pick one of four corners: both high is accelerate, high value only is research, doable only is incubate, and neither is shelve. It is like sorting post into four trays by two questions, after binning the junk. In Python the same steps are four empty lists, one if for the gate, and if, elif and else for the corners.',
        say='"I start from a real business [[problem|model|tool::Start from what hurts today, not from the technology.]]. I drop it if a simple [[rule|person|database::If plain if-this-then-that logic does the job, you don\'t need AI.]] could do it, I have nothing to test it on, or a mistake could hurt someone with nobody checking. Then I pilot the valuable, [[doable|exciting|cheap::The map asks two things: is it worth a lot, and could you do it now?]] ones."',
        classic=None,
    ),
    exercise=exercise(
        title='Put the Ideas on the Map',
        topic='use cases',
        difficulty='easy',
        fn='place_use_cases',
        prompt="""Your function gets `ideas`, a list of dicts. Each idea has:

- `"id"` and `"name"`.
- `"value"`: `"high"` or `"low"`.
- `"doable"`: `"high"` or `"low"`.
- `"gate"`: `""` if it passed every gate, or the reason it failed, like `"a rule does it"`.

Put each idea in one corner of the map:

- Failed a gate (`"gate"` is not `""`): **shelve**.
- High value and high doable: **accelerate**.
- High value, low doable: **research**.
- Low value, high doable: **incubate**.
- Low value, low doable: **shelve**.

Return the four lists in map order, top left to bottom right: `[research, accelerate, shelve, incubate]`. Keep the ideas in the order they came in.""",
        pattern='Check the gate first, then two questions pick one of four lists.',
        target='one pass over the ideas',
        realworld="Microsoft's business, experience and technology framework and most practitioner guides prioritise AI ideas on a value-by-feasibility map, with risky ideas gated or held to strong controls.",
        starter="""def place_use_cases(ideas):
    # your code here
    pass
""",
        solution="""def place_use_cases(ideas):
    research = []
    accelerate = []
    shelve = []
    incubate = []
    for idea in ideas:
        if idea["gate"] != "":
            shelve.append(idea)
        elif idea["value"] == "high" and idea["doable"] == "high":
            accelerate.append(idea)
        elif idea["value"] == "high":
            research.append(idea)
        elif idea["doable"] == "high":
            incubate.append(idea)
        else:
            shelve.append(idea)
    return [research, accelerate, shelve, incubate]
""",
        cases=[
            case([{'id': 'A', 'name': 'HR policy answers', 'value': 'high', 'doable': 'high', 'gate': ''}, {'id': 'B', 'name': 'Loan approvals', 'value': 'high', 'doable': 'high', 'gate': 'harm, nobody checks'}, {'id': 'C', 'name': 'Date formats', 'value': 'low', 'doable': 'high', 'gate': 'a rule does it'}, {'id': 'D', 'name': 'Contract risk review', 'value': 'high', 'doable': 'low', 'gate': ''}, {'id': 'E', 'name': 'Meeting summaries', 'value': 'low', 'doable': 'high', 'gate': ''}, {'id': 'F', 'name': 'Staffing forecast', 'value': 'low', 'doable': 'low', 'gate': ''}],
                 expected=[[{'id': 'D', 'name': 'Contract risk review', 'value': 'high', 'doable': 'low', 'gate': ''}], [{'id': 'A', 'name': 'HR policy answers', 'value': 'high', 'doable': 'high', 'gate': ''}], [{'id': 'B', 'name': 'Loan approvals', 'value': 'high', 'doable': 'high', 'gate': 'harm, nobody checks'}, {'id': 'C', 'name': 'Date formats', 'value': 'low', 'doable': 'high', 'gate': 'a rule does it'}, {'id': 'F', 'name': 'Staffing forecast', 'value': 'low', 'doable': 'low', 'gate': ''}], [{'id': 'E', 'name': 'Meeting summaries', 'value': 'low', 'doable': 'high', 'gate': ''}]], sample=True),
            case([],
                 expected=[[], [], [], []]),
            case([{'id': 'X', 'name': 'Ticket triage', 'value': 'high', 'doable': 'high', 'gate': ''}, {'id': 'Y', 'name': 'Invoice totals', 'value': 'high', 'doable': 'high', 'gate': 'a rule does it'}],
                 expected=[[], [{'id': 'X', 'name': 'Ticket triage', 'value': 'high', 'doable': 'high', 'gate': ''}], [{'id': 'Y', 'name': 'Invoice totals', 'value': 'high', 'doable': 'high', 'gate': 'a rule does it'}], []]),
            case([{'id': 'P', 'name': 'Code review hints', 'value': 'high', 'doable': 'low', 'gate': ''}, {'id': 'Q', 'name': 'Alt text for images', 'value': 'low', 'doable': 'high', 'gate': ''}, {'id': 'R', 'name': 'Churn calls', 'value': 'high', 'doable': 'low', 'gate': 'no examples'}],
                 expected=[[{'id': 'P', 'name': 'Code review hints', 'value': 'high', 'doable': 'low', 'gate': ''}], [], [{'id': 'R', 'name': 'Churn calls', 'value': 'high', 'doable': 'low', 'gate': 'no examples'}], [{'id': 'Q', 'name': 'Alt text for images', 'value': 'low', 'doable': 'high', 'gate': ''}]]),
        ],
        guided="""def place_use_cases(ideas):
    # Replace every ___ with real code, then run the tests.
    research = []
    accelerate = []
    shelve = []
    incubate = []
    for idea in ideas:
        # Step 1: a failed gate shelves it, whatever its value.
        if ___:
            shelve.append(idea)
        # Step 2: high value and doable: pilot it.
        elif idea["value"] == "high" and idea["doable"] == "high":
            accelerate.append(idea)
        # Step 3: high value, not doable yet.
        elif idea["value"] == "high":
            research.append(idea)
        # Step 4: doable, but low value.
        elif ___:
            incubate.append(idea)
        else:
            shelve.append(idea)
    # Map order: top left, top right, bottom left, bottom right.
    return [research, accelerate, shelve, incubate]
""",
        fills=['idea["gate"] != ""', 'idea["doable"] == "high"'],
        concepts=[
            [
                'if, elif, else',
                'Python checks each test in order and runs only the first one that is true. `else` catches everything left.',
                """size = 7
if size > 10:
    print("big")
elif size > 5:
    print("medium")   # this one
else:
    print("small")""",
            ],
            [
                'One of several lists',
                'Start with empty lists and `append` each item to the one it belongs in.',
                """odd, even = [], []
for n in [1, 2, 3]:
    if n % 2:
        odd.append(n)
    else:
        even.append(n)""",
            ],
            [
                'and',
                '`a and b` is true only when both are true.',
                '"high" == "high" and "low" == "high"   # False',
            ],
        ],
        byhand='A passes the gate, high and high: accelerate. B failed a gate: shelve. C failed a gate: shelve. D is high value, low doable: research. E is low value, high doable: incubate. F is low and low: shelve. Return [[D], [A], [B, C, F], [E]].',
        why='Each idea is looked at once, so the work grows with the number of ideas.',
        gotchas=[
            [
                'Starting from the technology',
                '"We need an agent" is not a use case. Start from a problem people already feel, and the one-line statement with a number in it.',
            ],
            [
                'One score for everything',
                'Adding value, ease and risk into one total hides the trade-off. Keep value and doable as two axes, and treat harm as a gate.',
            ],
            [
                'Automating work people want to keep',
                "Google's People + AI Guidebook automates tasks that are tedious, need scale and have an agreed right answer, and keeps people in charge where they value the work or disagree on the answer. When in doubt, augment: AI drafts, a person decides.",
            ],
        ],
        practice=practice(
            explain='The big idea: vet an AI idea by starting from a real problem, ruling it out at once if a rule could do it, there is nothing to test on, or a wrong answer would do harm unchecked, and then placing it by value and how doable it is. The order matters. The gates come first, because a valuable idea that does harm unchecked is still shelved. Then two separate questions, value and doable, pick one of four corners: both high is accelerate, high value only is research, doable only is incubate, and neither is shelve. It is like sorting post into four trays by two questions, after binning the junk.',
            intro='Six ideas came in. For each one, check the gates first, then how much it is worth and whether you could do it now.',
            asks=[_place(k, idea) for k, idea in enumerate(IDEAS)],
        ),
        machine=machine(bins=['research', 'accelerate', 'shelve', 'incubate'], who=['high value, hard to do yet', 'high value, doable: pilot it', 'low value, or failed a gate', 'doable but small: learn on it'], label_field='id'),
    ),
)

lesson(MODULE, 'use_case_card',
    title='Write the use case down',
    learn=[
        'Before building, write the use case on one page, a **use case card**. It makes everyone agree on the same job, and it lists what the trial must measure.',
        "A card answers ten questions, shaped like the **AI Canvas** from the economists behind **Prediction Machines**, which treats AI as cheap prediction inside a decision. **Who** uses it and the **task**. The **decision**: what the AI predicts or drafts, from what input. The **action**: what happens next, and who does it. How it is done **today**, and its cost. **Success**, as a number. What a **wrong answer** costs, and who catches it. The **data** to test on. The **feedback**: how real outcomes flow back to improve it. And the **owner** who decides.",
        'Vague cards fail. "Use AI for HR" cannot be tested. "Draft answers to employee policy questions in Teams; an HR person approves each one before it is sent; success is 80 in 100 drafts approved without edits on last month\'s 200 questions" can.',
        'A blank line on the card is an open question. Answer it before you build, because a missing owner or a missing test set will stop the project later anyway.',
    ],
    example=example('A card for the HR assistant', """card = {
  "user": "HR team",
  "task": "answer policy questions",
  "decision": "a draft answer from the policy pages",
  "action": "HR approves or edits it before sending",
  "today": "15 minutes by hand, $8",
  "success": "80 in 100 approved unedited",
  "wrong_answer": "HR catches it before sending",
  "data": "last month's 200 questions",
  "feedback": "every edit goes into the eval set",
  "owner": "Head of HR operations",
}"""),
    check=question(
        'Which line makes a use case card testable?',
        [
            'Use AI to improve the HR experience for everyone',
            'Employees will find what they need much faster',
            '80 in 100 drafts approved unedited on 200 past questions',
        ],
        answer=2,
        why='Only the last one names a number and the questions you will check it on, so a trial can say yes or no. The others are hopes, not measures.',
    ),
    angle=angle(
        pattern='Check every field, then the number',
        text='The big idea: a use case card answers ten questions on one page, and a blank line, or a success line with no number, is an open question to settle before building. Your code goes through the ten field names in order. For each it reads the card\'s value, or an empty string if the field is missing, and strips spaces. A blank value is a gap. For the success field it also checks the text has at least one digit, because success you cannot count is a gap too. It returns the gaps in the same order. It is like checking a form before you post it: every box filled, and the amount written as a number.',
        say='"I write the use case on [[one page|a slide deck|a ticket::Short enough to see every box at once.]]: who uses it, what the AI does, success as a [[number|feeling|demo::A pilot has to be able to measure it.]], and who owns it. Any empty box is a [[question|failure|detail::It isn\'t wrong yet; it\'s something you don\'t know.]] I answer before building."',
        classic=None,
    ),
    exercise=exercise(
        title='Find the Gaps in a Card',
        topic='use cases',
        difficulty='easy',
        fn='card_gaps',
        prompt="""Your function gets `card`, a dict of text fields.

A full card has these ten fields, in this order:

- `"user"`, `"task"`, `"decision"`, `"action"`, `"today"`
- `"success"`, `"wrong_answer"`, `"data"`, `"feedback"`, `"owner"`

A field is a gap if it is missing, or its text is blank after removing spaces from both ends.

The `"success"` field is also a gap if its text has no digit in it, because success must be a number you can check.

Return a list of the gap field names, in the order above. A complete card gives `[]`.""",
        pattern='Walk the field list in order and collect the gaps.',
        target='one pass over the ten fields',
        realworld='A use case card is the first page of most AI project proposals. Reviewers send it back when the success line has no number or nobody owns the decision.',
        practice=practice(
            intro='Review this use case card the way a reviewer does: go down the ten boxes and send back every gap.',
            explain='The big idea: a use case card answers ten questions on one page, and a blank line, or a success line with no number, is an open question to settle before building. You went down the boxes in order, caught the missing owner and the blank wrong-answer line, and sent back a success line nobody could measure.',
            asks=[
                ask('Which box is missing from this card altogether?', ['owner', 'data', 'feedback'], answer=0,
                    evidence=evidence('code', title='The HR assistant\'s card', text="""card = {
  "user": "HR team",
  "task": "answer policy questions",
  "decision": "a draft answer from the policy pages",
  "action": "HR approves or edits it before sending",
  "today": "15 minutes, $8",
  "success": "faster answers",
  "wrong_answer": "",
  "data": "200 past questions",
  "feedback": "edits are logged and added to the eval set",
}"""),
                    clue='A card has ten boxes. Count the lines here, then find the name that never appears.',
                    why='There is no owner line at all. Without someone who wants the result and will decide, a working pilot still goes nowhere.',
                    wrong=[None, 'data is there: 200 past questions to test on.', 'feedback is there: edits go into the eval set.']),
                ask('`success` has words in it. Is it still a gap?', ['No: the box is filled in', 'Yes: there is no number in it'], answer=1,
                    clue='Could a pilot measure "faster answers" and say yes or no?',
                    why='"Faster" can\'t be tested. Success needs a number and the cases you will check it on, like 80 in 100 approved unedited on last month\'s questions.',
                    wrong=['Filled in isn\'t enough for success: a pilot has to be able to count it.', None]),
                ask('Do you let `wrong_answer` stay blank?', ['Yes: the action line already says HR checks every draft first', 'No: write down what a wrong answer costs, and who catches it'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"The action line already says HR approves every draft, so `wrong_answer` can stay blank."'),
                    clue='The action line says who checks. Does it say what a wrong answer would cost?',
                    why='A blank box is still an open question, even when the answer seems obvious. One line closes it: what a wrong answer would cost, and that HR catches it before sending.',
                    wrong=['The action says who checks, not what a wrong answer costs. Write it on the card.', None]),
                ask('A second card, for sending IT tickets to the right team. Which boxes go back to the author?', ['data only', 'user and data', 'user, data and success'], answer=1,
                    evidence=evidence('code', title='The ticket triage card', text="""card = {
  "user": "  ",
  "task": "triage tickets",
  "decision": "which team gets the ticket",
  "action": "the ticket is routed; the team can bounce it back",
  "today": "2 minutes each",
  "success": "90 in 100 routed right",
  "wrong_answer": "rerouted by hand",
  "data": "",
  "feedback": "bounced tickets are relabelled",
  "owner": "IT lead",
}"""),
                    clue='A box holding only spaces is as empty as a blank one. And does the success line have a number?',
                    why='`user` is only spaces and `data` is blank: both are gaps. Success says 90 in 100 routed right, a number a pilot can check, so it stays.',
                    wrong=['Look at user again: spaces aren\'t an answer.', None, 'Success has a number, 90 in 100, so a pilot can check it.']),
            ],
        ),
        starter="""def card_gaps(card):
    # your code here
    pass
""",
        solution="""def card_gaps(card):
    fields = ["user", "task", "decision", "action", "today",
              "success", "wrong_answer", "data", "feedback", "owner"]
    gaps = []
    for field in fields:
        value = card.get(field, "").strip()
        if value == "":
            gaps.append(field)
        elif field == "success":
            has_number = False
            for ch in value:
                if ch in "0123456789":
                    has_number = True
            if not has_number:
                gaps.append(field)
    return gaps
""",
        cases=[
            case({'user': 'HR team', 'task': 'answer policy questions', 'decision': 'a draft answer from the policy pages', 'action': 'HR approves or edits it before sending', 'today': '15 minutes, $8', 'success': 'faster answers', 'wrong_answer': '', 'data': '200 past questions', 'feedback': 'edits are logged and added to the eval set'}, expected=['success', 'wrong_answer', 'owner'], sample=True),
            case({'user': 'HR team', 'task': 'answer policy questions', 'decision': 'a draft answer from the policy pages', 'action': 'HR approves or edits it', 'today': '15 minutes, $8', 'success': '80 in 100 approved', 'wrong_answer': 'HR checks first', 'data': '200 past questions', 'feedback': 'edits go into the eval set', 'owner': 'Head of HR'}, expected=[]),
            case({}, expected=['user', 'task', 'decision', 'action', 'today', 'success', 'wrong_answer', 'data', 'feedback', 'owner']),
            case({'user': '  ', 'task': 'triage tickets', 'decision': 'which team gets the ticket', 'action': 'the ticket is routed; the team can bounce it back', 'today': '2 minutes each', 'success': '90 in 100 routed right', 'wrong_answer': 'rerouted by hand', 'data': '', 'feedback': 'bounced tickets are relabelled', 'owner': 'IT lead'}, expected=['user', 'data']),
        ],
        guided="""def card_gaps(card):
    # Replace every ___ with real code, then run the tests.
    fields = ["user", "task", "decision", "action", "today",
              "success", "wrong_answer", "data", "feedback", "owner"]
    gaps = []
    for field in fields:
        # Step 1: the value, or "" if the field is missing.
        value = card.get(field, "").strip()
        # Step 2: a blank value is a gap.
        if ___:
            gaps.append(field)
        # Step 3: success must also hold a digit.
        elif field == "success":
            has_number = False
            for ch in value:
                if ch in "0123456789":
                    has_number = True
            if ___:
                gaps.append(field)
    return gaps
""",
        fills=['value == ""', 'not has_number'],
        concepts=[
            [
                'get with a default',
                '`card.get("owner", "")` gives the value if the key is there, and `""` if it is not, instead of an error.',
                """card = {"user": "HR"}
card.get("owner", "")   # \"\"""",
            ],
            [
                'strip',
                '`strip()` removes spaces from both ends of a string, so a field of only spaces becomes empty.',
                '"  HR  ".strip()   # "HR"',
            ],
            [
                'Looking for a digit',
                '`ch in "0123456789"` is True when the character is a digit. Loop over the text and remember if you saw one.',
                """seen = False
for ch in "80 in 100":
    if ch in "0123456789":
        seen = True   # True""",
            ],
        ],
        byhand='user, task, decision, action and today are filled. success is "faster answers": not blank, but no digit, so it is a gap. wrong_answer is blank: a gap. data and feedback are filled. owner is missing: a gap. Return ["success", "wrong_answer", "owner"].',
        why='Ten fields, each checked once, so the work stays small and fixed.',
        gotchas=[
            [
                'Success with no number',
                '"Faster", "better" and "happier users" cannot be tested. Name a number and the cases you will check it on, like 80 in 100 on last month\'s questions.',
            ],
            [
                'No owner',
                'Without someone who wants the result and will decide, a working pilot still goes nowhere. Find the owner before the build.',
            ],
        ],
    ),
)

lesson(MODULE, 'split_requirements',
    title='Functional and non-functional requirements',
    learn=[
        'A **requirement** is one thing the finished system must meet, and there are two kinds. **Functional** requirements are the jobs it does: things a user could watch it do, like "answer policy questions" or "hand hard questions to a person". **Non-functional** requirements are how well it does those jobs: how fast, how safe, how cheap, how many people at once. Engineers also call them **quality attributes**.',
        'To tell them apart, imagine crossing the line off the list. If a job a user relies on disappears, the line was functional: cross out "show the source page" and users lose the source. If the system still does every job, only worse (slower, less safe, dearer), the line was non-functional: cross out "reply within 5 seconds" and it still answers, just slowly.',
        'One sentence often holds both. "Answer policy questions within 5 seconds" is a job (answer policy questions) and a bar on that job (within 5 seconds). Split it into two lines, so each one can be built and tested on its own.',
        'Non-functional requirements are the ones teams forget, and they decide whether a working demo can go live. The usual ones for AI: speed, availability (also called **uptime**: how much of the time it is working), cost per finished task, privacy (where personal data may go), security (who can see what), how many users at once, and a record of every answer. Each needs a number or a rule you can check, like "under 5 seconds for 95 in 100 answers", or the pilot can\'t say yes or no. The next lesson checks them against the pillars of a well-architected review.',
    ],
    example=example('The cross-out test on the HR assistant', """# cross it out: is a job gone?
"Show the source page"
#  gone   -> functional
"Reply within 5 seconds"
#  slower -> non-functional

# one line holding both: split it
"Answer within 5 seconds"
#  job: "Answer"
#  bar: "within 5 seconds"""),
    check=question(
        'Which of these is a non-functional requirement?',
        [
            'Draft a reply to each support ticket',
            'Send refund questions to the finance team',
            'Be available 99.9 percent of working hours',
        ],
        answer=2,
        why='The first two are jobs the system does. Availability is how well it keeps doing them, so it is non-functional.',
    ),
    angle=angle(
        pattern='Sort by a list of how-well words',
        text='The big idea: functional requirements are the jobs a system does and non-functional ones are how well it does them; crossing a line out tells you which. A reviewer\'s quick first sort can look for words about speed, uptime, cost, security and scale. Your code makes two empty lists. For each requirement it lowercases the text and checks whether any word from the how-well list appears in it. If one does, the row goes in the non-functional list, otherwise in the functional list. It returns both lists, in their original order. It is like sorting post into bills and letters by looking for a price on the envelope; a person still checks the pile.',
        say='"I cross each line out. If a [[job|word|page::Something you could watch it do.]] disappears, it was functional. If it\'s still done, just [[worse|later|twice::Slower, less safe or dearer.]], it was non-functional, and it needs a [[number|name|owner::"Fast" can\'t be tested; "under 5 seconds" can.]] the pilot can test."',
        classic=None,
    ),
    exercise=exercise(
        title='Sort the Requirements',
        topic='use cases',
        difficulty='easy',
        fn='split_requirements',
        prompt="""Your function gets `reqs`, a list of dicts, each with an `"id"` and a `"text"`.

A requirement is non-functional if its text, in lowercase, contains any of these words:

`"seconds"`, `"uptime"`, `"cost"`, `"encrypt"`, `"personal data"`, `"audit"`, `"at once"`

Every other requirement is functional.

Return `[functional, non_functional]`: two lists of the requirement dicts, each in the order they came in.""",
        pattern='Check each row for any word from a list, then put it in one of two lists.',
        target='one pass over the requirements',
        realworld='Requirement reviews often start with exactly this sort, then a person checks the edge cases. Non-functional requirements map straight onto the Well-Architected pillars.',
        practice=practice(
            intro='Sort the HR assistant\'s requirements the way a reviewer does: cross each line out and see whether a job a user relies on disappears.',
            explain='The big idea: functional requirements are the jobs a system does and non-functional ones are how well it does them. You crossed out lines to sort them, spotted a list with no how-well lines at all, split a sentence that held both kinds, and turned "always up" into a number a pilot can test.',
            asks=[
                ask('Which pile does **R4** go in?', ['Functional: a job the system does', 'Non-functional: how well it does its jobs'], answer=1,
                    evidence=evidence('code', title='The HR assistant\'s requirements', text="""R1  Answer policy questions from the HR pages
R2  Reply within 5 seconds for 95 in 100 questions
R3  Show the source page for every answer
R4  Personal data never leaves the EU
R5  Hand hard questions to a person
R6  Serve 200 users at once
R7  Cost under $1 per answer"""),
                    clue='Cross R4 out. Does the assistant still answer questions?',
                    why='Crossed out, it still answers every question, only less safely. Where personal data may go is privacy: a rule about how well the job is done, not a job. Non-functional.',
                    wrong=['Cross it out and it still answers every question. It is a rule about how well, not a job.', None]),
                ask('What is missing from the product owner\'s requirements?', ['Nothing: those three lines cover the whole job', 'How well it must do it: speed, privacy, cost', 'More features, like summarising each policy'], answer=1,
                    evidence=evidence('claim', who='The product owner said', text='"The requirements are done: it answers policy questions from the HR pages, shows the source page, and hands hard questions to a person."'),
                    clue='All three lines say what it does. Which pile is that?',
                    why='All three are functional. A demo can do every one and still not go live, because it is too slow, too costly or sends personal data where it may not go.',
                    wrong=['That is the whole job, but not how well it must do it.', None, 'It has enough to do. What is missing is how well.']),
                ask('R8 mixes both kinds. Which part is the non-functional one?', ['Answer time-off questions', 'within 5 seconds', 'Neither: it is one requirement'], answer=1,
                    evidence=evidence('code', title='A new line', text='R8  Answer time-off questions within 5 seconds'),
                    clue='Cross out each half in turn. Which one still leaves a job to do?',
                    why='"Within 5 seconds" is a bar on the job. Split it into its own line, so the pilot can test the job and the speed separately.',
                    wrong=['Cross that out and the job is gone. That half is functional.', None, 'It holds two: a job and a bar on it. Split them.']),
                ask('How would you rewrite R9 so the pilot can test it?', ['The assistant should really always be up', '99.9 percent uptime in working hours', 'Run the assistant on a bigger server'], answer=1,
                    evidence=evidence('claim', who='A teammate added', text='"R9: The assistant should always be up."'),
                    clue='"Always" can\'t be measured. What share of the time, and when?',
                    why='A number turns a hope into a bar the pilot can check: it either stayed up 99.9 percent of working hours or it didn\'t.',
                    wrong=['Stronger words still can\'t be measured.', None, 'That is a way to build it, not how well it must work.']),
                ask('R10 sounds like something the assistant does. Which pile does it go in?', ['Functional: a job the system does', 'Non-functional: how well it does its jobs'], answer=1,
                    evidence=evidence('code', title='One more line', text='R10  Keep a record of every answer, for audits'),
                    clue='Cross R10 out. Does any user lose something they could ask for or see?',
                    why='Users still get every answer, with its source. Only the team loses the record they use to check answers later. That is about how well the system is run, so it is non-functional. (Some teams file it as a feature; either way, it has to be on the list.)',
                    wrong=['Cross it out and users lose nothing they can ask for or see. It is a how-well line.', None]),
            ],
        ),
        starter="""def split_requirements(reqs):
    # your code here
    pass
""",
        solution="""def split_requirements(reqs):
    words = ["seconds", "uptime", "cost", "encrypt",
             "personal data", "audit", "at once"]
    functional = []
    non_functional = []
    for req in reqs:
        text = req["text"].lower()
        how_well = False
        for word in words:
            if word in text:
                how_well = True
        if how_well:
            non_functional.append(req)
        else:
            functional.append(req)
    return [functional, non_functional]
""",
        cases=[
            case([
                {"id": "R1", "text": "Answer policy questions from the HR pages"},
                {"id": "R2", "text": "Reply within 5 seconds for 95 in 100 questions"},
                {"id": "R3", "text": "Show the source page for every answer"},
                {"id": "R4", "text": "Personal data never leaves the EU"},
                {"id": "R5", "text": "Hand hard questions to a person"},
                {"id": "R6", "text": "Serve 200 users at once"},
                {"id": "R7", "text": "Cost under $1 per answer"},
            ], expected=[
                [{"id": "R1", "text": "Answer policy questions from the HR pages"},
                 {"id": "R3", "text": "Show the source page for every answer"},
                 {"id": "R5", "text": "Hand hard questions to a person"}],
                [{"id": "R2", "text": "Reply within 5 seconds for 95 in 100 questions"},
                 {"id": "R4", "text": "Personal data never leaves the EU"},
                 {"id": "R6", "text": "Serve 200 users at once"},
                 {"id": "R7", "text": "Cost under $1 per answer"}],
            ], sample=True),
            case([], expected=[[], []]),
            case([{"id": "A", "text": "99.9 percent UPTIME"}, {"id": "B", "text": "Encrypt every stored answer"}],
                 expected=[[], [{"id": "A", "text": "99.9 percent UPTIME"}, {"id": "B", "text": "Encrypt every stored answer"}]]),
            case([{"id": "X", "text": "Summarise each meeting"}, {"id": "Y", "text": "Keep an audit log of answers"}],
                 expected=[[{"id": "X", "text": "Summarise each meeting"}], [{"id": "Y", "text": "Keep an audit log of answers"}]]),
        ],
        guided="""def split_requirements(reqs):
    # Replace every ___ with real code, then run the tests.
    words = ["seconds", "uptime", "cost", "encrypt",
             "personal data", "audit", "at once"]
    functional = []
    non_functional = []
    for req in reqs:
        # Step 1: lowercase, so "UPTIME" matches "uptime".
        text = req["text"].lower()
        # Step 2: does any how-well word appear?
        how_well = False
        for word in words:
            if ___:
                how_well = True
        # Step 3: put the row in the right list.
        if how_well:
            non_functional.append(req)
        else:
            ___
    return [functional, non_functional]
""",
        fills=['word in text', 'functional.append(req)'],
        concepts=[
            [
                'in for text',
                '`"cost" in text` is True when the word appears anywhere inside the text.',
                '"cost" in "cost under $1"   # True',
            ],
            [
                'lower',
                '`text.lower()` makes every letter small, so a match does not depend on capitals.',
                '"UPTIME".lower()   # "uptime"',
            ],
            [
                'Two lists at once',
                'Return both lists inside one list, in a fixed order, so the caller knows which is which.',
                """return [["R1"], ["R2"]]""",
            ],
        ],
        byhand='R1 has none of the words: functional. R2 has "seconds": non-functional. R3: functional. R4 has "personal data": non-functional. R5: functional. R6 has "at once": non-functional. R7 has "cost": non-functional. Return [[R1, R3, R5], [R2, R4, R6, R7]].',
        why='Each requirement is checked against the same short word list, so the work grows with the number of requirements.',
        gotchas=[
            [
                'Forgetting the non-functional ones',
                'A demo can answer every question and still fail to go live because it is too slow, too costly or sends personal data where it may not go. Write these down on day one.',
            ],
            [
                'How-well with no number',
                '"Fast" and "secure" cannot be tested. Write "under 5 seconds for 95 in 100 answers" or "only HR staff can see answers", so the pilot can say yes or no.',
            ],
            [
                'Trusting the word list',
                'A word list is a first pile, not the answer: "Show the cost of each request" is a job users can see, yet it holds the word cost. Run the cross-out test on every line the list sorts.',
            ],
        ],
        machine=machine(bins=['functional', 'non_functional'], who=['what it must do', 'how well it must do it'], label_field='id'),
    ),
)

lesson(MODULE, 'well_architected',
    title='A well-architected review',
    checked='2026-10-15',
    sources=[source('Azure Well-Architected Framework workloads', 'https://learn.microsoft.com/azure/well-architected/workloads')],
    learn=[
        "A **well-architected review** checks a design before you build it. Microsoft's **Azure Well-Architected Framework** splits the review into five **pillars**, and each pillar is one question about how the system could let people down. Ask all five of every design.",
        "**Reliability**: what happens when something it depends on breaks, like the model being down or out of quota? **Security**: who could see or do something they shouldn't, for example through a **prompt injection** (text in a user's message that tricks the model into ignoring its rules)? **Cost Optimization**: what makes the bill grow? **Operational Excellence**: would you notice it going wrong, and can you test and release changes safely? **Performance Efficiency**: does it stay fast at the busiest minute?",
        'Your non-functional requirements are the pillars\' targets: "reply within 5 seconds" belongs to Performance Efficiency, "keep personal data in the EU" to Security, "cost under $1 per answer" to Cost Optimization. A pillar with no requirement under it is a question nobody has answered yet.',
        "The pillars pull against each other: a second copy of the app keeps it up when one fails, and doubles the bill. That is why the framework says a workload should be \"just as reliable\" and \"just as secure\" as it needs to be. A person decides which risks are fine for a pilot, and writes down why.",
        'A model can draft the review from your use case card, if the **review prompt** sets rules: quote the card for every finding, write "Unknown" and a question where the card says nothing, and leave the decision to a person. Then check every claim against the card, because a model fills gaps with confident guesses.',
        "Databricks publishes its own version for the lakehouse with two more pillars: **data and AI governance** (who may use which data and models) and **interoperability and usability** (open formats, so other tools and people can use the data).",
    ],
    example=example('The HR assistant, pillar by pillar', """# pillar: its question
#   -> what the card says
Reliability: model down?
  -> not written: ask
Security: who sees what?
  -> R4: data stays in the EU
Cost: what grows the bill?
  -> R7: under $1 an answer
Operations: would we notice?
  -> R10: every answer kept
Performance: busiest minute?
  -> R2: 5 seconds, 95 in 100"""),
    check=question(
        'A second copy of the assistant would keep it up when one copy fails, but it doubles the bill. Which two pillars pull against each other here?',
        [
            'Reliability and Cost Optimization',
            'Security and Performance Efficiency',
            'Operational Excellence and Security',
        ],
        answer=0,
        why='Staying up when something fails is Reliability, and the doubled bill is Cost Optimization. A person decides how much uptime the pilot is worth paying for.',
    ),
    angle=angle(
        pattern='Card, then pillars, then rules',
        text='The big idea: the pillars are five questions to ask of every design, and a model can draft the answers only if its prompt gives the whole use case card, asks each pillar\'s questions, and sets rules that stop it guessing or deciding. Your code builds the prompt as a list of lines. It starts with the task and the card, writing "not written" for any blank field so the gap is visible. Then for each pillar it adds a heading and its questions, and at the end the rules. It joins the lines with new lines. It is like a briefing pack for a reviewer: the facts, the questions to answer, and how to answer them.',
        say='"I ask five [[pillar|team|test::Reliability, Security, Cost, Operations, Performance.]] questions of every design, and each non-functional requirement is a [[target|owner|price::"Under 5 seconds" belongs to Performance.]] for one of them. A model can draft the review, but a [[person|script|vote::The AI drafts but never decides.]] makes the call."',
        classic=None,
    ),
    exercise=exercise(
        title='Build the Review Prompt',
        topic='use cases',
        difficulty='medium',
        fn='review_prompt',
        prompt="""Your function gets two dicts:

- `card`: the use case card, field name to text, like `{"user": "HR team", "owner": ""}`.
- `pillars`: pillar name to a list of questions, like `{"Reliability": ["What happens if the model is down?"]}`.

Build a list of lines, then return them joined with `"\\n"`:

1. `"Review this AI use case against the Well-Architected pillars."`, then `""`, then `"Use case card:"`.
2. For each card field, in order: `"- field: text"`, with the text stripped of spaces at both ends. If the text is blank, write `not written` instead.
3. For each pillar, in order: `""`, then `"## "` and the pillar name, then `"- "` and each question.
4. `""`, then every line of `RULES`, which is already written for you above the function.""",
        pattern='Collect lines in a list, then join them once.',
        target='one pass over the card, one over the pillars',
        realworld='Teams increasingly draft design reviews with a model and then check them. The quality of the draft comes from the prompt: full context, one question at a time, and rules against guessing.',
        practice=practice(
            intro='Run a well-architected review of the HR assistant: put each question under its pillar, weigh what a fix costs, then brief a model and check its draft against the card.',
            explain='The big idea: the pillars are five questions to ask of every design, and they pull against each other. You put the busiest minute under Performance, wrote down what a second copy costs, made the blank owner visible to the model, struck its go-ahead, and trusted a finding only because it quoted a line you could check.',
            asks=[
                ask('You want to ask "Can it handle the busiest minute?" Which pillar does it go under?', ['Reliability', 'Performance Efficiency', 'Cost Optimization'], answer=1,
                    clue='One pillar is about staying fast as use grows.',
                    why='Performance Efficiency is about staying fast as use grows, and the busiest minute is exactly that test.',
                    wrong=['Reliability is about failures, like the model being down. This is about load.', None, 'Cost is what you pay. This is whether it keeps up.']),
                ask('What should the review write next to this idea?', ['Nothing: more uptime is always better', 'That it doubles the cost, and who agreed to pay it', 'That it makes the assistant less secure'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"Let\'s run two copies of the assistant, so it never goes down."'),
                    clue='A win for one pillar usually costs another. What does a second copy cost?',
                    why='Two copies help Reliability and double the bill, so Cost Optimization pays for it. The review records the trade and the person who chose it, because the framework says a pilot only needs to be as reliable as it needs to be.',
                    wrong=['Uptime has a price. Who agreed to pay it?', None, 'A second copy changes the bill, not who can see the data.']),
                ask('The card\'s owner box is blank. What goes on that line of the prompt?', ['Leave the line out', 'not written', 'Head of HR operations, the likely owner'], answer=1,
                    evidence=evidence('prompt', title='Your review prompt', text="""Review this AI use case against the Well-Architected pillars.

Use case card:
- user: HR team
- task: answer policy questions
- action: HR approves or edits it before sending
- data: last month's 200 questions
- feedback: every edit goes into the eval set
- owner: ___

## Reliability
- What happens if the model is down?

Rules:
- Base every finding on the card, and quote the line you used.
- If the card does not say, write Unknown, then the question to ask the owner.
- Give each pillar a risk: low, medium or high.
- Do not say whether to build it. A person decides."""),
                    clue='The model should see the gap: no silence, and no guess.',
                    why='Writing "not written" keeps the gap visible, so the model marks it Unknown and asks who owns it, instead of skipping it or making someone up.',
                    wrong=['Leave it out and the model never learns there is a gap.', None, 'A guess in the prompt comes back as a "fact" in the review.']),
                ask('What do you do with the last line of the draft?', ['Keep it: the model found every pillar low risk', 'Strike it: the decision belongs to a person', 'Ask the model to double-check its recommendation'], answer=1,
                    evidence=evidence('code', title='The end of the draft', text="""## Overall
All five pillars look low risk.
Recommendation: safe to build. Start the pilot."""),
                    clue='Read the last rule you gave the model.',
                    why='Whether a risk is fine for a pilot is a business call. The model drafts findings and questions; a person, once the card names an owner, makes the go or no-go.',
                    wrong=['Low risk on paper is still the model\'s view. Who decides?', None, 'A second opinion from the model is still the model deciding.']),
                ask('Can you rely on this finding?', ['Yes, once you find that line on the card', 'No: everything in an AI draft is a guess', 'Yes: the model sounds sure'], answer=0,
                    evidence=evidence('claim', who='The draft said', text='**Operational Excellence: low risk.** The card says "feedback: every edit goes into the eval set", so each new version can be tested on real edits.'),
                    clue='A good finding points at something you can check yourself.',
                    why='It quotes a real line from the card, as the rules asked. Find it on the card and it becomes evidence, not a guess.',
                    wrong=[None, 'Some findings are backed by the card. Check them instead of throwing them away.', 'Sounding sure isn\'t evidence. The quoted line is.']),
            ],
        ),
        starter="""RULES = [
    'Rules:',
    '- Base every finding on the card, and quote the line you used.',
    '- If the card does not say, write Unknown, then the question to ask the owner.',
    '- Give each pillar a risk: low, medium or high.',
    '- Do not say whether to build it. A person decides.',
]


def review_prompt(card, pillars):
    # your code here
    pass
""",
        solution="""RULES = [
    'Rules:',
    '- Base every finding on the card, and quote the line you used.',
    '- If the card does not say, write Unknown, then the question to ask the owner.',
    '- Give each pillar a risk: low, medium or high.',
    '- Do not say whether to build it. A person decides.',
]


def review_prompt(card, pillars):
    lines = ["Review this AI use case against the Well-Architected pillars.",
             "", "Use case card:"]
    for field in card:
        value = card[field].strip()
        if value == "":
            value = "not written"
        lines.append("- " + field + ": " + value)
    for pillar in pillars:
        lines.append("")
        lines.append("## " + pillar)
        for q in pillars[pillar]:
            lines.append("- " + q)
    lines.append("")
    for rule in RULES:
        lines.append(rule)
    return "\\n".join(lines)
""",
        cases=[
            case({'user': 'HR team', 'task': 'answer policy questions', 'owner': ''}, {'Reliability': ['What happens if the model is down?'], 'Security': ['Who can read the answers?', 'Is prompt injection tested?']},
                 expected='Review this AI use case against the Well-Architected pillars.\n\nUse case card:\n- user: HR team\n- task: answer policy questions\n- owner: not written\n\n## Reliability\n- What happens if the model is down?\n\n## Security\n- Who can read the answers?\n- Is prompt injection tested?\n\nRules:\n- Base every finding on the card, and quote the line you used.\n- If the card does not say, write Unknown, then the question to ask the owner.\n- Give each pillar a risk: low, medium or high.\n- Do not say whether to build it. A person decides.', sample=True),
            case({'task': 'triage tickets'}, {'Cost Optimization': ['What drives the monthly cost?']},
                 expected='Review this AI use case against the Well-Architected pillars.\n\nUse case card:\n- task: triage tickets\n\n## Cost Optimization\n- What drives the monthly cost?\n\nRules:\n- Base every finding on the card, and quote the line you used.\n- If the card does not say, write Unknown, then the question to ask the owner.\n- Give each pillar a risk: low, medium or high.\n- Do not say whether to build it. A person decides.'),
            case({}, {},
                 expected='Review this AI use case against the Well-Architected pillars.\n\nUse case card:\n\nRules:\n- Base every finding on the card, and quote the line you used.\n- If the card does not say, write Unknown, then the question to ask the owner.\n- Give each pillar a risk: low, medium or high.\n- Do not say whether to build it. A person decides.'),
            case({'user': '  IT  ', 'data': '   '}, {'Operational Excellence': ['Is every answer traced?'], 'Performance Efficiency': ['Can it handle the busiest minute?']},
                 expected='Review this AI use case against the Well-Architected pillars.\n\nUse case card:\n- user: IT\n- data: not written\n\n## Operational Excellence\n- Is every answer traced?\n\n## Performance Efficiency\n- Can it handle the busiest minute?\n\nRules:\n- Base every finding on the card, and quote the line you used.\n- If the card does not say, write Unknown, then the question to ask the owner.\n- Give each pillar a risk: low, medium or high.\n- Do not say whether to build it. A person decides.'),
        ],
        guided="""RULES = [
    'Rules:',
    '- Base every finding on the card, and quote the line you used.',
    '- If the card does not say, write Unknown, then the question to ask the owner.',
    '- Give each pillar a risk: low, medium or high.',
    '- Do not say whether to build it. A person decides.',
]


def review_prompt(card, pillars):
    # Replace every ___ with real code, then run the tests.
    lines = ["Review this AI use case against the Well-Architected pillars.",
             "", "Use case card:"]
    # Step 1: every card field, with blanks made visible.
    for field in card:
        value = card[field].strip()
        if ___:
            value = "not written"
        lines.append("- " + field + ": " + value)
    # Step 2: each pillar's heading, then its questions.
    for pillar in pillars:
        lines.append("")
        lines.append(___)
        for q in pillars[pillar]:
            lines.append("- " + q)
    # Step 3: the rules at the end.
    lines.append("")
    for rule in RULES:
        lines.append(rule)
    return "\\n".join(lines)
""",
        fills=['value == ""', '"## " + pillar'],
        concepts=[
            [
                'Building text from lines',
                'Collect lines in a list with `append`, then join them once with `"\\n".join(lines)`, which puts a new line between each.',
                """lines = ["a", "b"]
"\\n".join(lines)   # a, then b on the next line""",
            ],
            [
                'A constant above the function',
                '`RULES` is defined once, outside the function, and the function reads it. Capitals are the usual sign that a value never changes.',
                """GREETING = "Hi"
def hello(name):
    return GREETING + " " + name""",
            ],
            [
                'Looping over a dict in order',
                'A dict keeps the order its keys were added, so `for pillar in pillars:` gives them in the order written.',
                """d = {"b": 1, "a": 2}
list(d)   # ["b", "a"]""",
            ],
        ],
        byhand='Start with the three opening lines. Card: user is "HR team", task is "answer policy questions", owner is blank so it becomes "not written". Reliability: a blank line, "## Reliability", its one question. Security: a blank line, "## Security", two questions. Then a blank line and the five rules. Join them all with new lines.',
        why='Each card field and each question is added once, so the work grows with the size of the card and the review.',
        gotchas=[
            [
                'Trusting the draft',
                'A model fills gaps with confident guesses, like "data is encrypted" when the card never says so. Check every finding against the card and turn guesses into questions.',
            ],
            [
                'Letting the model decide',
                'Whether a risk is fine for a pilot is a business call. Ask the model for findings and questions, and leave go or no-go to a person.',
            ],
            [
                'Fixing one pillar and forgetting the rest',
                'Every fix moves another pillar: a bigger model is faster and dearer, a second copy is more reliable and dearer. Write the trade next to the fix, with who agreed to it.',
            ],
        ],
    ),
)

lesson(MODULE, 'fit_for_purpose',
    title='Is it fit for purpose?',
    learn=[
        '**Fit for purpose** means good enough for this job, measured on real examples, against bars (acceptance criteria) agreed before the trial. Not perfect, and not "it looked good in the demo".',
        'These bars are your non-functional requirements, and the review shows which pillars they protect. Set four when you write the card. **Quality**: like 80 in 100 answers right. **Must-pass**: the dangerous cases it must never get wrong. **Speed**: how many seconds a person will wait. **Cost**: the cost per finished task must beat today\'s cost.',
        'After the pilot, the call, often called a go/no-go decision, is one of three. **Go**: every bar met. **Fix**: one bar just missed, so improve that and test again. **Stop**: a must-pass case failed, more than one bar was missed, or a miss is far off. Writing the bars down first stops anyone from moving them to fit the result.',
        'The next lessons give you the tools behind each bar. Foundations show how to measure quality honestly, Pricing works out the cost, and Evaluate later repeats this check on every new version.',
    ],
    example=example('Pilot results against the bars', """bars = {"quality": 0.80, "seconds": 5,
        "cost": 2.00}
pilot = {"quality": 0.78, "seconds": 4,
         "cost": 1.20, "must_pass_failures": 0}
# cost and speed met; quality 2 points short
# and within 5 points of the bar: fix it,
# then test again"""),
    check=question(
        'The pilot scores 86 in 100 against a bar of 80, passes every must-pass case and costs less than its bar, but takes 5.5 seconds against a 5-second bar. What is the honest call?',
        [
            'Go: half a second is close enough',
            'Fix: speed it up, then test again',
            'Stop: it missed the speed bar',
        ],
        answer=1,
        why='Only one bar is missed, and only just: half a second over. That is worth improving and testing again. Calling it a go would quietly move the bar after seeing the result.',
    ),
    angle=angle(
        pattern='Must-pass first, then count the misses',
        text='The big idea: decide fit for purpose against bars written down before the trial, and treat a failed must-pass case as an automatic stop. Your code first returns "stop" if any must-pass case failed. Then it checks quality, speed and cost against their bars, noting each one missed and whether the miss is close: quality within 0.05 of the bar, speed or cost no more than 1.2 times the bar. No misses means "go". Exactly one close miss means "fix". Anything else means "stop". It is like a driving test: one serious fault fails you, a small slip means practise and retake.',
        say='"I agree the bars [[before|after|during::Setting them once you see results lets you move them.]] the pilot. A failed must-pass case means [[stop|a warning|a retest::Must-pass means exactly that.]], all bars met means go, and one near miss means fix it and [[test again|ship it|give up::A near miss gets another try, not a pass.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Go, Fix or Stop',
        topic='use cases',
        difficulty='medium',
        fn='pilot_verdict',
        prompt="""Your function gets two dicts:

- `results`: the pilot's numbers, with `"quality"` (share right, like `0.78`), `"seconds"` (time per answer), `"cost"` (dollars per finished task) and `"must_pass_failures"` (how many must-pass cases it got wrong).
- `bars`: the agreed bars, with `"quality"`, `"seconds"` and `"cost"`.

Decide like this:

1. If `"must_pass_failures"` is more than 0, return `"stop"`.
2. A bar is missed if quality is below its bar, or seconds or cost is above its bar.
3. A miss is close if quality is at most 0.05 below its bar, or seconds or cost is at most 1.2 times its bar.
4. No bars missed: return `"go"`. Exactly one bar missed, and that miss is close: return `"fix"`. Otherwise return `"stop"`.""",
        pattern='Stop on a must-pass failure, then count the misses.',
        target='a few checks, no loops',
        realworld='Pilots are usually judged go, fix or stop against bars agreed up front. Writing the rule in code keeps the decision the same however the results make people feel.',
        practice=practice(
            intro='Judge four pilots against the bars agreed before they started: go, fix or stop.',
            explain='The big idea: decide fit for purpose against bars written down before the trial, and treat a failed must-pass case as an automatic stop. You stopped a pilot with great averages because a must-pass case failed, gave one close miss a fix, called a result that met every bar exactly a go, and kept the cost bar where it was agreed.',
            asks=[
                ask('Pilot 1 looks great on quality, speed and cost. What\'s the call?', ['Go: roll it out', 'Fix: improve and retest', 'Stop: end the pilot'], answer=2,
                    evidence=evidence('code', title='Pilot 1 against the bars', text="""bars  = {"quality": 0.80, "seconds": 5,
         "cost": 2.00}
pilot = {"quality": 0.95, "seconds": 2,
         "cost": 0.50, "must_pass_failures": 1}"""),
                    clue='Read must_pass_failures before you look at the averages.',
                    why='A must-pass case is one it must never get wrong. One failure ends the pilot on its own, however good the averages look.',
                    wrong=['Great averages can hide one dangerous mistake. Look at must_pass_failures.', 'Fix is for a near miss on a bar. A failed must-pass case is not a near miss.', None]),
                ask('What\'s the call for pilot 2?', ['Go: roll it out', 'Fix: improve and retest', 'Stop: end the pilot'], answer=1,
                    evidence=evidence('code', title='Pilot 2 against the bars', text="""bars  = {"quality": 0.80, "seconds": 5,
         "cost": 2.00}
pilot = {"quality": 0.82, "seconds": 5.5,
         "cost": 1.00, "must_pass_failures": 0}"""),
                    clue='Only one bar is missed. A miss on speed is close if it is no more than 1.2 times the bar: 6 seconds here.',
                    why='Speed is the only miss, and 5.5 seconds is within 6, so it is close. Make it faster, then test again.',
                    wrong=['5.5 seconds is over the 5-second bar, so one bar is missed.', None, 'It is one bar, and only just missed. That is worth another try.']),
                ask('What\'s the call for pilot 3?', ['Go: roll it out', 'Fix: improve and retest', 'Stop: end the pilot'], answer=0,
                    evidence=evidence('claim', who='A teammate said', text='"Pilot 3: quality exactly 0.80, exactly 5 seconds, $1.20 a task, no must-pass failures. That only just scrapes through, so let\'s call it a fix to be safe."'),
                    clue='A bar is missed only when quality falls under it, or speed or cost is above it. Is any number past its bar?',
                    why='Meeting a bar exactly is meeting it. Calling it a fix would quietly move the bar after seeing the result, just upwards this time.',
                    wrong=[None, 'Fix is for a missed bar. Which one did it miss?', 'Nothing failed: no must-pass failures and no missed bars.']),
                ask('What do you do?', ['Go: raise the bar to $3, still cheaper than by hand', 'Fix: one bar missed, so cut the cost and retest', 'Stop: it is far over the agreed cost bar'], answer=2,
                    evidence=evidence('claim', who='The sponsor said', text='"Pilot 4 costs $3.00 a task against the $2.00 bar, but quality and speed are well inside, and it\'s still cheaper than doing it by hand. Raise the cost bar to $3 and call it a go."'),
                    clue='A close miss on cost is at most 1.2 times its bar: $2.40 here. And when were the bars agreed?',
                    why='$3.00 is well past $2.40, so it is not a near miss, and raising the bar after seeing the result is moving it to fit. If the cost case really has changed, agree new bars before the next pilot.',
                    wrong=['Change the bar once you see the result and the bar meant nothing.', 'Fix is for a near miss. $3.00 is far past $2.40.', None]),
            ],
        ),
        starter="""def pilot_verdict(results, bars):
    # your code here
    pass
""",
        solution="""def pilot_verdict(results, bars):
    if results["must_pass_failures"] > 0:
        return "stop"
    missed = []
    close = True
    if results["quality"] < bars["quality"]:
        missed.append("quality")
        if results["quality"] < bars["quality"] - 0.05:
            close = False
    if results["seconds"] > bars["seconds"]:
        missed.append("seconds")
        if results["seconds"] > bars["seconds"] * 1.2:
            close = False
    if results["cost"] > bars["cost"]:
        missed.append("cost")
        if results["cost"] > bars["cost"] * 1.2:
            close = False
    if len(missed) == 0:
        return "go"
    if len(missed) == 1 and close:
        return "fix"
    return "stop"
""",
        cases=[
            case({"quality": 0.78, "seconds": 4, "cost": 1.2, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="fix", sample=True),
            case({"quality": 0.86, "seconds": 3, "cost": 1.5, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="go"),
            case({"quality": 0.95, "seconds": 2, "cost": 0.5, "must_pass_failures": 1}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="stop"),
            case({"quality": 0.7, "seconds": 4, "cost": 1.0, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="stop"),
            case({"quality": 0.82, "seconds": 5.5, "cost": 1.0, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="fix"),
            case({"quality": 0.78, "seconds": 5.5, "cost": 1.0, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="stop"),
            case({"quality": 0.9, "seconds": 3, "cost": 3.0, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="stop"),
        ],
        guided="""def pilot_verdict(results, bars):
    # Replace every ___ with real code, then run the tests.
    # Step 1: any must-pass failure stops it.
    if results["must_pass_failures"] > 0:
        return "stop"
    missed = []
    close = True
    # Step 2: quality below its bar is a miss.
    if results["quality"] < bars["quality"]:
        missed.append("quality")
        if results["quality"] < bars["quality"] - 0.05:
            close = False
    # Step 3: too slow is a miss.
    if results["seconds"] > bars["seconds"]:
        missed.append("seconds")
        if results["seconds"] > bars["seconds"] * 1.2:
            close = False
    # Step 4: too costly is a miss.
    if ___:
        missed.append("cost")
        if results["cost"] > bars["cost"] * 1.2:
            close = False
    # Step 5: decide.
    if len(missed) == 0:
        return "go"
    if ___:
        return "fix"
    return "stop"
""",
        fills=['results["cost"] > bars["cost"]', 'len(missed) == 1 and close'],
        concepts=[
            [
                'A flag',
                'A True or False variable that starts one way and flips when something happens. Here `close` starts True and turns False on any big miss.',
                """close = True
if 9 > 5 * 1.2:
    close = False   # 9 is more than 6""",
            ],
            [
                'len',
                '`len(missed)` is how many items the list holds.',
                'len(["quality"])   # 1',
            ],
            [
                'and',
                '`a and b` is True only when both are True.',
                """len([1]) == 1 and True    # True
len([1]) == 1 and False   # False""",
            ],
        ],
        byhand='No must-pass failures. Quality 0.78 is below 0.80: missed, and 0.78 is not below 0.75, so still close. Seconds 4 is not above 5. Cost 1.20 is not above 2.00. One miss, and it is close: return "fix".',
        why='A handful of comparisons, whatever the numbers.',
        gotchas=[
            [
                'Moving the bar after the results',
                'If 78 in 100 suddenly becomes "good enough" once you see it, the bar meant nothing. Write the bars on the card before the pilot starts.',
            ],
            [
                'Averaging away a dangerous mistake',
                'A high overall score can hide one serious failure. Keep the dangerous cases as must-pass checks that stop the project on their own.',
            ],
        ],
    ),
)
