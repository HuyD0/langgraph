"""Driving one practice session: the loop that feeds the graph and reads its pauses.

Separated from the CLI on purpose. This module knows how to run a session but not
how to talk to a terminal - it calls you back when it needs code. That means the
same session logic could sit behind a web app or a notebook without change, and it
can be tested with a scripted "learner" that never touches stdin.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from langgraph.types import Command

from drill.deps import Deps
from drill.problems import Problem, get_problem
from drill.state import DrillState
from drill.tracking import drill_run, log_session_metrics


class SubmissionSource(Protocol):
    """Anything that can supply a solution when the graph asks for one."""

    def __call__(self, problem: Problem, request: dict) -> str: ...


@dataclass
class SessionOutcome:
    """What happened over one problem."""

    problem: Problem
    solved: bool
    attempts: int
    hints: list[str] = field(default_factory=list)
    feedback: str = ""
    final_state: DrillState = field(default_factory=dict)  # type: ignore[arg-type]


def run_session(
    graph: Any,
    deps: Deps,
    get_submission: SubmissionSource,
    problem_id: str | None = None,
    topic: str | None = None,
    thread_id: str | None = None,
    on_event: Callable[[str, dict], None] | None = None,
) -> SessionOutcome:
    """Run one problem to completion, asking ``get_submission`` for code as needed.

    The loop mirrors the graph exactly: invoke, and if the result carries an
    ``__interrupt__`` the graph is paused waiting for a submission, so collect one
    and resume with ``Command(resume=...)``. When there is no interrupt, the graph
    reached END and the session is over.
    """
    thread_id = thread_id or uuid.uuid4().hex[:12]
    config = deps.as_config(thread_id)
    emit = on_event or (lambda kind, payload: None)

    # First invoke: select_problem runs, then the graph pauses for attempt 1.
    state: dict = graph.invoke(
        {"problem_id": problem_id or "", "topic": topic or ""}, config=config
    )
    problem = get_problem(graph.get_state(config).values["problem_id"])
    emit("problem", {"problem": problem})

    with drill_run(problem, deps.settings, thread_id):
        while "__interrupt__" in state:
            request = state["__interrupt__"][0].value
            emit("awaiting_submission", request)

            submission = get_submission(problem, request)
            state = graph.invoke(Command(resume={"submission": submission}), config=config)

            values = graph.get_state(config).values
            if "__interrupt__" in state:
                # Paused again, which means the last attempt failed and a hint is ready.
                emit("hint", {"hint": values.get("feedback", ""), "result": values.get("result")})

        final: DrillState = graph.get_state(config).values
        log_session_metrics(final)

    solved = bool((final.get("result") or {}).get("passed"))
    emit("finished", {"solved": solved, "feedback": final.get("feedback", "")})

    return SessionOutcome(
        problem=problem,
        solved=solved,
        attempts=final.get("attempts", 0),
        hints=list(final.get("hints", [])),
        feedback=final.get("feedback", ""),
        final_state=final,
    )
