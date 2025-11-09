"""MLflow tracking and registry configuration."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLflowConfig(BaseSettings):
    """MLflow tracking and registry configuration."""

    experiment_name: Optional[str] = Field(default=None, description="MLflow experiment name")
    enable_autolog: bool = Field(default=True, description="Enable MLflow autologging")

    model_config = SettingsConfigDict(env_prefix="MLFLOW_")
