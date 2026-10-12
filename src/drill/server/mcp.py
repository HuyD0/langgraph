"""The MCP door: the same tutor as tools for Claude Code and the Claude desktop app.

MCP (Model Context Protocol) is the standard way an AI app calls functions on your
machine. Register this server once and you can say "give me my next drill" or "check
this attempt" in Claude Code, and it will use these tools, your progress and your
local model.

    uv run drill-mcp                      # stdio, for an app's MCP config
    claude mcp add drill -- /opt/homebrew/bin/uv run --directory /path/to/repo drill-mcp

The web server also serves these tools over HTTP at http://localhost:8787/mcp.

Every tool call is traced in MLflow (see ``observe``): a TOOL span with the arguments and
the result, and for hints, reviews and questions the model call inside it.
"""

from __future__ import annotations

import copy
import os
import time

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from drill.server import activity, study, tutor
from drill.server.observe import traced_tool
from drill.server.bank import Bank
from drill.server.router import ModelRouter
from drill.server.store import DocStore, open_store

READ_ONLY = ToolAnnotations(readOnlyHint=True)
PROGRESS_PATH = "data/users/local/progress"  # the same document the page uses when served locally

server = MCPServer(
    "drill",
    instructions=(
        "Daily Drill: a learning path for AI engineering (Databricks, LangGraph, LangChain, MLflow, "
        "Terraform). The learner is new to coding: explain plainly, never use Big-O notation, and "
        "prefer hints over full solutions. Start with next_drill."
    ),
)

_deps: dict = {}


def configure(store: DocStore | None = None, router: ModelRouter | None = None, bank: Bank | None = None) -> None:
    """Share one store, router and bank with the web server (or a test)."""
    _deps.update(store=store, router=router, bank=bank)


def _store() -> DocStore:
    if _deps.get("store") is None:
        _deps["store"] = open_store()
    return _deps["store"]


def _router() -> ModelRouter:
    if _deps.get("router") is None:
        _deps["router"] = ModelRouter.from_env(_store())
    return _deps["router"]


def _bank() -> Bank:
    if _deps.get("bank") is None:
        _deps["bank"] = Bank.load()
    return _deps["bank"]


def _progress() -> dict:
    return _store().get(PROGRESS_PATH) or {"solved": {}, "days": [], "lessons": {}, "current": None}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool(annotations=READ_ONLY)
@traced_tool
def next_drill() -> dict:
    """The next lesson the learner has not finished: what to read, the check question, the exercise and the interview angle."""
    bank = _bank()
    lesson_id = bank.next_lesson(_progress())
    if lesson_id is None:
        return {"done": True, "message": "Every lesson on the path is marked done. Pick any with get_drill to revisit it."}
    return bank.card(lesson_id)


@server.tool(annotations=READ_ONLY)
@traced_tool
def get_drill(lesson_id: str) -> dict:
    """One lesson by id (see list_lessons), with its exercise, scaffold and sample test case."""
    return _bank().card(lesson_id)


@server.tool(annotations=READ_ONLY)
@traced_tool
def list_lessons() -> list[dict]:
    """The whole path: modules in order, each with its lessons and whether they are done."""
    done = _progress().get("lessons", {})
    bank = _bank()
    return [
        {
            "module": m["title"],
            "lessons": [
                {"id": lid, "title": bank.lessons[lid]["title"], "done": bool(done.get(lid, {}).get("done"))}
                for lid in m["lessons"]
            ],
        }
        for m in bank.modules
    ]


@server.tool()
@traced_tool
def run_tests(lesson_id: str, code: str) -> dict:
    """Run the learner's code against the exercise's test cases. Returns pass counts and the first failure."""
    result = tutor.run_exercise(_bank().problems[lesson_id], code)
    _store().log("tests_run", lesson_id, door="mcp", passed=result["passed"],
                 passed_count=result["passed_count"], total=result["total"])
    return result


@server.tool(annotations=READ_ONLY)
@traced_tool
async def hint(lesson_id: str, code: str = "", level: int = 1) -> str:
    """A hint from the local model, levels 1 (where to look) to 3 (the approach in words). Never the solution."""
    card = _bank().card(lesson_id)
    failure = None
    if code.strip():
        result = tutor.run_exercise(_bank().problems[lesson_id], code)
        failure = result["first_failure"] or ({"error": result["fatal_error"]} if result["fatal_error"] else None)
    context = {"feature": "hint", "door": "mcp", "lesson_id": lesson_id, "exercise_fn": card["exercise"]["function"],
               "hint_level": level, "word_limit": 80}
    answer = await _router().ask(tutor.hint_prompt(card, code, level, failure), tier="quick", context=context)
    _store().log("hint_used", lesson_id, door="mcp", level=level)
    return answer.text


@server.tool(annotations=READ_ONLY)
@traced_tool
async def review(lesson_id: str, code: str) -> str:
    """Review a passing solution: how fast it is in plain words, an edge case, what to say out loud, one production practice."""
    card = _bank().card(lesson_id)
    context = {"feature": "review", "door": "mcp", "lesson_id": lesson_id, "exercise_fn": card["exercise"]["function"],
               "word_limit": 140}
    answer = await _router().ask(tutor.review_prompt(card, code), tier="complex", context=context)
    return answer.text


@server.tool(annotations=READ_ONLY)
@traced_tool
async def ask_tutor(prompt: str, tier: str = "default") -> str:
    """Ask the local tutor model anything, in the learner's plain-language style. tier: quick, default or complex."""
    context = {"feature": "ask_tutor", "door": "mcp", "question": prompt}
    answer = await _router().ask(f"{tutor.LEARNER}\n\n{prompt}", tier=tier, context=context)
    return answer.text


@server.tool(annotations=READ_ONLY)
@traced_tool
def study_list(status: str = "open") -> list[dict]:
    """Things the learner saved to understand better. status: open (to learn), due (understood
    before and due for a review: quiz them on these), got, or all."""
    items = []
    for item_id, doc in _store().list("study"):
        state = doc.get("status", "open")
        if status == "all" or state == status or (status == "due" and study.is_due(doc)):
            items.append({"id": item_id, "text": doc.get("text"), "note": doc.get("note", ""), "status": state,
                          "due": study.is_due(doc), "lesson": doc.get("problemId", "")})
    return items


@server.tool()
@traced_tool
def save_to_study(text: str, note: str = "", source: str = "Claude") -> dict:
    """Save a term, line of code or idea to the learner's study list, with an optional note on what confuses them."""
    item_id = f"s{int(time.time() * 1000):x}"
    doc = {
        "id": item_id, "text": text.strip()[:2000], "kind": "text", "source": source, "problemId": "",
        "note": note.strip(), "status": "open", "createdAt": int(time.time() * 1000),
        "updatedAt": int(time.time() * 1000), "explanation": "", "quiz": None, "thread": [],
    }
    _store().set(f"study/{item_id}", doc)
    _store().log("saved_to_study", "", door="mcp", source=source)
    return {"id": item_id, "saved": True}


@server.tool()
@traced_tool
def mark_done(lesson_id: str) -> dict:
    """Mark a lesson finished so next_drill moves on. Also counts today towards the streak."""
    bank = _bank()
    if lesson_id not in bank.lessons:
        raise KeyError(f"No lesson called {lesson_id!r}. Try list_lessons().")
    progress = _progress()
    before = copy.deepcopy(progress)
    lesson = progress.setdefault("lessons", {}).setdefault(lesson_id, {"step": 3, "checked": None, "done": False})
    lesson.update(step=3, done=True)
    today = time.strftime("%Y-%m-%d")
    if today not in progress.setdefault("days", []):
        progress["days"].append(today)
    _store().set(PROGRESS_PATH, progress)
    for kind, changed, detail in activity.progress_events(before, progress):
        _store().log(kind, changed, door="mcp", **detail)
    return {"lesson_id": lesson_id, "done": True, "next": bank.next_lesson(progress)}


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------


def http_app(port: int):
    """The MCP server as an ASGI app answering at /mcp, for mounting into the web server."""
    from mcp.server.transport_security import TransportSecuritySettings

    # Only this machine's own addresses may reach the MCP endpoint by default (a defence
    # against DNS rebinding); add more with DRILL_ALLOWED_HOSTS=host:port,host:port.
    allowed = [f"localhost:{port}", f"127.0.0.1:{port}", f"[::1]:{port}", "localhost", "127.0.0.1"]
    allowed += [h.strip() for h in os.getenv("DRILL_ALLOWED_HOSTS", "").split(",") if h.strip()]
    security = TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=allowed, allowed_origins=[])
    return server.streamable_http_app(streamable_http_path="/mcp", transport_security=security)


def main() -> None:
    """``uv run drill-mcp``: stdio transport, for a Claude app's MCP configuration."""
    from dotenv import load_dotenv

    from drill.config import PROJECT_ROOT

    load_dotenv(PROJECT_ROOT / ".env")
    server.run("stdio")
