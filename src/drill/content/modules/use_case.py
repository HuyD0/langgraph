"""Use case and fit: pick an AI use case worth doing, write it down, and decide whether it is fit for purpose."""

from drill.content.model import angle, case, example, exercise, lesson, machine, module, question

MODULE = module('use-case', 'Use case and fit', 'Pick an AI use case worth doing, write it down, and decide whether it is fit for purpose.')

lesson(MODULE, 'use_case_score',
    title='Is this a good AI use case?',
    learn=[
        'Most AI projects that fail go wrong before any code: they picked the wrong problem. So the first skill is judging an idea. A good first **use case** (one job you want AI to help with) has five things going for it.',
        '**Volume**: the task happens often, so small savings add up. **Judgement**: it needs reading or writing language, so a simple rule or a lookup cannot do it. **Examples**: you have real past cases with right answers to test on. **Safe to be wrong**: a wrong answer is cheap, or a person checks before it matters. **Owner**: someone in the business wants it and will decide.',
        'Three of these are **stoppers**. If a rule can do the job, write the rule, it is cheaper and always right. If there are no examples, you cannot tell whether it works. If a wrong answer causes real harm and nobody checks, do not let AI decide it.',
        'Score each idea from 0 to 2 on all five, rule out any idea with a 0 on a stopper, and start with the highest score. The rest of this phase then measures that one idea and prices it.',
    ],
    example=example('Four ideas, scored 0 to 2', """# volume, judgement, examples, safe, owner
hr_answers = [2, 2, 2, 1, 2]  # 9: start here
loan_yes_no = [2, 2, 2, 0, 2]  # safe 0: stop
date_format = [2, 0, 2, 2, 2]  # judgement 0:
                               # a rule does it
meeting_notes = [1, 2, 1, 2, 1]  # 7"""),
    check=question(
        'A team wants AI to turn dates like 12/10/2026 into 2026-10-12. Is it a good first AI use case?',
        [
            'Yes: it happens thousands of times a day',
            'No: a simple rule does it, exactly and for free',
            'Yes, as long as they use a large model',
        ],
        answer=1,
        why='Changing a date format needs no judgement. A few lines of ordinary code do it perfectly every time, so AI only adds cost and mistakes.',
    ),
    angle=angle(
        pattern='Rule out, then pick the best',
        text='The big idea: judge an AI idea on five things, volume, judgement, examples, safe to be wrong and an owner, and rule it out at once if a rule could do it, there is nothing to test on, or a wrong answer would do harm unchecked. Your code walks through the ideas. It skips any idea with a 0 for judgement, examples or safe. For the rest it adds the five scores and keeps the idea with the highest total so far, so on a tie the first one wins. If every idea is ruled out it returns None. It is like a job shortlist: anyone missing a must-have is out, then the best of the rest.',
        say='"Before building, I check the idea needs judgement, has examples to test on and is safe to get wrong, then I score volume and ownership and start with the best."',
        classic=None,
    ),
    exercise=exercise(
        title='Pick the First Use Case',
        topic='use cases',
        difficulty='easy',
        fn='best_use_case',
        prompt="""Your function gets `ideas`, a list of dicts. Each idea has a `"name"` and five scores from 0 to 2:

- `"volume"`: how often the task happens.
- `"judgement"`: how much it needs reading or writing language. 0 means a simple rule could do it.
- `"examples"`: real past cases with right answers to test on. 0 means none.
- `"safe"`: how safe a wrong answer is. 0 means real harm with nobody checking.
- `"owner"`: how much someone in the business wants it.

Skip any idea with a 0 for `"judgement"`, `"examples"` or `"safe"`. For the others, add up all five scores.

Return the `"name"` of the idea with the highest total. On a tie, return the one that comes first. If every idea is skipped, or the list is empty, return `None`.""",
        pattern='Skip the ruled-out ideas, keep the best total so far.',
        target='one pass over the ideas',
        realworld='Teams that score ideas before building drop the ones a rule could do, the ones they cannot test and the risky ones, and start where a pilot can succeed.',
        starter="""def best_use_case(ideas):
    # your code here
    pass
""",
        solution="""def best_use_case(ideas):
    best = None
    best_score = -1
    for idea in ideas:
        if idea["judgement"] == 0:
            continue
        if idea["examples"] == 0 or idea["safe"] == 0:
            continue
        score = (idea["volume"] + idea["judgement"]
                 + idea["examples"] + idea["safe"]
                 + idea["owner"])
        if score > best_score:
            best = idea["name"]
            best_score = score
    return best
""",
        cases=[
            case([
                {"name": "HR answers", "volume": 2, "judgement": 2, "examples": 2, "safe": 1, "owner": 2},
                {"name": "Loan yes or no", "volume": 2, "judgement": 2, "examples": 2, "safe": 0, "owner": 2},
                {"name": "Date format", "volume": 2, "judgement": 0, "examples": 2, "safe": 2, "owner": 2},
                {"name": "Meeting notes", "volume": 1, "judgement": 2, "examples": 1, "safe": 2, "owner": 1},
            ], expected="HR answers", sample=True),
            case([], expected=None),
            case([
                {"name": "No examples", "volume": 2, "judgement": 2, "examples": 0, "safe": 2, "owner": 2},
                {"name": "Rule does it", "volume": 2, "judgement": 0, "examples": 2, "safe": 2, "owner": 2},
            ], expected=None),
            case([
                {"name": "First", "volume": 1, "judgement": 2, "examples": 2, "safe": 2, "owner": 1},
                {"name": "Second", "volume": 2, "judgement": 1, "examples": 2, "safe": 1, "owner": 2},
            ], expected="First"),
            case([
                {"name": "Small", "volume": 0, "judgement": 1, "examples": 1, "safe": 1, "owner": 0},
                {"name": "Big", "volume": 2, "judgement": 1, "examples": 1, "safe": 2, "owner": 2},
            ], expected="Big"),
        ],
        guided="""def best_use_case(ideas):
    # Replace every ___ with real code, then run the tests.
    best = None
    best_score = -1
    for idea in ideas:
        # Step 1: a rule could do it, so skip it.
        if idea["judgement"] == 0:
            continue
        # Step 2: no examples, or unsafe to get wrong: skip.
        if idea["examples"] == 0 or ___:
            continue
        # Step 3: add up all five scores.
        score = (idea["volume"] + idea["judgement"]
                 + idea["examples"] + idea["safe"]
                 + idea["owner"])
        # Step 4: keep it only if it beats the best so far.
        if ___:
            best = idea["name"]
            best_score = score
    return best
""",
        fills=['idea["safe"] == 0', 'score > best_score'],
        concepts=[
            [
                'Reading a dict',
                'A dict holds named values. `idea["volume"]` reads the value named volume.',
                """idea = {"name": "HR", "volume": 2}
idea["volume"]   # 2""",
            ],
            [
                'continue',
                '`continue` skips the rest of this turn of the loop and moves on to the next item.',
                """for n in [1, 0, 3]:
    if n == 0:
        continue
    print(n)   # prints 1, then 3""",
            ],
            [
                'Keeping the best so far',
                'Start with a value every real score beats, then replace it whenever you find a bigger one. Using `>` (not `>=`) keeps the first on a tie.',
                """best = -1
for s in [4, 9, 9]:
    if s > best:
        best = s   # 4, then 9""",
            ],
        ],
        byhand='HR answers: no 0 on a stopper, total 2 + 2 + 2 + 1 + 2 = 9, the best so far. Loan yes or no: safe is 0, skip. Date format: judgement is 0, skip. Meeting notes: 1 + 2 + 1 + 2 + 1 = 7, less than 9. Return "HR answers".',
        why='It looks at each idea once, so the work grows with the number of ideas.',
        gotchas=[
            [
                'Using AI where a rule would do',
                'If the right answer follows a fixed rule, like a date format or a tax table, ordinary code is cheaper, faster and never wrong. Save AI for tasks that need judgement.',
            ],
            [
                'Starting with the riskiest idea',
                'A first project that makes unchecked, high-stakes decisions can do real harm and lose trust. Start where a wrong answer is cheap or a person checks it.',
            ],
        ],
    ),
)

lesson(MODULE, 'use_case_card',
    title='Write the use case down',
    learn=[
        'Before building, write the use case on one page, a **use case card**. It makes everyone agree on the same job, and it lists what the trial must measure.',
        'A card answers nine questions. **Who** uses it, and the **task** it helps with. The **input** and the **output**. How it is done **today**, and what that costs. What **success** looks like, as a number. What a **wrong answer** costs, and who catches it. The **data** to test on. And the **owner** who will decide.',
        'Vague cards fail. "Use AI for HR" cannot be tested. "Draft answers to employee policy questions in Teams; an HR person approves each one before it is sent; success is 80 in 100 drafts approved without edits on last month\'s 200 questions" can.',
        'A blank line on the card is an open question. Answer it before you build, because a missing owner or a missing test set will stop the project later anyway.',
    ],
    example=example('A card for the HR assistant', """card = {
  "user": "HR team",
  "task": "answer policy questions",
  "input": "an employee's question",
  "output": "a draft answer with a source",
  "today": "15 minutes by hand, $8",
  "success": "80 in 100 approved unedited",
  "wrong_answer": "HR catches it before sending",
  "data": "last month's 200 questions",
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
        text='The big idea: a use case card answers nine questions on one page, and a blank line, or a success line with no number, is an open question to settle before building. Your code goes through the nine field names in order. For each it reads the card\'s value, or an empty string if the field is missing, and strips spaces. A blank value is a gap. For the success field it also checks the text has at least one digit, because success you cannot count is a gap too. It returns the gaps in the same order. It is like checking a form before you post it: every box filled, and the amount written as a number.',
        say='"I write the use case on one page: who, the task, input and output, today\'s cost, success as a number, the cost of a wrong answer, the test data and the owner. Any blank is a question to answer first."',
        classic=None,
    ),
    exercise=exercise(
        title='Find the Gaps in a Card',
        topic='use cases',
        difficulty='easy',
        fn='card_gaps',
        prompt="""Your function gets `card`, a dict of text fields.

A full card has these nine fields, in this order:

- `"user"`, `"task"`, `"input"`, `"output"`, `"today"`
- `"success"`, `"wrong_answer"`, `"data"`, `"owner"`

A field is a gap if it is missing, or its text is blank after removing spaces from both ends.

The `"success"` field is also a gap if its text has no digit in it, because success must be a number you can check.

Return a list of the gap field names, in the order above. A complete card gives `[]`.""",
        pattern='Walk the field list in order and collect the gaps.',
        target='one pass over the nine fields',
        realworld='A use case card is the first page of most AI project proposals. Reviewers send it back when the success line has no number or nobody owns the decision.',
        starter="""def card_gaps(card):
    # your code here
    pass
""",
        solution="""def card_gaps(card):
    fields = ["user", "task", "input", "output", "today",
              "success", "wrong_answer", "data", "owner"]
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
            case({"user": "HR team", "task": "answer policy questions", "input": "a question", "output": "a draft answer", "today": "15 minutes, $8", "success": "faster answers", "wrong_answer": "", "data": "200 past questions"}, expected=["success", "wrong_answer", "owner"], sample=True),
            case({"user": "HR team", "task": "answer policy questions", "input": "a question", "output": "a draft answer", "today": "15 minutes, $8", "success": "80 in 100 approved", "wrong_answer": "HR checks first", "data": "200 past questions", "owner": "Head of HR"}, expected=[]),
            case({}, expected=["user", "task", "input", "output", "today", "success", "wrong_answer", "data", "owner"]),
            case({"user": "  ", "task": "triage tickets", "input": "a ticket", "output": "a team name", "today": "2 minutes each", "success": "90% routed right", "wrong_answer": "rerouted by hand", "data": "", "owner": "IT lead"}, expected=["user", "data"]),
        ],
        guided="""def card_gaps(card):
    # Replace every ___ with real code, then run the tests.
    fields = ["user", "task", "input", "output", "today",
              "success", "wrong_answer", "data", "owner"]
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
        byhand='user, task, input, output and today are filled. success is "faster answers": not blank, but no digit, so it is a gap. wrong_answer is blank: a gap. data is filled. owner is missing: a gap. Return ["success", "wrong_answer", "owner"].',
        why='Nine fields, each checked once, so the work stays small and fixed.',
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
        'The framework also says a system should be "just as reliable as it needs to be" and "just as secure as it needs to be". So answer each checklist question yes or no, and treat the no answers as a risk list: the pillar with the most gaps is where to look first, and some gaps are fine for a pilot if you write them down.',
    ],
    example=example('A short review of the HR assistant', """review = [
  ["Reliability", "Fallback if the model is down?", False],
  ["Reliability", "Retries with a limit?", True],
  ["Security", "Injection tested?", False],
  ["Security", "Only HR can read answers?", False],
  ["Operational Excellence", "Every answer traced?", True],
]
# Security has 2 gaps, Reliability 1:
# look at Security first"""),
    check=question(
        'Which pillar asks what happens when the model endpoint runs out of quota during the busiest minute?',
        [
            'Reliability, with Performance Efficiency',
            'Data and AI governance',
            'Interoperability and usability',
        ],
        answer=0,
        why='Keeping it working when a dependency fails is Reliability, and coping with the busiest minute is Performance Efficiency. Governance is about who may use which data and models.',
    ),
    angle=angle(
        pattern='Count the gaps per pillar',
        text='The big idea: a well-architected review asks yes-or-no questions under each pillar, and the no answers, counted per pillar, show where the design is weakest. Your code walks through the review rows. For every row answered no it adds one to that pillar\'s count, remembering pillars in the order they first appear. Then it turns the counts into [pillar, gaps] pairs, keeps only pillars with at least one gap, and sorts them with the most gaps first. It is like a car inspection sheet: count the fails in each section and fix the worst section first.',
        say='"Before building I review the design against the Well-Architected pillars: reliability, security, cost, operations and performance, plus governance on Databricks. Each no is a risk, and the pillar with the most gaps goes first."',
        classic=None,
    ),
    exercise=exercise(
        title='Find the Weakest Pillar',
        topic='use cases',
        difficulty='medium',
        fn='review_gaps',
        prompt="""Your function gets `review`, a list of rows. Each row is a list of three things: the pillar's name, the question, and `True` (yes) or `False` (no).

Count the `False` answers for each pillar.

Return a list of `[pillar, gaps]` pairs, one for each pillar with at least one gap, with the most gaps first. Pillars with no gaps are left out. An empty review gives `[]`.

(The tests never have two pillars with the same number of gaps.)""",
        pattern='Count per name, then sort the counts, biggest first.',
        target='one pass to count, then one sort',
        realworld="Microsoft's Well-Architected assessment and the AWS lenses work this way: questions per pillar, then a list of risks per pillar to work through.",
        starter="""def review_gaps(review):
    # your code here
    pass
""",
        solution="""def review_gaps(review):
    counts = {}
    order = []
    for pillar, question, ok in review:
        if pillar not in counts:
            counts[pillar] = 0
            order.append(pillar)
        if not ok:
            counts[pillar] += 1
    pairs = []
    for pillar in order:
        if counts[pillar] > 0:
            pairs.append([pillar, counts[pillar]])
    pairs.sort(key=lambda pair: pair[1], reverse=True)
    return pairs
""",
        cases=[
            case([
                ["Reliability", "Fallback if the model is down?", False],
                ["Reliability", "Retries with a limit?", True],
                ["Security", "Injection tested?", False],
                ["Security", "Only HR can read answers?", False],
                ["Operational Excellence", "Every answer traced?", True],
            ], expected=[["Security", 2], ["Reliability", 1]], sample=True),
            case([], expected=[]),
            case([["Security", "Secrets in a vault?", True], ["Cost Optimization", "Budget alert set?", True]], expected=[]),
            case([
                ["Cost Optimization", "Cost model written?", False],
                ["Performance Efficiency", "Load tested?", False],
                ["Performance Efficiency", "Quota for the busiest minute?", False],
                ["Performance Efficiency", "Latency target set?", False],
                ["Reliability", "Fallback model?", False],
                ["Reliability", "Timeouts set?", False],
            ], expected=[["Performance Efficiency", 3], ["Reliability", 2], ["Cost Optimization", 1]]),
        ],
        guided="""def review_gaps(review):
    # Replace every ___ with real code, then run the tests.
    counts = {}
    order = []
    for pillar, question, ok in review:
        # Step 1: first time we see a pillar, start it at 0.
        if pillar not in counts:
            counts[pillar] = 0
            order.append(pillar)
        # Step 2: a no answer is a gap.
        if ___:
            counts[pillar] += 1
    # Step 3: keep pillars with at least one gap.
    pairs = []
    for pillar in order:
        if counts[pillar] > 0:
            pairs.append([pillar, counts[pillar]])
    # Step 4: most gaps first.
    pairs.sort(key=___, reverse=True)
    return pairs
""",
        fills=['not ok', 'lambda pair: pair[1]'],
        concepts=[
            [
                'Counting with a dict',
                'Start a name at 0 the first time you see it, then add 1 each time it counts.',
                """counts = {}
for w in ["a", "b", "a"]:
    if w not in counts:
        counts[w] = 0
    counts[w] += 1   # {"a": 2, "b": 1}""",
            ],
            [
                'Unpacking a row',
                '`for pillar, question, ok in review:` gives each of the row\'s three parts its own name.',
                """for name, age in [["Ana", 30]]:
    print(name)   # Ana""",
            ],
            [
                'Sorting by one part',
                '`key=lambda pair: pair[1]` sorts by the second item; `reverse=True` puts the biggest first.',
                """p = [["a", 1], ["b", 3]]
p.sort(key=lambda x: x[1], reverse=True)
# [["b", 3], ["a", 1]]""",
            ],
        ],
        byhand='Reliability: one no, one yes, so 1 gap. Security: two no answers, 2 gaps. Operational Excellence: a yes, 0 gaps, left out. Sorted, most first: [["Security", 2], ["Reliability", 1]].',
        why='One pass to count every answer, then a sort of a handful of pillars.',
        gotchas=[
            [
                'Reviewing only the happy path',
                'An AI design that works when everything is up can still fail on the first quota limit or model outage. Ask what happens when each dependency fails.',
            ],
            [
                'Fixing every gap before a pilot',
                'The framework says just as reliable and as secure as it needs to be. Some gaps are fine for a small pilot, as long as they are written down and closed before going live.',
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
