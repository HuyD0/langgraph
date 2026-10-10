"""What the server measures about each answer, and where that goes.

Every answer becomes one MLflow trace: a ``tutor.ask`` span carrying the route, model,
tier, whether it came from the cache, whether the model was allowed to think, token
counts and total time, plus a child span ``first_word`` whose length is the **time to
first token**: how long the learner stared at "Thinking..." before words appeared. For
a streaming tutor that is the latency that matters, and it is not something MLflow's
latency dashboards show by themselves, hence the child span. Token counts are stored
in MLflow's own ``mlflow.chat.tokenUsage`` shape so the token and cost dashboards in
MLflow 3.17's trace analytics pick them up.

Traces go wherever MLflow is pointed (``MLFLOW_TRACKING_URI``; ``./mlruns`` by default,
viewed with ``uv run mlflow ui``). Nothing here can break an answer: a tracing failure
is logged once and tracing switches itself off.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

log = logging.getLogger("drill.server")

TEXT_LIMIT = 4000  # characters of prompt and answer kept on a span


class RecordingObserver:
    """Keeps every record in memory: for tests, and for a quick look without MLflow."""

    def __init__(self):
        self.records: list[dict] = []

    def start(self, messages: list, tier: str) -> dict:
        return {"t0": time.monotonic(), "tier": tier, "ttft_ms": None}

    def first_word(self, handle: dict) -> None:
        if handle.get("ttft_ms") is None:
            handle["ttft_ms"] = round((time.monotonic() - handle["t0"]) * 1000)

    def finish(self, handle: dict, **fields: Any) -> None:
        record = {"route": "", "model": "", "cached": False, "thinking": False, "tokens": None, "attempts": [], "error": None}
        record.update(handle, **fields, total_ms=round((time.monotonic() - handle["t0"]) * 1000))
        self.records.append(record)


class MlflowObserver:
    """One MLflow trace per answer, with time to first token as a child span."""

    def __init__(self, experiment: str | None = None):
        self.enabled = True
        try:
            import mlflow

            if not os.getenv("MLFLOW_TRACKING_URI", "").strip():
                # MLflow 3.17 no longer accepts the ./mlruns folder store, so the default
                # here is a SQLite file next to the progress database. View it with:
                #   uv run mlflow ui --backend-store-uri sqlite:///.drill/mlflow.db
                from drill.config import PROJECT_ROOT

                (PROJECT_ROOT / ".drill").mkdir(parents=True, exist_ok=True)
                mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / '.drill' / 'mlflow.db'}")
            mlflow.set_experiment(experiment or os.getenv("MLFLOW_EXPERIMENT_NAME", "daily-drill"))
        except Exception as exc:  # no server, bad URI: practise anyway, just without traces
            self._off(exc)

    def _off(self, exc: Exception) -> None:
        if self.enabled:
            log.warning("MLflow tracing switched off: %s", exc)
        self.enabled = False

    def start(self, messages: list, tier: str) -> dict:
        handle: dict = {"t0": time.monotonic(), "tier": tier, "ttft_ms": None, "span": None, "wait": None}
        if not self.enabled:
            return handle
        try:
            import mlflow

            prompt = next((str(m.content) for m in reversed(messages) if m.type == "human"), "")
            span = mlflow.start_span_no_context("tutor.ask", span_type="LLM", inputs={"prompt": prompt[:TEXT_LIMIT], "tier": tier})
            wait = mlflow.start_span_no_context("first_word", span_type="UNKNOWN", parent_span=span)
            handle.update(span=span, wait=wait)
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
    ) -> None:
        total_ms = round((time.monotonic() - handle["t0"]) * 1000)
        span = handle.get("span")
        if span is None:
            return
        try:
            from mlflow.entities import SpanStatusCode
            from mlflow.tracing.constant import SpanAttributeKey

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
                }
            )
            if tokens:
                span.set_attribute(SpanAttributeKey.CHAT_USAGE, tokens)
            if error:
                span.set_attribute("error", error)
                span.set_status(SpanStatusCode.ERROR)
            span.end(outputs={"text": text[:TEXT_LIMIT]} if text else None)
        except Exception as exc:
            self._off(exc)
