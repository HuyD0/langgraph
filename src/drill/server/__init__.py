"""The Daily Drill tutor as a local service: one core, two doors.

    uv run drill-server     # the web door: serves the page at http://localhost:8787 and
                            # answers its /api requests; also serves the MCP door at /mcp
    uv run drill-mcp        # the MCP door over stdio, for a Claude app's MCP config

Both doors share the same three pieces:

- :mod:`drill.server.bank`   - the lessons and exercises, read from the page's build
- :mod:`drill.server.router` - which model answers (Ollama on this Mac first, a hosted
  model as the fallback), with a cache and a daily budget
- :mod:`drill.server.store`  - your progress and study list, in one SQLite file

Nothing here needs the cloud. Pointing it at a hosted model or a Postgres database later
is configuration, not code, which is what makes the enterprise version the same code.
"""
