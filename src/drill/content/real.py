"""Build it for real: where a lesson's idea is built with the real libraries, in a notebook.

The lessons' exercises teach each idea in plain Python, in the browser. The notebooks in
notebooks/ build the same ideas with MLflow, LangGraph and LangChain's real classes, on your
Mac. The Build step shows a card pointing from the lesson to the exact notebook section.
tests/test_content.py checks every lesson and section named here exists.
"""

from __future__ import annotations

NOTEBOOKS = {
    "m8_designing_an_eval": "Notebook 8: Designing an eval",
    "m9a_build_the_eval_set": "Notebook 9a: Build the eval set from production traffic",
    "m9b_plan_and_run": "Notebook 9b: Plan and run the experiment",
    "m9c_analyse_and_decide": "Notebook 9c: Analyse and decide",
    "m9d_ship_monitor_grow": "Notebook 9d: Ship, monitor, and grow the eval set",
    "m10_one_agent_or_a_team": "Notebook 10: One agent or a team?",
    "m11_vet_a_use_case": "Notebook 11: Vet a use case with MLflow",
    "m12_build_the_agent_for_real": "Notebook 12: Build the agent for real",
}

# lesson id: (notebook, section heading as written in the notebook, the real things you use)
REAL: dict[str, tuple[str, str, list[str]]] = {
    # Use case and fit
    "well_architected": ("m11_vet_a_use_case", "1. Trace a review", ["@mlflow.trace", "mlflow.update_current_trace", "SpanType"]),
    "fit_for_purpose": ("m11_vet_a_use_case", "5. A scorer and an evaluation", ["@scorer", "Feedback", "mlflow.genai.evaluate"]),
    # Building with LLMs
    "resolve_prompt": ("m11_vet_a_use_case", "7. The prompt registry", ["mlflow.genai.register_prompt", "set_prompt_alias", "load_prompt"]),
    # Experiment design
    "best_run": ("m8_designing_an_eval", "3. Run both prompts on the same messages", ["mlflow.start_run", "mlflow.log_metrics", "mlflow.set_tag"]),
    "plan_gaps": ("m9b_plan_and_run", "1. Frame: write the plan before running anything", ["mlflow.set_active_model", "mlflow.log_dict"]),
    "clear_winner": ("m8_designing_an_eval", "7. Decide, using the rule you wrote first", ["mlflow.log_metrics", "mlflow.log_dict"]),
    "paired_verdict": ("m9c_analyse_and_decide", "5. The paired test: is v2's win real?", ["mlflow.search_traces", "trace.info.assessments"]),
    "biggest_gap": ("m9c_analyse_and_decide", "2. The oracle: how much can retrieval gain at all?", ["mlflow.search_traces"]),
    "ablation_report": ("m9c_analyse_and_decide", "8. The ablation: what does the rewrite add?", ["mlflow.search_traces"]),
    # Agents with LangGraph
    "run_agent": ("m12_build_the_agent_for_real", "2. The agent loop as a graph", ["StateGraph", "MessagesState", "ToolNode", "tools_condition"]),
    "tool_pairs": ("m12_build_the_agent_for_real", "1. A tool", ["@tool", "ToolMessage", "bind_tools"]),
    "trim_history": ("m12_build_the_agent_for_real", "3. Memory", ["InMemorySaver", "thread_id"]),
    "approval_run": ("m12_build_the_agent_for_real", "4. A person approves risky actions", ["interrupt", "Command(resume=...)"]),
    "assemble_stream": ("m12_build_the_agent_for_real", "5. Streaming", ["graph.stream", "stream_mode=\"updates\""]),
    "agent_scorecard": ("m10_one_agent_or_a_team", "2. The questions, and how an answer is checked", ["@scorer", "Feedback"]),
    # Agent teams
    "need_a_team": ("m10_one_agent_or_a_team", "1. Write the plan first", ["mlflow.log_dict"]),
    "gather_results": ("m10_one_agent_or_a_team", "4. The team, one piece at a time", ["StateGraph", "Send", "create_agent"]),
    "team_experiment": ("m10_one_agent_or_a_team", "5. Run the experiment", ["mlflow.genai.evaluate", "mlflow.langchain.autolog"]),
    # Evals
    "assign_splits": ("m9a_build_the_eval_set", "5. Split into dev, test and holdout", ["mlflow.search_traces", "mlflow.genai datasets"]),
    "review_queue": ("m9a_build_the_eval_set", "2. Label: grades and expected answers", ["mlflow.log_expectation", "mlflow.log_feedback"]),
    "weighted_score": ("m8_designing_an_eval", "4. Score each group, with a range", ["mlflow.log_metrics"]),
    "must_pass_gate": ("m9c_analyse_and_decide", "1. The must-pass gate comes first", ["mlflow.search_traces", "trace.info.assessments"]),
    "judge_agreement": ("m11_vet_a_use_case", "6. Does a judge agree with you?", ["cohen_kappa_score", "mlflow.log_feedback"]),
    "cohen_kappa": ("m11_vet_a_use_case", "6. Does a judge agree with you?", ["sklearn.metrics.cohen_kappa_score"]),
    "checker_score": ("m11_vet_a_use_case", "5. A scorer and an evaluation", ["@scorer", "mlflow.genai.evaluate"]),
    "change_report": ("m9c_analyse_and_decide", "6. Read the regressions and improvements", ["mlflow.search_traces"]),
    "mix_shift": ("m9d_ship_monitor_grow", "2. Monitor: a signal, not a score", ["mlflow.search_traces", "mlflow.log_expectation"]),
    # Shipping
    "route_request": ("m9d_ship_monitor_grow", "1. Ship behind the gate, then a canary", ["mlflow.get_trace"]),
    # Tracing and AgentOps
    "summarize_by_tag": ("m9b_plan_and_run", "3. Build and trace: make every request inspectable", ["@mlflow.trace", "mlflow.update_current_trace"]),
    "slowest_chain": ("m12_build_the_agent_for_real", "6. Tracing the agent", ["mlflow.langchain.autolog", "SpanType.TOOL"]),
    "failure_counts": ("m9d_ship_monitor_grow", "3. Trace the signal to a cause", ["mlflow.search_traces", "mlflow.log_feedback"]),
}


def data() -> dict:
    return {
        "notebooks": NOTEBOOKS,
        "lessons": {lid: {"notebook": nb, "section": section, "uses": uses} for lid, (nb, section, uses) in REAL.items()},
    }
