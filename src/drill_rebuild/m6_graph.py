"""Milestone 6 - wiring the graph.

Run: uv run pytest tests/rebuild/test_m6_graph.py

WHY THIS IS LAST
Everything before this was ordinary Python. This milestone is the LangGraph part:
nodes, edges, a conditional edge, a cycle, and the checkpointer that makes pausing
for a human possible at all.

You may import the finished node functions from `drill.nodes` - the lesson here is
the wiring, not the node bodies.
"""

from __future__ import annotations

from typing import Any


def build_drill_graph(checkpointer: Any | None = None):
    """Build and compile the tutor graph.

    The shape you are aiming for::

        START -> select_problem -> await_submission -> run_tests
                                        ^                  |
                                        |                  +-- passed -----> review --+
                                        |                  |                          |
                                        |                  +-- no tries left-> explain+
                                        |                  |                          |
                                        +------- hint <----+ otherwise                |
                                                                                      v
                                                                            record -> END

    Steps:

    1. `StateGraph(DrillState)` - the state type you built in milestone 1, or
       import `drill.state.DrillState`.
    2. `add_node(name, fn)` for each of the seven nodes in `drill.nodes`.
    3. `add_edge(START, "select_problem")` and the other plain edges.
    4. `add_conditional_edges("run_tests", route_after_tests, {...})` where the
       dict maps each string your router can return to a node name. Pass it
       explicitly rather than relying on the names matching - a typo then fails at
       compile time instead of mid-session.
    5. The cycle: an edge from "hint" back to "await_submission". This is what
       makes it a graph rather than a pipeline.
    6. Compile with a checkpointer. `InMemorySaver` is fine. This is NOT optional:
       `interrupt()` has to write the half-finished state somewhere before handing
       control back, so without a checkpointer there is nothing to resume from.

    Two things the tests check that are easy to get wrong:
    - Both "review" and "explain" must lead to "record", so a session is recorded
      whether or not you solved it.
    - "record" must lead to END.

    TODO: implement.
    """
    raise NotImplementedError("Milestone 6: implement build_drill_graph")
