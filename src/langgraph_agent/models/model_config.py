"""LLM model configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseSettings):
    """LLM model configuration."""

    endpoint_name: str = Field(default="databricks-claude-3-7-sonnet", description="Databricks model serving endpoint name")
    system_prompt: str = Field(
        default="You are a helpful assistant that can run Python code.", description="System prompt for the agent"
    )

    model_config = SettingsConfigDict(env_prefix="MODEL_")
