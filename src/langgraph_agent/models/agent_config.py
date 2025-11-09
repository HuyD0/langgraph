"""Main agent configuration combining all sub-configurations."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from langgraph_agent.models.databricks_config import DatabricksConfig
from langgraph_agent.models.deployment_config import DeploymentConfig
from langgraph_agent.models.mcp_config import MCPServerConfig
from langgraph_agent.models.mlflow_config import MLflowConfig
from langgraph_agent.models.model_config import ModelConfig
from langgraph_agent.models.unity_catalog_config import UnityCatalogConfig


class AgentConfig(BaseSettings):
    """Main agent configuration combining all sub-configurations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Sub-configurations
    model: ModelConfig = Field(default_factory=ModelConfig)
    mcp: MCPServerConfig = Field(default_factory=MCPServerConfig)
    databricks: DatabricksConfig = Field(default_factory=DatabricksConfig)
    mlflow: MLflowConfig = Field(default_factory=MLflowConfig)
    uc: UnityCatalogConfig = Field(default_factory=UnityCatalogConfig)
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Load configuration from environment variables and .env file."""
        return cls()


def get_config() -> AgentConfig:
    """Get the agent configuration."""
    return AgentConfig.from_env()
