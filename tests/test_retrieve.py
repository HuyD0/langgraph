"""Retrieval for questions that come with no lesson (drill.server.retrieve), all offline.

The embedding model here is a fake: it counts words into a fixed list of numbers, so a question that
shares words with a paragraph lands next to it. What these tests check is the plumbing: vectors built
once and read back, the top paragraphs, the time limit, failures that leave the answer alone, what is
recorded, and that the private use-case helper never retrieves.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import time

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from drill.embedding_compare import BGE_QUERY
from drill.server import mcp as mcp_door
from drill.server import retrieve
from drill.server.api import create_app
from drill.server.bank import Bank
from drill.server.observe import RecordingObserver
from drill.server.retrieve import DatabricksEmbedder, Retriever
from drill.server.router import ModelRouter, Route
from drill.server.store import DocStore

DATA = {
    "modules": [{"id": "rag", "lessons": ["chunking", "vector_index"]}, {"id": "ops", "lessons": ["tracing"]}],
    "lessons": {
        "chunking": {"title": "Chunking documents", "learn": [
            "Chunking cuts long documents into pieces small enough to embed and search.",
            "Overlap between chunks keeps a sentence from being cut in half.",
        ]},
        "vector_index": {"title": "Finding neighbours fast", "learn": [
            "A vector index finds the nearest vectors without comparing every one.",
        ]},
        "tracing": {"title": "Traces and spans", "learn": [
            "A trace records one request; each step inside it is a span with its own timing.",
            "",  # blank paragraphs are not searched
        ]},
    },
}


class WordCounter:
    """A fake embedding model: each word adds one to a slot picked by its hash. No network."""

    model = "fake-bge"

    def __init__(self, slow_query: float = 0.0, fail_query: bool = False):
        self.calls: list[list[str]] = []
        self.slow_query, self.fail_query = slow_query, fail_query

    def ready(self) -> str:
        return ""

    def embed(self, texts, timeout=300):
        self.calls.append(list(texts))
        is_query = any(t.startswith(BGE_QUERY) for t in texts)
        if is_query and self.fail_query:
            raise ConnectionError("endpoint refused")
        if is_query and self.slow_query:
            time.sleep(self.slow_query)
        out = []
        for text in texts:
            v = [0.0] * 64
            for word in re.findall(r"[a-z]+", text.removeprefix(BGE_QUERY).lower()):
                v[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
            out.append(v)
        return out


class Echo:
    """A chat model that remembers what it was sent and answers one fixed line."""

    def __init__(self):
        self.seen: list = []

    async def astream(self, messages, *args, **kwargs):
        self.seen.append(messages)
        yield AIMessage(content="An answer.")


@pytest.fixture
def store(tmp_path) -> DocStore:
    return DocStore(f"sqlite:///{tmp_path / 'drill.db'}")


@pytest.fixture(scope="module")
def bank() -> Bank:
    return Bank.load()


def built(tmp_path, embedder=None, **kw) -> Retriever:
    r = Retriever(DATA, embedder or WordCounter(), cache_dir=tmp_path / "retrieval", **kw)
    assert r.build()
    return r


# -- the module on its own ---------------------------------------------------------


def test_every_learn_paragraph_is_embedded_once_and_read_back(tmp_path):
    first = WordCounter()
    r = built(tmp_path, first)
    assert len(r.chunks) == 4 and len(first.calls) == 1, "one batch; the blank paragraph is skipped"
    assert not any(t.startswith(BGE_QUERY) for t in first.calls[0]), "no prompt before a paragraph"
    [saved] = (tmp_path / "retrieval").glob("*.npy")
    assert saved.name.startswith("fake-bge-")

    again = WordCounter()
    assert built(tmp_path, again).ready and again.calls == [], "the same lessons and model: read from disk"

    changed = {**DATA, "lessons": {**DATA["lessons"], "chunking": {"title": "Chunking documents", "learn": ["New text."]}}}
    assert retrieve.fingerprint(Retriever(changed).chunks, "fake-bge") != retrieve.fingerprint(r.chunks, "fake-bge")
    assert retrieve.fingerprint(r.chunks, "other") != retrieve.fingerprint(r.chunks, "fake-bge")


def test_a_question_finds_its_lessons_paragraphs_first(tmp_path):
    embedder = WordCounter()
    r = built(tmp_path, embedder)
    found = asyncio.run(r.search("what does a vector index do with the nearest vectors?"))
    assert found.state == "on" and found.model == "fake-bge"
    assert found.hits[0]["lesson"] == "vector_index" and found.hits[0]["title"] == "Finding neighbours fast"
    assert len(found.hits) == 4, "k is 5; there are only four paragraphs"
    assert found.lessons[0] == "vector_index" and len(found.lessons) == len(set(found.lessons))
    assert embedder.calls[-1] == [BGE_QUERY + "what does a vector index do with the nearest vectors?"], "the search prompt goes first"
    detail = found.detail()
    assert detail["retrieval"] == "on" and detail["retrieved"] == found.lessons and isinstance(detail["retrieval_ms"], int)
    assert detail["retrieved_paragraphs"][0] == "vector_index#0"
    span = found.trace()
    assert span["query"].startswith("what does") and span["documents"][0]["metadata"]["lesson_id"] == "vector_index"
    assert span["ended_ns"] >= span["started_ns"] > 0


def test_found_paragraphs_go_in_front_of_the_last_message_with_their_titles(tmp_path):
    from langchain_core.messages import HumanMessage, SystemMessage

    found = asyncio.run(built(tmp_path).search("chunk overlap"))
    messages = [SystemMessage(content="rules"), HumanMessage(content="first"), HumanMessage(content="Their new question: chunk overlap")]
    out = retrieve.with_found(messages, found.hits[:2])
    assert out[0] is messages[0] and out[1] is messages[1]
    assert out[2].content.startswith(retrieve.INTRO) and out[2].content.endswith("Their new question: chunk overlap")
    assert "Lesson: Chunking documents" in out[2].content
    assert retrieve.with_found(messages, []) == messages


def test_off_means_never_and_no_question_means_no_search(tmp_path):
    off = Retriever(DATA, WordCounter(), mode="off")
    assert not off.build() and asyncio.run(off.search("anything")).state == "off"
    r = built(tmp_path)
    nothing = asyncio.run(r.search("   "))
    assert (nothing.state, nothing.why, nothing.hits) == ("off", "no question to search with", [])


def test_before_the_paragraphs_are_ready_the_coach_goes_without_and_building_starts(tmp_path):
    class Waits(WordCounter):
        def embed(self, texts, timeout=300):
            time.sleep(0.2)
            return super().embed(texts, timeout)

    r = Retriever(DATA, Waits(), cache_dir=tmp_path)
    found = asyncio.run(r.search("vector index"))
    assert (found.state, found.why) == ("off", "still embedding the lessons")
    r._building.join(5)
    assert r.ready and asyncio.run(r.search("vector index")).state == "on"


def test_no_model_is_off_in_auto_and_an_error_when_asked_for(tmp_path):
    class Missing(WordCounter):
        def ready(self):
            return "bge-large is not pulled in Ollama (ollama pull bge-large)"

    auto = Retriever(DATA, Missing(), cache_dir=tmp_path)
    assert not auto.build()
    assert asyncio.run(auto.search("x")).state == "off"
    on = Retriever(DATA, Missing(), mode="on", cache_dir=tmp_path)
    on.build()
    found = asyncio.run(on.search("x"))
    assert found.state == "error" and "ollama pull" in found.why


def test_a_retry_while_the_model_is_still_missing_is_still_an_error_when_asked_for(tmp_path):
    class Missing(WordCounter):
        def ready(self):
            time.sleep(0.1)  # a real check is a network call: the ask is recorded before it answers
            return "Ollama is not running"

    on = Retriever(DATA, Missing(), mode="on", cache_dir=tmp_path)
    on.build()
    on._next_try = 0.0  # the minute before the next try has passed
    found = asyncio.run(on.search("x"))
    assert on._building is not None, "a retry started"
    assert (found.state, found.why) == ("error", "Ollama is not running"), "not 'still embedding': nothing is"
    on._building.join(5)
    auto = Retriever(DATA, Missing(), cache_dir=tmp_path)
    auto.build()
    auto._next_try = 0.0
    assert (asyncio.run(auto.search("x")).state, auto.why) == ("off", "Ollama is not running")
    auto._building.join(5)


@pytest.mark.parametrize("value, mode", [
    ("off", "off"), ("0", "off"), ("false", "off"), ("No", "off"), ("on", "on"), ("1", "on"), ("TRUE", "on"),
    ("yes", "on"), ("auto", "auto"), ("", "auto"), (None, "auto"), ("sometimes", "auto"),
])
def test_retrieval_reads_the_same_words_as_tracing(value, mode):
    assert retrieve.mode_from(value) == mode


def test_an_unknown_retrieval_setting_says_so_in_the_log(monkeypatch, caplog):
    monkeypatch.delenv("DATABRICKS_APP_NAME", raising=False)
    monkeypatch.setenv("DRILL_RETRIEVAL", "0")
    assert Retriever.from_env(DATA).embedder is None, "0 turns it off, so nothing is embedded"
    monkeypatch.setenv("DRILL_RETRIEVAL", "sometimes")
    with caplog.at_level("WARNING", logger="drill.server"):
        assert Retriever.from_env(DATA).mode == "auto"
    assert "DRILL_RETRIEVAL='sometimes'" in caplog.text


def test_fewer_paragraphs_are_kept_until_they_fit(tmp_path):
    found = asyncio.run(built(tmp_path).search("vector index nearest vectors"))
    first_two = [h["id"] for h in found.hits[:2]]
    kept = retrieve.fit(found, lambda hits: len(hits) <= 2)
    assert [h["id"] for h in kept.hits] == first_two and kept.state == "on", "the lowest-ranked go first"
    none = retrieve.fit(asyncio.run(built(tmp_path).search("vector index")), lambda hits: False)
    assert (none.hits, none.state, none.why) == ([], "off", "no room in the prompt")
    empty = retrieve.fit(retrieve.Found("timeout", why="slow"), lambda hits: False)
    assert (empty.state, empty.why) == ("timeout", "slow"), "nothing found: nothing about room is recorded"


def test_a_slow_model_is_cut_off_at_the_time_limit(tmp_path):
    r = built(tmp_path, WordCounter(slow_query=1.0), timeout=0.1)
    found = asyncio.run(r.search("vector index"))  # asyncio.run then waits for the sleeping thread; a server does not
    assert found.state == "timeout" and found.hits == [] and found.ms < 800, "the search gave up at the limit"
    assert "0.1s" in found.why


def test_a_failing_model_is_recorded_not_raised(tmp_path):
    found = asyncio.run(built(tmp_path, WordCounter(fail_query=True)).search("vector index"))
    assert found.state == "error" and "ConnectionError" in found.why and found.hits == []


def test_the_use_case_helper_and_lesson_pages_never_retrieve():
    assert retrieve.applies("ask_study_item", "") and retrieve.applies("", "")
    assert not retrieve.applies("ask_lesson", "chunking"), "a lesson the page sent is never replaced"
    assert not retrieve.applies("use_case_review", "") and not retrieve.applies("use_case_skill", "")


def test_the_databricks_endpoint_is_signed_by_the_login_and_called_by_name():
    import httpx

    sent = []

    def answer(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json={"data": [{"index": 1, "embedding": [0.0, 1.0]}, {"index": 0, "embedding": [1.0, 0.0]}]})

    class Config:
        host = "https://adb-1.azuredatabricks.net"

        def authenticate(self):
            return {"Authorization": "Bearer short-lived"}

    endpoint = DatabricksEmbedder(config_factory=Config, transport=httpx.MockTransport(answer))
    assert endpoint.ready() == "" and endpoint.model == "databricks-bge-large-en"
    assert endpoint.embed(["a", "b"]) == [[1.0, 0.0], [0.0, 1.0]], "rows come back in input order"
    assert str(sent[0].url) == "https://adb-1.azuredatabricks.net/serving-endpoints/databricks-bge-large-en/invocations"
    assert sent[0].headers["authorization"] == "Bearer short-lived"
    service = DatabricksEmbedder("system.ai.bge-large-en", config_factory=Config, transport=httpx.MockTransport(answer))
    service.embed(["a", "b"])
    assert str(sent[1].url) == "https://adb-1.azuredatabricks.net/ai-gateway/mlflow/v1/embeddings"
    assert b'"model":"system.ai.bge-large-en"' in sent[1].content.replace(b" ", b"")


def test_the_app_uses_the_endpoint_setting_and_this_computer_uses_ollama(monkeypatch):
    monkeypatch.delenv("DATABRICKS_APP_NAME", raising=False)
    assert isinstance(retrieve.choose_embedder(), retrieve.OllamaEmbedder)
    monkeypatch.setenv("DATABRICKS_APP_NAME", "daily-drill")
    assert retrieve.choose_embedder().model == "databricks-bge-large-en"
    monkeypatch.setenv("DRILL_EMBEDDING_ENDPOINT", "system.ai.bge-large-en")
    assert retrieve.choose_embedder().model == "system.ai.bge-large-en"
    monkeypatch.setenv("DRILL_RETRIEVAL", "off")
    assert Retriever.from_env(DATA).embedder is None


# -- through the server ---------------------------------------------------------------


def server(store, bank, retriever, **router_kw):
    chat, observer = Echo(), RecordingObserver()
    router = ModelRouter(Route("local", "fake", chat), None, store, observer=observer, **router_kw)
    client = TestClient(create_app(store=store, router=router, bank=bank, with_mcp=False, retriever=retriever))
    return client, chat, observer


STUDY_ASK = {"prompt": "They saved this: a vector index\n\nTheir new question: how does it find the nearest vectors?",
             "trace": {"feature": "ask_study_item", "lesson_id": "", "question": "how does it find the nearest vectors?",
                       "session": "study-s1"}}


def test_a_study_list_question_with_no_lesson_gets_the_paragraphs_and_says_so(store, bank, tmp_path):
    client, chat, observer = server(store, bank, built(tmp_path))
    response = client.post("/api/ask", json=STUDY_ASK)
    assert response.status_code == 200 and response.text == "An answer."
    sent = chat.seen[0][-1].content
    assert sent.startswith(retrieve.INTRO) and "Lesson: Finding neighbours fast" in sent and sent.endswith("nearest vectors?")
    [event] = [e for e in store.events() if e["kind"] == "asked"]
    d = event["detail"]
    assert (d["feature"], d["retrieval"], d["retrieval_model"]) == ("ask_study_item", "on", "fake-bge")
    assert d["retrieved"][0] == "vector_index" and d["question"].startswith("how does")
    [record] = observer.records
    assert record["retrieval"]["retrieved"] == d["retrieved"] and "retrieval" not in record["context"]


def test_a_question_on_a_lesson_is_unchanged(store, bank, tmp_path):
    embedder = WordCounter()
    client, chat, _ = server(store, bank, built(tmp_path, embedder))
    calls = len(embedder.calls)
    body = {"prompt": "Lesson: Chunking\nTheir message: why overlap?",
            "trace": {"feature": "ask_lesson", "lesson_id": "chunking", "step": "Learn", "question": "why overlap?"}}
    assert client.post("/api/ask", json=body).text == "An answer."
    assert chat.seen[0][-1].content == body["prompt"] and len(embedder.calls) == calls, "no search, nothing added"
    [event] = [e for e in store.events() if e["kind"] == "asked"]
    assert not any(k.startswith("retriev") for k in event["detail"])


@pytest.mark.parametrize("embedder, state", [(WordCounter(fail_query=True), "error"), (WordCounter(slow_query=1.0), "timeout")])
def test_a_failed_or_slow_search_still_answers(store, bank, tmp_path, embedder, state):
    client, chat, _ = server(store, bank, built(tmp_path, embedder, timeout=0.1))
    response = client.post("/api/ask", json=STUDY_ASK)
    assert response.status_code == 200 and response.text == "An answer."
    assert chat.seen[0][-1].content == STUDY_ASK["prompt"], "answered as before, with nothing added"
    [event] = [e for e in store.events() if e["kind"] == "asked"]
    assert event["detail"]["retrieval"] == state and event["detail"]["retrieved"] == [] and event["detail"]["retrieval_why"]


def test_the_private_use_case_helper_never_retrieves_or_records_it(store, bank, tmp_path):
    embedder = WordCounter()
    client, chat, observer = server(store, bank, built(tmp_path, embedder))
    calls = len(embedder.calls)
    body = {"prompt": "Review my use case card", "trace": {"feature": "use_case_review", "question": "my card"}}
    assert client.post("/api/ask", json=body).status_code == 200
    assert len(embedder.calls) == calls and chat.seen[0][-1].content == body["prompt"]
    [event] = [e for e in store.events() if e["kind"] == "asked"]
    assert not any(k.startswith("retriev") for k in event["detail"]) and observer.records[0]["retrieval"] is None


def test_the_found_text_never_makes_a_question_too_big(store, bank, tmp_path):
    from drill.server.guard import TUTOR_RULES

    size = len(TUTOR_RULES) + len(STUDY_ASK["prompt"])  # what the model is sent without retrieval
    client, chat, _ = server(store, bank, built(tmp_path), max_prompt_chars=size + 450)
    assert client.post("/api/ask", json=STUDY_ASK).status_code == 200
    [event] = [e for e in store.events() if e["kind"] == "asked"]
    assert event["detail"]["retrieval"] == "on" and 0 < len(event["detail"]["retrieved_paragraphs"]) < 4, "fewer paragraphs fit"
    assert len(chat.seen[0][-1].content) + len(TUTOR_RULES) <= size + 450
    tight, chat2, _ = server(store, bank, built(tmp_path), max_prompt_chars=size + 100)
    assert tight.post("/api/ask", json=STUDY_ASK).status_code == 200
    last = [e for e in store.events() if e["kind"] == "asked"][-1]["detail"]
    assert (last["retrieval"], last["retrieval_why"], last["retrieved"]) == ("off", "no room in the prompt", [])
    assert chat2.seen[0][-1].content == STUDY_ASK["prompt"]


FORGED = [
    {"feature": "ask_lesson", "lesson_id": "chunking", "question": "why overlap?", "retrieval": "boom"},
    {"feature": "ask_lesson", "lesson_id": "chunking", "question": "why overlap?",
     "retrieval": {"retrieval": "on", "query": "made up", "started_ns": "soon", "documents": [{"page_content": "fake"}]}},
    {"feature": "use_case_review", "question": "my card", "retrieval": {"retrieval": "on", "documents": [{"page_content": "x"}]}},
]


@pytest.mark.parametrize("trace", FORGED)
def test_a_retrieval_record_sent_by_the_page_is_dropped(store, bank, tmp_path, trace):
    embedder = WordCounter()
    client, chat, observer = server(store, bank, built(tmp_path, embedder))
    calls = len(embedder.calls)
    assert client.post("/api/ask", json={"prompt": "why?", "trace": trace}).status_code == 200
    assert len(embedder.calls) == calls and chat.seen[0][-1].content == "why?", "no search, nothing added"
    [record] = observer.records
    assert record["retrieval"] is None, "only the server records what retrieval found"


def test_the_observer_takes_only_the_servers_own_retrieval_record():
    from drill.server.observe import retrieval_record

    assert retrieval_record(None) is None and retrieval_record({"retrieval": "boom"}) is None
    assert retrieval_record({"retrieval": {}}) is None and retrieval_record({"retrieval": ["on"]}) is None
    record = retrieval_record({"retrieval": {"retrieval": "on", "started_ns": "12", "ended_ns": "later"}})
    assert (record["started_ns"], record["ended_ns"]) == (12, 0), "times are whole numbers or nothing"


def test_a_forged_retrieval_record_neither_stops_tracing_nor_adds_a_span(store, bank, tmp_path, monkeypatch):
    import mlflow

    from drill.server import observe

    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
    monkeypatch.setenv("DRILL_TRACING", "1")
    monkeypatch.setenv("DRILL_MLFLOW_EXPERIMENT", "drill-forged-retrieval-test")
    mlflow.set_tracking_uri(uri)
    try:
        observer = observe.MlflowObserver()
        router = ModelRouter(Route("local", "fake", Echo()), None, store, observer=observer)
        client = TestClient(create_app(store=store, router=router, bank=bank, with_mcp=False, retriever=built(tmp_path)))
        for trace in FORGED:
            assert client.post("/api/ask", json={"prompt": "why?", "trace": trace}).status_code == 200
            assert observer.enabled, "a bad value from the page never switches tracing off for everyone"
        observer.drain()
        mlflow.flush_trace_async_logging()
        experiment_id = mlflow.get_experiment_by_name("drill-forged-retrieval-test").experiment_id
        infos = mlflow.search_traces(locations=[experiment_id], return_type="list")
        assert len(infos) == len(FORGED)
        for info in infos:
            trace = mlflow.get_trace(info.info.trace_id)
            assert not [s for s in trace.data.spans if s.span_type == "RETRIEVER"] and "retrieval" not in trace.info.tags
    finally:
        mlflow.clear_active_model()
        mlflow.set_tracking_uri(None)


def test_health_says_whether_retrieval_is_ready(store, bank, tmp_path):
    client, _, _ = server(store, bank, built(tmp_path))
    assert client.get("/api/health").json()["retrieval"] == {"mode": "auto", "model": "fake-bge", "ready": True, "paragraphs": 4}


def test_claudes_ask_tutor_retrieves_and_records_the_question(store, bank, tmp_path):
    chat = Echo()
    mcp_door.configure(store=store, router=ModelRouter(Route("local", "fake", chat), None, store), bank=bank,
                       retriever=built(tmp_path))
    try:
        assert asyncio.run(mcp_door.ask_tutor("how does a trace record each span?")) == "An answer."
    finally:
        mcp_door.configure()
    sent = chat.seen[0][-1].content
    assert "Lesson: Traces and spans" in sent and sent.endswith("how does a trace record each span?")
    [event] = [e for e in store.events() if e["kind"] == "asked"]
    d = event["detail"]
    assert (d["door"], d["feature"], d["retrieval"], d["retrieved"][0]) == ("mcp", "ask_tutor", "on", "tracing")


def test_claudes_ask_tutor_keeps_the_paragraphs_that_fit(store, bank, tmp_path):
    from drill.server import tutor
    from drill.server.router import PromptTooLong

    question = "how does a trace record each span?"
    size = len(tutor.LEARNER) + 2 + len(question)  # what the tutor is sent without retrieval

    def ask(max_chars: int, prompt: str = question) -> Echo:
        chat = Echo()
        router = ModelRouter(Route("local", "fake", chat), None, store, max_prompt_chars=max_chars)
        mcp_door.configure(store=store, router=router, bank=bank, retriever=built(tmp_path))
        try:
            asyncio.run(mcp_door.ask_tutor(prompt))
        finally:
            mcp_door.configure()
        return chat

    chat = ask(size + 350)
    d = [e for e in store.events() if e["kind"] == "asked"][-1]["detail"]
    assert d["retrieval"] == "on" and 0 < len(d["retrieved_paragraphs"]) < 4, "fewer paragraphs, not none"
    assert len(chat.seen[0][-1].content) <= size + 350 and "Lesson: Traces and spans" in chat.seen[0][-1].content
    ask(size + 50)
    d = [e for e in store.events() if e["kind"] == "asked"][-1]["detail"]
    assert (d["retrieval"], d["retrieval_why"], d["retrieved"]) == ("off", "no room in the prompt", [])
    asked = len([e for e in store.events() if e["kind"] == "asked"])
    with pytest.raises(PromptTooLong):
        ask(size - 1)  # the question alone is too long: refused before any search, and nothing blamed on retrieval
    assert len([e for e in store.events() if e["kind"] == "asked"]) == asked


def test_drill_mcp_starts_the_retriever_when_it_launches(monkeypatch):
    import dotenv

    order = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(mcp_door, "_retriever", lambda: order.append("retriever"))
    monkeypatch.setattr(mcp_door.server, "run", lambda transport: order.append(transport))
    mcp_door.main()
    assert order == ["retriever", "stdio"], "the vectors are read before the first ask_tutor, not during it"


def test_the_trace_has_a_retriever_span(store, bank, tmp_path, monkeypatch):
    import mlflow

    from drill.server import observe

    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
    monkeypatch.setenv("DRILL_TRACING", "1")
    monkeypatch.setenv("DRILL_MLFLOW_EXPERIMENT", "drill-retrieval-test")
    mlflow.set_tracking_uri(uri)
    try:
        observer = observe.MlflowObserver()
        router = ModelRouter(Route("local", "fake", Echo()), None, store, observer=observer)
        client = TestClient(create_app(store=store, router=router, bank=bank, with_mcp=False, retriever=built(tmp_path)))
        client.post("/api/ask", json=STUDY_ASK)
        observer.drain()
        mlflow.flush_trace_async_logging()
        experiment_id = mlflow.get_experiment_by_name("drill-retrieval-test").experiment_id
        [info] = mlflow.search_traces(locations=[experiment_id], return_type="list")
        trace = mlflow.get_trace(info.info.trace_id)
        [span] = [s for s in trace.data.spans if s.span_type == "RETRIEVER"]
        assert span.inputs == {"query": STUDY_ASK["trace"]["question"]}
        assert span.outputs[0]["metadata"]["lesson_id"] == "vector_index" and span.attributes["retrieval"] == "on"
        assert span.attributes["retrieval_model"] == "fake-bge" and span.attributes["retrieved"][0] == "vector_index"
        assert trace.info.tags["retrieval"] == "on"
        root = next(s for s in trace.data.spans if s.parent_id is None)
        assert root.start_time_ns <= span.start_time_ns, "the trace starts when the search did"
    finally:
        mlflow.clear_active_model()
        mlflow.set_tracking_uri(None)
