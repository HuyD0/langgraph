"""The hosted model through Databricks AI Gateway, signed with the Databricks login on the machine.

Offline: the gateway is an httpx mock and the login a fake that hands out new tokens.
"""

from __future__ import annotations

import asyncio

import httpx

from drill.server.router import gateway_base_url, hosted_auth, hosted_route




class FakeLogin:
    """Just enough of a databricks.sdk Config: the workspace, and fresh headers on every call."""

    host = "https://adb-123.4.azuredatabricks.net/"

    def __init__(self):
        self.calls = 0

    def authenticate(self):
        self.calls += 1
        return {"Authorization": f"Bearer entra-{self.calls}"}


def test_gateway_calls_carry_a_fresh_databricks_login_not_a_stored_key(monkeypatch):
    seen = []

    def gateway(request: httpx.Request) -> httpx.Response:
        seen.append((str(request.url), request.headers["authorization"]))
        return httpx.Response(200, json={
            "id": "1", "object": "chat.completion", "created": 0, "model": "drill-claude",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "Look at the gate."}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
        })

    for name in ("DRILL_HOSTED_BASE_URL", "DRILL_HOSTED_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DRILL_HOSTED_AUTH", "databricks")
    monkeypatch.setenv("DRILL_HOSTED_MODEL", "drill-claude")
    login = FakeLogin()
    route = hosted_route(config_factory=lambda: login, transport=httpx.MockTransport(gateway))
    assert route.model == "drill-claude"
    asyncio.run(route.chat.ainvoke("why?"))
    asyncio.run(route.chat.ainvoke("and now?"))
    assert seen == [
        ("https://adb-123.4.azuredatabricks.net/serving-endpoints/chat/completions", "Bearer entra-1"),
        ("https://adb-123.4.azuredatabricks.net/serving-endpoints/chat/completions", "Bearer entra-2"),
    ]


def test_which_login_the_hosted_model_uses(monkeypatch):
    monkeypatch.delenv("DRILL_HOSTED_AUTH", raising=False)
    workspace = "https://adb-1.2.azuredatabricks.net/serving-endpoints"
    assert hosted_auth(workspace, "") == "databricks"  # a Databricks address and no key
    assert hosted_auth(workspace, "dapi123") == "key"  # a key you chose to keep
    assert hosted_auth("https://api.example.com/v1", "") == "key"
    assert hosted_auth("", "") == "key"  # nothing set: the Azure settings, as before
    monkeypatch.setenv("DRILL_HOSTED_AUTH", "databricks")
    assert hosted_auth("", "") == "databricks"


def test_no_databricks_login_means_no_hosted_model_rather_than_a_crash(monkeypatch):
    monkeypatch.setenv("DRILL_HOSTED_AUTH", "databricks")
    monkeypatch.setenv("DRILL_HOSTED_MODEL", "drill-claude")

    def no_login():
        raise ValueError("default auth: cannot configure default credentials")

    assert hosted_route(config_factory=no_login) is None


def test_a_unity_gateway_model_service_goes_to_the_gateway_and_an_endpoint_to_serving_endpoints():
    host = "https://adb-1.2.azuredatabricks.net/"
    assert gateway_base_url(host, "system.ai.some-model") == "https://adb-1.2.azuredatabricks.net/ai-gateway/mlflow/v1"
    assert gateway_base_url(host, "main.ai.drill-tutor") == "https://adb-1.2.azuredatabricks.net/ai-gateway/mlflow/v1"
    assert gateway_base_url(host, "drill-claude") == "https://adb-1.2.azuredatabricks.net/serving-endpoints"
    assert gateway_base_url(host, "gpt-5.2") == "https://adb-1.2.azuredatabricks.net/serving-endpoints"  # a dot is not a service name
    assert hosted_auth(gateway_base_url(host, "system.ai.some-model"), "") == "databricks"


def test_a_model_service_is_called_at_the_unity_gateway_with_the_login(monkeypatch):
    seen = []

    def gateway(request: httpx.Request) -> httpx.Response:
        seen.append((str(request.url), request.headers["authorization"], request.read()))
        return httpx.Response(200, json={
            "id": "1", "object": "chat.completion", "created": 0, "model": "system.ai.some-model",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    for name in ("DRILL_HOSTED_BASE_URL", "DRILL_HOSTED_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DRILL_HOSTED_AUTH", "databricks")
    monkeypatch.setenv("DRILL_HOSTED_MODEL", "system.ai.some-model")
    route = hosted_route(config_factory=FakeLogin, transport=httpx.MockTransport(gateway))
    asyncio.run(route.chat.ainvoke("hi"))
    url, auth, body = seen[0]
    assert url == "https://adb-123.4.azuredatabricks.net/ai-gateway/mlflow/v1/chat/completions"
    assert auth == "Bearer entra-1" and b'"model":"system.ai.some-model"' in body.replace(b" ", b"")
