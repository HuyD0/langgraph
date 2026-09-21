"""Settings parsing, and the Foundry endpoint auto-detection.

`LLMSettings.from_env` guesses which Foundry surface you have from the endpoint
URL. Getting that guess wrong means an auth error deep inside an SDK, so it is
worth pinning down.
"""

from __future__ import annotations

import pytest

from drill.config import DrillSettings, LLMSettings
from drill.llm import MissingCredentials, build_chat_model


def test_bare_environment_is_not_configured():
    settings = LLMSettings.from_env()
    assert not settings.is_configured
    assert len(settings.missing()) == 3


def test_openai_endpoint_detected(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-res.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "k")
    settings = LLMSettings.from_env()
    assert settings.flavour == "azure_openai"
    assert settings.is_configured


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://my-res.services.ai.azure.com/models",
        "https://my-res.services.ai.azure.com",
        "https://something.else/models",
    ],
)
def test_foundry_models_endpoint_detected(monkeypatch, endpoint):
    monkeypatch.setenv("AZURE_INFERENCE_ENDPOINT", endpoint)
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "Llama-3.3-70B")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "k")
    assert LLMSettings.from_env().flavour == "azure_inference"


def test_explicit_flavour_overrides_the_guess(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-res.openai.azure.com/")
    monkeypatch.setenv("AZURE_FOUNDRY_FLAVOUR", "azure_inference")
    assert LLMSettings.from_env().flavour == "azure_inference"


def test_nonsense_flavour_falls_back_to_the_guess(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-res.openai.azure.com/")
    monkeypatch.setenv("AZURE_FOUNDRY_FLAVOUR", "banana")
    assert LLMSettings.from_env().flavour == "azure_openai"


def test_service_principal_counts_as_auth(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-res.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    for var in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"):
        monkeypatch.setenv(var, "x")
    settings = LLMSettings.from_env()
    assert settings.uses_service_principal and settings.is_configured


def test_partial_service_principal_is_not_enough(monkeypatch):
    monkeypatch.setenv("AZURE_TENANT_ID", "x")
    monkeypatch.setenv("AZURE_CLIENT_ID", "x")  # no secret
    settings = LLMSettings.from_env()
    assert not settings.uses_service_principal


def test_api_key_takes_precedence_over_service_principal(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "k")
    for var in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"):
        monkeypatch.setenv(var, "x")
    assert not LLMSettings.from_env().uses_service_principal


def test_missing_credentials_error_names_every_gap():
    with pytest.raises(MissingCredentials) as exc:
        build_chat_model(LLMSettings())
    message = str(exc.value)
    assert "AZURE_OPENAI_ENDPOINT" in message
    assert "AZURE_OPENAI_DEPLOYMENT" in message
    assert "AZURE_TENANT_ID" in message


def test_invalid_numeric_env_falls_back(monkeypatch):
    """A typo in a number must not crash the app on startup."""
    monkeypatch.setenv("DRILL_MAX_ATTEMPTS", "three")
    assert DrillSettings.from_env().max_attempts == 3


def test_numeric_env_is_read(monkeypatch):
    monkeypatch.setenv("DRILL_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("DRILL_SANDBOX_TIMEOUT", "30")
    settings = DrillSettings.from_env()
    assert settings.max_attempts == 5 and settings.sandbox_timeout == 30


def test_importing_the_package_needs_no_credentials():
    """The defect that made the old agent untestable. Guard against a relapse."""
    import importlib

    for module in ("drill.config", "drill.llm", "drill.graph", "drill.nodes",
                   "drill.sandbox", "drill.session", "drill.tracking", "drill.evaluation"):
        importlib.import_module(module)
