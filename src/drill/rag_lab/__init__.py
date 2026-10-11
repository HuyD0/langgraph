"""A small help-center RAG app, used by notebook milestones 9a-9d.

It is deliberately small enough to read in one sitting, and complete enough to run a real
experiment on: a keyword search over 24 help articles, an optional query rewrite and
reranker, and a model that answers from the articles it is given. Every request is an
MLflow trace with typed spans (RETRIEVER, RERANKER, CHAT_MODEL), tagged with its variant
and question id, so the notebooks can look inside the runs as well as score them.

Model calls go to a local Ollama when one is running. Otherwise they are replayed from
answers recorded on a MacBook Pro (``recorded.json``), keyed by step, variant, run and
question, so every notebook works offline and the test suite gives the same result
everywhere.
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "data.json").read_text(encoding="utf-8"))

KB = DATA["kb"]                      # id -> {"title", "text"}
QUESTIONS = DATA["questions"]        # [{"id", "group", "question", "gold", "facts"}]
MUST_PASS = DATA["must_pass"]
TRAFFIC = DATA["traffic"]
NEW_KB = DATA["new_kb"]
NEW_QUESTIONS = DATA["new_questions"]
BY_ID = {q["id"]: q for q in QUESTIONS + NEW_QUESTIONS}

OLLAMA = "http://localhost:11434"
MODEL = "gemma3:12b"

VARIANTS = {
    "v1": "keyword search, top 3 articles",
    "v2": "rewrite the question, keyword search top 10, rerank to 3",
    "v2-no-rewrite": "keyword search top 10, rerank to 3 (v2 with the rewrite removed)",
    "oracle": "the right article handed over directly (perfect retrieval)",
}

DECLINE = "I don't know based on the help center."

ANSWER_PROMPT = """You answer customer questions using only the help-center articles below.
Include the specific numbers, timeframes and menu paths from the articles.
If the articles don't contain the answer, reply exactly: {decline}
Keep it under 60 words.

{articles}

Question: {question}"""

REWRITE_PROMPT = """Rewrite this customer question as a short search query, using the words a
help-center article about it would use. Reply with the query only, no quotes.

Question: {question}"""

RERANK_PROMPT = """Here is a customer question and some help-center articles.
Pick the {k} articles most useful for answering it, most useful first.
Reply with JSON only, like {{"ids": ["kb-07", "kb-08", "kb-09"]}}.

Question: {question}

{articles}"""


def ollama_is_running() -> bool:
    if os.getenv("DRILL_NOTEBOOK_OFFLINE") == "1":
        return False
    try:
        urllib.request.urlopen(OLLAMA + "/api/version", timeout=1)
        return True
    except OSError:
        return False


# ----------------------------------------------------------------------------- search

_STOP = set("""a an and are as at be but by can do does for from how i if in is it its me my
of on or so that the their them then there this to was we what when where which who why will
with you your yours i'm it's i've don't didn't isn't""".split())  # noqa: SIM905


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9$%]+(?:[.@][a-z0-9]+)*", text.lower().replace("'", ""))
    return [w for w in words if w not in _STOP and len(w) > 1]


class Index:
    """TF-IDF keyword search: rare words that match count most. No embeddings, no downloads."""

    def __init__(self, kb: dict):
        self.kb = kb
        docs = {i: tokens(a["title"] + " " + a["text"]) for i, a in kb.items()}
        df: dict[str, int] = {}
        for words in docs.values():
            for w in set(words):
                df[w] = df.get(w, 0) + 1
        n = len(docs)
        self.idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in df.items()}
        self.vectors = {i: self._vector(words) for i, words in docs.items()}

    def _vector(self, words: list[str]) -> dict[str, float]:
        tf: dict[str, float] = {}
        for w in words:
            tf[w] = tf.get(w, 0) + 1
        vec = {w: c * self.idf.get(w, 0.0) for w, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {w: v / norm for w, v in vec.items()}

    def search(self, query: str, k: int) -> list[str]:
        q = self._vector(tokens(query))
        scored = [(sum(q.get(w, 0.0) * v for w, v in vec.items()), i) for i, vec in self.vectors.items()]
        scored.sort(key=lambda s: (-s[0], s[1]))
        return [i for score, i in scored[:k]]


# ----------------------------------------------------------------------------- scoring


def normalise(text: str) -> str:
    text = text.lower().replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text)


def declined(answer: str) -> bool:
    return bool(re.search(r"don't know|do not know|isn't covered|not covered|no information|doesn't (say|mention|cover)", normalise(answer)))


def has_facts(answer: str, facts: list[str]) -> bool:
    """Every fact must appear; a fact may list acceptable wordings separated by " | "."""
    text = normalise(answer)
    return all(any(normalise(alt.strip()) in text for alt in fact.split("|")) for fact in facts)


def score(answer: str, question: dict) -> bool:
    """Pass if it declines an unanswerable question, or answers an answerable one with every fact."""
    if not question["facts"]:
        return declined(answer)
    return not declined(answer) and has_facts(answer, question["facts"])


def parse_ranking(reply: str, candidates: list[str], k: int) -> list[str]:
    """The reranker's ids in its order, keeping only real candidates, topped up from the original order."""
    ids = re.findall(r"kb-\d+", reply)
    ranked: list[str] = []
    for i in ids + candidates:
        if i in candidates and i not in ranked:
            ranked.append(i)
    return ranked[:k]


def articles_block(kb: dict, ids: list[str]) -> str:
    if not ids:
        return "(no articles found)"
    return "\n\n".join(f"[{i}] {kb[i]['title']}\n{kb[i]['text']}" for i in ids)


# ----------------------------------------------------------------------------- the app


class Lab:
    """One session of the help-center app: its knowledge base, search index and model calls."""

    def __init__(self, live: bool | None = None, model: str = MODEL):
        self.live = ollama_is_running() if live is None else live
        self.model = model
        self.kb = dict(KB)
        self.index = Index(self.kb)
        self.index_note = ""                       # changes the recording keys when the index changes
        self.session = uuid.uuid4().hex[:8]        # tags every trace from this session
        path, timing = HERE / "recorded.json", HERE / "recorded_ms.json"
        self.recorded = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.recorded_ms = json.loads(timing.read_text(encoding="utf-8")) if timing.exists() else {}
        self.new_recordings: dict[str, str] = {}
        self.new_ms: dict[str, int] = {}
        self.last_ms = 0                           # how long the last model call took (or took when recorded)

    # -- model calls ---------------------------------------------------------------

    def llm(self, key: str, prompt: str, temperature: float) -> str:
        if not self.live:
            if key not in self.recorded:
                raise KeyError(f"No recorded answer for {key!r}. Start Ollama to run this live.")
            self.last_ms = self.recorded_ms.get(key, 0)
            return self.recorded[key]
        started = time.perf_counter()
        body = {"model": self.model, "stream": False, "think": False,
                "options": {"temperature": temperature, "num_predict": 160},
                "messages": [{"role": "user", "content": prompt}]}
        request = urllib.request.Request(OLLAMA + "/api/chat", json.dumps(body).encode(),
                                         {"content-type": "application/json"})
        reply = json.load(urllib.request.urlopen(request, timeout=300))["message"]["content"].strip()
        self.last_ms = round((time.perf_counter() - started) * 1000)
        self.new_recordings[key] = reply
        self.new_ms[key] = self.last_ms
        return reply

    # -- knowledge base ------------------------------------------------------------

    def publish(self, articles: dict, reindex: bool):
        """Add articles to the help center. Search only finds them after a reindex."""
        self.kb.update(articles)
        if reindex:
            self.index = Index(self.kb)
            self.index_note = "reindexed"
        else:
            self.index_note = "stale-index"

    # -- one request -----------------------------------------------------------------

    def ask(self, question: dict, variant: str, run: int = 0, tags: dict | None = None) -> dict:
        import mlflow
        from mlflow.entities import SpanType

        qid, text, note = question["id"], question["question"], self.index_note
        suffix = f"|{note}" if note else ""
        with mlflow.start_span(name="support_app", span_type=SpanType.CHAIN) as root:
            root.set_inputs({"question": text})
            mlflow.update_current_trace(tags={"variant": variant, "qid": qid, "run": str(run),
                                              "session": self.session, **(tags or {})})
            query, candidates = text, []
            if variant == "v2":
                with mlflow.start_span(name="rewrite", span_type=SpanType.CHAT_MODEL) as span:
                    span.set_inputs({"question": text})
                    query = self.llm(f"rewrite|{qid}{suffix}", REWRITE_PROMPT.format(question=text), 0)
                    query = query.strip().strip('"').splitlines()[0]
                    span.set_attribute("model_ms", self.last_ms)
                    span.set_outputs({"query": query})
            if variant == "oracle":
                docs = [question["gold"]] if question["gold"] else []
            else:
                with mlflow.start_span(name="retrieve", span_type=SpanType.RETRIEVER) as span:
                    span.set_inputs({"query": query})
                    candidates = self.index.search(query, 3 if variant == "v1" else 10)
                    span.set_outputs([{"doc_id": i, "title": self.kb[i]["title"]} for i in candidates])
                docs = candidates
                if variant in ("v2", "v2-no-rewrite"):
                    with mlflow.start_span(name="rerank", span_type=SpanType.RERANKER) as span:
                        span.set_inputs({"question": text, "candidates": candidates})
                        prompt = RERANK_PROMPT.format(k=3, question=text, articles=articles_block(self.kb, candidates))
                        reply = self.llm(f"rerank|{variant}|{qid}{suffix}", prompt, 0)
                        docs = parse_ranking(reply, candidates, 3)
                        span.set_attribute("model_ms", self.last_ms)
                        span.set_outputs([{"doc_id": i, "title": self.kb[i]["title"]} for i in docs])
            with mlflow.start_span(name="answer", span_type=SpanType.CHAT_MODEL) as span:
                prompt = ANSWER_PROMPT.format(decline=DECLINE, articles=articles_block(self.kb, docs), question=text)
                span.set_inputs({"question": text, "doc_ids": docs})
                answer = self.llm(f"answer|{variant}|{run}|{qid}{suffix}", prompt, 0.5)
                span.set_attribute("model_ms", self.last_ms)
                span.set_outputs({"answer": answer})
            root.set_outputs({"answer": answer, "doc_ids": docs})
            trace_id = root.trace_id
        return {"qid": qid, "group": question["group"], "variant": variant, "run": run, "answer": answer,
                "docs": docs, "candidates": candidates, "passed": score(answer, question), "trace_id": trace_id}

    def run(self, questions: list[dict], variants: list[str], runs: int = 1, tags: dict | None = None,
            quiet: bool = False) -> list[dict]:
        """Every question through every variant, `runs` times. Prints progress when live."""
        import mlflow

        results = []
        total = len(questions) * len(variants) * runs
        for variant in variants:
            mlflow.set_active_model(name=f"support-{variant}")
            for run in range(runs):
                for q in questions:
                    results.append(self.ask(q, variant, run, tags))
                    if self.live and not quiet and len(results) % 25 == 0:
                        print(f"  {len(results)} of {total} requests done")
        mlflow.flush_trace_async_logging()
        return results


# ----------------------------------------------------------------------------- notebook helpers


def use_mlflow(name: str) -> str:
    """Point MLflow at a local store for the milestone 9 notebooks and return its URI.

    Under the test suite (DRILL_NOTEBOOK_OFFLINE=1) it uses a fresh temporary folder;
    otherwise ``.drill/m9/mlflow.db`` in the repo, which you can browse with ``mlflow ui``.
    """
    import mlflow

    if os.getenv("DRILL_NOTEBOOK_OFFLINE") == "1":
        folder = Path(tempfile.mkdtemp(prefix="drill-m9-"))
    else:
        from drill.config import PROJECT_ROOT

        folder = PROJECT_ROOT / ".drill" / "m9"
        folder.mkdir(parents=True, exist_ok=True)
    uri = f"sqlite:///{folder / 'mlflow.db'}"
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(name)
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    return uri


def split_of(question_ids_by_group: dict) -> dict:
    """The milestone 9 split: deal each group's questions 3-1-1 into dev, test and holdout."""
    pattern = ["dev", "dev", "dev", "test", "holdout"]
    split = {}
    for ids in question_ids_by_group.values():
        for n, qid in enumerate(ids):
            split[qid] = pattern[n % len(pattern)]
    return split


def default_split() -> dict:
    groups: dict[str, list[str]] = {}
    for q in QUESTIONS:
        groups.setdefault(q["group"], []).append(q["id"])
    return split_of(groups)


def save_recordings(lab: Lab, path: Path | None = None) -> int:
    """Merge a live session's model replies into recorded.json (used to refresh the recordings)."""
    path = path or HERE / "recorded.json"
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    current.update(lab.new_recordings)
    path.write_text(json.dumps(current, indent=0, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    timing = path.with_name("recorded_ms.json")
    ms = json.loads(timing.read_text(encoding="utf-8")) if timing.exists() else {}
    ms.update(lab.new_ms)
    timing.write_text(json.dumps(ms, indent=0, sort_keys=True), encoding="utf-8")
    return len(current)


def results_path() -> Path:
    from drill.config import PROJECT_ROOT

    return PROJECT_ROOT / ".drill" / "m9" / "experiment.json"


def save_results(results: list[dict], lab: Lab) -> Path | None:
    """Keep a live experiment's results for 9c. Recorded (offline) runs need no saving."""
    if not lab.live or os.getenv("DRILL_NOTEBOOK_OFFLINE") == "1":
        return None
    path = results_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"session": lab.session, "results": results}), encoding="utf-8")
    return path


def load_results() -> dict | None:
    """The last live experiment from 9b, if there is one."""
    path = results_path()
    if os.getenv("DRILL_NOTEBOOK_OFFLINE") == "1" or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def model_ms(trace) -> int:
    """Total model time in one traced request, from the steps' recorded timings."""
    return sum(int(span.attributes.get("model_ms") or 0) for span in trace.data.spans)
