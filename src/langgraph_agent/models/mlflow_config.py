"""MLflow tracking and registry configuration."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLflowConfig(BaseSettings):
    """MLflow tracking and registry configuration."""

    experiment_name: str = Field(default="/Shared/langgraph-mcp-agent", description="MLflow experiment name")
    enable_autolog: bool = Field(default=True, description="Enable MLflow autologging")

    model_config = SettingsConfigDict(env_prefix="MLFLOW_")
