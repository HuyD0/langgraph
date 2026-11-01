"""The insights layer: commented views, a metric view and trusted SQL functions over the app's Lakebase
data, a Genie Agent that reads them, and the managers' dashboard rebuilt on top.

    uv run drill cloud insights --dry-run          # print every statement and the JSON; runs nothing
    uv run drill cloud insights --step layer       # create the schema, views, functions, metric view, grants
    uv run drill cloud insights --step genie       # create or update the Genie Agent (with its benchmarks)
    uv run drill cloud insights --step dashboard   # rebuild the managers' dashboard in place

The SQL lives in ``sql/`` beside this file, one object per file, with two placeholders:
``{lakebase_catalog}`` (the read-only catalog over the app's database) and ``{insights_catalog}``
(the catalog that holds the ``drill_insights`` schema). Both names live in the git-ignored overrides
file, never in code. See docs/INSIGHTS.md.
"""
