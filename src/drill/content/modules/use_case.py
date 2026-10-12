"""Use case and fit: pick an AI use case worth doing, write it down, and decide whether it is fit for purpose."""

from drill.content.model import angle, case, example, exercise, lesson, machine, module, question, sort_task

MODULE = module('use-case', 'Use case and fit', 'Pick an AI use case worth doing, write it down, and decide whether it is fit for purpose.')

lesson(MODULE, 'use_case_score',
    title='Is this a good AI use case?',
    learn=[
        "Most AI projects that fail went wrong before any code: they started from the technology (\"we need an agent\") instead of a problem. Microsoft's Cloud Adoption Framework starts with **business problems**: where results miss expectations, or people repeat the same work. Then write the use case in one line, **\"Help [who] [do what] so [a number] improves\"**, and check the task happens often enough to matter.",
        "Next, three **gates**. If a fixed rule can do the job, write the rule: it is cheaper and never wrong. If there are no past examples with right answers, you cannot test it. If a wrong answer causes real harm and nobody checks, AI must not decide it. Also choose **automate or augment**: Google's People + AI Guidebook automates tasks that are tedious, need scale and have an agreed right answer, and keeps people in charge where they value the work or disagree on the answer. Most good first projects augment: AI drafts, a person decides.",
        "Ideas that pass the gates go on a **map** with two axes, as in Microsoft's business, experience and technology framework. **Value**: what the problem costs and how much the business cares. **Doable**: the data is ready, AI suits the task, and the team can change how it works. High value and doable: **accelerate** to a pilot. High value, not doable yet: **research**, usually fixing the data first. Doable but small: **incubate**, a safe way to learn. Neither, or failed a gate: **shelve**.",
        "Keep the two axes apart rather than adding scores together: a risky, valuable idea and a safe, trivial one can add up to the same total. Where an idea lands tells you what to do next.",
    ],
    example=example('Six ideas on the map', """             hard to do       doable
high value   research:        accelerate:
             contract review  HR policy answers
low value    shelve:          incubate:
             staffing         meeting summaries
             forecast
failed a gate, so shelved:
  loan approvals (harm, nobody checks)
  date formats (a rule does it)"""),
    check=question(
        'Reviewing contracts for risk would save a lot of lawyer time, but past contracts are not labelled and the legal team has not agreed what "risky" means. Where does it go?',
        [
            'Accelerate: the value is high',
            'Research: valuable, but the data and the definition are not ready',
            'Shelve: AI cannot read contracts',
        ],
        answer=1,
        why='The value is real, but it is not doable yet: there is nothing labelled to test on and no agreed right answer. Research means fixing that first, then looking again.',
    ),
    angle=angle(
        pattern='Gates first, then the map',
        text='The big idea: vet an AI idea by starting from a real problem, ruling it out at once if a rule could do it, there is nothing to test on, or a wrong answer would do harm unchecked, and then placing it by value and how doable it is. The order matters. The gates come first, because a valuable idea that does harm unchecked is still shelved. Then two separate questions, value and doable, pick one of four corners: both high is accelerate, high value only is research, doable only is incubate, and neither is shelve. It is like sorting post into four trays by two questions, after binning the junk. In Python the same steps are four empty lists, one if for the gate, and if, elif and else for the corners.',
        say='"I start from a business problem and write the use case in one line. I rule it out if a rule could do it, there is nothing to test on, or a wrong answer would do harm unchecked. Then I place it by value and how doable it is, and pilot the valuable, doable ones first."',
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
        ],
        sort=sort_task(
            intro="Six ideas came in. Check the gates first, then how valuable and how doable each one is. Tap where it goes, or drag it there.",
            bins=[
                ('research', 'Research', 'valuable, not doable yet'),
                ('accelerate', 'Accelerate', 'valuable and doable: pilot it'),
                ('shelve', 'Shelve', 'small, and hard to do'),
                ('incubate', 'Incubate', 'doable but small: learn on it'),
                ('gate', 'Failed a gate', 'a rule does it, nothing to test on, or harm nobody checks'),
            ],
            items=[
                {'name': 'Rejecting job applicants', 'say': 'Reads CVs and sends rejections on its own. Nobody looks before they go out.',
                 'bin': 'gate', 'why': 'A wrong rejection harms a real person, and nobody checks. That fails the harm gate, however much time it saves.',
                 'value': 'high', 'doable': 'high', 'gate': 'harm, nobody checks'},
                {'name': 'Customer email replies', 'say': 'Support answers 3,000 similar emails a month. Past replies are rated, and an agent checks every draft before it is sent.',
                 'bin': 'accelerate', 'why': 'Lots of repeated work, rated past replies to test on, and a person checks each draft. Valuable and doable: pilot it.',
                 'value': 'high', 'doable': 'high', 'gate': ''},
                {'name': 'Naming scanned files', 'say': "Suggests names for scanned files in one team's drive. Easy to try, and saves a few minutes a week.",
                 'bin': 'incubate', 'why': 'Doable, but small. A safe first project to learn on, not one to bet a budget on.',
                 'value': 'low', 'doable': 'high', 'gate': ''},
                {'name': 'Spotting fraud in expenses', 'say': 'Would save auditors weeks. Past claims were checked, but the records sit in three old systems, and audits would have to change how they work.',
                 'bin': 'research', 'why': 'Valuable, but not doable yet: the data has to be pulled together and the team has to agree to work differently. Fix that first, then look again.',
                 'value': 'high', 'doable': 'low', 'gate': ''},
                {'name': 'Busy meeting rooms', 'say': 'Guesses which meeting rooms will be busy next year. Few people asked for it, and bookings live in three systems.',
                 'bin': 'shelve', 'why': 'Small value and hard to do. Shelve it and spend the effort elsewhere.',
                 'value': 'low', 'doable': 'low', 'gate': ''},
                {'name': 'Currency on invoices', 'say': "Converts invoice amounts into dollars using today's exchange rate.",
                 'bin': 'gate', 'why': 'Amount times rate is a fixed rule. Write the rule: it is cheaper than AI and never wrong.',
                 'value': 'low', 'doable': 'high', 'gate': 'a rule does it'},
            ],
        ),
        machine=machine(bins=['research', 'accelerate', 'shelve', 'incubate'], who=['high value, hard to do yet', 'high value, doable: pilot it', 'low value, or failed a gate', 'doable but small: learn on it'], label_field='id'),
    ),
)

lesson(MODULE, 'use_case_card',
    title='Write the use case down',
    learn=[
        'Before building, write the use case on one page, a **use case card**. It makes everyone agree on the same job, and it lists what the trial must measure.',
        "A card answers ten questions, shaped like the **AI Canvas** from the economists behind *Prediction Machines*, which treats AI as cheap prediction inside a decision. **Who** uses it and the **task**. The **decision**: what the AI predicts or drafts, from what input. The **action**: what happens next, and who does it. How it is done **today**, and its cost. **Success**, as a number. What a **wrong answer** costs, and who catches it. The **data** to test on. The **feedback**: how real outcomes flow back to improve it. And the **owner** who decides.",
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
            'Use AI to improve the HR experience',
            'Employees will find it much faster',
            '80 in 100 draft answers approved without edits, on 200 past questions',
        ],
        answer=2,
        why='Only the last one names a number and the questions you will check it on, so a trial can say yes or no. The others are hopes, not measures.',
    ),
    angle=angle(
        pattern='Check every field, then the number',
        text='The big idea: a use case card answers ten questions on one page, and a blank line, or a success line with no number, is an open question to settle before building. Your code goes through the ten field names in order. For each it reads the card\'s value, or an empty string if the field is missing, and strips spaces. A blank value is a gap. For the success field it also checks the text has at least one digit, because success you cannot count is a gap too. It returns the gaps in the same order. It is like checking a form before you post it: every box filled, and the amount written as a number.',
        say='"I write the use case on one page: who and the task, the decision the AI makes and the action that follows, today\'s cost, success as a number, the cost of a wrong answer, the test data, how feedback improves it, and the owner. Any blank is a question to answer first."',
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
            case({'user': '  ', 'task': 'triage tickets', 'decision': 'which team gets the ticket', 'action': 'the ticket is routed; the team can bounce it back', 'today': '2 minutes each', 'success': '90% routed right', 'wrong_answer': 'rerouted by hand', 'data': '', 'feedback': 'bounced tickets are relabelled', 'owner': 'IT lead'}, expected=['user', 'data']),
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
        'A use case turns into two kinds of requirement. **Functional** requirements say what it must do: answer policy questions, show the source, hand hard questions to a person. **Non-functional** requirements say how well it must do it: how fast, how available, how secure, how much it may cost.',
        'Non-functional requirements are the ones teams forget, and they decide whether a working demo can go live. Common ones for AI: speed (seconds per answer), availability (uptime), cost per finished task, privacy (where personal data may go), security (who can see what), how many users at once, and audit (a record of every answer).',
        "Microsoft's Well-Architected Framework says every workload needs both kinds, written down and put in order of priority, and the next lesson checks them against its pillars. Give each non-functional requirement a number, like \"under 5 seconds for 95 in 100 answers\", so the pilot can test it.",
    ],
    example=example('The HR assistant, sorted', """# what it must do: functional
"Answer policy questions from the HR pages"
"Show the source page for every answer"
# how well: non-functional
"Reply within 5 seconds for 95 in 100"
"Keep personal data inside the EU region"
"Cost under $1 per finished answer\""""),
    check=question(
        'Which of these is a non-functional requirement?',
        [
            'Draft a reply to each support ticket',
            'Send refund questions to the finance team',
            'Be available 99.9 percent of working hours',
        ],
        answer=2,
        why='The first two say what the system does. Availability says how well it must keep doing it, which makes it non-functional.',
    ),
    angle=angle(
        pattern='Sort by a list of how-well words',
        text='The big idea: functional requirements say what a system does and non-functional ones say how well, and a first sort can look for words about speed, uptime, cost, security and scale. Your code makes two empty lists. For each requirement it lowercases the text and checks whether any word from the how-well list appears in it. If one does, the row goes in the non-functional list, otherwise in the functional list. It returns both lists, in their original order. It is like sorting post into bills and letters by looking for a price on the envelope; a person still checks the pile.',
        say='"I split requirements into what it must do and how well it must do it, and I give every how-well requirement a number the pilot can test, like under 5 seconds for 95 in 100 answers."',
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
                {"id": "R4", "text": "Keep personal data inside the EU region"},
                {"id": "R5", "text": "Hand hard questions to a person"},
                {"id": "R6", "text": "Serve 200 users at once"},
                {"id": "R7", "text": "Cost under $1 per finished answer"},
            ], expected=[
                [{"id": "R1", "text": "Answer policy questions from the HR pages"},
                 {"id": "R3", "text": "Show the source page for every answer"},
                 {"id": "R5", "text": "Hand hard questions to a person"}],
                [{"id": "R2", "text": "Reply within 5 seconds for 95 in 100 questions"},
                 {"id": "R4", "text": "Keep personal data inside the EU region"},
                 {"id": "R6", "text": "Serve 200 users at once"},
                 {"id": "R7", "text": "Cost under $1 per finished answer"}],
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
        ],
        machine=machine(bins=['functional', 'non_functional'], who=['what it must do', 'how well it must do it'], label_field='id'),
    ),
)

lesson(MODULE, 'well_architected',
    title='A well-architected review',
    learn=[
        "Before you build, check the design against a **well-architected framework**: a checklist of what good systems need, from the cloud providers. Microsoft's has five **pillars**. **Reliability**: it keeps working when a model or a service fails. **Security**: data and actions are protected. **Cost Optimization**: you know what drives the cost and pay only for what you use. **Operational Excellence**: you can see what it does, test it and release safely. **Performance Efficiency**: it stays fast as use grows.",
        "Microsoft's guidance for AI workloads applies every pillar to both the functional and the non-functional requirements. For AI that means questions like: what happens when the model endpoint is down or out of quota? Can a prompt injection make it leak data? Do you trace every answer? Can it handle the busiest minute? Databricks adds two pillars of its own, **data and AI governance** (who may use which data and models) and **interoperability and usability**.",
        'A quick way to start a review is to ask a model to draft it from your use case card. A good **review prompt** gives the whole card, asks each pillar\'s questions in turn, and sets rules: back every finding with a line from the card, write "Unknown" and a question when the card does not say, give each pillar a risk, and leave the decision to a person.',
        "Then read the draft like a reviewer, not a fan. Check every claim against the card, because a model will fill gaps with confident guesses. The Unknowns are your next questions for the owner. The framework itself says a system only needs to be \"just as reliable\" and \"just as secure\" as it needs to be, so a person decides which risks are fine for a pilot.",
    ],
    example=example('The shape of a review prompt', """Review this AI use case against the Well-Architected pillars.

Use case card:
- user: HR team
- owner: not written

## Reliability
- What happens if the model is down?

Rules:
- Base every finding on the card ...
- If the card does not say, write Unknown ..."""),
    check=question(
        'A model drafts a review that says "Security: low risk, data is encrypted". The card never mentions encryption. What should you do?',
        [
            'Accept it: the model knows how these systems are usually built',
            'Treat it as unknown and ask the owner how data is protected',
            'Drop the Security pillar from the review',
        ],
        answer=1,
        why='The claim is not backed by the card, so it is a guess. A good review prompt asks the model to write Unknown in that case, and the open question goes to the owner.',
    ),
    angle=angle(
        pattern='Card, then pillars, then rules',
        text='The big idea: an AI-drafted review is only as good as its prompt, so the prompt gives the whole use case card, asks each pillar\'s questions, and sets rules that stop the model guessing or deciding. Your code builds the prompt as a list of lines. It starts with the task and the card, writing "not written" for any blank field so the gap is visible. Then for each pillar it adds a heading and its questions, and at the end the rules. It joins the lines with new lines. It is like a briefing pack for a reviewer: the facts, the questions to answer, and how to answer them.',
        say='"I draft a well-architected review by giving a model the whole use case card, each pillar\'s questions and strict rules: back findings with the card, mark unknowns as questions, rate the risk, and leave the decision to a person. Then I check every claim myself."',
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
        ],
    ),
)

lesson(MODULE, 'fit_for_purpose',
    title='Is it fit for purpose?',
    learn=[
        '**Fit for purpose** means good enough for this job, measured on real examples, against bars agreed before the trial. Not perfect, and not "it looked good in the demo".',
        'These bars are your non-functional requirements, and the review shows which pillars they protect. Set four when you write the card. **Quality**: like 80 in 100 answers right. **Must-pass**: the dangerous cases it must never get wrong. **Speed**: how many seconds a person will wait. **Cost**: the cost per finished task must beat today\'s cost.',
        'After the pilot, the call is one of three. **Go**: every bar met. **Fix**: one bar just missed, so improve that and test again. **Stop**: a must-pass case failed, or it is far off. Writing the bars down first stops anyone from moving them to fit the result.',
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
        'The pilot scores 78 in 100 against a bar of 80, passes every must-pass case, and meets the speed and cost bars. What is the honest call?',
        [
            'Go: it is close enough',
            'Fix: improve quality, then test again',
            'Stop: it missed a bar',
        ],
        answer=1,
        why='Only one bar is missed, and only just, so it is worth improving and testing again. Calling it a go would quietly move the bar after seeing the result.',
    ),
    angle=angle(
        pattern='Must-pass first, then count the misses',
        text='The big idea: decide fit for purpose against bars written down before the trial, and treat a failed must-pass case as an automatic stop. Your code first returns "stop" if any must-pass case failed. Then it checks quality, speed and cost against their bars, noting each one missed and whether the miss is close: quality within 0.05 of the bar, speed or cost no more than 1.2 times the bar. No misses means "go". Exactly one close miss means "fix". Anything else means "stop". It is like a driving test: one serious fault fails you, a small slip means practise and retake.',
        say='"I agree the bars before the pilot: quality, must-pass cases, speed and cost. Any must-pass failure is a stop, all bars met is a go, and one near miss means fix and test again."',
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
