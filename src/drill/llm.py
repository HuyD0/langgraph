"""Builds the chat model that drives the tutor, against Azure AI Foundry.

Like :mod:`drill.config`, nothing here runs at import time. ``build_chat_model()``
is a function you call, so tests can import this module - and the graph that uses
it - with no credentials present at all.
"""

from __future__ import annotations

from typing import Any

from drill.config import LLMSettings

# The scope an AAD token must carry to call Azure AI / Cognitive Services.
_AAD_SCOPE = "https://cognitiveservices.azure.com/.default"


class MissingCredentials(RuntimeError):
    """Raised when Foundry settings are incomplete, listing exactly what to set."""


def _credential(settings: LLMSettings):
    """Build an ``azure.identity`` credential from the service-principal settings."""
    from azure.identity import ClientSecretCredential

    return ClientSecretCredential(
        tenant_id=settings.tenant_id,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
    )


def _build_azure_openai(settings: LLMSettings) -> Any:
    """Azure OpenAI surface: ``https://<resource>.openai.azure.com`` + a deployment."""
    from langchain_openai import AzureChatOpenAI

    kwargs: dict[str, Any] = {
        "azure_endpoint": settings.endpoint,
        "azure_deployment": settings.deployment,
        "api_version": settings.api_version,
        "temperature": settings.temperature,
    }

    if settings.api_key:
        kwargs["api_key"] = settings.api_key
    else:
        # No key, so exchange the service principal for a bearer token. The provider
        # is a callable, which lets the SDK refresh the token when it expires.
        from azure.identity import get_bearer_token_provider

        kwargs["azure_ad_token_provider"] = get_bearer_token_provider(
            _credential(settings), _AAD_SCOPE
        )

    return AzureChatOpenAI(**kwargs)


def _build_azure_inference(settings: LLMSettings) -> Any:
    """Foundry models surface: ``https://<resource>.services.ai.azure.com/models``."""
    from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel

    if settings.api_key:
        from azure.core.credentials import AzureKeyCredential

        credential: Any = AzureKeyCredential(settings.api_key)
    else:
        credential = _credential(settings)

    return AzureAIChatCompletionsModel(
        endpoint=settings.endpoint,
        credential=credential,
        model_name=settings.deployment,
        temperature=settings.temperature,
    )


def build_chat_model(settings: LLMSettings | None = None) -> Any:
    """Return a LangChain chat model wired to your Foundry resource.

    Raises :class:`MissingCredentials` - naming the unset variables - rather than
    failing later with an opaque auth error from deep inside an SDK.
    """
    settings = settings or LLMSettings.from_env()

    if not settings.is_configured:
        raise MissingCredentials(
            "Azure AI Foundry is not configured. Set the following, in your shell "
            "or in a .env file at the repo root:\n  - "
            + "\n  - ".join(settings.missing())
            + "\n\nSee README.md > Connecting Azure AI Foundry for a worked example."
        )

    if settings.flavour == "azure_inference":
        return _build_azure_inference(settings)
    return _build_azure_openai(settings)
