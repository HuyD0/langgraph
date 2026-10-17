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
from typing import Any, Callable, Iterator

from drill.config import databricks_user, experiment_path, is_databricks_uri, uc_trace_location

log = logging.getLogger("drill.server")

TEXT_LIMIT = 50_000  # characters kept per message; the page's prompts are about 4,000
RETRY_SECONDS = 30.0
SOURCE_ID = "drill.observe"
PAGE_SIGNALS = "drill.page.signals"  # what the page saw the learner do after an answer


def signals_every() -> float:
    """Minutes to hold the page's quiet signals before writing them in one go; 0 writes them at once."""
    try:
        return max(0.0, float(os.getenv("DRILL_SIGNALS_EVERY_MINUTES", "0") or 0))
    except ValueError:
        return 0.0

# What the page and the MCP tools may say about a request, and which of those become tags.
CONTEXT_KEYS = (
    "feature", "door", "lesson_id", "step", "hint_level", "question", "session", "user",
    "exercise_fn", "word_limit", "chip", "guard", "request", "prompt_version", "blank_fields", "retry_of",
)
TAG_KEYS = ("feature", "door", "lesson_id", "step", "hint_level", "chip", "guard", "prompt_version", "retry_of")  # "request" is the client_request_id
REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{6,64}$")  # the page's id for one request, used to find its trace again

_BIG_O = re.compile(r"\bO\([^)\n]{1,15}\)")


# ---------------------------------------------------------------------------
# Version and checks
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def app_version() -> str:
    """The git commit this code runs from, ``-dirty`` if tracked files changed; else the package version.

    A Databricks App has no git history, so ``drill cloud deploy`` writes the commit to
    ``.drill-version`` beside the code first.
    """
    from drill.config import PROJECT_ROOT

    stamp = PROJECT_ROOT / ".drill-version"
    if stamp.is_file() and stamp.read_text().strip():
        return stamp.read_text().strip()
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


PROMPT_FEATURES = {"use_case_review": "review", "use_case_challenge": "challenge"}  # feature -> prompt key


def load_prompt_versions(model_id: str | None) -> dict:
    """The registered prompt versions this app version uses, by the feature that uses them.

    The version record ``drill cloud deploy`` writes names them exactly (``prompt_review`` =
    ``catalog.schema.use_case_review/3``); without one, the ``production`` alias of each prompt's
    configured name. Nothing registered, or no access: no links, and nothing else changes.
    """
    import mlflow

    from drill import mlflow_names

    params: dict = {}
    if model_id:
        try:
            params = mlflow.get_logged_model(model_id).params or {}
        except Exception as exc:  # noqa: BLE001
            log.info("could not read the version record %s: %s", model_id, str(exc).splitlines()[0][:200])
            params = {}
    found = {}
    for feature, key in PROMPT_FEATURES.items():
        ref = params.get(f"prompt_{key}")
        uri = f"prompts:/{ref}" if ref else f"prompts:/{mlflow_names.prompt_name(key)}@production"
        try:
            found[feature] = mlflow.genai.load_prompt(uri, link_to_model=False)
        except Exception as exc:  # noqa: BLE001
            log.info("no prompt link for %s (%s): %s", feature, uri, str(exc).splitlines()[0][:200])
    if found:
        log.info("traces link to prompts: %s", ", ".join(f"{pv.name}/{pv.version}" for pv in found.values()))
    return found


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
    if context.get("feature") == "use_case_review":  # the review's own rules: drill.review_checks
        from drill.review_checks import review_checks

        checks.update(review_checks(text, (context.get("blank_fields") or "").split(",")))
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
        from drill import mlflow_names

        self.experiment = experiment or mlflow_names.experiment()
        self.enabled = False
        self._next_try = 0.0
        self._warned = False
        self._feedback: queue.Queue = queue.Queue(maxsize=500)
        self._worker: threading.Thread | None = None
        self._prompts: dict = {}  # feature -> the registered prompt version its traces are linked to
        self._reconnect: threading.Thread | None = None
        # The page's quiet signals (saved, asked again...) can wait: with DRILL_SIGNALS_EVERY_MINUTES
        # set (the app: 60), they are held and written in one burst, so a busy day wakes the SQL
        # warehouse that keeps Unity Catalog traces once an hour, not once per signal. The learner's
        # own feedback (Got it / Still stuck) is always written straight away.
        self._held: list[tuple] = []
        self._held_lock = threading.Lock()
        self._held_timer: threading.Thread | None = None
        self.ready(wait=True)  # at start-up, connect before the first request

    # -- connecting --------------------------------------------------------

    def ready(self, wait: bool = False) -> bool:
        """Is tracing on? When it is off, try again at most every 30 seconds.

        A retry runs on a background thread and this request goes untraced, so a slow or
        failing MLflow never holds up an answer (connecting can mean several network calls).
        ``wait=True`` connects right here instead: for start-up, before any request.
        """
        if self.enabled:
            return True
        if time.monotonic() < self._next_try:
            return False
        if not wait:
            if self._reconnect is None or not self._reconnect.is_alive():
                self._next_try = time.monotonic() + RETRY_SECONDS  # one try at a time
                self._reconnect = threading.Thread(target=self._try_connect, name="drill-mlflow-reconnect", daemon=True)
                self._reconnect.start()
            return False
        return self._try_connect()

    def _try_connect(self) -> bool:
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
        experiment_id = os.getenv("DRILL_MLFLOW_EXPERIMENT_ID", "").strip()  # a Databricks App's experiment resource
        if experiment_id:
            chosen = mlflow.set_experiment(experiment_id=experiment_id)
            experiment = chosen.name
        else:
            if is_databricks_uri(uri):
                # No /health to ask on Databricks: asking who we are is the quick check, and the
                # answer turns "daily-drill" into the workspace path the experiment needs.
                experiment = experiment_path(experiment, uri, databricks_user(uri))
            chosen = mlflow.set_experiment(experiment)
        from drill import mlflow_names

        if mlflow_names.prompt_schema():
            # Tells MLflow tools which Unity Catalog schema holds this app's prompts.
            mlflow.set_experiment_tags({"mlflow.promptRegistryLocation": mlflow_names.prompt_schema()})
        self.experiment_id = getattr(chosen, "experiment_id", None)  # for evals and datasets that belong beside the traces
        where = uc_trace_location(chosen)
        if where:
            log.info("Traces for %s go to Unity Catalog (%s); reading them needs a SQL warehouse", experiment, where)
        active = mlflow.set_active_model(name=f"daily-drill-{app_version()}")
        self._prompts = load_prompt_versions(getattr(active, "model_id", None))

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
            from mlflow.tracing.trace_manager import InMemoryTraceManager

            from drill import mlflow_names

            version = app_version()
            tags = {**{k: ctx[k] for k in TAG_KEYS if k in ctx}, **mlflow_names.context_tags(version)}
            parent = mlflow.get_current_active_span()  # an MCP tool call, when there is one
            if parent is None:
                question = ctx.get("question") or next(
                    (str(m.content) for m in reversed(messages) if getattr(m, "type", "") == "human"), ""
                )[:TEXT_LIMIT]
                inputs = {"question": question, **{k: ctx[k] for k in ("lesson_id", "step", "hint_level") if k in ctx}}
                metadata = mlflow_names.context_metadata(version)
                if "session" in ctx:
                    metadata[TraceMetadataKey.TRACE_SESSION] = ctx["session"]
                metadata[TraceMetadataKey.TRACE_USER] = ctx.get("user", "local")
                parent = mlflow.start_span_no_context(
                    ctx.get("feature", "request"), span_type="CHAIN", inputs=inputs, tags=tags, metadata=metadata
                )
                handle["root"] = parent
                tags = None  # already on the trace
                if ctx.get("request"):
                    # MLflow's own field for the caller's request id: the page finds this trace again by it.
                    with InMemoryTraceManager.get_instance().get_trace(parent.trace_id) as trace:
                        if trace is not None:
                            trace.info.client_request_id = ctx["request"]
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

            with InMemoryTraceManager.get_instance().get_trace(span.trace_id) as trace:
                if trace is not None:  # filterable per trace: tags.model, tags.route, tags.cached
                    trace.info.tags.update({"model": model or "none", "route": route or "none", "cached": str(cached).lower()})

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
                if os.getenv("DRILL_CHECKS_AS_FEEDBACK", "1").strip().lower() not in ("0", "false", "no"):
                    # Off in the app: with traces in Unity Catalog each write wakes a SQL warehouse.
                    # The checks are still tags and a span; `drill traces score` adds them in one batch.
                    self._queue_feedback(span.trace_id, {k: v for k, v in checks.items() if isinstance(v, bool)})

            pv = self._prompts.get(ctx.get("feature"))
            if pv is not None:
                # A tag to filter by; the link itself is kept with the prompt version in the registry.
                with InMemoryTraceManager.get_instance().get_trace(span.trace_id) as trace:
                    if trace is not None:
                        trace.info.tags["prompt"] = f"{pv.name}/{pv.version}"
                self._link_prompt(span.trace_id, ctx["feature"])

            root = handle.get("root")
            if root is not None:
                if error:
                    root.set_status(SpanStatusCode.ERROR)
                root.end(outputs={"answer": text[:TEXT_LIMIT]} if text else None)
        except Exception as exc:
            self._off(exc)

    def _link_prompt(self, trace_id: str, feature: str) -> None:
        """Link a review or challenge trace to the registered prompt version it was built from."""
        pv = self._prompts.get(feature)
        if pv is None:
            return
        try:
            self._feedback.put_nowait(("link", trace_id, pv))
        except queue.Full:
            return
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._log_feedback, name="drill-feedback", daemon=True)
            self._worker.start()

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
            item = self._feedback.get()
            if item and item[0] == "human":
                try:
                    self._log_human(*item[1:])
                finally:
                    self._feedback.task_done()
                continue
            if item and item[0] == "link":
                try:
                    for attempt in range(20):  # the trace must be saved before it can be linked
                        try:
                            mlflow.flush_trace_async_logging()
                            mlflow.MlflowClient().link_prompt_versions_to_trace([item[2]], item[1])
                            break
                        except Exception as exc:
                            if attempt == 19:
                                log.info("could not link %s to its prompt: %s", item[1], exc)
                            time.sleep(0.25)
                finally:
                    self._feedback.task_done()
                continue
            trace_id, checks = item
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

    # -- people's feedback on an answer ----------------------------------

    def human_feedback(self, request: str, name: str, value: Any, rationale: str | None, user: str, signal: bool = False) -> bool:
        """Attach a person's feedback to the trace the page tagged with ``request``. Queued, as the
        trace may still be saving; returns False when tracing is off or the id is not one of ours.
        ``signal``: something the page noticed the learner do (saved it, asked again...), not what they
        said, so it is recorded as CODE feedback from the page rather than HUMAN."""
        if not REQUEST_ID.match(request or "") or not self.ready():
            return False
        item = ("human", request, name, value, rationale, user, signal)
        if signal and signals_every() > 0:
            with self._held_lock:
                if len(self._held) >= 2000:
                    return False
                self._held.append(item)
            if self._held_timer is None or not self._held_timer.is_alive():
                self._held_timer = threading.Thread(target=self._release_held, name="drill-signals", daemon=True)
                self._held_timer.start()
            return True
        try:
            self._feedback.put_nowait(item)
        except queue.Full:
            return False
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._log_feedback, name="drill-feedback", daemon=True)
            self._worker.start()
        return True

    def flush_signals(self) -> int:
        """Write the held signals now (every hour, and when the app stops). Returns how many."""
        with self._held_lock:
            held, self._held = self._held, []
        for item in held:
            try:
                self._feedback.put(item, timeout=5)
            except queue.Full:
                log.info("feedback queue full: dropped %s signals", len(held))
                break
        if held and (self._worker is None or not self._worker.is_alive()):
            self._worker = threading.Thread(target=self._log_feedback, name="drill-feedback", daemon=True)
            self._worker.start()
        return len(held)

    def _release_held(self) -> None:
        while True:
            time.sleep(signals_every() * 60)
            if not self.flush_signals():
                return  # nothing came in for a whole round: the next signal starts the clock again

    def _log_human(self, request: str, name: str, value: Any, rationale: str | None, user: str, signal: bool = False) -> None:
        if not REQUEST_ID.fullmatch(request or ""):
            return  # the id goes into a filter string: the sink checks it itself, however it is reached
        import mlflow
        from mlflow.entities import AssessmentSource

        for attempt in range(20):
            try:
                mlflow.flush_trace_async_logging()
                found = mlflow.search_traces(filter_string=f"trace.client_request_id = '{request}'", max_results=1, return_type="list") \
                    or mlflow.search_traces(filter_string=f"tags.request = '{request}'", max_results=1, return_type="list")  # older traces
                if found:
                    mlflow.log_feedback(trace_id=found[0].info.trace_id, name=name, value=value, rationale=rationale or None,
                                        source=AssessmentSource(source_type="CODE", source_id=PAGE_SIGNALS) if signal
                                        else AssessmentSource(source_type="HUMAN", source_id=user or "learner"))
                    return
            except Exception as exc:
                if attempt == 19:
                    log.info("could not attach feedback for request %s: %s", request, exc)
            time.sleep(0.25)

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
            from drill import mlflow_names

            tags = {"feature": name, "door": "mcp", **mlflow_names.context_tags(app_version())}
            if inputs.get("lesson_id"):
                tags["lesson_id"] = str(inputs["lesson_id"])
            mlflow.update_current_trace(tags=tags, session_id=MCP_SESSION, user="local")
        except Exception:
            pass  # tracing is optional: a tag that does not stick must not fail the tool call
        yield span
    except BaseException as exc:
        manager.__exit__(type(exc), exc, exc.__traceback__)  # records the error on the span
        raise
    manager.__exit__(None, None, None)


def traced_tool(fn: Callable[..., Any]) -> Callable[..., Any]:
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
