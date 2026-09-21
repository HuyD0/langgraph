"""Wiring the nodes together into the tutor's control flow.

The whole graph, in one picture::

    START
      |
      v
    select_problem
      |
      v
    await_submission  <--------------+
      |                              |
      v                              |
    run_tests                        |
      |                              |
      +-- passed? ------> review     |
      |                     |        |
      +-- out of tries? -> explain   |
      |                     |        |
      +-- otherwise ----> hint ------+
                            |
                     (review/explain)
                            |
                            v
                          record --> END

The loop back from ``hint`` to ``await_submission`` is what makes this a *graph*
rather than a pipeline, and it is the reason the state carries ``attempts``: a
cycle needs something that changes, or it never terminates.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from drill.nodes import (
    await_submission_node,
    explain_node,
    hint_node,
    record_node,
    review_node,
    route_after_tests,
    run_tests_node,
    select_problem_node,
)
from drill.state import DrillState


def build_drill_graph(checkpointer: Any | None = None):
    """Compile the tutor graph.

    A checkpointer is **required** for the human-in-the-loop pause to work: an
    ``interrupt()`` has to write the half-finished state somewhere before handing
    control back, or there would be nothing to resume from. ``InMemorySaver`` keeps
    it in the process, which is all a single CLI session needs; swap in
    ``SqliteSaver`` if you want sessions to survive a restart.
    """
    if checkpointer is None:
        from langgraph.checkpoint.memory import InMemorySaver

        checkpointer = InMemorySaver()

    graph = StateGraph(DrillState)

    graph.add_node("select_problem", select_problem_node)
    graph.add_node("await_submission", await_submission_node)
    graph.add_node("run_tests", run_tests_node)
    graph.add_node("hint", hint_node)
    graph.add_node("review", review_node)
    graph.add_node("explain", explain_node)
    graph.add_node("record", record_node)

    graph.add_edge(START, "select_problem")
    graph.add_edge("select_problem", "await_submission")
    graph.add_edge("await_submission", "run_tests")

    # The one branching point. The third argument maps the router's return value
    # to a node name; listing it explicitly means a typo in `route_after_tests`
    # fails at compile time instead of at 11pm mid-session.
    graph.add_conditional_edges(
        "run_tests",
        route_after_tests,
        {"review": "review", "hint": "hint", "explain": "explain"},
    )

    graph.add_edge("hint", "await_submission")  # the retry loop
    graph.add_edge("review", "record")
    graph.add_edge("explain", "record")
    graph.add_edge("record", END)

    return graph.compile(checkpointer=checkpointer)
