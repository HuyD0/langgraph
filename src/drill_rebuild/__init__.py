"""The rebuild track: implement the tutor yourself, one milestone at a time.

`src/drill/` is the working tutor. This package is the same thing with the bodies
removed. Each module is a milestone with a matching test file under
`tests/rebuild/`, and the tests are the specification - read the test, write code
until it goes green, move on.

    uv run pytest -m rebuild                      # every milestone
    uv run pytest tests/rebuild/test_m1_state.py  # just the first

The milestones climb in difficulty:

    m1_state      typed state, partial updates      (Python types)
    m2_problems   dataclasses and lookup tables     (data modelling)
    m3_routing    the branching policy              (pure functions)
    m4_progress   aggregating your own history      (dicts, sorting, tie-breaks)
    m5_sandbox    running untrusted code safely     (subprocess, serialisation)
    m6_graph      wiring the graph together         (LangGraph)

`src/drill/` is the worked answer. Looking is allowed - but write your version
first, because reading a solution feels like understanding and rarely is. That is
the same trap as reading someone else's LeetCode answer and believing you could
have produced it.
"""
