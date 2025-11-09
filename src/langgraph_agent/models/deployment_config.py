"""Deployment configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentConfig(BaseSettings):
    """Deployment configuration."""

    scale_to_zero_enabled: bool = Field(default=True, description="Enable scale-to-zero for serving endpoint")
    tags: dict = Field(
        default_factory=lambda: {"endpointSource": "langgraph_mcp_agent"}, description="Tags for the deployment"
    )

    model_config = SettingsConfigDict(env_prefix="DEPLOYMENT_")
