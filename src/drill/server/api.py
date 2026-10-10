"""The web door: serves the Daily Drill page from this machine and answers its requests.

    uv run drill-server
    # http://localhost:8787 here; http://<your-mac-name>.local:8787 from a phone on the same Wi-Fi

The page is the same file that is published on claude.ai. There it talks to the
artifact's ``sample`` and ``db`` capabilities; here it talks to these routes, which hand
the work to the model router (Ollama first) and the document store (SQLite). The MCP door
is mounted on the same server at ``/mcp``, so Claude Code can use the tools over HTTP.

Settings: ``DRILL_HOST`` (default 0.0.0.0, so the phone can reach it; use 127.0.0.1 to keep
it to this machine), ``DRILL_PORT`` (default 8787).
"""

from __future__ import annotations

import contextlib
import hashlib
import logging
import os
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from drill.config import PROJECT_ROOT
from drill.server.bank import PAGE, Bank, ensure_built
from drill.server.router import ModelRouter, NoModelAvailable
from drill.server.store import DocStore

log = logging.getLogger("drill.server")

# claude.ai wraps the page in a skeleton like this when it publishes it; serving the same
# wrapper here keeps the page identical (phone viewport, safe areas, hidden elements).
PAGE_HEAD = (
    "<!doctype html><html><head><meta charset=\"utf-8\">"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
    "<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
    "body{margin:0;font:14px system-ui,sans-serif;background:#fafafa}img{max-width:100%}[hidden]{display:none!important}</style>"
    "</head><body>"
)
PAGE_TAIL = "</body></html>"

NO_MODEL = {
    "code": "unavailable",
    "text": "No model is running. Start Ollama (`ollama serve`) or set a hosted model in .env, then try again.",
}


class AskBody(BaseModel):
    """What the page sends: a prompt (or messages), the tier it would like, and whether it wants JSON back."""

    model_config = ConfigDict(populate_by_name=True)

    prompt: str | None = None
    messages: list[dict[str, Any]] | None = None
    tier: str = "default"
    json_mode: bool = Field(False, alias="json")


def user_id(request: Request) -> str:
    """Who is asking. Locally everyone is ``local``; behind a login proxy, a short hash of the identity header."""
    header = os.getenv("DRILL_USER_HEADER", "x-forwarded-email")
    value = request.headers.get(header, "").strip().lower()
    if not value:
        return "local"
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def create_app(
    store: DocStore | None = None,
    router: ModelRouter | None = None,
    bank: Bank | None = None,
    with_mcp: bool = True,
    port: int | None = None,
) -> FastAPI:
    store = store or DocStore()
    bank = bank or Bank.load()
    router = router or ModelRouter.from_env(store)
    port = port or int(os.getenv("DRILL_PORT", "8787"))

    mcp_app = None
    if with_mcp:
        from drill.server import mcp as mcp_door

        mcp_door.configure(store=store, router=router, bank=bank)
        mcp_app = mcp_door.http_app(port)

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if mcp_app is None:
            yield
            return
        from drill.server import mcp as mcp_door

        async with mcp_door.server.session_manager.run():
            yield

    app = FastAPI(title="Daily Drill", lifespan=lifespan)
    app.state.store, app.state.router, app.state.bank = store, router, bank

    # -- the page ------------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    def page() -> str:
        ensure_built()  # a content edit shows up on the next refresh
        return PAGE_HEAD + PAGE.read_text(encoding="utf-8") + PAGE_TAIL

    @app.get("/api/health")
    def health(request: Request) -> dict:
        return {
            "ok": True,
            "ai": router.available,
            "user": user_id(request),
            "models": router.describe(),
            "store": store.kind,
            "lessons": len(bank.lessons),
        }

    @app.get("/api/me")
    def me(request: Request) -> dict:
        return {"id": user_id(request)}

    # -- the tutor -----------------------------------------------------------

    @app.post("/api/ask")
    async def ask(body: AskBody):
        if body.messages is None and not (body.prompt or "").strip():
            raise HTTPException(400, {"code": "bad_request", "text": "Send a prompt or messages."})
        messages: Any = body.messages if body.messages is not None else body.prompt
        if not router.order(body.tier):
            raise HTTPException(503, NO_MODEL)

        if body.json_mode:
            try:
                return {"value": await router.ask_json(messages, body.tier)}
            except NoModelAvailable:
                raise HTTPException(503, NO_MODEL)
            except ValueError as exc:
                raise HTTPException(502, {"code": "bad_reply", "text": str(exc)})

        # Pull the first chunk before answering, so a model that is down turns into a
        # proper error instead of an empty stream.
        chunks = router.stream(messages, body.tier)
        try:
            first = await chunks.__anext__()
        except StopAsyncIteration:
            raise HTTPException(502, {"code": "bad_reply", "text": "The model returned nothing."})
        except NoModelAvailable:
            raise HTTPException(503, NO_MODEL)

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

    # -- documents: progress and the study list ------------------------------

    def _check(path: str) -> str:
        if not path or ".." in path.split("/") or path.startswith("/"):
            raise HTTPException(400, {"code": "bad_request", "text": "Bad document path."})
        return path

    @app.get("/api/docs/{path:path}")
    def get_doc(path: str) -> dict:
        doc = store.get(_check(path))
        return {"exists": doc is not None, "data": doc}

    @app.put("/api/docs/{path:path}")
    def set_doc(path: str, doc: dict[str, Any]) -> dict:
        return {"data": store.set(_check(path), doc)}

    @app.patch("/api/docs/{path:path}")
    def update_doc(path: str, patch: dict[str, Any]) -> dict:
        return {"data": store.update(_check(path), patch)}

    @app.delete("/api/docs/{path:path}")
    def delete_doc(path: str) -> dict:
        store.delete(_check(path))
        return {"ok": True}

    @app.get("/api/collections/{name:path}")
    def list_collection(name: str) -> dict:
        return {"docs": [{"id": doc_id, "data": doc} for doc_id, doc in store.list(_check(name))]}

    # Everything that is not a page or /api route goes to the MCP app, which answers at /mcp.
    if mcp_app is not None:
        app.mount("/", mcp_app)

    return app


def main() -> None:
    """``uv run drill-server``: load .env, build the page if needed, serve."""
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    host = os.getenv("DRILL_HOST", "0.0.0.0")
    port = int(os.getenv("DRILL_PORT", "8787"))
    ensure_built()
    app = create_app(port=port)
    log.info("Daily Drill at http://localhost:%s  (MCP at http://localhost:%s/mcp)", port, port)
    uvicorn.run(app, host=host, port=port, log_level="warning")
