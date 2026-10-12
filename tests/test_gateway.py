"""The hosted model through Databricks AI Gateway, signed with the Databricks login on the machine.

Offline: the gateway is an httpx mock and the login a fake that hands out new tokens.
"""

from __future__ import annotations

import asyncio

import httpx

from drill.server.router import hosted_auth, hosted_route




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
