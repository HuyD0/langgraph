"""Decides which model answers, and keeps the hosted one cheap.

Local first. Ollama on this Mac answers everything it can, for free. A hosted model -
your Azure deployment, or any OpenAI-compatible endpoint such as a Databricks serving
endpoint - is used when a "complex" job asks for it, or when Ollama is not running, and
only while today's hosted usage is under a budget.

Both are LangChain chat models, so nothing else in the server knows or cares which one
answered. Every answer is also cached by its exact prompt: the same hint for the same
code costs nothing the second time. And every answer is measured (see ``observe``):
who answered, how long until the first word, how many tokens.

Configuration (all optional, all in .env):

    OLLAMA_MODEL=gemma3:12b             the local model; unset picks one Ollama has pulled
    OLLAMA_BASE_URL=http://localhost:11434/v1
    DRILL_THINKING=complex              off | complex | on: when a thinking model may think
    DRILL_FIRST_WORD_SECONDS=45         give up on a model that has not started by then
    DRILL_HOSTED_BASE_URL=https://adb-123.azuredatabricks.net/serving-endpoints
    DRILL_HOSTED_MODEL=databricks-gemma-3-12b     the endpoint (or model) name
    DRILL_HOSTED_API_KEY=...                      a Databricks token, or the provider's key
    DRILL_HOSTED_DAILY_TOKENS=200000              stop using the hosted model past this
    DRILL_TRACING=1                               0 switches MLflow tracing off

With no DRILL_HOSTED_* set, the Azure settings from drill.config are the hosted model.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Iterable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from drill.config import LLMSettings
from drill.server.store import DocStore

log = logging.getLogger("drill.server")

# Variables that describe a *local* model. They are hidden from the hosted settings so
# that a .env which says OLLAMA_MODEL=... still yields the Azure model as the fallback.
LOCAL_ONLY_VARS = ("OLLAMA_MODEL", "OLLAMA_BASE_URL", "MLFLOW_GATEWAY_ENDPOINT", "MLFLOW_GATEWAY_URL")

# Models that think before answering. Thinking makes a hint take 5-20 seconds instead of
# one, so it is only allowed where DRILL_THINKING says. Through Ollama's OpenAI-style
# endpoint the switch that actually works is ``reasoning_effort: "none"`` (``think: false``
# and ``/no_think`` are ignored there). Any thinking that still leaks out as
# ``<think>...</think>`` text is hidden.
_THINKING_MODELS = ("qwen3", "deepseek-r1", "gpt-oss", "magistral")
_THINK_BLOCK = re.compile(r"<think>.*?</think>\s*", re.S)
THINKING_POLICIES = ("off", "complex", "on")


class NoModelAvailable(RuntimeError):
    """Neither a local nor a hosted model could answer."""


@dataclass
class Route:
    """One way to get an answer: a name for the logs, a model name, and a chat model."""

    name: str  # "local" or "hosted"
    model: str
    chat: Any  # a LangChain chat model: anything with .astream(messages)


@dataclass
class Chunk:
    """One step of a streamed answer. ``text`` is the whole answer so far, not a delta."""

    text: str
    done: bool = False
    route: str = ""
    model: str = ""
    cached: bool = False


@dataclass
class Answer:
    text: str
    route: str
    model: str
    cached: bool = False


class _NullObserver:
    def start(self, messages: list, tier: str) -> dict:
        return {}

    def first_word(self, handle: dict) -> None:
        pass

    def finish(self, handle: dict, **fields: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Finding the models
# ---------------------------------------------------------------------------


def ollama_models(base_url: str, timeout: float = 1.5) -> list[str]:
    """The models Ollama has pulled, or ``[]`` when Ollama is not running."""
    import httpx

    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        root = root[: -len("/v1")]
    try:
        response = httpx.get(root + "/api/tags", timeout=timeout)
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]
    except Exception:
        return []


def is_thinking_model(model: str) -> bool:
    return model.startswith(_THINKING_MODELS)


def pick_local_model(available: list[str], wanted: str = "") -> str | None:
    """``OLLAMA_MODEL`` if set; otherwise a model that answers without thinking first."""
    if wanted:
        return wanted
    if not available:
        return None
    for name in available:
        if not is_thinking_model(name):
            return name
    return available[0]


def local_route() -> Route | None:
    """Ollama on this machine, or ``None`` when it is not running."""
    base = os.getenv("OLLAMA_BASE_URL", "").strip() or "http://localhost:11434/v1"
    available = ollama_models(base)
    if not available:
        return None
    model = pick_local_model(available, os.getenv("OLLAMA_MODEL", "").strip())
    if model not in available:
        log.warning("OLLAMA_MODEL=%s is not pulled; Ollama has %s", model, ", ".join(available))
    from langchain_openai import ChatOpenAI

    # Ollama speaks the OpenAI chat API and ignores the key, but the client insists on one.
    # stream_usage asks for real token counts at the end of each streamed answer.
    chat = ChatOpenAI(
        base_url=base, model=model, api_key="local", temperature=0.3, timeout=120, max_retries=0, stream_usage=True
    )
    return Route("local", model, chat)


def hosted_route() -> Route | None:
    """``DRILL_HOSTED_*`` (any OpenAI-compatible endpoint) first, else the Azure settings."""
    base = os.getenv("DRILL_HOSTED_BASE_URL", "").strip()
    model = os.getenv("DRILL_HOSTED_MODEL", "").strip()
    if base and model:
        from langchain_openai import ChatOpenAI

        key = os.getenv("DRILL_HOSTED_API_KEY", "").strip() or "none"
        chat = ChatOpenAI(base_url=base, model=model, api_key=key, timeout=120, max_retries=1, stream_usage=True)
        return Route("hosted", model, chat)

    env = {k: v for k, v in os.environ.items() if k not in LOCAL_ONLY_VARS}
    settings = LLMSettings.from_env(env)
    if settings.is_configured and not settings.is_local:
        from drill.llm import build_chat_model

        return Route("hosted", settings.deployment or "azure", build_chat_model(settings))
    return None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def to_messages(prompt_or_messages: str | Iterable[Any]) -> list[BaseMessage]:
    """Accept a plain prompt, ``{"role", "content"}`` dicts, or LangChain messages."""
    if isinstance(prompt_or_messages, str):
        return [HumanMessage(content=prompt_or_messages)]
    out: list[BaseMessage] = []
    for m in prompt_or_messages:
        if isinstance(m, BaseMessage):
            out.append(m)
            continue
        role, content = m.get("role", "user"), str(m.get("content", ""))
        if role == "system":
            out.append(SystemMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
        else:
            out.append(HumanMessage(content=content))
    return out


def chunk_text(chunk: Any) -> str:
    """The text in one streamed message chunk, skipping any reasoning blocks."""
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type", "text") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content or "")


def strip_thinking(raw: str, final: bool = False) -> str:
    """Remove ``<think>...</think>`` blocks; while a block is still open, hide the rest."""
    text = _THINK_BLOCK.sub("", raw)
    open_at = text.find("<think>")
    if open_at != -1:
        text = text[:open_at]
    return text.strip() if final else text.lstrip()


def parse_json(text: str) -> Any:
    """The JSON value in a model's reply, tolerating code fences and a little prose around it."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = text.find(opener), text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("The model did not reply with JSON: " + text[:200])


def estimate_tokens(messages: list[BaseMessage], text: str) -> dict:
    """Roughly four characters per token: the fallback when a model reports no usage."""
    prompt = sum(len(str(m.content)) for m in messages) // 4 + 1
    answer = len(text) // 4 + 1
    return {"input_tokens": prompt, "output_tokens": answer, "total_tokens": prompt + answer}


# ---------------------------------------------------------------------------
# The router
# ---------------------------------------------------------------------------


class ModelRouter:
    """Picks a route for each request, falls back when one fails, caches, counts, and measures."""

    def __init__(
        self,
        local: Route | None = None,
        hosted: Route | None = None,
        store: DocStore | None = None,
        hosted_daily_tokens: int = 200_000,
        first_word_seconds: float = 45.0,
        thinking: str = "complex",
        observer: Any = None,
    ):
        self.local = local
        self.hosted = hosted
        self.store = store
        self.hosted_daily_tokens = hosted_daily_tokens
        # A deadline for the first visible word. A model that is loading, stalled, or
        # thinking out loud for minutes gets cut off here and the next route is tried,
        # instead of holding a hint hostage. Once an answer has started it is never cut.
        self.first_word_seconds = first_word_seconds
        # When a thinking model may think: never, only for "complex" jobs, or always.
        self.thinking = thinking if thinking in THINKING_POLICIES else "complex"
        self.observer = observer or _NullObserver()

    @classmethod
    def from_env(cls, store: DocStore | None = None) -> "ModelRouter":
        budget = int(os.getenv("DRILL_HOSTED_DAILY_TOKENS", "200000") or 200_000)
        first_word = float(os.getenv("DRILL_FIRST_WORD_SECONDS", "45") or 45)
        thinking = os.getenv("DRILL_THINKING", "complex").strip().lower()
        observer = None
        if os.getenv("DRILL_TRACING", "1").strip() not in ("0", "false", "no"):
            from drill.server.observe import MlflowObserver

            observer = MlflowObserver()
        router = cls(local_route(), hosted_route(), store, budget, first_word, thinking, observer)
        log.info(
            "models: local=%s hosted=%s thinking=%s",
            router.local and router.local.model, router.hosted and router.hosted.model, router.thinking,
        )
        return router

    # -- what is available -------------------------------------------------

    @property
    def available(self) -> bool:
        return self.local is not None or self.hosted is not None

    def describe(self) -> dict:
        """For the health check: which models exist, the thinking policy, and budget use."""
        return {
            "local": self.local.model if self.local else None,
            "hosted": self.hosted.model if self.hosted else None,
            "thinking": self.thinking,
            "tracing": not isinstance(self.observer, _NullObserver),
            "hosted_tokens_today": self.hosted_tokens_today(),
            "hosted_daily_tokens": self.hosted_daily_tokens,
        }

    def _usage_path(self) -> str:
        return "usage/" + time.strftime("%Y-%m-%d")

    def hosted_tokens_today(self) -> int:
        if not self.store:
            return 0
        doc = self.store.get(self._usage_path()) or {}
        return int(doc.get("hosted", {}).get("tokens", 0))

    def hosted_under_budget(self) -> bool:
        return self.hosted is not None and self.hosted_tokens_today() < self.hosted_daily_tokens

    def order(self, tier: str = "default") -> list[Route]:
        """Who to try first. Only a "complex" job starts with the hosted model."""
        hosted = self.hosted if self.hosted_under_budget() else None
        if tier == "complex" and hosted is not None:
            routes = [hosted, self.local]
        else:
            routes = [self.local, hosted]
        return [r for r in routes if r is not None]

    def may_think(self, tier: str) -> bool:
        return self.thinking == "on" or (self.thinking == "complex" and tier == "complex")

    # -- asking ------------------------------------------------------------

    def _prepare(self, messages: list[BaseMessage], route: Route, tier: str, json_mode: bool):
        """The messages and model to call for this route: JSON instructions, thinking on or off.

        Returns ``(messages, chat, thinking)`` where ``thinking`` says whether the model was
        left free to think, which is recorded on the trace.
        """
        if json_mode:
            note = "Reply with one JSON object and nothing else: no prose, no code fences."
            if messages and isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=f"{messages[0].content}\n{note}"), *messages[1:]]
            else:
                messages = [SystemMessage(content=note), *messages]
        chat = route.chat
        thinking = is_thinking_model(route.model)
        if thinking and route.name == "local" and not self.may_think(tier):
            chat = chat.bind(extra_body={"reasoning_effort": "none"})
            thinking = False
        return messages, chat, thinking

    def _cache_key(self, messages: list[BaseMessage], tier: str, json_mode: bool) -> str:
        payload = json.dumps([[m.type, str(m.content)] for m in messages]) + f"|{tier}|{json_mode}"
        return "cache/" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:40]

    def _record(self, route: Route, messages: list[BaseMessage], text: str, usage: dict | None) -> dict:
        """Count today's usage for the route, preferring the model's own token report."""
        tokens = estimate_tokens(messages, text)
        if usage and usage.get("total_tokens"):
            tokens = {
                "input_tokens": int(usage.get("input_tokens", 0)),
                "output_tokens": int(usage.get("output_tokens", 0)),
                "total_tokens": int(usage["total_tokens"]),
            }
        if self.store:
            path = self._usage_path()
            doc = self.store.get(path) or {}
            entry = doc.setdefault(route.name, {"calls": 0, "tokens": 0})
            entry["calls"] += 1
            entry["tokens"] += tokens["total_tokens"]
            self.store.set(path, doc)
        return tokens

    async def stream(
        self, prompt_or_messages: str | Iterable[Any], tier: str = "default", json_mode: bool = False
    ) -> AsyncIterator[Chunk]:
        """Yield the answer as it grows; the last chunk has ``done=True`` and says who answered."""
        messages = to_messages(prompt_or_messages)
        handle = self.observer.start(messages, tier)

        key = self._cache_key(messages, tier, json_mode)
        cached = self.store.get(key) if self.store else None
        if cached and cached.get("text"):
            self.observer.first_word(handle)
            self.observer.finish(handle, text=cached["text"], route=cached.get("route", ""), model=cached.get("model", ""), cached=True)
            yield Chunk(cached["text"], done=True, route=cached.get("route", ""), model=cached.get("model", ""), cached=True)
            return

        routes = self.order(tier)
        if not routes:
            self.observer.finish(handle, error="no model available")
            raise NoModelAvailable("No model is running. Start Ollama, or set a hosted model in .env.")

        errors: list[str] = []
        for route in routes:
            prepared, chat, thinking = self._prepare(messages, route, tier, json_mode)
            raw, started, usage, t0 = "", False, None, time.monotonic()
            pieces = chat.astream(prepared)
            try:
                while True:
                    # Until the first visible word, every wait is bounded by the deadline;
                    # thinking tokens keep arriving but do not count as an answer.
                    remaining = self.first_word_seconds - (time.monotonic() - t0)
                    if not started and remaining <= 0:
                        raise TimeoutError(f"no answer after {self.first_word_seconds:.0f}s")
                    try:
                        piece = await asyncio.wait_for(pieces.__anext__(), None if started else remaining)
                    except StopAsyncIteration:
                        break
                    if getattr(piece, "usage_metadata", None):
                        usage = piece.usage_metadata
                    part = chunk_text(piece)
                    if not part:
                        continue
                    raw += part
                    visible = strip_thinking(raw)
                    if visible:
                        if not started:
                            self.observer.first_word(handle)
                        started = True
                        yield Chunk(visible, route=route.name, model=route.model)
            except Exception as exc:  # down, refused, or too slow to start: try the next route
                if started:
                    self.observer.finish(handle, text=strip_thinking(raw, final=True), route=route.name, model=route.model, thinking=thinking, error=str(exc))
                    raise
                log.warning("%s (%s) failed: %s", route.name, route.model, exc)
                errors.append(f"{route.model}: {exc}")
                continue
            finally:
                await pieces.aclose()  # stop the model generating if we gave up on it
            text = strip_thinking(raw, final=True)
            if not text:
                errors.append(f"{route.model}: empty answer")
                continue
            tokens = self._record(route, messages, text, usage)
            if self.store:
                self.store.set(key, {"text": text, "route": route.name, "model": route.model, "at": time.time()})
            self.observer.finish(handle, text=text, route=route.name, model=route.model, thinking=thinking, tokens=tokens, attempts=errors)
            yield Chunk(text, done=True, route=route.name, model=route.model)
            return
        self.observer.finish(handle, error="; ".join(errors) or "no model answered")
        raise NoModelAvailable("; ".join(errors) or "no model answered")

    async def ask(self, prompt_or_messages: str | Iterable[Any], tier: str = "default", json_mode: bool = False) -> Answer:
        last: Chunk | None = None
        async for chunk in self.stream(prompt_or_messages, tier, json_mode):
            last = chunk
        if last is None:
            raise NoModelAvailable("no model answered")
        return Answer(last.text, last.route, last.model, last.cached)

    async def ask_json(self, prompt_or_messages: str | Iterable[Any], tier: str = "default") -> Any:
        answer = await self.ask(prompt_or_messages, tier, json_mode=True)
        return parse_json(answer.text)
