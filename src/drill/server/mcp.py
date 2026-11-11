"""The MCP door: the same tutor as tools for Claude Code and the Claude desktop app.

MCP (Model Context Protocol) is the standard way an AI app calls functions on your
machine. Register this server once and you can say "give me my next drill" or "check
this attempt" in Claude Code, and it will use these tools, your progress and your
local model.

    uv run drill-mcp                      # stdio, for an app's MCP config
    claude mcp add drill -- /opt/homebrew/bin/uv run --directory /path/to/repo drill-mcp

The web server also serves these tools over HTTP at http://localhost:8787/mcp, to this
computer only: the door has no sign-in and two of its tools (``run_tests``, and ``hint`` when it
is given code) run the code they are sent. So the web server leaves it out when it listens
beyond this computer, and every request is checked by where it really came from (see
``LocalCallersOnly``). It is left out of a Databricks App too: every learner there is a different person
and this door cannot yet tell them apart (every tool reads and writes one progress document),
so the web server does not mount it there (see ``api.create_app``).

The lesson cards never carry the Check answers or the Explain sentence: the agent marks a pick
with ``check_answer`` and gets the sentence from ``mark_done``, so a learner asking "which one
is right?" is helped, not told.

Every tool call is traced in MLflow (see ``observe``): a TOOL span with the arguments and
the result, and for hints, reviews and questions the model call inside it.
"""

from __future__ import annotations

import asyncio
import copy
import ipaddress
import logging
import os
import time

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

from drill.server import activity, retrieve, study, tutor
from drill.server.observe import traced_tool
from drill.server.bank import Bank
from drill.server.retrieve import Retriever
from drill.server.router import PAGE_TIERS, ModelRouter, PromptTooLong, to_messages
from drill.server.store import DocStore, open_store

log = logging.getLogger("drill.server")

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


def configure(store: DocStore | None = None, router: ModelRouter | None = None, bank: Bank | None = None,
              retriever: Retriever | None = None) -> None:
    """Share one store, router, bank and retriever with the web server (or a test)."""
    _deps.update(store=store, router=router, bank=bank, retriever=retriever)


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


def _retriever() -> Retriever:
    if _deps.get("retriever") is None:
        _deps["retriever"] = Retriever.from_env(_bank().data)
        _deps["retriever"].start()  # on its own (drill-mcp over stdio): embed the lessons in the background
    return _deps["retriever"]


def _progress() -> dict:
    return _store().get(PROGRESS_PATH) or {"solved": {}, "days": [], "lessons": {}, "current": None}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@server.tool(annotations=READ_ONLY)
@traced_tool
def next_drill() -> dict:
    """The next lesson the learner has not finished: what to read, the Check questions (without their
    answers: mark a pick with check_answer), the exercise and the Explain angle."""
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
def check_answer(lesson_id: str, question: int = 1, picked: int = 0) -> dict:
    """Mark the learner's pick on one Check question: question counts from 1 (the card's check, then its
    more_checks in order); picked is the option's position counting from 0. Returns right or wrong and why.
    Let the learner choose first: the card leaves the answers out on purpose."""
    return _bank().check_answer(lesson_id, question, picked)


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


@server.tool()  # not READ_ONLY: passing code runs it, like run_tests
@traced_tool
async def hint(lesson_id: str, code: str = "", level: int = 1) -> str:
    """A hint from the local model, levels 1 (where to look) to 3 (the approach in words). Never the solution.
    Passing code runs it against the exercise's tests first, so the hint can point at the failing case."""
    card = _bank().card(lesson_id)
    failure = None
    if code.strip():
        # Running the code can take up to the sandbox's time limit: do it on a worker thread
        # so the web server it's mounted in keeps answering everyone else meanwhile.
        result = await asyncio.to_thread(tutor.run_exercise, _bank().problems[lesson_id], code)
        failure = result["first_failure"] or ({"error": result["fatal_error"]} if result["fatal_error"] else None)
    context = {"feature": "hint", "door": "mcp", "lesson_id": lesson_id, "exercise_fn": card["exercise"]["function"],
               "hint_level": level, "word_limit": 80}
    answer = await _router().ask(tutor.hint_prompt(card, code, level, failure), tier="quick", context=context)
    await asyncio.to_thread(_store().log, "hint_used", lesson_id, door="mcp", level=level)
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
    """Ask the local tutor model anything, in the learner's plain-language style. tier: quick or default."""
    tier = tier if tier in PAGE_TIERS else "default"  # a client can't pick the paid tier, same as the page
    context = {"feature": "ask_tutor", "door": "mcp", "question": prompt}

    def sent(hits: list[dict]) -> str:
        """The prompt the tutor gets: found paragraphs go where a lesson's text would, between the learner note
        and the question."""
        lessons = f"{retrieve.context_text(hits)}\n\n" if hits else ""
        return f"{tutor.LEARNER}\n\n{lessons}{prompt}"

    def fits(hits: list[dict]) -> bool:
        try:
            _router().check_size(to_messages(sent(hits)))
            return True
        except PromptTooLong:
            return False

    # A question too long on its own is refused before any search, as the page's 413 is: never blamed on retrieval.
    _router().check_size(to_messages(sent([])))
    # No lesson comes with this tool: find the paragraphs that fit (drill.server.retrieve), fewer when the prompt
    # has room for only some of them.
    found = retrieve.fit(await _retriever().search(prompt), fits)
    context["retrieval"] = found.trace()
    await asyncio.to_thread(_store().log, "asked", "", door="mcp", feature="ask_tutor", question=prompt[:500], **found.detail())
    answer = await _router().ask(sent(found.hits), tier=tier, context=context)
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
    """Mark a lesson finished so next_drill moves on. Also counts today towards the streak, and hands
    back the Explain sentence (explain.say_it_like_this) now that the lesson is done."""
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
    return {"lesson_id": lesson_id, "done": True, "next": bank.next_lesson(progress),
            "explain": {"say_it_like_this": bank.explain_sentence(lesson_id)}}


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------


def is_loopback(address: object) -> bool:
    """Is this the address of this computer talking to itself (loopback)? 127.x.x.x, ::1, or a 127.x.x.x address
    written the IPv6 way (::ffff:127.0.0.1). Anything else, or anything that is not an address, is not."""
    if not isinstance(address, str):
        return False
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    # Older Python releases answer False for ::ffff:127.0.0.1, so look at the IPv4 address inside it.
    return (getattr(ip, "ipv4_mapped", None) or ip).is_loopback


# Headers a tunnel or a proxy adds to say "I am passing this request on for someone else"; so does any header whose
# name starts with X-Forwarded- (X-Forwarded-For carries the address the request first came from).
PASSED_ON = (b"forwarded", b"via", b"x-real-ip")


def passed_on(scope) -> bool:
    """Does this request say a tunnel or a proxy passed it on for someone else?"""
    names = [name.lower() for name, _ in scope.get("headers") or ()]
    return any(name in PASSED_ON or name.startswith(b"x-forwarded-") for name in names)


class LocalCallersOnly:
    """Plain ASGI middleware: the app behind it answers a request only when it was made on this computer.

    Two things must hold. The caller's address, ``scope["client"]``, is this computer's own (loopback): the server
    fills that in from the network connection, so unlike the Host header it is not something the caller writes. And
    the request carries no header saying it was passed on for someone else (:func:`passed_on`). Anyone else gets a
    plain 403 at the door (``/mcp``), and the same "not found" as ever on any other path, without reaching the app.
    A missing or unreadable address is refused too.

    Why the second rule: uvicorn swaps the caller's address for the one in an ``X-Forwarded-For`` header when it
    trusts the sender. By default that is only this computer, but ``FORWARDED_ALLOW_IPS=*`` makes it trust everyone,
    and then another device could type ``X-Forwarded-For: 127.0.0.1`` and look local. A program on this computer
    talking to the door directly never sends such a header, and a tunnel passing on a visitor's request does, so
    refusing the header closes that whatever uvicorn is told to believe.

    What the check cannot see: a tunnel that passes the raw connection along and adds no header (a TCP tunnel). Its
    visitors look like this computer, so docs/SERVER.md says not to put the server behind one.
    """

    def __init__(self, app, door: str = "/mcp"):
        self.app = app
        self.door = door

    async def __call__(self, scope, receive, send):
        client = scope.get("client")
        caller = client[0] if isinstance(client, (tuple, list)) and client else None
        if scope["type"] == "lifespan" or (is_loopback(caller) and not passed_on(scope)):
            return await self.app(scope, receive, send)
        if scope["type"] == "websocket":
            return await send({"type": "websocket.close", "code": 1008})  # 1008: refused by a rule
        path = scope.get("path", "").removeprefix(scope.get("root_path", "").rstrip("/"))
        if path == self.door or path.startswith(self.door + "/"):
            refusal = PlainTextResponse("The MCP door answers only requests made on this computer.\n", status_code=403)
        else:  # a path the server does not have (a browser asking for an icon, say): what everyone gets for it
            refusal = PlainTextResponse("Not Found", status_code=404)
        return await refusal(scope, receive, send)


def http_app(port: int, host: str | None = None) -> Starlette:
    """The MCP server as an ASGI app answering at /mcp, for mounting into the web server (which listens on ``host``)."""
    from mcp.server.transport_security import TransportSecuritySettings

    # The Host header has to name this computer: a defence against DNS rebinding, where a web page open in a browser
    # on this computer points its own name at 127.0.0.1 to reach the door. DRILL_ALLOWED_HOSTS=host:port,host:port
    # adds other names for this computer. The caller writes that header, so it keeps no other device out:
    # LocalCallersOnly does that, from the caller's real address.
    allowed = [f"localhost:{port}", f"127.0.0.1:{port}", f"[::1]:{port}", "localhost", "127.0.0.1"]
    if host and is_loopback(host):  # the server's own address, when it is another of this computer's, such as 127.0.0.2
        allowed.append(f"[{host}]:{port}" if ":" in host else f"{host}:{port}")
    allowed += [h.strip() for h in os.getenv("DRILL_ALLOWED_HOSTS", "").split(",") if h.strip()]
    security = TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=allowed, allowed_origins=[])
    app = server.streamable_http_app(streamable_http_path="/mcp", transport_security=security)
    app.add_middleware(LocalCallersOnly, door="/mcp")
    return app


def main() -> None:
    """``uv run drill-mcp``: stdio transport, for a Claude app's MCP configuration."""
    from dotenv import load_dotenv

    from drill.config import PROJECT_ROOT

    load_dotenv(PROJECT_ROOT / ".env")
    try:
        # Start reading (or building) the lessons' vectors now, in the background, so the first ask_tutor of a
        # session can already use them when they are on disk; waiting for that ask left it with none.
        _retriever()
    except Exception as exc:  # noqa: BLE001 - the tools work without retrieval
        log.warning("retrieval: could not start: %s", exc)
    server.run("stdio")
