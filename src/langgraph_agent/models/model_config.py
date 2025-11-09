"""LLM model configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from langgraph_agent.utils.config_loader import get_cached_config, get_config_value

# Load config for defaults
_config = get_cached_config()


class ModelConfig(BaseSettings):
    """LLM model configuration."""

    endpoint_name: str = Field(
        default_factory=lambda: get_config_value(
            _config, "model.endpoint_name", "MODEL_ENDPOINT_NAME", "databricks-claude-3-7-sonnet"
        ),
        description="Databricks model serving endpoint name",
    )
    system_prompt: str = Field(
        default_factory=lambda: get_config_value(
            _config,
            "model.system_prompt",
            "MODEL_SYSTEM_PROMPT",
            "You are a helpful AI assistant with access to various tools.",
        ),
        description="System prompt for the agent",
    )

    # MLflow Prompt Registry Configuration
    use_prompt_registry: bool = Field(
        default_factory=lambda: get_config_value(_config, "model.use_prompt_registry", "USE_PROMPT_REGISTRY", False),
        description="Whether to load system prompt from MLflow Prompt Registry",
    )
    prompt_name: str | None = Field(
        default_factory=lambda: get_config_value(_config, "model.prompt_name", "PROMPT_NAME", None),
        description="Name of the prompt in MLflow Prompt Registry",
    )
    prompt_version: str | int | None = Field(
        default_factory=lambda: get_config_value(_config, "model.prompt_version", "PROMPT_VERSION", None),
        description="Version of the prompt (number, 'latest', or alias name)",
    )

    model_config = SettingsConfigDict(env_prefix="MODEL_")
