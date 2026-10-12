"""What the server measures about each request, and where that goes.

Every request becomes one MLflow trace, named after what it was for (``ask_lesson``,
``hint``, ``review``, ``explain``, ``quiz``, or the MCP tool Claude called), and tagged so
you can find it again: ``feature``, ``door`` (``page`` or ``mcp``), ``lesson_id``, ``step``,
``hint_level`` and ``app_version``. Follow-up questions in one thread share a session.

    ask_lesson                 CHAIN       the learner's question in, the answer out
      tutor.ask                CHAT_MODEL  the full messages, model, route, tokens, timings
        first_word                         time to first token: how long "Thinking..." showed
        attempt local          CHAT_MODEL  only when a model failed and the next was tried
      checks                   GUARDRAIL   did the answer leak the exercise, use Big-O, run long

The checks also land on the trace as tags (search ``tags.solution_leak = 'true'``) and as
code-sourced feedback, so they show as columns in the MLflow UI. Token counts use MLflow's
``mlflow.chat.tokenUsage`` shape, which its token and cost charts read. Each trace is linked
to a version: the git commit this server runs, with ``-dirty`` when tracked files have
uncommitted changes.

Traces go wherever ``MLFLOW_TRACKING_URI`` points (a SQLite file in ``.drill/`` when unset).
Nothing here can break an answer: when MLflow is not running, tracing is off and is tried
again every 30 seconds, so starting MLflow later turns it back on without a restart.
"""

from __future__ import annotations

import contextlib
import functools
import inspect
import logging
import os
import queue
import re
import subprocess
import threading
import time
from typing import Any, Iterator

from drill.config import databricks_user, experiment_path, is_databricks_uri, uc_trace_location

log = logging.getLogger("drill.server")

TEXT_LIMIT = 50_000  # characters kept per message; the page's prompts are about 4,000
RETRY_SECONDS = 30.0
SOURCE_ID = "drill.observe"

# What the page and the MCP tools may say about a request, and which of those become tags.
CONTEXT_KEYS = (
    "feature", "door", "lesson_id", "step", "hint_level", "question", "session", "user",
    "exercise_fn", "word_limit", "chip", "guard",
)
TAG_KEYS = ("feature", "door", "lesson_id", "step", "hint_level", "chip", "guard")

_BIG_O = re.compile(r"\bO\([^)\n]{1,15}\)")


# ---------------------------------------------------------------------------
# Version and checks
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def app_version() -> str:
    """The git commit this code runs from, ``-dirty`` if tracked files changed; else the package version."""
    from drill.config import PROJECT_ROOT

    try:
        def git(*args: str) -> str:
            return subprocess.run(
                ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=3, check=True
            ).stdout.strip()

        commit = git("rev-parse", "--short", "HEAD")
        dirty = git("status", "--porcelain", "--untracked-files=no")
        return commit + ("-dirty" if dirty else "")
    except Exception:
        from importlib.metadata import version

        try:
            return version("daily-drill")
        except Exception:
            return "unknown"


def clean_context(raw: dict | None) -> dict:
    """Only the known keys, as short strings (the question may be longer)."""
    out: dict = {}
    for key in CONTEXT_KEYS:
        value = (raw or {}).get(key)
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            value = "yes" if value else "no"
        out[key] = str(value)[: 2000 if key == "question" else 200]
    return out


def answer_checks(text: str, context: dict) -> dict:
    """Simple rules every answer should keep. ``True`` means the rule was broken."""
    words = len(text.split())
    checks: dict = {"words": words}
    fn = context.get("exercise_fn")
    if fn:
        checks["solution_leak"] = bool(re.search(rf"def\s+{re.escape(fn)}\s*\(", text))
    checks["big_o"] = bool(_BIG_O.search(text))
    limit = context.get("word_limit")
    if limit and str(limit).isdigit():
        checks["over_word_limit"] = words > int(limit)
    return checks


def _message_dicts(messages: list) -> list[dict]:
    roles = {"human": "user", "ai": "assistant", "system": "system"}
    out = []
    for m in messages:
        content = str(getattr(m, "content", m))
        if len(content) > TEXT_LIMIT:
            content = content[: TEXT_LIMIT // 2] + "\n[...cut...]\n" + content[-TEXT_LIMIT // 2 :]
        out.append({"role": roles.get(getattr(m, "type", ""), "user"), "content": content})
    return out


# ---------------------------------------------------------------------------
# Observers
# ---------------------------------------------------------------------------


class RecordingObserver:
    """Keeps every record in memory: for tests, and for a quick look without MLflow."""

    def __init__(self):
        self.records: list[dict] = []

    def start(self, messages: list, tier: str, context: dict | None = None) -> dict:
        return {"t0": time.monotonic(), "tier": tier, "ttft_ms": None, "context": clean_context(context), "failed": []}

    def first_word(self, handle: dict) -> None:
        if handle.get("ttft_ms") is None:
            handle["ttft_ms"] = round((time.monotonic() - handle["t0"]) * 1000)

    def attempt_failed(self, handle: dict, route: str, model: str, error: str, started_ns: int) -> None:
        handle["failed"].append({"route": route, "model": model, "error": error})

    def finish(self, handle: dict, **fields: Any) -> None:
        record = {"route": "", "model": "", "cached": False, "thinking": False, "tokens": None, "attempts": [], "error": None}
        record.update(handle, **fields, total_ms=round((time.monotonic() - handle["t0"]) * 1000))
        record["checks"] = answer_checks(fields.get("text", ""), handle["context"]) if fields.get("text") else {}
        self.records.append(record)


class MlflowObserver:
    """One MLflow trace per request; see the module docstring for its shape."""

    def __init__(self, experiment: str | None = None):
        # DRILL_MLFLOW_EXPERIMENT, not MLFLOW_EXPERIMENT_NAME: Claude Code's MLflow tracing sets
        # the latter for every process it starts, drill-mcp included.
        self.experiment = experiment or os.getenv("DRILL_MLFLOW_EXPERIMENT") or "daily-drill"
        self.enabled = False
        self._next_try = 0.0
        self._warned = False
        self._feedback: queue.Queue = queue.Queue(maxsize=500)
        self._worker: threading.Thread | None = None
        self.ready()

    # -- connecting --------------------------------------------------------

    def ready(self) -> bool:
        """Is tracing on? When it is off, try again at most every 30 seconds."""
        if self.enabled:
            return True
        if time.monotonic() < self._next_try:
            return False
        try:
            self._connect()
        except Exception as exc:
            self._next_try = time.monotonic() + RETRY_SECONDS
            if not self._warned:
                log.warning("MLflow tracing is off for now (%s); trying again every %.0fs", exc, RETRY_SECONDS)
            self._warned = True
            return False
        if self._warned:
            log.info("MLflow tracing is back on")
        self.enabled, self._warned = True, False
        return True

    def _connect(self) -> None:
        import mlflow

        if not os.getenv("MLFLOW_TRACKING_URI", "").strip():
            # MLflow 3.17 no longer accepts the ./mlruns folder store, so the default
            # here is a SQLite file next to the progress database. View it with:
            #   uv run mlflow ui --backend-store-uri sqlite:///.drill/mlflow.db
            # (or the same file under DRILL_HOME, when that is set).
            from drill.server.store import data_dir

            mlflow.set_tracking_uri(f"sqlite:///{data_dir() / 'mlflow.db'}")
        uri = mlflow.get_tracking_uri()
        if uri.startswith(("http://", "https://")):
            # A stopped server makes MLflow retry for about four minutes. Ask it first,
            # with a one-second limit, so a hint never waits on tracing.
            import httpx

            httpx.get(uri.rstrip("/") + "/health", timeout=1.0).raise_for_status()
        experiment = self.experiment
        if is_databricks_uri(uri):
            # No /health to ask on Databricks: asking who we are is the quick check, and the
            # answer turns "daily-drill" into the workspace path the experiment needs.
            experiment = experiment_path(experiment, uri, databricks_user(uri))
        where = uc_trace_location(mlflow.set_experiment(experiment))
        if where:
            log.info("Traces for %s go to Unity Catalog (%s); reading them needs a SQL warehouse", experiment, where)
        mlflow.set_active_model(name=f"daily-drill-{app_version()}")

    def _off(self, exc: Exception) -> None:
        if self.enabled:
            log.warning("MLflow tracing switched off: %s", exc)
        self.enabled = False
        self._next_try = time.monotonic() + RETRY_SECONDS

    # -- one request -------------------------------------------------------

    def start(self, messages: list, tier: str, context: dict | None = None) -> dict:
        ctx = clean_context(context)
        handle: dict = {"t0": time.monotonic(), "tier": tier, "ttft_ms": None, "context": ctx,
                        "root": None, "parent": None, "span": None, "wait": None}
        if not self.ready():
            return handle
        try:
            import mlflow
            from mlflow.tracing.constant import TraceMetadataKey

            tags = {k: ctx[k] for k in TAG_KEYS if k in ctx}
            tags["app_version"] = app_version()
            parent = mlflow.get_current_active_span()  # an MCP tool call, when there is one
            if parent is None:
                question = ctx.get("question") or next(
                    (str(m.content) for m in reversed(messages) if getattr(m, "type", "") == "human"), ""
                )[:TEXT_LIMIT]
                inputs = {"question": question, **{k: ctx[k] for k in ("lesson_id", "step", "hint_level") if k in ctx}}
                metadata = {}
                if "session" in ctx:
                    metadata[TraceMetadataKey.TRACE_SESSION] = ctx["session"]
                metadata[TraceMetadataKey.TRACE_USER] = ctx.get("user", "local")
                parent = mlflow.start_span_no_context(
                    ctx.get("feature", "request"), span_type="CHAIN", inputs=inputs, tags=tags, metadata=metadata
                )
                handle["root"] = parent
                tags = None  # already on the trace
            span = mlflow.start_span_no_context(
                "tutor.ask", span_type="CHAT_MODEL", parent_span=parent,
                inputs={"messages": _message_dicts(messages), "tier": tier}, tags=tags,
            )
            wait = mlflow.start_span_no_context("first_word", span_type="UNKNOWN", parent_span=span)
            handle.update(parent=parent, span=span, wait=wait)
        except Exception as exc:
            self._off(exc)
        return handle

    def first_word(self, handle: dict) -> None:
        if handle.get("ttft_ms") is not None:
            return
        handle["ttft_ms"] = round((time.monotonic() - handle["t0"]) * 1000)
        wait = handle.get("wait")
        if wait is not None:
            try:
                wait.end()
            except Exception as exc:
                self._off(exc)
            handle["wait"] = None

    def attempt_failed(self, handle: dict, route: str, model: str, error: str, started_ns: int) -> None:
        """A model that was tried and failed before the one that answered: its own span, with the error."""
        span = handle.get("span")
        if span is None:
            return
        try:
            import mlflow
            from mlflow.entities import SpanStatusCode

            failed = mlflow.start_span_no_context(
                f"attempt {route}", span_type="CHAT_MODEL", parent_span=span,
                attributes={"route": route, "model": model, "error": error[:2000]}, start_time_ns=started_ns,
            )
            failed.set_status(SpanStatusCode.ERROR)
            failed.end()
        except Exception as exc:
            self._off(exc)

    def finish(
        self,
        handle: dict,
        text: str = "",
        route: str = "",
        model: str = "",
        cached: bool = False,
        thinking: bool = False,
        tokens: dict | None = None,
        attempts: list[str] | None = None,
        error: str | None = None,
        settings: dict | None = None,
        finish_reason: str | None = None,
    ) -> None:
        total_ms = round((time.monotonic() - handle["t0"]) * 1000)
        span = handle.get("span")
        if span is None:
            return
        try:
            import mlflow
            from mlflow.entities import SpanStatusCode
            from mlflow.tracing.constant import SpanAttributeKey
            from mlflow.tracing.trace_manager import InMemoryTraceManager

            if handle.get("wait") is not None:  # no first word ever came: the wait was the whole call
                handle["wait"].end()
                handle["wait"] = None
            span.set_attributes(
                {
                    "route": route,
                    "model": model,
                    "tier": handle["tier"],
                    "cached": cached,
                    "thinking": thinking,
                    "ttft_ms": handle.get("ttft_ms") if handle.get("ttft_ms") is not None else total_ms,
                    "total_ms": total_ms,
                    "fallbacks": attempts or [],
                    "finish_reason": finish_reason or ("cached" if cached else ""),
                    **(settings or {}),
                }
            )
            if tokens:
                span.set_attribute(SpanAttributeKey.CHAT_USAGE, tokens)
            if error:
                span.set_attribute("error", error)
                span.set_status(SpanStatusCode.ERROR)
            span.end(outputs={"content": text[:TEXT_LIMIT]} if text else None)

            ctx = handle["context"]
            if text:
                checks = answer_checks(text, ctx)
                guard = mlflow.start_span_no_context(
                    "checks", span_type="GUARDRAIL", parent_span=handle["parent"],
                    inputs={k: ctx[k] for k in ("exercise_fn", "word_limit") if k in ctx},
                )
                guard.end(outputs=checks)
                with InMemoryTraceManager.get_instance().get_trace(span.trace_id) as trace:
                    if trace is not None:
                        for name, value in checks.items():
                            trace.info.tags[name] = str(value).lower()
                self._queue_feedback(span.trace_id, {k: v for k, v in checks.items() if isinstance(v, bool)})

            root = handle.get("root")
            if root is not None:
                if error:
                    root.set_status(SpanStatusCode.ERROR)
                root.end(outputs={"answer": text[:TEXT_LIMIT]} if text else None)
        except Exception as exc:
            self._off(exc)

    # -- the checks as feedback ------------------------------------------

    def _queue_feedback(self, trace_id: str, checks: dict) -> None:
        """Feedback can only be logged once the trace is saved, which happens in the background."""
        if not checks:
            return
        try:
            self._feedback.put_nowait((trace_id, checks))
        except queue.Full:
            return
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._log_feedback, name="drill-feedback", daemon=True)
            self._worker.start()

    def _log_feedback(self) -> None:
        import mlflow
        from mlflow.entities import AssessmentSource

        source = AssessmentSource(source_type="CODE", source_id=SOURCE_ID)
        while True:
            trace_id, checks = self._feedback.get()
            try:
                for attempt in range(20):  # an MCP tool's trace is saved only when the tool returns
                    try:
                        mlflow.flush_trace_async_logging()
                        for name, broken in checks.items():
                            mlflow.log_feedback(trace_id=trace_id, name=name, value=broken, source=source)
                        break
                    except Exception as exc:
                        if attempt == 19:
                            log.info("could not attach checks to %s: %s", trace_id, exc)
                        time.sleep(0.25)
            finally:
                self._feedback.task_done()

    def drain(self) -> None:
        """Wait until every queued check has been attached (for tests)."""
        self._feedback.join()


# ---------------------------------------------------------------------------
# The shared observer, and MCP tool calls
# ---------------------------------------------------------------------------

_default: dict = {}
MCP_SESSION = f"mcp-{os.getpid()}-{int(time.time())}"  # one per server process, so per Claude Code session for stdio


def default_observer() -> MlflowObserver | None:
    """The process's MLflow observer, or ``None`` when ``DRILL_TRACING=0``."""
    if os.getenv("DRILL_TRACING", "1").strip().lower() in ("0", "false", "no"):
        return None
    if "observer" not in _default:
        _default["observer"] = MlflowObserver()
    return _default["observer"]


@contextlib.contextmanager
def tool_span(name: str, inputs: dict) -> Iterator[Any]:
    """A TOOL span for one MCP tool call: a trace of its own, or a span in the caller's trace.

    Yields the span, or ``None`` when tracing is off. A tracing failure never reaches the tool.
    """
    observer = default_observer()
    if observer is None or not observer.ready():
        yield None
        return
    try:
        import mlflow

        manager = mlflow.start_span(name=name, span_type="TOOL")
        span = manager.__enter__()
    except Exception as exc:
        observer._off(exc)
        yield None
        return
    try:
        try:
            span.set_inputs(inputs)
            tags = {"feature": name, "door": "mcp", "app_version": app_version()}
            if inputs.get("lesson_id"):
                tags["lesson_id"] = str(inputs["lesson_id"])
            mlflow.update_current_trace(tags=tags, session_id=MCP_SESSION, user="local")
        except Exception:
            pass
        yield span
    except BaseException as exc:
        manager.__exit__(type(exc), exc, exc.__traceback__)  # records the error on the span
        raise
    manager.__exit__(None, None, None)


def traced_tool(fn):
    """Wrap an MCP tool so each call is traced: which tool, with what, and what came back."""
    signature = inspect.signature(fn)

    def inputs_of(args, kwargs) -> dict:
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)

    def record(span, result) -> None:
        if span is not None:
            with contextlib.suppress(Exception):
                span.set_outputs(result)

    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            with tool_span(fn.__name__, inputs_of(args, kwargs)) as span:
                result = await fn(*args, **kwargs)
                record(span, result)
                return result

    else:

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with tool_span(fn.__name__, inputs_of(args, kwargs)) as span:
                result = fn(*args, **kwargs)
                record(span, result)
                return result

    return wrapper
