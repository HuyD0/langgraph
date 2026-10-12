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


def test_ollama_model_selects_local_flavour(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:12b")
    settings = LLMSettings.from_env()
    assert settings.flavour == "ollama" and settings.is_local
    assert settings.endpoint == "http://localhost:11434/v1"
    assert settings.is_configured  # no key or service principal needed


def test_ollama_wins_over_azure_settings(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-res.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "k")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:12b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://other-host:11434/v1")
    settings = LLMSettings.from_env()
    assert settings.flavour == "ollama"
    assert settings.endpoint == "http://other-host:11434/v1"


def test_ollama_respects_empty_temperature(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:12b")
    monkeypatch.setenv("DRILL_TEMPERATURE", "")
    assert LLMSettings.from_env().temperature is None


def test_ollama_builds_a_chat_model_without_network(monkeypatch):
    """Construction must not contact Ollama; only invoke() does."""
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:12b")
    model = build_chat_model(LLMSettings.from_env())
    assert type(model).__name__ == "ChatOpenAI"
    assert model.model_name == "gemma3:12b"


def test_local_settings_without_a_model_name_explain_what_to_set():
    with pytest.raises(MissingCredentials) as exc:
        build_chat_model(LLMSettings(flavour="ollama", endpoint="http://localhost:11434/v1"))
    assert "OLLAMA_MODEL" in str(exc.value)


def test_gateway_endpoint_selects_gateway_flavour(monkeypatch):
    monkeypatch.setenv("MLFLOW_GATEWAY_ENDPOINT", "drill-tutor")
    settings = LLMSettings.from_env()
    assert settings.flavour == "mlflow_gateway" and settings.is_configured
    assert settings.endpoint == "http://localhost:5050/gateway/mlflow/v1"
    assert settings.deployment == "drill-tutor"


def test_gateway_wins_over_ollama_and_azure(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-res.openai.azure.com/")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:12b")
    monkeypatch.setenv("MLFLOW_GATEWAY_ENDPOINT", "drill-tutor")
    monkeypatch.setenv("MLFLOW_GATEWAY_URL", "http://other:5050/gateway/mlflow/v1")
    settings = LLMSettings.from_env()
    assert settings.flavour == "mlflow_gateway"
    assert settings.endpoint == "http://other:5050/gateway/mlflow/v1"


def test_gateway_builds_a_chat_model_without_network(monkeypatch):
    monkeypatch.setenv("MLFLOW_GATEWAY_ENDPOINT", "drill-tutor")
    model = build_chat_model(LLMSettings.from_env())
    assert type(model).__name__ == "ChatOpenAI" and model.model_name == "drill-tutor"


def test_gateway_without_endpoint_name_explains_what_to_set():
    with pytest.raises(MissingCredentials) as exc:
        build_chat_model(LLMSettings(flavour="mlflow_gateway", endpoint="http://localhost:5050"))
    assert "MLFLOW_GATEWAY_ENDPOINT" in str(exc.value)


def test_experiment_names_become_workspace_paths_only_on_databricks():
    from drill.config import experiment_path

    assert experiment_path("daily-drill", "databricks", "ana@example.com") == "/Users/ana@example.com/daily-drill"
    assert experiment_path("daily-drill", "databricks://work", "ana@example.com") == "/Users/ana@example.com/daily-drill"
    assert experiment_path("/Shared/drill", "databricks", "ana@example.com") == "/Shared/drill"  # already a path
    assert experiment_path("daily-drill", "http://localhost:5050") == "daily-drill"  # local: unchanged
    assert experiment_path("daily-drill", None) == "daily-drill"
    with pytest.raises(ValueError):
        experiment_path("daily-drill", "databricks")  # a path needs the user


def test_the_databricks_profile_comes_from_the_uri_first(monkeypatch):
    from drill.config import databricks_profile, is_databricks_uri

    monkeypatch.setenv("DATABRICKS_CONFIG_PROFILE", "DEFAULT")
    assert databricks_profile("databricks://work") == "work"
    assert databricks_profile("databricks") == "DEFAULT"
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE")
    assert databricks_profile("databricks") is None
    assert is_databricks_uri("databricks") and is_databricks_uri("databricks://work")
    assert not is_databricks_uri("http://localhost:5050") and not is_databricks_uri(None)


def test_unity_catalog_trace_storage_is_spotted():
    from types import SimpleNamespace

    from drill.config import UC_TRACE_TAG, uc_trace_location

    assert uc_trace_location(SimpleNamespace(tags={UC_TRACE_TAG: "main.traces"})) == "main.traces"
    assert uc_trace_location(SimpleNamespace(tags={})) is None
