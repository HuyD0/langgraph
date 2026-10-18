"""Use case and fit: pick an AI use case worth doing, write it down, and decide whether it is fit for purpose."""

from drill.content.model import (angle, ask, card, case, evidence, example, exercise, lesson, machine, module, pile, piles,
                                 pillar, pillars, practice, question, rewrite, seesaw, sortby, sortrow, source, split, steps, tile, terms)

MODULE = module('use-case', 'Use case and fit', 'Pick an AI use case worth doing, write it down, and decide whether it is fit for purpose.')


# The first lesson's (use_case_score) six ideas, one practice question each. ``bin`` is where it lands; ``value``,
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
        "Most AI projects that fail went wrong before any code: they started from the technology (\"we need an agent\") instead of a problem. So start from a **business problem**, as Microsoft's Cloud Adoption Framework does: work people repeat, or results that miss what was expected. Write the use case in one line, **\"Help [who] [do what] so [a number] improves\"**, and check the task happens often enough to matter.",
        "Next come three **gates**: pass-or-fail checks an idea has to clear. Fail any one, and the idea is set aside (shelved), however valuable it looks. If a fixed rule can do the job, write the rule: it is cheaper and never wrong. If there are no past examples with right answers, you cannot test it. If a wrong answer causes real harm and nobody checks, AI must not decide it.",
        "Ideas that pass the gates go on a **map** with two axes, usually called a value-versus-feasibility map. **Value** is what the problem costs and how much the business cares. **Doable** (feasibility) means the data is ready, AI suits the task, and the team can change how it works. Keep the two axes apart: don't add them into one score.",
        "The corner an idea lands in tells you what to do next. High value and doable: **accelerate** to a **pilot**, a small first trial with real users. High value, not doable yet: **research**, usually fixing the data first. Doable but small: **incubate**, a safe way to learn. Low on both: **shelve**.",
        "Last, choose **automate or augment** for the ideas you keep. Automate means the AI does the task on its own; augment means it helps a person do it. Most good first projects augment: AI drafts, a person decides.",
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
            pattern='Rule it out, then place it on the map',
            realworld='When someone brings an AI idea to your team, run the gates before anyone talks about models: could a rule do it, is there data to test on, could a wrong answer do harm unchecked? Then place it by value and how doable it is, and say which corner it lands in.',
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
        "A card answers ten questions, shaped like the **AI Canvas** from the economists behind **Prediction Machines**, which treats AI as cheap prediction inside a decision. **Who** uses it and the **task**. The **decision**: what the AI predicts or drafts, from what input. The **action**: what happens next, and who does it. How it is done **today**, and its cost. **Success**, as a number. What a **wrong answer** costs, and who catches it. The **data** to test on, which becomes the **eval set**: the examples every version is scored on. The **feedback**: how real outcomes flow back to improve it. And the **owner** who decides.",
        'Vague cards fail. "Use AI for HR" cannot be tested. "Draft answers to employee policy questions in Teams; an HR person approves each one before it is sent; success is 80 in 100 drafts approved without edits on last month\'s 200 questions" can.',
        'A blank line on the card is an open question. Answer it before you build, because a missing owner or a missing test set will stop the project later anyway.',
    ],
    example=example('A card for the HR assistant', """card = {
  "user": "HR team",
  "task": "answer policy questions",
  "decision": "a draft answer from the policy pages",
  "action": "HR approves or edits it before sending",
  "today": "8 minutes by hand, $8",
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
            explain='The big idea: a use case card answers ten questions on one page, and every box has to be filled before building: a missing box, a blank box, or a success line with no number is an open question. On the HR card you found no owner line at all, a success line that only said "faster", and a wrong-answer box the team wanted to leave blank. Each one goes back to the author.',
            pattern='Down the ten boxes, send back every gap',
            realworld='When a teammate shares a use case card for review, go box by box and send back every gap in one reply. The two you\'ll send back most often: a success line with no number, and no owner.',
            asks=[
                ask('Which box is missing from this card altogether?', ['owner', 'data', 'feedback'], answer=0,
                    evidence=evidence('code', title='The HR assistant\'s card', text="""card = {
  "user": "HR team",
  "task": "answer policy questions",
  "decision": "a draft answer from the policy pages",
  "action": "HR approves or edits it before sending",
  "today": "8 minutes, $8",
  "success": "faster answers",
  "wrong_answer": "",
  "data": "200 past questions",
  "feedback": "edits are logged and added to the eval set",
}"""),
                    clue='A card has ten boxes. Count the lines here, then find the name that never appears.',
                    why='There is no owner line at all. Without someone who wants the result and will decide, a working pilot still goes nowhere.',
                    wrong=[None, 'data is there: 200 past questions to test on.', 'feedback is there: edits go into the eval set.']),
                ask('`success` has words in it. Is it still a gap?', ['No: the box is filled in', 'Yes: there is no number in it'], answer=1,
                    evidence=evidence('code', title='From the HR assistant\'s card', text='"success": "faster answers",'),
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
            case({'user': 'HR team', 'task': 'answer policy questions', 'decision': 'a draft answer from the policy pages', 'action': 'HR approves or edits it before sending', 'today': '8 minutes, $8', 'success': 'faster answers', 'wrong_answer': '', 'data': '200 past questions', 'feedback': 'edits are logged and added to the eval set'}, expected=['success', 'wrong_answer', 'owner'], sample=True),
            case({'user': 'HR team', 'task': 'answer policy questions', 'decision': 'a draft answer from the policy pages', 'action': 'HR approves or edits it', 'today': '8 minutes, $8', 'success': '80 in 100 approved', 'wrong_answer': 'HR checks first', 'data': '200 past questions', 'feedback': 'edits go into the eval set', 'owner': 'Head of HR'}, expected=[]),
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

lesson(MODULE, 'team_roles',
    title='Who moves the agent forward',
    cards=[
        card('An AI feature is never finished',
             'Ordinary features can be shipped and left until the next release. An AI feature can\'t: the model, the questions people ask, your documents and the prices keep changing, even when your code doesn\'t.',
             picture=piles(pile('Set and forget', ['Ship it, then move on', 'Change it at the next release', 'Test it once']),
                           pile('Run and tend', [('activity', 'Watch it every week'), ('reset', 'Fix it within hours when it goes wrong'), ('flask', 'Test every change, every time')]))),
        card('The people who build and run it',
             'An AI feature needs several kinds of work. Each kind has an owner.',
             picture=terms(('code', 'AI engineer', 'Builds it: prompts, model, tools, evals and cost per task'),
                           ('puzzle', 'Software engineer', 'Connects it: fits it into the app, APIs and error handling'),
                           ('layers', 'Data engineer', 'Feeds it: the data, pipelines, quality, personal data'),
                           ('power', 'Platform engineer', 'Runs it, on the platform team: capacity, rollout, alerts and incidents')),
             after='Evals are the tests that score the assistant\'s answers; a rollout turns it on for people, some at a time. Later modules teach both.'),
        card('The people who decide and guard it',
             'Others decide what it is for, what a good answer is, and what it may never do.',
             picture=terms(('target', 'Product manager', 'Decides: the problem, and whether it ships. The owner on the use case card'),
                           ('person', 'Subject-matter expert', 'Defines good: writes the marking scheme (the rubric) and checks answers'),
                           ('lock', 'Security and privacy', 'Guards it: the teams who say who may see what, and where data may go'),
                           ('coin', 'Finance', 'Budgets it: the budget, and the alerts when cost runs high'),
                           ('briefcase', 'Executive sponsor', 'Backs it: fit with the business, risk, the last word in a crisis')),
             after='A **subject-matter expert** (SME) is someone who knows the work itself: for the HR assistant, an HR advisor. The product manager is the owner on the use case card: for the HR assistant, the Head of HR operations. On a small team one person may hold several of these roles. What matters is that every kind of work has an owner.'),
        card('They work together the whole way',
             'The loop goes round fast and often, so nobody can hand their part over once and walk away.',
             picture=steps(('target', 'Frame', 'Product manager, sponsor and SME agree the problem and what success is.'),
                           ('layers', 'Data', 'Data engineer, with security and privacy, gets the data ready.'),
                           ('code', 'Build and evaluate', 'AI engineer builds; the SME defines good and checks the answers.'),
                           ('rocket', 'Ship and monitor', 'Platform engineer rolls it out and watches; the product manager decides.'),
                           ('reset', 'Improve, every week', 'AI engineer and SME fix what the traces show, then round again.')),
             after='A trace is the record of one answer, every step of it, so the team can see where it went wrong.'),
        card('One decider per decision',
             'A **RACI** table says, for each decision, who is **R**esponsible (does the work), who is **A**ccountable (makes the final call: exactly one person), who is **C**onsulted (asked first) and who is **I**nformed (told after).',
             picture=sortby('A quick fix to a prompt: what is each person\'s part?',
                            sortrow('AI engineer', 'Makes the change', 'Responsible', icon='code'),
                            sortrow('Product manager', 'Says it can go out', 'Accountable', icon='target'),
                            sortrow('Subject-matter expert', 'Checks the answers are right', 'Consulted', icon='person'),
                            sortrow('Platform engineer', 'Knows it is coming', 'Informed', icon='power'))),
    ],
    example=example('A RACI for the HR assistant', """# decision: ship a prompt fix
raci = {"AI engineer": "R",
        "product manager": "A",
        "HR advisor (SME)": "C",
        "platform engineer": "I"}
# exactly one A: one person decides"""),
    check=question(
        'The HR assistant starts giving a wrong answer about parental leave. Who confirms the fix gives the right answer?',
        [
            'An HR policy expert, the SME',
            'The platform engineer',
            'The finance team',
        ],
        answer=0,
        why='The subject-matter expert knows the policy, so they say what a right answer is. The platform engineer rolls the fix out, and finance watches the cost, but neither can judge the answer.',
    ),
    angle=angle(
        pattern='Exactly one Accountable, at least one Responsible',
        text='The big idea: an AI feature is never finished, so many people keep working on it together, and a RACI table makes clear who does the work and who decides. Your code goes through each decision in the table. It counts the people marked "A" and the people marked "R". A decision with anything other than exactly one "A", or with no "R", is a problem, so it adds that decision\'s name to a list. It returns the list in the order the decisions came. It is like a relay team: each leg needs exactly one runner holding the baton.',
        say='"An AI feature is never [[finished|started|tested::It keeps changing after launch.]], so the AI engineer, the subject-matter expert, platform, security and the product manager keep working on it [[together|in turn|alone::Not one after another.]], and every decision has exactly one person who [[decides|codes|watches::The Accountable one.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Check the RACI',
        topic='use cases',
        difficulty='easy',
        fn='raci_problems',
        prompt="""Your function gets `raci`, a dict. Each key is a decision, like `"ship a prompt fix"`. Each value is a dict of person to letter: `"R"` (does the work), `"A"` (makes the final call), `"C"` (asked first) or `"I"` (told after).

A decision is a problem if it doesn't have exactly one `"A"`, or if it has no `"R"`.

Return a list of the decisions that are problems, in the order they came. No problems gives `[]`.""",
        pattern='Count the letters for each decision, then test the rules.',
        target='one pass over the decisions and their people',
        realworld='Teams that build AI features write a light RACI for the decisions that matter, like shipping a fix or raising the budget, and revisit it as the team changes. Two people who both think they decide is a common cause of a slow, messy incident.',
        practice=practice(
            intro='Set up the team around the HR assistant: who owns what, who decides, and why nobody can walk away after launch.',
            explain='The big idea: an AI feature is never finished, so the people who build, run, decide and guard it keep working on it together, and each decision has exactly one person who makes the call. You saw that moving the team on after launch leaves nobody watching, that a team with no subject-matter expert can\'t say what a right answer is, that a RACI names one Accountable person, and that a small team can hold several roles as long as each has an owner.',
            pattern='Every kind of work has an owner',
            realworld='When an AI project starts at work, list the roles, put a name next to each, and write a short RACI for the decisions that matter. Check it again whenever someone joins or leaves.',
            gotchas=[
                ['Moving the team on after launch', 'An AI feature drifts and breaks as the world changes. Someone has to keep watching it and fixing it.'],
                ['No subject-matter expert', 'Engineers can build it, but only someone who knows the work can say what a right answer is.'],
                ['Two people who both decide', 'Name exactly one Accountable person for each decision, or an urgent fix waits while two people argue.'],
            ],
            asks=[
                ask('What is the risk?', ['Nobody watches it as its answers drift', 'None: it passed its evals at launch', 'The next release grows too big'], answer=0,
                    evidence=evidence('claim', who='The sponsor said', text='"The assistant is live. Let\'s move the team onto the next project and look at it again at the next release."'),
                    clue='What keeps changing after launch, even if the code doesn\'t?',
                    why='The model, the questions and the documents keep changing, so answers drift or break. Someone has to watch it weekly and be ready to fix it within hours.',
                    wrong=[None, 'Passing at launch says nothing about next month, when the questions and documents have changed.', 'The size of the next release isn\'t the risk. An unwatched assistant is.']),
                ask('Who is missing before anyone can say what a right answer is?', ['A subject-matter expert', 'Another AI engineer', 'The finance team'], answer=0,
                    evidence=evidence('code', title='Invited to the kickoff', text="""Product manager
AI engineer
Platform engineer"""),
                    clue='Who knows the HR policies themselves?',
                    why='Only someone who knows the work, here an HR advisor, can say whether an answer is right. Without them the evals measure nothing real.',
                    wrong=[None, 'More engineers can build more, but none of them knows the HR policies.', 'Finance sets the budget, not what a right answer is.']),
                ask('Two people each think they make the final call on whether a fix ships. What does a RACI change?', ['It names one Accountable person', 'It lets both of them decide', 'It removes the decision'], answer=0,
                    alone=True,
                    clue='How many people may be Accountable for one decision?',
                    why='Each decision has exactly one Accountable person. The other can be Consulted first, so an urgent fix doesn\'t wait while two people argue.',
                    wrong=[None, 'Two deciders is the problem a RACI exists to fix.', 'The decision still has to be made. A RACI says who makes it.']),
                ask('What do you say?', ['Fine: one person can hold several roles', 'We must hire one person per role', 'Then skip the roles nobody holds'], answer=0,
                    evidence=evidence('claim', who='The team lead said', text='"We are five people. We don\'t need all these roles."'),
                    clue='Is a role a person, or a kind of work that needs an owner?',
                    why='A small team can have one person as AI engineer and platform engineer. What matters is that each kind of work has an owner: skip security and privacy, and nobody owns where the data goes.',
                    wrong=[None, 'Roles are kinds of work, not head count. One person can hold several.', 'Skipping a role leaves its work with nobody. Give it to someone.']),
            ],
        ),
        starter="""def raci_problems(raci):
    # your code here
    pass
""",
        solution="""def raci_problems(raci):
    problems = []
    for decision in raci:
        letters = list(raci[decision].values())
        if letters.count("A") != 1 or "R" not in letters:
            problems.append(decision)
    return problems
""",
        cases=[
            case({"ship a prompt fix": {"AI engineer": "R", "product manager": "A", "SME": "C", "platform engineer": "I"},
                  "raise the budget": {"product manager": "A", "finance": "A", "AI engineer": "C"},
                  "pick the model": {"AI engineer": "R", "product manager": "C"}},
                 expected=["raise the budget", "pick the model"], sample=True),
            case({"ship a prompt fix": {"AI engineer": "R", "product manager": "A"}}, expected=[]),
            case({}, expected=[]),
        ],
        guided="""def raci_problems(raci):
    # Replace every ___ with real code, then run the tests.
    problems = []
    for decision in raci:
        # Step 1: everyone's letters for this decision.
        letters = list(raci[decision].values())
        # Step 2: exactly one A, and at least one R.
        if ___ or ___:
            problems.append(decision)
    return problems
""",
        fills=['letters.count("A") != 1', '"R" not in letters'],
        concepts=[
            [
                'values() of a dict',
                '`d.values()` gives every value; `list(...)` turns it into a list you can count.',
                """d = {"Ana": "R", "Bo": "A"}
list(d.values())   # ["R", "A"]""",
            ],
            [
                'count',
                '`letters.count("A")` says how many times "A" appears in the list.',
                '["A", "C", "A"].count("A")   # 2',
            ],
        ],
        byhand='"ship a prompt fix": one A and an R: fine. "raise the budget": two A\'s, and no R: a problem. "pick the model": an R but no A: a problem. Return ["raise the budget", "pick the model"].',
        why='Each person in each decision is looked at once, so the work grows with the size of the table.',
        gotchas=[
            [
                'Two Accountable people',
                'If two people both make the call, nobody does when it is urgent. Exactly one A per decision.',
            ],
            [
                'Nobody Responsible',
                'A decision with someone to approve it but nobody to do the work never happens. Give every decision an R.',
            ],
        ],
    ),
)

lesson(MODULE, 'gather_requirements',
    title='Gather the requirements',
    cards=[
        card('Requirements are gathered',
             'Nobody hands you a finished list of requirements. You draw them out of people: the real name is **requirements elicitation**, and most teams just say gathering. Your use case card is the first set of questions; these steps fill in the rest.',
             picture=steps(('people', 'Ask everyone with a stake', 'The users, the owner, and the teams who keep it safe and running.'),
                           ('chat', 'Ask about today', 'How the job is done now, with real examples of it.'),
                           ('listcheck', 'Ask the how-well questions', 'Reliable, secure, cheap, fast, and who runs it.'),
                           ('check', 'Read it back, then sort it', 'Check what you heard, and agree what is a Must.'),
                           decide=True)),
        card('Ask everyone with a stake',
             'A **stakeholder** is anyone who uses the system, pays for it, or has to keep it safe and running. Each one owns different requirements.',
             picture=sortby('Who would tell you?',
                            sortrow('What it must do', 'The people who will use it', 'What it does', icon='people'),
                            sortrow('What it may cost', 'The owner, who pays and decides', 'How well', look='dashed', icon='coin'),
                            sortrow('Where personal data may go', 'The privacy team', 'How well', look='dashed', icon='lock'),
                            sortrow('What happens if it is down', 'The platform team that runs it', 'How well', look='dashed', icon='power')),
             after='The how-well requirements mostly come from people who are not in the first meeting. That is why teams forget them.'),
        card('Ask about today, not wishes',
             '"What would you like?" gets a wish list. Ask about a real time instead, or sit with someone while they do the job, which is called **shadowing**. Collect 20 to 50 real past examples while you are there: they become your test set.',
             picture=rewrite(('What would you like it to do?', 'Walk me through the last time you did this'),
                             ('Would AI help you?', 'Show me where it takes the longest'),
                             ('It has to be fast', 'How long does it take today?')),
             after='Today\'s number is your **baseline**: if HR takes 8 minutes to answer now, "under 5 seconds" is a target you can check.'),
        card('Ask the how-well questions yourself',
             'Users talk about what it should do. Ask the how-well questions yourself, one per area, or nobody will.',
             picture=pillars('The HR assistant',
                             pillar('Reliability', 'power', 'What happens if it is down for an hour?'),
                             pillar('Security', 'lock', 'Who must not see this?'),
                             pillar('Cost Optimization', 'coin', 'What is one answer worth to you?', short='Cost'),
                             pillar('Operational Excellence', 'eye', 'Who notices and fixes it when it goes wrong?', short='Operations'),
                             pillar('Performance Efficiency', 'gauge', 'How fast, and for how many people at once?', short='Performance')),
             after='Add privacy too: where may personal data go? These five areas are the **pillars** of a well-architected review, two lessons on.'),
        card('Read it back, then sort it',
             'Write down what you heard and read it back to the people who said it. A gap is an **open question**, never a guess. Then sort by priority with **MoSCoW**: Must, Should, Could, and Won\'t this time. If everything is a Must, nothing is.',
             picture=piles(pile('Must', ['Answer policy questions', ('gauge', 'Under 5 seconds, 95 in 100'), ('lock', 'Personal data stays in the EU')]),
                           pile('Could', ['Answer in Spanish', 'Summarise each policy']))),
    ],
    example=example('Who to ask about the HR assistant', """# open question -> who answers
"what it must do"  -> users
"how fast"         -> users
"cost per answer"  -> owner
"where data goes"  -> privacy team
"if it is down"    -> not listed:
                      ask the owner"""),
    check=question(
        'The Head of HR says: "We need a chatbot for HR." What do you ask first?',
        [
            'Which chatbot product should we buy?',
            'What problem would it solve, and for whom?',
            'How soon can it go live for staff?',
        ],
        answer=1,
        why='"We need a chatbot" starts from the solution. Ask what job it does and for whom first: the requirements come from that, and so does whether it should be a chatbot at all.',
    ),
    angle=angle(
        pattern='Group the questions by who answers them',
        text='The big idea: requirements are gathered, not handed over, so before the interviews you list the open questions and who can answer each one. Your code makes an empty plan. For each open topic it looks up who answers it, or uses "owner" when nobody is listed, because someone still has to decide. The first time it meets a person it starts an empty list for them, then adds the topic. It returns the plan. It is like sorting post into pigeonholes by name: one hole per person, letters kept in the order they came.',
        say='"I ask everyone with a [[stake|title|laptop::Anyone who uses it, pays for it, or has to keep it safe.]], not just the users. I ask how the job works [[today|someday|ideally::Wishes make a wish list; the last real time makes requirements.]], and every answer gets a [[number|name|colour::"Fast" can\'t pass or fail; "under 5 seconds" can.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Plan Who to Ask',
        topic='use cases',
        difficulty='easy',
        fn='interview_plan',
        prompt="""Your function gets `topics`, a list of open questions (strings), and `owners`, a dict saying who answers each topic.

Return a dict with one entry per person: the list of topics to ask them, in the order the topics came.

A topic missing from `owners` goes to `"owner"`, the person who decides, because someone still has to answer it.

No topics gives `{}`.""",
        pattern='Group by a key; start its list the first time you meet it.',
        target='one pass over the topics',
        realworld='Before requirement interviews, teams list the open questions and who can answer each one, so every meeting has an agenda and nobody with a stake is forgotten.',
        practice=practice(
            intro='Gather the HR assistant\'s requirements the way an analyst does: ask the right people about today, then read back what you heard.',
            explain='The big idea: requirements are gathered, not handed over. You ask everyone with a stake about how the job is done today, and turn each answer into a number. You turned "make it fast" into a question about today\'s wait, found the privacy team missing from the first meeting, spotted the reliability question nobody had answered, and helped the owner pick real Musts instead of nine.',
            pattern='Ask everyone, about today',
            realworld='When you start an AI project, book short talks with the users, the owner, and the security, privacy and platform teams. Ask each about today, then send back what you heard for them to check.',
            gotchas=[
                ['Starting from the solution', '"We need a chatbot" skips the problem. Ask what job it does, for whom, and how it is done today.'],
                ['Only asking the users', 'Users know what it must do. Cost, privacy, security and uptime come from the owner and the teams who keep it safe and running.'],
                ['Everything is a Must', 'If all nine are Must, nothing can give when time runs short. Ask what the pilot could go live without.'],
            ],
            asks=[
                ask('What do you ask next?', ['How long do people wait for an answer today?', 'Which model is the fastest one we can use?', 'Can security wait until after the pilot?'], answer=0,
                    evidence=evidence('claim', who='The product manager said', text='"Make it fast, and it must be secure."'),
                    clue='"Fast" compared with what? Find out where things stand now.',
                    why='Today\'s wait is your baseline: if HR takes 8 minutes to answer now, "under 5 seconds" is a clear target. Then ask the same of "secure": secure against what, and for whom?',
                    wrong=[None, 'That picks a solution before you know the target. First find out how fast is fast enough.', 'Security is a requirement, not an extra. Ask what "secure" means to them instead.']),
                ask('You need to know where personal data may go. Who is missing?', ['The privacy team', 'More HR advisors', 'Nobody: the owner decides that'], answer=0,
                    evidence=evidence('code', title='Invited to the first meeting', text="""HR advisors      will use it
Head of HR ops   pays and decides"""),
                    clue='Who in the company sets the rules for personal data?',
                    why='Where personal data may go is the privacy team\'s call, and they are rarely in the first meeting. That is why privacy requirements turn up late, often just before launch.',
                    wrong=[None, 'The advisors know the job, not the rules for personal data.', 'The owner decides on the use case, but the rules for personal data belong to the privacy team.']),
                ask('Tomorrow you meet an HR advisor. Which question gets you real requirements?', ['What would you like the assistant to do?', 'Walk me through the last question you answered', 'Would an AI assistant help you in your job?'], answer=1,
                    alone=True,
                    clue='Which one gets a real story instead of a wish?',
                    why='The last real time shows the steps, the pages they search and where it is slow. "What would you like?" gets a wish list, and "would AI help?" gets a polite yes.',
                    wrong=['That gets a wish list. Ask about a real time it happened instead.', None, 'People say yes to be polite. It tells you nothing you can build or test.']),
                ask('You asked the how-well questions one by one. Which one has no answer yet?', ['What if it is down for an hour', 'How fast an answer has to be', 'Where personal data may go'], answer=0,
                    evidence=evidence('code', title='Your notes from the interviews', text="""how fast:       5 seconds, 95 in 100
cost:           under $2 an answer
personal data:  stays in the EU
who sees it:    HR staff only
at once:        200 people"""),
                    clue='Go area by area: reliable, secure, cheap, fast, run well. Which has no line?',
                    why='Nothing says what happens when it is down. That is the reliability question, and it is still open: write it down as one, and take it to the owner and the platform team.',
                    wrong=[None, 'Speed is there: 5 seconds for 95 in 100.', 'That is there: personal data stays in the EU.']),
                ask('What do you do?', ['Accept it: the owner decides the priorities', 'Ask which ones the pilot could go live without', 'Drop the last three to keep the pilot small'], answer=1,
                    evidence=evidence('claim', who='The owner said', text='"All nine requirements are Must."'),
                    clue='If every one is a Must, what gives when time runs short?',
                    why='If everything is a Must, nothing is. Asking what the pilot could go live without finds the real Musts; the rest become Should or Could. That is MoSCoW at work.',
                    wrong=['The owner does decide, but help them choose: if all nine are Must, nothing can give when time runs short.', None, 'Dropping lines yourself skips the owner. Ask them which ones can wait.']),
            ],
        ),
        starter="""def interview_plan(topics, owners):
    # your code here
    pass
""",
        solution="""def interview_plan(topics, owners):
    plan = {}
    for topic in topics:
        person = owners.get(topic, "owner")
        if person not in plan:
            plan[person] = []
        plan[person].append(topic)
    return plan
""",
        cases=[
            case(["what it must do", "how fast", "cost per answer", "where data goes", "if it is down"],
                 {"what it must do": "users", "how fast": "users", "cost per answer": "owner", "where data goes": "privacy team"},
                 expected={"users": ["what it must do", "how fast"], "owner": ["cost per answer", "if it is down"], "privacy team": ["where data goes"]},
                 sample=True),
            case([], {}, expected={}),
            case(["who must not see it"], {}, expected={"owner": ["who must not see it"]}),
            case(["uptime", "speed", "backups"], {"uptime": "platform team", "speed": "users", "backups": "platform team"},
                 expected={"platform team": ["uptime", "backups"], "users": ["speed"]}),
        ],
        guided="""def interview_plan(topics, owners):
    # Replace every ___ with real code, then run the tests.
    plan = {}
    for topic in topics:
        # Step 1: who answers it, or "owner" if nobody is listed.
        person = ___
        # Step 2: the first time you meet a person, start their list.
        if person not in plan:
            ___
        # Step 3: add the topic to their list.
        plan[person].append(topic)
    return plan
""",
        fills=['owners.get(topic, "owner")', 'plan[person] = []'],
        concepts=[
            [
                'get with a default',
                '`owners.get(topic, "owner")` gives the person listed for the topic, and `"owner"` if the topic is not there.',
                """owners = {"how fast": "users"}
owners.get("cost", "owner")   # "owner\"""",
            ],
            [
                'A dict of lists',
                'Each person maps to a list. Start an empty list the first time you see them, then `append` to it.',
                """plan = {}
plan["users"] = []
plan["users"].append("how fast")""",
            ],
            [
                'Checking a key first',
                '`person not in plan` is True the first time you meet that person, so you only start their list once.',
                '"users" in {"users": []}   # True',
            ],
        ],
        byhand='"what it must do": users, so start users\' list with it. "how fast": users again, add it. "cost per answer": owner, start the owner\'s list. "where data goes": privacy team, start theirs. "if it is down" is not in owners, so it goes to owner. Return {"users": ["what it must do", "how fast"], "owner": ["cost per answer", "if it is down"], "privacy team": ["where data goes"]}.',
        why='Each topic is looked up and added once, so the work grows with the number of topics.',
        gotchas=[
            [
                'Only asking the users',
                'Users know what it must do. Cost, privacy, security and uptime come from the owner and the teams who keep it safe and running, so put them on the plan too.',
            ],
            [
                'Starting the list every time',
                '`plan[person] = []` on every topic throws away the topics already there. Start the list only when the person is new.',
            ],
        ],
    ),
)

lesson(MODULE, 'split_requirements',
    title='Functional and non-functional requirements',
    cards=[
        card('What it does, and how well',
             'A **requirement** is something a system must do or be. Requirements come in two kinds. Picture a food delivery app.',
             picture=piles(pile('Functional', ['Order food', 'Track the driver', 'Pay by card'], sub='What it does'),
                           pile('Non-functional', [('gauge', 'Food arrives in 30 minutes'), ('lock', 'Card numbers kept safe'), ('people', 'Works in the Friday rush')],
                                sub='How well it does it', look='dashed')),
             after='**Functional** requirements are what the system does. **Non-functional** requirements are how well it does it: how fast, how safe, how cheap, how many people at once.',
             note=('Good to know: another name', 'Engineers also call non-functional requirements quality attributes.')),
        card('The test: watch it, or measure it?',
             'For each requirement, ask how you would check it. If you would check it by watching it happen, it is functional. If you would check it by measuring something, like time, cost or how many people, it is non-functional.',
             picture=sortby('How would you check it?',
                            sortrow('Track the driver', 'Watch it: open the map and see the driver move.', 'Functional', icon='eye'),
                            sortrow('Food arrives in 30 minutes', 'Measure it: time a hundred orders.', 'Non-functional', look='dashed', icon='gauge'),
                            sortrow('Card numbers kept safe', 'Measure it: you can\'t watch this in the app. A security check counts card numbers stored without protection, and the answer must be none.',
                                    'Non-functional', look='dashed', icon='lock')),
             after='Teams test them the same way: **functional testing** checks that it does each thing, and performance, load and security testing measure how well.'),
        card('Give it a number',
             '"Fast" can\'t pass or fail, but a number can. If you can\'t say yes or no after measuring, rewrite the requirement.',
             picture=rewrite(('fast', 'under 5 seconds, for 95 in 100 answers'), ('always up', 'working 99.9% of office hours, its **uptime**'),
                             ('cheap', 'under $2 per answer'), ('secure', 'only HR staff can see the answers'))),
        card('One sentence can hold both',
             'People often write both kinds in one line. Cut it in two, so each half can be checked on its own: one by watching, one by measuring.',
             picture=split(['Answer time-off questions', 'within 5 seconds'],
                           [tile('Answer time-off questions'), tile('Reply within 5 seconds', icon='clock', look='dashed')])),
        card('The HR assistant, sorted',
             'The HR assistant is an AI chatbot that answers staff questions about HR policy, like leave and expenses. Non-functional requirements are the ones teams forget, and they decide whether a working demo can go live. For AI the usual ones are speed, uptime, cost per answer, privacy (where personal data may go), security (who can see what) and how many people at once.',
             picture=piles(pile('Functional', ['R1 Answer policy questions', 'R3 Show the source page', 'R5 Hand hard questions to a person']),
                           pile('Non-functional', [('gauge', 'R2 5 seconds, 95 in 100'), ('lock', 'R4 Personal data stays in the EU'),
                                                   ('people', 'R6 200 people at once'), ('coin', 'R7 Under $2 an answer')], look='dashed'))),
        card('They choose the design',
             'Features rarely decide how a system is built. The how-well numbers do: they pick the model, where it runs, and how much capacity you pay for.',
             picture=sortby('What does it decide?',
                            sortrow('R7 Under $2 an answer', 'A smaller, cheaper model, not the biggest', 'The model', look='dashed', icon='coin'),
                            sortrow('R4 Personal data stays in the EU', 'Which region and model service you may use', 'Where it runs', look='dashed', icon='lock'),
                            sortrow('R6 200 people at once', 'Pay per use, or capacity reserved in advance', 'Capacity', look='dashed', icon='people')),
             after='The next lesson puts each non-functional requirement under a pillar of a well-architected review.'),
    ],
    example=example('How would you check it? The HR assistant', """# how would you check it?
"Show the source page"
#  watch it   -> functional
"Reply within 5 seconds"
#  measure it -> non-functional

# one line holding both: split it
"Answer within 5 seconds"
#  watch:   "Answer"
#  measure: "within 5 seconds"""),
    check=question(
        'Which of these is a non-functional requirement?',
        [
            'Draft a reply to each support ticket',
            'Send refund questions to the finance team',
            'Be available 99.9 percent of working hours',
        ],
        answer=2,
        why='You could watch the system do the first two. Availability you measure: how much of the time it stays up. So it is non-functional.',
    ),
    angle=angle(
        pattern='Sort by a list of how-well words',
        text='The big idea: functional requirements are what a system does and non-functional ones are how well it does it; asking whether you would check a line by watching or by measuring tells you which. A reviewer\'s quick first sort can look for words about speed, uptime, cost, security and scale. Your code makes two empty lists. For each requirement it lowercases the text and checks whether any word from the how-well list appears in it. If one does, the row goes in the non-functional list, otherwise in the functional list. It returns both lists, in their original order. It is like sorting post into bills and letters by looking for a price on the envelope; a person still checks the pile.',
        say='"I ask how I\'d check it. If I\'d [[watch|read|build::See it happen, like tapping a button.]] it happen, it\'s functional. If I\'d [[measure|guess|code::With a stopwatch, a bill or a count.]] it, it\'s non-functional, and it needs a [[number|name|owner::"Fast" can\'t pass or fail; "under 5 seconds" can.]] to pass or fail."',
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
            intro='Sort the HR assistant\'s requirements the way a reviewer does: for each one, ask whether you would check it by watching it happen or by measuring it.',
            explain='The big idea: functional requirements say what a system does, and non-functional ones say how well it does it. To tell them apart, ask: would I check this by watching it, or by measuring it? With that one question you saw the product manager\'s list said nothing about speed, cost or privacy, pulled "within 5 seconds" out of the time-off line, and turned "always up" into 99.9 percent uptime.',
            pattern='Watch it, or measure it?',
            realworld='When a team plans a pilot (a small first trial), someone will ask for the non-functional requirements. Bring each one with a number, so the trial can measure it and say pass or fail.',
            gotchas=[
                ['Forgetting the non-functional ones', 'A demo can answer every question and still not go live because it is too slow, too costly or sends personal data where it may not go. Write these down on day one.'],
                ['Nothing to measure', '"Fast" and "secure" can\'t pass or fail. Write "under 5 seconds for 95 in 100 answers" or "only HR staff can see answers".'],
                ['One line, both kinds', 'A sentence like "answer within 5 seconds" holds both. Split it, or the trial can check the answer and never time it.'],
            ],
            asks=[
                ask('Which kind is **R4**?', ['Functional: what the system does', 'Non-functional: how well it does it'], answer=1,
                    evidence=evidence('code', title='The HR assistant\'s requirements', text="""R1  Answer policy questions from the HR pages
R2  Reply within 5 seconds for 95 in 100 questions
R3  Show the source page for every answer
R4  Personal data never leaves the EU
R5  Hand hard questions to a person
R6  Serve 200 users at once
R7  Cost under $2 per answer"""),
                    clue='How would you check R4: by watching the assistant do something, or by checking where the data is stored?',
                    why='A user never sees where their data is stored, so you can\'t watch it. You check it by inspecting where the data lives, which is measuring. Where personal data may go is privacy: non-functional.',
                    wrong=['You can\'t watch this happen in the app. You check it by inspecting where the data is stored.', None]),
                ask('What is missing from the product manager\'s requirements?', ['Nothing: those three lines cover everything', 'How well it must do it: speed, privacy, cost', 'More features, like summarising each policy'], answer=1,
                    evidence=evidence('claim', who='The product manager said', text='"The requirements are done: it answers policy questions from the HR pages, shows the source page, and hands hard questions to a person."'),
                    clue='You could watch the assistant do all three. Which kind is that?',
                    why='All three are functional: you can watch it do each one. Nothing says how fast, how safe or how cheap, so a demo that does all three can still be too slow or too costly to go live.',
                    wrong=['Those say what it does. Nothing says how well, so there is nothing to measure.', None, 'It has enough to do. What is missing is how well.']),
                ask('R8 holds both kinds. Which part is the non-functional one?', ['Answer time-off questions', 'within 5 seconds', 'Neither: it is one requirement'], answer=1,
                    evidence=evidence('code', title='A new line', text='R8  Answer time-off questions within 5 seconds'),
                    clue='Which half would you watch, and which would you time with a stopwatch?',
                    why='"Within 5 seconds" is measured with a stopwatch, so it is the non-functional half. Split it into its own line so each half can be checked on its own.',
                    wrong=['You would check that half by watching it answer. That makes it functional.', None, 'It holds two: one you watch, one you measure. Split them.']),
                ask('How would you rewrite R9 so it can be measured?', ['The assistant should really always be up', '99.9 percent uptime in working hours', 'Run the assistant on a bigger server'], answer=1,
                    evidence=evidence('claim', who='A teammate added', text='"R9: The assistant should always be up."'),
                    clue='"Always" can\'t be measured. What share of the time, and when?',
                    why='A number turns a hope into something you can measure: it either stayed up 99.9 percent of working hours or it didn\'t.',
                    wrong=['Stronger words still can\'t be measured.', None, 'That is a way to build it, not how well it must work.']),
                ask('R10 sounds like something the assistant does. Which kind is it?', ['Functional: what the system does', 'Non-functional: how well it does it'], answer=1,
                    evidence=evidence('code', title='One more line', text='R10  Keep a record of every answer, for audits'),
                    clue='Could a user watch it happen? How would you check it?',
                    why='Users never see it. You check it by looking through the records later and counting that every answer is there, which is measuring. It is about how well the system is run, so it is non-functional. (Some teams file it as a feature; either way, it has to be on the list.)',
                    wrong=['A user can\'t watch it happen. You would check it by counting the records, so it is non-functional.', None]),
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
                {"id": "R7", "text": "Cost under $2 per answer"},
            ], expected=[
                [{"id": "R1", "text": "Answer policy questions from the HR pages"},
                 {"id": "R3", "text": "Show the source page for every answer"},
                 {"id": "R5", "text": "Hand hard questions to a person"}],
                [{"id": "R2", "text": "Reply within 5 seconds for 95 in 100 questions"},
                 {"id": "R4", "text": "Personal data never leaves the EU"},
                 {"id": "R6", "text": "Serve 200 users at once"},
                 {"id": "R7", "text": "Cost under $2 per answer"}],
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
                'A word list is a first pile, not the answer: "Show the cost of each request" is something users can watch it do, yet it holds the word cost. Ask "watch it or measure it?" of every line the list sorts.',
            ],
        ],
        machine=machine(bins=['functional', 'non_functional'], who=['what it must do', 'how well it must do it'], label_field='id'),
    ),
)

lesson(MODULE, 'well_architected',
    title='A well-architected review',
    checked='2026-10-15',
    sources=[source('Azure Well-Architected Framework workloads', 'https://learn.microsoft.com/azure/well-architected/workloads')],
    cards=[
        card('Five questions hold up a design',
             'A **well-architected review** checks a design before you build it. Microsoft\'s **Azure Well-Architected Framework** asks five questions, one per **pillar**. Ask all five of every design.',
             picture=pillars('Your design',
                             pillar('Reliability', 'power', 'What happens when something it depends on breaks, like the model being down or out of quota?'),
                             pillar('Security', 'lock', 'Who could see or do something they shouldn\'t? For example through a **prompt injection**: text in a message that tricks the model into ignoring its rules.'),
                             pillar('Cost Optimization', 'coin', 'What makes the bill grow?', short='Cost'),
                             pillar('Operational Excellence', 'eye', 'Would you notice it going wrong, and can you test and release changes safely?', short='Operations'),
                             pillar('Performance Efficiency', 'gauge', 'Does it stay fast at the busiest minute?', short='Performance'))),
        card('Why review before you build',
             'A review happens while the design is still on paper, because that is when a gap is cheapest to fix.',
             picture=steps(('pencil', 'Found on paper', 'A missing privacy rule costs a conversation.'),
                           ('code', 'Found while building', 'It costs rework on what is already built.'),
                           ('rocket', 'Found after launch', 'It costs a rebuild, or a privacy incident.'))),
        card('Requirements rest on the pillars',
             'Your non-functional requirements are the pillars\' targets: each one from the last lesson answers one pillar\'s question. A pillar with nothing on it is a question nobody has answered yet.',
             picture=pillars('HR assistant',
                             pillar('Reliability', 'power', 'So the review\'s first question is: what does the assistant do when the model is down?', open=True),
                             pillar('Security', 'lock', 'R4: personal data stays in the EU.', chips=['R4 EU']),
                             pillar('Cost Optimization', 'coin', 'R7: under $2 per answer.', short='Cost', chips=['R7 $2']),
                             pillar('Operational Excellence', 'eye', 'R10: a record of every answer.', short='Operations', chips=['R10 log']),
                             pillar('Performance Efficiency', 'gauge', 'R2: 5 seconds for 95 in 100. R6: 200 people at once.', short='Performance', chips=['R2 5 s', 'R6 200']),
                             list_questions=False)),
        card('Pillars pull against each other',
             'A second copy of the app keeps it up when one copy fails, and doubles the bill.',
             picture=seesaw(('Reliability', 'two copies: stays up'), ('Cost', 'twice the bill'), caption='A person chooses the balance, and writes down why.'),
             after='That is why the framework says a workload should be "just as reliable" and "just as secure" as it needs to be. A pilot rarely needs the most.'),
        card('A model drafts, a person decides',
             'A model can draft the review from your use case card, if the **review prompt** sets rules. Then you check every claim against the card, because a model fills gaps with confident guesses.',
             picture=steps(('listcheck', 'The use case card', 'Every field goes in the prompt. A blank one says "not written", so the gap shows.'),
                           ('bot', 'The model\'s draft', 'A finding per pillar, each quoting the card. Where the card says nothing: "Unknown", and a question.'),
                           ('person', 'A person decides', 'Check each quote against the card. Go or no-go is a business call, never the model\'s.'),
                           decide=True),
             after='Databricks publishes its own version for the lakehouse, with two more pillars: **data and AI governance** (who may use which data and models) and **interoperability and usability** (open formats, so other tools and people can use the data).'),
    ],
    example=example('The HR assistant, pillar by pillar', """# pillar: its question
#   -> what the card says
Reliability: model down?
  -> not written: ask
Security: who sees what?
  -> R4: data stays in the EU
Cost: what grows the bill?
  -> R7: under $2 an answer
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
            explain='The big idea: the five pillars are five questions to ask of every design, and they pull against each other, so a review writes down each trade and who chose it. Running two copies of the assistant helps Reliability and doubles the bill. When a model drafts the review, it gets the whole card, with "not written" in any blank box, and it drafts findings only: the "safe to build" line is a person\'s call, and a finding counts when it quotes a line you can find on the card.',
            pattern='Five questions, then a person decides',
            realworld='Architecture reviews at work use these pillar names. Bring your requirements sorted under them; the empty pillar is your first question.',
            asks=[
                ask('You want to ask "Can it handle the busiest minute?" Which pillar does it go under?', ['Reliability', 'Performance Efficiency', 'Cost Optimization'], answer=1,
                    alone=True,
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
    cards=[
        card('Good enough, measured',
             '**Fit for purpose** means good enough for this job, measured on real examples, against **acceptance criteria** agreed before the trial: the lines a result has to reach to pass, like the pass mark in an exam. Not perfect, and not "it looked good in the demo".',
             picture=rewrite(('It looked good in the demo', '80 in 100 right on last month\'s 200 questions'), ('Fast enough', 'Under 5 seconds for 95 in 100'), ('Cheap', 'Under $2 a finished task'))),
        card('Each criterion checks a requirement',
             'Set four acceptance criteria when you write the card, and agree each one with the people who own it. Each one checks one of your requirements.',
             picture=sortby('What does it check, and who sets it?',
                            sortrow('Quality: 80 in 100 answers right', 'R1 Answer policy questions. The owner and the users agree it.', 'Functional', icon='check'),
                            sortrow('Must-pass: the dangerous cases it must never get wrong', 'The card\'s wrong-answer box, like showing one person\'s data to another. The owner, privacy and security agree them.', 'Functional', icon='lock'),
                            sortrow('Speed: how many seconds a person will wait', 'R2 5 seconds, 95 in 100: the Performance Efficiency pillar. The users say how long they will wait.', 'Non-functional', look='dashed', icon='gauge'),
                            sortrow('Cost: the cost per finished task must beat today\'s', 'R7 Under $2 an answer: the Cost Optimization pillar. The owner, who pays.', 'Non-functional', look='dashed', icon='coin')),
             after='Speed and cost are non-functional, each on a pillar from the review. Quality and must-pass measure the functional requirement itself: an AI does its job right only some of the time, so with AI even what it does has to be measured.'),
        card('Go, fix or stop',
             'After the pilot, the call, often called a go/no-go decision, is one of three. Writing the acceptance criteria down first stops anyone from moving them to fit the result.',
             picture=sortby('What is the call?',
                            sortrow('Every criterion met', 'Go: it does the job well enough.', 'Go', icon='check'),
                            sortrow('One criterion just missed, like 5.5 seconds against 5', 'Improve that one, then test again.', 'Fix', icon='reset'),
                            sortrow('A must-pass case failed, more than one criterion was missed, or a miss is far off', 'However good the averages look.', 'Stop', icon='x'))),
        card('The tools behind each criterion',
             'The next lessons give you the tools behind each criterion.',
             picture=steps(('chart', 'Foundations', 'What an LLM is, then how to measure quality honestly.'),
                           ('coin', 'Pricing', 'The cost per finished task, and what it saves.'),
                           ('flask', 'Evaluate', 'The same check again, on every new version.'))),
    ],
    example=example('Pilot results against the acceptance criteria', """criteria = {"quality": 0.80, "seconds": 5,
            "cost": 2.00}
pilot    = {"quality": 0.78, "seconds": 4,
            "cost": 1.87, "must_pass_failures": 0}
# cost and speed met; quality 2 points short
# and within 5 points of its criterion: fix it,
# then test again"""),
    check=question(
        'The pilot scores 86 in 100 against a criterion of 80, passes every must-pass case and costs less than its criterion, but takes 5.5 seconds against a 5-second criterion. What is the honest call?',
        [
            'Go: half a second is close enough',
            'Fix: speed it up, then test again',
            'Stop: it missed the speed criterion',
        ],
        answer=1,
        why='Only one criterion is missed, and only just: half a second over. That is worth improving and testing again. Calling it a go would quietly move the criterion after seeing the result.',
    ),
    angle=angle(
        pattern='Must-pass first, then count the misses',
        text='The big idea: decide fit for purpose against acceptance criteria written down before the trial, and treat a failed must-pass case as an automatic stop. Your code first returns "stop" if any must-pass case failed. Then it checks quality, speed and cost against their criteria, noting each one missed and whether the miss is close: quality within 0.05 of the criterion, speed or cost no more than 1.2 times the criterion. No misses means "go". Exactly one close miss means "fix". Anything else means "stop". It is like a driving test: one serious fault fails you, a small slip means practise and retake.',
        say='"I agree the acceptance criteria [[before|after|during::Setting them once you see results lets you move them.]] the pilot. A failed must-pass case means [[stop|a warning|a retest::Must-pass means exactly that.]], all criteria met means go, and one near miss means fix it and [[test again|release it|give up::A near miss gets another try, not a pass.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Go, Fix or Stop',
        topic='use cases',
        difficulty='medium',
        fn='pilot_verdict',
        prompt="""Your function gets two dicts:

- `results`: the pilot's numbers, with `"quality"` (share right, like `0.78`), `"seconds"` (time per answer), `"cost"` (dollars per finished task) and `"must_pass_failures"` (how many must-pass cases it got wrong).
- `criteria`: the agreed acceptance criteria, with `"quality"`, `"seconds"` and `"cost"`.

Decide like this:

1. If `"must_pass_failures"` is more than 0, return `"stop"`.
2. Quality misses its criterion if it is below it. Seconds or cost miss theirs if they are above them.
3. A miss is close if quality is at most 0.05 below its criterion, or seconds or cost are at most 1.2 times theirs.
4. No criteria missed: return `"go"`. Exactly one criterion missed, and that miss is close: return `"fix"`. Otherwise return `"stop"`.""",
        pattern='Stop on a must-pass failure, then count the misses.',
        target='a few checks, no loops',
        realworld='Pilots are usually judged go, fix or stop against acceptance criteria agreed up front. Writing the rule in code keeps the decision the same however the results make people feel.',
        practice=practice(
            intro='Judge four pilots against the acceptance criteria agreed before they started: go, fix or stop.',
            explain='The big idea: decide fit for purpose against acceptance criteria written down before the trial, and a failed must-pass case is an automatic stop. Pilot 1 had great averages and one must-pass failure: stop. Pilot 2 missed only speed, by half a second: fix and retest. Pilot 3 met every criterion exactly: go, because meeting a criterion is meeting it. Pilot 4 was $1 over the cost criterion, and raising the criterion to fit it would be deciding after the result.',
            pattern='Must-pass first, then the agreed acceptance criteria',
            realworld='At the end of a pilot you\'ll be in the go, fix or stop meeting. Check the must-pass cases first, then each criterion exactly as it was written before the trial, so the call stays the same however the results feel.',
            asks=[
                ask('Pilot 1 looks great on quality, speed and cost. What\'s the call?', ['Go: roll it out', 'Fix: improve and retest', 'Stop: end the pilot'], answer=2,
                    evidence=evidence('code', title='Pilot 1 against the acceptance criteria', text="""criteria = {"quality": 0.80, "seconds": 5,
            "cost": 2.00}
pilot    = {"quality": 0.95, "seconds": 2,
            "cost": 0.50, "must_pass_failures": 1}"""),
                    clue='Read must_pass_failures before you look at the averages.',
                    why='A must-pass case is one it must never get wrong. One failure ends the pilot on its own, however good the averages look.',
                    wrong=['Great averages can hide one dangerous mistake. Look at must_pass_failures.', 'Fix is for a near miss on a criterion. A failed must-pass case is not a near miss.', None]),
                ask('What\'s the call for pilot 2?', ['Go: roll it out', 'Fix: improve and retest', 'Stop: end the pilot'], answer=1,
                    evidence=evidence('code', title='Pilot 2 against the acceptance criteria', text="""criteria = {"quality": 0.80, "seconds": 5,
            "cost": 2.00}
pilot    = {"quality": 0.82, "seconds": 5.5,
            "cost": 1.00, "must_pass_failures": 0}"""),
                    clue='Only one criterion is missed. A miss on speed is close if it is no more than 1.2 times the criterion: 6 seconds here.',
                    why='Speed is the only miss, and 5.5 seconds is within 6, so it is close. Make it faster, then test again.',
                    wrong=['5.5 seconds is over the 5-second criterion, so one criterion is missed.', None, 'It is one criterion, and only just missed. That is worth another try.']),
                ask('What\'s the call for pilot 3?', ['Go: roll it out', 'Fix: improve and retest', 'Stop: end the pilot'], answer=0,
                    evidence=evidence('claim', who='A teammate said', text='"Pilot 3: quality exactly 0.80, exactly 5 seconds, $1.20 a task, no must-pass failures. That only just scrapes through, so let\'s call it a fix to be safe."'),
                    clue='A criterion is missed only when quality falls under it, or speed or cost is above it. Is any number past its criterion?',
                    why='Meeting a criterion exactly is meeting it. Calling it a fix would quietly move the criterion after seeing the result, just upwards this time.',
                    wrong=[None, 'Fix is for a missed criterion. Which one did it miss?', 'Nothing failed: no must-pass failures and no missed criteria.']),
                ask('What do you do?', ['Go: raise the cost criterion to $3, still cheaper than by hand', 'Fix: one criterion missed, so cut the cost and retest', 'Stop: it is far over the agreed cost criterion'], answer=2,
                    evidence=evidence('claim', who='The sponsor said', text='"Pilot 4 costs $3.00 a task against the $2.00 cost criterion, but quality and speed are well inside, and it\'s still cheaper than doing it by hand. Raise the cost criterion to $3 and call it a go."'),
                    clue='Use the same rule as for speed: how far over $2.00 may a near miss go? And when were the criteria agreed?',
                    why='$3.00 is well past $2.40, so it is not a near miss, and raising the criterion after seeing the result is moving it to fit. If the cost case really has changed, agree new acceptance criteria before the next pilot.',
                    wrong=['Change the criterion once you see the result and the criterion meant nothing.', 'Fix is for a near miss. $3.00 is far past $2.40.', None]),
            ],
        ),
        starter="""def pilot_verdict(results, criteria):
    # your code here
    pass
""",
        solution="""def pilot_verdict(results, criteria):
    if results["must_pass_failures"] > 0:
        return "stop"
    missed = []
    close = True
    if results["quality"] < criteria["quality"]:
        missed.append("quality")
        if results["quality"] < criteria["quality"] - 0.05:
            close = False
    if results["seconds"] > criteria["seconds"]:
        missed.append("seconds")
        if results["seconds"] > criteria["seconds"] * 1.2:
            close = False
    if results["cost"] > criteria["cost"]:
        missed.append("cost")
        if results["cost"] > criteria["cost"] * 1.2:
            close = False
    if len(missed) == 0:
        return "go"
    if len(missed) == 1 and close:
        return "fix"
    return "stop"
""",
        cases=[
            case({"quality": 0.78, "seconds": 4, "cost": 1.87, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="fix", sample=True),
            case({"quality": 0.86, "seconds": 3, "cost": 1.5, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="go"),
            case({"quality": 0.95, "seconds": 2, "cost": 0.5, "must_pass_failures": 1}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="stop"),
            case({"quality": 0.7, "seconds": 4, "cost": 1.0, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="stop"),
            case({"quality": 0.82, "seconds": 5.5, "cost": 1.0, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="fix"),
            case({"quality": 0.78, "seconds": 5.5, "cost": 1.0, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="stop"),
            case({"quality": 0.9, "seconds": 3, "cost": 3.0, "must_pass_failures": 0}, {"quality": 0.8, "seconds": 5, "cost": 2.0}, expected="stop"),
        ],
        guided="""def pilot_verdict(results, criteria):
    # Replace every ___ with real code, then run the tests.
    # Step 1: any must-pass failure stops it.
    if results["must_pass_failures"] > 0:
        return "stop"
    missed = []
    close = True
    # Step 2: quality below its criterion is a miss.
    if results["quality"] < criteria["quality"]:
        missed.append("quality")
        if results["quality"] < criteria["quality"] - 0.05:
            close = False
    # Step 3: too slow is a miss.
    if results["seconds"] > criteria["seconds"]:
        missed.append("seconds")
        if results["seconds"] > criteria["seconds"] * 1.2:
            close = False
    # Step 4: too costly is a miss.
    if ___:
        missed.append("cost")
        if results["cost"] > criteria["cost"] * 1.2:
            close = False
    # Step 5: decide.
    if len(missed) == 0:
        return "go"
    if ___:
        return "fix"
    return "stop"
""",
        fills=['results["cost"] > criteria["cost"]', 'len(missed) == 1 and close'],
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
        byhand='No must-pass failures. Quality 0.78 is below 0.80: missed, and 0.78 is not below 0.75, so still close. Seconds 4 is not above 5. Cost 1.87 is not above 2.00. One miss, and it is close: return "fix".',
        why='A handful of comparisons, whatever the numbers.',
        gotchas=[
            [
                'Moving the criteria after the results',
                'If 78 in 100 suddenly becomes "good enough" once you see it, the criterion meant nothing. Write the acceptance criteria on the card before the pilot starts.',
            ],
            [
                'Averaging away a dangerous mistake',
                'A high overall score can hide one serious failure. Keep the dangerous cases as must-pass checks that stop the project on their own.',
            ],
        ],
    ),
)
