"""Milestone 10 answer key - one agent or a team: the checker's round limit, the hand-off,
passed every time, tokens per helper, and the verdict by the rule written first."""

from __future__ import annotations


def after_check(issues, rounds, max_rounds=3):
    """Where the team goes after the checker: done, stop at the round limit, or fix and check again."""
    if len(issues) == 0:
        return "done"
    if rounds >= max_rounds:
        return "stop"
    return "fix"


def handoff_kept(found, final):
    """The share of a helper's facts that reach the final answer, and the facts that didn't."""
    if len(found) == 0:
        return {"kept": 1.0, "lost": []}
    text = final.lower()
    lost = []
    for fact in found:
        if fact.lower() not in text:
            lost.append(fact)
    kept = len(found) - len(lost)
    return {"kept": round(kept / len(found), 2), "lost": sorted(lost)}


def every_time(runs):
    """The share of questions passed on every try."""
    passed = 0
    for qid in runs:
        if all(runs[qid]):
            passed += 1
    return passed / len(runs)


def tokens_by_agent(calls):
    """Each agent's tokens (input plus output), and the agent that used the most."""
    totals = {}
    for c in calls:
        used = c["input_tokens"] + c["output_tokens"]
        totals[c["agent"]] = totals.get(c["agent"], 0) + used
    top = None
    for name in sorted(totals):
        if top is None or totals[name] > totals[top]:
            top = name
    return [top, totals]


def team_verdict(one, team, rule):
    """Apply the decision rule written before the runs: "team" or "one agent"."""
    gain = round(every_time(team["runs"]) - every_time(one["runs"]), 2)
    wins = 0
    for qid in team["runs"]:
        wins += team["runs"][qid].count(True)
    if wins == 0:
        return "one agent"
    if gain < rule["min_gain"]:
        return "one agent"
    if team["cost"] / wins > rule["max_cost_per_success"]:
        return "one agent"
    return "team"
