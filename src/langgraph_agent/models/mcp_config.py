"""MCP server configuration."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfig(BaseSettings):
    """MCP server configuration."""

    managed_urls: List[str] = Field(
        default_factory=list, description="Managed MCP server URLs (including proxied external servers)"
    )
    custom_urls: List[str] = Field(default_factory=list, description="Custom MCP server URLs (hosted as Databricks Apps)")

    model_config = SettingsConfigDict(env_prefix="MCP_")
