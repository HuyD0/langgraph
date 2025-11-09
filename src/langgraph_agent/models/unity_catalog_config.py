"""Unity Catalog model registry configuration."""

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class UnityCatalogConfig(BaseSettings):
    """Unity Catalog model registry configuration."""

    model_config = SettingsConfigDict(env_prefix="UC_", protected_namespaces=())  # Allow 'model_' prefix

    catalog: str = Field(default="rag", description="Unity Catalog catalog name")
    schema_name: str = Field(default="development", description="Unity Catalog schema name", alias="schema")
    model_name: str = Field(default="langgraph_mcp_agent", description="Model name in Unity Catalog")

    @property
    def schema(self) -> str:
        """Get the schema name (for backward compatibility)."""
        return self.schema_name

    @property
    def full_model_name(self) -> str:
        """Get the full three-level UC model name."""
        return f"{self.catalog}.{self.schema_name}.{self.model_name}"
