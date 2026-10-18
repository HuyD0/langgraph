"""Pricing and sizing: What an AI task really costs (tokens, embeddings, search, tools and people), what it saves, which deployment to buy and how much capacity it needs, worked out before you build and packaged as a skill you can rerun."""

from drill.content.model import (angle, ask, card, case, evidence, example, exercise, lesson, module, pile, piles, practice, question,
                                 rewrite, seesaw, sortby, sortrow, source, stack, steps)

MODULE = module('pricing', 'Pricing and sizing', 'What an AI task really costs (tokens, embeddings, search, tools and people), what it saves, which deployment to buy and how much capacity it needs, worked out before you build and packaged as a skill you can rerun.')

lesson(MODULE, 'cost_per_finished_task',
    title='Cost per finished task',
    checked='2026-10-15',
    sources=[
        source('Gartner Predicts 30% of Generative AI Projects Will Be Abandoned After Proof of Concept By End of 2025', 'https://www.gartner.com/en/newsroom/press-releases/2024-07-29-gartner-predicts-30-percent-of-generative-ai-projects-will-be-abandoned-after-proof-of-concept-by-end-of-2025'),
        source('Better Call GPT, Comparing Large Language Models Against Lawyers (arXiv 2401.16212)', 'https://arxiv.org/abs/2401.16212'),
    ],
    learn=[
        'Work out what an AI task costs, and what it saves, before you build it. In July 2024 the research firm Gartner forecast that at least 30 in 100 generative AI projects would be dropped after the trial stage by the end of 2025, partly over rising costs and unclear value. Pricing first also tells your trial which numbers it must measure.',
        "Don't price only the tokens. The **cost per finished task** (its **fully loaded cost**) is the model's bill, plus a person checking some answers (**human review**), plus redoing the answers that fail (**rework**). In an HR ticket bot the model is under 4 percent of it.",
        'Mistakes nobody catches cost extra on top: in the HR ticket bot, 5 in 100 wrong answers slip through and cost $10 each to sort out later, so 50 cents a ticket. Some write-ups add this in, which makes about $2.37 a ticket. Here we keep it apart, and the payback lesson takes it off the saving.',
        "Each number has a source. The **price list** gives the token price, and the **POC** (proof of concept, a small trial build) measures the tokens and how often answers fail. The **owner** of the use case (the product manager) gives the hourly rate, today's cost of a task, how many answers get checked and how long a check takes.",
    ],
    example=example('One HR ticket, $8 by hand today', """# 30 in 100 answers checked,
# 2 minutes each, at $60 an hour
rate = 60             # dollars an hour
hours = 0.3 * 2 / 60  # 0.01 hours
check = hours * rate  # 0.60
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
- `hourly_rate`: what an hour of that person's time costs, like `60`.
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
            case(0.13, 0.3, 2, 60, 0.15, 8, expected=1.93, sample=True),
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
        byhand='Model: 0.13 dollars. Checking: 0.3 times 2 is 0.6 minutes a task. Divided by 60 that is 0.01 hours, and times 60 dollars an hour that is 0.60. Failures: 0.15 times 8 is 1.20. Add them: 0.13 plus 0.60 plus 1.20 is 1.93. Return 1.93.',
        why='A handful of multiplications and one sum, whatever the numbers.',
        gotchas=[
            [
                'Pricing tokens only',
                "In one 2024 contract-review study, a junior lawyer cost about $74 a document and the models 2 cents to $1.24. The study itself says that leaves out the people who must keep checking the model's answers. Count their time, and the redoing of wrong answers, and the gap shrinks a lot: in the HR example the model is under 4 percent of the total.",
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
    checked='2026-10-17',
    sources=[
        source('Anthropic: Prompt caching', 'https://platform.claude.com/docs/en/build-with-claude/prompt-caching'),
        source('OpenAI: Prompt caching', 'https://developers.openai.com/api/docs/guides/prompt-caching'),
    ],
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
            [
                'Pricing every input token at full price',
                'Providers charge much less, often a tenth of the input price, for the part of the prompt they have seen recently (prompt caching). OpenAI does it on its own once a prompt is long enough (1,024 tokens on its newer models). Claude caches only when the request carries a cache_control mark. The bill still grows every step, just more slowly than the token count, so price from the usage your traces report, which splits cached from fresh tokens.',
            ],
        ],
    ),
)

lesson(MODULE, 'total_cost',
    title='Total cost of ownership',
    checked='2026-10-18',
    sources=[source('Design principles for AI workloads on Azure: Cost Optimization', 'https://learn.microsoft.com/azure/well-architected/ai/design-principles#cost-optimization')],
    learn=[
        "The **total cost of ownership** (TCO) is everything it costs to have the system for its whole life, not just to call the model. It is the cost side of every business case, and the tokens are often the smallest part.",
        "Its variables fall into three groups. **Build**, paid once: people's time, preparing data, building the eval set, the security review. **Run**, paid every month: the model's tokens, hosting and compute, the vector search index, tracing and monitoring, and people checking and redoing answers. **Maintain** (keeping it working), also monthly: re-running evals when the model or prompt changes, updating prompts, and someone on call.",
        "For a typical **RAG pipeline** on Azure, the monthly lines are: LLM calls (the answers, plus embeddings for new documents and every question), retrieval (Azure AI Search, or Databricks AI Search), Databricks compute for the jobs that chunk (cut into passages) and embed documents, and storage for documents, chunks and traces. The first indexing of all the documents is a one-off.",
        "Microsoft's cost guidance for AI says to find the cost drivers first: how much data you index, how many queries arrive, the throughput you need, and the hidden costs of the services underneath, like the step that prepares documents before they are indexed.",
        'Add it up over the years you plan to run it: the one-off costs, plus every monthly cost times 12 times the years. Then look at the biggest single item, because that is where a saving matters most.',
    ],
    example=example('Two years of the HR assistant', """build = {"build team": 60000, "eval set": 8000,
         "security review": 5000}      # 73000
monthly = {"model": 390, "hosting": 1200,
           "evals": 1100, "people": 10800}
# people: checking and redoing answers
# 13490 a month for 24 months: 323760
# total: 396760
# biggest item: people, 10800 x 24 = 259200,
# more than three times the whole build"""),
    check=question(
        'Two years of an AI assistant cost $396,760. Which change cuts the most?',
        [
            'A model that is half the price per token',
            'Fewer answers for a person to check or redo',
            'A cheaper security review before launch',
        ],
        answer=1,
        why='People checking and redoing answers cost $10,800 a month, $259,200 over two years. Halving the model saves about $4,700, and the security review is paid only once.',
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
- `monthly`: a dict of costs paid every month, like `{"model": 390}`.
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
                 {"model": 390, "hosting": 1200, "evals": 1100, "people": 10800}, 2,
                 expected=[396760, "people"], sample=True),
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
                """costs = {"model": 390}
for name in costs:
    print(name, costs[name])   # model 390""",
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
        byhand='24 months. Build: 60000 + 8000 + 5000 = 73000; biggest so far is the build team at 60000. Monthly: model 390 times 24 = 9360, hosting 28800, evals 26400, people 10800 times 24 = 259200, now the biggest. Total 73000 + 323760 = 396760. Return [396760, "people"].',
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

OAI_PRICING = source('OpenAI API pricing', 'https://developers.openai.com/api/docs/pricing')
AZURE_OPENAI_PRICING = source('Azure OpenAI pricing', 'https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/')
DBX_MODEL_PRICING = source('Databricks Foundation Model Serving pricing', 'https://www.databricks.com/product/pricing/foundation-model-serving')

lesson(MODULE, 'embedding_cost',
    title='The cost of embeddings',
    checked='2026-10-18',
    sources=[OAI_PRICING, AZURE_OPENAI_PRICING, DBX_MODEL_PRICING],
    cards=[
        card('Text becomes numbers, and you pay per token',
             'An **embedding** turns text into a list of numbers, a **vector**, so a search can find text with a similar meaning. A RAG app embeds every chunk of every document, and every question. It is billed per token, like any model, but cheaply.',
             picture=piles(pile('OpenAI and Azure OpenAI', [('coin', 'text-embedding-3-small: $0.02 a million'), ('coin', 'text-embedding-3-large: $0.13 a million')]),
                           pile('Databricks', [('coin', 'GTE large: about $0.13 a million'), ('coin', 'Qwen3 0.6B: about $0.02 a million')])),
             after='Prices from each pricing page, checked on the date at the bottom. On Azure, one region can cost a little more than a Global deployment: $0.022 against $0.02 for 3-small.'),
        card('Three times you pay',
             'Embeddings cost something at three moments.',
             picture=sortby('When do you pay?',
                            sortrow('Every document', 'Once, when you first build the index', 'One-off', icon='layers'),
                            sortrow('New documents and every question', 'Every month: a question becomes a vector before the search', 'Monthly', icon='clock'),
                            sortrow('Every document, again', 'When you change the embedding model: vectors from two models can\'t be compared', 'Re-embedding', icon='reset'))),
        card('The sum, step by step',
             'Count the tokens, then multiply by the price per million and divide by a million.',
             picture=steps(('listcheck', 'Count the tokens', '2,000 HR documents times 1,500 tokens = 3,000,000 tokens.'),
                           ('coin', 'Times the price', '3 million times $0.02 = $0.06, once.'),
                           ('clock', 'Every month', '100 new documents and 30,000 questions: 900,000 tokens, about $0.02.')),
             after='Embeddings are rarely the big line. The search service that holds the vectors usually is: that is the next lesson.'),
        card('A better model costs one more full pass',
             'A newer embedding model can find better matches, but every document has to be embedded again.',
             picture=seesaw(('Better search', 'the newer model'), ('One-off cost', 'every document again'), caption='Put the re-embedding in the plan before anyone swaps the model.')),
    ],
    example=example('The HR assistant\'s embeddings', """price = 0.02 / 1000000   # $ a token
first = 2000 * 1500 * price
# 3,000,000 tokens: $0.06, once
new = 100 * 1500          # new docs
asks = 30000 * 25         # questions
month = (new + asks) * price
# 900,000 tokens: about $0.02 a month"""),
    check=question(
        'You move the HR assistant to a newer embedding model. What happens to the embedding bill?',
        [
            'Every document is embedded again, once',
            'Only new documents use the new model',
            'Nothing: the old vectors still work',
        ],
        answer=0,
        why='Vectors from two models can\'t be compared, so every chunk is embedded again: a one-off cost as big as the first indexing. For the HR documents that is 3,000,000 tokens times $0.02 divided by 1,000,000 = $0.06.',
    ),
    angle=angle(
        pattern='Tokens times the price, once and every month',
        text='The big idea: embeddings cost tokens like any model, once for every document, then every month for new documents and every question, and again in full if you change the embedding model. Your code turns the price per million into a price per token. The one-off cost is the documents times their tokens times that price. The monthly cost adds the new documents\' tokens to the questions\' tokens and multiplies by the same price. It returns both, rounded to cents. It is like printing: the first print run of the whole book, then a few new pages every month.',
        say='"I price embeddings in three parts: every document [[once|daily|never::When you first build the index.]], new documents and questions every [[month|year|run::They keep arriving.]], and everything again if I change the [[model|prompt|server::Vectors from two of these can\'t be compared.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Price the Embeddings',
        topic='pricing',
        difficulty='easy',
        fn='embedding_cost',
        prompt="""Your function gets `plan`, a dict:

- `"docs"`: how many documents to embed at the start, and `"tokens_per_doc"`: tokens in each one.
- `"new_docs"`: new documents a month, the same size.
- `"questions"`: questions a month, and `"tokens_per_question"`.
- `"price_per_million"`: dollars per million tokens.

The one-off cost is every document's tokens times the price. The monthly cost is the new documents' tokens plus the questions' tokens, times the price.

Return `[one_off, monthly]`, each rounded to 2 decimal places.""",
        pattern='Count the tokens, then multiply by the price per token.',
        target='a few multiplications',
        realworld='When a RAG pipeline is priced, embeddings are a small line, but re-embedding a large document set after a model change is a real one-off cost. Put it in the plan before anyone swaps the model.',
        starter="""def embedding_cost(plan):
    # your code here
    pass
""",
        solution="""def embedding_cost(plan):
    price = plan["price_per_million"] / 1000000
    first = plan["docs"] * plan["tokens_per_doc"] * price
    new = plan["new_docs"] * plan["tokens_per_doc"]
    asks = plan["questions"] * plan["tokens_per_question"]
    monthly = (new + asks) * price
    return [round(first, 2), round(monthly, 2)]
""",
        cases=[
            case({"docs": 2000, "tokens_per_doc": 1500, "new_docs": 100, "questions": 30000, "tokens_per_question": 25, "price_per_million": 0.02},
                 expected=[0.06, 0.02], sample=True),
            case({"docs": 200000, "tokens_per_doc": 1500, "new_docs": 5000, "questions": 300000, "tokens_per_question": 25, "price_per_million": 0.13},
                 expected=[39.0, 1.95]),
            case({"docs": 0, "tokens_per_doc": 1500, "new_docs": 0, "questions": 0, "tokens_per_question": 25, "price_per_million": 0.02},
                 expected=[0.0, 0.0]),
        ],
        guided="""def embedding_cost(plan):
    # Replace every ___ with real code, then run the tests.
    # Step 1: the price of one token.
    price = plan["price_per_million"] / 1000000
    # Step 2: every document, once.
    first = ___
    # Step 3: new documents and questions, each month.
    new = plan["new_docs"] * plan["tokens_per_doc"]
    asks = plan["questions"] * plan["tokens_per_question"]
    monthly = ___
    return [round(first, 2), round(monthly, 2)]
""",
        fills=['plan["docs"] * plan["tokens_per_doc"] * price', '(new + asks) * price'],
        concepts=[
            [
                'Price per million',
                'Prices are quoted per million tokens. Divide by 1,000,000 to get the price of one token, then multiply by the tokens.',
                """price = 0.02 / 1000000
3000000 * price   # 0.06""",
            ],
            [
                'round',
                '`round(x, 2)` keeps two decimal places, like cents.',
                'round(1.9512, 2)   # 1.95',
            ],
        ],
        byhand='The price of a token is 0.02 divided by 1,000,000. Every document: 2,000 times 1,500 = 3,000,000 tokens, times 0.02 divided by 1,000,000 = $0.06. Each month: new documents 100 times 1,500 = 150,000 tokens, questions 30,000 times 25 = 750,000 tokens, together 900,000 tokens times 0.02 divided by 1,000,000 = $0.018, which rounds to $0.02. Return [0.06, 0.02].',
        why='A few multiplications, whatever the size of the plan.',
        gotchas=[
            [
                'Forgetting the questions',
                'Every question is embedded too, before the search. With many users, the questions can outgrow the new documents.',
            ],
            [
                'Forgetting re-embedding',
                'A new embedding model means embedding every document again. Price it as a one-off before you switch.',
            ],
        ],
    ),
)

lesson(MODULE, 'vector_storage',
    title='Storing and searching vectors',
    checked='2026-10-18',
    sources=[
        source('OpenAI: Vector embeddings', 'https://developers.openai.com/api/docs/guides/embeddings'),
        source('Azure AI Search pricing', 'https://azure.microsoft.com/en-us/pricing/details/search/'),
        source('Azure AI Search service limits', 'https://learn.microsoft.com/en-us/azure/search/search-limits-quotas-capacity'),
        source('Databricks AI Search pricing', 'https://www.databricks.com/product/pricing/ai-search'),
        source('Databricks AI Search cost management', 'https://learn.microsoft.com/en-us/azure/databricks/ai-search/cost-management'),
    ],
    cards=[
        card('How much space the vectors take',
             'Each vector is a list of numbers, usually stored as 4 bytes each. text-embedding-3-small gives 1,536 numbers per chunk, and text-embedding-3-large 3,072, twice the space.',
             picture=steps(('layers', 'How many chunks', '2,000,000 chunks.'),
                           ('listcheck', 'Times the numbers in each', 'Times 1,536 numbers per vector.'),
                           ('chart', 'Times 4 bytes', '12,288,000,000 bytes: about 12.3 GB.'))),
        card('You pay for capacity, not gigabytes',
             'Search services bill units kept running every hour, used or not.',
             picture=piles(pile('Azure AI Search', [('coin', 'S1: about $245 a month a unit'), ('layers', '35 GB of vectors per partition'), ('coin', 'Basic: about $74 a month, 5 GB')]),
                           pile('Databricks AI Search', [('coin', 'Standard: $0.28 an hour, about $204 a month'), ('layers', '2,000,000 vectors of 768 numbers a unit')])),
             after='Databricks AI Search was called Vector Search before. An endpoint nobody searches still bills every hour it exists.'),
        card('The bill moves in steps',
             'You buy whole units, so a little growth can add a whole unit.',
             picture=sortby('How many 35 GB units?',
                            sortrow('34 GB of vectors', 'It fits in one', '1 unit', icon='check'),
                            sortrow('36 GB of vectors', 'One is not enough', '2 units', icon='alert'),
                            sortrow('73.7 GB of vectors', '73.7 divided by 35 is 2.1: round up', '3 units', icon='alert'))),
        card('Shorter vectors, smaller bill',
             'OpenAI\'s newer models let you ask for fewer numbers per vector. Its docs say text-embedding-3-large cut to 256 numbers still beats the older ada-002 model at 1,536.',
             picture=seesaw(('Less space', 'fewer numbers per vector'), ('Quality', 'may drop a little'), caption='Check the quality on your eval set before you shrink them.')),
    ],
    example=example('How many units do the vectors need?', """size = 2000000 * 1536 * 4   # bytes
# 12,288,000,000 bytes: about 12.3 GB
# one S1 partition holds 35 GB: 1 unit
size = 6000000 * 3072 * 4
# about 73.7 GB: 73.7 / 35 = 2.1,
# so 3 units, about 3 x $245 a month"""),
    check=question(
        'Your vectors grow from 34 GB to 36 GB, and each unit holds 35 GB. What happens to the bill?',
        [
            'It doubles: you need a second unit',
            'It grows by about 6 percent',
            'Nothing until you reach 70 GB',
        ],
        answer=0,
        why='36 GB no longer fits one 35 GB unit, so you pay for two: about 2 times $245 a month instead of 1 times $245. Capacity is bought in whole units, so the bill moves in steps.',
    ),
    angle=angle(
        pattern='Work out the size, then round up to whole units',
        text='The big idea: vector storage is vectors times dimensions times 4 bytes, but search services bill whole units of capacity kept running, so the bill jumps a step each time the vectors outgrow a unit. Your code works out the bytes and divides by a billion to get gigabytes. It divides by the gigabytes a unit holds, keeping the whole number, and adds one more unit if any space is left over. It never returns fewer than one unit. It returns the gigabytes, rounded to 2 places, and the units. It is like booking hotel rooms: 5 guests with 2 to a room need 3 rooms, not 2.5.',
        say='"For vector search I work out the size: vectors times dimensions times [[4|8|1::The bytes in one stored number.]] bytes. Then I [[round up|round down|average::Half a unit can\'t be bought.]] to whole units, because the bill is for [[capacity|gigabytes|queries::Units kept running, used or not.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Count the Search Units',
        topic='pricing',
        difficulty='easy',
        fn='search_units',
        prompt="""Your function gets three numbers: `vectors` (how many), `dims` (numbers in each vector) and `gb_per_unit` (gigabytes of vectors one unit holds).

Each number takes 4 bytes, and a gigabyte here is 1,000,000,000 bytes.

Return `[gb, units]`: the size in gigabytes rounded to 2 decimal places, and how many whole units you need. Round the units up: any space left over needs another unit. Always return at least 1 unit.""",
        pattern='Divide, keep the whole part, and add one if anything is left over.',
        target='a few sums',
        realworld='Search services bill whole units of capacity. Sizing vectors before you build tells you whether the index fits the tier you planned, and when growth will add a unit.',
        starter="""def search_units(vectors, dims, gb_per_unit):
    # your code here
    pass
""",
        solution="""def search_units(vectors, dims, gb_per_unit):
    gb = vectors * dims * 4 / 1000000000
    units = int(gb // gb_per_unit)
    if gb > units * gb_per_unit:
        units = units + 1
    if units < 1:
        units = 1
    return [round(gb, 2), units]
""",
        cases=[
            case(2000000, 1536, 35, expected=[12.29, 1], sample=True),
            case(6000000, 3072, 35, expected=[73.73, 3]),
            case(8750000, 1000, 35, expected=[35.0, 1]),
            case(8000, 1536, 5, expected=[0.05, 1]),
        ],
        guided="""def search_units(vectors, dims, gb_per_unit):
    # Replace every ___ with real code, then run the tests.
    # Step 1: 4 bytes a number, a billion bytes a gigabyte.
    gb = ___
    # Step 2: the whole units that fit.
    units = int(gb // gb_per_unit)
    # Step 3: anything left over needs one more.
    if ___:
        units = units + 1
    if units < 1:
        units = 1
    return [round(gb, 2), units]
""",
        fills=['vectors * dims * 4 / 1000000000', 'gb > units * gb_per_unit'],
        concepts=[
            [
                'Whole-number division',
                '`a // b` divides and drops the part after the point, so `73.7 // 35` is `2.0`. `int(...)` makes it a whole number.',
                'int(73.7 // 35)   # 2',
            ],
            [
                'Rounding up by hand',
                'If what fits in whole units is less than what you have, one more unit is needed.',
                """units = 2
if 73.7 > units * 35:
    units = units + 1   # 3""",
            ],
        ],
        byhand='2,000,000 times 1,536 times 4 = 12,288,000,000 bytes, divided by 1,000,000,000 = 12.288 GB. 12.288 // 35 is 0, and 12.288 is more than 0 times 35, so add one: 1 unit. Return [12.29, 1].',
        why='A few sums, however many vectors there are.',
        gotchas=[
            [
                'Pricing by the gigabyte',
                'Search services bill units kept running, not gigabytes. A small index still pays for a whole unit, every hour.',
            ],
            [
                'Rounding down',
                '2.1 units means 3 units. Half a unit can\'t be bought.',
            ],
        ],
    ),
)

lesson(MODULE, 'paid_tools',
    title='Tools billed per call or per page',
    checked='2026-10-18',
    sources=[
        source('Grounding with Bing Search pricing', 'https://www.microsoft.com/en-us/bing/apis/grounding-pricing'),
        OAI_PRICING,
        source('Claude API pricing', 'https://platform.claude.com/docs/en/about-claude/pricing'),
        source('Azure AI Document Intelligence pricing', 'https://azure.microsoft.com/en-us/pricing/details/ai-document-intelligence/'),
    ],
    cards=[
        card('Paid per use, not per token',
             'Some services charge for each use, and they can cost more than the model.',
             picture=piles(pile('Web search', [('search', 'Grounding with Bing Search: $14 per 1,000'), ('search', 'OpenAI or Anthropic: $10 per 1,000, plus tokens')]),
                           pile('Azure AI Document Intelligence', [('book', 'Read the text: $1.50 per 1,000 pages'), ('book', 'Layout and tables: $10 per 1,000 pages'), ('book', 'Custom model: $30 per 1,000 pages')]))),
        card('The sum, step by step',
             'The uses, times the price, divided by 1,000.',
             picture=steps(('search', 'Count the uses', 'Half of 30,000 questions search once: 15,000 searches.'),
                           ('coin', 'Times the price', '15,000 times $14 divided by 1,000 = $210 a month.'),
                           ('book', 'Pages work the same way', '20,000 pages for tables: 20,000 times $10 divided by 1,000 = $200, once.'))),
        card('Agents multiply it',
             'An agent can call a tool several times for one question. Take the calls per question from your traces.',
             picture=sortby('Searches per question, 30,000 questions a month',
                            sortrow('1 search each', '30,000 times $14 divided by 1,000', '$420 a month', icon='search'),
                            sortrow('3 searches each', '90,000 times $14 divided by 1,000', '$1,260 a month', icon='alert'))),
        card('Pay once, not on every question',
             'Use the cheapest service that does the job, and do the work once.',
             picture=rewrite(('Read the pages again for every question', 'Read each document once, when it arrives'),
                             ('Layout for every page', 'Read the text at $1.50 when you need no tables'),
                             ('Let the agent search as often as it likes', 'Cap the searches per task'))),
    ],
    example=example('The HR assistant\'s paid tools', """# web search: half of 30,000 questions
15000 * 14 / 1000     # $210 a month
# an agent searching 3 times each
30000 * 3 * 14 / 1000 # $1,260 a month
# tables from 20,000 pages, once
20000 * 10 / 1000     # $200
20000 * 1.5 / 1000    # $30 for text only"""),
    check=question(
        'An agent answers 10,000 questions a month and searches the web 3 times for each, at $14 per 1,000 searches. What is the monthly search bill?',
        ['$140', '$420', '$42'],
        answer=1,
        why='10,000 times 3 = 30,000 searches, and 30,000 times $14 divided by 1,000 = $420. The 3 searches per question is what multiplies it.',
    ),
    angle=angle(
        pattern='Uses times the price per thousand',
        text='The big idea: tools like web search and document reading charge per use, so the bill is uses times price divided by 1,000, and an agent that calls a tool several times per task multiplies it. Your code goes through the tools. For each it multiplies the tasks by the uses per task and the price per 1,000, then divides by 1,000. It adds that to the total and keeps the name of the tool with the biggest cost so far. It returns the total, rounded to cents, and that name. It is like a phone bill charged per call: count the calls, not the minutes.',
        say='"Tools like web search bill per [[use|token|month::Each search or page counts.]]: uses times the price, divided by a [[thousand|million|hundred::Prices here are quoted per this many.]]. And an agent that calls a tool three times a task pays [[three|one|ten::It multiplies.]] times."',
        classic=None,
    ),
    exercise=exercise(
        title='Add Up the Tool Bill',
        topic='pricing',
        difficulty='easy',
        fn='tool_bill',
        prompt="""Your function gets `tools`, a list of dicts, each with:

- `"name"`: the tool, like `"web search"`
- `"tasks"`: tasks a month that use it
- `"per_task"`: how many times each of those tasks uses it (it can be a fraction, like `0.5`)
- `"price_per_1000"`: dollars per 1,000 uses

A tool's monthly cost is tasks times per_task times price_per_1000 divided by 1000.

Return `[total, biggest]`: the total of all tools rounded to 2 decimal places, and the name of the tool that costs the most (on a tie, the first one). No tools gives `[0, None]`.""",
        pattern='Work out each line, add it to the total, and keep the biggest so far.',
        target='one pass over the tools',
        realworld='Agent designs list their tools, but the bill comes from how often each one is called. Pricing each tool per use, with the calls per task taken from traces, shows which one to cap first.',
        starter="""def tool_bill(tools):
    # your code here
    pass
""",
        solution="""def tool_bill(tools):
    total = 0
    biggest = None
    biggest_cost = -1
    for tool in tools:
        uses = tool["tasks"] * tool["per_task"]
        cost = uses * tool["price_per_1000"] / 1000
        total = total + cost
        if cost > biggest_cost:
            biggest = tool["name"]
            biggest_cost = cost
    return [round(total, 2), biggest]
""",
        cases=[
            case([{"name": "web search", "tasks": 30000, "per_task": 0.5, "price_per_1000": 14},
                  {"name": "document layout", "tasks": 2000, "per_task": 10, "price_per_1000": 10}],
                 expected=[410.0, "web search"], sample=True),
            case([{"name": "agent search", "tasks": 10000, "per_task": 3, "price_per_1000": 14}], expected=[420.0, "agent search"]),
            case([], expected=[0, None]),
            case([{"name": "read text", "tasks": 20000, "per_task": 1, "price_per_1000": 1.5},
                  {"name": "layout", "tasks": 20000, "per_task": 1, "price_per_1000": 10}],
                 expected=[230.0, "layout"]),
        ],
        guided="""def tool_bill(tools):
    # Replace every ___ with real code, then run the tests.
    total = 0
    biggest = None
    biggest_cost = -1
    for tool in tools:
        # Step 1: how many times it is used in a month.
        uses = ___
        # Step 2: the price is per 1,000 uses.
        cost = uses * tool["price_per_1000"] / 1000
        total = total + cost
        # Step 3: keep the biggest so far.
        if ___:
            biggest = tool["name"]
            biggest_cost = cost
    return [round(total, 2), biggest]
""",
        fills=['tool["tasks"] * tool["per_task"]', 'cost > biggest_cost'],
        concepts=[
            [
                'Price per thousand',
                'Divide the uses by 1,000 and multiply by the price, or multiply first and divide after: the answer is the same.',
                '15000 * 14 / 1000   # 210.0',
            ],
            [
                'Keeping the biggest so far',
                'Start with a value below any real one, like -1, and replace it whenever you see a bigger one.',
                """best = -1
for x in [210, 200]:
    if x > best:
        best = x   # 210""",
            ],
        ],
        byhand='Web search: 30,000 times 0.5 = 15,000 uses, times 14 divided by 1,000 = $210. Document layout: 2,000 times 10 = 20,000 pages, times 10 divided by 1,000 = $200. Total $410. Web search costs the most. Return [410.0, "web search"].',
        why='Each tool is worked out once, so the work grows with the number of tools.',
        gotchas=[
            [
                'Pricing one call per task',
                'Agents often call a tool several times for one task. Take the calls per task from traces, not from the design.',
            ],
            [
                'Paying per question for the same document',
                'Read each document once, when it arrives, and store the result. Don\'t pay per page every time someone asks about it.',
            ],
        ],
    ),
)

lesson(MODULE, 'find_the_price',
    title='Where to find the real price',
    checked='2026-10-18',
    sources=[
        source('Azure pricing calculator', 'https://azure.microsoft.com/en-us/pricing/calculator/'),
        source('Claude API pricing', 'https://platform.claude.com/docs/en/about-claude/pricing'),
        source('Databricks pricing', 'https://www.databricks.com/product/pricing'),
        source('Databricks GenAI pricing calculator', 'https://www.databricks.com/product/pricing/genai-pricing-calculator'),
        DBX_MODEL_PRICING,
        source('Azure AI Document Intelligence pricing', 'https://azure.microsoft.com/en-us/pricing/details/ai-document-intelligence/'),
    ],
    cards=[
        card('Start from the pricing page',
             'Every price in these lessons comes from a provider\'s pricing page, and those pages change.',
             picture=steps(('search', 'Find the page', 'The provider\'s pricing page, the Azure pricing calculator, or the Databricks pricing pages.'),
                           ('listcheck', 'Read the unit first', 'Per million tokens, per 1,000 pages, per hour, or per DBU.'),
                           ('coin', 'Turn it into one task', 'What one finished task uses, times the price of one unit.'),
                           ('pencil', 'Write the source and the date', 'So anyone can check it, and update it when the page changes.'))),
        card('DBUs into dollars',
             'A **DBU** (Databricks Unit) is the measure Databricks bills by. Multiply the DBUs by the price of one DBU, which depends on the product, the cloud, the region and your tier: for model serving in US East, $0.07.',
             picture=sortby('What is it in dollars?',
                            sortrow('GTE large embeddings: 1.857 DBU a million tokens', '1.857 times $0.07', '$0.13 a million', icon='coin'),
                            sortrow('AI Search Standard: 4 DBU an hour', '4 times $0.07', '$0.28 an hour', icon='coin'))),
        card('The page shows a list price',
             'The real price depends on more than the page, and Azure\'s pricing pages say so themselves. Ask whoever buys cloud services at your company for your rate.',
             picture=piles(pile('On the page', ['The list price', 'One region', 'The standard tier']),
                           pile('What you pay', [('people', 'Your company\'s agreement'), ('cloud', 'Your region and currency'), ('tag', 'Batch, Global or reserved tier')]))),
        card('Check the estimate against the bill',
             'After launch, swap estimates for the real bill: Azure Cost Management, or on Databricks the `system.billing.usage` table.',
             picture=sortby('Estimate against the real bill',
                            sortrow('Embeddings: $0.02 planned, $0.02 billed', 'On plan', 'Fine', icon='check'),
                            sortrow('Web search: $210 planned, $630 billed', '3 times the plan: check the traces', 'Look into it', icon='alert'))),
    ],
    example=example('One task, priced from its pages', """# Claude Sonnet 5.5: $2 in, $10 out per million
1800 * 2 / 1000000      # $0.0036 in
300 * 10 / 1000000      # $0.003 out
# web search: $14 per 1,000, half a search
0.5 * 14 / 1000         # $0.007
# one task: $0.0136
# source and date next to each line"""),
    check=question(
        'Your worksheet says "web search: $14 per 1,000". What else should that line have?',
        [
            'The page it came from, and the date',
            'The name of the person who typed it',
            'A note saying prices never change',
        ],
        answer=0,
        why='Prices change, and they differ by region and agreement. With the page and the date, anyone can check the number and update it when the page changes.',
    ),
    angle=angle(
        pattern='Price per unit, times the units one task uses',
        text='The big idea: every price is a number per unit, so read the unit, turn it into what one task uses, and write down where and when you found it. Your code goes through the lines. For each it divides the price by the size of its unit, like 1,000,000 tokens or 1,000 searches, and multiplies by how much of it one task uses. It adds the lines up and returns the cost of one task, rounded to 4 decimal places. It is like a recipe\'s cost: flour by the kilo, eggs by the dozen, but you only use 200 grams and 2 eggs.',
        say='"I take each price from the provider\'s [[pricing page|blog|forum::The official place prices are listed.]], read its unit, and turn it into the cost of one [[task|month|token::One finished piece of work.]]. Then I write down the source and the [[date|author|tier::Prices change, so note when you looked.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Price One Task',
        topic='pricing',
        difficulty='easy',
        fn='cost_per_task',
        prompt="""Your function gets `lines`, a list of dicts, one per thing a task uses:

- `"price"`: the price from the pricing page, in dollars
- `"per"`: the size of the unit that price is for, like `1000000` for per million tokens or `1000` for per 1,000 searches
- `"used"`: how much of it one task uses, like `1800` tokens or `0.5` searches

Each line costs price divided by per times used.

Return the cost of one task, the sum of the lines, rounded to 4 decimal places. No lines gives `0`.""",
        pattern='Turn each price into a price per unit, then multiply by what one task uses.',
        target='one pass over the lines',
        realworld='Pricing pages quote per million tokens, per 1,000 pages or per hour. Turning each into the cost of one finished task is how a business case compares AI with doing the work by hand.',
        practice=practice(
            intro='Use real pricing pages the way you will at work: read the unit, turn it into your numbers, and check what the page doesn\'t say.',
            explain='The big idea: a price only means something with its unit, its source and its date. You turned "per 1,000 pages" into the cost of 20,000 pages, turned DBUs into dollars, spotted that a list price leaves out your region and your company\'s agreement, and went looking for the reason when the real bill came in at 3 times the estimate.',
            pattern='Read the unit, then check the bill',
            realworld='When you price a new AI feature, take each number from the provider\'s pricing page, note the page and the date, and ask whoever buys cloud services for your company\'s rate. After launch, compare every line with the real bill.',
            gotchas=[
                ['Reading the number before the unit', '$10 per 1,000 pages and $10 per million tokens are very different bills. Read what the price is per before you use it.'],
                ['Treating the list price as your price', 'Region, tier, currency and your company\'s agreement all change it. The pricing page says so itself.'],
                ['Never checking the estimate', 'An estimate is a guess until the bill arrives. Compare each line with the real bill in the first month.'],
            ],
            asks=[
                ask('You need the tables from 20,000 pages. What does it cost?', ['$30', '$200', '$600'], answer=1,
                    evidence=evidence('code', title='From the Document Intelligence pricing page', text="""Read             $1.50 per 1,000 pages
Prebuilt, Layout $10 per 1,000 pages
Custom           $30 per 1,000 pages"""),
                    clue='Tables need layout, not just the text. Then pages times price divided by 1,000.',
                    why='Layout gives the tables: 20,000 times $10 divided by 1,000 = $200. Read is $30 but gives only the text, and custom is $600, for forms you trained it on.',
                    wrong=['$30 is Read, which gives the text but not the tables.', None, '$600 is a custom model trained on your own forms. Layout already gives tables.']),
                ask('What does it cost in dollars per million tokens?', ['About $0.13', 'About $1.86', 'About $0.07'], answer=0,
                    evidence=evidence('code', title='From the Databricks pricing page', text="""GTE large embeddings:
  1.857 DBU per 1M input tokens
Model serving: $0.07 per DBU"""),
                    clue='DBUs times the dollars for one DBU.',
                    why='1.857 times $0.07 = $0.13 per million tokens. The DBU is the unit Databricks bills by; the price per DBU turns it into dollars.',
                    wrong=[None, '1.857 is DBUs, not dollars. Multiply by the price of one DBU.', '$0.07 is the price of one DBU, not of a million tokens.']),
                ask('What is missing from this?', ['Nothing: the page is the price', 'Our region, tier and agreement', 'The cheapest rival\'s price'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"The pricing page says $0.13 per million tokens, so that is what we will pay."'),
                    clue='Does the page know where you run it and what your company agreed with the vendor?',
                    why='The page shows a list price. Your region, the tier and your company\'s agreement can all change it, and the page says so. Ask whoever buys cloud services for your rate.',
                    wrong=['A list price is a starting point. Region, tier and your agreement change it.', None, 'A rival\'s price doesn\'t change what you will pay for this one.']),
                ask('What do you do with the web search line?', ['Find out why it is 3 times the estimate', 'Keep the estimate: the first bill is odd', 'Drop the line: search is optional'], answer=0,
                    evidence=evidence('code', title='Your worksheet, a month after launch', text="""line          estimate   real bill
web search    $210       $630
embeddings    $0.02      $0.02"""),
                    clue='Three times the estimate: more searches than you thought, or a higher price?',
                    why='The estimate was a guess. 3 times usually means the agent searches more per question than assumed. Check the traces, then fix the estimate or cap the searches.',
                    wrong=[None, 'A first bill 3 times the estimate is the clearest sign the plan is wrong. Find out why.', 'The line is real money. Find out why it is high before you decide anything.']),
            ],
        ),
        starter="""def cost_per_task(lines):
    # your code here
    pass
""",
        solution="""def cost_per_task(lines):
    total = 0
    for line in lines:
        total = total + line["price"] / line["per"] * line["used"]
    return round(total, 4)
""",
        cases=[
            case([{"price": 2, "per": 1000000, "used": 1800},
                  {"price": 10, "per": 1000000, "used": 300},
                  {"price": 14, "per": 1000, "used": 0.5}], expected=0.0136, sample=True),
            case([], expected=0),
            case([{"price": 10, "per": 1000, "used": 12}], expected=0.12),
        ],
        guided="""def cost_per_task(lines):
    # Replace every ___ with real code, then run the tests.
    total = 0
    for line in lines:
        # the price of one unit, times what one task uses
        total = total + ___
    return ___
""",
        fills=['line["price"] / line["per"] * line["used"]', 'round(total, 4)'],
        concepts=[
            [
                'Price per unit',
                'Divide the price by the size of its unit: $14 per 1,000 searches is 14 / 1000, $0.014 a search.',
                '14 / 1000   # 0.014',
            ],
            [
                'Adding up in a loop',
                'Start the total at 0 and add each line to it.',
                """total = 0
for x in [0.0036, 0.003, 0.007]:
    total = total + x   # 0.0136""",
            ],
        ],
        byhand='Input tokens: 2 divided by 1,000,000 times 1,800 = $0.0036. Output: 10 divided by 1,000,000 times 300 = $0.003. Web search: 14 divided by 1,000 times 0.5 = $0.007. Together $0.0136. Return 0.0136.',
        why='Each line is worked out once, so the work grows with the number of lines.',
        gotchas=[
            [
                'Mixing units',
                'Per million tokens and per 1,000 searches need different divisions. Keep the unit size with each price.',
            ],
            [
                'No source or date',
                'A price with no page and no date can\'t be checked or updated. Write both next to it.',
            ],
        ],
    ),
)

lesson(MODULE, 'payback_plan',
    title='Payback and break-even',
    learn=[
        'A task that saves money every time can still lose money overall. Running costs come every month, and the build has to be paid back. Three numbers tell you whether it is worth building.',
        '**Monthly net** is the saving per task times tasks a month, minus the fixed monthly costs (search, logging, monitoring). **Payback** is the build cost divided by the monthly net: how many months until the build has paid for itself. **Break-even** is the fixed monthly costs divided by the saving per task: how many tasks a month you need just to cover the running costs.',
        "Where the numbers come from: **saving per task** is today's cost, minus the cost per finished task, minus what mistakes nobody caught cost later. The owner confirms the staff time saved is real money, a **hard saving**: fewer new hires or less overtime, not just quieter afternoons (a **soft saving**). They also guess tasks a month, and the POC checks that guess.",
        'In the HR example, $8 today minus about $1.87 with AI, minus 50 cents for mistakes nobody caught, saves about $5.64 a ticket. With the 6,000 tickets a month that HR answers by hand today, and $2,300 a month of fixed costs (hosting, evals and monitoring), the $73,000 build pays back in about 2.3 months.',
    ],
    example=example('The HR ticket plan', """saving = 5.635   # a ticket
tasks = 6000     # a month
fixed = 2300     # a month
build = 73000    # once
net = saving * tasks - fixed
# 31510 a month
payback = build / net   # 2.3 months
even = fixed / saving   # 408.2
# round up: 409 tickets a month"""),
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
        "fixed_monthly": 2300,
        "build_cost": 73000,
    })
    mlflow.log_metrics({
        "monthly_net": 31510,
        "payback_months": 2.3,
        "break_even_tasks": 409,
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
- `fixed_monthly`: the running costs each month, like `2300`.
- `build_cost`: what building it costs, paid once, like `73000`.

Return a dict with three keys:

- `"monthly_net"`: saving per task times tasks a month, minus the fixed costs, rounded to 2 decimal places.
- `"payback_months"`: the build cost divided by the monthly net, rounded to 1 decimal place. If the monthly net is 0 or less, use `None`.
- `"break_even_tasks"`: the fixed costs divided by the saving per task, rounded UP to a whole number. So 408.2 becomes 409, and 2000 stays 2000.""",
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
            case(5.635, 6000, 2300, 73000, expected={'monthly_net': 31510.0, 'payback_months': 2.3, 'break_even_tasks': 409}, sample=True),
            case(2, 1000, 3000, 50000, expected={'monthly_net': -1000, 'payback_months': None, 'break_even_tasks': 1500}),
            case(5, 2000, 10000, 60000, expected={'monthly_net': 0, 'payback_months': None, 'break_even_tasks': 2000}),
            case(4, 500, 0, 12000, expected={'monthly_net': 2000, 'payback_months': 6.0, 'break_even_tasks': 0}),
            case(2.535, 6000, 2300, 73000, expected={'monthly_net': 12910.0, 'payback_months': 5.7, 'break_even_tasks': 908}),
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
    # int() drops the decimals: 408.2 becomes 408.
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
                'round(2.3167, 1)   # 2.3',
            ],
        ],
        byhand='Saved a month: 5.635 times 6000 is 33810. Minus 2300 of fixed costs, the monthly net is 31510. That is above 0, so payback is 73000 divided by 31510, about 2.3167, which rounds to 2.3 months. Break-even: 2300 divided by 5.635 is about 408.2. int() gives 408, and 408 tickets save only about 2299, less than 2300, so add 1: 409. Return {"monthly_net": 31510, "payback_months": 2.3, "break_even_tasks": 409}.',
        why='A few sums and one check, whatever the numbers.',
        gotchas=[
            [
                'Counting saved minutes as money',
                'Staff time saved is money only if the business hires less, cuts overtime or moves people to work it would pay for anyway. Otherwise it is a soft saving, and finance will not count it.',
            ],
            [
                'Payback ignores the slow start',
                'People start using it slowly, which is called the **adoption ramp**. If the first 3 months run at half volume, the 2.3 months becomes about 3.9.',
            ],
        ],
    ),
)

lesson(MODULE, 'biggest_swing',
    title='Which guess matters most',
    learn=[
        "Every business case rests on guesses, called **assumptions**: how many tasks, how often the AI is right, how much each one saves. If you don't know which guess matters most, the trial measures the easy things and misses the one that sinks the plan.",
        'A **sensitivity analysis** changes one guess at a time, from a bad value to a good one, and keeps the others at their expected values. The **swing** is how far the answer moves. The guess with the biggest swing is the one to measure hardest.',
        'In the HR example, doubling the token price lowers the monthly value by only about $390. If the AI is right 50 in 100 times instead of 80, the value falls from about $31,300 to $18,700, as the example below works out.',
        'Where the numbers come from: you and the owner agree a bad, expected and good value for each guess (the **worst case**, **base case** and **best case**). Then measure the guesses with the biggest swings first. For example, try the prompt on 50 past tickets labelled by hand to see how often the AI is right: that share is the `success` guess in the example and the exercise.',
    ],
    example=example('One guess, low and high', """# value = tasks * success * saving - fixed
# tasks 6000, saving 7, fixed 2300
# success: how often the AI is right
low = 6000 * 0.5 * 7 - 2300     # 18700
high = 6000 * 0.95 * 7 - 2300   # 37600
swing = high - low              # 18900
# Do the same for each other guess,
# and compare the swings."""),
    check=question(
        "In the HR plan, doubling the token price moves the monthly value by about $390. Moving how often the AI is right from 50 in 100 to 95 in 100 moves it by $18,900. What should the POC measure hardest?",
        [
            'The token price, because it is on the monthly bill',
            'The fixed monthly costs, because they come every month',
            'How often the AI is right, on labelled past tickets',
        ],
        answer=2,
        why='The guess with the biggest swing decides whether the plan pays. How often the AI is right swings the value far more than the token price, so pin it down first.',
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

- `base`: your expected value for each guess, like `{"tasks": 6000, "success": 0.8, "saving": 7, "fixed": 2300}`.
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
            case({'tasks': 6000, 'success': 0.8, 'saving': 7, 'fixed': 2300}, {'tasks': [4000, 7000], 'success': [0.5, 0.95], 'fixed': [1500, 5000]}, expected='success', sample=True),
            case({'tasks': 6000, 'success': 0.8, 'saving': 7, 'fixed': 2300}, {'fixed': [1000, 8000]}, expected='fixed'),
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
        byhand='In alphabetical order. fixed: at 1500 the value is 6000 times 0.8 times 7, minus 1500: 32100. At 5000 it is 28600. The gap is 3500. success: at 0.5 the value is 18700, and at 0.95 it is 37600. The swing is 18900. tasks: at 4000 the value is 20100, and at 7000 it is 36900. The swing is 16800. The biggest swing is 18900, so return "success".',
        why='One walk through the guesses in ranges, working out the value twice for each.',
        gotchas=[
            [
                'Changing two guesses at once',
                "Then you can't tell which one moved the answer. Change one, and keep the rest at their expected values.",
            ],
            [
                'Measuring what is easy',
                'Token counts are easy to measure, but how often the AI is right usually moves the answer far more.',
            ],
        ],
    ),
)

lesson(MODULE, 'peak_capacity',
    title='Size for the busiest minute',
    checked='2026-10-15',
    sources=[
        source('Manage Azure OpenAI in Microsoft Foundry Models quota', 'https://learn.microsoft.com/azure/foundry/openai/how-to/quota'),
        source('Databricks Unity Gateway usage tracking', 'https://docs.databricks.com/aws/en/ai-gateway/usage-tracking'),
    ],
    learn=[
        'Traffic, the requests arriving at your system, is never spread evenly through the day. To **size** a system is to decide how many tokens a minute it must handle, and doing that ahead of time is called **capacity planning**. Every model has a limit on tokens a minute. If you size from the daily average, the busiest minute goes over that limit, and users get error 429, "too many requests". So size for the **busiest minute**.',
        'To find it, start with tasks a day. Multiply by the share of them that arrive in the busiest hour, and divide by 60 to get tasks a minute in that hour. Then multiply by a **burst factor**: how much busier the busiest minute is than an average minute of that hour. 3 is a fair first guess.',
        'Multiply by the tokens one task asks for, and you have the tokens in the busiest minute. Count what a task asks for, not what it uses: the prompt plus the longest answer you allow, because that is what the limit counts.',
        "Now check that number against the first limit on the path: the model's own. At work the model runs on **Azure AI Foundry**, Microsoft's service that hosts models. Your app talks to a **deployment**: one copy of a model, set up for you. Each deployment has a **quota**, the most it may use, counted in **tokens per minute** (TPM).",
        "Then check the second limit. Requests reach the model through a **gateway**, a front door that every request passes through. The gateway has its own **rate limits** on how much it lets through each minute, and either limit can send back error 429.",
        'Where the numbers come from: the owner gives tasks a day. The POC measures the busiest hour, the burst from 1-minute peaks, and the tokens per task. The platform team gives the deployment quota and the gateway limits.',
    ],
    example=example('Average against busiest minute', """tokens = 25000   # per HR ticket
# spread over an 8-hour day:
avg = 270 / (8 * 60) * tokens
# about 14000 tokens a minute
# busiest hour has a fifth, burst 3:
peak = 270 * 0.2 / 60 * 3 * tokens
# 67500 a minute: almost 5 times
# plan for 1 ticket a minute, not 0.9:
# 1 * 3 * 25000 = 75000, so ask for
# a limit above that"""),
    check=question(
        'Your bot\'s daily average is far below its tokens-per-minute limit, yet users get "too many requests" errors every morning. What went wrong?',
        [
            'It was sized from the daily average, not the busiest minute',
            'The gateway counts only output tokens against the limit',
            'Tokens cost more in the morning, so the limit shrinks',
        ],
        answer=0,
        why='Requests bunch up at busy times. Azure adds the tokens each request asks for to a running count that starts again every minute, so the busiest minute, not the daily average, decides whether you fit. It also counts requests over windows of 1 to 10 seconds, so a burst can be refused even when the minute\'s total would fit.',
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
        realworld='Azure adds the tokens each request asks for to a count that resets every minute, and counts requests over windows of 1 to 10 seconds, so a burst hits a limit long before the hourly totals look busy. Capacity is always sized for the peak, never the average.',
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

AZURE_FOUNDRY_PRICING = source('Azure OpenAI pricing (East US list prices, via the Azure Retail Prices API)', 'https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/')

lesson(MODULE, 'deployment_types',
    title='Deployment types and regions',
    checked='2026-10-18',
    sources=[
        source('Deployment types for Microsoft Foundry Models', 'https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types'),
        AZURE_FOUNDRY_PRICING,
        source('Manage Azure OpenAI in Microsoft Foundry Models quota', 'https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/quota'),
    ],
    cards=[
        card('Where may the model process your data?',
             'In Azure AI Foundry you pick a **deployment type** for each model. It decides where your requests may be processed, and it changes the price.',
             picture=sortby('Where can it process your data?',
                            sortrow('Global', 'In any Azure region', 'Cheapest', icon='cloud'),
                            sortrow('Data Zone', 'Only inside one zone: US, EU or Asia Pacific', 'About 10% more', icon='lock'),
                            sortrow('Regional (Standard)', 'Only inside the geography you choose', 'About 10% more', icon='lock')),
             after='Stored data stays in your chosen geography whichever you pick. Your company\'s data rules, often set by the privacy team, decide which types you may use.'),
        card('Same model, different price',
             'gpt-4.1 in East US, per million tokens:',
             picture=piles(pile('Global Standard', [('coin', '$2.00 a million in'), ('coin', '$8.00 a million out')]),
                           pile('Data Zone or Regional', [('coin', '$2.20 a million in'), ('coin', '$8.80 a million out')])),
             after='Work that can wait gets half price as Batch: Global Batch is $1.00 in and $4.00 out. Embedding models follow the same pattern: $0.02 Global, $0.022 Data Zone or Regional.'),
        card('Quota is per region, model and type',
             '**Quota**, the tokens per minute you may use, is given to your subscription per region, per model and per deployment type. Quota in one region doesn\'t carry over to another.',
             picture=sortby('240,000 tokens a minute of gpt-4o in East US',
                            sortrow('One deployment', 'All of it in one place', '240,000', icon='layers'),
                            sortrow('Two deployments', 'Split between two apps', '120,000 each', icon='layers')),
             after='New models usually arrive in Global first, with the most quota. A Data Zone or Regional version can come later.'),
        card('Pick in this order',
             'The price comes last, not first.',
             picture=steps(('lock', 'Your data rules', 'Which deployment types you may use at all.'),
                           ('cloud', 'The model and the region', 'Is the model offered there, with enough quota?'),
                           ('coin', 'Then the price', 'The cheapest type that passes both.'))),
    ],
    example=example('Which deployment for HR data that must stay in the EU?', """# per million input tokens
# Global          $2.00  any region
# Data Zone EU    $2.20  EU only
# Regional        $2.20  one geography
# rule: EU only, so Global is out
# cheapest left: Data Zone EU, $2.20"""),
    check=question(
        'Your HR data must stay in the EU. Which deployment type can you use?',
        [
            'Data Zone EU, or Regional in the EU',
            'Global, because it is the cheapest',
            'Any type: stored data stays put',
        ],
        answer=0,
        why='Global may process requests in any region, so it breaks the rule. Data Zone EU or a Regional deployment in an EU geography keeps processing in the EU, for about 10% more.',
    ),
    angle=angle(
        pattern='Filter by the rules, then take the cheapest',
        text='The big idea: the data rules decide which deployment types you may use, and only then does the price decide. Your code goes through the options. It skips any whose data location isn\'t in the allowed list, and among the rest keeps the one with the lowest price so far. It returns that option\'s name, or None if nothing is allowed. It is like picking a flight: first the ones that land where you need to be, then the cheapest of those.',
        say='"I let the data rules pick the deployment [[type|size|name::Global, Data Zone or Regional.]] first, then check the model and quota are in that [[region|budget|team::Where it runs.]], and only then choose the [[cheapest|fastest|newest::Among the ones still allowed.]]."',
        classic=None,
    ),
    exercise=exercise(
        title='Pick the Deployment',
        topic='pricing',
        difficulty='easy',
        fn='pick_deployment',
        prompt="""Your function gets two things:

- `options`: a list of dicts, each with `"name"`, `"data_in"` (where it may process data, like `"any region"` or `"EU"`) and `"price"` (dollars per million input tokens).
- `allowed`: a list of the `"data_in"` values your data rules allow.

Return the name of the cheapest option whose `"data_in"` is in `allowed`. On a tie, keep the first one. If none is allowed, return `None`.""",
        pattern='Skip what the rules forbid, then keep the cheapest so far.',
        target='one pass over the options',
        realworld='At work the privacy team\'s data rules come first: a Global deployment can be cheaper and still not allowed. Teams filter by the rules, then compare prices.',
        starter="""def pick_deployment(options, allowed):
    # your code here
    pass
""",
        solution="""def pick_deployment(options, allowed):
    best = None
    for option in options:
        if option["data_in"] in allowed:
            if best is None or option["price"] < best["price"]:
                best = option
    if best is None:
        return None
    return best["name"]
""",
        cases=[
            case([{"name": "Global", "data_in": "any region", "price": 2.0},
                  {"name": "Data Zone EU", "data_in": "EU", "price": 2.2},
                  {"name": "Regional Sweden Central", "data_in": "Sweden", "price": 2.2}],
                 ["EU", "Sweden"], expected="Data Zone EU", sample=True),
            case([{"name": "Global", "data_in": "any region", "price": 2.0},
                  {"name": "Data Zone EU", "data_in": "EU", "price": 2.2}],
                 ["any region", "EU"], expected="Global"),
            case([{"name": "Global", "data_in": "any region", "price": 2.0}], ["US"], expected=None),
            case([], ["EU"], expected=None),
        ],
        guided="""def pick_deployment(options, allowed):
    # Replace every ___ with real code, then run the tests.
    best = None
    for option in options:
        # Step 1: skip what the data rules don't allow.
        if ___:
            # Step 2: keep the cheapest so far.
            if best is None or ___:
                best = option
    if best is None:
        return None
    return best["name"]
""",
        fills=['option["data_in"] in allowed', 'option["price"] < best["price"]'],
        concepts=[
            [
                'in for a list',
                '`"EU" in ["EU", "US"]` is True when the value is one of the list\'s items.',
                '"EU" in ["EU", "US"]   # True',
            ],
            [
                'None until you find one',
                'Start with `best = None`. The first allowed option replaces it, and later ones only if they are cheaper.',
                """best = None
if best is None or 2.2 < best["price"]:
    best = {"price": 2.2}""",
            ],
        ],
        byhand='Global processes data in any region, which the rules don\'t allow: skip it. Data Zone EU is allowed: best so far, $2.20. Regional Sweden Central is allowed, but $2.20 is not less than $2.20, so the first stays. Return "Data Zone EU".',
        why='Each option is looked at once, so the work grows with the number of options.',
        gotchas=[
            [
                'Cheapest first, rules after',
                'Global is usually cheapest, and often not allowed. Filter by the data rules before you compare prices.',
            ],
            [
                'Forgetting quota',
                'An allowed type is no use if the model isn\'t offered there or the quota is too small. Check both before you plan on it.',
            ],
        ],
    ),
)

lesson(MODULE, 'ptu_or_paygo',
    title='Pay-per-token or provisioned throughput?',
    checked='2026-10-18',
    sources=[
        source('Provisioned throughput for Foundry Models', 'https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/provisioned-throughput'),
        source('Provisioned throughput billing', 'https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/provisioned-throughput-billing'),
        source('Provisioned throughput sizing', 'https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/provisioned-throughput-sizing'),
        AZURE_FOUNDRY_PRICING,
        source('Databricks reserved provisioned throughput', 'https://learn.microsoft.com/en-us/azure/databricks/machine-learning/foundation-model-apis/reserved-provisioned-throughput'),
    ],
    cards=[
        card('Two ways to pay for a model',
             'A **PTU** (provisioned throughput unit) is a unit of model capacity kept just for you.',
             picture=piles(pile('Pay per token (Standard)', [('coin', 'You pay for each token used'), ('alert', 'A busy minute can hit error 429')]),
                           pile('Provisioned throughput (PTU)', [('clock', 'You pay every hour, used or not'), ('check', 'The capacity is kept for you')])),
             after='Databricks sells provisioned throughput too: endpoints billed by the hour in model units, with reserved terms of 1 or 3 months billed in full.'),
        card('What a PTU costs',
             'Prices per PTU in East US. Billing runs until the deployment is deleted: it can\'t be paused.',
             picture=sortby('Price of one PTU',
                            sortrow('Global', '$1.00 an hour, or $260 a month reserved', 'From $260', icon='cloud'),
                            sortrow('Data Zone', '$1.10 an hour, or $286 a month reserved', 'From $286', icon='lock'),
                            sortrow('Regional', '$2.00 an hour, or $286 a month reserved', 'From $286', icon='lock')),
             after='A deployment has a minimum: for gpt-4.1, 15 PTUs on Global or Data Zone, then steps of 5; 50 on Regional, then steps of 50.'),
        card('How many PTUs: the sum',
             'Size from the busiest minute. Output tokens count as several input tokens: for gpt-4.1, one output token counts as 4.',
             picture=steps(('chart', 'Tokens in the busiest minute', '30,000 input and 3,000 output tokens a minute.'),
                           ('listcheck', 'Count output as 4 input', '30,000 plus 3,000 times 4 = 42,000.'),
                           ('layers', 'Divide by what a PTU handles', 'gpt-4.1 handles 3,000 a minute per PTU: 42,000 divided by 3,000 = 14.'),
                           ('reset', 'Round up to the minimum and steps', '14 is under the minimum, so 15 PTUs.'))),
        card('It buys capacity, not savings',
             'The same app, busy at that rate all month, priced three ways:',
             picture=sortby('15 PTUs against pay per token, for one month',
                            sortrow('Pay per token', '$2,628 in plus $1,051 out', 'About $3,679', icon='coin'),
                            sortrow('PTU by the hour', '15 times $1 times 730 hours', '$10,950', icon='clock'),
                            sortrow('PTU reserved monthly', '15 times $260', '$3,900', icon='clock')),
             after='Even busy all month, PTUs cost about the same or more. You buy them for capacity that is always there and steady speed. Turn on **spillover**: when the PTU deployment is full, extra requests go to a pay-per-token deployment instead of failing.'),
    ],
    example=example('Sizing gpt-4.1 PTUs for the busiest minute', """normalized = 30000 + 3000 * 4  # 42,000
ptus = 42000 / 3000              # 14
# minimum is 15 (Global): buy 15
# by the hour: 15 * 1.00 * 730 = $10,950
# reserved:    15 * 260        = $3,900
# pay per token, same load:  about $3,679"""),
    check=question(
        'Your app needs 42,000 tokens a minute at its busiest, a PTU handles 3,000, and the minimum is 15 PTUs. How many do you buy?',
        ['15', '14', '42'],
        answer=0,
        why='42,000 divided by 3,000 is 14, but a deployment can\'t go under its minimum of 15, so you buy 15.',
    ),
    angle=angle(
        pattern='Normalize, divide, then round up to the minimum and steps',
        text='The big idea: you size PTUs from the busiest minute, counting each output token as several input tokens, and round up to the deployment\'s minimum and its steps, because capacity is bought in whole blocks. Your code works out the normalized tokens: input plus output times the weight. It divides by what one PTU handles and rounds up to a whole number. If that is below the minimum, it uses the minimum. Otherwise it rounds up to the next step above the minimum. It returns the normalized tokens and the PTUs. It is like buying eggs by the box: you can\'t buy 14, and the smallest box is 15.',
        say='"I size PTUs from the [[busiest|average|first::Size for the peak, not the day.]] minute, with output counted as several input tokens, and round [[up|down|off::Half a step can\'t be bought.]]. PTUs buy guaranteed [[capacity|savings|quality::Kept for you every hour, used or not.]], not a smaller bill."',
        classic=None,
    ),
    exercise=exercise(
        title='Size the PTUs',
        topic='pricing',
        difficulty='medium',
        fn='ptus_needed',
        prompt="""Your function gets `need`, a dict:

- `"input_tpm"` and `"output_tpm"`: input and output tokens in the busiest minute.
- `"output_weight"`: how many input tokens one output token counts as, like `4`.
- `"tpm_per_ptu"`: input tokens a minute one PTU handles.
- `"minimum"` and `"step"`: the fewest PTUs a deployment can have, and the size of each step above that.

1. Normalized tokens = input_tpm + output_tpm times output_weight.
2. PTUs = normalized tokens divided by tpm_per_ptu, rounded **up** to a whole number.
3. If that is below the minimum, use the minimum. Otherwise round it up to the minimum plus a whole number of steps.

Return `[normalized, ptus]`.""",
        pattern='Work out the need, then round up to what can be bought.',
        target='a few sums',
        realworld='Platform teams size provisioned throughput from traces of the busiest minute, then round up to the deployment\'s minimum and steps. The rounding is often why a small app costs more on PTUs than on pay-per-token.',
        starter="""def ptus_needed(need):
    # your code here
    pass
""",
        solution="""def ptus_needed(need):
    normalized = need["input_tpm"] + need["output_tpm"] * need["output_weight"]
    ptus = int(normalized // need["tpm_per_ptu"])
    if normalized > ptus * need["tpm_per_ptu"]:
        ptus = ptus + 1
    if ptus <= need["minimum"]:
        return [normalized, need["minimum"]]
    extra = ptus - need["minimum"]
    steps = extra // need["step"]
    if extra > steps * need["step"]:
        steps = steps + 1
    return [normalized, need["minimum"] + steps * need["step"]]
""",
        cases=[
            case({"input_tpm": 30000, "output_tpm": 3000, "output_weight": 4, "tpm_per_ptu": 3000, "minimum": 15, "step": 5},
                 expected=[42000, 15], sample=True),
            case({"input_tpm": 60000, "output_tpm": 6000, "output_weight": 4, "tpm_per_ptu": 3000, "minimum": 15, "step": 5},
                 expected=[84000, 30]),
            case({"input_tpm": 60000, "output_tpm": 6000, "output_weight": 4, "tpm_per_ptu": 3000, "minimum": 50, "step": 50},
                 expected=[84000, 50]),
            case({"input_tpm": 200000, "output_tpm": 20000, "output_weight": 4, "tpm_per_ptu": 3000, "minimum": 50, "step": 50},
                 expected=[280000, 100]),
        ],
        guided="""def ptus_needed(need):
    # Replace every ___ with real code, then run the tests.
    # Step 1: output counts as several input tokens.
    normalized = ___
    # Step 2: PTUs, rounded up to a whole number.
    ptus = int(normalized // need["tpm_per_ptu"])
    if normalized > ptus * need["tpm_per_ptu"]:
        ptus = ptus + 1
    # Step 3: never below the minimum.
    if ptus <= need["minimum"]:
        return [normalized, need["minimum"]]
    # Step 4: round up to whole steps above the minimum.
    extra = ptus - need["minimum"]
    steps = extra // need["step"]
    if ___:
        steps = steps + 1
    return [normalized, need["minimum"] + steps * need["step"]]
""",
        fills=['need["input_tpm"] + need["output_tpm"] * need["output_weight"]', 'extra > steps * need["step"]'],
        concepts=[
            [
                'Rounding up by hand',
                'Divide with `//` to keep the whole part, then add one if anything was left over.',
                """n = 84000 // 3000      # 28
if 84000 > n * 3000:
    n = n + 1           # not needed: exact""",
            ],
            [
                'Minimum plus steps',
                'Above the minimum, capacity comes in steps. 28 PTUs with a minimum of 15 and steps of 5: 13 extra, which is 3 steps, so 15 plus 15 = 30.',
                """extra = 28 - 15        # 13
steps = 13 // 5        # 2, with 3 left over
steps = steps + 1      # 3
15 + steps * 5         # 30""",
            ],
        ],
        byhand='Normalized: 30,000 plus 3,000 times 4 = 42,000. 42,000 divided by 3,000 is exactly 14. 14 is below the minimum of 15, so buy 15. Return [42000, 15].',
        why='A few sums, whatever the size of the app.',
        gotchas=[
            [
                'Sizing from the daily average',
                'Size from the busiest minute, or the PTUs fill up at the worst time. Spillover catches the overflow, at pay-per-token prices.',
            ],
            [
                'Forgetting output counts more',
                'Each output token counts as several input tokens (4 for gpt-4.1). Leave that out and you buy too few PTUs.',
            ],
        ],
    ),
)

lesson(MODULE, 'make_a_skill',
    title='Turn your vetting into a skill',
    checked='2026-10-15',
    sources=[
        source('Agent Skills specification', 'https://agentskills.io/specification'),
        source('Claude Code: Skills', 'https://code.claude.com/docs/en/skills'),
    ],
    learn=[
        "Everything in Frame so far, from the one-line use case and the gates to the review, the cost and the acceptance criteria, is a routine you will repeat for every new idea. A **Claude skill** packages a routine so Claude follows it the same way every time: a folder holding a **SKILL.md** file of instructions, plus any reference files and scripts it needs.",
        "SKILL.md starts with **YAML frontmatter**: a few settings between `---` markers, two of them required. The **name** is lowercase letters, numbers and hyphens, at most 64 characters, and may not contain \"claude\" or \"anthropic\". The **description**, up to 1,024 characters, says what the skill does and when to use it, in the third person (\"Vets a proposed AI use case. Use when...\"). Claude reads only the name and description of every skill up front, and loads the rest when a request matches: so the description decides whether your skill is ever used.",
        "The body holds the steps and an output format, kept short (Anthropic suggests under 500 lines), with details in reference files it opens only when needed. Anything that must be exact, like adding up the total cost of ownership, goes in a **script** the skill runs, because a model can get sums wrong and a script cannot. This repository comes with one: `.claude/skills/vet-ai-use-case`, whose `scripts/tco.py` prints the cost table.",
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
...
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
        topic='use cases',
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
        practice=practice(
            intro='Review these SKILL.md drafts the way a reviewer does before they\'re shared: will it load, and will Claude ever use it?',
            explain='The big idea: a skill is a SKILL.md file whose name and description Claude reads first, so the file must follow the rules exactly or it will not load. You caught a name with capitals, listed every broken rule at once instead of stopping at the first, picked the description that says when to use the skill, and kept the body short with the details in reference files.',
            pattern='Will it load, and will it get used?',
            realworld="When a teammate shares a skill with the team, you'll review its SKILL.md first. Check the name and description against the rules, send back every problem at once, and ask for a description that says when to use it.",
            asks=[
                ask('Will this skill load?', ['Yes: both lines are filled in', 'No: the name breaks the rules', 'No: the description is too long'], answer=1,
                    evidence=evidence('code', title='SKILL.md, first draft', text="""---
name: Vet_AI
description: Vets a proposed AI use case. Use when someone asks whether an AI idea is worth doing.
---"""),
                    clue='Names may use only lowercase letters, numbers and hyphens.',
                    why='Capitals and the underscore aren\'t allowed in a name. `vet-ai` would load.',
                    wrong=['Filled in isn\'t enough: each line has rules.', None, 'It is well under 1,024 characters.']),
                ask('What do you send back?', ['Only the name: "claude" is a reserved word', 'Only the description: it is empty', 'Both: the reserved word and the empty description'], answer=2,
                    evidence=evidence('code', title='SKILL.md, a teammate\'s draft', text="""---
name: claude-helper
description:
---"""),
                    clue='Check every rule, not just the first one that fails.',
                    why='"claude" may not appear in a name, and a description needs 1 to 1,024 characters. Listing both lets the author fix them in one go.',
                    wrong=['The description is empty too.', 'The name uses a reserved word too.', None]),
                ask('All three of these load. Which description gets the skill used when someone asks about an AI idea?', ['A helpful assistant for all kinds of AI work: ideas, questions, projects and plans.', 'Vets a proposed AI use case. Use when someone asks whether an AI idea is worth doing.', 'I can help you work out whether your AI ideas are any good.'], answer=1,
                    alone=True,
                    clue='Claude reads only the name and description up front. Which one says when to use it?',
                    why='Claude chooses a skill from its description alone, so it must say what the skill does and when to use it, in the third person.',
                    wrong=['Long, but vague: it never says what the skill does or when to use it, so Claude never will.', None, 'It is in the first person and never says when to use it. Write descriptions in the third person.']),
                ask('What do you suggest?', ['Keep it: Claude does better with every detail in front of it', 'Keep SKILL.md short; put the details in reference files', 'Move the tables into the description, which Claude reads first'], answer=1,
                    evidence=evidence('claim', who='A teammate said', text='"I put all the pricing tables and every worked example straight into SKILL.md. It\'s 900 lines now, so Claude sees everything."'),
                    clue='Anthropic suggests keeping the body under 500 lines.',
                    why='The body holds the steps and the output format. Details go in reference files Claude opens only when it needs them, and prices change, so the skill asks for them instead of storing them.',
                    wrong=['The whole body is read every time the skill is used. Keep it short.', None, 'The description says when to use the skill, and it stops at 1,024 characters.']),
            ],
        ),
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
