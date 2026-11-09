"""Finding the lesson paragraphs that fit a question, for the asks that come with no lesson.

When a learner asks on a lesson page, the page sends that lesson's text, so the coach has nothing to find.
Some questions arrive with no lesson: a follow-up on a study list item saved from no exercise
(``ask_study_item``), Claude's ``ask_tutor`` tool over MCP, and any ``/api/ask`` without a ``lesson_id``.
For those, this module does **retrieval**: it turns the question into a list of numbers with an
**embedding model** and finds the five Learn paragraphs closest in meaning, which go into the coach's
prompt. Putting found text into the prompt is retrieval-augmented generation (RAG).

The model is the one the coach-retrieval lab kept as champion (``notebooks/learning/coach_retrieval``):
``bge-large`` as its makers ship it, with their search prompt (:data:`drill.embedding_compare.BGE_QUERY`)
before the question and nothing before the paragraphs. The paragraphs are the lab's own haystack,
:func:`drill.embedding_compare.corpus`: every Learn paragraph, one chunk each.

- **Embedded once.** Every paragraph is embedded when the server starts (on a background thread, so
  start-up does not wait) and the vectors are saved in ``DRILL_HOME/retrieval/``, named by the model and a
  fingerprint of the paragraphs, so a restart with the same lessons reads them back and any change to a
  paragraph embeds afresh.
- **Who embeds.** On your computer, Ollama's ``bge-large`` (``ollama pull bge-large``). In a Databricks App,
  the pay-per-token endpoint ``databricks-bge-large-en`` (``DRILL_EMBEDDING_ENDPOINT`` names another, such
  as the model service ``system.ai.bge-large-en``), signed with the app's own Databricks login, the way
  :mod:`drill.server.router` reaches the tutor's model: no key.
- **Never in the way.** A question is embedded with a short time limit (``DRILL_RETRIEVAL_SECONDS``, 2).
  On any error or timeout, or while the paragraphs are still being embedded, the coach answers as it
  always did, and :class:`Found` says why.
- ``DRILL_RETRIEVAL``: ``auto`` (the default) retrieves when an embedding model is there, ``on`` does too but
  counts a missing model as an error, ``off`` never retrieves. ``0``, ``false`` and ``no`` also mean off, and
  ``1``, ``true`` and ``yes`` mean on, the way ``DRILL_TRACING`` reads them; any other value means auto, with a
  warning in the log.

The help with a learner's own use case is private (its features start ``use_case``), so it never
retrieves and records nothing about retrieval: :func:`applies` says so.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from drill.embedding_compare import BGE_QUERY, corpus

log = logging.getLogger("drill.server")

K = 5
MODES = ("auto", "on", "off")
SPELLINGS = {"0": "off", "false": "off", "no": "off", "1": "on", "true": "on", "yes": "on"}
STATES = ("on", "off", "error", "timeout")
DEFAULT_ENDPOINT = "databricks-bge-large-en"
OLLAMA_MODEL = "bge-large"
RETRY_SECONDS = 60.0  # after a failed or impossible build, try again at most this often
BATCH = 32
QUESTION_CHARS = 2000

INTRO = ("Lessons from this course that may help, found by searching the course for their question. "
         "Use what fits and ignore the rest; never say you were given them.")


def mode_from(value: str | None) -> str:
    """``DRILL_RETRIEVAL`` as one of :data:`MODES`. ``0``/``false``/``no`` mean off and ``1``/``true``/``yes``
    mean on, as for ``DRILL_TRACING``; empty means auto, and anything else means auto with a warning."""
    raw = (value or "").strip().lower()
    if not raw:
        return "auto"
    mode = SPELLINGS.get(raw, raw)
    if mode not in MODES:
        log.warning("retrieval: DRILL_RETRIEVAL=%r is not off, auto or on; using auto", value)
        return "auto"
    return mode


def applies(feature: str, lesson_id: str) -> bool:
    """Retrieve only where no lesson is known, and never for the private use-case helper."""
    return not lesson_id and not (feature or "").startswith("use_case")


# ---------------------------------------------------------------------------
# What one search found
# ---------------------------------------------------------------------------


@dataclass
class Found:
    """One search: ``state`` is on, off, error or timeout; ``hits`` the paragraphs, closest first."""

    state: str
    model: str = ""
    ms: int = 0
    hits: list[dict] = field(default_factory=list)
    why: str = ""
    query: str = ""
    started_ns: int = 0
    ended_ns: int = 0

    @property
    def lessons(self) -> list[str]:
        """The lessons of the hits, in order, each once."""
        return list(dict.fromkeys(h["lesson"] for h in self.hits))

    def detail(self) -> dict:
        """What goes on the ``asked`` event."""
        out = {"retrieval": self.state, "retrieval_model": self.model, "retrieval_ms": self.ms, "retrieved": self.lessons}
        if self.hits:
            out["retrieved_paragraphs"] = [h["id"] for h in self.hits]
        if self.why:
            out["retrieval_why"] = self.why[:200]
        return out

    def trace(self) -> dict:
        """What the observer turns into a RETRIEVER span (see ``observe``)."""
        return {**self.detail(), "query": self.query, "started_ns": self.started_ns, "ended_ns": self.ended_ns,
                "documents": [{"id": h["id"], "page_content": h["text"],
                               "metadata": {"doc_uri": h["id"], "lesson_id": h["lesson"], "title": h["title"],
                                            "score": round(h["score"], 4)}} for h in self.hits]}


def fit(found: Found, fits: Callable[[list[dict]], bool]) -> Found:
    """Keep as many of the closest paragraphs as ``fits`` allows, dropping the lowest-ranked one at a time.
    When even one does not fit, ``found`` has none, with state off and why "no room in the prompt". The caller
    checks the prompt on its own first: a question too long by itself is never blamed on retrieval."""
    hits = list(found.hits)
    while hits and not fits(hits):
        hits.pop()
    if found.hits and not hits:  # found some, but there was no room for even one
        found.state, found.why = "off", "no room in the prompt"
    found.hits = hits
    return found


def context_text(hits: list[dict]) -> str:
    """The found paragraphs as the coach reads them: each lesson's title, then its paragraphs."""
    parts, last = [INTRO], None
    for h in hits:
        if h["lesson"] != last:
            parts.append(f"\nLesson: {h['title']}")
            last = h["lesson"]
        parts.append(h["text"])
    return "\n".join(parts)


def with_found(messages: list, hits: list[dict]) -> list:
    """The messages with the found paragraphs put before the learner's last message, in that same message:
    where a lesson page puts its lesson's text."""
    from langchain_core.messages import HumanMessage

    if not hits:
        return messages
    at = next((i for i in range(len(messages) - 1, -1, -1) if getattr(messages[i], "type", "") == "human"), None)
    if at is None:
        return messages
    out = list(messages)
    out[at] = HumanMessage(content=f"{context_text(hits)}\n\n{messages[at].content}")
    return out


# ---------------------------------------------------------------------------
# Embedders
# ---------------------------------------------------------------------------


class OllamaEmbedder:
    """``bge-large`` in Ollama on this computer, as the lab ran it (``drill.embedding_compare.ollama_embed``)."""

    def __init__(self, model: str = OLLAMA_MODEL, base_url: str = ""):
        root = (base_url or os.getenv("OLLAMA_BASE_URL", "") or "http://localhost:11434").strip().rstrip("/")
        self.root = root[: -len("/v1")] if root.endswith("/v1") else root
        self.model = model

    def ready(self) -> str:
        """``""`` when Ollama is running with the model pulled, else why not."""
        import httpx

        try:
            response = httpx.get(self.root + "/api/tags", timeout=1.5)
            response.raise_for_status()
            names = [m["name"] for m in response.json().get("models", [])]
        except Exception:  # noqa: BLE001
            return "Ollama is not running"
        if not any(n == self.model or n.startswith(self.model + ":") for n in names):
            return f"{self.model} is not pulled in Ollama (ollama pull {self.model})"
        return ""

    def embed(self, texts: list[str], timeout: float = 300) -> list[list[float]]:
        import httpx

        response = httpx.post(self.root + "/api/embed", json={"model": self.model, "input": texts, "truncate": True}, timeout=timeout)
        response.raise_for_status()
        return response.json()["embeddings"]


class DatabricksEmbedder:
    """A Databricks embedding endpoint (pay-per-token ``databricks-bge-large-en`` by default), signed with the
    Databricks login: the app's own service principal in an app. A three-part name (``system.ai.bge-large-en``)
    is a Unity Gateway model service and goes to the gateway, like the tutor's model does."""

    def __init__(self, endpoint: str = DEFAULT_ENDPOINT, config_factory: Callable[[], Any] | None = None, transport: Any = None):
        self.model = endpoint
        self._config_factory = config_factory
        self._transport = transport
        self._client = None

    def ready(self) -> str:
        try:
            self._http()
        except Exception as exc:  # noqa: BLE001
            return f"no Databricks login ({str(exc).splitlines()[0][:120]})"
        return ""

    def _http(self):
        if self._client is None:
            import httpx

            from drill.server.router import DatabricksAuth, databricks_config, gateway_base_url, is_model_service

            config = (self._config_factory or databricks_config)()
            base = gateway_base_url(config.host, self.model)
            self._url = base + ("/embeddings" if is_model_service(self.model) else f"/{self.model}/invocations")
            self._client = httpx.Client(auth=DatabricksAuth(config), transport=self._transport)
        return self._client

    def embed(self, texts: list[str], timeout: float = 300) -> list[list[float]]:
        from drill.server.router import is_model_service

        body: dict = {"input": texts}
        if is_model_service(self.model):
            body["model"] = self.model
        response = self._http().post(self._url, json=body, timeout=timeout)
        response.raise_for_status()
        rows = sorted(response.json()["data"], key=lambda d: d.get("index", 0))
        return [r["embedding"] for r in rows]


def choose_embedder() -> Any:
    """Ollama on your computer; the Databricks endpoint inside a Databricks App."""
    if os.getenv("DATABRICKS_APP_NAME", "").strip():
        return DatabricksEmbedder(os.getenv("DRILL_EMBEDDING_ENDPOINT", "").strip() or DEFAULT_ENDPOINT)
    return OllamaEmbedder()


# ---------------------------------------------------------------------------
# The retriever
# ---------------------------------------------------------------------------


def fingerprint(chunks: list[dict], model: str) -> str:
    """Changes when any paragraph or the model changes, so old vectors are never read for new text."""
    h = hashlib.sha256(f"{model}\x00{BGE_QUERY}\x00".encode())
    for c in chunks:
        h.update(f"{c['id']}\x00{c['text']}\x00".encode())
    return h.hexdigest()[:16]


def _unit(vectors):
    import numpy as np

    v = np.asarray(vectors, dtype="float32")
    return v / np.linalg.norm(v, axis=-1, keepdims=True).clip(min=1e-12)


class Retriever:
    """Every Learn paragraph's vector, and the top five paragraphs for a question."""

    def __init__(self, data: dict, embedder: Any = None, mode: str = "auto", timeout: float = 2.0,
                 cache_dir: Path | None = None, k: int = K):
        self.mode = mode_from(mode)
        self.chunks = corpus(data)
        titles = {lid: lesson.get("title", lid) for lid, lesson in data["lessons"].items()}
        for c in self.chunks:
            c["title"] = titles.get(c["lesson"], c["lesson"])
        self.embedder = embedder
        self.timeout = timeout
        self.cache_dir = cache_dir
        self.k = k
        self._vectors = None
        self._lock = threading.Lock()
        self._building: threading.Thread | None = None
        self._next_try = 0.0
        self.why = "not started"  # why there are no vectors yet
        self._failed = ""  # why the last build failed; kept while a retry runs, so "on" still counts it an error

    @classmethod
    def from_env(cls, data: dict) -> "Retriever":
        mode = mode_from(os.getenv("DRILL_RETRIEVAL"))
        try:
            timeout = float(os.getenv("DRILL_RETRIEVAL_SECONDS", "2") or 2)
        except ValueError:
            timeout = 2.0
        from drill.server.store import data_dir

        return cls(data, None if mode == "off" else choose_embedder(), mode, timeout, data_dir() / "retrieval")

    # -- the paragraphs' vectors ---------------------------------------------

    @property
    def model(self) -> str:
        return getattr(self.embedder, "model", "") if self.embedder is not None else ""

    @property
    def ready(self) -> bool:
        return self._vectors is not None

    def describe(self) -> dict:
        """For the health check."""
        return {"mode": self.mode, "model": self.model or None, "ready": self.ready,
                "paragraphs": len(self.chunks), **({} if self.ready else {"why": self.why})}

    def _cache_file(self) -> Path | None:
        if self.cache_dir is None:
            return None
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", self.model)
        return self.cache_dir / f"{safe}-{fingerprint(self.chunks, self.model)}.npy"

    def build(self) -> bool:
        """Read the paragraphs' vectors from disk, or embed them all and save them. True when ready."""
        import numpy as np

        if self.ready:
            return True
        if self.mode == "off" or self.embedder is None:
            self.why = "DRILL_RETRIEVAL=off"
            return False
        problem = self.embedder.ready() if hasattr(self.embedder, "ready") else ""
        if problem:
            self.why = self._failed = problem
            self._next_try = time.monotonic() + RETRY_SECONDS
            return False
        path = self._cache_file()
        try:
            if path is not None and path.is_file():
                vectors = np.load(path)
                if vectors.shape[0] == len(self.chunks):
                    with self._lock:
                        self._vectors = vectors
                    self._failed = ""
                    log.info("retrieval: %d paragraphs read from %s", len(self.chunks), path.name)
                    return True
            t0 = time.monotonic()
            texts = [c["text"] for c in self.chunks]  # no prompt before a paragraph: the lab's champion setup
            raw: list[list[float]] = []
            for start in range(0, len(texts), BATCH):
                raw.extend(self.embedder.embed(texts[start:start + BATCH]))
            vectors = _unit(raw)
            if vectors.shape[0] != len(self.chunks):
                raise ValueError(f"{vectors.shape[0]} vectors for {len(self.chunks)} paragraphs")
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                part = path.with_name(path.stem + ".part.npy")
                np.save(part, vectors)
                part.replace(path)  # whole or not at all: a half-written file is never read back
            with self._lock:
                self._vectors = vectors
            self._failed = ""
            log.info("retrieval: embedded %d paragraphs with %s in %.0fs", len(self.chunks), self.model, time.monotonic() - t0)
            return True
        except Exception as exc:  # noqa: BLE001 - the coach answers without it
            self.why = self._failed = f"could not embed the lessons: {str(exc).splitlines()[0][:160] if str(exc) else type(exc).__name__}"
            self._next_try = time.monotonic() + RETRY_SECONDS
            log.warning("retrieval: %s", self.why)
            return False

    def start(self) -> None:
        """Build on a background thread (once at a time, and not again straight after a failure)."""
        if self.ready or self.mode == "off" or self.embedder is None:
            return
        if self._building is not None and self._building.is_alive():
            return
        if time.monotonic() < self._next_try:
            return
        # a retry after a failure keeps saying what went wrong until it works: the model may still be missing
        self.why = self._failed or "still embedding the lessons"
        self._building = threading.Thread(target=self.build, name="drill-retrieval-index", daemon=True)
        self._building.start()

    # -- one question --------------------------------------------------------

    def top(self, query_vector, k: int | None = None) -> list[dict]:
        import numpy as np

        scores = self._vectors @ _unit([query_vector])[0]
        order = np.argsort(-scores)[: k or self.k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in order]

    async def search(self, question: str) -> Found:
        """The top paragraphs for ``question``. Never raises and never waits past the time limit."""
        t0, started = time.perf_counter(), time.time_ns()
        question = (question or "").strip()[:QUESTION_CHARS]

        def done(state: str, why: str = "", hits: list[dict] | None = None) -> Found:
            return Found(state, self.model, round((time.perf_counter() - t0) * 1000), hits or [], why, question, started, time.time_ns())

        if self.mode == "off":
            return done("off", "DRILL_RETRIEVAL=off")
        if self.embedder is None:
            return done("error" if self.mode == "on" else "off", "no embedding model")
        if not question:
            return done("off", "no question to search with")
        if not self.ready:
            self.start()
            # "on" asked for retrieval: a model that cannot be reached is an error; "auto" just goes without
            missing = self.why not in ("still embedding the lessons", "not started")
            return done("error" if self.mode == "on" and missing else "off", self.why)
        try:
            vectors = await asyncio.wait_for(
                asyncio.to_thread(self.embedder.embed, [BGE_QUERY + question], self.timeout), self.timeout)
            return done("on", hits=self.top(vectors[0]))
        except (asyncio.TimeoutError, TimeoutError):
            return done("timeout", f"no answer from {self.model} within {self.timeout:g}s")
        except Exception as exc:  # noqa: BLE001 - the coach answers without it
            name = type(exc).__name__
            if "Timeout" in name:
                return done("timeout", f"{name} from {self.model}")
            return done("error", f"{name}: {str(exc).splitlines()[0][:160] if str(exc) else ''}")

