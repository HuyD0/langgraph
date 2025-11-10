"""
MLflow experiment resource definition.

This module defines the MLflow experiment used for tracking
agent development, training, and evaluation.
"""

from typing import Dict, Any
from databricks.sdk.service.ml import Experiment


def get_experiment() -> Dict[str, Any]:
    """
    Get MLflow experiment definition for agent tracking.

    The experiment is used for:
    - Tracking agent development iterations
    - Logging model versions
    - Recording evaluation metrics

    Returns:
        Dictionary with experiment definition
    """
    return {
        "agent_experiment": Experiment.from_dict(
            {
                "name": "${var.experiment_name}",
                "tags": [
                    {"key": "project", "value": "langgraph-mcp-agent"},
                    {"key": "environment", "value": "${bundle.target}"},
                    {"key": "managed_by", "value": "databricks-asset-bundle"},
                ],
            }
        )
    }
