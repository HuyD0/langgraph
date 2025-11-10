"""
Agent deployment pipeline job definitions.

This module defines the deployment and serving jobs for the LangGraph MCP Agent:
1. agent_deployment_pipeline: Registers and validates the model
2. agent_deploy: Deploys the model to serving endpoint
"""

from typing import Dict, Any
from databricks.bundles.jobs import Job


def get_deployment_jobs() -> Dict[str, Any]:
    """
    Get agent deployment job definitions.

    Returns two jobs:
    - agent_deployment_pipeline: Registers model and runs validation
    - agent_deploy: Deploys model to serving endpoint

    Returns:
        Dictionary with job definitions keyed by job name
    """
    jobs = {}

    # Job 1: Register and validate model
    jobs["agent_deployment_pipeline"] = Job.from_dict(
        {
            "name": "${bundle.target}_agent_log_register",
            "run_as": {"user_name": "${var.user_email}"},
            "tasks": [
                {
                    "task_key": "register_model",
                    "python_wheel_task": {
                        "package_name": "langgraph_mcp_agent",
                        "entry_point": "register_model",
                        "named_parameters": {"experiment_name": "${var.experiment_name}"},
                    },
                    "environment_key": "serverless_env",
                },
                {
                    "task_key": "validate_model",
                    "depends_on": [{"task_key": "register_model"}],
                    "python_wheel_task": {
                        "package_name": "langgraph_mcp_agent",
                        "entry_point": "evaluate_model",
                        "named_parameters": {"experiment_name": "${var.experiment_name}"},
                    },
                    "environment_key": "serverless_env",
                },
            ],
            "environments": [
                {
                    "environment_key": "serverless_env",
                    "spec": {
                        "environment_version": "2",
                        "dependencies": [
                            "/Workspace/Users/${var.user_email}/.bundle/langgraph/dev/artifacts/.internal/langgraph_mcp_agent-0.1.0-py3-none-any.whl"
                        ],
                    },
                }
            ],
            "tags": {
                "project": "langgraph-mcp-agent",
                "environment": "${bundle.target}",
                "managed_by": "databricks-asset-bundle",
                "job_type": "register_and_validate",
            },
            "max_concurrent_runs": 1,
        }
    )

    # Job 2: Deploy to serving endpoint
    jobs["agent_deploy"] = Job.from_dict(
        {
            "name": "${bundle.target}_agent_deploy",
            "run_as": {"user_name": "${var.user_email}"},
            "tasks": [
                {
                    "task_key": "deploy_to_serving",
                    "python_wheel_task": {
                        "package_name": "langgraph_mcp_agent",
                        "entry_point": "deploy_model",
                        "named_parameters": {
                            "catalog": "${var.catalog}",
                            "schema": "${var.schema}",
                            "model_name": "${var.model_name}",
                        },
                    },
                    "environment_key": "serverless_env",
                }
            ],
            "environments": [
                {
                    "environment_key": "serverless_env",
                    "spec": {
                        "environment_version": "2",
                        "dependencies": [
                            "/Workspace/Users/${var.user_email}/.bundle/langgraph/dev/artifacts/.internal/langgraph_mcp_agent-0.1.0-py3-none-any.whl"
                        ],
                    },
                }
            ],
            "tags": {
                "project": "langgraph-mcp-agent",
                "environment": "${bundle.target}",
                "managed_by": "databricks-asset-bundle",
                "job_type": "deploy",
            },
            "max_concurrent_runs": 1,
        }
    )

    return jobs
