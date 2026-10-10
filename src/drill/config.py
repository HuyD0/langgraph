"""Runtime settings, read from the environment.

The single most important rule in this module: **importing it must never touch the
network, the filesystem, or a credential store.** The old Databricks agent built a
``WorkspaceClient`` and an Azure Search client at import time, which meant you could
not even ``import`` it - let alone unit-test it - without live cloud credentials.

Everything here is a plain dataclass built from ``os.environ`` when you ask for it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

# Repository root, i.e. the directory holding pyproject.toml.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Where your practice history is stored. One JSON file, easy to read and diff.
DEFAULT_PROGRESS_PATH = PROJECT_ROOT / ".drill" / "progress.json"


def _env_int(name: str, default: int) -> int:
    """Read an int from the environment, falling back if unset or unparseable."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class LLMSettings:
    """How to reach your Azure AI Foundry model.

    Foundry resources expose two different chat surfaces, and which one you have
    determines which client library speaks to it:

    ``azure_openai``
        The classic Azure OpenAI surface. Endpoint looks like
        ``https://<resource>.openai.azure.com/`` and you address a *deployment*
        by name. Served by ``langchain_openai.AzureChatOpenAI``.

    ``azure_inference``
        The newer Foundry "models" surface, covering non-OpenAI models too.
        Endpoint looks like ``https://<resource>.services.ai.azure.com/models``
        and you address a *model* by name. Served by
        ``langchain_azure_ai.chat_models.AzureAIChatCompletionsModel``.

    ``ollama``
        A model running locally under Ollama, no Azure and no credentials. Turned
        on by setting ``OLLAMA_MODEL``, which takes precedence over any Azure
        settings. Served by ``langchain_openai.ChatOpenAI`` against Ollama's
        OpenAI-compatible endpoint (``OLLAMA_BASE_URL``, default
        ``http://localhost:11434/v1``).

    ``mlflow_gateway``
        An endpoint on a local MLflow AI Gateway, which forwards to whichever model
        the endpoint is pointed at and records every call. Turned on by setting
        ``MLFLOW_GATEWAY_ENDPOINT`` (the endpoint name), which takes precedence over
        everything else. Served by ``ChatOpenAI`` against the gateway's
        OpenAI-compatible API (``MLFLOW_GATEWAY_URL``, default
        ``http://localhost:5050/gateway/mlflow/v1``).

    You do not have to pick manually - :func:`from_env` infers it from the endpoint
    URL, and ``AZURE_FOUNDRY_FLAVOUR`` overrides the guess if it gets it wrong.
    """

    endpoint: str | None = None
    deployment: str | None = None
    api_version: str = "2024-10-21"
    api_key: str | None = None
    flavour: str = "azure_openai"
    temperature: float | None = 0.2

    # Service-principal fields. Populated from the same three variables the old
    # agent used for Azure Search, so existing credentials carry straight over.
    tenant_id: str | None = None
    client_id: str | None = None
    client_secret: str | None = None

    @property
    def uses_service_principal(self) -> bool:
        """True when we should fetch an AAD token instead of sending an API key."""
        return not self.api_key and all([self.tenant_id, self.client_id, self.client_secret])

    @property
    def is_local(self) -> bool:
        """True for Ollama or a local MLflow gateway: no credentials needed here."""
        return self.flavour in {"ollama", "mlflow_gateway"}

    @property
    def is_configured(self) -> bool:
        """True when there is enough here to attempt a real connection."""
        if self.is_local:
            return bool(self.endpoint) and bool(self.deployment)
        has_auth = bool(self.api_key) or self.uses_service_principal
        return bool(self.endpoint) and bool(self.deployment) and has_auth

    def missing(self) -> list[str]:
        """Human-readable list of what is still unset, for a useful error message."""
        gaps: list[str] = []
        if self.is_local:
            if not self.deployment:
                gaps.append(
                    "MLFLOW_GATEWAY_ENDPOINT (a gateway endpoint name)"
                    if self.flavour == "mlflow_gateway"
                    else "OLLAMA_MODEL (a model you have pulled, e.g. gemma3:12b)"
                )
            return gaps
        if not self.endpoint:
            gaps.append("AZURE_OPENAI_ENDPOINT (or AZURE_INFERENCE_ENDPOINT)")
        if not self.deployment:
            gaps.append("AZURE_OPENAI_DEPLOYMENT (your model deployment name)")
        if not self.api_key and not self.uses_service_principal:
            gaps.append(
                "AZURE_OPENAI_API_KEY, or all of "
                "AZURE_TENANT_ID + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET"
            )
        return gaps

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "LLMSettings":
        """Settings from the environment, or from ``env``: a mapping standing in for it.

        The local server passes a copy of the environment with the Ollama variables
        removed, to get the *hosted* model as a fallback even when .env names a local one.
        """
        getenv = (env if env is not None else os.environ).get
        # Reasoning models - the gpt-5 family and the o-series - reject every
        # temperature but their own default, answering with an ``unsupported_value``
        # error. Setting DRILL_TEMPERATURE to an empty value omits the parameter
        # altogether; scripts/azure_up.sh writes that automatically when it detects
        # the deployed model refuses one.
        temperature_raw = getenv("DRILL_TEMPERATURE", "0.2")
        if temperature_raw.strip() == "":
            temperature = None
        else:
            try:
                temperature = float(temperature_raw)
            except ValueError:
                temperature = 0.2

        # A gateway endpoint wins over everything, then a local model, then Azure, so
        # switching is one line in .env.
        gateway_endpoint = getenv("MLFLOW_GATEWAY_ENDPOINT", "").strip()
        if gateway_endpoint:
            return cls(
                endpoint=getenv("MLFLOW_GATEWAY_URL", "").strip()
                or "http://localhost:5050/gateway/mlflow/v1",
                deployment=gateway_endpoint,
                flavour="mlflow_gateway",
                temperature=temperature,
            )

        ollama_model = getenv("OLLAMA_MODEL", "").strip()
        if ollama_model:
            return cls(
                endpoint=getenv("OLLAMA_BASE_URL", "").strip() or "http://localhost:11434/v1",
                deployment=ollama_model,
                flavour="ollama",
                temperature=temperature,
            )

        endpoint = (
            getenv("AZURE_OPENAI_ENDPOINT")
            or getenv("AZURE_INFERENCE_ENDPOINT")
            or getenv("AZURE_AI_ENDPOINT")
        )

        # Infer the surface from the URL shape, then let an explicit override win.
        inferred = "azure_openai"
        if endpoint and ("services.ai.azure.com" in endpoint or endpoint.rstrip("/").endswith("/models")):
            inferred = "azure_inference"
        flavour = getenv("AZURE_FOUNDRY_FLAVOUR", inferred).strip().lower()
        if flavour not in {"azure_openai", "azure_inference"}:
            flavour = inferred

        return cls(
            endpoint=endpoint,
            deployment=(
                getenv("AZURE_OPENAI_DEPLOYMENT")
                or getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                or getenv("AZURE_INFERENCE_MODEL")
            ),
            api_version=getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            api_key=getenv("AZURE_OPENAI_API_KEY") or getenv("AZURE_INFERENCE_CREDENTIAL"),
            flavour=flavour,
            temperature=temperature,
            tenant_id=getenv("AZURE_TENANT_ID"),
            client_id=getenv("AZURE_CLIENT_ID"),
            client_secret=getenv("AZURE_CLIENT_SECRET"),
        )


@dataclass(frozen=True)
class DrillSettings:
    """Everything else: how the tutor behaves and where it writes."""

    llm: LLMSettings = field(default_factory=LLMSettings.from_env)

    # How many failed submissions before the tutor stops hinting and just
    # explains the solution. Three is deliberate: enough to struggle
    # productively, not enough to get demoralised.
    max_attempts: int = 3

    # Seconds a submitted solution may run before we kill it. Guards against the
    # infinite loop you will absolutely write at some point.
    sandbox_timeout: int = 10

    progress_path: Path = DEFAULT_PROGRESS_PATH
    mlflow_tracking_uri: str | None = None
    mlflow_experiment: str = "daily-drill"

    @classmethod
    def from_env(cls) -> "DrillSettings":
        progress = os.getenv("DRILL_PROGRESS_PATH")
        return cls(
            llm=LLMSettings.from_env(),
            max_attempts=_env_int("DRILL_MAX_ATTEMPTS", 3),
            sandbox_timeout=_env_int("DRILL_SANDBOX_TIMEOUT", 10),
            progress_path=Path(progress) if progress else DEFAULT_PROGRESS_PATH,
            # Unset means MLflow writes to ./mlruns, which `mlflow ui` reads by default.
            mlflow_tracking_uri=os.getenv("MLFLOW_TRACKING_URI"),
            mlflow_experiment=os.getenv("MLFLOW_EXPERIMENT_NAME", "daily-drill"),
        )
