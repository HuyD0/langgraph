# Answer key

One module per milestone, holding a worked solution for every exercise in the
matching notebook.

**If you are learning:** don't open these first. Write your own version, get the
notebook's tests green, *then* compare. Reading a solution feels like
understanding and usually is not.

**If you are teaching:** this is your answer key, and it is checked. `tests/test_notebooks.py`
executes every notebook with these solutions substituted in and asserts that all
the embedded tests pass. So a notebook whose exercise you rename, or whose tests
you tighten without updating the solution, fails CI rather than failing in front
of a room.

Milestones 1-4 are the important ones to have here: `merge_update`,
`bump_attempts`, `build_index`, `stats_by_topic` and friends are teaching
constructs that exist only in the notebooks, so `src/drill/` is *not* an answer
key for them. Milestones 5 and 6 do mirror `src/drill/sandbox.py` and
`src/drill/graph.py` fairly closely.
