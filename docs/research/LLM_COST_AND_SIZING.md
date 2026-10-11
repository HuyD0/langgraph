# Pricing, sizing and judging the payoff of an LLM workload

Researched on 2026-10-11 by four researchers (business case, sizing, price levers, total cost) using primary sources only: vendor docs, price lists, standards groups and papers. A fact-checker per area re-opened every source, and a critic checked the draft (section 6). Claims the critic questioned were cut, or re-checked against their source on 2026-10-11.

> **Who this is for.** Learners who are new to coding, and the chat tutor that answers their
> questions from this file. Maths is in words and a few one-line Python sums. Prices are
> examples from one day: check them again. Lesson ideas mentioned here
> (such as "cost per finished task" or "payback and break-even") are plans, not lessons that
> exist. For what exists, see [../tutor/CURRICULUM_MAP.md](../tutor/CURRICULUM_MAP.md).

## 1. The short answer

Before you build, work out what one finished task costs today and what it would cost with AI, counting the people who still check answers and fix mistakes. The token bill is usually the smallest part. How often the AI is right, how much checking it needs and how many people use it decide whether it pays.

The method, in order. "Who" says where each number comes from.

1. **Frame the task, check you need an LLM, check the data.** One sentence, one measurable goal. If the steps follow fixed rules, Microsoft says use regular code; for answers from a fixed set of documents, use plain RAG (look up the relevant documents and give them to the model with the question), not an agent <https://learn.microsoft.com/azure/cloud-adoption-framework/ai-agents/business-strategy-plan>. Data check: does the AI have the records it needs, current and allowed for this use, plus past cases with known right answers to test on? *Who: the business owner, with you.*
2. **Write today's cost per task.** Tasks a month, minutes each, error rate, and the "fully loaded" hourly rate (pay plus the employer's extra costs; Microsoft suggests pay times 1.3 to 1.5, or $72 if unknown). Cost today is minutes divided by 60, times the hourly rate. Microsoft asks for 90 days of system data captured before launch, not before you start <https://learn.microsoft.com/microsoft-copilot-studio/guidance/agent-business-value-define-value>. For a new process, estimate and refine; timing a sample of the work is one way (our suggestion). *Who: the business owner, from system records.*
3. **Estimate tasks through the AI, and whether the saving is real money.** Tasks a month, times the share the AI can handle, times the share of people who use it. Saved minutes are money only if the business avoids hiring, cuts overtime or contractors, or moves people to work it would otherwise pay for. Microsoft calls value built only on theoretical time saved the time-savings trap <https://learn.microsoft.com/microsoft-copilot-studio/guidance/agent-business-value-measure-impact>. A measured check: across 5,172 support agents, AI help raised issues resolved per hour by 15 percent <https://arxiv.org/abs/2304.11771>. *Who: the business owner guesses; the POC (proof of concept) measures.*
4. **Count tokens for one task, and price them.** A token is a piece of a word. Add everything sent on every model call in one run: system prompt, tool definitions, retrieved text, chat history (it grows each turn), the question. Output is the answer plus any hidden reasoning, billed as output <https://developers.openai.com/api/docs/guides/reasoning>. Give low, typical and high numbers. Model cost is tokens times the price per million, divided by a million. Keep prices in one dated table. *Who: the price list; the POC measures tokens.*
5. **Cost per finished task.** Model cost, plus checking (share checked, times minutes, at the hourly rate), plus redo (share wrong and caught, times today's cost per task), plus errors that slip through (share wrong and not caught, times the cost of one error). This follows GDPval <https://arxiv.org/abs/2510.04374> and Microsoft's pricing of errors (link in step 3). To measure what slips through, review a random sample of the answers nobody checked (our suggestion). *Who: the POC measures right answers and catches; the business owner gives check time and error cost.*
6. **Add fixed monthly costs, the build and a buffer.** Monthly: search index, logging, LLM judges (a model that grades answers), monitoring, and people's time for upkeep (keeping evals, your test questions and checks, current; fixes). Build, paid once: engineering, the eval set, data preparation, a security review. Azure's cost-model guidance asks for a budget with room for surprises <https://learn.microsoft.com/azure/well-architected/cost-optimization/cost-model>. *Who: the price list; engineers estimate the build.*
7. **Work out the results.** *Who: you.*
   - Staff time freed per task: cost today minus checking minus redo.
   - Real saving per task: staff time freed, times the share of freed time that is real money (step 3), minus model cost, minus the cost of errors that slip through. The share shrinks only the freed staff time; model cost and error cost are paid either way. When the share is 1, this equals cost today minus AI cost per task.
   - Monthly net: tasks through the AI, times real saving per task, minus fixed monthly costs.
   - Payback in months: build cost divided by monthly net.
   - Break-even: fixed monthly costs divided by real saving per task (tasks a month needed to cover running costs).
   - First-year ROI (return on investment), the FinOps Foundation formula <https://www.finops.org/wg/finops-for-ai-overview/> over a fixed window: benefit minus cost, divided by cost. Benefit is 12 months of real saving on tasks; cost is the build plus 12 months of fixed costs.
8. **Change one guess at a time.** Bad, expected and good value for each guess. The one that moves the answer most is the one to measure hardest. *Who: you.*
9. **Check capacity and speed for the busiest minute,** with a burst allowance, against the limits on your path. Start on pay-as-you-go; reserve only once traffic is steady. *Who: the POC measures traffic; the platform team gives quota and gateway limits.*
10. **Pilot with go/no-go gates, then set controls.** Swap every guess for a measured number. Microsoft says use the baseline as decision gates and pause if a pilot misses them (step 1 link), and write a switch-off rule at build time: an adoption floor, a satisfaction floor, a cost ceiling or a regulatory trigger (step 2 link). Then add tags, budgets, rate limits and loop caps (section 4). *Who: measured by the POC.*

## 2. A worked example

Made-up numbers for an internal HR help desk. This is the only example in the file.

> **Example prices, checked 2026-10-11:** GPT-6 Sol, Global Standard (an Azure deployment
> type; deployment types set where your requests are processed), East US 2, $2 per
> million input tokens and $10 per million output, from the Azure Retail Prices API
> <https://prices.azure.com/api/retail/prices> (Azure's public pricing page showed blanks that
> day). Microsoft's PTU sizing page uses the same $2 input price. Your contract may differ.

**Today.** 10,000 tickets a month, 8 minutes each, at $60 an hour. 8 divided by 60, times $60, is **$8 a ticket**.

**Model cost.** 5 model calls a ticket, each sending 4,000 tokens and getting 500 back. Input costs 0.8 cents and output 0.5 cents, so 1.3 cents a call, and **6.5 cents a ticket**.

**Cost per finished ticket.** Think about 100 tickets.
- Model: 100 times 6.5 cents is $6.50.
- Checking: 30 are checked for 2 minutes each. 60 minutes is $60.
- Redo: 80 answers are right, 20 wrong. 15 wrong ones are caught (by the check, or the employee comes back) and redone by a person at $8: $120.
- Slip through: the other 5 wrong answers are used as if right. Each costs $10 to sort out later: $50. We treat this $10 as money spent either way.
- Total $236.50, so **$2.365 a ticket**. The model is under 3 percent of it.

**Real saving a ticket.** Staff time freed is $8 minus 60 cents of checking minus $1.20 of redo: $6.20. The business owner confirms the freed time replaces planned hiring, so the real-money share is 1 (all of it). $6.20 times 1, minus 6.5 cents of model cost, minus 50 cents of errors, is a **real saving of $5.635 a ticket**.

**Monthly net.** The AI handles 75 percent of ticket types and 80 percent of staff use it: 10,000 times 0.75 times 0.8 is **6,000 tickets a month**, saving 6,000 times $5.635, or $33,810. Minus a guessed $10,000 a month of fixed costs, **monthly net is $23,810**.

```python
tickets = 10_000        # tickets a month
fixed = 10_000          # fixed costs, dollars a month
share_money = 1.0       # share of freed staff time that is real money
model = 0.065           # dollars a ticket
check = 0.30*2/60*60    # 30 percent checked, 2 minutes, $60 an hour: 0.60
redo = 0.15*8           # 15 percent redone at $8: 1.20
slip = 0.05*10          # 5 percent slip through at $10: 0.50
cost_per_ticket = model + check + redo + slip                  # 2.365
real_saving = (8 - check - redo) * share_money - model - slip  # 5.635
monthly_net = tickets*0.75*0.80 * real_saving - fixed          # 23,810
```

**Payback, break-even, ROI.** Build is a guess of $150,000. Payback is the $150,000 build divided by the $23,810 monthly net: about **6.3 months**. Break-even is the $10,000 of fixed costs a month divided by the $5.635 real saving a ticket: about **1,775 tickets a month**. First-year ROI: benefit is 12 times $33,810, so $405,720; cost is $150,000 plus 12 times $10,000, so $270,000; ($405,720 minus $270,000) divided by $270,000 is about **50 percent**. **Payback ignores ramp-up:** if the first 3 months run at half volume, payback becomes about 8.4 months and ROI about 31 percent.

**Sensitivity: change one guess at a time.**

| Guess | Base | Changed to | Monthly net | Payback |
|---|---|---|---|---|
| (base case) | | | $23,810 | 6.3 months |
| Model cost a ticket (token price doubled) | 6.5 cents | 13 cents | $23,420 | 6.4 months |
| Share checked | 30 percent | 60 percent | $20,210 | 7.4 months |
| Right answers | 80 of 100 | 60 (30 caught, 10 slip) | $13,610 | 11 months |
| Staff who use it | 80 percent | 50 percent | $11,131 | 13.5 months |
| Freed time that is money | all | half | $5,210 | 28.8 months |

In the last row, only the $6.20 of freed staff time is halved: $3.10, minus 6.5 cents of model cost and 50 cents of errors, is a real saving of $2.535 a ticket. Break-even then rises to about 3,945 tickets a month.

Doubling the token price costs $390 a month; right answers, use, and real-money share matter far more. Before a pilot, label 50 past tickets by hand and try the prompt on them to guess the right-answer rate (our suggestion).

**Capacity check.**
- 6,000 tickets over 22 working days is about 270 a day. If the busiest hour carries a fifth (a guess), that is about 55, or 1 a minute.
- The busiest minute is burstier than the busiest hour divided by 60, and Azure checks requests in 1- or 10-second slices <https://learn.microsoft.com/azure/foundry/openai/how-to/quota>. Use a burst factor (a guess of 3, later measured from 1-minute peaks): 3 tickets, 15 calls, 60,000 tokens in and 7,500 out in the busiest minute.
- **Foundry deployment limit.** Each deployment gets a tokens-per-minute (TPM) share of quota, and the arrival check counts prompt plus max_tokens (the longest answer you allow), not tokens used (same link). With max_tokens at 1,000: 15 times 5,000 is 75,000 TPM. Allocate more than that.
- **Reasoning-model exception.** Reasoning models (models that think before they answer) reject max_tokens: the setting is called max_completion_tokens in the Chat Completions API and max_output_tokens in the Responses API <https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning>. That limit must also cover hidden reasoning; OpenAI suggests at least 25,000 at first, or answers can come back empty while you pay (step 4 link). Our estimate, assuming the arrival check counts this setting the same way: 15 times 29,000 (4,000 prompt plus 25,000) is 435,000 TPM.
- **Gateway limit.** Unity Gateway rate limits can be set per service, user or group, in requests or tokens per minute; going over returns error 429, "too many requests" <https://learn.microsoft.com/azure/databricks/ai-gateway/rate-limits>. An eval run firing hundreds of questions can hit a low test limit; requests arriving together aren't checked first, so a burst gets through and later ones are blocked briefly.
- Databricks' pay-per-token tiers <https://learn.microsoft.com/azure/databricks/machine-learning/foundation-model-apis/limits> cover models Databricks serves itself, so they are not the check for a Foundry deployment.
- **Speed.** Five calls in a row, each writing 500 tokens at about 80 a second (Microsoft's target for GPT-6 Sol on provisioned capacity), take over 30 seconds: fine for a ticket, too slow for chat. Output length drives total time <https://learn.microsoft.com/azure/foundry/openai/how-to/latency>.
- **Pay-as-you-go or reserve?** Tokens cost 6,000 times 6.5 cents: about $390 a month. Reserved capacity is counted in PTUs (provisioned throughput units). For GPT-6 Sol, 60,000 plus 5 times 7,500, divided by 3,000 per PTU, is 32.5, rounded up to 35 PTUs: about $9,100 a month at the $260 example price <https://learn.microsoft.com/azure/foundry/openai/how-to/provisioned-throughput-sizing>. Even the smallest, 15 PTUs, is $3,900. Stay on pay-as-you-go.

## 3. What changes the price

Each lever can cost quality, so run your eval set before and after. Microsoft's startup guide: "An optimization that breaks quality isn't an optimization. It's an outage." <https://learn.microsoft.com/startups/build/ai/ai-cost-optimization>

- **A smaller model, or routing.** From smallest to largest in one line-up, list prices differ about 10 to 40 times (example list prices on 2026-10-11: Claude Haiku 5.5 input $0.10 per million tokens, Opus 5.5 $4) <https://platform.claude.com/docs/en/about-claude/pricing>. AWS says test the smallest first and move up only until it passes <https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/gencost01-bp01.html>. *Risk:* lower pass rate, more retries. Routing isn't free: something must spot easy requests at request time (a rule, a classifier, which is a small sorter model, or a small model call), adding cost and delay; evals only label requests afterwards. Foundry's model router bills its own input tokens <https://learn.microsoft.com/azure/foundry/openai/concepts/model-router>.
- **Prompt caching.** Put the parts that never change first. Cached input costs about a tenth of normal or less. On Claude, a 5-minute cache write costs 1.25 times normal input, so it pays off after one reuse <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>. On newer OpenAI and Azure GPT models (GPT-5.6 and later), caching is automatic, writes also cost extra, and entries last at least 30 minutes <https://developers.openai.com/api/docs/guides/prompt-caching> <https://learn.microsoft.com/azure/foundry/openai/how-to/prompt-caching>. *Risk:* none to answers, but no saving if something that changes (a date, a name) comes before the cached part.
- **Batch for work nobody waits for.** About half price, results within 24 hours on Azure <https://azure.microsoft.com/en-us/pricing/details/azure-openai/>. Good for nightly evals and LLM judging. For GPT-6 models on Azure, the half-price option listed is Flex (preview), not Batch (Retail Prices API); check which price meters your model has. *Risk:* same quality, longer wait. Never for chat.
- **Shorter answers.** Output costs about 5 to 6 times input. AWS says keep answers as short as the use case allows, and ask for just a label when code only needs one <https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/gencost03-bp02.html>. *Risk:* cut-off answers, broken JSON. On reasoning models a tight answer limit can return nothing (section 2).
- **Less context.** Fewer chunks, summarised history, two or fewer retrievals per turn. One product change can grow a RAG prompt from 800 to 12,000 tokens (startup guide). Models use long inputs unevenly <https://www.trychroma.com/research/context-rot>. *Risk:* drop the chunk with the answer and the model guesses; run scorers (checks that grade each answer) for groundedness (is the answer backed by the documents?) and correctness.
- **Cap agent loops.** Agents used about 4 times the tokens of a chat, multi-agent systems about 15 times <https://www.anthropic.com/engineering/multi-agent-research-system>. A recursion limit (in LangGraph, the most steps one run may take) and token limits make the worst case a known number <https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/gencost05-bp01.html>. *Risk:* hard tasks stop unfinished; count them as failures.
- **Fine-tuning or self-hosting.** Last resorts with always-on costs: a fine-tuned Azure model is charged hourly for hosting even when unused <https://learn.microsoft.com/azure/ai-foundry/openai/how-to/manage-costs>, and your own GPUs cost money with or without requests.

Also raising the bill: Data Zone (a deployment type that keeps processing inside one zone, such as the US or the EU) costs about 1.1 times Global (Retail Prices API); very long GPT-6 prompts count double for input (sizing page); Anthropic adds 286 to 804 hidden tokens when you send tools (Claude pricing page); agent and reasoning work can use 5 to 30 times the tokens of plain chat <https://www.finops.org/insights/token-economics-the-atomic-unit-of-ai-value/>. Microsoft measured a 10-token question using about 5,500 to 6,400 tokens over 2 calls, on older GPT-3.5 and GPT-4 models <https://learn.microsoft.com/azure/foundry-classic/openai/concepts/use-your-data>.

## 4. On Azure AI Foundry and the Databricks gateway

**Pay-as-you-go deployments.** Quota is tokens per minute per region, model and deployment type, shared out to deployments with a requests-per-minute limit (checks in section 2). Standard deployments can be slowed when the shared pool is busy (quota page).

**Provisioned throughput (PTU).** Capacity rented by the hour or reserved for 1 month or 1 year. You pay for every deployed PTU, used or not, and can't pause it <https://learn.microsoft.com/azure/foundry/openai/concepts/provisioned-throughput-billing>. Size it as in section 2; Global and Data Zone start at 15 PTUs, in steps of 5. GPT-6 models count "normalized tokens": cached input 0.1 (0.05 on GPT-6.1 Sol), cache write 1.25, output 5, long-context input 2, long-context output 7.5, so cached tokens now use some capacity (sizing page). Example list prices, East US 2: Global $1.00 per PTU an hour, $260 a month on a 1-month reservation, $2,652 a year (Retail Prices API). Create the deployment first, then reserve: a reservation doesn't guarantee capacity, and unused hours are lost (billing page).

**When does reserving pay?** For GPT-6 Astra and Sol only, Microsoft's sizing page shows a PTU at its $260 example price costing about the same as pay-as-you-go at 100 percent use, and more per token below that. Our arithmetic: a 1-year reservation (about $221 a month) breaks even near 85 percent busy; hourly never. For gpt-5.4-mini, 1-year breaks even near 86 percent and 1-month never. So for these models reserving mostly buys guaranteed throughput and steadier speed. Microsoft's counterpoint: its PTU overview names production-scale volume, where per-token billing gets expensive, as a reason to choose PTU, and presents reservations as a discount on hourly PTU billing <https://learn.microsoft.com/azure/foundry/openai/concepts/provisioned-throughput>.

**Spillover.** Overflow from a provisioned deployment can go to a standard one (set on the deployment, or per request with the `x-ms-spillover-deployment` header), but not for third-party models such as DeepSeek and Llama (PTU overview). So reserve the baseline and spill the peaks.

**The gateway (Unity Gateway, the new name for AI Gateway).** Rate limits per service, user or group (section 2). Every request is logged to `system.ai_gateway.usage` with input, output, cache and reasoning tokens, status, speed and request tags; that logging is billed <https://learn.microsoft.com/azure/databricks/ai-gateway/usage-tracking>.

**Usage tags.** Tag every model service in Terraform (team, project, environment, and a workload tag with an "eval" value so testing costs show separately; startup guide). Service tags count toward budgets; request tags (the `Databricks-Ai-Gateway-Request-Tags` header) reach the usage tables but not budgets <https://learn.microsoft.com/azure/databricks/ai-gateway/budgets>.

**Budgets.** Databricks account budgets use list price, allow four thresholds, and email up to 24 hours late <https://learn.microsoft.com/azure/databricks/admin/account-settings/budgets>. Unity Gateway budgets act in near real time and can alert or block, overall or per user; but blocking is approximate, provisioned throughput isn't tracked, and Foundry (external model) spend counts only if you tick "Include external model usage" (Beta) (gateway budgets page). Azure OpenAI has no hard spending limit; Cost Management budgets only alert (manage-costs page). Use three layers: a budget alert (tells you), a rate limit (slows a caller), a loop cap (stops a runaway run).

**Where the real spend shows up.** Azure bills the Foundry tokens, so Azure Cost Management is the bill of record (Azure OpenAI sits under Cognitive Services; filter by service tier "Azure OpenAI") (manage-costs page). The gateway's `system.ai_gateway.external_model_spend` holds hourly *estimates* for external models that may not match the invoice; Databricks-hosted usage is in `system.billing.usage` <https://learn.microsoft.com/azure/databricks/ai-gateway/cost-observability>. MLflow 3 tracing records tokens per call and per trace from 3.2, and dollar cost from 3.10 via LiteLLM (an open-source library with a table of model prices); on Databricks-managed MLflow, cost appears only if your app installs LiteLLM or you set it <https://mlflow.org/docs/latest/genai/tracing/token-usage-cost/>. Join trace cost with your scorers' pass or fail for cost per finished task.

## 5. Common mistakes and their fixes

- **Pricing tokens only.** In GDPval one model was 474 times cheaper on model cost but only 1.2 to 1.6 times cheaper once review and redo counted; a weaker model cost more than a person (step 5 link). *Fix:* cost per finished task.
- **Saved minutes counted as money; no numeric baseline; one token count from a short test; sizing from the daily average.** *Fix:* steps 2 to 4 and the capacity check.
- **The answer limit huge on an ordinary model** (max_tokens; eats quota) **or tiny on a reasoning model** (max_completion_tokens or max_output_tokens; empty answers). *Fix:* tune from traces.
- **Reserving to save money on part-day traffic, or forgetting always-on items.** *Fix:* pay-as-you-go until steady; a cost-sheet row for each always-on item.
- **Cutting cost without evals.** *Fix:* the startup guide suggests testing one or two changes behind a feature flag (a switch that turns a change on for some users only) for 7 to 14 days, watching cost per active user, p95 response time (95 of every 100 requests finish within this time) and eval score, and reverting if the score drops past your tolerance.
- **Trusting a budget alert to stop spending.** *Fix:* three layers (section 4).
- **Skipping why projects fail.** Gartner predicted at least 30 percent of GenAI projects would be dropped after proof of concept by end of 2025, over poor data, weak risk controls, rising costs or unclear value <https://web.archive.org/web/2025/https://www.gartner.com/en/newsroom/press-releases/2024-07-29-gartner-predicts-30-percent-of-generative-ai-projects-will-be-abandoned-after-proof-of-concept-by-end-of-2025>. RAND found the top root cause is a misunderstood problem, the wrong metric, or a poor fit with the daily work, then too little data <https://www.rand.org/pubs/research_reports/RRA2680-1.html>. RAND's study left out projects that only prompted a ready-made LLM, so it fits projects like this one only loosely. Microsoft says adoption, not the licence, is the real investment <https://learn.microsoft.com/microsoft-copilot-studio/guidance/agent-business-value-measure-impact>. Treat headline failure rates as warnings: each measured something different. *Fix:* steps 1 to 3 before code.

## 6. What the critic corrected

- **One example everywhere** (6.5 cents of model cost a ticket; the draft mixed 5 and 6.5). Every price is labelled as an example with source and date.
- **One value formula** for method and example; the draft's separate attribution-discount model was dropped (Microsoft uses it for wider results such as revenue). The real-money share shrinks only freed staff time, not model or error costs, and the same real saving a ticket feeds monthly net, break-even and ROI.
- **Added:** errors that slip through, the time-savings trap, one first-year ROI including the build, payback ignoring ramp-up, the reasoning-model max_tokens exception, a burst factor, the cost of routing, the data check and why projects fail.
- **PTU break-even scoped** to GPT-6 Astra and Sol (gpt-5.4-mini differs), beside Microsoft's counterpoint. Price gap is 10 to 40 times, not 50 (that compared two families).
- **Dropped** the single-GPU self-hosting comparison: unbacked, and one 80 GB card can't hold a 70B model at full precision.
- **Capacity** is checked against the Foundry deployment's TPM and the gateway's limits, not Databricks' pay-per-token tiers.
- **Cut** unbacked side figures (fine-tuning and quantization savings, the search index's share of the bill). Re-checked and kept: the time-savings trap, the 5,172-agent study, budget and rate-limit behaviour, MLflow versions, the feature-flag test.

## 7. Sources

- <https://learn.microsoft.com/azure/cloud-adoption-framework/ai-agents/business-strategy-plan>
- <https://learn.microsoft.com/microsoft-copilot-studio/guidance/agent-business-value-define-value>
- <https://learn.microsoft.com/microsoft-copilot-studio/guidance/agent-business-value-measure-impact>
- <https://learn.microsoft.com/azure/well-architected/cost-optimization/cost-model>
- <https://www.finops.org/wg/finops-for-ai-overview/>
- <https://www.finops.org/insights/token-economics-the-atomic-unit-of-ai-value/>
- <https://arxiv.org/abs/2510.04374>
- <https://arxiv.org/abs/2304.11771>
- <https://web.archive.org/web/2025/https://www.gartner.com/en/newsroom/press-releases/2024-07-29-gartner-predicts-30-percent-of-generative-ai-projects-will-be-abandoned-after-proof-of-concept-by-end-of-2025>
- <https://www.rand.org/pubs/research_reports/RRA2680-1.html>
- <https://prices.azure.com/api/retail/prices>
- <https://azure.microsoft.com/en-us/pricing/details/azure-openai/>
- <https://platform.claude.com/docs/en/about-claude/pricing>
- <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>
- <https://developers.openai.com/api/docs/guides/reasoning>
- <https://learn.microsoft.com/azure/foundry/openai/how-to/reasoning>
- <https://developers.openai.com/api/docs/guides/prompt-caching>
- <https://learn.microsoft.com/azure/foundry/openai/how-to/prompt-caching>
- <https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/gencost01-bp01.html>
- <https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/gencost03-bp02.html>
- <https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/gencost05-bp01.html>
- <https://learn.microsoft.com/startups/build/ai/ai-cost-optimization>
- <https://learn.microsoft.com/azure/foundry/openai/concepts/model-router>
- <https://learn.microsoft.com/azure/foundry-classic/openai/concepts/use-your-data>
- <https://www.anthropic.com/engineering/multi-agent-research-system>
- <https://www.trychroma.com/research/context-rot>
- <https://learn.microsoft.com/azure/foundry/openai/how-to/quota>
- <https://learn.microsoft.com/azure/foundry/openai/how-to/latency>
- <https://learn.microsoft.com/azure/foundry/openai/how-to/provisioned-throughput-sizing>
- <https://learn.microsoft.com/azure/foundry/openai/concepts/provisioned-throughput>
- <https://learn.microsoft.com/azure/foundry/openai/concepts/provisioned-throughput-billing>
- <https://learn.microsoft.com/azure/ai-foundry/openai/how-to/manage-costs>
- <https://learn.microsoft.com/azure/databricks/ai-gateway/rate-limits>
- <https://learn.microsoft.com/azure/databricks/ai-gateway/usage-tracking>
- <https://learn.microsoft.com/azure/databricks/ai-gateway/budgets>
- <https://learn.microsoft.com/azure/databricks/ai-gateway/cost-observability>
- <https://learn.microsoft.com/azure/databricks/admin/account-settings/budgets>
- <https://learn.microsoft.com/azure/databricks/machine-learning/foundation-model-apis/limits>
- <https://mlflow.org/docs/latest/genai/tracing/token-usage-cost/>
