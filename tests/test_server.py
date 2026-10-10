"""The local tutor server: document store, model router, web API and MCP tools, all offline.

No Ollama, no Azure: the "models" here are LangChain's fake chat model and a deliberately
broken one, so these tests run anywhere. What they check is the routing and the plumbing -
local first, fallback, cache, budget, the page's document protocol - not the prose.
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from drill.server import mcp as mcp_door
from drill.server.api import create_app
from drill.server.bank import Bank
from drill.server.router import ModelRouter, NoModelAvailable, Route, parse_json, pick_local_model, strip_thinking
from drill.server.store import DocStore


def fake(*replies: str) -> GenericFakeChatModel:
    """A chat model that returns these replies in order, then fails: one reply per call."""
    return GenericFakeChatModel(messages=iter([AIMessage(content=r) for r in replies]))


class Broken:
    """A chat model whose server is down."""

    async def astream(self, *args, **kwargs):
        raise ConnectionError("connection refused")
        yield  # pragma: no cover - makes this an async generator


class ThinkingForever:
    """A model that keeps producing thinking tokens and never gets to an answer."""

    def __init__(self):
        self.closed = False

    async def astream(self, *args, **kwargs):
        try:
            while True:
                await asyncio.sleep(0.02)
                yield AIMessage(content="")  # reasoning arrives in a side field; the answer never starts
        finally:
            self.closed = True


class SlowButTalking:
    """A model whose first word is quick, then takes its time: it must not be cut off."""

    async def astream(self, *args, **kwargs):
        for word in ("slow", " and", " steady"):
            yield AIMessage(content=word)
            await asyncio.sleep(0.15)


@pytest.fixture
def store(tmp_path) -> DocStore:
    return DocStore(f"sqlite:///{tmp_path / 'drill.db'}")


@pytest.fixture(scope="module")
def bank() -> Bank:
    return Bank.load()


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# store
# ---------------------------------------------------------------------------


def test_store_roundtrip(store):
    assert store.get("study/a") is None
    store.set("study/a", {"text": "MERGE", "createdAt": 1})
    store.set("study/b", {"text": "idempotent", "createdAt": 2})
    store.set("study/a/nested", {"ignored": True})  # not a direct child of study/
    assert store.get("study/a") == {"text": "MERGE", "createdAt": 1}
    assert store.update("study/a", {"status": "got"}) == {"text": "MERGE", "createdAt": 1, "status": "got"}
    ids = [doc_id for doc_id, _ in store.list("study")]
    assert ids[0] == "a" and set(ids) == {"a", "b"}  # newest write first, nested doc excluded
    store.delete("study/a")
    assert store.get("study/a") is None
    assert store.kind == "sqlite"


# ---------------------------------------------------------------------------
# router
# ---------------------------------------------------------------------------


def test_local_answers_first(store):
    router = ModelRouter(Route("local", "fake-local", fake("local says hi")), Route("hosted", "fake-hosted", fake("hosted says hi")), store)
    answer = run(router.ask("hello"))
    assert (answer.text, answer.route) == ("local says hi", "local")


def test_complex_jobs_start_with_the_hosted_model(store):
    router = ModelRouter(Route("local", "l", fake("local")), Route("hosted", "h", fake("hosted")), store)
    assert run(router.ask("review this", tier="complex")).route == "hosted"


def test_falls_back_when_local_is_down(store):
    router = ModelRouter(Route("local", "l", Broken()), Route("hosted", "h", fake("hosted to the rescue")), store)
    answer = run(router.ask("hello"))
    assert (answer.text, answer.route) == ("hosted to the rescue", "hosted")


def test_no_model_at_all(store):
    router = ModelRouter(None, None, store)
    assert router.order() == []
    with pytest.raises(NoModelAvailable):
        run(router.ask("hello"))


def test_same_prompt_is_served_from_the_cache(store):
    router = ModelRouter(Route("local", "l", fake("only one reply")), None, store)
    first = run(router.ask("same prompt"))
    second = run(router.ask("same prompt"))  # the fake has no second reply: only a cache hit can answer
    assert (first.cached, second.cached) == (False, True)
    assert second.text == "only one reply"


def test_hosted_budget_is_respected(store):
    router = ModelRouter(Route("local", "l", fake("local", "local")), Route("hosted", "h", fake("hosted")), store, hosted_daily_tokens=5)
    assert run(router.ask("a long question that costs more than five tokens", tier="complex")).route == "hosted"
    assert router.hosted_tokens_today() > 5
    assert run(router.ask("another complex question", tier="complex")).route == "local"


def test_streaming_grows_and_reports_who_answered(store):
    router = ModelRouter(Route("local", "gemma", fake("one two three")), None, store)

    async def collect():
        return [c async for c in router.stream("hi")]

    chunks = run(collect())
    assert chunks[-1].done and chunks[-1].text == "one two three" and chunks[-1].model == "gemma"
    assert all(chunks[-1].text.startswith(c.text) for c in chunks)  # each step is a prefix of the next


def test_a_model_that_never_answers_is_cut_off_and_the_next_route_tried(store):
    thinker = ThinkingForever()
    router = ModelRouter(Route("local", "thinker", thinker), Route("hosted", "h", fake("hosted answered")), store, first_word_seconds=0.2)
    answer = run(router.ask("hello"))
    assert (answer.text, answer.route) == ("hosted answered", "hosted")
    assert thinker.closed  # the abandoned stream was closed, not left generating


def test_the_deadline_only_covers_the_first_word(store):
    router = ModelRouter(Route("local", "slow", SlowButTalking()), None, store, first_word_seconds=0.1)
    assert run(router.ask("hello")).text == "slow and steady"  # 0.3 s of streaming after a quick start is fine


def test_every_answer_is_measured_including_time_to_first_word(store):
    from drill.server.observe import RecordingObserver

    observer = RecordingObserver()
    router = ModelRouter(Route("local", "slow", SlowButTalking()), None, store, observer=observer)
    run(router.ask("hello"))
    run(router.ask("hello"))  # cache hit
    first, second = observer.records
    assert first["route"] == "local" and first["model"] == "slow" and not first["cached"]
    assert 0 <= first["ttft_ms"] < first["total_ms"]  # the first word came well before the last
    assert first["tokens"]["total_tokens"] > 0 and first["thinking"] is False
    assert second["cached"] and second["ttft_ms"] <= 5


def test_thinking_models_are_told_not_to_think_unless_the_job_is_complex(store):
    router = ModelRouter(Route("local", "qwen3:14b", fake("a")), None, store, thinking="complex")
    _, quick_chat, quick_thinks = router._prepare([], router.local, "quick", False)
    _, complex_chat, complex_thinks = router._prepare([], router.local, "complex", False)
    assert quick_thinks is False and quick_chat.kwargs == {"extra_body": {"reasoning_effort": "none"}}
    assert complex_thinks is True and complex_chat is router.local.chat
    always = ModelRouter(Route("local", "qwen3:14b", fake("a")), None, store, thinking="on")
    assert always._prepare([], always.local, "quick", False)[2] is True
    plain = ModelRouter(Route("local", "gemma3:12b", fake("a")), None, store, thinking="on")
    assert plain._prepare([], plain.local, "quick", False)[1] is plain.local.chat  # nothing to switch off


def test_traces_land_in_mlflow_with_the_first_word_span(store, tmp_path, monkeypatch):
    import mlflow

    from drill.server.observe import MlflowObserver

    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
    mlflow.set_tracking_uri(uri)
    try:
        observer = MlflowObserver("drill-test")
        assert observer.enabled
        router = ModelRouter(Route("local", "slow", SlowButTalking()), None, store, observer=observer)
        assert run(router.ask("hello")).text == "slow and steady"
        mlflow.flush_trace_async_logging()  # traces are written in the background
        experiment_id = mlflow.get_experiment_by_name("drill-test").experiment_id
        traces = mlflow.search_traces(locations=[experiment_id], return_type="list")
        assert len(traces) == 1
        spans = {s.name: s for s in traces[0].data.spans}
        assert {"tutor.ask", "first_word"} <= set(spans)
        ask = spans["tutor.ask"]
        assert ask.attributes["model"] == "slow" and ask.attributes["ttft_ms"] < ask.attributes["total_ms"]
        assert ask.attributes["mlflow.chat.tokenUsage"]["total_tokens"] > 0
        wait_ms = (spans["first_word"].end_time_ns - spans["first_word"].start_time_ns) / 1e6
        assert wait_ms < 100  # the first word was immediate; the rest took ~300 ms
    finally:
        mlflow.set_tracking_uri(None)


def test_thinking_is_hidden():
    assert strip_thinking("<think>hmm</think>the answer", final=True) == "the answer"
    assert strip_thinking("<think>still thinking") == ""
    assert strip_thinking("plain") == "plain"


def test_json_is_found_in_prose_and_fences():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('Sure! {"question": "q", "answer": "a"} Hope that helps.') == {"question": "q", "answer": "a"}
    with pytest.raises(ValueError):
        parse_json("no json here")


def test_local_model_choice_avoids_thinking_models_unless_asked():
    assert pick_local_model(["qwen3:14b", "gemma3:12b"]) == "gemma3:12b"
    assert pick_local_model(["qwen3:14b"]) == "qwen3:14b"
    assert pick_local_model(["gemma3:12b"], wanted="qwen3:14b") == "qwen3:14b"
    assert pick_local_model([]) is None


# ---------------------------------------------------------------------------
# web API
# ---------------------------------------------------------------------------


def client_with(store, bank, *replies, local=True):
    route = Route("local", "fake", fake(*replies)) if local else None
    router = ModelRouter(route, None, store)
    return TestClient(create_app(store=store, router=router, bank=bank, with_mcp=False))


def test_page_and_health(store, bank):
    client = client_with(store, bank, "unused")
    health = client.get("/api/health").json()
    assert health["ok"] and health["ai"] and health["user"] == "local" and health["models"]["local"] == "fake"
    page = client.get("/")
    assert page.status_code == 200
    assert page.text.startswith("<!doctype html>") and "<title>Daily Drill</title>" in page.text


def test_documents_follow_the_pages_protocol(store, bank):
    client = client_with(store, bank)
    assert client.get("/api/docs/data/users/local/progress").json() == {"exists": False, "data": None}
    client.put("/api/docs/data/users/local/progress", json={"solved": {}, "days": ["2026-10-10"]})
    client.patch("/api/docs/data/users/local/progress", json={"current": "resolve_prompt"})
    got = client.get("/api/docs/data/users/local/progress").json()
    assert got["exists"] and got["data"]["days"] == ["2026-10-10"] and got["data"]["current"] == "resolve_prompt"
    client.put("/api/docs/study/x1", json={"text": "alias", "createdAt": 5})
    assert client.get("/api/collections/study").json() == {"docs": [{"id": "x1", "data": {"text": "alias", "createdAt": 5}}]}
    client.delete("/api/docs/study/x1")
    assert client.get("/api/collections/study").json() == {"docs": []}
    assert client.get("/api/docs/..%2Fetc").status_code == 400


def test_ask_streams_text_and_returns_json(store, bank):
    client = client_with(store, bank, "Try a dict.", '{"question": "What prints?", "answer": "2"}')
    streamed = client.post("/api/ask", json={"prompt": "hint please", "tier": "quick"})
    assert streamed.status_code == 200 and streamed.text == "Try a dict."
    quiz = client.post("/api/ask", json={"prompt": "quiz please", "json": True})
    assert quiz.json() == {"value": {"question": "What prints?", "answer": "2"}}
    assert client.post("/api/ask", json={"prompt": ""}).status_code == 400


def test_ask_without_a_model_is_a_clear_503(store, bank):
    client = client_with(store, bank, local=False)
    assert not client.get("/api/health").json()["ai"]
    response = client.post("/api/ask", json={"prompt": "hello"})
    assert response.status_code == 503 and response.json()["detail"]["code"] == "unavailable"


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


def test_mcp_tools_share_the_store_and_bank(store, bank):
    mcp_door.configure(store=store, router=ModelRouter(Route("local", "fake", fake("Look at .get")), None, store), bank=bank)
    first = bank.order()[0]
    assert mcp_door.next_drill()["id"] == first

    card = mcp_door.get_drill("resolve_prompt")
    assert card["exercise"]["function"] == "resolve_prompt" and "prompts:/" in card["exercise"]["prompt"]
    assert card["check"]["answer_index"] == 1 and card["in_your_stack"]["title"].startswith("MLflow")

    good = mcp_door.run_tests("resolve_prompt", bank.problems["resolve_prompt"]["solution"])
    assert good["passed"] and good["passed_count"] == good["total"]
    bad = mcp_door.run_tests("resolve_prompt", "def resolve_prompt(registry, uri):\n    return None\n")
    assert not bad["passed"] and bad["first_failure"]["expected"] is not None

    assert run(mcp_door.hint("resolve_prompt", "def resolve_prompt(r, u): pass")) == "Look at .get"

    saved = mcp_door.save_to_study("MERGE INTO", note="when do I use it?")
    assert [i["text"] for i in mcp_door.study_list()] == ["MERGE INTO"]
    assert store.get(f"study/{saved['id']}")["note"] == "when do I use it?"

    marked = mcp_door.mark_done(first)
    assert marked["next"] == bank.order()[1] and mcp_door.next_drill()["id"] == bank.order()[1]
    modules = mcp_door.list_lessons()
    assert modules[0]["lessons"][0] == {"id": first, "title": bank.lessons[first]["title"], "done": True}
    with pytest.raises(KeyError):
        mcp_door.get_drill("no_such_lesson")
