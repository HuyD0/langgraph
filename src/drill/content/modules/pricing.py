"""Pricing and sizing: What an AI task really costs, what it saves, and how much capacity it needs, worked out before you build."""

from drill.content.model import angle, case, example, exercise, lesson, module, question, stack

MODULE = module('pricing', 'Pricing and sizing', 'What an AI task really costs, what it saves, and how much capacity it needs, worked out before you build.')

lesson(MODULE, 'cost_per_finished_task',
    title='Cost per finished task',
    learn=[
        'Work out what an AI task costs, and what it saves, before you build it. One forecast said at least 30 percent of generative AI projects would be dropped after the trial stage, partly over rising costs and unclear value. Pricing first also tells your trial which numbers it must measure.',
        "Don't price only the tokens. The **cost per finished task** (its **fully loaded cost**) is the model's bill, plus a person checking some answers (**human review**), plus redoing the answers that fail (**rework**). In an HR ticket bot the model is under 4 percent of it.",
        'Mistakes nobody catches cost extra on top: in the HR ticket bot, 5 in 100 wrong answers slip through and cost $10 each to sort out later, so 50 cents a ticket. Some write-ups add this in, which makes about $2.37 a ticket. Here we keep it apart, and the payback lesson takes it off the saving.',
        "Each number has a source. The **price list** gives the token price, and the **POC** (proof of concept, a small trial build) measures the tokens and how often answers fail. The **business owner** gives the hourly rate, today's cost of a task, how many answers get checked and how long a check takes.",
    ],
    example=example('One HR ticket, $8 by hand today', """# 30 in 100 answers checked,
# 2 minutes each, at $60 an hour
hours = 0.3 * 2 / 60  # 0.01 hours
check = hours * 60    # at $60: 0.60
# 15 in 100 fail, and a person
# redoes each one for $8
redo = 0.15 * 8       # 1.20
model = 0.065  # 6.5 cents of tokens
total = model + check + redo
# 1.865 dollars a finished ticket:
# the model is under 4 percent"""),
    check=question(
        'Your team moves to a model with half the token price. The cost per finished task hardly changes. Why?',
        [
            'The cheaper model still sends the same number of tokens',
            'Token prices only count for answers, not for prompts',
            'Checking and redoing answers cost far more than tokens',
        ],
        answer=2,
        why="The model is a few percent of the total. People's time checking and redoing answers is most of it, so a cheaper model barely moves the total.",
    ),
    angle=angle(
        pattern='Add up the three costs',
        text="The big idea: an AI task costs more than the model's bill, so you price a finished task: the model, plus a person checking, plus redoing failures. Your code works out each part. Checking is the share checked times the minutes per check, divided by 60 to make hours, times the hourly rate. Failures are the share that fails times the cost of a redo. It adds both to the model cost and rounds to cents. It is like a meal's real cost: the food, plus the cook's time.",
        say='"I price a [[finished task|model call|prompt::The thing the business actually gets.]], not a single call. That\'s the model cost, plus people [[checking|writing|training::Someone looks over a share of the answers.]] answers, plus [[redoing|ignoring|logging::Answers that fail have to be done again.]] the ones that fail."',
        classic=None,
    ),
    stack=stack('MLflow 3: model cost per task from traces', """import mlflow

traces = mlflow.search_traces(
    experiment_ids=[exp_id],
    return_type="list",
)
# example prices, $ per million
IN, OUT = 2, 10
costs = []
for t in traces:
    use = t.info.token_usage
    if use:
        costs.append((
            use["input_tokens"] * IN
            + use["output_tokens"] * OUT
        ) / 1000000)
model_cost = sum(costs) / len(costs)
# Checking and redo costs come from
# the POC's review notes, not traces."""),
    exercise=exercise(
        title='Price a Finished Task',
        topic='pricing',
        difficulty='easy',
        fn='cost_per_finished_task',
        prompt="""Your function gets six things:

- `model_cost`: the model's bill for one task, in dollars, like `0.13`.
- `check_share`: the share of answers a person checks, like `0.3` (30 in 100).
- `check_minutes`: the minutes one check takes, like `2`.
- `hourly_rate`: what an hour of that person's time costs, like `45`.
- `fail_share`: the share of answers that fail and are done again by hand, like `0.15`.
- `redo_cost`: what doing one task again by hand costs, like `8`.

Checking costs `check_share` times `check_minutes`, divided by 60, times `hourly_rate`. Failures cost `fail_share` times `redo_cost`.

Return the model cost plus checking plus failures, in dollars, rounded to 2 decimal places.""",
        pattern='Add three parts: the model, checking, and redoing failures.',
        target='a few sums, no loops',
        realworld='Teams that price only tokens get a surprise later: people checking and redoing answers usually cost far more than the model. This sum is the first line of any AI business case.',
        starter="""def cost_per_finished_task(
        model_cost, check_share,
        check_minutes, hourly_rate,
        fail_share, redo_cost):
    # your code here
    pass
""",
        solution="""def cost_per_finished_task(
        model_cost, check_share,
        check_minutes, hourly_rate,
        fail_share, redo_cost):
    hours = check_share * check_minutes / 60
    checking = hours * hourly_rate
    failures = fail_share * redo_cost
    total = model_cost + checking + failures
    return round(total, 2)
""",
        cases=[
            case(0.13, 0.3, 2, 45, 0.15, 8, expected=1.78, sample=True),
            case(0.04, 0, 2, 60, 0, 8, expected=0.04),
            case(0.1, 1, 3, 40, 0.1, 6, expected=2.7),
            case(0.0123, 0.25, 1, 50, 0.05, 7, expected=0.57),
            case(1.5, 0.5, 10, 90, 0.3, 25, expected=16.5),
        ],
        guided="""def cost_per_finished_task(
        model_cost, check_share,
        check_minutes, hourly_rate,
        fail_share, redo_cost):
    # Replace every ___ with real code, then run the tests.

    # Step 1: hours of checking for one task.
    hours = check_share * check_minutes / 60
    # Step 2: those hours at the hourly rate.
    checking = ___
    # Step 3: the share that fails, times one redo.
    failures = ___
    # Step 4: add the three parts, round to 2 places.
    total = model_cost + checking + failures
    return round(total, 2)
""",
        fills=['hours * hourly_rate', 'fail_share * redo_cost'],
        concepts=[
            [
                'Working out in steps',
                'Give each part its own name, then add the names. Python multiplies and divides from left to right.',
                """trip = 30 / 60 * 20   # 10.0
total = trip + 5      # 15.0""",
            ],
            [
                'round',
                '`round(x, 2)` keeps 2 decimal places, which suits dollars and cents.',
                'round(4.5678, 2)   # 4.57',
            ],
            [
                'A long def line',
                'When a function has many inputs, the list can wrap onto more lines inside the brackets.',
                """def area(
        width, height):
    return width * height""",
            ],
        ],
        byhand='Model: 0.13 dollars. Checking: 0.3 times 2 is 0.6 minutes a task. Divided by 60 that is 0.01 hours, and times 45 dollars an hour that is 0.45. Failures: 0.15 times 8 is 1.20. Add them: 0.13 plus 0.45 plus 1.20 is 1.78. Return 1.78.',
        why='A handful of multiplications and one sum, whatever the numbers.',
        gotchas=[
            [
                'Pricing tokens only',
                "In one study, a model's bill was 474 times cheaper than paying an expert to do the task, but only 1.2 to 1.6 times cheaper once checking and redoing its answers were counted.",
            ],
            [
                'Leaving out the mistakes nobody caught',
                'Wrong answers that slip through cost money later: 50 cents a ticket in the HR example, more than the model. Your function leaves them out, so take them off the saving.',
            ],
        ],
    ),
)

lesson(MODULE, 'run_tokens',
    title='Tokens grow every step',
    learn=[
        'An **agent** resends everything so far on every step. All of that is called the **context**: the instructions, the question, every earlier answer and every tool result. So the input grows with each step, and one task costs far more than one call.',
        'In one company\'s research system, one agent used about 4 times the tokens of a plain chat, and a team of agents about 15 times. Price an agent from whole runs, never from a single call.',
        'Where the numbers come from: the POC (your trial build) measures the tokens of each step from its traces, on real tasks. Give a low, typical and high count, because hard tasks take more steps. The price list then turns tokens into dollars.',
    ],
    example=example('Three steps, each one resending it all', """context = 4000  # prompt + question
total_in = 0
steps = [[100, 900], [100, 900],
         [500, 0]]
for out, tool in steps:
    total_in += context  # resend all
    context += out + tool
# reads 4000, then 5000, then 6000:
# 15000 in, not 3 times 4000 (12000)"""),
    check=question(
        'An agent takes 6 steps to finish a task. A teammate prices it as 6 times the tokens of the first call. What did they miss?',
        [
            'Each step resends everything that earlier steps added',
            'Output tokens cost less than input tokens, per token',
            'The first call is always the most expensive step',
        ],
        answer=0,
        why='Every step adds its answer and tool result to the context, and the next call reads all of it. So each step costs more than the one before.',
    ),
    angle=angle(
        pattern='A running total that grows',
        text="The big idea: an agent resends everything so far on every step, so the input grows and one task costs far more than one call. Your code keeps the context size in a variable, starting with the first input. For each step it first adds the whole context to the input total, and the step's output to the output total. Only after that does the context grow by the step's output and tool result. It is like an email thread where every reply quotes everything above it.",
        say='"I price an agent by the [[whole run|first call|last step::Every step of the task, start to finish.]], not one call. Each step [[resends|forgets|shortens::Like an email reply that quotes everything above it.]] everything so far, so the input bill [[grows|shrinks|stays flat::The context gets longer every step.]] every step."',
        classic=None,
    ),
    stack=stack('LangChain: tokens for a whole agent run', """from langchain_core.callbacks import (
    get_usage_metadata_callback,
)

with get_usage_metadata_callback() as cb:
    graph.invoke(
        {"messages": [("user", question)]},
        # The default limit is 10007
        # steps, so set your own.
        config={"recursion_limit": 12},
    )
# Tokens for every call in the run,
# added up per model:
print(cb.usage_metadata)"""),
    exercise=exercise(
        title='Tokens for a Whole Run',
        topic='pricing',
        difficulty='easy',
        fn='run_tokens',
        prompt="""An agent resends everything so far on every step.

Your function gets two things:

- `start_input`: the tokens in the first call (instructions, tools and the question), like `3000`.
- `steps`: one `[output_tokens, tool_result_tokens]` pair for each model call, in order, like `[[200, 800], [500, 0]]`.

The context starts at `start_input`. For each step:

- The call reads the whole context, so add the context to the total input.
- Add the step's output tokens to the total output.
- Then the context grows by the step's output and its tool result.

Return `[total_input, total_output]`. With no steps, return `[0, 0]`.""",
        pattern="Keep a running context size, and add it to the input total before each step grows it.",
        target='one pass over the steps',
        realworld="Agent bills grow with steps much faster than people expect. Teams count tokens per run from their traces, and cap steps with LangGraph's recursion_limit so the worst case is a known number.",
        starter="""def run_tokens(start_input, steps):
    # your code here
    pass
""",
        solution="""def run_tokens(start_input, steps):
    context = start_input
    total_input = 0
    total_output = 0
    for output, tool_result in steps:
        total_input += context
        total_output += output
        context += output + tool_result
    return [total_input, total_output]
""",
        cases=[
            case(3000, [[200, 800], [200, 800], [500, 0]], expected=[12000, 900], sample=True),
            case(1000, [], expected=[0, 0]),
            case(2000, [[300, 0]], expected=[2000, 300]),
            case(2000, [[100, 400], [100, 400], [100, 400], [100, 400], [500, 0]], expected=[15000, 900]),
            case(500, [[50, 2000], [50, 3000], [100, 0]], expected=[8650, 200]),
        ],
        guided="""def run_tokens(start_input, steps):
    # Replace every ___ with real code, then run the tests.

    context = start_input
    total_input = 0
    total_output = 0
    for output, tool_result in steps:
        # Step 1: this call reads the whole context.
        total_input += ___
        total_output += output
        # Step 2: the context grows by this step's
        # output and its tool result.
        context += ___
    return [total_input, total_output]
""",
        fills=['context', 'output + tool_result'],
        concepts=[
            [
                'Unpacking in a for loop',
                'When each item is a pair, the for line can name both parts.',
                """for name, age in [['ann', 30], ['bo', 25]]:
    print(name, age)""",
            ],
            [
                'Adding to a running total',
                '`total += x` is short for `total = total + x`.',
                """steps = 0
steps += 500
steps += 300   # steps is now 800""",
            ],
            [
                'Returning two numbers',
                'Put them in a list, in the order asked for.',
                """def low_high(nums):
    return [min(nums), max(nums)]""",
            ],
        ],
        byhand='The context starts at 3000. Step 1 reads 3000, so the input is 3000 and the output is 200. The context grows by 200 and 800, to 4000. Step 2 reads 4000: input 7000, output 400. The context grows to 5000. Step 3 reads 5000: input 12000, output 900. Return [12000, 900]. Pricing it as 3 times the first call would say 9000, so the growing context added a third more.',
        why='One walk through the steps, keeping two running totals.',
        gotchas=[
            [
                'Counting tokens from one short test',
                'A short test takes few steps, and real tasks take more. Each step costs more than the one before, so give low, typical and high counts from real traces.',
            ],
            [
                'Trusting the default step limit',
                "LangGraph's default recursion_limit is 10007 steps, far too high to stop a runaway agent in time. Set your own on every run.",
            ],
        ],
    ),
)

lesson(MODULE, 'total_cost',
    title='Total cost of ownership',
    learn=[
        "The **total cost of ownership** (TCO) is everything it costs to have the system for its whole life, not just to call the model. It is the cost side of every business case, and the tokens are often the smallest part.",
        "Its variables fall into three groups. **Build**, paid once: people's time, preparing data, building the eval set, the security review. **Run**, paid every month: the model's tokens, hosting and compute, the vector search index, tracing and monitoring, and people checking and redoing answers. **Maintain** (keeping it working), also monthly: re-running evals when the model or prompt changes, updating prompts, and someone on call.",
        "For a typical **RAG pipeline** on Azure, the monthly lines are: LLM calls (the answers, plus embeddings for new documents and every question), retrieval (Azure AI Search, or Databricks Vector Search), Databricks compute for the jobs that chunk and embed documents, and storage for documents, chunks and traces. The first indexing of all the documents is a one-off.",
        "Microsoft's cost guidance for AI says to find the cost drivers first: how much data you index, how many queries arrive, the throughput you need, and the hidden costs of the services underneath, like the step that prepares documents before they are indexed.",
        'Add it up over the years you plan to run it: the one-off costs, plus every monthly cost times 12 times the years. Then look at the biggest single item, because that is where a saving matters most.',
    ],
    example=example('Two years of the HR assistant', """build = {"build team": 60000, "eval set": 8000,
         "security review": 5000}      # 73000
monthly = {"model": 900, "hosting": 1200,
           "monitoring": 300, "checking": 3500}
# 5900 a month for 24 months: 141600
# total: 214600
# biggest item: checking, 3500 x 24 = 84000,
# more than the whole build team"""),
    check=question(
        'Two years of an AI assistant cost $214,600. Which change cuts the most?',
        [
            'A model that is half the price per token',
            'Fewer answers that need a person to check them',
            'A cheaper security review before launch',
        ],
        answer=1,
        why='Checking costs $3,500 a month, $84,000 over two years. Halving the model saves about $10,800, and the security review is paid only once.',
    ),
    angle=angle(
        pattern='One-off plus monthly times months',
        text='The big idea: the total cost of ownership is the one-off build costs plus every monthly cost for the whole life of the system, and the biggest single item shows where a saving matters most. Your code works out the number of months as 12 times the years. It adds up the one-off costs as they are and each monthly cost times the months, and while doing it keeps the name of the item with the biggest share so far. It returns the total, rounded to whole dollars, and that name. It is like the true cost of a car: the price, plus fuel, insurance and servicing for as long as you keep it.',
        say='"For total cost of ownership, I add the [[one-off|monthly|yearly::Things you pay for just once.]] build costs to every monthly cost, for the whole [[life|first year|launch::How long the system will be running.]] of the system. Then I look hardest at the [[biggest|newest|smallest::Where a saving matters most.]] item."',
        classic=None,
    ),
    exercise=exercise(
        title='Add Up the Total Cost',
        topic='pricing',
        difficulty='easy',
        fn='total_cost',
        prompt="""Your function gets three things:

- `build`: a dict of one-off costs in dollars, like `{"build team": 60000}`.
- `monthly`: a dict of costs paid every month, like `{"model": 900}`.
- `years`: how many years the system will run, like `2`.

Over its life, a one-off cost counts once, and a monthly cost counts 12 times `years`.

Return `[total, biggest]`: the total over its life, rounded to a whole number, and the name of the single item with the biggest life cost. Look at the `build` items first, then the `monthly` ones, and on a tie keep the one you saw first.""",
        pattern='Add every item over its life, keeping the biggest so far.',
        target='one pass over the items',
        realworld='Business cases that list only build cost and tokens surprise everyone later. A TCO table over the planned life, with the biggest line on top, is what finance asks for.',
        starter="""def total_cost(build, monthly, years):
    # your code here
    pass
""",
        solution="""def total_cost(build, monthly, years):
    months = 12 * years
    total = 0
    biggest = None
    biggest_cost = -1
    for name in build:
        cost = build[name]
        total += cost
        if cost > biggest_cost:
            biggest = name
            biggest_cost = cost
    for name in monthly:
        cost = monthly[name] * months
        total += cost
        if cost > biggest_cost:
            biggest = name
            biggest_cost = cost
    return [round(total), biggest]
""",
        cases=[
            case({"build team": 60000, "eval set": 8000, "security review": 5000},
                 {"model": 900, "hosting": 1200, "monitoring": 300, "checking": 3500}, 2,
                 expected=[214600, "checking"], sample=True),
            case({"build team": 50000}, {"model": 100}, 1, expected=[51200, "build team"]),
            case({}, {"model": 250.5, "hosting": 300}, 3, expected=[19818, "hosting"]),
            case({"pilot": 12000}, {"on call": 1000}, 1, expected=[24000, "pilot"]),
        ],
        guided="""def total_cost(build, monthly, years):
    # Replace every ___ with real code, then run the tests.
    months = 12 * years
    total = 0
    biggest = None
    biggest_cost = -1
    # Step 1: one-off costs count once.
    for name in build:
        cost = build[name]
        total += cost
        if cost > biggest_cost:
            biggest = name
            biggest_cost = cost
    # Step 2: monthly costs count for every month.
    for name in monthly:
        cost = ___
        total += cost
        if ___:
            biggest = name
            biggest_cost = cost
    return [round(total), biggest]
""",
        fills=['monthly[name] * months', 'cost > biggest_cost'],
        concepts=[
            [
                'Looping over a dict',
                '`for name in costs:` gives each key in turn; `costs[name]` is its value.',
                """costs = {"model": 900}
for name in costs:
    print(name, costs[name])   # model 900""",
            ],
            [
                '+=',
                '`total += cost` adds cost to the running total.',
                """total = 0
total += 5   # 5""",
            ],
            [
                'round to whole dollars',
                '`round(x)` with no second number gives a whole number.',
                'round(19818.0)   # 19818',
            ],
        ],
        byhand='24 months. Build: 60000 + 8000 + 5000 = 73000; biggest so far is the build team at 60000. Monthly: model 900 x 24 = 21600, hosting 28800, monitoring 7200, checking 3500 x 24 = 84000, now the biggest. Total 73000 + 141600 = 214600. Return [214600, "checking"].',
        why='Each cost is looked at once, so the work grows with the number of items.',
        gotchas=[
            [
                'Pricing the build and the tokens only',
                'Hosting, monitoring, people checking answers and upkeep are paid every month for years. They usually add up to more than the build.',
            ],
            [
                'Forgetting the services underneath',
                "Microsoft's guidance warns about hidden dependency costs, like the step that prepares documents before indexing. List every service the system touches.",
            ],
        ],
    ),
)

lesson(MODULE, 'payback_plan',
    title='Payback and break-even',
    learn=[
        'A task that saves money every time can still lose money overall. Running costs come every month, and the build has to be paid back. Three numbers tell you whether it is worth building.',
        '**Monthly net** is the saving per task times tasks a month, minus the fixed monthly costs (search, logging, monitoring). **Payback** is the build cost divided by the monthly net: how many months until the build has paid for itself. **Break-even** is the fixed monthly costs divided by the saving per task: how many tasks a month you need just to cover the running costs.',
        "Where the numbers come from: **saving per task** is today's cost, minus the cost per finished task, minus what mistakes nobody caught cost later. The business owner confirms the staff time saved is real money, a **hard saving**: fewer new hires or less overtime, not just quieter afternoons (a **soft saving**). They also guess tasks a month, and the POC checks that guess.",
        'In the HR example, $8 today minus about $1.87 with AI, minus 50 cents for mistakes nobody caught, saves about $5.64 a ticket. With 6,000 tickets a month and $10,000 of fixed costs, a $150,000 build pays back in about 6.3 months.',
    ],
    example=example('The HR ticket plan', """saving = 5.635   # a ticket
tasks = 6000     # a month
fixed = 10000    # a month
build = 150000   # once
net = saving * tasks - fixed
# 23810 a month
payback = build / net   # 6.3 months
even = fixed / saving   # 1774.6
# round up: 1775 tickets a month"""),
    check=question(
        'Your plan breaks even at 2,000 tasks a month, but the business only sends 1,500. What happens?',
        [
            'It pays back the build, just more slowly than planned',
            'It loses money every month, so the build never pays back',
            'It is fine, because break-even ignores the build cost',
        ],
        answer=1,
        why="Below break-even the savings don't even cover the running costs. The monthly net is below zero, so nothing is left over to pay back the build.",
    ),
    angle=angle(
        pattern='Check before you divide',
        text="The big idea: a task that saves money each time can still lose money once monthly costs and the build are counted. Your code works out the monthly net: saving per task times tasks a month, minus fixed costs. Only if the net is above zero does it divide the build cost by it to get payback months. Otherwise payback is `None`, Python's word for no value. Break-even is fixed costs divided by saving per task, rounded up to a whole task, because you can't do part of a task.",
        say='"First I work out what\'s left each month after [[fixed costs|the build|taxes::Costs you pay every month no matter how many tasks run.]]. If that\'s zero or less, there\'s [[no payback|quick payback|a refund::It never earns back what you spent.]]. I round break-even [[up|down|off::You can\'t do part of a task.]] to a whole task."',
        classic=None,
    ),
    stack=stack('MLflow: keep the business case next to the POC', """import mlflow

with mlflow.start_run(run_name="hr-bot-case"):
    mlflow.log_params({
        "saving_per_task": 5.635,
        "tasks_per_month": 6000,
        "fixed_monthly": 10000,
        "build_cost": 150000,
    })
    mlflow.log_metrics({
        "monthly_net": 23810,
        "payback_months": 6.3,
        "break_even_tasks": 1775,
    })
# Later, swap each guess for a
# number the POC measured."""),
    exercise=exercise(
        title='Payback and Break-even',
        topic='pricing',
        difficulty='medium',
        fn='payback_plan',
        prompt="""Your function gets four things:

- `saving_per_task`: real dollars saved on each task, like `5.635`. It is always above 0.
- `tasks_per_month`: the tasks the AI handles in a month, like `6000`.
- `fixed_monthly`: the running costs each month, like `10000`.
- `build_cost`: what building it costs, paid once, like `150000`.

Return a dict with three keys:

- `"monthly_net"`: saving per task times tasks a month, minus the fixed costs, rounded to 2 decimal places.
- `"payback_months"`: the build cost divided by the monthly net, rounded to 1 decimal place. If the monthly net is 0 or less, use `None`.
- `"break_even_tasks"`: the fixed costs divided by the saving per task, rounded UP to a whole number. So 1774.6 becomes 1775, and 2000 stays 2000.""",
        pattern='Net first, divide only when it is above zero, and round break-even up.',
        target='a few sums, no loops',
        realworld='Whoever funds the build asks for payback and break-even first. Written down, they also become go or no-go gates for the pilot: if real volume stays below break-even, stop.',
        starter="""def payback_plan(
        saving_per_task, tasks_per_month,
        fixed_monthly, build_cost):
    # your code here
    pass
""",
        solution="""def payback_plan(
        saving_per_task, tasks_per_month,
        fixed_monthly, build_cost):
    saved = saving_per_task * tasks_per_month
    net = saved - fixed_monthly
    if net > 0:
        payback = round(build_cost / net, 1)
    else:
        payback = None
    even = int(fixed_monthly / saving_per_task)
    if even * saving_per_task < fixed_monthly:
        even += 1
    return {
        "monthly_net": round(net, 2),
        "payback_months": payback,
        "break_even_tasks": even,
    }
""",
        cases=[
            case(5.635, 6000, 10000, 150000, expected={'monthly_net': 23810.0, 'payback_months': 6.3, 'break_even_tasks': 1775}, sample=True),
            case(2, 1000, 3000, 50000, expected={'monthly_net': -1000, 'payback_months': None, 'break_even_tasks': 1500}),
            case(5, 2000, 10000, 60000, expected={'monthly_net': 0, 'payback_months': None, 'break_even_tasks': 2000}),
            case(4, 500, 0, 12000, expected={'monthly_net': 2000, 'payback_months': 6.0, 'break_even_tasks': 0}),
            case(2.535, 6000, 10000, 150000, expected={'monthly_net': 5210.0, 'payback_months': 28.8, 'break_even_tasks': 3945}),
        ],
        guided="""def payback_plan(
        saving_per_task, tasks_per_month,
        fixed_monthly, build_cost):
    # Replace every ___ with real code, then run the tests.

    # Step 1: saved a month, minus the running costs.
    saved = saving_per_task * tasks_per_month
    net = ___
    # Step 2: payback only when the net is above 0.
    if net > 0:
        payback = round(build_cost / net, 1)
    else:
        payback = None
    # Step 3: tasks to cover the fixed costs.
    # int() drops the decimals: 1774.6 becomes 1774.
    even = int(fixed_monthly / saving_per_task)
    # If that many tasks save less than fixed, add 1.
    if ___:
        even += 1
    return {
        "monthly_net": round(net, 2),
        "payback_months": payback,
        "break_even_tasks": even,
    }
""",
        fills=['saved - fixed_monthly', 'even * saving_per_task < fixed_monthly'],
        concepts=[
            [
                'None',
                '`None` means "no value". Use it when there is no sensible answer, like a payback that never comes.',
                """if left > 0:
    days = 30 / left
else:
    days = None""",
            ],
            [
                'Rounding up with int()',
                '`int(x)` drops the decimals, so it rounds down. Check whether that falls short, and add 1 if it does.',
                """boxes = int(25 / 6)   # 4
if boxes * 6 < 25:
    boxes += 1         # 5 boxes""",
            ],
            [
                'A dict with several keys',
                'Curly braces hold named values. Each line is a key, a colon and its value.',
                """day = {
    "steps": 8000,
    "sleep": 7.5,
}""",
            ],
            [
                'round',
                '`round(x, 1)` keeps 1 decimal place.',
                'round(6.2998, 1)   # 6.3',
            ],
        ],
        byhand='Saved a month: 5.635 times 6000 is 33810. Minus 10000 of fixed costs, the monthly net is 23810. That is above 0, so payback is 150000 divided by 23810, about 6.2999, which rounds to 6.3 months. Break-even: 10000 divided by 5.635 is about 1774.6. int() gives 1774, and 1774 tickets save only about 9996, less than 10000, so add 1: 1775. Return {"monthly_net": 23810, "payback_months": 6.3, "break_even_tasks": 1775}.',
        why='A few sums and one check, whatever the numbers.',
        gotchas=[
            [
                'Counting saved minutes as money',
                'Staff time saved is money only if the business hires less, cuts overtime or moves people to work it would pay for anyway. Otherwise it is a soft saving, and finance will not count it.',
            ],
            [
                'Payback ignores the slow start',
                'People start using it slowly, which is called the **adoption ramp**. If the first 3 months run at half volume, the 6.3 months becomes about 8.4.',
            ],
        ],
    ),
)

lesson(MODULE, 'biggest_swing',
    title='Which guess matters most',
    learn=[
        "Every business case rests on guesses, called **assumptions**: how many tasks, how often the AI is right, how much each one saves. If you don't know which guess matters most, the trial measures the easy things and misses the one that sinks the plan.",
        'A **sensitivity analysis** changes one guess at a time, from a bad value to a good one, and keeps the others at their expected values. The **swing** is how far the answer moves. The guess with the biggest swing is the one to measure hardest.',
        'In the HR example, doubling the token price lowers the monthly net by only about $390. If half the staff use the bot instead of 80 percent, the net falls from about $23,800 to about $11,100.',
        'Where the numbers come from: you and the business owner agree a bad, expected and good value for each guess (the **worst case**, **base case** and **best case**). Then measure the guesses with the biggest swings first. For example, try the prompt on 50 past tickets labelled by hand to see how often the AI is right, and run a small pilot to see how many staff really use it.',
    ],
    example=example('One guess, low and high', """# value = tasks * success * saving - fixed
# tasks 6000, saving 7, fixed 10000
low = 6000 * 0.5 * 7 - 10000    # 11000
high = 6000 * 0.95 * 7 - 10000  # 29900
swing = high - low              # 18900
# Do the same for each other guess,
# and compare the swings."""),
    check=question(
        "Doubling the token price barely moves your plan's monthly net, but fewer staff using the bot halves it. What should the POC measure hardest?",
        [
            'The token price, because it is on the monthly bill',
            'The fixed monthly costs, because they come every month',
            'How many staff really use the bot, and how often',
        ],
        answer=2,
        why='The guess with the biggest swing decides whether the plan pays. The token price barely moves the answer, so measuring it hard tells you little.',
    ),
    angle=angle(
        pattern='Move one guess, keep the biggest',
        text="The big idea: change one guess at a time, and the one that moves the answer most is the one to measure hardest. Your code copies the base values into a dict: a lookup table from each guess's name to its value. It works out the value with one guess at its low, then at its high. The swing is the gap between them, made positive with `abs`. It keeps the biggest, going through names in alphabetical order so a tie goes to the name that comes first.",
        say='"I move [[one guess|three guesses|two guesses::Change a single thing so you know what caused the swing.]] at a time from its low to its high, and keep the others [[steady|random|at zero::Everything else stays at its expected value.]]. The one that moves the answer most is the one I [[measure|ignore|drop::It\'s the guess most worth pinning down.]] first."',
        classic=None,
    ),
    stack=stack('MLflow 3: measure the guess that matters most', """import mlflow
from mlflow.genai.scorers import Correctness

# 50 past tickets, labelled by hand:
# {"inputs": {...}, "expectations":
#  {"expected_response": "..."}}
result = mlflow.genai.evaluate(
    data=labelled_tickets,
    predict_fn=answer_ticket,
    scorers=[Correctness()],
)
success = result.metrics["correctness/mean"]
# Put the measured share in the plan
# in place of the guess."""),
    exercise=exercise(
        title='Which Guess Matters Most',
        topic='pricing',
        difficulty='medium',
        fn='biggest_swing',
        prompt="""Your function gets two things:

- `base`: your expected value for each guess, like `{"tasks": 6000, "success": 0.8, "saving": 7, "fixed": 10000}`.
- `ranges`: a low and a high value for some of the guesses, like `{"success": [0.5, 0.95]}`.

The plan's monthly value is `tasks * success * saving - fixed`.

For each name in `ranges`, work out the value twice: once with that guess at its low, once at its high. Keep every other guess at its `base` value. The swing is the gap between the two values, as a positive number.

Return the name with the biggest swing. If two tie, return the one that comes first in alphabetical order.""",
        pattern='Change one guess at a time, and keep the name with the biggest swing.',
        target='one pass over the ranges',
        realworld='Finance teams call this a tornado chart: one bar per guess, biggest swing at the top. It tells the POC which number to measure first.',
        starter="""def biggest_swing(base, ranges):
    # your code here
    pass
""",
        solution="""def biggest_swing(base, ranges):
    def value(g):
        done = g["tasks"] * g["success"]
        return done * g["saving"] - g["fixed"]

    best = None
    best_swing = -1
    for name in sorted(ranges):
        low, high = ranges[name]
        g = dict(base)
        g[name] = low
        low_value = value(g)
        g[name] = high
        swing = abs(value(g) - low_value)
        if swing > best_swing:
            best = name
            best_swing = swing
    return best
""",
        cases=[
            case({'tasks': 6000, 'success': 0.8, 'saving': 7, 'fixed': 10000}, {'tasks': [4000, 7000], 'success': [0.5, 0.95], 'fixed': [8000, 14000]}, expected='success', sample=True),
            case({'tasks': 6000, 'success': 0.8, 'saving': 7, 'fixed': 10000}, {'fixed': [5000, 20000]}, expected='fixed'),
            case({'tasks': 1000, 'success': 0.9, 'saving': 2, 'fixed': 3000}, {'tasks': [900, 1100], 'fixed': [1000, 6000]}, expected='fixed'),
            case({'tasks': 100, 'success': 1, 'saving': 10, 'fixed': 0}, {'tasks': [50, 150], 'saving': [5, 15]}, expected='saving'),
            case({'tasks': 2000, 'success': 0.5, 'saving': 4, 'fixed': 1000}, {'success': [0.4, 0.6], 'tasks': [1500, 2500], 'saving': [1, 9]}, expected='saving'),
        ],
        guided="""def biggest_swing(base, ranges):
    # Replace every ___ with real code, then run the tests.

    # The plan's monthly value for one set of guesses.
    def value(g):
        done = g["tasks"] * g["success"]
        return done * g["saving"] - g["fixed"]

    best = None
    best_swing = -1
    # Alphabetical order, so the first of a tie wins.
    for name in sorted(ranges):
        low, high = ranges[name]
        # Step 1: copy base, then change only this guess.
        g = dict(base)
        g[name] = low
        low_value = value(g)
        g[name] = ___
        # Step 2: the gap between the two values,
        # as a positive number.
        swing = ___
        # Keep it only if it is strictly bigger.
        if swing > best_swing:
            best = name
            best_swing = swing
    return best
""",
        fills=['high', 'abs(value(g) - low_value)'],
        concepts=[
            [
                'Unpacking a pair',
                'Two names on the left take the two values of a list, in order.',
                """low, high = [5, 15]
# low is 5, high is 15""",
            ],
            [
                'Keeping the biggest so far',
                'Start with a value anything beats, like -1. Each time you find a bigger one, keep it, and its name too if you need it.',
                """best = -1
for n in [3, 7, 5]:
    if n > best: best = n   # ends as 7""",
            ],
            [
                'Copying a dict',
                '`dict(d)` makes a new copy, so changing the copy leaves `d` alone.',
                """base = {"size": 1}
g = dict(base)
g["size"] = 5   # base["size"] is still 1""",
            ],
            [
                'abs',
                '`abs(x)` drops the minus sign, so a gap is always positive.',
                'abs(3 - 10)   # 7',
            ],
            [
                'sorted on a dict',
                "`sorted(d)` gives the dict's keys in alphabetical order.",
                "sorted({'pear': 1, 'apple': 2})\n# ['apple', 'pear']",
            ],
            [
                'A function inside a function',
                'A small `def` inside your function saves writing the same sum twice.',
                """def trip(km):
    def cost(x):
        return x * 0.3
    return cost(km) + cost(km)""",
            ],
        ],
        byhand='In alphabetical order. fixed: at 8000 the value is 6000 times 0.8 times 7, minus 8000: 25600. At 14000 it is 19600. The gap is 6000. success: at 0.5 the value is 11000, and at 0.95 it is 29900. The swing is 18900. tasks: at 4000 the value is 12400, and at 7000 it is 29200. The swing is 16800. The biggest swing is 18900, so return "success".',
        why='One walk through the guesses in ranges, working out the value twice for each.',
        gotchas=[
            [
                'Changing two guesses at once',
                "Then you can't tell which one moved the answer. Change one, and keep the rest at their expected values.",
            ],
            [
                'Measuring what is easy',
                'Token counts are easy to measure, but how often the AI is right and how many people use it usually move the answer far more.',
            ],
        ],
    ),
)

lesson(MODULE, 'peak_capacity',
    title='Size for the busiest minute',
    learn=[
        'Traffic is never spread evenly through the day. If you **size** capacity (decide how many tokens a minute to ask for, called **capacity planning**) from the daily average, the busiest minute hits your limit, and users get error 429, "too many requests". So size for the **busiest minute**.',
        'Take tasks a day times the share that arrive in the busiest hour, and divide by 60 to get tasks a minute. Multiply by a **burst factor**: how much busier the busiest minute is than an average minute of that hour (3 is a fair first guess).',
        "Multiply by the tokens one task asks for, to get tokens in the busiest minute. Check that against every limit on the path: the Foundry deployment's **tokens per minute** (TPM) and the gateway's rate limits.",
        'Where the numbers come from: the business owner gives tasks a day. The POC measures the busiest hour, the burst from 1-minute peaks, and the tokens per task. The platform team gives the deployment quota and the gateway limits.',
    ],
    example=example('Average against busiest minute', """tokens = 25000   # per HR ticket
# spread over an 8-hour day:
avg = 270 / (8 * 60) * tokens
# about 14000 tokens a minute
# busiest hour has a fifth, burst 3:
peak = 270 * 0.2 / 60 * 3 * tokens
# 67500 a minute: almost 5 times
# rounding 0.9 tickets a minute up
# to 1 gives 75000: a little spare"""),
    check=question(
        'Your bot\'s daily average is far below its tokens-per-minute limit, yet users get "too many requests" errors every morning. What went wrong?',
        [
            'It was sized from the daily average, not the busiest minute',
            'The gateway counts only output tokens against the limit',
            'Tokens cost more in the morning, so the limit shrinks',
        ],
        answer=0,
        why='Requests bunch up at busy times. The limit is checked over a few seconds at a time, so the busiest minute, not the daily average, decides whether you fit.',
    ),
    angle=angle(
        pattern='Daily count to busiest minute',
        text='The big idea: traffic is never even, so you size for the busiest minute, not the daily average, or users hit error 429. Your code takes tasks a day times the busy-hour share and divides by 60 to get tasks a minute. It multiplies by the burst factor, then by tokens per task, and rounds to a whole number of tokens. Then it checks that number is at or below the tokens-per-minute limit, and returns the number and that true or false answer. It is like staffing a café for the lunch rush.',
        say='"Traffic is never even, so I size for the [[busiest minute|daily average|whole day::Staff a café for the lunch rush.]]. Then I check that against the [[per-minute limit|monthly bill|daily average::The cap the endpoint sets on tokens.]], so users don\'t get [[error 429|slow pages|wrong answers::The too-many-requests error.]]."',
        classic=None,
    ),
    stack=stack("Databricks: the busiest minutes in the gateway's usage table", """-- the 5 busiest minutes last week
SELECT date_trunc('MINUTE', event_time)
         AS minute,
       sum(total_tokens) AS tokens
FROM system.ai_gateway.usage
WHERE endpoint_name = 'hr-ticket-bot'
  AND event_time >= current_date()
        - INTERVAL 7 DAYS
GROUP BY 1
ORDER BY tokens DESC
LIMIT 5
-- Foundry's quota counts the prompt
-- plus max_tokens, not tokens used,
-- so leave room above these."""),
    exercise=exercise(
        title='Size for the Busiest Minute',
        topic='pricing',
        difficulty='easy',
        fn='peak_capacity',
        prompt="""Your function gets five things:

- `daily_tasks`: the tasks on a normal day, like `270`.
- `busy_hour_share`: the share of a day's tasks that arrive in its busiest hour, like `0.2`.
- `burst`: how much busier the busiest minute is than an average minute of that hour, like `3`.
- `tokens_per_task`: the tokens one task asks for, like `25000` (5 calls, each 4,000 prompt tokens plus a 1,000-token answer limit).
- `tpm_limit`: your tokens-per-minute limit, like `80000`.

Peak tasks a minute: `daily_tasks` times `busy_hour_share`, divided by 60, times `burst`. Peak tokens a minute: that times `tokens_per_task`, rounded to a whole number.

Return `[peak_tokens, fits]`. `fits` is `True` when the peak tokens are at most `tpm_limit`.""",
        pattern='Turn the daily count into the busiest minute, then compare with the limit.',
        target='a few sums, no loops',
        realworld='Azure checks a deployment\'s limit every few seconds, so a burst hits it long before the hourly totals look busy. Capacity is always sized for the peak, never the average.',
        starter="""def peak_capacity(
        daily_tasks, busy_hour_share, burst,
        tokens_per_task, tpm_limit):
    # your code here
    pass
""",
        solution="""def peak_capacity(
        daily_tasks, busy_hour_share, burst,
        tokens_per_task, tpm_limit):
    per_minute = daily_tasks * busy_hour_share / 60
    peak_tasks = per_minute * burst
    peak = peak_tasks * tokens_per_task
    peak_tokens = int(round(peak))
    fits = peak_tokens <= tpm_limit
    return [peak_tokens, fits]
""",
        cases=[
            case(270, 0.2, 3, 25000, 80000, expected=[67500, True], sample=True),
            case(1000, 0.25, 2, 30000, 200000, expected=[250000, False]),
            case(600, 0.1, 2, 5000, 10000, expected=[10000, True]),
            case(0, 0.2, 3, 25000, 1000, expected=[0, True]),
            case(100, 0.2, 2, 3001, 2000, expected=[2001, False]),
        ],
        guided="""def peak_capacity(
        daily_tasks, busy_hour_share, burst,
        tokens_per_task, tpm_limit):
    # Replace every ___ with real code, then run the tests.

    # Step 1: tasks a minute in the busiest hour.
    per_minute = ___
    # Step 2: the busiest minute is burst times busier.
    peak_tasks = per_minute * burst
    # Step 3: tokens a minute, as a whole number.
    peak = peak_tasks * tokens_per_task
    peak_tokens = int(round(peak))
    # Step 4: True if it is at most the limit.
    fits = ___
    return [peak_tokens, fits]
""",
        fills=['daily_tasks * busy_hour_share / 60', 'peak_tokens <= tpm_limit'],
        concepts=[
            [
                'int(round(x))',
                '`round(x)` rounds to the nearest whole number, and `int()` makes it a whole-number type.',
                'int(round(2000.67))   # 2001',
            ],
            [
                'A comparison is a value',
                '`a <= b` is `True` when a is at most b, and `False` otherwise. You can store it in a name.',
                """ok = 5 <= 5    # True
big = 7 <= 3   # False""",
            ],
            [
                'Returning a list',
                'Put the answers in a list, in the order asked for.',
                """def check(n):
    return [n, n > 10]""",
            ],
        ],
        byhand='270 tickets times 0.2 is 54 in the busiest hour. Divided by 60, that is 0.9 a minute. Times the burst of 3, the busiest minute has 2.7 tickets. Times 25000 tokens, that is 67500 tokens a minute. 67500 is at most 80000, so it fits. Return [67500, True].',
        why='A few multiplications and one comparison, whatever the numbers.',
        gotchas=[
            [
                'Reserving capacity too early',
                '**Provisioned throughput** (reserved capacity, bought in PTUs, provisioned throughput units) costs the same every hour, busy or idle. Start on pay-as-you-go, paying per token used, and reserve only once traffic is high and steady.',
            ],
            [
                'Counting tokens used, not tokens asked for',
                "Foundry's quota counts the prompt plus max_tokens (the longest answer you allow). A huge max_tokens uses up quota even when the answers are short.",
            ],
        ],
    ),
)

lesson(MODULE, 'make_a_skill',
    title='Turn your vetting into a skill',
    learn=[
        "Everything in Frame so far, from the one-line use case and the gates to the review, the cost and the bars, is a routine you will repeat for every new idea. A **Claude skill** packages a routine so Claude follows it the same way every time: a folder holding a **SKILL.md** file of instructions, plus any reference files and scripts it needs.",
        "SKILL.md starts with **YAML frontmatter**: two lines of settings between `---` markers. The **name** is lowercase letters, numbers and hyphens, at most 64 characters, and may not contain \"claude\" or \"anthropic\". The **description**, up to 1,024 characters, says what the skill does and when to use it, in the third person (\"Vets a proposed AI use case. Use when...\"). Claude reads only the name and description of every skill up front, and loads the rest when a request matches: so the description decides whether your skill is ever used.",
        "The body holds the steps and an output format, kept short (Anthropic suggests under 500 lines), with details in reference files it opens only when needed. Anything that must be exact, like adding up the total cost of ownership, goes in a **script** the skill runs, because a model can get sums wrong and a script cannot. This repository ships one: `.claude/skills/vet-ai-use-case`, whose `scripts/tco.py` prints the cost table.",
        "To use it in Claude Code, put the folder in `~/.claude/skills/` (just for you) or a project's `.claude/skills/` (for everyone on the project), then ask Claude to assess an idea or type `/vet-ai-use-case`. On claude.ai, zip the folder and upload it in Settings, with code execution turned on. Then test it like any prompt: run it on a few use cases with known gaps, read what it misses, and change the instructions.",
    ],
    example=example('The top of a SKILL.md', """---
name: vet-ai-use-case
description: Vets a proposed AI use case before
  anything is built. Use when someone asks whether
  an AI idea is worth doing, or wants it costed.
---

# Vet an AI use case

1. Write the use case in one line.
2. Check the three gates.
8. Run python scripts/tco.py inputs.json
   and report its table."""),
    check=question(
        'Your skill must report the total cost of ownership. What is the most reliable way?',
        [
            'Ask Claude in the instructions to add up the costs carefully',
            'Put a script in the skill that works out the total, and have the skill run it',
            'Write the current prices into the description',
        ],
        answer=1,
        why='Sums must be exact, and a script is exact every time. Prices also change, so the skill asks for them instead of storing them.',
    ),
    angle=angle(
        pattern='Check the rules, then write the file',
        text='The big idea: a skill is a SKILL.md file whose name and description Claude reads first, so the file must follow the rules exactly or it will not load. Your code first collects every rule the name or description breaks: characters, length, the reserved words, an empty or too-long description, angle brackets. If there are any, it returns them all, so they can be fixed in one go. Otherwise it builds the file line by line: the frontmatter (the settings between --- markers), a title made from the name, and the steps numbered from 1. It is like filling in a form that is checked before it is sent.',
        say='"I package a routine I repeat as a Claude skill. Its [[description|title|folder::Claude reads it first to decide when to use the skill.]] says what it does and when to use it, and anything exact, like cost sums, goes in a [[script|prompt|comment::A model can get sums wrong; this can\'t.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Write a Valid SKILL.md',
        topic='pricing',
        difficulty='medium',
        fn='make_skill',
        prompt="""Your function gets three things: `name`, `description` (both text) and `steps`, a list of step texts.

First collect every problem, in this order:

- The name is empty, longer than 64 characters, or has a character that is not a lowercase letter, a digit or `-`: add `"name: lowercase letters, numbers and hyphens, 1 to 64 characters"`.
- The name contains `"claude"` or `"anthropic"`: add `"name: may not contain claude or anthropic"`.
- The description is blank (after stripping spaces) or longer than 1024 characters: add `"description: 1 to 1024 characters"`.
- The description contains `<` or `>`: add `"description: no angle brackets"`.

If there are problems, return `{"ok": False, "problems": [...]}`.

Otherwise return `{"ok": True, "text": ...}`, where the text is these lines joined with new lines, plus a new line at the end:

- `---`, then `name: ` and the name, then `description: ` and the description, then `---`
- an empty line, then `# ` and the title, then an empty line. The title is the name with each `-` turned into a space and its first letter in capitals.
- each step as `1. `, `2. ` and so on, then the step.""",
        pattern='Collect every problem first; build the file only when there are none.',
        target='one pass over the name, one over the steps',
        realworld='Claude Code and the Skills API refuse a skill whose name or description breaks these rules. Teams that share skills check them in code before publishing, the same way they lint code.',
        starter="""def make_skill(name, description, steps):
    # your code here
    pass
""",
        solution="""def make_skill(name, description, steps):
    problems = []
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
    ok_chars = True
    for ch in name:
        if ch not in allowed:
            ok_chars = False
    if name == "" or len(name) > 64 or not ok_chars:
        problems.append("name: lowercase letters, numbers and hyphens, 1 to 64 characters")
    if "claude" in name or "anthropic" in name:
        problems.append("name: may not contain claude or anthropic")
    if description.strip() == "" or len(description) > 1024:
        problems.append("description: 1 to 1024 characters")
    if "<" in description or ">" in description:
        problems.append("description: no angle brackets")
    if problems:
        return {"ok": False, "problems": problems}
    title = name.replace("-", " ")
    title = title[:1].upper() + title[1:]
    lines = ["---", "name: " + name, "description: " + description, "---", "", "# " + title, ""]
    for i in range(len(steps)):
        lines.append(str(i + 1) + ". " + steps[i])
    return {"ok": True, "text": "\\n".join(lines) + "\\n"}
""",
        cases=[
            case('vet-ai-use-case', 'Vets a proposed AI use case. Use when someone asks whether an AI idea is worth doing.', ['Write the use case in one line.', 'Check the three gates.', 'Run scripts/tco.py for the cost.'],
                 expected={'ok': True, 'text': '---\nname: vet-ai-use-case\ndescription: Vets a proposed AI use case. Use when someone asks whether an AI idea is worth doing.\n---\n\n# Vet ai use case\n\n1. Write the use case in one line.\n2. Check the three gates.\n3. Run scripts/tco.py for the cost.\n'}, sample=True),
            case('Vet_AI', 'Vets a proposed AI use case. Use when someone asks whether an AI idea is worth doing.', ['x'],
                 expected={'ok': False, 'problems': ['name: lowercase letters, numbers and hyphens, 1 to 64 characters']}),
            case('claude-helper', '', ['x'],
                 expected={'ok': False, 'problems': ['name: may not contain claude or anthropic', 'description: 1 to 1024 characters']}),
            case('tco', 'Works out <cost>', [],
                 expected={'ok': False, 'problems': ['description: no angle brackets']}),
            case('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'Vets a proposed AI use case. Use when someone asks whether an AI idea is worth doing.', ['x'],
                 expected={'ok': False, 'problems': ['name: lowercase letters, numbers and hyphens, 1 to 64 characters']})
        ],
        guided="""def make_skill(name, description, steps):
    # Replace every ___ with real code, then run the tests.
    problems = []
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
    # Step 1: is every character of the name allowed?
    ok_chars = True
    for ch in name:
        if ch not in allowed:
            ok_chars = False
    if name == "" or len(name) > 64 or not ok_chars:
        problems.append("name: lowercase letters, numbers and hyphens, 1 to 64 characters")
    # Step 2: the reserved words.
    if "claude" in name or "anthropic" in name:
        problems.append("name: may not contain claude or anthropic")
    # Step 3: the description's length.
    if ___:
        problems.append("description: 1 to 1024 characters")
    if "<" in description or ">" in description:
        problems.append("description: no angle brackets")
    if problems:
        return {"ok": False, "problems": problems}
    # Step 4: the title, then the file, line by line.
    title = name.replace("-", " ")
    title = title[:1].upper() + title[1:]
    lines = ["---", "name: " + name, "description: " + description, "---", "", "# " + title, ""]
    for i in range(len(steps)):
        lines.append(___)
    return {"ok": True, "text": "\\n".join(lines) + "\\n"}
""",
        fills=['description.strip() == "" or len(description) > 1024', 'str(i + 1) + ". " + steps[i]'],
        concepts=[
            [
                'Collecting problems in a list',
                'Check every rule and append each problem, instead of stopping at the first one, so they can all be fixed at once.',
                """problems = []
if len("ab") > 1:
    problems.append("too long")
problems   # ["too long"]""",
            ],
            [
                'Checking every character',
                'Loop over a string to look at each character; `in` checks it is one of the allowed ones.',
                """ok = True
for ch in "ab-1":
    if ch not in "abc-1":
        ok = False""",
            ],
            [
                'Slices for a capital letter',
                '`title[:1]` is the first character and `title[1:]` the rest; `.upper()` makes it a capital.',
                '"vet it"[:1].upper() + "vet it"[1:]   # "Vet it"',
            ],
        ],
        byhand='Name "vet-ai-use-case": every character allowed, 15 long, no reserved word. The description is filled and short, with no angle brackets. No problems, so build: ---, the name line, the description line, ---, an empty line, "# Vet ai use case", an empty line, then "1. Write the use case in one line.", "2. Check the three gates.", "3. Run scripts/tco.py for the cost.", joined with new lines and one at the end.',
        why='Each character of the name and each step is looked at once.',
        gotchas=[
            [
                'A vague description',
                'Claude decides whether to use a skill from its description alone. "Helps with AI" never triggers; "Vets a proposed AI use case. Use when someone asks whether an AI idea is worth doing" does.',
            ],
            [
                'Letting the model do the sums',
                'Models can get arithmetic wrong, and quietly. Put exact work, like the cost total, in a script the skill runs, and report the script\'s output.',
            ],
        ],
    ),
)
