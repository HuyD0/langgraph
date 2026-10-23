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
    DRILL_HOSTED_AUTH=databricks                  key | databricks: sign in with the Databricks login
    DRILL_HOSTED_DAILY_TOKENS=200000              stop using the hosted model for the tutor past this
    DRILL_NOTES_DAILY_TOKENS=150000               the managers' weekly notes: their own allowance
    DRILL_MAX_ANSWER_TOKENS=1200                  the longest answer the hosted model may write
    DRILL_MAX_PROMPT_CHARS=60000                  refuse a request bigger than this (about 15,000 tokens)
    DRILL_CACHE_DAYS=7                            forget a cached answer after this many days
    DRILL_CACHE_MAX=2000                          keep at most this many cached answers
    DRILL_TRACING=1                               0 switches MLflow tracing off (see observe.py)

With no DRILL_HOSTED_* set, the Azure settings from drill.config are the hosted model.

At work, the hosted model is behind Databricks Unity Gateway and there is no key to keep:
``DRILL_HOSTED_AUTH=databricks`` signs each request with the login already on the machine
(``databricks auth login``, which goes through Entra on Azure), renewed as it runs out. It
is also what happens when a Databricks address is set with no key. Without
``DRILL_HOSTED_BASE_URL`` the address comes from the workspace and the model's name, so
``DRILL_HOSTED_MODEL`` is the only other line needed: a Unity Gateway model service is named
``catalog.schema.service`` (``system.ai.<model>`` for the ready-made ones) and is reached at
``/ai-gateway/mlflow/v1``; any other name is a serving endpoint, at ``/serving-endpoints``
(the older route, which Databricks now calls legacy).
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
from typing import Any, AsyncIterator, Generator, Iterable
from urllib.parse import urlsplit

import httpx
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


# The tiers a learner-facing door (the page, the MCP tools) may ask for; "complex" is the paid one
# only the server's own features choose. Here, not in api.py, so mcp.py can use it without an import cycle.
PAGE_TIERS = ("quick", "default")


class NoModelAvailable(RuntimeError):
    """Neither a local nor a hosted model could answer.

    ``reason`` says why, so the door can tell the learner something true instead of
    "start Ollama" every time: ``budget`` (today's hosted allowance is spent and there is
    no local model), ``upstream`` (a model exists but did not answer: down, refused, or
    too slow to start) or ``none`` (no model is set up at all).
    """

    REASONS = ("budget", "upstream", "none")

    def __init__(self, message: str = "no model answered", reason: str = "upstream"):
        super().__init__(message)
        self.reason = reason if reason in self.REASONS else "upstream"


class PromptTooLong(ValueError):
    """The request is bigger than the server allows (``DRILL_MAX_PROMPT_CHARS``)."""


# Ollama can start or stop while the server runs: look again at most this often.
LOCAL_RECHECK_SECONDS = 30.0
# Clearing old cached answers is a database sweep, so do it at most this often.
CACHE_PRUNE_SECONDS = 3600.0


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
    def start(self, messages: list, tier: str, context: dict | None = None) -> dict:
        return {}

    def first_word(self, handle: dict) -> None:
        pass

    def attempt_failed(self, handle: dict, route: str, model: str, error: str, started_ns: int) -> None:
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


class DatabricksAuth(httpx.Auth):
    """Signs each request to a Databricks endpoint with the login on this machine.

    ``config`` is a ``databricks.sdk.config.Config``; its ``authenticate()`` hands back fresh
    headers, renewing the token when it runs out (it only goes to the network then, about
    once an hour), so a server left running all day keeps working. As the ``httpx`` auth
    under the OpenAI client, it replaces the placeholder key that client sends.
    """

    def __init__(self, config: Any):
        self.config = config

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers.update(self.config.authenticate())
        yield request


def is_databricks_url(url: str) -> bool:
    """Whether ``url`` is a Databricks workspace: judged on its host, not on the text anywhere in it."""
    host = urlsplit(url).hostname or ""
    return host.endswith((".azuredatabricks.net", ".cloud.databricks.com", ".gcp.databricks.com"))


def databricks_config() -> Any:
    """The Databricks login on this machine (``DATABRICKS_CONFIG_PROFILE`` picks a profile)."""
    from databricks.sdk.config import Config

    return Config()


def is_model_service(model: str) -> bool:
    """A Unity Gateway model service (``catalog.schema.service``) rather than a serving endpoint name."""
    return len(model.split(".")) == 3 and all(model.split("."))


def gateway_base_url(host: str, model: str) -> str:
    """Where to send a model's requests in a workspace: Unity Gateway for a model service, else the serving endpoints."""
    path = "/ai-gateway/mlflow/v1" if is_model_service(model) else "/serving-endpoints"
    return host.rstrip("/") + path


def hosted_auth(base: str, key: str) -> str:
    """``key`` or ``databricks``: ``DRILL_HOSTED_AUTH`` if set, else ``databricks`` for a Databricks address with no key."""
    wanted = os.getenv("DRILL_HOSTED_AUTH", "").strip().lower()
    if wanted in ("key", "databricks"):
        return wanted
    return "databricks" if not key and is_databricks_url(base) else "key"


def hosted_route(config_factory=databricks_config, transport: Any = None) -> Route | None:
    """``DRILL_HOSTED_*`` (any OpenAI-compatible endpoint) first, else the Azure settings.

    ``transport`` stands in for the network in tests.
    """
    base = os.getenv("DRILL_HOSTED_BASE_URL", "").strip()
    model = os.getenv("DRILL_HOSTED_MODEL", "").strip()
    key = os.getenv("DRILL_HOSTED_API_KEY", "").strip()
    if model and hosted_auth(base, key) == "databricks":
        from langchain_openai import ChatOpenAI

        try:
            config = config_factory()
        except Exception as exc:  # noqa: BLE001
            log.warning("No Databricks login for the hosted model (%s). Run `databricks auth login`.", exc)
            return None
        base = base or gateway_base_url(config.host, model)
        auth = DatabricksAuth(config)
        chat = ChatOpenAI(
            base_url=base, model=model, api_key="databricks", timeout=120, max_retries=1, stream_usage=True,
            http_client=httpx.Client(auth=auth, timeout=120, transport=transport),
            http_async_client=httpx.AsyncClient(auth=auth, timeout=120, transport=transport),
        )
        return Route("hosted", model, chat)
    if base and model:
        from langchain_openai import ChatOpenAI

        chat = ChatOpenAI(base_url=base, model=model, api_key=key or "none", timeout=120, max_retries=1, stream_usage=True)
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
    # Plain string trims, not a regex: `\s*```$` backtracks badly on a reply full of spaces.
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass  # not bare JSON: look for the first object or list inside the prose below
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
        find_local: Any = None,
        max_prompt_chars: int = 60_000,
        cache_seconds: float = 7 * 86400,
        cache_max: int = 2000,
        notes_daily_tokens: int = 150_000,
        max_answer_tokens: int = 0,
    ):
        self.local = local
        self.hosted = hosted
        self.store = store
        # How to look for Ollama again (``local_route``), so a server started before Ollama,
        # or one whose Ollama stopped, notices without a restart. None: ``local`` never changes.
        self.find_local = find_local
        self._local_checked = time.monotonic()
        # The hosted budget only means something if one request can't be enormous.
        self.max_prompt_chars = max_prompt_chars
        # Cached answers age out after ``cache_seconds``, and at most ``cache_max`` are kept.
        self.cache_seconds = cache_seconds
        self.cache_max = cache_max
        self._pruned: float | None = None  # when old cached answers were last cleared
        self.hosted_daily_tokens = hosted_daily_tokens
        # The managers' weekly notes have their own daily allowance ("notes"), so they can never
        # use up the tutor's; 0 means notes are never written with the hosted model.
        self.notes_daily_tokens = notes_daily_tokens
        # The longest answer the hosted model may write, in tokens (0: the model's own limit).
        self.max_answer_tokens = max_answer_tokens
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
        from drill.server.observe import default_observer

        observer = default_observer()  # None when DRILL_TRACING=0
        router = cls(
            local_route(), hosted_route(), store, budget, first_word, thinking, observer, find_local=local_route,
            max_prompt_chars=int(os.getenv("DRILL_MAX_PROMPT_CHARS", "60000") or 60_000),
            cache_seconds=float(os.getenv("DRILL_CACHE_DAYS", "7") or 7) * 86400,
            cache_max=int(os.getenv("DRILL_CACHE_MAX", "2000") or 2000),
            notes_daily_tokens=int(os.getenv("DRILL_NOTES_DAILY_TOKENS", "150000") or 0),
            max_answer_tokens=int(os.getenv("DRILL_MAX_ANSWER_TOKENS", "1200") or 0),
        )
        log.info(
            "models: local=%s hosted=%s thinking=%s",
            router.local and router.local.model, router.hosted and router.hosted.model, router.thinking,
        )
        return router

    # -- what is available -------------------------------------------------

    def refresh_local(self) -> None:
        """Look for Ollama again if it has been a while: it may have started, stopped or changed model.

        At most every ``LOCAL_RECHECK_SECONDS``, with the 1.5-second limit ``ollama_models`` uses,
        so it is cheap. Callers in async code run it on a worker thread (``order`` is).
        """
        if self.find_local is None or time.monotonic() - self._local_checked < LOCAL_RECHECK_SECONDS:
            return
        self._local_checked = time.monotonic()
        try:
            found = self.find_local()
        except Exception as exc:  # noqa: BLE001
            log.warning("could not look for Ollama: %s", exc)
            found = None
        before = self.local.model if self.local else None
        after = found.model if found else None
        if before == after:
            return  # same as before: keep the chat model already built
        log.info("local model: %s -> %s", before or "none", after or "none (Ollama is not running)")
        self.local = found

    @property
    def available(self) -> bool:
        self.refresh_local()
        return self.local is not None or self.hosted is not None

    def describe(self) -> dict:
        """For the health check: which models exist, the thinking policy, and budget use."""
        return {
            "local": self.local.model if self.local else None,
            "hosted": self.hosted.model if self.hosted else None,
            "thinking": self.thinking,
            "tracing": not isinstance(self.observer, _NullObserver) and bool(getattr(self.observer, "enabled", True)),
            "hosted_tokens_today": self.hosted_tokens_today(),
            "hosted_daily_tokens": self.hosted_daily_tokens,
            "notes_tokens_today": self.hosted_tokens_today("notes"),
            "notes_daily_tokens": self.notes_daily_tokens,
        }

    def _usage_path(self) -> str:
        return "usage/" + time.strftime("%Y-%m-%d")

    def hosted_tokens_today(self, pool: str = "hosted") -> int:
        """Hosted tokens used today from ``pool``: "hosted" is the tutor, "notes" the managers' notes."""
        if not self.store:
            return 0
        doc = self.store.get(self._usage_path()) or {}
        return int(doc.get(pool, {}).get("tokens", 0))

    def hosted_under_budget(self, needed: int = 0, pool: str = "hosted") -> bool:
        """Is there room in today's hosted budget for ``pool``, including ``needed`` tokens for this request?"""
        allowance = self.notes_daily_tokens if pool == "notes" else self.hosted_daily_tokens
        return self.hosted is not None and self.hosted_tokens_today(pool) + needed < allowance

    def unavailable_reason(self, needed: int = 0, pool: str = "hosted") -> str:
        """Why :meth:`order` came back empty: ``budget`` when a hosted model exists but today's
        allowance has no room for this request, else ``none`` (nothing is set up at all)."""
        return "budget" if self.hosted is not None and not self.hosted_under_budget(needed, pool) else "none"

    def order(self, tier: str = "default", needed: int = 0, pool: str = "hosted") -> list[Route]:
        """Who to try first. Only a "complex" job starts with the hosted model.

        ``needed`` is a rough token count for the request: one that would not fit in what is
        left of today's hosted budget is not sent to the hosted model at all.
        """
        self.refresh_local()
        hosted = self.hosted if self.hosted_under_budget(needed, pool) else None
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
        if route.name == "hosted" and self.max_answer_tokens and hasattr(chat, "bind"):
            chat = chat.bind(max_tokens=self.max_answer_tokens)  # a request can't buy an essay
        thinking = is_thinking_model(route.model)
        if thinking and route.name == "local" and not self.may_think(tier):
            chat = chat.bind(extra_body={"reasoning_effort": "none"})
            thinking = False
        return messages, chat, thinking

    def _cache_key(self, messages: list[BaseMessage], tier: str, json_mode: bool) -> str:
        payload = json.dumps([[m.type, str(m.content)] for m in messages]) + f"|{tier}|{json_mode}"
        return "cache/" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:40]

    def _fresh(self, cached: dict | None) -> bool:
        """A cached answer still young enough to reuse (one with no time on it counts as old)."""
        return bool(cached and cached.get("text")) and time.time() - float(cached.get("at") or 0) < self.cache_seconds

    def _prune_cache(self) -> None:
        """Forget answers past their time, and the oldest beyond ``cache_max``. At most hourly."""
        if not self.store or (self._pruned is not None and time.monotonic() - self._pruned < CACHE_PRUNE_SECONDS):
            return
        self._pruned = time.monotonic()
        try:
            self.store.prune("cache", older_than=time.time() - self.cache_seconds, keep=self.cache_max)
        except Exception as exc:  # noqa: BLE001 - a cache sweep must never fail an answer
            log.warning("could not clear old cached answers: %s", exc)

    def check_size(self, messages: list[BaseMessage]) -> None:
        """Refuse a request bigger than ``max_prompt_chars``, before any model sees it."""
        size = sum(len(str(m.content)) for m in messages)
        if self.max_prompt_chars and size > self.max_prompt_chars:
            raise PromptTooLong(
                f"That request is {size:,} characters; the most this server takes is {self.max_prompt_chars:,}."
            )

    def _record(self, route: Route, messages: list[BaseMessage], text: str, usage: dict | None, pool: str = "hosted") -> dict:
        """Count today's usage for the route (a hosted answer in its ``pool``), preferring the model's own token report."""
        tokens = estimate_tokens(messages, text)
        if usage and usage.get("total_tokens"):
            tokens = {
                "input_tokens": int(usage.get("input_tokens", 0)),
                "output_tokens": int(usage.get("output_tokens", 0)),
                "total_tokens": int(usage["total_tokens"]),
            }
        if self.store:
            self.store.add(self._usage_path(), pool if route.name == "hosted" else route.name, {"calls": 1, "tokens": tokens["total_tokens"]})
        return tokens

    async def stream(
        self,
        prompt_or_messages: str | Iterable[Any],
        tier: str = "default",
        json_mode: bool = False,
        context: dict | None = None,
        pool: str = "hosted",
    ) -> AsyncIterator[Chunk]:
        """Yield the answer as it grows; the last chunk has ``done=True`` and says who answered.

        ``context`` says what the request is for (feature, lesson, step...), for the trace.
        ``pool`` is whose daily allowance a hosted answer counts against: the tutor's, or "notes".
        """
        messages = to_messages(prompt_or_messages)
        self.check_size(messages)  # before tracing or the cache: a refused request costs nothing
        handle = self.observer.start(messages, tier, context)

        key = self._cache_key(messages, tier, json_mode)
        # The store may be Lakebase across the network: run its calls on a worker thread so
        # one slow save doesn't hold up every other request this server is answering.
        cached = await asyncio.to_thread(self.store.get, key) if self.store else None
        if self._fresh(cached):
            self.observer.first_word(handle)
            self.observer.finish(handle, text=cached["text"], route=cached.get("route", ""), model=cached.get("model", ""), cached=True)
            yield Chunk(cached["text"], done=True, route=cached.get("route", ""), model=cached.get("model", ""), cached=True)
            return

        needed = estimate_tokens(messages, "")["input_tokens"]
        routes = await asyncio.to_thread(self.order, tier, needed, pool)
        if not routes:
            reason = self.unavailable_reason(needed, pool)
            self.observer.finish(handle, error=f"no model available ({reason})")
            raise NoModelAvailable("No model is running. Start Ollama, or set a hosted model in .env.", reason=reason)

        errors: list[str] = []
        for route in routes:
            prepared, chat, thinking = self._prepare(messages, route, tier, json_mode)
            raw, started, usage, t0 = "", False, None, time.monotonic()
            began_ns, finish_reason = time.time_ns(), None
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
                    finish_reason = (getattr(piece, "response_metadata", None) or {}).get("finish_reason") or finish_reason
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
                self.observer.attempt_failed(handle, route.name, route.model, str(exc) or type(exc).__name__, began_ns)
                continue
            finally:
                await pieces.aclose()  # stop the model generating if we gave up on it
            text = strip_thinking(raw, final=True)
            if not text:
                errors.append(f"{route.model}: empty answer")
                self.observer.attempt_failed(handle, route.name, route.model, "empty answer", began_ns)
                continue
            tokens = await asyncio.to_thread(self._record, route, messages, text, usage, pool)
            if self.store:
                await asyncio.to_thread(
                    self.store.set, key, {"text": text, "route": route.name, "model": route.model, "at": time.time()}
                )
                await asyncio.to_thread(self._prune_cache)
            settings = {"temperature": getattr(route.chat, "temperature", None), "json_mode": json_mode}
            self.observer.finish(
                handle, text=text, route=route.name, model=route.model, thinking=thinking, tokens=tokens, attempts=errors,
                settings={k: v for k, v in settings.items() if v is not None}, finish_reason=finish_reason,
            )
            yield Chunk(text, done=True, route=route.name, model=route.model)
            return
        self.observer.finish(handle, error="; ".join(errors) or "no model answered")
        raise NoModelAvailable("; ".join(errors) or "no model answered", reason="upstream")

    async def ask(
        self,
        prompt_or_messages: str | Iterable[Any],
        tier: str = "default",
        json_mode: bool = False,
        context: dict | None = None,
        pool: str = "hosted",
    ) -> Answer:
        last: Chunk | None = None
        async for chunk in self.stream(prompt_or_messages, tier, json_mode, context, pool):
            last = chunk
        if last is None:
            raise NoModelAvailable("no model answered", reason="upstream")
        return Answer(last.text, last.route, last.model, last.cached)

    async def ask_json(self, prompt_or_messages: str | Iterable[Any], tier: str = "default", context: dict | None = None) -> Any:
        answer = await self.ask(prompt_or_messages, tier, json_mode=True, context=context)
        return parse_json(answer.text)
