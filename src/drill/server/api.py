"""The web door: serves the Daily Drill page from this machine and answers its requests.

    uv run drill-server
    # http://localhost:8787 here; http://<your-mac-name>.local:8787 from a phone on the same Wi-Fi

The page is the same file that is published on claude.ai. There it talks to the
artifact's ``sample`` and ``db`` capabilities; here it talks to these routes, which hand
the work to the model router (Ollama first) and the document store (SQLite). The MCP door
is mounted on the same server at ``/mcp``, so Claude Code can use the tools over HTTP;
not in a Databricks App, where every learner is a different person and the MCP door
cannot yet tell them apart.

Settings: ``DRILL_HOST`` (default 0.0.0.0, so the phone can reach it; use 127.0.0.1 to keep
it to this machine, which is the default when the store is Lakebase), ``DRILL_PORT`` (default 8787).

In a Databricks App the platform picks the port (``DATABRICKS_APP_PORT``) and signs people in
before they reach us, saying who they are in ``x-forwarded-email``; each request then reads
and writes that person's progress. The header is only believed behind such a login
(:func:`behind_login`), so nobody on the home Wi-Fi can claim to be someone else.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import os
from typing import Any, AsyncIterator, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.gzip import GZipMiddleware

from drill.config import PROJECT_ROOT
from drill.server.bank import Bank
from drill.server.router import PAGE_TIERS, ModelRouter, NoModelAvailable, PromptTooLong, to_messages
from drill.server import activity, team
from drill.server.store import DocStore, lakebase_endpoint, open_store

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
    while rest.startswith(("<title>", "<link ")):
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
BODY_LIMITS = {"/api/docs/": 2_000_000, "/api/ask": 400_000, "/api/feedback": 20_000}
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
            return await self.app(scope, receive, send)
        stated = dict(scope.get("headers") or []).get(b"content-length")
        if stated is not None and stated.isdigit() and int(stated) > limit:
            return await self._too_big(send, limit)
        # No length given (or a short one): read the body here, counting, then hand it on.
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                return  # the client went away: nothing to answer
            size += len(message.get("body", b""))
            if size > limit:
                return await self._too_big(send, limit)
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

        return await self.app(scope, replay, send)

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
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def behind_login() -> bool:
    """Is a login proxy in front of us? Always in a Databricks App; elsewhere only if ``DRILL_TRUST_USER_HEADER=1``."""
    return bool(os.getenv("DATABRICKS_APP_NAME", "").strip()) or os.getenv("DRILL_TRUST_USER_HEADER", "") == "1"


def owner_for(request: Request, default: str) -> str:
    """Whose rows this request reads and writes: the signed-in person behind a login, else ``default``."""
    if not behind_login():
        return default
    value = request.headers.get(os.getenv("DRILL_USER_HEADER", "x-forwarded-email"), "").strip().lower()
    return value or default


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
) -> FastAPI:
    store = store or open_store()
    bank = bank or Bank.load()
    router = router or ModelRouter.from_env(store)
    port = port or int(os.getenv("DRILL_PORT", "8787"))

    mcp_app = None
    # In a Databricks App every learner is a different person and the MCP door cannot yet tell them apart: no /mcp there.
    if with_mcp and not behind_login():
        from drill.server import mcp as mcp_door

        mcp_door.configure(store=store, router=router, bank=bank)
        mcp_app = mcp_door.http_app(port)

    idle = IdleStop.from_env()

    async def watch_idle() -> None:
        while True:
            await asyncio.sleep(60)
            if idle.check():
                return

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        watcher = asyncio.create_task(watch_idle()) if idle else None
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
    app.state.store, app.state.router, app.state.bank = store, router, bank
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
    etag = '"' + hashlib.sha1(served.encode("utf-8")).hexdigest() + '"'

    @app.get("/")
    def page(request: Request) -> Response:
        headers = {"ETag": etag, "Cache-Control": "no-cache"}
        offered = [t.strip().removeprefix("W/") for t in request.headers.get("if-none-match", "").split(",")]
        if etag in offered or "*" in offered:
            return Response(status_code=304, headers=headers)
        return HTMLResponse(served, headers=headers)

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
        messages: Any = body.messages if body.messages is not None else body.prompt
        tier = body.tier if body.tier in PAGE_TIERS else "default"  # the page can't pick the paid model
        try:
            router.check_size(to_messages(messages))
        except PromptTooLong as exc:
            raise HTTPException(413, {"code": "too_large", "text": str(exc)})
        # Store calls go to a worker thread: on Lakebase each is a network round trip, and
        # waiting here would hold up every other request the server is answering.
        if not await asyncio.to_thread(router.order, tier):
            raise HTTPException(503, no_model(router.unavailable_reason()))
        # MLflow's user field: the signed-in email in an app (the same owner Lakebase uses), "local" elsewhere.
        context = {**(body.trace or {}), "door": "page", "user": owner_for(request, "local")}
        trace = body.trace or {}
        detail = {k: trace[k] for k in ("feature", "step", "hint_level", "chip") if trace.get(k) is not None}
        if trace.get("question"):  # what they asked, for the manager's view (drill.server.team)
            detail["question"] = str(trace["question"])[:500]
        await asyncio.to_thread(mine(request).log, "asked", str(trace.get("lesson_id") or ""), **detail)

        if body.json_mode:
            try:
                return {"value": await router.ask_json(messages, tier, context=context)}
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
    # A work laptop on Lakebase keeps the server to itself; at home the phone may reach it.
    # A Databricks App must listen on every address, on the port the platform gives it.
    in_app = os.getenv("DATABRICKS_APP_PORT", "").strip()
    host = os.getenv("DRILL_HOST", "").strip() or ("0.0.0.0" if in_app or not lakebase_endpoint() else "127.0.0.1")
    port = int(os.getenv("DRILL_PORT", "").strip() or in_app or "8787")
    app = create_app(port=port)
    if behind_login():
        log.info("Daily Drill at http://localhost:%s  (behind a login: no MCP door)", port)
    else:
        log.info("Daily Drill at http://localhost:%s  (MCP at http://localhost:%s/mcp)", port, port)
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
