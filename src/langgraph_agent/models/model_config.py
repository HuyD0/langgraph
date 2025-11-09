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

    model_config = SettingsConfigDict(env_prefix="MODEL_")
