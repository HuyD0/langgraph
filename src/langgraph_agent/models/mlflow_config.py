"""MLflow tracking and registry configuration."""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from langgraph_agent.utils.config_loader import get_cached_config, get_config_value

# Load config for defaults
_config = get_cached_config()


class MLApplicationEntry(BaseSettings):
    """ML Application entry point configuration."""

    file: str = Field(default="app.py", description="Entry file name")
    function: str = Field(default="create_agent", description="Entry function name")

    model_config = SettingsConfigDict(env_prefix="MLFLOW_ML_APPLICATION_ENTRY_")


class MLApplicationConfig(BaseSettings):
    """ML Application metadata configuration."""

    name: str = Field(default="langgraph-mcp-agent", description="Application name")
    description: str = Field(
        default="LangGraph agent with MCP tool calling capabilities", description="Application description"
    )
    entry: MLApplicationEntry = Field(default_factory=MLApplicationEntry, description="Entry point configuration")
    requirements: List[str] = Field(
        default_factory=lambda: [
            "databricks-mcp",
            "langgraph",
            "mcp",
            "databricks-langchain",
            "databricks-sdk",
            "nest-asyncio",
            "pydantic",
        ],
        description="Python package requirements",
    )

    model_config = SettingsConfigDict(env_prefix="MLFLOW_ML_APPLICATION_")


class MLflowConfig(BaseSettings):
    """MLflow tracking and registry configuration."""

    experiment_name: str = Field(
        default_factory=lambda: get_config_value(
            _config, "mlflow.experiment_name", "MLFLOW_EXPERIMENT_NAME", "/Shared/langgraph-mcp-agent"
        ),
        description="MLflow experiment name",
    )
    model_name: str = Field(default="langgraph_mcp_agent", description="Model name for registry")
    run_name: str = Field(default="agent_run", description="MLflow run name")
    enable_autolog: bool = Field(default=True, description="Enable MLflow autologging")
    ml_application: MLApplicationConfig = Field(default_factory=MLApplicationConfig, description="ML Application metadata")

    model_config = SettingsConfigDict(env_prefix="MLFLOW_")
