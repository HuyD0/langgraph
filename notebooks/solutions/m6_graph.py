"""Milestone 6 answer key - wiring the graph.

Written against the names the notebook's setup cell already defines: ``StateGraph``,
``START``, ``END``, ``InMemorySaver``, ``nodes``, ``route_after_tests`` and
``DrillState``.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from drill import nodes
from drill.nodes import route_after_tests
from drill.state import DrillState


def build_drill_graph(checkpointer=None):
    """Compile the tutor graph.

    Two things carry the lesson. The explicit mapping in ``add_conditional_edges``
    means a typo in the router fails at compile time, not mid-session. And the
    checkpointer is not optional: ``interrupt()`` has to write the half-finished
    state somewhere before handing control back, so without one there is nothing
    to resume from.
    """
    graph = StateGraph(DrillState)

    graph.add_node("select_problem", nodes.select_problem_node)
    graph.add_node("await_submission", nodes.await_submission_node)
    graph.add_node("run_tests", nodes.run_tests_node)
    graph.add_node("hint", nodes.hint_node)
    graph.add_node("review", nodes.review_node)
    graph.add_node("explain", nodes.explain_node)
    graph.add_node("record", nodes.record_node)

    graph.add_edge(START, "select_problem")
    graph.add_edge("select_problem", "await_submission")
    graph.add_edge("await_submission", "run_tests")

    graph.add_conditional_edges(
        "run_tests",
        route_after_tests,
        {"review": "review", "hint": "hint", "explain": "explain"},
    )

    graph.add_edge("hint", "await_submission")  # the retry loop
    graph.add_edge("review", "record")
    graph.add_edge("explain", "record")
    graph.add_edge("record", END)

    return graph.compile(checkpointer=checkpointer or InMemorySaver())
