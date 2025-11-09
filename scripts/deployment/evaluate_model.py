"""Evaluate model task for Databricks job.

This script can be called directly from a Databricks job without CLI.
"""

import sys

from langgraph_agent.agents import initialize_agent
from langgraph_agent.models import get_config
from langgraph_agent.pipelines.evaluation import run_evaluation_pipeline
from langgraph_agent.utils.auth import get_workspace_client
from langgraph_agent.utils.mlflow_setup import setup_mlflow_tracking


def main():
    """Evaluate the agent."""
    config = get_config()

    print("Setting up MLflow tracking...")
    setup_mlflow_tracking(
        profile=config.databricks.profile,
        experiment_name=config.mlflow.experiment_name,
        enable_autolog=False,
    )

    print("Initializing agent...")
    ws = get_workspace_client(config.databricks.profile)
    ws_host = ws.config.host
    managed_urls = config.mcp.managed_urls or [f"{ws_host}/api/2.0/mcp/functions/system/ai"]

    agent = initialize_agent(
        workspace_client=ws,
        llm_endpoint_name=config.model.endpoint_name,
        system_prompt=config.model.system_prompt,
        managed_mcp_urls=managed_urls,
        custom_mcp_urls=config.mcp.custom_urls,
    )

    print("Running evaluation...")
    results = run_evaluation_pipeline(
        agent=agent,
        dataset_path=None,  # Will load from Unity Catalog
        experiment_name=config.mlflow.experiment_name,
    )

    print("✓ Evaluation complete!")
    print(f"  Metrics: {results['metrics']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
