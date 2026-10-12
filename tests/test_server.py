"""The local tutor server: document store, model router, web API and MCP tools, all offline.

No Ollama, no Azure: the "models" here are LangChain's fake chat model and a deliberately
broken one, so these tests run anywhere. What they check is the routing and the plumbing -
local first, fallback, cache, budget, the page's document protocol - not the prose.
"""

from __future__ import annotations

import asyncio
import time

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


@pytest.fixture
def mlflow_store(tmp_path, monkeypatch):
    """A throwaway MLflow store, with tracing switched on for this test only."""
    import mlflow

    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
    monkeypatch.setenv("DRILL_TRACING", "1")
    mlflow.set_tracking_uri(uri)
    yield uri
    mlflow.clear_active_model()
    mlflow.set_tracking_uri(None)


def traces_in(experiment: str) -> list:
    import mlflow

    mlflow.flush_trace_async_logging()  # traces are written in the background
    experiment_id = mlflow.get_experiment_by_name(experiment).experiment_id
    return [mlflow.get_trace(t.info.trace_id) for t in mlflow.search_traces(locations=[experiment_id], return_type="list")]


def test_traces_are_named_tagged_versioned_and_checked(store, mlflow_store):
    from mlflow.entities import SpanType

    from drill.server.observe import MlflowObserver, app_version

    observer = MlflowObserver("drill-test")
    assert observer.enabled
    router = ModelRouter(Route("local", "slow", SlowButTalking()), None, store, observer=observer)
    context = {"feature": "hint", "lesson_id": "resolve_prompt", "exercise_fn": "resolve_prompt",
               "hint_level": 2, "word_limit": 2, "session": "s1"}
    assert run(router.ask("hello", context=context)).text == "slow and steady"
    observer.drain()

    [trace] = traces_in("drill-test")
    tags, metadata = trace.info.tags, trace.info.trace_metadata
    assert tags["mlflow.traceName"] == "hint"  # named after what it was for, not "tutor.ask" every time
    assert (tags["feature"], tags["lesson_id"], tags["hint_level"]) == ("hint", "resolve_prompt", "2")
    assert tags["app_version"] == app_version() and metadata["mlflow.modelId"]  # linked to a version
    assert metadata["mlflow.trace.session"] == "s1" and metadata["mlflow.trace.user"] == "local"

    spans = {s.name: s for s in trace.data.spans}
    assert spans["hint"].span_type == SpanType.CHAIN and spans["checks"].span_type == SpanType.GUARDRAIL
    ask = spans["tutor.ask"]
    assert ask.span_type == SpanType.CHAT_MODEL and ask.inputs["messages"] == [{"role": "user", "content": "hello"}]
    assert ask.attributes["model"] == "slow" and ask.attributes["ttft_ms"] < ask.attributes["total_ms"]
    assert ask.attributes["mlflow.chat.tokenUsage"]["total_tokens"] > 0
    wait_ms = (spans["first_word"].end_time_ns - spans["first_word"].start_time_ns) / 1e6
    assert wait_ms < 100  # the first word was immediate; the rest took ~300 ms

    # Three words against a limit of two: the checks say so, as a span, as tags and as feedback.
    assert spans["checks"].outputs == {"words": 3, "solution_leak": False, "big_o": False, "over_word_limit": True}
    assert (tags["solution_leak"], tags["over_word_limit"]) == ("false", "true")
    feedback = {a.name: a.value for a in trace.info.assessments}
    assert feedback == {"solution_leak": False, "big_o": False, "over_word_limit": True}


def test_a_leaked_solution_and_a_failed_model_show_on_the_trace(store, mlflow_store):
    from mlflow.entities import SpanStatusCode

    from drill.server.observe import MlflowObserver

    observer = MlflowObserver("drill-test")
    leak = "def add(a, b):\n    return a + b"
    router = ModelRouter(Route("local", "down", Broken()), Route("hosted", "backup", fake(leak)), store, observer=observer)
    long_prompt = "why? " * 1500  # 7,500 characters: kept whole, not cut at 4,000
    run(router.ask(long_prompt, context={"feature": "ask_lesson", "question": "why?", "exercise_fn": "add"}))
    observer.drain()

    [trace] = traces_in("drill-test")
    spans = {s.name: s for s in trace.data.spans}
    assert spans["ask_lesson"].inputs == {"question": "why?"} and spans["ask_lesson"].outputs == {"answer": leak}
    assert spans["tutor.ask"].inputs["messages"][0]["content"] == long_prompt
    assert spans["tutor.ask"].attributes["route"] == "hosted"
    failed = spans["attempt local"]
    assert failed.status.status_code == SpanStatusCode.ERROR and "connection refused" in failed.attributes["error"]
    assert trace.info.tags["solution_leak"] == "true"


def test_tracing_waits_for_mlflow_without_holding_up_answers(store, tmp_path, monkeypatch):
    import socket

    import mlflow

    from drill.server.observe import MlflowObserver

    with socket.socket() as sock:  # a port nothing is listening on: MLflow is not running
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"http://127.0.0.1:{port}")
    mlflow.set_tracking_uri(f"http://127.0.0.1:{port}")
    try:
        started = time.monotonic()
        observer = MlflowObserver("drill-test")
        assert not observer.enabled and time.monotonic() - started < 3  # not MLflow's four minutes of retries
        router = ModelRouter(Route("local", "fake", fake("fine")), None, store, observer=observer)
        assert run(router.ask("hello")).text == "fine"

        # MLflow starts later: the next try after the wait turns tracing back on, no restart needed.
        uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
        monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
        mlflow.set_tracking_uri(uri)
        assert not observer.ready()  # still inside the 30-second wait
        observer._next_try = 0
        assert observer.ready()
    finally:
        mlflow.clear_active_model()
        mlflow.set_tracking_uri(None)


def test_tracing_to_databricks_uses_a_workspace_path_and_fails_fast(monkeypatch):
    import mlflow

    from drill.server import observe

    monkeypatch.setenv("MLFLOW_TRACKING_URI", "databricks")
    named = []
    monkeypatch.setattr(mlflow, "set_experiment", lambda name: named.append(name))
    monkeypatch.setattr(mlflow, "set_active_model", lambda **kw: None)
    monkeypatch.setattr(observe, "databricks_user", lambda uri: "ana@example.com")
    try:
        assert observe.MlflowObserver("daily-drill").enabled
        assert named == ["/Users/ana@example.com/daily-drill"]  # Databricks needs a workspace path

        def offline(uri):
            raise ConnectionError("no network")

        monkeypatch.setattr(observe, "databricks_user", offline)
        started = time.monotonic()
        observer = observe.MlflowObserver("daily-drill")
        assert not observer.enabled and time.monotonic() - started < 3  # the quick check gave up
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


def test_the_page_says_what_each_request_is_for(store, bank):
    from drill.server.observe import RecordingObserver

    observer = RecordingObserver()
    router = ModelRouter(Route("local", "fake", fake("Try a dict.")), None, store, observer=observer)
    client = TestClient(create_app(store=store, router=router, bank=bank, with_mcp=False))
    trace = {"feature": "ask_lesson", "lesson_id": "resolve_prompt", "step": "Learn", "question": "why?",
             "chip": False, "not_a_field": "dropped"}
    assert client.post("/api/ask", json={"prompt": "p", "trace": trace}).text == "Try a dict."
    [record] = observer.records
    assert record["context"] == {"feature": "ask_lesson", "door": "page", "lesson_id": "resolve_prompt",
                                 "step": "Learn", "question": "why?", "chip": "no", "user": "local"}


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


def test_a_slow_hint_run_does_not_freeze_the_server(store, bank, monkeypatch):
    """Running the learner's code for a hint happens off the main loop, so other requests go on."""
    mcp_door.configure(store=store, router=ModelRouter(Route("local", "fake", fake("Look at .get")), None, store), bank=bank)
    real = mcp_door.tutor.run_exercise
    monkeypatch.setattr(mcp_door.tutor, "run_exercise", lambda *a: (time.sleep(0.5), real(*a))[1])

    async def both():
        ticks = 0

        async def other_requests():
            nonlocal ticks
            while True:
                await asyncio.sleep(0.05)
                ticks += 1

        other = asyncio.create_task(other_requests())
        await mcp_door.hint("resolve_prompt", "def resolve_prompt(r, u): pass")
        other.cancel()
        return ticks

    assert run(both()) >= 5  # the other task kept running while the code ran


def test_mcp_tool_calls_are_traced_with_the_model_call_inside(store, bank, mlflow_store):
    from mlflow.entities import SpanType, TraceState

    from drill.server import observe

    observer = observe.default_observer()
    router = ModelRouter(Route("local", "fake", fake("Look at .get")), None, store, observer=observer)
    mcp_door.configure(store=store, router=router, bank=bank)
    mcp_door.next_drill()
    assert run(mcp_door.hint("resolve_prompt", "", 2)) == "Look at .get"
    with pytest.raises(KeyError):
        mcp_door.get_drill("no_such_lesson")
    observer.drain()

    traces = {t.info.tags["mlflow.traceName"]: t for t in traces_in("daily-drill")}
    assert set(traces) == {"next_drill", "hint", "get_drill"}
    hint = traces["hint"]
    assert (hint.info.tags["door"], hint.info.tags["lesson_id"]) == ("mcp", "resolve_prompt")
    assert hint.info.trace_metadata["mlflow.trace.session"] == observe.MCP_SESSION
    spans = {s.name: s for s in hint.data.spans}
    tool = spans["hint"]
    assert tool.span_type == SpanType.TOOL and tool.inputs == {"lesson_id": "resolve_prompt", "code": "", "level": 2}
    assert tool.outputs == "Look at .get"
    assert spans["tutor.ask"].parent_id == tool.span_id and spans["checks"].parent_id == tool.span_id
    assert hint.info.tags["solution_leak"] == "false" and hint.info.tags["hint_level"] == "2"
    assert traces["get_drill"].info.state == TraceState.ERROR  # a failing tool call is recorded, then re-raised


def test_feedback_is_accepted_and_logged_as_activity(store, bank):
    client = client_with(store, bank, "unused")
    r = client.post("/api/feedback", json={"request": "abc123def", "name": "useful", "value": True})
    assert r.status_code == 200 and r.json()["ok"]
    assert client.post("/api/feedback", json={"request": "x", "name": "n" * 61, "value": 1}).status_code == 422



# ---------------------------------------------------------------------------
# As a Databricks App: one server, everyone signed in, each with their own progress
# ---------------------------------------------------------------------------


def test_in_an_app_each_signed_in_person_gets_their_own_progress(store, bank, monkeypatch):
    monkeypatch.setenv("DATABRICKS_APP_NAME", "daily-drill")
    client = client_with(store, bank, "ok")
    sam, kim = {"x-forwarded-email": "Sam@Example.com"}, {"x-forwarded-email": "kim@example.com"}
    client.put("/api/docs/data/users/me/progress", json={"lesson": "a"}, headers=sam)
    client.put("/api/docs/data/users/me/progress", json={"lesson": "b"}, headers=kim)
    assert client.get("/api/docs/data/users/me/progress", headers=sam).json()["data"] == {"lesson": "a"}
    assert client.get("/api/docs/data/users/me/progress", headers=kim).json()["data"] == {"lesson": "b"}
    assert client.get("/api/health", headers=sam).json()["owner"] == "sam@example.com"
    assert store.for_owner("sam@example.com").get("data/users/me/progress") == {"lesson": "a"}


def test_outside_an_app_the_identity_header_is_not_believed(store, bank, monkeypatch):
    monkeypatch.delenv("DATABRICKS_APP_NAME", raising=False)
    monkeypatch.delenv("DRILL_TRUST_USER_HEADER", raising=False)
    client = client_with(store, bank, "ok")
    client.put("/api/docs/study/x", json={"text": "mine"}, headers={"x-forwarded-email": "boss@example.com"})
    assert store.get("study/x") == {"text": "mine"}  # saved as this machine's owner, not as "boss"
    assert store.for_owner("boss@example.com").get("study/x") is None


def test_an_apps_lakebase_resource_is_enough_to_find_the_database(monkeypatch):
    from drill.server.store import database_url, db_schema, lakebase_endpoint

    for name in ("DRILL_DATABASE_URL", "DRILL_LAKEBASE_ENDPOINT", "PGPORT", "PGSSLMODE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("PGHOST", "ep-1.database.example.com")
    monkeypatch.setenv("PGDATABASE", "databricks_postgres")
    monkeypatch.setenv("LAKEBASE_ENDPOINT", "projects/p/branches/production/endpoints/primary")
    monkeypatch.setenv("DRILL_DB_SCHEMA", "drill")
    assert database_url() == "postgresql+psycopg://ep-1.database.example.com:5432/databricks_postgres?sslmode=require"
    assert lakebase_endpoint() == "projects/p/branches/production/endpoints/primary"
    assert db_schema() == "drill"
    monkeypatch.setenv("DRILL_DB_SCHEMA", "drill; drop table docs")
    with pytest.raises(ValueError):
        db_schema()


def test_an_idle_app_stops_itself_and_a_busy_one_does_not():
    from drill.server.api import IdleStop

    now = [0.0]
    stopped: list[str] = []
    idle = IdleStop("daily-drill", minutes=30, stop=stopped.append, clock=lambda: now[0])
    now[0] = 29 * 60
    assert not idle.check()
    idle.seen()  # someone opened a lesson
    now[0] = 58 * 60
    assert not idle.check() and stopped == []
    now[0] = 60 * 60
    assert idle.check() and stopped == ["daily-drill"]


def test_idle_stop_only_runs_inside_an_app(monkeypatch):
    from drill.server.api import IdleStop

    monkeypatch.setenv("DRILL_IDLE_STOP_MINUTES", "30")
    monkeypatch.delenv("DATABRICKS_APP_NAME", raising=False)
    assert IdleStop.from_env() is None
    monkeypatch.setenv("DATABRICKS_APP_NAME", "daily-drill")
    assert IdleStop.from_env().seconds == 1800


def test_an_apps_traces_carry_where_they_ran_who_asked_and_the_pages_request_id(store, bank, mlflow_store, monkeypatch):
    """Context a portable deployment needs: environment, workspace, app, user email and the request id."""
    import mlflow

    from drill.server import observe

    monkeypatch.setenv("DATABRICKS_APP_NAME", "daily-drill")
    monkeypatch.setenv("DATABRICKS_WORKSPACE_ID", "123")
    monkeypatch.setenv("DRILL_MLFLOW_EXPERIMENT", "drill-app-test")
    observer = observe.MlflowObserver()
    router = ModelRouter(Route("hosted", "ai.models.haiku", fake("Use a dict.")), None, store, observer=observer)
    client = TestClient(create_app(store=store, router=router, bank=bank, with_mcp=False))
    sam = {"x-forwarded-email": "sam@example.com"}
    client.post("/api/ask", json={"prompt": "hint?", "trace": {"feature": "hint", "request": "req-123456"}}, headers=sam)
    observer.drain()

    [trace] = traces_in("drill-app-test")
    tags, metadata = trace.info.tags, trace.info.trace_metadata
    assert (tags["environment"], tags["app_name"], tags["workspace_id"]) == ("app", "daily-drill", "123")
    assert (tags["model"], tags["route"], tags["cached"]) == ("ai.models.haiku", "hosted", "false")
    assert metadata["mlflow.trace.user"] == "sam@example.com"  # the same owner Lakebase uses
    assert trace.info.client_request_id == "req-123456" and "request" not in tags

    client.post("/api/feedback", json={"request": "req-123456", "name": "useful", "value": True}, headers=sam)
    observer.drain()
    [assessment] = [a for a in mlflow.get_trace(trace.info.trace_id).info.assessments if a.name == "useful"]
    assert assessment.source.source_type == "HUMAN" and assessment.source.source_id == "sam@example.com"


def test_names_come_from_settings(monkeypatch):
    from drill import mlflow_names

    for name in ("DRILL_PROMPT_SCHEMA", "DRILL_ENVIRONMENT", "DATABRICKS_APP_NAME", "DRILL_MLFLOW_EXPERIMENT"):
        monkeypatch.delenv(name, raising=False)
    assert (mlflow_names.environment(), mlflow_names.experiment()) == ("local", "daily-drill")
    assert mlflow_names.prompt_name("review") == "use_case_review"
    assert mlflow_names.needs_prompt_schema("databricks") and not mlflow_names.needs_prompt_schema("http://localhost:5050")
    monkeypatch.setenv("DRILL_PROMPT_SCHEMA", "main.daily_drill")
    assert mlflow_names.prompt_name("challenge") == "main.daily_drill.use_case_challenge"
    monkeypatch.setenv("DRILL_PROMPT_SCHEMA", "main")
    with pytest.raises(ValueError):
        mlflow_names.prompt_name("review")
    assert mlflow_names.run_name("review eval", "review-v2") == "review-eval-review-v2"
    assert mlflow_names.context_metadata("7246346-dirty") == {"mlflow.source.git.commit": "7246346"}
    assert mlflow_names.context_metadata("0.1.0") == {}


def test_the_answer_rules_scorer_reads_checks_as_a_dict_or_as_json_text():
    from types import SimpleNamespace

    from drill.trace_scoring import answer_rules

    for outputs in ({"solution_leak": False, "over_word_limit": True, "words": 9},
                    '{"solution_leak": false, "over_word_limit": true, "words": 9}'):
        trace = SimpleNamespace(data=SimpleNamespace(spans=[SimpleNamespace(name="checks", outputs=outputs)]))
        got = {f.name: f.value for f in answer_rules(trace=trace)}
        assert got == {"no_solution_leak": True, "within_word_limit": False}  # True is a pass; counts are not rules
