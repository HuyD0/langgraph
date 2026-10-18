"""The HR assistant: the running example the lessons price, plan and judge.

One company runs through the path. Staff ask an assistant about HR policy (leave, expenses) in
Teams; the hard questions go to an HR person as tickets. The same numbers follow it from the use
case card to the production incident, so one lesson never contradicts another. They live here,
``quotes`` says which lessons repeat each one word for word, and ``tests/test_running_example.py``
fails when a lesson drifts. To change a number: edit ``HR``, then every lesson ``quotes`` lists
for it, re-derive the exercise cases it feeds, and regenerate the prepared tutor answers.

The story, in order:

- Today an HR person answers each ticket by hand: 8 minutes, $8 at $60 an hour.
- The pilot drafts answers for those tickets; HR approves or edits each one before it is sent.
  Success: 80 in 100 drafts approved unedited, on last month's 200 questions, the golden set.
- Requirements: R2 5 seconds for 95 in 100; R6 200 people at once; R7 under $2 an answer.
- Acceptance criteria: quality 0.80, 5 seconds, $2.00 a finished task, no must-pass failures.
- Cost per finished ticket: 6.5 cents of tokens, 60 cents of checking (30 in 100 checked, 2 minutes
  each, $60 an hour) and $1.20 of rework (15 in 100 redone at $8): $1.865, so about $1.87. Mistakes
  nobody caught cost 50 cents more, taken off the saving.
- Two scales, two words. HR answers 6,000 *tickets* a month by hand today, about 270 a working
  day: the business case, the total cost and the capacity plan use that. Once everyone uses it,
  staff ask about 30,000 *questions* a month: embeddings, searches and monitoring are priced on
  that.
- Total cost: build $73,000 (team 60,000, eval set 8,000, security review 5,000); a month: model
  $390, hosting $1,200, evals and monitoring $1,100, people checking and redoing $10,800.
- Payback: saving $5.635 a ticket, fixed costs $2,300 a month (hosting, evals and monitoring),
  the build pays back in 2.3 months, break-even 409 tickets a month.
- Evals: 500 examples (the 200 golden plus 300 from real traffic), 3 scorers, run twice: $18 a
  run. Labelling the golden set, 200 at 3 minutes each at $60 an hour: $600. Monitoring 1 in 10
  of 30,000 traces at $0.006: $18 a month.
"""

from __future__ import annotations

HR: dict = {
    "by_hand_minutes": 8,
    "by_hand_cost": 8,  # dollars, at the hourly rate
    "hourly_rate": 60,
    "tickets_per_month": 6000,  # answered by HR by hand today: the business case's scale
    "tickets_per_day": 270,
    "questions_per_month": 30000,  # what staff ask once everyone uses it: the data and tools' scale
    "golden_set": 200,  # last month's questions, labelled by hand
    "eval_examples": 500,  # the golden set plus real traffic
    "quality_criterion": 0.80,
    "seconds_criterion": 5,
    "cost_criterion": 2.00,  # dollars a finished task: R7, and the fit lesson's criterion
    "model_per_ticket": 0.065,
    "check_per_ticket": 0.60,
    "redo_per_ticket": 1.20,
    "cost_per_ticket": 1.865,
    "cost_per_ticket_about": "1.87",
    "uncaught_per_ticket": 0.50,
    "saving_per_ticket": 5.635,
    "build": 73000,
    "monthly": {"model": 390, "hosting": 1200, "evals": 1100, "people": 10800},
    "fixed_monthly": 2300,  # hosting plus evals: the lines that don't grow with the tickets
    "payback_months": 2.3,
    "break_even_tickets": 409,
    "judge_run": 18,  # dollars, one eval run scored by the judge
}


def quotes() -> dict[str, list[str]]:
    """What each lesson says word for word, so a number that drifts fails the test."""
    h = HR
    dollars = f"${h['cost_criterion']:.0f}"
    return {
        "use_case_card": [f"{h['by_hand_minutes']} minutes by hand, ${h['by_hand_cost']}", f"last month's {h['golden_set']} questions"],
        "gather_requirements": [f"under {dollars} an answer", f"if HR takes {h['by_hand_minutes']} minutes to answer now"],
        "split_requirements": [f"R7 Under {dollars} an answer", f"R7  Cost under {dollars} per answer", f"Under {dollars} per answer"],
        "well_architected": [f"R7: under {dollars} per answer.", f"R7 {dollars}"],
        "fit_for_purpose": [f'"cost": {h["cost_criterion"]:.2f}', f'"cost": {h["cost_per_ticket_about"]}, "must_pass_failures": 0'],
        "cost_per_finished_task": [f"${h['by_hand_cost']} by hand today", f"at ${h['hourly_rate']} an hour",
                                   f"# {h['cost_per_ticket']} dollars a finished ticket", f"{h['uncaught_per_ticket'] * 100:.0f} cents a ticket"],
        "total_cost": [f'"model": {h["monthly"]["model"]}, "hosting": {h["monthly"]["hosting"]},',
                       f'"evals": {h["monthly"]["evals"]}, "people": {h["monthly"]["people"]}',
                       f"# {sum(h['monthly'].values())} a month for 24 months: {24 * sum(h['monthly'].values())}",
                       f"# total: {h['build'] + 24 * sum(h['monthly'].values())}"],
        "payback_plan": [f"${h['by_hand_cost']} today minus about ${h['cost_per_ticket_about']} with AI",
                         f"{h['tickets_per_month']:,} tickets a month", f"fixed = {h['fixed_monthly']}", f"build = {h['build']}",
                         f"# {h['payback_months']} months", f"# round up: {h['break_even_tickets']} tickets a month"],
        "biggest_swing": [f"# tasks {h['tickets_per_month']}, saving 7, fixed {h['fixed_monthly']}"],
        "peak_capacity": [f"{h['tickets_per_day']} tickets times"],
        "embedding_cost": [f"{h['questions_per_month']:,} questions"],
        "paid_tools": [f"{h['questions_per_month']:,} questions"],
        "judge_cost": [f"{h['eval_examples']} examples ({h['golden_set']} golden, {h['eval_examples'] - h['golden_set']} from real traffic)",
                       f"${h['judge_run']} a run"],
        "eval_cost": [f"{h['golden_set']} examples at 3 minutes each", f"at ${h['hourly_rate']} an hour", f"{h['questions_per_month']:,} traces a month"],
    }
