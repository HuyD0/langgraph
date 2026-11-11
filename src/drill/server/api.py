"""The web door: serves the Daily Drill page from this machine and answers its requests.

    uv run drill-server
    # http://localhost:8787, on this computer only (DRILL_HOST=0.0.0.0 lets a phone on the same Wi-Fi in)

The page is the same file that is published on claude.ai. There it talks to the
artifact's ``sample`` and ``db`` capabilities; here it talks to these routes, which hand
the work to the model router (Ollama first) and the document store (SQLite). The MCP door
is mounted on the same server at ``/mcp``, so Claude Code can use the tools over HTTP:
only while the server keeps to this computer (two of the tools run the code they are sent,
and the door has no sign-in), and not in a Databricks App, where every learner is a
different person and the MCP door cannot yet tell them apart.

Settings: ``DRILL_HOST`` (default 127.0.0.1, the address that means "this computer only";
0.0.0.0 means every address this computer has, so a phone on the same network can reach it,
and so can every other device there: see :func:`listen_host`), ``DRILL_PORT`` (default 8787).

In a Databricks App the server listens on every address, because the platform reaches it from
outside; the platform picks the port (``DATABRICKS_APP_PORT``) and signs people in
before they reach us, saying who they are in ``x-forwarded-email``; each request then reads
and writes that person's progress. The header is only believed behind such a login
(:func:`behind_login`), so nobody on the home Wi-Fi can claim to be someone else.
"""

from __future__ import annotations

import asyncio
import contextlib
import datetime
import gzip
import hashlib
import ipaddress
import logging
import os
import re
import time
from typing import Any, AsyncIterator, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.gzip import GZipMiddleware

from drill.config import PROJECT_ROOT
from drill.server.bank import Bank
from drill.server.guard import LimitReached, PersonLimits, is_off_topic, with_rules
from drill.server.router import PAGE_TIERS, ModelRouter, NoModelAvailable, PromptTooLong, estimate_tokens, parse_json, to_messages
from drill.server import activity, team
from drill.server import retrieve
from drill.server.retrieve import Retriever
from drill.server.store import DocStore, open_store

log = logging.getLogger("drill.server")

# claude.ai wraps the page in a skeleton like this when it publishes it; serving the same
# wrapper here keeps the page identical (phone viewport, safe areas, hidden elements).
# ``lang`` tells screen readers how to pronounce the page (WCAG 3.1.1).
PAGE_HEAD = (
    "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
    "<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
    "body{margin:0;font:14px system-ui,sans-serif;background:#fafafa}img{max-width:100%}[hidden]{display:none!important}</style>"
    "</head><body>"
)
PAGE_TAIL = "</body></html>"


def whole_page(page: str) -> str:
    """The page inside its wrapper, with the ``<title>`` and font ``<link>`` lines at the top of
    ``page.html`` moved into the ``<head>`` half, where a browser and a validator expect them.

    page.html keeps those lines itself because the built file in ``dist/`` is opened on its own
    (and claude.ai reads the title from it), so only the served copy is rearranged.
    """
    head_lines, rest = [], page
    while rest.startswith(("<title>", "<link ", "<meta ")):
        line, _, rest = rest.partition("\n")
        head_lines.append(line)
    return PAGE_HEAD.replace("</head>", "".join(head_lines) + "</head>") + rest + PAGE_TAIL


# Cheap protective headers for every answer: the browser must not guess a file's type from
# its bytes, must not tell other sites where a link came from, and no site may frame the page.
SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"content-security-policy", b"frame-ancestors 'none'"),
]


class SecurityHeaders:
    """Plain ASGI middleware adding :data:`SECURITY_HEADERS` to every HTTP response."""

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                message = {**message, "headers": [*message.get("headers", []), *SECURITY_HEADERS]}
            await send(message)

        return await self.app(scope, receive, send_with_headers)

# The biggest request body each route takes, in bytes. A progress document for every lesson
# is well under 1 MB; a tutor request is a lesson's text plus the learner's code.
BODY_LIMITS = {"/api/docs/": 2_000_000, "/api/ask": 400_000, "/api/feedback": 20_000, "/api/board": 8_000}
# The tiers the page may ask for. "complex" starts with the hosted (paid) model, so only the
# server's own features choose it; the page never sends it, and a request that does gets "default".


class BodyLimit:
    """Refuses a request body bigger than its route's limit with 413, before it is read into memory.

    Plain ASGI middleware: a stated ``Content-Length`` that is too big is refused at once, and a
    body sent without one is counted as it arrives.
    """

    def __init__(self, app: Any, limits: dict[str, int]):
        self.app, self.limits = app, limits

    def limit_for(self, path: str) -> int | None:
        return next((n for prefix, n in self.limits.items() if path.startswith(prefix)), None)

    async def __call__(self, scope, receive, send):
        limit = self.limit_for(scope.get("path", "")) if scope["type"] == "http" else None
        if limit is None:
            await self.app(scope, receive, send)
            return
        stated = dict(scope.get("headers") or []).get(b"content-length")
        if stated is not None and stated.isdigit() and int(stated) > limit:
            await self._too_big(send, limit)
            return
        # No length given (or a short one): read the body here, counting, then hand it on.
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                return  # the client went away: nothing to answer
            size += len(message.get("body", b""))
            if size > limit:
                await self._too_big(send, limit)
                return
            chunks.append(message.get("body", b""))
            if not message.get("more_body"):
                break
        body, sent = b"".join(chunks), False

        async def replay():
            nonlocal sent
            if sent:
                return await receive()  # after the body: wait for a disconnect, as usual
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay, send)  # every way out of here returns nothing

    @staticmethod
    async def _too_big(send, limit: int) -> None:
        import json

        detail = {"detail": {"code": "too_large", "text": f"That is too big to save or send: the most is {limit // 1000:,} KB."}}
        payload = json.dumps(detail).encode("utf-8")
        await send({"type": "http.response.start", "status": 413,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(payload)).encode())]})
        await send({"type": "http.response.body", "body": payload})


# What the learner reads when no model could answer, by the router's reason (``NoModelAvailable.reason``).
# The Ollama text only helps someone running the server on their own machine: in an app the
# learner can't start anything or edit .env, so they are told to ask whoever runs it.
NO_MODEL_TEXT = {
    "budget": "The tutor has used today's allowance for everyone. It comes back tomorrow.",
    "upstream": "The tutor's model is not answering right now. Try again in a minute.",
    "none": "No model is running. Start Ollama (`ollama serve`) or set a hosted model in .env, then try again.",
    "none_app": "No tutor model is set up for this app. Ask whoever runs it.",
}


def no_model(reason: str) -> dict:
    """The 503 body for a tutor request no model could answer, in words the learner can act on."""
    if reason == "none" and behind_login():
        reason = "none_app"
    return {"code": "unavailable", "text": NO_MODEL_TEXT.get(reason, NO_MODEL_TEXT["upstream"])}


class ServedBody(BaseModel):
    """A prepared answer the page showed (no model asked): ``trace`` as in /api/ask, and the answer."""

    answer: str = Field(max_length=4000)
    model: str = Field(default="prepared", max_length=100)
    trace: dict = Field(default_factory=dict)


class BlueprintBody(BaseModel):
    """One thing someone did on the Unity Gateway blueprint (``/blueprint.html``), for the activity report.

    ``opened`` the page (``came_from`` says whether from inside Daily Drill or a shared link), ``layer``
    reached a step for the first time in this visit, ``finished`` reached the whole system, ``lesson``
    tapped a lesson link. ``visit`` groups one visit's rows; ``seen`` is how many of the ten layers it had shown.
    The page sends only numbers and ids: the server names the layer from its own copy of the blueprint.
    """

    action: Literal["opened", "layer", "finished", "lesson"]
    visit: str = Field(pattern=r"^[a-z0-9-]{1,40}$")
    step: int = Field(default=0, ge=0, le=11)
    seen: int = Field(default=0, ge=0, le=10)
    lesson: str = Field(default="", max_length=120)
    came_from: Literal["", "drill", "link"] = ""


class FeedbackBody(BaseModel):
    """A person's feedback on one answer: ``request`` is the id the page sent with it."""

    request: str
    name: str = Field(max_length=60)
    value: bool | int | float | str
    rationale: str | None = Field(default=None, max_length=1000)
    source: Literal["human", "code"] = "human"  # code: a signal the page noticed, not something the learner said


class AskBody(BaseModel):
    """What the page sends: a prompt (or messages), the tier it would like, and whether it wants JSON back.

    ``trace`` says what the request is for (feature, lesson_id, step, question, session...),
    so its MLflow trace can be found again; see ``observe.CONTEXT_KEYS``.
    """

    model_config = ConfigDict(populate_by_name=True)

    prompt: str | None = None
    messages: list[dict[str, Any]] | None = None
    tier: str = "default"
    json_mode: bool = Field(False, alias="json")
    trace: dict[str, Any] | None = None


def user_id(request: Request) -> str:
    """Who is asking. Locally everyone is ``local``; behind a login proxy, a short hash of the identity header."""
    header = os.getenv("DRILL_USER_HEADER", "x-forwarded-email")
    value = request.headers.get(header, "").strip().lower()
    if not value:
        return "local"
    return hashlib.sha1(value.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]  # a short id, not a secret


def behind_login() -> bool:
    """Is a login proxy in front of us? Always in a Databricks App; elsewhere only if ``DRILL_TRUST_USER_HEADER=1``."""
    return bool(os.getenv("DATABRICKS_APP_NAME", "").strip()) or os.getenv("DRILL_TRUST_USER_HEADER", "") == "1"


def listen_host() -> str:
    """The address the server listens on: ``DRILL_HOST`` if set; else 0.0.0.0 (every address this computer has) in
    a Databricks App, where the platform reaches the server from outside and signs people in first; else 127.0.0.1,
    the address only this computer can reach."""
    chosen = os.getenv("DRILL_HOST", "").strip()
    if chosen:
        return chosen
    return "0.0.0.0" if os.getenv("DATABRICKS_APP_PORT", "").strip() else "127.0.0.1"  # noqa: S104  # nosec B104 - only in the app, behind its sign-in


def this_computer_only(host: str) -> bool:
    """Does listening on ``host`` keep the server to this computer? Yes for a loopback address (127.x.x.x or ::1:
    it never leaves the computer) and the name ``localhost``; no for anything else, or anything unreadable."""
    host = host.strip().lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def page_address(host: str, port: int) -> str:
    """What to type into a browser on this computer to open the page, when the server listens on ``host``: the
    address itself, or ``localhost`` (``[::1]`` the IPv6 way) when it listens on every address, which is not one a
    browser can open."""
    host = host.strip()
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return f"http://{host}:{port}"  # a name, such as localhost
    if ip.version == 6:
        return f"http://[{'::1' if ip.is_unspecified else host}]:{port}"
    return f"http://{'localhost' if ip.is_unspecified or host == '127.0.0.1' else host}:{port}"


def blueprint_layer_names(source: str) -> list[str]:
    """The blueprint's step names in order (``name: '...'`` in its LAYERS list): Start, the ten layers, the whole system."""
    return re.findall(r"\{ slug: '[a-z]+',[^{}]*?\bname: '([^']+)'", source or "")


def owner_for(request: Request, default: str) -> str:
    """Whose rows this request reads and writes: the signed-in person behind a login, else ``default``."""
    if not behind_login():
        return default
    value = request.headers.get(os.getenv("DRILL_USER_HEADER", "x-forwarded-email"), "").strip().lower()
    return value or default


BOARD_DAYS = 15  # rows older than this are last week's at best: the board never needs them
# What a row may hold. Everyone's page draws everyone's row, so each part must be the kind the
# page itself saves (boardRow in page/board.js); tests/test_board.py keeps these in step with the page.
BOARD_COUNTS = ("days", "asked", "spark", "lessons", "reviews")  # a week's other counts, beside its points and its tally of three
BOARD_MAX = 1_000_000  # far more than a week can hold, and small enough that the number still fits in its place on the board
BOARD_GRADES = 5  # a grade is a place in the page's GRADES: 0 to 4
BOARD_MARKS = ("sign", "knot", "curtain")  # the page's MARKS
BOARD_TRIAL = 3  # the daily trial's questions (TRIAL_QS)


def board_id(owner: str) -> str:
    """The id a leaderboard row goes by: a short hash, so nobody's email reaches anyone else's page."""
    return hashlib.sha1(owner.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]  # a short id, not a secret


def board_name(owner: str) -> str:
    """The name shown on the board: ``DRILL_BOARD_NAME``, else the work email's first part ("sam.kim" is Sam Kim)."""
    named = os.getenv("DRILL_BOARD_NAME", "").strip()
    if named:
        return named[:200]
    words = [w for w in owner.split("@", 1)[0].replace("_", ".").replace("-", ".").split(".") if w]
    return " ".join(w.capitalize() for w in words)[:200] or "Someone"


def _board_count(value: Any, what: str, most: int = BOARD_MAX) -> int:
    """A whole number from 0 to ``most``, else ``ValueError``. True, NaN, Infinity and text are not one."""
    whole = isinstance(value, int) or (isinstance(value, float) and value.is_integer())  # NaN and Infinity are never whole
    if isinstance(value, bool) or not whole or not 0 <= value <= most:
        raise ValueError(f"In a leaderboard row, {what} must be a whole number from 0 to {most:,}.")
    return int(value)


def _board_date(value: Any, what: str) -> str:
    """A real day written YYYY-MM-DD, else ``ValueError``. The year is 1000 or later, the same
    as the page's own check (``boardDate``), so the two refuse the same dates."""
    wrong = ValueError(f"In a leaderboard row, {what} must be a real day written like 2026-10-19.")
    if not (isinstance(value, str) and re.fullmatch(r"[1-9][0-9]{3}-[0-9]{2}-[0-9]{2}", value)):
        raise wrong
    try:
        datetime.date.fromisoformat(value)  # the shape is right, but is it a real day? (2026-02-30 is not)
    except ValueError:
        raise wrong from None
    return value


def _board_week(week: Any, whose: str, missing: str) -> dict[str, Any]:
    """One week of a row (this week's or last week's), rebuilt from the parts the page saves.
    ``missing`` is what to say when it is not a week at all (not an object, or one with no points)."""
    if not isinstance(week, dict) or "pts" not in week:
        raise ValueError(missing)
    tally = week.get("tally")
    if not isinstance(tally, list) or len(tally) != 3:
        raise ValueError(f"In a leaderboard row, {whose} tally must be three whole numbers.")
    out: dict[str, Any] = {"week": _board_date(week.get("week"), f"{whose} date"), "pts": _board_count(week["pts"], f"{whose} pts"),
                           "tally": [_board_count(n, f"{whose} tally") for n in tally]}
    out.update({k: _board_count(week[k], f"{whose} {k}") for k in BOARD_COUNTS if k in week})
    return out


def board_checked(row: Any) -> dict[str, Any]:
    """A leaderboard row rebuilt from the parts the page saves, each one checked; anything else is dropped.

    Everyone's page draws everyone's row, so a part of the wrong kind (text where a count goes, a
    grade that does not exist, a mark the page does not know) is a ``ValueError`` that says which.
    Only this week's date, points and tally must be there; the rest may be left out.
    """
    if not isinstance(row, dict):
        raise ValueError("A leaderboard row needs this week's points.")
    out: dict[str, Any] = {}
    if "v" in row:
        out["v"] = _board_count(row["v"], "v")
    out["week"] = _board_week(row.get("week"), "this week's", "A leaderboard row needs this week's points.")
    if "last" in row:  # last week may be left out, so its message never says the row "needs" it
        out["last"] = None if row["last"] is None else _board_week(
            row["last"], "last week's", "In a leaderboard row, last week must be null, left out, or hold its date, points and tally.")
    if "grade" in row:
        out["grade"] = None if row["grade"] is None else _board_count(row["grade"], "the grade", BOARD_GRADES - 1)
    if "trial" in row:
        trial = row["trial"]
        if trial is not None:
            marks = trial.get("marks", []) if isinstance(trial, dict) else None
            if not isinstance(marks, list) or len(marks) > BOARD_TRIAL or any(m not in BOARD_MARKS for m in marks):
                raise ValueError(f"In a leaderboard row, the trial must be a date and at most {BOARD_TRIAL} marks, each one of: {', '.join(BOARD_MARKS)}.")
            trial = {"date": _board_date(trial.get("date"), "the trial's date"), "marks": list(marks)}
        out["trial"] = trial
    return out


def board_row(row: dict[str, Any]) -> dict[str, Any]:
    """The leaderboard row the page may save (:func:`board_checked`); one with a part of the wrong kind is refused."""
    try:
        return board_checked(row)
    except ValueError as err:
        raise HTTPException(400, {"code": "bad_request", "text": str(err)}) from None


def board_stored(row: Any) -> dict[str, Any] | None:
    """A row read back from the table, or None when it would be refused today: one saved before
    rows were checked, or written to the table by hand, must never reach anyone's page."""
    try:
        return board_checked(row)
    except ValueError:
        return None


class IdleStop:
    """Stops this Databricks App after ``minutes`` with no requests, so it stops billing.

    An app can't scale to zero (it bills about 0.5 DBU an hour while running, whether anyone
    is studying or not), so the next best thing is to switch itself off. Progress is in
    Lakebase, so nothing is lost; ``drill cloud start`` brings it back. The app's service
    principal needs CAN_MANAGE on the app, which ``drill cloud deploy`` grants.
    """

    def __init__(self, name: str, minutes: float, stop: Any = None, clock: Any = None):
        import time

        self.name, self.seconds = name, minutes * 60
        self.clock = clock or time.monotonic
        self.last = self.clock()
        self._stop = stop

    @classmethod
    def from_env(cls) -> "IdleStop | None":
        name = os.getenv("DATABRICKS_APP_NAME", "").strip()
        minutes = float(os.getenv("DRILL_IDLE_STOP_MINUTES", "0") or 0)
        return cls(name, minutes) if name and minutes > 0 else None

    def seen(self) -> None:
        self.last = self.clock()

    def check(self) -> bool:
        """Stop the app if it has been idle long enough; True when it asked to stop."""
        if self.clock() - self.last < self.seconds:
            return False
        log.info("No requests for %.0f minutes: stopping %s to save money", self.seconds / 60, self.name)
        try:
            if self._stop:
                self._stop(self.name)
            else:
                from databricks.sdk import WorkspaceClient

                WorkspaceClient().apps.stop(self.name)  # returns once asked; the platform does the rest
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not stop the app (%s); does its service principal have CAN_MANAGE on it?", exc)
            self.last = self.clock()  # try again after another quiet spell, not every minute
            return False
        return True


def create_app(
    store: DocStore | None = None,
    router: ModelRouter | None = None,
    bank: Bank | None = None,
    with_mcp: bool = True,
    port: int | None = None,
    retriever: Retriever | None = None,
    host: str | None = None,
) -> FastAPI:
    store = store or open_store()
    bank = bank or Bank.load()
    router = router or ModelRouter.from_env(store)
    # Finding the right lesson for a question that comes with none (drill.server.retrieve).
    retriever = retriever or Retriever.from_env(bank.data)
    port = port or int(os.getenv("DRILL_PORT", "8787"))
    limits = PersonLimits.from_env(shared=behind_login())  # each person's share, where people share one allowance

    mcp_app = None
    # In a Databricks App every learner is a different person and the MCP door cannot yet tell them apart: no /mcp there.
    # And none when the server listens beyond this computer: the door has no sign-in and two of its tools run the code
    # they are sent. Without an address from the caller we work it out as main() does, so DRILL_HOST=0.0.0.0 leaves
    # /mcp out whoever builds the app.
    host = host or listen_host()
    if with_mcp and not behind_login() and this_computer_only(host):
        from drill.server import mcp as mcp_door

        mcp_door.configure(store=store, router=router, bank=bank, retriever=retriever)
        mcp_app = mcp_door.http_app(port, host)

    idle = IdleStop.from_env()

    async def watch_idle() -> None:
        while True:
            await asyncio.sleep(60)
            if idle.check():
                return

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        watcher = asyncio.create_task(watch_idle()) if idle else None
        retriever.start()  # embeds the lessons on a background thread (or reads them back): start-up never waits
        notes = None
        if team.enabled(store):  # the manager's view: lessons table, managers' read access, weekly notes
            team.prepare(store, bank)
            notes = asyncio.create_task(team.keep_summaries(store, router, bank))
        try:
            if mcp_app is None:
                yield
            else:
                from drill.server import mcp as mcp_door

                async with mcp_door.server.session_manager.run():
                    yield
        finally:
            for task in (watcher, notes):
                if task:
                    task.cancel()
            if hasattr(router.observer, "flush_signals"):  # held quiet signals are written before the app stops
                router.observer.flush_signals()

    app = FastAPI(title="Daily Drill", lifespan=lifespan)
    app.state.store, app.state.router, app.state.bank, app.state.retriever = store, router, bank, retriever
    app.add_middleware(BodyLimit, limits=BODY_LIMITS)
    # The page is 2.4 MB of very compressible text: gzip makes it 6-8 times smaller on the wire.
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(SecurityHeaders)  # outermost, so even a 413 from BodyLimit carries the headers

    if idle:
        @app.middleware("http")
        async def note_activity(request: Request, call_next):
            idle.seen()
            return await call_next(request)

    def mine(request: Request) -> DocStore:
        """The store as whoever is asking: the signed-in person in an app, ``store.owner`` elsewhere."""
        return store.for_owner(owner_for(request, store.owner))

    # -- the page ------------------------------------------------------------

    # Rendered once. The ETag names this exact text, so a reload only downloads the page again
    # when the content or the wrapper changed; ``no-cache`` means "ask first", not "never keep".
    served = whole_page(bank.page)
    etag = '"' + hashlib.sha1(served.encode("utf-8"), usedforsecurity=False).hexdigest() + '"'  # a cache tag, not a secret
    # Compressed once, here: compressing 5 MB for every visitor was most of the server's work when a
    # whole team arrived at once (the load test). GZipMiddleware leaves an encoded answer alone.
    served_gz = gzip.compress(served.encode("utf-8"), 6)

    @app.get("/")
    def page(request: Request) -> Response:
        headers = {"ETag": etag, "Cache-Control": "no-cache"}
        offered = [t.strip().removeprefix("W/") for t in request.headers.get("if-none-match", "").split(",")]
        if etag in offered or "*" in offered:
            return Response(status_code=304, headers=headers)
        if "gzip" in request.headers.get("accept-encoding", ""):
            return Response(served_gz, media_type="text/html; charset=utf-8",
                            headers={**headers, "Content-Encoding": "gzip", "Vary": "Accept-Encoding"})
        return HTMLResponse(served, headers=headers)

    # The Unity Gateway blueprint: a second page, served the same way (rendered once, ETag, gzip).
    served_bp = whole_page(bank.blueprint)
    etag_bp = '"' + hashlib.sha1(served_bp.encode("utf-8"), usedforsecurity=False).hexdigest() + '"'  # a cache tag, not a secret
    served_bp_gz = gzip.compress(served_bp.encode("utf-8"), 6)

    @app.get("/blueprint.html")
    def blueprint(request: Request) -> Response:
        headers = {"ETag": etag_bp, "Cache-Control": "no-cache"}
        offered = [t.strip().removeprefix("W/") for t in request.headers.get("if-none-match", "").split(",")]
        if etag_bp in offered or "*" in offered:
            return Response(status_code=304, headers=headers)
        if "gzip" in request.headers.get("accept-encoding", ""):
            return Response(served_bp_gz, media_type="text/html; charset=utf-8",
                            headers={**headers, "Content-Encoding": "gzip", "Vary": "Accept-Encoding"})
        return HTMLResponse(served_bp, headers=headers)

    # The blueprint's steps by number (0 Start, 1 to 10 the layers, 11 the whole system), read from the page this
    # server sends, so a report shows the names the page showed and never words a browser made up.
    bp_layers = blueprint_layer_names(bank.blueprint)

    @app.post("/api/blueprint")
    async def blueprint_activity(body: BlueprintBody, request: Request) -> dict:
        """Record one blueprint action as an event (kinds ``blueprint_opened``, ``_layer``, ``_finished``, ``_lesson``)."""
        detail: dict[str, Any] = {"visit": body.visit}
        lesson_id = ""
        if body.action == "opened":
            detail.update(step=body.step, came_from=body.came_from or "link")
        elif body.action == "layer":
            detail.update(step=body.step, layer=bp_layers[body.step] if body.step < len(bp_layers) else "", seen=body.seen)
        elif body.action == "finished":
            detail.update(seen=body.seen)
        else:  # a lesson link: only a lesson this course has, so a made-up id never reaches the report
            if body.lesson not in app.state.bank.lessons:
                return {"ok": False}
            lesson_id = body.lesson
            detail.update(step=body.step, layer=bp_layers[body.step] if body.step < len(bp_layers) else "")
        await asyncio.to_thread(mine(request).log, "blueprint_" + body.action, lesson_id, **detail)
        return {"ok": True}

    @app.get("/pack-assets/{pack_id}/{path:path}")
    def pack_asset(pack_id: str, path: str) -> FileResponse:
        """A screenshot or diagram from a loaded content pack. Only files a lesson names are served."""
        found = bank.pack_asset(pack_id, path)
        if not found:
            raise HTTPException(404, {"code": "not_found", "text": "No such pack file."})
        return FileResponse(found)

    @app.get("/api/health")
    def health(request: Request) -> dict:
        return {
            "ok": True,
            "ai": router.available,
            "user": user_id(request),
            "models": router.describe(),
            "store": store.kind,
            "store_fallback": store.fallback,
            "owner": owner_for(request, store.owner),
            "lessons": len(bank.lessons),
            "retrieval": retriever.describe(),  # finding a lesson for questions that come with none
            "team": team.enabled(store),  # true at work: managers see progress, study lists and questions
            "app": behind_login(),  # behind a login (the Databricks App): the learner can't start a model themselves
        }

    @app.get("/api/me")
    def me(request: Request) -> dict:
        return {"id": user_id(request)}

    # -- the tutor -----------------------------------------------------------

    @app.post("/api/ask", response_model=None)  # the return type names a Response, which is not a schema
    async def ask(body: AskBody, request: Request) -> StreamingResponse | dict:
        if body.messages is None and not (body.prompt or "").strip():
            raise HTTPException(400, {"code": "bad_request", "text": "Send a prompt or messages."})
        # The server's own rules go first, whatever the page sent (drill.server.guard).
        messages = with_rules(to_messages(body.messages if body.messages is not None else body.prompt))
        tier = body.tier if body.tier in PAGE_TIERS else "default"  # the page can't pick the paid model
        try:
            router.check_size(messages)
        except PromptTooLong as exc:
            raise HTTPException(413, {"code": "too_large", "text": str(exc)})
        docs = mine(request)
        if limits:
            try:
                await asyncio.to_thread(limits.check, docs)
            except LimitReached as exc:
                raise HTTPException(429, {"code": exc.code, "text": exc.text})
        # Store calls go to a worker thread: on Lakebase each is a network round trip, and
        # waiting here would hold up every other request the server is answering.
        if not await asyncio.to_thread(router.order, tier):
            raise HTTPException(503, no_model(router.unavailable_reason()))
        # MLflow's user field: the signed-in email in an app (the same owner Lakebase uses), "local" elsewhere.
        # "retrieval" is the server's own record of what it found, set below and nowhere else: one the page sent
        # is dropped, so a lesson ask or the private use-case helper never carries a retrieval record.
        trace = body.trace or {}
        context = {**{k: v for k, v in trace.items() if k != "retrieval"}, "door": "page", "user": owner_for(request, "local")}
        detail = {k: trace[k] for k in ("feature", "step", "hint_level", "chip") if trace.get(k) is not None}
        if trace.get("question"):  # what they asked, for the manager's view (drill.server.team)
            detail["question"] = str(trace["question"])[:500]
        lesson_id = str(trace.get("lesson_id") or "")
        if retrieve.applies(str(trace.get("feature") or ""), lesson_id):
            # No lesson came with it: find the paragraphs that fit, and put them where a lesson page puts its lesson.
            # A lesson the page sent is never replaced, and the use-case helper never gets here (it is private).
            messages, found = await find_for(messages, str(trace.get("question") or ""))
            detail.update(found.detail())
            context["retrieval"] = found.trace()
        await asyncio.to_thread(docs.log, "asked", lesson_id, **detail)

        async def answered(text: str, cached: bool) -> None:
            """Count a fresh answer against the person's day, and note an off-topic request."""
            if limits and not cached:
                await asyncio.to_thread(limits.spend, docs, estimate_tokens(messages, text)["total_tokens"])
            if is_off_topic(text):
                await asyncio.to_thread(docs.log, "off_topic", lesson_id, **detail)

        if body.json_mode:
            try:
                answer = await router.ask(messages, tier, json_mode=True, context=context)
                await answered(answer.text, answer.cached)
                return {"value": parse_json(answer.text)}
            except NoModelAvailable as exc:
                raise HTTPException(503, no_model(exc.reason))
            except ValueError as exc:
                raise HTTPException(502, {"code": "bad_reply", "text": str(exc)})

        # Pull the first chunk before answering, so a model that is down turns into a
        # proper error instead of an empty stream.
        chunks = router.stream(messages, tier, context=context)
        try:
            first = await chunks.__anext__()
        except StopAsyncIteration:
            raise HTTPException(502, {"code": "bad_reply", "text": "The model returned nothing."})
        except NoModelAvailable as exc:
            raise HTTPException(503, no_model(exc.reason))

        async def deltas() -> AsyncIterator[str]:
            sent = ""
            chunk = first
            while True:
                if chunk.text.startswith(sent):
                    delta, sent = chunk.text[len(sent):], chunk.text
                    if delta:
                        yield delta
                if chunk.done:
                    await answered(chunk.text, chunk.cached)
                    break
                try:
                    chunk = await chunks.__anext__()
                except StopAsyncIteration:
                    break

        return StreamingResponse(
            deltas(),
            media_type="text/plain; charset=utf-8",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    async def find_for(messages: list, question: str) -> tuple[list, "retrieve.Found"]:
        """The messages with what retrieval found added, and what it found. Fewer paragraphs when the
        prompt would go over the size limit; none, and the messages as they came, on any failure."""
        found = await retriever.search(question)

        def fits(hits: list[dict]) -> bool:
            try:
                router.check_size(retrieve.with_found(messages, hits))
                return True
            except PromptTooLong:
                return False

        retrieve.fit(found, fits)  # the messages on their own were checked before this (the 413 above)
        return retrieve.with_found(messages, found.hits), found

    @app.post("/api/served")
    async def served_answer(body: ServedBody, request: Request) -> dict:
        from drill.server.observe import default_observer

        trace = {**body.trace, "door": "page", "user": owner_for(request, "local")}
        # logged like a live answer's question, so the manager's view counts it the same way
        detail = {k: body.trace[k] for k in ("feature", "step", "chip") if body.trace.get(k) is not None}
        if body.trace.get("question"):
            detail["question"] = str(body.trace["question"])[:500]
        await asyncio.to_thread(mine(request).log, "asked", str(body.trace.get("lesson_id") or ""), prepared=True, **detail)
        observer = router.observer if hasattr(router.observer, "served") else default_observer()
        logged = bool(observer and await asyncio.to_thread(observer.served, trace, body.answer, body.model))
        return {"ok": True, "logged": logged}

    @app.post("/api/feedback")
    async def feedback(body: FeedbackBody, request: Request) -> dict:
        from drill.server.observe import default_observer

        user = owner_for(request, "local")
        await asyncio.to_thread(mine(request).log, "feedback", "", name=body.name, value=str(body.value)[:60], request=body.request)
        # The router's own observer: the one that wrote the trace this feedback is about.
        observer = router.observer if hasattr(router.observer, "human_feedback") else default_observer()
        logged = bool(observer and observer.human_feedback(body.request, body.name, body.value, body.rationale, user, signal=body.source == "code"))
        return {"ok": True, "logged": logged}

    # -- documents: progress and the study list ------------------------------

    def _check(path: str) -> str:
        if not path or ".." in path.split("/") or path.startswith("/"):
            raise HTTPException(400, {"code": "bad_request", "text": "Bad document path."})
        return path

    @app.get("/api/docs/{path:path}")
    def get_doc(path: str, request: Request) -> dict:
        doc = mine(request).get(_check(path))
        return {"exists": doc is not None, "data": doc}

    def _log_progress(docs, before: dict | None, after: dict) -> None:
        for kind, lesson_id, detail in activity.progress_events(before, after):
            lesson = app.state.bank.lessons.get(lesson_id) if kind == "checked" else None
            if lesson and isinstance(detail.get("answer"), int):
                # the page shows Check options shuffled, so letters mean nothing later: keep the words
                options, right = lesson["check"][1], lesson["check"][2]
                if 0 <= detail["answer"] < len(options):
                    detail = {**detail, "picked": options[detail["answer"]], "right": options[right]}
            docs.log(kind, lesson_id, **detail)

    @app.put("/api/docs/{path:path}")
    def set_doc(path: str, doc: dict[str, Any], request: Request) -> dict:
        path, docs = _check(path), mine(request)
        before = docs.get(path) if activity.is_progress(path) else None
        saved = docs.set(path, doc)
        if activity.is_progress(path):
            _log_progress(docs, before, saved)
        return {"data": saved}

    @app.patch("/api/docs/{path:path}")
    def update_doc(path: str, patch: dict[str, Any], request: Request) -> dict:
        path, docs = _check(path), mine(request)
        before = docs.get(path) if activity.is_progress(path) else None
        saved = docs.update(path, patch)
        if activity.is_progress(path):
            _log_progress(docs, before, saved)
        return {"data": saved}

    @app.delete("/api/docs/{path:path}")
    def delete_doc(path: str, request: Request) -> dict:
        mine(request).delete(_check(path))
        return {"ok": True}

    # -- the leaderboard (page/board.js): everyone who joined reads every row; each writes their own --

    @app.get("/api/board")
    def get_board(request: Request) -> dict:
        me = owner_for(request, store.owner)
        rows = store.board_rows(since=time.time() - BOARD_DAYS * 86400)
        # Checked again on the way out, and a row that fails is left out: one bad row must not break the board for everyone.
        shown = [(r, board_stored(r["row"])) for r in rows]
        return {"me": board_id(me), "rows": [{"id": board_id(r["owner"]), "name": r["name"], "row": row} for r, row in shown if row is not None]}

    @app.put("/api/board")
    def put_board(row: dict[str, Any], request: Request) -> dict:
        docs = mine(request)
        docs.board_set(board_name(docs.owner), board_row(row))
        return {"ok": True}

    @app.delete("/api/board")
    def leave_board(request: Request) -> dict:
        mine(request).board_leave()
        return {"ok": True}

    @app.get("/api/collections/{name:path}")
    def list_collection(name: str, request: Request) -> dict:
        return {"docs": [{"id": doc_id, "data": doc} for doc_id, doc in mine(request).list(_check(name))]}

    # Everything that is not a page or /api route goes to the MCP app, which answers at /mcp.
    if mcp_app is not None:
        app.mount("/", mcp_app)

    return app


def main() -> None:
    """``uv run drill-server``: load .env, build the page, serve."""
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    # The server keeps to this computer unless DRILL_HOST says otherwise.
    # A Databricks App must listen on every address, on the port the platform gives it.
    in_app = os.getenv("DATABRICKS_APP_PORT", "").strip()
    host = listen_host()
    port = int(os.getenv("DRILL_PORT", "").strip() or in_app or "8787")
    app = create_app(port=port, host=host)
    here = page_address(host, port)
    if behind_login():
        log.info("Daily Drill at http://localhost:%s  (behind a login: no MCP door)", port)
    elif this_computer_only(host):
        log.info("Daily Drill at %s  (this computer only; MCP at %s/mcp)", here, here)
    else:
        log.warning("Daily Drill at %s on this computer. It is listening on %s, so every device on the same network "
                    "can open it too, with no sign-in. The MCP door at /mcp is left out; drill-mcp still works on "
                    "this computer.", here, host)
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
