"""
Agent evaluation job definition.

This module defines the standalone evaluation job that can run independently
for ongoing monitoring, scheduled evaluations, or ad-hoc testing.
"""

from typing import Dict, Any
from databricks.bundles.jobs import Job


def get_evaluation_job() -> Dict[str, Any]:
    """
    Get agent evaluation job definition.

    This job runs standalone evaluation that can be used for:
    - Ongoing monitoring
    - Scheduled evaluations
    - Ad-hoc testing

    Returns:
        Dictionary with evaluation job definition
    """
    return {
        "agent_evaluation": Job.from_dict(
            {
                "name": "${bundle.target}_agent_evaluation",
                "run_as": {"user_name": "${var.user_email}"},
                "tasks": [
                    {
                        "task_key": "run_evaluation",
                        "python_wheel_task": {
                            "package_name": "langgraph_mcp_agent",
                            "entry_point": "langgraph_mcp_agent",
                            "parameters": [
                                "evaluate"
                                # Dataset will be loaded from Unity Catalog automatically
                            ],
                        },
                        "environment_key": "default_env",
                    }
                ],
                "environments": [
                    {
                        "environment_key": "default_env",
                        "spec": {
                            "client": "1",
                            "dependencies": [
                                "/Workspace/Users/huy.d@hotmail.com/.bundle/langgraph/dev/artifacts/.internal/langgraph_mcp_agent-0.1.0-py3-none-any.whl"
                            ],
                        },
                    }
                ],
                "tags": {
                    "project": "langgraph-mcp-agent",
                    "environment": "${bundle.target}",
                    "managed_by": "databricks-asset-bundle",
                },
                "max_concurrent_runs": 1,
            }
        )
    }
