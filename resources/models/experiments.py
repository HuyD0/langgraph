"""MLflow experiment resources for agent tracking."""

from databricks.sdk.service.ml import (
    ExperimentTag,
)


def get_agent_experiment(bundle):
    """Define the MLflow experiment for agent tracking.

    This experiment is used to track all agent runs, evaluations,
    and model versions.
    """
    # Get user email from bundle or use default
    user_email = bundle.variables.get("user_email", "huy.d@hotmail.com")

    return {
        "name": f"/Users/{user_email}/langgraph-mcp-agent-{bundle.target}",
        "description": f"LangGraph MCP Agent experiment for {bundle.target} environment",
        "tags": [
            ExperimentTag(key="project", value="langgraph-mcp-agent"),
            ExperimentTag(key="environment", value=bundle.target),
            ExperimentTag(key="managed_by", value="databricks-asset-bundle"),
        ],
    }
