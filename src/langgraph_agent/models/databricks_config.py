"""Databricks workspace configuration."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabricksConfig(BaseSettings):
    """Databricks workspace configuration."""

    profile: str = Field(default="development", description="Databricks CLI profile name for local development")
    host: Optional[str] = Field(default=None, description="Databricks workspace URL")

    model_config = SettingsConfigDict(env_prefix="DATABRICKS_")
