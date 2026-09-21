"""The graph's nodes: one function per step the tutor takes.

Every node has the same shape - take the state, return a partial update - and every
node is an ordinary function you can call directly in a test without a graph, a
model, or a network. That is the point of the shape.
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from drill.deps import deps_from_config
from drill.problems import Problem, get_problem
from drill.progress import new_attempt
from drill.prompts import explain_prompt, hint_prompt, review_prompt
from drill.sandbox import first_failure, run_submission
from drill.state import DrillState


def _describe(fn) -> None:
    """Attach the node's docstring to its MLflow span.

    ``mlflow.langchain.autolog()`` names each span after the node function but
    shows nothing about what the node is for. This makes a trace readable without
    opening the code. It is a no-op when tracing is off.
    """
    try:
        import mlflow

        span = mlflow.get_current_active_span()
        if span is not None:
            span.set_attribute("description", (fn.__doc__ or "").strip())
    except Exception:
        pass


def _format_failure(problem: Problem, state: DrillState) -> str:
    """Describe what went wrong, in the terms the tutor should reason about."""
    result = state.get("result") or {}

    if result.get("fatal_error"):
        return f"Their code did not run at all:\n{result['fatal_error']}"

    case = first_failure(result)  # type: ignore[arg-type]
    if case is None:
        return "No failing case."

    lines = [
        f"Failing case: {problem.function_name}({', '.join(repr(a) for a in case['args'])})",
        f"  expected: {case['expected']!r}",
    ]
    if case["error"]:
        lines.append(f"  raised:   {case['error'].strip().splitlines()[-1]}")
    else:
        lines.append(f"  got:      {case['actual']!r}")
    lines.append(f"Passed {result.get('passed_count', 0)} of {result.get('total', 0)} cases.")
    return "\n".join(lines)


def _problem_brief(problem: Problem) -> str:
    return (
        f"Problem: {problem.title} ({problem.difficulty}, topic: {problem.topic})\n"
        f"{problem.prompt}\n"
        f"Target complexity: {problem.target_complexity}"
    )


def _ask(deps, system: str, user: str) -> str:
    """One turn against the chat model, returning plain text."""
    response = deps.chat_model.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)]
    )
    content = getattr(response, "content", response)
    if isinstance(content, list):
        # Some providers return content as a list of typed parts.
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    return str(content).strip()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def select_problem_node(state: DrillState, config: RunnableConfig) -> dict:
    """Choose what to practise, based on the topic you are weakest at."""
    _describe(select_problem_node)
    deps = deps_from_config(config)

    problem = deps.progress.choose_problem(
        problem_id=state.get("problem_id") or None,
        topic=state.get("topic") or None,
    )
    return {
        "problem_id": problem.id,
        "topic": problem.topic,
        "attempts": 0,
        "hints": [],
        "max_attempts": deps.settings.max_attempts,
        "started_at": time.time(),
    }


def await_submission_node(state: DrillState, config: RunnableConfig) -> dict:
    """Pause the graph and wait for you to submit a solution.

    ``interrupt()`` suspends the whole graph and hands control back to whatever
    invoked it. The CLI then collects your code and resumes with
    ``Command(resume={"submission": ...})``, at which point this node runs *again
    from the top* and ``interrupt()`` returns that value instead of pausing.

    Because the node re-runs on resume, nothing that has a side effect may happen
    before the interrupt call. That is why it is the first statement here.
    """
    payload = interrupt(
        {
            "kind": "submission_request",
            "problem_id": state["problem_id"],
            "attempt": state.get("attempts", 0) + 1,
            "max_attempts": state.get("max_attempts", 3),
            "hints": state.get("hints", []),
        }
    )
    _describe(await_submission_node)

    submission = payload.get("submission", "") if isinstance(payload, dict) else str(payload)
    return {"submission": submission, "attempts": state.get("attempts", 0) + 1}


def run_tests_node(state: DrillState, config: RunnableConfig) -> dict:
    """Run the submitted code against the problem's test cases in a subprocess."""
    _describe(run_tests_node)
    deps = deps_from_config(config)
    problem = get_problem(state["problem_id"])

    result = run_submission(
        problem, state.get("submission", ""), timeout=deps.settings.sandbox_timeout
    )
    return {"result": result}


def hint_node(state: DrillState, config: RunnableConfig) -> dict:
    """Give one Socratic hint about the failing case, without revealing code."""
    _describe(hint_node)
    deps = deps_from_config(config)
    problem = get_problem(state["problem_id"])

    previous = state.get("hints", [])
    prior = (
        "\n".join(f"- {h}" for h in previous)
        if previous
        else "(none yet - this is your first hint to them)"
    )

    hint = _ask(
        deps,
        hint_prompt(),
        f"{_problem_brief(problem)}\n\n"
        f"Attempt {state.get('attempts', 1)} of {state.get('max_attempts', 3)}.\n\n"
        f"Their code:\n```python\n{state.get('submission', '')}\n```\n\n"
        f"{_format_failure(problem, state)}\n\n"
        f"Hints you already gave:\n{prior}",
    )
    return {"hints": [*previous, hint], "feedback": hint}


def review_node(state: DrillState, config: RunnableConfig) -> dict:
    """Critique a passing solution on complexity and the edge cases it glosses over."""
    _describe(review_node)
    deps = deps_from_config(config)
    problem = get_problem(state["problem_id"])
    result = state.get("result") or {}

    review = _ask(
        deps,
        review_prompt(),
        f"{_problem_brief(problem)}\n\n"
        f"Their passing solution:\n```python\n{state.get('submission', '')}\n```\n\n"
        f"They solved it on attempt {state.get('attempts', 1)} of "
        f"{state.get('max_attempts', 3)}, using {len(state.get('hints', []))} hint(s), "
        f"passing {result.get('passed_count', 0)}/{result.get('total', 0)} cases.",
    )
    return {"feedback": review, "verdict": "solved"}


def explain_node(state: DrillState, config: RunnableConfig) -> dict:
    """Walk through the worked solution once the attempts are used up."""
    _describe(explain_node)
    deps = deps_from_config(config)
    problem = get_problem(state["problem_id"])

    explanation = _ask(
        deps,
        explain_prompt(),
        f"{_problem_brief(problem)}\n\n"
        f"The pattern this teaches: {problem.pattern}\n\n"
        f"Their final attempt:\n```python\n{state.get('submission', '')}\n```\n\n"
        f"{_format_failure(problem, state)}\n\n"
        f"Reference solution:\n```python\n{problem.reference_solution}```",
    )
    return {"feedback": explanation, "verdict": "explain"}


def record_node(state: DrillState, config: RunnableConfig) -> dict:
    """Write the finished session to your practice history."""
    _describe(record_node)
    deps = deps_from_config(config)
    problem = get_problem(state["problem_id"])

    finished = time.time()
    solved = bool((state.get("result") or {}).get("passed"))
    deps.progress.record(
        new_attempt(
            problem,
            solved=solved,
            attempts=state.get("attempts", 0),
            hints_used=len(state.get("hints", [])),
            duration_s=finished - state.get("started_at", finished),
        )
    )
    return {"finished_at": finished}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def route_after_tests(state: DrillState) -> str:
    """Decide where to go after grading: celebrate, hint, or explain.

    A plain function returning a string. LangGraph calls it on the edge and uses
    the return value to pick the next node, which means the tutor's core policy
    is one testable function with no model call in it.
    """
    result = state.get("result") or {}
    if result.get("passed"):
        return "review"
    if state.get("attempts", 0) >= state.get("max_attempts", 3):
        return "explain"
    return "hint"
